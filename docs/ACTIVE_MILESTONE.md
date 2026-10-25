# Active Milestone

## Milestone

**In progress.** W25: `command-wording` (`process`, governing version `2.2`), branch `milestone/command-wording`,
roadmap row 26b (RodrigoFAbreu/workflow#100 wording and message items, and the documents part of #105). Plan:
`docs/ai-workflow/COMMAND_WORDING_PLAN.md` (revision 3, approved by gate policy). The goal is Workflow 2.19.2, a
`fix:` patch that makes the checkpoint-start command's documents and two messages say what the code does. The
previous milestone, W24 `interleaving-pins`, is accepted (Workflow 2.19.1).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The documents, the message and their pins | **complete** |
| CP2 | Release 2.19.2 | **complete** |

## Verified state

- CP1: W1, W2, W3 (invariants page), W5 and M1/M1b (the first `AmendmentCheckpointActiveError` raise and the
  unclaimed-`IN_PROGRESS` release refusal) edited; seven new/changed pins (five M1/M1b tests in
  `workflow_state_test.py`, three in `workflow_integration_test.py`, two in `tools/release/release_test.py`), each
  shown red against its restored `bebf2d2` file and green on the candidate, recorded in
  `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md`. The production diff of `workflow_state.py` is message text, one
  optional keyword and the choice of the named checkpoint.
- Verified in a disposable clone (D-Staging): the nine suites (the state suite as the whole chunk under the orphan
  wrapper, no orphan beyond Git), the `tools/release` (275) and `tools/docs` tests, `check_docs.py`,
  `check-manager-block`; `workflow-manager verify .` is clean.

- CP2: `manifest.json` 2.19.2 (nine changed records with their digests, sizes and a `command-wording
  (workflow-2.19.2)` sentence each; posture with the D-Downgrade clauses; suite counts measured by `release.py
  manager-block --release-dir ... --write`: `workflow_state_test.py` 1244, `workflow_integration_test.py` 364),
  `WORKFLOW_RELEASE` 2.19.2 with its two pinned assertions and the protocol document edits, the 2.19.2 history row
  and the two "Last checked with" lines, and `CommandWordingReleaseTest` (the 2.19.1 class keeps what stays true of
  it). Verified in a scratch clone of the committed content: `tools/release` (277) in the zlib-ng environment,
  `tools/docs` (34), `check_docs.py`, `check-manager-block` and `release.py build --commit HEAD`; the nine suites
  from a stock `stage-conformance` fixture (see the implementation bundle's `TEST_RESULTS.md`).

## Next action

The checkpoints are complete: run `/milestone-implement command-wording` again to enter self-review and prepare
the implementation bundle.
