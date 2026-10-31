# Active Milestone

## Milestone

**Awaiting functional review** (`AWAITING_FUNCTIONAL_REVIEW`; technical approval `CURRENT`). W35:
`ci-latest-check-run` (`process`, governing version `2.2`), branch `milestone/ci-latest-check-run`, roadmap row 30
(RodrigoFAbreu/workflow#122). Plan: `docs/ai-workflow/CI_LATEST_CHECK_RUN_PLAN.md` (revision 2, approved by gate
policy). The goal, Workflow 2.25.3 (a `fix:` patch): the pull-request check state judges the latest run of each check,
so a failed run and a green re-run no longer leave `checks.state` at `failure`. Base commit `198b82b`; the previous
milestone, W34 `retention-polish`, is accepted (Workflow 2.25.2).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The latest run per check: the change, its tests and its sentence | **complete** |
| CP2 | Release 2.25.3 | **complete** |

## Verified state

- CP1: `_checks` in `payload/scripts/workflow_forge.py` groups entries by identity and keeps the latest run of each;
  `TestLatestCheckRun` (t1 to t10) passes; mutations m1 to m10 each fail the named tests; `workflow_gate_policy.py`,
  `_JSON_FIELDS` and the `gh` query are unchanged.
- CP2: `manifest.json` names 2.25.3 (six records re-hashed, the "ci-latest-check-run (workflow-2.25.3)" sentence, the
  posture, `workflow_gate_policy_test.py` 326); `WORKFLOW_RELEASE` is 2.25.3 with its pinned assertions and the
  protocol document edits (protocol stays 1.5); `docs/release-history.md` has the 2.25.3 row and its "Last checked
  with" line; `tools/release/release_test.py` has `CiLatestCheckRunReleaseTest`, the 2.25.2 class gave up the
  current-release pins, and every older docstring pointer names 2.25.3.
- Functional-review preparation: `TestLatestCheckRun` passes (10 of 10); `tools/docs` passes (34 tests);
  `tools/docs/check_docs.py` is clean; the flows below were run on the base commit and on the candidate. No shipped
  file has changed since the CP2 commit (`63fb238`). The working tree differs only in `docs/ROADMAP.md` (row 30,
  uncommitted). The nine suites and the `tools/release` tests were not re-run in this preparation.

## Functional review checklist

**What changed.** Only the Workflow's own tooling: `_checks` in `payload/scripts/workflow_forge.py` now derives one
state per check identity from its latest run, and `GATE_POLICY.md` item 5 says so. There is no UI and no change to the
`gh` query. Every flow below runs offline on recorded check data; none calls `gh` or GitHub.

### Setup

1. `S=$(mktemp -d)`: a scratch directory. Nothing is written into the product clone.
2. Base copy of the shipped scripts, read from the clone without writing to it:
   `mkdir -p "$S/base" && git -C <product clone> archive 198b82b payload/scripts | tar -x -C "$S/base"`
3. Candidate: `<product clone>/payload/scripts` (this branch, at `63fb238` or later).
4. Save the helper below as `$S/flows.py` and run it on each tree:
   `python3 -I "$S/flows.py" "$S/base/payload/scripts"` and `python3 -I "$S/flows.py" <product clone>/payload/scripts`.
   Each line prints `label state failing`. A line ending in `ORDER-DEPENDENT` is a failure.

**Test data:** none to seed. The check entries are literals in the helper.

```python
import sys
sys.path.insert(0, sys.argv[1])
import workflow_forge as f

def c(n, conc, at, wf="validate", st="COMPLETED", done=None):
    e = {"__typename": "CheckRun", "name": n, "workflowName": wf, "status": st, "conclusion": conc, "startedAt": at}
    if done:
        e["completedAt"] = done
    return e

A, B, W = "2026-10-27T11:10:00Z", "2026-10-27T11:40:00Z", "2026-10-27T12:39:00Z"
Z = "0001-01-01T00:00:00Z"
ok = {"__typename": "CheckRun", "name": "x", "workflowName": "validate", "status": "COMPLETED", "conclusion": "SUCCESS"}
flows = {
    "1": [c("tests (4)", "FAILURE", A, done=B), c("tests-result", "FAILURE", A, done=B), c("tests (4)", "SUCCESS", W), c("tests-result", "SUCCESS", W)],
    "2": [c("t", "SUCCESS", "2026-10-27T10:00:00Z", done="2026-10-27T10:10:00Z"), c("t", "FAILURE", "2026-10-27T12:00:00Z")],
    "3a": [c("t", "FAILURE", A, done=B), c("t", "", W, st="IN_PROGRESS")],
    "3b": [c("t", "SUCCESS", "2026-10-27T10:00:00Z", done="2026-10-27T10:10:00Z"), c("t", "", W, st="IN_PROGRESS")],
    "3c": [c("t", "FAILURE", A, done=B), c("t", "", Z, st="QUEUED")],
    "4": [c("x", "FAILURE", A, done=B), c("x", "SUCCESS", W, wf="release")],
    "5a": [c("x", "FAILURE", A, done=B), c("x", "SUCCESS", A, done=B)],
    "5b": [c("x", "FAILURE", A, done=B), {k: v for k, v in ok.items() if k != "startedAt"}],
    "5c": [c("x", "FAILURE", A, done=B), c("x", "SUCCESS", "not-a-time")],
    "5d": [c("x", "FAILURE", A, done=B), c("x", "SUCCESS", Z)],
    "6.1": [c("a", "SUCCESS", A)],
    "6.2": [c("a", "FAILURE", A)],
    "6.3": [c("a", "", A, st="IN_PROGRESS")],
    "6.4": [],
    "6.5": [{"context": "ci", "state": "SUCCESS"}],
    "6b": [c("t", "FAILURE", "2026-10-27T11:00:00Z", done="2026-10-27T11:50:00Z"), c("t", "SUCCESS", "2026-10-27T11:10:00Z", done="2026-10-27T11:20:00Z")],
    "6b-split": [c("t", "FAILURE", "2026-10-27T11:00:00Z", done="2026-10-27T11:05:00Z"), c("t", "SUCCESS", "2026-10-27T11:10:00Z", done="2026-10-27T11:20:00Z")],
}
for label, entries in flows.items():
    fwd, rev = f._checks(entries), f._checks(entries[::-1])
    print(label, fwd["state"], fwd["failing"], "" if fwd == rev else "ORDER-DEPENDENT")
```

