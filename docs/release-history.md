# Release history

> For: anyone choosing or reviewing a Workflow release. Last checked with: Workflow 2.9.1.

One line per release, newest first. Every release is immutable: a wrong one is
replaced by a new version, never edited. Each notes link is the release page,
which lists the package and its checksums. Check the
[Workflow Controller compatibility page](https://github.com/RodrigoFAbreu/workflow-controller/blob/main/docs/compatibility.md)
before updating a repository the Controller drives.

| Release | Date | What changed | Notes |
|---|---|---|---|
| 2.9.1 | 2026-10-09 | A fix for the dead end after an implementation review returns REVISE: the review now commits its own REVISE write, `/apply-implementation-review` commits a still-pending one, and the rule that an APPROVE write is never committed on its own is written down. Orchestration Protocol unchanged at 1.2. | [2.9.1](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.9.1) |
| 2.9.0 | 2026-10-08 | New installations default to governing version 2.2. The user-only `/retire-legacy-work-item` closes a finished legacy work item for good, and `/resume-implementation` returns an item to implementation. A version-1 item can now enter implementation review. Orchestration Protocol 1.2. | [2.9.0](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.9.0) |
| 2.8.0 | 2026-10-03 | A gate policy: approval gates are automatic by default (all three only for version-2.2 items), and a person can be turned on for all of them or one. A red or changes-requested pull request reopens the same work item. Orchestration Protocol 1.1. | [2.8.0](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.8.0) |
| 2.7.0 | 2026-10-02 | The Orchestration Protocol, so a tool can drive the Workflow, and a fix so withdrawn plan content can never be reviewed again. | [2.7.0](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.7.0) |
| 2.6.0 | 2026-09-30 | Safer reviews and parallel work: per-item feedback folders, hardened plan-review binding and cross-worktree coordination. | [2.6.0](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.6.0) |
| 2.5.1 | 2026-09-30 | A fix to checkpoint ids ending in a letter so a plan amendment can use them. | [2.5.1](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.5.1) |
| 2.5.0 | 2026-09-30 | Implementation review in two stages, local then external, like plan review. | [2.5.0](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.5.0) |
| 2.4.0 | 2026-09-30 | Changing an approved plan during implementation (`/request-plan-amendment`). | [2.4.0](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.4.0) |
| 2.3.1 | 2026-09-30 | The first published release, the original Workflow baseline. | [2.3.1](https://github.com/RodrigoFAbreu/workflow/releases/tag/v2.3.1) |

Releases 2.3.1 to 2.6.0 were authored in the workflow-manager repository before
this repository existed, and published here on 2026-09-30. The record is in
[its migration page](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/MIGRATION.md).
Releases 2.7.0 and later are built and published here.
