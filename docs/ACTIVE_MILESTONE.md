# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W17: `review-followups-3` (`process`, governing version `2.2`),
branch `milestone/review-followups-3`, roadmap row 20 (RodrigoFAbreu/workflow#71). Plan:
`docs/ai-workflow/REVIEW_FOLLOWUPS_3_PLAN.md` (revision 2, approved by gate policy). The goal is
Workflow 2.18.3, a patch release (`fix:`). The previous milestone, W16 `review-followups-2`, is
accepted (its record is in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The docstring clause and the shell-neutral suites loop | **complete** |
| CP2 | Release 2.18.3 | **complete** |

### CP1 verified state

- The `state_transaction` docstring (`payload/scripts/workflow_state.py`) now says "The original
  exception propagates unless `on_failure` raises a `BaseException` that is not an `Exception`
  (`KeyboardInterrupt`, `SystemExit`), which then replaces it, so an operator interrupt during an
  undo is never hidden; an `Exception` raised by `on_failure` is suppressed." No behaviour change.
  `workflow_state_test.py` pins the complete whitespace-normalised sentence and the absence of the
  old unqualified opening.
- The suites block in `docs/RELEASING.md` "Verification commands" is a `while read -r` loop over
  one name per line (here-string, `</dev/null`, `test -n` guard), so it runs under bash and zsh.
  `VerificationCommandsSectionTest` pins the new loop and forbids `for suite in $suites`.

### CP2 verified state

- Release 2.18.3: `manifest.json` `workflow_version`, digests, sizes, measured suite counts,
  rationales and downgrade posture; `WORKFLOW_RELEASE` and its pinned assertions;
  `ORCHESTRATION_PROTOCOL.md` mentions (the protocol stays 1.5); the release-history row; and
  `ReviewFollowups3ReleaseTest` in `tools/release/release_test.py`.

## Next action

No milestone is ready for `/milestone-plan`: roadmap row 21 is the deferred list, not a planned
milestone. Merge pull request #75, let the `Release` workflow publish Workflow 2.18.3, then pick
the next item from "Later (open items)" in `docs/ROADMAP.md`.
