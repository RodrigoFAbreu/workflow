#!/usr/bin/env python3
# state_writer: false
"""Orchestration Protocol v1: the Workflow's versioned public contract for
an orchestrator (`docs/ai-workflow/ORCHESTRATION_PROTOCOL_V1_PLAN.md`,
D-OP-Surface).

    python3 scripts/workflow_protocol.py [--repo-root PATH] [--protocol-major N] <operation> [operation args]

An orchestrator runs this script as a subprocess and never imports it. It
imports `workflow_state` and `workflow_fingerprint` from its own directory
and never shells out to them. stdout is exactly one JSON document, the
envelope; diagnostics go to stderr. Exit codes: 0 `ok: true`; 3 a refusal
with a stable code; 2 `invalid_request`; 1 `internal_error`.

Operations: `describe`, `verify`, `resolve-artifact`. Every read path here
is read-only: the state is read under a shared lock on
`WORKFLOW_STATE.lock`, never the write lock, and nothing is written.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import workflow_fingerprint  # noqa: E402
import workflow_state  # noqa: E402

#: The Workflow release these bytes are. A build refuses when it differs
#: from the manifest's `workflow_version` (CP7); it never reads the
#: installation record.
WORKFLOW_RELEASE = "2.7.0"

PROTOCOL_NAME = "workflow-orchestration"
PROTOCOL_MAJOR = 1
PROTOCOL_VERSION = "1.0"
SUPPORTED_PROTOCOL_MAJORS = (PROTOCOL_MAJOR,)

#: The single source of the governing versions the protocol supports
#: (D-OP-Describe): never a repository's `WORKFLOW_CONFIG.json`.
SUPPORTED_GOVERNING_VERSIONS = ("1", "2.1", "2.2")

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_INVALID_REQUEST = 2
EXIT_REFUSED = 3

#: D-OP-Errors: every v1 error code and whether it is retryable.
ERROR_CODES = {
    "unsupported_protocol": False,
    "invalid_request": False,
    "unknown_work_item": False,
    "no_work_item": False,
    "state_unreadable": False,
    "state_invalid": False,
    "stale_decision": True,
    "not_applicable": False,
    "unsupported_result_kind": False,
    "refused": False,
    "internal_error": False,
}

#: The explicit Workflow-exception-to-code table, keyed by class name. A
#: Workflow exception with no entry here is `refused`, never
#: `internal_error` (D-OP-Errors).
WORKFLOW_EXCEPTION_CODES = {
    "InvalidWorkItemIdError": "invalid_request",
    "FeedbackLayoutUndecidableError": "state_unreadable",
    "UnknownFeedbackLayoutError": "state_invalid",
}

#: D-OP-Next's dispositions. `validation` is W2 vocabulary that 2.7.0
#: never emits (`OD-W1-7`).
DISPOSITIONS = ("automatic", "validation", "human_gate", "external_gate", "blocked", "complete")

#: D-OP-External's result kinds: accepted, and reserved for W2.
EXTERNAL_RESULT_KINDS: tuple[str, ...] = ()
RESERVED_RESULT_KINDS = ("functional_evidence", "pr_review_result")

#: The action catalogue's ids (D-OP-Next).
ACTION_IDS: tuple[str, ...] = ()

REVIEW_FEEDBACK_FILE = "REVIEW_FEEDBACK.md"
FUNCTIONAL_REVIEW_FILE = "FUNCTIONAL_REVIEW.md"

#: The phases whose review bundle is the plan stage's (`resolve-artifact`'s
#: `review_bundle`): the two-stage plan-review partition plus the `"1"`
#: plan phases.
PLAN_STAGE_PHASES = (
    workflow_state.PLAN_REVIEW_READY_PHASES
    | workflow_state.PLAN_REVIEW_NON_READY_PHASES
    | {"SELF_REVIEWING_PLAN", "AWAITING_EXTERNAL_PLAN_REVIEW"}
)


class ProtocolError(Exception):
    """A refusal with a stable code. `native` is the Workflow exception
    behind it, or `None`."""

    def __init__(self, code: str, message: str, native: BaseException | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.native = native


class _ArgumentError(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    """argparse with its errors raised (as `invalid_request`) instead of
    printed, and no `--help`: stdout carries the envelope only."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("add_help", False)
        super().__init__(*args, **kwargs)

    def error(self, message):
        raise _ArgumentError(message)


# ---------------------------------------------------------------------------
# The Workflow exception domain (D-OP-Errors)
# ---------------------------------------------------------------------------


