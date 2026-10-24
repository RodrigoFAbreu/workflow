# W22: Workflow 2.18.7 — the engine that releases an uncommitted checkpoint start (Revision 4)

- **Work item:** `checkpoint-start-engine` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner split the paused W19 on 2026-10-23 (the
  sizing rule, principle 10). W21 (Workflow 2.18.6) shipped the live-owner guard lock and the probe
  `guard_holder_is_running`; this item is the **engine only**. It is row 24b of `docs/ROADMAP.md` (status
  `Current` from this plan, `Done` at acceptance); row 24c adds the command afterwards.
- **Issues:** RodrigoFAbreu/workflow#55 (engine only; it stays open for row 24c) and
  RodrigoFAbreu/workflow#95 (closed by this release).
- **Branch:** `milestone/checkpoint-start-engine`
- **Base commit:** `5645896` (main after #96: the release source and this repository's own installation
  are both Workflow 2.18.6, automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file
  declared, so the prose roadmap applies)
- **Plan revision:** 3 (round 2 of the local review applied: IMP-1, OPT-1; round 1: IMP-1, OPT-1 to OPT-4). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.7, a patch release (`fix:`), that adds the library function
`workflow_state.release_checkpoint_start(repo_root, work_item_id, checkpoint_id, *, now)`: it releases an
**uncommitted** checkpoint start (the `IN_PROGRESS` state entry and the claim that go with it) as one
continuous window, so that `/request-plan-amendment` is no longer wedged by a start its own plan forbids
completing (#55). It adds **no command, no command file and no document of the user-only lists**: nothing
calls the function yet, so no installed behaviour changes (row 24c adds the command). The same release
folds in the one-test fix for #95.

### The invariant (one sentence)

**I1.** A start is removed (entry first, claim second) only inside one window in which this process holds
the work item's lifecycle lock (9) and a live `release-start` guard, after proving under that guard that
no owner window is running and no commit followed the start, so that any interruption leaves the start
whole or half removed (entry gone, claim kept) under a guard whose holder is gone, and calling the function
again finishes the release or refuses.

What I1 does and does not promise, so the reviewer can test it against the code:

- **Success** leaves the entry **as the committed state at `HEAD` records it** (absent for a checkpoint
  `HEAD` never recorded; the `NEEDS_REVALIDATION` entry, old `start_commit` included, for a checkpoint an
  amendment demoted and that was re-started), no claim and no guard of the start. A live owner that holds the old token
  and tries `1f-commit` afterwards passes `acquire_guard` and then fails `assert_claim_owner` (no claim),
  so its body never runs and `complete_checkpoint` never recreates the entry. A later fresh start mints a
  different token, so the old token is refused for good.
- **A window that was running when the release began** is never overtaken: the probe and the guard
  acquisition refuse a live holder (W21's holder lock), so no body runs on after success. The one
  exception is the one W21 states: a guard published by a release before 2.18.6 keeps no lock.
- **An interruption** (a crash, a kill, a failed unlink) leaves the claim, possibly no entry, and a guard
  whose holder is gone. The next call re-observes and completes, or refuses (D-Recovery). **Between the
  interruption and that call the owner is not fenced by the engine**: the dead guard is reclaimable by
  the owner like any own leftover. If the owner completes its checkpoint in that interval, its `1f-commit`
  window runs `complete_checkpoint` and then step 1f releases the claim, so the next call finds a `COMPLETE`
  entry and refuses `CheckpointNotInProgressLocallyError`, changing nothing. **The residual after an interruption
  past the state write differs by case, and the demoted case is the harmful one.** The working entry is
  then `B`, and `complete_checkpoint` checks no status, so the owner (its claim still present) commits
  `COMPLETE` over it. (a) *Never recorded* (`B` absent): `setdefault` recreates the entry as
  `{status: COMPLETE}` with **no `start_commit`**; this is harmless, because that checkpoint has no earlier
  completion, so `prove_checkpoint_completions` resolves it from its single trailer candidate. (b)
  *Demoted and re-started* (`B` is the `NEEDS_REVALIDATION` entry): the owner commits `COMPLETE` carrying the
  **earlier** start's `start_commit` (a demoted checkpoint normally completes only after a step 1d
  re-start writes a new one; `_checkpoint_start_descendant` relies on that). The checkpoint then has two
  trailer commits, both recording `COMPLETE` and both strictly descending from the old `start_commit`, so
  `prove_checkpoint_completions` raises `AmbiguousCheckpointTrailerError` for it, and its next consumer
  (reconcile, the `verify` op, approval) wedges on that checkpoint. There is **no recovery in this release**:
  nothing calls the function, so no installed behaviour can reach it, and the next release call refuses
  `CheckpointNotInProgressLocallyError` and changes nothing. Closing it is row 24c's obligation (D-Residual).
  An interruption **before** the state write keeps the new `start_commit` and is whole. The engine never
  fabricates a start.

### Hard limits

- **No new command, state field, ledger, phase, trailer, commit shape or protocol change**, no new guard-
  body key and no new refusal class: every refusal is an existing class (D-Refusals). Nothing is
  committed. No Controller or Manager change: `min_manager_version` stays 1.13.0 and
  `tools/release/manager-pin.json` must EQUAL it.
- **One new concurrency mechanism: the release window** (D-Window). It is built only from existing
  primitives (the lifecycle lock, `owner_mutation`, `state_transaction`, W21's probe). The only
  concurrency-test edit it needs is declaring one edge the detector now derives (D-Lock-Order).
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`, `docs/ai-workflow/`
  managed documents, `.workflow-manager/`, the managed blocks of `CLAUDE.md` and `.gitignore`, and
  `.github/workflows/workflow-conformance.yml`. The change goes to `payload/`; release bookkeeping to
  `manifest.json`, `docs/` user documents and `tools/release/`.
- **Size:** two checkpoints including the release one. If a second concurrency mechanism appears, the
  work stops and splits (principle 10).

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test, shown to fail against the unedited code first; the
  nine payload suites from a staged fixture (`TestGlobalLockOrderItem372h` among them); the new tests and
  the whole chunk of the suite under the Manager's orphan wrapper (D-Orphan); the `tools/release` tests
  (in the zlib-ng environment); the `tools/docs` tests and checker; `check-manager-block` with
  `--manager-releases`; `workflow-manager verify .` clean. Every command form is copied from
  `docs/RELEASING.md`, "Verification commands".
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against `git diff`
  (CP2).

## 2. Facts this plan relies on (re-checked against `5645896`)

Rows are the primitives of `docs/CONCURRENCY_INVARIANTS.md`; they are cited, not rediscovered.

- **(9) Lifecycle lock.** Work-item-wide flock, a pure source, acquired first or alone, taken by
  `claim_checkpoint`, `adopt_claim`, an absent-claim `take_over_claim` and the amendment code; edges
  (9)→(2), (8), (6), (5), (3). While a release holds it, no fresh start, adoption or amendment of that
  work item can begin in any worktree, and a second release blocks. It refuses when the caller already
  holds another lock-order primitive (`LifecycleLockOrderError`).
- **(8) Claim.** `claim_checkpoint` publishes it at step 1d (under (9) and (2)); the `IN_PROGRESS` entry
  is written afterwards inside an `owner_mutation` window by `transition_checkpoint_in_progress`
  (`{status, start_commit}` plus `current_checkpoint_id`, uncommitted, in the claiming worktree). The proof
  from then on is the minted `owner_token`. The claim row's recovery cell says it: an `IN_PROGRESS` start
  with no commit has no release route (#55).
- **(5) Guard.** `owner_mutation(T)` is `acquire_guard(role="owner")`, `assert_claim_owner(T)` under the
  guard, the body, `release_guard`. After W21 the owner role reclaims a same-token same-worktree guard
  only when no other process holds its holder lock; a live holder is refused with
  `CheckpointOwnershipUnavailableError`, and a crashed holder's leftover is reclaimed. A takeover cannot
  break a destructive guard (`GUARD_STEP_CLASSES` is the set of the two step classes; a step is destructive because its caller passes
  `step_class=DESTRUCTIVE`, as steps `1d` and `1f-commit` do, and the engine does the same for `release-start`;
  no table changes).
- **The probe.** `guard_holder_is_running(repo_root, work_item_id)` takes (6) as a leaf and answers
  whether another process holds the published guard's lock; it raises on an undecidable guard.
- **Where the owner can write.** Step 1f's `1f-commit` window runs `complete_checkpoint`, which recreates
  an entry with `setdefault`, and then the commit; step 1d's window writes the entry. Both begin with
  `acquire_guard` and then `assert_claim_owner`, which refuses when the claim is absent or carries another
  token.
- **Detectors.** `TestGlobalLockOrderItem372h` derives edges from the AST of `workflow_state.py`:
  everything reachable from a `with owner_mutation(...)` body is a target of an edge sourced at (5), and the
  completeness arm decides that the claim file is a primitive because some unlink of it is gated by a
  same-content comparison.

## 3. Design decisions

### D-Window: one window, entry first, claim second, nothing committed

`release_checkpoint_start(repo_root, work_item_id, checkpoint_id, *, now)` returns `None`:

1. **Take (9)** (`lifecycle_lock`). Everything below runs inside it; there is no second window.
2. **Observe, advisory, no guard yet.** Read the claim (`resolve_claim`: an undecidable claim raises) and
   this worktree's state entry for the work item, and read **the baseline `B`**: the entry for
   `checkpoint_id` in the `WORKFLOW_STATE.json` committed at `HEAD` (`git show`), which must be readable.
   `B` is absent (a checkpoint `HEAD` never recorded) or `NEEDS_REVALIDATION` (a checkpoint an amendment
   demoted: `reconcile_checkpoints_after_amendment` keeps its old `start_commit`, the plan-approval commit
   commits it, and `transition_checkpoint_in_progress` overwrites it at the re-start). Any other `B`
   (`COMPLETE`, `IN_PROGRESS`) means the checkpoint is committed past a start and refuses. Classify and
   refuse (D-Refusals) every case that needs no guard. Ask `guard_holder_is_running`: `True` refuses (a window of this work item is running).
3. **Open the guard.** `with owner_mutation(repo_root, work_item_id, <the claim's token>,
   checkpoint_id=..., step="release-start", step_class=DESTRUCTIVE, now=now)`. That is `acquire_guard(role=
   "owner")` and then `assert_claim_owner` under the guard, so a claim that changed since step 2 refuses
   there. The step is **destructive**: the window removes the start, so no takeover may break it, and a
   leftover is cleared by the same route as any destructive guard of a registered worktree (this same
   call, from the same worktree). The owner role also refuses a live holder (W21) and a takeover's guard
   with this token, with the messages those branches already have.
4. **Re-verify under the guard**, from fresh reads, never from step 2. `B` is read again here, and **the
   commit rule** is defined on proof, not on the checkpoint being recorded. With a working
   `IN_PROGRESS` entry, `start_commit..HEAD` holds **no commit that carries this work item's
   `Workflow-Checkpoint: <checkpoint_id>` trailer and no commit whose committed state records the checkpoint
   other than as `B` does** (absent when `B` is absent; the identical `NEEDS_REVALIDATION` entry when `B`
   is). With a working entry equal to `B` there is no `start_commit` to bound a range, and none is needed:
   a completion commits the state it completes, so a completed or restarted-and-committed checkpoint makes
   `HEAD`'s own `B` `COMPLETE` or `IN_PROGRESS`, which already refused at the `B` validity check above. An unrelated
   commit after the start, for example a merge into the branch, records the checkpoint exactly as `B` does
   and does not block the release; a completion carries the trailer and records `COMPLETE`, and a committed
   start records `IN_PROGRESS` or a different `start_commit`, so both block. Then, by the working entry:
   - **`IN_PROGRESS` with a `start_commit`:** `state_transaction` with a mutator that re-checks the entry
     under the state lock, requires that `start_commit` resolve and be an ancestor of `HEAD` and the commit
     rule above, and **restores `checkpoints[checkpoint_id]` to `B`** (deletes the key when `B` is absent;
     writes back the `NEEDS_REVALIDATION` entry byte for byte when it is not), resets
     `current_checkpoint_id` when it names the checkpoint, and bumps `state_revision` and `last_transition`.
     A refusal raises from the mutator, so nothing is published. **This is the entry restoration, and it is
     first.**
   - **the working entry already equals `B`** (absent when `B` is absent, identical to `B` when it is
     present; this is a start that died between its claim and its state write, a live start paused between
     its claim and its 1d window, a re-started checkpoint not yet overwritten, or half of an interrupted
     release): the commit rule above must hold and the call refuses otherwise; no state is written.
   - **any other working entry** (`COMPLETE`, or `NEEDS_REVALIDATION` that differs from `B`) refuses
     (D-Refusals).
5. **Remove the claim, second.** Immediately before the unlink, re-read the claim and the guard: the claim
   must still carry the observed `owner_token`, and the guard on disk must be this window's own (its
   `lease_id` is one this process holds a holder lock for). **The re-read takes no (6):** it is `read_guard`
   plus membership of that `lease_id` in the in-process `_guard_holder_locks`, and nothing reachable from
   the `with owner_mutation(...)` body calls `guard_holder_is_running` or `guard_mutation_lock`; the probe
   is called only at step 2, outside the guard, so the graph arm derives no `(5)→(6)` edge from the body. Any difference unlinks nothing and raises. Then
   `claim_path(...).unlink(missing_ok=True)`; an `OSError` becomes `CheckpointOwnershipUnavailableError`
   saying the entry is already removed, the claim is not, and the same call finishes it.
6. **Leave the window**: `owner_mutation` releases the guard (a compare-and-delete on its lease), then the
   lifecycle lock is released. On any exception the same exit runs, which is what an interruption leaves
   (D-Recovery).

**Nothing is committed.** The start was never committed, so the engine writes the working-tree
`WORKFLOW_STATE.json` and nothing else: no commit, no trailer, no `git add`. The checkpoint's working-tree
files and the worktree identity record are never touched.

**No rotation, no adoption.** The claim is not rotated and no other release's guard or token is adopted:
the owner role's own-leftover reclaim is the only way a leftover guard of this work item is taken, and it
requires the claim's current token, this worktree, and a holder that holds no lock.

### D-Recovery: calling the function again is the one route

A re-run holds (9) first, so no other release is live. It re-observes from scratch; the table lists every
residue an interrupted window can leave (E: this worktree's `IN_PROGRESS` entry, C: the claim, G: a guard).

| Interrupted after | Residue | The re-run |
| --- | --- | --- |
| taking (9) only | nothing | a full release |
| the guard was published, before the state write | E, C, G (holder gone) | the owner role reclaims G (its holder holds no lock) and runs a full release |
| the state write, before the unlink | C, G; E equals `B` (no E when `B` is absent) | the entry-equals-`B` branch: the commit rule holds, then unlink C and leave. For a re-started checkpoint E is its `NEEDS_REVALIDATION` entry, so the re-run is not wedged by `HEAD` recording it |
| the unlink, before the guard was released | G only (superseded: no claim) | refuses `nothing to release`; the leftover G is reclaimable by any acquirer with no proof |
| the guard release | nothing | refuses `nothing to release` |
| a failed unlink (the call raised) | C, E equals `B`; the same as the third row | the same as the third row |
| a claim taken, before the 1d window (a live or dead start, never interrupted release) | C; E equals `B` (a re-started checkpoint still holds its `NEEDS_REVALIDATION` entry) | the entry-equals-`B` branch, as the third row |

The re-run **re-checks the commit rule every time**, against `B` as `HEAD` records it now: a completion or a
committed start that appeared since the first run refuses and changes nothing. If the owner completed its checkpoint in the interval, the re-run does not even reach that
rule: it finds a `COMPLETE` entry (or, if the owner's step 1f did not finish, a `COMPLETE` working-tree
entry with no commit) and refuses as D-Refusals says.

### D-Residual: what an interruption does not fence, said plainly

A crashed window's guard has no holder, so the owner can reclaim it as its own leftover and enter a window
before the re-run. The engine does not add a rule to prevent that: a rule would be a second mechanism (a
new branch in the guard's decision table, and a replacement of a leftover guard in place so that
reclaiming it never leaves a gap). The consequence is bounded but **not free**: the owner is the process the user is
releasing, and what it commits is a `COMPLETE` checkpoint the next call refuses on
(`CheckpointNotInProgressLocallyError`), never a fabricated start. Two interruption points differ:

- **Before the state write** (residue E, C, G): the owner reclaims G, completes the kept entry, commits;
  `start_commit` is kept and the committed entry is whole.
- **After the state write, never-recorded** (residue C, G; E equals `B`, absent): the owner's
  `complete_checkpoint` recreates the entry as `{status: COMPLETE}` **without `start_commit`**, and that
  entry is committed. This is harmless: the checkpoint has no earlier completion, so
  `prove_checkpoint_completions` resolves it from its single trailer candidate.
- **After the state write, demoted and re-started** (E equals `B`, the `NEEDS_REVALIDATION` entry with the
  earlier start's `start_commit`): the owner's `complete_checkpoint` (no status check) commits `COMPLETE`
  with that **old** `start_commit`, not a new one. The checkpoint now has two trailer commits that both
  record `COMPLETE` and both strictly descend from the old `start_commit`, so `prove_checkpoint_completions`
  raises `AmbiguousCheckpointTrailerError` for it. This is the harmful case. There is no recovery in this
  release; the next release call refuses `CheckpointNotInProgressLocallyError` and changes nothing.
  Restoring `B` without its `start_commit` would not help, since both candidates would still verify.

The residual is stated in `docs/CONCURRENCY_INVARIANTS.md` and pinned at all three cases by T9. It is
accepted for this release because no caller exists. **Row 24c must close it, the demoted and re-started
case included** (the `AmbiguousCheckpointTrailerError` wedge), before a command calls the function:
either fence a dead release guard (so the owner cannot reclaim it before the re-run), or make "the owner
session is stopped" a precondition the command **checks** (not only text) before it releases. This plan
records that as a requirement of row 24c's plan.

### D-Refusals: every refusal is an existing class and changes nothing

All before any write (the guard, once published, is released by the exit of its `with`), each with a message
that says what is true and the one next step:

| Case | Class |
| --- | --- |
| the work item has no state entry, or the checkpoint is neither recorded nor claimed (an unknown id), or its working entry is neither `IN_PROGRESS` nor equal to `B` (for example `COMPLETE`; the message names both cases: a **committed** completion, which step 1c releases, and an **uncommitted** one, a `COMPLETE` working-tree entry an owner left by dying in `1f-commit` after persisting it and before committing, for which the next step is to resume step 1f in the owner's worktree) | `CheckpointNotInProgressLocallyError` |
| the claim is another worktree's | `CheckpointOwnedByOtherWorktreeError` (never takes another worktree's claim; names the takeover route) |
| the claim is for another checkpoint; the entry is `IN_PROGRESS` but nothing claims it (nothing fences it; step 1c adopts it first); a commit in `start_commit..HEAD` that carries the checkpoint's trailer or records the checkpoint other than as `B` does; `B` is `COMPLETE` or `IN_PROGRESS`, or the state committed at `HEAD` is unreadable; a `start_commit` that does not resolve or is not an ancestor of `HEAD` | `CheckpointOwnershipStateMismatchError` |
| a window of this work item is running (the probe, or the owner role's own refusal of a live holder); an undecidable claim or guard; a claim or guard changed before the unlink; a failed unlink | `CheckpointOwnershipUnavailableError` |
| the caller already holds another lock-order primitive | `LifecycleLockOrderError` (existing) |

### D-Lock-Order: one edge the detector now derives, declared

The window is a `with owner_mutation(...)` body that calls `state_transaction`, so the graph arm derives
**(5)→(2)**. The edge is already in the specification's table, as a command-orchestrated edge, so the declared
count does not change; the script's code-derivable set must now list it (it stays listed as
command-orchestrated too, because steps 1d and 1f still take it from the command side). The window takes no (6) inside the body
(D-Window step 5), so no `(5)→(6)` edge is derived and the specification's table and counts need no edit
for it. The window is not written to hide from the detector. The completeness arm's regression 1 makes `release_checkpoint`'s claim
unlink unconditional and expects the claim to stop being a primitive; the engine's own gated unlink is a
second such site, so the mutation is extended to make that one unconditional too (it is the same
regression, applied to both sites). Both edits are in the two scripts under
`payload/docs/ai-workflow/dry-run/`; the specification's table and counts do not change. A prototype of
the window, in a scratch copy, passes both arms with exactly those edits and fails without them.

### D-Orphan: the #95 fix, and why waiting alone is not enough

`TestLiveGuardVisibility.test_a_forked_child_owns_nothing_it_inherited` forks a child of its worker,
**kills the worker** (case (c): the child must not keep a dead parent's guard looking live), then lets the
child go and returns. The Manager's wrapper (`tests/parallel/reaper.py`) is a child subreaper: every process
re-parented to it is recorded as an orphan when it is reaped, **whether it exits before or after the chunk**.
So making the test wait for the child to exit is necessary and not sufficient: the child is still
re-parented to the wrapper the moment its parent is killed. The fix makes the **test process** the child
subreaper for the duration of that one test (Linux `prctl(PR_SET_CHILD_SUBREAPER)` through `ctypes`,
restored in a cleanup; where it is unavailable the child re-parents to `init` and nothing changes). The
orphan then re-parents to the test, which reaps it. The child reports its pid in its event; the test waits
for its exit with a bounded `select` on the worker's stdout (EOF means the child has closed it) and then
`os.waitpid`; a cleanup kills and reaps the child if the test failed first. Scenario, assertions and the
worker are otherwise unchanged. Red first: the chunk run under the wrapper before the fix reports the
orphan; after it, none. The same wrapper run covers the new tests (their workers are direct children,
killed and waited by the test).

### D-Tests: deterministic, real processes, explicit seams, no sleeps as synchronisation

A worker (a constant of source in the test module, like `_LIVE_GUARD_WORKER_SOURCE`) runs in a real child
process and is driven over pipes; the test reads one line per event (a blocking read is the
synchronisation). Seams are wrappers installed **in the worker** over existing module functions, never
engine hooks: a wrapper over `ws.state_transaction` runs between the guard and the unlink (the entry-present
branch only); a wrapper over `ws.lifecycle_lock` reports that a contender reached acquisition before
delegating; a wrapper over `ws.release_guard` fires after the unlink and before the release (it is the only
seam between the two, and the entry-equals-`B` branch, which calls no `state_transaction`, is crashed at it or at
the next one); the unlink is failed by a wrapper over `ws.claim_path` that returns a path whose `unlink`
raises `OSError` only for the call the engine makes at step 5, so `resolve_claim`'s read of the same path and
the guard release are unaffected; a crash is `os._exit` (no cleanup, locks dropped by the kernel) at the
wrapper. A kill is `proc.kill()` then `proc.wait()`.
Each test is shown to fail against the unedited code first (the function does not exist; the pins of
existing behaviour pass, which is their point).

Class `TestReleaseCheckpointStart` in `payload/scripts/workflow_state_test.py`. The scratch state mirrors
step 1d: a committed state at `IMPLEMENTING`, `claim_checkpoint`, then the uncommitted `IN_PROGRESS` entry.

1. **T1 Success**: entry restored to `B` (gone when `HEAD` never recorded the checkpoint; **equal to the
   `NEEDS_REVALIDATION` entry `HEAD` records when it is a demoted, re-started checkpoint**, compared against
   `git show HEAD:...`) and claim gone, `current_checkpoint_id` reset, `state_revision` bumped, guard
   absent, `held_primitives()` and `_guard_holder_locks` empty, `HEAD` and the checkpoint's working files
   untouched, nothing staged.
2. **T2 Refusals, one subtest each**, each leaving state, claim and guard byte-identical: a commit carrying the
   checkpoint's trailer since `start_commit` (entry present), a commit that records the checkpoint as
   `COMPLETE` or with another `start_commit`, and, as the pass side, an **unrelated** commit since
   `start_commit` that does not block it, **including one that records the demoted checkpoint exactly as
   `B` does**; another worktree's claim; a claim for another checkpoint; an unknown id;
   a checkpoint not `IN_PROGRESS`; a work item with no state entry; an entry with no claim; an unresolvable
   `start_commit`.
3. **T3 Live owner** (a worker parked in `1f-commit`, via the W21 mixin, **before** its `complete_checkpoint`
   write): refused with the running-window message, the owner's guard untouched; after the window ends the
   release succeeds; a holder killed there leaves a reclaimable leftover and the release completes. A second
   case kills the owner **after** it persisted `COMPLETE` and before it committed: the release refuses
   `CheckpointNotInProgressLocallyError` with the uncommitted-completion message (resume step 1f).
4. **T4 Crash after each step, then a re-run** (real processes, `os._exit` at the seam): before the state
   write, after it, after the unlink. The residue is asserted exactly (D-Recovery's table) and the probe
   answers `False`; the re-run completes, or refuses `nothing to release`.
5. **T5 Two concurrent releases**: R1 parks inside its window; R2 reports that it reached acquisition of
   (9), blocked behind R1 (it can observe nothing before it holds (9)); the test lets R1 finish; R2
   refuses and never enters a window. Deterministic whatever the scheduler does, because R2's first read is
   inside (9).
6. **T6 The old race**: a live same-worktree owner process holding the old token attempts `1f-commit`
   **after** the release: refused (no claim), its body never runs, the entry is never recreated; also
   attempted **during** the window it is refused as a live holder. A fresh start after the release mints a
   different token and the old token is refused.
7. **T7 Failed claim cleanup**: a failing unlink of the claim path leaves the entry removed and the claim in
   place, the call raises with the re-run route, and the next call completes.
8. **T8 A changed claim or guard**: (a) the claim is rotated between the probe and the guard: refused at
   the assertion under the guard, nothing changed; (b) after the state write, the claim is rotated; (c)
   after the state write, the guard is replaced by another lease: (b) and (c) unlink nothing.
9. **T9 The residual, pinned at each case** (D-Residual), each with the exact class and the committed
   entry's shape: (a) **interrupted before the state write**: the owner reclaims the dead guard, completes and
   commits; the committed entry is `COMPLETE` **with** its `start_commit`; the next call refuses
   `CheckpointNotInProgressLocallyError`, changing nothing. (b) **interrupted after the state write**: the
   owner reclaims the dead guard, completes and commits; the committed entry is `{status: COMPLETE}` **with
   no `start_commit`**; the next call refuses `CheckpointNotInProgressLocallyError`, changing nothing. (c)
   **a demoted, re-started checkpoint, interrupted after the state write**: the owner reclaims the dead
   guard, completes and commits; the committed entry is `COMPLETE` **with the earlier start's
   `start_commit`**; `prove_checkpoint_completions` raises `AmbiguousCheckpointTrailerError`; the next
   release call refuses `CheckpointNotInProgressLocallyError` and changes nothing. No case is ever
   `CheckpointOwnershipStateMismatchError`.
10. **T10 Entry equals `B`**: a start paused between its claim and its 1d window is released and its window
    then refuses; `HEAD` recording the checkpoint as `COMPLETE` or `IN_PROGRESS` refuses; an unreadable
    `HEAD` state refuses.
11. **T11 A demoted (`NEEDS_REVALIDATION`) checkpoint, re-started** (the scratch state commits the demoted
    entry with an old `start_commit`, then the step 1d start overwrites it): (a) **success**: the result is
    the committed entry, byte for byte, and nothing committed is lost; (b) **an unrelated commit** after the
    re-start (which records the demoted entry as `HEAD` does): released; (c) **an interruption after the
    state write, then a re-run** (`os._exit` at the seam): the re-run completes, not
    `CheckpointOwnershipStateMismatchError`, and the claim is gone; (d) **a claim taken before its 1d window**
    (working entry still the demoted one): released, and the paused window then refuses; (e) a `COMPLETE`
    commit since the re-start refuses.
12. **Pins:** every refusal and success leaves `held_primitives()` empty; the existing guard, takeover and
    live-visibility tests pass unchanged; `TestGlobalLockOrderItem372h` passes with the D-Lock-Order edits
    and fails without them (run red first).

### D-Docs: `docs/CONCURRENCY_INVARIANTS.md` in the same change (CP2)

The checkpoint steps listed as destructive gain `release-start`; the claim row's recovery cell and the
known-gaps entry for #55 now say the library function exists and that no command calls it yet; the (5) row
gains the step; the (2) row's `(5)→(2)` note says the edge is now also taken by code; a new row for the
release window states I1, its lock order ((9)→(6)→(5), (5)→(2), and the release-time (5)→(6)), its residue
table and its pinning tests; its residual states both post-write cases (the never-recorded one harmless,
the demoted one making `prove_checkpoint_completions` raise `AmbiguousCheckpointTrailerError`, with no
recovery in this release); "Last checked with" follows the release. No internal milestone id appears on
the page (the docs checker).

### D-Patch: the version is 2.18.7, `fix:`

`manifest.json` `workflow_version` 2.18.7; `WORKFLOW_RELEASE` and its two pinned assertions in
`workflow_protocol_test.py` follow, with the matching `ORCHESTRATION_PROTOCOL.md` edits (tested releases
list, envelope example, protocol note); the protocol version stays. Why `fix:`: no state key, ledger,
phase, trailer, commit shape, guard-body key, protocol field or refusal class is added; the function is
called by nothing in the release, so no installed behaviour changes; the one change a user could see is a
test file.

**Downgrade posture.** 2.18.7 writes no state, ledger or file an older release cannot read, because
nothing calls the new function. A guard that a later call of it writes has the same body and shape as any
guard and the step name `release-start` with class `destructive`; an older release (2.18.6 or earlier)
reads it as a destructive guard of an unknown step: it never breaks it by takeover, reclaims a leftover as
its own when the holder is gone (2.18.6) or as before (earlier), and routes a deregistered worktree's
through `recover_abandoned_destructive_guard`. `workflow-manager update` back to 2.18.6 removes the
function, nothing else. The manager block and the release-history row say so.

### D-Staging: scratch staging for CP1 (the procedure W21 used)

`release.py stage-conformance` verifies the manifest against the tree, and CP1 changes shipped files whose
digests (and the suites' measured test counts) the committed manifest records only at CP2. So CP1 verifies
in a disposable clone (a full `git clone` under `$TMPDIR`): a scratch script recomputes `sha256` and `size`
of every `artifacts` and `templates` record whose file differs from its record, measures and rewrites
`manager.conformance.suites` (digests, sizes and counts, the discovery `release.py manager-block
--release-dir <scratch> --write` uses), commits it in the clone, and the "Verification commands" blocks run
from there. No rationale is touched in the scratch.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
| --- | --- | --- |
| OD-1 | The version: patch 2.18.7 (`fix:`) or minor | **Patch, `fix:`** (the owner's rows 24b and 24c). The command row is the `feat:`. |
| OD-2 | The guard step's class | **Destructive.** The window removes the start, so no takeover may break it. |
| OD-3 | An interruption leaves the owner unfenced (D-Residual) | **Accept and pin it at each case: the harmless `start_commit` loss of a never-recorded checkpoint, and the `AmbiguousCheckpointTrailerError` wedge of a demoted, re-started one.** The alternative is a second mechanism (a new branch in the guard's decision table plus an in-place replacement of a leftover guard); that is a split, not part of this item. Row 24c must close it, the demoted case included, or check "the owner session is stopped" as a precondition (D-Residual). |
| OD-4 | The #95 fix mechanism | **The test becomes the subreaper of its own orphan**, because the Manager records every re-parented process; waiting alone does not remove the record. |
| OD-5 | Binding a confirmation to the observed start | **Row 24c's.** The user's literal confirmation is the command's; if it needs the observed token passed in, that is one keyword added then, with its test. The engine observes the claim itself. |
| OD-6 | The manager CI pin | **No change.** `manager-pin.json` (1.13.0) equals `min_manager_version` (1.13.0). |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does not exist in
this repository's release source).

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The release engine, its tests and the fork-test fix | - | 4 | 1 |
| CP2 | Release 2.18.7 | CP1 | 3 | 1 |

<!-- CP1 -->
### CP1 — The release engine, its tests and the fork-test fix

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`,
`payload/docs/ai-workflow/dry-run/verify_372h_raw_edge_derivation.py`,
`payload/docs/ai-workflow/dry-run/verify_372h_lock_primitive_predicate.py`.

- **Tests first, red first** (D-Tests): T1 to T11 and the #95 reaper demonstration are written and run
  against the unedited `workflow_state.py`; the failures are recorded (the engine tests fail because the
  function does not exist; the pins pass; the unedited fork test is shown to leave an orphan under the
  wrapper). **Done:** the recorded failures name each new test.
- **The engine** (D-Window, D-Recovery, D-Refusals): `release_checkpoint_start` and a few private helpers
  (a `HEAD` commit resolver, a state-entry reader, the committed-state check), placed beside
  `release_checkpoint`, and a docstring that states I1. **Done:** `git diff` of `workflow_state.py` is those
  and nothing else; no `os.link` or `LOCK_EX`-attribute `flock` site is added; no guard, claim or message
  of an existing path changes; the function is not exported to any command.
- **The lock-order declaration** (D-Lock-Order): the two scripts, edited as stated. **Done:**
  `TestGlobalLockOrderItem372h` is run red first against the engine and shown to fail on exactly the
  (5)→(2) edge and on the extended regression, and passes after the edits.
- **The #95 fix** (D-Orphan) in `TestLiveGuardVisibility`. **Done:** the chunk under the Manager's wrapper
  reports no orphan; the scenario's assertions are unchanged.
- **Docs and roadmap:** `docs/CONCURRENCY_INVARIANTS.md` is CP2; `docs/ROADMAP.md` row 24b is `Current` from
  this plan and this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites (`TestGlobalLockOrderItem372h` among
them), the new class and the whole `workflow_state_test.py` chunk under the Manager's orphan wrapper, the
`tools/release` and `tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.18.7

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`,
`docs/release-history.md`, `docs/RELEASING.md`, `docs/CONCURRENCY_INVARIANTS.md`,
`tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.18.7 with its two pinned assertions in `workflow_protocol_test.py` and the
  matching `ORCHESTRATION_PROTOCOL.md` edits; the protocol version stays.
- `manifest.json` 2.18.7: `workflow_version`; `sha256` and `size` of every record changed in CP1 and CP2
  (`workflow_state.py`, `workflow_state_test.py`, the two dry-run scripts, `workflow_protocol.py` and its
  test, `ORCHESTRATION_PROTOCOL.md`); a `checkpoint-start-engine (workflow-2.18.7)` sentence on **each**
  changed artifact record, true of THAT file and read against `git diff 5645896..HEAD -- <file>`; the
  `manager` block: `min_manager_version` 1.13.0 (equal to the CI pin), `downgrade_boundary.posture` per
  D-Patch, `signals`, `new_work_only` and `gate_default_change` empty, `conformance.suites` (digests, sizes
  and test counts) measured by `release.py manager-block --release-dir <scratch> --write` from a staging of
  CP2's own content, never typed.
- `docs/release-history.md`: the 2.18.7 row (it closes #95 and leaves #55 open for the command; names the
  engine, its refusals, the residual (both post-write cases, the demoted one raising
  `AmbiguousCheckpointTrailerError`), the fork-test fix and the way back) and the "Last checked with" line;
  `docs/RELEASING.md`: any test count it states follows the measured count, no other change;
  `docs/CONCURRENCY_INVARIANTS.md` per D-Docs, "Last checked with: Workflow 2.18.7".
- `tools/release/release_test.py`: a 2.18.7 release class (version, release constant, the posture and
  history needles, counts); the 2.18.6 class keeps what stays true of that release and no longer pins the
  current version, constant or posture.
- `docs/ROADMAP.md` is not written by this checkpoint: row 24b becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture;
`release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #55, the engine | `release_checkpoint_start`, one window, entry first and claim second, the recovery table, T1 to T11 | CP1 | D-Window, D-Recovery, D-Tests. #55 stays open for the command |
| Lock-order declarations | (5)→(2) code-derivable; the extended regression | CP1 | D-Lock-Order |
| #95, the fork test | The test becomes the subreaper of its orphan and waits for it, bounded | CP1 | D-Orphan; the Manager's four declarations go in a later chore |
| Concurrency page | The window row, the step, the narrowed gap | CP2 | D-Docs |
| Release | 2.18.7 bookkeeping, closes #95 only | CP2 | D-Patch |
| The residual | Pinned at each case (T9 a-c); row 24c must close it, the demoted case included, or check the precondition | CP1 (T9); row 24c | D-Residual, OD-3 |

The artifact declaration `docs/ai-workflow/registry/checkpoint-start-engine-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its plan-stage
protected paths, and self-review checked that every path named in a Files paragraph, and every other path
this plan names (`docs/ROADMAP.md`, `docs/RELEASING.md`, `docs/release-history.md`,
`docs/CONCURRENCY_INVARIANTS.md`), is classified at both stages and that every deliverable is protected at
the implementation stage.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands", and the manifest key is
`workflow_version`. Each flow names its workspace.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | a scratch repository (the test harness's `ScratchRepo`) | a start released: entry and claim gone, nothing committed, the old token refused afterwards |
| f2 | the same scratch repository | an interruption after the state write; the second call completes; a commit since the start refuses |
| f3 | the same scratch repository | a live owner parked in `1f-commit` refuses the release; once it ends the release succeeds |
| f4 | the staged conformance fixture of the candidate | the `workflow_state_test.py` chunk under the Manager's orphan wrapper reports no orphan |
| f5 | the staged conformance fixture of the candidate (`stage-conformance`) | the nine suites, `tools/release` (zlib-ng environment) and `tools/docs`, `check-manager-block` |
| f6 | the checkout | `docs/CONCURRENCY_INVARIANTS.md` states the window, its residual and the narrowed gap |
