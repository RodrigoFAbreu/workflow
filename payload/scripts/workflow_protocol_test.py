#!/usr/bin/env python3
"""Tests for `workflow_protocol.py`, Orchestration Protocol v1's core
(`ORCHESTRATION_PROTOCOL_V1_PLAN.md`, CP3): the envelope, protocol
versioning, error codes and the Workflow exception domain, state identity,
`describe`, `verify` and `resolve-artifact`.

Every response is checked against the shipped
`docs/ai-workflow/orchestration-protocol-v1.schema.json` with the minimal
validator below (`type`, `required`, `properties`, `additionalProperties`,
`enum`, `items`, `$ref`). Scratch repositories come from
`workflow_test_harness`.

Stdlib-only. Run: python3 scripts/workflow_protocol_test.py
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import workflow_fingerprint as fingerprint
import workflow_protocol as wp
import workflow_state as ws
import workflow_test_harness as h

SCRIPT = Path(__file__).resolve().parent / "workflow_protocol.py"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "docs" / "ai-workflow" / "orchestration-protocol-v1.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())

# ---------------------------------------------------------------------------
# The minimal JSON Schema checker
# ---------------------------------------------------------------------------

VALIDATING_KEYWORDS = frozenset({
    "type", "required", "properties", "additionalProperties", "enum", "items", "$ref",
})
ANNOTATION_KEYWORDS = frozenset({"$schema", "$id", "$defs", "title", "description"})

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _resolve_ref(ref: str) -> dict:
    if not ref.startswith("#/"):
        raise AssertionError(f"unsupported $ref {ref!r}")
    node = SCHEMA
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def schema_errors(value, schema: dict, path: str = "$") -> list[str]:
    """Every violation of `schema` by `value`, as `path: reason` strings."""
    if "$ref" in schema:
        return schema_errors(value, _resolve_ref(schema["$ref"]), path)
    errors: list[str] = []
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_TYPES[t](value) for t in types):
            return [f"{path}: {value!r} is not of type {types}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required {key!r}")
        properties = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                errors.extend(schema_errors(item, properties[key], f"{path}.{key}"))
            elif extra is False:
                errors.append(f"{path}: unexpected property {key!r}")
            elif isinstance(extra, dict):
                errors.extend(schema_errors(item, extra, f"{path}.{key}"))
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(schema_errors(item, schema["items"], f"{path}[{index}]"))
    return errors


def _keywords(node, found: set[str], *, in_properties: bool = False) -> None:
    if isinstance(node, dict):
        for key, child in node.items():
            if not in_properties:
                found.add(key)
            if key in ("properties", "$defs") and not in_properties:
                _keywords(child, found, in_properties=True)
            elif key in ("enum", "required", "title", "description", "$schema", "$id"):
                continue
            else:
                _keywords(child, found)
    elif isinstance(node, list):
        for child in node:
            _keywords(child, found)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def call(*argv: str) -> tuple[dict, int]:
    """Run an operation in-process and check the envelope and its result
    against the schema."""
    body, code = wp.run(list(argv))
    assert_valid(body)
    return body, code


def assert_valid(body: dict) -> None:
    errors = schema_errors(body, SCHEMA)
    if body.get("ok"):
        result_schema = SCHEMA["$defs"]["results"]["properties"][body["operation"]]
        errors += schema_errors(body["result"], result_schema, "$.result")
        if "error" in body:
            errors.append("$: ok envelope carries an error")
    else:
        if "error" not in body or "result" in body:
            errors.append("$: a refusal carries error and no result")
    if errors:
        raise AssertionError("schema violations:\n" + "\n".join(errors))


def write_state(repo: h.ScratchRepo, state: dict) -> Path:
    path = repo.root / ws.DEFAULT_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")
    return path


def empty_state() -> dict:
    return h.base_state()


def item(**overrides) -> dict:
    return h.base_work_item(state_revision=1, **overrides)


def checks_by_id(body: dict) -> dict:
    return {c["id"]: c for c in body["result"]["checks"]}


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class TestSchema(unittest.TestCase):
    def test_schema_uses_only_the_supported_keywords(self):
        found: set[str] = set()
        _keywords(SCHEMA, found)
        self.assertLessEqual(found, VALIDATING_KEYWORDS | ANNOTATION_KEYWORDS)

    def test_every_operation_has_a_result_schema(self):
        self.assertEqual(set(SCHEMA["$defs"]["results"]["properties"]), set(wp.OPERATIONS))

    def test_error_code_enum_equals_the_code_table(self):
        self.assertEqual(SCHEMA["$defs"]["error"]["properties"]["code"]["enum"], sorted(wp.ERROR_CODES))

    def test_artifact_kind_enum_equals_the_kind_table(self):
        kinds = SCHEMA["$defs"]["results"]["properties"]["resolve-artifact"]["properties"]["kind"]["enum"]
        self.assertEqual(kinds, sorted(wp.ARTIFACT_KINDS))

    def test_verify_check_enum_equals_the_check_ids(self):
        ids = SCHEMA["$defs"]["results"]["properties"]["verify"]["properties"]["checks"]["items"][
            "properties"]["id"]["enum"]
        self.assertEqual(ids, list(wp.VERIFY_CHECK_IDS))

    def test_the_checker_rejects_a_bad_envelope(self):
        body, _ = wp.run(["describe"])
        body = dict(body, extra=1)
        with self.assertRaises(AssertionError):
            assert_valid(body)


# ---------------------------------------------------------------------------
# Envelope, versioning, exit codes
# ---------------------------------------------------------------------------


class TestEnvelope(unittest.TestCase):
    def test_stdout_is_exactly_one_envelope(self):
        with h.ScratchRepo() as repo:
            write_state(repo, empty_state())
            out = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo-root", str(repo.root), "verify"],
                capture_output=True, text=True,
            )
        self.assertEqual(out.returncode, wp.EXIT_OK, out.stderr)
        self.assertTrue(out.stdout.endswith("\n"))
        self.assertEqual(out.stdout.count("\n"), 1)
        body = json.loads(out.stdout)
        assert_valid(body)
        self.assertEqual(body["protocol"], {"name": "workflow-orchestration", "version": "1.0"})
        self.assertEqual(body["workflow_release"], wp.WORKFLOW_RELEASE)
        self.assertEqual(body["operation"], "verify")

    def test_unsupported_major_refuses_before_anything_is_read(self):
        with mock.patch.object(wp, "read_state_and_config", side_effect=AssertionError("read")), \
                mock.patch.dict(wp.OPERATIONS, {"describe": mock.Mock(side_effect=AssertionError("run"))}):
            body, code = call("--repo-root", "/nonexistent/repository", "--protocol-major", "2", "describe")
        self.assertEqual(code, wp.EXIT_REFUSED)
        self.assertEqual(body["error"]["code"], "unsupported_protocol")
        self.assertFalse(body["error"]["retryable"])
        self.assertIsNone(body["error"]["native"])

    def test_unsupported_major_through_the_cli_exits_3(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), "--protocol-major", "2", "describe"],
            capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 3)
        body = json.loads(out.stdout)
        assert_valid(body)
        self.assertEqual(body["error"]["code"], "unsupported_protocol")

    def test_supported_major_is_accepted(self):
        body, code = call("--protocol-major", "1", "describe")
        self.assertEqual(code, wp.EXIT_OK)
        self.assertTrue(body["ok"])

    def test_bad_argument_is_invalid_request_exit_2_as_an_envelope(self):
        for argv in (["bogus"], [], ["resolve-artifact", "--kind", "plan_document"],
                     ["--protocol-major", "one", "describe"], ["describe", "--unknown"]):
            out = subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, text=True)
            self.assertEqual(out.returncode, 2, argv)
            body = json.loads(out.stdout)
            assert_valid(body)
            self.assertEqual(body["error"]["code"], "invalid_request", argv)

    def test_missing_repo_root_is_invalid_request(self):
        body, code = call("--repo-root", "/nonexistent/repository", "verify")
        self.assertEqual(code, wp.EXIT_INVALID_REQUEST)
        self.assertEqual(body["error"]["code"], "invalid_request")

    def test_injected_unexpected_exception_is_internal_error_exit_1(self):
        with mock.patch.dict(wp.OPERATIONS, {"describe": mock.Mock(side_effect=RuntimeError("boom"))}), \
                mock.patch("sys.stderr"):
            body, code = call("describe")
        self.assertEqual(code, wp.EXIT_INTERNAL)
        self.assertEqual(body["error"]["code"], "internal_error")
        self.assertIsNone(body["error"]["native"])
        self.assertIn("boom", body["error"]["message"])


# ---------------------------------------------------------------------------
# The Workflow exception domain (D-OP-Errors, LPR-R4-001)
# ---------------------------------------------------------------------------


def workflow_exception_classes(module) -> list[type]:
    return [
        cls for _name, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, Exception) and cls.__module__ == module.__name__
    ]


def instantiate(cls: type) -> BaseException:
    exc = cls.__new__(cls)
    Exception.__init__(exc, "test")
    return exc


class LocalError(Exception):
    pass


class TestWorkflowExceptionDomain(unittest.TestCase):
    def setUp(self):
        self.classes = workflow_exception_classes(ws) + workflow_exception_classes(fingerprint)

    def test_the_enumeration_includes_the_intermediates_and_their_subclasses(self):
        names = {cls.__name__ for cls in self.classes}
        self.assertIn("LifecycleRefusalError", names)
        self.assertIn("PlanApprovalTakeoverRefusedError", names)
        self.assertIn("AmendmentInFlightError", names)
        self.assertTrue(any(
            issubclass(cls, ws.PlanApprovalTakeoverRefusedError) and cls is not ws.PlanApprovalTakeoverRefusedError
            for cls in self.classes))

    def test_every_workflow_class_is_in_the_domain(self):
        for cls in self.classes:
            self.assertTrue(wp.is_workflow_exception(instantiate(cls)), cls)

    def test_builtins_and_foreign_classes_are_not(self):
        for exc in (KeyError("k"), TypeError("t"), ValueError("v"), OSError("o"), LocalError("l")):
            self.assertFalse(wp.is_workflow_exception(exc), exc)

    def test_every_table_key_names_an_enumerated_class(self):
        names = {cls.__name__ for cls in self.classes}
        self.assertLessEqual(set(wp.WORKFLOW_EXCEPTION_CODES), names)

    def test_the_table_is_pinned(self):
        self.assertEqual(wp.WORKFLOW_EXCEPTION_CODES, {
            "InvalidWorkItemIdError": "invalid_request",
            "FeedbackLayoutUndecidableError": "state_unreadable",
            "UnknownFeedbackLayoutError": "state_invalid",
        })
        self.assertLessEqual(set(wp.WORKFLOW_EXCEPTION_CODES.values()), set(wp.ERROR_CODES))

    def test_every_unmapped_class_is_refused(self):
        for cls in self.classes:
            if cls.__name__ in wp.WORKFLOW_EXCEPTION_CODES:
                continue
            self.assertEqual(wp.code_for_workflow_exception(instantiate(cls)), "refused", cls)

    def test_a_class_added_by_a_later_release_is_refused(self):
        future = type("FutureRefusalError", (Exception,), {"__module__": ws.__name__})
        exc = future("later")
        self.assertTrue(wp.is_workflow_exception(exc))
        self.assertEqual(wp.code_for_workflow_exception(exc), "refused")

    def test_the_domain_follows_the_module_objects_not_literals(self):
        spec = importlib.util.spec_from_file_location(
            "renamed_workflow_state", Path(ws.__file__))
        renamed = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renamed)
        exc = renamed.CorruptJsonError("x")
        self.assertEqual(type(exc).__module__, "renamed_workflow_state")
        self.assertFalse(wp.is_workflow_exception(exc))
        with mock.patch.object(wp, "workflow_state", renamed):
            self.assertTrue(wp.is_workflow_exception(exc))
            self.assertEqual(wp.code_for_workflow_exception(exc), "refused")

    def test_a_workflow_refusal_from_an_operation_carries_native(self):
        for raised, expected in ((ws.CorruptJsonError("registry"), "refused"),
                                 (fingerprint.FeedbackLayoutUndecidableError("undecidable"), "state_unreadable")):
            with h.ScratchRepo() as repo:
                write_state(repo, h.base_state(wi=item()))
                with mock.patch.object(fingerprint, "resolve_feedback_dir", side_effect=raised):
                    body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                                      "--work-item", "wi", "--kind", "review_feedback")
            self.assertEqual(code, wp.EXIT_REFUSED)
            self.assertEqual(body["error"]["code"], expected)
            self.assertEqual(body["error"]["native"],
                             {"exception": type(raised).__name__, "message": str(raised)})

    def test_an_invalid_state_value_is_state_invalid_with_native(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(feedback_layout="bogus")))
            body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                              "--work-item", "wi", "--kind", "review_feedback")
        self.assertEqual(code, wp.EXIT_REFUSED)
        self.assertEqual(body["error"]["code"], "state_invalid")
        self.assertEqual(body["error"]["native"]["exception"], "UnknownFeedbackLayoutError")

    def test_raw_builtin_from_workflow_code_is_internal_error(self):
        for raised in (KeyError("missing"), OSError("disk")):
            with h.ScratchRepo() as repo:
                write_state(repo, h.base_state(wi=item()))
                with mock.patch.object(ws, "validate_state", side_effect=raised), mock.patch("sys.stderr"):
                    body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                                      "--work-item", "wi", "--kind", "plan_document")
            self.assertEqual(code, wp.EXIT_INTERNAL, raised)
            self.assertEqual(body["error"]["code"], "internal_error", raised)

    def test_unreadable_lock_file_is_state_unreadable(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item()))
            lock = ws.state_lock_path(repo.root)
            lock.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(repo.root / "elsewhere", lock)
            body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                              "--work-item", "wi", "--kind", "plan_document")
        self.assertEqual(code, wp.EXIT_REFUSED)
        self.assertEqual(body["error"]["code"], "state_unreadable")
        self.assertFalse(body["error"]["retryable"])

    def test_missing_and_corrupt_state_are_state_unreadable(self):
        with h.ScratchRepo() as repo:
            body, _ = call("--repo-root", str(repo.root), "resolve-artifact",
                           "--work-item", "wi", "--kind", "plan_document")
            self.assertEqual(body["error"]["code"], "state_unreadable")
            (repo.root / ws.DEFAULT_STATE_PATH).parent.mkdir(parents=True)
            (repo.root / ws.DEFAULT_STATE_PATH).write_text("{not json")
            body, _ = call("--repo-root", str(repo.root), "resolve-artifact",
                           "--work-item", "wi", "--kind", "plan_document")
            self.assertEqual(body["error"]["code"], "state_unreadable")
            self.assertEqual(body["error"]["native"]["exception"], "CorruptJsonError")

    def test_invalid_state_is_state_invalid(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(phase="NOT_A_PHASE")))
            body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                              "--work-item", "wi", "--kind", "plan_document")
        self.assertEqual(code, wp.EXIT_REFUSED)
        self.assertEqual(body["error"]["code"], "state_invalid")
        self.assertIsNotNone(body["error"]["native"])

    def test_unknown_work_item(self):
        with h.ScratchRepo() as repo:
            write_state(repo, empty_state())
            body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                              "--work-item", "absent", "--kind", "plan_document")
        self.assertEqual(code, wp.EXIT_REFUSED)
        self.assertEqual(body["error"]["code"], "unknown_work_item")


# ---------------------------------------------------------------------------
# describe
# ---------------------------------------------------------------------------


class TestDescribe(unittest.TestCase):
    def test_lists_equal_the_module_tables(self):
        body, code = call("describe")
        self.assertEqual(code, wp.EXIT_OK)
        result = body["result"]
        self.assertEqual(result["workflow_release"], wp.WORKFLOW_RELEASE)
        self.assertEqual(result["protocol_version"], wp.PROTOCOL_VERSION)
        self.assertEqual(result["supported_protocol_majors"], [wp.PROTOCOL_MAJOR])
        self.assertEqual(result["supported_governing_versions"], sorted(wp.SUPPORTED_GOVERNING_VERSIONS))
        capabilities = result["capabilities"]
        self.assertEqual(capabilities["operations"], sorted(wp.OPERATIONS))
        self.assertEqual(capabilities["dispositions"], sorted(wp.DISPOSITIONS))
        self.assertEqual(capabilities["action_ids"], sorted(wp.ACTION_IDS))
        self.assertEqual(capabilities["artifact_kinds"], sorted(wp.ARTIFACT_KINDS))
        self.assertEqual(capabilities["external_result_kinds"], sorted(wp.EXTERNAL_RESULT_KINDS))
        self.assertEqual(capabilities["reserved_result_kinds"], sorted(wp.RESERVED_RESULT_KINDS))
        self.assertEqual(capabilities["error_codes"], sorted(wp.ERROR_CODES))

    def test_supported_governing_versions_follow_the_two_stage_set(self):
        self.assertEqual(
            sorted(wp.SUPPORTED_GOVERNING_VERSIONS),
            sorted({"1"} | ws.TWO_STAGE_PLAN_REVIEW_VERSIONS))

    def test_the_v1_vocabulary(self):
        self.assertEqual(wp.PROTOCOL_VERSION, "1.0")
        self.assertEqual(wp.PROTOCOL_MAJOR, 1)
        self.assertEqual(
            set(wp.OPERATIONS),
            {"describe", "verify", "resolve-artifact", "next-action", "reconcile", "record-external-result"})
        self.assertEqual(set(wp.EXTERNAL_RESULT_KINDS), {"plan_review_verdict", "implementation_review_verdict"})
        self.assertEqual(set(wp.RESERVED_RESULT_KINDS), {"pr_review_result", "functional_evidence"})
        self.assertEqual(
            set(wp.DISPOSITIONS),
            {"automatic", "validation", "human_gate", "external_gate", "blocked", "complete"})
        self.assertEqual(
            {code for code, retryable in wp.ERROR_CODES.items() if retryable}, {"stale_decision"})

    def test_describe_reads_no_state(self):
        with h.ScratchRepo() as repo, \
                mock.patch.object(wp, "read_state_and_config", side_effect=AssertionError("read")):
            body, code = call("--repo-root", str(repo.root), "describe")
        self.assertEqual(code, wp.EXIT_OK)


# ---------------------------------------------------------------------------
# State identity and basis
# ---------------------------------------------------------------------------


class TestStateIdentity(unittest.TestCase):
    def test_stable_under_key_order(self):
        a = h.base_state(wi=item(phase="IMPLEMENTING", plan_revision=2))
        reordered = dict(reversed(list(a["work_items"]["wi"].items())))
        b = {"work_items": {"wi": reordered}, "active_work_item_id": None, "schema_version": 1}
        self.assertEqual(wp.state_identity("wi", a), wp.state_identity("wi", b))

    def test_changes_with_any_work_item_field(self):
        state = h.base_state(wi=item())
        before = wp.state_identity("wi", state)
        for key, value in (("phase", "SELF_REVIEWING_IMPLEMENTATION"), ("state_revision", 2),
                           ("checkpoints", {"CP1": {"status": "COMPLETE"}}), ("new_field", None)):
            changed = json.loads(json.dumps(state))
            changed["work_items"]["wi"][key] = value
            self.assertNotEqual(wp.state_identity("wi", changed), before, key)

    def test_unchanged_by_another_item_or_the_active_id(self):
        state = h.base_state(wi=item(), other=item(work_item_id="other"))
        before = wp.state_identity("wi", state)
        state["work_items"]["other"]["phase"] = "MILESTONE_COMPLETE"
        state["work_items"]["third"] = item(work_item_id="third")
        state["active_work_item_id"] = "other"
        self.assertEqual(wp.state_identity("wi", state), before)

    def test_is_sha256_of_the_canonical_projection(self):
        import hashlib
        state = h.base_state(wi=item())
        expected = hashlib.sha256(json.dumps(
            {"schema_version": 1, "work_item_id": "wi", "work_item": state["work_items"]["wi"]},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(wp.state_identity("wi", state), expected)

    def test_basis_shape(self):
        with h.ScratchRepo() as repo:
            state = h.base_state(wi=item(checkpoints={
                "CP2": {"status": "IN_PROGRESS"}, "CP1": {"status": "COMPLETE"}}))
            result = wp.basis(repo.root, state, "wi")
            self.assertEqual(result["head"], repo.head())
        self.assertEqual(result["checkpoints"], {"CP1": "COMPLETE", "CP2": "IN_PROGRESS"})
        self.assertEqual(result["state_identity"], wp.state_identity("wi", state))
        self.assertEqual(result["state_revision"], 1)
        self.assertEqual(result["phase"], "IMPLEMENTING")
        self.assertEqual(schema_errors(result, SCHEMA["$defs"]["basis"]), [])


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


class TestVerify(unittest.TestCase):
    def verify(self, repo: h.ScratchRepo) -> dict:
        body, code = call("--repo-root", str(repo.root), "verify")
        self.assertEqual(code, wp.EXIT_OK)
        self.assertTrue(body["ok"])
        self.assertEqual([c["id"] for c in body["result"]["checks"]], list(wp.VERIFY_CHECK_IDS))
        return body

    def assert_only_failure(self, body: dict, check_id: str) -> None:
        failed = [c["id"] for c in body["result"]["checks"] if c["status"] == "fail"]
        expected = [check_id]
        if check_id in wp.VERIFY_CHECK_IDS[:4]:
            expected.append("protocol_ready")
        self.assertEqual(failed, expected)
        self.assertFalse(body["result"]["healthy"])

    def test_healthy_on_a_fresh_scratch_repository(self):
        with h.ScratchRepo() as repo:
            write_state(repo, empty_state())
            body = self.verify(repo)
        self.assertTrue(body["result"]["healthy"])
        checks = checks_by_id(body)
        self.assertEqual(checks["installation_release_matches"]["status"], "skip")
        self.assertEqual(checks["protocol_ready"]["status"], "pass")

    def test_corrupt_state(self):
        with h.ScratchRepo() as repo:
            write_state(repo, empty_state()).write_text("{corrupt")
            body = self.verify(repo)
        checks = checks_by_id(body)
        self.assertEqual(checks["state_readable"]["status"], "fail")
        for check_id in ("state_valid", "config_valid", "active_item_resolvable",
                         "checkpoint_completions_provable"):
            self.assertEqual(checks[check_id]["status"], "skip", check_id)
        self.assertEqual(checks["protocol_ready"]["status"], "fail")
        self.assertFalse(body["result"]["healthy"])

    def test_missing_state(self):
        with h.ScratchRepo() as repo:
            body = self.verify(repo)
        self.assertEqual(checks_by_id(body)["state_readable"]["status"], "fail")

    def test_unknown_phase(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(phase="NOT_A_PHASE")))
            body = self.verify(repo)
        self.assert_only_failure(body, "state_valid")

    def test_corrupt_config(self):
        with h.ScratchRepo() as repo:
            write_state(repo, empty_state())
            (repo.root / ws.DEFAULT_CONFIG_PATH).write_text(json.dumps({"schema_version": 99}))
            body = self.verify(repo)
        self.assert_only_failure(body, "config_valid")

    def test_valid_config(self):
        with h.ScratchRepo() as repo:
            write_state(repo, empty_state())
            (repo.root / ws.DEFAULT_CONFIG_PATH).write_text(json.dumps(ws.default_config()))
            body = self.verify(repo)
        self.assertTrue(body["result"]["healthy"])

    def test_dangling_active_id(self):
        with h.ScratchRepo() as repo:
            state = h.base_state(wi=item())
            state["active_work_item_id"] = "absent"
            write_state(repo, state)
            body = self.verify(repo)
        self.assertEqual(checks_by_id(body)["active_item_resolvable"]["status"], "fail")
        self.assertEqual(checks_by_id(body)["protocol_ready"]["status"], "fail")

    def test_active_id_naming_a_terminal_item(self):
        with h.ScratchRepo() as repo:
            state = h.base_state(wi=item(phase="MILESTONE_COMPLETE"))
            state["active_work_item_id"] = "wi"
            write_state(repo, state)
            body = self.verify(repo)
        self.assertEqual(checks_by_id(body)["active_item_resolvable"]["status"], "fail")

    def test_complete_with_no_trailer_commit(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(
                base_commit=repo.base, checkpoints={"CP1": {"status": "COMPLETE"}})))
            body = self.verify(repo)
        self.assert_only_failure(body, "checkpoint_completions_provable")
        self.assertIn("CP1", checks_by_id(body)["checkpoint_completions_provable"]["detail"])

    def test_complete_with_its_trailer_commit(self):
        with h.ScratchRepo() as repo:
            base = repo.base
            repo.commit("cp1", trailers={"Workflow-Checkpoint": "CP1", "Workflow-Work-Item": "wi"})
            write_state(repo, h.base_state(wi=item(
                base_commit=base, checkpoints={"CP1": {"status": "COMPLETE"}})))
            body = self.verify(repo)
        self.assertTrue(body["result"]["healthy"])
        self.assertEqual(checks_by_id(body)["checkpoint_completions_provable"]["status"], "pass")

    def test_terminal_items_are_not_proven(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(
                phase="MILESTONE_COMPLETE", base_commit=repo.base,
                checkpoints={"CP1": {"status": "COMPLETE"}})))
            body = self.verify(repo)
        self.assertEqual(checks_by_id(body)["checkpoint_completions_provable"]["status"], "pass")

    def test_installation_record(self):
        for version, status in (("2.6.0", "fail"), (wp.WORKFLOW_RELEASE, "pass")):
            with h.ScratchRepo() as repo:
                write_state(repo, empty_state())
                record = repo.root / ws.INSTALLATION_RECORD_PATH
                record.parent.mkdir(parents=True)
                record.write_text(json.dumps({"schema_version": 1, "workflow_version": version}))
                body = self.verify(repo)
            self.assertEqual(checks_by_id(body)["installation_release_matches"]["status"], status, version)
            if status == "fail":
                self.assert_only_failure(body, "installation_release_matches")
            else:
                self.assertTrue(body["result"]["healthy"])

    def test_leaves_the_state_untouched(self):
        with h.ScratchRepo() as repo:
            path = write_state(repo, h.base_state(wi=item()))
            before = (path.read_bytes(), path.stat().st_mtime_ns)
            self.verify(repo)
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)
            self.assertFalse(ws.state_lock_path(repo.root).exists())


# ---------------------------------------------------------------------------
# resolve-artifact
# ---------------------------------------------------------------------------


class TestResolveArtifact(unittest.TestCase):
    def resolve(self, repo: h.ScratchRepo, work_item_id: str, kind: str) -> dict:
        body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                          "--work-item", work_item_id, "--kind", kind)
        self.assertEqual(code, wp.EXIT_OK, body)
        self.assertEqual(body["result"]["kind"], kind)
        return body["result"]

    def assert_matches_helpers(self, repo: h.ScratchRepo, work_item_id: str, *, plan_stage: bool) -> None:
        feedback_dir = fingerprint.resolve_feedback_dir(repo.root, work_item_id)
        expected = {
            "review_feedback": (feedback_dir / "REVIEW_FEEDBACK.md").as_posix(),
            "functional_review": (feedback_dir / "FUNCTIONAL_REVIEW.md").as_posix(),
            "review_bundle": fingerprint.resolve_bundle_dir(
                repo.root, work_item_id, stage="plan" if plan_stage else None).as_posix(),
            "plan_review_inputs": fingerprint.resolve_plan_review_inputs_dir(repo.root, work_item_id).as_posix(),
            "plan_document": "docs/plans/PLAN.md",
            "functional_checklist": ws.FUNCTIONAL_CHECKLIST_PATH,
        }
        self.assertEqual(set(expected), set(wp.ARTIFACT_KINDS))
        for kind, path in expected.items():
            result = self.resolve(repo, work_item_id, kind)
            self.assertEqual(result["path"], path, kind)
            self.assertEqual(result["exists"], (repo.root / path).exists(), kind)
            self.assertEqual(result["basis"]["work_item_id"], work_item_id)

    def test_scoped_item(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(feedback_layout="scoped", plan_path="docs/plans/PLAN.md")))
            self.assert_matches_helpers(repo, "wi", plan_stage=False)
            self.assertEqual(self.resolve(repo, "wi", "review_feedback")["path"],
                             ".ai-review/wi/feedback/REVIEW_FEEDBACK.md")

    def test_legacy_flat_item(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(plan_path="docs/plans/PLAN.md")))
            self.assert_matches_helpers(repo, "wi", plan_stage=False)
            self.assertEqual(self.resolve(repo, "wi", "review_feedback")["path"],
                             ".ai-review/feedback/REVIEW_FEEDBACK.md")
            self.assertEqual(self.resolve(repo, "wi", "review_bundle")["path"], ".ai-review/current")

    def test_plan_stage_phase(self):
        for phase in ("AWAITING_LOCAL_PLAN_REVIEW", "AWAITING_EXTERNAL_PLAN_REVIEW", "REVISING_PLAN"):
            with h.ScratchRepo() as repo:
                write_state(repo, h.base_state(wi=item(phase=phase, plan_path="docs/plans/PLAN.md")))
                self.assert_matches_helpers(repo, "wi", plan_stage=True)
                self.assertEqual(self.resolve(repo, "wi", "review_bundle")["path"], ".ai-review/wi/current")

    def test_exists_reflects_the_filesystem(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item(feedback_layout="scoped", plan_path="docs/plans/PLAN.md")))
            self.assertFalse(self.resolve(repo, "wi", "plan_document")["exists"])
            (repo.root / "docs" / "plans").mkdir(parents=True)
            (repo.root / "docs" / "plans" / "PLAN.md").write_text("plan\n")
            self.assertTrue(self.resolve(repo, "wi", "plan_document")["exists"])

    def test_no_plan_path(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item()))
            result = self.resolve(repo, "wi", "plan_document")
        self.assertIsNone(result["path"])
        self.assertFalse(result["exists"])

    def test_unknown_kind_is_invalid_request(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item()))
            body, code = call("--repo-root", str(repo.root), "resolve-artifact",
                              "--work-item", "wi", "--kind", "bundle_archive")
        self.assertEqual(code, wp.EXIT_INVALID_REQUEST)
        self.assertEqual(body["error"]["code"], "invalid_request")

    def test_leaves_the_state_untouched(self):
        with h.ScratchRepo() as repo:
            path = write_state(repo, h.base_state(wi=item(feedback_layout="scoped")))
            before = (path.read_bytes(), path.stat().st_mtime_ns)
            for kind in wp.ARTIFACT_KINDS:
                self.resolve(repo, "wi", kind)
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)
            self.assertFalse((repo.root / ".ai-review").exists())

    def test_reads_under_an_existing_lock_file(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=item()))
            with ws.state_lock(repo.root):
                pass
            self.assertTrue(ws.state_lock_path(repo.root).exists())
            self.assertIsNone(self.resolve(repo, "wi", "plan_document")["path"])


# ===========================================================================
# CP4: next-action and reconcile
# ===========================================================================

WI = "wi"
COMMANDS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "commands"

#: The catalogue's printed order (D-OP-Next's table, top to bottom).
PRINTED_ROW_ORDER = (
    "1", "1a", "2", "3", "4", "5", "6", "6a", "7", "7a", "8", "8a", "9", "10", "11", "11a", "12", "13",
    "14", "15", "16", "16a", "17", "18", "19", "20", "20a", "21", "22", "23", "24", "25", "25a", "25b",
    "26", "27", "28", "29", "30", "30a", "31", "31a", "32", "33", "34", "35", "35a", "36", "37", "38",
    "38a", "38b", "38c", "39", "40",
)


def next_action(repo: h.ScratchRepo, *extra: str) -> dict:
    """`next-action` in-process, schema-checked; every decision is also
    checked for the prose rules: each command its remedy or alternatives
    name is in exactly one of the row's `remedy_commands`/`refusing_commands`,
    and no remedy tells the operator to edit a verdict's binding fields."""
    body, code = call("--repo-root", str(repo.root), "next-action", *extra)
    assert code == 0, body
    result = body["result"]
    if "basis" in result and result["reason"]["code"] != "condition_refused":
        row = wp.ROWS_BY_ID[result["row"]]
        phase = result["snapshot"]["phase"]
        version = result["snapshot"]["governing_workflow_version"]
        named = prose_commands(result)
        remedies = set(row.remedy_commands_for(phase, version))
        refusing = set(row.refusing_commands)
        stray = {command for command in named if (command in remedies) == (command in refusing)}
        assert not stray, f"row {row.row_id} names {sorted(stray)} outside exactly one of its command fields"
        for text in (result["reason"]["remedy"] or "", result["reason"]["text"]):
            assert _EDIT_BINDING_FIELD_RE.search(text) is None, text
    return result


