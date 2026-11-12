# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W47: `wording-pass-plain-commands` (`process`, governing
version `2.2`), branch `milestone/wording-pass-plain-commands`, roadmap row 41 (RodrigoFAbreu/workflow#168, #165, #161 and
#152 item 1). The plan is `docs/ai-workflow/WORDING_PASS_PLAIN_COMMANDS_PLAN.md` (revision 2, approved by gate policy); an
archive copy is in `docs/milestones/completed/`.

## Goal

Workflow 2.29.3 (a `fix:` patch, released after the merge of pull request #174): one pass over the stale wording of the plain
acceptance commands. The only changed output is the detail of a library refusal (`complete_work_item`'s
`phase_not_reachable`), which no plain flag prints. The protocol stays 1.5; the Controller does not change.

## Outcome

- CP1 (the wording corrections, the library detail, the pins, the tests and row 41) and CP2 (release 2.29.3) are complete; the
  technical approval was recorded by policy.
- Functional flows 1 to 7 are recorded passed by the Controller's automated tester. The 10 recorded Optional findings are
  dispositioned (7 fixed, 2 follow-ups in RodrigoFAbreu/workflow#173, 1 dropped); see
  `docs/milestones/completed/wording-pass-plain-commands-findings.md`.

## Next action

No milestone is scheduled. Every remaining roadmap row is waiting on the Controller or is later and unscheduled (rows 12, 13,
27). The release of 2.29.3 follows the merge of pull request #174. Pick the next item, then `/milestone-plan`.
