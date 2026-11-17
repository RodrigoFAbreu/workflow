# W57: Workflow 2.29.8 — three command files and one engine refusal say what the code does (Revision 1)

Pull request title: `fix: make the bundle-record wording of the apply commands and the cross_device next step say what the code does`
(wording of shipped files only, no behaviour change: the version change is the next patch, so the title's impact must be patch; see D-Release).

- **Work item:** `command-wording-pins` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner standing order (queue the reviewed follow-ups when the queue is empty; reviewed against
  `origin/main` on 2026-11-16): row 50 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#190 points 1 and 2 and #123 point 6, each read with all its comments.
  **Branch:** `milestone/command-wording-pins`
- **Base commit:** `c2068ca7ec4c04c262b706375d0e07c616b15538` (`origin/main` after #197: the release source is 2.29.7; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. One mechanism: make shipped text say what the code does, no behaviour change. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: each point on main at `c2068ca`

R is `payload/scripts/workflow_retention.py`; the four commands are in `payload/.claude/commands/`.
Issue comments read: #190 has **none** (its body is the whole record); #123 has two owner comments (2026-11-12, 2026-11-14), and the second says points 1 to 5 are fixed and
"still open: 6 (the cross_device next step advises --archive-root although the command never passes it)".

| Point | State on main (file:line) | Class |
| --- | --- | --- |
| #190 1, `apply-pr-review.md`: the later-round sentence omits the `same_content` rule, the "run from 1 to N-1" check and the "with no quarantine say so" clause | `apply-pr-review.md` 113 to 122 ends "...and after a withdrawal restore the earlier ones byte for byte from the newest `current.rejected-*` sibling. Assert". `apply-implementation-review.md` 242 to 256 and `apply-functional-review.md` 235 to 249 carry "checking they run from 1 to `N-1`" (255 and 248), "with no quarantine say so in the entry" (256 and 249) and "a `"same_content"` round adds to the entry of round `N` and opens none" (248 and 241) | TRUE, but see D-Pr-Outcome: the `same_content` rule does not apply to this command |
| #190 2, "append a section" without the `same_content` exception | `apply-implementation-review.md` 242 and `apply-functional-review.md` 235: "append a section headed `## Implementation revision <N>` to `<bundle_dir>/TEST_RESULTS.md`" with no exception; the entry half has it ("a `"same_content"` round adds to the entry of round `N` and opens none", 248 and 241). `docs/ai-workflow/REVIEW_PROTOCOL.md` 526 to 527 states it: "a `same_content` round keeps `N` and rewrites section `N` with its new commit and results" | TRUE |
| #123 6, the `cross_device` next step | R 1751 to 1753 (selection step 10, dry run and `--apply`) and R 1886 to 1888 (the `EXDEV` of the rename itself) both say "keep the archive store on the repository's file system (`--archive-root`)". `payload/.claude/commands/archive-finished-item.md` runs `python3 -I scripts/workflow_retention.py archive <id>`, `remove <id>` and their `--apply` forms with **no** `--archive-root` (by design: the default archive root), so the command cannot follow its own next step | TRUE, and it is two sites, one sentence |
| #190 3, "and keeps it at the plan stage" in the 2.29.6 history row and manifest rationale | `docs/release-history.md` 2.29.6 row and the `REVIEW_PROTOCOL.md` rationale of `manifest.json`: no such clause. The issue has no comment and no owner decision; the point needs a manifest digest move and a history-row edit of a published release | **NOT TAKEN (owner decision)**: not touched, not planned |
| #190 4 (a vacuous test assertion) | not in this item's brief | not touched |

No point is false or obsolete. `apply-pr-review.md` is the only command with the three clauses missing; `milestone-implement.md` writes round 1 only and is not part of the point.

## 1. Goal and scope

Wording only, one mechanism: shipped text says what the code does. Three command files and one engine message change; nothing the code does changes.
Out of scope: any behaviour, #190 point 3 (owner decision), #190 point 4, the retention pages, the Manager, the Controller, the protocol document (`REVIEW_PROTOCOL.md` already states
the form correctly). This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance
workflow) stays untouched; the files under `payload/` change.

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page).

## 2. Design

### D-Wording (the exact sentences; whitespace is flattened when pinned, so line breaks are free)

