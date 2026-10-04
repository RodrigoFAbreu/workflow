# Workflow

> For: anyone who wants to know what the Workflow is and try it. Last checked with: Workflow 2.8.0, Workflow Manager 1.4.0.

This repository authors and publishes the releases of the Workflow: the
commands, scripts and documents that guide an AI coding agent through planned,
reviewed pieces of work. Each release is an immutable GitHub release.
The [Workflow Manager](https://github.com/RodrigoFAbreu/workflow-manager#readme)
installs it into your repositories.

## How the pieces fit

[Workflow](https://github.com/RodrigoFAbreu/workflow#readme) is the development process and its commands, installed into a repository. [Workflow Manager](https://github.com/RodrigoFAbreu/workflow-manager#readme) installs, updates and verifies the Workflow from published, digest-pinned releases. [Workflow Controller](https://github.com/RodrigoFAbreu/workflow-controller#readme) runs the Workflow's lifecycle steps automatically and stops wherever an approval gate needs a person.

## What the Workflow does

- It splits work into **work items**: a plan, then small checkpoints that are
  implemented one at a time.
- It has the plan and the finished code **reviewed twice**: once by a local
  reviewer and once by an independent external one.
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

4. **Start a first work item.** Open Claude Code in that repository and run:

   ```text
   /milestone-plan my-first-item
   ```

   The agent writes a plan and stops for review. From there each step is a
   command, and the [overview](docs/overview.md#lifecycle) shows the route.

Since 2.8.0 the approval gates are automatic by default. If you want a person
to approve, read [approval gates](docs/gates.md) before your first work item.

## Pages

- [docs/README.md](docs/README.md): a map of all the pages.
- [How it works](docs/overview.md): the lifecycle flowchart, step by step.
- [Approval gates](docs/gates.md): who approves, and how to change it.
- [Install and update](docs/install.md)
- [Glossary](docs/glossary.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Release history](docs/releases/README.md)
- [Releasing](docs/RELEASING.md): for maintainers, how a release is built and
  published.
