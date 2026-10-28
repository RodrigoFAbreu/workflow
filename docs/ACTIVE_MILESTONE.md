# Active Milestone

## Milestone

**Complete (accepted by policy).** W32: `retention-prune-command` (`process`, governing version `2.2`), branch
`milestone/retention-prune-command`, roadmap row 27g (RodrigoFAbreu/workflow#123 item 1, #126 items 2 and 3). Plan:
`docs/ai-workflow/RETENTION_PRUNE_COMMAND_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.0 (a
`feat:` minor, released after the merge of the pull request): the user-only command `/prune-archives
<work-item-id>...`, which previews the dry run of `workflow_retention.py prune` and runs `--apply` only after the
literal sentence `Prune the archives <n1>, <n2>.` naming exactly the named archives. Base commit `8537d23`; the previous
milestone, W31 `retention-prune`, is accepted (Workflow 2.24.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The command, its tests and the documents | **complete** |
| CP2 | Release 2.25.0 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `f09fbbd0`, reviewed implementation head `026261f`.
- The 12 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/retention-prune-command-dispositions.json` (fixed, dropped with reasons, and one follow-up
  on RodrigoFAbreu/workflow#129).
- Functional review: flows 1 to 5 by the Controller's automated tester (run `controller:20261028T072722Z-8b4e4085`),
  flow 6, f1, f3, f4, f5, f6, f6b, f7 and f8 by an independent Claude executor (`claude-sonnet-5-5`, scratch
  repositories); all passed at the approved content. The evidence is recorded in `WORKFLOW_STATE.json`.
- Acceptance: pull request #130 at `4a65b7c`, checks green, read by the Workflow's own `gh` query.

## Next action

W32 `retention-prune-command` is accepted by policy (Workflow 2.25.0 is released after the merge of the pull request).
No roadmap row is ready for `PLANNING`: rows 12, 13 and 24 are waiting or paused, and rows 26c and 27 are later and
unscheduled. Choose the next row with the owner before running `/milestone-plan`.
