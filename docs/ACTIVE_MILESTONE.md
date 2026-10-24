# Active Milestone

## Milestone

**In progress.** W22: `checkpoint-start-engine` (`process`, governing version `2.2`), branch
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
| CP2 | Release 2.18.7 | pending |

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

## Next action

`/milestone-implement checkpoint-start-engine` for CP2 (Release 2.18.7).
