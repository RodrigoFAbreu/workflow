# W42: Workflow 2.28.0 — the findings record as one plain command (Revision 2)

- **Work item:** `acceptance-findings-floor` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-05 (passed on from the RepFlow lane):
  RodrigoFAbreu/workflow#148, the rest; `docs/ROADMAP.md` row 37 (`Next`, becomes `Current` with this plan, `Done` at
  acceptance). The earlier halves are rows 35 and 36 (`docs/milestones/completed/ACCEPTANCE_PLAIN_COMMAND_PLAN.md` and
  `ACCEPTANCE_COMPLETION_COMMAND_PLAN.md`).
- **Branch:** `milestone/acceptance-findings-floor`
- **Base commit:** `bf1b456d229fa739eb666937b8c65e5a83f2b865` (main after #160: release source and own installation are 2.27.0;
  automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2 (round 1 of the local review: I1 to I3, O1 to O4 applied, see D-Output, D-Command, D-Tests and section 5). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1: the investigation (before any design)

Everything below was measured on scratch repositories with the base's `payload/scripts` (a probe, not shipped).

### 0a. The two functions

| | `write_finding_dispositions_record(repo_root, state, id)` | `commit_gate_policy_floor(repo_root, *, now)` |
| --- | --- | --- |
| Callers | `/accept-milestone` step 5a; `/satisfy-gate acceptance` step 4 cites it; tests; `docs/RETENTION.md` names it | `/satisfy-gate` step 5 of the policy evaluation and of the acceptance stage, cited only; tests |
| Reads | the state **dict it is given** (`optional_findings` of one item) and `<id>-dispositions.json` | the state file, the policy file, the commit history (`record_gate_policy_floor`) |
| Returns | the repository-relative paths the completion commit stages: the record, plus the dispositions file when it exists; `[]` for an empty ledger | the new commit's sha, or `None` |
| Writes | `docs/milestones/completed/<id>-findings.md` (directories created); nothing else, no lock, no commit | the state's top-level `gate_policy_floor` through one `state_transaction`, then one state-only commit (top-level-scoped staging) with `Workflow-Gate-Policy-Floor: <digest>`, then `validate_gate_policy_floor_commit` |
| Re-run | **idempotent**: deterministic text, overwritten byte for byte (a stale record is restored; a deleted dispositions file drops out of the paths) | second call: `None`, `HEAD` unmoved, clean tree (measured) |
| Refusals | `InvalidFindingDispositionsError` before any write (measured: no record created); `KeyError` for an unknown id; `FileExistsError` when `docs/milestones/completed` is a file; nothing written in each | `DirtyIndexBeforeStagingError` before the transaction (measured: state file byte-identical); a validator error **after** the commit landed |
| Phase guard | **none** (measured: an item at `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` with one undisposed finding gets a record whose disposition column says `none`) | none (measured: it commits with an uncommitted edit of a work item in the state file; the scoped staging leaves the edit out) |

### 0b. Order the command text requires

`accept-milestone.md` step 5a runs **after** `complete_work_item` has persisted the completed state and **before** step 6's
completion commit, which stages the returned paths. `satisfy-gate.md` step 4 runs steps 2b and 3 to 8 of `/accept-milestone`, so
step 5a is inside it. The floor is `satisfy-gate.md` step 5, **after** that completion commit (`LPR-R18-001`, `LPR-R23-003`:
evaluate against the virtual floor, perform the satisfying commit, only then record a stricter setting).

### 0c. The floor commit needs its own recovery design: it is split to the next row (sizing)

Four measured facts a thin wrapper cannot answer without a design of its own:

1. **A crash between the state write and the commit is not recoverable by a re-run.** After
   `state_transaction(record_gate_policy_floor)` and before the commit, the working tree shows `M WORKFLOW_STATE.json`;
   the second `commit_gate_policy_floor` returns `None` (the stored floor already equals the virtual one), commits nothing
   and leaves the file dirty. A flag printing `commit: null` would say "nothing stricter" when a floor is waiting.
2. **A validator refusal after the commit landed** leaves a commit that cannot be taken back (no `reset` in this
   Workflow); the text says "the approval stands, the floor stays virtual" and names the cause. The flag would have to report
   a commit that exists *and* an error.
3. **The order is not enforced by the library**: the floor commits fine before the completion commit (measured), so the flag
   must decide whether to refuse (a changed work item in the state file) or leave it to the text.
4. **A directory with no state file** returns `None` silently (measured), not an error a worker can read.

Each is a decision about recovery, not a wrapper. The owner's rule (one mechanism per item; a recovery design splits it) puts
the floor commit in **row 38** (`Next`, written with this plan). This item plans the findings record, which has none of these:
its write is a file, idempotent, and a refusal before the write (the phase guard, an invalid dispositions file, a path that cannot be created) writes nothing (0a); only a failure after the file was rewritten can leave it changed, and the command reports that (`record_changed`, D-Output). Said plainly in the hand-off: after 2.28.0 a worker
still runs **one** short Python call in `/satisfy-gate acceptance` (the floor), and only when a stricter setting was observed.

### 0d. Flag or protocol operation: a flag, by evidence (as rows 35 and 36)

The Controller launches `/satisfy-gate acceptance {id}` with a worker and never runs the record; what the worker runs inside
the command is not in the protocol, and a `workflow_protocol.py` operation would be protocol `1.6` and a Controller change for no
consumer. Precedent: `--finding-dispositions`, `--acceptance-gate`, `--satisfy-acceptance`. **Nothing here forces a protocol `1.6`:
it stays `1.5`, no Controller change.**

## 1. Goal, release, and what stays as it is

A headless worker writes the findings record with **one plain command**, `python3 scripts/workflow_state.py
--write-findings-record <work-item-id>`, with no inline Python, in `/accept-milestone` step 5a and wherever
`/satisfy-gate acceptance` step 4 reaches it. It calls `write_finding_dispositions_record` on the stored state and prints the
paths to stage.

- **Release: Workflow 2.28.0, a `feat:` minor** (a new command surface a worker is told to run). `manifest.json`'s
  `workflow_version` moves 2.27.0 to 2.28.0; the protocol stays `1.5`.
- **Semantics do not change:** same file, same text, same paths, same overwrite on a re-acceptance. **No line of
  `write_finding_dispositions_record`, `render_finding_dispositions` or `finding_dispositions_report` changes.** The one
  addition is a phase guard (D-Preflight).
- **Out of scope:** the floor commit (row 38, 0c); the library's phase gap (`complete_work_item` completes from `IMPLEMENTING` and
  from `MILESTONE_COMPLETE`; wf#158 item 1, a behaviour change, the row after 38); the optional `next-action` evidence line of #148
  (a third mechanism, only if the owner asks); any change to the gate's requirements (a recorded finding without a disposition
  still blocks acceptance exactly as before: this flag is after it and adds no check of dispositions).

