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
- CP2 (release 2.29.3): not started.

CP1 changes: `payload/scripts/workflow_state.py` (one string), `payload/scripts/workflow_gate_policy_test.py` (P7, P8; R6's needles),
`payload/scripts/workflow_integration_test.py` (two golden hashes), `payload/.claude/commands/satisfy-gate.md`, `accept-milestone.md`,
`apply-pr-review.md`, `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `audit/WORKFLOW_DEFECT_LEDGER.md`, `docs/exit-codes.md`,
`docs/common-problems.md`, `docs/ROADMAP.md` (row 41).

## Next action

Run `/milestone-implement wording-pass-plain-commands` again for CP2 (release 2.29.3).
