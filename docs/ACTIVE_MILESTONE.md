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
| CP2 | Backlog script, release tooling, CI and the conformance template | **complete** (60a-60d, 60f tests, 39g-39i, 56a, 56d) |
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

### CP2 verified state

Each new behavioural test was run red against the unfixed code first, then green.

- 60a: `_find_cycle` is iterative (same cycle, same order); a 2,000-line chained malformed file
  is reported by `status` with no `RecursionError`.
- 60b: `_snapshot` returns bytes and mode, `_restore` restores both (also when only the mode
  differs), `_write_atomic` takes the snapshot mode; the backlog file is snapshotted the same way.
- 60c: `?` is refused in a plain flow-list entry (a quoted `"a?b"` is still accepted).
- 60d: `protected_conflicts` reports an exact protected path or a protected prefix under
  `docs/items/`; the docstring is reworded.
- 60f (tests): `items: # x` and `depends_on: # x` are pinned as accepted.
- 39g, 39h: a non-string detector `kind` is a problem, not a `TypeError`; tags and versions
  use `fullmatch`.
- 39i: the CI update-fixture selector reads `isPrerelease` and skips prereleases; the existing
  selector test now supplies the field.
- 56a, 56d: in the template and the CI copy, identically, the checkout copy's output joins the
  unit's log and a bad coverage total with exit 0 is worded as the total. Beyond the plan's
  text, the suite's own redirect appends (`>>`) so the copy's error is not truncated away.

Verified in a disposable clone (D-Staging): the nine payload suites pass from a staged
fixture, `tools/release` (207 tests) and `tools/docs` pass, and `workflow-manager verify .`
is clean. The one `tools/release` failure on the first run (the selector test lacking
`isPrerelease`) was fixed and its class re-run green.

## Next action

`/milestone-implement review-followups-cleanup` implements CP3.
