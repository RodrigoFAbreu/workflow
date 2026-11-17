# Active Milestone

## Milestone

**Complete** (accepted by policy; a `fix:` change, Workflow patch release 2.29.8 follows the merge). W57: `command-wording-pins`
(`process`, governing version `2.2`), branch `milestone/command-wording-pins`, roadmap row 50 (RodrigoFAbreu/workflow#190 points 1 and 2,
#123 point 6). The plan is `docs/ai-workflow/COMMAND_WORDING_PINS_PLAN.md` (revision 1, approved by gate policy); an archive copy is in
`docs/milestones/completed/`.

## Goal

Wording only: shipped text says what the code does. Three command files and the two `cross_device` refusals of `workflow_retention.py`
change; nothing the code does changes. Not taken: #190 point 3 (owner decision) and #190 point 4 (not in the brief).

## Outcome

- CP1 (the wording, its pins, roadmap row 50) and CP2 (release 2.29.8) are complete.
- The technical approval was recorded by policy. Functional flows F1 to F9 are recorded passed by the orchestrator's independent
  headless executor.
- The 4 recorded Optional findings are dispositioned (all dropped, with reasons); see
  `docs/milestones/completed/command-wording-pins-findings.md`.

## Next action

The next incomplete milestone in `docs/ROADMAP.md` is row 27 ("Deferred: review-data simplification, longer-term evolution"), which is
deferred and trigger-driven (see "Later (open items)"). No item is ready for `PLANNING` until its trigger fires. `/milestone-plan` when
one is chosen.
