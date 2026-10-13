# W7: Workflow 2.11.0 — check checkpoint anchors before any plan review, and write them from the start (Revision 4)

- **Work item:** `checkpoint-anchors-early` (`process`, governing version `2.2`)
- **Issue:** RodrigoFAbreu/workflow#23 (owner: high priority, both scope parts,
  2026-10-12)
- **Roadmap step:** W7, a new row 8 in `docs/ROADMAP.md`'s "What's next"
  table, right after W5 (row 7, Workflow 2.10.0). This plan makes it the
  current item.
- **Branch:** `milestone/checkpoint-anchors-early`
- **Base commit:** `a5da36c` (main after W5: the release source is Workflow
  2.10.0; this repository's own installation is 2.9.2 with automatic gates,
  default "2.2" and no `GATE_POLICY.json`)
- **Plan revision:** 4 (revisions 1 to 3 were each reviewed, `REVISE`; section 11).
  Every checkpoint section below carries its `<!-- CPn -->`/`<!-- /CPn -->`
  pair, as from revision 1.

## 1. Goal

Ship Workflow 2.11.0, a minor release (`feat:` title: it changes behavior for
new plan revisions only), that stops plan amendments from costing review
rounds and revalidation they do not need. Two parts, both in scope:

1. **Check anchors early.** Today a plan revision whose checkpoints lack
   `<!-- CPn -->`/`<!-- /CPn -->` pairs is refused only at plan approval
   (`apply_plan_approval`, open amendment only), after both plan-review
   stages have been spent on it. On workflow-controller C6 (2026-10-12) that
   cost a withdrawal, a new revision and two more review rounds. From 2.11.0
   the same check runs when the revision is published, when it is bound, and
   when its plan-stage bundle is generated, so the refusal comes before any
   review round.
2. **Write anchors from the start.** `/milestone-plan` tells the author to
   put an anchor pair around every checkpoint section in every plan revision,
   and the same early check requires them for every new plan revision, not
   only an amending one. A plan approved without anchors makes its first
   amendment fall back to "every shared checkpoint changed" (C6: CP1 to CP5
   re-checked when only CP6 was new); a plan written with anchors from
   revision 1 never does.

**The one rule.** A plan revision of a two-stage work item (governing "2.1"
or "2.2") is reviewable only when `validate_post_anchor_coverage` accepts its
plan document against its registry. One implementation decides it: the
existing validator, called by one new wrapper,
`assert_plan_checkpoint_anchors`, from every place that makes a plan revision
reviewable. The approval-time call inside `apply_plan_approval` stays as it
is and stays the authority for an amendment.

### Hard requirements (invariants)

- **INV-1, one rule, one implementation.** No second anchor grammar, parser
  or coverage rule. The wrapper calls `validate_post_anchor_coverage` and
  raises the same three error classes it raises today.
- **INV-2, before any review.** A plan revision without full anchor coverage
  never reaches `AWAITING_LOCAL_PLAN_REVIEW`: the generator refuses before
  promoting a bundle, and the commands check before publishing and before
  binding. A refusal leaves the item at its non-ready plan-stage phase
  (`PLANNING`, `REVISING_PLAN` or `AMENDING_PLAN`), recoverable by editing
  the plan and running the command again.
- **INV-3, approval unchanged.** `apply_plan_approval`, its errors and their
  messages are unchanged (one behavior-preserving extraction, CP1).
- **INV-4, in-flight work unchanged until its next revision.** An approved
  plan without anchors keeps driving implementation, implementation reviews,
  technical approval, functional review, acceptance and pull-request
  reopening exactly as in 2.10.0; none of them reads plan anchors. A bound
  plan review in progress at the update is not re-checked, including when
  its bundle is regenerated unchanged (status row 4b, a wrapper-only
  regeneration, `/prepare-review plan <id>`). Only the next plan revision of
  such an item needs anchors.
- **INV-5, version "1" unchanged.** A "1" item's plan stage is not checked
  (the `/milestone-plan` "1" branch stays inert, pinned by its golden-output
  test).
- **INV-6, nothing new persisted.** No new state field, value, record,
  configuration key or commit shape (D-Downgrade).
- **INV-7, protocol unchanged.** Orchestration Protocol stays 1.3: no row,
  reason code, action or check is added (D-Protocol).

### Non-goals

- Changing reconciliation (`reconcile_checkpoints_after_amendment`), its
  zero-anchor default, or the approval-time check (OD-3 explains why the
  heading-section fallback is out).
- Adding anchors to, or otherwise touching, any already-approved plan of any
  repository.
- Checking anchors for version "1" items.
- Editing this repository's installation (`scripts/`, `.claude/`,
  `docs/ai-workflow/`'s managed files, the managed blocks). It stays Workflow
  2.9.2 and `workflow-manager verify .` stays clean.
- Publishing, pushing, pinning in `workflow-manager`, or changing the
  Controller.

## 2. What exists today (facts this plan relies on)

Read in the release source (`payload/`) at `a5da36c`.

- **The anchor grammar and validator** (`payload/scripts/workflow_state.py`,
  D-Plan-Amendment-4, 2.4.0; widened in 2.5.1):
  `_CHECKPOINT_ANCHOR_RE` (`<!--\s*(/?)CP(\d+[A-Z]?)\s*-->`),
  `checkpoint_id_supports_anchor` (`^CP\d+[A-Z]?\Z`),
  `parse_checkpoint_anchor_spans(text, strict=...)` (closed, non-nesting,
  per-id balanced pairs; any number of disjoint pairs per id), and
  `validate_post_anchor_coverage(post_plan_text, post_registry)`, pure, which
  raises `AmendmentAnchorMalformedError` (a malformed tag anywhere, strict
  parse), `AmendmentCheckpointIdShapeError` (a registry id no anchor can
  match) or `AmendmentAnchorCoverageError` (a registry id with no well-formed
  pair). A registry with zero checkpoints passes vacuously.
- **Its only caller** is `apply_plan_approval`, and only for an open
  amendment (`amendment_history[-1].resolved_at_plan_revision is None`),
  after two shape checks on `post_registry` that raise
  `AmendmentPostRegistryMalformedError` (no `checkpoints` key; an entry with
  no `id`). `apply_plan_approval` runs from `/approve-review plan` step 4c
  and `/satisfy-gate plan`, which read `post_plan_text`/`post_registry` from
  the working tree.
