# Active Milestone

## Milestone

**In progress (implementing).** W31: `retention-prune` (`process`, governing version `2.2`), branch
`milestone/retention-prune`, roadmap row 27f (RodrigoFAbreu/workflow#113 item 3, #119 item 7 and #123). Plan:
`docs/ai-workflow/RETENTION_PRUNE_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.24.0 (a `feat:`
minor): the prune engine, a fourth subcommand of `scripts/workflow_retention.py`:
`prune <work-item-id>... [--apply] [--json] [--ttl-days N]`. It removes the named archives `<id>.tar.zst` past the time
to live, one checked and durable `unlink` each, never opens the index, and judges the whole run before the first unlink.
The user-only command is row 27g and is not part of this item. Base commit `4529f21`; the previous milestone, W30
`retention-command`, is accepted (Workflow 2.23.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The prune engine, its tests and the documents | **complete** |
| CP2 | Release 2.24.0 | not started |

## Verified state

- CP1 changed `payload/scripts/workflow_retention.py` (`_check_id`, `_select_destination` and `_ttl_of` extracted with
  the existing behaviour; `prune_archives`, `render_prune_text`, the `prune` subcommand),
  `payload/scripts/workflow_state_completion_obligations_test.py` (class `RetentionPrune`, ten tests: P1 to P9, with P3b
  for the lock and the re-read under it, and P9 for the extracted helpers), `docs/RETENTION.md` (the section "The prune command") and
  `docs/exit-codes.md` (the `prune` rows). `git diff 4529f21 --stat -- payload` lists the script and its test file only.
- Verified in the disposable clone of D-Staging (the two changed manifest records re-hashed, `manager.conformance.suites`
  re-measured by `release.py manager-block --commit HEAD --write`; the release source stays 2.23.0): `RetentionPrune`
  and the three earlier retention classes 72 OK; the whole obligations chunk 265 OK under the orphan wrapper; `tools/release`
  288 OK (zlib-ng); `tools/docs` 34 OK; `check_docs.py` rc 0; `check-manager-block` ok.
- Mutations m1 to m17 each fail at least one named `RetentionPrune` case in a scratch copy; the control passes.

## Next action

CP2: release 2.24.0 (`/milestone-implement retention-prune`, once).
