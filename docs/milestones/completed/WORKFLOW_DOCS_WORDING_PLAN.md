# W62: two documentation sentences — the amendment phase limit and the findings-record output (Revision 1)

Pull request title: `docs: state the amendment phase limit and the findings-record output`
(`python3 tools/release/release.py check-title` prints `impact=none`: no shipped file changes, so there is no release and the manifest's version does not move).

- **Work item:** `workflow-docs-wording` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, a cleanup item. It has **no `docs/ROADMAP.md` row**: the item is not a roadmap milestone, and the roadmap is untouched.
- **Issues:** RodrigoFAbreu/workflow#173 point 1 and #161 point 1, each read with all its comments (#173 has none; #161 has one, the owner's "points 2 and 3 fixed, still open: 1").
  **Branch:** `milestone/workflow-docs-wording`
- **Base commit:** `7a486a296617a60cea51d8437d2718335c4b7ed0` (main after #209: the release source is 2.29.11; automatic gates, default `2.2`, no backlog file)
- **Plan revision:** 1. One mechanism: two documentation sentences. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. The investigation: both points on main at `7a486a2`

| Point | State on main (file:line) | Class |
| --- | --- | --- |
| #173 point 1: the plan route has no phase limit | `docs/common-problems.md` 11-14 ("An approval became stale after a change") says "for a plan approved and then changed, `/request-plan-amendment` and then `/milestone-plan`, both review stages and the plan approval" and names no phase. The engine refuses `/request-plan-amendment` outside the two phases of `_AMENDMENT_REQUEST_ALLOWED_PHASES` (`payload/scripts/workflow_state.py` 14828, refusal at 14944-14947: `WrongPhaseForAmendmentRequestError`, "requires phase in ['IMPLEMENTING', 'SELF_REVIEWING_IMPLEMENTATION']"). `payload/.claude/commands/request-plan-amendment.md` enters `AMENDING_PLAN` from those two phases, and `payload/docs/ai-workflow/REVIEW_PROTOCOL.md` 699-702 already says "(admitted only at `IMPLEMENTING` or `SELF_REVIEWING_IMPLEMENTATION`)". The page is incomplete, not false | TRUE-FIX-NEEDED |
| #161 point 1: the 2.28.0 row understates the output | `docs/release-history.md` 23 (the 2.28.0 row) says "it exits 0 with the record path (or nothing, for an item with no finding)". The release's own code (`git show v2.28.0:payload/scripts/workflow_state.py`, `_write_findings_record_cli`, 20455-20498) ends `print(json.dumps({"paths": [...]}, sort_keys=True, indent=2))` and returns 0, and `write_finding_dispositions_record` (same file, 16746-16758) returns `[]` for an empty ledger and otherwise the record path plus the dispositions file's path when that file exists. So success always prints JSON, never "nothing". `docs/exit-codes.md` 31 is already correct ("the paths to stage, the record and the dispositions file when it exists, `[]` for an item with no finding"), and the row's own earlier clause already says "prints `{paths}`" | TRUE-FIX-NEEDED |

Kept, out of scope: #173 points 2 and 3 (a plan sentence of a finished item; over-100-column lines, which the issue says to leave unless a real change moves them: this change re-wraps nothing that is not its own), #161 points 2 and 3 (fixed on main, per the owner), and the mapping-R4 naming point (a historical plan artifact).

**Manifest check.** `grep -n 'common-problems\|release-history' manifest.json` finds nothing: `docs/common-problems.md` and `docs/release-history.md` are neither a payload file nor a manifest record, `tools/release/release_test.py` is not one either, so no record, digest, count or version moves. If a record would move, D-Stop applies.

## 1. Goal and scope

Two sentences, each pinned. No payload file, manifest field, command file, engine message, other page, roadmap row or release. The tools test file gains assertions inside two existing methods and no test method (the counts of the `tools/release` tests do not move). This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance workflow) stays untouched.

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page).

## 2. Design

### D-Wording-1 (`docs/common-problems.md`, the plan route)

