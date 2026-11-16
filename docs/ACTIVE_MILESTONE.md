# Active Milestone

## Milestone

**Awaiting functional review.** W55: `retention-test-pins` (`process`, governing version `2.2`), branch
`milestone/retention-test-pins`, roadmap row 48 (`Current`). The plan is `docs/ai-workflow/RETENTION_TEST_PINS_PLAN.md`
(revision 1, approved by gate policy). The change is a `fix:` patch: Workflow 2.29.7, released at `f7a59df`, its publication
follows the merge.

## Goal

Six tests that pin retention lines no existing test pinned, all in one class, `RetentionTestPins`, in
`payload/scripts/workflow_state_completion_obligations_test.py`:

- a future mtime clamps the age to zero (RodrigoFAbreu/workflow#113, point 5a);
- `build_report` without `run` uses the forge default runner (#113, 5b);
- a read that fails after a successful open is `unreadable` and keeps nothing (#116, 2a);
- an archive whose bytes differ with names, types and sizes equal is not kept (#116, 2b);
- a stat-only change after the hash puts the folder back and deletes nothing (#119, 4c);
- the selection repeated under the lock stops the run on its own refusal (#119, 4c).

No line of `workflow_retention.py` changes and no behaviour changes. A defect found by a pin would be a finding, not a fix here.

## Checkpoints

- CP1 (the six pins, roadmap row 48): `COMPLETE` (start commit `7cbccc4`, commit `d7e2ef9`).
- CP2 (release 2.29.7: manifest, protocol constant and document, release history, release tests): `COMPLETE` (commit `f7a59df`).

Implementation revision 1, reviewed implementation head `f7a59df9da8e8d8927ba05e076c9303cecabb46e`. `technical_approval` is
`CURRENT` (basis `POLICY_SATISFIED`). Since `f7a59df`, no `payload/` file has changed; only `WORKFLOW_STATE.json` and metadata
commits have.

## Verified state

Checked by `/prepare-functional-review` on the candidate `f7a59df` payload, against the base `5fe44bb`:

- Nine suites from a fresh staged fixture (`release.py stage-conformance --commit HEAD`): all nine pass. `workflow_state_test.py`
  ran 1250 tests, OK, one skip; `workflow_acceptance_matrix_test.py` and `workflow_protocol_test.py` skip type-independent rows
  and historical-version checks by design.
- `RetentionTestPins` in the fixture: 6 tests, OK.
- Six failure-only mutations of `workflow_retention.py` (m1, m2, m3, m4, m5b, m6) each fail exactly their own pin.
- `tools/docs` tests: 34 tests, OK. `check_docs.py`: clean.
- `check-manager-block`: `ok: 2.29.7`. `check-title ... --agree --head f7a59df`: `impact=patch`, version `2.29.6 -> 2.29.7` agrees.

## Functional review checklist

Gate: `AWAITING_FUNCTIONAL_REVIEW`, implementation revision 1 (reviewed head `f7a59df`), plan revision 1. The candidate is the
`payload/` tree at `f7a59df`; base `5fe44bbef43e7b5d47950a79d0c805542e9bb0d2`. The checklist's evidence commit (SHA and blob)
is reported by `/prepare-functional-review` and read back by `/review-functional`.

Every flow runs offline, reads the clone only, and writes only under a scratch directory `$S` outside the clone. No flow needs
GitHub, the network, or a real `claude`, `codex` or `ssh`. The `gh` stand-in is never called.

### Setup

1. Run from the clone root. `git status --porcelain` must be empty and `HEAD` must be the commit under test (any commit at or
   after `f7a59df` with no `payload/` change).
2. `export S=$(mktemp -d)`. Use `python3 -B` everywhere so no bytecode lands in the clone.
3. Python 3.14 with `zstd` on `PATH`. If `zstd` is missing, the six pins skip silently, so flow F3 must show no skip.

### Test data

Nothing is seeded in the clone. The fixture comes from `stage-conformance` into `$S/fixture`. Flow F4 writes its mutated copies
into `$S/mut/`.

### Flows and expected results

- **F1, the payload scope.** `git diff --stat 5fe44bb -- payload`, then `git diff --quiet 5fe44bb -- payload/scripts/workflow_retention.py; echo $?`.
  Expect: four files: `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (8 +-), `scripts/workflow_protocol.py` (2 +-),
  `scripts/workflow_protocol_test.py` (4 +-) and `scripts/workflow_state_completion_obligations_test.py` (188 +); 195 insertions,
  7 deletions. The `echo` prints `0`.
- **F2, lines were only added to the test file.** `git diff 5fe44bb -- payload/scripts/workflow_state_completion_obligations_test.py | grep -c '^-[^-]'`.
  Expect: `0`.
- **F3, the six pins pass unmutated.** `python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"` (exit 0),
  then `cd "$S/fixture/scripts" && python3 -B workflow_state_completion_obligations_test.py RetentionTestPins`.
  Expect: `Ran 6 tests`, `OK`, no `skipped`.
- **F4, each pin fails only under its own mutation.** Save the script below as `$S/mut.py` (a heredoc, outside the clone) and run
  `python3 -B "$S/mut.py" "$S/fixture/scripts" "$S/mut"` from `$S`.

  ```python
  import shutil, subprocess, sys, pathlib, re
  src = pathlib.Path(sys.argv[1]); base = pathlib.Path(sys.argv[2])
  R = "workflow_retention.py"
  muts = {
   "m1": ('age = max(0, int((now - modified).total_seconds() // 86400))', 'age = int((now - modified).total_seconds() // 86400)'),
   "m2": ('if run is not None:\n', 'if True:\n'),
   "m3": ('if source.error is not None:', 'if False:'),
   "m4": ('if count != record["size"] or digest.hexdigest() != record["sha256"]:', 'if count != record["size"]:'),
   "m5b": ('if [_comparable(r) for r in _scan(removing_fd, item_id)] != [_comparable(r) for r in records]:', '_scan(removing_fd, item_id)\n        if False:'),
   "m6": ('again = _select_removal(repo_root, item_id, archive_root, now, run, resolve, zstd, fds)', 'again = sel'),
  }
  for name, (old, new) in muts.items():
      d = base / name
      if d.exists(): shutil.rmtree(d)
      shutil.copytree(src, d)
      text = (d / R).read_text()
      if text.count(old) != 1:
          print(name, "anchor count", text.count(old)); continue
      (d / R).write_text(text.replace(old, new))
      out = subprocess.run([sys.executable, "-B", "workflow_state_completion_obligations_test.py", "RetentionTestPins"], cwd=d, capture_output=True, text=True)
      fails = re.findall(r"^(?:FAIL|ERROR): (\S+)", out.stdout + out.stderr, re.M)
      print(name, "rc", out.returncode, "failing:", sorted(set(fails)))
  ```

  Expect: six lines, each `rc 1`, each with exactly one failing test: m1 `test_p1_…`, m2 `test_p2_…`, m3 `test_p3_…`,
  m4 `test_p4_…`, m5b `test_p5_…`, m6 `test_p6_…`. No `anchor count` line.
- **F5, the release and the title.** `git show d7e2ef9:manifest.json` and `git show f7a59df:manifest.json` read `workflow_version`
  (2.29.6 and 2.29.7). `python3 tools/release/release.py check-title "fix: add the missing retention tests for the future-mtime clamp, the default forge runner, a failed read, same-size altered bytes and the removal re-checks" --agree --head f7a59df`.
  Expect: `impact=patch`, then `version 2.29.6 -> 2.29.7 (patch) agrees with the title`. Pin `--head f7a59df`: `--agree` at a
  metadata commit compares it with its parent and refuses.
- **F6, the manager block and the docs.** `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`
  and `python3 -B tools/docs/check_docs.py`. Expect: `ok: 2.29.7 carries a valid manager block…`; checker exit 0.
- **F7, the nine suites.** From the fixture (F3's `$S/fixture`), run each name in `manifest.json` `manager.conformance.suites` with
  `python3 -B "$S/fixture/scripts/<suite>" </dev/null`. Run them from the fixture's `scripts` directory, as CI does.
  Expect: each suite exits 0 (`OK`; a skip is by design in the acceptance-matrix and protocol suites).
- **F8, no installation file changed.** `git diff --name-only 5fe44bb -- .claude scripts .workflow-manager .github CLAUDE.md`.
  Expect: no output.

### Known limitations and out of scope

- Not sandbox flows (full environment only): the `tools/release` tests, which need the pinned zlib-ng Python 3.12 venv
  (`docs/RELEASING.md`, "Building locally"); `workflow-manager verify .`, which needs the installed release's assets in the release
  cache; and the plan's reaper orphan check (`reaper.py` is not in this repository).
- The plan's section 0 table (the six existing retention classes under each mutation) was measured at CP1 and was not re-measured
  in this preparation. F4 is the check that the new pins themselves fail only under their own mutations.
- Out of scope: any behaviour, the documents, the retention pages, the Manager and the Controller. Publishing 2.29.7 and the Manager
  pins follow the merge.

### Next steps

- Testing clean: `/accept-milestone` is the only acceptance command. It requires every checkpoint of this item to be `COMPLETE`;
  CP1 and CP2 are, so no checkpoint is outstanding.
- Findings: write them to `.ai-review/retention-test-pins/feedback/FUNCTIONAL_REVIEW.md`. `/apply-functional-review` routes each one:
  the bounded branch for a same-scope fix, the broad branch (a `retention-test-pins-remediation-<n>` child) for new or wider scope.
