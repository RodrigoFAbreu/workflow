# W10: Workflow 2.14.0 — every Optional finding gets a disposition at acceptance, an adoption merged with a merge commit is named, and an artifact declaration that leaves a plan's paths unclassified is refused before review (Revision 5)

- **Work item:** `finding-dispositions` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner placed it as row 11
  of `docs/ROADMAP.md` (workflow#34 with the owner's clarification of
  2026-10-16, #37, and #40 added by the Controller lane).
- **Roadmap step:** W10, row 11 of "What's next". This plan makes it the
  current item.
- **Branch:** `milestone/finding-dispositions`
- **Base commit:** `f8eea78` (main after #42: the release source is Workflow
  2.13.0; this repository's own installation is also 2.13.0 with automatic
  gates, default 2.2 and no `GATE_POLICY.json`)
- **Plan revision:** 5. Every checkpoint section carries its
  `<!-- CPn -->`/`<!-- /CPn -->` pair. Section 10 has the revision history.

## 1. Goal

Ship Workflow 2.14.0, a minor release (`feat:`: it adds refusals and a persisted
key), that removes three defects found running 2.12.0 and 2.13.0.

1. **workflow#34 — Optional findings get a disposition.** Since 2.12.0 a round
   with only Optional findings is an `APPROVE`, so those findings live only in
   the gitignored archive and in a `REVIEW_FEEDBACK.md` that the next round
   overwrites. After this release the Workflow records every Optional finding
   at ingest, and acceptance (`/accept-milestone` and `/satisfy-gate acceptance`)
   refuses while any recorded finding has no disposition: **fixed**, **dropped
   with a reason**, or a **follow-up with a link**. A follow-up is a complete
   disposition and acceptance never waits for a fix (the owner: "Accept
   milestone does not need to have all minor findings fixed... from time to time
   we have to do a milestone to fix multiple findings"). The dispositions are
   kept in a committed completed-milestone record.
2. **workflow#37 — an adoption merged with a merge commit.** A
   `/adopt-gate-policy` adoption merged into `main` with a merge commit
   silently does not take effect. `verify`, `/adopt-gate-policy` and
   `GATE_POLICY.md` name the cause and the fix (merge the adoption with a
   squash, or re-adopt on a branch and merge that branch with a squash). The
   evaluation is not changed (D-Adoption).
3. **workflow#40 — an artifact declaration that classifies none of the plan's
   code.** When a plan revision is published, bound or turned into a bundle, the
   declaration is checked against every path the plan's checkpoints name (their
   `**Files:**` paragraphs), at both stages, and a revision that leaves one
   unclassified is refused with one next step, before any review round.

### Hard requirements (invariants)

- **INV-1** The only new persisted data is one work-item key,
  `optional_findings`, and two committed files per item that has findings
  (`docs/ai-workflow/registry/<id>-dispositions.json`, written by the
  author, and `docs/milestones/completed/<id>-findings.md`, generated). No new
  phase, status, configuration key or commit shape (the new key joins the
  closed commit-field sets of the existing commit shapes, D-Ledger). Approvals, gates and who
  may approve are unchanged.
- **INV-2** Recording a finding never fails or changes a verdict's ingest, the
  ledger of a review stage, a phase or an identity: the new key is outside
  `bundle_id` and `review_content_id`, and a failure to parse falls to "no
  findings recorded" (the section reads as written).
- **INV-3** Acceptance never waits for a fix, a review or a person beyond what it
  waits for today; the only new refusal is "a recorded finding has no valid
  disposition".
- **INV-4** The gate-policy evaluation (`effective_policy`, `_introduces_adoption`,
  the floor range) returns exactly what 2.13.0 returns for every history.
- **INV-5** The only new plan refusal is the declaration check, on a new plan
  revision. A bound plan keeps working until its next revision
  (`_plan_early_check_work_item` exempts a `BOUND` binding at a ready phase, only
  with `allow_bound_regeneration`); a revision that was published but not yet
  bound when 2.14.0 is installed is checked at its bind and at its bundle, and is
  refused there if its declaration leaves a named path unclassified.
- **INV-6** This repository's own installation (`.claude/`, `scripts/`, the
  managed `docs/ai-workflow/` documents, `.workflow-manager/`) is never edited.

### Non-goals

- workflow#30 part 2, #31, #39 and the other `review-follow-up` backlog, item C
  (acceptance-matrix sharding), the Controller's work, a new command.
- Verifying a disposition: "fixed" is a recorded claim, not a checked one.
- Recording findings of a feedback-only item (it has no ledger to extend), or of
  the functional review.
- Reconstructing Optional findings of verdicts ingested before 2.14.0.
- Starting a declaration from another item's reviewed declaration (the issue's
  second suggestion; OD-3).

### What is a gate and what is an aid

Said once, so no review round has to chase an edge case a boundary settles:

| Piece | Kind | Declared limit |
|---|---|---|
| The ledger entry for a finding | **Gate input**: acceptance refuses on it | Recognition is the reviewer's text read by D-Parse; a finding written outside `## Optional findings`, a re-raise that changed by even one non-whitespace character (a new key, so one more disposition, never a lost or merged finding) and a verdict never passed to a writer are not matched as a person would (limits a-d of D-Parse) |
| The disposition check at acceptance | **Gate** | Checks presence and shape, never that "fixed" is true |
| The completed-milestone record | Record, generated | Reads the ledger and the dispositions file as they are at acceptance |
| The adoption-merge notice | **Reviewer aid** (a `verify` warning and a preview line) | Names a likely cause, never changes an evaluation |
| The declaration coverage check | **Gate** on a new plan revision | Reads only `**Files:**` paragraphs (limits a-d of D-Coverage); an absent paragraph is an advisory |

## 2. What exists today (facts this plan relies on)

- `workflow_fingerprint._FINDING_ITEM_RE`, `_is_placeholder` and
  `_section_has_finding` (`payload/scripts/workflow_fingerprint.py:4103-4129`)
  decide what a finding is for 2.12.0's shape check
  (`assert_verdict_well_formed`): a list item or `### ` heading under a `## `
  section, with placeholders ("none", "n/a", "no findings", punctuation-only)
  skipped.
