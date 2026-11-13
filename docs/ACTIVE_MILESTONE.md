# Active Milestone

## Milestone

**Complete** (accepted by policy; a `docs:` change, no release). W49: `docs-restamp` (`process`, governing version `2.2`),
branch `milestone/docs-restamp`, roadmap row 42 (RodrigoFAbreu/workflow#147, the stamps part). The plan is
`docs/ai-workflow/DOCS_RESTAMP_PLAN.md` (revision 4, approved by gate policy); an archive copy is in
`docs/milestones/completed/`.

## Goal

Every user page with a `Last checked with` line says the release it was really re-checked against. Docs only: no
`payload/`, `tools/` or behaviour change, so no release (a `docs:` pull request, impact none; the manifest keeps 2.29.3).

## Outcome

- CP1 and CP2 are complete: seven stamps moved to Workflow 2.29.3 (Workflow Manager 1.18.1 where the page named the Manager);
  the retention and concurrency stamps stay at 2.25.6 and 2.19.2 because frozen release tests pin them. The stale wording was
  fixed (README, gates page, a concurrency row, the roadmap).
- The technical approval was recorded by policy. Functional flows 1 to 7 are recorded passed by the Controller's automated
  tester (flows 8 to 11 are automated verification, covered by CI). The 13 recorded Optional findings are dispositioned
  (5 fixed, 8 follow-ups in RodrigoFAbreu/workflow#178); see `docs/milestones/completed/docs-restamp-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled (rows 12, 13,
27). Pick the next item, then `/milestone-plan`.
