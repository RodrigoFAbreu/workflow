# Active Milestone

## Milestone

**In progress.** W41: `acceptance-completion-command` (`process`, governing version `2.2`), branch
`milestone/acceptance-completion-command`, roadmap row 36 (RodrigoFAbreu/workflow#148, the second half). The plan is
`docs/ai-workflow/ACCEPTANCE_COMPLETION_COMMAND_PLAN.md` (revision 3, approved by gate policy). The previous milestone,
W40 `acceptance-plain-command` (Workflow 2.26.0), is complete.

## Goal

Workflow 2.27.0 (a `feat:` minor): `python3 scripts/workflow_state.py --satisfy-acceptance <id>` makes the stage's step 2a
phase and registry check, then runs `satisfy_acceptance_gate` in one `state_transaction` and prints `{record, trailer}`.
Gate semantics do not change; the protocol stays 1.5. The findings record and the floor commit are row 37.

## Checkpoints

- **CP1 (the completion flag, its tests, the command text and the pages): complete.** `_acceptance_reachability_blocker`
  is shared by the report and the command; `AcceptancePreflightError`, `_satisfy_acceptance_cli` and the fourth flag in
  the exclusive group are in `payload/scripts/workflow_state.py`; `TestSatisfyAcceptanceCommand` (S1 to S8, 12 tests)
  is in `payload/scripts/workflow_gate_policy_test.py` (suite 346 to 358 tests, all passing); `satisfy-gate.md` and
  `docs/exit-codes.md` name the flag. Verified in the disposable clone of D-Staging (see the milestone commit).
- CP2 (release 2.27.0): not started.

## Next action

`/milestone-implement acceptance-completion-command` again for CP2.
