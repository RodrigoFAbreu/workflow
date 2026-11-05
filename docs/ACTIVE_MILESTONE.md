# Active Milestone

## Milestone

**Awaiting functional review** (`AWAITING_FUNCTIONAL_REVIEW`). W38: `retention-report-unreadable` (`process`, governing version `2.2`), branch
`milestone/retention-report-unreadable`, roadmap row 33 (RodrigoFAbreu/workflow#113 item 1, #116 item 1 and #119
item 8). Plan: `docs/ai-workflow/RETENTION_REPORT_UNREADABLE_PLAN.md` (revision 3, approved by gate policy). The goal,
Workflow 2.25.6 (a `fix:` patch, released after the merge of the pull request): the retention report says
`archive unreadable` / `review folder unreadable` where it cannot tell (a partly counted folder is a lower bound),
`review folder in .removing` for a folder an interrupted removal left, and records the failed directory itself in
`read_errors`. The JSON, every refusal code and exit code stay as they are. Base commit `e687d51`; the previous
milestone, W37 `retention-error-paths`, is accepted (Workflow 2.25.5).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The report text, the recorded path, tests and page | **complete** (see the commit of this checkpoint) |
| CP2 | Release 2.25.6 | **complete** (see the commit of this checkpoint) |

## Verified state

- CP1: `RetentionReportUnreadable` (T1 to T6) was red on the unedited tree and is green under `python3` (3.14) and
  `/home/rodrigo/.local/bin/python3.12`; the failure-only mutations m1 to m12 each fail at least one named test.
- CP1 staged in a disposable clone (D-Staging): the nine suites, `tools/docs`, `check_docs.py` and
  `check-manager-block` pass; `tools/release` has one failure owned by CP2, the 2.25.5 release class's pin of the
  obligations suite count (284; it is now 290 with the six new tests). CP2 moves that pin.

- CP2 (release 2.25.6), verified in a disposable clone of the working tree committed there: `RetentionReportUnreadable`
  green under `python3` (3.14) and `/home/rodrigo/.local/bin/python3.12`; `tools/release` (307 tests, zlib-ng
  interpreter), `tools/docs` (34), `check_docs.py`, `check-manager-block --manager-releases` and `release.py build`
  pass; `workflow-manager verify .` reports the installation matches 2.25.5 (the installation is not touched). The nine
  suites run from the stock `stage-conformance` fixture; the result is recorded in the implementation bundle.
  `conformance.suites` was measured (obligations suite 290), not typed.
- Self-review: the new tests now hold what D-Tests asks of every case (`_rr_snapshot` unchanged, the `--json` facts as
  literals, the exact stderr) and T5 compares against golden literals; the engine is unchanged. The mutations m1 to m12,
  plus m13 (the report writes a file) and m14 (an unaffected line reworded), each fail at least one test under both
  interpreters. `manifest.json` takes the test file's new `sha256` and `size`; the suite count stays 290.

- Functional gate (implementation revision 1, reviewed at `d6e056a`; `HEAD` when the gate opened `6d23a08`): the
  implementation bundle's recorded run (`.ai-review/retention-report-unreadable/current/TEST_RESULTS.md`) postdates the
  last code or test change (`ea23b3e`), and the tree was clean at the gate, so the nine suites were not rerun. Re-checked
  at the gate: `RetentionReportUnreadable` (6 tests) OK under `python3` (3.14) and `/home/rodrigo/.local/bin/python3.12`;
  plan section 6 flows 1 to 5 run under both interpreters with the outputs listed below. The orphan-rule (reaper) run
  that the bundle lists as not yet made is still open: flow 7.

## Functional review checklist

What changes: when the retention report cannot read part of the archive store or of `.ai-review`, it now says
`unreadable` (or `at least`, for a partial size) instead of `no archive` / `no review folder`; a `.removing` folder is
named as such; and `read_errors` names the directory that failed. The JSON, every refusal code and every exit code are
unchanged, and the report exits 0 for an incomplete view.

