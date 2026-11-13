# Active Milestone

## Milestone

**Awaiting functional review.** W50: `two-page-wording` (`process`, governing version `2.2`), branch `milestone/two-page-wording`, roadmap row 43
(RodrigoFAbreu/workflow#178, points 1 and 2). The plan is `docs/ai-workflow/TWO_PAGE_WORDING_PLAN.md` (revision 1, approved by
gate policy). Implementation revision 1 is approved by both implementation-review stages and by gate policy (technical approval).

## Goal

Two statements in two shipped pages read true and say each thing once: the retention row's lock-order cell in
`docs/CONCURRENCY_INVARIANTS.md` and the acceptance row of `docs/gates.md`. Docs only: no `payload/`, `tools/` or behaviour
change, so no release (a `docs:` pull request, impact none; the manifest keeps 2.29.3). No `Last checked with` stamp moves.

## Progress

- CP1 (reword the two cells, add roadmap row 43): complete (`a2d2030`).
- Self-review: the retention cell lacked the closing period of the plan's D-Retention sentence, so flow 10's mutation
  printed `0 1` where it expects `1 1`; the period is restored (`f16ca8c`).
- Implementation review, round 1: `LOCAL_MODEL_IMPLEMENTATION_REVIEW` (`anthropic/claude-opus-5-5`) and
  `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` (`openai/gpt-6.1-sol`), both APPROVE, on bundle `1a4473c46774`.
- Technical approval recorded by gate policy (`9837c85`).
- Automated verification: plan section 5's flows 1 to 13 ran on `f16ca8c` (`.ai-review/two-page-wording/current/TEST_RESULTS.md`);
  no content has changed since.

## Next action

Run the functional review checklist below. Findings go to `.ai-review/two-page-wording/feedback/FUNCTIONAL_REVIEW.md`.
Once testing is clean, `/accept-milestone` is the only acceptance command.

## Functional review checklist

The checklist is committed as the checklist-evidence commit that the preparing command reports (its SHA and blob are
in that report, not in this file, so the file does not have to name its own blob).

### Setup

- Use a clone at the checklist-evidence commit on branch `milestone/two-page-wording`. Flows 1 to 10 and 13 need no
  install, no network, no GitHub (`gh`), no `claude`/`codex`/`ssh`, and no zlib-ng interpreter. No flow needs a pull
  request or a forge, so no fake `gh` and no scratch origin are needed.
- Run from the repository root. Scratch files go under `$TMPDIR/w50-functional`, never inside the clone. Bytecode is
  off, so the suites do not write `__pycache__` into the clone.

```sh
export REPO="$PWD" B=8e1212b7aa388e168a01588eb9ba0cf8348ba969 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="${TMPDIR:-/tmp}/w50-functional"
mkdir -p "$TMPDIR" && rm -rf "$TMPDIR/base" "$TMPDIR/cand" "$TMPDIR/full" "$TMPDIR/fixture"
mkdir -p "$TMPDIR/base" "$TMPDIR/cand"
git -C "$REPO" archive "$B" docs/CONCURRENCY_INVARIANTS.md docs/gates.md docs/ROADMAP.md | tar -x -C "$TMPDIR/base"
git -C "$REPO" archive HEAD docs/CONCURRENCY_INVARIANTS.md docs/gates.md docs/ROADMAP.md | tar -x -C "$TMPDIR/cand"
```

Save this script as `$TMPDIR/flows.sh`. It is plan section 5's script, with two changes so it runs under plain `sh`:
flow 7 uses temp files instead of process substitution, and the `git status` call skips optional index locks.

