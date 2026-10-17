# Active Milestone

## Milestone

**In plan review.** W9: `review-loop-fixes` (`process`, governing version `2.2`),
branch `milestone/review-loop-fixes`, base `d911915` (main after #36: the
release source and this repository's own installation are both Workflow
2.12.0, with automatic gates, default "2.2" and no `GATE_POLICY.json`).
Requested by the Manager Super Orchestrator; roadmap row 10, placed by the
owner before item C. The plan is `docs/ai-workflow/REVIEW_LOOP_FIXES_PLAN.md`.
The previous milestone, W8 (`review-convergence`, Workflow 2.12.0), is complete.

## Goal

Workflow 2.13.0, a minor release (`feat:`), in five checkpoints:

1. **CP1** the real-process test's ready file is written atomically
   (workflow#32), and the governing-version sweep runs when a plan revision is
   published, bound or turned into a bundle (workflow#30, part 1).
2. **CP2, CP3** `CHANGES_SINCE_REVIEW.md` holds one section per review stage:
   the manual external stage compares against the content it last reviewed and
   quotes its own last verdict, through a gitignored baseline record
   (workflow#35). The local stage is unchanged. Nothing new is persisted in state.
3. **CP4** the producer side of the Manager's release metadata: the `manager`
   block of `manifest.json` (authored fields, computed suite counts) and its CI
   check.
4. **CP5** release 2.13.0 bookkeeping. The Orchestration Protocol stays 1.4.

## Current checkpoint

None yet: the plan (revision 1) is bound and waits for plan review
(`/review-plan review-loop-fixes`).

## Next action

Plan review, then plan approval (automatic), then `/milestone-implement`.
Publishing 2.13.0 follows the pull request merge; the Manager side is a
`chore: test Workflow 2.13.0` lock bump in `workflow-manager`. The Manager
release 1.13.0 must be published before this pull request merges (CP4's CI check).
