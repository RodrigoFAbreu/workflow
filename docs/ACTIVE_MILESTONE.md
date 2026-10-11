# Active Milestone

## Milestone

**Implementing** (plan revision 2). W5: `retire-21-for-new-work` (`process`,
governing version `2.2`), branch `milestone/retire-21-for-new-work`, base
`b854a0b` (the release source is Workflow 2.9.2; this repository's own
installation is also 2.9.2 with automatic gates and no `GATE_POLICY.json`). The
plan is `docs/ai-workflow/RETIRE_21_FOR_NEW_WORK_PLAN.md`. The previous
milestone, W6 (`functional-fix-commit-order`, Workflow 2.9.2), is complete.
This is a re-plan: W5 was planned once on 2.9.1 and paused at its plan review
while W6 went first; that work was never committed.

## Goal

Workflow 2.10.0, a minor release (`feat:`), roadmap row 7:

1. **New work items stop starting on "2.1".** While `WORKFLOW_CONFIG.json`
   names "2.1" as the default, creating a new work item (a fresh
   `/milestone-plan`, or a broad remediation child from
   `/apply-functional-review` or `/apply-pr-review`) refuses before any write
   with `DefaultWorkflowVersionRetiredError` and one next step: set the default
   to "2.2" in a `Workflow-Activation: 2.2` commit. Existing "2.1" items keep
   working to completion, legacy adoption still targets "2.1", "2.1" stays in
   `supported_versions`, and nothing persisted changes. Orchestration Protocol
   1.3 adds row 1b (`blocked`, `plan_start_default_retired`) and an advisory
   `verify` check, `default_workflow_version`.
2. **A faster managed conformance job.** `workflow-conformance.yml` cancels a
   pull request's superseded run on a new push (push runs are never cancelled)
   and runs the nine suites in parallel inside the one `workflow-conformance`
   job, each in its own copy of the checkout with its own `TMPDIR` and `HOME`,
   every failure shown and annotated.
3. **Two version-aware wording fixes** W6 deferred:
   `recover-implementation-provenance.md`'s introduction and
   `MILESTONE_WORKFLOW.md`'s broad-branch line.

The Manager side (the `workflow-manager doctor` warning, and the Manager's
template test pattern) ships in the Manager pin pull request; the plan's
D-Manager-Handoff says exactly what.

## Current checkpoint

Implementing (plan revision 2, approved). CP1 (the refusal at creation, and the
fixtures that seed existing "2.1" items) is complete: `workflow_state.py` gains
`NEW_WORK_RETIRED_VERSIONS`, `RETIRED_DEFAULT_NEXT_STEP`,
`DefaultWorkflowVersionRetiredError` and `assert_default_admits_new_work_item`,
which `route_work_item`'s fresh branch and `create_remediation_child_work_item`
call; the harness gains `seed_existing_work_item` and
`seed_existing_remediation_child`; the acceptance matrix creates its items
through one `route_item` helper, and the three real-creator child scenarios run
under a `Workflow-Activation: 2.2` default. CP2 (Orchestration Protocol 1.3) is
complete: `workflow_protocol.py` narrows row 1 to a default that is not retired,
adds row 1b (`plan_start_default_retired`, remedy `RETIRED_DEFAULT_NEXT_STEP`,
evaluated between rows 1 and 1a) and the advisory `default_workflow_version`
`verify` check, and `PROTOCOL_VERSION` is `1.3`; the protocol document, the
schema's check-id list and the protocol suite's mirror and release-comparison
tests follow. CP3 (command texts) is complete: `milestone-plan.md` step 0 stops a fresh
milestone under a "2.1" default before step 1, `apply-functional-review.md`
checks `assert_default_admits_new_work_item` before the first bounded sub-step,
and `apply-pr-review.md`'s broad fix names the refusal, that step 1's write
stands, and the re-run from `already_reopened`; the integration suite updates
two golden hashes, pins `apply-pr-review.md`, and adds static conformance tests.
CP4 (regression scenarios) is complete: the acceptance matrix gains
`RetiredDefaultVersionProcess`/`...Product` (14 scenarios each): the refusal on
every creation path under a "2.1" default (fresh milestone, row 1b, a broad
functional-review child, a broad pull-request child, with the `reconcile`
classes and the `verify` warning), the same paths after the
`Workflow-Activation: 2.2` edit (the "2.2" child driven through its own cycle to
`MILESTONE_COMPLETE`, then the "2.1" parent accepted), an existing "2.1" item
run to completion under a "2.1" default and under a "2.2" default, a "2.2" and
a "1" default unchanged, legacy adoption unchanged, and the shipped templates.
`Item.approve_implementation` gains an opt-in `scoped_staging`. The matrix runs
381 tests (353 + 28), all green. CP5 (managed conformance job) is complete: the
template gains the `concurrency` block (a pull request's runs share one group
and cancel; any other run is keyed by `run_id`/`run_attempt`) and one
`Run the conformance suites` step that runs the nine suites `min(4, nproc)` at a
time, longest first, each in its own checkout copy with its own `TMPDIR` and
`HOME`, every suite always run, failures unfolded with an `::error` line;
`release_test.py` gains `ConformanceTemplate` (7 tests). Verified in a scratch
clone with refreshed digests: the full `release_test.py` (86 tests, Python 3.12)
green; the step body on the nine real suites green in 4m09s wall against 572s
sequential. The committed manifest digests are refreshed at CP7. CP6 and CP7 are
not started.

## Next action

`/milestone-implement retire-21-for-new-work` again: it implements CP6, one
checkpoint per invocation.

## Functional review checklist

Written at `/prepare-functional-review`.
