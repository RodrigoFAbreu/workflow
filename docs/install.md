# Install and update the Workflow

> For: anyone adding the Workflow to a repository. Last checked with: Workflow 2.17.0, Workflow Manager 1.5.0.

The Workflow is installed, updated and checked with the
[Workflow Manager](https://github.com/RodrigoFAbreu/workflow-manager#readme).
You never copy its files by hand.

First
[install the Workflow Manager](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/install.md).
Then:

```bash
workflow-manager bootstrap <repo>   # install the Workflow into a repository
workflow-manager update <repo>      # move it to a newer release
workflow-manager verify <repo>      # check the installed files match the release
```

Details are on the Manager's pages:
[install](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/install.md),
[update](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/update.md)
and
[verify](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/verify.md).

## After installing: an optional backlog file

A repository can keep its planned work in a structured backlog file that
`/milestone-plan` reads and acceptance updates (Workflow 2.17). It is off until
the repository declares it in `docs/ai-workflow/WORKFLOW_CONFIG.json`; an
install or update never turns it on. Setup, the file format and the way back to
an earlier release are in [the backlog file](../payload/docs/ai-workflow/BACKLOG_FILE.md).

## The default version of a new installation

From Workflow 2.9, `bootstrap` creates `docs/ai-workflow/WORKFLOW_CONFIG.json`
with `default_workflow_version` `"2.2"`, so a new work item in a fresh repository
runs on Workflow version 2.2. `update` never rewrites a configuration that
already exists, and an existing work item keeps its governing version.

From Workflow 2.10, a configuration that still names `"2.1"` as the default
cannot start a new work item: `/milestone-plan`, `/apply-functional-review` (a
broad fix) and `/apply-pr-review` refuse before creating it, and the
Workflow's own `verify` check warns. Change it to `"2.2"` (with `"2.2"` in
`supported_versions`) in a commit carrying `Workflow-Activation: 2.2` before the
next new item. Existing `"2.1"` items finish unchanged. See
[Common problems](common-problems.md).

Retirement (`/retire-legacy-work-item`) is guarded by Workflow 2.9: a retired
legacy item stays closed. A repository later moved back to 2.8.0 or earlier has
no such guard, so a pull-request report for a retired item can reopen it there;
do not report pull-request facts for a retired item on those releases.

Workflow 2.9 also adds the user-only `/resume-implementation`, which returns a
work item stuck at the functional gate with a checkpoint outstanding to
implementation; see [Common problems](common-problems.md).

## Before you install 2.8.0

Workflow 2.8.0 makes plan approval and milestone acceptance automatic (and
implementation approval too, for work items on Workflow version 2.2) unless the
repository commits a human policy first. If you want a person to keep approving, commit
`docs/ai-workflow/GATE_POLICY.json` with
`{"schema_version": 1, "human_approval": true}` before you update. See
[approval gates](gates.md).

An update never changes your work-item state. Do not move a repository back to
an older release once it has used a newer one.