## 2. Design decisions

### D-Flag: the interface

`python3 scripts/workflow_state.py --write-findings-record <work-item-id>` (plain, not `python3 -I`: the script imports
`workflow_fingerprint` from its own directory). A fifth member of the mutually exclusive group, dispatched right after
`parse_args`, **before** the shared `git rev-parse`, with `args.write_findings_record is not None` (an empty id is an
`UnknownWorkItem`). No other option. The argparse description is reworded ("read-only except the last two").

### D-Preflight: the item is complete

The text says "on the completed state" and the library does not check it (0a). The command refuses unless the item's phase is
`MILESTONE_COMPLETE`, before anything is read for the record: `FindingsRecordPreflightError` (new class, `code`
`work_item_not_complete`, detail names the phase). This is the one addition; it stops a record that says `none` for every
disposition from being written and then committed. It is read from the same state dict the library receives.

### D-Output: the answer

Success: exit 0 and exactly `{"paths": [<posix path>, ...]}` (`sort_keys=True`, `indent=2`, one trailing newline): the library's
list, in its order, as strings; `[]` for an empty ledger (nothing was written). Failure or any exception: exit 1 and one object
`{"error": <class name>, "message": str(exc), "record_changed": bool, "state_changed": bool}` plus `"code"` when the exception
has a string `code`. `record_changed` is the sha256 of the record file before the call against after (an absent file, a directory or an unreadable path is its own marker, so a directory at the record path reports `false`, not an error of its own);
`state_changed` is the same for the state file, so it is measured, never assumed (it can only be true if another writer ran).
A worker's rule, in the text, covers all four answers: `record_changed: false` and `state_changed: false` mean nothing was written, stop and fix the
cause; `record_changed: true` means the record moved and the write then failed, so the file may be partial: do not stage or commit it, fix the cause and
re-run, because a successful run rewrites the whole file; `state_changed: true` means another writer changed the state: stop and re-read it (the precedent is
`satisfy-gate.md`'s "Any other `state_changed: true` means another writer changed the state"); the command never commits. Errors before the call (`StateMissing`, `CorruptJsonError`, `StateMalformed`, `UnknownWorkItem`, outside Git) are the
read-only flags' own objects, found by the same helper `_acceptance_cli_context`, with both fields false. Exit 2 stays argparse.
Every existing flag's output and exit code stays byte-identical.

### D-Discipline: what it touches

The state is **read once**, unlocked (as `--acceptance-gate` and the text path read it); the command takes **no** lock (so it creates
no `.ai-review/runtime/WORKFLOW_STATE.lock`: a whole-tree comparison needs no exclusion), enters no `state_transaction`, writes no state,
stages nothing, commits nothing, calls no forge. The one file it may write is the record. A concurrent writer between the read and
the write is the text path's window and is not widened. The command needs no `now` and no seam: tests call the CLI function in-process in the repository.

### D-Command: the command text

`accept-milestone.md` step 5a names the flag first and keeps the Python call as the specification: the line
`python3 scripts/workflow_state.py --write-findings-record <work-item-id>` alone on its line, the answer, the error object with the
four-way `record_changed`/`state_changed` rule (both `false`; `record_changed: true`; `state_changed: true`), that the command does not commit, and that it runs on
the stored completed state, so the completed state must already be **written to the state file** by the step that completed it (step 2a says to persist it as
part of the completion commit in step 6, but the flag reads the file: a worker holding the state in memory gets a clean `work_item_not_complete`, no harm done). **Every pinned phrase stays** (`write_finding_dispositions_record`, `5a. **Write the findings record**`,
`skip steps 3, 5 and 7, but run step 5a`), so the golden hash of the file moves (a recorded, intentional change). `satisfy-gate.md`'s
"Plain commands first" block, after the completion command, adds one paragraph naming the flag for step 4's findings record,
and its closing sentence is corrected: the findings record now has a plain command; the floor is the one Python call that remains,
and the sentence keeps the form the existing pins need: `workflow_gate_policy_test.py`'s `test_s7_the_command_text_names_the_flag_after_the_report_and_states_the_boundaries`
forbids the phrase "until its own plain" and pins "steps 4 and 5 below stay the worker's own edits", so the new wording avoids the first and keeps the second
(CP1 promises that test passes unmodified). The floor sentences (step 5) and `state_writer: true` stay.

### D-Tests

All in `payload/scripts/workflow_gate_policy_test.py`, class `TestWriteFindingsRecordCommand` on `AcceptanceRepo` with the
`TestFindingDispositions` helpers (`record`, `write_dispositions`), the CLI function called in-process in the repository; a subprocess
only for the documented line. Each test states exact output and compares the raw stdout with the documented serialisation.

- **R1 parity**: for five states (a disposed finding; two findings with one `dropped` reason; an empty ledger; a remediation child with its
  own finding; a dispositions file removed after a first write), the command's `paths` equal the library's on a **copy**, the record is byte-equal and
  every other file outside `.git` is byte-equal.
- **R2 re-run**: a second run prints the same stdout and leaves the same bytes; a stale record is restored; a deleted dispositions file
  drops out of `paths`; an item with no finding prints `{"paths": []}` and creates no file or directory.
- **R3 no write, one per refusal**: each of the phases `IMPLEMENTING`, `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, `AWAITING_FUNCTIONAL_REVIEW` (code
  `work_item_not_complete`); an invalid dispositions file (`InvalidFindingDispositionsError`); `docs/milestones/completed` a regular file
  (`FileExistsError`); the record path a directory; and every error before the call (unknown and empty id, no state, corrupt state, `[]`, `{}`, a
  run outside Git): exit 1, the whole tree outside `.git` identical (with a pre-existing stale record untouched), refs and index identical,
  `record_changed` and `state_changed` false.
- **R4 discipline**: `ws.state_transaction`, `ws.state_lock`, `resolve_gh` and every `git commit`/`git add` are asserted **not called**; the
  only file that differs after success is the record; no `.ai-review/` entry appears.
- **R5 interface**: two flags together exit 2 (each pair with the new flag); an empty id is `UnknownWorkItem`; the four existing flags print
  output byte-identical to before on the same repository.
- **R6 the command text**: `accept-milestone.md` and `satisfy-gate.md` name the flag, in `accept-milestone.md` before the first
  `write_finding_dispositions_record`, keep every pinned phrase (including those of `test_s7_...` above), state both `true` branches (`record_changed: true`: do not
  stage or commit the file, fix the cause and re-run; `state_changed: true`: another writer ran, stop and re-read the state) and that the completed state must
  already be in the state file, name that only the floor stays Python, have no `python3 -I` on the line;
  the documented line (found by pattern, id substituted) runs as written in a scratch repository and exits as R3 says for an early item.
- **R7 accuracy of the fields**: a failure with a record already present and unchanged reports `record_changed: false`; a failure after the
  record was rewritten (a monkeypatched `write_text` that writes then raises) reports `record_changed: true`; a failure whose seam changes the state file and
  then raises reports `state_changed: true` (with `record_changed: false`), so both fields are shown able to report `true`.
- **R8 the CLI calls the library itself**: a spy on `write_finding_dispositions_record` (or `inspect.getsource` of the CLI function, as
  `test_s8_the_report_and_the_command_call_one_function` does) shows the command calls that function, and `render_finding_dispositions` is not called by the CLI
  function directly.

**Failure-only mutations**, one per behaviour, each failing the named test, recorded on a scratch copy: m1 the phase guard dropped (R3); m2 the guard
accepts any phase in `TERMINAL_PHASES` plus `IMPLEMENTING` (R3); m3 the guard runs after the write (R3); m4 the output gains a key or `paths` become a
sorted or non-string list (R1); m5 a refusal exits 0 (R3); m6 `record_changed` constant (R3, R7); m7 `state_changed` constant (R3, R7); m8 the command
wraps the call in `state_transaction` or takes the lock (R4); m9 it commits or stages the paths (R4); m10 it re-renders the record itself (R8); m11 the
dispatch after the shared `git rev-parse` (R3, the run outside Git: an uncaught `CalledProcessError`); m12 the empty id falls through (R5); m13 the flag outside the exclusive group (R5); m14 an existing
flag's output changed (R5); m15 an exception swallowed into `{"paths": []}` (R3); m16 the text drops the flag or puts it after the Python call (R6).

### D-Docs

`docs/exit-codes.md`: three rows for the new flag (0 `{paths}` printed; 1 the JSON error with `record_changed`; 2 arguments) and "also two of the
five" in the existing row; no milestone id. `docs/ROADMAP.md`: row 37 `Current` with its description narrowed to the findings record, and row 38
`Next` for the floor commit (0c), written with this plan; row 37 becomes `Done` at acceptance.

### D-Release

2.28.0. `manifest.json`: `workflow_version`; the eight changed records (`workflow_state.py`, `workflow_gate_policy_test.py`,
`workflow_integration_test.py`, `workflow_protocol.py`, its test, `satisfy-gate.md`, `accept-milestone.md`, `ORCHESTRATION_PROTOCOL.md`) take their
`sha256` and `size`; no file is added or removed; `conformance.suites` by `release.py manager-block --write`. `WORKFLOW_RELEASE` becomes 2.28.0 with its
pinned assertions; `tools/release/release_test.py` gets a 2.28.0 class and the 2.27.0 class gives up the current-release pins (its suite count pin at
`tools/release/release_test.py:3593` among them). `docs/release-history.md`: the 2.28.0 row; the way back to 2.27.0 only removes the flag.
`ORCHESTRATION_PROTOCOL.md`: the release list and one sentence that 2.28.0 adds a `workflow_state.py` flag that writes the record file and is not a
protocol operation (the protocol stays `1.5`).

**The Manager block's posture** (Manager-facing, unchecked by any tool, `docs/RELEASING.md` "Not checked"; rewritten, with the downgrade guidance carried over
sentence for sentence): Workflow 2.28.0 is a minor release that adds `python3 scripts/workflow_state.py --write-findings-record <work-item-id>`, which writes
the findings record file and nothing else (no state, no commit); it is not a protocol operation and Orchestration Protocol stays 1.5 (the release constant
becomes 2.28.0); `workflow-manager update back to 2.27.0` (minimum Manager 1.13.0) removes the flag and restores `WORKFLOW_RELEASE` 2.27.0, and nothing needs
undoing, because the record the flag writes is the Python call's own file; the 2.27.0 guidance sentence carries over verbatim with only its first words
naming 2.27.0 and earlier, and the closing sentence "The release tooling and the maintainer documents are not part of the installed release." is **kept**
(2.27.0's plan dropped it without intent). Each changed record's `rationale` carries one sentence, `acceptance-findings-floor (workflow-2.28.0)`, on exactly
the eight changed records. The 2.28.0 class pins the needles (`2.28.0`, `2.27.0`, `--write-findings-record`, `Orchestration Protocol stays 1.5`,
`not a protocol operation`, `workflow-manager update back to 2.27.0`, `WORKFLOW_RELEASE`, `removes the flag`, `nothing needs undoing`,
`/release-checkpoint-start`, `2.14.0`, the closing sentence), the `rationale` sentence, `CHANGED` and the new `conformance.suites` counts.

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w42-tmp` (procedure of
`docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): recompute `sha256` and `size` of every record whose file differs (none added), measure
`conformance.suites` (**the `workflow_gate_policy_test.py` count moves**: D-Tests adds tests to that suite), commit in the clone, run the "Verification
commands" of `docs/RELEASING.md`; `tools/release` tests use
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`. **The one expected
failure at CP1**: the 2.27.0 class pins `suites["workflow_gate_policy_test.py"]` to 359 (`tools/release/release_test.py:3593`), so it fails once the measured
count is written; it is named, measured at implementation, and released in CP2 (stock `stage-conformance` is the real proof there). CP1 proves
`tools/release` by that failure and every other test passing. The new tests run again under the Manager's orphan rule (reaper).

## 3. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **The floor commit is row 38**, not here (0c): four measured recovery questions; drop the split if the owner prefers one item.
- **A flag, not a protocol operation** (0d), decided by evidence.
- **The phase guard** (D-Preflight) is the only addition to the record's semantics; without it the flag is easier to misuse than the text is.
- **`record_changed` and `state_changed`** are both reported and measured: the first tells a worker whether the file moved, the second proves the flag never writes state.
- **No disposition check**: a completed item cannot hold an undisposed finding (acceptance refuses it), so the record needs none here.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The findings-record flag, its tests, the command texts and the pages | - | 3 | 1 |
| CP2 | Release 2.28.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The findings-record flag, its tests, the command texts and the pages

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py`,
`payload/scripts/workflow_integration_test.py`, `payload/.claude/commands/satisfy-gate.md`,
`payload/.claude/commands/accept-milestone.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): R1 to R8 written and run red against the unedited tree; mutations m1 to m16 each fail the named test on a scratch copy and
  the results are recorded.
- **The change** (D-Flag, D-Preflight, D-Output, D-Discipline): `FindingsRecordPreflightError`, `_write_findings_record_cli`, the fifth group member and its
  dispatch; nothing else. Every existing test passes unmodified except the golden hash row of `accept-milestone.md` in `workflow_integration_test.py` (an
  intentional content change, with a comment line).
- **The command texts and the pages** (D-Command, D-Docs). `check_docs.py` stays clean.
- **No other mechanism:** `git diff bf1b456 --stat -- payload` lists `workflow_state.py`, `workflow_gate_policy_test.py`, `workflow_integration_test.py`,
  `satisfy-gate.md` and `accept-milestone.md` only, and `git diff bf1b456 -S commit_gate_policy_floor -- payload/scripts/workflow_state.py` is empty;
  `docs/ROADMAP.md` carries row 37 `Current` and row 38 `Next`.

**Verification:** the new tests as the suite runs them; D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`,
`check-manager-block` (with `--manager-releases`), `tools/release` (zlib-ng interpreter, no patch, no skip, with the **one expected failure** of D-Staging); the
new tests again under the Manager's orphan rule (reaper).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.28.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.28.0 with its pinned assertions and the protocol-document edits (protocol stays `1.5`; D-Release).
- `manifest.json` 2.28.0 (D-Release): `workflow_version`, the changed records, `conformance.suites`.
- The Manager block's posture and each changed record's `rationale` sentence (D-Release).
- `docs/release-history.md`: the 2.28.0 row and its "Last checked with" line; that of `docs/exit-codes.md` moves too.
- `tools/release/release_test.py`: a 2.28.0 class pinning the posture, the `rationale` sentence, `CHANGED` and the suite counts; the 2.27.0 class gives up
  the current-release pins.

**Verification:** the new tests again; the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD`
succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; `workflow-manager verify .` is clean; the tools tests pass in the
zlib-ng environment.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Every flow runs offline: no network, no real `gh`, no install, no socket, no zlib-ng, no
Python 3.12 (flows 13 and 14 need the full environment and say so); nothing runs against the real repository, its `.ai-review/` or the forge.** Setup, once, under
`$TMPDIR` (`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w42-tmp`): `base/` from `git archive bf1b456
payload/scripts` and `cand/` from the working tree's `payload/scripts`, and the two paths **absolute** (`cli` changes directory, and `git archive` puts the scripts
under `base/payload/scripts`):
`export BASE="$TMPDIR/base/payload/scripts" CAND="$TMPDIR/cand/payload/scripts"` (with `cand/payload/scripts` copied from the working tree). The fake `gh` (it only proves **no** forge call; the flag never needs one) lives outside
`/tmp`, `/var/tmp`, `/dev/shm` and `$TMPDIR`, mode 0755:

