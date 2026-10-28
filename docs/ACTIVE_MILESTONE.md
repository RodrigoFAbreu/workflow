# Active Milestone

## Milestone

**Complete (accepted by policy).** W31: `retention-prune` (`process`, governing version `2.2`), branch
`milestone/retention-prune`, roadmap row 27f (RodrigoFAbreu/workflow#113 item 3, #119 item 7 and #123). Plan:
`docs/ai-workflow/RETENTION_PRUNE_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.24.0 (a `feat:`
minor, released after the merge of the pull request): the prune engine, a fourth subcommand of
`scripts/workflow_retention.py`: `prune <work-item-id>... [--apply] [--json] [--ttl-days N]`. It removes the named
archives `<id>.tar.zst` past the time to live, one checked and durable `unlink` each, never opens the index, and judges
the whole run before the first unlink. The user-only command is row 27g and is not part of this item. Base commit
`4529f21`; the previous milestone, W30 `retention-command`, is accepted (Workflow 2.23.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The prune engine, its tests and the documents | **complete** |
| CP2 | Release 2.24.0 | **complete** |

## Verified state

- Gates: plan approval and technical approval `CURRENT`, basis `POLICY_SATISFIED`. Technical approval at the review
  content `28af5ae6`, reviewed implementation head `766aead`.
- The 15 recorded Optional findings are dispositioned in
  `docs/ai-workflow/registry/retention-prune-dispositions.json` (fixed, dropped with reasons, and five follow-ups on
  RodrigoFAbreu/workflow#126).
- Functional review: flows 1 to 6 by the Controller's automated tester (run `controller:20261028T022558Z-3a47d895`),
  flow 7 by an independent Claude executor (`claude-sonnet-5-5`, real `gh`, scratch archive root); all seven passed. The
  evidence is recorded in `WORKFLOW_STATE.json`.
- Acceptance: pull request #127 at `32905cc`, checks green, read by the Workflow's own `gh` query.

## Next action

W31 `retention-prune` is accepted by policy (Workflow 2.24.0 is released after the merge of the pull request). The next
incomplete roadmap row is 27g, the user-only prune command: run `/milestone-plan` when it is ready for `PLANNING`.
