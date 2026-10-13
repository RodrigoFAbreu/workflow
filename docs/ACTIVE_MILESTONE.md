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
New tests: `TestPrepareAiReviewShEarlyAnchorCheck` and two harness pins. CP3
complete: `milestone-plan.md` (step 3's anchor instruction, step 4's `[2.1]`
self-review bullet, the publication point's new item 4 before the publish,
step 6's check before the bind and the generator-refusal sentence),
`apply-plan-review.md` (step 5 check before the publish, step 7' before the
bind) and `request-plan-amendment.md` (the anchor paragraph) name
`assert_plan_checkpoint_anchors` and `PLAN_ANCHOR_NEXT_STEP`; the two golden
hashes are updated and `TestCheckpointAnchorsEarlyCommandConformance` pins the
ordering. The `"1"` golden output of `/milestone-plan` is unchanged. CP4
complete: `CheckpointAnchorsEarlyProcess`/`Product` in
`workflow_acceptance_matrix_test.py` (seven scenarios, plus the 2.10.0
stand-in helper and its pins); the matrix suite passes (415 tests, 20
skipped). CP5 complete: the rule, the early refusal and its one next step are
written in `MILESTONE_WORKFLOW.md` (`PLANNING`, `AMENDING_PLAN`),
`PLAN_REVIEW_WORKFLOW.md`, `REVIEW_PROTOCOL.md` and the operator reference, and
`docs/common-problems.md` has "A plan revision is refused for a missing
checkpoint anchor" with the downgrade posture. Run in place, the payload
suites show the same failures with and without the CP5 edits (they read the
installed 2.9.2 command files); the scratch conformance fixture was not
staged. CP6 complete: `manifest.json` is 2.11.0 with every `artifacts` and
`templates` digest and size refreshed, `WORKFLOW_RELEASE = "2.11.0"` (protocol
stays 1.3) with the two release strings in `workflow_protocol_test.py`, the
tested-releases list in `ORCHESTRATION_PROTOCOL.md`, a 2.11.0 row in
`docs/release-history.md` carrying the downgrade paragraph, and the "Last
checked with" lines of the two docs this milestone changed. The nine suites pass
in the stock `release.py stage-conformance` fixture, `release.py build` of the
commit succeeds and `check_docs.py` is clean. All checkpoints are complete.

## Functional review checklist

Milestone `checkpoint-anchors-early` (Workflow 2.11.0), implementation
revision 1. This is a process milestone with no UI: the "user flows" are
command-line and command-text checks on the release source. All commands run
from the repository root on branch `milestone/checkpoint-anchors-early`.

### Setup

- Python 3 and `git` only; no feature flags, no seeded data.
- Do not edit this repository's own installation (`.claude/`, `scripts/`,
  `docs/ai-workflow/`); the changes under test live in `payload/`,
  `manifest.json` and `docs/`.
- Scratch fixture for the suites (never run them from inside an extracted
  tree): `python tools/release/release.py stage-conformance --commit HEAD --out "$(mktemp -d)"`.

### Test data

None to seed. The suites build their own temporary repositories; the plan
under test is `docs/ai-workflow/CHECKPOINT_ANCHORS_EARLY_PLAN.md`.

### Flows and expected results

1. **Release source is consistent.**
   Run `python tools/release/release.py stage-conformance --commit HEAD --out "$(mktemp -d)"`,
   then the nine suites inside the staged fixture (per `docs/RELEASING.md`).
   Expected: all nine pass; `manifest.json` says 2.11.0 and its digests match.
2. **Installation untouched.** Run `workflow-manager verify .`.
   Expected: clean.
3. **Docs check.** Run `python tools/docs/check_docs.py`. Expected: clean.
4. **Early check, direct.** In a Python session with `payload/scripts` on the
   path, call `workflow_state.assert_plan_checkpoint_anchors` with a plan whose
   registry has `CP1`/`CP2` but only a `CP1` anchor pair.
   Expected: the same error class as plan approval, message ending with
   `PLAN_ANCHOR_NEXT_STEP` (one next step). With both pairs present: no error.
5. **Bundle generation refuses early.** Targeted tests:
   `python -m unittest workflow_fingerprint_generalization_test.TestPrepareAiReviewShEarlyAnchorCheck`
   and `workflow_state_test.TestAssertPlanCheckpointAnchors` (run in the
   staged fixture). Expected: pass; an anchorless plan makes the plan-stage
   branch of `prepare-ai-review.sh` exit 1 before any review round.
6. **End-to-end scenarios.** `workflow_acceptance_matrix_test`
   `CheckpointAnchorsEarlyProcess`/`CheckpointAnchorsEarlyProduct`. Expected:
   all seven scenarios pass, including: approved anchorless plan still drives
   implementation/acceptance; new "2.1"/"2.2" revision without anchors is
   refused at publish, bind and bundle generation; version-"1" unchanged.
7. **Command texts.** Read `payload/.claude/commands/milestone-plan.md`
   (step 3, step 4, publication point item 4, step 6),
   `apply-plan-review.md` (steps 5 and 7') and `request-plan-amendment.md`.
   Expected: each tells the author to wrap every checkpoint section in
   `<!-- CPn -->`/`<!-- /CPn -->` and names `assert_plan_checkpoint_anchors`
   before the publish/bind, with no wording contradicting the plan.
8. **Docs read right.** Skim `MILESTONE_WORKFLOW.md` (`PLANNING`,
   `AMENDING_PLAN`), `PLAN_REVIEW_WORKFLOW.md`, `REVIEW_PROTOCOL.md`, the
   operator reference, `docs/common-problems.md` ("A plan revision is refused
   for a missing checkpoint anchor") and the 2.11.0 row of
   `docs/release-history.md`. Expected: rule, refusal, one next step and the
   downgrade posture are described consistently; commands named exist.
9. **Release build.** `python tools/release/release.py build` of the commit
   succeeds (see `docs/RELEASING.md`). Expected: builds 2.11.0 artifacts, no
   changes to any published tag or asset.

### Known limitations / out of scope

- Approved plans without anchors keep working until their next plan revision.
- Run in place, some payload suites read the installed 2.9.2 command files and
  show failures unrelated to this milestone; use the staged fixture.
- Nothing new is persisted; Orchestration Protocol stays 1.3.
- Publishing the release and the `workflow-manager` pin are separate steps,
  not part of this milestone's functional review.
