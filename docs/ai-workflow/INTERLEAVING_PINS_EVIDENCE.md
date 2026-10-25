# interleaving-pins: evidence (CP1)

Companion to `INTERLEAVING_PINS_PLAN.md` (D-Evidence). Excluded at the plan stage, protected at the implementation stage.
Each mutant is one text substitution applied to a scratch copy of `payload/scripts/workflow_state.py` (it must occur exactly once); the named tests are then run from the copy's `scripts/` directory. The scratch script is neither shipped nor committed; the substitutions below are its complete input (flow f2 re-applies them).

## Control (unmutated copy)

`python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart.test_p1_the_release_window_takes_no_guardlock_inside_its_body workflow_state_test.TestReleaseCheckpointStart.test_p2_the_entry_absent_branch_writes_no_state workflow_state_test.TestReleaseCheckpointStart.test_p2_a_crash_at_the_unlink_of_the_entry_absent_branch workflow_state_test.TestReleaseCheckpointStart.test_p2_a_crash_in_the_gap_after_the_unlink_of_the_entry_absent_branch workflow_state_test.TestReleaseCheckpointStart.test_p2_a_failed_unlink_of_the_entry_absent_branch workflow_state_test.TestAmendmentResolutionReservation.test_the_journal_refusal_names_no_release_command workflow_state_test.TestReleaseCheckpointStartCommand.test_p4_the_in_progress_arm_over_the_real_entry_before_and_after_a_release`

Result: exit 0, `OK`.

## Mutants

