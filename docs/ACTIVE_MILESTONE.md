# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W21: `live-guard-visibility` (`process`, governing version `2.2`),
branch `milestone/live-guard-visibility`, roadmap row 24a (RodrigoFAbreu/workflow#91). Plan:
`docs/ai-workflow/LIVE_GUARD_VISIBILITY_PLAN.md` (revision 2, approved by gate policy). The goal is Workflow
2.18.6, a patch release (`fix:`): a live owner's guard is visible and not reclaimable, in both the claim guard
and the plan-approval journal guard. The previous milestone, W20 `takeover-fence`, is accepted (its record is
in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | A live holder's guard is visible and not reclaimable | **complete** |
| CP2 | Release 2.18.6 | **complete** |

## Verified state

- The holder of a guard keeps a non-blocking `flock` on the guard's inode for its window; the own-leftover
  reclaim of each guard refuses while another process holds it, and `guard_holder_is_running` answers whether
  a window is running. Release 2.18.6 bookkeeping is in `manifest.json`, `docs/release-history.md`,
  `docs/CONCURRENCY_INVARIANTS.md` and `tools/release/release_test.py`.
- Verified in a disposable clone (D-Staging): the nine suites, `check-manager-block`, `check_docs.py`, the
  `tools/docs` tests, `release.py build --commit HEAD`, and the `tools/release` tests in the zlib-ng
  environment; `workflow-manager verify .` is clean.
- Implementation review, revision 2 (`APPROVE`, `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`): the nine staged suites
  pass (3,329 tests, 40 skipped), as do the `tools/release` (267) and `tools/docs` (34) tests.
- Functional review: four flows (`w21-f1` to `w21-f4`) passed at the approved content, recorded as
  orchestrator evidence; the acceptance record is the work item's `acceptance_satisfaction`.
- Optional findings: twelve recorded, all dispositioned (seven fixed, five dropped); see
  `docs/milestones/completed/live-guard-visibility-findings.md`.

## Next action

Merge pull request #94, let the `Release` workflow publish Workflow 2.18.6, then plan roadmap row 24
(W19, `/milestone-plan`), which resumes on the live-guard liveness proof.
