# Active Milestone

## Milestone

**In progress.** W32: `retention-prune-command` (`process`, governing version `2.2`), branch
`milestone/retention-prune-command`, roadmap row 27g (RodrigoFAbreu/workflow#123 item 1, #126 items 2 and 3). Plan:
`docs/ai-workflow/RETENTION_PRUNE_COMMAND_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.0 (a
`feat:` minor, released after the merge of the pull request): the user-only command `/prune-archives
<work-item-id>...`, which previews the dry run of `workflow_retention.py prune` and runs `--apply` only after the
literal sentence `Prune the archives <n1>, <n2>.` naming exactly the named archives. Base commit `8537d23`; the previous
milestone, W31 `retention-prune`, is accepted (Workflow 2.24.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The command, its tests and the documents | **complete** (`8fd9885`) |
| CP2 | Release 2.25.0 | **complete** (see the commit carrying `Workflow-Checkpoint: CP2`) |

## Verified state

- Gates: plan approval `CURRENT`, basis `POLICY_SATISFIED`; implementation review APPROVE at implementation revision 3
  (`LOCAL_MODEL_IMPLEMENTATION_REVIEW` and `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`); technical approval `CURRENT`,
  basis `POLICY_SATISFIED`, for the reviewed content `026261f`.
- Automated verification: the last code change is `026261f`; `7724bd6` and `2685097` change only
  `docs/ai-workflow/WORKFLOW_STATE.json`. The nine suites, `tools/release` (zlib-ng interpreter), `tools/docs`,
  `check_docs.py`, `check-manager-block`, `release.py build` and `workflow-manager verify .` were run at `026261f`; the
  results are in `.ai-review/retention-prune-command/current/TEST_RESULTS.md`, "Round 2 fixes".
- CP1: the command file, `TestPruneArchivesCommand` and the moved tripwires, the three payload documents,
  `docs/RETENTION.md` and the four release classes' counts (83/57), committed as `8fd9885`.
- CP2: `WORKFLOW_RELEASE` 2.25.0 with its two assertions and the protocol document, `manifest.json` 2.25.0 (the
  command record, counts 83/57, the changed records, the posture, `conformance.suites` measured), the 2.25.0 row of
  `docs/release-history.md`, the "Last checked with" line of `docs/RETENTION.md`, and a 2.25.0 class in
  `tools/release/release_test.py` (the 2.24.0 class gives up the current-release pins). Verified in a disposable clone
  committed from this tree: `tools/release` (293 tests, zlib-ng interpreter), `tools/docs`, `check_docs.py` and
  `check-manager-block` pass; the stock `stage-conformance` fixture, the nine suites and `build` are reported in the
  implementation bundle's `TEST_RESULTS.md`.

## Functional review checklist

This checklist is the manual functional review of the candidate: `/prune-archives` (Workflow 2.25.0). Test the commit
that carries this section (its `Workflow-Functional-Checklist` trailer names it). Record findings in
`.ai-review/retention-prune-command/feedback/FUNCTIONAL_REVIEW.md`.

Every flow runs offline, in a sandbox: no network, no real GitHub, no real `claude`, `codex` or `ssh`. A flow that needs a
pull request or any forge call cannot run here, and none of the flows below needs one.

### Setup

Nothing here touches the real repository, its `.ai-review/`, the real archive store, the real forge or the network.

1. A scratch repository under `$TMPDIR` with a `github.com` origin (a scratch bare repository is enough), a state of
   eight finished work items and one open one (so with `KEEP_RECENT = 3`, five are archivable). Copy the candidate's
   `payload/.claude/commands/prune-archives.md` into its `.claude/commands/`, and `payload/scripts/workflow_retention.py`
   into its `scripts/`.
2. A scratch `HOME`, with the `XDG_*` directories and `TMPDIR` also scratch (the default archive root is under `HOME`).
3. A fake `gh` (the script of plan section 7 of `docs/ai-workflow/RETENTION_PRUNE_COMMAND_PLAN.md`: it prints the
   merged-pull-request facts the retention tests' fake forge returns), in a `fakebin` directory that is not under `/tmp`,
   `/var/tmp`, `/dev/shm` or `$TMPDIR`, not world-writable, first on `PATH`. The engine refuses a `gh` in those places.
4. Five archives made by the engine's own `archive --apply` for `m-1`, `m-10`, `m-2`, `m-3` and `m-4`. Then, in the
   scratch store only, `os.utime` ages `m-1`, `m-10` and `m-2` to 45 days; `m-3` and `m-4` stay fresh.
5. Each flow starts from a fresh copy of steps 1 to 4. Before and after it, hash the scratch repository, its folders and
   the store, and compare.
6. F2 needs the zlib-ng 1.0.0 interpreter of `tools/release/deflate-requirements.txt`, from a venv outside the checkout.

### Flows

Each message is what you send to the agent as the user. Expected results follow each flow.

- **F1 - the suites.** `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then
  each suite listed in `manifest.json` under `manager.conformance.suites`, run from the fixture's `scripts` directory.
  Expected: every suite exits 0. Last recorded counts at `026261f`: acceptance matrix 453 (skipped 20), protocol 344
  (skipped 19), state 1244 (skipped 1), gate policy 316, fingerprint generalization 142, completion obligations 265,
  integration 376 (including `TestPruneArchivesCommand`), fingerprint 283, test harness 27. All OK.
- **F2 - the tools and the docs.** `python -m unittest discover -s tools/release -p '*_test.py'` (zlib-ng interpreter),
  `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, and
  `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`.
  Expected: 293 tests OK, 34 tests OK, exit 0, and `ok: 2.25.0 carries a valid manager block that matches the measurement`.
- **F3 - no sentence, nothing applied.** In the scratch repository send `/prune-archives m-1 m-2`. Expected: the dry run
  is printed in full; the sentence `Prune the archives m-1, m-2.` is printed with the note that the listed archives are
  deleted for good and their index lines stay; the run stops. Then send `yes, go ahead`. Expected: nothing is applied and
  the sentence is printed again. Hashes are identical.
- **F4 - sentences that do not match.** After the preview of `m-1 m-2`, each of these is refused, the sentence is
  printed again, and nothing is removed: `Prune the archives m-1.` (a subset); `Prune the archives m-2, m-1, m-3.` (a
  superset); `Prune the archives m-1, m-3.` (another name); `Prune the archives m-1 and m-2.` (an "and" list);
  `Prune the archives m-1, m-2` (no full stop). Then, in two separate runs: named `m-10`, reply `Prune the archives m-1.`
  (refused); named `m-1`, reply `Prune the archives m-10.` (refused). Then, in one message each: `Prune the archives
  m-1, m-2. Prune the archives m-1.` and `Prune the archives m-1. Prune the archives m-1, m-2.`. Both are refused, because
  every match must name exactly the named archives.
- **F5 - the full run removes exactly the named archives.** Send `/prune-archives m-1 m-2`, then reply
  `Yes, please. Prune the archives m-2, m-1.` Expected: the apply runs once. `m-1.tar.zst` and `m-2.tar.zst` are removed;
  `m-10`, `m-3` and `m-4` are byte-identical; the index lines, the folders and the tracked files are unchanged. The
  report gives the removed archives and the bytes, says the index keeps its lines, and nothing else is run.
- **F6 - a preview refusal stops the run.** Send `/prune-archives m-1 m-3` (`m-3` is fresh). Expected: the preview exits
  non-zero with `error: not_prunable` and its `next step:` line verbatim. No sentence is asked for, nothing is applied,
  and the store is identical.
- **F6b - an apply refusal is reported, not retried.** Send `/prune-archives m-1 m-2`, let the preview pass, then, before
  you send the sentence, change the store in one of these ways. Each run stops at the apply, with nothing removed:
  (a) create `.removing/m-1/` in the scratch store. Expected: `error: removal_interrupted`, its `next step:` verbatim, and
  no `removed:` or `not removed:` lists, because that message carries none. (b) remove write permission from the scratch
  per-repository archive directory (not as root). Expected: `error: prune_failed` with `removed: none; not removed: m-1,
  m-2`, reported verbatim. Restore the permission afterwards. (c) optional: `touch m-1`. Expected: `error:
  not_prunable` (age 0). In every case the command reports the code and the next step, then stops. It does not retry
  the apply; a new run starts with a new message from you.
- **F7 - malformed arguments.** Send each of these as the command's arguments: none; `m-1 m-1` (a repeat); `M-1`;
  `m-1.tar.zst` (a file name); `Prune the archives m-1.` (a sentence). Expected: each is refused before anything runs,
  nothing is written, and no sentence is asked for.
- **F8 - the diff and the documents, on the checkout (read-only).** `git diff 8537d23 --stat -- payload` lists the
  command file, the integration suite, `COMMAND_FILES.md`, the operator reference, `ORCHESTRATION_PROTOCOL.md`,
  `workflow_protocol.py` and its test, and nothing else. `git diff 8537d23 -- tools/release/release_test.py` changes the
  four release classes' counts to 83 and 57 and adds the 2.25.0 class; the 2.24.0 class gives up the current-release
  pins. `manifest.json`, the 2.25.0 row of `docs/release-history.md` and the "Last checked with" line of
  `docs/RETENTION.md` all name 2.25.0. `workflow-manager verify .` reports the installation as 2.24.0, unchanged by design.

### Known limitations (not defects of this milestone)

- The sentence check is done by the agent, following the pattern in the command body, not by code. The pattern has no
  left-hand context, so `do not prune the archives m-1.` matches. This is the accepted limit of `/archive-finished-item`;
  the preview and the engine's own checks stand behind it.
- The command lists no archives. To see names, use the engine's `report`, a separate act.
- The engine prints `removed:` and `not removed:` only with `prune_failed`. The command body asks for those lists after
  every non-zero apply, so a message without them is the engine's output, not a failure of the command.
- The engine (`scripts/workflow_retention.py`) is unchanged; so are the state file, the phases and the protocol.
- The apply does not bind to the preview: the engine judges again at `--apply`. `archive_changed` at apply is reachable
  only inside the apply run itself, so no flow here reaches it.
- This repository's own installation stays at 2.24.0. `/prune-archives` reaches `.claude/` only after a release is
  installed with `workflow-manager update`; the flows use the payload copy.
- No flow uses a real forge, the network or a real `claude`, `codex` or `ssh`.

## Next action

Functional review, a manual hard gate: run the checklist above against the evidence commit that carries it, and place
findings in `.ai-review/retention-prune-command/feedback/FUNCTIONAL_REVIEW.md`. If findings come, `/apply-functional-review`
routes them. Once testing is clean, `/accept-milestone` is the acceptance command; CP1 and CP2 are both `COMPLETE`.
