# Active Milestone

## Milestone

**In progress** (CP1 complete, self-review done, implementation review next). W56: `retention-docs-notes` (`process`, governing version `2.2`), branch
`milestone/retention-docs-notes`, roadmap row 49. The plan is `docs/ai-workflow/RETENTION_DOCS_NOTES_PLAN.md` (revision 2, approved by
gate policy).

## Goal

Three documentation points, no release (a `docs:` pull request, impact none): the 2.25.5 row of `docs/release-history.md` says a downgrade
also restores the `UnicodeDecodeError` tracebacks; `docs/RETENTION.md` says a refusal after the rename puts the folder back into `.ai-review/`;
the two raw reaper reports of `TEST_HARDENING_OWNER_POINTS_EVIDENCE.md` are kept next to it, with the unsaved A12/A15 mutation logs said to be
unrecoverable (RodrigoFAbreu/workflow#143 points 1 and 2, #188).

## Outcome

- CP1 (the three notes and roadmap row 49) is complete. Nothing under `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changed.
- Self-review (`ac05114`): the evidence file now names both scratch files the two JSON reports were copied from.
- At `ac05114`: the `tools/docs` tests, `check_docs.py`, the `tools/release` tests, `check-manager-block`, `check-title`
  (`impact=none`), `workflow-manager verify .` and the nine payload suites pass.

## Next action

The local implementation review of the bundle in `.ai-review/retention-docs-notes/current/`.
