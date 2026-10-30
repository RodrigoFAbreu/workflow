# W34: Workflow 2.25.2 — polish of the finished retention work (Revision 2)

- **Work item:** `retention-polish` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 29 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance), chosen by the owner ("Proceed with the clean up") from the follow-ups of the retention track.
- **Issues:** RodrigoFAbreu/workflow#123, #126, #129 and #132 (all four read with their comments).
  **Branch:** `milestone/retention-polish`
- **Base commit:** `586c86c99335192981b7b335d97347f473091b39` (main after #134: the release source and this
  repository's own installation are both 2.25.1; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file,
  so the prose roadmap applies)
- **Plan revision:** 2. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.25.2, a **`fix:` patch**, that polishes finished retention work and changes **no behaviour**: two words
of documentation made precise, three test assertions added or tightened, and the release-history record made accurate.
The engine `payload/scripts/workflow_retention.py`, every command file, every refusal message and every state key stay
byte-identical.

### Hard limits (the owner's sizing rule)

One mechanism (wording and test pins of finished work), low complexity, **two checkpoints** (CP1 the four in-scope
items; CP2 the release), no new code, command, state key, phase, trailer, protocol field or refusal class. The plan is
well under 300 lines and has one kind of review surface (text and assertions). If review adds a behavioural item, STOP
and split.

## 2. Facts this plan relies on (re-read at `586c86c`), and the item table

Release rule (`docs/RELEASING.md`, "A published version never changes" and "How a release happens"): `payload/` is the
release source, and a change to it needs a bump to an unpublished version whose Conventional-Commit impact agrees with
it. The in-scope items change two shipped test files and one shipped document, so the release is a **`fix:` patch,
Workflow 2.25.2** (title `fix: ...`, manifest 2.25.1 to 2.25.2). `docs:`/`test:` with no release is impossible: a
payload byte change under the unchanged published 2.25.1 is refused by the immutability check.

Every numbered item of the four issues, checked against main (2.25.1):

| Item | Verdict | Where / reason |
| --- | --- | --- |
| #123 1 (section 6.1 list of user-only commands) | DONE | 2.25.0: `ORCHESTRATION_PROTOCOL.md` section 6.1 names `/archive-finished-item` and `/prune-archives`; `TestPruneArchivesCommand.test_the_documents_list_it` pins it |
| #123 2 ("Writes: nothing in the repository") | **IN SCOPE** | the line is still at `WORKFLOW_V2_1_OPERATOR_REFERENCE.md` (the archive command's section) |
| #123 3 (docstring pointers of the 2.20.0/2.21.0 classes) | DONE | every older class docstring already ends "the current release's class (2.25.1)"; `RetentionLstatErrorsReleaseTest` is that class and 2.25.1 is the manifest version. CP2 moves all pointers to 2.25.2 as every release does (section 3, D-Release) |
| #123 4 (pin the preview-result pairs) | **IN SCOPE** | `TestArchiveFinishedItemCommand` has no assertion on step 2's bullets |
| #123 5 (checklist-text nits) | OUT OF SCOPE | transient documents of a finished item |
| #123 6 (`cross_device` next step) | OUT OF SCOPE | an engine refusal message: this item changes no engine behaviour or message |
| #126 1 (raw `OSError`) | DONE | 2.25.1 (`_lstat_at` coded refusals) |
| #126 2 (`RETENTION.md` prune table, step 12) | DONE | 2.25.1: row 12 now reads "**any** named archive differs" |
| #126 3 (`prune_failed` cause named) | DONE | 2.25.1: `RETENTION.md` rows 9, 12 and 13 name it |
| #126 4 (`retention-prune-mapping.json`) | OUT OF SCOPE | requirements mapping of a finished item: a record of a completed milestone, not edited |
| #126 5 (checklist errors) | OUT OF SCOPE | transient checklist text |
| #129 1 (`retention-prune-command-mapping.json` R1) | OUT OF SCOPE | mapping of a finished item, not edited |
| #129 2 (checklist's fake `gh` prose) | OUT OF SCOPE | transient checklist text (this plan's checklist carries no forge flow) |
| #132 1 (`RetentionRemove.stat_refused` prefix) | **IN SCOPE** | `workflow_state_completion_obligations_test.py`: the archive class's helper asserts "check the permissions of", the remove class's does not |
| #132 2 (`release-history.md` 2.25.1 row) | **IN SCOPE** | the row says only "an archive file or a `.removing` entry"; the engine also stats the `.ai-review/<id>` entry (the leftover probe and the removal's selection, `_lstat_at(item_id, ai_fd, ...)`) |