def verdict(status: str | None, *, rcid: str | None = None, bundle: str | None = None, base: str | None = None,
            work_item: str | None = WI, role: str | None = None, extra_body: str = "") -> str:
    lines = ["# Review Decision", ""]
    if status is not None:
        lines += [f"Status: {status}", ""]
    if role is not None:
        lines.append(f"Reviewer role: {role}")
    if bundle is not None:
        lines.append(f"Reviewed bundle ID: {bundle}")
    if base is not None:
        lines.append(f"Reviewed base commit: {base}")
    if work_item is not None:
        lines.append(f"Work item: {work_item}")
    if rcid is not None:
        lines.append(f"{fingerprint.FEEDBACK_REVIEW_CONTENT_ID_LABEL} {rcid}")
    lines += ["", "## Blocking findings", "", "None." + extra_body, ""]
    return "\n".join(lines)


def feedback_path(repo: h.ScratchRepo, name: str = "REVIEW_FEEDBACK.md") -> Path:
    return repo.root / ".ai-review" / WI / "feedback" / name


def write_feedback(repo: h.ScratchRepo, text: str, name: str = "REVIEW_FEEDBACK.md") -> None:
    path = feedback_path(repo, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def bundle_dir(repo: h.ScratchRepo) -> Path:
    return repo.root / ".ai-review" / WI / "current"


def current_bundle_id(repo: h.ScratchRepo) -> str:
    return fingerprint.compute_bundle_id(bundle_dir(repo))[0]


def edit_item(repo: h.ScratchRepo, **fields) -> dict:
    state = h.read_state(repo)
    state["work_items"][WI].update(fields)
    h.write_state(repo, state)
    return state


def mutate(repo: h.ScratchRepo, fn, *args, **kwargs) -> dict:
    state = fn(h.read_state(repo), WI, *args, **kwargs)
    h.write_state(repo, state)
    return state


def _demote_checkpoint(state: dict, work_item_id: str, checkpoint_id: str) -> dict:
    entry = state["work_items"][work_item_id]["checkpoints"][checkpoint_id]
    entry["status"] = "NEEDS_REVALIDATION"
    return state


def current_I(repo: h.ScratchRepo) -> str:
    return ws.approval_review_content_id(
        repo.root, stage="implementation", base_commit=h.read_state(repo)["work_items"][WI]["base_commit"],
        work_item_type="process", work_item_id=WI, head="HEAD",
        artifacts_path=fingerprint.artifacts_path_for_work_item(WI))


def reject_bundle(repo: h.ScratchRepo) -> None:
    marker = repo.root / fingerprint.resolve_rejected_marker_path(repo.root, WI)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("rejected by the test\n")


def minimal_item(phase: str, version: str, **overrides) -> dict:
    overrides.setdefault("base_commit", "0" * 40)
    overrides.setdefault("work_item_id", WI)
    return h.base_work_item(phase=phase, governing_workflow_version=version, **overrides)


# -- a bound two-stage plan item at each plan-review phase -----------------


def plan_item_at(repo: h.ScratchRepo, phase: str, version: str = "2.2") -> dict:
    """A two-stage item whose plan bundle is generated and bound, moved
    through the real ledger writers to `phase`. Returns
    `{"P": review_content_id, "B": bundle_id}`."""
    h.seed_bundle_item(repo, governing_workflow_version=version, phase="PLANNING")
    P, B = h.publish_and_bind_plan_bundle(repo)
    if phase in ("AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW", "AWAITING_PLAN_APPROVAL"):
        mutate(repo, ws.record_local_plan_review, verdict="APPROVE", bundle_id=B, review_content_id=P,
               round=1, now="t-local")
    if phase == "AWAITING_PLAN_APPROVAL":
        mutate(repo, ws.record_manual_plan_review, verdict="APPROVE", bundle_id=B, round=1, now="t-manual",
               current_review_content_id=P, feedback_role="MANUAL_EXTERNAL_PLAN_REVIEW",
               feedback_review_content_id=P)
        write_feedback(repo, verdict("APPROVE", rcid=P, bundle=B, base=repo.base,
                                     role="MANUAL_EXTERNAL_PLAN_REVIEW"))
    if phase == "REVISING_PLAN":
        mutate(repo, ws.record_local_plan_review, verdict="REVISE", bundle_id=B, review_content_id=P,
               round=1, now="t-local")
    assert h.read_state(repo)["work_items"][WI]["phase"] == phase
    return {"P": P, "B": B}


def implementation_item_at(repo: h.ScratchRepo, version: str = "2.2", *, registry_checkpoints=None) -> dict:
    """An item whose first implementation bundle is generated from
    `SELF_REVIEWING_IMPLEMENTATION` (2.2: `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`;
    1/2.1: `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`). Returns `{"I", "B"}`."""
    h.seed_bundle_item(repo, governing_workflow_version=version, phase="SELF_REVIEWING_IMPLEMENTATION",
                       registry_checkpoints=registry_checkpoints)
    repo.commit("implement", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
    I = h.generate_implementation_bundle(repo)
    return {"I": I, "B": current_bundle_id(repo)}


def implementation_at_manual(repo: h.ScratchRepo) -> dict:
    ids = implementation_item_at(repo, "2.2")
    mutate(repo, ws.record_local_implementation_review, verdict="APPROVE", bundle_id=ids["B"],
           review_content_id=ids["I"], round=1, now="t-local")
    return ids


def implementation_at_external_2_2(repo: h.ScratchRepo) -> dict:
    ids = implementation_at_manual(repo)
    mutate(repo, ws.record_manual_implementation_review, verdict="APPROVE", bundle_id=ids["B"], round=1,
           now="t-manual", current_review_content_id=ids["I"], feedback_role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW",
           feedback_review_content_id=ids["I"])
    write_feedback(repo, verdict("APPROVE", rcid=ids["I"], bundle=ids["B"], base=repo.base,
                                 role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"))
    return ids


def applying_2_2(repo: h.ScratchRepo) -> dict:
    """A `"2.2"` item at `APPLYING_REVIEW_FEEDBACK` after a local `REVISE`."""
    ids = implementation_item_at(repo, "2.2")
    mutate(repo, ws.record_local_implementation_review, verdict="REVISE", bundle_id=ids["B"],
           review_content_id=ids["I"], round=1, now="t-local")
    h.commit_state(repo, "record the local REVISE")
    return ids


# ---------------------------------------------------------------------------
# The catalogue's structure
# ---------------------------------------------------------------------------


class TestCatalogueStructure(unittest.TestCase):
    def test_the_catalogue_is_one_list_in_the_printed_order(self):
        self.assertIsInstance(wp.CATALOGUE, list)
        self.assertEqual(wp.ROW_IDS, PRINTED_ROW_ORDER)
        self.assertEqual(len(set(wp.ROW_IDS)), len(wp.ROW_IDS))

    def test_supported_governing_versions_are_the_two_stage_set_plus_1(self):
        self.assertEqual(sorted(wp.SUPPORTED_GOVERNING_VERSIONS),
                         sorted({"1"} | ws.TWO_STAGE_PLAN_REVIEW_VERSIONS))
        self.assertIn("2.2", wp.SUPPORTED_GOVERNING_VERSIONS)

    def test_every_phase_and_version_reaches_an_unconditional_row(self):
        """Totality, structurally: enumerated from `KNOWN_PHASES` and
        `SUPPORTED_GOVERNING_VERSIONS`, every pair has an explicit
        unconditional row, so nothing can fall through."""
        for phase in sorted(ws.KNOWN_PHASES):
            for version in wp.SUPPORTED_GOVERNING_VERSIONS:
                with self.subTest(phase=phase, version=version):
                    rows = [row for row in wp.CATALOGUE if not row.no_item and row.covers(phase, version)]
                    self.assertTrue(rows, "no row covers the pair")
                    self.assertTrue(any(row.unconditional for row in rows), [row.row_id for row in rows])

    def test_every_phase_and_version_decides_in_a_default_config_repository(self):
        """Totality, dynamically, in a repository whose config is
        `default_config()` (`["1","2.1"]`): the `2.2` rows are still
        enumerated, and every state ends at an explicit row that covers it."""
        self.assertEqual(ws.default_config()["supported_versions"], ["1", "2.1"])
        with h.ScratchRepo() as repo:
            config_path = repo.root / ws.DEFAULT_CONFIG_PATH
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(json.dumps(ws.default_config()))
            for phase in sorted(ws.KNOWN_PHASES):
                for version in wp.SUPPORTED_GOVERNING_VERSIONS:
                    with self.subTest(phase=phase, version=version):
                        write_state(repo, h.base_state(wi=minimal_item(phase, version, base_commit=repo.base)))
                        result = next_action(repo, "--work-item", WI)
                        self.assertTrue(wp.ROWS_BY_ID[result["row"]].covers(phase, version), result["row"])

    def test_condition_calls_cover_exactly_the_rows(self):
        self.assertEqual(set(wp.CONDITION_CALLS), set(wp.ROW_IDS))

    def test_condition_calls_are_well_formed(self):
        domain = {cls.__name__ for module in (ws, fingerprint) for cls in workflow_exception_classes(module)}
        for row_id, calls in wp.CONDITION_CALLS.items():
            for entry in calls:
                with self.subTest(row=row_id, function=entry["function"]):
                    self.assertIn(entry["kind"], ("guard", "acceptance", "value"))
                    self.assertTrue(callable(wp._fn(entry["function"])))
                    for name in entry["classes"]:
                        self.assertIn(name, domain)
                    if entry["kind"] in ("guard", "acceptance"):
                        self.assertTrue(entry["classes"], "a guard or acceptance call lists its classes")

    def test_rows_without_a_condition_have_an_empty_entry(self):
        for row_id in ("2", "3", "4", "6a", "7", "9", "12", "14", "21", "24", "26", "28", "36", "40"):
            self.assertEqual(wp.CONDITION_CALLS[row_id], [], row_id)

    def test_illegal_pairs_are_row_4s(self):
        row_4 = wp.ROWS_BY_ID["4"]
        self.assertIn(("REVISING_PLAN", "1"), row_4.pairs)
        self.assertIn(("SELF_REVIEWING_IMPLEMENTATION", "1"), row_4.pairs)
        self.assertIn(("AWAITING_EXTERNAL_PLAN_REVIEW", "2.2"), row_4.pairs)
        self.assertNotIn(("AWAITING_EXTERNAL_PLAN_REVIEW", "1"), row_4.pairs)


class TestActionsAndEdges(unittest.TestCase):
    def test_action_ids_are_the_action_table(self):
        self.assertEqual(wp.ACTION_IDS, tuple(sorted(wp.ACTIONS)))
        emitted = {row.action_id for row in wp.CATALOGUE if row.action_id}
        self.assertLessEqual(emitted, set(wp.ACTIONS))

    def test_user_only_actions_are_the_users_and_never_automatic(self):
        for action_id, spec in wp.ACTIONS.items():
            if spec["user_only"]:
                self.assertEqual(spec["role"], "user", action_id)
        for row in wp.CATALOGUE:
            if row.disposition == "automatic":
                self.assertFalse(wp.ACTIONS[row.action_id]["user_only"], row.row_id)

    def test_user_only_matches_the_command_files_flag(self):
        """Replaces the Controller's scan for `disable-model-invocation`;
        covers `implementation.recover_provenance`, which is not user-only."""
        for action_id, spec in wp.ACTIONS.items():
            if spec["command"] is None:
                continue
            with self.subTest(action=action_id):
                text = (COMMANDS_DIR / f"{spec['command']}.md").read_text()
                frontmatter = text.split("---", 2)[1]
                self.assertEqual("disable-model-invocation: true" in frontmatter, spec["user_only"])
        self.assertFalse(wp.ACTIONS["implementation.recover_provenance"]["user_only"])

    def test_every_automatic_row_has_an_edge_entry(self):
        automatic = {row.action_id for row in wp.CATALOGUE if row.disposition == "automatic"}
        self.assertEqual(automatic, set(wp.EDGES))
        self.assertEqual(set(wp.AUTOMATIC_ACTION_IDS), automatic)

    def test_every_edge_names_known_phases_legal_for_its_version(self):
        for action_id, entry in wp.EDGES.items():
            for edge in entry["edges"]:
                for phase in (edge["from"], edge["to"]):
                    if phase is None:
                        continue
                    with self.subTest(action=action_id, edge=edge):
                        self.assertIn(phase, ws.KNOWN_PHASES)
                        for version in edge["versions"]:
                            self.assertTrue(wp.phase_legal_for_version(phase, version), (phase, version))

    def test_allowed_results_are_reconcile_classes_and_next_action_copies_them(self):
        for action_id, entry in wp.EDGES.items():
            self.assertLessEqual(set(entry["allowed_results"]), set(wp.RECONCILE_CLASSES) - {"invalid"})
            self.assertEqual(wp.render_action(action_id, WI)["allowed_results"], entry["allowed_results"])
        self.assertNotIn("gate_reached", wp.EDGES["implementation.checkpoint"]["allowed_results"])

    def test_functional_apply_findings_edges_follow_the_post_fix_target(self):
        for version in wp.SUPPORTED_GOVERNING_VERSIONS:
            target = ws.bundle_generation_target_phase("post-fix", version)
            self.assertTrue(wp.edge_is_legal("functional.apply_findings", "AWAITING_FUNCTIONAL_REVIEW", target, version))


_EDIT_BINDING_FIELD_RE = re.compile(
    r"\b(edit|change|set|rewrite|update|replace)\b[^.;]*\b(Reviewed bundle ID|Reviewed base commit|Work item:)",
    re.IGNORECASE)


def assert_no_binding_field_edit(test: unittest.TestCase, result: dict) -> None:
    """No catalogue remedy tells the operator to edit a verdict's binding
    fields (`MPR-R9-001`)."""
    for text in (result["reason"]["remedy"] or "", result["reason"]["text"]):
        test.assertIsNone(_EDIT_BINDING_FIELD_RE.search(text), text)


def write_config(repo: h.ScratchRepo, default: str) -> None:
    path = repo.root / ws.DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "default_workflow_version": default,
                                "supported_versions": ["1", "2.1", "2.2"]}))


def move_head(repo: h.ScratchRepo, subject: str = "unrelated state-only commit") -> str:
    """An excluded-only commit (the state file alone): HEAD moves past the
    bundle's `generation_head`, the protected content does not."""
    state = h.read_state(repo)
    state["work_items"][WI]["last_transition"] = subject
    h.write_state(repo, state)
    return h.commit_state(repo, subject)


def regenerate_wrapper_only(repo: h.ScratchRepo) -> str:
    """A wrapper-only regeneration: the same content, a new `bundle_id`."""
    before = current_bundle_id(repo)
    (bundle_dir(repo) / "TEST_RESULTS.md").write_text(
        f"stage: plan (revision 1)\nhead: {repo.head()}\nwrapper-only rerun\n")
    h._run_generator(repo, "plan", WI)
    after = current_bundle_id(repo)
    assert before != after
    return after


class TestNoItemRows(unittest.TestCase):
    def test_two_stage_default_gives_plan_start(self):
        with h.ScratchRepo() as repo:
            write_config(repo, "2.2")
            write_state(repo, h.base_state())
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["action"]["id"]),
                             ("1", "automatic", "plan.start"))
            self.assertEqual(result["action"]["invocation"], "/milestone-plan")
            self.assertNotIn("basis", result)
            self.assertEqual(result["snapshot"], {"work_item_ids": []})

    def test_a_v1_default_gives_row_1a_never_plan_start(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(other=minimal_item("MILESTONE_COMPLETE", "1", work_item_id="other")))
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                             ("1a", "blocked", "plan_start_not_tracked"))
            self.assertIsNone(result["action"])
            self.assertEqual(result["snapshot"], {"work_item_ids": ["other"]})

    def test_expect_state_identity_with_no_item_is_invalid_request(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state())
            body, code = call("--repo-root", str(repo.root), "next-action", "--expect-state-identity", "0" * 64)
            self.assertEqual((code, body["error"]["code"]), (2, "invalid_request"))


class TestFixedRows(unittest.TestCase):
    def decide_minimal(self, phase: str, version: str) -> dict:
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=minimal_item(phase, version, base_commit=repo.base)))
            return next_action(repo, "--work-item", WI)

    def test_vocabulary_only_phases_are_row_2(self):
        for phase in sorted(wp.VOCABULARY_ONLY_PHASES):
            result = self.decide_minimal(phase, "2.2")
            self.assertEqual((result["row"], result["reason"]["code"]), ("2", "invalid_state"))

    def test_legacy_ready_is_row_3(self):
        result = self.decide_minimal("LEGACY_READY", "1")
        self.assertEqual((result["row"], result["reason"]["code"]), ("3", "legacy_item_not_activated"))

    def test_every_illegal_pair_is_row_4(self):
        for phase, versions in sorted(wp.ILLEGAL_PHASE_VERSIONS.items()):
            for version in sorted(versions):
                with self.subTest(phase=phase, version=version):
                    result = self.decide_minimal(phase, version)
                    self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                                     ("4", "blocked", "phase_not_legal_for_governing_version"))

    def test_milestone_complete_is_row_40(self):
        result = self.decide_minimal("MILESTONE_COMPLETE", "2.2")
        self.assertEqual((result["row"], result["disposition"], result["action"]), ("40", "complete", None))

    def test_v1_planning_amending_and_implementing_are_row_6a(self):
        for phase in ("PLANNING", "AMENDING_PLAN", "IMPLEMENTING"):
            with self.subTest(phase=phase), h.ScratchRepo() as repo:
                h.seed_bundle_item(repo, governing_workflow_version="1", phase=phase,
                                   registry_checkpoints=[{"id": "C1", "depends_on": []}])
                result = next_action(repo)
                self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                                 ("6a", "blocked", "v1_state_not_advanced"))
                self.assertIsNone(result["action"])
                self.assertIn("v2.6.0-003", result["reason"]["remedy"])

    def test_v1_self_reviewing_implementation_is_row_4(self):
        self.assertEqual(self.decide_minimal("SELF_REVIEWING_IMPLEMENTATION", "1")["row"], "4")

    def test_an_unsupported_governing_version_is_not_applicable(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=minimal_item("PLANNING", "9.9", base_commit=repo.base)))
            body, code = call("--repo-root", str(repo.root), "next-action", "--work-item", WI)
            self.assertEqual((code, body["error"]["code"]), (3, "not_applicable"))


