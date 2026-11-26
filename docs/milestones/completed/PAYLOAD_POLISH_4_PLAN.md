# W64: Workflow 2.29.15 — the still-open test pins of #143, #119 and #113: the errno text and the permissions hint of the delete step's refusals (Revision 2)

Pull request title: `fix: pin the errno text and the permissions hint of the remove delete step's refusals`
(shipped test files change, the behaviour of every working path does not: the version change is the next patch, so the title's impact must be patch; see D-Release).

- **Work item:** `payload-polish-4` (`process`, automatic gates).
- **Requested by:** the Manager Super Orchestrator, owner standing order: a row of `docs/ROADMAP.md` (`Current` from this plan, `Done` from CP2, the last checkpoint).
- **Issues:** RodrigoFAbreu/workflow#143 (points 1 to 3), #119 (points 4 and 6) and #113 (point 5), each read with all its comments (the owner's "reviewed against main" comments of 2026-11-14 and the later status comments).
  **Branch:** `milestone/payload-polish-4` (bound by the Controller)
- **Base commit:** `f4926525ef73cc80eef3e5951f669591f8f76d23` (main after #219: the release source is 2.29.14; default gate version, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2. One mechanism: pin what the issues still name and main does not pin, change no behaviour, no message and no document. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: every point on main at `f492652`

E is `payload/scripts/workflow_state_completion_obligations_test.py`, R is `payload/scripts/workflow_retention.py`, D is `docs/release-history.md`, P is `docs/RETENTION.md`. Lines move: the code is found by name. Each class below was checked by reading the code and, for a pin, by a mutation of a copy of R in a staged fixture (`release.py stage-conformance --commit HEAD`, scratch under `$TMPDIR`, nothing in the repository).

| Point | State on main (evidence) | Class |
| --- | --- | --- |
| #143 1: the 2.25.5 row's downgrade sentence | D line 33: "Back to 2.25.4 ... restores the traceback at three places, the `UnicodeDecodeError` traceback for a state file that is not valid UTF-8 and for a tracked path that is not UTF-8 under a UTF-8 locale (under a single-byte locale 2.25.4 counts such a path again), and `pack_failed` at the pack". It names both undecodable inputs (the state file and the tracked path, which is the `git ls-files` output) | ALREADY-FIXED (nothing changes) |
| #143 2: RETENTION, remove section: the folder is renamed back after the rename | P lines 583 to 588: "A symlink in the review folder whose target cannot be read is `unreadable` ... at the same places, before the rename and after it (after the rename the folder is renamed back into `.ai-review/` and the message says "the folder is back in" its place; a leftover whose verification could not complete stays in `.removing/<id>`)" | ALREADY-FIXED |
| #143 3: T6 asserts the unlinks directly | E `test_w37_t6_an_unreadable_symlink_while_deleting_stops_with_the_count` (E 6173 to 6213) records every successful `unlink` and `rmdir` made with a `dir_fd` (E 6180 to 6198, the comment says "observed, not inferred (#143 point 3)"), asserts that set equals the entries missing from the disk (E 6205), and that the message's count is the observed one (E 6208). The remove harness `_RM` has no `rr.unlinks` (that attribute is the prune harness `_RP`'s, E 7242); the observation the issue asks for is made by the test itself. The remaining `deleted == len(everything) - len(rest)` (E 6204) is a cross-check of the observation against the disk, not the inference | ALREADY-FIXED in substance (KEEP; recorded as F1) |
| #119 4a: the `remove_failed` errno and the permissions hint | R `_stopped` (R 1564) adds "; check the permissions of `.removing/<id>`" to every `remove_failed`, and four arms put the errno in the message: the walk's first open `top_failed` (R 1583), the in-folder `rmdir` (R 1603), the `unlink` (R 1617) and the last `rmdir` (R 1624). Already pinned: E `test_t4` (E 8012, class `RetentionErrorPathsTwo`) pins the hint for the open arm, and `test_t12` (E 6943, class `RetentionRemove`) asserts the count, "run `remove w00 --apply` again" and, for the `EIO` unlink arm, the hint (``check the permissions of `.removing/w00` ``, E 6961). Not pinned: the errno text at all four arms, the hint at the two `rmdir` arms, and the exact message and next step of each arm. Mutations on copies of R (m-a) the `unlink` arm drops "({exc.strerror or exc})"; (m-b) the in-folder `rmdir`, the last `rmdir` and the open arms drop it: `RetentionRemove`, `RetentionErrorPathsTwo` and `RetentionTestPins` (54 tests), and the whole obligations suite, give the same results as the unmutated tree | TRUE-FIX-NEEDED (a test pin; no behaviour or message change) |
| #119 4b: T6 empty-destination case (the rename-back `lstat` guard) | E `test_t6_the_rename_back_never_replaces_anything` (E 6626) has the populated-destination case and a second case `seam_empty` (E 6655) that creates an empty `.ai-review/w00` after the rename and asserts `restore_failed`, the folder whole in `.removing/w00` and the empty directory untouched | ALREADY-FIXED |
| #119 4c: the stat-only `_scan` re-check after the hash, and the selection repeated under the lock | E `RetentionTestPins.test_p5_a_stat_only_change_after_the_hash_puts_the_folder_back_and_deletes_nothing` (E 8709) and `test_p6_the_selection_is_repeated_under_the_lock_and_its_own_refusal_stops_the_run` (E 8745), added by the earlier test-pins item | ALREADY-FIXED |
| #119 4d: T14's rename-back runs on `RetentionError` only | R `_flow` step 6 catches `except RetentionError as exc` (R 1955), not `BaseException`; E `test_t14` (E 7054) raises `_Killed(BaseException)` (E 4357) after the comparison (`after_compare`) and asserts the folder stays in `.removing/w00` and is not renamed back; widening the `except` fails it | ALREADY-FIXED |
| #119 6: messages and docs | (a) a persistent `remove_failed` names the errno and the permissions: done in R (`_stopped`, the four arms above), its pin is point 4a; (b) an unreadable archive "cannot be repaired" and the manual `mv` back: R `_bad_archive` (R 1416) says "repair the archive or its access, then run `remove <id> --apply` again", and after the rename the folder is already back (the message says so) or is a leftover that must stay in `.removing`; a `mv` there would be wrong advice (row 55 of the roadmap records the same, "#119 6d"); (c) the next step of an L1 `folder_changed` before the comparison: R 1957 to 1962 adds "repair the cause and run `remove <id> --apply` again", pinned at E 6144 to 6146; (d) every L1 refusal names the place: `_add_leftover_note` (R 1743) through `note` and the selection's two arms, pinned by the earlier items; (e) a `restore_failed` after an `archive_mismatch` keeps the differences: R 1966 to 1968 carries "the refusal was {code}: {message}", pinned at E 6332 ("the refusal was archive_mismatch") and E 6371 and E 6644 ("a.txt (differs)"); (f) "new in 2.22.0": P lines 476 and 549 | (a) pin only (4a); (b) KEEP (F2); (c) to (f) ALREADY-FIXED |
| #113 5: the future-mtime clamp and `build_report` without `run` | E `RetentionTestPins.test_p1_an_archive_dated_in_the_future_reports_age_zero_and_is_never_prunable` (E 8605) and `test_p2_build_report_without_run_uses_the_forge_default_runner` (E 8625, patching `query_forge_pr_facts.__kwdefaults__["run"]`) | ALREADY-FIXED |

Findings recorded and not taken (D-Stop does not apply: no point needs a behaviour change):

- **(F1)** #143 point 3: the test observes the successful `unlink`/`rmdir` calls itself instead of reading an `rr.unlinks` the remove harness does not have; adding such a list to `_RM` would be a harness change for no new assertion. Nothing changes.
- **(F2)** #119 point 6, the unreadable archive and the manual `mv` back: advice that would be wrong for a leftover (the missing entries exist only in the archive) and unnecessary after a rename back (the folder is already in place). If the owner wants a sentence for "the archive is lost for good", that is a design question, not a message fix.
- **(F3)** #113 point 6 (`docs/exit-codes.md` and the manifest rationale without `-I`) is outside the named scope of this item; the roadmap's row 55 records that the `-I` form was given in `docs/exit-codes.md` (2.29.13).

## 1. Goal and scope

One point done (the pins of point 4a), the rest of the named points already fixed or kept. Out of scope: every refusal order, exit code and message (byte-identical, no line of R or of any other payload file except E changes in CP1), every documentation page other than the release-history row and the roadmap row. D and P are **not** edited: their two sentences the issues name are already right.
This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance workflow) stays untouched.

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page).
The judgments made: a point already fixed on main is not redone, so the checkpoint set is two, not the three the brief allowed (there is no docs checkpoint: both documentation points are already true); the pins are added as subtests of existing methods, so no test method is added and the suite counts do not move.

