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
