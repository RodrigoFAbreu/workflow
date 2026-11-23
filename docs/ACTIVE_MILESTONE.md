# Active Milestone

## Milestone

**Complete** (accepted by policy; a `docs:` change, no Workflow release). W62: `workflow-docs-wording` (`process`, governing version `2.2`), branch
`milestone/workflow-docs-wording`. It has no `docs/ROADMAP.md` row, and the roadmap is untouched. Issues RodrigoFAbreu/workflow#173
point 1 and #161 point 1. The plan is `docs/ai-workflow/WORKFLOW_DOCS_WORDING_PLAN.md` (revision 1).

## Goal

Two documentation sentences say what the engine already does. No product behaviour, payload file, manifest field, command, message,
roadmap row or release changes.

- `docs/common-problems.md`, "An approval became stale after a change": the plan route now says that a plan amendment is possible only
  at `IMPLEMENTING` or `SELF_REVIEWING_IMPLEMENTATION`.
- `docs/release-history.md`, the 2.28.0 row: `--write-findings-record` exits 0 with the paths to stage (the record, and the dispositions
  file when it exists; `[]` for an item with no finding). The row said "the record path (or nothing, for an item with no finding)".

The release tests gain assertions inside two existing methods. No test method is added or removed.

## Outcome

- CP1 (`1fcad47`) and CP2 (`0bc3d5a`) are complete. The plan was approved by gate policy at revision 1.
- Implementation review round 1 is APPROVE from both the local and the external reviewer. The technical approval was recorded by
  policy (`3c67a85`).
- Verification at `0bc3d5a`, recorded in `.ai-review/workflow-docs-wording/current/TEST_RESULTS.md`: the nine payload suites, `tools/release`
  (386 tests), `tools/docs` (34 tests), `check_docs.py`, `check-manager-block`, `workflow-manager verify .`, `check-title` (`impact=none`),
  the reaper on the two pin classes, and a failure-only mutation of each page. All pass. The commits after it (`61565b7`, `3c67a85`) change
  only `docs/ai-workflow/WORKFLOW_STATE.json`, so the verified tree is unchanged.
- Not taken: #173 points 2 and 3, and #161 points 2 and 3 (fixed on main, or a finished item's plan prose). See the plan, section 0 and
  section 5.
- The functional flows 1 to 12 are recorded passed. The recorded Optional findings are dispositioned; see
  `docs/milestones/completed/workflow-docs-wording-findings.md`. An archive copy of the plan is in `docs/milestones/completed/`.
- Nothing is pushed, merged or published. There is no Workflow release and no Manager pin.

## Next action

No item is ready for `PLANNING` from this milestone: it has no roadmap row. The next incomplete milestone in `docs/ROADMAP.md` is row 27
("Deferred: review-data simplification, longer-term evolution"), which is deferred and trigger-driven (see "Later (open items)").
`/milestone-plan` when one is chosen.