## 2. Design

### D-Pins (CP1; all in E, in two classes: `RetentionErrorPathsTwo` for item 1 and `RetentionRemove` for items 2 and 3; no method added, every new assertion is a subtest or an addition to an existing method)

The harnesses. Item 1: `test_t4_a_remove_tree_that_cannot_open_the_folder_stops_with_nothing_deleted` (E 8012) belongs to `RetentionErrorPathsTwo` (E 7848) and uses that class's `rr = self.rm_env()` and `self.refused(result, code, *, text=())`. Items 2 and 3: `test_t12_failures_during_the_delete_and_the_place` (E 6943) belongs to `RetentionRemove` (E 6052) and uses `rr = self.env(); rr.prepared()` and `self.refused(rr, result, code)`. The review folder of the `RetentionRemove` harness (`_RA.folder`, E 4443) holds `a.txt`, `sub/b.txt`, `sub/deeper/c.bin`, the empty directory `empty`, the link `ln` and the link `dirlink`, so `everything` is its 8 entries (`a.txt`, `sub`, `sub/b.txt`, `sub/deeper`, `sub/deeper/c.bin`, `empty`, `ln`, `dirlink`); `rr.removing` is `<archive_root>/widgets/.removing` (E 4431, 5972) and the leftover place in a message is `str(rr.removing / "w00")`. The exact texts below are the ones R builds at the four arms; each subtest ends with the no-write proof (the archive's bytes equal before and after, the leftover `.removing/w00` equal to the original minus the entries the run observed deleting, `.ai-review/w00` absent, no rename back) and a clean `rr.rm(apply=True)` with code 0 and `.removing/w00` gone.

