# W41: Workflow 2.27.0 — the acceptance completion as one plain command (Revision 3)

- **Work item:** `acceptance-completion-command` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-05 (passed on from the RepFlow lane):
  RodrigoFAbreu/workflow#148, the second half; `docs/ROADMAP.md` row 36 (`Next`, becomes `Current` with this plan,
  `Done` at acceptance). The first half is row 35 (Workflow 2.26.0, `docs/milestones/completed/ACCEPTANCE_PLAIN_COMMAND_PLAN.md`).
- **Branch:** `milestone/acceptance-completion-command`
- **Base commit:** `b2db092742459901ea50734d9bccf0d58dcc73fc` (main after #157: release source and own installation are
  2.26.0; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2 (round 1 of the local review applied, section 7). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1: the investigation (before any design)

### 0a. What the worker does after `--acceptance-gate` says `ready`, in order

Read from `payload/.claude/commands/satisfy-gate.md` (the acceptance stage, steps 0 to 6) and the steps of
`payload/.claude/commands/accept-milestone.md` it cites (2a, 2b, 3 to 8), against `workflow_state.py` at the base.

| # | Step | What it is | Writes |
| --- | --- | --- | --- |
| 0 | stage step 0 | `python3 scripts/workflow_backlog.py preflight-accept <id>`: already a plain command | no |
| 1 | `/accept-milestone` 2a, first bullet | Python: `resolve_own_registry_completion_status` then `milestone_complete_gate_reachable` (the phase and the registry). **Only the worker's reading of the text performs it: the library does not** (see 0d) | no |
| 2 | stage steps 1 to 3 | Python, **one** call: `satisfy_acceptance_gate(repo_root, id, now=<now>)` = one `state_transaction`: `anchor_of`, the network query (`resolve_gh`, `query_forge_pr_facts`), `store_workflow_pr_fact`, `reopen_for_stored_fact`, `evaluate_gate`, then `apply_acceptance_satisfaction` (`assert_acceptance_evidence_current`, `build_acceptance_satisfaction`, `complete_work_item` with its children, own-checkpoint, completion-obligation and `assert_finding_dispositions_recorded` refusals). Returns `{record, trailer}`, or raises | **yes**: the PR fact (and a possible reopening) even on a gate refusal; on success `MILESTONE_COMPLETE` and `acceptance_satisfaction`; every refusal inside the mutator writes nothing |
| 3 | stage step 4, `/accept-milestone` 3 to 5 | by hand, plain: `docs/ROADMAP.md` row, `docs/ACTIVE_MILESTONE.md`, the archive copy, `workflow_backlog.py accept` when declared | files |
| 4 | `/accept-milestone` 5a | Python: `write_finding_dispositions_record(repo_root, state, id)` on the completed state; returns the paths to stage | **yes**: `docs/milestones/completed/<id>-findings.md` |
| 5 | stage step 4, `/accept-milestone` 6 | by hand: `git commit` with the final paragraph `Workflow-Work-Item: <id>` and `Workflow-Gate-Satisfied-By: policy:<12>` (`acceptance_satisfied_by_trailer(record)`, a string the command returns as `trailer`) | the commit |
| 6 | stage step 5 | Python: `commit_gate_policy_floor(repo_root, now=)`, only when a stricter setting was observed: its own state-only commit with `Workflow-Gate-Policy-Floor` | **yes**: state and a commit |

Rows 2, 4 and 6 are the Python calls (`gate_satisfied_by_trailer` belongs to the plan and implementation stages, not
here). Row 3 and 5 stay the worker's: the roadmap row, the archive copy and the completion commit message
are judgment about prose and the item's own history (the owner's row 36 keeps them so), and the commit's trailers
are the Workflow's own commit contract that the worker states; the command hands it the exact `trailer` value.

### 0b. Which mechanisms: the findings record and the floor are separable (sizing, the owner's rule)

- **Row 6 cannot be in the completion's process.** `satisfy-gate.md` step 5 and `LPR-R18-001`/`LPR-R23-003` order it
  **after** the worker's completion commit (the floor is recorded against the virtual floor first;
  `commit_gate_policy_floor` asserts a clean index and commits). A command that ran it inside the completion would
  run it before the commit it must follow, or would have to commit for the worker, which row 36 forbids.
- **Row 4 cannot be a step of the completion either.** It reads the *completed* state, writes a file and can fail
  after the state is complete, when the stage can no longer be re-run (a terminal item is refused). Its recovery is
  therefore a standalone, re-runnable invocation in any case, so embedding it adds coupling and no value. It is also
  `/accept-milestone`'s own step 5a (the human path).
