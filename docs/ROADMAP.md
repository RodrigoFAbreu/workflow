# Workflow Roadmap

The reusable AI development Workflow: what it is, the releases it has shipped, and what comes next.
This roadmap moved here from `workflow-manager`'s `docs/ROADMAP.md` (https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/ROADMAP.md) when the Workflow
became its own product in that repository's milestone M2 (2026-10-01). The sections keep their
historical numbers; the table below is the current order.

## At a glance

**Where things stand (2026-10-03).**
- Releases 2.3.1 to 2.7.0 are published here as immutable packages: one GitHub release per
  version, each with `workflow-<version>.tar.gz`, its manifest and `SHA256SUMS`, and one tagged
  commit per release on `main`. `main` ends at 2.7.0 (published from `d14e0a7`, pinned in
  `workflow-manager` by `workflow-manager#13`, Manager v1.3.0), the base the next release develops from.
- `workflow-manager` (v1.2.0 and later) installs a release by downloading its package and
  verifying it against a pin it ships. **Each new release needs a small `workflow-manager` pull
  request that adds its pin** (`OD-M2-2`), and the Manager tests the newest release plus the
  update path to it.
- Released bytes never change. A wrong release is superseded by a new version, never
  re-published.

**In order:**

| # | Step | Section |
|---|---|---|
| W0 | **COMPLETE** (milestone `workflow-repository-setup`, accepted 2026-10-01; the post-acceptance squash-merge and `main` read-back, `docs/RELEASING.md` "Cutover" steps 5-6, are done: workflow#3 merged as `ef714f3`, and Release run 36906626604 read back `v2.6.0` with "nothing to release") — Set this repository up for development: CI, a release workflow (build the package and `SHA256SUMS`, publish an immutable release), `main` protection with Conventional-Commit titles, `CLAUDE.md`, its own Workflow installation kept apart from the release source, and this roadmap | this table |
| W1 | **COMPLETE** (milestone `orchestration-protocol-v1`, accepted 2026-10-02; published as Workflow 2.7.0 from `d14e0a7` and pinned in `workflow-manager` by `workflow-manager#13`, Manager v1.3.0) — Workflow 2.7, the first release developed here: Orchestration Protocol v1, and the `v2.6.0-001` and `v2.6.0-002` follow-ups | [1.9](#19-post-26-controller-integration-and-workflow-orchestration-protocol-foundation) |
| W2 | **COMPLETE, pending cutover** (milestone `gate-policy-and-reopening`, accepted 2026-10-03; Workflow 2.8.0 is authored and releasable, and is published and pinned in `workflow-manager` only after acceptance and merge) — Workflow 2.8: declarative gate policy, and a red or changes-requested pull request reopening the same work item | [1.9](#19-post-26-controller-integration-and-workflow-orchestration-protocol-foundation) |
| W3 | **IN PROGRESS** (milestone `legacy-retire-and-default-version`; Workflow 2.9.0 is authored on its branch and is published and pinned in `workflow-manager` only after acceptance and merge) — Workflow 2.9: retire a dormant legacy work item (`/retire-legacy-work-item`), new installations default to governing version 2.2, and `v2.6.0-003` fixed except the two `1` planning phases. It goes first, ahead of the update tools, to unblock RepFlow | [1.9](#19-post-26-controller-integration-and-workflow-orchestration-protocol-foundation) |

The Workflow Controller consumes W1 (its C9, the Controller on the protocol) and W2 (its C10, gate
policy and automatic acceptance). The Manager-and-Workflow lane drives this repository and
`workflow-manager` together; see `workflow-manager`'s roadmap for the cross-repository order.

**Deferred** (they do not unlock the operating model): review-data simplification (4),
multi-worktree maturity (7), longer-term evolution (9).

The defect write-ups cited below (`v2.3.1-*`, `v2.4.0-*`, `v2.6.0-*`) are in `workflow-manager`'s
`docs/defects/` (https://github.com/RodrigoFAbreu/workflow-manager/tree/main/docs/defects).

---

# 0. Released versions

## Workflow 2.3.1

**Status:** Frozen historical baseline.

Important properties:

- original reusable Workflow baseline;
- preserved byte-for-byte;
- no in-place semantic repairs.

Known defects discovered against 2.3.1 have either been fixed in later authored releases or retained only as historical records.

### Closed defect: v2.3.1-001 — host-history-coupled conformance test

**Disposition:** Fixed in Workflow 2.5.0.

The affected integration test previously assumed target repositories carried RepFlow-specific historical prose in `docs/ACTIVE_MILESTONE.md`.

Workflow 2.5.0 made the check portable by skipping the host-specific assertion when the historical note is absent.

No new implementation work is planned for this defect.

### Closed defect: v2.3.1-002 — no legal plan-amendment edge

**Disposition:** Fixed in Workflow 2.4.0.

Workflow 2.3.1 had no supported transition from implementation back into plan revision/review when the approved plan itself needed to change.

Workflow 2.4.0 introduced:

- `AMENDING_PLAN`;
- `/request-plan-amendment`;
- amendment reconciliation;
- approval supersession/re-approval semantics;
- checkpoint/amendment quiescence within one worktree.

No new implementation work is planned for the missing-edge defect itself.

### Closed defect: v2.3.1-003 — first plan approval requires precommitted `WORKFLOW_STATE.json`

**Disposition:** Fixed in Workflow 2.5.0.

The plan-approval transaction previously required `WORKFLOW_STATE.json` to already exist at `HEAD` so it could reuse the tracked file mode.

Workflow 2.5.0 now falls back to mode `100644` when no previous tracked state blob exists.

The fix is regression-tested and should remain preserved.

---

## Workflow 2.4.0

**Status:** Complete authored release.

Primary feature:

- first-class approved-plan amendment during implementation.

Delivered:

- `AMENDING_PLAN`;
- `/request-plan-amendment`;
- approval supersession and reconciliation;
- amendment-specific review behavior;
- same-worktree amendment/checkpoint quiescence.

Known follow-up defects remain and are tracked below.

---

## Workflow 2.5.0

**Status:** Complete authored release.

Primary feature:

- two-stage implementation review:
  - local model implementation review;
  - manual external implementation review;
- both bound to the same implementation identity.

Additional improvements:

- review scalability/convergence improvements;
- separation of current normative review state from immutable history;
- generated/canonical review data where practical;
- reduced duplicated self-audit bookkeeping;
- multiple portability/correctness fixes inherited from earlier defect records.

Important fixes carried here:

- v2.3.1-001 host-history portability;
- v2.3.1-003 first plan-approval state-blob mode fallback;
- implementation-stage `.workflow-manager/` classification for newly generated artifact declarations.

---

## Workflow 2.5.1

**Status:** Complete authored release. It was this repository's installed baseline until 2026-09-28.

Primary purpose:

- compatibility/correctness follow-up for checkpoint identifiers and surrounding Workflow machinery.

This is the base release the 2.6.0 hardening overlay was built from. This repository stayed on 2.5.1 until the Controller's integration (1.9) admitted 2.6.0. Both repositories moved to 2.6.0 on 2026-09-28.

---

## Workflow 2.6.0

**Status:** Complete authored release — accepted as milestone `workflow-review-artifact-and-concurrency-hardening` (section 1).

Delivered:

- per-work-item/scoped review feedback storage (new work items stamped `feedback_layout: "scoped"`);
- legacy `.workflow-manager/installation.json` compatibility handling for active legacy work items (release-derived, exact-path terminal fallback; no declarations rewritten);
- plan-review publication/binding hardening (`/apply-plan-review` ordering and recovery, `plan_review_binding`, `.ai-review/<id>/plan-inputs/`);
- approval commit closure for newly introduced protected paths;
- cross-worktree amendment/checkpoint coordination (repository-global lifecycle lock plus amendment witness under the common git dir);
- correct, non-empty `AMENDMENT_DIFF.patch` anchored at the working tree;
- regression preservation for v2.3.1-001, v2.3.1-002 and v2.3.1-003.

Documented residuals / follow-ups left by the accepted implementation:

- `v2.4.0-002` is closed **qualified**: mixed-release worktrees remain unsupported until every registered worktree's branch has merged the 2.6.0 update (see the defect record's 2.6.0 disposition and `CLAUDE.md`);
- `v2.4.0-001`'s separate `workflow_manager update`-rewrites-protected-paths hazard for an active `process` work item is out of scope and belongs to milestone 5;
- `v2.6.0-001` (withdrawn plan-stage content can re-bind after a detour) was open — partially mitigated in 2.6.0, mandatory follow-up for a later Workflow release; fixed in 2.7.0.

---

## Workflow 2.7.0

**Status:** Complete authored release, the first developed in this repository — accepted as milestone W1, `orchestration-protocol-v1` (section 1.9), on 2026-10-02. It was published by the `Release` workflow from `d14e0a7` (tag `v2.7.0`) and is pinned in `workflow-manager` by `workflow-manager#13` (Manager v1.3.0).

Delivered:

- Orchestration Protocol v1: `scripts/workflow_protocol.py` (`describe`, `verify`, `next-action`, `reconcile`, `record-external-result`, `resolve-artifact`), one versioned JSON envelope with stable error codes, its schema `docs/ai-workflow/orchestration-protocol-v1.schema.json`, and the normative specification `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, whose tables are tested against the code's own;
- `next-action`'s total action catalogue over every phase and governing version, with dispositions, worker requirements and stale-decision refusal; `reconcile` recognizes same-phase progress;
- one Workflow-owned ingest for manual plan and implementation verdicts, shared by `record-external-result` and the `/record-manual-*-review` commands;
- a two-stage `REVISE` applied by its `review_content_id`, the bundle fields advisory (`/apply-plan-review`, `/apply-implementation-review`);
- `v2.6.0-001` fixed: a durable consumed plan-review history, so withdrawn, revised or amended content never re-binds;
- `v2.6.0-002` fixed: the pinned `Reviewed review_content_id:` label, read from the feedback header only, with the legacy label accepted as an alias;
- a new conformance suite, `workflow_protocol_test.py`, run by `workflow-conformance.yml` (eight suites).

Compatibility: the 2.6.0 query CLIs are unchanged. A `review_content_id` stated only after the feedback's first `## ` section now parses as absent. Workflow Controller 1.5.0 does not admit 2.7.0; do not update a Controller-driven repository until the Controller does (its C9).

Open, reported by the protocol rather than fixed: `v2.6.0-003` (see the Defect Disposition Summary).

---

## Workflow 2.8.0

**Status:** Complete authored release, developed as milestone W2, `gate-policy-and-reopening` (section 1.9, accepted 2026-10-03), pending cutover: it is published by the `Release` workflow only once the milestone is accepted and its pull request is squash-merged, and pinned in `workflow-manager` afterwards.

Delivered:

- a declarative gate policy (`GATE_POLICY.json`, master switch and per-gate overrides, tighten-only against a recorded floor, content-verified adoption that survives squash merges): plan and technical approval satisfiable by current local plus independent cross-model review evidence, functional validation by configured evidence, acceptance evaluated from evidence; human approval is off by default: with no policy adopted the three gates are automatic on their evidence, and a person restores the 2.7.0 gates by turning `human_approval` on (the master switch, or per gate);
- `scripts/workflow_gate_policy.py`, `scripts/workflow_forge.py` (GitHub-sourced pull-request facts), `/adopt-gate-policy`, `/satisfy-gate`, `/apply-pr-review` and the operator guide `docs/ai-workflow/GATE_POLICY.md`;
- reopening the same work item into remediation when a pull request is red or has `CHANGES_REQUESTED`;
- Orchestration Protocol 1.1: the gate rows, validation actions, evidence kinds and schema, with a golden all-human equivalence matrix against the 2.7.0 modules;
- a new conformance suite, `workflow_gate_policy_test.py`, run by `workflow-conformance.yml` (nine suites).

Compatibility: with no policy adopted, the three gates are automatic on their evidence; a person restores the 2.7.0 gates by turning `human_approval` on (the master switch, or per gate). Workflow Controller 1.7.0 (C9, released 2026-10-03) admits 2.8.0 by protocol capability; the Controller's C10 consumes the gate policy.

---

## Workflow 2.9.0

**Status:** Authored release, developed as milestone W3, `legacy-retire-and-default-version`, pending acceptance and cutover: it is published by the `Release` workflow only once the milestone is accepted and its pull request is squash-merged, and pinned in `workflow-manager` afterwards.

Delivered:

- `/retire-legacy-work-item <id>`: a user-only command that moves a dormant `LEGACY_READY` work item to `MILESTONE_COMPLETE` as already finished, guarded by the user's own confirmation naming the exact id and `retirement`, keeping its `LEGACY_V1` approval, auditable through a `Workflow-Legacy-Retirement` commit trailer; a retired item stays closed under later pull-request evidence (`is_retired_legacy_item`). Its motivating case is RepFlow's `milestone-8`;
- new installations default to governing version 2.2: the bootstrap template's `default_workflow_version` is `"2.2"`; `default_config()`, every existing configuration and every existing work item are untouched;
- `v2.6.0-003` fixed, except the `PLANNING` and `AMENDING_PLAN` phases at governing `1`: a governing-`1` item with a state entry reaches review from `IMPLEMENTING` and passes acceptance when it has no registry; `IncompleteOwnCheckpointsError` is phase-aware; and the user-only `/resume-implementation <id>` returns a 2.1/2.2 item with an outstanding checkpoint from `AWAITING_FUNCTIONAL_REVIEW` to `IMPLEMENTING`;
- Orchestration Protocol 1.2: the user-only actions `legacy.retire` (an alternative of blocked row 3) and `implementation.resume` (an alternative of blocked row 38c), never automatic.

Compatibility: with all gates human, `next-action`, `verify` and `describe` are byte-equal to 2.8.0 apart from the enumerated exemptions (`TestEquivalenceAgainstV280`). An older release has no retirement guard: on 2.8.0 or earlier a pull-request report for a retired item can reopen it (see `docs/install.md`). Unblocks RepFlow: after updating to 2.9.0, `/retire-legacy-work-item milestone-8`.

---

# 1. Review Artifact, Publication, and Concurrency Hardening

**Status:** COMPLETE — accepted as Workflow 2.6.0 (milestone `workflow-review-artifact-and-concurrency-hardening`, commit `136c417`).

The subsections below are retained as the milestone's scope record; see "Workflow 2.6.0" above and the Defect Disposition Summary for outcomes.

**Priority:** Immediate / High (delivered)

Suggested milestone:

`workflow-review-artifact-and-concurrency-hardening`

This milestone groups the remaining Workflow correctness and operator-friction defects around:

- review feedback ownership;
- review publication correctness;
- approval commit integrity;
- active-work-item migration compatibility;
- amendment artifacts;
- cross-worktree concurrency.

It should be a bounded Workflow hardening release, not a general redesign.

---

## 1.1 Per-work-item review feedback storage

### Problem

Review feedback currently converges through the shared path:

```text
.ai-review/feedback/REVIEW_FEEDBACK.md
```

Ownership guards correctly prevent one work item from overwriting feedback owned by another, but this creates recurring operational friction:

- a completed work item's stale feedback file blocks a new work item;
- the next review worker exits after doing all review work but before persisting its verdict;
- operators must manually copy/delete the stale file before retrying.

This has now interrupted multiple real Controller milestones.

### Required direction

Move review feedback to work-item-scoped storage.

Preferred minimal shape:

```text
.ai-review/<work-item-id>/feedback/REVIEW_FEEDBACK.md
```

This file is the current, ephemeral feedback surface for its work item. It preserves the existing feedback document format and lifecycle semantics.

Durable review history stays where it already lives: Workflow state, review ledgers, bundles, and Git.

### Non-goal: per-stage / per-round feedback files

Do not introduce persistent per-stage or per-round feedback storage such as:

```text
.ai-review/<work-item-id>/feedback/plan-local/round-1.md
.ai-review/<work-item-id>/feedback/implementation-local/round-2.md
```

It would improve filesystem-level history, but at the cost of:

- more review-artifact noise and agent context overhead;
- more cleanup and migration rules;
- a higher risk of stale artifacts being mistaken for current state;
- duplicating history the canonical mechanisms already preserve.

### Required semantics

- new work items use scoped feedback storage;
- unrelated work items cannot block one another through a shared feedback file;
- active legacy work items using the shared path remain supported;
- completed legacy feedback must never block a new work item;
- do not silently reinterpret a legacy feedback file as belonging to a different work item;
- review/apply/manual-record commands resolve feedback through one authoritative helper;
- Controller should consume the Workflow-resolved feedback location instead of hard-coding the old shared path;
- cleanup/ownership rules must remain fail-closed.

### Affected areas

At minimum:

- `/review-plan`;
- `/apply-plan-review`;
- `/review-implementation`;
- `/apply-implementation-review`;
- manual external plan-review recording;
- manual external implementation-review recording;
- feedback ownership helpers;
- review admissibility/reconciliation;
- tests and migration compatibility.

---

## 1.2 Legacy active-work-item compatibility for `.workflow-manager/installation.json`

**Status:** Closed in 2.6.0 (`v2.4.0-001` 2.6.0 disposition).

### Current state

The forward-looking classification problem is already mostly fixed:

- Workflow 2.4.0 added `.workflow-manager/` to newly generated plan-stage exclusions;
- Workflow 2.5.0 added the same behavior to newly generated implementation-stage exclusions.

Therefore newly created work items are generated correctly.

### Remaining problem

Existing work items whose artifact declarations were generated before those fixes remain exposed.

A Workflow Manager update can commit:

```text
.workflow-manager/installation.json
```

inside an active work item's `base_commit..HEAD` interval.

The old work item's declarations do not know how to classify that path, so review/approval reachability can fail with an unclassified-path error.

This is especially relevant during migration of long-lived repositories such as RepFlow.

### Required outcome

Design a migration-safe compatibility mechanism for active legacy work items without silently rewriting their approved protected-path declarations.

The solution must answer:

- how known Workflow Manager-owned metadata is classified for a pre-existing work item;
- how compatibility is authorized and recorded;
- how plan approval identity remains trustworthy;
- whether compatibility is release-derived, migration-derived, or explicit per-work-item metadata;
- how to avoid broad rules such as "ignore everything under `.workflow-manager/`".

### Non-goal

Do not reopen the already-correct forward-generated declarations for new work items except where needed for consistency.

---

## 1.3 `/apply-plan-review` publication ordering and recovery

### Problem

A previously reproduced failure showed this sequence:

```text
revision N
  |
/apply-plan-review
  |
Workflow state advances to revision N+1 / AWAITING_LOCAL_PLAN_REVIEW
  |
new review bundle generation fails
```

The durable Workflow state then claims revision N+1 is review-ready while the current review bundle is still revision N.

Controller correctly fails closed on this stale-bundle mismatch, but Workflow itself should not publish contradictory durable state.

### Required outcome

Make the transition to a review-ready plan revision transactional or explicitly recoverable.

Preferred semantic shape:

```text
prepare revised plan state
generate + validate review artifacts
publish the review-ready durable state only after required artifacts exist
```

If full atomicity is impractical, introduce an explicit intermediate/recovery state where the Workflow never claims the new review round is ready before the matching bundle is durable.

### Requirements

- never advertise a review-ready revision before its matching required bundle exists and validates;
- deterministic recovery after process failure;
- safe retry;
- no duplicate revision advancement;
- review bundle identity and durable state remain bound;
- Controller stale-bundle gates remain valid defense-in-depth, not the primary repair mechanism.

---

## 1.4 Plan approval commit closure

### Problem

The reviewed plan-stage content can include a newly introduced protected file that the approval commit fails to include.

The failure shape is:

```text
reviewed:
A + B + C + D

approval commit:
A + B + C
```

where `D` is a valid newly introduced protected plan-stage file.

Post-approval verification then recomputes review identity from the approval commit tree and no longer sees the exact content that was approved.

### Required outcome

The approval commit closure must be derived from the complete declared protected plan-stage set, not only a fixed list of conventional artifacts.

### Requirements

- every protected plan-stage path contributing to the approved review identity is present in the approval commit tree;
- new protected companion/reference files work without special-case code;
- deleted/renamed protected paths are handled deterministically;
- approval commit verification proves exact reviewed-content closure;
- regression test reproduces the previously observed new-file case.

---

## 1.5 Cross-worktree amendment/checkpoint correctness

### Defect

`v2.4.0-002-amendment-claim-race-crosses-worktree-boundary`

**Status:** Closed, qualified, in 2.6.0 — closed for every repository whose registered worktrees have all merged the 2.6.0 update; mixed-release worktrees remain unsupported (residual stated in the defect record's 2.6.0 disposition).

### Problem

The existing amendment/checkpoint serialization works only inside one worktree root.

Two linked worktrees can still independently decide:

- worktree A: plan amendment may begin;
- worktree B: checkpoint claim may begin.

The defect has two independent causes:

1. the current state lock is worktree-local, so the two processes do not serialize on the same lock;
2. Workflow phase lives in each worktree's own tracked `WORKFLOW_STATE.json`, so one worktree cannot authoritatively observe another worktree's newly committed `AMENDING_PLAN` phase merely by taking a shared lock.

### Required outcome

Establish a repository-wide guarantee, not only a same-worktree guarantee.

A complete repair must address both:

- repository-global serialization/ownership;
- repository-global visibility/witness of the conflicting lifecycle condition.

### Likely design work

Potential ingredients include:

- a `git_common_dir` / claims-rooted mutation lock;
- a repository-global amendment witness/lease;
- explicit lock ordering with existing claim/guard/journal primitives;
- durable crash recovery;
- stale witness detection;
- clear ownership rules.

### Required tests

- amendment begins first -> checkpoint claim cannot start from another worktree;
- checkpoint claim begins first -> amendment cannot begin from another worktree;
- real-process cross-worktree racing case;
- deterministic non-concurrent stale-phase case;
- crash while holding amendment ownership;
- crash while holding checkpoint ownership;
- no deadlock with existing guard/claim/journal locks;
- same-worktree behavior remains correct.

### Important constraint

Do not land only a partial fix that closes the shared-lock problem but leaves foreign-worktree phase visibility stale.

The defect is closed only when both causes are addressed.

---

## 1.6 `AMENDMENT_DIFF.patch` correctness

### Defect

`v2.4.0-003-amendment-diff-anchored-at-head-is-always-empty`

**Status:** Closed in 2.6.0 (repair form 1, working-tree anchor).

### Problem

During plan review of an open amendment, the generated convenience artifact currently behaves like:

```bash
git diff "${amendment_base_commit}..HEAD" -- <plan-stage protected paths>
```

The amended plan-stage files are still uncommitted during review, so `HEAD` does not contain them.

The result is an empty `AMENDMENT_DIFF.patch` even though the working tree contains real amendment changes.

### Preferred repair

Generate the amendment diff against the working tree:

```bash
git diff "${amendment_base_commit}" -- <plan-stage protected paths>
```

This matches how plan-stage review identity already reasons about uncommitted reviewed content.

### Requirements

- local and manual external reviewers see the same meaningful amendment diff;
- documentation accurately describes the chosen anchor;
- artifact remains convenience-only unless intentionally promoted into identity semantics;
- existing review identity/bundle identity rules remain unchanged unless explicitly redesigned;
- regression test proves a real uncommitted amendment generates a non-empty diff.

---

## 1.7 Preserve previously closed defect fixes

The milestone must explicitly regression-test that nearby changes do not reopen:

### v2.3.1-001

Host-history-specific integration test remains portable.

### v2.3.1-002

First-class plan amendment edge remains intact.

### v2.3.1-003

First-ever plan approval still succeeds when `WORKFLOW_STATE.json` has no prior `HEAD` entry.

These are not implementation scope; they are protected regressions.

---

## 1.8 Functional / migration acceptance

The milestone should include disposable-repository exercises covering:

1. fresh work item using scoped feedback;
2. completed old work item's feedback cannot block a new item;
3. active legacy work item still resolves its existing feedback correctly;
4. Workflow Manager update during a legacy active work item;
5. plan-review remediation with intentional bundle-generation failure/recovery;
6. plan approval with a brand-new protected file;
7. cross-worktree amendment/checkpoint contention;
8. non-empty amendment diff during an open amendment;
9. update from Workflow 2.5.1 to the new release without corrupting active state.

---

# 1.9 Post-2.6 Controller integration and Workflow Orchestration Protocol foundation

**Status:** The integration half is complete. The Workflow Controller admits 2.6.0 since its release 1.3.0 (milestone `workflow-controller-workflow-2-6-integration`), and both repositories run 2.6.0. The protocol half is complete as Workflow 2.7.0 (W1, milestone `orchestration-protocol-v1`, accepted 2026-10-02); the Controller adopts it in its C9.

**Priority:** The protocol is W1 (Workflow 2.7), and the declarative gate policy and PR reopening are W2 (Workflow 2.8). Both follow M1 and M2 ([At a glance](#at-a-glance)).

The 2.6 hardening milestone (now complete) and the Controller trunk/branch/PR/release milestone run independently in parallel.

After both complete, perform a small integration milestone first:

- upgrade the Controller repository from Workflow 2.5.1 to the released 2.6.x;
- verify the actual released contract rather than planning against unreleased details;
- replace the Controller's copied feedback-path resolver with Workflow's authoritative resolver/query;
- update/re-measure Controller expectations that still name Workflow internal state writers;
- validate 2.5.1 -> 2.6.x migration and current Controller lifecycle behavior.

After that compatibility step, introduce a stable Workflow-facing orchestration protocol so later Workflow releases normally do not require Controller lifecycle-code changes.

## Public orchestration protocol

The protocol should be a versioned public contract, separate from both:

- Workflow release version (`2.6.0`, `2.7.0`, ...);
- the work item's governing Workflow version (`2.1`, `2.2`, ...).

Initial operations:

1. `describe`
   - Workflow release;
   - orchestration protocol version;
   - supported governing versions;
   - capabilities.

2. `verify`
   - repository/installation/state health;
   - protocol readiness.

3. `next-action`
   - normalized state snapshot;
   - semantic action id and arguments;
   - disposition:
     - `automatic`;
     - `validation`;
     - `human_gate`;
     - `external_gate`;
     - `blocked`;
     - `complete`;
   - generic worker requirements;
   - state revision / state identity.

4. `reconcile`
   - Workflow-authoritative classification of the durable result of an action;
   - must recognize same-phase progress such as one checkpoint completing while phase remains `IMPLEMENTING`;
   - returns progress/result class and new state identity.

5. `record-external-result`
   - ingest typed external/manual evidence without requiring Controller to know Workflow-owned storage paths.
   - it also owns parsing a manual verdict's header, so the Controller stops reading labels itself
     (`docs/defects/v2.6.0-002-review-content-id-label-not-pinned.md`).

6. `resolve-artifact`
   - narrow semantic artifact resolver when another component genuinely needs a path.

Optional convenience:

- `inspect` for CLI/UI/debugging.

## Protocol design constraints

- public semantic action ids, not internal Python helper/function names;
- Workflow may return a rendered command invocation, but command text is not the protocol identity;
- artifact locations remain Workflow-owned;
- Controller should not copy feedback/bundle/path selection rules;
- state revision/identity must make stale decisions detectable;
- unknown protocol major fails closed;
- broad stable protocol error codes may accompany precise Workflow-native exceptions;
- exact Workflow releases may be recorded as tested/validated combinations, but should not remain the fundamental compatibility mechanism.

Target compatibility:

```text
Workflow 2.6.x ─┐
Workflow 2.7.x ─┤
Workflow 2.9.x ─┤── Orchestration Protocol v1 ── Controller
Workflow 3.x   ─┘
```

## Gate and validation policy must be declarative

**Delivered in Workflow 2.8.0** (W2, milestone `gate-policy-and-reopening`; pending cutover): `GATE_POLICY.json`, `scripts/workflow_gate_policy.py`, `/adopt-gate-policy`, `/satisfy-gate` and `docs/ai-workflow/GATE_POLICY.md`. Human approval is off by default: with no policy adopted the three gates are automatic on their evidence, and a person restores the 2.7.0 gates by turning `human_approval` on (the master switch, or per gate).

Workflow must own the meaning of lifecycle gates rather than assuming today's user-gate layout forever.

Future supported policies may include:

- plan approval automatically satisfied by current local + independent cross-model review evidence;
- implementation technical acceptance automatically satisfied by current review evidence;
- functional validation satisfied automatically by configured integration/E2E/migration evidence;
- human functional acceptance only where repository/risk policy requires it;
- PR review/merge as the final external/human acceptance boundary.

The protocol must therefore distinguish:

- automation-safe action;
- automated validation;
- human gate;
- external gate;
- blocked/refused state;
- completion.

Removing a human gate must not require Controller lifecycle-code changes if the public protocol contract remains compatible.

## Post-validation reopening and PR-review defects

**Delivered in Workflow 2.8.0** (W2, milestone `gate-policy-and-reopening`; pending cutover): reopening the same work item into remediation, `/apply-pr-review`, and GitHub-sourced pull-request facts.

"Validation passed" is not irreversible milestone completion.

The Workflow model should support an external gate result such as PR `CHANGES_REQUESTED` reopening the same work item into remediation.

Required semantic shape:

```text
technical review
  -> functional validation
  -> PR ready
  -> external PR review
       -> approved/merged
       -> or changes requested -> remediation -> re-review/re-validation -> PR ready
```

Evidence/readiness must be bound to exact implementation / PR-head identity.

When the Controller's forge adapter reports facts such as:

- PR head SHA changed;
- PR review requested changes;
- checks changed;
- PR reopened/closed/merged;

Workflow decides:

- which evidence became stale;
- whether technical review must repeat;
- whether full or targeted functional validation is required;
- what the next legal action is.

The Controller must not encode those invalidation rules itself.

## Functional validation evolution

For repositories where manual functional testing is weak or repetitive, Workflow should support strong automated functional evidence.

Examples:

- Workflow / Workflow Manager:
  - disposable-repository scenarios;
  - migration suites;
  - integration/conformance suites;
  - real lifecycle E2E exercises.

- RepFlow:
  - Room migration tests;
  - Compose/UI tests;
  - emulator/device E2E flows;
  - backup/restore and navigation/session flows.

Repository policy may still require human product/visual acceptance even when automated evidence passes.

The long-term principle is:

> stop for a human only when policy says available automation/evidence is insufficient for the next decision.

---

# 4. Review Data / History Simplification

**Priority:** Medium

Continue the convergence/scalability work begun in Workflow 2.5.0.

Potential areas:

- clearer separation of normative current review state from immutable history;
- fewer duplicated review facts across state, ledgers, bundles, and feedback;
- generated projections instead of manually synchronized copies;
- better historical indexing;
- compact long-running work-item state;
- easier audit without increasing author/reviewer bookkeeping.

Principle:

> One authoritative fact, multiple generated views.

Review storage stays intentionally minimal: one current feedback file per work item (milestone 1.1), with history held in the existing canonical mechanisms. Add persistent review files only when a concrete requirement cannot be met by state, ledgers, bundles, Git, or a generated view.

---

# 7. Multi-Worktree and Concurrency Model Maturity

**Priority:** Later / Ongoing

After the specific amendment/checkpoint race is fixed, review the broader concurrency model systematically.

Areas:

- repository-global vs worktree-local primitives;
- claim ownership;
- guard ownership;
- plan-amendment ownership;
- journal transactions;
- lock ordering;
- crash recovery;
- stale lease detection;
- multiple unrelated work items in linked worktrees.

Goal:

Document which invariants are:

- repository-wide;
- work-item-wide;
- worktree-local;
- process-local.

Then mechanically test those scopes.

---

# 9. Longer-Term Workflow Evolution

Potential future work:

- stronger transactional publication primitives;
- generalized repository-global lifecycle leases;
- reduced review convergence cost;
- better review-history compaction;
- versioned Workflow Orchestration Protocol for Controller integration;
- declarative gate/validation policy;
- semantic external-result ingestion and post-validation reopening;
- compatibility contracts for Controller/Workflow Manager integrations;
- deprecation policy for very old governing Workflow releases;
- migration tooling for retiring historical compatibility branches.

---

# Defect Disposition Summary

| Defect                                                                       | Status                                        | Roadmap disposition        |
| ---------------------------------------------------------------------------- | --------------------------------------------- | -------------------------- |
| `v2.3.1-001-host-history-coupled-tests`                                      | Fixed in 2.5.0                                | Regression protection only |
| `v2.3.1-002-no-plan-amendment-edge`                                          | Fixed in 2.4.0                                | Regression protection only |
| `v2.3.1-003-plan-approval-requires-precommitted-state-file`                  | Fixed in 2.5.0                                | Regression protection only |
| `v2.4.0-001-workflow-manager-installation-record-unclassified-at-plan-stage` | Closed in 2.6.0 (legacy active-item gap)      | Regression protection; separate update-rewrites-protected-paths hazard -> milestone 5 |
| `v2.4.0-002-amendment-claim-race-crosses-worktree-boundary`                  | Closed, qualified, in 2.6.0                   | Mixed-release worktrees unsupported (documented residual) |
| `v2.4.0-003-amendment-diff-anchored-at-head-is-always-empty`                 | Closed in 2.6.0                               | Regression protection only |
| `v2.6.0-001-withdrawn-plan-content-can-rebind-after-a-detour`                | Fixed in 2.7.0                                | Regression protection only |
| `v2.6.0-002-review-content-id-label-not-pinned`                              | Fixed in 2.7.0                                | Regression protection only |
| `v2.6.0-003-v1-state-tracked-item-cannot-advance`                            | Fixed in 2.9.0, except the two `1` planning phases (`PLANNING`, `AMENDING_PLAN`), still reported as `blocked` | Regression protection; the `1` planning phases in a later release |

`v2.6.0-003` (`OD-W1-10`): a work item governed by `"1"` that has a state entry cannot be advanced
by any 2.6.0 or 2.7.0 command. `/milestone-plan`'s `"1"` branch writes no state at `PLANNING` or
`AMENDING_PLAN`, and `/milestone-implement`'s `"1"` step 4 calls `record_bundle_generation` from
`IMPLEMENTING`, which refuses (`IllegalBundleGenerationSourcePhaseError`). At the functional gate,
a `"1"` item with a registry can never pass `/accept-milestone`'s step-2a pre-flight, since no
`"1"` command writes checkpoint statuses (protocol row 38b, LPR-R4-004).
`apply-functional-review.md`'s remediation-child sentence assumes the first of these works. The
related 2.6.0 prose inaccuracy is corrected in 2.7.0: `accept-milestone.md` step 2a told the
operator to finish an outstanding checkpoint with `/milestone-implement` from
`AWAITING_FUNCTIONAL_REVIEW`, where `transition_checkpoint_in_progress` refuses (LPR-R5-003);
`IncompleteOwnCheckpointsError`'s message still carries that advice. The `2.1`/`2.2` counterpart:
no 2.6.0 or 2.7.0 command completes an outstanding checkpoint from `AWAITING_FUNCTIONAL_REVIEW` at
any governing version (`/request-plan-amendment` refuses at that phase, and neither
`/apply-functional-review` branch makes the parent's registry terminal); a legacy promotion or a
hand-constructed state reaches it (protocol row 38c, LPR-R6-001). 2.7.0 reports these states as
`blocked` and fixes none of them: fixing the `"1"` branches changes their v1-inert contract and
golden-output test (`WF8a-ii`).

**2.9.0 disposition (milestone W3).** The origin recorded above is corrected: the
`AWAITING_FUNCTIONAL_REVIEW` state with an outstanding checkpoint is reached by a hand-constructed
or hand-edited state, never by a legacy promotion (`promote_legacy_work_item` adds no plan
approval, so row 38a precedes row 38c). 2.9.0 lets a `"1"` item with a state entry reach review
from `IMPLEMENTING`, makes the checkpoint-incomplete message phase-aware, and adds the user-only
`/resume-implementation` for `2.1`/`2.2`. Still reported: `PLANNING` and `AMENDING_PLAN` at
governing `1`, and a `"1"` item with a non-terminal registry at the functional gate (row 38b).

Additional hardening items delivered in milestone 1 (Workflow 2.6.0):

- shared review-feedback ownership/contention;
- `/apply-plan-review` publication ordering/recovery;
- plan approval commit closure for newly introduced protected files.

---

# Roadmap Principles

1. **Frozen releases are immutable.**  
   Fixes ship as new authored releases.

2. **Work-item governance is durable.**  
   Installing a newer Workflow does not silently rewrite the semantics of an already-governed work item.

3. **Review identity must describe exactly what was reviewed.**  
   Approval commits, bundles, ledgers, and protected-path declarations must remain consistent.

4. **Publish only durable truths.**  
   Workflow must not claim a review-ready or approved state before the artifacts required by that state are valid and durable.

5. **Fail closed, but recover cleanly.**  
   Unknown classification, stale artifacts, and conflicting ownership should stop progress with actionable recovery rather than corrupt state.

6. **Repository-wide claims require repository-wide primitives.**  
   A worktree-local lock cannot establish a repository-wide concurrency guarantee.

7. **Legacy compatibility must be explicit.**  
   Forward-generated fixes are not automatically retroactive fixes for already-approved work items.

8. **Avoid duplicating review/history state.**  
   Each review fact has one canonical home; do not add persistent files that restate what state, ledgers, bundles, or Git already record.

9. **Prefer minimal canonical state and generated views.**  
   Derive projections on demand rather than maintaining more persistent bookkeeping.

10. **Dogfood migrations before touching real long-lived repositories.**  
    RepFlow disposable migration remains a required proving ground.

