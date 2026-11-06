# Active Milestone

## Milestone

**In progress (implementing).** W43: `acceptance-floor-commit` (`process`, governing version `2.2`), branch
`milestone/acceptance-floor-commit`, roadmap row 38 (RodrigoFAbreu/workflow#148, the last Python call). The plan is
`docs/ai-workflow/ACCEPTANCE_FLOOR_COMMIT_PLAN.md` (revision 5, approved by gate policy). The previous milestone, W42
`acceptance-findings-floor` (Workflow 2.28.0), is complete.

## Goal

Workflow 2.29.0 (a `feat:` minor): `python3 scripts/workflow_state.py --commit-gate-policy-floor <id>` calls
`commit_gate_policy_floor` (unchanged, byte for byte) and, when that answers `None`, a new sibling
`commit_pending_gate_policy_floor` that commits a floor already waiting in the state file after six preconditions;
prints `{commit, recovered}`. It refuses unless the item is `MILESTONE_COMPLETE` and `HEAD` holds its completed copy. The
acceptance stage then has no inline Python call; the protocol stays 1.5.

## Checkpoints

- CP1 (the floor flag, its recovery, tests, the command text and the pages): implemented, verified state below.
- CP2 (release 2.29.0): not started.

CP1 verified state: `TestCommitFloorCommand` (29 tests) passes on the working tree, alongside the 2.26.0 to 2.28.0 command
classes; the source of `commit_gate_policy_floor` hashes to the base's value (pinned by F8). The staged-fixture run of the nine
suites, `tools/docs`, `check_docs.py`, `check-manager-block` and `tools/release`, and the failure-only mutations, are reported
with the CP1 commit (D-Staging; the one expected failure is the 2.28.0 release class's suite-count pin, released in CP2).

## Functional review checklist

Not yet written: `/prepare-functional-review` produces it from section 5 of the plan once the implementation review is done.
