# W38: Workflow 2.25.6 — the retention report says `unreadable` where it cannot tell (Revision 3)

- **Work item:** `retention-report-unreadable` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-04: row 33 of `docs/ROADMAP.md` (`Current`
  from this plan, `Done` at acceptance; no other row is added).
- **Issues:** RodrigoFAbreu/workflow#113 item 1, #116 item 1, #119 item 8. **Branch:** `milestone/retention-report-unreadable`
- **Base commit:** `e687d51ba050267181b143551b56e95b04fd8bdc` (main after #145: release source and own installation are
  2.25.5; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 3 (round 1, `LPR-R1-001` to `-004` and `-O1`, and round 2, `LPR-R2-001`, `-002`, `-O1`, `-O2`, applied: see sections 2, 3, 4 and 6). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. What the order named, checked against main (Workflow 2.25.5)

Each item was reproduced on `e687d51` with the scratch harness of section 6 (real `chmod` stand-ins, no forge, no network).

| Order item | State on main | Disposition |
| --- | --- | --- |
| #113 item 1, archive: `render_text` (`workflow_retention.py` 2006) prints `no archive` when `archive.readable` is false | **open**: with the archive directory not searchable the line reads `w00: 9 B in 3 files; no archive`; the JSON says `readable: false` and `INCOMPLETE` lists the paths | **this item** |
| #113 item 1, review folder (2007): `no review folder` when `review_folder.complete` is false | **open**: `.ai-review` readable but not searchable gives `present: false, complete: false` and the line `no review folder`; a partly counted folder prints `6 B in 2 files` as if exact | **this item**: `review folder unreadable`; a partial size is a lower bound |
| #116 item 1: `walk_failed` in `_review_folder` (234-240) builds the path from `here`, the last yielded directory | **open**: an unreadable `.ai-review/w00/zz` is recorded as `.ai-review/w00/empty/zz` (and `…/a/b/c/zz` for a deeper last directory) | **this item**: record the failed directory's real parent |
| #119 item 8: a review folder left in `.removing` prints `no review folder` (2007) | **open**: `w00: no review folder; archive 20 B …` beside the `Interrupted removals (1): w00` section | **this item**: `review folder in .removing` |
| #113 items 2 to 7, #116 items 2 to 7, #119 items 1 to 7, every refusal code, the JSON shape, every other text line, the engine messages of row 32, any command file | not touched | **out of scope** |

**Seen on the way, not changed (a sizing choice, presented to the owner; `LPR-R1-002`).** (a) When the archive
directory is a symlink the archive fact is the absent one (`readable: true`), and when `.ai-review` itself cannot be
opened every folder reads `complete: true, present: false`; the text then still says `no archive` / `no review folder`
(on the candidate, `w00: no review folder; no archive` for a mode-000 `.ai-review`), beside an `INCOMPLETE` entry that
names the path. This is **not** blocked by the JSON: `render_text` already receives `read_errors`, which names
`report["archive_dir"]` and the `.ai-review` path, so a text-only change could tell them apart. It is left out because
it is a second mechanism (matching error paths to fragments, not reading a fact the record already holds), and a
mode-000 `.ai-review` is arguably what #113 item 1 calls an unreadable review folder, so the owner may want it in this
patch: **open decision 1 of section 4**. (b) An item folder with mode 000 makes `os.fwalk` re-raise from its first
open (the root of a walk is not routed to `onerror`): `report` raises `PermissionError`, a traceback, exit 1; it prints
no `review folder unreadable` line, and the page does not imply that it does. Neither is named by the order.
**Follow-up:** both go on RodrigoFAbreu/workflow#113 as one comment at acceptance (the acceptance step posts it; this
plan does not, since nothing outward-facing is written before approval), so they are tracked on an issue.

## 1. Goal

