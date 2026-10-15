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

Planning, plan revision 3: five checkpoints (CP1 verdict shape, CP2 the
changes file, CP3 protocol 1.4 and the distinct-provider courier
clarification for workflow#28, CP4 plan size and small fixes, CP5 release).

## Next action

`/review-plan review-convergence` (the local plan review).
