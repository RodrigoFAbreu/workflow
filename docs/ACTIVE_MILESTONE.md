# Active Milestone

## Milestone

**In progress (implementation).** W37: `retention-error-paths` (`process`, governing version `2.2`), branch
`milestone/retention-error-paths`, roadmap row 32 (RodrigoFAbreu/workflow#119 item 1 and #113 item 2). Plan:
`docs/ai-workflow/RETENTION_ERROR_PATHS_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.5 (a
`fix:` patch, released after the merge of the pull request): an unreadable symlink in a review folder, and a state
file or tracked path that is not valid UTF-8, are coded refusals (exit 2, a `next step:`) instead of a traceback.
Base commit `69ebb46`; the previous milestone, W36 `check-time-by-value`, is accepted (Workflow 2.25.4).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The helpers, their call sites, tests and documents | **complete** |
| CP2 | Release 2.25.5 | **complete** (see the commit of this checkpoint) |

## Verified state

- CP1: the readlink helper and its four call sites, the two decoding catches, tests T1 to T8, `docs/RETENTION.md` and
  `docs/exit-codes.md`.
- CP2: `manifest.json` 2.25.5 (five changed records, the posture, `conformance.suites` measured: the completion
  obligations suite 274 to 283), `WORKFLOW_RELEASE` 2.25.5 and its pinned assertions, the protocol document's example
  and `1.5` lists, the 2.25.5 history row, the pages' "Last checked with" lines, and a 2.25.5 class in
  `tools/release/release_test.py` (the 2.25.1 and 2.25.4 classes give up the current-release pins).

## Next action

Self-review of the full diff, then the full verification and the implementation-review bundle; stop at the review gate.
