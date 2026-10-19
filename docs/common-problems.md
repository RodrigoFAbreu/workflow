# Common problems

> For: anyone who hit an error or a blocked work item and wants the quick fix. Last checked with: Workflow 2.16.0.

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
`plan_start_default_retired`, or the Workflow's own `verify` check (not
`workflow-manager verify`) warns `default_workflow_version`. Nothing was
written (for `/apply-pr-review`, nothing after its first step, which may have
reopened the item). Set `default_workflow_version`
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

### A plan revision is refused for a missing checkpoint anchor

`/milestone-plan` or `/apply-plan-review` stopped (or `prepare-ai-review.sh`
exited 1 at the plan stage) naming a checkpoint whose plan section has no
well-formed `<!-- CPn -->`/`<!-- /CPn -->` pair. The
cause is a plan revision that does not delimit every registry checkpoint. The
one fix: put the pair around that checkpoint's section (every checkpoint, `n`
of the shape `CP<digits>[A-Z]?`), then run the same command again. It happens
before review now, instead of at `/approve-review plan` after the reviews,
because the check runs at publish, bind and plan-stage generation. A plan
approved before 2.11.0 without anchors is not affected until its next revision.
Moving back to 2.10.0 loses only these early refusals (nothing new is written):
a plan without anchors is accepted again, and an amendment of it is refused
first at plan approval, after both plan reviews.

### A plan is refused before review because of a list of governing versions

`/milestone-plan` or `/apply-plan-review` stopped (or `prepare-ai-review.sh`
exited 1 at the plan stage) with `PlanGoverningVersionSweepError`, which lists
each flagged passage as `<path>:<line> (<form>): <snippet>`. The cause is a plan
revision under `docs/ai-workflow/` that names a list of governing versions,
which the repository's conformance sweep rejects. The one fix: reword each
flagged passage so it names no list of governing versions (say a feedback-only
item or a two-stage item), then run the same command again. It happens before
review now, instead of at pull-request time when an approved plan can no longer
be corrected, because the check runs at publish, bind and plan-stage generation
(after the anchor check, so a plan without anchors is refused for that cause
first). A plan approved or bound before 2.13.0 is not affected until its next
revision. Moving back to 2.12.0 loses only this early refusal (nothing new is
written).

### Acceptance is refused because an Optional finding has no disposition

`/accept-milestone` or `/satisfy-gate acceptance` stopped with
`UndispositionedFindingsError`, listing each recorded Optional finding (key,
stage, role, round, text) that has no disposition. An `APPROVE` may carry Optional
findings, and since Workflow 2.14.0 each one is recorded when the verdict is
ingested. The one fix: run `python3 scripts/workflow_state.py --finding-dispositions <id>`,
which lists them and prints a skeleton, record a disposition for each in
`docs/ai-workflow/registry/<id>-dispositions.json` (`fixed`; `dropped` with a
`reason`; or `follow-up` with a `link`), save the file, and run the command again.
A follow-up is complete: acceptance does not wait for its fix.
`InvalidFindingDispositionsError` means the file itself has a problem; the message
names each one. The file is not committed on its own; the completion commit stages
it with `docs/milestones/completed/<id>-findings.md`. Findings are recorded from
the first verdict ingested after updating to 2.14.0; an item in flight keeps
earlier findings out of the ledger. Moving back to 2.13.0 removes the refusal; see
the [release history](release-history.md) for what to commit before moving back.

### A plan is refused because its artifact declaration leaves a path unclassified

`/milestone-plan` or `/apply-plan-review` stopped (or `prepare-ai-review.sh`
exited 1 at the plan stage) with `PlanArtifactDeclarationCoverageError`, which
lists each `<checkpoint>: <path>` that a checkpoint's Files paragraph names but the
work item's declaration, `docs/ai-workflow/registry/<id>-artifacts.json`, leaves
unclassified at the plan stage, the implementation stage or both. The one fix: add
each path, or its folder, to `plan_stage` and/or `implementation_stage` of that
file (protected for a deliverable, excluded for repository territory). If the
listed span is not a path (a dotted identifier, a function name, a flag), drop its
backticks or move it out of the Files paragraph. Then run the command again. The
check runs on a new plan revision only; a plan approved or bound before 2.14.0 is
not affected until its next revision. A plan with no Files paragraph, or none that
names a path, gets an advisory and is not refused. Moving back to 2.13.0 loses only
this early refusal.

### A gate policy adopted with a merge commit does not take effect

