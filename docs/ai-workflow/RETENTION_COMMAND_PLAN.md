# W30: Workflow 2.23.0 — the user-only archive command (Revision 3)

- **Work item:** `retention-command` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 27e of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance; row 27f stays `Later`, now "after row 27e", and is not part of this item).
- **Issue:** RodrigoFAbreu/workflow#84 (the clutter of finished work), the user-gated step. **Branch:**
  `milestone/retention-command`
- **Base commit:** `e6c12beccd2fe839ba4426518888c7ccd41dbfc3` (main after #121: release source and own installation
  are 2.22.0; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 3 (round 1 of the local review applied: RC-R1-001, RC-R1-002 and the optional RC-R1-O1 to O6;
  round 2, the manual external review, applied: RC-EXT-001 and RC-EXT-O1; see section 8). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.23.0, a `feat:` minor, that adds **one command file**, `/archive-finished-item <work-item-id>`. It is
the only way the Workflow archives and removes a finished item's review folder in one act, and it is **user-only**:
the engines of rows 27c and 27d already do the work; the command only decides, with the user's literal confirmation,
whether to call them.

The command (all in the command file, nothing in a script):

1. takes exactly one work item id from `$ARGUMENTS`, refuses anything else;
2. **previews**: runs `python3 -I scripts/workflow_retention.py archive <id>` and `... remove <id>` (both dry runs,
   which write nothing) and prints both outputs in full;
3. **stops** and prints the one sentence the user must send: `Archive and remove the review folder of <id>.`;
4. only if the user's own current-turn message carries that sentence, with the id as an exact token, runs
   `archive <id> --apply` and then `remove <id> --apply`;
5. on any engine refusal, reports its code and `next step:` verbatim and stops: never retries, and never runs
   `remove` after an `archive` that did not succeed.

### The invariants (one sentence each)

- **I1. The command never packs, verifies, renames or deletes anything itself.** Its only effects are the two
  engine calls; it runs no `tar`, `zstd`, `rm` or `mv`, passes no `--archive-root` or `--repo-root`, and does not
  write the state file, the archive or its index.
- **I2. Nothing is applied without the literal sentence naming the item.** A missing sentence, a sentence naming
  another id (also an id of which this one is a prefix, or the reverse), or one carried over from an earlier turn
  or arriving inside `$ARGUMENTS` applies nothing. The previews of step 2 write nothing.
- **I3. `remove` runs only after `archive` succeeded** in this run, or after the archive step was shown to be
  already done (the one case in D-Steps).
- **I4. One item per run, no retry.** After any refusal the run ends; the user runs the command again.
- **I5. The engines stay the authority.** Which item is finished, kept, archived or leftover is decided by the
  engines' own rules at the moment of `--apply`; the command re-derives none of it.

### Hard limits (the owner's sizing rule)

- **One mechanism, no engine, state or protocol change.** `payload/` changes are the command file, the integration
  suite, the two documents that list the commands, the three release classes' count asserts (CP1), and (CP2) the
  release constant and its other pinned assertions. No change
  to `workflow_retention.py`, `workflow_state.py`, a phase, a trailer, a state key or `workflow_protocol.py`'s
  catalogue. Pruning (27f) is not here.
- **Two checkpoints** (CP1 the command, its tests and documents; CP2 the release). If this plan passes about 350
  lines or needs a third checkpoint, STOP and split before the first review.
- **This repository's own installation stays untouched** (`.claude/`, `scripts/`, `docs/ai-workflow/` managed
  documents, `.workflow-manager/`, managed blocks, the conformance workflow); the change goes to `payload/`,
  `manifest.json`, `tools/release/` and the pages `docs/RETENTION.md`, `docs/release-history.md`.

## 2. Facts this plan relies on (re-read at `e6c12be`)

- `payload/scripts/workflow_retention.py` (`# state_writer: false`) has `report`, `archive` and `remove`; both
  `archive` and `remove` are a dry run without `--apply`, take one id, and on a refusal print `error: <code>: <message>`
  and `next step: <text>` on stderr and exit 2. Both accept `--json`, `--archive-root` and `--repo-root`; the default
  archive root is under `~/.local/share/workflow-archive`.
- `remove` refuses `not_archived` when the archive or its index line is missing, so before the first `archive --apply`
  its dry run is expected to refuse; `archive` refuses `already_archived` when the archive exists.
