# W20: Workflow 2.18.5 — fence a takeover against the live owner (Revision 1)

- **Work item:** `takeover-fence` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner chose this on 2026-10-22, when W19 (#55,
  row 24) was paused. It is row 23 of `docs/ROADMAP.md` (status `Current` from this plan, `Done` at
  acceptance).
- **Issue:** RodrigoFAbreu/workflow#82.
- **Branch:** `milestone/takeover-fence`
- **Base commit:** `0f74e24` (main after #83: the release source is Workflow 2.18.4; this
  repository's own installation is also 2.18.4, automatic gates, default `2.2`, no
  `GATE_POLICY.json`, no backlog file declared, so the prose roadmap applies)
- **Plan revision:** 1. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.5, a patch release (`fix:`), that closes #82: a takeover must not be enterable by
the owner it is taking over from.

**The defect.** `take_over_claim` publishes its guard (`step="takeover"`) carrying the observed old
owner token T, in the worktree that runs the takeover, and only then rotates the claim to a fresh
token T'. Until the rotation, a live owner in that same worktree that still holds T presents
`role="owner"`, token T, same worktree, and `_acquire_guard_locked`'s same-token/same-worktree
branch reclaims the takeover's guard. The owner's window then passes `assert_claim_owner(T)` (the
claim still names T), and the takeover goes on to publish T' without checking that its guard is still
its own, so the owner's already-validated window can run (`complete_checkpoint` recreates the entry
with `setdefault`). The plan-approval journal has the same shape: `_acquire_plan_approval_guard_locked`
reclaims for `role="owner"` whenever the held guard's token equals the presented one, with no step
check, while `take_over_plan_approval_transaction` publishes its guard as `step="takeover"` with the
observed token. Both were reproduced: W19's external review reproduced the claim case, and this
plan's probe (a hook just before `_publish_claim_replacing`, token T, step `1f-commit`) shows the
owner entering the window on 2.18.4.