### Setup

1. Run nothing against this repository's real `.ai-review/`, the real archive store, the forge or the network. Every
   flow uses a scratch repository that the harness builds; the harness passes the forge seam, so `gh` is never called.
2. Use a writable `TMPDIR` outside this clone. Make two reference trees outside it, from git only:
   - `base/`: `git archive e687d51 payload/scripts | tar -x -C base` (the base commit);
   - `cand/`: `git archive <reviewed HEAD> payload/scripts | tar -x -C cand`.
   Use commit-to-commit diffs (`git diff A B`), not working-tree forms, so git writes nothing into the clone.
3. Copy the one `python` block of `docs/ai-workflow/RETENTION_REPORT_UNREADABLE_PLAN.md` section 6 to `flow.py` in the
   scratch directory, and run `python3 -I flow.py <base|cand>/payload/scripts <case>` from there, for `case` in
   `clean`, `archive`, `folder`, `partial`, `removing`.
4. Repeat each run with `/home/rodrigo/.local/bin/python3.12` (the CI interpreter). The sandbox PATH may not reach it;
   if it does not, record that leg as not run, not as passed.

Sandbox note: flows 1 to 6 and 8 need only `python3`, `git` and the scratch directory, so they run offline. Flow 7 is
the operator's full-environment check.

### Test data

Nothing to seed by hand; the harness builds it. The scratch repository has six finished items, `w00` to `w05`. `w00`
holds `a.txt` (5 B), `empty/x` and `zz/q.txt` (3 B): 9 B in 3 files, and a 20-byte `w00.tar.zst` dated 40 days before
the run. `w01` and `w02` have no review folder and no archive. The `case` argument applies one stand-in:
`archive` (archive directory not searchable), `folder` (`.ai-review` readable but not searchable), `partial`
(`w00/zz` not openable), `removing` (`w00` moved into `.removing`).

### Flows and expected results

Observed at the reviewed revision under both interpreters. "Identical" means the base and candidate lines match byte
for byte, apart from the `REPO` and `STORE` scrubbing. Every run exits `0 0` and prints `tree unchanged: True`.

