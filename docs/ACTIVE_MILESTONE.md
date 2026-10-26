# Active Milestone

## Milestone

**Complete (accepted by policy).** W28: `retention-archive` (`process`, governing version `2.2`), branch `milestone/retention-archive`,
roadmap row 27c (RodrigoFAbreu/workflow#84, step 3, and #113 items 3 and 4). Plan:
`docs/ai-workflow/RETENTION_ARCHIVE_PLAN.md` (revision 7, approved by gate policy). The goal, Workflow 2.21.0 (released after the merge of the pull request), a
`feat:` minor that adds the non-destructive archive creation, `scripts/workflow_retention.py archive <id>`: a dry run by
default, and with `--apply` it packs a finished item's untracked review folder into a verified `.tar.zst` outside the
repository, indexes it and makes it durable. It never removes, renames or modifies anything in the folder or the
repository. The removal (row 27d), the user-only command (27e) and the prune (27f) are not part of this item. The
previous milestone, W27 `retention-report`, is accepted (Workflow 2.20.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The archive engine, its tests and the documents | **complete** (verified in a scratch clone, see below) |
| CP2 | Release 2.21.0 | **complete** (verified in a stock `stage-conformance` fixture, see below) |

## Verified state

- CP1: `payload/scripts/workflow_retention.py` (`archive_item`, the `archive` subcommand, the `zstd` seam, and the report's
  four checks: a repository `.`/`..`, a symlinked per-repository directory, the ids `runtime`/`archive`, and the
  traversal anchored on a `.ai-review` descriptor), the `RetentionArchive` tests in
  `workflow_state_completion_obligations_test.py` (208 -> 240 counting the report's), `docs/RETENTION.md` (the section
  "The archive command" and the re-targeted row references) and `docs/exit-codes.md`. `git diff f1c78ef --stat -- payload`
  lists the script and its test file only. Each mutation the plan lists fails at least one test in a scratch copy (the
  results are in the implementation bundle's `TEST_RESULTS.md`).
- Verified in a disposable clone (D-Staging): the nine suites from the staged fixture, `tools/docs` (34),
  `check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng), and the new and the whole obligations tests under
  the orphan wrapper (no orphan beyond Git's own detached maintenance).

- CP2: `manifest.json` 2.21.0 (counts unchanged at 81, 6 and `distribution` 55; `sha256`, `size` and a `retention-archive
  (workflow-2.21.0)` sentence for the five changed records; the posture; `conformance.suites` measured), `WORKFLOW_RELEASE`
  2.21.0 with its two pinned assertions, `ORCHESTRATION_PROTOCOL.md`, the 2.21.0 row of `docs/release-history.md`, the
  "Last checked with" lines of the three pages, and the 2.21.0 release class of `tools/release/release_test.py`.

## Next action

Row 27d of `docs/ROADMAP.md`, Retention tool, step 4: the removal of an archived finished item's folder (its design is
open, so plan it with `/milestone-plan`). The Workflow 2.21.0 release follows the merge of this milestone's pull
request.
