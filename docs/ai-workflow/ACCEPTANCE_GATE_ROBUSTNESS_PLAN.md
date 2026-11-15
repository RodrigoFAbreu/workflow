# W52: Workflow 2.29.5 — the acceptance report never ends in an error for an absent pull-request head, its requirement partition is pinned, and the path messages name the right file and phases (Revision 5)

- **Work item:** `acceptance-gate-robustness` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner standing order (queue the reviewed follow-ups; a review of 2026-11-14 found
  these points still true on main): row 45 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#155 points 4, 5 and 6, and #152 points 2 to 5. **Branch:** `milestone/acceptance-gate-robustness`
- **Base commit:** `9d37c60434b50528f041c43717d3252060d6c830` (main after #183: release source and own installation are 2.29.4;
  automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 5. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1, the investigation: every point checked on main (`9d37c60`)

Each point was read in `payload/scripts` and, where it is behaviour, run on a hand-built repository (the test file's own
`AcceptanceRepo`, Python 3.14, no forge, no network; probes live outside the repository). Classes: TRUE-FIX-NEEDED, ALREADY-FIXED, KEEP.

| Point | State on main (file:line) | Class |
| --- | --- | --- |
| #155 points 1 to 3 | fixed by 2.29.2 (`_plain_command_state` 20366, the `except Exception` of `_acceptance_reachability_blocker` 20296 to 20299) | ALREADY-FIXED, not touched |
| #155 point 4: a stored PR fact whose head is absent | **reproduced**: a ready item whose stored `workflow_gh` fact is edited to head `0123…4567` (absent): `--acceptance-gate` prints `{"error": "AmbiguousBaseError", "message": "base '0123…4567' does not resolve to exactly one commit"}`, exit 1, no report. Cause: `acceptance_gate_report` (`workflow_state.py` 20308) calls `gate_policy.evaluate_gate` unguarded; `_acceptance_pr` (`workflow_gate_policy.py` 1901, the `position_of` call near 1935) calls `position_of`, `identity_at`, `approval_review_content_id`, `resolve_base` (`workflow_fingerprint.py` 731, raising at 741 and 747) | **TRUE-FIX-NEEDED** (D-Report) |
| #155 point 5, first half: `RegistryCoverageError` has no test | `test_m4_the_existing_clauses_keep_their_detail` (`workflow_gate_policy_test.py` 7376) pins that clause with a mock | ALREADY-FIXED (2.29.2) |
| #155 point 5, second half: every requirement id is in exactly one blocking set | `_ACCEPTANCE_REPORT_PR_REQUIREMENTS` and `_ACCEPTANCE_REPORT_BLOCKING_REQUIREMENTS` (20274) are tuples nothing ties to `ACCEPTANCE_REQUIREMENT_IDS` (`workflow_gate_policy.py` 1834); `PR_IDS` and `BLOCKING_IDS` of the test class (5117) are a third copy | **TRUE-FIX-NEEDED** (D-Partition) |
| #155 point 6, the detail | `_acceptance_reachability_blocker` (20301 to 20304) at the right phase with a checkpoint outstanding reads "the phase is AWAITING_FUNCTIONAL_REVIEW; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW and every checkpoint complete (outstanding: CP1)": the first clause contradicts the second | **TRUE-FIX-NEEDED** (D-Wording) |
| #155 point 6, `python3 -B` | the owner's list for this item names the detail only; `workflow_fingerprint.py` sets `sys.dont_write_bytecode` at import | KEEP, not touched |
| #152 points 1 and 6 | fixed (2.29.3) | ALREADY-FIXED, not touched |
| #152 point 2: the path by its own f-string | `unclassified_path_message` (`workflow_fingerprint.py` 262) writes `docs/ai-workflow/registry/{item}-artifacts.json`; `artifacts_path_for_work_item` (992) writes the same text separately; no test ties them | **TRUE-FIX-NEEDED** (D-Path) |
| #152 point 3: an explicit `artifacts_path` | `promote_legacy_work_item` (`workflow_state.py` 18808) loads the classification from its `artifacts_path` argument, then wraps the check in `naming_work_item(work_item_id)` (18890), which always names the templated path | **TRUE-FIX-NEEDED** (D-Path) |
| #152 point 4: "neither command is admitted" | `assert_plan_review_entry_phase` (`workflow_state.py` 17074) returns at once for a feedback-only item, so `/milestone-plan` is admitted at every phase of such an item; the sentence (`workflow_fingerprint.py` 301) says otherwise | **TRUE-FIX-NEEDED** (D-Phase) |
| #152 point 5: the 1079-character line | the plan-stage text is one line of 1079 characters for a known item (1158 for an unknown one); `docs/common-problems.md` is not shipped to an installed repository (it lives at the root, not under `payload/`), so the explanation cannot move there and the message would point at a page the reader does not have | **TRUE-FIX-NEEDED** as a split into lines (D-Phase); the move to the page is KEEP-out |

## 1. Goal

Ship Workflow 2.29.5, a **`fix:` patch**: **the plain acceptance report never ends in an error for the ambiguous-base case, the
requirement partition is pinned, and the path messages name the right file and phases.** Five changes: (1) a stored pull-request fact
whose head the repository lacks gives a named, blocked report (D-Report); (2) a test pins the partition (D-Partition); (3) the
`phase_not_reachable` detail stops contradicting itself (D-Wording); (4) the unclassified-path message takes its path from one
template and `promote_legacy_work_item` names the file it really read (D-Path); (5) the message's last sentence is true of every item
and its plan-stage text is split into lines (D-Phase). **The gate does not change**: `evaluate_gate` and every library function
return what they returned; the ambiguous-base case is the one report that moves from an error object to a report, and it is
never `ready`. No state key, phase, trailer, protocol field (the protocol stays 1.5) or command file moves.

**The Controller reads none of this.** `controller/` of `workflow-controller` has no reference to `UnclassifiedPathError`, a blocker
code, `stored_pr_fact` or the detail text; its copies of the command files under `.claude/commands/` are installed Workflow files, not readers. The
Controller's contract is out of scope and no change here touches it. Had it read one, that change would be dropped.

### Hard limits (the owner's sizing rule)

- **Two checkpoints** (CP1 the change, tests and pages; CP2 the release 2.29.5), under about 350 lines of plan. If review finds the plan
  past that, split: the report first (D-Report, D-Partition, D-Wording), the messages second (D-Path, D-Phase).
- This repository's own installation (`.claude/`, `scripts/`, the managed documents of `docs/ai-workflow/`, `.workflow-manager/`, managed
  blocks, the conformance workflow) stays untouched; the copies under `payload/` change.

