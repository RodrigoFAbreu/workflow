# Active Milestone

## Milestone

**Complete (accepted by policy).** W30: `retention-command` (`process`, governing version `2.2`), branch
`milestone/retention-command`, roadmap row 27e (RodrigoFAbreu/workflow#84, the user-gated step of the retention tool).
Plan: `docs/ai-workflow/RETENTION_COMMAND_PLAN.md` (revision 3, approved by gate policy). The goal, Workflow 2.23.0 (a
`feat:` minor, released after the merge of the pull request): one user-only command file,
`/archive-finished-item <work-item-id>`. It previews the dry runs of `scripts/workflow_retention.py archive` and
`remove` for ONE finished item, and runs `archive --apply` and then `remove --apply` only after the user's own
current-turn message carries the sentence `Archive and remove the review folder of <id>.`. The engines are unchanged;
the command packs, verifies, renames and deletes nothing itself. Base commit `e6c12be`; the previous milestone,
W29 `retention-removal`, is accepted (Workflow 2.22.0). The prune (roadmap row 27f) is not part of this item.

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The command, its tests and the documents | **complete** |
| CP2 | Release 2.23.0 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED` (local and manual external reviews
  APPROVE). Technical approval at the review content `6379ce13`.
- Implementation revision 2 is the post-review-fix tree: round 1's findings were fixed in `858f3f3`. The 20 recorded
  Optional findings are dispositioned in `docs/ai-workflow/registry/retention-command-dispositions.json` (fixed,
  dropped with reasons, and four follow-ups on RodrigoFAbreu/workflow#123).
- Automated verification, run at `858f3f3`: the nine suites from a stock `release.py stage-conformance --commit HEAD`
  fixture (453 / 344 / 1244 / 316 / 142 / 255 / 370 / 283 / 27, all OK; the 370 include
  `TestArchiveFinishedItemCommand`, T1 to T8); `tools/release` 288 OK (zlib-ng); `tools/docs` 34 OK; `check_docs.py`
  rc 0; `check-manager-block` ok; `release.py build` ok; `workflow-manager verify .` clean at 2.22.0.
- Functional review: round 1 at `884d05e`, an independent Claude executor (`claude-sonnet-5-5`), flows F1 to F9 (with
  F7b and F7c) passed in scratch repositories; the evidence is recorded in `WORKFLOW_STATE.json`.
- Acceptance: pull request #124 at `884d05e`, checks green, read by the Workflow's own `gh` query.

## Next action

W30 `retention-command` is accepted by policy (Workflow 2.23.0 is released after the merge of the pull request). The
next incomplete roadmap row is 27f, the user-only prune of archives past the TTL: run `/milestone-plan` when it is
ready for `PLANNING`.
