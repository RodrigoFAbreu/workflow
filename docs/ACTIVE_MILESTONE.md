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
| CP1 | The command, its tests and the documents | **complete** (`8fd9885`) |
| CP2 | Release 2.25.0 | **complete** (see the commit carrying `Workflow-Checkpoint: CP2`) |

## Verified state

- Gates: plan approval `CURRENT`, basis `POLICY_SATISFIED`.
- CP1: the command file, `TestPruneArchivesCommand` and the moved tripwires, the three payload documents,
  `docs/RETENTION.md` and the four release classes' counts (83/57), committed as `8fd9885`.
- CP2: `WORKFLOW_RELEASE` 2.25.0 with its two assertions and the protocol document, `manifest.json` 2.25.0 (the
  command record, counts 83/57, the changed records, the posture, `conformance.suites` measured), the 2.25.0 row of
  `docs/release-history.md`, the "Last checked with" line of `docs/RETENTION.md`, and a 2.25.0 class in
  `tools/release/release_test.py` (the 2.24.0 class gives up the current-release pins). Verified in a disposable clone
  committed from this tree: `tools/release` (293 tests, zlib-ng interpreter), `tools/docs`, `check_docs.py` and
  `check-manager-block` pass; the stock `stage-conformance` fixture, the nine suites and `build` are reported in the
  implementation bundle's `TEST_RESULTS.md`.

## Next action

Self-review the full milestone diff, run the full verification, then `/milestone-implement` again to prepare the
implementation bundle and stop at the review gate.
