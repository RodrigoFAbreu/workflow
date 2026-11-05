# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W40: `acceptance-plain-command` (`process`, governing
version `2.2`), branch `milestone/acceptance-plain-command`, roadmap row 35 (RodrigoFAbreu/workflow#148). The plan is
`docs/ai-workflow/ACCEPTANCE_PLAIN_COMMAND_PLAN.md` (revision 4, approved by gate policy); an archive copy is in
`docs/milestones/completed/`. The previous milestone, W39 `unclassified-path-message` (Workflow 2.25.7), is complete.

## Goal

Workflow 2.26.0 (a `feat:` minor, released after the merge of pull request #156): `python3 scripts/workflow_state.py
--acceptance-gate <id>` prints, read-only and without a lock, a write or a GitHub call, the acceptance gate's evaluation,
the missing dispositions by key with the skeleton, the blockers and one `ready` answer; `/satisfy-gate acceptance` names
it first and keeps the Python description as the specification. Gate semantics do not change. The completion as one plain
command is row 36.

## Outcome

- CP1 (the report flag, its tests, the command text and the page) and CP2 (release 2.26.0) are complete; the technical
  approval was recorded by policy.
- Functional flows 1 to 7 (F1 to F7) are recorded passed. The 22 recorded Optional findings are dispositioned (9 follow-ups
  in RodrigoFAbreu/workflow#155, 2 fixed, 11 dropped); see
  `docs/milestones/completed/acceptance-plain-command-findings.md`.

## Next action

The next roadmap item is row 36, the acceptance completion as one plain command. Pick it, then `/milestone-plan`. The
release of 2.26.0 follows the merge of pull request #156.
