# W63: Workflow 2.29.14 — the open points of #216: the takeover arm of the plan-approval guard refusal, the early-selection note, one leftover-state pin (Revision 1)

Pull request title: `fix: name the takeover route in the plan-approval guard refusal and pin two retention cases`
(shipped scripts and shipped test files change, the behaviour of every working path does not: the version change is the next patch, so the title's impact must be patch; see D-Release).

- **Work item:** `payload-polish-3` (`process`, automatic gates). The orchestrator's brief named `payload-polish-2` as the work item id; that id is `MILESTONE_COMPLETE` (accepted, merged as #215) and an id is permanently non-reusable, so this item takes the next one.
- **Requested by:** the Manager Super Orchestrator, owner standing order: a row of `docs/ROADMAP.md` (`Current` from this plan, `Done` from CP3, the last checkpoint).
- **Issue:** RodrigoFAbreu/workflow#216 (four points; no comments, the body is the whole record), the optional findings of the previous item. The findings record behind it is `docs/ai-workflow/registry/payload-polish-2-dispositions.json`.
  **Branch:** `milestone/payload-polish-3` (bound by the Controller)
- **Base commit:** `9c22845cbf9b14978a6d101ac041a696207e5699` (main after #217: the release source is 2.29.13; default gate version, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. One mechanism: a message of the shipped payload says what is true, a test pins each case the issue names, and nothing changes any refusal order, code or exit code. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: every point on main at `9c22845`

E is `payload/scripts/workflow_state.py`, R is `payload/scripts/workflow_retention.py`, O is `payload/scripts/workflow_state_completion_obligations_test.py`, I is `payload/scripts/workflow_integration_test.py`. Lines move: the code is found by name.

| Point | State on main (evidence) | Class |
| --- | --- | --- |
| 1: the plan-approval final refusal has no takeover arm | E `_acquire_plan_approval_guard_locked`, the `if not reclaim:` block (E 3833 to 3851) picks `next_step` by `held.get("step_class") == DESTRUCTIVE` only: a destructive guard gets the by-hand removal, every other guard (a takeover's included) gets the ordinary "take the transaction over" step. The claim-guard sibling `_acquire_guard_locked` (E 6912 to 6932, the `OPUS-R82-002` branch) tests `held.get("step") == "takeover"` first and says "that guard is a takeover's: let a running takeover finish, or, if it died, re-run it: `workflow_state.takeover_evidence`, then `workflow_state.take_over_claim` with the takeover literal and the guard-release literal ...". The sibling is pinned (`workflow_state_test.py`, `test_same_token_other_worktree_still_gets_the_foreign_worktree_message`); the plan-approval refusal is pinned by I `test_acquire_guard_refuses_when_held_under_the_current_epoch_by_a_different_token` for the ordinary and the destructive guard only. The takeover's guard reaches this refusal: role `owner`, presented token not the held one (the first takeover arm needs the same token, the `takeover` role branch never falls through). Reproduced: `acquire_plan_approval_guard(role="takeover", step="takeover")`, then an owner call with another token, gives the ordinary text | TRUE-FIX-NEEDED (a message) |
| 2: an unmapped `OSError` in the first `_select_finished` names no leftover, the docs promise it | R `_select_removal` sets `adir_fd = resolved = None` before its `try`; the tuple that fills them is the return value of `_select_finished`, so an exception raised inside it leaves `adir_fd` None and `_add_leftover_note` (through `_has_leftover(None, ...)`) appends nothing. Reproduced in the leftover state (`rr.park()`): the first `os.open` of `_walk_chain` (of `/`, the unwrapped open before any archive-directory component) failing gives `error: unreadable: remove stopped on an unexpected I/O error: EIO` and the step "this run renamed nothing: the review folder is where it was before it started; repair the cause, then run the same command again" with no leftover note; the same failure with `.removing/w00` parked says nothing about it. `docs/RETENTION.md` (the remove stat-errors paragraph, "in the leftover state it also names the leftover, once") promises the note for every unexpected I/O error before the rename | TRUE-FIX-NEEDED (the sentence and a pin; no behaviour change: naming the leftover there would need the selection to look for `.removing` before the archive directory is open, which it cannot do without opening the archive directory by path, which the engine never does) |
| 3: no subtest drives an `OSError` through `_select_removal`'s `except OSError` arm in the leftover state | The arm exists and works: reproduced with `_call_fails("pread", "_index_ids", EIO)` and `_call_fails("fstat", "_judge_removal_archive", EIO)` after `rr.park()`: both give the step and, once, "an earlier run's leftover is untouched in .../.removing/w00; once this is resolved, run `remove w00 --apply` again". O `test_t7b3` runs these in the in-place state only; `test_t7b4`'s one leftover subtest fails `fstat` at `_flow`, which is `_flow`'s own arm, not the selection's | TRUE-FIX-NEEDED (a test) |
| 4: `docs/RETENTION.md` line 476 says the command does not archive from a partial view | The row is in the table of "The archive command" (the nearest heading above it) and its `.removing` clause says where the directory comes from ("from the remove command", new in 2.22.0). The refusal it describes is the archive command's: a `.removing` that is a symlink, not a directory or unreadable is a `read_errors` entry beneath the archive directory, and `_select_destination` says `the engine does not {verb} from a partial view` with the verb of the running command. Reproduced: `archive` with `.removing` a symlink gives `unreadable`, "repair it; the engine does not archive from a partial view". The remove command's own paragraph already says "the command does not remove from a partial view" (RETENTION line 539, pinned by the verb texts of R). The sentence is right in its table; the issue's premise (that this row describes the remove command) is false | KEEP (recorded as a finding, nothing changes) |

Finding recorded and not taken (D-Stop does not apply: no point needs a behaviour change): **(F1)** point 4, above. If the owner wants the row to name the command explicitly ("`archive` does not archive from a partial view"), that is a one-word docs edit for a later polish; it is not a correction.

## 1. Goal and scope

Three points done (one message, two pins and one doc sentence), one point not taken. Out of scope: every refusal order, exit code and message not named above (byte-identical), the claim guard's own final refusal (E 6956, which names no step: recorded in the previous item), `docs/exit-codes.md`, every other documentation page.
This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance workflow) stays untouched.

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page).
The judgments made: the takeover arm mirrors the claim guard's third arm word for word (no trailing "then run this again": the sibling has none, and the arm's own "re-run it" is the step); point 2 is a documentation and test change because the refusal cannot name a leftover it has no descriptor to look for; point 4's premise is false and is kept as is.

