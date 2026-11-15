# W54: Workflow 2.29.6 — an implementation bundle shows the test record and the fixes of every revision up to its own (Revision 4)

- **Work item:** `bundle-revision-sections` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner standing order (queue the reviewed follow-ups when the queue is empty; reviewed
  2026-11-14, still true): row 47 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issue:** RodrigoFAbreu/workflow#142 (read with all comments: none), found by the Controller lane's local implementation review
  (LOCAL-IMPL-R2-001 and R3-001). **Branch:** `milestone/bundle-revision-sections`
- **Base commit:** `7a52f49f100b843f5b77ceaa66018a7c3397f7b2` (main after #189: release source and own installation are 2.29.5; automatic gates,
  default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 4 (applies LOCAL-PLAN-R3-001 and the two optional findings of local round 3, on top of revision 3's LOCAL-PLAN-R2-001 and the optional finding of local round 2, revision 2's LOCAL-PLAN-R1-001 to -003 and the three optional findings of local round 1). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: who writes the two files (main at `7a52f49`)

Read in `payload/`, run on hand-built directories (Python 3.14, no forge, no network; probes live outside the repository). Classes:
TRUE-FIX-NEEDED, ALREADY-FIXED, KEEP.

| Part | State on main (file:line) | Class |
| --- | --- | --- |
| The generator, `prepare-ai-review.sh` | at the implementation and post-fix stages it only creates an **empty stub** of `REVIEW_REQUEST.md`, `IMPLEMENTATION_SUMMARY.md`, `TEST_RESULTS.md`, `CONTEXT_FILES.txt`, `PLAN.md` when one is missing and never overwrites (482 to 489); `workflow_fingerprint.py` 3006 names them as author inputs. **The generator never writes a heading or a body, and there is no template file for either** (`templates/` has no bundle file). The "implementation revision 1" heading is the worker's own text | KEEP: not a generator feature; the fix is command text and the protocol contract |
| The commands that fill them | `milestone-implement.md` 400 to 408 (summary "what was built, per checkpoint"; test results "exact commands + results": no revision, no history); `apply-implementation-review.md` 167 (rejections go into the summary) and 223 to 232, `apply-functional-review.md` 212 and `apply-pr-review.md` 110 (each refreshes only the `implementation_revision:` line and the `review_content_id:` line, never the test record or a round entry) | TRUE-FIX-NEEDED, four command files |
| The contract, `REVIEW_PROTOCOL.md` 497 to 510 | the summary "what was built" with the revision line; the test results "exact commands run and their real outcome", plan-stage line rules only. Nothing says what a later revision keeps. The tree at 303 and 304 says only "author-written" | TRUE-FIX-NEEDED, one paragraph pair |
| `assert_stage_completeness` (`workflow_fingerprint.py` 3948 to 3999) | at implementation and post-fix it reads `IMPLEMENTATION_SUMMARY.md` with `^implementation_revision: (\d+)$` and `.search` (**the first match**); a missing or different value withdraws the bundle. It reads nothing of `TEST_RESULTS.md` there (the `stage: plan (revision N)` checks, 4010 to 4060, are plan-stage only) | KEEP, and the form must never put a second line of that shape in the summary (D-Form) |
| `bundle_id` (`compute_bundle_id`, 4550) | hashes every file under the bundle by bytes; any worker text already moves it, so a longer record is no new case. A line `bundle_id: <64 hex>` in any file but the manifest is refused (4535); the form has none (commit ids are 40 hex) | KEEP |
| `review_content_id` (`compute_review_content_id_implementation_stage`, 2021) | hashes the protected tracked content scoped to the base, never a `.ai-review/` file (gitignored). **Run:** the id of a scratch repository with `TEST_RESULTS.md` empty and with a revision section is the same digest | KEEP: no binding, approval or stale check moves |
| Bundle completeness check for the record | none exists, and none is added (D-NoCheck) | KEEP |
| The Controller (`controller/` of 1.31.1, 1.27.13, 1.19.1) | grep, all three: `evidence.py` 2203, 2258, 2296, 2680, 2742, 2784 and 2799 (the same lines in each version) name the files; only 1.31.1 also has `codex_carry.py` 63 and 64, which carry the files **whole** between worktrees. No version parses their text: `_author_file_has_content` (2206) checks only that a file is non-empty. It reads the state key `implementation_revision`, which does not move. No verdict header, `MANIFEST.md` field or file name changes, so **no part is stopped**; the protocol stays 1.5. **One conflict:** `_implementation_bundle_recovery_steps` (`evidence.py` 2797 to 2800) tells the operator to "write/refresh `<bundle_dir>/TEST_RESULTS.md` with the exact commands and results of this round"; read literally under D-Form that replaces sections 1 to N-1. Handled by D-Form's "this round means section N" rule, and a Controller follow-up issue (orchestrator, outside this item) to reword it | KEEP, with the conflict handled in the contract |
| `bootstrap-workflow-v2.md` 192, `prepare-review.md` 35, `review-implementation.md` 130 and 207 | the bootstrap of a finished item; ad-hoc bundles (no revision); the reviewer who reads and re-runs what the files claim | KEEP, not touched |

## 1. Goal

Ship Workflow 2.29.6, a **`fix:` patch** (D-Release): **a bundle of revision N shows the test record and the fixes of every revision up to N, in a
stable documented form.** Because a worker writes both files, the change is the text a worker follows (four command files) and the contract a
reviewer reads (`REVIEW_PROTOCOL.md`); the generator, the identifiers, every check and the state do not change. Not a new mechanism.

**The Controller parses none of this** (section 0): it checks only that the files are non-empty and names them in recovery text and a carried-file list; had a change touched a name or field it reads, that part would stop here. Its recovery wording "the exact commands and results of this round" is read as section N only (D-Form).

### Hard limits (the owner's sizing rule)

- **Two checkpoints** (CP1 the text, the contract and the tests; CP2 the release 2.29.6), under about 350 lines of plan. Past that, split before review:
  the commands first, the contract second.
- This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, managed blocks,
  the conformance workflow) stays untouched; the copies under `payload/` change. No CI workflow file changes. No gate or approval semantics change.

