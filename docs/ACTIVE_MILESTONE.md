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

### CP2 -- The declaration, the command line and the artifact template (complete)

`workflow_backlog.py` gains the rest of the script:

- `load_declaration` (D-Declare: undeclared when the config lacks the key, is missing,
  unparsable or not an object; `declaration_invalid` otherwise, including symbolic-link and
  case-mismatched components), `declared_paths` (never raises), `protected_conflicts` and
  `check_declaration_conflict` (`declaration_conflict`, D-Classify).
- The command line `status`, `next`, `preflight-accept`, `accept [--release]`, `generate
  [--replace]`, `check`: one JSON object on stdout, the two-line refusal on stderr, exit 0, 1
  (`roadmap_stale`) or 2; `accept` snapshots and on any refusal restores both the backlog file
  and the page and appends the step-4 recovery to the next step.
- The declared generator (no shell, 120 s timeout, `WORKFLOW_BACKLOG_SHA256`, the four
  post-conditions, the Workflow's stamp) and `check` verifying the stamp without running user
  code; the built-in page refuses a hand-written page unless `--replace`.

`workflow_state.generate_artifacts_declarations` gains the optional `repo_root` keyword: with a
valid declaration it refuses a protected declared path and classifies the declared `file`,
`roadmap` and `docs/items/` as excluded at both stages (lazy import; an unavailable script is
`BacklogScriptUnavailableError`). Omitted or undeclared, the bytes are 2.16.0's (pinned by a
golden digest). The test harness and the generalization suite install `workflow_backlog.py`.

Tests: `BacklogDeclaration`, `BacklogCli`, `BacklogGenerator`, `BacklogAcceptAtomicity`,
`BacklogDeclarationConflict` (completion-obligations suite) and
`GeneratedDeclarationsBacklogClassificationTest` (`workflow_state_test.py`). Ran the
completion-obligations, generalization, harness and integration suites (pass) and
`workflow_state_test.py` (all pass except two `TestCanonicalStateSerialization` live-state tests,
which read `payload/docs/...` and only run from an installed layout; they fail identically
without this change).

### CP3 -- The commands, the lifecycle documents and the end-to-end tests (complete)

Release-source changes only (`payload/`):

- `milestone-plan.md` step 1 gains the version-independent "Backlog declared" bullet (`next`, a
  refusal stops with nothing written, `item.id` is the work item id, `item.detail` the
  description, the active-item advisory line, no write to the file); the explicit id forms never
  read it; step 3's `generate_artifacts_declarations` call passes `repo_root`.
- `accept-milestone.md`: the backlog pre-flight is a bullet of step 2a after the
  optional-finding dispositions pre-flight and before `requires_pr_approved` (and a head-of-2a
  paragraph for an item with no state entry); step 3 gains the declared branch (`accept`, the
  one-step recovery after a refusal); step 6 stages the printed paths; step 7 runs `next`.
- `satisfy-gate.md`: step 0 runs the pre-flight before the first step stores anything, and the
  acceptance stage states the policy-path recovery (step 4, then 5 and 6, trailer on the
  completion commit).
- `MILESTONE_WORKFLOW.md` and the operator reference: one sentence at each place that names
  `docs/ROADMAP.md`.

Tests: `TestBacklogCommandConformance` and two golden hashes (plus the v1 step-1-to-5 constant,
recomputed for the one new bullet; removing it restores the old constant) in
`workflow_integration_test.py`; `BacklogLifecycle`, `BacklogLifecycleDeclaredGenerator`,
`BacklogProtectedDeclaredPath` and `BacklogUndeclared` (29 tests) in
`workflow_acceptance_matrix_test.py`, which now installs `workflow_backlog.py`.

Verification (scratch conformance fixture staged from the working tree, nine payload suites):
all nine pass. Suite sizes now: acceptance matrix 444, state 1191, completion-obligations 176,
integration 328 (the others unchanged); `manifest.json` still records 415, 1183, 106, 317, so
`release_test.py`'s `test_real_acceptance_module_partitions_exactly` and `test_round_trip`
fail until CP5 updates the manifest (digests, sizes, the new script's record and these counts).
`tools/docs` checks pass.

### CP4 -- The shipped backlog document and the user documents (complete)

- New shipped reference `payload/docs/ai-workflow/BACKLOG_FILE.md` (the document every
  refusal names): setup, the accepted grammar and schema with the refused forms, how
  `/milestone-plan` chooses, what acceptance does and the one-step recovery after an `accept`
  refusal, the declared generator's freshness contract and stamp, the path and symbolic-link
  rules, "Items in flight at adoption" (with the approval-staling warning and the link to
  REVIEW_PROTOCOL.md's repair section), the commands, exit codes and every error code, and the
  way back to 2.16.0. It carries the marked `starter`, `full` and `generator` example blocks.
- Repository pages (not installed): `docs/README.md` row, `docs/install.md` pointer,
  `docs/gates.md` section, `docs/glossary.md` (backlog file, generated roadmap),
  `docs/common-problems.md` (each code, the reused id, the hand-edited page, "Acceptance
  stopped at the backlog") and `docs/exit-codes.md` (0, 1, 2); their headers name 2.17.0.

Tests: `BacklogDocument` (8, completion-obligations suite): the starter and the complete example
parse and validate with the parser; every error code of the script appears in the document; the
script's next-step text names the document's path; the cited repair section exists; the example
generator satisfies the freshness contract in a scratch repository (`check` passes, then fails
after a hand edit of the page and after an edit of the file); the downgrade "keep the backlog"
procedure (copy to `tools/`, the copy's `generate`, `check`) exits 0. The test caught one defect in
the draft (a three-space trailing comment in the example), fixed in the document.

Verification: completion-obligations suite 184 tests pass; `tools/docs/check_docs.py` clean and
its 34 tests pass. The suite count changed from 176 to 184, so CP5 records it in the manifest.

## Next action

Invoke `/milestone-implement backlog-file` again for CP5.
