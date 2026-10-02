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
        self.assertEqual(set(wp.OPERATIONS), {"describe", "verify", "resolve-artifact"})
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


if __name__ == "__main__":
    unittest.main()
