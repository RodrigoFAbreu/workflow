# W43: Workflow 2.29.0 — the floor commit as one plain command (Revision 5)

- **Work item:** `acceptance-floor-commit` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-05 (passed on from the RepFlow lane):
  RodrigoFAbreu/workflow#148, the last Python call; `docs/ROADMAP.md` row 38 (`Next`, becomes `Current` with this plan,
  `Done` at acceptance). The earlier parts are rows 35 to 37 (`docs/milestones/completed/ACCEPTANCE_PLAIN_COMMAND_PLAN.md`,
  `ACCEPTANCE_COMPLETION_COMMAND_PLAN.md`, `ACCEPTANCE_FINDINGS_FLOOR_PLAN.md`); the last one measured the recovery questions below.
- **Branch:** `milestone/acceptance-floor-commit`
- **Base commit:** `d6e6cb07f1c97837dd98a43cb2f3c198dade47dc` (main after #163: release source and own installation are 2.28.0;
  automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 4 (rounds 1 to 3 of the local review applied: `LOCAL-R1-001` to `-006`, `LOCAL-R2-001` to `-005`, `LOCAL-R3-001` to `-004`, sections 7 to 9). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1: the investigation (before any design)

Measured on scratch repositories built by hand with the base's `payload/scripts` (a probe kept outside the repository, not shipped).

### 0a. The function

`commit_gate_policy_floor(repo_root, *, now)` (`payload/scripts/workflow_state.py`). **Callers:** none in code. `satisfy-gate.md` cites it
twice (step 5 of "The policy evaluation, then the stage's transaction" and, by reference, step 5 of the acceptance stage; "Plain commands first"
calls it "the one Python call that remains"); `workflow_gate_policy.py` names it in a docstring; tests. `workflow_protocol.py` never calls it, so the
Controller never runs it.

| | |
| --- | --- |
| Reads | the state file (`{}` when absent), the policy file, the commit history (`record_gate_policy_floor`) |
| Order inside | (1) `record_gate_policy_floor` on the file's state: the same object back means nothing stricter, return `None`; (2) the index must hold nothing but the state file (`DirtyIndexBeforeStagingError`); (3) one `state_transaction` writes the top-level `gate_policy_floor`; (4) top-level-scoped staging; (5) nothing staged: `None`; (6) one commit, subject `chore: record gate policy floor <12>`, final paragraph `Workflow-Gate-Policy-Floor: <digest>`; (7) `validate_gate_policy_floor_commit`; (8) `gate_policy.clear_caches()` |
| Returns | the commit sha, or `None` |
| Writes | the state file (whole file, canonical form), `.ai-review/runtime/WORKFLOW_STATE.lock`, the index, one commit. No other file, no ref but the branch |

### 0b. Re-run after a stop at each step (all measured)

| Stop | State after | A second call of the function |
| --- | --- | --- |
| nothing stricter observed (step 1) | untouched | `None`, nothing written |
| a staged foreign path (step 2) | untouched, no commit | `DirtyIndexBeforeStagingError` (the probe stopped there) |
| after the state write, before staging (step 3-4) | `M WORKFLOW_STATE.json`, floor in the file, **not** in `HEAD` | **`None`, `HEAD` unmoved, file still dirty**: the floor is already the virtual one, so step 1 sees nothing to record (a floor waiting is invisible) |
| after staging, before the commit (step 4-6) | `M ` staged, no commit | **`None`**, same reason; the staged floor stays staged |
| after the commit, before the validator (step 6-7) | the commit exists, tree clean | `None`; the validator never runs on it |
| the validator refuses (step 7) | the commit **exists** (nothing can take it back) | `None`; the refusal is not repeated |
| a directory with **no state file** and a stricter setting | — | **commits**: it creates a state file holding only `gate_policy_floor` and a valid floor commit (so the earlier note "returns `None` silently" holds only when nothing is stricter) |
| the completion commit **not yet made** (an uncommitted `MILESTONE_COMPLETE` edit in the state file) | — | **commits** the floor; the scoped staging leaves the item edit uncommitted. **The library does not enforce the order** |
| a corrupt state file | untouched | `CorruptJsonError` |

### 0c. The order the command text requires

`satisfy-gate.md`: the floor is step 5 of the acceptance stage, **after** step 4's completion commit (the commit that stages the completed state
file, the record paths and the documents). The flag therefore has no business before that commit: the library lets it run (0b), so **the flag
must refuse**. The test it can apply: the item's stored phase is `MILESTONE_COMPLETE` and `HEAD`'s copy of the item equals the working copy.

### 0d. Flag or protocol operation, and what the evidence forces

A flag, as rows 35 to 37: the Controller launches `/satisfy-gate acceptance {id}` with a worker and never runs the floor (0a), so a
`workflow_protocol.py` operation would be protocol `1.6` and a Controller change for no consumer. **Nothing here forces protocol `1.6`: it stays
`1.5`, no Controller change.**

### 0e. Does the investigation prove a defect in the function?

The re-run blindness (0b, rows 3 and 4) is a gap the function has always had (and its `None` is not proof of a pending, valid floor: `record_gate_policy_floor` also answers the same object when provenance has failed, when `_virtual_floor` is `None`, and when the working floor's `policy` matches but the rest of the record is damaged, because `_floor_resolved` reads `policy` alone; measured in round 1, `LOCAL-R1-001`); its text says only what to call, and a worker never re-ran it. It
does not corrupt anything, and every fix inside the function would change what the plan-stage and implementation-stage callers see. **No defect
is claimed; `commit_gate_policy_floor` does not change, not one line** (a test pins its source). The recovery lives in the flag, through one new
function beside it (D-Recovery).

## 1. Goal, release, scope

A headless worker records the floor with **one plain command**, `python3 scripts/workflow_state.py --commit-gate-policy-floor <work-item-id>`, with
no inline Python, in `/satisfy-gate acceptance` step 5. After 2.29.0 the acceptance stage contains no inline Python call. The plan-stage and
implementation-stage floors (step 5 of "The policy evaluation, then the stage's transaction") keep the Python description: the flag's order test is the
acceptance one.

- **Release: Workflow 2.29.0, a `feat:` minor** (a new command surface a worker is told to run). `manifest.json` `workflow_version` 2.28.0 to 2.29.0.
- **Out of scope:** the library's phase gap (`complete_work_item`; wf#158 item 1, the next row); the optional `next-action` evidence line of #148; any
  change to the gate's requirements or to the floor's semantics.

## 2. Design decisions

### D-Flag: the interface

`python3 scripts/workflow_state.py --commit-gate-policy-floor <work-item-id>` (not under `python3 -I`: the script imports its neighbours). A sixth member
of the mutually exclusive group, dispatched after `parse_args` and **before** the shared `git rev-parse`, with `is not None` (an empty id is an
`UnknownWorkItem`). The id is used for the order test only; the floor is repository-wide, as in the function. No other option. The argparse
description gains one sentence.

### D-Order: refuse before anything is written

After the shared context (`_acceptance_cli_context`: state present, an object, the id known) and before any call that writes:
`FloorCommitPreflightError` (new class, `code`): `work_item_not_complete` when the stored phase is not `MILESTONE_COMPLETE`;
`completion_not_committed` when `HEAD`'s copy of the item (read from `HEAD:docs/ai-workflow/WORKFLOW_STATE.json`, absent when there is no `HEAD`
or no such item) differs from the working copy. Foreign work items' edits do not matter (the scoped staging already leaves them out).
This also refuses the directory without a state file (`StateMissing`, 0b) before the function can create one.

