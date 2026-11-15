# Active Milestone

## Milestone

**In progress.** W53: `test-hardening-owner-points` (`process`, governing version `2.2`), branch
`milestone/test-hardening-owner-points`, roadmap row 46 (RodrigoFAbreu/workflow#170 point 1, #116 point 3, #158 point 3). The
plan is `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_PLAN.md` (revision 2, approved by gate policy). Docs only: no release.

## Goal

Settle the three points that needed an owner decision, with evidence: a recorded run of `TestPlainCommandMalformedState`
under the Manager's reaper, the ordering of the A12 and A15 race hooks, and the 2.27.0 posture sentence. Nothing under
`payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changes.

## Outcome

- CP1: the evidence is in `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`. #170 point 1: keep the test, the reaper
  run is `OK` with only Git's own helpers left (`[git]` and its detached maintenance). #116 point 3: already fixed, shown by
  three failure-only mutations of the retention engine. #158 point 3: keep, the sentence is true and every release carries it.
- One comment per issue is posted from the evidence file's last section; no issue is closed.

## Next action

The implementation is self-reviewed and its review bundle generated: the local implementation review, then the external one.