Ship Workflow 2.25.6, a **`fix:` patch** (the manifest's version change and the pull-request title agree), with one
mechanism: **the report says `unreadable` where it cannot tell, and records the right path.** Four text and data
corrections, nothing else moves: no JSON key, no refusal code, no exit code (the report still exits 0 for an incomplete
view), no engine data, no command file, no state or protocol field.

**Every other output stays byte-identical.** The only byte-different outputs are the five named: the archive and
folder fragments of a `Finished` line in the unreadable and `.removing` cases; the `path` string of a `read_errors`
entry that was wrong (so its `INCOMPLETE:` line); and, from the same entries, the **message text of the `unreadable`
refusal of `archive` and `remove`** (`{entry['path']} cannot be read (…)`, `workflow_retention.py` 1078 and 1620),
whose path is the corrected one and which names the first entry in path order, which can change with the paths. The
refusal **code** (`unreadable`), the exit code and the gate are unchanged: `_underneath` accepts the folder itself, so
a refusal that held still holds. A wrong path used to collapse two failures that shared it into one entry; they are
now two entries and the `N path(s)` count follows.

### Hard limits (the owner's sizing rule)

- One mechanism, two functions (`render_text`, `_review_folder`); the plan stays under about 350 lines. One review surface.
- **Two checkpoints** (CP1 the change, tests and page; CP2 the release 2.25.6).
- This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`,
  `.workflow-manager/`, managed blocks, the conformance workflow) stays untouched; the shipped copies under `payload/` change.

## 2. Facts this plan relies on (re-read at `e687d51`)

- `_archive_fact` returns `{present: False, readable: False, …}` when the `lstat` fails with anything but absence;
  `_ABSENT_ARCHIVE` has `readable: True`. `_review_folder` returns `complete: False` when the folder's `stat` or any step
  of its walk failed; `present` is then true only if the folder itself was seen. `report["removing"]` is the sorted
  list of directory names under `<archive-dir>/.removing/` (empty when that is a link or unreadable).
- `os.fwalk(top, dir_fd=…, follow_symlinks=False)` is a pre-order walk: it yields a directory, then visits its
  sub-directories in the order of `dirs`. A sub-directory it cannot open reaches `onerror` with `filename` set to the
  **base name only**; a sub-directory that is a symlink is listed in `dirs` and opened the same way: dropped silently when
  the open succeeds (then `samestat` differs), but **reaching `onerror` with the link's name when the open fails** (a link
  to a mode-000 directory; `LPR-R1-001`, reproduced). This was read in the 3.14 source and checked there; the 3.12 form (what CI runs, `workflow-conformance.yml:37`) is a recursion over the same order that calls `next()` on
  what `os.scandir` returns, so any wrapper of `scandir` must be an iterator (`LPR-R2-002`). `python3` here is 3.14 only and
  no workflow runs 3.14: CP1 and CP2 each run the new class explicitly under both `python3` and
  `/home/rodrigo/.local/bin/python3.12`. The first open of the top is not routed to `onerror`.
- Tests: `RetentionReport` and the helpers `_RR`, `_rr_many`, `_rr_item`, `_rr_snapshot` of
  `payload/scripts/workflow_state_completion_obligations_test.py`; `RetentionReport.test_t7c` already provokes these
  states with `chmod` and skips as root. The new tests inject the errors instead, so they run as any user.

## 3. Design decisions

### D-Text: three fragments, one precedence

In `render_text`, per finished record (the only place the two fragments exist):

| Fragment | Condition (first that holds) | Text |
| --- | --- | --- |
| archive | `archive.present` | unchanged: `archive <size>, <n> days old[, prunable]` |
| | `not archive.readable` | `archive unreadable` |
| | otherwise | `no archive` |
| review folder | `folder.present` and `folder.complete` | unchanged: `<size> in <n> files` |
| | `folder.present` (partly counted) | `at least <size> in <n> files (partly unreadable)` |
| | `not folder.complete` | `review folder unreadable` |
| | the id is in `report["removing"]` | `review folder in .removing` |
| | otherwise | `no review folder` |

Reasons: *unreadable* is the report's own word (`readable`, `complete`, `INCOMPLETE`), and a size from a failed walk is
a lower bound, as `docs/RETENTION.md` already says. *Unreadable wins over `.removing`*: if the view is partial the report
cannot say where the folder is, and the `Interrupted removals` section still names the id. A folder that is present *and*
listed in `.removing` keeps its sizes (unchanged; that state is not the order's). The record keys are read with
`.get(key, True)` so a hand-built record without them renders as before. No other line (`tracked file(s)`, `Kept as recent`,
`Not finished`, `Archives`, `INCOMPLETE`, the stderr `warning: incomplete:`) is touched.

### D-Path: the parent from the walk itself

`walk_failed` cannot recover the parent from the exception (base name only). `_review_folder` keeps a list `pending`
of `(path, name)` pairs that mirrors the walk's pre-order, built from what the loop already receives (`path` is what
the walk would yield for it: `os.path.join(directory, name)`):

1. on each yielded `directory`: if some entry of `pending` has `path == directory`, truncate `pending` to the part
   below it and drop it (what was above it was a sub-directory the walk never yielded); with **no match leave
   `pending` untouched**. Then push, for each `sub` in `reversed(dirs)`, the entries the walk can still fail on: a real
   directory (`os.stat(sub, dir_fd=dirfd, follow_symlinks=False)`), a failed `stat` (nothing is hidden), and a **symlink
   whose open fails** when tried the way the walk opens it (`os.open(sub, os.O_RDONLY | os.O_NONBLOCK, dir_fd=dirfd)`,
   closed at once on success). A symlink whose open succeeds is dropped silently by the walk, so it is not pushed: that
   keeps it from masquerading as a failed directory of the same name;
2. in `walk_failed`: search `pending` from the top for the name `exc.filename`; on a match, truncate to it, drop it,
   and its parent gives `.ai-review/<parent>/<name>`; **on no match leave `pending` intact** and record the review
   folder's own path, as it already does when `filename` is missing. `here` is removed.

Search-first in both steps is what keeps one unexplained failure from consuming the entries of later ones. One extra
`lstat` per sub-directory, plus one `open` and `close` per symlinked sub-directory; nothing is read or written beyond
that. The data change: `read_errors[].path` is the failed directory, not its predecessor. `complete`, the counted files
and bytes do not move.

### D-Tests

Written first, red against the unedited tree, in a new class `RetentionReportUnreadable` next to `RetentionReport`. The
errors are injected, not provoked, so they hold as root: `os.lstat` raises `PermissionError` for the archive path
(`_archive_fact`); `os.stat` raises for `("w00", dir_fd=<fd>)` (the folder's own `stat`); `os.open` raises for a
real directory named `zz` opened with `dir_fd` (the walk) -- widened for the link layouts of T4: `os.open` raises for
the **symlink** named in the layout, which is what a link to a mode-000 directory does -- and `os.scandir` is wrapped to
list entries sorted by name so the visiting order is fixed; the wrapper is an **iterator** (`__iter__`/`__next__`, `__enter__`,
`close`), because 3.12's `os.walk` calls `next()` on it, and it is lifted before `_rr_snapshot` (which walks) runs. Every case asserts the exact text line, the JSON facts as pinned literals (`archive` is the
absent dict with `readable: False`; `review_folder` has exactly its six keys), exit 0, the unchanged stderr warning
and `_rr_snapshot` identical before and after (nothing written or removed).

| Test | Proves |
| --- | --- |
| T1 archive | `archive.readable` false: `archive unreadable` for an item with and without a folder; absent and readable: `no archive`; present: unchanged. Control: the same report with the injection removed prints the base text |
| T2 folder | folder `stat` denied: `review folder unreadable`; walk denied below the root: `at least 5 B in 1 files (partly unreadable)` with `complete: False`; absent and complete: `no review folder`; complete: `5 B in 1 files` |
| T3 `.removing` | id in `removing`, folder absent: `review folder in .removing`, with the archive fragment unchanged beside it; not in `removing`: `no review folder`; unreadable and in `removing`: `review folder unreadable`; present and in `removing`: sizes unchanged |
| T4 path | layouts `empty` + `zz`; `a/b/c` + `zz`; `a/zz` and `zz` both failing (two entries, `w00/a/zz`, `w00/zz`); `a/zz` a symlink to a directory whose open **succeeds** and `w00/zz` failing (`w00/zz` only); **`a/zz` a symlink whose open fails and `w00/zz` a readable real directory (`w00/a/zz` only, `w00/zz` not named)**; **such a link `a/lnk` before a really unreadable `zz` (two entries, `w00/a/lnk`, `w00/zz`)**; **such a link and a failure in a later sub-tree `m/deep` (two entries)**; **`a/lnk` a symlink whose probe open succeeds and whose walk open fails (the injection fails the link's second open) with `w00/zz` really failing: the fallback `w00` for the link and `w00/zz`, the later failure intact (`LPR-R2-001`)**; a clean tree (`read_errors == []`, same counts) |
| T6 refusals | `archive` and `remove` of an item with a failing sub-directory (injected, T4's `empty` + `zz` layout; `remove` needs a verified archive first, else it refuses `not_archived` before the `read_errors` loop, so that case archives the clean folder, then injects, and sits under the `_HAVE_ZSTD` guard of the archive tests): code `unreadable`, exit code unchanged, nothing written, and the message names the corrected path `…/w00/zz` (not `…/w00/empty/zz`) |
| T5 unchanged | a mixed report's whole text equals a golden string for every unaffected line; `render_text` leaves the report equal to a deep copy; the `--json` output of each case has exactly the base keys; stdout of a clean report is byte-identical to a golden literal |

**Failure-only mutations** (each on a scratch copy; the named tests fail there, pass on the real file; results go to the
implementation bundle's `TEST_RESULTS.md`): m1 archive fragment back to `no archive` (T1); m2 `archive unreadable` for
any absent archive (T1 control); m3 an unreadable folder back to `no review folder` (T2); m4 the lower-bound wording
dropped (T2); m5 `review folder unreadable` for every absent folder (T2 control, T3); m6 the `.removing` branch removed
(T3); m7 `.removing` ahead of unreadable (T3); m8 `walk_failed` back to the last yielded directory (T4, T6); m9 `pending`
without the real-directory filter (T4, the symlink layout); m10 a new key in `review_folder` (T5); m11 a failed-open
symlink dropped from `pending` instead of kept (T4, the three link layouts); m12 `pending` cleared when `walk_failed`
finds no match (T4, the probe-succeeds/walk-fails link layout only: every other layout finds its entry; clearing at a yielded
directory is an equivalent mutant and is not asked for).

### D-Docs

`docs/RETENTION.md`, the paragraph "A path that does not exist is absence…": the text form says `archive unreadable`
and `review folder unreadable` for what the report could not read (a partly counted folder `at least …`), `review
folder in .removing` for a folder left by an interrupted removal, and `no archive` / `no review folder` for absence,
with **named exceptions** the text cannot yet tell apart (an archive directory that is itself a link, and an
`.ai-review` that cannot be opened): there `INCOMPLETE` names the path. "Absence" includes an entry that is not a real
directory or regular file (a `.ai-review/w00` or `w00.tar.zst` that is a symlink, `docs/RETENTION.md:666`). It says nothing of an item folder that cannot
be opened at all (the report fails there). The path in `read_errors` is the directory that could not be read, and the
`unreadable` refusal of `archive` and `remove` names it; the text said `no archive` / `no review folder` there, and
the path of the previous directory, before Workflow 2.25.6. `docs/exit-codes.md` is not touched (no exit code or refusal changes). No page names an
internal milestone id; "Last checked with" of `docs/RETENTION.md` moves in CP2.

### D-Release

2.25.6, a **`fix:` patch**. `manifest.json` `workflow_version` 2.25.6; the changed records (`workflow_retention.py`, the
test file, `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`) take their sentence, `sha256` and `size`;
no file is added or removed, so counts and `distribution` do not move; `conformance.suites` is measured by `release.py
manager-block --write` (the test file gains the new class). `WORKFLOW_RELEASE` becomes 2.25.6 with its pinned assertions and
the protocol document's example (protocol stays 1.5); `tools/release/release_test.py` gets a 2.25.6 class and the
2.25.5 class gives up the current-release pins. `docs/release-history.md`: the 2.25.6 row; the way back to 2.25.5
restores the old text and the wrong path (archives and engine data are unchanged).

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w38-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256`
and `size` of every record whose file differs from its record (no record is added, so counts and the release-test
counts do not move), measures `conformance.suites` with `release.py manager-block --release-dir <scratch> --write`,
commits in the clone and runs the "Verification commands" of `docs/RELEASING.md` from there. `tools/release` tests run with
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
The new tests also run under the Manager's orphan rule (the reaper). CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **`at least … (partly unreadable)`** for a partly counted folder. The order asks only for "a lower bound"; this wording
  keeps the `files` count, which is a lower bound too.
- **Unreadable before `.removing`** (D-Text). The alternative hides that the view is partial.
- **Not fixing the seen-on-the-way cases** (section 0). (a) the symlinked archive directory and the unopenable
  `.ai-review` could be handled in `render_text` from `read_errors` (so not blocked by the JSON), at the price of a second
  mechanism; (b) the mode-000 item folder is a traceback, a different fix. **Recommendation: leave both out, track them
  on #113** (section 0); the owner may instead ask for (a) in this patch, which adds T1/T2 cases and a mutation.
- **The `pending` list** relies on `os.fwalk`'s pre-order and its handling of links; it is tested under 3.12 and 3.14, each run explicitly in CP1 and CP2 (section 2). Search-first matching means a mismatch leaves the later entries intact and
  falls back to the review folder's own path for that failure only, never to a wrong directory.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The report text, the recorded path, tests and page | - | 2 | 1 |
| CP2 | Release 2.25.6 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The report text, the recorded path, tests and page

**Files:** `payload/scripts/workflow_retention.py`, `payload/scripts/workflow_state_completion_obligations_test.py`,
`docs/RETENTION.md`.

- **Tests first** (D-Tests): T1 to T6 written and run red against the unedited tree; mutations m1 to m12 each fail the
  named tests on a scratch copy and the results are recorded; the class also runs green under 3.12 and 3.14 (below).
- **The change** (D-Text, D-Path): the two fragments in `render_text`; the `pending` list replacing `here` in
  `_review_folder`; the `unreadable` refusals of `archive` and `remove` change only through the corrected paths. Every existing test passes unmodified; the diff of the script touches those two functions only.
- **The page** (D-Docs). `check_docs.py` stays clean; "Last checked with" unchanged until CP2.
- **No other mechanism:** `git diff e687d51 --stat -- payload` lists the script and its test only; `docs/ROADMAP.md`
  carries row 33 as `Current` (written with this plan; `Done` at acceptance).

**Verification:** `RetentionReportUnreadable` under `python3` (3.14) and `/home/rodrigo/.local/bin/python3.12`; D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`,
`check-manager-block`, `tools/release` (zlib-ng interpreter, no patch, no skip).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.6

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.6 with its pinned assertions and the matching protocol-document edits (protocol 1.5).
- `manifest.json` 2.25.6 (D-Release): `workflow_version`, the changed records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.6 row and its "Last checked with" line; that of `docs/RETENTION.md` moves to
  2.25.6; `docs/exit-codes.md` stays at 2.25.5 (unchanged page).
- `tools/release/release_test.py`: a 2.25.6 class; the 2.25.5 class gives up the current-release pins.

**Verification:** `RetentionReportUnreadable` again under both interpreters; the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build
--commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; `workflow-manager
verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its
`.ai-review/`, the real archive store, the real forge or the network; no `apply` is ever run.** Setup, once, under `$TMPDIR`:
`base/` from `git archive e687d51 payload/scripts` and `cand/` from the working tree (run with `TMPDIR` on any file
system: the harness sorts directory listings, so the order is the same everywhere). **Every flow runs under both
`python3` (3.14) and `/home/rodrigo/.local/bin/python3.12`, the version CI runs.** The harness below builds its own
scratch repository (six finished items; `w00` holds `a.txt`, `empty/x`, `zz/q.txt` and a 20-byte archive 40 days old),
applies one stand-in, prints the text, the pinned JSON facts and whether the tree changed, and passes the forge seam
(`run=`) so no `gh` is needed. Save it outside the scratch repository as `flow.py` and run
`python3 -I flow.py <base|cand>/payload/scripts <case>` for `clean`, `archive`, `folder`, `partial`, `removing`.

```python
import contextlib, datetime, hashlib, io, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
scripts, case = sys.argv[1], sys.argv[2]; sys.path.insert(0, scripts)
_scandir = os.scandir
class _Sorted:                       # directory listings in name order; an iterator, as 3.12's os.walk needs
    def __init__(self, items): self._it = iter(items)
    def __enter__(self): return self
    def __exit__(self, *exc): return None
    def __iter__(self): return self
    def __next__(self): return next(self._it)
    def close(self): pass
def _sorted_scandir(path):
    with _scandir(path) as it: return _Sorted(sorted(it, key=lambda e: e.name))
os.scandir = _sorted_scandir
import workflow_retention as wr
NOW = datetime.datetime(2026, 11, 1, 12, tzinfo=datetime.timezone.utc)
root, store = Path(tempfile.mkdtemp(prefix="flow-repo-")), Path(tempfile.mkdtemp(prefix="flow-store-"))
(store / "widgets").mkdir()
for cmd in (["git", "init", "-q"], ["git", "remote", "add", "origin", "https://github.com/acme/widgets.git"]):
    subprocess.run(cmd, cwd=root, check=True)
def put(rel, data="1"):
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(data)
put("docs/ai-workflow/WORKFLOW_STATE.json", json.dumps({"work_items": {f"w0{n}": {"phase": "MILESTONE_COMPLETE",
    "last_transition": f"2026-09-0{n + 1}T00:00:00Z", "parent_work_item_id": None,
    "reviewed_implementation_head": f"{n:040x}"} for n in range(6)}}))
put(".ai-review/w00/a.txt", "12345"); put(".ai-review/w00/empty/x"); put(".ai-review/w00/zz/q.txt", "123")
arc = store / "widgets/w00.tar.zst"; arc.write_bytes(b"x" * 20); os.utime(arc, (NOW.timestamp() - 40 * 86400,) * 2)
undo = []
def deny(path, mode=0):
    undo.append((path, os.stat(path).st_mode & 0o7777, mode)); os.chmod(path, mode)
if case == "archive": deny(store / "widgets")                     # archive directory not searchable
if case == "folder": deny(root / ".ai-review", 0o644)             # readable, not searchable
if case == "partial": deny(root / ".ai-review/w00/zz")            # one sub-directory not openable
if case == "removing":
    shutil.rmtree(root / ".ai-review/w00"); (store / "widgets/.removing/w00").mkdir(parents=True)
def main(*extra):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = wr.main(["report", "--repo-root", str(root), "--archive-root", str(store), *extra],
            run=lambda argv, timeout: json.dumps([{"number": 7, "url": "https://github.com/acme/widgets/pull/7",
                                                   "state": "MERGED", "headRefOid": "a" * 40}]),
            resolve=lambda r: {"path": "/usr/bin/gh", "sha256": "0" * 64}, now=NOW)
    return code, out.getvalue(), err.getvalue()
def tree():                      # the permissions are lifted for the hash, then put back
    for path, old, _ in undo: os.chmod(path, old)
    try:
        return hashlib.sha256(repr([(d, sorted(n), sorted(f)) for r in (root, store)
                                    for d, n, f in sorted(os.walk(r)) if ".git" not in d]).encode()).hexdigest()
    finally:
        for path, _, mode in undo: os.chmod(path, mode)
before = tree(); code, text, err = main(); jcode, js, _ = main("--json")
scrub = lambda s: s.replace(str(root), "REPO").replace(str(store), "STORE")
print("exit", code, jcode); print(scrub(text.split("\nKept")[0]).split("\n", 4)[4].rstrip())
print("read_errors:", [scrub(e["path"]) for e in json.loads(js)["read_errors"]], "| stderr:", scrub(err)[:44])
doc = json.loads(js); last = doc["finished"][-1]
print("json:", json.dumps({"complete": doc["complete"], "removing": doc["removing"], "folder": last["review_folder"],
                           "archive": {k: last["archive"][k] for k in ("present", "readable")}}, sort_keys=True))
print("tree unchanged:", tree() == before)
for path, old, _ in reversed(undo): os.chmod(path, old)
shutil.rmtree(root, ignore_errors=True); shutil.rmtree(store, ignore_errors=True)
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `clean` with base and cand | the two outputs are identical byte for byte: `w00: 9 B in 3 files; archive 20 B, 40 days old, prunable`, `w01` and `w02` `no review folder; no archive` (true absences), exit `0 0`, `tree unchanged: True` |
| 2 | `archive` with base and cand (the archive directory is not searchable) | base: `w00: 9 B in 3 files; no archive`. cand: `w00: 9 B in 3 files; archive unreadable` (and `w01`, `w02`: `no review folder; archive unreadable`); exit `0 0`; the same `read_errors` and `warning: incomplete:` line; `json:` line identical in both (`readable: False`, `complete: false`); `tree unchanged: True` |
| 3 | `folder` with base and cand (`.ai-review` readable, not searchable) | base: `w00: no review folder; archive 20 B, 40 days old, prunable`. cand: `w00: review folder unreadable; archive 20 B, 40 days old, prunable`; `json:` identical (`folder` has `present: false, complete: false`); `tree unchanged: True` |
| 4 | `partial` with base and cand (`w00/zz` not openable) | base: `w00: 6 B in 2 files; …` and `read_errors` `REPO/.ai-review/w00/empty/zz`. cand: `w00: at least 6 B in 2 files (partly unreadable); …` and `REPO/.ai-review/w00/zz`; `complete: false` and the counts in `json:` identical; `tree unchanged: True` |
| 5 | `removing` with base and cand (the folder moved to `.removing/w00`) | base: `w00: no review folder; archive 20 B, …`. cand: `w00: review folder in .removing; archive 20 B, …`; the `Interrupted removals (1): w00` line and the `json:` line (`removing: ["w00"]`, `complete: true`) identical |
| 6 | `python3 -I flow.py cand/payload/scripts clean`, then `git diff e687d51 --stat -- payload docs` in the working tree (CP1) | no `.ai-review` or store write; the diff lists the script, its test and `docs/RETENTION.md` only (plus plan, registry, mapping, declaration, roadmap and `docs/ai-workflow/WORKFLOW_STATE.json`); the script diff touches `_review_folder` and `render_text` only |
| 7 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` and its checker, `check-manager-block` with `--manager-releases`, and the `tools/release` tests with the zlib-ng interpreter | all pass, no skip; the new class runs under the Manager's orphan rule (reaper) |
| 8 | (needs the full environment) scope: `git diff e687d51 --stat` at CP2 | CP2 adds `manifest.json`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md` and `tools/release/release_test.py`; the history row, manifest and page agree on 2.25.6; no command file, no `docs/exit-codes.md` |

## 7. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #113 item 1 | `archive unreadable`, `review folder unreadable`, a lower bound for a partial size | CP1 | D-Text, T1, T2, m1 to m5 |
| #116 item 1 | the failed directory's parent in `read_errors`, links included | CP1 | D-Path, T4, T6, m8, m9, m11, m12 |
| #119 item 8 | `review folder in .removing` | CP1 | D-Text, T3, m6, m7 |
| Row 33 | JSON, refusal codes, exit codes, other lines byte-identical; the outputs that change are five: the three text fragments' lines, the path string, the `unreadable` refusal message | CP1 | T5, T6, m10; the one data change is the path string |
| Row 33 | the release is a `fix:` patch, 2.25.6 | CP2 | D-Release |
| #113 items 2 to 7, #116 items 2 to 7, #119 items 1 to 7 | not here | stay on their issues | section 0 |
| seen-on-the-way cases (symlinked archive directory, unopenable `.ai-review`, mode-000 item folder) | not here | one comment on #113 at acceptance | section 0, open decision 1 |

The artifact declaration `docs/ai-workflow/registry/retention-report-unreadable-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations` and then extended by hand for `payload/`, `tools/`, `fixtures/`,
`templates/`, `manifest.json`, `docs/RETENTION.md`, `docs/exit-codes.md` and `docs/release-history.md`, as the earlier
retention items' were; every path a checkpoint's **Files** paragraph names is classified at both stages.