- **The zero-anchor default.** `reconcile_checkpoints_after_amendment` hashes
  each shared checkpoint's anchor spans on both sides
  (`checkpoint_content_hash`; the pre side non-strict, `None` for an id with
  no well-formed span) and treats `pre_hash is None` as "changed", so a
  pre-amendment plan without anchors demotes every shared `COMPLETE`
  checkpoint to `NEEDS_REVALIDATION`. `pre_plan_text` is the plan at the
  pre-amendment approval commit.
- **`/request-plan-amendment`** already refuses, before superseding
  anything, a current registry holding an id that no anchor can match
  (`AmendmentCheckpointIdShapeError`), and its text and
  `MILESTONE_WORKFLOW.md` tell the author to add anchors "while drafting",
  naming only the approval-time refusal.
- **Publishing and binding are pure state functions.**
  `publish_plan_revision` (mirror-only for a two-stage item, writes the
  `PUBLISHED` record) and `bind_plan_review_bundle` (the sole writer of
  `AWAITING_LOCAL_PLAN_REVIEW`) take no `repo_root`; the commands compute the
  fresh id and call `verify_plan_review_bundle(repo_root, id)` around them.
  `verify_plan_review_bundle` is also called by
  `plan_review_publication_status` for ready and non-ready rows, so a check
  placed inside it would re-judge a review already bound before the update.
- **Plan-stage generation** (`payload/scripts/prepare-ai-review.sh`, stage
  `plan`) runs a Python preflight (base commit and revision mirror), then
  `workflow_fingerprint.py --derive-plan-stage-document`, which captures a
  private pin of every plan-stage protected path (the plan document, the
  registry and the mapping among them) into
  `.ai-review/<id>/.pin.staging-<token>/` and derives `PLAN.md` from it. The
  bundle, `review_content_id` and `PLAN.md` all come from the pinned bytes.
  Any failure exits through the `cleanup` trap, which removes the staging
  directory and the staging pin and leaves the previous `current/`, archive
  and `.pin` untouched, with no `REJECTED` marker. `workflow_fingerprint`
  does not import `workflow_state`.
- **The commands.** `/milestone-plan`'s publication point (between its steps
  5 and 6) publishes; its step 6 generates, then verifies and binds.
  `/apply-plan-review` step 5 publishes and generates; its step 7' verifies
  and binds. Both name the explicit-id re-run after a generator failure.
  Neither says anything about anchors; `/milestone-plan` step 3 does not
  mention them at all.
- **The protocol.** Row 7 (`PLANNING`/`AMENDING_PLAN`, two-stage, automatic
  `plan.author`, `/milestone-plan <id>`) and the `REVISING_PLAN` rows route a
  non-ready plan-stage item back to its author; an `AMENDING_PLAN` to
  `AMENDING_PLAN` run is an allowed transition, classified `no_progress`.
  The protocol names no anchor error.
- **Test fixtures.** The acceptance matrix renders one anchor pair per
  registry checkpoint in every plan it writes (`plan_anchors`,
  `cp4_render_plan`), and it already drives amendments whose anchored,
  unchanged checkpoints are retained. The harness's default plan has zero
  checkpoints. Section 11 records the probe of what else would fail.

## 3. Design decisions

### D-Check: one wrapper, one rule

`payload/scripts/workflow_state.py` gains:

- `PLAN_ANCHOR_NEXT_STEP`, the one next step every early refusal ends with:
  give every registry checkpoint an id of the shape `CP<digits>[A-Z]?` and a
  well-formed `<!-- CPn -->` ... `<!-- /CPn -->` pair around its section of
  the plan document, then run the command again.
- `_assert_post_registry_well_formed(work_item_id, registry)`: the two
  `AmendmentPostRegistryMalformedError` checks `apply_plan_approval` makes
  today, moved verbatim into a helper both callers use (same order, same
  messages; `apply_plan_approval` calls it where the two checks stand now,
  so the approval's own message is unchanged, INV-3; the wrapper alone adds
  context).
