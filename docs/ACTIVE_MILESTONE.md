# Active Milestone

## Milestone

**In progress** (implementing). W27: `retention-report` (`process`, governing version `2.2`), branch
`milestone/retention-report`, roadmap row 27b (RodrigoFAbreu/workflow#84, step 2). Plan:
`docs/ai-workflow/RETENTION_REPORT_PLAN.md` (revision 2, approved by gate policy). The goal is Workflow 2.20.0, a
`feat:` minor that adds one read-only script, `scripts/workflow_retention.py report`, listing the finished work items
by the rule of `docs/RETENTION.md`, the size of their untracked review folders and the archives older than the time
to live. The archive command (row 27c) and the prune (row 27d) are not part of this item. The previous milestone,
W25 `command-wording`, is accepted (Workflow 2.19.2).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The report script, its tests and the documents | **complete** (verified in a scratch clone, see below) |
| CP2 | Release 2.20.0 | not started |

## Verified state

- CP1: `payload/scripts/workflow_retention.py` (`# state_writer: false`, stdlib plus `workflow_forge`;
  `build_report` and `main`), the `RetentionReport` tests in `workflow_state_completion_obligations_test.py`
  (193 -> 208), `docs/RETENTION.md` (the section "The report" and the re-targeted row references) and
  `docs/exit-codes.md`. Each mutation the plan lists (open items queried, the stored fact trusted, an exception
  aborting the run, `>=` for `>`, a symlink followed, a write to the archive directory, a write only in the
  query-failure handler, a write only on a refusal path, the bytecode assignment moved after the sibling import,
  `archives` in directory order) fails at least one test in a scratch copy.
- Verified in a disposable clone (D-Staging, the adjusted staging reported): `tools/release` (277, with the one
  declared scratch patch of the two pinned counts), `tools/docs` (34), `check_docs.py`, `check-manager-block`, and the
  nine suites from the staged fixture (see the implementation bundle's `TEST_RESULTS.md`).

## Next action

CP2: `/milestone-implement retention-report` again, for the release bookkeeping of Workflow 2.20.0.
