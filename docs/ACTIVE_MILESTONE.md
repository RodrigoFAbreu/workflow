# Active Milestone

## Milestone

**In progress (implementing).** W14: `harness-neutral-commands` (`process`, governing version
`2.2`), branch `milestone/harness-neutral-commands`, base `ad6f863` (main after #63: the
release source is Workflow 2.17.0 and this repository's own installation is the published
2.17.0). Roadmap row 17 (RodrigoFAbreu/workflow#59). The plan is
`docs/ai-workflow/HARNESS_NEUTRAL_COMMANDS_PLAN.md`, approved by gate policy at plan
revision 5. The previous milestone, W13 (`backlog-file`, Workflow 2.17.0), is complete.

## Goal

Workflow 2.18.0 (a minor release, `feat:`): the one shared `.claude/commands/` set can be
read by a harness other than the one that created it. The command bodies and the three
documents they point to name the model "the agent"; the user-only guard is restated as the
literal-confirmation check each command carries under every harness, with the flag as an
additional layer; one shipped document, `COMMAND_FILES.md`, states the frontmatter contract
and `$ARGUMENTS`, with tests that pin it.

1. **CP1** the command-file contract and the neutral documents.
2. **CP2** neutral command bodies, the restated guards, `$ARGUMENTS` and the golden hashes.
3. **CP3** release 2.18.0.

## Current checkpoint

### CP1 -- The command-file contract and the neutral documents (complete)

- `payload/docs/ai-workflow/COMMAND_FILES.md` (new): terms, file format, the key table
  (`disable-model-invocation`, `state_writer` Honour; `review-subject` Carry; `description`,
  `argument-hint` Hint), `$ARGUMENTS` (where, substitution, empty case, rule for bodies), the
  six user-only commands, the Claude Code note (the moved enforcement history) and the
  neutrality rules.
- `MILESTONE_WORKFLOW.md`, `REVIEW_PROTOCOL.md`, the operator reference: the model is "the
  agent" (the `Claude-Session:` trailer key is untouched); the operator reference's
  user-only bullet states the restated control and points to `COMMAND_FILES.md`.
- `docs/README.md`: one row for `COMMAND_FILES.md`.
- Tests: `TestCommandFilesContractDocument` (5 tests: key coverage in both directions,
  term and placeholder wording, the user-only list equals the flagged commands, the neutrality
  pattern over the three documents, the operator-reference pointer); the six-point sentence
  pin in `workflow_protocol_test.py` follows the rename.

Verified in a fixture staged from the scratch release of plan section 5: the eight suites
that run directly pass (integration 334 tests including the 5 new ones) and the acceptance
matrix passes (450 tests, 20 skipped); `tools/docs` check and tests are clean; the
`tools/release` suite passes (198 tests) unchanged from the disposable Git clone in the
zlib-ng environment.

### CP2 -- Neutral command bodies, the restated guards, `$ARGUMENTS` and the golden hashes (pending)

### CP3 -- Release 2.18.0 (pending)

## Next action

Run `/milestone-implement harness-neutral-commands` again for CP2.
