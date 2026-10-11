# Common problems

> For: anyone who hit an error or a blocked work item and wants the quick fix. Last checked with: Workflow 2.9.1.

Each problem has a one-line fix. The exact rules are in the shipped documents
under `payload/docs/ai-workflow/`. What a script's exit status means is in
[exit codes](exit-codes.md).

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

### A new work item was refused: the default is "2.1"

`/milestone-plan`, `/apply-functional-review` (a broad fix) or `/apply-pr-review`
stopped with `DefaultWorkflowVersionRetiredError`, or `next-action` reports
`plan_start_default_retired`, or `workflow-manager verify` warns
`default_workflow_version`. Nothing was written. Set `default_workflow_version`
to `"2.2"` in `docs/ai-workflow/WORKFLOW_CONFIG.json` (with `"2.2"` in
`supported_versions`), commit it with the trailer `Workflow-Activation: 2.2`,
then run the command again. Existing `"2.1"` items are not affected.

Where to commit it: on the new work's branch where there is one. For the two
remediation-child paths, on the parent's branch while the parent is at
`AWAITING_FUNCTIONAL_REVIEW` (no generation gate is armed there, and
`WORKFLOW_CONFIG.json` is excluded in the template's implementation-stage
classification). Otherwise where no item is awaiting a review or gate. If it
was already committed while a review was pending and
`bundle_generation_mismatch` followed, run `/recover-implementation-provenance`.

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

### A REVISE round is refused with "must always transition phase"

Either the review stage's `REVISE` write, or `/apply-implementation-review`'s
own entry into `APPLYING_REVIEW_FEEDBACK` (the ordinary route for `"1"` and
`"2.1"` items, where no review stage writes `REVISE`), was never committed on
its own, so the post-fix generation-record commit swept it up and showed no
`phase` change. On Workflow 2.9.1 the review commands commit the `REVISE`
write, and `/apply-implementation-review` commits a pending one, or its own
entry, before its first fix commit. On Workflow 2.9.0 and earlier, which have no
such step, commit the state file alone, with a `Workflow-Work-Item: <id>`
trailer as the final paragraph, after the review writes `REVISE` and before any
fix commit, or, after `/apply-implementation-review` has entered
`APPLYING_REVIEW_FEEDBACK`, before its first fix commit.

Both prevent the refusal; neither repairs a generation-record commit that was
already refused. Re-running `/apply-implementation-review` then does nothing:
the record commit already holds the state. The forward repair used so far is
in [issue #13](https://github.com/RodrigoFAbreu/workflow/issues/13).

### An approve or gate check is refused with bundle_generation_mismatch after a review

An `APPROVE` write was committed on its own, which puts `HEAD` past the bundle's
generation head. Leave an `APPROVE` write (and every plan-stage write)
uncommitted: `/approve-review` or `/satisfy-gate` takes it. A bundle is bound to
the `HEAD` it was generated at. Once a stray commit is past it, the remedy is
`/recover-implementation-provenance <id>`. It changes the bundle id, so both
review verdicts go stale and need another review round. Never edit the
recorded generation head by hand.

### The next review stops with bundle_generation_mismatch after a functional fix

A commit landed after the post-fix generation record, typically the checklist
update in `docs/ACTIVE_MILESTONE.md`, which moved `HEAD` past the bundle's
generation head. From 2.9.2, `/apply-functional-review`'s bounded branch commits
the stale `technical_approval` write, the fix, the narrative and the checklist
first, and the generation record last. On 2.9.1, do that order by hand: commit
the stale `technical_approval` write alone before the first fix edit, commit
the checklist before the record and commit nothing after it. An uncommitted
stale write left for the record to sweep up shows instead as a refused
generation record that names `technical_approval`. If it already
happened, `/recover-implementation-provenance <id>` repairs it; it changes the
bundle id, so both review verdicts go stale and need another round. Never edit
the recorded generation head by hand.

### A generation record is refused for its trailer set

The record's final paragraph holds more than the `Workflow-*` trailers, usually
a `Co-Authored-By:` line, and the trailer set is checked exactly. Put
`Co-Authored-By:`/`Claude-Session:` lines in an earlier paragraph, separated by
a blank line, and keep only the `Workflow-*` trailers in the last one. While the
refused commit is still the unpublished `HEAD`, rewrite its message in that
layout (same tree); a later recovery cannot supersede it. Once it is published
or built on, ask the repository owner.

### The write-commit helper refuses with ReviewStageWriteNotCommittableError

`commit_pending_applying_review_feedback_entry` commits only the entry into
`APPLYING_REVIEW_FEEDBACK`, and only fields a review write may change. It
refuses an uncommitted `APPROVE` (leave it) and any other field, such as a
persisted but uncommitted `technical_review_block_pins` entry left by a crash.
For a leftover pin, stage the state file with
`workflow_state.stage_scoped_state(repo_root, <id>)` (when it returns `False`,
stage exactly `docs/ai-workflow/WORKFLOW_STATE.json`) and commit it with a
`Workflow-Work-Item: <id>` trailer as the final paragraph; never stage the
whole file while another work item holds uncommitted state. The helper then
returns `None` and the post-fix generation proceeds. For any other field, the
write is not a pure review-stage entry: investigate it, then commit or revert
it deliberately. When a pin and another field are both left, resolve the
other field first and commit the pin only afterwards. If another path is
staged, the helper raises `DirtyIndexBeforeStagingError`; unstage the unrelated
content first.
