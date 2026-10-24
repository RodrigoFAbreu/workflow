# Active Milestone

## Milestone

**In progress.** W23: `checkpoint-start-command` (`process`, governing version `2.2`), branch
`milestone/checkpoint-start-command`, roadmap row 24c (RodrigoFAbreu/workflow#55 and the three command items of
#97). Plan: `docs/ai-workflow/CHECKPOINT_START_COMMAND_PLAN.md` (revision 3, approved by gate policy).
The goal is Workflow 2.19.0, a minor release (`feat:`): the user-only command
`/release-checkpoint-start <work-item-id> <checkpoint-id>`, which releases an uncommitted checkpoint start by
calling the W22 engine after a confirmation bound to the claim the user was shown. The previous milestone, W22
`checkpoint-start-engine`, is accepted (Workflow 2.18.7).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The command, its confirmation, the amendment message and their tests | **complete** |
| CP2 | Release 2.19.0 | pending |

## Verified state

- CP1: `observe_checkpoint_start_release`, `release_checkpoint_start_confirmed`, the sentence builder and
  validator, `claim_reference` and the engine keyword `confirmed_claim_ref` are in
  `payload/scripts/workflow_state.py`; both `AmendmentCheckpointActiveError` raise sites name the command.
  `TestReleaseCheckpointStartCommand` (C1 to C5) was shown red against the unedited code and passes;
  `TestReleaseCheckpointStartCommandFile` (C6) pins the command file; the command file, `COMMAND_FILES.md`, the
  operator reference, `MILESTONE_WORKFLOW.md`, `request-plan-amendment.md` and the census tests are updated.
- No lock, guard, claim, `os.link` or `flock` site was added.
- Verified in a disposable clone (D-Staging): see the commit message of CP1 for the exact runs.

## Next action

`/milestone-implement checkpoint-start-command` for CP2 (Release 2.19.0).
