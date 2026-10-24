# W21: Workflow 2.18.6 — a live owner's guard is visible and not reclaimable (Revision 2)

- **Work item:** `live-guard-visibility` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner chose this split on 2026-10-23, when W19
  (#55, row 24) was paused again. It is row 24a of `docs/ROADMAP.md` (status `Current` from this plan,
  `Done` at acceptance).
- **Issue:** RodrigoFAbreu/workflow#91.
- **Branch:** `milestone/live-guard-visibility`
- **Base commit:** `2865182` (main after #92: the release source is Workflow 2.18.5; this repository's
  own installation is also 2.18.5, automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog
  file declared, so the prose roadmap applies)
- **Plan revision:** 2. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.6, a patch release (`fix:`), that closes #91: a holder of a mutation guard must be
**visible** to a later acquirer and to a liveness check, so that a second owner window cannot open
beside a running one, and so that the paused release of an uncommitted checkpoint start (#55) has a
sound way to prove that no owner body is running.

**The defect.** `_acquire_guard_locked` reclaims, for `role="owner"`, a held guard of the owner's own
token and worktree (the "own leftover" branch) by removing and replacing it without asking whether the
previous holder is still running. `_acquire_plan_approval_guard_locked` has the sibling branch (same
token). Owner A enters `1f-commit` and pauses; same-token owner B reclaims A's guard, enters, and
releases; no guard is published while A is alive, so no check on the published guard can see A.
`workflow_state_test.py::TestSameWorktreeConcurrencyRealProcesses` pins this as intended ("both
windows stay open"); `docs/CONCURRENCY_INVARIANTS.md` lists it as out of scope.

**The fix** ("D-Lock", one mechanism): the holder keeps a non-blocking kernel lock (`fcntl.flock`) on
its guard's inode for the whole window. The kernel drops it when the holder dies, so a crash leaves a
guard that nobody holds. The own-leftover reclaim of each guard, and one small public probe, refuse a
guard whose lock is held by another process; a guard whose holder is gone stays reclaimable exactly as
today.

### Hard limits (invariants)

- **No new command, state field, ledger, phase, trailer, commit shape or protocol change**, and no
  new key in a guard's body. Refusal classes keep their names: the claim guard's new refusal is the
  existing `CheckpointOwnershipUnavailableError` (the class its neighbouring "held" refusals raise),
  the journal guard's the existing `PlanApprovalGuardHeldError`, each with a message of its own
  (OD-2). No Controller or Manager change: `min_manager_version` stays 1.13.0 and the CI pin in
  `tools/release/manager-pin.json` must EQUAL it.
- **One concurrency mechanism** (the holder lock), applied to the two guards. The release command of
  the paused item is not built here.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`,
  `docs/ai-workflow/` managed documents, `.workflow-manager/`, the managed blocks of `CLAUDE.md`
  and `.gitignore`, and `.github/workflows/workflow-conformance.yml`. The fix goes to `payload/`;
  release bookkeeping to `manifest.json`, `docs/` user documents and `tools/release/`.
- **Size:** two checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test, shown to fail against the unfixed code first; the
  nine payload suites from a staged fixture (including `TestGlobalLockOrderItem372h`); the
  `tools/release` tests (in the zlib-ng environment); the `tools/docs` tests and checker;
  `check-manager-block` with `--manager-releases`; `workflow-manager verify .` clean. Every command
  form is copied from `docs/RELEASING.md`, "Verification commands".
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against `git diff`
  (CP2).

## 2. Facts this plan relies on (re-checked against `2865182`)

- **Publication.** `acquire_guard` runs `_acquire_guard_locked` under `guard_mutation_lock` (6).
  `_publish_guard` calls `_publish_claim_exclusive`: `_stage_claim_payload` writes a complete temp file
  (`.claim-*.tmp`) in the claims directory, then `os.link(tmp, path)` publishes it (`FileExistsError`
  means someone else won) and the temp name is unlinked. The guard is therefore the **temp file's
  inode**. The plan-approval guard does the same in `_publish_plan_approval_guard` (its own
  `.plan-approval-guard-*.tmp`, `os.link`), under `_plan_approval_guard_lock` (7).
- **Who holds what across a window.** `owner_mutation` and `plan_approval_guarded_mutation` are
  `with` blocks of **one Python process**: acquire, assert ownership, the body (git commits are
  `subprocess` children, which `exec`), `finally` release. `release_guard` ->
  `_release_guard_path_locked` compare-and-deletes the guard by `lease_id`. The takeover
  (`_take_over_claim_window`, `take_over_plan_approval_transaction`) and the recovery
  (`recover_abandoned_destructive_guard`, the journal rollback) acquire and release the same way. No
  window spans two invocations, so a process-lifetime lock matches the window it represents.
- **Decision tables** (`_acquire_guard_locked`, `_acquire_plan_approval_guard_locked`), in order:
  superseded epoch (reclaim, no proof); `role="owner"` against a caller's own `takeover` guard
  (refuse, takeover-fence); `role="owner"`, same token and worktree (claim) or same token (journal):
  **reclaim, the defect**; the claim guard's same-token other-worktree refusal; `role="takeover"`
  (ordinary guard and quoted `lease_id`: reclaim; destructive: refuse); `role="recovery"` (quoted
  `lease_id`: reclaim); else refuse.
- **Tests that leave a guard behind in the same process.** Many existing tests simulate a crash by
  acquiring a guard and never releasing it, then re-acquiring in the same process
  (`test_same_worktree_same_token_guard_reclaimed`, `test_owner_reclaims_its_own_leftover_guard_and_retries_once`,
  and the abandoned-guard recovery tests). A lock held by the test's own process must not refuse them
  (D-Own).
- **The lock-order tests.** `TestGlobalLockOrderItem372h` discovers `fcntl.flock(fd, fcntl.LOCK_EX)`
  call sites by AST (`args[1]` an attribute named `LOCK_EX`) and `os.link` sites, and compares them to
  the specification's primitive list. The holder lock is `LOCK_EX | LOCK_NB` (a binary operation), is
  non-blocking and is waited on by nobody, so it is not a lock-order primitive and the discovery does
  not classify it; CP1 runs the test to prove it. No `os.link` site is added.
- **Kernel semantics used.** `flock` belongs to the open file description, not the process: a second
  `open` of the same inode in any process is a distinct description, so a non-blocking `LOCK_SH`
  attempt on it fails with `EWOULDBLOCK` while a `LOCK_EX` description is open anywhere; the lock is
  dropped when the last descriptor of the holder's description closes, in particular when the holder
  dies. A descriptor opened through Python is close-on-exec (PEP 446), so `git` and other children do
  not inherit it. A `fork` without `exec` shares the description (D-Fork).

## 3. Design decisions

### D-Lock: the lock is on the guard's own inode, taken before publication

On every successful publication of either guard (any role: owner, takeover, recovery; the window the
guard represents is the window the lock covers), the publisher: stages the temp file as today; keeps
the `O_RDWR` descriptor `mkstemp` already returned (it is not reopened `O_RDONLY`: where `flock` is
emulated with POSIX locks, as on NFS, an exclusive lock needs a writable descriptor, and a read-only
one would fail every acquisition closed); takes `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on it; then runs
the existing `os.link`. **The seam:** the claim guard publishes through `_publish_claim_exclusive`,
which the checkpoint claim's own publication (`_claim_or_refuse`) shares; it gains one opt-in
keyword parameter that only `_publish_guard` passes, so the claim stays lockless and byte for byte as
today, and no second `os.link` site is added. The plan-approval guard's `_publish_plan_approval_guard`
takes the lock in the same place. The staging helper hands the descriptor to the caller instead of
closing it; the descriptor is close-on-exec. The descriptor is kept in a process-local table `_guard_holder_locks`
(`lease_id` to descriptor) until the guard is released. On `FileExistsError` (lost the race) or any
other failure the descriptor is closed and nothing is recorded.

Why the inode and not a sibling lock file:

- The lock exists **before** the guard is visible, so there is no instant at which a published guard is
  unlocked and a prober could misread a live holder (no gap, no ordering rule to get right).
- It adds **no new file**, no cleanup and no crash residue: the guard is the only artifact, removed
  by the routes that remove it today. A sibling file would be a second object to create, unlink and
  recover, and its identity would have to be tied to the guard's `lease_id`.
- A guard that is replaced (reclaimed, or broken by an authorized takeover) is a **new inode**, so
  the old holder's lock stays on an unlinked inode that nobody opens: a displaced holder can never
  make the new guard look live. The displaced holder's release is already a `lease_id`
  compare-and-delete and is unaffected.

The lock is a **visibility lock**, not a lock-order primitive: non-blocking, never waited
on, a leaf that takes nothing else. It adds no edge to the lock graph.

**Release.** `release_guard` (and `release_plan_approval_guard`) closes the descriptor in its `finally`
(`_drop_guard_lock`), idempotently; `_release_guard_path_locked` and its plan-approval twin also drop
the lock of the lease they remove, so a process that reclaims its own earlier lease does not keep the
orphan descriptor. After a normal release no descriptor of the process holds the old inode.

**Failure to lock** (`flock` raising anything on a fresh private inode) fails closed: the publication
raises the guard's existing unavailable error, having published nothing. The repository already
requires `flock` on the very directories involved (the state lock, (6) and (7)).

### D-Probe: one small function, and the reclaim uses the same helper

`_guard_held_by_another_process(guard_file, lease_id)`:

1. `lease_id` in `_guard_holder_locks` -> `False` (the lock is this process's own, D-Own; the table
   holds only this process's own entries, D-Fork).
2. `os.open(guard_file, O_RDONLY | O_NOFOLLOW | O_CLOEXEC)`; absent -> `False`.
3. `fcntl.flock(fd, LOCK_SH | LOCK_NB)`: `BlockingIOError` -> `True`; success -> `False`. The
   descriptor is closed at once, which drops a shared lock taken for the test. A shared probe never
   excludes another probe, and the holder locks its inode before publishing, so a probe can never
   make a holder's acquisition fail.

It is called only with the guard bytes already read (`read_guard` / `read_plan_approval_guard`) under
the guard's serialization lock, so the path names one inode for the whole decision.

**Public probe** (the function a later milestone calls):

`guard_holder_is_running(repo_root, work_item_id) -> bool`

It takes `guard_mutation_lock`, reads the guard with `read_guard`, and returns `False` when no guard
is published, else the helper's answer. Its contract, stated in its docstring and in
`docs/CONCURRENCY_INVARIANTS.md`:

- `True`: another process holds the lock of the guard now published, so a window of this work item
  is running. A `fork`ed child of the holder is another process too: it is refused and answers
  `True` while the holder lives (D-Fork).
- `False`: no guard is published, or the published guard's holder holds no lock: it crashed, or the
  guard was published by a release before 2.18.6, which keeps no lock (the gap the downgrade posture
  and the page name). A guard this process itself holds is not another process's, so it answers
  `False` for the caller's own window.
- **An undecidable guard raises** `CheckpointOwnershipUnavailableError` (from `read_guard`), never
  `False`: an unreadable guard is not evidence that nobody runs.
- It is not a proof about time outside a window: between two windows no guard exists. It answers "is a
  guarded window of this work item running now" and nothing more.
- Lock order: it takes (6) as a leaf, so a caller may hold (9) (the documented (9)->(6) edge) and
  must not hold the checkpoint guard it asks about. It writes nothing.

The plan-approval guard has no public probe here (one function, as the orchestrator asked): its
reclaim uses the private helper, and the page notes that the helper is the building block.

### D-Reclaim: the own-leftover branch asks first

In `_acquire_guard_locked`, the branch `role == "owner"`, same token **and** same worktree changes
from `reclaim = True` to: if `_guard_held_by_another_process(...)` raise
`CheckpointOwnershipUnavailableError` (message below), else `reclaim = True`. In
`_acquire_plan_approval_guard_locked` the branch `role == "owner"`, same token changes the same way and
raises `PlanApprovalGuardHeldError`. **Nothing else changes**: the superseded-epoch branch (a guard of
a rotated epoch is reclaimed with no proof, as always), the takeover-fence refusal, the foreign-
worktree refusal, the `takeover` and `recovery` branches (an authorized break of a locked guard still
works: the authorization, not liveness, is what those routes use), the generic refusal and every
existing message keep their condition and text byte for byte.

**The message** is true here and says the next step. It names the lease, the step and the class, says
that the process holding the guard's lock is still running and that a second window of the same
owner must not open beside it, and then one next step: wait for that window to finish and retry; if it
is certain that process is not doing this work, find it with `fuser <guard path>` and stop it. It
adds that a **crashed** holder holds nothing, so its leftover guard is reclaimed by the next entry
with no further step (the sentence that tells a reader which route clears a crashed holder: none is
needed). It does not say "foreign worktree" and does not name a takeover (a takeover cannot break a
destructive guard; for an ordinary one the existing authorization route is unchanged and unmentioned).

### D-Own: a lock held by the calling process is its own leftover

The helper answers `False` for a lease the calling process still holds. This is the rule that keeps
every currently legal sequence legal: a process that acquires a guard and never releases it, then
acquires again, is the "interrupted earlier step re-entering" that the branch exists for (and what
the existing in-process tests simulate); windows are strictly non-nested within a session, so a
second owner entry in the same process after an unreleased first one is never a concurrent window.
"This process" is exact across `fork` (D-Fork): an entry belongs to the process that took the lock,
never to a child that merely inherited the table. Threads are not told apart, exactly as `_held_primitives` is not thread-local (stated as a known gap
beside the existing one). Reclaiming such a lease closes its descriptor (D-Lock).

### D-Fork: a forked child owns nothing it inherited

`flock` follows the open file description, and `os.fork` copies both the descriptor and the module
global `_guard_holder_locks` into the child. Left alone, the child would treat the parent's live lease
as its own leftover (D-Own, probe step 1): a same-token owner acquisition in the child would reclaim
the parent's live guard and `guard_holder_is_running` would answer `False` while the parent's window
runs, which is the defect again and the under-report the probe must never give. So the rule is
process-exact: the module registers `os.register_at_fork(after_in_child=_forget_inherited_guard_locks)`
at import, and the hook clears `_guard_holder_locks` and `os.close`s every inherited descriptor in the
child (never `LOCK_UN`, which would release the parent's lock: closing a duplicate descriptor leaves
the description, and its lock, held by the parent). After the hook the child owns nothing, so it is
refused a same-token owner acquisition by a live holder, and its probe answers `True`; it also no
longer keeps a dead parent's guard looking live, so the fail-safe residue of an inherited lock does
not exist. A forked child that wants a window of its own acquires normally. The hook is the only
at-fork code, touches only this table, and cannot raise (an `OSError` from `os.close` is swallowed:
the child's copy is then merely a leaked descriptor of the parent's description). Residue that
remains, stated on the page: a `fork` made while another thread is between taking the lock and
recording it can inherit an untracked descriptor (threads are the existing gap), and a child that
`exec`s without `fork`'s hook is not affected (close-on-exec). The workflow's own code never forks
while holding a guard (`subprocess` children `exec`).

### D-Tests: deterministic, two real processes, no sleeps as synchronisation

A small worker (a constant of source in each test module, like the existing `_GUARD_WORKER_SOURCE`)
runs in a real child process and is driven over pipes: it writes one line when its window is open and
blocks reading its stdin; the test reads that line (a blocking read is the synchronisation), and
ends the window by writing a line or closing stdin. A crash is `proc.kill()` followed by
`proc.wait()`: the kernel has dropped the lock when `wait` returns, so no poll or delay is needed.

Tests, each shown red against the unfixed code first (the failures are recorded):

The new tests use their own worker constant; `_GUARD_WORKER_SOURCE` and its ready-file publication
(`publish_atomically(ready_path, json.dumps(lease))`) stay as they are, so
`TestPublishAtomically.test_the_worker_source_publishes_through_it` is untouched.

*Claim guard, `workflow_state_test.py` (a new class `TestLiveGuardVisibility`):*

1. **Live owner A, same-token B refused**, for `1d` (ordinary) and `1f-commit` (destructive): A holds
   the window, B's `acquire_guard`/`owner_mutation` raises `CheckpointOwnershipUnavailableError`
   with the new message (lease, step, "still running", the route), A's guard is untouched (same
   `lease_id`), B's body did not run, and `guard_holder_is_running` is `True` from the test process.
   Red first: on 2.18.5 B enters.
2. **A killed, B reclaims** (same two steps): after `kill` and `wait`, the leftover guard is still
   published, the probe says `False`, B's acquisition succeeds with a fresh `lease_id`, the old lease
   is gone, and the probe is `False` after B releases. Red first (the probe does not exist; the
   assertion that B was refused while A lived already fails).
3. **A releases, B enters**: no refusal after a normal release; no descriptor left in
   `_guard_holder_locks` of the test process after its own window.
4. **The probe**: no guard -> `False`; a guard this process holds -> `False`; a live other process ->
   `True`, and a second probe, and a probe while the holder is mid-window, leave the holder's lock
   and the guard untouched; a leftover (holder killed) -> `False`; an undecidable guard (torn bytes)
   -> raises, never `False`; a guard whose holder holds no lock (published as a pre-fix release
   does, with `_publish_claim_exclusive` and no lock) -> `False` (the documented gap, pinned so it
   cannot silently change).
5. **Unchanged routes with a locked guard**: a live-locked ordinary guard is still broken by
   `role="takeover"` with the quoted `lease_id` (the authorized break; A's later release leaves the
   new guard alone) and a live-locked destructive guard still refuses a takeover; a live-locked guard
   of a superseded epoch is still reclaimed with no proof; the takeover-fence refusal and its message
   are unchanged; the same-token other-worktree refusal and message are unchanged.
6. **Fork, both directions** (D-Fork): (a) *fail-open, red first on the plan as written*: a live
   holder forks a child that stays alive; the child's same-token `role="owner"` acquisition is
   refused with the new message, the parent's guard keeps its `lease_id`, and the child's
   `guard_holder_is_running` answers `True`; (b) the child's `_guard_holder_locks` is empty and its
   inherited descriptor closed; (c) the parent is killed while the child lives: the probe answers
   `False` at once (the child holds nothing) and a new owner reclaims the leftover.
7. **Descriptor hygiene**: after `release_guard`, after a reclaim of the process's own lease and after
   a lost publication race (`FileExistsError`), `_guard_holder_locks` is empty and the saved
   descriptor is closed.
8. **Regression pins**: `test_same_worktree_same_token_guard_reclaimed`,
   `test_superseded_epoch_guard_reclaimed_with_no_authorization`, the destructive-guard and
   abandoned-guard recovery tests pass unchanged.

*The one existing test that asserts the defect.* `TestSameWorktreeConcurrencyRealProcesses` pins "a
second process with the same token reclaims a live destructive guard and both windows stay open".
That assertion **is** the defect, so the fix necessarily rewrites this one test to the new contract
(the second process is refused while the first is parked; its leftover is reclaimed once the first is
killed), and its docstring is updated; it keeps using `_GUARD_WORKER_SOURCE`, or a new worker of its
own, never an edit of that constant. It is the only existing test whose assertion
changes; the plan states it here so the reviewer expects it. Every other existing guard, takeover
and recovery test passes unchanged.

*Journal guard, `workflow_integration_test.py` (beside the plan-approval guard tests):* the same
four cases with `plan_approval_guarded_mutation` on a real journal: live owner A refused to a
same-token B with `PlanApprovalGuardHeldError` and the new message; A killed then B reclaims;
the authorized-takeover break of a live-locked ordinary guard and the refusal of a destructive one
are unchanged; the superseded epoch is reclaimed; the existing
`test_owner_reclaims_its_own_leftover_guard_and_retries_once` passes unchanged.

*Journal sibling, `workflow_state_test.py`:* none beyond the above; the journal's own `.claim.<T>`
link, `take_over_plan_approval_transaction` and `rollback_plan_approval_transaction` are untouched and
covered by the existing suites, which must pass.

### D-Docs: `docs/CONCURRENCY_INVARIANTS.md` in the same change

CP1 updates the page: a "Kinds" bullet for the holder lock (a non-blocking `flock` on the guard's
own inode, not a numbered primitive, dropped by the kernel when its holder dies); rows (5) and (1):
who may acquire (the own-leftover reclaim now requires that no other process holds the guard's lock),
a crashed holder leaves (the guard, with no lock), the recovery route (a crashed holder: re-enter, no
other step; a live holder: wait, or stop the process named by `fuser`), the new tests; the probe as
the way to ask "is a window of this work item running"; and Known gaps: the same-worktree bullet
narrowed (a second process of the same owner is now refused; what remains is threads of one process,
guards published by a release before 2.18.6, which keep no lock, a `fork` racing a thread that is
mid-acquisition, and the two non-guard consequences already listed), the abandoned destructive plan-approval
guard bullet gains that the lock now distinguishes a crashed holder from a live one (the route stays
by hand, by design), and the checkpoint-start gap bullet is untouched. No internal milestone id
appears on the page (the docs checker). The "Last checked with" line moves with the release (CP2).

### D-Patch: the version is 2.18.6, `fix:`

`manifest.json` `workflow_version` 2.18.6; `WORKFLOW_RELEASE` and its two pinned assertions in
`workflow_protocol_test.py` follow, with the matching `ORCHESTRATION_PROTOCOL.md` edits (tested
releases list, envelope example, protocol-1.5 note); the protocol version stays. Why `fix:`: no state
key, ledger, phase, trailer, commit shape, guard-body key, protocol field, persisted vocabulary or
refusal code is added; a refusal that did not exist is new only in that a sequence which used to
silently open a second window now stops (the defect), and it uses the existing exception classes.

**Downgrade posture.** 2.18.6 writes no state, ledger or file an older release cannot read: a guard
it publishes has the same body, the same name and the same inode shape; the lock is a property of the
open file, not a byte on disk. `workflow-manager update` back to 2.18.5 restores the old reclaim, that
is, the defect (an own-token owner can reclaim a live owner's guard), and nothing else. Mixed
installs: a 2.18.6 acquirer sees a 2.18.5 holder as having no lock, so it reclaims that guard as
before (no new refusal, no new protection), and a 2.18.5 acquirer ignores a 2.18.6 holder's lock. The
manager block's posture and the release-history row say so.

### D-Staging: scratch staging for CP1 (the procedure W20 used)

`release.py stage-conformance` and `tools/release/release_test.py` verify the manifest against the
tree, and CP1 changes shipped files whose digests (and the suites' measured test counts) the committed
manifest records only at CP2. So CP1 verifies in a disposable clone (a full `git clone` of this
repository under `$TMPDIR`): a scratch script recomputes `sha256` and `size` of every `artifacts` and
`templates` record whose file differs from its record, measures and rewrites
`manager.conformance.suites` (digests, sizes and counts; the same discovery `release.py manager-block
--release-dir <scratch> --write` uses), commits it in the clone, and the "Verification commands"
blocks run from there. No rationale is touched in the scratch.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
|---|---|---|
| OD-1 | The version: patch 2.18.6 (`fix:`) or minor | **Patch, `fix:`.** Nothing persisted or reported changes; say otherwise in review and the release becomes a `feat:` minor. |
| OD-2 | The exception classes of the two new refusals | **The existing ones** (`CheckpointOwnershipUnavailableError`, `PlanApprovalGuardHeldError`): each is what its neighbouring "held" refusals raise, callers already catch them, and a new class would be a new refusal code. |
| OD-3 | The manager CI pin | **No change.** `manager-pin.json` (1.13.0) equals `min_manager_version` (1.13.0). |
| OD-4 | Lock on the guard's inode or a sibling lock file | **The inode** (D-Lock): no gap before publication, no new file, no residue. |
| OD-5 | A lock held by the calling process | **Its own leftover** (D-Own): keeps every in-process legal sequence legal; threads stay an honest gap. |
| OD-6 | A guard written by a release before 2.18.6 | **Reclaimable as today and reported as "no live holder"** by the probe (the gap is documented, not hidden); a later milestone that needs more must say so. |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does not
exist in this repository's release source).

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | A live holder's guard is visible and not reclaimable | - | 4 | 1 |
| CP2 | Release 2.18.6 | CP1 | 3 | 1 |

<!-- CP1 -->
### CP1 — A live holder's guard is visible and not reclaimable

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`,
`payload/scripts/workflow_integration_test.py`, `docs/CONCURRENCY_INVARIANTS.md`.

- **Tests first, red first** (D-Tests): the two-process, probe, unchanged-route, fork, hygiene and
  journal tests are written and run against the unedited `workflow_state.py`; the failures are
  recorded (the live-owner, probe and hygiene tests fail; the regression pins pass). **Done:** the
  recorded failures name each new test.
- **The mechanism** (D-Lock, D-Probe, D-Reclaim, D-Own): the process-local table, its at-fork hook, and three helpers,
  the lock taken before `os.link` in both publishers (through the one opt-in parameter of
  `_publish_claim_exclusive`), the close in both release paths, the two
  reclaim branches asking first, `guard_holder_is_running`, and the docstring entries of
  `acquire_guard` and `acquire_plan_approval_guard`. **Done:** `git diff` of `workflow_state.py` is
  those pieces only; every other branch's condition and message is byte for byte unchanged; no
  `os.link` or `LOCK_EX`-attribute `flock` site is added.
- **The one rewritten test** (`TestSameWorktreeConcurrencyRealProcesses`), as D-Tests states.
- **The page** (D-Docs), without its "Last checked with" line.
- **Roadmap:** `docs/ROADMAP.md` row 24a is `Current` from this plan; this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites (`TestGlobalLockOrderItem372h`
among them), the `tools/release` and `tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.18.6

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/RELEASING.md`, `docs/CONCURRENCY_INVARIANTS.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.18.6 with its two pinned assertions in `workflow_protocol_test.py` and
  the matching `ORCHESTRATION_PROTOCOL.md` edits; the protocol version stays.
- `manifest.json` 2.18.6: `workflow_version`; `sha256` and `size` of every record changed in CP1 and
  CP2 (`workflow_state.py`, `workflow_state_test.py`, `workflow_integration_test.py`,
  `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`); a `live-guard-visibility
  (workflow-2.18.6)` sentence on **each** changed artifact record, true of THAT file and read against
  `git diff 2865182..HEAD -- <file>`; the `manager` block: `min_manager_version` 1.13.0 (equal to the
  CI pin), `downgrade_boundary.posture` per D-Patch, `signals`, `new_work_only` and
  `gate_default_change` empty, `conformance.suites` (digests, sizes and test counts) measured by
  `release.py manager-block --release-dir <scratch> --write` from a staging of CP2's own content,
  never typed.
- `docs/release-history.md`: the 2.18.6 row (it closes #91 and leaves #55 open for the checkpoint-
  start release; names the holder lock, the probe, the refusal and its route, the pre-2.18.6 gap and
  the way back) and the "Last checked with" line; `docs/RELEASING.md`: any test count it states
  follows the measured count, no other change; `docs/CONCURRENCY_INVARIANTS.md`: "Last checked
  with: Workflow 2.18.6".
- `tools/release/release_test.py`: a 2.18.6 release class (version, release constant, the posture
  and history needles, counts); the 2.18.5 class keeps what stays true of that release and no longer
  pins the current version, constant or posture.
- `docs/ROADMAP.md` is not written by this checkpoint: row 24a becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD`
fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is
clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
|---|---|---|---|
| #91, claim guard | The own-leftover reclaim refuses a guard whose lock another process holds; a crashed holder's leftover is still reclaimed | CP1 | D-Lock, D-Reclaim |
| #91, journal guard | The same rule for the plan-approval guard | CP1 | D-Reclaim |
| #91, liveness probe | `guard_holder_is_running`, with its own tests | CP1 | D-Probe |
| Concurrency page | Rows (5) and (1), the new kind, the Known gaps | CP1, CP2 | D-Docs |
| Release | 2.18.6 bookkeeping, closes #91 only; #55 stays open | CP2 | D-Patch |

The artifact declaration `docs/ai-workflow/registry/live-guard-visibility-artifacts.json` is generated
by `workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its
plan-stage protected paths, and self-review checked that every path named in a Files paragraph, and
every other path this plan names (`docs/ROADMAP.md`, `docs/RELEASING.md`, `docs/release-history.md`,
`docs/CONCURRENCY_INVARIANTS.md`), is classified at both stages and that every deliverable is protected
at the implementation stage.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands", and the manifest key is
`workflow_version`. Each flow names its workspace.

| Flow | Workspace | What it shows |
|---|---|---|
| f1 | a scratch repository (the test harness's `ScratchRepo`) | a live owner A parked in `1f-commit`; a same-token process B is refused with the new message and A's guard is untouched |
| f2 | the same scratch repository | A killed with `kill -9`; B then reclaims and the probe reports no live holder |
| f3 | a scratch repository with an opened plan-approval journal | the same two flows for the journal guard |
| f4 | a scratch repository, two worktrees | an authorized takeover still breaks a live ordinary guard and still refuses a destructive one |
| f5 | the staged conformance fixture of the candidate (`stage-conformance`) | the nine suites, `tools/release` (zlib-ng environment) and `tools/docs`, `check-manager-block` |
| f6 | the checkout | `docs/CONCURRENCY_INVARIANTS.md` states the lock, the probe contract and the narrowed gaps |
