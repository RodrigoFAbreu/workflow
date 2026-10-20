# Active Milestone

## Milestone

**Complete.** W14: `harness-neutral-commands` (`process`, governing version `2.2`), branch
`milestone/harness-neutral-commands`, roadmap row 17 (RodrigoFAbreu/workflow#59). Accepted by
gate policy; the release (Workflow 2.18.0) follows the merge of pull request #65. The plan is
archived at `docs/milestones/completed/HARNESS_NEUTRAL_COMMANDS_PLAN.md` and the Optional
findings with their dispositions are in
`docs/milestones/completed/harness-neutral-commands-findings.md`.

## Outcome

Workflow 2.18.0 (a minor release, `feat:`): the command bodies and the three documents they
point to name the model "the agent"; the six user-only guards are restated as the
literal-confirmation check each command carries under every harness, with the flag as an
additional layer; `COMMAND_FILES.md` states the frontmatter contract and `$ARGUMENTS`, with
tests that pin it. All three checkpoints (CP1 to CP3) are complete, the seven functional
flows passed in round 2, and seven Optional findings are follow-ups in
RodrigoFAbreu/workflow#64.

## Next action

No item is ready: the only open roadmap row (18) is "Later, unscheduled". Merge pull request
#65, publish 2.18.0, then pin it through `workflow-manager`. Start the next milestone with
`/milestone-plan` once one is scheduled.
