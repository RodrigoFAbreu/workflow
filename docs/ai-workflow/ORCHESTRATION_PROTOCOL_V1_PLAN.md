# W1: Workflow 2.7.0 — Orchestration Protocol v1 and the 2.6.0 follow-ups (Revision 12)

- **Work item:** `orchestration-protocol-v1` (`process`, governing version `2.2`)
- **Roadmap step:** W1 (`docs/ROADMAP.md`, "At a glance"; section 1.9)
- **Branch:** `milestone/orchestration-protocol-v1`
- **Base commit:** `ef714f3` (W0's squash merge, #3; release source at 2.6.0)
- **Plan revision:** 11

## 1. Goal

Ship Workflow 2.7.0, the first release developed in this repository. It has
three parts:

1. **Orchestration Protocol v1.** This is a small, versioned public contract
   through which an orchestrator (the Workflow Controller, its C9) drives a
   repository's Workflow. The orchestrator does not copy Workflow phases,
   artifact paths, helper names or transition rules. The operations are
   `describe`, `verify`, `next-action`, `reconcile`,
   `record-external-result` and `resolve-artifact`. The Workflow owns what
   the lifecycle means, and the orchestrator owns how it is run.
2. **`v2.6.0-002`.** Review feedback gets one pinned `review_content_id`
   label. The other historical label is kept as a legacy alias. The parsing
   of a verdict's header moves inside the Workflow, behind
   `record-external-result`.
3. **`v2.6.0-001`.** Plan-stage content that was once taken out of review
   can never be published or bound again. This holds even after a detour
   through other content. That is the guarantee 2.6.0's approved plan
   states and enforces only for the most recent consumption.

After W1, a 2.7.0-governed repository can be driven by calling the protocol
only. Each existing command still works as before when a human runs it.

### Non-goals

- **Declarative gate policy, automatic approvals, and PR-review reopening.**
  These are W2 (Workflow 2.8). v1 defines the `validation` disposition and
  reserves the PR and functional-evidence result kinds, but 2.7.0 emits none
  of them (`OD-W1-7`).
- **The Controller integration follow-ups.** These are the per-work-item
  integration record and a sanctioned base-moving transition after a trunk
  merge. The Controller's ADR 0006 places them "beside `reconcile`". They
  are not on W1's roadmap row, and they need their own design.
- **Changes to this repository's installation** (`.claude/`, `scripts/`,
  the managed Workflow documents, `.workflow-manager/`, the managed
  `workflow-conformance.yml`). They stay at 2.6.0, and `workflow-manager
  verify .` stays clean. Installing 2.7.0 here is a separate pull request
  made after the `workflow-manager` pin.
- **The `workflow-manager` pin pull request** (`CI_SUITES["2.7.0"]`, the
  pin entry). It belongs to that repository and is made after v2.7.0 is
  published (section 7).
- **Changes to the Controller.** C9 consumes this protocol in the
  Controller's own repository.
- **Removing the 2.6.0 query CLIs** (`--plan-review-publication-status`,
  `--resolve-feedback-path`). Their output stays byte-compatible.

## 2. What exists today (facts this plan relies on)

All paths below are in the release source (`payload/`) unless stated
otherwise.

- **No phase-to-action table exists in code.** The 20 `KNOWN_PHASES`
  (`scripts/workflow_state.py:352`) are an allow-list, not a transition
  graph. The "which command next" mapping is prose only, in
  `docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md` "Which command do I
  run next?". 16 phases are persisted. Four are vocabulary-only
  (`SELF_REVIEWING_PLAN`, `AWAITING_TECHNICAL_APPROVAL`,
  `FIXING_FUNCTIONAL_FINDINGS`, `AWAITING_USER_ACCEPTANCE`), as pinned by
  `TestPersistedPhaseWriterCensus`.
- **The Controller re-derives all of it.** Workflow Controller 1.5.0:
  - pins exact releases (`VALIDATED_WORKFLOW_RELEASES = {"2.5.1","2.6.0"}`)
    and the sha256 of both scripts;
  - copies `KNOWN_PHASES` and several phase subsets;
  - maps each phase to a command in `decision.py` (`AUTOMATIC_TRIPLES`,
    `_STATIC_GATES`);
  - keeps 18 expected-outcome rows naming Workflow writer functions and
    command-file line numbers (`job.py`);
  - re-implements the admissibility checks for feedback and bundles, and
    parses `REVIEW_FEEDBACK.md`, `MANIFEST.md`, `REVIEW_REQUEST.md` and
    commit trailers itself (`evidence.py`);
  - hard-codes `.ai-review/<id>/…` paths.

  Two 2.6.0 queries are the only Workflow-owned answers it consumes:
  `workflow_fingerprint.py --resolve-feedback-path` and
  `workflow_state.py --plan-review-publication-status`. It has no
  stale-decision check: `state_revision` is recorded, but it is never
  compared between the decision and the launch.
- **State identity.** Every mutator bumps the per-item `state_revision` and
  writes under `state_transaction` (lock, re-read, mutate, atomic publish).
  The canonical serializers `_canonical_json_bytes` and `_serialize_state`
  exist. No state digest exists.
- **`validate_state` has no production caller**, as its own docstring says.
  `_validate_work_item` checks the fields it knows and **ignores unknown
  work-item keys**.
- **Existing decision helpers that the protocol can reuse:**
  - `plan_review_publication_status`: a total 11-row plan-stage table with
    a `remedy`;
  - `select_next_checkpoint`;
  - `registry_completion_status`;
  - `plan_approval_gate_reachable`, `technical_approval_gate_reachable`
    and `milestone_complete_gate_reachable`;
  - `verify_checkpoint_completions`, which proves that every `COMPLETE` has
    a reachable trailer commit;
  - `discover_current_functional_checklist_evidence`;
  - `assert_bundle_not_rejected`;
  - `resolve_feedback_dir`, `resolve_bundle_dir(stage=…)` and
    `resolve_plan_review_inputs_dir`.
- **The approval-gate predicates are pure; their inputs are command prose.**
  `plan_approval_gate_reachable` and `technical_approval_gate_reachable`
  (`workflow_state.py:12907`, `:12832`) take `latest_round_status`,
  `protected_path_dirty`, `head_matches_reviewed_implementation_head`,
  `pinned_block`, the review ledger and `current_review_content_id` as
  arguments. Computing those inputs is `/approve-review`'s step list, not a
  function.
- **A `"1"` plan round has no phase of its own.** No writer persists
  `REVISING_PLAN` or `AWAITING_PLAN_APPROVAL` for a `"1"` item
  (`TestPersistedPhaseWriterCensus.EXPECTED_WRITERS`: their writers are the
  two-stage `record_*_plan_review` and `withdraw_plan_review`). A `"1"` item
  sits at `AWAITING_EXTERNAL_PLAN_REVIEW` through the whole round, and
  `/apply-plan-review` re-runs `publish_plan_revision`, which writes that
  same phase. `/approve-review plan` binds a `"1"` verdict by `bundle_id`
  only through `resolve_approval_basis` (`EXTERNAL_APPROVE` on a match,
  `USER_OVERRIDE` otherwise), and `approval_gate_reachable` admits `REVISE`
  as well as `APPROVE`.
- **The plan stage binds by content, the implementation `"1"`/`"2.1"` stage
  by bundle.** Both manual-stage ingests hard-check `review_content_id`
  and treat `bundle_id` as advisory (`check_manual_stage_bundle_id_advisory`).
  `/approve-review` and `/apply-*-review` bind a `"1"`/`"2.1"` verdict with
  `assert_feedback_matches_bundle` (bundle id, base commit, work item).
  The apply commands also bind a **two-stage** `REVISE` that way: step 1
  of `/apply-plan-review` (in `"bundle"` mode) and of
  `/apply-implementation-review` calls `assert_feedback_matches_bundle`
  at every `gv`. A two-stage `REVISE` is therefore bound by content when it
  is recorded and by bundle id when it is applied (MPR-R9-001,
  D-Apply-Binding).
- **`/recover-implementation-provenance` is not user-only.** Its command
  file has no `disable-model-invocation`. The user-only commands are
  `/approve-review`, `/accept-milestone` and `/request-plan-amendment`.
- **Manual-verdict ingestion is prose that orchestrates functions.**
  `record-manual-plan-review.md` calls `resolve_feedback_dir`,
  `assert_bundle_not_rejected`, `assert_manual_feedback_names_work_item`,
  `assert_plan_review_bundle_bound`,
  `validate_manual_plan_review_preconditions` and
  `check_manual_stage_bundle_id_advisory`, then
  `state_transaction(record_manual_plan_review)`. The implementation-stage
  command mirrors it. No single function performs the ingest.
- **`v2.6.0-002`.** The two readers accept disjoint labels:
  - `_FEEDBACK_REVIEW_CONTENT_ID_RE` (`workflow_fingerprint.py:3364`)
    matches `review_content_id:`, optionally preceded by `Reviewed `, over
    the whole file.
  - The Controller matches exactly `Reviewed review content ID:`, before
    the first `## `.

  `review-plan.md` does not name a label, and `review-implementation.md`
  writes the spaced form. `REVIEW_PROTOCOL.md` "Required structure" lists
  only `Status:` and the three binding fields.
- **`v2.6.0-001`.** `plan_review_binding.consumed` is a single slot.
  `_write_consumed_plan_review_binding` is its only writer, and its callers
  are `request_plan_amendment`, both `REVISE` writers,
  `ensure_plan_review_binding_marker` and `withdraw_plan_review`. The slot
  is overwritten on each write. `_assert_not_consumed` compares against the
  slot only. `TestPlanApprovalPhaseGate.test_withdraw_detour_restore_never_reaches_plan_approval`
  pins today's partial mitigation: A re-binds, and approval is gated on
  `AWAITING_PLAN_APPROVAL`.
- **Release mechanics (W0):**
  - A new payload file needs a manifest entry, or the build refuses it as
    "untracked file in release".
  - `feat:` with 2.6.0 → 2.7.0 agrees with `check-title`.
  - Once merged, 2.7.0 is pending, and the release source is frozen until
    it is published.
  - `release-source-conformance` runs seven hard-coded suites, so a new
    suite must be added there and to `templates/.github/workflows/workflow-conformance.yml`.
    The Manager's `TestAuthoredReleaseCiTemplateSuiteNames` requires that
    template to name exactly `CI_SUITES[version]`.
  - Nothing validates the manifest's `provenance`, `overlay_delta` or
    `overlay_*` counts. Since 2.7 there is no overlay
    (`workflow-manager` `docs/ARCHITECTURE.md`).

## 3. Design decisions

### D-OP-Surface: one CLI, one envelope

A new distribution script, `scripts/workflow_protocol.py`, is the whole
protocol surface:

```text
python3 scripts/workflow_protocol.py [--repo-root PATH] [--protocol-major N] <operation> [operation args]
```

It imports `workflow_state` and `workflow_fingerprint` from its own
directory. It never shells out to them. An orchestrator runs it as a
subprocess and never imports it. stdout is exactly one JSON document, the
**envelope**:

```json
{
  "protocol": {"name": "workflow-orchestration", "version": "1.0"},
  "workflow_release": "2.7.0",
  "operation": "next-action",
  "ok": true,
  "result": { "...": "operation-specific" }
}
```

On refusal, `"ok": false` and the envelope carries `"error"` instead of
`"result"`:

```json
{"code": "stale_decision", "message": "…", "retryable": true,
 "native": {"exception": "PlanReviewNotPublishedError", "message": "…"}}
```

`native` is `null` when no Workflow exception is involved. Exit codes:

| exit code | meaning |
| --- | --- |
| `0` | `ok: true` |
| `3` | a refusal with a stable code |
| `2` | `invalid_request`, which covers argument errors |
| `1` | `internal_error`, an unexpected exception |

Every exit code still prints an envelope. Nothing goes to stdout except the
envelope. Diagnostics go to stderr.

`workflow_release` is a module constant, `WORKFLOW_RELEASE`. A build
refuses when it differs from the manifest's version (CP7). The installation
record is `workflow-manager`'s, and the bytes are the truth, so the
constant does not read that record.

### D-OP-Version: protocol version is separate and fails closed

- The protocol version is `MAJOR.MINOR`, starting at `1.0`. It is
  independent of the Workflow release (2.7.0) and of any work item's
  governing version (`2.1`, `2.2`).
- A **minor** bump only adds things: optional response fields, new action
  ids, new error codes, new artifact or result kinds, or new capabilities.
  A consumer of `1.x` must ignore unknown response fields. It must treat an
  unknown action id, disposition or error code as `blocked` and never as
  success.
- A **major** bump is anything else.
- `--protocol-major N` asserts the consumer's major. Any `N` other than `1`
  refuses with `unsupported_protocol` before any other work. Omitting it is
  allowed, for humans.
- 2.7.0 lists the releases tested against v1 only in documentation, never
  in the response.

### D-OP-Errors: stable codes beside native diagnostics

The v1 codes are:

| code | meaning | retryable |
| --- | --- | --- |
| `unsupported_protocol` | unknown protocol major | no |
| `invalid_request` | bad arguments, or a malformed input document | no |
| `unknown_work_item` | the id is not a key of `work_items` | no |
| `no_work_item` | no id was given and no `active_work_item_id` exists, for operations that need one | no |
| `state_unreadable` | the state or config file is missing or corrupt, or the lock file cannot be opened | no |
| `state_invalid` | `validate_state` refused | no |
| `stale_decision` | the decision basis no longer matches the state | yes, by re-deciding |
| `not_applicable` | the operation does not apply at the item's phase or governing version, for example recording a manual verdict at `IMPLEMENTING` | no |
| `unsupported_result_kind` | a result kind is reserved or unknown | no |
| `refused` | a Workflow precondition refused; `native` names the exception | no |
| `internal_error` | an unexpected exception | no |

**The Workflow exception domain** (LPR-R4-001). The release source has no
common base class: `workflow_state.py` defines 168 exception classes and
`workflow_fingerprint.py` 48, and each subclasses `Exception` directly or
one of two module-local intermediates (`LifecycleRefusalError`,
`PlanApprovalTakeoverRefusedError`). None subclasses a built-in other than
`Exception`. W1 does not add a common base: re-basing 216 classes is a
larger change than the protocol needs, and it would alter the MRO that
every existing `except`/`assertRaises` already relies on. Instead, the
domain is defined by origin:

> A **Workflow exception** is an instance of a class `C` such that
> `issubclass(C, Exception)` and `C.__module__` is the `__name__` of the
> `workflow_state` or the `workflow_fingerprint` module object that
> `workflow_protocol` imported.

`workflow_protocol.is_workflow_exception(exc)` implements exactly this
test, and the mapping uses nothing else. It compares against
`{workflow_state.__name__, workflow_fingerprint.__name__}` read from the
imported module objects, never against string literals, so a loader that
imports the scripts under another name (as the `importlib` loader in
`workflow_state_test.py` does for other scripts) cannot silently empty
the domain (round-5 architecture note). Then:

- each Workflow exception class that the protocol maps explicitly has
  exactly one code. The mapping is a table in `workflow_protocol.py`,
  keyed by class name, and a test pins it;
- a Workflow exception with no explicit entry (an unmapped class, or a
  class added in a later release) becomes `refused`, never
  `internal_error`;
- an exception that is not a Workflow exception is `internal_error`, even
  when Workflow code raised it: a built-in such as `KeyError`,
  `TypeError`, `ValueError` or `AttributeError` propagating out of
  `workflow_state` is a defect, not a refusal. `OSError` is
  `internal_error` too, except where the protocol's own state, config or
  lock-file read raises it, which is `state_unreadable`. That read is a
  single protocol function, so the distinction is made by where the error
  is caught, never by inspecting a traceback.

There is no lock timeout to map: `state_lock` blocks in
`fcntl.flock(fd, LOCK_EX)` until it acquires the lock, so
`state_unreadable` is never retryable (corrected in revision 5; revision 4
listed "yes for a lock timeout").

### D-OP-Identity: decision basis and stale decisions

The **state identity** of a work item is

```text
sha256(_canonical_json_bytes({"schema_version": <state schema_version>,
                              "work_item_id": <id>,
                              "work_item": work_items[<id>]}))
```

It covers one work item, not the whole file (`OD-W1-6`). Under D1, unrelated
concurrent items are normal and must not stale each other's decisions.
`active_work_item_id` is not part of it.

Every response that is about a work item carries a `basis`:

```json
{"work_item_id": "…", "state_revision": 7, "state_identity": "<64 hex>",
 "phase": "IMPLEMENTING", "head": "<40 hex>",
 "checkpoints": {"CP1": "COMPLETE", "CP2": "IN_PROGRESS"}}
```

`head` and `checkpoints` are informational. They let `reconcile` compare
with no Workflow-side history. Staleness is decided by `state_identity`
alone.

`next-action --expect-state-identity <hex>` refuses with `stale_decision`
when the current identity differs. The orchestrator calls this immediately
before launching. That closes the gap the Controller has today for the
**state**: a decision is taken and the launch happens later with no check
in between.

The check covers the state only. Some catalogue rows also read inputs
outside the state: the feedback file, the `REJECTED` marker, the worktree
(the publication status and dirty protected paths) and
`FUNCTIONAL_REVIEW.md`. A change to those inputs after the decision, for
example a `BLOCK` pasted into the feedback file, is not a `stale_decision`.
It is still caught, because every command re-checks its own preconditions
when it runs, and `reconcile` re-decides from the new inputs. v1 adds no
digest over these inputs (LPR-R1-008, section 11).

### D-OP-Describe: `describe`

`describe` reads nothing from the repository except to confirm that it
exists. It returns:

- `workflow_release`;
- `protocol_version`;
- `supported_protocol_majors: [1]`;
- `supported_governing_versions: ["1","2.1","2.2"]`, the module constant
  `SUPPORTED_GOVERNING_VERSIONS`. It is the single source of this list and
  of the catalogue's totality enumeration (CP4), never a repository's
  `WORKFLOW_CONFIG.json`, whose `default_config()` lists only
  `["1","2.1"]` until activation (`workflow_state.py:9282`). A test pins it
  to `sorted({"1"} | workflow_state.TWO_STAGE_PLAN_REVIEW_VERSIONS)`
  (LPR-R4-003);
- `capabilities: {operations, dispositions, action_ids, artifact_kinds,
  external_result_kinds, reserved_result_kinds, error_codes}`.

Every list is sorted. A test pins each list against the module's own tables,
so the description cannot drift from what the code does.

### D-OP-Verify: `verify`

`verify` is read-only and never takes the state lock for writing. It returns
`{healthy: bool, checks: [{id, status: "pass"|"fail"|"skip", detail}]}`
with these checks, in order:

1. `state_readable`: the state file and the config parse.
2. `state_valid`: `validate_state(state, repo_root=…)` passes. This
   includes the registry-to-mirror `plan_revision` check, and it is
   `validate_state`'s first production caller.
3. `config_valid`: `validate_config` passes.
4. `active_item_resolvable`: `active_work_item_id` is null or names a
   non-terminal item.
5. `checkpoint_completions_provable`, for each non-terminal item with
   `COMPLETE` checkpoints: `verify_checkpoint_completions` passes.
6. `installation_release_matches`: when `.workflow-manager/installation.json`
   exists, its `workflow_version` equals `WORKFLOW_RELEASE`. This check is
   `skip` when the file is absent.
7. `protocol_ready`: checks 1-4 passed.

`verify` does not check installation digests. That is `workflow-manager
verify`'s job, and the spec says so. A failing check gives `healthy:
false` with `ok: true`. `verify` returns `ok: false` only for
`unsupported_protocol` or `invalid_request`. An unreadable state is
reported by check 1, not refused.

### D-OP-Next: `next-action` and the action catalogue

`next-action [--work-item ID] [--expect-state-identity HEX]` reads the
state without a write lock and returns:

```json
{"basis": { "...": "D-OP-Identity" },
 "snapshot": {"phase": "…", "governing_workflow_version": "…", "work_item_type": "…",
              "plan_revision": 1, "implementation_revision": null,
              "current_checkpoint_id": null, "next_checkpoint_id": "CP2",
              "registry_complete": false, "plan_approval": "CURRENT|STALE|null",
              "technical_approval": "…", "plan_review_publication_status": "BOUND|…|null"},
 "disposition": "automatic|validation|human_gate|external_gate|blocked|complete",
 "action": {"id": "implementation.checkpoint", "arguments": {"work_item_id": "…", "checkpoint_id": "CP2"},
            "invocation": "/milestone-implement orchestration-protocol-v1",
            "worker": {"role": "implementer", "fresh_session": false,
                       "independent_of": [], "user_only": false},
            "allowed_results": ["progress", "no_progress"]},
 "satisfied_by": null,
 "alternatives": [],
 "reason": {"code": "…", "text": "…", "remedy": null}}
