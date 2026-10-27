# W29: Workflow 2.22.0 — the retention removal (Revision 1)

- **Work item:** `retention-removal` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 27d of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance). The user-only command (27e) and the prune (27f) are not part of this item.
- **Issue:** RodrigoFAbreu/workflow#116 item 7, and the obligations EPR-001 and EPR-010 that row 27d carries.
  **Branch:** `milestone/retention-removal`
- **Base commit:** `0c06330727d72d418d1d00f36d53343ea455c211` (main after #118: release source and own installation
  are 2.21.0; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.22.0, a `feat:` minor, that adds **the removal** as a third subcommand of the shipped script:

```
python3 -I scripts/workflow_retention.py remove <work-item-id> [--apply] [--json] [--archive-root DIR] [--repo-root DIR]
```

**The owner's decision of 2026-10-26 (option D, the rename-aside design).** The threat model is accidental loss, not an
adversary: the item is finished and merged, it cannot be reopened, and nothing in the Workflow writes to its review
folder. The removal of an archived finished item's `.ai-review/<id>/` is one mechanism:

1. re-derive that the item is finished (the report's rules, N = 3 keep-recent included, a fresh forge query), that a
   verified archive exists with its index line, and take the tool's lock;
2. take the folder out of the repository with **one atomic rename** into `<archive-root>/<repo>/.removing/<id>`, a
   directory only this tool owns, on the same file system (a different one is refused, no copy fallback);
3. **verify the archive against the renamed folder by contents** (the listing and the SHA-256 of every file, symlinks as
   symlinks), now that nothing in the repository refers to it;
4. equal: delete the renamed folder, entry by entry; different: rename it back without replacing anything and refuse,
   naming the difference;
5. an interrupted run leaves one recognisable leftover, `.removing/<id>`, which the report lists and the next run
   completes (verify, then delete) or renames back. **Nothing is ever deleted that is not proven present in the
   archive with matching contents.**

Dry run by default; `--apply` removes. One item per run. Never an open item, a `kept_recent` item, a tracked file (a
tracked gitlink at the item root counts) or anything outside `.ai-review/<id>/`; the folder is never deleted without a
verified archive.

### The invariants (one sentence each)

- **I1. The dry run writes nothing,** on every path, a refusal included: no directory, rename, lock or bytecode. It
  reads the folder and the archive and says whether they match.
- **I2. Nothing leaves the repository except the one rename,** and what is deleted is only what was proven present in
  the archive with matching contents, at the moment of its own unlink (D-Delete).
- **I3. Only an item the report lists as finished,** from a fresh query, with an archive file **and** an index line.
- **I4. The archive and the index are read, never written** (the archive's modification time is the report's age).
- **I5. No link is followed:** the same descriptor-relative access as the archive command; a symlink inside the folder
  is unlinked as a symlink.
- **I6. A failure never loses data, and says where the folder is.** After a refusal it is (a) in its original place;
  (b) whole in `.removing/<id>`, when it could not be put back without replacing something; or (c) only after a
  stopped delete (`folder_changed`, `remove_failed`), a **smaller leftover** in `.removing/<id>`, every deleted entry
  proven archived. Each refusal names the place, and for (c) the count deleted and the next step. A failure to make a completed step
  durable names the place that step completed (D-Flow 3, D-Restore, D-Delete), never a place it did not reach.

### Hard limits (the owner's sizing rule)

- **One mechanism, no protocol or state change.** The change to `payload/` is the script, its tests in the existing
  suite, the release constant, `payload/scripts/workflow_protocol_test.py` and
  `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (the CP2 files of D-Release): no change to `workflow_state.py`, `workflow_forge.py`, `workflow_gate_policy.py`,
  `WORKFLOW_STATE.json`, `WORKFLOW_CONFIG.json`, a phase, a trailer or a command file; no new manifest record, no
  tenth suite (CP1 re-checks with `git diff 0c06330 --stat -- payload`).
- **Sizing guard.** The recovery section (D-Leftover) is **one table of three states** (L0, L1, conflict). A row may
  gain words; if it gains a fourth state, or a second table, STOP and split (detect and report the leftover now, repair
  later). The plan's own length is not a limit.
- **Two checkpoints** (CP1 the removal and its documents, CP2 the release). **This repository's own installation stays
  untouched** (`.claude/commands/`, `scripts/`, `docs/ai-workflow/`, `.workflow-manager/`, managed blocks, the
  conformance workflow); the change goes to `payload/`, `manifest.json`, `tools/release/` and the three pages
  `docs/RETENTION.md`, `docs/exit-codes.md`, `docs/release-history.md`.

## 2. Facts this plan relies on (re-read at `0c06330`)

- `payload/scripts/workflow_retention.py` (1265 lines, `# state_writer: false`) holds the report (`build_report`) and
  the archive (`archive_item`). Reused as they are: `_ID_RE`, `RESERVED_IDS`, `_platform_ok`, `_open_review_root`, `_walk_folder`, `_scan`, `_record`,
  `_comparable`, `_open_file`, `_walk_chain`, `_open_index`, `_index_ids`, `_git_tracked`, `_underneath`, `_fsync`,
  `_refuse`, `_reap`, `_stderr_of`, `RetentionError`, the `flock` on the archive directory descriptor
  (`archive_busy`), and `main`'s `error:`/`next step:` convention.
- `archive_item` lines 900 to 948 (id, platform, anchor, report, finished record, destination, chain walk) are the
  selection both subcommands need. CP1 extracts them into `_select_finished(..., fds)` and calls it from both. The
  lines straddle `archive_item`'s `try:`, so **the caller owns every descriptor**: `_select_finished` appends each one
  it opens to the caller's `fds` list (and `ai_fd`) before anything can refuse, and the caller's `finally` closes them,
  as `archive_item`'s does today. Proof: the existing cases pass unchanged, and T4 asserts no descriptor leaks.
- The archive store holds `<id>.tar.zst`, `.<id>.partial` and `index.jsonl` in `<archive-root>/<repo>/`; the report
  lists only `.tar.zst` names and `_judge_archive_side` looks only at those three, so a directory `.removing` beside
  them is invisible to the 2.20.0 report and the 2.21.0 archive.
- An archive's members are `<id>`, then `<id>/<path>`, written by `_pack`; `_verify` compares in order and cannot name
  a difference or allow a missing entry, so the removal reads the archive into a table (D-Compare).
- `os.rename(src, dst, src_dir_fd=, dst_dir_fd=)` replaces an **empty** destination directory silently and fails with
  `EXDEV` across file systems. `shutil.rmtree(dir_fd=)` re-opens by name; this item does not use it.

## 3. Design decisions

### D-Surface: a subcommand, `remove_item`, in the existing script

`remove` joins `report` and `archive`. The module gains `remove_item(repo_root, item_id, *, apply=False,
archive_root=..., now, run=None, resolve=None, zstd=None) -> dict` (importable like `archive_item`) and two test
seams: `_rename = os.rename` (every rename the item makes goes through it) and `_same_device(fd_a, fd_b)`. `main`
dispatches on the subcommand; `--apply`, `--json`, `--archive-root`, `--repo-root` are the archive command's. It needs
`zstd` (D-Compare reads the archive with `zstd -dc`) and `"rename"` in `os.supports_dir_fd` (else `path_unsafe`, checked
by `remove` itself).

### D-Selection: the one refusal order

Each step is a refusal with a stable code and one next step, and none writes anything. **This is the only list of the
order; every other section refers to it by number.** The dry run runs 1 to 12; `--apply` runs 1 to 11, then D-Flow.

1. `invalid_id`: the id must match `^[a-z0-9][a-z0-9_-]{0,63}$` and not be `runtime` or `archive`.
2. `path_unsafe` (no descriptor-relative access, or `.ai-review` a symlink or not a directory), `unreadable`. An
   **absent** `.ai-review` is not refused here (L1 allows it); `ai_fd` is then `None` and nothing passes it on (D-Restore).
3. The report's own refusals (`state_missing`, `state_invalid`, `repository_unknown`), passed through.
4. `not_finished:<reason>`, `kept_recent`, `unknown_item`: the id must be in the report's `finished` list.
5. The destination: `archive_inside_repository`; `archive_dir_unsafe` (the per-repository directory or a component of
   its chain only); `unreadable` (a `read_errors` entry beneath it, a component without read permission, or a broken
   `.removing`, which D-Report makes a `read_errors` entry). So a broken `.removing` is `unreadable` for `remove` and
   `archive` alike, through this one shared check, which is not changed. For `archive` that is a deliberate change
   from 2.22.0 (`docs/RETENTION.md`'s archive table, T13). The shared next step takes the command name: `remove`
   prints "the engine does not remove from a partial view".
6. The archive store, read-only: a missing chain, `<id>.tar.zst` not an ordinary file, or no index line for the id →
   `not_archived` (the message names which half is missing); judged after the index's integrity: `index_unsafe`,
   `index_invalid` (this is where a **partial index line** stops the run: a half line means a run was killed in the
   middle of an append, and nothing is deleted under an index that cannot be read).
7. `tracked_files`: `_git_tracked`, any tracked entry at or beneath `.ai-review/<id>`, a gitlink at the root included.
8. The leftover (D-Leftover): `.removing/<id>` present and not a real directory, or present while `.ai-review/<id>` is
   also present → `leftover_conflict`; present alone → state **L1**; absent → state **L0**.
9. The folder to remove: in L0 `.ai-review/<id>` not a real directory → `review_folder_absent`; a `read_errors` entry
   beneath it → `unreadable`; in both states `_scan` of it (the leftover in L1) → `unsupported_entry`
   (socket, FIFO, device, a file with more than one link).
10. `cross_device` (L0): `.ai-review` and the archive directory on different file systems (`_same_device`). Nothing was
    moved; the next step is to keep the archive store on the repository's file system (`--archive-root`) or leave the
    folder.
11. `zstd_missing`.
12. **Dry run only:** the contents comparison of D-Compare, read-only, against the folder in place (L0) or the
    leftover (L1) → `archive_mismatch`, **a refusal like any other** (D-Output). `--apply` makes the same comparison
    after the rename (D-Flow 5), which is the one that counts.

**The leftover note (I6, every state).** Any refusal from selection 6 on, and any of D-Flow 1 and 2 (`archive_busy`,
`place_failed`), raised while `.removing/<id>` exists as a real directory (a read-only `lstat`, so L1 is known at
selection 7, 9 and 11 too), ends with one shared line: `an earlier run's leftover is untouched in
<archive-root>/<repo>/.removing/<id>; once this is resolved, run `remove <id> --apply` again`. A refusal that moved the
folder (D-Restore, D-Delete) names its own place instead (I6).

### D-Compare: the archive read into a table, the folder hashed, the differences named

`_archive_table(zstd, adir_fd, name, item_id)` streams `zstd -dc <archive>` into `tarfile` (`r|`, as `_verify` does)
and returns `{path: (type, size, link target, sha256)}`, hashing each file's bytes as they stream (memory is the
table). `_hash_folder(dir_fd, item_id)` walks with `_walk_folder` and returns `_record`s with a SHA-256 for every file
(`_open_file`, one read each, the same size and `nlink` checks as `_pack`). `_differences(table, records,
allow_missing)` returns `([(path, why)], missing)` where `why` is `differs` (type, size, target or hash) or `not in archive`, and,
only when `allow_missing` is false, `missing from folder` is a `why` too; with it true those entries are counted in
`missing` instead. The refusal names the first ten differences and the count.

- **A fresh run** (L0) compares with `allow_missing=False`: a folder that is not the archived one stops the run.
- **A leftover** (L1) compares with `allow_missing=True`: a leftover a killed delete left smaller is fine, because the
  rule is that **every entry that will be deleted is present in the archive with matching contents**. An entry that is
  extra or differing is not.
- The comparison is by **contents**. A listing is never enough (EPR-010), and sizes or modification times are never
  trusted to equal the archived ones: a changed file of the same size with its modification time restored is a
  difference (test T3a).

### D-Flow: what `--apply` does, in order

Under the lock the whole way. A refusal that leaves the folder in its place also leaves the archive store as it was
(a `.removing` this run created and left empty is removed; after a success it stays, empty). A refusal that leaves
the folder elsewhere is I6 (b) or (c): step 4's renames nothing, step 5's and a stopped delete (D-Delete) name where
the folder is.

1. Selection 1 to 11 (the descriptors stay open); take `flock(LOCK_EX | LOCK_NB)` on the archive directory descriptor,
   the lock `archive` uses: a second run gets `archive_busy`. Repeat selection 5 to 11 under the lock (defence in
   depth against a change between the two: no case or mutation pins it, and none claims it).
2. Create `.removing` (mode 0700) if absent, open it with `O_NOFOLLOW | O_DIRECTORY`, make it durable (`fsync` of
   it and of the archive directory). In L1 this step only opens it. A failure is `place_failed`.
3. **L0 only: the rename.** `lstat` of `.removing/<id>` shows it absent (present: `leftover_conflict`); record
   `before = stat(.ai-review/<id>)`; `_rename(<id>, <id>, src_dir_fd=ai_fd, dst_dir_fd=removing_fd)`; `EXDEV` →
   `cross_device` (nothing moved), any other error → `place_failed` (nothing moved). `fsync` both directories; a
   failure there is `place_failed` saying the rename **is done**: the folder is whole in `.removing/<id>`, not
   confirmed durable, nothing renamed back or deleted, the next step `remove <id> --apply` (state L1). From here the
   repository refers to nothing in the folder.
4. Check the identity: `stat(.removing/<id>)` is a real directory, and in L0 its `(st_dev, st_ino)` equals `before`'s;
   otherwise `folder_changed`, **and nothing is renamed back or deleted** (it is not the folder this run moved).
5. Compare (D-Compare): `records = _hash_folder(...)`, `table = _archive_table(...)`, `diff = _differences(...)`;
   then a stat-only `_scan` of the folder whose `_comparable` list must equal `records`' (a process that held a file
   open and wrote during the verify is `folder_changed`; defence in depth, since D-Delete's per-entry check also
   catches it, so no mutation pins it). A `diff` is `archive_mismatch`.
6. Equal: delete (D-Delete), then `fsync` `.removing`; a failure there is `remove_failed` saying the folder **is
   deleted**, every entry proven archived, durability unconfirmed, nothing to restore. Different, or any refusal of step 5: in L0 (the folder is whole) **rename back** (D-Restore) on `archive_mismatch`,
   `folder_changed`, `unreadable` or `unsupported_entry` and raise the refusal. **In L1 the rename back happens only
   after `_differences` has returned** (so `missing` is known), that is on `archive_mismatch`, or on a `folder_changed`
   of the re-check; a step-5 refusal raised before the comparison could run (`unreadable` from `_archive_table` or
   `_hash_folder`, `unsupported_entry`) **leaves the leftover in `.removing/<id>`** (I6 b): the refusal names that place,
   says the folder may be incomplete and that the missing entries exist only in the archive, and its next step is to
   repair the archive or the access and run `remove <id> --apply` again. A `folder_changed` raised by `_hash_folder`'s
   walk (an entry vanished while it was read) takes the same no-rename path, and its next step is "run it again when
   nothing writes to `.removing/<id>`". **Only a refusal (`RetentionError`) renames
   back**: an interruption (`KeyboardInterrupt` or any `BaseException`) leaves the state T14 names, and the
   `except BaseException` undo of `archive_item` is not copied. Step 4's refusal is the one that renames nothing.
7. Release the lock. The result is `{"removed": true, "files", "bytes"}` from `records`.

### D-Delete: entry by entry, each checked against what was verified

`_remove_tree(removing_fd, item_id, records)` walks `os.fwalk(item_id, topdown=False, dir_fd=removing_fd,
follow_symlinks=False)`. For each file or symlink (a symlink to a directory is in `dirnames` and is unlinked, never
descended) it `lstat`s the entry and requires its `_comparable` to equal the verified record's: an entry that is not in
`records`, or whose size, modification time or change time moved, **stops the walk** with `folder_changed` and is kept.
Directories are checked by name only (their times move as children go). `unlink`/`rmdir` go through the descriptor;
any `rmdir` (nested or the last, `<id>`) failing with `ENOTEMPTY` is `folder_changed` (an entry appeared), another
`OSError` is `remove_failed`, whose message names the errno and the entry and adds "check the permissions of
`.removing/<id>`" to the next step (a cause that persists is not cured by a rerun alone). **A stop leaves a smaller leftover** (I6 c), which is L1 for the next run. The refusal
says: `stopped after deleting <n> entries, each proven archived; the rest is in <archive-root>/<repo>/.removing/<id>;
run `remove <id> --apply` again`. The rerun completes the delete, or, if the cause was an extra or changed entry,
renames the remainder back as D-Restore says. This answers EPR-001 (section 8).

### D-Restore: rename back, never replacing

A valid `ai_fd` is required: with `.ai-review` absent (L1 only) **nothing is moved** and `None` never reaches a
rename: the refusal says the folder stays whole (or smaller) in `.removing/<id>`, that `.ai-review` is absent, and the
next step is to create it and `mv` the folder back. Otherwise `lstat(.ai-review/<id>)` through `ai_fd` must say absent;
then `_rename(<id>, <id>, src_dir_fd=removing_fd, dst_dir_fd=ai_fd)`, and `fsync` both. If `.ai-review/<id>` exists, or
the rename fails with `ENOTEMPTY`, `EEXIST` or `ENOTDIR`, **nothing is moved**: the refusal says the folder stays in
`.removing/<id>` (the next step names the `mv` back). Any other `OSError` of the rename is `restore_failed` with that
location. A failing `fsync` **after** the rename is `restore_failed` saying the folder **is back** in
`.ai-review/<id>`, durability unconfirmed. The residual: the rename onto an *empty* directory created in the
milliseconds after the `lstat` replaces that empty directory (only an empty directory is at risk, and nothing in the
Workflow creates `.ai-review/<id>` for a finished item). Every rename back uses this one function. `_fsync` gets a
`where` argument for its message: its default, "nothing was kept", is used only before any rename.

**What a refusal says about the differing entries (EPR-010).** An `archive_mismatch` refusal ends: the differing
entries exist only in this folder, **keep them** (copy them out first); a later `remove` stays refused while they
differ. When the comparison ran with `allow_missing` and `missing` is above zero (a delete was stopped or killed
earlier), the folder that returns is also **incomplete**: the refusal adds `<m> archived entries are missing because an
earlier run already deleted them; they are in <archive>; extract them with `zstd -dc <archive> | tar -x -C <scratch>`
and merge by hand`. Nothing in any message offers to delete the folder or its differing entries. A `restore_failed` raised while renaming
back after an `archive_mismatch` (the `fsync` after a completed rename, or a failing rename) still carries the
differences and the "keep them" text, so the run that found unarchived bytes never drops that fact. After a
`restore_failed` the `.removing` this run created stays, empty or holding the folder as the message says; it is removed
only after a rename back that finished cleanly.

### D-Leftover: one table of three states

The recognisable leftover is `<archive-root>/<repo>/.removing/<id>/`. What is on disk at selection step 8:

| State | On disk | The run |
| --- | --- | --- |
| L0 | `.ai-review/<id>` present, no `.removing/<id>` | a fresh removal (D-Flow 3 to 7) |
| L1 | `.removing/<id>` a real directory, `.ai-review/<id>` absent: a run was killed or stopped after the rename, during the verify, during the delete (a smaller folder) or during the rename back (atomic: exactly one of the two places) | selection 5 to 11 still apply, D-Flow 4 to 7 without the rename, with `allow_missing`: complete the delete, or rename back (a partial one with the message of D-Restore) |
| conflict | `.removing/<id>` not a real directory, or both folders present | `leftover_conflict`, nothing moved or deleted: compare by hand and move one aside |

A run killed **before** the rename leaves L0. A leftover whose archive is gone or whose index is unreadable stops at
selection 6 untouched; the next step names it and the `mv` back. **The report lists the leftover** (D-Report).

### D-Report: one additive key

`build_report` gains `"removing": [<id>, ...]` (sorted): the names of the directories in `<archive-dir>/.removing/`.
A `.removing` that is a symlink or not a directory, or cannot be read, is one `read_errors` entry (`complete` false);
no key for it elsewhere. The text form gains `Interrupted removals (n): <ids>, finish them with `remove <id> --apply``.
`schema_version` stays 1 (additive; the Manager and Controller ignore unknown keys). Whole-report cases gain the key.

### D-Output: JSON, text, exit codes

`--json` prints one object, keys sorted: `{"schema_version": 1, "kind": "retention-remove", "mode": "dry-run" |
"apply", "generated_at", "repository", "work_item_id", "pull_request": {"number", "url"}, "review_folder": {"path",
"state": "in_place" | "leftover", "files", "bytes", "entries": [{"path", "type", "bytes"}]}, "archive": {"path",
"bytes", "indexed": true}, "target": {"removing": "<path of .removing/<id>>"}, "verify": {"matches": true}, "zstd", "result": {"removed": false} | {"removed": true, "files", "bytes"}}`. Exit 0: the dry run
was printed or the folder was removed; 2: a refusal, on stderr only, with **nothing on stdout, `--json` included**.
So a dry run that finds a difference is the `archive_mismatch` refusal (selection 12; the message names the first ten
differences), never an object, and `verify` is always `{"matches": true}` in a printed object. New codes:
`not_archived`, `archive_mismatch`, `leftover_conflict`, `cross_device`, `remove_failed`, `restore_failed`; every
other code (`place_failed` too, which gets `remove` rows in `docs/exit-codes.md`) is the archive's.

### D-Residual: what the design does not claim

A process that held a file of the folder open before the rename could still write to it; a finished item has none.
Against it stand D-Flow 5's comparison and re-check and D-Delete's per-entry check; a write between one file's `lstat`
and `unlink` is not excluded. Also not claimed: protection against a hand replacement of `.removing/<id>` during the
run (D-Flow 4 refuses the swap it can see) or a file-system crash.

### D-Tests and D-Orphan: class `RetentionRemove`, harness `_RM(_RA)`

In `workflow_state_completion_obligations_test.py`. `_RM` extends the existing `_RA` fixture: a scratch repository
with a `github.com` origin, a hand-built state, the fake forge (`merged` for every anchor), review folders with files,
a nested directory, an empty one and symlinks, a **real archive made by `archive_item(apply=True)`**, and the write
guard, which here allows exactly the rename out of `.ai-review/<id>` (and back) and unlink/rmdir beneath
`.removing/<id>`. Every refusal case asserts exit 2, the stable code, and a snapshot **by outcome**. **What a snapshot compares
(EPR-016).** Strict: the names, types, modes, symlink targets and file bytes (and the modification time of every
**file**) of every path in the repository and the archive store, the archive's and the index's bytes, and every path
outside `.ai-review` and the archive store. Never compared: the **timestamps of directories** (a rename or an unlink
changes the directory it leaves or enters, and a restored folder keeps its files but not its parents' times). The one
namespace change permitted is the container `<archive-root>/<repo>/.removing`, and **what is permitted depends on the
outcome and on the state before the run (LPR-R6-001)**. Where `.removing` was **absent before** an L0 run and the run
refused with the folder restored or never moved (T3, T5, and every other refusal of D-Flow 1 to 6 that leaves the
folder in place), `.removing` is asserted **absent** afterwards: the run created it and removed it again (its one
`rmdir`). "Present and empty" is permitted only where it existed before the run, after an L1 rename back (it
held only the leftover, which has moved), after a success (T2), after an interruption (T14, which skips cleanup),
and for outcome (e). The outcomes: (a) the folder in place: the repository
as before, the archive store as before apart from that container (for an L1 case, `.removing/<id>` has moved to
`.ai-review/<id>`, bytes equal to the leftover's); (b) the folder whole in `.removing/<id>`: the same, with the
leftover's files byte-identical and `.ai-review/<id>` absent; (c) a stopped delete (T7, T12): everything else
identical, the leftover a subset of the original, and every missing entry present in the archive with equal contents;
(d) deleted with durability unconfirmed (T15, after the last `rmdir`): `.removing/<id>` absent, everything else
identical; (e) a `restore_failed` after a completed rename back: the folder in place, `.removing` present and empty.
The prohibitions that guard the folder (T3) concern **its entries**, never the empty container. `skipUnless` names the
missing `zstd`.

- **T1 dry run:** lists every entry and `matches: true`; the repository, folder and archive store are identical
  before and after (hashes and times); no rename, no `.removing`, no lock file; a changed folder gives
  the `archive_mismatch` refusal in the dry run too: exit 2, empty stdout with and without `--json`. A fresh `python3 -I
  scripts/workflow_retention.py remove w00` subprocess leaves no `__pycache__` or `.pyc` anywhere in the scratch tree.
- **T2 apply:** `.ai-review/w00` is gone; other items' folders, tracked files, the state, the archive's bytes and
  mtime and the index's bytes are unchanged; `.removing` is empty; the call order is rename, reads, then unlinks; the
  report afterwards lists the item as finished with no folder, an archive and `removing: []`.
- **T3 a difference refuses and nothing is lost:** (a) same-size changed bytes with the modification time restored,
  (b) an added file, (c) a removed file, (d) a retargeted symlink, (e) a changed file in a nested directory. Each:
  `archive_mismatch` naming the path, the folder back in place byte for byte, `.removing` **absent** (it was absent before the run; the container
  this run created is removed after the clean rename back; for an L1 case that renamed the leftover back, present and empty), **no `unlink` call, and no `rmdir` of any path
  other than that empty container** (never of the item or an entry beneath `.removing/<id>`), the archive store
  unchanged (the snapshot rules above).
- **T4 the refusal table,** one case per code of D-Selection (the list is not the refusal order): invalid ids, an open item, `kept_recent`, an
  unknown id, no archive, an archive without its line, a line without its archive, a half index line, a symlinked
  index, a symlinked `.ai-review`, a symlinked per-repository directory, a symlinked `.removing` (`unreadable`), an archive store inside the
  checkout, a tracked file and a tracked gitlink at the item root, a FIFO in the folder, `zstd` missing, an absent folder, `archive_busy` (a lock held by the test; never in a dry run), the report's pass-through codes
  (`state_missing`, `state_invalid`, `repository_unknown`) and `unreadable` (a folder without read permission). Each
  case also asserts the open-descriptor count (`/proc/self/fd`, else `/dev/fd`, as on macOS) is the same after the call (a leak in `_select_finished` fails it).
- **T5 `cross_device`:** the `_same_device` seam refuses in the dry run and `--apply`; the `_rename` seam raising
  `EXDEV` at the rename leaves the folder in place and the archive store as it was (`.removing`, absent before the run, is **absent** after it: the case that fails m13).
- **T6 rename back never replaces:** a hook after the rename creates a populated `.ai-review/w00` while the contents
  differ; the run refuses saying the folder stays in `.removing/w00`; the populated directory and the leftover are intact.
- **T7 a late writer:** a hook on the descending delete walk (`os.fwalk` with `topdown=False`) changes one file and
  adds another inside the renamed folder; the walk stops with `folder_changed`, both are kept, and the message names
  `.removing/w00`, the count deleted and `remove w00 --apply`; the next run finds the extra entry, renames the
  remainder back and names it, saying the missing entries are in the archive (D-Restore).
- **T8 identity:** a hook placed **immediately after the outward rename and before D-Flow 4's identity check** (not the
  delete-walk hook of T7, which runs after that check and so cannot tell m6 from the control) swaps `.removing/w00`
  for a populated directory; nothing is deleted,
  nothing is renamed back, the swapped-in directory is intact.
- **T9 a killed run, for real:** `main` in a subprocess (own process group) with a stand-in `zstd` that sleeps in `-dc`;
  once `.removing/w00` exists the group gets `SIGKILL`. The state is L1: the folder whole in `.removing`, none in
  place, archive and index intact, the report lists `removing: ["w00"]`. A second `remove w00 --apply` completes it
  (folder and leftover gone). The test waits for and asserts the death of every child.
- **T10 leftover states built by hand:** (a) whole, resumed and deleted; (b) partly deleted, finished; (c) **same-size
  changed bytes, modification time restored (EPR-010): not deleted, renamed back, the difference named**; (d) an extra
  file in a partly deleted leftover: renamed back, the refusal names the extra file, the count of entries missing,
  the archive path and the restore command (a whole leftover with an extra file: the difference only); (e) both folders present: `leftover_conflict`, both intact; (f) archive gone: `not_archived`,
  leftover untouched; (g) half index line: `index_invalid`, leftover untouched; (h) `.removing/w00` a file or a
  symlink: `leftover_conflict`; (i) **`.ai-review` absent** with a different leftover, the process working directory an
  unrelated scratch directory: the leftover is kept where it is, the refusal names it and the absent `.ai-review`, and
  nothing is created in the working directory; (j) the archive truncated: `unreadable`, nothing deleted, the
  refusal names the place the folder is in. **In L1 with a partly deleted leftover and a truncated archive the leftover
  stays in `.removing/w00` (not renamed back), `.ai-review/w00` stays absent, and the refusal says the folder may be
  incomplete and that the missing entries exist only in the archive** (LPR-R4-001; mutation m20); with a whole
  leftover in L0 the same truncated archive renames the folder back; (k) the refusal text of (c) and (d) never offers to delete; (l) **the leftover note**: an L1 leftover with a tracked file (selection 7), an unsupported entry (9), `zstd` missing (11) and a held lock (`archive_busy`) each ends with the shared line naming `.removing/w00`.
- **T11 links are not followed:** a symlink to a directory outside the tree is unlinked, the outside tree intact.
- **T12 a failure during the delete:** `os.unlink` raising `EIO` on the third file gives `remove_failed` with the
  message of D-Delete (`.removing/w00`, two entries deleted, `remove w00 --apply`); what was deleted was verified; the
  rerun finishes. A second case: `rmdir` of a nested directory raising `ENOTEMPTY` gives `folder_changed`. Creating
  `.removing` failing gives `place_failed`, and a hook that makes `.removing/w00` appear after selection 8 gives
  `leftover_conflict` (D-Flow 3).
- **T14 an interruption at every transition:** the seams (`_rename`, `os.fsync`, `os.unlink`, `os.rmdir`, the
  `zstd` stand-in) raise `KeyboardInterrupt` once, at each of: before the outward rename, after it, after the compare,
  after the second unlink, after the last `rmdir`, after the rename back. Each leaves L0, L1, L1, a smaller L1, removed,
  or restored (never a rename back on an interruption), with no entry lost (the T7 subset rule); a rerun reaches removed or restored.
- **T15 failures after a completed step:** `_rename` raising `EIO` on the rename back: `restore_failed` naming
  `.removing/w00`; `os.fsync` failing after the outward rename: `place_failed` naming `.removing/w00` as the folder's
  place, the rerun finishes; after the rename back: `restore_failed` naming `.ai-review/w00`; after the last `rmdir`:
  `remove_failed` saying the folder is deleted. None says "nothing was kept".
- **T13 the report and the CLI:** `removing` empty, listing a leftover, and a symlinked `.removing` as a
  `read_errors` entry, after which `archive` and `remove` both refuse `unreadable` (never `archive_dir_unsafe`), `remove`
  with a next step that speaks of removing; `main(["remove", ...])` text and `--json`, exit codes, usage errors.

**The failure-only mutations** (each fails a named case in a scratch copy; the control passes): m1 delete without the comparison (T3); m2 compare listings only (T3a, T10c); m3 the resume path deletes without
comparing (T10c); m4 rename back without the `lstat` guard (T6); m5 no per-entry check in the delete (T7); m6 no
identity check (T8); m7 follow symlinks in the delete (T11); m8 a copy fallback on `EXDEV` (T5); m9 no index
validation (T4 half line, T10g); m10 no lock (T4 `archive_busy`); m11 no `tracked_files` check (T4 gitlink); m12 the dry
run renames (T1); m13 `.removing` left behind by a refused run (T5); m14 the resume renames back over `.ai-review/<id>`
(T10e); m15 `allow_missing` also forgives an extra entry (T10d); m16 a fresh run uses `allow_missing` (T3c); m17 a write
injected only into the refusal handler (T3, T15); m18 a removal injected only into the handler of a failing delete
(T7, T12, T14); m19 the rename back passes `None` as the destination (T10i); m20 an L1 `unreadable` renames the partial leftover back (T10j). Results
are recorded in `TEST_RESULTS.md`. **The corrected snapshot rules (EPR-016) loosen no failure-only mutation:** each of m1 to m20 is re-run
against the corrected assertions and still fails its named case (m13 against the container rule: T5's `EXDEV` and T3's fresh mismatches assert `.removing` absent, m17/m18 against the
strict file and entry comparisons), and the control passes.

**No process left behind.** The new class and the whole obligations chunk run under the Manager's orphan wrapper
(`tests/parallel/reaper.py`, form in `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md`): no orphan beyond Git's own
maintenance. A failed compare reaps its `zstd` child (`_reap`); T9 asserts every child is gone.

### D-Docs: where it is described

`docs/RETENTION.md` gets a section "The remove command": the command, the dry run, D-Selection's order, D-Flow in
words, the leftover table with one next step per state (a stopped delete and a partial leftover renamed back included),
the new codes, the JSON, D-Residual, the report's `removing` key, the archive table's new `unreadable` cause, and the downgrade note (D-Release: an older release does not see `.removing/<id>`; inspect and preserve it by hand). **Every
reference to rows 27c to 27f is re-read** (grep `27[a-f]` line by line): the intro, the archive section's "Removing the
folder is a later row (27d)", the review-folder paragraph ("deleting it ... is row 27d's") and the report's JSON shape.
No page names an internal milestone id or lists governing versions. `docs/exit-codes.md` gets the `remove` rows; "Last
checked with" lines move at CP2 only. `docs/ROADMAP.md` is written **with this plan** (27d Current with the chosen
design; 27e and 27f consistent), never by a checkpoint.

### D-Release: 2.22.0, `feat:`

`manifest.json` 2.22.0, **no record added** (counts 81, 6 and `distribution` 55). The records that move are the script,
`workflow_state_completion_obligations_test.py`, `workflow_protocol.py` (`WORKFLOW_RELEASE` and nothing else),
`workflow_protocol_test.py` (its two pinned assertions) and `ORCHESTRATION_PROTOCOL.md` (tested releases, envelope
example, protocol note; the protocol version stays 1.5), each with a `retention-removal (workflow-2.22.0)` sentence
true of that file. `manager.conformance.suites` are measured, never typed. `min_manager_version` stays 1.13.0.

**Downgrade posture.** 2.22.0 writes no state key, phase, trailer, command file or protocol field, and adds one
report key. The 2.20.0 report and the 2.21.0 archive read no `.removing` at all: against the shipped 2.21.0 code a
symlinked `.removing` gives `complete: true`, no `read_errors`, and `already_archived` from `archive`; the `unreadable`
refusal for a broken `.removing` is **new in 2.22.0** and goes away with it. A downgraded release therefore has no
`remove`, **neither detects nor resumes a leftover, and does not tell the operator one exists**: after a killed or
stopped removal and a downgrade, the folder (whole or smaller) sits in `<archive-root>/<repo>/.removing/<id>/`
unseen. The operator must inspect `.removing/<id>` and preserve it by hand (`mv` it back to `.ai-review/<id>`, or keep
it), and must not delete it as archive-store clutter: it may hold entries that exist only there or only in the archive
(D-Restore). The documents say so (`docs/RETENTION.md`, the release-history row).
`tools/release/release_test.py` gets a 2.22.0 class and the 2.21.0 class stops pinning the current version, constant,
"Last checked with" lines and posture. `docs/release-history.md` gets the 2.22.0 row (#116 item 7, the subcommand, a dry
run by default, removes only after the contents are verified, needs `zstd`, adds no command, the way back and the downgrade note above).

### D-Staging: scratch staging for CP1

CP1 changes two shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage its
tree. CP1 verifies in a disposable clone under `$TMPDIR`
(`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w29-tmp`):
a scratch script recomputes `sha256` and `size` of the two changed `artifacts` records, rewrites
`manager.conformance.suites` by the discovery `release.py manager-block --release-dir <scratch> --write` uses, commits
in the clone, and runs the "Verification commands" of `docs/RELEASING.md` from there. No rationale is touched; the
counts (81, 6, 55) stay true. A `tools/release` failure is a stop for the plan, never patched around, and no test is
skipped. Those tests run with the zlib-ng interpreter
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions

No row of `docs/TECHNICAL_DECISIONS.md` is touched. Reversible: the resume forgives missing entries and the fresh run
does not; the report gains one additive key; `.removing` stays, empty, after a success.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The removal, its tests and the documents | - | 3 | 1 |
| CP2 | Release 2.22.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The removal, its tests and the documents

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`, `docs/exit-codes.md`.

- **The script** (D-Surface to D-Restore): `_select_finished` extracted from `archive_item` with the descriptor ownership of section 2 and
  the command name in the `unreadable` next step (selection otherwise unchanged), the `remove` subcommand, `remove_item`, `_archive_table`, `_hash_folder`, `_differences`, `_remove_tree`, the restore, the report's
  `removing` key and the text lines; stdlib plus `workflow_forge`, still `# state_writer: false`. **Done:** every case
  of D-Tests passes and the existing `RetentionArchive` and `RetentionReport` cases pass unchanged (the report cases
  that compare a whole report gain the key only).
- **The tests** (D-Tests): written first; each mutation m1 to m20 fails at least one named case in a scratch copy and
  its result is recorded.
- **The documents** (D-Docs). `check_docs.py` stays clean. **Done:** `grep -nE '27[a-f]' docs/RETENTION.md` read line
  by line against the roadmap rows shows no sentence naming a row for a duty it does not carry; the "Last checked
  with" lines are unchanged. **No other mechanism:** `git diff 0c06330 --stat -- payload` lists the script and its
  test file only.

**Verification:** D-Staging in a disposable clone: the nine suites, the new class and the whole obligations chunk
under the orphan wrapper, the `tools/release` and `tools/docs` tests (zlib-ng interpreter, no patch),
`check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.22.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.22.0 with its two pinned assertions and the matching `ORCHESTRATION_PROTOCOL.md` edits
  (protocol version stays).
- `manifest.json` 2.22.0 (D-Release): `workflow_version`, `sha256`, `size` and sentence of every changed record, counts
  unchanged, the posture, `conformance.suites` measured by `release.py manager-block --release-dir <scratch> --write`
  from a staging of CP2's own content.
- `docs/release-history.md`: the 2.22.0 row and its "Last checked with" line; those of `docs/RETENTION.md` and
  `docs/exit-codes.md` move to 2.22.0.
- `tools/release/release_test.py`: a 2.22.0 class; the 2.21.0 class keeps what stays true of it.
- `docs/ROADMAP.md` is not written by this checkpoint: row 27d becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block` and `tools/docs` are clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 27d | the removal: fresh re-derivation, rename aside, contents verify, delete or rename back, leftover | CP1 | D-Selection to D-Leftover |
| Row 27d | never an open item, `kept_recent`, a tracked file or anything outside the folder; never without a verified archive | CP1 | I2, I3, D-Selection 4, 6, 7 |
| EPR-001 | a renamed directory replaced by another; a file added after the last check deleted unarchived | CP1 | D-Flow 4, D-Delete, T7, T8 (section 8) |
| EPR-010 | a changed same-size file survived a listing; recovery must compare contents and handle a partial index line | CP1 | D-Compare, D-Selection 6, T10c, T10g (section 8) |
| Rows 27e, 27f | the user-only command (calls `archive` then `remove`) and the user-only prune | **not here** | later rows |
| Roadmap, release | 27d Current with this design; 2.22.0 bookkeeping | this plan; CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-removal-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; every path a checkpoint's **Files** names is classified at both
stages (`assert_plan_artifact_declaration_coverage`, which reads those paragraphs only), and the scopes of section 1
are written as classified prefixes or exact files, never as a bare directory.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands". **Never run `--apply` against the real repository.**

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`), from `$TMPDIR/fixture/scripts` | `python3 -B -m unittest -v workflow_state_completion_obligations_test.RetentionRemove` passes, `RetentionArchive` and `RetentionReport` unchanged, the whole chunk under the Manager's orphan wrapper reports no orphan beyond Git's own detached maintenance, and the nine suites of `manager.conformance.suites` pass |
| f2 | a scratch copy of the staged fixture, one mutation at a time | each of m1 to m20 makes the named case fail; the control run passes |
| f3 | the checkout (zlib-ng interpreter for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f4 | a **scratch repository** (`git init` under `$TMPDIR` with a `github.com` origin, a hand-built state of five finished items and one open, a `.ai-review/<id>/` folder each with files, a nested directory and a symlink) with a fake forge returning `merged`, and a **real archive made by the engine** (`archive <id> --apply`) | **the dry run changes nothing:** `remove <id>` prints the entries and `matches`; hashes of the repository, the folder and the archive store are identical before and after |
| f5 | the same scratch repository | **apply removes only that item's folder after the verify:** `remove <id> --apply` ends with `.ai-review/<id>` gone, the other folders, tracked files, state, archive bytes and mtime and index identical, `.removing` empty, and the report listing the item as finished with an archive and no folder |
| f6 | the same scratch repository | **a file changed after archiving refuses and loses nothing:** edit one file (same size, mtime restored), `--apply` exits 2 `archive_mismatch` naming it, the folder is back in place byte for byte, `.removing` (and so `.removing/<id>`) is absent |
| f7 | the same scratch repository, a stand-in `zstd` that sleeps in `-dc`, the process group killed once `.removing/<id>` exists | **a leftover from a killed run is handled:** the report lists it under `removing`, the next `remove <id> --apply` completes it; a second kill followed by an edit of one leftover file ends with the folder renamed back and the difference named |
| f8 | the same scratch repository | **an open item and a `kept_recent` item are refused** (`not_finished:open_phase`, `kept_recent`), as are `runtime`, an unarchived item (`not_archived`), a tracked gitlink at the item root and a half index line; each exits 2 and writes nothing |
| f9 | the checkout | `git diff 0c06330 --stat -- payload` lists the script, its test file, the release constant and the CP2 files of D-Release only; the 2.22.0 history row, the manifest and `docs/RETENTION.md` agree on the version |

## 8. Answers to the carried obligations

**EPR-001** (a renamed directory replaced by another populated one was deleted; a file added after the last check was
deleted unarchived). The first half: the design never deletes by the name the repository knows. The folder is moved to
a name only this tool uses and its identity (`st_dev`, `st_ino`) is compared (D-Flow 4); a different directory at
`.removing/<id>` is neither deleted nor renamed back (T8). The second half: each entry is compared with its verified
record at its own unlink and a new or changed one stops the walk and is kept (T7). A write between one entry's `lstat`
and `unlink` is the residual of D-Residual.

**EPR-010** (changed same-size bytes survived a listing and recovery deleted them; a partial index line). Recovery
compares SHA-256 contents with the archive and deletes only what matches (D-Compare, T10c); a different leftover is
renamed back and the difference named. A partial index line stops every run at selection 6 before anything moves, on
the fresh path and the leftover path alike (T4, T10g).
