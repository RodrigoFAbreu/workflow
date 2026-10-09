# Documentation map

> For: anyone looking for the right page. Last checked with: Workflow 2.9.0.

| I want to... | Go to |
| --- | --- |
| understand what the Workflow is | [README](../README.md) |
| see how a work item moves from plan to merge | [How it works](overview.md#lifecycle) |
| decide who approves plans, code and acceptance | [Approval gates](gates.md) |
| install or update the Workflow in a repository | [Install and update](install.md) |
| look up a term | [Glossary](glossary.md) |
| fix an error message | [Common problems](common-problems.md) |
| look up what a script's exit status means | [Exit codes](exit-codes.md) |
| see what changed in each release | [Release history](release-history.md) |
| run the lifecycle automatically | [Workflow Controller](https://github.com/RodrigoFAbreu/workflow-controller#readme) |
| install the tooling | [Workflow Manager](https://github.com/RodrigoFAbreu/workflow-manager#readme) |
| build and publish a release (maintainers) | [Releasing](RELEASING.md) |
| read the exact rules (maintainers) | the shipped documents in [payload/docs/ai-workflow](../payload/docs/ai-workflow/) |

The shipped reference documents most readers need:

- [MILESTONE_WORKFLOW.md](../payload/docs/ai-workflow/MILESTONE_WORKFLOW.md):
  every state and hard gate.
- [GATE_POLICY.md](../payload/docs/ai-workflow/GATE_POLICY.md): the gate policy.
- [PLAN_REVIEW_WORKFLOW.md](../payload/docs/ai-workflow/PLAN_REVIEW_WORKFLOW.md)
  and
  [REVIEW_PROTOCOL.md](../payload/docs/ai-workflow/REVIEW_PROTOCOL.md): reviews
  and bundles.
- [ORCHESTRATION_PROTOCOL.md](../payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md):
  how a tool drives the Workflow.
