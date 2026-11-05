# Active Milestone

## Milestone

**In progress.** W40: `acceptance-plain-command` (`process`, governing version `2.2`), branch
`milestone/acceptance-plain-command`, roadmap row 35 (RodrigoFAbreu/workflow#148). The plan is
`docs/ai-workflow/ACCEPTANCE_PLAIN_COMMAND_PLAN.md` (revision 4, approved by gate policy). The previous milestone, W39
`unclassified-path-message` (Workflow 2.25.7), is complete.

## Goal

Workflow 2.26.0 (a `feat:` minor): `python3 scripts/workflow_state.py --acceptance-gate <id>` prints, read-only and
without a lock, a write or a GitHub call, the acceptance gate's evaluation, the missing dispositions by key with the
skeleton, the blockers and one `ready` answer; `/satisfy-gate acceptance` names it first and keeps the Python
description as the specification. Gate semantics do not change. The completion as one plain command is row 36.

## Progress

- CP1 (the report flag, its tests, the command text and the page): complete. `acceptance_gate_report` and
  `_acceptance_gate_cli` in `payload/scripts/workflow_state.py`; `TestAcceptanceGateReport` in
  `payload/scripts/workflow_gate_policy_test.py`; the plain-commands block in `payload/.claude/commands/satisfy-gate.md`;
  the rows in `docs/exit-codes.md`.
- CP2 (release 2.26.0): complete. `manifest.json` 2.26.0 (changed records, posture, `conformance.suites`), `WORKFLOW_RELEASE`, the protocol document and test, `docs/release-history.md`, `docs/exit-codes.md`, `AcceptancePlainCommandReleaseTest`. Verified in a scratch commit: the nine suites from a stock `stage-conformance` fixture, `build`, `check-manager-block`, `tools/docs`, `check_docs.py`, `tools/release` (311 tests, zlib-ng interpreter).
- Self-review: T11's stale-fact cases now cover all the plan names (`CHANGES_REQUESTED` and failed checks were missing, and the older-head case did not produce an older head); the outside-Git failure path now measures the tree; the outstanding-checkpoint detail has a test. Test-only: the suite count stays 346 and only the test file's manifest record moves. Mutations m1 to m19 were run (29 variants, all killed by their named test) and are recorded in the bundle's `TEST_RESULTS.md`.

## Next action

The functional-review gate (`AWAITING_FUNCTIONAL_REVIEW`). Test with the checklist below. Findings go to
`.ai-review/acceptance-plain-command/feedback/FUNCTIONAL_REVIEW.md`, and `/apply-functional-review` routes each one. After
clean testing, `/accept-milestone` is the only acceptance command.

## Functional review checklist

**Reviewed state:** implementation revision 1, reviewed head `80bc5e1`. No code has changed since that head; the only later
commits change `docs/ai-workflow/WORKFLOW_STATE.json`, so the automated verification recorded in the bundle
(`.ai-review/acceptance-plain-command/current/TEST_RESULTS.md`) is current.

**Target:** the release source in `payload/` on this branch. The repository's own `scripts/` and `.claude/` are the previous
installation and do not have `--acceptance-gate`; they change only through `workflow-manager update`. So every flow runs the
candidate from `payload/`.

### Setup

- Python 3 standard library only. No build or install step, no network, no `gh`, no `claude`, `codex` or `ssh`. Every flow
  below runs offline.
- Run from the repository root as written, with `python3 -B` (no bytecode writes). Do not use `python3 -I`: the script
  imports `workflow_fingerprint` from its own directory.
- Write nothing inside the clone. Scratch work goes in `SCRATCH=$(mktemp -d)`.
- Shorthand used below: `S=payload/scripts/workflow_state.py`.

### Test data

- The item's real state in `docs/ai-workflow/WORKFLOW_STATE.json`: phase `AWAITING_FUNCTIONAL_REVIEW`, checkpoints CP1 and
  CP2 `COMPLETE`, technical approval `CURRENT`, 22 optional findings without a disposition, no functional flow recorded.
  Flows F1 to F4 need nothing seeded.
- Scratch repositories for F5 (`git init` in `$SCRATCH`).

### Flows and expected results

**F1. Read the gate on the real item (read-only).**
`python3 -B $S --acceptance-gate acceptance-plain-command`

Expected: exit 0 and one JSON document. `phase` is `AWAITING_FUNCTIONAL_REVIEW`; `ready` is `false`; `query_pending` is
`true`; `dispositions.invalid` is `null`. In `gate.requirements`, `checkpoints_complete` and `technical_approval_current` are
met and `functional_flows_passed` is unmet. `blockers` holds one `requirement_unmet` (`functional_flows_passed`) and one
`disposition_missing` per key in `dispositions.missing` (22 when this was written; the key list is live). No blocker names
`pr_fact_current`, `no_standing_pr_objection` or `ci_green`: they appear only under `stored_pr_fact.unmet`. `not_checked`
has four entries.

**F2. The skeleton matches the existing command.**
```
diff <(python3 -B $S --acceptance-gate acceptance-plain-command | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["dispositions"]["skeleton"], sort_keys=True))') \
     <(python3 -B $S --finding-dispositions acceptance-plain-command | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["skeleton"], sort_keys=True))')
```
Expected: no output, exit 0.

**F3. Nothing is written.**
Before F1, record `sha256sum docs/ai-workflow/WORKFLOW_STATE.json`, `git status --porcelain --ignored`, and whether
`.ai-review/runtime/WORKFLOW_STATE.lock` exists. Run F1 and F2, then record the same three again.
Expected: all three are identical before and after.

**F4. Refusals print JSON, never a traceback.**
- a. `python3 -B $S --acceptance-gate no-such-item`: exit 1, `{"error": "UnknownWorkItem", "message": "no-such-item"}`.
- b. `python3 -B $S --acceptance-gate ""`: exit 1, `UnknownWorkItem`. An empty id is not the publication-status path.
- c. `cd "$SCRATCH" && python3 -B <clone>/$S --acceptance-gate acceptance-plain-command`, outside any Git repository:
  exit 1, `error` is `CalledProcessError`.
- d. `python3 -B $S --acceptance-gate acceptance-plain-command --finding-dispositions acceptance-plain-command`: exit 2 with
  the argparse usage message on stderr.

**F5. Missing and corrupt state (scratch).**
In `$SCRATCH`: `git init -q .`, then `python3 -B <clone>/$S --acceptance-gate x`: exit 1, `StateMissing`.
Then `mkdir -p docs/ai-workflow && printf '{' > docs/ai-workflow/WORKFLOW_STATE.json` and run it again: exit 1,
`CorruptJsonError`. Neither prints a traceback.

**F6. The command text.**
In `payload/.claude/commands/satisfy-gate.md`, the "Plain commands first" block (about line 165) names
`python3 scripts/workflow_state.py --acceptance-gate <work-item-id>` before the first `workflow_state.satisfy_acceptance_gate(`
call (about line 196). It says the report is read-only and that the completion is still the Python call. The Python step
descriptions and step 0 (`preflight-accept`) are unchanged.

**F7. Release surfaces.**
`manifest.json` has `workflow_version` `2.26.0`. `docs/exit-codes.md` has the `--acceptance-gate` rows (exit 0 and exit 2).
`docs/release-history.md` has the 2.26.0 row. The payload's `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` is still protocol `1.5`.

### Known limitations and out of scope

- Writing the acceptance (the completion transaction, the findings record, the floor) is not part of this item. It is
  roadmap row 36. The report completes nothing.
- The report makes no GitHub call. A stored pull-request fact is information only, and the stage's own query decides. A real
  `/satisfy-gate acceptance` needs `gh` and a real pull request, so no flow here runs it.
- `ready: true` needs functional flows recorded and every disposition written. Those states come from the automated fixtures
  (`TestAcceptanceGateReport`, T3 and T11), not from a manual flow.
- Unchanged: gate semantics, `/accept-milestone`, every other `workflow_state.py` flag and its output, and Orchestration
  Protocol `1.5`.
