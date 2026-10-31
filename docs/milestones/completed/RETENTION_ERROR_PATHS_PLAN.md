# W37: Workflow 2.25.5 — an unreadable symlink or an undecodable input is a coded refusal (Revision 1)

- **Work item:** `retention-error-paths` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-10-31 (priority 3): row 32 of
  `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#119 item 1 and #113 item 2. **Branch:** `milestone/retention-error-paths`
- **Base commit:** `69ebb46fae71dd73761624c393b1436be655f044` (main after #141: release source and own installation are
  2.25.4; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. What the order named, checked against main (Workflow 2.25.4), and the split

| Order item | State on main | Disposition |
| --- | --- | --- |
| #119 item 1: `os.readlink` in `_hash_folder` (line 1322), `_scan` (538, run again by `archive` after the pack at 1138, by `remove` at selection and again under the lock (1591, through `_select_removal`) and after the rename at 1745), `_remove_tree` (1435), and in the pack (`_pack`, 608) | **open**: a bare call; an `OSError` ends as a traceback, exit 1 (nothing is deleted), except in the pack, where `_pack_to` (684) already catches the `OSError` and refuses `pack_failed`, exit 2 (checked by an injected `EIO`) | **this item**, group 1 |
| #113 item 2: a state file that is not valid UTF-8 (`_load_state`, 123) | **open**: `read_text(encoding="utf-8")` raises `UnicodeDecodeError`, a `ValueError` that neither `except` catches | **this item**, group 2 |
| #113 item 2: strict decoding of `git ls-files` in `_tracked_counts` (155) | **open**: `text=True` decodes strictly with the locale's encoding, inside `subprocess.run`, before the return code is read | **this item**, group 2 |
| #113 item 2: the same for `_git_tracked` (927) | **already correct**: it captures bytes and tests `stdout.strip(b"\0")`, nothing is decoded | dropped; one test pins it |
| #113 item 1 (`no archive` / `no review folder` for an unreadable path) and #116 item 1 (`read_errors` path built from `here`) | **open**; the JSON is right, the text and one recorded path are wrong | **split to the next item, row 33** (report text) |
| #119 items 2 to 8, #113 items 3 to 7, #116 items 2 to 7, any refusal code that exists for another reason, the `cross_device` text | not touched | out of scope |

**The split (sizing guard).** The order asks for two kinds of change: refusals that end the run (groups 1 and 2) and
text of the read-only report (group 3, with a data fix in the report's walker). Two kinds of change are not one
review, so this item is the refusals; the report text is row 33, planned right after it, from the same wording of the
mechanism (an unreadable thing is reported as unreadable, never as absent).

**Seen on the way, not changed (report to the owner, a follow-up on #119 if wanted).** Other bare descriptor calls of the
same walkers can raise an `OSError` the same way: `os.read(fd, 1)` that ends `_pack` (line 631) and the `os.fstat` calls
on an open descriptor. They are not `readlink` and not named by the order; one mechanism is kept.

## 1. Goal

Ship Workflow 2.25.5, a **`fix:` patch**, with one mechanism: **an unreadable or undecodable input is reported as what it
is, a coded refusal (exit 2, a `next step:`), never a traceback.** Today (a) a symlink whose target cannot be read
escapes the `archive` and `remove` subcommands as an `OSError` from four call sites, and (b) a state file or a `git
ls-files` path that is not valid UTF-8 escapes every subcommand as a `UnicodeDecodeError`. The documented contract is
exit 0 or 2. No state key, phase, trailer, protocol field or command file moves, every success and every existing
refusal stays byte-identical **except one, named**: a `readlink` failure in the pack, which is `pack_failed` today and becomes
`unreadable` (or `folder_changed`) like the other three sites, so the four sites say the same thing; and **no new refusal
code** is added (D-Codes).

### Hard limits (the owner's sizing rule)

- One mechanism, one helper and two catches; if the plan passes about 350 lines, STOP and split further before review.
- **Two checkpoints** (CP1 the change, its tests and documents; CP2 the release 2.25.5).
- This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`,
  `.workflow-manager/`, managed blocks, the conformance workflow) stays untouched; the shipped copies under `payload/`
  change.

## 2. Facts this plan relies on (re-read at `69ebb46`)

