# Approval gates

> For: anyone who decides who approves a work item's plan, code and acceptance. Last checked with: Workflow 2.8.0, Workflow Manager 1.4.0.

An approval gate is a point where a work item cannot move on until a decision
is recorded. There are three: plan approval, implementation approval and
milestone acceptance. Workflow 2.8 lets each repository choose who decides.

## The default is automatic, for most gates

With no `docs/ai-workflow/GATE_POLICY.json` file, the Workflow satisfies a gate
itself once its evidence is complete. A gate whose evidence is missing is
**blocked**, with the missing requirement named. It is never passed.

Which gates this covers depends on the work item's **governing version**: the
Workflow version it was started under, taken from `default_workflow_version`
in `docs/ai-workflow/WORKFLOW_CONFIG.json` when the item is created.

| Governing version | Plan approval | Implementation approval | Milestone acceptance |
| --- | --- | --- | --- |
| 2.2 | automatic | automatic | automatic |
| 2.1 (the default of a freshly bootstrapped repository) | automatic | always a person | automatic |
| 1 | always a person | always a person | automatic |

So in a fresh repository, plan approval and acceptance are automatic for new
items, and implementation approval stays with a person until the repository's
`default_workflow_version` is `"2.2"`. Updating a repository to 2.8.0 changes
no state file by itself.

## What evidence each gate needs

| Gate | Evidence the Workflow checks |
| --- | --- |
| Plan approval | The latest review verdict is approve and matches the current plan bundle. The two review stages come from different model families (on by default). Both review stages carry their audit details. |
| Implementation approval | The same checks, for the code. |
| Milestone acceptance | All checkpoints are complete. The implementation approval is current. At least one functional flow passed on the current code, none failed, and every flow you list as required passed. An open pull request exists for the same code. The pull request has no changes requested and its checks are not failing. CI is green (on by default). Optionally, a person has approved the pull request. |

Automatic acceptance needs the pull request to be open and pushed first. A
repository that opens its pull request only after acceptance keeps acceptance
human.

The commands behind this are `/satisfy-gate plan <id>`,
`/satisfy-gate implementation <id>` and `/satisfy-gate acceptance <id>`.
`/approve-review` and `/accept-milestone` stay available as the human path.

## Turn human approval on

For all three gates, create `docs/ai-workflow/GATE_POLICY.json`:

```json
{"schema_version": 1, "human_approval": true}
```

Every gate then needs a person, as in Workflow 2.7.0.

For one gate only, for example a person approves the plan and the rest stays
automatic:

```json
{
  "schema_version": 1,
  "gates": {
    "plan_approval": {"human": true}
  }
}
```

A person accepts only the milestone: set `human_approval` to true and
`"human": false` on `plan_approval` and `technical_approval`.

The gate names are `plan_approval`, `technical_approval` and `acceptance`.
To list the functional flows acceptance must see, or to require a person's
review of the pull request, use `required_flows` and `requires_pr_approved`
under `acceptance`.

## Tightening and loosening

A policy file can only make things stricter on its own.

- **Tightening** (a gate becomes human, a requirement is added) takes effect
  immediately. Deleting the file or editing it back does not undo it.
- **Loosening** needs the user-only command `/adopt-gate-policy`. Commit the
  file first, then run the command. It shows what will loosen and asks you to
  confirm. If the file differs from the committed one, it refuses
  (`GatePolicyFileUncommittedError`) and writes nothing.
- A change never reaches back: an approval already recorded keeps the policy it
  was given under.
- If the record of the adopted policy fails its own checks, all three gates
  become human until a new `/adopt-gate-policy` fixes it.

## Where facts about CI and pull requests come from

CI results and pull-request facts come only from the Workflow's own GitHub
query, run through the `gh` tool. A report from an orchestrator can only
trigger that query, never replace it. If `gh` is missing, not signed in, or
gives an unclear answer, the gate is blocked.

## The limits

The protection is against an agent that works through the Workflow's commands.
It is not against someone who forges commits or state by hand, or replaces
system programs such as `gh` or `git`. The Workflow guarantees that approvals
are tied to the reviewed content, go stale when it changes, and leave an audit
record. It does not prove that a review or a test run really happened.
Turning human approval on is the stronger mode: where the risk includes an
agent forging state, use human gates.

## More

The full operator guide is
[GATE_POLICY.md](https://github.com/RodrigoFAbreu/workflow/blob/main/payload/docs/ai-workflow/GATE_POLICY.md).