## 2. Design

### D-Wording (CP1; each changed message has an exact pin, next to its neighbours' pins, and a failure-only mutation)

1. **Point 1, E.** In the `if not reclaim:` block of `_acquire_plan_approval_guard_locked` the choice of `next_step` gains a first arm, tested before the destructive one, as in the sibling: when `held.get("step") == "takeover"` the step is `that guard is a takeover's: let a running takeover finish, or, if it died, re-run it: `workflow_state.plan_approval_takeover_evidence`, then `workflow_state.take_over_plan_approval_transaction` with the takeover literal and the guard-release literal {plan_approval_guard_release_authorization_literal(held)!r}` (the words of the claim guard's third arm, with the plan-approval functions' names). The cause text, the class (`PlanApprovalGuardHeldError`), the branch order, the guard and the other two arms are byte-identical; the refusal raises before any write.
   **Pin.** The existing I test `test_acquire_guard_refuses_when_held_under_the_current_epoch_by_a_different_token` gains a third subtest `takeover`, next to its `ordinary` and `destructive` subtests: a takeover's guard (`acquire_plan_approval_guard(repo.root, holder_owner_token=<journal token>, step="takeover", role="takeover")`) held, an owner call presenting `"0" * 32`: `assertRaises(PlanApprovalGuardHeldError)`, the exact full message (cause, then "; this session presents a token that is not the owner's, so it is not the holder: " and the arm above, with the literal of the held guard), `assertNotIn("then run this again", message)`, the guard file bytes equal before and after, and the guard read back equal to the held one. No new method: I's count stays.