class TestTwoStagePlanRows(unittest.TestCase):
    def test_planning_is_plan_author(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, phase="PLANNING")
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"], result["action"]["invocation"]),
                             ("7", "plan.author", f"/milestone-plan {WI}"))
            self.assertEqual(result["action"]["worker"]["role"], "planner")

    def test_local_review_is_row_12(self):
        for version in ("2.1", "2.2"):
            with self.subTest(version=version), h.ScratchRepo() as repo:
                plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW", version)
                result = next_action(repo)
                self.assertEqual((result["row"], result["action"]["id"]), ("12", "plan.review.local"))
                self.assertEqual(result["action"]["worker"],
                                 {"role": "independent_reviewer", "fresh_session": True,
                                  "independent_of": ["planner"], "user_only": False})
                self.assertEqual(result["snapshot"]["plan_review_publication_status"], "BOUND")

    def test_an_inconsistent_binding_is_row_5(self):
        """Publication row 6 (a non-ready phase with a BOUND record) offers
        no withdrawal, since `/milestone-plan`'s writers refuse it too;
        publication row 4d (a ready phase without BOUND) does."""
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            edit_item(repo, phase="REVISING_PLAN")
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("5", "plan_review_binding_inconsistent"))
            self.assertEqual(result["alternatives"], [])
            with self.assertRaises(ws.PlanReviewBindingInconsistentError):
                ws.publish_plan_revision(h.read_state(repo), WI, 1, "t", review_content_id="e" * 64)
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "REVISING_PLAN")
            edit_item(repo, phase="AWAITING_LOCAL_PLAN_REVIEW")
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("5", "plan_review_binding_inconsistent"))
            self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.withdraw"])

    def test_a_rejected_bundle_is_row_6_at_every_review_and_apply_phase(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"], bundle=ids["B"], base=repo.base))
            self.assertEqual(next_action(repo)["row"], "8")
            reject_bundle(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("6", "bundle_rejected"))
            self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.withdraw"])
        for version in wp.SUPPORTED_GOVERNING_VERSIONS:
            with self.subTest(version=version), h.ScratchRepo() as repo:
                write_state(repo, h.base_state(wi=minimal_item("APPLYING_REVIEW_FEEDBACK", version,
                                                               base_commit=repo.base, feedback_layout="scoped")))
                reject_bundle(repo)
                result = next_action(repo, "--work-item", WI)
                self.assertEqual((result["row"], result["alternatives"]), ("6", []))

    def test_content_drift_at_a_ready_phase_is_row_10(self):
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            plan = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
            plan.write_text(plan.read_text() + "drift\n")
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("10", "content_drifted"))
            self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.withdraw"])

    def test_a_current_block_is_review_resolve_block_at_both_review_phases(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            write_feedback(repo, verdict("BLOCK", rcid=ids["P"], bundle=ids["B"], base=repo.base,
                                         role="LOCAL_MODEL_PLAN_REVIEW"))
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["action"]["id"]),
                             ("11", "human_gate", "review.resolve_block"))
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
            write_feedback(repo, verdict("BLOCK", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW", work_item=None))
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"], result["reason"]["code"]),
                             ("11", "review.resolve_block", "review_blocked"))

    def test_manual_phase_without_and_with_an_unrecorded_verdict(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["satisfied_by"]),
                             ("14", "external_gate", "plan_review_verdict"))
            write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW", work_item=None))
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("13", "plan.record_external"))
            # A local verdict, or one for other content, is not an unrecorded manual verdict.
            write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="LOCAL_MODEL_PLAN_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "14")
            write_feedback(repo, verdict("APPROVE", rcid="e" * 64, role="MANUAL_EXTERNAL_PLAN_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "14")

    def test_a_wrapper_only_regeneration_keeps_rows_11_to_14(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            regenerate_wrapper_only(repo)
            self.assertEqual(next_action(repo)["row"], "12")
            write_feedback(repo, verdict("BLOCK", rcid=ids["P"], bundle=ids["B"], base=repo.base))
            self.assertEqual(next_action(repo)["row"], "11")
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
            regenerate_wrapper_only(repo)
            self.assertEqual(next_action(repo)["row"], "14")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"], bundle=ids["B"],
                                         role="MANUAL_EXTERNAL_PLAN_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "13")
            write_feedback(repo, verdict("BLOCK", rcid=ids["P"], bundle=ids["B"],
                                         role="MANUAL_EXTERNAL_PLAN_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "11")

    def test_head_moved_past_generation_head_is_row_11a(self):
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            move_head(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("11a", "bundle_generation_mismatch"))
            self.assertIn(f"prepare-ai-review.sh {repo.base} plan {WI}", result["reason"]["remedy"])
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
            move_head(repo)
            self.assertEqual(next_action(repo)["row"], "14", "no fb: row 14 is unaffected")
            write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "11a")

    def test_a_different_worktree_root_is_row_11a(self):
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            other = repo.root.parent / (repo.root.name + "-wt")
            h.git(repo, "worktree", "add", "-q", "--detach", str(other), "HEAD")
            try:
                shutil.copytree(repo.root / ".ai-review", other / ".ai-review")
                shutil.copy(repo.root / ws.DEFAULT_STATE_PATH, other / ws.DEFAULT_STATE_PATH)
                body, code = call("--repo-root", str(other), "next-action")
                self.assertEqual((body["result"]["row"], body["result"]["reason"]["code"]),
                                 ("11a", "bundle_generation_mismatch"))
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(other)], cwd=repo.root,
                               capture_output=True)
                shutil.rmtree(other, ignore_errors=True)

    def test_the_plan_approval_gate(self):
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_PLAN_APPROVAL")
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["action"]["id"]),
                             ("15", "human_gate", "plan.approve"))
            self.assertEqual(result["action"]["invocation"], f"/approve-review plan {WI}")
            self.assertEqual(result["action"]["worker"]["user_only"], True)

    def test_the_plan_gate_unreachable_causes_are_row_16(self):
        def check(mutation, cause):
            with h.ScratchRepo() as repo:
                ids = plan_item_at(repo, "AWAITING_PLAN_APPROVAL")
                mutation(repo, ids)
                result = next_action(repo)
                self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                                 ("16", "blocked", cause))
                self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.withdraw"])

        check(lambda repo, ids: feedback_path(repo).unlink(), "no_review_round")
        check(lambda repo, ids: write_feedback(repo, verdict("BLOCK", rcid=ids["P"])), "review_blocked")
        check(lambda repo, ids: edit_item(repo, plan_review_stages=dict(
            h.read_state(repo)["work_items"][WI]["plan_review_stages"], review_content_id="d" * 64)),
            "review_ledger_stale")
        check(lambda repo, ids: move_head(repo), "bundle_generation_mismatch")


class TestRevisingPlanRows(unittest.TestCase):
    """Rows 7a, 8, 8a and 9, and the content binding (D-Apply-Binding)."""

    def apply_sequence(self, repo: h.ScratchRepo) -> dict:
        """`/apply-plan-review`'s step-0/step-1 guard sequence, before any
        write: the entry phase, the feedback file, the `REJECTED` marker, the
        acceptance rule, and the binding in `"bundle"` mode."""
        state = h.read_state(repo)
        work_item = state["work_items"][WI]
        ws.assert_plan_review_entry_phase(work_item, WI, command="/apply-plan-review")
        text = feedback_path(repo).read_text()
        fingerprint.assert_bundle_not_rejected(repo.root, WI)
        status = ws.plan_review_publication_status(repo.root, state, WI)["status"]
        mode = ws.assert_apply_plan_review_feedback(work_item, WI, feedback_content=text, publication_status=status)
        if mode == "bundle":
            return ws.assert_apply_review_feedback_binding(repo.root, work_item, WI, stage="plan",
                                                           feedback_content=text)
        return {"binding": "durable"}

    def test_a_recorded_revise_is_applied_whatever_its_bundle_fields_say(self):
        variants = {
            "full": lambda ids, repo: verdict("REVISE", rcid=ids["P"], bundle=ids["B"], base=repo.base),
            "no bundle fields": lambda ids, repo: verdict("REVISE", rcid=ids["P"], work_item=None),
            "stale bundle id": lambda ids, repo: verdict("REVISE", rcid=ids["P"], bundle="f" * 64, base=repo.base),
        }
        for version in ("2.1", "2.2"):
            for name, build in variants.items():
                with self.subTest(version=version, variant=name), h.ScratchRepo() as repo:
                    ids = plan_item_at(repo, "REVISING_PLAN", version)
                    write_feedback(repo, build(ids, repo))
                    result = next_action(repo)
                    self.assertEqual((result["row"], result["action"]["id"]), ("8", "plan.apply_review"))
                    binding = self.apply_sequence(repo)
                    self.assertEqual(binding["binding"], "content")
                    if name == "stale bundle id":
                        self.assertIn("advisory only", binding["advisory"])
                    else:
                        self.assertIsNone(binding["advisory"])

    def test_after_a_wrapper_only_regeneration_the_old_bundle_id_is_advisory(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            # The consumed round's bundle, regenerated wrapper-only before the REVISE was recorded.
            write_feedback(repo, verdict("REVISE", rcid=ids["P"], bundle=ids["B"], base=repo.base))
            (bundle_dir(repo) / "TEST_RESULTS.md").write_text("wrapper-only\n")
            # The manifest no longer matches the edited file: that is row 7a, not a binding refusal.
            self.assertEqual(next_action(repo)["row"], "7a")

    def test_a_legacy_marker_is_row_8_by_work_item(self):
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "REVISING_PLAN")
            state = h.read_state(repo)
            work_item = state["work_items"][WI]
            work_item["plan_review_binding"]["consumed"] = {"review_content_id": None, "plan_revision": 1, "legacy": True}
            work_item.pop(ws.CONSUMED_PLAN_REVIEW_CONTENT_IDS_KEY, None)
            h.write_state(repo, state)
            write_feedback(repo, verdict("REVISE"))
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("8", "plan.apply_review"))
            self.assertEqual(self.apply_sequence(repo)["binding"], "durable")

    def test_a_withdrawal_and_a_stale_verdict_are_row_9(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            mutate(repo, ws.withdraw_plan_review, "t-withdraw")
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("9", "plan.author"))
            # A prior round's REVISE (other content): FeedbackContentMismatchError.
            write_feedback(repo, verdict("REVISE", rcid="c" * 64, bundle=ids["B"], base=repo.base))
            self.assertEqual(next_action(repo)["row"], "9")
            # A local APPROVE left behind: FeedbackStatusNotApplicableError.
            write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="LOCAL_MODEL_PLAN_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "9")

    def test_published_unbound_with_feedback_for_other_content_is_row_9(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            plan = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
            plan.write_text(plan.read_text() + "edited after the REVISE\n")
            fresh, _ = fingerprint.compute_review_content_id_plan_stage_for_work_item(repo.root, WI)
            mutate(repo, ws.publish_plan_revision, 1, "t-publish", review_content_id=fresh)
            state = h.read_state(repo)
            self.assertEqual(ws.plan_review_publication_status(repo.root, state, WI)["status"], "PUBLISHED_UNBOUND")
            write_feedback(repo, verdict("REVISE", rcid="c" * 64))
            self.assertEqual(next_action(repo)["row"], "9")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
            self.assertEqual(next_action(repo)["row"], "8", "durable: the consumed content's REVISE applies")

    def test_the_forgery_is_refused_and_gives_row_9(self):
        """MPR-R9-001: bundle fields rewritten to B, the base and the id,
        over a review_content_id that is not the reviewed content."""
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            write_feedback(repo, verdict("REVISE", rcid="c" * 64, bundle=ids["B"], base=repo.base))
            with self.assertRaises(ws.FeedbackContentMismatchError):
                self.apply_sequence(repo)
            self.assertEqual(next_action(repo)["row"], "9")

    def test_a_bundle_of_other_content_is_row_7a(self):
        with h.ScratchRepo() as other:
            plan_item_at(other, "AWAITING_LOCAL_PLAN_REVIEW")
            plan = other.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
            plan.write_text(plan.read_text() + "another revision\n")
            h.git(other, "add", "-A")
            h.git(other, "commit", "-q", "-m", "another revision")
            h.generate_plan_bundle(other)
            with h.ScratchRepo() as repo:
                ids = plan_item_at(repo, "REVISING_PLAN")
                write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
                shutil.rmtree(bundle_dir(repo))
                shutil.copytree(bundle_dir(other), bundle_dir(repo))
                with self.assertRaises(ws.ReviewBundleManifestMismatchError):
                    self.apply_sequence(repo)
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("7a", "bundle_unverified"))
                self.assertIn("ReviewBundleManifestMismatchError", result["reason"]["text"])
                self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.withdraw"])

    def test_a_missing_bundle_directory_is_row_7a(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
            shutil.rmtree(bundle_dir(repo))
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("7a", "bundle_unverified"))
            self.assertIn("MissingRequiredBundleFileError", result["reason"]["text"])

    def test_a_tampered_bundle_is_row_7a(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
            (bundle_dir(repo) / "PLAN.md").write_text("tampered\n")
            self.assertEqual(next_action(repo)["row"], "7a")

    def test_an_unbindable_revise_is_row_8a(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            for text in (verdict("REVISE"),  # names the item, no rcid, no bundle fields
                         verdict("REVISE", bundle="f" * 64, base=repo.base)):  # a bundle id that is not B
                with self.subTest(text=text):
                    write_feedback(repo, text)
                    result = next_action(repo)
                    self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                                     ("8a", "blocked", "review_feedback_unbound"))
                    self.assertIn(ids["B"], result["reason"]["text"])
                    self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.withdraw"])
                    assert_no_binding_field_edit(self, result)
                    with self.assertRaises((fingerprint.MissingFeedbackBindingFieldError,
                                            fingerprint.FeedbackBundleMismatchError)):
                        self.apply_sequence(repo)
            # A verdict that names no item and states no rcid is no applicable REVISE.
            write_feedback(repo, verdict("REVISE", work_item=None))
            self.assertEqual(next_action(repo)["row"], "9")

    def test_a_manifest_naming_no_work_item_selects_the_bundle_binding(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            manifest = bundle_dir(repo) / "MANIFEST.md"
            manifest.write_text("\n".join(line for line in manifest.read_text().splitlines()
                                          if not line.startswith("work_item_id:")) + "\n")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"], work_item=WI))
            state = h.read_state(repo)
            self.assertEqual(ws.apply_review_feedback_binding_selection(
                repo.root, state["work_items"][WI], WI, stage="plan",
                feedback_content=feedback_path(repo).read_text()), "bundle")
            self.assertEqual(next_action(repo)["row"], "8a")

    def test_an_unrecorded_revise_then_a_withdrawal_is_row_8(self):
        """MPR-R9-002: a manual REVISE of the bound content pasted but never
        recorded, then `/milestone-plan <id>`'s withdrawal."""
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW"))
            mutate(repo, ws.withdraw_plan_review, "t-withdraw")
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("8", "plan.apply_review"))
            self.assertEqual(self.apply_sequence(repo)["binding"], "content")
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            # /review-plan wrote its REVISE file, then its state write failed.
            write_feedback(repo, verdict("REVISE", rcid=ids["P"], bundle=ids["B"], base=repo.base,
                                         role="LOCAL_MODEL_PLAN_REVIEW"))
            mutate(repo, ws.withdraw_plan_review, "t-withdraw")
            self.assertEqual(next_action(repo)["row"], "8")
            self.apply_sequence(repo)


class TestV1PlanRound(unittest.TestCase):
    """Rows 16a to 21: a `"1"` item at `AWAITING_EXTERNAL_PLAN_REVIEW`."""

    def v1_plan(self, repo: h.ScratchRepo) -> str:
        h.seed_bundle_item(repo, governing_workflow_version="1", phase="AWAITING_EXTERNAL_PLAN_REVIEW")
        h.generate_plan_bundle(repo)
        return current_bundle_id(repo)

    def apply_writer_sequence(self, repo: h.ScratchRepo) -> None:
        """`/apply-plan-review`'s `"1"` writers: an edit, then the plan
        bundle's regeneration (a new **B**)."""
        audit = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_AUDIT.md"
        audit.write_text(audit.read_text() + "applied finding\n")
        h.generate_plan_bundle(repo)

    def test_no_feedback_is_row_21(self):
        with h.ScratchRepo() as repo:
            self.v1_plan(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["satisfied_by"]),
                             ("21", "external_gate", "plan_review_verdict"))

    def test_a_current_revise_is_row_18_and_after_the_apply_row_20(self):
        with h.ScratchRepo() as repo:
            B = self.v1_plan(repo)
            write_feedback(repo, verdict("REVISE", bundle=B, base=repo.base))
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("18", "plan.apply_review"))
            self.apply_writer_sequence(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["action"]["id"]),
                             ("20", "human_gate", "plan.approve"))
            self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.review.external"])
            self.assertEqual(result["alternatives"][0]["satisfied_by"], "plan_review_verdict")

    def test_a_current_approve_is_row_19(self):
        with h.ScratchRepo() as repo:
            B = self.v1_plan(repo)
            write_feedback(repo, verdict("APPROVE", bundle=B, base=repo.base))
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("19", "plan.approve"))
            self.assertTrue(result["action"]["worker"]["user_only"])

    def test_a_current_block_is_row_17_and_after_the_apply_row_21(self):
        with h.ScratchRepo() as repo:
            B = self.v1_plan(repo)
            write_feedback(repo, verdict("BLOCK", bundle=B, base=repo.base))
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["action"]["id"],
                              result["reason"]["code"]), ("17", "automatic", "plan.apply_review", "review_blocked"))
            self.apply_writer_sequence(repo)
            self.assertEqual(next_action(repo)["row"], "21")

    def test_the_gate_unreachable_is_row_20a(self):
        with h.ScratchRepo() as repo:
            B = self.v1_plan(repo)
            write_feedback(repo, verdict("APPROVE", bundle=B, base=repo.base))
            move_head(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("20a", "bundle_generation_mismatch"))
            self.assertEqual([a["id"] for a in result["alternatives"]], ["plan.review.external"])

    def test_a_stale_feedback_reaches_20_or_21_through_the_acceptance_call(self):
        """`LPR-R5-001`: through real states, never `condition_refused`."""
        with h.ScratchRepo() as repo:
            self.v1_plan(repo)
            write_feedback(repo, verdict("REVISE", bundle="f" * 64, base=repo.base))
            self.assertEqual(next_action(repo)["row"], "20")
            write_feedback(repo, verdict("APPROVE", bundle="f" * 64, base=repo.base))
            self.assertEqual(next_action(repo)["row"], "21")
            write_feedback(repo, verdict("APPROVE", bundle=current_bundle_id(repo)))  # no base commit line
            self.assertEqual(next_action(repo)["row"], "21")

    def test_a_missing_plan_bundle_is_row_16a(self):
        with h.ScratchRepo() as repo:
            self.v1_plan(repo)
            shutil.rmtree(bundle_dir(repo))
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("16a", "bundle_unverified"))
            self.assertIn(f"prepare-ai-review.sh {repo.base} plan {WI}", result["reason"]["remedy"])


class TestImplementingRows(unittest.TestCase):
    CHECKPOINTS = [{"id": "C1", "depends_on": []}, {"id": "C2", "depends_on": ["C1"]}]

    def implementing(self, repo: h.ScratchRepo, version: str = "2.2", phase: str = "IMPLEMENTING") -> None:
        h.seed_bundle_item(repo, governing_workflow_version=version, phase=phase,
                           registry_checkpoints=self.CHECKPOINTS)
        h.approve_plan(repo)

    def test_an_incomplete_registry_is_implementation_checkpoint(self):
        for version in ("2.1", "2.2"):
            with self.subTest(version=version), h.ScratchRepo() as repo:
                self.implementing(repo, version)
                result = next_action(repo)
                self.assertEqual((result["row"], result["action"]["id"]), ("23", "implementation.checkpoint"))
                self.assertEqual(result["action"]["arguments"], {"work_item_id": WI, "checkpoint_id": "C1"})
                self.assertEqual(result["action"]["allowed_results"], ["progress", "no_progress"])
                self.assertEqual(result["snapshot"]["next_checkpoint_id"], "C1")
                self.assertIs(result["snapshot"]["registry_complete"], False)

    def test_a_complete_registry_and_self_reviewing_are_self_review(self):
        with h.ScratchRepo() as repo:
            self.implementing(repo)
            edit_item(repo, checkpoints={"C1": {"status": "COMPLETE", "start_commit": repo.base},
                                         "C2": {"status": "COMPLETE", "start_commit": repo.base}})
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"], result["action"]["worker"]["role"]),
                             ("24", "implementation.self_review", "self_reviewer"))
            edit_item(repo, phase="SELF_REVIEWING_IMPLEMENTATION")
            self.assertEqual(next_action(repo)["row"], "24")

    def test_the_implementing_entry_causes_are_row_22(self):
        for phase in ("IMPLEMENTING", "SELF_REVIEWING_IMPLEMENTATION"):
            for version in ("2.1", "2.2"):
                with self.subTest(phase=phase, version=version):
                    with h.ScratchRepo() as repo:
                        self.implementing(repo, version, phase)
                        approval = h.read_state(repo)["work_items"][WI]["plan_approval"]
                        edit_item(repo, plan_approval=dict(approval, status="STALE"))
                        result = next_action(repo)
                        self.assertEqual((result["row"], result["reason"]["code"]), ("22", "plan_approval_not_current"))
                    with h.ScratchRepo() as repo:
                        self.implementing(repo, version, phase)
                        plan = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
                        plan.write_text(plan.read_text() + "edited after approval\n")
                        h.git(repo, "add", "-A")
                        h.git(repo, "commit", "-q", "-m", "edit the approved plan")
                        result = next_action(repo)
                        self.assertEqual((result["row"], result["reason"]["code"]), ("22", "plan_content_drifted"))
                        self.assertIn(f"/request-plan-amendment {WI}", result["reason"]["remedy"])
                    with h.ScratchRepo() as repo:
                        self.implementing(repo, version, phase)
                        state = h.read_state(repo)
                        h.git(repo, "checkout", "-q", "--detach", repo.base)
                        h.write_state(repo, state)
                        result = next_action(repo)
                        self.assertEqual((result["row"], result["reason"]["code"]),
                                         ("22", "plan_approval_commit_unreachable"))

    def test_implementing_entry_status_reports_the_same_causes(self):
        with h.ScratchRepo() as repo:
            self.implementing(repo)
            work_item = h.read_state(repo)["work_items"][WI]
            self.assertEqual(ws.implementing_entry_status(repo.root, work_item, repo.base),
                             {"reachable": True, "cause": None})
            self.assertTrue(ws.implementing_entry_reachable(repo.root, work_item, repo.base))
            stale = dict(work_item, plan_approval=dict(work_item["plan_approval"], status="STALE"))
            self.assertEqual(ws.implementing_entry_status(repo.root, stale, repo.base)["cause"],
                             "plan_approval_not_current")
            self.assertFalse(ws.implementing_entry_reachable(repo.root, stale, repo.base))


