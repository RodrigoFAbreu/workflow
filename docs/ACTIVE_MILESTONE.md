# Active Milestone

## Milestone

**In progress.** W32: `retention-prune-command` (`process`, governing version `2.2`), branch
`milestone/retention-prune-command`, roadmap row 27g (RodrigoFAbreu/workflow#123 item 1, #126 items 2 and 3). Plan:
`docs/ai-workflow/RETENTION_PRUNE_COMMAND_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.0 (a
`feat:` minor, released after the merge of the pull request): the user-only command `/prune-archives
<work-item-id>...`, which previews the dry run of `workflow_retention.py prune` and runs `--apply` only after the
literal sentence `Prune the archives <n1>, <n2>.` naming exactly the named archives. Base commit `8537d23`; the previous
milestone, W31 `retention-prune`, is accepted (Workflow 2.24.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The command, its tests and the documents | **in progress** |
| CP2 | Release 2.25.0 | pending |

## Verified state

- Gates: plan approval `CURRENT`, basis `POLICY_SATISFIED`.
- CP1: the command file, `TestPruneArchivesCommand` and the moved tripwires, the three payload documents,
  `docs/RETENTION.md` and the four release classes' counts (83/57) are written; verification runs in a disposable clone.

## Next action

Finish CP1 verification and commit; then `/milestone-implement` again for CP2 (Release 2.25.0).
