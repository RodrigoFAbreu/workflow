# Active Milestone

## Milestone

**In progress.** W44: `acceptance-phase-guard` (`process`, governing version `2.2`), branch `milestone/acceptance-phase-guard`,
roadmap row 39 (RodrigoFAbreu/workflow#158, item 1). The plan is `docs/ai-workflow/ACCEPTANCE_PHASE_GUARD_PLAN.md` (revision 2,
approved by gate policy). The previous milestone, W43 `acceptance-floor-commit` (Workflow 2.29.0), is complete.

## Goal

Workflow 2.29.1 (a `fix:` patch): `complete_work_item` refuses unless the item is at `AWAITING_FUNCTIONAL_REVIEW` or
`AWAITING_USER_ACCEPTANCE` (`CompletionPhaseNotReachableError`, codes `work_item_terminal` / `phase_not_reachable`, checked after the
child and own-registry checks and before the obligations), and the acceptance stage's phase and registry check moves from before the
lock to the first statement of `satisfy_acceptance_gate`'s mutator, so a writer landing before the lock can no longer make the stage
complete from a phase it must refuse. The protocol stays 1.5; the Controller does not change.

## Checkpoints

- CP1 (the phase guard in the library and inside the lock, tests, command text and pages): implemented; verified state below.
- CP2 (release 2.29.1): implemented; verified state below.