**W1, `apply-pr-review.md`, step 4 of "Durable ordering".** The text from "carry every earlier section" to "sibling. Assert" is replaced by:

> carry every earlier section and entry forward unchanged, and read "for this round" as section and entry `N` only. This command records every round with the ordinary outcome
> (`record_bundle_generation` is called without an outcome), so `N` advances and section and entry `N` are new: no round here adds to an earlier entry or rewrites an earlier section.
> When the generator stubbed both files empty after a withdrawal, restore sections 1 to `N-1` and entries 1 to `N-1` byte for byte from the newest `current.rejected-*` sibling
> (by modification time) whose files hold them, checking they run from 1 to `N-1`; never rewrite them from memory, and with no quarantine say so in the entry. Assert

**W2, `apply-implementation-review.md` step 7 and `apply-functional-review.md` bounded branch step 4.** In both, the parenthesis after "append a section headed `## Implementation revision <N>` to `<bundle_dir>/TEST_RESULTS.md`"
(`- commit:`, `- commands:`, `- result:`, written fresh at this round's commit, the full suite re-run for it) gets one more clause, so it reads:

> (`- commit:`, `- commands:`, `- result:`, written fresh at this round's commit, the full suite re-run for it; a `"same_content"` round keeps `N` and rewrites section `N` with its new commit and results, appending none)

**W3, R, both `cross_device` refusals** (R 1751 to 1753 and R 1886 to 1888; message and code unchanged, only the next step). Both next steps become exactly:

> run the engine by hand with an --archive-root on the repository's file system (archive there, then remove), or leave the folder; nothing was moved

The next step says the true thing the old one hid: a different file system means the default archive store cannot be used; the Manager-run command never passes `--archive-root`, so the way out is to run
`archive <id> --apply --archive-root <DIR>` and `remove <id> --apply --archive-root <DIR>` by hand, with `<DIR>` on the repository's file system, or to leave the folder. (The archive already written in the default
store stays; `remove` and `prune` read the store they are given, so it is not found there. Nothing else in the refusal changes.)

### D-Pr-Outcome (why W1 does not copy the `same_content` rule)

The issue asks for the rule in `apply-pr-review.md`. The command's step 4 calls `record_bundle_generation` with `stage="post-fix"` and no `outcome`
(`workflow_state.record_bundle_generation`, `outcome: str = "ordinary"`, `workflow_state.py` 15167 to 15168) and writes the `Workflow-Bundle-Generation-Record` trailer without `Workflow-Supersedes`: a pull-request round is always ordinary, `N`
advances, and no round there adds to an earlier entry. Copying "a `same_content` round adds to the entry of round `N`" would describe a path the command never takes (and would invite a worker to resolve an outcome
the command does not). So the sentence says what the code does: every round here is ordinary. The two other clauses (the 1 to `N-1` check, say-so with no quarantine) are copied as the other commands state them.
The plan review may overrule this; the alternative is a one-line change of W1.

### D-Pins (a pin is a test that fails on the old wording; a mutation restores the old wording in a scratch copy of one file)

The command pins go to `payload/scripts/workflow_integration_test.py` (the suite that already pins the command files: `_command_text`, `_flat`, `TestGoldenCommandFileHashes`, the 2.29.6 class
`TestBundleRevisionSectionsContract`), as the new class `TestCommandWordingPins`. The engine pins go to `payload/scripts/workflow_state_completion_obligations_test.py` as the new class `RetentionCrossDeviceWording`,
`skipUnless` the `zstd` program like its neighbours, using the `_RM` environment.

| Test | Drives | Asserts | No-write proof | Mutation (old wording back, one place) |
| --- | --- | --- | --- | --- |
| `test_apply_pr_review_states_the_restore_checks_and_the_ordinary_outcome` (c1) | the flattened text of `apply-pr-review.md` | contains, each on its own: "checking they run from 1 to `N-1`", "with no quarantine say so in the entry", "records every round with the ordinary outcome", "no round here adds to an earlier entry or rewrites an earlier section" (a `subTest` each) | reads one file; writes nothing | m1: drop "checking they run from 1 to `N-1`"; m2: drop ", and with no quarantine say so in the entry"; m3: drop the ordinary-outcome sentence; each fails its own `subTest` |
| `test_the_two_apply_commands_say_a_same_content_round_rewrites_section_n` (c2) | the flattened text of `apply-implementation-review.md` and `apply-functional-review.md` (a `subTest` per file) | contains W2's clause exactly, and the old parenthesis ending "the full suite re-run for it)" does **not** occur followed by "and an entry headed" | reads two files; writes nothing | m4: remove W2's clause from the first file; m5: from the second; each fails its file's `subTest` only |
| `test_cross_device_at_the_selection_says_to_run_the_engine_by_hand` (e1) | `rr.rm` with `_same_device` patched to `False`, dry run and `--apply` | `err_code` `cross_device`; `next_step` equals W3 exactly (and does not contain "keep the archive store") for both runs | `rr.snap(times=False)` equal before and after, `rr.renames == []`, the folder files unchanged | m6: R 1752 back to the old text |
| `test_cross_device_of_the_rename_says_to_run_the_engine_by_hand` (e2) | `rr.rm(apply=True, guard=False)` with `_rename` raising `OSError(EXDEV)` | `err_code` `cross_device`; `next_step` equals W3 exactly | the same snapshot, the folder files, `.removing` absent (created by this run, removed again) | m7: R 1887 to 1888 back to the old text |

`TestGoldenCommandFileHashes` pins every byte of the three command files, so each of m1 to m5 also fails it for that file by design; the measured claim is "the pin of its row fails, and apart from the golden-hash test
nothing else". Measured in the staged fixture (D-Staging): unmutated, the four pass; under each mutation exactly the test and `subTest` of its row fails (plus the golden-hash test for m1 to m5); the existing retention classes
(`RetentionRemove` `test_t5_cross_device_refuses_before_and_during_the_rename` among them) stay green under m6 and m7, which is the gap the pins close. The two new engine tests also run under the Manager's orphan rule (the reaper):
re-parented `[git]` helpers only, all `exited`. A test that cannot fail without its mutation is not accepted: CP1's author re-runs the seven mutations and records each result.

The golden hashes of the three command files in `_GOLDEN_COMMAND_FILE_SHA256` take the new values, each with a comment line naming the wording change ("W57 (command-wording-pins): ... -- intentional content change"), as the 2.29.6 item did.

### D-Stop

If any pin fails on the unmutated change, or a mutation does not fail its test, **stop**: a real defect is recorded as a finding (a separate item); no behaviour is changed here.

### D-Release

The pull request changes shipped files: the three command files, R and the two test suites are manifest artifacts. `docs/RELEASING.md` ("A published version never changes", "A pending version is frozen until published")
refuses a release-source change without a version change, and the required `Conventional Commit title` check requires the title's impact to equal the version change. So the change is **a release, Workflow 2.29.8, a `fix:`
patch** (the precedent of 2.29.6 for command wording and 2.29.7 for test pins). `manifest.json` `workflow_version` 2.29.8; the nine changed records (the three commands, R, the obligations suite, the integration suite,
`workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`) take their sentence ("command-wording-pins (workflow-2.29.8)"), `sha256` and `size`; counts and `distribution` do not move;
`manager.conformance.suites` is measured by `release.py manager-block --write` (the obligations suite 314 to 316, the integration suite 383 to 385, if the six tests above are the only additions). `WORKFLOW_RELEASE`
becomes 2.29.8 with its pinned assertions and the document's lines (protocol 1.5, no operation or flag changes). The posture says the way back to 2.29.7 needs nothing undone (wording and tests only: the older text is back, no state
or flag differs). `tools/release/release_test.py` gets a 2.29.8 class, carries the suite-count pin, and the 2.29.7 class gives up the pins a newer release owns. `docs/release-history.md`: the 2.29.8 row and its stamp. The release
workflow publishes it; the Manager lock and install pull requests follow (orchestrator).