- `assert_plan_checkpoint_anchors(repo_root, work_item_id, *, state=None,
  pin_dir=None, allow_bound_regeneration=False) -> None`, read-only:
  1. reads the state (when `state` is `None`) and returns at once for a work
     item whose governing version is not two-stage (INV-5), and, only when
     `allow_bound_regeneration` is true (the generator's call, D-Where 2),
     for an item at a ready plan-review phase (`AWAITING_LOCAL_PLAN_REVIEW`,
     `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`, `AWAITING_PLAN_APPROVAL`) whose
     `plan_review_binding.status` is `BOUND`;
  2. resolves `plan_path` and `registry_path` through
     `workflow_fingerprint.resolve_plan_stage_metadata` (the same resolver
     the generator uses, never a second reader) and reads both from
     `pin_dir` when given, else from the working tree;
  3. runs `_assert_post_registry_well_formed`, then
     `validate_post_anchor_coverage(plan_text, registry)`;
  4. on any of the three anchor errors **and on
     `AmendmentPostRegistryMalformedError`**, raises **the same class** again
     with the work item id, the plan revision, whether an amendment is open,
     the original message kept verbatim, and `PLAN_ANCHOR_NEXT_STEP`,
     chained from the original (LPR-R1-002: a malformed registry at a first
     revision would otherwise surface the approval's "... for this
     amendment" message with no item, no revision and no next step). The
     revision named is the registry's `plan_revision`, read from the same
     source (pin or working tree) as the plan text (LPR-R1-003): at the
     publish check the state mirror has not advanced yet, so the registry,
     which the author has already regenerated at that point (D-Where 1,
     LPR-R2-001), is the revision being made reviewable. A registry with no readable `plan_revision` is named
     "unknown revision".

Nothing else changes: `validate_post_anchor_coverage`,
`parse_checkpoint_anchor_spans`, reconciliation and `apply_plan_approval`'s
behavior stay as they are (INV-1, INV-3). The three classes' docstrings gain
one sentence naming the early callers.

### D-Where: the places that make a revision reviewable

The check runs at three points, all before `AWAITING_LOCAL_PLAN_REVIEW`:

1. **Publish** (command texts). `/milestone-plan`'s publication point and
   `/apply-plan-review` step 5 call `assert_plan_checkpoint_anchors(repo_root,
   work_item_id)` immediately before the `publish_plan_revision`
   transaction, and after everything that can still change the plan or the
   registry: in `/milestone-plan` that is after the publication point's items
   1 to 3 (registry and mapping regeneration, table re-embed, staging), so
   the check is a new item 4 and the publish is renumbered item 5
   (LPR-R2-001); in `/apply-plan-review` step 5 the regeneration, re-embed
   and staging already precede the publish in the same step. A refusal writes nothing: the item stays at its non-ready
   phase with its previous record.
2. **Generation** (mechanical). `prepare-ai-review.sh`, stage `plan`, right
   after the `--derive-plan-stage-document` step, runs a short Python step
   (`python3 -B`, naming no governing version, CP2) that calls `assert_plan_checkpoint_anchors(repo_root, work_item_id,
   pin_dir=<the staging pin>, allow_bound_regeneration=True)`. Every entry
   to the generator reaches it: `./scripts/prepare-ai-review.sh <base> plan
   <id>` from the commands, `/prepare-review plan <id>`, and a manual
   re-run. It checks the pinned bytes, which are exactly
   the bytes the bundle and its `review_content_id` describe, so an edit
   between a worktree check and the pin cannot slip through. A refusal prints
   `error: <ErrorClass>: <message>` and exits 1 through the existing
   `cleanup` trap: the staging directory and staging pin are removed, the
   previous `current/`, archive and `.pin` are untouched, nothing is marked
   `REJECTED`, and no state is written. The commands' existing "if the
   generator fails" paragraphs already route this (row 9, recoverable).

   **The exception (LPR-R1-001).** The check is skipped, through
   `allow_bound_regeneration=True`, for an item at a ready phase whose
   binding record is `BOUND`. The skip is safe because the readers accept only
   the bound `review_content_id` (`assert_plan_review_bundle_bound` and the
   approval readers), so a regeneration skipped here can never put other
   content in front of a reviewer: if the worktree has drifted at the ready
   phase (row 4a), the regenerated `current/` describes unchecked content
   that can never be reviewed or approved, and the status stays at row 4a
   (LPR-R2-002). A withdrawal returns the item to a non-ready phase, where
   the publish check and this check both apply. In the ordinary case what
   the generator regenerates is the bound review's own content, with the same
   `review_content_id`. That is status row 4b's remedy ("regenerate the
   bundle; the content is unchanged, so row 2 then matches", for a damaged or
   missing `current/` or a failed final rename), and `/review-plan` step 5's
   and `/record-manual-plan-review`'s "rows 4b/4c: regenerate, or withdraw".
   Refusing it would force a withdrawal and spend both plan-review stages
   again, the cost this milestone removes. INV-2 holds: no unchecked revision
   ever becomes bound. Row 4c (a ready item with no binding record) is not
   skipped: its regeneration needs anchors or it takes the row's other
   remedy, withdrawal. At `PLANNING`, `REVISING_PLAN` and `AMENDING_PLAN`
   (rows 7 to 11, `PUBLISHED_UNBOUND` included) the check always runs.
3. **Bind** (command texts). `/milestone-plan` step 6 and
   `/apply-plan-review` step 7' call the same function immediately before
   `verify_plan_review_bundle`. The generator check already covers every
   bundle 2.11.0 generates; this one covers a bundle a 2.10.0 generator left
   behind for an item that was published but not bound at the update (row
   9), which `/milestone-plan` would otherwise bind without regenerating.

Not inside `verify_plan_review_bundle` (it also serves the status function,
so it would re-judge a review bound before the update, against INV-4) and not
inside `publish_plan_revision`/`bind_plan_review_bundle` (pure functions with
no repository access; giving them one changes every caller for no gain over
the generator, which no review can bypass).

### D-Scope: which revisions must carry anchors (OD-1)

Every plan revision of a two-stage work item that is published, generated or
bound by 2.11.0 or later, whatever release created the item. Version "1"
items are exempt.

- An item created on 2.11.0 has anchors from revision 1.
- An in-flight item still in planning (`PLANNING`, `REVISING_PLAN`) adds
  anchors to its next revision: cheap, and nothing it has completed depends
  on them yet.
- An item at `AMENDING_PLAN` already needed anchors at approval; it now hears
  so before review.
- An item bound in plan review at the update keeps its bound review, and
  that review's bundle can be regenerated unchanged (status row 4b) without
  anchors; only a revision after it is checked (D-Where 2, the exception). A
  ready item with no binding record (a pre-2.6.0 item, status row 4c) whose
  remedy is to regenerate its bundle needs anchors for that regeneration, or
  takes the row's other remedy, withdrawal.
- An item at `IMPLEMENTING` or later with an approved plan without anchors is
  untouched until it amends (INV-4); its amending revision needs anchors, as
  it already did at approval.

The alternative, only items created on 2.11.0 or later, needs to know which
release created an item. Nothing records that today, so it needs a new
persisted field (against INV-6) or a guess, and it would keep producing plans
whose first amendment demotes every checkpoint, the cost this milestone
exists to remove.

### D-Error: what the refusal says (OD-2)

The same three classes everywhere, so approval-time and early refusals are
one error to an operator, an orchestrator, and every existing `except`.
`AmendmentAnchorCoverageError` raised for a first plan revision reads oddly,
so its docstring and the message say what it covers: "a plan revision" with
"(amendment open)" when it is one. A new class (a subclass, or a renamed
family) would buy a cleaner name at the price of two names for one rule. Each
message names the work item, the revision, the first offending checkpoint id
(as today) and ends with `PLAN_ANCHOR_NEXT_STEP`. The original message is
kept verbatim, including its "being approved", because rewording it would
change the approval's own message (INV-3). For example:

> checkpoint-anchors-early plan revision 2 (amendment open): CP3 has no
> well-formed anchor pair in the plan document being approved -- every
> registry checkpoint id must have at least one -- give every registry
> checkpoint an id of the shape `CP<digits>[A-Z]?` and a well-formed
> `<!-- CPn -->` ... `<!-- /CPn -->` pair around its section of the plan
> document, then run the command again.

### D-Heading-Fallback: comparing `### CPn` sections when the pre-plan has no anchors (OD-3)

Out of scope; reconciliation's zero-anchor default stays. A heading-section
comparison is small, but it is not provably conservative: a checkpoint's
design also lives outside its own `### CPn` section (the design decisions it
implements, the requirements table, the risks). An amendment that changes a
design decision CP3 implemented, without touching `### CP3`, would leave CP3
`COMPLETE`. Anchors avoid that because the author draws the spans around
everything that describes the checkpoint, and a reviewer sees them. The cost
of the default falls once per legacy plan: the amendment that adds anchors
pays it, and every later amendment of that item reconciles per checkpoint.

### D-Command: `/milestone-plan`'s text

Step 3 (`[2.1]`) gains one instruction: write a well-formed `<!-- CPn -->` ...
`<!-- /CPn -->` pair around every checkpoint's section of the plan document in
every revision (each id `CP<digits>[A-Z]?`; more than one disjoint pair per
checkpoint where its design is spread out; the pairs may wrap the checkpoint
heading). Step 4's self-review confirms it. The publication point gains a
new item 4, the check, placed after item 3's staging and immediately before
the publish, which is renumbered item 5 (LPR-R2-001: an item 0 would read the
registry before step 4's self-review edits are regenerated into it, refusing
a removed checkpoint's missing anchor and passing an added one); step 6 names the generator's refusal and adds
the check before the bind; both name `PLAN_ANCHOR_NEXT_STEP`.
`/apply-plan-review` step 5 and step 7' gain the same two checks.
`/request-plan-amendment`'s anchor paragraph says the amended plan is now
refused at publish and generation, not first at approval. Only these
sentences change in each command file.

### D-Downgrade: what an older release does with this release's state (OD-4)

The paragraph for the release notes:

> Workflow 2.11.0 checks a plan revision's checkpoint anchors when the
> revision is published, bound or turned into a plan-review bundle, and
> writes nothing new: no state field, value, record, configuration key or
> commit shape. A repository on 2.11.0 can be read and driven by 2.10.0.
> Moving back to 2.10.0 loses only the early refusals: an amending plan
> without anchors is again refused first at plan approval, after both plan
> reviews, and a new plan without anchors is accepted, so its first
> amendment demotes every completed checkpoint. Plans already written with
> anchors keep them, and 2.10.0's reconciliation uses them.

### D-Protocol: unchanged at 1.3 (OD-5)

No row, reason code, action or check is added. A refusal happens inside the
author's own run (`plan.author`, or `/apply-plan-review` for a revision), the
author is the one who can fix it, and the item stays at a non-ready
plan-stage phase that rows 7 and the `REVISING_PLAN` rows already route back
to that author (`AMENDING_PLAN` to `AMENDING_PLAN` is `no_progress`).
`WORKFLOW_RELEASE` becomes `2.11.0`, and `ORCHESTRATION_PROTOCOL.md`'s list of
tested releases gains **Workflow 2.11.0** (protocol `1.3`).

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | recommendation |
| --- | --- | --- |
| OD-1 | Does the requirement apply to every work item's next plan revision, or only to items created on 2.11.0 or later? | **Every two-stage item's next plan revision**; version "1" exempt; approved and bound plans untouched until then (D-Scope). Telling items apart by creating release needs a new persisted field, and would keep producing plans whose first amendment demotes everything. |
| OD-2 | What the refusal says, and under which error | **The same three classes as approval** (`AmendmentAnchorCoverageError`, `AmendmentAnchorMalformedError`, `AmendmentCheckpointIdShapeError`), the message naming the item, the revision, whether an amendment is open, the first offending id, and one next step, `PLAN_ANCHOR_NEXT_STEP` (D-Error). |
| OD-3 | Heading-section fallback for an amendment of a plan without anchors | **Out of scope**: it is small but not provably conservative (D-Heading-Fallback). |
| OD-4 | Downgrade posture | **Nothing new is written**; a move back loses only the early refusals (D-Downgrade). |
| OD-5 | Protocol | **Unchanged at 1.3**, no row or reason code; only the release constant and the tested-releases list (D-Protocol). |
| OD-6 | Release version | **2.11.0**, a minor, `feat:` title: new plan revisions must carry anchors. Not a patch (it refuses input 2.10.0 accepts), not a major (nothing persisted or already approved changes). |

## 5. Checkpoints

Each checkpoint runs the payload's nine suites in a release-source
conformance fixture and `workflow-manager verify .` on the checkout, with
`TMPDIR=$HOME/.cache/w7-plan/tmp` (`/tmp` is a nearly full shared tmpfs).
Package builds use the Manager venv
`~/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv`.
The installation under `scripts/`, `.claude/` and `docs/ai-workflow/`'s
managed files is never edited.

**Conformance at a checkpoint** (the W4/W5 procedure). `release.py
stage-conformance` refuses changed payload bytes while `manifest.json` still
carries 2.10.0's digests, which CP6 refreshes. CP1 to CP5 therefore stage a
scratch release from the checkpoint's own commit (`package.stage` with the
venv's Python, into an empty directory outside the repository), rewrite
`sha256` and `size` of every `artifacts` and `templates` record of the
scratch `manifest.json` from the bytes on disk with a throw-away script kept
outside the repository, then run `package.stage_conformance` and the nine
suites in that fixture. CP6 runs the stock `release.py stage-conformance
--commit <CP6 commit>`, and the scratch digests must equal CP6's committed
ones for the same tree.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | One anchor check for every plan revision, reusing validate_post_anchor_coverage | - | 3 | 1 |
| CP2 | Plan-stage bundle generation refuses a plan without anchors, on the pinned bytes | CP1 | 3 | 1 |
| CP3 | Command texts: write anchors from revision 1, check at publish and at bind | CP1 | 2 | 1 |
| CP4 | Regression scenarios end to end: refusals before review, anchored amendments, in-flight plans without anchors | CP1, CP2, CP3 | 4 | 1 |
| CP5 | Documentation: the rule, the refusal and its next step, the downgrade posture | CP2, CP3 | 2 | 1 |
| CP6 | Release 2.11.0: manifest, release constant, release history | CP1, CP2, CP3, CP4, CP5 | 2 | 1 |

<!-- CP1 -->
### CP1 — One anchor check for every plan revision

**Files:**

- `payload/scripts/workflow_state.py`: `PLAN_ANCHOR_NEXT_STEP`,
  `_assert_post_registry_well_formed` (the two checks moved verbatim out of
  `apply_plan_approval`, which calls it in their place),
  `assert_plan_checkpoint_anchors` (D-Check, with its
  `allow_bound_regeneration` argument); one docstring sentence on each
  of the three anchor error classes and on `validate_post_anchor_coverage`
  naming the early callers.
- `payload/scripts/workflow_state_test.py`: unit tests, each through a real
  scratch repository whose plan-stage metadata resolves:
  - a two-stage item ("2.1" and "2.2") whose plan has a pair for every
    checkpoint passes, from the working tree and from a `pin_dir`;
  - a missing pair raises `AmendmentAnchorCoverageError`, a malformed tag
    `AmendmentAnchorMalformedError`, a non-`CP` id
    `AmendmentCheckpointIdShapeError`; each message names the item, the
    revision, the first offending id and ends with `PLAN_ANCHOR_NEXT_STEP`;
    "(amendment open)" appears exactly when the last `amendment_history`
    entry is unresolved; the revision named is the registry's
    `plan_revision` from the same source as the plan text (a `pin_dir`
    registry at revision 3 against a state mirror at 2 names 3); the original
    error is chained;
  - `allow_bound_regeneration=True` returns without reading the plan for an
    item at each ready phase with a `BOUND` record, and still raises for the
    same plan at `PLANNING`, `REVISING_PLAN`, `AMENDING_PLAN` and at a ready
    phase with no binding record (row 4c) or a `CONSUMED`/`PUBLISHED` one;
    with the default `False` a `BOUND` item is checked;
  - with `pin_dir`, the pinned bytes decide, not the working tree (a
    worktree with anchors and a pin without them refuses, and the reverse
    passes);
  - a registry with zero checkpoints passes; a registry without `checkpoints`
    or with an id-less entry raises `AmendmentPostRegistryMalformedError`,
    at a first (non-amendment) revision as well, whose message contains the
    approval's own message verbatim, the item id, the revision and
    `PLAN_ANCHOR_NEXT_STEP`, while `apply_plan_approval` still raises the
    unwrapped message;
  - a "1" item returns without reading the plan (a plan without anchors and
    an unreadable registry path both pass);
  - nothing is written (state file bytes and `git status` unchanged);
  - `apply_plan_approval`'s existing amendment tests stay green unchanged,
    and one new test pins that the early check and the approval refuse the
    same inputs with the same class (a table of plan/registry pairs run
    through both).

**Verification:** the nine suites green in the scratch fixture; a whole-file
diff of `workflow_state.py` against `v2.10.0` shows only the additions above
and the moved block.

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Plan-stage bundle generation refuses a plan without anchors

**Files:**

- `payload/scripts/prepare-ai-review.sh`: after the
  `--derive-plan-stage-document` step, inside the same `STAGE == plan`
  block, a Python step that calls `assert_plan_checkpoint_anchors(repo_root,
  work_item_id, pin_dir=plan_stage_staging_paths(...)["pin_dir"],
  allow_bound_regeneration=True)` and, on
  any of the three anchor errors or `AmendmentPostRegistryMalformedError`,
  prints `error: <ErrorClass>: <message>` and exits 1 (D-Where 2). The
  block sits between two marker comments (CP4's 2.10.0 stand-in removes
  exactly it); its comment names D-Check and says why the pin is checked.
- `payload/scripts/workflow_fingerprint_generalization_test.py` (the suite
  that runs the real generator for arbitrary work items): a plan without a
  pair for a registry checkpoint fails generation with the class name in
  stderr; the previous `current/`, archive and `.pin` are byte-identical
  afterwards; no `current.staging-*` or `.pin.staging-*` is left; no
  `REJECTED` marker; `WORKFLOW_STATE.json` unchanged; the same with an open
  amendment; a plan with pairs generates as before; a "1" item without
  anchors generates as before; an item at a ready phase with a `BOUND`
  record and an anchorless plan regenerates unchanged (same
  `review_content_id`), while the same plan at a non-ready phase, or at a
  ready phase with no binding record, is refused; a ready `BOUND` item whose
  worktree plan has drifted (row 4a) regenerates without the check and the
  status stays at row 4a (LPR-R2-002).
- The fixtures the probe (section 11) found, and nothing else:
  - `payload/scripts/workflow_test_harness.py`: when `seed_bundle_item` is
    given registry checkpoints and no `plan_text`, its default plan carries
    one anchor pair per checkpoint (the same shape as the matrix's
    `plan_anchors`); with no checkpoints the default plan is unchanged.
    `workflow_test_harness_test.py` pins both cases.
  - `payload/scripts/workflow_protocol_test.py`: `LIFECYCLE_CHECKPOINTS`'s
    ids `C1`/`C2` become `CP1`/`CP2`, with every use of them in the
    lifecycle drivers. No anchor can ever match `C1`, so these fixtures
    would otherwise be refused with `AmendmentCheckpointIdShapeError`.
  - `payload/scripts/workflow_acceptance_matrix_test.py`:
    `test_the_pre_repair_sequence_publishes_a_table_the_registry_contradicts`
    (and its product copy) reproduces the old stale-table defect by adding
    CP2 to the registry without touching the plan, and asserts that the
    generator does not stop it. That assertion is the one this milestone
    deliberately reverses: it now asserts the generator refuses with
    `AmendmentAnchorCoverageError` naming CP2, and its docstring says why.
    This is the only existing assertion CP2 changes; CP6 changes the two
    release-version expectations (below).
- The new step keeps `prepare-ai-review.sh` version-agnostic: the governing
  version is read inside `assert_plan_checkpoint_anchors`, never named in the
  script (`workflow_integration_test.py`'s
  `test_bundle_scripts_are_deliberately_version_agnostic` stays as it is),
  and the step runs `python3 -B` so it writes no `__pycache__` into the
  repository (an untracked bytecode file changes the next generation's
  `bundle_id`).

**Verification:** the nine suites green; the test counts are 2.10.0's plus
the new tests only; a whole-file diff of each changed test file shows only
the new tests, the fixture changes above and the one reversed assertion.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Command texts: write anchors from revision 1, check at publish and at bind

**Files:**

- `payload/.claude/commands/milestone-plan.md`: step 3's anchor instruction,
  step 4's self-review item, the publication point's new item 4 (the publish
  becomes item 5), step 6's
  check before the bind and the generator refusal (D-Command).
- `payload/.claude/commands/apply-plan-review.md`: step 5's check before the
  publish and step 7''s check before the bind.
- `payload/.claude/commands/request-plan-amendment.md`: the anchor paragraph
  names the early refusals.
- `payload/scripts/workflow_integration_test.py`:
  `_GOLDEN_COMMAND_FILE_SHA256` for the changed command files (with a comment
  naming this milestone), and static conformance tests: `milestone-plan.md`
  and `apply-plan-review.md` name `assert_plan_checkpoint_anchors` before
  `publish_plan_revision` and before `verify_plan_review_bundle` in the same
  step, and pin the publish ordering (LPR-R2-001): in `milestone-plan.md`'s
  publication point and in `apply-plan-review.md` step 5, the first mention
  of `assert_plan_checkpoint_anchors` comes after `write_registry_and_mapping`,
  after `render_registry_markdown` and after the `add -N` staging step, and
  before `publish_plan_revision`, `milestone-plan.md` step 3 states the anchor instruction, and all
  three name `PLAN_ANCHOR_NEXT_STEP`. The "1" branch's golden output of
  `/milestone-plan` is unchanged (INV-5).

**Verification:** the nine suites green; a whole-file diff of each changed
command against `v2.10.0` shows only these sentences.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Regression scenarios, end to end

**Files:** `payload/scripts/workflow_acceptance_matrix_test.py`. A
new `CheckpointAnchorsEarly` class for each work-item type drives the
functions, generator and commits the command texts name:

1. **A new plan without anchors.** `/milestone-plan`'s writes with a plan
   that has no pair for one checkpoint: the check before the publish
   refuses with `AmendmentAnchorCoverageError` and `PLAN_ANCHOR_NEXT_STEP`,
   and the state file is unchanged. A self-review (step 4) that removes an
   anchored checkpoint and its pair is not refused at publish (the check
   reads the regenerated registry), and one that adds a checkpoint without a
   pair is refused at publish, not first by the generator (LPR-R2-001).
   Publishing anyway (a caller that skips
   the check) and generating: the generator refuses before any bundle is
   promoted, the item stays at `PLANNING` with its `PUBLISHED` record (row
   9), and `/review-plan`'s entry refuses (non-ready phase). Adding the pair
   and running again binds at `AWAITING_LOCAL_PLAN_REVIEW`.
2. **An amendment without anchors.** An item with an anchored, approved plan
   and `COMPLETE` checkpoints is amended; the amending revision drops one
   pair: refused at publish and at generation exactly as in 1, at
   `AMENDING_PLAN`, before any review stage is written (the item's
   `plan_review_stages` and both review ledgers unchanged). A malformed tag
   instead gives `AmendmentAnchorMalformedError` the same way.
3. **A bundle left by 2.10.0.** An item published and generated without
   anchors by the 2.10.0 stand-in (below), left unbound (row 9): `/milestone-plan`'s check before the bind
   refuses and nothing is bound. Recovery is then exercised to the end
   (EPR-R1-002): the pair is added to the plan, `/milestone-plan`'s steps run
   again through the real 2.11.0 generator (the item passes through
   `EDIT_IN_PROGRESS`, row 11, because the published content changed), and
   the bundle binds at `AWAITING_LOCAL_PLAN_REVIEW`.
4. **An anchored amendment that only adds a checkpoint.** Both plans carry
   pairs; the amendment adds CP4 and leaves CP1 to CP3 byte-identical: after
   both reviews and approval, CP1 to CP3 stay `COMPLETE`, the
   `reconciliation_outcome` is `retained` for them and `new` for CP4, and
   `/milestone-implement` selects CP4 next.
5. **An approved plan without anchors keeps working.** An item whose
   plan without pairs was generated by the 2.10.0 stand-in (below), then
   reviewed and approved by the real steps, runs
   implementation, both implementation reviews, the technical gate, the
   functional gate and acceptance to `MILESTONE_COMPLETE` with no anchor
   refusal. A second such item is amended: its amending revision without
   pairs is refused at publish and generation; with pairs it passes review
   and approval, and every shared `COMPLETE` checkpoint is
   `needs_revalidation` (the zero-anchor default, unchanged).
6. **Version "1" unchanged.** A "1" item's plan without pairs generates as
   in 2.10.0.

7. **A review bound before the update survives a regeneration (row 4b).**
   An item bound at `AWAITING_LOCAL_PLAN_REVIEW` with an anchorless plan by
   the 2.10.0 stand-in has its `current/` damaged (so
   `plan_review_publication_status` reports `BUNDLE_UNVERIFIED`, row 4b).
   The real 2.11.0 generator regenerates it with no anchor refusal, to the
   same `review_content_id`; the status returns to row 2 (`BOUND`); the item
   proceeds through both plan reviews and plan approval with no anchor
   refusal. The reverse: the same anchorless plan, taken to a non-ready
   phase (withdrawn with `/milestone-plan`, or an item at `REVISING_PLAN`),
   is refused by the generator, and a ready item with no binding record
   (row 4c) is refused too.

**The 2.10.0 stand-in for scenarios 3, 5 and 7.** 2.11.0 cannot produce a
plan-stage bundle without anchors, and approval binds the plan's bytes, so a
plan approved without anchors cannot be made by editing an anchored one. No
state is seeded instead: CP2 delimits its block in `prepare-ai-review.sh`
with two marker comments, and the matrix gains one helper that writes a copy
of the shipped script with exactly that block removed, outside the scratch
repository (the script works on the repository it is run in and loads its
Python from that repository's `scripts/`). Scenarios 3, 5 and 7 run their first plan
generation through that copy, standing in for 2.10.0's generator; every
other step is the real one. A test pins that the copy differs from the
shipped script only by the marked block, and that the block is present
exactly once. The commands' own checks before publish and bind are the
command text's steps, which these scenarios skip for their 2.10.0 rounds,
as 2.10.0's commands did.

**Verification:** the nine suites green; the matrix's test count is
2.10.0's plus the new tests only; a whole-file diff shows only the new class
and its helpers, the 2.10.0 stand-in among them.

<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Documentation

**Files:**

- `payload/docs/ai-workflow/MILESTONE_WORKFLOW.md`: `PLANNING` and
  `AMENDING_PLAN` say every plan revision carries an anchor pair per
  checkpoint and is refused at publish, bind and generation without one; the
  approval-time check stays.
- `payload/docs/ai-workflow/PLAN_REVIEW_WORKFLOW.md` and
  `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`: the plan-stage generator's
  refusal, in the lists of what fails a plan-stage generation.
- `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`: the anchor
  requirement and the early refusal next to its existing anchor text.
- `docs/common-problems.md`: "A plan revision is refused for a missing
  checkpoint anchor", the cause and the one fix (add the pair, run the
  command again), and why it now happens before review.

**Verification:** the nine suites green (the protocol and integration
suites mirror some of these documents); the repository's documentation check
passes; no `docs/ai-workflow/*.md` file quotes a governing-version list.

<!-- /CP5 -->

<!-- CP6 -->
### CP6 — Release 2.11.0

**Files:** `manifest.json` (`workflow_version` 2.11.0 and every `artifacts`
and `templates` digest and size), `payload/scripts/workflow_protocol.py`
(`WORKFLOW_RELEASE = "2.11.0"`, `PROTOCOL_VERSION` stays `1.3`),
`payload/scripts/workflow_protocol_test.py` (the two release-version
expectations, EPR-R1-001: `test_describe_lists_the_new_capabilities_and_1_1`
expects `("1.3", "2.11.0")` for `(protocol_version, workflow_release)`, and
`test_the_release_constant_and_the_protocol_version` expects
`("2.11.0", "1.3", 1)` for `(WORKFLOW_RELEASE, PROTOCOL_VERSION,
PROTOCOL_MAJOR)`; the protocol `1.3` and major `1` halves are preserved, and
nothing else in the file changes in CP6),
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (the tested-releases
list), `docs/release-history.md` (a 2.11.0 row carrying D-Downgrade's
paragraph), and the "Last checked with" lines of the documents this
milestone changed. The manifest digests are committed before the
bundle-generation record.

**Verification:** a whole-file diff of `workflow_protocol_test.py` against
CP5's commit shows only those two release strings; `release.py
stage-conformance --commit <CP6 commit>` and
the nine suites in that fixture; `release.py build` of the commit;
`release_test.py`; `workflow-manager verify .`; the scratch digests of CP5
equal CP6's committed ones for the payload files CP6 does not change.

<!-- /CP6 -->

## 6. Tests and verification summary

CP1 unit tests, CP2 generator tests and any fixture pairs, CP3 static
conformance and golden hashes, CP4 the seven end-to-end scenarios for both
work-item types, the nine suites green, the documentation check, the release
package build, and `workflow-manager verify .`.

## 7. Release and follow-ups (owner actions, after acceptance)

Pull request titled `feat: ...`, squash merge; the `Release` workflow
publishes 2.11.0 when `main`'s manifest names it. Then a Manager pin pull
request in `workflow-manager` (no Manager behavior change is needed for this
release). Consumers get the early check through `workflow-manager update`;
this repository's own installed copy changes only when it updates to 2.11.0.
`docs/ROADMAP.md`'s W7 row is marked Done at acceptance.

## 8. Risks

- **A fixture or real plan without anchors stops a plan review it did not
  stop before.** That is the point of part 2. In-flight approved and bound
  plans are untouched (INV-4); the probe (section 11) found the test fixtures
  CP2 adjusts, and only those.
- **A planner meets the refusal in its own run.** The refusal names the
  checkpoint and the fix, the item stays at its non-ready phase, and the
  protocol already routes it back to the planner (D-Protocol). The plan text
  instructs anchors from revision 1, so a planner following it never sees it.
- **A pinned check and a worktree check disagree.** The generator checks the
  pin (the reviewed bytes); the commands check the worktree before publish
  and bind, and the bind refuses drift between worktree and bundle anyway.
- **A legacy id shape.** A two-stage item whose registry uses ids such as
  `WF4a-i` (or `C1`, as the protocol suite's lifecycle fixtures did) is
  refused at its next revision with `AmendmentCheckpointIdShapeError`.
  Before approval a rename costs nothing; after approval
  `/request-plan-amendment` already refuses such ids.
- **Golden hashes and manifest digests drift.** CP3 and CP6 own them; the
  manifest is committed before the generation record.

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/checkpoint-anchors-early-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | While an amendment is open, the amending plan revision is refused before any review round when a checkpoint lacks a well-formed anchor pair: at publish and bind, and at plan-stage bundle generation, with the same named error as approval and one next step; the approval-time check is unchanged | CP1, CP2, CP3, CP4 |
| REQ-2 | Every new plan revision of a two-stage work item carries a well-formed anchor pair around every checkpoint: `/milestone-plan` says so, and the same check refuses a revision without them at publish, bind and plan-stage bundle generation | CP1, CP2, CP3, CP4 |
| REQ-3 | In-flight work is not broken: a plan approved without anchors keeps driving implementation, reviews and acceptance until its next plan revision, a plan review bound before the update survives an unchanged regeneration of its bundle, and version-1 items are unchanged | CP2, CP4 |
| REQ-4 | An amendment that only adds a checkpoint keeps the other checkpoints COMPLETE when both plans carry anchors | CP4 |
| REQ-5 | The rule, the refusal and its next step, the downgrade posture and the unchanged protocol are written down, with a common-problems entry | CP5, CP6 |
| REQ-6 | 2.11.0 is releasable | CP6 |

## 10. Artifact classification

`docs/ai-workflow/registry/checkpoint-anchors-early-artifacts.json` comes from
the `process` template and is fitted to this plan's footprint, as W5's was.

**Plan stage.** Protected: this plan document, the registry and the mapping.
Excluded beyond the template: `manifest.json`, `docs/release-history.md`,
`docs/common-problems.md` and the prefixes `payload/`, `fixtures/`,
`templates/` and `tools/`. `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`,
`docs/ai-workflow/…` (this plan's own protected paths are matched first),
`.workflow-manager/`, `.github/` and the installation's `scripts/` and
`.claude/commands/` are classified by the template. Every repository path
this document names is run through the classifier before the bundle is
generated.

**Implementation stage.** Protected: `manifest.json`,
`docs/release-history.md`, `docs/common-problems.md`, the prefixes
`payload/`, `fixtures/`, `templates/` and `tools/`, the installation prefixes
`.claude/commands/` and `scripts/` (never edited here; protecting them makes
a stray edit visible to the technical approval), and the declarations file's
own path. `docs/ROADMAP.md` and `docs/ACTIVE_MILESTONE.md` stay excluded as
bookkeeping, and `.github/` stays excluded.

## 11. Probe and review rounds

### Review round 1 (LOCAL_MODEL_PLAN_REVIEW, `REVISE`, applied in revision 2)

All three findings were validated against the release source and accepted.

- **LPR-R1-001 (important, accepted).** Confirmed:
  `plan_review_publication_status` row 4b prescribes regenerating the bundle
  of a bound review, and the phase-agnostic check would have refused it for a
  review bound under 2.10.0. Resolved with a hybrid of the reviewer's two
  options, chosen so that row 4c keeps the rule D-Scope already stated: the
  generator's call passes `allow_bound_regeneration=True`, which skips the
  check only for an item at a ready phase whose binding record is `BOUND`
  (D-Check 1, D-Where 2, D-Scope, INV-4). Not the phase-only option, because
  that would also skip row 4c, which has no binding record and whose
  regeneration needs anchors or withdrawal. Not the content-id option,
  because it needs the pin's `review_content_id` inside the check for no gain
  (a bound item at a ready phase cannot carry other content). CP1 tests the
  argument, CP2 the generator, and CP4 scenario 7 pins the 2.10.0-bound
  anchorless item, its damaged `current/`, the regeneration, row 2, both
  reviews and approval, plus the reverse. `/prepare-review plan <id>` is
  named in D-Where 2.
- **LPR-R1-002 (optional, accepted).** The wrapper also wraps
  `AmendmentPostRegistryMalformedError`; `apply_plan_approval` keeps the
  unwrapped message (D-Check 4, CP1).
- **LPR-R1-003 (apparatus, accepted).** The message names the registry's
  `plan_revision`, read from the same source as the plan text (D-Check 4,
  CP1).

### Review round 2 (LOCAL_MODEL_PLAN_REVIEW, `REVISE`, applied in revision 3)

Both findings were validated against the release source and accepted. Round
1's three dispositions were confirmed resolved by the reviewer.

- **LPR-R2-001 (important, accepted).** Confirmed:
  `payload/.claude/commands/milestone-plan.md:362-400` regenerates the
  registry and mapping (item 1), re-embeds the table (item 2), re-stages
  (item 3) and only then publishes (item 4), so an "item 0" check reads the
  registry before step 4's self-review changes are regenerated into it. Both
  the false refusal (a removed checkpoint's anchor demanded) and the missed
  refusal (an added checkpoint passes, refused later by the generator) follow.
  Resolved: `/milestone-plan`'s check is a new item 4, immediately before the
  publish, which becomes item 5 (D-Where 1, D-Command, CP3 files); the
  LPR-R1-003 rationale is restated against that position (D-Check 4). CP3's
  static test pins the ordering for `milestone-plan.md`'s publication point
  and `apply-plan-review.md` step 5 (after `write_registry_and_mapping`,
  `render_registry_markdown` and the `add -N` staging, before
  `publish_plan_revision`), and CP4 scenario 1 gains the removed-checkpoint
  and added-checkpoint self-review variants.
- **LPR-R2-002 (optional, accepted).** Confirmed: a ready, `BOUND` item's
  worktree can drift (row 4a), so "content cannot change" was wrong; the
  reason INV-2 holds is that the readers accept only the bound
  `review_content_id`. D-Where 2 is reworded and CP2's generator test gains
  the drifted-`BOUND` case (status stays row 4a).

### Review round 3 (MANUAL_EXTERNAL_PLAN_REVIEW, `REVISE`, applied in revision 4)

Both findings were validated against the release source and accepted.

- **EPR-R1-001 (important, accepted).** Confirmed:
  `payload/scripts/workflow_protocol_test.py:5470` expects `("1.3",
  "2.10.0")` from `describe` and `:5480` expects `("2.10.0", "1.3", 1)` from
  the constants, so CP6's `WORKFLOW_RELEASE = "2.11.0"` fails both while CP2
  restricted existing-assertion changes to the stale-table reversal.
  Resolved: CP6 names both updates (files and verification), preserving
  protocol `1.3` and major `1`, and CP2's restriction now says it covers CP2
  only.
- **EPR-R1-002 (optional, accepted).** CP4 scenario 3 continues past the
  refusal: the pair is added and `/milestone-plan` is run again to a bind,
  exercising `EDIT_IN_PROGRESS` after published content changed.

### Probe (planning)

A conformance fixture staged from `a5da36c` (Workflow 2.10.0) outside the
repository, with a refusal patched into its `prepare-ai-review.sh` right
after `--derive-plan-stage-document`: `validate_post_anchor_coverage` on the
staging pin's plan and registry for a "2.1" or "2.2" item. The nine suites
ran four at a time, each in its own copy with its own `TMPDIR` and `HOME`
(TMPDIR=$HOME/.cache/w7-plan/tmp). Suites that failed were rerun unpatched,
and all of them were green.

- Green with the patch: state (1102), gate policy (292), completion
  obligations (106), fingerprint (257), harness (25).
- Protocol (320): 9 failures, all from one fixture. The lifecycle drivers
  seed `LIFECYCLE_CHECKPOINTS` (ids `C1`, `C2`) through
  `seed_bundle_item`, whose default plan has no anchors, and are refused with
  `AmendmentCheckpointIdShapeError`. CP2 renames the ids and gives the
  harness default plan pairs.
- Acceptance matrix (381): 2 failures, one test and its product copy,
  `test_the_pre_repair_sequence_publishes_a_table_the_registry_contradicts`,
  which asserts that the generator does not stop a revision whose registry
  gained CP2 with no plan text for it. CP2 reverses that assertion.
  Everything else in the matrix already writes anchors.
- Integration (292) and generalization (106): 1 failure each, both caused by
  how the probe was written, not by the rule. The probe named
  `governing_workflow_version` in the script, which
  `test_bundle_scripts_are_deliberately_version_agnostic` forbids, and it
  imported modules without `-B`, so a `__pycache__` file changed the second
  generation's `bundle_id` in
  `test_inputs_seed_from_current_when_plan_inputs_has_none`. That test
  passes with `PYTHONDONTWRITEBYTECODE=1`. D-Where and CP2 avoid both.
- No zero-checkpoint plan failed: an empty registry passes vacuously.