### D-Recovery: a floor waiting in the file is committed by the flag, after the sibling has proved it

The flag calls `commit_gate_policy_floor` first. On `None` it calls `commit_pending_gate_policy_floor(repo_root)`, new, beside it, in the library. A `None` proves
nothing about the working floor (0e), so **the sibling proves what it commits, before it stages anything**, reusing the library's own checks, in this order, reading
the state file and the history once and writing nothing:

1. no `gate_policy_floor` in the working state: nothing waiting, return `None`;
2. `verify_gate_policy_provenance(repo_root)["ok"]` is true, else `FloorRecoveryRefusedError` with `code` `floor_provenance_failed` (a failed provenance records nothing, and
   a floor commit on a broken chain is not repaired by another commit);
3. `floor_record_errors(working_floor)` is empty, else `floor_record_invalid` (a damaged `digest`, a missing key, a malformed `policy`);
4. the working floor's `policy` equals what `_virtual_floor` returns when it is **recomputed** (not inferred from the earlier `None`), else `floor_not_virtual`;
5. the working floor's `policy` is no looser than `HEAD`'s effective floor (`_effective_floor_of(adoption, committed)`: the committed floor, else the adopted policy, else the
   default; `stricter(head_floor, working) == working`), else `floor_looser_than_head`;
6. the working floor's `policy` differs from `HEAD`'s committed floor policy (absent counts as different); equal means nothing new is waiting (for example only `recorded_at`
   or `observed` was touched, `LOCAL-R1-005`): return `None`, nothing written, so no second commit for no new setting.

Every refusal raises before the index check and before staging (F9 pins the order against the index check for **each** of the preconditions 2 to 5, cases (e), (i), (j), (k), and for the two `None` answers of preconditions 1 and 6, cases (l), (m): with a foreign path staged the answer is the precondition's own, never `DirtyIndexBeforeStagingError`, and the foreign path stays staged; `LOCAL-R3-001`; the staging itself writes nothing a refusal could leave): nothing written, nothing staged, `HEAD`, refs and index identical, and the provenance unchanged. Then the
function's own steps 2, 4, 5, 6, 7 and 8 (index check, top-level-scoped staging, nothing staged: `None`, the same subject and `Workflow-Gate-Policy-Floor` trailer, the validator).
It writes no state and takes no lock. The answer carries `recovered: true` when this branch made the commit. **Why it is safe:** it commits only a floor it has just proved
valid, virtual, no looser than `HEAD`'s and new; the validator then checks the commit as for a fresh one, so the validator is the second line, no longer the only one (before this
revision the first check of content ran after a commit that cannot be taken back). A completed floor (nothing pending) answers `commit: null` on a healthy chain, so a re-run after a success is a
no-op, **also with a foreign path staged**: exit 0, `{"commit": null, "recovered": false}`, the foreign path still staged (the index check comes after precondition 6, F9 (l), (m)). **A hand-written floor equal to the base** (no floor in `HEAD`, nothing stricter, a valid working floor holding the default policy) passes every precondition, since precondition 6 treats an absent committed floor as different, and is committed once with `recovered: true`: left as it is on purpose (`LOCAL-R3-002`), because nothing is damaged, only a hand edit reaches it, and the validator accepts the commit; comparing with `_effective_floor_of` would change what "new" means for the written-by-the-function case. With a **failed provenance** and nothing waiting (the working floor equals `HEAD`'s) precondition 2 runs before precondition 6 and the flag refuses with `floor_provenance_failed`, exit 1, `commit` null, `state_changed` false, where the base's Python call answers `None` (`LOCAL-R2-004`): left as it is on purpose, since the failure is real and nothing is written, and F9 case (f) pins it; a re-run after a real validator refusal therefore gets this refusal, one more reason for D-Output's "do not run it again". A stop after staging with a foreign item's residue also in the state file: the re-run refuses with `DirtyIndexBeforeStagingError` (`stage_scoped_state` refuses an already-staged
path); the rule of D-Output names the step (`git restore --staged <state file>`, then run it again), and F5 pins the refusal (`LOCAL-R1-004`, the second option the finding offers; the
sibling `commit_pending_applying_review_feedback_entry` accepts its own interrupted staging instead, a different design that this item does not copy). The new function duplicates six lines
of the commit half on purpose: refactoring the old function is what 0e rules out; a test pins subject, trailer and validator parity.

### D-Output: the answer

Success: exit 0 and exactly `{"commit": <sha>|null, "recovered": <bool>}` (`sort_keys=True`, `indent=2`, one trailing newline); `null` means no stricter
setting is waiting. Failure or any exception: exit 1 and one object `{"error": <class>, "message": str(exc), "commit": <sha>|null, "state_changed": bool}`
plus `"code"` when the exception has a string `code`. `commit` is the new `HEAD` when it moved during the call, else `null`; `state_changed` compares the
state file's digest before the call with the one after the failure (measured, never assumed). The worker's rule, in the text, covers the three cases: **`commit: null`**: nothing was committed; fix the cause the message names (for example unstage the foreign path) and run it again, and if a floor was already waiting in the state file (`state_changed` shows whether this call wrote it) the re-run commits it (`recovered: true`), so never commit the file by hand; **`commit` set**: the floor commit exists and a later check refused it, so the approval stands, the floor stays virtual, report the commit and the error, and do not run it again to repair it. `state_changed: true` with `commit: null` means this call wrote the floor into the file before it stopped. The sibling's refusals (D-Recovery) are errors of class `FloorRecoveryRefusedError` with `code` `floor_provenance_failed`, `floor_record_invalid`, `floor_not_virtual` or `floor_looser_than_head`,
`commit` null and `state_changed` false: the working floor is not committed by hand either; the way out is the one `GATE_POLICY.md` names for the cause (a damaged record is restored from `HEAD`, a failed
provenance by a new `/adopt-gate-policy` commit). A `DirtyIndexBeforeStagingError` after an interrupted staging (the state file staged next to a foreign path) is cleared with `git restore --staged
docs/ai-workflow/WORKFLOW_STATE.json` and the same command again. Errors before the call are the other flags' own objects (`StateMissing`,
`CorruptJsonError`, `StateMalformed`, `UnknownWorkItem`, outside Git) with `commit: null`, `state_changed: false`. Exit 2 stays argparse. Every
existing flag's output and exit code stays byte-identical.

