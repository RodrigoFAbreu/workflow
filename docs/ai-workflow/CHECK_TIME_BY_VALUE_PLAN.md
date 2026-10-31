# W36: Workflow 2.25.4 — the latest-run judge recognises the zero instant by value (Revision 1)

- **Work item:** `check-time-by-value` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 31 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance), chosen by the owner ("address the open issues by priority", 2026-10-31).
- **Issue:** RodrigoFAbreu/workflow#137 items 1 to 4 (item 5, the plan's table order, is cosmetic and out of scope).
  **Branch:** `milestone/check-time-by-value`
- **Base commit:** `e70ccb13434a381106a36ae030f68c880c9b7c92` (main after #139: the release source and this
  repository's own installation are both 2.25.3; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog
  file, so the prose roadmap applies)
- **Plan revision:** 1. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.25.4, a **`fix:` patch**. The latest-run judge of `payload/scripts/workflow_forge.py` (2.25.3) treats a
start or completion time as unusable when it is missing, not text, unparseable, naive, or the literal
`0001-01-01T00:00:00Z` (what GitHub emits for a queued or unfinished run). `_check_time` compares that **literal**, so
`0001-01-01T00:00:00+00:00`, `0001-01-01T00:00:00.000Z` and any offset that denotes the same instant parse as usable.
As the `completedAt` of a failed run such a value reads as "completed long before the re-run started", so a green run
could wrongly supersede a failure: against the invariant "never turn a real failure into success by guesswork". GitHub
emits the literal, so this is not known to occur; the gap is that the rule is stated by spelling, not by value.

The fix is **one mechanism**: `_check_time` parses the text and rejects by value every instant that cannot be a real
run time, failing closed (the group keeps its worst state, as for any unusable time). The rest of issue #137 is the
test that would have caught it, one documentation sentence, and the roadmap text.

### Hard limits (the owner's sizing rule)

One mechanism, low complexity, **two checkpoints** (CP1 the change, its tests, the sentence and the roadmap rows; CP2
the release). No change to the output shape, the query, its field list, its pin or any other behaviour; single-entry
and ordered cases stay byte-identical. The plan is about 230 lines. If review asks for a second mechanism, STOP and
split.

## 2. Facts this plan relies on (re-read at `e70ccb1`)

- `_check_time` (`workflow_forge.py`) is called only from `_standing_state`: for every `startedAt` of a repeated
  identity, and for the `completedAt` of every entry other than the latest. A `None` start makes the group
  unusable (worst state stands); a `None` or later-than-latest `completedAt` makes the earlier run concurrent (worst
  state stands). Nothing else changes with the helper.
- `datetime.fromisoformat` of the installed interpreters accepts the spellings below (offset forms, `.000`, `-00:00`);
  comparing two aware datetimes of different offsets does not overflow, but converting year 1 with a positive
  offset to UTC does, so the helper compares aware values and never converts. The `Z` suffix is still replaced
  by `+00:00` first (older interpreters do not read `Z`).
- `TestLatestCheckRun` (`payload/scripts/workflow_gate_policy_test.py`, 10 tests, gate policy suite 326) has the zero
  time in t5 only on the SUCCESS entry as `startedAt` and in t10 only as the literal `completedAt` (which, once `_ZERO_TIME` goes, is rejected only by the by-value zero test, so t10 now depends on it too). Accepting a zero
  `startedAt` on the SUCCESS entry still ends in failure (the failure then is the latest), which is why the mutation
  of issue item 2 survives.
- Row 30 of `docs/ROADMAP.md` says "the greatest timestamp wins, and a tie or an unusable timestamp keeps the worst
  state". The shipped rule (plan and code of `ci-latest-check-run`, revision 2) is: the latest-started run stands only
  when every other run had a usable `completedAt` not later than its start (a re-run); a tie, an unusable `startedAt`,
  an unusable `completedAt` or an overlap keeps the worst state.
- Item 5 of the acceptance requirements in `payload/docs/ai-workflow/GATE_POLICY.md` names, as residual, "an earlier run
  of a different event that completed first". Two jobs with the same `name:` in one workflow have the same
  `workflowName` and name too, so they share the identity, and a failed job followed by a passing one with the same
  name reads as a re-run.

## 3. Design decisions

### D-By-Value (the one mechanism)

