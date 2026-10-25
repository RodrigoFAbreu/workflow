# W25: Workflow 2.19.2 — wording and message accuracy of the checkpoint-start command (Revision 3)

- **Work item:** `command-wording` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator. It is row 26b of `docs/ROADMAP.md` (status `Current` from
  this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#100 (the wording and message items) and the documents part of
  RodrigoFAbreu/workflow#105 (the tests cell of the invariants page). The other half of #105 (two uncovered
  statements of the `owner_mutation` pin) is **not** done here and stays open.
- **Branch:** `milestone/command-wording`
- **Base commit:** `bebf2d2` (main after #107: the release source is Workflow 2.19.1, this repository's own
  installation is the published 2.19.1, automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog
  file declared, so the prose roadmap applies)
- **Plan revision:** 3. Revision 2 came from local round 1 (LPR-001 dropped M2, LPR-O1 and LPR-O2 applied) and
  stayed revision 2 through local round 2, local round 3 and the manual external round 1 (EPR-001, EPR-002);
  revision 3 comes from local round 4 (LPR4-001 and LPR4-002 applied, LPR4-O1 and LPR4-O2 applied; see
  section 4). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.19.2, a `fix:` patch, that makes what the checkpoint-start command and its refusals **say**
accurate. Shipped documents and the text of two messages change; no behaviour, refusal class, state key, phase, trailer,
guard-body key or protocol field changes. Six items, all from the two issues:

1. **W1.** `payload/docs/ai-workflow/COMMAND_FILES.md` says `true` for "six commands" in the
   `disable-model-invocation` row; seven command files carry the flag.
2. **W2.** The `released` bullet of step 2 of `release-checkpoint-start.md` says "this worktree holds no
   claim"; the code tests the work item's one shared claim (`resolve_claim` over the git common directory),
   and a claim held by another worktree is refused with `CheckpointOwnedByOtherWorktreeError`, never reported
   as `released`. The condition is "no claim for the work item in any worktree".
