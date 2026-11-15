# Active Milestone

## Milestone

**Complete** (accepted by policy; a `fix:` change, Workflow patch release 2.29.5 follows the merge). W52:
`acceptance-gate-robustness` (`process`, governing version `2.2`), branch `milestone/acceptance-gate-robustness`, roadmap
row 45 (RodrigoFAbreu/workflow#155 points 4 to 6, #152 points 2 to 5). The plan is
`docs/ai-workflow/ACCEPTANCE_GATE_ROBUSTNESS_PLAN.md` (revision 5, approved by gate policy); an archive copy is in
`docs/milestones/completed/`.

## Goal

The plain acceptance report never ends in an error for an absent pull-request head, its requirement partition is pinned by a
test, and the path messages name the right file and phases. The gate does not change: `evaluate_gate` and every library
function return what they returned before.

## Outcome

- CP1 and CP2 are complete: the report names a stored pull-request fact whose head the repository lacks
  (`stored_pr_fact_unresolvable`), the requirement partition is pinned, the `phase_not_reachable` and path messages name the
  right file and phases (CP1), and Release 2.29.5 (CP2).
- The technical approval was recorded by policy. Functional flows 1 to 7 are recorded passed by the Controller's automated
  tester (flows 8 to 11 are automated verification, covered by CI on the pull request). The 15 recorded Optional findings are
  dispositioned (10 fixed, 4 follow-ups in RodrigoFAbreu/workflow#185, 1 dropped with a reason); see
  `docs/milestones/completed/acceptance-gate-robustness-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled (rows 12, 13,
26c, 27). Pick the next item, then `/milestone-plan`.