- `_walk_folder` (line 483) already raises `_refuse` for every failure it meets: `unreadable` for a walk error,
  `folder_changed` for an entry that vanishes, `unsupported_entry`. The four readlink sites sit in loops over its
  `others`, so a `RetentionError` from them takes exactly the paths a `RetentionError` from the walker takes today:
  the archive's `_undo` (`except BaseException`, line 1196) drops the temporary, the directories this run created and
  the lock; `remove`'s step 6 (line 1748) renames the folder back for the codes `archive_mismatch`, `folder_changed`,
  `unreadable` and `unsupported_entry`, and adds the leftover note when it was a leftover (`L1`).
- `_open_file` (line 544) maps `EACCES`/`EPERM` to `unreadable` and every other `OSError` to `folder_changed`; the
  step 12/5 hash read maps a read error to `unreadable`. `_stopped(code, why, deleted, place, item_id)` (line 1398)
  builds the refusal of `_remove_tree` ("stopped after deleting N entries, each proven archived; the rest is in ...",
  next step "run `remove <id> --apply` again").
- `readlink` fails with `ENOENT` when the entry vanished, `EINVAL` when it is no longer a symlink (it was replaced), and
  with `EACCES`, `EIO`, `ELOOP`, `ENAMETOOLONG`, `ENOMEM` for a real read problem.
- Codes: `unreadable` and `folder_changed` exist for all three engines; `state_invalid` and `repository_unknown` are
  the report's own refusals, shared by every subcommand through `build_report` (`docs/exit-codes.md`).
- Tests: the classes `RetentionReport`, `RetentionArchive` and `RetentionRemove` of
  `payload/scripts/workflow_state_completion_obligations_test.py`; the 2.25.1 injector `_stat_fails` (patches
  `os.stat`, matches the calling function by name, `skip` count) is the precedent for the new `_readlink_fails`.

## 3. Design decisions

### D-Readlink: one helper, four sites

`_readlink_at(name, dirfd, shown, *, fail=_refuse)` returns `os.readlink(name, dir_fd=dirfd)`; on an `OSError`, `from None`:

- `ENOENT` or `EINVAL` (the entry vanished or is no longer a link): `folder_changed`, message `<shown> changed while it
  was read (<strerror>)`, next step `run it again when nothing writes to the review folder` (the text `_open_file`
  already uses for the same cause);
- any other errno: `unreadable`, message `<shown> cannot be read (<strerror>)`, next step `grant read access to the
  review folder, then run it again; the engine does not act from a partial view`.

`fail(code, message, next_step)` builds the refusal (default `_refuse`); `_remove_tree` passes
`lambda code, message, _step: _stopped(code, message, deleted, place, item_id)` so its refusal keeps the deleted count
and the place. `shown` is the entry's path inside the review folder, as the neighbouring messages build it.

