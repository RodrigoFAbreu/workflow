# Active Milestone

## Milestone

**Complete** (accepted by policy; a `docs:` change, no release). W53: `test-hardening-owner-points` (`process`, governing
version `2.2`), branch `milestone/test-hardening-owner-points`, roadmap row 46 (RodrigoFAbreu/workflow#170 point 1, #116
point 3, #158 point 3). The plan is `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_PLAN.md` (revision 2, approved by gate
policy); an archive copy is in `docs/milestones/completed/`.

## Goal

Settle the three points that needed an owner decision, with evidence: a recorded run of `TestPlainCommandMalformedState`
under the Manager's reaper, the ordering of the A12 and A15 race hooks, and the 2.27.0 posture sentence. Nothing under
`payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changed, so there is no release (the manifest keeps 2.29.5).

## Outcome

- CP1 is complete: the evidence is in `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`. #170 point 1: keep the
  test, the reaper run is `OK` with only Git's own helpers left (`[git]` and its detached maintenance). #116 point 3: already
  fixed, shown by three failure-only mutations of the retention engine. #158 point 3: keep, the sentence is true and every
  release from v2.25.6 carries it.
- One comment per issue is posted from the evidence file's last section; no issue is closed.
- The technical approval was recorded by policy. Functional flows 1 to 7 are recorded passed by the Controller's automated
  tester (flows 8 to 11 are automated verification, covered by CI on the pull request). The 9 recorded Optional findings are
  dispositioned (5 fixed, 1 follow-up in RodrigoFAbreu/workflow#188, 3 dropped with a reason); see
  `docs/milestones/completed/test-hardening-owner-points-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled (rows 12, 13,
26c, 27). Pick the next item, then `/milestone-plan`.
