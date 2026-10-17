# Active Milestone

## Milestone

**In implementation (CP1 to CP4 complete).** W9: `review-loop-fixes` (`process`, governing version `2.2`),
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
`tools/docs/`. Next: CP5.

## Next action

`/milestone-implement`, one checkpoint per invocation (CP5 next).
Publishing 2.13.0 follows the pull request merge; the Manager side is a
`chore: test Workflow 2.13.0` lock bump in `workflow-manager`. The Manager
release 1.13.0 must be published before this pull request merges (CP4's CI check).
