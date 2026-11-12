# W47: Workflow 2.29.3 — one pass over the stale wording of the plain acceptance commands (Revision 2)

- **Work item:** `wording-pass-plain-commands` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-12 ("sweep both repos and queue what's reported", ranked #2): RodrigoFAbreu/workflow#168, #165, #161 and #152 item 1; `docs/ROADMAP.md` row 41 (`Current` with this plan, `Done` at acceptance).
- **Branch:** `milestone/wording-pass-plain-commands`
- **Base commit:** `da8c68e6b55765a95d37a974a5f396821329859e` (main after #172: release source and own installation are 2.29.2; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2 (round 3's LPR-5, LPR-O5 to LPR-O7 applied, and round 4's LPR-6 applied without a revision bump: flow 5's mechanical check removed; each is validated against the repository, none rejected). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair. Behaviour, #155 items 4 to 6, the rest of #152, the Controller's contract: out of scope (D-Scope).

## 0. Phase 1: the investigation (before any design)

Each statement the four issues call stale was read on the base (all four issues read with their comments: none has a comment). **TRUE-FIX-NEEDED** = still false or misleading on the base; **ALREADY-FIXED** = true now; **KEEP** = intentionally left, with the reason.

| # | Statement on the base (file:line) | Class | Evidence and decision |
| --- | --- | --- | --- |
| E1 | #168 1a: `payload/docs/ai-workflow/audit/WORKFLOW_DEFECT_LEDGER.md:66` "`complete_work_item` has no phase guard" and the O13 paragraph at 1617-1620 "Unchanged." | TRUE-FIX-NEEDED | 2.29.1 added the guard (`workflow_state.py:13755-13759`). The row's status (`ACCEPTED`) is the review's and stays; the text says the guard now exists. No test reads the ledger's wording (the one sweep that mentions it excludes `audit/`). |
| E2 | #168 1b: the human-path list in `satisfy-gate.md:321` lacks `CompletionPhaseNotReachableError` | ALREADY-FIXED / KEEP | `satisfy-gate.md:208-209` already says "`complete_work_item` refuses the same phases (`CompletionPhaseNotReachableError`, the same codes) for every other caller". The list at 321 is the refusals reached **after** the stage's own phase check (`/accept-milestone` step 2a's phase and registry check is the transaction's first act, `satisfy-gate.md:201-205`), so adding the phase would misplace it. No edit. |
| E3 | #168 1c: `accept-milestone.md:253` and `apply-pr-review.md:165-166` "`complete_work_item` is unchanged" | TRUE-FIX-NEEDED | 2.29.1 changed it (a new refusal). The sentence means "a re-acceptance takes no path of its own"; it says "unchanged". Both files are pinned by the golden hash table of `workflow_integration_test.py` (0b). |
| E4 | #168 2: `workflow_state.py:13759` the `phase_not_reachable` detail "the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW" | TRUE-FIX-NEEDED | `milestone_complete_gate_reachable` (`:11375`) accepts `AWAITING_USER_ACCEPTANCE` too. Code output: 0b. The sibling string at `:20301` (the flags' blocker) is the **released JSON of the plain flags**: KEEP, unchanged. |
| E5 | #165 1: `satisfy-gate.md:268-269` "restore a damaged record from `HEAD`" | TRUE-FIX-NEEDED | The record is the top-level key `gate_policy_floor` (`GATE_POLICY_FLOOR_KEY`); a whole-file `git restore` discards another item's uncommitted edits, and with no floor in `HEAD` there is nothing to restore. |
| E6 | #165 2: `satisfy-gate.md:261-263` and `docs/exit-codes.md:35` "`state_changed: true` with `commit: null` means this call wrote the floor" | TRUE-FIX-NEEDED | The flag compares whole-file digests (`workflow_state.py:20569`), so another writer trips it too. Pinned verbatim by R6 (0b). |
| E7 | #161 1: `docs/exit-codes.md:31` "(or nothing, for an item with no finding)" | TRUE-FIX-NEEDED | Success always prints `{"paths": [...]}`; `[]` for an empty ledger. The same sentence in the 2.28.0 row of `docs/release-history.md:16`: **KEEP**, the row records what that release announced; the live page carries the truth. |
| E8 | #161 2: "both `false` nothing was written" in `accept-milestone.md:272`, `satisfy-gate.md:237`, `docs/exit-codes.md:32`; and (LPR-O1) "nothing was stored" for `--satisfy-acceptance` at `docs/exit-codes.md:29` | TRUE-FIX-NEEDED | `record_changed`/`state_changed` compare digests (`workflow_state.py:20508-20509`): a run that rewrote identical bytes also reads both false; `_satisfy_acceptance_cli` compares the same digest (`:20448`). |
| E9 | #152 1: `payload/docs/ai-workflow/REVIEW_PROTOCOL.md:657-658` "`/apply-plan-review` (or `/milestone-plan` again)" | TRUE-FIX-NEEDED | After the plan approval the route is `/request-plan-amendment`, then `/milestone-plan` (`workflow_fingerprint.py:299`, 2.25.7's message). Unpinned: the tests read only the heading. |
| E9b | LPR-3, the sibling copy of E9: `docs/common-problems.md:12`, "An approval became stale after a change": "for a plan, `/apply-plan-review` (or `/milestone-plan` again) and both review stages" | TRUE-FIX-NEEDED | A plan approval leaves the item at `IMPLEMENTING` or later, where `/apply-plan-review` is not admitted and `/milestone-plan` needs `/request-plan-amendment` first (`workflow_fingerprint.py:296-299`; `request-plan-amendment.md:69`): the troubleshooting page sends the user to a command that refuses. Unpinned (grep of the page's wording over the tests: only its "Last checked with" line is read, by the 2.25.7 class of `release_test.py`). Unlike E7's history row, this is a live page, not a record of what a release announced. |
| — | #168 3 (rename test P3; the plan's "15" for "377"); #161 3 (test coverage); #152 2 to 6; #155 4 to 6 | KEEP (out of scope) | Not command, message or page wording, or a behaviour/code change, or tracked elsewhere; the archived plan is history. |

### 0b. What the code-output and golden pins are

- **E4 (the library detail).** Reached only by a direct caller of `complete_work_item`: the plain flags run `_acceptance_reachability_blocker` first, inside the same lock, on the same state and with the same predicate, so they never reach the guard (the flow proves it by golden). No test pins its bytes: grep for `the acceptance stage needs` over `payload/`, `tools/`, `fixtures/`, `templates/` finds only the two source lines; the P tests assert `ctx.exception.code`. Changing it is a change of released output of a library refusal, hence a **patch**, and the flags' output is re-proved, **each flag with its own pin** (the two print different things at `IMPLEMENTING`, verified on the base): `--satisfy-acceptance` prints `{"code": "phase_not_reachable", "error": "AcceptancePreflightError", "message": "the phase is IMPLEMENTING; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW", ...}` and exits 1 (the exact object, all keys, a golden literal captured on the base); `--acceptance-gate` exits 0 with the read-only report, where the detail appears only as `blockers[0] = {"code": "phase_not_reachable", "detail": "the phase is IMPLEMENTING; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW"}` (pinned: exit 0, `ready: false`, and that blocker's exact `detail`). Both are before and after, pinned by new tests.
- **E6.** `test_r6_the_command_text_names_the_flag_and_the_rule` (`workflow_gate_policy_test.py`, the needle list) pins the old sentence verbatim: its needle changes with the wording, and gains one for E5. The only existing test edited besides the golden table.
- **E3.** `_GOLDEN_COMMAND_FILE_SHA256` in `workflow_integration_test.py` (entries `accept-milestone.md`, `apply-pr-review.md`): two hashes move, each with an "intentional content change" comment. The integration suite's other pins (`PRE_EXISTING` sentences) are not touched by the edits.
- **No pin** for the ledger, `REVIEW_PROTOCOL.md`, the exit-code rows, or `satisfy-gate.md` beyond R6 (grep of each file's SHA-256 over every test finds only the two golden entries).

### 0c. The Controller, patch or minor

The Controller reads the plain flags' JSON (`code`, `state_changed`, `commit`, `paths`) and the protocol operations; none returns the library's `CompletionPhaseNotReachableError` text (`ORCHESTRATION_PROTOCOL.md` and the schema do not name it; the call sits behind the blocker). **The Controller does not read any message changed here**: nothing is dropped, the protocol stays 1.5. A `fix:` patch (2.29.3): the changed text is a library refusal detail and documentation; no flag, key, code, phase, exit code or well-formed output moves.

## 1. Goal, release, scope

Correct every statement of 0a marked TRUE-FIX-NEEDED, by the smallest wording that is true, in `payload/`, `docs/exit-codes.md` and `docs/common-problems.md` (**LPR-O5**); add row 41. Semantics of every command are unchanged. Release 2.29.3.

## 2. Design decisions

### D-Wording: the exact corrections (one principle: say what the code does)

- E1: row 66 becomes "`complete_work_item` had no phase guard (2.29.1 added one); the command-level path is proven safe"; the paragraph's "Unchanged." becomes "Unchanged in this round; Workflow 2.29.1 later gave `complete_work_item` a phase guard (`CompletionPhaseNotReachableError`)."
- E3: "`complete_work_item` is unchanged" becomes "`complete_work_item` takes no separate path for a re-acceptance" (accept-milestone) and "... takes no separate path for it" (apply-pr-review); the rest of each sentence is kept.
- E4: only `:13759` becomes "...the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW or AWAITING_USER_ACCEPTANCE". `:20301` and every flag path are untouched.
- E5: "restore a damaged record from `HEAD`" becomes "restore only the `gate_policy_floor` key of the state file from `HEAD` (remove the key when `HEAD` has none; never restore the whole file, which would discard another item's uncommitted edits)".
- E6: the sentence becomes "`state_changed: true` with `commit: null` means the state file's content changed during the call: this call wrote the floor into it before it stopped, or another writer changed it" (the parenthetical contrast with the other flags goes); `docs/exit-codes.md`'s row (`--commit-gate-policy-floor`, exit 1) changes its parenthetical to "(`state_changed: true` here means the state file's content changed during the call: this call wrote the floor into it before it stopped, or another writer changed it; in the first case the re-run commits the floor)" -- the old continuation "and the re-run commits it" no longer follows in every case, so it is qualified, and CP1/CP2's release test pins this one sentence.
- E7: "(or nothing, for an item with no finding)" becomes "the paths to stage: the record and the dispositions file when it exists, `[]` for an item with no finding".
- E8: "nothing was written" becomes "the content of both files is unchanged" in the three places. **LPR-O1:** `docs/exit-codes.md:29` (`--satisfy-acceptance`, exit 1) says "`state_changed: false`: stop, nothing was stored"; its flag compares the same whole-file digest (`workflow_state.py:20448`), so it is added to E8: "nothing was stored" becomes "the state file's content is unchanged" (the rest of the cell, including its "another writer" clause, is true and kept). It is a fourth place, in `docs/exit-codes.md` only; its CP2 test pins it.
- E9: "`/apply-plan-review` (or `/milestone-plan` again)" becomes "`/request-plan-amendment` (admitted only at `IMPLEMENTING` or `SELF_REVIEWING_IMPLEMENTATION`) and then `/milestone-plan`"; the tail "then the two-stage plan review, then `/approve-review plan`" gains the parenthetical of the message it follows (`workflow_fingerprint.py:299`): "then `/approve-review plan` (or `/satisfy-gate` when the plan gate is automatic)"; the rest of step 2 is kept. **LPR-O3.**
- E9b (**LPR-3**): in `docs/common-problems.md`, "for a plan, `/apply-plan-review` (or `/milestone-plan` again) and both review stages" becomes "for a plan approved and then changed, `/request-plan-amendment` and then `/milestone-plan`, both review stages and the plan approval"; the rest of the paragraph (the code route, "Do not edit the approval by hand") is kept. Its "Last checked with: Workflow 2.25.7." line moves to 2.29.3 at CP2, with that of `docs/exit-codes.md`; the 2.25.7 class's assertion of the old line moves to the 2.29.3 class (CP2).

### D-Scope: what is left

Behaviour, the other #152/#161/#168/#155 items (0a), `docs/release-history.md`'s 2.28.0 row, the sweep corpus. A statement not in 0a is not touched.

### D-Tests (in `workflow_gate_policy_test.py`; written and run red first against the unedited tree)

Two new tests in the phase-guard class: **P7** the library detail for `IMPLEMENTING` names both phases and keeps `code == "phase_not_reachable"` and an unchanged state; **P8** the two plain flags at `IMPLEMENTING`, each pinned on its own as 0b states: `--satisfy-acceptance` exit 1 and its exact JSON object (message and all keys); `--acceptance-gate` exit 0, `ready: false` and the `phase_not_reachable` blocker's exact `detail`. R6's needle list: the E6 needle replaced, one needle added for E5 (`restore only the \`gate_policy_floor\` key`). The gate-policy count moves 422 to 424. Failure-only mutations, each failing exactly its test on a scratch copy: m1 the old library detail (P7 fails, P8 passes); m2 the blocker's detail `:20301` given the new text (P8 fails on both flags' pins, P7 passes); m3 the old E6 sentence back in `satisfy-gate.md` and m4 the old E5 clause (R6 fails each); m5 `accept-milestone.md` with the old sentence (the golden test fails).

### D-Golden, D-Release, D-Staging

- `_GOLDEN_COMMAND_FILE_SHA256`: the two new hashes, comment "workflow-2.29.3 (wording-pass-plain-commands, CP1): wording only -- intentional content change".
- 2.29.3 by the procedure of `docs/milestones/completed/PLAIN_COMMAND_MALFORMED_STATE_PLAN.md` (D-Release): changed records `workflow_state.py`, `workflow_gate_policy_test.py`, `workflow_integration_test.py`, `satisfy-gate.md`, `accept-milestone.md`, `apply-pr-review.md`, `REVIEW_PROTOCOL.md`, `WORKFLOW_DEFECT_LEDGER.md`, `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md` (`sha256`, `size`, sentence `wording-pass-plain-commands (workflow-2.29.3)`); suites: gate-policy 424, the others unchanged (1249, 377); `WORKFLOW_RELEASE` 2.29.3; a 2.29.3 class in `tools/release/release_test.py`, the 2.29.2 class gives up the current-release pins; the release-history row (patch; the way back restores the old wording; no state to undo); the posture rewritten with the guidance carried over sentence for sentence and "The release tooling and the maintainer documents are not part of the installed release." kept.
- CP1 changes shipped files whose records move at CP2: it verifies in a scratch clone under `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w47-tmp` with the records adjusted first (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging; counts as in the lstat-errors plan); `tools/release` runs with the zlib-ng interpreter named in `docs/RELEASING.md`. The one expected CP1 failure: the 2.29.2 class pins the gate-policy count. The new tests run again under the Manager's orphan rule (reaper).

## 3. Open decisions (for the plan reviewer and the owner)

No `docs/TECHNICAL_DECISIONS.md`, so no Open decision row is touched. Reversible: **patch or minor** (0c: patch); **the 2.28.0 history row kept** (E7); **P3's rename left to a later item** (it is a test name; adding it is one line and no count change); **`satisfy-gate.md:321`'s list kept** (E2). **The "another writer changed the state" sentence of the other plain flags** (the same digest comparison; no issue names them) is left as released.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The wording corrections, the library detail, the pins, the tests and row 41 | - | 2 | 1 |
| CP2 | Release 2.29.3 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The wording corrections, the library detail, the pins, the tests and row 41

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py`, `payload/scripts/workflow_integration_test.py`, `payload/.claude/commands/satisfy-gate.md`, `payload/.claude/commands/accept-milestone.md`, `payload/.claude/commands/apply-pr-review.md`, `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `payload/docs/ai-workflow/audit/WORKFLOW_DEFECT_LEDGER.md`, `docs/exit-codes.md`, `docs/common-problems.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): the base's golden literal is captured before any edit; P7 and P8 are run red (P7) and green (P8) on the unedited tree; m1 to m5 recorded.
- **The change:** the E1 to E9b edits of D-Wording and the one string at `workflow_state.py:13759`; `git diff da8c68e -- payload/scripts/workflow_state.py` is that one line. Existing tests edited: R6's needles and the two golden hashes, nothing else.
- **No other mechanism:** `git diff da8c68e --stat -- payload` lists exactly the eight payload files above; `docs/ROADMAP.md` carries row 41; `docs/exit-codes.md` and `docs/common-problems.md` carry their corrections.

**Verification:** the new and edited tests as the suite runs them; each corrected statement by the grep flows (before: present on the base, after: absent or true on the candidate); D-Staging: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block` (with `--manager-releases`), `tools/release` (zlib-ng interpreter, with the one expected failure); the new tests again under the reaper.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.3

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`, `docs/common-problems.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` 2.29.3 with its pinned assertions and the protocol-document edits (protocol stays `1.5`).
- `manifest.json`: `workflow_version`, the eleven changed records' `sha256`, `size` and `rationale` sentence, the gate-policy count, the posture.
- `docs/release-history.md`: the 2.29.3 row and "Last checked with" line (those of `docs/exit-codes.md` and `docs/common-problems.md` move too).
- `tools/release/release_test.py`: the 2.29.3 class (version, constant, counts, digests, posture, `CHANGED`, the wording of E6, E7 and E8 (including `--satisfy-acceptance`'s "state file's content is unchanged") in the exit-code page, E9b's wording and "Last checked with: Workflow 2.29.3." in `docs/common-problems.md` (the 2.25.7 class's assertion of the old line is removed there, and the sentence "`docs/common-problems.md` stays at 2.25.7" in that class's docstring (`release_test.py:3456`, `UnclassifiedPathMessageReleaseTest`) goes with it, so that the docstring does not become false (**LPR-O6**); the history row).
- `ORCHESTRATION_PROTOCOL.md`'s new sentence (**LPR-O4**) follows the 2.29.1 sentence's pattern but names neither `CompletionPhaseNotReachableError` nor any message text nor the phrase "needs AWAITING": it says only that 2.29.3 changes no flag and no protocol operation and that the protocol stays 1.5. Flow 6 therefore checks a stated constraint, and the 2.29.3 release test asserts it (the two needles of flow 6 absent from the document).

**Verification:** the nine suites from `release.py stage-conformance --commit HEAD`; `release.py build --commit HEAD`; `check-manager-block` (with `--manager-releases`), `tools/docs` and `check_docs.py` clean; `workflow-manager verify .` clean; the tools tests in the zlib-ng environment.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Flows 1 to 7 run offline: no network, no real `gh`, no install, no socket, no zlib-ng, no Python 3.12; nothing runs against the real repository, its `.ai-review/` or the forge.** Setup, once, `TMPDIR` set to `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w47-tmp`: `base/payload` from `git archive da8c68e6b55765a95d37a974a5f396821329859e payload/scripts payload/.claude/commands payload/docs`, `cand/payload` the working tree's same three directories copied (`command cp -af`); `export BASE="$TMPDIR/base/payload" CAND="$TMPDIR/cand/payload"`. The fake `gh` (it only proves **no** forge call) lives outside `/tmp`, `/var/tmp`, `/dev/shm` and `$TMPDIR`, mode 0755 in a directory only its owner writes:

```sh
export W47_BIN="$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w47-bin"
export GH_LOG="$W47_BIN/gh.log"
mkdir -p "$W47_BIN" && printf '#!/bin/sh\necho "gh called: $*" >> "$GH_LOG"\nexit 1\n' > "$W47_BIN/gh" && chmod 755 "$W47_BIN/gh"
cat > "$TMPDIR/stmts.py" <<'PY'
import os, sys
root, which = os.environ[sys.argv[1]], sys.argv[2]            # BASE|CAND, old|new
S = [("E1", "docs/ai-workflow/audit/WORKFLOW_DEFECT_LEDGER.md", "`complete_work_item` has no phase guard; the command-level path", "had no phase guard (2.29.1 added one)"),
     ("E3a", ".claude/commands/accept-milestone.md", "`complete_work_item` is unchanged: an automatic", "takes no separate path for a re-acceptance"),
     ("E3b", ".claude/commands/apply-pr-review.md", "`complete_work_item` is unchanged, and a re-acceptance", "takes no separate path for it"),
     ("E4", "scripts/workflow_state.py", "the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW\")", "AWAITING_FUNCTIONAL_REVIEW or AWAITING_USER_ACCEPTANCE"),
     ("E5", ".claude/commands/satisfy-gate.md", "restore a damaged record from `HEAD`", "restore only the `gate_policy_floor` key"),
     ("E6", ".claude/commands/satisfy-gate.md", "means this call wrote the floor into the file before it stopped", "or another writer changed it"),
     ("E8a", ".claude/commands/accept-milestone.md", "both `false` nothing was written", "content of both files is unchanged"),
     ("E8b", ".claude/commands/satisfy-gate.md", "`false` nothing was written", "content of both files is unchanged"),
     ("E9", "docs/ai-workflow/REVIEW_PROTOCOL.md", "`/apply-plan-review` (or `/milestone-plan` again)", "`/request-plan-amendment` (admitted only at")]
for tag, rel, old, new in S:
    t = " ".join(open(os.path.join(root, rel)).read().split())
    print(f"{tag:4s} {rel.split('/')[-1]:28s} old={t.count(' '.join(old.split()))} new={t.count(' '.join(new.split()))}")
PY
cat > "$TMPDIR/lib.py" <<'PY'
import sys, copy
from pathlib import Path
from unittest import mock
sys.path.insert(0, sys.argv[1]); import workflow_state as ws
st = {"schema_version": 1, "work_items": {"wi": {"work_item_id": "wi", "phase": sys.argv[2]}}}; before = copy.deepcopy(st)
with mock.patch.object(ws, "resolve_own_registry_completion_status", return_value=(True, None)):
    try: ws.complete_work_item(st, "wi", "2026-11-12T00:00:00Z", repo_root=Path(sys.argv[3]))
    except ws.CompletionPhaseNotReachableError as e: print(e.code, "|", e, "| state unchanged:", st == before)
PY
cat > "$TMPDIR/flags.sh" <<'SH'
R="$TMPDIR/r"; rm -rf "$R"; mkdir -p "$R/docs/ai-workflow"; cd "$R" && git init -q -b main && printf '.ai-review/\n' > .gitignore
printf '{"schema_version": 1, "active_work_item_id": "wi", "work_items": {"wi": {"work_item_id": "wi", "phase": "IMPLEMENTING", "registry_path": null, "governing_workflow_version": "2.2"}}}' > docs/ai-workflow/WORKFLOW_STATE.json
git add -A && git -c user.email=t@t -c user.name=t commit -q -m base && : > "$GH_LOG"
for f in --acceptance-gate --satisfy-acceptance; do PATH="$W47_BIN:$PATH" python3 -B "$1/workflow_state.py" $f wi > "$TMPDIR/out$f"; sha256sum < "$TMPDIR/out$f"; done
grep -o '"message": "[^"]*"' "$TMPDIR/out--satisfy-acceptance"
echo "gh calls $(wc -l < "$GH_LOG")"; git status --short
SH
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `for r in BASE CAND; do echo "== $r"; python3 -I "$TMPDIR/stmts.py" $r x; done` | base: every `old=` is `1` (E3a and E3b included) and every `new=` is `0`; candidate: every `old=` is `0` and every `new=` is `1` |
| 2 | `git show da8c68e:docs/exit-codes.md > "$TMPDIR/exit-base.md"`, then `for f in "$TMPDIR/exit-base.md" docs/exit-codes.md; do echo "== $f"; for s in 'nothing, for an item with no finding' 'this call wrote the floor into the file before it stopped' 'both .false.: stop, nothing was written' 'false.: stop, nothing was stored'; do grep -c "$s" "$f"; done; done; grep -c '^| 41 |' docs/ROADMAP.md; git show da8c68e:docs/common-problems.md > "$TMPDIR/cp-base.md"; for f in "$TMPDIR/cp-base.md" docs/common-problems.md; do echo "== $f"; tr '\n' ' ' < "$f" | grep -c 'for a plan, .*/apply-plan-review. (or .*/milestone-plan. again)'; tr '\n' ' ' < "$f" | grep -c 'for a plan approved and then changed'; done` (**LPR-O7**: the two E9b greps read the file with its newlines turned into spaces, like `stmts.py`, so a re-wrapped paragraph cannot hide the phrase), run from the repository root (plain files, no word-splitting: the same under zsh and `sh`) | base `1`, `1`, `1`, `1`; candidate `0`, `0`, `0`, `0`; the roadmap count is `1`; `docs/common-problems.md` (E9b): base `1` then `0`, candidate `0` then `1` (row 41 is added with this plan; `git show da8c68e:docs/ROADMAP.md \| grep -c '^| 41 |'` is `0`) |
| 3 | `for r in BASE CAND; do for p in IMPLEMENTING MILESTONE_COMPLETE; do python3 -I "$TMPDIR/lib.py" "$(eval echo \$$r)/scripts" $p "$TMPDIR"; done; done` | base: `phase_not_reachable | the phase is IMPLEMENTING; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW | state unchanged: True`; candidate: the same with `... needs AWAITING_FUNCTIONAL_REVIEW or AWAITING_USER_ACCEPTANCE`; `MILESTONE_COMPLETE`: `work_item_terminal | wi is already MILESTONE_COMPLETE | state unchanged: True` on both, byte-identical |
| 4 | `for s in BASE CAND; do sh "$TMPDIR/flags.sh" "$(eval echo \$$s)/scripts"; done` | **the plain flags' bytes are identical**: the two digests of the base equal the two of the candidate (`--satisfy-acceptance` exits 1 with the object below, `--acceptance-gate` exits 0 with `ready: false` and the `phase_not_reachable` blocker's `detail` unchanged); the `--satisfy-acceptance` object carries `"message": "the phase is IMPLEMENTING; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW"` (the old words, kept) and `"state_changed": false`; `gh calls 0`; `git status --short` prints nothing (the lock file is in the ignored directory) |
| 5 | `diff <(cd "$BASE" && cat scripts/workflow_state.py) <(cd "$CAND" && cat scripts/workflow_state.py)`; `diff -rq "$BASE/.claude/commands" "$CAND/.claude/commands"`; `diff -rq "$BASE/docs" "$CAND/docs"`; `diff "$BASE/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md" "$CAND/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md"` (the candidate is the working tree at functional review, after CP2) | one changed line in `workflow_state.py` (the `:13759` string); the commands differ in `accept-milestone.md`, `apply-pr-review.md`, `satisfy-gate.md` only; the docs differ in three documents, `REVIEW_PROTOCOL.md`, `audit/WORKFLOW_DEFECT_LEDGER.md` and `ORCHESTRATION_PROTOCOL.md` (**LPR-4**), and the last diff shows exactly three changed hunks and no other change (**LPR-5**; the lines are rewritten in place, so `diff` prints each as a removed line and an added one): section 1's release list (line 44, gains "**Workflow 2.29.3**"), the envelope example's `"workflow_release"` (line 64, `2.29.2` becomes `2.29.3`), and section 10's protocol-`1.5` note (lines 1193-1194, gains `2.29.3` and the new LPR-O4 sentence) (**LPR-6**: no substitution check is offered, because a release rewrites each list's last join, "X and Y" becoming "X, Y and Z", so a literal `2.29.3`-to-`2.29.2` replacement cannot reproduce the base; the three-hunk statement is the check) |
| 6 | `for r in BASE CAND; do grep -c 'needs AWAITING\|CompletionPhaseNotReachable' "$(eval echo \$$r)/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md" "$(eval echo \$$r)/docs/ai-workflow/orchestration-protocol-v1.schema.json"; done` | `0` for both files on both sides: the Controller's contract does not name the changed message (CP2 writes the 2.29.3 sentence without the class, the message or the phrase, **LPR-O4**); the protocol stays 1.5 (`grep -c 'PROTOCOL_VERSION = "1.5"' "$CAND/scripts/workflow_protocol.py"` is `1` on both) |
| 7 | mutations of the wording on a copy: `command cp -a "$TMPDIR/cand" "$TMPDIR/mut"`; in `mut/payload/.claude/commands/satisfy-gate.md` put back the old E6 words, then run flow 1 on it (`CAND=$TMPDIR/mut/payload`) and `diff` of its other lines against `cand` | exactly the E6 line reads `old=1 new=0` again, the other eight rows keep `old=0 new=1`; the same holds for each other statement put back alone |
| 8 | **Full environment (the repository and `python3`; the nine suites).** `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the loop of `docs/RELEASING.md` over `manifest.json`'s suites from inside the fixture (from a scratch clone with adjusted records at CP1, D-Staging) | all nine suites pass; the gate-policy suite counts 424 and P7, P8 and R6 pass; the integration suite's golden test passes with the two new hashes; the other suites are unedited |
| 9 | **Full environment (failure-only mutations m1 to m5 of D-Tests).** In the staged fixture's copy, one literal at a time (`python3 -I` one-liner with `assert s.count(x) == 1`), then `python3 -m unittest -k <test>` for the named test and for the other of P7, P8 and R6 | each mutant fails exactly its named test (m1: P7; m2: P8; m3 and m4: R6; m5: the golden-hash test) and no other; the unmutated fixture passes all |
| 10 | **Full environment (zlib-ng).** `python -m unittest discover -s tools/release -p '*_test.py'` with the zlib-ng venv; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | all pass (at CP1 the one expected failure of D-Staging) |
| 11 | **Scope (full environment).** `git diff da8c68e --stat` at CP1, then at CP2 | CP1: the eleven files of CP1 (the eight payload files, `docs/exit-codes.md`, `docs/common-problems.md`, `docs/ROADMAP.md`) plus the plan, registry, mapping, artifacts, state and `docs/ACTIVE_MILESTONE.md`; nothing under `.claude/`, `scripts/`, `docs/ai-workflow/` managed documents or `.workflow-manager/`; `manifest.json`, `workflow_protocol.py` and `tools/` untouched until CP2 |
