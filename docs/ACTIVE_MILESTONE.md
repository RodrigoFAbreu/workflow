# Active Milestone

## Milestone

**Complete (accepted by policy).** W42: `acceptance-findings-floor` (`process`, governing version `2.2`), branch
`milestone/acceptance-findings-floor`, roadmap row 37 (RodrigoFAbreu/workflow#148, the rest). The plan is
`docs/ai-workflow/ACCEPTANCE_FINDINGS_FLOOR_PLAN.md` (revision 2, approved by gate policy). The previous milestone, W41
`acceptance-completion-command` (Workflow 2.27.0), is complete. The release follows the merge.

## Goal

Workflow 2.28.0 (a `feat:` minor): `python3 scripts/workflow_state.py --write-findings-record <id>` calls
`write_finding_dispositions_record` on the stored state and prints `{paths}`; it refuses an item that is not
`MILESTONE_COMPLETE`, takes no lock, writes only the record file and commits nothing. The floor commit is row 38; the
protocol stays 1.5.

## Checkpoints

- CP1 (the findings-record flag, its tests, the command texts and the pages): complete, verified state below.
- CP2 (release 2.28.0): complete, verified state below.

CP1 verified state: `TestWriteFindingsRecordCommand` (14 tests) passes; mutations m1 to m16 each fail the named test on a
scratch copy; the golden hash of `accept-milestone.md` moved (intentional); `workflow_integration_test.py` passes. The
staged-fixture run of the nine suites, `tools/docs` and `check_docs.py` is reported with the commit.

CP2 verified state (scratch clone with the changes committed): the nine suites pass from a `stage-conformance` fixture
(`workflow_gate_policy_test.py` 373); `check-manager-block --manager-releases` valid; `tools/docs` 34 tests and `check_docs.py`
clean; `tools/release` 313 tests pass (zlib-ng interpreter); `release.py build --commit HEAD` succeeds; `workflow-manager
verify .` clean (installation 2.27.0).

Self-review: the 2.28.0 release class reused the 2.27.0 class's name, so the 2.27.0 tests silently stopped running; it is now
`AcceptanceFindingsFloorReleaseTest`, and `tools/release` runs two more tests. The eight record sentences now read
`acceptance-findings-floor (workflow-2.28.0)`, as D-Release says, and the posture's closing sentence is pinned. R4 spies the
real `workflow_forge.resolve_gh`; R5 and R6 assert what D-Tests asks (the empty id, `--satisfy-acceptance`, both `true` branches,
the state-file line, the floor sentence). Six failure-only mutations of those assertions each fail on a scratch copy.

## Functional review checklist

Scope: the findings-record flag, `workflow_state.py --write-findings-record <id>` (Workflow 2.28.0). Test the release source
(`payload/`) in a scratch clone. Every flow below runs offline: no network, no real `gh`, `claude`, `codex` or `ssh`, and no
write inside the product clone. The one state seed (flow 7) is made in the scratch clone only.

### Setup

```bash
R=/home/rodrigo/Workspace/workflow            # the product clone: read only
S="$(mktemp -d)/fixture"
git clone -q --no-local "$R" "$S"             # committed HEAD; the product tree must be clean
cd "$S"
```

Run every flow as `python3 -B payload/scripts/workflow_state.py ...`. The installed copy `scripts/workflow_state.py` is
Workflow 2.27.0 and has no flag until `workflow-manager update` (flow 1).

Automated, optional, offline: `python3 -B payload/scripts/workflow_gate_policy_test.py TestWriteFindingsRecordCommand`
(expect `Ran 14 tests` and `OK`).

### Test data

- Flows 1 to 6 use the state as committed: `acceptance-findings-floor` is at `AWAITING_FUNCTIONAL_REVIEW`.
- Flows 7 and 8 need a completed item. Seed it in the scratch clone only:

  ```bash
  python3 -B -c "import json; p='docs/ai-workflow/WORKFLOW_STATE.json'; s=json.load(open(p)); s['work_items']['acceptance-findings-floor']['phase']='MILESTONE_COMPLETE'; json.dump(s, open(p,'w'), indent=2)"
  ```

### Flows

1. **The flag is in the release source, not in the installation.**
   `python3 -B payload/scripts/workflow_state.py --help` lists `--write-findings-record WORK_ITEM_ID` as the fifth option.
   `python3 -B scripts/workflow_state.py --write-findings-record acceptance-findings-floor; echo "exit=$?"` prints an argparse
   error ("one of the arguments ... is required") and `exit=2`.

2. **Refusal: the item is not complete.**
   `python3 -B payload/scripts/workflow_state.py --write-findings-record acceptance-findings-floor; echo "exit=$?"`
   Expected: `exit=1` and one JSON line with `"error": "FindingsRecordPreflightError"`, `"code": "work_item_not_complete"`,
   a message naming phase `AWAITING_FUNCTIONAL_REVIEW`, `"record_changed": false`, `"state_changed": false`. No file at
   `docs/milestones/completed/acceptance-findings-floor-findings.md`; `git status --short` shows nothing new.

3. **Refusal: unknown id.** `--write-findings-record no-such-item` gives `exit=1`, `"error": "UnknownWorkItem"`, both
   changed fields `false`, nothing written.

4. **Refusal: empty id.** `--write-findings-record ""` gives `exit=1`, `"error": "UnknownWorkItem"`, `"message": ""`, both
   changed fields `false`.

5. **Refusal: two flags.** `--write-findings-record acceptance-findings-floor --acceptance-gate acceptance-findings-floor`
   gives `exit=2` and "argument --acceptance-gate: not allowed with argument --write-findings-record". No file written.

6. **Refusal: no state file.** In an empty directory made with `git init`, run
   `python3 -B "$S/payload/scripts/workflow_state.py" --write-findings-record acceptance-findings-floor`. Expected: `exit=1`,
   `"error": "StateMissing"`, both changed fields `false`.

7. **Happy path (after the seed).** `python3 -B payload/scripts/workflow_state.py --write-findings-record acceptance-findings-floor; echo "exit=$?"`
   Expected: `exit=0` and exactly this stdout:

   ```
   {
     "paths": [
       "docs/milestones/completed/acceptance-findings-floor-findings.md"
     ]
   }
   ```

   The record has one row per optional finding in this item's ledger, and each disposition reads `none`. `git status --short`
   shows the record as untracked and the seeded state as modified. Nothing is committed: `git rev-parse HEAD` is unchanged.

8. **Re-run is byte-identical.** Run flow 7 again. Expected: the same stdout, and `sha256sum` of the record file is the same
   before and after the second run.

9. **The command texts name the flag.** `grep -n "write-findings-record" payload/.claude/commands/accept-milestone.md
   payload/.claude/commands/satisfy-gate.md`. Expected: `accept-milestone.md` names the flag in step 5a before
   `write_finding_dispositions_record`; `satisfy-gate.md` names it in the "Plain commands first" block. Neither line has
   `python3 -I`. `satisfy-gate.md` (only: `accept-milestone.md` has no floor step) says the floor
   (`commit_gate_policy_floor`) is still one Python call.
   *Functional-review round 1 (flow-9): the tester's "both texts" miss was a checklist wording error, classified expected
   behavior; no source change. Re-test: `grep -n commit_gate_policy_floor payload/.claude/commands/satisfy-gate.md`.*

10. **The public docs.** `docs/exit-codes.md` has three rows for the flag (exit 0, 1, 2), and `docs/release-history.md` has
    the 2.28.0 row. Read both; they should agree with flows 2 to 7.

### Known limitations and out of scope

- The floor commit (`commit_gate_policy_floor`, `/satisfy-gate acceptance` step 5) is still a Python call. It is roadmap row 38.
- `complete_work_item` still completes from `IMPLEMENTING` (wf#158 item 1). Not part of this milestone.
- The flag does not check dispositions. A finding with no disposition still blocks acceptance through the gate, as before.
- `/accept-milestone` and `/satisfy-gate acceptance` end to end need the real forge (`gh`). They cannot run in the sandbox
  and are not part of this offline checklist.
- The installed `scripts/` stays at Workflow 2.27.0 until `workflow-manager update`; flow 1 expects this.
- Open optional finding `F-0c27be55ecbf` (recorded by the implementation review): the 2.28.0 row of `docs/release-history.md`
  says the flag exits 0 "with the record path". The flag prints every path to stage, which can include the dispositions
  file. Disposition `none`; not changed in this round.

## Next action

W42 is accepted by policy. The next incomplete item in `docs/ROADMAP.md` is row 38 (the floor commit as one plain command,
the item after W42), ready for `PLANNING`: `/milestone-plan`.
