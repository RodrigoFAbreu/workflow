# Active Milestone

## Milestone

**Complete** (accepted by policy; a `docs:` change, no release). W50: `two-page-wording` (`process`, governing version `2.2`),
branch `milestone/two-page-wording`, roadmap row 43 (RodrigoFAbreu/workflow#178, points 1 and 2). The plan is
`docs/ai-workflow/TWO_PAGE_WORDING_PLAN.md` (revision 1, approved by gate policy); an archive copy is in
`docs/milestones/completed/`.

## Goal

Two statements in two shipped pages read true and say each thing once: the retention row's lock-order cell in
`docs/CONCURRENCY_INVARIANTS.md` and the acceptance row of `docs/gates.md`. Docs only: no `payload/`, `tools/` or behaviour
change, so no release (a `docs:` pull request, impact none; the manifest keeps 2.29.3). No `Last checked with` stamp moves.

## Outcome

- CP1 is complete: the retention cell now says once that the engine takes no state lock and no checkpoint claim and imports
  nothing from `workflow_state.py`; the acceptance row of the gates page says its latest-run rule once. Roadmap row 43 added.
- The technical approval was recorded by policy. Functional flows 1 to 7 are recorded passed by the Controller's automated
  tester (the remaining flows are automated verification, covered by CI). The 6 recorded Optional findings are dispositioned
  (3 fixed, 3 dropped with reasons); see `docs/milestones/completed/two-page-wording-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled (rows 12, 13,
27). Pick the next item, then `/milestone-plan`.