Four items remain (#123 2 and 4, #132 1 and 2). Nothing else is touched. `docs/RETENTION.md` and `docs/exit-codes.md` are
not edited, so their "Last checked with" lines stay at 2.25.1.

**Out of scope, stated so it does not read as a miss:** the manifest record of `scripts/workflow_retention.py` carries the
same sentence as the 2.25.1 history row ("a stat error other than \"not found\" on an archive-directory entry or a
`.removing` entry"). #132 item 2 names only the history row, and the record's file bytes do not change, so the record
is left alone and the six changed records of D-Release stay six.

## 3. Design decisions

### D-Wording (#123 item 2)

The archive command's **Writes** line in the operator reference becomes: "no tracked file and no state. The engines
write the archive and its index line in the archive store, and `remove` takes the untracked `.ai-review/<id>/` folder
away." (The wording the issue asks for; the `/prune-archives` section already uses "no tracked file and no state".)

### D-Pin (#123 item 4)

One new test in `TestArchiveFinishedItemCommand`, `test_the_preview_result_pairs_and_the_catch_all_stop_are_pinned`.
On the whitespace-collapsed body, between "Read each result by its exit status" and step 3, it asserts, in order: the
first pair (`archive` exits 0 and `remove` refuses `not_archived`, "The run is **archive then remove**"), the second
pair (`archive` refuses `already_archived` and `remove` exits 0, "The run is **remove only**"), and the catch-all
("any other combination, or any other refusal code: report both codes and their `next step:` lines and stop. Nothing
is applied and no sentence is asked for."); that the backticked codes directly following "refuses " (the pattern ``refuses `<code>` ``; the phrase "if one refuses
there" and the parenthesised `tracked_files`, `cross_device` and `zstd_missing` list name none) are exactly `not_archived` and
`already_archived`, and that each is a literal refusal code of `workflow_retention.py`, so a typo is caught too. The
corrected Writes sentence is pinned in the existing `test_the_documents_list_it` (no second new test). The suite count
of `workflow_integration_test.py` moves 376 to 377 at CP2.

### D-Prefix (#132 item 1)

`RetentionRemove.stat_refused` gains `self.assertIn("check the permissions of", result.error.next_step)`, exactly the
archive class's assertion. Every site goes through `_lstat_at`, so the prefix is in every call.

### D-Release

2.25.2, a `fix:` patch. `manifest.json`: `workflow_version`, the six changed records (the operator reference, the
integration and obligations tests, `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`, the last three for
the release constant) with the sentence "retention-polish (workflow-2.25.2)", their `sha256` and `size`, the downgrade
posture, and `conformance.suites` measured (integration 377; the others unchanged). Counts (83 artifacts, 6 templates)
do not move. `WORKFLOW_RELEASE` becomes 2.25.2 with its pinned assertions and the protocol document's example and `1.5`
list; the protocol stays 1.5. `docs/release-history.md`: the 2.25.2 row (the way back to 2.25.1 restores the old wording
and the weaker assertions, nothing needs undoing), the 2.25.1 row corrected (#132 item 2: "an archive-directory entry,
a `.removing` entry or the `.ai-review/<id>` entry"), and its "Last checked with" line. `tools/release/release_test.py`:
a 2.25.2 class; the 2.25.1 class (`RetentionLstatErrorsReleaseTest`) gives up the current-release pins on the version,
the constant, the counts, the digests, the posture and the `release-history.md` "Last checked with" line (the 2.25.2 class
takes those over), but **keeps** the pin "Last checked with: Workflow 2.25.1." on `docs/RETENTION.md` and
`docs/exit-codes.md`, the two pages that stay at 2.25.1; **every docstring pointer "(2.25.1)" of the older classes moves to
"(2.25.2)"** (the miss that #123 item 3 recorded), and the 2.25.1 class gains its own pointer, which is a ninth. Eight
pointers move now: three of them wrap across lines (`class` ends one line and `(2.25.1)."""` starts the next, at
`InterleavingPinsReleaseTest`, `RetentionReportReleaseTest` and `RetentionCommandReleaseTest`), so the check is
independent of line breaks: `grep -n '(2\.25\.[01])\."""' tools/release/release_test.py` prints nothing (every pointer ends
its docstring that way) and `grep -c '(2\.25\.2)\."""' tools/release/release_test.py` prints 9.

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage CP1. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w34-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256`
and `size` of every record whose file differs, `release.py manager-block --release-dir <scratch> --write` measures the
suites, the clone commits, and the "Verification commands" blocks of `docs/RELEASING.md` run from there. The release-test
counts do not move in CP1 (no record is added). The `tools/release` tests run with
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
The new test also runs under the Manager's orphan rule (the reaper). CP2's stock `stage-conformance` is the real proof.

### Failure-only mutations (each passes on the baseline, fails once only the named change is made)

| Id | Mutation (in a scratch copy) | Must fail |
| --- | --- | --- |
| m1 | command step 2: `not_archived` becomes `cross_device` | the new test (the pair and the code list) |
| m2 | command step 2: `already_archived` becomes `not_archived` | the new test |
| m3 | command step 2: the catch-all loses "Nothing is applied and no sentence is asked for." | the new test |
| m4 | command step 2: the catch-all bullet moves above the first pair | the new test (order) |
| m5 | command step 2: first pair "archive then remove" becomes "remove only" | the new test |
| m6 | operator reference: the archive Writes line returns to "nothing in the repository and no state ..." | `test_the_documents_list_it` |
| m7 | `workflow_retention.py` `_lstat_at`: "check the permissions of" becomes "look at" | with the old helper, `RetentionRemove` still passes (the gap); with the new assertion it fails |
| m8 | release history: the 2.25.1 row loses `.ai-review/<id>` | the 2.25.2 release-test class |

## 4. Open decisions

None finalised silently: `docs/TECHNICAL_DECISIONS.md` has no open row this touches. The one choice (a `fix:` patch
rather than a release-less `docs:`/`test:`) is forced by the immutability rule and is stated in section 2.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The four in-scope items: wording, three assertions | - | 1 | 1 |
| CP2 | Release 2.25.2 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The four in-scope items: wording, three assertions

**Files:** `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
`payload/scripts/workflow_state_completion_obligations_test.py`, `payload/scripts/workflow_integration_test.py`.

- D-Wording: the archive command's Writes line in the operator reference.
- D-Prefix: the one assertion in `RetentionRemove.stat_refused`.
- D-Pin: the new test, and the Writes pin in `test_the_documents_list_it`.
- `docs/ROADMAP.md` is written with this plan (row 29 `Current`) and becomes Done at acceptance, not in CP1.

**Verification** (D-Staging): the nine suites pass from the scratch-staged fixture; m1 to m7 each fail as the table says
and the baseline passes; the new test also passes under the reaper; `workflow_retention.py` is byte-identical to the
base (`git diff 586c86c -- payload/scripts/workflow_retention.py` is empty).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.2

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.2 with its pinned assertions and the protocol-document edits (protocol stays 1.5).
- `manifest.json` 2.25.2 (D-Release): version, the six records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.2 row, the corrected 2.25.1 row, and the page's "Last checked with" line.
- `tools/release/release_test.py`: a 2.25.2 class (pinning m8), the 2.25.1 class gives up the current pins except the two
  pages that stay at 2.25.1, and every older docstring pointer (eight, three of them wrapped) moves to 2.25.2.
- `docs/ROADMAP.md` becomes Done at acceptance, not in CP2.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block` and `tools/docs` are clean; `workflow-manager verify .` is clean;
the tools tests pass in the zlib-ng environment; `grep -n '(2\.25\.[01])\."""' tools/release/release_test.py` prints nothing and
`grep -c '(2\.25\.2)\."""' tools/release/release_test.py` prints 9 (the line-break-independent pointer check, D-Release); m8 fails
`RetentionPolishReleaseTest` in a disposable clone of the candidate (the release history is not in the `stage-conformance`
fixture), and the baseline passes there.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

Commands are copied from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its
`.ai-review/`, the real archive store, a forge or the network** (flow 6 uses a clone of it, never the repository itself); no flow needs `gh`. Setup, once: `S=$TMPDIR/fr`; stage
the candidate with `python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"`; for every
mutation flow copy it first (`command cp -rf "$S/fixture" "$S/m"`), edit the copy with `python3 -I -c` and run from
`"$S/m/scripts"` (the suites read the fixture's own git root).

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | the nine suites from the staged fixture, then `python -m unittest discover -s tools/release -p '*_test.py'` (zlib-ng Python) and `python3 tools/docs/check_docs.py` | all pass; `workflow_integration_test.py` runs 377 tests |
| 2 | in a copy, apply m1, then m2, m3, m4, m5 (one per copy) to `.claude/commands/archive-finished-item.md` and run `python3 -B -m unittest workflow_integration_test.TestArchiveFinishedItemCommand` | the baseline passes; each mutation fails exactly `test_the_preview_result_pairs_and_the_catch_all_stop_are_pinned` |
| 3 | in a copy, apply m6 to the operator reference and run the same class | fails `test_the_documents_list_it`; the baseline passes |
| 4 | in a copy, apply m7 to `scripts/workflow_retention.py`; run `workflow_state_completion_obligations_test.RetentionRemove` once without the new `assertIn` line (the 2.25.1 helper) and once with it | without it the class passes; with it the class fails |
| 5 | read the archive command's Writes line in the operator reference and the `RetentionRemove.stat_refused` helper | the Writes line reads as D-Wording states; the helper asserts the prefix like the archive class's |
| 6 | read the 2.25.1 and 2.25.2 rows of `docs/release-history.md`; make a disposable clone of the candidate (`git clone -q "$PWD" "$S/repo" && git -C "$S/repo" checkout -q <candidate>`; the `stage-conformance` fixture holds neither `docs/release-history.md` nor `tools/release/`, and `release_test.py` reads `REPO_ROOT / "docs" / "release-history.md"`), apply m8 to `"$S/repo/docs/release-history.md"` and run `RetentionPolishReleaseTest` from that clone with the zlib-ng Python; the baseline passes there | the 2.25.1 row names the archive-directory entry, the `.removing` entry and the `.ai-review/<id>` entry; the 2.25.2 row names #123, #132, no behaviour change and the way back; m8 fails the class |
| 7 | `grep -n '(2\.25\.[01])\."""' tools/release/release_test.py`, `grep -c '(2\.25\.2)\."""' tools/release/release_test.py` and `git diff 586c86c --stat -- payload scripts .claude` | the first prints nothing and the second prints 9 (every pointer, wrapped or not, says 2.25.2); the only shipped changes are the three CP1 files and the three release-constant files; installed copies untouched |
| 8 | `git diff 586c86c -- payload/scripts/workflow_retention.py payload/.claude` | empty: no engine or command file changed |

## 7. Disposition of every item

| Source | What | Where | Proof |
| --- | --- | --- | --- |
| #123 1, 3; #126 1, 2, 3 | already done on main | none | section 2 table |
| #123 5, 6; #126 4, 5; #129 1, 2 | out of scope (records of finished milestones, transient text, an engine message) | none | section 2 table |
| #123 2 | the Writes line | CP1 | D-Wording, m6, flow 3 and 5 |
| #123 4 | preview pairs and catch-all pinned | CP1 | D-Pin, m1 to m5, flow 2 |
| #132 1 | the prefix assertion | CP1 | D-Prefix, m7, flow 4 |
| #132 2 | the 2.25.1 row made accurate | CP2 | D-Release, m8, flow 6 |
| Row 29 | the release is a `fix:` patch, 2.25.2 | CP2 | D-Release |