- So the completion (row 2 with row 1's guard) is **one mechanism**; rows 4 and 6 are two more, each a thin wrapper of
  an existing function. **This item plans only the completion.** Rows 4 and 6 are the next row, **37** (`Next`,
  written with this plan). Until row 37, a worker still runs two short Python calls; the issue's denials fall by the
  largest call (the one with `gh` and the state transaction), not to zero. Said plainly in the hand-off.

### 0c. Flag or protocol operation: a flag, by evidence (decision (i))

- `ORCHESTRATION_PROTOCOL.md` section 1: a **minor** bump "only adds ... new capabilities"; `describe` lists
  `capabilities.operations` (5.1), so a `workflow_protocol.py` operation is protocol `1.6`, a schema, test and
  `describe` change, and **the Controller lane must learn it**.
- The Controller never runs the completion. `next-action` row 38h returns the action `acceptance.satisfy`, whose
  `invocation` is the command text `/satisfy-gate acceptance {id}` (action table, role `validator`); the Controller
  launches a **worker** with that command and reads the outcome through `reconcile` (section 7: the act's effects are
  observed in state, not through an operation). What script the worker runs inside the command is not in the protocol
  ("It copies no ... helper names"). `record-external-result` is an operation because the Controller itself calls it
  with a fact it holds; nothing like that exists here.
- The protocol's header says every read path is read-only and `record-external-result` is the one writer; a second
  writer would change that statement for no consumer.
- Precedent: `--finding-dispositions` (2.14.0, protocol `1.4` unchanged), `--acceptance-gate` (2.26.0, `1.5`
  unchanged), `workflow_backlog.py accept` (a writer outside the protocol). `COMMAND_FILES.md` has no flag rule;
  `state_writer: true` stays and holds: the write goes through `state_transaction`.
- **Decision: (i), a `workflow_state.py` flag. Protocol stays `1.5`; no Controller change.** Nothing here forces (ii).

### 0d. Measured baseline (scratch repository, the suite's `AcceptanceRepo`, a fake query)

`satisfy_acceptance_gate` on the base, same repository, four states (a probe, not shipped):

| State | Result | State file |
| --- | --- | --- |
| phase `AWAITING_FUNCTIONAL_REVIEW`, flow recorded, query green | `{record, trailer}`: `policy:bae758b4f4ce`, record keys `adopted_digest, evaluated_at, file_digest, floor_digest, inputs, policy_digest, policy_source, requirements, trust, workflow_release` | changed, `MILESTONE_COMPLETE` |
| **phase `IMPLEMENTING`**, otherwise the same | **completes** | changed, `MILESTONE_COMPLETE` |
| one recorded Optional finding, no disposition | `UndispositionedFindingsError` | unchanged (the query ran, nothing stored) |
| no functional flow recorded | `GateNotSatisfiableError` ("Only the pull-request fact the query read was stored") | changed (the fact) |

The second row is the finding that shapes the design: the library has **no phase guard**, because the stage's step 2a
(row 1 of 0a) is a pre-flight the worker performs by following the text. A plain command that called the library
alone would be easier to misuse than the text is. So the command performs row 1 as well (D-Preflight).
A fake `gh` (`pr list ...` printing one green pull request for the `--search` commit), put first on `PATH` outside
the temporary directory, was run through the real `resolve_gh` and `_default_run` on the same repository: the same
`policy:bae758b4f4ce` and a `workflow_gh` fact. That script is the one of section 5.

## 1. Goal, release, and what stays as it is

A headless worker completes the acceptance gate with **one plain command**, `python3 scripts/workflow_state.py
--satisfy-acceptance <work-item-id>`, with no inline Python and no heredoc. It runs `satisfy_acceptance_gate` in one
process, under the same `state_transaction`, and prints `{record, trailer}`. The command text names it first and keeps
the Python description as the specification.

- **Release: Workflow 2.27.0, a `feat:` minor** (a new command surface a worker is told to run). `manifest.json`'s
  `workflow_version` moves 2.26.0 to 2.27.0; the protocol stays `1.5`.
- **Gate semantics do not change.** The command calls `satisfy_acceptance_gate` and adds no requirement: same
  requirements, same refusals, same query, same trust record, same commit order (the worker's completion commit still
  follows the command; the floor after it), same by-policy record. **No line of `satisfy_acceptance_gate`,
  `apply_acceptance_satisfaction`, `complete_work_item`, `evaluate_gate` or `state_transaction` changes.** The one
  addition is the stage's own step 2a pre-flight, which the command text already makes the worker perform (D-Preflight).
- **Not done here:** the findings record and the floor commit (row 37); the document edits and the completion commit
  (the worker's, row 36's own words); `/approve-review`; **the optional `next-action` evidence line, declined**: it
  changes `workflow_protocol.py`'s row 38h (a Controller-read string), its `ctx.call` registrations pinned in
  `workflow_protocol_test.py` and the mirrored tables, none in this item's files, a second mechanism. It stays open on #148.

## 2. Design decisions

### D-Flag: the interface

`python3 scripts/workflow_state.py --satisfy-acceptance <work-item-id>` (plain, not `python3 -I`: `workflow_state.py`
imports `workflow_fingerprint` from its own directory, as `--acceptance-gate` documents). A fourth member of the existing
mutually exclusive group, dispatched right after `parse_args`, **before** the shared `git rev-parse`, with
`args.satisfy_acceptance is not None` (an empty id is an `UnknownWorkItem`, not "absent"). It has no other option: `run_ref`
stays `None`, as the text calls the library today. The argparse description (it says "Read-only") is reworded.

### D-Preflight: the stage's step 2a, shared with the report

Before anything is written or queried, the command runs `/accept-milestone` step 2a's first bullet, the **same code**
`acceptance_gate_report` uses for its `work_item_terminal`, `registry_unresolvable` and `phase_not_reachable`
blockers: extracted unchanged into `_acceptance_reachability_blocker(repo_root, work_item_id, work_item)` (returns a
`{code, detail}` or `None`), called by both. The report's output is byte-identical. A blocker raises
`AcceptancePreflightError(code, detail)` (a new class in `workflow_state.py`; the library is not touched), printed as an
error object, exit 1, nothing written, `gh` never called. The check is advisory exactly as step 2a says
(`complete_work_item` re-validates the registry inside); the phase has no other guard, so this is the guard. It reads before `state_transaction` takes the lock, so a writer landing in that
window can move the phase and the library then completes from there; this is no worse than today's text path and the window is small, so
it needs no design change here. The library gap itself (`complete_work_item` completes from `IMPLEMENTING`, and from
`MILESTONE_COMPLETE` too, a re-completion measured as `policy:bae758b4f4ce`) is a follow-up, recorded on row 37 and in section 3.
It does **not** run `preflight-accept` (already a plain command, step 0) or the disposition pre-flight
(`complete_work_item` makes it inside the transaction, so a refusal writes nothing, as the text says).

### D-Output: the answer

Success: exit 0 and exactly `{"record": <acceptance_satisfaction record>, "trailer": "policy:<12>"}` (`sort_keys=True`,
`indent=2`), the library's own return value, nothing else on stdout.
Refusal or any exception: exit 1 and one object `{"error": <exception class name>, "message": str(exc), "state_changed":
bool}` plus `"code"` when the exception has a string `code` (`ForgeUnavailableError` `forge_unavailable`,
`ForgeUndecidableError` `forge_undecidable`, `EvidenceRefusedError`'s codes, `AcceptancePreflightError`'s). The
worker's rule is in the text: `state_changed: false` means stop and write nothing; `true` with `GateNotSatisfiableError` means
only the pull-request fact (and maybe a reopening) was stored, as the message says; **a refusal is never worked around by
hand-writing the completion**. `state_changed` is a measurement: the sha256 of `docs/ai-workflow/WORKFLOW_STATE.json`
before the pre-flight and after the call (a concurrent writer can also change it; the state lock is held only inside
the call). Exit 2 stays argparse. The existing flags, their output and exit codes are byte-identical.
Errors before the call (`StateMissing`, `CorruptJsonError`, `StateMalformed`, `UnknownWorkItem`, a run outside Git) are
the read-only flag's own objects, found the same way (class name fallback, never a traceback), with `state_changed: false`.

### D-Transaction: why the discipline is the same

The command is `satisfy_acceptance_gate(repo_root, id, now=<UTC now>)` and nothing else: one `state_transaction`, the
lock held across re-read, query, evaluation, `apply_acceptance_satisfaction` and publish. The command takes no lock of
its own, makes no `git add` or `git commit`, writes no file other than the state file and the state lock `.ai-review/runtime/WORKFLOW_STATE.lock`, which `state_lock` creates on first use (the
findings record and the floor are row 37). Every "whole tree outside `.git`" comparison below, in the tests and the flows, therefore
excludes `.ai-review/runtime/` explicitly, so a fixture that has not yet run a transaction does not change the result, and the pre-flight and the digests only read. `now` is `%Y-%m-%dT%H:%M:%SZ`, the format
`workflow_protocol.py` uses; the CLI function takes `now`, `run` and `resolve` as test seams (default none), like the library.

### D-Command: the command text

`satisfy-gate.md`'s "Plain commands first" block names the completion after the report: a line
`python3 scripts/workflow_state.py --satisfy-acceptance <work-item-id>` (alone on its line, as the existing test finds
`--acceptance-gate`), **that step 0's `workflow_backlog.py preflight-accept` runs first and that the flag does not run it** (the flag's `--acceptance-gate` report
names the backlog pre-flight in `not_checked`, so `ready: true` does not stand in for it: a refusal there is the stop that stores nothing, and
running the flag first would complete the item before `workflow_backlog.py accept` can refuse at `/accept-milestone` step 3), what it does (step 1 to 3's one transaction, preceded by step 2a's phase check), the answer and the
error object with the `state_changed` rule, that it does not commit or edit documents, and that `satisfy_acceptance_gate` and
the other Python descriptions are the specification. The sentence "The completion ... is still the Python call below
until its own plain command exists" is replaced. Steps 4 and 5's findings record and floor stay the Python calls until
row 37, and the text says so. **Every other sentence stays**; `state_writer: true` stays.

