# Active Milestone

## Milestone

**Planning** (plan revision 1, in plan review). W6: `functional-fix-commit-order`
(`process`, governing version `2.2`), branch
`milestone/functional-fix-commit-order`, base `04d155a` (the release source is
Workflow 2.9.1; this repository's own installation is also 2.9.1 with automatic
gates and no `GATE_POLICY.json`). The plan is
`docs/ai-workflow/FUNCTIONAL_FIX_COMMIT_ORDER_PLAN.md`. The previous milestone,
W4 (`review-stage-write-durability`, Workflow 2.9.1), is complete. W5
(`retire-21-for-new-work`) is paused at its plan review in another worktree and
resumes after this release.

## Goal

Workflow 2.9.2, a patch release that fixes
[RodrigoFAbreu/workflow#19](https://github.com/RodrigoFAbreu/workflow/issues/19)
and [#20](https://github.com/RodrigoFAbreu/workflow/issues/20):

1. **#19.** `/apply-functional-review`'s bounded branch commits the post-fix
   generation record, then updates the checklist in `docs/ACTIVE_MILESTONE.md`
   after it. That commit moves `HEAD` past the bundle's generation head, and the
   next implementation review stops with `bundle_generation_mismatch`. The
   bounded branch now commits the stale technical-approval write before the
   first edit (it was persisted only, and a record commit that sweeps it up is
   refused), then the fix, then the narrative and checklist, and the
   generation record last. Nothing is committed after it.
2. **#20.** Every command that states the trailer rule (`OPUS-R129-001`) says
   plainly that `Co-Authored-By:`/`Claude-Session:` lines go in their own
   paragraph before the `Workflow-*` trailers, because a generation record's
   trailer set is checked exactly. The refusal message names the cause and the
   remedy.

The read side stays strict, the Orchestration Protocol stays 1.2, no state or
commit shape is added, and the Manager lane's order (checklist committed before
the record) keeps working.

## Current checkpoint

None yet: the plan (CP1 to CP5) is in plan review.

## Next action

`/review-plan functional-fix-commit-order`.
