# Glossary

> For: anyone reading Workflow documents. Last checked with: Workflow 2.8.0, Workflow Manager 1.4.0.

The shared terms of the Workflow. The other Workflow repositories link here.

### Work item

One unit of planned work tracked by the Workflow, identified by an id. Its
record lives in `docs/ai-workflow/WORKFLOW_STATE.json` in the repository the
Workflow is installed in, and that file is the ground truth for where the work
item is.

### Milestone

A work item that is planned, implemented, reviewed and accepted as one piece,
and that normally lands as one pull request.

### Phase

Where a work item is in the Workflow's lifecycle, for example `PLANNING`,
`IMPLEMENTING`, `AWAITING_PLAN_APPROVAL` or `MILESTONE_COMPLETE`. Phases that
begin with `AWAITING_` are points where the Workflow waits. The
[lifecycle](overview.md#lifecycle) shows the main ones.

### Checkpoint

One slice of a milestone's plan, implemented and committed on its own. A work
item has one or more checkpoints, done one per implementation step.

### Approval gate

Approval gate: one of the points in a work item's lifecycle where it cannot move on until a decision is recorded: plan approval, implementation approval (also called technical approval) and milestone acceptance. Up to Workflow 2.7, a person always makes these decisions. From Workflow 2.8, each gate follows the repository's gate policy (GATE_POLICY.json). By default the Workflow satisfies the gate itself once its evidence is complete (for example, both reviews approve). A repository that turns human approval on (`human_approval` for all gates, or `gates.<gate>.human` for one) gets the person-decides behavior back. The review stages (external plan review, external implementation review, functional review) are separate waiting points; they wait for a review result, not an approval.

A gate whose evidence is missing is blocked, not passed.

Two older cases stay human whatever the policy says: a version 1 work item always has a person for plan and implementation approval, and a version 2.1 work item always has a person for implementation approval.

### Gate policy

The repository's choice of who passes each approval gate, kept in
`docs/ai-workflow/GATE_POLICY.json`. With no file, the gates are automatic.
See [approval gates](gates.md).

### Review stage

One step of a review. Plan review and implementation review each have a local
stage and an external stage. Each stage records a verdict (approve, revise or
block) for the exact bundle it reviewed.

### Functional review

The check that finished work behaves correctly in real use. It happens after
implementation approval and before milestone acceptance, with a checklist
and recorded results for each flow.

### Bundle

The review package the Workflow generates for a plan or an implementation. It
is bound to the exact content that was reviewed, so a change after the review
makes the approval stale.

### Binding

A recorded tie between two things that must stay together. The Workflow binds a
published plan review to the plan content it reviewed.

### Protocol

The Workflow Orchestration Protocol: a small set of commands a Workflow
installation answers so a tool can drive it without knowing its internals
(`describe`, `next-action` and `reconcile`). Workflow 2.7.0 is the first
release that ships it, and major version 1 is the one the Controller speaks.