- Review stages are recorded by four pure writers in `workflow_state.py`:
  `record_local_plan_review`, `record_manual_plan_review`,
  `record_local_implementation_review`, `record_manual_implementation_review`.
  An `APPROVE` writes the stage ledger (`plan_review_stages`,
  `implementation_review_stages`), which is scoped to one `review_content_id`
  and replaced for new content; a `REVISE` writes no ledger; a `BLOCK` writes
  nothing. None keeps a finding. The manual stage is ingested by
  `ingest_manual_review_verdict` (also the protocol's `record-external-result`),
  inside one `state_transaction`; the local stage by `/review-plan` and
  `/review-implementation`, which call the writers in a `state_transaction`.
- `REVIEW_FEEDBACK.md` is overwritten by the next round and `.ai-review/` is
  gitignored, so a finding of an earlier round survives nowhere.
- Both acceptance paths end in `complete_work_item(state, id, now, repo_root=...)`
  (`/accept-milestone` step 2a; `apply_acceptance_satisfaction` for `/satisfy-gate
  acceptance`). It already refuses on incomplete children, an incomplete own
  registry and an unsatisfied completion obligation. Its callers write the
  archive copy in `docs/milestones/completed/` (step 5 of each command).
- `workflow_gate_policy._introduces_adoption` returns false when another parent
  of a commit holds the new adoption digest; `_range_for_floor` then spans the
  whole first-parent history, so an older all-human `GATE_POLICY.json` is
  observed and the effective policy reads `file_loosening_ignored`. `verify_check`
  then warns by its `file_loosening_ignored` branch and, while the stricter
  setting is unrecorded, its floor-pending branch ("a stricter setting is
  observed but not yet recorded..."); its `gate_lowering` branch fires only for an
  adoption that lowers a field. None of them names the merge.
- A merge commit made by `git merge main` on a feature branch (an update merge)
  and a pull-request merge commit made by `gh pr merge --merge` have the same
  shape: first parent the line being merged into, second parent the line being
  merged in. Nothing in a commit says which one is "the target".
- `generate_artifacts_declarations` emits a template whose `excluded_prefixes`
  name `.claude/commands/`, `scripts/`, `docs/ai-workflow/`, `docs/milestones/`
  and a few more, and whose implementation stage protects the deliverable tree
  of a `process` item under `.claude/commands/` and `scripts/` only. Run against
  this plan's own paths it leaves `payload/`, `tools/`, `fixtures/`,
  `templates/`, `manifest.json` and the user documents unclassified at both
  stages; the previous items edited it by hand. That is #40.
- `assert_plan_checkpoint_anchors` and `assert_plan_governing_version_sweep` are
  the two early checks of a plan revision (`_PLAN_EARLY_CHECK_ERRORS`); they run
  at `/milestone-plan` step 5 (publish) and step 6 (bind), at
  `/apply-plan-review`'s equivalents and in `prepare-ai-review.sh`'s plan-stage
  block (on the pinned plan bytes), with the same exemptions
  (`_plan_early_check_work_item`).
- `classify_path` (plan stage) and `classify_path_implementation_stage` raise
  `UnclassifiedPathError` for a path in no set; the sets come from
  `resolve_plan_stage_metadata` (plan stage) and
  `load_implementation_stage_classification` (implementation stage), both read
  from the working tree's declaration file.
- `manifest.json` carries a `manager` block (2.13.0). The release tooling
  measures `conformance.suites` and checks the block; `posture` must be
  non-empty when a release adds a persisted key (check (d) of the Manager's
  release-metadata contract).

## 3. Design decisions

### D-Parse: what an Optional finding is (OD-1)

`workflow_fingerprint.parse_optional_findings(content) -> list[OptionalFinding]`,
reading the text only. It reuses the shape check's section reader,
`_FINDING_ITEM_RE` and `_is_placeholder`, and adds the item, label and identity
rules below, which count and identify findings, a stricter job than the shape
check's "is there at least one".

1. **Section.** The lines under the heading `## Optional findings`
   (case-insensitive); the next `## ` line ends it.
2. **Item: a top-level entry, never a nested one.** Read the section in order.
   A `### ` heading is an item, and every following line up to the next `### `
   heading or the end of the section (list items included) is its body. List
   lines matched by `_FINDING_ITEM_RE` **before the first heading** (or in a
   section with no heading) are items too, measured by indentation (a tab counts
   as four columns): the first matched line is an item; a later matched line whose
   indentation is greater than the previous item's is **nested** and belongs to
   that item's body; any other matched line (the same or a smaller indentation)
   is a new item. So `- O1: x` followed by `### O2: y` is two findings, and the
   sub-bullets of one finding ("- ...; or" / "- ...; or" under one entry) are one
   finding. An item whose text is a placeholder by `_is_placeholder` is skipped.
   The **body** of an item is every following line up to the next item or the end
   of the section.
3. **Label (display only).** After removing emphasis (`*`, `_`, backtick) from the
   first line, a leading label is read when it matches `LABEL [remains|persists] SEP`:
   `LABEL` is one or more hyphen-separated alphanumeric segments, starting with a
   letter and holding at least one digit (`O1`, `OPT-2`, `EXT-R2-O1`, `EXT6-O2`,
   `LIR-R5-001`), so a round segment is part of the label; `SEP` is `:`, `.`, `)`,
   ` — `, ` – ` or ` - `. These shapes of the reviewers' own files all strip:
   `O3: x`, `OPT-2. x`, `**O1 — Stale test-results metadata.**`, `EXT-R2-O1 — x`,
   `EXT6-O2 — x`, `LIR-R5-001 remains: x`. A word without a digit, such as `Note:`,
   is not a label. The label is used **only for display** (the listing and the
   refusal may show it), never for identity.
4. **Identity text: the whole entry, exactly as written.** The identity text is
   the item's first line as written (after its list marker or `### `), **its label
   included**, followed by its whole body, with only two normalizations: every run
   of whitespace (newlines included, so a different wrapping does not matter) is
   collapsed to one space, and leading and trailing whitespace is trimmed. Nothing
   else is normalized: no lowercasing, no emphasis or underscore removal, no label
   stripping. The **digest** is the sha256 of the identity text; the **key** is
   `F-` plus its first 12 hex characters. **Entries merge, within one verdict or
   across verdicts, only when their identity texts are identical.** The one
   tie-break: two or more identical entries inside one verdict are separate
   findings, the first keyed on its identity text and each later one on its
   identity text followed by ` @` and its ordinal (2, 3, ...), so a later verdict
   raising the same pair again merges each with its counterpart. So `CP1: tests
   miss failures` and `CP2: tests miss failures` are two keys, in one verdict or in
   separate ones; `user_id` and `userid` are two keys; a re-raise identical but for
   whitespace and wrapping, in a later round, is one entry with two references.
   The stored **text** is the whole entry as written (first line, then body lines
   joined by a newline), cut to 1200 characters; the refusal and the listing show
   its first line (at most 240 characters) and the record shows all of it. A
   finding's substance therefore survives in state when `REVIEW_FEEDBACK.md` is
   overwritten.

Declared limits: (a) a finding written under another heading, or an Optional
entry left under Important, is not an Optional finding (as in the shape check);
(b) any re-raise that changed by even one non-whitespace character (another label,
such as `O1` then `EXT-R2-O1`, a reworded line, an edited body, other emphasis or
case) is a new key, and its disposition may say "dropped: same as F-...": the cost
is one more disposition, never a lost or merged finding;
(c) a verdict that no writer received records nothing; (d) two distinct findings
with the same twelve hex characters would merge (about 3e-12 for 40 findings).
The key is for people to copy; the stored digest is the full 64.

### D-Ledger: where the Workflow keeps them (OD-1)

A new key on the work item, `optional_findings`, in `WORKFLOW_STATE.json`:

```
"optional_findings": {
  "F-3a9c0b17d2e4": {
    "digest": "<64 hex>",
    "text": "<the whole entry, at most 1200 characters>",
    "raised": [
      {"stage": "plan"|"implementation", "role": "LOCAL_MODEL_..."|"MANUAL_EXTERNAL_...",
       "round": <int or null>, "review_content_id": "<hex>", "verdict": "APPROVE"|"REVISE",
       "at": "<now>"}
    ]
  }
}
```

Why the state file: it is the one record written in the same
`state_transaction` as the verdict (ingest holds `state_lock` through the write),
it is committed with the item's other state, and it survives the overwritten
`REVIEW_FEEDBACK.md` and the gitignored archive. A file under `.ai-review/`
is neither committed nor atomic with the verdict; a committed file written at
ingest would be a second write with no common transaction. The cost is state
size: up to about 1.5 kilobytes a finding, tens of findings a milestone.

The four writers gain a keyword `verdict_text: str | None = None`. Given it, an
`APPROVE` or `REVISE` merges the verdict's findings into the ledger (a `BLOCK`
stays a no-op, and a call without `verdict_text`, an older caller, records
nothing). The merge is pure and idempotent: a finding already in the ledger
gains one `raised` reference unless an identical `(stage, role, round,
review_content_id, verdict)` reference is present. A **re-raised finding is one
entry with several references**, so it needs one disposition. The manual ingest
passes `verdict_text` itself; `/review-plan` and `/review-implementation` pass
the text they just wrote to `REVIEW_FEEDBACK.md`, and their command files say so.
`validate_state` checks the key's shape when present. Nothing else in a writer
changes (INV-2). A work item with no key is a work item with no recorded
findings.

**The commit-field contracts admit the ledger** (manual plan review, I1). The key
sits uncommitted in the working tree until the item's next commit, exactly as
`gate_evidence` and `reopenings` do, and the existing commit helpers refuse a
state whose item-field diff holds a field outside a closed set:
`REVIEW_STAGE_WRITE_COMMIT_FIELDS` (`commit_pending_applying_review_feedback_entry`:
an implementation `REVISE` carrying an Optional finding would write the state and
then raise `ReviewStageWriteNotCommittableError`), `TECHNICAL_APPROVAL_COMMIT_FIELDS`
(an implementation `APPROVE` leaves the ledger uncommitted until the technical
approval, whose post-commit validation would then reject it) and the two
generation-record sets, `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS` and
`RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS` (a post-fix republication of a round
that recorded findings). CP1 adds `optional_findings` to all four, unconditionally
(not `2.2`-scoped, like `implementation_review_stages` and `gate_evidence`: a
`"1"`/`"2.1"` item never has the key). Scoping is unchanged: the diff is read on
the item's own entry, so another item's `optional_findings` residue is neither
staged nor admitted, and every other check of the four helpers (phase, trailers,
revisions, legal source phases) is untouched. The plan-stage commit paths take the
whole working-tree state and need no change; CP1 audits every other closed
field set in `workflow_state.py` (every `_FIELDS = frozenset`) and records the
audit in its checkpoint notes.

### D-Dispositions: the file and the rules (OD-1, OD-2)

`docs/ai-workflow/registry/<id>-dispositions.json`, authored by the lane (a
person or an agent) before acceptance:

```
{"schema_version": 1, "work_item_id": "<id>",
 "dispositions": {
   "F-3a9c0b17d2e4": {"disposition": "fixed", "note": "optional text"},
   "F-77d10a9be201": {"disposition": "dropped", "reason": "required text"},
   "F-0c4e5f6a7b88": {"disposition": "follow-up", "link": "https://github.com/o/r/issues/12"}
 }}
```

- `fixed`: nothing else is required (`note` is optional).
- `dropped`: a non-empty `reason`.
- `follow-up`: a `link`, either `https://…` or `owner/repo#N`. A follow-up is a
  complete disposition.
- Any other value, a missing field, or a `work_item_id` that is not the item's is
  an `InvalidFindingDispositionsError` naming every problem. A key that matches no
  recorded finding is ignored by the gate and listed in the record.
- The file sits under `docs/ai-workflow/registry/`, which the default template
  excludes at both stages, so writing or editing it moves no approval's identity.
  CP2 tests that classification for the generated template of both item types.

`workflow_state.finding_dispositions_report(repo_root, state, work_item_id)`
returns every recorded finding with its references and disposition (or none);
`python3 scripts/workflow_state.py --finding-dispositions <id>` prints it and a
skeleton `dispositions` object whose entries read `"disposition": "?"` for each
undispositioned finding (invalid until filled in). The `--plan-review-publication-status`
option stays; the two become a required mutually exclusive pair.

### D-Gate: the one refusal, in the one function both paths share (OD-2)

`workflow_state.assert_finding_dispositions_recorded(repo_root, state, work_item_id)`
raises `UndispositionedFindingsError`, listing each recorded finding without a
valid disposition as `<key> (<stage> <role> round <n>): <text>` and one next step:
"record a disposition for each in `docs/ai-workflow/registry/<id>-dispositions.json`
(`fixed`, `dropped` with a `reason`, or `follow-up` with a `link`; `python3
scripts/workflow_state.py --finding-dispositions <id>` lists them and prints a
skeleton), save the file, then run the command again". An item with no key passes.

It is called in `complete_work_item`, after the completion-obligation check (so the
existing refusals keep their order), which both acceptance paths reach, and as an
early pre-flight in `/accept-milestone` step 2a and `/satisfy-gate acceptance`
(clear message before any query or write). `/satisfy-gate acceptance` raises it
inside its transaction, so nothing is written, including the pull-request fact
the same call read (re-run it). **`next-action` and the gate evaluation do not
predict it** (OD-2): the Orchestration Protocol stays 1.4 and an orchestrator sees
the named refusal and the next step. The pre-flight reads the working tree's file,
so a disposition is effective once saved; it is **not** committed on its own, and the
completion commit stages it. (A separate commit pushed to the pull request would
move its head and, under `require_ci`, make `ci_green` wait for a new run.
`pr_fact_current` is unaffected either way: the file is excluded.)

### D-Record: the committed completed-milestone record

`workflow_state.render_finding_dispositions(repo_root, state, work_item_id) ->
str | None` renders `docs/milestones/completed/<id>-findings.md`: one table row
per recorded finding (key, stage and role of each reference, round, text,
disposition, reason or link) and, if any, the dispositions that matched no
finding. It returns `None` when the ledger is empty (no file). Step 5 of
`/accept-milestone` and `/satisfy-gate acceptance` writes it through
`workflow_state.write_finding_dispositions_record(repo_root, state, work_item_id)
-> list[Path]` (the record, written, plus the dispositions file when it exists),
and the completion commit stages exactly the paths it returns. A re-acceptance
overwrites it. The record is a view; the gate reads the ledger and the dispositions
file.

**A remediation child** (`parent_work_item_id` non-null, accepted by `/accept-milestone`
or `/satisfy-gate acceptance`, whose step 4 runs `/accept-milestone` step 2b
unchanged) goes through the two-stage reviews and so has its own ledger. Step 2b
skips steps 3, 5 and 7, which would archive a plan the child does not roll into
the roadmap. The findings record is not part of that archive, so it moves out of
step 5 into a new **step 5a** that applies to every item, child included: 2b is
edited to say "skip steps 3, 5 and 7, but run step 5a", and the pre-flight of step
2a already runs for a child. A child's record is
`docs/milestones/completed/<child-id>-findings.md`, its dispositions file is
`docs/ai-workflow/registry/<child-id>-dispositions.json`, both staged by the
child's completion commit (step 6 applies to a child). The child's findings do not
roll up into its parent's ledger; the parent's acceptance asks only for the
parent's own.

### D-Adoption: name the cause, do not count the merge (OD-4, #37)

Decision: do **not** count a merge whose second parent introduced the adoption.
`_introduces_adoption` and every evaluation stay as they are (INV-4).

Why: a pull-request merge commit and an update merge have the same shape (section
2). On a feature branch `git merge main` makes a commit whose first parent is the
feature line and whose second parent is `main`, holding an adoption the feature
line never introduced; counting "second parent introduced it" would count that as
an introduction on the feature line and bound `_range_for_floor` there, dropping
the feature line's older, stricter file versions from the observed set. That is a
loosening by an update merge, the exact thing the rule at `_introduces_adoption`
exists to prevent. No rule on parent order or on the content of the commit can
tell the two apart, so no rule can be added without a heuristic on the branch
names or on `HEAD`'s position. The squash merge (a single parent) already works.

What ships:

- `workflow_gate_policy.adoption_merge_cause(repo_root, head=None) -> dict | None`:
  walking the first-parent history as `verify_gate_policy_provenance` does, the
  newest commit whose adoption differs from its first parent's; when it has more
  than one parent and `_introduces_adoption` is false for it, `{commit, sha256,
  parents}`; else `None`. `effective_policy` carries it as `adoption_merge`.
- `verify_check` adds a warning only when the cause exists and the effective
  policy is stricter than the adopted policy alone: "the adoption `<sha12>` reached
  this line through merge commit `<sha12>`, which does not record it on this line,
  so older versions of `GATE_POLICY.json` on this line still count and the gates
  can read stricter than adopted; merge an adoption with a squash, or run
  /adopt-gate-policy again on a branch and merge that branch with a squash". (A
  re-adoption of the same policy is not refused, and under a squash it introduces
  the adoption, because its `history` and `adopted_at` differ; on a protected line it
  cannot be done in place.) The preview, the `/adopt-gate-policy` report and
  `GATE_POLICY.md` use the same wording. The status is a warn as before; the
  check never changes the overall status.