## 2. Design

### D-Form: the stable form (written once, in `REVIEW_PROTOCOL.md`; the commands point to it and repeat the headings)

`TEST_RESULTS.md` (implementation and post-fix stages) is a list of sections, ascending, one for **every** revision from 1 to N (N is the counter
`record_bundle_generation` just wrote), each the same shape, the heading matching `^## Implementation revision (\d+)$`:

```
## Implementation revision 2
- commit: <40-hex sha the commands ran at>
- commands: <each exact command, one per line>
- result: <the real outcome of each; a command not run says so and why>
```

Sections below N are **carried forward unchanged**: never edited, never relabelled as a run of this round. Section N is written fresh at this round,
against this round's commit. **The rule's sentence is reworded, not only kept (LOCAL-PLAN-R3-001):** `REVIEW_PROTOCOL.md`'s "Never state a check passed unless it actually ran in this session" (the `TEST_RESULTS.md` paragraph, 502 to 503) becomes "section N states only checks that actually ran in this session, at its stated commit; sections below N are the record of their own commit and are never restated as this round's runs", so carrying sections 1 to N-1 forward does not contradict the paragraph. The same paragraph says the reviewer reruns section N only; earlier sections are history tied to their own `commit:` line (`review-implementation.md` step 5 stays untouched, section 0). A `same_content` round keeps N and rewrites
section N with its new commit and results. The plan-stage lines (`stage: plan (revision N)`, `head:`) are unchanged and plan-stage only.

`IMPLEMENTATION_SUMMARY.md` keeps the one line `implementation_revision: <N>` first, **and no other line of that shape** (the check takes the first
match), then one entry per round, ascending, headed `^## Round (\d+)$`, where the round number **is** the implementation revision (a `same_content` round opens no entry, so there is no second counter): round 1 is what was built per checkpoint;
each later round lists every finding applied (file, line, test) and every finding rejected with its evidence, and the commit that holds the fix. A
`same_content` round adds its lines to the entry of round N and opens none. The headings are not the label line, so the check is unchanged.

**Two rules for a worker who finds the files short** (stated once in the contract, repeated in each command): (1) any instruction to write or refresh `TEST_RESULTS.md` or `IMPLEMENTATION_SUMMARY.md` "for this round", including a Controller's recovery text, means section N and round entry N only, never the earlier ones; (2) when `<bundle_dir>` was withdrawn and regenerated, the generator has stubbed both files empty, so sections 1 to N-1 and round entries 1 to N-1 are restored **byte for byte** from the newest (by modification time, since the token is a `uuid4` hex) `current.rejected-*` quarantine next to it whose files hold those sections, checking that the restored sections run from 1 to N-1 (two withdrawals in a row leave the generator's empty stubs in the newest one and the history in an older one) (`REVIEW_PROTOCOL.md` "Bundle location"; the Controller already names it as the restore source), never rewritten from memory; with no quarantine, the worker says so in the entry and states no earlier result it cannot show.

