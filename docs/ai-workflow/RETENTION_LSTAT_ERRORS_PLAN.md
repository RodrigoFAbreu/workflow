# W33: Workflow 2.25.1 — a stat error becomes a coded refusal (Revision 4)

- **Work item:** `retention-lstat-errors` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 28 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance), chosen by the owner from the follow-ups of the retention track.
- **Issue:** RodrigoFAbreu/workflow#126 item 1 (items 2 and 3 were folded into W32; items 4 and 5 stay on the issue).
  **Branch:** `milestone/retention-lstat-errors`
- **Base commit:** `d101bebae7401a00364da702b37baaf69fc9f7b0` (main after #131: release source and own installation are
  2.25.0; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 3 (rounds 1 and 2 of the local review applied: LPR-R1-001 to -003, LPR-R1-O1 to -O3, LPR-R2-001 and
  the optional LPR-R2-O1 to -O3, see section 4). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.25.1, a **`fix:` patch**, that closes one defect of `scripts/workflow_retention.py`: `_lstat_at` catches
only `FileNotFoundError`, so any other `OSError` of the `lstat` of an archive-directory entry (`EACCES` on a directory
without search permission, `ELOOP`, `ENAMETOOLONG`, `EIO`, `ENOTDIR`) escapes the `archive`, `remove` and `prune`
subcommands as a traceback, without the engine's coded refusal and its `next step:` (#126 item 1; the local
implementation review of the prune engine noted it as LIR-R2-O1).

**One mechanism:** `_lstat_at` turns a stat error that is not "not found" into a coded refusal. Everything else is
unchanged: every success and every existing refusal stays byte-identical, no state key, phase, trailer or protocol
field moves, no command file is touched, and **no new refusal code** is added.

### Hard limits (the owner's sizing rule)

- One helper-level mechanism; the prune call sites are in it, not split out. If the plan passes about 350 lines or a
  second mechanism appears, STOP and split before the first review.
- **Two checkpoints** (CP1 the helper, its call sites, tests and documents; CP2 the release 2.25.1).
- This repository's own installation (`.claude/`, `scripts/`, `docs/ai-workflow/` managed documents,
  `.workflow-manager/`, managed blocks, the conformance workflow) stays untouched; the shipped copies under `payload/`
  change.

## 2. Facts this plan relies on (re-read at `d101beb`)

- `_lstat_at(name, adir_fd)` (`payload/scripts/workflow_retention.py`, line 808) is `os.stat(name, dir_fd=adir_fd,
  follow_symlinks=False)` returning `None` on `FileNotFoundError`. `_lstat_at_path` (line 1072) already converts a path
  `OSError` into `_unsafe_component`. `_refuse(code, message, next_step)` builds a `RetentionError`, printed as `error:
  <code>: <message>` and `next step:` on stderr, exit 2.