```

- `action` is `null` for `complete`, and for a `blocked` row that has no
  resume action.
- `satisfied_by` names an `external_result_kind` for an `external_gate`.
- `alternatives` lists the other legal actions at a gate. Examples are the
  optional advisory `/review-implementation`, and at the functional gate
  `milestone.accept` beside `functional.apply_findings`.
- `invocation` is the rendered command. It is never the identity: an
  orchestrator dispatches on `action.id`.
- `worker.role` is one of `planner`, `implementer`, `self_reviewer`,
  `independent_reviewer`, `applier`, `user` or `external`.
- `independent_of` lists the roles whose sessions the worker must not
  share.

When no id is given and there is no active item, the result has no `basis`,
and the action is `plan.start` (`/milestone-plan`, automatic). Its
`snapshot` is `{"work_item_ids": [...]}`, the sorted keys of `work_items`
at decision time, which `reconcile` uses to find the new item
(LPR-R2-005). `/milestone-plan` creates the item at the config's
`default_workflow_version` (`load_config`), but only when that version is
two-stage. Its `"1"` branch is v1-inert ("no
`WORKFLOW_STATE.json`/`WORKFLOW_CONFIG.json` reads or writes beyond the one
just performed", `milestone-plan.md` step 0), and the only creating call,
`route_work_item`, is a `[2.1]` sub-step of its step 1. A `"1"` default
therefore gives row 1a, `blocked`, and never `plan.start` (LPR-R3-001).

**`"1"` items.** The protocol drives a `"1"` item only once it already has
a `work_items` entry. 2.6.0 creates one in three ways: a remediation child
created while the config default is `"1"` (`create_remediation_child_work_item`),
a legacy import (`import_legacy_work_item`), and the bootstrap's
`workflow-v2-1-core`. Their `"1"` commands are v1-inert, so they differ
from the two-stage branches in what they write, not only in which review
protocol they use. Two `"1"` states cannot be advanced by any 2.6.0
command:

- **`PLANNING` and `AMENDING_PLAN`**: `/milestone-plan`'s `"1"` branch
  writes no state, so no `"1"` command publishes the plan.
  `apply-functional-review.md` says a `"1"` remediation child reaches
  `AWAITING_EXTERNAL_PLAN_REVIEW` through `publish_plan_revision`'s `"1"`
  branch, but no `"1"` command at `PLANNING` makes that call.
- **`IMPLEMENTING`**: `/milestone-implement`'s `"1"` branch runs every
  checkpoint in one invocation (its step 1), with no
  `complete_checkpoint` or `enter_self_reviewing_implementation` write
  (both are `[2.1]` only). Its step 4 then calls
  `record_bundle_generation(stage="implementation")`, whose only legal
  source phase is `SELF_REVIEWING_IMPLEMENTATION`
  (`BUNDLE_GENERATION_LEGAL_SOURCE_PHASES_BY_STAGE`). From `IMPLEMENTING`
  it refuses with `IllegalBundleGenerationSourcePhaseError`, which this
  revision reproduced against `payload/scripts/workflow_state.py`.

Both are 2.6.0 defects, recorded as `v2.6.0-003`: CP7 adds its roadmap
row, and its write-up joins `v2.6.0-001`/`-002` in `workflow-manager`'s
`docs/defects/` (section 7, item 5). They are not fixed in W1, because the fix changes the `"1"` commands' v1-inert
contract and their golden-output test (`WF8a-ii`) (`OD-W1-10`). Row 6a
reports both states as `blocked` with reason `v1_state_not_advanced`, so
the catalogue never emits an automatic action that the command cannot
complete. The other `"1"` states are drivable: the external plan round
(rows 17-21), the implementation review (rows 31-35), `APPLYING_REVIEW_FEEDBACK`,
the functional review and acceptance. "The registry is incomplete" is
never evaluated for a `"1"` item as a reason to implement: rows 23 and 24
are `2.1`/`2.2` only. At the functional gate, row 38b reports a `"1"` item
whose registry is not terminal as `blocked` (`v1_state_not_advanced`),
because `/accept-milestone` can never accept it; it is the same gap seen at
acceptance, since no `"1"` command writes checkpoint statuses, and it joins
`v2.6.0-003` (LPR-R4-004). Row 38c is its `2.1`/`2.2` counterpart, reached
by a legacy promotion: no 2.6.0 command completes an outstanding checkpoint
from `AWAITING_FUNCTIONAL_REVIEW` at any `gv`, and that case is recorded
beside `v2.6.0-003` too (LPR-R6-001).

**The catalogue.** It is total over every persisted phase and every
supported governing version (`gv`). **The printed order is the evaluation
order**: the rows are tried from top to bottom, across phases, and the
first row whose phase, `gv` and condition all match wins. No other
precedence rule exists. A row that pre-empts another (a block, a `BLOCK`
verdict, an unreachable gate) is printed above it. CP4 builds the
catalogue as this one ordered table, and CP6 tests that the specification's
Markdown table equals the code's, row for row and in order. A test
enumerates `KNOWN_PHASES` × `SUPPORTED_GOVERNING_VERSIONS` and asserts that every
state reaches an explicit row; nothing falls through to an implicit
default.

**A condition that raises** (LPR-R4-002, LPR-R5-001). A row's condition is
made of one or more **calls** to Workflow functions. Every call has exactly
one of three **kinds**, and the kind decides what an exception from that
call means:

- a **guard** call: the refusal *is* the condition. The row lists the
  exception classes that make it true ("`assert_bundle_not_rejected`
  refuses" is `BundleRejectedError`). A listed class means "the condition
  is true": the row matches;
- an **acceptance** call: an `assert_*` function used as a test, whose
  refusal means "the condition is false". The row lists the exception
  classes that mean "false": a listed class makes the call's sub-condition
  false, and evaluation continues exactly as for any false condition (the
  row does not match, unless its condition is the negation, and the next
  row is tried);
- a **value** call: a function that returns the value the condition tests
  (a publication status, a gate wrapper, `implementing_entry_status`,
  `registry_completion_status`, `select_next_checkpoint`,
  `resolve_own_registry_completion_status`,
  `discover_current_functional_checklist_evidence`, the verdict parser, the
  computation of **P** or **I**). It raises only on a data-integrity
  problem. A row may still list named classes for it, with their own reason
  (row 38a).

The rule for every call is then:

- a Workflow exception (D-OP-Errors' domain) whose class the row lists for
  that call has the listed meaning: true for a guard call, false for an
  acceptance call, the named reason for a value call;
- any other Workflow exception, from a call of any kind, ends the
  evaluation at that row. The decision is `blocked`, `action` is `null`,
  the reason is `condition_refused`, with the exception's class and message
  in `reason.text` and in a `native` field of `reason` shaped like the
  envelope's. It is never a fall-through to a later row and never an
  `ok: false` envelope, because the state was read and a decision was made;
- an exception that is not a Workflow exception is not caught by the
  catalogue. It propagates to the envelope writer and becomes
  `internal_error`, exit 1.

**The kinds are data, not prose.** `workflow_protocol.py` holds one table,
`CONDITION_CALLS`, keyed by row id. Each entry lists the row's calls in
evaluation order as `{function, kind, classes}`, where `classes` is the
list of exception class names with the meaning above (empty for a value
call with no named reason). The catalogue's predicates evaluate a call only
through this table's entry, so a call cannot be made without a declared
kind. A row with no condition has an empty entry. The table, by row (calls
that never raise outside the D-OP-Errors domain, such as comparing two
parsed ids, are not calls and are not listed):

| row(s) | call | kind | classes |
| --- | --- | --- | --- |
| 1, 1a | `load_config` | value | — |
| 5 | `plan_review_publication_status` | guard | `PlanReviewBindingInconsistentError` |
| 6 | `assert_bundle_not_rejected` | guard | `BundleRejectedError` |
| 7a | `plan_review_publication_status` (its `status`), the verdict parser, `assert_apply_plan_review_feedback`, then `assert_apply_review_feedback_binding` with `stage="plan"` (only when the previous call returned `"bundle"`) | value, value, acceptance, then guard | —; —; `FeedbackStatusNotApplicableError`, `FeedbackNotForConsumedContentError`; `MissingRequiredBundleFileError`, `ReviewBundleManifestMismatchError` |
| 8 | `plan_review_publication_status` (its `status`, the acceptance call's `publication_status` input), the verdict parser, then `assert_apply_plan_review_feedback` | value, value, then acceptance | —; —; `FeedbackStatusNotApplicableError`, `FeedbackNotForConsumedContentError` |
| 8 | `assert_apply_review_feedback_binding` with `stage="plan"` (only when the previous call returned `"bundle"`) | acceptance | `FeedbackContentMismatchError`, `FeedbackBundleMismatchError`, `MissingFeedbackBindingFieldError` |
| 8a | `plan_review_publication_status` (its `status`), the verdict parser, `assert_apply_plan_review_feedback`, then `assert_apply_review_feedback_binding` with `stage="plan"` (only when `assert_apply_plan_review_feedback` returned `"bundle"` and the binding's selection is `"bundle"`: a legacy marker, or a `REVISE` that states no `review_content_id`) | value, value, acceptance, then guard | —; —; `FeedbackStatusNotApplicableError`, `FeedbackNotForConsumedContentError`; `FeedbackBundleMismatchError`, `MissingFeedbackBindingFieldError` |
| 10 | `plan_review_publication_status` | value | — |
| 11, 13 | the verdict parser and **P** (fb is current, two-stage) | value | — |
| 11a | the verdict parser and **P** (when at `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`), then `assert_local_generation_matches` | value, then guard | —; `WorktreeOrHeadMismatchError` |
| 15, 16 | `plan_approval_gate_status` | value | — |
| 16a | `compute_bundle_id` over the plan bundle (**B**) | guard | `MissingRequiredBundleFileError` |
| 17-20, 20a | the verdict parser, **B**, then `assert_feedback_matches_bundle` (fb is current, `"1"` plan stage) | value, value, acceptance | —; —; `FeedbackBundleMismatchError`, `MissingFeedbackBindingFieldError` |
| 19, 20, 20a | `plan_approval_gate_status` | value | — |
| 22 | `implementing_entry_status` | value | — |
| 23 | `registry_completion_status`, `select_next_checkpoint` | value | — |
| 25, 27 | the verdict parser and **I** (fb is current, `2.2` implementation stage) | value | — |
| 25a | the verdict parser and **I** (when at `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`), then `assert_local_generation_matches` | value, then guard | —; `WorktreeOrHeadMismatchError` |
| 25b | `verify_implementation_review_bundle` (at both phases, whatever fb holds) | guard | `ImplementationReviewBundleUnverifiedError` |
| 29, 30 | `technical_approval_gate_status` | value | — |
| 30a | `compute_bundle_id` over the implementation bundle (**B**) | guard | `MissingRequiredBundleFileError` |
| 31-35, 31a | the verdict parser, **B**, then `assert_feedback_matches_bundle` (fb is current, `"1"`/`"2.1"` implementation stage) | value, value, acceptance | —; —; `FeedbackBundleMismatchError`, `MissingFeedbackBindingFieldError` |
| 31, 31a | `is_technical_review_block_pinned` | value | — |
| 33, 34, 35 | `technical_approval_gate_status` | value | — |
| 35a | the verdict parser, then `assert_apply_review_feedback_binding` with `stage="implementation"` (`/apply-implementation-review`'s step-1 binding, at every `gv`; content at `2.2` for a `REVISE` that states a `review_content_id`, bundle otherwise) | value, then value with named reasons | —; `MissingRequiredBundleFileError`, `ReviewBundleManifestMismatchError` (`bundle_unverified`), `FeedbackContentMismatchError`, `FeedbackBundleMismatchError`, `MissingFeedbackBindingFieldError` (`review_feedback_not_current`). No fb is tested on the parser's result (`review_feedback_missing`), and the binding is called only when fb is present, matching the command's order |
| 37 | `discover_current_functional_checklist_evidence` | value | — |
| 38 | `resolve_feedback_dir`, then `assert_functional_review_not_already_consumed` | value, then acceptance | —; `FunctionalReviewAlreadyAppliedError` |
| 38a | `resolve_own_registry_completion_status` | value, with named reasons | `StalePlanApprovalRegistryReadError` (`plan_content_drifted`), `RegistryCoverageError` (`registry_unreadable`) |
| 38b, 38c, 39 | `resolve_own_registry_completion_status` | value | — |

Every other row (2, 3, 4, 6a, 7, 9, 12, 14, 21, 24, 26, 28, 36, 40) has no
call. The acceptance classes are exactly the classes the called function
raises for "this feedback does not apply here": `assert_apply_plan_review_feedback`
raises `FeedbackStatusNotApplicableError` for a status other than
`REVISE` and `FeedbackNotForConsumedContentError` for feedback of another
round (`workflow_state.py`, `assert_apply_plan_review_feedback`);
`assert_feedback_matches_bundle` raises `MissingFeedbackBindingFieldError`
for an absent binding field and `FeedbackBundleMismatchError` for a
mismatched one (`workflow_fingerprint.py:3397`), and
`assert_apply_review_feedback_binding` (D-Apply-Binding) raises those two
from its bundle binding and `FeedbackContentMismatchError` from its content
binding; `assert_functional_review_not_already_consumed` raises
`FunctionalReviewAlreadyAppliedError` for consumed content
(`workflow_fingerprint.py:2240`). The binding's two bundle-integrity
classes, `MissingRequiredBundleFileError` and
`ReviewBundleManifestMismatchError`, are not acceptance classes: they say
nothing about fb, so they are a guard (row 7a) or a named reason (row 35a).
This is how rows 9, 20, 21, 35 and 39
are reached: a `"1"` `REVISE` that `/apply-plan-review` has applied no
longer matches the regenerated **B**, so "fb is current" is false and row
20 matches; a withdrawal that leaves a `REVISE` of other content or an
`APPROVE` in fb makes row 8 false and row 9 match; a two-stage `REVISE`
for the consumed content is accepted by the content binding whatever its
bundle fields say, so it gives row 8 and never reaches row 9 (MPR-R8-001,
MPR-R9-001); a consumed `FUNCTIONAL_REVIEW.md` makes row 38 false.

**Every call is declared at every row that uses it** (LPR-R6-003). An
implementation may compute a value once per evaluation and reuse it (row 5
and row 8 both read `plan_review_publication_status` at `REVISING_PLAN`),
but the table still lists the call at each row whose condition depends on
it. CP4's recorder test checks the declared set per row, not the number of
invocations: a row passes when every function it reaches, freshly computed
or reused, is in its own entry.

`condition_refused` and the named reasons are reason codes like every
other row's. They add no error code, because the envelope is `ok: true`.

Terms used in the conditions:

- **fb** is the item's `<feedback_dir>/REVIEW_FEEDBACK.md`, read with the
  Workflow's verdict parser (`parse_review_feedback_header`, CP1). An absent
  file, or one whose `Work item:` names another item, is "no fb".
- **P** is the fresh plan-stage `review_content_id`
  (`plan_review_publication_status`'s `fresh_review_content_id`). **I** is
  the current implementation-stage `review_content_id`, computed the way
  `/approve-review` computes it. **B** is the `bundle_id` recomputed over
  the stage's resolved bundle directory (`resolve_bundle_dir`, with
  `stage="plan"` at plan-stage phases).
- **fb is current** means, by stage and `gv` (LPR-R1-005):
  - two-stage plan phases (`2.1`, `2.2`): fb's `review_content_id` equals
    **P**. Its `bundle_id` is not compared, because both plan-stage ingests
    treat it as advisory, so a wrapper-only regeneration leaves fb current;
  - two-stage implementation phases (`2.2`): fb's `review_content_id`
    equals **I**, for the same reason;
  - the `"1"` plan stage and the `"1"`/`"2.1"` implementation stage:
    `assert_feedback_matches_bundle` against **B**, the item's
    `base_commit` and its id accepts fb. This is the binding
    `/approve-review` and `/apply-*-review` apply there.
- **an unrecorded manual verdict** is a current fb whose `Reviewer role:`
  normalizes to the stage's `MANUAL_EXTERNAL_*_REVIEW`, whose `Status:` is
  `APPROVE` or `REVISE`, and for whose content the ledger records no manual
  stage. A current `BLOCK` is matched by an earlier row.
- **the plan gate status** and **the technical gate status** are the two
  repository-aware wrappers CP4 adds (LPR-R1-003, below). Each returns
  `reachable` and, when it is false, one `cause`.
- **the generation check** is
  `assert_local_generation_matches(repo_root, <bundle_dir>/MANIFEST.md)`
  over the stage's resolved bundle directory: it refuses when the live
  worktree root or HEAD differs from `MANIFEST.md`'s `worktree_root` /
  `generation_head` (LPR-R2-002).
- **pinned** is `is_technical_review_block_pinned(work_item, B)` at the
  implementation stage.
- **the implementation bundle verifier** is
  `verify_implementation_review_bundle(repo_root, work_item_id)`, a new
  read-only function in `workflow_state` (CP4, LPR-R5-002). It performs
  `/review-implementation` step 4's bundle check as one function, over
  the item's resolved implementation-stage bundle directory: `MANIFEST.md`
  is present; `compute_bundle_id` succeeds (a `MissingRequiredBundleFileError`
  for an absent or incomplete directory is chained); the recomputed
  `bundle_id` equals `read_manifest_identifiers`' `bundle_id`; and the
  manifest's `review_content_id` equals **I**, computed commit-source
  exactly as step 4 names (`approval_review_content_id(...,
  stage="implementation", base_commit=work_item["base_commit"],
  head="HEAD")`). Any failure raises `ImplementationReviewBundleUnverifiedError`,
  naming the bundle path, the failing comparison and both values, and the
  stale-plan-stage-manifest variant by name when the manifest records
  `stage: plan`. It returns `{bundle_id, review_content_id}`. It does not
  compare the archive: step 4 does not, and the implementation stage has
  no bind that reads it. `assert_local_generation_matches` stays a
  separate call, because it catches a different failure (step 4 says so).
- **regenerate the implementation bundle** names the stage of the round
  being regenerated (LPR-R6-004): `./scripts/prepare-ai-review.sh <base>
  <stage> <id>`, with `<stage>` `implementation` when the item's
  `implementation_revision` is `1` (the first generation) and `post-fix`
  when it is greater. `record_bundle_generation` advances the revision only
  on an `ordinary` outcome (`workflow_state.py`, `record_bundle_generation`),
  so a same-content republication keeps the round's stage. The stage is
  not read from `MANIFEST.md`: the implementation-stage manifest always
  states `stage: implementation`
  (`render_manifest_md_implementation_stage`), and only `CHANGED_FILES.txt`'s
  `stage:` line records the stage the generator was given. The remedy text
  carries the computed command.
- **the implementing entry status** is `implementing_entry_status(repo_root,
  work_item, base_commit)`, a new function in `workflow_state` (CP4) that
  returns `{"reachable": bool, "cause": str | None}` and evaluates
  `implementing_entry_reachable`'s three conditions in the same order. The
  causes are: `plan_approval_not_current` (no record, or its status is not
  `CURRENT`), `plan_approval_commit_unreachable`
  (`discover_plan_approval_commit` finds none, or it is not an ancestor of
  HEAD), and `plan_content_drifted` (`approval_is_current` is false).
  `implementing_entry_reachable` becomes `implementing_entry_status(...)["reachable"]`,
  so `/milestone-implement`'s 1a and row 22 call the same function, and the
  existing tests of `implementing_entry_reachable` stay (LPR-R3-002).

Row ids are stable labels, not positions. A row added in a later revision
gets a letter suffix (`11a`), so that existing references stay valid; the
printed order is still the evaluation order.

| # | phase | gv | condition | disposition | action id | invocation and notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | — | — | no id given, no active item, and `load_config`'s `default_workflow_version` is `2.1` or `2.2` | automatic | `plan.start` | `/milestone-plan` |
| 1a | — | — | no id given and no active item (the default is `"1"`) | blocked | — | reason `plan_start_not_tracked`; remedy: a `"1"` `/milestone-plan` creates no work item, so activate a two-stage `default_workflow_version`, or run the `"1"` milestone outside the protocol (LPR-R3-001) |
| 2 | `SELF_REVIEWING_PLAN`, `AWAITING_TECHNICAL_APPROVAL`, `FIXING_FUNCTIONAL_FINDINGS`, `AWAITING_USER_ACCEPTANCE` | all | — (a vocabulary-only phase is persisted) | blocked | — | reason `invalid_state` |
| 3 | `LEGACY_READY` | all | — | blocked | — | reason `legacy_item_not_activated` |
| 4 | `REVISING_PLAN`, `AWAITING_PLAN_APPROVAL`, `AWAITING_LOCAL_PLAN_REVIEW`, `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` at `1`; `AWAITING_EXTERNAL_PLAN_REVIEW` at `2.1`/`2.2`; `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` at `1`/`2.1`; `SELF_REVIEWING_IMPLEMENTATION` at `1` | as listed | — (no writer persists the phase at that `gv`) | blocked | — | reason `phase_not_legal_for_governing_version` |
| 5 | `PLANNING`, `AMENDING_PLAN`, `REVISING_PLAN`, `AWAITING_LOCAL_PLAN_REVIEW`, `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`, `AWAITING_PLAN_APPROVAL` | 2.1, 2.2 | `plan_review_publication_status` raises `PlanReviewBindingInconsistentError` (its rows 4d and 6) | blocked | — | reason `plan_review_binding_inconsistent`; the remedy is the error's own (row 4d: withdraw with `/milestone-plan <id>`) |
| 6 | every review phase: `AWAITING_LOCAL_PLAN_REVIEW`, `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`, `AWAITING_PLAN_APPROVAL`, `AWAITING_EXTERNAL_PLAN_REVIEW`, `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`, `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`; and the two apply phases, `REVISING_PLAN` and `APPLYING_REVIEW_FEEDBACK` | all | `assert_bundle_not_rejected` refuses | blocked | — | reason `bundle_rejected`; the remedy is the marker's recorded detail; at a two-stage plan phase (including `REVISING_PLAN`), alternative `plan.withdraw` (`/milestone-plan <id>`, whose successful generation clears the marker, `clear_rejected_marker_if_present`). The apply phases are listed because `/apply-plan-review` and `/apply-implementation-review` call `assert_bundle_not_rejected` in their step 1, so without them rows 8 and 36 would emit an automatic action the command refuses (MPR-R7-001). `REVISING_PLAN` at `"1"` never reaches this row (row 4) |
| 6a | `PLANNING`, `AMENDING_PLAN`, `IMPLEMENTING` | 1 | — | blocked | — | reason `v1_state_not_advanced`; remedy: no 2.6.0 `"1"` command advances this state (defect `v2.6.0-003`); the text names the failing writer (`/milestone-plan` writes no state; `record_bundle_generation` refuses from `IMPLEMENTING`) (LPR-R3-001) |
| 7 | `PLANNING`, `AMENDING_PLAN` | 2.1, 2.2 | — | automatic | `plan.author` | `/milestone-plan <id>` |
| 7a | `REVISING_PLAN` | 2.1, 2.2 | fb is present, `assert_apply_plan_review_feedback` with the publication status accepts it and returns `"bundle"`, and `assert_apply_review_feedback_binding` raises `MissingRequiredBundleFileError` (computing **B** fails) or `ReviewBundleManifestMismatchError` (**B** differs from its `MANIFEST.md`'s `bundle_id`, or, under the content binding, the manifest names another work item, base commit or stage, or its `review_content_id` is not the consumed one, MPR-R9-001, MPR-R10-001) | blocked | — | reason `bundle_unverified`; the text names the failing comparison and both values; remedy: run from the worktree that holds the reviewed plan bundle, or restore its `.ai-review/<id>/current/`. Regenerating is not offered: the reviewed bundle is what fb binds to, and `/apply-plan-review` step 1 checks fb against it before any write. Alternative `plan.withdraw` (`/milestone-plan <id>`). Without this row, row 8's condition would end in `condition_refused` with no remedy. Under `"durable"` (publication rows 9 and 11) the on-disk bundle is not read, so this row never matches there (MPR-R7-001) |
| 8 | `REVISING_PLAN` | 2.1, 2.2 | fb passes `/apply-plan-review`'s own step-1 acceptance: `assert_apply_plan_review_feedback` with the publication status accepts it and, when that returns `"bundle"`, `assert_apply_review_feedback_binding` accepts it, by content for a `REVISE` that states a `review_content_id` (non-legacy marker) and by bundle otherwise (D-Apply-Binding). This covers the legacy marker, matched by `Work item:` only | automatic | `plan.apply_review` | `/apply-plan-review <id>`. A recorded `REVISE` with no `Reviewed bundle ID:`, or naming a bundle a wrapper-only regeneration replaced, matches here (MPR-R9-001) |
| 8a | `REVISING_PLAN` | 2.1, 2.2 | fb is a `REVISE` that names this item and that the content binding cannot bind, and the bundle binding refuses it: `assert_apply_plan_review_feedback` with the publication status accepts fb and returns `"bundle"`; `assert_apply_review_feedback_binding` selects the bundle binding, because the marker is legacy (`consumed.review_content_id` is `null`), fb states no `review_content_id`, or **B**'s manifest states no `work_item_id` (MPR-R10-001); and that binding refuses with `MissingFeedbackBindingFieldError` or `FeedbackBundleMismatchError` | blocked | — | reason `review_feedback_unbound`; the text names the failing field, fb's value (or "absent") and the expected one (**B**, the item's `base_commit`, its id), and says that fb cannot be bound to a round: it states no content, and its bundle fields do not name **B**. Remedy: a verdict for **B** from its reviewer, which states this round's `review_content_id` (the content binding then applies) or the three binding fields as the reviewer saw them. The verdict's binding fields are never to be edited to the printed values: they attest to what the reviewer reviewed (`REVIEW_PROTOCOL.md`, "Required structure"), and an edit would apply findings to a bundle the reviewer may not have seen (MPR-R9-001). Alternative `plan.withdraw` (`/milestone-plan <id>`), which discards fb knowingly. `remedy_commands` is the withdrawal only, since the remedy is a new verdict; `refusing_commands` is `/apply-plan-review`. Every two-stage writer of a `REVISE` states its `review_content_id` (`/review-plan` step 7, the ingest's required label), so only a legacy marker, an fb written by hand, or a manifest with no `work_item_id`, which no 2.6.0 plan-stage generator writes, reaches this row. The legacy match, by `Work item:` only, is inherited from 2.6.0's durable legacy check (`assert_apply_plan_review_feedback`) and accepts any `REVISE` naming the item; this row adds no hazard to it, because it blocks and offers no automatic action |
| 9 | `REVISING_PLAN` | 2.1, 2.2 | — (a withdrawal, or no applicable `REVISE`: fb is absent, is not a `REVISE`, or states a `review_content_id` other than the consumed one) | automatic | `plan.author` | `/milestone-plan <id>`. Accepted residual: no fb at all (a fresh worktree after a recorded `REVISE`, `.ai-review/` being untracked) also matches here; see the table notes (MPR-R8-002) |
| 10 | `AWAITING_LOCAL_PLAN_REVIEW`, `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`, `AWAITING_PLAN_APPROVAL` | 2.1, 2.2 | publication status `CONTENT_DRIFTED`, `BUNDLE_UNVERIFIED` or `LEGACY_UNVERIFIED` | blocked | — | reason is the status; the remedy is the status's own `remedy`; alternative `plan.withdraw` |
| 11 | `AWAITING_LOCAL_PLAN_REVIEW`, `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` | 2.1, 2.2 | fb is current and its `Status:` is `BLOCK` | human_gate | `review.resolve_block` | none; reason `review_blocked`; alternative `plan.withdraw`. A `BLOCK` writes no state, so without this row rows 12 and 13 would re-emit the review or record action forever |
| 11a | `AWAITING_LOCAL_PLAN_REVIEW`, `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` | 2.1, 2.2 | at `AWAITING_LOCAL_PLAN_REVIEW`, or at `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` when fb holds an unrecorded manual verdict: the generation check refuses | blocked | — | reason `bundle_generation_mismatch`; remedy: run from the generating worktree, or regenerate the plan bundle at the current HEAD (`./scripts/prepare-ai-review.sh <base> plan <id>`; a wrapper-only regeneration keeps the binding, its `bundle_id` advisory only); alternative `plan.withdraw`. `/review-plan` and `/record-manual-plan-review` refuse here with `WorktreeOrHeadMismatchError`, so without this row rows 12 and 13 would loop (LPR-R2-002) |
| 12 | `AWAITING_LOCAL_PLAN_REVIEW` | 2.1, 2.2 | — | automatic | `plan.review.local` | `/review-plan <id>`; role `independent_reviewer`, fresh session, independent of `planner` |
| 13 | `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` | 2.1, 2.2 | fb holds an unrecorded manual verdict | automatic | `plan.record_external` | `/record-manual-plan-review <id>` |
| 14 | `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` | 2.1, 2.2 | — | external_gate | `plan.review.external` | none; `satisfied_by: plan_review_verdict` |
| 15 | `AWAITING_PLAN_APPROVAL` | 2.1, 2.2 | the plan gate status is reachable | human_gate | `plan.approve` | `/approve-review plan <id>`; `user_only` |
| 16 | `AWAITING_PLAN_APPROVAL` | 2.1, 2.2 | — (the gate is unreachable) | blocked | — | reason is the gate's cause (`bundle_generation_mismatch`, `plan_review_bundle_unbound`, `no_review_round`, `review_blocked`, `review_ledger_stale`); alternative `plan.withdraw` |
| 16a | `AWAITING_EXTERNAL_PLAN_REVIEW` | 1 | computing **B** raises `MissingRequiredBundleFileError` (the plan bundle directory is absent or incomplete) | blocked | — | reason `bundle_unverified`; remedy: regenerate the plan bundle (`./scripts/prepare-ai-review.sh <base> plan <id>`). Without this row, "fb is current" would end in `condition_refused` at row 17 with no remedy (LPR-R5-002) |
| 17 | `AWAITING_EXTERNAL_PLAN_REVIEW` | 1 | fb is current and `BLOCK` | automatic | `plan.apply_review` | `/apply-plan-review <id>`; reason `review_blocked`. Its `"1"` path applies a `BLOCK` and then stays for another round (its step 6), so this is not a gate (LPR-R2-001, self-found) |
| 18 | `AWAITING_EXTERNAL_PLAN_REVIEW` | 1 | fb is current and `REVISE` | automatic | `plan.apply_review` | `/apply-plan-review <id>` |
| 19 | `AWAITING_EXTERNAL_PLAN_REVIEW` | 1 | fb is current and `APPROVE`, and the plan gate status is reachable | human_gate | `plan.approve` | `/approve-review plan <id>`; `user_only` |
| 20 | `AWAITING_EXTERNAL_PLAN_REVIEW` | 1 | fb is not current and its `Status:` is `REVISE` (an applied `REVISE`, LPR-R1-004), and the plan gate status is reachable | human_gate | `plan.approve` | `/approve-review plan <id>`, `user_only` (basis `USER_OVERRIDE`); alternative `plan.review.external` (another round), `satisfied_by: plan_review_verdict` |
| 20a | `AWAITING_EXTERNAL_PLAN_REVIEW` | 1 | fb is current and `APPROVE`, or fb is an applied `REVISE` as in row 20 (the plan gate is unreachable) | blocked | — | reason is the gate's cause (`bundle_generation_mismatch`); alternative `plan.review.external` (another round) |
| 21 | `AWAITING_EXTERNAL_PLAN_REVIEW` | 1 | — (no fb, or a verdict for an earlier round) | external_gate | `plan.review.external` | none; `satisfied_by: plan_review_verdict` |
| 22 | `IMPLEMENTING`, `SELF_REVIEWING_IMPLEMENTATION` | 2.1, 2.2 | the implementing entry status is not reachable | blocked | — | reason is its cause: `plan_approval_not_current` (remedy: obtain a current plan approval), `plan_content_drifted` (remedy: restore the approved plan-stage bytes, or `/request-plan-amendment <id>`), or `plan_approval_commit_unreachable` (remedy: restore the history that contains the plan-approval commit). `/milestone-implement`'s 1a runs this check on every invocation at both phases (LPR-R3-002) |
| 23 | `IMPLEMENTING` | 2.1, 2.2 | the registry is incomplete (`registry_completion_status`) | automatic | `implementation.checkpoint` | `/milestone-implement <id>`; `arguments.checkpoint_id` is `select_next_checkpoint` |
| 24 | `IMPLEMENTING`, `SELF_REVIEWING_IMPLEMENTATION` | 2.1, 2.2 | — | automatic | `implementation.self_review` | `/milestone-implement <id>`; role `self_reviewer` |
| 25 | `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` | 2.2 | fb is current and `BLOCK` | human_gate | `review.resolve_block` | none; reason `review_blocked` |
| 25a | `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` | 2.2 | at `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, or at `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` when fb holds an unrecorded manual verdict: the generation check refuses | blocked | — | reason `bundle_generation_mismatch`; remedy: run from the generating worktree; alternative `implementation.recover_provenance` (`/recover-implementation-provenance <id>`, for an excluded-only commit past `generation_head`). Same reason as row 11a (LPR-R2-002) |
| 25b | `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` | 2.2 | the implementation bundle verifier refuses (at either phase, whatever fb holds) | blocked | — | reason `bundle_unverified`; remedy: regenerate the implementation bundle (the round's stage, as defined above). `/review-implementation` (step 4) and `/record-manual-implementation-review` (step 5) refuse an absent, incomplete or mismatched bundle, so without this row rows 26 and 27 would loop as `no_progress`, and row 28 would ask for an external verdict on a bundle that does not exist and whose ingest would refuse (LPR-R6-002). `.ai-review/` is gitignored while the state is tracked, so a fresh clone or a second worktree is in this state (LPR-R5-002) |
| 26 | `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` | 2.2 | — | automatic | `implementation.review.local` | `/review-implementation <id>`; role `independent_reviewer`, fresh session, independent of `implementer` and `self_reviewer` |
| 27 | `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` | 2.2 | fb holds an unrecorded manual verdict | automatic | `implementation.record_external` | `/record-manual-implementation-review <id>` |
| 28 | `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` | 2.2 | — | external_gate | `implementation.review.external` | none; `satisfied_by: implementation_review_verdict` |
| 29 | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 2.2 | the technical gate status is reachable | human_gate | `implementation.approve` | `/approve-review implementation <id>`; `user_only` |
| 30 | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 2.2 | — (the gate is unreachable) | blocked | — | reason is the gate's cause (`bundle_generation_mismatch`, `bundle_unverified`, `review_block_pinned`, `review_blocked`, `protected_path_dirty`, `implementation_provenance_stale`, `review_ledger_stale`); for `bundle_unverified`, remedy: regenerate the implementation bundle (the round's stage); for `bundle_generation_mismatch` and `implementation_provenance_stale`, alternative `implementation.recover_provenance` (`/recover-implementation-provenance <id>`); for `review_blocked` and `review_block_pinned`, alternative `implementation.apply_review` (`/apply-implementation-review <id>`, the documented late-fix re-entry at this terminal `"2.2"` phase, LPR-R2-001) |
| 30a | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 1, 2.1 | computing **B** raises `MissingRequiredBundleFileError` (the implementation bundle directory is absent or incomplete) | blocked | — | reason `bundle_unverified`; remedy: regenerate the implementation bundle (the round's stage, as defined above). `/apply-implementation-review` and `/approve-review` compute **B** in their first steps and refuse here (LPR-R5-002) |
| 31 | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 1, 2.1 | fb is current, and its `Status:` is `BLOCK` or the item is pinned | automatic | `implementation.apply_review` | `/apply-implementation-review <id>`; reason `review_blocked` or `review_block_pinned`. The command accepts a current `BLOCK`, pins it and remediates (its step 1), as the operator reference routes it; its post-fix republication changes **B**, which clears the pin's match (LPR-R2-001). Its step 1 stops on an absent or non-current fb, so the row requires a current fb even when pinned (LPR-R3-003) |
| 31a | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 1, 2.1 | pinned (fb is absent, not current, or names another item) | external_gate | `implementation.review.external` | none; reason `review_block_pinned`; `satisfied_by: implementation_review_verdict`; remedy: place the `BLOCK` feedback back, or obtain a new verdict for this bundle. Either one is a current fb, so the item then matches row 31 (LPR-R3-003) |
| 32 | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 1, 2.1 | fb is current and `REVISE` | automatic | `implementation.apply_review` | `/apply-implementation-review <id>` |
| 33 | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 1, 2.1 | fb is current and `APPROVE`, and the technical gate status is reachable | human_gate | `implementation.approve` | `/approve-review implementation <id>`; `user_only` |
| 34 | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 1, 2.1 | fb is current and `APPROVE` | blocked | — | reason is the gate's cause (`bundle_generation_mismatch`, `protected_path_dirty`, `implementation_provenance_stale`); alternative `implementation.recover_provenance` for those three |
| 35 | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | 1, 2.1 | — (no current fb) | external_gate | `implementation.review.external` | none; `satisfied_by: implementation_review_verdict`; alternative `implementation.review.local` (advisory); and, when fb is an applied `REVISE` (not current, `Status: REVISE`) and the technical gate status is reachable, alternative `implementation.approve` (`/approve-review implementation <id>`, `user_only`, basis `USER_OVERRIDE` by `resolve_approval_basis`), the implementation-stage counterpart of row 20 (LPR-R2-006) |
| 35a | `APPLYING_REVIEW_FEEDBACK` | all | `/apply-implementation-review`'s own step-1 acceptance fails: no fb, or `assert_apply_review_feedback_binding` with `stage="implementation"` refuses (D-Apply-Binding: at `2.2`, a `REVISE` that states a `review_content_id` is bound by content against **B** and its `MANIFEST.md`, whose `work_item_id`, `base_commit` and `stage` must name this item and the implementation stage; any other fb, every fb whose bundle's manifest states no `work_item_id`, and every fb at `1`/`2.1`, by `assert_feedback_matches_bundle` against **B**, the item's `base_commit` and its id) | blocked | — | reason by cause: `review_feedback_missing` (remedy: place the verdict being applied at the resolved `<feedback_dir>/REVIEW_FEEDBACK.md`, whose path the text prints, or run from the worktree that holds it), `bundle_unverified` (`MissingRequiredBundleFileError` or `ReviewBundleManifestMismatchError`; remedy: run from the worktree that holds the reviewed bundle, or restore its `.ai-review/<id>/` directory; when the manifest names another work item, the text says so, because the flat `.ai-review/current/` is shared, MPR-R10-001) or `review_feedback_not_current` (`FeedbackContentMismatchError`, `FeedbackBundleMismatchError` or `MissingFeedbackBindingFieldError`; remedy: place the verdict for the bundle being applied, as its reviewer wrote it, or obtain a new verdict for **B**). No remedy edits a verdict's binding fields (MPR-R9-001). The content binding compares fb with the manifest's `review_content_id`, not with **I**, because **I** moves as soon as the applier commits a fix, while **B** and its manifest stay the reviewed ones until the round's `post-fix` exit. No regeneration is offered: a `post-fix` generation from this phase is the round's exit (`BUNDLE_GENERATION_LEGAL_SOURCE_PHASES_BY_STAGE`), so it would end the round without applying the findings. `remedy_commands` is empty, since every remedy restores a file. `.ai-review/` is untracked, so a fresh worktree is in this state (MPR-R7-001) |
| 36 | `APPLYING_REVIEW_FEEDBACK` | all | — (fb is present and `assert_apply_review_feedback_binding` accepts it, and no `REJECTED` marker: rows 6 and 35a pre-empt the rest) | automatic | `implementation.apply_review` | `/apply-implementation-review <id>` (`OD-W1-8`) |
| 37 | `AWAITING_FUNCTIONAL_REVIEW` | all | no current checklist evidence | automatic | `functional.prepare` | `/prepare-functional-review <id>` |
| 38 | `AWAITING_FUNCTIONAL_REVIEW` | all | `<feedback_dir>/FUNCTIONAL_REVIEW.md` exists and `assert_functional_review_not_already_consumed` accepts it | automatic | `functional.apply_findings` | `/apply-functional-review <id>` |
| 38a | `AWAITING_FUNCTIONAL_REVIEW` | all | `resolve_own_registry_completion_status`, `/accept-milestone`'s own step-2a pre-flight, raises | blocked | — | `StalePlanApprovalRegistryReadError` (no `CURRENT` `plan_approval`, no `review_content_manifest`, or a plan-stage protected path that differs from the approved snapshot, `_assert_registry_covered_by_current_plan_approval`): reason `plan_content_drifted`, remedy: restore the approved plan-stage bytes. If the content change is wanted, the text says that 2.6.0 has no in-phase route to amend the plan from `AWAITING_FUNCTIONAL_REVIEW`: `/request-plan-amendment` refuses here (`_AMENDMENT_REQUEST_ALLOWED_PHASES` is `{"IMPLEMENTING", "SELF_REVIEWING_IMPLEMENTATION"}`, `workflow_state.py:13378`), unlike row 22, whose phases are exactly the amendment's (LPR-R6-001). `RegistryCoverageError` (the declared registry cannot be resolved, read or parsed, or names a foreign `work_item_id`): reason `registry_unreadable`, remedy: restore the item's own `registry_path` file. Any other Workflow exception: `condition_refused`. Alternative `functional.review.advisory`. `/accept-milestone` reports the same error and stops, so `milestone.accept` is never offered here (LPR-R4-002) |
| 38b | `AWAITING_FUNCTIONAL_REVIEW` | 1 | `resolve_own_registry_completion_status` reports the registry not terminal | blocked | — | reason `v1_state_not_advanced`; remedy: no `"1"` command writes checkpoint statuses, so `/accept-milestone` can never pass its pre-flight for this item (defect `v2.6.0-003`). Alternatives `functional.apply_findings` and `functional.review.advisory`, neither of which makes the registry terminal. Reachable only from a pre-constructed or imported entry (LPR-R4-004) |
| 38c | `AWAITING_FUNCTIONAL_REVIEW` | 2.1, 2.2 | `resolve_own_registry_completion_status` reports the registry not terminal | blocked | — | reason `registry_incomplete`; remedy: none exists in 2.6.0. No 2.6.0 command completes an outstanding checkpoint from `AWAITING_FUNCTIONAL_REVIEW` at `2.1`/`2.2`: `/milestone-implement` cannot start one here (`CHECKPOINT_START_LEGAL_PHASES` is `{"IMPLEMENTING"}`, `workflow_state.py:4550`), `/request-plan-amendment` refuses at this phase (`workflow_state.py:13378`), `/apply-functional-review`'s bounded branch returns through implementation review (`bundle_generation_target_phase("post-fix", gv)`, never `IMPLEMENTING`) to this same row, and its broad branch never touches the parent's registry. The text names the reachable origins, a legacy promotion (`promote_legacy_work_item` writes this phase at `"2.1"` for an imported item) or a hand-constructed state, since ordinary flow cannot leave `IMPLEMENTING` with a checkpoint outstanding, and names the defect `v2.6.0-003`, beside which the case is recorded (CP7, section 7). Alternatives `functional.apply_findings` and `functional.review.advisory`, for the functional findings only; neither makes the registry terminal. `milestone.accept` is never offered, because `/accept-milestone` step 2a refuses (LPR-R5-003, LPR-R6-001) |
| 39 | `AWAITING_FUNCTIONAL_REVIEW` | all | — (the registry is terminal: rows 38a, 38b and 38c pre-empt every other outcome of `resolve_own_registry_completion_status`) | human_gate | `functional.review` | none; alternatives are `milestone.accept` (`/accept-milestone`, `user_only`), `functional.apply_findings` and the optional `functional.review.advisory`. A registry-less item is terminal by that function, so a registry-less `"1"` item lists `milestone.accept` (LPR-R3-001, LPR-R4-004, LPR-R5-003) |
| 40 | `MILESTONE_COMPLETE` | all | — | complete | — | — |

Notes on the table:

- **Row 4** is grounded in `TestPersistedPhaseWriterCensus.EXPECTED_WRITERS`:
  every writer of the four two-stage plan phases is two-stage, the
  `AWAITING_EXTERNAL_PLAN_REVIEW` writer is `publish_plan_revision`'s
  `"1"` branch, and the two two-stage implementation phases are written by
  `"2.2"`-only writers. In particular, `REVISING_PLAN` at `"1"` is a state
  no `"1"` item persists, so the catalogue has no `"1"` row for it
  (LPR-R1-004). The `"1"` round is rows 17-21 instead.
  `SELF_REVIEWING_IMPLEMENTATION` at `"1"` is grounded in the commands, not
  the census: its two writers, `complete_checkpoint` and
  `enter_self_reviewing_implementation`, are not version-gated in code, but
  only `/milestone-implement`'s `[2.1]` steps call them (LPR-R3-001).
- **Row 20** is how a `"1"` round tells an applied `REVISE` from an
  unapplied one (LPR-R1-004). Before the apply, fb's `Reviewed bundle ID`
  equals **B**, so row 18 matches. `/apply-plan-review` advances the
  revision and regenerates the plan bundle, so afterwards **B** differs and
  row 18 no longer matches: the apply is never re-emitted. The test uses
  only the required binding fields. It needs no round identifier, which a
  `"1"` round does not have. The row is the `REVISING_PLAN` exit of
  `MILESTONE_WORKFLOW.md`: a `REVISE` round reaches the approval gate, and
  `/approve-review plan` resolves the basis as `USER_OVERRIDE`. The user can
  instead ask for another external round (the alternative). One residual is
  accepted: a bundle regenerated by hand without applying the `REVISE` also
  matches row 20. That can only offer a user-only gate, never an automatic
  action, and the user sees the unapplied findings in fb.
- **Rows 8, 8a and 9: a recorded `REVISE` never reaches `plan.author`**
  (MPR-R8-001, MPR-R9-001). The choice is normative: a two-stage `REVISE`
  is applied by content (D-Apply-Binding), as it was recorded, so a
  recorded `REVISE` gives row 8 whatever its optional bundle fields say,
  and the two-stage ingest keeps those fields optional (D-OP-External).
  Row 8a blocks only an fb the content binding cannot bind: one under a
  legacy marker, one that states no `review_content_id`, which no
  two-stage writer produces, or one whose bundle's manifest states no
  `work_item_id`, which no 2.6.0 plan-stage generator writes
  (MPR-R10-001). A `REVISE` that states the consumed
  `review_content_id` is a verdict for the round being applied, and the
  content binding applies it. That includes one sequence that is not the
  recorded round (MPR-R9-002): a `REVISE` of the content under review that
  was left in fb **unrecorded** (a manual `REVISE` pasted at
  `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` but never recorded, or a
  `/review-plan` `REVISE` whose state write crashed after its file write),
  followed by a withdrawal with `/milestone-plan <id>`.
  `withdraw_plan_review` consumes `bound.review_content_id`
  (`workflow_state.py:15399`), which is that `REVISE`'s id, and the
  generator refuses consumed content (`_assert_not_consumed`), so the
  on-disk bundle is still the one for that content. The item gives row 8,
  and `/apply-plan-review` applies a genuine verdict for the withdrawn
  content, which 2.6.0's `/apply-plan-review` would also have accepted
  when its bundle fields named **B**. That is safe: the applied content
  still needs a local and a manual `APPROVE` of its own. A `REVISE` left in
  fb from an earlier round states a different id, so the content binding
  refuses it with `FeedbackContentMismatchError`, and it gives row 9.
  The residual
  row 9 does accept (MPR-R8-002): with **no fb at all** at `REVISING_PLAN`
  (a fresh worktree after a recorded `REVISE`, `.ai-review/` being
  untracked), row 9 re-authors without the findings. The state cannot tell
  this from a withdrawal: `_write_consumed_plan_review_binding` writes the
  same `CONSUMED` record for both (`workflow_state.py:15245`), and
  `withdraw_plan_review` leaves `plan_review_stages` untouched (`:15399`),
  so a block here would also block every withdrawal. No gate is bypassed:
  the next bind consumes the round, and the re-authored content still
  needs a local and a manual `APPROVE` of its own `review_content_id`
  before `AWAITING_PLAN_APPROVAL` is reachable. `APPLYING_REVIEW_FEEDBACK`
  differs (row 35a blocks on no fb): it is entered only by a recorded
  verdict and left only through the apply's `post-fix` generation, so no
  withdrawal shares the phase and a missing fb is always a missing verdict.
- **`BLOCK` rows.** Only the two-stage `BLOCK` (rows 11 and 25) is a gate:
  `MILESTONE_WORKFLOW.md`'s two-stage tables say "explicit user resolution
  required", and no command applies it. A `"1"`/`"2.1"` `BLOCK` (rows 17
  and 31) is applied by `/apply-plan-review` or
  `/apply-implementation-review`, exactly as for a `REVISE`, so the
  catalogue adds no gate the Workflow does not have (LPR-R2-001). An apply
  that changes nothing gives `no_progress`, and the row is then emitted
  again; the orchestrator's `no_progress` handling applies.