class TestImplementationReviewRows2_2(unittest.TestCase):
    def test_local_review(self):
        with h.ScratchRepo() as repo:
            implementation_item_at(repo, "2.2")
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("26", "implementation.review.local"))
            self.assertEqual(result["action"]["worker"]["independent_of"], ["implementer", "self_reviewer"])

    def test_a_current_block_is_review_resolve_block_at_both_phases(self):
        with h.ScratchRepo() as repo:
            ids = implementation_item_at(repo, "2.2")
            write_feedback(repo, verdict("BLOCK", rcid=ids["I"], bundle=ids["B"], base=repo.base,
                                         role="LOCAL_MODEL_IMPLEMENTATION_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "25")
        with h.ScratchRepo() as repo:
            ids = implementation_at_manual(repo)
            write_feedback(repo, verdict("BLOCK", rcid=ids["I"], role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW",
                                         work_item=None))
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["action"]["id"]),
                             ("25", "human_gate", "review.resolve_block"))

    def test_the_manual_phase(self):
        with h.ScratchRepo() as repo:
            ids = implementation_at_manual(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["satisfied_by"]), ("28", "implementation_review_verdict"))
            write_feedback(repo, verdict("APPROVE", rcid=ids["I"], role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"))
            self.assertEqual(next_action(repo)["action"]["id"], "implementation.record_external")

    def test_head_moved_is_row_25a(self):
        with h.ScratchRepo() as repo:
            implementation_item_at(repo, "2.2")
            move_head(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("25a", "bundle_generation_mismatch"))
            self.assertEqual([a["id"] for a in result["alternatives"]], ["implementation.recover_provenance"])
        with h.ScratchRepo() as repo:
            ids = implementation_at_manual(repo)
            move_head(repo)
            self.assertEqual(next_action(repo)["row"], "28")
            write_feedback(repo, verdict("APPROVE", rcid=ids["I"], role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"))
            self.assertEqual(next_action(repo)["row"], "25a")

    def test_bundle_integrity_is_row_25b(self):
        faults = {
            "missing directory": lambda repo: shutil.rmtree(bundle_dir(repo)),
            "required file removed": lambda repo: (bundle_dir(repo) / "MANIFEST.md").unlink(),
            "files differ from the manifest": lambda repo: (bundle_dir(repo) / "DIFF.patch").write_text("x\n"),
            "manifest content is not I": lambda repo: self.reclassify(repo),
        }
        for name, fault in faults.items():
            with self.subTest(fault=name), h.ScratchRepo() as repo:
                implementation_item_at(repo, "2.2")
                fault(repo)
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("25b", "bundle_unverified"))
                self.assertIn(f"prepare-ai-review.sh {repo.base} implementation {WI}", result["reason"]["remedy"])
                with self.assertRaises(ws.ImplementationReviewBundleUnverifiedError):
                    ws.verify_implementation_review_bundle(repo.root, WI)
            with self.subTest(fault=name, phase="manual"), h.ScratchRepo() as repo:
                ids = implementation_at_manual(repo)
                write_feedback(repo, verdict("APPROVE", rcid=ids["I"], role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"))
                fault(repo)
                self.assertEqual(next_action(repo)["row"], "25b")
        with h.ScratchRepo() as repo:
            implementation_at_manual(repo)
            shutil.rmtree(bundle_dir(repo))
            self.assertEqual(next_action(repo)["row"], "25b", "no fb and no bundle: never row 28")

    @staticmethod
    def reclassify(repo: h.ScratchRepo) -> None:
        """Moves the implementation content out of the protected set: the
        current **I** moves, HEAD and the bundle do not."""
        path = repo.root / "docs" / "ai-workflow" / "registry" / f"{WI}-artifacts.json"
        declarations = json.loads(path.read_text())
        stage = declarations["implementation_stage"]
        del stage["protected_paths"][h.BUNDLE_ITEM_IMPLEMENTATION_PATH]
        stage["excluded_paths"][h.BUNDLE_ITEM_IMPLEMENTATION_PATH] = "reclassified by the test"
        path.write_text(json.dumps(declarations) + "\n")

    def test_the_remedy_names_post_fix_after_a_revise_round(self):
        with h.ScratchRepo() as repo:
            applying_2_2(repo)
            repo.commit("fix", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
            h.generate_implementation_bundle(repo, stage="post-fix")
            self.assertEqual(h.read_state(repo)["work_items"][WI]["implementation_revision"], 2)
            shutil.rmtree(bundle_dir(repo))
            result = next_action(repo)
            self.assertEqual(result["row"], "25b")
            self.assertIn(f"prepare-ai-review.sh {repo.base} post-fix {WI}", result["reason"]["remedy"])

    def test_the_technical_gate(self):
        with h.ScratchRepo() as repo:
            implementation_at_external_2_2(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["action"]["id"]),
                             ("29", "human_gate", "implementation.approve"))

    def test_the_technical_gate_causes_are_row_30(self):
        def check(mutation, cause, alternatives=(), remedy=None):
            with self.subTest(cause=cause), h.ScratchRepo() as repo:
                ids = implementation_at_external_2_2(repo)
                mutation(repo, ids)
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("30", cause))
                self.assertEqual([a["id"] for a in result["alternatives"]], list(alternatives))
                if remedy:
                    self.assertIn(remedy(repo), result["reason"]["remedy"])

        check(lambda repo, ids: feedback_path(repo).unlink(), "no_review_round")
        check(lambda repo, ids: write_feedback(repo, verdict("BLOCK", rcid=ids["I"])), "review_blocked",
              ["implementation.apply_review"])
        check(lambda repo, ids: mutate(repo, ws.record_technical_review_block_pin, bundle_id=ids["B"],
                                       review_content_id=ids["I"], now="t-pin"),
              "review_block_pinned", ["implementation.apply_review"])
        check(lambda repo, ids: (repo.root / h.BUNDLE_ITEM_IMPLEMENTATION_PATH).write_text("dirty\n"),
              "protected_path_dirty")
        check(lambda repo, ids: edit_item(repo, reviewed_implementation_head=repo.base),
              "implementation_provenance_stale", ["implementation.recover_provenance"])
        check(lambda repo, ids: edit_item(repo, implementation_review_stages=dict(
            h.read_state(repo)["work_items"][WI]["implementation_review_stages"], review_content_id="d" * 64)),
            "review_ledger_stale")
        check(lambda repo, ids: move_head(repo), "bundle_generation_mismatch", ["implementation.recover_provenance"])
        check(lambda repo, ids: shutil.rmtree(bundle_dir(repo)), "bundle_unverified", (),
              lambda repo: f"prepare-ai-review.sh {repo.base} implementation {WI}")


class TestImplementationReviewRowsV1(unittest.TestCase):
    """Rows 30a to 35 at `"1"` and `"2.1"`."""

    def external(self, repo: h.ScratchRepo, version: str) -> dict:
        return implementation_item_at(repo, version)

    def pin_then_post_fix(self, repo: h.ScratchRepo, ids: dict) -> None:
        """`/apply-implementation-review`'s writers for a current `BLOCK`:
        the pin, the phase, a fix, then the post-fix republication."""
        mutate(repo, ws.record_technical_review_block_pin, bundle_id=ids["B"], review_content_id=ids["I"], now="t-pin")
        mutate(repo, ws.enter_applying_review_feedback, "t-apply")
        h.commit_state(repo, "pin and enter")
        repo.commit("fix the blocking finding", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
        h.generate_implementation_bundle(repo, stage="post-fix")

    def test_rows_by_version(self):
        for version in ("1", "2.1"):
            with self.subTest(version=version):
                with h.ScratchRepo() as repo:
                    self.external(repo, version)
                    result = next_action(repo)
                    self.assertEqual((result["row"], result["satisfied_by"]), ("35", "implementation_review_verdict"))
                    self.assertEqual([a["id"] for a in result["alternatives"]], ["implementation.review.local"])
                with h.ScratchRepo() as repo:
                    ids = self.external(repo, version)
                    write_feedback(repo, verdict("REVISE", bundle=ids["B"], base=repo.base))
                    self.assertEqual(next_action(repo)["row"], "32")
                    write_feedback(repo, verdict("APPROVE", bundle=ids["B"], base=repo.base))
                    result = next_action(repo)
                    self.assertEqual((result["row"], result["action"]["id"]), ("33", "implementation.approve"))
                    (repo.root / h.BUNDLE_ITEM_IMPLEMENTATION_PATH).write_text("dirty\n")
                    result = next_action(repo)
                    self.assertEqual((result["row"], result["reason"]["code"]), ("34", "protected_path_dirty"))
                    self.assertEqual([a["id"] for a in result["alternatives"]], ["implementation.recover_provenance"])
                with h.ScratchRepo() as repo:
                    ids = self.external(repo, version)
                    write_feedback(repo, verdict("APPROVE", bundle="f" * 64, base=repo.base))
                    self.assertEqual(next_action(repo)["row"], "35", "a stale fb is not current")

    def test_a_current_block_is_row_31_and_after_the_apply_row_35(self):
        for version in ("1", "2.1"):
            with self.subTest(version=version), h.ScratchRepo() as repo:
                ids = self.external(repo, version)
                write_feedback(repo, verdict("BLOCK", bundle=ids["B"], base=repo.base))
                result = next_action(repo)
                self.assertEqual((result["row"], result["disposition"], result["action"]["id"],
                                  result["reason"]["code"]),
                                 ("31", "automatic", "implementation.apply_review", "review_blocked"))
                self.pin_then_post_fix(repo, ids)
                self.assertEqual(next_action(repo)["row"], "35")

    def test_a_pinned_block_edited_to_revise_is_row_31(self):
        with h.ScratchRepo() as repo:
            ids = self.external(repo, "2.1")
            mutate(repo, ws.record_technical_review_block_pin, bundle_id=ids["B"], review_content_id=ids["I"], now="t")
            write_feedback(repo, verdict("REVISE", bundle=ids["B"], base=repo.base))
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("31", "review_block_pinned"))

    def test_a_pinned_block_without_a_current_fb_is_row_31a(self):
        for version in ("1", "2.1"):
            with self.subTest(version=version), h.ScratchRepo() as repo:
                ids = self.external(repo, version)
                mutate(repo, ws.record_technical_review_block_pin, bundle_id=ids["B"], review_content_id=ids["I"],
                       now="t")
                result = next_action(repo)
                self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                                 ("31a", "external_gate", "review_block_pinned"))
                write_feedback(repo, verdict("BLOCK", bundle=ids["B"], base=repo.base, work_item="other"))
                self.assertEqual(next_action(repo)["row"], "31a")
                write_feedback(repo, verdict("BLOCK", bundle=ids["B"], base=repo.base))
                self.assertEqual(next_action(repo)["row"], "31")

    def test_an_applied_revise_with_a_reachable_gate_offers_approval(self):
        with h.ScratchRepo() as repo:
            ids = self.external(repo, "2.1")
            write_feedback(repo, verdict("REVISE", bundle=ids["B"], base=repo.base))
            mutate(repo, ws.enter_applying_review_feedback, "t-apply")
            h.commit_state(repo, "enter")
            repo.commit("fix", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
            h.generate_implementation_bundle(repo, stage="post-fix")
            result = next_action(repo)
            self.assertEqual(result["row"], "35")
            self.assertEqual([a["id"] for a in result["alternatives"]],
                             ["implementation.review.local", "implementation.approve"])
            self.assertTrue(result["alternatives"][1]["worker"]["user_only"])

    def test_a_missing_bundle_is_row_30a(self):
        for version in ("1", "2.1"):
            with self.subTest(version=version), h.ScratchRepo() as repo:
                self.external(repo, version)
                shutil.rmtree(bundle_dir(repo))
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("30a", "bundle_unverified"))
                self.assertIn(f"prepare-ai-review.sh {repo.base} implementation {WI}", result["reason"]["remedy"])


class TestApplyingRows(unittest.TestCase):
    """Rows 35a and 36, and the implementation-stage content binding."""

    def apply_sequence(self, repo: h.ScratchRepo) -> dict:
        """`/apply-implementation-review` step 1: the feedback file, the
        `REJECTED` marker, then the binding."""
        state = h.read_state(repo)
        text = ws.read_review_feedback(repo.root, WI)
        if text is None:
            raise FileNotFoundError("no REVIEW_FEEDBACK.md")
        fingerprint.assert_bundle_not_rejected(repo.root, WI)
        return ws.assert_apply_review_feedback_binding(repo.root, state["work_items"][WI], WI,
                                                       stage="implementation", feedback_content=text)

    def test_content_bound_revise_variants_are_row_36(self):
        variants = {
            "no bundle fields": lambda ids, repo: verdict("REVISE", rcid=ids["I"], work_item=None),
            "stale bundle id": lambda ids, repo: verdict("REVISE", rcid=ids["I"], bundle="f" * 64, base=repo.base),
        }
        for name, build in variants.items():
            with self.subTest(variant=name), h.ScratchRepo() as repo:
                ids = applying_2_2(repo)
                write_feedback(repo, build(ids, repo))
                self.assertEqual(next_action(repo)["row"], "36")
                self.assertEqual(self.apply_sequence(repo)["binding"], "content")
                repo.commit("a fix the applier committed", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
                self.assertNotEqual(current_I(repo), ids["I"])
                result = next_action(repo)
                self.assertEqual((result["row"], result["action"]["id"]), ("36", "implementation.apply_review"))
                self.apply_sequence(repo)

    def test_the_forgery_is_refused_and_gives_row_35a(self):
        with h.ScratchRepo() as repo:
            ids = applying_2_2(repo)
            write_feedback(repo, verdict("REVISE", rcid="c" * 64, bundle=ids["B"], base=repo.base))
            with self.assertRaises(ws.FeedbackContentMismatchError):
                self.apply_sequence(repo)
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "review_feedback_not_current"))
            self.assertIn("FeedbackContentMismatchError", result["reason"]["text"])
            assert_no_binding_field_edit(self, result)

    def test_a_tampered_or_missing_bundle_is_row_35a_bundle_unverified(self):
        for fault in (lambda repo: (bundle_dir(repo) / "DIFF.patch").write_text("x\n"),
                      lambda repo: shutil.rmtree(bundle_dir(repo))):
            with h.ScratchRepo() as repo:
                ids = applying_2_2(repo)
                write_feedback(repo, verdict("REVISE", rcid=ids["I"]))
                fault(repo)
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "bundle_unverified"))
                with self.assertRaises((ws.ReviewBundleManifestMismatchError, fingerprint.MissingRequiredBundleFileError)):
                    self.apply_sequence(repo)

    def test_a_manifest_of_another_base_or_stage_is_refused_by_check_3(self):
        with h.ScratchRepo() as repo:
            ids = applying_2_2(repo)
            write_feedback(repo, verdict("REVISE", rcid=ids["I"]))
            edit_item(repo, base_commit=h.git(repo, "rev-parse", f"{repo.base}~1"))
            with self.assertRaisesRegex(ws.ReviewBundleManifestMismatchError, "base_commit"):
                self.apply_sequence(repo)
        with h.ScratchRepo() as plan_repo:
            plan_item_at(plan_repo, "AWAITING_LOCAL_PLAN_REVIEW")
            with h.ScratchRepo() as repo:
                ids = applying_2_2(repo)
                plan_manifest = (bundle_dir(plan_repo) / "MANIFEST.md").read_text()
                self.assertIn("stage: plan", plan_manifest)
                shutil.rmtree(bundle_dir(repo))
                shutil.copytree(bundle_dir(plan_repo), bundle_dir(repo))
                manifest = fingerprint.read_plan_stage_manifest_fields(bundle_dir(repo) / "MANIFEST.md")
                write_feedback(repo, verdict("REVISE", rcid=manifest["review_content_id"]))
                with self.assertRaisesRegex(ws.ReviewBundleManifestMismatchError, "stage|base_commit"):
                    self.apply_sequence(repo)
                self.assertEqual(next_action(repo)["row"], "35a")
        with h.ScratchRepo() as impl_repo:
            implementation_item_at(impl_repo, "2.2")
            with h.ScratchRepo() as repo:
                ids = plan_item_at(repo, "REVISING_PLAN")
                shutil.rmtree(bundle_dir(repo))
                shutil.copytree(bundle_dir(impl_repo), bundle_dir(repo))
                write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
                state = h.read_state(repo)
                with self.assertRaises(ws.ReviewBundleManifestMismatchError):
                    ws.assert_apply_review_feedback_binding(repo.root, state["work_items"][WI], WI, stage="plan",
                                                            feedback_content=feedback_path(repo).read_text())
                self.assertEqual(next_action(repo)["row"], "7a")

    def test_another_items_flat_bundle_is_refused_by_its_owner(self):
        """MPR-R10-001: item X on the flat layout, the shared
        `.ai-review/current/` holding item Y's bundle and Y's `REVISE` with
        no `Work item:`."""
        with h.ScratchRepo() as other:
            h.seed_bundle_item(other, "y", phase="SELF_REVIEWING_IMPLEMENTATION")
            other.commit("implement y", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
            h.generate_implementation_bundle(other, "y")
            y_bundle = other.root / ".ai-review" / "y" / "current"
            y_manifest = fingerprint.read_plan_stage_manifest_fields(y_bundle / "MANIFEST.md")
            with h.ScratchRepo() as repo:
                applying_2_2(repo)
                shutil.rmtree(repo.root / ".ai-review")
                state = h.read_state(repo)
                state["work_items"][WI].pop("feedback_layout")
                h.write_state(repo, state)
                shutil.copytree(y_bundle, repo.root / ".ai-review" / "current")
                y_text = verdict("REVISE", rcid=y_manifest["review_content_id"], work_item=None)
                flat_feedback = repo.root / ".ai-review" / "feedback" / "REVIEW_FEEDBACK.md"
                flat_feedback.parent.mkdir(parents=True)
                flat_feedback.write_text(y_text)
                self.assertEqual(fingerprint.resolve_bundle_dir(repo.root, WI), Path(".ai-review/current"))
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "bundle_unverified"))
                self.assertIn("another item", result["reason"]["text"])
                with self.assertRaises(ws.ReviewBundleManifestMismatchError):
                    self.apply_sequence(repo)

    def test_a_manifest_naming_no_work_item_takes_the_bundle_binding(self):
        with h.ScratchRepo() as repo:
            ids = applying_2_2(repo)
            manifest = bundle_dir(repo) / "MANIFEST.md"
            manifest.write_text("\n".join(line for line in manifest.read_text().splitlines()
                                          if not line.startswith("work_item_id:")) + "\n")
            write_feedback(repo, verdict("REVISE", rcid=ids["I"], work_item=None))
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "review_feedback_not_current"))
            with self.assertRaises(fingerprint.MissingFeedbackBindingFieldError):
                self.apply_sequence(repo)
            write_feedback(repo, verdict("REVISE", rcid=ids["I"], bundle=current_bundle_id(repo), base=repo.base))
            self.assertEqual(next_action(repo)["row"], "36")
            self.assertEqual(self.apply_sequence(repo)["binding"], "bundle")

    def test_the_apply_rows_preemptions_at_every_version(self):
        for version in wp.SUPPORTED_GOVERNING_VERSIONS:
            with self.subTest(version=version), h.ScratchRepo() as repo:
                if version == "2.2":
                    ids = applying_2_2(repo)
                    good = verdict("REVISE", rcid=ids["I"], bundle=ids["B"], base=repo.base)
                else:
                    ids = implementation_item_at(repo, version)
                    good = verdict("REVISE", bundle=ids["B"], base=repo.base)
                    write_feedback(repo, good)
                    mutate(repo, ws.enter_applying_review_feedback, "t-apply")
                    feedback_path(repo).unlink()
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "review_feedback_missing"))
                self.assertIn(".ai-review/wi/feedback/REVIEW_FEEDBACK.md", result["reason"]["text"])
                write_feedback(repo, verdict("REVISE", bundle="f" * 64, base=repo.base, work_item="another"))
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "review_feedback_missing"))
                self.assertIn("'another'", result["reason"]["text"])
                feedback_path(repo).unlink()
                with self.assertRaises(FileNotFoundError):
                    self.apply_sequence(repo)
                write_feedback(repo, verdict("REVISE", bundle="f" * 64, base=repo.base))
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "review_feedback_not_current"))
                with self.assertRaises(fingerprint.FeedbackBundleMismatchError):
                    self.apply_sequence(repo)
                write_feedback(repo, verdict("REVISE", base=repo.base, bundle=None))
                self.assertEqual(next_action(repo)["reason"]["code"], "review_feedback_not_current")
                write_feedback(repo, good)
                result = next_action(repo)
                self.assertEqual((result["row"], result["action"]["id"]), ("36", "implementation.apply_review"))
                self.assertEqual(self.apply_sequence(repo)["binding"], "content" if version == "2.2" else "bundle")
                reject_bundle(repo)
                self.assertEqual(next_action(repo)["row"], "6")
                with self.assertRaises(fingerprint.BundleRejectedError):
                    self.apply_sequence(repo)
                (repo.root / fingerprint.resolve_rejected_marker_path(repo.root, WI)).unlink()
                shutil.rmtree(bundle_dir(repo))
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("35a", "bundle_unverified"))
                with self.assertRaises(fingerprint.MissingRequiredBundleFileError):
                    self.apply_sequence(repo)


CHECKPOINT_C1 = [{"id": "C1", "depends_on": []}]


def commit_checklist_evidence(repo: h.ScratchRepo, revision) -> str:
    """`/prepare-functional-review`'s checklist-evidence commit for `revision`."""
    path = repo.root / ws.FUNCTIONAL_CHECKLIST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Active milestone\n\n## Functional review checklist\n\n- exercise the flow\n")
    h.git(repo, "add", "--", ws.FUNCTIONAL_CHECKLIST_PATH)
    blob = h.git(repo, "hash-object", "--", ws.FUNCTIONAL_CHECKLIST_PATH)
    h.git(repo, "commit", "-q", "-m",
          f"checklist\n\nWorkflow-Functional-Checklist: {WI}/{revision}/{blob}\nWorkflow-Work-Item: {WI}")
    return blob


def functional_item(repo: h.ScratchRepo, version: str, *, complete: bool = True, evidence: bool = True) -> None:
    """An item at `AWAITING_FUNCTIONAL_REVIEW` with a covering `CURRENT`
    plan approval, its registry's one checkpoint `COMPLETE` (or not), and
    committed checklist evidence for its round."""
    h.seed_bundle_item(repo, governing_workflow_version=version, phase="AWAITING_FUNCTIONAL_REVIEW",
                       registry_checkpoints=CHECKPOINT_C1, implementation_revision=1)
    if complete:
        edit_item(repo, checkpoints={"C1": {"status": "COMPLETE", "start_commit": repo.base}})
    h.approve_plan(repo)
    if evidence:
        commit_checklist_evidence(repo, 1)


class TestFunctionalRows(unittest.TestCase):
    def test_no_evidence_is_functional_prepare(self):
        with h.ScratchRepo() as repo:
            functional_item(repo, "2.2", evidence=False)
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("37", "functional.prepare"))
            commit_checklist_evidence(repo, 1)
            (repo.root / ws.FUNCTIONAL_CHECKLIST_PATH).write_text("edited after its evidence commit\n")
            self.assertEqual(next_action(repo)["row"], "37", "the evidence blob is not the live checklist")

    def test_a_terminal_registry_is_the_functional_gate(self):
        for version in wp.SUPPORTED_GOVERNING_VERSIONS:
            with self.subTest(version=version), h.ScratchRepo() as repo:
                functional_item(repo, version)
                result = next_action(repo)
                self.assertEqual((result["row"], result["disposition"], result["action"]["id"]),
                                 ("39", "human_gate", "functional.review"))
                self.assertEqual([a["id"] for a in result["alternatives"]],
                                 ["milestone.accept", "functional.apply_findings", "functional.review.advisory"])
                self.assertTrue(result["alternatives"][0]["worker"]["user_only"])

    def test_unconsumed_findings_are_row_38_and_consumed_ones_row_39(self):
        with h.ScratchRepo() as repo:
            functional_item(repo, "2.2")
            write_feedback(repo, "# Functional review\n\n- a finding\n", name="FUNCTIONAL_REVIEW.md")
            result = next_action(repo)
            self.assertEqual((result["row"], result["action"]["id"]), ("38", "functional.apply_findings"))
            fingerprint.mark_functional_review_consumed(repo.root, WI)
            self.assertEqual(next_action(repo)["row"], "39")

    def test_the_registry_read_refusals_are_row_38a(self):
        for version in ("1", "2.2"):
            with self.subTest(version=version, cause="plan_content_drifted"), h.ScratchRepo() as repo:
                functional_item(repo, version)
                plan = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
                plan.write_text(plan.read_text() + "edited after approval\n")
                result = next_action(repo)
                self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                                 ("38a", "blocked", "plan_content_drifted"))
                self.assertIn("restore the approved plan-stage bytes", result["reason"]["remedy"])
                self.assertNotIn("/request-plan-amendment", result["reason"]["remedy"])
                self.assertNotIn("milestone.accept", [a["id"] for a in result["alternatives"]])
            with self.subTest(version=version, cause="registry_unreadable"), h.ScratchRepo() as repo:
                functional_item(repo, version)
                registry = repo.root / "docs" / "ai-workflow" / "registry" / f"{WI}-registry.json"
                data = json.loads(registry.read_text())
                data["work_item_id"] = "another-item"
                registry.write_text(json.dumps(data) + "\n")
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("38a", "registry_unreadable"))

    def test_a_v1_incomplete_registry_is_row_38b(self):
        with h.ScratchRepo() as repo:
            functional_item(repo, "1", complete=False)
            result = next_action(repo)
            self.assertEqual((result["row"], result["disposition"], result["reason"]["code"]),
                             ("38b", "blocked", "v1_state_not_advanced"))
            self.assertEqual([a["id"] for a in result["alternatives"]],
                             ["functional.apply_findings", "functional.review.advisory"])

    def test_a_two_stage_incomplete_registry_is_row_38c(self):
        for version in ("2.1", "2.2"):
            with self.subTest(version=version), h.ScratchRepo() as repo:
                functional_item(repo, version, complete=False)
                result = next_action(repo)
                self.assertEqual((result["row"], result["reason"]["code"]), ("38c", "registry_incomplete"))
                self.assertIn("v2.6.0-003", result["reason"]["remedy"])
                self.assertNotIn("/request-plan-amendment", result["reason"]["remedy"])
                self.assertIn("none_exists", wp.ROWS_BY_ID["38c"].remedy_commands_for("AWAITING_FUNCTIONAL_REVIEW", version))
                self.assertNotIn("implementation.checkpoint", [a["id"] for a in result["alternatives"]])

    def test_a_promoted_legacy_item_with_an_incomplete_registry_is_row_38c(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, governing_workflow_version="1", phase="LEGACY_READY",
                               registry_checkpoints=CHECKPOINT_C1, implementation_revision=1)
            h.approve_plan(repo)
            milestone = repo.root / "docs" / "ACTIVE_MILESTONE.md"
            milestone.write_text("# wi\n\naccepted and closed\n")
            h.git(repo, "add", "-A")
            h.git(repo, "commit", "-q", "-m", "integrate the legacy branch")
            state = h.read_state(repo)
            state["work_items"][WI]["technical_approval"] = ws.build_approval_record(
                basis="LEGACY_V1", stage="implementation", user_confirmation="legacy import of wi implementation",
                now="t", approved_review_content_id="a" * 64, reviewed_content_commit=repo.head(),
                legacy_evidence={"rounds": 1})
            state = ws.promote_legacy_work_item(
                state, repo.root, work_item_id=WI, required_active_milestone_substring="accepted and closed",
                artifacts_path=fingerprint.artifacts_path_for_work_item(WI), now="t-promote")
            self.assertEqual((state["work_items"][WI]["governing_workflow_version"],
                              state["work_items"][WI]["phase"]), ("2.1", "AWAITING_FUNCTIONAL_REVIEW"))
            h.write_state(repo, state)
            commit_checklist_evidence(repo, 1)
            result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("38c", "registry_incomplete"))

    def test_a_v1_terminal_or_registry_less_item_lists_milestone_accept(self):
        with h.ScratchRepo() as repo:
            functional_item(repo, "1")
            self.assertEqual(next_action(repo)["row"], "39")
            edit_item(repo, registry_path=None, checkpoints={})
            result = next_action(repo)
            self.assertEqual(result["row"], "39")
            self.assertIn("milestone.accept", [a["id"] for a in result["alternatives"]])


