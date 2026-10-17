# Active Milestone

## Milestone

**In implementation (CP1 to CP5 complete).** W9: `review-loop-fixes` (`process`, governing version `2.2`),
branch `milestone/review-loop-fixes`, base `d911915` (main after #36: the
release source and this repository's own installation are both Workflow
2.12.0, with automatic gates, default "2.2" and no `GATE_POLICY.json`).
Requested by the Manager Super Orchestrator; roadmap row 10, placed by the
owner before item C. The plan is `docs/ai-workflow/REVIEW_LOOP_FIXES_PLAN.md`.
The previous milestone, W8 (`review-convergence`, Workflow 2.12.0), is complete.

## Goal

Workflow 2.13.0, a minor release (`feat:`), in five checkpoints:

1. **CP1** the real-process test's ready file is written atomically
   (workflow#32), and the governing-version sweep runs when a plan revision is
   published, bound or turned into a bundle (workflow#30, part 1).
2. **CP2, CP3** `CHANGES_SINCE_REVIEW.md` holds one section per review stage:
   the manual external stage compares against the content it last reviewed and
   quotes its own last verdict, through a gitignored baseline record
   (workflow#35). The local stage is unchanged. Nothing new is persisted in state.
3. **CP4** the producer side of the Manager's release metadata: the `manager`
   block of `manifest.json` (authored fields, computed suite counts) and its CI
   check.
4. **CP5** release 2.13.0 bookkeeping. The Orchestration Protocol stays 1.4.

## Current checkpoint

CP1 is complete: the real-process test's holder publishes its ready file
through `publish_atomically` (workflow#32), and
`workflow_state.assert_plan_governing_version_sweep` runs right after the
anchor check at the four command steps and in `prepare-ai-review.sh`
(workflow#30, part 1). Verified from a scratch release staged from the
checkpoint's tree: the nine payload suites.

CP2 is complete: `workflow_fingerprint.record_stage_baseline` /
`read_stage_baseline` / `remove_stage_baseline` keep a gitignored baseline per
manual review role under `.ai-review/<id>/review-baselines/<ROLE>/`, written by
`ingest_manual_review_verdict` inside its state transaction for a `REVISE` or
`APPROVE` and replaced wholesale by the next one; the reader proves a record
consistent or returns `None` (full review). `REVIEW_PROTOCOL.md` describes the
directory, its trust boundary and its limits. Verified from a scratch release
staged from the checkpoint's tree: the nine payload suites.

CP3 is complete: `CHANGES_SINCE_REVIEW.md` holds one section per review stage
(`## LOCAL_MODEL_*_REVIEW`, `## MANUAL_EXTERNAL_*_REVIEW`). The local section is the
2.12.0 content; the manual section compares against the stage baseline and quotes
that stage's own last verdict, or says `not available (<reason>): review the whole
bundle.`; each section is built and fails on its own, and the file is deleted when
neither has a basis. The seven commands that word the changes file name the section
for the reviewer's role; the protocol and the two stage workflow documents describe
the layout. Verified from a scratch release staged from the checkpoint's tree: the
nine payload suites.

CP4 is complete: the Manager metadata block's tooling. `tools/release/manager_block.py`
(`validate`, `measure_suites`, `check`, `check_pin`, `replace_suites`) and
`release.py manager-block` (`--commit` or `--release-dir`, `--write` replaces only
`suites`), `check-manager-block` (checks (a), (b), (c), (e), (g) against the committed
`tools/release/manager-releases.json`, recorded from Manager 1.13.0's publication),
`record-manager-releases`, `compare-manager-releases` and `update-fixture` (verified
once against the real Manager 1.13.0, v2.11.0 to 2.12.0). Three new steps in
`workflow-ci.yml`; `docs/RELEASING.md` documents the authored and computed fields.
The counting method equals each suite's own `Ran N tests` on 2.12.0 (415, 330, 1115,
292, 125, 106, 300, 269, 27). `manager-pin.json` is advanced in CP5. Verified: the
nine payload suites from a scratch release staged from the checkpoint's tree, the
tools tests (all but `test_round_trip`, which needs CP5's refreshed digests), and
`tools/docs/`.

CP5 is complete: release 2.13.0 bookkeeping. `manifest.json` names 2.13.0 with every
digest and size refreshed, the rationale of each changed record extended, and the
authored `manager` block (minimum Manager 1.13.0, empty downgrade posture, one
`new_work_only` note); `conformance.suites` was written by `release.py manager-block
--release-dir` from the working tree staged with refreshed digests (415, 330, 1133, 292,
140, 106, 307, 269, 27), never by hand. `WORKFLOW_RELEASE` is 2.13.0 and the protocol stays
1.4 (tested-releases note, envelope example, compatibility note); `manager-pin.json`
advances to Manager 1.13.0; `docs/release-history.md` has the 2.13.0 row with the
downward-move paragraph and `docs/common-problems.md` the governing-version refusal.
All five checkpoints are complete.

## Next action

Self-review, the full verification and the implementation review bundle (every
checkpoint is complete).
Publishing 2.13.0 follows the pull request merge; the Manager side is a
`chore: test Workflow 2.13.0` lock bump in `workflow-manager`. The Manager
release 1.13.0 must be published before this pull request merges (CP4's CI check).

## Functional review checklist

Item `review-loop-fixes` (process, Workflow 2.13.0), implementation revision 4.
Findings go to `.ai-review/review-loop-fixes/feedback/FUNCTIONAL_REVIEW.md`.

### Setup

- On branch `milestone/review-loop-fixes`, clean tree. Python 3 only; no feature
  flags and no external data. Run commands from the repository root.
- Stage a scratch release from the working tree (never edit this repository's own
  installation by hand) and keep it outside the repository.

### Test data

- A scratch git repository with a `2.2` work item that has a plan bundle and one
  manual external plan review already ingested (`REVISE`), then a revised plan.
- `tools/release/manager-releases.json` as committed (Manager 1.13.0 record).

### Flows

1. **Atomic ready file (CP1, workflow#32).** Run the real-process lock test suite
   several times in a row (`python3 -m unittest` on the state-lock real-process
   test). Expected: no flaky "ready file" failure; the holder's ready file appears
   whole or not at all.
2. **Governing-version sweep (CP1, workflow#30).** In the scratch repo, edit the
   plan so its governing version disagrees with the work item's, then run the plan
   bundle step (`prepare-ai-review.sh` or `/milestone-plan`'s publish step).
   Expected: refusal naming the governing-version mismatch
   (`docs/common-problems.md`); with the plan corrected, the step succeeds.
3. **Baseline record (CP2).** After ingesting a manual `REVISE` verdict, look under
   `.ai-review/<id>/review-baselines/<ROLE>/`. Expected: a gitignored record; a
   second ingest replaces it wholesale; deleting or corrupting it makes the reader
   return a full review (no crash).
4. **Per-stage changes file (CP3).** Revise the plan and rebuild the bundle.
   Expected: `CHANGES_SINCE_REVIEW.md` has `## LOCAL_MODEL_PLAN_REVIEW` and
   `## MANUAL_EXTERNAL_PLAN_REVIEW` sections; the manual one diffs against the
   content it last reviewed and quotes its own last verdict; with the baseline
   removed it says `not available (<reason>): review the whole bundle.`; with no
   basis for either stage, the file is absent. Repeat for the implementation stage.
5. **Manager block (CP4).** Run `python3 tools/release/release.py manager-block
   --release-dir <scratch release>` and `check-manager-block`. Expected: the block
   validates (integer, string and full-match rules); `--write` changes only
   `suites`; a deliberately wrong authored field or suite count is reported.
6. **Release bookkeeping (CP5).** Check `manifest.json` names 2.13.0, `WORKFLOW_RELEASE`
   is 2.13.0, protocol stays 1.4, `manager-pin.json` names Manager 1.13.0, and
   `docs/release-history.md` has the 2.13.0 row. Run the nine payload suites from
   the scratch release and the tools tests; expected counts 415, 331, 1134, 292,
   140, 106, 307, 269, 27 (acceptance matrix, protocol, state, gate policy,
   fingerprint generalization, completion obligations, integration, fingerprint,
   harness). Where possible compare them against the manifest's measured map
   (`release.py manager-block --release-dir <scratch release>`) rather than these
   fixed numbers.

### Known limitations / out of scope

- Publishing 2.13.0, the `workflow-manager` lock bump and Manager 1.13.0
  publication happen after merge; CP4's CI check needs Manager 1.13.0 published
  before the pull request merges.
- The local review stage's changes file is deliberately unchanged from 2.12.0.
- `test_round_trip` depends on refreshed digests and is judged on the scratch
  release, not the raw working tree.

### Functional review round 1

- Fixed (usability): the wrong-count refusal of the Manager block check now names
  an executable next step, `python3 tools/release/release.py manager-block
  --commit HEAD --write` (or `--release-dir <staged-release>` for an uncommitted
  release source), with a test that parses the printed arguments with the real
  argument parser.
- Checklist correction (no code change): flow 6's expected suite counts are now
  415, 331, 1134, 292, 140, 106, 307, 269, 27.
- Re-test flows 5 and 6.
