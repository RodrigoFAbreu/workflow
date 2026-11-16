# test-hardening-owner-points: evidence (CP1)

Companion to `TEST_HARDENING_OWNER_POINTS_PLAN.md` (D-Evidence). Excluded at the plan stage, protected at the implementation stage.
Every result below was produced on the branch `milestone/test-hardening-owner-points`, at base `f9d63f4246041afc21ff35d85bc2e994fc6d66f8`, from the staged conformance fixture (`python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`; no record adjusted, nothing shipped is changed). The scratch directory `$TMPDIR` is `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w53-tmp`. The scratch scripts are neither shipped nor committed.

## Point 1 (#170)

**Class: KEEP the test, RECORD the run.** No test change.

Command, from the fixture's `scripts/` directory:

```
python3 -I -S -B /home/rodrigo/Workspace/workflow-manager/tests/parallel/reaper.py --report "$TMPDIR/r.json" --chunk-id pcms -- python3 -B workflow_gate_policy_test.py TestPlainCommandMalformedState
```

Result: `Ran 10 tests`, `OK`; 10 tests, chunk status 0 (the report's `chunk_status`), `supported` true. The report lists 79 re-parented processes, all with fate `exited`: 78 `[git]` and 1 `git maintenance run --auto --quiet --detach`, and nothing else. The counts of git helpers vary from run to run (the investigation run saw 77 and 2, the first review run 78 and 1, this run 78 and 1): what is pinned is the two kinds and the absence of a third kind. That is the accepted set of the earlier items (`COMMAND_WORDING_EVIDENCE.md`: no orphan beyond Git's own detached maintenance).

The class's own children (`payload/scripts/workflow_gate_policy_test.py`, lines 7365 to 7390) are `subprocess.run` calls, which wait for their child, so the class has no orphan source of its own to declare or remove. Point 1 of #170 is settled; point 2 of #170 (it needs a real change to the bundle files) stays open.