- The calls, by function: `_judge_archive_side` (archive step 7: lines 893 final, 905 temporary), `_restore` (1456),
  `_judge_removal_archive` (1508), `_has_leftover` (1532), `_select_removal` (1551, 1552 and 1554, step 8), `_flow` (1682,
  apply step 3, before the rename; 1703, step 4, **after** the rename), `_prune_select` (1801, step 9), `_unchanged` (1810,
  which prune's steps 12 and 13a reach through `_check_unchanged`).
- **Steps 12 and 13a already report a stat error coded:** `_check_unchanged` catches `OSError` from `_unchanged` and
  refuses `prune_failed` with the `removed:`/`not removed:` lists (`docs/RETENTION.md` row 12 says so; the existing test
  `test_p5` injects `EIO` after the first unlink). They call `_lstat_at` today only because it lets the error through,
  so they must keep a raw stat (D-Raw), or the new coded refusal would drop the lists.
- `_has_leftover` probes with `except OSError: return False`: an error there reads as "no leftover". That is the
  existing behaviour (a success path), so it keeps the raw stat and is **not** changed here (section 7 records it).
- The `unreadable` code is already documented for the archive, remove and prune (`docs/RETENTION.md`, `docs/exit-codes.md`);
  `restore_failed` for remove; `prune_failed` for prune. The tests of the three engines are the classes `RetentionArchive`,
  `RetentionRemove` and `RetentionPrune` of `payload/scripts/workflow_state_completion_obligations_test.py`, whose
  `os.stat` patches (`name`, `dir_fd`) are the injection precedent.

## 3. Design decisions

### D-Raw

Two helpers, one mechanism:

- `_lstat_raw(name, adir_fd)`: the current body of `_lstat_at` (returns `None` on `FileNotFoundError`, lets every other
  `OSError` through). Its users are `_has_leftover`, `_unchanged` and prune's step 9 (which builds its own refusal).
- `_lstat_at(name, adir_fd, *, shown, code="unreadable", after="nothing was written or removed")`: calls `_lstat_raw`;
  on an `OSError` raises `_refuse(code, f"{shown} cannot be examined: <ERRNO> <strerror>", f"check the permissions of
  {shown} and of the directory that holds it; {after}")`, with the errno name as `errno.errorcode` prints it, like
  prune's. `from None`. `shown` is **required** and is the full displayed path of the entry that failed, never the bare
  `name` (LPR-R1-002): the directory differs by site (D-Sites, column "shown"), so a message built from `name` alone
  would send the owner to the wrong directory. It never returns for an error, so no call site can treat a failed stat
  as "absent".

### D-Sites (the decision per call site)

| Site | shown | State when the stat fails | Refusal |
| --- | --- | --- | --- |
| S1a `_judge_archive_side`, final archive (893), **selection call** (`archive_item`, line 1026) | `os.path.join(resolved, <id>.tar.zst)` | selection, nothing written (dry run and apply) | `unreadable` |
| S1b the same stat, **second call under the lock** (`_apply`, line 1133, `check_partial=False`) | the same | apply only, after the hierarchy walk (which may have created directories), after `.<id>.partial` was written and verified, lock held; `_undo` drops the temporary, removes the directories this run created and releases the lock | `unreadable`, `after`: "nothing was archived; the temporary and the directories this run created were removed" |
| S2 `_judge_archive_side`, temporary (905), selection call only (`check_partial=False` skips it in `_apply`) | `os.path.join(resolved, .<id>.partial)` | selection, nothing written | `unreadable` |
| S3 `_judge_removal_archive` (1508) | `os.path.join(resolved, <id>.tar.zst)` | selection, nothing moved | `unreadable` |
| S4 `_select_removal` step 8: probe 1 (1551, `<id>` in `.removing`) and probe 3 (1554, the leftover's mode) | `os.path.join(resolved, ".removing", <id>)` | selection, nothing moved | `unreadable` |
| S4 probe 2 (1552, `<id>` in the repository's `.ai-review`, `ai_fd`) | `<repo>/.ai-review/<id>` | selection, nothing moved | `unreadable` |
| (S3 and S4 run twice in `remove --apply`: the selection, then the re-run under the lock in `_flow`; a failure in the re-run leaves the folder in place. S1 is the two rows S1a and S1b; S2 runs only in the selection. **S1a and S2 are reached only when the per-repository archive directory exists at selection:** `_judge_archive_side` returns at once for `adir_fd is None`, which `_select_destination` gives for an absent directory) | | | |
| S5 `_flow` step 3 (1682) | `os.path.join(resolved, ".removing", <id>)` (`removing_place`) | lock held, container possibly created, nothing moved | `unreadable`, through `leave_in_place` (drops a container this run created); `after`: "nothing was moved or deleted" |
| S6 `_flow` step 4 (1703), state `L0` (this run renamed the folder) | `removing_place` | the folder **was moved** and is whole in `.removing/<id>` | `unreadable`; `after`: "the folder is whole in `<removing_place>`; nothing was renamed back or deleted; once it is readable run `remove <id> --apply` again" (the same resume the `place_failed` text names) |
| S6 `_flow` step 4, state `L1` (a leftover from an earlier run; this run renamed nothing) | `removing_place` | the leftover is untouched in `.removing/<id>` and **may be incomplete** (`_flow` step 6 says so for the same state, and `docs/exit-codes.md` separates "a whole copy" from "a smaller leftover there after a stopped delete") | `unreadable`; `after`: "the leftover is untouched in `<removing_place>`, it may be incomplete and the missing entries exist only in the archive; nothing was renamed or deleted; once it is readable run `remove <id> --apply` again". The `after` is chosen by `leftover`, so the L1 text never calls the folder whole (LPR-R1-001) |
| S7 `_restore` (1456) | `ai_place` | a verification refusal is being undone | `restore_failed` (`code=`), `after`: "the folder stays in `<removing_place>`; once it is readable `mv` it to `<ai_place>`"; the caller already joins it to the original refusal ("the refusal was ...") |
| S8 `_prune_select` step 9 (1801) | `os.path.join(resolved, <name>)` | before the first unlink, nothing removed | `prune_failed`, built with the existing `_stop_after([], ids, ...)` and the existing message and next step of `_check_unchanged` ("could not be examined: ERRNO strerror", "check the permissions of <dir>; run `prune` again for a fresh preview"), so steps 9, 12 and 13a read the same. The `shown` path is `os.path.join(resolved, <name>)`, but the **message and next step are `_check_unchanged`'s unchanged**: the bare `<name>` in the message and `check the permissions of <resolved>` in the next step (LPR-R2-O1); T7 pins that text, and the full path is not put into the shared builder (T8 forbids changing steps 12 and 13a) |
| unchanged: `_unchanged` (12, 13a), `_has_leftover` | — | — | the raw stat: `prune_failed` with the lists at 12 and 13a, and "no leftover" for the probe |

`_judge_archive_side` and `_judge_removal_archive` take the displayed archive directory `resolved` (both of their callers
hold it) as a new argument, to build `shown`. `_check_unchanged`'s message is moved into a small shared builder used by step 9 and by `_check_unchanged`, with the
text unchanged (a refactor pinned by the existing `test_p5` assertions and by T8 below). Why `unreadable` for the
selection sites: the code already means "an entry of the archive directory cannot be read" for these three engines,
with the next step "grant read access". Why `prune_failed` for step 9: prune's stat failures are one family, and the
command wrapper reports its `removed:`/`not removed:` lists verbatim.

### D-Tests

Written first, red against the unedited tree, in the three classes of
`payload/scripts/workflow_state_completion_obligations_test.py`. One injector, `stat_fails(site, name, err)`, a patch of
`os.stat` that raises `OSError(err, ...)` when the function that called `_lstat_at` or `_lstat_raw` (the first frame above the
helpers) is named `site` and the call is `(name, dir_fd=<fd>)`, so a site is hit and no other (the same name is stat'ed
elsewhere); a `skip` count raises on a later matching call. **Counting rule (LPR-R1-O2):** only a call that reaches
`os.stat` through `_lstat_at` or `_lstat_raw` counts toward a site's matches and its `skip`; a direct `os.stat` made by
the site itself does not (for example `_flow`'s `before = os.stat(item_id, dir_fd=ai_fd, ...)` at line 1686, between S5
and S6: if it counted, flow 5's `--skip 1` would hit it and give `folder_changed` instead of S6). **Precondition of S1a and S2 (LPR-R2-001):** they stat
nothing when the per-repository archive directory is absent at selection, so T1's S1a, S2 and S1b-`skip 1` cases run with
the directory present (the test archives another item first). With it absent the walk creates the hierarchy and S1b is
the first matching call (`skip` 0). In `remove --apply`
the site `_select_removal` is reached twice, by the selection (`skip` 0) and by the re-run under the lock in `_flow`
(`skip` equal to the number of its probes in the selection); T3 and flow 3 name which. Each test asserts: exit 2 and the stable code; the exact
message prefix **with the site's `shown` path** (D-Sites; never a generic prefix) in the message and in the `next step:`, and that the `next step:` is present; **no write and no removal** (the existing `snap()` of repository
and store identical, no archive, no partial, no index line, the folder in `.ai-review` still there, no `.removing`
created where the site is before the rename, `rr.unlinks == []`, no descriptor left open, the lock released by a second
run that succeeds).

| Test | Site | Proves |
| --- | --- | --- |
| T1 | S1a, S2, S1b | With the archive directory present (another item archived first): `archive` (dry run and apply) refuses `unreadable` for each name with nothing written; `ELOOP` and `EIO` give the same code. **S1b, directory present:** `archive --apply` with the injector's `skip` 1 on `_judge_archive_side` for the final archive reaches the call under the lock in `_apply`: `unreadable`, no `.partial`, no archive or index line, no descriptor left open, the lock released (a second run without the injector succeeds). **S1b, directory absent (`skip` 0):** the walk creates the hierarchy and S1b is the first matching call: `unreadable`, no `.partial`, no archive or index line, **the directories this run created are gone** (`_undo`'s `rmdir` of `created`), the lock released, a second run succeeds |
| T2 | S3 | `remove` (dry run and apply) refuses `unreadable` naming `<resolved>/<id>.tar.zst`, folder and store identical |
| T3 | S4 | `remove` with a `.removing` present refuses `unreadable` at each of the three probes, naming `<resolved>/.removing/<id>` for probes 1 and 3 and `<repo>/.ai-review/<id>` for probe 2; the folder is in place. The dry run hits the selection (`skip` 0); `remove --apply` is run once more with `skip` set to the probe count to hit the re-run under the lock in `_flow` |
| T4 | S5 | `remove --apply`: the stat error under the lock before the rename leaves the folder in `.ai-review` and no container this run created |
| T5 | S6, `L0` and `L1` | `L0`: `remove --apply`, the error right after the rename (the first stat counted by the injector after S5's) refuses `unreadable` naming `.removing/<id>` and the `remove <id> --apply` resume, saying the folder is whole; nothing deleted; the resume then succeeds. `L1`: a `.removing/<id>` left by an earlier stopped run (made by the test), the error at step 4 refuses `unreadable` with the `L1` wording (untouched, may be incomplete, missing entries exist only in the archive), **not** "whole"; nothing renamed or deleted, the leftover's bytes identical; the resume then succeeds |
| T6 | S7 | a verification refusal followed by a failed stat of the original place gives `restore_failed` that carries both causes, names `<repo>/.ai-review/<id>` as the entry that failed, and names where the folder is |
| T7 | S8 | `prune --apply` with `EACCES` at step 9 refuses `prune_failed`, `removed: none; not removed: <every id>`, no unlink; the dry run too |
| T8 | steps 12, 13a, probe | the existing `test_p5` stays green unmodified; a new case fails the stat at step 12 and at 13a after one unlink and keeps `removed: w00` and `not removed: w01, w02` byte for byte; `_has_leftover` still returns `False` on an error |
| T9 | helper | `_lstat_at` returns `None` for `ENOENT`, the stat for a present name, and raises for every other errno of a list (`EACCES`, `ELOOP`, `ENAMETOOLONG`, `EIO`, `ENOTDIR`); `_lstat_raw` lets the `OSError` through |

**Failure-only mutations** (each run on a scratch copy; the named tests must fail there and pass on the real file;
results in the implementation bundle's `TEST_RESULTS.md`). S8 (step 9) calls `_lstat_raw` and builds its own
`prune_failed`, so a mutation of `_lstat_at` alone never reaches it (LPR-R3-001): m1 restore the bare catch (`_lstat_at` =
the old body: T1 to T6 and T9 fail with the raw `OSError`; T7 is unaffected); m2 to m9, one per `_lstat_at` call line,
make that line call `_lstat_raw` (S8 is not among them, it already does; S1a and S1b share line 893 and cannot be
mutated apart; S4 is two lines): m2 line 893 (T1, the S1a and S1b cases), m3 line 905 (T1, the S2 case), m4 line 1508
(T2), m5 lines 1551 and 1554 (T3, probes 1 and 3), m6 line 1552 (T3, probe 2), m7 line 1682 (T4), m8 line 1703 (T5, the
`L0` and `L1` cases), m9 line 1456 (T6); in each only the named test fails; m10 let `_unchanged` call `_lstat_at` (T8
fails: the lists are gone); m11 let `_has_leftover` call `_lstat_at` (T8 fails); m12 drop `leave_in_place` at S5 (T4
fails: a container is left); m13 make step 9 raise `unreadable` instead of `prune_failed` (T7 fails); m14 make
`_lstat_at` swallow the error and return `None` (T1 to T6 and T9 fail; T7 is unaffected, S8 uses `_lstat_raw`); m15 S6
always uses the `L0` `after` text, "the folder is whole" (T5's `L1` case fails; LPR-R3-O1); m16 remove step 9's own
`except OSError` (T7 fails with the raw `OSError`; S8's real mutation, next to m13).

Where the injection is not a real permission error the tests say so; a real `chmod` case runs in the functional review
(section 6), skipped by the tests when run as root.

### D-Docs

`docs/RETENTION.md`: the archive step 7 and the remove steps list `unreadable` for "an archive-directory entry that
cannot be examined" (the three tables that name `unreadable` today, lines about 443 to 444, 503 to 511 and 650 to 657),
the restore text names that a failed stat there is `restore_failed`, and the prune table's row 9 reads "`archive_changed`
or `prune_failed`" (a stat error is `prune_failed` at steps 9, 12 and 13a alike). `docs/exit-codes.md`: the three engine
rows say that a stat error other than "not found" is `unreadable` (prune: `prune_failed`), never a traceback. The "Last
checked with" lines (`docs/RETENTION.md`, `docs/exit-codes.md`, `docs/release-history.md`) and the downgrade sentence move
to 2.25.1 in CP2 (LPR-R1-O1; `docs/exit-codes.md` reads 2.24.0 until then, as #127 moved it when it last edited the page). No page names an internal milestone id.

### D-Release

2.25.1, a `fix:` patch (the manifest's version change and the pull request title agree, as `docs/RELEASING.md`
requires). `manifest.json` `workflow_version` 2.25.1; the changed records (`workflow_retention.py`, the test file,
`workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`) take their sentence, `sha256` and `size`; counts and
`distribution` do not move (no file is added); `conformance.suites` is measured by `release.py manager-block --write`.
`WORKFLOW_RELEASE` becomes 2.25.1 with its pinned assertions (`workflow_protocol.py`, `workflow_protocol_test.py`, the
protocol document's example and the `1.5` list). `tools/release/release_test.py`: a 2.25.1 class and the 2.25.0 class
gives up the current-release pins to it. `docs/release-history.md`: the 2.25.1 row (fix; the way back to 2.25.0 restores
the traceback, archives and engine data unchanged). The protocol stays 1.5.

### D-Staging: scratch staging for CP1

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage CP1. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w33-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256`
and `size` of every `artifacts` record whose file differs from its record (no record is added, so the counts and the
release-test counts do not move in CP1), measures `manager.conformance.suites` with `release.py manager-block
--release-dir <scratch> --write`, commits in the clone, and runs the "Verification commands" blocks of `docs/RELEASING.md`
from there. `tools/release` tests run with the zlib-ng interpreter
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
The new tests also run under the Manager's orphan rule (the reaper). CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **`unreadable` over a new code.** One word already documented for the three engines; a new `stat_failed` would need a
  next step in two documents for no new action by the owner.
- **S6 is `unreadable`, not `folder_changed`.** After the rename the useful fact is where the folder is and how to resume;
  `folder_changed` says the folder differs, which is not known.
- **`_has_leftover` keeps swallowing.** Making it refuse would change what the report-free dry run does for a broken
  `.removing`; section 7 records it as a follow-up, not part of this fix.

### Review round 1 (local, `REVISE`), dispositions

All validated against `payload/scripts/workflow_retention.py` at `d101beb`; all accepted, none rejected.

- **LPR-R1-001** (S6 `L1`): confirmed, `_flow` step 4 (line 1703) runs in `L1` and step 6 (line ~1724) already calls that
  folder possibly incomplete. D-Sites splits S6 by `leftover`; T5 and flow 5 gain the `L1` case.
- **LPR-R1-002** (the message names the wrong directory): confirmed, S4 probe 2 (1552) and S7 stat `.ai-review`, the others
  the archive directory or `.removing`. D-Raw requires `shown`; D-Sites has a `shown` column; T1 to T7 pin it.
- **LPR-R1-003** (`_apply` call): confirmed, line 1133 calls `_judge_archive_side(..., check_partial=False)` under the lock.
  D-Sites has S1b with its real state; T1 and flow 2 gain the `skip` case.
- **LPR-R1-O1**: `docs/exit-codes.md` joins CP2's **Files** and bullets. **LPR-R1-O2**: the counting rule and the
  selection-versus-re-run `skip` are in D-Tests, T3 and flows 3 and 5. **LPR-R1-O3**: the four prefix reasons of
  `retention-lstat-errors-artifacts.json` now say 2.25.1.

### Review round 2 (local, `REVISE`), dispositions

All validated against `payload/scripts/workflow_retention.py` at `d101beb`; all accepted, none rejected.

- **LPR-R2-001**: confirmed, `_judge_archive_side` returns at line 883 for `adir_fd is None` and `_select_destination`
  documents `adir_fd` as None when absent. D-Sites and D-Tests state the precondition; T1 and flow 2 run S1a, S2 and
  S1b-`skip 1` with the directory present and gain the S1b-`skip 0` case with it absent, asserting `_undo` removes the
  hierarchy the walk created.
- **LPR-R2-O1**: the S8 row says its message and next step are `_check_unchanged`'s unchanged; T7 pins that text.
  **LPR-R2-O2**: the parenthetical row reads "S3 and S4 run twice in `remove --apply`". **LPR-R2-O3**: flow 4's Expect
  names the helper stat of `.removing/m-1` at step 3 (S5).

### Review round 3 (local, `REVISE`), dispositions

Validated against `payload/scripts/workflow_retention.py` at `d101beb`: step 9 (S8) uses `_lstat_raw`, so `_lstat_at`
mutations never reach T7. Both findings accepted, none rejected.

- **LPR-R3-001**: D-Tests' mutation list is rewritten. m1 and m14 name T1 to T6 and T9 (T7 unaffected); m2 to m9 map
  explicitly onto the `_lstat_at` call lines without S8 (S1a and S1b share line 893); m16 removes step 9's own catch
  (S8's real mutation, next to m13). CP1 now says m1 to m16.
- **LPR-R3-O1**: m15 (S6 always uses the `L0` `after`; T5's `L1` case fails) added.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The coded refusal, its call sites, tests and documents | - | 3 | 1 |
| CP2 | Release 2.25.1 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The coded refusal, its call sites, tests and documents

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`, `docs/exit-codes.md`.

- **Tests first** (D-Tests): T1 to T9 written and run red against the unedited tree; the mutations m1 to m16 each fail
  the named tests in a scratch copy and the results are recorded.
- **The helper and the sites** (D-Raw, D-Sites): `_lstat_raw`, the new `_lstat_at`, the nine sites (S1a, S1b, S2 to S8) with their `shown` paths, S6 split by `leftover`, the shared
  `prune_failed` builder. Every existing test of the three classes passes unmodified. The diff of the script touches the
  helper and the call lines only.
- **The documents** (D-Docs, CP1 part). `check_docs.py` stays clean, no page names an internal milestone id, the "Last
  checked with" lines are unchanged until CP2.
- **No other mechanism:** `git diff d101beb --stat -- payload` lists the script and its test only.
  `docs/ROADMAP.md` is written with this plan (row 28 `Current`) and becomes Done at acceptance, not in CP1.

**Verification:** D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`,
`check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng interpreter, no patch, no skip).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.1

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.1 with its pinned assertions and the matching protocol-document edits (the protocol
  version stays 1.5).
- `manifest.json` 2.25.1 (D-Release): `workflow_version`, the changed records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.1 row and its "Last checked with" line; those of `docs/RETENTION.md` and
  `docs/exit-codes.md` (2.24.0 until now) and the downgrade sentence move to 2.25.1.
- `tools/release/release_test.py`: a 2.25.1 class; the 2.25.0 class gives up the current-release pins to it.
- `docs/ROADMAP.md` becomes Done at acceptance, not in CP2.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block` and `tools/docs` are clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its
`.ai-review/`, the real archive store, the real forge or the network.** Setup, once, under `$TMPDIR`: a scratch
repository with a `github.com` origin and a state of eight finished items plus one open (so that with `KEEP_RECENT = 3`
five are archivable), the candidate's `scripts/workflow_retention.py` copied in; a scratch `HOME`; a **fake `gh`** in a
`fakebin` directory that is not under `/tmp`, `/var/tmp`, `/dev/shm`, `$TMPDIR` or the scratch repository and not
world-writable (a sibling of `$TMPDIR` in the run directory), first on `PATH`:

```sh
#!/bin/sh
# fake gh: the engine runs `gh pr list --repo R --state all --search <sha> --limit N --json ...`
while [ $# -gt 0 ]; do [ "$1" = "--search" ] && sha="$2"; shift; done
printf '[{"number":7,"url":"https://github.com/acme/widgets/pull/7","state":"MERGED","headRefOid":"%s"}]\n' "$sha"
```

The injector, `inject.py`, kept outside the scratch repository and run as `python3 -I inject.py <site> <name> <ERRNO>
-- <engine args>`: it puts the candidate `scripts/` first on `sys.path`, imports `workflow_retention`, replaces `os.stat`
by a function that raises `OSError(errno, ...)` when the call is `(<name>, dir_fd=<an fd>)` and the function that called
`_lstat_at` or `_lstat_raw` is named `<site>` (`--skip N` lets the first N matching calls through), calls `main([...engine args...])` and prints the exit code and stderr. It works as root too. Archives are made
by the engine's own `archive --apply` (so the per-repository archive directory exists once one item is archived; flow 2's S1a and S2 steps need it present at selection, LPR-R2-001), and one is aged with `os.utime` for the prune flows. Each flow starts from a fresh
copy of the scratch repository and store; before and after it, hashes of the repository, the folders and the store are
compared.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `archive m-1` and `archive m-1 --apply`, `remove m-1 --apply`, then `prune m-1 --apply` (aged), with no injection | exit 0 each, outputs as before the change; the archive, the index line, the removed folder and the removed archive are exactly as 2.25.0 gives |
| 2 | with the archive directory present (archive `m-2` first): injector `_judge_archive_side` `m-1.tar.zst` `EACCES`, then `.m-1.partial` `EIO`, each with `archive m-1` and with `archive m-1 --apply`; then `archive m-1 --apply` with injector `_judge_archive_side` `m-1.tar.zst` `EIO` `--skip 1` (the call under the lock); then, from a fresh store with **no** archive directory, the same `--apply` with `--skip 0` (S1b is the first matching call, after the walk created the hierarchy) | exit 2, `error: unreadable: <store>/<repo>/m-1.tar.zst cannot be examined: EACCES ...` (the full path) and a `next step:` line naming it, no traceback; nothing written (the store and the folder hash-identical, no `.partial`, no directory this run created, including after the fresh-store `--skip 0` run, where `_undo` removed the hierarchy the walk created); a run without the injector then succeeds |
| 3 | injector `_judge_removal_archive` `m-1.tar.zst` `EACCES`; then `mkdir` a `.removing` in the store and injector `_select_removal` `m-1` `ELOOP` (`--skip 0`: the selection; and `--skip 2` for the re-run under the lock if the selection made two matching probes), each with `remove m-1 --apply` | exit 2 `unreadable` naming `<store>/<repo>/.removing/m-1` (and `<repo>/.ai-review/m-1` for the second probe), next step present, the folder still in `.ai-review/m-1`, the store identical |
| 4 | injector `_flow` `m-1` `EACCES` with `remove m-1 --apply` | exit 2 `unreadable`: the helper stat of `.removing/m-1` at step 3 (S5, before the rename) leaves the folder in place and no `.removing` the run created; a second run without the injector removes it |
| 5 | after flow 4's setup, injector `_flow` `m-1` `EIO` on the stat after the rename (`--skip 1`: the second stat of `_flow` that reaches `os.stat` through the helper; its direct `os.stat` at step 3 does not count). Then `L1`: from a fresh copy, leave `.removing/m-1` by hand as an earlier stopped run would, and inject the same site with `--skip 0` | `L0`: exit 2 `unreadable` naming `.removing/m-1` and `remove m-1 --apply`, saying the folder is whole; nothing deleted; the run without the injector resumes and succeeds. `L1`: exit 2 `unreadable` saying the leftover is untouched and may be incomplete (never "whole"); nothing renamed or deleted; the run without the injector resumes |
| 6 | age three archives, injector `_prune_select` `m-1.tar.zst` `EACCES` with `prune m-1 m-2 m-3 --apply` and without `--apply` | exit 2 `prune_failed`, message ends `removed: none; not removed: m-1, m-2, m-3`, next step present, no archive removed |
| 7 | the same prune with the injector on the **second** stat of `m-2.tar.zst` by `_unchanged` after `m-1` was removed (`--skip` as needed) | exit 2 `prune_failed`, `removed: m-1; not removed: m-2, m-3`, unchanged from 2.25.0 |
| 8 | not as root only: `chmod 0600` the per-repository archive directory of the scratch store (read, no search), run `archive m-2 --apply`, `remove m-2` and `prune m-2`, then `chmod 0700`. As root, say so and mark the flow not run | a coded refusal or the report's own `unreadable` with a `next step:` and no traceback, nothing changed |
| 9 | `git diff d101beb --stat -- payload` and `docs`, and `python3 -I scripts/workflow_retention.py --help` | the script and its test only (CP1), no new code in the help or the documents' code lists, the history row, manifest and pages agree on 2.25.1 (CP2) |

## 7. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 28, #126 item 1 | `_lstat_at` turns a non-"not found" stat error into a coded refusal; per-site codes; no new code | CP1 | D-Raw, D-Sites, T1 to T9 |
| Row 28 | prune's steps 9, 12, 13a keep `removed:`/`not removed:` | CP1 | S8, T7, T8 |
| Row 28 | existing success and refusal behaviour byte-identical | CP1 | the unmodified existing tests, T8 |
| Row 28 | the release is a `fix:` patch, 2.25.1 | CP2 | D-Release |
| `_has_leftover` swallowing an `OSError` | stays as is; a follow-up on #126 if the owner wants it coded | not here | section 4 |
| #126 items 4 and 5; #123 items 2 to 6 | the mapping and the checklists | **not here** | stay on their issues |

The artifact declaration `docs/ai-workflow/registry/retention-lstat-errors-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations` and then extended by hand for `payload/`, `tools/`, `fixtures/`,
`templates/`, `manifest.json`, `docs/RETENTION.md`, `docs/exit-codes.md` and `docs/release-history.md`, as the earlier
retention items' were; every path a checkpoint's **Files** paragraph names is classified at both stages.
