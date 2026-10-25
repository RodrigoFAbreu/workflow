# W27: Workflow 2.20.0 — the retention report (Revision 2)

- **Work item:** `retention-report` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator. It is row 27b of `docs/ROADMAP.md` (status `Current` from
  this plan, `Done` at acceptance). The roadmap rows were split by this item: 27b is the report, 27c the
  user-only archive command, 27d the user-only prune.
- **Issue:** RodrigoFAbreu/workflow#84, step 2 (the rule is `docs/RETENTION.md`, step 1, already merged).
- **Branch:** `milestone/retention-report`
- **Base commit:** `e026781` (main after #112: the release source is Workflow 2.19.2, this repository's own
  installation is the published 2.19.2, automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog
  file declared, so the prose roadmap applies)
- **Plan revision:** 2 (revision 1 plus the three important findings and the optional one of the manual external
  review, `EPR-001` to `EPR-004`, answered in section 8). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.20.0, a `feat:` minor, that adds **one read-only report**: which work items of a repository are
finished by the rule of `docs/RETENTION.md`, how large each one's untracked `.ai-review/<id>/` folder is, and
whether an archive of it exists outside the repository and is older than the time to live (the TTL). The report
is the first of three steps the owner decided on 2026-10-25 (option B): the archive command (row 27c) and the
prune (row 27d) are **not** part of this item.

```
python3 scripts/workflow_retention.py report [--json] [--archive-root DIR] [--ttl-days N] [--repo-root DIR]
```

It is called by the Manager's `status`/`doctor` report and by the Controller (JSON), and read by a person (text).

### The invariants (one sentence each)

- **I1. It writes nothing.** No archive, no removal, no state write, no stored fact, no bytecode file: the
  working tree, `.git` content other than what a read-only Git command refreshes, and the archive directory are
  byte-identical before and after a run, **on every path of the run, a failed forge query and a refusal included**.
  The no-bytecode part is a property of the two supported invocation forms of D-Writes, not of the module alone.
- **I2. A failed or empty query means not finished.** An item is reported finished only when a fresh query
  returned a pull request whose state is `merged`; every other outcome puts it in `not_finished` with a reason.
- **I3. An open item is never listed as finished,** and is never queried: a phase other than
  `MILESTONE_COMPLETE`, or a parent or child not at `MILESTONE_COMPLETE`, ends the decision before the forge.

### Hard limits (the owner's sizing rule)

- **One mechanism, no protocol or state change.** One new script. No change to `workflow_protocol.py` beyond the
  release constant (a new protocol operation would change the protocol), `workflow_state.py`,
  `workflow_forge.py`, `workflow_gate_policy.py`, `WORKFLOW_STATE.json`, `WORKFLOW_CONFIG.json`, a phase, a
  trailer or a command file. **If the work needs more, STOP and split it into a roadmap row.** CP1 re-checks
  this: `git diff e026781 --stat -- payload` lists only the script and its test file.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`, the managed documents of
  `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks of `CLAUDE.md` and `.gitignore`, and
  `.github/workflows/workflow-conformance.yml`. The change goes to `payload/`; release bookkeeping to
  `manifest.json`, `docs/` user documents and `tools/release/`.
- **Size:** two checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** the new tests; the nine payload suites from a staged fixture; the new tests
  under the Manager's orphan wrapper; the `tools/release` tests (zlib-ng environment); the `tools/docs` tests and
  checker; `check-manager-block` with `--manager-releases`; `workflow-manager verify .` clean; the functional
  flow that proves nothing was written. Every command form is copied from `docs/RELEASING.md`, "Verification
  commands".
- **Aids (never a stop):** the per-record reading of the manifest rationales against `git diff` (CP2).

## 2. Facts this plan relies on (re-checked against `e026781`)

- **The rule** is `docs/RETENTION.md`, "Which items the rule applies to": a work item is finished when its phase
  and the phase of its parent and of every child are `MILESTONE_COMPLETE`, a fresh pull-request fact says
  `merged`, and it is not one of the 3 most recent such items by `last_transition`. The stored
  `gate_evidence.pr` is stale (it says `open` for every finished item measured), so the report ignores it.