The raw reports of Point 1 are kept next to this file (added by `retention-docs-notes`, #188; both are byte copies of the scratch files named above):

- `TEST_HARDENING_OWNER_POINTS_REAPER_REPORT.json` (`sha256` `f965db8e91df0c93df73488fa243295ef98688ee29f9333b6869295485572ec9`, 4136 bytes): a later run of the command above, written 2026-11-15 12:58:17Z, after this text was committed (12:55:44Z). Chunk status 0, `supported` true, 78 `[git]` and 1 `git maintenance run --auto --quiet --detach`, all `exited`. It is not the run this text calls "this run": every run wrote the same `$TMPDIR/r.json`, so that report was overwritten and cannot be reconstructed.
- `TEST_HARDENING_OWNER_POINTS_REAPER_INVESTIGATION.json` (`sha256` `615de6f7173b2a3b3b83b49b6c5d2aca8e126c864e662a26a12561d0472b7d04`, 4192 bytes): the investigation run (written 12:22:39Z, before plan approval), 77 `[git]` and 2 `git maintenance` processes, all `exited`.

The A12/A15 mutation runs (Point 3 below) were terminal output and were never saved; they cannot be reconstructed, so the table below remains the only record of those runs. No log is invented here.

## Point 3 (#116)

**Class: ALREADY-FIXED.** No test change.

The point asked that the A12 and A15 race hooks substitute only after the earlier selection checks. They do, since 2.21.0 (plan EPR-011), in `payload/scripts/workflow_state_completion_obligations_test.py` at the base:

- A12, `test_a12_a_file_replaced_by_a_symlink_after_the_walk_is_opened_with_no_follow` (line 5505): the substitution is made inside the wrapped `os.open` of `a.txt` (line 5514), after the walk, and the test asserts the observed `ELOOP` and that the sentinel was never read (lines 5540 to 5543).
- A15, `test_a15_the_substitutions_made_after_the_selection_are_refused_by_the_open_itself` (line 5757): the substitution is made inside the `O_RDWR` open of `index.jsonl` (line 5769), after the selection tests of line 5738 refused the same five variants.

Three failure-only mutations of a copy of `payload/scripts/workflow_retention.py` (each old string is a substring of the named line, occurs once in the base file, its replacement nowhere; the base file is never edited) in a copy of the fixture:

| id | engine line at the base | old string | new string |
|---|---|---|---|
| m1 | 691, `_open_file` | `flags = os.O_RDONLY \| os.O_NOFOLLOW \| getattr(os, "O_NONBLOCK", 0)` | `flags = os.O_RDONLY \| getattr(os, "O_NONBLOCK", 0)` |
| m2 | 1012, `_open_index` | `flags = os.O_NOFOLLOW \| getattr(os, "O_CLOEXEC", 0) \| getattr(os, "O_NONBLOCK", 0)` | `flags = getattr(os, "O_CLOEXEC", 0) \| getattr(os, "O_NONBLOCK", 0)` |
| m3 | 1034 | `or info.st_nlink != 1:` | `or False:` |

Run from each copy's `scripts/`: `python3 -B workflow_state_completion_obligations_test.py RetentionArchive.test_a12_a_file_replaced_by_a_symlink_after_the_walk_is_opened_with_no_follow RetentionArchive.test_a15_the_substitutions_made_after_the_selection_are_refused_by_the_open_itself`.

| run | result |
|---|---|
| unmutated | `Ran 2 tests`, `OK` |
| m1, combined | 1 failure: the A12 test, `AssertionError: None != 40` |
| m2, combined | 5 failures, all of the A15 test: `symlink to an outside file` first (`0 != 2`), then `symlink to a repository file`, `hard link`, `directory` and `FIFO`, each `[] is not true` |
| m3, combined | 3 failures, all of the A15 test: `hard link` first (`0 != 2`), then `directory` and `FIFO`, each `[] is not true` |

The five A15 variants share one fixture, so a mutation that lets one variant archive `w00` makes every later variant fail `assertTrue(fired)` (`[] is not true`): the hooked `O_RDWR` open of `index.jsonl` is never reached again. The `[] is not true` failures are that cascade of the first failure, not five independent detections. Run alone (the A12 test alone, the A15 test alone): m1 fails the A12 test and passes the A15 test; m2 passes the A12 test and fails the A15 test starting with the outside-file symlink; m3 passes the A12 test and fails the A15 test starting with the hard link. One variant alone (the A15 test run from a scratch copy of the test file whose variant tuple names that one variant; the shipped test file is never edited), each of the five in turn: unmutated, all five pass; m2 fails exactly the two symlink variants; m3 fails exactly the hard link. That is what the plan's investigation saw.

Each mutation makes its test fail and the unmutated tests pass, so both hooks are verified to run after the selection checks. Point 3 of #116 is dropped.

## Point 3 (#158)

**Class: KEEP, true.** No posture change, no release.

The sentence is `The release tooling and the maintainer documents are not part of the installed release.` `git show <tag>:manifest.json`, key `manager.downgrade_boundary.posture`, ends with it in every published release that exists from v2.25.6 on (checked one by one): v2.25.6, v2.25.7, v2.26.0, v2.27.0, v2.28.0, v2.29.0, v2.29.1, v2.29.2, v2.29.3, v2.29.4 and v2.29.5 (11 tags, each `1`).

It is true. At the base `manifest.json` lists 83 artifacts; every `target_path` is under `.claude/commands/`, `docs/ai-workflow/` or `scripts/`, plus `CLAUDE.md`, `docs/ACTIVE_MILESTONE.md` and `scripts/prepare-ai-review.sh`. None is under `tools/` and none is `docs/RELEASING.md`, `docs/ROADMAP.md` or `docs/release-history.md` (the maintainer pages): the check prints `83 []`. With the sentence cut from the v2.27.0 posture it no longer matches (`0`), so the check can fail. v2.27.0 is immutable and needs no correction. Points 1 to 3 of #158 are now all settled.

## Release

Nothing under `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changes, so this item releases nothing: a `docs:` pull request, impact none, the manifest keeps 2.29.5.

## Issue comments

Posted by `gh issue comment` after this file was committed (D-Comments); no issue is closed. The text is word for word.

### RodrigoFAbreu/workflow#170

Point 1 is settled. `TestPlainCommandMalformedState` was run under the Manager's reaper (`python3 -I -S -B tests/parallel/reaper.py --report R.json --chunk-id pcms -- python3 -B workflow_gate_policy_test.py TestPlainCommandMalformedState`, from the staged conformance fixture): `Ran 10 tests`, `OK`, `chunk_status` 0, 79 re-parented processes, all `exited`: 78 `[git]` and 1 `git maintenance run --auto --quiet --detach`, and nothing else (the number of git helpers varies run to run; the two kinds do not). That is the accepted set of the earlier items. The class's own children are `subprocess.run` calls, which wait, so it has no orphan source of its own: no test change. Evidence: `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`, "Point 1 (#170)". Point 2 stays open.

### RodrigoFAbreu/workflow#116

Point 3 is already fixed, so it is dropped. The A12 hook substitutes inside the wrapped `os.open` of `a.txt`, after the walk (`workflow_state_completion_obligations_test.py` line 5514, test at line 5505), and the A15 hook inside the `O_RDWR` open of `index.jsonl`, after the selection tests that refuse the same five variants (lines 5769 and 5738, test at line 5757); this was built in 2.21.0 (EPR-011). Three failure-only mutations of a copy of `workflow_retention.py` make the tests fail: dropping `O_NOFOLLOW` from `_open_file` (m1) fails the A12 test (`None != 40`), dropping it from `_open_index` (m2) fails the A15 test, and dropping the `st_nlink != 1` test (m3) fails the A15 test; unmutated, both pass. The five A15 variants share one fixture, so after the first failure the later variants fail `[] is not true`. Evidence: `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`, "Point 3 (#116)".

### RodrigoFAbreu/workflow#158

Point 3 is decided KEEP: the 2.27.0 posture sentence "The release tooling and the maintainer documents are not part of the installed release." is true and stays. `manifest.json` lists 83 artifacts, and every `target_path` is under `.claude/commands/`, `docs/ai-workflow/` or `scripts/`, or is `CLAUDE.md`, `docs/ACTIVE_MILESTONE.md` or `scripts/prepare-ai-review.sh`; none is under `tools/` or is `docs/RELEASING.md`, `docs/ROADMAP.md` or `docs/release-history.md`. The manifests of v2.25.6, v2.25.7, v2.26.0, v2.27.0, v2.28.0 and v2.29.0 to v2.29.5 all keep the sentence. v2.27.0 is immutable and needs no correction: no posture change and no release. Points 1 to 3 are now all settled. Evidence: `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`, "Point 3 (#158)".
