# Active Milestone

## Milestone

**Awaiting functional review.** W22: `checkpoint-start-engine` (`process`, governing version `2.2`), branch
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

## Next action

The user performs the functional review in the checklist below and places findings at
`.ai-review/checkpoint-start-engine/feedback/FUNCTIONAL_REVIEW.md`. Clean testing leads to `/accept-milestone`, the
only acceptance command; it needs every checkpoint `COMPLETE` (CP1 and CP2 are). Findings go to
`/apply-functional-review`: a same-scope fix takes its bounded branch, anything wider a
`checkpoint-start-engine-remediation-<n>` child work item.

## Functional review checklist

Scope: `release_checkpoint_start`, the release engine of Workflow 2.18.7, on the release source. The repository's
own installation stays at 2.18.6, so test the staged fixture, not `scripts/`. Nothing calls the function and no
command exposes it, so there is no screen or command to click through. The review asks two things: does the
engine behave as invariant I1 of `docs/ai-workflow/CHECKPOINT_START_ENGINE_PLAN.md` says, against scratch
repositories and real processes; and is the documented residual acceptable.

### Setup

Work only in a scratch directory. The product clone is read-only: it is cloned, never written to. The clone is the
branch tip, which is the checklist-evidence commit named in the report.

```bash
SCR=$(mktemp -d)
export HOME=$SCR/home TMPDIR=$SCR/tmp XDG_CONFIG_HOME=$SCR/xdg-config XDG_CACHE_HOME=$SCR/xdg-cache XDG_DATA_HOME=$SCR/xdg-data
mkdir -p "$HOME" "$TMPDIR" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME" "$SCR/out"
git clone -q --no-hardlinks --branch milestone/checkpoint-start-engine /home/rodrigo/Workspace/workflow "$SCR/clone"
cd "$SCR/clone" && PYTHONDONTWRITEBYTECODE=1 python3 tools/release/release.py stage-conformance --commit HEAD --out "$SCR/fixture"
```

Test data: nothing to seed. Each flow builds its own scratch repository through the suite's harness, or runs its own
real child processes. F5(b) and F5(d) also need the provisioning named there.

Every flow in F1 to F3 and F6 runs offline: no network, and no `gh`, `claude`, `codex` or `ssh`. Expected output is
`OK`; any other output is a finding.

### Flows

**F1: a start is released, nothing is committed, and the old owner is refused afterwards** (plan f1; T1, T6).

```bash
cd "$SCR/fixture/scripts" && PYTHONDONTWRITEBYTECODE=1 python3 -B workflow_state_test.py \
  TestReleaseCheckpointStart.test_t1_success_restores_the_committed_entry_and_removes_the_claim \
  TestReleaseCheckpointStart.test_t6_the_old_owner_cannot_write_after_the_release -v
```

- Expected: `Ran 2 tests`, `OK`. T1 checks that the entry is restored to what `HEAD` records (absent, or the demoted
  `NEEDS_REVALIDATION` entry), that the claim and the guard are gone, that `HEAD` and the working files are untouched,
  and that nothing is staged. T6 checks that an owner holding the old token is refused after the release and that its
  body never runs.

**F2: an interrupted release is finished by the next call, and a commit since the start refuses** (plan f2; T4, T2,
T11).

```bash
cd "$SCR/fixture/scripts" && PYTHONDONTWRITEBYTECODE=1 python3 -B workflow_state_test.py \
  TestReleaseCheckpointStart.test_t4_a_crash_at_each_step_is_finished_or_refused_by_the_next_call \
  TestReleaseCheckpointStart.test_t2_a_commit_since_the_start_refuses_and_an_unrelated_one_does_not \
  TestReleaseCheckpointStart.test_t11_a_demoted_checkpoint_that_was_restarted -v
```

- Expected: `Ran 3 tests`, `OK`. T4 kills a release at each seam with `os._exit` in a real process, asserts the exact
  residue, and checks that the next call completes or refuses `nothing to release`. T2 checks that a commit carrying the
  checkpoint's trailer since the start refuses, and that an unrelated commit does not block. T11 covers a demoted
  checkpoint that was restarted.

**F3: a live owner is not overtaken, and two releases never overlap** (plan f3; T3, T5).

```bash
cd "$SCR/fixture/scripts" && PYTHONDONTWRITEBYTECODE=1 python3 -B workflow_state_test.py \
  TestReleaseCheckpointStart.test_t3_a_live_owner_is_not_overtaken \
  TestReleaseCheckpointStart.test_t5_two_concurrent_releases -v
```

- Expected: `Ran 2 tests`, `OK`. T3 parks an owner in `1f-commit`: the release is refused with the running-window
  message and the owner's guard is untouched; once the owner ends, the release succeeds. T5 checks that a second
  concurrent release blocks behind the lifecycle lock and refuses without entering a window.

**F4: the state suite leaves no orphan process under the Manager's reaper** (plan f4; #95). Needs the reaper of a
`workflow-manager` checkout, `<wm>/tests/parallel/reaper.py`, which lies outside the product clone and must be readable
in the sandbox. The four `GIT_CONFIG_*` settings are the Manager's own quiet-Git layer (`THROWAWAY_GIT_CONFIG` in
`src/workflow_manager/fixture.py`): they stop Git's detached auto-maintenance from outliving the chunk.

