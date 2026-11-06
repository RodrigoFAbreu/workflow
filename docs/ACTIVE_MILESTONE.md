# Active Milestone

## Milestone

**Implementing.** W42: `acceptance-findings-floor` (`process`, governing version `2.2`), branch
`milestone/acceptance-findings-floor`, roadmap row 37 (RodrigoFAbreu/workflow#148, the rest). The plan is
`docs/ai-workflow/ACCEPTANCE_FINDINGS_FLOOR_PLAN.md` (revision 2, approved by gate policy). The previous milestone, W41
`acceptance-completion-command` (Workflow 2.27.0), is complete.

## Goal

Workflow 2.28.0 (a `feat:` minor): `python3 scripts/workflow_state.py --write-findings-record <id>` calls
`write_finding_dispositions_record` on the stored state and prints `{paths}`; it refuses an item that is not
`MILESTONE_COMPLETE`, takes no lock, writes only the record file and commits nothing. The floor commit is row 38; the
protocol stays 1.5.

## Checkpoints

- CP1 (the findings-record flag, its tests, the command texts and the pages): complete, verified state below.
- CP2 (release 2.28.0): complete, verified state below.

CP1 verified state: `TestWriteFindingsRecordCommand` (14 tests) passes; mutations m1 to m16 each fail the named test on a
scratch copy; the golden hash of `accept-milestone.md` moved (intentional); `workflow_integration_test.py` passes. The
staged-fixture run of the nine suites, `tools/docs` and `check_docs.py` is reported with the commit.

CP2 verified state (scratch clone with the changes committed): the nine suites pass from a `stage-conformance` fixture
(`workflow_gate_policy_test.py` 373); `check-manager-block --manager-releases` valid; `tools/docs` 34 tests and `check_docs.py`
clean; `tools/release` 313 tests pass (zlib-ng interpreter); `release.py build --commit HEAD` succeeds; `workflow-manager
verify .` clean (installation 2.27.0).

## Next action

`/milestone-implement acceptance-findings-floor` again: self-review, full verification and the implementation bundle.
