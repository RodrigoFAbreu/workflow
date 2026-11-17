# W55: Workflow 2.29.7 — the missing retention test pins: the future-mtime clamp, the default forge runner, a failed read, same-size altered bytes and the removal's two re-checks (Revision 1)

Pull request title: `fix: add the missing retention tests for the future-mtime clamp, the default forge runner, a failed read, same-size altered bytes and the removal re-checks`
(a `test:` title cannot be used: see D-Release; the version change is the next patch, so the title's impact must be patch).

- **Work item:** `retention-test-pins` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner standing order (queue the reviewed follow-ups when the queue is empty; reviewed against
  `origin/main` `5fe44bb` on 2026-11-16): row 48 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#113 point 5, #116 point 2 and #119 point 4 (the test-pin half), each read with all its comments.
  **Branch:** `milestone/retention-test-pins`
- **Base commit:** `5fe44bbef43e7b5d47950a79d0c805542e9bb0d2` (main after #184: the release source is 2.29.6; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. One mechanism: add the missing tests, change no behaviour. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: each point on main at `5fe44bb`

R is `payload/scripts/workflow_retention.py`, T is `payload/scripts/workflow_state_completion_obligations_test.py`. Run in a staged fixture
(`release.py stage-conformance --commit HEAD`, real `zstd`, Python 3.14, no forge, no network; scratch under `$TMPDIR`, outside the repository).
"Existing" is the six retention classes (`RetentionReport`, `RetentionReportUnreadable`, `RetentionArchive`, `RetentionRemove`, `RetentionPrune`,
`RetentionErrorPathsTwo`: 115 tests, all green on main). Each mutation was applied to a copy of R in the fixture, one at a time, and every one is
**failure-only**: it changes behaviour only on the path the new test drives.

| Point | State on main (file:line) | Class | Existing tests under the mutation |
| --- | --- | --- | --- |
| #113 5a, future mtime | R 366 `age = max(0, int(... // 86400))`; T `_RR.archive` (3761) is called only with positive ages (3961 to 3969, 3991, 4008). m1: drop the `max(0, ...)` | TRUE-GAP | 115 green |
| #113 5b, `build_report` without `run` | R 374 to 375 passes `run` to the forge only `if run is not None`; every T call passes it (`build` 3749, 4213, 6379). m2: pass `run` unconditionally (`None` is then called, the query becomes `query_failed:unexpected`) | TRUE-GAP | 115 green |
| #116 2a, a failed `os.read` after a successful open | R 773 to 775: the `_Hashing.read` error is `unreadable` with next step "repair it; the engine does not archive from a partial view"; T has `EIO` injections only for `readlink`, `stat`, `fstat` and `fsync`, and the open-error branch (5204). m3: `if source.error is not None:` becomes `if False:` (the run then ends `folder_changed` "changed size while it was read") | TRUE-GAP | 115 green |
| #116 2b, altered bytes with equal names, types and sizes | R 891 `digest.hexdigest() != record["sha256"]`; T 5231 to 5247 use truncated or one-byte streams that fail on names or sizes. m4: drop the digest test | TRUE-GAP | 115 green |
| #119 4c, the stat-only re-check after hashing | R 1912 `_scan` against the hashed records, then `folder_changed` "the folder changed while it was verified". T covers only a failing `readlink` inside that `_scan` (6089, 6128). m5: drop the whole condition (`if False:`) fails those two tests, so it is **not** the right mutation; m5b keeps the `_scan` call and drops the comparison | TRUE-GAP (the comparison); the call is already covered | m5: 2 red (`test_w37_t5`, `test_w37_t5c`); **m5b: 115 green** |
| #119 4c, the selection repeated under the lock | R 1838 `again = _select_removal(...)`; T 8001 (`test_t5_the_lock_recheck_says_folder_changed_and_moves_nothing`, three state changes) and `test_w33_t3` (a stat error) already cover the repeat. m6: `again = sel` | ALREADY-COVERED for a state change; one case is missing: a refusal only the repeated selection yields (the archive vanishes after the lock) | m6: red (T 8001, `test_w33_t3`) |

No point is false or obsolete. The other points of the three issues are out of scope (their state is in the issues' status comments). No defect was found
by any pin (D-Stop). The archive's own stat-only re-check (R 1287) is not in the points and is not touched.

## 1. Goal and scope

Six tests, all added to T as one class, `RetentionTestPins`; no line of R or of any other payload file changes, and no existing test changes.
Out of scope: any behaviour, the documents, the retention pages, the Manager and the Controller. This repository's own installation (`.claude/`, `scripts/`,
the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance workflow) stays untouched; the file under `payload/` changes.

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page), and the one judgment made, that a test-only change is a `fix:` release, is D-Release.

## 2. Design

### D-Tests (class `RetentionTestPins` at the end of T; `skipUnless` the `zstd` program, like its neighbours)

| Test | Drives | Asserts | No-write proof | Failure-only mutation |
| --- | --- | --- | --- | --- |
| `test_p1_an_archive_dated_in_the_future_reports_age_zero_and_is_never_prunable` | two archives dated one hour and forty days ahead (`rr.archive(name, -3600)`, `-40 * 86400`) | each `age_days == 0`, `present`, `prunable` false, in `finished` and in `archives` | the snapshot of the repository and the archive root is equal before and after | m1 (one hour gives `-1`, forty days `-40`) |
| `test_p2_build_report_without_run_uses_the_forge_default_runner` | `wr.build_report` with no `run`, `workflow_forge.query_forge_pr_facts.__kwdefaults__["run"]` patched to a recording stand-in | six queries through the stand-in, none through the fixture's runner, nothing `query_failed` | the same snapshot | m2 |
| `test_p3_a_read_that_fails_after_a_successful_open_is_unreadable_and_nothing_is_kept` | `os.open` records the descriptor of `a.txt`, `os.read` of it fails once with `EIO` | code `unreadable`, message `a.txt cannot be read (Input/output error)`, next step exactly "repair it; the engine does not archive from a partial view" (differs from the open-error "grant read access") | `rr.snap` of repository and archive store and the folder snapshot equal before and after (no archive, no `.partial`, no index line) | m3 |
| `test_p4_an_archive_whose_bytes_differ_with_names_types_and_sizes_equal_is_not_kept` | a `zstd` stand-in that, in compress mode, re-writes the tar with the first byte of every non-empty file flipped (same names, types and sizes) and compresses it with the real program; `-dc` is the real one | code `verify_failed`, message has "differs in content" | the same equal snapshots | m4 |
| `test_p5_a_stat_only_change_after_the_hash_puts_the_folder_back_and_deletes_nothing` | `remove --apply` with `_archive_table` wrapped: after the real call it moves the modification time of `.removing/w00/a.txt` by five seconds (bytes and size unchanged) | code `folder_changed`, message "the folder changed while it was verified" ending `; the folder is back in <.ai-review/w00>`, two renames (out and back), `.removing/w00` gone | the folder's kinds, link targets and hashes equal before and after; nothing deleted | m5b |
| `test_p6_the_selection_is_repeated_under_the_lock_and_its_own_refusal_stops_the_run` | `_hook_after_flock` deletes the archive file right after the exclusive lock | code `not_archived` ("has no verified archive"), no rename at all, the folder still in place, `.removing/w00` absent | the same | m6 |

The mutations, each one edit of one copy of R (old line to new line; R line numbers of the base):

| m | R | old | new |
| --- | --- | --- | --- |
| m1 | 366 | `age = max(0, int((now - modified).total_seconds() // 86400))` | `age = int((now - modified).total_seconds() // 86400)` |
| m2 | 374 to 375 | `if run is not None:` / `kwargs["run"] = run` | `kwargs["run"] = run` |
| m3 | 773 | `if source.error is not None:` | `if False:` |
| m4 | 891 | `if count != record["size"] or digest.hexdigest() != record["sha256"]:` | `if count != record["size"]:` |
| m5b | 1912 | `if [_comparable(r) for r in _scan(removing_fd, item_id)] != [_comparable(r) for r in records]:` | `_scan(removing_fd, item_id)` then `if False:` |
| m6 | 1838 | `again = _select_removal(repo_root, item_id, archive_root, now, run, resolve, zstd, fds)` | `again = sel` |

Measured on the branch's tree in the staged fixture (D-Staging): unmutated, the six pass; under each mutation exactly the one test of its row fails and nothing
else in the class; the existing classes' results are the table of section 0. The six also run under the Manager's orphan rule: 6 re-parented `[git]` helpers, all
`exited`, nothing else. A test that cannot fail without its mutation is not accepted: CP1's author re-runs the six mutations and records each result.

### D-Stop

If any pin fails on unmutated R, or a mutation does not fail its test, **stop**: a real defect is recorded as a finding (a separate fix item); R is not changed here.

### D-Release

The pull request changes a shipped file: T is a manifest artifact (`distribution`, `target_path` `scripts/workflow_state_completion_obligations_test.py`) and the conformance
suite the installed repositories run. `docs/RELEASING.md` ("A published version never changes", "A pending version is frozen until published") refuses a release-source change
without a version change (2.29.6 is published, so `check-pending` needs the bump and `check-immutable` needs it too), and the required `Conventional Commit title` check requires the
title's impact to equal the version change (`check-title --agree`: "a patch change needs a title of patch impact"; `check-title "test: ..."` prints `impact=none`, `fix: ...` prints `impact=patch`).
So the change is **a release, Workflow 2.29.7, a `fix:` patch**, the precedent of the earlier test-and-wording polish (2.25.2): the title is `fix:`, not `test:`, and the Controller's classification
follows the manifest's version change. `manifest.json` `workflow_version` 2.29.7; the four changed records (T, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`) take their sentence, `sha256` and
`size`; counts and `distribution` do not move; `manager.conformance.suites` is measured by `release.py manager-block --write` (the obligations suite 308 to 314). `WORKFLOW_RELEASE` becomes 2.29.7 with its
pinned assertions and the document's lines (protocol 1.5). The posture says the way back to 2.29.6 needs nothing undone (tests only). `tools/release/release_test.py` gets a 2.29.7 class, carries the suite-count pin,
and the 2.29.6 class gives up the pins a newer release owns. `docs/release-history.md`: the 2.29.7 row and its stamp. The release workflow publishes it; the Manager lock and install pull requests follow (orchestrator).

### D-Staging

CP1 changes a shipped file whose record moves only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w55-tmp` (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging):
a scratch script, in the clone only, (a) recomputes `sha256` and `size` of the record whose file differs (T), (b) measures `manager.conformance.suites` with `release.py manager-block --release-dir <scratch> --write`,
(c) rewrites the one pin that reads the counts in `tools/release/release_test.py` (the obligations count, as the lstat-errors plan did); that pin is CP2's change in the real tree. Then the "Verification commands" of
`docs/RELEASING.md` run from the clone (the tools tests with the zlib-ng interpreter), and the new tests also run under the reaper.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The six pins and roadmap row 48 | - | 2 | 1 |
| CP2 | Release 2.29.7 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The six pins and roadmap row 48

**Files:** `payload/scripts/workflow_state_completion_obligations_test.py`, `docs/ROADMAP.md`.

- D-Tests as code in T: the class `RetentionTestPins`, six tests, no existing test touched; the six mutations of D-Tests run in a scratch copy of R, each result recorded. `docs/ROADMAP.md` carries row 48 (`Current`) from this plan.
- No other file of `payload/` changes: `git diff 5fe44bb --stat -- payload` lists T only, and `git diff 5fe44bb -- payload/scripts/workflow_retention.py` is empty.

**Verification:** D-Staging (nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` in the zlib-ng interpreter; the new tests under the reaper); the mutations fail their tests only.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.7

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` 2.29.7 with its pinned assertions and the document's matching lines (protocol 1.5); `manifest.json` per D-Release; the history row and stamp; the 2.29.7 class and the 2.29.6 class's given-up pins.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; the tools tests pass in the zlib-ng environment;
`check-title "<the title above>" --agree` agrees; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 4. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Nothing runs against the real repository, the forge or the network. `$S` is a scratch directory under `$TMPDIR`; `base/` is `git archive 5fe44bb payload` extracted there; `cand/` a copy of the working tree's `payload`.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --stat 5fe44bb -- payload`, `git diff --quiet 5fe44bb -- payload/scripts/workflow_retention.py; echo $?` | CP1: the test file only; `0` (R identical). CP2 adds the protocol script, its test and the protocol document |
| 2 | `git diff 5fe44bb -- payload/scripts/workflow_state_completion_obligations_test.py \| grep -c '^-[^-]'` | `0`: only lines were added |
| 3 | in a staged fixture, `python3 -B workflow_state_completion_obligations_test.py RetentionTestPins` | 6 tests OK |
| 4 | the six mutations of D-Tests on a copy of R in the fixture, the class after each | m1 to m4, m5b, m6: exactly the test of its row fails |
| 5 | the same mutations against the six existing classes | m1 to m4, m5b green; m5 and m6 red (they were already covered); the table of section 0 |
| 6 | `reaper.py --report R.json --chunk-id pins -- python3 -B <T> RetentionTestPins` | status 0; orphans: only `[git]`, all `exited` |
| 7 | (full environment) the nine payload suites from a staged fixture; the `tools/release` tests with the zlib-ng interpreter; `tools/docs` tests and checker; `check-manager-block` with `--manager-releases` | all pass; the manifest says 2.29.7; `check-title` agrees |
| 8 | `git diff --name-only 5fe44bb -- .claude scripts .workflow-manager .github CLAUDE.md` | nothing |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #113 5a future mtime | `test_p1`, m1 | CP1 | |
| #113 5b no `run` | `test_p2`, m2 | CP1 | |
| #116 2a failed read | `test_p3`, m3 | CP1 | |
| #116 2b altered bytes | `test_p4`, m4 | CP1 | |
| #119 4c stat-only re-check | `test_p5`, m5b | CP1 | the call was covered, the comparison was not |
| #119 4c selection under the lock | `test_p6`, m6 | CP1 | the state-change cases were covered (T 8001) |
| Release | 2.29.7, a `fix:` patch | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-test-pins-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand for `payload/`, `tools/`, `fixtures/`, `templates/`,
`manifest.json` and `docs/release-history.md` (excluded at the plan stage, protected at the implementation stage); every path a checkpoint's **Files** paragraph names is classified at both stages. `docs/ROADMAP.md` stays excluded at both stages
(acceptance edits it after the technical approval), so row 48 is a classified, unprotected change.
