# command-wording: evidence (CP1)

Companion to `COMMAND_WORDING_PLAN.md` (D-Evidence). Excluded at the plan stage, protected at the implementation stage.
Each case restores exactly one changed file to its `bebf2d2` version (`git show bebf2d2:<path>`) in a copy of the staged conformance fixture, then runs the named tests from the copy's `scripts/` directory with `python3 -B -m unittest`. The scratch script is neither shipped nor committed.

## Control (candidate, unrestored fixture)

All pass: the five M1/M1b tests of `workflow_state_test.TestReleaseCheckpointStartCommand`
(`test_m1_the_first_raise_names_an_in_progress_checkpoint`,
`test_m1_the_two_added_facts_belong_to_the_in_progress_raise_only`,
`test_m1_epr001_adoption_is_promised_only_when_the_pointer_names_the_entry`,
`test_m1_epr002_the_guidance_for_a_claim_on_another_checkpoint_is_true`,
`test_m1b_the_unclaimed_release_refusal_states_the_pointer_condition`), the unedited
`test_c4_the_amendment_refusal_names_the_command` and `test_c5_end_to_end_in_a_scratch_repository`,
`workflow_integration_test.TestReleaseCheckpointStartCommandFile.test_the_released_bullet_states_the_work_items_one_claim_in_any_worktree`
and `workflow_integration_test.TestUserOnlyCommandListings` (2 tests).

## Cases

| Case | File restored to `bebf2d2` | Result |
| --- | --- | --- |
| E1 | `payload/scripts/workflow_state.py` | all five M1/M1b tests fail (`failures=2, 1, 2, 1, 2`) |
| E1, second subcase | only the text of the unclaimed-`IN_PROGRESS` release refusal in `workflow_state.py` | the four M1 tests pass; `test_m1b_*` alone fails (`failures=2`) |
| E2 | `payload/docs/ai-workflow/COMMAND_FILES.md` | `TestUserOnlyCommandListings.test_the_command_files_row_states_the_number_of_flagged_commands` fails |
| E3 | `payload/.claude/commands/release-checkpoint-start.md` | `TestReleaseCheckpointStartCommandFile.test_the_released_bullet_states_the_work_items_one_claim_in_any_worktree` fails |
| E4 | `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md` | `TestUserOnlyCommandListings.test_the_operator_reference_names_every_user_only_command` fails (`failures=6`) |
| E4, second subcase (round 1, IMP-001) | only the `**User-only commands**` bullet of `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`, restored to its `82f9a47` text | `test_the_operator_reference_names_every_user_only_command` fails on `'(the exact work item, and' unexpectedly found` (`failures=1`); green against the fix |
| E5 | `docs/CONCURRENCY_INVARIANTS.md`, in the checkout (stashed to the committed text) | `python3 -B -m unittest tools.release.release_test.ConcurrencyInvariantsReleaseWindowRowTest` fails (`failures=2`) |

## Other gates

CP1 changes shipped files whose `sha256`, `size` and measured suite counts `manifest.json` records only at CP2. They
were run in a disposable clone of the branch under a scratch directory, with every changed record's `sha256` and
`size` recomputed, then `release.py manager-block --commit HEAD --write` (`workflow_state_test.py` 1239 -> 1244,
`workflow_integration_test.py` 361 -> 364) committed in the clone. No rationale was touched. The staging was adjusted;
the branch's `manifest.json` is unchanged.

- `release.py stage-conformance --commit HEAD --out <fixture>`, then the nine suites from `<fixture>/scripts`:
  `workflow_acceptance_matrix_test.py` 453 OK (skipped 20), `workflow_protocol_test.py` 344 OK (skipped 19),
  `workflow_gate_policy_test.py` 316 OK, `workflow_fingerprint_generalization_test.py` 142 OK,
  `workflow_state_completion_obligations_test.py` 193 OK, `workflow_integration_test.py` 364 OK,
  `workflow_fingerprint_test.py` 283 OK, `workflow_test_harness_test.py` 27 OK; `workflow_state_test.py` as the whole
  chunk under the orphan wrapper, below. The first run of the integration suite failed
  `TestUserOnlyCommandLineWidth` (a rewrapped line of the command file was 99 columns); the bullet was re-flowed
  within 90 and the suite re-run from a re-staged fixture: 364 OK.
- Orphan wrapper (`python3 -I -S -B workflow-manager/tests/parallel/reaper.py --report FILE --chunk-id ID -- ...`),
  from `<fixture>/scripts`:
  - the new and neighbouring tests (`workflow_state_test.TestReleaseCheckpointStartCommand
    workflow_state_test.TestAmendmentResolutionReservation workflow_state_test.TestReleaseCheckpointStart
    workflow_state_test.TestRequestPlanAmendment`): 61 tests OK, chunk status 0, the report lists 364 re-parented `[git]` processes and 2 `git maintenance run --auto --quiet --detach`, nothing else.
  - the whole chunk (`python3 -B workflow_state_test.py`): 1244 tests OK (skipped 1), chunk status 0; 2872 `[git]` and 23 `git maintenance run --auto --quiet --detach`, nothing else.
- `python -m unittest discover -s tools/release -p '*_test.py'` (zlib-ng venv, Python 3.12), in the clone: 275 tests OK.
- `python3 -m unittest discover -s tools/docs -p '*_test.py'`: 34 tests OK; `python3 tools/docs/check_docs.py`: exit 0.
- `release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` in the clone
  after the count adjustment: `ok: 2.19.1 carries a valid manager block that matches the measurement`.
- `git diff bebf2d2 -- payload/scripts/workflow_state.py` adds the text of two messages, the
  `entry_may_be_unclaimed` keyword of `_release_start_next_step` and the choice of the named checkpoint; no
  lock, guard, claim, `os.link`, `flock` or new `resolve_claim` site (the one `resolve_claim` line in the diff is
  unchanged context). `TestGlobalLockOrderItem372h` passes in the whole chunk, unedited.
- `workflow-manager verify .`: `installation matches workflow 2.19.1`.
