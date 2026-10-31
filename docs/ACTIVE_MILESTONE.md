# Active Milestone

## Milestone

**Complete (accepted by policy).** W36: `check-time-by-value` (`process`, governing version `2.2`), branch
`milestone/check-time-by-value`, roadmap row 31 (RodrigoFAbreu/workflow#137, items 1 to 4). Plan:
`docs/ai-workflow/CHECK_TIME_BY_VALUE_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.4 (a
`fix:` patch, released after the merge of the pull request): the latest-run judge recognises the zero instant
`0001-01-01T00:00:00Z` by value, in every spelling that denotes it, so a green run can no longer supersede a failure
because of how the zero time is written. Base commit `e70ccb1`; the previous milestone, W35 `ci-latest-check-run`, is
accepted (Workflow 2.25.3).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The zero instant by value: the change, its tests, its sentence and the roadmap rows | **complete** |
| CP2 | Release 2.25.4 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `b68e2c7d`, reviewed implementation head `34881af`.
- The 10 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/check-time-by-value-dispositions.json` (5 fixed, 3 dropped, 2 follow-ups on
  RodrigoFAbreu/workflow#137).
- Functional review: flows 1 to 7 by the Controller's automated tester (run `controller:20261031T150737Z-f8815030`),
  all passed at the approved content. The evidence is recorded in `WORKFLOW_STATE.json`.
- Acceptance: pull request #140 at `c9458b0`, checks green, read by the Workflow's own `gh` query.

## Next action

W36 `check-time-by-value` is accepted by policy (Workflow 2.25.4 is released after the merge of the pull request).
Choose the next row of `docs/ROADMAP.md` with the owner before running `/milestone-plan`.
