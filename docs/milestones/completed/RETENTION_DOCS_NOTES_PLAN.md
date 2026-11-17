# W56: three retention documentation notes: the downgrade row, the remove section and the raw reaper reports (Revision 2)

Pull request title: `docs: say what a downgrade restores, where the folder goes after the rename and keep the raw reaper reports`
(release impact none: no file under `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changes; `release.py check-title` prints `impact=none`).

- **Work item:** `retention-docs-notes` (`process`, governing version `2.2`; docs only: no release)
- **Requested by:** the Manager Super Orchestrator, owner standing order (queue the reviewed follow-ups when the queue is empty; reviewed against
  `origin/main` on 2026-11-16): row 49 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#143 points 1 and 2 and #188, each read with all its comments.
  **Branch:** `milestone/retention-docs-notes`
- **Base commit:** `9aacb87` (`origin/main` after #196: the release source is 2.29.7; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2 (round 1 of the local review applied: RDN-L1-001, -002 and -003 accepted; no rejection). One mechanism: three documentation points, no payload change, no release. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. The investigation: each point on main at `9aacb87`

| Point | State on main (file:line) | Class |
| --- | --- | --- |
| #143 pt 1, the 2.25.5 row | `docs/release-history.md:26` ends "Back to 2.25.4 with `workflow-manager update` (minimum Manager 1.13.0) restores the traceback at three places and `pack_failed` at the pack". The row's own body (same line) says a state file that is not valid UTF-8 was a `UnicodeDecodeError` traceback, fixed at `payload/scripts/workflow_retention.py:128`, and that a tracked path that is not UTF-8 under a single-byte locale was counted and now refuses `repository_unknown` (`:169`, `git ls-files`; at `v2.25.4` the call used `text=True`, lines 155-156, so under a UTF-8 locale it was a traceback and under a single-byte locale the path was counted). The downgrade sentence omits the tracebacks | TRUE-FIX-NEEDED |
| #143 pt 2, remove section | `docs/RETENTION.md:575` to `:579` say an unreadable symlink is refused "at the same places, before the rename and after it" and say nothing of where the folder is. The engine renames the folder back for a refusal after the rename: `workflow_retention.py:1915` to `:1931` (the refusal handler; `_restore` is called at `:1924`, the message ending "the folder is back in <.ai-review/id>" is added at `:1930`), except a leftover whose verification could not complete (`:1918` to `:1922`: it stays in `.removing/<id>`) | TRUE-FIX-NEEDED |
| #143 pts 3 and 4 | pt 3 is a test assertion (payload), pt 4 is engine work | out of scope (payload; the comment of 2026-11-14 says pt 4 is in progress elsewhere) |
| #188, the raw reaper JSON | `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md` (lines 13 to 16 and 68 region) records only the summary. The two raw reports still exist in the item's scratch directory `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w53-tmp`: `r.json` (a run of the same recorded command, file written 2026-11-15 12:58:17Z, after the evidence text was committed in `ddc2366` at 12:55:44Z: status 0, `supported` true, 78 `[git]` and 1 `git maintenance run --auto --quiet --detach`, all `exited`; every run writes the same `$TMPDIR/r.json`, so it is not the run the evidence text calls "this run", whose report was overwritten and cannot be reconstructed) and `reaper-pcms.json` (written 12:22:39Z, before plan approval `968e1d4` at 12:50:35Z: the investigation run, 77 and 2, all `exited`). Both were read and counted | TRUE-FIX-NEEDED |
| #188, the A12/A15 mutation logs | the mutation runs were terminal output; the scratch directory holds the mutated copies (`mut-m0` to `mut-m3`, `fx-m1` to `fx-m3`, `fx-u`) and no output file of any run (checked: no log names `m1`, `Ran 2 tests` or `AssertionError`). The results exist only as the summary table of the evidence file | NOT RECONSTRUCTIBLE: dropped, said so in the evidence file; no log is invented (a new run would be a new record, not the original) |

`docs/RETENTION.md` and `docs/release-history.md` are maintainer pages outside `payload/`; neither is a manifest artifact (`manifest.json` names them only inside two rationale strings),
so editing them moves no digest. `tools/release/release_test.py` reads the 2.25.5 row by substring (`restores the traceback`, `nothing needs undoing`, `v2.25.5`, `2.25.4`): the new sentence keeps all of them.

## 1. Goal and scope

Docs only. No file under `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json` changes, so there is no version change and no release. This repository's own installation
(`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks, the conformance workflow) stays untouched; the evidence file and the
two JSON files added next to it are this item's own documents, not managed ones. No issue is closed; one comment per issue, posted after acceptance (D-Comments).

Open decisions: none; the plan finalizes no open decision row (this repository has no technical-decisions page).

## 2. Design

### D-History (#143 pt 1)

