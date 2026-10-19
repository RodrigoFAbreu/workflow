# Active Milestone

## Milestone

**In progress.** W13: `backlog-file` (`process`, governing version `2.2`), branch
`milestone/backlog-file`, base `16b7531` (main after #58: the release source is Workflow
2.16.0 and this repository's own installation is the published 2.16.0). Roadmap row 16
(RodrigoFAbreu/workflow#48). The plan is `docs/ai-workflow/BACKLOG_FILE_PLAN.md`, approved by
gate policy at plan revision 6. The previous milestone, W12 (`conformance-sharding`,
Workflow 2.16.0), is complete.

## Goal

Workflow 2.17.0 (a minor release, `feat:`): a repository can declare a structured backlog
file in `WORKFLOW_CONFIG.json`; `/milestone-plan` with no argument takes the next ready item
from it, acceptance sets the item `done` and regenerates the roadmap page inside the
acceptance commit, and the Workflow ships the generator and a staleness check. A repository
that declares nothing behaves exactly as today. This repository keeps its prose
`docs/ROADMAP.md`.

1. **CP1** the backlog module: parser, schema, selection, edit and generator.
2. **CP2** the declaration, the command line and the artifact template.
3. **CP3** the commands, the lifecycle documents and the end-to-end tests.
4. **CP4** the shipped backlog document and the user documents.
5. **CP5** release 2.17.0: manifest, release constant, release history, downgrade posture.

## Current checkpoint

### CP1 -- The backlog module (complete)

`payload/scripts/workflow_backlog.py` (`# state_writer: false`, standard library only, no
Workflow-module import) is the library half:

- `parse_backlog` / `parse_backlog_bytes` implement D-Format rules 1 to 8 exactly and raise
  `BacklogFormatError(line, what)`; the per-item line map carries each key's line for the
  editor.
- `validate_backlog` is the schema (ids, orders, statuses, dependency graph and cycle, size,
  `detail` under `docs/items/` with the symbolic-link and exact-case rule, release) and
  collects every violation of one pass, ten shown; `parse_and_validate` wraps both and names
  the file in each message. `path_problem` is D-Declare's path rule, shared with CP2.
- `select_next` is D-Select (a ready `in-progress` item first, else the lowest ready `next`;
  `no_ready_item` otherwise; blocked `in-progress` items become warnings).
- `set_status_text` edits only the `status` (and `release`) lines and proves by re-parse that
  nothing else changed; `render_roadmap` is the deterministic built-in page.
- `BacklogError(code, message, next_step)` carries the D-Messages codes.

`declared_paths` and the command line are CP2.

Tests (`workflow_state_completion_obligations_test.py`, groups `BacklogParser`,
`BacklogSchema`, `BacklogSelect`, `BacklogEdit`, `BacklogRender`, 42 tests): every accepted
form and one refusal per rule with its line number, the accepted counterparts a looser
reading would refuse, every schema rule, the selection table, the editor, the page, and a
PyYAML cross-check (skipped without PyYAML).

## Next action

Invoke `/milestone-implement backlog-file` again for CP2.
