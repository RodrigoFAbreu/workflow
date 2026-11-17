# Active Milestone

## Milestone

**Implementing.** W58: `gate-policy-test-pins` (`process`, governing version `2.2`), branch `milestone/gate-policy-test-pins`, roadmap row 51
(RodrigoFAbreu/workflow#185 points 2 to 4, #143 point 3, #149 point 3, #190 point 4). The plan is
`docs/ai-workflow/GATE_POLICY_TEST_PINS_PLAN.md` (revision 3, approved by gate policy).

## Goal

Test-only: five tightenings and one new test in three payload test files; no script changes. Not taken: #185 point 1 (a code change).

## Progress

- CP1 (the pins p1 to p6 and roadmap row 51): implemented. G (`workflow_gate_policy_test.py`) 429 tests OK and I's edited class OK; T
  (`workflow_state_completion_obligations_test.py`) 317 tests OK (316 plus the new `RetentionReportUnreadable.test_t7`).
  Mutations m1 to m5 run in scratch copies of `payload/`: each fails exactly the test its plan row names (m1: the two `stale_changes` and
  `stale_failed` subtests of T4; m2: T5; m3: T3; m5: the new T7; m4: the demonstration, four other tests that patch `os.unlink` plus the new
  observed-call assertions of T6). m6 (the label line emitted twice) fails only the surviving `len == 1` assertion of p6.
- CP2 (release 2.29.9): not started.

## Next action

`/milestone-implement gate-policy-test-pins` for CP2.
