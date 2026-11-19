# W59: Workflow 2.29.10 — the retention index descriptor is closed when its stat fails (Revision 2)

Pull request title: `fix: close the retention index descriptor when its stat fails`
(a shipped script changes, the behaviour of every working path does not: the version change is the next patch, so the title's impact must be patch; see D-Release).

- **Work item:** `retention-index-fd-close` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner standing order: row 52 of `docs/ROADMAP.md` (`Current` from CP1, `Done` from CP2, the last checkpoint).
- **Issue:** RodrigoFAbreu/workflow#181 point 1 only, read with all its comments (the issue has **none**; its body is the whole record). Point 2 was declined by the owner and is not touched.
  **Branch:** `milestone/retention-index-fd-close`
- **Base commit:** `92ca0f8dacb35679a20f2fff9db9f7334f605718` (main after #203: the release source is 2.29.9; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2 (round 1 of the local plan review applied: the close assertion is bound to the failed stat; see D-Test). One mechanism, one code path, one fix: close the descriptor on every exit path after a successful open. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: point 1 on main at `92ca0f8`

R is `payload/scripts/workflow_retention.py`, T is `payload/scripts/workflow_state_completion_obligations_test.py`.

| Claim of #181 point 1 | State on main (file:line) | Class |
| --- | --- | --- |
| `_open_index` leaves its descriptor unclosed when `os.fstat` raises | R 1008 to 1037 (the brief's ~1038 is R 1033 on this base). The open is the inner `try` (R 1016 to 1022: `os.open`, and on `FileNotFoundError` with `create` the `O_CREAT | O_EXCL` open); the outer `except` clauses (R 1023 to 1032) cover only the **open**. R 1033 `info = os.fstat(fd)` is outside any `try`. R 1034 to 1036 closes the descriptor only in the not-an-ordinary-file branch (`os.close(fd)` then `_index_unsafe`). When `os.fstat` raises, `fd` is lost: it is a local, and the caller has not stored it yet | TRUE |
| the callers cannot compensate | `_judge_archive_side` (R 1047) and `_judge_removal_archive` (R 1677) close `fd` in a `finally`, but only for a descriptor `_open_index` **returned**. `_flow` step 3 (R 1324 to 1325) stores the returned descriptor in `state["index_fd"]` first and `_undo` closes it from there, again only for a returned descriptor. So the raise leaks the descriptor in all three flows (dry run `archive`, `archive --apply` with the index created or appended, `remove`) | TRUE |
| what the user sees today | T 8112 `test_t7a_archive_turns_a_stray_oserror_into_unreadable` fails `os.fstat` inside `_open_index` (`_call_fails("fstat", "_open_index", errno.EIO)`, T 7801) and pins the surface: exit 2, `error: unreadable`, `archive stopped on an unexpected I/O error: EIO`, `next step: the review folder was not touched`, only an empty `index.jsonl` added. The `OSError` is not caught in `_open_index`, so the engine's one backstop (the decorator at R 570 to 586, which turns an `OSError` into the `unreadable` refusal) names it. `remove` has the same backstop (`remove stopped on an unexpected I/O error: EIO`, T 8130, which fails `fstat` at three other sites but not at `_open_index`). No test observes the descriptor | TRUE (the surface is pinned, the leak is not) |

No point is false or obsolete. Point 2 of the issue (the `_remove_tree` wording) is out of scope by the owner's decision. No defect beyond the leak was found; D-Stop applies to the measurements of CP1.

## 1. Goal and scope

One fix in one function and one new test. Out of scope: any behaviour; the refusal order, the messages and the exit codes of `_open_index` and of its three callers (byte-identical); the other `os.fstat` calls of R (each of them is on a descriptor a `try`/`finally` or `_undo` already owns, or is outside this point); point 2 of #181; every page and command file.
This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance workflow) stays untouched.

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page).
The one judgment made is how a failing `os.close` in the new path behaves (D-Fix), and that a script fix with no visible change is still a release (D-Release).

## 2. Design

### D-Fix

In R `_open_index`, only the `os.fstat` line moves into a guard; the rest of the function, including its `not S_ISREG or st_nlink != 1` branch, its `os.close(fd)` there and its `_index_unsafe` text, stays as it is:

```python
    try:
        info = os.fstat(fd)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        raise
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        os.close(fd)
        raise _index_unsafe("is not an ordinary file with exactly one link")
    return fd, created
```

- One principle: after a successful open, the descriptor is closed on every path that does not return it. `BaseException` (not `OSError`) so that an interrupt between the open and the stat does not leak either; the original exception is re-raised unchanged, so the backstop reports exactly what it reports today (`unreadable`, "unexpected I/O error: EIO", the same next step).
- The close in the new arm is best effort: a failing `os.close` there must not replace the error being reported (the descriptor is released by the kernel on every `EIO` or `EINTR` of `close(2)` on Linux, and nothing more can be done with it). The existing close in the not-an-ordinary-file branch is deliberately left as it is, so that branch stays byte-identical.
- A created index (`create=True` and the file did not exist) stays on disk when the stat fails, exactly as today (T 8112 pins "only the empty index"): nothing about what is kept or removed changes.
- Behaviour that cannot change: the open's own refusals (R 1023 to 1032), the order (open, stat, link-count and type check), the return value, and the three callers.

### D-Test (one new test, no existing test touched)

`RetentionErrorPathsTwo.test_t7a2_a_failed_stat_of_the_index_closes_its_descriptor` in T, directly after `test_t7a_archive_turns_a_stray_oserror_into_unreadable` (the neighbouring index-open test, same class, same fault-injection helper `_call_fails`, same environments `ra_env` and `rm_env`). Two `subTest`s, one per flow whose `_open_index` is reached by a different mode (`archive --apply`: write and create; `remove --apply`: read):

1. a local `_open_fds()` helper lists `/proc/self/fd` as `{number: readlink}` (excluding the descriptor of the listing itself); the test needs `/proc` (`skipUnless`). The module already has `_fd_count()` (T 6031, a bare count used by the archive and removal tests); it is not reused because a count cannot name which file survived and is fooled by one close and one open cancelling out, so the map is the stronger evidence here and the helper is not a near-duplicate;
2. `os.close` is patched with a recorder that calls the real one and appends its argument to `closed` **only when the caller's frame is `_open_index`** (`sys._getframe(1).f_code.co_name == "_open_index"`, the test `_call_fails` uses), and `_call_fails("fstat", "_open_index", errno.EIO)` fails the stat of the index descriptor; `counted` holds that descriptor. Descriptor numbers are reused and an unrelated close earlier in the run can carry the index descriptor's number, so a membership test over every close of the engine call would pass vacuously; the frame-bound record holds only closes made by `_open_index` itself, and on this path the only such close is the new guard's (the not-an-ordinary-file branch is not reached);
3. the descriptors are compared before and after the engine call: **(a)** `closed == counted` (the one descriptor whose stat failed was closed by `_open_index`) and the open descriptors after the call equal those before (no `index.jsonl` descriptor survives); **(b)** the surfaced error is the engine's existing one for a stray I/O error at that point: exit 2, `error: unreadable`, `archive stopped on an unexpected I/O error: EIO` (resp. `remove stopped on an unexpected I/O error: EIO`) in stderr, and for `archive` also `next step: the review folder was not touched`; no new refusal code or message is introduced (D-Fix keeps the original exception);
4. **no-write proof for the failure path:** the archive subtest compares `rr.snap(times=False)` with its before as T 8112 does (only an empty `index.jsonl` added, every other entry equal; the run is then repeatable: `rr.call("w00", apply=True).code == 0`), the remove subtest requires `rr.snap(times=False)` equal to its before and `rr.rm(apply=True).code == 0` afterwards.

**Failure-only mutation (m1):** in a scratch copy of R, drop the new guard's `os.close(fd)` (the `try`/`except OSError`/`pass` block becomes `pass`). Unmutated: the new test passes; under m1 the new test fails in **both** subtests on each half of assertion (a) on its own: `closed` is empty where `counted` holds the descriptor (`closed == counted` fails), and the open-descriptor map after the call has one more entry, `index.jsonl`, than before and **no other test** of the nine suites fails, in particular `test_t7a` and the six retention classes stay green (they never observed the descriptor), which is the gap the test closes. m2 (the guard narrowed to `except OSError`) is not required to fail: the interrupt path is not driven; it is recorded as a stated limit.

The new test also runs under the Manager's orphan rule (the reaper): `reaper.py` on the class `RetentionErrorPathsTwo` (re-parented `[git]` helpers only, all `exited`).
The test counts: T moves by exactly one (317 to 318); every other suite stays.

### D-Stop

If the new test fails on the fixed tree, if m1 does not fail it, or if any existing test changes its result with the fix, **stop**: a requirement that cannot be met without changing behaviour beyond the descriptor close is recorded as a finding in this plan (a separate item) and no further code is changed here.

### D-Release

The pull request changes shipped files: R and T are manifest artifacts (`distribution`) and the conformance suite the installed repositories run. `docs/RELEASING.md` ("A published version never changes", "A pending version is frozen until published") refuses a release-source change without a version change, and the required `Conventional Commit title` check requires the title's impact to equal the version change (`check-title --agree`; `fix:` prints `impact=patch`). So the change is **a release, Workflow 2.29.10, a `fix:` patch**, the precedent of 2.29.7, 2.29.8 and 2.29.9.
`manifest.json` `workflow_version` 2.29.10; the five changed records (R, T, `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`) take their sentence ("retention-index-fd-close (workflow-2.29.10)"), `sha256` and `size`; counts of files and `distribution` do not move; `manager.conformance.suites` is measured by `release.py manager-block --write` (the obligations suite 317 to 318). `WORKFLOW_RELEASE` becomes 2.29.10 with its pinned assertions and the protocol document's matching lines (protocol 1.5, no operation or flag changes). The posture says the way back to 2.29.9 needs nothing undone (a descriptor close and one test: the older script is back, no state, flag or output differs). `tools/release/release_test.py` gets a 2.29.10 class, carries the suite-count pin, and the 2.29.9 class gives up the pins a newer release owns. `docs/release-history.md`: the 2.29.10 row and its stamp; it names the issue by number and not by an internal id (`check_docs`). A pending version is frozen until published: no further release-source change may be added to this branch after its version bump. The release workflow publishes it; the Manager lock and install pull requests follow (orchestrator).
Docs pages: no page describes the descriptor handling, so none changes besides the history row (the 2.29.9 row stays as it is).

### D-Staging

CP1 changes shipped files whose records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under `$TMPDIR` (a new empty directory outside the repository; procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script, in the clone only, (a) recomputes `sha256` and `size` of every record whose file differs (R and T), (b) measures `manager.conformance.suites` with `release.py manager-block --release-dir <scratch> --write`, (c) rewrites the pin in `tools/release/release_test.py` that reads the obligations count (as the lstat-errors plan did); that pin is CP2's change in the real tree. Then the "Verification commands" of `docs/RELEASING.md` run from the clone (the tools tests with the zlib-ng interpreter `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`), and the new test also runs under the reaper. Nothing runs an archive, remove or prune command against a real repository: every retention run of the test uses its own scratch repository.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The descriptor close, its test and roadmap row 52 | - | 2 | 1 |
| CP2 | Release 2.29.10 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The descriptor close, its test and roadmap row 52

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`, `docs/ROADMAP.md`.

- D-Fix as code in R (`git diff 92ca0f8 -- payload/scripts/workflow_retention.py` shows one hunk, the `os.fstat` line guarded; nothing else), D-Test as one new test in T; the mutation m1 run in a scratch copy and its result recorded. `docs/ROADMAP.md` carries row 52 (`Current`) in the style of its neighbours.
- `git diff 92ca0f8 --stat -- payload` lists those two files only.

**Verification:** D-Staging (nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` in the zlib-ng interpreter; the new test under the reaper); m1 fails the new test only.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.10

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`, `docs/ROADMAP.md`.

- `WORKFLOW_RELEASE` 2.29.10 with its pinned assertions and the document's matching lines (protocol 1.5); `manifest.json` per D-Release; the history row and stamp; the 2.29.10 class and the 2.29.9 class's given-up pins; `docs/ROADMAP.md` row 52 becomes `Done` (the last checkpoint), with the release following the merge.
- The title is checked with `python3 tools/release/release.py check-title "fix: close the retention index descriptor when its stat fails" --agree --head <the version-bump commit>`.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; the tools tests pass in the zlib-ng environment; `check-title` agrees; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 4. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Nothing runs against the real repository, the forge or the network. `$S` is a scratch directory under `$TMPDIR`.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --stat 92ca0f8 -- payload` | CP1: the retention script and the obligations suite. CP2 adds the protocol script, its test and the protocol document |
| 2 | `git diff 92ca0f8 -- payload/scripts/workflow_retention.py \| grep '^[-+][^-+]'` | one hunk: the `os.fstat` line inside `try`/`except BaseException` with the best-effort close and `raise` |
| 3 | in a staged fixture, `python3 -B workflow_state_completion_obligations_test.py RetentionErrorPathsTwo` | OK; the class gains one test (the whole suite counts 318) |
| 4 | m1 of D-Test on a scratch copy of R in the fixture, then the nine suites | exactly the new test fails, in both subtests; in each, `closed == counted` fails (`closed` is empty) and the descriptor map after the call holds one more entry (`index.jsonl`) than before; nothing else |
| 5 | `reaper.py --report R.json --chunk-id fdclose -- python3 -B <obligations suite> RetentionErrorPathsTwo` | status 0; orphans: only `[git]`, all `exited` |
| 6 | (full environment) the nine payload suites from a staged fixture; the `tools/release` tests with the zlib-ng interpreter; `tools/docs` tests and checker; `check-manager-block` with `--manager-releases` | all pass; the manifest says 2.29.10; `check-title` agrees |
| 7 | `git diff --name-only 92ca0f8 -- .claude scripts .workflow-manager .github CLAUDE.md` | nothing |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #181 1 | D-Fix, the new test, m1 | CP1 | the one code path |
| #181 2 | not taken | - | declined by the owner; not touched |
| Release | 2.29.10, a `fix:` patch | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-index-fd-close-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand for `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json` and `docs/release-history.md` (excluded at the plan stage, protected at the implementation stage); every path a checkpoint's **Files** paragraph names is classified at both stages.
`docs/ROADMAP.md` stays excluded at both stages, so row 52 is a classified, unprotected change.
