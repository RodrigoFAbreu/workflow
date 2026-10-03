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

## `CP5` — Reopening the same work item into remediation

Requirements: REQ-7 (a red or changes-requested pull request reopens the same
work item into remediation, with re-review and re-validation, and the item
completes again), REQ-12 (the trust boundary: a reopen reads only the
Workflow's own `workflow_gh` fact, and the `findings` text is data).

- **Implementation** (release source only):
  - `payload/scripts/workflow_state.py`: `reopen_work_item` (the only writer of
    an item's `reopenings`; legal from `AWAITING_FUNCTIONAL_REVIEW` and
    `MILESTONE_COMPLETE`; the refusals `reopen_phase_illegal`,
    `pr_fact_not_workflow_gh`, `pr_merged`, `pr_review_disabled`,
    `cause_not_actionable`, `key_consumed`, `already_reopened`,
    `incomplete_child`, `reopen_plan_archived`; it never touches
    `active_work_item_id`), `reopenings_errors` / `InvalidReopeningsError`
    (checked in `_validate_work_item`), `mark_pr_key_applied` (the one
    consumption write, idempotent), `reopen_for_stored_fact` (the store-time
    reopen, called by `satisfy_acceptance_gate` after it stores its
    `workflow_gh` fact; the human step-2a query and a reported fact never call
    it) and `begin_pr_review` (`/apply-pr-review`'s first step and the one reopen
    decision: the case (a) path without a query, and the query path with D-GP-Reopen's
    decision table, `pr_merged`, `pr_fact_superseded`, `pr_fact_refreshed`).
    `reopenings` joins the three commit field sets.
  - `payload/scripts/workflow_gate_policy.py`: `reopen_candidate`, the one
    selector the store-time reopen shares with the command.
  - `payload/.claude/commands/apply-pr-review.md` (new, `state_writer: true`,
    not user-only): the required id, the reopen first step, the branches of the
    cause table, the durable ordering of every branch that stales
    (`LPR-R4-001`), the data rule for `findings`. `accept-milestone.md` states
    what a re-acceptance does; `apply-functional-review.md` names
    `/apply-pr-review <child-id>` in the child sequence; the operator reference
    sections the new command (the roster tests require it).
  - Tests: `workflow_gate_policy_test.py` (`TestReopenWorkItem`,
    `TestBeginPrReview`, `TestStoreTimeReopen`, `TestReopenCommitContracts`,
    `TestReopenCommandText`); `workflow_integration_test.py` (command count 20,
    two golden hashes, the symbol allowlist).
- **Deviations and judgements**:
  - `reopen_work_item` takes a `repo_root` keyword the plan's signature omits:
    the plan-path check and the policy in effect need it.
  - The refusals of `begin_pr_review`'s decision table that the plan says store
    the fresh fact (`pr_merged`, `pr_fact_superseded`) are returned as results,
    not raised, so the transaction publishes the fact; the forge and head
    refusals raise and store nothing, as the plan says.
  - The "no code change" note is recorded in the ledger or
    `docs/ACTIVE_MILESTONE.md` by the command, not in a state field: the
    `gate_evidence` key set is closed.
- **Deferred inside the plan's ordering**: row `38d` and the protocol's
  `pr.apply_review` action are CP6's, so `next-action` does not yet emit this
  command; the `record-external-result` kinds are CP6's too. The guide chapter
  and the update simulation are CP7's.
- **Verification**: the release-source suites in a conformance fixture built
  from the working tree: `workflow_gate_policy_test` 278 OK,
  `workflow_integration_test` 267 OK (1 skipped), `workflow_protocol_test` 217
  OK, `workflow_fingerprint_test` 257 OK, `workflow_acceptance_matrix_test` 291
  OK (18 skipped), `workflow_state_completion_obligations_test` 106 OK,
  `workflow_fingerprint_generalization_test` 105 OK,
  `workflow_test_harness_test` 22 OK; `workflow_state_test` 1011 run with the
  two in-place-layout errors the CP4 head also has (the live state file is not
  in the fixture) after the phase-writer census gained `reopen_work_item`;
  `workflow_state_demo_test` and `workflow_fingerprint_demo_test` fail with
  exactly the same tests as the CP4 head (they need the real repository
  layout). `tools/release/release_test.py` was not re-run: nothing under
  `tools/` changed.

## `CP6` — Protocol 1.1: rows, actions, `validation`, schema, human equivalence

Requirements: REQ-3 (human equivalence: with every gate human, behavior equals
2.7.0's apart from the listed deltas), REQ-5 (functional flows and
GitHub-sourced pull-request facts ingested as identity-bound evidence; the
Workflow owns every invalidation rule and the next legal action), REQ-8
(protocol 1.1: additive rows, actions and kinds, `validation` emitted, schema,
`describe`, unaware consumers fail closed or stall).

- **Implementation** (release source only):
  - `payload/scripts/workflow_protocol.py`: `PROTOCOL_VERSION` `1.1`,
    `WORKFLOW_RELEASE` `2.8.0`; the role `validator` and the six new actions
    (`plan.satisfy`, `implementation.satisfy`, `acceptance.satisfy` as
    `validation`, `pr.apply_review`, and the external gates
    `functional.evidence.external` and `pr.review.external`); rows `14a`/`14b`,
    `28a`/`28b` and `38d` to `38i` with their `CONDITION_CALLS` (every call
    goes through `ctx.call`), `EDGES` for the four new automatic/validation
    actions (a forward and an unchanged edge each; `pr.apply_review` also
    `MILESTONE_COMPLETE` to `AWAITING_FUNCTIONAL_REVIEW` and its unchanged
    edge), the optional `policy` object (`{source, digest, gate, mode}` plus
    `gate_lowering`) on the new rows only, `reconcile` accepting a `validation`
    decision (row and disposition must agree), and `record-external-result`
    for `functional_evidence` and `pr_review_result` (delegating to
    `record_functional_evidence` / `record_pr_fact`; `RESERVED_RESULT_KINDS`
    is now empty). `workflow_forge` joins the Workflow exception domain, so a
    forge refusal is `refused`, never `internal_error`. `verify`'s advisory
    `gate_policy` check was already CP1's.
  - `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`: the new
    action ids and role, the `satisfied_by` values, the decision's `policy`,
    the `forge` block and `$defs.inputs` for the two evidence kinds, and the
    `record-external-result` result widened (`stage` gains `functional` and
    `pr_review`; only `stage` and `basis` are required).
  - `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`: the mirrored tables
    (actions, conditions, catalogue, edges, proofs) and the passages the
    tests tie to the code (version, roles, kinds, section 9). The prose
    chapters, the edge-class definitions and the operator guide remain CP7's.
  - Tests (`workflow_protocol_test.py`): `TestAllHumanEquivalence` (INV-1,
    below), `TestPlanAndTechnicalGateRows`, `TestAcceptanceRows`,
    `TestTriggerAndRemedyRuns`, `TestNewActionEdgesAndReconcile`,
    `TestUnawareConsumer`, `TestEvidenceResultKinds`,
    `TestProtocolSchemaAndDescribe`; the existing tests are re-pointed at the
    1.1 vocabulary (row order, version, kinds) and gain guards for the new
    actions.
- **The all-human equivalence matrix.** Every scenario builder the file
  already has (each phase at each governing version, each automatic row, the
  functional rows, the plan-review phases) is built as a real repository under
  the harness's committed all-human `GATE_POLICY.json` (the unadopted-file
  configuration). `next-action` is compared **byte for byte** with the 2.7.0
  module's, apart from the two envelope fields of delta 1; `describe`,
  `verify` (no file, unadopted file and invalid file; the advisory check is
  the only addition and `healthy` is 2.7.0's) and `record-external-result`
  (the result, the state bytes and the feedback bytes of both stages, with no
  `Reviewer model:` line and no ledger key) are compared the same way. Under
  the default configuration only the gate rows (15, 29, 39) are replaced by
  new rows; the `policy` object appears nowhere else.
- **Deviations and judgements**:
  - **The golden outputs are produced live from the immutable tag `v2.7.0`,
    not stored.** The 2.7.0 modules are read with `git show v2.7.0:...` into a
    scratch directory and run as a subprocess. Stored outputs would embed
    commit SHAs, state identities and temp paths that change on every run;
    the tag is immutable by the repository's own rule (CLAUDE.md). The class
    skips, naming the reason, when the tag is not in the checkout (an
    installation holds no release-source history).
  - **The adopted all-human fixture compares 2.8.0 before and after the
    adoption**, at the phases that have no bundle for the adoption commit to
    stale (D-GP-Compat delta 7: 2.7.0 refuses the adoption fields, so it
    cannot be the reference there).
  - **Row conditions beyond the plan's text.** `38e` to `38g` match only when
    the registry is complete and the technical approval is current (and, for
    `38f`/`38g`, the flows pass), so a stale approval or a failed flow is
    `38i` (blocked), never an external gate that cannot help; `38g` for an
    automatic gate also requires a pull-request fact to be obtainable (an
    objection is `38i`). `38d`'s `policy.gate` is `pr_review` with mode
    `automatic` (the row has no gate-mode condition and matches only while
    `pr_review.enabled`).
  - `reconcile`'s error text for a non-automatic decision now says "automatic
    or validation".
  - The spec's mirrored tables are CP6's, not CP7's, because the
    spec-equals-code tests would otherwise fail at this checkpoint.
  - `WORKFLOW_RELEASE` is `2.8.0` while `manifest.json` still says `2.7.0`: the
    release build's constant guard refuses until CP8 bumps the manifest, which
    is that guard's purpose.
- **Not done here (stated, not omitted)**: the two-concurrent-2.2-items
  all-human fixture and the legacy-declared in-flight item are CP1's and
  CP7's (the update simulation); the `14b`/`28b` withdrawal is run end to end
  at the plan stage only (the implementation analogue shares the same
  predicates, and its toggle and adoption halves are run); the commands
  themselves are model-run prose, so the end-to-end remedy runs call the same
  library functions the commands name.
- **Verification**: the release-source suites in a conformance fixture built
  from the working tree (`payload/` synced over the CP5 fixture):
  `workflow_gate_policy_test` 278 OK, `workflow_integration_test` 267 OK (1
  skipped), `workflow_fingerprint_test` 257 OK, `workflow_acceptance_matrix_test`
  291 OK (18 skipped), `workflow_state_completion_obligations_test` 106 OK,
  `workflow_fingerprint_generalization_test` 105 OK,
  `workflow_test_harness_test` 22 OK; `workflow_state_test` 1011 run with the
  two in-place-layout errors CP4 and CP5 also have. `workflow_protocol_test`
  275 OK, run from `payload/scripts` against the checkout (the equivalence
  class needs the `v2.7.0` tag; it ran, none skipped). The two `*_demo_test`
  suites and `tools/release/release_test.py` were not re-run: nothing they
  cover changed.

## `CP7` — Specification, operator guide, update simulation, lifecycle end to end

Requirements: REQ-3 (update to 2.8.0 stated and simulated for the default and
the all-human configuration), REQ-8 (CP7 part), REQ-9 (specification, operator
guide, lifecycle end-to-end tests, documentation sweeps), REQ-12 (CP7 part).

- **Implementation** (release source only):
  - `payload/docs/ai-workflow/GATE_POLICY.md` (new): toggles, safety rule and
    floor, evidence, `requires_pr_approved` order, the way back to human gates,
    both reopening residuals with the query-path table, trust boundary, the
    named threat-model section (guaranteed, not guaranteed, safeguards;
    gate-lowering event), `provenance_failed`, the single-subscription paths,
    families, the `gh` resolution rule.
  - `ORCHESTRATION_PROTOCOL.md`: section 7 (classes of the new actions in the
    classifier's terms; the completion passage amended), section 8 (`validation`
    in obligation 5; new obligation 10, the `no_progress` bound), section 10
    (1.1 compatibility notes), new section 11 (gate policy and reopening, trust
    boundary). `MILESTONE_WORKFLOW.md`, the operator reference and
    `REVIEW_PROTOCOL.md` point at the guide.
  - `workflow_integration_test.py`: `TestGatePolicyDocuments` (8 tests, incl.
    both installed documentation sweeps). `workflow_protocol_test.py`:
    `TestUpdateSimulation27To28`, `TestUpdateSimulationLegacyDeclaration`,
    `TestUpdateSimulationInFlightDefault`, `TestAutomaticLifecycle`,
    `TestMixedLifecycle`, `TestAllHumanLifecycle` (23 tests).
- **Deviations and judgements** (the code is authoritative):
  - After CI turns green and a fresh `pr_review_result` is reported,
    `next-action` emits `38d` (the Workflow's own query, `pr_fact_refreshed`),
    then `38h` re-queries and completes; the plan's text said `38h` directly.
  - **Downgrade posture is narrower than the plan's text.** The immutable
    v2.7.0 refuses only the basis `POLICY_SATISFIED`; it accepts
    `gate_evidence`, `reopenings`, `acceptance_satisfaction`, the ledger audit
    keys and the top-level adoption and floor. The protocol's compatibility
    note says so; a test pins the observed behaviour.
  - With a legacy declaration the installed `GATE_POLICY.md` is itself
    unclassified; the same declaration remedies clear it (noted in section 10).
  - An uncommitted toggle file is seen by the plan-stage classifier only; the
    implementation-stage classifier reads `HEAD`. The committed case raises in
    both.
  - The gate-policy section of the protocol is section 11, appended, to avoid
    renumbering.
  - The update simulation is a model of `workflow-manager update` (it re-copies
    the scripts and adds a stand-in guide); `.claude/commands/*` is not copied.
- **Verification** (conformance fixture from the working tree, `payload/`
  synced over the CP6 fixture): `workflow_integration_test` 275 OK (1 skipped),
  `workflow_gate_policy_test` 278 OK, `workflow_fingerprint_test` 257 OK,
  `workflow_acceptance_matrix_test` 291 OK (18 skipped),
  `workflow_state_completion_obligations_test` 106 OK,
  `workflow_fingerprint_generalization_test` 105 OK,
  `workflow_test_harness_test` 22 OK; `workflow_protocol_test` 298 OK, run from
  `payload/scripts`. `workflow_state_test`, the demo suites and
  `tools/release/release_test.py` were not re-run: nothing they cover changed.

## `CP8` — Release 2.8.0

Requirements: REQ-10 (2.8.0 releasable: manifest, conformance CI for the new
suite, release-constant guard), REQ-11 (roadmap: W2 complete pending cutover).

- **Implementation** (release source and repository tooling only):
  - `manifest.json`: `workflow_version` `2.8.0`; seven new entries
    (`adopt-gate-policy.md`, `apply-pr-review.md`, `satisfy-gate.md`,
    `GATE_POLICY.md`, `workflow_forge.py`, `workflow_gate_policy.py` as
    `distribution`; `workflow_gate_policy_test.py` as `conformance`); 28
    refreshed `sha256`/`size` pairs, each rationale naming W2; `counts` now 74
    artifacts (48 distribution, 24 conformance, 2 host-evidence); the
    conformance template's digest and derivation.
  - `templates/.github/workflows/workflow-conformance.yml` and
    `.github/workflows/workflow-ci.yml`: a ninth step, `workflow_gate_policy_test.py`;
    `docs/RELEASING.md` says nine suites.
  - `docs/ROADMAP.md`: W2 row complete pending cutover, a "Workflow 2.8.0"
    entry, both roadmap sections marked delivered. `RoadmapTest` in
    `tools/release/release_test.py` updated to match.
- **Deviations and judgements:**
  - The repository's own installation (`.github/workflows/workflow-conformance.yml`
    included) stays at 2.6.0 and was not edited; it reaches 2.8.0 only through
    `workflow-manager update` after publication.
  - The release workflow is run under Python 3.12 (the pinned zlib-ng wheel);
    the local default interpreter is 3.14, so verification used a 3.12 venv.
- **Verification** (temporary commit of the CP8 tree, conformance fixture staged
  from it): `release.py build` reports 2.8.0 and accepts `WORKFLOW_RELEASE`;
  `check-title ... --agree` and `check-pending` report `2.7.0 -> 2.8.0 (minor)`;
  all nine suites green (fingerprint 257, state OK, harness 22, integration 275,
  acceptance matrix 291, completion obligations 106, generalization 105,
  protocol 298, gate policy 278); `workflow-manager verify .` reports the
  installation matches 2.6.0.

## Self-review (`SELF_REVIEWING_IMPLEMENTATION`, 2026-10-03)

Review of the full milestone diff (`d14e0a7..`, CP1-CP8): the new modules
(`workflow_forge.py`, `workflow_gate_policy.py`), the `workflow_state.py`
writers (adoption, floor, evidence, acceptance, reopen, `begin_pr_review`),
the new and changed commands against the functions they name (every
`workflow_state.`/`gate_policy.`/`workflow_forge.` reference resolves), and
the release constants (`WORKFLOW_RELEASE` 2.8.0, `PROTOCOL_VERSION` 1.1, the
manifest's `workflow_version`).

- **Fixed (important), `workflow_forge._derive`:** `reviewed_head` and
  `review_id` came from the latest review of any kind. A `COMMENTED` review
  on the current head after an `APPROVED` review of an earlier head made the
  stale approval read as current (defeating "a decision on an earlier head is
  outdated and reads as `REVIEW_REQUIRED`"), and any later review (a comment,
  another reviewer's approval) changed the `changes_requested` key's
  `review_id`, so one changes request could reopen the item a second time and
  `review_id` disagreed with `findings` (already the latest
  `CHANGES_REQUESTED` review's text). Both now come from the latest review
  whose state is the decision (`APPROVED` or `CHANGES_REQUESTED`), falling
  back to the latest review when there is none. This is a reading of the
  plan's "come from the latest review" consistent with D-GP-Invalidation's
  rule that a decision applies only when `reviewed_head` equals `head`, and
  with `findings`. Two tests in `TestForgeParser`; the manifest's `sha256`
  and `size` for `workflow_forge.py` and `workflow_gate_policy_test.py`
  refreshed.
- **Fixed (narrative), `docs/ACTIVE_MILESTONE.md`:** the W2 goal still said
  acceptance stays human and the default equals today's gates (superseded by
  the user's 2026-10-03 decision in plan section 1), and W1's records sat
  under W2's headings; W1's are now under their own "Previous milestone
  record" heading.
- **Observed, not changed (plan-level, for the reviewers):** a
  `statusCheckRollup` entry with `status: COMPLETED` and an empty conclusion
  counts as passed (GitHub always sets a conclusion on completion); the
  `pr_fact` writers (`store_workflow_pr_fact`, `ingest_pr_facts`) do not bump
  the item's `state_revision`, as the plan's residue design admits.
