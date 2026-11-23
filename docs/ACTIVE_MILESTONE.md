# Active Milestone

## Milestone

**Complete** (accepted by policy; a `fix:` change, Workflow patch release 2.29.11 follows the merge). W60: `payload-test-hardening-1`
(`process`, governing version `2.2`), branch `milestone/payload-test-hardening-1`, roadmap row 53 (RodrigoFAbreu/workflow#85 points 1
to 3, #194 points 1 and 3, #108 point 4). The plan is `docs/ai-workflow/PAYLOAD_TEST_HARDENING_1_PLAN.md` (revision 3); an archive copy
is in `docs/milestones/completed/`.

## Goal

Six existing payload tests now pin behaviour the product already had but the tests did not check. No product behaviour, message, key,
code or phase changed, and no test method was added or removed. CP1 strengthened the tests in
`payload/scripts/workflow_integration_test.py`, `workflow_state_test.py` and `workflow_state_completion_obligations_test.py`. CP2 is
Workflow release 2.29.11, a `fix:` patch, because those three files are shipped records.

## Outcome

- CP1 (the six strengthened tests) and CP2 (release 2.29.11) are complete.
- The technical approval was recorded by policy. Functional flows 1 to 13 are recorded passed.
- The 10 recorded Optional findings are dispositioned (5 fixed, 2 dropped, 3 follow-up, with reasons or link); see
  `docs/milestones/completed/payload-test-hardening-1-findings.md`.
- Not taken: #85 point 4 and #108 point 3 (both change payload code or a message, and the owner deferred them). #194 point 2 is
  obsolete: the test it names no longer exists on main.
- Nothing is pushed, merged, published or pinned here. The release is published by `Build and publish` after the merge, and the
  Manager pin is a separate `workflow-manager` pull request.

## Next action

The next incomplete milestone in `docs/ROADMAP.md` is row 27 ("Deferred: review-data simplification, longer-term evolution"), which is
deferred and trigger-driven (see "Later (open items)"). No item is ready for `PLANNING` until its trigger fires. `/milestone-plan` when
one is chosen.