### D-Tests

All in `payload/scripts/workflow_gate_policy_test.py`, class `TestSatisfyAcceptanceCommand` on `AcceptanceRepo`, the CLI
function called in-process with the suite's fake query seams and a fixed `now`; subprocess only where the real
`resolve_gh` matters. Each test states exact output.

- **S1 parity**: for six states (ready, ready with a disposed finding, a red stored fact that reopens, `human`, an unmet
  requirement, a missing disposition), the command's outcome equals `ws.satisfy_acceptance_gate` on a **copy** of the
  repository with the same `now`: the same record and trailer, or the same exception class and message, and
  **byte-equal** `WORKFLOW_STATE.json` and every other file outside `.git`.
- **S2 no write**: each refusal that writes nothing leaves the whole tree outside `.git` and `.ai-review/runtime/` (the state lock; directories included), the refs
  and `HEAD` identical and `state_changed` false: the phase refusals (`IMPLEMENTING`, `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`,
  `MILESTONE_COMPLETE`, an unresolvable registry; the fake query asserts **zero** calls), a forge refusal inside the call
  (`forge_unavailable`), the disposition refusal (one query call, nothing stored), and every error before the call.
- **S3 the answer**: success prints exactly `{record, trailer}` with `trailer == ws.acceptance_satisfied_by_trailer(record)`
  and the state `MILESTONE_COMPLETE`; the gate refusal prints the error object with `state_changed` true and the state
  holding the stored fact; every key set is exact; exit codes 0 and 1.
