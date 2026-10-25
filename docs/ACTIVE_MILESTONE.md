# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W24: `interleaving-pins` (`process`, governing version `2.2`), branch
`milestone/interleaving-pins`, roadmap row 26a (RodrigoFAbreu/workflow#97 items 4 and 5 and the two pins of
#100). Plan: `docs/ai-workflow/INTERLEAVING_PINS_PLAN.md` (revision 2, approved by gate policy). The goal is
Workflow 2.19.1, a `fix:` patch that adds four pins to the shipped test suites and changes no behaviour. The
previous milestone, W23 `checkpoint-start-command`, is accepted (Workflow 2.19.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The four pins and their evidence | **complete** |
| CP2 | Release 2.19.1 | **complete** |

## Verified state

- CP1: seven new tests in `payload/scripts/workflow_state_test.py` (`test_p1_*`, four `test_p2_*`,
  `test_the_journal_refusal_names_no_release_command`, `test_p4_*`) and the worker mode `crash_at_unlink`; each is
  shown red against its own mutant (M1a to M7) and green unmutated, recorded with its exact substitutions in
  `docs/ai-workflow/INTERLEAVING_PINS_EVIDENCE.md`. `payload/scripts/workflow_state.py` is unchanged.
- Verified in a disposable clone (D-Staging): the nine suites, the whole `workflow_state_test.py` chunk and the new
  tests under the orphan wrapper (no orphan beyond Git), the `tools/release` and `tools/docs` tests, `check_docs.py`
  and `check-manager-block`; `workflow-manager verify .` is clean.
- CP2: Workflow 2.19.1 (`fix:`): `WORKFLOW_RELEASE`, its two pinned assertions and the Orchestration Protocol
  lists name 2.19.1 (protocol stays 1.5); `manifest.json` moves the four changed records (digest, size, an
  `interleaving-pins (workflow-2.19.1)` sentence), the posture and the measured `workflow_state_test.py` count
  (1232 to 1239); the release-history row (closes nothing), the invariants page and a 2.19.1 release class in
  `tools/release/release_test.py`. Counts stay (80, 6).

## Next action

The next incomplete milestone in `docs/ROADMAP.md` is row 26b (wording and message accuracy of the
checkpoint-start command, W25, RodrigoFAbreu/workflow#100), ready for `PLANNING`: run `/milestone-plan`. The
Workflow 2.19.1 release follows the merge of this milestone's pull request.