class TestRaisingConditions(unittest.TestCase):
    """`LPR-R4-002`, `LPR-R5-001`: a raising condition call."""

    def test_an_unmapped_workflow_exception_from_a_value_call_is_condition_refused(self):
        with h.ScratchRepo() as repo:
            functional_item(repo, "2.2", evidence=False)
            with mock.patch.object(ws, "discover_current_functional_checklist_evidence",
                                   side_effect=ws.CorruptJsonError("evidence store corrupt")):
                body, code = call("--repo-root", str(repo.root), "next-action")
            self.assertEqual((code, body["ok"]), (0, True))
            result = body["result"]
            self.assertEqual((result["row"], result["disposition"], result["action"], result["reason"]["code"]),
                             ("37", "blocked", None, "condition_refused"))
            self.assertEqual(result["reason"]["native"],
                             {"exception": "CorruptJsonError", "message": "evidence store corrupt"})
            self.assertIn("CorruptJsonError", result["reason"]["text"])

    def test_a_builtin_from_a_value_call_is_internal_error(self):
        with h.ScratchRepo() as repo:
            functional_item(repo, "2.2", evidence=False)
            with mock.patch.object(ws, "discover_current_functional_checklist_evidence", side_effect=KeyError("x")):
                body, code = call("--repo-root", str(repo.root), "next-action")
            self.assertEqual((code, body["error"]["code"]), (1, "internal_error"))

    def assert_acceptance(self, build, target, function, listed, *, falls_to: str, at: str):
        """Patched to raise each listed class, the acceptance call falls
        through; patched to raise an unlisted Workflow exception, it is
        `condition_refused` at its first row."""
        for cls in listed:
            with self.subTest(function=function, raised=cls.__name__), h.ScratchRepo() as repo:
                build(repo)
                with mock.patch.object(target, function, side_effect=cls("patched")):
                    self.assertEqual(next_action(repo)["row"], falls_to)
        with self.subTest(function=function, raised="unlisted"), h.ScratchRepo() as repo:
            build(repo)
            with mock.patch.object(target, function, side_effect=ws.CorruptJsonError("patched")):
                result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), (at, "condition_refused"))

    def test_the_apply_plan_acceptance(self):
        def build(repo):
            ids = plan_item_at(repo, "REVISING_PLAN")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
        self.assert_acceptance(build, ws, "assert_apply_plan_review_feedback",
                               [ws.FeedbackStatusNotApplicableError, ws.FeedbackNotForConsumedContentError],
                               falls_to="9", at="7a")
        self.assert_acceptance(build, ws, "assert_apply_review_feedback_binding",
                               [ws.FeedbackContentMismatchError], falls_to="9", at="7a")

    def test_the_bundle_binding_acceptance(self):
        def build(repo):
            h.seed_bundle_item(repo, governing_workflow_version="1", phase="AWAITING_EXTERNAL_PLAN_REVIEW")
            h.generate_plan_bundle(repo)
            write_feedback(repo, verdict("REVISE", bundle=current_bundle_id(repo), base=repo.base))
        self.assert_acceptance(build, fingerprint, "assert_feedback_matches_bundle",
                               [fingerprint.FeedbackBundleMismatchError, fingerprint.MissingFeedbackBindingFieldError],
                               falls_to="20", at="17")

    def test_the_functional_review_acceptance(self):
        def build(repo):
            functional_item(repo, "2.2")
            write_feedback(repo, "# Functional review\n", name="FUNCTIONAL_REVIEW.md")
        self.assert_acceptance(build, fingerprint, "assert_functional_review_not_already_consumed",
                               [fingerprint.FunctionalReviewAlreadyAppliedError], falls_to="39", at="38")


# ---------------------------------------------------------------------------
# Every call a row reaches is declared (`LPR-R5-001`, `LPR-R6-003`)
# ---------------------------------------------------------------------------


def _scenarios() -> dict:
    """Builders for a spread of states across the catalogue."""
    def plan_revise(repo):
        ids = plan_item_at(repo, "REVISING_PLAN")
        write_feedback(repo, verdict("REVISE", rcid=ids["P"]))

    def plan_manual(repo):
        ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
        write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW"))

    def v1_plan(repo):
        h.seed_bundle_item(repo, governing_workflow_version="1", phase="AWAITING_EXTERNAL_PLAN_REVIEW")
        h.generate_plan_bundle(repo)
        write_feedback(repo, verdict("APPROVE", bundle=current_bundle_id(repo), base=repo.base))

    def implementing(repo):
        h.seed_bundle_item(repo, phase="IMPLEMENTING", registry_checkpoints=CHECKPOINT_C1)
        h.approve_plan(repo)

    def impl_manual(repo):
        ids = implementation_at_manual(repo)
        write_feedback(repo, verdict("APPROVE", rcid=ids["I"], role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"))

    def v1_external(repo):
        ids = implementation_item_at(repo, "2.1")
        write_feedback(repo, verdict("REVISE", bundle="f" * 64, base=repo.base))

    def applying(repo):
        ids = applying_2_2(repo)
        write_feedback(repo, verdict("REVISE", rcid=ids["I"]))

    def functional(repo):
        functional_item(repo, "2.2")
        write_feedback(repo, "# Functional review\n", name="FUNCTIONAL_REVIEW.md")
        fingerprint.mark_functional_review_consumed(repo.root, WI)

    return {
        "plan.local": lambda repo: plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW"),
        "plan.revise": plan_revise, "plan.manual": plan_manual,
        "plan.approval": lambda repo: plan_item_at(repo, "AWAITING_PLAN_APPROVAL"),
        "v1.plan": v1_plan, "implementing": implementing,
        "impl.local": lambda repo: implementation_item_at(repo, "2.2"),
        "impl.manual": impl_manual, "impl.external": implementation_at_external_2_2,
        "v1.external": v1_external, "applying": applying, "functional": functional,
        "no item": lambda repo: write_state(repo, h.base_state()),
    }


class TestDeclaredCalls(unittest.TestCase):
    def test_every_reached_condition_call_is_declared_by_its_row(self):
        """Each `CONDITION_CALLS` function is patched to a recorder. Every
        call a row makes goes through its declared entry (`_Context.call`
        refuses an undeclared one, so `ctx.reached` holds only declared
        pairs), and no listed function is ever called by a predicate outside
        such a call -- a bypass of the table."""
        names = sorted(wp._CONDITION_FUNCTION_MODULES)
        bypasses: list[tuple[str, str]] = []

        def evaluating_context():
            frame = inspect.currentframe()
            while frame is not None:
                for key in ("ctx", "self"):
                    candidate = frame.f_locals.get(key)
                    if isinstance(candidate, wp._Context):
                        return candidate
                frame = frame.f_back
            return None

        def recorder(name, original):
            def wrapped(*args, **kwargs):
                ctx = evaluating_context()
                if ctx is not None and ctx.row_id is not None and ctx.in_call is None:
                    bypasses.append((ctx.row_id, name))
                return original(*args, **kwargs)
            return wrapped

        for scenario, build in _scenarios().items():
            with self.subTest(scenario=scenario), h.ScratchRepo() as repo:
                build(repo)
                state = h.read_state(repo)
                patches = [mock.patch.object(wp._CONDITION_FUNCTION_MODULES[name], name,
                                             recorder(name, getattr(wp._CONDITION_FUNCTION_MODULES[name], name)))
                           for name in names]
                for patch in patches:
                    patch.start()
                try:
                    bypasses.clear()
                    _decision, ctx = wp.evaluate_catalogue(repo.root, state, state.get("active_work_item_id"))
                finally:
                    for patch in patches:
                        patch.stop()
                self.assertEqual(bypasses, [])
                for row_id, function in ctx.reached:
                    declared = {entry["function"] for entry in wp.CONDITION_CALLS[row_id]}
                    self.assertIn(function, declared, f"row {row_id} reached {function}")

    def test_an_undeclared_call_is_refused(self):
        ctx = wp._Context(Path("."), h.base_state(wi=minimal_item("PLANNING", "2.2")), WI)
        ctx.row_id = "7"
        with self.assertRaises(AssertionError):
            ctx.call("load_config", lambda: None)

    def test_a_value_reused_from_an_earlier_row_counts_for_every_row_that_reads_it(self):
        """Row 8 reuses row 5's `plan_review_publication_status`, and must
        still declare it."""
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
            state = h.read_state(repo)
            _decision, ctx = wp.evaluate_catalogue(repo.root, state, WI)
            rows_reading = {row for row, function in ctx.reached if function == "plan_review_publication_status"}
            self.assertEqual(rows_reading, {"5", "7a", "8"})


# ---------------------------------------------------------------------------
# Command agreement (LPR-R2-002, MPR-R11-001)
# ---------------------------------------------------------------------------


def _command_text(command: str) -> str:
    return (COMMANDS_DIR / f"{command}.md").read_text()


def _fb_text(repo: h.ScratchRepo) -> str | None:
    return ws.read_review_feedback(repo.root, WI)


def _guard_plan_author(repo, state):
    work_item = state["work_items"][WI]
    ws.assert_plan_review_entry_phase(work_item, WI, command="/milestone-plan")
    ws.load_config(repo.root)


def _guard_plan_apply_review(repo, state):
    work_item = state["work_items"][WI]
    two_stage = work_item["governing_workflow_version"] in ws.TWO_STAGE_PLAN_REVIEW_VERSIONS
    if two_stage:
        ws.assert_plan_review_entry_phase(work_item, WI, command="/apply-plan-review")
    text = _fb_text(repo)
    if text is None:
        raise FileNotFoundError("no REVIEW_FEEDBACK.md")
    fingerprint.assert_bundle_not_rejected(repo.root, WI)
    mode = "bundle"
    if two_stage:
        status = ws.plan_review_publication_status(repo.root, state, WI)["status"]
        mode = ws.assert_apply_plan_review_feedback(work_item, WI, feedback_content=text, publication_status=status)
    if mode == "bundle":
        return ws.assert_apply_review_feedback_binding(repo.root, work_item, WI, stage="plan", feedback_content=text)
    return None


def _guard_plan_review_local(repo, state):
    fingerprint.assert_local_generation_matches(repo.root, bundle_dir(repo) / "MANIFEST.md")
    fingerprint.assert_bundle_not_rejected(repo.root, WI)
    ws.assert_plan_review_bundle_bound(repo.root, WI, state=state)
    ws.validate_local_plan_review_preconditions(state["work_items"][WI])


def _guard_plan_record_external(repo, state):
    """The record-manual command's path since CP5: the shared ingest."""
    return ws.ingest_manual_review_verdict(
        repo.root, WI, stage="plan", verdict_text=_fb_text(repo), now="t", two_stage_only=True)


def _guard_implementing_entry(repo, state):
    work_item = state["work_items"][WI]
    status = ws.implementing_entry_status(repo.root, work_item, work_item["base_commit"])
    if not status["reachable"]:
        raise AssertionError(f"implementing entry refused: {status['cause']}")


def _guard_checkpoint(repo, state):
    _guard_implementing_entry(repo, state)
    registry = json.loads((repo.root / state["work_items"][WI]["registry_path"]).read_text())
    checkpoint_id = ws.select_next_checkpoint(state["work_items"][WI], registry)
    ws.transition_checkpoint_in_progress(state, WI, checkpoint_id, start_commit=repo.head(), now="t")


def _guard_self_review(repo, state):
    _guard_implementing_entry(repo, state)
    registry = json.loads((repo.root / state["work_items"][WI]["registry_path"]).read_text())
    ws.enter_self_reviewing_implementation(state, WI, registry, now="t")


def _guard_implementation_review_local(repo, state):
    ws.verify_implementation_review_bundle(repo.root, WI, state=state)
    fingerprint.assert_local_generation_matches(repo.root, bundle_dir(repo) / "MANIFEST.md")
    fingerprint.assert_bundle_not_rejected(repo.root, WI)
    ws.validate_local_implementation_review_preconditions(state["work_items"][WI])


def _guard_implementation_record_external(repo, state):
    return ws.ingest_manual_review_verdict(
        repo.root, WI, stage="implementation", verdict_text=_fb_text(repo), now="t", two_stage_only=True)


def _guard_implementation_apply_review(repo, state):
    if state["work_items"][WI]["phase"] != "APPLYING_REVIEW_FEEDBACK":
        ws.enter_applying_review_feedback(state, WI, now="t")
    text = _fb_text(repo)
    if text is None:
        raise FileNotFoundError("no REVIEW_FEEDBACK.md")
    fingerprint.assert_bundle_not_rejected(repo.root, WI)
    return ws.assert_apply_review_feedback_binding(repo.root, state["work_items"][WI], WI,
                                                   stage="implementation", feedback_content=text)


def _guard_functional_prepare(repo, state):
    if state["work_items"][WI]["phase"] != "AWAITING_FUNCTIONAL_REVIEW":
        raise AssertionError("not at the functional gate")


def _guard_functional_apply(repo, state):
    if not feedback_path(repo, "FUNCTIONAL_REVIEW.md").is_file():
        raise FileNotFoundError("no FUNCTIONAL_REVIEW.md")
    fingerprint.assert_functional_review_not_already_consumed(repo.root, WI)


#: Per automatic action: the command's pre-write guard sequence (as a
#: callable over the row's state), and the names the command document must
#: carry for it. `plan.record_external`/`implementation.record_external`
#: name the shared ingest from CP5, which rewrites those two commands; their
#: document check is CP5's.
COMMAND_GUARDS = {
    "plan.author": (_guard_plan_author, ["assert_plan_review_entry_phase", "WORKFLOW_CONFIG.json", "route_work_item"]),
    "plan.apply_review": (_guard_plan_apply_review, [
        "assert_plan_review_entry_phase", "REVIEW_FEEDBACK.md", "assert_bundle_not_rejected",
        "assert_apply_plan_review_feedback", "assert_apply_review_feedback_binding"]),
    "plan.review.local": (_guard_plan_review_local, [
        "assert_local_generation_matches", "assert_bundle_not_rejected", "assert_plan_review_bundle_bound",
        "validate_local_plan_review_preconditions"]),
    "plan.record_external": (_guard_plan_record_external, ["ingest_manual_review_verdict", "two_stage_only=True"]),
    "implementation.checkpoint": (_guard_checkpoint, ["implementing_entry_status", "transition_checkpoint_in_progress"]),
    "implementation.self_review": (_guard_self_review, ["implementing_entry_status", "enter_self_reviewing_implementation"]),
    "implementation.review.local": (_guard_implementation_review_local, [
        "verify_implementation_review_bundle", "assert_local_generation_matches", "assert_bundle_not_rejected",
        "validate_local_implementation_review_preconditions"]),
    "implementation.record_external": (_guard_implementation_record_external, [
        "ingest_manual_review_verdict", "two_stage_only=True"]),
    "implementation.apply_review": (_guard_implementation_apply_review, [
        "REVIEW_FEEDBACK.md", "assert_bundle_not_rejected", "assert_apply_review_feedback_binding"]),
    "functional.prepare": (_guard_functional_prepare, ["AWAITING_FUNCTIONAL_REVIEW"]),
    "functional.apply_findings": (_guard_functional_apply, ["assert_functional_review_not_already_consumed"]),
}


def _automatic_scenarios() -> dict:
    """`(builder, expected row)` for automatic rows at each `gv` they cover."""
    def revise(variant):
        def build(repo, version):
            ids = plan_item_at(repo, "REVISING_PLAN", version)
            write_feedback(repo, {"plain": verdict("REVISE", rcid=ids["P"], bundle=ids["B"], base=repo.base),
                                  "no fields": verdict("REVISE", rcid=ids["P"], work_item=None),
                                  "stale id": verdict("REVISE", rcid=ids["P"], bundle="f" * 64)}[variant])
        return build

    def withdrawn(repo, version):
        plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW", version)
        mutate(repo, ws.withdraw_plan_review, "t")

    def manual(repo, version):
        ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW", version)
        write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW"))

    def v1_plan(status):
        def build(repo, version):
            h.seed_bundle_item(repo, governing_workflow_version="1", phase="AWAITING_EXTERNAL_PLAN_REVIEW")
            h.generate_plan_bundle(repo)
            write_feedback(repo, verdict(status, bundle=current_bundle_id(repo), base=repo.base))
        return build

    def implementing(complete):
        def build(repo, version):
            h.seed_bundle_item(repo, governing_workflow_version=version, phase="IMPLEMENTING",
                               registry_checkpoints=CHECKPOINT_C1)
            h.approve_plan(repo)
            if complete:
                edit_item(repo, checkpoints={"C1": {"status": "COMPLETE", "start_commit": repo.base}})
        return build

    def impl_manual(repo, version):
        ids = implementation_at_manual(repo)
        write_feedback(repo, verdict("APPROVE", rcid=ids["I"], role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"))

    def applying(variant):
        def build(repo, version):
            if version == "2.2":
                ids = applying_2_2(repo)
                write_feedback(repo, {"plain": verdict("REVISE", rcid=ids["I"], bundle=ids["B"], base=repo.base),
                                      "no fields": verdict("REVISE", rcid=ids["I"], work_item=None),
                                      "stale id": verdict("REVISE", rcid=ids["I"], bundle="f" * 64)}[variant])
            else:
                ids = implementation_item_at(repo, version)
                write_feedback(repo, verdict("REVISE", bundle=ids["B"], base=repo.base))
                mutate(repo, ws.enter_applying_review_feedback, "t")
        return build

    def v1_external(status):
        def build(repo, version):
            ids = implementation_item_at(repo, version)
            write_feedback(repo, verdict(status, bundle=ids["B"], base=repo.base))
        return build

    def functional(findings):
        def build(repo, version):
            functional_item(repo, version, evidence=findings)
            if findings:
                write_feedback(repo, "# Functional review\n", name="FUNCTIONAL_REVIEW.md")
        return build

    two = ("2.1", "2.2")
    return [
        ("7", two, lambda repo, version: h.seed_bundle_item(repo, governing_workflow_version=version, phase="PLANNING")),
        ("9", two, withdrawn),
        ("8", two, revise("plain")), ("8", two, revise("no fields")), ("8", two, revise("stale id")),
        ("12", two, lambda repo, version: plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW", version)),
        ("13", two, manual),
        ("17", ("1",), v1_plan("BLOCK")), ("18", ("1",), v1_plan("REVISE")),
        ("23", two, implementing(False)), ("24", two, implementing(True)),
        ("26", ("2.2",), lambda repo, version: implementation_item_at(repo, "2.2")),
        ("27", ("2.2",), impl_manual),
        ("31", ("1", "2.1"), v1_external("BLOCK")), ("32", ("1", "2.1"), v1_external("REVISE")),
        ("36", ("1", "2.1", "2.2"), applying("plain")), ("36", ("2.2",), applying("no fields")),
        ("36", ("2.2",), applying("stale id")),
        ("37", ("1", "2.1", "2.2"), functional(False)), ("38", ("1", "2.1", "2.2"), functional(True)),
    ]


class TestCommandAgreement(unittest.TestCase):
    def test_every_automatic_action_has_a_guard_sequence(self):
        self.assertEqual(set(COMMAND_GUARDS), set(wp.EDGES) - {"plan.start"})

    def test_each_command_document_names_its_guards(self):
        for action_id, (_guard, names) in COMMAND_GUARDS.items():
            if names is None:
                continue
            text = _command_text(wp.ACTIONS[action_id]["command"])
            for name in names:
                with self.subTest(action=action_id, name=name):
                    self.assertIn(name, text)
        self.assertIn("route_work_item", _command_text("milestone-plan"))

    def test_neither_apply_command_binds_with_assert_feedback_matches_bundle_itself(self):
        for command in ("apply-plan-review", "apply-implementation-review"):
            step1 = _command_text(command).split("\n1. ", 1)[1].split("\n2. ", 1)[0]
            self.assertIn("workflow_state.assert_apply_review_feedback_binding(repo_root", step1)
            self.assertNotIn("parse_review_feedback_binding_fields`/", step1)

    def test_every_automatic_row_is_accepted_by_its_commands_guards(self):
        for row_id, versions, build in _automatic_scenarios():
            for version in versions:
                with self.subTest(row=row_id, version=version), h.ScratchRepo() as repo:
                    build(repo, version)
                    result = next_action(repo)
                    self.assertEqual((result["row"], result["disposition"]), (row_id, "automatic"))
                    guard, _names = COMMAND_GUARDS[result["action"]["id"]]
                    outcome = guard(repo, h.read_state(repo))
                    if row_id == "8" and isinstance(outcome, dict):
                        self.assertEqual(outcome["binding"], "content")
                    if row_id == "36" and isinstance(outcome, dict):
                        self.assertEqual(outcome["binding"], "content" if version == "2.2" else "bundle")


#: Each command's phase gate, evaluated on `(phase, gv)`.
def _accepts_milestone_plan(phase, version):
    try:
        ws.assert_plan_review_entry_phase(minimal_item(phase, version), WI, command="/milestone-plan")
        return version in ws.TWO_STAGE_PLAN_REVIEW_VERSIONS
    except ws.PlanReviewPhaseNotPlanStageError:
        return False


def _accepts_apply_implementation_review(phase, version):
    if phase == "APPLYING_REVIEW_FEEDBACK":
        return True
    try:
        ws.enter_applying_review_feedback(h.base_state(wi=minimal_item(phase, version)), WI, now="t")
    except Exception as exc:  # noqa: BLE001 -- the phase refusal
        if not wp.is_workflow_exception(exc):
            raise
        return False
    return True


COMMAND_PHASE_GATES = {
    "milestone-plan": _accepts_milestone_plan,
    "request-plan-amendment": lambda phase, version: phase in ws._AMENDMENT_REQUEST_ALLOWED_PHASES,
    "recover-implementation-provenance":
        lambda phase, version: phase in ws.bundle_generation_recovered_role_legal_committed_phases(version),
    "apply-implementation-review": _accepts_apply_implementation_review,
    "review-implementation": lambda phase, version: phase == "AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW" or (
        version == "2.2" and phase == "AWAITING_LOCAL_IMPLEMENTATION_REVIEW"),
    "approve-review": lambda phase, version: (
        phase == "AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW"
        or (version in ws.TWO_STAGE_PLAN_REVIEW_VERSIONS and phase == "AWAITING_PLAN_APPROVAL")
        or (version == "1" and phase == "AWAITING_EXTERNAL_PLAN_REVIEW")),
    "apply-functional-review": lambda phase, version: phase == "AWAITING_FUNCTIONAL_REVIEW",
    "review-functional": lambda phase, version: phase == "AWAITING_FUNCTIONAL_REVIEW",
    "accept-milestone": lambda phase, version: phase == "AWAITING_FUNCTIONAL_REVIEW",
    "milestone-implement": lambda phase, version: phase in ws.CHECKPOINT_START_LEGAL_PHASES,
}

_SLASH_COMMAND_RE = re.compile(r"(?<![\w./-])/([a-z][a-z-]+)\b")


def prose_commands(result: dict) -> set[str]:
    texts = [result["reason"]["text"], result["reason"]["remedy"] or ""]
    texts += [alternative["invocation"] or "" for alternative in result["alternatives"]]
    return {match.group(1) for text in texts for match in _SLASH_COMMAND_RE.finditer(text)} & set(COMMAND_PHASE_GATES)


class TestRemedyCommands(unittest.TestCase):
    def test_every_remedy_command_accepts_the_rows_phase(self):
        for row in wp.CATALOGUE:
            if row.no_item or row.disposition not in ("blocked", "human_gate", "external_gate"):
                continue
            for phase, version in sorted(row.pairs):
                for command in row.remedy_commands_for(phase, version):
                    if command == "none_exists":
                        continue
                    with self.subTest(row=row.row_id, phase=phase, version=version, command=command):
                        self.assertTrue(COMMAND_PHASE_GATES[command](phase, version))

    def test_no_command_is_both_a_remedy_and_a_refusal(self):
        for row in wp.CATALOGUE:
            for phase, version in row.pairs:
                self.assertFalse(set(row.remedy_commands_for(phase, version)) & set(row.refusing_commands), row.row_id)

    def test_the_rows_without_a_route_say_so(self):
        for row_id in ("6a", "38b", "38c"):
            row = wp.ROWS_BY_ID[row_id]
            phase, version = sorted(row.pairs)[0]
            self.assertIn("none_exists", row.remedy_commands_for(phase, version))

    def test_refusing_commands_refuse_the_rows_state(self):
        """Every command a row names only to say that it refuses does
        refuse that row's state."""
        def accept_milestone_refuses(repo, state):
            try:
                terminal, _ = ws.resolve_own_registry_completion_status(repo.root, state["work_items"][WI])
            except (ws.StalePlanApprovalRegistryReadError, ws.RegistryCoverageError):
                return True
            return not terminal

        def milestone_implement_refuses(repo, state):
            try:
                ws.transition_checkpoint_in_progress(state, WI, "C1", start_commit=repo.head(), now="t")
            except ws.IllegalCheckpointStartPhaseError:
                return True
            return False

        def amendment_refuses(repo, state):
            return state["work_items"][WI]["phase"] not in ws._AMENDMENT_REQUEST_ALLOWED_PHASES

        refusals = {"accept-milestone": accept_milestone_refuses, "milestone-implement": milestone_implement_refuses,
                    "request-plan-amendment": amendment_refuses}

        def drifted(repo):
            functional_item(repo, "2.2")
            plan = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
            plan.write_text(plan.read_text() + "drift\n")

        cases = [("38a", drifted), ("38b", lambda repo: functional_item(repo, "1", complete=False)),
                 ("38c", lambda repo: functional_item(repo, "2.2", complete=False))]
        for row_id, build in cases:
            with h.ScratchRepo() as repo:
                build(repo)
                self.assertEqual(next_action(repo)["row"], row_id)
                for command in wp.ROWS_BY_ID[row_id].refusing_commands:
                    with self.subTest(row=row_id, command=command):
                        self.assertTrue(refusals[command](repo, h.read_state(repo)))


class TestWriterSequencesEndOnLegalEdges(unittest.TestCase):
    """For each automatic `(row, gv)`, the command's writer sequence on the
    row's state ends on one of the action's legal edges."""

    def assert_edge(self, action_id, before, after, version):
        self.assertTrue(wp.edge_is_legal(action_id, before, after, version), (action_id, before, after, version))

    def test_plan_rows(self):
        for version in ("2.1", "2.2"):
            with self.subTest(version=version), h.ScratchRepo() as repo:
                h.seed_bundle_item(repo, governing_workflow_version=version, phase="PLANNING")
                h.publish_and_bind_plan_bundle(repo)
                self.assert_edge("plan.author", "PLANNING", h.read_state(repo)["work_items"][WI]["phase"], version)
            with self.subTest(version=version, row="12 and 13"), h.ScratchRepo() as repo:
                ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW", version)
                for status, expected in (("APPROVE", "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW"), ("REVISE", "REVISING_PLAN")):
                    state = ws.record_local_plan_review(h.read_state(repo), WI, verdict=status, bundle_id=ids["B"],
                                                        review_content_id=ids["P"], round=1, now="t")
                    self.assert_edge("plan.review.local", "AWAITING_LOCAL_PLAN_REVIEW",
                                     state["work_items"][WI]["phase"], version)
                    self.assertEqual(state["work_items"][WI]["phase"], expected)
            with self.subTest(version=version, row="8"), h.ScratchRepo() as repo:
                plan_item_at(repo, "REVISING_PLAN", version)
                plan = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
                plan.write_text(plan.read_text() + "the applied finding\n")
                h.publish_and_bind_plan_bundle(repo)
                self.assert_edge("plan.apply_review", "REVISING_PLAN", h.read_state(repo)["work_items"][WI]["phase"],
                                 version)

    def test_implementation_rows(self):
        for version in ("2.1", "2.2"):
            with self.subTest(version=version, row="23"), h.ScratchRepo() as repo:
                h.seed_bundle_item(repo, governing_workflow_version=version, phase="IMPLEMENTING",
                                   registry_checkpoints=CHECKPOINT_C1)
                registry = json.loads((repo.root / "docs/ai-workflow/registry/wi-registry.json").read_text())
                state = ws.transition_checkpoint_in_progress(h.read_state(repo), WI, "C1", start_commit=repo.head(),
                                                             now="t")
                self.assert_edge("implementation.checkpoint", "IMPLEMENTING", state["work_items"][WI]["phase"], version)
                state = ws.complete_checkpoint(state, WI, "C1", registry, now="t", repo_root=repo.root)
                self.assert_edge("implementation.checkpoint", "IMPLEMENTING", state["work_items"][WI]["phase"], version)
                state = ws.record_bundle_generation(state, WI, stage="implementation", head=repo.head(), now="t")
                self.assert_edge("implementation.self_review", "IMPLEMENTING", state["work_items"][WI]["phase"], version)
        with h.ScratchRepo() as repo:
            ids = implementation_item_at(repo, "2.2")
            for status in ("APPROVE", "REVISE"):
                state = ws.record_local_implementation_review(h.read_state(repo), WI, verdict=status,
                                                              bundle_id=ids["B"], review_content_id=ids["I"],
                                                              round=1, now="t")
                self.assert_edge("implementation.review.local", "AWAITING_LOCAL_IMPLEMENTATION_REVIEW",
                                 state["work_items"][WI]["phase"], "2.2")
        for version in wp.SUPPORTED_GOVERNING_VERSIONS:
            with self.subTest(version=version, row="36"):
                state = h.base_state(wi=minimal_item("APPLYING_REVIEW_FEEDBACK", version, implementation_revision=1))
                state = ws.record_bundle_generation(state, WI, stage="post-fix", head="a" * 40, now="t")
                self.assert_edge("implementation.apply_review", "APPLYING_REVIEW_FEEDBACK",
                                 state["work_items"][WI]["phase"], version)
        for version in ("1", "2.1"):
            state = ws.enter_applying_review_feedback(
                h.base_state(wi=minimal_item("AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW", version)), WI, now="t")
            self.assert_edge("implementation.apply_review", "AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW",
                             state["work_items"][WI]["phase"], version)

    def test_a_v1_plan_apply_stays_at_its_phase(self):
        state = h.base_state(wi=minimal_item("AWAITING_EXTERNAL_PLAN_REVIEW", "1"))
        state = ws.publish_plan_revision(state, WI, 2, "t")
        self.assert_edge("plan.apply_review", "AWAITING_EXTERNAL_PLAN_REVIEW", state["work_items"][WI]["phase"], "1")


# ---------------------------------------------------------------------------
# Stale decisions and reconcile (D-OP-Identity, D-OP-Reconcile)
# ---------------------------------------------------------------------------


def reconcile(repo: h.ScratchRepo, decision: dict, *extra: str) -> tuple[dict, int]:
    path = repo.root.parent / (repo.root.name + "-decision.json")
    path.write_text(json.dumps(decision))
    try:
        body, code = call("--repo-root", str(repo.root), "reconcile", "--decision", str(path), *extra)
    finally:
        path.unlink()
    if body["ok"] and body["result"]["next"] is not None:
        errors = schema_errors(body["result"]["next"], SCHEMA["$defs"]["decision"], "$.result.next")
        assert not errors, errors
    return body, code


def reconciled(test: unittest.TestCase, repo: h.ScratchRepo, decision: dict) -> dict:
    body, code = reconcile(repo, decision)
    test.assertEqual(code, 0, body)
    result = body["result"]
    allowed = wp.EDGES[decision["action"]["id"]]["allowed_results"]
    if result["class"] != "invalid":
        test.assertIn(result["class"], allowed)
    return result


class TestStaleDecision(unittest.TestCase):
    def test_an_old_identity_is_stale_decision(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, phase="PLANNING")
            identity = next_action(repo)["basis"]["state_identity"]
            self.assertEqual(next_action(repo, "--expect-state-identity", identity)["row"], "7")
            edit_item(repo, last_transition="moved on")
            body, code = call("--repo-root", str(repo.root), "next-action", "--expect-state-identity", identity)
            self.assertEqual((code, body["error"]["code"], body["error"]["retryable"]), (3, "stale_decision", True))


class TestReconcile(unittest.TestCase):
    def test_a_phase_change_is_progress(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, phase="PLANNING")
            decision = next_action(repo)
            h.publish_and_bind_plan_bundle(repo)
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["from"]["phase"], result["to"]["phase"]),
                             ("progress", "PLANNING", "AWAITING_LOCAL_PLAN_REVIEW"))
            self.assertEqual(result["next"]["row"], "12")
            self.assertEqual(result["basis"]["state_identity"], result["to"]["state_identity"])

    def checkpoint_decision(self, repo: h.ScratchRepo) -> dict:
        h.seed_bundle_item(repo, phase="IMPLEMENTING", registry_checkpoints=[{"id": "C1", "depends_on": []},
                                                                            {"id": "C2", "depends_on": ["C1"]}])
        h.approve_plan(repo)
        decision = next_action(repo)
        self.assertEqual(decision["action"]["id"], "implementation.checkpoint")
        return decision

    def complete_c1(self, repo: h.ScratchRepo, *, commit: bool) -> None:
        registry = json.loads((repo.root / "docs/ai-workflow/registry/wi-registry.json").read_text())
        state = ws.transition_checkpoint_in_progress(h.read_state(repo), WI, "C1", start_commit=repo.head(), now="t")
        state = ws.complete_checkpoint(state, WI, "C1", registry, now="t", repo_root=repo.root)
        h.write_state(repo, state)
        if commit:
            (repo.root / h.BUNDLE_ITEM_IMPLEMENTATION_PATH).write_text("C1\n")
            h.git(repo, "add", "-A")
            h.git(repo, "commit", "-q", "-m", f"C1\n\nWorkflow-Checkpoint: C1\nWorkflow-Work-Item: {WI}")

    def test_same_phase_checkpoint_progress_needs_its_trailer_commit(self):
        with h.ScratchRepo() as repo:
            decision = self.checkpoint_decision(repo)
            self.complete_c1(repo, commit=True)
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["evidence"]["completed_checkpoints"]), ("progress", ["C1"]))
        with h.ScratchRepo() as repo:
            decision = self.checkpoint_decision(repo)
            self.complete_c1(repo, commit=False)
            result = reconciled(self, repo, decision)
            self.assertEqual(result["class"], "invalid")
            self.assertEqual([reason["code"] for reason in result["invalid_reasons"]],
                             ["checkpoint_completion_unproven"])

    def revalidate_c1(self, repo: h.ScratchRepo) -> dict:
        """The Workflow's sanctioned amendment revalidation: C1 is demoted,
        then re-run through the ordinary start, complete and trailer commit,
        leaving two `Workflow-Checkpoint: C1` commits. Returns the decision
        taken before C1 first completed."""
        decision = next_action(repo)
        self.complete_c1(repo, commit=True)
        mutate(repo, _demote_checkpoint, "C1")
        self.complete_c1(repo, commit=True)
        return decision

    def test_a_revalidated_checkpoint_is_progress(self):
        with h.ScratchRepo() as repo:
            self.checkpoint_decision(repo)
            decision = self.revalidate_c1(repo)
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["evidence"]["completed_checkpoints"]), ("progress", ["C1"]))

    def test_a_revalidated_checkpoint_is_proven_by_verify(self):
        with h.ScratchRepo() as repo:
            self.checkpoint_decision(repo)
            self.revalidate_c1(repo)
            body, code = call("--repo-root", str(repo.root), "verify")
        self.assertEqual(code, wp.EXIT_OK)
        self.assertTrue(body["result"]["healthy"])
        self.assertEqual(checks_by_id(body)["checkpoint_completions_provable"]["status"], "pass")

    def test_a_reopened_checkpoint_with_only_its_earlier_trailer_is_unproven(self):
        with h.ScratchRepo() as repo:
            self.checkpoint_decision(repo)
            decision = next_action(repo)
            self.complete_c1(repo, commit=True)
            mutate(repo, _demote_checkpoint, "C1")
            self.complete_c1(repo, commit=False)
            result = reconciled(self, repo, decision)
            body, code = call("--repo-root", str(repo.root), "verify")
        self.assertEqual(result["class"], "invalid")
        self.assertEqual([reason["code"] for reason in result["invalid_reasons"]],
                         ["checkpoint_completion_unproven"])
        self.assertFalse(body["result"]["healthy"])
        self.assertEqual(checks_by_id(body)["checkpoint_completions_provable"]["status"], "fail")

    def test_an_unrelated_second_trailer_is_still_ambiguous(self):
        with h.ScratchRepo() as repo:
            decision = self.checkpoint_decision(repo)
            self.complete_c1(repo, commit=True)
            (repo.root / h.BUNDLE_ITEM_IMPLEMENTATION_PATH).write_text("again\n")
            h.git(repo, "add", "-A")
            h.git(repo, "commit", "-q", "-m", f"C1 again\n\nWorkflow-Checkpoint: C1\nWorkflow-Work-Item: {WI}")
            result = reconciled(self, repo, decision)
        self.assertEqual(result["class"], "invalid")

    def test_an_unchanged_state_and_a_started_checkpoint_are_no_progress(self):
        with h.ScratchRepo() as repo:
            decision = self.checkpoint_decision(repo)
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["from"], result["to"]["state_identity"]),
                             ("no_progress", {"phase": "IMPLEMENTING",
                                              "state_identity": decision["basis"]["state_identity"]},
                              decision["basis"]["state_identity"]))
            mutate(repo, ws.transition_checkpoint_in_progress, "C1", start_commit=repo.head(), now="t")
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["evidence"]["started_checkpoints"]), ("no_progress", ["C1"]))

    def test_an_unchanged_state_after_a_block_is_gate_reached(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            decision = next_action(repo)
            self.assertEqual(reconciled(self, repo, decision)["class"], "no_progress", "no new verdict")
            write_feedback(repo, verdict("BLOCK", rcid=ids["P"], role="LOCAL_MODEL_PLAN_REVIEW"))
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["next"]["action"]["id"]), ("gate_reached", "review.resolve_block"))

    def test_reaching_plan_approval_is_gate_reached(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
            write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW"))
            decision = next_action(repo)
            self.assertEqual(decision["action"]["id"], "plan.record_external")
            mutate(repo, ws.record_manual_plan_review, verdict="APPROVE", bundle_id=ids["B"], round=1, now="t",
                   current_review_content_id=ids["P"], feedback_role="MANUAL_EXTERNAL_PLAN_REVIEW",
                   feedback_review_content_id=ids["P"])
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["to"]["phase"], result["evidence"]["recorded_stage"]),
                             ("gate_reached", "AWAITING_PLAN_APPROVAL", "MANUAL_EXTERNAL_PLAN_REVIEW"))

    def test_a_v1_plan_apply_needs_its_revision_advance(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, governing_workflow_version="1", phase="AWAITING_EXTERNAL_PLAN_REVIEW")
            h.generate_plan_bundle(repo)
            write_feedback(repo, verdict("REVISE", bundle=current_bundle_id(repo), base=repo.base))
            decision = next_action(repo)
            self.assertEqual(decision["action"]["id"], "plan.apply_review")
            with mock.patch.object(ws, "plan_review_publication_status", side_effect=AssertionError("not for 1")):
                self.assertEqual(reconciled(self, repo, decision)["class"], "no_progress")
                audit = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_AUDIT.md"
                audit.write_text(audit.read_text() + "applied\n")
                h.generate_plan_bundle(repo)
                edit_item(repo, plan_revision=2)
                result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["next"]["row"]), ("gate_reached", "20"))

    def test_plan_start(self):
        with h.ScratchRepo() as repo:
            write_config(repo, "2.2")
            write_state(repo, h.base_state(old=minimal_item("MILESTONE_COMPLETE", "2.2", work_item_id="old")))
            decision = next_action(repo)
            self.assertEqual(decision["action"]["id"], "plan.start")
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["from"], result["to"], result["basis"]),
                             ("no_progress", None, None, None))
            state = h.base_state(old=minimal_item("MILESTONE_COMPLETE", "2.2", work_item_id="old"),
                                 wi=minimal_item("PLANNING", "2.2", base_commit=repo.base))
            state["active_work_item_id"] = WI
            write_state(repo, state)
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["from"], result["to"]["phase"]), ("progress", None, "PLANNING"))
            for active, extra in ((WI, {"third": minimal_item("PLANNING", "2.2", work_item_id="third",
                                                                base_commit=repo.base)}),
                                  ("third", {"third": minimal_item("PLANNING", "2.2", work_item_id="third",
                                                                     base_commit=repo.base)})):
                state = h.base_state(old=minimal_item("MILESTONE_COMPLETE", "2.2", work_item_id="old"),
                                     wi=minimal_item("PLANNING", "2.2", base_commit=repo.base), **extra)
                state["active_work_item_id"] = active
                write_state(repo, state)
                result = reconciled(self, repo, decision)
                self.assertEqual((result["class"], result["invalid_reasons"][0]["code"]),
                                 ("invalid", "plan_start_item_ambiguous"))
            state = h.base_state(old=minimal_item("AMENDING_PLAN", "2.2", work_item_id="old", base_commit=repo.base))
            state["active_work_item_id"] = "old"
            write_state(repo, state)
            self.assertEqual(reconciled(self, repo, decision)["invalid_reasons"][0]["code"], "plan_start_item_ambiguous")

    def test_a_class_outside_allowed_results_is_invalid(self):
        with h.ScratchRepo() as repo:
            edges = dict(wp.EDGES["implementation.checkpoint"], allowed_results=["progress"])
            with mock.patch.dict(wp.EDGES, {"implementation.checkpoint": edges}):
                decision = self.checkpoint_decision(repo)
                result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["invalid_reasons"][0]["code"]), ("invalid", "result_not_allowed"))

    def test_an_illegal_edge_and_milestone_complete_are_invalid(self):
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            decision = next_action(repo)
            edit_item(repo, phase="IMPLEMENTING")
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["invalid_reasons"][0]["code"]), ("invalid", "illegal_edge"))
            state = edit_item(repo, phase="MILESTONE_COMPLETE")
            state["active_work_item_id"] = None  # as complete_work_item leaves it
            h.write_state(repo, state)
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["invalid_reasons"][0]["code"]), ("invalid", "illegal_edge"))
            self.assertNotIn("complete", wp.RECONCILE_CLASSES)
            self.assertEqual((result["next"]["row"], result["next"]["disposition"]), ("40", "complete"))

    def test_a_review_phase_reached_with_a_marker_or_unbound_is_invalid(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, phase="PLANNING")
            decision = next_action(repo)
            h.publish_and_bind_plan_bundle(repo)
            reject_bundle(repo)
            codes = [reason["code"] for reason in reconciled(self, repo, decision)["invalid_reasons"]]
            self.assertIn("bundle_rejected", codes)
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, phase="PLANNING")
            decision = next_action(repo)
            edit_item(repo, phase="AWAITING_LOCAL_PLAN_REVIEW")
            result = reconciled(self, repo, decision)
            self.assertEqual(result["class"], "invalid")
            self.assertIn("plan_review_not_bound", [reason["code"] for reason in result["invalid_reasons"]])

    def test_a_foreign_tampered_or_gate_decision_is_invalid_request(self):
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW")
            decision = next_action(repo)
            tampered = json.loads(json.dumps(decision))
            tampered["action"]["id"] = "implementation.checkpoint"
            tampered["action"]["allowed_results"] = wp.EDGES["implementation.checkpoint"]["allowed_results"]
            invocation = json.loads(json.dumps(decision))
            invocation["action"]["invocation"] = "/review-plan someone-else"
            foreign = json.loads(json.dumps(decision))
            foreign["basis"]["work_item_id"] = "nobody"
            foreign["action"]["arguments"]["work_item_id"] = "nobody"
            foreign["action"]["invocation"] = "/review-plan nobody"
            for name, bad in (("tampered action", tampered), ("tampered invocation", invocation),
                              ("unknown item", foreign)):
                with self.subTest(case=name):
                    body, code = reconcile(repo, bad)
                    self.assertEqual((code, body["error"]["code"]), (2, "invalid_request"))
            body, code = reconcile(repo, decision, "--work-item", "another")
            self.assertEqual((code, body["error"]["code"]), (2, "invalid_request"))
            edit_item(repo, phase="AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW")
            gate = next_action(repo)
            self.assertEqual(gate["disposition"], "external_gate")
            body, code = reconcile(repo, gate)
            self.assertEqual((code, body["error"]["code"]), (2, "invalid_request"))
            body, code = call("--repo-root", str(repo.root), "reconcile", "--decision", str(repo.root / "missing.json"))
            self.assertEqual((code, body["error"]["code"]), (2, "invalid_request"))

    def test_the_full_envelope_is_accepted_as_the_decision(self):
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, phase="PLANNING")
            body, _code = call("--repo-root", str(repo.root), "next-action")
            self.assertEqual(reconcile(repo, body)[0]["result"]["class"], "no_progress")