`_check_time(value)` returns a usable aware `datetime` or `None`. `None` is returned when the value is not a string,
cannot be parsed, is naive, **or does not lie strictly after the zero instant and at or before the latest
representable instant**, both as UTC instants:

- `0001-01-01T00:00:00Z`, `…+00:00`, `….000Z`, `…-00:00`, `0001-01-01T05:30:00+05:30` (the zero instant in another
  offset) and `0001-01-01T00:00:00+01:00` (before the zero instant) are unusable. The literal `_ZERO_TIME` constant and
  its equality test go; the parsed value is compared with `datetime(1, 1, 1, tzinfo=timezone.utc)`.
- A value after `datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=timezone.utc)` (for example `9999-12-31T23:59:59-05:00`)
  cannot be an instant in the supported range: unusable. Such a start on a SUCCESS entry must not let it supersede a
  failure.
- Everything else keeps today's behaviour, including `0001-01-01T00:00:01Z` (not the zero instant) and every real
  time. Any non-zero year-1 value after the zero instant is deliberately accepted: the rule is the zero instant "by
  value" (issue #137), and GitHub never emits such a value.
- No exception escapes: a parse failure is `None` as today (`ValueError`); the comparisons do not overflow.
- `_standing_state`, `_checks`, `_check_state` and every caller are unchanged; the output is still `{state, failing}`.

### D-Docs

`GATE_POLICY.md` item 5: the residual sentence gains "or of another job of the same workflow with the same `name:`"
(both share the identity). One sentence; the text pins of t9 stay true. `docs/ROADMAP.md`: the new row 31 (`Current`,
`Done` at acceptance) and row 30's description corrected to the shipped rule (the completedAt supersede and the
overlap rule) in the same edit.

### D-Release

