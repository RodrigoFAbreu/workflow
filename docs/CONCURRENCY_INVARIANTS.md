# Concurrency invariants

> For: maintainers who change a lock, claim, guard, journal or lease in the Workflow's scripts. Last checked with: Workflow 2.19.0.

This page lists, in one table, every primitive that serializes Workflow
processes or records who owns a piece of work. Every cell comes from the
release source. `file:function` names a function in `payload/scripts/`, or a
step of a command file in `payload/.claude/commands/`. A test is
`file::class` in `payload/scripts/`. A cell the code does not settle says
"not verified".

## How to read this

**Scopes.**

- **Repository-wide**: one object under
  `$(git rev-parse --git-common-dir)/ai-workflow/`, shared by every linked
  worktree (`workflow_state.py:claims_dir`, `identity_gap_lock_path`).
- **Work-item-wide**: a repository-wide object keyed by `sha256(work_item_id)`
  in `<git-common-dir>/ai-workflow/checkpoint-claims/` (`claim_path`,
  `guard_path`, `guard_mutation_lock_path`, `lifecycle_lock_path`,
  `amendment_witness_path`).
- **Worktree-local**: under the worktree's own gitignored `.ai-review/`, and
  invisible to other worktrees (`state_lock_path`,
  `identity_document_lock_path`, `plan_approval_journal_path`,
  `plan_approval_guard_path`). `WORKFLOW_STATE.lock` is per worktree
  (`claim_checkpoint` docstring).
- **Process-local**: the memory of one Python process (`_state_lock_held`,
  `_held_primitives`, `_guard_holder_locks`).

**Kinds, and what a crash leaves behind.**

- A **flock** is `fcntl.flock(LOCK_EX)` on a file that is created once and
  never unlinked. A contender blocks until the holder releases it. The
  kernel releases it when the holder dies, so a crash leaves only the empty
  lock file.
- A **link record** is a complete temp file published with `os.link`
  (`_publish_claim_exclusive`, `_publish_plan_approval_guard`,
  `open_plan_approval_journal`). On `EEXIST`, someone else won. A contender
  is refused, never blocked. A crash leaves the record in place until a
  named route removes it.
- A **holder lock** is a non-blocking `fcntl.flock(LOCK_EX | LOCK_NB)` that
  the holder of a guard keeps on the guard's own inode for the whole window
  (`_publish_claim_exclusive` with `lock_lease_id`, taken before the
  `os.link`; `_publish_plan_approval_guard`). It is not a numbered primitive:
  nobody waits on it and it takes nothing else. A later process asks it with
  a non-blocking shared `flock` (`_guard_held_by_another_process`). The
  kernel drops it when the holder dies, so a crash leaves the guard with no
  lock. A replaced guard is a new inode, so a displaced holder's lock never
  makes the new guard look live. A `fork`ed child closes the descriptors it
  inherits and owns none (`_forget_inherited_guard_locks`).
- A **replace record** is a temp file published with `os.replace`. It is
  complete or the previous one, and it serializes nothing.

**Epochs.** An epoch is an `owner_token`. `_build_claim_record` mints it for
a claim and `open_plan_approval_journal` for a journal. Only a takeover or a
recovery rotates it. A guard whose `holder_owner_token` is not the current
token belongs to a superseded epoch. The next acquirer reclaims it with no
authorization (`_acquire_guard_locked`,
`_acquire_plan_approval_guard_locked`).

**Step classes.** Every guard names a `step` and a class, `ORDINARY` or
`DESTRUCTIVE` (`GUARD_STEP_CLASSES`, and `plan_approval_step_class` for the
journal). An authorized takeover may break an ordinary guard whose
`lease_id` it quoted. It never breaks a destructive one. The checkpoint
steps `1d` and `1f-commit` are destructive (`milestone-implement.md` steps
1d and 1f), and so is `release-start` (`release_checkpoint_start`). `1f-release`, `takeover` and `recover-abandoned-guard` are
ordinary (`release_checkpoint`, `_take_over_claim_window`,
`recover_abandoned_destructive_guard`). The journal's steps are listed in
`PLAN_APPROVAL_DESTRUCTIVE_STEPS` and `PLAN_APPROVAL_ORDINARY_STEPS`.

