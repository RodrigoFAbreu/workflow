# W49: re-stamp the user pages against Workflow 2.29.3 (Revision 3)

- **Work item:** `docs-restamp` (`process`, governing version `2.2`; docs-only: no release)
- **Requested by:** the Manager Super Orchestrator, owner queue: RodrigoFAbreu/workflow#147 (its stamps part and the 2026-11-12 sweep comment on the roadmap's open-defects table); `docs/ROADMAP.md` row 42 (`Current` with this plan, `Done` at acceptance).
- **Branch:** `milestone/docs-restamp`
- **Base commit:** `144267cc2826e606e94aeaa47c741a0e7144b889` (main after #177: release source 2.29.3, this repository's installation 2.29.3; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 3 (round 1 of the local review: the release boundary, `LPR` I1, and the lock-site names, O1; round 2, the manual external review: the roadmap completion edit against the approval boundary, I1). The one checkpoint carries its `<!-- CP1 -->`/`<!-- /CP1 -->` pair. Out of scope: new checker rules (issue option b: a rule in `tools/docs/check_docs.py` is a later item of its own; it triggers CI but does not by itself publish a release), any `payload/`, `tools/` or behaviour change, the Manager repository.

## 0. Phase 1: the investigation

**What the checker requires of a stamp.** `tools/docs/check_docs.py` (`HEADER_RE`) requires the first non-blank line after the H1 of `README.md` and every `docs/*.md` except the three in `EXCLUDED` (`docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`, `docs/RELEASING.md`) to match `> For: <reader>. Last checked with: <versions>.`. It does **not** compare the versions with anything: the stamp is a claim only a re-check makes true, which is what this item does. No test pins a stamp (`check_docs_test.py` uses its own synthetic header). `docs/ROADMAP.md` is stamped but excluded from the checker; `docs/RELEASING.md` has no stamp.

**Release context.** `manifest.json` says 2.29.3 and every tag up to `v2.29.3` has its row in `docs/release-history.md`. The Manager's latest release is v1.18.1 (read with `gh release list -R RodrigoFAbreu/workflow-manager`; its README is stamped `Workflow Manager 1.18.1, Workflow 2.29.3`). `tools/release/manager-pin.json` (1.13.0) is the pin CI installs, not the version the pages are checked against.

**Method.** For each page: the payload files and sibling pages it states facts about, `git diff v<stamp> HEAD` over them, and the claims read against the result. `git diff v2.17.0 HEAD` of `payload/docs/ai-workflow/GATE_POLICY.md`, `ORCHESTRATION_PROTOCOL.md`, `MILESTONE_WORKFLOW.md`, the templates and the Manager's README was read in full; `PROTOCOL_VERSION` is still `1.5`; the lifecycle states did not change (the `MILESTONE_WORKFLOW.md` diff is the word "Claude" becoming "the agent" and one message note). **RE-CHECKED** = read and stamped; **KEPT** = not touched.

| Page (stamp at base) | Class | Evidence and decision |
| --- | --- | --- |
| `README.md` (2.8.0, Manager 1.4.0) | RE-CHECKED, one fix | Quick start (`workflow-manager bootstrap`, `verify`, `/milestone-plan`, the base-commit step) matches the Manager's README and the command set. Stale: "How the pieces fit" says the Manager installs from "digest-pinned releases"; the Manager's own README, the source of that paragraph, now says "digest-pinned up to 2.12.0 and checked by their own checksums after that". Copy that sentence. Stamp to Workflow 2.29.3, Manager 1.18.1. |
| `docs/README.md` (2.17.0) | RE-CHECKED, no fix | Every row and link resolves (the checker proves links; the file list of `docs/` has a row for each user page and for `RELEASING.md`, `CONCURRENCY_INVARIANTS.md`, `RETENTION.md`); the shipped documents it lists still exist. Stamp 2.29.3 (its header names no Manager). |
| `docs/overview.md` (2.9.0, 1.5.0) | RE-CHECKED, no fix | The flowchart and the 11 steps against `MILESTONE_WORKFLOW.md` and the gate defaults of `GATE_POLICY.md`: unchanged since 2.9.0; every command it names exists (checker). Stamp 2.29.3, Manager 1.18.1. |
| `docs/install.md` (2.17.0, 1.5.0) | RE-CHECKED, no fix | `bootstrap`, `update`, `verify` and the three Manager pages it links exist and the Manager's README still lists them (it adds `doctor`; the page does not claim to be complete); the `default_workflow_version` and 2.10 refusal statements against `templates/` and `payload/` (templates unchanged but the conformance workflow). Stamp 2.29.3, Manager 1.18.1. |
| `docs/gates.md` (2.17.0, 1.5.0) | RE-CHECKED, one addition | The gate table and evidence list against `GATE_POLICY.md`: unchanged except 2.25.3/2.25.4, which made the check state judge the latest run of each check (`GATE_POLICY.md`); the page says only "its checks are not failing". Add one sentence taken from that document. Stamp 2.29.3, Manager 1.18.1. |
| `docs/glossary.md` (2.17.0, 1.4.0) | RE-CHECKED, no fix | Protocol 1.5 and the `review_round` fields against `workflow_protocol.py` (`PROTOCOL_VERSION = "1.5"`) and `ORCHESTRATION_PROTOCOL.md`; the gate, review, declaration and backlog terms against the commands. Stamp 2.29.3, Manager 1.18.1. |
| `docs/CONCURRENCY_INVARIANTS.md` (2.19.2) | RE-CHECKED, one row | All 30 `file:function` and `file::Class` references resolve in `payload/scripts/` (script of flow 7). Stale against its own maintenance rule ("a new `flock` or `os.link` call site"): `workflow_retention.py` (2.21.0 to 2.24.0) takes a non-blocking `flock` on the archive directory in `archive`, `remove` and `prune --apply` (refusal `archive_busy`, never blocked) and publishes the archive with `os.link`; the page has no row for it. Add one row, from the three call sites (`_apply`'s lock and link, `_flow`'s lock, `prune_archives`'s lock) and `docs/RETENTION.md`'s own text, with `not verified` in any cell the code does not settle. The engine takes no state lock (`grep` finds none). Stamp 2.29.3. |
| `docs/RETENTION.md` (2.25.6) | RE-CHECKED, no fix | `git diff v2.25.6 HEAD` over `workflow_retention.py`, `archive-finished-item.md` and `prune-archives.md` is empty; all 20 references resolve (flow 7); the later releases (2.26.0 to 2.29.3) changed only the acceptance commands, which the page does not describe. Stamp 2.29.3. |
| `docs/ROADMAP.md` (2.18.5) | RE-CHECKED, four fixes | (a) the "Open defects" rows for #50 and #55: both issues are CLOSED and their rows (22, 24b, 24c) are Done (the issue's sweep comment, re-read with `gh issue view`); drop both rows. (b) Row 24's status "Paused again" is stale: it was replaced by 24b and 24c, both Done. (c) Row 27a's status begins "Next: right after the current clean-up items" although every retention row after it is Done; say Done. (d) Add row 42. Rows 12, 13, 26c and 27 stay (Waiting, Later). #30 part 2 and #85 stay OPEN, so their text stays. Stamp 2.29.3. |
| `docs/exit-codes.md`, `docs/common-problems.md`, `docs/release-history.md` (2.29.3) | KEPT | Edited and stamped by the 2.29.3 release item itself (`git log -1`: #174); nothing in the payload changed since, and every tag has its history row. Not re-read again, so not touched: `git diff --exit-code` proves it (flow 3). |
| `docs/RELEASING.md`, `docs/ACTIVE_MILESTONE.md` | not stamped / owned by the commands | `RELEASING.md` has no stamp; `ACTIVE_MILESTONE.md` is rewritten by the workflow commands, not this item. |

**Release or not.** `docs/RELEASING.md` ("changes outside the release source (`tools/`, `.github/`, `docs/`) are always ..." and the `changes` job): the release source is only `manifest.json`, `payload/`, `fixtures/` and `templates/` (`tools/release/package.py:45`, `RELEASE_SOURCE_PATHS`); `tools/release/`, the CI workflow and `.gitattributes` only trigger the CI `changes` job (`release.py` `CANDIDATE_CI_PATHS`, `CANDIDATE_ARCHIVE_PATHS`), they do not require a release. `README.md` and `docs/` are outside both. This item touches none of those, so it is a `docs:` pull request with impact `none`, the manifest keeps 2.29.3 and **no release is needed**. The orchestrator is not asked to stop.

## 1. Goal and scope

Every stamped page says the release it was really re-checked against. Nine pages move (README.md, docs/README.md, overview, install, gates, glossary, the concurrency page, the retention page, the roadmap); three are kept. Four facts are fixed (README sentence, gates sentence, the concurrency row, the roadmap rows). Nothing in `payload/` or `tools/` changes.

## 2. Design decisions

- **D-Stamp (one principle: a stamp is a claim of a re-check).** A page's stamp moves only with the table's RE-CHECKED row done in CP1; the Manager version is written only where the header named it, and is `1.18.1`, the release read from the forge when CP1 starts (CP1 re-reads it and writes what it finds, not a remembered value).
- **D-Fix.** Only what the table lists is changed, in the smallest true wording: the README sentence is the Manager's own; the gates sentence is `GATE_POLICY.md`'s ("a check that ran again counts by its latest run; where the order of runs cannot be established its worst run counts"); the concurrency row is built from the code and says `not verified` where the code does not settle a cell.
- **D-Roadmap.** Row 42 is the next free row after 41, in the style of row 41, status `Current` at plan time and `Done (accepted by policy)` at acceptance; the two open-defects rows are dropped (the sentence above the table already says all other defects are fixed).
- **D-Declaration.** The generated declaration protects, at the implementation stage, `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json`, `docs/release-history.md`, the three kept pages, `docs/RELEASING.md` and the nine pages; at the plan stage the same paths are excluded (the plan protects only its own three files). `README.md` moves out of the implementation-stage exclusions; **`docs/ROADMAP.md` does not: it stays an implementation-stage exclusion** (D-Roadmap-Boundary).
- **D-Roadmap-Boundary (resolves the manual review's I1).** Row 42 is `Current` while the item is implemented and reviewed, and `/accept-milestone` step 3 flips it to `Done (accepted by policy)` in the completion commit, after the technical approval. If the roadmap were an implementation-stage protected path, that required write would change the approved fingerprint (`compute_review_content_id_implementation_stage` hashes every protected changed path with no completion exception), `approval_is_current` would turn false and a fresh fact for the open pull request would classify `content_changed`. So `docs/ROADMAP.md` is classified **excluded** at the implementation stage, as in every earlier item (`docs/ai-workflow/registry/wording-pass-plain-commands-artifacts.json` and `acceptance-phase-guard-artifacts.json` list it under `excluded_paths`, with the machinery-bookkeeping reason). The cost is that the row's bytes are not covered by the approval hash; they are covered instead by the functional-review flows 6 and 14 and by the status the acceptance command writes. The other eight pages stay protected: nothing in the workflow rewrites them after approval. The generated declaration `docs-restamp-artifacts.json` is changed accordingly (`docs/ROADMAP.md` moved from `implementation_stage.protected_paths` to `excluded_paths`) and `D-Declaration` above states it.
- **D-Verify.** No payload file changes, so the staged fixture of HEAD is the release source of 2.29.3 unchanged: the nine suites run from `stage-conformance --commit HEAD` with no adjusted records; they prove the item changed no shipped byte. The new content has no failure path of its own (no code): the one failure-only proof is the checker rejecting a page whose stamp is removed, on a scratch copy.

## 3. Open decisions

No `docs/TECHNICAL_DECISIONS.md`, so no Open decision row is touched. Reversible: **the Manager stamp 1.18.1 against 1.13.0** (the pin is not what the pages are checked against); **the concurrency row** (if the code leaves a cell unsettled it says `not verified`; the row can be dropped without touching the rest); **option b** (a checker rule comparing stamps with the manifest) is a later item, not this one (a change to `tools/docs/check_docs.py` is outside the release source, so it would not need a release either).

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Re-check the stamped pages, fix what is stale, move only the stamps of the pages re-checked, add row 42 | - | 2 | 1 |

<!-- CP1 -->
### CP1 — Re-check the stamped pages, fix what is stale, move only the stamps of the pages re-checked, add row 42

**Files:** `README.md`, `docs/README.md`, `docs/overview.md`, `docs/install.md`, `docs/gates.md`, `docs/glossary.md`, `docs/CONCURRENCY_INVARIANTS.md`, `docs/RETENTION.md`, `docs/ROADMAP.md`.

- **Read first, edit after.** For each RE-CHECKED row of section 0, re-read the page against the files the row names; if a claim is stale in a way the table did not list, fix it with a fact the code or a sibling page states (or say `not verified`), and say so in the report. A page whose re-check cannot be finished keeps its stamp and the report says why.
- **The edits:** README's "How the pieces fit" sentence; one sentence in `docs/gates.md`'s evidence section; one row in `docs/CONCURRENCY_INVARIANTS.md`'s table (and the page's own text only if the row makes a sentence false); the roadmap's open-defects rows, rows 24 and 27a, and row 42; then the nine "Last checked with" lines (Workflow 2.29.3; Workflow Manager 1.18.1 on `README.md`, overview, install, gates and glossary).
- **No other change:** `git diff --exit-code 144267cc2826e606e94aeaa47c741a0e7144b889 -- docs/exit-codes.md docs/common-problems.md docs/release-history.md docs/RELEASING.md payload tools fixtures templates manifest.json` exits 0.

**Verification:** `tools/docs` tests and `check_docs.py`; the nine suites from `stage-conformance --commit HEAD`; `tools/release` tests with the zlib-ng interpreter; `check-manager-block` with `--manager-releases`; the offline flows below; flow 14 (the completion edit leaves the approval fingerprint unchanged).
<!-- /CP1 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Flows 1 to 10 run offline: no network, no real `gh`, no install, no socket, no zlib-ng, no Python 3.12; nothing writes in the real repository.** No flow needs the forge, so there is no fake `gh`. Setup, once, from the repository root, with `TMPDIR=/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w49-tmp`:

```sh
export REPO="$PWD" B=144267cc2826e606e94aeaa47c741a0e7144b889
export PAGES="README.md docs/README.md docs/overview.md docs/install.md docs/gates.md docs/glossary.md docs/CONCURRENCY_INVARIANTS.md docs/RETENTION.md docs/ROADMAP.md"
export KEPT="docs/exit-codes.md docs/common-problems.md docs/release-history.md"
rm -rf "$TMPDIR/base" "$TMPDIR/cand" && mkdir -p "$TMPDIR/base" "$TMPDIR/cand"
git -C "$REPO" archive "$B" README.md docs/*.md | tar -x -C "$TMPDIR/base"          # the base commit's pages
git -C "$REPO" archive HEAD README.md docs/*.md | tar -x -C "$TMPDIR/cand"          # the candidate's pages
cat > "$TMPDIR/refs.py" <<'PY'
import re, sys
bad = []
for page in sys.argv[2:]:
    t = open(page).read()
    for m in re.finditer(r"(workflow_[a-z_]+\.py):([A-Za-z_]\w*)", t):
        s = open(sys.argv[1] + "/" + m.group(1)).read()
        if not re.search(r"^\s*def %s\b|^class %s\b|^%s\b" % ((m.group(2),) * 3), s, re.M): bad.append(m.group(0))
    for m in re.finditer(r"(workflow_[a-z_]+\.py)::(\w+)", t):
        if not re.search(r"^class %s\b" % m.group(2), open(sys.argv[1] + "/" + m.group(1)).read(), re.M): bad.append(m.group(0))
print("unresolved:", sorted(set(bad)))
PY
cat > "$TMPDIR/flows.sh" <<'SH'
# usage: flows.sh <n>; reads REPO, B, PAGES, KEPT, TMPDIR from the environment
cd "$TMPDIR"
case "$1" in
1) for d in base cand; do echo "== $d"; (cd $d && grep -m1 '^> For: ' $PAGES | sed 's/^> For: .*Last checked with: //'); done ;;
2) (cd cand && grep -m1 '^> For: ' $PAGES $KEPT | grep -vc 'Workflow 2.29.3'); python3 -I -c "import json,os; print(json.load(open(os.environ['REPO']+'/manifest.json'))['workflow_version'])" ;;
3) cd "$REPO"; git diff --exit-code $B -- $KEPT docs/RELEASING.md; echo "exit $?" ;;
4) cd "$REPO"; git diff --exit-code $B -- payload tools fixtures templates manifest.json .claude scripts .workflow-manager .github CLAUDE.md .gitignore; echo "exit $?"; git diff --name-only $B -- docs | sort ;;
5) for d in base cand; do echo "== $d"; grep -c 'digest-pinned up to 2.12.0' $d/README.md; tr '\n' ' ' < $d/docs/gates.md | grep -c 'latest run of each check'; grep -c 'archive_busy' $d/docs/CONCURRENCY_INVARIANTS.md; done ;;
6) for d in base cand; do echo "== $d"; grep -c '^. RodrigoFAbreu/workflow#[5][05] ' $d/docs/ROADMAP.md; grep -c 'Paused again' $d/docs/ROADMAP.md; grep '^. 27a ' $d/docs/ROADMAP.md | grep -c 'Next: right after'; grep -c '^. 42 ' $d/docs/ROADMAP.md; done
   diff <(grep '^. 41 ' base/docs/ROADMAP.md) <(grep '^. 41 ' cand/docs/ROADMAP.md) && echo row41-same
   grep '^. 42 ' cand/docs/ROADMAP.md | awk -F'|' '{print $2 "/" $(NF-1)}' | cut -c1-60 ;;
7) python3 -I refs.py "$REPO/payload/scripts" cand/docs/CONCURRENCY_INVARIANTS.md cand/docs/RETENTION.md ;;
8) (cd cand && grep -nE '\b[MW][0-9]+[a-z]?\b|\bCP[0-9]+\b|docs-restamp' README.md docs/README.md docs/overview.md docs/install.md docs/gates.md docs/glossary.md docs/exit-codes.md docs/common-problems.md docs/release-history.md docs/CONCURRENCY_INVARIANTS.md docs/RETENTION.md); echo "exit $?" ;;
9) n0=$(git -C "$REPO" status --short | wc -l); rm -rf full && mkdir full && git -C "$REPO" archive HEAD | tar -x -C full
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   sed -i '3s/ Last checked with: .*$//' full/docs/gates.md
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   echo "status lines: before $n0 after $(git -C "$REPO" status --short | wc -l)" ;;
10) rm -rf s && git init -q -b main s && cd s
   for p in $PAGES; do mkdir -p "$(dirname "$p")"; cp "$TMPDIR/base/$p" "$p"; done
   git add -A && git -c user.email=t@t -c user.name=t commit -qm base
   for p in $PAGES; do cp "$TMPDIR/cand/$p" "$p"; done
   git diff --stat | tail -1; git diff --exit-code --quiet -- $KEPT; echo "kept diff exit $?" ;;
esac
SH
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `sh "$TMPDIR/flows.sh" 1` | base: the old stamps (2.8.0, 2.9.0, 2.17.0 on four pages, 2.19.2, 2.25.6, 2.18.5); candidate: nine lines, every one starting `Workflow 2.29.3`; the lines of `README.md`, `docs/overview.md`, `docs/install.md`, `docs/gates.md` and `docs/glossary.md` end `, Workflow Manager 1.18.1.`, the other four end `Workflow 2.29.3.` |
| 2 | `sh "$TMPDIR/flows.sh" 2` | `0` (none of the twelve stamped pages lacks 2.29.3), then `2.29.3` (the manifest's version, the stamp's value) |
| 3 | `sh "$TMPDIR/flows.sh" 3` | no diff output and `exit 0`: the three kept pages and `docs/RELEASING.md` are byte-identical to the base |
| 4 | `sh "$TMPDIR/flows.sh" 4` | `exit 0` (release source and this repository's installation untouched: docs-only, releases nothing), then the changed `docs/` names: the nine pages, `docs/ACTIVE_MILESTONE.md`, `docs/ai-workflow/DOCS_RESTAMP_PLAN.md`, `docs/ai-workflow/WORKFLOW_STATE.json` and the item's registry, mapping and artifacts files, nothing else (run on the milestone branch after the checkpoint commit) |
| 5 | `sh "$TMPDIR/flows.sh" 5` | base: `0`, `0`, `0`; candidate: `1`, `1`, at least `1`: each listed fix is absent from the base and present on the candidate |
| 6 | `sh "$TMPDIR/flows.sh" 6` | base: `2`, `1`, `1`, `0` (the two defect rows, the paused status, the stale `Next:`, no row 42); candidate: `0`, `0`, `0`, `1`; then `row41-same`; then `42/` and a status starting `Current` |
| 7 | `sh "$TMPDIR/flows.sh" 7` | `unresolved: []`: every function and test the two maintainer pages name (the new row's too) exists in `payload/scripts/` |
| 8 | `sh "$TMPDIR/flows.sh" 8` | no match line and `exit 1`: no user page names a milestone id, a checkpoint id or this item's id (`docs/ROADMAP.md`, `docs/RELEASING.md` and `docs/ACTIVE_MILESTONE.md` are outside the checker and this grep) |
| 9 | `sh "$TMPDIR/flows.sh" 9` | the first checker run prints nothing and `exit 0` (the candidate passes, offline); after the stamp is cut from `docs/gates.md` the second run prints a line naming `docs/gates.md` and the header rule and `exit 1` (failure-only mutation: only the stamp-less page fails); `status lines: before N after N` with the same N (the scratch copy is the only thing written) |
| 10 | `sh "$TMPDIR/flows.sh" 10` | a scratch repository built by hand, the base commit against the candidate: the stat's last line says `9 files changed` and `kept diff exit 0` (the three kept pages are not part of it) |
| 11 | **Full environment (the repository, `python3`; the nine suites).** After the checkpoint commit: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the suites loop of `docs/RELEASING.md` | the fixture stages with no adjusted records (no shipped file changed) and all nine suites pass |
| 12 | **Full environment (zlib-ng).** `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python -m unittest discover -s tools/release -p '*_test.py'`; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | all pass |
| 13 | **Full environment (scope).** `git diff 144267cc2826e606e94aeaa47c741a0e7144b889 --stat` | the nine pages, `docs/ACTIVE_MILESTONE.md`, the plan, the item's registry, mapping and artifacts files and `docs/ai-workflow/WORKFLOW_STATE.json`, no other path; nothing under `.claude/`, `scripts/`, `.workflow-manager/` or `.github/` |
| 14 | **Full environment (approval boundary; scratch copy, nothing written in the real repository).** Resolves I1. In a scratch clone of the milestone branch after the checkpoint commit, compute `workflow_fingerprint.compute_review_content_id_implementation_stage` (arguments from the item's artifacts file) before and after rewriting row 42's status cell from `Current` to `Done (accepted by policy; the release follows the merge)` and committing it; also call `classify_path_implementation_stage("docs/ROADMAP.md", ...)` and `...("docs/gates.md", ...)` with the artifacts file's implementation-stage sets | `docs/ROADMAP.md` classifies `excluded` and `docs/gates.md` `protected`; the two `review_content_id` values are **equal**, so `approval_is_current` stays true across the completion commit and the pull-request fact is not `content_changed` for that edit alone; as a failure-only control, editing a protected page (`docs/gates.md`) in the same scratch clone changes the id |
