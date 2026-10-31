# W35: Workflow 2.25.3 — the pull-request check state judges the latest run of each check (Revision 2)

- **Work item:** `ci-latest-check-run` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator: row 30 of `docs/ROADMAP.md` (`Current` from this plan, `Done` at
  acceptance), chosen by the owner ("Analise and prioritize the current issues and start addressing them", 2026-10-31).
- **Issue:** RodrigoFAbreu/workflow#122 (read with its comments: none). **Branch:** `milestone/ci-latest-check-run`
- **Base commit:** `198b82bfdaa921993354a36497674533afd47a31` (main after #136: the release source and this
  repository's own installation are both 2.25.2; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file,
  so the prose roadmap applies)
- **Plan revision:** 2. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.25.3, a **`fix:` patch**. The Workflow's fixed `gh` query returns `statusCheckRollup`, which lists
every check run on the head, including runs a later re-run superseded. `_checks` in `payload/scripts/workflow_forge.py`
walks every entry, so a failed first run and a green re-run of the same check make `checks.state` `failure`, and
`ci_green` and `no_standing_pr_objection` refuse a pull request GitHub itself shows as green (`mergeStateStatus` CLEAN,
`gh pr checks` all SUCCESS). Seen on workflow-controller#199 (2026-10-27): `validate / tests (4)` and
`validate / tests-result` FAILURE (started 11:10) and SUCCESS (started 12:39) on the same head after a close and reopen.

The fix is **one mechanism**: `_checks` keeps the latest run per check identity before it derives the state, treating a run as
superseded only when a later run of the same identity started after it had completed (a re-run). Both requirements, the `checks_failed` reopening cause and every other reader take the derived fact, so nothing
else changes.

### Hard limits (the owner's sizing rule)

One mechanism, low to medium complexity, **two checkpoints** (CP1 the change, its tests and its one documentation
sentence; CP2 the release). No new state key, protocol field, command file, refusal class or `gh` field. The plan is
about 245 lines. If review asks for a second mechanism (for example reading `gh pr checks`, or `mergeStateStatus`, as a
second source), STOP and split.

## 2. Facts this plan relies on (re-read at `198b82b`)

- `_JSON_FIELDS` is `number,url,state,headRefOid,reviewDecision,reviews,statusCheckRollup`. `statusCheckRollup` is one
  top-level field: `gh` returns all sub-fields of each entry with it. A CheckRun entry carries `__typename`, `name`,
  `workflowName`, `status`, `conclusion`, `startedAt`, `completedAt`, `detailsUrl`; a StatusContext entry carries
  `__typename`, `context`, `state`, `startedAt`, `targetUrl`. `workflowName`, `startedAt` and `completedAt` are
  therefore already in every recorded answer.
- `gh_argv` is pinned by `TestForgeParser.test_the_argv_is_the_fixed_constant_with_an_explicit_limit` and the query
  name by `FORGE_QUERY_NAME`; the stored provenance is the verbatim `gh` stdout plus the argv. **The query, its
  field list, its pin and its provenance do not change**: the same bytes are read, only `_checks` derives differently.
- The fake forges of the tests (`pr_checks` in `workflow_gate_policy_test.py`, `pr_record` in
  `workflow_acceptance_matrix_test.py`, and the `FAKE_GH` runners) feed entries with a `name`, a `status` and a
  `conclusion` only, with distinct names and no timestamps. Every such entry is a single occurrence of its identity, so
  those suites run unchanged.
- `ci_green` (`fact["checks"]["state"] == "success"`) and `no_standing_pr_objection` (`... == "failure"`) in
  `_acceptance_pr` of `workflow_gate_policy.py` read only the derived `{state, failing}`. The shape stays; `failing`
  stays the sorted set of names whose latest run failed.
- `payload/docs/ai-workflow/GATE_POLICY.md` item 5 of the acceptance requirements says "its checks are not
  `failure`"; it is the only description of the check state (`docs/exit-codes.md` does not describe it, so it does not
  change).

## 3. Design decisions

### D-Latest (the one mechanism)

`_checks` classifies every entry as it does today (one helper, `_check_state(entry)`, returns `failure`, `pending` or
`success` with exactly the current conditions), groups the entries by identity, and lets each group contribute one state.

- **Identity.** A CheckRun (an entry with a `name`): `("check", workflowName or "", name)`. A StatusContext (an entry
  with a `context` and no `name`): `("context", context)`. The kind is part of the key, so a check run and a status
  context with the same text are separate, and two workflows with the same check name are separate. An entry with
  neither is the identity `("check", workflowName or "", "unnamed")` as today's `"unnamed"`.