| Site | Replaces | Reached when | Result |
| --- | --- | --- | --- |
| R1 `_scan` (538) | bare call | `archive` selection (1053) and the re-check after the pack (1138); `remove` selection (1591), the re-selection under the lock (`_flow` step 1, 1676, which runs `_select_removal` and so `_scan` again) and the re-check at step 5 after the rename (1745) | selection: nothing written or moved. Archive re-check: `_undo` runs. Re-selection under the lock: the refusal goes through `note(exc)`, nothing was moved yet (no container to drop), the lock is released when the descriptors close and a later run succeeds. Step 5 re-check: `compared` is already true there, so step 6 renames the folder back, in `L0` and in `L1` alike, with the "may be incomplete" note when entries were `missing` (an incomplete leftover goes back into `.ai-review/<id>`, as every refusal after `compared` does today; step 6 is not changed) |
| R2 `_pack` (608) | bare call, caught today by `_pack_to` (684) as `pack_failed` | `archive --apply`, while the tar is written (`_pack_to` re-raises a `RetentionError`, so the helper's refusal passes through unwrapped) | **the one targeted change to an existing refusal**: `pack_failed` becomes `unreadable` or `folder_changed`, by errno. `_undo` drops the temporary, the directories this run created, the lock |
| R3 `_hash_folder` (1322) | bare call | `remove` dry run (step 12, 1631) and step 5 after the rename (1739) | dry run: nothing moved. Step 5: `compared` is still false, so the folder is renamed back in `L0`, and in `L1` kept in place with the leftover note, nothing renamed |
| R4 `_remove_tree` (1435) | the third clause of the entry check | `remove --apply` while it deletes | `_stopped`: `unreadable` or `folder_changed`, "stopped after deleting N entries, each proven archived; the rest is in `.removing/<id>`", next step "run `remove <id> --apply` again" (the entries already deleted are in the archive, as with every other stop of this function). The clause is split so the readlink runs only after the other clauses pass, as today |

The code per site: R1 to R3 give `unreadable` or `folder_changed` by errno; R4 gives the same two codes through
`_stopped`. No other code is used (D-Codes).

### D-Decode: two catches

- `_load_state`: `except UnicodeDecodeError` after the `OSError` clause: `state_invalid`, message `<STATE_PATH> is not valid
  UTF-8 (byte <start>)`, next step `repair the state file` (the same next step the neighbours give).
- `_tracked_counts`: run `git ls-files -z` with bytes captured (no `text=True`); decode stdout with `utf-8` strict and
  stderr with `errors="replace"`. A stdout that does not decode is `repository_unknown`: message `git ls-files printed a
  path under .ai-review that is not valid UTF-8`, next step `rename or untrack that path (git ls-files -z --
  .ai-review lists them), then run it again`. A non-zero exit keeps its refusal and message, with a stderr that can no
  longer raise. Decoding explicitly as UTF-8 equals today's behaviour for UTF-8 paths in a UTF-8 locale, apart from newline translation
  (`text=True` read a `\r` as `\n`), which cannot be observed: only `parts[1]`, a work-item id, is counted.
- `_git_tracked` and the index reader (`json.loads` of bytes, whose `UnicodeDecodeError` is already a `ValueError`
  caught as `index_invalid`) are unchanged; a test pins each.

### D-Codes

No code is added or re-assigned. `unreadable`, `folder_changed`, `state_invalid` and `repository_unknown` exist and keep
every meaning they have; a code that exists for another reason is not changed (the order's out-of-scope list, #119
item 3).

### D-Tests

Written first, red against the unedited tree, in the three classes. One injector, `_readlink_fails(site, name, err,
skip=0)`, patches `os.readlink` to raise `OSError(err, ...)` when the call is `(name, dir_fd=<fd>)` and the function `site`
is its caller, stepping over one `_readlink_at` frame when present (as `_stat_fails` steps over `_lstat_raw`/`_lstat_at`,
test file line 4273) and still matching the bare call, so the same injector works on the unedited tree (red) and on the
changed one; `skip` lets the first N matching calls through (so a later run of `_scan` is reachable). T1 pins that the
injector fires through `_readlink_at`. The `_scan` calls of `remove --apply` are, in order, the selection (`skip` 0), the
re-selection under the lock (`skip` 1) and the step-5 re-check (`skip` 2); `_hash_folder` has one call in `--apply`
(`skip` 0).
Each test asserts: exit 2 and the stable code; the message prefix with the `shown` path, and a `next step:`; **no write and
no removal** (the existing `snap()` of repository and store identical, no archive, no partial, no index line, the folder
in place, `rr.unlinks`/`rr.renames` as stated, no descriptor left open, the lock released by a later run that
succeeds); where a site is after the rename, where the folder is.

| Test | Site | Proves |
| --- | --- | --- |
| T1 | helper | the injector fires through `_readlink_at` and on a bare call; returns the target; `ENOENT` and `EINVAL` give `folder_changed`; `EACCES`, `EIO`, `ELOOP`, `ENAMETOOLONG` give `unreadable`; the message, next step and `fail` hook are exact |
| T2 | R1, archive | a folder with a symlink: `archive` dry run and `--apply` refuse (`EACCES`, `ENOENT`) with nothing written; `--apply` with `skip` 1 (the re-check after the pack) refuses, no `.partial`, no archive, no index line, the hierarchy this run created gone, lock released, a later run succeeds |
| T3 | R2 | `archive --apply` with the error at the pack: the baseline gives `pack_failed` (exit 2), the candidate `unreadable` (`ENOENT`: `folder_changed`); no archive, no temporary, no index line, lock released, a later run succeeds |
| T4 | R1, R3, remove | `remove` dry run and `--apply` selection (`_scan`, `skip` 0), the re-selection under the lock (`_scan`, `skip` 1) and the dry-run hash (`_hash_folder`): refuse, folder in place, `renames == []`, the lock free for a later run; after the rename, `_hash_folder` (`skip` 0) and the re-check `_scan` (`skip` 2): the folder is renamed back, `.removing` dropped, the message says where it is, store identical |
| T5 | R1, R3, `L1` | a leftover from a stopped run: `_hash_folder` failing at step 5 leaves it untouched, nothing renamed, with step 6's own text (`; the folder is in <removing_place>, it may be incomplete and the missing entries exist only in the archive`, next step `; repair the cause and run `remove <id> --apply` again`; step 5's `except` re-raises, so `_leftover_note` is not involved); the re-check `_scan` failing at step 5 (`skip` 2) renames it back into `.ai-review/<id>` with `_incomplete_note` when entries were `missing` (step 6 unchanged) |
| T6 | R4 | an error at the symlink after one entry was deleted: `unreadable` (and `ENOENT`: `folder_changed`) with "stopped after deleting N entries", `rr.unlinks` equals exactly the entries before it, the rest in `.removing/<id>`; the run without the injector finishes the removal |
| T7 | `_load_state` | a state file with bytes `\xff`: `report`, `archive`, `remove` and `prune` (through `main`) give exit 2, `state_invalid`, "not valid UTF-8", `next step:`, nothing written; the existing `state_invalid` outputs unchanged |
| T8 | `_tracked_counts` | a `subprocess.run` stand-in that returns bytes like the real call and decodes when `text` is requested (as `subprocess` does) with a path `\xff`: `repository_unknown`, exit 2; a UTF-8 non-ASCII path still counts; a non-zero exit with undecodable stderr keeps `git ls-files failed`; `_git_tracked` with such a path returns true |

