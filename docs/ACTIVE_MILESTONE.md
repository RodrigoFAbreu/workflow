# Active Milestone

## Milestone

**Complete** (accepted by policy; a `fix:` change, Workflow patch release 2.29.4 follows the merge). W51:
`retention-engine-error-paths-2` (`process`, governing version `2.2`), branch `milestone/retention-engine-error-paths-2`,
roadmap row 44 (RodrigoFAbreu/workflow#119 items 1 and 3, #149 items 1, 2 and 5, #143 item 4). The plan is
`docs/ai-workflow/RETENTION_ENGINE_ERROR_PATHS_2_PLAN.md` (revision 3, approved by gate policy); an archive copy is in
`docs/milestones/completed/`.

## Goal

No path of the retention engine ends in a traceback, or names a directory the walk did not fail on, where the contract is a
named refusal: an item folder that cannot be opened (D-Walk), the lock-time recheck of `remove` (D-Lock), the same-name
collision of the report (D-Collision), an `OSError` no site maps (D-Stray) and the report's best-effort `close`.

## Outcome

- CP1 and CP2 are complete: the walks, the lock recheck, the collision, the backstop, tests and pages (CP1), and Release 2.29.4
  (CP2: `manifest.json`, `WORKFLOW_RELEASE`, the release history and the stamped pages; the protocol stays 1.5).
- The technical approval was recorded by policy. Functional flows 1 to 7 are recorded passed by the Controller's automated
  tester (flows 8 to 11 are automated verification, covered by CI on the pull request). The 26 recorded Optional findings are
  dispositioned (17 fixed, 2 follow-ups in RodrigoFAbreu/workflow#181, 7 dropped with reasons); see
  `docs/milestones/completed/retention-engine-error-paths-2-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled (rows 12, 13,
27). Pick the next item, then `/milestone-plan`.