- **Order.** `startedAt` orders the runs of an identity, parsed as an ISO 8601 timestamp: a trailing `Z` is first
  replaced by `+00:00`, so the parse does not depend on the interpreter (`datetime.fromisoformat` takes `Z` only from
  Python 3.11). A `startedAt` that is missing, not a string, unparseable, naive (no offset) or the zero time
  `0001-01-01T00:00:00Z` is **unusable**; `completedAt` is read with the same parse and the same unusable classes (an
  unfinished run has the zero time).
- **Superseded (LMPR-R1-001).** `gh` gives no event field, so a `push` run and a `pull_request` run of one job, or two
  jobs with the same `name:` in a workflow, share an identity and must not hide one another. A run is superseded only by
  the latest run `L` of its group, and only when its `completedAt` is usable and not later than `L`'s `startedAt`: it
  had finished before `L` began, which is what a re-run is (the issue's FAILURE started 11:10 and completed before the
  SUCCESS started 12:39). A run that overlaps `L`, has no usable `completedAt` or is still unfinished is **concurrent**.
- **Rule for a group of one entry:** its own state, byte-identical to today.
- **Rule for a group of two or more:** if every entry has a usable `startedAt`, the greatest is unique, and every other
  entry is superseded by it, the state of that latest entry stands. Otherwise (a tie, any unusable `startedAt`, or a
  concurrent run) the order cannot be established and the **worst** state of the group stands (`failure` over `pending`
  over `success`). A failure is therefore never turned into a success by guesswork or by overlap, and a latest
  *started* unfinished run is `pending` even when an earlier run succeeded. A *queued* re-run has the zero `startedAt`,
  so its group is unusable and comes out as its worst state (`failure` after a failure): fail closed, as today, until
  the re-run starts.
- **Residual (named, section 4).** A `push` run that failed and completed, followed by a later `pull_request` run of the
  same job that passed, is indistinguishable from a re-run and stands as `success`. Telling them apart needs the event,
  which is a second field or source and out of scope.
- **Result.** `failing` is the sorted set of names of identities whose standing state is `failure`; `state` is `failure`
  when there is one, else `pending` when any identity is `pending` or the list is empty, else `success`; the input of a
  non-object entry still raises `ForgeUnparseableError`. Nothing is written by `_checks`: it is a pure function, so
  every refusal path of the change is "nothing is derived differently, nothing is stored".

### D-Docs

One sentence in `GATE_POLICY.md` item 5: the checks are those of the latest run of each check once the earlier run had
completed before it started; a repeated check whose order cannot be established, or whose runs overlap, counts as its
worst run, and an earlier run of a different event that completed first is not told from a re-run. No other page changes.

### D-Release

