# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W10: `finding-dispositions` (`process`, governing version `2.2`), branch
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

#### Optional review findings: dispositions

23 distinct Optional findings across the 13 review rounds (local and external, plan and implementation); a re-raise is one row.

**Fixed in this milestone:**

| Finding | Raised by | Fix |
|---|---|---|
| D-Gate said "commit it" while the text said a saved file is enough | local plan, round 1 | plan revision 2; the refusal says "save the file" |
| The plan misdescribed 2.13.0's `verify` warnings for #37 | local plan, round 1 | plan revision 2 |
| "Re-adopt on this line" cannot happen on a protected `main` | local plan, round 1 | plan revision 2: a branch merged with a squash |
| D-Coverage would read `/`, `~` and `..` spans | local plan, round 1 | plan revision 2 (exception iii in revision 5) |
| INV-5 exempted published plans, not only bound ones | local plan, round 1 | plan revision 2 |
| A `path:line` span read as a path | local plan, round 2; Codex plan round 1 (I4) | plan revision 3, CP4: annotations stripped first |
| Heading mode dropped list items before the first heading | local plan, round 2; Codex plan round 1 (I3) | plan revision 3, CP1 |
| Label stripping merged `CP1:`/`CP2:` findings | local plan, round 2; Codex plan round 1 (I2) | plan revisions 3 and 5, CP1: identity is the whole entry |
| A stale state-growth figure | local plan, round 3 | plan revision 4 |
| Limit (b)'s tie-break exception | local plan, rounds 3 and 4 | plan revision 4, superseded by revision 5 |
| The plan header named a stale revision | local plan, round 4; Codex plan round 2 | plan revision 5 |
| The non-path exception set was open-ended (`…`, "URL") | local plan, round 5 | CP4 code: a closed character set and a URL pattern |
| The bare-name note in the refusal | local plan, round 5 | CP4 code: the next step says to write every path in full from the repository root |
| CP2's Files paragraph named an unchanged test file | local implementation, round 1 | recorded in the implementation summary (the tests are in `workflow_state_test.py`) |
| The bundle's test results named revision 1 | local implementation, round 2 | `TEST_RESULTS.md` has a revision 3 section |

**Dropped, with the reason:**
- The declaration left four user pages unclassified (local plan, round 2): no checkpoint touched them, so nothing was ever refused; CP4's check covers it for later plans.
- "Pre-flight and step 5" should say step 5a (local plan, round 2), "limits a-d" should say a-e (local plan, rounds 4 and 5), a stale line citation (local plan, rounds 4 and 5), and R1's "keyed by content" wording (local plan, round 5): plan text only. The approved plan is frozen; the shipped command and code text are correct.
- The plan's D-Parse still states the old ordinal encoding (local implementation, round 3): the implementation's newline-and-`@n` key is the external round-1 fix, and the implementation summary declares the deviation.

**Deferred:** 2 follow-ups in issue #45 (`review-follow-up`): the acceptance refusal prints the whole stored entry instead of its first line cut to 240 characters; the two-item D-Downgrade diff test uses a weak `assertNotIn`.

## Next action

