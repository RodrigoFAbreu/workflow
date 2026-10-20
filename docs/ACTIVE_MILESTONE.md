# Active Milestone

## Milestone

**In progress (awaiting functional review).** W14: `harness-neutral-commands` (`process`, governing version
`2.2`), branch `milestone/harness-neutral-commands`, base `ad6f863` (main after #63: the
release source is Workflow 2.17.0 and this repository's own installation is the published
2.17.0). Roadmap row 17 (RodrigoFAbreu/workflow#59). The plan is
`docs/ai-workflow/HARNESS_NEUTRAL_COMMANDS_PLAN.md`, approved by gate policy at plan
revision 5. The previous milestone, W13 (`backlog-file`, Workflow 2.17.0), is complete.

## Goal

Workflow 2.18.0 (a minor release, `feat:`): the one shared `.claude/commands/` set can be
read by a harness other than the one that created it. The command bodies and the three
documents they point to name the model "the agent"; the user-only guard is restated as the
literal-confirmation check each command carries under every harness, with the flag as an
additional layer; one shipped document, `COMMAND_FILES.md`, states the frontmatter contract
and `$ARGUMENTS`, with tests that pin it.

1. **CP1** the command-file contract and the neutral documents.
2. **CP2** neutral command bodies, the restated guards, `$ARGUMENTS` and the golden hashes.
3. **CP3** release 2.18.0.

## Current checkpoint

### CP1 -- The command-file contract and the neutral documents (complete)

- `payload/docs/ai-workflow/COMMAND_FILES.md` (new): terms, file format, the key table
  (`disable-model-invocation`, `state_writer` Honour; `review-subject` Carry; `description`,
  `argument-hint` Hint), `$ARGUMENTS` (where, substitution, empty case, rule for bodies), the
  six user-only commands, the Claude Code note (the moved enforcement history) and the
  neutrality rules.
- `MILESTONE_WORKFLOW.md`, `REVIEW_PROTOCOL.md`, the operator reference: the model is "the
  agent" (the `Claude-Session:` trailer key is untouched); the operator reference's
  user-only bullet states the restated control and points to `COMMAND_FILES.md`.
- `docs/README.md`: one row for `COMMAND_FILES.md`.
- Tests: `TestCommandFilesContractDocument` (5 tests: key coverage in both directions,
  term and placeholder wording, the user-only list equals the flagged commands, the neutrality
  pattern over the three documents, the operator-reference pointer); the six-point sentence
  pin in `workflow_protocol_test.py` follows the rename.

Verified in a fixture staged from the scratch release of plan section 5: the eight suites
that run directly pass (integration 334 tests including the 5 new ones) and the acceptance
matrix passes (450 tests, 20 skipped); `tools/docs` check and tests are clean; the
`tools/release` suite passes (198 tests) unchanged from the disposable Git clone in the
zlib-ng environment.

### CP2 -- Neutral command bodies, the restated guards, `$ARGUMENTS` and the golden hashes (complete)

- Eleven command bodies changed per the plan's hunk table: the model is "the agent"; the six
  user-only bodies state the literal-confirmation check as "the control this command carries
  itself, under every harness" with the flag as an additional layer and carry "The agent must
  never invoke" (added to `accept-milestone.md` and `retire-legacy-work-item.md`);
  `approve-review.md`'s `SlashCommand`/changelog history is replaced by a pointer to the
  harness notes in `COMMAND_FILES.md`; `apply-pr-review.md` and `prepare-review.md` gain a
  `$ARGUMENTS` sentence; the three reviewer bodies say "any capable model".
- Golden hashes: six rows re-recorded, five added. Pinned name text updated in
  `workflow_integration_test.py` and `workflow_state_test.py`.
- New tests: `TestHarnessNeutralCommandBodies` (neutrality, `Claude-Session:` still named,
  `$ARGUMENTS` gate, each user-only body's confirmation step, history moved). Plan deviation:
  the plan says sixteen files name `Claude-Session:`; there are fourteen at 2.17.0 and still
  fourteen, so the test pins fourteen.

### CP3 -- Release 2.18.0 (complete)

- `manifest.json` 2.18.0: a `distribution` record for `COMMAND_FILES.md`, `counts` 79 / 53
  distribution, every touched record's `sha256`/`size` refreshed (the eleven command files, the
  three documents, the three test files, `ORCHESTRATION_PROTOCOL.md`, `workflow_protocol.py`)
  and the command and document rationales noting this release; the `manager` block keeps
  `min_manager_version` 1.13.0 and empty `new_work_only`/`gate_default_change`, carries the
  D-Release downgrade posture, and `conformance.suites` was written by `release.py
  manager-block --write` from a staging of this content (integration 339).
- `WORKFLOW_RELEASE` 2.18.0 with its two pinned assertions and the matching
  `ORCHESTRATION_PROTOCOL.md` edits (tested-releases note, compatibility note, envelope
  example); protocol version stays 1.5.
- `docs/release-history.md`: the 2.18.0 row. `docs/RELEASING.md` states no count this release
  moves, so it is unchanged. `tools/release/release_test.py`: `HarnessNeutralReleaseTest`
  (record, counts, constant, posture, history row); the 2.17.0-pinned constant and posture
  tests of `BacklogReleaseTest` are superseded and removed.

Verified from a scratch clone holding this tree (the repository's `manifest.json` is the
committed deliverable): `release.py build` succeeds in the zlib-ng environment;
`tools/release` tests 200 pass; `check-manager-block` clean; the nine suites pass in a stock
`stage-conformance` fixture; the 2.17.0 -> 2.18.0 `update-fixture` passes (9 suites, `verify`
clean); `tools/docs` check clean and its 34 tests pass; `workflow-manager verify .` clean
against this repository's 2.17.0 installation.

## Functional review checklist

W14 changes shipped command and document text and the release metadata, not runtime code, so
the review is a reading-and-running check. Everything runs from the repository root on branch
`milestone/harness-neutral-commands` with a clean tree.

### Setup

- Python 3 with `git`; no feature flags. Release builds need the zlib-ng environment used
  during CP3 (`release.py build`); the suites below do not.
- Test data: none to seed. `payload/scripts/` suites stage their own fixtures.

### Flows

1. **Contract document.** Read `payload/docs/ai-workflow/COMMAND_FILES.md`.
   Expected: it defines the terms, the file format, a key table (`disable-model-invocation`,
   `state_writer` Honour; `review-subject` Carry; `description`, `argument-hint` Hint),
   `$ARGUMENTS` (where, substitution, empty case), exactly six user-only commands, a Claude
   Code note, and neutrality rules.
2. **Neutral wording.** `grep -rniE "claude|the model" payload/.claude/commands payload/docs/ai-workflow/{MILESTONE_WORKFLOW,REVIEW_PROTOCOL,WORKFLOW_V2_1_OPERATOR_REFERENCE}.md`.
   Expected: the model is called "the agent"; the only remaining Claude names are intended ones
   (the `Claude-Session:` trailer key, the Claude Code note and harness notes in
   `COMMAND_FILES.md`, and the reviewer bodies' "any capable model" phrasing).
3. **User-only guards.** Open `accept-milestone.md`, `approve-review.md`, `adopt-gate-policy.md`,
   `request-plan-amendment.md`, `resume-implementation.md`, `retire-legacy-work-item.md`.
   Expected: each states the literal-confirmation check as the control the command carries
   itself under every harness, names the flag as an additional layer, and says the agent must
   never invoke it.
4. **`$ARGUMENTS`.** Open `apply-pr-review.md` and `prepare-review.md`.
   Expected: each has the `$ARGUMENTS` sentence consistent with `COMMAND_FILES.md`.
5. **Suites.** From a `stage-conformance` fixture of this tree (the payload suites run staged,
   as in CP1-CP3): `workflow_integration_test.py` (340 tests), `workflow_protocol_test.py`,
   `workflow_state_test.py`; then `python3 tools/release/release_test.py`
   (needs the Git-clone environment of CP3). Expected: all pass, including
   `TestCommandFilesContractDocument` and `TestHarnessNeutralCommandBodies`.
6. **Release metadata.** `python3 tools/release/release.py check-manager-block` and
   `workflow-manager verify .`. Expected: both clean; `manifest.json` is 2.18.0 with 79 records
   (53 distribution), `min_manager_version` 1.13.0, and a row for 2.18.0 in
   `docs/release-history.md`.
7. **Installation untouched.** `git diff ad6f863..HEAD --stat -- .claude scripts .workflow-manager`.
   Expected: empty (this repository's own 2.17.0 installation is not edited by hand).

### Known limitations / out of scope

- No behaviour change to any script or state transition; only text, tests and metadata.
- This repository stays on installed 2.17.0 until 2.18.0 is published and installed through
  `workflow-manager update`; `workflow-manager` needs its own pin PR for 2.18.0.
- Harnesses other than Claude Code are not exercised; only the documented contract is.
- Plan deviation: fourteen command files name `Claude-Session:` (the plan said sixteen).

## Next action

Manual functional testing against the checklist above. Place findings at
`.ai-review/harness-neutral-commands/feedback/FUNCTIONAL_REVIEW.md`, then `/apply-functional-review`; if clean, `/accept-milestone`.
