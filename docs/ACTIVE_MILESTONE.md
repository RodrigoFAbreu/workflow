# Active Milestone

## Milestone

**Awaiting functional review.** W33: `retention-lstat-errors` (`process`, governing version `2.2`), branch
`milestone/retention-lstat-errors`, roadmap row 28 (RodrigoFAbreu/workflow#126 item 1). Plan:
`docs/ai-workflow/RETENTION_LSTAT_ERRORS_PLAN.md` (revision 4, approved by gate policy). The goal, Workflow 2.25.1 (a
`fix:` patch, released after the merge of the pull request): `_lstat_at` in `workflow_retention.py` turns a stat error
other than "not found" into a coded refusal with a `next step:` line (`unreadable` at the archive, remove and prune
sites, `restore_failed` while a refusal is undone, `prune_failed` at prune's step 9), instead of a traceback. No new
refusal code, state key, phase, trailer or command. Base commit `d101beb`; the previous milestone, W32
`retention-prune-command`, is accepted (Workflow 2.25.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The coded refusal, its call sites, tests and documents | **complete** (`62e3cc1`) |
| CP2 | Release 2.25.1 | **complete** (`44351fd`) |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `0b4f58ca`, reviewed implementation head `bea39a8`. Implementation revision 3.
- Automated verification, rerun for this checklist at `8912907` (the code under test is unchanged since `44351fd`):
  `tools/release` 296 tests OK (zlib-ng interpreter), `tools/docs` 34 tests OK, `check_docs.py` clean,
  `release.py check-manager-block` OK. The nine suites ran at `44351fd` (`TEST_RESULTS.md`) and were not rerun; no
  file they exercise has changed since. The later commits (`e8d90f7`, `bea39a8`) changed one row of
  `docs/release-history.md`, which only `tools/release` reads.
- Mutations m1 to m16 (plan D-Tests) were run on scratch copies at `44351fd`; their results are in `TEST_RESULTS.md`.
- Working tree: `docs/ROADMAP.md` has an uncommitted row 28 `Current` edit, written with the plan. It is not part of
  this checklist and stays uncommitted.

## Functional review checklist

### Setup

Paste the block below into a `bash` shell (not zsh) before each numbered case. It wipes and recreates the scratch run in
`$RUN`, outside the clone. It writes a fake `gh` (the engine's forge query, offline; a `gh` inside a temporary directory
or a world-writable one is refused by `resolve_gh`), the fault injector `inject.py`, and a scratch repository whose
`scripts/` is the candidate `payload/scripts/` (the 2.25.1 engine). Nothing runs against the real repository, its
`.ai-review/`, the real archive store, the forge or the network.

```sh
RUN=/home/rodrigo/.cache/w33-fr
CANDIDATE=/home/rodrigo/Workspace/workflow/payload/scripts
rm -rf "$RUN"; mkdir -p "$RUN/fakebin" "$RUN/tmp" "$RUN/home" "$RUN/store" "$RUN/repo"
cat > "$RUN/fakebin/gh" <<'GH'
#!/bin/sh
# fake gh: the engine runs `gh pr list --repo R --state all --search <sha> --limit N --json ...`
while [ $# -gt 0 ]; do [ "$1" = "--search" ] && sha="$2"; shift; done
printf '[{"number":7,"url":"https://github.com/acme/widgets/pull/7","state":"MERGED","headRefOid":"%s"}]\n' "$sha"
GH
chmod 755 "$RUN/fakebin/gh"
cat > "$RUN/inject.py" <<'PY'
"""Fault injector. python3 -I inject.py <site> <name> <ERRNO> [--skip N] -- <engine args>
Counts only os.stat calls made by _lstat_raw (through _lstat_at, or directly), walks up past the helpers to the
first other frame, and raises OSError(ERRNO) when that frame is <site>. --skip N lets the first N matches through."""
import errno, os, sys

args = sys.argv[1:]
site, name, err = args[0], args[1], args[2]
rest = args[3:]
skip = 0
if rest[:1] == ["--skip"]:
    skip, rest = int(rest[1]), rest[2:]
assert rest[:1] == ["--"], "expected -- before the engine arguments"
engine_args = rest[1:]

sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
sys.dont_write_bytecode = True
import workflow_retention as wr

code = getattr(errno, err)
real_stat = os.stat
matches = [0]
HELPERS = ("_lstat_at", "_lstat_raw")


def fake_stat(path, *a, **kw):
    caller = sys._getframe(1)
    if path == name and kw.get("dir_fd") is not None and caller.f_code.co_name == "_lstat_raw":
        frame = caller
        while frame is not None and frame.f_code.co_name in HELPERS:
            frame = frame.f_back
        if frame is not None and frame.f_code.co_name == site:
            matches[0] += 1
            if matches[0] > skip:
                raise OSError(code, os.strerror(code), path)
    return real_stat(path, *a, **kw)


os.stat = fake_stat
rc = wr.main(engine_args)
print(f"injector: exit={rc} matches={matches[0]}")
sys.exit(rc)
PY
cd "$RUN/repo" && git init -q -b main . && git config user.email t@example.invalid && git config user.name t
git remote add origin https://github.com/acme/widgets.git
mkdir -p scripts && cp "$CANDIDATE"/*.py scripts/
echo x > README && git add -A && git commit -qm init
python3 -I - "$(git rev-parse HEAD)" <<'PY'
import json, os, sys
sha = sys.argv[1]
items = {f"m-{i}": {"phase": "MILESTONE_COMPLETE", "reviewed_implementation_head": sha,
                    "last_transition": f"2026-10-{i:02d}T12:00:00Z"} for i in range(1, 9)}
items["m-9"] = {"phase": "AWAITING_FUNCTIONAL_REVIEW", "reviewed_implementation_head": sha}
os.makedirs("docs/ai-workflow", exist_ok=True)
json.dump({"schema_version": 1, "active_work_item_id": "m-9", "work_items": items},
          open("docs/ai-workflow/WORKFLOW_STATE.json", "w"), indent=1)
for name in items:
    os.makedirs(f".ai-review/{name}/feedback", exist_ok=True)
    open(f".ai-review/{name}/feedback/REVIEW_FEEDBACK.md", "w").write(f"scratch {name}\n")
PY
export PATH="$RUN/fakebin:/usr/bin:/bin" HOME="$RUN/home" TMPDIR="$RUN/tmp" XDG_CACHE_HOME="$RUN/home/.cache" \
  XDG_DATA_HOME="$RUN/home/.local/share" PYTHONDONTWRITEBYTECODE=1
E="--archive-root $RUN/store --repo-root $RUN/repo"
I="python3 -I $RUN/inject.py"
```

Every command below runs in that shell from `$RUN/repo` (`cd "$RUN/repo"`), with `$E` and `$I` as set above.
Commands that do not use `$I` are the plain engine; `--apply` is the write.

### Test data

Eight finished items `m-1` to `m-8` (`MILESTONE_COMPLETE`, each with a merged pull request `#7` from the fake `gh`,
`last_transition` rising with the number) and one open item `m-9`. With `KEEP_RECENT = 3`, `m-6`, `m-7` and `m-8` are
kept and `m-1` to `m-5` are archivable. Each `.ai-review/m-N/feedback/REVIEW_FEEDBACK.md` is 12 bytes. An archive is
aged for the prune cases with `touch -d 2026-08-01 "$RUN/store/widgets/<id>.tar.zst"` (over the 30-day time to live).

### Flows

Run each numbered case from a fresh setup, unless it says otherwise.

**1. No injection (regression).** Expect exit 0 each, and the same output lines as the 2.25.0 engine
(`git show d101beb:payload/scripts/workflow_retention.py`, run in a second copy of the scratch repository), apart from
timestamps.

```sh
python3 -I scripts/workflow_retention.py archive m-1 $E
python3 -I scripts/workflow_retention.py archive m-1 --apply $E
python3 -I scripts/workflow_retention.py remove m-1 --apply $E
touch -d 2026-08-01 "$RUN/store/widgets/m-1.tar.zst"
python3 -I scripts/workflow_retention.py prune m-1 --apply $E
```

**2. Archive, the three sites of the selection and the lock (S1a, S2, S1b).**

```sh
python3 -I scripts/workflow_retention.py archive m-2 --apply $E
$I _judge_archive_side m-1.tar.zst EACCES -- archive m-1 $E
$I _judge_archive_side m-1.tar.zst EACCES -- archive m-1 --apply $E
$I _judge_archive_side .m-1.partial EIO -- archive m-1 $E
$I _judge_archive_side .m-1.partial EIO -- archive m-1 --apply $E
$I _judge_archive_side m-1.tar.zst EIO --skip 1 -- archive m-1 --apply $E
ls -A "$RUN/store/widgets"
```

Expect: exit 2 each, `error: unreadable: <store>/widgets/m-1.tar.zst cannot be examined: EACCES Permission denied` (for
`.m-1.partial`, that name), and a `next step:` naming the same path. No traceback. The last one (under the lock) adds
"nothing was archived; the temporary and the directories this run created were removed". `ls` shows only `index.jsonl`
and `m-2.tar.zst`: no `.partial`.

Then, from a fresh setup with no archive directory yet (S1b as the first match):

```sh
$I _judge_archive_side m-1.tar.zst EIO --skip 0 -- archive m-1 --apply $E
ls -A "$RUN/store"
python3 -I scripts/workflow_retention.py archive m-1 --apply $E
```

Expect: exit 2, `unreadable` naming `<store>/widgets/m-1.tar.zst`; `ls` prints nothing (the directories the walk created
were removed); the last command, with no injector, exits 0.

**3. Removal, the selection's probes and the lock re-run (S3, S4).**

```sh
python3 -I scripts/workflow_retention.py archive m-1 --apply $E
$I _judge_removal_archive m-1.tar.zst EACCES -- remove m-1 $E
mkdir -p "$RUN/store/widgets/.removing/m-1"
$I _select_removal m-1 ELOOP --skip 0 -- remove m-1 $E
$I _select_removal m-1 ELOOP --skip 1 -- remove m-1 $E
$I _select_removal m-1 ELOOP --skip 2 -- remove m-1 $E
rm -rf "$RUN/store/widgets/.removing"
$I _select_removal m-1 ELOOP --skip 1 -- remove m-1 --apply $E
```

Expect: S3 exits 2 `unreadable` naming `<store>/widgets/m-1.tar.zst`. The three probes, with `.removing` present, exit 2
naming `<store>/widgets/.removing/m-1` (`--skip 0`), `<repo>/.ai-review/m-1` (`--skip 1`) and
`<store>/widgets/.removing/m-1` again (`--skip 2`). The lock re-run (`--apply`, no `.removing`, `--skip 1`) exits 2
naming `<repo>/.ai-review/m-1`. In every case the folder stays in `.ai-review/m-1`, nothing is moved or deleted, and each
`next step:` is present. (With no `.removing` the selection makes one matching probe, so the lock re-run is the second
match: `--skip 1`. The plan's "`--skip 2`" for the re-run does not apply.)

**4. Before the rename (S5).**

```sh
python3 -I scripts/workflow_retention.py archive m-1 --apply $E
$I _flow m-1 EACCES -- remove m-1 --apply $E
ls -A "$RUN/store/widgets"
python3 -I scripts/workflow_retention.py remove m-1 --apply $E
```

Expect: exit 2 `unreadable` naming `<store>/widgets/.removing/m-1`, "nothing was moved or deleted". The folder is still in
`.ai-review/m-1`, and `ls` shows no `.removing`. The last command, with no injector, exits 0 (the resume).

**5. After the rename (S6), the two states.**

`L0`: this run renamed the folder.

```sh
python3 -I scripts/workflow_retention.py archive m-1 --apply $E
$I _flow m-1 EIO --skip 1 -- remove m-1 --apply $E
python3 -I scripts/workflow_retention.py remove m-1 --apply $E
```

Expect: exit 2 `unreadable` naming `<store>/widgets/.removing/m-1`; `next step:` says the folder is whole there, nothing
was renamed back or deleted, and to run `remove m-1 --apply` again. The resume exits 0.

`L1`: an earlier stopped run left `.removing/m-1`, possibly incomplete (made here by moving the folder and removing one
file).

```sh
python3 -I scripts/workflow_retention.py archive m-1 --apply $E
mkdir -p "$RUN/store/widgets/.removing"
mv "$RUN/repo/.ai-review/m-1" "$RUN/store/widgets/.removing/m-1"
rm -f "$RUN/store/widgets/.removing/m-1/feedback/REVIEW_FEEDBACK.md"
$I _flow m-1 EIO --skip 0 -- remove m-1 --apply $E
python3 -I scripts/workflow_retention.py remove m-1 --apply $E
```

Expect: exit 2 `unreadable` naming `<store>/widgets/.removing/m-1`; `next step:` says the leftover is untouched, may be
incomplete, and that the missing entries exist only in the archive. It must never say "whole". Nothing is renamed or
deleted: `.removing/m-1` keeps its `feedback` directory without the removed file. The last command, with no injector,
resumes and exits 0.

**6. Prune's step 9 (S8).** Expect exit 2 both times, and every archive still present.

```sh
for i in 1 2 3; do python3 -I scripts/workflow_retention.py archive m-$i --apply $E; done
for i in 1 2 3; do touch -d 2026-08-01 "$RUN/store/widgets/m-$i.tar.zst"; done
$I _prune_select m-1.tar.zst EACCES -- prune m-1 m-2 m-3 $E
$I _prune_select m-1.tar.zst EACCES -- prune m-1 m-2 m-3 --apply $E
```

Expect: `prune_failed: m-1.tar.zst could not be examined: EACCES Permission denied; removed: none; not removed: m-1, m-2, m-3`,
and a `next step:` naming `<store>/widgets`.

**7. Prune's steps 12 and 13a, unchanged.** Each case from its own fresh setup, archives aged as in flow 6.

```sh
$I _unchanged m-2.tar.zst EIO --skip 0 -- prune m-1 m-2 m-3 --apply $E
$I _unchanged m-2.tar.zst EIO --skip 1 -- prune m-1 m-2 m-3 --apply $E
```

Expect: `--skip 0` (step 12, before any unlink) exits 2 `prune_failed` with `removed: none; not removed: m-1, m-2, m-3`,
all archives present. `--skip 1` (step 13a, after `m-1` was removed) exits 2 with `removed: m-1; not removed: m-2, m-3`;
`m-1` is gone, `m-2` and `m-3` remain. The message keeps the bare `m-2.tar.zst`: that text is `_check_unchanged`'s, unchanged.

**8. A real permission error (not as root only).** Run it only when `id -u` is not 0; as root, say so and mark the flow not
run.

```sh
python3 -I scripts/workflow_retention.py archive m-2 --apply $E
touch -d 2026-08-01 "$RUN/store/widgets/m-2.tar.zst"
chmod 0600 "$RUN/store/widgets"
python3 -I scripts/workflow_retention.py archive m-2 --apply $E
python3 -I scripts/workflow_retention.py remove m-2 --apply $E
python3 -I scripts/workflow_retention.py prune m-2 --apply $E
chmod 0700 "$RUN/store/widgets"
```

Expect: each of the three exits 2 with the report's own `unreadable: <store>/widgets/.removing cannot be read
(PermissionError ...)` and a `next step:`, with no traceback. The archive and the index are unchanged.

**9. Documents, help and the diff (from the clone; read-only).** Expect the diff under `payload/` to list the retention
script and its test, `workflow_protocol.py` and its test, and `ORCHESTRATION_PROTOCOL.md`; under `docs/`, `RETENTION.md`,
`exit-codes.md`, `release-history.md` and the plan's own files; and `--help` to list only `report`, `archive`, `remove`
and `prune`.

```sh
cd /home/rodrigo/Workspace/workflow && git diff d101beb --stat -- payload docs
PYTHONDONTWRITEBYTECODE=1 python3 -I "$RUN/repo/scripts/workflow_retention.py" --help
```

### Known limitations and out of scope

- The faults are injected (`os.stat` raises `OSError`), so the errno and the path are real but the cause is not a real
  permission. A real permission error is flow 8, and it runs only as a non-root user. As root it is not run.
- The forge is the fake `gh`: offline, it reports the merged pull request `#7` for every commit. No real GitHub is used.
  Every flow that archives, removes or prunes queries it, so each needs the fake `gh` first on `PATH`.
- `_has_leftover` still treats a stat error as "no leftover" (plan section 4 and 7; a follow-up on #126). No flow tests it.
- Not in this change: #126 items 4 and 5, #123 items 2 to 6, and the release publication (2.25.1 is published only after
  the merge).

### Next steps

- Findings go to `.ai-review/retention-lstat-errors/feedback/FUNCTIONAL_REVIEW.md`. `/apply-functional-review` routes each
  one: a bounded fix for the same scope, or a `retention-lstat-errors-remediation-<n>` child for new or wider scope.
- Once testing is clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint in this item's
  registry to be `COMPLETE`, and both (CP1 and CP2) are.

## Next action

The user runs the functional review above and places any findings in `.ai-review/retention-lstat-errors/feedback/FUNCTIONAL_REVIEW.md`.
Nothing else is outstanding for this item.
