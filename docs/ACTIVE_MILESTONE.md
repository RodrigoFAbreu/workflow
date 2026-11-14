# Active Milestone

## Milestone

**In progress.** W51: `retention-engine-error-paths-2` (`process`, governing version `2.2`), branch
`milestone/retention-engine-error-paths-2`, roadmap row 44 (RodrigoFAbreu/workflow#119 items 1 and 3, #149 items 1, 2 and 5,
#143 item 4). The plan is `docs/ai-workflow/RETENTION_ENGINE_ERROR_PATHS_2_PLAN.md` (revision 3, approved by gate policy).
A `fix:` patch, Workflow 2.29.4, two checkpoints.

## Goal

No path of the retention engine ends in a traceback, or names a directory the walk did not fail on, where the contract is a
named refusal: an item folder that cannot be opened (D-Walk), the lock-time recheck of `remove` (D-Lock), the same-name
collision of the report (D-Collision), an `OSError` no site maps (D-Stray) and the report's best-effort `close`.

## Progress

- CP1 (the walks, the lock recheck, the collision, the backstop, tests and pages): complete. `workflow_retention.py` gains
  `_guard_walk` (three sites), the `folder_changed` refusals of step 1, the `pending` entries with `silent`/`ambiguous`
  flags, the `_stray_io` decorator on `archive_item`, `remove_item` and `prune_archives`, and the report's guarded `close`.
  The new class `RetentionErrorPathsTwo` (17 tests) fails on the unedited script and passes on the change; the one amended
  tuple of `test_t4` is the "link opens, zz fails" layout. `docs/RETENTION.md` and `docs/exit-codes.md` say it.
- CP2 (Release 2.29.4): complete. `manifest.json` 2.29.4 (five records, posture, `conformance.suites`: the obligations suite is 307), `WORKFLOW_RELEASE` 2.29.4 with its two pinned assertions and the protocol document's edits (protocol stays 1.5), the 2.29.4 row of `docs/release-history.md`, the stamps of `docs/release-history.md`, `docs/RETENTION.md` and `docs/exit-codes.md`, and a 2.29.4 class in `tools/release/release_test.py` (the 2.29.3 and 2.25.6 classes give up the pins that moved).

## Next action

All checkpoints are complete. `/milestone-implement retention-engine-error-paths-2` again enters self-review, the full verification and the implementation review bundle.
