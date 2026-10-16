# W8: Workflow 2.12.0 — review convergence: incremental re-review, a severity rule for verdicts, a review-round field (Revision 9)

- **Work item:** `review-convergence` (`process`, governing version `2.2`)
- **Requested by:** the Controller lane; slot approved by the owner on
  2026-10-14, the next Workflow item after the CI change (#27, `f30e352`).
- **Roadmap step:** W8, a new row 9 in `docs/ROADMAP.md`'s "What's next"
  table, right after W7 (row 8, Workflow 2.11.0). This plan makes it the
  current item.
- **Branch:** `milestone/review-convergence`
- **Base commit:** `f30e352` (main after #27: the release source is Workflow
  2.11.0; this repository's own installation is 2.11.0 with automatic gates,
  default "2.2" and no `GATE_POLICY.json`)
- **Plan revision:** 9. Every checkpoint section carries its
  `<!-- CPn -->`/`<!-- /CPn -->` pair. Section 11 has the revision history.

## 1. Goal

Ship Workflow 2.12.0, a minor release (`feat:` title: new review mechanics),
that makes review loops cheaper and shorter without weakening what an
approval means.

**Why.** Review loops (`plan.review.local`, `plan.apply_review`,
`implementation.review.local`, `implementation.apply_review` and the two
`record_external` actions) are 68% of the worker cost in the shared
Controller job logs since 1 October (section 7 has the measurement). Local
review jobs per work item reach 11 to 16 at the plan stage and up to 15 at
the implementation stage. Three things drive that, and this release answers
each with one rule:

1. **Every round re-reads everything.** A round-2 reviewer gets the whole
   bundle again and nothing that says what changed. → From round 2 the
   bundle carries the changes since the last reviewed bundle and that
   round's findings (D-Changes).
2. **Minor findings cost a round.** A round whose findings are all optional
   is often a `REVISE`. → A `REVISE` must name a Blocking or Important
   finding; otherwise it is refused as malformed and the reviewer reissues
   it, as an `APPROVE` with the findings recorded (D-Severity).
3. **An orchestrator cannot cap rounds without parsing text.** → An
   additive Orchestration Protocol 1.4 field gives the current review round
   (D-Round), and the plan-writing command asks for small plans (D-Size).

One owner-approved addition (2026-10-15), documentation only: the
Orchestration Protocol states when a distinct-provider verdict courier at an
`external_gate` is admissible (D-Courier). The release closes
RodrigoFAbreu/workflow#28, which records the question and the answer.

### Hard requirements (invariants)

- **INV-1, approvals bind the full content.** `review_content_id`,
  `bundle_id`, the ledgers, the gates and every approval basis are computed
  exactly as in 2.11.0. Nothing in this release changes what is hashed or
  approved.
- **INV-2, no review stage is skipped.** Both stages of both two-stage
  reviews still run on every revision. An `APPROVE` must follow a full
  review of the whole bundle, by the reviewer's own declaration (D-Changes).
- **INV-3, a REVISE is never converted.** A malformed verdict is refused
  with nothing written; the reviewer reissues it. No code turns a `REVISE`
  into an `APPROVE` or the reverse (D-Severity).
- **INV-4, who may approve is unchanged.** No new approval basis, no
  automatic acceptance at a cap. The gate policy is unchanged (it already
  accepts an `APPROVE` with recorded optional findings: it reads the
  verdict, never the findings).
- **INV-5, protocol additive.** 1.3 → 1.4 adds one snapshot field and
  nothing else: no row, action, reason code or check changes (D-Round).
  D-Courier's paragraph is documentation of existing obligations only.
- **INV-6, nothing new persisted in state.** No new `WORKFLOW_STATE.json`
  or `WORKFLOW_CONFIG.json` key or value, no new commit shape. The new
  bundle-side file is gitignored, outside `bundle_id` and
  `review_content_id` (D-Downgrade).

### Non-goals

- Acceptance-matrix sharding and the managed conformance width (a later
  release; a new roadmap row).
- Controller-side round counting and caps (the Controller lane's work).
- Any change to who may approve, to the gate policy, or to `BLOCK`.
- Version-"1" items and the single-stage "2.1" implementation review: their
  verdicts are applied by `/apply-*-review` straight from the feedback file
  and stay as they are (D-Severity, "where").
- Editing this repository's installation. It stays Workflow 2.11.0 and
  `workflow-manager verify .` stays clean.
- Publishing, pushing, pinning in `workflow-manager`.

## 2. What exists today (facts this plan relies on)

Read in the release source (`payload/`) at `f30e352`.

- **The verdict.** `REVIEW_PROTOCOL.md` "Feedback protocol" fixes the file:
  a header block (`Status: APPROVE | REVISE | BLOCK`, the binding fields,
  `Reviewed review_content_id:`, `Reviewer role:`, optional
  `Reviewer model:`/`Round:`), then `## Blocking findings`,
  `## Important findings`, `## Optional findings` and five more sections.
  `workflow_fingerprint.parse_review_feedback_header` is the one parser.
  **Nothing counts findings by severity**: the gates read only `Status:`
  (`approval_gate_reachable`, `workflow_gate_policy._review_gate_requirements`).
- **Where a verdict becomes state.** The local stages: `/review-plan` and
  `/review-implementation` (the "2.2" branch) write `REVIEW_FEEDBACK.md`,
  then call `record_local_plan_review`/`record_local_implementation_review`
  (pure state functions, no text). The manual stages:
  `workflow_state.ingest_manual_review_verdict` is the single entry point
  for `/record-manual-plan-review`, `/record-manual-implementation-review`
  and the protocol's `record-external-result`; it refuses a bad header with
  `ManualVerdictHeaderError`, nothing written.
- **Rounds.** Only an `APPROVE` writes a ledger entry
  (`{bundle_id, verdict, round, completed_at, ...}`); a `REVISE` leaves no
  per-round record. `plan_revision` advances only when a round changes the
  registry (`publish_plan_revision` publishes on every round, so it does not
  count rounds); `implementation_revision` advances
  once per implementation bundle generation (`record_bundle_generation`,
  "ordinary" outcome), and each value has its own generation-record commit
  (`Workflow-Bundle-Generation-Record: <id>/<revision>`,
  `discover_bundle_generation_record_commits`).
- **What survives of the previous round.**
  - Plan stage: the plan stays uncommitted between rounds, so Git does not
    hold the previously reviewed bytes. The generator's outgoing `.pin`
    (the previous round's pinned protected paths) and `current/MANIFEST.md`
    (its `review_content_id`) still exist while a new generation runs, and
    are deleted when the new bundle is promoted
    (`_promote_plan_stage_staging`). The previous id is in
    `consumed_plan_review_content_ids` once its `REVISE` (or a withdrawal)
    consumed it.
  - Implementation stage: the previous round's head is recoverable from
    Git: the state file at the `<id>/<revision-1>` generation-record commit
    holds its `reviewed_implementation_head`.
  - Findings: `<feedback_dir>/REVIEW_FEEDBACK.md`, one file overwritten each
    round; at generation time it holds the verdict being answered.
- **The amendment diff.** `prepare-ai-review.sh` writes
  `.ai-review/<id>/AMENDMENT_DIFF.patch`, a sibling of `current/` (outside
  `bundle_id`/`review_content_id`), with a provenance preamble and a diff
  whose Git options are all pinned, and puts it in `review-bundle.tar.gz`
  next to `current`. Readers of the archive extract it and hash only
  `current/`, so an extra member is ignored.
- **Accepting despite findings.** `/approve-review` is user-only
  (`disable-model-invocation`, `validate_user_confirmation`) and records
  `USER_OVERRIDE` when the last verdict is `REVISE` and the gate is
  reachable. For a two-stage item the plan gate needs
  `AWAITING_PLAN_APPROVAL` and both stage `APPROVE`s on the current content,
  and the "2.2" implementation gate needs both implementation-stage
  `APPROVE`s, so neither is reachable from a loop of local `REVISE`s (OD-1).
- **The protocol.** `workflow_protocol.py` (`PROTOCOL_VERSION = "1.3"`,
  `WORKFLOW_RELEASE = "2.11.0"`); `_snapshot()` already reports
  `plan_revision` and `implementation_revision`; the schema's `snapshot`
  object has `additionalProperties: false`. `ORCHESTRATION_PROTOCOL.md`
  section 5.5 says a gate is resolved "outside the orchestrator's run, by a
  person or by `record-external-result`"; consumer obligation 5 forbids
  running a gate's action, and obligation 8 admits external verdicts through
  `record-external-result` only. Nothing says whether an orchestrator may
  carry a verdict produced by an independent reviewer it launched
  (workflow#28).

## 3. Design decisions

### D-Severity: a REVISE names a Blocking or Important finding (OD-2)

One pure check, `workflow_fingerprint.assert_verdict_well_formed(text)`,
next to the parser it builds on. It refuses with a new
`MalformedVerdictError` (protocol error code `refused`, like every other
verdict refusal) when:

1. `Status: REVISE` and neither `## Blocking findings` nor
   `## Important findings` holds a finding. A **finding** is a list item
   (`- `, `* `, `<n>. `) or a `### ` heading inside the section whose text
   is not empty and not a "none" placeholder. Placeholders (case, markdown
   emphasis and trailing punctuation ignored): `none`, `n/a`, `-`, `none
   identified`, and any text of the form `no [<word>] findings` (so `- No
   important findings.` is a placeholder). The review commands write the
   literal `None.` in an empty section, and the tests cover every form the
   commands write (LPR-R1-003).
2. `Status: APPROVE` and `## Blocking findings` holds a finding: an
   approval that lists a blocking finding contradicts itself (LPR-R1-004).
3. `Status: APPROVE` and the header declares `Review scope: changes`
   (D-Changes).

The message names the rule broken and the one next step: reissue the
verdict, either as `APPROVE` with the findings under `## Optional findings`,
or as `REVISE` with the finding that requires a change moved to Blocking or
Important. `BLOCK` and every other status are not checked.

**Where.** Before a two-stage verdict becomes state, nowhere else. What is
mechanical differs by stage (LPR-R1-005):

- **Manual stages: enforced in code.** `ingest_manual_review_verdict`, after
  `require_manual_verdict_fields`, at a two-stage row only (covers both
  manual stages and `record-external-result`; a feedback-only "1"/"2.1" row
  is unchanged). Nothing can reach state around it.
- **Local stages: enforced by the command.** `record_local_plan_review` and
  `record_local_implementation_review` are pure state functions that take no
  text, so `/review-plan` step 7 and `/review-implementation`'s "2.2" branch
  call the check on the text they are about to write, before the feedback
  file and the state write; on a refusal the reviewer rewrites its own
  verdict in the same run. The command text is golden-hashed, so a change to
  that call is a reviewed change. The check is not moved into
  `local_review_audit`, which sees `feedback_text` at automatic gates only.

The apply commands do not re-check: a verdict already turned into state by
2.11.0 is applied as before, so an item in flight at the update never
deadlocks.

**Severity meaning, stated once in `REVIEW_PROTOCOL.md`:** Blocking — the
content is wrong or unsafe and must change; Important — must change before
approval, not wrong in itself; Optional — a suggestion. A round with only
Optional findings is an `APPROVE`; the gate already accepts it and the
findings stay recorded in the verdict.

### D-Changes: the changes since the last reviewed bundle (OD-3)

**The file.** The generator writes
`.ai-review/<id>/CHANGES_SINCE_REVIEW.md`, a sibling of `current/` like
`AMENDMENT_DIFF.patch`: outside `bundle_id` and `review_content_id`,
regenerated on every ordinary generation, deleted when there is nothing to
compare with, and added to `review-bundle.tar.gz` so the manual reviewer has
it. A same-content post-fix republication
(`record_bundle_generation(..., outcome="same_content")`) does not write,
change or delete it; an ordinary `post-fix` generation (every implementation
remediation round after the first, which advances `implementation_revision`)
writes it like any other implementation round. It holds:

1. a preamble: work item, stage, the previous and current
   `review_content_id` and revision;
2. **Previous findings**: the text of `<feedback_dir>/REVIEW_FEEDBACK.md`
   when its header's `review_content_id` is the previous round's id, else
   the line "not available";
3. **Changes**: a unified diff of the stage's protected content, previous
   round → this round, under the same pinned diff options as
   `AMENDMENT_DIFF.patch`.

**The previous round**, at each stage, from data already on disk:

- **Plan stage:** the outgoing `current/MANIFEST.md` and `.pin`, read before
  promotion, used only when that manifest is a plan-stage manifest of this
  item. Two cases, decided by the outgoing manifest's `review_content_id`
  `O` against the new staging `review_content_id` `S`:
  - `O` is in `consumed_plan_review_content_ids` (reviewed and consumed, or
    withdrawn) and `O != S`: a new round. The diff compares the outgoing
    `.pin` with the new staging pin, path by path over the union of both
    protected sets (`git diff --no-index` per path, the same options).
  - `O == S` (a wrapper-only regeneration of unchanged, BOUND content: the
    advisory `bundle_id` in `/review-plan` step 5, or the row-9
    `PUBLISHED_UNBOUND` resume): the outgoing `.pin` is already this
    round's pin, so the previous round's pin is gone and nothing can be
    rebuilt. The rule is to **carry the live `CHANGES_SINCE_REVIEW.md`
    forward unchanged** when its preamble names `S` as the current
    `review_content_id` (copied into staging, then renamed by
    `_promote_plan_stage_staging`), and otherwise to delete it
    (LPR-R1-001).
  - Any other `O` (not consumed and not `S`, not a plan-stage manifest of
    this item, or absent): no file.
- **Implementation stage:** the generation-record commit of
  `<id>/<implementation_revision - 1>`
  (`discover_bundle_generation_record_commits`), its state's
  `reviewed_implementation_head` as the old side, the working tree as the
  new side, over the implementation-stage protected set at both ends
  (`load_implementation_stage_classification`, each end read from the
  declaration in force at that end, so a declaration that changed between
  rounds is compared as it was and as it is). No previous revision, no file.
  **The previous round's `review_content_id`** comes from the outgoing
  `current/MANIFEST.md`, which `prepare-ai-review.sh` reads and keeps in a
  temporary copy at its start, before `current/` is rewritten, and only when
  it is an implementation-stage manifest of this item whose recorded head is
  that `reviewed_implementation_head` (the same bundle the old side
  names). The state stores no per-round id, and recomputing one would need
  the old classification and artifacts, so the manifest is the single
  source. Where it is absent or does not match, the preamble says the
  previous id is "not available", and "Previous findings" is "not
  available" (the feedback header cannot be matched to an id): the diff is
  still written.

A failure to build the file never fails the generation: the file is
reviewer convenience, so the generator deletes any stale copy and writes
nothing, with one warning line. (`AMENDMENT_DIFF.patch` fails closed because
an open amendment's reviewer needs it; a missing changes file only means a
full review.)

**The review rule** (`/review-plan`, `/review-implementation`, the
`REVIEW_REQUEST.md` the planning and apply commands write, and the manual
reviewer's instructions in `/record-manual-*`):

- With the file present, a round may review only the changes and check
  each previous finding is resolved; it then declares
  `Review scope: changes` in the header and may return `REVISE` or `BLOCK`.
- **Any `APPROVE` is a full review of the whole bundle**, declared
  `Review scope: full` or by omitting the line. D-Severity refuses an
  `APPROVE` declaring `changes`.

This is how "final" is known without predicting it: the round that approves
is, by rule, a full round. A reviewer who finds nothing in the changes goes
on to the full pass in the same run. The cost saving is in the `REVISE`
rounds, which are the majority.

### D-Round: the `review_round` snapshot field, protocol 1.4 (OD-4)

`_snapshot()` gains one field for a work item:

```json
"review_round": {"plan": 3, "implementation": null, "current": "plan_local"}
```

- `plan`: the number of plan-review rounds, derived from state already
  persisted and never from `plan_revision` alone, because
  `publish_plan_revision` publishes on every round "whether or not it
  advanced the revision" (`apply-plan-review.md`, step 5) and a round that
  edits protected content without a registry change leaves `plan_revision`
  unchanged (EPR-R1-001). Every plan-review round ends by taking its
  content out of review, and `_write_consumed_plan_review_binding` adds that
  content's `review_content_id` to `consumed_plan_review_content_ids`
  (together with the `plan_review_binding` slot's `consumed` id, as
  `_consumed_plan_review_content_ids` reads them). With `C` = the number of
  distinct ids in that history and `B` = 1 when the binding record is
  `PUBLISHED` or `BOUND`, whatever the phase (content awaiting, in review or
  approved: `apply_plan_approval` never touches the record, so an approved
  item stays `BOUND`), and 0 otherwise (`CONSUMED` or absent):
  **`plan = C + B` when the history is complete and `C + B >= 1`, and
  `null` otherwise.**
  The value is an exact count or nothing within the exactness boundary
  below; it is never an estimate.
  - *Complete* means every round the item has spent is in the history, which
    the Workflow can show from the state's shape in two cases only: no
    consumed slot and no history (a new item before its first `REVISE`), or
    a `consumed_plan_review_content_ids` list that is present, holds the
    slot's non-null id, and has `C >= R`, where `R` is the `plan_revision`
    the `consumed` slot records. `C >= R` is a sufficient check against
    lost rounds, not a description of every complete history (LPR-R8-001):
    it takes a revision to have cost at least one round, and the Workflow
    does not guarantee that. `route_work_item` writes the `plan_revision` its
    caller supplies, and `_publish_plan_revision_two_stage` replaces a
    `PUBLISHED`, never-bound record with new content at a higher revision
    without consuming the unreviewed id (row 11, `EDIT_IN_PROGRESS`, "the
    normal path"). An item that did either has a complete history with
    `C < R`, and reads `null`: safe, never a wrong number. A new item reads 1 at its
    first bound phase and the same 1 at the `REVISING_PLAN` phase that
    follows (LPR-R6-001); it reads `null` at `PLANNING` before its first
    publication (`C + B = 0`, no round yet).
  - *Not derivable, `null`*: every other shape. Named: the fail-closed legacy
    marker (a consumed slot with `review_content_id: null` and
    `legacy: true`, `ensure_plan_review_binding_marker`; LPR-R7-001); a
    `2.6.0`-shaped item (a consumed slot and no history list, so its history
    is the slot alone); a slot id the list lacks (a `2.6.0` writer after a
    downgrade); and any history shorter than `R`. A `2.6.0`-shaped or
    legacy-marker item reads `null` at every phase while its history stays
    short, and `null` is not a round number: it carries no running value
    and no baseline. A `C < R` history from a revision advanced without a
    consumed round (a row-11 re-publication, or a skipped revision number)
    reads `null` too, until `C` catches up with `R`, which may not happen
    while each round also advances the revision.
  - *The exactness boundary, stated once (EPR-R1-001).* A non-null value is
    exact for every item whose plan-review rounds all ran under Workflow
    2.7.0 or later: the durable consumed history exists since 2.7.0, and
    every round consumed under it is kept. A round consumed by an earlier
    writer can be lost, because that writer keeps one slot and overwrites
    it, and nothing can recover an overwritten id. Two cases do this: an
    item begun before 2.7.0, and an item any of whose rounds a pre-2.7.0
    writer drove after a downgrade. Once such an item's history grows to
    `C >= R` it has the shape of a complete one, and from then on the
    field can read a number lower than the item's true round (the external
    reviewer's drives: 6 at true round 10; 3 after four consumed rounds).
    The state records neither the release an item began under nor which
    writer consumed each round, so the Workflow cannot tell, and no
    detection rule or field is added (INV-6). A repository moved back below
    2.7.0 is outside the supported downgrade posture (D-Downgrade), so the
    second case is outside it too; the first is a supported item whose
    value is advisory. For such items `review_round.plan` is advisory for
    cap purposes: a consumer that must enforce a hard cap on an item that
    predates 2.7.0, or on any item of a repository that was ever moved back
    below 2.7.0, counts the rounds itself.
  - *Non-null values never fall, but the field can return to `null`.* While
    the field is a number, `C` only grows and `B` drops from 1 to 0 only in
    the same write that adds the consumed id, so the number never falls and
    is never replaced by a smaller one. It can go from `null` to a number
    and, in the `C < R` case above, from a number back to `null`. The
    protocol text and the section-8 cap obligation say so: a consumer that
    sees `null` after a number counts the rounds itself from its own
    history, which is retroactive, and does not keep the earlier number as a
    cap. No running maximum is asked of it, and no new persisted state
    (INV-6) is added.
  `implementation`: its `implementation_revision` (`null` until set); each
  ordinary implementation bundle generation is one implementation-review
  round, and a same-content post-fix republication
  (`outcome="same_content"`) does not advance it: it is a new review under
  the same number.
  - *Ordinary re-review* (REVISE, edit, republish, bind): the consumed id
    joins the history, the new content is `PUBLISHED` then `BOUND`, so `C`
    and `plan` advance by one per cycle with the revision unchanged (the
    external reviewer's round-2 reproduction of the ordinary sequence).
  - *Plan amendment* (`request_plan_amendment`): the approved content's id is
    consumed, so the count continues and the amended content is the next
    round.
  - *Republication of the same bytes*: `publish_plan_revision` refuses
    consumed content (`ConsumedPlanReviewContentError`), so there is no
    same-content plan republication to count; a withdrawal
    (`/milestone-plan <id>`) also consumes its id and counts as a round, the
    deliberate reading that a withdrawn round was spent.
  - *Approved item*: the approved content is still `BOUND` (`B = 1`) and not
    in the history, so `plan` is the approving round's number and does not
    drop at approval. Through an amendment the value reads 3 at
    `AWAITING_PLAN_APPROVAL`, 3 at `IMPLEMENTING` after approval, 3 at
    `AMENDING_PLAN` (the approved id now consumed, `B = 0`) and 4 once the
    amended content is published (LPR-R4-001).
  Both stages of a round share its `review_round` number, but not the
  ledgers' `round`: that counts per stage (`/review-plan` step 7: one more
  than the highest prior `LOCAL_MODEL_PLAN_REVIEW` round on record) and a
  `REVISE` round leaves no ledger entry, whereas `plan` counts consumed
  contents across both stages. The two can differ for the same item (ledger
  round 7, `plan` 9) and a consumer must not compare them (LPR-R8-002). The
  derivation reads only fields
  that exist and writes none.
- `current`: the review stage the phase is waiting for, from the phase
  alone: `plan_local` (`AWAITING_LOCAL_PLAN_REVIEW`), `plan_external`
  (`AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`, and `AWAITING_EXTERNAL_PLAN_REVIEW`
  for "1"), `implementation_local` (`AWAITING_LOCAL_IMPLEMENTATION_REVIEW`),
  `implementation_external` (`AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`
  for "2.2", `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` for "1" and "2.1"),
  else `null`. For a "2.2" item `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` is
  the ready-for-approval phase after both stages approved
  (`record_manual_implementation_review`), so it maps to `null`; the
  mapping is by phase and governing version, the same pair
  `_MANUAL_VERDICT_ROW_PHASES` uses.

It is derived on every call, never stored. With no work item the snapshot
has no `review_round`. The schema adds the property; `PROTOCOL_VERSION`
becomes `"1.4"`.

**The cap, documented in `ORCHESTRATION_PROTOCOL.md` (a new subsection of
section 8, "Consumer obligations"):** an orchestrator with a round cap
compares `review_round[<stage>]` with it before dispatching a review or an
apply action and, at the cap, stops dispatching and hands the item to a
person. When the field is `null` (not derivable: D-Round's named shapes,
including a field that was a number earlier, LPR-R8-001) it
counts the rounds itself, for example by its own review-job count for the
item, and never treats `null` as 0 or as any number. A number is exact
for an item whose plan-review rounds all ran under 2.7.0 or later and
advisory for cap purposes otherwise: a consumer that must enforce a hard
cap on an item that predates 2.7.0, or on any item of a repository that was
ever moved back below 2.7.0, counts the rounds itself (D-Round's exactness
boundary). The Workflow never accepts at a cap. What the person can do is the
existing user-only paths, unchanged: `/approve-review` with the
confirmation guard where the gate is reachable (`USER_OVERRIDE` after a
`REVISE`); otherwise continue the loop, or withdraw and re-scope the plan
(`/milestone-plan <id>`). OD-1 is the gap this leaves.

### D-Courier: a distinct-provider verdict courier at an `external_gate` (workflow#28)

A clarification of obligations 5 and 8 and section 5.5, added to
`ORCHESTRATION_PROTOCOL.md` section 8 next to the round-cap text: no behavior
change, no new field, no new row, action or check. Independence is enforced
by the Workflow, not by trust in the courier: `ingest_manual_review_verdict`
runs every guard (binding, content id, stage preconditions,
`distinct_reviewer_models` under automatic gates). A courier is admissible
when, and only when:

1. the verdict is produced by a different provider and model family from the
   local stage's reviewer (stated in its `Reviewer model:` line), in a
   disposable copy with no write access to the real repository;
2. the courier passes the verdict text verbatim, never edits, filters or
   retries it into a different status, and records every verdict it obtains,
   `REVISE` included; a limit or failure retry re-runs only an attempt that
   produced no verdict;
3. entry is through `record-external-result` only; on a refusal the
   orchestrator re-decides with `next-action` and never works around the
   guard;
4. it couriers only the two verdict kinds at rows 14 and 28, never resolves a `user_only` action, and
   under a human gate policy the approval stays a person's (recording a
   verdict is not an approval);
5. it is opt-in; unset, the gate stops as today.

### D-Size: plan-size guidance in `/milestone-plan` (OD-5)

`/milestone-plan` step 3 says: keep the plan short and the checkpoint count
small (about six at most); split a large scope into several milestones, each
a release; one principle per decision. A soft check,
`workflow_state.plan_size_advisory(registry) -> str | None`, returns a
warning when the registry holds more than
`PLAN_CHECKPOINT_SOFT_LIMIT = 6` checkpoints; the publication point prints
it and continues. It never refuses and writes nothing.

### D-Downgrade: what 2.11.0 does with what 2.12.0 writes (OD-6)

**Workflow 2.12.0 writes no new key or value to `WORKFLOW_STATE.json` or
`WORKFLOW_CONFIG.json` and no new commit shape. It adds one gitignored file,
`.ai-review/<id>/CHANGES_SINCE_REVIEW.md`, outside `bundle_id` and
`review_content_id`, and one optional verdict header line,
`Review scope:`. Workflow 2.11.0 never reads either: after a move back it
ignores the header line, does not regenerate or delete the file (delete it
by hand so a reviewer does not read a stale copy), and verifies an archive
that carries it, because archive readers hash only `current/`. A move back
loses the severity refusal and the `review_round` field (an orchestrator
reading protocol 1.4 sees 1.3 again).**

The `review_round.plan` value is exact only for an item whose plan-review
rounds all ran under 2.7.0 or later. A move back below 2.7.0 is outside the
supported posture: 2.7.0's own note names content consumed and displaced by
a pre-2.7.0 writer as the residual its history does not hold
(`ORCHESTRATION_PROTOCOL.md`, "Durable consumed plan-review history"), and a
move back from 2.8.0 is supported only for a repository that has written
none of 2.8.0's fields (its "Downgrade" note). A repository that was ever
moved back below 2.7.0 can therefore report a plan number lower than the
true round, undetectably; a consumer that must enforce a hard cap there
counts rounds itself (D-Round).

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | recommendation |
| --- | --- | --- |
| OD-1 | Accepting at a cap for a two-stage item in a loop of `REVISE`s. The existing user-only `/approve-review` (`USER_OVERRIDE`) is reachable only after both stage `APPROVE`s on the current content (section 2), so it cannot accept such an item. | **Do not add a path in this release** (the scope excludes changes to who may approve, and a new user-only acceptance is an approval-mechanics change that deserves its own review). Document what exists (D-Round) and name the gap in `ORCHESTRATION_PROTOCOL.md` and the roadmap's open items. The severity rule already removes the common case (a loop on optional findings). The owner may instead ask for a user-only `/accept-at-cap` in this release; that would add a checkpoint. |
| OD-2 | What a REVISE must contain | **At least one Blocking or Important finding**, checked where a two-stage verdict becomes state: in code at the manual stages, by the review command at the local stages; refused and reissued, never converted (D-Severity). |
| OD-3 | How the approving round is known to be a full review | **Every APPROVE is a full review**, declared `Review scope:`; `changes` with APPROVE is refused (D-Changes). No prediction of the "last" round. |
| OD-4 | Round field shape | **`review_round: {plan, implementation, current}`**: `plan` = `C + B` from the consumed-content history and the binding record when that history is complete, else `null` (not derivable: the legacy marker, a `2.6.0`-shaped item, a history shorter than `plan_revision`, including after a row-11 re-publication); never an estimate, a number never replaced by a smaller one but possibly by `null` (a revision advanced without a consumed round); a consumer receiving `null`, at any time, counts rounds itself; a non-null value is exact for an item whose plan-review rounds all ran under 2.7.0 or later, and advisory for cap purposes otherwise (an item begun before 2.7.0, or a repository ever moved back below it, can read lower than its true round, undetectably), where a consumer enforcing a hard cap counts rounds itself, `implementation` from `implementation_revision`, `current` from the phase and governing version; never stored (D-Round). |
| OD-5 | Plan-size threshold | **6 checkpoints, a warning only** (D-Size). |
| OD-6 | Downgrade posture | **Nothing new in state; one gitignored file and one optional header line 2.11.0 ignores** (D-Downgrade). |
| OD-7 | Release version | **2.12.0, a minor, `feat:`**: it refuses verdicts 2.11.0 accepts and adds a protocol field. |

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Verdict shape: a REVISE names a Blocking or Important finding, an APPROVE is a full review | - | 3 | 1 |
| CP2 | Changes since the last reviewed bundle, at both stages, in the bundle's sibling file and archive | CP1 | 4 | 1 |
| CP3 | Orchestration Protocol 1.4: the review_round snapshot field and the at-cap hand-off | - | 3 | 1 |
| CP4 | Plan-size guidance, the soft checkpoint-count warning, and three small fixes | - | 2 | 1 |
| CP5 | Release 2.12.0: manifest, release constant, release history, downgrade posture | CP1, CP2, CP3, CP4 | 2 | 1 |

Every checkpoint updates the golden command-file hashes
(`_GOLDEN_COMMAND_FILE_SHA256` in `workflow_integration_test.py`) for the
command files it edits. The installation under `scripts/`, `.claude/` and
`docs/ai-workflow/`'s managed files is never edited.

**Conformance at a checkpoint** (the W4 to W7 procedure).
`release.py stage-conformance` refuses changed payload bytes while
`manifest.json` still carries 2.11.0's digests, which CP5 refreshes. CP1 to
CP4 therefore stage a scratch release from the checkpoint's own commit
(`package.stage` with the Manager venv's Python, into an empty directory
outside the repository), rewrite `sha256` and `size` of every `artifacts`
and `templates` record of the scratch `manifest.json` from the bytes on
disk with a throw-away script kept outside the repository, then run
`package.stage_conformance` and the nine suites in that fixture, with
`TMPDIR` outside `/tmp`. CP5 runs the stock `release.py stage-conformance
--commit <CP5 commit> --out "$(mktemp -d)/fixture"`, and the scratch digests
must equal CP5's committed ones for the same tree.

<!-- CP1 -->
### CP1 — Verdict shape

**Files:** `payload/scripts/workflow_fingerprint.py`,
`payload/scripts/workflow_state.py`, `payload/scripts/workflow_protocol.py`
(error-code map only), `payload/.claude/commands/review-plan.md`,
`review-implementation.md`, `record-manual-plan-review.md`,
`record-manual-implementation-review.md`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`.

- `MalformedVerdictError`, `parse_review_scope(text)` (header block only,
  `full`/`changes`/`None`) and `assert_verdict_well_formed(text)` in
  `workflow_fingerprint.py` (D-Severity: three rules, the widened
  placeholder set, an `APPROVE` with a Blocking finding refused).
- `ingest_manual_review_verdict` calls it after
  `require_manual_verdict_fields`; nothing is written on a refusal.
- The four commands: the local reviewers check before writing and rewrite on
  a refusal, and write the literal `None.` in an empty severity section; the
  manual commands report the refusal and ask for a reissued verdict. `REVIEW_PROTOCOL.md` "Feedback protocol": the severity meanings,
  the REVISE rule, the `Review scope:` line.

**Tests:** `workflow_fingerprint_test.py` — REVISE with only Optional
findings refused; REVISE with one Blocking, one Important, a `### ` finding,
accepted; "None.", "- n/a", "- None identified", "- No important findings."
and an empty section do not count (a REVISE whose Important section holds
only one of these, with Optional findings elsewhere, is refused); APPROVE
with a Blocking finding refused, with `None.` there accepted; APPROVE with
`Review scope: changes` refused, with `full` or no line accepted; BLOCK not
checked; the same scope text in the body is not read.
`workflow_state_test.py` — `ingest_manual_review_verdict` refuses a
malformed REVISE at both stages and leaves state and feedback bytes
unchanged; a well-formed one is ingested as before.
`workflow_protocol_test.py` — `record-external-result` with a malformed
verdict returns `refused`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Changes since the last reviewed bundle

**Files:** `payload/scripts/prepare-ai-review.sh`,
`payload/scripts/workflow_fingerprint.py` (the writer, the staging path and
the promotion rename), `payload/.claude/commands/review-plan.md`,
`review-implementation.md`, `record-manual-plan-review.md`,
`record-manual-implementation-review.md`, `milestone-plan.md`,
`apply-plan-review.md`, `apply-implementation-review.md` (the
`REVIEW_REQUEST.md` sentence), `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`
("Bundle location" and the bundle file list), `PLAN_REVIEW_WORKFLOW.md`,
`IMPLEMENTATION_REVIEW_WORKFLOW.md`.

- `workflow_fingerprint.write_changes_since_review(repo_root, work_item_id,
  stage, out_path, *, outgoing_bundle_dir, outgoing_pin_dir, staging_pin_dir)`
  builds the file (D-Changes) and returns whether it wrote one; it catches
  its own errors, deletes `out_path` and returns `False` with a warning.
- Plan stage: called before promotion, writing into the staging area;
  `_promote_plan_stage_staging` renames it next to `current/` or removes a
  live copy, like `AMENDMENT_DIFF.patch`. Implementation stage: written next
  to `current/` after the manifest. The `tar` line adds the member when
  present, keeping the bare `current` positional argument (item 341's
  guard).
- The command texts: D-Changes' review rule, and `REVIEW_REQUEST.md` is
  worded conditionally, because it is written before the generator decides
  whether the file exists: "if `CHANGES_SINCE_REVIEW.md` is present next to
  `current/` and its preamble names this bundle's `review_content_id`, ..."
  (LPR-R1-006).
- Implementation stage: `prepare-ai-review.sh` copies the outgoing
  `current/MANIFEST.md` to a temporary file before it rewrites `current/`,
  and passes it to the writer (D-Changes); a same-content post-fix republication
  (`outcome="same_content"`) leaves the file alone, and an ordinary `post-fix`
  generation writes it.

**Tests:** `workflow_fingerprint_generalization_test.py` or the integration
suite, through the real generator: round 1 writes no file; a plan revision
after a REVISE writes one whose diff shows exactly the edited plan lines and
whose findings are the consumed verdict's; a regeneration of the same bound
content keeps the same file when its preamble names the unchanged
`review_content_id` and deletes it when the live file's preamble names
another id (the wrapper-only regeneration, both directions); an
implementation round 2, generated through the `post-fix` stage with outcome
`ordinary`, writes the file and diffs from round 1's reviewed head over the protected
set only (an excluded-path change is absent) and carries as "Previous
findings" the round-1 local `REVISE`'s text, matched by the previous id from
the outgoing manifest; an implementation round 2 whose feedback header names
another id, or whose outgoing manifest is absent, prints "not available" for
the previous findings and still writes the diff; a same-content post-fix
republication (`outcome="same_content"`) leaves the file untouched; `bundle_id` and `review_content_id` are identical with and without
the file; the archive holds it and `compute_archived_bundle_id` is
unchanged; a corrupt outgoing `.pin` produces no file and a successful
generation. `workflow_test_harness` gains what these need.
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Orchestration Protocol 1.4

**Files:** `payload/scripts/workflow_protocol.py`,
`payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`,
`payload/scripts/workflow_protocol_test.py`.

- `_review_round(work_item)` and the `review_round` snapshot field
  (D-Round), the plan number derived from the consumed-content history and
  the binding record, not from `plan_revision` alone, and `null` for every shape D-Round does not prove complete (EPR-R1-001, LPR-R7-001); `PROTOCOL_VERSION = "1.4"`; the schema property
  (`plan`/`implementation` integer or null, `current` one of the four
  tokens or null).
- `ORCHESTRATION_PROTOCOL.md`: the version history, the field in 5.4 (an
  exact count or `null`, "not derivable", with D-Round's named shapes, the
  exactness boundary: exact for an item whose plan-review rounds all ran
  under 2.7.0 or later, advisory for cap purposes for an item begun before
  2.7.0 or in a repository ever moved back below it, where a number lower
  than the true round is possible and undetectable and a consumer that must
  enforce a hard cap counts rounds itself, the fact that a number can return to `null`, and that
  `plan` is not the ledgers' per-stage `round`), the round-cap obligation in
  section 8 (a consumer receiving `null`, even after a number, counts rounds itself) with the user-only paths and OD-1's gap,
  and a "Protocol 1.4" compatibility note in section 10.
- `ORCHESTRATION_PROTOCOL.md` section 8: the D-Courier paragraph, with its
  five conditions, cross-referenced from obligations 5 and 8 and section 5.5
  (documentation only; workflow#28).

**Tests:** `null` regressions in the same scratch fixture shape
(EPR-R1-001, LPR-R7-001): a schema-valid `2.6.0`-shaped item
(`plan_revision = 5`, one consumed slot id, no history list) and a
legacy-marker item (slot `review_content_id: null`, `legacy: true`) each read
`review_round.plan: null` at every phase they pass through, `REVISING_PLAN`,
the published and bound phases and the following `REVISING_PLAN`, and a
history shorter than its slot's revision reads `null`. The ordinary-cycle,
approval, amendment and withdrawal assertions below are kept unchanged.

A generator-driven regression for EPR-R1-001, through the real
generator, `publish_plan_revision`, `bind_plan_review_bundle` and the local
verdict writer in a scratch fixture: repeat `REVISE`, protected-path edit
without a registry change, publish, generate and bind for three distinct
contents with `plan_revision` held at 1, and assert that `review_round.plan`
reads `null` at `PLANNING` before the first publication, exactly 1 at the first bound phase of a new item (no consumed slot, no
history; LPR-R6-001), 2, 3 at the next two bound phases, that it reads the same value at
the following `REVISING_PLAN` phase, that it does not drop at
`AWAITING_PLAN_APPROVAL`, after plan approval (`IMPLEMENTING`), at
`AMENDING_PLAN` and once the amended content is published and bound (3, 3, 3,
then 4 for the third content approved; the held-at-1 fixture, where `max`
with `plan_revision` cannot hide a drop; LPR-R4-001), that a plan amendment and a withdrawal
each continue the count, that the value never decreases while non-null
along that drive, and that an orchestrator-style cap check against
the reported value trips at the cap; also the field at each review phase of "1", "2.1" and "2.2" items
(`current` and both numbers), including `null` for a "2.2" item at
`AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`, `current: null` elsewhere, absent with no work item;
the field matches the schema; `describe` reports `1.4`; no row, action,
reason code or check list changed (the existing catalogue pins); the
comparisons against the frozen v2.7.0 release strip the new field the way
`without_release()` strips 1.3's check.
A row-11 regression (LPR-R8-001), pure state against the payload functions:
a new "2.2" item publishes content `a` at revision 1, re-publishes `b` at
revision 2 before any bind (row 11), binds, and takes a local `REVISE`;
assert `review_round.plan` is 1 at the bound phase and `null` after the
`REVISE` (`C = 1 < R = 2`), never a smaller number, and that a later round
that brings `C` up to `R` reads a number again.

**Acceptance (D-Courier):** `ORCHESTRATION_PROTOCOL.md` section 8 states the
courier's admissibility with exactly D-Courier's five conditions, as a
clarification of obligations 5 and 8 and section 5.5, and the protocol
diff for it changes no row, action, reason code, check or schema property.
<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Plan-size guidance and three small fixes

**Files:** `payload/scripts/workflow_state.py`,
`payload/.claude/commands/milestone-plan.md`,
`payload/.claude/commands/apply-plan-review.md`, `docs/RELEASING.md`.

- `PLAN_CHECKPOINT_SOFT_LIMIT` and `plan_size_advisory` (D-Size); step 3's
  guidance; the publication point (in both commands) prints the advisory.
- `docs/RELEASING.md`: the `stage-conformance` example uses
  `--out "$(mktemp -d)/fixture"` (the command refuses an existing
  directory).
- `validate_local_plan_review_preconditions`: at a non-ready plan-stage
  phase the refusal names the command that makes the item reviewable:
  `/milestone-plan <id>` at `PLANNING` or `AMENDING_PLAN`, and for a
  published but unbound revision (a `PUBLISHED` `plan_review_binding`
  record, status row 9: it regenerates and binds without re-advancing the
  revision); `/apply-plan-review <id>` at `REVISING_PLAN` otherwise. Other
  phases keep their message.
- `milestone-plan.md`: rewrap the over-long line in step 6's generator-refusal
  bullet.

**Tests:** `plan_size_advisory` at 6 and 7 checkpoints; the refusal text at
each non-ready phase; the `"1"` golden output of `/milestone-plan` unchanged.
<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Release 2.12.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`
(`WORKFLOW_RELEASE`), `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (tested releases),
`docs/release-history.md`, `docs/common-problems.md`, `docs/gates.md`,
`docs/glossary.md`.

- `manifest.json` 2.12.0 with every digest and size refreshed;
  `WORKFLOW_RELEASE = "2.12.0"`; the tested-releases list.
- `docs/release-history.md`: a 2.12.0 row with D-Downgrade's paragraph and
  the D-Courier clarification; the row and the release pull request say the
  release closes workflow#28.
- `docs/common-problems.md`: "A review verdict is refused as malformed" with
  the reissue step. `docs/gates.md`: one paragraph, the gate is unchanged
  and an `APPROVE` may carry optional findings. `docs/glossary.md`: review
  round, review scope. "Last checked with" lines of the docs changed.

**Verification:** the nine suites pass in a stock `release.py
stage-conformance` fixture; `release.py build` of the commit succeeds;
`tools/docs/check_docs.py` is clean; `workflow-manager verify .` is clean.
<!-- /CP5 -->

## 6. Tests and verification summary

Each checkpoint names its tests. Every checkpoint ends with the nine suites
green in a scratch `stage-conformance` fixture, never in place (the
installation is 2.11.0), and `workflow-manager verify .` clean.

## 7. Measuring the effect

**Source.** The shared Controller job logs,
`~/.local/state/workflow-controller/jobs/<job>/`: `decision.json`'s
`action.id` and `action.arguments.work_item_id`, and the worker's cost from
the last `"type":"result"` line of `worker.stdout` (sum of
`modelUsage.*.costUSD`, list price). Same source, same script, before and
after.

**Metrics.**

- M1: review-loop share of worker cost, numerator exactly the six action ids
  `plan.review.local`, `plan.apply_review`, `plan.record_external`,
  `implementation.review.local`, `implementation.apply_review` and
  `implementation.record_external`; denominator all jobs' cost. Before and
  after use this set.
- M2: local review jobs per work item, plan and implementation stage.
- M3: mean cost per `*.review.local` job from round 2 on (the incremental
  rounds).

**Baseline** (jobs at or after 2026-10-01T00:00:00Z and before
2026-10-15T00:00:00Z): M1 = 68% ($309 of $453) for the six-action numerator
(67%, $304, for the four local-review and apply actions alone), recomputed
under the pinned window rule below (the planning script's own figure, taken
before the rule, was 68%, $309 of $457; the per-action shares `plan.review.local` 28%, `implementation.review.local` 22%,
`plan.apply_review` 9% and `implementation.apply_review` 8% are from that
earlier run and are indicative only). A recomputation later on 2026-10-15
without the upper bound gave 66% ($312 of $471), because jobs were added
after planning, this item's own among them; the window rule is therefore fixed as
"jobs whose start time is at or after 2026-10-01T00:00:00Z and before
2026-10-15T00:00:00Z", and the "after" run applies the same rule to its own
window, with the cut-off dates stated beside its result. M2 per item
(plan/implementation): workflow-controller-signalhub-notifications 16/7,
workflow-controller-codex-reviewer 15/0, workflow-manager-operator-ux 14/10,
workflow-controller-usage-budget 11/15, workflow-manager-update-ergonomics
6/14, checkpoint-anchors-early 4/2. Jobs are not exactly rounds (a restart
is a job), so M2 is compared as a distribution, not per item.

**After.** The same script over work items whose plan starts after 2.12.0
is installed in their repository, once at least five items in each lane
have been accepted. Plan size (checkpoint count) is reported next to M2,
because it may explain as much as the rules. The comparison goes into the
roadmap's Done entry for W8 when it is known; the release does not wait for
it.

## 8. Risks

- **A reviewer declares `full` without reading everything.** The scope line
  is declared and unverified, like `Reviewer model:`; the second stage and
  the gate still see the whole bundle. Mitigation: the rule is stated in
  every review command, and the full content is always in the bundle.
- **The severity check misreads a verdict.** A finding format it does not
  recognise refuses a valid `REVISE`; the cost is one reissue, never a
  wrong state. The recognised forms are the ones the commands write.
- **A stale changes file.** It is regenerated or deleted on every
  generation and names both ids in its preamble; a reviewer can see it does
  not match `MANIFEST.md`.
- **Protocol consumers that validate strictly.** A 1.3 schema rejects the
  new snapshot property; section 10 says so, as 1.3's note did.
- **A low `review_round.plan` delays a cap.** For an item begun before
  2.7.0, or in a repository ever moved back below 2.7.0, the field can read
  a number lower than the true round once its history reaches its
  revision, and the Workflow cannot tell (D-Round's exactness boundary,
  EPR-R1-001). Mitigation: the value is documented as exact only for items
  whose rounds all ran under 2.7.0 or later and advisory for cap purposes
  otherwise; a consumer that must enforce a hard cap on such an item counts
  rounds itself. No detection rule or field is added (INV-6).

## 9. Requirements

| id | requirement | checkpoints |
| --- | --- | --- |
| R1 | From round 2 a review gets the changes since the last reviewed bundle and that round's findings, at both stages and both review stages; approvals still bind the full content | CP2, CP5 |
| R2 | A REVISE with no Blocking or Important finding, an APPROVE that lists a Blocking finding, or an APPROVE that declares a changes-only review, is refused as malformed and reissued, never converted | CP1, CP5 |
| R3 | An additive protocol 1.4 field gives the current review round per stage, from existing state; accepting at a cap stays a person's step | CP3, CP5 |
| R4 | `/milestone-plan` asks for small plans and warns, without blocking, above a checkpoint-count threshold | CP4, CP5 |
| R5 | Small fixes: the RELEASING.md fixture path, the `/review-plan` refusal's next step, a line wrap in `milestone-plan.md` | CP4 |
| R6 | The Orchestration Protocol states when a distinct-provider verdict courier at an `external_gate` is admissible, with five conditions, as documentation only (workflow#28) | CP3, CP5 |

## 10. Artifact classification

`docs/ai-workflow/registry/review-convergence-artifacts.json`: the generated
template, plus the release source. At the plan stage the plan, registry and
mapping are protected; `payload/`, `fixtures/`, `templates/`, `tools/`,
`manifest.json`, `docs/release-history.md`, `docs/common-problems.md`,
`docs/RELEASING.md`, `docs/gates.md` and `docs/glossary.md` are excluded
(implementation deliverables). At the implementation stage those same paths
are protected, with the declaration itself; `docs/ROADMAP.md`,
`docs/ACTIVE_MILESTONE.md` and `docs/ai-workflow/` stay excluded. Every path
section 5 names is covered at both stages, including
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` for D-Courier (excluded
at the plan stage by the `payload/` prefix, protected at the implementation
stage by the `payload/` protected prefix); the declaration needs no change
for it.

## 11. Revision history

| revision | change |
| --- | --- |
| 1 | First plan. |
| 2 | Local review round 1 (`REVISE`) applied: LPR-R1-001 (a same-content plan-stage regeneration carries the changes file forward, else deletes it) and LPR-R1-002 (the previous implementation round's `review_content_id` comes from the outgoing manifest), plus the optional LPR-R1-003 to -008 (placeholder set, APPROVE with a Blocking finding, local-stage enforcement, conditional `REVIEW_REQUEST.md` wording, same-content round count, baseline window). |
| 3 | Owner-approved scope addition (2026-10-15): D-Courier, a documentation-only clarification in `ORCHESTRATION_PROTOCOL.md` (CP3) that a distinct-provider verdict courier at an `external_gate` is admissible under five conditions; one acceptance line in CP3, requirement R6, the classification note in section 10, and CP5's release notes close workflow#28. No new checkpoint. Revision 2 withdrawn from local review to carry it. |
| 4 | Local review round 2 (`REVISE`) applied: LPR-R2-001 (D-Courier condition 4 covers rows 14 and 28 only, as workflow#28), LPR-R2-002 (D-Changes and CP2 exclude only the `outcome="same_content"` republication; an ordinary `post-fix` generation writes the file, with a test) and the optional LPR-R2-003 (baseline restated under the pinned window rule, 67%, $304 of $453). |
| 5 | Manual external review round 1 (`REVISE`) applied: EPR-R1-001 (D-Round derives `review_round.plan` from the consumed-content history and the binding record instead of `plan_revision`, which does not advance on every round; the ordinary re-review, amendment, withdrawal and approved cases are documented, and CP3 gains a generator-driven regression) and the optional EPR-R1-002 (M1's numerator is the six named actions, 68%, $309 of $453, with the four-action 67% beside it). |
| 6 | Local review round 4 (`REVISE`) applied: LPR-R4-001 (D-Round's `B` is 1 whenever the binding record is `PUBLISHED` or `BOUND`, approved items included, so `review_round.plan` does not drop at approval; CP3's regression asserts the value at `AWAITING_PLAN_APPROVAL`, after approval, through an amendment and after the amended content is bound), LPR-R4-002 (OD-4 restates the D-Round derivation) and the optional LPR-R4-003 (header revision). |
| 7 | Manual external review round 1 narrow re-check (`REVISE`) applied: EPR-R1-001 (D-Round's `plan` is `S + B`; for a history shorter than `plan_revision` the revision is the baseline and each further distinct consumed id adds a round, so a legacy item reads 5, 6, 7, 8 instead of plateauing at 5; OD-4 and CP3 restated, and CP3 gains a legacy-history regression with the cap hand-off). No new persisted field. Local review round 6 (`REVISE`) then applied at the same revision: LPR-R6-001 (`S = 0` with no consumed history, so a new item reads 1 at its first bound phase), LPR-R6-002 (the single legacy fall is stated exactly and the cap obligation compares the running maximum; CP3's legacy regression runs `R + 1` cycles and asserts it) and the optional LPR-R6-003 (header revision). |
| 8 | Manual external review round 1, third re-check (`REVISE`) applied, by the orchestrator's direction to stop estimating: EPR-R1-001 (D-Round's `plan` is `C + B` only when the consumed-content history is complete, shown by shape, and `null`, "not derivable", for every other shape: the legacy marker, a `2.6.0`-shaped item, a slot id the list lacks, a history shorter than `plan_revision`; never an estimate, never decreasing while non-null; the short-history baseline, the accepted fall and the running-maximum obligation are removed; the cap text says a consumer receiving `null` counts rounds itself; the one limit a shape test has, a pre-2.7.0 history that later reaches its revision, is stated; OD-4, CP3's files and the protocol text restated; CP3's legacy drive replaced by `null` assertions for the `2.6.0`-shaped and legacy-marker items, the ordinary 1, 2, 3 drive through approval and an amendment kept) and the optional LPR-R7-001 (the legacy marker reads `null`, with an assertion). The suggested cap-10 recovery test is not added: with no estimate there is no fall to recover from. No new persisted field. |
| 8 (local round 8) | Local review round 8 (`REVISE`) applied at the same revision (no checkpoint changed): LPR-R8-001 (D-Round states `C >= R` as a sufficient check, not every complete history; a row-11 re-publication or a skipped revision number reads `null`; the "never back" claim is replaced: a number is never replaced by a smaller one but can return to `null`, and a consumer then counts rounds itself, retroactively; OD-4, the CP3 protocol text and the section-8 cap obligation restated; CP3 gains the row-11 regression, asserting `null` after the `REVISE`) and the optional LPR-R8-002 (`plan` is not the ledgers' per-stage `round`; one sentence in D-Round and the 5.4 text). No new persisted field. |
| 9 | Manual external review round 1, fourth re-check (`REVISE`) applied, by the orchestrator's direction to end the loop without a new heuristic or field: EPR-R1-001 is resolved by a truthful exactness boundary, not by detection. Revision 8's exact-or-`null` rule is kept unchanged. The false claim that a low value requires an item begun before 2.7.0 is removed: the reviewer's second drive (a current-writer item driven two rounds by a 2.6.0 writer, reading 3 after four consumed rounds) shows a downgrade does it too, and the current writer cannot recover overwritten ids (`payload/scripts/workflow_state.py:15970`, `:16018`). D-Round now states that a non-null value is exact for every item whose plan-review rounds all ran under 2.7.0 or later; that an item begun before 2.7.0, or driven by a pre-2.7.0 writer after a move back, can read lower than its true round once its history reaches its revision, undetectably (no creation-release stamp, no per-round writer record, INV-6); that a move back below 2.7.0 is outside the supported downgrade posture (`ORCHESTRATION_PROTOCOL.md`'s 2.7.0 note names displaced pre-2.7.0 content as the residual, and its 2.8.0 "Downgrade" note supports a move back only for a repository that wrote none of 2.8.0's fields); and that the value is advisory for cap purposes for such items, a consumer that must enforce a hard cap on an item that predates 2.7.0, or on any repository ever moved back below 2.7.0, counting rounds itself. The same statement is made in the cap paragraph (replacing "never reports a cap-relevant value it cannot prove"), OD-4, CP3's 5.4 text, a new section-8 risk and a new D-Downgrade paragraph. The reviewer's suggested threshold-crossing and downgrade regressions are not added: with no detection the Workflow has no behavior to assert for those histories beyond the documented limit; CP3's existing `null`, ordinary-cycle, approval, amendment, withdrawal and row-11 regressions are kept unchanged. No checkpoint, requirement or persisted field changed. |
