# Active Milestone

## Milestone

**Implementing.** W11: `review-round-counts` (`process`, governing version `2.2`),
branch `milestone/review-round-counts`, base `16c2599` (main after #49: the release
source is Workflow 2.14.0 and this repository's own installation is the published
2.14.0). Roadmap row 14. The plan is `docs/ai-workflow/REVIEW_ROUND_COUNTS_PLAN.md`,
approved by gate policy at plan revision 3. The previous milestone, W10
(`finding-dispositions`, Workflow 2.14.0), is complete.

## Goal

Workflow 2.15.0, a minor release (`feat:`), in four checkpoints: `next-action`
reports how many **local** and how many **external** review rounds an item has had
at each stage (`plan_local`, `plan_external`, `implementation_local`,
`implementation_external`), from one persisted counter `review_round_counts`
written in the verdict's own state transaction. Orchestration Protocol becomes 1.5,
additive.

1. **CP1** the counter in the state and the four review writers.
2. **CP2** the four snapshot fields, schema and protocol constant 1.5.
3. **CP3** the Protocol 1.5 specification and the user documents.
4. **CP4** release 2.15.0 bookkeeping and the downgrade posture.

## Current checkpoint

CP1 is complete: `workflow_state.initial_review_round_counts` (written by
`default_work_item`: `plan` is a zero pair for a two-stage plan-review version,
`implementation` for `2.2`, else `null`), `review_round_counts_errors`,
`validate_review_round_counts` and `InvalidReviewRoundCountsError` (none of them
called from `validate_state`, so a malformed counter never refuses an operational
path), and the private `_count_review_round`, called by the four review writers for
`APPROVE` and `REVISE` only. An absent key, a `null` stage or a malformed value is
left exactly as it was. `review_round_counts` joins the four closed commit-field sets
that name `optional_findings`; the audit of the file's other closed sets
(`LEGACY_RETIREMENT_FIELDS`, `RESUME_IMPLEMENTATION_FIELDS`,
`_ACCEPTANCE_SATISFACTION_FIELDS`) is unchanged. Tests: `TestReviewRoundCounts` and
`TestReviewRoundCountsDowngrade` in `workflow_state_test.py`, including the
downgrade regression (2.15.0's helpers accept a committed counter-bearing recovered
generation record; helpers with 2.14.0's field sets refuse it).
