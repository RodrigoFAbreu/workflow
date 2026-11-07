# Active Milestone

## Milestone

**In progress.** W44: `acceptance-phase-guard` (`process`, governing version `2.2`), branch `milestone/acceptance-phase-guard`,
roadmap row 39 (RodrigoFAbreu/workflow#158, item 1). The plan is `docs/ai-workflow/ACCEPTANCE_PHASE_GUARD_PLAN.md` (revision 2,
approved by gate policy). The previous milestone, W43 `acceptance-floor-commit` (Workflow 2.29.0), is complete.

## Goal

Workflow 2.29.1 (a `fix:` patch): `complete_work_item` refuses unless the item is at `AWAITING_FUNCTIONAL_REVIEW` or
`AWAITING_USER_ACCEPTANCE` (`CompletionPhaseNotReachableError`, codes `work_item_terminal` / `phase_not_reachable`, checked after the
child and own-registry checks and before the obligations), and the acceptance stage's phase and registry check moves from before the
lock to the first statement of `satisfy_acceptance_gate`'s mutator, so a writer landing before the lock can no longer make the stage
complete from a phase it must refuse. The protocol stays 1.5; the Controller does not change.

## Checkpoints

- CP1 (the phase guard in the library and inside the lock, tests, command text and pages): implemented; verified state below.
- CP2 (release 2.29.1): not started.

CP1 changes: `payload/scripts/workflow_state.py` (the error class, the guard, the mutator's first statement, the CLI's outside call
removed), `payload/scripts/workflow_gate_policy_test.py` (`TestCompletionPhaseGuard`, P1 to P6; the three named existing-test edits:
the `AcceptanceRepo` fixture's phase, the two old-phase assertions, `test_s8`), `payload/.claude/commands/satisfy-gate.md`,
`payload/.claude/commands/accept-milestone.md`, `docs/exit-codes.md`, `docs/ROADMAP.md` (row 39).

## Next action

Self-review of the full diff, then the implementation-review bundle (`/milestone-implement`, steps 2 to 5).