- The user-only pattern (`retire-legacy-work-item.md`, `resume-implementation.md`, `adopt-gate-policy.md`):
  frontmatter `disable-model-invocation: true`, the pinned sentences "the control this command carries itself, under
  every harness" and "The agent must never invoke", "refuse to write anything unless", "Never fabricate, infer or
  carry over this text", and an ask-and-stop step. `workflow_state.validate_user_only_confirmation` serves only the
  stages `retirement` and `resumption` (`USER_ONLY_ACTION_STAGES`); extending it is an engine change, so this command
  states its own check in its body (D-Guard) and a test runs that check.
- Tripwires a new command file moves (all in the integration suite, which ships in `payload/scripts/`): the user-only
  table `USER_ONLY`, the guard-line width list, the set of `state_writer: false` commands (two today), and the
  operator reference's count of 23 command files and its sections (one `### \`/name\`` per file). The count 23 is
  stated in four places of the operator reference (`payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`: "holds 23
  files today, and all 23" at line 256, "The number 23 itself" at 271, `assertEqual(len(on_disk), 23)` at 272, and "roster
  of 23" in the `/bootstrap-workflow-v2` section at 1054) and pinned by two existing tests in the integration suite:
  `test_the_operator_reference_command_count_matches_reality` (`assertEqual(len(on_disk), 23)`, line 7410) and
  `test_the_command_inventory_claim_states_the_real_guarantee` (lines 7825-7835: the literal assert, the four strings
  above, and the list of stale forms of 16). The command is
  `state_writer: false` and `review-subject: none`; it is on neither the state-writer nor the review-subject roster.
- `COMMAND_FILES.md` says "seven commands" in two places and lists them; the operator reference lists them and says what
  each confirmation names.
- A new command file is a new manifest record: counts 81 to 82 and `distribution` 55 to 56, which three release
  classes in `tools/release/release_test.py` pin (and fail at `(82, 6) != (81, 6)` as soon as the record exists, so
  their count asserts move in CP1, the checkpoint that adds it to the verification tree): `RetentionReportReleaseTest` (2.20.0, lines 2959-2960),
  `RetentionArchiveReleaseTest` (2.21.0, 3012-3013) and `RetentionRemovalReleaseTest` (2.22.0, 3060-3061).

## 3. Design decisions

### D-Name

`/archive-finished-item`, file `payload/.claude/commands/archive-finished-item.md`, by the verb-object naming of
`/retire-legacy-work-item` and `/adopt-gate-policy`. Frontmatter: `description`, `argument-hint: "<work-item-id>"`,
`disable-model-invocation: true`, `state_writer: false`, `review-subject: none`. `$ARGUMENTS` appears in the body.

### D-Guard

The user-only guard has the two mechanisms of the existing commands: the flag, and the literal sentence the body
checks itself. The sentence is `Archive and remove the review folder of <id>.` where `<id>` is the resolved id. The
check, stated in the body as a fenced pattern so it is exact: collapse whitespace in the user's current-turn message,
then it must match `(?i)archive and remove the review folder of ID(?![A-Za-z0-9_-])` with `ID` the `re.escape`d id.
The id is a prefix-safe exact token (`m-1` never authorizes `m-10`; `m-10` never authorizes `m-1`), the final full stop
is not required, and the message may carry other words. That last point is an **accepted limit**: the pattern has no left-hand
context, so "do not archive and remove the review folder of m-1" matches, the same token-based posture as
`validate_user_only_confirmation`; the preview, the printed sentence and the engines' own checks still stand behind
it. The id comes from `$ARGUMENTS` only, never from the
confirmation. An `$ARGUMENTS` of more or fewer than one token that matches `^[a-z0-9][a-z0-9_-]{0,63}$` is refused
before anything runs, so the sentence can never arrive inside the arguments and the preview always comes first.
If the sentence is missing or wrong the command prints the sentence and stops.

### D-Steps

1. Resolve the id (above). Never the active work item; the engines refuse an unknown or open item themselves.
2. Preview, in this order: `archive <id>`, then `remove <id>`, both with no other flag, from the repository root, text
   output, printed in full. Read the result by exit status and the `error: <code>:` line:
   - `archive` exits 0 and `remove` refuses `not_archived`: expected before the first archive; **archive then remove**.
     Say that `remove` cannot be previewed until the archive exists, that its other preview checks (`tracked_files`,
     `cross_device`, `zstd_missing`) therefore first run at `remove --apply`, and that if one of them refuses there the
     archive is kept and the folder is untouched; and that `remove --apply` verifies the archive against the moved
     folder by contents before deleting anything;
   - `archive` refuses `already_archived` and `remove` exits 0: the archive step was done earlier (an interrupted
     earlier run); **remove only**;
   - any other combination (including both exiting 0, which cannot happen: an archive that exists makes `archive`
     refuse), or any other refusal code: report both outputs' codes and next steps and **stop**, with
     nothing applied. No confirmation is asked for a run that cannot proceed.
3. Print the sentence, say which of "archive then remove" or "remove only" it authorizes and that the folder is deleted
   only after the engine has verified the archive against it, and stop until the user's reply carries the sentence.
4. Apply, one engine call at a time: `archive <id> --apply` (unless remove only); on a non-zero exit report the code
   and next step and **stop** — `remove` is not run, the folder is untouched. Then `remove <id> --apply`; on a
   non-zero exit report the code, the next step and where the engine says the folder now is, and stop.
5. Report: the archive path and size from the engine's output, that the folder is gone, and that the retention report
   now lists the item as archived with no folder. Nothing else is run.

No step reads or writes the state file, the archive store or the index by hand; the engines hold their own locks.

### D-Docs

`COMMAND_FILES.md`: "seven" becomes "eight" in both places and the list gains the command. The operator reference: the
user-only list and its sentence on what each confirmation names, a section `### \`/archive-finished-item
<work-item-id>\` — user-only` in the format of its neighbours (When, Expects, Does, Writes, Next, Refuses), every place the
count 23 is stated (the four of section 2, including the `/bootstrap-workflow-v2` "roster of 23") moves to 24, and the `state_writer: false` paragraph (now three commands, `/review-functional`
and this one named beside `/prepare-review`). `docs/RETENTION.md`: a section "The archive-finished-item command" and
the sentences that point to row 27e (the intro, the archive and remove sections, guarantee 5) now say it exists.

### D-Tests

Written first, red against the unedited tree. All in `payload/scripts/workflow_integration_test.py`:

| Case | Proves |
| --- | --- |
| T1 | the command is in `USER_ONLY` with its needles, and the set of flagged files equals that table; the existing generic tests (neutrality, `$ARGUMENTS`, guard sentences) pass for it |
| T2 | the guard-line width test lists it |
| T3 | the `state_writer: false` set is exactly `prepare-review`, `review-functional`, `archive-finished-item`, and the operator reference says so |
| T4 | the operator reference has exactly one section per command file (24) and states 24 in every place it states the count; the two existing tests of section 2 move with it (24 for 23 in the current strings and in the `assertEqual(len(on_disk), ...)` pin, the 23 forms added to the stale list) |
| T5 | the body's engine calls: exactly the four invocation forms `archive <id>`, `remove <id>`, `archive <id> --apply`, `remove <id> --apply`; each parses with the engine's own `_parse`; `archive ... --apply` is written before `remove ... --apply`; no `--archive-root`, `--repo-root` or `--force`; no fenced or inline code span starting with `python`, `tar`, `zstd`, `rm` or `mv` other than those four forms (the body's other spans, `$ARGUMENTS`, the pattern and `error: <code>:`, are not commands); none of the tokens `WORKFLOW_STATE.json`, `state_transaction` or `state_lock` appears |
| T6 | the sentence and pattern pinned in the body: the exact sentence is accepted, case-insensitively and without the full stop; a message lacking it, naming only the id, naming only the words, naming another id, `m-10` for `m-1` and `m-1` for `m-10`, or a sentence arriving as `$ARGUMENTS` text are each rejected |
| T7 | the body pins "never retry", "never run `remove` after", "one item per run", "stop" at each refusal, and the ask-and-stop step 3 before any `--apply` |
| T8 | `COMMAND_FILES.md` counts eight and lists the eight; the operator reference's user-only list names all eight |

Each test is run once against a scratch copy with the corresponding line of the command removed or reordered (the
`--apply` pair swapped, the id check loosened to a substring, a flag added) and must fail there; the results are
recorded in the implementation bundle's `TEST_RESULTS.md`.

### D-Release

2.23.0: `manifest.json` gains the record for the command (`counts` 82, `distribution` 56, a `rule` of its own path),
and the changed records (the two documents, the integration suite, `workflow_protocol.py` and its test, the protocol
document) take their `retention-command (workflow-2.23.0)` sentence, `sha256` and `size`; `conformance.suites` is
measured by `release.py manager-block --write` (the integration suite's count moves). The protocol stays 1.5. The
downgrade posture says that going back to 2.22.0 removes the command and leaves archives, index and folders as they
are. `tools/release/release_test.py` is edited in two steps. **CP1:** in each of the three classes of section 2 (2.20.0,
2.21.0, 2.22.0) the hard-coded 81/55 count asserts move to the current 82/56 and nothing else changes (the precedent is
`9eb2eb1`, which moved 80 to 81 in the older classes), so the tests pass against CP1's scratch manifest. **CP2:** a
2.23.0 class, and the 2.22.0 class gives up the current-release pins to it. The implementer edits exactly the asserts
that fail, never a skip.

### D-Staging: scratch staging for CP1

CP1 changes shipped files and adds one whose record `manifest.json` moves only at CP2, so stock `stage-conformance`
cannot stage CP1's tree. The scratch manifest carries 82/56, which the three classes' count asserts expect once CP1 has
moved them, so `tools/release` passes there with no patch. CP1 verifies in a disposable clone under `$TMPDIR`
(`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w30-tmp`):
a scratch script recomputes `sha256` and `size` of every `artifacts` record whose file differs from its record,
**adds the record for the new command file and the counts**, measures `manager.conformance.suites` with
`release.py manager-block --release-dir <scratch> --write`, commits it in the clone, and runs the "Verification
commands" blocks of `docs/RELEASING.md` from there. Any `tools/release` failure is a stop for the plan; no test is
skipped. The `tools/release` tests run with the zlib-ng interpreter
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **Own check, not `validate_user_only_confirmation`.** Reusing the validator needs a third stage word in the engine
  (`USER_ONLY_ACTION_STAGES`), which the owner's brief rules out for this item. A later release may move the check into
  the library; the sentence the user types would not change.
- **`remove only` when the archive already exists.** One recovery case beyond "archive then remove": an earlier run
  archived and then stopped at `remove`. Without it the user would have to call the script by hand. It is taken only on
  the engine's `already_archived` refusal paired with a successful `remove` preview; every other refusal stops.
- **No `--json`, no overrides.** The command prints the engines' text; a non-default archive root or repository is the
  script's own use, not this command's.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The command, its tests and the documents | - | 3 | 1 |
| CP2 | Release 2.23.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The command, its tests and the documents

**Files:** `payload/.claude/commands/archive-finished-item.md`, `payload/scripts/workflow_integration_test.py`,
`payload/docs/ai-workflow/COMMAND_FILES.md`, `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
`docs/RETENTION.md`, `tools/release/release_test.py`.

- **Tests first** (D-Tests): T1 to T8 written and run red against the unedited tree; the mutations listed there fail
  at least one case each in a scratch copy, and the results are recorded.
- **The command file** (D-Name, D-Guard, D-Steps): the guard lines stay within the 90-column limit; the body names
  the model "the agent" and no harness. **Done:** T1 to T8 and the existing command-conformance tests pass.
- **The documents** (D-Docs): the two payload documents and `docs/RETENTION.md`. `check_docs.py` stays clean, no page
  names an internal milestone id, and the "Last checked with" lines are unchanged.
- **The release classes' counts** (D-Release): the 81/55 asserts of `RetentionReportReleaseTest`,
  `RetentionArchiveReleaseTest` and `RetentionRemovalReleaseTest` become 82/56; no other line of
  `tools/release/release_test.py` changes in CP1.
- **No other mechanism:** `git diff e6c12be --stat -- payload` lists the command file, the suite and the two documents
  only. `docs/ROADMAP.md` is written with this plan, not by this checkpoint.

**Verification:** D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`,
`check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng interpreter, no patch, no skip: the three classes pass at 82/56).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.23.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.23.0 with its two pinned assertions and the matching protocol-document edits (the
  protocol version stays 1.5).
- `manifest.json` 2.23.0 (D-Release): the new record, the counts, `workflow_version`, the changed records, the posture,
  `conformance.suites`.
- `docs/release-history.md`: the 2.23.0 row (the way back, the unchanged archives) and its "Last checked with" line;
  that of `docs/RETENTION.md` moves to 2.23.0.
- `tools/release/release_test.py`: a 2.23.0 class; the 2.22.0 class gives up the current-release pins to it (their
  count asserts moved in CP1).
- `docs/ROADMAP.md` is not written by this checkpoint: row 27e becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block` and `tools/docs` are clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 27e | the user-only command: names one finished item, previews both dry runs, applies `archive` then `remove` only on the literal sentence naming the id | CP1 | D-Steps, D-Guard, I1 to I4 |
| Row 27e | refuse on any engine refusal, report code and next step, never retry, no `remove` after a failed `archive`; one item per run | CP1 | D-Steps 4, I3, I4, T5, T7 |
| Row 27e | the guard, the listing and the documents | CP1 | D-Docs, T1 to T4, T8 |
| Row 27f | the prune | **not here** | later row, "after row 27e" |
| Roadmap, release | 27e Current with this plan; 2.23.0 bookkeeping | this plan; CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-command-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations`; every path a checkpoint's **Files** paragraph names is classified at
both stages (`assert_plan_artifact_declaration_coverage`, which reads those paragraphs only). Other paths the prose
mentions, such as `docs/RELEASING.md` (a reference for the verification commands, not edited here), are not claimed to
be classified.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its
`.ai-review/` or the real archive store**: every flow below uses a scratch repository under `$TMPDIR` whose `HOME` is a
scratch directory (so the default archive root is scratch), with the candidate's command file and
`scripts/workflow_retention.py` copied in, a `github.com` origin, a fake forge returning `merged`, a state of eight
finished items (so that with `KEEP_RECENT = 3` five are archivable, `m-1` and `m-10` among them; flows f4 to f7c each
use a fresh copy of the scratch repository) and one open, and a `.ai-review/<id>/` folder each (files, a nested directory, a symlink). Before and
after every flow the checks hash the scratch repository, the folders and the archive store.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`) | T1 to T8 pass, the whole integration suite passes, and the nine suites of `manager.conformance.suites` pass |
| f2 | the checkout (zlib-ng interpreter for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f3 | scratch repository, the command given an id | **the preview writes nothing and the command refuses without the literal sentence:** both dry runs are printed, the sentence is printed, and the hashes are identical; a reply without the sentence leaves them identical |
| f4 | the same | **a confirmation naming another item is rejected:** the reply names a different finished item, then `m-1` for `m-10` and `m-10` for `m-1`; nothing is applied |
| f5 | the same | **the literal sentence applies archive then remove:** the folder is gone, the archive and its index line exist, the other folders, tracked files and state are identical, the report lists the item archived with no folder |
| f6 | the same, a stand-in `zstd` that fails | **a failed archive stops the run:** exit reported with its code and next step, `remove` not run, the folder and the archive store identical to before |
| f7 | the same, a scratch `HOME` on a different file system from the scratch repository | **a failed remove reports where the folder is:** `archive --apply` succeeds, `remove --apply` refuses `cross_device` with its next step, the folder untouched and in place, the archive kept, no retry |
| f7b | the same, the archive made by hand first, then a file of the folder edited after the command's preview and before the confirming reply | **`remove` refuses `archive_mismatch` at apply time:** the command took "remove only", the engine renamed the folder aside, compared, refused and renamed it back; the folder is back in place byte for byte and the report says so, no retry |
| f7c | the same, a file edited after the archive was made and before the command is run | **the preview-time `archive_mismatch` stops the run:** the `remove` preview refuses, the combination is "any other", the run stops before any `--apply`, no sentence asked for, nothing renamed |
| f8 | the same | **an open item, a recent item, an unknown id, a missing or extra argument** are each refused in the preview or at step 1 with nothing written and no sentence asked for |
| f9 | the checkout | `git diff e6c12be --stat -- payload` lists the command file, the suite, the two documents and the CP2 files only, and `tools/release/release_test.py` differs only in the three classes' counts at CP1 and the 2.23.0 class at CP2; the history row, the manifest and the pages agree on the version |

## 8. Round 1 of the local plan review (applied in revision 2)

- **RC-R1-001 accepted:** section 2 names the four places of the operator reference and the two tests; D-Docs and T4 say
  "every place".
- **RC-R1-002 accepted:** f7 now reaches `remove --apply` through `cross_device`; f7b reaches `archive_mismatch` at apply
  time; the preview-time stop is its own row, f7c.
- **RC-R1-O1 accepted** (section 2, D-Release); **O2** stated as an accepted limit in D-Guard; **O3** named in D-Steps
  step 2; **O4** T5 names the forbidden tokens and what counts as a command; **O5** the stale clause is dropped from
  roadmap row 27f; **O6** section 7 fixes the scratch state at eight finished items and a fresh copy per flow.

## 9. Round 2 (manual external review, applied in revision 3)

- **RC-EXT-001 accepted:** reproduced by reasoning from the plan: the scratch manifest with the new record has counts
  82/56, the three classes pin 81/55. The count asserts move to 82/56 in CP1 (`tools/release/release_test.py` joins CP1's
  Files; D-Release, D-Staging, CP1 and CP2 say so), two checkpoints kept; the 2.23.0 class and the 2.22.0 class's
  current-release pins stay in CP2.
- **RC-EXT-O1 accepted:** the claim is narrowed to the paths of the checkpoints' **Files** paragraphs (section 6).