```sh
# usage: sh "$TMPDIR/flows.sh" <n>; reads REPO, B, TMPDIR; the greps name the two pages only, never docs/ACTIVE_MILESTONE.md
cd "$TMPDIR" || exit 1
P1=docs/CONCURRENCY_INVARIANTS.md; P2=docs/gates.md
A='Not verified for the order'; C='a check that ran again'; K='where the order of runs cannot be established its worst run counts'
N='None of (1) to (9): the engine takes no state lock and no checkpoint claim, and imports nothing from `workflow_state.py`'
flat() { tr '\n' ' ' < "$1"; }
case "$1" in
1) for d in base cand; do echo "$d: $(grep -c -F "$A" $d/$P1) $(flat $d/$P2 | grep -c -F "$C")"; done ;;
2) for d in base cand; do echo "$d: $(grep -c -F "$N" $d/$P1) $(grep '^| \*\*Retention archive-directory lock' $d/$P1 | grep -o 'imports nothing from' | wc -l)"; done ;;
3) for d in base cand; do echo "$d: $(flat $d/$P2 | grep -o -F "$K" | wc -l) $(grep '^| Milestone acceptance' $d/$P2 | grep -o 'latest run' | wc -l)"; done ;;
4) for p in $P1 $P2; do echo "$p: $(diff base/$p cand/$p | grep -c '^<') $(diff base/$p cand/$p | grep -c '^>')"; done ;;
5) for p in $P1 $P2; do for d in base cand; do grep -m1 '^> For: ' $d/$p | sed 's/^.*Last checked with: //'; done; done ;;
6) cd "$REPO" && git diff --name-only $B -- docs ':!docs/ai-workflow' ':!docs/milestones' | sort
   git diff --exit-code --quiet $B -- payload tools fixtures templates manifest.json docs/release-history.md docs/RELEASING.md .claude scripts .workflow-manager .github CLAUDE.md .gitignore; echo "release source and installation: exit $?"
   git diff --exit-code --quiet $B -- docs/ai-workflow/DOCS_RESTAMP_PLAN.md docs/milestones/completed/DOCS_RESTAMP_PLAN.md; echo "archived plans: exit $?" ;;
7) grep '^| 42 ' "$TMPDIR/base/docs/ROADMAP.md" > r1; grep '^| 42 ' "$TMPDIR/cand/docs/ROADMAP.md" > r2
   for d in base cand; do echo "$d: $(grep '^| 4[23] \|^| 27 ' $d/docs/ROADMAP.md | awk -F'|' '{printf "%s", $2}')"; done
   diff r1 r2 && echo row42-same
   grep '^| 43 ' cand/docs/ROADMAP.md | awk -F'|' '{print $5}' | cut -c1-20 ;;
8) f=$P1; s='Last checked with: Workflow 2.19.2.'
   echo "pinned $(grep -c -F "$s" "$REPO/tools/release/release_test.py") base $(grep -c -F "$s" base/$f) cand $(grep -c -F "$s" cand/$f)"
   sed 's/Last checked with: Workflow [0-9.]*\./Last checked with: Workflow 2.29.3./' cand/$f > mut.md; echo "mutated: $(grep -c -F "$s" mut.md)" ;;
9) n0=$(git -C "$REPO" --no-optional-locks status --short | wc -l); rm -rf full && mkdir full && git -C "$REPO" archive HEAD | tar -x -C full
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   sed -i '3s/ Last checked with: .*$//' full/$P2
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   echo "status lines: before $n0 after $(git -C "$REPO" --no-optional-locks status --short | wc -l)" ;;
10) cp cand/$P1 m1.md; cp cand/$P2 m2.md
   sed -i 's/ (`grep` finds no call)\./ (`grep` finds no call). Not verified for the order against the item'"'"'s own checkpoint claim, because the code never takes one/' m1.md
   sed -i 's/each check; where/each check: a check that ran again counts by its latest run; where/' m2.md
   echo "mutated: $(grep -c -F "$A" m1.md) $(flat m2.md | grep -c -F "$C")" ;;
esac
```

### Flows

Flows 1 to 10 and 13 run in the sandbox. Flows 11 and 12 need the full environment (the nine suites, and the pinned
zlib-ng interpreter that the sandbox does not have), so they run on the user's machine only.