def is_workflow_exception(exc: BaseException) -> bool:
    """A Workflow exception is an instance of a class `C` with
    `issubclass(C, Exception)` whose `__module__` is the `__name__` of the
    `workflow_state` or `workflow_fingerprint` module object this module
    imported -- read from the module objects, never from literals."""
    if not isinstance(exc, Exception):
        return False
    return type(exc).__module__ in {workflow_state.__name__, workflow_fingerprint.__name__}


def code_for_workflow_exception(exc: BaseException) -> str:
    return WORKFLOW_EXCEPTION_CODES.get(type(exc).__name__, "refused")


def native_of(exc: BaseException | None) -> dict | None:
    if exc is None:
        return None
    return {"exception": type(exc).__name__, "message": str(exc)}


# ---------------------------------------------------------------------------
# Reading the state (the one read that maps `OSError` to `state_unreadable`)
# ---------------------------------------------------------------------------


def read_state_and_config(repo_root: Path) -> tuple[dict, dict | None]:
    """Read `WORKFLOW_STATE.json` and the raw `WORKFLOW_CONFIG.json` (or
    `None` when absent) under a shared lock on `WORKFLOW_STATE.lock`, so a
    read never interleaves with a `state_transaction` publication. The lock
    file is opened read-only and never created: when it is absent, no
    writer has ever run and the read proceeds without it.

    Every refusal is `state_unreadable`: a missing or corrupt state file, a
    state that is not a JSON object, a corrupt config, or a lock file that
    cannot be opened. This is the single protocol read where an `OSError`
    is `state_unreadable` rather than `internal_error`."""
    lock_path = workflow_state.state_lock_path(repo_root)
    state_path = repo_root / workflow_state.DEFAULT_STATE_PATH
    config_path = repo_root / workflow_state.DEFAULT_CONFIG_PATH
    fd = None
    try:
        try:
            fd = os.open(lock_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except FileNotFoundError:
            fd = None
        if fd is not None:
            fcntl.flock(fd, fcntl.LOCK_SH)
        state = workflow_state._load_json(state_path)
        config = workflow_state._load_json(config_path)
    except OSError as exc:
        raise ProtocolError("state_unreadable", f"cannot read the Workflow state: {exc}") from exc
    except workflow_state.CorruptJsonError as exc:
        raise ProtocolError("state_unreadable", str(exc), exc) from exc
    finally:
        if fd is not None:
            os.close(fd)
    if state is None:
        raise ProtocolError(
            "state_unreadable", f"{workflow_state.DEFAULT_STATE_PATH.as_posix()} does not exist")
    if not isinstance(state, dict):
        raise ProtocolError(
            "state_unreadable", f"{workflow_state.DEFAULT_STATE_PATH.as_posix()} is not a JSON object")
    if config is not None and not isinstance(config, dict):
        raise ProtocolError(
            "state_unreadable", f"{workflow_state.DEFAULT_CONFIG_PATH.as_posix()} is not a JSON object")
    return state, config


def load_valid_state(repo_root: Path) -> dict:
    """The state, read and schema-validated: `validate_state(state)` without
    the whole-state registry-mirror check, which `verify` runs and which a
    plan being edited may legitimately fail mid-round. A refusal is
    `state_invalid`."""
    state, _config = read_state_and_config(repo_root)
    try:
        workflow_state.validate_state(state)
    except Exception as exc:
        if not is_workflow_exception(exc):
            raise
        raise ProtocolError("state_invalid", str(exc), exc) from exc
    return state


def work_item_of(state: dict, work_item_id: str) -> dict:
    work_items = state.get("work_items") or {}
    if work_item_id not in work_items:
        raise ProtocolError("unknown_work_item", f"no work item {work_item_id!r} in work_items")
    return work_items[work_item_id]


# ---------------------------------------------------------------------------
# State identity and the decision basis (D-OP-Identity)
# ---------------------------------------------------------------------------


def state_identity(work_item_id: str, state: dict) -> str:
    """sha256 of the canonical JSON of one work item, its id and the state's
    `schema_version`. Unrelated items and `active_work_item_id` are not part
    of it (`OD-W1-6`)."""
    return hashlib.sha256(workflow_state._canonical_json_bytes({
        "schema_version": state.get("schema_version"),
        "work_item_id": work_item_id,
        "work_item": state["work_items"][work_item_id],
    })).hexdigest()


def head_commit(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD^{commit}"],
        cwd=repo_root, capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def basis(repo_root: Path, state: dict, work_item_id: str) -> dict:
    """The decision basis of a response about a work item. Staleness is
    decided by `state_identity` alone; `head` and `checkpoints` are
    informational."""
    work_item = state["work_items"][work_item_id]
    return {
        "work_item_id": work_item_id,
        "state_revision": work_item.get("state_revision"),
        "state_identity": state_identity(work_item_id, state),
        "phase": work_item.get("phase"),
        "head": head_commit(repo_root),
        "checkpoints": {
            checkpoint_id: entry.get("status")
            for checkpoint_id, entry in sorted((work_item.get("checkpoints") or {}).items())
        },
    }


# ---------------------------------------------------------------------------
# describe (D-OP-Describe)
# ---------------------------------------------------------------------------


def op_describe(repo_root: Path, args: argparse.Namespace) -> dict:
    return {
        "workflow_release": WORKFLOW_RELEASE,
        "protocol_version": PROTOCOL_VERSION,
        "supported_protocol_majors": sorted(SUPPORTED_PROTOCOL_MAJORS),
        "supported_governing_versions": sorted(SUPPORTED_GOVERNING_VERSIONS),
        "capabilities": {
            "operations": sorted(OPERATIONS),
            "dispositions": sorted(DISPOSITIONS),
            "action_ids": sorted(ACTION_IDS),
            "artifact_kinds": sorted(ARTIFACT_KINDS),
            "external_result_kinds": sorted(EXTERNAL_RESULT_KINDS),
            "reserved_result_kinds": sorted(RESERVED_RESULT_KINDS),
            "error_codes": sorted(ERROR_CODES),
        },
    }


# ---------------------------------------------------------------------------
# verify (D-OP-Verify)
# ---------------------------------------------------------------------------


VERIFY_CHECK_IDS = (
    "state_readable",
    "state_valid",
    "config_valid",
    "active_item_resolvable",
    "checkpoint_completions_provable",
    "installation_release_matches",
    "protocol_ready",
)


def _check(check_id: str, status: str, detail: str) -> dict:
    return {"id": check_id, "status": status, "detail": detail}


def _refusal_detail(exc: BaseException) -> str:
    if isinstance(exc, subprocess.CalledProcessError):
        stderr = (exc.stderr or "").strip()
        return f"git {' '.join(map(str, exc.cmd))} failed: {stderr or exc.returncode}"
    return f"{type(exc).__name__}: {exc}"


def _is_check_refusal(exc: BaseException) -> bool:
    """A check fails on a Workflow refusal, or on Git refusing a commit or
    object the state names (a repository fault, not a defect). Anything
    else propagates as `internal_error`."""
    return is_workflow_exception(exc) or isinstance(exc, subprocess.CalledProcessError)


def op_verify(repo_root: Path, args: argparse.Namespace) -> dict:
    checks: list[dict] = []
    state = None
    config = None
    try:
        state, config = read_state_and_config(repo_root)
        checks.append(_check("state_readable", "pass", "the state and the config parse"))
    except ProtocolError as exc:
        checks.append(_check("state_readable", "fail", exc.message))

    if state is None:
        checks.append(_check("state_valid", "skip", "the state is unreadable"))
    else:
        try:
            workflow_state.validate_state(state, repo_root=repo_root)
            checks.append(_check("state_valid", "pass", "validate_state accepts the state"))
        except Exception as exc:
            if not _is_check_refusal(exc):
                raise
            checks.append(_check("state_valid", "fail", _refusal_detail(exc)))

    if state is None:
        checks.append(_check("config_valid", "skip", "the state is unreadable"))
    else:
        try:
            if config is not None:
                workflow_state.validate_config(config)
                checks.append(_check("config_valid", "pass", "validate_config accepts the config"))
            else:
                workflow_state.load_config(repo_root)
                checks.append(_check(
                    "config_valid", "pass", "no config file; the pre-activation default applies"))
        except Exception as exc:
            if not _is_check_refusal(exc):
                raise
            checks.append(_check("config_valid", "fail", _refusal_detail(exc)))

    work_items = state.get("work_items") if state is not None else None
    if state is None:
        checks.append(_check("active_item_resolvable", "skip", "the state is unreadable"))
    else:
        active = state.get("active_work_item_id")
        if active is None:
            checks.append(_check("active_item_resolvable", "pass", "no active work item"))
        elif not isinstance(active, str) or not isinstance(work_items, dict) or active not in work_items:
            checks.append(_check(
                "active_item_resolvable", "fail", f"active_work_item_id {active!r} names no work item"))
        elif not isinstance(work_items[active], dict) or \
                work_items[active].get("phase") in workflow_state.TERMINAL_PHASES:
            checks.append(_check(
                "active_item_resolvable", "fail",
                f"active_work_item_id {active!r} names a terminal or malformed work item"))
        else:
            checks.append(_check("active_item_resolvable", "pass", f"{active} is non-terminal"))

    if state is None:
        checks.append(_check("checkpoint_completions_provable", "skip", "the state is unreadable"))
    elif not isinstance(work_items, dict):
        checks.append(_check("checkpoint_completions_provable", "skip", "work_items is not an object"))
    else:
        failures: list[str] = []
        proven: list[str] = []
        for work_item_id, work_item in sorted(work_items.items()):
            if not isinstance(work_item, dict) or work_item.get("phase") in workflow_state.TERMINAL_PHASES:
                continue
            checkpoints = work_item.get("checkpoints")
            if not isinstance(checkpoints, dict) or not any(
                    isinstance(entry, dict) and entry.get("status") == "COMPLETE"
                    for entry in checkpoints.values()):
                continue
            base_commit = work_item.get("base_commit")
            if not isinstance(base_commit, str):
                failures.append(f"{work_item_id}: COMPLETE checkpoints but no base_commit")
                continue
            try:
                workflow_state.verify_checkpoint_completions(work_item, repo_root, base_commit)
                proven.append(work_item_id)
            except Exception as exc:
                if not _is_check_refusal(exc):
                    raise
                failures.append(f"{work_item_id}: {_refusal_detail(exc)}")
        if failures:
            checks.append(_check("checkpoint_completions_provable", "fail", "; ".join(failures)))
        else:
            checks.append(_check(
                "checkpoint_completions_provable", "pass",
                "every COMPLETE checkpoint has a reachable trailer commit"
                + (f" ({', '.join(proven)})" if proven else " (none recorded)")))

    record_path = repo_root / workflow_state.INSTALLATION_RECORD_PATH
    if not record_path.exists():
        checks.append(_check("installation_release_matches", "skip", "no installation record"))
    else:
        try:
            record = json.loads(record_path.read_text())
            version = record.get("workflow_version") if isinstance(record, dict) else None
        except (OSError, ValueError) as exc:
            checks.append(_check(
                "installation_release_matches", "fail", f"the installation record is unreadable: {exc}"))
        else:
            if version == WORKFLOW_RELEASE:
                checks.append(_check(
                    "installation_release_matches", "pass", f"installed release {version}"))
            else:
                checks.append(_check(
                    "installation_release_matches", "fail",
                    f"the installation record names {version!r}, these scripts are {WORKFLOW_RELEASE}"))

    ready = all(c["status"] == "pass" for c in checks[:4])
    checks.append(_check(
        "protocol_ready", "pass" if ready else "fail",
        "checks 1-4 passed" if ready else "a check among 1-4 did not pass"))
    return {"healthy": all(c["status"] != "fail" for c in checks), "checks": checks}


# ---------------------------------------------------------------------------
# resolve-artifact (D-OP-Artifacts)
# ---------------------------------------------------------------------------


def _feedback_file(name: str):
    def resolve(repo_root: Path, work_item_id: str, work_item: dict) -> Path:
        return workflow_fingerprint.resolve_feedback_dir(repo_root, work_item_id) / name
    return resolve


def _review_bundle(repo_root: Path, work_item_id: str, work_item: dict) -> Path:
    if work_item.get("phase") in PLAN_STAGE_PHASES:
        return workflow_fingerprint.resolve_bundle_dir(repo_root, work_item_id, stage="plan")
    return workflow_fingerprint.resolve_bundle_dir(repo_root, work_item_id)


def _plan_review_inputs(repo_root: Path, work_item_id: str, work_item: dict) -> Path:
    return workflow_fingerprint.resolve_plan_review_inputs_dir(repo_root, work_item_id)


def _plan_document(repo_root: Path, work_item_id: str, work_item: dict) -> Path | None:
    plan_path = work_item.get("plan_path")
    return Path(plan_path) if isinstance(plan_path, str) and plan_path else None


def _functional_checklist(repo_root: Path, work_item_id: str, work_item: dict) -> Path:
    return Path(workflow_state.FUNCTIONAL_CHECKLIST_PATH)


#: The v1 artifact kinds, each resolved by the Workflow's own helper only.
ARTIFACT_KINDS = {
    "review_feedback": _feedback_file(REVIEW_FEEDBACK_FILE),
    "functional_review": _feedback_file(FUNCTIONAL_REVIEW_FILE),
    "review_bundle": _review_bundle,
    "plan_review_inputs": _plan_review_inputs,
    "plan_document": _plan_document,
    "functional_checklist": _functional_checklist,
}


def op_resolve_artifact(repo_root: Path, args: argparse.Namespace) -> dict:
    if args.kind not in ARTIFACT_KINDS:
        raise ProtocolError(
            "invalid_request",
            f"unknown artifact kind {args.kind!r}; expected one of {sorted(ARTIFACT_KINDS)}")
    state = load_valid_state(repo_root)
    work_item = work_item_of(state, args.work_item)
    path = ARTIFACT_KINDS[args.kind](repo_root, args.work_item, work_item)
    return {
        "kind": args.kind,
        "path": path.as_posix() if path is not None else None,
        "exists": path is not None and (repo_root / path).exists(),
        "basis": basis(repo_root, state, args.work_item),
    }


# ---------------------------------------------------------------------------
# The CLI and the envelope (D-OP-Surface)
# ---------------------------------------------------------------------------


OPERATIONS = {
    "describe": op_describe,
    "verify": op_verify,
    "resolve-artifact": op_resolve_artifact,
}


def _global_parser() -> _Parser:
    parser = _Parser(prog="workflow_protocol.py")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--protocol-major", type=int, default=None)
    return parser


def _parser() -> _Parser:
    parser = _global_parser()
    sub = parser.add_subparsers(dest="operation", required=True, parser_class=_Parser)
    sub.add_parser("describe")
    sub.add_parser("verify")
    p = sub.add_parser("resolve-artifact")
    p.add_argument("--work-item", required=True)
    p.add_argument("--kind", required=True)
    return parser


def envelope(operation: str | None, *, result: dict | None = None,
             error: ProtocolError | None = None) -> dict:
    body = {
        "protocol": {"name": PROTOCOL_NAME, "version": PROTOCOL_VERSION},
        "workflow_release": WORKFLOW_RELEASE,
        "operation": operation,
        "ok": error is None,
    }
    if error is None:
        body["result"] = result
    else:
        body["error"] = {
            "code": error.code,
            "message": error.message,
            "retryable": ERROR_CODES[error.code],
            "native": native_of(error.native),
        }
    return body


def exit_code_for(code: str) -> int:
    if code == "invalid_request":
        return EXIT_INVALID_REQUEST
    if code == "internal_error":
        return EXIT_INTERNAL
    return EXIT_REFUSED


def _operation_hint(argv: list[str]) -> str | None:
    for token in argv:
        if token in OPERATIONS:
            return token
    return None


def run(argv: list[str]) -> tuple[dict, int]:
    """Parse `argv`, run the operation and return `(envelope, exit code)`.
    Never raises: every outcome is an envelope."""
    operation = _operation_hint(argv)
    try:
        try:
            known, _rest = _global_parser().parse_known_args(argv)
        except _ArgumentError as exc:
            raise ProtocolError("invalid_request", str(exc)) from exc
        if known.protocol_major is not None and known.protocol_major not in SUPPORTED_PROTOCOL_MAJORS:
            raise ProtocolError(
                "unsupported_protocol",
                f"protocol major {known.protocol_major} is not supported; "
                f"supported: {sorted(SUPPORTED_PROTOCOL_MAJORS)}")
        try:
            args = _parser().parse_args(argv)
        except _ArgumentError as exc:
            raise ProtocolError("invalid_request", str(exc)) from exc
        operation = args.operation
        repo_root = (args.repo_root or Path.cwd()).resolve()
        if not repo_root.is_dir():
            raise ProtocolError("invalid_request", f"--repo-root {repo_root} is not a directory")
        try:
            result = OPERATIONS[operation](repo_root, args)
        except ProtocolError:
            raise
        except Exception as exc:
            if not is_workflow_exception(exc):
                raise
            raise ProtocolError(code_for_workflow_exception(exc), str(exc), exc) from exc
        return envelope(operation, result=result), EXIT_OK
    except ProtocolError as exc:
        return envelope(operation, error=exc), exit_code_for(exc.code)
    except Exception as exc:  # an unexpected exception is a defect
        traceback.print_exc(file=sys.stderr)
        error = ProtocolError("internal_error", f"{type(exc).__name__}: {exc}")
        return envelope(operation, error=error), EXIT_INTERNAL


def main(argv: list[str] | None = None) -> int:
    body, code = run(sys.argv[1:] if argv is None else argv)
    sys.stdout.write(json.dumps(body, sort_keys=True, ensure_ascii=False) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