- **The fresh fact** is `workflow_forge.query_forge_pr_facts(repo_root, queried_commit)`: a fixed `gh pr list`
  query that writes nothing and returns `facts.state` in `open`, `closed`, `merged` or `none`, raising a
  `ForgeError` subclass (each with a code) when `gh` is unavailable or the answer is undecidable. It has a test
  seam `run`/`resolve`. The commit that `/apply-pr-review` queries is the item's anchor
  (`workflow_gate_policy.anchor_of`): `technical_approval.reviewed_content_commit` **only when
  `technical_approval.approved_review_content_id` is also present**, else `reviewed_implementation_head`. The
  report applies the same two-field condition, so the queried commit always equals the one `/apply-pr-review`
  queries, and does not call `anchor_of` itself, because `anchor_of`
  computes a review identity (a heavy read) when there is no technical approval, which the report does not need.
- **Scripts are standalone.** `workflow_backlog.py` is the precedent: a script under `payload/scripts/` with
  `# state_writer: false`, not a protocol operation, tested in an existing suite
  (`workflow_state_completion_obligations_test.py` holds the backlog tests), with a row in `docs/exit-codes.md`.
  A new test file would add a tenth suite to `manager.conformance.suites`, which the Manager reads: not done.
- **`.ai-review/<id>/`** is untracked and per worktree. The report reads the folder of the worktree it runs in
  (the repository root, by default the parent of the script's directory).
- **The archive layout** is the owner's: `~/.local/share/workflow-archive/<repo>/<id>.tar.zst`, `<repo>` the
  repository name (the part after the slash of `origin`'s `owner/name`). Row 27c writes it; the report only reads.
- **Python 3.14** is the runtime here; the script is stdlib-only and runs under `python3 -I`.

## 3. Design decisions

### D-Surface: a script, not a `verify` check

Row 27b first said "`verify` reports the clutter". `workflow_protocol.py`'s `verify` result is part of the
Orchestration Protocol envelope (version 1.5); adding a section changes the protocol and needs the Manager to
learn it. A standalone script changes neither. The Manager's `status`/`doctor` and the Controller run
`python3 scripts/workflow_retention.py report --json` and read the JSON (Manager row 17 does the wiring, outside
this item). The same module exposes `build_report(...)` for a caller that imports it, under the bytecode
condition of D-Writes (the caller suppresses bytecode before the import).

### D-Finished: the decision, in order, cheapest first

For every `work_items` entry of `docs/ai-workflow/WORKFLOW_STATE.json` (read as JSON, never written, no lock):

1. id not matching `^[a-z0-9][a-z0-9_-]{0,63}$` → `not_finished: invalid_id` (an id is part of two paths).
2. phase not `MILESTONE_COMPLETE` → `open_phase`.
3. `parent_work_item_id` names an entry not at `MILESTONE_COMPLETE` (or absent), or any entry whose
   `parent_work_item_id` is this id is not at `MILESTONE_COMPLETE` → `family_open`.
4. no anchor commit → `no_anchor`. The anchor is `technical_approval.reviewed_content_commit` when
   `technical_approval.approved_review_content_id` is also present, else `reviewed_implementation_head`
   (`anchor_of`'s own condition; a `reviewed_content_commit` without the identity is not used).
5. the fresh query: `facts.state` `merged` → merged; `none` → `no_pull_request`; `open` or `closed` →
   `pr_not_merged:<state>`; any exception → `query_failed:<code>` (the `ForgeError` code, else `unexpected`).
   Items of step 5 are queried newest `last_transition` first, one at a time, each under the module's own
   30-second timeout; nothing is cached or stored.
6. the merged items sorted by `last_transition` descending (ties by id): the first 3 are `kept_recent`, the
   rest `finished`.

### D-Report: what is measured for each listed item

- **Review folder** `.ai-review/<id>/`: `present` only when it is a real directory (a symlink, a file or nothing
  is `present: false`); `files` and `bytes` are the regular files below it counted without following a symlink;
  `tracked_files` is the number of paths under it that `git ls-files` lists (one call for the whole
  `.ai-review/`), so row 27c can refuse a tracked file. Reported for `finished` and `kept_recent` items.
- **Archive** `<archive-root>/<repo>/<id>.tar.zst` for a `finished` item: `present` only for a regular file (not
  a symlink); `bytes`, `modified` (UTC, from the file's mtime) and `age_days` (whole days at `generated_at`),
  which are JSON `null` (never omitted, never `0`) when `present` is false, with `prunable` then `false`;
  `prunable` is true when `age_days` (whole days, rounded down) is strictly greater than the TTL, so an archive
  30 days and 23 hours old is not prunable and one 31 days and 1 second old is.
- **`archives`:** every `*.tar.zst` regular file directly in `<archive-root>/<repo>/`, with the same fields and
  `item` = `finished`, `recent`, `open` (the stem names a `not_finished` item, for example one reopened after it
  was archived: row 27d must not prune it on the report's say-so) or `other` (the stem names no work item of the
  state). This is the list row 27d prunes.
- **The TTL** is `--ttl-days N` (default `30`, an integer from 1 to 3650). It is a setting of the caller; the
  report writes none. The recent-items count (3) is a constant of the rule, not an option.

### D-Output: the JSON and the text

```
{"schema_version": 1, "kind": "retention-report", "generated_at": "<UTC ISO>", "repository": "<owner>/<name>",
 "archive_dir": "<path>", "ttl_days": 30, "keep_recent": 3,
 "finished":    [{"work_item_id", "last_transition", "pull_request": {"number", "url"},
                  "review_folder": {"present", "files", "bytes", "tracked_files"},
                  "archive": {"present", "bytes", "modified", "age_days", "prunable"}}],
 "kept_recent": [{"work_item_id", "last_transition", "pull_request", "review_folder"}],
 "not_finished":[{"work_item_id", "phase", "reason"}],
 "archives":    [{"name", "work_item_id", "bytes", "modified", "age_days", "prunable", "item"}],
 "totals": {"finished", "finished_folder_bytes", "archives", "prunable"}}
```

Keys are sorted, one object, newline-terminated. **Order and absence are fixed** so the output is a pure function
of the state, the folders, the archives and `generated_at` (the caller's `now`; `build_report` takes it, the CLI
reads the clock once): `finished` and `kept_recent` by `last_transition` descending then `work_item_id`;
`not_finished` by `work_item_id`; `archives` by `name`; no list depends on directory or `work_items` order. An
absent review folder is `{"present": false, "files": 0, "bytes": 0, "tracked_files": <count git lists, 0 if none>}`;
`pull_request` is `{"number": <int>, "url": <string>}`, each `null` when the fact lacks it. The text form is a header (repository, archive directory, TTL),
one line per finished item (id, folder size, archive state), the kept recent ids, the count of not-finished items
by reason, and the prunable archives. A refusal prints `error: <code>: <message>` and `next step: ...` on
standard error. Exit codes: **0** the report was printed (also when some items could not be queried: they are in
`not_finished`); **2** a refusal or usage error with a code: `state_missing`, `state_invalid`,
`repository_unknown` (no GitHub `origin`), `usage`. The row goes into `docs/exit-codes.md`.

### D-Writes: nothing is written, and the tests prove it

**Bytecode.** A module cannot keep Python from caching its own bytecode by an assignment it makes while loading:
the cache file is written when the import compiles the module, before that assignment runs (reproduced by the
manual external review under Python 3.14 with `-I`). I1's no-bytecode guarantee is therefore stated for two
invocation forms, not for the module:

1. **The CLI form, supported for the Manager and the Controller:** `python3 -I scripts/workflow_retention.py report
   ...`. The script runs as `__main__`, whose bytecode Python never caches. It sets `sys.dont_write_bytecode = True`
   and inserts its own directory into `sys.path` (as `payload/scripts/workflow_protocol.py:39` does, because
   `python3 -I` leaves it off), both **before** the sibling import (`workflow_forge`), so no sibling's bytecode is
   written either.
2. **The import form, for `build_report`:** the caller sets `sys.dont_write_bytecode = True` (or runs with `-B`, or
   with `PYTHONDONTWRITEBYTECODE`) **before** the first import of `workflow_retention`. The module docstring and
   `docs/RETENTION.md` say so, and say that an import without it may leave `__pycache__` in the scripts directory,
   by Python's doing and not by a run of the report.

The script is stdlib-only and runs only read-only Git commands: its own `git ls-files`, and those of
`workflow_forge` (`git remote get-url origin` and `git worktree list --porcelain`, through `resolve_gh` and
`_worktree_roots`, once per queried item). **No-write proof (T7, T9):** the tests hash every file of the scratch
repository and of the archive directory before and after a run (CLI and `build_report`) and compare them, for the
successful run **and for every failure path**: each query outcome of T4 (an unavailable `gh`, an undecidable
answer, an unexpected exception, `none`, `closed`), a missing anchor, and each refusal (`state_missing`,
`state_invalid`, `repository_unknown`, `usage`). T9 proves the bytecode contract from fresh interpreters.

### D-Tests: in `workflow_state_completion_obligations_test.py`, class `RetentionReport`

A scratch Git repository with a hand-built state file and `main(argv, run=..., resolve=...)` with the forge seam
(no network, no `gh`). Cases: (T1) merged → finished, open phase → `open_phase`, a stored `gate_evidence.pr`
saying `merged` with a fresh `open` is not finished, a stored `open` with a fresh `merged` is; (T2) parent or
child not complete → `family_open`; (T3) the 3 newest merged are `kept_recent`, ties by id; (T4) each query
outcome (`ForgeUnavailableError`, `ForgeUndecidableError`, an unexpected exception, `none`, `closed`) and a
missing anchor → not finished with its reason, and the exception does not stop the others; an open item is never
queried (the seam records its calls); (T5) folder sizes, a symlinked folder and a symlink inside it, tracked
files counted; (T6) archive absent, present, 30 days exactly and 30 days 23 hours (not prunable), 31 days (prunable), a symlink
ignored, an `other` archive listed; (T7) nothing written, by the snapshot comparison of D-Writes on the successful run and, as separate cases, on
every failure path it lists, with the assertion that the snapshots are **non-trivial** (the scratch repository
and archive directory hold files, so an empty comparison cannot pass); (T8) the CLI: JSON parses with the keys above, the text
form names each section, each refusal code and exit code, `--ttl-days 0` and `abc` refused, a real subprocess run
with `python3 -I` on a repository with no `origin` exits 2 with `repository_unknown`; (T9) the bytecode contract,
from fresh interpreters, **without `-B`** on the child command line (the child environment drops
`PYTHONDONTWRITEBYTECODE`, so the harness's own `-B` is not inherited): a copy of the scripts directory with no
`__pycache__` is made in a scratch directory; (a) `python3 -I <copy>/workflow_retention.py report` on a repository
with no `origin` leaves no `__pycache__` anywhere in the copy, the repository or the archive directory; (b) a
`python3 -I -c` that sets `sys.dont_write_bytecode = True`, inserts the copy on `sys.path`, imports
`workflow_retention` and runs `build_report` with a seam leaves none either; (c) the same import **without** the
assignment does create one (a control: the check can see bytecode); (d) the tree is listed before module
loading and compared after. (T10) determinism: the same state with `work_items` reordered, the archive directory
filled in another order and a fixed `now` gives byte-identical JSON, and an absent archive and an absent folder
carry the documented `null`/`0` values. The tests start no process except the `python3` children of T8 and T9 and
Git.

### D-Orphan: no process left behind

The new tests run under the Manager's wrapper (`tests/parallel/reaper.py` of the Manager checkout; the form is
in the evidence file of the previous release `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md`) from the staged
fixture, then the whole `workflow_state_completion_obligations_test.py` chunk; the reports must list no orphan
beyond Git's own detached maintenance.

### D-Docs: where it is described

`docs/RETENTION.md` gets a section "The report" (the command, the JSON above, the exit codes, the cost: one
forge query per item at `MILESTONE_COMPLETE`, so run it between work items, and the statement that it writes
nothing). **Every reference to a roadmap row in it is re-targeted** (line numbers at `e026781`), because the
split gave the old rows' duties to no row:

| Where | Today | After CP1 |
| --- | --- | --- |
| 15 | "Steps 2 to 4 (the `verify` report, the command that applies the rule, and the link check) are later roadmap rows" | step 2 is the retention report (row 27b, this release); the archive command (27c) and the prune (27d) follow; the tracked-file command and the link check are "a later row, not yet scheduled" |
| 47 | whether the fresh fact is stored "is for row 27c's plan" | "is for the plan of a later row, not yet scheduled" (none of 27b to 27d stores it) |
| 70, 226 | `check_docs` reading the archive index "(row 27d)" | "(a later row, not yet scheduled)": the historical-links row was dropped |
| 159-161 | archival example `tar -czf <dir>/<repository>-<id>.tar.gz .ai-review/<id>` | the owner's layout: `~/.local/share/workflow-archive/<repo>/<id>.tar.zst`, the file the report reads (the example's `.tar.gz` would never be seen as `finished.archive`, in `archives` or as prunable); row 27c writes it |
| 265-266 | "Rows 27b (`verify` reports the clutter), 27c (a command applies the rule) and 27d (historical links keep working) must guarantee" | "The tooling that applies the rule to tracked files and links, a later row not yet scheduled, must guarantee 1 to 6"; the review-folder archive command (row 27c) keeps 1 (never touch an open item, here by the report's finished set), the last sentence of 4 and 5 |
| 297 | "for row 27c's plan to decide" | row 27c is user-only by its roadmap row; for the tracked-file command, "for the plan of that later row to decide" |
| 308-311 | guarantee 7 gives row 27b a `verify` check and a limit | guarantee 7 moves to "a later row, not yet scheduled"; the section says that the report of row 27b does **not** implement it: it reports review-folder sizes and archives only, warns about nothing and chooses no limit |

`docs/exit-codes.md` gets the script's rows. No page names an internal milestone id (the pages
say "the retention report"), and no list of governing versions is written in a managed document.

### D-Release: 2.20.0, `feat:`

`manifest.json` `workflow_version` 2.20.0. One record is **added**: `scripts/workflow_retention.py`
(`distribution`, rule `^scripts/workflow_retention\.py$`), so the counts become 81 artifacts, 6 templates,
`distribution` 55. Records that move: `payload/scripts/workflow_state_completion_obligations_test.py` (the new
tests), `payload/scripts/workflow_protocol.py` (`WORKFLOW_RELEASE` 2.20.0 and nothing else),
`payload/scripts/workflow_protocol_test.py` (its two pinned assertions) and
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (tested releases, envelope example, protocol note; the
protocol version stays 1.5). Each carries a `retention-report (workflow-2.20.0)` sentence true of that file.
`manager.conformance.suites` are **measured, never typed**. `min_manager_version` stays 1.13.0, equal to the CI
pin in `tools/release/manager-pin.json`. The detector vocabulary is untouched (`signals` stays empty).

**Downgrade posture.** 2.20.0 writes nothing an older release reads: no state key, phase, trailer, commit shape,
guard-body key, protocol field or refusal class changes, and the script is not called by any Workflow command.
`workflow-manager update` back to 2.19.2 (minimum Manager 1.13.0) removes `scripts/workflow_retention.py`; a
Manager or Controller report that calls it then finds no script and must treat that as "no retention report",
not as an error of the repository. Nothing the script touched needs undoing, because it touched nothing.

**Documents.** `docs/release-history.md` gets the 2.20.0 row (references #84 step 2, names the script, says it
writes nothing and changes no behaviour, gives the way back) and its "Last checked with" line;
`docs/RETENTION.md` and `docs/exit-codes.md` get "Last checked with: Workflow 2.20.0".
`tools/release/release_test.py`: a 2.20.0 release class (version, constant, counts (81, 6), the added record, each
changed record's sentence and no other record carrying it, the posture and history needles); the 2.19.2 class
keeps what stays true of it and no longer pins the current version, constant, counts or posture.
`docs/RELEASING.md` changes only if a count it states changes.

### D-Staging: scratch staging for CP1

CP1 adds a shipped file and changes a shipped test, whose records `manifest.json` moves only at CP2, so stock
`stage-conformance` cannot stage CP1's own tree. CP1 verifies in a disposable clone under `$TMPDIR`: a scratch
script adds the new record, recomputes `sha256` and `size` of every `artifacts` record whose file differs from its
record, measures and rewrites `manager.conformance.suites` by the discovery `release.py manager-block
--release-dir <scratch> --write` uses, commits it in the clone, and runs the "Verification commands" blocks from
there (the procedure of `docs/milestones/completed/CHECKPOINT_START_COMMAND_PLAN.md`). No rationale is touched in
the scratch, and the report says the staging was adjusted.

**The `tools/release` tests in the CP1 scratch, one declared patch.** The new record moves the counts to
(81, 6) and `distribution` to 55, and the only release test that pins the old counts is
`CommandWordingReleaseTest.test_the_release_names_2_19_2_and_adds_no_record` (`tools/release/release_test.py:2917-2918`,
`(80, 6)` and `54`); the same method's consistency assertions (`counts` equal to the measured numbers) need the
new counts while its pins need the old, so it cannot pass in a scratch that adds the record. CP2 rewrites that
class (D-Release). In the CP1 scratch **only**, a scratch patch changes exactly those two pinned numbers to
`(81, 6)` and `55`; the patch is applied by the scratch script, never to the checkout, its diff is pasted in
`TEST_RESULTS.md`, and **every other `tools/release` test runs unmodified and must pass**. Any other failure is
a stop for the plan, not something the scratch patches around, and no test is skipped, deselected or marked
expected-to-fail. The CP2 stock `stage-conformance` run is the real proof of that class.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Two choices are made here and may be reversed:

- **The TTL is a flag with a default, not a stored setting.** Storing it would add a key to
  `WORKFLOW_CONFIG.json`, a state change this item must not make. The Manager and the Controller hold their own
  setting and pass `--ttl-days`.
- **The age of an archive is its file's mtime.** The index line with the date belongs to row 27c; the report does
  not read an index that does not exist yet. Row 27c must therefore not touch an archive's mtime after writing it.

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The report script, its tests and the documents | - | 3 | 1 |
| CP2 | Release 2.20.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The report script, its tests and the documents

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`, `docs/exit-codes.md`.

- **The script** (D-Surface, D-Finished, D-Report, D-Output, D-Writes): `# state_writer: false`,
  stdlib-only plus `workflow_forge`; `build_report(repo_root, *, archive_root, ttl_days, now, run=None,
  resolve=None)` and `main(argv, *, run=None, resolve=None)`; the `report` subcommand with `--json`,
  `--archive-root`, `--ttl-days`, `--repo-root`. **Done:** every case of D-Tests passes.
- **The tests** (D-Tests): written first; each case T1 to T8 is checked by a one-line mutation of the script in a
  scratch copy (open items queried, the stored fact trusted, an exception aborting the run, `>=` for `>`, a
  symlink followed, a write to the archive directory, **a write that happens only in the query-failure handler**,
  **a write only on a refusal path**, **the `sys.dont_write_bytecode` assignment moved after the sibling import**,
  `archives` left in directory order) and fails there; the mutations and their results are listed
  in the implementation bundle's `TEST_RESULTS.md`.
- **The documents** (D-Docs): the section "The report" and the re-targeted row references of `docs/RETENTION.md`
  (the table of D-Docs, line by line), and the `docs/exit-codes.md` rows. `check_docs.py` stays clean.
  **Done:** no sentence of `docs/RETENTION.md` names 27b, 27c or 27d for a duty that row does not carry
  (`grep -n '27[bcd]' docs/RETENTION.md` is read line by line against the roadmap rows), the tracked-file
  command and guarantee 7 each name their home, and the archival example names the `.tar.zst` layout.
- **No other mechanism:** `git diff e026781 --stat -- payload` lists the script and its test file only.
- `docs/ROADMAP.md` already carries the split rows (written with this plan); this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites, the new tests and then the whole
`workflow_state_completion_obligations_test.py` chunk under the orphan wrapper, the `tools/release` tests (with
D-Staging's one declared scratch patch of two pinned numbers, its diff pasted) and the `tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.20.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.20.0 with its two pinned assertions in `workflow_protocol_test.py` and the
  matching `ORCHESTRATION_PROTOCOL.md` edits; the protocol version stays.
- `manifest.json` 2.20.0 (D-Release): `workflow_version`; the added `scripts/workflow_retention.py` record with
  its rule, digest, size and rationale; `sha256` and `size` of every changed record with a
  `retention-report (workflow-2.20.0)` sentence true of THAT file; counts 81, 6 and `distribution` 55; the
  `manager` block's posture rewritten for the minor with the way back; `conformance.suites` measured by
  `release.py manager-block --release-dir <scratch> --write` from a staging of CP2's own content;
  `min_manager_version` equal to the CI pin.
- `docs/release-history.md`: the 2.20.0 row and its "Last checked with" line; the "Last checked with" lines of
  `docs/RETENTION.md` and `docs/exit-codes.md` (edited in CP1) are already 2.20.0.
- `tools/release/release_test.py`: a 2.20.0 release class; the 2.19.2 class keeps what stays true of it.
- `docs/ROADMAP.md` is not written by this checkpoint: row 27b becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture;
`release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 27b | the read-only report: finished items, folder sizes, archive presence, prunable archives, JSON and text | CP1 | D-Finished, D-Report, D-Output |
| Row 27b | writes nothing | CP1 | D-Writes, T7 |
| Row 27b | roadmap split into 27b, 27c, 27d; references in `docs/RETENTION.md` | CP1 and this plan | D-Docs; `docs/ROADMAP.md` is written with this plan |
| Tracked-file command (old guarantees 1 to 6) | applies the rule to tracked files and links | **not here** | a later row, not yet scheduled; `docs/RETENTION.md` says so |
| Guarantee 7 | warns when the pile regrows | **not here** | a later row, not yet scheduled; the report does not implement it |
| Row 27c | the user-only archive command | **not here** | row 27c |
| Row 27d | the user-only prune | **not here** | row 27d |
| Manager row 17 | `status`/`doctor` calls the script | **not here** | outside this repository |
| Release | 2.20.0 bookkeeping | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-report-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its plan-stage
protected paths, and self-review checked that every path named in a Files paragraph, and every other path this
plan names (`docs/ROADMAP.md`, `docs/RELEASING.md`), is classified at both stages and that every deliverable is
protected at the implementation stage (`docs/RETENTION.md`, `docs/exit-codes.md`, `docs/release-history.md` and
`manifest.json` are listed in `implementation_stage.protected_paths`; `payload/`, `tools/` are protected
prefixes).

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands"; the manifest key is `workflow_version`.
Flows that need a Workflow release read the release cache primed under the orchestrator's runs
(`--release-cache`), never the network. Each flow names its workspace.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`), from `$TMPDIR/fixture/scripts` | the new tests pass: `python3 -B -m unittest -v workflow_state_completion_obligations_test.RetentionReport` (T9 does not rely on this `-B`: its children run without it) |
| f2 | a scratch copy of the staged fixture, one mutation at a time | each mutation named in CP1 makes at least one test fail; the control run passes |
| f3 | the staged conformance fixture | the `workflow_state_completion_obligations_test.py` chunk under the Manager's orphan wrapper reports no orphan beyond Git's own detached maintenance |
| f4 | the staged conformance fixture | the nine suites from the manifest's `manager.conformance.suites` list |
| f5 | the checkout (zlib-ng environment for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, and `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f6 | a scratch clone of this repository at the candidate, with a short script under `$TMPDIR` that calls `main(["report", "--json", "--archive-root", "<scratch dir>"], run=<fake>, resolve=<fake>)` from the clone's `payload/scripts` (the fake returns `merged` for every anchor commit; no network, no `gh`) | the JSON has the documented keys; the finished list excludes the 3 newest merged items and every open item; with scratch archives of 29, 30 and 31 days, only the 31-day one is `prunable` |
| f7 | the same scratch clone and archive directory as f6 | **nothing was written:** `find <repo> <archive-root> -type f -print0 \| sort -z \| xargs -0 sha256sum` before and after the run is identical, `git status --porcelain --ignored` is unchanged, and `ls <archive-root>/<repo>` lists the same names; the same comparison after a run whose fake raises on every query, and after a refused run; and a CLI run `python3 -I <fixture>/scripts/workflow_retention.py report` (no `-B`) on a copy of the fixture's scripts leaves no `__pycache__` |
| f8 | the checkout | `git diff e026781 --stat -- payload` lists the script and its test file, the release constant and protocol document edits only; the 2.20.0 history row, the manifest and `docs/RETENTION.md` agree on the version; the 2.19.2 and older rows are unchanged |

## 8. Answers to the manual external review of revision 1

| Finding | Verdict | Where |
| --- | --- | --- |
| EPR-001 (bytecode on the import surface) | accepted: the assignment cannot precede the module's own cache write | I1, D-Surface, D-Writes (two invocation forms), T9, CP1 mutation, f7 |
| EPR-002 (CP1 cannot pass the release tests) | accepted: `tools/release/release_test.py:2917-2918` pins (80, 6) and 54, the only pin of the old counts (grep over `tools/release/*_test.py`) | D-Staging (one declared scratch patch of two numbers, everything else unmodified) |
| EPR-003 (failure paths unverified) | accepted | D-Writes, T7, CP1 mutations, f7 |
| EPR-004 (determinism and absence, optional) | accepted | D-Output, T10 |
