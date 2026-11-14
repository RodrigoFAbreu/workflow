# W51: Workflow 2.29.4 — the remaining error paths of the retention engine are named refusals (Revision 3)

- **Work item:** `retention-engine-error-paths-2` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner standing order of 2026-11-14 (queue the open follow-up
  issues; substance first): row 44 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#119 items 1 and 3, #149 items 1, 2 and 5, #143 item 4. **Branch:**
  `milestone/retention-engine-error-paths-2`
- **Base commit:** `522e518241f9535c067d52b6e669acdb3467c8b4` (main after #180: release source and own installation are
  2.29.3; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 3. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: every point checked on main (`522e518`)

Each point was read in `payload/scripts/workflow_retention.py` and reproduced with a scratch harness built on the
test file's own `_RM`/`_RP` environments (a hand-built repository, no forge, no network; real `chmod` and injected
errors; Python 3.14, and 3.12 for the `os.fwalk` fact). A sweep then failed, with `EIO`, every call of
`os.stat`, `lstat`, `fstat`, `readlink`, `open`, `read`, `close`, `rmdir`, `unlink`, `mkdir`, `fsync`, `link`,
`scandir` and `listdir` made from the engine, one at a time, in `archive`, `remove` (dry run, apply, a leftover) and
`prune`, and listed every run that ended in a traceback. Classes: TRUE-FIX-NEEDED, ALREADY-FIXED, KEEP.

| Point | State on main (file:line) | Class |
| --- | --- | --- |
| #119 item 1: `os.readlink` in `_hash_folder`, in `_scan` (the post-verify re-check) and in `_remove_tree`'s per-entry check | the one `os.readlink` is inside `_readlink_at` (577-591), called by `_scan` (600), `_pack` (670), `_hash_folder` (1384) and `_remove_tree` (1501, with its deleted count); the sweep with `EIO` at every `readlink` ends in a refusal | ALREADY-FIXED (2.25.5) |
| #119 item 1, "and similar calls": the first open of `os.fwalk` | `os.fwalk` opens the top directory outside its `onerror` (CPython 3.12 and 3.14: `PermissionError` raised from the first step, `onerror` never called). Used in `_review_folder` (270), `_walk_folder` (544, behind `_scan`, the pack and `_hash_folder`) and `_remove_tree` (1476). A real `chmod 000` of `.ai-review/<id>` ends the report, `archive` and `remove` in a `PermissionError` traceback (exit 1); in the pack `_pack_to` turns it into `pack_failed` | **TRUE-FIX-NEEDED** (this is also #149 item 5) |
| #119 item 1, "and similar calls": the bare descriptor calls | the sweep: `os.fstat(dirfd)` in `_walk_folder` (566), `os.fstat(fd)` after an open in `_hash_folder` (1388), `_same_device` (1308), `_open_index` (948), `_judge_removal_archive` (1588), `_flow` (1743, 1744); `os.close` in `_hash_folder` (1411), `_archive_table` (1330), `_judge_removal_archive` (1590), `build_report` (414); `os.open` of `/` in `_walk_chain` (842). Each ends `archive`, `remove` or `prune` in an `OSError` traceback (exit 1). They fail only on `EIO`, `EMFILE` and the like, never on a permission, and every one leaves the engine's own recoverable state (a folder in `.removing`, a dropped temporary) | **TRUE-FIX-NEEDED**, by one backstop (D-Stray) |
| #119 item 3: `_flow` step 1 | `_flow` (1746) reports a swapped archive directory, a leftover that appeared (L0 to L1) and one that vanished (L1 to L0) as `place_failed` ("the archive directory or the leftover changed while the lock was taken"); reproduced with a hook after the real `flock` | **TRUE-FIX-NEEDED** (D-Lock) |
| #149 item 1: quadratic search in `_review_folder` | `walk_failed` searches `pending` from the end (259-262) | ALREADY-FIXED (2.25.6) |
| #149 item 2: same-name collision after a symlink changes readability | with `a/zz` a link that opens in the probe and fails in the walk, and `zz` a readable directory: `read_errors` names `.ai-review/<id>/zz`, a wrong directory (the first error is attributed to the pending sibling) | **TRUE-FIX-NEEDED** (D-Collision) |
| #149 item 5: an item folder with mode 000 | as the second row; reproduced for `report`, `archive` (dry run, apply) and `remove` (dry run, apply, a leftover) | **TRUE-FIX-NEEDED** (D-Walk) |
| #143 item 4: `os.read(fd, 1)` at the end of the pack (693) | not a traceback: `_pack_to` catches the `OSError` and refuses `pack_failed` (exit 2; the sweep gives `unreadable` for the data reads and `pack_failed` for this one); its advice ("check free space and the zstd program") is wording, a later item | KEEP |
| #143 item 4, second half: `_tracked_counts` decodes UTF-8 explicitly | a documented limit of 2.25.5 | KEEP |
| #119 item 7 (the prune never prunes an archive listed under interrupted removals) | `removal_interrupted` in `_prune_select` (1879) and the apply re-check (1990) | ALREADY-FIXED |
| #113 and #116 | per their own status comments, every code point is fixed (2.25.5, 2.25.6); the rest is test pins | KEEP |
| #119 items 2, 4, 5, 6, 8; #149 items 3, 4, 6, 7; #143 items 1 to 3; #113 and #116 test and wording points | wording, test pins, docs | **the later item**, not here |