**The fix** ("D-Handoff", validated by W19's reviews and replayed by Codex): one new branch in each of
the two acquisition decisions, placed after the superseded-epoch branch and before the same-token
reclaim, that refuses a `role="owner"` acquisition of a current-epoch guard whose step is `takeover`
and whose token (and, for the claim guard, worktree) is the caller's own. It raises an existing
exception class with its own, accurate message. Every other branch keeps its condition and its
message byte for byte.

Why `fix:` and not `feat:` (OD-1): no state key, ledger, phase, trailer, commit shape, protocol
field, persisted vocabulary or refusal code is added; the way back is stated in D-Patch.

### Hard limits (invariants)

- **No new command, state field, ledger, phase, trailer, commit shape or protocol change.** Refusal
  codes keep their names: the claim guard's new branch raises the existing
  `CheckpointOwnershipUnavailableError`, the journal guard's the existing `PlanApprovalGuardHeldError`
  (OD-2). No Controller or Manager change: `min_manager_version` stays 1.13.0 and the CI pin in
  `tools/release/manager-pin.json` must EQUAL it.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`,
  `docs/ai-workflow/` managed documents, `.workflow-manager/`, the managed blocks of `CLAUDE.md`
  and `.gitignore`, and `.github/workflows/workflow-conformance.yml`. The fix goes to `payload/`;
  release bookkeeping to `manifest.json`, `docs/` user documents and `tools/release/`.
- **Size:** two checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test, shown to fail against the unfixed code first; the
  nine payload suites from a staged fixture; the `tools/release` tests (in the zlib-ng environment);
  the `tools/docs` tests and checker; `check-manager-block` with `--manager-releases`;
  `workflow-manager verify .` clean. Every command form is copied from `docs/RELEASING.md`,
  "Verification commands".
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against `git diff`
  (CP2).

## 2. Facts this plan relies on (re-checked against `0f74e24`)

- **Claim guard** (`payload/scripts/workflow_state.py`, `_acquire_guard_locked`): after the
  create-if-absent attempt and the `held is None` retry, the decision is an `if/elif` chain over
  `held`: (1) superseded epoch (`decidable` and the claim is absent or its token differs from the
  guard's), reclaim; (2) `role == "owner"`, same token **and** same worktree, reclaim; (3)
  `role == "owner"`, same token, different worktree, refuse with the foreign-worktree message (its
  text says "presenting the claim's token is not being the holder"); (4) `role == "takeover"`; (5)
  `role == "recovery"`. Anything not reclaimed refuses with the generic "held by lease" message.
- **Takeover entry** (`_take_over_claim_window`): `acquire_guard(holder_owner_token=<observed T>,
  step="takeover", step_class=ORDINARY, role="takeover", authorized_lease_id=<observed guard's
  lease or None>)`, then `observe_claim`, then `_publish_claim_replacing`, then `release_guard` in a
  `finally`. A takeover can be run from the owner's own worktree (the probe did), so the guard it
  publishes has the owner's token **and** the owner's worktree: exactly the reclaim branch's
  conjunct.
- **Journal guard** (`_acquire_plan_approval_guard_locked`): (1) the held guard's token differs from
  the journal's current `owner_token` (or there is no journal), reclaim; (2) `role == "owner"` and the
  token equals the presented one, reclaim; (3) `role == "takeover"`; else refuse with
  `PlanApprovalGuardHeldError`. The guard has no worktree field. `take_over_plan_approval_transaction`
  acquires with `step="takeover"`, `step_class="ordinary"`, `holder_owner_token=T`, then re-verifies,
  rotates with `_replace_plan_approval_journal`, and releases in a `finally`.
- **After the rotation** the old owner is already refused: the takeover's guard names T, the claim (or
  journal) now names T', so the superseded-epoch branch lets the old owner reclaim the guard, and
  `assert_claim_owner(T)` (or `assert_plan_approval_journal_owner`) then refuses. The probe shows
  `CheckpointOwnershipStateMismatchError` for the claim. The defect is the window **before** the
  rotation, which is why the tests observe both sides in one test.
- **Only a takeover writes `step="takeover"`.** The owner's own steps are `1d`, `1f-commit` and the
  like; the journal's are `step-5-declaration-pin`, `step-6.2-stage-ordinary` and the like. No
  existing test acquires `role="owner"` against a `step="takeover"` guard.
- **Where a leftover takeover guard comes from.** `release_guard` runs in a `finally`, so a leftover
  takeover guard is a takeover process that died (killed) between publishing its guard and releasing
  it, with the claim (or journal) still naming T. The guard is well-formed, `ordinary`, current-epoch.

## 3. Design decisions

### D-Handoff: a takeover's guard is not the owner's to reclaim

**Claim guard.** A new `elif`, directly after the superseded-epoch branch and before the
same-worktree reclaim branch:

`role == "owner"` and `held["step"] == "takeover"` and `held["holder_owner_token"] ==
holder_owner_token` and `held["holder_worktree_git_dir"] == <this worktree>` → raise
`CheckpointOwnershipUnavailableError` with a message of its own.

Properties: it is reached only when the superseded-epoch branch did not reclaim, so it concerns a
**current-epoch** takeover guard (and, when the claim cannot be judged, `decidable` is false and the
guard is also refused: the fail-closed direction). It does not touch `role == "takeover"`
or `"recovery"`, a different token, or a different worktree: the foreign-worktree same-token case still
reaches branch (3) with its own message, which is true there. The existing branches keep their
conditions and messages byte for byte; a test pins the foreign-worktree message and the same-step
reclaim of a non-takeover guard.

**Journal guard.** The same rule: after the superseded-epoch branch and before the owner reclaim,
`role == "owner"` and `held["step"] == "takeover"` and the held token equals the presented one → raise
`PlanApprovalGuardHeldError` with a message of its own. The journal guard is repository-scoped with no
worktree, so the conjunct is the token alone, as the existing owner reclaim already uses.

**The messages (LPR-R6-001).** Neither falls into a message that is false here. Each says, in one
sentence, what is true: the guard is a takeover's, it carries this session's own token, a takeover of
this claim (or transaction) is in progress or was left by one that died before it rotated, and this
session must not enter its own window; then one next step (below). They do not say "foreign worktree"
or "another session's window".

**The next step for a leftover takeover guard (LPR-R6-002).** A takeover that died leaves a
well-formed, `ordinary`, current-epoch guard. Of the existing routes:

- `clear_malformed_guard` refuses a well-formed guard (it removes only an undecidable one): **not it.**
- `recover_abandoned_destructive_guard` refuses a guard that is not `destructive`, and a takeover
  guard is `ordinary`: **not it.**
- Waiting does nothing: no timeout or liveness inference exists, by design.
- **Re-running the takeover is the route.** `takeover_evidence` reports the guard; the takeover's
  `role="takeover"` acquisition reclaims a current-epoch ordinary guard whose `lease_id` the
  authorization quoted (the guard-release literal), and then rotates. For the claim guard that is
  `workflow_state.takeover_evidence(...)`, then `take_over_claim(...)` with the takeover literal and
  `guard_release_authorization_literal(guard)`; for the journal guard it is `/approve-review plan
  <id>` step 4b (`plan_approval_takeover_evidence`, then `take_over_plan_approval_transaction(...)`
  with the takeover literal and `plan_approval_guard_release_authorization_literal(guard)`).

Each message names that route for its own guard. Where a takeover is still live (a running process),
the same sentence says to let it finish: the old owner is then displaced and its next
`assert_claim_owner` (or journal owner assertion) refuses, as today. A test proves the named route
clears a leftover takeover guard for both guards (the owner is refused, the takeover is re-run with
both literals, the guard is gone, the new owner can enter).

**Step 1c's escape hint is unaffected.** `_ownership_escape_hint` ("continue it here — no takeover
applies") is attached only to step 1c's origination refusals, which precede any guard acquisition;
this refusal is raised at step 1d's `owner_mutation` and carries its own route.

**Docstrings.** `acquire_guard`'s and `acquire_plan_approval_guard`'s decision lists each gain the
new rule in the position it has in the code. The historical design record shipped as
`WORKFLOW_V2_PLAN.md` narrates the guard's design revision by revision and is not edited (a
published design record is not rewritten for a patch); no command file or operator document states
the reclaim rule, so the docstrings and the refusal messages are the documentation of the new rule.

**Tests (deterministic, no sleeps, no threads).** Interleaving is made by wrapping the primitive the
takeover calls at the interesting instant, so each observation happens at a known point:

- *Claim, before and after the rotation, for step `1d` (ordinary) and `1f-commit` (destructive).*
  Wrap `ws._publish_claim_replacing` so that before delegating it tries
  `owner_mutation(repo.root, "wi", T, ..., step=<step>)` and after delegating it tries again. Assert:
  before, the attempt raises `CheckpointOwnershipUnavailableError`, with its own message, the body does
  not run and the takeover's guard (its `lease_id`) is still the held guard; after, the attempt raises
  the existing rotated-claim error and the body does not run; the takeover returns a record whose token
  is not T and the guard is released at the end. Red first: on 2.18.4 the first attempt enters.
- *Claim, leftover.* Publish a takeover guard with `acquire_guard(role="takeover")` and never release
  it (the dead takeover); assert `owner_mutation` is refused with the message that names
  `take_over_claim` and the guard-release literal; then run `takeover_evidence`, `take_over_claim` with
  both literals; assert the guard is gone, the claim rotated and the new token can enter. Red first.
- *Claim, regression pins.* The same-token, other-worktree acquisition against a takeover guard
  still gets the existing foreign-worktree message (unchanged text); the existing
  `test_same_worktree_same_token_guard_reclaimed` and `test_superseded_epoch_guard_reclaimed_with_no_authorization`
  still pass. These pass on 2.18.4 by design (they pin what must not move).
- *Journal*, the same three in `workflow_integration_test.py` beside the existing plan-approval guard
  tests: a hook on `ws._replace_plan_approval_journal`, an owner `plan_approval_guarded_mutation`
  attempt before (refused with `PlanApprovalGuardHeldError`, own message) and after (refused by the
  existing owner assertion) the rotation; the leftover route through
  `take_over_plan_approval_transaction`; and the existing leftover-owner test unchanged.

Each interleaving and leftover test makes its before-rotation observation in the same test as its
after-rotation one, so the whole test fails red on 2.18.4; the after-rotation half alone already
passes there (the superseded-epoch branch plus the owner assertion), which is the point of keeping
the new branch from disturbing it.

### D-Patch: the version is 2.18.5, `fix:`

`manifest.json` `workflow_version` 2.18.5; `WORKFLOW_RELEASE` and its two pinned assertions in
`workflow_protocol_test.py` follow, with the matching `ORCHESTRATION_PROTOCOL.md` edits (tested
releases list, envelope example, protocol-1.5 note); the protocol version stays.

**Downgrade posture.** 2.18.5 writes no state, ledger or file an older release cannot read: the
guard it refuses is one 2.18.4 already writes, in the same shape. `workflow-manager update` back to
2.18.4 restores the old reclaim, that is, the defect (a live same-worktree owner can reclaim a
takeover's guard), and nothing else. The manager block's posture says so, and that W19's draft
was never released.

### D-Staging: scratch staging for CP1 (the procedure W16 to W18 used)

`release.py stage-conformance` and `tools/release/release_test.py` verify the manifest against the
tree, and CP1 changes shipped files whose digests (and the suites' measured test counts) the
committed manifest records only at CP2. So CP1 verifies in a disposable clone (a full `git clone` of
this repository under `$TMPDIR`): a scratch script recomputes `sha256` and `size` of every `artifacts`
and `templates` record whose file differs from its record, measures and rewrites
`manager.conformance.suites` (digests, sizes and counts; the same discovery `release.py manager-block
--release-dir <scratch> --write` uses), commits it in the clone, and the "Verification commands"
blocks run from there. No rationale is touched in the scratch.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
|---|---|---|
| OD-1 | The version: patch 2.18.5 (`fix:`) or minor | **Patch, `fix:`.** Nothing persisted or reported changes; say otherwise in review and the release becomes a `feat:` minor. |
| OD-2 | The exception classes of the two new branches | **The existing ones** (`CheckpointOwnershipUnavailableError`, `PlanApprovalGuardHeldError`): each is the class its neighbouring "held" refusals raise, callers already catch them, and a new class would be a new refusal code. |
| OD-3 | The manager CI pin | **No change.** `manager-pin.json` (1.13.0) equals `min_manager_version` (1.13.0). |
| OD-4 | An undecidable claim (the epoch cannot be judged) with a takeover guard | **Refuse** (the new branch does not depend on `decidable`), the fail-closed direction the code already takes for reclaiming. |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does not
exist in this repository's release source).

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | A takeover's guard is not the owner's to reclaim | - | 3 | 1 |
| CP2 | Release 2.18.5 | CP1 | 3 | 1 |

<!-- CP1 -->
### CP1 — A takeover's guard is not the owner's to reclaim

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`,
`payload/scripts/workflow_integration_test.py`.

- **Tests first, red first** (D-Handoff): the claim and journal interleaving, leftover-route and
  regression-pin tests are written and run against the unedited `workflow_state.py`; the failures
  are recorded (the interleaving and leftover tests fail, the pins pass). **Done:** the recorded
  failures name each new test.
- **The two branches** and the two docstring entries. **Done:** `git diff` of `workflow_state.py`
  is the two new branches (each with its message) and the two docstring entries only; every other
  branch's condition and message is byte for byte unchanged.
- **Roadmap:** `docs/ROADMAP.md` row 23 is `Current` from this plan; this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites, the `tools/release` and
`tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.18.5

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/RELEASING.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.18.5 with its two pinned assertions in `workflow_protocol_test.py` and
  the matching `ORCHESTRATION_PROTOCOL.md` edits; the protocol version stays.
- `manifest.json` 2.18.5: `workflow_version`; `sha256` and `size` of every record changed in CP1 and
  CP2 (`workflow_state.py`, `workflow_state_test.py`, `workflow_integration_test.py`,
  `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`); a `takeover-fence
  (workflow-2.18.5)` sentence on **each** changed artifact record, true of THAT file and read against
  `git diff 0f74e24..HEAD -- <file>`; the `manager` block: `min_manager_version` 1.13.0 (equal to the
  CI pin), `downgrade_boundary.posture` per D-Patch, `signals`, `new_work_only` and
  `gate_default_change` empty, `conformance.suites` (digests, sizes and test counts) measured by
  `release.py manager-block --release-dir <scratch> --write` from a staging of CP2's own content,
  never typed.
- `docs/release-history.md`: the 2.18.5 row (it closes #82 and leaves #55 open for W19; names the
  fence, the leftover route and the way back) and the "Last checked with" line; `docs/RELEASING.md`:
  any test count it states follows the measured count, no other change.
- `tools/release/release_test.py`: a 2.18.5 release class (version, release constant, the posture and
  history needles, counts); the 2.18.4 class keeps what stays true of that release and no longer pins
  the current version, constant or posture.
- `docs/ROADMAP.md` is not written by this checkpoint: row 23 becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD`
fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is
clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
|---|---|---|---|
| #82, claim guard | A `role="owner"` acquisition of the caller's own current-epoch takeover guard is refused, with its own message and next step | CP1 | D-Handoff |
| #82, journal guard | The same rule for the plan-approval guard | CP1 | D-Handoff |
| Leftover takeover guard | The refusal names the route that clears it: re-run the takeover with the guard-release authorization | CP1 | D-Handoff |
| Release | 2.18.5 bookkeeping, closes #82 only; #55 stays open | CP2 | D-Patch |

The artifact declaration `docs/ai-workflow/registry/takeover-fence-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its
plan-stage protected paths, and self-review checked that every path named in a Files paragraph, and
every other path this plan names (`docs/ROADMAP.md`, `docs/RELEASING.md`, `docs/release-history.md`),
is classified at both stages and that every deliverable is protected at the implementation stage.
