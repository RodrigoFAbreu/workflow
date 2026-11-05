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

## Next action

`/milestone-implement acceptance-plain-command` again: all checkpoints are complete; it enters self-review and prepares the implementation review bundle.