## 1. Goal

Ship Workflow 2.29.4, a **`fix:` patch**: **no path of the retention engine ends in a traceback, or names a directory
the walk did not fail on, where the contract is a named refusal** (exit 2, a `next step:`). Five changes, one theme: (1) an
item folder that cannot be opened is read as unreadable by the report and refused by every walker (D-Walk); (2)
the lock-time recheck of `remove` says `folder_changed` (D-Lock); (3) `_review_folder` never names a directory the
walk did not fail on (D-Collision); (4) an `OSError` no site maps becomes `unreadable` at the end of `archive`, `remove` and `prune`
(D-Stray); (5) the report's own best-effort `close`. No state key, phase, trailer, protocol field or command file
moves, **no new refusal code**, and every output of a path that works today stays byte-identical. The outputs that
change are exactly these, all of which were a traceback (exit 1) except where named: the five above; and the pack's
top-open failure, `pack_failed` today (the one existing refusal that changes, like the pack's `readlink` in 2.25.5);
and `place_failed` of the lock recheck.

### Hard limits (the owner's sizing rule)

- **Two checkpoints** (CP1 the change, its tests and pages; CP2 the release 2.29.4), under about 350 lines of plan. If
  review finds the plan past that, split: the removal flow first (D-Walk for the walkers and `_remove_tree`, D-Lock,
  D-Stray), the report second (D-Walk's report half, D-Collision, the report's `close`).
- This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`,
  `.workflow-manager/`, managed blocks, the conformance workflow) stays untouched; the copies under `payload/` change.
- The destructive-adjacent rule: `remove` deletes untracked folders. No change moves, adds or reorders a rename, an
  unlink or a rmdir, and a refusal deletes nothing beyond what the rename-aside design guarantees (each deleted entry
  proven archived; the rest whole in `.removing/<id>`, which the next run resumes).

## 2. Facts this plan relies on (re-read at `522e518`)

- `_walk_folder` (528) already refuses every failure it meets through its `onerror`, `failed` (`unreadable`, "<name>
  cannot be read: <strerror>"), and `folder_changed` for an entry that vanishes. Its three callers take any
  `RetentionError` down the paths they already have: the archive's `_undo` (a temporary, the directories this run
  created and the lock are dropped); `remove` step 6's rename back for `archive_mismatch`, `folder_changed`,
  `unreadable` and `unsupported_entry`, or, for a leftover not yet compared, the in-place message of step 6.
- `_stopped(code, why, deleted, place, item_id)` (1397) is the refusal of `_remove_tree`; `_review_folder` records an
  unreadable path with `_unreadable(errors, path, exc)` and sets `complete` false; a record whose folder is present
  and incomplete prints "at least N B in M files (partly unreadable)", and `archive`/`remove` refuse `unreadable` for
  any `read_errors` path under the folder (`archive_item`, `_select_removal` step 9).
- The report's walk keeps `pending`, the pre-order of the sub-directories `os.fwalk` can still fail on, because the walk
  reports a failed child by its base name only; `_can_fail_walk` (216) predicts failure (a real directory, an entry that
  cannot be examined, a link whose open fails); a link that opens is dropped silently by the walk.
- Tests: the classes `RetentionReport`, `RetentionReportUnreadable` (its `_Inject` fails `open` of a named
  sub-directory by kind, from the n-th open on), `RetentionArchive`, `RetentionRemove` and `RetentionPrune` of
  `payload/scripts/workflow_state_completion_obligations_test.py`: 97 tests, all green on `522e518`; the injectors
  `_stat_fails` and `_readlink_fails` are the precedent for the new `_fwalk_fails`.

## 3. Design decisions

### D-Walk: the first open of `os.fwalk`, three sites, one helper

`_guard_walk(walk, handle)` is a generator: `yield from walk`; on an `OSError` it calls `handle(exc)`, and raises what it
returns (from None), or ends when it returns None. The three sites wrap their `os.fwalk(...)` call; nothing else
changes in them, so no loop is re-indented.

| Site | `handle(exc)` | Result |
| --- | --- | --- |
| `_review_folder` (270) | `ENOENT`/`ENOTDIR` before the walk yielded anything: `present` false, nothing recorded (as the `stat` branch does for absence); any other errno, or `ENOENT`/`ENOTDIR` after an entry was yielded (a record of `present: false` with files counted would be incoherent): records `_unreadable(errors, folder, exc)`, sets `complete` false; returns None | a vanished folder reads "no review folder"; otherwise the report prints with `present` true, `complete` false, 0 files, exit 0, the incomplete warning, and the read error naming `.ai-review/<id>` |
| `_walk_folder` (544) | `ENOENT`/`ENOTDIR`: `folder_changed`, "<id> vanished while the folder was read", next step "run it again when nothing writes to the review folder"; any other errno: the existing `failed` refusal (`unreadable`, "<id> cannot be read: <strerror>") | `_scan`, `_pack` and `_hash_folder` all refuse. In the pack this replaces `pack_failed` (named above); `remove`'s step 6 renames the folder back or keeps the leftover, as for any walker refusal |
| `_remove_tree` (1476) | `ENOENT`/`ENOTDIR`: `_stopped("folder_changed", "<id> vanished", ...)`; any other errno: `_stopped("remove_failed", "<id> cannot be read (<strerror>)", ...)`; it covers any `OSError` leaving the walk, so it takes the live `deleted` count through the existing `fail` closure, never a value fixed at the walk's start | "stopped after deleting 0 entries, each proven archived; the rest is in `.removing/<id>`", next step "run `remove <id> --apply` again; check the permissions of `.removing/<id>`" (the existing `_stopped` text) |

Why these codes: `unreadable` and `folder_changed` are what the sub-directory failure and a vanished entry already say;
`remove_failed` is what a failed `unlink`/`rmdir` of `_remove_tree` already says for a permission, with the hint.

### D-Lock: `_flow` step 1

The three causes become `folder_changed` (1746), each with its own message and the next step `nothing was moved or
deleted; run it again`: "the archive directory was replaced while the lock was taken"; "`.removing/<id>` appeared while
the lock was taken"; "`.removing/<id>` is gone while the lock was taken, the folder is in `.ai-review/<id>` again".
**Why `folder_changed` and not `leftover_conflict`:** a re-run is the right step in all three (it resumes an appeared
leftover, or removes the restored folder), while `leftover_conflict`'s next step ("compare the two by hand, move one
aside") is wrong for a benign race. The leftover note of `note(exc)` is still appended. Nothing is created or moved
before this check (`created` is false), so the refusal leaves the repository and the store as they were.

### D-Collision: `_review_folder`'s `pending`

`pending` entries become `(path, name, silent)`, `silent` true for a link whose probe opened (such a link is pushed now;
it was not). The walk reports a failure by base name only, and nothing the report can observe afterwards (a probe, a
retry) says which same-name entry failed, so **no success is ever read as proof an entry was passed**. On a failure for
`name`, take the topmost entry with that name. A real entry is used as today. A silent one makes the failure
**ambiguous** (the link's open failed, or a real same-name sibling below it did): it is recorded on the review folder's
own path, which is never wrong, and only that silent entry is popped. **The nearest real same-name entry below it is kept
in place and flagged ambiguous**, never dropped, so `pending` keeps mirroring the walk's pre-order: a later failure for
that name that meets it is recorded on the review folder's path and pops it, and a yield of it pops it as today, so
nothing lower on the stack can be matched in its place (a dropped sibling let a lower `x/zz`'s `EACCES` name a readable
top-level `zz`). Nothing is re-probed, so no parent is opened. Compatibility: the layouts of `test_t4` keep their results except
**one**, "link opens, zz fails" (`a/zz` link, `zz` directory): it named `zz` and now names the review folder, because the
two cases cannot be told apart; its expected tuple is amended and nothing else in the file changes (D-Golden).

### D-Stray: an `OSError` that no site maps

A decorator on `archive_item`, `remove_item` and `prune_archives` (outermost, after their own `finally` closed the
descriptors and released the lock, and after `archive`'s `_undo`) turns an `OSError` into `unreadable`: "<command>
stopped on an unexpected I/O error: <ERRNO> <strerror>" (and the file name when the error has one). `BrokenPipeError` is
not special: the engines write nothing to the terminal (`main` prints). Next steps: archive, "the review folder was not
touched; `report` shows whether the archive was placed; repair the cause, then run it again"; remove, "the review folder may be in the archive directory's `.removing/<id>`, renamed aside and
not yet compared with the archive, so it may hold files the archive does not: keep it, never delete it as clutter; repair
the cause, then run `remove <id> --apply` again, which compares it before deleting anything" (only what holds on every
path: the rename may have happened, the contents are unverified); prune, the existing "run `prune` again for a fresh preview". The report is not wrapped
(its contract is a complete or incomplete report); its one stray site, `os.close(own_fd)` (414), becomes best effort
(`except OSError: pass`, as `remove_item`'s own `finally` does).

### D-Codes

No code is added or re-assigned. Changed outputs: a traceback (exit 1) becomes `unreadable`, `folder_changed`,
`remove_failed` or an incomplete report; `place_failed` of the lock recheck becomes `folder_changed`; `pack_failed` of the
pack's top open becomes `unreadable` or `folder_changed`. Nothing else moves.

### D-Golden: nothing that works changes

(1) The 97 existing retention tests run green, unmodified but for the one tuple of D-Collision. (2) A driver, `golden.py`, runs base (`522e518`
`payload/scripts`) and candidate through `main` over the working paths (the report, text and `--json`; `archive`, dry run
and apply; `remove`, dry run, apply and a leftover resumed; `prune`, dry run and apply; the refusals that exist today:
`not_archived`, `archive_mismatch`, `leftover_conflict`, `cross_device`, `tracked_files`, `unreadable` for a sub-directory,
`remove_failed` for an `rmdir`), normalises the scratch root, and compares stdout, stderr, exit code and the tree and
store hashes byte for byte. (3) **Pins of the old bytes, listed:** no test or page asserts `place_failed` for step 1 (the
tests that assert `place_failed` are the `.removing` creation at 6939 of the test file and the fsync cases at 7127 and
5868-5910, none of which changes); the pinned layouts of `test_t4` are kept except the one D-Collision amends; no test or page
asserts a traceback for any changed path; `docs/RETENTION.md` and `docs/exit-codes.md` name the old behaviour nowhere
for these paths. In `tools/release/release_test.py` the 2.29.3 class pins the current release (moves in CP2), and the
2.25.6 class pins `docs/RETENTION.md`'s stamp (3439), which moves in CP2 with the page.

### D-Tests

Written first, red against the unedited tree, in one new class, `RetentionErrorPathsTwo`, built on `_RM`. Injectors:
`_fwalk_fails(site, err, skip=0)` patches `os.fwalk` with a wrapper that, when `site` is the **driving** caller, returns a generator raising `OSError(err)` on its first step, after `skip` calls
passed (the immediate caller of `os.fwalk` is `_walk_folder` for `_scan`, `_pack` and `_hash_folder`, so the wrapper walks
up from it, past `_walk_folder` frames, to the first other function and matches that; every test asserts the injector
fired, so a mismatched `site` is a failure and not a pass); `_hook_after_flock(effect)`
patches `wr.fcntl.flock` to run `effect` after the first real exclusive lock; `_fails(fn, site, err, skip)` patches
`os.fstat`/`os.close` for the calling function `site`. Real `chmod` variants run when not root; the injected ones always. Each
test asserts the exit code and stable code, the message and `next step:`, **no write and no removal** (`snap()` of the
repository and store identical, no archive, partial or index line, the folder where the design says, `rr.unlinks` as
stated, no descriptor left open, the lock released by a later run that succeeds).

| Test | Proves |
| --- | --- |
| T1 | report: the item folder's first open fails (`EACCES` real and injected): exit 0, `complete` false, one `read_errors` entry naming `.ai-review/w00`, the text line "at least 0 B in 0 files (partly unreadable)", the incomplete warning, `--json` shape, nothing written; a sibling item is still counted; `ENOENT`/`ENOTDIR`: "no review folder", no read error, complete |
| T2 | `archive` (dry run, apply) and `remove` (dry run, apply) with the folder unreadable (real `chmod 000`): exit 2 `unreadable` through the report's `read_errors` rule; `remove` of a leftover (`.removing/<id>` mode 000; the report never walks it): exit 2 `unreadable` through `_scan`'s `_walk_folder` handle ("<id> cannot be read: ..." with the leftover note); in all, nothing written, nothing moved, a later run after the mode is restored succeeds |
| T3 | `_walk_folder`'s three callers through `_fwalk_fails`: `_scan` at the archive selection and the re-check after the pack (`_undo` runs: no `.partial`, no archive, no index line, lock released), `_pack` (`pack_failed` on the baseline, `unreadable` now; `ENOENT`: `folder_changed`), `remove`'s selection, the re-selection under the lock, `_hash_folder` after the rename (the folder renamed back, `.removing` dropped, the message says where) and the leftover case (kept in place, step 6's text) |
| T4 | `_remove_tree`'s top open after the verify (`EACCES`, `EIO`: `remove_failed`, "<id> cannot be read"; `ENOENT`: `folder_changed`), and an `EIO` raised mid-walk after `k` unlinks (the live count, "stopped after deleting k entries"); with the top open: "stopped after deleting 0 entries", `rr.unlinks == []`, the folder whole in `.removing/w00`, the permissions hint; the run without the injector finishes the removal |
| T5 | step 1: the archive directory swapped for a copy with a new inode, a leftover that appears, a leftover that vanishes: `folder_changed`, the three messages, `renames == []`, `unlinks == []`, store identical, the leftover note present when one exists; a later run succeeds (resumes in the second case) |
| T6 | `_review_folder` collision, `{a/zz: link, zz: dir}`: (a) the link's walk open fails once and the sibling `zz` is readable (a later retry would open: the case a re-probe misreads): the review folder's path, never `zz`; (b) the link fails and `zz` fails too: one entry, the review folder's path, no `zz`; (c) the link opens and `zz` fails: the review folder (the amended `test_t4` tuple); (d) a later failure that meets the kept, flagged real sibling after (a): the review folder; (e) the three-level layout `x/a/zz` (a link whose open fails once), `x/zz` (a directory that cannot be opened), `zz` (readable): `.ai-review/w00/zz` is never named; in every case no entry names a path that did not fail |
| T7 | the backstop, **one test per decorator**, each through `main`, exit 2 `unreadable`, the message names the errno, the next step is the command's: (a) `archive`: `os.fstat` in `_open_index` at the apply (948), no partial, no archive, no index line, lock released; (b) `remove`: `os.fstat` in `_same_device`, in `_flow` (1743), in `_judge_removal_archive` and `os.close` in `_judge_removal_archive` (1590), all before the rename, and `os.fstat` in `_hash_folder` after the rename with an unchanged folder: the folder whole in `.removing/w00` and the next run finishes the removal; (c) `prune`: `os.open` of `/` in `_walk_chain` (842), reached through `_select_destination` (1871), red on the base, never the report's best-effort `close`, nothing removed that was not reported. The `os.close` in `_archive_table` is not injected (D-Staging) |
| T9 | I2: after `archive`, a file is added (and, in a second case, one changed) in the review folder; `os.fstat` fails in `_hash_folder` after `remove`'s rename: exit 2 `unreadable`, the message says the folder may be in `.removing/w00`, unverified, and **never** claims the archive holds every entry (no "archived", "holds every" or "proven"); the folder whole with its extra file; the next run without the injector refuses `archive_mismatch`, renames back, deletes nothing |
| T8 | the report's `os.close(own_fd)` failing: the report still prints, exit 0, nothing written |

**Failure-only mutations** (each on a scratch copy; the named tests fail there, and pass on the real file; results go in
the implementation bundle's `TEST_RESULTS.md`): m1 `_review_folder` without `_guard_walk` (T1, T2); m2 `_walk_folder`
without it (T3); m3 `_remove_tree` without it (T4); m4 the mapping of `ENOENT` inverted in `_walk_folder` (T3); m5 step 1
back to `place_failed` (T5); m6 step 1 uses `leftover_conflict` (T5); m7 a silent match is skipped like a passed one, or retried (T6 a); m8 the real sibling is dropped through again, or not flagged (T6 d, e); m9 `silent` entries not
pushed (T6 c, a); m10 each of the three
decorators removed (T7 a, b, c, each failing its own); m12 the remove stray message restored to claim the archive holds every entry (T9); m11 `os.close(own_fd)` unguarded (T8).

### D-Docs

`docs/RETENTION.md`: the archive and remove tables gain "an item folder that cannot be opened" (`unreadable`;
`folder_changed` when it vanished; a traceback before Workflow 2.29.4), the report section says such a folder reads as
partly unreadable, the remove text names the stop of `_remove_tree` at the top, the `folder_changed` of the lock recheck
(it was `place_failed`), and the unexpected I/O error. `docs/exit-codes.md`: the archive, remove and prune rows say the
same in a clause each. No page names an internal milestone id; the stamps move in CP2.

### D-Release

2.29.4, a **`fix:` patch** (as `docs/RELEASING.md` requires, the manifest's version change and the pull request title
agree). `manifest.json` `workflow_version` 2.29.4; the changed records (`workflow_retention.py`, the test file,
`workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`) take their sentence, `sha256` and `size`; counts and
`distribution` do not move; `conformance.suites` is measured by `release.py manager-block --write`. `WORKFLOW_RELEASE`
becomes 2.29.4 with its pinned assertions and the protocol document's example (the protocol stays 1.5).
`tools/release/release_test.py` gets a 2.29.4 class; the 2.29.3 class gives up the current-release pins; the 2.25.6 class
gives up the `docs/RETENTION.md` stamp. `docs/release-history.md`: the 2.29.4 row (the way back to 2.29.3 restores the
tracebacks, `place_failed` and `pack_failed`; archives and engine data are unchanged). The release workflow publishes it;
the Manager lock and install pull requests follow (done by the orchestrator).

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies
in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w51-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256` and `size`
of every `artifacts` record whose file differs from its record (no record is added, so counts and release-test counts do not
move), measures `conformance.suites` with `release.py manager-block --release-dir <scratch> --write`, commits in the clone, and
runs the "Verification commands" of `docs/RELEASING.md` from there; the `tools/release` tests run with the zlib-ng
interpreter `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
The new tests also run under the Manager's orphan rule (the reaper): each test that starts `zstd` waits for it. One existing
limit is kept, not fixed: a failing `os.close(rfd)` in `_archive_table`'s `finally` runs before the `try/finally` that
reaps, so a started `zstd` is not waited for there; no test injects at that close, and the guarantee covers every other path. CP2's stock
`stage-conformance` run is the real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **#149 item 5 is included** though the order names #149 items 1 and 2: it is the one traceback a person can cause with
  `chmod`, and the same missing `onerror` (D-Walk). Striking it leaves the first row of section 0 open.
- **The backstop (D-Stray) over a site by site fix** of the exotic descriptor calls: eleven sites that fail only on `EIO`/
  `EMFILE`, each leaving recoverable state; a site by site fix would be eleven helpers for no case a person can reach. The
  cost: its message names the errno and not the place.
- **`folder_changed` over `leftover_conflict`** for the lock recheck (D-Lock), for the next step it carries.
- **Pack `pack_failed` to `unreadable`** for the top open: the one existing refusal that changes (D-Codes), consistent with 2.25.5.
- **An ambiguous collision names the review folder** (D-Collision), at the cost of one existing layout's more specific
  path; the alternative, a retry that proves nothing, can name a wrong directory.
- **`os.read(fd, 1)` stays `pack_failed`** (KEEP): it is a named refusal; its advice is a wording point of the later item.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The walks, the lock recheck, the collision, the backstop, tests and pages | - | 3 | 1 |
| CP2 | Release 2.29.4 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The walks, the lock recheck, the collision, the backstop, tests and pages

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): T1 to T9 written and run red against the unedited tree; mutations m1 to m12 each fail the named
  tests in a scratch copy and the results are recorded; `golden.py` (D-Golden) is run on the unedited tree and recorded.
- **The change** (D-Walk, D-Lock, D-Collision, D-Stray): `_guard_walk` and its three sites, step 1's refusals, the `pending`
  triple (no re-probe; the real sibling kept and flagged), the decorator on three functions, the report's best-effort `close`. Every existing test passes,
  unmodified but for the one `test_t4` tuple of D-Collision; the diff of the script touches those places only.
- **The pages** (D-Docs, CP1 part): `check_docs.py` stays clean; "Last checked with" lines are unchanged until CP2.
  `docs/ROADMAP.md` carries row 44 from this plan (`Current`); it becomes Done at acceptance.
- **No other mechanism:** `git diff 522e518 --stat -- payload` lists the script and its test only.

**Verification:** D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`,
`check-manager-block`, `tools/release` (zlib-ng interpreter, no patch, no skip); the new class also runs under Python 3.12
(`/home/rodrigo/.local/bin/python3.12`) as well as 3.14, because `os.fwalk` and `os.walk` differ between them;
`golden.py` identical before and after.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.4

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.29.4 with its pinned assertions and the matching protocol-document edits (protocol 1.5).
- `manifest.json` 2.29.4 (D-Release): `workflow_version`, the changed records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.29.4 row and its "Last checked with" line; those of `docs/RETENTION.md` and
  `docs/exit-codes.md` move to 2.29.4.
- `tools/release/release_test.py`: a 2.29.4 class; the 2.29.3 class gives up the current-release pins and the 2.25.6 class
  the `docs/RETENTION.md` stamp.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build
--commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; the tools tests pass in
the zlib-ng environment; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its `.ai-review/`,
the real archive store, the real forge or the network.** Setup, once, under `$TMPDIR`:

- two copies of `payload/scripts/`: `base/` from `git archive 522e518 payload/scripts` and `cand/` from the working tree;
- a scratch repository with a `github.com` origin and a state of eight finished items plus one open (five archivable),
  `.ai-review/m-1` holding `a.txt`, `b.txt`, `sub/c.txt` and a symlink `ln` to `a.txt`; a scratch `HOME`;
- a **fake `gh`** in `$HOME/wf-fakebin` (mode 0755, not under `/tmp`, `/var/tmp`, `/dev/shm` or `$TMPDIR`, first on `PATH`):

```sh
#!/bin/sh
while [ $# -gt 0 ]; do [ "$1" = "--search" ] && sha="$2"; shift; done
printf '[{"number":7,"url":"https://github.com/acme/widgets/pull/7","state":"MERGED","headRefOid":"%s"}]\n' "$sha"
```

- `inject.py`, kept outside the scratch repository, run as `python3 -I inject.py <scripts-dir> <kind> <args> -- <engine
  args>`: it puts `<scripts-dir>` first on `sys.path`, imports `workflow_retention`, installs one injector, runs `main([...])`
  and prints the exit code. Kinds: `fwalk <site> <ERRNO> <skip>` (the caller `<site>`'s `os.fwalk` raises on its first step, the
  first `<skip>` calls pass), `flock <swap|appear|vanish>` (after the real lock of `remove --apply`: the archive directory
  copied to a new inode; the folder renamed into `.removing`; the leftover renamed back), `fstat <site> <ERRNO> <skip>`,
  `close <site>`, `open <name> <link|dir> <first>` (the report's probe: `open` of that name fails from the n-th call on);
- `golden.py`, which runs the working paths of D-Golden through `main` for base and cand and compares everything byte for byte.

Each flow runs against `base/` and `cand/` from a fresh copy of the repository and store; hashes of the repository, folders
and store are compared before and after. Archives are made with the engine's own `archive --apply`. Flows 1 to 9 are offline;
flows 10 and 11 need the full environment.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | no injection: `python3 -I golden.py base/ cand/` | every output, exit code, tree and store hash identical, byte for byte |
| 2 | as a non-root user, `chmod 000 .ai-review/m-1`; `report` and `report --json` with base and cand; restore the mode | base: `PermissionError` traceback, exit 1. cand: exit 0, a line `m-1: at least 0 B in 0 files (partly unreadable); ...`, the warning `incomplete`, `read_errors` names `.ai-review/m-1`; nothing written |
| 3 | the same mode: `archive m-1`, `archive m-1 --apply`, `remove m-1`, `remove m-1 --apply` (after an archive made before the chmod) | base: traceback, exit 1. cand: exit 2 `unreadable`, `.ai-review/m-1 cannot be read (...)`, a `next step:`; the repository, folder and store identical; after the mode is restored the run succeeds |
| 4 | `inject.py fwalk _scan EACCES 0` with `archive m-1 --apply`; `fwalk _pack EACCES 0` and `fwalk _pack ENOENT 0` with the same; `fwalk _scan EACCES 1` (the re-check) | base: traceback (and `pack_failed` for the pack). cand: exit 2 `unreadable` (`folder_changed` for `ENOENT`), no `.partial`, no archive, no index line, no directory this run created |
| 5 | after an archive: `fwalk _hash_folder EACCES 0` with `remove m-1 --apply` (after the rename), and `fwalk _scan EACCES 0` with `remove m-1` | base: traceback, the folder left in `.removing/m-1` (apply). cand: exit 2 `unreadable`, the folder back in `.ai-review/m-1`, no `.removing`, store identical; the dry run writes nothing |
| 6 | after an archive: `fwalk _remove_tree EACCES 0` with `remove m-1 --apply`; then without the injector | base: traceback. cand: exit 2 `remove_failed`, "stopped after deleting 0 entries, each proven archived; the rest is in", the permissions hint, the folder whole in `.removing/m-1`; the next run finishes the removal |
| 7 | after an archive: `flock swap`, `flock appear`, `flock vanish` (with a parked leftover for the last) with `remove m-1 --apply` | base: `place_failed`. cand: exit 2 `folder_changed` with the three messages, next step `nothing was moved or deleted; run it again`; nothing moved or deleted; a later run succeeds |
| 8 | the layout `.ai-review/m-1/a/zz` a link to a directory, `.ai-review/m-1/zz` a directory; `report --json` with (a) `open zz link 2` (the link fails once, `zz` readable), (b) `open zz link 2` and `open zz dir 1`, (c) `open zz dir 1` alone | (a) base: `read_errors` names `.ai-review/m-1/zz`, a directory that opens. cand: `.ai-review/m-1` only. (b) cand: `.ai-review/m-1`, never `zz`. (c) base names `.ai-review/m-1/zz`; cand names `.ai-review/m-1` (the one amended layout, D-Collision) |
| 9 | `fstat _same_device EIO 0` and `close _judge_removal_archive EIO 0` with `remove m-1 --apply`; `fstat _hash_folder EIO 1` after the rename, once with an extra file added to the folder after the archive (the message says the folder may be in `.removing/m-1`, unverified, and never that the archive holds every entry; the next run refuses `archive_mismatch` and deletes nothing); `fstat _walk_folder EIO 0` with `archive m-1`; `close build_report EIO 0` with `report` and with `prune m-1` | base: traceback, exit 1. cand: exit 2 `unreadable` with the errno and the command's next step, except `report` and `prune` with the `close` error, which run as without it; after the rename the folder is whole in `.removing/m-1` and a run finishes the removal; `archive` leaves no partial |
| 10 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` tests and checker, `check-manager-block` | all pass, no skip |
| 11 | (needs the full environment) the `tools/release` tests with the zlib-ng interpreter; `git diff 522e518 --stat -- payload docs` | all pass; the diff lists in `payload` the script and its test (CP1), plus the protocol script, its test and the protocol document (CP2); no new code in `--help` |

## 7. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #119 item 1 | `readlink` sites already refuse; the first open of `os.fwalk` and the bare descriptor calls become refusals | CP1 | D-Walk, D-Stray, T1 to T4, T7, T8, T9, m1 to m3, m10 to m12 |
| #119 item 3 | step 1's `place_failed` becomes `folder_changed` | CP1 | D-Lock, T5, m5, m6 |
| #149 item 1 | already fixed | - | section 0 |
| #149 item 2 | the collision records the review folder's path | CP1 | D-Collision, T6, m7 to m9 (one existing layout's tuple amended) |
| #149 item 5 | an unreadable item folder is a named refusal or an incomplete report | CP1 | D-Walk, T1 to T3 |
| #143 item 4 | `os.read(fd, 1)` is already a named refusal; the other bare descriptor calls | CP1 | KEEP and D-Stray |
| Row 44 | every working path byte-identical; no new code; a `fix:` patch, 2.29.4 | CP1, CP2 | D-Golden, D-Codes, D-Release |
| Wording, test pins, docs of the same issues | not here | the later item | section 0 |

The artifact declaration `docs/ai-workflow/registry/retention-engine-error-paths-2-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations` and then extended by hand for `payload/`, `tools/`, `fixtures/`, `templates/`,
`manifest.json`, `docs/RETENTION.md`, `docs/exit-codes.md` and `docs/release-history.md`, as the earlier retention items' were;
every path a checkpoint's **Files** paragraph names is classified at both stages.
