# Active Milestone

## Milestone

**Awaiting functional review** (`AWAITING_FUNCTIONAL_REVIEW`). W31: `retention-prune` (`process`, governing version `2.2`), branch
`milestone/retention-prune`, roadmap row 27f (RodrigoFAbreu/workflow#113 item 3, #119 item 7 and #123). Plan:
`docs/ai-workflow/RETENTION_PRUNE_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.24.0 (a `feat:`
minor): the prune engine, a fourth subcommand of `scripts/workflow_retention.py`:
`prune <work-item-id>... [--apply] [--json] [--ttl-days N]`. It removes the named archives `<id>.tar.zst` past the time
to live, one checked and durable `unlink` each, never opens the index, and judges the whole run before the first unlink.
The user-only command is row 27g and is not part of this item. Base commit `4529f21`; the previous milestone, W30
`retention-command`, is accepted (Workflow 2.23.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The prune engine, its tests and the documents | **complete** |
| CP2 | Release 2.24.0 | **complete** |

## Verified state

- CP1 changed `payload/scripts/workflow_retention.py` (`_check_id`, `_select_destination` and `_ttl_of` extracted with
  the existing behaviour; `prune_archives`, `render_prune_text`, the `prune` subcommand),
  `payload/scripts/workflow_state_completion_obligations_test.py` (class `RetentionPrune`, ten tests: P1 to P9, with P3b
  for the lock and the re-read under it, and P9 for the extracted helpers), `docs/RETENTION.md` (the section "The prune command") and
  `docs/exit-codes.md` (the `prune` rows). `git diff 4529f21 --stat -- payload` lists the script and its test file only.
- Verified in the disposable clone of D-Staging (the two changed manifest records re-hashed, `manager.conformance.suites`
  re-measured by `release.py manager-block --commit HEAD --write`; the release source stays 2.23.0): `RetentionPrune`
  and the three earlier retention classes 72 OK; the whole obligations chunk 265 OK under the orphan wrapper; `tools/release`
  288 OK (zlib-ng); `tools/docs` 34 OK; `check_docs.py` rc 0; `check-manager-block` ok.
- Mutations m1 to m17 each fail at least one named `RetentionPrune` case in a scratch copy; the control passes.

## Next action

The user performs the manual functional review below (a hard gate; the agent stops here). Implementation revision 2 and
the technical approval are current against the reviewed content commit `766aead`. Findings go to
`.ai-review/retention-prune/feedback/FUNCTIONAL_REVIEW.md`; `/apply-functional-review` routes each one: a same-scope fix
takes its bounded branch, new or wider scope a `retention-prune-remediation-<n>` item. Once testing is clean,
`/accept-milestone` is the only acceptance command. CP1 and CP2 are both complete, so nothing else is outstanding.

## Functional review checklist

Scope: the `prune` subcommand of `payload/scripts/workflow_retention.py` as shipped by Workflow 2.24.0. Flows 1 to 6 run
offline, in a scratch repository and a scratch archive root. Flow 7 needs a real `gh` login (it reads a merged pull request),
so it cannot run in a sandbox without GitHub access.

### Setup

- Check out `milestone/retention-prune`. `git status` shows only `docs/ROADMAP.md`, an unrelated change that is not part of this item.
- No build or install. Tools on the PATH: `python3`, `git`, `zstd` (flow 7 only), `touch`, `stat`, `sha256sum`, `find`. Use bash.
- Run the release-source script `payload/scripts/workflow_retention.py`. The installed `scripts/workflow_retention.py` is the
  2.23.0 copy and has no `prune` (`grep -c "def prune_archives" scripts/workflow_retention.py` prints `0`).
- Never run `prune --apply` without `--archive-root`: the default is your real archive store, `~/.local/share/workflow-archive`.

```bash
CK=$PWD; S=$(mktemp -d); R=$S/repo; ARC=$S/archive; A=$ARC/prune-check
prune() { python3 -I "$CK/payload/scripts/workflow_retention.py" prune "$@" --archive-root "$ARC" --repo-root "$R"; }
mkdir -p "$R/docs/ai-workflow" && mkdir -m 700 "$ARC" && mkdir -m 700 "$A"
git -C "$R" init -q && git -C "$R" remote add origin https://github.com/scratch-owner/prune-check.git
printf '%s\n' '{"schema_version": 1, "active_work_item_id": "open-item", "work_items": {"open-item": {"phase": "AWAITING_FUNCTIONAL_REVIEW"}}}' > "$R/docs/ai-workflow/WORKFLOW_STATE.json"
git -C "$R" add -A && git -C "$R" -c user.email=t@t -c user.name=t commit -qm init
```

### Test data

The archives are random bytes. `prune` reads their names, `lstat` and modification times, never their contents.

```bash
mk() { head -c "$2" /dev/urandom > "$A/$1.tar.zst"; touch -d "$3" "$A/$1.tar.zst"; }
mk old-one 4096 '45 days ago'; mk old-two 2048 '45 days ago'; mk old-three 4096 '45 days ago'
mk young 1024 '2 days ago'; mk edge 1024 '30 days ago'; mk open-item 4096 '45 days ago'; mk left-over 4096 '45 days ago'
mkdir -m 700 "$A/.removing" "$A/.removing/left-over"
printf '%s\n' '{"work_item_id": "old-one"}' '{"work_item_id": "young"}' > "$A/index.jsonl"; touch -d '10 days ago' "$A/index.jsonl"
```

`open-item` is open in the scratch state. `left-over` has a leftover under `.removing`.

### Flows

1. **The dry run writes nothing.** `prune old-one old-two old-one`. Expected: exit 0; lists `old-one.tar.zst` and
   `old-two.tar.zst` (a name given twice counts once); prints `dry run: nothing was written`. Before and after: the archive
   listing, `index.jsonl` (bytes and mtime) and `git -C "$R" status` are identical.
2. **Apply removes only the named archives.** `prune old-one old-two --apply`. Expected: exit 0, `removed 2 archive(s)`.
   Gone: `old-one`, `old-two`. Still present: `old-three`, `young`, `edge`, `open-item`, `left-over`, `.removing/left-over`.
   `index.jsonl` keeps both lines, with unchanged bytes and mtime.
3. **Refusals touch nothing.** Each of these must exit 2, print `error: <code>:` on stderr, print nothing on stdout, and
   remove nothing:

   | Command | Expected code |
   | --- | --- |
   | `prune young --apply` | `not_prunable` (2 days old) |
   | `prune edge --apply` | `not_prunable` (exactly 30 days is not past the time to live) |
   | `prune open-item --apply` | `item_not_finished` (the item is open) |
   | `prune left-over --apply` | `removal_interrupted` |
   | `prune nope-such-id --apply` | `not_in_report` |
   | `prune Bad_ID --apply`, `prune runtime --apply` | `invalid_id` |
   | `prune old-three young --apply` | `not_prunable`: the whole run is refused, so `old-three` stays |
   | `python3 -I "$CK/payload/scripts/workflow_retention.py" prune young --archive-root "$CK/docs" --repo-root "$R" --apply` | `archive_inside_repository`, and no `docs/prune-check` is created |

4. **The time to live is a flag.** `prune edge young --ttl-days 1` (dry run). Expected: exit 0; lists both `edge.tar.zst`
   (30 days old) and `young.tar.zst` (2 days old).
5. **JSON.** `prune young --json` exits 2 with empty stdout. `prune edge --ttl-days 1 --json` prints one object with
   `"mode": "dry-run"`, `"kind": "retention-prune"` and `"result": {"bytes": 0, "removed": []}`.
6. **A pruned id is no longer listed.** After flow 2, `prune old-one` exits 2 with `not_in_report`, and `index.jsonl`
   still has its `old-one` line.
7. **A real archive of merged items (manual; needs `gh` and network).** Set `R="$CK"` so the commands use the checkout.
   Archive two finished items from the report's `Finished` list, then age them:

   ```bash
   W=$ARC/workflow; R="$CK"
   python3 -I "$CK/payload/scripts/workflow_retention.py" archive retention-report --apply --archive-root "$ARC" --repo-root "$CK"
   python3 -I "$CK/payload/scripts/workflow_retention.py" archive interleaving-pins --apply --archive-root "$ARC" --repo-root "$CK"
   touch -d '45 days ago' "$W/retention-report.tar.zst" "$W/interleaving-pins.tar.zst"
   ```

   - Each `archive` says `the review folder was not touched`; `"$CK/.ai-review/retention-report"` still exists, and
     `git -C "$CK" status --short` shows only `docs/ROADMAP.md`.
   - `prune retention-report --apply` (dry run first). Expected: exit 0, `removed 1 archive(s)`. `retention-report.tar.zst` is gone;
     `interleaving-pins.tar.zst` and `index.jsonl` (with its line) are untouched.
   - `archive retention-report` again. Expected: exit 2, `already_indexed`; the index keeps the line.
   - **Recent refusal.** Pick a name the report lists under `Kept as recent`. Copy an archive to it, age it, then
     `prune <that-name> --apply`. Expected: exit 2, `item_not_finished` ("is recent"); the archive stays. The report's
     `prunable` count may include this archive; prune refuses it, as designed.

### Expected limits and out of scope

- `prune` is only the engine. It writes no state, phase, trailer or commit. The user-only confirmation command is row 27g, a later row.
- `prune` never opens or rewrites `index.jsonl`. A pruned id stays indexed: `archive` then says `already_indexed` and `remove` says `not_archived`.
- `prune` removes no review folder, tracked file or index line. It does not finish a `.removing` leftover; it refuses one (flow 3).
- Not reproduced by hand: `archive_changed` (a file replaced between the preview and its `lstat`). The `RetentionPrune` unit tests cover it.
  Not claimed: a write between one archive's `lstat` and its `unlink`, a file-system crash, a hard link, or a restored mtime.
- Downgrading to 2.23.0 removes `prune`; archives already pruned stay pruned.
- The installed `scripts/workflow_retention.py` gets `prune` only when 2.24.0 is released and installed with `workflow-manager update`.
- Flow 7 cannot run in the Controller sandbox: its `gh` refuses, so a refusal there is an `environment` limit, not a `defect`.

Evidence: the checklist's evidence commit is the one whose message carries `Workflow-Functional-Checklist: retention-prune/2/<blob>`
(`git log --grep Workflow-Functional-Checklist`).

## CP2 record

CP2 changed `manifest.json` (2.24.0, five records, posture, obligations suite count 265), `workflow_protocol.py` and its test
(`WORKFLOW_RELEASE`), `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md` (2.24.0 row), the "Last checked with" lines of
`docs/RETENTION.md` and `docs/exit-codes.md`, and `tools/release/release_test.py` (2.24.0 class). Verified in a scratch clone of
the CP2 content: `stage-conformance` ok; nine suites OK (453, 344, 1244 via its own runner, 316, 142, 265, 370, 283, 27);
`build` ok (zlib-ng); `check-manager-block` ok; `tools/docs` 34 OK; `check_docs.py` rc 0; `tools/release` 291 OK (zlib-ng);
`workflow-manager verify .` clean against the installed 2.23.0.

CP2 is complete.
