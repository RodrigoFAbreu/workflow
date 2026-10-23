# Active Milestone

## Milestone

**In functional review.** W20: `takeover-fence` (`process`, governing version `2.2`), branch
`milestone/takeover-fence`, roadmap row 23 (RodrigoFAbreu/workflow#82). Plan:
`docs/ai-workflow/TAKEOVER_FENCE_PLAN.md` (revision 1, approved by gate policy). The goal is Workflow
2.18.5, a patch release (`fix:`): a takeover's guard (`step="takeover"`) is not the owner's to reclaim,
in both the claim guard and the plan-approval journal guard. The previous milestone, W18
`review-followups-4`, is accepted (its record is in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | A takeover's guard is not the owner's to reclaim | **complete** |
| CP2 | Release 2.18.5 | **complete** |

## Functional review checklist

The Controller's functional tester runs offline in a sandbox: no network, no real `gh`/`claude`/`codex`/
`ssh`, a read-only product clone. Every flow below runs from a staged fixture in `$TMPDIR` and writes
nothing inside the clone. This milestone changes a Python state library, so the flows are
command-line runs of its suites and of the defect's reproduction; there is no UI.

### Setup

```bash
cd <product clone>                       # read-only; do not write here
export WORK="${TMPDIR:?}/tf"; rm -rf "$WORK"; mkdir -p "$WORK"
python3 tools/release/release.py stage-conformance --commit HEAD --out "$WORK/fixture"
```

Expected: the command exits 0 and `$WORK/fixture/scripts/` holds `workflow_state.py`,
`workflow_state_test.py` and `workflow_integration_test.py`. If `stage-conformance` cannot run in the
sandbox, say so in the findings and use flow 5 (read the diff) for what follows.

Test data: none to seed; the tests build their own scratch repositories and work items.

### Flows

1. **The new tests pass on the fixed code.**
   ```bash
   cd "$WORK/fixture/scripts"
   python3 -B -m unittest workflow_state_test.TestTakeoverGuardIsNotTheOwnersToReclaim -v </dev/null
   python3 -B -m unittest workflow_integration_test.TestPlanApprovalMutationGuardAndTakeover -v </dev/null
   ```
   Expected: both exit 0. The first runs 4 tests: `test_owner_cannot_enter_during_a_takeover_and_is_fenced_after_the_rotation`,
   `test_leftover_takeover_guard_names_the_route_and_the_route_clears_it`,
   `test_same_token_other_worktree_still_gets_the_foreign_worktree_message`,
   `test_non_takeover_guard_of_the_same_token_is_still_reclaimed`. The second includes the plan-approval
   journal counterparts of the first, second and fourth.

2. **The defect reproduces without the fix (red-first check).** Replace the fixture's
   `workflow_state.py` with the base commit's, in the scratch fixture only:
   ```bash
   git -C <product clone> show 0f74e24:payload/scripts/workflow_state.py > "$WORK/fixture/scripts/workflow_state.py"
   cd "$WORK/fixture/scripts"
   python3 -B -m unittest workflow_state_test.TestTakeoverGuardIsNotTheOwnersToReclaim </dev/null
   ```
   Expected: the run FAILS, and at least `test_owner_cannot_enter_during_a_takeover_and_is_fenced_after_the_rotation`
   and `test_leftover_takeover_guard_names_the_route_and_the_route_clears_it` are among the failures
   (the owner enters the takeover's window on 2.18.4). The foreign-worktree and non-takeover tests
   should still pass on the old code, since those branches are unchanged. Re-stage the fixture
   (setup command) before flow 3.

3. **The full payload suites still pass.**
   ```bash
   suites=$(python3 -c "import json; print(*json.load(open('manifest.json'))['manager']['conformance']['suites'], sep='\n')") && test -n "$suites" && ( cd "$WORK/fixture/scripts" && while read -r s; do python3 -B "$WORK/fixture/scripts/$s" </dev/null || exit 1; done <<< "$suites" )
   ```
   (run with the product clone as the working directory). Expected: exit 0 for all nine suites. This
   is long; if the sandbox time limit prevents it, report which suites completed.

4. **The refusal messages read correctly.** In the fixed `payload/scripts/workflow_state.py`, find the
   two new `takeover-fence (#82)` branches (in `_acquire_guard_locked` and
   `_acquire_plan_approval_guard_locked`). Expected: each message says the guard is a takeover's and
   carries the caller's own owner token, says to let a running takeover finish, and names the re-run
   route (`takeover_evidence` then `take_over_claim`, or `plan_approval_takeover_evidence` then
   `take_over_plan_approval_transaction`) with the guard-release literal. Neither mentions an owner
   "reclaiming" its own leftover.

5. **The diff is only what the plan allows.**
   ```bash
   git diff --stat 0f74e24..HEAD
   git diff 0f74e24..HEAD -- payload/scripts/workflow_state.py
   ```
   Expected: `workflow_state.py` gains exactly two `elif` branches plus docstring bullets; no existing
   branch condition or message changes; no new command, state field, ledger, phase, trailer or
   protocol field. The installation (`.claude/`, `scripts/`, `.workflow-manager/`) is untouched.

6. **Release bookkeeping agrees.** `python3 tools/docs/check_docs.py` exits 0; `manifest.json` names
   release 2.18.5 and `docs/release-history.md` has a 2.18.5 row that closes #82 (read, do not edit).
   Optional, if the zlib-ng environment is available:
   `python -m unittest discover -s tools/release -p '*_test.py'`.

### Known limitations and out of scope

- The live-owner race itself (a real second process entering mid-takeover) is exercised by the tests
  through a hook before the claim rotation, not by two real processes.
- A leftover takeover guard is cleared only by re-running the takeover; no new "force release" command
  exists, deliberately.
- Releasing 2.18.5 and the `workflow-manager` pin are after merge and out of scope; this repository's
  own installation stays at 2.18.4 until then.
- No pull request, GitHub or forge flow can run in the sandbox; none is needed here.

## Next action

Run the checklist above and place findings at the feedback path reported by `/prepare-functional-review`.
If testing is clean, `/accept-milestone` (every checkpoint is `COMPLETE`). Findings go to
`/apply-functional-review`.
