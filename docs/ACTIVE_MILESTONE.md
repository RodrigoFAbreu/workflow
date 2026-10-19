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

### CP5 -- Release 2.17.0 (complete)

- `manifest.json` 2.17.0: `scripts/workflow_backlog.py` and `docs/ai-workflow/BACKLOG_FILE.md`
  added as `distribution` records (counts 78 artifacts, 52 distribution), every touched record's
  `sha256` and `size` refreshed with a rationale note, `manager` block `min_manager_version`
  `1.13.0`, the downgrade posture of D-Downgrade, no signals, no `new_work_only`, and
  `conformance.suites` written by `release.py manager-block --release-dir <scratch> --write`
  (acceptance 444, state 1191, completion-obligations 184, integration 328; the others unchanged).
- `WORKFLOW_RELEASE` is 2.17.0 in `workflow_protocol.py`, its two pinned assertions and the three
  edits of `ORCHESTRATION_PROTOCOL.md`; the protocol stays 1.5.
- `docs/release-history.md`: the 2.17.0 row (what it adds, the downgrade posture in full, what
  stays open). `docs/RELEASING.md`: the acceptance suite is 444 tests.
- `tools/release/release_test.py`: `BacklogReleaseTest` (6 tests): the records and counts, the
  release constant, the posture text, the history row, and a repository with the script
  installed from the release that runs `generate`, `next`, `accept` and `check` (and fails
  `check` after a hand edit), and one without a declaration that is unchanged.

Verification is recorded in the commit report and the implementation bundle.

## Functional review checklist

Implementation revision 6 (after functional review round 1); every checkpoint is complete and
technical approval is recorded. Priority is the round 1 re-test list under "Functional review
round 1" below (flows 4, 5, 7 and 9), then a quick pass over the rest.
The release source is `payload/` (this repository's own installation is untouched), so manual
testing runs in a **scratch repository**, never in this one.

### Setup

1. Make a scratch directory outside this repository and `git init` it (set a user name and
   email). Copy `payload/scripts/` (at least `workflow_backlog.py`) to `scratch/scripts/`, and
   create `scratch/docs/ai-workflow/WORKFLOW_CONFIG.json` containing `{}`.
2. In the repository, run `python3 -I tools/docs/check_docs.py` (expect clean) and the CP5
   release test `python3 -I tools/release/release_test.py BacklogReleaseTest` (expect 6 pass).
3. Read `payload/docs/ai-workflow/BACKLOG_FILE.md`; it is the document every refusal names.

### Test data

`scratch/docs/backlog.yaml` (the document's `starter`, then the `full` example block):

```yaml
version: 1
items:
  - id: first-item
    title: My first item
    status: next
    order: 1
  - id: second-item
    title: My second item
    status: next
    order: 2
    depends_on: [first-item]
```

### Flows and expected results

1. **Undeclared is unchanged.** With `{}` config run `python3 scripts/workflow_backlog.py status`
   and `next`. Expected: one JSON object saying no backlog is declared, exit 0, nothing written.
2. **Declare.** Config `{"backlog": {"file": "docs/backlog.yaml"}}`. Run `status`: the file
   parses, two items listed, exit 0.
3. **Generate.** `generate` creates `docs/ROADMAP.md` with the Workflow's stamp. Run `check`
   (exit 0). Hand-edit the page, `check` exits 1 with `roadmap_stale`; `generate` repairs it.
4. **Hand-written page.** Replace the page with prose, remove the stamp: `generate` refuses
   (`roadmap_not_generated`); `generate --replace` succeeds.
5. **Selection.** `next` returns `first-item` (second is blocked by its dependency). Mark
   `first-item` `in-progress`: still returned first. Add a cycle or an unknown dependency:
   `next` refuses on stderr (`error: backlog_invalid: docs/backlog.yaml:<line>: ...` then a
   `next step:` line naming `docs/ai-workflow/BACKLOG_FILE.md` and `check`), exit 2. `status`
   does not refuse: it always exits 0 and prints one JSON object with `"valid": false` and an
   `error` whose `code` is `backlog_invalid`, and no stderr.
6. **Accept.** `preflight-accept first-item` then `accept first-item` (and `accept --release
   2.17.0`): the file's `status` becomes `done` (only that line, plus `release`), the page is
   regenerated, JSON lists the paths to stage. On a forced refusal (e.g. break the page
   generator) both files are restored and the next step names the one-step recovery.
7. **Refusals.** Try a tab indent, a CRLF line, a duplicate id, a `detail` that is a symbolic
   link or outside `docs/items/`: each is refused (`next`, exit 2) as `backlog_invalid` with the
   file name and line (a duplicate id may list several located diagnostics before the single
   `next step:` line, which names `BACKLOG_FILE.md`). A protected declared path is different:
   put `WORKFLOW_STATE.json` in `docs/ai-workflow/registry/first-item-artifacts.json` as a
   declared artifact and run `preflight-accept first-item`: expected `declaration_conflict`,
   exit 2, nothing written, naming the path and the artifact stage (no line number; line
   numbers apply only to backlog parse and schema failures).
8. **Declared generator.** Add `"generator": ["python3", "tools/roadmap.py"]` using the
   document's example generator: `generate` runs it, `check` verifies without running it.
9. **Commands read (document review).** In `payload/.claude/commands/`: `milestone-plan.md`
   step 1 ("Backlog declared"), `accept-milestone.md` steps 2a, 3, 6, 7, and `satisfy-gate.md`
   step 0 describe the flows above and leave the explicit-id forms alone. Each tells the
   operator to report stderr verbatim (every diagnostic and the next step), not "two lines".
   `accept-milestone.md` offers the backlog branch only for an item with a state entry (its
   step 0 requires one); it makes no promise for an item without.
10. **Release.** `manifest.json` is 2.17.0, `WORKFLOW_RELEASE` is 2.17.0, `docs/release-history.md`
    has the 2.17.0 row with the downgrade posture.

### Known limitations and out of scope

- This repository keeps its prose `docs/ROADMAP.md` and declares no backlog.
- The managed conformance workflow does not add the `check` step for you (optional, documented).
- Two `TestCanonicalStateSerialization` live-state tests only run from an installed layout.
- Publishing the 2.17.0 release and the `workflow-manager` pin are separate pull requests.

## Functional review round 1

An independent executor ran the checklist; six findings, handled as follows.

- **Fixed (bounded):** a refused `generate` changed existing files from mode 0644 to 0600
  (atomic writes and the rollback now keep the existing mode and an untouched snapshot is not
  rewritten; regression tests cover refusal and successful writes). `backlog_invalid` refusals
  now name `docs/ai-workflow/BACKLOG_FILE.md` in the next step.
- **Documentation:** `milestone-plan.md`, `accept-milestone.md` and `satisfy-gate.md` say to
  report stderr verbatim instead of "the two stderr lines"; the unreachable no-state-entry
  backlog paragraph in `accept-milestone.md` and its promise in `BACKLOG_FILE.md` are removed
  (step 0 is unchanged); the guide's refusal description follows the real output.
- **Checklist corrections (no code change):** flows 5, 7 and 9 above (`status` exits 0 with
  JSON; the protected-path fixture and `declaration_conflict` wording; verbatim stderr).
- Measured counts are now 187 (completion-obligations) and 329 (integration); the other
  suites are unchanged.
- **Re-test:** flows 4 (modes preserved on the refusal), 5, 7 and 9.

## Next action

Test with the checklist above and put findings in
`.ai-review/backlog-file/feedback/FUNCTIONAL_REVIEW.md`. If clean, run `/accept-milestone backlog-file`;
otherwise `/apply-functional-review backlog-file`.