- **S4 discipline**: `ws.state_transaction` is entered **exactly once**; no commit and no ref moves; the only file that
  differs after success is the state file; the findings record is **not** written even for an item with findings.
- **S5 interface**: two flags together exit 2; an empty id is `UnknownWorkItem`; a state `{}` or `[]` is `StateMalformed`; a run
  outside Git is the class-name fallback; `--finding-dispositions`, `--plan-review-publication-status` and
  `--acceptance-gate` print output byte-identical to before on the same repository.
- **S6 the real `resolve_gh`**, in a subprocess: `PATH` without `gh` is `forge_unavailable`; a `gh` in the temporary
  directory is `forge_undecidable`; each leaves the tree unchanged.
- **S7 the command text**: names `--satisfy-acceptance` after `--acceptance-gate` and before the first `satisfy_acceptance_gate`, states that step 0's
  `preflight-accept` runs first and that the flag does not run it, with that sentence **before** the flag's line in the block,
  keeps every pinned phrase and `state_writer: true`, has no `python3 -I` on it, and the documented line (found by pattern,
  the id substituted) runs as written in a scratch repository and exits as S2 says (a refusal for the early state).
- **S8 shared pre-flight**: the report's blockers for the three codes are unchanged (the existing tests) and the command
  and the report call one function.

**Failure-only mutations** on a scratch copy, one per behaviour, each failing the named test, recorded: m1 the
pre-flight dropped (S2, S1); m2 the pre-flight applied after the call (S2); m3 the success output gains a key or the
trailer is recomputed (S3); m4 a refusal exits 0 (S3); m5 the command re-implements the mutator without
`reopen_for_stored_fact` (S1, the red-fact state); m6 `state_changed` constant (S3, S2); m7 the command wraps the call in a second
`state_transaction` or bypasses the library's (S4); m8 the command writes the findings record or commits (S4); m9 the
dispatch after the shared `git rev-parse` (S5); m10 the empty id falls through (S5); m11 the flag outside the exclusive
group (S5); m12 an existing flag's output changed (S5); m13 the forge error swallowed so the fact is stored (S2, S6);
m14 the command text drops the flag or moves it after the Python (S7); m16 the step-0-first sentence dropped, or placed after the flag's line (S7); m15 the helper copied, not shared (S8) (m1 to m16 in all).

