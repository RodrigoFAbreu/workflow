# Active Milestone

## Milestone

**In progress.** W29: `retention-removal` (`process`, governing version `2.2`), branch `milestone/retention-removal`,
roadmap row 27d (RodrigoFAbreu/workflow#116 item 7, and the obligations EPR-001 and EPR-010). Plan:
`docs/ai-workflow/RETENTION_REMOVAL_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.22.0 (released
after the merge of the pull request), a `feat:` minor that adds the removal, `scripts/workflow_retention.py remove <id>`:
a dry run by default, and with `--apply` it takes a finished, archived item's untracked review folder out of the
repository with one atomic rename into `<archive-root>/<repo>/.removing/<id>`, verifies the archive against the moved
folder by contents (the listing and the SHA-256 of every file), and deletes it entry by entry, or renames it back and
refuses naming the difference. An interrupted run leaves one recognisable leftover, which the report lists and the next
run completes or renames back. The user-only command (27e) and the prune (27f) are not part of this item. The previous
milestone, W28 `retention-archive`, is accepted (Workflow 2.21.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The removal, its tests and the documents | **complete** (verified in a scratch clone, see below) |
| CP2 | Release 2.22.0 | **complete** (verified in a scratch clone, see below) |

## Verified state

- CP1: `payload/scripts/workflow_retention.py` (`_select_finished` extracted from `archive_item`, `remove_item`,
  `_archive_table`, `_hash_folder`, `_differences`, `_remove_tree`, the rename back, the `remove` subcommand, and the
  report's `removing` key and text line), the `RetentionRemove` tests in
  `workflow_state_completion_obligations_test.py` (240 -> 255), `docs/RETENTION.md` (the section "The remove command",
  the `removing` key, the archive table's new `unreadable` cause and the re-read references to rows 27c to 27f) and
  `docs/exit-codes.md`. `git diff 0c06330 --stat -- payload` lists the script and its test file only. Each mutation m1
  to m20 fails at least one named case in a scratch copy, and the control passes (the results are in the
  implementation bundle's `TEST_RESULTS.md`).
- Verified in a disposable clone (D-Staging): the nine suites from the staged fixture, `tools/docs` (34),
  `check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng), and the new and the whole obligations tests under
  the orphan wrapper.

- CP2: `manifest.json` 2.22.0 (counts 81, 6, 55 unchanged; the five changed records carry their `retention-removal
  (workflow-2.22.0)` sentence, every digest and size recomputed, `conformance.suites` measured by `release.py
  manager-block --write`: obligations 240 -> 255, the others unchanged), `WORKFLOW_RELEASE` and its two pinned
  assertions, `ORCHESTRATION_PROTOCOL.md` (protocol stays 1.5), the 2.22.0 row of `docs/release-history.md` with the
  downgrade note, the "Last checked with" lines of the three pages, and `RetentionRemovalReleaseTest` in
  `tools/release/release_test.py` (the 2.21.0 class keeps what stays true of it).
- Verified in a scratch clone committed with the CP2 content: stock `stage-conformance --commit HEAD` and the nine
  suites, `release.py build` (zlib-ng, 88 files), `check-manager-block`, `tools/docs` (34) and `check_docs.py`, and
  `tools/release` (285, zlib-ng interpreter).

## Next action

Manual functional review (`AWAITING_FUNCTIONAL_REVIEW`). Test the checklist below against the evidence commit that
`/prepare-functional-review` reports. Findings go to `.ai-review/retention-removal/feedback/FUNCTIONAL_REVIEW.md`, and
`/apply-functional-review` routes each one. When testing is clean, `/accept-milestone`.

## Functional review checklist

Scope: `retention-removal` (Workflow 2.22.0). It tests the release source, `payload/scripts/workflow_retention.py`. The
installed `scripts/workflow_retention.py` is the 2.21.0 copy and has no `remove` subcommand; the installation changes
only through `workflow-manager update` after the release.

**Setup**

- Needs `python3`, `git` and `zstd`. For the flows marked *forge*, an authenticated `gh` as well (each finished-item
  check makes a fresh query).
- Run every command as `python3 -I payload/scripts/workflow_retention.py <command> ...` and always pass
  `--repo-root <clone>`. The default is the `payload/` folder, which gives `state_missing`.
- Use a scratch `--archive-root` on the same file system as the clone (the default is
  `~/.local/share/workflow-archive`). A different file system is refused with `cross_device`.
