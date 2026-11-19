# Active Milestone

## Milestone

**Complete** (accepted by policy; a `fix:` change, Workflow patch release 2.29.10 follows the merge). W59: `retention-index-fd-close`
(`process`, governing version `2.2`), branch `milestone/retention-index-fd-close`, roadmap row 52 (RodrigoFAbreu/workflow#181 point 1
only; point 2 was declined by the owner). The plan is `docs/ai-workflow/RETENTION_INDEX_FD_CLOSE_PLAN.md` (revision 2); an archive copy
is in `docs/milestones/completed/`.

## Goal

In `payload/scripts/workflow_retention.py`, `_open_index` closes the index descriptor when its `os.fstat` raises. Before this change that
descriptor leaked in all three flows (`archive` dry run, `archive --apply`, `remove`). Every working path is unchanged; the surfaced
error for a failed stat is the existing `unreadable` refusal.

## Outcome

- CP1 (the descriptor close, its test, roadmap row 52) and CP2 (release 2.29.10) are complete.
- The technical approval was recorded by policy. Functional flows 1 to 13 are recorded passed.
- The 4 recorded Optional findings are dispositioned (2 fixed, 1 dropped, 1 follow-up, with reasons or link); see
  `docs/milestones/completed/retention-index-fd-close-findings.md`.

## Next action

The next incomplete milestone in `docs/ROADMAP.md` is row 27 ("Deferred: review-data simplification, longer-term evolution"), which is
deferred and trigger-driven (see "Later (open items)"). No item is ready for `PLANNING` until its trigger fires. `/milestone-plan` when
one is chosen.
