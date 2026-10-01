# Active Milestone

## Milestone

W0: `workflow-repository-setup` (`process`, governing version `2.2`),
branch `milestone/workflow-repository-setup`, base `bf51137`.

## Goal

Set this repository up for development: CI over the release source, a
release workflow that publishes an immutable release when `main`'s manifest
names an unpublished version, and `main` protection with Conventional-Commit
titles. W0 itself releases nothing.

## Current checkpoint

`CP1` (release tooling) complete: `tools/release/` builds the release
source into a package that reproduces every published release (2.3.1 to
2.6.0) byte-for-byte under the pinned `zlib-ng` 1.0.0 wheel; 62 tests green.
Next: `CP2` (CI). Evidence: the requirements ledger,
`docs/ai-workflow/requirements/workflow-repository-setup-ledger.md`.

## Current blockers

None.

## Active plan

`docs/ai-workflow/WORKFLOW_REPOSITORY_SETUP_PLAN.md` (revision 4, approved;
implementing).

## Functional review checklist

Empty. `/prepare-functional-review` writes the numbered checklist for the
active work item into this section; `/apply-functional-review` and
`/accept-milestone` read it back from here.

<!--
This file is `workflow_state.FUNCTIONAL_CHECKLIST_PATH`. It is
repository-local state: workflow-manager generates it once at bootstrap and
never overwrites it on update.
-->
