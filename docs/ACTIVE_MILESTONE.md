# Active Milestone

## Milestone

W10: `finding-dispositions` (`process`, governing version `2.2`), branch
`milestone/finding-dispositions`, base `f8eea78` (main after #42: the release
source is Workflow 2.13.0 and this repository's own installation is the
published 2.13.0). Roadmap row 11. The plan is
`docs/ai-workflow/FINDING_DISPOSITIONS_PLAN.md`, approved by gate policy at
plan revision 5. The previous milestone, W9 (`review-loop-fixes`, Workflow
2.13.0), is complete.

## Goal

Workflow 2.14.0, a minor release (`feat:`), in five checkpoints:

1. **CP1, CP2** every Optional finding of every recorded verdict is kept in the
   item's state (workflow#34); acceptance refuses while one has no disposition
   (`fixed`, `dropped` with a reason, or a `follow-up` with a link), and the
   dispositions go into the completed-milestone record.
2. **CP3** `verify` and `/adopt-gate-policy` name the cause of a gate-policy
   adoption merged with a merge commit (workflow#37).
3. **CP4** a plan whose artifact declaration leaves a path named in a Files
   paragraph unclassified is refused before review (workflow#40).
4. **CP5** release 2.14.0 bookkeeping. The Orchestration Protocol stays 1.4.

## Current checkpoint

CP1 is complete: `workflow_fingerprint.parse_optional_findings` reads the
`## Optional findings` section (top-level entries only; identity is the whole
entry as written, label included, whitespace collapsed; the key is `F-` plus 12
hex characters of its sha256). `workflow_state.merge_optional_findings` and the
new `verdict_text` keyword on `record_local_plan_review`,
`record_manual_plan_review`, `record_local_implementation_review` and
`record_manual_implementation_review` record an `APPROVE` or `REVISE` verdict's
findings into the work item's `optional_findings` in the verdict's own
transaction (a `BLOCK`, or a call without `verdict_text`, records nothing);
`ingest_manual_review_verdict` passes the text, `/review-plan` and
`/review-implementation` say to. `validate_state` checks the key's shape
(`InvalidOptionalFindingsError`). `optional_findings` is admitted by the four
closed commit-field sets (`REVIEW_STAGE_WRITE_COMMIT_FIELDS`,
`TECHNICAL_APPROVAL_COMMIT_FIELDS`, `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS`,
`RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS`). Audit of the file's other closed
field sets (`LEGACY_RETIREMENT_FIELDS`, `RESUME_IMPLEMENTATION_FIELDS`,
`_ACCEPTANCE_SATISFACTION_FIELDS`, `_ACCEPTANCE_INPUT_FIELDS`, `_REOPENING_FIELDS`):
none concerns a verdict's write; unchanged. `REVIEW_PROTOCOL.md` carries the
"Optional findings are recorded" paragraph and the declared limits.

CP2 is complete: `workflow_state.read_finding_dispositions`,
`finding_dispositions_report`, `assert_finding_dispositions_recorded`
(`UndispositionedFindingsError`, `InvalidFindingDispositionsError`),
`render_finding_dispositions` and `write_finding_dispositions_record` keep the
dispositions in `docs/ai-workflow/registry/<id>-dispositions.json`; `complete_work_item`
calls the check after the completion-obligation check, so `/accept-milestone` and
`/satisfy-gate acceptance` both refuse (the second writes nothing). The
completed-milestone record is `docs/milestones/completed/<id>-findings.md`, written by
the new step 5a of `accept-milestone.md` (a remediation child runs it too; step 2b is
edited). `python3 scripts/workflow_state.py --finding-dispositions <id>` lists the
findings and prints a skeleton; it is a required mutually exclusive pair with
`--plan-review-publication-status`. `MILESTONE_WORKFLOW.md` and `GATE_POLICY.md` state
the exit condition and that it is not a policy requirement. Golden hash of
`accept-milestone.md` refreshed. Tests: `TestFindingDispositions` in
`workflow_gate_policy_test.py`, `TestFindingDispositionsCommandConformance` in
`workflow_integration_test.py`.

CP3 is complete: `workflow_gate_policy.adoption_merge_cause` names the adoption that
reached the line through a merge commit that does not introduce it (`{commit, sha256,
parents}`, else `None`); `effective_policy` carries it as `adoption_merge` and no
evaluation reads it. `verify_check` warns with `adoption_merge_notice` only when the
effective policy is stricter than the adopted one. `gate_policy_adoption_preview`
carries `adoption_merge` and `adoption_merge_notice`; `adopt-gate-policy.md` prints the
notice in step 1 and repeats the squash advice in step 3; `GATE_POLICY.md` states the
squash requirement. `adopt-gate-policy.md` has no golden hash, so none changed. Tests:
`TestAdoptionMergeCause` in `workflow_gate_policy_test.py` (merge commit, squash,
update merge, no-cause cases, preview and command text). Run in a scratch git copy of
`payload/`: the gate-policy suite (310), state suite (331) and the integration suite
pass apart from three tests that read `CLAUDE.md`/`ACTIVE_MILESTONE.md` the scratch
copy lacks.

CP4 is complete: `workflow_state.plan_named_paths` reads each checkpoint's Files
paragraph (every backtick span is a path, line annotations stripped, apart from spans
with whitespace or glob/placeholder characters, URLs, `/`, `~` or `..` starts and
version strings); `assert_plan_artifact_declaration_coverage` refuses a path left
unclassified at the plan stage, the implementation stage or both
(`PlanArtifactDeclarationCoverageError`, in `_PLAN_EARLY_CHECK_ERRORS`, with
`PLAN_DECLARATION_NEXT_STEP`); `plan_files_advisory` warns for a checkpoint naming no
file. `prepare-ai-review.sh`, `milestone-plan.md` (publication and bind),
`apply-plan-review.md` (publication and bind), `review-plan.md` and
`PLAN_REVIEW_WORKFLOW.md` carry it; three golden command-file hashes refreshed. Tests:
`TestPlanNamedPaths` and `TestAssertPlanArtifactDeclarationCoverage` in
`workflow_state_test.py`, the generator cases in
`workflow_fingerprint_generalization_test.py`, `TestDeclarationCoverageEarlyCommandConformance`
in `workflow_integration_test.py`. This item's own plan passes the check. Run in a
scratch fixture staged from the working tree (digests refreshed in the scratch
manifest only): all nine payload suites pass; `tools/release` tests pass except
`ReproductionTest.test_round_trip`, which verifies the committed manifest whose digests
CP5 refreshes.

CP5 is complete: release 2.14.0. `manifest.json` names 2.14.0 with every changed digest
and size refreshed (23 records, rationale text extended; counts unchanged) and the
`manager` block: `min_manager_version` `1.13.0`, D-Downgrade's posture with the
`optional-findings-ledger` `state-key` signal, one `new_work_only` entry, an empty
`gate_default_change`, and `conformance.suites` written by `release.py manager-block
--release-dir <scratch staging> --write` (state 1167, protocol 331, gate policy 310,
generalization 142, integration 317, fingerprint 279, others unchanged).
`WORKFLOW_RELEASE` is `2.14.0` (protocol stays 1.4; tested-releases list, envelope example
and compatibility note updated). `docs/release-history.md` has the 2.14.0 row;
`docs/common-problems.md`, `docs/gates.md` and `docs/glossary.md` carry the three
problems, the acceptance disposition requirement and "Disposition".
`tools/release/manager-releases.json` re-recorded (adds Manager 1.13.1). Verified from a
conformance fixture staged from the working tree: all nine payload suites pass;
`tools/docs/check_docs.py` and its tests are clean; `tools/release` tests pass except
`ReproductionTest.test_round_trip`, which stages the previous commit's manifest and is
re-run after the CP5 commit. `docs/ROADMAP.md` is marked Done at acceptance.
