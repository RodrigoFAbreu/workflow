# Active Milestone

## Milestone

**Complete (accepted by policy).** W33: `retention-lstat-errors` (`process`, governing version `2.2`), branch
`milestone/retention-lstat-errors`, roadmap row 28 (RodrigoFAbreu/workflow#126 item 1). Plan:
`docs/ai-workflow/RETENTION_LSTAT_ERRORS_PLAN.md` (revision 4, approved by gate policy). The goal, Workflow 2.25.1 (a
`fix:` patch, released after the merge of the pull request): `_lstat_at` in `workflow_retention.py` turns a stat error
other than "not found" into a coded refusal with a `next step:` line (`unreadable` at the archive, remove and prune
sites, `restore_failed` while a refusal is undone, `prune_failed` at prune's step 9), instead of a traceback. No new
refusal code, state key, phase, trailer or command. Base commit `d101beb`; the previous milestone, W32
`retention-prune-command`, is accepted (Workflow 2.25.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The coded refusal, its call sites, tests and documents | **complete** |
| CP2 | Release 2.25.1 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `0b4f58ca`, reviewed implementation head `bea39a8`.
- The 13 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/retention-lstat-errors-dispositions.json` (fixed, dropped with reasons, and two follow-ups
  on RodrigoFAbreu/workflow#132).
- Functional review: flows 1 to 9 by the Controller's automated tester (run `controller:20261030T181910Z-022d2075`);
  all passed at the approved content. The evidence is recorded in `WORKFLOW_STATE.json`.
- Acceptance: pull request #133 at `45df3b3`, checks green, read by the Workflow's own `gh` query.

## Next action

W33 `retention-lstat-errors` is accepted by policy (Workflow 2.25.1 is released after the merge of the pull request).
No roadmap row is ready for `PLANNING`: rows 12, 13 and 24 are waiting or paused, and rows 26c and 27 are later and
unscheduled. Choose the next row with the owner before running `/milestone-plan`.
