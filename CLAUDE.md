# CLAUDE.md

Guidance for Claude Code (claude.ai/code) in this repository.

## Semi-autonomous workflow gates

Work follows the state machine in `docs/ai-workflow/MILESTONE_WORKFLOW.md`.
Claude works autonomously between gates but must stop and wait at every hard
gate that document names -- see its "Hard gates summary" for the current
count and list, which changes as the workflow evolves; do not hardcode a
count here.

Use the commands in `.claude/commands/` to drive each state. Do not skip a
gate because the diff looks small.

## Workflow documents

- Milestone state machine: `docs/ai-workflow/MILESTONE_WORKFLOW.md`
- Two-stage plan review: `docs/ai-workflow/PLAN_REVIEW_WORKFLOW.md`
- Bundle mechanics and feedback format: `docs/ai-workflow/REVIEW_PROTOCOL.md`
- Phase/command reference: `docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`
- Current work-item state: `docs/ai-workflow/WORKFLOW_STATE.json` (ground
  truth -- never inferred from plan text)
- Active work item narrative: `docs/ACTIVE_MILESTONE.md`

## Git restrictions

- Commits are normally prohibited. Only commit when a workflow command
  explicitly authorizes it after verification gates pass.
- Never push, merge, rebase, force-push, or open a pull request.
- Don't touch unrelated working-tree changes.

<!--
Sections above this marker are managed by workflow-manager and are replaced
on update. Add repository-specific guidance below it; it is never touched.
-->

<!-- workflow-manager:end -->

# The `workflow` repository

This repository is the AI development Workflow itself: the product that
`workflow-manager` installs into other repositories. It is not
`workflow-manager`, and it is not RepFlow.

## Two copies of the Workflow live here

- **The release source** (`manifest.json`, `payload/`, `fixtures/`,
  `templates/`): what a release of this repository ships. Changing these
  files is the work of a Workflow milestone, through its approved plan.
- **This repository's own installation** (`.claude/`, `scripts/`,
  `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks of
  `CLAUDE.md` and `.gitignore`, and `.github/workflows/workflow-conformance.yml`):
  the published Workflow 2.8.0, installed by `workflow-manager bootstrap`, which
  runs this repository's own milestones. Never edit it by hand. Change it only
  through `workflow-manager update`, and `workflow-manager verify .` must stay
  clean.

Never mix the two: a fix to the Workflow goes into the release source, and
reaches this repository's installation only once a new release is published
and installed.

## Releases

- Every published release is immutable: the tags `v2.3.1` to `v2.8.0` and
  their GitHub release assets (`workflow-<version>.tar.gz`, its manifest,
  `SHA256SUMS`). Never move a tag or replace an asset. A wrong release is
  superseded by a new version.
- `workflow-manager` installs a release only once its pin is added there, in
  a small `workflow-manager` pull request.
- The roadmap is `docs/ROADMAP.md`.
- `main` is protected: squash merges only, Conventional-Commit pull-request
  titles whose impact agrees with the manifest's version change, and the
  required checks `aggregate`, `Conventional Commit title` and
  `workflow-conformance`, up to date with `main`. A release is published by
  the `Release` workflow when `main`'s manifest names an unpublished
  version. How releases, CI and the settings work: `docs/RELEASING.md`.

## Hard rules

- `~/Workspace/repflow-android` is read-only.
- Never modify a published release's bytes or semantics. A defect in a
  published release is written up and fixed in the next release.