## 2. Design decisions

### D-Report: `acceptance_gate_report`, an absent stored head

In `acceptance_gate_report`, `evaluate_gate` is called as before. On `fingerprint.AmbiguousBaseError` the report evaluates the gate
once more on a deep copy of the state whose item has `gate_evidence.pr` set to `None` (the shape of "no stored fact"), so the three
blocking requirements still say what they say. If that second call raises (the cause is not the stored fact: the anchor, say), the
exception propagates exactly as today (one JSON error, exit 1). The report also confirms the cause before it says it: the stored head is
read from the fact and the report treats the error as an absent head only when `git cat-file -e <sha>^{commit}` fails in the repository; if the commit
exists, the original `AmbiguousBaseError` propagates, so an ambiguity from another commit inside `identity_at` is never reported as an absent head. Otherwise the report differs from a normal one in four places only:

- `blockers` gains `{"code": "stored_pr_fact_unresolvable", "detail": "the stored pull-request fact is for head <sha>, which this repository does not have; fetch it (git fetch) and run this report again"}`, after the requirement blockers and before the disposition ones (the order: reachability, human gate or unmet requirements, this, dispositions). `ready` is therefore false;
- every pull-request requirement of `gate.requirements` (the two to four `_acceptance_pr` emits, by `require_ci` and `requires_pr_approved`; no fixed count) carries that same detail (the copy's own text, "no fact is stored", would be false);
- `stored_pr_fact.unmet` is the one entry `pr_fact_current` with that detail, and its `note` says the fact cannot be read here, so the report cannot say what the stage's query would decide;
- `gate.evidence` is the copy's (no stored fact). `query_pending` is the copy's (true: the stage's own query would replace the fact).

The new code is the only new output; `_acceptance_reachability_blocker`, the state context and every well-formed path are untouched, so
their bytes are identical (D-Golden). `satisfy_acceptance_gate` is untouched (its query replaces the fact before it decides).

### D-Partition

One test, in `TestAcceptanceGateReport`: `ACCEPTANCE_REQUIREMENT_IDS` equals the union of the two tuples, which are disjoint and have no
duplicate; every requirement id `evaluate_gate` emits for acceptance on the class's **automatic-mode** fixtures (`ready`, `stale`,
`stalenone`, `early`, `terminal`, `after_query`, spelled as the class spells them) is in the union. The `human` fixture is **not** in that
check: a human-mode gate returns the single requirement `human_gate` before `_evaluate_acceptance` (`workflow_gate_policy.py` 1323 to 1326),
and `human_gate` is in neither tuple nor in `ACCEPTANCE_REQUIREMENT_IDS` (1834 to 1837), which the library keeps. The test asserts that
fixture separately, as the mode branch (`["human_gate"]`, which `acceptance_gate_report` handles through `gate.get("mode") == "human"`, not through
the partition). A requirement added later fails the test until it is put in exactly one list. No production change.

### D-Wording: the `phase_not_reachable` detail

Only when the phase is one the stage accepts (`AWAITING_FUNCTIONAL_REVIEW` or `AWAITING_USER_ACCEPTANCE`) and a checkpoint is outstanding
(the contradictory case) the detail becomes `the phase is <phase>, which the acceptance stage accepts, but not every checkpoint is complete (outstanding: <id>)`. Every other phase keeps its released bytes
(`IMPLEMENTING` with or without an outstanding checkpoint: the existing `test_p8` and a new exact pin). The `--satisfy-acceptance` refusal
uses the same function and so says the same.

### D-Path: one template, the file really read

`workflow_fingerprint.ARTIFACTS_PATH_TEMPLATE = "docs/ai-workflow/registry/{work_item_id}-artifacts.json"` is used by
`artifacts_path_for_work_item` and by `unclassified_path_message` (known item, and the placeholder `<work_item_id>` of the unknown one), so they cannot
disagree; a test names the helper's result for several ids in the message. `unclassified_path_message` and `naming_work_item` take an optional
`declaration` (a repository-relative path string) that replaces the named file; `promote_legacy_work_item` passes `Path(artifacts_path).as_posix()`.
With the templated path (every other caller) the bytes are identical.

### D-Phase: the qualified sentence and the lines

"at any other phase neither command is admitted, so tell the user" becomes "at any other phase of a two-stage item neither command is
admitted, so tell the user" (a feedback-only item is admitted at every phase). The plan-stage text is the same sentences, joined by a newline
instead of a space after each full stop that ends a route (head; the declaration instruction; the phase route to `/milestone-plan`; the route through
`/request-plan-amendment`; the protocol pointer): five lines (141, 266, 226, 364 and 78 characters for the known form with path `x` and item `demo-item`, which gives the 1079 total; the head grows with the path, 157 for the test file's `_UPM_PATH`, and the qualification adds 20 to the fourth). No sentence is split, so the phase-set and ordering
checks of `test_t6` and the sentence checks of `test_t9` keep their regexes except the one sentence above (the phase-set test is `test_t6_the_plan_route_is_pinned_to_the_phase_sets`, the sentence test `test_t9`). The implementation-stage and the
interval texts are untouched.

### D-Golden: nothing that works changes

`workflow_gate_policy_test.py` (existing classes unmodified), the golden digests of `test_m5`, `test_p8`, and the message tests other than the ones named
in D-Tests pass unmodified. A `drive.py` (section 5) compares the report, the library and the messages of the base against the candidate byte for byte on the working paths.

### D-Tests

Every new test that asserts the new behaviour fails on the unedited tree first (T1, T2, T5 to T9). T3 (the unchanged library and the present-head report) and T4 (the partition, which already holds on main) are preservation tests: they pass on the unedited tree and are recorded as passing there; their sensitivity is shown by the mutations (T3 by m11, T4 by m4 and m5). Mutations are run on a scratch copy; each must fail the named test and only it.

- `workflow_gate_policy_test.py`, `TestAcceptanceGateReport`: **T1** an absent stored head: exit 0, `ready` false, exactly the one blocker with the
  head in its detail, the blocking requirements met, every pull-request requirement the policy emits and `stored_pr_fact.unmet` as D-Report; the tree, the refs and the lock
  file are unchanged and the trap `gh` was not called (the class's own `report` helper). **T2** the same at `IMPLEMENTING`: blockers `phase_not_reachable`
  then the new one. **T3** the library still raises `AmbiguousBaseError` on that state (the gate does not change) and a head that is present gives the existing
  report byte for byte; and, with the stored head present, the confirmation case (the `git cat-file -e` confirmation of D-Report): `gate_policy.evaluate_gate` is patched with `side_effect=[AmbiguousBaseError(...), <the real evaluate_gate result>]` (it raises on the first call only and delegates to the real evaluation for any later call, so that an evaluation of the copy would succeed), and the case calls `_acceptance_gate_cli` in process in the scratch repository with stdout captured (the class's `report`/`error` helpers run the flag in a `subprocess`, which a patch in the test process does not reach): the output is the one JSON error object and the exit is 1, with no report printed. Under m11 the confirmation is gone, the copy is evaluated through the real result, a report is printed with exit 0 and `stored_pr_fact_unresolvable`, and T3 fails. **T4** D-Partition (the automatic-mode fixtures against the union, the `human` fixture's `["human_gate"]` asserted apart). **T5** D-Wording: the new text at `AWAITING_FUNCTIONAL_REVIEW` and `AWAITING_USER_ACCEPTANCE`, the released text at
  `IMPLEMENTING` with an outstanding checkpoint, and the `--satisfy-acceptance` refusal. Mutations: m1 the `except` removed (T1, T2); m2 the blocker not appended (T1, T2);
  m3 the copy not hidden (T1, T2: the second `evaluate_gate` raises the same `AmbiguousBaseError` at `IMPLEMENTING` too); m4 an id added to `ACCEPTANCE_REQUIREMENT_IDS` (T4); m5 `ci_green` listed in both tuples (T4); m6 the wording condition dropped (T5); m11 the `git cat-file -e` confirmation removed (T3 only: T1 and T2 use an absent head and still pass).
- `workflow_fingerprint_generalization_test.py`: **T6** the message names `artifacts_path_for_work_item(id).as_posix()` for three ids and the template for the placeholder; the helper and
  the message share `ARTIFACTS_PATH_TEMPLATE`. **T7** `declaration` replaces the named file, in the known form only, and the default is byte-identical. **T8** the plan-stage text is five lines, none over
  400 characters for the test's short path, and rejoined with spaces it equals the text of 2.29.4 except the qualified sentence (the exact expected text is written out in `_upm_plan_route`). Mutations: m7 the helper's
  directory edited (T6); m8 `declaration` ignored (T7); m9 two lines joined (T8).
- `workflow_state_test.py`: **T9** `promote_legacy_work_item` with an explicit `artifacts_path` (the reconciliation, the classification load and the change check mocked, the last raising `UnclassifiedPathError`)
  names that file and not the templated one; with a templated path the text is the 2.29.4 text. `test_t6_the_plan_route_is_pinned_to_the_phase_sets` is updated for the one sentence. Mutation: m10 `naming_work_item` called without `declaration` (T9).

**Every test and doc that pins the old bytes** (each is updated in CP1 or CP2, and nothing else is): the 2.29.4 text of the plan-stage route in `_upm_plan_route` and
`_upm_known`/`_upm_unknown` (`workflow_fingerprint_generalization_test.py` 3573 to 3605); the sentence regex of `test_t6_the_plan_route_is_pinned_to_the_phase_sets` (`workflow_state_test.py` 23203); `docs/common-problems.md`
(the clause "At any other phase neither command is admitted", line 44); the `phase_not_reachable` detail is pinned by `assertIn("(outstanding: CP1)")` (`workflow_gate_policy_test.py` 5361, still true) and by
`test_p8` at `IMPLEMENTING` (unchanged bytes); the 2.29.4 class of `tools/release/release_test.py` and the 2.29.3 class's stamp of `docs/common-problems.md` (CP2). The 2.25.7 class and the release-history rows of 2.25.7 and 2.29.2 pin their own release text and stay.

### D-Docs

`docs/exit-codes.md`, the `--acceptance-gate` row: `stored_pr_fact_unresolvable` among the blockers, with its next step. `docs/common-problems.md`: the clause qualified as in D-Phase, and the
lines of the message. No page names an internal milestone id; the stamps move in CP2. `docs/ROADMAP.md` carries row 45 from this plan (`Current`).

### D-Release

2.29.5, a **`fix:` patch** (the manifest's version change and the pull request title agree; read `docs/RELEASING.md`). `manifest.json` `workflow_version` 2.29.5; the changed records
(`workflow_state.py`, `workflow_fingerprint.py`, the three test files, `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`) take their sentence, `sha256` and `size`; counts and
`distribution` do not move; `manager.conformance.suites` is measured by `release.py manager-block --write`. `WORKFLOW_RELEASE` becomes 2.29.5 with its pinned assertions and the protocol document's example (protocol 1.5).
`tools/release/release_test.py` gets a 2.29.5 class that carries the pin of the four suite counts with the measured counts (the pin now at `RetentionEngineErrorPathsTwoReleaseTest`, 3917 to 3920, moves there, as earlier releases moved it); the 2.29.4 class gives up that pin with its other current-release pins (and the `docs/exit-codes.md` stamp), the 2.29.3 class the `docs/common-problems.md` stamp.
`docs/release-history.md`: the 2.29.5 row (the way back to 2.29.4 restores the error object for an absent head, the old detail and the one-line message; nothing needs undoing). The release workflow publishes it;
the Manager lock and install pull requests follow (done by the orchestrator).

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1 verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w52-tmp` (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script, in the clone only and never part of CP1's change, (a) recomputes
`sha256` and `size` of every `artifacts` record whose file differs from its record (no record is added or removed, so `distribution` and the artifact counts do not move), (b) measures `manager.conformance.suites` (CP1 adds tests to `workflow_gate_policy_test.py`,
`workflow_fingerprint_generalization_test.py` and `workflow_state_test.py`, so these counts do move), and (c) rewrites the one pin that reads them, the four counts of `RetentionEngineErrorPathsTwoReleaseTest` (`tools/release/release_test.py` 3917 to 3920, which passes on main and fails
once a suite count changes), to the measured counts. That pin is the only edit to `tools/release` in the clone; it is CP2's change in the real tree (D-Release), so CP1's committed files do not include `tools/release/release_test.py` and the pin in the real tree still agrees with the real manifest. The clone is then committed and runs
the "Verification commands" of `docs/RELEASING.md` from there; the `tools/release` tests run with the zlib-ng interpreter
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`, with no skip and no deselection and with that single pin as the only difference from the real tree. The new tests also run under the Manager's orphan rule (the reaper): they start only `python3`
children that `subprocess.run` waits for. CP2's stock `stage-conformance` run is the real proof.

## 3. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **A blocked report over `ready` with an information line** for an absent head: the owner's order and #155 point 4 say `ready: false`; it costs one way forward (fetch the head), and the stage's own query is not claimed to be green or red.
- **The copy of the state** over catching inside `_acceptance_pr`: the library keeps raising (the gate does not change) and the three blocking requirements stay visible; the cost is one more evaluation on this path only.
- **Lines over a page move** for #152 point 5: the page is not installed with the Workflow. The cost: a newline inside an exception message, read by no script (section 1).
- **`python3 -B` and the `phase_not_reachable` detail of other phases** are KEEP: not in this item's list, released bytes.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The report, the partition, the messages, tests and pages | - | 3 | 1 |
| CP2 | Release 2.29.5 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The report, the partition, the messages, tests and pages

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_fingerprint.py`, `payload/scripts/workflow_gate_policy_test.py`,
`payload/scripts/workflow_fingerprint_generalization_test.py`, `payload/scripts/workflow_state_test.py`, `docs/common-problems.md`,
`docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): T1 to T9 written and run red against the unedited tree; mutations m1 to m11 each fail the named tests in a scratch copy and the results are recorded; `drive.py` (section 5) is run on the unedited tree and recorded.
- **The change** (D-Report, D-Wording, D-Path, D-Phase): the guarded evaluation and the one blocker, the condition of the detail, the template constant, the `declaration` argument and its one caller, the sentence and the line breaks. Every existing test passes
  unmodified but for that `test_t6` and the expected text of `_upm_plan_route`; the diff of the scripts touches those places only.
- **The pages** (D-Docs, CP1 part): `check_docs.py` stays clean; "Last checked with" lines are unchanged until CP2. `docs/ROADMAP.md` carries row 45 (`Current`); it becomes Done at acceptance.
- **No other mechanism:** `git diff 9d37c60 --stat -- payload` lists the two scripts and the three tests only.

**Verification:** D-Staging in a disposable clone (records, suite counts and the one count pin re-measured there; nothing of that is committed by CP1): the nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block`, `tools/release` (zlib-ng interpreter, no patch, no skip); `drive.py` identical on the working paths.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.5

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/common-problems.md`,
`docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.29.5 with its pinned assertions and the matching protocol-document edits (protocol 1.5).
- `manifest.json` 2.29.5 (D-Release): `workflow_version`, the changed records, the posture, `manager.conformance.suites`.
- `docs/release-history.md`: the 2.29.5 row and its "Last checked with" line; those of `docs/common-problems.md` and `docs/exit-codes.md` move to 2.29.5.
- `tools/release/release_test.py`: a 2.29.5 class; the pin of the four suite counts takes the measured counts; the 2.29.4 and 2.29.3 classes give up the pins named in D-Release.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean;
the tools tests pass in the zlib-ng environment; `workflow-manager verify .` is clean.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, the forge or the network.** Setup, once, as bullets (no installs, no sockets; flows 1 to 10 are offline):

- `$S` is a scratch directory under `$TMPDIR` (never `/tmp`); `base/` is `git archive 9d37c60 payload/scripts` extracted there and `cand/` is a copy of the working tree's `payload/scripts`;
- a fake `gh` that only logs its calls, in `$HOME/wf-fakebin` (mode 0755, not world-writable, not under `/tmp`, `/var/tmp`, `/dev/shm` or `$TMPDIR`), first on `PATH`; no flow may leave a line in `$HOME/wf-gh.log`:

```sh
#!/bin/sh
echo "gh called: $*" >> "$HOME/wf-gh.log"
exit 1
```

- `drive.py <scripts-dir> <case> [phase]`, kept outside the repository and run as `python3 -I`: it puts `<scripts-dir>` first on `sys.path`, builds a scratch repository by hand with the test file's own `AcceptanceRepo` (an item at `AWAITING_FUNCTIONAL_REVIEW`, a current technical approval, one passing flow, a stored open pull-request fact at the approved head), runs the one case and prints one JSON line (exit code, whether the tree hashes were unchanged, the digest of the report, `ready`, the blockers, `stored_pr_fact`). Cases: `ready`, `absent` (the stored fact's head edited to a 40-hex commit the repository lacks), `absent-early` (the same at `IMPLEMENTING`), `library` (prints the class `evaluate_gate` raises), `outstanding <phase>` (one checkpoint left in the registry), `partition` (prints the three sets);
- `msg.py <scripts-dir> <case>`: `plan <id or ->` prints the plan-stage text for the path `x`; `digests` prints the length, line count and digest of the implementation, interval and plan texts and the helper's path; `promote <artifacts_path>` runs `promote_legacy_work_item` with the reconciliation, the classification load and the change check mocked (the last raising `UnclassifiedPathError`) and prints the first sentence of the refusal.

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `drive.py` `ready` with `base/` and `cand/` | identical lines: exit 0, `ready` true, no blockers, the same digest, tree unchanged, no `gh` log |
| 2 | `drive.py` `absent` with `base/` and `cand/` | base: exit 1, `error` `AmbiguousBaseError`, no report. cand: exit 0, `ready` false, one blocker `stored_pr_fact_unresolvable` naming the head and "fetch it", `stored_pr_fact.unmet` the one id `pr_fact_current`; tree unchanged; no `gh` log |
| 3 | `drive.py` `absent-early` with `cand/` | blockers in order: `phase_not_reachable`, then `stored_pr_fact_unresolvable`; `ready` false; tree unchanged |
| 4 | `drive.py` `library` with `base/` and `cand/` | both print `AmbiguousBaseError`: the library did not change |
| 5 | `drive.py` `outstanding AWAITING_FUNCTIONAL_REVIEW`, `outstanding AWAITING_USER_ACCEPTANCE` and `outstanding IMPLEMENTING` with `base/` and `cand/` | the first two: base "the phase is X; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW and every checkpoint complete (outstanding: CP1)", cand "the phase is X, which the acceptance stage accepts, but not every checkpoint is complete (outstanding: CP1)". `IMPLEMENTING`: the digest and text identical |
| 6 | `drive.py` `partition` with `cand/`, then the new partition test in a scratch copy of `cand/` with `ci_green` appended to the blocking tuple of `workflow_state.py` | the two tuples are disjoint and their union is the seven ids; the mutated copy fails that test and no other |
| 7 | `msg.py` `digests` with both; `msg.py` `plan demo-item` and `plan -` (the path passed is always `x`) with both, then compare the cand text with its newlines turned into spaces against the base text | implementation, interval and helper lines identical; the plan text is 1 line (1079 characters) on base and five lines, each under 400, on cand; the only words that differ are "of a two-stage item" |
| 8 | `msg.py` `promote docs/ai-workflow/registry/legacy-core-artifacts.json` and `promote docs/ai-workflow/registry/demo-item-artifacts.json` with both | base names `demo-item-artifacts.json` for both. cand names `legacy-core-artifacts.json` for the first and the same text as base for the second |
| 9 | `git grep -n "other phase neither command is" 9d37c60 -- payload`; the same without the commit; `git grep -n "other phase neither command is" -- docs/common-problems.md` | the base commit matches in the script and in two test files; the working tree matches nowhere in `payload` or the page (the sentence now reads "of a two-stage item"); the page carries the same qualification |
| 10 | `python3 tools/docs/check_docs.py` | clean; no page names `acceptance-gate-robustness` |
| 11 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` tests and checker, `check-manager-block` | all pass, no skip |
| 12 | (needs the full environment) the `tools/release` tests with the zlib-ng interpreter; `git diff 9d37c60 --stat -- payload docs` | all pass; the diff lists in `payload` the two scripts and the three tests (CP1), plus the protocol script, its test and the protocol document (CP2); no state key, phase or command file |

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #155 point 4 | an absent stored head is a named, blocked report | CP1 | D-Report, T1 to T3, m1 to m3, m11 |
| #155 point 5 | first half already fixed; the partition is pinned | CP1 | D-Partition, T4, m4, m5 |
| #155 point 6 | the contradictory detail is reworded; `python3 -B` KEEP | CP1 | D-Wording, T5, m6 |
| #152 point 2 | one template for the declaration path | CP1 | D-Path, T6, m7 |
| #152 point 3 | the promotion names the file it read | CP1 | D-Path, T7, T9, m8, m10 |
| #152 point 4 | the sentence is true of every item | CP1 | D-Phase, the updated phase-route test |
| #152 point 5 | five lines; the page move is KEEP-out | CP1 | D-Phase, T8, m9 |
| Row 45 | a `fix:` patch, 2.29.5, the gate unchanged | CP1, CP2 | D-Golden, D-Release |
| #155 points 1 to 3, #152 points 1 and 6 | already fixed | - | section 0 |

The artifact declaration `docs/ai-workflow/registry/acceptance-gate-robustness-artifacts.json` is generated by `workflow_state.generate_artifacts_declarations` and then extended by hand for `payload/`, `tools/`, `fixtures/`, `templates/`,
`manifest.json`, `docs/release-history.md`, `docs/common-problems.md` and `docs/exit-codes.md`, as the earlier items' were; every path a checkpoint's **Files** paragraph names is classified at both stages. `docs/ROADMAP.md` stays excluded at both stages (as in every earlier item: acceptance edits it after the technical approval), so its row 45 is a classified, unprotected change.
