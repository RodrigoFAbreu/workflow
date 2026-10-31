# Active Milestone

## Milestone

**Awaiting functional review** (`AWAITING_FUNCTIONAL_REVIEW`, implementation revision 1). W37: `retention-error-paths` (`process`, governing version `2.2`), branch
`milestone/retention-error-paths`, roadmap row 32 (RodrigoFAbreu/workflow#119 item 1 and #113 item 2). Plan:
`docs/ai-workflow/RETENTION_ERROR_PATHS_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.5 (a
`fix:` patch, released after the merge of the pull request): an unreadable symlink in a review folder, and a state
file or tracked path that is not valid UTF-8, are coded refusals (exit 2, a `next step:`) instead of a traceback.
Base commit `69ebb46`; the previous milestone, W36 `check-time-by-value`, is accepted (Workflow 2.25.4).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The helpers, their call sites, tests and documents | **complete** |
| CP2 | Release 2.25.5 | **complete** (see the commit of this checkpoint) |

## Verified state

- CP1: the readlink helper and its four call sites, the two decoding catches, tests T1 to T8, `docs/RETENTION.md` and
  `docs/exit-codes.md`.
- CP2: `manifest.json` 2.25.5 (five changed records, the posture, `conformance.suites` measured: the completion
  obligations suite 274 to 284, after the self-review test), `WORKFLOW_RELEASE` 2.25.5 and its pinned assertions, the protocol document's example
  and `1.5` lists, the 2.25.5 history row, the pages' "Last checked with" lines, and a 2.25.5 class in
  `tools/release/release_test.py` (the 2.25.1 and 2.25.4 classes give up the current-release pins).
- Automated verification is current: `.ai-review/retention-error-paths/current/TEST_RESULTS.md` records every suite green at
  `c7f863f` (the nine suites at `77ca825`). Since `77ca825` the only product-tree change is one line of
  `tools/release/release_test.py` (the pin, run at `c7f863f`); later commits change the state file only.

## Functional review checklist

**Scope.** The unreadable symlink and the undecodable input are coded refusals (exit 2, a `next step:`) where they used to
be a traceback: `archive`, `remove`, `prune` and `report`. No new refusal code. One intended change to an existing
refusal: a `readlink` failure while `archive --apply` packs now gives `unreadable` or `folder_changed`, not `pack_failed`.

**Setup.**

- `python3` (standard library only), `git` and `zstd` on `PATH`; `zstd` is needed by the archive and remove flows. No
  network, no real GitHub, no real `claude`, `codex` or `ssh`.
- Work in scratch directories under `$TMPDIR` only. Do not write inside this clone (use `git archive` and copies), and
  never run against the real `.ai-review/`, the real archive store or the real forge.
- The scripts are in `docs/ai-workflow/RETENTION_ERROR_PATHS_PLAN.md`, section 6: `base/` and `cand/`, the scratch
  repository, the fake `gh` and `inject.py`. Use them as written. Each flow starts from a fresh copy of the repository and
  the store; hash both, and the folders, before and after.

**Test data.** The scratch repository of plan section 6: `origin` `https://github.com/acme/widgets.git`; a state of eight
finished items and one open (five archivable); `.ai-review/m-1` holding `a.txt`, `b.txt` and the symlink `ln` to `a.txt`;
a scratch `HOME`.

**Flows.** "Needs fake gh" flows select the item by its pull-request record, so they run only with the fake `gh` of plan
section 6 on `PATH`; a `gh` that refuses cannot run them. "None" flows make no forge call. `base` is the 2.25.4 engine, `cand`
is this change.

| # | Needs | Do | Expect |
| --- | --- | --- | --- |
| 1 | fake gh | No injection, with `base` and `cand`: `archive m-1`, `archive m-1 --apply`, `remove m-1`, `remove m-1 --apply`, `prune m-1` | outputs and exit codes identical, byte for byte |
| 2 | fake gh | `inject.py`, `_scan`, `ln`, `EACCES`, skip 0: `archive m-1`, then `archive m-1 --apply`; then skip 1 with `--apply` | `base`: traceback, exit 1. `cand`: exit 2, `error: unreadable: ln cannot be read (Permission denied)`, a `next step:`; store and folder hash-identical, no `.partial`, no directory this run created |
| 3 | fake gh | `_pack`, `ln`, `EIO`, skip 0, with `archive m-1 --apply`; then the same without the injector | `base`: exit 2 `pack_failed`. `cand`: exit 2 `unreadable`; no archive, no temporary, no index line; the later run succeeds |
| 4 | fake gh | Archive `m-1`. `_hash_folder`, `ln`, `EACCES` with `remove m-1` (dry run). `_scan`, `ln`, `EACCES` with `remove m-1 --apply`, skip 0, then skip 1 | `base`: traceback. `cand`: exit 2 `unreadable`; the folder still in `.ai-review/m-1`, nothing moved; the later run succeeds |
| 5 | fake gh | Archive `m-1`. `_hash_folder`, `ln`, `EIO` with `remove m-1 --apply` (after the rename); then `ENOENT` | `cand`: exit 2 `unreadable` (`folder_changed` for `ENOENT`); the message says the folder is back in `.ai-review/m-1`; no `.removing`; store identical. `base`: traceback, folder left in `.removing/m-1`; a run without the injector removes it |
| 6 | fake gh | Archive `m-1`. `_remove_tree`, `ln`, `EACCES` with `remove m-1 --apply` | `cand`: exit 2 `unreadable`, "stopped after deleting N entries, each proven archived; the rest is in `.removing/m-1`", next step ``run `remove m-1 --apply` again``; a run without the injector finishes. `base`: traceback |
| 7 | none | Write the byte `\xff` into the scratch `docs/ai-workflow/WORKFLOW_STATE.json`; run `report`, `archive m-1`, `remove m-1`, `prune m-1` | `base`: traceback `UnicodeDecodeError`, exit 1. `cand`: exit 2, `error: state_invalid: ... is not valid UTF-8 (byte ...)`, a `next step:`; nothing written |
| 8 | none | Create a file whose name holds the byte `\xff` under `.ai-review/m-1` (a bytes path, `python3 -I`), `git add -f` it; run `report` | `base`: traceback `UnicodeDecodeError`, exit 1. `cand`: exit 2, `error: repository_unknown: git ls-files printed a path under .ai-review that is not valid UTF-8`, a `next step:`; nothing written |
| 9 | none | `git diff 69ebb46 --stat -- payload docs`; `python3 -I workflow_retention.py --help` in a copy of `cand` | six `payload` files change: `workflow_retention.py` and its test, `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`, plus the documents; no new code in the help or in the documents' code lists |

Flows 7 to 9 were run once in a scratch copy (`cand`, no `gh` on `PATH`): 7 and 8 gave the `cand` results above, and the
help ran.

**Known limitations.**

- The `readlink` failures are injected. A real `chmod` cannot make `readlink` fail, because a symlink in a searchable
  directory always reads, so `inject.py` stands in for the real error (plan section 6).
- Not in this milestone: the report's text for an unreadable symlink and its `read_errors` path (#113 item 1, #116 item
  1; row 33, planned next); the other bare descriptor calls (`os.read` in the pack, `os.fstat`; plan section 0); #119
  items 2 to 8.
- A tracked non-UTF-8 path under a single-byte (Latin-1) locale now refuses `repository_unknown` where it used to be
  counted. This is the intended direction (plan section 4).
- This repository's own installation stays at 2.25.4 until 2.25.5 is published; `workflow-manager verify .` is clean at
  2.25.4.

## Next action

Run the flows above against the checklist commit. Findings go to `.ai-review/retention-error-paths/feedback/FUNCTIONAL_REVIEW.md`;
`/apply-functional-review` routes each one. When testing is clean, `/accept-milestone` is the only acceptance command. CP1
and CP2 are both `COMPLETE`, so no checkpoint is outstanding.
