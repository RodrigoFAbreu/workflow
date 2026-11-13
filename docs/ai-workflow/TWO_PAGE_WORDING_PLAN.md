# W50: two page wording points: the retention row's lock-order cell and the acceptance row of the gates page (Revision 1)

- **Work item:** `two-page-wording` (`process`, governing version `2.2`; docs-only: no release)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-13 (queue the follow-up issues): RodrigoFAbreu/workflow#178, points 1 and 2 only; `docs/ROADMAP.md` row 43 (`Current` with this plan, `Done` at acceptance).
- **Branch:** `milestone/two-page-wording`
- **Base commit:** `8e1212b7aa388e168a01588eb9ba0cf8348ba969` (main after #179: release source 2.29.3; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. One checkpoint, with its anchor pair.

## 0. Phase 1: the investigation

Each point of #178 against main at the base commit.

| Point | Class | Evidence |
|---|---|---|
| 1. `docs/CONCURRENCY_INVARIANTS.md`, the retention row's lock-order cell says "Not verified for the order against the item's own checkpoint claim, because the code never takes one" | TRUE-FIX-NEEDED | The cell (line 97) first says the engine takes no state lock and imports nothing from `workflow_state.py`, then says "not verified" about an order that its own reason ("the code never takes one") makes empty: the two halves contradict each other. What is true: `payload/scripts/workflow_retention.py` imports `argparse`, `datetime`, `errno`, `fcntl`, `hashlib`, `json`, `os`, `re`, `stat`, `shutil`, `subprocess`, `tarfile` and `workflow_forge` (lines 65-85), and `workflow_forge.py` (lines 18-25) imports no Workflow module; the lowercase name `workflow_state` occurs nowhere in either file; the only lock is `fcntl.flock(adir_fd, ...)` (lines 1205, 1738, 1981); no word `claim` occurs in the engine. It does read `docs/ai-workflow/WORKFLOW_STATE.json` (`STATE_PATH`, line 121) without a lock: a read, not a lock, so the cell's claim ("takes no state lock") stays true. |
| 2. `docs/gates.md`, the acceptance row (line 48): "judged by the latest run of each check: a check that ran again counts by its latest run; where the order of runs cannot be established its worst run counts" | TRUE-FIX-NEEDED | The first clause after the colon repeats the sentence's own opening. The behaviour is right and stays: `payload/scripts/workflow_forge.py:_standing_state` (lines 206-226) takes the latest run when every other run had completed before it started, otherwise the worst. The clause to keep is the second one. |
| The other four points of #178 (the archived plan of the previous item) | KEEP, closed as "not editable" | `docs/ai-workflow/DOCS_RESTAMP_PLAN.md` and `docs/milestones/completed/DOCS_RESTAMP_PLAN.md` are bound by that item's approval; this plan does not touch them (flow 6 proves it). |

**Frozen tests.** `grep` of `tools/`, `payload/`, `fixtures/`, `templates/` and `manifest.json` for the page names finds only `tools/release/release_test.py` (lines 2921 and 3942) and a path string in `payload/scripts/workflow_state_test.py:3547`. Line 2921 pins the stamp `Last checked with: Workflow 2.19.2.` of the concurrency page: this item leaves every stamp unchanged. Line 3942 pins the release-window row (`Checkpoint-start release window`), not the retention row. No test or tool in those trees reads either sentence this item changes, or any word of the two new ones; `tools/docs/check_docs.py` checks the stamp line, links and internal ids, none of which change. So **no frozen test pins a sentence to be changed: no stop.**

**Release.** `docs/RELEASING.md` (lines 123 and 203): the release source is `manifest.json`, `payload/`, `fixtures/`, `templates/`, `tools/release/`, the CI workflow and `.gitattributes`; `docs/` is outside it and always allowed. Neither page is in `manifest.json`. So this item releases nothing: a `docs:` change with impact none, and the manifest keeps 2.29.3.

## 1. Goal and scope

Two statements in two shipped pages read true and say each thing once. Out of scope: `payload/`, `tools/`, the Manager repository, the archived plans, any behaviour change, any stamp.

## 2. Design decisions

- **D-Retention.** One sentence replaces the two in the cell: ``None of (1) to (9): the engine takes no state lock and no checkpoint claim, and imports nothing from `workflow_state.py` (`grep` finds no call).`` Every word is a fact of section 0. The rest of the row is unchanged.
- **D-Gates.** The words `: a check that ran again counts by its latest run;` become `;`, so the row reads `judged by the latest run of each check; where the order of runs cannot be established its worst run counts.` The clause about the worst run is kept as it is.
- **D-Stamps.** No `Last checked with` line moves: the concurrency page stays at 2.19.2 (frozen), the gates page is already at 2.29.3 and was re-checked by the previous item.
- **D-Roadmap.** Row 43, after row 42 and before the deferred row, in the style of the rows above: `Current`, `Done (accepted by policy; a docs: change, no release)` at acceptance. `docs/ACTIVE_MILESTONE.md` gets the usual active-milestone text.

## 3. Open decisions

None: `docs/TECHNICAL_DECISIONS.md` has no open row on page wording.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Reword the retention row's lock-order cell and the acceptance row; add roadmap row 43 | - | 1 | 1 |

<!-- CP1 -->
### CP1 — Reword the retention row's lock-order cell and the acceptance row; add roadmap row 43

**Files:** `docs/CONCURRENCY_INVARIANTS.md`, `docs/gates.md`, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`.

- **Read first, edit after:** re-read the line of each page and the evidence of section 0 on the branch; if the evidence changed, stop and say so.
- **The edits:** D-Retention in the concurrency page (one table cell), D-Gates in the gates page (one table cell), the roadmap row, the active-milestone text. Nothing else.
- **Done when:** `diff` of each of the two pages against the base shows one changed line; the two stamp lines are byte-identical to the base; `git diff --exit-code 8e1212b7aa388e168a01588eb9ba0cf8348ba969 -- payload tools fixtures templates manifest.json docs/release-history.md docs/RELEASING.md` exits 0.

**Verification:** flows 1 to 10 (offline), then 11 to 13 (full environment): `tools/docs` tests and `check_docs.py`; the nine suites from `stage-conformance --commit HEAD`; `tools/release` tests with the zlib-ng interpreter; `check-manager-block` with `--manager-releases`.
<!-- /CP1 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Flows 1 to 10 run offline: no network, no real `gh`, no install, no socket, no zlib-ng, no Python 3.12; nothing writes in the real repository. No flow needs the forge, so there is no fake `gh`. Setup, once, from the repository root, with `TMPDIR=/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w50-tmp`:

```sh
export REPO="$PWD" B=8e1212b7aa388e168a01588eb9ba0cf8348ba969
rm -rf "$TMPDIR/base" "$TMPDIR/cand" && mkdir -p "$TMPDIR/base" "$TMPDIR/cand"
git -C "$REPO" archive "$B" docs/CONCURRENCY_INVARIANTS.md docs/gates.md docs/ROADMAP.md | tar -x -C "$TMPDIR/base"
git -C "$REPO" archive HEAD docs/CONCURRENCY_INVARIANTS.md docs/gates.md docs/ROADMAP.md | tar -x -C "$TMPDIR/cand"
cat > "$TMPDIR/flows.sh" <<'SH'
# usage: flows.sh <n>; reads REPO, B, TMPDIR; greps name the two pages only, never docs/ACTIVE_MILESTONE.md
cd "$TMPDIR"; P1=docs/CONCURRENCY_INVARIANTS.md; P2=docs/gates.md
A='Not verified for the order'; C='a check that ran again'; K='where the order of runs cannot be established its worst run counts'
N='None of (1) to (9): the engine takes no state lock and no checkpoint claim, and imports nothing from `workflow_state.py`'
flat() { tr '\n' ' ' < "$1"; }
case "$1" in
1) for d in base cand; do echo "$d: $(grep -c -F "$A" $d/$P1) $(flat $d/$P2 | grep -c -F "$C")"; done ;;
2) for d in base cand; do echo "$d: $(grep -c -F "$N" $d/$P1) $(grep '^| \*\*Retention archive-directory lock' $d/$P1 | grep -o 'imports nothing from' | wc -l)"; done ;;
3) for d in base cand; do echo "$d: $(flat $d/$P2 | grep -o -F "$K" | wc -l) $(grep '^| Milestone acceptance' $d/$P2 | grep -o 'latest run' | wc -l)"; done ;;
4) for p in $P1 $P2; do echo "$p: $(diff base/$p cand/$p | grep -c '^<') $(diff base/$p cand/$p | grep -c '^>')"; done ;;
5) for p in $P1 $P2; do for d in base cand; do grep -m1 '^> For: ' $d/$p | sed 's/^.*Last checked with: //'; done; done ;;
6) cd "$REPO"; git diff --name-only $B -- docs ':!docs/ai-workflow' ':!docs/milestones' | sort
   git diff --exit-code --quiet $B -- payload tools fixtures templates manifest.json docs/release-history.md docs/RELEASING.md .claude scripts .workflow-manager .github CLAUDE.md .gitignore; echo "release source and installation: exit $?"
   git diff --exit-code --quiet $B -- docs/ai-workflow/DOCS_RESTAMP_PLAN.md docs/milestones/completed/DOCS_RESTAMP_PLAN.md; echo "archived plans: exit $?" ;;