3. **W3.** `docs/CONCURRENCY_INVARIANTS.md`, release-window row: the recovery cell gives the command's act
   ("asks for the same attestation") to the engine, and the tests cell attributes the `test_p4_*` pin to
   `::TestAmendmentResolutionReservation`, where it is not (#100 W3, #105).
4. **W4.** The downgrade posture and the release-history row do not say how to finish an interrupted release
   when moving back to 2.18.7, which has no command for it. The published 2.19.0 and 2.19.1 records never
   change: this goes into the **new** 2.19.2 row and posture.
5. **W5.** the `**User-only commands**` bullet of `WORKFLOW_V2_1_OPERATOR_REFERENCE.md` (lines 34-35) lists only `/approve-review` and `/accept-milestone`
   as the user-only commands though the file documents seven.
6. **M1.** The first `AmendmentCheckpointActiveError` site of `request_plan_amendment` (the `IN_PROGRESS`
   arm) names `current_checkpoint_id or in_progress_ids[0]` and a release step that refuses for an entry with
   no claim ("step 1c adopts it first"). The message must name the right next step. The release refusal the
   message sends the reader to says the same unconditional thing ("step 1c adopts it first"), which is false
   when `current_checkpoint_id` does not name the entry (LPR4-002); its text is qualified the same way, so the
   two messages on one recovery path agree.

### The invariant (one sentence)

**I1.** Every sentence changed here is true of the shipped code, and each change is **pinned** by a test that
fails against the text it replaces and passes against the new one.

### Hard limits (the owner's sizing rule)

- **No new mechanism, protocol or state change.** The only production edits are the text of **two** messages:
  for M1, the choice of which checkpoint and which text the existing first raise prints, and the text of the
  existing release refusal for an unclaimed `IN_PROGRESS` entry in `_classify_checkpoint_start` (same class,
  same condition, no new read of `current_checkpoint_id`). No new branch of
  behaviour, no new read (the first raise does **not** start reading the claim), no new refusal class, no
  lock, guard, claim, `os.link` or `flock` site. **If a fix needs more, STOP and split it into a roadmap
  row.** Implementation re-checks this before it ends CP1: `git diff bebf2d2 -- payload/scripts/workflow_state.py`
  contains only message text and the choice of the named checkpoint.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`, the managed documents of
  `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks of `CLAUDE.md` and `.gitignore`, and
  `.github/workflows/workflow-conformance.yml`. The change goes to `payload/`; release bookkeeping to
  `manifest.json`, `docs/` user documents and `tools/release/`.
- **Size:** two checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test shown to fail against the text it replaces and to pass
  against the new one (D-Evidence); the nine payload suites from a staged fixture; the new tests and the whole
  chunks of the suites that changed under the Manager's orphan wrapper (D-Orphan); the `tools/release` tests
  (zlib-ng environment); the `tools/docs` tests and checker; `check-manager-block` with
  `--manager-releases`; `workflow-manager verify .` clean. Every command form is copied from
  `docs/RELEASING.md`, "Verification commands".
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against `git diff` (CP2).

## 2. Facts this plan relies on (re-checked against `bebf2d2`)

- **The seven user-only commands** are the command files with `disable-model-invocation: true`:
  `accept-milestone`, `adopt-gate-policy`, `approve-review`, `release-checkpoint-start`,
  `request-plan-amendment`, `resume-implementation` and `retire-legacy-work-item`. `COMMAND_FILES.md` already
  lists seven in its inventory below the table; only the row's count and line 34 of the operator reference are
  stale. The implementation counts the files and does not copy this list.
- **`released`** is returned by `observe_checkpoint_start_release` when `resolve_claim` finds **no** claim for
  the work item and the entry is `HEAD`'s. A claim held by another worktree reaches
  `_classify_checkpoint_start`'s `claim_is_this_worktree` test and is refused. So "this worktree holds no
  claim" is narrower than the code and wrong about the other-worktree case.
- **The recovery cell** of the release-window row already says "the engine re-classifies under (9)" (the phrase
  of #100's LIR-O3 was applied in 2.19.0). What stays inaccurate is the subject of the rest of the sentence:
  it is the **command** that observes (outside (9)) and asks for the attestation, and the **engine** that then
  re-classifies under (9).
- **The tests cell** reads "`::TestAmendmentResolutionReservation` (the `test_p4_*` pin and the journal
  refusal)". `test_p4_*` is in `TestReleaseCheckpointStartCommand`; only the journal refusal is in
  `TestAmendmentResolutionReservation`.
- **The first raise** is in `request_plan_amendment` (`workflow_state.py`, the `if in_progress_ids:` arm). It
  prints `current_checkpoint_id` in the message and names `current_checkpoint_id or in_progress_ids[0]` in
  `_release_start_next_step`. `current_checkpoint_id` need not be an `IN_PROGRESS` checkpoint, and the release
  of an `IN_PROGRESS` entry with **no** claim refuses with `CheckpointOwnershipStateMismatchError` ("nothing
  claims it, so nothing fences it -- step 1c adopts it first"). That classifier never reads
  `current_checkpoint_id`, while `resolve_checkpoint_ownership` derives `local_in_progress` from it alone
  (`claim is None and local_in_progress is None` is `FRESH`), so "adopts it first" is true only when the pointer
  names the entry. The claim arm below it needs no change: it
  names the claim's own checkpoint, and a claim held by another worktree is covered by the existing
  "from the worktree that holds the claim".
- **The `COMPLETE` refusals (why there is no M2).** `_classify_checkpoint_start` has two. The last one (a
  working entry that is neither `IN_PROGRESS` nor `HEAD`'s, the refusal reading "is {status!r} in this worktree, not IN_PROGRESS") already names both
  next steps (a committed completion: step 1c releases the claim; an uncommitted one, an owner died in
  `1f-commit`: resume step 1f), pinned by `test_c5_*`'s "a COMPLETE working entry names both next steps". That
  is where the uncommitted completion lands: step 1d's start is a working-tree write only, so `HEAD` records
  the entry as absent or `NEEDS_REVALIDATION`, and an uncommitted `COMPLETE` working entry falls through to the
  last refusal. The `HEAD`-baseline refusal (`6421-6426`) fires only when the state **committed at `HEAD`**
  records the checkpoint past a start, so a `COMPLETE` there is a committed completion and "step 1c releases
  this worktree's claim" is already its right and complete next step. The uncommitted-completion wording was
  RodrigoFAbreu/workflow#97 OPT-4, assigned to row 24c and fixed at the last refusal in 2.19.0. Neither #100
  (its "Message accuracy" has the one item M1) nor roadmap row 26b carries a `COMPLETE`-refusal item.
- **Where the repository already pins text.** `TestReleaseCheckpointStartCommandFile`
  (`workflow_integration_test.py`) pins the command file's wording and its listing in the contract;
  `TestRequestPlanAmendment` and `TestReleaseCheckpointStartCommand.test_c4_*` pin the amendment messages;
  `tools/release/release_test.py` pins manifest rationales, postures and history rows. The invariants page has
  no pin today.
- **Python 3.14** is the runtime here.

## 3. Design decisions

### D-Messages: wording and the choice of the named checkpoint, no new behaviour

**M1 (the first raise).** The text must be true whether or not a claim exists, **without reading the claim**
(the arm decides from the state it already holds; reading `resolve_claim` there would add a read whose failure
could change the refusal class). Two edits:

- the checkpoint named is chosen from `in_progress_ids`: `current_checkpoint_id` when it is one of them, else
  the first `IN_PROGRESS` id **in the `checkpoints` dict's own order**, exactly as the fallback
  `in_progress_ids[0]` does today (no sort is added, so the diff carries only the
  `current_checkpoint_id in in_progress_ids` choice). A `current_checkpoint_id` that is not `IN_PROGRESS` is no
  longer named, and the parenthesis "(`current_checkpoint_id`)" of the message names the same chosen id. The
  message names **one** checkpoint, not every `IN_PROGRESS` id (#100 LIR-O2 floated naming all): the release
  command takes a single checkpoint id, the work item's one shared claim fences one checkpoint at a time, and
  naming several would invite a release of the wrong one; after the named one is released the amendment
  request refuses again and names the next;
- `_release_start_next_step` gains an optional keyword (`entry_may_be_unclaimed`, default off, so the claim
  arm is byte-identical to today) that appends the two facts the release's own refusals state about an
  `IN_PROGRESS` entry, each qualified by the condition under which it holds, none of them read from the claim:
  (i) "The release refuses an `IN_PROGRESS` entry that nothing claims; `/milestone-implement <work_item_id>`
  (step 1c) adopts such an entry only when `current_checkpoint_id` names it, so with that pointer absent or
  naming another checkpoint, adoption is not offered and the entry is not releasable until state and claim
  agree." (EPR-001: `resolve_checkpoint_ownership` derives `local_in_progress` from `current_checkpoint_id`
  alone, so a stale pointer yields `FRESH`, not adoption. The text states that limit and promises no
  recovery step beyond it; ownership behaviour is unchanged.) (ii) "Run from the worktree that holds the work
  item's claim: if that claim is for another checkpoint, the release of this one refuses with the claim's
  checkpoint named; release that checkpoint instead." (LPR4-O1: from a worktree that does not hold the claim
  the release refuses first with `CheckpointOwnedByOtherWorktreeError`, which names the worktree, not the
  checkpoint, so (ii) carries its worktree condition in its own sentence.) (EPR-002: with several `IN_PROGRESS` entries the message names one by pointer membership or dict
  order, and `_classify_checkpoint_start` refuses it with `CheckpointOwnershipStateMismatchError` when the
  shared claim belongs to another entry, which that classifier accepts. The text sends the reader to the
  checkpoint the refusal names, and the selection rule is not changed to look for it, because finding it
  would be the claim read this arm must not add.) The command's name, the "from the worktree that holds the
  claim" clause and "never committed" stay.

**M1b (the release refusal M1 sends the reader to; LPR4-002, option (a)).** `_classify_checkpoint_start` refuses
an `IN_PROGRESS` entry that nothing claims with `CheckpointOwnershipStateMismatchError` and the text "step 1c
adopts it first". It is a second message edit, text only: the sentence becomes "step 1c adopts it only when
`current_checkpoint_id` names it; with that pointer absent or naming another checkpoint it is not adopted, and
the entry is not releasable until state and claim agree". The class, the condition (`claim is None` and the
working status `IN_PROGRESS`) and the order of the refusals stay; the classifier still does not read
`current_checkpoint_id` (the qualification is static text, true because `resolve_checkpoint_ownership` is the
authority on adoption). It is done rather than deferred because the two messages sit on one recovery path (M1
names this release as the next step), so leaving one false would make the reader's very next command contradict
the message that sent them there. The cost is one more pin (CP1 test (e)) and one more E1 subcase.

**No M2.** The `COMPLETE` refusals of `_classify_checkpoint_start` are not edited: both are accurate (section 2).

### D-Documents: what each edit says, and its pin

| Item | Edit | Pin (fails against `bebf2d2`) |
| --- | --- | --- |
| W1 | `COMMAND_FILES.md` row: "`true` (seven commands)" | integration suite: the count of command files carrying the flag, spelled as a word, equals the count the row states |
| W2 | command file step 2, `released` bullet: "no claim for the work item in any worktree and the checkpoint's entry is `HEAD`'s" | integration suite, `TestReleaseCheckpointStartCommandFile`: the new phrase present, "this worktree holds no claim" absent |
| W5 | operator reference line 34 lists every user-only command and says what the confirmation names without claiming "work item and stage" for all | integration suite: every command file carrying the flag is named in the `**User-only commands**` bullet (the text from that label to the next bullet, so a reflow cannot break the pin); the bullet no longer lists two as the general statement |
| W3 | invariants page: the recovery cell says the command observes and asks, the engine re-classifies under (9); the tests cell puts `test_p4_*` under `::TestReleaseCheckpointStartCommand` | `tools/release/release_test.py`: both phrases, and the old attribution absent |
| W4 | CP2: the 2.19.2 row and posture | `tools/release/release_test.py` 2.19.2 class (CP2) |

The pins read the shipped files through the repository's own helpers (`_command_text`, `_operator_reference_text`
and the contract path of `TestReleaseCheckpointStartCommandFile`); the flag count is **derived from the command
files**, never typed, so an eighth user-only command fails the pin until the document follows.

