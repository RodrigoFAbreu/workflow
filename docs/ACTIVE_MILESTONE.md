# Active Milestone

## Milestone

**Complete (accepted by policy).** W38: `retention-report-unreadable` (`process`, governing version `2.2`), branch
`milestone/retention-report-unreadable`, roadmap row 33 (RodrigoFAbreu/workflow#113 item 1, #116 item 1 and #119
item 8). Plan: `docs/ai-workflow/RETENTION_REPORT_UNREADABLE_PLAN.md` (revision 3, approved by gate policy). The goal,
Workflow 2.25.6 (a `fix:` patch, released after the merge of the pull request): the retention report says
`archive unreadable` / `review folder unreadable` where it cannot tell (a partly counted folder is a lower bound),
`review folder in .removing` for a folder an interrupted removal left, and records the failed directory itself in
`read_errors`. The JSON, every refusal code and exit code stay as they are. Base commit `e687d51`; the previous
milestone, W37 `retention-error-paths`, is accepted (Workflow 2.25.5).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The report text, the recorded path, tests and page | **complete** (see the commit of this checkpoint) |
| CP2 | Release 2.25.6 | **complete** (see the commit of this checkpoint) |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `eb1b13eb`, reviewed implementation head `d6e056a`.
- The 13 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/retention-report-unreadable-dispositions.json` (8 follow-ups on
  RodrigoFAbreu/workflow#149, 5 dropped with a reason).
- Functional review: flows 1 to 4 by the Controller's automated tester (run `controller:20261105T060059Z-0cffef92`),
  flows 5 to 8 by an independent headless executor (run `manager-orchestrator:runs-workflow/w38-functional-r1`), all
  recorded passed at the approved content. Flow 8 failed on a strict reading of the checklist: its Expect over-claimed,
  and the orchestrator recorded it passed with the reason in the record's summary (follow-up item 7 of #149).
- Acceptance: pull request #150 at `30b61bf`, checks green, read by the Workflow's own `gh` query.

## Next action

W38 `retention-report-unreadable` is accepted by policy (Workflow 2.25.6 is released after the merge of the pull
request). No row of `docs/ROADMAP.md` is scheduled and incomplete: rows 12, 13 and 24 are waiting or paused and row 27
is unscheduled. Confirm the next milestone with the owner before running `/milestone-plan`.
