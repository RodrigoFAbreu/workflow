# W31: Workflow 2.24.0 — the retention prune engine (Revision 2)

- **Work item:** `retention-prune` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 27f of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance). The user-only command is the new row 27g (`Later`, after 27f) and is not part of this item.
- **Issues:** RodrigoFAbreu/workflow#113 item 3, #119 item 7 and #123. **Branch:** `milestone/retention-prune`
- **Base commit:** `4529f218af343078a6768e6129b0e6be68116c02` (main after #125: release source and own installation
  are 2.23.0; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.24.0, a `feat:` minor, that adds **the prune engine** as a fourth subcommand of the shipped script:

```
python3 -I scripts/workflow_retention.py prune <work-item-id>... [--apply] [--json] [--ttl-days N] [--archive-root DIR] [--repo-root DIR]
```

It removes archive files `<archive-root>/<repo>/<id>.tar.zst` that are past the time to live (30 days by default, the
report's own rule: age by modification time, `age_days > ttl_days`). Dry run by default; `--apply` removes. The archives
are named explicitly, one or more, by work item id (never a path); each must be a current `archives` entry of the
report, derived fresh, with `prunable` true.

### The invariants (one sentence each)

- **I1. The dry run writes nothing,** on every path, a refusal included: no unlink, lock file, directory or bytecode.
- **I2. Only the named archives are removed,** each one `<id>.tar.zst` in the per-repository archive directory, by one
  `unlink` through that directory's descriptor. Nothing else is touched: not the index, not another archive, not
  `.removing`, not `.ai-review`, not the repository.
- **I3. The index is never opened.** `index.jsonl` keeps every line (the history of what was archived); a pruned id
  stays indexed.
- **I4. A refusal before the first unlink removes nothing:** the whole run is judged first (D-Selection 1 to 9, then
  under the lock 10 to 12), so one bad name stops all of them.
- **I5. Each unlink is checked immediately before it** (`lstat` through the descriptor: a regular file, not a symlink,
  still the size and modification time the report saw) and made durable (`fsync` of the directory).
- **I6. A failure stops the run,** leaves every archive not yet reached as it was, and names which were removed and
  which were not.

### Hard limits (the owner's sizing rule)

- **One mechanism, no protocol or state change.** `payload/` changes in the script, its tests in the existing suite,
  the release constant, `payload/scripts/workflow_protocol_test.py` and
  `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (the CP2 files): no change to `workflow_state.py`,
  `workflow_forge.py`, `workflow_gate_policy.py`, `WORKFLOW_STATE.json`, a phase, a trailer or a command file; no new
  manifest record, no tenth suite (CP1 re-checks with `git diff 4529f21 --stat -- payload`).
- **Sizing guard.** Two checkpoints (CP1 the engine, its tests and documents; CP2 the release). If this plan passes
  about 350 lines or needs a third, STOP and split before the first review.
- **This repository's own installation stays untouched** (`.claude/`, `scripts/`, `docs/ai-workflow/` managed
  documents, `.workflow-manager/`, managed blocks, the conformance workflow). The change goes to `payload/`,
  `manifest.json`, `tools/release/` and the three pages `docs/RETENTION.md`, `docs/exit-codes.md`,
  `docs/release-history.md`.

## 2. Facts this plan relies on (re-read at `4529f21`)

- `payload/scripts/workflow_retention.py` (1882 lines, `# state_writer: false`) holds the report, `archive_item` and
  `remove_item`. Reused as they are: `_ID_RE`, `RESERVED_IDS`, `_platform_ok`, `build_report` (its `archives` list holds
  only regular `*.tar.zst` files, each with `bytes`, `modified`, `age_days`, `prunable`, `item`; `removing` lists the
  ids under `.removing`; `repository_unknown` already covers a repository named `.` or `..`), `_removing_ids`,
  `_walk_chain`, `_lstat_at`, `_refuse`, `RetentionError`, the `flock` on the archive directory descriptor
  (`archive_busy`), `DEFAULT_TTL_DAYS`, `MAX_TTL_DAYS` and `main`'s `error:`/`next step:` convention.
- The report's `modified` has one-second precision, so the exact size and `st_mtime_ns` come from the engine's own
  `lstat` through the directory descriptor (D-Check).
- `_select_finished` ends (lines 976 to 991) with the destination checks every subcommand needs:
  `archive_inside_repository`, `archive_dir_unsafe` (a symlinked or non-directory per-repository directory),
  `unreadable` (a `read_errors` entry beneath it, a broken `.removing` included) and the chain walk. CP1 extracts them
  into `_select_destination` and calls it from `_select_finished` and from `prune_archives` (no copy). It extracts the
  id check (lines 944 to 946) into `_check_id` and the `--ttl-days` validation of `_parse` into `_ttl_of` the same way.
  Proof: the existing cases pass unchanged.
- The archive store holds `<id>.tar.zst`, `.<id>.partial`, `index.jsonl` and `.removing/` in
  `<archive-root>/<repo>/`. Nothing but `<id>.tar.zst` is touched by this item.

## 3. Design decisions

### D-Surface: a subcommand, `prune_archives`

`prune_archives(repo_root, ids, *, apply=False, archive_root=..., ttl_days=DEFAULT_TTL_DAYS, now, run=None,
resolve=None) -> dict`, importable like `archive_item`. `main` dispatches on `prune`; `--apply`, `--json`,
`--archive-root`, `--repo-root` are the other commands'; `--ttl-days` is the report's (the same validation and range),
so the preview and the report agree on what is prunable. At least one id is required (a usage error otherwise).
Duplicate ids collapse; the archives are processed in sorted order. It needs `"unlink"` and `"stat"` in
`os.supports_dir_fd` (else `path_unsafe`). It needs no `zstd` (it never reads an archive's contents) and opens no
`.ai-review` descriptor of its own.

### D-Selection: the one refusal order

**This is the only list of the order; every other section refers to it by number.** Each step is a refusal with a
stable code, one next step, and nothing written. The dry run runs 1 to 9; `--apply` runs 1 to 9, then 10 to 13.

| Step | Code | When | Next step |
| --- | --- | --- | --- |
| 1 | `invalid_id` | a name does not match `^[a-z0-9][a-z0-9_-]{0,63}$`, or is `runtime` or `archive` (#113) | pass the ids exactly as the report's `archives` lists them |
| 2 | `path_unsafe` | no descriptor-relative `unlink`/`stat` | run it on Linux or macOS |
| 3 | the report's refusals, passed through | `state_missing`, `state_invalid`, `repository_unknown` (a repository named `.` or `..`, #113) | the report's own |
| 4 | `archive_inside_repository`, `archive_dir_unsafe`, `unreadable` (via `_select_destination`) | the destination checks of section 2: a symlinked per-repository directory (#113), a path inside the checkout, a `read_errors` entry beneath the directory | repair it; the engine does not prune from a partial view |
| 5 | `not_in_report` | a name has no entry in the report's `archives` (no regular `<id>.tar.zst`: absent, a symlink, a directory; or no archive directory at all) | prune only archives the report lists |
| 6 | `removal_interrupted` | the id is in the report's `removing` (a leftover `.removing/<id>`, #119 item 7) | finish it first with `remove <id> --apply`; the archive may be the only copy of the leftover's missing entries |
| 7 | `not_prunable` | the entry's `prunable` is false (`age_days` not above the TTL); the message gives both | it becomes prunable when it is older than the TTL |
| 8 | `item_not_finished` | the entry's `item` is `open` (a failed forge query, no anchor, an open phase) or `recent` (one of the newest three): `docs/RETENTION.md` rule 1 calls such an item open and never touches its files, and its archive may be the only copy of its review folder. `finished` and `other` (an id absent from the state, so no item to protect) pass | wait until the report classes the item `finished`; the message gives the `item` |
| 9 | `archive_changed` | the first `lstat` of each named archive (D-Check) is not a regular file, or its size or time differs from the report's | run `prune` again for a fresh preview; nothing was removed |
| 10 | `archive_busy` | `flock(LOCK_EX \| LOCK_NB)` on the archive directory descriptor, the lock `archive` and `remove` use, is held (never in a dry run) | wait for the other run |
| 11 | `removal_interrupted`, `unreadable` | under the lock, `_removing_ids` is read again: it lists a named id (a `remove` began after step 6), or it adds an entry to its `errors` (`.removing` became a symlink, a non-directory or unreadable after the report, which must not read as "no interrupted removal") | as step 6; for `unreadable`, as step 4 |
| 12 | `archive_changed` | under the lock, every named archive is `lstat`ed again (the pre-pass) and differs from the value step 9 saw | as step 9; nothing was removed |
| 13 | `prune_failed`, `archive_changed` | during the deletes (D-Delete) | as D-Delete says |

The shared lock is what makes step 11 true: a `remove` creates `.removing/<id>` only under it.

### D-Check: what "the same file the report saw" means

At step 9 each named archive is `lstat`ed through the directory descriptor (`os.stat(name, dir_fd=, follow_symlinks=False)`)
and must be a regular file whose size equals the report's `bytes` and whose modification time, formatted by the report's own expression (the float `st_mtime` through
`datetime.fromtimestamp(..., timezone.utc)` and `_iso`, never `st_mtime_ns` by integer division, which can round a
second differently), equals `modified`; otherwise `archive_changed` (the report itself raced with a change). The exact
`(st_size, st_mtime_ns)` of that `lstat` is the **seen** value. Step 12 and D-Delete compare against it. A hard link or
a replaced file with a restored time is not claimed (the threat model is accidental loss, as in the removal).

### D-Delete: `--apply`, in order, under the lock

For each archive in sorted order: (a) `lstat` through the descriptor; not a regular file (a symlink included), or
`(size, mtime_ns)` not equal to the seen value, is `archive_changed`; (b) `os.unlink(name, dir_fd=adir_fd)` with the bare
validated name; an `OSError` is `prune_failed`; (c) `os.fsync(adir_fd)`; a failure is `prune_failed` saying that archive
**is removed**, its durability unconfirmed. Any refusal after the first unlink names `removed: <ids>` and
`not removed: <ids>` (the archives not reached are untouched, I6), and its next step is `run prune again for a fresh
preview`; `prune_failed` adds the errno and "check the permissions of the archive directory". No retry, no
`BaseException` handler: an interruption leaves the archives removed so far removed, the rest present, and the index
untouched. The result is `{"removed": [ids], "bytes": n}`.

### D-Output: JSON, text, exit codes

`--json` prints one object, keys sorted: `{"schema_version": 1, "kind": "retention-prune", "mode": "dry-run" | "apply",
"generated_at", "repository", "archive_dir", "ttl_days", "archives": [{"work_item_id", "name", "path", "bytes",
"modified", "age_days", "item"}], "index": "<path>", "result": {"removed": [], "bytes": 0}}`, where `index` is shown
as untouched and `item` is the report's class (`finished`, `recent`, `open` or `other`) so a person sees what the
archive belonged to. Exit 0: the dry run was printed or the archives were removed. Exit 2: a refusal, on stderr only,
with **nothing on stdout, `--json` included**. New codes: `not_in_report`, `removal_interrupted`, `not_prunable`,
`item_not_finished`, `archive_changed`, `prune_failed`; every other code is the report's or the archive's.

### D-Residual: what the design does not claim

A write between one archive's `lstat` and its `unlink` is not excluded; a hand replacement of the archive directory
during the run is refused only where D-Check sees it; a file-system crash. An archive of a finished item whose review
folder still exists is prunable like any other (the folder is the data; the prune does not read it). After a prune,
`archive` of that id says `already_indexed` (the index keeps the line; the owner decides), and `remove` says
`not_archived`.

### D-Tests and D-Orphan: class `RetentionPrune`, harness `_RP(_RA)`

In `workflow_state_completion_obligations_test.py`. `_RP` builds archives with the real engine (`archive_item`
`apply=True`), ages them with `os.utime` **in the scratch store only**, and uses a write guard that allows exactly the
`unlink` of a named `<id>.tar.zst` beneath the scratch archive directory, and nothing at all for the index. Every
refusal case asserts exit 2, the stable code, a snapshot **identical** to the one before (names, types, modes, symlink
targets, bytes and modification times of every file in the repository and the archive store, the index's bytes) and
the same open-descriptor count after the call. `skipUnless` names the missing `zstd` (the archives are made by it).

- **P1 dry run:** lists the named archives with `item`; the repository and the store are identical; no lock file, no
  unlink; a fresh `python3 -I scripts/workflow_retention.py prune w00` subprocess leaves no `__pycache__` or `.pyc`.
- **P2 apply:** only the named prunable archives are gone; an older unnamed prunable archive, a young one, the index
  (bytes and mtime), the review folders, the state and tracked files are identical; `os.fsync` of the archive
  directory follows each unlink; the report afterwards no longer lists them and `archive` says `already_indexed`.
- **P3 the refusal table,** one case per code of D-Selection, in order: invalid ids and `runtime`; a repository named
  `..`; the report's pass-through codes; a symlinked per-repository directory, an archive store inside the checkout,
  a broken (symlinked) `.removing` (`unreadable`); an absent archive, a symlink and a directory named `w00.tar.zst`
  (`not_in_report`); a leftover `.removing/w00` (`removal_interrupted`); an archive exactly at the TTL (age 30, not
  above) against one at 31 (`not_prunable` / accepted); an archive whose `item` is `open` (a forge query that fails for that id), `recent` or `other` (`item_not_finished` for the first two, accepted for `other`) and a `finished` one (accepted); `archive_busy` with a lock held by the test (never in a dry
  run); the re-read under the lock: a hook that replaces `.removing` by a symlink after step 9 gives `unreadable`, one that creates `.removing/w00` gives `removal_interrupted`; a **mixed run** (one valid name, one bad) removes nothing.
- **P4 changed after the preview:** between step 9 and step 12 the size, the mtime, a symlink swapped in and a
  directory swapped in each give `archive_changed` with nothing removed; a hook after the first unlink that changes the
  second archive gives `archive_changed` naming `removed: [first]`, `not removed: [second, ...]`, the later archives
  untouched; a symlink swapped in at the second `lstat` leaves its outside target intact.
- **P5 failures:** `os.unlink` raising `EIO` on the second archive: `prune_failed`, the first removed, the rest present,
  the message names both lists and the errno; `os.fsync` raising after an unlink: `prune_failed` saying that archive
  is removed; a `KeyboardInterrupt` at each of before the first unlink and between two unlinks leaves removed-so-far
  removed and a rerun finishes.
- **P6 the index is never opened:** the guard records every `open`; the index is not among them, in any case above.
- **P7 `--ttl-days`:** `--ttl-days 1` makes a two-day archive prunable and the preview agrees with `report --ttl-days 1`;
  `0`, `abc` and `3651` are usage errors (exit 2).
- **P8 the CLI:** `main(["prune", ...])` text and `--json`, exit codes, no names (usage), a refusal prints nothing on
  stdout.

**The failure-only mutations** (each fails a named case in a scratch copy; the control passes): m1 no TTL check (P3);
m2 no `removal_interrupted` at step 6 (P3); m3 no `removal_interrupted` under the lock (P3, a hook that creates
`.removing/w00` after step 6); m16 the re-read at step 11 ignores its `errors` (P3, a hook that replaces `.removing` by a
symlink after step 9); m17 no `item` check (P3); m4 delete by name without the report's entry (P3); m5 no pre-pass at step 12, so a mixed
change removes the first (P4); m6 no `lstat` immediately before the unlink (P4 hook); m7 `stat` that follows links
(P4 symlink); m8 continue after a failure (P5); m9 no `fsync` (P2, P5); m10 the dry run unlinks (P1); m11 the index
opened or touched (P6, P2); m12 no lock (P3 `archive_busy`); m13 a write injected only into the refusal handler, an
`os.utime` on an archive (P3 snapshot); m14 unlink by a joined path instead of through the descriptor (P2); m15 the
shared destination checks skipped (P3 symlinked directory, store inside the checkout). Results are recorded in `TEST_RESULTS.md`.

**No process left behind.** The new class and the whole obligations chunk run under the Manager's orphan wrapper
(`tests/parallel/reaper.py`, form in `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md`): no orphan beyond Git's own
maintenance.

### D-Docs: where it is described

`docs/RETENTION.md` gets a section "The prune command": the command, the dry run, D-Selection's table, D-Check and
D-Delete in words, the new codes, the JSON, D-Residual (the index keeps the line; `already_indexed` afterwards), and
how it differs from the report's `prunable` count. **Every reference to rows 27b to 27g is re-read** (grep `27[a-g]`
line by line): the intro paragraph ("The prune of old archives (row 27f) follows" becomes the engine of row 27f, with
the user-only command a later row, 27g), the archive section's note that the prune must not remove index lines, and
the last section's guarantees, which it extends with what the prune keeps: rule 1 (an `open` or `recent` item's
archive is never pruned, `item_not_finished`) and the rule's other guarantees, which it does not reach (it removes no
review folder, tracked file or index line). `docs/exit-codes.md` gets the `prune` rows. No page names an internal milestone id or
lists governing versions. "Last checked with" lines move at CP2 only. `docs/ROADMAP.md` is written **with this plan**
(27f `Current`, 27g added), never by a checkpoint.

### D-Release: 2.24.0, `feat:`

`manifest.json` 2.24.0, **no record added** (counts 82, 6 and `distribution` 56). The records that move are the script,
`workflow_state_completion_obligations_test.py`, `workflow_protocol.py` (`WORKFLOW_RELEASE` and nothing else),
`workflow_protocol_test.py` (its two pinned assertions) and `ORCHESTRATION_PROTOCOL.md` (tested releases, envelope
example, protocol note; the protocol version stays), each with a `retention-prune (workflow-2.24.0)` sentence true of
that file. `manager.conformance.suites` are measured, never typed. `min_manager_version` stays 1.13.0.
**Downgrade posture.** 2.24.0 writes no state key, phase, trailer, command file or protocol field. A downgraded release
has no `prune`; archives already pruned stay pruned and their index lines stay, so the older `archive` says
`already_indexed` for them. `tools/release/release_test.py` gets a 2.24.0 class and the 2.23.0 class stops pinning the
current version, constant, "Last checked with" lines and posture. `docs/release-history.md` gets the 2.24.0 row.

### D-Staging: scratch staging for CP1

CP1 changes two shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage its
tree. CP1 verifies in a disposable clone under `$TMPDIR`
(`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w31-tmp`):
a scratch script recomputes `sha256` and `size` of the two changed `artifacts` records, rewrites
`manager.conformance.suites` by the discovery `release.py manager-block --release-dir <scratch> --write` uses, commits
in the clone, and runs the "Verification commands" of `docs/RELEASING.md` from there (the release source stays at
2.23.0 in that commit). No rationale is touched; the counts (82, 6, 56) stay true. A `tools/release` failure is a stop
for the plan, never patched around, and no test is skipped. Those tests run with the zlib-ng interpreter
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions

No row of `docs/TECHNICAL_DECISIONS.md` is touched. Reversible choices made here: the whole run is refused when any
name is bad (instead of skipping it); the archive of a finished item whose folder still exists is prunable; the archive of an `open` or `recent` item is not
(`item_not_finished`, D-Selection 8, because rule 1 of `docs/RETENTION.md` never touches an open item's files and the
archive may be their only copy), while that of an `other` id is, since no item remains to protect; the archives are named by id, so a store entry whose stem is not a valid id can only be removed by hand.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The prune engine, its tests and the documents | - | 3 | 1 |
| CP2 | Release 2.24.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The prune engine, its tests and the documents

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`, `docs/exit-codes.md`.

- **The script** (D-Surface to D-Output): `_check_id`, `_select_destination` and `_ttl_of` extracted with the existing
  behaviour (selection otherwise unchanged), the `prune` subcommand, `prune_archives`, the text form; stdlib plus
  `workflow_forge`, still `# state_writer: false`. **Done:** every case of D-Tests passes and the existing
  `RetentionReport`, `RetentionArchive` and `RetentionRemove` cases pass unchanged.
- **The tests** (D-Tests): written first; each mutation m1 to m17 fails at least one named case in a scratch copy and
  its result is recorded.
- **The documents** (D-Docs). `check_docs.py` stays clean. **Done:** `grep -nE '27[a-g]' docs/RETENTION.md` read line
  by line against the roadmap rows shows no sentence naming a row for a duty it does not carry; the "Last checked with"
  lines are unchanged. **No other mechanism:** `git diff 4529f21 --stat -- payload` lists the script and its test file
  only.

**Verification:** D-Staging in a disposable clone: the nine suites, the new class and the whole obligations chunk
under the orphan wrapper, the `tools/release` and `tools/docs` tests (zlib-ng interpreter, no patch),
`check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.24.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.24.0 with its two pinned assertions and the matching `ORCHESTRATION_PROTOCOL.md` edits
  (protocol version stays).
- `manifest.json` 2.24.0 (D-Release): `workflow_version`, `sha256`, `size` and sentence of every changed record, counts
  unchanged, the posture, `conformance.suites` measured by `release.py manager-block --release-dir <scratch> --write`
  from a staging of CP2's own content.
- `docs/release-history.md`: the 2.24.0 row and its "Last checked with" line; those of `docs/RETENTION.md` and
  `docs/exit-codes.md` move to 2.24.0.
- `tools/release/release_test.py`: a 2.24.0 class; the 2.23.0 class keeps what stays true of it.
- `docs/ROADMAP.md` is not written by this checkpoint: row 27f becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block` and `tools/docs` are clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 27f | the prune: named archives, fresh report, past the TTL, one unlink each, checked and durable, index untouched | CP1 | D-Selection to D-Delete |
| #113 item 3 | `.`/`..`, symlinked per-repository directory, ids `runtime`/`archive`, act only on the report's `archives` | CP1 | D-Selection 1, 3, 4, 5, 8 |
| #119 item 7 | never prune an archive whose id is under the report's interrupted removals | CP1 | D-Selection 6 and 11, P3, m2, m3, m16 |
| #123 item 1 | the protocol's list of user-only commands | **not here** | row 27g (the command is its subject) |
| #123 item 3 | release-test docstring pointers to "the current release" | CP2 | the 2.24.0 class moves them |
| #123 items 2, 4 to 6 | operator-reference wording, command-test pins, checklist text, `cross_device` wording | **not here** | they belong to the archive command and its documents, not to this engine; one mechanism per item |
| Row 27g | the user-only prune command | **not here** | new row, `Later` |
| Roadmap, release | 27f Current, 27g added; 2.24.0 bookkeeping | this plan; CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-prune-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; every path a checkpoint's **Files** names is classified at both
stages (`assert_plan_artifact_declaration_coverage` reads those paragraphs only), and the generated template protects
only its own file, so `payload/`, `tools/`, `fixtures/`, `templates/`, `manifest.json`, `docs/RETENTION.md` and
`docs/release-history.md`, `docs/exit-codes.md` are added to the implementation-stage protected paths before the first bundle.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands". **Never run `--apply` against the real archive
store**; the checklist executor has no real archives. The key is `workflow_version` in `manifest.json`.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`), from `$TMPDIR/fixture/scripts` | `python3 -B -m unittest -v workflow_state_completion_obligations_test.RetentionPrune` passes, the three earlier retention classes unchanged, the whole chunk under the orphan wrapper reports no orphan beyond Git's own maintenance, and the nine suites of `manager.conformance.suites` pass |
| f2 | a scratch copy of the staged fixture, one mutation at a time | each of m1 to m17 makes the named case fail; the control run passes |
| f3 | the checkout (zlib-ng interpreter for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f4 | a **scratch repository** (`git init` under `$TMPDIR` with a `github.com` origin, a hand-built state of finished items, a fake forge returning `merged`), a **scratch archive root**, archives made by the engine (`archive <id> --apply`) and aged with `os.utime` in the scratch store only | **the dry run changes nothing:** `prune <id> <id2>` prints both; hashes and times of the repository and the store are identical before and after, the index byte for byte |
| f5 | the same scratch workspace | **apply removes only the named prunable archives:** `prune <id> <id2> --apply` leaves an unnamed old archive, a young one, the index (bytes and mtime), the folders and the state identical |
| f6 | the same scratch workspace | **refusals touch nothing:** a young archive (`not_prunable`), an id not in the report (`not_in_report`), one with a hand-made `.removing/<id>` (`removal_interrupted`), a symlinked archive (`not_in_report`), an archive of an `open` item (`item_not_finished`), a mixed run, and a file touched after the preview (`archive_changed`) each exit 2 with nothing removed |
| f7 | the checkout | `git diff 4529f21 --stat -- payload` lists the script, its test file and the CP2 files of D-Release only; the 2.24.0 history row, the manifest and `docs/RETENTION.md` agree on the version |
