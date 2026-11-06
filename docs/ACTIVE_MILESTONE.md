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
- CP2 (release 2.29.0): implemented, verified state below.

CP1 verified state: `TestCommitFloorCommand` (29 tests at that commit) passes on the working tree, alongside the 2.26.0 to 2.28.0 command
classes; the source of `commit_gate_policy_floor` hashes to the base's value (pinned by F8). The staged-fixture run of the nine
suites, `tools/docs`, `check_docs.py`, `check-manager-block` and `tools/release` ran under D-Staging (the one expected failure is the
2.28.0 release class's suite-count pin, released in CP2). The CP1 commit carries no report of them, and no record of the failure-only
mutations survives from CP1: they were run in self-review, below.

CP2 verified state: `manifest.json` is 2.29.0 (six records, posture, suite count 402 for `workflow_gate_policy_test.py`), `WORKFLOW_RELEASE`
is 2.29.0, the protocol document, release history and exit-codes page follow, and `tools/release/release_test.py` has the 2.29.0 class
with the 2.28.0 class demoted. In a disposable clone: all nine suites pass from a stock `stage-conformance` fixture, `release.py build`
succeeds (zlib-ng interpreter), `check-manager-block` (with `--manager-releases`) is ok, `tools/docs` tests and `check_docs.py` are clean,
`tools/release` tests pass (317). `workflow-manager verify .` is clean against the installed 2.28.0.

Self-review (`/milestone-implement`, full diff), three gaps fixed, no engine change. (1) The command text lacked D-Output's sentence on
`state_changed: true` with `commit: null`, which means something else than on the flags before it: `satisfy-gate.md` and `docs/exit-codes.md`
now say it, and R6 pins it. (2) Mutants m14 (dispatch after the shared `git rev-parse`, and the empty id) survived: the class called the CLI
function directly, past the parser. F7's parser test now covers both. (3) F7 did not pin the five existing flags' output, so m16 survived;
`test_f7_the_existing_flags_print_what_they_printed` is new. The suite count for `workflow_gate_policy_test.py` is 403. The series m1 to m26 now
runs, each mutant failing a named test; the results are in the implementation bundle's `TEST_RESULTS.md`.

## Functional review checklist

Not yet written: `/prepare-functional-review` produces it from section 5 of the plan once the implementation review is done.
