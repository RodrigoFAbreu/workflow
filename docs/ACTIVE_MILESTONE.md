# Active Milestone

## Milestone

**Planning.** W8: `review-convergence` (`process`, governing version `2.2`),
branch `milestone/review-convergence`, base `f30e352` (main after the CI
change #27: the release source is Workflow 2.11.0; this repository's own
installation is also 2.11.0 with automatic gates, default "2.2" and no
`GATE_POLICY.json`). Requested by the Controller lane; the owner approved the
slot on 2026-10-14. The plan is `docs/ai-workflow/REVIEW_CONVERGENCE_PLAN.md`.
The previous milestone, W7 (`checkpoint-anchors-early`, Workflow 2.11.0), is
complete.

## Goal

Workflow 2.12.0, a minor release (`feat:`), roadmap row 9. Review loops are
about two thirds of the Controller's worker cost; this release makes them
cheaper and shorter without changing what an approval binds:

1. **Incremental re-review.** From round 2 a bundle carries
   `CHANGES_SINCE_REVIEW.md`: the diff of the protected content since the
   last reviewed bundle and that round's findings, at both stages, for the
   local and the manual reviewer. A round may review only the changes to
   return `REVISE`; every `APPROVE` is a full review of the whole bundle.
2. **Severity rule.** A `REVISE` must name a Blocking or Important finding,
   and an `APPROVE` may not declare a changes-only review; otherwise the
   verdict is refused as malformed and reissued, never converted. A round
   with only optional findings is an `APPROVE` with the findings recorded.
3. **Round field.** Orchestration Protocol 1.4 adds `review_round` to the
   `next-action` snapshot (the plan and implementation round, and which
   review stage is waiting), so an orchestrator can stop at its own cap.
   Accepting at a cap stays a person's step; the plan's OD-1 names the gap
   for two-stage items.
4. **Small plans.** `/milestone-plan` asks for few checkpoints and warns,
   without blocking, above six.

Nothing new is persisted in state; approvals, gates and who may approve are
unchanged.

## Current checkpoint

Implementing, plan revision 9. CP1 (verdict shape) is complete:
`assert_verdict_well_formed`, `parse_review_scope` and
`MalformedVerdictError` in `workflow_fingerprint.py`, called by
`ingest_manual_review_verdict` at a two-stage row and by the two local review
commands before they write; the two manual commands report a refusal and ask
for a reissue; `REVIEW_PROTOCOL.md` states the severity meanings and the
rule. `workflow_protocol.py` needed no change: a `MalformedVerdictError` maps
to `refused` by default. Verified in a scratch release fixture: the nine
conformance suites pass. CP2 (the changes file) is complete:
`workflow_fingerprint.write_changes_since_review` builds
`CHANGES_SINCE_REVIEW.md` (preamble, previous findings, pinned-option diff) at
the plan stage (outgoing `.pin` against the staging pin, carried forward on a
wrapper-only regeneration, promoted or removed with `AMENDMENT_DIFF.patch`) and
at the implementation stages (previous round's reviewed head against the
working tree, from the outgoing manifest copy `prepare-ai-review.sh` keeps; a
same-content republication leaves it alone); the archive carries it; the
review and request commands and the three protocol documents state the review
rule. `load_implementation_stage_classification` gained `at_commit`. Thirteen
tests in `workflow_fingerprint_generalization_test.py` (`TestChangesSinceReview`).
CP3 (protocol 1.4) is complete: `workflow_protocol._review_round` adds the
snapshot's `review_round` (`plan` an exact count from the consumed-content
history and the binding record, or `null` for every shape not shown complete;
`implementation`; `current`), `PROTOCOL_VERSION` is `1.4`, the schema gained the
property, and `ORCHESTRATION_PROTOCOL.md` states the field, the exactness
boundary, the round cap (8.1), the verdict courier (8.2) and a 1.4 note. Nine
tests in `workflow_protocol_test.py` (`TestReviewRoundField`), including the
generator-driven drive; `without_release()` strips the field. The suite's 16
failures (a stale `workflow_release` of 2.9.0 in the update-simulation tests)
are the same at the CP2 commit. CP4 (plan-size guidance) is complete:
`workflow_state.PLAN_CHECKPOINT_SOFT_LIMIT` (6) and `plan_size_advisory`, printed
at the publication point of `/milestone-plan` and `/apply-plan-review` (a
`[2.1]` step 3 sentence keeps the `"1"` output unchanged); the
`validate_local_plan_review_preconditions` refusal names `/milestone-plan <id>`
or `/apply-plan-review <id>` at a non-ready phase; `docs/RELEASING.md`'s
`stage-conformance` example uses `--out "$(mktemp -d)/fixture"`; the over-long
line in `milestone-plan.md` step 6 is rewrapped. Two tests in
`workflow_state_test.py`; golden hashes refreshed. Verified in a scratch release
fixture: the nine conformance suites pass. CP5 (release 2.12.0) is complete:
`manifest.json` 2.12.0 with refreshed digests, `WORKFLOW_RELEASE`, the
tested-releases list, the release-history row with the downgrade posture and
the courier clarification (closes workflow#28), and the common-problems, gates
and glossary entries.

Every checkpoint is complete; the phase is `SELF_REVIEWING_IMPLEMENTATION`.
The self-review of the whole milestone diff fixed three documentation
defects: `REVIEW_PROTOCOL.md` and the glossary said `Review scope: changes` is
valid on a `REVISE` only, where the check, the commands and the other documents
accept it on a `REVISE` or a `BLOCK`; and the protocol's 1.4 compatibility note
now says that a consumer validating against its own copy of the 1.3 schema
(whose `snapshot` has `additionalProperties: false`) rejects the new field, as
the plan's risk section requires. Manifest digests refreshed for the two
payload documents.

## Next action

The implementation review: the bundle is generated at
`AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, then `/review-implementation
review-convergence`.
