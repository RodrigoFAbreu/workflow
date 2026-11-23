# Active Milestone

## Milestone

W61: `payload-polish-batch` (`process`, governing version `2.2`), branch `milestone/payload-polish-batch`, base
`16e013022e01e52b572b2a24090e91c4e886ae63`. Release Workflow 2.29.12, a `fix:` patch. Row 54 of `docs/ROADMAP.md`. Issues
RodrigoFAbreu/workflow#108 point 3, #85 point 4, #205, and #208 points 1 and 2. The plan is
`docs/ai-workflow/PAYLOAD_POLISH_BATCH_PLAN.md` (revision 3).

## Goal

Three wording points and two test follow-ups in the shipped payload. No refusal order, command, exit code or working path changes.
The release (manifest `workflow_version` 2.29.12, the history row, the protocol document's release lines) is part of this branch;
its version bump is commit `903d363`.

## Outcome (complete)

- CP1 (`791418f`), CP2 (`525a3db`) and CP3 (`903d363`) are complete. Implementation review round 3: local `APPROVE`
  (`LOCAL_MODEL_IMPLEMENTATION_REVIEW`) and external `APPROVE` (manual, `openai/gpt-6.1-sol`) on implementation revision 2. The
  technical approval is `CURRENT` (recorded by policy, `afd7c9d`).
- Implementation revision 2 changed the #85 wording to three arms, not the two the plan's D-Wording 2 text describes (round 2 of the
  implementation review, LIR-R1-001: a non-takeover ordinary guard cannot be recovered by "abandoned-guard recovery", which refuses it).
  The plan bytes are the approved ones, so the plan's D-Wording 2 text is stale on this point; the shipped wording is recorded in
  `.ai-review/payload-polish-batch/current/IMPLEMENTATION_SUMMARY.md` (round 2) and in the history row and roadmap row 54.
- Automated verification is recorded in `.ai-review/payload-polish-batch/current/TEST_RESULTS.md` (revision 2). No shipped file, test
  or manifest has changed since `26be4f1`, so that verification is current. Results: the nine payload suites pass (453, 344, 1250,
  429, 151, 319, 385, 283 and 27 tests); `tools/release` 388 tests; `tools/docs` 34 tests; `check_docs.py` exit 0;
  `check-manager-block` ok; `check-title` `impact=patch`; `release.py build` exit 0; the reaper on the touched tests; mutations m1,
  m2, m2b, m3, m4 (a) and (b), and m5 each fail exactly what the plan states.
- Not taken, recorded as optional findings in the plan (section 0): F1 (the remove flow's other strays before its rename keep the
  "renamed aside" text) and F2 (the leftover note is appended twice in the `_flow` lock-time re-selection, pre-existing). Neither is a
  defect of this batch to fix here.
- Nothing is pushed, merged or published. The installation (`.claude/`, `scripts/`, `.workflow-manager/`, managed blocks,
  `.github/`) is untouched, so `workflow-manager verify .` reports the installation at 2.29.11. That is expected until a release is
  published and a manager pin is added.

## Next action

`payload-polish-batch` is complete (accepted by policy, `policy:bae758b4f4ce`). No roadmap item is ready for `PLANNING` in this
repository: the open rows are waiting on the Controller (rows 12 and 13) or are deferred ("Later (open items)"). Run `/milestone-plan`
when the next milestone is chosen. Nothing is pushed, merged or published; the release (Workflow 2.29.12) follows the merge.