CP1 changes: `payload/scripts/workflow_state.py` (the error class, the guard, the mutator's first statement, the CLI's outside call
removed), `payload/scripts/workflow_gate_policy_test.py` (`TestCompletionPhaseGuard`, P1 to P6; the three named existing-test edits:
the `AcceptanceRepo` fixture's phase, the two old-phase assertions, `test_s8`), `payload/.claude/commands/satisfy-gate.md`,
`payload/.claude/commands/accept-milestone.md`, `docs/exit-codes.md`, `docs/ROADMAP.md` (row 39).

CP2 changes: `manifest.json` (2.29.1: `workflow_version`, the eight changed records' `sha256`/`size` and `rationale` sentence, the
gate-policy suite count 404 to 412, the posture), `payload/scripts/workflow_protocol.py` (`WORKFLOW_RELEASE`), its test,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md` (the 2.29.1 row), `docs/exit-codes.md` ("Last checked
with"), `tools/release/release_test.py` (`AcceptancePhaseGuardReleaseTest`; the 2.29.0 class gives up the current-release pins).

## Functional review checklist

Scope: the release source `payload/scripts/workflow_state.py` and the two documents `satisfy-gate.md` and `accept-milestone.md` as they
are at the checklist's evidence commit. The change: `complete_work_item` refuses outside `AWAITING_FUNCTIONAL_REVIEW` and
`AWAITING_USER_ACCEPTANCE`, and the acceptance stage's phase check runs inside the state lock. The full rationale and the flow harness
are in `docs/ai-workflow/ACCEPTANCE_PHASE_GUARD_PLAN.md` §0 and §5; the flows below are the ones that run offline.

### Setup

- Work in a scratch directory outside the repository (`TMPDIR`). Never write inside the product clone; run Python with
  `PYTHONDONTWRITEBYTECODE=1` and `python3 -I -B` so no `__pycache__` appears in it.
- `base` is the release before this change: `git archive bee00609379aa6ab29a7f9076987bb5bfb7dd5de payload/scripts payload/.claude/commands`
  extracted into `$TMPDIR/base`. `cand` is the working tree's `payload/scripts` (read-only).
- The harness `$TMPDIR/flow.py` is the heredoc of plan §5 (copy it verbatim). It builds scratch repositories by hand; it needs no
  remote and no network.
- `gh`: the sandbox's stand-in is on `PATH`. Every flow below expects **zero** `gh` calls in its log. A flow that needs a pull request
  or any forge call is out of scope here (see Limitations).

### Test data

No data to seed. Each flow builds its own scratch repository with one item (`wi`) at the phase it names, with no registry and no
technical approval.

### Flows (offline; expected results)

Run each flow against `base` and `cand` (`$BASE`, `$CAND` as absolute paths) and compare. The numbers here are this checklist's own;
the plan's §5 numbering differs (its flow 14 is item 11 here, its flows 11 to 13 are the full-environment part below).

1. **Every phase, the library.** `python3 -I -B $TMPDIR/flow.py "$s" phases` for each `s`. Base: all 20 phases `completes -> MILESTONE_COMPLETE`.
   Cand: only `AWAITING_FUNCTIONAL_REVIEW` and `AWAITING_USER_ACCEPTANCE` complete; `MILESTONE_COMPLETE` refuses with
   `work_item_terminal`; the other 17 refuse with `phase_not_reachable`.
2. **A writer lands before the transaction (library).** `... "$s" txn IMPLEMENTING`. Base completes (the file is rewritten).
   Cand refuses `phase_not_reachable`; the file is byte-equal to the writer's and the phase on disk is still `IMPLEMENTING`.
3. **The same with `MILESTONE_COMPLETE`.** `... "$s" txn MILESTONE_COMPLETE`. Base completes again. Cand refuses `work_item_terminal`;
   bytes equal the writer's.
4. **A writer lands between the read and the lock (the flag).** `... "$s" race IMPLEMENTING`, then `race MILESTONE_COMPLETE`. Base passes
   the guard and stops later with `forge_undecidable`. Cand: `AcceptancePreflightError`, `phase_not_reachable` (`work_item_terminal`
   for the second), `state_changed: true`, `queries: 0`, and the only new file is `.ai-review/runtime/WORKFLOW_STATE.lock`.
5. **The flag, refused phases.** `IMPLEMENTING` and `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, run through `workflow_state.py
   --satisfy-acceptance wi` in the scratch repository. Both: one JSON line with `code` `phase_not_reachable`, `state_changed` false,
   exit 1, state bytes unchanged, 0 `gh` calls. Cand's `git status --ignored` additionally shows `!! .ai-review/` (the lock).
6. **The flag, already complete.** `MILESTONE_COMPLETE`. Both: `work_item_terminal`, message `wi is already MILESTONE_COMPLETE`,
   `state_changed` false, exit 1, bytes unchanged, 0 `gh` calls.
7. **The flag, the guard passes.** `AWAITING_FUNCTIONAL_REVIEW`. Both identical: `forge_undecidable`, `wi: no anchor commit ...`,
   `state_changed` false, exit 1, bytes unchanged, 0 `gh` calls (nothing past the guard changed the state).
8. **Outside a repository, and no id.** In an empty directory that is not a Git repository, `--satisfy-acceptance wi`: one JSON object
   with an `error`, exit 1, directory still empty. With no id: argparse usage error, exit 2.
9. **Mutation (the guard is what flows 1 and 2 prove).** Copy `cand` to `$TMPDIR/mut`, delete the guard in `complete_work_item`
   (the `phase == "MILESTONE_COMPLETE"` raise and the `milestone_complete_gate_reachable` raise). Flows 1 and 2 on `mut` must behave like base.
10. **Document text.** `satisfy-gate.md` no longer contains `the library does not` (base: 1, cand: 0). `accept-milestone.md` names
    `CompletionPhaseNotReachableError` (base: 0, cand: at least 1).
11. **Golden hash (offline part).** `sha256sum payload/.claude/commands/accept-milestone.md` equals the value on the
    `"accept-milestone.md":` line of `payload/scripts/workflow_integration_test.py`; `git diff bee0060 --numstat -- payload/scripts/workflow_integration_test.py`
    is `1 1`.

### Not in the sandbox set (maintainer, full environment)

- Plan §5 flows 11 to 12: the nine suites from `release.py stage-conformance`, `tools/release` under the zlib-ng interpreter,
  `check_docs.py`, `check-manager-block`. These need Python 3.12 and a fixture; they were run at the implementation stage (CP2).
- Plan §5 flow 14's `unittest` step (`TestGoldenCommandFileHashes`) from the staged fixture.

### Known behaviour changes (expected, not defects)

- A direct Python caller of `complete_work_item` or `satisfy_acceptance_gate` from a phase other than the two acceptance phases now
  gets an error where 2.29.0 completed the item. No shipped command, protocol operation or document flow relied on that.
- A phase refusal of the flag now takes the state lock and creates `.ai-review/runtime/WORKFLOW_STATE.lock` on first use.
- A refusal caused by a writer that landed in the gap reports `state_changed: true`, because the file did change, by that writer.

### Limitations (out of scope for this checklist)

- No flow reaches a real forge: `gh` is a refusing stand-in, so the real acceptance path past the guard (anchor, forge query,
  `acceptance_satisfaction` written, `MILESTONE_COMPLETE`) is not exercised. Flow 7 proves only that nothing past the guard runs first.
- Issues #158 items 2 and 3 (wording), the optional `next-action` evidence line, the gate's requirements, the Controller, and the
  protocol (stays 1.5) are out of scope.

## Next action

Functional review gate: the user performs the manual testing above and places findings in
`.ai-review/acceptance-phase-guard/feedback/FUNCTIONAL_REVIEW.md`. Then `/apply-functional-review` routes each finding, and
`/accept-milestone` accepts only once every checkpoint is `COMPLETE` (both are).
