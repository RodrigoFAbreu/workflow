# Active Milestone

## Milestone

W61: `payload-polish-batch` (`process`, governing version `2.2`), branch `milestone/payload-polish-batch`, base
`16e013022e01e52b572b2a24090e91c4e886ae63`. Release Workflow 2.29.12, a `fix:` patch. Row 54 of `docs/ROADMAP.md`. Issues
RodrigoFAbreu/workflow#108 point 3, #85 point 4, #205, and #208 points 1 and 2. The plan is
`docs/ai-workflow/PAYLOAD_POLISH_BATCH_PLAN.md` (revision 3).

## Goal

Three wording points and two test follow-ups in the shipped payload. No refusal order, command, exit code or working path changes.
The release (manifest `workflow_version` 2.29.12, the history row, the protocol document's release lines) is part of this branch;
its version bump is commit `903d363`.

## Outcome

- CP1 (`791418f`), CP2 (`525a3db`) and CP3 (`903d363`) are complete. Implementation review round 3: local `APPROVE`
  (`LOCAL_MODEL_IMPLEMENTATION_REVIEW`) and external `APPROVE` (manual, `openai/gpt-6.1-sol`) on implementation revision 2. The
  technical approval is `CURRENT` (recorded by policy, `afd7c9d`).
- Implementation revision 2 changed the #85 wording to three arms, not the two the plan's D-Wording 2 text describes (round 2 of the
  implementation review, LIR-R1-001: a non-takeover ordinary guard cannot be recovered by "abandoned-guard recovery", which refuses it).
  The plan bytes are the approved ones, so the plan's D-Wording 2 text is stale on this point; the shipped wording is recorded in
  `.ai-review/payload-polish-batch/current/IMPLEMENTATION_SUMMARY.md` (round 2) and in the history row and roadmap row 54.
- Automated verification is recorded in `.ai-review/payload-polish-batch/current/TEST_RESULTS.md` (revision 2). No shipped file, test
  or manifest has changed since `26be4f1`, so that verification is current. Results: the nine payload suites pass (453, 344, 1250,
  429, 151, 319, 385, 283 and 27 tests); `tools/release` 388 tests; `tools/docs` 34 tests; `check_docs.py` exit 0;
  `check-manager-block` ok; `check-title` `impact=patch`; `release.py build` exit 0; the reaper on the touched tests; mutations m1,
  m2, m2b, m3, m4 (a) and (b), and m5 each fail exactly what the plan states.
- Not taken, recorded as optional findings in the plan (section 0): F1 (the remove flow's other strays before its rename keep the
  "renamed aside" text) and F2 (the leftover note is appended twice in the `_flow` lock-time re-selection, pre-existing). Neither is a
  defect of this batch to fix here.
- Nothing is pushed, merged or published. The installation (`.claude/`, `scripts/`, `.workflow-manager/`, managed blocks,
  `.github/`) is untouched, so `workflow-manager verify .` reports the installation at 2.29.11. That is expected until a release is
  published and a manager pin is added.

## Functional review checklist

Scope: the shipped wording of two refusals, the message of one remove-flow refusal, the docs sentence in `docs/RETENTION.md`, and the
two test follow-ups. The check is that exactly these messages changed, that the new tests and mutations behave as stated, and that the
release is consistent. Every flow below is offline. None needs GitHub, `gh`, the network, `claude`, `codex`, `ssh`, a PID namespace, or a
pull request.

### Setup

- Work from `milestone/payload-polish-batch` at its HEAD. Do not write inside the product clone: every command below writes only to a
  scratch directory, `S="$(mktemp -d)"`, and mutations run in copies of the fixture, never in the repository.
- Tools: `git`, `python3`. Two flows also use the zlib-ng interpreter named in the flow (an absolute path under `~/.claude`). The reaper
  flow uses `~/Workspace/workflow-manager/tests/parallel/reaper.py`, which is outside the product clone.
- Base for the diffs: `16e013022e01e52b572b2a24090e91c4e886ae63`.

### Test data

None beyond the repository and the scratch directories. The retention tests build their own scratch repositories. No flow runs
`archive`, `remove` or `prune` against a real repository.

### Flows

**F1. Scope of the change.** `git diff --stat 16e0130 -- payload` must list seven files: `workflow_state.py`,
`workflow_retention.py`, `workflow_state_test.py`, `workflow_state_completion_obligations_test.py` (CP1 and CP2),
`workflow_protocol.py`, `workflow_protocol_test.py` and `docs/ORCHESTRATION_PROTOCOL.md` under `payload/docs/ai-workflow/` (CP3).
Expected: 178 insertions and 42 deletions in those seven files, nothing else.

**F2. #108 point 3 (comment only).** `git diff 16e0130 -- payload/scripts/workflow_state.py | grep '^[-+][^-+]'`.
Expected: the docstring of `_release_start_next_step` now says "three cases, and this step is the first", plus the new branch of the
`OPUS-R82-002` refusal (the foreign-worktree refusal of the claim guard). No other line changes. The branch has three arms: a
takeover's guard names the takeover route; a `DESTRUCTIVE` guard keeps "use the abandoned-guard recovery"; any other guard names the
takeover route with the guard-release literal. The cause text of the refusal is unchanged.

**F3. #205 (remove flow).** `git diff 16e0130 -- payload/scripts/workflow_retention.py | grep '^[-+][^-+]'`.
Expected: the new `_stray_message(command, exc)` helper, the decorator calling it (its text byte-identical), and one `except OSError`
arm around the index block of `_judge_removal_archive`. Nothing else changes.

**F4. The installation is untouched.** `git diff --name-only 16e0130 -- .claude scripts .workflow-manager .github CLAUDE.md`.
Expected: no output. Then `python3 -c "import json;print(json.load(open('manifest.json'))['workflow_version'])"` prints `2.29.12`, and
`docs/ROADMAP.md` row 54 reads `Done`.

