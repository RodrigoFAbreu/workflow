# Install and update the Workflow

> For: anyone adding the Workflow to a repository. Last checked with: Workflow 2.8.0, Workflow Manager 1.4.0.

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

## Before you install 2.8.0

Workflow 2.8.0 makes plan approval and milestone acceptance automatic (and
implementation approval too, for work items on Workflow version 2.2) unless the
repository commits a human policy first. If you want a person to keep approving, commit
`docs/ai-workflow/GATE_POLICY.json` with
`{"schema_version": 1, "human_approval": true}` before you update. See
[approval gates](gates.md).

An update never changes your work-item state. Do not move a repository back to
an older release once it has used a newer one.
