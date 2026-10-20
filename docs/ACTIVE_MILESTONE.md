# Active Milestone

## Milestone

**In progress.** W16: `review-followups-2` (`process`, governing version `2.2`), branch
`milestone/review-followups-2`, roadmap row 19 (RodrigoFAbreu/workflow#60 item 60e, #64 item
64c, #68). Plan: `docs/ai-workflow/REVIEW_FOLLOWUPS_2_PLAN.md` (revision 1, approved by gate
policy). The goal is Workflow 2.18.2, a patch release (`fix:`). The previous milestone, W15
`review-followups-cleanup`, is accepted (its record is in git history and
`docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | Command files: the early collision check and the guard re-wrap | **complete** (60e, 64c) |
| CP2 | Verification commands and the Optional findings | pending |
| CP3 | Release 2.18.2 | pending |

### CP1 verified state

- 60e: `milestone-plan.md` step 1's `[2.1]` bullet carries a "Declared-backlog collision check"
  before the `route_work_item` call: a discarded `generate_artifacts_declarations(...,
  repo_root=<repo_root>)` call whose refusal stops the run with nothing written. The needle test
  (`test_plan_refuses_a_declared_backlog_collision_before_routing`) failed against the unedited
  command file (substring not found) and passes now; the behavioural tests in
  `workflow_state_test.py` (a colliding declaration leaves the tree byte-identical, for both work
  item types; an undeclared repository gets the plain template) pass by design, as the plan says.
  The undeclared steps-1-to-5 digest (`814f7c63...`) did not move.
- 64c: the six user-only command files are re-wrapped to at most 78 columns on every prose line
  that was over 90. `TestUserOnlyCommandLineWidth` failed on the base files (32 lines) and
  passes on the re-wrapped ones. Per file, `' '.join(old.split()) == ' '.join(new.split())`
  against the base holds for all six. The one line left is `approve-review.md`'s unbreakable
  91-column single-span line (OD-3); front matter, code fences, tables and headings are exempt.
- `_GOLDEN_COMMAND_FILE_SHA256` is re-recorded for the seven changed files.

Verified in a disposable clone (D-Staging): the nine payload suites, the `tools/release` and
`tools/docs` tests (see the checkpoint commit's report for the exact results).

## Next action

CP2 (verification commands and the Optional findings), by `/milestone-implement review-followups-2`.
