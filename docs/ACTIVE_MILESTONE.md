# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W20: `takeover-fence` (`process`, governing version `2.2`), branch
`milestone/takeover-fence`, roadmap row 23 (RodrigoFAbreu/workflow#82). Plan:
`docs/ai-workflow/TAKEOVER_FENCE_PLAN.md` (revision 1, approved by gate policy). The goal is Workflow
2.18.5, a patch release (`fix:`): a takeover's guard (`step="takeover"`) is not the owner's to reclaim,
in both the claim guard and the plan-approval journal guard. The previous milestone, W18
`review-followups-4`, is accepted (its record is in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | A takeover's guard is not the owner's to reclaim | **complete** |
| CP2 | Release 2.18.5 | **complete** |

## Verified state

- A takeover's guard (`step="takeover"`) is refused to its own owner token with its own message, in
  both `_acquire_guard_locked` and `_acquire_plan_approval_guard_locked`; a leftover takeover guard
  is cleared only by re-running the takeover. Release 2.18.5 bookkeeping is in `manifest.json`,
  `docs/release-history.md` and `tools/release/release_test.py`.
- Functional review: six flows (`w20-f1` to `w20-f6`) passed at the approved content, recorded as
  orchestrator evidence; the acceptance record is the work item's `acceptance_satisfaction`.
- Optional findings: seven recorded, all dispositioned (five follow-ups on
  RodrigoFAbreu/workflow#85, two dropped); see `docs/milestones/completed/takeover-fence-findings.md`.

## Next action

Merge pull request #86, let the `Release` workflow publish Workflow 2.18.5, then plan roadmap row 24
(W19, `/milestone-plan`), which resumes after row 23 with a fresh, simpler design.