`verify` (or the `/adopt-gate-policy` report) warns that an adoption reached this
line through a merge commit that does not record it on this line. Older versions of
`GATE_POLICY.json` on this line still count, so the gates can read stricter than the
policy you adopted. Nothing was loosened, and the evaluation is unchanged. The one
fix: merge an adoption with a squash, or run `/adopt-gate-policy` again on a branch
and merge that branch with a squash. A merge commit from `git merge main` into a
feature branch is the usual cause.

### A review verdict is refused as malformed

`/review-plan`, `/review-implementation` or the manual ingest
(`/record-manual-plan-review`, `/record-manual-implementation-review`,
`record-external-result`) refused a verdict as malformed and wrote nothing.
Either a `REVISE` names no Blocking or Important finding, an `APPROVE` lists a
Blocking finding, an `APPROVE` declares `Review scope: changes` (every
`APPROVE` is a full review), or an `APPROVE`'s header states a conflicting or
unrecognised `Review scope` (for example `full.`, or `full` together with
`changes`): it needs exactly one `Review scope: full` line, or none. The one fix: have the reviewer reissue the
verdict, never edit it into a different status. A round with only Optional
findings is an `APPROVE` with those findings under `## Optional findings`;
write `None.` in a section with no finding. A verdict already recorded is
applied as before. Moving back to 2.11.0 loses the refusal.

### A review-round count reads null

`review_round.plan_local`, `plan_external`, `implementation_local` or
`implementation_external` in `next-action` is `null`. The Workflow holds no
count for that item or stage: the item was created before 2.15.0, it is a
promoted legacy item, it is a feedback-only item, the stage records no per-role
rounds, or `review_round_counts` is malformed (`verify` reports the last as a
`state_valid` failure). Nothing is wrong with the item: a count started
mid-history would read low without any sign, so the Workflow never starts one.
Count the rounds yourself, for example from the review verdicts recorded for the
item, and never read `null` as 0.

### A review-round count reads lower than expected

An item was moved back to an earlier release and up again. A verdict ingested
while the repository ran a release before 2.15.0 was not counted, and the
numbers survive and read low afterwards without a sign. For a hard round cap on
an item that was ever moved back, count the rounds yourself.

### A generation record is refused for its trailer set

The record's final paragraph holds more than the `Workflow-*` trailers, usually
a `Co-Authored-By:` line, and the trailer set is checked exactly. Put
`Co-Authored-By:`/`Claude-Session:` lines in an earlier paragraph, separated by
a blank line, and keep only the `Workflow-*` trailers in the last one. While the
refused commit is still the unpublished `HEAD`, rewrite its message in that
layout (same tree); a later recovery cannot supersede it. Once it is published
or built on, ask the repository owner.

### Implementation approval fails with MalformedBundleGenerationRecordCommitError after a move back to 2.14.0

The repository was moved back to 2.14.0 while an item had a commit that changes
`review_round_counts` inside its open implementation-stage provenance interval,
for example a provenance recovery that committed a local `APPROVE`'s pending
ledger and counter in a recovered generation record. 2.14.0's closed field sets
do not name the counter, so it refuses that record even on a clean tree, and
committing the state does not help. Finish the implementation approval under
2.15.0, or keep the repository on 2.15.0 until it has. Move back to 2.14.0 only
when every item's pending state is committed and no non-terminal item has such a
commit.

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

### A sharded conformance job fails, or reports a missing shard

Since 2.16.0 the managed `workflow-conformance` job runs the acceptance suite in
four shards of whole test classes. A failing shard shows as `acceptance N/4` in
the summary and as an `::error` annotation naming the shard, its classes and the
original test ids that failed; the full log of that shard follows the
annotation, unfolded, and every other shard log is in the job log as a collapsed
group (the managed job uploads no artifact). Fix the
named tests as for any acceptance failure. "No complete shard file", "did not
finish (no result)" or "missing: <ids>" means the shard did not report some or
all of its planned tests: it was killed, its runner was lost, or it crashed
before writing its result, so the coverage gate could not count them
(`coverage: expected T, recorded R` with `R < T`). Re-run the job; if it repeats,
read that shard's log in the job log for the crash. "not in the plan" means a
shard recorded a test id the plan did not list, typically a class-level fixture
error (`setUpClass`, `setUpModule`) or a `SkipTest` raised outside a test,
which the runner reports under the class rather than under a planned test.
"executed more than once" means a planned test started twice within its shard
(for example a `run()` override that calls `super().run()` twice); remove the
repeat.