After "both review stages and the plan approval" (on the same line, so the two pinned substrings `for a plan approved and then changed, \`/request-plan-amendment\`` and `and then \`/milestone-plan\`, both review stages and the plan approval` stay byte for byte, as does `tools/release/release_test.py`'s `WordingPassPlainCommandsReleaseTest`), insert one parenthesis, wrapped like its neighbours: "(a plan amendment is possible only while the work item is at `IMPLEMENTING` or `SELF_REVIEWING_IMPLEMENTATION`; at any other phase `/request-plan-amendment` refuses and names the phase)". It is true of the engine (the refusal above names the phase) and says nothing of `/milestone-plan`, which the plan-stage phases admit. The page's "Last checked with: Workflow 2.29.5." line is pinned by `tools/release/release_test.py` (4577) and stays.

### D-Wording-2 (`docs/release-history.md`, the 2.28.0 row)

The row is a published-release record: change exactly one clause, byte for byte elsewhere. Replace "it exits 0 with the record path (or nothing, for an item with no finding)" by "it exits 0 with the paths to stage (the record, and the dispositions file when it exists; `[]` for an item with no finding)". That is what 2.28.0 printed (section 0). `git diff --word-diff` must show only that clause on that line, and `git diff --stat` one line changed in the file.

### D-Pins (a pin per changed sentence; each neighbour is already pinned)

- The common problems page's neighbouring sentences are pinned by `WordingPassPlainCommandsReleaseTest.test_the_pages_carry_the_corrected_wording_and_their_last_checked_line` (`tools/release/release_test.py`, near 4477): after its last two `assertIn`, add `self.assertIn("a plan amendment is possible only while the work item is at `IMPLEMENTING` or `SELF_REVIEWING_IMPLEMENTATION`", " ".join(problems.split()))` (whitespace-normalized, because the sentence wraps).
- The 2.28.0 row's neighbouring sentences are pinned by `AcceptanceFindingsFloorReleaseTest.test_the_release_history_rows_name_the_release_and_the_way_back`: add the new clause to its needles and `assertNotIn("(or nothing, for an item with no finding)", self.row())`.
- Neither change adds or removes a method; a docs page has no failure path of its own, so there is no no-write proof to make: the failure-only mutation of each pin is to revert its sentence in a scratch copy, where the new assertion fails and every old pin still passes.

### D-Stop

If a manifest record, digest, count or version would move, or if a pinned substring of either page would not survive, **stop**, record it as a finding in this plan and exclude that point. If any existing test changes its result on the unmodified tree, stop.

### D-Staging

No shipped file changes, so stock `stage-conformance --commit HEAD` stages the working tree's commit as it is (no scratch clone, no adjusted record). The "Verification commands" of `docs/RELEASING.md` run from the repository root: the nine payload suites from the staged fixture, `tools/release` in the zlib-ng interpreter `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`, the `tools/docs` tests, `check_docs.py`, and `check-manager-block` with `--manager-releases`. The pins run under the Manager's orphan rule (the reaper) as well: `reaper.py` on the two test classes. Nothing runs an archive, remove or prune command against a real repository.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The amendment phase limit in the common problems page | - | 1 | 1 |
| CP2 | The findings-record output in the 2.28.0 history row | CP1 | 1 | 1 |

<!-- CP1 -->
### CP1 — The amendment phase limit in the common problems page

**Files:** `docs/common-problems.md`, `tools/release/release_test.py`.

- D-Wording-1 and its pin of D-Pins; the mutation reverts the sentence in a scratch copy (the new assertion fails, the old pins pass).

**Verification:** D-Staging; `git diff --stat` shows these two files; no `manifest.json` or `payload/` change.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — The findings-record output in the 2.28.0 history row

**Files:** `docs/release-history.md`, `tools/release/release_test.py`.

- D-Wording-2 and its pin of D-Pins; `git diff --word-diff` shows the one clause; the mutation reverts it in a scratch copy.

**Verification:** D-Staging in full; `check_docs.py` clean (no internal milestone id in a page); `git diff 7a486a2 --stat` lists the three files of the two checkpoints only (the two pages and `tools/release/release_test.py`, and the plan's own bookkeeping), nothing under `payload/`, `manifest.json`, `.claude/`, `scripts/` or `.workflow-manager/`.
<!-- /CP2 -->

## 4. Functional review (for the later checklist)

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff 7a486a2 --stat -- docs/common-problems.md docs/release-history.md tools` | the two pages and `tools/release/release_test.py` only |
| 2 | `git diff --word-diff 7a486a2 -- docs/release-history.md` | one line, one clause replaced |
| 3 | `git diff 7a486a2 --name-only -- manifest.json payload .claude scripts .workflow-manager .github CLAUDE.md` | nothing |
| 4 | the verification commands of D-Staging | all pass; `python3 tools/release/release.py check-title "<the title>"` prints `impact=none` |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #173 1 | D-Wording-1 | CP1 | |
| #161 1 | D-Wording-2 | CP2 | |
| #173 2, 3; #161 2, 3 | not taken | - | fixed, a finished item's plan prose, or deferred (section 0) |
| Release | none | - | documentation only; no roadmap row |

The artifact declaration `docs/ai-workflow/registry/workflow-docs-wording-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and extended by hand: `docs/common-problems.md`, `docs/release-history.md` and `tools/` are classified at both stages (excluded at the plan stage, protected at the implementation stage), so that every path a checkpoint's **Files** paragraph names is classified at both stages and every deliverable is protected; `docs/ROADMAP.md` stays excluded at both stages and is not changed.
