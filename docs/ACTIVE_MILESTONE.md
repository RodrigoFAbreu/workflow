# Active Milestone

## Milestone

**Awaiting functional review.** W30: `retention-command` (`process`, governing version `2.2`), branch
`milestone/retention-command`, roadmap row 27e (RodrigoFAbreu/workflow#84, the user-gated step of the retention tool).
Plan: `docs/ai-workflow/RETENTION_COMMAND_PLAN.md` (revision 3, approved by gate policy). The goal, Workflow 2.23.0 (a
`feat:` minor, released after the merge of the pull request): one user-only command file,
`/archive-finished-item <work-item-id>`. It previews the dry runs of `scripts/workflow_retention.py archive` and
`remove` for ONE finished item, and runs `archive --apply` and then `remove --apply` only after the user's own
current-turn message carries the sentence `Archive and remove the review folder of <id>.`. The engines are unchanged;
the command packs, verifies, renames and deletes nothing itself. Base commit `e6c12be`; the previous milestone,
W29 `retention-removal`, is accepted (Workflow 2.22.0). The prune (roadmap row 27f) is not part of this item.

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The command, its tests and the documents | **complete** |
| CP2 | Release 2.23.0 | **complete** |

## Verified state

- Gates: plan approval `CURRENT`, basis `POLICY_SATISFIED` (local `LOCAL_MODEL_PLAN_REVIEW` and the external review both
  APPROVE, round 3 of the local stage). Implementation: `LOCAL_MODEL_IMPLEMENTATION_REVIEW` APPROVE (round 2) and the
  manual external `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` APPROVE of revision 2. Technical approval `CURRENT`, basis
  `POLICY_SATISFIED`, at the review content `6379ce13`.
- Implementation revision 2 is the post-review-fix tree: round 1's findings (the operator reference's confirmation count
  "six" to "seven", the test pin, the stale docstring, the step-3 wording, the "never the active item" wording) were
  fixed in `858f3f3`.
- Automated verification, run at `858f3f3` after the fix (the full record is the implementation bundle's
  `TEST_RESULTS.md`, "Review round 1 (post-fix)"): the nine suites from a stock
  `release.py stage-conformance --commit HEAD` fixture (453 / 344 / 1244 / 316 / 142 / 255 / 370 / 283 / 27, all OK; the
  370 include `TestArchiveFinishedItemCommand`, T1 to T8); `tools/release` 288 OK (zlib-ng 2.2.5); `tools/docs` 34 OK;
  `check_docs.py` rc 0; `check-manager-block` ok; `release.py build` ok; `workflow-manager verify .` clean at 2.22.0.
  The mutation results of D-Tests (swapped `--apply` pair, the lookahead removed, `--json` added) each fail the
  command's tests, and the baseline passes.
- Since that run, only state-only commits (`WORKFLOW_STATE.json`) landed, so the automated state is current.
- The uncommitted `docs/ROADMAP.md` edit (row 27e to "Current", row 27f re-stated) is the plan's roadmap bookkeeping,
  unrelated to the checklist and excluded from the review content. It is left as it is.

## Functional review checklist

Scope: what the user confirms is the command's behaviour in scratch repositories. Nothing here runs against this
repository, its `.ai-review/` or the real archive store (`~/.local/share/workflow-archive`). The candidate is the 2.23.0
payload, not this repository's installation (this repository's `.claude/commands/` does not carry the command until the
release is installed by `workflow-manager update`).

### Setup

1. Stage the candidate: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`
   (flow F1). Use the fixture's `.claude/commands/archive-finished-item.md` and `scripts/workflow_retention.py`.
2. `tools/release` tests need a Python 3.12 venv outside the checkout with zlib-ng:
   `pip install --only-binary=:all: --require-hashes -r tools/release/deflate-requirements.txt`.
3. Scratch: `S=$(mktemp -d)`; set `TMPDIR="$S/tmp"` and a scratch `HOME="$S/home"`, with `XDG_DATA_HOME`,
   `XDG_CONFIG_HOME`, `XDG_CACHE_HOME` under `$S`, before running any engine call. The default archive root then lands in
   the scratch HOME.
4. Fake forge. The engine asks `gh` for the pull-request fact of the item's commit (`gh pr list --repo ... --json
   number,url,state,headRefOid,reviewDecision,reviews,statusCheckRollup`). A `gh` in `$TMPDIR`, `/tmp`, the repository or
   any world-writable directory is refused as `forge_undecidable` by `resolve_gh`. So put the fake in your own directory
   outside all of those, for example `~/.cache/retention-fake-gh/bin` (taken from the real HOME before you change it). It
   prints a JSON list with one record for `pr list` (`state` `MERGED`, `number`, `url`, `headRefOid`, empty `reviews`
   and `statusCheckRollup`), and logs its argv. Put that directory first on `PATH`.
5. Scratch repository: `git init`, `origin` = `https://github.com/example/retention-scratch.git` (the engine needs a
   `github.com` origin). Seed `docs/ai-workflow/WORKFLOW_STATE.json` with eight finished items (`MILESTONE_COMPLETE`):
   `m-1`, `m-2`, `m-3`, `m-4`, `m-5`, `m-6`, `m-7` and `m-10`, and one open item `m-8`, copying an entry of the
   candidate's state file. Give `m-5`, `m-6` and `m-7` the three latest merge dates: they are the `kept_recent` items
   (check the report). `m-1`, `m-2`, `m-3`, `m-4` and `m-10` are archivable. Create `.ai-review/<id>/` for each item with
   files, a nested directory and a symlink. Commit it. Flows F4 to F7c each start from a fresh copy of this scratch
   repository.