### Flows and expected results

| Flow | Case | Expected (candidate) | Base (for contrast) |
| --- | --- | --- | --- |
| 1 | the issue's data: a failed run, then a green re-run of each check | `success`, none failing | `failure`, both names failing |
| 2 | a success, then a later failure | `failure`, `['t']` | same |
| 3a | a failure, then a later run still in progress | `pending`, none | `failure` |
| 3b | a success, then a later run still in progress | `pending`, none | `pending` |
| 3c | a failure, then a queued re-run with no start time yet | `failure`, `['t']` (fails closed) | same |
| 4 | one name in two workflows: a failure, then a later success in the other | `failure`, `['x']` | same |
| 5a to 5d | a repeated check whose order cannot be established: equal starts, no start, an unparseable start, the zero start | `failure`, `['x']` each | same |
| 6.1 to 6.5 | single entries: a success, a failure, in progress, no entries, a status context | `success`; `failure`, `['a']`; `pending`; `pending`; `success` | identical |
| 6b | overlapping runs of one check: a failure from 11:00 to 11:50, a success from 11:10 | `failure`, `['t']` (concurrent, the worst stands) | same |
| 6b-split | a failure from 11:00 to 11:05, then a success from 11:10 | `success`, none | `failure` |

**Flow 7, scope (in the product clone, reads only):**

- `git -C <product clone> diff 198b82b --stat -- payload scripts .claude` lists six payload files: `GATE_POLICY.md`,
  `ORCHESTRATION_PROTOCOL.md`, `workflow_forge.py`, `workflow_gate_policy_test.py`, `workflow_protocol.py`,
  `workflow_protocol_test.py`. Nothing under `scripts/` or `.claude/` changed, so the installed copy is untouched.
- `grep -n '_JSON_FIELDS = ' payload/scripts/workflow_forge.py` gives line 32, with the field list
  `number,url,state,headRefOid,reviewDecision,reviews,statusCheckRollup` unchanged.
- `git -C <product clone> diff 198b82b -- payload/scripts/workflow_gate_policy.py` prints nothing.

**Flow 8, full environment (not part of the sandboxed run):** the nine conformance suites from a staged fixture, the
`tools/release` tests with the pinned zlib-ng Python, and `tools/docs/check_docs.py`, as in `docs/RELEASING.md`
"Verification commands". This needs that interpreter and the staged fixture, so it cannot run in the sandbox.

### Known limitations (accepted, not defects)

- A non-overlapping `push` run that fails, followed by a passing `pull_request` run of the same job, reads as a re-run
  and stands as `success`. The event is not in the recorded answer (LMPR-R1-001, named in `GATE_POLICY.md` item 5).
- A queued re-run with no start time keeps a repeated failure until it starts.
- No flow exercises the live forge. The end-to-end path through `ci_green` and `no_standing_pr_objection` is covered by
  the automated test t8 only.
- `docs/ROADMAP.md` row 30 reads `Current` until acceptance.

### Findings and next steps

- Place findings in `.ai-review/ci-latest-check-run/feedback/FUNCTIONAL_REVIEW.md`, the resolved path for this item.
  Then run `/apply-functional-review`: a same-scope fix takes its bounded branch, and new or wider scope takes the broad
  branch, a `ci-latest-check-run-remediation-<n>` child item.
- Once testing is clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint to be
  `COMPLETE`, and CP1 and CP2 are. No command records acceptance of a partial round.
