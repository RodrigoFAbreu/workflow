# Active Milestone

## Milestone

**In progress.** W47: `wording-pass-plain-commands` (`process`, governing version `2.2`), branch `milestone/wording-pass-plain-commands`,
roadmap row 41 (RodrigoFAbreu/workflow#168, #165, #161 and #152 item 1). The plan is
`docs/ai-workflow/WORDING_PASS_PLAIN_COMMANDS_PLAN.md` (revision 2, approved by gate policy).

## Goal

Workflow 2.29.3 (a `fix:` patch): one pass over the stale wording of the plain acceptance commands. Every statement the four issues call
stale and the investigation found still false or misleading is corrected by the smallest true wording; the only changed output is the
detail of a library refusal (`complete_work_item`'s `phase_not_reachable`), which no plain flag prints. The protocol stays 1.5; the
Controller does not change.

## Checkpoints

- CP1 (the wording corrections, the library detail, the pins, the tests and row 41): complete (verified in a scratch fixture, see the commit).
- CP2 (release 2.29.3): complete (verified in a scratch clone, see the commit).

CP1 changes: `payload/scripts/workflow_state.py` (one string), `payload/scripts/workflow_gate_policy_test.py` (P7, P8; R6's needles),
`payload/scripts/workflow_integration_test.py` (two golden hashes), `payload/.claude/commands/satisfy-gate.md`, `accept-milestone.md`,
`apply-pr-review.md`, `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `audit/WORKFLOW_DEFECT_LEDGER.md`, `docs/exit-codes.md`,
`docs/common-problems.md`, `docs/ROADMAP.md` (row 41).

CP2 changes: `manifest.json` (version 2.29.3, the eleven changed records, gate-policy count 424, the posture),
`payload/scripts/workflow_protocol.py` and its test (`WORKFLOW_RELEASE` 2.29.3), `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`
(release list, envelope example, protocol 1.5 note; names no changed message), `docs/release-history.md` (the 2.29.3 row),
`docs/exit-codes.md` and `docs/common-problems.md` ("Last checked with" lines), `tools/release/release_test.py` (the 2.29.3 class;
the 2.29.2 and 2.25.7 classes give up the current-release pins).

## Next action

All checkpoints are complete. Run `/milestone-implement wording-pass-plain-commands` again: it enters
`SELF_REVIEWING_IMPLEMENTATION` (a no-op if the phase is already there), runs the full verification and prepares the implementation review bundle.
