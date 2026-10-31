# Active Milestone

## Milestone

**Complete (accepted by policy).** W37: `retention-error-paths` (`process`, governing version `2.2`), branch
`milestone/retention-error-paths`, roadmap row 32 (RodrigoFAbreu/workflow#119 item 1 and #113 item 2). Plan:
`docs/ai-workflow/RETENTION_ERROR_PATHS_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.5 (a
`fix:` patch, released after the merge of the pull request): an unreadable symlink in a review folder, and a state
file or tracked path that is not valid UTF-8, are coded refusals (exit 2, a `next step:`) instead of a traceback.
Base commit `69ebb46`; the previous milestone, W36 `check-time-by-value`, is accepted (Workflow 2.25.4).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The helpers, their call sites, tests and documents | **complete** |
| CP2 | Release 2.25.5 | **complete** (see the commit of this checkpoint) |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `8664a0e4`, reviewed implementation head `c7f863f`.
- The 13 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/retention-error-paths-dispositions.json` (5 fixed, 4 dropped, 4 follow-ups on
  RodrigoFAbreu/workflow#143).
- Functional review: flows 1 to 9 by the Controller's automated tester (run `controller:20261031T191455Z-45ffe2b0`),
  all passed at the approved content. The evidence is recorded in `WORKFLOW_STATE.json`.
- Acceptance: pull request #144 at `be97c94`, checks green, read by the Workflow's own `gh` query.

## Next action

W37 `retention-error-paths` is accepted by policy (Workflow 2.25.5 is released after the merge of the pull request).
The next incomplete row of `docs/ROADMAP.md` is row 33 (the retention report says `unreadable` where it cannot tell);
confirm it with the owner before running `/milestone-plan`.
