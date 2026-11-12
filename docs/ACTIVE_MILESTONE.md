# Active Milestone

## Milestone

**Complete (accepted by policy).** W45: `plain-command-malformed-state` (`process`, governing version `2.2`), branch `milestone/plain-command-malformed-state`,
roadmap row 40 (RodrigoFAbreu/workflow#155, items 1 to 3). The plan is `docs/ai-workflow/PLAIN_COMMAND_MALFORMED_STATE_PLAN.md`
(revision 1, approved by gate policy). The milestone was accepted by policy from evidence; release 2.29.2 follows the merge of the pull request (#171). The previous milestone, W44 `acceptance-phase-guard` (Workflow 2.29.1), is complete.

## Goal

Workflow 2.29.2 (a `fix:` patch): the plain acceptance commands refuse a malformed state or registry with one JSON object instead of a
traceback. The shared state context (`_plain_command_state`) tells an absent state file (`StateMissing`) from one holding JSON `null`
(`StateMalformed`); `--finding-dispositions` uses it and answers every state refusal as one JSON object; the acceptance gate's
reachability blocker turns a malformed registry into `registry_unresolvable`. The protocol stays 1.5; the Controller does not change.

## Checkpoints

- CP1 (the shared state context, the dispositions flag and the blocker's catch, tests, command text and pages): complete.
- CP2 (release 2.29.2): complete.

CP1 changes: `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py` (ten new tests), `payload/.claude/commands/satisfy-gate.md`,
`docs/exit-codes.md`, `docs/ROADMAP.md` (row 40).

CP2 changes: `manifest.json` (2.29.2: `workflow_version`, the six changed records' `sha256`/`size` and `rationale` sentence, the
gate-policy suite count 412 to 422, the posture), `payload/scripts/workflow_protocol.py` (`WORKFLOW_RELEASE`), its test,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md` (the 2.29.2 row), `docs/exit-codes.md` ("Last checked
with"), `tools/release/release_test.py` (`PlainCommandMalformedStateReleaseTest`; the 2.29.1 class gives up the current-release pins).

CP2 verification (scratch clone with the CP2 tree committed, D-Staging): `release.py stage-conformance` and the nine suites, `tools/release`
tests (323, zlib-ng interpreter), `tools/docs` tests and `check_docs.py`, `release.py build`, `check-manager-block` with `--manager-releases`;
`workflow-manager verify .` in this repository.

## Next action

No incomplete milestone remains in `docs/ROADMAP.md` (row 40 was the last). Merge pull request #171, then the `Release` workflow publishes
2.29.2. Plan the next milestone with `/milestone-plan` once the roadmap names one.