2.25.3, a `fix:` patch (title `fix: ...`, manifest 2.25.2 to 2.25.3). `manifest.json`: `workflow_version`, the six
changed records (`workflow_forge.py`, `workflow_gate_policy_test.py`, `GATE_POLICY.md`, and, for the release constant,
`workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md`) with the sentence "ci-latest-check-run
(workflow-2.25.3)", their `sha256` and `size`, the downgrade posture, and `conformance.suites` measured
(`workflow_gate_policy_test.py` 316 to 326; the others unchanged). Counts (83 artifacts, 6 templates) do not move.
`WORKFLOW_RELEASE` becomes 2.25.3 with its pinned assertions and the protocol document's example and `1.5` list; the
protocol stays 1.5. `docs/release-history.md`: the 2.25.3 row (the way back to 2.25.2 restores the old derivation, and
nothing needs undoing: no state or protocol changed) and its "Last checked with" line. `tools/release/release_test.py`: a
2.25.3 class; the 2.25.2 class gives up the current-release pins (version, constant, counts, digests, posture and the
`release-history.md` line), and **every docstring pointer "(2.25.2)" of the older classes moves to "(2.25.3)"**, with the
2.25.2 class gaining its own pointer (the check is line-break independent: `grep -n '(2\.25\.[012])\."""'
tools/release/release_test.py` prints nothing and `grep -c '(2\.25\.3)\."""' tools/release/release_test.py` prints 10).

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage CP1. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w35-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256`
and `size` of every record whose file differs, `release.py manager-block --release-dir <scratch> --write` measures the
suites (gate policy 326), the clone commits, and the "Verification commands" blocks of `docs/RELEASING.md` run from
there. The `tools/release` tests run with
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
The new tests also run under the Manager's orphan rule (the reaper). CP2's stock `stage-conformance` is the real proof.

### Tests (in `TestLatestCheckRun`, `workflow_gate_policy_test.py`, 10 tests)

Each builds entries with a small helper (`check(name, workflow, conclusion, started)`), calls `forge._checks`, and
asserts the whole `{state, failing}` dict.

| Id | Case | Expect |
| --- | --- | --- |
| t1 | the issue's data: two entries per name (`validate / tests (4)`, `validate / tests-result`, workflow `validate`), FAILURE started 11:10 and completed 11:40, then SUCCESS started 12:39, listed in both orders (failure first, success first) | `success`, no failing |
| t2 | SUCCESS then a later FAILURE, both list orders | `failure`, failing is the name |
| t3 | FAILURE then a later `IN_PROGRESS`; SUCCESS then a later `IN_PROGRESS`; the unfinished run has the zero `completedAt`; a failure then a *queued* re-run (zero `startedAt`) | `pending` for the first two; `failure` for the queued case (fail closed) |
| t4 | two workflows, the same check name: one failed, the other later succeeded; a check run and a status context with the same text | `failure` (separate identities), both pairs |
| t5 | repeated identity, fail closed: equal `startedAt`; one `startedAt` missing; unparseable; naive; zero time; non-string; each unusable value sits on the *later-listed, otherwise-standing* entry (the SUCCESS that would win), so accepting it flips the result; a `Z` and a `+00:00` form of the same instant tie | the worst state in every case, in both list orders |
| t6 | single entries: with and without `workflowName` or timestamps, a StatusContext (`state`), no entry, a mix of identities | exactly today's `{state, failing}` (`failing` sorted and deduplicated) |
| t7 | `failing` names only identities whose latest run failed: `a` fail-then-success, `b` success-then-fail, `c` only success | `failing == ["b"]` |
| t8 | end to end through `EvidenceRepo.query` with the issue's record (`reviewDecision` empty): the stored fact, `ci_green` and `no_standing_pr_objection` for it, and the same record with the latest run failing | the first two are met, the third is unmet and `checks_failed` is actionable |
| t10 | overlapping runs of one identity (a `push` and a `pull_request` run): FAILURE started 11:00 completing 11:50, SUCCESS started 11:10; and a FAILURE with a missing, zero or later-than-successor `completedAt` then a later SUCCESS | `failure` (concurrent, worst stands), both list orders; the same pair with the failure completing before the success starts is `success` |
| t9 | the `GATE_POLICY.md` text says the checks are those of the latest run of each check (a text pin) | passes with the sentence |

### Failure-only mutations (each passes on the baseline, fails once only the named change is made)

| Id | Mutation (in a scratch copy of `workflow_forge.py`) | Must fail |
| --- | --- | --- |
| m1 | the standing entry is the first of the group instead of the latest | t1 (list order) and t2 |
| m2 | the identity drops `workflowName` | t4 |
| m3 | the order ignores `startedAt` (the last in list order stands) | t1 and t2 (the other list order) |
| m4 | a tie or an unusable timestamp takes the last in list order instead of the worst state | t5 |
| m5 | the identity drops the kind (a status context and a check run share a key) | t4 |
| m6 | `failing` collects every failed entry, not only the standing ones | t7 |
| m7 | an unfinished latest run is dropped from the group before the choice | t3 |
| m8 | the documentation sentence is removed from `GATE_POLICY.md` | t9 |
| m9 | an unusable `startedAt` class is parsed as usable (a naive time read as UTC, the zero time, or a non-string coerced) | t5 |
| m10 | `completedAt` is ignored: the latest-started run always stands, overlapping or not | t10 |

## 4. Open decisions

None finalised silently: `docs/TECHNICAL_DECISIONS.md` has no open row this touches. The `fix:` patch is forced by the
immutability rule (a payload byte change under the unchanged published 2.25.2 is refused). `startedAt` orders the
runs and `completedAt` only decides whether an earlier run was superseded (D-Latest). The **residual** is accepted and
named (LMPR-R1-001): a non-overlapping `push` failure followed by a passing `pull_request` run of the same job reads as a
re-run, because the event is not in the recorded answer; D-Docs says so.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The latest run per check: the change, its tests and its sentence | - | 2 | 1 |
| CP2 | Release 2.25.3 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The latest run per check: the change, its tests and its sentence

**Files:** `payload/scripts/workflow_forge.py`, `payload/scripts/workflow_gate_policy_test.py`,
`payload/docs/ai-workflow/GATE_POLICY.md`.

- D-Latest: `_check_state`, the grouping and the rule in `_checks`; `_JSON_FIELDS`, `gh_argv` and `_derive` unchanged.
- The ten tests t1 to t10 (t9 pins the documentation sentence).
- D-Docs: the sentence in `GATE_POLICY.md`.
- `docs/ROADMAP.md` is written with this plan (row 30 `Current`) and becomes Done at acceptance, not in CP1.

**Verification** (D-Staging): the nine suites pass from the scratch-staged fixture (gate policy runs 326 tests); m1 to
m10 each fail as the table says and the baseline passes; the new tests pass under the reaper; `git diff 198b82b --
payload/scripts/workflow_gate_policy.py` is empty and `grep -n '_JSON_FIELDS = ' payload/scripts/workflow_forge.py` is
the unchanged line.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.3

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.3 with its pinned assertions and the protocol-document edits (protocol stays 1.5).
- `manifest.json` 2.25.3 (D-Release): version, the six records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.3 row and the page's "Last checked with" line.
- `tools/release/release_test.py`: a 2.25.3 class, the 2.25.2 class gives up the current pins, and every older
  docstring pointer moves to 2.25.3.
- `docs/ROADMAP.md` becomes Done at acceptance, not in CP2.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py
build --commit HEAD` succeeds; `check-manager-block --manager-releases tools/release/manager-releases.json` and
`tools/docs` are clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment; the
docstring-pointer greps of D-Release print nothing and 10.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