2.25.4, a `fix:` patch (title `fix: ...`, manifest 2.25.3 to 2.25.4). `manifest.json`: `workflow_version`, the six
changed records (`workflow_forge.py`, `workflow_gate_policy_test.py`, `GATE_POLICY.md`, and, for the release constant,
`workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`) with the sentence "check-time-by-value
(workflow-2.25.4)", their `sha256` and `size`, the downgrade posture, and `conformance.suites` measured
(`workflow_gate_policy_test.py` 326 to 330; the others unchanged). Counts (83 artifacts, 6 templates) do not move.
`WORKFLOW_RELEASE` becomes 2.25.4 with its pinned assertions and the protocol document's example and `1.5` list; the
protocol stays 1.5. `docs/release-history.md`: the 2.25.4 row (the way back to 2.25.3 restores the literal rule, and
nothing needs undoing: no state or protocol changed) and its "Last checked with" line. `tools/release/release_test.py`:
a 2.25.4 class; the 2.25.3 class gives up the current-release pins, and **every docstring pointer "(2.25.3)" of the
older classes moves to "(2.25.4)"**, the 2.25.3 class gaining its own (the check is line-break independent:
`grep -n '(2\.25\.[0-3])\."""' tools/release/release_test.py` prints nothing and
`grep -c '(2\.25\.4)\."""' tools/release/release_test.py` prints 11).

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage CP1. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w36-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256`
and `size` of every record whose file differs, `release.py manager-block --release-dir <scratch> --write` measures the
suites (gate policy 330), the clone commits, and the "Verification commands" blocks of `docs/RELEASING.md` run from
there, **except the `tools/release` tests, which CP1 does not run** (`CiLatestCheckRunReleaseTest` pins the current
release's gate-policy count at 326, `tools/release/release_test.py:3357`; against the 330 of the scratch manifest it
fails `330 != 326` until CP2 removes that pin, and a scratch-only pin edit would verify nothing real). The complete
`tools/release` suite runs once, in CP2, against the final 2.25.4 candidate, with
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
The new tests also run under the Manager's orphan rule (the reaper). CP2's stock `stage-conformance` is the real proof.

### Tests (in `TestLatestCheckRun`, four new tests, 14 in all)

Each uses the class's `check` helper and `both_orders`, asserts the whole `{state, failing}` dict, and puts the value
under test on the entry **whose acceptance would flip the result**. The zero-instant spellings (`ZEROS`): the literal,
`…+00:00`, `….000Z`, `…-00:00`, `0001-01-01T05:30:00+05:30`, plus `0001-01-01T00:00:00+01:00` (before zero), each a subtest.

| Id | Case | Expect |
| --- | --- | --- |
| t11 | the zero instant (each spelling) as the `startedAt` of the **FAILURE** entry, which completed (real time) before the later SUCCESS started: accepted, the failure would be the earliest and superseded | `failure`, failing is the name, both list orders |
| t12 | the zero instant (each spelling) as the `completedAt` of the earlier FAILURE (real `startedAt`) with a later SUCCESS: accepted, it reads as completed before the success started | `failure`, both list orders |
| t13 | `9999-12-31T23:59:59-05:00` as the `startedAt` of the later SUCCESS (the FAILURE completed first): accepted, the success would be the latest and supersede; and `0001-01-01T00:00:01Z` as the `startedAt` of the earlier FAILURE (still a real instant, completed before the success) | `failure` for the first, `success` for the second (a value that is not the zero instant is still usable), both list orders |
| t14 | the `GATE_POLICY.md` text names two jobs with the same `name:` among the shared identities (a text pin) | passes with the sentence |

t1 to t10 stay as they are (t5's zero `startedAt` on the SUCCESS entry and t10's literal `completedAt` remain).

### Failure-only mutations (each passes on the baseline, fails once only the named change is made)

| Id | Mutation (in a scratch copy of the named file) | Must fail |
| --- | --- | --- |
| m11 | `_check_time` reverts to the literal comparison (`value == "0001-01-01T00:00:00Z"`, no range check) | t11, t12 and t13 |
| m12 | `_standing_state` parses a zero `startedAt` as usable (the zero test skipped for starts only) | t11 |
| m13 | the zero test skipped for `completedAt` only | t10 and t12 (t10's literal `completedAt` is rejected only by the by-value zero test once `_ZERO_TIME` goes) |
| m14 | only the upper-range test removed | t13 |
| m15 | the residual sentence in `GATE_POLICY.md` loses the same-`name:` clause | t14 |

m1 to m10 of `ci-latest-check-run` keep failing the tests they named.

## 4. Open decisions

None finalised silently: `docs/TECHNICAL_DECISIONS.md` has no open row this touches. The `fix:` patch is forced by the
immutability rule (a payload byte change under the unchanged published 2.25.3 is refused). The shape of the answer, the
query and every other rule are untouched; the same-`name:` jobs and the `push`/`pull_request` pair stay a named
residual (D-Docs), as telling them apart needs the event, a second field or source and out of scope.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The zero instant by value: the change, its tests, its sentence and the roadmap rows | - | 2 | 1 |
| CP2 | Release 2.25.4 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The zero instant by value: the change, its tests, its sentence and the roadmap rows

**Files:** `payload/scripts/workflow_forge.py`, `payload/scripts/workflow_gate_policy_test.py`,
`payload/docs/ai-workflow/GATE_POLICY.md`, `docs/ROADMAP.md`.

- D-By-Value: `_check_time` and the removed `_ZERO_TIME` literal; `_standing_state`, `_checks`, `_JSON_FIELDS`,
  `gh_argv` and `_derive` unchanged.
- The four tests t11 to t14.
- D-Docs: the residual sentence in `GATE_POLICY.md`; row 31 (`Current`) and row 30's corrected description in
  `docs/ROADMAP.md`, written with this plan; row 31 becomes Done at acceptance, not in CP1.

**Verification** (D-Staging): the nine suites pass from the scratch-staged fixture (gate policy runs 330 tests; the
`tools/release` tests wait for CP2); m11 to
m15 each fail as the table says and the baseline passes; the new tests pass under the reaper;
`git diff e70ccb1 -- payload/scripts/workflow_gate_policy.py` is empty and `grep -n '_JSON_FIELDS = '
payload/scripts/workflow_forge.py` is the unchanged line.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.4

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.4 with its pinned assertions and the protocol-document edits (protocol stays 1.5).
- `manifest.json` 2.25.4 (D-Release): version, the six records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.4 row and the page's "Last checked with" line.
- `tools/release/release_test.py`: a 2.25.4 class, the 2.25.3 class gives up the current pins, and every older
  docstring pointer moves to 2.25.4.
- `docs/ROADMAP.md` row 31 becomes Done at acceptance, not in CP2.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block --manager-releases tools/release/manager-releases.json` and
`tools/docs` are clean; `workflow-manager verify .` is clean; the complete `tools/release` suite passes in the zlib-ng environment (its first run, against the final candidate); the
docstring-pointer greps of D-Release print nothing and 11.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

