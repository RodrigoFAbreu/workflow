# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W22: `checkpoint-start-engine` (`process`, governing version `2.2`), branch
`milestone/checkpoint-start-engine`, roadmap row 24b (RodrigoFAbreu/workflow#55, engine only; #95 closes with
the release). Plan: `docs/ai-workflow/CHECKPOINT_START_ENGINE_PLAN.md` (revision 4, approved by gate policy).
The goal is Workflow 2.18.7, a patch release (`fix:`): the library function
`workflow_state.release_checkpoint_start`, which releases an uncommitted checkpoint start (the `IN_PROGRESS`
entry, then the claim) as one window. It adds no command; row 24c adds that. The previous milestone, W21
`live-guard-visibility`, is accepted (Workflow 2.18.6).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The release engine, its tests and the fork-test fix | **complete** |
| CP2 | Release 2.18.7 | **complete** |

## Verified state

- CP1: `release_checkpoint_start` and its helpers are in `payload/scripts/workflow_state.py`;
  `TestReleaseCheckpointStart` (T1 to T11) was shown red against the unedited code and passes; the two
  lock-order scripts declare the (5)->(2) edge and extend regression 1 to the engine's own unlink; the fork
  test is the subreaper of its own orphan (#95).
- Verified in a disposable clone (D-Staging): the nine suites, the whole `workflow_state_test.py` chunk under
  the Manager's orphan wrapper (only git's own detached-maintenance orphans), `check-manager-block`,
  `check_docs.py`, the `tools/docs` tests and the `tools/release` tests in the zlib-ng environment;
  `workflow-manager verify .` is clean.
- Plan deviation: the plan names `prove_checkpoint_completions`, which the payload does not have; T9(c) pins
  the same wedge through `discover_checkpoint_commits`, which raises `AmbiguousCheckpointTrailerError`.
- CP2: `manifest.json` 2.18.7 (digests and sizes of the seven changed records, their
  `checkpoint-start-engine (workflow-2.18.7)` sentences, the downgrade posture, and `conformance.suites`
  measured by `release.py manager-block --write`: only `workflow_state_test.py` changed, 1214 to 1226);
  `WORKFLOW_RELEASE`, its two pinned assertions and `ORCHESTRATION_PROTOCOL.md`; the `docs/release-history.md`
  row; the release-window row, the `release-start` step and the narrowed #55 gap in
  `docs/CONCURRENCY_INVARIANTS.md`; the `CheckpointStartEngineReleaseTest` class in `release_test.py`.
- Verified in a disposable clone (D-Staging; the tree committed there): the nine suites in a stock
  `stage-conformance --commit HEAD` fixture, `release.py build --commit HEAD`, `check-manager-block`,
  `check_docs.py`, the `tools/docs` tests and the 269 `tools/release` tests in the zlib-ng environment;
  `workflow-manager verify .` is clean (the installation is untouched and stays 2.18.6).
- The plan names `prove_checkpoint_completions` for the residual's wedge; the docs name
  `discover_checkpoint_commits`, which is what raises `AmbiguousCheckpointTrailerError` (see CP1).
- Functional review: six flows (`w22-f1` to `w22-f6`) passed at the approved content, recorded as orchestrator
  evidence by an independent executor (F4 ran the state suite under the Manager's reaper with no orphans); the
  acceptance record is the work item's `acceptance_satisfaction`.
- Optional findings: seventeen recorded, all dispositioned (two fixed, nine dropped, six follow-ups on
  RodrigoFAbreu/workflow#97); see `docs/milestones/completed/checkpoint-start-engine-findings.md`.

## Next action

Merge pull request #98, let the `Release` workflow publish Workflow 2.18.7, then plan roadmap row 24c (W19b, the
`/release-checkpoint-start` command, `/milestone-plan`).