- **Rows 38a, 38b and 38c** follow rows 37 and 38 on purpose: preparing
  the checklist and applying unconsumed functional findings call neither
  `resolve_own_registry_completion_status` nor the plan approval, and
  `/prepare-functional-review` and `/apply-functional-review` accept those
  states, so a drifted plan or a non-terminal registry is reported only
  where acceptance would be offered (LPR-R4-002, LPR-R4-004, LPR-R5-003).
  Row 38c replaces revision 5's `implementation.checkpoint` alternative at
  row 39: `/milestone-implement` refuses at `AWAITING_FUNCTIONAL_REVIEW`
  (`transition_checkpoint_in_progress` raises
  `IllegalCheckpointStartPhaseError` outside `IMPLEMENTING`), so that
  alternative named a command that cannot run. `accept-milestone.md` step
  2a's "finish it with `/milestone-implement`" is the same 2.6.0 prose
  inaccuracy; CP6 corrects the sentence, and it is recorded beside
  `v2.6.0-003` (CP7, section 7). Revision 6's replacement remedy
  (`/request-plan-amendment`, or `/apply-functional-review`'s two branches)
  was wrong too (LPR-R6-001): the amendment refuses at this phase, and
  neither branch makes the parent's registry terminal. Row 38c is
  therefore treated like row 38b, a state no 2.6.0 command advances. It
  keeps its own reason code, `registry_incomplete`, rather than
  `v1_state_not_advanced`, because the item is not a `"1"` item and its
  origin differs; the defect record is shared.
- **Remedy commands are checked against the row's phase** (LPR-R6-001
  architecture concern). Every `blocked`, `human_gate` and `external_gate`
  row carries, beside its prose, a `remedy_commands` field in the catalogue
  data: the command ids its remedy and alternatives name, with the remedy
  part set to the explicit value `none_exists` when no route exists (rows
  6a, 38b, 38c, whose alternatives are still listed: 38b's and 38c's
  `/apply-functional-review` and `/review-functional` accept the phase,
  they only do not make the registry terminal), and a `refusing_commands` field
  listing the commands the prose names only to say that they refuse here
  (for example row 38a's `/request-plan-amendment`, and row 38c's
  `/milestone-implement`, `/request-plan-amendment` and `/accept-milestone`). Both are
  catalogue data, not envelope fields, so the envelope is unchanged. CP4
  tests that every `remedy_commands` entry's phase gate accepts the row's
  phase at the row's `gv`, that every `refusing_commands` entry refuses the
  row's state,
  and that every command named in the prose is in one of the two.
  LPR-R5-003 and LPR-R6-001 were both errors of this kind.