- Run every flow that uses `--apply`, and the leftover and symlink flows, in a scratch clone (`git clone <origin>
  <scratch>`, then copy the item's `.ai-review/<id>/` into it), never in this working tree. The untracked review folders
  here are the only copies: no archive exists yet.

**Test data**

- Pick an item the report lists under "Finished", not under "Kept as recent" (`report --repo-root <clone>`). At the
  time of writing `interleaving-pins` (42 files, no archive) qualifies. The list changes after each archive.
- Archive it first in the scratch clone: `archive <id> --apply --repo-root <clone> --archive-root <scratch>`. Removal
  needs that archive.
- Symlink flow only: before archiving, add to the folder a symlink to a file outside the clone (for example
  `/tmp/outside.txt`, with known content).

**Flows** (*offline* flows need no network and no forge, so the sandboxed functional tester can run them; *forge*
flows need a real `gh`)

| # | Kind | Flow | Command | Expected |
| --- | --- | --- | --- | --- |
| O1 | offline | Invalid id is refused | `remove runtime --repo-root <clone>` | exit 2; `error: invalid_id:` on stderr; nothing on stdout |
| O2 | offline | An open item is refused without a forge query | `remove retention-removal --repo-root <clone>`, in a clone whose `origin` is a github.com URL | exit 2; `not_finished:open_phase` |
| O3 | offline | A non-GitHub origin is refused | the same command in a clone whose `origin` is a local path | exit 2; `repository_unknown` |
| O4 | offline | `--apply` on a refused item writes nothing | O2 with `--apply --archive-root <empty scratch dir>` | exit 2 as O2; the archive root is still empty |
| F1 | forge | Dry run of a finished, archived item | `remove <id> --repo-root <clone> --archive-root <scratch>` | exit 0; `contents match the archive`; `dry run: nothing was written; pass --apply to remove`; folder still in place; no `.removing/`; archive unchanged |
| F2 | forge | JSON dry run | F1 with `--json` | one object on stdout, keys sorted, ending in a newline; `mode` `dry-run`, `result.removed` false, `review_folder.state` `in_place`, `verify.matches` true |
| F3 | forge | Apply removes the folder | F1 with `--apply` | exit 0; `removed N file(s), ...; the archive holds them`; `.ai-review/<id>` gone; `.removing/` present and empty; `zstd -dc <archive> \| tar -t` still lists the folder |
| F4 | forge | A second apply finds nothing to remove | F3 again | exit 2; `review_folder_absent`; nothing changes |
| F5 | forge | A changed file stops the removal, and nothing is deleted | archive, then append one byte to a file in the folder; F1, then F1 with `--apply` | both exit 2 with `archive_mismatch` naming the file; the folder is back at `.ai-review/<id>` with the byte; `.removing/<id>` gone |
| F6 | forge | A symlink is removed as a link | symlink test data; F1 with `--apply` | exit 0; the link is gone; the file it pointed to is unchanged |
| F7 | forge | A leftover is completed | after an archive, in the scratch clone: `mv .ai-review/<id> <archive-root>/<repo>/.removing/<id>`; `report` lists it under "removing"; then F1 (dry run shows `Review folder (leftover)`), then F1 with `--apply` | exit 0; `.removing/<id>` gone; the archive still lists the folder |
| F8 | forge | A leftover that differs is renamed back | as F7, but append one byte to a file in the leftover before `--apply` | exit 2 `archive_mismatch`; the folder is back at `.ai-review/<id>` with the byte; `.removing/<id>` gone |
| F9 | forge | One of the three most recent items is kept | `remove <id>` for an item under "Kept as recent" | exit 2 `kept_recent`; nothing written |
| F10 | forge | A different file system is refused (optional, needs a second file system) | `remove <id> --archive-root <dir on another file system>` | exit 2 `cross_device`; the folder is in place; no `.removing/` created |

**Known limitations and out of scope**

- The user-only command (27e) and the prune (27f) are not part of this item.
- The threat is accidental loss, not an adversary. A process that held a file of the folder open before the rename could
  still write to it; the post-rename comparison catches that. A write between one entry's check and its `unlink` is not
  excluded (`docs/RETENTION.md`, "What it does not claim").
- A crash (kill, power loss) between the steps is covered by the unit suite's mutation tests, not by manual testing.
  F7 and F8 reproduce a stopped run's leftover by hand.
- Until the release is installed, the installation keeps the 2.21.0 script, which cannot see or resume a leftover.
- In the sandboxed functional tester only O1 to O4 can run. A `.ai-review` that is a link there refuses the rename
  (`environment`), which is not a product defect.