6. Before and after each flow, hash the scratch repository, the `.ai-review/` folders and the archive store
   (`find ... -exec sha256sum`), and compare.

### Flows

| Flow | Steps | Expected result |
| --- | --- | --- |
| F1 | Run the nine suites from the staged fixture (the suite list is `manifest.json`'s `manager.conformance.suites`), the integration suite included. | All nine pass. `TestArchiveFinishedItemCommand` (T1 to T8) passes. |
| F2 | In the checkout: `python -m unittest discover -s tools/release -p '*_test.py'`; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`. | 288 OK (zlib-ng); 34 OK; check_docs rc 0; the manager block ok. |
| F3 | Give the command `m-1`. Read the two previews. Reply with a message that does **not** carry the sentence. | Both dry runs print in full, the sentence is printed, nothing is applied. Hashes identical before and after, the reply included. |
| F4 | Give `m-1`, then reply with the sentence naming another finished item; then `m-10` with `m-1`'s sentence, and `m-1` with `m-10`'s. | Each reply is rejected, nothing is applied, hashes identical. |
| F5 | Give `m-1` (fresh copy), reply with the sentence for `m-1` exactly. | `archive --apply` then `remove --apply` run. The folder is gone; the archive and its index line exist; other folders, tracked files and state are identical; `python3 -I scripts/workflow_retention.py report` lists `m-1` as archived with no folder. |
| F6 | As F5 for `m-2`, with a stand-in `zstd` on the scratch `PATH` that exits non-zero. | The `archive` error code and `next step:` are reported; `remove` is not run; the folder and the archive store are identical to before. |
| F7 | As F5 for `m-3`, with the scratch HOME on a different file system from the scratch repository (check with `findmnt -T`). | `archive --apply` succeeds; `remove --apply` refuses `cross_device` with its next step; the folder is untouched; the archive is kept; no retry. |
| F7b | Make the archive by hand first (`archive m-4 --apply`), then edit a file of `.ai-review/m-4/` **after** the command's preview and **before** the reply. | `remove --apply` refuses `archive_mismatch` at apply time; the engine renames the folder aside, compares, refuses and renames it back. The folder is back byte for byte; the report says so; no retry. |
| F7c | As F7b (fresh copy, `m-10`), but edit the file **before** the command is run. | The `remove` preview refuses `archive_mismatch`; the combination is "any other"; the run stops before any `--apply`; no sentence is asked for; nothing renamed. |
| F8 | Run the command with `m-8` (open), `m-7` (recent, kept), `m-99` (unknown), no argument, and two arguments. | Each is refused at step 1 or in the preview, with nothing written and no sentence asked for. |
| F9 | In the checkout: `git diff e6c12be --stat -- payload`. | Only the command file, the integration suite, `COMMAND_FILES.md` and the operator reference (CP1), and `ORCHESTRATION_PROTOCOL.md`, `workflow_protocol.py` and its test (CP2). `tools/release/release_test.py` differs only in the three classes' counts (CP1) and the 2.23.0 class (CP2). The history row, the manifest and the pages agree on 2.23.0. |

F3 to F8 run the engine's forge query. They need a fake `gh` that answers `merged` (setup step 4). If the sandbox's `gh`
refuses, those flows cannot run there; that is an environment limit, not a product defect.

### Expected behaviour to confirm by reading

- The command never runs `tar`, `zstd`, `rm` or `mv` itself, and never passes `--archive-root` or `--repo-root`.
- A reply that names the id only, or the words only, applies nothing. The id is never taken from `$ARGUMENTS` text that
  carries the sentence, nor from the active item.
- After any refusal the run ends; the user runs the command again. `remove` never runs after an `archive` that failed.

### Known limitations (out of scope for this milestone)

- The prune of archives past the TTL (roadmap row 27f) is not part of this item.
- The check is token-based by design (an accepted limit, plan D-Guard): a message such as "do not archive and remove the
  review folder of m-1" matches the pattern. The previews and the engines' own checks stand behind it.
- No `--json` and no archive-root or repository override in the command; the script keeps those for its own use.
- The command is user-only: the agent does not invoke it. The tester types the command and sends the sentence in their own
  message.
- No flow runs against this repository's real `.ai-review/` folders or archive store.

## Next action

Manual functional testing of the candidate, against the checklist above. Findings go to
`.ai-review/retention-command/feedback/FUNCTIONAL_REVIEW.md`; `/apply-functional-review` routes each one. Once testing is
clean and every checkpoint of this item is `COMPLETE` (they are), `/accept-milestone` is the acceptance command. There is no
command that records acceptance of a partial round.