**Numbers and edges.** (1) to (9) are the code's own primitive numbers: the
first argument of `_primitive_held` and `_note_primitive_acquired`. They
match the list in "The complete global partial order" of
`payload/docs/ai-workflow/WORKFLOW_V2_PLAN.md`. The edge X→Y means that Y is
acquired while X is held, in the order the code takes them; the specification's graph leaves out the release-time edges (5)→(6) and (1)→(7) listed in the rows below. "Command order" marks an edge that comes from the
order of a command file's steps, not from the module.

## The table

| Primitive and code | Scope | Who may acquire, with what proof | Who may take it over, with what proof | Lock order | A crashed holder leaves | Recovery route | Tests |
|---|---|---|---|---|---|---|---|
| **(2) State lock**, `.ai-review/runtime/WORKFLOW_STATE.lock`. `workflow_state.py:state_lock`, `state_transaction`. Shared read: `workflow_protocol.py:read_state_and_config` | Worktree-local: every writer of this worktree's `WORKFLOW_STATE.json` | Any process, no proof. It blocks. A nested acquisition in the same process raises `StateLockReentrancyError` (`state_lock`). Protocol reads take `LOCK_SH`, and read unlocked when the file is absent (`read_state_and_config`) | Nobody: "a live holder is never displaced" (the module comment above `STATE_LOCK_PATH`) | (9)→(2) (`claim_checkpoint`, `request_plan_amendment_transaction`). (5)→(2) and (8)→(2) at steps 1d and 1f (command order, `milestone-implement.md`); (5)→(2) is also taken by code, in the window of `release_checkpoint_start`. (2)→(8): the claim is published under it (`claim_checkpoint`). The specification's (1)→(2) at step 8b is not taken in the code: `materialize_plan_approval_state` writes without `state_lock`, and `approve-review.md` step 4c names this write the one exception | The lock file. The state file holds the old or the new bytes (`_publish_state_file`, one `os.replace`) | None needed: the kernel releases the lock | `workflow_state_completion_obligations_test.py::TestStateLock`; `workflow_state_test.py::TestStateTransactionOnFailure`, `::TestConcurrentManualVerdictIngests`; `workflow_protocol_test.py::TestResolveArtifact`, `::TestWorkflowExceptionDomain`. That the shared read excludes a writer: not verified, no test |
| **(3) Identity lock**, `.ai-review/runtime/WORKTREE_IDENTITY.lock`. `identity_document_lock`, held by `write_worktree_identity` and `repair_worktree_identity` | Worktree-local: the one `WORKTREE_IDENTITY.json`, which holds every work item's entry | Any writer of that document, no proof | Nobody | (5)→(3) (`_take_over_claim_window` through `_establish_or_repair_identity`; step 1d). (8)→(3) (step 1d, command order). (9)→(3) (absent-claim `take_over_claim`). A leaf: never held across a state write (`identity_document_lock` docstring) | The lock file. The document holds the old or the new bytes (`_publish_worktree_identity`) | None for the lock. An undecidable document is repaired only by a takeover or recovery literal that carries the repair clause (`_identity_repair_clause`, `repair_worktree_identity`) | `workflow_state_test.py::TestIdentityDocumentSerialization` |
| **(4) Identity-gap lock**, `<git-common-dir>/ai-workflow/identity-gap.lock`. `identity_gap_lock`, used by `authorize_identity_reference_gap`; its record is published by `_publish_identity_gap_authorization_exclusive` | Repository-wide: one lock for all work items. It serves work-item creation, before any claim exists | The caller of `authorize_identity_reference_gap`, with the user literal from `identity_reference_gap_authorization_literal`, bound to the evidence | Nobody | Isolated: never held with (2), (3) or (5), and none of them is taken under it (`identity_gap_lock` docstring). `TestGlobalLockOrderItem372h` derives no edge for it | The lock file. A record is complete or absent (`os.link`) | None for the lock. A record is durable by design: its `EEXIST` is the replay check. `mark_identity_reference_gap_consumed` marks it consumed | `workflow_state_test.py::TestAuthorizeIdentityReferenceGap` (the record). Contention on the lock: not verified, no test |
| **(9) Lifecycle lock**, `checkpoint-claims/<sha256>.lifecycle.lock`. `lifecycle_lock` | Work-item-wide: every worktree of the repository | Any process that holds no other primitive; otherwise `LifecycleLockOrderError`. No proof. Taken by `claim_checkpoint`, `adopt_claim`, absent-claim `take_over_claim`, `request_plan_amendment_transaction`, `reserve_amendment_resolution`, `assert_amendment_resolution_held`, `advance_amendment_witness`, `release_amendment_resolution` and `_clear_witness` | Nobody | A pure source, acquired first or alone: (9)→(2), (8), (6), (5), (3). Refused inside a `plan_approval_guarded_mutation` window, because (1) is then in the held set | The lock file | None needed | `workflow_state_test.py::TestLifecycleLockIsAPureSource`, `::TestCrossWorktreeAmendmentClaimRaceIsClosed`, `::TestAmendmentClaimRaceRealProcesses`, `::TestAmendmentWitnessCrashRecovery` (a killed holder) |
| **(8) Checkpoint claim**, `checkpoint-claims/<sha256>.json`. `claim_checkpoint`, `adopt_claim`, `_claim_or_refuse`, `assert_claim_owner`, `release_checkpoint` | Work-item-wide: at most one claimed checkpoint per work item in the repository | `claim_checkpoint` at step 1d, under (9) and (2), after the amendment-witness check, in `CHECKPOINT_START_LEGAL_PHASES` when the work item has a state entry (with no entry the phase check is skipped and the lifecycle check stays: `workflow_state_test.py::TestRequestPlanAmendment.test_claim_checkpoint_with_no_state_entry_is_unaffected`). It publishes with `os.link`: another worktree's claim refuses (`CheckpointOwnedByOtherWorktreeError`); the same worktree and checkpoint is idempotent. `adopt_claim` only for a checkpoint already `IN_PROGRESS` in this worktree's state, with origination proven (`checkpoint_origination_provable`, checked again under (6)). From then on the proof is the minted `owner_token`, compared by `assert_claim_owner` | `take_over_claim` (the claim-takeover row) or `recover_abandoned_destructive_guard`. Both rotate the claim with `os.rename` (`_publish_claim_replacing`) | Published under (9) and (2), and under (6) in `adopt_claim`. Held from step 1d to step 1f: (8)→(5), (6), (2), (3) (command order). `release_checkpoint` unlinks it inside a (5) window | The claim file | In its own worktree, step 1c (`resolve_checkpoint_ownership`): `RESUME`, `CONTINUE_CLAIM` (a claim with no state write), or the one automatic release, when the checkpoint is `COMPLETE` at `HEAD`. From another worktree: `take_over_claim`. An `IN_PROGRESS` start with no commit: the user-only `/release-checkpoint-start` calls `release_checkpoint_start_confirmed` (the release-window row) | `workflow_state_test.py::TestCheckpointClaimRecord`, `::TestClaimAdoption`, `::TestResolveCheckpointOwnership`; `workflow_acceptance_matrix_test.py::CheckpointOwnership` |
| **(5) Checkpoint mutation guard**, `checkpoint-claims/<sha256>.lease`. `acquire_guard`, `_acquire_guard_locked`, `owner_mutation`, `release_guard`, `_release_guard_path_locked` | Work-item-wide: one guard per work item, held for one mutation window. Its steps: `1d`, `1f-commit` and `release-start` (destructive); `1f-release`, `takeover` and `recover-abandoned-guard` (ordinary) | `owner_mutation(T)`: `role="owner"`, with the claim's token and this worktree's git dir, then `assert_claim_owner(T)` under the guard. When the guard is held: a superseded epoch (the guard's token is not the claim's, or there is no claim) is reclaimed with no proof. The owner's own leftover (same token, same worktree, step not `takeover`) is reclaimed only when no other process holds the guard's lock; otherwise it is refused with `CheckpointOwnershipUnavailableError`. A `takeover` guard carrying the caller's token and worktree is refused. The same token from another worktree is refused. To ask whether a window of a work item is running now, call `guard_holder_is_running(repo_root, work_item_id)`: `True` when another process holds the published guard's lock, `False` when no guard is published or its holder holds no lock (crashed, or published by a release before 2.18.6), and it raises on an undecidable guard, never `False`. It takes (6) as a leaf and writes nothing | `role="takeover"`: an ordinary guard only, and only the exact `lease_id` the guard-release literal quoted; a destructive guard is refused. `role="recovery"`: a destructive guard whose holder worktree is deregistered (`recover_abandoned_destructive_guard`) | Published under (6): (6)→(5). `release_guard` also takes (6) while (5) is still recorded as held: (5)→(6), which the specification's graph does not draw. Inside a window: (5)→(2) and (5)→(3). Targets: (8)→(5), (9)→(5). One guard per session at a time: stated by the `owner_mutation` docstring; not enforced by the code, not verified | The `.lease` file, naming its `lease_id`, token, holder worktree git dir, step and class, with no lock on it | By case. The owner's own leftover: re-enter from that worktree, with no other step (a live holder is refused: wait for its window, or stop the process `fuser <guard path>` names). A superseded epoch: the next acquirer reclaims it. A leftover `takeover` guard: re-run `take_over_claim` with the guard-release literal. A destructive guard of a deregistered worktree: `recover_abandoned_destructive_guard`. An undecidable guard: `clear_malformed_guard`. A destructive guard of a registered worktree: only that worktree | `workflow_state_test.py::TestCheckpointMutationGuard`, `::TestTakeoverGuardIsNotTheOwnersToReclaim`, `::TestGuardFailureSurfaceItem372`, `::TestSameWorktreeConcurrencyRealProcesses`, `::TestLiveGuardVisibility` (two real processes, the probe, the fork cases, descriptor hygiene) |
| **(6) Checkpoint guardlock**, `checkpoint-claims/<sha256>.guardlock`. `guard_mutation_lock` | Work-item-wide, held for a few syscalls | `acquire_guard`, `_release_guard_path`, `clear_malformed_guard` and `adopt_claim`. No proof | Nobody | (6)→(5), and (6)→(8) in `adopt_claim`. At release the order reverses: (5)→(6) in `release_guard`. Targets: (8)→(6), (9)→(6). Never held across a state write (`guard_mutation_lock` docstring) | The lock file | None needed | `workflow_state_test.py::TestGuardFailureSurfaceItem372` (publish exclusivity without the lock), `::TestRealProcessConcurrentTakeover` |
| **Checkpoint-start release window**, `release_checkpoint_start`, with `_classify_checkpoint_start`, `_checkpoint_entry_at` and `_assert_no_commit_past_start` | Work-item-wide: releases the one uncommitted start of a work item in this worktree, and nothing else. It writes the working-tree `WORKFLOW_STATE.json` and removes the claim; it commits, stages and fabricates nothing | I1: a start is removed (entry first, claim second) only inside one window in which this process holds (9) and a live `release-start` guard, after proving under the guard that no window of the work item is running (`guard_holder_is_running`, asked before the guard is opened) and that no commit since the start carries the checkpoint's `Workflow-Checkpoint` trailer or records it other than as `HEAD` does. The claim must be this worktree's, for this checkpoint, with the observed token. Every refusal is an existing class (`CheckpointNotInProgressLocallyError`, `CheckpointOwnershipStateMismatchError`, `CheckpointOwnedByOtherWorktreeError`, `CheckpointOwnershipUnavailableError`) and changes nothing | Nobody: the guard is destructive, so no takeover breaks it | (9)→(6)→(5), as any owner window. (5)→(2) by `state_transaction` inside the window, a code-derived edge declared in `verify_372h_raw_edge_derivation.py`. The probe takes (6) as a leaf, before (5) is opened. At release, (5)→(6) as in `release_guard`. The claim's unlink is gated by a re-read of the claim and of the guard and is declared to the lock-primitive predicate (`MUTATION_UNCONDITIONAL_RELEASE_START`) | Interrupted before the state write: the entry, the claim and a guard with no holder lock. After the state write: the claim and the guard, the entry equal to the state at `HEAD`. After the unlink: only a guard with no claim. After the guard's release: nothing | Run `/release-checkpoint-start` again, before any session resumes the checkpoint: the engine re-classifies under (9) and, while a claim exists, asks for the same attestation with the fresh claim; once the claim is gone it reports the start already released and the obligation ends. The command (`release_checkpoint_start_confirmed`) runs the engine only after the user supplies the claim-bound sentence, which attests that the owner session is stopped. **That attestation is a stated precondition, not a check:** the disk cannot show an owner session that is alive and idle (the claim records no process), so the command checks only the running window (`guard_holder_is_running`). **Not fenced between the interruption and the next run, by two routes (R-i, a true attestation broken: an owner session is started before the command is run again and completed; R-ii, a false attestation: the owner was alive and idle):** the dead guard has no holder lock, so the owner reclaims it as its own leftover and may complete the checkpoint. A checkpoint `HEAD` never recorded then loses only its `start_commit` (harmless). A demoted and re-started one commits `COMPLETE` with the old `start_commit`; the checkpoint has two completion commits and `discover_checkpoint_commits` raises `AmbiguousCheckpointTrailerError`. No recovery in this release; the command makes it a breach of the attested precondition and does not close it. **Guardless residue:** a recovery crash between deleting the old guard and publishing its replacement leaves the claim and the restored baseline entry with no guard; another run completes the release, and an owner entry in that interval falls within the same attested precondition | `workflow_state_test.py::TestReleaseCheckpointStart` (T1 to T11, T9 pins the residual at each case), `::TestGlobalLockOrderItem372h` |
| **Claim takeover**, `take_over_claim`, `takeover_evidence`, `_take_over_claim_window` | Work-item-wide | Any worktree, in five steps. (1) `takeover_evidence` records `claim_observation_id` (the claim bytes' sha256, or `absent`), the guard and whether each holder worktree is registered. (2) The user literal `takeover_authorization_literal` names that observation, the held checkpoint and the target checkpoint, plus a repair clause for an undecidable identity document. If a guard was observed, `guard_release_authorization_literal` is also required; a destructive guard is refused. (3) `acquire_guard(role="takeover", step="takeover", ORDINARY)` with the observed token. (4) Under the guard, the claim is observed again; any change refuses. (5) Identity is written, then the claim is published with a fresh token, `takeover_count + 1` and `previous_owner_tokens` | A second takeover that quotes the first takeover's `lease_id` (Known gaps, #85) | Absent claim: (9)→(6)→(5)→(3). Existing claim: no (9), because the amendment side already refuses while any claim exists (`take_over_claim` docstring) | Before the rotation: a `takeover` guard carrying the old token and the taker's worktree, and the claim unchanged. After it: the new claim | Re-run the takeover with fresh evidence and both literals (the refusal message of `_acquire_guard_locked`). The displaced owner's next `assert_claim_owner` refuses | `workflow_state_test.py::TestExplicitTakeover`, `::TestRealProcessConcurrentTakeover`, `::TestTakeoverGuardIsNotTheOwnersToReclaim`, `::TestAbandonedDestructiveGuardRecovery` |
| **Amendment witness and resolution reservation**, `checkpoint-claims/<sha256>.amendment.json`. `request_plan_amendment_transaction`, `reserve_amendment_resolution`, `advance_amendment_witness`, `release_amendment_resolution`, `_evaluate_lifecycle` | Work-item-wide. A gate that can only refuse; committed Git state stays the authority (the section comment above `AMENDMENT_WITNESS_SCHEMA_VERSION`) | Written only under (9) (`_publish_amendment_witness` asserts it). `OPEN`: `request_plan_amendment_transaction`, after `request_plan_amendment` refuses an `IN_PROGRESS` checkpoint or any claim. `RESOLVING`: `reserve_amendment_resolution` at `/approve-review plan` step 4d, recording the journal's `owner_token` | A reservation passes with a journal takeover: the old token still counts through `previous_owner_tokens` (`assert_amendment_resolution_held`, `_journal_tokens`). No other route | A replace record written under (9); not a numbered primitive | An `OPEN` witness without its state entry, or a `RESOLVING` witness without a commit | The next entry point that calls `_evaluate_lifecycle` under (9) runs the predicate list (not every holder of (9) does: `assert_amendment_resolution_held` runs no list and never writes the witness): it advances to `RESOLVED` or rolls back a provable orphan. After a rollback at step 6b: `release_amendment_resolution`. When the orphan test cannot decide: the evidence-bound literal through `clear_amendment_witness` or `clear_amendment_resolution` | `workflow_state_test.py::TestAmendmentWitnessCrashRecovery`, `::TestAmendmentResolutionReservation`, `::TestRepoGlobalLifecycleClaimAndAmendment`, `::TestRequestPlanAmendment`; `workflow_acceptance_matrix_test.py::RepoGlobalLifecycleAcrossWorktrees` |
| **Plan-approval journal**, `.ai-review/runtime/PLAN_APPROVAL_JOURNAL.json`, with `PLAN_APPROVAL_JOURNAL.claim.<T>` and `PLAN_APPROVAL_OWNER.<T>.json`. `open_plan_approval_journal`, `assert_plan_approval_journal_owner`, `take_over_plan_approval_transaction`, `_replace_plan_approval_journal`, `rollback_plan_approval_transaction`, `close_plan_approval_journal` | Worktree-local: one journal per worktree, for any work item. The code calls it "repository-wide" in the sense of "not per work item" | `/approve-review plan` step 4c. It publishes with `os.link`, so a second open is refused (`PlanApprovalTransactionInProgressError`). It is refused while the item has an open amendment and a live claim (`AmendmentCheckpointActiveError`). From then on the proof is the journal's `owner_token`, read again by `assert_plan_approval_journal_owner` in every guarded window | `take_over_plan_approval_transaction`. The journal's work item must be the caller's. The user literal names the owner token and `step_seq`; a held guard also needs the guard-release literal, and a destructive guard is refused. The journal is `os.link`ed onto `.claim.<T>`: an existing link is removed and made again once while the journal still names `T`, and refused once it names another token. Then the guard with `role="takeover"`, a re-check of the token, `step_seq` and `updated_at`, and a rotation by `os.replace` | Spans invocations and holds no flock. Its windows are (1)'s | The journal, possibly the owner-progress record, a `.claim.<T>` link and the guard (1). A successful takeover also leaves the old epoch's `.claim.<T>` and `PLAN_APPROVAL_OWNER.<T>.json`; no code removes them | Re-run `/approve-review` for the same work item. Step 4b reports the journal; only the takeover literal (and the guard-release literal) resumes it, at step 6a: forward completion, or the rollback at step 6b (`approve-review.md` step 4b) | `workflow_integration_test.py::TestPlanApprovalFailureAtomicityTransaction`, `::TestPlanApprovalMutationGuardAndTakeover`; `workflow_acceptance_matrix_test.py::PlanApprovalTransactionRecovery` |
| **(1) Plan-approval guard**, `.ai-review/runtime/PLAN_APPROVAL_MUTATION.lease`. `acquire_plan_approval_guard`, `_acquire_plan_approval_guard_locked`, `plan_approval_guarded_mutation`, `release_plan_approval_guard` | Worktree-local: one guard for the one journal | `role="owner"` with the journal's token. When the guard is held: a superseded epoch (the guard's token is not the journal's, or there is no journal) is reclaimed. The owner's own leftover (same token, step not `takeover`) is reclaimed only when no other process holds the guard's lock; otherwise it is refused with `PlanApprovalGuardHeldError`. A `takeover` guard carrying the caller's token is refused. The guard records no worktree. The rollback (`rollback-index-reset`) acquires it directly (`approve-review.md` step 6b) | `role="takeover"`: an ordinary guard only, and only the exact `lease_id` quoted | (7)→(1). At release `release_plan_approval_guard` takes (7) while (1) is still recorded as held: (1)→(7), which the specification's graph does not draw. (1)→(2) is declared by the specification but not taken (see (2)). (9) is refused inside it | The `.lease` file, with no lock on it | The owner's own leftover: owner re-entry (a live holder is refused: wait, or stop the process `fuser` names). A leftover ordinary or `takeover` guard: re-run the takeover with the guard-release literal. A destructive guard of the current epoch: no in-band route; it is removed by hand once the holder is independently known to be gone (the section comment above `PLAN_APPROVAL_GUARD_PATH`) | `workflow_integration_test.py::TestPlanApprovalMutationGuardAndTakeover`, `::TestPlanApprovalGuardCarriesNoWorkItemLiteral`, `::TestLiveGuardVisibilityJournal` |
| **(7) Plan-approval guardlock**, `.ai-review/runtime/PLAN_APPROVAL_MUTATION.guardlock`. `_plan_approval_guard_lock` | Worktree-local, held for a few syscalls | `acquire_plan_approval_guard` and `release_plan_approval_guard`. No proof | Nobody | (7)→(1); (1)→(7) at release | The lock file | None needed | No test names it: not verified. The edge (7)→(1) is checked by `workflow_state_test.py::TestGlobalLockOrderItem372h` |
| **Plan-stage bundle generation**, `.ai-review/<id>/current.staging-<token>/` and `.pin.staging-<token>/`. `prepare-ai-review.sh` (plan stage), `workflow_fingerprint.py:finalize_staged_plan_bundle_generation`, `_promote_plan_stage_staging`, `remove_leftover_plan_stage_staging` | Worktree-local, per work item | Any process, no lock and no proof: each generation has a random staging token | Nobody | None of (1) to (9) | Staging directories, or `current.old-<token>` and `.pin.old-<token>` in the middle of a promotion. The renames are not atomic as a set (`_promote_plan_stage_staging` docstring) | The next plan-stage generation removes every leftover (`prepare-ai-review.sh`, `remove_leftover_plan_stage_staging`). A half-promoted bundle is refused by the bind verifier (`_promote_plan_stage_staging` docstring). The verifier rejects a missing manifest, disagreeing bundle ids among manifest, current and archive, and drift of the fresh content; that it rejects at every interrupted-promotion boundary is not verified. The implementation stages generate in place (`prepare-ai-review.sh` comment) | `workflow_fingerprint_generalization_test.py::TestPrepareAiReviewShPlanStageStaging`; `workflow_acceptance_matrix_test.py::PlanReviewGeneratorRecovery` |
| **Held set**, `_state_lock_held` and `_held_primitives`. `_primitive_held`, `held_primitives`. The holder locks of the guards this process holds are kept apart, in `_guard_holder_locks` | Process-local; not thread-local (comment above `_state_lock_held`) | Recorded automatically: the flocks (2), (3), (4), (6), (7) and (9) for their `with` block, and the guards (1) and (5) from publication to release | Not applicable | It enforces the reentrancy refusal of (2) and the pure-source refusal of (9). A guard published by an earlier invocation is not in a later process's set | Nothing | Not applicable | `workflow_state_completion_obligations_test.py::TestStateLock` (nested acquisition); `workflow_state_test.py::TestLifecycleLockIsAPureSource`, `::TestGlobalLockOrderItem372h` |

## Known gaps

- **A claim takeover can break a live takeover's window**
  ([#85](https://github.com/RodrigoFAbreu/workflow/issues/85), its note on
  the multi-worktree table). `_acquire_guard_locked` lets `role="takeover"`
  reclaim any ordinary guard whose `lease_id` was quoted, including a live
  takeover's own `takeover` guard. `_take_over_claim_window` does not check
  its guard again before `_publish_claim_replacing`. This needs a human to
  quote a live lease, so the issue records it as a note, not a defect. The
  note says the journal is serialized by its per-epoch `.claim.<T>` link. In
  the code, `take_over_plan_approval_transaction` removes and re-makes an
  existing `.claim.<T>` while the journal still names `T`, which is also
  true of a live takeover before its rotation. That part of the note is not
  verified: before the rotation, the journal appears to rely on its guard
  alone, as the claim does.
- **The release of an uncommitted checkpoint start rests on an attestation.**
  `/release-checkpoint-start` closes
  [#55](https://github.com/RodrigoFAbreu/workflow/issues/55) (the wedge of
  `/request-plan-amendment`), but it does not fence the owner session between
  an interruption and the next run: the person attests that the owner session
  is stopped, and nothing on disk can check it. The demoted and re-started
  checkpoint (`AmbiguousCheckpointTrailerError`) stays reachable by R-i and
  R-ii (the release-window row). A fence that removes both by construction
  needs an owner heartbeat or a fence on the dead guard, a new mechanism.
- **Concurrency within one worktree is only partly fenced.**
  A second process of the same owner is now refused beside a live holder of
  a guard (`workflow_state_test.py::TestLiveGuardVisibility`,
  `workflow_state_test.py::TestSameWorktreeConcurrencyRealProcesses`). What
  remains: threads of one process are not told apart (the holder-lock table
  and `_held_primitives` are not thread-local); a guard published by a
  release before 2.18.6 keeps no lock, so it is reclaimed, and the probe
  answers "no live holder", exactly as before; a `fork` that races a thread
  between taking the lock and recording it can inherit an untracked
  descriptor. The plan-approval guard records no worktree at all. Two more
  consequences follow from the code, with no issue filed: the step 8b write
  (`materialize_plan_approval_state`) is not serialized with
  `state_transaction` writers, only preceded by a freshness re-check
  (`plan_approval_state_matches_pre_transaction`); and nothing serializes
  two plan-stage generations of one work item, whose leftover sweep in
  `prepare-ai-review.sh` removes every `current.staging-*`.
- **Mixed releases across worktrees.** The lifecycle exclusion holds only
  once every registered worktree runs a release at or after
  `LIFECYCLE_MIN_RELEASE` (2.6.0). Before that, a lagging worktree's
  unrecorded amendment refuses (`LaggingWorktreeAmendmentError`,
  `_lagging_checks`; `claim_checkpoint` docstring).
- **An abandoned destructive plan-approval guard has no in-band route**, by
  design. The holder lock now tells a crashed holder from a live one, but the
  route stays by hand. The checkpoint guard has `recover_abandoned_destructive_guard`;
  the journal's guard does not (the section comment above
  `PLAN_APPROVAL_GUARD_PATH`).

## Maintenance

Update this table in the same change that changes one of these primitives:
a new lock, guard, claim, lease, journal, or `flock` or `os.link` call site,
or a changed acquisition proof, takeover rule, lock order, crash residue or
recovery route. Then update the "Last checked with" line.
`workflow_state_test.py::TestGlobalLockOrderItem372h` fails when the code's
lock-shaped primitives or edges stop matching the list in
`WORKFLOW_V2_PLAN.md`. It does not read this page.