### D-Downgrade: how to finish an interrupted release on a move back to 2.18.7 (W4)

2.18.7 has the engine function `release_checkpoint_start(repo_root, work_item_id, checkpoint_id, *, now)` and
no command or confirmation sentence. The 2.19.2 posture and history row say, in this order: finish an
interrupted release **before** moving back below 2.19.0 by running `/release-checkpoint-start` again to
completion (as 2.19.0 already says); if the move was made first, update forward to a release that has the
command (2.19.0 or later), finish the release there, and move back; the only way to finish on 2.18.7 itself is
to call the library function directly, which carries none of the command's attestation and is for someone who
has made sure the owner session is stopped. The implementation checks each clause against the 2.18.7 and 2.19.0
history rows and `git show v2.18.7` before writing it. The 2.19.0 and 2.19.1 rows and manifest records are not
edited.

### D-Evidence: every changed text shown to fail before and pass after

Each new test is run against a scratch copy in which **exactly one** changed file is replaced by its
`bebf2d2` version (`git show bebf2d2:<path>`), and must fail there; the control run on the candidate must pass.
A scratch script under `$TMPDIR` (neither shipped nor committed) does the replacement into a fresh staged
fixture (D-Staging) and runs the named tests with `python3 -B -m unittest` from the fixture's `scripts/`.
The cases:

| Case | File restored to `bebf2d2` | Tests that must fail |
| --- | --- | --- |
| E1 | `payload/scripts/workflow_state.py` (first raise and the unclaimed-`IN_PROGRESS` release refusal) | the M1 tests (a) to (d) and the M1b test (e); a second subcase restores only the release refusal's text and shows (e) alone fails |
| E2 | `payload/docs/ai-workflow/COMMAND_FILES.md` | the W1 pin |
| E3 | `payload/.claude/commands/release-checkpoint-start.md` | the W2 pin |
| E4 | `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md` | the W5 pin |
| E5 | `docs/CONCURRENCY_INVARIANTS.md` (the checkout, not the fixture) | the W3 pin |

Results go to `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md` with the exact
command lines and the exact restored paths, plus the other gates' commands and the orphan reports. The file is
excluded at the plan stage (it cannot stale the plan approval) and **protected at the implementation stage**,
the precedent of `INTERLEAVING_PINS_EVIDENCE.md`.

### D-Orphan: no process left behind

The new tests start no process (they read files and call `request_plan_amendment` and
`observe_checkpoint_start_release` in a scratch repository). The new tests, and then the whole
`workflow_state_test.py` chunk, run under the Manager's wrapper (`tests/parallel/reaper.py` of the Manager
checkout; the form is in the evidence file of the previous release) from the staged fixture; the reports must
list no orphan beyond Git's own detached maintenance.