### M1a: a call to guard_holder_is_running in the body, before the claim re-read

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart.test_p1_the_release_window_takes_no_guardlock_inside_its_body`

Result: exit 1, `FAILED (failures=4)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStart.test_p1_the_release_window_takes_no_guardlock_inside_its_body`

Substitution 1, old text:

```python
            current = resolve_claim(repo_root, work_item_id)
            held = read_guard(repo_root, work_item_id)
            if (current is None or current.get("owner_token") != owner_token
```

new text:

```python
            guard_holder_is_running(repo_root, work_item_id)
            current = resolve_claim(repo_root, work_item_id)
            held = read_guard(repo_root, work_item_id)
            if (current is None or current.get("owner_token") != owner_token
```

### M1b: the guard re-read wrapped in guard_mutation_lock

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart.test_p1_the_release_window_takes_no_guardlock_inside_its_body`

Result: exit 1, `FAILED (failures=4)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStart.test_p1_the_release_window_takes_no_guardlock_inside_its_body`

Substitution 1, old text:

```python
            current = resolve_claim(repo_root, work_item_id)
            held = read_guard(repo_root, work_item_id)
            if (current is None or current.get("owner_token") != owner_token
```

new text:

```python
            current = resolve_claim(repo_root, work_item_id)
            with guard_mutation_lock(repo_root, work_item_id):
                held = read_guard(repo_root, work_item_id)
            if (current is None or current.get("owner_token") != owner_token
```

### M1c: a guard re-read under guard_mutation_lock only in the re-read refusal branch

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart.test_p1_the_release_window_takes_no_guardlock_inside_its_body`

Result: exit 1, `FAILED (failures=1)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStart.test_p1_the_release_window_takes_no_guardlock_inside_its_body`

Substitution 1, old text:

```python
                raise CheckpointOwnershipUnavailableError(
                    f"{work_item_id!r}'s claim or guard changed after
```

new text:

```python
                with guard_mutation_lock(repo_root, work_item_id):
                    read_guard(repo_root, work_item_id)
                raise CheckpointOwnershipUnavailableError(
                    f"{work_item_id!r}'s claim or guard changed after
```

### M2: the non-entry branch calls state_transaction

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart.test_p2_the_entry_absent_branch_writes_no_state`

Result: exit 1, `FAILED (failures=2)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStart.test_p2_the_entry_absent_branch_writes_no_state`

Substitution 1, old text:

```python
                state_transaction(repo_root, restore)
            current = resolve_claim
```

new text:

```python
                state_transaction(repo_root, restore)
            else:
                state_transaction(repo_root, lambda s: s)
            current = resolve_claim
```

### M3: the claim unlink moved after the guard release

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart.test_p2_a_crash_at_the_unlink_of_the_entry_absent_branch workflow_state_test.TestReleaseCheckpointStart.test_p2_a_crash_in_the_gap_after_the_unlink_of_the_entry_absent_branch`

Result: exit 1, `FAILED (failures=4)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStart.test_p2_a_crash_at_the_unlink_of_the_entry_absent_branch`
- `workflow_state_test.TestReleaseCheckpointStart.test_p2_a_crash_in_the_gap_after_the_unlink_of_the_entry_absent_branch`

Substitution 1, old text:

```python
            try:
                claim_path(repo_root, work_item_id).unlink(missing_ok=True)
            except OSError as exc:
```

new text:

```python
            pass
        claim_path(repo_root, work_item_id).unlink(missing_ok=True)
        if False:
            try:
                pass
            except OSError as exc:
```

### M4: the unlink's except OSError swallows the error

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart.test_p2_a_failed_unlink_of_the_entry_absent_branch`

Result: exit 1, `FAILED (failures=2)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStart.test_p2_a_failed_unlink_of_the_entry_absent_branch`

Substitution 1, old text:

```python
            try:
                claim_path(repo_root, work_item_id).unlink(missing_ok=True)
            except OSError as exc:
```

new text:

```python
            try:
                claim_path(repo_root, work_item_id).unlink(missing_ok=True)
            except OSError as exc:
                return None
```

### M5: the third raise gains _release_start_next_step

Command: `python3 -B -m unittest workflow_state_test.TestAmendmentResolutionReservation.test_the_journal_refusal_names_no_release_command`

Result: exit 1, `FAILED (failures=1)`. Failing tests:

- `workflow_state_test.TestAmendmentResolutionReservation.test_the_journal_refusal_names_no_release_command`

Substitution 1, old text:

```python
                f"transaction that would resolve the amendment under it"
```

new text:

```python
                f"transaction that would resolve the amendment under it "
                f"{_release_start_next_step(work_item_id, live_claim.get('checkpoint_id'))}"
```

### M6: the IN_PROGRESS arm of request_plan_amendment disabled

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStartCommand.test_p4_the_in_progress_arm_over_the_real_entry_before_and_after_a_release`

Result: exit 1, `FAILED (failures=2)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStartCommand.test_p4_the_in_progress_arm_over_the_real_entry_before_and_after_a_release`

Substitution 1, old text:

```python
    if in_progress_ids:
        raise AmendmentCheckpointActiveError(
```

new text:

```python
    if False and in_progress_ids:
        raise AmendmentCheckpointActiveError(
```

### M7: the release's entry restore skipped

Command: `python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStartCommand.test_p4_the_in_progress_arm_over_the_real_entry_before_and_after_a_release`

Result: exit 1, `FAILED (failures=2)`. Failing tests:

- `workflow_state_test.TestReleaseCheckpointStartCommand.test_p4_the_in_progress_arm_over_the_real_entry_before_and_after_a_release`

Substitution 1, old text:

```python
            if kind == "entry":
                def restore
```

new text:

```python
            if False:
                def restore
```

Information (not a gate): `TestGlobalLockOrderItem372h` independently fails M1a (1 failure), M1b (2 failures) and M1c (2 failures).
M1c fails only the fifth `test_p1_*` scenario (`the re-read refusal`).

## Other gates (D-Staging)

CP1 changes `payload/scripts/workflow_state_test.py`, whose digest, size and measured suite count `manifest.json`
records only at CP2. They were run in a disposable clone of the branch under a scratch directory, with that
record's `sha256` and `size` recomputed, then (for `check-manager-block`) `release.py manager-block --commit HEAD
--write` (`workflow_state_test.py` 1232 -> 1239) committed in the clone. No rationale was touched. The staging was
adjusted; the branch's `manifest.json` is unchanged.

- `python3 tools/release/release.py stage-conformance --commit HEAD --out <fixture>`, then each of the nine suites
  of `manager.conformance.suites`, from `<fixture>/scripts`: `workflow_acceptance_matrix_test.py` 453 tests OK
  (skipped 20), `workflow_protocol_test.py` 344 OK (skipped 19), `workflow_gate_policy_test.py` 316 OK,
  `workflow_fingerprint_generalization_test.py` 142 OK, `workflow_state_completion_obligations_test.py` 193 OK,
  `workflow_integration_test.py` 361 OK, `workflow_fingerprint_test.py` 283 OK, `workflow_test_harness_test.py`
  27 OK; `workflow_state_test.py` is run as the whole chunk under the orphan wrapper, below.
- Orphan wrapper (`python3 -I -S -B workflow-manager/tests/parallel/reaper.py --report FILE --chunk-id ID -- ...`),
  from `<fixture>/scripts`:
  - the new tests (`python3 -B -m unittest workflow_state_test.TestReleaseCheckpointStart
    workflow_state_test.TestReleaseCheckpointStartCommand workflow_state_test.TestAmendmentResolutionReservation`):
    38 tests OK, chunk status 0; the report lists 301 re-parented `[git]` processes and 3
    `git maintenance run --auto --quiet --detach`, nothing else.
  - the whole chunk (`python3 -B workflow_state_test.py`): 1239 tests OK (skipped 1), chunk status 0; 2855 `[git]`
    and 18 `git maintenance run --auto --quiet --detach`, nothing else.
- `python -m unittest discover -s tools/release -p '*_test.py'` (zlib-ng 2.2.5 venv): 271 tests OK, in the clone.
- `python3 -m unittest discover -s tools/docs -p '*_test.py'`: 34 tests OK; `python3 tools/docs/check_docs.py`:
  exit 0.
- `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases
  tools/release/manager-releases.json` in the clone: before the count adjustment it refused with
  `workflow_state_test.py recorded 1232, measured 1239`; after it: `ok: 2.19.0 carries a valid manager block`.
- `git diff e8aff0a -- payload/scripts/workflow_state.py`: empty. `workflow-manager verify .`: `installation
  matches workflow 2.19.0`.