**Nothing runs against the real GitHub, the repository's `.ai-review/`, a forge or the network; no flow needs `gh`,
sockets, a zlib-ng Python or Python 3.12 except the last, which is marked as needing the full environment.** Setup,
once: `S=$TMPDIR/fr`; a clone of the base (`git clone -q "$PWD" "$S/base" && git -C "$S/base" checkout -q 198b82b`) and
the candidate tree is the working tree. Each flow below runs one snippet with `python3 -I -c`, importing
`workflow_forge` from the named `payload/scripts` directory, with `R=<that directory>`:

```python
import sys, json; sys.path.insert(0, R); import workflow_forge as f
def c(n, conc, at, wf="validate", st="COMPLETED", done=None):
    e = {"__typename": "CheckRun", "name": n, "workflowName": wf, "status": st, "conclusion": conc, "startedAt": at}
    if done: e["completedAt"] = done
    return e
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | the issue's data: `print(f._checks([c("tests (4)","FAILURE","2026-10-27T11:10:00Z",done="2026-10-27T11:40:00Z"), c("tests-result","FAILURE","2026-10-27T11:10:00Z",done="2026-10-27T11:40:00Z"), c("tests (4)","SUCCESS","2026-10-27T12:39:00Z"), c("tests-result","SUCCESS","2026-10-27T12:39:00Z")]))` with `R` the base clone's `payload/scripts`, then the candidate's | base prints `failure` with both names; candidate prints `{'state': 'success', 'failing': []}` |
| 2 | success (with `done`) then a later failure, and the same entries listed in the opposite order, on the candidate | `failure` with `['tests (4)']` in both orders |
| 3 | failure (with `done` before the next start) then a later `c("tests (4)","","2026-10-27T12:39:00Z","validate","IN_PROGRESS")`, then success then the same unfinished run | `pending` in both |
| 4 | two entries of the same check name in workflows `validate` and `release`, the first FAILURE, the second a later SUCCESS | `failure`: separate identities |
| 5 | a repeated identity with equal `startedAt`, with one `startedAt` removed, with `"not-a-time"` and with `"0001-01-01T00:00:00Z"`, a failure and a success each time | `failure` every time (fail closed) |
| 6 | single entries on base and candidate: one success, one failure, one pending, an empty list, a StatusContext `{"context": "ci", "state": "SUCCESS"}` | identical output on both trees |
| 6b | a `push` and a `pull_request` run of one job overlapping: `c("t","FAILURE","2026-10-27T11:00:00Z",done="2026-10-27T11:50:00Z")` and `c("t","SUCCESS","2026-10-27T11:10:00Z",done="2026-10-27T11:20:00Z")`, then the failure with `done` removed | `failure` both (concurrent, worst stands); with the failure's `done` at 11:05 it is `success` |
| 7 | `git diff 198b82b --stat -- payload scripts .claude` and `grep -n '_JSON_FIELDS = ' payload/scripts/workflow_forge.py` | only the three CP1 files and the three release-constant files changed; the field list is unchanged; installed copies untouched |
| 8 | (full environment) the nine suites from the staged fixture, then the `tools/release` tests with the zlib-ng Python and `python3 tools/docs/check_docs.py` | all pass; `workflow_gate_policy_test.py` runs 326 tests |

## 7. Disposition

| Source | What | Where | Proof |
| --- | --- | --- | --- |
| #122 expected | the latest run per check, by workflow name and check name | CP1 | D-Latest, t1 to t4, m1 to m5 |
| #122 expected | a genuinely failing latest run still counts | CP1 | t2, t3, t7, t8, m6, m7 |
| design constraint | ties, unusable timestamps and overlapping runs fail closed | CP1 | t5, t10, m4, m9, m10 |
| LMPR-R1-001 | concurrent runs of one identity keep the worst state; the non-overlapping event case is a named residual | CP1 | D-Latest, section 4, t10, m10 |
| design constraint | the query, its pin and its provenance do not change | CP1 | section 2, flow 7 |
| Row 30 | the release is a `fix:` patch, 2.25.3 | CP2 | D-Release |
