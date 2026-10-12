# Active Milestone

## Milestone

W7: `checkpoint-anchors-early` (`process`, governing version `2.2`), branch
`milestone/checkpoint-anchors-early`, base `a5da36c` (main after W5: the
release source is Workflow 2.10.0; this repository's own installation is 2.9.2
with automatic gates and no `GATE_POLICY.json`). Issue
RodrigoFAbreu/workflow#23, high priority. The plan is
`docs/ai-workflow/CHECKPOINT_ANCHORS_EARLY_PLAN.md`. The previous milestone,
W5 (`retire-21-for-new-work`, Workflow 2.10.0), is complete.

## Goal

Workflow 2.11.0, a minor release (`feat:`), roadmap row 8:

1. **Check anchors early.** The plan-approval check that every registry
   checkpoint has a well-formed `<!-- CPn -->`/`<!-- /CPn -->` pair in the
   plan (`validate_post_anchor_coverage`) also runs, through one wrapper
   (`assert_plan_checkpoint_anchors`), when a plan revision is published, when
   it is bound, and in plan-stage bundle generation on the pinned bytes. An
   amending plan without anchors is refused before any review round, with the
   same error classes as approval and one next step. The approval-time check
   is unchanged.
2. **Write anchors from the start.** `/milestone-plan` tells the author to put
   a pair around every checkpoint section in every revision, and the same
   check requires them for every new plan revision of a "2.1" or "2.2" item,
   so a later amendment reconciles checkpoint by checkpoint instead of
   re-checking every completed one.

Approved plans without anchors keep driving implementation, reviews and
acceptance until their next plan revision; version-"1" items are unchanged;
nothing new is persisted; Orchestration Protocol stays 1.3.

## Current checkpoint

Implementing, plan revision 4 approved. CP1 complete: `PLAN_ANCHOR_NEXT_STEP`,
`_assert_post_registry_well_formed` (moved verbatim out of
`apply_plan_approval`) and `assert_plan_checkpoint_anchors` in
`payload/scripts/workflow_state.py`, with `TestAssertPlanCheckpointAnchors`
in `workflow_state_test.py`. The nine suites pass in a scratch conformance
fixture and `workflow-manager verify .` is clean. CP2 complete: the plan-stage
branch of `payload/scripts/prepare-ai-review.sh` calls
`assert_plan_checkpoint_anchors` on the staging pin (`allow_bound_regeneration`)
and exits 1 through `cleanup` on an anchor error; the harness's default plan
carries an anchor pair per checkpoint, `workflow_protocol_test.py`'s lifecycle
ids are `CP1`/`CP2`, and the matrix's pre-repair test now asserts the refusal.
New tests: `TestPrepareAiReviewShEarlyAnchorCheck` and two harness pins. Next is
CP3 (command texts).
