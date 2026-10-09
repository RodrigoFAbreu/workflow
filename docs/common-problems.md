# Common problems

> For: anyone who hit an error or a blocked work item and wants the quick fix. Last checked with: Workflow 2.9.0.

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

### The write-commit helper refuses with ReviewStageWriteNotCommittableError

`commit_pending_applying_review_feedback_entry` commits only the entry into
`APPLYING_REVIEW_FEEDBACK`, and only fields a review write may change. It
refuses an uncommitted `APPROVE` (leave it) and any other field, such as a
persisted but uncommitted `technical_review_block_pins` entry left by a crash.
Commit that pin alone, as `/apply-implementation-review` step 1 does, then
re-run the command.