7) for d in base cand; do echo "$d: $(grep '^| 4[23] \|^| 27 ' $d/docs/ROADMAP.md | awk -F'|' '{printf "%s", $2}')"; done
   diff <(grep '^| 42 ' base/docs/ROADMAP.md) <(grep '^| 42 ' cand/docs/ROADMAP.md) && echo row42-same
   grep '^| 43 ' cand/docs/ROADMAP.md | awk -F'|' '{print $5}' | cut -c1-20 ;;
8) f=$P1; s='Last checked with: Workflow 2.19.2.'
   echo "pinned $(grep -c -F "$s" "$REPO/tools/release/release_test.py") base $(grep -c -F "$s" base/$f) cand $(grep -c -F "$s" cand/$f)"
   sed 's/Last checked with: Workflow [0-9.]*\./Last checked with: Workflow 2.29.3./' cand/$f > mut.md; echo "mutated: $(grep -c -F "$s" mut.md)" ;;
9) n0=$(git -C "$REPO" status --short | wc -l); rm -rf full && mkdir full && git -C "$REPO" archive HEAD | tar -x -C full
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   sed -i '3s/ Last checked with: .*$//' full/$P2
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   echo "status lines: before $n0 after $(git -C "$REPO" status --short | wc -l)" ;;
10) cp cand/$P1 m1.md; cp cand/$P2 m2.md
   sed -i 's/ (`grep` finds no call)\./ (`grep` finds no call). Not verified for the order against the item'"'"'s own checkpoint claim, because the code never takes one/' m1.md
   sed -i 's/each check; where/each check: a check that ran again counts by its latest run; where/' m2.md
   echo "mutated: $(grep -c -F "$A" m1.md) $(flat m2.md | grep -c -F "$C")" ;;
