# Active Milestone

## Milestone

**In progress (self-reviewing the implementation).** W35: `ci-latest-check-run` (`process`, governing version `2.2`), branch
`milestone/ci-latest-check-run`, roadmap row 30 (RodrigoFAbreu/workflow#122). Plan:
`docs/ai-workflow/CI_LATEST_CHECK_RUN_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.25.3 (a
`fix:` patch): the pull-request check state judges the latest run of each check, so a failed run and a green re-run no
longer leave `checks.state` at `failure`. Base commit `198b82b`; the previous milestone, W34 `retention-polish`, is
accepted (Workflow 2.25.2).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The latest run per check: the change, its tests and its sentence | **complete** |
| CP2 | Release 2.25.3 | **complete** |

## Verified state

- CP1: `_checks` in `payload/scripts/workflow_forge.py` groups entries by identity and keeps the latest run of each;
  `TestLatestCheckRun` (t1 to t10) passes; mutations m1 to m10 each fail the named tests; `workflow_gate_policy.py`,
  `_JSON_FIELDS` and the `gh` query are unchanged.
- CP2: `manifest.json` names 2.25.3 (six records re-hashed, the "ci-latest-check-run (workflow-2.25.3)" sentence, the
  posture, `workflow_gate_policy_test.py` 326); `WORKFLOW_RELEASE` is 2.25.3 with its pinned assertions and the
  protocol document edits (protocol stays 1.5); `docs/release-history.md` has the 2.25.3 row and its "Last checked
  with" line; `tools/release/release_test.py` has `CiLatestCheckRunReleaseTest`, the 2.25.2 class gave up the
  current-release pins, and every older docstring pointer names 2.25.3.

## Next action

Self-review the full diff, run the full verification, then prepare the implementation review bundle
(re-run `/milestone-implement ci-latest-check-run`).
