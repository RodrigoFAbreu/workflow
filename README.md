# Workflow

> For: anyone who wants to know what the Workflow is and try it. Last checked with: Workflow 2.8.0, Workflow Manager 1.4.0.

This repository authors and publishes the releases of the Workflow: the
commands, scripts and documents that guide an AI coding agent through planned,
reviewed pieces of work. Each release is an immutable GitHub release.
The [Workflow Manager](https://github.com/RodrigoFAbreu/workflow-manager#readme)
installs it into your repositories.

## How the pieces fit

[Workflow](https://github.com/RodrigoFAbreu/workflow#readme) is the development process and its commands, installed into a repository. [Workflow Manager](https://github.com/RodrigoFAbreu/workflow-manager#readme) installs, updates and verifies the Workflow from published, digest-pinned releases. [Workflow Controller](https://github.com/RodrigoFAbreu/workflow-controller#readme) runs the Workflow's lifecycle steps automatically and stops wherever a person is needed.

## What the Workflow does

- It splits work into **work items**: a plan, then small checkpoints that are
  implemented one at a time.
- It has the plan **reviewed twice**, by a local reviewer and then an
  independent external one. The finished code gets the same two reviews on
  items using the newest Workflow version (2.2), and one external review on
  older ones.
- It puts three **approval gates** in the way: plan approval, implementation
  approval and milestone acceptance. Nothing moves on until each one is
  recorded.
- It ties every approval to the exact content that was reviewed, so a later
  change makes the approval **stale** instead of silently reusing it.
- Since 2.8, a repository chooses who passes each gate: the Workflow itself,
  from complete evidence, or a person.
- It keeps the state of every work item in one file in your repository, so you
  can always see where the work stands.

See [how it works](docs/overview.md#lifecycle) for the flowchart.

## Quick start

About five minutes. You need Git and [Claude Code](https://claude.com/claude-code); the Manager's install page lists its own requirements.

1. **Install the Workflow Manager.** Follow its
   [install page](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/install.md).
2. **Bootstrap a repository.** The repository must already exist and be a Git
   repository.

   ```bash
   workflow-manager bootstrap /path/to/your/repo
   ```

3. **Check it.**

   ```bash
   workflow-manager verify /path/to/your/repo
   ```

4. **Commit the installed files.** The first plan needs a base commit, so
   the repository needs at least one commit that holds the Workflow.

   ```bash
   git -C /path/to/your/repo add -A && git -C /path/to/your/repo commit -m "chore: install the Workflow"
   ```

5. **Describe your first milestone.** Write it in `docs/ACTIVE_MILESTONE.md`
   (and list it in `docs/ROADMAP.md`). `/milestone-plan` reads both to find
   the work to plan. The id of a new work item comes from there, not from the
   command.
6. **Start the first work item.** Open Claude Code in that repository and run:

   ```text
   /milestone-plan
   ```

   The agent writes a plan and stops for review. From there each step is a
   command, and the [overview](docs/overview.md#lifecycle) shows the route.

New work items follow the repository's default Workflow version, set in
`docs/ai-workflow/WORKFLOW_CONFIG.json`. Which gates are automatic depends on
it; read [approval gates](docs/gates.md) before your first work item. If you
want a person to approve, set that up first.

## Pages

- [docs/README.md](docs/README.md): a map of all the pages.
- [How it works](docs/overview.md): the lifecycle flowchart, step by step.
- [Approval gates](docs/gates.md): who approves, and how to change it.
- [Install and update](docs/install.md)
- [Glossary](docs/glossary.md)
- [Common problems](docs/common-problems.md)
- [Exit codes](docs/exit-codes.md)
- [Release history](docs/release-history.md)
- [Releasing](docs/RELEASING.md): for maintainers, how a release is built and
  published.