### D-Docs

`docs/exit-codes.md`: the rows of the new flag (0 `{record, trailer}` printed and the item is `MILESTONE_COMPLETE`; 1 the JSON
error with `state_changed`; 2 arguments; "also two of the four" in the existing row); no milestone id.
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (CP2): the release list and the one sentence that 2.27.0 adds a
`workflow_state.py` flag that writes through `state_transaction` and is not a protocol operation (the protocol stays `1.5`).
`docs/ROADMAP.md`: row 36 `Current` with its description updated to what this item does, row 37 `Next` (0b), written with
this plan; row 36 becomes `Done` at acceptance.

### D-Release

2.27.0. `manifest.json`: `workflow_version`; the changed records (`satisfy-gate.md`, `workflow_state.py`,
`workflow_gate_policy_test.py`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`) take their `sha256` and
`size`; no file is added or removed; `conformance.suites` by `release.py manager-block --write`. `WORKFLOW_RELEASE` becomes
2.27.0 with its pinned assertions; `tools/release/release_test.py` gets a 2.27.0 class and the 2.26.0 class gives up the
current-release pins. `docs/release-history.md`: the 2.27.0 row; the way back to 2.26.0 only removes the flag (nothing to migrate).

**The Manager block's posture** (`manager.downgrade_boundary.posture`, Manager-facing, unchecked by any tool, `docs/RELEASING.md` "Not checked"; it
is rewritten, the 2.26.0 wording does not carry over, except the downgrade guidance below, which carries over sentence for sentence): Workflow 2.27.0 is a minor release that adds `python3 scripts/workflow_state.py
--satisfy-acceptance <work-item-id>`, **the first flag on this CLI that writes state**, through `state_transaction` (the same completion records as
the Python path's); it is not a protocol operation and Orchestration Protocol stays 1.5 (the release constant becomes 2.27.0);
`workflow-manager update back to 2.26.0` (minimum Manager 1.13.0) removes the flag and restores `WORKFLOW_RELEASE` 2.26.0, and nothing needs
undoing, because the completion records the flag writes are the same as the Python path's; the 2.26.0 posture's guidance sentence carries over verbatim, with only its first words naming 2.26.0 and earlier: "The guidance of 2.26.0 and earlier still applies unchanged: finish an interrupted checkpoint-start release (run /release-checkpoint-start again to completion) before moving back below 2.19.0, and before a move back below 2.14.0 (or 2.15.0 for review_round_counts) follow the procedure in the 2.18.4 row of docs/release-history.md." Each changed record's
`rationale` carries one sentence, `acceptance-completion-command (workflow-2.27.0)`, on exactly the six changed records. The 2.27.0 release class
in `tools/release/release_test.py` pins the posture's needles (`2.27.0`, `2.26.0`, `--satisfy-acceptance`, `state_transaction`,
`Orchestration Protocol stays 1.5`, `not a protocol operation`, `workflow-manager update back to 2.26.0`, `WORKFLOW_RELEASE`, `removes the flag`,
`nothing needs undoing`, `/release-checkpoint-start`, `2.14.0`, the two pins the 2.26.0 class already carries at `tools/release/release_test.py:3548`), that sentence and `CHANGED`, and the new `conformance.suites` counts.

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w41-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): recompute `sha256` and `size` of every
record whose file differs (none added), measure `conformance.suites` (**the `workflow_gate_policy_test.py` count moves**: D-Tests adds every
new test to that suite), commit in the clone, run the "Verification commands" of `docs/RELEASING.md`. `tools/release` tests use
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
**The one expected failure at CP1** (measured on a scratch clone of the base with the count set to 347: `AssertionError`, `(1249, 346)`, 1 test failed):
`AcceptancePlainCommandReleaseTest.test_the_manager_block_states_the_minor_and_the_way_back_in_the_posture` (`tools/release/release_test.py`)
pins `suites["workflow_gate_policy_test.py"]` to 346, so it fails once the measured count is written. CP1 proves `tools/release` by that
single named failure and **every other `tools/release` test passing**; the pin is released in CP2, where the 2.26.0 class gives up the
current-release pins. Leaving the count unwritten is not an option: the block would then disagree with the measured suite.
CP2's stock `stage-conformance` run is the real proof.

## 3. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **A flag, not a protocol operation** (0c), decided by evidence; (ii) would be protocol `1.6` and a Controller change.
- **The command includes step 2a's phase check, which the library lacks** (0d): the only addition to the stage's semantics, taken
  because the text already requires it and the alternative is a command that completes from `IMPLEMENTING`.
- **Rows 4 and 6 are row 37**, a roadmap row added with this plan (the owner's sizing rule); drop it if the owner prefers them here.
- **`state_changed` is reported**; without it a worker cannot tell "stop, nothing stored" from "the fact was stored" by class alone
  (both are `GateNotSatisfiableError`).
- **`run_ref` is not exposed**; the text never passes it.
- **The library's phase gap** (`complete_work_item` completes from `IMPLEMENTING` and `MILESTONE_COMPLETE`) is not closed here (no line of the library changes); it is a follow-up on row 37.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The completion flag, its tests, the command text and the pages | - | 3 | 1 |
| CP2 | Release 2.27.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The completion flag, its tests, the command text and the pages

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py`,
`payload/.claude/commands/satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): S1 to S8 written and run red against the unedited tree; mutations m1 to m16 each fail the named
  test on a scratch copy and the results are recorded.
- **The change** (D-Flag, D-Preflight, D-Output, D-Transaction): `_acceptance_reachability_blocker` extracted from
  `acceptance_gate_report` (byte-identical output), `AcceptancePreflightError`, `_satisfy_acceptance_cli`, the fourth group member and its
  dispatch; nothing else. Every existing test passes unmodified (no assertion pins the replaced sentence: "until its own plain" and "still the Python call" occur only in `satisfy-gate.md`).
- **The command text and the pages** (D-Command, D-Docs). `check_docs.py` stays clean.
- **No other mechanism:** `git diff b2db092 --stat -- payload` lists `workflow_state.py`, `workflow_gate_policy_test.py` and
  `satisfy-gate.md` only; `docs/ROADMAP.md` carries row 36 `Current` and row 37 `Next`.

**Verification:** the new tests as the suite runs them; D-Staging in a disposable clone: the nine suites from the staged fixture,
`tools/docs`, `check_docs.py`, `check-manager-block` (with `--manager-releases`), `tools/release` (zlib-ng interpreter, no
patch, no skip, with **one expected failure**, named in D-Staging); the new tests again under the Manager's orphan rule (reaper).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.27.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`,
`tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.27.0 with its pinned assertions and the protocol-document edits (protocol stays `1.5`; D-Docs).
- `manifest.json` 2.27.0 (D-Release): `workflow_version`, the changed records, `conformance.suites`.
- The Manager block's posture, rewritten for 2.27.0 (D-Release: `--satisfy-acceptance`, a state writer through `state_transaction`, protocol stays `1.5`,
  `workflow-manager update back to 2.26.0` removes the flag, nothing needs undoing), and each changed record's `rationale` sentence.
- `docs/release-history.md`: the 2.27.0 row and its "Last checked with" line; that of `docs/exit-codes.md` moves too.
- `tools/release/release_test.py`: a 2.27.0 class pinning the posture, the `rationale` sentence, `CHANGED` and the suite counts; the 2.26.0 class gives up the
  current-release pins (the `(1249, 346)` pin among them).

**Verification:** the new tests again; the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture;
`release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Every flow runs offline: no network, no real `gh`, no install,
no socket, no zlib-ng, no Python 3.12; nothing runs against the real repository, its `.ai-review/` or the forge.** Setup, once, under
`$TMPDIR` (`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w41-tmp`):
`base/` from `git archive b2db092 payload/scripts` and `cand/` from the working tree's `payload/scripts`. The fake `gh` lives in a
directory that is not under `/tmp`, `/var/tmp`, `/dev/shm` or `$TMPDIR` and is mode 0755 (the real `resolve_gh` accepts it):

```sh
export W41_BIN="$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w41-bin"
mkdir -p "$W41_BIN" && cat > "$W41_BIN/gh" <<'EOF'
#!/bin/sh
echo "gh called: $*" >> "$GH_LOG"
case "$GH_MODE" in
  fail) echo "boom" >&2; exit 1 ;;
  empty) echo '[]'; exit 0 ;;
  red) printf '[{"number":7,"url":"https://github.com/o/r/pull/7","state":"OPEN","headRefOid":"%s","reviewDecision":"CHANGES_REQUESTED","reviews":[{"id":"R1","state":"CHANGES_REQUESTED","body":"please fix x","commit":{"oid":"%s"}}],"statusCheckRollup":[{"name":"ci","status":"COMPLETED","conclusion":"SUCCESS"}]}]\n' "$8" "$8"; exit 0 ;;
esac
printf '[{"number":7,"url":"https://github.com/o/r/pull/7","state":"OPEN","headRefOid":"%s","reviewDecision":"","reviews":[],"statusCheckRollup":[{"name":"ci","status":"COMPLETED","conclusion":"SUCCESS"}]}]\n' "$8"
EOF
chmod 755 "$W41_BIN/gh"; export GH_LOG="$W41_BIN/gh.log"; : > "$GH_LOG"
```

`python3 -I flow.py <cand>/payload/scripts <cli-scripts> <case>` (`flow.py` inserts the candidate directory in `sys.path`, builds a
scratch repository with `workflow_gate_policy_test.AcceptanceRepo`, **copies it** (same commits) to a second root, runs the
Python path `ws.satisfy_acceptance_gate(root, "wi", now=N)` in the copy with `PATH=$W41_BIN:$PATH` and the plain command
`python3 <cli-scripts>/workflow_state.py --satisfy-acceptance wi` (not `-I`) in the original, and prints for each: exit code,
stdout, the state file with timestamps **and `fact_id`s** masked (`\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ` to `T`, and `"fact_id": "<64 hex>"` to `"fact_id": "F"`: the plain command has no `now` seam, so its `fetched_at` differs from the Python path's `now`, `store_workflow_pr_fact` puts `fetched_at` in the provenance and `_build_fact` hashes the provenance into `fact_id`, so `fact_id` is a timestamp in hashed form that the timestamp mask does not reach; the exact, same-`now` parity is S1's), whether the tree outside `.git` and `.ai-review/runtime/` (the state lock) and the
refs changed, and the `gh` log lines it added). `<case>` sets the scratch state: `ready` (phase `AWAITING_FUNCTIONAL_REVIEW`, flow
recorded), `early` (`IMPLEMENTING`), `terminal` (`MILESTONE_COMPLETE`), `noflow` (no functional flow), `missing` (ready plus two
recorded Optional findings, no dispositions file), `human` (`GATE_POLICY.json` with `human_approval` true), `red` (ready,
and `flow.py` sets `GH_MODE=red`: the query finds a standing `CHANGES_REQUESTED`), `badregistry` (the registry file removed); the error cases `unknown`, `emptyid`, `nostate`,
`corrupt`, `malformed` (`[]`), `malformed_empty` (`{}`) and `nogit` (a directory outside any Git repository) run the plain
command only.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `ready` with cand (the base has no flag: also run `--satisfy-acceptance wi` with base) | base: exit 2 and the argparse "one of the arguments" refusal. cand: exit 0; stdout is `{record, trailer}` and nothing else, `trailer` `policy:<12>` of the record's `policy_digest`, the item `MILESTONE_COMPLETE`; the masked state equals the Python path's, the record equals the Python path's under the same mask (`evaluated_at` and `inputs.pr.fact_id`); the only file that changed is `WORKFLOW_STATE.json` (no findings record, no commit, same `HEAD`); one `gh` call |
| 2 | `early` with base-Python and with cand | the Python path **completes** (the library has no phase guard: the baseline of 0d). cand: exit 1, `{"error": "AcceptancePreflightError", "code": "phase_not_reachable", "state_changed": false}`, the message naming `IMPLEMENTING`; tree and refs unchanged; **zero** `gh` calls |
| 3 | `terminal` and `badregistry` with cand | `terminal`: exit 1, `work_item_terminal`; `badregistry`: exit 1, `registry_unresolvable` with the registry error text; both `state_changed` false, tree unchanged, zero `gh` calls |
| 4 | `noflow` with cand and the Python path | cand: exit 1, `GateNotSatisfiableError`, `state_changed` true, the message listing `functional_flows_passed: no functional flow is recorded` and "Only the pull-request fact the query read was stored"; the masked state equals the Python path's after its raise; the phase is still `AWAITING_FUNCTIONAL_REVIEW` |
| 5 | `missing` with cand and the Python path | cand: exit 1, `UndispositionedFindingsError` naming both keys and the skeleton command; `state_changed` false, the state file byte-identical to before; **one** `gh` call (the query ran, nothing was stored); the Python path raises the same class and message |
| 6 | `ready` with `GH_MODE=fail`, then with `GH_MODE=empty`, with cand | `fail`: exit 1, `ForgeUnavailableError`, `code` `forge_unavailable`, `state_changed` false, tree unchanged. `empty`: the fact is `state: none` and the gate refuses as in flow 4 (`pr_fact_current` unmet), `state_changed` true |
| 7 | `ready` with cand and a `PATH` holding only a symlink to `git` (no `gh`), then with a copy of the fake `gh` under `$TMPDIR` first on `PATH` | first: `forge_unavailable`; second: `forge_undecidable` naming the path inside the temporary directory; both `state_changed` false, tree unchanged |
| 8 | `human` and `red` with cand and the Python path | `human`: exit 1, `GateNotSatisfiableError` (mode `'human'`), fact stored as in the Python path. `red`: exit 1, `GateNotSatisfiableError` whose message names `no_standing_pr_objection` and "the item was reopened for remediation" (`reopenings` has one entry, the phase stays `AWAITING_FUNCTIONAL_REVIEW`); the masked state equals the Python path's |
| 9 | `unknown`, `emptyid`, `nostate`, `corrupt`, `malformed`, `malformed_empty`, `nogit` with cand | exit 1 each: `UnknownWorkItem`, `UnknownWorkItem` (the empty id is not "absent"), `StateMissing`, `CorruptJsonError`, `StateMalformed`, `StateMalformed`, and for `nogit` a class name (no traceback); one JSON object on stdout, `state_changed` false, tree unchanged, zero `gh` calls |
| 10 | `--satisfy-acceptance wi --acceptance-gate wi` and `--finding-dispositions wi` / `--plan-review-publication-status wi` / `--acceptance-gate wi`, base and cand | the pair: exit 2, "not allowed with argument"; the three old flags: stdout and exit code byte-identical between base and cand on one repository (no write on any) |
| 11 | `grep -n -e '--satisfy-acceptance' -e '--acceptance-gate' -e 'satisfy_acceptance_gate' payload/.claude/commands/satisfy-gate.md`, then run the documented line verbatim with the id substituted in the `early` repository with cand's `scripts/` | the two flags precede the first `satisfy_acceptance_gate`; the line has no `python3 -I`; it runs (no `ModuleNotFoundError`) and refuses with `phase_not_reachable` |
| 12 | `git diff b2db092 --stat -- payload docs` in the working tree at CP1 | `workflow_state.py`, `workflow_gate_policy_test.py`, `satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md` (updated by `/milestone-implement` at the checkpoint), the plan, registry, mapping, declaration and the state; no `workflow_protocol.py`, no manifest |
| 13 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` and its checker, `check-manager-block` with `--manager-releases`, the `tools/release` tests with the zlib-ng interpreter | all pass, no skip; the new tests run |
| 14 | (needs the full environment) scope: `git diff b2db092 --stat` at CP2 | CP2 adds `manifest.json`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md` and `tools/release/release_test.py`; no file added or removed; protocol still `1.5` |

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #148 proposal, completion | one plain command that runs the query, completion and prints `{record, trailer}` in one process | CP1 | D-Flag, S1 to S8 |
| #148 proposal, findings record and floor | the two thin wrappers after the completion | none: row 37 | 0b (separable; the floor must follow the worker's commit) |
| #148 optional | `next-action` names the missing dispositions | none | declined, section 1; stays open on #148 |
| Row 36 | `Current` with this plan, `Done` at acceptance; row 37 `Next` | CP1 | D-Docs |
| Release | `feat:` 2.27.0, protocol `1.5`, no Controller change | CP2 | D-Release, 0c |

## 7. Plan review, round 1 (LOCAL_MODEL_PLAN_REVIEW, REVISE): disposition

| Finding | Disposition |
| --- | --- |
| B1 | Accepted, verified (`tools/release/release_test.py:3554-3555` pins `(1249, 346)`). D-Staging and CP1's verification now name that one test as the single expected failure at CP1; CP2 releases the pin. |
| I1 | Accepted, verified (`satisfy-gate.md`: the "Plain commands first" block precedes step 0). D-Command, S7 and m16 pin step 0 first. |
| I2 | Accepted, verified (`manifest.json` posture names 2.26.0). D-Release and CP2 rewrite the posture and the `rationale` sentence; the 2.27.0 class pins both. |
| O1 | Accepted: the no-write comparisons exclude `.ai-review/runtime/` explicitly (D-Transaction, S2, the flows). |
| O2 | Accepted: sentence in D-Preflight, follow-up on row 37 and in section 3. |
| O3 | Accepted, verified by search: CP1's exception removed. |
| O4 | Accepted: flow 12 lists `docs/ACTIVE_MILESTONE.md`. |

## 8. Plan review, round 2 (LOCAL_MODEL_PLAN_REVIEW, REVISE): disposition

| Finding | Disposition |
| --- | --- |
| I1 | Accepted, verified (`payload/scripts/workflow_gate_policy.py:1653` puts `now` in the provenance as `fetched_at`; `:1598-1599` hash the provenance into `fact_id`). Section 5's `flow.py` masks `fact_id` as well, with the reason; flow 1's record comparison uses the same mask; exact, same-`now` parity stays with S1. |
| I2 | Accepted, verified (D-Tests says m1 to m16, the mapping's R5 names m16). CP1 now says m1 to m16. |
| O1 | Accepted, verified (`tools/release/release_test.py:3548` pins `/release-checkpoint-start` and `2.14.0` in the 2.26.0 class). D-Release says the sentences carry over unchanged, and the 2.27.0 needle list adds both. |
