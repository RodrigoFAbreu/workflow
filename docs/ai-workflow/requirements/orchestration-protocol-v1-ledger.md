# `orchestration-protocol-v1` Requirements Ledger

Mutable, human-readable execution record for the `orchestration-protocol-v1`
work item (W1). Physically separate from the immutable, machine-readable
`orchestration-protocol-v1-mapping.json` in this same directory: the mapping
is the approved requirement↔checkpoint binding and is plan-stage protected;
this ledger resolves under the excluded prefix `docs/ai-workflow/requirements/`,
so editing it never stales an approval.

Each checkpoint appends one section here as it completes. This is a log, not
a status source: `WORKFLOW_STATE.json`'s `checkpoints[id]` remains the sole
record of checkpoint status.

## `CP1` — Pinned `review_content_id` label (`v2.6.0-002`)

Requirements: REQ-7 (one pinned label, legacy alias, distinct values
refused; the ingest half is CP5's).

- **Implementation** (release source only):
  - `payload/scripts/workflow_fingerprint.py`:
    `_FEEDBACK_REVIEW_CONTENT_ID_RE` also accepts the legacy alias
    `Reviewed review content ID:`; the new `feedback_header_block` returns
    the lines before the first `## ` heading that follows a field line;
    `parse_feedback_review_content_id` reads that header block only; the new
    `parse_review_feedback_header` composes `parse_review_feedback_binding_fields`
    (unchanged, whole-file), a whole-file first-match `Reviewer role:` and the
    header-only `review_content_id`; `FEEDBACK_REVIEW_CONTENT_ID_LABEL` names
    the pinned label `Reviewed review_content_id:`.
  - `payload/docs/ai-workflow/REVIEW_PROTOCOL.md` "Required structure": the
    pinned line, when it is required (two-stage stage verdicts) or optional
    (`"1"`, advisory `/review-implementation`), the alias, the header-block
    rule and the compatibility note (an ID stated only after the first `## `
    parses as absent from 2.7.0 on).
  - `review-plan.md` step 7, `review-implementation.md` step 6 and A5: write
    exactly the pinned label, before the first `## ` section.
    `record-manual-plan-review.md` / `record-manual-implementation-review.md`
    step 4: the reviewer must state the pinned label, header before the first
    `## `.
  - `payload/scripts/workflow_fingerprint_test.py`:
    `TestPinnedReviewContentIdLabel`, 14 tests, every row CP1 names.
  - `payload/scripts/workflow_integration_test.py`: the golden hashes of the
    three roster command files that changed, with their reason.
- **Verification**: the seven release-source suites in a conformance fixture
  staged by `tools/release/release.py stage-conformance` from an
  unreferenced commit of the working tree whose `manifest.json` digests were
  refreshed in that commit only (the manifest itself is CP7's):
  `workflow_fingerprint_test.py` 256 OK, `workflow_state_test.py` 972 OK
  (1 skipped), `workflow_test_harness_test.py` 19 OK,
  `workflow_integration_test.py` 267 OK, `workflow_acceptance_matrix_test.py`
  291 OK (18 skipped), `workflow_state_completion_obligations_test.py` 106 OK,
  `workflow_fingerprint_generalization_test.py` 105 OK.
  `workflow-manager verify .`: installation matches workflow 2.6.0.

## `CP2` — Durable consumed history (`v2.6.0-001`)

Requirements: REQ-8 (durable consumed history; withdrawn, revised or amended
content never re-binds; 2.6.0 records migrate).

- **Implementation** (release source only):
  - `payload/scripts/workflow_state.py`: the work-item key
    `consumed_plan_review_content_ids` (`CONSUMED_PLAN_REVIEW_CONTENT_IDS_KEY`),
    outside `plan_review_binding`. `_write_consumed_plan_review_binding`, still
    the single `CONSUMED` writer, first adds the slot's old id and the new id
    to it (a legacy marker adds none; an empty history leaves the key
    absent). `_consumed_plan_review_content_ids(work_item)` reads the union of
    the list and the slot, migrating a 2.6.0 item at read time.
    `_assert_not_consumed` refuses any id in that union (the legacy-marker
    revision rule is unchanged). `plan_review_publication_status` row 10 keeps
    the slot's full predicate and adds an id-only hit on the stored list
    (`LPR-R1-010`); row 11 is reached only when neither matches.
    `_validate_consumed_plan_review_content_ids` (from `_validate_work_item`
    and every read) refuses a list that is not sorted, duplicate-free 64-hex,
    and accepts one without the slot's id. `default_work_item` is unchanged.
  - `payload/scripts/workflow_state_test.py`: `TestPlanApprovalPhaseGate`'s
    detour test now asserts the restore is refused at publish, and at bind
    given a forged `PUBLISHED` record. New `TestConsumedPlanReviewHistory`,
    8 tests: the defect's sequence through a `REVISE` and through a real
    `request_plan_amendment`; restore refused, then any edit publishes;
    2.6.0 migration (`[old, new]`, sorted); legacy marker adds nothing (and
    keeps an overwritten slot's id); row 10/11 cases including the slot's full
    predicate; validator cases; the downgrade unit test.
  - `payload/scripts/workflow_acceptance_matrix_test.py`: `cp4_make_legacy`
    also drops the 2.7.0 key (a 2.5.1 item never has it);
    `test_legacy_amending_plan_with_approved_id_uses_the_amendment_record` now
    expects row 10: the entry marker is a 2.7.0 `CONSUMED` write, so the
    unchanged amended-away content is a list hit.
  - `payload/scripts/workflow_integration_test.py`: golden hashes of
    `milestone-plan.md` and `review-plan.md`, with their reason;
    `consumed_plan_review_content_ids` allowlisted as a state field in the
    operator-reference symbol check.
  - Text made true, plus the history and edit-to-re-enter sentence:
    `MILESTONE_WORKFLOW.md`, `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
    `PLAN_REVIEW_WORKFLOW.md`, `milestone-plan.md`, `review-plan.md`,
    `request-plan-amendment.md`.
- **Downgrade check** (one-off, the plan's exact command): 2.6.0's
  `validate_state` printed `ACCEPTED ['consumed_plan_review_content_ids']`,
  exit 0. Command, output and 2.6.0 blob ids: `docs/ACTIVE_MILESTONE.md`,
  "CP2 evidence".
- **Verification**: the seven release-source suites in a conformance fixture
  staged by `tools/release/release.py stage-conformance` from an
  unreferenced commit of the working tree whose `manifest.json` digests and
  sizes were refreshed in that commit only (the manifest itself is CP7's):
  `workflow_fingerprint_test.py` 256 OK, `workflow_state_test.py` 980 OK
  (1 skipped), `workflow_test_harness_test.py` 19 OK,
  `workflow_integration_test.py` 267 OK, `workflow_acceptance_matrix_test.py`
  291 OK (18 skipped), `workflow_state_completion_obligations_test.py` 106 OK,
  `workflow_fingerprint_generalization_test.py` 105 OK.
  `workflow-manager verify .`: installation matches workflow 2.6.0.

## `CP3` — Protocol core

Requirements: REQ-1 (one CLI, one envelope, unknown major fails closed,
stable codes beside native diagnostics, `describe`; the specification half
is CP6's), REQ-2 (`verify`), REQ-6 (`resolve-artifact`).

- **Implementation** (release source only):
  - `payload/scripts/workflow_protocol.py` (new, `state_writer: false`):
    the CLI (`[--repo-root PATH] [--protocol-major N] <operation>`), argparse
    errors raised as `invalid_request` and no `--help` (stdout carries the
    envelope only); the envelope writer and exit codes 0/3/2/1;
    `WORKFLOW_RELEASE = "2.7.0"`, `PROTOCOL_VERSION = "1.0"`,
    `PROTOCOL_MAJOR = 1`; `ERROR_CODES` (the eleven v1 codes, only
    `stale_decision` retryable); `is_workflow_exception` (origin test against
    the imported modules' `__name__`) and `WORKFLOW_EXCEPTION_CODES`
    (`InvalidWorkItemIdError` → `invalid_request`,
    `FeedbackLayoutUndecidableError` → `state_unreadable`,
    `UnknownFeedbackLayoutError` → `state_invalid`; any other Workflow
    exception `refused`, anything else `internal_error`);
    `read_state_and_config`, the single read where an `OSError` or a corrupt
    file is `state_unreadable`, under a shared `flock` on an existing
    `WORKFLOW_STATE.lock` opened read-only (never created, never the write
    lock); `load_valid_state` (schema-only `validate_state`, refusal
    `state_invalid`); `state_identity` and `basis`; `describe` (lists from
    the module tables: `OPERATIONS`, `DISPOSITIONS`, `ACTION_IDS` (empty
    until CP4), `ARTIFACT_KINDS`, `EXTERNAL_RESULT_KINDS` (empty until CP5),
    `RESERVED_RESULT_KINDS`, `ERROR_CODES`; `SUPPORTED_GOVERNING_VERSIONS`);
    `verify`'s seven checks in order (a check fails on a Workflow refusal or
    a Git refusal, skips when the state is unreadable or, for check 6, when
    there is no installation record); `resolve-artifact` for the six kinds,
    each through the existing helper, `review_bundle` with `stage="plan"` at
    the plan-stage phases, plus the item's `basis`.
  - `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json` (new):
    the envelope, `error`, `native`, `basis`, and `$defs.results` for
    `describe`, `verify` and `resolve-artifact`; only `type`, `required`,
    `properties`, `additionalProperties`, `enum`, `items` and `$ref`.
  - `payload/scripts/workflow_protocol_test.py` (new), 58 tests: the minimal
    schema checker and its keyword-set test; every response validated;
    stdout is one envelope; `--protocol-major 2` refuses (exit 3) with no
    read and before `--repo-root` is checked; bad arguments are
    `invalid_request` (exit 2) envelopes; an injected exception is
    `internal_error` (exit 1); the exception domain over every enumerated
    class of both modules (including both intermediates and their
    subclasses), built-ins and a test-module class excluded, the pinned
    table, unmapped and later-release classes `refused`, a renamed
    `importlib` load of `workflow_state`; a raw `KeyError`/`OSError` from a
    patched `validate_state` is `internal_error`, a symlinked lock file
    `state_unreadable`; `describe` against the tables; identity stability,
    per-field change and isolation from other items; each `verify` fault
    on its own (corrupt or missing state, unknown phase, invalid config,
    dangling or terminal active id, `COMPLETE` without a trailer commit,
    mismatched installation record) and `skip` without a record;
    `resolve-artifact` against the helpers for a scoped item, a legacy-flat
    item and plan-stage phases, `invalid_request` for an unknown kind; both
    operations leave the state file and its mtime untouched.
- **Not yet in the manifest**: the three new files are added to
  `manifest.json` by CP7, with the conformance CI suite list.
- **Verification**: the eight release-source suites (the seven plus
  `workflow_protocol_test.py`) in a conformance fixture staged by
  `tools/release/release.py stage-conformance` from an unreferenced commit
  of the working tree whose `manifest.json` digests and sizes were refreshed
  and the three new files listed in that commit only:
  `workflow_protocol_test.py` 58 OK, `workflow_fingerprint_test.py` 256 OK,
  `workflow_state_test.py` 980 OK (1 skipped), `workflow_test_harness_test.py`
  19 OK, `workflow_integration_test.py` 267 OK,
  `workflow_acceptance_matrix_test.py` 291 OK (18 skipped),
  `workflow_state_completion_obligations_test.py` 106 OK,
  `workflow_fingerprint_generalization_test.py` 105 OK.
  `workflow-manager verify .`: installation matches workflow 2.6.0.

## `CP4` — `next-action` and `reconcile`

Requirements: REQ-3 (`next-action`: the total catalogue, dispositions,
worker requirements, `allowed_results`, stale-decision refusal), REQ-4
(`reconcile`), REQ-11 (a two-stage `REVISE` is applied by content).

- **Implementation** (release source only):
  - `payload/scripts/workflow_protocol.py`: `ACTIONS` (22 action ids, each
    with its command, rendered invocation and worker; `ACTION_IDS` is now
    the catalogue's); `CATALOGUE`, the one ordered list of the 55 rows in
    the plan's printed order, each `Row` carrying its `(phase, gv)` pairs,
    predicate, disposition, action, `remedy_commands` (per phase where the
    prose differs, row 6) and `refusing_commands`; `CONDITION_CALLS`, the
    per-row `{function, kind, classes}` table, evaluated only through
    `_Context.call`, which refuses an undeclared call, memoizes a value a
    later row reuses, and turns an unlisted Workflow exception into
    `condition_refused` at that row (a non-Workflow exception propagates to
    `internal_error`); `EDGES`, the legal-edge table with its same-phase
    proofs and `allowed_results`, which `next-action` copies into
    `action.allowed_results`; `next-action [--work-item ID]
    [--expect-state-identity HEX]` (`stale_decision` on a changed identity,
    `not_applicable` for an unsupported `gv`); `reconcile --decision FILE
    [--work-item ID]` (automatic decisions only; a malformed, tampered,
    foreign or non-automatic decision is `invalid_request`; classes
    `invalid` → `gate_reached` → `progress` → `no_progress`, then
    `result_not_allowed`; `plan.start` by the new active item; writes
    nothing).
  - `payload/scripts/workflow_state.py`: `implementing_entry_status` (causes
    `plan_approval_not_current`, `plan_approval_commit_unreachable`,
    `plan_content_drifted`), `implementing_entry_reachable` reduced to its
    `reachable` field; `plan_approval_gate_status` and
    `technical_approval_gate_status` (`{reachable, cause, inputs}`, the
    generation check first, then the bundle-bound check or the `bundle_id`
    computation, then the pure predicate's order) and `read_review_feedback`;
    `verify_implementation_review_bundle` and
    `ImplementationReviewBundleUnverifiedError` (naming the
    stale-plan-stage-manifest variant); `apply_review_feedback_binding_selection`,
    `assert_apply_review_feedback_binding` (content binding, checks 1-4, or
    2.6.0's bundle binding; every refusal carries its `binding`),
    `FeedbackContentMismatchError`, `ReviewBundleManifestMismatchError`.
  - `payload/scripts/workflow_fingerprint.py`: `assert_local_generation_matches`'
    docstring names the two gate wrappers as callers.
  - Commands: `apply-plan-review.md` and `apply-implementation-review.md`
    step 1 bind through `assert_apply_review_feedback_binding` and report
    its advisory and refusals by class; `review-implementation.md` step 4
    calls `verify_implementation_review_bundle`; `milestone-implement.md`
    1a calls `implementing_entry_status` and reports cause and remedy;
    `approve-review.md` step 1 keeps the `BLOCK` pin write first and calls
    the wrappers on the re-read state, naming the deliberate cause-order
    change (`LPR-R3-004`); step 2's generation and bundle-bound checks are
    described as run inside the wrapper.
  - `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`: "Required structure"
    states that a two-stage `REVISE` is applied by its
    `review_content_id`, the bundle fields advisory, and that nothing
    rewrites a reviewer's binding fields.
  - `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`:
    `reason`, `worker`, `action`, `snapshot`, `decision`, `phase_identity`,
    and the `next-action` and `reconcile` results.
  - `payload/scripts/workflow_test_harness.py`: real-bundle fixtures
    (`seed_bundle_item`, `generate_plan_bundle`,
    `publish_and_bind_plan_bundle`, `generate_implementation_bundle`,
    `approve_plan`, state helpers), self-tested in
    `workflow_test_harness_test.py`.
- **Tests**: `workflow_protocol_test.py` gains structure (row order,
  structural and dynamic totality over `KNOWN_PHASES` ×
  `SUPPORTED_GOVERNING_VERSIONS`, the latter in a `default_config()`
  repository; `CONDITION_CALLS` shape), the action and edge tables, every
  row from a real state (bundles generated by the real script), the apply
  binding (content variants, the forgery, other content, a tampered or
  missing bundle, another item's flat bundle, a manifest naming no item,
  another stage or base), ingest-to-apply routing, the raising-condition
  and acceptance-call rules, a recorder that fails any listed function a
  predicate calls outside its declared call, command agreement (each
  automatic row's guard sequence accepts its state; each command document
  names its guards), remedy and refusing commands against each command's
  phase gate, writer sequences ending on legal edges, stale decisions and
  every `reconcile` class; every decision in the suite is also checked for
  the prose rules (each named command in exactly one field; no remedy
  edits a binding field). `workflow_state_test.py` gains the two gate
  wrappers (each cause; `reachable` equals the predicate on `inputs`; the
  pin precedes the wrapper; the generation mismatch named before the pin,
  through a real provenance recovery) and `verify_implementation_review_bundle`.
  `workflow_integration_test.py`: the five changed command files' golden
  hashes, `/apply-plan-review`'s pinned step-1 phrase, and
  `workflow_state.py` as a fourth `assert_local_generation_matches` call site.
- **Deviations from the plan's text, found while implementing**:
  - Rows 7a and 8a declare `assert_apply_review_feedback_binding` twice,
    as a guard and as an acceptance: one invocation refuses with either a
    bundle-integrity class (the guard's) or a feedback class (the
    acceptance's). As printed, row 7a lists only the guard classes, so the
    forgery (`FeedbackContentMismatchError`) would end at row 7a as
    `condition_refused`, contradicting CP4's own forgery test ("the item
    gives row 9").
  - The tests that the plan words as "recorded through
    `record-external-result`" record through the same state writers
    (`record_manual_*_review`); CP5 adds the operation. The record-manual
    commands' guard-name text check is CP5's, which rewrites those two
    commands.
- **Self-review** (an independent agent checked the catalogue, the
  condition-call and edge tables, the wrappers' cause order, the apply
  binding and `reconcile` against the plan); three findings, all fixed:
  row 5 offered `plan.withdraw` also at publication row 6 (a non-ready
  phase holding a `BOUND` record), where `/milestone-plan`'s writers refuse
  the same record -- now only at a ready phase (row 4d), `none_exists`
  otherwise; row 35a tested an absent file rather than "no fb", so a
  verdict naming another item reported `review_feedback_not_current`
  instead of `review_feedback_missing`; row 8a recomputed **B** outside its
  declared calls, under a blanket `except` -- the bundle binding's refusal
  now carries its `bundle_id`.
- **Not yet in the manifest**: the new files stay out of `manifest.json`
  until CP7.
- **Verification**: the eight release-source suites in a conformance fixture
  staged by `tools/release/release.py stage-conformance` from an
  unreferenced commit of the working tree whose `manifest.json` digests and
  sizes were refreshed and the three CP3 files listed in that commit only:
  `workflow_protocol_test.py` 183 OK, `workflow_fingerprint_test.py` 256 OK,
  `workflow_state_test.py` 990 OK (1 skipped), `workflow_test_harness_test.py`
  22 OK, `workflow_integration_test.py` 267 OK,
  `workflow_acceptance_matrix_test.py` 291 OK (18 skipped),
  `workflow_state_completion_obligations_test.py` 106 OK,
  `workflow_fingerprint_generalization_test.py` 105 OK.
  `workflow-manager verify .`: installation matches workflow 2.6.0.

### Revalidation after plan revision 13 (2026-10-02)

Amendment 0 reworded three `default_config()` quotations in the plan; the
registry row's content changed for `CP4` only through that wording. No
code changes. Checked: `payload/scripts/workflow_protocol_test.py`, `Ran
213 tests`, `OK`, including
`test_every_phase_and_version_decides_in_a_default_config_repository`,
which is the behaviour the reworded sentence describes.


### `CP5` revalidation after plan revision 13 (2026-10-02)

`CP5`'s checkpoint text is unchanged; it was demoted by dependency closure
on `CP4`. No code changes. Checked in `payload/scripts/`:
`workflow_protocol_test.py`, `Ran 213 tests`, `OK` (it covers
`record-external-result`), and `workflow_state_test.py` filtered to the
ingest and `before_publish` tests, `Ran 21 tests`, `OK`.

### `CP6` revalidation after plan revision 13 (2026-10-02)

`CP6`'s checkpoint text is unchanged; it was demoted by dependency closure
on `CP4`. No code changes (`git diff 2a3c7c7 HEAD -- payload` is empty).
Checked: `payload/scripts/workflow_protocol_test.py`, `Ran 213 tests`,
`OK` (it holds the specification-table comparison and the three lifecycle
E2E runs), and the installed `GoverningVersionEnumerationSweepTest`
(`test_real_corpus_sweep_is_clean`, `scripts/`), `Ran 2 tests`, `OK`: the
corpus, now including the reworded plan, is clean.

### `CP7` revalidation after plan revision 13 (2026-10-02)

`CP7`'s checkpoint text is unchanged; it was demoted by dependency closure
on `CP4`. No release-source change (`git diff fec1b94 HEAD -- payload
manifest.json templates fixtures tools .github/workflows/workflow-ci.yml
docs/ROADMAP.md docs/RELEASING.md` is empty), so the manifest hashes
recorded at `fec1b94` still describe the release source. Checked here:
`payload/scripts/workflow_protocol_test.py`, `Ran 213 tests`, `OK`; the
installed `GoverningVersionEnumerationSweepTest`, `Ran 9 tests`, `OK`;
`workflow-manager verify .`, `installation matches workflow 2.6.0`.

Not re-run in this environment: the `release.py build` byte-for-byte checks
and the `release_test.py` cases that build a release (25 of 75 tests fail
with `zlib_ng is not installed`). This machine has only Python 3.14, and the
pinned `zlib-ng==1.0.0` wheel hash in `tools/release/deflate-requirements.txt`
does not match the cp314 wheel, so the pinned runtime was not installed and
the hash pin was not bypassed. The other 50 `release_test.py` tests pass. The
Python 3.12 run recorded at `fec1b94` is the last full release-build
verification, and nothing it covers has changed since.

## `CP5` — `record-external-result` and the shared ingest

Requirements: REQ-5 (`record-external-result`: one Workflow-owned ingest for
manual plan and implementation verdicts, shared by the commands), REQ-7's
ingest half (the required `review_content_id` label at the two-stage rows).

- **Implementation** (release source only):
  - `payload/scripts/workflow_state.py`: `state_transaction`'s
    `before_publish` keyword, run after the pin-monotonicity check and
    immediately before `_publish_state_file` (`MPR-R7-002`, `MPR-R8-003`);
    `ManualVerdictHeaderError`, `ConflictingReviewFeedbackError`;
    `select_manual_verdict_row` (the four rows of D-OP-External's table by
    stage, `gv` and phase; `two_stage_only` keeps the record-manual
    commands' 2.6.0 governing-version guard), `parse_manual_verdict` and
    `require_manual_verdict_fields` (CP1's parser plus a header-block
    `Round:`), and `ingest_manual_review_verdict`. A two-stage row runs the
    row selection, the header check, the guards in 2.6.0's order
    (`verify_implementation_review_bundle` before
    `assert_local_generation_matches` at the implementation row,
    `LPR-R5-002`), the second `assert_bundle_not_rejected` and the pure
    `record_manual_*_review` call as `state_transaction`'s mutator, and
    the atomic feedback write (under `assert_feedback_not_owned_by_other_work_item`,
    identical bytes a no-op) as its `before_publish`. A feedback-only row
    holds `state_lock` around the same steps and writes no state; it
    refuses a different verdict that already binds to the current bundle.
    `round` is `Round:` or the local `APPROVE`'s round; `bundle_id` is
    `Reviewed bundle ID:` verbatim, or `null` with the advisory
    `"Reviewed bundle ID: absent"` and no advisory check (`LPR-R3-005`).
  - `payload/scripts/workflow_protocol.py`: `record-external-result
    --work-item ID --kind KIND --input FILE`; `EXTERNAL_RESULT_KINDS` is
    `plan_review_verdict` and `implementation_review_verdict`; reserved
    kinds are `unsupported_result_kind`, an unknown kind or unreadable
    input `invalid_request`; a refusal meaning "no row here" (wrong phase
    or governing version, or a duplicate stage) is `not_applicable`, every
    other Workflow refusal `refused`. The result is `{stage, verdict,
    review_content_id, round, bundle_id, advisory, basis}`. The module now
    declares `state_writer: true`: this operation writes, through
    `workflow_state.state_transaction`/`state_lock`.
  - `payload/scripts/workflow_fingerprint.py`: the docstrings of
    `assert_local_generation_matches` and `WorktreeOrHeadMismatchError` name
    the record-manual commands, through the ingest, as callers (`LPR-R2-002`).
  - Commands: `record-manual-plan-review.md` and
    `record-manual-implementation-review.md` state that steps 2-7 are one
    call to the ingest with `two_stage_only=True`, holding the lock through
    the publication; the steps document its order; the required header
    fields, `Round:`, and the absent-bundle-id advisory are stated.
  - `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`: the
    `record-external-result` result.
- **Tests**: `workflow_state_test.py` gains
  `TestManualVerdictIngestRecordsAs260` (each verdict at both two-stage
  stages gives the `record_manual_*_review` state; the `## Review Decision`
  and no-`Work item:` shapes; both labels; the identical-bytes no-op),
  `TestManualVerdictIngestRefusals` (every listed refusal leaves the state
  and the feedback file byte-identical, including the verifier's
  precedence over the generation check and a `REJECTED` marker placed
  after the guards), `TestManualVerdictRoundAndBundleId`,
  `TestManualVerdictIngestCrashWindow`, `TestStateTransactionBeforePublish`
  (a hook exception publishes nothing; checks, hook, publish order; a
  failed pin check never calls the hook) and
  `TestConcurrentManualVerdictIngests` (real processes: at each two-stage
  row two different verdicts started together, and the first paused
  between its guards and its write while the second blocks on the lock;
  at each feedback-only row, the conflict and the no-op).
  `workflow_protocol_test.py` gains `TestRecordExternalResultTwoStage`
  (the command path's state at every two-stage row and verdict; the same
  `round`/`bundle_id` through both paths; refusals; a duplicate and a retry
  are `not_applicable`; the crash window retried once through either path,
  with rows 13/27 reported in between; `MPR-R8-001`'s absent and
  pre-regeneration bundle ids routing to row 8/36, whose command accepts
  the file by content), `TestRecordExternalResultFeedbackOnly` and
  `TestRecordExternalResultApplicability`; the record-external command
  guards now run the ingest, and the command documents must name it.
  `workflow_integration_test.py`: `record-manual-plan-review.md`'s golden
  hash.
- **Deviations from the plan's text, found while implementing**:
  - No row is reported by the existing `WrongPhaseFor*ReviewStageError`/
    `WrongGoverningVersionFor*ReviewStageError` classes rather than a new
    one: the command path then refuses exactly as 2.6.0's steps 2-3 did,
    and the protocol maps them (and the two `Duplicate*` classes) to
    `not_applicable` inside the operation, not in the global exception
    table.
  - Whether a row is two-stage depends on the governing version alone, so
    the ingest reads it before taking the lock to choose between
    `state_transaction` and a bare `state_lock`; the row itself, and every
    guard, is selected and run on the state re-read under the lock.
  - `ingest_manual_review_verdict` also returns `feedback_written`, which
    the protocol result omits.
- **Not yet in the manifest**: as for CP4, the new files stay out of
  `manifest.json` until CP7.
- **Verification**: the eight release-source suites in a conformance fixture
  staged by `tools/release/release.py stage-conformance` from an
  unreferenced commit of the working tree whose `manifest.json` digests and
  sizes were refreshed and the three CP3 files listed in that commit only:
  `workflow_protocol_test.py` 197 OK, `workflow_fingerprint_test.py` 256 OK,
  `workflow_state_test.py` 1011 OK (1 skipped), `workflow_test_harness_test.py`
  22 OK, `workflow_integration_test.py` 267 OK,
  `workflow_acceptance_matrix_test.py` 291 OK (18 skipped),
  `workflow_state_completion_obligations_test.py` 106 OK,
  `workflow_fingerprint_generalization_test.py` 105 OK. Only a comment in
  `workflow_integration_test.py`'s `EXPECTED_CALL_SITES` changed after
  staging.

## `CP6` — Specification, documentation, lifecycle E2E

Requirements: REQ-10 (shipped normative spec; command and operator documents
agree; protocol-only lifecycle E2E), REQ-1's specification half.

- **Implementation** (release source only):
  - `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (new): versioning
    (and the releases tested against v1, 2.7.0), the invocation, envelope,
    exit codes and error codes with the Workflow exception domain, state
    identity and basis, each operation's request, result (citing the
    schema's `$defs.results`) and refusals, the ingest table, the actions
    and worker roles, the condition terms and kinds, the condition-call
    table, the catalogue table with its notes (the `"1"` states and
    `v2.6.0-003`, `BLOCK`, applied `"1"` verdicts, content-bound `REVISE`,
    bundle integrity, row order), the legal-edge and proof tables with
    `reconcile`'s classification, consumer obligations, the W2 reservations
    and the compatibility notes (D-Feedback-Label, D-Consumed-History,
    D-Apply-Binding, the 2.6.0 query CLIs). Its tables were rendered from the
    code's own tables.
  - `payload/.claude/commands/accept-milestone.md` step 2a: no longer tells
    the operator to finish an outstanding checkpoint with
    `/milestone-implement`; it says that command cannot start one at
    `AWAITING_FUNCTIONAL_REVIEW` and that no 2.6.0 command completes one
    there (`v2.6.0-003`), keeping the `/apply-functional-review` routing.
  - `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`: a `next-action` row in "Which
    command do I run next?", and the "Driving the Workflow by protocol"
    section. `MILESTONE_WORKFLOW.md`: the paragraph in "Hard gates summary"
    stating that the protocol reports the same gates and adds none (count
    still 6).
  - `payload/scripts/workflow_protocol_test.py`:
    `TestSpecificationTablesEqualTheCode` (8 tests) parses the spec's
    catalogue, condition-call, edge, proof and action tables and compares
    them with `CATALOGUE`, `CONDITION_CALLS`, `EDGES` and `ACTIONS`, row for
    row and in order, plus the error-code, artifact-kind, exit-code and
    ingest tables, and checks that a drifted table is caught.
    `TestOperatorDocuments` (3 tests) pins step 2a's text (no
    `/request-plan-amendment`, `/milestone-implement` only in a "cannot"
    sentence, the routing kept), the operator reference's pointer, and the
    hard-gates paragraph. The lifecycle E2E (`_Lifecycle`):
    `TestLifecycleEndToEnd2_2` drives a `"2.2"` item from no work item
    (`plan.start`, row 1) to row 40 by `next-action` alone, with the identity
    check before each launch, each automatic action's `COMMAND_GUARDS`
    sequence and then its writers, `reconcile` after each automatic action
    and `next-action` after each gate. It has a `REVISE` round at the local
    and manual stages of both reviews (manual verdicts through
    `record-external-result`) and two checkpoints, the first of them
    same-phase progress. It also asserts once that `reconcile` refuses a
    gate's own decision. `TestLifecycleEndToEndV1` has the `"1"` plan round
    (rows 21, 18, gate_reached at 20, approval, row 6a) and the `"1"`
    implementation round with `registry_path: null` (rows 35, 32, 35, 33,
    37, 39, then `complete`).
  - `payload/scripts/workflow_test_harness.py`: `generate_plan_bundle`
    writes the item's current `plan_revision` into `TEST_RESULTS.md` (it was
    always 1), which the `"1"` apply round needs.
  - `payload/scripts/workflow_integration_test.py`: `accept-milestone.md`'s
    golden hash, with its reason; `human_gate`/`external_gate` allowlisted
    as literal values in the operator-reference symbol check.
- **Deviations from the plan's text, found while implementing**:
  - The operator reference's "Which command do I run next?" row for
    "a checkpoint still outstanding" and the acceptance paragraph after the
    table repeated step 2a's inaccuracy, so they are corrected too
    (REQ-10: the command and operator documents agree).
  - `IncompleteOwnCheckpointsError`'s message in `workflow_state.py` still
    carries 2.6.0's `/milestone-implement` advice. CP6 changes no code, so
    step 2a now says the message carries that advice and that it cannot run
    at this phase. It belongs with the `v2.6.0-003` follow-up (CP7's
    roadmap row).
  - The specification also mirrors the actions table, which a test checks
    too, beyond the three tables CP6 names.
  - The E2E's writer sequences are the commands' state functions and
    commits: the plan approval is `apply_plan_approval` and an approval
    commit, without `/approve-review plan`'s journal and closure-proof
    machinery; plan edits are committed before the regeneration; the
    implementation fix is committed with the state of the recorded verdict.
- **Self-review**: an independent agent checked the specification's prose
  and free-text columns against the code and the plan. It made 15
  findings, all fixed: the input-file and installation-record exceptions
  to the `OSError` rule; the unlocked read when the lock file is absent;
  `verify`'s skip rules; `action` null for every `blocked` row;
  `reconcile`'s `--work-item` for `plan.start` and the optional `row`;
  `Round:` refusing when malformed; the bundle-id advisory's wording; retry
  outcomes; `state_invalid` standing alone; `no_work_item` reserved; the
  remedies and conditions of rows 5, 8a, 10, 34 and 35; the schema path.
  It also raised two minor points, both fixed.
- **Not yet in the manifest**: the new specification joins the three CP3
  files in `manifest.json` in CP7.
- **Verification**: the eight release-source suites in a conformance
  fixture staged by `tools/release/release.py stage-conformance`. The
  fixture came from an unreferenced commit of the working tree whose
  `manifest.json` digests and sizes were refreshed, with the four new files
  listed in that commit only. Results: `workflow_protocol_test.py` 213 OK,
  `workflow_fingerprint_test.py` 256 OK, `workflow_state_test.py` 1011 OK
  (1 skipped), `workflow_test_harness_test.py` 22 OK,
  `workflow_integration_test.py` 267 OK,
  `workflow_acceptance_matrix_test.py` 291 OK (18 skipped),
  `workflow_state_completion_obligations_test.py` 106 OK,
  `workflow_fingerprint_generalization_test.py` 105 OK. After the
  self-review fixes and the symbol allowlist, the protocol, integration
  and harness suites were rerun green in a restaged fixture.
  `workflow-manager verify .`: the installation matches workflow 2.6.0.

## `CP7` — Release 2.7.0

Requirements: REQ-9 (2.7.0 releasable: manifest, conformance CI and template
run the new suite, release-constant guard).

- **Implementation**:
  - `manifest.json`: `workflow_version` `2.7.0`; `provenance` is
    `{origin: "authored", base_release: "2.6.0"}` (`OD-W1-4`), with
    `overlay_commit`, every `overlay_delta` and the `overlay_*` counts
    dropped; four new artifacts, `scripts/workflow_protocol.py`,
    `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` and
    `docs/ai-workflow/orchestration-protocol-v1.schema.json`
    (`distribution`) and `scripts/workflow_protocol_test.py`
    (`conformance`); refreshed `sha256`/`size` for the 23 changed artifacts,
    each rationale extended with what W1 changed and in which checkpoint;
    the `workflow-conformance.yml` template's digest, size and derivation;
    `counts` 67 artifacts (42 distribution, 23 conformance, 2 host-evidence),
    6 templates.
  - `templates/.github/workflows/workflow-conformance.yml`: an eighth step,
    `workflow_protocol_test.py`. `.github/workflows/workflow-ci.yml`: the
    same step in `release-source-conformance`.
  - `tools/release/package.py`: the release-constant guard,
    `check_release_constant`, run by `build` before anything is written.
    When the manifest lists `scripts/workflow_protocol.py`, the file must
    hold exactly one `WORKFLOW_RELEASE = "<v>"` line equal to the manifest
    version, or the build refuses and names both. `release_test.py`:
    `ReleaseConstantGuardTest` (match, mismatch naming both, missing or
    repeated literal, absence in a minimal 2.6.0 release and in each of the
    five published releases, and HEAD's own release).
  - `docs/ROADMAP.md`: W1 marked complete; a "Workflow 2.7.0" entry;
    `v2.6.0-001` and `v2.6.0-002` "Fixed in 2.7.0" (the `v2.6.0-002` row was
    missing and is added); the new `v2.6.0-003-v1-state-tracked-item-cannot-advance`
    row with its write-up (both `"1"` gaps, row 38b, the remediation-child
    sentence, the corrected step-2a prose and `IncompleteOwnCheckpointsError`'s
    remaining advice, row 38c). `docs/RELEASING.md`: one sentence on the
    guard, and "eight" suites.
- **Verification** (Python 3.12.14, `zlib-ng` 1.0.0 / zlib-ng 2.2.5, Workflow
  Manager 1.2.0 from the pinned wheel, sha256 checked), against an
  unreferenced commit of the working tree, `67452e4`:
  - `release.py build --commit 67452e4`: `version=2.7.0`, `files=74`,
    `tar_sha256=96dc1154…`, `archive_sha256=1873fbbc…`,
    `manifest_sha256=2dabaae0…`;
  - `workflow-manager package verify`: `release 2.7.0, 73 files, verified`;
    `--release-dir` bootstrap of a scratch repository: `bootstrapped
    workflow 2.7.0 (full)`, and its verify: `installation matches workflow
    2.7.0`;
  - `check-title "feat: Workflow 2.7.0 with Orchestration Protocol v1"
    --agree`: `impact=minor`, `version 2.6.0 -> 2.7.0 (minor) agrees with
    the title`; `check-pending`: `ok: 2.6.0 -> 2.7.0 (minor)`;
    `check-immutable`: `ok: version 2.7.0 is not published`;
  - the eight release-source suites in the fixture staged from `67452e4`:
    `workflow_fingerprint_test.py` 256 OK, `workflow_state_test.py` 1011 OK
    (1 skipped), `workflow_test_harness_test.py` 22 OK,
    `workflow_integration_test.py` 267 OK,
    `workflow_acceptance_matrix_test.py` 291 OK (18 skipped),
    `workflow_state_completion_obligations_test.py` 106 OK,
    `workflow_fingerprint_generalization_test.py` 105 OK,
    `workflow_protocol_test.py` 213 OK;
  - `release_test.py`: 75 OK, including the five-release reproduction, in
    a scratch clone with the change committed. In this working tree, before
    the checkpoint commit, `test_round_trip` fails as expected: it builds
    the committed `HEAD`, whose manifest is still CP6's;
  - `workflow-manager verify .`: the installation matches workflow 2.6.0.

## Implementation self-review

Status: **blocked** (2026-10-02). The full milestone diff (`ef714f3..HEAD`,
CP1 to CP7) was reviewed against the plan (revision 12). The code, the
release source and the release tooling raised no blocking or important
finding. One blocking finding is in the approved plan document itself, and
fixing it needs a plan amendment, so the implementation bundle was **not**
generated. `enter_self_reviewing_implementation` was a no-op: the phase was
already `SELF_REVIEWING_IMPLEMENTATION`.

- **Blocking: the required `workflow-conformance` check fails on this
  branch.** The installed (2.6.0) `scripts/workflow_state_test.py`,
  `GoverningVersionEnumerationSweepTest.test_real_corpus_sweep_is_clean`,
  sweeps the top level of `docs/ai-workflow/*.md` for exhaustive
  governing-version enumerations. It flags three lines of
  `docs/ai-workflow/ORCHESTRATION_PROTOCOL_V1_PLAN.md` (`exhaustive_enumeration`
  at lines 360, 1860 and 2681), each the literal `` `["1","2.1"]` `` that
  quotes `default_config()`. Under Python 3.12, as CI runs it, the suite
  reports `Ran 972 tests`, `FAILED (failures=1, skipped=1)`. The lines
  were added by the plan-approval commit `ecf05b0`, so the check has failed
  since then. The release-source suites pass, because the plan is not part
  of the release source. 2.7.0 ships the same sweep, so installing 2.7.0
  here later would not clear it.
  The plan is plan-stage protected, so any edit makes the plan approval
  stale (`plan_content_drifted`), and `scripts/` is the frozen installation.
  The remedy is a plan amendment that rewords the three quotations. Checked:
  replacing each `` `["1","2.1"]` `` with `` `"1"` and `"2.1"` only `` leaves
  the sweep with no findings over the whole plan.
- **Minor, not fixed:** `next-action --expect-state-identity` with a value
  that is not 64-hex refuses as `stale_decision` (retryable) rather than
  `invalid_request`. This matches the specification's wording ("refuses
  with `stale_decision` when the current identity differs"), and a
  re-decision recovers. The CLI's `argparse` parsers also accept unique
  prefixes of long options (`--work` for `--work-item`).
- Probed beyond the suites: the protocol CLI against this repository's
  real state (`describe`; `verify` healthy except
  `installation_release_matches`, as expected for 2.7.0 scripts over a 2.6.0
  installation; `next-action` row 24 `self_review_due`; `resolve-artifact`;
  `reconcile` of that decision `no_progress`; the `stale_decision`,
  `unknown_work_item`, `unsupported_protocol`, `unsupported_result_kind`
  and `not_applicable` refusals). The header-only `review_content_id`
  parser reads both real feedback files in `.ai-review/` correctly. The
  installation is untouched (`git diff ef714f3..HEAD` over `.claude/`,
  `scripts/`, `.workflow-manager/`, the managed documents and
  `workflow-conformance.yml` is empty).

Full verification at `fec1b94`, in Python 3.12.14 with the pinned `zlib-ng`
1.0.0 (zlib-ng 2.2.5) and the pinned Workflow Manager 1.2.0 (wheel sha256
`f7ab05a2…4139`, equal to `tools/release/manager-pin.json`):

- `release_test.py`: `Ran 75 tests`, `OK`;
- `release.py build --commit HEAD`: `version=2.7.0`, `files=74`,
  `tar_sha256=96dc1154…`, `archive_sha256=1873fbbc…`,
  `manifest_sha256=2dabaae0…` (CP7's digests);
- `workflow-manager package verify`: `release 2.7.0, 73 files, verified`;
  `--release-dir` bootstrap of a scratch repository: `bootstrapped workflow
  2.7.0 (full)`, and its verify: `installation matches workflow 2.7.0`;
- against the live release list: `check-title "feat: Workflow 2.7.0 with
  Orchestration Protocol v1" --agree` `impact=minor`, agrees;
  `check-pending` `ok: 2.6.0 -> 2.7.0 (minor)`; `check-immutable` `ok:
  version 2.7.0 is not published`;
- `workflow-manager verify .`: `installation matches workflow 2.6.0`;
- `stage-conformance --commit HEAD`, then the eight release-source suites
  in the fixture: all `OK` (fingerprint 256, state 1011, test_harness 22,
  integration 267, acceptance_matrix 291 with 18 skipped,
  completion_obligations 106, fingerprint_generalization 105, protocol 213);
- the installation's seven suites in `scripts/` (the `workflow-conformance`
  job), under Python 3.14.7: fingerprint 242, test_harness 19, integration
  267, acceptance_matrix 291, completion_obligations 106 and
  fingerprint_generalization 105 `OK`; **state 972, `FAILED (failures=1)`**,
  the finding above, reproduced under Python 3.12.14.
- The `./gradlew …` line of `/milestone-implement` step 3 is for Android
  repositories and does not apply here.

### Implementation self-review after plan revision 13 (2026-10-02)

Status: **complete**. `/milestone-implement`'s 1a-1c returned
`NO_CHECKPOINT` (plan approval reachable, every registry checkpoint
`COMPLETE`), and `enter_self_reviewing_implementation` was a no-op (phase
already `SELF_REVIEWING_IMPLEMENTATION`, `state_revision` 72 unchanged), so
no phase commit was made.

- **The blocking finding above is resolved.** Amendment 0 (plan revision 13)
  reworded the three quotations; the installed `workflow_state_test.py`
  now runs `Ran 972 tests`, `OK` under Python 3.12.14.
- **Re-review of the milestone diff** (`ef714f3..ddc2672`): the release
  source is byte-identical to the reviewed `fec1b94`. Since then only the plan
  wording, the registry's `plan_revision`, the state, `docs/ACTIVE_MILESTONE.md`
  and this ledger changed. `workflow_protocol.py` was re-read in full
  (envelope, exception domain, the state read, `verify`, `resolve-artifact`,
  the catalogue and its condition-call table, `EDGES`, `reconcile`,
  `record-external-result`), with the helpers it relies on
  (`implementing_entry_status`'s causes against row 22's remedy table, the
  stage-key normalizers, `ingest_manual_review_verdict`'s two paths). No
  blocking or important finding. Minor, not fixed, besides the two above:
  `--protocol-major` is read by `parse_known_args` anywhere in `argv`, so
  `describe --protocol-major 2` is `unsupported_protocol` while
  `describe --protocol-major 1` is `invalid_request` (the global option is
  documented before the operation, where both behave as specified).
- **Release checks at the branch tip.** `check-title --agree` and
  `check-pending` compare a commit with its first parent, so at
  `ddc2672` (whose parent already says 2.7.0) they report `2.7.0 -> 2.7.0
  (none)`, and `check-title` refuses `feat:`. That is the tip, not the pull
  request: run against an unreferenced commit with `ddc2672`'s tree and
  `main` (`ef714f3`) as its only parent (`d8835ef`, what the squash merge
  produces), they report `version 2.6.0 -> 2.7.0 (minor) agrees with the
  title` and `ok: 2.6.0 -> 2.7.0 (minor); release source changed: …`.

Full verification at `ddc2672`, Python 3.12.14 in a fresh venv with the
pinned `zlib-ng` 1.0.0 (zlib-ng 2.2.5, hash-checked) and Workflow Manager
1.2.0 (wheel sha256 checked against `tools/release/manager-pin.json`):

- `release_test.py`: `Ran 75 tests`, `OK` (the 25 build tests that could
  not run at the `CP7` revalidation ran here);
- `release.py build --commit HEAD`: `version=2.7.0`, `files=74`,
  `zlib_ng=2.2.5`, `tar_sha256=96dc1154…`, `archive_sha256=1873fbbc…`,
  `manifest_sha256=2dabaae0…`, equal to `CP7`'s;
- `workflow-manager package verify`: `release 2.7.0, 73 files, verified`;
  `--release-dir` bootstrap of a scratch repository: `bootstrapped workflow
  2.7.0 (full)`, and its verify: `installation matches workflow 2.7.0`;
- live release list (`v2.3.1` … `v2.6.0`, no drafts): `check-immutable`
  `ok: version 2.7.0 is not published`; `check-title`/`check-pending` as
  above;
- `workflow-manager verify .`: `installation matches workflow 2.6.0`;
- `stage-conformance --commit HEAD`, then the eight release-source suites in
  the fixture: fingerprint 256, state 1011, test_harness 22, integration
  267, acceptance_matrix 291 (18 skipped), completion_obligations 106,
  fingerprint_generalization 105, protocol 213, all `OK`;
- the installation's seven suites in `scripts/` (the `workflow-conformance`
  job): fingerprint 242, state 972, test_harness 19, integration 267
  (1 skipped), acceptance_matrix 291 (18 skipped), completion_obligations
  106, fingerprint_generalization 105, all `OK`;
- the working tree was clean afterwards. `./gradlew …` does not apply to
  this repository.

### Implementation review round 1: disposition (2026-10-02)

`LOCAL_MODEL_IMPLEMENTATION_REVIEW`, `REVISE`, bundle `dc027545…`,
`review_content_id` `76e5b298…`. No Blocking finding, one Important, three
Optional. The plan-amendment route is unavailable from
`APPLYING_REVIEW_FEEDBACK` (`_AMENDMENT_REQUEST_ALLOWED_PHASES` is
`IMPLEMENTING` and `SELF_REVIEWING_IMPLEMENTATION` only), so the user chose,
verbatim, "fix it in this round", without a plan amendment. The plan is not
edited: it is protected plan-stage content, and editing it would stale the
approved plan. The disposition is recorded here and in
`IMPLEMENTATION_SUMMARY.md`.

- **Important 1, accepted and fixed (commit `5b587e8`).** Reproduced before
  any change: `verify_checkpoint_completions` over the real history raises
  `AmbiguousCheckpointTrailerError` for CP4 to CP7 (two trailer commits each,
  both first-parent ancestors, both recording the checkpoint `COMPLETE`), so
  `reconcile` returned `invalid`/`checkpoint_completion_unproven` and
  `verify` check 5 failed. The plan's promise that check 5 passes for
  `COMPLETE` checkpoints held only for histories without a revalidation.
  Fix, in `payload/scripts/workflow_protocol.py` only:
  `prove_checkpoint_completions` is the one proof used by `reconcile` and by
  `op_verify` check 5. It calls `workflow_state._discover_trailer_commits`
  with the 2.6.0 tie-break predicate (committed state records the checkpoint
  `COMPLETE`) plus a third filter, strict descent from the checkpoint's
  recorded `checkpoints[<id>].start_commit`, which a revalidation rewrites.
  The extra filter is consulted only when the first two leave a tie, so any
  history 2.6.0 resolved resolves identically (corrected in round 2: the
  descent filter also applies when the first two would resolve, so one
  malformed history can differ from 2.6.0; see the docstring of
  `prove_checkpoint_completions`). `discover_checkpoint_commits`,
  `verify_checkpoint_completions` and every 2.6.0 command are unchanged.
  Descent is strict because a revalidation can start at the commit that was
  the checkpoint's own earlier completion. Two tests drive the lifecycle
  through the CLI: a checkpoint completed, demoted to `NEEDS_REVALIDATION` and
  re-completed is `progress` under `reconcile` and `pass` under `verify`; and
  a second trailer commit that is not a revalidation (same start) is still
  `invalid`. `manifest.json` digests for the script and its suite were
  refreshed.
  Real history at the fix: `workflow_protocol.py verify` reports
  `checkpoint_completions_provable: pass` (orchestration-protocol-v1);
  `installation_release_matches` still fails, correctly, until 2.7.0 is
  installed (the installation is 2.6.0 and untouched).
- **Missing tests, applied**: the two tests above (protocol suite 213 -> 216).
- **Optional 1, not applied.** The bare `KeyError`/`AssertionError` in
  `ingest_manual_review_verdict` is reachable only by a state race after the
  protocol resolved the item, and giving it a stable code means a new
  exception class in the registered domain with its tests, which is not
  cheap or low-risk in a fix round. Deferred.
- **Optional 2, not applied**: the three CLI items already recorded stay
  deferred, as the reviewer agreed.
- **Optional 3, applied** in `TEST_RESULTS.md`: the state suite is reported as
  1011 with one skipped.

Verification after the fix, Python 3.12.14, the pinned `zlib-ng` 2.2.5:
`stage-conformance --commit HEAD` and the eight release-source suites
(fingerprint 256, state 1011 (1 skipped), test_harness 22, integration 267,
acceptance_matrix 291 (18 skipped), completion_obligations 106,
fingerprint_generalization 105, protocol 216), all OK; `release_test.py` 75
OK; `release.py build --commit HEAD` gives tar/archive/manifest sha256
`96d89352…`/`770c35d2…`/`17503864…` (they differ from the previous round
because the manifest and two files changed); `workflow-manager verify .`:
installation matches workflow 2.6.0; `git diff ef714f3..HEAD` over `.claude/`,
`scripts/`, `.workflow-manager/` and `workflow-conformance.yml` is empty.

### Implementation review, rounds 2 and 3

- **Round 2, Important 1, accepted and fixed (commit `b8bf647`).**
  `ORCHESTRATION_PROTOCOL.md` check 5 and `reconcile`'s
  `checkpoint_completion_unproven` now name `prove_checkpoint_completions` and
  its `start_commit` descent filter. Optional 1, applied (commit `0256c0a`):
  the docstring no longer claims the descent filter applies only on a tie.
- **Round 3, Important 1, accepted and fixed.** Reproduced by reading
  `workflow_state._discover_trailer_commits`: a single trailer candidate
  resolves before any filter, a single first-parent candidate resolves
  without the `verify` predicate, and only two or more first-parent candidates
  reach the `COMPLETE`-and-descent predicate (`OPUS-R129-M03`). Check 5 now
  describes these as ordered tie-breaks. `manifest.json`'s digest and size for
  the specification were refreshed; no code changed. `reconcile`'s wording
  defers to check 5 and is unchanged.
- **Round 3, Optional 1, applied**: `TEST_RESULTS.md` hashes refreshed.
- **Round 3, Optional 2, applied**: the ledger claim corrected and these
  dispositions added.
- **Round 3, Optional 3**: the `ingest_manual_review_verdict` pre-lock peek
  stays deferred, as recorded in round 1.