1. **The open arm** (`RetentionErrorPathsTwo`). `test_t4_...` gains, per subtest, the exact message and the exact next step: for `EACCES` and `EIO` the message is `w00 cannot be read ({os.strerror(err)}); stopped after deleting 0 entries, each proven archived; the rest is in {rr.removing / 'w00'}` and the next step is exactly ``run `remove w00 --apply` again; check the permissions of `.removing/w00` ``; for `ENOENT` the message is `w00 vanished; stopped after deleting 0 entries, ...` and the next step exactly ``run `remove w00 --apply` again`` (no hint).
2. **The `unlink` arm** (`RetentionRemove`). The existing unlink block of `test_t12` (E 6950 to 6963: the third `unlink` fails with `EIO`, the count, the two next-step assertions, the clean second run) is wrapped in its own `subTest("the unlink fails")`, because the method's body is sequential and a failed assertion outside a subtest ends it, which would hide every later subtest. The subtest gains the exact message (the entry's relative path, whose basename is the third observed call, then ` cannot be deleted (Input/output error); stopped after deleting 3 entries, each proven archived; the rest is in {rr.removing / 'w00'}`, matched with `re.escape` and a captured path) and the exact next step ``run `remove w00 --apply` again; check the permissions of `.removing/w00` `` (the existing E 6961 hint assertion stays and is made exact by this one).
3. **The `rmdir` arms** (`RetentionRemove`), three subtests of `test_t12`, each in its own `subTest`, after the unlink subtest: "a directory that cannot be removed" (new), "a directory that is not empty" (the existing `ENOTEMPTY` case on `deeper`, E 6965 to 6974, strengthened and wrapped, not duplicated) and "the folder itself cannot be removed" (new). `os.rmdir` is patched so the first call for the named directory fails once: `EIO` on `sub` gives `remove_failed`, the message `sub cannot be removed (Input/output error); stopped after deleting {n} entries, ...` (`n` the observed count of successful `unlink`/`rmdir` calls with a `dir_fd`, as the observation of `test_w37_t6`) and the next step with the hint; `ENOTEMPTY` on `deeper` gives `folder_changed`, the message `sub/deeper cannot be removed (Directory not empty); stopped after deleting {n} entries, ...` (the shown path is relative to the folder; `n` observed) and the next step exactly ``run `remove w00 --apply` again`` (no hint); the last `rmdir` (`w00`, `EIO`) gives `w00 cannot be removed (Input/output error); stopped after deleting {len(everything)} entries, ...` with the hint, where `everything` is the folder's 8 entries before the run.

