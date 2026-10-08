# Troubleshooting

> For: anyone who hit an error or a blocked work item. Last checked with: Workflow 2.9.0, Workflow Manager 1.4.0.

Each problem has a one-line fix. The exact rules are in the shipped documents
under `payload/docs/ai-workflow/`.

### An approval became stale after a change

The approval is tied to the reviewed content, and the content changed. Go back
through review: for a plan, `/apply-plan-review` (or `/milestone-plan` again)
and both review stages; for code, `/apply-implementation-review` and its
reviews. Do not edit the approval by hand.

### A gate is blocked for missing evidence

The Workflow names the unmet requirement. Provide that evidence (a review
verdict, a functional flow result, an open pull request, green checks) and run
`/satisfy-gate` again. A blocked gate is never passed on its own.

### GatePolicyFileUncommittedError

`/adopt-gate-policy` refuses a policy file that differs from the committed one.
Commit `docs/ai-workflow/GATE_POLICY.json` first, then run the command again.

### UnclassifiedPathError when generating a bundle

Every work item has a declaration: the files that count as reviewed content
(protected) and the files that are left out of it (excluded). A changed file is
in neither list. Add the path (or its folder) to one of them before the bundle
is generated. For a new `GATE_POLICY.json` on an older declaration,
exclude the `docs/ai-workflow/` prefix.

### An approve is refused because the reviewer models match

Automatic plan and implementation gates need two review stages from different
model families. Re-submit the approving verdict with a second declared
`Reviewer model:`, or turn that gate human in the [gate policy](gates.md).

### A gate is blocked because GitHub cannot be asked

The Workflow's own `gh` query failed: `gh` is not installed, not signed in, or
gave an unclear answer. Fix `gh`, then run `/satisfy-gate acceptance <id>`.

### A looser gate policy is ignored

A policy file can only tighten by itself. Commit it, then run
`/adopt-gate-policy` to loosen. See [approval gates](gates.md).

### Gates are all human and verify reports provenance_failed

The record of the adopted policy no longer checks out, which the Workflow's own `verify` check reports (not `workflow-manager verify`). A new
`/adopt-gate-policy` commit repairs it.

### A pull request turned red after completion

Run `/apply-pr-review <id>` with the work item id. It reopens the same work
item. A merged pull request is refused; the follow-up is a new work item.

### A legacy work item is stuck at LEGACY_READY

An imported legacy item that is already finished can be closed with the
user-only `/retire-legacy-work-item <id>`. Your own message must name the id and
the word `retirement`. It refuses any other phase, the active item and an item
with unfinished children. A retired item stays closed. Workflow 2.8.0 and
earlier have no such guard: on those releases a red pull-request report for a
retired item can reopen it, so do not report pull-request facts for it there, or
stay on 2.9.0.

### A work item sits at the functional gate with a checkpoint outstanding

Run the user-only `/resume-implementation <id>`; your own message names the id
and the word `resumption`. It returns a 2.1 or 2.2 item to `IMPLEMENTING` and
marks its technical approval stale; then `/milestone-implement` continues. An
item governed by version `1` is not handled by this command.