```sh
export W42_BIN="$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w42-bin"
mkdir -p "$W42_BIN" && printf '#!/bin/sh\necho "gh called: $*" >> "$GH_LOG"\nexit 1\n' > "$W42_BIN/gh" && chmod 755 "$W42_BIN/gh"
export GH_LOG="$W42_BIN/gh.log"; : > "$GH_LOG"
mk() { # mk <dir> <case>: a scratch repository built by hand
  d="$1"; rm -rf "$d"; mkdir -p "$d/docs/ai-workflow/registry"; git -C "$d" init -q .
  git -C "$d" config user.email t@t; git -C "$d" config user.name t
  CASE="$2" python3 -I - "$d" <<'PY'
import json, os, sys
d, case = sys.argv[1], os.environ["CASE"]
def one(key, text, stage, role, n): return {key: {"text": text, "raised": [{"stage": stage, "role": role, "round": n}]}}
found = {}
if case != "nofind":
    found.update(one("F-aaa111", "O1: add a test", "plan", "LOCAL_MODEL_PLAN_REVIEW", 1))
    found.update(one("F-bbb222", "O2: reword | x", "implementation", "LOCAL_MODEL_IMPLEMENTATION_REVIEW", 2))
phase = {"early": "IMPLEMENTING", "afr": "AWAITING_FUNCTIONAL_REVIEW"}.get(case, "MILESTONE_COMPLETE")
item = {"work_item_id": "wi", "phase": phase}
if found: item["optional_findings"] = found
json.dump({"schema_version": 1, "work_items": {"wi": item}}, open(d + "/docs/ai-workflow/WORKFLOW_STATE.json", "w"), indent=2)
path = d + "/docs/ai-workflow/registry/wi-dispositions.json"
if case == "done":
    json.dump({"schema_version": 1, "work_item_id": "wi", "dispositions": {"F-aaa111": {"disposition": "fixed"},
              "F-bbb222": {"disposition": "dropped", "reason": "not needed"}}}, open(path, "w"))
if case == "baddisp": open(path, "w").write("{nope")
if case == "blocked": os.makedirs(d + "/docs/milestones"); open(d + "/docs/milestones/completed", "w").write("x")
if case == "dirrec": os.makedirs(d + "/docs/milestones/completed/wi-findings.md")
PY
  git -C "$d" add -A; git -C "$d" commit -q -m scratch
}
snap() { (cd "$1" && { git rev-parse HEAD; git for-each-ref; git diff --cached --name-only; find . -path ./.git -prune -o -print | sort |
  while read -r f; do if [ -f "$f" ]; then sha256sum "$f"; else echo "$f"; fi; done; }); }
py() { # py <scripts-dir> <repo>: the Python call on the stored state; prints the returned paths
  (cd "$2" && python3 -I -c 'import sys, json; sys.path.insert(0, sys.argv[1]); import workflow_state as ws; from pathlib import Path
st = json.load(open("docs/ai-workflow/WORKFLOW_STATE.json")); print(json.dumps([str(p) for p in ws.write_finding_dispositions_record(Path("."), st, "wi")]))' "$1"); }
cli() { (cd "$2" && PATH="$W42_BIN:$PATH" python3 "$1/workflow_state.py" --write-findings-record "${3-wi}"; echo "exit=$?"); }
```