### D-Release: 2.19.2, `fix:`

`manifest.json` `workflow_version` 2.19.2. The shipped files that change, and so the records that move (each with
`sha256`, `size` and a `command-wording (workflow-2.19.2)` sentence true of **that** file, read against
`git diff bebf2d2..HEAD -- <file>`): `payload/scripts/workflow_state.py` (the first raise's message, its checkpoint choice, the helper keyword and the text of the unclaimed-`IN_PROGRESS` release refusal),
`payload/scripts/workflow_state_test.py` (the M1 message tests), `payload/scripts/workflow_integration_test.py`
(the document pins), `payload/.claude/commands/release-checkpoint-start.md`,
`payload/docs/ai-workflow/COMMAND_FILES.md`, `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
`payload/scripts/workflow_protocol.py` (`WORKFLOW_RELEASE` 2.19.2 and nothing else),
`payload/scripts/workflow_protocol_test.py` (the two pinned assertions) and
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (tested releases, envelope example, protocol note; the
protocol version stays 1.5). No artifact record is added or removed (counts stay 80 and 6).
`manager.conformance.suites` are **measured, never typed**: the counts of the suites that gained tests move.
`min_manager_version` stays 1.13.0, equal to the CI pin in `tools/release/manager-pin.json`. The detector
vocabulary is untouched (`signals` stays empty).

**Downgrade posture.** An older release reads everything 2.19.2 writes, because 2.19.2 writes nothing new: no
state key, phase, trailer, commit shape, guard-body key, protocol field or refusal class changes. What an older
release does with the changed message: 2.19.1 and 2.19.0 raise the same refusal classes under the same
conditions and print the previous text of both changed messages; 2.18.7 has no command and its amendment refusals name no release step.
`workflow-manager update` back to 2.19.1 (minimum Manager 1.13.0) restores the previous documents, message and
suites and the release constant 2.19.1. The finishing rule of D-Downgrade is stated in the posture and the row.

**Documents.** `docs/release-history.md` gets the 2.19.2 row (it **references #100 and the documents part of
#105 as done**, names the six items of section 1, says no behaviour changes, and gives the way back and D-Downgrade) and
its "Last checked with" line; the roadmap records the rest at acceptance. `docs/CONCURRENCY_INVARIANTS.md`:
"Last checked with: Workflow 2.19.2" (its two cells change in CP1). `tools/release/release_test.py`: a 2.19.2
release class; the 2.19.1 class keeps what stays true of that release (its rationale sentences and history row)
and no longer pins the current version, constant, counts or posture. `docs/RELEASING.md` changes only if a
count it states changes. No internal milestone id appears on a `docs/*.md` page (the pages say "the
checkpoint-start command", not a work-item id), and no list of governing versions is written in a managed
document.

### D-Staging: scratch staging for CP1

CP1 changes shipped files whose digest, size and measured suite counts `manifest.json` records only at CP2.
CP1 therefore verifies in a disposable clone under `$TMPDIR`: a scratch script recomputes `sha256` and `size`
of every `artifacts` record whose file differs from its record, measures and rewrites
`manager.conformance.suites` by the discovery `release.py manager-block --release-dir <scratch> --write` uses,
commits it in the clone, and runs the "Verification commands" blocks from there (the procedure of
`docs/milestones/completed/CHECKPOINT_START_COMMAND_PLAN.md`). No rationale is touched in the scratch, and the
report says the staging was adjusted.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
| --- | --- | --- |
| OD-1 | The version | **Patch 2.19.2, `fix:`**: shipped documents, one message and suites change; no capability. |
| OD-2 | M1: read the claim to choose the text, or word it for both cases | **Word it for both cases** (D-Messages): no new read, so no new way for the refusal class to change. |
| OD-6 | The release refusal's "step 1c adopts it first" (LPR4-002): qualify it, or defer it as a follow-up | **Qualify it** (D-Messages, M1b): text only, one pin, one E1 subcase; the two messages share a recovery path. |
| OD-3 | Where the document pins live | **The integration suite for shipped documents, `tools/release/release_test.py` for the invariants page**: the first already pins that command file and contract; the page is not shipped. |
| OD-4 | Whether the PR closes #100 | The release row **references** #100 and #105 as done and does not carry a closing keyword; whether the PR body closes #100 (all of its items are done with 2.19.1 and 2.19.2) is the owner's. #105 stays open for its pin-scenario half. |
| OD-5 | The manager CI pin | **No change** (1.13.0 equals `min_manager_version`). |

**Round 1 of the local plan review (revision 2).** LPR-001 accepted, option (a): M2 is dropped (section 2 gives
the evidence: the `HEAD`-baseline refusal cannot meet an uncommitted completion, the last refusal already names
both cases, and the source was #97 OPT-4, fixed in 2.19.0), with the goal count, the old E2, the mapping row, the
release sentences and the disposition table adjusted. LPR-O1 accepted (D-Messages keeps dict order and says why
one checkpoint is named). LPR-O2 accepted (the W5 pin reads the bullet, not a line).

**Round 2 of the local plan review (still revision 2).** LPR2-001 accepted: D-Release's history-row sentence now
names "the six items of section 1", the count section 1 states (no other seven/M2 leftover remains besides the
seven user-only commands, which is a different count). LPR2-O1 accepted: the last `COMPLETE` refusal is cited by
its text ("is {status!r} in this worktree, not IN_PROGRESS"), not by a line range that goes out of date. No
checkpoint, requirement or revision changes, so the registry and mapping are untouched.

**Manual external review round 1 (still revision 2).** EPR-001 and EPR-002 accepted after confirming both
against the code (section 3, D-Messages; CP1 tests (c) and (d)). Both are wording-only: the first says step 1c
adopts an unclaimed entry only when `current_checkpoint_id` names it (`resolve_checkpoint_ownership` returns
`FRESH` otherwise), the second says a claim for another checkpoint makes the named release refuse and points to
the checkpoint that refusal names. Selection, raise conditions, exception classes and the no-new-claim-read rule
are unchanged. That round changed no checkpoint, requirement or revision and left the registry and mapping as
they were, which left requirement R2 stating the unconditional adoption EPR-001 found false; local round 4
corrects it (next paragraph). The statement that the mapping was untouched was true only of that round.

**Round 4 of the local plan review (revision 3).** LPR4-001 accepted: requirement R2 of the mapping is reworded
to the revised design (an `IN_PROGRESS` checkpoint named by pointer membership, else dict order; the release
with the two qualified facts; adoption only when `current_checkpoint_id` names the entry and, for a claim on
another checkpoint, the release of the checkpoint the refusal names; the claim arm unchanged; no new read,
branch or refusal class), and R3 now says the text of two messages. The mapping changes, so the registry and
mapping are regenerated at revision 3 (the checkpoints are unchanged). LPR4-002 accepted, option (a): M1b in
D-Messages; the hard limits, D-Evidence (E1 subcase), D-Release, CP1 (test (e)) and the disposition table agree
(two messages). LPR4-O1 accepted (sentence (ii) carries its worktree condition). LPR4-O2 accepted (the header
names every round).

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does not exist in this
repository's release source).

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The documents, the message and their pins | - | 2 | 1 |
| CP2 | Release 2.19.2 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The documents, the message and their pins

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`,
`payload/scripts/workflow_integration_test.py`, `payload/.claude/commands/release-checkpoint-start.md`,
`payload/docs/ai-workflow/COMMAND_FILES.md`, `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
`docs/CONCURRENCY_INVARIANTS.md`, `tools/release/release_test.py`,
`docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md`.

- **Tests first, shown red** (D-Evidence): write the pins, run them against the candidate's old text (cases E1
  to E5) and see them fail, then make the edits and see them pass. **Done:** the evidence file lists every case,
  its exact command line, the restored path and the failing tests, and a control run that passes.
- **The messages** (D-Messages, M1 and M1b): the first raise names an `IN_PROGRESS` checkpoint and, in the same message, the
  release together with the two qualified facts about an `IN_PROGRESS` entry (unclaimed: adoption only when
  `current_checkpoint_id` names it; claim for another checkpoint: release the one the refusal names). Tests,
  in `workflow_state_test.py`: (a) an `IN_PROGRESS` entry with a `current_checkpoint_id` that is another
  checkpoint names the `IN_PROGRESS` one in both places, and with no `current_checkpoint_id` of its own it names
  the first `IN_PROGRESS` id in dict order; (b) an `IN_PROGRESS` entry with no claim names the release, still
  names the command, and the claim arm's text is byte-identical to today's (a claim exists: neither added
  sentence); (c) **EPR-001:** an unclaimed `IN_PROGRESS` entry with `current_checkpoint_id` absent, and again
  with it naming another checkpoint, yields a message that does not promise step 1c adopts the entry
  unconditionally (it states the pointer condition), checked against `resolve_checkpoint_ownership` on the
  same scratch state (`FRESH`, not adoption) so the pin cannot drift from the behaviour it describes;
  (d) **EPR-002:** two `IN_PROGRESS` entries (CP1 then CP2), a stale pointer and a shared claim for CP2: the
  raise names CP1, the message says a claim for another checkpoint makes that release refuse and to release
  the checkpoint the refusal names, and `release_checkpoint_start` for CP1 on that state raises
  `CheckpointOwnershipStateMismatchError` while the classifier accepts CP2, so the guidance is shown true.
  Raise conditions, exception classes and the absence of a new claim read stay: the raise site still does not
  call `resolve_claim` before the `IN_PROGRESS` raise; (e) **LPR4-002 (M1b):** `release_checkpoint_start` on an
  unclaimed `IN_PROGRESS` entry, once with `current_checkpoint_id` absent and once naming another checkpoint,
  still raises `CheckpointOwnershipStateMismatchError`, and its text states the pointer condition and no longer
  says "step 1c adopts it first" unqualified, with `resolve_checkpoint_ownership` on the same scratch state
  returning `FRESH` so the pin cannot drift from the behaviour it describes. **Done:** each fails against `bebf2d2`'s
  `workflow_state.py` and passes with the edit; `test_c4_*` and the `test_c5_*` COMPLETE subtest pass unedited.
- **The documents** (D-Documents): W1, W2, W5 with their integration-suite pins; W3 with its pin in
  `tools/release/release_test.py`. **Done:** each pin fails against its restored file.
- **No new mechanism:** `git diff bebf2d2 -- payload/scripts/workflow_state.py` shows the text of two messages, one optional
  keyword of `_release_start_next_step` and the choice of the named checkpoint; no lock,
  guard, claim, `os.link`, `flock` or `resolve_claim` site is added; `TestGlobalLockOrderItem372h` passes
  unedited.
- `docs/ROADMAP.md` row 26b is `Current` from this plan and this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites, the new tests and then the whole
`workflow_state_test.py` chunk under the Manager's orphan wrapper (no orphan beyond Git's own detached
maintenance), the `tools/release` and `tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.19.2

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`,
`docs/release-history.md`, `docs/CONCURRENCY_INVARIANTS.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.19.2 with its two pinned assertions in `workflow_protocol_test.py` and the
  matching `ORCHESTRATION_PROTOCOL.md` edits (tested releases list, envelope example, protocol note); the
  protocol version stays.
- `manifest.json` 2.19.2 (D-Release): `workflow_version`; `sha256` and `size` of every changed record; an
  accurate `command-wording (workflow-2.19.2)` sentence on **each** changed record, true of THAT file and read
  against `git diff bebf2d2..HEAD -- <file>`; the `manager` block's posture rewritten for the patch with the
  D-Downgrade clauses and what an older release does with the changed message; `conformance.suites` measured
  by `release.py manager-block --release-dir <scratch> --write` from a staging of CP2's own content;
  `min_manager_version` equal to the CI pin.
- `docs/release-history.md`: the 2.19.2 row (references #100 and #105 as done, closes no issue by keyword,
  says how to finish an interrupted release on 2.18.7) and the "Last checked with" line;
  `docs/CONCURRENCY_INVARIANTS.md`: its "Last checked with" line.
- `tools/release/release_test.py`: a 2.19.2 release class (version, constant, counts (80, 6), each changed
  record's sentence and no other record carrying it, the posture and history needles including the D-Downgrade
  clauses); the 2.19.1 class keeps what stays true of it.
- `docs/ROADMAP.md` is not written by this checkpoint: row 26b becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture;
`release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #100 W1 | `COMMAND_FILES.md` "six commands" | CP1 | D-Documents, E2 |
| #100 W2 | the `released` bullet | CP1 | D-Documents, E3 |
| #100, #105 W3 | the invariants recovery cell and the tests cell | CP1 | D-Documents, E5 |
| #100 W4 | finishing an interrupted release on 2.18.7 | CP2 | D-Downgrade; the 2.19.0 and 2.19.1 records are not edited |
| #100 W5 | the operator reference `**User-only commands**` bullet (line 34) | CP1 | D-Documents, E4 |
| #100 M1 | the first `AmendmentCheckpointActiveError` site, and the unclaimed-`IN_PROGRESS` release refusal it sends the reader to (LPR4-002) | CP1 | D-Messages (M1, M1b), E1 |
| #100 M2 | none: #100 has no such item; the `COMPLETE` refusals are accurate (section 2) | - | the item came from #97 OPT-4 (row 24c, fixed in 2.19.0) |
| #105, first bullet | two uncovered statements of the `owner_mutation` pin | **not here** | stays open |
| Release | 2.19.2 bookkeeping; references #100 and #105 as done | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/command-wording-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its plan-stage
protected paths, and self-review checked that every path named in a Files paragraph, and every other path this
plan names (`docs/ROADMAP.md`, `docs/RELEASING.md`, `docs/release-history.md`,
`docs/CONCURRENCY_INVARIANTS.md`), is classified at both stages and that every deliverable is protected at the
implementation stage. The evidence file `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md` is excluded at the plan
stage and listed in `implementation_stage.protected_paths` (before the excluded `docs/ai-workflow/` prefix is
consulted).

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands", and the manifest key is
`workflow_version`. Each flow names its workspace.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`), from `$TMPDIR/fixture/scripts` | the new tests pass: the message tests of `workflow_state_test.py` (named in the evidence file) and `python3 -B -m unittest -v workflow_integration_test.TestReleaseCheckpointStartCommandFile` |
| f2 | a staged fixture per case, one file restored to `bebf2d2` | each of E1 to E5 makes exactly the named tests fail, and the control run passes |
| f3 | the staged conformance fixture | the `workflow_state_test.py` chunk under the Manager's orphan wrapper reports no orphan beyond Git's own detached maintenance |
| f4 | the staged conformance fixture | the nine suites from the manifest's `manager.conformance.suites` list |
| f5 | the checkout (zlib-ng environment for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, and `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f6 | the checkout | `git diff bebf2d2 -- payload/scripts/workflow_state.py` shows only the text of two messages, the optional keyword and the choice of the named checkpoint; the 2.19.2 history row, the invariants page and the manifest agree on the version; the 2.19.0 and 2.19.1 rows are unchanged |
