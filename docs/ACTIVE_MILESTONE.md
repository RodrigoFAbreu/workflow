# Active Milestone

## Milestone

**Complete** (accepted by policy; a `docs:` change, no release). W56: `retention-docs-notes` (`process`, governing version `2.2`), branch
`milestone/retention-docs-notes`, roadmap row 49 (RodrigoFAbreu/workflow#143 points 1 and 2, #188). The plan is
`docs/ai-workflow/RETENTION_DOCS_NOTES_PLAN.md` (revision 2, approved by gate policy); an archive copy is in
`docs/milestones/completed/`.

## Goal

Three documentation points, no release: the 2.25.5 row of `docs/release-history.md` says a downgrade also restores the `UnicodeDecodeError`
tracebacks; `docs/RETENTION.md` says a refusal after the rename puts the folder back into `.ai-review/`; the two raw reaper reports of
`TEST_HARDENING_OWNER_POINTS_EVIDENCE.md` are kept next to it, with the unsaved A12/A15 mutation logs said to be unrecoverable.

## Outcome

- CP1 (the three notes and roadmap row 49) is complete. Nothing under `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changed.
- The technical approval was recorded by policy. Functional flows F1 to F4 are recorded passed by the Controller's automated tester.
- The 3 recorded Optional findings are dispositioned (1 fixed, 2 dropped as cosmetic); see
  `docs/milestones/completed/retention-docs-notes-findings.md`.

## Next action

The next incomplete milestone in `docs/ROADMAP.md` is row 27 ("Deferred: review-data simplification, longer-term evolution"), which is
deferred and trigger-driven (see "Later (open items)"). No item is ready for `PLANNING` until its trigger fires. `/milestone-plan` when
one is chosen.
