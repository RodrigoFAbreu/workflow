# W28: Workflow 2.21.0 — the retention archive engine (Revision 7)

- **Work item:** `retention-archive` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator. It is row 27c of `docs/ROADMAP.md` (status `Current` from
  this plan, `Done` at acceptance). This item re-sliced the rows: 27c is the archive creation (this item), 27d the
  removal of an archived finished item's folder (new, design open), 27e the user-only command with the literal
  confirmation (calls 27c and 27d), 27f the user-only prune (the old 27d, then 27e).
- **Issue:** RodrigoFAbreu/workflow#84 step 3, and the obligations of #113 items 3 and 4.
- **Branch:** `milestone/retention-archive`
- **Base commit:** `f1c78ef9513d0718eb5df8f5dfb5a33557c6bbf0` (main after #115: the release source is Workflow
  2.20.0, and this repository's own installation is the published 2.20.0; automatic gates, default `2.2`, no
  `GATE_POLICY.json`, no backlog file declared, so the prose roadmap applies)
- **Plan revision:** 7. Revision 7 applies round 6 of the local review (LPR-R6-001 to -005: the order of the
  index and archive checks, and the refusal codes and dry-run parity of the walk from the file-system root).
  Revision 6 applies the third round of the manual external review (EPR-006 durability of an
  adopted hierarchy, EPR-011, EPR-012; section 8). Revision 5 applied **one owner decision taken under the sizing rule** (split at the first
  repeated finding class): the external reviewer's rounds 1 and 2 both reported that the destructive removal of
  the review folder cannot be bound to the verified contents (EPR-001, and round 2's EPR-010 on recovery), and the
  plan had grown from 478 to 732 lines. **This item is narrowed to non-destructive archive creation**: it never
  removes, renames, moves or modifies anything under `.ai-review/<id>/` or in the repository. Everything that
  existed only for the removal is deleted (the quarantine, the removal step, the recovery instructions, their
  tests and mutations). The removal is row 27d, a separate item with its own design. The answers to the external
  review are in section 8. Earlier rounds: round 1 of the local review applied in revision 2 (LPR-R1-001 to -006);
  the manual external review of revision 2 applied in revision 3 (EPR-001 to -009); round 3 of the local review
  applied in revision 4 (LPR-R3-001 to -004); the external round on revision 5 applied in revision 6; round 6 of the local review applied in revision 7. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->`
  pair.

## 1. Goal

Ship Workflow 2.21.0, a `feat:` minor, that adds **the archive creation** as a second subcommand of the shipped
script:

```
python3 -I scripts/workflow_retention.py archive <work-item-id> [--apply] [--json] [--archive-root DIR] [--repo-root DIR]
```

Option B of the owner's decision of 2026-10-25, first half: the untracked `.ai-review/<id>/` folder of a finished
item is packed into one tarball **outside the repository**, the tarball is verified, linked into place without
overwriting, indexed, and everything newly created is made durable. **The command then stops.** The folder stays
under its own name, byte for byte, and the report keeps showing the item as finished with an archive present.
Without `--apply` the command is a dry run: it prints exactly what it would pack and where, and writes nothing.

Removing the folder (row 27d, which takes an existing, verified archive as its precondition), the user-only command
with its literal confirmation (row 27e) and the prune (row 27f) are **not** part of this item.

### The invariants (one sentence each)

- **I1. Dry run is the default and writes nothing.** Not the archive directory, not the repository, not the
  state, not a stored fact, not bytecode: on every path of the run, a refusal included. The dry run and `--apply`
  differ only by the archive-side writes (directories, temporary, archive, index).
- **I2. The folder and the repository are read, never written.** Nothing under `.ai-review/<id>/` or anywhere in
  the repository is written, renamed, moved, removed, chmod-ed or re-timestamped by any path of the run, success or
  failure. (A read can move a file's access time on a file system that tracks it; the engine asks for `O_NOATIME`
  and does not depend on it.) A failure leaves the archive directory as it was: the temporary this run created,
  an archive this run placed, the index line this run appended and every directory this run created are removed; a
  file this run did not create is never removed.
- **I3. Only an item the report lists as finished, with a fresh query.** The engine calls the report's own
  `build_report` (a fresh forge query, nothing stored) and acts only on an id in its `finished` list. An open
  item, a `kept_recent` item, an unknown id, a failed or empty query, and a path that is not
  `.ai-review/<id>/` of the repository are refused. It never touches a tracked file.
- **I4. Never overwrite, never re-age.** An existing archive makes the run refuse; the engine never changes an
  archive's modification time after placing it (the report ages archives by it) and never opens one for writing.
- **I5. Nothing outside the folder is read, written or removed by following a link.** A symlink inside the folder
  is packed as a symlink, never followed; the folder, `.ai-review/` and the per-repository archive directory must be
  real directories, and every access, **the report's own traversal included**, goes through a descriptor opened
  without following links (D-Confine); the archive's index is a regular file with one link.
- **I6. The archive is outside the repository.** A destination that resolves inside the checkout is refused in
  both modes (D-Selection step 6).
- **I7. Archived means durable.** The item counts as archived only after the archive, the index line and **every
  directory entry this run created** have been made durable (D-Place); a failure of any of them leaves no half-state.
  Durability of the hierarchy the archive is reached through never depends on who created it: every successful run
  makes the whole resolved chain durable itself (D-Place step 0), directories another, unfinished run created
  included.

### Hard limits (the owner's sizing rule)

- **One mechanism, no protocol or state change.** The change to `payload/` is the script, its tests in the
  existing suite and the release constant. No change to `workflow_protocol.py` beyond `WORKFLOW_RELEASE`,
  `workflow_state.py`, `workflow_forge.py`, `workflow_gate_policy.py`, `WORKFLOW_STATE.json`,
  `WORKFLOW_CONFIG.json`, a phase, a trailer or a command file; no new manifest record, no tenth suite. **If the
  work needs more, STOP and split it into a roadmap row.** CP1 re-checks this: `git diff f1c78ef --stat -- payload`
  lists the script and its test file only.
- **No destructive step.** No removal, rename, move or modification of anything under `.ai-review/<id>/` or in the
  repository, and none is added to this item later: it is row 27d.
- **Two checkpoints** (CP1 the engine, CP2 the release), no more.
- **This repository's own installation stays untouched:** the command files under `.claude`, `scripts`, the managed
  documents of the Workflow, `.workflow-manager`, the managed blocks of `CLAUDE.md` and `.gitignore`, and
  `.github/workflows/workflow-conformance.yml`. The change goes to `payload/`; release bookkeeping to
  `manifest.json`, the user documents `docs/RETENTION.md`, `docs/exit-codes.md` and `docs/release-history.md`, and
  `tools/release/`.

### What is a gate and what is an aid

- **Gates:** the nine suites from a staged fixture, the new tests with their failure-path proofs, the
  `tools/release` and `tools/docs` tests, `check_docs.py`, `check-manager-block`, and the scratch-repository
  functional flows of section 7.
- **Aids (never a stop):** the per-record reading of the manifest rationales against `git diff` (CP2).

## 2. Facts this plan relies on (re-checked against `f1c78ef`)

- **The report** is `payload/scripts/workflow_retention.py` (405 lines, Workflow 2.20.0): `build_report(repo_root,
  *, archive_root, ttl_days, now, run=None, resolve=None)` returns `finished`, `kept_recent`, `not_finished`,
  `archives`, `complete` and `read_errors`; `main(argv, *, run=None, resolve=None, now=None)` has the one
  subcommand `report`, a `RetentionError(code, message, next_step)` refusal printed as `error: <code>: <message>`
  and `next step: ...` with exit 2, and runs as `python3 -I` with `sys.dont_write_bytecode` set and its own
  directory on `sys.path` before the sibling import. Its tests are the class `RetentionReport` in
  `workflow_state_completion_obligations_test.py` (helpers `_RR`, `_rr_item`, `_rr_many`, `_rr_snapshot`,
  `_rr_find_pycache`; the forge seam is `run`/`resolve`, no network).
- **The report's traversal follows a symlinked ancestor.** `_review_folder` (lines 140-175) takes the folder as
  `repo_root / ".ai-review" / id`, calls `os.lstat` on that path and walks it with `os.walk`; both resolve a symlink
  in `.ai-review` itself, so with `.ai-review` linked to a directory outside the checkout the report returns that
  directory's file count and size (the external reviewer reproduced it). The engine therefore cannot call
  `build_report` before it has a validated anchor (D-Confine; EPR-002).
- **The finished set** is the report's: `MILESTONE_COMPLETE` for the item, its parent and its children, a fresh
  pull-request query saying `merged`, not one of the 3 newest. The engine reuses `build_report` whole and
  duplicates none of it. The cost is one forge query per item at `MILESTONE_COMPLETE` (newest first), the same
  as the report.
- **The archive layout** is the owner's: `<archive-root>/<repo>/<id>.tar.zst`, default root
  `~/.local/share/workflow-archive`, `<repo>` the part after the slash of `origin`'s `owner/name`. The report
  reads that file's mtime for the age and lists every `*.tar.zst` regular file of the directory in `archives`. An
  item with its folder in place and an archive present is, for the report, a finished item with an archive: the
  report states both facts and nothing about removal.
- **zstd is not in the Python this Workflow supports.** `compression.zstd` exists only from Python 3.14; this
  machine has Python 3.14.8 and the `zstd` program at `/usr/bin/zstd`. The Workflow ships stdlib-only scripts
  with no declared minimum beyond what they use, so a 3.14-only module would raise the floor of the whole
  distribution for one subcommand. See D-Dependency.
- **`tarfile`** (stdlib) writes and reads a tar stream (`w|` / `r|`) and stores a symlink as a symlink unless
  asked to dereference; it does not compress with zstd before 3.14.
- **The report's tracked count** (`_tracked_counts`, lines 113-125) runs `git ls-files -z -- .ai-review` and counts
  a path only with three or more components (`.ai-review/<id>/<file>`): a tracked entry at the item root itself
  (a gitlink, mode 160000, `.ai-review/<id>`) has two components and counts for nothing, so the report says
  `tracked_files: 0` for it. The engine therefore does its own check (D-Selection step 8).
- **Python's descriptor-relative functions** (`os.open`/`stat`/`mkdir`/`link`/`unlink`/`rmdir` with `dir_fd`,
  `os.fwalk`, `O_NOFOLLOW`) exist on Linux and macOS, not everywhere. `os.walk` and `tarfile.gettarinfo` resolve a
  path string, so a symlink in an **ancestor** of that path (a symlinked `.ai-review/`) is followed by them, and
  `gettarinfo` followed by an ordinary open can follow a link substituted between the two calls. D-Confine exists
  because of both.
- **#113 items 3 and 4** are obligations of this item: names that reach a path (a repository `.`/`..`, a
  symlinked `<archive-root>/<repo>`, the ids `runtime` and `archive`), act only on the report's list, and never
  touch an archive's mtime after writing it.

## 3. Design decisions

### D-Surface: a subcommand, in the existing script

`archive` is added next to `report` in `workflow_retention.py`, with `# state_writer: false` unchanged (it
writes no state). The docstring, the `-I` invocation form, the bytecode rules and the `RetentionError` contract
are the report's. The module gains `archive_item(...)` (importable like `build_report`, under the same bytecode
condition) and `main` dispatches on the subcommand. It takes the test seams `run`, `resolve`, `now` and a new
`zstd` (the executable's path, default the first `zstd` on `PATH`).

### D-Dependency: the `zstd` program, stated and refused clearly

**Decision: the `zstd` executable on `PATH`, driven through `subprocess`; `tarfile` writes and reads the tar
stream.** Why:

- the archive name is fixed by the owner as `.tar.zst`, so the format is zstd; gzip or xz would not be seen
  by the report and would not match the owner's layout;
- `compression.zstd` would make the script need Python 3.14 for one subcommand, while the report runs on any
  Python that has `tarfile`; the program is a smaller, more honest dependency, present in every mainstream
  package set (`zstd` on Debian, Arch, Homebrew);
- `tar --zstd` is not used: GNU and BSD `tar` differ in how they store links and name entries, and the engine
  needs to compare the archive's entries with its own walk. Python's `tarfile` gives one behaviour and is
  testable.

`tar` is a **stream** of the walk piped into `zstd -q -T1 -c` (stdout is the temporary file, opened by the
engine with `O_EXCL`, mode 0600); verification pipes `zstd -dc` into `tarfile` in `r|` mode. When the program is
not found, the run refuses `zstd_missing` with the next step (install `zstd` so that it is on the `PATH`). There
is no command-line flag for another path: only the in-process seam exists, for the tests. The refusal is the
**dry run's** too: the dry run refuses everything `--apply` would refuse before its first write, so an operator
learns of a missing program before the real run. A failed pack or verification reaps its `zstd` child.

### D-Selection: act only on the report's finished list

In order, each a refusal with a stable code and the one next step, none of them writing anything:

1. the id must match `^[a-z0-9][a-z0-9_-]{0,63}$` and must not be `runtime` or `archive` → `invalid_id` (the
   report gets the same rule: those two ids are `not_finished: invalid_id` there too);
2. **the platform**: `os.supports_dir_fd` lists `open`, `stat`, `mkdir`, `link`, `unlink` and `rmdir`, `os.fwalk`
   exists, and `os.O_NOFOLLOW` and `os.O_DIRECTORY` are defined, else `path_unsafe` (the engine will not read or
   write without the guarantee);
3. **the anchor, before anything is read from the source** (D-Confine): `<root>/.ai-review` is opened with
   `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`; a symlink or a non-directory → `path_unsafe` (both modes, nothing read
   through it); absent → no anchor (every folder is absent, step 8 answers); another failure → `unreadable`;
4. `build_report` (fresh query), **given that descriptor** (D-Confine), raises its own refusals (`state_missing`,
   `state_invalid`, `repository_unknown`), which the engine passes through unchanged; a repository named `.` or
   `..` is `repository_unknown` in the report (shared by both subcommands);
5. the id is in `not_finished` → `not_finished:<reason>` (the report's reason, including `query_failed:<code>`
   and `no_pull_request`); in `kept_recent` → `kept_recent`; in neither → `unknown_item`;
6. **the destination, before anything is read from it:** the resolved per-repository directory
   (`os.path.realpath` of `<archive-root>/<repo>`, which resolves every existing ancestor and appends the part that
   does not exist yet) is **the repository root or beneath it** → `archive_inside_repository` (both modes; I6; an
   archive root that is itself a symlink to a place outside the checkout stays allowed, as the owner may set one
   up);
7. **the archive side**: the per-repository archive directory an existing symlink or non-directory →
   `archive_dir_unsafe` (the archive root itself may be a symlink the owner set up; the per-repository directory
   may not), or named by a `read_errors` entry of the report → `unreadable`; **the existing part of the resolved chain**
   (LPR-R6-002) opened from `/` with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, one component at a time, read-only (no
   `mkdir`, no `fsync`; D-Confine): `ELOOP` or `ENOTDIR` on a component → `archive_dir_unsafe`, `EACCES` →
   `unreadable`, and the walk stops at the first missing component; the dry run and `--apply` run this walk alike, so
   the dry run refuses what `--apply` would refuse before its first write; **then, in this order** (EPR-012: the
   two checks that judge the index's integrity come before the archive, because a half line is the more specific
   state and an append after it would merge two records; LPR-R6-001: the archive is judged before the index line,
   so an archived item answers `already_archived`) the index (D-Index) present but not a regular file with exactly
   one link (a symlink, a directory, a FIFO, a hard-linked file) → `index_unsafe`; an `index.jsonl` with a line that
   is not a JSON object, or whose last byte is not a newline → `index_invalid` (the engine refuses rather than guess
   whether the id is in it); `<id>.tar.zst` present (any kind of file, including a symlink) → `already_archived`;
   the index already holding a line for the id (and no archive) → `already_indexed`; the temporary `.<id>.partial` in the archive directory present (any kind of
   file) → `partial_present`. The dry run reports all of these too, because it runs this step;
8. the folder: not a real directory (`lstat` through the anchor) → `review_folder_absent` (also the answer for a
   symlink); **any tracked entry at the folder's path or beneath it** → `tracked_files` (a tracked folder is not
   the untracked folder this command archives). The engine counts this **itself**, with its own `git ls-files -z --
   .ai-review/<id>` (a path equal to the folder is a tracked entry too: a mode-160000 gitlink at the item root has
   two path components, and the report's `_tracked_counts` misses it); a failed `git ls-files` → `unreadable`. The
   report's `read_errors` naming the folder or a path under it → `unreadable` (the engine does not archive from a
   partial view);
