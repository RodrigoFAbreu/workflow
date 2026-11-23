# Active Milestone

## Milestone

**W60: `payload-test-hardening-1`** (`process`, governing version `2.2`), branch `milestone/payload-test-hardening-1`, roadmap row 53
(RodrigoFAbreu/workflow#85 points 1 to 3, #194 points 1 and 3, #108 point 4). The plan is
`docs/ai-workflow/PAYLOAD_TEST_HARDENING_1_PLAN.md` (revision 3). Phase: `AWAITING_FUNCTIONAL_REVIEW`; implementation revision 1;
checkpoints CP1 and CP2 are both `COMPLETE`; plan and technical approvals are recorded by policy.

## Goal

Strengthen six existing payload tests so that they pin behaviour the product already has but the tests did not check. No product
behaviour, message, key, code or phase changes, and no test method is added or removed. CP1 strengthens the tests in
`payload/scripts/workflow_integration_test.py`, `workflow_state_test.py` and `workflow_state_completion_obligations_test.py`. CP2 is
Workflow release 2.29.11, a `fix:` patch, because those three files are shipped records.

## Functional review checklist

This is a test-only change. Functional testing here means running the tests and checking the release metadata. Nothing runs against
the real repository, GitHub, the network, or any agent CLI. Every flow below works in a scratch directory outside the repository.
No flow needs GitHub, the network, `claude`, `codex`, `ssh`, or a PID namespace.

### 1. Setup

- The repository at `milestone/payload-test-hardening-1`, with a clean tree (`git status --short` prints nothing).
- Tools: `git`, the system `python3`, and a Python with the pinned zlib-ng runtime (`docs/RELEASING.md`, "Building locally"). Set
  `ZLIB_NG_PYTHON` to that interpreter. Use it for every `tools/release` command. The build refuses unless it reports zlib-ng 2.2.5.
- Set `S` to a new, empty directory outside the repository (`S="$(mktemp -d)"`). Run every Python command with `-B` (or
  `PYTHONDONTWRITEBYTECODE=1`), so that no bytecode is written into the read-only product clone.
- Run the suites from inside the staged fixture, never from the repository root (`docs/RELEASING.md`, "Verification commands").

### 2. Test data

None. Each flow builds its own fixture or scratch copy under `$S`.

### 3. Flows

`1519eed` is the base commit. `HEAD` is the implementation head plus the recorded state commits.

| Flow | Steps | Expected |
| --- | --- | --- |
| F1 scope | `git diff --name-only 1519eed HEAD -- payload` | exactly six files: `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `payload/scripts/workflow_integration_test.py`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/scripts/workflow_state_completion_obligations_test.py`, `payload/scripts/workflow_state_test.py` |
| F2 product lines | `git diff 1519eed HEAD -- payload/scripts/workflow_protocol.py \| grep '^[-+][^-+]'` | exactly one change: `WORKFLOW_RELEASE` `"2.29.10"` to `"2.29.11"`. No other product line changes anywhere in `payload/` |
| F3 no test added or removed | `git diff 1519eed HEAD -- payload/scripts/*_test.py \| grep '^[-+]' \| grep -c 'def test_'` | `0` |
| F4 nine suites | from the staged fixture, `python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"`, then the `docs/RELEASING.md` loop over `manifest.json`'s `manager.conformance.suites` | every suite prints `OK`. Each suite's `Ran` count equals its manifest value: `workflow_acceptance_matrix_test.py` 453, `workflow_protocol_test.py` 344, `workflow_state_test.py` 1250, `workflow_gate_policy_test.py` 429, `workflow_fingerprint_generalization_test.py` 151, `workflow_state_completion_obligations_test.py` 318, `workflow_integration_test.py` 385, `workflow_fingerprint_test.py` 283, `workflow_test_harness_test.py` 27 |
| F5 tools tests | `"$ZLIB_NG_PYTHON" -B -m unittest discover -s tools/release -p '*_test.py'`; `python3 -B -m unittest discover -s tools/docs -p '*_test.py'`; `python3 -B tools/docs/check_docs.py` | all OK; `check_docs` is clean |
| F6 release metadata | `python3 -B -c` reading `manifest.json`; `grep -n '^\| 53 ' docs/ROADMAP.md`; `git show HEAD:docs/release-history.md` | `workflow_version` is `2.29.11`; row 53 is `Done`; the history has a `2.29.11` row and its "Last checked with" line names `2.29.11` |
| F7 manager block and title | `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`; `python3 tools/release/release.py check-title "fix: strengthen the takeover-fence, retention stand-in and release-start pointer tests" --agree --head 5081b8f` | the block check is clean; the title agrees and reports `impact=patch` |
| F8 release build | `"$ZLIB_NG_PYTHON" -B tools/release/release.py build --commit HEAD --out "$S/build"` | succeeds; the archive is written under `$S` only |
| F9 installation | `workflow-manager verify .` with `--release-cache` (or `WORKFLOW_MANAGER_RELEASE_CACHE`) set to a cache of the installed release's assets | clean. With no cache and no network it exits 1 with `cannot fetch`. That is an environment failure, not a pass; record it as such |
| F10 mutations, strengthened | for each of m1, m1b, m2 to m8 (table below): copy the fixture to `$S/<m>`, make the one edit the plan's D-Tests names in that copy only, and run the suites it names | the failures are exactly the set in the table. Any other failure is a D-Stop. An unmutated run is all `OK` |
| F11 mutations, original | in each copy from F10, first replace the three test files with `git show 1519eed:<path>`, then run the same suites | the original target test passes. The other failures are exactly those the table lists for the original run |
| F12 reaper | `reaper.py --report "$S/R.json" --chunk-id hardening -- python3 -B <suite> <class>` for the five classes: `TestPlanApprovalMutationGuardAndTakeover` (integration), `TestTakeoverGuardIsNotTheOwnersToReclaim` and `TestReleaseCheckpointStartCommand` (state), `RetentionArchive` and `RetentionTestPins` (obligations) | status 0 for all five; orphan processes only `[git]` helpers, all `exited`. `reaper.py` is in the workflow-manager checkout (`tests/parallel/reaper.py`), not here. If it is not available, the flow is not run and must be reported as not run, not as passed |
| F13 scope guards | `git diff --name-only 1519eed HEAD -- .claude scripts .workflow-manager .github CLAUDE.md` | prints nothing |

**F10 and F11 mutations.** Each edit is the one `docs/ai-workflow/PAYLOAD_TEST_HARDENING_1_PLAN.md` names in its section D-Tests.
Check each copy with `diff` against the fixture: the only difference must be that edit. "Strengthened target" means the new
assertion in the test named. "Other failures" are tests that already pin the mutated line.

| Mutation | Scratch edit (D-Tests) | Strengthened run must fail | Other failures, in both runs (any other is a D-Stop) |
| --- | --- | --- | --- |
| m1 | `workflow_state.py`, `take_over_plan_approval_transaction`: a dead claim raises `PlanApprovalTakeoverInProgressError` instead of clear-and-retry | I `test_leftover_takeover_guard_names_the_route_and_the_route_clears_it` (journal) | I `test_a_dead_claim_from_a_crashed_same_epoch_takeover_is_cleared_and_retried`. S: none |
| m1b | the same branch: on `FileExistsError` with the journal still naming the token, skip the clear and the retry | I, the same target, on its inode assertion | none in I or S |
| m2 | `acquire_guard`: drop `decidable and` from the superseded-epoch test | S `TestTakeoverGuardIsNotTheOwnersToReclaim.test_leftover_takeover_guard_names_the_route_and_the_route_clears_it` | none in I or S |
| m3 | `_acquire_plan_approval_guard_locked`, own-leftover branch: release the held guard and return without publishing it | I `test_non_takeover_guard_of_the_same_token_is_still_reclaimed` | I `TestPlanApprovalMutationGuardAndTakeover.test_owner_reclaims_its_own_leftover_guard_and_retries_once` and `TestLiveGuardVisibilityJournal.test_killed_owner_a_leftover_is_reclaimed_by_b` (two results). S: none |
| m4 | `acquire_guard`, own-leftover branch: the same | S `test_non_takeover_guard_of_the_same_token_is_still_reclaimed` (claim guard) | S, eleven results in seven tests: `TestLiveGuardVisibility.test_killed_owner_a_leftover_is_reclaimed_by_b`, `TestLiveGuardVisibility.test_descriptor_hygiene`, `TestReleaseCheckpointStart.test_p2_a_crash_at_the_unlink_of_the_entry_absent_branch`, `test_t11_a_demoted_checkpoint_that_was_restarted`, `test_t3_a_live_owner_is_not_overtaken`, `test_t4_a_crash_at_each_step_is_finished_or_refused_by_the_next_call`, and `TestReleaseCheckpointStartCommand.test_c5_end_to_end_in_a_scratch_repository`. I: none |
| m5 | test helper in O (scratch copy): both `stand_in` helpers write `real=` without `shlex.quote` | O `test_a5_a_failed_pack_reaps_its_child_and_a_truncated_stream_is_not_placed` and `test_p4_an_archive_whose_bytes_differ_with_names_types_and_sizes_equal_is_not_kept` | none (the original helpers' paths hold no space) |
| m6 | test helper in O: `test_p4` drops the quoting of the interpreter and the script | O `test_p4` alone | none |
| m7 | product `workflow_retention.py`, `_restore`: after the rename back, touch `a.txt` with an `os.utime` taken at import | O `test_p5_a_stat_only_change_after_the_hash_puts_the_folder_back_and_deletes_nothing`, and the four existing tests below | O `RetentionRemove.test_t3_a_difference_refuses_and_nothing_is_lost` (five subtests), `test_t10_leftover_states_built_by_hand`, `test_w37_t5_an_unreadable_symlink_after_the_rename_puts_the_folder_back`, `test_w37_t5c_an_unreadable_symlink_at_the_recheck_puts_an_incomplete_leftover_back`. I: none |
| m8 | `resolve_checkpoint_ownership`: a pointer counts as in progress here when its entry merely exists (`checkpoints.get(current_id) is not None`) | S `test_m1_epr001_adoption_is_promised_only_when_the_pointer_names_the_entry` and `test_m1b_the_unclaimed_release_refusal_states_the_pointer_condition`, in the new non-`IN_PROGRESS` subtest only | none in I or S (the original tests pass) |

### 4. Expected results at a glance

- Every suite is green unmutated: integration 385, state 1250, obligations 318, and the other six at their manifest counts.
- Each mutation fails its strengthened target and the other failures listed above, and nothing else. Each original target passes.

### 5. Known limitations and out of scope

- No behaviour change. A green run shows that the tests pass against the current product, not that the product is correct beyond
  the existing tests. No defect was found in the scratch prototype (plan section 0).
- Not taken: #85 point 4 and #108 point 3 (both change payload code or a message, and the owner deferred them). #194 point 2 is
  obsolete: the test it names no longer exists on main.
- Nothing is pushed, merged, published or pinned here. The release is published by `Build and publish` after the merge, and the
  Manager pin is a separate `workflow-manager` pull request.
- No flow proves namespace isolation. If a runner wraps these suites in a namespace and the launcher is refused, the flow that needs
  it is `environment`, and its summary quotes the refusal. A run that reports `namespace: none` is not isolation evidence.

## Next action

This is the functional-review gate: a person (or the Controller's functional tester) runs the flows above. Findings go to
`.ai-review/payload-test-hardening-1/feedback/FUNCTIONAL_REVIEW.md`, and `/apply-functional-review` routes them. Once testing is
clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint in this item's registry to be `COMPLETE`.
CP1 and CP2 are complete, so no checkpoint is outstanding.
