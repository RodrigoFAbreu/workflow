# Active Milestone

## Milestone

**In progress.** W29: `retention-removal` (`process`, governing version `2.2`), branch `milestone/retention-removal`,
roadmap row 27d (RodrigoFAbreu/workflow#116 item 7, and the obligations EPR-001 and EPR-010). Plan:
`docs/ai-workflow/RETENTION_REMOVAL_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.22.0 (released
after the merge of the pull request), a `feat:` minor that adds the removal, `scripts/workflow_retention.py remove <id>`:
a dry run by default, and with `--apply` it takes a finished, archived item's untracked review folder out of the
repository with one atomic rename into `<archive-root>/<repo>/.removing/<id>`, verifies the archive against the moved
folder by contents (the listing and the SHA-256 of every file), and deletes it entry by entry, or renames it back and
refuses naming the difference. An interrupted run leaves one recognisable leftover, which the report lists and the next
run completes or renames back. The user-only command (27e) and the prune (27f) are not part of this item. The previous
milestone, W28 `retention-archive`, is accepted (Workflow 2.21.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The removal, its tests and the documents | **complete** (verified in a scratch clone, see below) |
| CP2 | Release 2.22.0 | not started |

## Verified state

- CP1: `payload/scripts/workflow_retention.py` (`_select_finished` extracted from `archive_item`, `remove_item`,
  `_archive_table`, `_hash_folder`, `_differences`, `_remove_tree`, the rename back, the `remove` subcommand, and the
  report's `removing` key and text line), the `RetentionRemove` tests in
  `workflow_state_completion_obligations_test.py` (240 -> 255), `docs/RETENTION.md` (the section "The remove command",
  the `removing` key, the archive table's new `unreadable` cause and the re-read references to rows 27c to 27f) and
  `docs/exit-codes.md`. `git diff 0c06330 --stat -- payload` lists the script and its test file only. Each mutation m1
  to m20 fails at least one named case in a scratch copy, and the control passes (the results are in the
  implementation bundle's `TEST_RESULTS.md`).
- Verified in a disposable clone (D-Staging): the nine suites from the staged fixture, `tools/docs` (34),
  `check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng), and the new and the whole obligations tests under
  the orphan wrapper.

## Next action

CP2, Release 2.22.0 (`/milestone-implement retention-removal`): `manifest.json`, the release constant and its pinned
assertions, `ORCHESTRATION_PROTOCOL.md`, the `docs/release-history.md` row, the "Last checked with" lines and the
2.22.0 class of `tools/release/release_test.py`.