9. the entries of the folder (D-Pack): a socket, FIFO, device, or a regular file with more than one link →
   `unsupported_entry`;
10. `zstd` not found → `zstd_missing`.

The report's own `tracked_files` count keeps its rule: the engine does not depend on it, and its blind spot for a
gitlink at the item root is recorded in #113 (disposition table), not changed here.

**The next steps of the half-finished states.** The folder is never touched, so no run, killed or not, can lose
data; what a killed run (SIGKILL, power loss, a closed terminal) leaves is only archive-side. By what is on disk:

- `partial_present` naming `.<id>.partial` (killed before the archive was linked, or a run still active): confirm
  no other `archive` run is active, remove the named file by hand and run again. The engine never removes a
  temporary it did not create.
- `already_archived`: with the archive's index line present (the ordinary answer to a second run on an archived
  item), the item is archived; nothing to do. With **no line
  for the id** in `index.jsonl`, a run was killed after it placed the archive and before its index line was durable:
  the folder is intact, so compare the archive with it (`zstd -dc <archive> | tar -tvf -`), then remove the
  archive by hand and run again (the engine never rewrites an archive or the index). A `.<id>.partial` beside the
  archive is the same file's second name (a run killed between the link and the unlink) and may be removed.
- `already_indexed` (given only when there is no archive file): the archive was pruned or removed by hand; the engine never rewrites
  the index, so the owner decides.