### D-Tests (CP2)

2. **Point 3, O.** `test_t7b4_every_stray_before_the_rename_says_nothing_was_renamed` gains, after its leftover subtest, a loop of two subtests "in the leftover state a failed index read names the leftover once" over `("pread", "_index_ids")` and `("fstat", "_judge_removal_archive")`: `rr = self.rm_env(); rr.park(); before = rr.snap(times=False)`, `_call_fails(function, site, errno.EIO)` around `rr.main_rm("w00", "--apply")`; asserts the call was counted, exit 2, `error: unreadable`, the cause `remove stopped on an unexpected I/O error: EIO`, the exact `{step}; an earlier run's leftover is untouched in ` prefix, the note count 1, `assertNotIn("renamed aside", err)`, `rr.renames == []`, the snapshot equal, the leftover whole in `.removing/w00` and `.ai-review/w00` absent, and a clean `rr.rm(apply=True).code == 0` afterwards.
3. **Point 2, O.** The same method gains a subtest "in the leftover state an error before the archive directory is open names no leftover": `rr.park()`, `_call_fails("open", "_walk_chain", errno.EIO)` (with `skip=0` it fails the first, unwrapped `os.open` of `/`; the subtest says so in a comment, so that a later `only=`/`skip=` change does not silently retarget it), `rr.main_rm("w00", "--apply")`: exit 2, `error: unreadable`, the cause, the exact step line `next step: {_NOTHING_RENAMED}` as the whole line (no note), `assertNotIn("an earlier run's leftover", err)`, `assertNotIn("renamed aside", err)`, the no-write proof as above, and a clean run afterwards. It pins the case the documentation now qualifies.
4. **Point 2, docs.** The sentence of `docs/RETENTION.md` ("in the leftover state it also names the leftover, once") becomes "in the leftover state it also names the leftover, once, unless the error is met before the archive directory is open (the first steps of the selection), which names the cause and the same next step only". The neighbouring sentences of that paragraph are not pinned by the release class, so the docs-only change needs no release pin; its behaviour is pinned by the subtest of item 3.
   Point 4 changes nothing (section 0).

**Failure-only mutations**, each in a scratch copy of the staged fixture, never in the repository: (m1) drop the takeover arm of E (the step falls to the ordinary text): the new `takeover` subtest of I fails, the `ordinary` and `destructive` subtests and every other test of the nine suites pass; (m1b) make the takeover arm fire for every guard: the `ordinary` and `destructive` subtests fail and the `takeover` one passes; (m2) in R's `_select_removal`, drop the `_add_leftover_note(...)` call of the `except OSError` arm (it raises `_before_the_rename(exc)` alone): the two new L1 index-read subtests of `test_t7b4` fail, nothing else; (m3) in R's `_select_removal`, open the archive directory by path before the selection and pass it as `adir_fd` (so the leftover is looked up even when the selection did not reach it): the early-selection subtest of `test_t7b4` fails the early-selection subtest (the whole-line `next step:` assertion, which carries the note, comes first), nothing else. Each result is recorded.

### D-Stop

If a new or strengthened test fails on the fixed tree, if a mutation does not fail exactly what is stated above, or if any existing test changes its result, **stop**: a point that cannot be done without a behaviour change beyond a message or a test is recorded as a finding in this plan (a separate item), excluded, and no further code is changed for it. Point 4 is already such a finding (F1: its premise is false and nothing needs doing).

### D-Release

