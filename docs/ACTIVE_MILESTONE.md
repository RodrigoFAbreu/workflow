# Active Milestone

## Milestone

**In progress.** W51: `retention-engine-error-paths-2` (`process`, governing version `2.2`), branch
`milestone/retention-engine-error-paths-2`, roadmap row 44 (RodrigoFAbreu/workflow#119 items 1 and 3, #149 items 1, 2 and 5,
#143 item 4). The plan is `docs/ai-workflow/RETENTION_ENGINE_ERROR_PATHS_2_PLAN.md` (revision 3, approved by gate policy).
A `fix:` patch, Workflow 2.29.4, two checkpoints.

## Goal

No path of the retention engine ends in a traceback, or names a directory the walk did not fail on, where the contract is a
named refusal: an item folder that cannot be opened (D-Walk), the lock-time recheck of `remove` (D-Lock), the same-name
collision of the report (D-Collision), an `OSError` no site maps (D-Stray) and the report's best-effort `close`.

## Progress

- CP1 (the walks, the lock recheck, the collision, the backstop, tests and pages): complete. `workflow_retention.py` gains
  `_guard_walk` (three sites), the `folder_changed` refusals of step 1, the `pending` entries with `silent`/`ambiguous`
  flags, the `_stray_io` decorator on `archive_item`, `remove_item` and `prune_archives`, and the report's guarded `close`.
  The new class `RetentionErrorPathsTwo` (17 tests) fails on the unedited script and passes on the change; the one amended
  tuple of `test_t4` is the "link opens, zz fails" layout. `docs/RETENTION.md` and `docs/exit-codes.md` say it.
- CP2 (Release 2.29.4): complete. `manifest.json` 2.29.4 (five records, posture, `conformance.suites`: the obligations suite is 308), `WORKFLOW_RELEASE` 2.29.4 with its two pinned assertions and the protocol document's edits (protocol stays 1.5), the 2.29.4 row of `docs/release-history.md`, the stamps of `docs/release-history.md`, `docs/RETENTION.md` and `docs/exit-codes.md`, and a 2.29.4 class in `tools/release/release_test.py` (the 2.29.3 and 2.25.6 classes give up the pins that moved).

## Next action

The item is at the functional-review gate (`AWAITING_FUNCTIONAL_REVIEW`). The manual functional tests are the flows of the checklist below. Findings go to the feedback directory the gate step reports; `/apply-functional-review` routes them. Once testing is clean, `/accept-milestone` is the only acceptance command.

## Functional review checklist

Work item `retention-engine-error-paths-2` (`fix:`, Workflow 2.29.4, implementation revision 4, base `522e518`). The retention engine's error paths now end in a named refusal, never a traceback. Plan section 6 (`docs/ai-workflow/RETENTION_ENGINE_ERROR_PATHS_2_PLAN.md`) is the authoritative flow table; this section is the run order and the sandbox split. The commit that pins this checklist is reported with the gate status, not repeated here.

### Setup

- **Writable locations:** `$TMPDIR` and a scratch `HOME` only. Nothing inside the product clone is written. Run Python with `-I`; the suites with `-B`.
- **Non-root:** flow 2 and the `chmod 000` step of flow 3 need a non-root user. Under root, `chmod 000` does not deny reads, so those steps are **NOT RUN**, not PASS.
- **`base/` and `cand/`:** `base/` = `git archive 522e518 payload/scripts`; `cand/` = `git archive <evidence-commit> payload/scripts`. The payload is byte-identical from the reviewed head `b1968fa` to the evidence commit.
- **Scratch repository:** `git init` with origin `https://github.com/acme/widgets.git` (the URL only; nothing is fetched). Eight finished items plus one open (five archivable). `.ai-review/m-1` holds `a.txt`, `b.txt`, `sub/c.txt` and a symlink `ln -> a.txt`. Hash the repository, the folders and the store before and after each flow.
- **Fake `gh`:** `$HOME/wf-fakebin/gh`, mode 0755, text as in plan section 6, first on `PATH`. Every flow that reads forge facts (`report`, `archive`, `remove`, `prune`) depends on it; the sandbox's refusing `gh` must not shadow it.
- **Harnesses:** `inject.py` and `golden.py` are not committed. Write them from plan section 6, keep them outside the scratch repository, and run them as `python3 -I`.
- **Engine:** `python3 -I <base-or-cand>/scripts/workflow_retention.py <command> ... --repo-root <scratch> --archive-root <scratch-store>`. It uses the system `zstd`. Always pass `--archive-root`; never use the default store.

### Flows 1 to 9 (sandbox, offline)

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | No injection: `python3 -I golden.py base/ cand/` | Every output, exit code, tree and store hash identical, byte for byte |
| 2 | Non-root: `chmod 000 .ai-review/m-1`; `report` and `report --json` with base and cand; restore the mode | base: `PermissionError` traceback, exit 1. cand: exit 0, a line `m-1: at least 0 B in 0 files (partly unreadable); ...`, the warning `incomplete`, `read_errors` names `.ai-review/m-1`; nothing written |
| 3 | Same mode: `archive m-1`, `archive m-1 --apply`, `remove m-1`, `remove m-1 --apply` (after an archive made before the chmod) | base: traceback, exit 1. cand: exit 2 `unreadable`, `.ai-review/m-1 cannot be read (...)`, a `next step:`; repository, folder and store identical; after the mode is restored the run succeeds |
| 4 | `inject.py fwalk _scan EACCES 0` with `archive m-1 --apply`; `fwalk _pack EACCES 0` and `fwalk _pack ENOENT 0` with the same; `fwalk _scan EACCES 1` (the re-check) | base: traceback (and `pack_failed` for the pack). cand: exit 2 `unreadable` (`folder_changed` for `ENOENT`); no `.partial`, no archive, no index line, no directory this run created |
| 5 | After an archive: `fwalk _hash_folder EACCES 0` with `remove m-1 --apply` (after the rename); `fwalk _scan EACCES 0` with `remove m-1` | base: traceback, the folder left in `.removing/m-1` (apply). cand: exit 2 `unreadable`, the folder back in `.ai-review/m-1`, no `.removing`, store identical; the dry run writes nothing |
| 6 | After an archive: `fwalk _remove_tree EACCES 0` with `remove m-1 --apply`; then without the injector | base: traceback. cand: exit 2 `remove_failed`, "stopped after deleting 0 entries, each proven archived; the rest is in", the permissions hint, the folder whole in `.removing/m-1`; the next run finishes the removal |
| 7 | After an archive: `flock swap`, `flock appear`, `flock vanish` (with a parked leftover for the last) with `remove m-1 --apply` | base: `place_failed`. cand: exit 2 `folder_changed` with the three messages, next step `nothing was moved or deleted; run it again`; nothing moved or deleted; a later run succeeds |
| 8 | Layout `.ai-review/m-1/a/zz` a link to a directory, `.ai-review/m-1/zz` a directory; `report --json` with (a) `open zz link 2`, (b) `open zz link 2` and `open zz dir 1`, (c) `open zz dir 1` alone | (a) base: `read_errors` names `.ai-review/m-1/zz`, a directory that opens. cand: `.ai-review/m-1` only. (b) cand: `.ai-review/m-1`, never `zz`. (c) base names `.ai-review/m-1/zz`; cand names `.ai-review/m-1` (the one amended layout, D-Collision) |
| 9 | `fstat _same_device EIO 0` and `close _judge_removal_archive EIO 0` with `remove m-1 --apply`; `fstat _hash_folder EIO 1` after the rename, once with an extra file added to the folder after the archive; `fstat _walk_folder EIO 0` with `archive m-1`; `close build_report EIO 0` with `report` and with `prune m-1` | base: traceback, exit 1. cand: exit 2 `unreadable` with the errno and the command's next step, except `report` and `prune` with the `close` error, which run as without it. After the rename the folder is whole in `.removing/m-1` and a run finishes the removal. The extra-file run says the folder may be in `.removing/m-1`, unverified, never that the archive holds every entry; the next run refuses `archive_mismatch` and deletes nothing. `archive` leaves no partial |

### Flows 10 and 11 (full environment; not runnable in the sandbox as written)

- **Flow 10.** Runnable offline: the nine conformance suites from a `stage-conformance` fixture written under `$TMPDIR`; `tools/docs` tests and `check_docs.py`; `check-manager-block --manager-releases tools/release/manager-releases.json`. Run them from a scratch clone, with `PYTHONDONTWRITEBYTECODE=1`, so no bytecode is written into the product clone. Expect all to pass, none skipped. **Not runnable here:** `workflow-manager verify .` needs a release cache (`--release-cache`); without one it exits 1 by design.
- **Flow 11.** `tools/release` tests need Python 3.12 with `zlib_ng` 2.2.5 installed from hashes (network). The sandbox has no such interpreter, so this flow is **NOT RUN** unless a prebuilt venv is provided. `git diff 522e518 --stat -- payload docs` is runnable: it should list `workflow_retention.py` and its test, `workflow_protocol.py` and its test, and `ORCHESTRATION_PROTOCOL.md`, with no new code in `--help`.

### Known limits and out of scope

- The same-name layout (D-Collision) is the one amended behaviour: layout (c) of flow 8 now names `.ai-review/m-1`. Intended.
- The engine never touches a real forge, the network, a real `gh`, `claude`, `codex` or `ssh`.
- The protocol stays at 1.5; `workflow_protocol.py` changes by two lines only.
- Flow 2 and the `chmod` steps are invalid under root (see Setup).

### Where findings go, and what comes next

- Findings go to `<feedback_dir>/FUNCTIONAL_REVIEW.md`. The resolved directory is printed by `ensure_feedback_dir` in the gate step, not written here.
- Once testing is clean, `/accept-milestone` is the only acceptance command. Both checkpoints (CP1, CP2) are `COMPLETE`, so it is available.
- Findings are routed by `/apply-functional-review`: a same-scope fix takes its bounded branch; new or wider scope takes its broad branch (a `retention-engine-error-paths-2-remediation-<n>` child).
