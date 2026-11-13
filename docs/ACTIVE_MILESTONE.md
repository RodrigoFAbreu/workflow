# Active Milestone

## Milestone

**Awaiting functional review** (`AWAITING_FUNCTIONAL_REVIEW`). W49: `docs-restamp` (`process`, governing version `2.2`), branch `milestone/docs-restamp`,
roadmap row 42 (RodrigoFAbreu/workflow#147, the stamps part). The plan is `docs/ai-workflow/DOCS_RESTAMP_PLAN.md`
(revision 4, the owner's amendment, approved by gate policy). The implementation review (`LOCAL_MODEL_IMPLEMENTATION_REVIEW`,
round 1) approved, and the technical approval is `CURRENT` by policy for the reviewed commit `4b74297`.

## Goal

Every user page with a `Last checked with` line says the release it was really re-checked against. Docs only: no
`payload/`, `tools/` or behaviour change, so no release (a `docs:` pull request, impact none; the manifest keeps 2.29.3).

## Outcome

- CP1 is complete: nine pages re-read and re-stamped to Workflow 2.29.3 (Workflow Manager 1.18.1 on `README.md`, overview,
  install, gates and glossary; 1.18.1 is the latest release read with `gh release list`). Fixed: the README's wording of how
  the Manager installs, one sentence in `docs/gates.md` on the latest run of each check, a row for the retention engine's
  archive-directory lock in `docs/CONCURRENCY_INVARIANTS.md` (cells the code does not settle say `not verified`), and the
  roadmap (open-defects rows for #50 and #55 dropped, row 24 and row 27a statuses, row 42 added as `Current`).
- Checked in CP1: `tools/docs` tests and `check_docs.py` pass; the kept pages, `docs/RELEASING.md` and the release source
  have no diff against the base commit; every `file:function` reference on the two maintainer pages resolves.
- Self-review: the concurrency row's test cell said the `prune --apply` refusal was not verified, but
  `workflow_state_completion_obligations_test.py::RetentionPrune` (`test_p3b_the_lock_and_the_re_read_under_it`) holds the
  lock and expects `archive_busy`; the cell now names it.
- Revalidated after the amendment (revision 4): CP1's content is unchanged and still holds (`tools/docs` tests and
  `check_docs.py` pass; offline flows 2 to 7, 9 and 10 behave as expected for the pre-CP2 state). Two stamps (the retention
  and concurrency pages) are pinned by frozen release tests, so CP2 restores them to their base text; the concurrency row stays.
- CP2 is complete: the stamps of `docs/RETENTION.md` (2.25.6) and `docs/CONCURRENCY_INVARIANTS.md` (2.19.2) are back to their
  base text (frozen release tests pin them); `docs/RETENTION.md` has no diff against the base commit and the concurrency
  page's diff is exactly the added row. Final state: seven moved stamps. Checked: `tools/docs` tests, `check_docs.py`,
  `check-manager-block`, and the whole `tools/release` suite (328 tests, Python 3.12 with the pinned zlib-ng wheel) pass.
- Self-review after CP2: row 42 of the roadmap still described CP1 as first done (one checkpoint, and the retention and
  concurrency pages among the stamps moved to 2.29.3). It now says two checkpoints, seven moved stamps, and that those two
  pages were re-checked but keep 2.19.2 and 2.25.6 because frozen release tests pin them.
- Self-review, flow 5: the gates sentence followed D-Fix's wording but did not contain the phrase flow 5 checks for
  (`latest run of each check`, `GATE_POLICY.md`'s own words), so flow 5 printed `0` where the plan expects `1`. The sentence
  keeps D-Fix's wording and is now introduced with `GATE_POLICY.md`'s phrase.
- Verification at `796f05e` (the rerun before this checklist, since the self-review commits came after the CP2 run):
  `tools/docs` tests (34 pass), `check_docs.py` (exit 0), `check-manager-block` (ok), the `tools/release` suite (328 tests
  pass, Python 3.12.14, pinned zlib-ng 1.0.0), `workflow-manager verify .` (installation matches workflow 2.29.3), and the
  nine conformance suites from `stage-conformance --commit HEAD` (a staged fixture, run from inside it): all nine exit 0.

## Next action

Manual functional review of `docs-restamp`, against the checklist below at the checklist evidence commit. Findings, if any,
go to `.ai-review/docs-restamp/feedback/FUNCTIONAL_REVIEW.md`. If testing is clean, `/accept-milestone docs-restamp` is the
only acceptance command (every checkpoint, CP1 and CP2, is `COMPLETE`). A finding that is a same-scope fix goes through
`/apply-functional-review`'s bounded branch; a new or wider one goes through its broad branch (`docs-restamp-remediation-<n>`).

## Functional review checklist

**Scope.** Docs only. Changed: the eight stamped pages (`README.md`, `docs/README.md`, `docs/overview.md`,
`docs/install.md`, `docs/gates.md`, `docs/glossary.md`, `docs/CONCURRENCY_INVARIANTS.md`, `docs/ROADMAP.md`), this file,
the plan and the item's own files. Unchanged: `docs/RETENTION.md` (byte-identical to the base), `payload/`, `tools/`,
`templates/`, `fixtures/`, `manifest.json`, and the three kept pages. No release: the manifest stays `2.29.3`.

**Setup (once).** Nothing is built or installed.

- From the repository root, on `milestone/docs-restamp`, with a clean tree. Use **bash** for the driver below: it relies on
  word splitting, which zsh does not do for an unquoted variable.
- Tools: `git` and the system `python3`. Flows 12 and 13 also need the pinned zlib-ng Python 3.12 (see flow 13).
- A scratch directory outside the clone: `export REPO="$PWD" B=144267cc2826e606e94aeaa47c741a0e7144b889 TMPDIR="$(mktemp -d)"`.
  Write the driver (the `<details>` block below) to `"$TMPDIR/flows.sh"`, then run `bash "$TMPDIR/flows.sh" <n>` for flow `<n>`.
- No flow needs the forge: no `gh`, no network, no `claude`, `codex` or `ssh`, no socket.

**Test data.** None. The data is the git history: the base commit `144267c` (the old stamps) and `HEAD` (the new ones).

**Flows.** Each row is a command and its expected result. Flows 1 to 11 and 14 to 15 are offline (flow 15 runs in its own
scratch clone). Flow M1 is the only one a person must judge.

| Flow | Run | Expect |
| --- | --- | --- |
| 1 | `bash "$TMPDIR/flows.sh" 1` | `base`: 2.8.0 (Manager 1.4.0), 2.17.0, 2.9.0 (1.5.0), 2.17.0 (1.5.0), 2.17.0 (1.5.0), 2.17.0 (1.4.0), 2.19.2, 2.25.6, 2.18.5. `cand`: `Workflow 2.29.3, Workflow Manager 1.18.1.` for README, overview, install, gates and glossary; `Workflow 2.29.3.` for `docs/README.md` and the roadmap; `Workflow 2.19.2.` and `Workflow 2.25.6.` unchanged for the concurrency and retention pages |
| 2 | `bash "$TMPDIR/flows.sh" 2` | exactly `docs/CONCURRENCY_INVARIANTS.md` and `docs/RETENTION.md` (the frozen stamps), then `2.29.3` |
| 3 | `bash "$TMPDIR/flows.sh" 3` | `exit 0` (kept pages and `docs/RELEASING.md`, `docs/RETENTION.md` unchanged), then `1` (one added row in the concurrency page) and `0` (no stamp line in that diff) |
| 4 | `bash "$TMPDIR/flows.sh" 4` | `exit 0` (no change under `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json`, `.claude/`, `scripts/`, `.workflow-manager/`, `.github/`, `CLAUDE.md`, `.gitignore`), then the 13 changed `docs/` paths: the eight pages, `docs/ACTIVE_MILESTONE.md`, the plan, `docs/ai-workflow/WORKFLOW_STATE.json` and the item's registry, mapping and artifacts files; not `docs/RETENTION.md` |
| 5 | `bash "$TMPDIR/flows.sh" 5` | `base`: `0`, `0`, `0`. `cand`: `1`, `1`, `1` |
| 6 | `bash "$TMPDIR/flows.sh" 6` | `base`: `2`, `1`, `1`, `0`. `cand`: `0`, `0`, `0`, `1`; then `row41-same`; then the row 42 line, status `Current` |
| 7 | `bash "$TMPDIR/flows.sh" 7` | `unresolved: []` |
| 8 | `bash "$TMPDIR/flows.sh" 8` | no match line, then `exit 1` (no user page names a milestone, checkpoint or this item) |
| 9 | `bash "$TMPDIR/flows.sh" 9` | first checker run: nothing, `exit 0`. After the stamp is cut from a scratch copy of `docs/gates.md`: a line naming `docs/gates.md` and the header rule, `exit 1`. `status lines: before N after N` with the same N |
| 10 | `bash "$TMPDIR/flows.sh" 10` | `8 files changed, 13 insertions(+), 13 deletions(-)` and `kept diff exit 0` (a scratch repository, base against candidate) |
| 11 | `bash "$TMPDIR/flows.sh" 11` | for each frozen page: `1`, `1`, `1`, `mutated: 0` |
| 12 | Full environment: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the nine-suite loop from `docs/RELEASING.md` ("The nine payload suites"), run from inside the fixture | the fixture stages with no adjusted records; all nine suites exit 0. Not runnable in the offline sandbox if the suites need a tool it lacks |
| 13 | Full environment: `<pinned Python 3.12 with zlib-ng 1.0.0>` `-m unittest discover -s tools/release -p '*_test.py'`; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | `Ran 328 tests … OK`; `Ran 34 tests … OK`; `exit 0`; `ok: 2.29.3 carries a valid manager block`. The zlib-ng interpreter is outside this repository; the sandbox may not reach it |
| 14 | `git diff 144267cc2826e606e94aeaa47c741a0e7144b889 --name-only` | exactly 14 paths: `README.md` and the 13 `docs/` paths of flow 4 (nothing under `.claude/`, `scripts/`, `.workflow-manager/` or `.github/`) |
| 15 | the Python block below, run with `python3 -I -B` | `classify docs/ROADMAP.md: excluded`, `classify docs/gates.md: protected`, `id before == after (row 42 edit): True`, `control: protected page edit changes id: True` |
| M1 | read the prose, no script | the three changed sentences read true to a reader who knows the Workflow: the README's "How the pieces fit" line (the Manager's own wording), the `docs/gates.md` evidence sentence (`GATE_POLICY.md`'s phrase), and the concurrency row (`not verified` where the code does not settle a cell); row 42 of the roadmap says two checkpoints and seven moved stamps |

**Known limitations and out of scope.**

- A stamp is a claim that a re-check was done. The checker only checks that a stamp line exists and has the right form
  (flow 9); it does not compare the versions with anything. Flows 1 and 5 prove the claims were written, not that they are true.
- Two stamps are frozen: `docs/RETENTION.md` (2.25.6) and the concurrency page (2.19.2). The frozen release tests pin them
  (flow 11). The concurrency row was read against 2.29.3 code while the page keeps 2.19.2; the owner accepted that cost.
- `docs/ROADMAP.md` is an excluded path at the implementation stage (`D-Roadmap-Boundary`), so its bytes are not in the
  approval hash. Flow 15 shows that the completion edit to row 42 does not change the approval, and the roadmap is checked by flows 6 and M1.
- The Manager stamp is `1.18.1` (the latest release), not the `1.13.0` pin in `tools/release/manager-pin.json`.
- A checker rule that compares stamps with the manifest (issue option b) is a later item; it is not part of this one.
- No payload change, so no release and no fixture adjustment. Nothing here opens a pull request or touches a forge.

**Driver for the offline flows** (save as `"$TMPDIR/flows.sh"`; run with `bash`):

<details>
<summary>flows.sh</summary>

```bash
#!/bin/bash
# docs-restamp functional flows, offline. Usage: bash flows.sh <flow-number>
# Environment: REPO (the milestone clone, read-only for this script), B (base commit), TMPDIR (scratch).
set -u
: "${REPO:?}" "${B:?}" "${TMPDIR:?}"
PAGES="README.md docs/README.md docs/overview.md docs/install.md docs/gates.md docs/glossary.md docs/CONCURRENCY_INVARIANTS.md docs/RETENTION.md docs/ROADMAP.md"
KEPT="docs/exit-codes.md docs/common-problems.md docs/release-history.md"
export PAGES KEPT
# Scratch extraction of the pages (flows 1-3, 5-7 read these copies, never the clone).
if [ ! -d "$TMPDIR/base/docs" ]; then
  rm -rf "$TMPDIR/base" "$TMPDIR/cand"; mkdir -p "$TMPDIR/base" "$TMPDIR/cand"
  git -C "$REPO" archive "$B" README.md docs/ | tar -x -C "$TMPDIR/base"
  git -C "$REPO" archive HEAD README.md docs/ | tar -x -C "$TMPDIR/cand"
fi
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
cd "$TMPDIR" || exit 1
case "$1" in
1) for d in base cand; do echo "== $d"; (cd "$d" && grep -m1 '^> For: ' $PAGES | sed 's/^.*Last checked with: //'); done ;;
2) (cd cand && grep -m1 '^> For: ' $PAGES $KEPT | grep -v 'Workflow 2.29.3' | cut -d: -f1); python3 -I -c "import json,os; print(json.load(open(os.environ['REPO']+'/manifest.json'))['workflow_version'])" ;;
3) cd "$REPO" || exit 1; git diff --exit-code "$B" -- $KEPT docs/RELEASING.md docs/RETENTION.md; echo "exit $?"; git diff "$B" -- docs/CONCURRENCY_INVARIANTS.md | grep -c '^[-+] *[^-+ ]'; git diff "$B" -- docs/CONCURRENCY_INVARIANTS.md | grep -c 'Last checked' ;;
4) cd "$REPO" || exit 1; git diff --exit-code "$B" -- payload tools fixtures templates manifest.json .claude scripts .workflow-manager .github CLAUDE.md .gitignore; echo "exit $?"; git diff --name-only "$B" -- docs | sort ;;
5) for d in base cand; do echo "== $d"; grep -c 'digest-pinned up to 2.12.0' $d/README.md; tr '\n' ' ' < $d/docs/gates.md | grep -c 'latest run of each check'; grep -c 'archive_busy' $d/docs/CONCURRENCY_INVARIANTS.md; done ;;
6) for d in base cand; do echo "== $d"; grep -c -E '^\| (RodrigoFAbreu/workflow#50|RodrigoFAbreu/workflow#55) ' $d/docs/ROADMAP.md; grep -c 'Paused again' $d/docs/ROADMAP.md; grep '^| 27a ' $d/docs/ROADMAP.md | grep -c 'Next: right after'; grep -c '^| 42 ' $d/docs/ROADMAP.md; done
   diff <(grep '^| 41 ' base/docs/ROADMAP.md) <(grep '^| 41 ' cand/docs/ROADMAP.md) && echo row41-same
   grep '^| 42 ' cand/docs/ROADMAP.md | cut -c1-120 ;;
7) python3 -I "$TMPDIR/refs.py" "$REPO/payload/scripts" cand/docs/CONCURRENCY_INVARIANTS.md cand/docs/RETENTION.md ;;
8) (cd cand && grep -nE '\b[MW][0-9]+[a-z]?\b|\bCP[0-9]+\b|docs-restamp' README.md docs/README.md docs/overview.md docs/install.md docs/gates.md docs/glossary.md docs/exit-codes.md docs/common-problems.md docs/release-history.md docs/CONCURRENCY_INVARIANTS.md docs/RETENTION.md); echo "exit $?" ;;
9) rm -rf full && mkdir full && git -C "$REPO" archive HEAD | tar -x -C full
   n0=$(git -C "$REPO" status --short | wc -l)
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   sed -i '3s/ Last checked with: .*$//' full/docs/gates.md
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   echo "status lines: before $n0 after $(git -C "$REPO" status --short | wc -l)" ;;
10) rm -rf s && git init -q -b main s && cd s || exit 1
   for p in $PAGES; do mkdir -p "$(dirname "$p")"; cp "$TMPDIR/base/$p" "$p"; done
   git add -A && git -c user.email=t@t -c user.name=t commit -qm base
   for p in $PAGES; do cp "$TMPDIR/cand/$p" "$p"; done
   git diff --stat | tail -1; git diff --exit-code --quiet -- $KEPT; echo "kept diff exit $?" ;;
11) for pin in "docs/RETENTION.md|Last checked with: Workflow 2.25.6." "docs/CONCURRENCY_INVARIANTS.md|Last checked with: Workflow 2.19.2."; do f=${pin%%|*}; s=${pin#*|}
   grep -c -F "\"$s\"" "$REPO/tools/release/release_test.py"; for d in base cand; do grep -c -F "$s" "$d/$f"; done
   rm -rf mut && mkdir mut && sed 's/Last checked with: Workflow [0-9.]*\./Last checked with: Workflow 2.29.3./' "cand/$f" > mut/p.md; echo "mutated: $(grep -c -F "$s" mut/p.md)"; done ;;
*) echo "unknown flow $1"; exit 2 ;;
esac
```

</details>

Approval boundary (flow 15): Make a scratch clone first, then run the script on it. It edits only that clone:

```bash
git clone -q "$REPO" "$TMPDIR/f15-clone" && git -C "$TMPDIR/f15-clone" checkout -q milestone/docs-restamp
python3 -I -B "$TMPDIR/f15.py" "$TMPDIR/f15-clone" "$B"
```

Save the script below as `"$TMPDIR/f15.py"`:

<details>
<summary>f15.py</summary>

```python
import sys, json, subprocess, os
from pathlib import Path
# usage: python3 -I -B f15.py <scratch-clone-dir> <base-commit>; run after: git clone -q "$REPO" <scratch-clone-dir>
clone = Path(sys.argv[1]); base = sys.argv[2]
sys.path.insert(0, str(clone / 'scripts'))
import workflow_fingerprint as f
arts = json.load(open(clone / 'docs/ai-workflow/registry/docs-restamp-artifacts.json'))['implementation_stage']
args = dict(protected_paths=arts['protected_paths'], protected_prefixes=arts['protected_prefixes'],
            excluded_paths=arts['excluded_paths'], excluded_prefixes=arts['excluded_prefixes'])
def cid():
    return f.compute_review_content_id_implementation_stage(clone, base, 'process', 'docs-restamp', **args)[0]
print('classify docs/ROADMAP.md:', f.classify_path_implementation_stage('docs/ROADMAP.md', **args))
print('classify docs/gates.md:', f.classify_path_implementation_stage('docs/gates.md', **args))
before = cid()
rm = clone / 'docs/ROADMAP.md'
lines = rm.read_text().split('\n')
idx = [i for i, l in enumerate(lines) if l.startswith('| 42 ')][0]
cells = lines[idx].split('|')
pos = max(i for i, c in enumerate(cells) if c.strip() == 'Current')
cells[pos] = cells[pos].replace('Current', 'Done (accepted by policy; the release follows the merge)')
lines[idx] = '|'.join(cells)
rm.write_text('\n'.join(lines))
subprocess.run(['git', '-c', 'user.email=t@t', '-c', 'user.name=t', 'commit', '-qam', 'scratch: row 42 done'], cwd=clone, check=True)
after = cid()
print('id before == after (row 42 edit):', before == after, before[:16], after[:16])
g = clone / 'docs/gates.md'
g.write_text(g.read_text() + '\nscratch control\n')
print('control: protected page edit changes id:', cid() != after)
```

</details>

**Findings and next steps.** Findings go to `.ai-review/docs-restamp/feedback/FUNCTIONAL_REVIEW.md` (the path from
`workflow_fingerprint.py --resolve-feedback-path docs-restamp`). `/apply-functional-review` routes each one. When testing is
clean, `/accept-milestone` is the only acceptance command; there is no command that records acceptance of a partial round.