**Nothing runs against the real GitHub, the repository's `.ai-review/`, a forge or the network; no flow needs `gh`,
sockets, a zlib-ng Python or Python 3.12 except flow 8, which is marked as needing the full environment.**
Setup, once: `S=${TMPDIR:-/tmp}/fr`; a clone of the base (`git clone -q "$PWD" "$S/base" && git -C "$S/base" checkout -q e70ccb1`)
and the candidate tree is the working tree. Each flow runs one `python3 -I -c` snippet importing `workflow_forge` from
the named `payload/scripts` directory, with `R=<that directory>`, `Z` the zero-time spelling named in the flow, and:

```python
import sys; sys.path.insert(0, R); import workflow_forge as f
def c(n, conc, at, done=None, wf="validate", st="COMPLETED"):
    e = {"__typename": "CheckRun", "name": n, "workflowName": wf, "status": st, "conclusion": conc, "startedAt": at}
    if done: e["completedAt"] = done
    return e
F, S = "2026-10-27T11:10:00Z", "2026-10-27T12:39:00Z"   # the failure's start, the re-run's start
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `Z = "0001-01-01T00:00:00Z"`: `print(f._checks([c("t","FAILURE",Z,done="2026-10-27T11:40:00Z"), c("t","SUCCESS",S)]))` and the same with `c("t","FAILURE",F,done=Z)`, on the base clone then the candidate | both trees print `failure` (the literal is unusable on both) |
| 2 | `Z = "0001-01-01T00:00:00+00:00"`, same two prints | base prints `success` (wrongly superseding); candidate prints `{'state': 'failure', 'failing': ['t']}` |
| 3 | `Z = "0001-01-01T00:00:00.000Z"`, same two prints | base `success`; candidate `failure` |
| 4 | `Z = "0001-01-01T05:30:00+05:30"` (the zero instant in another offset), same two prints | base `success`; candidate `failure` |
| 5 | `Z = "0001-01-01T00:00:00-00:00"` and `"0001-01-01T00:00:00+01:00"` (before zero), same two prints each | base `success`; candidate `failure` |
| 6 | `print(f._checks([c("t","FAILURE",F,done="2026-10-27T11:40:00Z"), c("t","SUCCESS","9999-12-31T23:59:59-05:00")]))` | base `success`; candidate `failure` |
| 7 | the issue's re-run and the other unchanged cases on both trees: a failure with real `done` before a later success; a success then a later failure; an overlap (failure 11:00–11:50, success 11:10); `0001-01-01T00:00:01Z` as the failure's start with a real `done`; one single entry; an empty list | identical output on both trees: `success`; `failure`; `failure`; `success`; as today; `pending` |
| 8 | (full environment) the nine suites from the staged fixture, then the `tools/release` tests with the zlib-ng Python and `python3 -I tools/docs/check_docs.py` | all pass; `workflow_gate_policy_test.py` runs 330 tests |
| 9 | `git diff e70ccb1 --stat -- payload scripts .claude` and `grep -n '_JSON_FIELDS = ' payload/scripts/workflow_forge.py` | only the CP1 payload files and the three release-constant files changed; the field list is unchanged; installed copies untouched |

## 7. Disposition

| Source | What | Where | Proof |
| --- | --- | --- | --- |
| #137 items 1, 2 | the zero instant recognised by value, in every spelling; fail closed | CP1 | D-By-Value, t11 to t13, m11 to m14 |
| #137 item 2 | a test on the entry whose acceptance flips the result, with failure-only mutations | CP1 | t11 to t13, m11 to m14 |
| #137 item 3 | row 30 describes the shipped rule (completedAt supersede, overlap rule) | CP1 | D-Docs, flow 9 |
| #137 item 4 | the residual names two jobs with the same `name:` | CP1 | D-Docs, t14, m15 |
| #137 item 5 | the plan's table order | none | cosmetic, out of scope |
| design constraint | the query, the output shape and every other behaviour do not change | CP1 | section 2, flow 7 and 9 |
| Row 31 | the release is a `fix:` patch, 2.25.4 | CP2 | D-Release |
