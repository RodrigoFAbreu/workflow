# Active Milestone

## Milestone

W64: `payload-polish-4` (`process`, governing version `2.2`), branch `milestone/payload-polish-4`, base
`f4926525ef73cc80eef3e5951f669591f8f76d23`. Release Workflow 2.29.15, a `fix:` patch. Row 57 of `docs/ROADMAP.md`. Issues
RodrigoFAbreu/workflow#143, #119 and #113 (the still-open test pins). The plan is `docs/ai-workflow/PAYLOAD_POLISH_4_PLAN.md`
(revision 2).

## Goal

Pin the errno text and the permissions hint of the `remove_failed` refusals of the remove command's delete step. No refusal
order, command, exit code, message or working path changes.

## Outcome (complete)

- CP1 (the errno and permissions pins of the remove delete step): complete. `test_t4_...` (`RetentionErrorPathsTwo`) pins the
  exact message and next step of the open arm; `test_t12_...` (`RetentionRemove`) pins the `unlink`, in-folder `rmdir`,
  not-empty `rmdir` and last `rmdir` arms, each in its own subtest. Only
  `payload/scripts/workflow_state_completion_obligations_test.py` changes in `payload/`. Mutations m1 to m6 on scratch copies
  fail exactly the subtests the plan names; the obligations suite still counts 322.
- CP2 (release 2.29.15): complete. `WORKFLOW_RELEASE` and the protocol document's lines name 2.29.15 (protocol 1.5); the manifest
  carries the version, the posture and the four changed records' sentence, `sha256` and `size`; the history row and stamp, the
  `PayloadPolishFourReleaseTest` class (the 2.29.14 class gives up the pins a newer release owns) and roadmap row 57 (`Done`).
- Self-review: the `unlink fails` subtest of `test_t12` now carries the no-write proof (the archive's bytes, `.ai-review/w00`
  absent, the leftover minus 3 entries, the clean second run) and checks that the shown path is an entry of the folder whose
  basename is the failing third call's, as D-Pins item 2 says; the `observed_run` docstring names its three arguments. The
  manifest record of the obligations test moves with it (`sha256`, `size`); m1 still fails only that subtest.
- Implementation review: `LOCAL_MODEL_IMPLEMENTATION_REVIEW` (round 1) and `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` (round 1) both
  APPROVE the implementation bundle at `9fd9c5757ffa4c1b846f67b478526baea089b083`.
- The functional review passed all eight flows (`flow-1` to `flow-8`, recorded by the orchestrator). The technical approval is
  `CURRENT` (recorded by policy).
- The six recorded Optional findings are dispositioned in `docs/ai-workflow/registry/payload-polish-4-dispositions.json` (two
  dropped, four follow-ups to RodrigoFAbreu/workflow#221); the record is `docs/milestones/completed/payload-polish-4-findings.md`.
- Nothing is pushed, merged or published. The installation (`.claude/`, `scripts/`, `.workflow-manager/`, managed blocks,
  `.github/`) is untouched. Release 2.29.15 is published only after this work is merged to `main`.

## Next action

`payload-polish-4` is complete (accepted by policy, `policy:bae758b4f4ce`). No roadmap item is ready for `PLANNING` in this
repository: the open rows are waiting on the Controller (rows 12 and 13) or are deferred ("Later (open items)"). Run `/milestone-plan`
when the next milestone is chosen. Nothing is pushed, merged or published; the release (Workflow 2.29.15) follows the merge.
