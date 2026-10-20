# Active Milestone

## Milestone

**In progress.** W15: `review-followups-cleanup` (`process`, governing version `2.2`), branch
`milestone/review-followups-cleanup`, roadmap row 18 (RodrigoFAbreu/workflow#31, #39, #45,
#52, #56, #60, #64). Plan: `docs/ai-workflow/REVIEW_FOLLOWUPS_CLEANUP_PLAN.md` (revision 5,
approved by gate policy). The goal is Workflow 2.18.1, a patch release (`fix:`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | Review-core defects and messages | **complete** (31b, 39a, 45a, 52b, 52f) |
| CP2 | Backlog script, release tooling, CI and the conformance template | not started |
| CP3 | Test hardening | not started |
| CP4 | Shipped documents and the tests that pin them | not started |
| CP5 | Release 2.18.1 | not started |

### CP1 verified state

Each regression test was run red against the unfixed code first, then green.

- 31b: a wrapped or prefixed "none" (`(none)`, `[none]`, `"None"`, `— None`, `~~none~~`) is a
  placeholder: `_is_placeholder` strips punctuation, symbols and spaces from both ends.
  `REVIEW_PROTOCOL.md` states the leading, trailing and wrapping rule, pinned by a needle.
- 39a: `state_transaction` takes `on_failure`, run inside the lock on any `BaseException`; the
  manual ingest's baseline undo uses it.
- 45a: the undispositioned-finding refusal prints the first line of each finding, cut to 240
  characters; the ledger and the `--finding-dispositions` listing keep the whole stored text.
- 52b: the `state_valid` pass detail names both checks.
- 52f: the recovered-role field-set refusal ends with a next step.

Verified in a disposable clone (D-Staging): the nine payload suites pass from a staged
fixture, the `tools/release` tests (200) and the `tools/docs` tests (34) pass, and
`payload/.claude/commands` is byte-identical to the base.

## Next action

`/milestone-implement review-followups-cleanup` implements CP2.
