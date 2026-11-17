# Active Milestone

## Milestone

**Awaiting functional review.** W58: `gate-policy-test-pins` (`process`, governing version `2.2`), branch `milestone/gate-policy-test-pins`, roadmap row 51
(RodrigoFAbreu/workflow#185 points 2 to 4, #143 point 3, #149 point 3, #190 point 4). The plan is
`docs/ai-workflow/GATE_POLICY_TEST_PINS_PLAN.md` (revision 3, approved by gate policy).

## Goal

Test-only: five tightenings and one new test in three payload test files; no script changes. Not taken: #185 point 1 (a code change).

## Progress

- CP1 (the pins p1 to p6 and roadmap row 51): implemented. G (`workflow_gate_policy_test.py`) 429 tests OK and I's edited class OK; T
  (`workflow_state_completion_obligations_test.py`) 317 tests OK (316 plus the new `RetentionReportUnreadable.test_t7`).
  Mutations m1 to m5 run in scratch copies of `payload/`: each fails exactly the test its plan row names (m1: the two `stale_changes` and
  `stale_failed` subtests of T4; m2: T5; m3: T3; m5: the new T7; m4: the demonstration, four other tests that patch `os.unlink` plus the new
  observed-call assertions of T6). m6 (the label line emitted twice) fails only the surviving `len == 1` assertion of p6.
- CP2 (release 2.29.9): implemented. `manifest.json` 2.29.9 (six records with the sentence, `sha256`, `size`; the obligations suite count 316 to 317 measured by `release.py manager-block --write`; posture), `WORKFLOW_RELEASE` 2.29.9 with the protocol test and `ORCHESTRATION_PROTOCOL.md` lines, the `docs/release-history.md` row and stamp, and `tools/release/release_test.py` (a 2.29.9 class; the 2.29.8 class gives up the pins a newer release owns).

## Functional review checklist

This is a test-only change, so the manual check is to run the flows below and confirm the expected results. Every flow runs offline: no network, no forge, no real `gh`, `claude`, `codex` or `ssh`, and nothing writes inside the product clone. The automated verification (the nine suites, the `tools/docs` and `tools/release` tests, the manager block) was run at the implementation stage and stays current: the shipped files have not changed since the reviewed head `f08ab6e`, and the technical approval is `CURRENT`.

### Setup

- Run from the repository root, on branch `milestone/gate-policy-test-pins`. Use the system `python3` (3.14); `zstd` must be on `PATH`, because `stage-conformance` uses it.
- `S=$(mktemp -d)` is the scratch directory. Every write goes under `$S`. Run Python with `-B` so that no `__pycache__` lands in the repository.
- Stage the fixture once, from `HEAD`: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"`. Flows F4 and F5 run in `$S/fixture/scripts`. Re-stage if `HEAD` moves.

### Test data

None to seed. The suites build their own repositories and fixtures under `$TMPDIR`.

### Flows

- **F1. Scope of the payload change.** `git diff --name-only 774b441 -- payload`. Expected: six paths, the three test files (`workflow_gate_policy_test.py`, `workflow_integration_test.py`, `workflow_state_completion_obligations_test.py`) and the protocol pieces (`workflow_protocol.py`, `workflow_protocol_test.py`, `ORCHESTRATION_PROTOCOL.md`). `git diff --stat 774b441 -- payload` ends with `6 files changed, 167 insertions(+), 16 deletions(-)`.
- **F2. No script behaviour changed.** `git diff --quiet 774b441 -- payload/scripts/workflow_retention.py payload/scripts/workflow_state.py payload/scripts/workflow_gate_policy.py; echo $?`. Expected: `0`.
- **F3. Nothing outside the release source changed.** `git diff --name-only 774b441 -- .claude scripts .workflow-manager .github CLAUDE.md`. Expected: no output.
- **F4. The edited suites pass in the fixture.** `cd "$S/fixture/scripts"`, then:
  - `python3 -B workflow_gate_policy_test.py`: expected `OK` (429 tests). This run took about four minutes here (247.8 s).
  - `python3 -B workflow_state_completion_obligations_test.py RetentionReportUnreadable`: expected `OK`, `Ran 7 tests`. The class holds the new `test_t7`.
  - `python3 -B workflow_integration_test.py TestBundleRevisionSectionsDocumentedForm`: expected `OK`.
- **F5. The new failed-stat test fails on its mutation.** `command cp -r "$S/fixture" "$S/m5"`, then in `$S/m5/scripts`, in `workflow_retention.py`, change the `return True` in the `except OSError:` arm right after `os.stat(name, dir_fd=dirfd, follow_symlinks=False)` in `_can_fail_walk` to `return False`. Run `python3 -B workflow_state_completion_obligations_test.py RetentionReportUnreadable`. Expected: `FAILED (failures=1)`, and the one failure is `test_t7_a_sub_directory_that_cannot_be_examined_is_still_named_by_its_own_path`. The unmutated fixture (`$S/fixture/scripts`) gives `OK`. The other mutations (m1 to m4) are recorded in the plan's D-Pins table; they are optional here.
- **F6. The nine payload suites pass from the fixture.** From `$S/fixture`, run the loop in `docs/RELEASING.md`, "The nine payload suites" (the `suites=$(...)` line with `while read -r suite`). Expected: every suite exits 0.
- **F7. Docs and the Manager block.** `python3 tools/docs/check_docs.py`: expected exit 0 and no output. `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`: expected `ok: 2.29.9 carries a valid manager block that matches the measurement`.
- **F8. The release title agrees with the version change.** `python3 tools/release/release.py check-title "fix: tighten the acceptance-report, removal and bundle tests and add the missing failed-stat retention test" --agree --head f08ab6e`. Expected: `impact=patch`, then `version 2.29.8 -> 2.29.9 (patch) agrees with the title`. Run it on the release commit `f08ab6e`, not on `HEAD`: `HEAD` is a docs commit, and the check refuses there by design.

### Expected results and limits

- Only the test files and the release records change. No script changes, and `#185` point 1 (a code change in `_absent_stored_pr_head`) is not taken; it stays in the issue.
- Not exercised here: the forge (no pull request, no CI, no `workflow-conformance` run), and anything that needs the Manager.
- Not in the offline sandbox, so not part of F1 to F8: the `tools/release` tests (they need the pinned zlib-ng interpreter, see `docs/RELEASING.md`, "Building locally"), `workflow-manager verify .` (needs the release cache), and the reaper orphan check on the new tests (the reaper is a Manager tool, not in this repository).

## Next action

Functional review is the gate now (`AWAITING_FUNCTIONAL_REVIEW`). Run the flows above by hand. Write any findings to `.ai-review/gate-policy-test-pins/feedback/FUNCTIONAL_REVIEW.md`. If testing is clean, run `/accept-milestone`; every checkpoint (CP1 and CP2) is `COMPLETE`, so it is reachable. If testing produces findings, run `/apply-functional-review`.
