# W53: three owner points settled with evidence: a recorded reaper run, the race-hook ordering and the posture sentence (Revision 2)

- **Work item:** `test-hardening-owner-points` (`process`, governing version `2.2`; docs-only: no release)
- **Requested by:** the Manager Super Orchestrator, owner instruction of 2026-11-15 (the three points that needed an owner decision are now worked): RodrigoFAbreu/workflow#170 point 1, #116 point 3 and #158 point 3; `docs/ROADMAP.md` row 46 (`Current` with this plan, `Done` at acceptance).
- **Branch:** `milestone/test-hardening-owner-points`
- **Base commit:** `f9d63f4246041afc21ff35d85bc2e994fc6d66f8` (main after #187: release source 2.29.5; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2 (revision 1 plus the local review round 1 findings LPR-R1-001 to -005, applied below). One checkpoint, with its anchor pair. Size: about 110 lines, under the 300-line split limit.

## 0. Phase 1: the investigation

Each point read with all issue comments, then run against main at the base commit. Scratch: `$TMPDIR` is `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w53-tmp`; the fixture is `stage-conformance --commit HEAD` (no record adjusted: nothing shipped is changed).

| Point | Class | Evidence |
|---|---|---|
| #170 point 1: no durable run of `TestPlainCommandMalformedState` under the Manager's orphan rule | KEEP the test, RECORD the run | Run from the fixture's `scripts/`: `python3 -I -S -B /home/rodrigo/Workspace/workflow-manager/tests/parallel/reaper.py --report R.json --chunk-id pcms -- python3 -B workflow_gate_policy_test.py TestPlainCommandMalformedState`: 10 tests OK, chunk status 0, 79 re-parented processes in the investigation run: 77 `[git]` and 2 `git maintenance run --auto --quiet --detach`, all fate `exited`, nothing else. The counts of git helpers vary from run to run (the local review run saw 78 and 1): what is pinned is the two kinds and the absence of a third, and CP1 records the counts of its own branch re-run. That is the accepted set of the earlier items (COMMAND_WORDING_EVIDENCE.md, "no orphan beyond Git's own detached maintenance"). The class's own children (`payload/scripts/workflow_gate_policy_test.py` lines 7365 to 7390) are `subprocess.run` calls, which wait, so it has no orphan source of its own to declare or remove: **no test change**. |
| #116 point 3: the A12 and A15 race hooks "should substitute after the earlier selection checks" (the issue calls it unverified) | ALREADY-FIXED | `payload/scripts/workflow_state_completion_obligations_test.py`: A12's `test_a12_a_file_replaced_by_a_symlink_after_the_walk_is_opened_with_no_follow` (line 5505) substitutes inside the wrapped `os.open` of `a.txt` (line 5514), after the walk, and asserts the observed `ELOOP` and that the sentinel was never read (lines 5540 to 5543); A15's `test_a15_the_substitutions_made_after_the_selection_are_refused_by_the_open_itself` (line 5757) substitutes inside the `O_RDWR` open of `index.jsonl` (line 5769), after the selection tests of line 5738 refused the same five variants. Reproduced by failure-only mutations of a fixture copy of `payload/scripts/workflow_retention.py` (mutation script in flows.sh): m1 drops `O_NOFOLLOW` from `_open_file` (line 691): the A12 test fails (`None != 40`); m2 drops it from `_open_index` (line 1012): the A15 test fails; m3 drops the `st_nlink != 1` test (line 1034): the A15 test fails. The five A15 variants share one fixture, so in the combined run of both tests a mutation that lets one variant archive `w00` makes every later variant fail `assertTrue(fired)` (`[] is not true`), because the hooked `O_RDWR` open of `index.jsonl` is never reached again. Exact combined-run results: m2 fails all five variants, the first being `symlink to an outside file` (`0 != 2`) and the other four (repository-file symlink, hard link, directory, FIFO) `[] is not true`; m3 fails the hard link (first failure), the directory and the FIFO with `[] is not true`. Run one variant alone, m2 fails exactly the two symlink variants and m3 exactly the hard link. Unmutated, both pass. The point was accepted and built in 2.21.0 (plan EPR-011). |
| #158 point 3: does the 2.27.0 posture keep "The release tooling and the maintainer documents are not part of the installed release." | KEEP, true | `git show v2.27.0:manifest.json` ends the posture with the sentence, and so do v2.25.6, v2.25.7, v2.26.0 and every release from v2.28.0 to v2.29.5 (checked one by one). It is true: `manifest.json` lists 83 artifacts, every `target_path` is under `.claude/commands/`, `docs/ai-workflow/` or `scripts/`, plus `CLAUDE.md`, `docs/ACTIVE_MILESTONE.md` and `scripts/prepare-ai-review.sh`; none is under `tools/` or is `docs/RELEASING.md`, `docs/ROADMAP.md` or `docs/release-history.md` (the maintainer pages). 2.27.0 is immutable and needs no correction, so **no posture change, no release**. |

**Release.** `docs/RELEASING.md`, lines 118 to 126: the release source is `manifest.json`, `payload/`, `fixtures/`, `templates/`, `tools/release/`, one CI file (`.github/workflows/workflow-ci.yml`) and the root `.gitattributes`; `docs/` is outside it and always allowed. A `test:` change in a payload script would release a patch only through the manifest records; none changes here. So this item releases nothing: a `docs:` pull request, impact none, the manifest keeps 2.29.5.

## 1. Goal and scope

Three points settled with evidence, one durable record. Out of scope: any `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` change, #170 point 2 (it needs a real change to the bundle files), the other points of the three issues, the Controller's contract (protocol stays 1.5), the Manager repository and the CI workflow files.

## 2. Design decisions

- **D-Evidence.** One file, `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md` (excluded at the plan stage, protected at the implementation stage, the precedent of `COMMAND_WORDING_EVIDENCE.md`): one section per point with its class, the commands and results of section 0 re-run on the branch, the three mutations with their exact old and new strings, and a last section holding the three issue comments word for word.
- **D-Comments.** After the evidence file is committed, one comment per issue is posted with `gh issue comment` from that last section (owner-authorized by this item's order): #170 the reaper result (point 1 settled; point 2 stays open); #116 point 3 is ALREADY-FIXED with the file:line evidence, and the point is dropped; #158 point 3 is KEEP with the manifest evidence, and points 1 to 3 are now all settled. No issue is closed here.
- **D-Stop.** CP1 re-runs the three checks on the branch before writing. If the reaper run finds an orphan, or a mutation does not fail its test, or any posture lacks the sentence, **stop**: the first needs a test fix with a failure-only mutation (a `test:` change of payload scripts, which moves the manifest record and needs its own checkpoint and release checkpoint), the other two are reported.
- **D-Roadmap.** Row 46 after row 45 and before the deferred row, in the style of the rows above: `Current`, `Done (accepted by policy; a docs: change, no release)` at acceptance. `docs/ACTIVE_MILESTONE.md` gets the usual text.

## 3. Open decisions

None: `docs/TECHNICAL_DECISIONS.md` has no open row on test evidence or release postures.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Record the reaper run, the race-hook verdict and the posture decision; add roadmap row 46 | - | 1 | 1 |

<!-- CP1 -->
### CP1 — Record the reaper run, the race-hook verdict and the posture decision; add roadmap row 46

**Files:** `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`, `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`.

- **Read first, write after:** re-run section 0's three checks on the branch (D-Stop); then write the evidence file, row 46 and the active-milestone text; then post the three comments and record their URLs in the item's implementation summary.
- **Done when:** flows 1 to 9 hold; `git diff --exit-code f9d63f4246041afc21ff35d85bc2e994fc6d66f8 -- payload tools fixtures templates manifest.json docs/release-history.md docs/RELEASING.md` exits 0.

**Verification:** flows 1 to 9 (offline), then 10 to 13 (full environment).
<!-- /CP1 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". Flows 1 to 9 run offline: no network, no real `gh`, no install, no socket, no zlib-ng, no Python 3.12; nothing writes in the real repository. No flow needs the forge (the comments are checked as text in the evidence file; their posting is shown by the implementation report), so there is no fake `gh`. Setup, once, from the repository root, with `TMPDIR` as in section 0:

- `export REPO="$PWD" B=f9d63f4246041afc21ff35d85bc2e994fc6d66f8 E=docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`
- `rm -rf "$TMPDIR/cand" && mkdir -p "$TMPDIR/cand" && git -C "$REPO" archive HEAD docs payload manifest.json | tar -x -C "$TMPDIR/cand"`
- `flows.sh` below is saved to `$TMPDIR/flows.sh` and run as `sh "$TMPDIR/flows.sh" <n>`; its greps name the evidence file, the roadmap and git objects, never `docs/ACTIVE_MILESTONE.md`.

```sh
cd "$TMPDIR"; R=docs/ROADMAP.md; T=payload/scripts/workflow_state_completion_obligations_test.py; X=payload/scripts/workflow_retention.py
S='The release tooling and the maintainer documents are not part of the installed release.'
sec() { awk -v h="## $1" '/^## /{p=(index($0,h)==1)} p' cand/$E; }
posture() { git -C "$REPO" show "$1:manifest.json" | python3 -I -c "import json,sys; print(json.load(sys.stdin)['manager']['downgrade_boundary']['posture'])"; }
case "$1" in
1) for h in 'Point 1 (#170)' 'Point 3 (#116)' 'Point 3 (#158)' 'Issue comments'; do echo "$h: $(grep -c -F "## $h" cand/$E)"; done; git -C "$REPO" cat-file -e "$B:$E" 2>&1 | head -1 ;;
2) sec 'Point 1 (#170)' | grep -q -F 'chunk status 0' && echo status0; sec 'Point 1 (#170)' | grep -q -F '10 tests' && echo tests10; sec 'Point 1 (#170)' | grep -o -E '`\[git\]`|`git maintenance run --auto --quiet --detach`' | sort -u; sec 'Point 1 (#170)' | grep -q -F 'nothing else' && echo no-third-kind ;;
3) sec 'Point 3 (#116)' | grep -q -F 'ALREADY-FIXED' && echo already-fixed; for l in 5514 5769; do git -C "$REPO" show "$B:$T" | sed -n "${l}p" | grep -c -E 'a.txt|index.jsonl'; done
   for l in 691 1012 1034; do git -C "$REPO" show "$B:$X" | sed -n "${l}p" | grep -c -E 'O_NOFOLLOW|st_nlink'; done ;;
4) for v in v2.25.6 v2.25.7 v2.26.0 v2.27.0 v2.28.0 v2.29.0 v2.29.5; do echo "$v $(posture $v | grep -c -F "$S")"; done
   git -C "$REPO" show "$B:manifest.json" | python3 -I -c "import json,sys; a=json.load(sys.stdin)['artifacts']; print(len(a), [x['target_path'] for x in a if x['target_path'].startswith('tools') or x['target_path'] in ('docs/RELEASING.md','docs/ROADMAP.md','docs/release-history.md')])" ;;
5) posture v2.27.0 | sed "s/$S//" | grep -c -F "$S"; git -C "$REPO" tag --list v2.27.0 ;;
6) grep -n -o -E '^\| (45|46|27) ' cand/$R | tr -d '\n'; echo; git -C "$REPO" show "$B:$R" | grep '^| 45 ' > r45; grep '^| 45 ' cand/$R | cmp - r45 && echo row45-same; grep '^| 46 ' cand/$R | awk -F'|' '{print $5}' | cut -c1-20 ;;
7) cd "$REPO"; git diff --name-only "$B" | sort; git diff --exit-code --quiet "$B" -- payload tools fixtures templates manifest.json docs/release-history.md docs/RELEASING.md .claude scripts .workflow-manager .github CLAUDE.md .gitignore; echo "release source and installation: exit $?" ;;
8) rm -rf m && mkdir m && git -C "$REPO" archive "$B" payload/scripts/workflow_retention.py | tar -x -C m
   python3 -I - <<'PY'
import pathlib
p = pathlib.Path("m/payload/scripts/workflow_retention.py"); t = p.read_text()
for name, old, new in (("m1", 'flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)', 'flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)'),
                       ("m2", 'flags = os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)', 'flags = getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)'),
                       ("m3", "or info.st_nlink != 1:", "or False:")):
    print(name, t.count(old), t.count(new))
PY
   ;;
9) n0=$(git -C "$REPO" status --short | wc -l); rm -rf full && mkdir full && git -C "$REPO" archive HEAD | tar -x -C full
   python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   sed -i '3s/ Last checked with: .*$//' full/docs/gates.md; python3 -I full/tools/docs/check_docs.py --root "$TMPDIR/full"; echo "exit $?"
   echo "status lines: before $n0 after $(git -C "$REPO" status --short | wc -l)" ;;
esac
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `sh "$TMPDIR/flows.sh" 1` | four lines `<heading>: 1` (one section each), then a git error that the evidence file is absent at the base |
| 2 | `sh "$TMPDIR/flows.sh" 2` | read inside the point's own section only: `status0`, `tests10`, the two orphan kinds (`` `[git]` `` and `` `git maintenance run --auto --quiet --detach` ``, sorted) and `no-third-kind`; no count of helpers is pinned: the durable reaper record |
| 3 | `sh "$TMPDIR/flows.sh" 3` | `already-fixed` (inside the #116 section only), then `1 1` for the two hook lines and `1 1 1` for the three engine lines at the base: the cited file:line evidence is real |
| 4 | `sh "$TMPDIR/flows.sh" 4` | each of the seven postures `…: 1`, then `83 []`: the sentence is kept by every release and no installed artifact is a tooling or maintainer path |
| 5 | `sh "$TMPDIR/flows.sh" 5` | `0` (failure-only mutation: the 2.27.0 posture with the sentence cut no longer contains it), then `v2.27.0` (the tag exists, so flow 4 read the published manifest) |
| 6 | `sh "$TMPDIR/flows.sh" 6` | `45`, `46`, `27` in file order; then `row45-same`; then a status starting `Current` |
| 7 | `sh "$TMPDIR/flows.sh" 7` | the names `docs/ACTIVE_MILESTONE.md`, the plan, the evidence file, `docs/ROADMAP.md`, the registry, mapping and artifacts files and `docs/ai-workflow/WORKFLOW_STATE.json`, and no other; then `release source and installation: exit 0` |
| 8 | `sh "$TMPDIR/flows.sh" 8` | `m1 1 0`, `m2 1 0`, `m3 1 0`: each old string occurs once in the base file and its replacement nowhere (the three mutations apply; flow 10 runs them) |
| 9 | `sh "$TMPDIR/flows.sh" 9` | the first checker run `exit 0`; after the stamp is cut from the gates page the second names `docs/gates.md` and `exit 1`; `status lines: before N after N` |
| 10 | **Full environment (the fixture and `zstd`).** `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`; copy it three times, apply one mutation of flow 8 to each copy's `scripts/workflow_retention.py`; in each, `python3 -B workflow_state_completion_obligations_test.py RetentionArchive.test_a12_a_file_replaced_by_a_symlink_after_the_walk_is_opened_with_no_follow RetentionArchive.test_a15_the_substitutions_made_after_the_selection_are_refused_by_the_open_itself`; and once unmutated | unmutated `OK` (2 tests); m1 fails the A12 test (`None != 40`); the combined run of the two tests, whose five A15 variants share one fixture, prints for m2 five A15 failures (first `symlink to an outside file`, `0 != 2`; the repository-file symlink, hard link, directory and FIFO `[] is not true`, the cascade of the first) and for m3 three (hard link first, then directory and FIFO, `[] is not true`); one variant run alone fails as section 0 says (m2: the two symlink variants; m3: the hard link). Section 0 and the evidence file use this same wording |
| 11 | **Full environment (the Manager checkout).** From the fixture's `scripts/`: `python3 -I -S -B /home/rodrigo/Workspace/workflow-manager/tests/parallel/reaper.py --report "$TMPDIR/r.json" --chunk-id pcms -- python3 -B workflow_gate_policy_test.py TestPlainCommandMalformedState` | `Ran 10 tests`, `OK`; the report's `chunk_status` 0 and its orphans only `[git]` and `git maintenance run --auto --quiet --detach`, all `exited` |
| 12 | **Full environment (the nine suites).** The suites loop of `docs/RELEASING.md` from the staged fixture | all nine pass |
| 13 | **Full environment (zlib-ng).** `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python -m unittest discover -s tools/release -p '*_test.py'`; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | all pass |