| Flow | Where it runs | Do | Expect |
| --- | --- | --- | --- |
| 1 | sandbox | `sh "$TMPDIR/flows.sh" 1` | `base: 1 1`, `cand: 0 0`: the two contradicting passages are in the base and gone from the candidate |
| 2 | sandbox | `sh "$TMPDIR/flows.sh" 2` | `base: 0 1`, `cand: 1 1`: the new sentence is present once, and the row says "imports nothing from" once |
| 3 | sandbox | `sh "$TMPDIR/flows.sh" 3` | `base: 1 2`, `cand: 1 1`: the worst-run clause is kept once; "latest run" occurs twice in the acceptance row at the base and once in the candidate |
| 4 | sandbox | `sh "$TMPDIR/flows.sh" 4` | `docs/CONCURRENCY_INVARIANTS.md: 1 1` and `docs/gates.md: 1 1`: one line removed and one added in each page, nothing else |
| 5 | sandbox | `sh "$TMPDIR/flows.sh" 5` | four lines: `Workflow 2.19.2.` twice (concurrency page, base and candidate), then `Workflow 2.29.3, Workflow Manager 1.18.1.` twice (gates page): no stamp moved |
| 6 | sandbox | `sh "$TMPDIR/flows.sh" 6` | the names `docs/ACTIVE_MILESTONE.md`, `docs/CONCURRENCY_INVARIANTS.md`, `docs/ROADMAP.md`, `docs/gates.md` and no other; then `release source and installation: exit 0` and `archived plans: exit 0` |
| 7 | sandbox | `sh "$TMPDIR/flows.sh" 7` | `base:  42  27` and `cand:  42  43  27`; then `row42-same`; then a status starting `Current` |
| 8 | sandbox | `sh "$TMPDIR/flows.sh" 8` | `pinned 1 base 1 cand 1`, then `mutated: 0` (the stamp mutation no longer satisfies the frozen test's string) |
| 9 | sandbox | `sh "$TMPDIR/flows.sh" 9` | the first checker run prints nothing and `exit 0`; after the stamp is cut from the gates page, the second run names `docs/gates.md` and `exit 1`; `status lines: before N after N` with the same N |
| 10 | sandbox | `sh "$TMPDIR/flows.sh" 10` | `mutated: 1 1`: putting either old passage back into a copy of the candidate page is detected by flow 1's greps (the real files are not touched) |
| 11 | user machine | `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the nine-suite loop of `docs/RELEASING.md` ("The nine payload suites"), run from inside the fixture | the fixture stages with no adjusted records (no shipped file changed) and all nine suites pass |
| 12 | user machine | with the pinned zlib-ng interpreter (the one in `docs/RELEASING.md`, "Building locally"): `python -m unittest discover -s tools/release -p '*_test.py'`; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | all pass |
| 13 | sandbox | `git diff 8e1212b7aa388e168a01588eb9ba0cf8348ba969 --stat` | the two pages, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`, the plan, the item's registry, mapping and artifacts files, and `docs/ai-workflow/WORKFLOW_STATE.json`; nothing under `payload/`, `tools/`, `fixtures/`, `templates/`, `.claude/`, `scripts/`, `.workflow-manager/` or `.github/` |
| 14 | user, by reading | Open the retention row's lock-order cell in `docs/CONCURRENCY_INVARIANTS.md` (`grep -n '^| \*\*Retention archive-directory lock' docs/CONCURRENCY_INVARIANTS.md`) and the Milestone acceptance row in `docs/gates.md` (`grep -n '^| Milestone acceptance' docs/gates.md`). Read the roadmap row 43 too. | The retention cell's one sentence reads: the engine takes no state lock and no checkpoint claim, and imports nothing from `workflow_state.py`; nothing else in the cell contradicts it. The acceptance row says "judged by the latest run of each check; where the order of runs cannot be established its worst run counts" once. Both read as true statements. Flows 1 to 13 check the wording character by character; this flow is the only check that the prose reads well. |

### Known limitations and out of scope

- Docs only. No behaviour, no `payload/`, `tools/` or release change, no stamp moves (the manifest keeps 2.29.3).
- The other four points of #178 are not in this item. Their archived plans are protected, so they are closed as "not
  editable" (flow 6 proves the archived plans are unchanged).
- `workflow-manager verify .` may print a notify-mode retention alert that is not part of this item (reported in
  `TEST_RESULTS.md`).
