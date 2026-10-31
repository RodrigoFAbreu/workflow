# Active Milestone

## Milestone

**Complete (accepted by policy).** W35: `ci-latest-check-run` (`process`, governing version `2.2`), branch
`milestone/ci-latest-check-run`, roadmap row 30 (RodrigoFAbreu/workflow#122). Plan:
`docs/ai-workflow/CI_LATEST_CHECK_RUN_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.25.3 (a
`fix:` patch, released after the merge of the pull request): the pull-request check state judges the latest run of each
check, so a failed run and a green re-run no longer leave `checks.state` at `failure`. Base commit `198b82b`; the
previous milestone, W34 `retention-polish`, is accepted (Workflow 2.25.2).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The latest run per check: the change, its tests and its sentence | **complete** |
| CP2 | Release 2.25.3 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `f2568828`, reviewed implementation head `63fb238`.
- The 11 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/ci-latest-check-run-dispositions.json` (3 fixed, 8 follow-ups on
  RodrigoFAbreu/workflow#137).
- Functional review: flows 1 to 3 by the Controller's automated tester (run `controller:20261031T112323Z-ce7d795e`);
  flows h, 7 and 8 by an independent executor (run `manager-orchestrator:runs-workflow/w35-functional-r1`); all passed
  at the approved content. The evidence is recorded in `WORKFLOW_STATE.json`.
- Acceptance: pull request #138 at `6212ca6`, checks green, read by the Workflow's own `gh` query.

## Next action

W35 `ci-latest-check-run` is accepted by policy (Workflow 2.25.3 is released after the merge of the pull request).
Choose the next row of `docs/ROADMAP.md` with the owner before running `/milestone-plan`.
