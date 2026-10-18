# W11: Workflow 2.15.0 — local and external review rounds are counted separately (Revision 3)

- **Work item:** `review-round-counts` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner placed it as row 14
  of `docs/ROADMAP.md` (workflow#43; the Controller's companion is
  workflow-controller#88).
- **Roadmap step:** W11, row 14 of "What's next". This plan makes it the current item.
- **Branch:** `milestone/review-round-counts`
- **Base commit:** `16c2599` (main after #49: the release source is Workflow 2.14.0;
  this repository's own installation is also 2.14.0 with automatic gates, default
  `2.2` and no `GATE_POLICY.json`)
- **Plan revision:** 3. Every checkpoint section carries its
  `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.15.0, a minor release (`feat:`: it adds snapshot fields and one
persisted key), in which `next-action` tells an orchestrator how many **local** and
how many **external** review rounds an item has had at each stage, so that two round
caps (local 6, external 4: the owner's decision, enforced by the Controller) can
replace one number that a cheap local round and an external round both raise.

The snapshot's `review_round` gains four fields: `plan_local`, `plan_external`,
`implementation_local`, `implementation_external`. `plan`, `implementation` and
`current` are not touched. Orchestration Protocol becomes 1.5, additive.

### The premise of the request does not hold (read this first)

The request asks for the counts "derived from persisted fields only", counting
"verdicts recorded per stage role". Reading the four writers shows the Workflow does
**not** record a verdict per role:

- `record_local_plan_review`, `record_manual_plan_review`,
  `record_local_implementation_review` and `record_manual_implementation_review` write
  a stage ledger entry **only on `APPROVE`**. A `REVISE` writes a phase and, at the plan
  stage, a `CONSUMED` binding record; a `BLOCK` writes nothing.
- The stage ledgers (`plan_review_stages`, `implementation_review_stages`) are scoped
  to one `review_content_id` and replaced for new content, so they show the current
  content's verdicts only.
- The plan-stage history (`consumed_plan_review_content_ids`, the binding's `consumed`
  slot) lists contents taken out of review, with **no role**: a content rejected by the
  local reviewer, one rejected by the external reviewer and one withdrawn before any
  verdict look the same. `implementation_revision` is the same for both roles.
- The ledger's `round` is the number the reviewer states in the verdict header, not a
  count the Workflow keeps. `optional_findings` references carry a role, but only for
  verdicts that raised an Optional finding.

So for any item that has had a `REVISE` before its current content, the per-role past
cannot be derived from what is persisted today, and the cap case that motivated the
request (C10a: three local rounds and one external round at the plan stage) is exactly
that case. Counting only what is derivable would return `None` in it.

**Decision proposed (OD-1):** persist one small counter (D-Counter), written in the same
call that records the verdict, and derive the four numbers from it. This is one new
work-item key, `review_round_counts`; the request's expectation "nothing new persisted"
is the part that changes, and D-Downgrade states what that costs. The alternative
(derive only what exists, `None` otherwise) is listed in section 4 with why it is not
recommended.

### Hard requirements (invariants)

- **INV-1** `plan`, `implementation` and `current` return byte-for-byte what 2.14.0
  returns for every state. The four new fields are the only snapshot change.
- **INV-2** The only new persisted data is the work-item key `review_round_counts`. No
  new phase, status, configuration key or commit shape (the key joins the closed
  commit-field sets that already admit `optional_findings`, D-Counter). It is outside
  `bundle_id` and `review_content_id`.
- **INV-3** Recording a count never fails or changes a verdict's ingest, a stage
  ledger, a phase or an identity. A malformed key is **not** a refusal of any
  operational path: `validate_state` (and so `load_valid_state`, which `next-action` and
  `record-external-result` use) does not check it, the writers leave a malformed value
  exactly as it was, and the snapshot reads `None`. The malformed key is reported only by
  the explicit `verify` operation (D-Counter, "Validation").
- **INV-4** A count never becomes a smaller number, and never becomes `None` once it
  is a number. (`review_round.plan` can; these cannot.)
- **INV-5** This repository's own installation (`.claude/`, `scripts/`, the managed
  `docs/ai-workflow/` documents, `.workflow-manager/`) is never edited.

### Non-goals

- Any Controller change, the caps themselves (the Workflow reports counts; an
  orchestrator owns the caps), accepting at a cap.
- Reconstructing the counts of an item created before 2.15.0 (it reads `None`).
- Counting the functional review, a pull-request review or a person's approval.
- #30 part 2, #31, #39, #45, #48 and item C.

### What is a gate and what is an aid

| Piece | Kind | Declared limit |
|---|---|---|
| `review_round_counts` in the state | **Record**, exact for what it counts | Counts only verdicts recorded by the four writers under 2.15.0 or later, on an item created under 2.15.0 or later (D-Counter); a verdict ingested while the repository runs an earlier release is not counted (D-Downgrade) |
| The four snapshot fields | **Aid** to an orchestrator's cap | Exact or `None`; no cap is applied by the Workflow |
| `verify`'s `state_valid` check, through `validate_review_round_counts` (not `validate_state`) | **Gate** on the file's shape, for diagnosis only | Checks shape (non-negative integers), never that a count matches the history; no operational loader runs it, so a malformed key never refuses `next-action`, a verdict ingest or a writer |

## 2. What exists today (facts this plan relies on)

- `workflow_protocol._review_round` (`payload/scripts/workflow_protocol.py`) builds the
  snapshot's `review_round` as `{plan, implementation, current}`; `_plan_review_round`
  derives `plan` from the consumed history and the binding record, `implementation` is
  `implementation_revision`, `current` comes from the phase. The schema's
  `review_round` object is `additionalProperties: false` with those three required.
- The four writers named above are pure (`state` in, new `state` out) and are the only
  code that records a review-stage verdict. `/review-plan` and `/review-implementation`
  call the local ones in a `state_transaction`; `ingest_manual_review_verdict` (also
  `record-external-result`) calls the manual ones. `BLOCK` returns the state unchanged.
- `default_work_item` builds every fresh item (`route_work_item` and
  `create_remediation_child_work_item` use it); it fixes `governing_workflow_version`.
- `optional_findings` (2.14.0) is the precedent for a work-item key written by those
  writers: it is admitted by four closed commit-field sets
  (`ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS`, `RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS`,
  `REVIEW_STAGE_WRITE_COMMIT_FIELDS` and `TECHNICAL_APPROVAL_COMMIT_FIELDS`) and
  checked by `validate_state`. Releases that predate a key reject it only in those
  commit helpers, while it is an uncommitted change.
- The manifest `manager` block carries `min_manager_version`, `downgrade_boundary`
  (`posture`, `undetectable`, `signals`), `new_work_only`, `gate_default_change` and
  `conformance.suites`; a `state-key` signal detects a work-item key.

## 3. Design decisions

### D-Counter: the key, what is a round, and when it exists

`work_items[<id>].review_round_counts` is an object:

```
{"plan": {"local": <int>, "external": <int>} | null,
 "implementation": {"local": <int>, "external": <int>} | null}
```

Each integer is a non-negative integer (not a boolean). A stage value of `null` means
"this item records no per-role rounds at that stage".

**A round, for a role, is one recorded verdict of that role.** Exactly: one call of the
role's writer that records an `APPROVE` or a `REVISE` for the item.

| Role | Writer | Counts under |
|---|---|---|
| local, plan | `record_local_plan_review` (`LOCAL_MODEL_PLAN_REVIEW`) | `plan.local` |
| external, plan | `record_manual_plan_review` (`MANUAL_EXTERNAL_PLAN_REVIEW`; the protocol's `record-external-result` reaches it) | `plan.external` |
| local, implementation | `record_local_implementation_review` (`LOCAL_MODEL_IMPLEMENTATION_REVIEW`) | `implementation.local` |
| external, implementation | `record_manual_implementation_review` (`MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`) | `implementation.external` |

The increment is made inside the writer, on the same copied state that records the
verdict, so it is committed or lost with the verdict and no crash can separate them.
The "external" counter is the owner's second stage whichever harness produced the
verdict: the Workflow names the stage, never the reviewer. (The `EXTERNAL_*` phases of
a feedback-only item record no stage verdict and are not counted: that item has no
per-role record.)

What each case counts:

| Case | Counted? |
|---|---|
| `APPROVE` or `REVISE` recorded by a writer | Yes, one round of that role |
| `BLOCK` (the writer returns the state unchanged) | No: nothing is recorded, as for the ledger and `optional_findings` |
| A fix round after a `REVISE`, then a new verdict on the new content | Yes, each recorded verdict is one more round; nothing resets |
| A post-fix republication of the same content, then a verdict | Yes, a recorded verdict; the republication itself is not a round |
| A plan amendment, then a new plan review | Yes, new plan verdicts add to the plan counts; the amendment resets nothing |
| A plan withdrawn (`/milestone-plan <id>`) before a verdict | No: no verdict was recorded |
| A person's approval, a `USER_OVERRIDE`, a gate-policy satisfaction | No: not a review verdict |
| A rejected manual ingest (stale id, wrong role, duplicate) | No: the writer refuses before any write |
| A reopening or a remediation child | The parent keeps its counts; the child is a new item and starts at zero |
| A legacy item imported under 2.15.0, then promoted | **The one exception to "created under 2.15.0".** `import_legacy_work_item` creates it with governing version `"1"`, so both stages are `null`; `promote_legacy_work_item` changes the version to `"2.1"` and initializes nothing. Its counts read `None` for its whole life, by the same never-start-mid-history rule |

**Where the key exists.** `default_work_item` writes it at creation: `plan` is
`{local: 0, external: 0}` when `governing_workflow_version` is in
`TWO_STAGE_PLAN_REVIEW_VERSIONS`, else `null`; `implementation` is
`{local: 0, external: 0}` when the version is `2.2`, else `null` (the implementation
ledger's two-stage protocol is `2.2` only). An item created before 2.15.0 has **no**
key. A writer increments only an existing integer pair; it never creates the key and
never starts a count on an item that has none. That is the single rule for "items
created before 2.15.0": no key, every field `None`, for the item's whole life, because a
count started mid-history would read low without any sign (the failure the existing
`review_round.plan` documents for pre-2.7.0 items). The consumer counts such an item
itself, as it does today.

**Validation, strict for diagnosis and tolerant for operation.** A pure
`review_round_counts_errors(value)` states the shape: an object with exactly the keys
`plan` and `implementation`, each `null` or an object with exactly `local` and
`external`, non-negative integers and not booleans (`InvalidReviewRoundCountsError`, a
sibling of `InvalidOptionalFindingsError`). It is **not** called from `validate_state`:
`load_valid_state` (`workflow_protocol.py`) runs `validate_state` and turns any refusal
into `state_invalid`, and `next-action` and `record-external-result` both load the state
through it, so a check there would let a malformed counter, even on an unrelated item,
stop every orchestration operation and every verdict ingest. Instead a separate
`validate_review_round_counts(state)` applies the shape check to every work item, and
`op_verify` calls it right after `validate_state` inside its existing `state_valid`
check (no new check id, so no protocol change). Every existing `validate_state` check
is unchanged. A malformed value is therefore reported by `verify` and never refuses
`next-action`, `record-external-result`, a writer or `validate_state`.

**Commit-field sets.** `review_round_counts` is added to the four closed sets that name
`optional_findings`, for the same reason: a verdict leaves it uncommitted until the
item's next commit, and those commit helpers refuse a field they do not name. The
audit that CP1 repeats from 2.14.0: every other closed set is item-scoped or does not
see a review-stage write.

### D-Derive: the four snapshot numbers

`review_round.<stage>_<role>` is read from `work_item["review_round_counts"]`:

- the key exists, is well-formed, and the stage value is an object → that integer;
- anything else (no key, a `null` stage, a malformed value) → `None`, whatever the phase.

A boolean counts as malformed (`True` is an `int` in Python). It reads only persisted
fields, never raises, and is computed on every call (never
stored in the snapshot). The four fields are always present in the object (a number or
`null`), after `current`.

**The two units differ and are both kept.** `plan` counts **contents** taken out of
review plus one in review; `plan_local + plan_external` counts **verdicts**. One content
can take a local and an external verdict, so the sum can exceed `plan`; an item with a
withdrawn content can have a smaller sum. They are not compared. `implementation` is
`implementation_revision`; `implementation_local`/`implementation_external` count
verdicts.

### D-Protocol: Orchestration Protocol 1.5, additive

- `PROTOCOL_VERSION` becomes `1.5`; `PROTOCOL_MAJOR` stays 1. The schema's
  `review_round` object gains the four properties (`integer ≥ 0` or `null`), all
  required; `plan`, `implementation` and `current` are unchanged.
- **Compatibility rule for a 1.4 reader.** The change is additive inside an existing
  object. A 1.4 consumer ignores the unknown fields (obligation 2) and reads `plan`,
  `implementation` and `current` exactly as before. A consumer that validates a 1.5
  response against its own copy of the **1.4** schema rejects it (that object has
  `additionalProperties: false`): validate against the 1.5 schema, or drop unknown
  `review_round` fields first. A 1.5 consumer reading a 1.4 response (an older
  Workflow) finds the four fields absent and treats each as `None`, counting itself.
- No row, action, reason code, check, envelope key or error code changes. Section 8.1
  (the round cap) is rewritten as consumer guidance to use the per-stage-and-role
  numbers: before dispatching a review at `current`, compare that stage-and-role's
  number with its cap; `None` means the consumer counts itself; a number is exact.

### D-Downgrade: what 2.14.0 does after 2.15.0

2.15.0 adds one work-item key, `review_round_counts`, written by the four review
writers. After a move back to 2.14.0 the key stays, `validate_state` and the pure
writers ignore it, **but 2.14.0's commit helpers do not name it**. That has two
consequences, and committing pending state removes only the first.

1. **While the key is an uncommitted change of an item's entry**, 2.14.0 rejects the
   item (the refusal family 2.14.0 documented for `optional_findings`, for example
   `ReviewStageWriteNotCommittableError`). Letting the item's pending state be committed
   under 2.15.0 (`git diff HEAD -- docs/ai-workflow/WORKFLOW_STATE.json` shows no
   `review_round_counts` hunk) clears it.
2. **Once a commit that changes the key is in an in-flight item's history**, 2.14.0
   still refuses it. Implementation-stage provenance verification (the check behind
   implementation approval) revalidates the field diff of each generation-record commit
   in the item's provenance interval against closed sets that do not name the key
   (`ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS`, `RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS`
   and the technical-approval set). A reachable case: a local implementation `APPROVE`
   leaves the counter pending, an excluded-only commit lands, and provenance recovery
   then commits the pending ledger and counter in a recovered-role generation record.
   With a clean working tree, stock 2.14.0 raises
   `MalformedBundleGenerationRecordCommitError` at the next provenance check, so
   implementation approval is blocked. Committing the state does not help, because the
   commit is the cause. A key that only appears in `HEAD` through a review-stage write
   or a commit outside any open provenance interval is harmless.

**The supported boundary is therefore:** move back to 2.14.0 only when every item's
pending state is committed **and** no non-terminal item has a commit that changes
`review_round_counts` inside an open implementation-stage provenance interval. An item
that does have such a commit finishes its implementation approval under 2.15.0, or the
repository stays on 2.15.0 until it has. This boundary, not the clean-tree rule alone, is
what the `manager` block, the release history and `docs/common-problems.md` state.

The snapshot loses the four fields and the protocol reads 1.4 again. **Undetectable:** a
verdict ingested while the repository runs 2.14.0 is not counted, so after a re-upgrade
the item's counts read low without a sign; the manifest's `undetectable` text says so,
and a consumer that must hold a hard cap on an item that was ever moved back counts
itself. The provenance refusal above is not undetectable: it is a named error at the
first provenance check.
The `manager` block therefore has a non-empty `posture` that states the boundary (both
consequences), a `state-key` signal `review-round-counts` for `review_round_counts`, a
`new_work_only` entry (counts exist only for items created under 2.15.0), no gate
default change, and `min_manager_version` `1.13.0`: nothing here needs a Manager change
(no new detector kind, package format or CLI contract).

## 4. Open decisions (for the plan reviewer and the user)

| Id | Question | Recommendation |
|---|---|---|
| OD-1 | Persist a counter, or derive only from what is persisted today | Persist (D-Counter). Derivation alone is exact only for an item with no earlier `REVISE` and returns `None` for the C10a case that motivated the request, which makes the fields useless for the cap. The cost is one key, the four commit-field sets and the downgrade posture of D-Downgrade, all of which 2.14.0 already did for `optional_findings`. |
| OD-2 | Items created before 2.15.0 | No key and `None` for the item's whole life (D-Counter). Seeding from the current history would be a guess for exactly the items whose history is incomplete. |
| OD-3 | Whether a `BLOCK` is a round | No: it records nothing today and a count must equal what is recorded. A consumer that wants to cap blocks reads its own job count. |
| OD-4 | Whether the Workflow applies the caps | No: it reports counts; the Controller owns the caps (6 and 4). The protocol text (8.1) states how to compare, not the numbers. |
| OD-5 | The downgrade posture and `min_manager_version` | D-Downgrade; `1.13.0`. |

None of these finalizes a row of `docs/TECHNICAL_DECISIONS.md` (it has no open row on
review data).

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Record the per-role round counts in the state | - | 4 | 1 |
| CP2 | The four snapshot fields and Orchestration Protocol 1.5 in code and schema | CP1 | 3 | 1 |
| CP3 | Protocol 1.5 specification and the user documents | CP2 | 2 | 1 |
| CP4 | Release 2.15.0: manifest, release constant, release history, downgrade posture | CP1, CP2, CP3 | 2 | 1 |

**Conformance at a checkpoint** (the W4 to W10 procedure, as
`docs/ai-workflow/FINDING_DISPOSITIONS_PLAN.md` states it). `manifest.json` still
carries 2.14.0's digests until CP4, and stock `release.py stage-conformance` verifies
the manifest before it builds the fixture and refuses changed payload bytes. CP1 to
CP3 therefore stage a scratch release from the checkpoint's own commit
(`package.stage` with the zlib-ng virtual environment's Python, into an empty
directory outside the repository and outside `/tmp`), rewrite `sha256` and `size` of
every `artifacts` and `templates` record of the **scratch** `manifest.json` from the
bytes on disk with a throw-away script kept outside the repository, then run
`package.stage_conformance` and the nine payload suites in that fixture (`TMPDIR`
outside `/tmp`); the `tools/release` tests run in the same virtual environment. The
committed `manifest.json` is never touched before CP4. CP4 runs the stock
`release.py stage-conformance --commit <CP4 commit> --out "$(mktemp -d)/fixture"`
against its committed manifest, and the scratch digests must equal CP4's committed
ones for the same tree.

<!-- CP1 -->
### CP1 — Record the per-role round counts in the state

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`.

- `REVIEW_ROUND_COUNTS_KEY`, `InvalidReviewRoundCountsError`, a pure
  `review_round_counts_errors(value)` (the shape of D-Counter) and
  `validate_review_round_counts(state)`, which applies it to every work item. Neither is
  called from `validate_state` (D-Counter, "Validation"); `op_verify` in CP2 calls the
  second.
- `default_work_item` writes the key at creation (D-Counter's two initial values by
  governing version).
- A private `_count_review_round(work_item, stage, role)` increments an existing
  integer pair by one and does nothing, and never raises, for an absent key, a `null`
  stage or any malformed value (a string stage, a missing `local` or `external`, a
  negative number, a boolean, an extra key, a non-object); the four
  writers call it for `APPROVE` and `REVISE` after their preconditions pass and before
  `state_revision` is bumped, and not for `BLOCK`.
- `review_round_counts` joins the four closed commit-field sets that name
  `optional_findings`, and the audit of the others is repeated and recorded in the
  tests.

**Tests** (`workflow_state_test.py`): each writer counts one round for `APPROVE` and one
for `REVISE` under its own role and stage and no other counter moves; `BLOCK` and a
refused call (wrong phase, duplicate, stale id) change nothing; a fix round, a
same-content republication, a plan amendment and a withdrawal behave as D-Counter's
table says; an item without the key and an item whose stage is `null` are never
written and never gain the key; `default_work_item` writes the right initial value for
a two-stage plan-review version, for `2.2` and for a version with neither; one
writer test per malformed shape (a string stage, a missing `local`, a negative number, a
boolean, an extra key, a non-object): the verdict, ledger and phase are recorded exactly
as for a well-formed item and the malformed value is left exactly as it was (a boolean
is not "repaired" to 2); `validate_state` accepts a state with a malformed
`review_round_counts` as it did before the key existed; a legacy item imported and then
promoted keeps `null` stages and is never counted; the shape validator accepts the valid
shapes and refuses a boolean, a negative, a string, a missing or an extra key and a
non-object; a remediation child starts at zero; the key
is outside both content identities (`review_content_id` and `bundle_id` unchanged); the
four commit helpers accept an item whose only extra change is the key (review-stage
write, ordinary and recovered generation record, technical approval) and the existing
ones still refuse any other unknown field; **a downgrade regression** (D-Downgrade,
consequence 2): in a scratch repository, a local implementation `APPROVE` under 2.15.0,
an excluded-only commit, provenance recovery committing the pending ledger and counter
in a recovered-role generation record, and a clean working tree. Under the 2.15.0 helpers
the subsequent provenance check passes; the same committed history checked with the
unmodified 2.14.0 helpers raises `MalformedBundleGenerationRecordCommitError`, which pins
the documented boundary (the test fails if 2.14.0 ever accepts it, so the posture text
is revisited). The existing provenance checks are preserved: a recovered-role commit that
changes `reviewed_implementation_head` or `implementation_revision` is still refused.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — The four snapshot fields and Orchestration Protocol 1.5 in code and schema

**Files:** `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`.

- `op_verify` calls `validate_review_round_counts(state)` after `validate_state`, inside
  the `state_valid` check, so a malformed key fails `verify` with the shape message.
- `_review_round` adds `plan_local`, `plan_external`, `implementation_local`,
  `implementation_external` after `current`, each from a small `_role_round(work_item,
  stage, role)` that returns the integer or `None` and never raises (D-Derive).
  `plan`, `implementation` and `current` keep their code unchanged.
- `PROTOCOL_VERSION = "1.5"`; the schema's `review_round` gains the four required
  properties; every test that names the protocol version moves to 1.5.

**Tests** (`workflow_protocol_test.py`): the new fields read the key (zero on a fresh
item; the C10a sequence at the plan stage, kept separate from the full walkthrough:
local `REVISE`, local `REVISE`, local `APPROVE`, external `REVISE`, then republish and
bind, which reads `plan_local` 3 and `plan_external` 1 while `plan` reads 4; and a
separate test that walks a complete approval through each stage and checks the counts
after each verdict); `None` for an item without the key, a `null`
stage, a malformed key and a feedback-only item; **public-entry tests for the
malformed-key fallback**: with a malformed `review_round_counts` on the target item and,
in a second case, only on an unrelated item, the `next-action` command succeeds and
returns the four fields as `None` with `plan`, `implementation` and `current`
unchanged, and `record-external-result` ingests a verdict (the key left byte-identical),
while `verify` fails its `state_valid` check naming the shape problem; when only an
unrelated item is malformed, a target whose own counters are valid keeps its numeric
fields (the fallback to `None` applies to the target's own malformed key, not to a
neighbour's); direct helper
tests alone do not cover the loader; `plan`, `implementation` and `current`
equal a golden copy of 2.14.0's values over the existing `review_round` test matrix
(INV-1); responses validate against the schema, and a response without the four
fields does not; the field is present at every decision row that carries a snapshot;
an item never loses a number it had (INV-4).
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Protocol 1.5 specification and the user documents

**Files:** `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/glossary.md`,
`docs/common-problems.md`.

- `ORCHESTRATION_PROTOCOL.md`: the version line and history sentence, the `review_round`
  bullet of section 5.4 (the four fields, what a round is, which persisted key each
  reads, `None`, the two units, the pre-2.15.0 rule), section 8.1 (per-stage-and-role
  comparison with a cap, `None` handling), the envelope example's version, and a new
  "Protocol `1.5`" compatibility note in section 10 (the compatibility rule of
  D-Protocol for a 1.4 reader and for a 1.5 reader of a 1.4 response).
  The section 5.4 text that calls a ledger's reviewer-stated `round` a count of recorded
  verdicts is corrected (it is the number the reviewer wrote in the verdict header, not a
  Workflow count) and points consumers to the four per-role fields for that meaning.
  Section 8.1 distinguishes the two ways a number can mislead: **missing** (`None`: an
  item created before 2.15.0, a promoted legacy item, a feedback-only item, a malformed
  key; the consumer counts itself) and **stale** (a number that reads low after a verdict
  was ingested under an earlier release, D-Downgrade; undetectable, so a consumer holding
  a hard cap on an item that was ever moved back counts itself).
- `ORCHESTRATION_PROTOCOL.md` section 5.2, `verify` check 2 (`state_valid`): states that
  the check passes when `validate_state(state, repo_root=…)` passes and, in addition,
  `validate_review_round_counts(state)` reports no shape problem; and that
  `validate_state`, and so every operational loader, does not apply the counter check.
  Otherwise the 1.5 specification would contradict the code on what a `state_valid`
  failure means.
- `docs/glossary.md`: the review-round entry names the per-role counts.
  `docs/common-problems.md`: "A review-round count reads null" (an item created before
  2.15.0, a promoted legacy item or a malformed key: the consumer counts itself) and,
  as a separate entry, "A review-round count reads lower than expected" (an item moved
  back to an earlier release and up again: the numbers survive and read low) and a third,
"Implementation approval fails with `MalformedBundleGenerationRecordCommitError` after a
move back to 2.14.0" (D-Downgrade, consequence 2: a counter in a committed
generation-record; finish the approval under 2.15.0).
- No document under `docs/ai-workflow/` carries a list of governing versions
  (the sweep refuses it); the spec says "a two-stage plan-review item" and `2.2`.

**Tests:** `workflow_protocol_test.py` (CP2) already parses the mirrored tables of this
document against the code; nothing mirrored changes. `tools/docs/check_docs.py` is
clean for the edited user documents.
<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Release 2.15.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/common-problems.md`.

- `manifest.json` 2.15.0 with every digest and size refreshed and the rationale text
  updated on the changed records; `counts` unchanged (no file is added or removed). The
  `manager` block: `min_manager_version` `1.13.0`, a non-empty `posture` and an
  `undetectable` text (D-Downgrade) and a `posture` that states the supported downgrade
  boundary (pending state committed **and** no counter-bearing commit in an open
  provenance interval), with the `review-round-counts` `state-key` signal,
  the `new_work_only` entry, an empty `gate_default_change`, and `conformance.suites`
  computed by `release.py manager-block --release-dir <scratch directory> --write` from
  a staging of CP4's own content, in one commit, in the order the 2.14.0 release used:
  make every other edit and refresh digests, stage to a scratch directory outside the
  repository, write `suites`, make the one CP4 commit. No hand-written count, second
  commit or amend. `check-manager-block --commit HEAD` then agrees.
- The release-version constant in `workflow_protocol.py` becomes 2.15.0 and the tested
  releases note (and the envelope example) of the protocol document names it, with the
  protocol at 1.5.
- `docs/release-history.md`: a 2.15.0 row with D-Downgrade's paragraph and boundary, the closed issue
  (workflow#43) and what stays open (#30 part 2, #31, #39, #45, #48). Documents whose
  header names 2.14.0 are re-checked and bumped as `tools/docs/check_docs.py` requires.
- `docs/ROADMAP.md` is marked Current now and Done at acceptance, not in this checkpoint.

**Verification:** the nine suites pass in a stock `release.py stage-conformance`
fixture; `release.py build` of the commit succeeds; `check-manager-block` is clean; the
`update-fixture` step passes from the 2.14.0 bootstrap through the 1.13.0 update;
`tools/docs/check_docs.py` is clean; `workflow-manager verify .` is clean; the tools
tests pass in the zlib-ng virtual environment.
<!-- /CP4 -->

## 6. Tests and verification summary

Each checkpoint's tests are listed in its section. Every checkpoint runs the nine
payload suites from a staged fixture of its own commit (CP1 to CP3 through the
scratch-manifest procedure of section 5) and the `tools/release` tests; CP4 adds the
release steps above.

## 7. Risks

- **A verdict recorded while an earlier release runs is not counted.** The counts then
  read low with no sign. Mitigation: D-Downgrade declares it as undetectable and the
  consumer counts itself for any item that was ever moved back; the new-item rule keeps
  the common path exact.
- **A downgrade with a counter-bearing commit in an in-flight provenance interval
  blocks implementation approval under 2.14.0** (D-Downgrade, consequence 2). Mitigation:
  the boundary is stated in the posture, the release history and common-problems, and
  pinned by a regression test; the remedy is to finish the approval under 2.15.0.
- **Two units.** `plan` and the per-role sum differ by design (D-Derive); a consumer that
  compares them is told not to.
- **State growth.** Four small integers per new item. Accepted.
- **This repository runs 2.14.0.** The new key is not written on this plan's own
  reviews; the counts are tested in scratch repositories.

## 8. Requirements

| Id | Requirement | Checkpoints |
|---|---|---|
| R1 | A work item created under 2.15.0 (except one imported as legacy and later promoted, D-Counter) records, in its state and in the verdict's own transaction, one local or one external round per recorded `APPROVE` or `REVISE` of each review stage, and nothing else changes | CP1, CP4 |
| R2 | `next-action`'s snapshot reports `plan_local`, `plan_external`, `implementation_local` and `implementation_external` (a number, or `None` when not recorded), and `plan`, `implementation` and `current` are unchanged | CP2, CP4 |
| R3 | Orchestration Protocol 1.5, additive: version constant, schema, specification and a stated compatibility rule for a 1.4 reader | CP2, CP3, CP4 |
| R4 | Release 2.15.0: manifest and `manager` block, release constant, release history and the downgrade posture | CP4 |

## 9. Artifact classification

`docs/ai-workflow/registry/review-round-counts-artifacts.json` is declared as the
previous release-source items declared theirs (the generated template does not
classify `payload/`, `manifest.json` or the user documents). At the plan stage the plan
(`docs/ai-workflow/REVIEW_ROUND_COUNTS_PLAN.md`), the registry and the mapping are
protected; `payload/`, `fixtures/`, `templates/`, `tools/`, `manifest.json`,
`docs/release-history.md`, `docs/common-problems.md`, `docs/glossary.md`,
`docs/ROADMAP.md`, `docs/milestones/` and `.github/` are excluded. At the
implementation stage `payload/`, `fixtures/`, `templates/`, `tools/`, `manifest.json`,
`docs/release-history.md`, `docs/common-problems.md`, `docs/glossary.md` and the
declaration itself are protected; the plan, `docs/ROADMAP.md`,
`docs/ACTIVE_MILESTONE.md`, `docs/milestones/` and `docs/ai-workflow/` are excluded.
Every path section 5 names is classified at both stages, including this plan file; the
declaration check of 2.14.0 runs at publication and refuses otherwise.

## 10. Revision history

| Rev | Change |
|---|---|
| 1 | First plan for row 14. |
| 2 | Plan review round 1 (manual external `REVISE`). I1: the shape check is no longer in `validate_state`; a separate `validate_review_round_counts` is called by `verify` only, so a malformed counter never refuses `next-action`, `record-external-result` or a writer (INV-3, D-Counter, CP1, CP2 with public-entry tests). Writers leave malformed values untouched, tested per shape (also the local reviewer's optional finding). O1: C10a test sequence spelled out. O2: legacy-promotion exception named in D-Counter and R1, with a test. O3: missing versus stale counters distinguished in CP3. O4: the ledger `round` description corrected in CP3. |
| 3 | Plan review round 2 (manual external `REVISE`). I2: committing pending state does not make a downgrade safe for an in-flight item, because 2.14.0 revalidates committed generation-record field diffs; D-Downgrade states both consequences and the supported boundary, propagated to the `manager` posture, release history, common-problems and a CP1 regression test (committed counter-bearing recovered record, clean tree, provenance check; existing checks preserved). O1: unrelated-item malformed case keeps the target's numeric values (CP2). O2: CP3 edits the specification's `state_valid` definition; the section 1 table row renamed to the validation split (also the local reviewer's two optional findings). |
