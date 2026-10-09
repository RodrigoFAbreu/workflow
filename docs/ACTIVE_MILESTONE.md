# Active Milestone

## Milestone

**Planning** (`PLANNING`, then plan review). W4: `review-stage-write-durability`
(`process`, governing version `2.2`), branch
`milestone/review-stage-write-durability`, base `576dfd5` (the release source is
Workflow 2.9.0; this repository's own installation is also 2.9.0 with automatic
gates and no `GATE_POLICY.json`). The plan is
`docs/ai-workflow/REVIEW_STAGE_WRITE_DURABILITY_PLAN.md` (revision 1). The
previous milestone, W3 (`legacy-retire-and-default-version`, Workflow 2.9.0),
is complete.

## Goal

Workflow 2.9.1, a patch release that fixes
[RodrigoFAbreu/workflow#13](https://github.com/RodrigoFAbreu/workflow/issues/13):

1. **REVISE.** A review stage that returns REVISE persists its phase write and
   never commits it; `/apply-implementation-review`'s post-fix
   generation-record commit then picks it up, shows no `phase` change and is
   refused ("must always transition phase", OPUS-R101-001). The REVISE branches
   of `/review-implementation` and `/record-manual-implementation-review`
   commit their write alone (a `Workflow-Work-Item` trailer), and
   `/apply-implementation-review` commits a still-pending one before its first
   fix commit, doing nothing when an orchestrator already committed it.
2. **APPROVE.** The opposite rule is written down: an APPROVE write is never
   committed on its own, because HEAD past the generation record makes
   `/satisfy-gate` and `/approve-review` refuse (`bundle_generation_mismatch`).
3. **Plan stage.** Checked for the same gap; none (no generation-record
   commit), so its rule (writes stay uncommitted until the plan-approval
   commit) is written down and tested.

The read side stays strict, the Orchestration Protocol stays 1.2, and 2.9.1
accepts no commit shape 2.9.0 refuses.

## Current checkpoint

**Implementing** (`IMPLEMENTING`). CP1 to CP5 are complete. CP1:
`payload/scripts/workflow_state.py` gains
`commit_pending_applying_review_feedback_entry`,
`REVIEW_STAGE_WRITE_COMMIT_FIELDS` and `ReviewStageWriteNotCommittableError`
(the scoped-state construction is extracted from `stage_scoped_state` into
`_scoped_state_from`, behavior unchanged), with 15 unit tests. CP2: the REVISE
branches of `review-implementation.md` (A6) and
`record-manual-implementation-review.md` (step 7) commit through the helper and
their APPROVE branches say to leave the write uncommitted;
`apply-implementation-review.md` step 1 calls the helper after the binding check
and before the `BLOCK` pin; `review-plan.md`, `record-manual-plan-review.md` and
`apply-plan-review.md` carry the plan-stage sentence. Golden hashes updated and
`TestReviewStageWriteCommitRuleConformance` added in
`workflow_integration_test.py`. Verified: the nine payload suites green in a
scratch conformance fixture (the two `*_demo_test.py` files need this
repository's history and are not among them), whole-file diff against `v2.9.0`
shows only the listed hunks, `workflow-manager verify .` clean. CP3:
`workflow_acceptance_matrix_test.py` gains `ReviewStageWriteDurabilityProcess`
and `...Product` (18 scenarios each, plan CP3 scenarios 1 to 15 plus the
helper-removed negatives `s06b` and `s10b`, which show 2.9.0's texts are refused
by the generator with OPUS-R101-001) and `Item.generate_impl_bundle` gains an
opt-in `scoped_staging` that stages through `stage_scoped_state`. Verified: the
36 new tests green and the nine payload suites green in a scratch conformance
fixture built from the checkpoint's tree (327 acceptance-matrix tests, 18
skipped as before).
CP4: `REVIEW_PROTOCOL.md` gains "Which review-stage writes are committed"
(the commit-rule table, the helper and its refusals); `IMPLEMENTATION_REVIEW_WORKFLOW.md`,
`PLAN_REVIEW_WORKFLOW.md` and the operator reference carry one paragraph each
pointing at it; `docs/common-problems.md` gains three entries (REVISE refused
with "must always transition phase", the APPROVE counterpart, and the helper's
`ReviewStageWriteNotCommittableError`). Verified: `tools/docs/check_docs.py`
clean; the integration, protocol, fingerprint and gate-policy suites green in a
scratch conformance fixture (the operator-reference symbol check caught a
backticked `bundle_generation_mismatch` in the first draft, reworded).
CP5: `WORKFLOW_RELEASE` is `2.9.1` (`PROTOCOL_VERSION` stays `1.2`; `ORCHESTRATION_PROTOCOL.md` names 2.9.1 among
the tested releases and `workflow_protocol_test.py` pins `2.9.1`, both beyond
the plan's file list, required by the protocol suite);
`manifest.json` names `2.9.1` with the refreshed `sha256`/`size` of the 17
changed records (counts unchanged, `tools/release/manager-pin.json` untouched);
`docs/release-history.md` gains the 2.9.1 row. `docs/ROADMAP.md` marks W4 Done
at acceptance. Verification: see the CP5 commit and the implementation bundle's
`TEST_RESULTS.md`.

## Open decisions

OD-1 to OD-5 of the plan, each with a recommendation: fix shape (recommended:
the review step commits its REVISE write, `/apply-*` commits a pending one,
through one idempotent helper; the generation check is not loosened), helper
versus prose, the APPROVE trap, the plan stage, and the version.
