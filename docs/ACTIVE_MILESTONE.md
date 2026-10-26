# Active Milestone

## Milestone

**In progress.** W28: `retention-archive` (`process`, governing version `2.2`), branch `milestone/retention-archive`,
roadmap row 27c (RodrigoFAbreu/workflow#84, step 3, and #113 items 3 and 4). Plan:
`docs/ai-workflow/RETENTION_ARCHIVE_PLAN.md` (revision 7, approved by gate policy). The goal is Workflow 2.21.0, a
`feat:` minor that adds the non-destructive archive creation, `scripts/workflow_retention.py archive <id>`: a dry run by
default, and with `--apply` it packs a finished item's untracked review folder into a verified `.tar.zst` outside the
repository, indexes it and makes it durable. It never removes, renames or modifies anything in the folder or the
repository. The removal (row 27d), the user-only command (27e) and the prune (27f) are not part of this item. The
previous milestone, W27 `retention-report`, is accepted (Workflow 2.20.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The archive engine, its tests and the documents | **complete** (verified in a scratch clone, see below) |
| CP2 | Release 2.21.0 | **complete** (verified in a stock `stage-conformance` fixture, see below) |

## Verified state

- CP1: `payload/scripts/workflow_retention.py` (`archive_item`, the `archive` subcommand, the `zstd` seam, and the report's
  four checks: a repository `.`/`..`, a symlinked per-repository directory, the ids `runtime`/`archive`, and the
  traversal anchored on a `.ai-review` descriptor), the `RetentionArchive` tests in
  `workflow_state_completion_obligations_test.py` (208 -> 240 counting the report's), `docs/RETENTION.md` (the section
  "The archive command" and the re-targeted row references) and `docs/exit-codes.md`. `git diff f1c78ef --stat -- payload`
  lists the script and its test file only. Each mutation the plan lists fails at least one test in a scratch copy (the
  results are in the implementation bundle's `TEST_RESULTS.md`).
- Verified in a disposable clone (D-Staging): the nine suites from the staged fixture, `tools/docs` (34),
  `check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng), and the new and the whole obligations tests under
  the orphan wrapper (no orphan beyond Git's own detached maintenance).

- CP2: `manifest.json` 2.21.0 (counts unchanged at 81, 6 and `distribution` 55; `sha256`, `size` and a `retention-archive
  (workflow-2.21.0)` sentence for the five changed records; the posture; `conformance.suites` measured), `WORKFLOW_RELEASE`
  2.21.0 with its two pinned assertions, `ORCHESTRATION_PROTOCOL.md`, the 2.21.0 row of `docs/release-history.md`, the
  "Last checked with" lines of the three pages, and the 2.21.0 release class of `tools/release/release_test.py`.

## Functional review checklist

**Scope.** The archive creation only: `scripts/workflow_retention.py archive <id>`, a dry run by default, and with
`--apply` a packed, verified, indexed `.tar.zst` outside the repository. The folder is never removed or changed. The
removal (27d), the user-only command (27e) and the prune (27f) are not in this item, so nothing here tests them.
Plan section 7 (`docs/ai-workflow/RETENTION_ARCHIVE_PLAN.md`) is the source of flows f1 to f11 below.

**Findings** go to `.ai-review/retention-archive/feedback/FUNCTIONAL_REVIEW.md`.

### Setup

- Work on `milestone/retention-archive` at the checklist evidence commit named in the gate report, with a clean tree.
- The archive subcommand is in `payload/` only. This repository's own installation is still 2.20.0, so
  `python3 scripts/workflow_retention.py archive` does not exist here. Stage the candidate and run from the fixture:
  `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then use
  `$TMPDIR/fixture/scripts`.
- `zstd` must be on `PATH` (`/usr/bin/zstd` here). Without it, both modes refuse `zstd_missing`.
- Set `TMPDIR` to a scratch directory outside the checkout. **Never run `--apply` against the real repository.**
- Use `python3 -B` (no bytecode in the fixture) and `python3 -I` for the `archive` runs.
- Environment, not product defects, if absent: f5 needs the zlib-ng interpreter for `tools/release`, and f3 needs the
  Manager's orphan wrapper (`~/Workspace/workflow-manager/tests/parallel/reaper.py`).

### Test data (f6 to f11)

A scratch repository under `$TMPDIR`: `git init`, `git remote add origin https://github.com/acme/widgets.git`, and
a hand-built `docs/ai-workflow/WORKFLOW_STATE.json` with:

- five finished items (`MILESTONE_COMPLETE`, each with a `reviewed_implementation_head`),
- one open item (a non-terminal phase, for example `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`), and
- one `kept_recent` item (merged, among the three newest).

Each item gets a `.ai-review/<id>/` folder with files, a nested directory and a symlink to a file inside the folder.

The forge is a fake, so no network and no `gh`. Call
`main(["archive", "<id>", "--repo-root", <scratch>, "--archive-root", <scratch-archive>] [--apply], run=<fake>, resolve=<fake>)`
from the fixture's scripts. `run(argv, timeout)` returns `merged` for every anchor except the open item's (never
queried), and `resolve` returns `acme/widgets`. The fake in `_RR` in
`payload/scripts/workflow_state_completion_obligations_test.py` (around line 3703) is the reference.

### Flows and expected results

- **f1, the new tests.** In the fixture's scripts:
  `python3 -B -m unittest -v workflow_state_completion_obligations_test.RetentionArchive workflow_state_completion_obligations_test.RetentionReport`.
  Expected: all pass (47 at the verified implementation head).
- **f2, the mutations.** On a scratch copy of the fixture, apply each mutation named in the implementation bundle's
  `TEST_RESULTS.md` one at a time. Expected: each makes at least one test fail, and the unmutated control passes.
- **f3, the orphan wrapper.** Run the obligations chunk under the orphan wrapper. Expected: no orphan beyond Git's
  own detached maintenance.
- **f4, the nine suites.** Run every entry of `manifest.json` `manager.conformance.suites` from the fixture. Expected:
  all OK.
- **f5, the checkout.** `python -m unittest discover -s tools/release -p '*_test.py'` (zlib-ng),
  `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, and
  `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`. Expected: all pass.
- **f6, dry run is the default.** `archive <finished-id>` with no `--apply`. Expected: it lists every entry and the
  target and exits 0. The repository and the archive root are byte-identical before and after
  (`find ... -type f -print0 | sort -z | xargs -0 sha256sum` and `git status --porcelain --ignored`).
- **f7, apply touches nothing else.** `archive <finished-id> --apply`. Expected: `zstd -dc <archive> | tar -tvf -` lists
  the folder's files, `index.jsonl` gains exactly one line, and the folder is still present and byte-identical (hashes,
  `stat` mtime and ctime). The other folders, the tracked files and the state are unchanged. The report afterwards
  lists the item as finished with its archive present.
- **f8, a failure mid-way.** Put a stand-in `zstd` first on `PATH` that exits 1 while packing, then one that truncates
  its output. Expected: exit 2 with `pack_failed`, then `verify_failed`. The folder is byte-identical, and the archive
  directory has no temporary file, no archive and no directory this run created.
- **f9, refusals write nothing.** Expected, each with exit 2 and no write: an open item (`not_finished:open_phase`), the
  `kept_recent` item, an unknown id, `runtime` (`invalid_id`), an already archived item (`already_archived`, its
  archive's mtime unchanged, the folder in place), a leftover temporary (`partial_present`), and a repository whose
  per-repository archive directory is a symlink (`archive_dir_unsafe`).
- **f10, the checkout's diff.** `git diff f1c78ef --stat -- payload` lists exactly five files: `workflow_retention.py`,
  its test file, `workflow_protocol.py` (the release constant), `workflow_protocol_test.py` and
  `docs/ORCHESTRATION_PROTOCOL.md`. The 2.21.0 history row, the manifest and `docs/RETENTION.md` agree on the version,
  and the 2.20.0 and older rows are unchanged.
- **f11, unsafe paths.** One setup at a time, each with exit 2 (the report exits 0) and the outside tree, the
  repository and the archive root byte-identical afterwards, in both dry run and `--apply`:
  - `.ai-review/` is a symlink to an outside directory: `path_unsafe`, and `report` lists nothing from it;
  - `--archive-root` inside the checkout: `archive_inside_repository`;
  - `index.jsonl` is a symlink to an outside JSONL file: `index_unsafe`, and the outside file is unchanged;
  - a tracked gitlink at `.ai-review/<id>`: `tracked_files`.

### Known limitations (out of scope)

- The folder is kept after `--apply`, by design. Removing it is row 27d.
- The user-only command (27e) and the prune (27f) do not exist yet.
- The archive subcommand is not in this repository's installation until the 2.21.0 release is installed. The release
  follows the merge of this milestone's pull request.
- The flows use a fake forge, so a real `gh` query is not exercised.
- The default archive root is `~/.local/share/workflow-archive`. The flows always pass `--archive-root` to a scratch
  directory.
- Automated verification was run at implementation head `efaddc7`, and nothing in the tree changed since except
  `docs/ai-workflow/WORKFLOW_STATE.json`.

## Next action

Test the checklist above against the checklist evidence commit. Findings go to
`.ai-review/retention-archive/feedback/FUNCTIONAL_REVIEW.md`. Then run `/apply-functional-review retention-archive` for
any findings, or `/accept-milestone` once testing is clean. The Workflow 2.21.0 release follows the merge of this
milestone's pull request.
