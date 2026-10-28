# W32: Workflow 2.25.0 — the user-only prune command (Revision 1)

- **Work item:** `retention-prune-command` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 27g of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance).
- **Issues:** RodrigoFAbreu/workflow#126 (items 2 and 3 are folded in, section 8) and #123 (item 1 is this item's
  core). **Branch:** `milestone/retention-prune-command`
- **Base commit:** `8537d23f3d3a28872540703dfc00d99f78c486d8` (main after #128: release source and own installation
  are 2.24.0; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.25.0, a `feat:` minor, that adds **one command file**, `/prune-archives <work-item-id>...`, the sibling of
`/archive-finished-item`. The engine of row 27f (`workflow_retention.py prune`) already does the work; the command only
decides, with the user's literal confirmation, whether to call it with `--apply`. It is **user-only**.

The command (all in the command file, nothing in a script):

1. takes one or more work item ids from `$ARGUMENTS` (the id of each archive, its name without `.tar.zst`, exactly as
   the report's `archives` lists them; `m-1`, never `m-1.tar.zst`), matching the engine's own token pattern, all
   distinct; refuses anything else;
2. **previews**: runs `python3 -I scripts/workflow_retention.py prune <names>` (a dry run, which writes nothing) and
   prints its output in full;
3. **stops** and prints the one sentence the user must send: `Prune the archives <n1>, <n2>.`;
4. only if the user's own current-turn message carries that sentence naming **exactly** the named archives, runs
   `prune <names> --apply`;
5. on any engine refusal, reports its code and `next step:` verbatim and stops: never retries.

### The invariants (one sentence each)

- **I1. The command never deletes anything itself.** Its only effects are the two engine calls (dry run, then apply);
  it runs no `rm`, `mv`, `tar`, `zstd` or `unlink`, passes no `--archive-root`, `--repo-root`, `--ttl-days` or
  `--json`, and does not write the state file, an archive or the index.
- **I2. Nothing is applied without the literal sentence naming every named archive.** A missing sentence, one naming
  only some of them, one naming others besides, one naming a prefix or an extension of a name (`m-1` and `m-10`), or one
  carried over from an earlier turn or arriving inside `$ARGUMENTS`, applies nothing. The preview writes nothing.
- **I3. Never an archive the user did not name.** The apply passes the same tokens as the preview, none added.
- **I4. No retry.** After any refusal the run ends; the user runs the command again.
- **I5. The engine stays the authority.** Which archive is prunable, which item is open or recent and which removal is
  interrupted is decided by the engine at the moment of `--apply`; the command re-derives none of it. The apply does
  not bind to the preview: it is a new process that re-judges from scratch, and the preview only shows what the engine
  would do at that moment.

### Hard limits (the owner's sizing rule)

- **One mechanism, no engine, state or protocol change.** `payload/` changes are the command file, the integration
  suite, the three documents that list the commands (`COMMAND_FILES.md`, the operator reference, section 6.1 of
  `ORCHESTRATION_PROTOCOL.md`) and, at the release, the release constant with its pinned assertions. No change to
  `workflow_retention.py`, `workflow_state.py`, a phase, a trailer, a state key or the protocol catalogue.
- **Two checkpoints** (CP1 the command, its tests and documents; CP2 the release). If this plan passes about 350
  lines or needs a third checkpoint, STOP and split before the first review.
- **This repository's own installation stays untouched** (`.claude/`, `scripts/`, `docs/ai-workflow/` managed
  documents, `.workflow-manager/`, managed blocks, the conformance workflow).

## 2. Facts this plan relies on (re-read at `8537d23`)

- `payload/scripts/workflow_retention.py` has `prune <work_item_id>...` (`nargs="+"`), a dry run without `--apply`;
  on a refusal it prints `error: <code>: <message>` and `next step: <text>` on stderr and exits 2, with nothing on
  stdout. Its first check (`_check_id`) is the token pattern `^[a-z0-9][a-z0-9_-]{0,63}$` and refuses `runtime` and
  `archive`. A name given twice counts once. Refusals in order: `not_in_report`, `removal_interrupted`,
  `not_prunable`, `item_not_finished`, `archive_changed`, then under the lock `archive_busy` and the re-reads; a
  failed delete is `prune_failed`, whose message names `removed:` and `not removed:`. The apply builds a fresh
  report and fresh `lstat`s (`_seen_by_report`, steps 9, 12 and 13a compare with that run's own `seen`), so
  `archive_changed` at apply is reachable only inside the apply run's own window, never between preview and reply. The
  dry run exits 0 only when every named archive would be removed, so one preview decides the run (there is no pairing of two previews, unlike
  `/archive-finished-item`).
- The user-only pattern is `payload/.claude/commands/archive-finished-item.md` (row 27e): frontmatter
  `disable-model-invocation: true`, `state_writer: false`, `review-subject: none`; the pinned sentences "refuse to
  write anything unless", "Never fabricate, infer or carry over this text", "The agent must never invoke"; an
  ask-and-stop step; a fenced check pattern that the tests extract and run.
- Tripwires a new command file moves, all in `payload/scripts/workflow_integration_test.py`: `USER_ONLY` (line 8928
  area), the guard-line width list (`TestUserOnlyCommandLineWidth.FILES`), `test_the_state_writer_false_claim_matches_the_frontmatter`
  (three stems today and "One of the three commands" in the operator reference), `test_the_operator_reference_command_count_matches_reality`
  (`assertEqual(len(on_disk), 24)`, line 7411) and `test_the_command_inventory_claim_states_the_real_guarantee` (lines
  7830-7835: the literal assert, four strings, the stale forms), and `TestArchiveFinishedItemCommand.test_the_documents_list_it`
  (`"for seven of them"`, "eight commands"). The count 24 is stated in four places of the operator reference (lines
  256, 271, 272, 1074), "for seven of them the exact work item" at line 41, and "One of the three commands" at 1042.
  `COMMAND_FILES.md` says "eight commands" twice and lists them (lines 37, 81).
- `ORCHESTRATION_PROTOCOL.md` section 6.1 (lines 541-544) lists the user-only commands that are not actions:
  `/request-plan-amendment`, `/adopt-gate-policy` and `/release-checkpoint-start`. `/archive-finished-item` is missing
  (#123 item 1) and the new command is not an action either (no `wp.ACTIONS` entry, no catalogue row). No test pins the list.
- A new command file is a new manifest record: counts 82 to 83 and `distribution` 56 to 57. Four release classes of
  `tools/release/release_test.py` pin 82/56 today: `RetentionReportReleaseTest` (lines 2959-2960),
  `RetentionArchiveReleaseTest` (3012-3013), `RetentionRemovalReleaseTest` (3060-3061) and `RetentionPruneReleaseTest`
  (3155-3156). They fail as soon as the record exists, so they move in CP1, the checkpoint that adds the file to the
  verification tree (the precedent of row 27e).
- The engine finds `gh` through `workflow_forge.resolve_gh`, which refuses one inside a temporary directory, the
  repository or a world-writable directory (section 7 builds a fake outside all three).

## 3. Design decisions

### D-Name

`/prune-archives`, file `payload/.claude/commands/prune-archives.md`, by the verb-object naming of
`/archive-finished-item`. Frontmatter: `description`, `argument-hint: "<work-item-id>..."`,
`disable-model-invocation: true`, `state_writer: false`, `review-subject: none`. `$ARGUMENTS` appears in the body.

### D-Guard

The two mechanisms of the existing commands: the flag, and the literal sentence the body checks itself. The sentence
is `Prune the archives <n1>, <n2>.`: the names in the order of `$ARGUMENTS`, separated by a comma and a space, and the
**final full stop required** (it ends the list, so a name can never be read as a prefix of a longer word). The check,
stated in the body as a fenced pattern so it is exact: collapse the whitespace of the user's current-turn message,
then `(?i)prune the archives (T(?:, T)*)\.` with `T` the engine's token pattern `[a-z0-9][a-z0-9_-]{0,63}`, over
**every** match in the message. The confirmation holds when there is at least one match and, in every match, the
lower-cased list of names, as a set, equals the set of names in `$ARGUMENTS`. So a sentence naming only some of them,
naming others besides, naming a prefix or an extension of one (`m-1` for `m-10`, `m-10` for `m-1`), listing them with
"and", or lacking the full stop is rejected; order does not matter and the message may carry other words. A plain
`re.escape` and lookahead per name (as in row 27e) cannot reject a sentence that names others besides, which is why the
check compares the captured set. The accepted limit of row 27e stands: the pattern has no left-hand context, so
"do not prune the archives m-1." matches; the preview, the printed sentence and the engine's own checks stand behind it.
The names come from `$ARGUMENTS` only, never from the confirmation. An `$ARGUMENTS` that is empty, has a token not
matching the engine's pattern, or repeats a name is refused before anything runs, so the sentence can never arrive
inside the arguments and the preview always comes first.

### D-Steps

1. Resolve the ids (above; a token such as `m-1.tar.zst` is refused with the text "pass the work item id of each
   archive, its name without `.tar.zst`"). Never from the active work item and never from the report; the command does not list
   archives. The engine refuses an unknown or unprunable one itself.
2. Preview: `prune <names>` from the repository root, text output, no other flag, printed in full. Exit 0: go on. Any
   non-zero exit: report the `error:` code and the `next step:` line verbatim and **stop**; nothing was applied and no
   sentence is asked for.
3. Print the sentence, say that the archives listed in the preview are deleted for good (their index lines stay) and
   stop until the user's own next message carries it. If that message does not match, apply nothing, print the
   sentence again and stop.
4. Apply, one engine call: `prune <names> --apply`. On a non-zero exit report the code, the `next step:` line and the
   engine's `removed:`/`not removed:` lists verbatim, and stop.
5. Report the removed archives and the bytes from the engine's output, and that the index keeps its lines. Nothing
   else is run.

No step reads or writes the state file, the archive store or the index by hand; the engine holds its own lock.

### D-Docs

`COMMAND_FILES.md`: "eight" becomes "nine" in both places and the list gains the command. The operator reference: the
user-only list, the confirmation sentence becomes "for seven of them the exact work item ...; for `/prune-archives`
the exact archives; for `/adopt-gate-policy` the policy digest" (the count is not moved), a section
``### `/prune-archives <work-item-id>...` — user-only``
in the format of its neighbours (When, Expects, Does, Writes, Next, Refuses), every place the count 24 is stated moves
to 25, and the `state_writer: false` paragraph names four commands. Its Writes line says no tracked file and no state,
the engine deleting the named archive files in the archive store. `ORCHESTRATION_PROTOCOL.md` section 6.1: the list of
user-only commands that are not actions gains `/archive-finished-item` and `/prune-archives` (#123 item 1).
`docs/RETENTION.md`: a section "The prune-archives command", the sentences that point to the user-only command as a
later row now say it exists (the intro, the prune section, the guarantees), and the two prune-table edits of section 8, and the new section says to pass the work item id of each archive, never a
file name or path.
No page names an internal milestone id.

### D-Tests

Written first, red against the unedited tree. In `payload/scripts/workflow_integration_test.py`, a class
`TestPruneArchivesCommand` and the moved tripwires:

| Case | Proves |
| --- | --- |
| T1 | the command is in `USER_ONLY` with its needles, and the set of flagged files equals that table |
| T2 | the guard-line width test lists it, and its docstring says "nine" user-only command bodies |
| T3 | the `state_writer: false` set is exactly four stems and the operator reference says "four commands" (the existing test moved; "three commands" is a stale form) |
| T4 | one operator-reference section per command file (25) and 25 in every place it states the count; the two existing tests move (25 for 24 in the strings and the `assertEqual(len(on_disk), ...)` pin, the 24 forms added to the stale list) |
| T5 | the body's engine calls: exactly the two forms `prune <names>` and `prune <names> --apply`, each parsing with the engine's own `_parse` (names equal, `apply` as written); the dry run is written before the apply; no `--archive-root`, `--repo-root`, `--ttl-days`, `--json`, `--force`; no code span starting with `python`, `tar`, `zstd`, `rm`, `mv` other than those two; none of `WORKFLOW_STATE.json`, `state_transaction`, `state_lock` |
| T6 | the sentence check, extracted from the body and run: accepted exactly, case-insensitively, in any order, with other words around; rejected: no sentence, a subset, a superset, other names, `m-1` for `m-10` and the reverse, a missing full stop, an "and" list, the sentence arriving as `$ARGUMENTS`; and the `$ARGUMENTS` pattern accepts one or several distinct tokens and refuses none, a repeat and a bad token |
| T7 | the body pins "Never retry", "One run", the stop at a non-zero preview with no sentence asked for, and the order Preview, Ask and stop, Apply (the preview-result branches pinned, the gap #123 item 4 names for the sibling), and the mismatch branch of step 3 ("apply nothing, print the sentence again and stop") |
| T8 | `COMMAND_FILES.md` counts nine and lists the nine; the operator reference lists them, has its section and pins the form "for seven of them the exact work item ...; for `/prune-archives` the exact archives; for `/adopt-gate-policy` the policy digest"; section 6.1 of the protocol document names both commands, each a flagged file |

Each test is run once against a scratch copy with the corresponding line of the command removed or reordered (the
two forms swapped, the set comparison loosened to "each named is present", `--json` added to the apply) and must
fail there; the results go in the implementation bundle's `TEST_RESULTS.md`.

### D-Release

2.25.0: `manifest.json` gains the record for the command (`counts` 83, `distribution` 57, a `rule` of its own path)
and the changed records (the three documents, the integration suite, `workflow_protocol.py` and its test) take their
`retention-prune-command (workflow-2.25.0)` sentence, `sha256` and `size`; `conformance.suites` is measured by
`release.py manager-block --write`. The protocol stays 1.5. The downgrade posture says that going back to 2.24.0
removes the command and leaves archives, index and engine as they are. `tools/release/release_test.py` in two steps.
**CP1:** the four classes' 82/56 asserts become 83/57 and nothing else changes. **CP2:** a 2.25.0 class, and the
2.24.0 class gives up the current-release pins to it. The implementer edits exactly the asserts that fail, never a skip.

### D-Staging: scratch staging for CP1

CP1 adds a shipped file whose manifest record moves only at CP2, so stock `stage-conformance` cannot stage CP1's tree.
CP1 verifies in a disposable clone under `$TMPDIR`
(`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w32-tmp`):
a scratch script recomputes `sha256` and `size` of every `artifacts` record whose file differs from its record, adds
the record for the new command and the counts 83/57, measures `manager.conformance.suites` with `release.py
manager-block --release-dir <scratch> --write`, commits it in the clone, and runs the "Verification commands" blocks
of `docs/RELEASING.md` from there. The `tools/release` tests run with the zlib-ng interpreter
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
Any `tools/release` failure is a stop for the plan; no test is skipped. CP2's stock `stage-conformance` run is the
real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **Own check, not `validate_user_only_confirmation`.** Reusing it needs a third stage word in the engine, which the
  brief rules out; a later release may move the check into the library without changing the sentence.
- **Set comparison, full stop required.** Stricter than the sibling's pattern, because a list can name too many; the
  user types a comma-separated list and a final full stop, which the command prints for them to copy.
- **One preview.** The engine's dry run judges the whole run, so the command previews once; it does not first list the
  archives (that is `report`, a separate act).

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The command, its tests and the documents | - | 3 | 1 |
| CP2 | Release 2.25.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The command, its tests and the documents

**Files:** `payload/.claude/commands/prune-archives.md`, `payload/scripts/workflow_integration_test.py`,
`payload/docs/ai-workflow/COMMAND_FILES.md`, `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/RETENTION.md`, `tools/release/release_test.py`.

- **Tests first** (D-Tests): T1 to T8 written and run red against the unedited tree; the mutations listed there fail
  at least one case each in a scratch copy, and the results are recorded.
- **The command file** (D-Name, D-Guard, D-Steps): the guard lines stay within the 90-column limit; the body names
  the model "the agent" and no harness. **Done:** T1 to T8 and the existing command-conformance tests pass.
- **The documents** (D-Docs): the three payload documents and `docs/RETENTION.md`, with the section 8 edits.
  `check_docs.py` stays clean, no page names an internal milestone id, and the "Last checked with" lines are unchanged.
- **The release classes' counts** (D-Release): the four 82/56 asserts become 83/57; no other line of
  `tools/release/release_test.py` changes in CP1.
- **No other mechanism:** `git diff 8537d23 --stat -- payload` lists the command file, the suite and the three
  documents only. `docs/ROADMAP.md` is written with this plan, not by this checkpoint.

**Verification:** D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`,
`check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng interpreter, no patch, no skip).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/RETENTION.md`,
`tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.0 with its two pinned assertions and the matching protocol-document edits (the
  protocol version stays 1.5).
- `manifest.json` 2.25.0 (D-Release): the new record, the counts, `workflow_version`, the changed records, the
  posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.0 row (the way back, the unchanged archives and engine) and its "Last checked
  with" line; that of `docs/RETENTION.md` moves to 2.25.0.
- `tools/release/release_test.py`: a 2.25.0 class; the 2.24.0 class gives up the current-release pins to it.
- `docs/ROADMAP.md` is written with this plan (row 27g `Current`) and becomes Done at acceptance, not in CP2.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block` and `tools/docs` are clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| Row 27g | the user-only command: names the archives, previews the dry run, applies `--apply` only on the literal sentence naming every one | CP1 | D-Steps, D-Guard, I1 to I3 |
| Row 27g | refuse on any engine refusal, report code and next step, never retry, never an archive not named | CP1 | D-Steps 2 and 4, I3, I4, T5, T7 |
| Row 27g, #123 item 1 | list both user-only commands in the protocol's section 6.1; the guard, the listing and the documents | CP1 | D-Docs, T1 to T4, T8 |
| #126 items 2 and 3 | the two prune-table edits of `docs/RETENTION.md` | CP1 | section 8 |
| #126 items 1, 4, 5; #123 items 2 to 6 | the engine, the mapping, checklists and other wording | **not here** | stay on their issues |
| Roadmap, release | 27g Current with this plan; 2.25.0 bookkeeping | this plan; CP2 | D-Release |

The artifact declaration `docs/ai-workflow/registry/retention-prune-command-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations` and then extended by hand for `payload/`, `tools/`, `fixtures/`,
`templates/`, `manifest.json` and the docs pages, as the earlier retention items' were; every path a checkpoint's
**Files** paragraph names is classified at both stages. Other paths the prose mentions are not claimed to be classified.

## 7. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its
`.ai-review/`, the real archive store, the real forge or the network**, so an automated tester in a sandbox can run
every flow. Setup, once: a scratch repository under `$TMPDIR` with a `github.com` origin and a state of eight finished
items (so that with `KEEP_RECENT = 3` five are archivable) plus one open, the candidate's `prune-archives.md` and
`scripts/workflow_retention.py` copied in; a scratch `HOME` (the default archive root is under it); a **fake `gh`**, a
shell script that prints the merged-pull-request facts the retention tests' fake forge returns, placed in a
`fakebin` directory that is **not** under `/tmp`, `/var/tmp`, `/dev/shm`, `$TMPDIR` or the scratch repository and not
world-writable (a sibling of `$TMPDIR` in the run directory), first on `PATH`; five archives made by the engine's own
`archive --apply` for `m-1`, `m-10`, `m-2`, `m-3`, `m-4` and then **aged with `os.utime`** in the scratch store only
(`m-1`, `m-10`, `m-2` to 45 days, `m-3` and `m-4` left fresh). Each flow starts from a fresh copy of the scratch
repository and store; before and after it, hashes of the repository, the folders and the store are compared.

| Flow | Workspace | What it shows |
| --- | --- | --- |
| f1 | the staged conformance fixture of the candidate (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`) | T1 to T8 pass, the whole integration suite passes, and the nine suites of `manager.conformance.suites` pass |
| f2 | the checkout (zlib-ng interpreter for `tools/release`) | `python -m unittest discover -s tools/release -p '*_test.py'`, `python3 -m unittest discover -s tools/docs -p '*_test.py'`, `python3 tools/docs/check_docs.py`, `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` |
| f3 | scratch repository, the command given `m-1 m-2` | **no sentence applies nothing:** the dry run is printed, the sentence is printed, hashes identical; a reply without the sentence leaves them identical |
| f4 | the same | **a sentence naming only some, or another archive, is rejected:** `Prune the archives m-1.`, then `m-2, m-1, m-3.`, then `m-1, m-3.`, then `m-1` named where `m-10` is, and the reverse, then an "and" list; nothing is removed |
| f5 | the same | **the full dry-run-then-apply run removes exactly the named archives:** the reply `Prune the archives m-2, m-1.` removes `m-1.tar.zst` and `m-2.tar.zst` only; `m-10`, `m-3`, `m-4`, the index lines, the folders and tracked files are identical |
| f6 | the same, `m-1 m-3` (`m-3` fresh) | **a preview refusal stops with nothing removed:** the preview refuses `not_prunable` with its next step, no sentence is asked for, the store is identical |
| f6b | the same, `m-1 m-2`, after a successful preview | **an apply refusal is reported, not retried:** with the sentence sent, each of these sandbox actions between preview and reply gives a non-zero `--apply`, reported with its exact code, the `next step:` line and the `removed:`/`not removed:` lists verbatim, nothing removed, no retry: `.removing/m-1/` created in the scratch store (`removal_interrupted`); write permission removed from the scratch per-repository archive directory (`prune_failed` from the failed `unlink`, `removed: none; not removed: m-1, m-2`; not as root); optionally `touch` an archive (`not_prunable`, age 0) |
| f7 | the same | **a missing, extra or malformed argument** (none, a repeat, `M-1`, a sentence) is refused at step 1 with nothing written and no sentence asked for |
| f8 | the checkout | `git diff 8537d23 --stat -- payload` lists the command file, the suite, the three documents and the CP2 files only; `tools/release/release_test.py` differs only in the four classes' counts at CP1 and the 2.25.0 class at CP2; the history row, the manifest and the pages agree on the version |

## 8. Folded follow-ups (the two document items)

Both are edits to the prune table of `docs/RETENTION.md`, a page this item rewrites anyway; neither touches the engine.

- **#126 item 2:** table row 12 ("every named archive differs from what step 9 saw") now says that **any** named
  archive differing refuses the run, nothing removed.
- **#126 item 3:** the page names the `prune_failed` cause where it describes the deletes (table rows 12 and 13 and
  "How an archive is removed"): the engine's `removed:`/`not removed:` lists, which the new command reports verbatim,
  and a failed `lstat` (the archive could not be examined, `_check_unchanged`) is also `prune_failed`; row 12 then
  reads "`archive_changed` or `prune_failed`".