- **Rows 25a and 25b are ordered on purpose** (LPR-R6-001 architecture
  concern). The `2.2` ingest and `/review-implementation` run the verifier
  before the generation check (2.6.0's step-4 order), while the catalogue
  tries 25a before 25b. When both fail, the command reports "regenerate"
  and `next-action` reports `bundle_generation_mismatch`. The catalogue
  keeps its order because the generation mismatch has the narrower remedy:
  an excluded-only commit past `generation_head` is repaired by
  `/recover-implementation-provenance` without a new round, and a
  regeneration offered first would bypass it. Both rows block, so no
  automatic action differs.
- **Bundle integrity (rows 7a, 16a, 25b, 30a, 35a, and the technical
  gate's `bundle_unverified`)** (LPR-R5-002, MPR-R7-001). At the two apply
  phases (rows 7a and 35a) the remedy is to restore the reviewed bundle,
  never to regenerate it: the feedback being applied binds to the reviewed
  bundle, and at `APPLYING_REVIEW_FEEDBACK` a generation is the round's
  exit. At both apply phases `assert_apply_review_feedback_binding` also
  checks **B** against its own `MANIFEST.md`: its `bundle_id`, its
  `work_item_id`, `base_commit` and `stage` and, at the plan stage, its
  `review_content_id` against the consumed one. A bundle directory copied
  or restored from another round, or another item's bundle in the shared
  flat `.ai-review/current/`, is reported as `bundle_unverified`, not
  trusted (MPR-R9-003, MPR-R10-001). `.ai-review/` is gitignored while the
  state is tracked, so a fresh clone or a second worktree has the state and
  no bundle. At the `2.2` implementation review stages, row 25b calls the
  implementation bundle verifier, the function `/review-implementation`
  step 4 and `/record-manual-implementation-review` step 5 now call; it is
  placed after row 25a (a generation mismatch has its own remedy) and ahead
  of rows 26, 27 and 28. Unlike row 25a, it does not depend on fb at the
  manual-external phase (LPR-R6-002): `WFR-17`'s reason for 25a's
  restriction, that an external reviewer reads a portable archive rather
  than this worktree, is about the generating worktree, not about whether
  a bundle exists to send. The plan stage does the same (row 10's
  `BUNDLE_UNVERIFIED` holds whatever fb holds). At the external gates (rows 16a, 30a, and the
  technical gate wrapper for rows 29 and 30) the check is narrower: only an
  absent or incomplete bundle, the `MissingRequiredBundleFileError` that
  computing **B** raises and that 2.6.0's `/apply-*-review` and
  `/approve-review` already refuse on. They do not add a manifest
  comparison, because none of those commands makes one today and adding it
  would tighten a 2.6.0 gate: at `2.2` the approval is bound to **I** by
  the ledger, whose two stages each ran the verifier when they were
  recorded, and at `"1"`/`"2.1"` a bundle that differs from the reviewed one
  already makes fb not current. So rows 29 and 30 need no separate row; the
  wrapper reports `bundle_unverified` and row 30 names it. For a `"1"`/`"2.1"`
  item the wrapper's `bundle_unverified` is unreachable from the catalogue,
  because rows 16a and 30a pre-empt it, as `plan_review_bundle_unbound` is
  at row 16.
- **`user_only`** actions are never `automatic`. A user-only action always
  has `worker.role: "user"` and `user_only: true`. That replaces the
  Controller's scan of the command files for `disable-model-invocation`.
  `implementation.recover_provenance` is **not** user-only: its command
  file has no such flag (section 2). It is listed only as an alternative,
  because the orchestrator never runs an `alternatives` entry on its own.
  Alternatives are for the human who resolves the gate or block.

**Conditions call Workflow functions only.** Each condition calls a
function that the matching command also calls. Most exist already:

- the publication status is `plan_review_publication_status`;
- `/apply-plan-review`'s acceptance is `assert_apply_plan_review_feedback`
  plus, in `"bundle"` mode, `assert_apply_review_feedback_binding` with
  `stage="plan"` (D-Apply-Binding, MPR-R11-001);
- `plan.start` reads the default with `load_config`, as `/milestone-plan`
  step 0 reads it;
- the implementing entry uses `implementing_entry_status`, the function
  behind `/milestone-implement`'s 1a;
- checkpoints use `select_next_checkpoint` and `registry_completion_status`;
- rows 38a, 38b, 38c and 39 use `resolve_own_registry_completion_status`,
  `/accept-milestone`'s step-2a pre-flight;
- the checklist uses `discover_current_functional_checklist_evidence`;
- unapplied functional findings use `resolve_feedback_dir` and
  `assert_functional_review_not_already_consumed`, the entry check of
  `/apply-functional-review` (LPR-R2-007). The command checks nothing more
  about the file's content before it starts, so neither does row 38;
- rejection uses `assert_bundle_not_rejected`;
- the generation check uses `assert_local_generation_matches`, which
  `/review-plan`, `/review-implementation`, `/approve-review` and the
  record-manual commands call before any write;
- the pin uses `is_technical_review_block_pinned`;
- the `2.2` implementation bundle check uses `verify_implementation_review_bundle`,
  which `/review-implementation`, `/record-manual-implementation-review` and
  the shared ingest call (LPR-R5-002);
- fb uses CP1's verdict parser.

**Two new repository-aware gate wrappers** (CP4, in `workflow_state`,
LPR-R1-003):

```text
plan_approval_gate_status(repo_root, state, work_item_id) -> {"reachable": bool, "cause": str | None, "inputs": {...}}
technical_approval_gate_status(repo_root, state, work_item_id) -> {"reachable": bool, "cause": str | None, "inputs": {...}}
```

Each computes the inputs that `/approve-review` computes in its own steps
today: the generation check (its step 2, both stages), `latest_round_status` from fb, `protected_path_dirty`,
`head_matches_reviewed_implementation_head` (including
`verify_implementation_provenance_interval`), `pinned_block` via
`is_technical_review_block_pinned`, the ledger and the current
`review_content_id`. It then calls the existing pure predicate. `inputs`
returns what it computed, and `reachable` is the predicate's result. When
`reachable` is false, `cause` names the first failing input: the
generation check first, then, at the plan stage of a `2.1`/`2.2` item,
`assert_plan_review_bundle_bound`, and at the implementation stage and
the `"1"` plan stage the computation of **B** (`bundle_unverified` when it raises
`MissingRequiredBundleFileError`, LPR-R5-002), then the predicate's own
order. `reachable` is false whenever any of these refuses, even though the
pure predicate takes none of them.

**This order is a deliberate change of `/approve-review`** (LPR-R3-004).
In 2.6.0 the command runs the predicate in its step 1 and the generation
check and `assert_plan_review_bundle_bound` in its step 2, so when both
fail it reports the predicate's refusal. The rewritten command calls the
wrapper and reports the wrapper's cause. A predicate computed for a bundle
generated at another HEAD or in another worktree says nothing about the
current checkout, so its remedy comes first. For example, a pinned `BLOCK`
with HEAD moved past `generation_head` now reports
`bundle_generation_mismatch` (row 30 offers
`implementation.recover_provenance`), and after the recovery it reports
`review_block_pinned` (row 30 offers `implementation.apply_review`). The
command refuses in both orders, so the change affects only which refusal is
named first. CP4 tests the new order.

`assert_plan_review_bundle_bound` refuses exactly when the publication
status at a ready phase is not `BOUND`. In the catalogue, rows 5 and 10
pre-empt every such status at `AWAITING_PLAN_APPROVAL`, so row 16 reports
`plan_review_bundle_unbound` only when the binding changes between the two
reads. The wrapper still reports it, so the command's own refusal is
complete without the catalogue.

| cause | plan gate | technical gate |
| --- | --- | --- |
| `bundle_generation_mismatch` | the generation check refuses | the generation check refuses |
| `plan_review_bundle_unbound` | `2.1`/`2.2`: `assert_plan_review_bundle_bound` refuses | — |
| `bundle_unverified` | `1`: computing **B** raises `MissingRequiredBundleFileError` | computing **B** raises `MissingRequiredBundleFileError` |
| `review_block_pinned` | — | `pinned_block` is true |
| `no_review_round` | no fb | no fb |
| `review_blocked` | `latest_round_status` is neither `REVISE` nor `APPROVE` | same |
| `protected_path_dirty` | — | a protected path is dirty |
| `implementation_provenance_stale` | — | HEAD does not match `reviewed_implementation_head`, or the provenance interval refuses |
| `review_ledger_stale` | `2.1`/`2.2`: the ledger does not record both `APPROVE`s for the current `review_content_id` | `2.2`: the same for the implementation ledger |

`/approve-review` is rewritten to call these wrappers for its gate check,
in the same way CP5 rewrites the record-manual commands to call the shared
ingest. The wrappers are read-only. `/approve-review implementation`'s
step-1 `BLOCK` pin write (`record_technical_review_block_pin`, under
`state_transaction`) stays in the command, ahead of the wrapper call, and
the wrapper is called on the state re-read after that write, so a `BLOCK`
observed in this turn is already pinned when `pinned_block` is computed
(LPR-R2-008). The pure predicates stay, and their existing tests stay. This
makes the catalogue's gate rows and the command read the same computed
inputs, so the command-agreement tests cover gate-input drift as well.

`next-action` never re-implements a rule that a command enforces. When a
command would refuse at a state where the catalogue says `automatic`, that
is a catalogue defect, and CP4's tests look for it by running each row's
command preconditions: every guard the command calls before its first
write, not only its entry assertion (LPR-R2-002).

`validation` is in the v1 vocabulary. 2.7.0 emits it from no row (W2,
`OD-W1-7`).

### D-OP-Reconcile: `reconcile`

The orchestrator runs:

```text
reconcile --decision FILE
```

`FILE` is the exact `next-action` result whose `action` it executed. Passing
it back verbatim keeps the Workflow free of decision history. `reconcile`
re-reads the state and returns:

```json
{"class": "progress|no_progress|gate_reached|invalid",
 "from": {"phase": "…", "state_identity": "…"},
 "to": {"phase": "…", "state_identity": "…"},
 "evidence": {"completed_checkpoints": ["CP2"], "recorded_stage": null},
 "invalid_reasons": [],
 "basis": { "...": "D-OP-Identity" },
 "next": { "...": "the next-action result for the new state" }}
```

**The item reconciled** is the decision's `basis.work_item_id`. For
`plan.start`, which has no basis, it is the new `active_work_item_id`: it
must not be in the decision's `snapshot.work_item_ids`, and exactly one key
of `work_items` may be new compared with that list. `from` is then `null`,
and the edge's source is "none" (LPR-R2-005). When no key is new and
`active_work_item_id` is still null, the class is `no_progress`: an interrupted `/milestone-plan` that has not
yet reached `route_work_item` is the ordinary case, and `to` is also
`null` (LPR-R3-006). Every other outcome is `invalid`
(`plan_start_item_ambiguous`): two or more new keys, a new key that is not
the active item, or no new key while the pointer is set. The
`plan.start` snapshot holds ids only, so a change to an existing item is
not detected here; the next `next-action` decides from it.

`reconcile` accepts a decision whose disposition is `automatic` only. A gate
is resolved outside the orchestrator's run, by a person or by
`record-external-result`, and the orchestrator then calls `next-action`
again. Any other decision refuses with `invalid_request`.

**Completion is reported by `next-action`, never by `reconcile`**
(MPR-R7-003). The only writer of `MILESTONE_COMPLETE` is
`complete_work_item`, behind `/accept-milestone`, a `user_only` action that
is offered only at the `human_gate` row 39. No automatic action has an edge
to `MILESTONE_COMPLETE`, so `reconcile` has no `complete` class: an
automatic action that left the item there would be on no legal edge, and
is `invalid`. After the user accepts, the orchestrator's next `next-action`
returns row 40, disposition `complete`, and that is the terminal signal.
Revision 7 listed a `complete` class and a CP6 test that reconciled
`milestone.accept`; neither could exist beside the automatic-only rule.

Each automatic action id has a fixed set of **legal edges**
(`from_phase → to_phase`, by `gv` where it matters), a **same-phase proof**
where a same-phase result can be progress, and a fixed **`allowed_results`**
list. All three are one table in `workflow_protocol.py`. `next-action`
copies `allowed_results` from this table into `action.allowed_results`, so
the two cannot disagree. The table is normative (CP6 copies it into the
specification), and it replaces the Controller's 18 expected-outcome rows
with their writer-call and line-number pins:

| action id | legal edges | same-phase proof of progress | `allowed_results` |
| --- | --- | --- | --- |
| `plan.start` | none → `PLANNING`, → `AWAITING_LOCAL_PLAN_REVIEW` (`2.1`/`2.2`; row 1a means no `"1"` edge exists, LPR-R3-001); none → none (no new item and no active item: `no_progress`, LPR-R3-006) | — | `progress`, `gate_reached`, `no_progress` |
| `plan.author` | `PLANNING`, `AMENDING_PLAN`, `REVISING_PLAN` → `AWAITING_LOCAL_PLAN_REVIEW` (`2.1`/`2.2`); `PLANNING`, `AMENDING_PLAN` → `AWAITING_EXTERNAL_PLAN_REVIEW` (`1`); unchanged | none (an unchanged phase, including one with a `PUBLISHED` record after a failed generation, is `no_progress`) | `progress`, `gate_reached`, `no_progress` |
| `plan.apply_review` | `REVISING_PLAN` → `AWAITING_LOCAL_PLAN_REVIEW` (`2.1`/`2.2`); `REVISING_PLAN` unchanged; `AWAITING_EXTERNAL_PLAN_REVIEW` unchanged (`1`) | `"1"`: `plan_revision` exceeds the decision's `snapshot.plan_revision` | `progress`, `gate_reached`, `no_progress` |
| `plan.review.local` | `AWAITING_LOCAL_PLAN_REVIEW` → `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` (`APPROVE`), → `REVISING_PLAN` (`REVISE`), unchanged (`BLOCK`, or no verdict) | none | `progress`, `gate_reached`, `no_progress` |
| `plan.record_external` | `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` → `AWAITING_PLAN_APPROVAL`, → `REVISING_PLAN`, unchanged | none | `progress`, `gate_reached`, `no_progress` |
| `implementation.checkpoint` | `IMPLEMENTING` unchanged, → `SELF_REVIEWING_IMPLEMENTATION` | at least one checkpoint is `COMPLETE` now that was not in `basis.checkpoints`, and `last_completed_checkpoint_id` is one of them | `progress`, `no_progress` |
| `implementation.self_review` | `IMPLEMENTING` → `SELF_REVIEWING_IMPLEMENTATION`; `IMPLEMENTING`, `SELF_REVIEWING_IMPLEMENTATION` → `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` (`2.2`), → `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (`2.1`; rows 23 and 24 are not emitted at `"1"`, LPR-R3-001); unchanged | none | `progress`, `gate_reached`, `no_progress` |
| `implementation.review.local` | `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` → `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`, → `APPLYING_REVIEW_FEEDBACK`, unchanged | none | `progress`, `gate_reached`, `no_progress` |
| `implementation.record_external` | `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` → `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`, → `APPLYING_REVIEW_FEEDBACK`, unchanged | none | `progress`, `gate_reached`, `no_progress` |
| `implementation.apply_review` | `APPLYING_REVIEW_FEEDBACK`, `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (`1`/`2.1`) → `APPLYING_REVIEW_FEEDBACK`, → `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` (`2.2`), → `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (`1`/`2.1`, including unchanged) | `implementation_revision` exceeds the decision's `snapshot.implementation_revision` | `progress`, `gate_reached`, `no_progress` |
| `functional.prepare` | `AWAITING_FUNCTIONAL_REVIEW` unchanged | none (the new decision's gate is the result) | `gate_reached`, `no_progress` |
| `functional.apply_findings` | `AWAITING_FUNCTIONAL_REVIEW` unchanged, → `bundle_generation_target_phase("post-fix", gv)` (the bounded-fix branch) | none | `progress`, `gate_reached`, `no_progress` |

Classification, first match wins:

1. **`invalid`** in any of these cases:
   - `validate_state` fails;
   - the decision is not a well-formed, automatic `next-action` result for
     this item, which also refuses with `invalid_request`;
   - the edge is not in the action's legal edges;
   - a checkpoint is `COMPLETE` now that was not in `basis.checkpoints`, and
     `verify_checkpoint_completions` cannot prove it by a reachable trailer
     commit (whether or not the phase changed);
   - the new phase is a review phase (row 6's seven review phases, not its
     two apply phases) and `assert_bundle_not_rejected` refuses. An apply
     phase reached with a marker is not `invalid`: the marker is a
     pre-existing condition, which the new decision reports as row 6;
   - at `2.1`/`2.2` only, the new phase is a ready plan phase
     (`AWAITING_LOCAL_PLAN_REVIEW`, `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`,
     `AWAITING_PLAN_APPROVAL`) and `plan_review_publication_status` is not
     `BOUND`. `REVISING_PLAN`, `PLANNING` and `AMENDING_PLAN` are exempt:
     a `REVISE` there leaves a `CONSUMED` record by design, and a failed
     generation leaves `PUBLISHED`. For `"1"` the publication status is
     never called; it raises for `"1"` (`_require_v2_1_plan_review`,
     LPR-R2-004).
2. **`gate_reached`**: the new `next-action` disposition is `human_gate` or
   `external_gate`. This includes an unchanged state after a `BLOCK`
   verdict: the `BLOCK` writes no state, but the new decision is
   `review.resolve_block`.
3. **`progress`**: an edge to a different phase, or a same-phase edge
   whose proof in the table holds.
4. **`no_progress`**: everything else on a legal edge. That is an
   unchanged state identity, or a changed identity with no proof of
   progress. One example is a checkpoint moved to `IN_PROGRESS` before the
   session ended; `evidence.started_checkpoints` then names it. Another is a
   `PUBLISHED` record after a failed generation.

After classification, a class not in the action's `allowed_results` is
replaced by `invalid` with reason `result_not_allowed`. With the table
above, that happens only where the table says so. For example,
`implementation.checkpoint` never produces `gate_reached`.

`reconcile` writes nothing.

### D-OP-External: `record-external-result`

```text
record-external-result --work-item ID --kind KIND --input FILE
```

v1 kinds:

- `plan_review_verdict`: a manual external plan-review verdict, accepted at
  `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` (2.1, 2.2) or
  `AWAITING_EXTERNAL_PLAN_REVIEW` (1).
- `implementation_review_verdict`: accepted at
  `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` (2.2) or
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (1, 2.1).

Reserved kinds, refused with `unsupported_result_kind`: `pr_review_result`
and `functional_evidence` (W2).

The operation calls one new function in `workflow_state`:

```text
ingest_manual_review_verdict(repo_root, work_item_id, *, stage, verdict_text, now) -> dict
```

What it requires and checks depends on the stage and the item's governing
version. It selects one row of this table from the item's phase and `gv`,
and refuses with `not_applicable` when no row matches (LPR-R1-006):

| kind | `gv` | accepted phase | required header fields | guards, in order | records |
| --- | --- | --- | --- | --- | --- |
| `plan_review_verdict` | `2.1`, `2.2` | `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` | `Status:`, `Reviewer role:`, a `review_content_id` label | `assert_manual_feedback_names_work_item`; `assert_local_generation_matches`; `assert_bundle_not_rejected`; `assert_plan_review_bundle_bound`; `validate_manual_plan_review_preconditions`; `check_manual_stage_bundle_id_advisory`; `assert_bundle_not_rejected` again, immediately before the first write | `record_manual_plan_review` |
| `implementation_review_verdict` | `2.2` | `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` | the same three | `assert_manual_feedback_names_work_item`; `verify_implementation_review_bundle`; `assert_local_generation_matches`; `assert_bundle_not_rejected`; `validate_manual_implementation_review_preconditions`; `check_manual_stage_bundle_id_advisory`; `assert_bundle_not_rejected` again, immediately before the first write | `record_manual_implementation_review` |
| `plan_review_verdict` | `1` | `AWAITING_EXTERNAL_PLAN_REVIEW` | `Status:` and the three binding fields | `assert_manual_feedback_names_work_item`; `assert_bundle_not_rejected`; `assert_feedback_matches_bundle` against the current plan bundle (**B**) | nothing (feedback only) |
| `implementation_review_verdict` | `1`, `2.1` | `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | `Status:` and the three binding fields | `assert_manual_feedback_names_work_item`; `assert_bundle_not_rejected`; `assert_feedback_matches_bundle` against the current implementation bundle | nothing (feedback only) |

The two two-stage rows list the guards that `/record-manual-plan-review`
and `/record-manual-implementation-review` run today, in their order,
including step 5's "staleness/wrong-worktree handling", which is
`/review-plan`'s `assert_local_generation_matches` call, and the `WFR-67`
re-check under step 7's mutation guard (LPR-R2-002). At the implementation
stage, step 5's recompute "identical in mechanism to `/review-implementation`'s
own" is `/review-implementation` step 4's bundle check, which refuses an
absent, incomplete or mismatched bundle; it is the
`verify_implementation_review_bundle` guard, in 2.6.0's position (step 5's
recompute, before its generation check). Without it the ingest would
accept a verdict that 2.6.0 refuses (LPR-R5-002). The plan-stage row needs
no counterpart: `assert_plan_review_bundle_bound` re-runs
`verify_plan_review_bundle`. CP5 adds the
record-manual commands to the caller list in the docstrings of
`assert_local_generation_matches` and `WorktreeOrHeadMismatchError`: they
are repository-local commands, and `WFR-17`'s exclusion covers only an
external reviewer reading a portable archive.

**Required fields are those 2.6.0 required** (LPR-R2-003). The two-stage
rows require `Status:`, `Reviewer role:` and a `review_content_id` label,
the three values 2.6.0's step 6 hard-checks. `Work item:` stays optional
there, as in 2.6.0's step 4: a present foreign value refuses, and an absent
one is bound by the hard `review_content_id` check. `Reviewed bundle ID:`
and `Reviewed base commit:` stay optional, because the bundle id is
advisory only. In 2.6.0 the apply commands then bound the same `REVISE`
by bundle id, so a recorded `REVISE` that lacked these fields, or named a
bundle a wrapper-only regeneration replaced, was refused at its apply.
2.7.0 removes that disagreement at the apply commands, not at the ingest:
a two-stage `REVISE` that states a `review_content_id` is applied by
content (D-Apply-Binding), so every verdict a two-stage row records is
also accepted by its apply command, and `Reviewed bundle ID:` stays the
reviewer's own attestation, never rewritten (MPR-R9-001). The ingest is
deliberately not tightened to refuse such a `REVISE` (MPR-R8-001): that
would change a 2.6.0 command for one status only, would contradict the
advisory rule that keeps a wrapper-only regeneration's verdict current
(row 11a), and would still leave the file-edit and fresh-worktree routes
into the same state uncovered. The feedback-only rows require `Status:` and the three
binding fields, which `assert_feedback_matches_bundle` requires of the same
file at `/approve-review` and `/apply-*-review`. A `review_content_id`
label is optional for `"1"`, as D-Feedback-Label says.
Their guard is the binding that `/approve-review` and `/apply-*-review`
later apply to the same file. Those two rows have no 2.6.0 command. They
are the protocol's equivalent of a person placing the feedback file by
hand, and they change no state, which is what placing the file does today.

The `/record-manual-plan-review` and `/record-manual-implementation-review`
commands are rewritten to call **the same function**, with the text of the
file the user pasted. That leaves one ingest and no duplicated guard
sequence. In order, it:

1. parses the verdict with the Workflow's verdict parser (CP1), which reads
   each field where 2.6.0 read it (D-Feedback-Label). This step reads no
   state;
2. acquires `state_lock` and holds it through step 6, so the steps below
   read the state fresh inside the lock and no other ingest or state
   writer can run between them (MPR-R7-002);
3. selects the table row from the state re-read under the lock, or refuses
   with `not_applicable`. A field the row requires that is missing refuses
   (`refused`, with a native `ManualVerdictHeaderError`);
4. runs the row's guards in the order shown, on that state, the last of
   them immediately before step 5's write. For a two-stage row it then
   computes the recorded state, `record_manual_*_review(state, …)`, which
   is pure, so a refusal of the writer itself also comes before any write;
5. writes `verdict_text` to the resolved `<feedback_dir>/REVIEW_FEEDBACK.md`
   atomically (temporary file then `os.replace`), under the existing
   feedback-ownership guard (`assert_feedback_not_owned_by_other_work_item`).
   When the bytes are already identical, this is a no-op, which is the
   command path;
6. for a two-stage row, publishes the state computed in step 4, with the
   same checks and the same canonical, atomic publication that
   `state_transaction` performs, then releases the lock. A feedback-only
   row releases the lock after step 5.

**Steps 3 to 6 are one critical section** (MPR-R7-002). `state_lock`
refuses re-entry in a process, so the ingest cannot call
`state_transaction` inside it. CP5 therefore adds one keyword to
`state_transaction`, `before_publish`: a callable that receives the
mutator's result and runs inside the lock after every pre-publication
check, immediately before `_publish_state_file`. Its position is fixed
(MPR-R8-003): `state_transaction` runs the mutator, then
`_assert_technical_review_block_pins_monotonic` and any other check on the
candidate state, then `before_publish`, then `_publish_state_file`, and a
check added later goes before the hook. A refusal of any check therefore
leaves both the feedback file and the state untouched, and only the
publication I/O itself lies in the crash window below. An exception from
the hook aborts the transaction with nothing published. The two-stage rows run steps 3 and 4
as the mutator and step 5 as `before_publish`. The feedback-only rows have
no state to publish, so they hold `state_lock` directly around steps 3 to
5. Every existing caller passes no `before_publish`, and its behaviour is
unchanged. Two concurrent ingests are therefore serialized, whatever their
verdicts:

- at a two-stage row, the second one re-reads the state the first one
  published. Its phase or its ledger has moved, so its row selection or
  `validate_manual_*_review_preconditions` refuses (`not_applicable` or
  `refused`), before its step 5. The feedback file always holds the verdict
  the ledger recorded;
- at a feedback-only row, the second one finds a different verdict in the
  file that `assert_feedback_matches_bundle` accepts against the current
  **B**, and refuses with `refused` and a native
  `ConflictingReviewFeedbackError` (new in CP5), before its step 5.
  Identical bytes are still the no-op. A verdict that no longer binds to
  **B** (an earlier round's) is replaced, as placing a new file by hand
  replaces it. The 2.6.0 commands never write a feedback-only row, so this
  refusal changes no 2.6.0 path.

A file edited by hand is outside every lock, as it is in 2.6.0. A
two-stage ingest that finds an unrecorded verdict left in the file by hand
or by an earlier crash replaces it and records its own, so the file and the
ledger still agree.

**`round` and `bundle_id`** (LPR-R3-005). `record_manual_plan_review` and
`record_manual_implementation_review` take both, and an `APPROVE` stores
both in the ledger verbatim. 2.6.0's commands never say how `round` is
chosen. The ingest derives them, and the commands, which now call it,
inherit the rule:

- `round` is the verdict's `Round:` line when it is a positive integer.
  Otherwise it is the `round` the ledger records for the same stage's local
  `APPROVE` of the current `review_content_id`, the round the manual
  review follows. Validation requires that local `APPROVE`, so the
  fallback always exists. A `Round:` line that is present but not a
  positive integer refuses with `ManualVerdictHeaderError`.
- `bundle_id` is the verdict's `Reviewed bundle ID:` when present, passed
  to `check_manual_stage_bundle_id_advisory` as in 2.6.0. When it is
  absent, the ingest records `null`, does not call the advisory check, and
  reports the advisory `"Reviewed bundle ID: absent"`. `null` records that
  the reviewer named no bundle. Substituting the current id would record a
  bundle the reviewer may not have seen. Neither
  `_validate_plan_review_stages` nor `_validate_implementation_review_stages`
  checks the field's shape, so a 2.6.0 reader accepts it.

Both values appear in the result.

Writing the file before the state makes a crash between steps 5 and 6
safe for the two-stage rows. The phase is unchanged, the file holds the
verdict, and a retry of either path finds it and records it (catalogue
rows 13 and 27). A retry after step 6 refuses as a duplicate under the
existing precondition, and the protocol reports that as `not_applicable`
with the native exception.

The result is `{stage, verdict, review_content_id, round, bundle_id, advisory, basis}`; `round` and `bundle_id` are `null` for a feedback-only row. The
orchestrator never reads or writes a feedback path itself.

### D-Apply-Binding: a two-stage `REVISE` is applied by content

(MPR-R9-001, `OD-W1-11`.) The two-stage ingests bind a verdict by
`review_content_id` and treat its bundle id as advisory, but 2.6.0's
apply commands bind the same `REVISE` by bundle id (section 2). The two
disagree for a recorded `REVISE` with no `Reviewed bundle ID:`, or one
naming a bundle that a wrapper-only regeneration replaced. 2.7.0 resolves
the disagreement in the apply commands, with one function both commands
and the catalogue call:

```text
assert_apply_review_feedback_binding(repo_root, work_item, work_item_id, *,
                                     stage, feedback_content) -> dict
```

It lives in `workflow_state`, and it reads the state and the bundle but
writes nothing. It selects one of two bindings:

- **content**, when all of these hold:
  - the item is two-stage for the stage: `gv` in
    `TWO_STAGE_PLAN_REVIEW_VERSIONS` at `stage="plan"`, `2.2` at
    `stage="implementation"`;
  - fb's `Status:` is `REVISE`;
  - fb states a `review_content_id` (CP1's verdict parser);
  - at the plan stage, `plan_review_binding.consumed` is not the legacy
    marker. The plan-stage call is made only where `/apply-plan-review`
    ran `assert_apply_plan_review_feedback` and got `"bundle"`. At the
    implementation stage, the phase is `APPLYING_REVIEW_FEEDBACK`;
  - **B**'s `MANIFEST.md` states a `work_item_id`
    (`_read_manifest_binding_fields`). Both 2.6.0 manifest writers
    require one (`write_manifest_with_verified_identifiers`,
    `workflow_fingerprint.py:3895`, and the implementation-stage writer,
    `:4196`), but `render_manifest_md_implementation_stage` makes it
    optional (`:4098`), so a flat legacy manifest may lack it. Such a
    bundle names no owner, so the bundle binding, which requires fb's
    `Work item:` to name this item, applies (MPR-R10-001);
- **bundle** otherwise: exactly 2.6.0's `assert_feedback_matches_bundle`
  against **B**, the item's `base_commit` and its id.

The content binding checks, in order:

1. a `Work item:` that is present and names another item refuses with
   `FeedbackBundleMismatchError`, as the ingest refuses it;
2. at the plan stage, fb's `review_content_id` must equal
   `consumed.review_content_id`, or `FeedbackContentMismatchError`: the
   verdict is not for the round being applied;
3. **B** is computed (`MissingRequiredBundleFileError` when the
   directory is absent or incomplete), and it must equal the
   `bundle_id` recorded in the bundle's own `MANIFEST.md`
   (`read_plan_stage_manifest_fields` or `read_manifest_identifiers`).
   The manifest must also name this item's bundle at this stage
   (MPR-R10-001): its `work_item_id` must equal the item's id; its
   `base_commit`, when present, the item's `base_commit`; and its
   `stage` must be `plan` at `stage="plan"` and `implementation` at
   `stage="implementation"`. Every implementation and `post-fix`
   generation writes `stage: implementation` (`workflow_fingerprint.py:4141`).
   At the plan stage, the manifest's `review_content_id` must also equal
   the consumed one. Otherwise `ReviewBundleManifestMismatchError`
   (new), naming the comparison and both values: the directory is not
   this item's reviewed bundle (MPR-R9-003, MPR-R10-001);
4. fb's `review_content_id` must equal the manifest's, or
   `FeedbackContentMismatchError` (new), naming both. At the plan stage
   this follows from 2 and 3. At the implementation stage it is the
   binding itself. The manifest's id is used rather than **I**, because
   **I** moves when the applier commits a fix.

**Why check 3 names the owner** (MPR-R10-001). The content binding does
not require fb's `Work item:`: check 1 refuses only a foreign one,
because a recorded manual verdict may omit the field
(`assert_manual_feedback_names_work_item`, `workflow_fingerprint.py:3381`).
The manifest's `work_item_id` takes its place. At the plan stage, check 2
already ties fb to this item's consumed id, so the owner check adds
defence in depth. At the implementation stage nothing durable and
per-item does: `record_local_implementation_review` writes no ledger
entry for a `REVISE`, and `resolve_bundle_dir` resolves a non-plan stage
of an item with no `.ai-review/<id>/` root to the shared flat
`.ai-review/current` (`workflow_fingerprint.py:2041`), with the legacy
feedback directory flat in the same way. Without the owner check, item
Y's flat bundle and Y's manual `REVISE` with no `Work item:` would form a
self-consistent pair that X's `/apply-implementation-review` accepted at
`APPLYING_REVIEW_FEEDBACK`, where 2.6.0 refused it
(`MissingFeedbackBindingFieldError`). The rule is the same at both
stages: fb is bound to content, and the content to a bundle that this
item owns at this stage.

`Reviewed bundle ID:` and `Reviewed base commit:` are not compared by
the content binding. When they are present and differ from **B** or the
item's `base_commit`, the result reports it as an advisory, the
apply-side counterpart of `check_manual_stage_bundle_id_advisory`. The
function returns `{binding, bundle_id, review_content_id, advisory}`.

**What changes for an operator.** `/apply-plan-review` step 1 (in
`"bundle"` mode) and `/apply-implementation-review` step 1 call this
function in place of `assert_feedback_matches_bundle`. For every `"1"`
and `"2.1"` implementation round, every legacy marker, and every
two-stage fb that states no `review_content_id`, the function is that
same call, so their behaviour is unchanged. So is an fb whose bundle's
manifest states no `work_item_id`. For a two-stage `REVISE` that
states a `review_content_id`, the change is a bounded loosening and one
tightening:

- **loosened:** absent or differing bundle fields no longer refuse. The
  verdict is still bound to the exact content reviewed, and that content
  is still on disk, in a bundle whose manifest names this item and this
  stage (check 3). The manifest's `work_item_id` takes the place of fb's
  `Work item:`. At the implementation stage, which has no consumed
  record, it is what ties the verdict to this item (MPR-R10-001);
- **tightened:** a stated `review_content_id` that is not the reviewed
  content refuses, even when the bundle fields were edited to name **B**.
  2.6.0 accepted that file at face value, so the forged attestation that
  MPR-R9-001 describes can no longer pass.

`/approve-review` is unchanged: a two-stage approval reads the review
ledger, not fb's bundle fields. The `durable` mode of
`assert_apply_plan_review_feedback` (publication rows 9 and 11) is
unchanged, and it already binds by content. A `"1"`/`"2.1"` `BLOCK` pin
still records the recomputed **B** (`apply-implementation-review.md`
step 1), because those rounds keep the bundle binding.

**Why not keep the block** (option (b) of MPR-R9-001). Blocking a
recorded `REVISE` until a new verdict for **B** arrives would send every
recorded manual `REVISE` without the optional field, and every verdict
that outlived a wrapper-only regeneration, back to its reviewer, although
the ingest has already bound it by content. A separate operator field
(`Bound to bundle ID:`) would keep two binding rules and add a third
field. One rule per stage, the same one D-OP-Next's "fb is current"
already uses for two-stage phases, is simpler, and it removes the
file-edit remedy entirely. Round 8 rejected a different change, tightening
the ingest. This change loosens the apply, so it agrees with the ingest's
advisory bundle id (row 11a) instead of contradicting it.

`REVIEW_PROTOCOL.md`'s "Required structure" paragraph is amended (CP4).
The three binding fields stay required in every verdict a reviewer
writes, and they keep their meaning: the bundle the reviewer reviewed. The
paragraph states that a two-stage `REVISE` is applied by its
`review_content_id`, with the bundle fields advisory. It also states that
no command or remedy rewrites a reviewer's binding fields.

### D-OP-Artifacts: `resolve-artifact`

```text
resolve-artifact --work-item ID --kind KIND
```

It returns `{kind, path (repo-relative), exists}`. The v1 kinds, each
resolved by the existing helper only:

| kind | resolved by |
| --- | --- |
| `review_feedback` | `resolve_feedback_dir` + `REVIEW_FEEDBACK.md` |
| `functional_review` | `resolve_feedback_dir` + `FUNCTIONAL_REVIEW.md` |
| `review_bundle` | `resolve_bundle_dir` with `stage="plan"` at plan-stage phases, and the item's resolved bundle dir otherwise |
| `plan_review_inputs` | `resolve_plan_review_inputs_dir` |
| `plan_document` | the item's `plan_path` |
| `functional_checklist` | the functional-review checklist path |

This is an escape hatch for display and hand-off, for example "upload this
bundle". No catalogue decision requires the orchestrator to read a
resolved artifact.

### D-OP-Schema: a shipped JSON Schema

`docs/ai-workflow/orchestration-protocol-v1.schema.json` (JSON Schema 2020-12,
distribution) defines the envelope and every operation's `result`. The
Workflow stays stdlib-only. Its tests check each response against the schema
with a minimal validator in the test module. That validator covers `type`,
`required`, `properties`, `additionalProperties`, `enum`, `items` and
`$ref`; the schema uses only these keywords, and a test asserts it. The
orchestrator validates with its own tooling.

### D-Feedback-Label (`v2.6.0-002`)

- **Pinned label:** `Reviewed review_content_id: <64 hex>` (`OD-W1-3`). It
  is added to `REVIEW_PROTOCOL.md` "Required structure":
  - **required** for every two-stage stage verdict (plan stage at `2.1` and
    `2.2`, implementation stage at `2.2`);
  - optional for `"1"` and the advisory `/review-implementation` at
    `1`/`2.1`.

  `/review-plan` and `/review-implementation` (both branches) write exactly
  this label, and the record-manual commands' reviewer instructions name it
  and say that the header fields come before the first `## ` section
  (LPR-R2-003).
- **Header block:** the lines before the first `## ` heading that follows a
  field line (`key: value`). A verdict that opens with `## Review Decision`
  and puts its fields under it therefore still has those fields in its
  header block; only a `## ` heading after the fields ends it (LPR-R2-003).
- **Parser:** `parse_feedback_review_content_id` reads the header block only.
  This matches where the required structure puts the binding fields. It accepts the pinned label,
  the bare `review_content_id:` form it already accepted, and **the legacy
  alias** `Reviewed review content ID:`, case-insensitively as today. If
  more than one distinct value appears, the result is `None`, as today. The
  workaround's two labels with one value still parse.
- **Scope of the header-only rule** (LPR-R1-009, LPR-R2-003): it applies to
  `review_content_id` only. `parse_review_feedback_binding_fields` keeps its
  2.6.0 whole-file scan for `Status:`, `Reviewed bundle ID:`,
  `Reviewed base commit:` and `Work item:`. Its callers (`/approve-review`,
  `/apply-*-review`, `assert_feedback_matches_bundle`,
  `assert_manual_feedback_names_work_item`) therefore behave exactly as in
  2.6.0. The new `parse_review_feedback_header` composes the existing
  readers rather than adding a third: those four fields from
  `parse_review_feedback_binding_fields`, `Reviewer role:` by the same
  whole-file first-match convention (2.6.0 has no role parser; the command
  read it), and `review_content_id` from `parse_feedback_review_content_id`.
  The ingest, `next-action` and the 2.6.0 consumers therefore read every
  field identically, and only `review_content_id` is header-only.
- A verdict that names its ID only after the first `## ` was accepted by
  2.6.0's whole-file scan. In 2.7.0 it parses as absent. This is
  deliberate: the required structure always put the ID in the header, and
  the Controller already read only the header. CP1 records it in the spec's
  compatibility notes. It is the only field a 2.7.0 command reads more
  strictly than 2.6.0 did (LPR-R2-003).

### D-Consumed-History (`v2.6.0-001`)

Option 1 of the defect: **enforce** (`OD-W1-1`).

- **Record:** a new work-item key, `consumed_plan_review_content_ids`. It
  holds the sorted, duplicate-free list of every non-null `review_content_id`
  ever written as `consumed`. It lives on the work item, outside
  `plan_review_binding` (`OD-W1-2`), so that 2.6.0's exact-key-set validator
  for `plan_review_binding` is untouched. 2.6.0's `_validate_work_item`
  ignores the unknown key.
- **Writer:** `_write_consumed_plan_review_binding`, which is still the
  single `CONSUMED` writer, also inserts the id into the list. The legacy
  marker (a `null` id) adds nothing.
- **Check:** `_assert_not_consumed` refuses when `rcid` equals the slot's id
  **or** is in the list (`ConsumedPlanReviewContentError`, unchanged). The
  legacy-marker revision rule is unchanged. `plan_review_publication_status`
  reads the same union. Its row 10 today requires
  `mirror == registry == consumed.plan_revision` and `fresh ==
  consumed.review_content_id`. A list entry stores an id only, so for a
  list hit the row-10 predicate is id-only, exactly as `_assert_not_consumed`
  is: row 10 (`NEEDS_EDIT`) matches when the fresh id is in the list,
  whatever the revisions are. The slot keeps today's full predicate. Row 11
  (`EDIT_IN_PROGRESS`) is unchanged and is reached only when neither
  matches. Content consumed earlier therefore shows as `NEEDS_EDIT`, not
  `EDIT_IN_PROGRESS` (LPR-R1-010).
- **Migration** happens at read time, with no rewrite. An absent key means
  that the history is `[slot id]`, or `[]` for a legacy marker. The first
  2.7.0 `CONSUMED` write materializes the key as the union of that and the
  new id. 2.6.0 single-slot records therefore lose nothing they held.
  Content consumed before the upgrade and then displaced is unrecoverable
  history, and it is the one residual.
- **Validation:** when present, the value is a list of unique, sorted 64-hex
  strings. It is not required to contain the slot's id: a 2.6.0 writer after
  a downgrade could write a slot that the list does not hold, and the
  checker reads the union anyway.
- **Downgrade posture:** the state stays readable by 2.6.0. 2.6.0 ignores
  the list, so it enforces only the slot, which is its own documented
  behaviour. Mixed-release worktrees remain unsupported (`v2.4.0-002`).
- **Consequence, stated normatively:** content that was withdrawn, revised
  or amended away can only re-enter review after an edit. Restoring the
  exact bytes is refused. `review_content_id` hashes the protected content,
  so any edit at all is enough. The 2.6.0 texts that already claim this
  become true, and the defect's sequence is the regression test.
  `TestPlanApprovalPhaseGate`'s detour test changes from "re-binds, but
  never reaches approval" to "refused at publish, and at bind if a
  published record is forged".

## 4. Open decisions (for the plan reviewer and the user)

This repository has no `docs/TECHNICAL_DECISIONS.md`. These are the
decisions the plan would otherwise finalize silently. The plan is written
against each recommendation.

| id | decision | options | recommendation |
| --- | --- | --- | --- |
| `OD-W1-1` | `v2.6.0-001` outcome | (a) enforce: a durable consumed history; (b) narrow the guarantee to the latest consumption and rewrite the texts | **(a).** The texts already promise it, and the history costs one list. (b) would document a hole that W2's automatic approvals would widen, because evidence keyed by content would then be re-usable after a detour. |
| `OD-W1-2` | Where the history lives | (a) a work-item key beside `plan_review_binding`; (b) a key inside the binding record | **(a).** 2.6.0's binding validator checks an exact key set, so (b) would make a 2.7.0-written state invalid for 2.6.0. (a) is ignored by 2.6.0. |
| `OD-W1-3` | The pinned label | (a) `Reviewed review_content_id:`; (b) `Reviewed review content ID:` | **(a).** It names the field exactly as `REVIEW_REQUEST.md`, the manifest and the ledger do, and the Workflow's parser already accepts it. (b) stays a legacy alias. |
| `OD-W1-4` | Manifest provenance for an authored-here release | (a) `provenance: {origin: "authored", base_release: "2.6.0"}`, dropping `overlay_commit`, every `overlay_delta` and the `overlay_*` counts; (b) keep the overlay fields relative to 2.3.1 and recompute them | **(a).** There is no overlay since 2.7 (`workflow-manager` `ARCHITECTURE.md`), and no code reads the fields. Keeping them would require recomputing diffs against an upstream that is no longer the base. `upstream` stays, because it records where 2.3.1 came from. |
| `OD-W1-5` | Transport | (a) a new `scripts/workflow_protocol.py` with subcommands; (b) more flags on `workflow_state.py` | **(a).** It gives one surface with one envelope, and keeps the existing 2.6.0 flags byte-compatible. |
| `OD-W1-6` | State identity scope | (a) per work item; (b) the whole state file | **(a).** Concurrent items are normal (D1), and (b) would turn unrelated progress into stale decisions. |
| `OD-W1-7` | W2 vocabulary in v1 | (a) define `validation`, `pr_review_result` and `functional_evidence` now, with nothing emitting or accepting them; (b) add them in v1.1 | **(a).** Consumers built on v1.0 then already handle the disposition (fail closed as `blocked` until they support it), and W2 is a minor bump. |
| `OD-W1-8` | `APPLYING_REVIEW_FEEDBACK` for `"1"`/`"2.1"` items | (a) `automatic`, like `"2.2"`; (b) `human_gate`, as Controller 1.5.0's `_STATIC_GATES` does | **(a).** The operator reference treats the phase as `/apply-implementation-review` mid-run, which is model-runnable and returns to the external-review gate. The Controller's gate there was conservative, not something the Workflow stated. |
| `OD-W1-9` | Header-only parsing of `review_content_id` (D-Feedback-Label); `Status:`, `Reviewer role:` and the three binding fields keep the whole-file scan, and the record-manual commands require only what 2.6.0 required | (a) the header only; (b) keep the whole-file scan | **(a).** It is where the required structure puts the field, and a finding that quotes another ID can no longer make the parse `None`. A leading `## Review Decision` heading does not end the header block. The cost is the one compatibility note. |
| `OD-W1-10` | The `"1"` states that no 2.6.0 command advances (`PLANNING`/`AMENDING_PLAN`, `IMPLEMENTING`), found by LPR-R3-001 | (a) report them as `blocked` (rows 1a, 6a) and write the gap up as `v2.6.0-003` for a later release; (b) fix the `"1"` commands in W1 | **(a).** The fix changes the `"1"` branches' v1-inert contract and their golden-output test (`WF8a-ii`), which is a decision about the `"1"` lifecycle, not about the protocol. Under (a) the catalogue reports exactly what the commands do, and nothing W1 ships makes the gap worse. |
| `OD-W1-11` | How a two-stage `REVISE` binds at its apply command, found by MPR-R8-001 and MPR-R9-001 | (a) by content: `/apply-plan-review` and `/apply-implementation-review` accept a two-stage `REVISE` whose `review_content_id` is the reviewed content, with the bundle fields advisory (D-Apply-Binding); (b) keep 2.6.0's bundle binding, block a recorded `REVISE` that it refuses, and require a new verdict for the current bundle | **(a).** The ingest already binds the same verdict by content, so (b) would send recorded verdicts back to their reviewer for a field the ingest calls advisory. (a) changes two 2.6.0 apply commands, for two-stage `REVISE` verdicts only. It is bounded by the content check and by a manifest check of the bundle on disk, including the work item and stage the manifest names (MPR-R10-001), and it refuses a rewritten `Reviewed bundle ID:`, which 2.6.0 accepted. |

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Pinned review_content_id label in review feedback, legacy alias accepted (v2.6.0-002) | - | 2 | 1 |
| CP2 | Durable consumed plan-review content history: withdrawn or revised content never re-binds (v2.6.0-001) | - | 3 | 1 |
| CP3 | Protocol core: workflow_protocol.py envelope, versioning, error codes, state identity, describe, verify, resolve-artifact | - | 3 | 1 |
| CP4 | next-action and reconcile: the total action catalogue, dispositions, worker requirements, stale-decision refusal, same-phase progress | CP3 | 3 | 1 |
| CP5 | record-external-result: one Workflow-owned ingest for manual plan and implementation verdicts, shared by the commands | CP1, CP3, CP4 | 3 | 1 |
| CP6 | Protocol specification document, command and operator documentation, lifecycle end-to-end test in a disposable repository | CP2, CP4, CP5 | 2 | 1 |
| CP7 | Release 2.7.0: manifest, conformance CI for the new suite, release-constant guard, roadmap | CP6 | 2 | 1 |

All paths in the checkpoints are release-source paths (`payload/…`,
`templates/…`, `manifest.json`) unless stated otherwise. The installation
copies under the repository root are never edited. Each checkpoint runs the
payload's seven existing suites, plus the new one from CP3 onwards, in a
release-source conformance fixture
(`tools/release/release.py stage-conformance`). It also runs
`workflow-manager verify .` on the checkout.

<!-- CP1 -->
### CP1 — Pinned `review_content_id` label (`v2.6.0-002`)

**Files:**

- `payload/scripts/workflow_fingerprint.py`:
  - `_FEEDBACK_REVIEW_CONTENT_ID_RE` gets the alias;
  - `parse_feedback_review_content_id` restricts its scan to the header
    block;
  - a new `parse_review_feedback_header(text) -> dict` returns `status`,
    `reviewer_role`, `reviewed_bundle_id`, `reviewed_base_commit`,
    `work_item` and `review_content_id`, composed as D-Feedback-Label
    states (only `review_content_id` is header-only). This is the single
    verdict parser that CP5 and `next-action` use.
    `parse_review_feedback_binding_fields` is unchanged and keeps its
    whole-file scan (D-Feedback-Label, LPR-R1-009, LPR-R2-003).
- `payload/scripts/workflow_fingerprint_test.py`: the tests below.
- `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`: "Required structure" gets
  the pinned line, the rule for when it is required, and the alias note.
- `payload/.claude/commands/review-plan.md` (step 7) and
  `payload/.claude/commands/review-implementation.md` (both branches): the
  exact label.
- `payload/.claude/commands/record-manual-plan-review.md` and
  `record-manual-implementation-review.md`: the reviewer template names the
  pinned label and says that the header fields come before the first `## `
  section.

**Tests:**

- pinned label only, alias only, bare form, and alias plus pinned with the
  same value all parse;
- two labels with different values give `None`;
- the ID after the first `## ` that follows a field line is ignored;
- a verdict that opens with `## Review Decision` and states its fields under
  it parses every field, including the ID;
- a finding body quoting another 64-hex ID under a `## ` heading leaves the
  parse intact;
- `parse_review_feedback_header` on the M1 round-1 verdict shape and on the
  Controller's archived spaced-only shape;
- `parse_review_feedback_binding_fields` is unchanged: a `Status:` or
  `Work item:` line only after the first `## ` still parses, as in 2.6.0;
- each command file names exactly the pinned label (text test).

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Durable consumed history (`v2.6.0-001`)

**Files:**

- `payload/scripts/workflow_state.py`:
  - `_write_consumed_plan_review_binding` maintains
    `consumed_plan_review_content_ids`;
  - `_assert_not_consumed` and `plan_review_publication_status` rows 10
    and 11 read the union (a helper `_consumed_plan_review_content_ids(work_item)`);
  - `_validate_work_item` adds the shape check;
  - `default_work_item` is unchanged, because the key is absent until the
    first consumption.
- `payload/scripts/workflow_state_test.py`:
  - `TestPlanApprovalPhaseGate`'s detour test is rewritten for the new
    outcome;
  - a new `TestConsumedPlanReviewHistory`.
- Text that already states the guarantee is made true, and a sentence on
  the history record and the edit-to-re-enter rule is added to:
  - `payload/docs/ai-workflow/MILESTONE_WORKFLOW.md`;
  - `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`;
  - `PLAN_REVIEW_WORKFLOW.md`;
  - `payload/.claude/commands/milestone-plan.md`;
  - `review-plan.md`;
  - `request-plan-amendment.md`.

**Tests:**

- the defect's sequence (dual-approve A, withdraw, publish and bind B,
  withdraw, restore A) refuses at `publish_plan_revision` with
  `ConsumedPlanReviewContentError`, and also at `bind_plan_review_bundle`
  given a hand-forged `PUBLISHED` record;
- the same through a `REVISE` consumption and through an amendment
  consumption;
- after restoring A and making any one-byte edit, the content publishes;
- migration: a 2.6.0-shaped item (slot only, no key) refuses its slot
  content, and its first 2.7.0 consumption writes `[old, new]`, sorted;
- a legacy marker adds nothing;
- `plan_review_publication_status` gives row 10 (`NEEDS_EDIT`) for a fresh
  id that is in the list but not in the slot, at a revision that differs
  from the one it was consumed at, and row 11 (`EDIT_IN_PROGRESS`) for a
  fresh id in neither;
- the validator refuses an unsorted, duplicated or non-hex list, and
  accepts a list without the slot id;
- downgrade, in two parts:
  - **Unit test:** the key is never written inside `plan_review_binding`,
    and a 2.7.0-written state with the key stripped validates, so the only
    difference 2.6.0 sees is a work-item key it ignores.
  - **One-off check, recorded as CP2 evidence in `docs/ACTIVE_MILESTONE.md`:**
    2.6.0's `validate_state` accepts a 2.7.0-written state. The conformance
    fixture has no tags, so this check cannot be a suite test. The exact
    command, run from the repository root with `STATE` set to a
    `WORKFLOW_STATE.json` written by CP2's code (the
    `TestConsumedPlanReviewHistory` migration scenario, dumped to a
    temporary file), is:

    ```text
    d=$(mktemp -d)
    git show v2.6.0:payload/scripts/workflow_state.py > "$d/workflow_state.py"
    git show v2.6.0:payload/scripts/workflow_fingerprint.py > "$d/workflow_fingerprint.py"
    python3 -c 'import json, sys; sys.path.insert(0, sys.argv[1]); import workflow_state as w; s = json.load(open(sys.argv[2])); w.validate_state(s); print("ACCEPTED", sorted(k for i in s["work_items"].values() for k in i if k == "consumed_plan_review_content_ids"))' "$d" "$STATE"
    ```

    The expected output is exactly
    `ACCEPTED ['consumed_plan_review_content_ids']`, with exit code 0. The
    evidence records the command, the output and the 2.6.0 blob ids of both
    scripts.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Protocol core

**Files (new):**

- `payload/scripts/workflow_protocol.py`:
  - argument parsing, with argparse errors converted to `invalid_request`;
  - the envelope writer;
  - the `WORKFLOW_RELEASE`, `PROTOCOL_VERSION` and `PROTOCOL_MAJOR`
    constants;
  - the error-code table;
  - `state_identity(work_item_id, state)` and `basis(...)`;
  - `describe`, `verify` and `resolve-artifact`;
  - read paths that never take a write lock.
- `payload/scripts/workflow_protocol_test.py`: the minimal schema checker
  and the tests below. It uses `workflow_test_harness` for scratch
  repositories.
- `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`: the
  envelope plus the `describe`, `verify` and `resolve-artifact` results.
  CP4 and CP5 extend it.

**Tests:**

- every response validates against the schema;
- `--protocol-major 2` gives `unsupported_protocol` and exit 3, with
  nothing else read;
- a bad argument gives `invalid_request` and exit 2, still as a JSON
  envelope;
- an injected unexpected exception gives `internal_error` and exit 1;
- the Workflow exception domain (D-OP-Errors, LPR-R4-001):
  - `is_workflow_exception` is true for every class `inspect.getmembers`
    finds in `workflow_state` and `workflow_fingerprint` that subclasses
    `Exception` and whose `__module__` is that module, including the two
    intermediates and their subclasses, and false for `KeyError`,
    `TypeError`, `ValueError`, `OSError` and an `Exception` subclass defined
    in the test module;
  - every key of the explicit mapping table names a class in that
    enumeration, so a renamed or removed class fails the test, and the
    table's code for each entry is pinned;
  - every enumerated class with no table entry maps to `refused`, never
    `internal_error`; a class defined at test time with `__module__` set to
    `workflow_state.__name__` (a stand-in for one added by a later release)
    maps to `refused`;
  - with `workflow_state` loaded through `importlib` under another module
    name and injected as the module `workflow_protocol` uses, its classes
    are still Workflow exceptions (the domain compares the module objects'
    `__name__`, not literals);
  - a raw `KeyError` raised from inside a patched `workflow_state` function
    that an operation calls gives `internal_error` and exit 1, and an
    `OSError` from the same place gives `internal_error`, while an
    unreadable lock file gives `state_unreadable`;
- `describe`'s lists equal the module tables;
- identity is stable under key order, changes when any work-item field
  changes, and does not change when another item changes;
- `verify`:
  - healthy on a fresh scratch repository;
  - each check fails on its own fault (corrupt JSON, an unknown phase, a
    dangling active id, a `COMPLETE` with no trailer commit, a mismatched
    installation record);
  - `skip` without an installation record;
- `resolve-artifact`:
  - for a scoped item, a legacy-flat item and a plan-stage phase, each path
    equals the direct helper's;
  - an unknown kind gives `invalid_request`;
- `verify` and `resolve-artifact` leave the state file and its mtime
  untouched.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — `next-action` and `reconcile`

**Files:**

- `payload/scripts/workflow_protocol.py`:
  - the catalogue as one ordered table of rows `{phases, versions,
    predicate, disposition, action builder}`;
  - `CONDITION_CALLS`, the per-row table of condition calls with their
    kind (guard, acceptance, value) and exception classes (LPR-R5-001);
  - the legal-edge table per action id, with its same-phase proofs and
    `allowed_results`;
  - `next-action` with `--expect-state-identity`;
  - `reconcile --decision`.
- `payload/scripts/workflow_state.py`: the two gate wrappers,
  `plan_approval_gate_status` and `technical_approval_gate_status`
  (D-OP-Next, LPR-R1-003), and `implementing_entry_status`, with
  `implementing_entry_reachable` reduced to its `reachable` field
  (LPR-R3-002); `verify_implementation_review_bundle` and
  `ImplementationReviewBundleUnverifiedError` (LPR-R5-002).
  Also `assert_apply_review_feedback_binding`,
  `FeedbackContentMismatchError` and `ReviewBundleManifestMismatchError`
  (D-Apply-Binding, MPR-R9-001, MPR-R10-001).
- `payload/.claude/commands/apply-plan-review.md` and
  `apply-implementation-review.md`: step 1's binding calls
  `assert_apply_review_feedback_binding` in place of
  `assert_feedback_matches_bundle`, and reports its advisory and its
  refusals by class. The `REJECTED`-bundle checks, the acceptance rule and
  the `"1"`/`"2.1"` `BLOCK` pin are unchanged (D-Apply-Binding).
- `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`: the "Required
  structure" paragraph on the binding fields, as D-Apply-Binding states.
- `payload/.claude/commands/review-implementation.md`: step 4's bundle
  check calls `verify_implementation_review_bundle` and reports its
  refusal; the prose that describes the check is reduced to naming it
  (LPR-R5-002).
- `payload/.claude/commands/milestone-implement.md`: 1a reports
  `implementing_entry_status`'s cause and remedy (LPR-R3-002).
- `payload/.claude/commands/approve-review.md`: the gate check calls the
  wrappers instead of computing the predicate inputs in its own steps. The
  step-1 `BLOCK` pin write stays where it is, ahead of the wrapper call,
  and the wrapper reads the state re-read after it (LPR-R2-008).
- `workflow_protocol_test.py`, and wrapper tests in `workflow_state_test.py`.
- The schema is extended.

**Tests:**

- **Totality:** for every phase in `KNOWN_PHASES` × governing versions
  `1`, `2.1` and `2.2`, every state reaches an explicit row, and none falls
  through. The enumeration is generated from `workflow_state.KNOWN_PHASES`
  and `SUPPORTED_GOVERNING_VERSIONS`, never from a repository's config, so
  a future phase or version without a row fails the test. A companion
  test pins `SUPPORTED_GOVERNING_VERSIONS` to
  `sorted({"1"} | TWO_STAGE_PLAN_REVIEW_VERSIONS)`, so removing `2.2` from
  the enumeration source fails, and runs the totality check in a scratch
  repository built with `default_config()` (`["1","2.1"]`) to show that
  the `2.2` rows are still enumerated (LPR-R4-003).
- **Row order:** the code's catalogue is one list, and the test asserts
  that its order equals the table's. For each row that pre-empts another,
  a state matching both is constructed and the earlier row wins.
- **Row tests:** each row is reached from a constructed state and returns
  its disposition, action id, invocation and worker. These include:
  - a manual `BLOCK` at `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` and at
    `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`, both recorded through
    `record-external-result` **and** pasted into fb by hand, gives
    `review.resolve_block` (rows 11, 25) and never the record action again;
  - the gate-unreachable rows 16, 30 and 34, one state per cause:
    `no_review_round`, `review_blocked`, `review_ledger_stale` (plan ledger
    keyed to older content), `review_block_pinned`, `protected_path_dirty`
    and `implementation_provenance_stale`, each giving `blocked` with that
    reason;
  - a wrapper-only regeneration (a new `bundle_id`, the same
    `review_content_id`) at `AWAITING_LOCAL_PLAN_REVIEW` and at
    `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` keeps rows 11, 12, 13 and 14
    matching exactly as before the regeneration;
  - row 8 for a legacy marker (`consumed.legacy`, fb matched by
    `Work item:`), and row 9 for a withdrawal;
  - the apply binding (D-Apply-Binding, MPR-R8-001, MPR-R9-001), through
    `assert_apply_review_feedback_binding` and through each command's
    step-1 sequence, which must agree:
    - at `REVISING_PLAN`, `2.1` and `2.2`, a `REVISE` that states the
      consumed `review_content_id`, once with no `Reviewed bundle ID:`,
      `Reviewed base commit:` or `Work item:`, and once with a
      `Reviewed bundle ID:` from before a wrapper-only regeneration, is
      accepted by content with the advisory, and the item gives row 8
      (`plan.apply_review`), never `plan.author`;
    - at `APPLYING_REVIEW_FEEDBACK`, `2.2`, the same two variants of a
      `REVISE` that states **B**'s manifest's `review_content_id` are
      accepted, also after the applier has committed a fix (**I** moved,
      the manifest's id did not), and the item gives row 36;
    - the forgery (MPR-R9-001): a `REVISE` whose `Reviewed bundle ID:`,
      `Reviewed base commit:` and `Work item:` were rewritten to **B**, the
      item's `base_commit` and its id, over a `review_content_id` that is
      not the reviewed content, is refused with
      `FeedbackContentMismatchError` at both stages, by the function and
      by both commands' step 1; at the plan stage the item gives row 9
      (another round's verdict), and at the implementation stage row 35a
      with `review_feedback_not_current`;
    - a bundle directory whose manifest names other content
      (MPR-R9-003): at `REVISING_PLAN`, a `REVISE` of the consumed content
      with `.ai-review/<id>/current/` replaced by a self-consistent bundle
      of another revision gives row 7a (`bundle_unverified`,
      `ReviewBundleManifestMismatchError`), never row 8; a bundle whose
      files differ from its manifest's `bundle_id` gives the same at both
      apply phases (row 7a, row 35a);
    - the bundle's owner and stage (MPR-R10-001): at
      `APPLYING_REVIEW_FEEDBACK`, `2.2`, with two items on the flat
      layout, a `REVISE` with no `Work item:` whose `review_content_id`
      equals the on-disk manifest's, where the manifest names another
      `work_item_id`, is refused with `ReviewBundleManifestMismatchError`
      and gives row 35a with `bundle_unverified`, by the function and by
      `/apply-implementation-review`'s step 1, never row 36; the same
      case at `REVISING_PLAN` gives row 7a; with a manifest that has no
      `work_item_id` line (a flat legacy generation), the bundle binding
      is selected, so the `REVISE` is refused with
      `MissingFeedbackBindingFieldError` (row 35a,
      `review_feedback_not_current`) unless fb's `Work item:`,
      `Reviewed bundle ID:` and `Reviewed base commit:` name this item,
      **B** and its `base_commit`, when it is accepted; a `stage: plan`
      manifest at the implementation stage, a `stage: implementation`
      manifest at the plan stage, and a manifest whose `base_commit` is
      not the item's are each refused by check 3
      (`ReviewBundleManifestMismatchError`);
    - the bundle binding is unchanged where it still applies: `"1"` and
      `"2.1"` items at `APPLYING_REVIEW_FEEDBACK` with a missing or
      mismatched binding field give row 35a's `review_feedback_not_current`,
      exactly as 2.6.0's step 1 refuses; a two-stage `BLOCK` or `APPROVE`
      is still refused before any binding;
    - row 8a: under a legacy marker, and for a `REVISE` that names this
      item but states no `review_content_id`, a bundle binding that
      refuses gives `blocked`, `review_feedback_unbound`, never
      `plan.author`; its remedy text names a new verdict for **B** and
      `plan.withdraw`, and a text test asserts that no catalogue remedy
      tells the operator to edit `Reviewed bundle ID:`,
      `Reviewed base commit:` or `Work item:`;
    - the unrecorded-`REVISE`-then-withdraw sequence (MPR-R9-002): a
      `REVISE` of the bound content written to fb without being recorded
      (both the manual paste at `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` and
      a `/review-plan` whose state write is made to fail after its file
      write), then `/milestone-plan <id>`'s withdrawal with the content
      unchanged, gives row 8, and `/apply-plan-review`'s step 1 accepts the
      state; a `REVISE` of an earlier round left in fb after a withdrawal,
      and no fb at all, give row 9 (the documented residual, MPR-R8-002);
  - **ingest-to-apply routing** (MPR-R8-001, the converse of the
    command-agreement test): for every ingest row and every verdict that
    `record-external-result` accepts there, including the optional-field
    variants above, the test records it, takes the next decision, and
    asserts that it is the stage's apply action whose command then accepts
    the state, a gate, or a `blocked` decision whose remedy is followable;
    it is never a different automatic action (`plan.author` in
    particular). A recorded two-stage `REVISE` gives the apply action
    itself (rows 8 and 36), never a block (MPR-R9-001). The same is
    asserted for `/review-plan`'s and `/review-implementation`'s own
    `REVISE` outputs;
  - the `"1"` plan round: no fb gives row 21; a current `REVISE` gives row
    18; after `/apply-plan-review`'s writer sequence (publish and
    regenerate), the same fb gives row 20, never `plan.apply_review` again;
    a current `APPROVE` gives row 19 and a current `BLOCK` row 17;
  - row 4 for each illegal (phase, `gv`) pair, including `REVISING_PLAN`
    at `1`;
  - `"1"`/`"2.1"` at `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`: a current
    `BLOCK`, and a pinned `BLOCK` whose fb was edited to `REVISE`, each give
    row 31 (`implementation.apply_review`); after `/apply-implementation-review`'s
    writer sequence (pin, then post-fix republication), the same item gives
    row 35. A `"1"` plan `BLOCK` gives row 17 (`plan.apply_review`), and
    after the apply, row 21. At `2.2`, row 30 for `review_blocked` and
    `review_block_pinned` carries the `implementation.apply_review`
    alternative (LPR-R2-001);
  - HEAD moved past `generation_head`, and a different worktree root, at
    `AWAITING_LOCAL_PLAN_REVIEW`, at `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW`
    with an unrecorded manual verdict, and at
    `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, give rows 11a and 25a
    (`blocked`, `bundle_generation_mismatch`), never the review or record
    action; at `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` with no fb, row 14 is
    unaffected; at `AWAITING_PLAN_APPROVAL` and the technical gate the
    wrapper reports `bundle_generation_mismatch` (LPR-R2-002);
  - row 35 with an applied `REVISE` and a reachable technical gate lists
    `implementation.approve` (`user_only`) as an alternative, and without
    it does not (LPR-R2-006);
  - row 38 with an unconsumed `FUNCTIONAL_REVIEW.md`, and row 39 once it is
    marked consumed (LPR-R2-007);
  - `"1"` items (LPR-R3-001): no active item with
    `default_workflow_version: "1"` gives row 1a (`blocked`,
    `plan_start_not_tracked`), never `plan.start`; a `"1"` item at
    `PLANNING`, at `AMENDING_PLAN` and at `IMPLEMENTING` gives row 6a
    (`blocked`, `v1_state_not_advanced`), never `plan.author`,
    `implementation.checkpoint` or `implementation.self_review`. The
    `IMPLEMENTING` case is constructed with a registry whose checkpoints
    have no state status, as a `"1"` item has; `SELF_REVIEWING_IMPLEMENTATION`
    at `"1"` gives row 4; row 39 at `"1"` lists `milestone.accept` for a
    registry-less item;
  - the functional gate's registry read (LPR-R4-002, LPR-R4-004), with a
    consumed `FUNCTIONAL_REVIEW.md` and current checklist evidence so that
    rows 37 and 38 do not match:
    - at `2.2`, a plan-stage protected file edited after approval makes
      `resolve_own_registry_completion_status` raise
      `StalePlanApprovalRegistryReadError`, and the item gives row 38a
      (`blocked`, `plan_content_drifted`, remedy naming the restoration of
      the approved bytes and not naming `/request-plan-amendment`), never
      `milestone.accept` and never row 39 (LPR-R6-001);
    - at `2.2`, a registry file whose `work_item_id` names another item
      gives row 38a with `registry_unreadable` (`RegistryCoverageError`);
    - the same two states at `"1"` give the same row 38a results;
    - at `"1"`, an item with a registry whose checkpoints are not
      terminal, constructed with a `CURRENT` `plan_approval` whose
      `review_content_manifest` covers the live registry and plan bytes
      (so the call returns `(False, <id>)` rather than raising), gives row
      38b (`blocked`, `v1_state_not_advanced`), never `milestone.accept`
      and never `implementation.checkpoint`; the same construction with
      every checkpoint terminal gives row 39 with `milestone.accept`;
    - at `2.1` and `2.2`, the covering construction with an incomplete
      registry gives row 38c (`blocked`, `registry_incomplete`,
      `remedy_commands` `none_exists`, the text naming `v2.6.0-003` and not
      naming `/request-plan-amendment`), never `milestone.accept` and never
      `implementation.checkpoint` (LPR-R5-003, LPR-R6-001);
    - a `"1"` item with a non-terminal registry and a covering `CURRENT`
      `plan_approval`, promoted through `promote_legacy_work_item` (so it
      is persisted at `"2.1"` `AWAITING_FUNCTIONAL_REVIEW`), gives row 38c,
      the reachable origin beside the hand-constructed case (LPR-R6-001);
  - the raising-condition rule (LPR-R4-002): a value call patched to
    raise an unmapped Workflow exception gives `blocked`,
    `condition_refused`, with the class and message in `reason`, and the
    envelope is `ok: true`; the same call patched to raise `KeyError`
    gives `internal_error` and exit 1; in neither case is a later row's
    action emitted;
  - the acceptance calls (LPR-R5-001), each through a real state, not a
    patch:
    - the `"1"` plan round with a stale fb (its `Reviewed bundle ID` an
      earlier bundle) reaches row 20 for a `REVISE` and row 21 for an
      `APPROVE`, and an `APPROVE` with no `Reviewed base commit:` line
      reaches row 21 (through `MissingFeedbackBindingFieldError`); none gives `condition_refused`;
    - a stale fb at the `"1"` and `"2.1"` `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`
      reaches row 35;
    - a withdrawal that leaves the prior round's `REVISE`, and one that
      leaves a local `APPROVE`, in fb reach row 9 (through
      `FeedbackContentMismatchError` and `FeedbackStatusNotApplicableError`
      respectively); a `PUBLISHED_UNBOUND` item whose fb names other
      content reaches row 9 through `FeedbackNotForConsumedContentError`;
    - a consumed `FUNCTIONAL_REVIEW.md` reaches row 39;
    - for each acceptance call, the same call patched to raise each of its
      listed classes falls through to the next row, and patched to raise an
      unlisted Workflow exception gives `condition_refused` at that row;
  - `CONDITION_CALLS` (LPR-R5-001): every catalogue row id has an entry
    (empty for a row with no condition), and every entry's id is a
    catalogue row; every class name in it resolves to a class in the
    D-OP-Errors enumeration; every call has one of the three kinds; the
    predicates evaluate no Workflow function that their row's entry does
    not list (each listed function is patched to a recorder, and an
    unlisted call fails the test; a value reused from an earlier row's
    evaluation counts as reached by every row that reads it, so row 8's
    `plan_review_publication_status` must be listed even when row 5
    computed it, LPR-R6-003); CP6 compares the specification's copy of
    the table with the code's;
  - bundle integrity (LPR-R5-002): at `2.2` `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`,
    and at `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` with an
    unrecorded manual verdict, a missing bundle directory, a bundle with a
    required file removed, a bundle whose files differ from `MANIFEST.md`'s
    `bundle_id`, and a manifest whose `review_content_id` is not **I** each
    give row 25b (`blocked`, `bundle_unverified`), never
    `implementation.review.local` or `implementation.record_external`; at
    `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` with no fb, a missing
    bundle directory also gives row 25b, never row 28's external gate, and
    a valid bundle with no fb gives row 28 (LPR-R6-002); row 25b's remedy
    names `implementation` at `implementation_revision` 1 and `post-fix`
    after a `REVISE` round, and so do rows 30 and 30a (LPR-R6-004); a
    missing bundle directory gives row 16a at the `"1"` plan
    gate, row 30a at the `"1"`/`"2.1"` implementation gate, and row 30 with
    `bundle_unverified` at the `2.2` technical gate;
  - `verify_implementation_review_bundle` itself: it returns the identifiers
    for a freshly generated bundle, and raises
    `ImplementationReviewBundleUnverifiedError` for each of the four faults
    above and for a plan-stage `MANIFEST.md`, naming that variant;
  - the implementing entry (LPR-R3-002), at `IMPLEMENTING` and at
    `SELF_REVIEWING_IMPLEMENTATION`, `2.1` and `2.2`: `plan_approval`
    `STALE` gives row 22 with `plan_approval_not_current`; `CURRENT` with
    a plan-stage protected file edited after approval gives
    `plan_content_drifted`; `CURRENT` with HEAD reset to a commit that does
    not contain the approval commit gives `plan_approval_commit_unreachable`.
    None of them gives `implementation.checkpoint` or
    `implementation.self_review`. `implementing_entry_status` reports the
    same three causes directly, and `implementing_entry_reachable`'s
    existing tests stay green;
  - pinned implementation `BLOCK`s at `"1"` and `"2.1"`
    `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (LPR-R3-003): with fb deleted,
    and with fb whose `Work item:` names another item, the item gives row
    31a (`external_gate`, `review_block_pinned`), never an automatic
    `implementation.apply_review`. After a verdict for the same bundle is
    placed through `record-external-result`, it gives row 31.
- **Gate wrappers:** for each cause, the wrapper reports it, and, whenever
  the generation check passes, `reachable` equals the pure predicate called
  on the wrapper's own `inputs`. `/approve-review`'s text names the
  wrappers, and its `record_technical_review_block_pin` write precedes the
  wrapper call (text test); a `BLOCK` fb at the technical gate, run through
  the command's writer sequence, leaves the pin recorded and the wrapper
  reporting `review_block_pinned` (LPR-R2-008). The cause order
  (LPR-R3-004): a pinned `BLOCK` with HEAD moved past `generation_head`
  reports `bundle_generation_mismatch`, and after the recovery
  `review_block_pinned`; at the plan stage, a binding changed between the
  catalogue's read and the wrapper's gives `plan_review_bundle_unbound`.
- **Command agreement:**
  - for each `automatic` row, the named command's full pre-write guard
    sequence accepts the state. The test holds, per automatic action id,
    every guard function the command document calls before its first
    write, in order (for example `plan.review.local`:
    `assert_local_generation_matches`, `assert_bundle_not_rejected`,
    `assert_plan_review_bundle_bound`, then the local-review
    preconditions; `implementation.review.local`:
    `verify_implementation_review_bundle`, `assert_local_generation_matches`,
    `assert_bundle_not_rejected`, then the local-review preconditions;
    `plan.apply_review`: `assert_plan_review_entry_phase`, the feedback
    file's presence, `assert_bundle_not_rejected`,
    `assert_apply_plan_review_feedback`, then
    `assert_apply_review_feedback_binding` with `stage="plan"` when it
    returned `"bundle"`; `implementation.apply_review`: the feedback
    file's presence, `assert_bundle_not_rejected`, then
    `assert_apply_review_feedback_binding` with `stage="implementation"`,
    which computes **B** itself). A text test asserts that each listed
    function appears in the command document, and that neither apply
    command's step 1 still names `assert_feedback_matches_bundle` as its
    own call (D-Apply-Binding: the binding function makes that call for
    the bundle binding). The behaviour test invokes all of them on the
    row's state (LPR-R2-002), including, for `plan.apply_review` (row 8,
    `2.1` and `2.2`) and `implementation.apply_review` (row 36, `2.2`),
    the content-bound `REVISE` variants the apply-binding tests above
    construct: one with no `Reviewed bundle ID:`, `Reviewed base commit:`
    or `Work item:`, and one whose `Reviewed bundle ID:` is stale after a
    wrapper-only regeneration. Each passes the full sequence, the binding
    function returning `binding: "content"` with its advisory, so the
    automatic action is one the command accepts (MPR-R11-001). For a
    `"1"`/`"2.1"` implementation row, the same sequence takes the bundle
    binding, and the test asserts it.
  - the apply rows' pre-emptions (MPR-R7-001): at `REVISING_PLAN`
    (`2.1`, `2.2`) with an applicable `REVISE` and a `REJECTED` marker, the
    decision is row 6, not row 8; with no marker and no plan bundle
    directory, in `"bundle"` mode, it is row 7a (`bundle_unverified`). At `APPLYING_REVIEW_FEEDBACK`, at every
    `gv`: a `REJECTED` marker gives row 6; with the marker absent, no feedback
    file gives row 35a with `review_feedback_missing`, an absent bundle
    directory (a fresh worktree) gives `bundle_unverified`, and a feedback
    file for another bundle gives `review_feedback_not_current`; in each of
    these, `/apply-implementation-review`'s step-1 sequence refuses the same
    state. Only a current feedback file for **B** with no marker gives row
    36.
  - the test enumerates **two things per automatic row and governing
    version**: the command's entry check (the function the command
    actually calls, not the state field it reads first) and the
    per-version writer sequence it then performs. `implementation.checkpoint`
    and `implementation.self_review` list `implementing_entry_status`;
    `plan.start` lists `load_config` and `route_work_item`. A `"1"` branch
    that is v1-inert is listed with its own (empty or partial) writer
    sequence, so a catalogue row that emits a two-stage-only writer for a
    `"1"` item fails the test. This is the check that would have caught
    LPR-R3-001 and LPR-R3-002.
  - for each `(row, gv)` pair the catalogue marks `automatic`, the writer
    sequence applied to the row's state ends on one of the action's legal
    edges, or leaves the state unchanged.
  - for each `blocked`, `human_gate` and `external_gate` row and each `gv`
    it covers, every command id in its `remedy_commands` accepts the row's
    phase: the command's phase gate is evaluated on the row's state (for
    example `request_plan_amendment`'s `_AMENDMENT_REQUEST_ALLOWED_PHASES`,
    `transition_checkpoint_in_progress`'s `CHECKPOINT_START_LEGAL_PHASES`),
    and a refusal fails the test. Every command in its `refusing_commands`
    refuses the row's state, and an acceptance fails the test. A text test
    asserts that every slash command named in the row's remedy or
    alternatives prose is in exactly one of the two fields. This is the
    check that would have caught LPR-R5-003 and LPR-R6-001.
  - for each `user_only` action, the command file carries
    `disable-model-invocation: true`, and for each action that is not
    `user_only`, it does not (this covers
    `implementation.recover_provenance`).
- **Stale decision:** `--expect-state-identity` with an old identity gives
  `stale_decision` with `retryable: true`.
- **Edge table:** for every automatic action id, `next-action`'s
  `allowed_results` equals the edge table's; every edge's phases are in
  `KNOWN_PHASES` and legal for the edge's `gv` under row 4.
- **Reconcile classes**, each asserted against the edge table's
  `allowed_results` for the action:
  - `progress` for a phase change;
  - same-phase checkpoint progress, with a trailer commit present, gives
    `progress`;
  - the same without the trailer commit gives `invalid`;
  - an unchanged state after `implementation.checkpoint` gives
    `no_progress`;
  - a checkpoint moved to `IN_PROGRESS` with none completed gives
    `no_progress`, with `evidence.started_checkpoints` naming it;
  - an unchanged state after a `BLOCK` gives `gate_reached`, because the
    new decision is `review.resolve_block`;
  - an unchanged state with no new verdict after `plan.review.local` gives
    `no_progress`;
  - `"1"` `plan.apply_review` with the revision advanced gives
    `gate_reached` (row 20), and without it `no_progress`; neither calls
    `plan_review_publication_status` (LPR-R2-004);
  - `plan.start` with exactly one new item gives the class of its new
    phase, with `from: null` (LPR-R2-005); with no new item and no active
    item it gives `no_progress`, with `from` and `to` `null` (LPR-R3-006);
    with two new items, a new item that is not the active one, or no new
    item and a set pointer, it gives `invalid` (`plan_start_item_ambiguous`);
  - a class outside `allowed_results` gives `invalid`
    (`result_not_allowed`);
  - an illegal edge gives `invalid`;
  - reaching `AWAITING_PLAN_APPROVAL` gives `gate_reached`;
  - `reconcile` never returns `complete`: an automatic decision followed by
    a state at `MILESTONE_COMPLETE` gives `invalid` (no legal edge), and
    the item's `next-action` there gives disposition `complete` (row 40)
    (MPR-R7-003);
  - a decision for another item, a tampered decision, or a decision whose
    disposition is not `automatic`, gives `invalid_request`.
- `next-action` and `reconcile` never write.

<!-- /CP4 -->

<!-- CP5 -->
### CP5 — `record-external-result` and the shared ingest

**Files:**

- `payload/scripts/workflow_state.py`: `ingest_manual_review_verdict`,
  `ManualVerdictHeaderError`, `ConflictingReviewFeedbackError`, and
  `state_transaction`'s `before_publish` keyword (MPR-R7-002).
- `payload/scripts/workflow_protocol.py`: the operation.
- `payload/.claude/commands/record-manual-plan-review.md` and
  `record-manual-implementation-review.md`: the step list now calls the
  ingest, and the guard order is documented once, in the function. The
  implementation-stage ingest row calls CP4's
  `verify_implementation_review_bundle` in step 5's position, which is why
  CP5 depends on CP4 (LPR-R5-002).
- `payload/scripts/workflow_fingerprint.py`: the docstrings of
  `assert_local_generation_matches` and `WorktreeOrHeadMismatchError` name
  the record-manual commands as callers (LPR-R2-002).
- Tests in `workflow_state_test.py` (the ingest) and
  `workflow_protocol_test.py` (the operation).
- The schema is extended.

**Tests:**

- `APPROVE`, `REVISE` and `BLOCK` for both stages give the same state as
  2.6.0's command-driven sequence. This is asserted against the existing
  `record_manual_*` writers' expected state.
- Refusals:
  - a foreign `Work item:`;
  - a rejected bundle;
  - an unbound plan bundle;
  - a wrong role;
  - a `review_content_id` mismatch;
  - a missing local `APPROVE`;
  - a duplicate (`not_applicable`);
  - a missing required field (`ManualVerdictHeaderError`);
  - HEAD moved past `generation_head`, or a different worktree root
    (`WorktreeOrHeadMismatchError`, nothing written);
  - at the `2.2` implementation row, a missing bundle directory and a
    bundle whose files differ from `MANIFEST.md`'s `bundle_id`
    (`ImplementationReviewBundleUnverifiedError`, neither the feedback file
    nor the state written, as 2.6.0's command refuses both), and the
    verifier runs before `assert_local_generation_matches` (a state that
    fails both reports the verifier's refusal) (LPR-R5-002);
  - a `REJECTED` marker placed after the guards ran but before the write
    (the pre-write re-check refuses, nothing written).
- 2.6.0 compatibility at the two-stage rows (LPR-R2-003): a verdict that
  opens with `## Review Decision` and states its fields under it is
  accepted, and a verdict with no `Work item:` is accepted, each recording
  the same state as 2.6.0's command; a verdict whose `review_content_id`
  appears only after a `## ` section that follows its fields is refused
  (`ManualVerdictHeaderError`), the one documented tightening.
- The crash window: the file is written, the state write is simulated to
  fail, and a retry through the command path and through the protocol
  each record once.
- Concurrent ingests (MPR-R7-002), with real, separate processes, as the
  existing `state_lock` tests use: at each two-stage row, two valid
  verdicts with different `Status:` values for the same content, started
  together. Exactly one records; the other refuses before writing; and the
  final `REVIEW_FEEDBACK.md` parses to the verdict the ledger recorded. The
  same with the first ingest paused (by a test hook) between its guards
  and its file write: the second blocks on the lock until the first
  publishes. At each feedback-only row, two different current verdicts:
  one is stored, the other refuses with `ConflictingReviewFeedbackError`,
  and the file holds the stored one; an identical second verdict is the
  no-op.
- `state_transaction`'s `before_publish`: an exception from it leaves
  `WORKFLOW_STATE.json` byte-identical; without it, every existing
  `state_transaction` test passes unchanged. Its position (MPR-R8-003): a
  mutator whose result fails `_assert_technical_review_block_pins_monotonic`
  never calls the hook, and leaves both the feedback file and
  `WORKFLOW_STATE.json` byte-identical; a recorded call order shows the
  checks, then the hook, then `_publish_state_file`.
- A manual `REVISE` recorded through `record-external-result` at the `2.1`
  and `2.2` plan rows and at the `2.2` implementation row (MPR-R8-001),
  once with no `Reviewed bundle ID:` and once naming the bundle id from
  before a wrapper-only regeneration: each is recorded by D-OP-External's
  `bundle_id` rule (`null` with the absent advisory, or the stated id with
  `check_manual_stage_bundle_id_advisory`'s mismatch advisory), and the
  next decision is the stage's apply action (row 8 or 36), whose command's
  step 1 then accepts the stored file by content (D-Apply-Binding,
  MPR-R9-001), never `plan.author`, row 8a or row 35a.
- The identical-bytes no-op.
- Each row of the ingest table (D-OP-External), through
  `record-external-result`:
  - `plan_review_verdict` at `1` (`AWAITING_EXTERNAL_PLAN_REVIEW`) and
    `implementation_review_verdict` at `1` and at `2.1`
    (`AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`), each with and without the
    pinned label: stored, the state unchanged, and the stored file then
    accepted by `assert_feedback_matches_bundle`;
  - each of those refused for a foreign `Work item:`, a rejected bundle,
    and a `Reviewed bundle ID` that is not the current bundle;
  - a two-stage kind at a `"1"`/`"2.1"` item, and a feedback-only kind at a
    two-stage phase, give `not_applicable`;
  - for a two-stage row, a missing `Reviewed review_content_id:` refuses
    with `ManualVerdictHeaderError`; for a feedback-only row, it does not.
- Reserved kinds give `unsupported_result_kind`, and the wrong phase gives
  `not_applicable`.
- A verdict with only the legacy spaced label is accepted. A verdict with
  only the pinned label is accepted.
- `round` and `bundle_id` (LPR-R3-005), for both two-stage stages: a
  verdict with `Round: 4` records round 4; a verdict with no `Round:`
  records the round of the local `APPROVE` for the same content; a
  `Round:` that is not a positive integer refuses with
  `ManualVerdictHeaderError`, nothing written; an `APPROVE` with no
  `Reviewed bundle ID:` records `bundle_id: null`, reports the advisory
  `"Reviewed bundle ID: absent"`, does not call
  `check_manual_stage_bundle_id_advisory`, and leaves a state that
  `validate_state` accepts. The command path and the protocol path give the
  same values.

<!-- /CP5 -->

<!-- CP6 -->
### CP6 — Specification, documentation, lifecycle E2E

**Files:**

- `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (new, distribution)
  is the normative specification:
  - versioning rules;
  - the envelope, the error codes and the exit codes;
  - each operation's request and result, referencing the schema;
  - the catalogue table, the condition-call table (`CONDITION_CALLS`,
    with the three kinds and the raising-condition rule) and the legal-edge
    table, which the code mirrors (a test checks that the document's three
    tables equal the code's tables, by parsing the Markdown);
  - worker roles;
  - consumer obligations (validate, fail closed on unknown majors and
    values, check identity before launch, pass the decision back verbatim);
  - what is reserved for W2;
  - the compatibility notes (D-Feedback-Label, D-Consumed-History).
- `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`: a short "Driving the Workflow by
  protocol" section and a pointer from "Which command do I run next?" to
  `next-action`.
- `MILESTONE_WORKFLOW.md`: one paragraph stating that the protocol reports
  the same gates and adds none. The hard-gate count is unchanged.
- `payload/.claude/commands/accept-milestone.md`: step 2a's "finish it with
  `/milestone-implement`" is corrected to say that `/milestone-implement`
  cannot start a checkpoint from `AWAITING_FUNCTIONAL_REVIEW` and that no
  2.6.0 command completes it (defect `v2.6.0-003`), the statement row 38c
  reports. The bullet's second half, the 2.6.0 bounded/broad routing of
  functional-review findings through `/apply-functional-review`, is kept
  unchanged. A text test pins that the step names neither
  `/milestone-implement` nor `/request-plan-amendment` as a way forward
  from this phase, and that the routing sentence is still present
  (LPR-R5-003, LPR-R6-001).
- `workflow_protocol_test.py`: **the lifecycle E2E.** A disposable
  repository (`workflow_test_harness`) is driven from `PLANNING` to
  `MILESTONE_COMPLETE` for a `"2.2"` item:
  - at every step the test takes only `next-action`'s `action.id` and
    `arguments`, applies the corresponding Workflow writer sequence (the
    same functions the command invokes), calls `reconcile` and asserts its
    class;
  - both manual verdicts enter through `record-external-result`;
  - it covers a `REVISE` round at each review stage and two checkpoints
    with same-phase progress.

  Two shorter runs cover a `"1"` item, using only what the `"1"` commands
  write (LPR-R3-001). No `"1"` command creates an item, so each starts
  from a pre-constructed `"1"` state entry (`default_work_item` with
  `governing_workflow_version: "1"`, the constructor that
  `create_remediation_child_work_item` and `import_legacy_work_item` use),
  in the phase that the named 2.6.0 writer persists:
  - **Plan round**, from `AWAITING_EXTERNAL_PLAN_REVIEW` as
    `publish_plan_revision`'s `"1"` branch writes it. No fb gives row 21.
    A `REVISE` placed by `record-external-result` gives row 18, and
    `plan.apply_review`, applied as `/apply-plan-review`'s `"1"` writer
    sequence (publish and regenerate), reconciles to `gate_reached` (row
    20, never row 18 again). The approval is applied as the user's writer
    sequence (`apply_plan_approval`), and the next decision is row 6a
    (`blocked`, `v1_state_not_advanced`) at `IMPLEMENTING`, never an
    implementation action.
  - **Implementation round**, from `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`
    as `record_bundle_generation` writes it, with `registry_path: null`.
    No fb gives row 35. A `REVISE` placed by `record-external-result` gives
    row 32, and `implementation.apply_review`, applied as
    `/apply-implementation-review`'s `"1"` writer sequence, reconciles to
    `gate_reached` (row 35). An `APPROVE` then gives row 33; the approval
    is applied as the user's writer sequence; the functional rows follow,
    and `milestone.accept`, applied as `complete_work_item`, is followed by
    `next-action`, whose disposition is `complete` (row 40).

  The gates in all three runs follow one contract (MPR-R7-003): `reconcile`
  is called only after an automatic action. After a gate's action is
  applied as the user's writer sequence (`plan.approve`,
  `implementation.approve`, `milestone.accept`), or a verdict is recorded
  through `record-external-result`, the test calls `next-action` and
  asserts the new decision. Passing a gate's own decision to `reconcile` is
  asserted once, to refuse with `invalid_request`. The `"2.2"` run and the
  `"1"` implementation run end with `next-action` returning `complete`.

<!-- /CP6 -->

<!-- CP7 -->
### CP7 — Release 2.7.0

**Files:**

- `manifest.json`:
  - `workflow_version: "2.7.0"`;
  - new artifact entries: `scripts/workflow_protocol.py` and
    `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` and the schema
    (`distribution`), and `scripts/workflow_protocol_test.py`
    (`conformance`), each with `rule`, `rationale`, `sha256`, `size` and
    `executable`;
  - refreshed `sha256`/`size` for every changed file;
  - `counts`;
  - `provenance` per `OD-W1-4`;
  - each changed entry's `rationale` names W1.
- `templates/.github/workflows/workflow-conformance.yml`: a step for
  `workflow_protocol_test.py`. The template's `sha256`/`size` in
  `manifest.templates` is updated.
- `.github/workflows/workflow-ci.yml` (repository CI, not the installation):
  the same suite in `release-source-conformance`.
- `tools/release/package.py` (or `release.py build`): the **release-constant
  guard**. When the staged payload has `scripts/workflow_protocol.py`, its
  `WORKFLOW_RELEASE = "<v>"` literal must equal the manifest's version, or
  the build refuses and names both. `tools/release/release_test.py` gets
  tests for it: a match, a mismatch, and absence for 2.6.0 and earlier, so
  the five-release reproduction still passes.
- `docs/ROADMAP.md`:
  - the W1 row is marked complete;
  - a "Workflow 2.7.0" released-version entry;
  - the defect summary rows for `v2.6.0-001` and `v2.6.0-002` are marked
    "Fixed in 2.7.0";
  - a new row, `v2.6.0-003-v1-state-tracked-item-cannot-advance`, "Open;
    reported as `blocked` by the protocol", "Follow-up in a later Workflow
    release" (`OD-W1-10`). Its text names both gaps: `/milestone-plan`'s
    `"1"` branch writes no state at `PLANNING`/`AMENDING_PLAN`, and
    `/milestone-implement`'s `"1"` step 4 calls `record_bundle_generation`
    from `IMPLEMENTING`, which refuses. It notes the consequence at the
    functional gate: a `"1"` item with a registry can never pass
    `/accept-milestone`'s step-2a pre-flight (row 38b, LPR-R4-004). It also names
    `apply-functional-review.md`'s remediation-child sentence that assumes
    the first one works, and the related 2.6.0 prose inaccuracy that CP6
    corrects: `accept-milestone.md` step 2a told the operator to finish an
    outstanding checkpoint with `/milestone-implement` from
    `AWAITING_FUNCTIONAL_REVIEW`, where `transition_checkpoint_in_progress`
    refuses (LPR-R5-003). It records the `2.1`/`2.2` counterpart of the
    functional-gate gap: no 2.6.0 command completes an outstanding
    checkpoint from `AWAITING_FUNCTIONAL_REVIEW` at any `gv`
    (`/request-plan-amendment` refuses at that phase, and neither
    `/apply-functional-review` branch makes the parent's registry
    terminal), reachable from a legacy promotion or a hand-constructed
    state (row 38c, LPR-R6-001).
- `docs/RELEASING.md`: only if the guard needs a sentence.

**Verification:**

- `release.py build --commit HEAD` reports version 2.7.0;
- `package verify` and a scratch bootstrap/verify pass with the pinned
  Manager 1.2.0;
- `check-title "feat: Workflow 2.7.0 with Orchestration Protocol v1" --agree`
  passes;
- `check-pending` reports `2.6.0 -> 2.7.0 (minor)`;
- `check-immutable` reports that 2.7.0 is not published;
- all eight release-source suites are green in the staged fixture;
- `release_test.py` is green, including the five-release reproduction;
- `workflow-manager verify .` is clean.

<!-- /CP7 -->

## 6. Tests and verification summary

| what | where | when |
| --- | --- | --- |
| label pin, alias, header-only parsing | `workflow_fingerprint_test.py` | CP1 |
| consumed history, migration, downgrade, the defect's sequence | `workflow_state_test.py` | CP2 |
| envelope, versioning, errors, identity, `describe`, `verify`, `resolve-artifact`, schema | `workflow_protocol_test.py` | CP3 |
| catalogue totality, row order and rows, gate wrappers, command agreement, stale decisions, edge table and `reconcile` classes | `workflow_protocol_test.py`, `workflow_state_test.py` | CP4 |
| shared ingest equivalence, the per-(stage, version) table, refusals, crash window | `workflow_state_test.py`, `workflow_protocol_test.py` | CP5 |
| spec tables equal code tables; protocol-only lifecycle E2E (`2.2`; and two `1` runs from pre-constructed entries) | `workflow_protocol_test.py` | CP6 |
| release-constant guard; five-release reproduction intact; package, verify, bootstrap of 2.7.0 | `release_test.py`, local `release.py`, CI | CP7 |
| the existing seven suites stay green | release-source conformance fixture | every checkpoint |
| installation untouched | `workflow-manager verify .` | every checkpoint, acceptance |

## 7. Release and follow-ups (owner actions, after acceptance)

1. Open the pull request from this branch with the title `feat: Workflow
   2.7.0 with Orchestration Protocol v1` (impact `minor`, which agrees with
   2.6.0 → 2.7.0). Merge it when `aggregate`, `Conventional Commit title`
   and `workflow-conformance` are green. `Release` then publishes `v2.7.0`
   and reads it back (`docs/RELEASING.md`).
2. Open a `workflow-manager` pull request that pins 2.7.0:
   - the archive and manifest digests;
   - `CI_SUITES["2.7.0"]` with eight suites and their exact test counts;
   - the portability-exceptions entry.
3. Afterwards, install 2.7.0 into this repository with `workflow-manager
   update`, in its own pull request.
4. **The Controller, until C9.** Controller 1.5.0 refuses 2.7.0, because
   that release is not in its validated set and it pins script hashes. Do
   not update a Controller-driven repository to 2.7.0 until the Controller
   admits it. 2.7.0 keeps both 2.6.0 query CLIs byte-compatible, but that
   alone is not enough for an interim Controller release. 2.7.0's
   `/review-plan` and `/review-implementation` write
   `Reviewed review_content_id:` (D-Feedback-Label), and Controller 1.5.0's
   parser matches only `Reviewed review content ID:`, so it would find no id
   in 2.7.0-written feedback. An interim release would also have to accept
   the pinned label (LPR-R2-009).
5. Write `v2.6.0-003-v1-state-tracked-item-cannot-advance.md` in
   `workflow-manager`'s `docs/defects/`, beside `v2.6.0-001` and
   `v2.6.0-002`, from plan D-OP-Next's "`"1"` items" paragraph and its
   reproduction (`OD-W1-10`, LPR-R3-001). It also records `accept-milestone.md`
   step 2a's `/milestone-implement` sentence as a 2.6.0 prose inaccuracy,
   corrected in 2.7.0 (LPR-R5-003), and the `2.1`/`2.2` functional-gate
   case: no 2.6.0 command, `/request-plan-amendment` included, completes an
   outstanding checkpoint from `AWAITING_FUNCTIONAL_REVIEW`; a legacy
   promotion reaches that state (row 38c, LPR-R6-001). The gap stays open
   in 2.7.0, which only reports it.

## 8. Risks

| risk | mitigation |
| --- | --- |
| The catalogue disagrees with what a command actually accepts | the catalogue's conditions call the commands' own guard functions, each with a declared kind in `CONDITION_CALLS` (LPR-R5-001); a command's prose check is made a function before a row relies on it (`verify_implementation_review_bundle`, LPR-R5-002); and the approval gates go through the wrappers `/approve-review` also calls; CP4's command-agreement tests; the E2E is driven by `next-action` alone |
| The catalogue's precedence is misread | the printed order is the evaluation order, with no other precedence rule; CP4's row-order test; CP6 compares the specification's table with the code's, in order |
| The `/approve-review` rewrite changes what the gate accepts | the wrappers call the unchanged pure predicates; a test asserts `reachable` equals the predicate on the wrapper's own inputs; the predicates' existing tests stay |
| A future phase or governing version is added without a catalogue row | the totality test is generated from `KNOWN_PHASES` and `SUPPORTED_GOVERNING_VERSIONS`, which a test pins to the versions `workflow_state` accepts; the unknown case is `blocked` (`invalid_state` / `phase_not_legal_for_governing_version`), never automatic |
| The spec and the code drift | a test parses the spec's catalogue and edge tables and compares them with the code's; `describe` is pinned to the module tables |
| Header-only parsing rejects a verdict that 2.6.0 accepted | the required structure always placed the ID in the header; compatibility note; alias tests; the Controller already parses only the header |
| Stricter consumed-content refusal surprises an operator who reverts a plan | the refusal names the content and the remedy ("edit the plan"); the operator reference states the edit-to-re-enter rule; any one-byte edit suffices |
| The 2.6.0 single-slot migration loses earlier history | it is stated as the one residual; it cannot be reconstructed, and the slot itself is preserved |
| A downgraded installation writes a slot that the list lacks | the checker reads the union; the validator does not require containment |
| The ingest refactor changes what the record-manual commands do | equivalence tests against 2.6.0's writer outcomes for every verdict; the guard order is unchanged, including the implementation bundle verifier (step 5's recompute, LPR-R5-002), the generation check and the pre-write `REJECTED` re-check; the required fields are 2.6.0's, with header-only `review_content_id` the one stated tightening (CP5 compatibility tests) |
| Another work item's verdict is applied, because the content binding does not require `Work item:` | check 3 requires the bundle's manifest to name this item, its `base_commit` and the stage, and a manifest that names no item keeps 2.6.0's bundle binding, which requires `Work item:`; CP4 tests drive the flat-layout cross-item case to row 35a (MPR-R10-001) |
| A recorded `REVISE` that its apply command refuses is routed to another automatic action | the apply commands bind a two-stage `REVISE` by content, as the ingest does (D-Apply-Binding), so a recorded `REVISE` is accepted at its apply; row 8a blocks the remaining unbindable fb, with a remedy that never edits the verdict; CP4's ingest-to-apply routing test drives every accepted ingest verdict into its next decision (MPR-R8-001, MPR-R9-001) |
| The loosened apply binding accepts a verdict for other content | the content binding compares fb's `review_content_id` with the consumed id (plan) and with the on-disk bundle's manifest, and checks that bundle against its manifest; a rewritten `Reviewed bundle ID:` over other content is refused; the `"1"`/`"2.1"` and legacy bindings are unchanged (CP4 tests) |
| A crash between the feedback write and the state write | the file is written first; retry is idempotent through both paths (CP5 test) |
| Two ingests racing on one feedback file | the guards, the file write and the state publication are one `state_lock` critical section; the loser refuses before writing (CP5 test, MPR-R7-002) |
| A Controller-driven repository updates to 2.7.0 before C9 | section 7, item 4; the 2.6.0 queries are kept byte-compatible |
| The new suite does not run in CI, or the Manager's `CI_SUITES` check fails at pinning | the suite is added to both the template and `workflow-ci.yml` in CP7; the pin pull request carries the exact counts |
| The `WORKFLOW_RELEASE` constant goes stale in a later release | the CP7 build guard refuses a mismatch |
| The release-source freeze while 2.7.0 is pending | publish promptly after merging; tooling fixes are `ci:` (W0) |

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/orchestration-protocol-v1-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | A versioned public contract: one CLI, one envelope, unknown major fails closed, stable error codes beside native diagnostics, `describe` | CP3, CP6 |
| REQ-2 | `verify`: health of state, config, registry mirror, checkpoint proofs and installed release, read-only | CP3 |
| REQ-3 | `next-action`: total over phases × governing versions; semantic action, invocation, disposition, worker requirements, allowed results, decision basis; stale decisions refused | CP4 |
| REQ-4 | `reconcile`: progress / no_progress / gate_reached / invalid for an automatic action, including same-phase checkpoint progress; new basis; completion is `next-action`'s `complete` disposition | CP4 |
| REQ-5 | `record-external-result`: Workflow-owned parsing, binding checks, storage and recording of manual verdicts through the commands' own ingest; reserved kinds refused | CP5 |
| REQ-6 | `resolve-artifact`: semantic artifact kinds resolved by the Workflow's own helpers | CP3 |
| REQ-7 | `v2.6.0-002`: one pinned label, legacy alias, distinct values refused | CP1, CP5 |
| REQ-8 | `v2.6.0-001`: durable consumed history; withdrawn, revised or amended content never re-binds; 2.6.0 records migrate | CP2 |
| REQ-9 | 2.7.0 releasable: manifest, conformance CI and template run the new suite, release-constant guard | CP7 |
| REQ-10 | Shipped normative spec and schema; command and operator documents agree; protocol-only lifecycle E2E | CP6 |
| REQ-11 | A two-stage `REVISE` is applied by content: both apply commands accept one that states the reviewed `review_content_id` whatever its advisory bundle fields say, refuse one that states other content even when its bundle fields name the current bundle, and check the on-disk bundle against its manifest, including that the manifest names this work item and stage, which takes the place of a `Work item:` the verdict may omit (a manifest that names no work item keeps the bundle binding); no catalogue remedy rewrites a reviewer's binding fields (D-Apply-Binding) | CP4 |

## 10. Artifact classification

`docs/ai-workflow/registry/orchestration-protocol-v1-artifacts.json` comes
from the `process` template and is fitted to this plan's footprint.

**Plan stage.**

- The template as generated, plus these exclusions: `manifest.json`,
  `docs/RELEASING.md`, `payload/`, `fixtures/`, `templates/` and `tools/`.
  This is the same set that W0's amendment 0 added.
- Planning writes only this plan, the registry and the mapping (protected),
  plus the declaration file, the state file and `docs/ACTIVE_MILESTONE.md`
  (excluded).

**Implementation stage.** These are added to the protected set:

- the release source: `manifest.json`, and the prefixes `payload/`,
  `fixtures/` and `templates/`;
- `tools/` (CP7's guard);
- `docs/RELEASING.md`;
- the exact path `.github/workflows/workflow-ci.yml`, carved out of the
  template's shared `.github/` exclusion. That exclusion still covers the
  managed `workflow-conformance.yml`, which W1 does not touch.

The template's protected `scripts/` and `.claude/commands/` prefixes (the
installation) stay protected. W1 must not change them, and any accidental
change would be reviewed. `docs/ROADMAP.md` stays excluded as bookkeeping,
as it was in W0.

Every path the checkpoints write is classified at both stages.

## 11. Review rounds and decisions

### Round 1 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 1 → 2)

Reviewed `review_content_id`
`443d5fa6bc77b11e95c189d483f53016c40bef7ce98219cf033c5933f3e3d884`, bundle
`1db73e9d…`. No blocking findings. Each finding was checked against the
repository before it was applied.

| finding | disposition | where |
| --- | --- | --- |
| LPR-R1-001 (Important): three incompatible statements of the catalogue's evaluation order | **Accepted.** Verified against the plan text: row 10 claimed precedence over rows 6, 8 and 9, which were printed above it. The catalogue is reordered so that the printed order is the evaluation order, and the competing sentences are deleted. `BLOCK` rows (11, 17, 25, 31) and unreachable-gate rows (16, 30, 34) now sit above the rows they pre-empt | D-OP-Next; CP4 row-order test |
| LPR-R1-002 (Important): no "gate unreachable" row for `AWAITING_PLAN_APPROVAL` or the `2.2` `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` | **Accepted.** Verified: `plan_approval_gate_reachable` (`workflow_state.py:12907`) is false for a ledger keyed to other content, and `technical_approval_gate_reachable` (`:12832`) is false for a pin, a dirty protected path or a HEAD mismatch. Rows 16, 30 and 34 are explicit `blocked` rows, one reason code per cause | D-OP-Next; CP4 tests |
| LPR-R1-003 (Important): the gate predicates are pure and their inputs are command prose | **Accepted.** Verified: both predicates take every input as an argument, and `/approve-review` computes them in its steps. CP4 adds `plan_approval_gate_status` and `technical_approval_gate_status`, and `/approve-review` is rewritten to call them | D-OP-Next; CP4 files and tests; section 2 |
| LPR-R1-004 (Important): the `"1"` plan rows cannot tell an applied `REVISE` from an unapplied one | **Accepted.** Verified: `EXPECTED_WRITERS` lists only two-stage writers for `REVISING_PLAN` and `AWAITING_PLAN_APPROVAL`, and `publish_plan_revision` writes `AWAITING_EXTERNAL_PLAN_REVIEW` for `"1"`. Currentness for `"1"` is `assert_feedback_matches_bundle` against the recomputed bundle; an applied `REVISE` is a non-current `REVISE` (row 20, `plan.approve` with another round as the alternative). `REVISING_PLAN` at `"1"` moves to row 4. The `"1"` E2E's reconcile classes are listed | D-OP-Next rows 4, 17-21; CP4; CP6 |
| LPR-R1-005 (Important): "current" was `current_bundle_id`, but the plan stage binds by `review_content_id` | **Accepted.** Verified: `validate_manual_plan_review_preconditions` hard-checks `review_content_id` and `check_manual_stage_bundle_id_advisory` treats `bundle_id` as advisory. "fb is current" is now defined per stage and version. The legacy-marker case is covered because row 8 calls `assert_apply_plan_review_feedback` itself | D-OP-Next terms, row 8; CP4 tests |
| LPR-R1-006 (Important): the ingest's guards are two-stage-only but offered for `"1"`/`"2.1"` | **Accepted.** Verified: `validate_manual_*_review_preconditions` start with the two-stage version checks (`_require_v2_1_plan_review`, `_require_implementation_review_stage_version`) and a phase check. The ingest now selects a row of a per-(stage, version) table with its own required fields and guards; the two feedback-only rows are stated to have no 2.6.0 command | D-OP-External; CP5 tests |
| LPR-R1-007 (Important): `no_progress` contradicted `allowed_results` | **Accepted.** `allowed_results` is now a column of the legal-edge table, which `next-action` copies. `implementation.checkpoint` allows `progress` and `no_progress`. An unchanged state, and a checkpoint moved to `IN_PROGRESS` with none completed, are both `no_progress`. A class outside the list is `invalid` (`result_not_allowed`). A `BLOCK` is `gate_reached`, because the new decision is a gate | D-OP-Reconcile; CP4 tests |
| LPR-R1-008 (Optional): the decision basis excludes non-state inputs | **Accepted as a narrowing.** D-OP-Identity's claim is scoped to the state, and the inputs outside it are named. No `inputs_digest` is added: every command re-checks those inputs when it runs, and `reconcile` re-decides from them, so the digest would add a second staleness rule without making any action safer | D-OP-Identity |
| LPR-R1-009 (Optional): the header-only change was wider than its note | **Accepted, by keeping the binding parser's scope.** Verified: `parse_review_feedback_binding_fields` (`workflow_fingerprint.py:3346`) searches the whole file. It keeps that scan and no longer delegates to the new header parser. The header-only rule covers `review_content_id` and the new parser only | D-Feedback-Label; `OD-W1-9`; CP1 |
| LPR-R1-010 (Optional): publication-status row 10 cannot read an id-only list | **Accepted.** Verified: row 10 compares `mirror == registry == consumed.plan_revision`. For a list hit the predicate is id-only, like `_assert_not_consumed` | D-Consumed-History; CP2 test |
| LPR-R1-011 (Optional): row 2 called `plan_review_publication_status` for `"1"` | **Accepted.** Verified: the function starts with `_require_v2_1_plan_review`. The publication-status row (now 5) is `2.1`/`2.2` only, and the `plan.author` row (now 7) has no publication-status condition | D-OP-Next rows 5, 7 |
| Migration concern: name the downgrade check's command | **Accepted.** CP2 gives the exact command, its expected output and the evidence to record | CP2 |

**Self-found correction.** The round-1 plan marked
`implementation.recover_provenance` `user_only`. `/recover-implementation-provenance`
has no `disable-model-invocation` flag, so CP4's command-agreement test
would have failed. It is now not user-only and is offered only as an
alternative, and that test also checks the converse direction.

### Round 2 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 2 → 3)

Reviewed `review_content_id`
`da970210a812d47ddbc18109cf1163de1d06d397d34d10f1982ba0552fd7caab`, bundle
`768d8608…`. No blocking findings. Each finding was checked against the
release source (`payload/`) before it was applied. New rows take letter
suffixes (`11a`, `20a`, `25a`), so round-1 row references stay valid.

| finding | disposition | where |
| --- | --- | --- |
| LPR-R2-001 (Important): row 31 made a `"1"`/`"2.1"` implementation `BLOCK` a gate with no action | **Accepted.** Verified: `WORKFLOW_V2_1_OPERATOR_REFERENCE.md:174` routes `REVISE`/`BLOCK` to `/apply-implementation-review`, whose step 1 pins a `BLOCK` and "never blocks the remediation steps below"; the "explicit user resolution" rows in `MILESTONE_WORKFLOW.md` are the two-stage ones only. Row 31 is now `automatic` / `implementation.apply_review` and uses `is_technical_review_block_pinned` directly. Row 30 gives `review_blocked` and `review_block_pinned` the `implementation.apply_review` alternative. **Self-found, same defect:** row 17 (`"1"` plan `BLOCK`) was a gate too, but `/apply-plan-review`'s `"1"` path applies a `BLOCK` and stays for another round (its step 6); row 17 is now `automatic` / `plan.apply_review`. CP6's "adds none" sentence is now true as written | D-OP-Next rows 17, 30, 31 and the `BLOCK` note; CP4 tests |
| LPR-R2-002 (Important): the review and record rows ignored the worktree/HEAD generation check | **Accepted.** Verified: `/review-plan` (step 5), `/review-implementation` (`review-implementation.md:198`) and `/approve-review` (step 2, both stages) call `assert_local_generation_matches`; the record-manual commands' step 5 adopts `/review-plan`'s mechanism "staleness/wrong-worktree handling included", and re-run `assert_bundle_not_rejected` under step 7's mutation guard. `verify_plan_review_bundle` (`workflow_state.py:15491`) checks neither HEAD nor worktree. Added rows 11a and 25a (`bundle_generation_mismatch`), a first cause in both gate wrappers (so rows 16, 30, 34 and the new `"1"` row 20a cover the gates), both checks in the two-stage ingest rows and its step list, and a command-agreement test over each automatic row's full pre-write guard sequence. The docstrings that list the function's callers gain the record-manual commands; `WFR-17` excludes only external archive readers | D-OP-Next terms, rows 11a, 19, 20, 20a, 25a, wrapper cause table; D-OP-External; CP4; CP5 |
| LPR-R2-003 (Important): the shared ingest was stricter than 2.6.0, unstated | **Accepted, by keeping 2.6.0's requirements.** Verified: `record-manual-plan-review.md` step 4 tolerates a missing `Work item:`, and `parse_review_feedback_binding_fields` (`workflow_fingerprint.py:3346`) scans the whole file. The two-stage rows now require only `Status:`, `Reviewer role:` and a `review_content_id` label, the values 2.6.0's step 6 hard-checks. `parse_review_feedback_header` composes the existing whole-file readers, so only `review_content_id` is header-only, and the header block is redefined so that a leading `## Review Decision` heading does not end it. That one tightening is the compatibility note `OD-W1-9` already records. The reviewer template states the header rule | D-Feedback-Label; D-OP-External; `OD-W1-9`; CP1; CP5 tests |
| LPR-R2-004 (Optional): `reconcile` rule 1 called the publication status for `"1"` | **Accepted.** Verified: `plan_review_publication_status` (`workflow_state.py:15582`) starts with `_require_v2_1_plan_review`. The check is now `2.1`/`2.2` only and limited to the three ready plan phases; `REVISING_PLAN`, `PLANNING` and `AMENDING_PLAN` are exempt by name. The rejected-bundle check covers row 6's review phases | D-OP-Reconcile; CP4 test |
| LPR-R2-005 (Optional): `reconcile` after `plan.start` had no item | **Accepted.** The `plan.start` decision's `snapshot` lists the existing ids; `reconcile` takes the new `active_work_item_id`, requires it to be the only new id (`plan_start_item_ambiguous` otherwise), and reports `from: null`. CP6's `"1"` run sets the config's `default_workflow_version: "1"` before `plan.start` | D-OP-Next; D-OP-Reconcile; CP4; CP6 |
| LPR-R2-006 (Optional): row 35 hid the `USER_OVERRIDE` approval after an applied `REVISE` | **Accepted.** Verified: `resolve_approval_basis` (`workflow_state.py:12968`) returns `USER_OVERRIDE` for a non-matching `REVISE`. Row 35 lists `implementation.approve` as an alternative when fb is an applied `REVISE` and the technical gate is reachable; the primary action stays the external round, as the operator reference's "Post-fix bundle published" row says | D-OP-Next row 35; CP4 test |
| LPR-R2-007 (Optional): row 38's condition named no function | **Accepted.** Row 38 now calls `resolve_feedback_dir` and `assert_functional_review_not_already_consumed` (`workflow_fingerprint.py:2240`), the entry check of `/apply-functional-review`. "With findings" is dropped rather than given a new predicate: the command checks nothing more about the file before it starts (its findings are classified by the model in step 2), so a predicate would be a rule no command enforces | D-OP-Next row 38 and the function list; CP4 test |
| LPR-R2-008 (Optional): the `/approve-review` rewrite must keep the pin write | **Accepted.** Verified: `approve-review.md` step 1 writes `record_technical_review_block_pin` before `pinned_block` is computed. The write stays in the command, ahead of the wrapper call, and the wrapper reads the re-read state; a text test and a behaviour test pin it | D-OP-Next wrappers; CP4 files and tests |
| LPR-R2-009 (Optional): section 7 item 4 understated an interim Controller's needs | **Accepted.** The sentence now says an interim Controller must also accept the pinned `Reviewed review_content_id:` label | Section 7 |
| Missing tests (four) | **Accepted**, each added where its finding is applied | CP4; CP5 |

### Round 3 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 3 → 4)

Reviewed `review_content_id`
`50e13b8abd90bbb2d01a5931e08134d88e4837f98b08fb0dffa704a121d99e59`, bundle
`78da3f69…`. No blocking findings. Each finding was checked against the
release source (`payload/`) before it was applied. New rows take letter
suffixes (`1a`, `6a`, `31a`).

| finding | disposition | where |
| --- | --- | --- |
| LPR-R3-001 (Important): the catalogue's `"1"` lifecycle does not match the `"1"` commands | **Accepted, with one premise corrected.** Verified: `milestone-plan.md` step 0 makes the `"1"` branch v1-inert, and `route_work_item` is a `[2.1]` sub-step, so `plan.start` creates no `"1"` item. Verified: `milestone-implement.md`'s `"1"` step 1 loops over every checkpoint with no state write. **Correction:** the `"1"` step 4 does not move `IMPLEMENTING` → `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`. `record_bundle_generation(stage="implementation")` is legal only from `SELF_REVIEWING_IMPLEMENTATION` (`BUNDLE_GENERATION_LEGAL_SOURCE_PHASES_BY_STAGE`, `workflow_state.py:1262`), and a reproduction from `IMPLEMENTING` at `"1"` raises `IllegalBundleGenerationSourcePhaseError`. No 2.6.0 command advances a `"1"` item at `PLANNING`, `AMENDING_PLAN` or `IMPLEMENTING`. So no `"1"` implementation action with an `IMPLEMENTING` → `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` edge is added, because no command would produce that edge. Instead: row 1a (`plan.start` blocked under a `"1"` default); row 6a (`blocked`, `v1_state_not_advanced`); rows 7, 23 and 24 limited to `2.1`/`2.2`; `SELF_REVIEWING_IMPLEMENTATION` at `"1"` added to row 4; row 39's acceptance alternative keyed to `resolve_own_registry_completion_status`; `"1"` items driven only once they exist; the gap recorded as `v2.6.0-003` (`OD-W1-10`; CP7's roadmap row, section 7's write-up); CP6's `"1"` runs rebuilt from pre-constructed entries | D-OP-Next (`"1"` items, rows 1, 1a, 4, 6a, 7, 23, 24, 39, row-4 note); edge table; `OD-W1-10`; CP4; CP6; CP7; section 7 |
| LPR-R3-002 (Important): row 22 tested only the stored `plan_approval.status` | **Accepted.** Verified: `implementing_entry_reachable` (`workflow_state.py:2233`) also requires the approval commit to be an ancestor of HEAD and `approval_is_current`, and `/milestone-implement`'s 1a runs it on every invocation, at `SELF_REVIEWING_IMPLEMENTATION` too. CP4 adds `implementing_entry_status`, which returns the cause, and the old function becomes its `reachable` field, so row 22 and 1a call the same function. Row 22 covers both phases, with three causes and three remedies | D-OP-Next terms, row 22, function list; CP4 files and tests |
| LPR-R3-003 (Important): row 31's "or pinned" emitted an apply with no current fb | **Accepted.** Verified: `apply-implementation-review.md` step 1 stops on a missing file or a failed `assert_feedback_matches_bundle`. Row 31 is now "fb is current, and (`BLOCK` or pinned)". New row 31a: a pinned item with no current fb is an `external_gate` (`review_block_pinned`, `satisfied_by: implementation_review_verdict`), because placing the `BLOCK` back or a new verdict for the bundle makes fb current and leads to row 31 | D-OP-Next rows 31, 31a; CP4 tests |
| LPR-R3-004 (Optional): the wrapper's cause order cited `/approve-review` wrongly | **Accepted.** Verified: `approve-review.md` step 1 calls the predicate, and step 2 calls `assert_local_generation_matches` (`:248`) and `assert_plan_review_bundle_bound` (`:261`). The sentence is corrected, and the order is stated as a deliberate change of the rewritten command, with the pinned-`BLOCK` example. The plan wrapper adds `plan_review_bundle_unbound` as its second cause, reachable from row 16 only by a race, because rows 5 and 10 pre-empt every non-`BOUND` status at `AWAITING_PLAN_APPROVAL` | D-OP-Next wrappers and cause table, row 16; CP4 test |
| LPR-R3-005 (Optional): the ingest left `round` and an absent `bundle_id` unspecified | **Accepted.** Verified: `record_manual_plan_review` (`:14969`) and `record_manual_implementation_review` (`:15986`) take both, the `APPROVE` ledger stores both, and neither `_validate_plan_review_stages` nor `_validate_implementation_review_stages` checks the field's shape. `round` is the verdict's `Round:`, else the local `APPROVE`'s round for the same content; an absent bundle id records `null` with the advisory "absent" | D-OP-External; CP5 tests |
| LPR-R3-006 (Optional): `plan.start`'s `no_progress` was unreachable | **Accepted.** No new item with no active item is `no_progress` (`from` and `to` `null`); `invalid` stays for two new items, a new item that is not active, or no new item with a set pointer. The edge table lists the none → none edge | D-OP-Reconcile; edge table; CP4 test |
| Missing tests (five) | **Accepted.** Each is added where its finding is applied. The `"1"` `IMPLEMENTING` test expects row 6a (`blocked`), the decided class, rather than a reconcile class, since no action is emitted there | CP4; CP5; CP6 |
| Architecture concern: enumerate the entry check and the per-version writer sequence per automatic row | **Accepted.** CP4's command-agreement test now lists both for every automatic row and `gv`, and checks that the writer sequence ends on a legal edge | CP4 |

### Round 4 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 4 → 5)

Reviewed `review_content_id`
`ed3fcfc6a90b26acd57200a15295c461f5ab49604665f1cb23a9658456bb47e4`, bundle
`61fda819…`. No blocking findings. Each finding was checked against the
release source (`payload/`) before it was applied. New rows take letter
suffixes (`38a`, `38b`). The checkpoint set is unchanged.

| finding | disposition | where |
| --- | --- | --- |
| LPR-R4-001 (Important): `WorkflowStateError` does not exist | **Accepted.** Verified: `grep -rn WorkflowStateError payload/scripts/` finds nothing. Counted with `inspect` over the modules, `workflow_state` defines 168 exception classes and `workflow_fingerprint` 48 (the finding's 155 omits subclasses of the two module-local intermediates `LifecycleRefusalError` and `PlanApprovalTakeoverRefusedError`); none subclasses a built-in other than `Exception`. The domain is defined by origin (`issubclass(C, Exception)` and `C.__module__` in the two modules, `is_workflow_exception`), not by a new base class, which would re-base 216 classes and change the MRO existing handlers rely on. Built-ins from Workflow code are `internal_error`; `OSError` is `state_unreadable` only from the protocol's own state/config/lock-file read. **Self-found correction:** `state_unreadable` was "retryable for a lock timeout", but `state_lock` blocks in `fcntl.flock(fd, LOCK_EX)` with no timeout, so the case does not exist and the code is not retryable | D-OP-Errors (code table, domain); CP3 tests |
| LPR-R4-002 (Important): no rule for a condition function that raises; row 39's call raises in ordinary states | **Accepted.** Verified: `resolve_own_registry_completion_status` (`workflow_state.py:10263`) raises `RegistryCoverageError` for an unresolvable, unreadable, unparsable or foreign registry, and `StalePlanApprovalRegistryReadError` from `_assert_registry_covered_by_current_plan_approval` (`:10416`) when `plan_approval` is not `CURRENT` or the plan-stage bytes drifted. General rule: a Workflow exception from a value-returning condition ends the evaluation at that row as `blocked`, reason the row's named reason or `condition_refused`, native class and message in `reason`, `ok: true`; a non-Workflow exception is `internal_error`. New row 38a: `plan_content_drifted` (remedy: restore, or `/request-plan-amendment <id>`, which applies at every `gv` per `request-plan-amendment.md` step 0; **corrected in round 6, LPR-R6-001:** step 0 is the version guard only, and step 1's phase gate, `_AMENDMENT_REQUEST_ALLOWED_PHASES` (`workflow_state.py:13378`), refuses at `AWAITING_FUNCTIONAL_REVIEW`, so the amendment was removed from row 38a's remedy) and `registry_unreadable`. CP4's `"1"` test now constructs a covering `CURRENT` `plan_approval`, so the non-raising branch is actually exercised | D-OP-Next (raising-condition rule, rows 38a, 39, function list, table notes); CP4 tests |
| LPR-R4-003 (Optional): the totality enumeration was keyed to the config | **Accepted.** Verified: `default_config()` lists `["1","2.1"]` (`workflow_state.py:9282`). `SUPPORTED_GOVERNING_VERSIONS` is now the one module constant behind `describe` and the totality test, pinned to `sorted({"1"} \| TWO_STAGE_PLAN_REVIEW_VERSIONS)`, and the test also runs under `default_config()` | D-OP-Describe; D-OP-Next totality sentence; CP4 tests; section 8 |
| LPR-R4-004 (Optional): row 39 at `"1"` with a non-terminal registry was a gate no command completes | **Accepted.** `/accept-milestone` step 2a refuses such an item, and no `"1"` command writes checkpoint statuses, so nothing at the gate can complete it. New row 38b: `blocked`, `v1_state_not_advanced`, alternatives `functional.apply_findings` and `functional.review.advisory`; the case joins `v2.6.0-003` | D-OP-Next (rows 38b, 39, `"1"` items paragraph); CP4 tests; CP7 roadmap row |
| Missing tests (three) | **Accepted.** The error-mapping tests are in CP3, the two raising cases of row 38a and the `condition_refused` rule in CP4, and the `2.2`-removal test is CP4's companion totality test | CP3; CP4 |

### Round 5 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 5 → 6)

Reviewed `review_content_id`
`bb169d4bafc6ff4c8805fb718b8afd1ee30103b554fcaae7bbfa203aa5c97275`, bundle
`a0e2c356…`. No blocking findings. Each finding was checked against the
release source (`payload/`) before it was applied. New rows take letter
suffixes (`16a`, `25b`, `30a`, `38c`). The checkpoint set is unchanged; CP5
now also depends on CP4.

| finding | disposition | where |
| --- | --- | --- |
| LPR-R5-001 (Important): the raising-condition rule turned every acceptance-test condition into a block | **Accepted.** Verified: `assert_apply_plan_review_feedback` raises `FeedbackStatusNotApplicableError` for a status other than `REVISE` and `FeedbackNotForConsumedContentError` for another round's feedback; `assert_feedback_matches_bundle` (`workflow_fingerprint.py:3397`) raises `MissingFeedbackBindingFieldError` and `FeedbackBundleMismatchError`; `assert_functional_review_not_already_consumed` (`:2240`) raises `FunctionalReviewAlreadyAppliedError`. All are in the D-OP-Errors domain, so revision 5's rule made rows 8, 17-21, 31-35 and 38 block where rows 9, 20, 21, 35 and 39 and their own CP4 tests expected a fall-through. The rule now attaches a kind to each **call** (guard, acceptance, value), and an acceptance call's listed classes mean "false". The kinds and classes are one table, `CONDITION_CALLS`, keyed by row id, which the predicates evaluate through and which a test checks against the catalogue, the D-OP-Errors enumeration and the calls actually made. Any unlisted Workflow exception still gives `condition_refused` | D-OP-Next (raising-condition rule, `CONDITION_CALLS`); CP4 files and tests; CP6 specification tables; section 8 |
| LPR-R5-002 (Important): no implementation-stage bundle-integrity check at `2.2`; row 26 emitted an action `/review-implementation` refuses, and the ingest dropped a 2.6.0 refusal | **Accepted.** Verified: `review-implementation.md` step 4 refuses an absent or mismatched bundle in prose only, and states that `assert_local_generation_matches` performs no comparison for an absent `MANIFEST.md` (`read_manifest_generation_metadata` returns `{}`, `workflow_fingerprint.py:3119`); `record-manual-implementation-review.md` step 5 adopts that mechanism; `.ai-review/` is gitignored. CP4 adds `verify_implementation_review_bundle` (manifest present, `compute_bundle_id` against `read_manifest_identifiers`' `bundle_id`, the manifest's `review_content_id` against **I** computed commit-source), called by `/review-implementation` step 4, `/record-manual-implementation-review` and the `2.2` ingest row in step 5's position, before the generation check. New row 25b (`blocked`, `bundle_unverified`, remedy: regenerate) ahead of rows 26 and 27. **Rows 29 and 30:** no separate row; the technical gate wrapper reports `bundle_unverified` only when computing **B** raises `MissingRequiredBundleFileError`, which 2.6.0's `/approve-review` already refuses on; a manifest comparison at the gate would tighten `/approve-review`, and the `2.2` approval is bound to **I** by a ledger whose two stages each ran the verifier. **`"1"`/`"2.1"`:** the same narrow check gives named rows 16a (plan, `"1"`) and 30a (implementation), so a missing bundle is `bundle_unverified` with a remedy rather than `condition_refused` | D-OP-Next (terms, rows 16a, 25b, 30, 30a, bundle-integrity note, function list, wrapper causes); D-OP-External (`2.2` implementation row, guard paragraph); CP4; CP5 (depends on CP4); section 8 |
| LPR-R5-003 (Optional): row 39's `implementation.checkpoint` alternative names a command that refuses | **Accepted.** Verified: `CHECKPOINT_START_LEGAL_PHASES` is `frozenset({"IMPLEMENTING"})` (`workflow_state.py:4550`), and `transition_checkpoint_in_progress` raises `IllegalCheckpointStartPhaseError` elsewhere. New row 38c (`2.1`/`2.2`, `blocked`, `registry_incomplete`), with 38b's treatment: remedy `/request-plan-amendment <id>` or `/apply-functional-review`'s bounded or broad branch, alternatives `functional.apply_findings` and `functional.review.advisory`. Row 39 now always lists `milestone.accept`, since rows 38a-38c pre-empt every non-terminal outcome. CP6 corrects `accept-milestone.md` step 2a's `/milestone-implement` sentence, and the inaccuracy is recorded beside `v2.6.0-003` | D-OP-Next (rows 38c, 39, table note); CP4 test; CP6; CP7 roadmap row; section 7 |
| Missing tests (two groups) | **Accepted.** The acceptance fall-through cases and the unlisted-exception case are CP4 tests, through real states and through patched calls; the missing and mismatched `2.2` bundle cases are CP4 row tests and a CP5 ingest refusal with nothing written | CP4; CP5 |
| Architecture concern: the condition kind belongs in data | **Accepted.** That is `CONDITION_CALLS`; the totality and row-order tests are joined by a test that every row has a declared entry | D-OP-Next; CP4 |
| Architecture concern: compare `__module__` against the imported modules' `__name__` | **Accepted.** `is_workflow_exception` compares against `{workflow_state.__name__, workflow_fingerprint.__name__}`; CP3 tests a module loaded under another name | D-OP-Errors; CP3 |

### Round 6 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 6 → 7)

Reviewed `review_content_id`
`81eb535aed59bcb94a30d974d389d15a584d4567edb6298c6041b07a7d5a5a1c`, bundle
`b67d1a9c…`. No blocking findings. Each finding was checked against the
release source (`payload/`) before it was applied. No row is added; rows
8 (call table), 25b, 30, 30a, 38a and 38c change, and the catalogue gains
the `remedy_commands`/`refusing_commands` data. The checkpoint set is
unchanged.

| finding | disposition | where |
| --- | --- | --- |
| LPR-R6-001 (Important): rows 38a and 38c, and CP6's `accept-milestone.md` correction, name `/request-plan-amendment`, which refuses at `AWAITING_FUNCTIONAL_REVIEW`; neither `/apply-functional-review` branch makes the registry terminal | **Accepted.** Verified: `_AMENDMENT_REQUEST_ALLOWED_PHASES = frozenset({"IMPLEMENTING", "SELF_REVIEWING_IMPLEMENTATION"})` (`workflow_state.py:13378`), raised on at `:13469`; `bundle_generation_target_phase` returns only `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` or `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (`:13647-13649`); `apply-functional-review.md:225` leaves the parent's registry untouched; `promote_legacy_work_item` writes `AWAITING_FUNCTIONAL_REVIEW` at `"2.1"`. Row 38c: `blocked`, remedy "none exists in 2.6.0", reason code kept as `registry_incomplete` (not `v1_state_not_advanced`: the item is not a `"1"` item), the origins named, and the case recorded beside `v2.6.0-003`; the alternatives stay, for findings only. Row 38a's `plan_content_drifted` remedy is reduced to restoring the bytes, stating that 2.6.0 has no in-phase amendment route here (row 22 keeps the amendment, its phases being the amendment's own). CP6's step-2a correction names neither `/milestone-implement` nor `/request-plan-amendment` and keeps the bounded/broad routing of findings. The round-4 disposition note is corrected in place | D-OP-Next (`"1"` items paragraph, rows 38a, 38c, table notes); CP4 tests; CP6; CP7 roadmap row; section 7 item 5; section 11 round 4 |
| LPR-R6-002 (Optional): row 28 offers an external gate whose bundle may not exist | **Accepted.** Row 25b's condition no longer depends on fb at `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`, matching row 10 at the plan stage; row 25a keeps its fb restriction (`WFR-17`). Its `CONDITION_CALLS` entry is now the verifier alone | D-OP-Next (`CONDITION_CALLS` row 25b, row 25b, bundle-integrity note); CP4 test |
| LPR-R6-003 (Optional): `CONDITION_CALLS` row 8 omits its publication-status input | **Accepted**, both ways the reviewer offered: row 8 lists `plan_review_publication_status` (value), and the table states that a value reused from an earlier row's evaluation is still declared at every row that reads it, which the recorder test checks per row rather than per invocation | D-OP-Next (`CONDITION_CALLS`, reuse paragraph); CP4 test |
| LPR-R6-004 (Optional): the "regenerate" remedies name the `implementation` stage only | **Accepted, with one premise corrected.** The remedy names `post-fix` when `implementation_revision > 1` and `implementation` at `1` (`record_bundle_generation` advances the revision only on an `ordinary` outcome). **Correction:** the stage cannot be read from `MANIFEST.md`, because `render_manifest_md_implementation_stage` always writes `stage: implementation` (`workflow_fingerprint.py:4090`); the generator's own stage label is `CHANGED_FILES.txt`'s `stage:` line (`prepare-ai-review.sh:442`) | D-OP-Next (terms, rows 25b, 30, 30a); CP4 test |
| Missing tests (rows 38a/38c, LPR-R6-002) | **Accepted.** Row 38a's and 38c's remedies are tested not to name `/request-plan-amendment`; a legacy-promoted `"2.1"` item gives row 38c; a missing bundle with no fb at the manual-external implementation phase gives row 25b, not row 28; and the command-agreement tests now cover remedy commands | CP4 |
| Architecture concern: remedy commands are not checked against their row's phase | **Accepted.** Each non-automatic row carries `remedy_commands` (with an explicit `none_exists`) and `refusing_commands` as catalogue data; CP4 checks that the first accept the row's state, the second refuse it, and that every command the prose names is in one of them | D-OP-Next (table notes); CP4 command agreement |
| Architecture concern: the ingest and the catalogue order the generation check and the verifier differently | **Kept deliberately, now stated.** The catalogue tries row 25a first because `/recover-implementation-provenance` repairs an excluded-only commit without a new round, and a "regenerate" remedy reported first would bypass it; both rows block, so no automatic action differs | D-OP-Next (table notes) |

### Round 7 — `MANUAL_EXTERNAL_PLAN_REVIEW`, `REVISE` (plan revision 7 → 8)

Reviewed `review_content_id`
`1453c323d278ca1f5ff5706aea8beb82297d5ff51ba1d4cd83b6317a1bc3e298`, bundle
`9c524efa…`, after the local review's `APPROVE` of the same content. No
blocking findings. The findings are numbered `MPR-R7-001` to `-003` in the
order the feedback lists them. Each was checked against the release source
(`payload/`) before it was applied. Rows 7a and 35a are added; rows 6 and
36 change; the checkpoint set is unchanged. Requirement REQ-4's wording
changes, and the mapping is regenerated with it.

| finding | disposition | where |
| --- | --- | --- |
| MPR-R7-001 (Important): rows 8 and 36 can emit an automatic action that its command refuses (a `REJECTED` marker; a missing feedback file or bundle) | **Accepted, and widened to row 8's missing bundle.** Verified: `apply-plan-review.md:120` and `apply-implementation-review.md:101` call `assert_bundle_not_rejected` in step 1, and both commands stop on an absent feedback file and compute **B** for `assert_feedback_matches_bundle` there. Row 6 listed only the review phases, so neither apply phase was guarded, and row 36 had no condition. `.ai-review/` is untracked, so a fresh worktree has the state without the files. Row 6 now also lists `REVISING_PLAN` and `APPLYING_REVIEW_FEEDBACK`. New row 35a blocks at `APPLYING_REVIEW_FEEDBACK` when the command's step-1 acceptance fails, with three reasons (`review_feedback_missing`, `bundle_unverified`, `review_feedback_not_current`); row 36 now matches only a current fb. New row 7a blocks at `REVISING_PLAN` when, in `"bundle"` mode, **B** cannot be computed; before, row 8 ended there in `condition_refused` with no remedy. Neither row offers a regeneration: the feedback binds to the reviewed bundle, and a `post-fix` generation from `APPLYING_REVIEW_FEEDBACK` is the round's exit (`BUNDLE_GENERATION_LEGAL_SOURCE_PHASES_BY_STAGE`, `workflow_state.py:1262`). `reconcile`'s rejected-bundle rule keeps the seven review phases | D-OP-Next (rows 6, 7a, 35a, 36, `CONDITION_CALLS`, bundle-integrity note); D-OP-Reconcile rule 1; CP4 command-agreement tests |
| MPR-R7-002 (Important): two concurrent `record-external-result` calls can leave the feedback file disagreeing with the recorded verdict | **Accepted.** Verified: steps 3-5 ran the guards, then wrote the file, then opened a separate `state_transaction`, so two ingests could both pass the guards and the losing one's file stays beside the winner's ledger entry. `state_lock` refuses re-entry in a process (`StateLockReentrancyError`), so the fix cannot nest `state_transaction` in a held lock. The ingest now holds `state_lock` from row selection through publication. Row selection, guards and the pure `record_manual_*_review` call run on the state re-read under the lock; the file write runs in a new `before_publish` hook of `state_transaction`, before the state is published. The loser re-reads the winner's state and refuses before writing. A feedback-only row holds the lock directly and refuses a second, different current verdict with the new `ConflictingReviewFeedbackError`. No guard in either sequence takes another lock (checked: `verify_plan_review_bundle`, `assert_plan_review_bundle_bound`, both `validate_manual_*_review_preconditions`, `assert_local_generation_matches`, `check_manual_stage_bundle_id_advisory`, `assert_feedback_not_owned_by_other_work_item`) | D-OP-External (ingest steps, critical section, crash window); CP5 files and tests; section 8 |
| MPR-R7-003 (Important): `reconcile` accepts only automatic decisions, yet CP6 reconciled `milestone.accept` to `complete` | **Accepted, by keeping the automatic-only rule.** Verified: the only writer of `MILESTONE_COMPLETE` is `complete_work_item`, behind the `user_only` `/accept-milestone`, offered only at the `human_gate` row 39, and no edge-table row reaches `MILESTONE_COMPLETE`. `reconcile` loses its `complete` class, and an automatic action that leaves the item complete is `invalid`. Completion is `next-action`'s `complete` disposition (row 40). CP4's `complete` test is replaced. CP6's runs reconcile only automatic actions, call `next-action` after each gate's writer sequence, assert once that a gate decision is refused with `invalid_request`, and end on `next-action`'s `complete`. Accepting gate decisions in `reconcile` was rejected: it would need a way to name which alternative the user ran, and it would contradict "a gate is resolved outside the orchestrator's run" | D-OP-Reconcile; CP4 tests; CP6; section 9 REQ-4; requirements mapping |
| Optional: the metadata bullet said "Plan revision: 6" under a Revision 7 title | **Accepted.** Both now say 8 | Header |
| Missing tests (three) | **Accepted**, each added where its finding is applied: rows 6, 7a and 35a with a marker and with missing feedback or bundle (CP4); the two-process ingest race (CP5); terminal completion through `next-action` (CP4, CP6) | CP4; CP5; CP6 |

### Round 8 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 8 → 9)

Reviewed `review_content_id`
`eeab41ce4a7a4a7299ae95550ad68769bdac8591aaaada992b0e4b421dc4145f`, bundle
`82711d74…`. No blocking findings. The findings are numbered `MPR-R8-001`
to `-003` in the order the feedback lists them (the prefix kept from round
7, whose findings these continue). Each was checked against the release
source (`payload/`) before it was applied. Row 8a is added; rows 9 and 35a
change; the checkpoint set and the requirements are unchanged.

| finding | disposition | where |
| --- | --- | --- |
| MPR-R8-001 (Important): a recorded two-stage `REVISE` whose binding fields are absent or name another bundle reaches an automatic `plan.author` (plan stage), or a block with an unfollowable remedy (`2.2` implementation stage) | **Accepted, option (a).** Verified: `assert_apply_plan_review_feedback` returns `"bundle"` for any status outside `PLAN_REVIEW_DURABLE_FEEDBACK_CHECK_STATUSES` (so under `NEEDS_EDIT`), after which `/apply-plan-review` step 1 runs `assert_feedback_matches_bundle` (`workflow_fingerprint.py:3397`), which raises `MissingFeedbackBindingFieldError` or `FeedbackBundleMismatchError`; row 8 lists both as acceptance classes, so row 9 matched, and `milestone-plan.md:180` reads no feedback file. New row 8a, ahead of row 9, blocks with `review_feedback_unbound` when fb is a `REVISE` of the consumed `review_content_id` (legacy marker: by `Work item:`) and only the bundle binding refuses, naming the field and both values; its remedy (set the three fields to the printed values, or a new verdict for **B**) is followable, and `plan.withdraw` stays an alternative. **Superseded in round 9 (MPR-R9-001):** that remedy rewrote the reviewer's binding attestation; the apply commands now bind a two-stage `REVISE` by content (D-Apply-Binding), row 8a is narrowed to the fb the content binding cannot bind, and row 35a loses `review_feedback_unbound`. Row 35a gives the same reason when fb is a `REVISE` whose `review_content_id` equals **B**'s manifest's; the manifest's id, not **I**, because **I** moves once the applier commits a fix. Option (b), tightening the ingest, is rejected, and the reasons are stated in D-OP-External: it changes a 2.6.0 command for one status, contradicts the advisory bundle id that keeps a wrapper-only regeneration's verdict current (row 11a, `check_manual_stage_bundle_id_advisory`, `workflow_state.py:14950`), and leaves the file-edit and fresh-worktree routes uncovered | D-OP-Next (`CONDITION_CALLS` 8a and 35a, the reached-rows paragraph, rows 8a, 9, 35a, table notes); D-OP-External (required fields); CP4 tests; CP5 tests; section 8 |
| MPR-R8-002 (Optional): no fb at `REVISING_PLAN` gives row 9's automatic `plan.author`, with the residual undocumented | **Accepted.** Verified: `_write_consumed_plan_review_binding` (`workflow_state.py:15245`) writes the same `CONSUMED` record for a recorded `REVISE` and a withdrawal, and `withdraw_plan_review` (`:15399`) leaves `plan_review_stages` untouched, so the state cannot tell a lost fb from a withdrawal. Recorded as an accepted residual in the rows 8a/9 note and on row 9, with why `APPLYING_REVIEW_FEEDBACK` differs (no withdrawal shares that phase) and why no gate is bypassed | D-OP-Next (row 9, table notes); CP4 test |
| MPR-R8-003 (Optional): `before_publish`'s position relative to `state_transaction`'s other checks | **Accepted.** Verified: `state_transaction` runs `_assert_technical_review_block_pins_monotonic` between the mutator and `_publish_state_file`. The hook now runs after every check, immediately before `_publish_state_file`, and later checks go before it; a test shows a pin-assertion failure never calls the hook and leaves both files untouched | D-OP-External (critical section); CP5 test |
| Missing tests (two) | **Accepted**: the optional-field and pre-regeneration manual `REVISE` through `record-external-result` at both stages (CP5), with rows 8a/35a (CP4); `before_publish` ordering (CP5) | CP4; CP5 |
| Architecture concern: no test of the converse of command agreement | **Accepted.** CP4 adds the ingest-to-apply routing test: every verdict an ingest row accepts, and each local review's `REVISE`, is driven into its next decision, which must be the matching apply action, a gate, or a block with a followable remedy | CP4 |

### Round 9 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 9 → 10)

Reviewed `review_content_id`
`03c1b8f2535510e480d66fc1c62c2ea6bf16dabf6edda4bc9fc3cfeb08013563`, bundle
`9be0fed0…`. No blocking findings. The findings are numbered `MPR-R9-001`
to `-004` in the order the feedback lists them, the Important finding
first. Each was checked against the release source (`payload/`) before it
was applied. D-Apply-Binding, `OD-W1-11` and `REQ-11` are added; rows 7a,
8, 8a, 9, 35a and 36 change. CP4 gains the binding function, the two
apply-command edits and the `REVIEW_PROTOCOL.md` paragraph. The checkpoint
set is unchanged.

| finding | disposition | where |
| --- | --- | --- |
| MPR-R9-001 (Important): rows 8a's and 35a's `review_feedback_unbound` remedy tells the operator to rewrite the verdict's binding attestation | **Accepted, option (a).** Verified: `REVIEW_PROTOCOL.md:629` defines `Reviewed bundle ID:` as "the exact bundle_id this feedback reviewed", and `:650-657` rejects feedback whose values disagree, "never applied at face value" (`WFR-03`); D-OP-External records `null` rather than substitute the current id. The remedy is removed. New D-Apply-Binding: `assert_apply_review_feedback_binding`, called by `/apply-plan-review` (in `"bundle"` mode) and `/apply-implementation-review` step 1 in place of `assert_feedback_matches_bundle`, binds a two-stage `REVISE` that states a `review_content_id` by content: the consumed id at the plan stage, and **B**'s manifest id at both, with **B** checked against its manifest. The bundle fields become advisory there. Every `"1"`/`"2.1"` round, every legacy marker and every fb without a stated id keeps 2.6.0's bundle binding. A rewritten `Reviewed bundle ID:` over other content, which 2.6.0 accepted, is now refused. Row 8 now accepts a recorded `REVISE` with absent or stale bundle fields. Row 8a is narrowed to the fb the content binding cannot bind (legacy marker, or no stated id), with a remedy that asks for a new verdict and never edits one. Row 35a loses `review_feedback_unbound`. Option (b), keeping the block, is rejected in D-Apply-Binding: it would send every recorded `REVISE` that lacks the optional field back to its reviewer. The decision is surfaced as `OD-W1-11` | D-Apply-Binding; section 2; D-OP-Next (`CONDITION_CALLS` 7a, 8, 8a, 35a, the reached-rows paragraph, rows 7a, 8, 8a, 9, 35a, 36, table notes); D-OP-External (required fields); section 4; CP4 files and tests; CP5 test; sections 8 and 9 |
| MPR-R9-002 (Optional): "told apart from a withdrawal by that id" is not exact for an unrecorded `REVISE` of the withdrawn content | **Accepted.** Verified: `withdraw_plan_review` (`workflow_state.py:15399`) consumes `bound.review_content_id`, which is that `REVISE`'s id, and `_assert_not_consumed` keeps the on-disk bundle the withdrawn one. The note now describes the sequence: under D-Apply-Binding it gives row 8, which applies a genuine verdict for the withdrawn content, and 2.6.0 would also have accepted it when its bundle fields named **B**. A CP4 test pins the sequence for the manual paste and for a crashed `/review-plan` state write | D-OP-Next (table notes); CP4 test |
| MPR-R9-003 (Optional): row 8a's premise that **B** carries the consumed content is argued, not checked | **Accepted, as part of the binding.** The content binding checks **B** against its own `MANIFEST.md` and, at the plan stage, the manifest's `review_content_id` against the consumed one. A mismatch raises `ReviewBundleManifestMismatchError`, reported as row 7a's or 35a's `bundle_unverified` with the restore remedy | D-Apply-Binding; rows 7a, 35a; bundle-integrity note; CP4 test |
| MPR-R9-004 (Optional): row 8a's legacy-marker clause matches any `REVISE` naming the item | **Accepted, noted as inherited.** Verified: `assert_apply_plan_review_feedback` (`workflow_state.py:15757`) matches a legacy marker by `Work item:` only. Row 8a keeps the legacy case, because falling back to row 9 would re-author over a possibly recorded `REVISE`. The row blocks and offers no automatic action, and its remedy no longer rebinds anything, so the inherited weakness adds no hazard. The row says so | row 8a |
| Missing tests (three) | **Accepted**: the content binding at both stages with no bundle id and with a pre-regeneration bundle id, and refused for other content and for a forged bundle id; the unrecorded-`REVISE`-then-withdraw sequence; a bundle directory whose manifest names other content (CP4). CP5's ingest-to-apply test now expects the apply action | CP4; CP5 |
| Architecture concern: rows 8a and 35a encode a workaround in the catalogue | **Accepted.** The ingest, the apply commands and the catalogue now share one binding rule per stage, in the one function the commands and the catalogue call | D-Apply-Binding |
| Migration and data-integrity concern: the remedy made `Reviewed bundle ID:` unreliable as provenance | **Accepted.** No remedy edits a verdict. `REVIEW_PROTOCOL.md` states that no command or remedy rewrites a reviewer's binding fields, and CP4's text test asserts it of every catalogue remedy | D-Apply-Binding; CP4 |

### Round 10 — `LOCAL_MODEL_PLAN_REVIEW`, `REVISE` (plan revision 10 → 11)

Reviewed `review_content_id`
`6a563ca315f385e21c18988384bf03c5b018407cbfb7be5313c357eb08c8a03b`, bundle
`378515df…`. No blocking findings. The reviewer found round 9's four
findings resolved. The findings are numbered `MPR-R10-001` and `-002` in
the order the feedback lists them. Each was checked against the release
source (`payload/`) before it was applied. D-Apply-Binding's selection
rule and check 3 change, and so do rows 7a, 8a and 35a, the table notes,
`OD-W1-11`, CP4's tests, section 8 and `REQ-11`. The checkpoint set is
unchanged.

| finding | disposition | where |
| --- | --- | --- |
| MPR-R10-001 (Important): at the implementation stage, the content binding never checks that the bundle, or the verdict, belongs to this work item | **Accepted.** Verified: `assert_feedback_matches_bundle` (`workflow_fingerprint.py:3397`) requires `Work item:`, which the content binding dropped; `assert_manual_feedback_names_work_item` (`:3381`) accepts an absent field; `record_local_implementation_review` (`workflow_state.py:15870`) writes no ledger entry for a `REVISE`; and `resolve_bundle_dir` (`workflow_fingerprint.py:2041`) gives the shared flat `.ai-review/current` for a non-plan stage of an item with no scoped root. Check 3 now also requires the manifest's `work_item_id` to equal the item's id, its `base_commit` (when present) the item's, and its `stage` to be `plan` or `implementation` by stage, refusing with `ReviewBundleManifestMismatchError` (`bundle_unverified`). The reviewer's `implementation`/`post-fix` is narrowed to `implementation`, because the only implementation-stage renderer writes `stage: implementation` for both (`workflow_fingerprint.py:4141`). The `base_commit` comparison is added beyond the finding: the content binding also drops fb's `Reviewed base commit:`, and the manifest's line restores that check. For a manifest with no `work_item_id` (`render_manifest_md_implementation_stage`'s optional parameter, `:4098`), the reviewer's second option is taken: the bundle binding is selected, so fb's `Work item:` must name this item. That routes the case to rows that already exist (8a, 35a's `review_feedback_not_current`) rather than to a new content-binding refusal. One rule states both stages | D-Apply-Binding (selection, check 3, "Why check 3 names the owner"); rows 7a, 8a, 35a; table notes; `OD-W1-11`; CP4 files and tests; sections 8 and 9 |
| MPR-R10-002 (Optional): "What changes for an operator" should say what the reviewed content is bound to | **Accepted.** The loosened bullet now says the content is in a bundle whose manifest names this item and this stage, and that the manifest's `work_item_id` replaces fb's `Work item:`, which is what ties the verdict to the item at the implementation stage | D-Apply-Binding |
| Missing tests (three) | **Accepted.** CP4 adds the foreign-manifest case at both stages, the no-`work_item_id` manifest, and the stage and `base_commit` mismatches | CP4 tests |
| Required acceptance criteria | **Met** by MPR-R10-001's changes; `REQ-11` now covers the work-item check | section 9 |

### Round 11 — `MANUAL_EXTERNAL_PLAN_REVIEW`, `REVISE` (plan revision 11 → 12)

Reviewed `review_content_id`
`44b09d7082ec986dabb062d83971be1a85f8ac2eaf72b89ad22a39cd45399e28`, bundle
`e6d4608b…`, after the local review's `APPROVE` of the same content. No
blocking findings. The reviewer found round 7's three findings closed. The
finding is numbered `MPR-R11-001`. It was checked against the plan text
before it was applied. Only CP4's command-agreement test and D-OP-Next's
condition list change. The checkpoint set is unchanged.

| Finding | Disposition | Where |
| --- | --- | --- |
| MPR-R11-001 (Important): CP4's command-agreement test still runs `assert_feedback_matches_bundle` at both apply commands, which refuses the content-bound `REVISE` variants the apply-binding tests require to pass | **Accepted, and widened to D-OP-Next's condition list.** Verified: CP4's command-agreement bullet listed `assert_feedback_matches_bundle` as the last guard of `plan.apply_review` and `implementation.apply_review`, and the behaviour test invokes every listed guard on each automatic row's state. D-Apply-Binding ("What changes for an operator") and CP4's files (`apply-plan-review.md`, `apply-implementation-review.md`) replace that call with `assert_apply_review_feedback_binding`, and the apply-binding tests require a two-stage `REVISE` with absent or stale bundle fields to be accepted, which `assert_feedback_matches_bundle` refuses (`MissingFeedbackBindingFieldError`, `FeedbackBundleMismatchError`, `workflow_fingerprint.py:3397`). Both sequences now end in `assert_apply_review_feedback_binding` with the stage, and the behaviour test runs them on the two content-bound variants at rows 8 and 36, with the `"1"`/`"2.1"` implementation rows asserting the bundle binding. The text test also asserts that neither apply command still names the old call in step 1. The same stale call was in D-OP-Next's "Conditions call Workflow functions only" list for `/apply-plan-review`'s acceptance, and is replaced there too. Section 2's description of 2.6.0 and the `"1"`/`"2.1"` ingest rows' tests keep `assert_feedback_matches_bundle`, which is correct for them | D-OP-Next (conditions list); CP4 tests (command agreement) |
| Missing tests | **Accepted** by MPR-R11-001: the guard sequence exercises the binding function at both apply commands, including both content-bound variants | CP4 tests |
| Required acceptance criteria | **Met**: CP4's command-agreement test matches D-Apply-Binding, and still checks that every automatic apply action passes the command's actual pre-write guards | CP4 tests |
