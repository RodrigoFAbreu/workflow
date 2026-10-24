# W23: Workflow 2.19.0 — the command that releases an uncommitted checkpoint start (Revision 3)

- **Work item:** `checkpoint-start-command` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner split the paused W19 on 2026-10-23 (the
  sizing rule, principle 10). W21 (Workflow 2.18.6) shipped the live-owner guard lock and the probe; W22
  (Workflow 2.18.7) shipped the engine, the library function `workflow_state.release_checkpoint_start`.
  This item is the **command surface only**. It is row 24c of `docs/ROADMAP.md` (status `Current` from this
  plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#55 (closed by this release) and the three items of
  RodrigoFAbreu/workflow#97 that belong to the command (the other two ship with a later roadmap row).
- **Branch:** `milestone/checkpoint-start-command`
- **Base commit:** `ad1121a` (main after #99: the release source and this repository's own installation
  are both Workflow 2.18.7, automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file
  declared, so the prose roadmap applies)
- **Plan revision:** 3 (round 1 of the local plan review and round 1 of the manual external plan review applied, sections 8 and 9). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.19.0, a `feat:` minor (a user-visible command is added), that adds the user-only command
`/release-checkpoint-start <work-item-id> <checkpoint-id>`. It releases an **uncommitted** checkpoint start
(the `IN_PROGRESS` entry and the claim) by calling the engine, so that `/request-plan-amendment` is no
longer wedged by a start its own plan forbids completing (#55). The engine stays the only concurrency
mechanism. This item adds **one** new mechanism, a confirmation that is bound to the claim the user was
shown, and no second concurrency mechanism.

### The invariant (one sentence)

**I1.** A start is released only by a person who was shown the claim that holds it and attested, in the
current turn, that no session owns it any longer and that none will until the release has completed; the
literal they type names the work item, the checkpoint and that claim, and the engine refuses unless the
claim it finds under its lock is that claim. The attestation is a stated precondition, not a check: the
engine's residual is turned into a breach of it, not closed (D-Residual).

### Hard limits

- **No state field, ledger, phase, trailer or commit-shape change; no protocol change.** Refusal classes
  keep their names; nothing is committed by the command. The Orchestration Protocol stays at its current
  version (D-Protocol). No Controller or Manager change: `min_manager_version` stays 1.13.0 and
  `tools/release/manager-pin.json` must EQUAL it.
- **One new mechanism, no second concurrency one.** The engine gains one optional keyword (D-Engine-Keyword)
  and two small public functions around it; no lock, guard, claim, primitive or lock-order edge is added.
  If implementation finds that a check of the idle owner needs a second concurrency mechanism (a fence, a
  heartbeat), it STOPS and splits it into a roadmap row (principle 10); see D-Residual for why this item
  does not add one and what it therefore does not close.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`, the managed documents of
  `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks of `CLAUDE.md` and `.gitignore`, and
  `.github/workflows/workflow-conformance.yml`. The change goes to `payload/`; release bookkeeping to
  `manifest.json`, `docs/` user documents and `tools/release/`.
- **Size:** two checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test, shown to fail against the unedited code first; the
  nine payload suites from a staged fixture; the whole `workflow_state_test.py` chunk under the Manager's
  orphan wrapper (new tests leave no process behind); the `tools/release` tests (zlib-ng environment); the
  `tools/docs` tests and checker; `check-manager-block` with `--manager-releases`;
  `workflow-manager verify .` clean. Every command form is copied from `docs/RELEASING.md`, "Verification
  commands".
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against `git diff` (CP2).

## 2. Facts this plan relies on (re-checked against `ad1121a`)

- **The engine.** `release_checkpoint_start(repo_root, work_item_id, checkpoint_id, *, now)` takes the
  lifecycle lock (9), classifies the start from fresh reads (`_classify_checkpoint_start`: kind `entry`
  for a working `IN_PROGRESS` entry, `baseline` for an entry equal to the one `HEAD` records), asks the
  probe `guard_holder_is_running` (a live holder refuses), opens one destructive `release-start` guard,
  re-verifies, restores the entry, then unlinks the claim. Every refusal is an existing class.
- **The claim records no process.** `_build_claim_record` stores the worktree, the checkpoint, the minted
  `owner_token` and timestamps; no pid, no start time, no heartbeat. Between two owner windows no guard
  exists. So from disk alone nobody can tell a stopped owner session from an idle live one.
- **The accepted residual of the engine** (its plan, D-Residual; its findings record): after an
  interruption past the state write, the dead `release-start` guard is reclaimable by the owner like any
  own leftover, so an owner that is still alive can run `1f-commit` before the next call. Never recorded:
  harmless. Demoted and re-started: the owner commits `COMPLETE` with the old `start_commit`, the checkpoint
  has two trailer commits, and `prove_checkpoint_completions` raises `AmbiguousCheckpointTrailerError`.
  "Row 24c must close it, or check that the owner is stopped, before a command calls the function."
- **The benign HEAD movement and the `COMPLETE` wording are already in the engine** (re-read at
  `payload/scripts/workflow_state.py`): `_assert_no_commit_past_start` walks `start_commit..HEAD`, refuses
  only a commit that carries the checkpoint's trailer or records it other than as `HEAD` does, so a merge
  after the start does not block; the final refusal of `_classify_checkpoint_start` names a committed
  completion (step 1c) and an uncommitted one (resume step 1f). Both are pinned by the engine's T2 and T3;
  this item adds the command-level pin (D-Followups).
- **User-only commands.** Six command files carry `disable-model-invocation: true`. Their shared guard is
  the literal confirmation validated by the writer itself (`validate_user_only_confirmation` for
  `/retire-legacy-work-item` and `/resume-implementation`; sibling validators for the others). Only some
  are protocol actions: `/request-plan-amendment` and `/adopt-gate-policy` are user-only and are not in
  the protocol's `ACTIONS` table.
- **Tests that count command files** (found by running the nine suites over a staged fixture that holds
  one extra command file, which this plan does not need to guess): in `workflow_integration_test.py`, the
  `COMMAND_FILES.md` user-only list equality, the per-file literal-confirmation needles, the operator
  reference sections (heading, count of live commands, inventory claim, child-lifecycle naming), the
  child-sequence exemption set and the width lint of the user-only files.

## 3. Design decisions

### D-Residual: (a), an attested and observed precondition, not (b), an engine refusal

The owner asked to decide between (a) a literal confirmation that includes an explicit attestation that the
owner session is stopped (the command shows the observed claim, the guard state and the probe result
first) and (b) the engine refusing while an owner could still be running.

**This item diverges from the engine plan's requirement, and says so.** The engine plan
(`docs/milestones/completed/CHECKPOINT_START_ENGINE_PLAN.md`, D-Residual) asked row 24c to close the
residual "or check that the owner is stopped" before the command calls the function, a precondition the
command **checks** and not only states in text. Under (a) the only part that is checked is a running window
(which the engine already refuses); the part that matters, an owner session that is alive and idle, is
**text the person attests**. That is the choice the owner offered (the first alternative above); it is not
a check, and no wording below calls it one.

**(b) is not available without a second mechanism.** The only evidence of a running owner on disk is a
published guard held by a live process, and the engine already refuses that (the probe and the owner
role's own refusal of a live holder). An owner that is alive and idle between two windows leaves nothing:
no guard, and a claim with no process identity (`_build_claim_record` records no pid, start time or
heartbeat). To refuse it the engine would need a new fact (an owner heartbeat or lease, or a fence that
makes a dead release guard unreclaimable by the owner), which is a new concurrency mechanism: a new branch
in the guard's decision table and a replacement of a leftover guard in place. That is a split, not part of
this item.

**(a) is chosen.** The command:

1. shows, before it asks for anything: the observed claim (checkpoint, worktree, `claimed_at`, whether it
   was adopted, and the claim reference `owner_token[:12]`), the kind of start (`entry`: an `IN_PROGRESS`
   entry; `baseline`: an entry already equal to `HEAD`'s, so a start that died before its state write or a
   half-finished release; `released`: no claim at all and an entry equal to `HEAD`'s, the end state of a
   release, see below), the guard state (none, or the step, class and whether its holder is running),
   and the probe result;
2. stops, without asking for a confirmation, when the probe answers that a window of the work item is
   running (the checked part: a live owner window is never overtaken, the engine refuses it too);
3. **says, before it asks and before anything is released,** that the release has an interval in which an
   interruption leaves it half done, that an interrupted release must be finished by running this command
   again, and that no session may resume the checkpoint, from this worktree or any other, until the command
   has reported success (D-Command step 3). This wording is printed before the release because an
   interruption that kills the call (the process killed, the session ended, the machine failing) prints
   nothing afterwards;
4. asks for the one literal sentence (D-Literal), which attests that the owner session is stopped and stays
   stopped until the release has completed, the part the disk cannot show;
5. reports, after the call, what to do after an interruption that does return a refusal (D-Command step 6).

**What (a) does, and every way the residual stays reachable.** (a) turns the residual into a **breach of
the attested precondition**; it does not close it. The demoted-and-re-started outcome
(`AmbiguousCheckpointTrailerError`, two trailer commits for the checkpoint) remains reachable, by exactly
two routes, and the docs say so (D-Docs):

- **R-i, a true attestation broken.** The person attests a stopped owner, the call is interrupted past the
  state write, and an owner session is started (or resumed) before the command is run again and completed.
- **R-ii, a false attestation.** The person attests a stopped owner that is in fact alive and idle, and the
  call is interrupted past the state write; the dead `release-start` guard is reclaimable by that owner like
  any own leftover, so it can run `1f-commit` before the next call.

The never-recorded outcome stays harmless in both. The next run of the command observes an interrupted
release and finishes it, by one of two outcomes that depend on whether the claim is still there:

- **The claim is still there** (the interruption was before the claim unlink: kind `baseline`, usually with a
  `release-start` guard whose holder is not running). The next run asks the same sentence again with the
  fresh claim. The attestation requirement holds for as long as a claim exists, so an incomplete release is
  never completed without it.
- **The claim is gone** (the interruption was after the claim unlink, or the engine returned and the
  report was lost). The release is complete, but the engine's classification looks for a claim first and
  would refuse every retry with `CheckpointNotInProgressLocallyError` ("there is nothing to release"), so a
  person following the command's rule would never obtain a success to wait for. The observation therefore
  answers this state itself, before the engine's classification, with kind `released`: no claim in this
  worktree for the work item, and the work item's entry for the checkpoint equal to the state `HEAD` records
  (absent, or the `NEEDS_REVALIDATION` entry of a demoted checkpoint; anything else falls through to the
  engine's refusal, unchanged). It is a **terminal, read-only outcome**: the command reports that the start
  is released (or that no start was ever held, which this state cannot tell apart and which is equally
  safe), asks for no sentence because nothing is left to attest to, writes nothing, and **lifts the
  pre-release obligation**, the same as a success report for the purpose of resuming. Lifting is safe: with
  no claim, a guarded window of an owner session passes `acquire_guard` (a dead guard of a rotated-away
  epoch is reclaimed) and then fails `assert_claim_owner`, so its body never runs, as the engine's I1
  states. A dead `release-start` guard that may remain is reported and left alone; the next guarded window
  reclaims it by that same existing rule.

A fence that removes even these two routes by construction remains a roadmap candidate and is
not needed to close #55 (the wedge of `/request-plan-amendment`).

**Who the owner session is.** An *owner session* is any session other than the one running this command
that started, resumed or may resume the checkpoint, in this worktree or another. The session that is running
the command is not what the attestation is about, even when it is the very session that started the
checkpoint and just received `AmendmentCheckpointActiveError` (the common case of #55, where the claim is
this worktree's): that session counts as stopped for this purpose only when it runs nothing else for the
work item until the release has completed. The command file and the operator reference say this in the same
words (D-Command step 3, D-Docs).

### D-Literal: the confirmation names the work item, the checkpoint and the observed claim

The sentence is fixed text that the command prints for the person to send back:

`Release checkpoint start <checkpoint-id> of <work-item-id> held under claim <claim-ref>; its owner session is stopped and stays stopped until this release has completed.`

- `claim_ref` is the first 12 hex characters of the claim's `owner_token`: it identifies the claim that was
  shown, so a confirmation given for an earlier claim of the same checkpoint (released and started again,
  or rotated by a takeover) names a different reference and cannot release the new start. (The token
  prefix, not `claim_observation_id` as in the takeover literals: see OD-4.)
- The attestation has two halves, both inside the sentence: *is stopped* (the state at the time of the
  answer) and *stays stopped until this release has completed* (the obligation that covers an
  interruption). *Owner session* is defined in D-Residual (any session other than the one running the
  command that started, resumed or may resume the checkpoint; the current session counts as stopped while
  it runs nothing else for the work item).
- The match is **case-insensitive**, as `validate_user_only_confirmation` is (`re.IGNORECASE`); the
  expected sentence printed in a rejection keeps the canonical case. C1 pins an upper-case and a mixed-case
  acceptance.
- `workflow_state.checkpoint_start_release_confirmation(work_item_id, checkpoint_id, claim_ref)` builds the
  sentence and `workflow_state.validate_checkpoint_start_release_confirmation(text, *, work_item_id,
  checkpoint_id, claim_ref)` validates it: whitespace-normalised, the sentence must occur in the text with
  an id-alphabet boundary before it. It is a literal (not a set of words), so it carries the attestation
  with it, and its rejection message prints the sentence expected. Raises the existing
  `UserConfirmationRejectedError`; no new refusal class (D-Refusals).
- Never fabricated, inferred or carried over from an earlier turn: the same user-only guard text as the
  other commands, so a stale confirmation cannot release a different start.

### D-Engine-Keyword: the engine re-checks the confirmed claim under its own lock

The confirmation is validated outside the lifecycle lock, against a claim read outside it; the claim could
change in between. So `release_checkpoint_start` gains one optional keyword, `confirmed_claim_ref: str |
None = None`. When given, the engine compares it with the reference of the claim it classifies under (9)
and refuses with `CheckpointOwnershipStateMismatchError` ("the claim changed since you confirmed: run the
command again") before the probe and the guard. When `None`, nothing changes: the engine's eleven tests
and its 2.18.7 behaviour are unedited. The owner role's `assert_claim_owner` under the guard then fixes the
token, so the claim the confirmation named is the claim released. This is the "one keyword, with its test"
that the engine plan's OD-5 reserved for this item.

### D-Functions: two small public functions, no new lock

- `workflow_state.observe_checkpoint_start_release(repo_root, work_item_id, checkpoint_id)` is read-only and
  takes no lock of its own (the probe takes (6) as a leaf). It returns the observation of D-Residual step 1
  as a dict and raises the engine's classification refusals unchanged, so the command stops at the first
  true fact. Its one addition to the engine's classification is the terminal kind `released` (D-Residual):
  when `resolve_claim` finds no claim and the work item's entry for the checkpoint equals the state `HEAD`
  records (absent for absent, or the `NEEDS_REVALIDATION` entry), it returns `kind: "released"` with no
  claim, the guard state and the probe result, instead of `CheckpointNotInProgressLocallyError`. A working
  `IN_PROGRESS` entry with no claim, or any other state, still raises as before. It adds no primitive, no
  edge and no state.
- `workflow_state.release_checkpoint_start_confirmed(repo_root, work_item_id, checkpoint_id, *,
  user_confirmation, now)` observes, validates the literal against the observed claim reference, then calls
  `release_checkpoint_start(..., confirmed_claim_ref=<that reference>)`. Like `resume_implementation` it
  validates the confirmation itself. It returns the observation it acted on. For kind `released` it
  validates nothing, calls nothing and writes nothing: there is no claim to name and no release to make.
  Refusal order: the engine's classification refusals first (the claim
  must be known to build the sentence), then `UserConfirmationRejectedError`, then the engine's own.

### D-Command: `/release-checkpoint-start <work-item-id> <checkpoint-id>`

A new `payload/.claude/commands/release-checkpoint-start.md`, `disable-model-invocation: true`,
`state_writer: true`, `review-subject: none`, with the user-only guard of the other commands (the
confirmation check is the control the command carries under every harness, the flag an additional layer,
"The agent must never invoke"). Steps:

1. **Resolve the ids** from `$ARGUMENTS` only (never from the confirmation, never from
   `active_work_item_id`); refuse when either is missing or the work item is not a key of `work_items`.
2. **Observe** with `observe_checkpoint_start_release` and show everything D-Residual lists. Stop on a
   classification refusal, and stop when a window of the work item is running. **Stop, as a success, on
   kind `released`:** report that this worktree holds no claim and the checkpoint's entry is `HEAD`'s, so
   the start is already released (or none was held); name any dead `release-start` guard as a harmless
   leftover the command did not touch; state that the pre-release obligation of step 3 is lifted and that
   `/request-plan-amendment <id>` or `/milestone-implement <id>` is next. No sentence is asked and nothing
   is written. Every other kind (`entry`, `baseline`) goes on to step 3: while a claim exists, no step is
   skipped.
3. **Say, then ask for the literal** (D-Literal). Before asking, print, in this order: what the sentence
   attests, with *owner session* defined as in D-Residual (including that the current session counts as
   stopped only while it runs nothing else for the work item); that an interrupted release must be finished
   by running this command again, and that no session may resume this checkpoint, from this worktree or
   any other, until the command has reported success (the step 5 report, or the step 2 `released` outcome);
   then the exact sentence. Stop if the current turn's
   message does not carry it. The interruption wording is printed here, before the release, because a call
   that is killed prints nothing afterwards.
4. **Release** with `release_checkpoint_start_confirmed`. Report the refusal and stop on any.
5. **Report** what changed: the entry restored to `HEAD`'s state (absent, or the demoted entry), the claim
   removed, nothing committed, and that `/request-plan-amendment <id>` or `/milestone-implement <id>` is
   next. A `COMPLETE` refusal names both cases (a committed completion: `/milestone-implement` step 1c
   releases the claim; an uncommitted one: resume step 1f in the owner's worktree).
6. **After an interruption that returns a refusal** (for example `CheckpointOwnershipUnavailableError`
   after the restore), repeat the obligation of step 3: do not start the owner session again; run the
   command again. It shows the interrupted release and, while the claim still exists, asks for the same
   attestation with the fresh claim; if the claim is already gone it reports the `released` outcome of
   step 2 and the obligation ends. An interruption that returns nothing, and a release whose report was
   lost after the engine returned, are covered by step 3 and by running the command again.

The command writes the working-tree `WORKFLOW_STATE.json` through the engine's `state_transaction` (the
standard state-writer paragraph) and commits nothing.

### D-Protocol: documentation only; the Orchestration Protocol stays at its current version

The command is reached from `IMPLEMENTING` after `/request-plan-amendment` refuses with
`AmendmentCheckpointActiveError`. The protocol's rows are derived from the phase and the state, and a
checkpoint whose own plan forbids completing it is not a state the protocol can see: `next-action` for that
item correctly says to continue the checkpoint. Naming the release as a blocked-row alternative would make
`next-action` assert something it cannot know. The same holds for `/request-plan-amendment` itself and
`/adopt-gate-policy`: user-only commands that are not protocol actions. So no action, row, field or check
is added, the protocol version stays, and the release constant `WORKFLOW_RELEASE` follows the release. The
Orchestration Protocol document gains one sentence beside its `user_only` paragraph naming the user-only
commands that are not actions, the new one included (CP2).

### D-Amendment-Message: the refusal names the command

Both raise sites of `AmendmentCheckpointActiveError` in `request_plan_amendment` (the `IN_PROGRESS` one and
the outstanding-claim one) gain the next step: if the checkpoint's own approved plan forbids completing it
and its start was never committed, stop its owner session and run the user-only
`/release-checkpoint-start <work-item-id> <checkpoint-id>`. The message says to run it **from the worktree that
holds the claim** (the claim message already names it) because the release has two further refusals this
step cannot see from the raise site: at the first site an `IN_PROGRESS` entry may have no claim, and the
release then refuses `CheckpointOwnershipStateMismatchError` (step 1c adopts it first); at the second, the
claim may be held by another worktree, and the release then refuses `CheckpointOwnedByOtherWorktreeError`.
The message names the command as the step for a start that was never committed, not as the step for every
case. The error keeps its name and its two conditions; the third raise (the plan-approval open, which concerns a live claim during an approval
transaction) is unchanged.

### D-Followups: the #97 items that belong here

- **Guardless recovery residue** (docs only): `docs/CONCURRENCY_INVARIANTS.md` gains the row for a
  recovery crash between deleting the old guard and publishing its replacement: the claim and the restored
  baseline entry remain with no guard; another call completes the release; owner entry falls within the
  accepted residual, now covered by the attestation.
- **Benign HEAD movement: no engine widening.** The engine already uses the "no checkpoint commit" rule
  (Facts). The decision is to keep it and to say so: the docs state that a merge into the branch after the
  start does not block the release, and an end-to-end test pins it through the command's steps (D-Tests).
  A commit that really is a checkpoint commit (it carries the checkpoint's trailer or records it other than
  as `HEAD` does) is not an uncommitted start, so the refusal stays and its next step is the ordinary one:
  continue or complete the checkpoint with `/milestone-implement`.
- **The `COMPLETE` refusal's next step** names both a durable and a not-yet-committed completion in the
  engine already; this item pins the exact text through the command and repeats it in the command file's
  step 5 and the operator reference.
- Not here (later row): pinning that the guard re-read takes no (6) inside the body, and naming the test
  seams for residues `state_transaction` does not bracket.

### D-Refusals: existing classes only

`UserConfirmationRejectedError` for a missing or wrong sentence; `CheckpointOwnershipStateMismatchError`
for a claim that changed since it was confirmed; every other refusal is the engine's, unchanged. No new
class.

### D-Tests: deterministic, no sleeps, no process left behind

New class `TestReleaseCheckpointStartCommand` in `payload/scripts/workflow_state_test.py`, red first on
the unedited code (the new functions do not exist; the keyword is unknown; the message has no command):

1. **C1 The literal:** the exact sentence is accepted, also inside a longer message; rejected: empty; a
   stale claim reference; another work item (including an id that merely extends it, such as `wi-2` for
   `wi`); another checkpoint (`CP2` for `CP`); a missing or altered attestation, including the sentence cut before
   *and stays stopped until this release has completed*; a reordered sentence; the rejection message prints
   the expected sentence. Case: the sentence in upper case and in mixed case is accepted.
2. **C2 The observation:** `entry`, `baseline` and `released` kinds (`released` for an absent entry equal to
   an absent `HEAD` entry and for a demoted `NEEDS_REVALIDATION` entry equal to `HEAD`'s; not `released`
   when the working entry is `IN_PROGRESS` with no claim, which still raises
   `CheckpointOwnershipStateMismatchError`, nor when the entry differs from `HEAD`'s, nor when `HEAD`
   records it `COMPLETE`, which still raise the engine's refusals); the claim reference equals the token prefix; the
   guard state for none, for a leftover of an interrupted release (holder not running) and for a live
   holder (one worker of the existing live-guard mixin, killed and waited by the test); the engine's
   classification refusals pass through (another worktree's claim, no claim, an unknown id).
3. **C3 The confirmed release:** a wrong confirmation changes nothing (state, claim and guard
   byte-identical); the right one releases; a confirmation for an earlier claim of the same checkpoint
   (released, then started again) is rejected; the engine keyword refuses a claim reference that no longer
   matches with `CheckpointOwnershipStateMismatchError` and changes nothing; with `None` the engine's
   behaviour is unchanged.
4. **C4 The amendment message:** both raise sites name `/release-checkpoint-start` with the work item and
   checkpoint ids and say to run it from the worktree that holds the claim, and keep the class; the third
   raise is unchanged. Two variants pin why the qualifier is there: an `IN_PROGRESS` entry with no claim
   (the release refuses `CheckpointOwnershipStateMismatchError`) and a claim held by another worktree (the
   release refuses `CheckpointOwnedByOtherWorktreeError`).
5. **C5 End to end, a scratch repository, the command's steps in order:** start a checkpoint (claim and
   `IN_PROGRESS` entry); a merge-like commit that does not touch the checkpoint (the benign HEAD
   movement); observe; build the sentence; confirm; release; assert the entry and claim are gone,
   nothing is committed, and `request_plan_amendment` no longer raises `AmendmentCheckpointActiveError`
   for the checkpoint. A second flow: an interruption after the state write (a seam over an existing
   function, as the engine's T4 does), the observation then reports the interrupted release, the same
   command steps complete it (the sentence is asked again and a wrong one changes nothing while the claim
   exists); a commit that carries the checkpoint's trailer still refuses; a `COMPLETE` working entry refuses
   with both next steps named. A third flow, the terminal recovery, in two cases: an interruption after the
   claim unlink (a seam over the unlink: no claim, entry equal to `HEAD`'s, dead `release-start` guard) and
   the engine returning with its report lost (no claim, no guard). In both, the observation answers
   `released`, `release_checkpoint_start_confirmed` returns it without a sentence, and the state, the claim
   (absent) and the guard (left as found) are byte-identical before and after, also after a second and a
   third run; the plan-amendment request is not refused for the checkpoint.
6. **C6 The command file:** it exists and is flagged `disable-model-invocation: true`; carries the guard
   needles of the other user-only commands (the validator name, the sentence, `refuse to write anything
   unless`, `Never fabricate, infer or carry over this text`, `The agent must never invoke`); names
   `$ARGUMENTS`; carries the pre-release wording of step 3 (the needles *must be finished by running
   this command again*, *until the command has reported success* and the definition of *owner session*,
   each before the sentence is printed) and the step 2 `released` outcome (the needles *already released* and
   *the pre-release obligation is lifted*); names neither the model nor a harness; stays inside the width lint; is listed in
   `COMMAND_FILES.md` and the operator reference. The existing census tests in
   `workflow_integration_test.py` are updated in step (their counts and lists include the new command).

All run with no real-time waits; the only worker is the existing one, driven over pipes, killed and waited
by the test; the chunk runs under the Manager's orphan wrapper and reports no orphan beyond Git's own
detached maintenance.

### D-Docs: every list of user-only commands

`COMMAND_FILES.md` (seven user-only commands, the list); the operator reference (a section for the command,
its place in the inventory, and the `AmendmentCheckpointActiveError` bullet naming it); `MILESTONE_WORKFLOW.md`
(the amendment entry's refusal names the next step); `request-plan-amendment.md` (its refusal list names
it); the Orchestration Protocol (D-Protocol); `docs/common-problems.md` (the wedge: what to do, and that an interrupted release is finished by running
the command again before any session resumes the checkpoint, and that a run which reports the start
already released ends the obligation);
`docs/CONCURRENCY_INVARIANTS.md` (the claim row's recovery cell now says a command calls the function; the
known gap for #55 is closed; the release-window row states the attestation as a stated precondition that is not checked, the two routes
by which the residual stays reachable (R-i and R-ii of D-Residual) and the guardless residue;
"Last checked with: Workflow 2.19.0"); `docs/release-history.md`; `docs/RELEASING.md` only if a count it
states changes. No internal milestone id appears on a `docs/*.md` page, and no list of governing versions
is written in a managed document.

### D-Release: 2.19.0, `feat:`

`manifest.json` `workflow_version` 2.19.0; `WORKFLOW_RELEASE` and its two pinned assertions in
`workflow_protocol_test.py`; the protocol version stays. The manifest gains one `distribution` artifact
record (the command file) and its counts follow (`artifacts` 80, `distribution` 54); every changed record
gets its digest, size and an accurate `checkpoint-start-command (workflow-2.19.0)` sentence; the
`manager` block: `min_manager_version` 1.13.0 (equal to the CI pin), `conformance.suites` measured, never
typed. **The detector vocabulary of the manager block is not touched:** a user-only command file adds no
state key, ledger, phase, trailer, commit shape or capability that the closed vocabulary names, so
`signals` stays empty, as for the previous command additions.

**Downgrade posture.** The command writes only what an older release already reads: the working-tree
`WORKFLOW_STATE.json` entry restored to the state committed at `HEAD`, the removal of the claim, and a
`release-start` destructive guard of the shape any guard has. `workflow-manager update` back to 2.18.7
(minimum Manager 1.13.0) removes the command file `.claude/commands/release-checkpoint-start.md` and the
two functions and the keyword, and restores the release constant 2.18.7; the library function
`release_checkpoint_start` of 2.18.7 stays and nothing in an older release calls it. An older release does
not know the command: a start released by 2.19.0 is simply a start that is no longer there, and a start
interrupted by it is the half-released state the engine's recovery table describes, which 2.18.7 reads as
an entry equal to `HEAD`'s and a claim. **Finish an interrupted release before moving back:** a claim with a dead `release-start` guard and an
entry equal to `HEAD`'s, left in place, has no command in 2.18.7 that finishes it, so the posture and the
release-history row both say to run `/release-checkpoint-start` again to completion first. The 2.18.4
correction of the 2.14.0 limit still applies unchanged.

### D-Staging: scratch staging for CP1 (the engine plan's procedure)

CP1 changes shipped files whose digests and measured suite counts `manifest.json` records only at CP2. CP1
therefore verifies in a disposable clone under `$TMPDIR`: a scratch script recomputes `sha256` and `size`
of every `artifacts` and `templates` record whose file differs from its record, **adds the manifest record
for the new command file**, measures and rewrites `manager.conformance.suites` (digests, sizes and counts)
by the discovery `release.py manager-block --release-dir <scratch> --write` uses, commits it in the clone,
and runs the "Verification commands" blocks from there. No rationale is touched in the scratch.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
| --- | --- | --- |
| OD-1 | The version | **Minor 2.19.0, `feat:`**, the owner's row 24c: a user-visible command is added. |
| OD-2 | The residual | **(a), the attestation inside the literal plus the observed probe, which diverges from the engine plan's "check" requirement and does not close the residual:** it makes the demoted-and-re-started case a breach of a stated precondition, reachable by a broken true attestation (R-i) or a false one (R-ii). (b) needs a second concurrency mechanism (D-Residual). A fence stays a candidate row if the owner wants those two routes closed by construction. |
| OD-3 | Protocol addition or documentation only | **Documentation only; protocol unchanged** (D-Protocol). |
| OD-4 | The claim reference | **`owner_token[:12]`**, shown to the person, checked as an exact token inside a fixed sentence. The takeover literals bind `claim_observation_id` (the sha256 of the exact record bytes) under exact equality because they authorise acting on one observed byte state; this literal confirms *which claim* a person was shown, which the owner token names. A claim that is re-created, an adoption included (`adopt_claim` builds a new record through `_build_claim_record`, which mints a fresh token), carries a different reference, so a confirmation given for the earlier claim cannot release it; the engine's compare under its lock (D-Engine-Keyword) is on the token, not the bytes. |
| OD-5 | Benign HEAD movement | **No engine change**: the engine already walks `start_commit..HEAD` for a checkpoint commit. Pinned at command level. |
| OD-6 | The manager CI pin | **No change** (1.13.0 equals `min_manager_version`). |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does not exist in
this repository's release source).

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The command, its confirmation, the amendment message and their tests | - | 3 | 1 |
| CP2 | Release 2.19.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The command, its confirmation, the amendment message and their tests

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`,
`payload/scripts/workflow_integration_test.py`, `payload/.claude/commands/release-checkpoint-start.md`,
`payload/.claude/commands/request-plan-amendment.md`, `payload/docs/ai-workflow/COMMAND_FILES.md`,
`payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
`payload/docs/ai-workflow/MILESTONE_WORKFLOW.md`.

- **Tests first, red first** (D-Tests): C1 to C6 are written and run against the unedited code; the
  failures are recorded (the functions, the keyword and the command file do not exist; the message names no
  command). **Done:** the recorded failures name each new test.
- **The code** (D-Engine-Keyword, D-Functions, D-Literal, D-Amendment-Message): the keyword, the
  observation, the confirmed release, the sentence builder and validator, and the two message additions,
  placed beside `release_checkpoint_start` and `validate_user_only_confirmation`. **Done:** `git diff` of
  `workflow_state.py` is those and nothing else; no lock, guard, claim, `os.link` or `flock` site is added;
  the engine without the keyword behaves as before; `TestGlobalLockOrderItem372h` passes unedited.
- **The command file** (D-Command) and the lists (D-Docs, payload part): `COMMAND_FILES.md`, the operator
  reference, `MILESTONE_WORKFLOW.md`, `request-plan-amendment.md`, and the census tests of
  `workflow_integration_test.py`. **Done:** the integration suite passes with the new command counted
  everywhere it counts commands.
- The Orchestration Protocol document and `docs/` pages are CP2; `docs/ROADMAP.md` row 24c is `Current`
  from this plan and this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites, the new class and the whole
`workflow_state_test.py` chunk under the Manager's orphan wrapper, the `tools/release` and `tools/docs`
tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.19.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`,
`docs/release-history.md`, `docs/RELEASING.md`, `docs/CONCURRENCY_INVARIANTS.md`,
`docs/common-problems.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.19.0 with its two pinned assertions in `workflow_protocol_test.py` and the
  matching `ORCHESTRATION_PROTOCOL.md` edits (tested releases list, envelope example, protocol note, and
  the one sentence of D-Protocol); the protocol version stays.
- `manifest.json` 2.19.0: `workflow_version`; the new `distribution` record for the command file; counts;
  `sha256` and `size` of every changed record; an accurate `checkpoint-start-command (workflow-2.19.0)`
  sentence on **each** changed record, true of THAT file and read against `git diff ad1121a..HEAD -- <file>`;
  the `manager` block per D-Release, `conformance.suites` measured by `release.py manager-block
  --release-dir <scratch> --write` from a staging of CP2's own content.
- `docs/release-history.md`: the 2.19.0 row (closes #55; names the command, the literal, the attestation,
  the amendment message, the residual as a breach of an attested precondition with its two routes, and the way back, which says to finish an interrupted release first) and the "Last checked with" line;
  `docs/RELEASING.md`: any count it states follows the measured count; `docs/CONCURRENCY_INVARIANTS.md` and
  `docs/common-problems.md` per D-Docs.
- `tools/release/release_test.py`: a 2.19.0 release class (version, release constant, counts (80, 6), the
  posture and history needles); the 2.18.7 class keeps what stays true of that release and no longer pins
  the current version, constant, counts or posture.
- `docs/ROADMAP.md` is not written by this checkpoint: row 24c becomes Done at acceptance, with #55 closed.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture;
`release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #55, the command | `/release-checkpoint-start`, the literal, the observation, the keyword, the amendment message | CP1 | D-Command, D-Literal, D-Engine-Keyword |
| The engine's residual | Not closed: (a) makes it a breach of an attested precondition (observed probe plus the attestation); two routes stay reachable (R-i, R-ii); diverges from the engine plan's "check" wording | CP1, CP2 | D-Residual, OD-2 |
| The terminal recovery | Kind `released` of the observation: an interrupted release whose claim is gone ends in a read-only success that lifts the obligation (EPR-001) | CP1 | D-Residual, D-Command step 2 |
| Lists of user-only commands | `COMMAND_FILES.md`, operator reference, `MILESTONE_WORKFLOW.md`, `request-plan-amendment.md`, protocol sentence, common problems | CP1, CP2 | D-Docs, D-Protocol |
| #97, guardless residue | Row in the concurrency page | CP2 | docs only |
| #97, benign HEAD movement | Engine already widened; pinned through the command | CP1 | OD-5 |
| #97, `COMPLETE` next step | Engine already names both; pinned and repeated in the docs | CP1 | D-Followups |
| Release | 2.19.0 bookkeeping, closes #55 | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/checkpoint-start-command-artifacts.json` is generated
by `workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its
plan-stage protected paths, and self-review checked that every path named in a Files paragraph, and every
other path this plan names (`docs/ROADMAP.md`, `docs/RELEASING.md`, `docs/release-history.md`,
`docs/CONCURRENCY_INVARIANTS.md`, `docs/common-problems.md`), is classified at both stages and that every
deliverable is protected at the implementation stage.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands", and the manifest key is
`workflow_version`. Each flow names its workspace.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | a scratch repository (the test harness's `ScratchRepo`) | the command's steps in order: observation shown, wrong sentence refused, right sentence releases; entry and claim gone, nothing committed |
| f2 | the same scratch repository | an interruption after the state write; the observation reports it; the second run completes; an interruption after the claim unlink ends in the `released` outcome with nothing written; a commit carrying the checkpoint's trailer refuses |
| f3 | the same scratch repository | a stale sentence (an earlier claim) is rejected; `request_plan_amendment` is no longer refused after the release, and its refusal before names the command |
| f4 | the staged conformance fixture of the candidate | the `workflow_state_test.py` chunk under the Manager's orphan wrapper reports no new orphan |
| f5 | the staged conformance fixture of the candidate (`stage-conformance`) | the nine suites, `tools/release` (zlib-ng environment) and `tools/docs`, `check-manager-block` |
| f6 | the checkout | the seven-command user-only lists, the concurrency page and the release-history row agree |

## 8. Disposition of the local plan review, round 1 (REVISE; revision 1 to 2)

| Finding | Disposition | Where |
| --- | --- | --- |
| LPR-001 (the interruption guard rests on a message a crashed call never prints) | **Accepted.** The obligation moves before the release and into the attestation: the literal ends *and stays stopped until this release has completed*; step 3 prints the interruption wording before asking; step 6 keeps only the interruptions that return a refusal; C1 and C6 gain needles; `docs/common-problems.md` states it. | D-Residual, D-Literal, D-Command, D-Tests, D-Docs |
| LPR-002 (overstated closure; owner session undefined) | **Accepted.** (a) is worded as a breach of an attested precondition, the divergence from the engine plan's "check" requirement is stated, both routes (R-i, R-ii) are listed, *owner session* is defined, and the same wording goes to the concurrency page. | D-Residual, OD-2, section 6, D-Docs |
| LPR-O1 (amendment message's next step) | **Accepted.** "From the worktree that holds the claim", with both refusals named; two C4 variants. | D-Amendment-Message, D-Tests C4 |
| LPR-O2 (downgrade with an interrupted release) | **Accepted.** Finish an interrupted release before moving back. | D-Release |
| LPR-O3 (token prefix vs observation id) | **Accepted.** One sentence in OD-4. | OD-4 |
| LPR-O4 (case sensitivity) | **Accepted.** Case-insensitive, as `validate_user_only_confirmation`; C1 pins it. | D-Literal, D-Tests C1 |

## 9. Disposition of the manual external plan review, round 1 (REVISE; revision 2 to 3)

| Finding | Disposition | Where |
| --- | --- | --- |
| EPR-001 (an interrupted release whose claim is already gone can never satisfy the command's success requirement) | **Accepted; validated against the engine.** `_classify_checkpoint_start` looks for the claim first and, finding none while the entry is not `IN_PROGRESS`, raises `CheckpointNotInProgressLocallyError`, so every retry after the claim unlink refuses before any report. The observation gains the terminal kind `released` (no claim, entry equal to `HEAD`'s): a read-only success that asks for no sentence and lifts the pre-release obligation; the attestation is still required for as long as a claim exists; the engine is not edited for it. D-Residual's recovery description covers both the present and the absent claim; step 6 and the pre-release wording name both outcomes; C2, C5 (a third flow, two cases) and C6 pin it. | D-Residual, D-Functions, D-Command, D-Tests, D-Docs, section 7 |
| EPR-002 (OD-4 misdescribes adoption) | **Accepted.** `adopt_claim` mints a fresh token through `_build_claim_record`; the parenthetical is corrected, the conclusion stands. | OD-4 |
