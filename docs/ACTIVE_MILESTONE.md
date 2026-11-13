# Active Milestone

## Milestone

**In progress.** W50: `two-page-wording` (`process`, governing version `2.2`), branch `milestone/two-page-wording`, roadmap row 43
(RodrigoFAbreu/workflow#178, points 1 and 2). The plan is `docs/ai-workflow/TWO_PAGE_WORDING_PLAN.md` (revision 1, approved by
gate policy).

## Goal

Two statements in two shipped pages read true and say each thing once: the retention row's lock-order cell in
`docs/CONCURRENCY_INVARIANTS.md` and the acceptance row of `docs/gates.md`. Docs only: no `payload/`, `tools/` or behaviour
change, so no release (a `docs:` pull request, impact none; the manifest keeps 2.29.3). No `Last checked with` stamp moves.

## Progress

- CP1 (reword the two cells, add roadmap row 43): implemented; verification and the implementation review follow.
- Self-review: the retention cell lacked the closing period of the plan's D-Retention sentence, so flow 10's mutation
  printed `0 1` where it expects `1 1`; the period is restored.

## Next action

Finish the self-review, run the verification of the plan's section 5, and prepare the implementation review bundle.