class TestNeverWrites(unittest.TestCase):
    def test_next_action_and_reconcile_leave_the_state_untouched(self):
        with h.ScratchRepo() as repo:
            ids = plan_item_at(repo, "REVISING_PLAN")
            write_feedback(repo, verdict("REVISE", rcid=ids["P"]))
            state_path = repo.root / ws.DEFAULT_STATE_PATH
            before = (state_path.read_bytes(), state_path.stat().st_mtime_ns)
            status_before = h.git(repo, "status", "--porcelain", "--ignored")
            decision = next_action(repo)
            reconcile(repo, decision)
            self.assertEqual((state_path.read_bytes(), state_path.stat().st_mtime_ns), before)
            self.assertEqual(h.git(repo, "status", "--porcelain", "--ignored"), status_before)


class TestIngestToApplyRouting(unittest.TestCase):
    """`MPR-R8-001`: every verdict a stage ingest records leads to the
    stage's apply action, whose command then accepts the state, or to a
    gate -- never to a different automatic action (`plan.author` in
    particular). The ingests are recorded through their state writers here;
    CP5's `record-external-result` calls the same writers."""

    PLAN_VARIANTS = {
        "full": lambda ids, repo: verdict("REVISE", rcid=ids["P"], bundle=ids["B"], base=repo.base,
                                          role="MANUAL_EXTERNAL_PLAN_REVIEW"),
        "no bundle fields": lambda ids, repo: verdict("REVISE", rcid=ids["P"], work_item=None,
                                                      role="MANUAL_EXTERNAL_PLAN_REVIEW"),
        "stale bundle id": lambda ids, repo: verdict("REVISE", rcid=ids["P"], bundle="f" * 64,
                                                     role="MANUAL_EXTERNAL_PLAN_REVIEW"),
    }

    def test_plan_stage(self):
        for version in ("2.1", "2.2"):
            for name, build in self.PLAN_VARIANTS.items():
                with self.subTest(version=version, verdict=name), h.ScratchRepo() as repo:
                    ids = plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW", version)
                    write_feedback(repo, build(ids, repo))
                    mutate(repo, ws.record_manual_plan_review, verdict="REVISE", bundle_id=ids["B"], round=1,
                           now="t", current_review_content_id=ids["P"], feedback_role="MANUAL_EXTERNAL_PLAN_REVIEW",
                           feedback_review_content_id=ids["P"])
                    result = next_action(repo)
                    self.assertEqual((result["row"], result["action"]["id"]), ("8", "plan.apply_review"))
                    COMMAND_GUARDS["plan.apply_review"][0](repo, h.read_state(repo))
            with self.subTest(version=version, verdict="local REVISE"), h.ScratchRepo() as repo:
                ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW", version)
                write_feedback(repo, verdict("REVISE", rcid=ids["P"], bundle=ids["B"], base=repo.base,
                                             role="LOCAL_MODEL_PLAN_REVIEW"))
                mutate(repo, ws.record_local_plan_review, verdict="REVISE", bundle_id=ids["B"],
                       review_content_id=ids["P"], round=1, now="t")
                self.assertEqual(next_action(repo)["row"], "8")
            with self.subTest(version=version, verdict="APPROVEs"), h.ScratchRepo() as repo:
                ids = plan_item_at(repo, "AWAITING_LOCAL_PLAN_REVIEW", version)
                write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="LOCAL_MODEL_PLAN_REVIEW"))
                mutate(repo, ws.record_local_plan_review, verdict="APPROVE", bundle_id=ids["B"],
                       review_content_id=ids["P"], round=1, now="t")
                self.assertEqual(next_action(repo)["disposition"], "external_gate")
                write_feedback(repo, verdict("APPROVE", rcid=ids["P"], role="MANUAL_EXTERNAL_PLAN_REVIEW"))
                mutate(repo, ws.record_manual_plan_review, verdict="APPROVE", bundle_id=ids["B"], round=1, now="t",
                       current_review_content_id=ids["P"], feedback_role="MANUAL_EXTERNAL_PLAN_REVIEW",
                       feedback_review_content_id=ids["P"])
                self.assertEqual(next_action(repo)["disposition"], "human_gate")

    def test_implementation_stage(self):
        variants = {
            "full": lambda ids, repo: verdict("REVISE", rcid=ids["I"], bundle=ids["B"], base=repo.base,
                                              role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"),
            "no bundle fields": lambda ids, repo: verdict("REVISE", rcid=ids["I"], work_item=None,
                                                          role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"),
            "stale bundle id": lambda ids, repo: verdict("REVISE", rcid=ids["I"], bundle="f" * 64,
                                                         role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"),
        }
        for name, build in variants.items():
            with self.subTest(verdict=name), h.ScratchRepo() as repo:
                ids = implementation_at_manual(repo)
                write_feedback(repo, build(ids, repo))
                mutate(repo, ws.record_manual_implementation_review, verdict="REVISE", bundle_id=ids["B"], round=1,
                       now="t", current_review_content_id=ids["I"],
                       feedback_role="MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW", feedback_review_content_id=ids["I"])
                result = next_action(repo)
                self.assertEqual((result["row"], result["action"]["id"]), ("36", "implementation.apply_review"))
                self.assertEqual(COMMAND_GUARDS["implementation.apply_review"][0](repo, h.read_state(repo))["binding"],
                                 "content")
        with h.ScratchRepo() as repo:
            ids = implementation_item_at(repo, "2.2")
            write_feedback(repo, verdict("REVISE", rcid=ids["I"], bundle=ids["B"], base=repo.base,
                                         role="LOCAL_MODEL_IMPLEMENTATION_REVIEW"))
            mutate(repo, ws.record_local_implementation_review, verdict="REVISE", bundle_id=ids["B"],
                   review_content_id=ids["I"], round=1, now="t")
            self.assertEqual(next_action(repo)["row"], "36")
        with h.ScratchRepo() as repo:
            implementation_at_external_2_2(repo)
            self.assertEqual(next_action(repo)["disposition"], "human_gate")


class TestPlanGateRace(unittest.TestCase):
    def test_a_binding_changed_between_the_two_reads_is_plan_review_bundle_unbound(self):
        """Rows 5 and 10 read the publication status first; if it changes
        before the gate wrapper's own read, the wrapper still reports it."""
        with h.ScratchRepo() as repo:
            plan_item_at(repo, "AWAITING_PLAN_APPROVAL")
            state = h.read_state(repo)
            bound = ws.plan_review_publication_status(repo.root, state, WI)
            plan = repo.root / "docs" / "ai-workflow" / "WORKFLOW_V2_PLAN.md"
            plan.write_text(plan.read_text() + "changed between the reads\n")
            real = ws.plan_review_publication_status
            calls = {"n": 0}

            def first_read_is_stale(*args, **kwargs):
                calls["n"] += 1
                return dict(bound) if calls["n"] == 1 else real(*args, **kwargs)

            with mock.patch.object(ws, "plan_review_publication_status", side_effect=first_read_is_stale):
                result = next_action(repo)
            self.assertEqual((result["row"], result["reason"]["code"]), ("16", "plan_review_bundle_unbound"))


# ---------------------------------------------------------------------------
# record-external-result (D-OP-External, CP5)
# ---------------------------------------------------------------------------


def record_external(repo: h.ScratchRepo, kind: str, text: str, work_item: str = WI) -> tuple[dict, int]:
    """`record-external-result` in-process, schema-checked, with `text` as
    its input file (outside the repository)."""
    tmp = Path(repo.root).parent / f"{Path(repo.root).name}-verdict.md"
    tmp.write_text(text)
    try:
        return call("--repo-root", str(repo.root), "record-external-result", "--work-item", work_item,
                    "--kind", kind, "--input", str(tmp))
    finally:
        tmp.unlink(missing_ok=True)


def recorded(test: unittest.TestCase, repo: h.ScratchRepo, kind: str, text: str) -> dict:
    body, code = record_external(repo, kind, text)
    test.assertEqual(code, wp.EXIT_OK, body)
    return body["result"]


def refusal(test: unittest.TestCase, repo: h.ScratchRepo, kind: str, text: str, code: str,
            native: str | None = None) -> dict:
    """Refused with `code` (and the `native` exception), writing nothing."""
    state_path = repo.root / ws.DEFAULT_STATE_PATH
    before = (state_path.read_bytes(), _fb_text(repo))
    body, exit_code = record_external(repo, kind, text)
    test.assertEqual((exit_code, body["error"]["code"]), (wp.exit_code_for(code), code), body)
    if native is not None:
        test.assertEqual(body["error"]["native"]["exception"], native, body)
    test.assertEqual((state_path.read_bytes(), _fb_text(repo)), before)
    return body["error"]


_TWO_STAGE_KINDS = {
    "plan_review_verdict": ("MANUAL_EXTERNAL_PLAN_REVIEW", "P",
                            lambda repo, version: plan_item_at(repo, "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW", version),
                            ("2.1", "2.2")),
    "implementation_review_verdict": ("MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW", "I",
                                      lambda repo, version: implementation_at_manual(repo), ("2.2",)),
}


def _feedback_only_item(repo: h.ScratchRepo, kind: str, version: str) -> str:
    """An item at a feedback-only row's phase with its bundle generated.
    Returns the bundle id."""
    if kind == "plan_review_verdict":
        h.seed_bundle_item(repo, governing_workflow_version=version, phase="AWAITING_EXTERNAL_PLAN_REVIEW")
        h.generate_plan_bundle(repo)
    else:
        implementation_item_at(repo, version)
    return current_bundle_id(repo)


_FEEDBACK_ONLY_ROWS = (("plan_review_verdict", "1"), ("implementation_review_verdict", "1"),
                       ("implementation_review_verdict", "2.1"))


class TestRecordExternalResultTwoStage(unittest.TestCase):
    def test_each_verdict_records_the_command_paths_state(self):
        for kind, (role, key, build, versions) in _TWO_STAGE_KINDS.items():
            writer = ws.record_manual_plan_review if kind == "plan_review_verdict" else ws.record_manual_implementation_review
            for version in versions:
                for status in ("APPROVE", "REVISE", "BLOCK"):
                    with self.subTest(kind=kind, version=version, status=status), h.ScratchRepo() as repo:
                        ids = build(repo, version)
                        before = h.read_state(repo)
                        text = verdict(status, rcid=ids[key], bundle=ids["B"], base=repo.base, role=role)
                        result = recorded(self, repo, kind, text)
                        after = h.read_state(repo)
                        now = after["work_items"][WI]["last_transition"]
                        expected = writer(before, WI, verdict=status, bundle_id=ids["B"], round=1, now=now,
                                          current_review_content_id=ids[key], feedback_role=role,
                                          feedback_review_content_id=ids[key])
                        self.assertEqual(after, expected)
                        self.assertEqual(_fb_text(repo), text)
                        self.assertEqual(
                            {k: result[k] for k in ("stage", "verdict", "review_content_id", "round", "bundle_id",
                                                    "advisory")},
                            {"stage": "plan" if kind == "plan_review_verdict" else "implementation",
                             "verdict": status, "review_content_id": ids[key], "round": 1, "bundle_id": ids["B"],
                             "advisory": None})
                        self.assertEqual(result["basis"], wp.basis(repo.root, after, WI))

    def test_the_command_path_and_the_protocol_path_give_the_same_values(self):
        """`round` and `bundle_id` (`LPR-R3-005`): a stated `Round:` and an
        absent bundle id, through both paths."""
        for kind, (role, key, build, versions) in _TWO_STAGE_KINDS.items():
            stage = "plan" if kind == "plan_review_verdict" else "implementation"
            for path in ("command", "protocol"):
                with self.subTest(kind=kind, path=path), h.ScratchRepo() as repo:
                    ids = build(repo, versions[-1])
                    text = verdict("APPROVE", rcid=ids[key], role=role).replace(
                        "Status: APPROVE\n", "Status: APPROVE\nRound: 4\n")
                    if path == "command":
                        result = ws.ingest_manual_review_verdict(repo.root, WI, stage=stage, verdict_text=text,
                                                                 now="t", two_stage_only=True)
                    else:
                        result = recorded(self, repo, kind, text)
                    self.assertEqual((result["round"], result["bundle_id"], result["advisory"]),
                                     (4, None, ws.ABSENT_REVIEWED_BUNDLE_ID_ADVISORY))

    def test_refusals(self):
        for kind, (role, key, build, versions) in _TWO_STAGE_KINDS.items():
            with self.subTest(kind=kind), h.ScratchRepo() as repo:
                ids = build(repo, versions[-1])
                ok = dict(rcid=ids[key], bundle=ids["B"], role=role)
                refusal(self, repo, kind, verdict("APPROVE", **dict(ok, rcid=None)), "refused",
                        "ManualVerdictHeaderError")
                refusal(self, repo, kind, verdict("APPROVE", **ok, work_item="other-item"), "refused",
                        "ManualFeedbackForeignWorkItemError")
                refusal(self, repo, kind, verdict("APPROVE", **dict(ok, role="LOCAL_MODEL_PLAN_REVIEW")), "refused",
                        "WrongReviewerRoleError")
                refusal(self, repo, kind, verdict("APPROVE", **dict(ok, rcid="e" * 64)), "refused",
                        "StaleReviewContentIdError")
                reject_bundle(repo)
                refusal(self, repo, kind, verdict("APPROVE", **ok), "refused", "BundleRejectedError")

    def test_a_duplicate_is_not_applicable(self):
        for kind, (role, key, build, versions) in _TWO_STAGE_KINDS.items():
            with self.subTest(kind=kind), h.ScratchRepo() as repo:
                ids = build(repo, versions[-1])
                state = h.read_state(repo)
                ledger = state["work_items"][WI]["plan_review_stages" if key == "P" else "implementation_review_stages"]
                local = next(k for k in ledger if k.startswith("LOCAL_MODEL"))
                ledger[role] = dict(ledger[local])
                h.write_state(repo, state)
                refusal(self, repo, kind, verdict("APPROVE", rcid=ids[key], bundle=ids["B"], role=role),
                        "not_applicable")

    def test_a_retry_after_the_record_is_not_applicable(self):
        for kind, (role, key, build, versions) in _TWO_STAGE_KINDS.items():
            with self.subTest(kind=kind), h.ScratchRepo() as repo:
                ids = build(repo, versions[-1])
                text = verdict("APPROVE", rcid=ids[key], bundle=ids["B"], role=role)
                recorded(self, repo, kind, text)
                refusal(self, repo, kind, text, "not_applicable")

    def test_the_crash_window_is_retried_once_through_either_path(self):
        """The file is written and the state write fails: the item stays at
        its phase, next-action reports the unrecorded verdict (rows 13 and
        27), and a retry through the command path or the protocol records
        it once."""
        for kind, (role, key, build, versions) in _TWO_STAGE_KINDS.items():
            stage = "plan" if kind == "plan_review_verdict" else "implementation"
            for retry in ("command", "protocol"):
                with self.subTest(kind=kind, retry=retry), h.ScratchRepo() as repo:
                    ids = build(repo, versions[-1])
                    text = verdict("REVISE", rcid=ids[key], bundle=ids["B"], role=role)
                    revision = h.read_state(repo)["work_items"][WI]["state_revision"]
                    with mock.patch.object(ws, "_publish_state_file", side_effect=OSError("disk full")):
                        body, code = record_external(repo, kind, text)
                    self.assertEqual((code, body["error"]["code"]), (wp.EXIT_INTERNAL, "internal_error"))
                    self.assertEqual(_fb_text(repo), text)
                    self.assertEqual(next_action(repo)["row"], "13" if stage == "plan" else "27")
                    if retry == "command":
                        ws.ingest_manual_review_verdict(repo.root, WI, stage=stage, verdict_text=text, now="t",
                                                        two_stage_only=True)
                    else:
                        recorded(self, repo, kind, text)
                    self.assertEqual(h.read_state(repo)["work_items"][WI]["state_revision"], revision + 1)
                    refusal(self, repo, kind, text, "not_applicable")

    def test_a_manual_revise_without_current_bundle_fields_routes_to_its_apply(self):
        """`MPR-R8-001`: recorded by the bundle-id rule, then the stage's
        apply action, whose command accepts the stored file by content."""
        for kind, (role, key, build, versions) in _TWO_STAGE_KINDS.items():
            for version in versions:
                for variant in ("absent", "pre-regeneration"):
                    with self.subTest(kind=kind, version=version, variant=variant), h.ScratchRepo() as repo:
                        ids = build(repo, version)
                        bundle = None
                        if variant == "pre-regeneration":
                            bundle = ids["B"]
                            if kind == "plan_review_verdict":
                                regenerate_wrapper_only(repo)
                            else:
                                summary = bundle_dir(repo) / "IMPLEMENTATION_SUMMARY.md"
                                summary.write_text(summary.read_text() + "wrapper-only rerun\n")
                                h._run_generator(repo, "implementation", WI)
                            self.assertNotEqual(current_bundle_id(repo), bundle)
                        result = recorded(self, repo, kind, verdict("REVISE", rcid=ids[key], bundle=bundle,
                                                                    role=role))
                        self.assertEqual(result["bundle_id"], bundle)
                        if bundle is None:
                            self.assertEqual(result["advisory"], ws.ABSENT_REVIEWED_BUNDLE_ID_ADVISORY)
                        else:
                            self.assertIn("advisory only", result["advisory"])
                        decision = next_action(repo)
                        action = "plan.apply_review" if kind == "plan_review_verdict" else "implementation.apply_review"
                        self.assertEqual((decision["row"], decision["action"]["id"]),
                                         ("8" if kind == "plan_review_verdict" else "36", action))
                        self.assertEqual(COMMAND_GUARDS[action][0](repo, h.read_state(repo))["binding"], "content")


class TestRecordExternalResultFeedbackOnly(unittest.TestCase):
    def test_stored_with_and_without_the_label_and_the_state_unchanged(self):
        for kind, version in _FEEDBACK_ONLY_ROWS:
            for label in (True, False):
                with self.subTest(kind=kind, version=version, label=label), h.ScratchRepo() as repo:
                    B = _feedback_only_item(repo, kind, version)
                    rcid = "c" * 64 if label else None
                    text = verdict("REVISE", rcid=rcid, bundle=B, base=repo.base)
                    state_before = (repo.root / ws.DEFAULT_STATE_PATH).read_bytes()
                    result = recorded(self, repo, kind, text)
                    self.assertEqual((repo.root / ws.DEFAULT_STATE_PATH).read_bytes(), state_before)
                    self.assertEqual(_fb_text(repo), text)
                    self.assertEqual((result["verdict"], result["review_content_id"], result["round"],
                                      result["bundle_id"], result["advisory"]), ("REVISE", rcid, None, None, None))
                    fingerprint.assert_feedback_matches_bundle(
                        fingerprint.parse_review_feedback_binding_fields(_fb_text(repo)),
                        bundle_id=B, base_commit=repo.base, work_item_id=WI)

    def test_refusals(self):
        for kind, version in _FEEDBACK_ONLY_ROWS:
            with self.subTest(kind=kind, version=version), h.ScratchRepo() as repo:
                B = _feedback_only_item(repo, kind, version)
                refusal(self, repo, kind, verdict("APPROVE", bundle=B, base=repo.base, work_item="other-item"),
                        "refused", "ManualFeedbackForeignWorkItemError")
                refusal(self, repo, kind, verdict("APPROVE", bundle="f" * 64, base=repo.base), "refused",
                        "FeedbackBundleMismatchError")
                refusal(self, repo, kind, verdict("APPROVE", base=repo.base), "refused", "ManualVerdictHeaderError")
                reject_bundle(repo)
                refusal(self, repo, kind, verdict("APPROVE", bundle=B, base=repo.base), "refused",
                        "BundleRejectedError")

    def test_a_different_current_verdict_conflicts_and_an_earlier_rounds_is_replaced(self):
        for kind, version in _FEEDBACK_ONLY_ROWS:
            with self.subTest(kind=kind, version=version), h.ScratchRepo() as repo:
                B = _feedback_only_item(repo, kind, version)
                first = verdict("APPROVE", bundle=B, base=repo.base)
                recorded(self, repo, kind, first)
                refusal(self, repo, kind, verdict("REVISE", bundle=B, base=repo.base), "refused",
                        "ConflictingReviewFeedbackError")
                recorded(self, repo, kind, first)
                write_feedback(repo, verdict("APPROVE", bundle="f" * 64, base=repo.base))
                recorded(self, repo, kind, first)
                self.assertEqual(_fb_text(repo), first)


class TestRecordExternalResultApplicability(unittest.TestCase):
    def test_reserved_and_unknown_kinds(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=minimal_item("IMPLEMENTING", "2.2")))
            for kind in wp.RESERVED_RESULT_KINDS:
                with self.subTest(kind=kind):
                    refusal(self, repo, kind, "anything", "unsupported_result_kind")
            refusal(self, repo, "no_such_kind", "anything", "invalid_request")

    def test_the_wrong_phase_is_not_applicable(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=minimal_item("IMPLEMENTING", "2.2")))
            for kind in wp.EXTERNAL_RESULT_KINDS:
                with self.subTest(kind=kind):
                    refusal(self, repo, kind, verdict("APPROVE", rcid="a" * 64), "not_applicable")

    def test_a_kind_at_the_other_shape_of_row_is_not_applicable(self):
        """A two-stage kind's phase at a `"1"`/`"2.1"` item, and a
        feedback-only phase at a two-stage item."""
        cases = [
            ("plan_review_verdict", "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW", "1"),
            ("implementation_review_verdict", "AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW", "2.1"),
            ("plan_review_verdict", "AWAITING_EXTERNAL_PLAN_REVIEW", "2.2"),
            ("implementation_review_verdict", "AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW", "2.2"),
        ]
        for kind, phase, version in cases:
            with self.subTest(kind=kind, phase=phase, version=version), h.ScratchRepo() as repo, \
                    mock.patch.object(ws, "validate_state"):
                write_state(repo, h.base_state(wi=minimal_item(phase, version)))
                refusal(self, repo, kind, verdict("APPROVE", rcid="a" * 64, bundle="b" * 64, base="0" * 40),
                        "not_applicable")

    def test_an_unknown_work_item_and_an_unreadable_input(self):
        with h.ScratchRepo() as repo:
            write_state(repo, h.base_state(wi=minimal_item("IMPLEMENTING", "2.2")))
            body, _code = record_external(repo, "plan_review_verdict", "x", work_item="nope")
            self.assertEqual(body["error"]["code"], "unknown_work_item")
            body, code = call("--repo-root", str(repo.root), "record-external-result", "--work-item", WI,
                              "--kind", "plan_review_verdict", "--input", str(repo.root / "missing.md"))
            self.assertEqual((code, body["error"]["code"]), (wp.EXIT_INVALID_REQUEST, "invalid_request"))



# ---------------------------------------------------------------------------
# The specification (CP6): ORCHESTRATION_PROTOCOL.md's mirrored tables
# ---------------------------------------------------------------------------

SPEC_PATH = Path(__file__).resolve().parent.parent / "docs" / "ai-workflow" / "ORCHESTRATION_PROTOCOL.md"
_VERSION_ORDER = ("1", "2.1", "2.2")


def spec_table(header: str) -> list[list[str]]:
    """The body rows of the specification's one Markdown table whose header
    line is exactly `header`, each as its stripped cells."""
    lines = SPEC_PATH.read_text().splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == header]
    assert len(starts) == 1, f"{len(starts)} tables with header {header!r}"
    rows = []
    for line in lines[starts[0] + 2:]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def _ticked(cell: str) -> list[str]:
    """The backticked values of a cell, in order; `—` and `none` are none."""
    return re.findall(r"`([^`]*)`", cell)