**Failure-only mutations**, each one edit of one copy of R in a scratch copy of the staged fixture, never in the repository (the fixed tree passes every test). Each result is stated as the set of subtests that fail, measured over the whole obligations suite in a staged fixture against its unmutated baseline (the bare copy's 12 environment-dependent results are the same in both and are not counted), and each is recorded: (m1) the `unlink` arm drops its errno text: only the `unlink fails` subtest of `test_t12` fails (its item-2 message assertion); (m2) the in-folder `rmdir` arm drops it: only the `a directory that cannot be removed` and `a directory that is not empty` subtests fail; (m3) the last `rmdir` arm drops it: only `the folder itself cannot be removed` fails; (m4) `top_failed` drops it: only the `EACCES` and `EIO` subtests of `test_t4` fail; (m5) `_stopped` gives the hint only when `deleted == 0` (`if code == "remove_failed" and deleted == 0`): the open arm passes, and the `unlink fails` (its existing E 6961 assertion fails too), `a directory that cannot be removed` and `the folder itself cannot be removed` subtests fail; (m6) the in-folder `rmdir` arm picks `remove_failed` for `ENOTEMPTY` too: only `a directory that is not empty` fails (its code check; the existing case already asserts the code).

### D-Stop

If a new or strengthened assertion fails on the fixed tree, if a mutation does not fail exactly what is stated above, or if any existing test changes its result, **stop**: a point that cannot be done without a behaviour change beyond a test is recorded as a finding (a separate item), excluded, and no further code is changed for it.

### D-Release

The pull request changes a shipped file: E is a manifest artifact (`distribution`, a conformance suite the installed repositories run). `docs/RELEASING.md` ("A published version never changes", "A pending version is frozen until published") refuses a release-source change without a version change, and the required `Conventional Commit title` check requires the title's impact to equal the version change (`check-title --agree`; `fix:` prints `impact=patch`). So the change is **a release, Workflow 2.29.15, a `fix:` patch**, the precedent of 2.29.7 to 2.29.14.
`manifest.json` `workflow_version` 2.29.15; the four changed records (E, `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`) take their sentence ("payload-polish-4 (workflow-2.29.15)", added to the rationale, which accumulates), `sha256` and `size`; counts of files and `distribution` (83 artifacts, 6 templates, 57 distribution) do not move, and neither do the suite counts (`manager.conformance.suites`: 1250, 429, 385 and 322 stay, since every new assertion is a subtest or an addition to an existing method; `release.py manager-block --write` measures them and the release class pins them). `WORKFLOW_RELEASE` becomes 2.29.15 with its pinned assertions (`workflow_protocol_test.py`) and the protocol document's matching lines (protocol 1.5, no operation or flag changes). The posture says the way back to 2.29.14 needs nothing undone (tests and the release constant only). `tools/release/release_test.py` gets a 2.29.15 class (`PayloadPolishFourReleaseTest`: version, constant, counts, digests and sentences, posture, suite counts, the history page's `Last checked with` line, protocol lines, the history row, the roadmap row `Done` with its exact ending), and the 2.29.14 class gives up only the pins a newer release owns, the shape of the 2.29.13 and 2.29.14 classes: the version, the constant, the counts, the digest loop, the posture with the suite counts, the history page's `Last checked with` line and the protocol list line. It keeps the sentence test (`CHANGED`, `SENTENCE` and the `others == CHANGED` set check, since rationale sentences accumulate across releases), the protocol document's constraint line, the `docs/RETENTION.md` pins (the page is unchanged and stays stamped 2.29.14, so its `Last checked with` line moves from the history pin to a RETENTION-only pin), roadmap row 56 and the history row. `docs/release-history.md`: the 2.29.15 row and its stamp; it names the issues by number and not by an internal id (`check_docs`), and says it closes nothing by keyword. A pending version is frozen until published: no further release-source change may be added to this branch after its version bump. The release workflow publishes it; the Manager lock and install pull requests follow (orchestrator). The title in the header is checked with `python3 tools/release/release.py check-title "<that title>" --agree --head <the version-bump commit>`.
The roadmap row 57 pin: the acceptance rewrites the row to `Done (accepted by policy; ...)`, so the release test pins the row's ending with exactly `| Done (accepted by policy; a `fix:` change, Workflow patch release 2.29.15 follows the merge) |`, written from CP2.

### D-Staging

