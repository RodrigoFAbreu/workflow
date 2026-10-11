# Active Milestone

## Milestone

**Planning** (plan revision 1). W5: `retire-21-for-new-work` (`process`,
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

None yet: the plan is at its first review.

## Next action

The plan (revision 1) goes to `AWAITING_LOCAL_PLAN_REVIEW` (a "2.2" item's plan
review starts with the local model): `/review-plan retire-21-for-new-work`.

## Functional review checklist

Written at `/prepare-functional-review`.