### D-Commands: where each command writes it

`milestone-implement.md` (the first bundle): both files in the form above, one section and one entry. `apply-implementation-review.md`,
`apply-functional-review.md` and `apply-pr-review.md` (each later round): at the step that refreshes the `implementation_revision:` line, also
append section N and round entry N, keep the earlier ones untouched, and re-run the full suite for section N. The existing step order is kept: the
text is added to the step that already writes these files, before the generator run, so no step moves and no commit-order rule changes. Each command also carries the two rules above in one sentence each.

### D-NoCheck: no completeness check is added

A hard check of the record (a heading per revision) would withdraw bundles the commands of every installed release write today, and a worker
mid-round at an update would lose its bundle; the cost it prevents is minutes of reading at low priority. The contract and the tests pin the
form; the generator stays byte-identical. A later item may add an advisory.

### D-Golden: existing bundles behave the same where no section is needed

No script under test changes (the generator, the fingerprint and the state script stay byte-identical; the release constant and the integration test are the only scripts touched). Proof by a driver run of `base/` (`git archive` of the base) and `cand/` (the working tree):
for a revision-1 bundle in the old shape (empty or free-form record, one label line) `compute_bundle_id` and `assert_stage_completeness` give the same
digest and the same verdict; the implementation-stage `review_content_id` is the same with the record empty, old-form or three-section; a
three-section bundle passes at N=3 and a stale label fails with the same refusal and no write.

### D-Pins: every test, doc and fixture that pins the old bytes

- `payload/scripts/workflow_integration_test.py`: the table of command digests (`milestone-implement.md` 949, `apply-implementation-review.md` 1204,
  `apply-functional-review.md` 1452, `apply-pr-review.md` 1456) takes the four new digests with a comment line each; the tests listed in D-Tests are added.
- Read and confirmed to stay passing (CP1's author re-runs them): the structural regex tests over the edited steps in the same file, among them the bounded-branch revert pattern on `apply-functional-review.md` (2235 to 2247: exactly one match from `**Then refresh` to `[work_item_id]`.`). **Placement chosen (LOCAL-PLAN-R2-001):** in `apply-functional-review.md` step 4 the new sentences go **inside** that span, before the `Then run ./scripts/prepare-ai-review.sh ... post-fix` sentence, never between `round.` and `**Then refresh` (that breaks the regex anchor and raises the "update this mutation" error). Reason: `_extract_numbered_steps` returns the whole step as one block and `_generation_authoring_violations` (1864 to 1878) looks in it for `implementation_revision: <N>`, `assert_stage_completeness` and `withdraw`; today every such token of step 4 sits inside the span, which is why `test_the_reverted_command_fails_the_generation_authoring_conformance` (2265 to 2280) passes, asserting `"withdrawal and quarantine"` among the violations of the reverted copy. Text inside the span is removed by the revert along with the rest, so that assertion and the count-1 check both stay true; text outside it would survive the revert and fail the test. CP1's author re-runs both and the step-extraction assertions at 1864, 1973, 1978 and 2150.
- No test reads `REVIEW_PROTOCOL.md`'s digest (grep: none); `fixtures/` and `templates/` hold no bundle file; the demo suite's per-command
  declaration table and assertion counts (`workflow_state_demo_test.py` 1416 to 1449) are untouched because no text of them moves.
- `manifest.json` records of the changed files (CP2); `docs/release-history.md` row and stamp (CP2); the 2.29.5 class of `tools/release/release_test.py`
  gives up its release pins (CP2, D-Release). No `docs/*.md` page other than the history and the roadmap changes, and none of the shipped pages (`payload/docs`, the `docs/*.md` user pages) names a milestone id; the roadmap row and the later `docs/milestones/completed/` archive do, by convention (rows 46 and the acceptance archive).

### D-Tests (all in `payload/scripts/workflow_integration_test.py`, offline, no write outside a temporary directory)

- T1 each of the four commands names the two heading forms, the carry-forward rule, the "this round means section N" rule and the `current.rejected-*` restore rule; T2 `REVIEW_PROTOCOL.md` states the form once with both regular expressions and both rules, and scopes the "ran in this session" sentence to section N (the unscoped old sentence fails T2).
- T3 a three-round summary in the documented form passes `assert_stage_completeness` at 3 and fails at 2 (`StageCompletenessError`); T4 no round or section heading
  matches the label regex and the documented summary has exactly one label line.
- T5 the old-form bundle's `compute_bundle_id` equals a recorded literal (the golden; the hand-built bundle sets every file mode explicitly, `0o644`, with `0o755` where the literal records it, since the digest hashes modes and must not inherit the umask), T6 the `review_content_id` of a scratch repository is the same for
  an empty, an old-form and a three-section record.
- Failure-only mutations (the tests fail, nothing else does): m1 drop the heading rule, or the restore rule, from one command (T1), m2 add a second label line in the sample (T3, T4), m3 say a
  section is rewritten each round, or drop the quarantine restore rule, or restore the unscoped "ran in this session" sentence, in the protocol (T2). There is no new failure path in code, so there is no new no-write proof beyond T3's.

### D-Release

2.29.6, a **`fix:` patch**: the pull request title is `fix: ...` and the manifest's version change is the next patch (`docs/RELEASING.md`, "Titles": `fix` is
patch). It is not `feat:` because no capability, flag, key or script behaviour is added; a worker follows clearer text, as the earlier wording releases
(2.29.3, 2.19.2) shipped as patches. `manifest.json` `workflow_version` 2.29.6; the nine changed records (four commands, the protocol, the integration test,
`workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`) take their sentence, `sha256` and `size`; counts and `distribution` do not move;
`manager.conformance.suites` is measured by `release.py manager-block --write`. `WORKFLOW_RELEASE` becomes 2.29.6 with its pinned assertions and the protocol
document's lines (protocol 1.5). The posture says the way back to 2.29.5 restores the older command text and needs nothing undone (bundles in the new
form still pass, the generator being unchanged). `tools/release/release_test.py` gets a 2.29.6 class, carries the four-suite count pin (the
`workflow_integration_test.py` count moves by the tests added), and the 2.29.5 class gives up the pins a newer release owns. `docs/release-history.md`: the 2.29.6 row
and its stamp. The release workflow publishes it; the Manager lock and install pull requests follow (orchestrator).