### D-Discipline: what it touches

The flag takes no lock of its own; the function's `state_transaction` takes the lock when it writes. It calls no forge and runs no `git` but the
function's own and a read of `HEAD`. `now` is `_utc_now_stamp()`; tests pass a seam. A crash is `KeyboardInterrupt`/a kill, not an exception: the recovery
(D-Recovery) is what makes the re-run complete it. The one residual, said in the report text: a stop between the commit and the validator leaves a commit the
validator never saw (0b); `workflow-manager verify` and the `gate_policy` check still read it.

### D-Command: the command text

`satisfy-gate.md` "Plain commands first": after the findings-record paragraph, one paragraph for the floor with the line
`python3 scripts/workflow_state.py --commit-gate-policy-floor <work-item-id>` alone on its line, "run it **after** step 4's completion commit, and only when
the evaluation observed a setting stricter than `gate_policy_floor`" (a run that finds nothing prints `commit: null`, harmless), the answer, the error object
and the rule of D-Output, that it refuses before the completion commit (`work_item_not_complete`, `completion_not_committed`), and that it is not
run under `python3 -I`. **Two sentences change** (`LOCAL-R1-003`; `satisfy-gate.md` says it twice). (1) The sentence ending the completion-command paragraph (lines 210-211 of the base): `...steps 4 and 5 below stay the worker's own edits,
`git commit` and, for the floor, one Python call.` keeps its pinned clause `steps 4 and 5 below stay the worker's own edits` and replaces its ending: `...steps 4 and 5 below stay the worker's own edits,
`git commit` and, for the floor, the plain command below.` (2) The sentence ending the findings-record paragraph (lines 231-232): `The floor (step 5, `commit_gate_policy_floor`) is the one Python call that
remains.` is deleted, and the new floor paragraph follows that paragraph, ending: `The acceptance stage has no inline Python call; the plan-stage and implementation-stage floors keep the Python
description (`commit_gate_policy_floor`).` Neither new wording contains `until its own plain`. Step 5 of the acceptance stage names the flag. The floor sentences elsewhere and `state_writer: true` stay.

### D-Tests

All in `payload/scripts/workflow_gate_policy_test.py`, class `TestCommitFloorCommand` on `PolicyRepo` (an item `wi` at `MILESTONE_COMPLETE` committed, a stricter
policy file in the working tree), the CLI function in-process with the `now` seam; a subprocess only for the documented line. Each test states exact output.

- **F1 parity**: on a copy of the repository the Python call makes a commit; the flag's commit has the same changed path, subject, trailer and state bytes at
  `HEAD`; `{"commit": sha, "recovered": false}`.
