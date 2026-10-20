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
| CP3 | Test hardening | **complete** (39b, 45b, 52a, 52c, 52e) |
| CP4 | Shipped documents and the tests that pin them | **complete** (31c, 31d, 39c-39f, 56b, 60f, 60g, 64b, 64f, 64h) |
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

### CP3 verified state

Test-only (`payload/scripts/workflow_state_test.py`); no production line changed. Each new or
tightened test was shown to fail under a deliberate break applied to a scratch copy only.

- 39b: a real manual `REVISE` ingest, a plan edit and the real generator; the manual section of
  `CHANGES_SINCE_REVIEW.md` names `previous_review_content_id` and shows the edit. Fails when the
  ingest stops recording the baseline.
- 45b: the two-item residue test asserts the exact changed lines of the diff (the other item's
  ledger hunk). A spurious extra hunk that does not name the committed item now fails it.
- 52a: 2.14.0's four commit-field sets are literals; a test asserts the current sets equal them
  plus exactly `review_round_counts`, and the downgrade helper uses the literals.
- 52c: a duplicate ingest (same call on the post-state) and a stale feedback content id, for both
  manual writers, raise and leave the state and counter unchanged. Fails when the stale check goes.
- 52e: the grep of `workflow_fingerprint.py` is replaced by a comparison, in one repository, of the plan-stage
  and implementation-stage `review_content_id` before and after the counter changes. Deviation
  from the plan text: `bundle_id` is not compared, because the bundle ships a copy of the state
  file, so it covers the counter by design (the approval binds `review_content_id`).

Verified in a disposable clone (D-Staging): the nine payload suites pass from a staged fixture,
`tools/release` (207 tests) and `tools/docs` (34 tests) pass, and `payload/.claude/commands` is
byte-identical to the base.

### CP4 verified state

Wording in six shipped documents and `docs/common-problems.md`, one comment in
`workflow_fingerprint.py` (39c), and needles pinning each edit (`workflow_protocol_test.py`,
`workflow_integration_test.py`, `workflow_state_completion_obligations_test.py`). 64h states 22 in
all four places of the operator reference; `test_the_command_inventory_claim_states_the_real_guarantee`
was updated to the new quote and now also refuses the stale 16 forms. 56b has no needle (page not shipped).

Verified in a disposable clone (D-Staging, scratch manifest re-stamped with measured suite counts):
the nine payload suites pass from a staged fixture (one first-run error in a misplaced new test
was fixed and the class re-run green), `tools/release` (207 tests) and `tools/docs` (34 tests)
pass, and `payload/.claude/commands` is unchanged.

## Next action

`/milestone-implement review-followups-cleanup` implements CP5.
