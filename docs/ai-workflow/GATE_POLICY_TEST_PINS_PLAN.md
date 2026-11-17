# W58: Workflow 2.29.9 — the missing gate-policy, removal, failed-stat and bundle-test pins (Revision 3)

Pull request title: `fix: tighten the acceptance-report, removal and bundle tests and add the missing failed-stat retention test`
(a `test:` title cannot be used: see D-Release; the version change is the next patch, so the title's impact must be patch).

- **Work item:** `gate-policy-test-pins` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner standing order (queue the reviewed follow-ups when the queue is empty; reviewed against
  `origin/main` `774b441` on 2026-11-16): row 51 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#185 points 2 to 4, #143 point 3, #149 point 3 and #190 point 4, each read with all its comments.
  **Branch:** `milestone/gate-policy-test-pins`
- **Base commit:** `774b441b01c59436543a9b86bce656f977cc2df6` (main after #199: the release source is 2.29.8; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 3. One mechanism: add or tighten tests, change no behaviour. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: each point on main at `774b441`

G is `payload/scripts/workflow_gate_policy_test.py`, T is `payload/scripts/workflow_state_completion_obligations_test.py`, I is `payload/scripts/workflow_integration_test.py`,
R is `payload/scripts/workflow_retention.py`, S is `payload/scripts/workflow_state.py`, P is `payload/scripts/workflow_gate_policy.py`. Run in a staged fixture
(`release.py stage-conformance --commit HEAD`, real `zstd`, Python 3.14, no forge, no network; scratch under `$TMPDIR`, outside the repository).

| Point | State on main (file:line) | Class |
| --- | --- | --- |
| #185 2, T4 iterates six cases | G 5448 to 5458: the loop is `("ready", "stale", "stalenone", "early", "terminal", "after_query")`. `fixture` (G 5140 to 5172) also builds `stale_changes`, `stale_failed`, `stale_head`, `missing`, `partial`, `invalid`; each was run through `ev.evaluate()` and emits the six requirement ids. The objection branch (`CHANGES_REQUESTED`, failed checks) is built only by `stale_changes` and `stale_failed`. The objection path's requirement *id* `no_standing_pr_objection` is already pinned by other tests (the standing-objection, the changes-request-on-an-earlier-head, the each-requirement-failing-alone, the `require_ci` false, the stale-stored-facts and the T8 latest-run tests), so only the **partition membership** of the ids that path emits is new | TRUE-GAP |
| #185 3, T5's satisfy arm | G 5493 to 5497 calls `ws._acceptance_reachability_blocker(...)` directly. The command is `_satisfy_acceptance_cli` (S 20478), which prints `{"code", "error": "AcceptancePreflightError", "message", "state_changed"}` from `satisfy_acceptance_gate`'s mutator (S 21705 to 21707). Other tests already reach the same raise through a command (G 6165 and the phase tests; G 6319 pins the exact IMPLEMENTING message; G 6603 and G 7216 `work_item_terminal`; the plain-command malformed-state subtests), but none runs the outstanding-checkpoint detail T5 is about | TRUE-GAP |
| #185 4, T3 has no golden of the present-head report | G 5418 to 5424 asserts `ready` and the absence of one blocker; the `--acceptance-gate` stdout of the **minimal** states (no PR fact, not ready) is already pinned by hash (G 7515 to 7521, `TestPlainCommandMalformedState.test_m5_well_formed_and_already_refused_inputs_are_unchanged`, seven golden repos: `complete`, `implementing`, `reg-absent`, `reg-list`, `reg-notjson`, `reg-null`, `wellformed`), and those reports carry the S 20381 `note`. What is pinned nowhere is the **ready, present-head** report: `gate.evidence`, a met `pr_fact_current`, `stored_pr_fact` and the dispositions (the issue says the out-of-repo drive.py flows only). The report of the `ready` fixture was printed: 1 object of about 90 lines. Run-dependent values: the 40- and 64-hex digests **and** `gate.evidence.technical_approval.recorded_at`, which comes from the module-global `_CLOCK` counter (G 48 to 55) that every `AcceptanceRepo` advances (two consecutive `ready` fixtures gave `2026-10-03T12:00:02Z` then `…:06Z`), so the golden must normalize both | TRUE-GAP |
| #185 1, `_absent_stored_pr_head`'s exit code | S `_absent_stored_pr_head`: a **code** change in a shipped script, unreachable today because the earlier `evaluate_gate` already needed a working git | NOT TAKEN: recorded, not in this item (a test-only item changes no code) |
| #143 3, T6 infers the count | T 6161 `deleted = len(everything) - len(rest)`; the test never asserts the unlink calls of its *stopped* run. `rr.unlinks` exists only on the prune class (T 7198, `_RP`), not on `_RM`. The success-path removal tests do record and count the unlinks beneath `.removing` (R 1598) with a local `self.patch(os, "unlink", ...)` (T 6363 and 6378 count 5, T 6638, 6911, 7061); only T6's failing path **infers** its count ("T6's stopped-run count is inferred, not observed") | TRUE-GAP |
| #149 3, the failed-`stat` arm of `_can_fail_walk` | R 217 to 227 (`_can_fail_walk`; its failed-`stat` arm is R 226 to 227, `except OSError: return True`, the arm after the `os.stat`; the second `except OSError: return True`, R 234 to 235, is the failed `open` of a symlink and is not this pin's). Read first: `_Inject` (T 4502) fails `stat` only for `folder=` (the item folder) and `open` for sub-directory names; no test calls it with a sub-directory name, and no test names the helper. Measured: with `return False` in that arm all 115 tests of the six retention classes and the 6 of `RetentionTestPins` stay green | TRUE-GAP |
| #190 4, the vacuous T4 assertion | **Located:** I 9380 to 9389 `test_no_heading_matches_the_label_line_and_the_summary_has_one`; its last assertion (I 9388 to 9389) counts the label lines of `_documented_summary(3, label_lines=2)`, a sample builder called with its own parameter, so it can only ever be 2 and touches no production code. The `len == 1` assertion above it (I 9383) is the one that pins the sample | TRUE-GAP (a vacuous assertion to drop, not a missing one) |

No point is false or obsolete. The other points of the five issues are out of scope (their state is in the issues' status comments). No defect was found while reading; D-Stop applies to the measurements of CP1.

## 1. Goal and scope

Five tightenings and one new test, all in three test files of `payload/`; no line of a script or of any other payload file changes. Out of scope: any behaviour, the documents, the retention pages, the Manager and the Controller,
#185 point 1 (a code change), the other points of the five issues. This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance workflow) stays untouched.

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page), and the one judgment made, that a test-only change is a `fix:` release, is D-Release.

## 2. Design

### D-Pins (edits in place unless a row says new; the test counts move only by the one new test)

| Pin | Where | Change | No-write proof | Failure-only mutation (it changes behaviour only on the path the pin drives) |
| --- | --- | --- | --- | --- |
| p1 (#185 2) | G `test_t4_every_requirement_is_in_exactly_one_of_the_two_report_lists` | the loop covers every non-human fixture case: the six it has plus `stale_changes`, `stale_failed`, `stale_head`, `missing`, `partial`, `invalid` | each `AcceptanceRepo` is discarded; `ev.evaluate()` writes nothing | m1: P 1938 to 1943, the requirements list gains `*([_req("pr_objection_note", True, "x")] if objection else [])` before `no_standing_pr_objection` (a met requirement whose id is in neither report list, on the objection path only, so no unmet list, blocker or satisfiability changes). Measured on the unedited G suite: all 429 tests pass; with the edited loop, `stale_changes` and `stale_failed` fail (and no other subtest) |
| p2 (#185 3) | G `test_t5_the_phase_not_reachable_detail_does_not_contradict_itself`, the last `with` | the satisfy arm runs `ws._satisfy_acceptance_cli(WI, now=..., run=..., resolve=...)` in the fixture with the outstanding checkpoint, captures stdout, and asserts exit 1, `error` `AcceptancePreflightError`, `code` `phase_not_reachable`, `state_changed` false, `message` equal to the report's `blockers[0]["detail"]` for the same state, containing "which the acceptance stage accepts, but not every checkpoint is complete", and that the forge runner was never called; the direct call is dropped | the state file's digest is unchanged and no query ran (the recording runner stays empty) | m2: S 21707 raises with `blocker["detail"] + " (satisfy)"` **only when** `"but not every checkpoint is complete" in blocker["detail"]`. Measured on the unedited G suite: all 429 tests pass (the direct call and every other command-level test keep their bytes); the new command arm fails |
| p3 (#185 4) | G `test_t3_the_library_still_raises_and_a_present_head_and_the_confirmation`, the present-head arm | adds a golden: the report of the `ready` fixture as `json.dumps(report, sort_keys=True, indent=1)` with every run of 40 or 64 hex digits replaced by `<hex>` **and** every `YYYY-MM-DDTHH:MM:SSZ` stamp replaced by `<stamp>` (the `_CLOCK`-driven `recorded_at`, G 48 to 55, advances with every `AcceptanceRepo`), compared with one literal in the test, which therefore passes alone and inside the full G suite; the existing two assertions stay | the report's own `tree`/`refs` check in `report()` | m3: P 1927, the `current` branch's `current_detail` (`"workflow_gh fact for PR #… at … is current"`, taken only by a ready, present-head report), gains a trailing ".". Measured (GPTP-L2-001): the unedited G suite stays at 429 OK, and the edited suite fails the new golden (T3) only. The S 20381 `note` is **not** used: it is on the branch every resolvable report takes, so a trailing "." there fails seven `TestPlainCommandMalformedState` subtests already (`[complete]`, `[implementing]`, `[reg-absent]`, `[reg-list]`, `[reg-notjson]`, `[reg-null]`, `[wellformed]`, `flag='--acceptance-gate'`) |
| p4 (#143 3) | T `test_w37_t6_an_unreadable_symlink_while_deleting_stops_with_the_count` | records the successful `os.unlink` and `os.rmdir` calls made with a `dir_fd` while `rr.rm(apply=True)` runs (a local wrapper, `rr.unlinks` and `rr.rmdirs`, for the failing run only), and asserts: `deleted == len(unlinks) + len(rmdirs)` (the observed count), the message states that count, the names are exactly the basenames of `set(everything) - set(rest)`, and the inferred `len(everything) - len(rest)` agrees; the later finishing run is outside the recorder | the existing `archive_before` byte check stays | **none exists** (measured): the reported count is already pinned to the disk by the inferred `len(everything) - len(rest)`, so a mutation of the count fails the unedited test, and an unlink that keeps the disk the same is the success-path recorders' business. m4 (R 1598 `os.unlink(name, dir_fd=dirfd)` becomes `os.remove(name, dir_fd=dirfd)`, the same effect on disk) is the demonstration, not a failure-only mutation: unedited, it fails four other tests, `RetentionErrorPathsTwo.test_t4b_an_error_raised_mid_walk_reports_the_live_count`, `RetentionRemove.test_t2_apply_removes_only_that_folder_after_the_verify`, `…test_t12_failures_during_the_delete_and_the_place` and `…test_t14_an_interruption_at_every_transition_loses_nothing` (they patch `os.unlink`); with the edit, CP1 records that T6's new observed-call assertions fail as well while the inferred-count assertion stays green |
| p5 (#149 3) **new test** | T class `RetentionReportUnreadable`, `test_t7_a_sub_directory_that_cannot_be_examined_is_still_named_by_its_own_path` | a review folder with `a/zz`, `_Inject(folder="zz")` (no `opens`: every `stat` of the name `zz` with a `dir_fd` fails with `PermissionError`, which is the walk's own `_fwalk` stat of the listed sub-directory as well as the `_can_fail_walk` and `_is_link` probes; the walk never reaches an `open`, so an `opens` argument would be inert), through `self.case` with `want` = `at least 5 B in 1 files (partly unreadable); no archive` (the whole item line is compared, archive suffix included): exactly one read error whose path is `<repo>/.ai-review/w00/a/zz`, and the review folder's `complete` is false | `self.case` snapshots the repository and archive root before and after and asserts exit 0 | m5: R 227 `return True` in the `OSError` arm after the `os.stat` becomes `return False`; the recorded path falls back to `<repo>/.ai-review/w00` (unmutated: one read error at `<repo>/.ai-review/w00/a/zz`); fails the new test only (the existing classes were measured green) |
| p6 (#190 4) | I `test_no_heading_matches_the_label_line_and_the_summary_has_one` and `_documented_summary` | drops the last assertion and its comment (I 9388 to 9389) and the then unused `label_lines` parameter (I 9299 to 9300), which no other test passes | none (reads only) | **none exists**: the assertion cannot fail by construction, which is why it goes. m6 shows what the surviving assertion pins: `_documented_summary` emitting its label line twice fails the `len == 1` assertion (I 9383) and `test_a_three_round_summary_passes_at_three_and_fails_at_two` stays green |

m1 to m5 are one edit each of one copy of the script in the staged fixture, never of the repository. Measured (CP1's author records each): unmutated, every pin passes; under its mutation exactly the test of its row fails and
nothing else in the three suites except what the row names; a row that says "none exists" (p4, p6) names the mutation that shows what the pin adds and every other test it fails. A pin that cannot fail without its mutation is not accepted. The test counts: G and I do not move (all edits in place), T moves by exactly one (316 to 317); CP2 measures
`manager.conformance.suites` and records the result.

The new tests also run under the Manager's orphan rule (the reaper): `reaper.py` on the T class `RetentionReportUnreadable`, and on the G and I classes of the edited tests; re-parented `[git]` helpers only, all `exited`.

### D-Stop

If any pin fails on the unmutated tree, or a mutation does not fail its test, **stop**: a real defect is recorded as a finding (a separate item); no script is changed here.

### D-Release

The pull request changes shipped files: the three test files are manifest artifacts (`distribution`, `target_path` under `scripts/`) and the conformance suites the installed repositories run. `docs/RELEASING.md` ("A published version
never changes", "A pending version is frozen until published") refuses a release-source change without a version change, and the required `Conventional Commit title` check requires the title's impact to equal the version change
(`check-title --agree`; `test:` prints `impact=none`, `fix:` prints `impact=patch`). So the change is **a release, Workflow 2.29.9, a `fix:` patch**, the precedent of 2.29.7 (test pins) and 2.29.8 (wording).
`manifest.json` `workflow_version` 2.29.9; the six changed records (G, T, I, `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`) take their sentence ("gate-policy-test-pins (workflow-2.29.9)"), `sha256` and `size`;
counts of files and `distribution` do not move; `manager.conformance.suites` is measured by `release.py manager-block --write` (the obligations suite 316 to 317). `WORKFLOW_RELEASE` becomes 2.29.9 with its pinned assertions and the
document's lines (protocol 1.5, no operation or flag changes). The posture says the way back to 2.29.8 needs nothing undone (tests only). `tools/release/release_test.py` gets a 2.29.9 class, carries the suite-count pin, and the
2.29.8 class gives up the pins a newer release owns. `docs/release-history.md`: the 2.29.9 row and its stamp. The release workflow publishes it; the Manager lock and install pull requests follow (orchestrator).

### D-Staging

CP1 changes shipped files whose records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w58-tmp` (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script, in the clone only,
(a) recomputes `sha256` and `size` of every record whose file differs, (b) measures `manager.conformance.suites` with `release.py manager-block --release-dir <scratch> --write`, (c) rewrites the pin in
`tools/release/release_test.py` that reads the obligations count (as the lstat-errors plan did); that pin is CP2's change in the real tree. Then the "Verification commands" of `docs/RELEASING.md` run from the clone (the tools tests
with the zlib-ng interpreter `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`), and the new tests also run under the reaper.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The pins and roadmap row 51 | - | 2 | 1 |
| CP2 | Release 2.29.9 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The pins and roadmap row 51

**Files:** `payload/scripts/workflow_gate_policy_test.py`, `payload/scripts/workflow_state_completion_obligations_test.py`, `payload/scripts/workflow_integration_test.py`, `docs/ROADMAP.md`.

- D-Pins as code: p1 to p3 in G, p4 and p5 in T, p6 in I; the five mutations m1 to m5 (and the m6 reading of p6) run in scratch copies, each result recorded. `docs/ROADMAP.md` carries row 51 (`Current`) from this plan.
- No script changes: `git diff 774b441 --stat -- payload` lists the three test files only, and `git diff 774b441 -- payload/scripts/workflow_retention.py payload/scripts/workflow_state.py payload/scripts/workflow_gate_policy.py` is empty.

**Verification:** D-Staging (nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` in the zlib-ng interpreter; the new and edited tests under the reaper); each mutation fails its pin only.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.9

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` 2.29.9 with its pinned assertions and the document's matching lines (protocol 1.5); `manifest.json` per D-Release; the history row and stamp; the 2.29.9 class and the 2.29.8 class's given-up pins.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean;
the tools tests pass in the zlib-ng environment; `check-title "<the title above>" --agree` agrees; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 4. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Nothing runs against the real repository, the forge or the network. `$S` is a scratch directory under `$TMPDIR`.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --stat 774b441 -- payload` | CP1: the three test files. CP2 adds the protocol script, its test and the protocol document |
| 2 | `git diff --quiet 774b441 -- payload/scripts/workflow_retention.py payload/scripts/workflow_state.py payload/scripts/workflow_gate_policy.py; echo $?` | `0` (the three scripts identical) |
| 3 | in a staged fixture, the edited classes: `python3 -B workflow_gate_policy_test.py`, `python3 -B workflow_state_completion_obligations_test.py RetentionReportUnreadable RetentionRemove`, `python3 -B workflow_integration_test.py TestBundleRevisionSectionsDocumentedForm` | all OK; the obligations class holds 7 tests |
| 4 | m1 to m5 of D-Pins on scratch copies in the fixture, the suites after each | exactly the test of its row fails (m1: two subtests; m2, m3, m5: one test each; m3 is P 1927, so the seven `--acceptance-gate` hash subtests of `TestPlainCommandMalformedState` stay green); m4 is the exception D-Pins names (four more tests that patch `os.unlink` fail, the inferred-count assertion stays green) |
| 5 | m5 against the six existing retention classes | green: the gap the pin closes |
| 6 | `reaper.py --report R.json --chunk-id pins -- python3 -B <obligations suite> RetentionReportUnreadable` | status 0; orphans: only `[git]`, all `exited` |
| 7 | (full environment) the nine payload suites from a staged fixture; the `tools/release` tests with the zlib-ng interpreter; `tools/docs` tests and checker; `check-manager-block` with `--manager-releases` | all pass; the manifest says 2.29.9; `check-title` agrees |
| 8 | `git diff --name-only 774b441 -- .claude scripts .workflow-manager .github CLAUDE.md` | nothing |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #185 1 | `_absent_stored_pr_head` exit-code tightening | - | **not taken**: a code change, unreachable today; stays in the issue |
| #185 2 | p1, m1 | CP1 | |
| #185 3 | p2, m2 | CP1 | |
| #185 4 | p3, m3 | CP1 | |
| #143 3 | p4, m4 | CP1 | |
| #149 3 | p5, m5 | CP1 | the one new test |
| #190 4 | p6 | CP1 | located; a vacuous assertion dropped, no mutation catches it by construction |
| Release | 2.29.9, a `fix:` patch | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/gate-policy-test-pins-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand for `payload/`, `tools/`, `fixtures/`, `templates/`,
`manifest.json` and `docs/release-history.md` (excluded at the plan stage, protected at the implementation stage); every path a checkpoint's **Files** paragraph names is classified at both stages.
`docs/ROADMAP.md` stays excluded at both stages (acceptance edits it after the technical approval), so row 51 is a classified, unprotected change.
