# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W15: `review-followups-cleanup` (`process`, governing version `2.2`), branch
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
| CP5 | Release 2.18.1 | **complete** (manifest 2.18.1, rationales incl. 64a, posture, release history, release tests) |

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

### CP5 verified state

`manifest.json` names 2.18.1: `sha256` and `size` of the 16 changed artifact records and the
template, a `workflow-2.18.1` sentence on each changed record, the 64a per-file 2.18.0 sentences,
the template `derivation`, the downgrade posture (per-area; the `- (none)` APPROVE is not portable
back to 2.18.0), and `manager.conformance.suites` measured by `release.py manager-block --write`
(453/344/1197/316/142/193/346/283/27). `WORKFLOW_RELEASE` is 2.18.1 with its two assertions and the
`ORCHESTRATION_PROTOCOL.md` edits; `docs/release-history.md` has the 2.18.1 row; `docs/RELEASING.md`
states 453 tests (two places); `release_test.py` has a 2.18.1 class and the 2.18.0 class no longer
pins the current version, constant or posture. No command file changed.

Verified in a clone of the committed tree: `stage-conformance` fixture, all nine suites pass,
`tools/release` (211 tests, zlib-ng python), `tools/docs` (34 tests) and `check_docs.py`, `release.py
build`, `check-manager-block`. Not run: the `update-fixture` (needs the published 2.18.0 assets).
`workflow-manager verify .` reports the installation matches 2.18.0.

## Functional review checklist

This is a `process` milestone (Workflow 2.18.1, a patch release): there is no UI. Testing is
running the commands below from the repository root on branch `milestone/review-followups-cleanup`.

**Setup.** Clean working tree on the branch; `python3` available. Nothing to seed. Do not run the
`update-fixture` (needs the published 2.18.0 assets; not run in CP5).

| # | Flow | Expected |
| --- | --- | --- |
| 1 | `python3 payload/scripts/workflow_state_test.py` and the other payload suites (`payload/scripts/*_test.py`) | All pass; counts match `manifest.json` `manager.conformance.suites` (453/344/1197/316/142/193/346/283/27) |
| 2 | `python3 -m unittest discover tools/release` and `tools/docs` | 211 and 34 tests pass |
| 3 | `python3 tools/release/release.py check-manager-block` and `python3 tools/docs/check_docs.py` | Both clean |
| 4 | `workflow-manager verify .` | Clean; installation still matches 2.18.0 (this repo is not updated by hand) |
| 5 | `git diff e1be478..HEAD --stat -- payload/.claude/commands` | Empty: no command file changed |
| 6 | Review-core spot checks (31b): in a scratch review feedback, a finding disposition of `(none)`, `[none]`, `"None"`, `~~none~~` is treated as a placeholder | Accepted as "none"; see `REVIEW_PROTOCOL.md` leading/trailing/wrapping rule |
| 7 | 45a: an undispositioned finding refusal prints only each finding's first line, cut at 240 chars | Ledger and `--finding-dispositions` keep the full text |
| 8 | 60a-60c backlog script: a 2,000-line chained malformed backlog file under `status` | Reported, no `RecursionError`; `?` in a plain flow-list entry refused, quoted `"a?b"` accepted |
| 9 | `manifest.json` / `docs/release-history.md` | Version 2.18.1, a 2.18.1 row, downgrade posture notes the `- (none)` APPROVE is not portable back to 2.18.0 |

**Known limitations / out of scope.** `update-fixture` not run; this repository's own installation
stays on 2.18.0 until 2.18.1 is published and installed; 56b has no needle (page not shipped);
52e compares `review_content_id`, not `bundle_id`, by design.

## Next action

Row 19 is deferred and unscheduled. Publishing 2.18.1 follows the pull request merge (#69); the Manager side is a `workflow-manager` pin pull request. The 4 follow-ups are in RodrigoFAbreu/workflow#68.
