# Release history

> For: anyone choosing or reviewing a Workflow release. Last checked with: Workflow 2.8.0, Workflow Manager 1.4.0.

One line per release. Every release is immutable. Check the
[Workflow Controller compatibility page](https://github.com/RodrigoFAbreu/workflow-controller/blob/main/docs/compatibility.md)
before updating a repository the Controller drives.

| Release | Date | What it added |
| --- | --- | --- |
| 2.8.0 | 2026-10-03 | A gate policy: the three approval gates are automatic by default and a person can be turned on for all or one. A red or changes-requested pull request reopens the same work item. Orchestration Protocol 1.1. |
| 2.7.0 | 2026-10-02 | The Orchestration Protocol, so a tool can drive the Workflow, and a fix so withdrawn plan content can never be reviewed again. |
| 2.6.0 | 2026-09-30 | Safer reviews and parallel work: per-item feedback folders, hardened plan-review binding and cross-worktree coordination. |
| 2.5.1 | 2026-09-30 | A fix to checkpoint ids ending in a letter so a plan amendment can use them. |
| 2.5.0 | 2026-09-30 | Implementation review in two stages, local then external, like plan review. |
| 2.4.0 | 2026-09-30 | Changing an approved plan during implementation (`/request-plan-amendment`). |
| 2.3.1 | 2026-09-30 | The first published release, the original Workflow baseline. |