The pull request changes shipped files: E, I and O are manifest artifacts (`distribution`, and the conformance suites the installed repositories run); R is unchanged. `docs/RELEASING.md` ("A published version never changes", "A pending version is frozen until published") refuses a release-source change without a version change, and the required `Conventional Commit title` check requires the title's impact to equal the version change (`check-title --agree`; `fix:` prints `impact=patch`). So the change is **a release, Workflow 2.29.14, a `fix:` patch**, the precedent of 2.29.7 to 2.29.13.
`manifest.json` `workflow_version` 2.29.14; the six changed records (E, I, O, `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`) take their sentence ("payload-polish-3 (workflow-2.29.14)"), `sha256` and `size`; counts of files and `distribution` (83 artifacts, 6 templates, 57 distribution) do not move, and neither do the suite counts (`manager.conformance.suites`: 1250, 429, 385 and 322 stay, since every new test is a subtest of an existing method; `release.py manager-block --write` measures them and the release class pins them). `WORKFLOW_RELEASE` becomes 2.29.14 with its pinned assertions (`workflow_protocol_test.py`) and the protocol document's matching lines (protocol 1.5, no operation or flag changes). The posture says the way back to 2.29.13 needs nothing undone (a message and tests: the older files are back, no state, flag, code or exit code differs). `tools/release/release_test.py` gets a 2.29.14 class (`PayloadPolishThreeReleaseTest`: version, constant, counts, digests and sentences, posture, suite counts, the history page's and `docs/RETENTION.md`'s `Last checked with` lines, protocol lines, the history row, the roadmap row `Done`), and the 2.29.13 class gives up only the pins a newer release owns, the shape of the 2.29.11 and 2.29.12 classes (#215): the version, the constant, the counts, the digest loop, the posture with the suite counts, the two `Last checked with` lines (history and RETENTION pages) and the protocol list line. It keeps the sentence test (`CHANGED`, `SENTENCE` and the `others == CHANGED` set check, since rationale sentences accumulate across releases), the protocol document's constraint line ("Workflow 2.29.13 changes no flag ..."), the pins that name `docs/exit-codes.md` (unchanged, still stamped 2.29.13) and the `archives` sentence, the roadmap row 55 and the history row. `docs/release-history.md`: the 2.29.14 row and its stamp; it names the issue by number and not by an internal id (`check_docs`), and says it closes nothing by keyword. `docs/RETENTION.md`'s stamp moves to 2.29.14 (the page changes in CP2). A pending version is frozen until published: no further release-source change may be added to this branch after its version bump. The release workflow publishes it; the Manager lock and install pull requests follow (orchestrator). The title in the header is checked with `python3 tools/release/release.py check-title "<that title>" --agree --head <the version-bump commit>`.

### D-Staging