def _single(cell: str) -> str | None:
    if cell in ("—", "none"):
        return None
    values = _ticked(cell)
    assert len(values) == 1 and cell == f"`{values[0]}`", cell
    return values[0]


def _pairs(phases_cell: str, versions_cell: str) -> frozenset:
    if versions_cell != "as listed":
        return frozenset((phase, version) for phase in _ticked(phases_cell) for version in _ticked(versions_cell))
    pairs = set()
    for entry in phases_cell.split(", "):
        match = re.fullmatch(r"`([A-Z_]+)` at (.+)", entry)
        assert match, entry
        pairs |= {(match.group(1), version) for version in _ticked(match.group(2))}
    return frozenset(pairs)


def _versions(cell: str) -> list[str]:
    versions = _ticked(cell)
    assert versions == [v for v in _VERSION_ORDER if v in versions], cell
    return versions


_CATALOGUE_HEADER = "| row | phases | gv | condition | disposition | action | reason, invocation and notes |"


def catalogue_table_mismatches() -> list[str]:
    """Every difference between the specification's catalogue table and
    `CATALOGUE`: the row ids in order, then each row's `(phase, gv)`
    pairs, disposition and action id."""
    rows = spec_table(_CATALOGUE_HEADER)
    ids = [cells[0] for cells in rows]
    if ids != list(wp.ROW_IDS):
        return [f"row ids {ids} != {list(wp.ROW_IDS)}"]
    mismatches = []
    for (row_id, phases, versions, _condition, disposition, action, _notes), row in zip(rows, wp.CATALOGUE):
        pairs = frozenset() if (phases, versions) == ("—", "—") else _pairs(phases, versions)
        expected = (frozenset() if row.no_item else row.pairs, row.disposition, row.action_id)
        if (pairs, disposition, _single(action)) != expected:
            mismatches.append(f"row {row_id}: {(sorted(pairs), disposition, _single(action))} != "
                              f"{(sorted(expected[0]), *expected[1:])}")
    return mismatches


class TestSpecificationTablesEqualTheCode(unittest.TestCase):
    """`ORCHESTRATION_PROTOCOL.md` is normative, and its mirrored tables are
    parsed and compared with the module's own, row for row and in order:
    the catalogue, the condition calls, the legal edges with their proofs
    and `allowed_results`, and the actions."""

    def test_the_catalogue_table_is_the_catalogue_in_order(self):
        self.assertEqual(catalogue_table_mismatches(), [])

    def test_the_condition_call_table_is_condition_calls(self):
        rows = spec_table("| row | call | kind | classes |")
        parsed: dict[str, list[dict]] = {}
        for row_id, function, kind, classes in rows:
            calls = parsed.setdefault(row_id, [])
            if function == "—":
                self.assertEqual((kind, classes), ("—", "—"), row_id)
                continue
            calls.append({"function": _single(function), "kind": kind, "classes": _ticked(classes)})
        self.assertEqual(list(parsed), list(wp.ROW_IDS), "every row, in catalogue order")
        self.assertEqual(parsed, wp.CONDITION_CALLS)

    def test_the_edge_table_is_the_legal_edges(self):
        rows = spec_table("| action id | from | to | gv |")
        parsed: dict[str, list[dict]] = {}
        for action, source, target, versions in rows:
            parsed.setdefault(_single(action), []).append(
                {"from": _single(source), "to": _single(target), "versions": _versions(versions)})
        self.assertEqual(list(parsed), list(wp.EDGES))
        self.assertEqual(parsed, {action: entry["edges"] for action, entry in wp.EDGES.items()})

    def test_the_proof_table_is_the_proofs_and_allowed_results(self):
        rows = spec_table("| action id | same-phase proof | allowed_results |")
        parsed = {_single(action): {"proof": _single(proof), "allowed_results": _ticked(allowed)}
                  for action, proof, allowed in rows}
        self.assertEqual(list(parsed), list(wp.EDGES))
        self.assertEqual(parsed, {action: {"proof": entry["proof"], "allowed_results": entry["allowed_results"]}
                                  for action, entry in wp.EDGES.items()})
        for proof in {entry["proof"] for entry in wp.EDGES.values()} - {None}:
            self.assertIn(f"- `{proof}`:", SPEC_PATH.read_text(), "each proof is defined")

    def test_the_action_table_is_the_actions(self):
        rows = spec_table("| action id | command | invocation | role | fresh_session | independent_of | user_only |")
        parsed = {}
        for action, command, invocation, role, fresh, independent, user_only in rows:
            self.assertIn(fresh, ("yes", "no"))
            self.assertIn(user_only, ("yes", "no"))
            parsed[_single(action)] = {
                "command": _single(command), "invocation": _single(invocation), "role": _single(role),
                "fresh_session": fresh == "yes", "independent_of": _ticked(independent),
                "user_only": user_only == "yes",
            }
        self.assertEqual(list(parsed), list(wp.ACTION_IDS))
        self.assertEqual(parsed, wp.ACTIONS)

    def test_the_vocabulary_tables_name_the_code_values(self):
        text = SPEC_PATH.read_text()
        codes = spec_table("| code | meaning | retryable |")
        self.assertEqual([_single(cells[0]) for cells in codes], list(wp.ERROR_CODES))
        self.assertEqual({_single(cells[0]): cells[2] != "no" for cells in codes}, wp.ERROR_CODES)
        kinds = spec_table("| kind | resolved by |")
        self.assertEqual([_single(cells[0]) for cells in kinds], list(wp.ARTIFACT_KINDS))
        exits = spec_table("| exit code | meaning |")
        self.assertEqual([_single(cells[0]) for cells in exits],
                         [str(c) for c in (wp.EXIT_OK, wp.EXIT_REFUSED, wp.EXIT_INVALID_REQUEST, wp.EXIT_INTERNAL)])
        for check_id in wp.VERIFY_CHECK_IDS:
            self.assertIn(f"`{check_id}`", text)
        for name in (*wp.DISPOSITIONS, *wp.WORKER_ROLES, *wp.EXTERNAL_RESULT_KINDS, *wp.RESERVED_RESULT_KINDS,
                     *wp.RECONCILE_CLASSES, *wp.WORKFLOW_EXCEPTION_CODES):
            self.assertIn(f"`{name}`", text)
        self.assertIn(f'"version": "{wp.PROTOCOL_VERSION}"', text)
        self.assertIn(f"**Workflow {wp.WORKFLOW_RELEASE}**", text, "the tested releases name this one")

    def test_the_ingest_table_names_each_rows_kind_and_versions(self):
        rows = spec_table("| kind | gv | accepted phase | required header fields | guards, in order | records |")
        self.assertEqual(
            [(_single(kind), tuple(_versions(versions)), _single(phase)) for kind, versions, phase, *_ in rows],
            [("plan_review_verdict", ("2.1", "2.2"), "AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW"),
             ("implementation_review_verdict", ("2.2",), "AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW"),
             ("plan_review_verdict", ("1",), "AWAITING_EXTERNAL_PLAN_REVIEW"),
             ("implementation_review_verdict", ("1", "2.1"), "AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW")])
        for kind, versions, phase, _fields, _guards, records in rows:
            stage = wp.EXTERNAL_RESULT_KIND_STAGES[_single(kind)]
            for version in _versions(versions):
                with self.subTest(kind=kind, version=version):
                    item = minimal_item(_single(phase), version)
                    self.assertEqual(ws.select_manual_verdict_row(item, stage=stage),
                                     {"stage": stage, "two_stage": records != "nothing (feedback only)",
                                      "phase": _single(phase)})

    def test_the_parser_catches_a_drifted_table(self):
        real = SPEC_PATH.read_text()
        drifted = real.replace("| 23 | `IMPLEMENTING` | `2.1`, `2.2` |", "| 23 | `IMPLEMENTING` | `2.2` |", 1)
        self.assertNotEqual(drifted, real)
        with mock.patch(f"{__name__}.SPEC_PATH", _DriftedSpec(drifted)):
            self.assertEqual(catalogue_table_mismatches(), [
                f"row 23: {([('IMPLEMENTING', '2.2')], 'automatic', 'implementation.checkpoint')} != "
                f"{([('IMPLEMENTING', '2.1'), ('IMPLEMENTING', '2.2')], 'automatic', 'implementation.checkpoint')}"])