### D-Staging

CP1 changes shipped files whose records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w57-tmp` (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script, in the clone only,
(a) recomputes `sha256` and `size` of every record whose file differs, (b) measures `manager.conformance.suites` with `release.py manager-block --release-dir <scratch> --write`, (c) rewrites the pins in
`tools/release/release_test.py` that read the counts (as the lstat-errors plan did); those pins are CP2's change in the real tree. Then the "Verification commands" of `docs/RELEASING.md` run from the clone (the tools tests
with the zlib-ng interpreter `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`), and the new tests also run under the reaper.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The wording, its pins and roadmap row 50 | - | 2 | 1 |
| CP2 | Release 2.29.8 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The wording, its pins and roadmap row 50

**Files:** `payload/.claude/commands/apply-pr-review.md`, `payload/.claude/commands/apply-implementation-review.md`, `payload/.claude/commands/apply-functional-review.md`,
`payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`, `payload/scripts/workflow_integration_test.py`, `docs/ROADMAP.md`.

- D-Wording as text in the three command files and in R's two refusals; D-Pins as code: the class `TestCommandWordingPins` (two tests) and the three golden hashes with their comment lines in the integration suite, the class
  `RetentionCrossDeviceWording` (two tests) in the obligations suite, no existing test touched; the seven mutations run in scratch copies, each result recorded. `docs/ROADMAP.md` carries row 50 (`Current`) from this plan.
- R changes in exactly two string literals (`git diff c2068ca -- payload/scripts/workflow_retention.py` shows two hunks, only next-step text); nothing else of `payload/` changes in CP1.

**Verification:** D-Staging (nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` in the zlib-ng interpreter; the new tests under the reaper); each mutation fails its pin only.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.8

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` 2.29.8 with its pinned assertions and the document's matching lines (protocol 1.5); `manifest.json` per D-Release; the history row and stamp; the 2.29.8 class and the 2.29.7 class's given-up pins.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean;
the tools tests pass in the zlib-ng environment; `check-title "<the title above>" --agree` agrees; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 4. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Nothing runs against the real repository, the forge or the network. `$S` is a scratch directory under `$TMPDIR`.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --stat c2068ca -- payload` | CP1: the three command files, R and the two test suites. CP2 adds the protocol script, its test and the protocol document |
| 2 | `git diff c2068ca -- payload/scripts/workflow_retention.py \| grep '^[-+][^-+]'` | two hunks, each one next-step literal replaced by another: the two next steps, nothing else |
| 3 | in a staged fixture, `python3 -B workflow_integration_test.py TestCommandWordingPins` and `python3 -B workflow_state_completion_obligations_test.py RetentionCrossDeviceWording` | 2 tests OK each |
| 4 | the seven mutations of D-Pins on scratch copies in the fixture, the class after each | m1 to m7: exactly the test (and `subTest`) of its row fails; m1 to m5 also fail the golden-hash test of their file |
| 5 | the same mutations m6 and m7 against `RetentionRemove` | green: the gap the pins close |
| 6 | `reaper.py --report R.json --chunk-id wording -- python3 -B <obligations suite> RetentionCrossDeviceWording` | status 0; orphans: only `[git]`, all `exited` |
| 7 | read W1 to W3 against D-Wording; read the two other commands' sentences for the same clauses | identical clauses; no `same_content` token added to `apply-pr-review.md` |
| 8 | (full environment) the nine payload suites from a staged fixture; the `tools/release` tests with the zlib-ng interpreter; `tools/docs` tests and checker; `check-manager-block` with `--manager-releases` | all pass; the manifest says 2.29.8; `check-title` agrees |
| 9 | `git diff --name-only c2068ca -- .claude scripts .workflow-manager .github CLAUDE.md` | nothing |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #190 1 | W1, c1, m1 to m3 | CP1 | the `same_content` rule is replaced by the true statement (D-Pr-Outcome) |
| #190 2 | W2, c2, m4, m5 | CP1 | |
| #123 6 | W3, e1, e2, m6, m7 | CP1 | both sites |
| #190 3 | not taken | - | owner decision: the issue has no comment; not touched |
| #190 4 | not in the brief | - | not touched |
| Release | 2.29.8, a `fix:` patch | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/command-wording-pins-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand for `payload/`, `tools/`, `fixtures/`,
`templates/`, `manifest.json` and `docs/release-history.md` (excluded at the plan stage, protected at the implementation stage); every path a checkpoint's **Files** paragraph names is classified at both stages.
`docs/ROADMAP.md` stays excluded at both stages (acceptance edits it after the technical approval), so row 50 is a classified, unprotected change.