Cases of `mk`: `done` (complete, two findings, both disposed), `nofind` (complete, none), `undisp` (complete, two findings, no dispositions file), `early`
(`IMPLEMENTING`, two findings, no file), `afr` (`AWAITING_FUNCTIONAL_REVIEW`), `baddisp` (`{nope`), `blocked` (a regular file at `docs/milestones/completed`), `dirrec`
(a directory at the record path). The Python baseline is run on a **copy** (`cp -a`) of each repository so the two never share a tree.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `mk r done`, `cp -a r r2`; `snap r > before`; `cli $BASE r` (the base has no flag); then `py $BASE r2`, `cli $CAND r`, `snap r > after` | base: exit 2 and the argparse "one of the arguments" refusal. Python on `r2`: prints the two paths. cand: exit 0, stdout exactly `{"paths": ["docs/milestones/completed/wi-findings.md", "docs/ai-workflow/registry/wi-dispositions.json"]}` (indent 2, sorted keys; the record first, then the dispositions file, the library's order), `cmp r/docs/milestones/completed/wi-findings.md r2/docs/milestones/completed/wi-findings.md` is silent; `diff before after` shows only the new record file and the two new directory lines above it (`docs/milestones` and `docs/milestones/completed`, since `snap` lists directories); same `HEAD`, no staged path, no `.ai-review` directory |
| 2 | `mk r nofind`; `snap r > before`; `cli $CAND r`; `snap r > after` | exit 0, stdout `{"paths": []}`, `diff before after` empty (no `docs/milestones` directory was created); `py $BASE` on a copy prints `[]` |
| 3 | on flow 1's `r`: run `cli $CAND r` twice more; `echo stale > r/docs/milestones/completed/wi-findings.md`, run it again; `rm r/docs/ai-workflow/registry/wi-dispositions.json`, run it again | the first two runs print the same stdout and leave the same bytes; the stale record is restored to the first run's bytes; after the removal `paths` is only the record |
| 4 | `mk r early`, `cp -a r r2`; `py $BASE r2`; `cli $CAND r`; the same with `afr` | the Python path **writes** a record whose disposition column says `none` (the baseline: no guard). cand: exit 1, `{"code": "work_item_not_complete", "error": "FindingsRecordPreflightError", "record_changed": false, "state_changed": false, ...}`, the message naming the phase; `snap` before and after identical |
| 5 | `mk r undisp`; `cp -a r r2`; `py $BASE r2`; `cli $CAND r` | both write the record with `none` dispositions and print the record path only: the command adds no disposition check (acceptance already refuses it); `cmp` of the two records is silent |
| 6 | `mk r baddisp`; `py $BASE r`; `cli $CAND r` (each on a copy; `snap` first) | the Python path raises `InvalidFindingDispositionsError`; cand: exit 1 with that class name, `record_changed` false, no record file, `snap` identical |
| 7 | `mk r blocked`, `mk q dirrec`; run `py $BASE` and `cli $CAND` on a copy of each | cand: exit 1 with the same class name the Python path raises (a `FileExistsError` for `blocked`, an `OSError` subclass for `dirrec`), `record_changed` false, `snap` identical; no traceback on stdout |
| 8 | `cli $CAND r unknown`; `cli $CAND r ""`; in an empty `git init` directory; with the state file removed; with `corrupt` text in it; with `[]` and `{}` in it; in a directory outside any repository | exit 1 each, one JSON object: `UnknownWorkItem`, `UnknownWorkItem`, `StateMissing`, `StateMissing`, `CorruptJsonError`, `StateMalformed`, `StateMalformed`, and a class name (no traceback) for the last; `record_changed` and `state_changed` false; tree unchanged |
| 9 | `mk r done`; for each of `--finding-dispositions wi`, `--plan-review-publication-status wi`, `--acceptance-gate wi`, `--satisfy-acceptance wi` run base and cand and compare stdout and exit; run `--write-findings-record wi --acceptance-gate wi` and `--write-findings-record wi --finding-dispositions wi` with cand | each of the four old flags prints byte-identical output and exit code from base and cand; both pairs exit 2 with "not allowed with argument" |
| 10 | `cat $GH_LOG` after flows 1 to 9, and `ls r/.ai-review` | the log is empty (no forge call); no `.ai-review` directory (no state lock was taken) |
| 11 | `grep -n -e '--write-findings-record' -e 'write_finding_dispositions_record' payload/.claude/commands/accept-milestone.md`; the same for `satisfy-gate.md`; then, in `mk r early` after `cp -a "$CAND" r/scripts` (`mk` does not create `scripts/`), run the documented line verbatim from `r` with the id substituted | the flag precedes the first `write_finding_dispositions_record` in `accept-milestone.md`; the three pinned phrases are still present; `satisfy-gate.md` still names `commit_gate_policy_floor` as the one remaining Python call; the line has no `python3 -I`; it runs (no `ModuleNotFoundError`) and refuses with `work_item_not_complete` |
| 12 | `git diff bf1b456 <the CP1 commit> --stat -- payload docs manifest.json`; `git diff bf1b456 <the CP1 commit> -S commit_gate_policy_floor -- payload/scripts/workflow_state.py` | the first lists `workflow_state.py`, `workflow_gate_policy_test.py`, `workflow_integration_test.py`, `satisfy-gate.md`, `accept-milestone.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md` (updated by `/milestone-implement`), the plan, registry, mapping, declaration and the state; no `workflow_protocol.py`, no manifest; the second is empty |
| 13 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` and its checker, `check-manager-block` with `--manager-releases`, the `tools/release` tests with the zlib-ng interpreter | all pass (the protocol and matrix suites report their own deliberate skips; `tools/release` fails rather than skips); the new tests run |
| 14 | (needs the full environment) scope: `git diff bf1b456 --stat` at CP2 | CP2 adds `manifest.json`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md` and `tools/release/release_test.py`; no file added or removed; protocol still `1.5` |

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #148 proposal, findings record | one plain command for the re-runnable record write | CP1 | D-Flag, R1 to R8 |
| #148 proposal, floor commit | the state-only commit after the completion commit | none: row 38 | 0c (recovery design) |
| #148 optional | `next-action` names the missing dispositions | none | out of scope; only if the owner asks |
| Library phase gap | `complete_work_item` from `IMPLEMENTING` and `MILESTONE_COMPLETE` | none | wf#158 item 1, the row after 38 |
| Row 37 | `Current` with this plan, `Done` at acceptance; row 38 `Next` | CP1 | D-Docs |
| Release | `feat:` 2.28.0, protocol `1.5`, no Controller change | CP2 | D-Release, 0d |