class _DriftedSpec:
    """A stand-in for `SPEC_PATH` whose text is given."""

    def __init__(self, text: str):
        self._text = text

    def read_text(self) -> str:
        return self._text


class TestOperatorDocuments(unittest.TestCase):
    """CP6's command and operator documentation."""

    def accept_step_2a(self) -> str:
        text = _command_text("accept-milestone")
        return text.split("\n2a. ", 1)[1].split("\n2b. ", 1)[0]

    def test_accept_milestone_offers_no_command_that_cannot_run_here(self):
        """`v2.6.0-003`, `LPR-R5-003`, `LPR-R6-001`: step 2a names neither
        `/milestone-implement` nor `/request-plan-amendment` as a way
        forward from `AWAITING_FUNCTIONAL_REVIEW`; it says no 2.6.0 command
        completes the checkpoint there, and keeps the functional routing."""
        step = self.accept_step_2a()
        self.assertNotIn("/request-plan-amendment", step)
        self.assertNotIn("finish it with `/milestone-implement`", step)
        for sentence in re.split(r"(?<=[.:;])\s+", step):
            if "/milestone-implement" in sentence:
                self.assertRegex(sentence, r"cannot", sentence)
        self.assertIn("no 2.6.0 command completes one here", " ".join(step.split()))
        self.assertIn("v2.6.0-003", step)
        self.assertIn("route that\n      finding through `/apply-functional-review` instead", step)

    def test_the_operator_reference_points_at_next_action(self):
        text = (Path(__file__).resolve().parent.parent / "docs" / "ai-workflow"
                / "WORKFLOW_V2_1_OPERATOR_REFERENCE.md").read_text()
        table = text.split("## Which command do I run next?", 1)[1].split("\n---", 1)[0]
        self.assertIn("workflow_protocol.py next-action", table)
        self.assertNotIn("`/milestone-implement` — finish it", table)
        self.assertIn("## Driving the Workflow by protocol", text)
        self.assertIn("docs/ai-workflow/ORCHESTRATION_PROTOCOL.md", text)

    def test_milestone_workflow_says_the_protocol_adds_no_gate(self):
        text = (Path(__file__).resolve().parent.parent / "docs" / "ai-workflow" / "MILESTONE_WORKFLOW.md").read_text()
        summary = text.split("## Hard gates summary", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Claude must stop and wait for a human/external input at exactly six points", summary)
        self.assertIn("reports these same gates and\nadds none", summary)



# ---------------------------------------------------------------------------
# The lifecycle end to end, by protocol only (CP6)
# ---------------------------------------------------------------------------

LIFECYCLE_CHECKPOINTS = [{"id": "C1", "depends_on": []}, {"id": "C2", "depends_on": ["C1"]}]
_PLAN_DOC = "docs/ai-workflow/WORKFLOW_V2_PLAN.md"


class _Lifecycle:
    """One disposable repository driven by the protocol alone: every step
    takes `next-action`'s `action.id` and `arguments`, runs the action's
    command guards (`COMMAND_GUARDS`) and then applies the Workflow writer
    sequence that command performs -- the same functions, never a state
    edit by hand. `reconcile` is called only after an automatic action; a
    gate's action is applied as the user's writer sequence, and a verdict
    enters through `record-external-result`, each followed by
    `next-action`. `verdicts[action id]` scripts what each review returns,
    in order."""

    def __init__(self, test: unittest.TestCase, repo: h.ScratchRepo, verdicts: dict[str, list[str]]):
        self.test = test
        self.repo = repo
        self.verdicts = {key: list(values) for key, values in verdicts.items()}
        self.trace: list[tuple] = []
        self.rounds = 0
        self.edits = 0
        self.writers = {
            "plan.start": self.plan_start,
            "plan.review.local": self.plan_review_local,
            "plan.apply_review": self.plan_apply_review,
            "implementation.checkpoint": self.implementation_checkpoint,
            "implementation.self_review": self.implementation_self_review,
            "implementation.review.local": self.implementation_review_local,
            "implementation.apply_review": self.implementation_apply_review,
            "functional.prepare": self.functional_prepare,
        }
        self.gates = {
            "plan.approve": self.user_approves_plan,
            "implementation.approve": self.user_approves_implementation,
            "functional.review": self.user_accepts_milestone,
        }

    # -- the protocol calls ------------------------------------------------

    def decide(self) -> dict:
        state = h.read_state(self.repo)
        if state.get("active_work_item_id") is None and WI in state.get("work_items", {}):
            return next_action(self.repo, "--work-item", WI)
        return next_action(self.repo)

    def run(self, decision: dict) -> dict:
        """Execute one decision and return the next one. An automatic
        decision is executed and reconciled; a gate's is resolved."""
        action = decision["action"]
        if decision["disposition"] == "automatic":
            if decision.get("basis") is not None:
                self.test.assertEqual(
                    next_action(self.repo, "--work-item", WI, "--expect-state-identity",
                                decision["basis"]["state_identity"])["row"], decision["row"],
                    "the identity check immediately before the launch")
                COMMAND_GUARDS.get(action["id"], (lambda repo, state: None,))[0](self.repo, h.read_state(self.repo))
            self.writers[action["id"]](action["arguments"])
            result = reconciled(self.test, self.repo, decision)
            self.trace.append((decision["row"], action["id"], result["class"]))
            self.test.assertEqual(result["invalid_reasons"], [])
            self.test.assertEqual(result["next"], self.decide(), "reconcile's next is next-action's decision")
            return result["next"]
        if decision["disposition"] == "external_gate":
            self.trace.append((decision["row"], action["id"], decision["satisfied_by"]))
            self.record_external(decision["satisfied_by"])
        else:
            self.test.assertEqual(decision["disposition"], "human_gate", decision)
            self.trace.append((decision["row"], action["id"], "user"))
            self.gates[action["id"]](decision)
        return self.decide()

    def drive(self, decision: dict | None = None, *, until: str = "complete") -> dict:
        decision = decision or self.decide()
        for _ in range(60):
            if decision["disposition"] == until:
                return decision
            self.test.assertNotEqual(decision["disposition"], "blocked", decision)
            decision = self.run(decision)
        raise AssertionError(f"no {until} after 60 steps: {self.trace}")

    def record_external(self, kind: str) -> None:
        stage = wp.EXTERNAL_RESULT_KIND_STAGES[kind]
        status = self.verdicts[f"{stage}.manual"].pop(0)
        state = h.read_state(self.repo)
        work_item = state["work_items"][WI]
        if work_item["governing_workflow_version"] in ("2.1", "2.2") and (
                stage == "plan" or work_item["governing_workflow_version"] == "2.2"):
            text = verdict(status, rcid=self.current_content(stage), bundle=self.bundle_id(stage),
                           base=work_item["base_commit"], role=f"MANUAL_EXTERNAL_{stage.upper()}_REVIEW")
        else:
            text = verdict(status, bundle=self.bundle_id(stage), base=work_item["base_commit"])
        result = recorded(self.test, self.repo, kind, text)
        self.test.assertEqual((result["stage"], result["verdict"]), (stage, status))

    # -- what the commands compute -----------------------------------------

    def bundle_id(self, stage: str) -> str:
        directory = fingerprint.resolve_bundle_dir(self.repo.root, WI, **({"stage": "plan"} if stage == "plan" else {}))
        return fingerprint.compute_bundle_id(self.repo.root / directory)[0]

    def current_content(self, stage: str) -> str:
        if stage == "plan":
            return fingerprint.compute_review_content_id_plan_stage_for_work_item(self.repo.root, WI)[0]
        return current_I(self.repo)

    def tick(self) -> str:
        self.rounds += 1
        return f"t-{self.rounds}"

    # -- the automatic actions' writer sequences --------------------------

    def plan_start(self, arguments: dict) -> None:
        """`/milestone-plan`'s `[2.1]` creation: `route_work_item` at the
        config's default (committed), then the publication and the bound
        generation."""
        self.test.assertEqual(arguments, {})
        state = ws.route_work_item(
            h.read_state(self.repo), ws.load_config(self.repo.root), work_item_id=WI, work_item_type="process",
            work_item_kind="process", plan_path=_PLAN_DOC, registry_path=f"docs/ai-workflow/registry/{WI}-registry.json",
            mapping_path=f"docs/ai-workflow/requirements/{WI}-mapping.json", plan_revision=1, now=self.tick(),
            base_commit=self.repo.base, repo_root=self.repo.root)
        h.write_state(self.repo, state)
        h.commit_state(self.repo, "route the work item")
        h.publish_and_bind_plan_bundle(self.repo)

    def plan_review_local(self, arguments: dict) -> None:
        """`/review-plan`: the verdict file, then `record_local_plan_review`."""
        status = self.verdicts["plan.local"].pop(0)
        P, B = self.current_content("plan"), self.bundle_id("plan")
        write_feedback(self.repo, verdict(status, rcid=P, bundle=B, base=self.repo.base, role="LOCAL_MODEL_PLAN_REVIEW"))
        mutate(self.repo, ws.record_local_plan_review, verdict=status, bundle_id=B, review_content_id=P,
               round=self.rounds + 1, now=self.tick())

    def plan_apply_review(self, arguments: dict) -> None:
        """`/apply-plan-review`: the applied edit (committed), then the
        publication and the regeneration -- a `2.x` item's bound bundle
        (`AWAITING_LOCAL_PLAN_REVIEW`), a `"1"` item's next revision at its
        phase."""
        self.edits += 1
        plan = self.repo.root / _PLAN_DOC
        plan.write_text(plan.read_text() + f"applied finding {self.edits}\n")
        work_item = h.read_state(self.repo)["work_items"][WI]
        v1 = work_item["governing_workflow_version"] == "1"
        if v1:  # a "1" round advances the plan's and the registry's revision with the mirror
            revision = work_item["plan_revision"]
            plan.write_text(plan.read_text().replace(f"(Revision {revision})", f"(Revision {revision + 1})", 1))
            registry_path = self.repo.root / f"docs/ai-workflow/registry/{WI}-registry.json"
            registry = json.loads(registry_path.read_text())
            registry["plan_revision"] = revision + 1
            registry_path.write_text(json.dumps(registry) + "\n")
        h.git(self.repo, "add", "-A", "--", "docs/ai-workflow")
        h.git(self.repo, "reset", "-q", "--", str(ws.DEFAULT_STATE_PATH))
        h.git(self.repo, "commit", "-q", "-m", f"apply plan review round {self.edits}")
        if v1:
            mutate(self.repo, ws.publish_plan_revision, work_item["plan_revision"] + 1, self.tick())
            h.generate_plan_bundle(self.repo)
        else:
            h.publish_and_bind_plan_bundle(self.repo)

    def implementation_checkpoint(self, arguments: dict) -> None:
        """`/milestone-implement`'s `[2.1]` step 1: the checkpoint started,
        implemented, completed, and committed with its trailers."""
        checkpoint_id = arguments["checkpoint_id"]
        registry = json.loads((self.repo.root / f"docs/ai-workflow/registry/{WI}-registry.json").read_text())
        mutate(self.repo, ws.transition_checkpoint_in_progress, checkpoint_id, start_commit=self.repo.head(),
               now=self.tick())
        (self.repo.root / h.BUNDLE_ITEM_IMPLEMENTATION_PATH).write_text(f"{checkpoint_id}\n")
        mutate(self.repo, ws.complete_checkpoint, checkpoint_id, registry, now=self.tick(), repo_root=self.repo.root)
        h.git(self.repo, "add", "-A")
        h.git(self.repo, "commit", "-q", "-m",
              f"{checkpoint_id}\n\nWorkflow-Checkpoint: {checkpoint_id}\nWorkflow-Work-Item: {WI}")

    def implementation_self_review(self, arguments: dict) -> None:
        """`/milestone-implement` steps 2 to 4: the (no-op) self-review
        entry, then the bundle generation."""
        registry = json.loads((self.repo.root / f"docs/ai-workflow/registry/{WI}-registry.json").read_text())
        mutate(self.repo, ws.enter_self_reviewing_implementation, registry, now=self.tick())
        h.generate_implementation_bundle(self.repo)

    def implementation_review_local(self, arguments: dict) -> None:
        """`/review-implementation` at `"2.2"`: the verdict file, then
        `record_local_implementation_review`."""
        status = self.verdicts["implementation.local"].pop(0)
        I, B = self.current_content("implementation"), self.bundle_id("implementation")
        write_feedback(self.repo, verdict(status, rcid=I, bundle=B, base=self.repo.base,
                                          role="LOCAL_MODEL_IMPLEMENTATION_REVIEW"))
        mutate(self.repo, ws.record_local_implementation_review, verdict=status, bundle_id=B,
               review_content_id=I, round=self.rounds + 1, now=self.tick())

    def implementation_apply_review(self, arguments: dict) -> None:
        """`/apply-implementation-review`: at the external phase of a
        `"1"`/`"2.1"` item, `enter_applying_review_feedback`; then the fix,
        committed with the recorded verdict's state (the round's committed
        source phase), and the `post-fix` generation."""
        if h.read_state(self.repo)["work_items"][WI]["phase"] == "AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW":
            mutate(self.repo, ws.enter_applying_review_feedback, now=self.tick())
            h.commit_state(self.repo, "enter APPLYING_REVIEW_FEEDBACK")
        self.edits += 1
        (self.repo.root / h.BUNDLE_ITEM_IMPLEMENTATION_PATH).write_text(f"fix {self.edits}\n")
        h.git(self.repo, "add", "--", h.BUNDLE_ITEM_IMPLEMENTATION_PATH, str(ws.DEFAULT_STATE_PATH))
        h.git(self.repo, "commit", "-q", "-m", f"apply implementation review round {self.edits}")
        h.generate_implementation_bundle(self.repo, stage="post-fix")

    def functional_prepare(self, arguments: dict) -> None:
        """`/prepare-functional-review`: the checklist-evidence commit for
        the item's round."""
        commit_checklist_evidence(self.repo, h.read_state(self.repo)["work_items"][WI]["implementation_revision"])

    # -- the user's writer sequences at the gates -------------------------

    def _feedback_fields(self) -> dict:
        return fingerprint.parse_review_feedback_binding_fields(ws.read_review_feedback(self.repo.root, WI))

    def user_approves_plan(self, decision: dict) -> None:
        """`/approve-review plan`: the gate wrapper, the basis, the record
        over the committed plan-stage projection, `apply_plan_approval`,
        and the approval commit."""
        state = h.read_state(self.repo)
        self.test.assertTrue(ws.plan_approval_gate_status(self.repo.root, state, WI)["reachable"])
        confirmation = f"I approve {WI} at the plan stage"
        B = self.bundle_id("plan")
        basis = ws.resolve_approval_basis(
            latest_round_status=self._feedback_fields()["status"],
            feedback_bundle_id=self._feedback_fields()["reviewed_bundle_id"], current_bundle_id=B,
            user_confirmation=confirmation, work_item_id=WI, stage="plan")
        digest, projection = fingerprint.compute_review_content_id_plan_stage_at_commit_for_work_item(
            self.repo.root, WI, "HEAD", base=self.repo.base)
        record = ws.build_approval_record(
            basis=basis, stage="plan", user_confirmation=confirmation, now=self.tick(), reviewed_bundle_id=B,
            approved_review_content_id=digest, review_content_manifest=projection["review_content_manifest"])
        mutate(self.repo, ws.apply_plan_approval, record, self.tick())
        h.commit_state(self.repo, "approve the plan", {"Workflow-Plan-Approval": digest, "Workflow-Work-Item": WI})
        self.plan_basis = basis

    def user_approves_implementation(self, decision: dict) -> None:
        """`/approve-review implementation`: the gate wrapper's inputs, the
        basis, the record, `apply_technical_approval`, and the approval
        commit."""
        state = h.read_state(self.repo)
        gate = ws.technical_approval_gate_status(self.repo.root, state, WI)
        self.test.assertTrue(gate["reachable"], gate)
        confirmation = f"I approve {WI} at the implementation stage"
        inputs = gate["inputs"]
        basis = ws.resolve_approval_basis(
            latest_round_status=inputs["latest_round_status"],
            feedback_bundle_id=self._feedback_fields()["reviewed_bundle_id"], current_bundle_id=inputs["bundle_id"],
            user_confirmation=confirmation, work_item_id=WI, stage="implementation",
            pinned_block=inputs["pinned_block"])
        work_item = state["work_items"][WI]
        record = ws.build_approval_record(
            basis=basis, stage="implementation", user_confirmation=confirmation, now=self.tick(),
            reviewed_bundle_id=inputs["bundle_id"], approved_review_content_id=inputs["current_review_content_id"],
            review_content_manifest=[], reviewed_content_commit=work_item["reviewed_implementation_head"])
        mutate(self.repo, ws.apply_technical_approval, record, self.tick())
        h.commit_state(self.repo, "approve the implementation", {
            "Workflow-Technical-Approval": inputs["current_review_content_id"], "Workflow-Work-Item": WI})

    def user_accepts_milestone(self, decision: dict) -> None:
        """At the functional gate the user tests and accepts: the offered
        `milestone.accept` alternative, applied as `/accept-milestone`'s
        writer sequence (`complete_work_item`) and its completion commit."""
        self.test.assertIn("milestone.accept", [a["id"] for a in decision["alternatives"]])
        state = h.read_state(self.repo)
        is_terminal, _outstanding = ws.resolve_own_registry_completion_status(self.repo.root, state["work_items"][WI])
        self.test.assertTrue(ws.milestone_complete_gate_reachable(phase="AWAITING_FUNCTIONAL_REVIEW",
                                                                  is_terminal=is_terminal))
        h.write_state(self.repo, ws.complete_work_item(state, WI, self.tick(), repo_root=self.repo.root))
        h.commit_state(self.repo, "accept the milestone", {"Workflow-Work-Item": WI})


def _seed_unrouted(repo: h.ScratchRepo, default: str) -> None:
    """The repository `/milestone-plan` starts from, committed as the base:
    the declared plan-stage files and the installed scripts, a config whose
    default is `default`, and no work item yet. The checkpoints' file is
    classified at the plan stage too (excluded), as a real declaration
    classifies every path the work writes."""
    h.seed_bundle_item(repo, registry_checkpoints=LIFECYCLE_CHECKPOINTS)
    h.git(repo, "reset", "-q", "--hard", repo.base)  # drop the seeded entry: ids are never reused
    artifacts = repo.root / "docs" / "ai-workflow" / "registry" / f"{WI}-artifacts.json"
    declarations = json.loads(artifacts.read_text())
    declarations["plan_stage"]["excluded_paths"][h.BUNDLE_ITEM_IMPLEMENTATION_PATH] = "the checkpoints' output"
    artifacts.write_text(json.dumps(declarations) + "\n")
    write_config(repo, default)
    h.write_state(repo, h.base_state())
    h.git(repo, "add", "-A")
    h.git(repo, "commit", "-q", "-m", "no work item yet")
    repo.base = repo.head()


class TestLifecycleEndToEnd2_2(unittest.TestCase):
    """A `"2.2"` item from no work item to `MILESTONE_COMPLETE`, driven by
    `next-action`'s decisions only: a `REVISE` round at both stages of both
    reviews (each manual verdict recorded through `record-external-result`)
    and two checkpoints, the first of them same-phase progress."""

    VERDICTS = {
        "plan.local": ["REVISE", "APPROVE", "APPROVE"],
        "plan.manual": ["REVISE", "APPROVE"],
        "implementation.local": ["REVISE", "APPROVE", "APPROVE"],
        "implementation.manual": ["REVISE", "APPROVE"],
    }

    EXPECTED = [
        ("1", "plan.start", "progress"),
        ("12", "plan.review.local", "progress"),
        ("8", "plan.apply_review", "progress"),
        ("12", "plan.review.local", "gate_reached"),
        ("14", "plan.review.external", "plan_review_verdict"),
        ("8", "plan.apply_review", "progress"),
        ("12", "plan.review.local", "gate_reached"),
        ("14", "plan.review.external", "plan_review_verdict"),
        ("15", "plan.approve", "user"),
        ("23", "implementation.checkpoint", "progress"),
        ("23", "implementation.checkpoint", "progress"),
        ("24", "implementation.self_review", "progress"),
        ("26", "implementation.review.local", "progress"),
        ("36", "implementation.apply_review", "progress"),
        ("26", "implementation.review.local", "gate_reached"),
        ("28", "implementation.review.external", "implementation_review_verdict"),
        ("36", "implementation.apply_review", "progress"),
        ("26", "implementation.review.local", "gate_reached"),
        ("28", "implementation.review.external", "implementation_review_verdict"),
        ("29", "implementation.approve", "user"),
        ("37", "functional.prepare", "gate_reached"),
        ("39", "functional.review", "user"),
    ]

    def test_from_no_work_item_to_milestone_complete(self):
        with h.ScratchRepo() as repo:
            _seed_unrouted(repo, "2.2")
            run = _Lifecycle(self, repo, self.VERDICTS)
            final = run.drive()
            self.assertEqual(run.trace, self.EXPECTED)
            self.assertEqual((final["row"], final["disposition"], final["action"]), ("40", "complete", None))
            state = h.read_state(repo)
            self.assertEqual((state["work_items"][WI]["phase"], state["active_work_item_id"]),
                             ("MILESTONE_COMPLETE", None))
            self.assertEqual(run.plan_basis, "EXTERNAL_APPROVE")
            self.assertTrue(all(value == [] for value in run.verdicts.values()), run.verdicts)

    def test_the_first_checkpoint_is_same_phase_progress(self):
        with h.ScratchRepo() as repo:
            _seed_unrouted(repo, "2.2")
            run = _Lifecycle(self, repo, self.VERDICTS)
            decision = run.drive(until="human_gate")  # the plan approval gate
            decision = run.run(decision)
            self.assertEqual((decision["row"], decision["action"]["arguments"]),
                             ("23", {"work_item_id": WI, "checkpoint_id": "C1"}))
            run.implementation_checkpoint(decision["action"]["arguments"])
            result = reconciled(self, repo, decision)
            self.assertEqual((result["class"], result["from"]["phase"], result["to"]["phase"],
                              result["evidence"]["completed_checkpoints"]),
                             ("progress", "IMPLEMENTING", "IMPLEMENTING", ["C1"]))
            self.assertEqual(result["next"]["action"]["arguments"]["checkpoint_id"], "C2")

    def test_a_gates_own_decision_is_refused_by_reconcile(self):
        with h.ScratchRepo() as repo:
            _seed_unrouted(repo, "2.2")
            run = _Lifecycle(self, repo, self.VERDICTS)
            gate = run.drive(until="human_gate")
            self.assertEqual(gate["action"]["id"], "plan.approve")
            body, code = reconcile(repo, gate)
            self.assertEqual((code, body["error"]["code"]), (wp.EXIT_INVALID_REQUEST, "invalid_request"))


class TestLifecycleEndToEndV1(unittest.TestCase):
    """The two `"1"` runs (`LPR-R3-001`), each from a pre-constructed
    `"1"` state entry in the phase the named 2.6.0 writer persists, using
    only what the `"1"` commands write."""

    def test_the_plan_round(self):
        """From `AWAITING_EXTERNAL_PLAN_REVIEW` as `publish_plan_revision`'s
        `"1"` branch writes it, to row 6a at `IMPLEMENTING`."""
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, governing_workflow_version="1", phase="AWAITING_EXTERNAL_PLAN_REVIEW")
            h.generate_plan_bundle(repo)
            run = _Lifecycle(self, repo, {"plan.manual": ["REVISE"]})
            decision = run.decide()
            self.assertEqual((decision["row"], decision["disposition"]), ("21", "external_gate"))
            decision = run.run(decision)
            self.assertEqual((decision["row"], decision["action"]["id"]), ("18", "plan.apply_review"))
            decision = run.run(decision)
            self.assertEqual(run.trace[-1], ("18", "plan.apply_review", "gate_reached"))
            self.assertEqual((decision["row"], decision["action"]["id"]), ("20", "plan.approve"))
            decision = run.run(decision)
            self.assertEqual(run.plan_basis, "USER_OVERRIDE")
            self.assertEqual((decision["row"], decision["disposition"], decision["reason"]["code"],
                              decision["snapshot"]["phase"]),
                             ("6a", "blocked", "v1_state_not_advanced", "IMPLEMENTING"))
            self.assertIsNone(decision["action"])

    def test_the_implementation_round(self):
        """From `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` as
        `record_bundle_generation` writes it, with `registry_path: null`, to
        `complete`."""
        with h.ScratchRepo() as repo:
            h.seed_bundle_item(repo, governing_workflow_version="1", phase="SELF_REVIEWING_IMPLEMENTATION",
                               registry_path=None)
            repo.commit("implement", filename=h.BUNDLE_ITEM_IMPLEMENTATION_PATH)
            h.generate_implementation_bundle(repo)
            run = _Lifecycle(self, repo, {"implementation.manual": ["REVISE", "APPROVE"]})
            decision = run.decide()
            self.assertEqual((decision["row"], decision["disposition"]), ("35", "external_gate"))
            final = run.drive(decision)
            self.assertEqual(run.trace, [
                ("35", "implementation.review.external", "implementation_review_verdict"),
                ("32", "implementation.apply_review", "gate_reached"),
                ("35", "implementation.review.external", "implementation_review_verdict"),
                ("33", "implementation.approve", "user"),
                ("37", "functional.prepare", "gate_reached"),
                ("39", "functional.review", "user"),
            ])
            self.assertEqual((final["row"], final["disposition"]), ("40", "complete"))


if __name__ == "__main__":
    unittest.main()