```bash
cd "$SCR/fixture/scripts" && export GIT_CONFIG_COUNT=4 GIT_CONFIG_KEY_0=maintenance.auto GIT_CONFIG_VALUE_0=false \
  GIT_CONFIG_KEY_1=gc.auto GIT_CONFIG_VALUE_1=0 GIT_CONFIG_KEY_2=maintenance.autoDetach GIT_CONFIG_VALUE_2=false \
  GIT_CONFIG_KEY_3=gc.autoDetach GIT_CONFIG_VALUE_3=false
PYTHONDONTWRITEBYTECODE=1 python3 -I -S -B <wm>/tests/parallel/reaper.py \
  --report "$SCR/out/reaper-state.json" --chunk-id workflow_state_test -- python3 -B workflow_state_test.py
```

- Expected: the suite ends `OK (skipped=1)`, and `$SCR/out/reaper-state.json` has `"supported": true`,
  `"chunk_status": 0` and `"orphans": []`. Without the four settings the same run reports about 2,700 orphans, all
  Git processes with an empty command line or `git maintenance run`; that is the reason for the settings, not a defect
  of the engine.

**F5: the verification suites from the staged fixture** (plan f5; the commands of `docs/RELEASING.md`,
"Verification commands").

(a) The nine suites. Each must exit 0. The round-3 record (`.ai-review/checkpoint-start-engine/current/TEST_RESULTS.md`
in the product clone, read only) ran `workflow_state_test.py` 1227 times with `OK (skipped=1)`.

```bash
cd "$SCR/clone" && suites=$(python3 -c "import json; print(*json.load(open('manifest.json'))['manager']['conformance']['suites'], sep='\n')") && test -n "$suites" && ( cd "$SCR/fixture/scripts" && while read -r suite; do PYTHONDONTWRITEBYTECODE=1 python3 -B "$SCR/fixture/scripts/$suite" </dev/null || exit 1; done <<< "$suites" )
```

(b) The `tools/release` tests and the build need the pinned compression runtime. Provision a Python 3.12 venv with
`tools/release/deflate-requirements.txt` (`zlib-ng` 2.2.5) as `docs/RELEASING.md`, "Building locally", describes, and
set `VENV` to it. Without it, the build refuses with `zlib_ng is not installed`, and the tests fail on system Python.

```bash
cd "$SCR/clone" && PYTHONDONTWRITEBYTECODE=1 "$VENV/bin/python" -m unittest discover -s tools/release -p '*_test.py'
PYTHONDONTWRITEBYTECODE=1 "$VENV/bin/python" tools/release/release.py build --commit HEAD --out "$SCR/build"
```

- Expected: `Ran 269 tests`, `OK`; the build exits 0 and prints its tar, archive and manifest digests.

(c) The docs and the Manager metadata block:

```bash
cd "$SCR/clone" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/docs -p '*_test.py'
PYTHONDONTWRITEBYTECODE=1 python3 tools/docs/check_docs.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json
```

- Expected: `Ran 34 tests`, `OK`; `check_docs.py` exits 0; `check-manager-block` prints
  `ok: 2.18.7 carries a valid manager block that matches the measurement`.

(d) The installation. It must match the release this repository records, 2.18.6. Offline it needs the release cache:
with an empty cache and no reachable release source it exits 1 with `error: cannot fetch`, which is a stop, not a
pass (`docs/RELEASING.md`, "Verification commands"). The `workflow-manager` binary must be on `PATH`.

```bash
cd "$SCR/clone" && WORKFLOW_MANAGER_RELEASE_CACHE=<cache> workflow-manager verify .
```

- Expected: `.: installation matches workflow 2.18.6`.

**F6: the documents say what the code does** (plan f6). A reading check, not a command.

- `docs/CONCURRENCY_INVARIANTS.md`, the row "Checkpoint-start release window": it states I1, the lock order
  ((9)→(6)→(5), (5)→(2) by `state_transaction`, (5)→(6) at release), the residue table, and the demoted case, which
  makes `discover_checkpoint_commits` raise `AmbiguousCheckpointTrailerError`, with no recovery in this release. The
  #55 gap is narrowed, not closed.
- `docs/release-history.md`, the 2.18.7 row: it closes #95, leaves #55 open for the command, and states the way back.
- Expected: no sentence claims a command or a recovery that the code does not have.

### Known limitations (out of scope for this milestone)

- No command calls `release_checkpoint_start`. `/request-plan-amendment` is still wedged by an uncommitted start until
  row 24c adds the command. Nothing calls the function, so no installed behaviour changes.
- **Accepted residual** (D-Residual, OD-3). An interruption leaves the owner unfenced until the next call. In the
  demoted, restarted case the owner's completion commits `COMPLETE` with the old `start_commit`, and that checkpoint
  then raises `AmbiguousCheckpointTrailerError`. There is no recovery in this release. Row 24c must close it, or check
  that the owner is stopped, before a command calls the function.
- Non-blocking, documentation (EIR-001): a crash while an old guard is reclaimed, between deleting it and publishing its
  replacement, leaves the claim and the restored entry with no guard. The next call still completes the release safely.
  The release-window row does not state this case yet.
- Non-blocking, metadata (EPR-002, OPT-003): `docs/ai-workflow/CHECKPOINT_START_ENGINE_PLAN.md:14` still reads
  "Plan revision: 3". It is a plan-stage path, so it is left for an amendment.

### Reporting findings

Place findings at `.ai-review/checkpoint-start-engine/feedback/FUNCTIONAL_REVIEW.md`.