**F5. Nine payload suites in a staged fixture.** From the repository root:

```bash
python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"
suites=$(python3 -c "import json; print(*json.load(open('manifest.json'))['manager']['conformance']['suites'], sep='\n')") && test -n "$suites" && ( cd "$S/fixture/scripts" && while read -r suite; do python3 -B "$S/fixture/scripts/$suite" </dev/null || exit 1; done <<< "$suites" )
```

Expected: exit 0. Test counts: `workflow_acceptance_matrix_test.py` 453, `workflow_protocol_test.py` 344, `workflow_state_test.py`
1250, `workflow_gate_policy_test.py` 429, `workflow_fingerprint_generalization_test.py` 151,
`workflow_state_completion_obligations_test.py` 319, `workflow_integration_test.py` 385, `workflow_fingerprint_test.py` 283,
`workflow_test_harness_test.py` 27. All OK.

**F6. Tools and docs.** `<zlib-ng interpreter> -m unittest discover -s tools/release -p '*_test.py'`, where the interpreter is
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
Expected: 388 tests OK. Then `python3 -m unittest discover -s tools/docs -p '*_test.py'` (34 OK) and `python3 tools/docs/check_docs.py`
(exit 0).

**F7. Release consistency.**

```bash
python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json
python3 tools/release/release.py check-title "fix: name the true next step in two payload refusals and harden two payload tests" --agree --head 903d363
<zlib-ng interpreter> tools/release/release.py build --commit HEAD --out "$S/build"
```

Expected: `check-manager-block` prints `ok: 2.29.12 carries a valid manager block that matches the measurement`; `check-title` reports
`impact=patch` and agrees with 2.29.11 -> 2.29.12; `build` exits 0 and writes `workflow-2.29.12.tar.gz`, its manifest and `SHA256SUMS`.

**F8. Reaper (orphan check) on the new and touched tests.** From `$S/fixture/scripts`, for each suite and its tests:

```bash
python3 ~/Workspace/workflow-manager/tests/parallel/reaper.py --report "$S/R1.json" --chunk-id polish-obl -- python3 -B workflow_state_completion_obligations_test.py RetentionErrorPathsTwo.test_t7b3_a_failed_index_io_says_nothing_was_renamed RetentionTestPins.test_p5_a_stat_only_change_after_the_hash_puts_the_folder_back_and_deletes_nothing
python3 ~/Workspace/workflow-manager/tests/parallel/reaper.py --report "$S/R2.json" --chunk-id polish-state -- python3 -B workflow_state_test.py TestTakeoverGuardIsNotTheOwnersToReclaim.test_same_token_other_worktree_still_gets_the_foreign_worktree_message TestLiveGuardVisibility.test_the_unchanged_routes_with_a_locked_guard TestStateValidation.test_repo_root_check_rejects_dot_dot_traversal_registry_path
```

Expected: both exit 0; orphans only `[git]`, all `exited`.

**F9. Mutations, each in its own scratch copy of the fixture (never the repository).** Each must fail exactly what is listed and nothing else.

| Mutation | Change in the copy | Expected |
| --- | --- | --- |
| m1 | drop the appended step of `OPUS-R82-002` (all three arms) | exactly three failures: the takeover test, and the subtests "the same-token other-worktree refusal, ordinary guard" and "…, destructive guard"; no `LifecycleLockOrderError` cascade |
| m2 | drop the new `except OSError` arm in `_judge_removal_archive` | the new `test_t7b3` fails in four subtests (the stat after the open with `remove --apply` and with dry-run `remove`, the size stat, the close); the rest of the 319-test suite passes |
| m2b | narrow the arm to the `_open_index` call only | `test_t7b3` fails in two subtests (the size stat, the close) |
| m3 | "repair the cause" → "fix the cause" in the new step | the four subtests asserting the exact step fail, nothing else |
| m4 (a) | round the hook's `os.utime` stamp in `test_p5` down to a whole 2 s | the old `test_p5` form fails; the new one passes |
| m4 (b) | make `_restore` `os.utime` the restored `a.txt` after the rename back | the new `test_p5` assertion fails |
| m5 | plant a `foreign.json` sentinel in the temporary directory's parent before the dot-dot test | the old form overwrites and deletes the sentinel; the new form passes and leaves it intact |

The open-failure subtests (`EACCES`, `EIO`) and the post-rename subtest pass under m2, m2b and m3.

### Known limitations and out of scope

- No refusal order, exit code or unrelated message changes. F1 and F2 (above) are not taken. The remove flow's other pre-rename strays
  (the dry run's step 12, `_hash_folder` and `_archive_table`, and `_flow`'s lock-time sites such as `os.fstat(adir_fd)`) still say
  "renamed aside". This is recorded, not a defect of this batch.
- The #85 point 4 wording follows the shipped three-arm form described under Outcome. A tester comparing the plan's D-Wording 2 text
  with the shipped message will find a difference in the non-takeover arms; the shipped form is the reviewed one.
- No pull request, push, merge or publication happens in this checklist. The release is published by CI after the merge.
- Nothing here changes this repository's own installation: `workflow-manager verify .` reports 2.29.11, as it should.

## Next action

The checklist is ready for the functional review (`AWAITING_FUNCTIONAL_REVIEW`). Findings go to
`.ai-review/payload-polish-batch/feedback/FUNCTIONAL_REVIEW.md`. Once testing is clean, `/accept-milestone` is the only acceptance
command, and it requires every checkpoint of this item to be `COMPLETE` (CP1 to CP3 are). If a finding needs a change, use
`/apply-functional-review`.