CP1 changes a shipped file whose record moves only at CP2, so stock `stage-conformance` cannot stage it. It verifies in a disposable clone under `$TMPDIR` (a new empty directory outside the repository; procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script, in the clone only, (a) recomputes `sha256` and `size` of every record whose file differs, (b) measures `manager.conformance.suites` with `release.py manager-block --release-dir <scratch> --write` (the counts must come out unchanged), (c) rewrites the pins in `tools/release/release_test.py` that read a changed digest (those pins are CP2's change in the real tree). Then the "Verification commands" of `docs/RELEASING.md` run from the clone: the nine suites from `stage-conformance`'s fixture, run from inside it, `tools/release` with the zlib-ng interpreter `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`, `tools/docs` and `check_docs.py`, `check-manager-block` with `--manager-releases`; the touched tests also run under the Manager's reaper (the orphan rule: `reaper.py --report R.json --chunk-id polish4 -- python3 -B workflow_state_completion_obligations_test.py RetentionRemove RetentionErrorPathsTwo`). Mutations m1 to m6 run in further copies of that fixture, never in the repository. Nothing runs an archive, remove or prune command against a real repository: every retention run of the tests uses its own scratch repository.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The errno and permissions pins of the remove delete step | - | 1 | 1 |
| CP2 | Release 2.29.15 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The errno and permissions pins of the remove delete step

**Files:** `payload/scripts/workflow_state_completion_obligations_test.py`, `docs/ROADMAP.md`.

- D-Pins 1 to 3 as additions to two existing methods, `test_t4_...` of `RetentionErrorPathsTwo` (item 1) and `test_t12_...` of `RetentionRemove` (items 2 and 3, each case in its own subtest) (`git diff f492652 -- payload` shows only the test file; no line of R changes); m1 to m6 run in scratch copies and each result is recorded. `docs/ROADMAP.md` carries the new row 57 (`Current`, added with this plan) in the style of its neighbours.

**Verification:** D-Staging (nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` in the zlib-ng interpreter); the two touched classes (`RetentionRemove`, `RetentionErrorPathsTwo`) under the reaper; m1 to m6 fail exactly the subtests D-Pins says, measured over the whole obligations suite; the obligations suite count stays 322.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.15

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`, `docs/ROADMAP.md`.

- `WORKFLOW_RELEASE` 2.29.15 with its pinned assertions and the document's matching lines (protocol 1.5); `manifest.json` per D-Release; the history row and stamp; the 2.29.15 class and the given-up pins of the 2.29.14 class (exactly: version, constant, counts, digest loop, posture and suite counts, the history page's `Last checked with` line, the protocol list line; kept: the sentence test, the protocol constraint line, the RETENTION pins, roadmap row 56, the history row); `docs/ROADMAP.md`'s row 57 becomes `Done` (the last checkpoint), with the release following the merge.
- The title is checked as D-Release says.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD --out "$(mktemp -d)"` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; the tools tests pass in the zlib-ng environment; `check-title` agrees; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 4. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Nothing runs against the real repository, the forge or the network. `$S` is a scratch directory under `$TMPDIR`.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --stat f492652 -- payload` | the obligations test file; CP2 adds the protocol script, its test and the protocol document; R is absent |
| 2 | `git diff f492652 -- payload/scripts/workflow_retention.py` | nothing |
| 3 | in a staged fixture, `python3 -B workflow_state_completion_obligations_test.py RetentionRemove RetentionErrorPathsTwo` | OK; the suite count stays 322 |
| 4 | m1 to m6, each on its own scratch copy, the whole obligations suite | exactly the stated subtests fail beyond the unmutated baseline; the originals pass |
| 5 | `reaper.py --report R.json --chunk-id polish4 -- python3 -B workflow_state_completion_obligations_test.py RetentionRemove RetentionErrorPathsTwo` | status 0; orphans: only `[git]`, all `exited` |
| 6 | (full environment) the nine payload suites from a staged fixture; the `tools/release` tests with the zlib-ng interpreter; `tools/docs` tests and checker; `check-manager-block` with `--manager-releases` | all pass; the manifest says 2.29.15; `check-title` agrees |
| 7 | `git diff --name-only f492652 -- .claude scripts .workflow-manager .github CLAUDE.md` | nothing |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #143 1 | ALREADY-FIXED | - | D line 33 names both undecodable inputs |
| #143 2 | ALREADY-FIXED | - | P lines 583 to 588 |
| #143 3 | ALREADY-FIXED in substance (F1) | - | the test observes the calls itself |
| #119 4a | D-Pins 1 to 3, m1 to m6 | CP1 | the only real gap |
| #119 4b, 4c, 4d | ALREADY-FIXED | - | `seam_empty`; `test_p5`, `test_p6`; `after_compare` |
| #119 6 | (a) pin only; (b) not taken (F2); (c) to (f) ALREADY-FIXED | CP1 | |
| #113 5 | ALREADY-FIXED | - | `test_p1`, `test_p2` |
| Release | 2.29.15, a `fix:` patch | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/payload-polish-4-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand for `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json` and `docs/release-history.md` (excluded at the plan stage, protected at the implementation stage); every path a checkpoint's **Files** paragraph names is classified at both stages.
`docs/ROADMAP.md` stays excluded at both stages, so the roadmap row is a classified, unprotected change.
