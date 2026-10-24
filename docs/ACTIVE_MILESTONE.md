# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W23: `checkpoint-start-command` (`process`, governing version `2.2`), branch
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
| CP2 | Release 2.19.0 | **complete** |

## Verified state

- CP1: `observe_checkpoint_start_release`, `release_checkpoint_start_confirmed`, the sentence builder and
  validator, `claim_reference` and the engine keyword `confirmed_claim_ref` are in
  `payload/scripts/workflow_state.py`; both `AmendmentCheckpointActiveError` raise sites name the command.
  `TestReleaseCheckpointStartCommand` (C1 to C5) was shown red against the unedited code and passes;
  `TestReleaseCheckpointStartCommandFile` (C6) pins the command file; the command file, `COMMAND_FILES.md`, the
  operator reference, `MILESTONE_WORKFLOW.md`, `request-plan-amendment.md` and the census tests are updated.
- CP2: `manifest.json` names 2.19.0 (80 artifacts, 54 distribution; the command file has its record; every
  changed record has its digest, size and `checkpoint-start-command (workflow-2.19.0)` sentence; the manager
  block's posture and measured suite counts are rewritten); `WORKFLOW_RELEASE` and its two pinned assertions,
  `ORCHESTRATION_PROTOCOL.md` (protocol stays 1.5), `docs/release-history.md`, `docs/CONCURRENCY_INVARIANTS.md`,
  `docs/common-problems.md` and a 2.19.0 class in `tools/release/release_test.py` are updated.
- No lock, guard, claim, `os.link` or `flock` site was added.
- Verified in a disposable clone (D-Staging): see the commit message of CP1 for the exact runs.
- Functional review: six automated flows (`w23-a1` to `w23-a6`) passed at the approved content, recorded as
  orchestrator evidence by an independent executor; the manual flows M1 to M6 need a person in Claude Code and
  were not run (the owner's optional check). The acceptance record is the work item's `acceptance_satisfaction`.
- Optional findings: seventeen recorded, all dispositioned (three fixed, four dropped, ten follow-ups on
  RodrigoFAbreu/workflow#100); see `docs/milestones/completed/checkpoint-start-command-findings.md`.

## Next action

Merge pull request #101, let the `Release` workflow publish Workflow 2.19.0, then plan the next roadmap row
(`/milestone-plan`).
