# Workflow Roadmap

> For: anyone following where the Workflow is going. Last checked with: Workflow 2.9.1.

The full text of earlier versions is in this file's git history; the last long version is [here](https://github.com/RodrigoFAbreu/workflow/blob/f00c1c3/docs/ROADMAP.md).

## How to read this roadmap

- **What's next** is one ordered table. Work top to bottom; the first row that is not done is the current one.
- **Done** is the short history, newest first. The per-release list is in [the release history](release-history.md).
- **Later (open items)** explains the larger ideas that are not scheduled, with the direction to take when they are.
- **Open defects** lists the known problems that are not fixed yet.
- Status words: **Done** (shipped), **Next** (the item to start when the one above it is done), **Later** (agreed, not scheduled), **Waiting on ...** (blocked on something outside this repository).

## What's next

| Order | Item | What it gives you | Status |
|---|---|---|---|
| 1 | Documentation clean-up | Readable user documentation: install, update, verify guides, lifecycle overview and gate guide | Done (this repository's #8, the Manager's #16) |
| 2 | This roadmap clean-up | A roadmap a person can read | Done (#9) |
| 3 | A small Workflow fix release | Fixes `v2.6.0-003` (a version-"1" item with a state entry cannot be advanced) and makes the latest governing version ("2.2") the default for new work items instead of "2.1", and adds `/retire-legacy-work-item`: a user-only, confirmation-guarded way to close a dormant legacy work item that was already finished (RepFlow needs it). It matters because on "2.1" items implementation approval stays with a person even under 2.8's automatic gates. RepFlow's owner agreed to the default change on 2026-10-04. Once published, the release is pinned in `workflow-manager` by a Manager pin pull request. | Done: Workflow 2.9.0 (W3), published 2026-10-08, pinned by Manager v1.5.0 |
| 4 | Workflow Manager update ergonomics: `workflow-manager doctor` and `update --dry-run` | See what an update would do, and check an installation, before changing anything. The doctor and the dry run also warn about the `v2.4.0-001` hazard: `workflow-manager update` rewrites a `process` work item's protected scripts and commands in the middle of its implementation. It lives in [the Manager's roadmap](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/ROADMAP.md) | Done: Manager v1.6.0 (the Manager's #22), released 2026-10-09 |
| 5 | A small Workflow fix release, W4: Workflow 2.9.1 (RodrigoFAbreu/workflow#13) | Fixes the dead end after a review returns REVISE: the local and manual implementation reviews persist the REVISE write and never commit it, so `/apply-implementation-review`'s generation-record commit picks it up, has no `phase` change, and is refused ("must always transition phase"). The review step now commits its REVISE write alone, `/apply-implementation-review` commits a still-pending one before its first fix commit (and does nothing when an orchestrator already did), and the opposite rule is written down: an APPROVE write is never committed on its own, because it would put HEAD past the bundle's generation record and make `/satisfy-gate` and `/approve-review` refuse. The plan stage is checked too. Read-side checks stay strict; a patch, protocol unchanged at 1.2. Pinned in `workflow-manager` afterwards by a Manager pin pull request. | Done: Workflow 2.9.1 (W4, PR #15), published 2026-10-10, pinned by Manager v1.7.0 and installed here |
| 6 | Retire "2.1" for new work items (W5) | 2.9.0 made "2.2" the default for new installations, but a repository whose configuration still names "2.1" keeps starting new work items on it, and on "2.1" items implementation approval stays with a person even under automatic gates. A Workflow release stops starting new work items on "2.1" (refused or moved to "2.2", decided in its plan), while existing "2.1" items keep working to completion and nothing already governed changes. `workflow-manager doctor` warns about a configuration that still defaults to "2.1". Then a Manager pin pull request. | Next, after the Manager's Operator UX. RepFlow, the last repository defaulting to "2.1", switches to "2.2" in a follow-up to its 2.9.1 update |
| 7 | Controller C10 (in the Controller's repository) | The Controller satisfies 2.8's automatic gates by itself; until then the orchestrator runs `/satisfy-gate` | Waiting on the Controller |
| 8 | M3: the Controller's own loop drives `workflow` and `workflow-manager` | The Controller runs this repository's and the Manager's milestones itself; see [the Manager's roadmap](https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/ROADMAP.md) | Waiting on the Controller's C11 |
| 9 | Deferred: review-data simplification, multi-worktree maturity, longer-term evolution | See "Later (open items)" below | Later, unscheduled |

## Done

Newest first. Design detail lives in the shipped docs, not here.

- **Workflow 2.9.1** (published 2026-10-10, pinned by Manager v1.7.0, installed here). Milestone W4, the fix for #13. A review that returns REVISE now commits its write on its own, so the fix round after it is no longer refused, and `/apply-implementation-review` commits a still-pending write as a safety net (it does nothing when an orchestrator already did). An APPROVE write stays uncommitted for the approval commit. No new state, protocol unchanged at 1.2, and 2.9.0 reads everything 2.9.1 writes.
- **Workflow 2.9.0** (published 2026-10-08, pinned by Manager v1.5.0). Milestone W3, legacy retirement and the 2.2 default. New installations default to governing version `"2.2"` (an existing configuration is never rewritten). The user-only `/retire-legacy-work-item` closes a dormant legacy work item that was finished long ago as complete, keeping its old approval, and a retired item can never be reopened by a later pull-request report. Most of `v2.6.0-003` is fixed: a version-"1" item can now enter implementation review, the blocked message names the right next step, and the user-only `/resume-implementation` returns a 2.1 or 2.2 item with a checkpoint outstanding at the functional gate to implementation. Orchestration Protocol 1.2 lists both new commands as steps for a person, never automatic. This was the first milestone whose plan, technical approval and acceptance were all satisfied automatically by the gate policy.
- **Workflow 2.8.0** (published 2026-10-03, pinned by Manager v1.4.0, installed in this repository and in `workflow-manager`). Milestone W2, gate policy and pull-request reopening. A declarative gate policy (`GATE_POLICY.json`) lets plan approval, technical approval, functional validation and acceptance be satisfied automatically from review and test evidence. Human approval is off by default; a person turns `human_approval` on, overall or per gate, to restore the earlier behavior. Only version-"2.2" items get all three gates automatic: version-"1" items keep a human plan and technical gate, and version-"2.1" items keep a human technical gate. A red or changes-requested pull request reopens the same work item into remediation (`/apply-pr-review`). New commands: `/adopt-gate-policy`, `/satisfy-gate`. See `docs/ai-workflow/GATE_POLICY.md`. Workflow Controller 1.7.0 admits it; the Controller's C10 will consume the policy.
- **Workflow 2.7.0** (published 2026-10-02, pinned by Manager v1.3.0). Milestone W1, Orchestration Protocol v1: one versioned, machine-readable interface (`describe`, `verify`, `next-action`, `reconcile`, `record-external-result`, `resolve-artifact`) so that a controller can drive the Workflow without copying its internal rules. Also fixed two defects: withdrawn plan content could re-bind after a detour, and the review-id label in manual verdicts was not pinned. See `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`.
- **Repository setup, milestone W0** (accepted 2026-10-01). This repository became the Workflow's own home: CI, an immutable-release workflow, a protected `main` with Conventional-Commit titles, and its own Workflow installation kept apart from the release source.
- **Workflow 2.6.0** (2026-09-30). Hardening: feedback stored per work item, safer plan-review publication and recovery, approval commits that cover newly protected files, cross-worktree coordination of amendments and checkpoints, and a correct amendment diff. Mixed-release worktrees stay unsupported until every worktree has merged the update.
- **Workflow 2.5.1** (2026-09-30). Compatibility fix for checkpoint identifiers with a letter suffix (`CP4B`).
- **Workflow 2.5.0** (2026-09-30). Two-stage implementation review (a local model review, then an external one, both bound to the same implementation), and less duplicated review bookkeeping.
- **Workflow 2.4.0** (2026-09-30). First-class plan amendment during implementation (`/request-plan-amendment`).
- **Workflow 2.3.1** (2026-09-30). The frozen original baseline; later releases fixed its three known defects.

Releases 2.3.1 to 2.6.0 were first built in the `workflow-manager` repository; 2026-09-30 is the day they were published here, not when they were built. 2.7.0 onward are built and published here. A published release never changes: a wrong one is superseded by a new version.

## Later (open items)

None of these is scheduled, and none unlocks the operating model.

**Review-data simplification.** Review facts are currently spread over state, ledgers, bundles and feedback files, and some are kept in step by hand. That raises the cost of every review round and makes long-running work items heavy. Direction: continue what 2.5.0 began. Keep the current review state separate from immutable history, keep one authoritative copy of each fact and generate the other views from it, index history better, and compact long-lived work-item state. Add a persistent review file only when a concrete need cannot be met by state, ledgers, bundles, Git or a generated view.

**Multi-worktree maturity.** 2.6.0 fixed the specific amendment/checkpoint race across worktrees, but the broader concurrency model has not been reviewed as a whole. Direction: write down which invariants are repository-wide, work-item-wide, worktree-local or process-local (claims, guards, amendment ownership, journal transactions, lock ordering, crash recovery, stale leases, unrelated work items in linked worktrees), then test each scope mechanically. This also closes the documented residual that mixed-release worktrees are unsupported.

**Longer-term evolution.** Candidates, in no order: stronger transactional publication; generalized repository-wide lifecycle leases; cheaper review convergence and review-history compaction; compatibility contracts for the Controller and Workflow Manager integrations; a deprecation policy for very old governing versions; tooling to retire historical compatibility branches. Pick one only when a real operating problem asks for it.

**Small wording fixes for the next release.** For an unknown work-item id, `/retire-legacy-work-item` and `/resume-implementation` refuse with a `...WrongPhaseError` whose message is clear ("names no work item"), but their command files describe that error only as a phase problem. Say so in the command files, or add a dedicated unknown-item error.

**Functional validation evolution.** Where manual testing is weak or repetitive, strong automated evidence should be able to replace it: for the Workflow and the Manager, disposable-repository scenarios, migration, conformance and lifecycle end-to-end suites; for RepFlow, Room migration, Compose/UI, emulator end-to-end, backup/restore and navigation tests. Repository policy may still require a person's product or visual acceptance. The principle: stop for a person only when policy says the available evidence is not enough for the next decision. 2.8.0 delivered the mechanism; what remains is choosing and configuring evidence per repository.

## Open defects

All other defects are fixed: `v2.3.1-001` and `v2.3.1-003` in 2.5.0; `v2.3.1-002` in 2.4.0; `v2.4.0-001`, `v2.4.0-002` (qualified: mixed-release worktrees stay unsupported) and `v2.4.0-003` in 2.6.0; `v2.6.0-001` and `v2.6.0-002` in 2.7.0. Their write-ups are in the `workflow-manager` repository's [`docs/defects/`](https://github.com/RodrigoFAbreu/workflow-manager/tree/main/docs/defects).

| Defect | Problem | Plan |
|---|---|---|
| `v2.6.0-003` | Mostly fixed in 2.9.0 (see Done). Still open: a version-"1" work item in `PLANNING` or `AMENDING_PLAN` that has a state entry still cannot be advanced, and a version-"1" item with a registry that is not complete cannot pass the functional gate (rows 6a and 38b of `ORCHESTRATION_PROTOCOL.md`, reported as `blocked`). Details: [Defect Disposition Summary in the long version](https://github.com/RodrigoFAbreu/workflow/blob/f00c1c3/docs/ROADMAP.md#defect-disposition-summary) and the 2.9.0 plan, `docs/milestones/completed/LEGACY_RETIRE_AND_DEFAULT_VERSION_PLAN.md`. | A later release, when a version-"1" item actually needs it. |

## Principles

1. **Published releases are immutable.** Fixes ship as new releases.
2. **Work-item governance is durable.** Installing a newer Workflow never silently changes how an already-governed work item behaves.
3. **Review identity must describe exactly what was reviewed.** Approvals, bundles, ledgers and protected-path declarations stay consistent.
4. **Publish only durable truths.** Never claim a review-ready or approved state before its artifacts are valid and durable.
5. **Fail closed, recover cleanly.** Unknown or stale input stops progress with an actionable recovery instead of corrupting state.
6. **Repository-wide claims need repository-wide primitives.** A worktree-local lock cannot guarantee a repository-wide property.
7. **Legacy compatibility is explicit.** A fix for new work items is not automatically a fix for already-approved ones.
8. **One home per fact.** Keep minimal canonical state and derive views on demand; do not add files that restate what state, ledgers, bundles or Git already record.
9. **Dogfood migrations first.** Try them on a disposable repository before touching a real long-lived one.