esac
SH
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `sh "$TMPDIR/flows.sh" 1` | `base: 1 1`, `cand: 0 0`: the two contradicting passages are in the base and gone from the candidate |
| 2 | `sh "$TMPDIR/flows.sh" 2` | `base: 0 1`, `cand: 1 1`: the new sentence is present once, and the row says "imports nothing from" once (it said it once before, in the old sentence it replaces) |
| 3 | `sh "$TMPDIR/flows.sh" 3` | `base: 1 2`, `cand: 1 1`: the worst-run clause is kept once; "latest run" occurs twice in the acceptance row at the base and once in the candidate |
| 4 | `sh "$TMPDIR/flows.sh" 4` | `docs/CONCURRENCY_INVARIANTS.md: 1 1` and `docs/gates.md: 1 1`: one line removed and one added in each page, nothing else |
| 5 | `sh "$TMPDIR/flows.sh" 5` | four lines: `Workflow 2.19.2.` twice (concurrency page, base and candidate), then `Workflow 2.29.3, Workflow Manager 1.18.1.` twice (gates page): no stamp moved |
| 6 | `sh "$TMPDIR/flows.sh" 6` | the names `docs/ACTIVE_MILESTONE.md`, `docs/CONCURRENCY_INVARIANTS.md`, `docs/ROADMAP.md`, `docs/gates.md` and no other; then `release source and installation: exit 0` and `archived plans: exit 0` |
| 7 | `sh "$TMPDIR/flows.sh" 7` | `base:  42  27` and `cand:  42  43  27` (the row numbers in file order); then `row42-same`; then a status starting `Current` |
| 8 | `sh "$TMPDIR/flows.sh" 8` | `pinned 1 base 1 cand 1`, then `mutated: 0` (failure-only mutation: a copy whose stamp moved to 2.29.3 no longer satisfies the frozen test's string); nothing is written outside `$TMPDIR` |
| 9 | `sh "$TMPDIR/flows.sh" 9` | the first checker run prints nothing and `exit 0` (the candidate passes, offline); after the stamp is cut from the gates page the second run names `docs/gates.md` and `exit 1`; `status lines: before N after N` with the same N |
| 10 | `sh "$TMPDIR/flows.sh" 10` | `mutated: 1 1`: putting either old passage back into a copy of the candidate page is detected by flow 1's greps (failure-only mutation of flows 1 and 2; the real files are not touched) |
| 11 | **Full environment (the repository, `python3`; the nine suites).** After the checkpoint commit: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the suites loop of `docs/RELEASING.md` | the fixture stages with no adjusted records (no shipped file changed) and all nine suites pass |
| 12 | **Full environment (zlib-ng).** `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python -m unittest discover -s tools/release -p '*_test.py'`; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | all pass |
| 13 | **Full environment (scope).** `git diff 8e1212b7aa388e168a01588eb9ba0cf8348ba969 --stat` | the two pages, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`, the plan, the item's registry, mapping and artifacts files and `docs/ai-workflow/WORKFLOW_STATE.json`, no other path; nothing under `payload/`, `tools/`, `fixtures/`, `templates/`, `.claude/`, `scripts/`, `.workflow-manager/` or `.github/` |