### D-Staging

CP1 changes shipped files whose records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w54-tmp` (procedure of
`docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script, in the clone only, (a) recomputes `sha256` and `size` of each record whose file differs, (b) measures
`manager.conformance.suites`, (c) rewrites the one pin that reads the counts in `tools/release/release_test.py`; that pin is CP2's change in the real tree. Then the "Verification
commands" of `docs/RELEASING.md` run from the clone (the tools tests with the zlib-ng interpreter), and new tests also run under the Manager's orphan rule (the reaper).

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The form: four commands, the contract, the tests | - | 2 | 1 |
| CP2 | Release 2.29.6 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The form: four commands, the contract, the tests

**Files:** `payload/.claude/commands/milestone-implement.md`, `payload/.claude/commands/apply-implementation-review.md`,
`payload/.claude/commands/apply-functional-review.md`, `payload/.claude/commands/apply-pr-review.md`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `payload/scripts/workflow_integration_test.py`, `docs/ROADMAP.md`.

- D-Form and D-Commands as text; D-Tests; the four digests of D-Pins. `docs/ROADMAP.md` carries row 47 (`Current`) from this plan.
- No other file of `payload/` changes: `git diff 7a52f49 --stat -- payload` lists these six.

**Verification:** D-Staging (nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` in the zlib-ng interpreter; new tests under the reaper);
the driver of D-Golden identical on base and cand where nothing is to change.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.6

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` 2.29.6 with its pinned assertions and the document's matching lines (protocol 1.5); `manifest.json` per D-Release; the history row and stamp;
  the 2.29.6 class and the 2.29.5 class's given-up pins.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block`
(with `--manager-releases`) and `tools/docs` are clean; the tools tests pass in the zlib-ng environment; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 4. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, the forge or the network.** Setup, as bullets:

- `$S` is a scratch directory under `$TMPDIR`; `base/` is `git archive 7a52f49 payload` extracted there, `cand/` a copy of the working tree's `payload`;
- a fake `gh` that logs its calls, in `$HOME/wf-fakebin` (mode 0755, first on `PATH`; no flow may leave a line in `$HOME/wf-gh.log`):

```sh
#!/bin/sh
echo "gh called: $*" >> "$HOME/wf-gh.log"
exit 1
```

- `drive.py <payload-dir> <case>`, kept outside the repository, run as `python3 -I`, putting `<payload-dir>/scripts` first on `sys.path`. Cases: `bundle old|new3 <N>` builds by hand a bundle directory with the
  required files, an old-form or a three-section record, prints `compute_bundle_id`'s digest and `assert_stage_completeness`'s verdict at N and whether the directory hash changed;
  `ids` builds a scratch repository with a base commit, one changed tracked file and `.ai-review/x/current/TEST_RESULTS.md` empty, old-form and three-section, and prints the implementation-stage `review_content_id` each time.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --quiet 7a52f49 -- payload/scripts/prepare-ai-review.sh payload/scripts/workflow_fingerprint.py payload/scripts/workflow_state.py; echo $?`; `git diff 7a52f49 --stat -- payload` | `0` (the generator, the fingerprint and the state are identical); the stat lists the four commands, the protocol and the integration test (CP1), plus the protocol script, its test and the protocol document (CP2) |
| 2 | `git grep -c "^## Implementation revision" -- payload/.claude/commands payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, then the same on `7a52f49` | candidate: a count in each of the four commands and the protocol; base: no match |
| 3 | `drive.py` `ids` with `base/` and `cand/` | one digest, repeated three times, identical on both |
| 4 | `drive.py` `bundle old 1` with `base/` and `cand/` | identical digest, verdict ok, directory unchanged |
| 5 | `drive.py` `bundle new3 3`, then `bundle new3 2` with `base/` and `cand/` | at 3 ok, at 2 `StageCompletenessError` naming the label value, directory hash unchanged both times; same on both; the digest differs from the old form's and is the same on both |
| 6 | `grep -c "^implementation_revision: " <(sed -n '/^implementation_revision:/,$p' the sample summary the driver writes)`, and a grep of the two heading forms against `^implementation_revision: ` | one label line; no heading matches it |
| 7 | `grep -rn "TEST_RESULTS\|IMPLEMENTATION_SUMMARY" ~/.local/share/pipx/venvs/workflow-controller/lib/*/site-packages/controller` | `evidence.py` 2203, 2258, 2296, 2680, 2742, 2784, 2799 (file names and the recovery text `_implementation_bundle_recovery_steps`) and `codex_carry.py` 63 and 64 (a carried-file list); no parse of the text, no header or manifest field; the same `evidence.py` lines in tags v1.27.13 and v1.19.1 (`git grep` in the Controller repository) |
| 8 | for each of the four commands, `sha256sum` against the digest table of `payload/scripts/workflow_integration_test.py` | equal; the table has no stale digest |
| 9 | `grep -n "^| 47 " docs/ROADMAP.md \| cut -c1-120`; `python3 -I tools/docs/check_docs.py`; `git grep -n "bundle-revision-sections" -- docs ':!docs/ACTIVE_MILESTONE.md' ':!docs/ai-workflow' ':!docs/ROADMAP.md' ':!docs/milestones'` | row 47 present and `Current` (then `Done`); clean; no shipped page names the id |
| 10 | `git diff --name-only 7a52f49 -- .claude scripts .workflow-manager .github CLAUDE.md; git diff --name-only 7a52f49 -- docs/ai-workflow` | the first prints nothing; the second lists only this item's plan, registry, mapping and artifact files |
| 11 | (needs the full environment) the nine payload suites from a staged fixture; the three mutations in a scratch copy | all pass; each mutation fails its tests and no other |
| 12 | (needs the full environment) the `tools/release` tests with the zlib-ng interpreter, `tools/docs` tests, `check-manager-block` with `--manager-releases` | all pass, no skip; the manifest says 2.29.6 and `check-title "fix: ..." --agree` agrees |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #142 test record per revision | `TEST_RESULTS.md` section per revision, carried forward | CP1 | D-Form, D-Commands, T1 to T4 |
| #142 summary per round | one entry per review round applied | CP1 | D-Form, T3 |
| Generator and template | none writes content; no feature added | - | section 0, D-NoCheck |
| Ids and bindings | unchanged | CP1 | D-Golden, T5, T6 |
| Row 47 | a `fix:` patch, 2.29.6, the generator unchanged | CP1, CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/bundle-revision-sections-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand
for `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json` and `docs/release-history.md`; every path a checkpoint's **Files** paragraph names is classified at both stages. `docs/ROADMAP.md`
stays excluded at both stages (acceptance edits it after the technical approval), so row 47 is a classified, unprotected change.
