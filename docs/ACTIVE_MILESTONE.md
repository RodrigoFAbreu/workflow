# Active Milestone

## Milestone

**Complete (accepted by policy).** W29: `retention-removal` (`process`, governing version `2.2`), branch `milestone/retention-removal`,
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
| CP2 | Release 2.22.0 | **complete** (verified in a scratch clone, see below) |

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

- CP2: `manifest.json` 2.22.0 (counts 81, 6, 55 unchanged; the five changed records carry their `retention-removal
  (workflow-2.22.0)` sentence, every digest and size recomputed, `conformance.suites` measured by `release.py
  manager-block --write`: obligations 240 -> 255, the others unchanged), `WORKFLOW_RELEASE` and its two pinned
  assertions, `ORCHESTRATION_PROTOCOL.md` (protocol stays 1.5), the 2.22.0 row of `docs/release-history.md` with the
  downgrade note, the "Last checked with" lines of the three pages, and `RetentionRemovalReleaseTest` in
  `tools/release/release_test.py` (the 2.21.0 class keeps what stays true of it).
- Verified in a scratch clone committed with the CP2 content: stock `stage-conformance --commit HEAD` and the nine
  suites, `release.py build` (zlib-ng, 88 files), `check-manager-block`, `tools/docs` (34) and `check_docs.py`, and
  `tools/release` (285, zlib-ng interpreter).

## Next action

W29 `retention-removal` is accepted by policy (Workflow 2.22.0 is released after the merge of the pull request). The
next incomplete roadmap row is 27e, the user-only archive command, which is planned after rows 27c and 27d: run
`/milestone-plan` when it is ready for `PLANNING`.