Row 12 (Controller C10, in the Controller's repository) is next once the owner schedules it. Publishing 2.14.0 follows the pull request merge; the Manager side is a `workflow-manager` pin pull request.

## Functional review checklist

Reviewed content: branch `milestone/finding-dispositions`, implementation revision 3,
Workflow 2.14.0 release source (`payload/`, `manifest.json`). This repository's own
installation is 2.13.0 and is never edited, so every flow below runs against the release
source in a scratch copy, never in this working tree.

### Setup

1. `git worktree add /tmp/fd-review HEAD` (or `cp -r` the repository to a scratch
   directory); work only there.
2. Stage a conformance fixture as the suites do: copy `payload/` over a scratch git
   repository with `manifest.json` digests refreshed in the scratch copy only.
   Alternatively run each suite from `payload/scripts/` in the scratch copy.
3. No feature flags. Python 3 and git only.

### Test data

- A scratch git repository with a two-stage (`2.2`) work item at the implementation
  stage, and a verdict text whose `## Optional findings` section holds three top-level
  entries (one labelled `O1:`, one unlabelled, one re-raised later with only a whitespace
  change), plus a `BLOCK` verdict with findings.
- A scratch `GATE_POLICY.json` adoption, once merged with `git merge --no-ff` and once
  with `git merge --squash`.
- A plan whose `**Files:**` paragraph names a path (e.g. `tools/x.py`) that its artifact
  declaration does not classify, and a copy whose declaration classifies it.

### Flows and expected results

| # | Flow | Expected |
|---|---|---|
| 1 | Record an `APPROVE` verdict with three Optional findings through `record_local_implementation_review(..., verdict_text=...)` (or `ingest_manual_review_verdict`) | The item gains `optional_findings` with three `F-<12 hex>` keys; the stage ledger, phase and `review_content_id` are as without findings |
| 2 | Record a `REVISE` verdict with Optional findings; then a `BLOCK`; then an `APPROVE` call with no `verdict_text` | `REVISE` records them; `BLOCK` and the no-text call record nothing |
| 3 | Re-raise a finding in a later round with whitespace-only changes, then with one word changed | Whitespace-only: one entry, two references. Word changed: a new key |
| 4 | `python3 scripts/workflow_state.py --finding-dispositions <id>` | Lists every finding with its key and prints a skeleton for `registry/<id>-dispositions.json` |
| 5 | Run `/accept-milestone` logic (`complete_work_item`) with no dispositions file | Refused with `UndispositionedFindingsError` naming every undispositioned key; nothing written. `/satisfy-gate acceptance` refuses the same way and writes nothing |
| 6 | Add dispositions: one `fixed`, one `dropped` with a reason, one `follow-up` with a link; try `dropped` without a reason and `follow-up` without a link | The malformed ones are refused with `InvalidFindingDispositionsError`; the valid set lets acceptance proceed, a follow-up never blocks it |
| 7 | After acceptance, open `docs/milestones/completed/<id>-findings.md` | Lists each finding with its disposition; generated, not hand-written |
| 8 | An item with no Optional findings | Acceptance behaves as in 2.13.0; no findings record is demanded |
| 9 | Adoption merged with `git merge --no-ff` into the line, then `verify` | `verify` warns with `adoption_merge_notice` naming the merge commit and the squash fix, only while the effective policy is stricter than the adopted one |
| 10 | Same adoption merged with `--squash` | No notice; effective policy as in 2.13.0 |
| 11 | `gate_policy_adoption_preview` / `adopt-gate-policy.md` step 1 and 3 | The notice and the squash advice appear in the preview and the command text |
| 12 | Publish or bind the plan whose declaration leaves `tools/x.py` unclassified (`milestone-plan.md` step 5 and 6; `prepare-ai-review.sh`) | Refused before any publication write with `PlanArtifactDeclarationCoverageError` and one next step (`PLAN_DECLARATION_NEXT_STEP`) |
| 13 | Same plan with the declaration classifying the path | Accepted; a checkpoint with no `**Files:**` paragraph gets only an advisory |
| 14 | Backticked non-paths in a Files paragraph: a glob, a URL, `/abs`, `~/x`, `../x`, a version string, an identifier | Ignored or refused with the second remedy exactly as D-Coverage states; `Dockerfile`, `Makefile`, `.env` count as paths |
| 15 | A plan already `BOUND` at a ready phase | Keeps working (INV-5); a new revision is checked |
| 16 | Release bookkeeping: `manifest.json` names 2.14.0, digests match, `WORKFLOW_RELEASE` is `2.14.0`, protocol is still 1.4; run `tools/docs/check_docs.py` and `tools/release` tests | Clean, except `ReproductionTest.test_round_trip` which is re-run after the CP5 commit |
| 17 | `workflow-manager verify .` in this repository | Clean: the installation is untouched |

### Known limitations and out of scope

- "fixed" is a recorded claim, never verified.
- Recording covers two-stage review verdicts only: not feedback-only items, not the
  functional review, not verdicts ingested before 2.14.0.
- Recognition is the reviewer's text read by D-Parse: a finding outside `## Optional
  findings` is not recorded; any non-whitespace change in a re-raise is a new key.
- The adoption-merge notice is an aid; the gate-policy evaluation is unchanged (INV-4).
- workflow#30 part 2, #31, #39, acceptance-matrix sharding and the Controller's work
  are not in this release.
- The three tests that read `CLAUDE.md`/`ACTIVE_MILESTONE.md` fail in a scratch copy
  that lacks them; that is the copy, not the release.
