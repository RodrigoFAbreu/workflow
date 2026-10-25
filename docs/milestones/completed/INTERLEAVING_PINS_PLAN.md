# W24: Workflow 2.19.1 — pin the deferred interleaving seams (Revision 2)

- **Work item:** `interleaving-pins` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator. It is row 26a of `docs/ROADMAP.md` (status `Current` from
  this plan, `Done` at acceptance). Row 26b (the wording and message fixes of RodrigoFAbreu/workflow#100) is a
  separate item and is **not** done here.
- **Issues:** RodrigoFAbreu/workflow#97 items 4 and 5, and the two pins of RodrigoFAbreu/workflow#100. The
  release **closes nothing**: it references both issues as partly done.
- **Branch:** `milestone/interleaving-pins`
- **Base commit:** `e8aff0a` (main after #103: the release source and this repository's own installation are
  both Workflow 2.19.0, automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file declared, so
  the prose roadmap applies)
- **Plan revision:** 2. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.19.1, a `fix:` patch, that adds **four pins to the shipped payload test suites** and changes
no behaviour. Each pin names a property of the checkpoint-start release and of the amendment refusals that
today holds only by the shape of the code, so that a later change cannot remove it silently:

1. **P1 (#97 item 4).** The release's guard re-read (step 5 of `release_checkpoint_start`) takes no
   checkpoint guardlock (6) (`guard_mutation_lock`) inside the body of its `with owner_mutation(...)` window.
   A call to `guard_holder_is_running`, or a re-read of the guard under (6), in that body would make the
   lock-order graph derive an undeclared (5)->(6) edge.
2. **P2 (#97 item 5).** Name the injection seams for the two residues `state_transaction` does not bracket
   (the entry-absent branch of the release, and the gap between the claim unlink and the guard release) and
   test an interruption at each (the engine's T4 and T7 cases).
3. **P3 (#100).** The third raise of `AmendmentCheckpointActiveError` (`open_plan_approval_journal`, the
   plan-approval open) carries no `/release-checkpoint-start`.
4. **P4 (#100).** The `IN_PROGRESS`-entry arm of `request_plan_amendment` is asserted directly after a
   release, over the real entry the release leaves on disk. Today `_assert_amendment_accepted` builds a
   synthetic state with no entry for the released checkpoint, so only the on-disk claim arm is exercised.

### The invariant (one sentence)

**I1.** Every property above stays true of the shipped code and is **observable**: each pin fails against a
mutant that removes exactly the property it names, runs with no sleep as synchronisation, and leaves no
process behind.

### Hard limits (the owner's sizing rule)

- **No production change.** `payload/scripts/workflow_state.py` is not edited. No module-level hook is added;
  a seam is a patch of an existing function boundary, installed by the test (in the test process or in the
  worker source the test module owns). **If a pin needs a production change, a second theme, or a third
  checkpoint, STOP and split it into a roadmap row.** Implementation re-checks this before it ends CP1:
  `git diff e8aff0a -- payload/scripts/workflow_state.py` is empty.
- **The wording and message fixes are row 26b.** Nothing here edits a message, a command file or an operator
  document, and `payload/scripts/workflow_integration_test.py` is not edited (no command file changes, so no
  census changes).
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`, the managed documents of
  `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks of `CLAUDE.md` and `.gitignore`, and
  `.github/workflows/workflow-conformance.yml`. The change goes to `payload/`; release bookkeeping to
  `manifest.json`, `docs/` user documents and `tools/release/`.
- **Size:** two checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test shown to fail against its mutant and to pass unmutated
  (D-Evidence); the nine payload suites from a staged fixture; the new tests and the whole
  `workflow_state_test.py` chunk under the Manager's orphan wrapper (D-Orphan); the `tools/release` tests
  (zlib-ng environment); the `tools/docs` tests and checker; `check-manager-block` with
  `--manager-releases`; `workflow-manager verify .` clean. Every command form is copied from
  `docs/RELEASING.md`, "Verification commands".
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against `git diff` (CP2).

## 2. Facts this plan relies on (re-checked against `e8aff0a`)

- **The release window.** `release_checkpoint_start` takes the lifecycle lock (9), classifies the start
  (`_classify_checkpoint_start`), asks the probe `guard_holder_is_running` (it takes (6) as a leaf and is
  called before the guard is opened), opens one destructive `release-start` guard through
  `owner_mutation`, and inside that body: re-classifies; for kind `entry` restores the entry in one
  `state_transaction`; re-reads the claim and the guard (`resolve_claim`, `read_guard`, neither takes (6));
  unlinks the claim. The guard is released by `owner_mutation`'s exit (`release_guard`, which takes (6):
  the declared (5)->(6) release-time edge).
- **Two kinds of start.** Kind `entry` has an `IN_PROGRESS` working entry; kind `baseline` has a working
  entry equal to the one `HEAD` records (a start paused between its claim and its 1d window, or whose
  release already restored the entry), and calls **no** `state_transaction`.
- **The engine's tests already crash and fail the entry branch.** `TestReleaseCheckpointStart` T4 crashes a
  worker (`os._exit` in a wrapper over `ws.state_transaction`, or over `ws.release_guard`) before the
  write, after it and after the unlink, **only for kind `entry`**; T7 fails the unlink with `_UnlinkFails`
  (a `Path` subclass returned by a patched `ws.claim_path`, whose `unlink` raises), also only for kind
  `entry`; T10 and T11(d) release kind `baseline` with no interruption. So the two residues this plan names
  have no interruption test on the `baseline` branch: the worker's `state_transaction` seams never fire there
  (it has no `state_transaction` call), and its `crash_after_unlink` wrapper over `release_guard` (`S-gap`)
  does fire on kind `baseline` but no existing test runs it on that kind. The gap is crashed only on the
  entry branch, through a seam the test does not name.
- **The lock-order tests.** `TestGlobalLockOrderItem372h` derives the code's edges by AST and compares them
  with the declared list. It reads source shape, not a run; it was written for the release functions' own
  edges and is not changed here.
- **The three raise sites** of `AmendmentCheckpointActiveError` are in `workflow_state.py`:
  `open_plan_approval_journal` (the plan-approval open, "has an open amendment and a live checkpoint
  claim"), and the `IN_PROGRESS` arm and the claim arm of `request_plan_amendment`. The last two name the
  next step `_release_start_next_step`; the first does not, and must not: its amendment is already open, so a
  start released then does not lift the refusal the way it does before the amendment is requested.
  `TestRequestPlanAmendment` and `TestReleaseCheckpointStartCommand.test_c4_*` pin the other two and the
  class; nothing pins the first one's text.
- **`_assert_amendment_accepted`** (`TestReleaseCheckpointStartCommand`) builds its state with
  `TestRequestPlanAmendment._state_with_approved_plan`, whose work item has `CP1` `COMPLETE` and nothing
  else, so the released checkpoint's entry is never in the state the mutator reads.
- **Python 3.14** is the runtime here; the worker source runs under `sys.executable`.

## 3. Design decisions

### D-P1: a recording spy over the two function boundaries, no static analysis

`test_p1_*` runs inside `TestReleaseCheckpointStart` and patches, for the duration of a scenario,
`ws.owner_mutation` (a context manager that delegates to the real one and, once the real one has yielded,
marks the body as open until the body ends) and `ws.guard_mutation_lock` (a context manager that records
whether the body is open at the moment it is entered, then delegates). The properties asserted:

- **Non-vacuous:** the lock was entered **outside** the body **exactly three** times, and the spy names them
  (the probe `guard_holder_is_running`, the guard's acquire, the guard's release), so the spy is wired to the
  names the engine calls and a spy that misses the release-time edge fails here;
- **The pin:** it was entered **zero** times inside the body.

Scenarios, one subtest each, so every exit of the body is covered: a kind `entry` success, a kind `baseline`
success, a failed unlink (`_UnlinkFails`), a refusal inside the `restore` mutator (a commit carrying the
checkpoint's trailer since the start), and the **re-read refusal** (`CheckpointOwnershipUnavailableError`,
"claim or guard changed after ... entry was restored", raised before the unlink), reached in-process the way
T8(b) reaches it: `state_transaction` patched with a `write_then_change` wrapper that, after the real write,
rotates the claim (or rewrites the guard). A reachability proof by AST would cover branches no scenario runs,
and is not chosen: it would duplicate the call-graph walk of `TestGlobalLockOrderItem372h`, and the five
scenarios exercise every statement of the body (the statements after the re-read refusal run in the
success scenarios; the refusal branch itself runs in the fifth). The spy fails by name (`inside`), which is the readable
failure the issue asks for.

### D-P2: named seams, installed by the test, over existing function boundaries

The seams are **test-only** and sit at boundaries that exist in the module today:

| Seam | Over | Fires | Installed in |
| --- | --- | --- | --- |
| `S-write` (exists) | `ws.state_transaction` | before and after the restore write; kind `entry` only | the worker (`crash_before_write`, `crash_after_write`) |
| `S-unlink` (new in the worker; exists in-process as `_UnlinkFails`) | `ws.claim_path`, returning a `Path` subclass whose `unlink` is the injection point | at the engine's one `unlink` of the claim; `resolve_claim`'s reads of the same path and the guard release are unaffected | the worker (`crash_at_unlink`) and the test (`_UnlinkFails`) |
| `S-gap` (exists; named here) | `ws.release_guard` | after the claim unlink and before the guard is released (the only call between the two); both kinds | the worker (`crash_after_unlink`) |

The worker source (`_RELEASE_START_WORKER_SOURCE`, a constant of the test module) gains the `crash_at_unlink`
mode: it patches `ws.claim_path` to return a `Path` subclass whose `unlink` calls `os._exit(0)` in that mode
and delegates otherwise. Every other mode behaves as before. A crash is `os._exit`: no cleanup, the kernel
drops the holder lock, which is the residue a killed process leaves.

Tests, in `TestReleaseCheckpointStart`, each as subtests over an undemoted baseline (the checkpoint absent
from `HEAD`) and a demoted one (the `NEEDS_REVALIDATION` entry `HEAD` records), all with `window=False`
(kind `baseline`):

- **`test_p2_the_entry_absent_branch_writes_no_state`:** a release of kind `baseline` calls
  `state_transaction` zero times (a counting spy over the real function) and leaves the state file
  byte-identical; the claim is gone. It pins why `S-write` cannot fire here, and keeps the other P2 tests
  meaningful.
- **`test_p2_a_crash_at_the_unlink_of_the_entry_absent_branch`** (`S-unlink`): residue asserted exactly:
  state bytes unchanged, the claim present, a guard published with no live holder (the probe answers
  `False`); the next call completes (`_released`).
- **`test_p2_a_crash_in_the_gap_after_the_unlink_of_the_entry_absent_branch`** (`S-gap`): state bytes
  unchanged, **no** claim, a leftover guard with no holder; the next call refuses
  `CheckpointNotInProgressLocallyError` ("nothing to release") and changes nothing; the leftover is
  reclaimable by a fresh `acquire_guard`, as in T4's third case.
- **`test_p2_a_failed_unlink_of_the_entry_absent_branch`** (`S-unlink`, T7's analogue): the call raises
  `CheckpointOwnershipUnavailableError` ("claim was not unlinked"), the state is byte-identical, the claim
  stays, the guard is released; the next call completes.

The entry-branch counterpart of the gap is T4's "after the unlink" subtest; it is cited in the new tests'
docstrings and not duplicated.

### D-P3: the text of the plan-approval raise

`test_the_journal_refusal_names_no_release_command`, in `TestAmendmentResolutionReservation` beside
`test_the_journal_refuses_to_open_over_a_live_claim_on_an_open_amendment` (same fixture): opening the
journal over an open amendment with a live claim raises `AmendmentCheckpointActiveError`; the message is the
plan-approval raise's (it names the open transaction), and contains neither `/release-checkpoint-start` nor
`release-checkpoint-start`. No second `AmendmentCheckpointActiveError` raise is added or changed.

### D-P4: the `IN_PROGRESS` arm over the real entry, before and after a release

`test_p4_*`, in `TestReleaseCheckpointStartCommand` beside C5, over an undemoted and a demoted start: after
`_start`, build the amendment state from `_state_with_approved_plan` and **overlay the real on-disk
`checkpoints` and `current_checkpoint_id` of the work item** (the entry the release will act on). The overlay
**replaces** the helper's `checkpoints` map wholesale (it does not merge into it), so the helper's `CP1`
`COMPLETE` entry is dropped and the accepted/refused outcome is decided only by the on-disk entry; it also
sets `current_checkpoint_id` and `last_completed_checkpoint_id` to the on-disk work item's values, so no
leftover helper pointer to `CP1` survives. Then:

- **Before** the release, `request_plan_amendment` raises `AmendmentCheckpointActiveError` **from the entry
  arm** (the message says the checkpoint is `IN_PROGRESS`, not that a claim is outstanding) and names
  `/release-checkpoint-start wi CP`. The arm is identified by its message so a regression that removes the
  entry arm and leaves the claim arm cannot pass.
- After the real release (`_plain_release`), the same overlay over the **post-release** on-disk entry
  (absent, or equal to the demoted entry `HEAD` records) is accepted: the new state's phase is
  `AMENDING_PLAN`, and the entry the state carries is not `IN_PROGRESS`.

### D-Evidence: every pin shown red against its own mutant

Each new test is run against a scratch copy that carries **one** mutant. A scratch script (kept in `$TMPDIR`,
not shipped and not committed) copies `payload/` to a fresh directory per mutant, applies one text
substitution to the copied `scripts/workflow_state.py` (it fails unless the old text occurs exactly once),
and runs the named tests from the copy's `scripts/` directory with `python3 -B -m unittest`. A control run on
an unmutated copy passes first. The mutants:

| Mutant | Substitution (in the copy of `workflow_state.py`) | Test that must fail |
| --- | --- | --- |
| M1a | in `release_checkpoint_start`'s body, a call `guard_holder_is_running(repo_root, work_item_id)` before the claim re-read | `test_p1_*` |
| M1b | the guard re-read `read_guard(...)` wrapped in `with guard_mutation_lock(...)` | `test_p1_*` |
| M1c | a guard re-read under `guard_mutation_lock`, placed only in the re-read refusal branch, before its `raise` | `test_p1_*` (the fifth scenario only) |
| M2 | the engine's non-`entry` branch calls `state_transaction(repo_root, lambda s: s)` | `test_p2_the_entry_absent_branch_writes_no_state` |
| M3 | the claim unlink moved out of the `owner_mutation` window (done after the guard is released) | both `test_p2_a_crash_*` tests |
| M4 | the unlink's `except OSError` swallows the error | `test_p2_a_failed_unlink_*` |
| M5 | the third raise's message gains `_release_start_next_step(...)` | `test_the_journal_refusal_names_no_release_command` |
| M6 | the `IN_PROGRESS` arm of `request_plan_amendment` disabled (`if False and in_progress_ids`) | `test_p4_*` |
| M7 | the release's entry restore skipped (`if kind == "entry"` becomes `if False`) | `test_p4_*` |

Each result is recorded in `docs/ai-workflow/INTERLEAVING_PINS_EVIDENCE.md` with its exact command line **and
the exact old text and new text of its substitution**, because the scratch script that holds them is neither
shipped nor committed and functional flow f2 re-applies the recorded substitution (written at CP1; it is
excluded at the plan stage, so it cannot stale the plan approval, and **protected at the implementation
stage**, so technical approval binds the evidence the mutants are judged by, as
`CONFORMANCE_SHARDING_EVIDENCE.md` is; the commit message of CP1 repeats its summary and the implementation
bundle's `TEST_RESULTS.md` carries it). The file
also records the exact commands of the other gates and the orphan-wrapper reports. Whether
`TestGlobalLockOrderItem372h` independently fails M1a and M1b is recorded as information, not as a gate.

### D-Orphan: no process left behind, the Manager's orphan rule

The new tests start a worker only through `_run_worker`, whose `addCleanup(self._reap, proc)` kills and
waits a survivor, and the crash modes exit by themselves; `_crash_in` waits for the exit (status 0) inside
the test, so a worker is reaped before the test returns. P1, P3 and P4 start no process. The new tests, and
then the whole `workflow_state_test.py` chunk, run under the Manager's wrapper
(`tests/parallel/reaper.py` of the Manager checkout, a child subreaper that records every re-parented
process), from the staged fixture; the reports must list no orphan beyond Git's own detached maintenance.
No test uses a sleep as synchronisation: a blocking read of the worker's stdout is the synchronisation, as
in the existing tests.

### D-Release: 2.19.1, `fix:`

`manifest.json` `workflow_version` 2.19.1. The shipped files that change, and so the records that move (each
with its `sha256`, `size` and a `interleaving-pins (workflow-2.19.1)` sentence that is true of **that**
file, read against `git diff e8aff0a..HEAD -- <file>`):

- `payload/scripts/workflow_state_test.py`: the new tests and the worker mode (the sentence says exactly
  that);
- `payload/scripts/workflow_protocol.py`: `WORKFLOW_RELEASE` becomes 2.19.1 and nothing else;
- `payload/scripts/workflow_protocol_test.py`: the two pinned assertions of the release constant;
- `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`: the tested-releases list, the envelope example's
  `workflow_release` and the protocol note's list of releases that keep protocol 1.5; the protocol version
  stays.

No artifact record is added or removed (counts stay 80 and 6). `manager.conformance.suites` are **measured,
never typed**: only `workflow_state_test.py`'s digest, size and count move. `min_manager_version` stays
1.13.0, equal to the CI pin in `tools/release/manager-pin.json`. The detector vocabulary is untouched
(`signals` stays empty).

**Downgrade posture.** An older release reads everything 2.19.1 writes, because 2.19.1 writes nothing new:
no production code, state key, phase, trailer, commit shape, guard-body key, protocol field or refusal
class changes, only the shipped test suites and the release constant. `workflow-manager update` back to
2.19.0 (minimum Manager 1.13.0) restores the previous test suites and the constant `WORKFLOW_RELEASE`
2.19.0 that the protocol envelope reports as `workflow_release`. The 2.19.0 guidance still applies: finish
an interrupted checkpoint-start release before a move back below 2.19.0, and the 2.14.0 correction of 2.18.4
applies unchanged.

**Documents.** `docs/release-history.md` gets the 2.19.1 row (it **closes nothing**: it references #97
(items 4 and 5) and #100 (the pins) as partly done, names the four pins, says no behaviour changes, and
gives the way back) and its "Last checked with" line. `docs/CONCURRENCY_INVARIANTS.md`: the
checkpoint-start release row's tests cell names the new pins (its other cells do not change: no primitive,
lock order, residue or route changes), and "Last checked with: Workflow 2.19.1". `tools/release/release_test.py`:
a 2.19.1 release class (version, constant, counts (80, 6), the changed records' sentences, the posture and
history needles); the 2.19.0 class keeps what stays true of that release and no longer pins the current
version, constant, counts or posture. `docs/RELEASING.md` changes only if a count it states changes
(none is expected). No internal milestone id appears on a `docs/*.md` page, and no list of governing
versions is written in a managed document.

### D-Staging: scratch staging for CP1 (the command plan's procedure)

CP1 changes a shipped file whose digest, size and measured suite count `manifest.json` records only at CP2.
CP1 therefore verifies in a disposable clone under `$TMPDIR`: a scratch script recomputes `sha256` and
`size` of every `artifacts` record whose file differs from its record, measures and rewrites
`manager.conformance.suites` by the discovery `release.py manager-block --release-dir <scratch> --write`
uses, commits it in the clone, and runs the "Verification commands" blocks from there. No rationale is
touched in the scratch, and the report says the staging was adjusted.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
| --- | --- | --- |
| OD-1 | The version | **Patch 2.19.1, `fix:`**: shipped suites change, behaviour does not. |
| OD-2 | P1: dynamic spy or AST reachability | **The spy** over five scenarios (D-P1): it fails readably and does not duplicate the existing graph arm. |
| OD-3 | Where the evidence lives | **A companion file, excluded at the plan stage and protected at the implementation stage** (D-Evidence): the plan itself is plan-protected, so evidence written into it after approval would stale the approval, while technical approval must bind the evidence. |
| OD-4 | Whether the concurrency page changes | **Its tests cell only**, to name the pins; every other cell stays true. |
| OD-5 | The manager CI pin | **No change** (1.13.0 equals `min_manager_version`). |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does not exist in
this repository's release source).

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The four pins and their evidence | - | 2 | 1 |
| CP2 | Release 2.19.1 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The four pins and their evidence

**Files:** `payload/scripts/workflow_state_test.py`, `docs/ai-workflow/INTERLEAVING_PINS_EVIDENCE.md`.

- **Tests first, shown red against the mutants** (D-Evidence): write the seven new tests and the worker mode;
  run them unmutated (they pass: they pin existing behaviour); then run each against its mutant (M1a to M7,
  including M1c) and record the failing test ids. **Done:** the evidence file lists every mutant, its exact
  command line, its exact old and new substitution text and the failing tests, and a control run that
  passes.
- **The seams** (D-P2): the `crash_at_unlink` worker mode and the four P2 tests, over kind `baseline`
  undemoted and demoted. **Done:** the worker's other modes behave as before (T4, T5, T6 and the command
  class pass unchanged).
- **The pins** (D-P1, D-P3, D-P4): `test_p1_*` in `TestReleaseCheckpointStart`;
  `test_the_journal_refusal_names_no_release_command` in `TestAmendmentResolutionReservation`; `test_p4_*`
  in `TestReleaseCheckpointStartCommand`. **Done:** each fails on its mutant and passes unmutated.
- **No production change:** `git diff e8aff0a -- payload/scripts/workflow_state.py` is empty; no lock,
  guard, claim, `os.link` or `flock` site is added; `TestGlobalLockOrderItem372h` passes unedited.
- `docs/ROADMAP.md` row 26a is `Current` from this plan and this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites, the new tests and then the whole
`workflow_state_test.py` chunk under the Manager's orphan wrapper (no orphan beyond Git's own detached
maintenance), the `tools/release` and `tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.19.1

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`,
`docs/release-history.md`, `docs/CONCURRENCY_INVARIANTS.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.19.1 with its two pinned assertions in `workflow_protocol_test.py` and the
  matching `ORCHESTRATION_PROTOCOL.md` edits (tested releases list, envelope example, protocol note); the
  protocol version stays.
- `manifest.json` 2.19.1 (D-Release): `workflow_version`; `sha256` and `size` of every changed record; an
  accurate `interleaving-pins (workflow-2.19.1)` sentence on **each** changed record, true of THAT file
  and read against `git diff e8aff0a..HEAD -- <file>`; the `manager` block's posture rewritten for the
  patch and `conformance.suites` measured by `release.py manager-block --release-dir <scratch> --write`
  from a staging of CP2's own content; `min_manager_version` equal to the CI pin.
- `docs/release-history.md`: the 2.19.1 row (references #97 and #100, closes nothing) and the "Last checked
  with" line; `docs/CONCURRENCY_INVARIANTS.md`: the tests cell of the release-window row and its "Last
  checked with" line.
- `tools/release/release_test.py`: a 2.19.1 release class; the 2.19.0 class keeps what stays true of it.
- `docs/ROADMAP.md` is not written by this checkpoint: row 26a becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture;
`release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #97 item 4 | The guard re-read takes no (6) inside the body | CP1 | D-P1, M1a, M1b, M1c |
| #97 item 5 | The seams for the entry-absent branch and the gap, with tests (T4, T7) | CP1 | D-P2, M2 to M4 |
| #100, third raise | The plan-approval raise names no release command | CP1 | D-P3, M5 |
| #100, the entry arm | `request_plan_amendment`'s `IN_PROGRESS` arm over the real entry after a release | CP1 | D-P4, M6, M7 |
| #100, wording and messages | `COMMAND_FILES.md`, the `released` bullet, the invariants recovery cell, the downgrade note, the operator reference, the first raise's checkpoint | **not here** | roadmap row 26b |
| Release | 2.19.1 bookkeeping; closes nothing, references #97 and #100 | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/interleaving-pins-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its plan-stage
protected paths, and self-review checked that every path named in a Files paragraph, and every other path
this plan names (`docs/ROADMAP.md`, `docs/RELEASING.md`, `docs/release-history.md`,
`docs/CONCURRENCY_INVARIANTS.md`), is classified at both stages and that every deliverable is protected at
the implementation stage. The evidence file `docs/ai-workflow/INTERLEAVING_PINS_EVIDENCE.md` is excluded at
the plan stage and listed in `implementation_stage.protected_paths` (before the excluded
`docs/ai-workflow/` prefix is consulted), the precedent of `conformance-sharding-artifacts.json`.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands", and the manifest key is
`workflow_version`. Each flow names its workspace.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`), from `$TMPDIR/fixture/scripts` | the new tests pass: `python3 -B -m unittest -v workflow_state_test.TestReleaseCheckpointStart workflow_state_test.TestReleaseCheckpointStartCommand workflow_state_test.TestAmendmentResolutionReservation` |
| f2 | a scratch copy of `payload/` per mutant | each of M1a to M7, applied by the evidence file's recorded substitution, makes exactly the named test or tests fail, and the control run passes |
| f3 | the staged conformance fixture | the `workflow_state_test.py` chunk under the Manager's orphan wrapper reports no orphan beyond Git's own detached maintenance |
| f4 | the staged conformance fixture | the nine suites from the manifest's `manager.conformance.suites` list |
| f5 | the checkout (zlib-ng environment for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, and `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f6 | the checkout | `git diff e8aff0a -- payload/scripts/workflow_state.py` is empty; the 2.19.1 history row, the invariants page and the manifest agree on the version and name no issue as closed |