**Failure-only mutations** (each on a scratch copy; the named tests fail there and pass on the real file; results in the
implementation bundle's `TEST_RESULTS.md`): m1 `_scan` calls bare `os.readlink` (T2, T4, T5 fail); m2 `_pack` bare (T3: the candidate gives `pack_failed` again);
m3 `_hash_folder` bare (T4, T5); m4 `_remove_tree` bare (T6); m5 the helper maps every errno to `unreadable` (T1, T2 `ENOENT`
case fail); m6 the helper maps every errno to `folder_changed` (T1 fails); m7 `_remove_tree` does not pass `fail=` (T6 fails:
the deleted count is gone); m8 `_load_state` drops the `UnicodeDecodeError` clause (T7); m9 `_tracked_counts` is back to
`text=True` (T8); m10 `_tracked_counts` decodes with `errors="replace"` (T8 fails: no refusal). The injected error stands in for a
real one; a real `chmod` case cannot reach `readlink` (a link in a searchable directory always reads), so the functional
review (section 6) injects through a patched `os.readlink` in a `python3 -I` snippet.

### D-Docs

`docs/RETENTION.md`: the archive and remove tables gain "a symlink in the review folder whose target cannot be read" as
`unreadable` (`folder_changed` when it vanished or was replaced), the remove text names the stop of the delete, and the
report's refusal list says a state file or a tracked path that is not valid UTF-8 is `state_invalid` / `repository_unknown`.
`docs/exit-codes.md`: the report, archive and remove rows say the same in a clause each. No page names an internal
milestone id; "Last checked with" lines move in CP2.

### D-Release

2.25.5, a **`fix:` patch** (the manifest's version change and the pull request title agree, as `docs/RELEASING.md`
requires). `manifest.json` `workflow_version` 2.25.5; the changed records (`workflow_retention.py`, the test file,
`workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`) take their sentence, `sha256` and `size`; counts and
`distribution` do not move (no file is added); `conformance.suites` is measured by `release.py manager-block --write`.
`WORKFLOW_RELEASE` becomes 2.25.5 with its pinned assertions and the protocol document's example; `tools/release/release_test.py`
gets a 2.25.5 class and the previous class gives up the current-release pins. `docs/release-history.md`: the 2.25.5 row (the
way back to 2.25.4 restores the traceback at three sites and `pack_failed` at the pack; archives and engine data are unchanged). The protocol stays 1.5.

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w37-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256` and
`size` of every `artifacts` record whose file differs from its record (no record is added, so counts and the release-test
counts do not move), measures `conformance.suites` with `release.py manager-block --release-dir <scratch> --write`,
commits in the clone, and runs the "Verification commands" of `docs/RELEASING.md` from there. `tools/release` tests run
with `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
The new tests also run under the Manager's orphan rule (the reaper). CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **`folder_changed` for `ENOENT`/`EINVAL`.** A link that vanished or was replaced between the listing and the read is
  the same cause `_open_file` and the walker map to `folder_changed`; the alternative (all `unreadable`) would tell the
  owner to grant access that is not missing.
- **`repository_unknown` for an undecodable tracked path.** It is the code of that function's other failure; a new code
  is forbidden here, and the next step names the path.
- **A tracked non-UTF-8 path under a single-byte locale.** Equivalence is for UTF-8 paths in a UTF-8 locale; where the locale
  is single-byte (Latin-1), `text=True` used to decode such a path and count it, and it now refuses `repository_unknown`. This
  is the intended direction, named in the 2.25.5 history row.
- **CP1's name** keeps "The helpers" (the helper and its two catches); renaming it would regenerate the registry for a label.
- **The other bare descriptor calls** (section 0) are left for a follow-up the owner may order.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The helpers, their call sites, tests and documents | - | 3 | 1 |
| CP2 | Release 2.25.5 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The helpers, their call sites, tests and documents

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`, `docs/exit-codes.md`.

- **Tests first** (D-Tests): T1 to T8 written and run red against the unedited tree; mutations m1 to m10 each fail the
  named tests in a scratch copy and the results are recorded.
- **The change** (D-Readlink, D-Decode): `_readlink_at` and its four sites, the `_load_state` clause, the bytes form of
  `_tracked_counts`. Every existing test passes unmodified; the diff of the script touches those lines only.
- **The documents** (D-Docs, CP1 part). `check_docs.py` stays clean; "Last checked with" lines unchanged until CP2.
- **No other mechanism:** `git diff 69ebb46 --stat -- payload` lists the script and its test only. `docs/ROADMAP.md`
  is written with this plan (row 32 `Current`, row 33 planned) and row 32 becomes Done at acceptance.

**Verification:** D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`,
`check-manager-block`, `tools/release` (zlib-ng interpreter, no patch, no skip).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.5

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.5 with its pinned assertions and the matching protocol-document edits (protocol 1.5).
- `manifest.json` 2.25.5 (D-Release): `workflow_version`, the changed records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.5 row and its "Last checked with" line; those of `docs/RETENTION.md` and
  `docs/exit-codes.md` move to 2.25.5, with the downgrade sentence.
- `tools/release/release_test.py`: a 2.25.5 class; the previous class gives up the current-release pins.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build
--commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; `workflow-manager
verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its
`.ai-review/`, the real archive store, the real forge or the network.** Setup, once, under `$TMPDIR`: two copies of
`payload/scripts/`, `base/` from `git archive 69ebb46 payload/scripts` and `cand/` from the working tree; a scratch
repository with a `github.com` origin and a state of eight finished items plus one open (so five are archivable),
`.ai-review/m-1` holding `a.txt`, `b.txt` and a symlink `ln` to `a.txt`; a scratch `HOME`; a **fake `gh`** in a
`fakebin` directory that is not under `/tmp`, `/var/tmp`, `/dev/shm` or `$TMPDIR`, not world-writable, first on `PATH`:

```sh
#!/bin/sh
while [ $# -gt 0 ]; do [ "$1" = "--search" ] && sha="$2"; shift; done
printf '[{"number":7,"url":"https://github.com/acme/widgets/pull/7","state":"MERGED","headRefOid":"%s"}]\n' "$sha"
```

The injector `inject.py`, kept outside the scratch repository, run as `python3 -I inject.py <scripts-dir> <site> <name>
<ERRNO> <skip> -- <engine args>`: it puts `<scripts-dir>` first on `sys.path`, imports `workflow_retention`, replaces `os.readlink`
by a function that raises `OSError(errno.<ERRNO>, ...)` when `dir_fd` is set, the name is `<name>`, and the caller of
`os.readlink` (stepping over one `_readlink_at` frame when present) is the function `<site>` (the first `<skip>` matching calls pass), runs `main([...])`, and prints the exit
code. A flow runs against `base/` and `cand/` from a fresh copy of the repository and store; hashes of the repository,
folders and store are compared before and after. Archives are made with the engine's own `archive --apply`.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | no injection: `archive m-1`, `archive m-1 --apply`, `remove m-1`, `remove m-1 --apply`, `prune m-1` with base and cand | the outputs and exit codes are identical, byte for byte |
| 2 | inject `_scan` `ln` `EACCES` 0 with `archive m-1` and `archive m-1 --apply`; then the same with skip 1 and `--apply` | base: traceback, exit 1. cand: exit 2, `error: unreadable: ln cannot be read (Permission denied)`, a `next step:`; the store and the folder hash-identical, no `.partial`, no directory this run created |
| 3 | inject `_pack` `ln` `EIO` 0 with `archive m-1 --apply`; then a run without the injector | base: exit 2 `pack_failed` (`packing failed: ...`; no traceback). cand: exit 2 `unreadable` (the one intended change to an existing refusal); no archive, no temporary, no index line; the later run succeeds |
| 4 | archive `m-1`, then inject `_hash_folder` `ln` `EACCES` 0 with `remove m-1`, and `_scan` `ln` `EACCES` with `remove m-1 --apply` at skip 0 (selection) and skip 1 (the re-selection under the lock) | base: traceback. cand: exit 2 `unreadable`, the folder still in `.ai-review/m-1`, nothing moved, a later run succeeds |
| 5 | archive `m-1`, then inject `_hash_folder` `ln` `EIO` 0 with `remove m-1 --apply` (the hash after the rename), and `ENOENT` for the same site | cand: exit 2 `unreadable` (and `folder_changed` for `ENOENT`), the message says the folder is back in `.ai-review/m-1`, no `.removing` left, the store identical; base: traceback with the folder left in `.removing/m-1`; a run without the injector then removes it |
| 6 | archive `m-1`; inject `_remove_tree` `ln` `EACCES` 0 with `remove m-1 --apply` | cand: exit 2 `unreadable`, "stopped after deleting N entries, each proven archived; the rest is in", next step ``run `remove m-1 --apply` again``; the remaining entries in `.removing/m-1`; a run without the injector finishes; base: traceback |
| 7 | write the bytes `\xff` into the scratch repository's `docs/ai-workflow/WORKFLOW_STATE.json`; run `report`, `archive m-1`, `remove m-1`, `prune m-1` | base: traceback `UnicodeDecodeError`, exit 1. cand: exit 2 `error: state_invalid: ... is not valid UTF-8 (byte ...)` and a `next step:`; nothing written |
| 8 | `git add -f` a file named with the byte `\xff` under `.ai-review/m-1` (created with a bytes path in `python3 -I`), run `report` | base: traceback `UnicodeDecodeError`, exit 1. cand: exit 2 `error: repository_unknown: git ls-files printed a path under .ai-review that is not valid UTF-8` and a `next step:`; nothing written |
| 9 | `git diff 69ebb46 --stat -- payload docs` and `python3 -I scripts/workflow_retention.py --help` (CP1), the history row, manifest and pages agree on 2.25.5 (CP2) | CP1: the script and its test only in `payload`; CP2 adds `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`; no new code in the help or the documents' code lists |
| 10 | (needs the full environment) the nine payload suites from a staged fixture and the `tools` tests with the zlib-ng interpreter | all pass, no skip |

## 7. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 32, #119 item 1 | the four readlink sites become coded refusals | CP1 | D-Readlink, T1 to T6, m1 to m7 |
| Row 32, #113 item 2 | a non-UTF-8 state file and `git ls-files` path become coded refusals; `_git_tracked` already safe | CP1 | D-Decode, T7, T8, m8 to m10 |
| Row 32 | every existing success and refusal byte-identical, except the pack's `readlink` failure (`pack_failed` to `unreadable`, T3); no new code | CP1 | the unmodified existing tests, D-Codes |
| Row 32 | the release is a `fix:` patch, 2.25.5 | CP2 | D-Release |
| #113 item 1, #116 item 1 | report text and the `read_errors` path | **next item, row 33** | section 0 |
| #119 items 2 to 8, other issue items, other bare descriptor calls | not here | stay on their issues | section 0 |

The artifact declaration `docs/ai-workflow/registry/retention-error-paths-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations` and then extended by hand for `payload/`, `tools/`, `fixtures/`,
`templates/`, `manifest.json`, `docs/RETENTION.md`, `docs/exit-codes.md` and `docs/release-history.md`, as the earlier
retention items' were; every path a checkpoint's **Files** paragraph names is classified at both stages.
