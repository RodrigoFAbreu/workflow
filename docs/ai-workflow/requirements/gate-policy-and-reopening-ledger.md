# `gate-policy-and-reopening` Requirements Ledger

Mutable, human-readable execution record for the `gate-policy-and-reopening`
work item (W2). Physically separate from the immutable, machine-readable
`gate-policy-and-reopening-mapping.json` in this same directory: the mapping
is the approved requirement↔checkpoint binding and is plan-stage protected;
this ledger resolves under the excluded prefix `docs/ai-workflow/requirements/`,
so editing it never stales an approval.

Each checkpoint appends one section here as it completes. This is a log, not
a status source: `WORKFLOW_STATE.json`'s `checkpoints[id]` remains the sole
record of checkpoint status.

## `CP1` — Gate policy model

Requirements: REQ-1 (the closed schema, the automatic default, the master
switch and per-gate overrides, the default `distinct_reviewer_models`
requirement, user-only adoption by digest), REQ-2 (tighten-only effective
policy, the recorded floor, provenance by content and chain that survives a
squash, the stated merge rule, gate-lowering events), REQ-11 (the roadmap
refresh, W1 complete including the cutover and W2 in progress).

- **Implementation** (release source only):
  - `payload/scripts/workflow_gate_policy.py` (new, `state_writer: false`,
    stdlib-only, never imports `workflow_state`): the closed schema
    (`policy_errors`, `validate_policy`), `DEFAULT_POLICY`, the resolved
    (flat) form (`resolve_policy`, `FIELDS`), `policy_digest`, `stricter`,
    `loosened_fields`, `tightened_fields`, the confirmation validator, the
    adoption and floor record validators, `read_policy_file` (never raises),
    `effective_policy` (D-GP-Policy's table, with `ignore_file` for the
    adoption's "before"), `record_gate_policy_floor` (the ratchet's one
    writer: it returns a state, never loosens, restores a removed committed
    floor), `verify_gate_policy_provenance` (the adoption's newest change and
    every floor change since the newest adoption-introducing commit, by
    content and chain; the reset exemption; the three-way merge bound;
    criss-cross merges fail closed), `assert_gate_policy_fields_unchanged_or_tightened`,
    `adoption_lowering`/`gate_lowering_event` (recomputed from history, never
    the label), `verify_check`, `gate_mode` and `evaluate_gate`'s skeleton
    (the `human` result; an automatic gate is reported unevaluated until
    CP2). Git history is read with two batched `git cat-file` processes and
    parsed once per distinct state blob.
  - `payload/scripts/workflow_state.py`: `import workflow_gate_policy`; the
    optional top-level `gate_policy_adoption` and `gate_policy_floor` and
    their `validate_state` check (`InvalidGatePolicyStateError`);
    `validate_gate_policy_confirmation`; `record_gate_policy_adoption` (the
    adoption plus the reset floor); `validate_gate_policy_adoption_commit`
    and `validate_gate_policy_floor_commit` (exactly the diff each contract
    names); `stage_scoped_state` (item scope, `GATE_POLICY_ADOPTION_SCOPE`,
    `GATE_POLICY_FLOOR_SCOPE`); `commit_gate_policy_floor`;
    `gate_policy_adoption_preview` and `open_bundles_staled_by_adoption`;
    `adopt_gate_policy`; `assert_gate_policy_fields_unchanged_or_tightened`,
    called at the end of `verify_plan_approval_commit`. `APPROVAL_STAGES`,
    `_forbidden_state_mutation` and the four commit validators are unchanged.
  - `payload/scripts/workflow_protocol.py`: `verify` gains the advisory
    eighth check `gate_policy` (`ADVISORY_VERIFY_CHECKS`: never part of
    `protocol_ready`, never changes `healthy`); `workflow_gate_policy`'s
    exceptions are Workflow exceptions for the error-code mapping. The schema
    (`orchestration-protocol-v1.schema.json`) lists the check id and the new
    check status `warn`; `ORCHESTRATION_PROTOCOL.md` section 5.2 says so.
  - `payload/.claude/commands/adopt-gate-policy.md` (new, `user_only`,
    `state_writer: true`); one sentence each in `approve-review.md`,
    `milestone-implement.md`, `apply-implementation-review.md`,
    `apply-functional-review.md` and `recover-implementation-provenance.md`
    (item-scoped staging, exactly the commits whose validator calls
    `_forbidden_state_mutation`) and in `milestone-implement.md` (twice) and
    `request-plan-amendment.md` (the content check after the unvalidated
    whole-file commits, which keep 2.7.0's staging).
  - `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`: the
    `/adopt-gate-policy` section the roster tests require (CP7 writes the
    guide).
  - `payload/scripts/workflow_gate_policy_test.py` (new suite, 113 tests) and
    the existing suites' fixtures (`workflow_gate_policy.py` is now one of
    the files a scratch repository copies beside `workflow_state.py`),
    `workflow_integration_test.py` (the four changed commands' golden hashes
    with their reason; the command count 17 to 18).
  - `docs/ROADMAP.md` and `tools/release/release_test.py` (`RoadmapTest`, the
    docs check): W1 complete without the cutover clause, W2 in progress, the
    "Where things stand" paragraph at 2.7.0, and the stale "The `Release`
    workflow publishes it when its pull request merges" line corrected.