- `gate_policy_adoption_preview` carries the same cause as `adoption_merge`, and
  `/adopt-gate-policy` prints it in step 1 and step 3 (the report).
- `GATE_POLICY.md` states the squash requirement where it says an adoption keeps
  verifying after a squash merge.

### D-Coverage: the declaration check (OD-3, #40)

`workflow_state.assert_plan_artifact_declaration_coverage(repo_root,
work_item_id, *, state=None, pin_dir=None, allow_bound_regeneration=False)`,
beside the anchor and sweep checks: same exemptions (an item that is not
two-stage, and with `allow_bound_regeneration` a bound regeneration), same call
sites (`/milestone-plan` publication and bind, `/apply-plan-review`'s, and
`prepare-ai-review.sh`'s plan-stage block), and its error joins
`_PLAN_EARLY_CHECK_ERRORS`.

**Input.** `plan_named_paths(plan_text)` reads, in each well-formed anchor span of
a checkpoint (`parse_checkpoint_anchor_spans`), the **Files paragraph**: the line
starting `**Files:**` (after an optional `- `) through the next blank line.

**The notation: in a Files paragraph, every backtick span is a named path**,
except a span that (i) contains whitespace or any of `* ? [ ] { } < > ( ) …`,
(ii) is a URL, (iii) starts with `/`, `~` or `..` (an absolute path, a home path or
a path outside the repository, such as a sibling read-only repository named for
reference, is never read), or (iv) is a version string (only digits and dots, such
as `2.14.0` or `1.3`). Nothing else decides: no check of the disk, no file-name
grammar. **Reference annotations are stripped first**: a trailing `:N`, `:N-M`,
`#LN` or `#LN-LM` (a line reference such as `docs/gates.md:12`) is removed, and the
path that remains is what is classified and named in the refusal. A trailing `/`
marks a directory. A path is repository-relative, so `Dockerfile`, `Makefile`,
`.env` and `fresh_tool.py` are root-level paths whether or not they exist (a
checkpoint that creates a new root file names it this way, and an undeclared one is
refused, not advised). A backticked span that is not a path (a dotted identifier
such as `json.dumps`, a function name, a flag) is therefore refused unless
declared; write it without backticks or outside the Files paragraph.

**Rule.** Each named path must be classified at the plan stage (by
`classify_path` over the item's plan-stage sets) **and** at the implementation
stage (by `classify_path_implementation_stage` over its sets); protected or
excluded both count, since the declaration's judgment is a reviewed fact and the
check is about the unclassified. A directory is classified when some prefix of the
relevant sets covers it. Sets: the plan-stage sets of `resolve_plan_stage_metadata`
and the implementation-stage sets of `load_implementation_stage_classification`,
both from the working tree's declaration (the source the fingerprint itself reads
at each stage); the plan text from `pin_dir` when given, else the working tree.

**Refusal.** `PlanArtifactDeclarationCoverageError` names the work item, the plan
revision and each `<checkpoint>: <path> (unclassified at the plan stage |
the implementation stage | both stages)`, then `PLAN_DECLARATION_NEXT_STEP`: add
each path, or its directory prefix, to `plan_stage` and/or `implementation_stage`
of `docs/ai-workflow/registry/<id>-artifacts.json` (protected for a deliverable,
excluded for repository territory), **or, when the span is not a path (a dotted
identifier, a function name, a flag), drop its backticks or move it out of the Files paragraph**, then run
the command again. The declaration
may still be edited freely before approval (it moves the digest, which is
intended). The check runs only on a new plan revision, at its publication, bind
or bundle: an already approved or bound plan is not re-checked (INV-5), so items
in flight keep working until they publish a new revision.

**Advisory.** `plan_files_advisory(plan_text, registry)` returns a warning for a
checkpoint that has no Files paragraph or no named path in it ("`CPn` names no
files, so its paths are not checked"), printed beside `plan_size_advisory`. It
never refuses.

Declared limits of this gate: (a) only Files paragraphs are read; (b) a bare name
relying on the preceding path's directory is read as a root-level path (write
every path in full from the repository root; the refusal names the bare name and
says so); (c) a glob, a placeholder, a path in prose and a path outside the repository are
not read; (d) whether a path is protected or excluded rightly is
for the plan reviewer; (e) a backticked span that is not a path (`json.dumps`, a
function name, a flag) is read as a path, because backticks are the path notation
of a Files paragraph; the refusal says so and offers the second remedy.
`/milestone-plan` step 3 and `review-plan.md` state the notation and these limits.

### D-Downgrade: what 2.13.0 loses (OD-5)

2.14.0 adds the work-item key `optional_findings` and two committed files per item
that has findings; no phase, status, configuration key or commit shape (the commit-field sets
admit the key, D-Ledger). After a
move back to 2.13.0: the key stays; `validate_state` and the pure writers ignore
it (CP1 tests that a state holding it validates and that every pure writer
preserves it), **but 2.13.0's commit helpers do not**: their closed commit-field
sets (D-Ledger) do not name `optional_findings`, so while the key is an
*uncommitted* change of the item's entry, `commit_pending_applying_review_feedback_entry`,
the generation-record validation and the technical-approval post-commit validation
reject the item (a field-diff refusal such as `ReviewStageWriteNotCommittableError`).
The supported procedure is therefore: **before moving back, let the item's pending
state be committed under 2.14.0** (the item's next review-stage commit, generation
record or approval commit does it; `git diff HEAD -- docs/ai-workflow/WORKFLOW_STATE.json`
shows no `optional_findings` hunk once it is done); a key already in `HEAD` is
harmless to 2.13.0. The limitation: an item downgraded while its ledger is still
uncommitted is refused by those helpers until the ledger is committed or removed
by hand (an operator edit of the state file, outside the Workflow's supported
commands). Acceptance no longer asks
for dispositions; the dispositions file and the findings record are ordinary
committed documents; verdicts ingested while downgraded are not recorded, so after
a re-upgrade the ledger lacks them and their Optional findings are triaged by hand
at acceptance; the adoption notice and the declaration check are gone. The
manifest `manager` block therefore has a non-empty `posture` stating this, a
`state-key` signal named `optional-findings-ledger` for `optional_findings`, a
`new_work_only` entry (findings are recorded from the first verdict ingested after
the update; an item in flight keeps earlier findings out of its ledger), no gate
default change, and `min_manager_version` `1.13.0`: nothing here needs a Manager
change (no new detector kind, package format or CLI contract).

### D-Protocol: Orchestration Protocol stays 1.4

No snapshot field, row, action, envelope key or classification changes; the new
refusals are command-step refusals, like 2.11.0's and 2.13.0's. `WORKFLOW_RELEASE`
and the tested-releases list gain 2.14.0.

## 4. Open decisions (for the plan reviewer and the user)

| Id | Question | Recommendation |
|---|---|---|
| OD-1 | Where the Workflow keeps Optional findings and how it recognizes them | The state file's `optional_findings`, written by the four existing writers; recognition by D-Parse (the shape check's rules, whole-entry identity, content-keyed). Not a gitignored file (lost) or a second committed file (no common transaction). |
| OD-2 | Whether `next-action` and the gate evaluation predict the refusal | No: the refusal lives in `complete_work_item` and a pre-flight. Predicting it needs a protocol row and a bump; revisit with the Controller. |
| OD-3 | #40: check the plan or seed the declaration from the last accepted item | Check the plan. A copied declaration imports another item's reviewed judgment and goes stale; the check is cheap, gates only what the plan states and is one more early check. |
| OD-4 | #37: count the merge or name the cause | Name the cause (D-Adoption's argument); revisit only if a signal other than parent order appears. |
| OD-5 | The downgrade posture and `min_manager_version` | D-Downgrade; `1.13.0`. |