- **F2 no-op**: nothing stricter: `{"commit": null, "recovered": false}`, tree, refs and index identical, no `.ai-review`; a second run after F1 is the same as before that run (tree outside `.ai-review`, refs and index unchanged; the first run created `.ai-review/runtime/WORKFLOW_STATE.lock`, so "no `.ai-review`" is not asserted for it, `LOCAL-R3-003`); a
  looser working-tree edit of a recorded floor leaves nothing pending and nothing committed (this case alone does not assert the opening identity sentence: the function rewrites the state file back to the committed floor and creates `.ai-review/runtime`, so it asserts `commit: null`, `HEAD` and refs unmoved, the index empty and the state file equal to `HEAD`'s, `LOCAL-R2-005`); a committed floor with only `recorded_at` (and, separately, only `observed`) edited in the
  working file answers `commit: null`, no second commit (`LOCAL-R1-005`).
- **F3 order**: each of `IMPLEMENTING` and `AWAITING_FUNCTIONAL_REVIEW` (`work_item_not_complete`) and an uncommitted completion edit
  (`completion_not_committed`), **with a stricter policy present** (so the function would commit: shown on a copy): exit 1, tree outside `.git`, refs, index identical,
  `commit` null, `state_changed` false.
- **F4 other refusals, no write**: a staged foreign path (`DirtyIndexBeforeStagingError`), also in the pending case of F5; no state file; corrupt state; `[]`; `{}`;
  unknown and empty id; outside Git. Same identity proof, one test each.
- **F5 recovery**: for a stop after the state write and a stop after staging (seams in `_stage_state_for_commit` and the `git commit` call), the flag run afterwards
  commits the floor, `recovered: true`, the commit passes the validator and parity with F1, the state file clean; a run once more is `commit: null`; a stop after the commit and
  before the validator: `commit: null`, no second commit; a stop after staging with a foreign item's uncommitted edit also in the state file: `DirtyIndexBeforeStagingError` (the pinned refusal, `LOCAL-R1-004`),
  and after `git restore --staged` on the state file the next run commits the floor (`recovered: true`). An error with `commit` null and `state_changed` true is shown (a seam raises after the state write, the file changed); with a foreign path staged and a floor already waiting, `commit` null and `state_changed` false.
- **F9 the sibling proves before it stages** (`LOCAL-R1-001`, `LOCAL-R2-001`, `LOCAL-R2-002`, `LOCAL-R2-004`): the cases run through the flag, each with exit 1, the `code`, `commit` null, `state_changed` false, `HEAD`, refs, index and tree identical, no staged path
  (except (e)) and `verify_gate_policy_provenance` unchanged: (a) a healthy repository with a committed floor and a working floor of the same policy and a damaged `digest` (`floor_record_invalid`; the validator never runs);
  (b) no floor in `HEAD`, nothing stricter, a malformed floor record in the working file (`floor_record_invalid`); (c) provenance failed at `HEAD` (a malformed floor commit in the history) and a working floor set to
  the default policy, looser than a floor committed earlier (`floor_provenance_failed`, not exit 0); (d) a working floor with no `digest` (`floor_record_invalid`, no `KeyError`, nothing staged); **(e)** the damaged working floor of (a) **with a foreign path staged** (`x.md`):
  `floor_record_invalid`, not `DirtyIndexBeforeStagingError`, and `x.md` still staged, the index equal to its state before the call (a refusal that ran after the index check would answer the other class); **(f)** provenance failed at `HEAD` and the working floor equal to `HEAD`'s,
  nothing waiting: `floor_provenance_failed`, exit 1, nothing written (the case D-Recovery qualifies). **Each remaining precondition is pinned against the index check with `x.md` staged** (`LOCAL-R3-001`; each case: the answer is the precondition's own, `x.md` still staged, the index equal to its state before the call): **(i)** (c) plus `x.md` staged: `floor_provenance_failed` (precondition 2); **(j)** (g)'s direct call plus `x.md` staged: `floor_not_virtual` (precondition 4); **(k)** (h) plus `x.md` staged: `floor_looser_than_head` (precondition 5); **(l)** no floor in `HEAD`, nothing stricter observed (no policy file; the repository is `mk $c plain`, not fixture `ready`), no `gate_policy_floor` in the working file and `x.md` staged: exit 0, `{"commit": null, "recovered": false}`, `x.md` still staged (precondition 1; a floor removed or loosened in the working file, or a stricter policy file, with a foreign path staged gives the function's own `DirtyIndexBeforeStagingError`, since the function then has something to record and its index check answers before the sibling is reached, `LOCAL-R4-002`); **(m)** a committed floor, the working file differing from `HEAD`'s only in `recorded_at`, and `x.md` staged: exit 0, `commit` null, `recovered` false, `x.md` still staged, no second commit (precondition 6). In (g) and (h) the working floor differs from `HEAD`'s (a floor waiting in the file), so that a precondition moved after the staging would stage the state file and leave a trace; if it equalled `HEAD`'s, the staging would stage nothing and the mutant would leave none. Four cases need a seam ((g), (h), (j), (k); they belong to the tests, not to flow 11a, `LOCAL-R4-001`) because no repository state reaches them once the record is valid (a valid working floor is itself a candidate of `_virtual_floor`), and the seam must **reach the sibling** (`LOCAL-R2-001`):
  `commit_gate_policy_floor` and the sibling share `_virtual_floor` through `record_gate_policy_floor`, so a patch that makes the sibling see a non-virtual floor also makes the function record and commit it, and the flag never reaches the sibling. (g) `floor_not_virtual`: **`commit_pending_gate_policy_floor` is called directly** under the patch (`gate_policy._virtual_floor` returning a stricter policy than the working one), on a repository whose working floor is valid, so the function is not in the path; the assertions are the raise of `FloorRecoveryRefusedError` with `code` `floor_not_virtual`, nothing written, nothing staged and `HEAD`, refs, index and tree identical (the exit code and the error object belong to the flag and are not asserted there). (h) `floor_looser_than_head`: through the flag in the test (in-process, with the patch; (k) is the same case plus `x.md` staged and needs the same patch), `HEAD` given a floor stricter than the working one and `_virtual_floor` patched to return the working policy (the patched floor equals the working one, so the function answers `None` and the sibling is reached), with the full assertions of the other cases.
- **F6 refusal after the commit**: a validator that raises: exit 1, `commit` equal to the new `HEAD`, the error class and message, `state_changed` true, exactly one commit added.
- **F7 interface**: each of the five other flags with the new one exits 2; an empty id is `UnknownWorkItem`; the five existing flags print what they printed.
- **F8 the function is untouched**: the sha256 of `inspect.getsource(ws.commit_gate_policy_floor)` equals a literal recorded at the base; the flag calls it (spy), and
  calls `commit_pending_gate_policy_floor` only after a `None`.
- **R6 the command text**: `satisfy-gate.md` names the flag, the line alone, the rule of D-Output, both codes, "after step 4's completion commit", no `python3 -I`, the plan
  and implementation stages keep `commit_gate_policy_floor`, the existing pins stay; the documented line runs in a scratch repository and refuses an early item; **neither stale sentence survives** (`LOCAL-R1-003`): the text of "Plain commands first" and of the acceptance stage contains
neither `for the floor, one Python call` nor `is the one Python call that remains` nor the phrase `one Python call` at all, and does contain the two new wordings. **The one
  existing test that changes:** the 2.28.0 class's assertion that `commit_gate_policy_floor` "is the one Python call that remains" (`test_r6_the_command_texts_name_the_flag_and_state_the_boundaries`)
  now asserts the new closing sentence.

**Failure-only mutations**, each failing the named test, recorded on a scratch copy: m1 phase test dropped (F3); m2 `HEAD` equality dropped (F3); m3 order test after the
function (F3); m4 no state file not refused (F4); m5 recovery branch dropped (F5); m6 recovery without the index check (F4); m7 recovery commit without the trailer or with
another subject (F5); m8 `recovered` constant (F1, F5); m9 `commit` of the error constant `null` (F6); m10 `commit` always `HEAD` (F3); m11 `state_changed` constant (F5);
m12 an exception swallowed into a success (F4); m13 a refusal exits 0 (F3); m14 dispatch after the shared `git rev-parse` (F4, outside Git); m15 the flag outside the exclusive
group (F7); m16 an existing flag's output changed (F7); m17 one line of `commit_gate_policy_floor` edited (F8); m18 the text drops the flag or puts it before the completion commit (R6);
m19 recovery tried before the function (F2, a looser edit); m20 the provenance check of the sibling dropped (F9 c, f); m21 the record check dropped (F9 a, b, d, e); m22 the recomputed-virtual-floor comparison
dropped (F9 g, the direct call); m23 the no-looser-than-`HEAD` check dropped (F9 h); m24 the equal-to-`HEAD`'s-floor check dropped (F2, the `recorded_at` case); m25 any one precondition moved after the index check (a staged foreign path no longer gets the precondition's own answer: 4 on (j), 5 on (k) and 6 on (m) answer `DirtyIndexBeforeStagingError`, 2 on (i) answers `floor_not_virtual` and 3 on (e) answers exit 0 `commit: null`, because the later preconditions see the same state (`LOCAL-R4-003`): precondition 1 F9 l, 2 F9 i, 3 F9 e, 4 F9 j, 5 F9 k, 6 F9 m; each precondition moved separately fails its named case) or after the staging (F9 a to d, g, h: `HEAD`, refs
or index differ, with the working floor differing from `HEAD`'s in (g) and (h)); m26 the old "for the floor, one Python call" ending restored, and separately the old "is the one Python call that remains" sentence restored (R6, each).

### D-Docs

`docs/exit-codes.md`: three rows (0 `{commit, recovered}`; 1 the JSON error with `commit` and `state_changed`; 2 arguments) and the group count; no milestone id.
`docs/ROADMAP.md`: row 38 `Current` with its description narrowed to what the investigation found, `Done` at acceptance. A line for the next row (the library's phase gap) stays.

### D-Release

2.29.0, the procedure of the 2.28.0 plan (`docs/milestones/completed/ACCEPTANCE_FINDINGS_FLOOR_PLAN.md`, D-Release) with these differences. `manifest.json`: `workflow_version`; the
**six** changed records (`workflow_state.py`, `workflow_gate_policy_test.py`, `satisfy-gate.md`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`) take `sha256` and `size`; no file
added or removed; `conformance.suites` by `release.py manager-block --write`. `WORKFLOW_RELEASE` 2.29.0 with its pinned assertions; `tools/release/release_test.py` gets a 2.29.0 class and the
2.28.0 class (`release_test.py:3567`) gives up the current-release pins. `docs/release-history.md`: the 2.29.0 row (the way back to 2.28.0 only removes the flag and `commit_pending_gate_policy_floor`;
a floor commit it made is the function's own commit, nothing to undo). `ORCHESTRATION_PROTOCOL.md`: the release list and one sentence that 2.29.0 adds a flag that records the floor through the library
and is not a protocol operation (protocol stays `1.5`). **The Manager block's posture** is rewritten, the downgrade guidance carried over sentence for sentence (`workflow-manager update back to 2.28.0`, minimum
Manager 1.13.0), with the 2.28.0 guidance sentence kept and the closing sentence "The release tooling and the maintainer documents are not part of the installed release." kept. Each of the six
records' `rationale` carries `acceptance-floor-commit (workflow-2.29.0)`. The 2.29.0 class pins the needles (`2.29.0`, `2.28.0`, `--commit-gate-policy-floor`, `Orchestration Protocol stays 1.5`,
`not a protocol operation`, `workflow-manager update back to 2.28.0`, `WORKFLOW_RELEASE`, `removes the flag`, `/release-checkpoint-start`, `2.14.0`, the closing sentence), the `rationale` sentence, `CHANGED`
and the new suite counts.

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w43-tmp` (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging, and
the count handling of the lstat-errors plan): recompute `sha256` and `size` of every record whose file differs (none added), measure `conformance.suites` (only the `workflow_gate_policy_test.py`
count moves), commit in the clone, run the "Verification commands" of `docs/RELEASING.md`; the `tools/release` tests use
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`. **The one expected failure at CP1:** the 2.28.0 class pins
the `workflow_gate_policy_test.py` count; it fails once the measured count is written, is named at implementation, and is released in CP2 (stock `stage-conformance` is the proof there). The new tests run
again under the Manager's orphan rule (reaper).

## 3. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Reversible choices: **a flag, not a protocol operation** (0d); **the function stays untouched** and the recovery is a sibling (0e;
the owner may instead ask for a defect fix inside the function, which changes the plan-stage callers); **the flag refuses outside the acceptance order** (D-Order), so the plan-stage and
implementation-stage floors keep Python; **`recovered` in the answer** is the only field beyond the sha; **no re-validation of an old floor commit** on a re-run (0b, the residual).

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The floor flag, its recovery, tests, the command text and the pages | - | 3 | 1 |
| CP2 | Release 2.29.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The floor flag, its recovery, tests, the command text and the pages

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py`, `payload/.claude/commands/satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): F1 to F9 and R6 written and run red against the unedited tree; mutations m1 to m26 each fail the named test on a scratch copy and the results are recorded.
- **The change** (D-Flag, D-Order, D-Recovery, D-Output, D-Discipline): `FloorCommitPreflightError`, `FloorRecoveryRefusedError`, `_commit_gate_policy_floor_cli`, `commit_pending_gate_policy_floor` (with its six preconditions), the sixth group member and
  its dispatch; nothing else in the library. Every existing test passes unmodified except the one named in R6.
- **The command text and the pages** (D-Command, D-Docs). `check_docs.py` stays clean.
- **No other mechanism:** `git diff d6e6cb0 --stat -- payload` lists `workflow_state.py`, `workflow_gate_policy_test.py` and `satisfy-gate.md` only; the source of `commit_gate_policy_floor` is
  byte-identical to the base's; `docs/ROADMAP.md` carries row 38 `Current`.

**Verification:** the new tests as the suite runs them; D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block` (with
`--manager-releases`), `tools/release` (zlib-ng interpreter, no patch, no skip, with the **one expected failure** of D-Staging); the new tests again under the Manager's orphan rule (reaper).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.29.0 with its pinned assertions and the protocol-document edits (protocol stays `1.5`; D-Release).
- `manifest.json` 2.29.0 (D-Release): `workflow_version`, the six changed records, `conformance.suites`; the Manager block's posture and each record's `rationale` sentence.
- `docs/release-history.md`: the 2.29.0 row and its "Last checked with" line; that of `docs/exit-codes.md` moves too.
- `tools/release/release_test.py`: a 2.29.0 class pinning the posture, the `rationale` sentence, `CHANGED` and the suite counts; the 2.28.0 class gives up the current-release pins.

**Verification:** the new tests again; the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with
`--manager-releases`) and `tools/docs` are clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Every flow runs offline: no network, no real `gh`, no install, no socket, no zlib-ng, no Python 3.12 (the last two flows need the full
environment and say so); nothing runs against the real repository, its `.ai-review/` or the forge.** Setup, once, under `$TMPDIR`
(`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w43-tmp`): `base/` from `git archive d6e6cb07f1c97837dd98a43cb2f3c198dade47dc payload/scripts` and
`cand/` the working tree's `payload/scripts` copied to `$TMPDIR/cand/payload/scripts`, the two paths **absolute**:
`export BASE="$TMPDIR/base/payload/scripts" CAND="$TMPDIR/cand/payload/scripts"`. The fake `gh` (it only proves **no** forge call) lives outside `/tmp`, `/var/tmp`, `/dev/shm` and `$TMPDIR`, mode 0755:

```sh
export W43_BIN="$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w43-bin"
mkdir -p "$W43_BIN" && printf '#!/bin/sh\necho "gh called: $*" >> "$GH_LOG"\nexit 1\n' > "$W43_BIN/gh" && chmod 755 "$W43_BIN/gh"
export GH_LOG="$W43_BIN/gh.log"; : > "$GH_LOG"
mk() { # mk <dir> <case>: a scratch repository built by hand (the candidate's serializer writes the state)
  d="$1"; command rm -rf "$d"; mkdir -p "$d/docs/ai-workflow"; git -C "$d" init -q -b main .
  git -C "$d" config user.email t@t; git -C "$d" config user.name t; printf '.ai-review/\n__pycache__/\n' > "$d/.gitignore"
  CASE="$2" python3 -I - "$d" "$CAND" <<'PY'
import json, os, sys
sys.path.insert(0, sys.argv[2]); import workflow_state as ws
d, case = sys.argv[1], os.environ["CASE"]
phase = {"early": "IMPLEMENTING", "uncommitted": "IMPLEMENTING", "afr": "AWAITING_FUNCTIONAL_REVIEW"}.get(case, "MILESTONE_COMPLETE")
state = {"schema_version": 1, "active_work_item_id": None, "work_items": {"wi": {"work_item_id": "wi", "phase": phase}}}
if case != "nostate": open(d + "/docs/ai-workflow/WORKFLOW_STATE.json", "wb").write(ws._serialize_state(state))
if case == "corrupt": open(d + "/docs/ai-workflow/WORKFLOW_STATE.json", "w").write("{nope")
PY
  git -C "$d" add -A; git -C "$d" commit -q -m base
  if [ "$2" = uncommitted ]; then python3 -I - "$d" "$CAND" <<'PY'
import json, sys; sys.path.insert(0, sys.argv[2]); import workflow_state as ws
p = sys.argv[1] + "/docs/ai-workflow/WORKFLOW_STATE.json"; s = json.load(open(p)); s["work_items"]["wi"]["phase"] = "MILESTONE_COMPLETE"
open(p, "wb").write(ws._serialize_state(s))
PY
  fi
  if [ "$2" != plain ]; then printf '{"schema_version": 1, "gates": {"acceptance": {"human": true}}}' > "$d/docs/ai-workflow/GATE_POLICY.json"; fi  # a stricter setting, in the working tree
}
cpy() { # cpy <from> <to>: a copy that never lands inside a leftover of an earlier flow
  command rm -rf "$2"; command cp -a "$1" "$2"; }
snap() { (cd "$1" && { git rev-parse HEAD; git for-each-ref; git diff --cached --name-only; git status --porcelain; find . -path ./.git -prune -o -type f -print | sort |
  while read -r f; do sha256sum "$f"; done; }); }
py() { # py <scripts-dir> <repo>: the Python call; prints the sha or None
  (cd "$2" && python3 -I -c 'import sys; sys.path.insert(0, sys.argv[1]); import workflow_state as ws; from pathlib import Path
print(ws.commit_gate_policy_floor(Path("."), now="2026-11-06T10:00:00Z"))' "$1"); }
cli() { (cd "$2" && PATH="$W43_BIN:$PATH" python3 "$1/workflow_state.py" --commit-gate-policy-floor "${3-wi}"; echo "exit=$?"); }
refuse() { # refuse <repo>: the flag in-process with a validator that refuses after the commit landed
  (cd "$1" && python3 -I -c 'import sys; sys.path.insert(0, sys.argv[1]); import workflow_state as ws
def bad(*a, **k): raise ws.MalformedGatePolicyFloorCommitError("synthetic")
ws.validate_gate_policy_floor_commit = bad
raise SystemExit(ws._commit_gate_policy_floor_cli("wi", now=lambda: "2026-11-06T10:00:00Z"))' "$CAND"; echo "exit=$?"); }
crash() { # crash <repo> <state|stage|validate>: run the Python call and stop it at one step, as a kill would
  (cd "$1" && STOP="$2" python3 -I -c 'import os, sys; sys.path.insert(0, sys.argv[1]); import workflow_state as ws; from pathlib import Path
class Kill(BaseException): pass
def stop(*a, **k): raise Kill()
s = os.environ["STOP"]
if s == "state": ws._stage_state_for_commit = stop
if s == "validate": ws.validate_gate_policy_floor_commit = stop
if s == "stage":
    run = ws._run
    ws._run = lambda cmd, **k: stop() if cmd[:2] == ["git", "commit"] else run(cmd, **k)
try: ws.commit_gate_policy_floor(Path("."), now="2026-11-06T10:00:00Z")
except Kill: print("stopped at", s)' "$CAND"); }
```

Cases of `mk`: `ready` (item `MILESTONE_COMPLETE` committed, a stricter policy file in the working tree), `plain` (no policy file), `early` (`IMPLEMENTING`), `afr` (`AWAITING_FUNCTIONAL_REVIEW`), `uncommitted`
(`HEAD` holds `IMPLEMENTING`, the working file `MILESTONE_COMPLETE`), `nostate`, `corrupt`. The Python baseline always runs on a **copy** (`cpy`, which removes the target first, so a name used by an earlier flow is never copied into) so the two never share a tree. Every flow starts from its own `mk` where it says so.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `mk r ready`; `cpy r r2`; `cli $BASE r` (the base has no flag); `py $BASE r2`; `cli $CAND r` | base: exit 2 with argparse's "one of the arguments" refusal. Python on `r2` prints a sha. cand: exit 0, stdout exactly `{"commit": "<sha>", "recovered": false}` (indent 2, sorted keys); `git -C r show -s --format=%B HEAD` and `r2`'s are identical (subject `chore: record gate policy floor <12>`, final paragraph `Workflow-Gate-Policy-Floor: <digest>`), `git show HEAD:docs/ai-workflow/WORKFLOW_STATE.json` of the two differs only in the `recorded_at` line (the flag stamps the real clock; the tests use a seam and compare bytes), `git -C r diff-tree --name-only -r HEAD` is the state file alone, `git -C r status --porcelain` shows only the untracked policy file |
| 2 | on flow 1's `r`: `snap r > before`; `cli $CAND r`; `snap r > after`; then `mk r plain`, `snap`, `cli $CAND r`, `snap` | both runs: exit 0, `{"commit": null, "recovered": false}`, `diff` of the snapshots empty (nothing written, no commit, no `.ai-review` in the second); `py $BASE` on a copy of `plain` prints `None`; then, **on its own setup** (`mk r ready`; `cli $CAND r`, so a floor is committed and the file holds a `recorded_at` line: `grep -c recorded_at` prints 1), edit only that line of the working state file and run `cli $CAND r`: exit 0, `{"commit": null, "recovered": false}`, `HEAD` unmoved (`LOCAL-R1-005`) |
| 3 | `mk r early`, `mk q afr`, `mk s uncommitted`, each with `cpy` to a copy for `py $BASE`; `snap`; `cli $CAND`; `snap` | the Python baseline **commits** on each copy (no phase or order check). cand: exit 1 each, `{"code": "work_item_not_complete", "commit": null, "error": "FloorCommitPreflightError", "message": ..., "state_changed": false}` for `early` and `afr`, code `completion_not_committed` for `uncommitted`; snapshots identical, no `.ai-review` |
| 4 | `mk r ready`; `echo x > r/x.md; git -C r add x.md`; `snap r`; `cli $CAND r`; `snap r` | exit 1, `DirtyIndexBeforeStagingError` naming `x.md`, `commit` null, `state_changed` false, snapshots identical |
| 5 | `mk r ready`; `crash r state`; `git -C r status --porcelain`; `cpy r r2`; `py $CAND r2`; `cli $CAND r` | after the stop: ` M ...WORKFLOW_STATE.json`, no new commit. The Python call on `r2` prints `None` and leaves the file dirty (the measured blindness). cand: exit 0, `{"commit": "<sha>", "recovered": true}`, the state file is clean, `HEAD`'s subject and `Workflow-Gate-Policy-Floor` trailer as flow 1; a second `cli` prints `{"commit": null, "recovered": false}` |
| 6 | `mk r ready`; `crash r stage`; `git -C r status --porcelain`; `cli $CAND r` | after the stop: `M ` (staged), no new commit. cand: the same answer as flow 5 (`recovered: true`) and a commit of the state file alone. Then `mk r ready`; `crash r stage`; add a foreign item to the working state file with `ws._serialize_state` (the floor stays staged, the foreign edit is not); `cli $CAND r`: exit 1, `DirtyIndexBeforeStagingError`, `commit` null (`LOCAL-R1-004`); after `git -C r restore --staged docs/ai-workflow/WORKFLOW_STATE.json` the next `cli $CAND r` commits the floor with `recovered: true`, the foreign edit left uncommitted |
| 7 | `mk r ready`; `crash r validate`; `git -C r log --oneline -2`; `cli $CAND r` | after the stop the floor commit exists. cand: exit 0, `{"commit": null, "recovered": false}`, `HEAD` unmoved (the validator is not run again: the documented residual) |
| 8 | `mk r ready`; `crash r state`; `echo x > r/x.md; git -C r add x.md`; `snap`; `cli $CAND r`; `snap` | exit 1, `DirtyIndexBeforeStagingError`, `commit` null, **`state_changed` false** (the floor was already in the file before the call) and the floor not committed; after `git -C r rm -q --cached x.md; command rm -f r/x.md` the next `cli $CAND r` commits it (`recovered: true`) |
| 9 | `mk r ready`; `refuse r`; `git -C r log --oneline -2` | exit 1, one object with `"error": "MalformedGatePolicyFloorCommitError"`, `"commit"` equal to `git -C r rev-parse HEAD`, `"state_changed": true`; exactly one commit added; a `cli $CAND r` afterwards prints `{"commit": null, ...}` (the chain is healthy there: the refusal is synthetic; with a really failed provenance the answer is flow 11a (f)) |
| 10 | `cli $CAND r unknown`; `cli $CAND r ""`; `mk n nostate` then `py $BASE` on a copy and `cli $CAND n`; `mk c corrupt`; a state of `[]` and one of `{}`; a directory outside any repository | the Python baseline on `nostate` **creates** a state file holding only the floor and commits. cand: exit 1 each, one object, `UnknownWorkItem`, `UnknownWorkItem`, `StateMissing`, `CorruptJsonError`, `StateMalformed`, `StateMalformed`, and a class name (no traceback) outside Git; `commit` null and `state_changed` false; trees unchanged |
| 11 | `mk r ready`; for each of `--finding-dispositions wi`, `--plan-review-publication-status wi`, `--acceptance-gate wi`, `--satisfy-acceptance wi`, `--write-findings-record wi` run base and cand and compare stdout and exit (on `mk`'s item, which has no `governing_workflow_version`, `--plan-review-publication-status` prints nothing on stdout and exits 1 with a traceback on stderr: for that flag only the exit code is compared, `LOCAL-R1-006`); run `--commit-gate-policy-floor wi --acceptance-gate wi` and `--commit-gate-policy-floor wi --write-findings-record wi` with cand | the five old flags print byte-identical stdout and the same exit code from base and cand (stdout empty and exit 1 for the publication-status flag); both pairs exit 2 with "not allowed with argument" |
| 11a | the sibling proves before it stages (`LOCAL-R1-001`): in each of eight repositories, each built by its own `mk` (named `a` to `f`, `i`, `l`, `m`; every command below is given with the case's repository substituted, e.g. `snap $c`, `cli $CAND $c`, `mk $c plain` for (b), `LOCAL-R3-004`) and, where it says so, copied with `cpy`, run the Python call so the floor is committed, then (a) edit only the working floor's `digest` to 64 zeros; (b) `mk r plain`, no floor in `HEAD`, put a floor record with a malformed `policy` in the working file; (c) commit a malformed floor commit so provenance fails, then set the working floor to the default policy; (d) delete the working floor's `digest` key; (e) as (a), plus `echo x > x.md; git add x.md`; (f) a malformed floor commit so provenance fails and the working floor equal to `HEAD`'s; (i) as (c) plus `x.md` staged; (l) `mk $c plain` (no floor in `HEAD`, no policy file; the preamble's Python call does not apply to it, as for (b)), no `gate_policy_floor` in the working file, `x.md` staged; (m) a committed floor with only `recorded_at` edited, `x.md` staged (the cases (g), (h), (j) and (k) need the `_virtual_floor` patch, which no subprocess has, and belong to the tests); for each case `c`: `snap $c`; `cli $CAND $c`; `snap $c`; `git -C $c diff --cached --name-only` | exit 1 each except (l) and (m), which exit 0 with `{"commit": null, "recovered": false}` and `x.md` still staged, `FloorRecoveryRefusedError` with `floor_record_invalid` (a, b, d, e) and `floor_provenance_failed` (c, f, i), `commit` null, `state_changed` false, snapshots identical, nothing staged except `x.md` in (e), where `FloorRecoveryRefusedError` and not `DirtyIndexBeforeStagingError` is the answer, no `KeyError`; the base's Python call on a copy of (a) answers `None` and the old design would have committed: the contrast the finding measured |
| 12 | `cat $GH_LOG` after flows 1 to 11a; the function is untouched: `python3 -I -c` printing `hashlib.sha256(inspect.getsource(ws.commit_gate_policy_floor).encode()).hexdigest()` with `$BASE` and with `$CAND` | the log is empty (no forge call); the two digests are equal |
| 13 | `grep -n -e '--commit-gate-policy-floor' -e 'commit_gate_policy_floor' payload/.claude/commands/satisfy-gate.md`; then in `mk r early` after `cpy "$CAND" r/scripts`, run the documented line verbatim from `r` with the id substituted | the flag appears in "Plain commands first" and in the acceptance stage's step 5, after the findings-record paragraph; `commit_gate_policy_floor` stays named for the plan and implementation stages; the line has no `python3 -I`; it runs (no `ModuleNotFoundError`) and refuses with `work_item_not_complete`; `grep -c 'one Python call' payload/.claude/commands/satisfy-gate.md` prints 0 for the acceptance stage's text and `grep -n 'for the floor, one Python call\|is the one Python call that remains'` finds nothing (`LOCAL-R1-003`) |
| 14 | `git diff d6e6cb07f1c97837dd98a43cb2f3c198dade47dc <the CP1 commit> --stat -- payload docs manifest.json` | `workflow_state.py`, `workflow_gate_policy_test.py`, `satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md` (updated by `/milestone-implement`), the plan, registry, mapping, declaration and the state; no `workflow_protocol.py`, no manifest |
| 15 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` and its checker, `check-manager-block` with `--manager-releases`, the `tools/release` tests with the zlib-ng interpreter | all pass (the protocol and matrix suites report their own deliberate skips; `tools/release` fails rather than skips); the new tests run |
| 16 | (needs the full environment) scope: `git diff d6e6cb07f1c97837dd98a43cb2f3c198dade47dc --stat` at CP2 | CP2 adds `manifest.json`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md` and `tools/release/release_test.py`; no file added or removed; protocol still `1.5` |

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #148, floor commit | the state-only commit after the completion commit, as a flag | CP1 | D-Flag, F1 to F9 |
| Recovery: a floor waiting in the file | committed by the flag, `recovered`, after six preconditions | CP1 | D-Recovery, F5, F9 |
| Recovery: refusal after the commit | the commit and the error both reported | CP1 | D-Output, F6 |
| Order after the completion commit | refused by the flag; the library does not enforce it | CP1 | D-Order, F3 |
| Directory without a state file | refused (the function would create one) | CP1 | D-Order, F4 |
| #148 optional | `next-action` names the missing dispositions | none | out of scope; only if the owner asks |
| Library phase gap | `complete_work_item` from `IMPLEMENTING` and `MILESTONE_COMPLETE` | none | wf#158 item 1, the next row |
| Row 38 | `Current` with this plan, `Done` at acceptance | CP1 | D-Docs |
| Release | `feat:` 2.29.0, protocol `1.5`, no Controller change | CP2 | D-Release, 0d |

## 7. Decisions on the local review, round 1 (`7006c535...`, `REVISE`)

| Finding | Decision | Where |
| --- | --- | --- |
| LOCAL-R1-001 (blocking) | **Accepted in full.** Checked against `workflow_gate_policy.py`: `record_gate_policy_floor` (line 1053) returns the same object on a failed provenance, on `_virtual_floor` `None`, and when `_floor_resolved` (`policy` alone, line 603) matches; `validate_gate_policy_floor_commit` compares only with the parent. The sibling now proves provenance, record validity, the recomputed virtual floor and the no-looser bound before staging, each with a stable `code`; 0e, D-Recovery and D-Output are corrected | 0e, D-Recovery, D-Output, F9, m20 to m25, flow 11a |
| LOCAL-R1-002 | **Accepted.** `crash` takes `<repo> <step>` and now uses `cd "$1"`, `STOP="$2"` | section 5 |
| LOCAL-R1-003 | **Accepted.** Both sentences of `satisfy-gate.md` (lines 210-211 and 231-232 of the base) are named with their new wording; R6 asserts neither old text nor `one Python call` survives, mutation m26 | D-Command, R6, flow 13 |
| LOCAL-R1-004 | **Accepted, the second option:** the refusal is pinned by a test and the step is named in the rule (`git restore --staged`); the sibling does not accept an interrupted staging of its own, so the shared `stage_scoped_state` is not changed | D-Recovery, D-Output, F5, flow 6 |
| LOCAL-R1-005 | **Accepted.** Precondition 6 compares `policy` with `HEAD`'s floor and answers `commit: null` | D-Recovery, F2, m24, flow 2 |
| LOCAL-R1-006 | **Accepted, the second option:** the flow states that it compares the exit code alone for that flag on `mk`'s item | flow 11 |

## 8. Decisions on the local review, round 2 (`76ee4d8d...`, `REVISE`)

| Finding | Decision | Where |
| --- | --- | --- |
| LOCAL-R2-001 (important) | **Accepted.** Checked against `workflow_gate_policy.py`: `record_gate_policy_floor` (line 1067) and the sibling both call `_virtual_floor`, so a patch that makes the sibling's recomputation differ makes the function commit first. `floor_not_virtual` is shown by a direct call of `commit_pending_gate_policy_floor`; `floor_looser_than_head` stays through the flag (the patched floor equals the working one); the assertions of each are stated | F9 (g), (h), m22, m23 |
| LOCAL-R2-002 (important) | **Accepted, the first option:** F9 gains case (e) (a foreign path staged and a damaged working floor: `floor_record_invalid`, the path still staged), named in m25; the promise "refusals precede the index check" stays and is now pinned | D-Recovery, F9 (e), m25, flow 11a (e) |
| LOCAL-R2-003 (important) | **Accepted.** Flow 2's last case has its own `mk r ready` + `cli`; a `cpy` helper removes the target before every copy to a reused name (flows 1, 3, 5, 11a, 13) | section 5 |
| LOCAL-R2-004 (optional) | **Accepted, the qualify option:** D-Recovery says a completed floor answers `commit: null` on a healthy chain and that a failed provenance with nothing waiting is refused with `floor_provenance_failed` on purpose; F9 (f), flow 11a (f); flow 9 says its chain is healthy | D-Recovery, F9 (f), flow 9, flow 11a |
| LOCAL-R2-005 (optional) | **Accepted.** F2's looser case does not assert the opening identity sentence and states what it asserts | F2 |

## 9. Decisions on the local review, round 3 (`163d060e...`, `REVISE`)

| Finding | Decision | Where |
| --- | --- | --- |
| LOCAL-R3-001 (important) | **Accepted, the first option:** the promise "every refusal raises before the index check" stays and is pinned for every precondition. F9 gains (i) (precondition 2), (j) (4), (k) (5), each with `x.md` staged, and (l) (1), (m) (6) as the nothing-waiting answers with `x.md` staged (exit 0, `commit` null, `x.md` still staged); m25 names the case per precondition; F9 (g) and (h) state that the working floor differs from `HEAD`'s so that a mutant moved after the staging leaves a trace. D-Recovery states the nothing-waiting answer with a foreign path staged | D-Recovery, F9, m25, flow 11a |
| LOCAL-R3-002 (optional) | **Accepted, the one-sentence option:** a hand-written floor equal to the base is committed once; left as it is on purpose, with the reason | D-Recovery |
| LOCAL-R3-003 (optional) | **Accepted.** F2's second run is asserted as unchanged from before that run, not as "no `.ai-review`" | F2 |
| LOCAL-R3-004 (optional) | **Accepted.** Flow 11a's commands are written per case repository (`$c`) | section 5 |

## 10. Decisions on the local review, round 4 (`af3846f3...`, `REVISE`)

| Finding | Decision | Where |
| --- | --- | --- |
| LOCAL-R4-001 (important) | **Accepted, the first option.** Without the `_virtual_floor` patch, `record_gate_policy_floor` has something to write and its own index check answers `DirtyIndexBeforeStagingError` before the sibling is reached, so (k) cannot run as a subprocess. (k) leaves flow 11a and its Expect column; (g), (h), (j), (k) are named as the four seam cases that belong to the tests; F9's count is corrected | F9, flow 11a |
| LOCAL-R4-002 (important) | **Accepted.** F9 (l) and flow 11a (l) state "no floor in `HEAD`, nothing stricter observed", built by `mk $c plain`; one sentence says a floor removed or loosened with a foreign path staged answers the function's `DirtyIndexBeforeStagingError` | F9 (l), flow 11a |
| LOCAL-R4-003 (optional) | **Accepted.** m25 names what each moved precondition answers (4, 5, 6: `DirtyIndexBeforeStagingError`; 2 on (i): `floor_not_virtual`; 3 on (e): exit 0 `commit: null`); each still fails its named case | m25 |
| LOCAL-R4-004 (optional) | **Accepted.** F9 says (g) and (h) for the working floor differing from `HEAD`'s; flow 11a's repository count and names are corrected | F9, flow 11a |
