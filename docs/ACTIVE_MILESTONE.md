# Active Milestone

## Milestone

**Complete** (accepted by policy; a `fix:` change, Workflow patch release 2.29.7 follows the merge). W55: `retention-test-pins`
(`process`, governing version `2.2`), branch `milestone/retention-test-pins`, roadmap row 48. The plan is
`docs/ai-workflow/RETENTION_TEST_PINS_PLAN.md` (revision 1, approved by gate policy); an archive copy is in
`docs/milestones/completed/`.

## Goal

Six tests in one class, `RetentionTestPins`, in `payload/scripts/workflow_state_completion_obligations_test.py`, pin retention lines
no existing test pinned (the future-mtime clamp, the default forge runner, a failed read, same-size altered bytes and the removal's
two re-checks). No line of `workflow_retention.py` changes and no behaviour changes.

## Outcome

- CP1 (the six pins) and CP2 (release 2.29.7: manifest, protocol constant, history row, release tests) are both complete.
- The technical approval was recorded by policy. Functional flows 1 to 11 are recorded passed (flows 1 to 3 by the Controller's
  automated tester, flows 4 to 11 by an independent headless executor). The 8 recorded Optional findings are dispositioned (2 fixed,
  1 dropped, 5 follow-ups in RodrigoFAbreu/workflow#194); see `docs/milestones/completed/retention-test-pins-findings.md`.

## Next action

No milestone is ready for planning: rows 12 and 13 wait on the Controller and row 27 is deferred and unscheduled. Merge pull request
#195; Workflow 2.29.7 is then published by the `Publish` workflow. After that, `/milestone-plan` when the owner names the next item.
