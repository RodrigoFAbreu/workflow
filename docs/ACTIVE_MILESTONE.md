# Active Milestone

## Milestone

**Awaiting functional review.** W36: `check-time-by-value` (`process`, governing version `2.2`), branch
`milestone/check-time-by-value`, roadmap row 31 (RodrigoFAbreu/workflow#137, items 1 to 4). Plan:
`docs/ai-workflow/CHECK_TIME_BY_VALUE_PLAN.md` (revision 1, approved by gate policy). The goal, Workflow 2.25.4 (a
`fix:` patch, released after the merge of the pull request): the latest-run judge recognises the zero instant
`0001-01-01T00:00:00Z` by value, in every spelling that denotes it, so a green run can no longer supersede a failure
because of how the zero time is written. Base commit `e70ccb1`; the previous milestone, W35 `ci-latest-check-run`, is
accepted (Workflow 2.25.3).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The zero instant by value: the change, its tests, its sentence and the roadmap rows | **complete** |
| CP2 | Release 2.25.4 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `b68e2c7d`, reviewed implementation head `34881af`.
- Implementation review: `LOCAL_MODEL_IMPLEMENTATION_REVIEW` and `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`, both round 1,
  both `APPROVE`.
- Optional findings: 10 recorded (9 from plan review, 1 from implementation review). Each needs a disposition at
  acceptance (`fixed`, `dropped` with a reason, or `follow-up` with a link).

## Functional review checklist

### Setup

1. Work from the repository root, on `milestone/check-time-by-value`. The candidate is the committed `payload/` tree at
   `34881af`, unchanged since; nothing needs to be built or installed.
2. The flows import `payload/scripts/workflow_forge.py` directly with the standard library of Python 3. No network, no
   `gh`, no `claude`, `codex` or `ssh`, no forge, no `.ai-review/` state is needed.
3. Make a scratch area and a base clone of the pre-change commit (the product clone is only read):

   ```sh
   S=$(mktemp -d)
   git clone -q "$PWD" "$S/base" && git -C "$S/base" checkout -q e70ccb1
   ```

4. Save this helper as `$S/flow.py`. It builds synthetic check runs in code; there is no test data to seed:

   ```python
   import sys; sys.path.insert(0, sys.argv[1]); import workflow_forge as f
   def c(n, conc, at, done=None):
       e = {"__typename": "CheckRun", "name": n, "workflowName": "validate", "status": "COMPLETED", "conclusion": conc, "startedAt": at}
       if done: e["completedAt"] = done
       return e
   F, S, D = "2026-10-27T11:10:00Z", "2026-10-27T12:39:00Z", "2026-10-27T11:40:00Z"
   ZEROS = {"literal": "0001-01-01T00:00:00Z", "plus00": "0001-01-01T00:00:00+00:00", "millis": "0001-01-01T00:00:00.000Z",
            "offset": "0001-01-01T05:30:00+05:30", "minus00": "0001-01-01T00:00:00-00:00", "before": "0001-01-01T00:00:00+01:00"}
   for k, Z in ZEROS.items():
       n = {"literal": 1, "plus00": 2, "millis": 3, "offset": 4}.get(k, 5)
       print(f"flow {n} {k} as-FAILURE-startedAt", f._checks([c("t","FAILURE",Z,done=D), c("t","SUCCESS",S)]))
       print(f"flow {n} {k} as-FAILURE-completedAt", f._checks([c("t","FAILURE",F,done=Z), c("t","SUCCESS",S)]))
   print("flow 6 9999-SUCCESS-startedAt", f._checks([c("t","FAILURE",F,done=D), c("t","SUCCESS","9999-12-31T23:59:59-05:00")]))
   print("flow 7 real-rerun", f._checks([c("t","FAILURE",F,done=D), c("t","SUCCESS",S)]))
   print("flow 7 success-then-later-failure", f._checks([c("t","SUCCESS",F,done=D), c("t","FAILURE",S)]))
   print("flow 7 overlap", f._checks([c("t","FAILURE","2026-10-27T11:00:00Z",done="2026-10-27T11:50:00Z"), c("t","SUCCESS","2026-10-27T11:10:00Z")]))
   print("flow 7 year1-1s-startedAt", f._checks([c("t","FAILURE","0001-01-01T00:00:01Z",done=D), c("t","SUCCESS",S)]))
   print("flow 7 single-entry", f._checks([c("t","SUCCESS",F)]))
   print("flow 7 empty", f._checks([]))
   ```

5. Run it on both trees and compare. `-B` keeps bytecode out of the read-only product clone:

   ```sh
   python3 -I -B "$S/flow.py" "$S/base/payload/scripts" > "$S/base.out"
   python3 -I -B "$S/flow.py" "$PWD/payload/scripts" > "$S/cand.out"
   diff "$S/base.out" "$S/cand.out"
   ```

   The diff covers exactly flows 2 to 6 (11 lines on each side). Flows 1 and 7 print identically on both trees.

### Test flows

Each result is the `{state, failing}` dict printed by the helper. "Base" is `e70ccb1`; "candidate" is the working tree.

| Flow | What it checks | Base | Candidate |
| --- | --- | --- | --- |
| 1 | the literal `0001-01-01T00:00:00Z` as the FAILURE's `startedAt`, and as its `completedAt` (with a later SUCCESS) | `failure` | `failure` |
| 2 | `0001-01-01T00:00:00+00:00`, both positions (same two prints) | `success` (wrongly supersedes) | `failure` |
| 3 | `0001-01-01T00:00:00.000Z`, both positions | `success` | `failure` |
| 4 | `0001-01-01T05:30:00+05:30` (the zero instant in another offset), both positions | `success` | `failure` |
| 5 | `0001-01-01T00:00:00-00:00` and `0001-01-01T00:00:00+01:00` (before the zero instant), both positions | `success` | `failure` |
| 6 | `9999-12-31T23:59:59-05:00` as the SUCCESS's `startedAt` (out of the supported range) | `success` | `failure` |
| 7 | unchanged behaviour: a real re-run; a success then a later failure; an overlap; `0001-01-01T00:00:01Z` as a start; one entry; an empty list | `success`; `failure`; `failure`; `success`; `success`; `pending` | identical to base |

Flow 7 is the guard against over-rejection: the output on both trees must match line for line.

8. **Automated suites.** The nine payload suites from a staged fixture of the candidate, run as `docs/RELEASING.md`
   describes ("The nine payload suites"): expect every suite to exit `0`.

9. **Scope of the change.** From the repository root:

   ```sh
   GIT_OPTIONAL_LOCKS=0 git diff e70ccb1 --stat -- payload scripts .claude
   grep -n '_JSON_FIELDS = ' payload/scripts/workflow_forge.py
   ```

   Expect exactly six files under `payload/` (`docs/ai-workflow/GATE_POLICY.md`,
   `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `scripts/workflow_forge.py`, `scripts/workflow_gate_policy_test.py`,
   `scripts/workflow_protocol.py`, `scripts/workflow_protocol_test.py`), and no line for the installed `scripts/` or
   `.claude/`. The `grep` prints line 32, `_JSON_FIELDS = "number,url,state,headRefOid,reviewDecision,reviews,statusCheckRollup"`,
   unchanged.

10. **Roadmap rows.** `GIT_OPTIONAL_LOCKS=0 git diff e70ccb1 -- docs/ROADMAP.md` changes row 30's description and adds
    row 31 (`Current`), and nothing else. Row 30 must describe the shipped rule: the latest-started run stands only when
    every earlier run had a usable `completedAt` not later than the latest start. (Added beyond the plan's section 6, as
    review finding R2-O1 asked: flow 9 never looks at `docs/ROADMAP.md`.)

### Full environment only (not run in the sandbox)

- The `tools/release` test suite with the zlib-ng Python named in `docs/RELEASING.md`, and
  `python3 -I tools/docs/check_docs.py`. They need the full environment, not the sandbox. Expect both to pass; the
  gate policy suite runs 330 tests. Skip them and say so if the environment is not available.

### Known limitations and out of scope

- Real GitHub is not exercised. The flows call `workflow_forge._checks` on synthetic rollups. The `gh` query, its field
  list and the output shape are unchanged.
- The zero instant is defensive. GitHub emits the literal for an unfinished run, so this is not known to occur. Any
  non-zero year-1 value after the zero instant, such as `0001-01-01T00:00:01Z`, is deliberately accepted.
- Two jobs with the same `name:` in one workflow, and a `push`/`pull_request` pair, still share an identity. This is the
  named residual in `GATE_POLICY.md` item 5: the item now names the same-`name:` case, and the rule is unchanged.
- Issue #137 item 5 (the table order of the finished plan) is cosmetic and out of scope.
- No change to the gate, the state, the protocol or any command file.

### Findings

Place any finding at `.ai-review/check-time-by-value/feedback/FUNCTIONAL_REVIEW.md`. `/apply-functional-review` routes
each finding: the bounded branch for a same-scope fix, the broad branch (a `check-time-by-value-remediation-<n>` child
work item) for new or wider scope.

## Next action

Run the checklist above. Once testing is clean, `/accept-milestone` is the only acceptance command, and it needs every
checkpoint `COMPLETE` (both are) and a disposition for each of the 10 Optional findings. Row 31 of `docs/ROADMAP.md` becomes
`Done` at acceptance, not before. If a finding needs a fix, `/apply-functional-review` routes it; there is no acceptance
of a partial round.