- **Decisions made inside the plan's text** (nothing here widens it):
  - The adoption record's `lowered` label is optional on read: D-GP-Policy
    requires a hand-built adoption that "omits or empties `lowered`" to be
    accepted by provenance and still reported, so the validator does not
    require the key. The writer always writes it.
  - `policy_digest` is the sha256 of the canonical bytes (sorted keys,
    compact, UTF-8) of whatever dict it is given: the raw file body for an
    adoption (so the digest shown to the user is independent of key order and
    whitespace) and the resolved form for the floor.
  - The adoption's `lowered` label and `gate_lowering_event` share one
    definition, `adoption_lowering`, evaluated against the commit's own first
    parent's committed adoption and floor.
  - The criss-cross refusal applies to every in-range merge whose floor
    changed against its first parent, not only to an adoption-bringing one
    (D-GP-Policy says "with more than one ... the verification fails closed
    on that merge"; the plan's test says "in every configuration").
  - `bootstrap-workflow-v2.md` gets no scoped-staging sentence: it is the
    one-time driver of `workflow-v2-1-core` and is named as outside the flow
    by the grep test.
- **Deferred inside the plan's own ordering** (not omissions):
  - The `next-action` `policy` object with `gate_lowering` on a new row and a
    read-only `next-action` computing the virtual floor need rows that CP6
    adds (D-GP-Rows); CP1 provides and tests their data
    (`effective_policy`, `gate_lowering_event`).
  - `/apply-pr-review`'s scoped-staging sentence is CP5's (the command does
    not exist yet).
  - `GATE_POLICY.md`, the operator guide's policy chapter, the threat-model
    text and the merge-rule text are CP7's; `adopt-gate-policy.md` already
    names `docs/ai-workflow/GATE_POLICY.md`.
  - The manifest and the conformance workflow are CP8's: the suites below ran
    in a conformance fixture built from the working tree (digests unchecked).
- **Measured**: effective policy for a repository with no adoption and 2000
  commits of an 85 KB state file: 1.4 s, 60 MB.
- **Checks run once** (D-GP-Compat, section 10): `classify_path` and
  `classify_path_implementation_stage` over the 37 paths the plan names, with
  the work item's own declarations: none unclassified.
- **Verification**: the eight release-source suites and the new one, in a
  conformance fixture built from the working tree (digests unchecked, the
  manifest being CP8's): `workflow_gate_policy_test.py` 114 OK,
  `workflow_protocol_test.py` 217 OK, `workflow_state_test.py` 1011 OK
  (1 skipped), `workflow_fingerprint_test.py` 256 OK,
  `workflow_integration_test.py` 267 OK, `workflow_acceptance_matrix_test.py`
  291 OK (18 skipped), `workflow_state_completion_obligations_test.py` 106 OK,
  `workflow_fingerprint_generalization_test.py` 105 OK,
  `workflow_test_harness_test.py` 22 OK; `tools/release/release_test.py` 79 OK
  under the pinned runtime. `workflow-manager verify .`: installation matches
  workflow 2.6.0.

## `CP2` — Automatic plan and technical approvals, with audit evidence

Requirements: REQ-4 (plan and implementation approvals satisfied by current
local plus independent cross-model review evidence, every existing
precondition retained, distinct reviewer families by default, an auditable
record), REQ-12 (the trust boundary for review verdicts, CP2's part).

- **Implementation** (release source only):
  - `payload/scripts/workflow_gate_policy.py`: `evaluate_gate` for
    `plan_approval` and `technical_approval` (wrapper `reachable`, `APPROVE`
    bound to the recomputed bundle id, `distinct_reviewer_models`,
    `review_evidence_audited`), `distinct_reviewer_models`, `reviewer_family`,
    `ledger_entry_sha256`.
  - `payload/scripts/workflow_fingerprint.py`: `parse_review_feedback_header`
    returns `reviewer_model`, header-only (`parse_feedback_reviewer_model`).
  - `payload/scripts/workflow_state.py`: `POLICY_SATISFIED`,
    `resolve_policy_approval_basis`, `validate_policy_satisfied_confirmation`,
    `build_policy_evidence`, `build_policy_approval_record`,
    `assert_policy_still_satisfied`, `gate_satisfied_by_trailer`; the optional
    `reviewer_model`, `verdict_sha256` and `run_ref` ledger keys and their
    validators; `review_stage_audit`/`local_review_audit`; the D-GP-Ingest
    refusal (`assert_ingest_reviewer_model_admissible`) raised before any write.
  - `payload/scripts/workflow_protocol.py`: `record-external-result` carries
    the reporter's `--run-ref`.
  - `payload/.claude/commands/satisfy-gate.md` (new; `plan` and
    `implementation`); the pointer in `approve-review.md`; the
    `Reviewer model:` request in the reviewer, record-manual and author
    commands and in `REVIEW_PROTOCOL.md`; `ORCHESTRATION_PROTOCOL.md` and the
    operator reference section for `/satisfy-gate`.
  - Tests: `workflow_gate_policy_test.py` (CP2 classes, including the trust
    boundary, fabricated inputs, the toggle and master switch, and the plan
    commit trailers), `workflow_fingerprint_test.py`,
    `workflow_integration_test.py` (golden hashes, command count 19, roster).
- **Deferred inside the plan's ordering**: `acceptance` in `/satisfy-gate` is
  CP4's; the next-action rows are CP6's; the guide chapters are CP7's.
- **Note**: `workflow_integration_test.py` reads the git toplevel as the
  installed layout, so it is run in a fixture built from `payload/` (plus
  `CLAUDE.md` and `docs/ACTIVE_MILESTONE.md`), not in place.

## `CP3` — Functional evidence, GitHub-sourced pull-request facts and the stale-evidence table

Requirements: REQ-5 (functional flows and GitHub-sourced pull-request facts
ingested as identity-bound evidence; the Workflow owns every invalidation
rule), REQ-12 (the trust boundary for CI and pull-request facts, CP3's part).

- **Implementation** (release source only):
  - `payload/scripts/workflow_forge.py` (new, stdlib-only, `state_writer:
    false`): the one fixed `gh` argv (`gh_argv`, `--limit 200`),
    `FORGE_PR_LIST_LIMIT`, `resolve_gh` (the absolute path; refused inside the
    repository, any worktree, the temporary directory or a world-writable
    directory, by the resolved target; records `path` and `sha256`),
    `query_forge_pr_facts` (no shell, 30 s timeout, `origin` parsed and
    validated, `run` and `resolve` injectable), `parse_forge_raw` (the one
    parser both sources use; a full page and two open pull requests are
    `forge_undecidable`), and the stable-code errors.
  - `payload/scripts/workflow_gate_policy.py`: `gate_evidence` shape and
    validator (`gate_evidence_errors`), `identity_at`, `anchor_of`,
    `position_of` (equal, ahead, behind), `current_at_anchor`,
    `ingest_functional_evidence`, `ingest_pr_facts` (orchestrator report,
    `orchestrator_forge`, own slot), `store_workflow_pr_fact` (`workflow_gh`,
    `gh_path`/`gh_sha256`), the cause table (`cause_key`, `evidential_causes`),
    `pr_key_actionable`, `actionable_pr_keys`, `pr_query_trigger`,
    `INVALIDATION_RULES` and `apply_invalidation`.
  - `payload/scripts/workflow_state.py`: `InvalidGateEvidenceError` checked in
    `_validate_work_item`; the writers `record_functional_evidence`,
    `record_pr_fact` and `query_and_store_pr_fact`, each through
    `state_transaction`; `gate_evidence` added to the technical-approval and the
    two bundle-generation field sets.
  - Tests: `workflow_gate_policy_test.py` (CP3 classes: forge parser, `gh`
    resolution, the Workflow query, functional evidence, reported facts, cause
    table, position, invalidation table, query trigger, shape, commit
    contracts and cross-item residue); `workflow_forge.py` added to the
    harness, the generalization and the acceptance-matrix script lists.
- **Deviations and judgements**:
  - An empty `statusCheckRollup` reads `checks.state: pending` (fail closed:
    "no check has reported" never satisfies `ci_green`); a repository without
    CI sets `require_ci: false`.
  - When no pull request is open the newest merged or closed record stands
    (`gh pr list --search <sha>` also returns merged and closed ones).
  - The pure ingest functions live in `workflow_gate_policy.py` as the plan
    says and take `state`; the `state_transaction` wrappers are in
    `workflow_state.py` (the policy module never imports it at import time).
- **Deferred inside the plan's ordering**: `reopen_work_item`, the reopen at
  store time (`acceptance.satisfy`, `pr.apply_review`), `pr_keys.reopened_for`
  and `applied` writes, and every `38d`/`38f`-`38h` assertion of the plan's
  "single principle" cases are CP4's and CP5's; the `record-external-result`
  kinds (`functional_evidence`, `pr_review_result`) and their error codes are
  wired by CP6 (CP3 ships the library calls and tests, as the plan says). The
  predicates those rows call (`actionable_pr_keys`, `pr_query_trigger`,
  `pr_key_actionable`) are here and are tested directly.

## `CP4` — Automatic milestone acceptance

Requirements: REQ-6 (acceptance satisfied by evidence, audited, blocked when
evidence is missing, stale, behind a local fix or undecidable), REQ-12 (the
trust boundary at acceptance, CP4's part).

- **Implementation** (release source only):
  - `payload/scripts/workflow_gate_policy.py`: `evaluate_gate('acceptance')`
    (`_evaluate_acceptance`): `checkpoints_complete`,
    `technical_approval_current`, `functional_flows_passed`, `pr_fact_current`,
    `no_standing_pr_objection`, `ci_green`, `pr_approved`, each recomputed from
    the recorded heads (a stored identity is never read), plus `pending_query`,
    `satisfiable_after_query`, `obtainable` and `evidence`;
    `assert_acceptance_evidence_current` (the library predicate,
    `LPR-R2-005`), `requires_pr_approved`, `pr_approved_requirements`.
  - `payload/scripts/workflow_state.py`: the item's optional
    `acceptance_satisfaction` and its validator
    (`acceptance_satisfaction_errors`, checked in `_validate_work_item`),
    `build_acceptance_satisfaction`, `apply_acceptance_satisfaction` (sets the
    record in the same mutator as `complete_work_item`, so a refusal writes
    nothing), `satisfy_acceptance_gate` (the Workflow's own `gh` query, the
    evaluation and the completion in one `state_transaction`),
    `acceptance_satisfied_by_trailer`, and
    `assert_human_acceptance_pr_approved` (`/accept-milestone` step 2a).
  - Commands: `satisfy-gate.md` ("The acceptance stage", citing
    `/accept-milestone` steps by number; the floor is recorded after the
    satisfying commit, `LPR-R23-003`), `accept-milestone.md` (pointer, the
    `requires_pr_approved` pre-flight, step 5 pinned to copy, `LPR-R2-003`),
    `apply-functional-review.md` (cross-reference); golden hashes updated.
  - Tests: `workflow_gate_policy_test.py` (`TestEvaluateAcceptance`,
    `TestSatisfyAcceptance` including a remediation child accepted
    automatically with its parent then unblocked, `TestHumanAcceptancePrApproved`,
    `TestAcceptanceCommandText`).
- **Deviations and judgements**:
  - A stored `orchestrator_forge` fact never counts; with none and no
    `workflow_gh` fact the PR requirements are *pending the query*, and only the
    act (which queries GitHub itself) can satisfy them.
  - The floor-commit order is pinned by the command text (the satisfying
    commit, then the floor commit), as for plan and technical approval.
- **Verification**: `workflow_gate_policy_test` 247 tests OK;
  `workflow_state_test` 1011 tests with 2 errors and `workflow_integration_test`
  run in place with 12 failures, both identical at the CP3 head (the in-place
  layout); the integration suite run in a fixture built from `payload/` passes
  (267 tests, 1 skipped).