In the 2.25.5 row only, the downgrade sentence becomes: "... restores the traceback at three places, the `UnicodeDecodeError` traceback for a state file that is not valid UTF-8 and for a tracked path that is not UTF-8 under a UTF-8 locale (under a single-byte locale 2.25.4 counts such a path again), and `pack_failed` at the pack; the archives and the engine data are unchanged, so nothing needs undoing." Nothing else in the row or in any other row changes.

### D-Remove (#143 pt 2)

In `docs/RETENTION.md`, the sentence at 575 to 579 gains, after "before the rename and after it,": that after the rename the folder is renamed back into `.ai-review/` and the message says "the folder is back in" its place (a leftover whose verification could not complete stays in `.removing/<id>`, as the paragraph above already says for a leftover). The user-page rules hold: no internal milestone id, the page header unchanged.

### D-Evidence (#188)

Two files are added next to `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`: `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_REAPER_REPORT.json` (byte copy of `r.json`, a later run of the recorded command with the same counts) and
`docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_REAPER_INVESTIGATION.json` (byte copy of `reaper-pcms.json`). The evidence file's "Point 1 (#170)" section names both with their `sha256` and size,
says which run each is (the report file is a run of the same command written at 2026-11-15 12:58:17Z, after the evidence text, with counts 78 and 1; it is not the run the text calls "this run", whose report was overwritten and is not reconstructible, like the mutation logs; the investigation file is the 77 and 2 run), and states that the A12/A15 mutation logs were never saved and cannot be reconstructed, so the table remains the only record of those runs. No existing sentence of the evidence file is changed.

### D-Declaration

The generated declaration is adjusted before publication, at both stages: `docs/RETENTION.md`, `docs/release-history.md` (the template names only itself and leaves a docs page unclassified, fail-closed), the evidence file and its two JSON files are
`implementation_stage.protected_paths`; at the plan stage they are excluded (the deliverables of the implementation, like the release pages of earlier items); `payload/`, `tools/`, `fixtures/`, `templates/` and `manifest.json` are protected at the
implementation stage so that a change there is seen (the item changes none). `docs/ROADMAP.md` stays excluded, as in the template.

### D-No-write proofs and mutation

Docs have no failure path to prove. The checks are exact: `git diff --name-only 9aacb87` lists only this item's documents and none of the paths above; the 2.25.5 row differs from the base by the one sentence; the two JSON files are byte-identical to the scratch originals (`cmp`); the checker and the tests that read these pages stay green.

## 3. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The three notes and roadmap row 49 | - | 1 | 1 |

<!-- CP1 -->
### CP1 — The three notes and roadmap row 49

**Files:** `docs/release-history.md`, `docs/RETENTION.md`, `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`, `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_REAPER_REPORT.json`, `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_REAPER_INVESTIGATION.json`, `docs/ROADMAP.md`.

- D-History, D-Remove and D-Evidence as written; `docs/ROADMAP.md` carries row 49 (`Current`) from this plan.
- No file of the release source changes: `git diff 9aacb87 --stat -- payload tools fixtures templates manifest.json` is empty.

**Verification:** `docs/RELEASING.md`, "Verification commands": `tools/docs` tests and `check_docs.py`; the `tools/release` tests in the zlib-ng interpreter (`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`);
`check-manager-block` with `--manager-releases`; the nine payload suites from a stock `release.py stage-conformance --commit HEAD` fixture (unchanged files, run for the record); `check-title "<the title above>"` prints `impact=none`; `workflow-manager verify .` is clean.
<!-- /CP1 -->

## 4. Functional review (for the later checklist)

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `git diff --name-only 9aacb87` | the plan, registry, mapping, artifacts and dispositions files, the six paths of CP1 and the state file; nothing under `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json`, `.claude/`, `scripts/`, `.workflow-manager/`, `.github/` |
| 2 | `git diff 9aacb87 -- docs/release-history.md` | one line changed (the 2.25.5 row), the added words name the `UnicodeDecodeError` traceback for a state file and for a tracked path under a UTF-8 locale (and the single-byte case) |
| 3 | `git diff 9aacb87 -- docs/RETENTION.md` | one sentence extended: the folder is renamed back into `.ai-review/` after the rename |
| 4 | `cmp` of each JSON file with its scratch original; `sha256sum` against the evidence file | identical; the digests match the text; the text calls the report file a later run (written 12:58:17Z, counts 78 and 1), never "this run" |
| 5 | `python3 -I tools/docs/check_docs.py`, the `tools/docs` and `tools/release` tests | all pass |
| 6 | `python3 -I tools/release/release.py check-title "<the title above>"` | `impact=none` |

## 5. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #143 pt 1 | D-History | CP1 | |
| #143 pt 2 | D-Remove | CP1 | |
| #143 pts 3, 4 | not here | | payload and engine work |
| #188 raw reaper JSON | D-Evidence, two files | CP1 | |
| #188 mutation logs | dropped | CP1 | not reconstructible, said in the evidence file |
