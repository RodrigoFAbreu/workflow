# Active Milestone

## Milestone

**In progress.** W53: `test-hardening-owner-points` (`process`, governing version `2.2`), branch
`milestone/test-hardening-owner-points`, roadmap row 46 (RodrigoFAbreu/workflow#170 point 1, #116 point 3, #158 point 3). The
plan is `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_PLAN.md` (revision 2, approved by gate policy). Docs only: no release.

## Goal

Settle the three points that needed an owner decision, with evidence: a recorded run of `TestPlainCommandMalformedState`
under the Manager's reaper, the ordering of the A12 and A15 race hooks, and the 2.27.0 posture sentence. Nothing under
`payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changes.

## Outcome

- CP1: the evidence is in `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`. #170 point 1: keep the test, the reaper
  run is `OK` with only Git's own helpers left (`[git]` and its detached maintenance). #116 point 3: already fixed, shown by
  three failure-only mutations of the retention engine. #158 point 3: keep, the sentence is true and every release carries it.
- One comment per issue is posted from the evidence file's last section; no issue is closed.

## Next action

The item is at the functional-review gate (`AWAITING_FUNCTIONAL_REVIEW`). Run the checklist below by hand, then place any
findings in `.ai-review/test-hardening-owner-points/feedback/FUNCTIONAL_REVIEW.md`. Once testing is clean, `/accept-milestone`
is the only acceptance command.

## Functional review checklist

**Scope.** Docs only. `git diff --exit-code f9d63f4246041afc21ff35d85bc2e994fc6d66f8 -- payload tools fixtures templates manifest.json`
is empty (flow 7). The review checks that the evidence file and this record say what the evidence shows. Automated
verification: CP1 re-ran the section 0 checks on the branch, and nothing in the product tree changed since the implementation
review (only `docs/ai-workflow/WORKFLOW_STATE.json` moved).

### Setup

Run from the product clone root, on the branch at the evidence commit reported to you. `TMPDIR` is a writable scratch
directory outside the clone.

1. Save the code block of `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_PLAN.md`, section 5, as `$TMPDIR/flows.sh`.
2. `export REPO="$PWD" B=f9d63f4246041afc21ff35d85bc2e994fc6d66f8 E=docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`
3. `rm -rf "$TMPDIR/cand" && mkdir -p "$TMPDIR/cand" && git -C "$REPO" archive HEAD docs payload manifest.json | tar -x -C "$TMPDIR/cand"`
4. Run a flow with `sh "$TMPDIR/flows.sh" <n>`.

Flows 1 to 9 run offline in a sandbox: no network, no `gh`, no `claude`, `codex` or `ssh`, no socket. They write only under
`$TMPDIR`. Flows 10 to 13 need the full environment (below).

### Test data

Nothing to seed. Each flow reads the committed tree (`$TMPDIR/cand`), the base commit `f9d63f4`, or git objects.

### Flows 1 to 9 (offline): expected results

| Flow | Run | Expected output |
| --- | --- | --- |
| 1 | `sh "$TMPDIR/flows.sh" 1` | `Point 1 (#170): 1`, `Point 3 (#116): 1`, `Point 3 (#158): 1`, `Issue comments: 1`; then a `fatal:` line saying the evidence file is not in the base |
| 2 | `2` | `status0`, `tests10`, the orphan kinds `` `[git]` `` and `` `git maintenance run --auto --quiet --detach` ``, then `no-third-kind` |
| 3 | `3` | `already-fixed`, then five lines of `1` (two hook lines, three engine lines) |
| 4 | `4` | seven lines `<tag> 1` (v2.25.6, v2.25.7, v2.26.0, v2.27.0, v2.28.0, v2.29.0, v2.29.5), then `83 []` |
| 5 | `5` | `0`, then `v2.27.0` |
| 6 | `6` | `74:\| 45`, `75:\| 46`, `76:\| 27` in file order, then `row45-same`, then row 46's status `Current` |
| 7 | `7` | exactly these eight names: `docs/ACTIVE_MILESTONE.md`, `docs/ROADMAP.md`, `docs/ai-workflow/WORKFLOW_STATE.json`, `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_PLAN.md`, `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`, and the three `test-hardening-owner-points` JSON files under `docs/ai-workflow/registry/` and `docs/ai-workflow/requirements/`; then `release source and installation: exit 0` |
| 8 | `8` | `m1 1 0`, `m2 1 0`, `m3 1 0` (each old string occurs once in the base file, its replacement nowhere) |
| 9 | `9` | `exit 0`; then a `docs/gates.md:` line naming the missing `Last checked with` stamp, then `exit 1`; then `status lines: before N after N` with equal N (0 in a clean clone) |

### Flows 10 to 13 (full environment only, not the sandbox)

These need the Manager checkout at `/home/rodrigo/Workspace/workflow-manager`, the zlib-ng venv, and `zstd`, so they are
not runnable in the sandbox.

- **10 (mutations).** Stage the fixture with `tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`.
  Unmutated, the A12 and A15 tests pass (`Ran 2 tests`, `OK`). With m1, the A12 test fails (`None != 40`). With m2, the
  combined run shows five A15 failures, the first `symlink to an outside file` (`0 != 2`). With m3, three, the first the hard link.
- **11 (reaper).** From the fixture's `scripts/`, the reaper run of `TestPlainCommandMalformedState` gives `Ran 10 tests`,
  `OK`, `chunk_status` 0, and orphans only `[git]` and `git maintenance run --auto --quiet --detach`, all `exited`.
- **12 (nine suites).** The suites loop of `docs/RELEASING.md` from the staged fixture passes all nine.
- **13 (zlib-ng and docs).** The `tools/release` and `tools/docs` unit tests, `tools/docs/check_docs.py`, and
  `check-manager-block` all pass.

### Checks only you can make

- **Issue comments.** `gh` is not available in the sandbox, so the three comments on #170, #116 and #158 cannot be checked
  offline. Their text is in the evidence file's last section. Confirm on GitHub that each was posted. The evidence file
  records no comment URLs, and no issue is closed by this item.

### Known limits

- Docs only: no product behaviour, no release (the manifest stays at 2.29.5), and #170 point 2 stays open.
- The git-helper count in the reaper report varies from run to run. Flow 2 pins the kinds, not the count.
- Roadmap row 46 reads `Current` until acceptance.

### If testing finds something

Write the finding to `.ai-review/test-hardening-owner-points/feedback/FUNCTIONAL_REVIEW.md` and run `/apply-functional-review`.
A same-scope fix takes its bounded branch. New or wider scope takes its broad branch, a `test-hardening-owner-points-remediation-<n>`
child item.