CP1 and CP2 change shipped files whose records move only at CP3, so stock `stage-conformance` cannot stage them. Each verifies in a disposable clone under `$TMPDIR` (a new empty directory outside the repository; procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script, in the clone only, (a) recomputes `sha256` and `size` of every record whose file differs, (b) measures `manager.conformance.suites` with `release.py manager-block --release-dir <scratch> --write` (the counts must come out unchanged), (c) rewrites the pins in `tools/release/release_test.py` that read a changed digest (those pins are CP3's change in the real tree). Then the "Verification commands" of `docs/RELEASING.md` run from the clone: the nine suites from `stage-conformance`'s fixture, run from inside it, `tools/release` with the zlib-ng interpreter `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`, `tools/docs` and `check_docs.py`, `check-manager-block` with `--manager-releases`; the new and the touched tests also run under the reaper (the orphan rule). Mutations m1 to m3 run in further copies of that fixture, never in the repository. Nothing runs an archive, remove or prune command against a real repository: every retention run of the tests uses its own scratch repository.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The takeover arm of the plan-approval refusal and its pin | - | 1 | 1 |
| CP2 | The leftover-state pins and the RETENTION sentence | CP1 | 1 | 1 |
| CP3 | Release 2.29.14 | CP2 | 2 | 1 |

<!-- CP1 -->
### CP1 — The takeover arm of the plan-approval refusal and its pin

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_integration_test.py`, `docs/ROADMAP.md`.

- D-Wording 1 as one edit to E (`git diff 9c22845 -- payload/scripts/workflow_state.py` shows the one added arm and nothing else) and the third subtest in I; m1 and m1b run in scratch copies and each result is recorded. `docs/ROADMAP.md` carries the new row 56 (`Current`, added with this plan) in the style of its neighbours.

**Verification:** D-Staging (nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` in the zlib-ng interpreter); the touched I test under the reaper; m1 and m1b fail exactly what D-Wording says.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — The leftover-state pins and the RETENTION sentence

**Files:** `payload/scripts/workflow_state_completion_obligations_test.py`, `docs/RETENTION.md`.

- D-Tests 2 to 4: the three new subtests of `test_t7b4` (no product line changes; no method added) and the qualified sentence of `docs/RETENTION.md`; m2 and m3 run in scratch copies and each result is recorded. Point 4 is recorded as finding F1 and changes nothing.

**Verification:** D-Staging; the touched test under the reaper; m2 and m3 fail exactly what D-Wording says; `tools/docs` and `check_docs.py` are clean; the obligations suite count stays 322.
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Release 2.29.14

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`, `tools/release/release_test.py`, `docs/ROADMAP.md`.

- `WORKFLOW_RELEASE` 2.29.14 with its pinned assertions and the document's matching lines (protocol 1.5); `manifest.json` per D-Release; the history row and stamp; the stamp of `docs/RETENTION.md`; the 2.29.14 class and the given-up pins of the 2.29.13 class (exactly: version, constant, counts, digest loop, posture and suite counts, the two `Last checked with` lines, the protocol list line; kept: the sentence test, the protocol constraint line, the exit-codes and RETENTION plain-form pins, roadmap row 55, the history row); `docs/ROADMAP.md`'s row becomes `Done` (the last checkpoint), with the release following the merge.
- The title is checked as D-Release says.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD --out "$(mktemp -d)"` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; the tools tests pass in the zlib-ng environment; `check-title` agrees; `workflow-manager verify .` is clean.
<!-- /CP3 -->

## 4. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Nothing runs against the real repository, the forge or the network. `$S` is a scratch directory under `$TMPDIR`.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --stat 9c22845 -- payload` | E, I and O; CP3 adds the protocol script, its test and the protocol document; R is absent |
| 2 | `git diff 9c22845 -- payload/scripts/workflow_state.py \| grep '^[-+][^-+]'` | the one added arm of the plan-approval refusal; no other line |
| 3 | in a staged fixture, `python3 -B workflow_integration_test.py` and `python3 -B workflow_state_completion_obligations_test.py RetentionErrorPathsTwo` | OK; the suite counts 385 and 322 |
| 4 | m1 to m3, each on its own scratch copy | exactly the stated tests fail; the originals pass |
| 5 | `reaper.py --report R.json --chunk-id polish3 -- python3 -B <suite> <class>` for the touched classes | status 0; orphans: only `[git]`, all `exited` |
| 6 | (full environment) the nine payload suites from a staged fixture; the `tools/release` tests with the zlib-ng interpreter; `tools/docs` tests and checker; `check-manager-block` with `--manager-releases` | all pass; the manifest says 2.29.14; `check-title` agrees |
| 7 | `git diff --name-only 9c22845 -- .claude scripts .workflow-manager .github CLAUDE.md` | nothing |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #216 1 | D-Wording 1, pin, m1, m1b | CP1 | the claim guard's third arm, mirrored |
| #216 2 | D-Tests 3 and 4, m3 | CP2 | no behaviour change: the sentence is qualified and the case pinned |
| #216 3 | D-Tests 2, m2 | CP2 | |
| #216 4 | not taken (F1) | - | the row is the archive command's own refusal; the premise is false |
| Release | 2.29.14, a `fix:` patch | CP3 | D-Release |

The artifact declaration `docs/ai-workflow/registry/payload-polish-3-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand for `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json`, `docs/release-history.md` and `docs/RETENTION.md` (excluded at the plan stage, protected at the implementation stage); every path a checkpoint's **Files** paragraph names is classified at both stages.
`docs/ROADMAP.md` stays excluded at both stages, so the roadmap row is a classified, unprotected change.