None of these finalizes a row of `docs/TECHNICAL_DECISIONS.md` (it has no open row
on review data or acceptance).

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Record every Optional finding at ingest (#34, part 1) | - | 4 | 1 |
| CP2 | Dispositions: the acceptance refusal, the listing and the completed-milestone record (#34, part 2) | CP1 | 4 | 1 |
| CP3 | Name the cause of an adoption merged with a merge commit (#37) | - | 3 | 1 |
| CP4 | Refuse a plan whose artifact declaration leaves a named path unclassified (#40) | - | 4 | 1 |
| CP5 | Release 2.14.0: manifest, release constant, release history, downgrade posture | CP1, CP2, CP3, CP4 | 2 | 1 |

Every checkpoint updates the golden command-file hashes
(`_GOLDEN_COMMAND_FILE_SHA256` in `workflow_integration_test.py`) for the
command files it edits. The installation under `scripts/`, `.claude/` and
`docs/ai-workflow/`'s managed files is never edited.

**Conformance at a checkpoint** (the W4 to W9 procedure, as
`docs/ai-workflow/REVIEW_LOOP_FIXES_PLAN.md` states it). `manifest.json` still
carries 2.13.0's digests, which CP5 refreshes, and stock `release.py
stage-conformance` calls `package.stage_conformance`, which verifies the manifest
before it builds the fixture and refuses changed payload bytes (`digest mismatch`).
CP1 to CP4 therefore stage a scratch release from the checkpoint's own commit
(`package.stage` with the zlib-ng virtual environment's Python, into an empty
directory outside the repository and outside `/tmp`), rewrite `sha256` and `size`
of every `artifacts` and `templates` record of the **scratch** `manifest.json` from
the bytes on disk with a throw-away script kept outside the repository, then run
`package.stage_conformance` and the nine payload suites in that fixture (`TMPDIR`
outside `/tmp`); the `tools/release` tests run in the same virtual environment. The
committed `manifest.json` is never touched before CP5. CP5 runs the stock
`release.py stage-conformance --commit <CP5 commit> --out "$(mktemp -d)/fixture"`
against its committed manifest, and the scratch digests must equal CP5's committed
ones for the same tree.

<!-- CP1 -->
### CP1 — Record every Optional finding at ingest

**Files:** `payload/scripts/workflow_fingerprint.py`,
`payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`,
`payload/scripts/workflow_fingerprint_test.py`,
`payload/scripts/workflow_integration_test.py` (golden command-file hashes),
`payload/.claude/commands/review-plan.md`,
`payload/.claude/commands/review-implementation.md`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`.

- `workflow_fingerprint`: `OptionalFinding`, `parse_optional_findings` (D-Parse),
  reusing `_FINDING_ITEM_RE`, `_is_placeholder` and the section reader.
- `workflow_state`: `merge_optional_findings(work_item, findings, ref)` (pure,
  idempotent), the `verdict_text` keyword on the four writers, `_validate_optional_findings`
  called from the work-item validation, and the manual ingest passing
  `verdict_text`. The two local command files pass the text they just wrote.
- `workflow_state`: `optional_findings` added to `REVIEW_STAGE_WRITE_COMMIT_FIELDS`,
  `TECHNICAL_APPROVAL_COMMIT_FIELDS`, `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS` and
  `RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS` (D-Ledger), with the audit of the
  file's other closed field sets noted in the checkpoint's report.
- `REVIEW_PROTOCOL.md`: a short "Optional findings are recorded" paragraph and the
  declared limits (a)-(d) of D-Parse.

**Tests:** unit — parsing: bullets, numbered items, `###` headings, placeholders
(`none`, `n/a`, `No findings`, a punctuation-only entry, each as `_is_placeholder` decides), `**O1:** x` and `O2: x` two keys (nothing but
whitespace is normalized), an absent section, a
case-different heading, a section ended by the next `## `. Item and identity
rules, on shapes copied from real reviewers' files: sub-bullets under one entry
("- ...; or" twice) are one finding, not three; items under `### ` headings are the
headings; a nested item at greater indentation is body, a later item at the same or
a smaller indentation is a new one; `### O1` and `- **O2:**` with the text on the
next line key on the label line and the body, and the same label with different
text in two rounds is two keys; two label-only items with the same label and no
body in one verdict are two keys (the ordinal tie-break); `EXT-R2-O1 — x` and
`EXT-R3-O1 — x` are two keys, as are `LIR-R5-001 remains: x` and `LIR-R6-001
remains: x`, `**O1 — Title.**` and `O1. Title.`, and `EXT6-O2 — x` and `x`, while
the label parse still reads `EXT-R2-O1`, `LIR-R5-001` and `O1` for display and
`Note: x` has no label; a differently worded re-raise is a new key (limit b). Writers — an
`APPROVE` and a `REVISE` record, a `BLOCK` and a call without `verdict_text`
record nothing; the same finding in two rounds and in the local and the manual
stage is one entry with the references; the same verdict applied twice adds
nothing; the stage ledgers, phase, `plan_review_binding` and
`review_content_id` are byte-identical to a call without `verdict_text`. Ingest —
`ingest_manual_review_verdict` records at both stages inside the one transaction,
and a refused ingest (malformed verdict, stale content, wrong phase) records
nothing. Identity and item rules added by review — `O1: Improve tests.` and `O2:
Improve tests.` with different bodies are two keys and with the same body are still
two, and two byte-identical entries in one verdict are two (the ordinal
tie-break); `CP1: tests miss failures` and `CP2: tests miss failures` in separate
verdicts are two keys; findings about `user_id` and `userid` are two keys; a
re-raise with the same words and body under a new label is a new key, and so are
the same words with a changed body; a byte-identical re-raise (whitespace and
wrapping changes only) in a later round merges into one entry with two
references; the
stored text holds the whole entry and is cut at 1200 characters; a section holding
`- O1: Keep a local cache.` followed by `### O2: Document its lifetime.` records
both, and a list under a heading is that heading's body. Commit contracts —
finding-bearing local and manual `APPROVE` and `REVISE` writes at both stages go
through the actual commit helpers and validators in disposable repositories:
`commit_pending_applying_review_feedback_entry` after an implementation `REVISE`
with an Optional finding, the technical-approval commit and its post-commit
validation after an `APPROVE` that recorded one, and the ordinary and the recovered
generation record (the post-fix republication) with the ledger pending; each is
accepted, another item's pending `optional_findings` residue is still neither
staged nor admitted, and a stray field outside the sets is still refused. A test
asserts the four sets name the key and that D-Downgrade's `git diff HEAD` check
sees no hunk once the item's pending state is committed. State — a state holding the key validates; one with a malformed entry
is refused; a state with the key survives each writer unchanged for items the
writer does not touch. Command files — both name `verdict_text`. The golden
hashes are refreshed.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Dispositions: the acceptance refusal, the listing and the record

**Files:** `payload/scripts/workflow_state.py`,
`payload/scripts/workflow_state_test.py`,
`payload/scripts/workflow_acceptance_matrix_test.py`,
`payload/scripts/workflow_integration_test.py` (golden command-file hashes),
`payload/.claude/commands/accept-milestone.md`,
`payload/.claude/commands/satisfy-gate.md`,
`payload/docs/ai-workflow/MILESTONE_WORKFLOW.md`,
`payload/docs/ai-workflow/GATE_POLICY.md`.

- `workflow_state`: `UndispositionedFindingsError`, `InvalidFindingDispositionsError`,
  `read_finding_dispositions`, `finding_dispositions_report`,
  `assert_finding_dispositions_recorded` (D-Gate), the call in
  `complete_work_item` after the completion-obligation check,
  `render_finding_dispositions` and `write_finding_dispositions_record` (D-Record),
  and the `--finding-dispositions` option (D-Dispositions).
- `accept-milestone.md` and `satisfy-gate.md`: the pre-flight in step 2a and in
  the acceptance stage, the two errors with their next step, and a new step 5a
  (applies to every item, a remediation child included; step 2b is edited to
  "skip steps 3, 5 and 7, but run step 5a") writing the record through
  `write_finding_dispositions_record` and staging the paths it returns with the
  completion commit.
- `MILESTONE_WORKFLOW.md`: the `AWAITING_USER_ACCEPTANCE` exit condition gains
  "every recorded Optional finding has a disposition; a follow-up is complete".
  `GATE_POLICY.md`: the acceptance gate section says the disposition check is
  not a policy requirement and applies under every policy.

**Tests:** unit — no key passes; one finding without an entry refuses naming
key, stage, role, round and text; each of `fixed`, `dropped` with a reason and
`follow-up` with a link satisfies; `dropped` without a reason, `follow-up`
without a link or with a bad link, an unknown disposition, the skeleton `?`,
a wrong `work_item_id` and a non-JSON file refuse with every problem named; an
unmatched key is ignored by the gate and listed in the record; a finding raised
in three rounds needs one entry. Acceptance — `complete_work_item` refuses and
returns no state; both `/accept-milestone`'s and `satisfy_acceptance_gate`'s
paths refuse, the second writing nothing; with a follow-up disposition both
complete although nothing was fixed; the existing refusals keep their order;
the dispositions file is classified (excluded) at both stages by the generated
template for a `process` and a `product` item. Record — deterministic text, the
`None` case, an overwrite on re-acceptance; `write_finding_dispositions_record`
returns the record and the dispositions file (only the record when no file exists)
and nothing for an empty ledger. Remediation child — accepting a
`<parent>-remediation-<n>` child with recorded findings by each path refuses with
none, completes with a disposition, writes `<child-id>-findings.md` and returns the
record and the child's dispositions file for staging, while the parent's ledger and
record are untouched; `accept-milestone.md` step 2b names step 5a and
`satisfy-gate.md` step 4 cites it. The listing option prints the skeleton
and the `--plan-review-publication-status` option still works. Command files name
the pre-flight and step 5. The golden hashes are refreshed.
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Name the cause of an adoption merged with a merge commit

**Files:** `payload/scripts/workflow_gate_policy.py`,
`payload/scripts/workflow_gate_policy_test.py`,
`payload/scripts/workflow_state.py` (the preview),
`payload/.claude/commands/adopt-gate-policy.md`,
`payload/docs/ai-workflow/GATE_POLICY.md`.

- `workflow_gate_policy`: `adoption_merge_cause` (D-Adoption), the
  `adoption_merge` key of `effective_policy`, the `verify_check` warning.
- `workflow_state.gate_policy_adoption_preview`: the `adoption_merge` field;
  `adopt-gate-policy.md` prints it in step 1 and step 3.
- `GATE_POLICY.md`: the squash requirement and the cause, where the document says an
  adoption keeps verifying after a squash merge and in the two-branches paragraph.

**Tests:** disposable repositories built by the suite's helpers. (1) The issue's
case (the `verify_check` assertion compares against 2.13.0's actual
`file_loosening_ignored` and floor-pending warning text, which the new warning is added
to, not replaces): an adoption on a branch merged with a merge commit into a line whose
history holds an older all-human `GATE_POLICY.json`: `effective_policy` reports
`file_loosening_ignored` exactly as 2.13.0 does (the assertion compares the whole
report apart from the new key against the values 2.13.0 gives), `adoption_merge`
names the merge, `verify_check` warns with the cause and the fix. (2) The same
branch squash-merged: `source` is `adopted`, no `adoption_merge`, no warning.
(3) An update merge on a feature branch (`git merge main`, `main` holding an
adoption): every field of `effective_policy` is identical to 2.13.0's, and the
notice appears only if the effective policy is stricter than the adopted one.
The fix text names a branch merged with a squash, in the `verify` message, the
preview and `GATE_POLICY.md`.
(4) No adoption, one introduced on the line, and an adoption older than a later
non-adoption merge: `adoption_merge` is `None`. (5) The preview carries the field
and the command text names it. The existing provenance tests pass unchanged.
<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Refuse a plan whose artifact declaration leaves a named path unclassified

**Files:** `payload/scripts/workflow_state.py`,
`payload/scripts/prepare-ai-review.sh`,
`payload/scripts/workflow_state_test.py`,
`payload/scripts/workflow_fingerprint_generalization_test.py`,
`payload/scripts/workflow_integration_test.py` (golden command-file hashes),
`payload/.claude/commands/milestone-plan.md`,
`payload/.claude/commands/apply-plan-review.md`,
`payload/.claude/commands/review-plan.md`,
`payload/docs/ai-workflow/PLAN_REVIEW_WORKFLOW.md`.

- `workflow_state`: `PlanArtifactDeclarationCoverageError`,
  `PLAN_DECLARATION_NEXT_STEP`, `plan_named_paths` (the backtick notation and
  annotation stripping per D-Coverage),
  `assert_plan_artifact_declaration_coverage`, `plan_files_advisory`, and the error
  added to `_PLAN_EARLY_CHECK_ERRORS` (D-Coverage).
- `prepare-ai-review.sh`: the existing early-check Python block also calls the
  new check, on the pinned plan bytes; a refusal leaves `current/`, the archive and the
  pin untouched and writes no `REJECTED` marker, like the anchor and sweep refusals.
- The command files: `milestone-plan.md` tells the author to give every
  checkpoint a `**Files:**` paragraph naming each changed path and states the
  notation (every backtick span there is a path, apart from the four exceptions;
  a non-path is written without backticks), names the new
  call after the sweep call at the publication point and the bind, and prints the
  advisory; `apply-plan-review.md` has the same call; `review-plan.md` says
  the gate reads only Files paragraphs and states the notation.
  `PLAN_REVIEW_WORKFLOW.md`: one paragraph
  beside the anchor and sweep paragraphs.

**Tests:** unit — `plan_named_paths` over: a Files paragraph with paths, a
directory, an existing root file, **new** root files (`fresh_tool.py`, `Dockerfile`,
`Makefile` and `.env`, none of which exists: each is a named path), a line-annotated
reference (`docs/gates.md:12`, `docs/gates.md:12-30`, `docs/gates.md#L12`, which
classify as `docs/gates.md` and are named without the annotation), a **version
string** (`2.9.1`, `2.14.0`, `1.3`, as in `` `manifest.json` (version `2.14.0`) ``:
ignored, the neighbouring `manifest.json` is read), a **backticked identifier**
(`json.dumps`, a function name, a flag: each refused when undeclared, with the
non-path remedy in the message), a glob, a
placeholder, a URL, an absolute path, a `~/` path and a `../` path
(`~/Workspace/repflow-android/...`, `/tmp/x/`, `../other-repo/file`, none read), a path in prose outside any Files paragraph, a paragraph in
a second span of the same checkpoint, and a plan with no Files paragraph.
The check — `Dockerfile`, `Makefile` and `.env`, each named beside a classified
path in an otherwise covered plan, are refused before any publication write (the
publish, the bind and the generator leave `WORKFLOW_STATE.json`, `current/` and the
pin byte-identical); a declaration that classifies everything passes; one that leaves a
path unclassified at the plan stage only, at the implementation stage only and at
both is refused with the right wording and the next step, naming the checkpoint;
protected and excluded both satisfy; a directory covered by a prefix passes and
one covered only by an exact path inside it is refused; the exemptions (not
two-stage, a bound regeneration); the plan read through `pin_dir` while the
declaration comes from the working tree. The generated template for this
plan's own paths is refused, and the declaration of this item passes (the plan is
its own test case). Generator — `prepare-ai-review.sh` exits 1 with the error and
leaves `current/`, the archive and `.pin` untouched. Command files name the call
and the advisory. The golden hashes are refreshed.
<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Release 2.14.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`
(WORKFLOW_RELEASE), `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (tested releases and the
envelope example), `docs/release-history.md`, `docs/common-problems.md`,
`docs/gates.md`, `docs/glossary.md`, `tools/release/manager-releases.json`.

- `manifest.json` 2.14.0 with every digest and size refreshed and the rationale text
  updated on the changed records; `counts` unchanged (no file is added or
  removed). The `manager` block: `min_manager_version` `1.13.0`, a non-empty
  `posture` (D-Downgrade) with the `optional-findings-ledger` `state-key`
  signal, the `new_work_only` entry, an empty `gate_default_change`, and
  `conformance.suites` computed by `release.py manager-block --release-dir <scratch
  directory> --write` from a staging of CP5's own content, in one commit, in the
  order the 2.13.0 release used: make every other edit and refresh digests, stage to
  a scratch directory outside the repository, write `suites`, make the one CP5
  commit. No hand-written count, second commit or amend. `check-manager-block
  --commit HEAD` then agrees.
- `WORKFLOW_RELEASE = "2.14.0"`; the release-version assertions; the protocol stays
  1.4 and says so in the tested-releases note.
- `docs/release-history.md`: a 2.14.0 row with D-Downgrade's paragraph, the closed
  issues (workflow#34, #37, #40) and what stays open (#30 part 2, #31, #39).
  `docs/common-problems.md`: "Acceptance is refused because an Optional finding has
  no disposition", "A plan is refused because its artifact declaration leaves a
  path unclassified" and "A gate policy adopted with a merge commit does not take
  effect". `docs/gates.md` and `docs/glossary.md`: the acceptance gate's
  disposition requirement and the word "disposition". Documents whose header
  names 2.13.0 are re-checked and bumped as `tools/docs/check_docs.py` requires.
- `docs/ROADMAP.md` is marked Done at acceptance, not in this checkpoint.

**Verification:** the nine suites pass in a stock `release.py stage-conformance`
fixture; `release.py build` of the commit succeeds; `check-manager-block` is clean;
the `update-fixture` step passes from the 2.13.0 bootstrap through the 1.13.0
update; `tools/docs/check_docs.py` is clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng virtual environment.
<!-- /CP5 -->

## 6. Tests and verification summary

Each checkpoint's tests are listed in its section. Every checkpoint runs the nine
payload suites from a staged fixture of its own commit (CP1 to CP4 through the
scratch-manifest procedure of section 5, so a stale committed digest cannot refuse
the staging) and the `tools/release` tests; CP5 adds the release steps above. Command-file edits refresh the golden
hashes in `workflow_integration_test.py`.

## 7. Risks

- **A verdict that never reaches a writer records nothing.** The two local
  commands are prose; a run that forgets `verdict_text` leaves a gap the gate cannot
  see. Mitigation: both files name it, a test asserts they do, and the ledger is
  written by the same call that records the stage, so the usual path cannot skip it.
- **Changed re-raises.** A finding re-raised with any non-whitespace change (label,
  wording, body) is two keys.
  Mitigation: a disposition may say "dropped: same as F-…"; limit (b) is declared.
- **State growth.** Up to about 1.5 kilobytes a finding (the whole stored entry, D-Ledger). Accepted.
- **Declared-only coverage (#40).** A plan with no Files paragraph is only
  advised. Mitigation: the command text asks for Files paragraphs; the plan
  reviewer is told what the gate does not read.
- **The adoption notice can be wrong about the cause.** It says "can read stricter",
  and only when the effective policy is stricter than the adopted one.
- **This repository runs 2.13.0.** The new checks do not run on this plan; the
  declaration was checked by hand against both classifiers (section 9), and CP4
  adds the plan as a test case.

## 8. Requirements

| Id | Requirement | Checkpoints |
|---|---|---|
| R1 | Every Optional finding of every recorded verdict (local and manual, plan and implementation stages, `APPROVE` or `REVISE`) of a two-stage item is recorded in the item's state in the verdict's own transaction, keyed by content so a re-raised finding is one entry; no stage ledger, phase or identity changes | CP1, CP5 |
| R2 | Acceptance, by `/accept-milestone` and by `/satisfy-gate acceptance`, refuses while a recorded finding lacks a valid disposition (fixed, dropped with a reason, or a follow-up with a link); a follow-up is complete and acceptance never waits for a fix; the dispositions are in a committed completed-milestone record | CP2, CP5 |
| R3 | `verify`, `/adopt-gate-policy` and `GATE_POLICY.md` name the cause of an adoption merged with a merge commit and the fix; the evaluation is unchanged | CP3, CP5 |
| R4 | A plan revision whose declaration leaves a path named in a Files paragraph unclassified at either stage is refused when published, bound or bundled, with one next step; an absent paragraph is an advisory | CP4, CP5 |
| R5 | Release 2.14.0: manifest and `manager` block, release constant, release history, downgrade posture and documentation; the protocol stays 1.4 | CP5 |

## 9. Artifact classification

`docs/ai-workflow/registry/finding-dispositions-artifacts.json`: the generated
template does not classify `payload/`, `tools/`, `fixtures/`, `templates/`,
`manifest.json` or the user documents (that is #40), so it is declared as the
previous release-source items did. At the plan stage the plan
(`docs/ai-workflow/FINDING_DISPOSITIONS_PLAN.md`), the registry and the mapping are
protected; `payload/`, `fixtures/`, `templates/`, `tools/`, `manifest.json`,
`docs/release-history.md`, `docs/common-problems.md`, `docs/RELEASING.md`,
`docs/gates.md`, `docs/glossary.md`, `docs/ROADMAP.md`, `docs/milestones/` and
`.github/` are excluded (implementation deliverables or repository territory).
At the implementation stage `payload/`, `fixtures/`, `templates/`, `tools/`,
`manifest.json`, `docs/release-history.md`, `docs/common-problems.md`,
`docs/RELEASING.md`, `docs/gates.md` and `docs/glossary.md` are protected, with the
declaration itself; `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`,
`docs/milestones/` and `docs/ai-workflow/` (which holds the dispositions file and
this plan's siblings) are excluded. Every path section 5 names is classified at
both stages, including this plan file; the check in CP4 runs this against the
declaration as its own test.

## 10. Revision history

| Rev | Change |
|---|---|
| 1 | First plan for row 11. |
| 2 | Local plan review round 1 (`REVISE`, no blocking finding). D-Parse: an item is a top-level entry (nested list items are body), the label grammar is pinned (a round segment is part of the label; ` — `, `remains:`), a label-only first line keys on the first body line, else on position; limits (b) and (e) and section 1's table say what stays a new key. D-Record, CP2: a remediation child's findings record moves to a new step 5a that step 2b does not skip; `write_finding_dispositions_record` returns the paths to stage; no roll-up to the parent. D-Gate: save the file, no separate commit. Section 2, D-Adoption, CP3: the actual 2.13.0 `verify` warnings, and the fix is a squash of a branch. D-Coverage, CP4: absolute, `~` and `..` spans are not read. INV-5: names the published-but-unbound case. Tests added for each. No finding rejected. |
| 3 | Manual external plan review round 1 (`REVISE`, five Important findings, none rejected). I1: D-Ledger and CP1 add `optional_findings` to the four closed commit-field sets (review-stage write, technical approval, ordinary and recovered generation record) with item scoping unchanged and an audit of the others; D-Downgrade corrects "ignored" (2.13.0's commit helpers reject uncommitted residue), states the procedure (commit the pending state before moving back) and the limitation; CP1 tests the actual commit helpers and validators. I2: D-Parse identity is the whole entry, same-identity entries within a verdict are never merged (label and ordinal tie-break), the stored text is the whole entry, limit (e) removed. I3: list entries before the first heading are items, lists under a heading are its body. I4: D-Coverage reads a bare file name (existing root file or ending in an extension) as a root-level path and strips line annotations (`:N`, `:N-M`, `#LN`) before classifying; CP4 tests both. I5: section 5 prescribes the scratch-manifest digest refresh before CP1 to CP4 stage a fixture. |
| 4 | Local plan review round 3 (`REVISE`, one Important, two Optional; none rejected). I1: D-Coverage's bare-name extension must start with a letter, so a version string (`2.9.1`, `1.3`) is not a file name; a dotted identifier still matches and is declared limit (e), with a second remedy in `PLAN_DECLARATION_NEXT_STEP`; CP4 tests a version string and a dotted identifier. O1: section 7's state-growth figure aligned with D-Ledger. O2: limit (b) states the tie-break exception. |
| 5 | Manual external plan review round 2 (`REVISE`, two Important, one Optional; none rejected). Each class is closed with one exact rule instead of another heuristic. I1: D-Parse identity is the whole entry as written, its label included, with only whitespace collapsed and trimmed (no lowercasing, emphasis, underscore or label removal); entries merge, within or across verdicts, only on identical text; the ordinal tie-break remains only for identical entries inside one verdict; the label parse is display-only; the "broad grammar made harmless" text and the label-only/position case are removed; limit (b) is now the whole story (any non-whitespace change is a new key, one more disposition, never a lost or merged finding). CP1 tests `CP1:`/`CP2:` in separate verdicts, `user_id`/`userid`, and a whitespace-only re-raise merging into one entry with two references; the old "label stripped, keys shared" tests are inverted. I2: D-Coverage drops the existing-root-file and extension heuristics: in a Files paragraph every backtick span is a named path except (i) whitespace or glob/placeholder characters, (ii) a URL, (iii) a `/`, `~` or `..` start, (iv) a version string; annotations are stripped first and a trailing `/` marks a directory, so `Dockerfile`, `Makefile`, `.env` are paths. A backticked non-path is refused with the second remedy; limit (e) replaced; the notation is stated in D-Coverage and in `milestone-plan.md`/`review-plan.md`; already approved or bound plans are not re-checked (INV-5). CP4 tests `Dockerfile`, `Makefile`, `.env` beside a classified path refused before any publication write, a backticked identifier refused with the remedy, a version string ignored. This plan's own Files paragraphs comply: CP5's backticked `WORKFLOW_RELEASE` lost its backticks; all 39 named paths of CP1 to CP5 classify under both classifiers, none ignored. O1: line 13's revision corrected. |
