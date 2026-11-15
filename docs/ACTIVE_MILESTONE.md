# Active Milestone

## Milestone

**Complete** (accepted by policy; a `fix:` change, Workflow patch release 2.29.6 follows the merge). W54:
`bundle-revision-sections` (`process`, governing version `2.2`), branch `milestone/bundle-revision-sections`, roadmap row 47
(RodrigoFAbreu/workflow#142). The plan is `docs/ai-workflow/BUNDLE_REVISION_SECTIONS_PLAN.md` (revision 4, approved by gate
policy); an archive copy is in `docs/milestones/completed/`.

## Goal

An implementation bundle of revision N shows the test record and the fixes of every revision up to N, in a stable documented form.
The change is the text a worker follows (`milestone-implement.md`, `apply-implementation-review.md`, `apply-functional-review.md`,
`apply-pr-review.md`) and the contract a reviewer reads (`REVIEW_PROTOCOL.md`), with the tests that pin them. The generator
(`prepare-ai-review.sh`), the fingerprint, the state, the identifiers and every check do not change.

## Outcome

- CP1 (the form, the four commands, the contract, the tests) and CP2 (release 2.29.6: manifest, protocol constant, history row,
  release tests) are both complete.
- The technical approval was recorded by policy. Functional flows 1 to 7 are recorded passed by the Controller's automated
  tester (flows 8 to 11 are automated verification, covered by CI on the pull request). The 16 recorded Optional findings are
  dispositioned (12 fixed, 4 follow-ups in RodrigoFAbreu/workflow#190); see
  `docs/milestones/completed/bundle-revision-sections-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled (rows 12, 13,
26c, 27). Pick the next item, then `/milestone-plan`.