| Flow | Run | Expect |
| --- | --- | --- |
| 1 `clean` | base and cand | outputs identical; `w00: 9 B in 3 files; archive 20 B, 40 days old, prunable`; `w01`, `w02`: `no review folder; no archive`; `complete: true` |
| 2 `archive` | base, then cand | base `w00: 9 B in 3 files; no archive`. cand `w00: 9 B in 3 files; archive unreadable`; `w01`, `w02`: `no review folder; archive unreadable`. `read_errors` identical (5 entries: `STORE/widgets`, `STORE/widgets/.removing`, the three archives) with the `warning: incomplete: 5 path(s)` line; `json:` identical (`readable: False`, `complete: false`) |
| 3 `folder` | base, then cand | base `w00: no review folder; archive 20 B, 40 days old, prunable`. cand `w00: review folder unreadable; archive 20 B, 40 days old, prunable`; `w01`, `w02`: `review folder unreadable; no archive`. `read_errors` identical (`REPO/.ai-review/w00` to `w05`); `json:` identical (`folder` `present: false`, `complete: false`, bytes 0) |
| 4 `partial` | base, then cand | base `w00: 6 B in 2 files; archive 20 B, 40 days old, prunable`, `read_errors` `REPO/.ai-review/w00/empty/zz`. cand `w00: at least 6 B in 2 files (partly unreadable); archive 20 B, 40 days old, prunable`, `read_errors` `REPO/.ai-review/w00/zz`. This path change is the intended data change. `json:` identical (`complete: false`, 6 B, 2 files) |
| 5 `removing` | base, then cand | base `w00: no review folder; archive 20 B, 40 days old, prunable`. cand `w00: review folder in .removing; archive 20 B, 40 days old, prunable`. Both print `Interrupted removals (1): w00, finish them with `remove <id> --apply``; `json:` identical (`removing: ["w00"]`, `complete: true`) |
| 6 scope, git only | `git diff --stat e687d51 39f870b -- payload docs` | nine files: `docs/ACTIVE_MILESTONE.md`, `docs/RETENTION.md`, the plan, `docs/ai-workflow/WORKFLOW_STATE.json`, the item's `registry/…-artifacts.json`, `registry/…-registry.json` and `requirements/…-mapping.json`, `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`. The script diff changes `_review_folder` and `render_text` and adds one helper, `_can_fail_walk`, after `_open_review_root`. The range ends at CP1 (`39f870b`) because CP2 also touches `payload/` and `docs/`; the plan's literal "only" needs that range |
| 7 operator only | full environment, plus the sandbox-runnable class | `python3 -B payload/scripts/workflow_state_completion_obligations_test.py RetentionReportUnreadable` gives 6 tests OK (runnable offline). Still to run in the full environment: the nine suites, `tools/docs`, `check_docs.py`, `check-manager-block --manager-releases`, the `tools/release` tests with the zlib-ng interpreter (`docs/RELEASING.md`), and the Manager's orphan-rule (reaper) run. Recorded at `d6e056a`: all green except the orphan-rule run |
| 8 release scope, git only | `git diff --name-only e687d51 HEAD` | 16 files: the flow 6 files, plus `docs/ROADMAP.md`, `docs/release-history.md`, `manifest.json`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `payload/scripts/workflow_protocol.py` and its test, and `tools/release/release_test.py`. None under `scripts/`, `.claude/`, a command file or `docs/exit-codes.md`. `manifest.json` says 2.25.6, and the `release-history.md` row and `docs/RETENTION.md` name the same release and the same way back |

### Known limitations

These are accepted for this milestone. Report one as a finding only if the behaviour contradicts the text above.

- **Wide directories are slow.** `_review_folder` searches its pending list from the start at yield time
  (`workflow_retention.py`, around line 272). Both implementation reviewers measured several seconds at 16,000 to
  20,000 sibling directories. This repository's busiest folder has 38. Not fixed here.
- **A readability change mid-run can name the wrong entry.** If `a/zz` opens during the probe and fails during the walk,
  a readable sibling `w00/zz` can be recorded as the failed path. It needs a permission change inside the run.
  Incompleteness and refusals still hold.
- **An item folder inside an unreadable `.removing` prints `no review folder`.** Reproduce with the `removing` case and
  `.removing` at mode 000: the report still says `INCOMPLETE` and names `.removing` in `read_errors`, but the line is
  not `unreadable`. `docs/RETENTION.md`'s list of undecided cases omits this one.
- **Some symlink and mode cases are not covered.** A `.ai-review/w00` that is itself a symlink prints
  `no review folder` with no `INCOMPLETE` entry, on the base and the candidate alike. A symlinked archive directory and
  a mode-000 item folder were seen on the way and are not in this milestone. The plan's section 0 and open decision 1
  send them to one comment on RodrigoFAbreu/workflow#113 at acceptance.
- **Not tested:** the stat-failure branch of `_can_fail_walk`. A mutation that returns `False` there keeps the class
  green. The behaviour was checked by hand on a real file.

### Where findings go, and the next steps

- Put findings at `.ai-review/retention-report-unreadable/feedback/FUNCTIONAL_REVIEW.md`.
- Once testing is clean, `/accept-milestone` is the only acceptance command. It needs every checkpoint `COMPLETE`
  (CP1 and CP2 are). There is no command that records acceptance of a partial round.
- A finding fixable inside the approved scope goes to `/apply-functional-review`'s bounded branch. A new or wider one
  goes to its broad branch, a `retention-report-unreadable-remediation-<n>` child work item.

## Next action

Manual functional review, at the gate. Run the checklist above, and place findings at the feedback path.
