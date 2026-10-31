# Active Milestone

## Milestone

**Complete (accepted by policy).** W34: `retention-polish` (`process`, governing version `2.2`), branch
`milestone/retention-polish`, roadmap row 29 (RodrigoFAbreu/workflow#123 items 2 and 4, #132 items 1 and 2). Plan:
`docs/ai-workflow/RETENTION_POLISH_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.25.2 (a `fix:`
patch, released after the merge of the pull request): wording and test pins of finished retention work, no behaviour
change. Base commit `586c86c`; the previous milestone, W33 `retention-lstat-errors`, is accepted (Workflow 2.25.1).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The four in-scope items: wording, three assertions | **complete** |
| CP2 | Release 2.25.2 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `6a92aecf`, reviewed implementation head `49926f8`.
- The 8 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/retention-polish-dispositions.json` (5 fixed, 3 dropped with reasons).
- Functional review: flows 2 to 8 by the Controller's automated tester (run `controller:20261030T224932Z-5eae0773`);
  flow 1 (the automated suites) by an independent executor (run
  `manager-orchestrator:runs-workflow/w34-functional-r1`); all passed at the approved content. The evidence is recorded
  in `WORKFLOW_STATE.json`.
- Acceptance: pull request #135 at `03e9a36`, checks green, read by the Workflow's own `gh` query.

## Next action

W34 `retention-polish` is accepted by policy (Workflow 2.25.2 is released after the merge of the pull request).
No roadmap row is ready for `PLANNING`: rows 12, 13 and 24 are waiting or paused, and rows 26c and 27 are later and
unscheduled. Choose the next row with the owner before running `/milestone-plan`.
