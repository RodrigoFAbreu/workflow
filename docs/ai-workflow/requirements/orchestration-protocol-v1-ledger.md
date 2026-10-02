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
