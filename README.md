# Workflow

The AI development Workflow: the commands, scripts and documents that drive
an AI coding agent through planned, reviewed milestones with hard gates.
`workflow-manager` (https://github.com/RodrigoFAbreu/workflow-manager)
installs it into other repositories.

The current release is **2.6.0**. Every release is an immutable GitHub
release `vV` with three assets: `workflow-V.tar.gz`,
`workflow-V.manifest.json` and `SHA256SUMS`. Published releases never
change; a wrong release is superseded by a new version.

## Two copies of the Workflow

This repository holds the Workflow twice, kept apart:

- **The release source**, `manifest.json`, `payload/`, `fixtures/` and
  `templates/`: what a release ships. `manifest.json`'s `workflow_version`
  is the release's version. Changes to it are the work of a Workflow
  milestone, in a pull request that also bumps the version.
- **This repository's own installation**, `.claude/`, `scripts/`,
  `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks of
  `CLAUDE.md` and `.gitignore`, and `.github/workflows/workflow-conformance.yml`:
  a published release, installed by `workflow-manager bootstrap`, that runs
  this repository's own milestones. It changes only through
  `workflow-manager update`; CI runs `workflow-manager verify .` on every
  pull request.

A fix to the Workflow goes into the release source, and reaches this
repository's installation only once a new release is published and
installed.

## More

- `docs/RELEASING.md`: how a release happens, what CI checks, recovering
  from a failed publication, the repository settings.
- `docs/ROADMAP.md`: what comes next.
- `CLAUDE.md`: guidance for the AI agent working in this repository.
