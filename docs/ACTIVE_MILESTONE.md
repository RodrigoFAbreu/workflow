# Active Milestone

## Milestone

**Awaiting functional review.** W59: `retention-index-fd-close` (`process`, governing version `2.2`), branch
`milestone/retention-index-fd-close`, roadmap row 52. A `fix:` change that ships as Workflow 2.29.10 (patch). The plan is
`docs/ai-workflow/RETENTION_INDEX_FD_CLOSE_PLAN.md` (revision 2). Requested by RodrigoFAbreu/workflow#181, point 1 only;
point 2 was declined by the owner and is not touched.

## Goal

In `payload/scripts/workflow_retention.py`, `_open_index` closes the index descriptor when its `os.fstat` raises. Before this
change that descriptor leaked in all three flows (`archive` dry run, `archive --apply`, `remove`). Every working path is unchanged;
the surfaced error for a failed stat is the existing `unreadable` refusal.

## Outcome

- CP1 (the descriptor close, its test, roadmap row 52) and CP2 (release 2.29.10) are `COMPLETE`. Implementation head: `2300da7`.
- Implementation review round 1 is `APPROVE` from both the local model stage and the manual external stage. Technical approval
  is recorded by policy (`POLICY_SATISFIED`).

## Functional review checklist

Test the committed content this checklist was written into. The evidence commit's SHA and blob are reported by the
`/prepare-functional-review` run that wrote this section.

### Setup

- Work from a staged copy of the branch, never inside the product clone. Read-only git commands are fine in the clone:
  `S=$(mktemp -d) && git archive HEAD | tar -x -C "$S"`.
- Python 3 standard library only. No network, no real `gh`, `claude`, `codex` or `ssh`. Tests create their own scratch
  repositories under `$TMPDIR`.
- Run the suites from inside the staged tree, as CI does, with `python3 -B`.
- The `tools/release` tests need the pinned zlib-ng interpreter (the Workflow's own build environment). System `python3` lacks
  `zlib_ng`, and then 15 tests fail and 27 error. That is an environment gap, not a defect.

### Test data

None. Each retention test builds its own scratch repository and index.

### Flows

Run each flow from the stated directory. Expected results are the exact output or the stated condition.

| # | Do | Expected |
| --- | --- | --- |
| F1 | `git diff --stat 92ca0f8 -- payload` | 5 files, 64 insertions, 8 deletions: `workflow_retention.py`, `workflow_state_completion_obligations_test.py`, `workflow_protocol.py`, `workflow_protocol_test.py`, `ORCHESTRATION_PROTOCOL.md` |
| F2 | `git diff 92ca0f8 -- payload/scripts/workflow_retention.py \| grep '^[-+][^-+]'` | one removed line `info = os.fstat(fd)`, and the added guard: `try:`, `except BaseException:`, an inner `try: os.close(fd)` with `except OSError: pass`, then `raise`. Nothing else |
| F3 | In `$S/payload/scripts`: `python3 -B workflow_state_completion_obligations_test.py RetentionErrorPathsTwo` | `Ran 19 tests` and `OK` |
| F4 | Same directory: `python3 -B workflow_state_completion_obligations_test.py` | `Ran 318 tests` and `OK` |
| F5 | Failure-only mutation m1, in a scratch copy only: in `_open_index`'s guard, drop the `os.close(fd)` so the arm reads `except BaseException: raise`. Run the class `RetentionErrorPathsTwo` | Exactly `test_t7a2_a_failed_stat_of_the_index_closes_its_descriptor` fails, in both subtests (`flow='archive'`, `flow='remove'`), with `Lists differ: [] != [N]` (nothing closed where the failed descriptor `N` should be) |
| F6 | Same mutated copy: the whole suite | `Ran 318 tests`, `FAILED (failures=2)`, and no other test fails |
| F7 | Reaper, from the Manager checkout: `python3 -I -S -B <manager>/tests/parallel/reaper.py --report "$S/R.json" --chunk-id fdclose -- python3 -B "$S/payload/scripts/workflow_state_completion_obligations_test.py" RetentionErrorPathsTwo` | status 0; orphans only `[git]` helpers, all `exited`. The reaper lives in the Manager checkout, not in this repository |
| F8 | Conformance: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"`, then run the nine suites named by `manifest.json`'s `manager.conformance.suites` from `$S/fixture/scripts`, one per line, under bash, each with `python3 -B` and `</dev/null` | All nine exit 0 |
| F9 | `python3 -m unittest discover -s tools/docs -p '*_test.py'` and `python3 tools/docs/check_docs.py` | `Ran 34 tests` and `OK`; the checker exits 0 |
| F10 | `tools/release` tests with the pinned zlib-ng interpreter: `<pinned-python> -m unittest discover -s tools/release -p '*_test.py'` | `Ran 383 tests` and `OK` |
| F11 | `python3 tools/release/release.py check-title "fix: close the retention index descriptor when its stat fails" --agree --head 2300da7` | `impact=patch` and `version 2.29.9 -> 2.29.10 (patch) agrees with the title` |
| F12 | `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | `ok: 2.29.10 carries a valid manager block that matches the measurement` |
| F13 | `git diff --name-only 92ca0f8 -- .claude scripts .workflow-manager .github CLAUDE.md` | no output |

### Known limitations and out of scope

- #181 point 2 (the `_remove_tree` wording) is declined by the owner and not touched.
- No behaviour changes. The refusal order, messages and exit codes of `_open_index` and its three callers are byte-identical.
- A created index stays on disk when the stat fails, as it does today. The surfaced error is still `error: unreadable` with
  `unexpected I/O error: EIO`.
- A failing `os.close` in the new arm is swallowed on purpose, so the original error is re-raised.
- The interrupt path between the open and the stat (`BaseException`) is not driven by any test. The stated limit of the plan.
- `workflow-manager verify .` (a CP2 verification) is not part of this checklist. It needs the release cache.
- Release 2.29.10 is not published by this checklist. The release workflow and the Manager pull requests follow the merge.

## Next action

Manual functional testing of this checklist. Findings go to `.ai-review/retention-index-fd-close/feedback/FUNCTIONAL_REVIEW.md`.
Once testing is clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint in this item's registry
to be `COMPLETE`, which CP1 and CP2 already are.
