# Active Milestone

## Milestone

**In progress.** W34: `retention-polish` (`process`, governing version `2.2`), branch `milestone/retention-polish`,
roadmap row 29 (RodrigoFAbreu/workflow#123 items 2 and 4, #132 items 1 and 2). Plan:
`docs/ai-workflow/RETENTION_POLISH_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.25.2 (a `fix:`
patch): wording and test pins of finished retention work, no behaviour change. Base commit `586c86c`.

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The four in-scope items: wording, three assertions | **complete** |
| CP2 | Release 2.25.2 | **complete** |

## Verified state

- CP1: the operator reference's Writes line for `/archive-finished-item`, the `RetentionRemove.stat_refused` prefix
  assertion and the new preview-pairs test. Verified from a scratch-staged fixture (D-Staging): the nine suites pass
  (integration 377); mutations m1 to m7 each fail as the plan says; `workflow_retention.py` and `payload/.claude` are
  byte-identical to the base.

- CP2: Workflow 2.25.2 (manifest, the six records, the posture, `conformance.suites` integration 377; the release
  constant, its assertions and the protocol document; the 2.25.2 and corrected 2.25.1 history rows; the
  `RetentionPolishReleaseTest` class and the nine docstring pointers). Verified from a squashed scratch clone of the
  candidate: the nine suites from `stage-conformance`, `build`, `check-manager-block`, the `tools/release` tests (299)
  and `tools/docs`; m8 fails `RetentionPolishReleaseTest` and the baseline passes.

## Next action

Run `/milestone-implement retention-polish` again: all checkpoints are complete, so it runs the full-milestone review
and prepares the implementation review bundle.