- `index_invalid`: repair or remove the named line of `index.jsonl` by hand (this is also the state of a run killed
  in the middle of the append, where the archive is already placed too: the index is judged first, so this is the
  code given; after the repair the next run gives `already_archived` and its next step above applies: archived,
  nothing to do, when the repair completed the line, or the no-line case, when the operator removed it).
- `index_unsafe`: the index must be an ordinary file with one link; replace the named path by hand (the engine
  never follows or rewrites it).
- `archive_dir_unsafe` from the chain walk: a component of the resolved archive path is a symlink (swapped in after
  `realpath`) or not a directory; the owner fixes the named component. `unreadable` from it: a component lacks read
  permission for this user (the walk needs it to `fsync` the directory); grant it or choose another `--archive-root`.

The report's own halves agree with the engine on the obligations: a symlinked per-repository directory makes
the report treat every archive as absent **and** record a `read_errors` entry for it (`complete` false), so
neither half reads an archive through a link and the engine's step 7 refuses for the same reason.

### D-Confine: every access is anchored, none follows a link

The engine resolves the repository root once (`os.path.realpath`) and opens `<root>/.ai-review` as D-Selection
step 3 says: that descriptor (`ai_fd`) is the **only** way the engine, **and the report it calls,** reach the
folder. A `.ai-review/` that is a symlink (to a directory outside the checkout, say) makes that open fail, and the
run refuses `path_unsafe` before reading anything: a link in an ancestor of the item's folder is therefore never
followed, which a check of the leaf (`lstat` of `.ai-review/<id>`) cannot see.

**The report's traversal uses the anchor** (EPR-002). `build_report` gains the keyword `review_root_fd=None`. With
a descriptor the report uses it and does not close it; with `None` it opens `.ai-review` itself in the same way,
for the `report` subcommand too. `_review_folder` then reads **only** through that descriptor: the type check is
`os.stat(id, dir_fd=ai_fd, follow_symlinks=False)` and the count is `os.fwalk(id, dir_fd=ai_fd,
follow_symlinks=False)` with the same finished-set rules as today (regular files only, by `lstat` of each name
through its directory's descriptor, a vanished name skipped, a failure recorded in `read_errors`). A `.ai-review`
that is a symlink or not a directory is **not read**: the report records one `read_errors` entry for it
(`complete` false) and every folder is `present: false` (the same treatment as a symlinked per-repository archive
directory); an absent `.ai-review` is plain absence. For every ordinary tree the report's output is unchanged
(A8). This is the one change to the report's behaviour beyond the three name checks of D-Obligations.

Every later operation on the folder is relative to `ai_fd`: the type check, the walk, and each file open
(`os.open(name, O_RDONLY | O_NOFOLLOW | O_NONBLOCK | O_CLOEXEC, dir_fd=<the directory's descriptor>)`, with
`O_NOATIME` added where the platform has it and dropped on `EPERM`, then `fstat` must say a regular file, or the
run refuses `folder_changed`). `tarfile.gettarinfo` is **not** used: it `stat`s by path and a following open can
follow a link substituted between the two, so the engine builds each `TarInfo` itself from the `lstat`/`fstat`
result of the descriptor it opened and passes that descriptor's stream to `addfile`. The archive side has the same
anchor: the resolved real path of `<archive-root>/<repo>` is walked **from the file-system root**, one component
at a time, each opened with `O_DIRECTORY | O_NOFOLLOW` relative to its parent's descriptor; a missing component is
created with `os.mkdir(name, 0o700, dir_fd=parent)` and then opened the same way, and recorded as created by this
run; a component that `mkdir` reports as existing (`FileExistsError`: another run created it between the look and
the call) is **adopted**: opened the same way and not recorded as created. The per-repository directory is opened
with `O_DIRECTORY | O_NOFOLLOW` too. The temporary, the link, the unlink, the index and the lock are all relative
to that descriptor (`adir_fd`). The walk's failures have codes (LPR-R6-002): `ELOOP`/`ENOTDIR` on a component (a
symlink swapped into an ancestor after `realpath`, or a file where a directory was) is `archive_dir_unsafe`, `EACCES`
(`fsync` needs a descriptor opened `O_RDONLY`, which wants read permission on every ancestor, where path resolution
wants only search permission: an execute-only `/home` at 0711 refuses) is `unreadable`, in the dry run through
D-Selection step 7's read-only walk of the existing part of the chain and in `--apply` through the same opens. What
is **not** protected: the operator's own directories above the repository root (their symlinks are resolved once, by
design). A symlink swapped into an ancestor of the archive root after `realpath` is no longer "resolved once, by
design": the walk refuses it as above and never follows it.

### D-Pack: what goes into the tarball

One tar stream, entries sorted by path, names `<id>/<relative path>` (so extraction recreates the folder);
directories, regular files, and symlinks stored as symlinks (the target text via `os.readlink(name, dir_fd=...)`,
never followed); owner ids zeroed and names empty, mode and mtime kept. Each regular file is opened as D-Confine
says and read **once**: the same bytes feed the SHA-256 and the tar member, and the number of bytes read must equal
the `fstat` size taken at the open (a file that grows or shrinks while it is read is `folder_changed`). The walk
is `os.fwalk` through the anchor, sorted, with one difference from the report's: a symlink to a directory is listed
in `dirnames`, not in `filenames`, so the engine also examines every name in `dirnames` and stores one that is a
symlink as a symlink entry (never descends into it). A count of **files** (the index line's `files` and
`review_folder.files`) is of regular files only, as the report counts them, and `bytes` is their summed sizes;
directories and symlinks are listed in `entries` and counted nowhere else. The walk **records** for every entry its
path, type, mode, size, `st_mtime_ns`, `st_ctime_ns`, symlink target and, for a regular file, the SHA-256: this
record (`W1`) is what the archive is verified against. After packing and verifying, the folder is walked again by
stat only and compared with `W1` (path, type, size, `mtime_ns`, `ctime_ns`): a difference is `folder_changed`, so
the archive that is placed is a **consistent snapshot of a folder that did not move while it was read**. (The
`ctime_ns` cannot be set by a program, so an edit that restored the `mtime` still differs there.) Nothing in the
folder is changed by either walk.

### D-Verify: the tarball lists every file

Before anything is placed, verification **reads the archive back**: `zstd -dc` piped into `tarfile` (`r|`),
comparing, in order, each member's name, type, size, symlink target and, for a regular file, the SHA-256 of its
bytes with `W1`. Any difference, an extra member, a missing member or a decompression error is `verify_failed`.
The listing check is the owner's requirement (every file and its size); the hash is added because a truncated or
corrupted tarball whose listing happened to match must still not be placed and indexed as good.

### D-Lock: one writer of the archive directory at a time

The index is shared by every item of the repository, while the temporary names are per item, so two runs for two
items could interleave on the index (EPR-004): run A records the size S, run B appends its line, A's append fails
partway and A truncates to S, which erases B's line, or A unlinks an index it created, which erases B's whole
file. The engine therefore takes `fcntl.flock(adir_fd, LOCK_EX | LOCK_NB)` (on the archive directory's descriptor,
so no lock file is written) **before D-Place's first placing step and holds it until the index is durable**,
which includes any rollback. A run that cannot take it refuses `archive_busy` (next step: another `archive` run
for this repository is active; wait for it, then run again), after removing what it created. The lock serializes
index validation, size capture, append, fsync and rollback across different ids. The dry run takes no lock and
writes nothing. The lock is advisory: it protects against this engine's own concurrent runs, not against another
program that writes `index.jsonl`.

### D-Place: no clobber, mtime untouched, everything durable, then stop

Order, `--apply` only:

0. **the archive hierarchy and its durability** (EPR-006): walk and create the hierarchy as D-Confine says (mode
   0700), then, for **every directory of the resolved chain, from the file-system root down to the per-repository
   directory, whoever created it** (this run, an unfinished run of another process, or an earlier one: a descriptor
   cannot tell, and an adopted or pre-existing entry may not be durable yet), `fsync` the directory itself and then
   `fsync` the descriptor **of its parent**, in order from the root (the entry of a directory lives in its parent;
   `fsync` of the child's descriptor alone does not make that entry durable). No run decides what is durable from
   who created it; the cost is a few `fsync` calls on directories per `--apply`. A failure of any `mkdir` or
   `fsync` here is `place_failed` and takes the undo below, which removes only the directories this run created (an
   adopted or pre-existing directory is never removed);
1. pack and verify into the temporary `.<id>.partial` (D-Pack, D-Verify), created with `O_EXCL` relative to
   `adir_fd`, then the stat walk of D-Pack; then take the lock (D-Lock) and **re-run D-Selection step 7's checks
   under it** through the safe descriptors (the final name absent, the index validated, in step 7's order: `index_unsafe`,
   `index_invalid`, `already_archived`, `already_indexed`, so a run that finished meanwhile is seen);
2. `fsync` the temporary file; place it with `os.link(temporary, final, src_dir_fd=adir_fd, dst_dir_fd=adir_fd)`
   and then `os.unlink(temporary, dir_fd=adir_fd)`: the no-clobber form of a rename (`os.rename` replaces an
   existing file silently, which would break "never overwrites" under a race). `FileExistsError` is
   `already_archived`; any other error is `place_failed`. `adir_fd` is `fsync`ed. The file keeps the temporary's
   mtime: nothing in the engine calls `utime`, `chmod`, `touch` or opens the final file after the link (I4);
3. append the index line (D-Index) and **make it durable**: `fsync` of the index descriptor, and, when this run
   created `index.jsonl`, `fsync` of `adir_fd` as well (the entry of a new file lives in its directory). A failure
   of the open, the write (even partway: `ENOSPC` can leave half a line), the `fsync` of the file or the `fsync`
   of the directory is `index_failed`;
4. release the lock and close the descriptors. **Only now does the run count as archived** (I7): print the result
   and exit 0. The folder was not touched and is still there.

**Undo, for any failure of steps 0 to 3.** In this order, under the lock when it is held: restore the index
(`ftruncate` to the size recorded before the append and `fsync`, or `unlink` the file when this run created it and
`fsync` `adir_fd`), unlink the archive this run placed (and `fsync` `adir_fd`), remove the temporary this run
created, `os.rmdir` the directories this run created, deepest first, each with its parent `fsync`ed afterwards (an
`ENOTEMPTY` there is expected, not an undo failure: another run (another id) placed its archive in the same
per-repository directory meanwhile, so the directory is kept, LPR-R3-004; LPR-R6-005: the same applies across runs in the other direction. If run B
created a directory that run A adopted, and B fails, B's `rmdir` removes the then-empty directory while A is between
step 0 and its temporary, and A's `O_EXCL` create or link then fails with `ENOENT` and becomes `place_failed`. That
is safe, since A never reports success into a deleted directory, and an implementer must not "fix" it by re-creating
the directory without step 0's durability), then release the lock; the exit is the
step's code. If a part of the undo fails, the message says which one and names the file; the folder is never at
risk because the engine never wrote to it. **No half-state** (EPR-006): what this run created is gone, what it did
not create is untouched.

The temporary name is `.<id>.partial` in the archive directory: it does not end in `.tar.zst`, so the report
never lists a half-written file, and it is created with `O_EXCL` (relative to `adir_fd`), so two runs cannot share
it: a second run, or a run after a killed one, finds it in D-Selection step 7 and refuses `partial_present` (and a
collision on the `O_EXCL` open itself, if the file appears between the check and the open, is the same refusal and
leaves the file alone). The cleanup removes the temporary **only if this run's own `O_EXCL` open created it** (a
flag set by that open), never one that was already there. Every failure removes it. The link itself is the second
guard: a final name that appears between the check and `os.link` is `already_archived`.

### D-Index: one line per item, never rewritten

`<archive-root>/<repo>/index.jsonl`, one line per archived item, keys sorted: `{"archived_at": "<UTC>", "bytes":
<archive size>, "files": <count of regular files>, "pull_request": {"number", "url"}, "work_item_id": "<id>"}`. The
report ignores it (it lists only `*.tar.zst`). The prune row never removes index lines. The file is the only record
of an archive once the archive is pruned, so a second line for the same id is refused (`already_indexed`).

**It is opened safely** (EPR-005): `os.open("index.jsonl", O_RDWR | O_APPEND | O_NOFOLLOW | O_CLOEXEC,
dir_fd=adir_fd)` for an existing file, and `O_CREAT | O_EXCL | ...` (mode 0600) when it is absent, which is what
tells the run that it created it. The open refuses a symlink (`ELOOP`); `fstat` on the descriptor must then say a
regular file with `st_nlink == 1`, or the run refuses `index_unsafe` **before any write**. A symlink to another
valid JSONL file, a hard link shared with another path, a directory and a FIFO therefore never reach `write`,
and the outside target is never appended to or truncated by the rollback. The validation of D-Selection step 7
reads the same descriptor under the lock, so the file that was checked is the file that is appended to.

### D-Obligations: the names that reach a path (#113 items 3 and 4)

| Obligation | Where it is met |
| --- | --- |
| a repository name of `.` or `..` | `build_report`: `repository_unknown` (both subcommands) |
| a symlinked `<archive-root>/<repo>` | `build_report`: archives read as absent plus a `read_errors` entry; the engine: `archive_dir_unsafe` |
| the ids `runtime` and `archive` | `build_report`: `not_finished: invalid_id`; the engine: `invalid_id` |
| symlinks inside the folder | D-Pack: packed as symlinks, never followed |
| act only on the report's list, never from a path | D-Selection step 5: the id is looked up in `finished`; no path is accepted |
| never touch an archive's mtime | D-Place and I4; the test compares the mtime before and after the whole run, and a mutation that adds `os.utime` fails it |

### D-Output: JSON, text and exit codes

`--json` prints one object, keys sorted, newline-terminated; without it a text form. Both modes carry the same
facts:

```
{"schema_version": 1, "kind": "retention-archive", "mode": "dry-run" | "apply", "generated_at": "<UTC>",
 "repository": "<owner>/<name>", "work_item_id": "<id>", "pull_request": {"number", "url"},
 "review_folder": {"path", "files" (regular files), "bytes", "entries": [{"path", "type", "bytes"}]},
 "target": {"archive": "<path>", "temporary": "<path>", "index": "<path>"},
 "zstd": "<path>",
 "result": {"archived": false} | {"archived": true, "bytes", "index_line"}}
```

The dry run lists **every** entry (path, type, size), the target, the temporary name and the index file, and ends
with the line "dry run: nothing was written; pass --apply to archive". The apply text ends with "archived; the
review folder was not touched". Refusals print `error: <code>: <message>` and `next step: ...` on standard error,
as the report does.

Exit codes: **0** the dry run was printed, or the item was archived (durably); **2** a refusal or a usage error,
with a code: the report's (`state_missing`, `state_invalid`, `repository_unknown`, `usage`) and the engine's
(`invalid_id`, `not_finished`, `kept_recent`, `unknown_item`, `review_folder_absent`, `tracked_files`,
`unreadable`, `archive_dir_unsafe`, `archive_inside_repository`, `path_unsafe`, `already_archived`,
`already_indexed`, `index_invalid`, `index_unsafe`, `partial_present`, `unsupported_entry`, `zstd_missing`,
`archive_busy`, `pack_failed`, `verify_failed`, `folder_changed`, `place_failed`, `index_failed`). **Every
failure leaves the folder byte-identical under its own name, because the engine never writes to it.**
`archive_busy` is the only code the dry run never gives. The rows go into `docs/exit-codes.md`; the contract of
0 and 2 is the report's.

### D-Writes: nothing is written before `--apply`, and the tests prove it

The dry run runs the report's read-only Git calls and the forge query, reads the folder, and writes nothing: no
temporary file, no lock, no directory creation (the archive hierarchy is created by `--apply` only, mode 0700), no
bytecode (the `python3 -I` form and the import form are the report's, unchanged). **No-write proof (A1, A4):** the
tests hash every file of the scratch repository and of the archive root before and after a dry run and after
**every refusal** of D-Selection, and compare them, with the assertion that the snapshots are non-trivial. **The
folder is never written (A18):** a guard wraps every mutating call of `os` and `shutil` (`rename`, `replace`,
`unlink`, `rmdir`, `mkdir`, `link`, `symlink`, `utime`, `chmod`, `chown`, `truncate`, `write`, `rmtree`, and `open`
with a write flag) and fails the test for any call whose path or descriptor is under the repository root; the
folder's own snapshot (path, type, mode, size, `mtime_ns`, `ctime_ns`, hash) equals the one before, on success and
after every failure of A5.

### D-Tests: in `workflow_state_completion_obligations_test.py`, class `RetentionArchive`

Same scratch repository and forge seam as `RetentionReport` (`_RR`), with a folder of files, a nested directory,
a symlink to a file and a symlink to a directory outside the tree under `.ai-review/<id>/`, and the real `zstd`.
Cases:

- **A1** the dry run lists every entry, path and size, the target and the temporary name, writes nothing, and is
  the default without `--apply`;
- **A2** `--apply` archives the item: the tarball decompresses to exactly the folder (names, sizes, contents, the
  symlinks as symlinks), the index has one correct line, **the folder is still there and identical to its
  snapshot**, and no other folder, no tracked file and no other item's folder changed;
- **A3** the report run afterwards lists the item as finished with its archive present and not prunable, and the
  archive's mtime equals the temporary file's mtime (recorded by wrapping `os.link`), so a mutation adding
  `os.utime` fails;
- **A4** each selection refusal in order (an open item, a `kept_recent` item, an unknown id, a failed query, an
  empty query, `runtime`, `archive`, a folder that is a symlink or absent, a tracked file under the folder, a
  tracked gitlink at the item root (A12), an existing archive, an existing index line, an `index.jsonl` with a line
  that is not JSON (`index_invalid`), a leftover `.<id>.partial` (`partial_present`: the dry run and `--apply` both
  refuse and the leftover is left in place), an unsupported entry, a symlinked per-repository directory, a
  repository named `..`), each with its code, exit 2 and the no-write snapshot proof;
- **A5** each failure path leaves the folder untouched, and the archive directory as it was, proved by the
  snapshot of both before and after: `zstd` missing (`PATH` without it, `zstd_missing`), a `zstd` stand-in that
  exits 1 while packing (`pack_failed`, the child reaped), one that writes a truncated stream and exits 0
  (`verify_failed`), a folder that changes during packing (`folder_changed`, A11), an index that cannot be opened
  for append (a read-only `index.jsonl`: `index_failed`, the placed archive is gone; skipped, with the reason named,
  when the tests run as root), a second run that finds the temporary of another (a real second run while the first
  is held, or a file created between the check and the `O_EXCL` open: `partial_present`, the other's file and the
  first archive untouched), a final name created between the check and the link (simulated by wrapping `os.link`:
  `already_archived`, the file untouched), and an index append that fails partway (a wrapped `os.write` writes
  half the line and raises `ENOSPC`: the file is back to its recorded size, the archive is gone); **interrupted
  runs**, each simulated by stopping at the call and then running again, dry run and `--apply` alike: (i) after
  the temporary is created and before the link: `partial_present`; (ii) after `os.link` and before the unlink:
  `already_archived` with the next step naming the leftover `.<id>.partial`; (iii) after the unlink and before the
  index append: `already_archived` whose next step says the index has no line for the id and the folder is
  intact; (iv) in the middle of the index append (half a line, the final archive also present): `index_invalid`,
  not `already_archived` (the index's integrity is judged first, D-Selection step 7), and after the named line is
  removed by hand the next run gives `already_archived` as in (iii), or, when it is completed into a whole line,
  `already_archived` with the line present (archived, nothing to do). Each changes nothing, the next step
  is the one D-Selection states for it, and following it (removing the named file, or the archive of (iii)) gives a
  state the engine runs again from;
- **A7** a second `--apply` on an archived item (folder still in place, archive **and** a complete index line
  present) refuses `already_archived`, with the "archived, nothing to do" next step, and changes nothing, the
  archive's mtime included; and, as its counterpart, a complete index line for the id with **no** archive file gives
  `already_indexed` with the "pruned or removed by hand" next step;
- **A8** the report halves of D-Obligations (`runtime`/`archive` ids and a repository `..` in the report, a
  symlinked per-repository directory marking `complete` false), the report's anchored traversal (A12) and that
  `report` output for the existing cases is unchanged;
- **A9** a real `python3 -I` subprocess: the dry run on a scratch repository leaves no `__pycache__`, and a run
  with no `origin` exits 2 with `repository_unknown`;
- **A10** determinism: the same folder and a fixed `now` give byte-identical dry-run JSON;
- **A11** **the archive is a consistent snapshot** (what remains of EPR-001 for this item): through the test seams
  (wrapped `os.open`, `os.fsync`, `os.link` that run a hook at that call), a file **added** to the folder, a file
  **changed to the same size with its `mtime` restored by `os.utime`** (the `ctime` still moves), and a file
  removed, each at three moments: while packing (before the file's open), after its read, and after verification
  (the stat walk). Each is `folder_changed`, exit 2, nothing was placed, the archive directory snapshot equals the
  one before, and the folder holds exactly what the hook left (the engine neither restored nor removed anything);
- **A12** **confinement** (EPR-002, EPR-003): `.ai-review/` replaced by a symlink to an outside directory that
  holds a populated `<id>/` and an outside sentinel: `path_unsafe` in both modes, the outside tree byte-identical,
  and **the `report` subcommand returns no file count, size or name from the outside tree** (the sentinel's size
  never appears), records the `read_errors` entry and `complete` false, exit 0; a `.ai-review/<id>/sub` replaced by a
  symlink to an outside directory (packed as a symlink), and a file replaced by a symlink **after the walk and
  before its open** (a hook in the wrapped `os.open`): `folder_changed`, the sentinel's bytes never in the archive,
  **and the read itself observed** (EPR-011: the final assertions alone cannot tell a no-follow open from a followed
  one that the stat comparison catches later): the wrapped `os.open` records every call with its flags and its
  outcome, and the test asserts, before the cleanup runs, that the open of the substituted name raised `ELOOP` and
  that **no descriptor was ever opened on the outside sentinel** (no recorded `fstat` equals the sentinel's inode,
  and a wrapped `os.read` never returned its bytes);
  the per-repository archive directory replaced by a symlink to an outside directory **after the step 7 check and
  before the descriptor open** (a hook): the run fails with the outside tree byte-identical; a **tracked gitlink**
  at the item root (`git update-index --add --cacheinfo 160000,<sha>,.ai-review/<id>` over a populated directory)
  and a tracked file at depth 1 and at depth 3: each `tracked_files` (the gitlink's is the regression: the
  report's own count says 0 for it, and the test asserts both facts);
- **A13** **the destination is outside the repository** (EPR-007): `--archive-root` an existing directory inside
  the checkout, a not-yet-existing child of the checkout, a symlink inside the checkout to a directory inside it,
  and a symlink outside the checkout that points into it: each `archive_inside_repository` in the dry run **and**
  with `--apply`, with the snapshot of the repository unchanged and no directory created; and, as the control, a
  repository root reached through a symlink with an archive root outside it, and an archive root that is a symlink
  to an outside directory, both archive normally; **and the chain walk** (LPR-R6-002): an ancestor of the archive root with mode
  0311 (execute-only; skipped as root, with the reason named) gives `unreadable`, and an ancestor swapped for a
  symlink after `realpath` (a hook between the resolution and the walk) gives `archive_dir_unsafe`; each in the dry
  run **and** with `--apply`, with the no-write snapshot of the repository and the archive root and the folder
  untouched;
- **A14** **the index is shared safely** (EPR-004): two real runs for two items against one archive directory, the
  first held between the recorded size and the append by a hook that waits on an event: the second exits
  `archive_busy` with its folder and the archive directory untouched, the first then fails (a wrapped `os.write`
  raising `ENOSPC` after half a line) and rolls back, and the index holds exactly what it held before; the same
  with an existing index holding another item's line (that line survives byte for byte) and with an index the first
  run created (a second item archived **sequentially** afterwards gets a one-line index, and no earlier line was
  erased); and the control: both items archived one after the other leaves two correct lines. With the lock
  removed, the same scenario loses the second item's line, so the case fails;
- **A15** **the index is a safe regular file** (EPR-005, EPR-011): `index.jsonl` a symlink to another valid JSONL
  file (outside the archive directory, and a file of the repository), a hard link shared with another path, a
  directory and a FIFO: each `index_unsafe` in the dry run and with `--apply`, before any write, the outside target
  and the archive directory byte-identical, the folder untouched; **and, separately, the same substitutions made
  by a hook after the selection checks and before the low-level open** (so the open's own `O_NOFOLLOW` and the
  `st_nlink` check are what refuse them, not selection); and an existing index whose last byte is not a newline
  is `index_invalid`;
- **A16** **everything new is durable before the run counts as archived** (EPR-006): the wrapped `os.fsync`,
  `os.mkdir`, `os.link` and `os.rmdir` record their order, and the test asserts, for an archive root with **two
  missing ancestors and a missing per-repository directory**, `fsync` of each created directory and then of its
  parent (every one), `fsync(temporary)`, `link`, `fsync(archive directory)`, append, `fsync(index)`,
  [`fsync(archive directory)` when the index was created], and only then the exit; an injected `OSError` from each
  of those `fsync` calls in turn (every created directory's parent, the index, the directory after the index was
  created) and from an `os.mkdir` is `place_failed`/`index_failed`, and the undo leaves **no created directory, no
  archive, no index and no temporary** (the pre-existing part of the archive root byte-identical), and the folder
  untouched; **and the hierarchy another run made** (EPR-006, round 3): (a) a hook in the wrapped `os.mkdir` creates
  the next directory itself, with no `fsync`, as an unfinished second run would, just before this run's call, so the
  call raises `FileExistsError` and the directory is adopted; (b) the whole chain exists before the run, created
  and not synced by a stand-in (modelled by an empty `fsync` record); in both, the test asserts that this run
  `fsync`ed **every directory of the chain and then its parent**, from the root, before `fsync(temporary)` and the
  link, and so before the exit; an injected `OSError` from each of those `fsync` calls in turn is `place_failed`,
  nothing is placed, and the adopted or pre-existing directories are still there (only what this run created is
  removed);
- **A17** **the failure-only writes** (EPR-009), by the mutations below, which the snapshots of A4 and A5 must
  catch because they are exercised **only** on the refusal or failure branch they name;
- **A18** **the folder is never written** (D-Writes): the guard and the folder snapshot, on success and on every
  failure of A5.

**The mutations.** Each case is checked by a one-line mutation in a scratch copy of the script and fails there; the
mutations and their results go in the implementation bundle's `TEST_RESULTS.md`:

- the existing set: the cleanup removing a temporary it did not create, a `utime` after the link, `os.rename` for
  `os.link`, a symlink followed, the tracked-file check dropped, the `kept_recent` check dropped, the cleanup of the
  temporary dropped, a write in the dry run;
- **the failure-only set** (EPR-009): (m1) a write that exists **only in a selection refusal's handler** (a file
  created in the archive root or the repository when the refusal is raised) must fail A4's snapshot assertions; (m2)
  a write that exists **only in the pack, verify or index failure handler** (a stray file in the archive directory,
  or a change of the folder's `mtime`) must fail A5's; (m3) any removal, rename or write under the folder, on the
  success path or in a failure handler (an `rmtree`, `rename` or `unlink` of the folder or one of its entries), must
  fail A18's guard and the folder snapshot; (m4) the undo leaving what this run created (the temporary, the archive,
  the index line, a created directory) must fail A5's and A16's;
- **the set of this revision:** (m5) the report's traversal by the path string (`os.walk`/`os.lstat` of
  `repo_root / ".ai-review" / id`) instead of the anchor (A12's report case fails); (m6) the post-pack stat walk
  dropped (A11's third moment fails); (m7) the comparison by size and `mtime` only, without the `ctime` (A11's
  same-size case fails); (m8) `O_NOFOLLOW` dropped from the file open, or `gettarinfo` for the member (A12's
  substituted symlink fails); (m9) the engine's own tracked count replaced by the three-component rule (A12's
  gitlink fails); (m10) the lock dropped (A14 fails); (m11) the index opened without `O_NOFOLLOW` or without the
  `st_nlink` check (A15's post-selection hooks fail); (m12) the `fsync` of the index dropped and (m13) the `fsync`
  of the directory after creating the index dropped (A16 fails); (m14) the `fsync` of a created directory's parent
  dropped, for the per-repository directory and, separately, for an ancestor (A16 fails); (m17) the `fsync`
  skipped for a directory this run did not create (adopted or pre-existing), or for the ancestors above the
  archive root (A16's adoption and pre-existing cases fail); (m15) the destination
  check dropped, or done on the unresolved path (A13 fails); (m16) the per-repository directory opened without
  `O_NOFOLLOW` (A12's substituted directory fails); (m18) the dry run skipping the chain walk, or the walk mapping
  `ELOOP` or `EACCES` to another code (A13's chain cases fail); (m19) D-Selection step 7 judging the index line
  before the archive (A7 fails).

The tests need the `zstd` program: the class is skipped only with `unittest.skipUnless` naming the missing
program, the evidence records `skipped=0`, and the refusal itself (A5) is tested with `PATH` emptied, so it needs
no program.

### D-Orphan: no process left behind

The new tests start `zstd` and `python3` children and wait for them. They run under the Manager's wrapper
(`tests/parallel/reaper.py` of the Manager checkout; the form is in `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md`)
from the staged fixture, then the whole `workflow_state_completion_obligations_test.py` chunk; the reports must
list no orphan beyond Git's own detached maintenance. A failed pack must also reap its `zstd` child (the test
for `pack_failed` asserts the child is gone).

### D-Docs: where it is described

`docs/RETENTION.md` gets a section "The archive command" (the command, the dry run, the steps in order, the lock,
the index and its safety rules, the durability rule, the dependency on `zstd`, the refusals, the half-finished
states and their next steps, **that the folder is never touched and stays**, and that removing it is a later row),
and **every reference to a roadmap row is re-targeted** (grep `27[a-f]` read line by line against the roadmap
rows): the intro paragraph (the archive command is 27c, the removal of an archived folder 27d, the user-only
command 27e, the prune 27f), "none of rows 27b to 27d stores it" (now 27b to 27f), the review-folder paragraph
("the archive command (row 27c) writes that file": the engine does, and it does not delete the folder; the rule's
"only then delete the folder" is row 27d's), guarantee 5's sentence on the user-only step (row 27e, which calls
27c and 27d), and the guarantees paragraph (the engine keeps 1 and, with nothing removed, the last sentence of 4;
5 for the dry run). The "Last checked with" lines of `docs/RETENTION.md` and `docs/exit-codes.md` are **not**
changed by CP1: the 2.20.0 release test asserts them, and CP2 moves them with the release. `docs/exit-codes.md`
gets the rows of the new subcommand. The report's own section of `docs/RETENTION.md` and the `report` rows of
`docs/exit-codes.md` also state the report's four new behaviours (a repository `.`/`..` is `repository_unknown`; a
symlinked per-repository directory is a `read_errors` entry with `complete` false; the ids `runtime` and `archive`
are `invalid_id`; a symlinked `.ai-review` is a `read_errors` entry with `complete` false and is not read), and the
review-folder paragraph's check command becomes the engine's documented one, `zstd -dc <archive> | tar -tf -`. No
page names an internal milestone id, and no list of governing versions is written in a managed document.
`docs/ROADMAP.md` is re-sliced **with this plan** (27c Current, 27d the removal, 27e the user-only command, 27f the
prune) and is not written by a checkpoint; 27c becomes Done at acceptance.

### D-Release: 2.21.0, `feat:`

`manifest.json` `workflow_version` 2.21.0. **No record is added**: the counts stay 81, 6 and `distribution` 55.
The records that move are the script, `workflow_state_completion_obligations_test.py`, `workflow_protocol.py`
(`WORKFLOW_RELEASE` 2.21.0 and nothing else), `workflow_protocol_test.py` (its two pinned assertions) and
`ORCHESTRATION_PROTOCOL.md` (tested releases, envelope example, protocol note; the protocol version stays 1.5).
Each carries a `retention-archive (workflow-2.21.0)` sentence true of that file, beside the 2.20.0 sentence it
already has. `manager.conformance.suites` are **measured, never typed**. `min_manager_version` stays 1.13.0.

**Downgrade posture.** 2.21.0 writes nothing an older release reads: no state key, phase, trailer, commit shape,
guard-body key, protocol field or refusal class changes, no command file is added, and nothing in the Workflow
calls the subcommand. `workflow-manager update` back to 2.20.0 leaves `scripts/workflow_retention.py` with only
`report`; an archive already written stays valid (it is a plain `.tar.zst` file and an `index.jsonl` line, which
the 2.20.0 report lists as an archive and ignores), and no review folder was ever changed. Nothing needs undoing.

`docs/release-history.md` gets the 2.21.0 row (references #84 step 3 and #113 items 3 and 4, names the
subcommand, says it is a dry run by default, creates an archive and an index line and removes nothing, needs `zstd`,
adds no command and changes the report only by the four name and anchor checks, gives the way back) and its
"Last checked with" line. `tools/release/release_test.py` gets a 2.21.0 release class (version, constant, counts
unchanged, the sentences, the posture and history needles); the 2.20.0 class keeps what stays true of it and no
longer pins the current version, constant, pages' "Last checked with" lines or posture.

### D-Staging: scratch staging for CP1

CP1 changes two shipped files, whose records `manifest.json` moves only at CP2, so stock `stage-conformance`
cannot stage CP1's own tree. CP1 verifies in a disposable clone under `$TMPDIR` (`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w28-tmp`):
a scratch script recomputes `sha256` and `size` of every `artifacts` record whose file differs from its record
(the script and the test file only), measures and rewrites `manager.conformance.suites` by the discovery
`release.py manager-block --release-dir <scratch> --write` uses (the new tests change the obligations suite's
count), commits it in the clone, and runs the "Verification commands" blocks of `docs/RELEASING.md` from there.
No rationale is touched. This item adds no record, so the counts the 2.20.0 release class pins stay true; the
scratch commit holds the release source at version 2.20.0, and the class asserts exactly that. Any
`tools/release` failure is a stop for the plan, not something a scratch patch works around, and no test is
skipped, deselected or marked expected-to-fail. The `tools/release` tests run with the zlib-ng interpreter
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices made here that may be reversed:

- **The `zstd` program, not `compression.zstd`.** Reversible by a later release; the archive format is the same.
- **The index is `index.jsonl` in the per-repository directory.** The owner asked for one line per item (id,
  date, size, merged pull request); the format and name were not decided. A line of sorted-key JSON is read by
  the Manager and the Controller without a parser of its own. The prune row must not remove lines from it.
- **Hash as well as listing in the verification.** More than the owner asked (every file and its size); it costs
  one pass over the archive and closes the corrupt-but-matching-listing case.
- **`os.link` then `os.unlink` for the placement**, not `os.rename`: a rename would replace a file that appeared
  after the check. It needs a file system with hard links, which every file system under `~/.local/share` has
  in practice; where it has none the run refuses `place_failed` and nothing is lost.
- **The report gains four checks** (a repository `.`/`..`, a symlinked per-repository directory, the ids
  `runtime`/`archive`, and the anchored traversal of a symlinked `.ai-review`) so that the engine's list and the
  report's agree and neither reads through a link. They change the report's output only for those inputs, which no
  repository has today.
- **The removal is not here.** The owner's sizing rule split it: row 27d, with its own design, takes an existing,
  verified archive as its precondition. Until it ships, a finished item's folder stays after `archive --apply`, and
  the report shows it as finished with an archive present.

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The archive engine, its tests and the documents | - | 3 | 1 |
| CP2 | Release 2.21.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The archive engine, its tests and the documents

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`, `docs/exit-codes.md`.

- **The script** (D-Surface to D-Output, including D-Confine and D-Lock): the `archive` subcommand, `archive_item`,
  the `zstd` seam, the four report checks (D-Obligations and the anchored traversal, `review_root_fd`); stdlib plus
  `workflow_forge`, still `# state_writer: false`. **Done:** every case of D-Tests passes and the report's existing
  `RetentionReport` cases pass unchanged.
- **The tests** (D-Tests): written first; each mutation listed there (the existing set, the failure-only set m1 to
  m4 and every other mutation listed there) fails at least one case in a scratch copy, and its result is recorded.
- **The documents** (D-Docs): the section "The archive command" and the re-targeted row references of
  `docs/RETENTION.md`, and the `docs/exit-codes.md` rows. `check_docs.py` stays clean. **Done:** `grep -nE
  '27[a-f]' docs/RETENTION.md` read line by line against the roadmap rows shows no sentence naming a row for a
  duty it does not carry, and the "Last checked with" lines are unchanged.
- **No other mechanism:** `git diff f1c78ef --stat -- payload` lists the script and its test file only.
- `docs/ROADMAP.md` was re-sliced with this plan; this checkpoint does not write it.

**Verification:** D-Staging in a disposable clone: the nine suites, the new tests and then the whole
`workflow_state_completion_obligations_test.py` chunk under the orphan wrapper, the `tools/release` tests (zlib-ng
interpreter, no patch) and the `tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.21.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.21.0 with its two pinned assertions in `workflow_protocol_test.py` and the
  matching `ORCHESTRATION_PROTOCOL.md` edits; the protocol version stays.
- `manifest.json` 2.21.0 (D-Release): `workflow_version`; `sha256` and `size` of every changed record, each with
  a `retention-archive (workflow-2.21.0)` sentence true of THAT file; counts unchanged; the `manager` block's
  posture rewritten for the minor with the way back; `conformance.suites` measured by `release.py manager-block
  --release-dir <scratch> --write` from a staging of CP2's own content; `min_manager_version` unchanged.
- `docs/release-history.md`: the 2.21.0 row and its "Last checked with" line; the "Last checked with" lines of
  `docs/RETENTION.md` and `docs/exit-codes.md` move to 2.21.0.
- `tools/release/release_test.py`: a 2.21.0 release class; the 2.20.0 class keeps what stays true of it.
- `docs/ROADMAP.md` is not written by this checkpoint: row 27c becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture;
`release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is clean;
`workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 27c | the archive creation: dry run by default, fresh re-derivation, pack, verify, place, index, durable, stop | CP1 | D-Selection to D-Place |
| Row 27c | never touches an archive's mtime, the folder, a tracked file or an open item | CP1 | I2, I3, I4, D-Place, A3, A4, A18 |
| #113 item 3 | repository `.`/`..`, symlinked per-repository directory, ids `runtime`/`archive`, act only on the report's list | CP1 | D-Obligations |
| #113 item 4 | never touch an archive's mtime after writing it | CP1 | I4, A3 and its mutation |
| #113 (new note) | the report's `tracked_files` count misses a tracked gitlink at the item root (three-component rule) | **not here** | the engine counts for itself (D-Selection step 8); the report's count stays open in #113 |
| EPR-002, EPR-006, EPR-011 | rounds 2 and 3 of the manual external review: still apply | CP1 | D-Confine (the report's anchored traversal), D-Place step 0 and undo, D-Tests A12, A15, A16 |
| EPR-001, EPR-010 | round 2: destructive removal and its recovery | **not here** | moot for this item; carried to row 27d as obligations with the reviewer's reproductions (section 8) |
| EPR-003 to -005, -007 to -009 | rounds 1 and 2: resolved protections | CP1 | kept unchanged (D-Confine, D-Lock, D-Index, D-Selection steps 6 and 8, D-Tests A12 to A17) |
| LPR-R3-001 to -003 | quarantine states, rename back, `rmtree` `dir_fd` | **not here** | moot: no quarantine, no removal |
| LPR-R3-004 | `ENOTEMPTY` on the undo's `rmdir` | CP1 | D-Place undo |
| #113 items 1, 2, 5, 6, 7 | text form of unreadable paths, undecodable input, test pins, doc nits, checklist notes | **not here** | stay open in #113 |
| EPR-012 | round 3: interrupted append contradicts the refusal order | CP1 | D-Selection step 7 (`index_invalid` before the archive), A5 (iv) |
| LPR-R6-001 to -005 | round 6 of the local review | CP1 | order of `already_archived`/`already_indexed` (A7, m19); chain-walk codes and dry-run parity (A13, m18); CP1 Done wording; this table and section 8; the adoption note in D-Place |
| Roadmap | 27c archive creation (Current), 27d removal, 27e the user-only command, 27f the prune | this plan | written with the plan |
| Row 27d | removal of an archived finished item's folder | **not here** | new row, design open |
| Row 27e | the user-only command and its literal confirmation (calls 27c and 27d) | **not here** | row 27e |
| Row 27f | the user-only prune | **not here** | row 27f |
| Manager row 17 | `status`/`doctor` calls the script | **not here** | outside this repository |
| Release | 2.21.0 bookkeeping | CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-archive-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its plan-stage
protected paths, and self-review checked that every path named in a Files paragraph, and every other path this
plan names, is classified at both stages and that every deliverable is protected at the implementation stage.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands"; the manifest key is `workflow_version`.
Each flow names its workspace. **Never run `--apply` against the real repository.**

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`), from `$TMPDIR/fixture/scripts` | the new tests pass: `python3 -B -m unittest -v workflow_state_completion_obligations_test.RetentionArchive`, and `RetentionReport` unchanged |
| f2 | a scratch copy of the staged fixture, one mutation at a time | each mutation named in D-Tests makes at least one test fail; the control run passes |
| f3 | the staged conformance fixture | the obligations chunk under the Manager's orphan wrapper reports no orphan beyond Git's own detached maintenance |
| f4 | the staged conformance fixture | the nine suites from the manifest's `manager.conformance.suites` list |
| f5 | the checkout (zlib-ng interpreter for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f6 | a **scratch repository** (a `git init` under `$TMPDIR` with a `github.com` origin, a hand-built state file of five finished items and one open, a `.ai-review/<id>/` folder with files, a nested directory and a symlink for each) and a short script that calls `main(["archive", "<id>", "--repo-root", ..., "--archive-root", "<scratch>"], run=<fake forge>, resolve=<fake>)` from the fixture's scripts (the fake returns `merged` for every anchor except the open item's: it is never queried) | **dry run is the default:** the output lists every entry and the target, the archive root and the repository are byte-identical before and after (`find ... -type f -print0 \| sort -z \| xargs -0 sha256sum` and `git status --porcelain --ignored`) |
| f7 | the same scratch repository | **apply** (`--apply`) archives and **touches nothing else**: `zstd -dc <archive> \| tar -tvf -` lists the folder's files, the index has one line, **the folder is still there and byte-identical (hashes and `stat` mtime and ctime)**, the other items' folders, the tracked files and the state are unchanged, and the report afterwards lists the item as finished with its archive present |
| f8 | the same scratch repository, a stand-in `zstd` first on `PATH` that exits 1 while packing, then one that truncates | **a failure mid-way leaves the archive directory as it was:** the folder is byte-identical, the archive directory holds no temporary file, no archive and no directory this run created, the exit status is 2 with `pack_failed` and `verify_failed` |
| f9 | the same scratch repository | **an open item is refused** (`not_finished:open_phase`), as are a `kept_recent` item, an unknown id, `runtime`, an already archived item (`already_archived`, the archive's mtime unchanged, the folder still in place), a leftover temporary (`partial_present`), and a repository whose per-repository directory is a symlink; each exits 2 and writes nothing |
| f10 | the checkout | `git diff f1c78ef --stat -- payload` lists the script and its test file, the release constant and the protocol document edits only; the 2.21.0 history row, the manifest and `docs/RETENTION.md` agree on the version; the 2.20.0 and older rows are unchanged |
| f11 | the same scratch repository, one setup at a time | **unsafe paths refuse and change nothing outside:** `.ai-review/` a symlink to an outside directory (`path_unsafe`, and `report` lists nothing from it), `--archive-root` inside the checkout (`archive_inside_repository`), `index.jsonl` a symlink to an outside JSONL file (`index_unsafe`, the outside file byte-identical), a tracked gitlink at `.ai-review/<id>` (`tracked_files`); each exits 2 (the report 0), dry run and `--apply` alike, and the outside tree, the repository and the archive root are byte-identical before and after |

## 8. Answers to the reviews (the manual external review of revisions 4 and 5, the local review, and the owner's decision)

**The owner's decision.** Rounds 1 and 2 of the external review both reported that the destructive removal of the
review folder cannot be bound to the verified contents (EPR-001, then EPR-001 again and EPR-010), and the plan
grew from 478 to 732 lines. Under the sizing rule (split at the first repeated finding class), this item is
narrowed to **non-destructive archive creation**: the engine never removes, renames, moves or modifies anything
under `.ai-review/<id>/` or in the repository. The quarantine (D-Quarantine), the removal (D-Remove), the recovery
instructions for source bytes, their tests (A6, the removal moments of A11, the quarantine cases of A5) and their
mutations are deleted. The folder stays; the report keeps showing it as finished with an archive present. The
removal is the new row 27d, with its own design; the user-only command is 27e and the prune 27f (`docs/ROADMAP.md`
re-sliced with this plan; the row references of `docs/RETENTION.md` are re-targeted by CP1, D-Docs).

- **EPR-001 (the quarantine name does not bind removal to the verified contents): moot for this item**, there is
  no removal. **Carried to row 27d as an obligation**, with the reviewer's reproductions, which the 27d design must
  make impossible and test: (a) the verified directory renamed aside and a different populated directory created
  at its name, then the descriptor-relative `rmtree` called: it deleted the replacement directory (its symlink
  protection validates the directory it meets, not the directory previously verified); (b) a file added through the
  quarantine's new pathname after the last check: it was deleted unarchived. Neither needs a descriptor held before
  the rename. Row 27d must bind deletion to the verified directory (identity, not a name) and either specify an
  enforceable source-consistency boundary through the removal or refuse when it cannot be kept.
- **EPR-010 (recovery can delete changed bytes absent from the archive): moot for this item**, there is no
  recovery of source bytes: a killed run leaves archive-side files only, and its next steps never delete anything
  from the folder (D-Selection). **Carried to row 27d as an obligation**: (a) a supported `folder_changed` failure
  followed by a kill left changed same-size bytes in the quarantine while `tar -tvf` still listed successfully, and
  the append-and-remove instructions then discarded the new bytes, so recovery must prove that every entry it deletes
  is represented with matching **contents** in the archive (a listing is not enough) or restore and preserve; (b) a
  partial index line left by an interrupted append must be handled before another append is prescribed (this item
  already refuses it as `index_invalid`, D-Selection step 7).
- **EPR-002 (the report follows the source ancestor before the engine checks it): accepted, still applies.**
  Validated against `payload/scripts/workflow_retention.py` lines 140-175 (`os.lstat` and `os.walk` of a path
  string). D-Selection steps 3 and 4 open the anchor first and hand it to `build_report` (`review_root_fd`), and
  D-Confine moves the report's `_review_folder` onto `os.stat`/`os.fwalk` through it, keeping the finished-set
  rules; packing reads through the same anchor with no-follow opens. A12 proves the outside tree contributes
  nothing to the `report` output; m5 removes the protection.
- **EPR-006 (newly created archive directory entries are not durable): accepted, still applies.** D-Place step 0
  makes every directory this run created durable (the directory and its parent's descriptor) before anything is
  placed, steps 2 and 3 keep the archive and index durability, I7 makes all of it a precondition of "archived", and
  the undo removes what this run created (deepest first) so that no half-state remains. A16 asserts the order with
  two missing ancestors plus the per-repository directory and injects a failure at each `fsync` and `mkdir`; m14
  removes a parent `fsync`.
- **Round 3 (the external review of revision 5; the local approval had passed).**
  - **EPR-006, remainder (a run reports durable success through another run's undurable hierarchy): accepted.**
    Validated by reading D-Place step 0 of revision 5: "an existing hierarchy fsyncs nothing here", so a run that
    adopted directories another run created, or found them already created and not yet synced, never made their
    entries durable. Revision 6 removes the dependence on the creator: D-Confine walks from the file-system root
    and adopts a directory that `mkdir` reports as existing, and D-Place step 0 `fsync`s every directory of the
    resolved chain and its parent, whoever created it; the undo still removes only what this run created. A16 gains
    the adoption case (a hook creating the directory unsynced just before `mkdir`) and the pre-existing case, with
    an injection at each of those `fsync` calls; m17 removes the protection.
  - **EPR-011 (A12 can miss the no-follow mutation): accepted.** A12 now asserts the observed `open` outcome
    (`ELOOP`) and that no descriptor was ever opened on, and no read returned the bytes of, the outside sentinel,
    before the cleanup; m8 therefore fails on a followed open even though the stat comparison would still give
    `folder_changed`.
  - **EPR-012 (interrupted append contradicts the refusal order): accepted.** D-Selection step 7 judges the
    index's integrity first (`index_unsafe`, `index_invalid`) and the archive after, so the half line of A5 (iv),
    with the final archive also present, gives `index_invalid`; the next step and the test agree, and following the
    repair gives the `already_archived` state. (Revision 6 also moved `already_indexed` ahead of the archive; that
    was wrong, see LPR-R6-001.)
- **Local review round 6 (LPR-R6-001 to -005; revision 7).**
  - **LPR-R6-001 (an archived item refused `already_indexed`): accepted.** Validated against step 7 of revision 6:
    after a successful `--apply` both the archive and the index line exist, so the second run stopped at
    `already_indexed`, whose next step says "pruned", contradicting A7, f9 and the `already_archived` next step.
    Revision 7 keeps EPR-012 (only `index_unsafe` and `index_invalid` precede the archive) and restores
    `already_archived` before `already_indexed`; D-Place step 1 re-checks in the same order; A7 gains the
    counterpart (line without archive: `already_indexed`); m19 pins the order.
  - **LPR-R6-002 (the walk from `/` had no code, and the dry run did not walk): accepted.** `fsync` of a directory
    needs an `O_RDONLY` descriptor, which needs read permission on every ancestor. Step 7 now runs a read-only walk
    of the existing chain in both modes (`ELOOP`/`ENOTDIR` → `archive_dir_unsafe`, `EACCES` → `unreadable`), so the
    dry run refuses what `--apply` would; D-Confine's "not protected" sentence is corrected; A13 gains the
    execute-only and swapped-symlink ancestors; m18 pins them. No new exit code.
  - **LPR-R6-003 to -005 (optional): accepted.** CP1's Done wording names every mutation listed; the disposition
    table and this heading are corrected; D-Place's undo states the cross-run adoption case.
- **EPR-011 of round 2 (race hooks for the mutation promises): accepted, applies to what remains.** A12 gains a substitution of
  the per-repository directory after the step 7 check and before the descriptor open, and a file replaced by a
  symlink after the walk; A15 gains the index substitutions made after the selection checks and before the
  low-level open; m8, m11 and m16 pin them. The hooks that existed only for the removal (m5 of revision 4, the
  lock-release hook before removal) are deleted with it.
- **EPR-003 to -005, -007 to -009**: the reviewer found them adequately addressed; they are kept unchanged
  (round 1 protections: index serialization and rollback, the symlinked index refusal, the destination outside the
  repository, the name checks, the gitlink at the item root, the classification of every path the plan names, the
  failure-only write mutations, the no-bytecode proof).
- **Local review round 3 (LPR-R3-001 to -004).** -001 (quarantine states first), -002 (the guarded rename back)
  and -003 (`rmtree` `dir_fd`, Python 3.11) belong to the deleted removal and are moot; -004 (`ENOTEMPTY` on the
  undo's `rmdir`) still applies to the directories this run created and stays in D-Place.
