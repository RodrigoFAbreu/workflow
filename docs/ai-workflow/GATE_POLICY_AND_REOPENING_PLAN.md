# W2: Workflow 2.8.0 — declarative gate policy, automatic gates and post-validation reopening (Revision 34)

- **Work item:** `gate-policy-and-reopening` (`process`, governing version `2.2`)
- **Roadmap step:** W2 (`docs/ROADMAP.md`, "At a glance"; section 1.9, "Gate and validation policy must be declarative" and "Post-validation reopening and PR-review defects")
- **Branch:** `milestone/gate-policy-and-reopening`
- **Base commit:** `d14e0a7` (W1's squash merge, #5; the release source is Workflow 2.7.0, pinned by `workflow-manager#13`, Manager v1.3.0)
- **Plan revision:** 34

## 1. Goal

Ship Workflow 2.8.0 with Orchestration Protocol 1.1 (a minor bump of v1). It
has two parts, both built on W1's protocol:

1. **Declarative, toggleable gates.** The Workflow, not an orchestrator, owns
   what "this gate is satisfied" means. There are three gates a person signs
   today: the plan approval, the implementation (technical) approval and the
   milestone acceptance. From 2.8.0 each is satisfied **automatically by its
   evidence** unless a human toggle is on for it. A master switch
   (`human_approval`) turns all three into the human gates of 2.7.0, and a
   per-gate override turns individual ones on or off (for example: a human
   approves only the plan, or only the acceptance). The shipped default is
   human approval **off**: with no policy file, all three gates are satisfied
   by evidence. The toggles can only be loosened by a person (D-GP-Policy).
2. **Post-validation reopening.** "Validation passed" stops being
   irreversible. When the forge reports that a pull request is red or has
   `CHANGES_REQUESTED`, the Workflow reopens the same work item into
   remediation, decides which evidence became stale, and names the next
   legal action. The orchestrator reports facts and encodes none of those
   rules.

**The user's decision (2026-10-03, recorded verbatim).** "Add automatic
acceptance now, but i want this human gates to be toggleble, by default they
will be off but if you want but you can run with the current flow of user
acceptance at the plan, implementation and acceptance of milestone by
toggling humman approval, maybe inside you can also toggle each individual
gate if you maybe only want to approve the plan or only approve the
acceptance of the milestone, for example." This supersedes the earlier
instruction that the default must reproduce 2.7.0's gates. The shape that
follows (a master switch plus per-gate overrides, a default of automatic,
human-to-automatic changes needing a person) is this plan's reading of that
decision; `OD-W2-2`, `OD-W2-5`, `OD-W2-14` and `OD-W2-15` flag the choices the
user may still overrule. Two later questions are decided, by the user's
decisions of 2026-10-03 recorded in section 11: `OD-W2-17` (b), where
`distinct_reviewer_models` is on by default for the automatic plan and technical
gates and configurable, and `LPR-R9-002`, where an orchestrator-supplied forge
fact is tighten-only.

### Hard requirements (invariants)

These are the properties every checkpoint is tested against.

- **INV-1, human equivalence.** With every gate human (the master switch on,
  no per-gate override to automatic), every `next-action` decision, every
  state write and every command's behavior equals 2.7.0's, byte for byte where
  bytes are written, **except for the exhaustive list of intentional deltas in
  D-GP-Compat**. The shipped default (switch off) is **not** 2.7.0: its three
  gates are automatic, and the differences are the point of this release.
  They are listed in D-GP-Compat, stated plainly in the compatibility notes,
  the operator guide and the update simulation. CP6 proves INV-1 with a golden
  matrix over every phase and governing version for `next-action`, `verify`,
  `describe` and `record-external-result`, and CP7 with an update simulation
  of both configurations.
- **INV-2, the Workflow owns every invalidation rule.** Which evidence
  became stale, whether technical review repeats, which validation must be
  redone, and what the next legal action is: all are decided by Workflow
  code from a table the Workflow ships. The Controller reports facts only.
- **INV-3, evidence binds to exact identity.** Every evidence record carries
  the implementation `review_content_id` and the commit it was computed at
  (and, for pull-request facts, the PR head). The Workflow recomputes the
  identity when it evaluates; it never trusts a reporter's claim of it.
- **INV-4, an automatic satisfaction is auditable.** Every gate satisfied
  automatically leaves a durable record naming the policy digest and source,
  each requirement and whether it was met, and the evidence it read. A gate
  never passes without that record.
- **INV-5, automatic never weakens a precondition, and missing or stale
  evidence blocks.** Automatic satisfaction requires everything the human path
  requires (the existing gate predicates, unchanged), and then more. A
  `USER_OVERRIDE` approval over a `REVISE` is never automatic. An automatic
  gate whose evidence is missing, stale or failed is **blocked** (a `blocked`
  decision naming what is unmet, or an `external_gate` naming the evidence to
  obtain), never passed. The human path stays available beside the automatic
  one: a person can always run `/approve-review` or `/accept-milestone`.
- **INV-6, an agent can never loosen a gate.** Switching a gate to human
  applies immediately (a stricter setting needs no adoption). Switching a
  human gate back to automatic, or removing any requirement, needs the
  user-only `/adopt-gate-policy`. A human setting the Workflow has ever recorded
  (D-GP-Policy, "Bundle generation"; the stated residuals name what is not yet
  recorded) survives an edit or deletion of the file: the effective policy is the
  strictest of the committed adopted policy, a recorded **floor** (a ratchet
  of every setting observed in the file, in the working tree or in history)
  and the file. The adopted policy and the floor are trusted only while they
  verify by their own content and by the chain of their changes in history
  (never by a commit message, which this repository's squash merges discard),
  and a state that no longer verifies fails closed to all gates human
  (D-GP-Policy). "Never" is bounded by the **threat model** (D-GP-ThreatModel):
  the guarantee holds against an agent acting through the Workflow's commands
  and protocol, not against an agent that forges commits, trailers or state by
  hand or replaces system programs, which no local mechanism can tell from the
  user's own act; the same limit as today's user-only gates.
- **INV-9, the trust boundary is stated, and every automatic satisfaction is
  traceable to it (D-GP-Trust).** CI and pull-request facts come from GitHub
  and never from an agent's word: a gate is satisfied only by a fact the
  Workflow obtained itself, with its one fixed built-in query run inside the
  satisfying command's own transaction. A fact an orchestrator reports (with
  the forge provenance of D-GP-Invalidation) can only **tighten**: it is
  recorded and it can only **trigger** the Workflow's own fixed query (it can
  never suppress one); it never decides PR state, actionability, a reopening or
  completion, and never satisfies `pr_fact_current`, `ci_green` or
  `pr_approved` (the single principle of D-GP-Trust, `LPR-R28-001`). A gate that cannot decide
  (no `gh`, an undecidable answer) fails closed (blocks). Review
  verdicts (local and external) and functional evidence are **trusted from the
  orchestrator** that reports them: the Workflow guarantees binding to the
  exact content, freshness and an audit trail, not provenance. Turning human
  approval on is the stronger mode. All of INV-5, INV-6 and this invariant are
  stated under the threat model of D-GP-ThreatModel.
- **INV-7, the acceptance gate is a gate like the others.** It has the same
  toggle, the same audit record and the same safety rule. Automatic acceptance
  requires current evidence for every checkpoint, the technical approval, the
  functional flows and CI, and (by policy) an approved pull request
  (D-GP-Acceptance). There is no gate this release leaves outside the policy.
- **INV-8, the protocol stays compatible.** The protocol moves to `1.1`, an
  additive change. Nothing emitted by a human gate changes except the
  D-GP-Compat list. An unaware `1.0` consumer meets the `validation`
  disposition and new action ids: unknown action ids are `blocked` (its
  obligation 3), and `validation` is already in the `1.0` schema's enum, so
  obligation 5 ("runs an `automatic` action only") is what keeps it from
  running one. The effect is a stalled item, not a `blocked` one
  (`LPR-R2-008`), and it applies to the default, not only to an opted-in
  repository.

### Non-goals

- **Changes to the Controller.** Its C10 consumes this release.
- **Executing evidence commands named in a repository file** (`OD-W2-4`). The
  orchestrator runs suites and reports functional results. The Workflow's one
  built-in `gh` query (D-GP-Trust) is fixed in code and names nothing from a
  repository file.
- **Functional or review evidence produced in CI.** The user decided
  (2026-10-03, section 11) that this release does not add it, and it is not
  offered as a policy option either. Functional evidence and review verdicts
  stay trusted from the orchestrator that reports them.
- **Verified model identity.** The Workflow records a declared reviewer
  model family and checks that two families differ when a policy requires it.
  It cannot prove which model answered (`OD-W2-3`).
- **Changes to this repository's installation** (`.claude/`, `scripts/`,
  the managed Workflow documents, `.workflow-manager/`). It stays at 2.6.0
  and `workflow-manager verify .` stays clean.
- **The `workflow-manager` pin pull request** for 2.8.0, made after the
  release is published (section 7).
- **The `v2.6.0-003` gap** (a `1` item's states that no command advances). It
  stays reported, not fixed.

## 2. What exists today (facts this plan relies on)

All paths are in the release source (`payload/`) unless stated otherwise.

- **Protocol 1.0** (`scripts/workflow_protocol.py`,
  `docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`). `PROTOCOL_VERSION` is `1.0`,
  `WORKFLOW_RELEASE` is `2.7.0` and the build guard requires the two release
  constants to agree with the manifest. `DISPOSITIONS` includes `validation`,
  which no catalogue row emits. `RESERVED_RESULT_KINDS` is
  `functional_evidence` and `pr_review_result`; `record-external-result`
  refuses both with `unsupported_result_kind`. The catalogue is an ordered
  list of `Row` entries (rows named by stable labels, a later row gets a
  letter suffix), `EDGES` maps each automatic action to its legal phase
  edges and allowed result classes, and `reconcile` classifies a result as
  `progress`, `no_progress`, `gate_reached` or `invalid`.
- **The human gates.** Plan approval (`/approve-review plan`, phase
  `AWAITING_PLAN_APPROVAL`) and technical approval
  (`/approve-review implementation`, phase
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`) are `user_only`: the command has
  `disable-model-invocation: true` and requires a `user_confirmation` naming
  the work item and the stage (`validate_user_confirmation`,
  `APPROVAL_STAGES`). Reachability is decided by the read-only wrappers
  `plan_approval_gate_status` and `technical_approval_gate_status`, over the
  pure predicates `plan_approval_gate_reachable` and
  `technical_approval_gate_reachable`. They require the latest verdict to be
  `APPROVE`, and for a two-stage item both ledger stages to record `APPROVE`
  for the current `review_content_id`. The record is built by
  `build_approval_record` (bases `EXTERNAL_APPROVE`, `USER_OVERRIDE`,
  `LEGACY_V1`) and written by `apply_plan_approval` /
  `apply_technical_approval`. The plan approval is a journaled commit
  transaction (steps 4a to 6d of the command) that commits every plan-stage
  protected path, with the `Workflow-Plan-Approval` and `Workflow-Work-Item`
  trailers.
- **Currency.** `approval_is_current` recomputes a commit-source
  `review_content_id` and compares it with `approved_review_content_id`; no
  writer flips an approval to stale on drift (drift is read live). The one
  stale writer is `mark_technical_approval_stale`, called by
  `/apply-functional-review` before any edit. `record_bundle_generation` with
  stage `post-fix` is legal from `AWAITING_FUNCTIONAL_REVIEW` only when the
  technical approval is `STALE`, and it opens a new implementation round.
- **Reviewer independence** is a role label, not a model identity. The
  ledger entries (`LOCAL_MODEL_*_REVIEW`, `MANUAL_EXTERNAL_*_REVIEW`) hold
  `bundle_id`, `verdict`, `round` and `completed_at`; `/review-plan`'s own text
  says nothing in its contract names a model. A fresh session is
  recommended operationally and never verified.
- **The functional gate.** `AWAITING_FUNCTIONAL_REVIEW` is a `human_gate`
  (catalogue row 39, action `functional.review`) with `/accept-milestone`
  (`user_only`, `validate_user_confirmation` with stage `acceptance`) as the
  way out. `/apply-functional-review` classifies findings: no code change, a
  bounded fix (stale the technical approval, fix, `record_bundle_generation`
  `post-fix`), or a broad one (`create_remediation_child_work_item`).
  `complete_work_item` refuses while a child is incomplete.
- **Terminal items.** `MILESTONE_COMPLETE` is terminal; `route_work_item`
  refuses to reuse its id, and nothing moves it back.
- **No pull-request model exists** anywhere in the release source: no code,
  schema or template names a PR, its head, checks or a review decision. The
  only text is the roadmap prose these two sections implement.
- **Acceptance today.** `/accept-milestone` (`user_only`, stage
  `acceptance`) runs a pre-flight (step 2a: `resolve_own_registry_completion_status`,
  `milestone_complete_gate_reachable`), then `complete_work_item`, which
  re-resolves the item's own registry and refuses while a child is incomplete,
  while a checkpoint is not `COMPLETE`, or while a completion obligation is
  unsatisfied. Steps 3 to 7 update the roadmap and the narrative, archive the
  plan (step 5, "Archive ... to `docs/milestones/completed/`", which does not
  say copy or move) and create the completion commit. Rows 38a to 38c already
  block when the registry is unreadable or not terminal.
- **The bundle generation check (`LPR-R18-001`).**
  `workflow_fingerprint.assert_local_generation_matches`
  (`payload/scripts/workflow_fingerprint.py:3160`) refuses with
  `WorktreeOrHeadMismatchError` when `HEAD` differs, by exact equality, from the
  `generation_head` that `MANIFEST.md` recorded (and when the worktree root
  differs). It is called by the two gate wrappers (`plan_approval_gate_status`,
  `payload/scripts/workflow_state.py:13089`; `technical_approval_gate_status`,
  `:13165`, whose first cause is `bundle_generation_mismatch`), and by the
  manual-ingest guards of both stages (`_two_stage_manual_verdict_guards`, `:16795`
  plan and `:16810` implementation, which serve `/record-manual-*-review` and
  `record-external-result`). **Any commit that lands after a bundle was generated
  stales that bundle**, whatever it changes, because `HEAD` moved. The only
  recovery is `/recover-implementation-provenance`, which is an
  implementation-stage command (for a 2.2 item, from the three phases of its
  `bundle_generation_recovered_role_legal_committed_phases`); a plan-stage
  bundle has none but the withdrawal, `/milestone-plan <id>`. The two commits
  this release adds (the floor commit and the adoption commit) are such commits
  (D-GP-Policy, "Bundle generation").
- **State and approvals have exact shapes.** `validate_state`,
  `validate_approval_record` and `_validate_plan_review_stages` /
  `_validate_implementation_review_stages` reject unknown keys and bases.
  Every field this plan adds therefore needs its validator widened (D-GP-Compat).
- **`approval_review_content_id` takes a `head`.** The implementation
  identity can be computed at any reachable commit, which is how a PR head
  is compared with the approved implementation (D-GP-Invalidation).


## 3. Design decisions

### D-GP-Policy: the toggles, the file, the default and adoption

**The file.** `docs/ai-workflow/GATE_POLICY.json` is repository-local state,
like `WORKFLOW_CONFIG.json`: never shipped, never overwritten by an update.
A shipped document, `docs/ai-workflow/GATE_POLICY.md`, specifies it and
carries examples. The file is a closed-vocabulary schema; an unknown key is
refused. Every key is optional and an omitted key takes the default:

```json
{
  "schema_version": 1,
  "human_approval": false,
  "gates": {
    "plan_approval":      {"human": true, "require": ["distinct_reviewer_models"]},
    "technical_approval": {"require": ["distinct_reviewer_models"]},
    "acceptance":         {"human": false, "require_ci": true,
                           "requires_pr_approved": false,
                           "required_flows": ["migration-suite", "e2e-suite"]}
  },
  "pr_review": {"enabled": true, "reopen_on": ["changes_requested", "checks_failed"]}
}
```

- **The master switch.** `human_approval` (boolean, default `false`) turns
  all three gates human when `true`.
- **The per-gate override.** `gates.<gate>.human` (boolean, optional)
  overrides the master for that gate. A gate is human when its `human` is
  present and true, or absent while `human_approval` is true. So
  `{"human_approval": false, "gates": {"plan_approval": {"human": true}}}`
  makes a person approve only the plan, and `{"human_approval": true,
  "gates": {"plan_approval": {"human": false}, "technical_approval":
  {"human": false}}}` makes a person accept only the milestone. The gate ids
  are `plan_approval`, `technical_approval` and `acceptance` (milestone
  acceptance).
- `require` (plan and technical gates) is a closed list. In 2.8.0 it can hold
  `distinct_reviewer_models` and nothing else; the review-ledger and
  gate-status conditions are always required and are not configurable
  (INV-5). **Default: `["distinct_reviewer_models"]` for both `plan_approval`
  and `technical_approval`** (`OD-W2-17` (b), decided by the user on
  2026-10-03). It applies only where the gate is automatic, so it changes
  nothing under all-human (INV-1). Removing it is a **loosening**: the file
  cannot do it (`require: []` in the file is `file_loosening_ignored`), and only
  the user-only `/adopt-gate-policy` can, which is reported as a gate-lowering
  event. A person with one reviewer subscription has the remedies
  `14b`/`28b`, D-GP-Ingest and `GATE_POLICY.md` name, and they depend on the
  phase (`LPR-R19-001`). While the stage is open (the refused ingest): record a
  review from a second declared family, or turn that gate human (immediate, no
  adoption). After the stage has closed (`AWAITING_PLAN_APPROVAL` and its
  technical analogue): turn that gate human, or withdraw with `/milestone-plan
  <id>` (or its implementation analogue), edit, regenerate and repeat both
  review stages. Adopting a policy without the requirement through
  `/adopt-gate-policy` is **not** a remedy at either phase: its commit moves
  `HEAD` past the open bundle's `generation_head` ("Bundle generation"). It is
  advice for before the stage's bundle is generated, and its confirmation text
  lists the bundles it stales and the regeneration or withdrawal each then
  needs.
- `acceptance` evidence options (D-GP-Acceptance): `require_ci` (default
  `true`), `requires_pr_approved` (default `false`) and `required_flows`
  (flow ids matching `^[a-z0-9][a-z0-9_-]{0,63}$`; default empty).
  `requires_pr_approved` is a per-gate option because in automatic mode no
  person may review the pull request: a repository where a human review of the
  PR is the evidence turns it on. It also applies, as an added precondition,
  to a human acceptance, and it never removes a human.
- `pr_review.enabled` (default `true`) and `pr_review.reopen_on` (default both
  causes, a subset of `changes_requested` and `checks_failed`) govern whether
  a Workflow-queried PR fact reopens an item (D-GP-Invalidation; a reported fact only triggers that query, `LPR-R28-001`). `content_changed`
  is always a cause when enabled.

**The built-in default** is `DEFAULT_POLICY`, a constant in the new module
`scripts/workflow_gate_policy.py` (stdlib-only): `human_approval` false, no
override, `require_ci` true, `requires_pr_approved`
false, no required flows, `pr_review` enabled with both causes; the one
non-empty `require` is `["distinct_reviewer_models"]` on `plan_approval` and
`technical_approval`. With no file,
**all three gates are satisfied automatically by their evidence.** A test pins
the all-human configuration's decisions to 2.7.0's (INV-1).

**Safety: tighten-only, loosen by adoption, never from the file alone
(INV-6, `OD-W2-2`).** Every setting has a stricter and a looser value.
Stricter means: a gate `human` rather than automatic; a larger `require` list;
a larger `required_flows` list; `require_ci` or `requires_pr_approved` true
rather than false; `pr_review` enabled rather than disabled; a larger
`reopen_on` set. The policy is compared in its **resolved** form (each gate's
human or automatic after the master switch and the override are applied). The
effective policy is, field by field, the stricter of three inputs:

- the **base**: the last adopted policy, read from the **committed** state at
  `HEAD` and only once its provenance verifies (below), or `DEFAULT_POLICY`
  when none was adopted;
- the **floor**: the top-level `gate_policy_floor`, a ratchet of every
  setting the Workflow has observed in the file (below); and
- the **file**, when it is present and valid.

So a file that turns a gate human, adds a requirement or adds a flow takes
effect **immediately**, with no adoption, and from the first evaluation that
observes it **it stays in effect even if the file is edited back or deleted**:
the looser value is ignored and the floor's value stays. The only way to
lower the floor or the base is `/adopt-gate-policy`.

**The floor, a ratchet (B1).** `record_gate_policy_floor(repo_root, state,
now)` is the one writer of the optional top-level `gate_policy_floor`:
`{policy, digest, recorded_at, observed}`, where `policy` is the resolved
(flat) policy and `observed` lists the file digests it came from. It sets
`policy` to the field-wise stricter of its current value and of every file
version it can see: the working-tree file, the file at `HEAD`, and every
version of `docs/ai-workflow/GATE_POLICY.json` in a first-parent commit
reachable from `HEAD` since the newest **adoption-introducing commit** (defined
once below, `LPR-R12-001`; never a merge that only brings in another parent's
adoption) (a history scan, cached per `HEAD`, so a committed
deletion or loosening of the file cannot hide a setting that was once
committed **on the history `HEAD` can see**). It never loosens: when nothing observed is stricter than the
current floor and the base it writes nothing. It is called inside the
`state_transaction` of every **committing** command that evaluates a gate
(`/satisfy-gate`, **after** its satisfying commit and never before its
evaluation, `LPR-R18-001`; `/adopt-gate-policy`), and the
caller then commits the change in its own state-only commit with the trailer
`Workflow-Gate-Policy-Floor: <digest>`, staged top-level-scoped. `/satisfy-gate`
evaluates against the **virtual** floor, the very value `next-action` computes,
so its evaluation is as strict as if the floor had been recorded first, and the
floor commit follows the approval commit, when the bundle it would have staled
is already consumed (see "Bundle generation" below). Read-only calls (`next-action`, `verify`) and the non-committing
`record-external-result` compute the same floor **virtually** and never write
it. `/adopt-gate-policy` resets the floor to the adopted policy's resolved
form (an adoption is the user's act of loosening). The floor only ever
tightens by itself: a working-tree edit of the floor to a looser value is
ignored in favour of the committed one.

**What survives a squash merge (`LPR-R9-001`).** This repository merges by
squash only, with a blank squash body (`.github/repository/merge-settings.json`,
`docs/RELEASING.md`), and deletes the branch, so on `main` a branch's commits,
their messages and their trailers are gone: `main` holds one commit whose diff is
the branch's net change. The design therefore rests on what the **tracked state
file** carries, and on content checks, never on a commit message or on a branch
commit surviving. `gate_policy_floor` and `gate_policy_adoption` live in the
state file, so once recorded they are part of `main`'s committed state and every
later branch reads them. The history scan above is a **bonus on top** of that, and
its guarantee is restated to what a squash leaves: a setting is guaranteed to
persist once a committing evaluation (`/satisfy-gate`, `/adopt-gate-policy`) has
**recorded it in `gate_policy_floor`** and the record is committed; a human
setting that was committed and then deleted *inside one squashed branch*, with
no committing evaluation in between, leaves no trace on `main` and is not
recovered. That is the stated residual (alongside "a setting never observed
durably"), pinned by a test, and the operator guide's remedy is the same as for
every residual here: adopt a human policy with `/adopt-gate-policy`, which
records it at once.

**Adoption.** `/adopt-gate-policy` is a `user_only` command
(`disable-model-invocation: true`). Its guard is a dedicated
`validate_gate_policy_confirmation(text, digest)` that requires the text to
contain the literal `gate_policy` and the first 12 hex characters of the digest
shown to the user; it is work-item-free and touches neither
`validate_user_confirmation` nor `APPROVAL_STAGES` (`LPR-R1-003`). Before the
user confirms it shows the file's digest and the resolved difference from the
current effective policy, listing each loosening and each tightening. It
records, in the state file's optional top-level `gate_policy_adoption`,
`{sha256, adopted_at, confirmation, policy, history, lowered}`: the digest of
the canonical bytes, the policy body itself (so a deleted file cannot loosen
what was adopted), a list of earlier adopted digests, and `lowered`, the
**gate-lowering label** (below). It also resets `gate_policy_floor`. **The adoption commit's diff contract, stated once
(`LPR-R9-003`):** the adoption commit changes exactly **two** top-level keys,
`gate_policy_adoption` and `gate_policy_floor` (the floor reset to the adopted
policy's resolved form, which may lower a recorded floor), and no work item;
`validate_gate_policy_adoption_commit` requires exactly that diff, and every
other section of this plan that names the adoption commit means this contract.

**Bundle generation: what the two commits do to an open bundle, chosen once
(`LPR-R18-001`).** Both the floor commit and the adoption commit change only
`WORKFLOW_STATE.json`, an excluded path, so no `review_content_id` changes, but
`HEAD` moves, and the 2.7.0 generation check (section 2) refuses every reader of
a bundle generated at the earlier `HEAD`. The 2.7.0 check is **not relaxed**: no
new reader, relaxation or recovery is added, and an external-reviewer path never
calls it (`WFR-17`). The two commits are instead ordered and described so that
neither one stales a bundle that is still needed.

- **The floor commit never stales a needed bundle.** `/satisfy-gate` evaluates
  against the virtual floor, runs the satisfying commit, and only then records
  the floor in its own floor commit. The bundle is consumed by then (a plan
  approval commit, or the technical approval commit, closes the gate and moves
  `HEAD` itself, so the floor commit adds no staleness). A `/satisfy-gate` that
  refuses, or finds the gate not `satisfiable`, records no floor and makes no
  commit, so a tightening not yet in the floor never stales the plan or
  implementation bundle of an item that is merely waiting. `/adopt-gate-policy`'s
  own floor reset is part of its adoption commit (below). For `acceptance`, which
  reads no bundle (D-GP-Acceptance), the same order is kept for uniformity.
- **The adoption commit stales every open bundle, and that is stated, not
  hidden.** `HEAD` is repository-wide, so an adoption made while any work item
  holds an open plan-stage or implementation-stage bundle stales that bundle:
  its readers then refuse with `bundle_generation_mismatch`/
  `WorktreeOrHeadMismatchError`, and `next-action` falls to the row-16/row-30
  cause remedies. Therefore **adoption is not offered, anywhere in this plan, as
  a remedy executable at an open review phase.** The remedy texts of D-GP-Ingest,
  `14b`/`28b`, `GATE_POLICY.md`, `OD-W2-17` and the operator guide name it only
  as a policy set **before** the stage's bundle is generated, when it costs
  nothing; adopting while a bundle is open is allowed (it is the user's act) but
  its confirmation text lists each open bundle it will stale and the way out:
  a plan-stage bundle is withdrawn and regenerated with `/milestone-plan <id>`
  (both review stages are then recorded again, the withdrawn content being
  consumed), an implementation-stage bundle is recovered with
  `/recover-implementation-provenance <id>` from the phases that command admits,
  and otherwise regenerated by the item's own remediation cycle.
- **Remedies that remain executable at an open phase.** Turning the gate human
  is an uncommitted working-tree edit of `GATE_POLICY.json`, read live by the
  wrapper, which moves no `HEAD` (committing it later does, like any commit, and
  only after the gate is satisfied it matters no more). A second-family
  `Reviewer model:` is recorded at ingest while the stage is open. The
  withdrawal is as stated.
- **D-GP-Compat line.** Under all-human no floor commit and no adoption commit is
  made by this release (nothing runs `/satisfy-gate`; an adoption is the user's
  own act), so the generation check sees no new commit and INV-1 holds.

**Provenance of the adopted policy and the floor (B2, `LPR-R9-001`).** The
fields supply the base and the floor, so the Workflow does not trust them for
being in the state file. It verifies them by **content and by the chain of their
changes**, never by a commit message, because a squash merge discards the branch
commits and this repository's squash body is blank (above).
`verify_gate_policy_provenance(repo_root)` reads the state **at `HEAD`**, never
the working tree. **The ranges, stated once (`LPR-R10-001`):** the adoption is
checked at the **newest** first-parent commit reachable from `HEAD` whose state
differs from its first parent's in `gate_policy_adoption` (a removal counts as a
change; the chain below carries every earlier adoption, so the newest change is
enough). **Adoption-introducing commit (defined once, `LPR-R12-001`):** a
first-parent commit that changes `gate_policy_adoption` against its first parent
**and** whose new `sha256` is held by no *other* parent, neither as that parent's
current `sha256` nor in its `history` (the `LPR-R11-003` criterion). An adoption
made on this branch (`/adopt-gate-policy`, or a squash that folded it) is
adoption-introducing; an update merge that only brings in `main`'s adoption is
not, because `main` already holds that digest. The floor is checked at **every**
first-parent commit that changed `gate_policy_floor` **since and including the
newest adoption-introducing commit**, or since the root when none exists. So an
adoption this branch introduces is the reset point: a floor loosening before it
no longer fails, which is what makes the re-adoption remedy below work. An update
merge is never a reset point, so a floor loosening made on the branch before it
stays in range and is compared with its own first parent; and no loosening after
the reset can be hidden by a later tightening, because each floor change is
compared with its own first parent. The file history scan above and the reset
exemption below use this same one lower bound. (A merge that brings in `main`'s
adoption still has its own adoption chain checked, at the newest
adoption-changing commit above; only the *lower bound* differs.) A
commit may be a branch commit or the squash commit that folded it; the checks
are the same. Then:

- **`gate_policy_adoption`**: the field at `HEAD` must be self-consistent (the
  sha256 of the canonical bytes of its `policy` equals its `sha256`, and its
  `confirmation` passes `validate_gate_policy_confirmation` for that digest),
  and, at the commit that changed it, its `history` must **begin with** the first
  parent's `history` followed by the first parent's `sha256` (an empty `history`
  when the parent had no adoption). The chain lets one commit, a squash, carry
  several adoptions, and it ties each adoption to the one before it, so a
  replaced, spliced or removed record fails. A removal, or a change that breaks
  either check, is a failure. If the commit **does** carry a
  `Workflow-Gate-Policy-Adoption: <digest>` trailer (an adoption commit on a
  branch, before a squash), the trailer must equal the field's `sha256`: it is
  an audit label that is checked when present and never required, so a squash
  commit with a blank body verifies;
- **`gate_policy_floor`**: at every first-parent commit in the range above that
  changed it, the floor must be **no looser** than the first parent's floor (or than the
  first parent's adopted policy when it had no floor, or the default when
  neither), unless the **same commit** also changed `gate_policy_adoption`
  validly, in which case the floor must be no looser than the new adopted
  policy's resolved form (the reset; an adoption that lowers the floor is
  therefore accepted exactly when it is itself valid, before and after a squash).
  **The reset applies only to an adoption the commit itself introduces
  (`LPR-R11-003`):** the new adoption's `sha256` must equal no adoption digest
  that any *other* parent of the commit already holds (as its current `sha256`
  or in its `history`). At a merge commit whose new adoption came from a
  non-first parent (a branch updating from `main`, where `main` adopted
  meanwhile), the floor is bound **three-way against the merge base** instead
  (`LPR-R13-001`): for each floor field (each gate's setting and each other
  field of `policy`), the merged value must be no looser than **the incoming
  (non-first) parent's value when the first parent's value equals the merge
  base's value for that field** (the branch did not record it, so it simply
  inherited it from `main` and takes `main`'s, which is how a user's loosening
  adoption on `main` survives), and otherwise no looser than the **field-wise
  stricter of both parents' values** (the branch recorded or changed it). A
  parent or base with no floor counts as its adopted policy, or the default.
  So a resolution that keeps the incoming adoption's reset floor and drops a
  stricter floor *the branch itself recorded* fails on the branch, until it is
  resolved stricter for those fields or the branch re-adopts; a field the
  branch never touched is never held against it. The merge base is the
  one `git merge-base --all` names for the merge's parents when it names exactly
  one; with **more than one** (a criss-cross history) the verification **fails
  closed** on that merge, naming the merge and its bases (`LPR-R14-O4`), so the
  definition is deterministic; an unreachable base counts as "no floor". A removal, or a loosening by
  any other commit, is a failure. The trailer
  `Workflow-Gate-Policy-Floor` is an audit label and not a precondition.

A failed verification **fails closed**: the effective policy is *all three
gates human*, `source: provenance_failed`, and `verify`'s `gate_policy` check
is `fail`, naming the field and the commit. The way out is a new
`/adopt-gate-policy` commit, which becomes the newest change to both fields and
so the lower bound of the floor range; `verify`'s message names that remedy.
Because the checks are content-based, an adoption **keeps verifying after it is
squash-merged** and on every branch cut from `main` afterwards; it is no longer
a property of a branch that is lost when the branch is deleted.
Every other commit type is checked too (a validator that rejects an
unrecorded change, B2): `validate_technical_approval_commit`,
`validate_bundle_generation_record_commit` and `validate_gate_policy_adoption_commit`
already refuse any top-level change through `_forbidden_state_mutation` and
are unchanged; the unvalidated whole-file state commits (the plan approval, the
checkpoint and self-review commits of `milestone-implement.md`,
`/request-plan-amendment`'s commit) gain a post-commit call to
`assert_gate_policy_fields_unchanged_or_tightened(repo_root, commit)` (their
one added sentence each, and a call inside `verify_plan_approval_commit`),
which applies the two content rules above to that commit and fails on an
adoption change that breaks them or a floor loosening. A
hand edit of the working tree that loosens either field changes nothing: the
base is read from `HEAD`, and the floor can only tighten.

**Concurrent branches: the merge rule for the two fields, stated once
(`LPR-R10-004`).** Both fields are repository-wide keys in the one tracked state
file, and `main` is `strict` (`.github/repository/ruleset-main.json`,
`docs/RELEASING.md`), so a branch updates from `main` before it merges, normally
with a merge commit, and the first-parent check on the branch compares only that
branch's own commits. The rule:

- **Floor**: when two branches changed `gate_policy_floor`, the conflict is
  resolved to the **field-wise stricter of both sides, for the fields both
  changed**, never to one side; a field only one side changed takes that side's
  value (three-way, against the merge base, `LPR-R13-001`), so an adoption's
  reset on `main` is never silently reverted by a branch that did not itself
  record that field. A
  resolution that keeps the looser side loosens `main`'s floor in the squash
  commit; that is a floor loosening and `main` then fails closed
  (`provenance_failed`, all gates human) by design. When the update merge also
  brings in a new adoption from `main`, the branch's own check closes the same
  hole: the adoption-reset exemption does not apply at that merge, and the
  three-way bound of the floor rule above holds the fields the branch itself
  recorded, so a branch that dropped a floor it recorded itself fails closed at
  the merge commit, before any squash, and not only on `main`. Nor does that merge reset the range: a floor loosening
  made on the branch before it stays in range (`LPR-R12-001`).
- **Adoption**: two branches that each adopt from the same base both extend the
  same parent `history`, so the second squash breaks the chain check. A
  concurrent second adoption **fails closed** and is **re-adopted after updating
  from `main`**: run `/adopt-gate-policy` again on the updated branch, which
  chains onto `main`'s adoption. When the update merge conflicts on
  `gate_policy_adoption`, the resolution is stated: **take `main`'s record, then
  re-adopt**. A resolution that keeps the branch's own record chains the new
  adoption onto that record and fails the chain check on `main` after the squash.
- In both cases the failure is recoverable by one new `/adopt-gate-policy`
  commit (the range above makes it the reset point), `verify`'s `gate_policy`
  message names that remedy, and `GATE_POLICY.md` and the operator guide point
  here instead of leaving the conflict to whoever resolves it. CP1 tests both
  cases on a constructed repository (below).

**Gate-lowering events (safeguard, D-GP-ThreatModel).** An adoption **lowers a
gate** when its resolved policy is less human, or less demanding in any setting,
than the stricter of the policy in effect before it (the previous adoption, or
the default, and the recorded floor), that is `loosened_fields(before, adopted)`
is not empty. `record_gate_policy_adoption` writes the list of such fields into
the record's `lowered` (empty when it lowers nothing; the adoption's
confirmation display lists the same fields, so the user sees the lowering before
confirming). `lowered` is an **audit label, never a precondition and never read
back as truth**: `verify_gate_policy_provenance` recomputes the lowering of the
newest **adoption-changing** commit (the commit at which the adoption now in
effect arrived, whether introduced on this branch or imported by an update merge
from `main`; `LPR-R23-002`: the lowering is the one **in effect**, so an
imported adoption is never masked by an earlier one) against that commit's own
first parent (for an update merge, the branch's own side: exactly the policy the
branch was running before the import; the same `loosened_fields` over its
adopted policy, floor and the default), so a
hand-built adoption that omits or empties `lowered` is reported exactly like an
honest one. A non-empty recomputed lowering is a **gate-lowering event**, and it
stands out in three places: (1) `verify`'s `gate_policy` check is a `warn` naming
the adoption's digest, its commit and each lowered field, and a record whose
label disagrees with the recomputation is a second `warn`; (2) `next-action`'s
`policy` object, on every row that carries it, gains `gate_lowering: {sha256,
adopted_at, lowered}` while the newest adoption is a gate-lowering event
(D-GP-Rows; an existing row never carries the object, so INV-1 holds); and (3)
every automatic satisfaction's audit record (`policy_evidence`,
`acceptance_satisfaction`) copies it, so an approval given under a lowered gate
shows that in review. It is a **report**, not a block: a lowering the user chose
is legitimate (INV-6 is exactly that the user can do it), and the point is that
no lowering passes unseen.

**Honest limit, and the threat model it falls under (D-GP-ThreatModel).**
Provenance catches every edit that does not go through the named writers, in
the working tree or in a commit. It does not stop an agent that builds a commit
by hand with a self-consistent adoption record (a digest, a confirmation naming
it, a chain): the user's `/adopt-gate-policy` and a perfect hand-built forgery
are the same bytes, and no local mechanism can tell them apart, exactly as for
today's user-only gates and approval records. The record is evidence and not a
signature, and a trailer would be no stronger. **This is an accepted limit of
the threat model, not an open defect** (the user's decision of 2026-10-03,
section 11); the safeguards are that the command is `user_only` and records the
user's confirmation text, and that a forged lowering is reported as a
gate-lowering event (above); **turning human approval on is the stronger mode**
and the operator guide says so (D-GP-Trust). A second limit is
stated under "What survives a squash merge": a human setting committed and
deleted inside one squashed branch before any committing evaluation recorded it.

The policy in effect:

| situation | effective policy | `source` |
| --- | --- | --- |
| no file, no adoption, no floor | the default | `default` |
| no file, adoption verified, no stricter floor | the adopted policy | `adopted` |
| file valid, equal to the adopted policy (or to the default with no adoption), no stricter floor | the adopted policy (or the default) | `adopted` / `default` |
| file valid, otherwise | the stricter of base, floor and file; looser fields ignored | `file_tightened` if no field was ignored, else `file_loosening_ignored` |
| file absent, and the floor is stricter than the base | the stricter of base and floor | `floor` |
| file invalid | the stricter of base and floor (the default when neither) | `invalid` |
| provenance of the adoption or the floor fails | **all three gates human** | `provenance_failed` |

An invalid file never fails a command. `verify` reports a `gate_policy` check:
`pass` when no file is present or the file equals the adopted policy and no
floor is stricter; `warn` for a file that differs from the adopted or default
policy (a normal state while a policy pull request is under review), for an
ignored loosening, for a floor that is not yet recorded in a commit, and for a
floor that holds a setting the file no longer carries, naming each field;
`fail` for an invalid file and for a failed provenance. The check is
**advisory only**: it never changes `verify`'s overall status (`LPR-R2-007`).
**A residual, stated plainly:** a setting observed nowhere durable before it
vanishes is lost: a human setting written to the file and deleted again before
the file was ever committed or any committing command evaluated a gate was
never seen by the Workflow. To make a human setting durable, commit the file,
let a `/satisfy-gate` run that makes its satisfying commit record it (any gate's, after
that commit), or adopt it.
An approval or acceptance already recorded under an earlier policy stays valid
and shows that policy's digest in its evidence; a policy change is never
applied retroactively (`OD-W2-12`).

### D-GP-Gates: evaluation

`evaluate_gate(repo_root, state, work_item_id, gate_id)` returns
`{gate, mode, source, policy_digest, satisfiable, obtainable, requirements:
[{id, met, detail}]}` and writes nothing. `mode` is `human` or `automatic`;
`obtainable` names the evidence kinds that are missing or still pending and
that a reporter can supply (`functional_evidence`, `pr_review_result`), as distinct from evidence that is failed or stale-and-unfixable
without remediation. `policy_digest` is the sha256 of the canonical effective
(resolved) policy, and the evidence also records the file digest, the adopted
digest and the floor digest. The gate ids are `plan_approval`, `technical_approval` and
`acceptance`.

- A gate in `human` mode evaluates to `satisfiable: false` with the single
  requirement `human_gate`; the existing row (15, 29, 39) and command apply
  unchanged.
- `plan_approval` and `technical_approval`, in `automatic` mode, are
  `satisfiable` only when **all** of these hold:
  1. the existing wrapper (`plan_approval_gate_status` /
     `technical_approval_gate_status`) is `reachable`;
  2. the latest verdict is `APPROVE` and its recorded bundle id equals the
     recomputed one: the `EXTERNAL_APPROVE` condition of
     `resolve_approval_basis`, so a `USER_OVERRIDE` is never automatic;
  3. each policy `require` entry is met. `distinct_reviewer_models` is met
     when both ledger stages record a `reviewer_model` and the two values
     differ after normalization (lowercased, trimmed; the family is the value
     up to the first `/`, `:` or space). A family is meant to be a vendor-level
     identity, for example `anthropic/...` against `openai/...`; two models of
     one vendor declared as `anthropic/opus` and `anthropic/sonnet` are one
     family. The values are declared and unverified (`OD-W2-3`, `LPR-R16-O4`);
     when it is unmet, the `14b`/`28b` remedies are the two of D-GP-Rows (turn
     the gate human, or withdraw; D-GP-Ingest states the set once);
  4. `review_evidence_audited` (always required in automatic mode): each of
     the two ledger stages carries the audit keys of D-GP-Trust
     (`verdict_sha256`, and `run_ref` when the reporter gave one). A stage
     recorded without them (it was recorded while its gate was human) is unmet,
     with the executable remedies of D-GP-Ingest (turn that gate human, which
     is immediate, or withdraw and re-review); it is never wrongly met. It can
     arise only for an entry recorded while its gate was human, because every
     ingest under an automatic gate writes the keys by construction.
- **Governing versions (`LPR-R4-005`).** The plan and technical gates read
  the two-stage ledger, so each can be automatic only where that ledger
  exists. The acceptance gate reads no ledger (D-GP-Acceptance), so it is
  automatic for every governing version. The gate is always human, whatever
  the policy says, where the table says so; the compatibility notes state it.

  | gate | governed by `1` | governed by 2.1 | governed by 2.2 | catalogue rows (D-GP-Rows) |
  | --- | --- | --- | --- | --- |
  | `plan_approval` | always human (no ledger) | policy | policy | `14a`, `14b` (2.1 and 2.2) |
  | `technical_approval` | always human | always human (no implementation ledger) | policy | `28a`, `28b` (2.2) |
  | `acceptance` | policy | policy | policy | `38e` to `38i` (every version, after `38b` and `38c`) |
- `acceptance` is evaluated by D-GP-Acceptance.

**The ledger records the audit keys, and the reviewer model only for an
automatic gate that requires it.** A ledger entry written while its gate is automatic gains the optional
keys `verdict_sha256` (the sha256 of the verdict's own bytes, which the
recording writer has in hand) and `run_ref` (D-GP-Trust); while its gate is
human the entry is exactly 2.7.0's bytes (INV-1). The verdict header gets an
optional `Reviewer model:` line, parsed by
`parse_review_feedback_header` into `reviewer_model`. `/review-plan` and
`/review-implementation` write it from the reviewing session's own declared
model family, and `record-external-result` carries a manual verdict's line
through, **only when that stage's gate is `automatic` and its effective
`require` lists `distinct_reviewer_models`** (the same mode condition the audit
keys use; `LPR-R16-002`); otherwise they write exactly 2.7.0's bytes (no line,
no ledger key). Because the shipped default lists the requirement, the default
(automatic) writes the line, and the all-human configuration, whose gates are
`human`, still writes none, so INV-1 holds there. The plan-stage and
implementation-stage `REVIEW_REQUEST.md` wrapper text the bundle generator
writes, and `REVIEW_PROTOCOL.md`, ask the reviewer to state `Reviewer model:`
when the gate is automatic and requires distinct models (`LPR-R16-003`), so the
pasted external verdict normally carries it. The reviewer commands' "nothing in this contract names a
model" sentence is amended explicitly to "except the `Reviewer model:` line
when the gate policy requires distinct reviewer models" (`LPR-R1-005`).
`distinct_reviewer_models` is unmet, never wrongly met, for a verdict that
stated none.

**The declared form, and header-only parsing (`LPR-R17-O1`, `LPR-R17-O2`).**
The requested form is `Reviewer model: <vendor>/<model>`, for example
`anthropic/claude-opus-5-5`; `/review-plan`, `/review-implementation` and the
wrapper text ask for exactly that, and the reviewer commands write it with the
vendor prefix of the session's own model. A bare model id still parses (its
family is the whole token), so two bare ids differ and pass as two families; the
guide states that the vendor prefix is the form that makes "family" mean a
vendor. `parse_review_feedback_header` reads `Reviewer model:` header-only, in
the same way as `review_content_id`: only within the leading header block, never
from a body line, so a verdict without the header line that quotes the text in
its body declares nothing (CP2 tests it with a body-quoted line).

### D-GP-Ingest: a missing or equal family is refused while the stage is still open (`LPR-R17-001`)

The two ledger stages are recorded at phases that no later command can
re-enter: `/record-manual-plan-review` accepts only
`AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` and `/record-manual-implementation-review`
only `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`
(`payload/scripts/workflow_state.py:15200`), and the only route back from
`AWAITING_PLAN_APPROVAL` is the ready-phase withdrawal `/milestone-plan <id>`,
which discards both stages and consumes the reviewed content. This design
therefore **chooses one remedy, once: catch it at ingest.** No new transition,
action id or edge is added.

- **The refusal.** When the stage being recorded has its gate `automatic` and
  its effective `require` lists `distinct_reviewer_models`, the manual-stage
  ingest writers (`/record-manual-plan-review`,
  `/record-manual-implementation-review`, and `record-external-result` where it
  carries a manual verdict) refuse an **`APPROVE`** verdict that (i) states no
  `Reviewer model:` header line, or (ii) states a family equal, after
  normalization, to the other stage's recorded family when that stage is already
  recorded. The refusal is raised before any write: `WORKFLOW_STATE.json` stays
  byte-identical, the phase stays at the open manual-review phase, and no ledger
  entry is written. Its message names the missing or equal value and the remedies of the next
  bullet. A `REVISE` or `BLOCK` ingest is admitted unchanged (it records no
  approval and needs no family).
- **The remedies work at that phase.** (1) Re-submit the same ingest with a
  `Reviewer model:` line of a second declared family. (2) Turn that gate human
  (`"human_approval": true` for the gate), which is immediate (an uncommitted
  edit, so `HEAD` does not move); the same ingest is then admitted with no
  line, as 2.7.0 wrote it. Adopting a policy without the requirement through
  `/adopt-gate-policy` is **not** a remedy at this phase (`LPR-R18-001`): its
  commit moves `HEAD` past the open bundle's `generation_head`, and the
  re-submitted ingest would then be refused by 2.7.0's generation check
  (`WorktreeOrHeadMismatchError`, D-GP-Policy, "Bundle generation"). It is
  advice for before the stage's bundle is generated. The local stage never
  needs the refusal: `/review-plan` and `/review-implementation` write the line themselves for an
  automatic gate that requires it.
- **`review_evidence_audited` needs no ingest refusal.** An ingest under an
  automatic gate writes `verdict_sha256` (and `run_ref` when given) by
  construction, so it cannot leave that requirement unmet. It is unmet only for
  an entry recorded while its gate was human, and that case is the in-flight
  one below.
- **Under all-human nothing changes (INV-1).** A human gate has no refusal, no
  line and no key.
- **What remains after the stage is closed (the in-flight and the later-change
  cases).** `14b`/`28b` still fire when a ledger was recorded before the gate
  was automatic (an in-flight 2.7.0 item updated at `AWAITING_PLAN_APPROVAL` or
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`), or when the policy changed after
  the ingest. At that point no command can re-record a stage, so the rows name
  only remedies that are executable there: turn that gate human (immediate;
  `/approve-review plan` or the technical approval then proceeds), or **the
  withdrawal that it really is**: `/milestone-plan <id>` at plan stage, or the
  implementation stage's own bundle withdrawal and regeneration, then an edit
  that regenerates, then both review stages again, with the reviewed content
  consumed. The documents recommend the first for an in-flight item.

### D-GP-Satisfy: automatic satisfaction of the plan and technical gates

A new command, `/satisfy-gate <plan|implementation|acceptance> [id]`, is
**not** `user_only`. It is the action behind the `validation` disposition: an
automated validation the Workflow performs, run by a worker like an
`automatic` action. This section covers `plan` and `implementation`;
`acceptance` is D-GP-Acceptance.

- `plan` runs `/approve-review`'s step 0 (the dual-mode version branch, which
  refuses an unknown governing version) and steps 1 to 6d unchanged except for
  the points below (`LPR-R1-003`). `implementation` runs step 0, steps 1 to 4
  and the implementation-stage branch of step 6 (steps 4a to 6d are plan stage
  only; the technical stage uses the same direct
  `apply_technical_approval`/`state_transaction` write and plain `git commit`
  with the `Workflow-Technical-Approval` trailers, its post-commit validators
  `validate_technical_approval_commit` and `verify_post_approval_manifest_match`
  and ledger row `I21` sitting in that paragraph), adding the
  `Workflow-Gate-Satisfied-By` trailer in its final paragraph. Step 7 is the
  report and is restated for the automatic path (`LPR-R3-005`). Step 3 is
  `resolve_approval_basis`, which cannot be reused: it calls
  `validate_user_confirmation` (work item id and stage required in the text)
  and returns only `EXTERNAL_APPROVE` or `USER_OVERRIDE`. It is replaced by a
  new `resolve_policy_approval_basis(state, work_item_id, stage, evaluation)`,
  which keeps `resolve_approval_basis`'s `pinned_block` and `BLOCK` refusals,
  requires the `EXTERNAL_APPROVE` condition (never `USER_OVERRIDE`) and
  returns `POLICY_SATISFIED`. The user-only guard and `user_confirmation` are
  replaced by the policy evaluation, which must be `satisfiable`; the record
  carries `policy_evidence`. Every other cited step that branches on basis or
  confirmation has its automatic-mode behavior written out in the command
  text, not only these points. The command text cites `/approve-review`'s
  steps by number and adds only those differences, so there is one
  transaction (`OD-W2-11`). The plan stage keeps the journaled commit with its
  trailers, and adds `Workflow-Gate-Satisfied-By: policy:<digest first 12>`.
  The technical stage's commit carries the same added trailer; CP2 confirms
  that `validate_technical_approval_commit` admits a record that carries
  `policy_evidence` and `POLICY_SATISFIED`.
- `POLICY_SATISFIED` is added to `APPROVAL_BASES`. `validate_approval_record`
  requires, for it, `policy_evidence` and an `approved_review_content_id`, a
  `reviewed_bundle_id` and a manifest (as for `EXTERNAL_APPROVE`), and
  `user_confirmation` set to the literal `policy:<digest>` (never text that
  claims a person), validated by a dedicated
  `validate_policy_satisfied_confirmation(value, policy_digest)` that checks
  the literal equals `policy:` plus the record's `policy_evidence.policy_digest`.
  `APPROVAL_STAGES` stays the approval-record vocabulary (no `gate_policy`
  stage is added), and an approval record with `stage="gate_policy"` is
  refused. `policy_evidence` is `{policy_digest, policy_source, file_digest,
  adopted_digest, adopted_at, requirements: [{id, met, detail}], inputs:
  {review_content_id, ledger: {local: {...}, manual: {...}},
  gate_status_digest}, floor_digest, trust, evaluated_at, workflow_release}`
  (INV-4). Each `ledger` entry carries the stage's `bundle_id`, `verdict`,
  `round`, `verdict_sha256`, `ledger_entry_sha256` and `run_ref`, and `trust`
  is the D-GP-Trust statement (`review_verdicts: orchestrator`), so a record
  names the verdict hash, the bundle and content ids and the producing run.
- **Order of the floor (`LPR-R18-001`).** The command evaluates against the
  virtual floor and records nothing before its satisfying commit. After that
  commit, if the committing evaluation observed a setting stricter than
  `gate_policy_floor`, it records the floor in its own floor commit
  (D-GP-Policy, "Bundle generation"); a refused or `blocked` run records and
  commits nothing, so it never moves `HEAD` past an open bundle. The cost is
  stated: a human setting is recorded by the next satisfying run of any gate (or
  by an adoption), not by a run that was refused because that very gate is human,
  so the stated residuals (a setting never observed durably) widen only by that
  window. If the floor commit or its validator refuses **after** the satisfying
  commit (`LPR-R19-O3`), the approval stands and is reported as done, the floor
  stays virtual (every later evaluation recomputes it), the next committing
  evaluation records it, and the report names the failed floor commit and its
  cause.
- The command re-evaluates the policy inside the state transaction. If the
  evaluation is no longer `satisfiable` (for example a human toggle was turned
  on meanwhile) it refuses and writes nothing.
- `/approve-review` keeps working, unchanged, as the human path for every
  gate in either mode (INV-5).

### D-GP-ThreatModel: the threat model of this release's guarantees

The user decided (2026-10-03, section 11, option A) the threat model, and this
section is the one place that states it; INV-6, INV-9, D-GP-Policy's honest
limit, D-GP-Trust, the operator guide (`GATE_POLICY.md`, CP7) and the risks
table refer here.

**The threat model is the one today's human gates already have.** An agent
running on the same machine as the user can write any file, make any commit and
install any program. No local mechanism can therefore tell the user's
`/adopt-gate-policy` from a perfect hand-built forgery of its commit, or the real
`gh` from a fake one; today's user-only gates (`/approve-review`,
`/accept-milestone`: `disable-model-invocation` plus the confirmation text) have
exactly this limit, and this release does not pretend to remove it.

**What 2.8.0 guarantees.** INV-5, INV-6 and the GitHub-sourced facts hold
against **an agent acting through the Workflow's commands and protocol**: one
that runs the commands and the `record-external-result` ingest, edits the policy
file and the working tree, and reports evidence, but does not deliberately forge
commits, trailers or state by hand or replace system programs. Against that
agent the plan's mechanisms (the tighten-only effective policy, the floor, the
content and chain provenance, the Workflow's own forge query) are what stop a
loosened gate and a fabricated CI fact.

**What it does not guarantee.** It does not hold against an agent that
**deliberately forges** a commit, a trailer or the state (a self-consistent
adoption record, a hand-built commit), or **replaces a system program** (a `gh`
or `git` earlier on `PATH` or placed in a directory it controls). Nothing the
Workflow can check locally distinguishes such an act from the user's own, and
this release adds **no** signed commits and **no** GitHub-side adoption: those
are not part of the decision. The two Blocking findings of the round 2 external
review (a forged adoption that lowers a human gate; a `gh` executable the agent
supplies) are resolved by this statement plus the cheap safeguards below, not by
a cryptographic or GitHub-side mechanism.

**The safeguards that remain, so a forgery is harder and never silent.**

1. **`gh` resolution** (D-GP-Trust): the Workflow resolves `gh` to an absolute
   path and refuses (`forge_undecidable`, so the gate blocks) when it resolves
   inside the repository, any of its worktrees, the temporary directory or a
   world-writable directory; the GitHub fact records the resolved path and the
   executable's sha256.
2. **Gate-lowering events** (D-GP-Policy): every adoption that lowers any gate is
   flagged in its audit record and reported by `verify` and `next-action`, so a
   lowering, forged or real, stands out in review.
3. The existing evidence trail (INV-4), the `user_only` flag and confirmation on
   `/adopt-gate-policy`, and **human approval as the stronger mode**.

### D-GP-Trust: who is believed, and what the Workflow guarantees

The user decided (2026-10-03, section 11) where each kind of evidence comes
from. The Workflow cannot tell a deterministic orchestrator from an agent that
calls the same command, so each fact has one defined source and the trust it
carries is stated, not implied. Every row below is stated under the threat
model of D-GP-ThreatModel (an agent acting through the commands and protocol,
not one that forges state by hand or replaces system programs).

| evidence | source | trust | what the Workflow checks and records |
| --- | --- | --- | --- |
| CI result and pull-request facts that **satisfy** a gate (state, head, review decision, checks) | **GitHub**, queried by the Workflow itself inside the satisfying command's transaction, never an agent's word | the forge | the fact is parsed from GitHub's own JSON by Workflow code, bound to the exact head and repository, and carries its provenance (`workflow_gh`) |
| a pull-request fact an orchestrator reports (`orchestrator_forge`) | the orchestrator's forge module | **tighten-only** | recorded; it can only trigger the Workflow's own query, and never decides PR state, actionability, a reopening or completion; it never satisfies `pr_fact_current`, `ci_green` or `pr_approved` (`LPR-R28-001`) |
| review verdicts, local and external | the reviewing session or the orchestrator that reports them | **trusted from the orchestrator** | binding to the bundle id and `review_content_id`, freshness, and the audit keys below; **not** that a review happened |
| functional evidence | the orchestrator that ran the flow | **trusted from the orchestrator** | the identity recomputed at `head`, the flow id, the digest and the run reference; **not** that the suite ran |
| the policy file, the adoption and the floor | the repository | verified by content and by the chain of their changes (D-GP-Policy), which survives a squash merge | provenance, fail closed |

**The Workflow guarantees binding, freshness and audit. It does not guarantee
provenance for review verdicts or functional evidence.** An agent able to
drive the non-user-only commands can report such evidence; every automatic
satisfaction therefore leaves a trail that a person can check afterwards
(INV-4), and **turning human approval on is the stronger mode**: it puts a
person between the evidence and each gate it is turned on for. The operator
guide (`GATE_POLICY.md`) says this in those words (CP7).

**The audit trail of every automatic satisfaction.** The record
(`policy_evidence`, `acceptance_satisfaction`) holds, for each review verdict:
the verdict's own sha256 (`verdict_sha256`), the sha256 of the ledger entry,
the bundle id and the `review_content_id`; and a reference to the producing
run's log, `run_ref`, as the reporter gave it. A reporter through the protocol
supplies `run_ref` (its own run or log identifier); a standalone session
records `session:local` and the path of the feedback artifact. `run_ref` is
declared, never verified, and an absent one is recorded as `null` and shown by
`verify`'s `gate_policy` check as a warning. For functional evidence it holds
the record's `log_digest`, `reporter` and `run_ref`; for forge facts the
provenance below, including the resolved `gh_path` and `gh_sha256`; and, when
the newest adoption is a gate-lowering event, its `gate_lowering` (D-GP-Policy).

**Where CI and pull-request facts come from (`LPR-R9-002`).** The Workflow
cannot authenticate who submitted a `record-external-result` input: the command
is not user-only, and a `raw` block is JSON anyone can write and hash. A
`sha256(raw) == raw_sha256` check therefore proves integrity, not origin. So the
two sources differ in what they may do, and **only the first can satisfy a
gate**:

1. **The Workflow's own query (satisfies and tightens).** `/satisfy-gate
   acceptance` (and `/accept-milestone`'s step 2a, for a human acceptance with
   `requires_pr_approved`) runs, **inside the state transaction that would
   satisfy the gate**, one fixed, built-in `gh` invocation for the exact commit
   and repository. The argv is a constant in `payload/scripts/workflow_forge.py`,
   run without a shell and with a timeout of 30 seconds: `gh pr list --repo
   <owner>/<name> --state all --search <40-hex commit> --limit 200 --json
   number,url,state,headRefOid,reviewDecision,reviews,statusCheckRollup`.
   **The result limit is explicit (round 15's Important finding, section 11, mirroring the
   Controller's `controller/forge.py`, `PR_LIST_LIMIT`):** `gh pr list`
   truncates at `--limit`, so a result of **200 or more** records is a full page
   and is `forge_undecidable` (more matching pull requests may exist than were
   listed; a green match could otherwise be taken as unique while a red one is
   omitted). `FORGE_PR_LIST_LIMIT = 200` is a constant beside the argv, and
   `parse_forge_raw`, the one parser both sources use, applies the same refusal
   to an orchestrator's `raw`.
   **Which `gh` runs (safeguard, D-GP-ThreatModel).** The executable is not
   looked up by name at run time. `resolve_gh(repo_root)` takes the first `gh` on
   `PATH` (`shutil.which`), resolves symlinks (`os.path.realpath`) and refuses,
   naming `forge_undecidable` and the path, when the resolved executable or its
   directory is **inside the repository, inside any worktree** (`git worktree
   list --porcelain`), **inside the temporary directory** (`tempfile.gettempdir()`,
   `TMPDIR`, `/tmp`, `/var/tmp`, `/dev/shm`) or **in a world-writable directory**
   (or is itself world-writable). A `gh` that is not found at all stays
   `forge_unavailable`. The query then runs that **absolute path**, never the
   bare name, and the stored fact's provenance records `gh_path` (the resolved
   path) and `gh_sha256` (the executable's sha256, computed at resolution), so a
   review can see which program answered. This stops a `gh` placed in the
   repository, a worktree or a temp directory by an agent working through the
   commands; it cannot stop one that replaces the real `gh` or a program in a
   directory only the user could write to, which is the stated limit of
   D-GP-ThreatModel.
   `<owner>/<name>` is parsed from `git remote get-url origin` and must be a
   `github.com` repository matching `^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$`; the
   commit is the item's anchor commit (D-GP-Invalidation). This is **not** a
   command named in a repository file, so `OD-W2-4` holds: nothing in the
   repository chooses or alters it, and no policy option can. Its result, parsed
   by `parse_forge_raw`, is the **only** input `pr_fact_current`, `ci_green` and
   `pr_approved` are evaluated on. It is stored as the item's PR fact with
   provenance `workflow_gh` (also when the gate is refused, so a red answer can
   reopen the item and a poll does not loop; a query that finds no pull request
   stores `state: none`). The store reopens only on `acceptance.satisfy`'s path;
   `pr.apply_review` started at `MILESTONE_COMPLETE` stores the same fact
   without the ingest-time reopen (D-GP-Reopen, `LPR-R26-001`).
2. **An orchestrator's forge fact (tighten-only, one principle, `LPR-R28-001`).**
   `record-external-result
   --kind pr_review_result` accepts a fact only when it carries the `forge`
   provenance block of D-GP-Invalidation (the verbatim output of that same
   query, its sha256, the repository, the queried commit, the time and the
   fetching component). The Workflow parses the verbatim output itself and
   derives every field from it. Because the origin of that block cannot be
   verified, the stored fact (`source: orchestrator_forge`, `fetched_by`) is
   governed by one principle, which replaces every earlier source-priority rule
   (rounds 4 to 6 each patched which source's PR state wins, and each patch
   opened the mirror-image gap; the principle follows from the user's
   2026-10-03 decision that orchestrator facts are tighten-only):

   1. **An `orchestrator_forge` fact never decides.** It never decides PR state,
      actionability, a reopening, completion or acceptance. It is recorded (in
      its own slot, with a Workflow-assigned `ingest_seq`) and it can only
      **trigger** the Workflow's own fixed `gh` query; it can never suppress one.
   2. **Every decision reads `workflow_gh` facts only.** Actionability (the
      shared predicate `pr_key_actionable`), the reopening, row `38d`, rows
      `38e` to `38i` and the acceptance requirements are all computed from the
      `gate_evidence.pr` fact (provenance `workflow_gh`) and nothing else. No
      predicate reads the `state`, head or keys of a reported fact, and no
      predicate compares the two sources' PR states.
   3. **The query trigger, defined once (`LPR-R29-001`): `pr_query_trigger`.**
      The trigger is evaluated on the two slots as wholes, never per PR number.
      It holds exactly when `pr_review.enabled` **and** the `pr_reported` slot
      holds a fact whose `ingest_seq` is **greater than the `pr` slot's** (or the
      `pr` slot is empty) **and** that reported fact's PR number, `state`, `head`,
      `review_decision`, `reviewed_head`, `checks` or cause keys differ from the
      `pr` fact's (an empty `pr` slot, or a `pr` fact of `state: none`, differs
      from any reported fact). Where `D-GP-Invalidation`, `D-GP-Acceptance`,
      `38d` and `pr.apply_review` say the trigger, they mean this predicate and
      no other, except that the acceptance rows' broader "any newer report" rule
      adds a query and never decides (D-GP-Acceptance). The trigger makes the
      next step a **fresh Workflow query before any decision**, at any phase `38d` or `38f`-`38h` evaluates,
      **including `MILESTONE_COMPLETE`**, through the existing query action or
      row: `pr.apply_review` at row `38d` (D-GP-Rows, D-GP-Reopen) or
      `acceptance.satisfy` at row `38h`. This covers a reported `open` (a reopen)
      after a Workflow-observed `closed`, and a reported `merged` or `closed`
      after a Workflow-observed `open` red key, in the same way: in both the
      report only causes the query, and the query's `workflow_gh` fact decides.
      A reported fact that equals the stored `workflow_gh` fact in all of those
      fields triggers nothing at `38d`. **Any successful Workflow query clears
      the trigger, whatever it returns** (the same PR, a different PR number, a
      replacement PR, or `state: none`): the query stores a fact in the `pr` slot
      with an `ingest_seq` greater than the report's, so the first clause fails
      and the trigger cannot hold again until a newer report arrives. One report
      therefore triggers **at most one successful query** and nothing loops. The
      query's `queried_commit` is the item's anchor commit by construction; the
      ingest of a reported fact does not require its `queried_commit` to equal
      the anchor, and nothing depends on it.
   4. **When `gh` is unavailable the trigger blocks, never resolves to
      "nothing to do".** The query refuses (`forge_unavailable`, or
      `forge_undecidable`) and stores nothing, so the trigger still holds at the
      next evaluation and `38d` emits the action again, bounded by the
      consumer's retry bound and then `blocked` with the remedy; the item is
      never reported `complete`, never offered row 39, and never reopened or
      accepted from the reported fact.

   It also **never displaces a stored `workflow_gh` fact** (separate slots,
   D-GP-Invalidation, `LPR-R10-002`). It can **never satisfy** a requirement: a
   stored `orchestrator_forge` fact is treated as absent by `pr_fact_current`,
   `ci_green` and `pr_approved`, with any age, so a fabricated all-green `raw`
   achieves nothing. There is no `FORGE_FACT_MAX_AGE_SECONDS`: nothing relies on
   how fresh an unauthenticated fact is. The Controller's forge module
   (`controller/forge.py`) is the intended supplier; what an orchestrator
   misreports can cost one extra query or, with `gh` unavailable, a block, which
   is the safe direction, and the fact's provenance names it.

**Fail closed when `gh` cannot decide.** The Workflow's own query refuses, writes
nothing and the act's refusal names `forge_unavailable` (a refusal result the
consumer reconciles as `no_progress`, never a durable `blocked` decision; the gate
does not pass, `LPR-R12-003`) when `gh`
is not installed or not authenticated, exits non-zero, times out, prints
something that is not the expected JSON, names a repository other than this
one, or when more than one open pull request carries the commit, the result is a
full page of 200 or more records, or the resolved `gh` is inside the
repository, a worktree, the temporary directory or a world-writable directory
(`forge_undecidable`). A pull request that does not exist is not undecidable:
it is an unmet requirement (`pr_fact_current`) with the remedy to open it. An
unavailable `gh` never falls back to anything: a stored orchestrator fact does
not stand in for the query, so with `gh` unavailable the gate does not pass (the act refuses), whatever
facts an orchestrator has reported.

### D-GP-Acceptance: automatic milestone acceptance and its evidence

`OD-W2-5` becomes the evidence mode. Acceptance is `automatic` unless its
toggle makes it human. In `automatic` mode, `evaluate_gate('acceptance')` is
`satisfiable` only when **all** of these requirements hold, each recomputed at
evaluation time from the state and the repository, never read back from an
earlier record (and the pull-request requirements, 4 to 6, only from the
Workflow's own GitHub query run in that same evaluation, D-GP-Trust; a
read-only evaluation that cannot run it treats them as *pending the query*, below):

1. `checkpoints_complete`: the item's own registry is terminal (every
   checkpoint `COMPLETE`), the same `resolve_own_registry_completion_status`
   the human pre-flight calls (step 2a). Rows 38a to 38c already stop an
   unreadable or non-terminal registry earlier.
2. `technical_approval_current`: the item has a technical approval and
   `approval_is_current` holds for it (its recorded content identity equals the
   identity recomputed now). The **anchor** (D-GP-Invalidation) is that
   approval's commit.
3. `functional_flows_passed`: the item has at least one recorded functional
   flow (D-GP-Evidence) whose identity is current at the anchor, every such flow
   `passed`, and every `required_flows` entry present and passed. Functional
   evidence is trusted from the orchestrator (D-GP-Trust).
4. `pr_fact_current` (always required, **I1**): a **`workflow_gh`** pull-request
   fact exists (D-GP-Trust: the Workflow's own query; an `orchestrator_forge`
   fact never counts) for the item's **current approved implementation head**: its
   `state` is `open`, its `head` descends from the anchor commit (the anchor is
   `head` or an ancestor of it) and the implementation identity computed at its
   `head` equals the anchor identity. A fact for an **older** head (*behind*) or
   for different protected content (*ahead*) does not satisfy it: the gate
   blocks, with the remedy to push and re-run `/satisfy-gate acceptance`. A red or
   `CHANGES_REQUESTED` fact on an older head therefore cannot be ignored while a
   local fix is approved but unpushed.
5. `no_standing_pr_objection` (always required, applied to that same fact): its
   `review_decision` is not `CHANGES_REQUESTED` and its `checks.state` is not
   `failure`. The decision is read as GitHub reports it, without the
   `reviewed_head` softening the reopening cause uses, so a pushed fix stays
   blocked until the reviewer approves or dismisses (including after a no-code
   `/apply-pr-review` branch, which marks the finding dealt with but does not
   clear the objection).
6. `ci_green` (when `require_ci`, default true) and `pr_approved` (when
   `requires_pr_approved`): on the same fact, `checks.state` is `success`
   (`ci_green`; the fact's checks are the CI evidence, so there is no separate
   CI report) and `review_decision` is `APPROVED` (`pr_approved`). A `pending`
   or `failure` check blocks acceptance whether or not `reopen_on` lists
   `checks_failed`; `reopen_on` only controls whether a failure reopens.

**Pending the query.** `next-action` and `verify` never run `gh` (they are
read-only and must stay deterministic). For requirements 4 to 6 they read the
item's stored PR facts: a stored `workflow_gh` fact is evaluated as above
**unless a reported (`orchestrator_forge`) fact is newer than it**; with **no**
`workflow_gh` fact, or with a reported fact whose `ingest_seq` is greater than
the stored `workflow_gh` fact's (`LPR-R11-001`), the three are *pending the
query*, which does not make the gate `satisfiable` by itself but lets row `38h`
emit `acceptance.satisfy`, whose act runs the query, **stores a fresh
`workflow_gh` fact (also when it refuses)** and then satisfies or refuses. That
fresh fact carries a greater `ingest_seq`, so each report triggers **at most one
successful query**: until the next report, `38f`/`38g` (or `38i`) read the stored
fact and nothing loops. This is the acceptance-side instance of the query trigger
(D-GP-Trust principle 3, `LPR-R28-001`): row `38d` is evaluated first and, when
the policy enables PR review and the reported fact differs from the stored
`workflow_gh` fact, runs the query through `pr.apply_review`; the acceptance rows
keep the broader rule that **any** newer report is pending the query, which only
ever adds a query (tighten-only) and never decides. **A failed query (`gh` unavailable, `LPR-R12-003`) stores
nothing**, so the requirements stay *pending the query* and `next-action`, which
never runs `gh`, emits `38h` again. The stated contract: the act's refusal names
`forge_unavailable` (or `forge_undecidable`) and its remedy (install or
authenticate `gh`, or turn acceptance human); `reconcile` classifies it
`no_progress`; and retrying is the consumer's job (advice: CP7 adds a recommendation to the spec's consumer obligations that a `1.1` consumer bound its consecutive `no_progress` results of the same action id at an unchanged `state_identity`, `LPR-R14-001`; protocol section 8 defines no such limit today). No durable `forge_unavailable` marker exists, so
`gate_evidence` gains no field. Only the act, inside its transaction, can make the
gate pass.

Beyond these, the command is subject to every refusal of the human path
(INV-5): `complete_work_item` still refuses an incomplete child, an outstanding
checkpoint and an unsatisfied completion obligation (step 2a). Because
requirement 4 is always required, **automatic acceptance needs an open pull
request before it runs** (`OD-W2-18`); `GATE_POLICY.md` states the order, and
this repository's own flow (section 7, pull request after acceptance) therefore
keeps acceptance human.

**What counts as the exact head (`OD-W2-14`).** Evidence is bound by identity
(INV-3): its `head` must resolve, local `HEAD` must contain it, and the
implementation `review_content_id` computed at it equals the anchor identity
(for a pull-request fact, additionally descending from the anchor, requirement
4). A
commit that changes only excluded paths (the roadmap, the functional-checklist
evidence commit) does not stale it; a commit that changes protected
implementation content does. A literal-`HEAD` rule would stale functional evidence on
every bookkeeping commit.

**The act.** `/satisfy-gate acceptance` runs `/accept-milestone`'s steps 0, 2,
2a, 2b and 3 to 8 unchanged (cited by number, `OD-W2-11`), with these
differences. Step 1 (the user-only guard) is replaced by the evaluation above,
re-run inside the state transaction **with a fresh run of the Workflow's own
query** (D-GP-Trust, source 1); if it is no longer `satisfiable` the command
refuses and writes nothing, except that it stores the `workflow_gh` fact it read
(a successful query only; D-GP-Trust). In the same mutator that calls
`complete_work_item` it writes the item's `acceptance_satisfaction` record:
`{policy_digest, policy_source, file_digest, adopted_digest, floor_digest,
requirements: [{id, met, detail}], inputs: {anchor_commit, anchor_identity,
technical_approval, functional: {flow_id: {evidence_id, log_digest, run_ref}},
pr: {fact_id, head, provenance: workflow_gh, raw_sha256}}, trust, evaluated_at,
workflow_release}` (INV-4), so a refusal by `complete_work_item` leaves nothing
written. The completion commit (step 6) carries
`Workflow-Gate-Satisfied-By: policy:<digest first 12>` beside the work-item
trailer, in the final paragraph.

**The human path.** In `human` mode `/accept-milestone` is exactly today's
user-only command, plus one added precondition at step 2a when
`requires_pr_approved` is true: the `pr_approved` part of requirement 6 above, on
a fresh `workflow_gh` fact from the Workflow's own query (requirement 4); with
`gh` unavailable that pre-flight refuses (`forge_unavailable`). Step 2a **stores
the `workflow_gh` fact it read** (a successful query only, also when it then
refuses), exactly as `/satisfy-gate` does, so the item's stored fact is then at
least as new as any earlier report (`LPR-R12-002`). The library predicate
`evaluate_gate('acceptance')` is shipped and tested in CP4, with the command
wiring in the same checkpoint (`LPR-R2-005`).

**An automatic gate with unmet evidence is blocked, never passed (INV-5).**
D-GP-Rows names the decision each unmet requirement produces.

### D-GP-Evidence: `functional_evidence`

`record-external-result --kind functional_evidence --input FILE` ingests one
flow's result from the orchestrator:

```json
{"flow_id": "migration-suite", "status": "passed",
 "head": "<40 hex>", "ran_at": "<UTC time>",
 "summary": {"passed": 120, "failed": 0, "skipped": 2},
 "log_digest": "<64 hex>", "run_ref": "<the producing run's log id>",
 "reporter": "controller"}
```

Functional evidence is **trusted from the orchestrator** (D-GP-Trust, INV-9):
the Workflow binds it and records its audit keys, and cannot prove the suite
ran. There is **no CI result kind**: the CI outcome is the `checks` of the
`workflow_gh` pull-request fact (D-GP-Invalidation), so the only evidence kinds
are `functional_evidence` and `pr_review_result`. Functional or review
evidence **produced in CI** is not accepted, and no policy option offers it
(the user's decision, section 11).

- The Workflow recomputes the implementation `review_content_id` at `head`
  (`approval_review_content_id` with `head`), requires `head` to resolve in the
  repository and local `HEAD` to contain it (`evidence_head_unknown`,
  `evidence_head_not_in_branch`), and stores the record under the item's new
  `gate_evidence.functional[<flow_id>]` (the latest per flow), with the identity
  it computed. The identity is the Workflow's, not the reporter's (INV-3).
- A record is **current** when the identity computed at its `head` equals the
  identity at the **anchor** (D-GP-Invalidation) and its `status` is `passed`.
  A later commit that changes protected implementation content makes it stale;
  one that changes only excluded paths does not.
- A flow id the policy does not list is still recorded, and counts toward
  `functional_flows_passed` (every current recorded flow must pass). A failed
  run is recorded and makes the gate unmet. A flow re-reported at a current head
  replaces the earlier record of the same id.
- **What no policy can know.** With `required_flows` empty the gate requires
  at least one current passing flow and no failing one; it cannot know which
  flows ought to exist. A repository that needs specific flows lists them in
  `required_flows`.
- Both kinds are accepted under **every** policy, including all-human
  (`OD-W2-9`). `functional_evidence` is an inert record under a human
  acceptance gate: nothing reads it. A `pr_review_result` is not inert under any
  gate mode: `pr_review` is independent of `human_approval`, so a reportable
  `CHANGES_REQUESTED` or failed-checks fact reopens the item whatever the gate
  modes (`LPR-R3-003`, decided once here; D-GP-Compat lists it as a delta that
  arises only once such a fact is reported).

### D-GP-Invalidation: pull-request facts and the stale-evidence table

`record-external-result --kind pr_review_result --input FILE` ingests a
pull-request fact **only with forge provenance** (D-GP-Trust, INV-9). The input
is the provenance block, and nothing the reporter derived from it:

```json
{"forge": {"source": "github", "query": "pr-list-v1",
           "repository": "owner/name", "queried_commit": "<40 hex>",
           "fetched_at": "<UTC time>",
           "fetched_by": {"name": "controller-forge", "version": "<v>"},
           "raw": "<the verbatim stdout of the fixed query>",
           "raw_sha256": "<64 hex>"},
 "run_ref": "<the fetching run's log id>"}
```

The Workflow checks `sha256(raw)` against `raw_sha256`, `repository` against
this repository's `origin`, parses `raw` itself (`parse_forge_raw`, the same
function the Workflow's own query uses) and **derives** the fact from it:
`{pr: {number, url}, state, head, review_decision, reviewed_head, checks:
{state, failing}, review_id, findings}`, where `head` is GitHub's
`headRefOid`, `reviewed_head` and `review_id` come from the latest review, and
`findings` is the latest `CHANGES_REQUESTED` review's text, verbatim. An input
with no `forge` block, a digest that does not match, a repository that is not
this one, or a `raw` that does not parse is refused (`forge_provenance_required`,
`forge_digest_mismatch`, `forge_repository_mismatch`, `forge_unparseable`), and
nothing is stored. **The stored fact is tighten-only (`LPR-R9-002`):** the digest
check proves the bytes were not altered after hashing, not who produced them, so
a fact stored from this input (`source: orchestrator_forge`) is recorded and can
only trigger the Workflow's own query (D-GP-Trust, `LPR-R28-001`); it feeds
neither the cause table nor the reopening, and is never read by
`pr_fact_current`, `ci_green` or `pr_approved`. A standalone session, or the act of
`acceptance.satisfy`, obtains the fact that can satisfy through the Workflow's
own query (D-GP-Trust), whose provenance is `workflow_gh`; it is stored in the
`gate_evidence.pr` slot. **One slot per source (`LPR-R10-002`):** a
`workflow_gh` fact is stored in `gate_evidence.pr` (the latest `workflow_gh` fact
wins there) and an `orchestrator_forge` fact in its own slot,
`gate_evidence.pr_reported` (the latest reported fact wins there). **The shape,
defined once (`LPR-R11-002`):** `gate_evidence: {functional, pr, pr_reported,
pr_keys: {reopened_for, applied, ingest_seq}}`. `pr` and `pr_reported` each hold
one fact with its `provenance` and an `ingest_seq`; `pr_keys` holds the two
per-item key sets and `ingest_seq`, the counter. **Every stored fact is stamped
with the next `ingest_seq`, assigned by the Workflow inside the ingest or query
transaction, never by the reporter's `fetched_at`.** Replacing either slot
**never touches `pr_keys`**, so a later `workflow_gh` query cannot drop
`reopened_for` or `applied`. `validate_state` knows all four keys and
rejects any other. An
orchestrator fact therefore **never displaces or hides** a `workflow_gh` fact:
the cause table's actionability, `38d`, `pr_fact_current`, `ci_green`,
`pr_approved` and rows `38f`/`38g` read **only** `gate_evidence.pr`, and
`gate_evidence.pr_reported` is read only by the query trigger (D-GP-Trust,
`LPR-R28-001`). A key exists for the cause table only when a `workflow_gh` fact
yields it, so `pr_keys` holds only keys of Workflow-queried facts.
Red `workflow_gh`, then a self-consistent all-green `orchestrator_forge`: `38d`
still emits `pr.apply_review` for the red key (it reads the `workflow_gh` fact)
and a human is not offered row 39.
The stored record keeps `provenance: {source: workflow_gh |
orchestrator_forge, fetched_by, fetched_at, raw_sha256, run_ref}`; a
`workflow_gh` record also carries `gh_path` and `gh_sha256` (D-GP-Trust), and its
validator requires both.

`state` is `open`, `closed` or `merged`; `review_decision` is `APPROVED`,
`CHANGES_REQUESTED`, `REVIEW_REQUIRED` or `null`; `checks.state` is `success`,
`failure` or `pending` (`pending` also when any check is still running).
When `raw` holds more than one open pull request for the commit, or 200 or more
records (a full page, D-GP-Trust), the ingest refuses `forge_undecidable`.

**The anchor, defined once (`LPR-R1-002`).** The anchor is the commit of the
item's technical approval, `reviewed_content_commit`, and the anchor identity
is its `approved_review_content_id`; for an item with no technical approval it
is `reviewed_implementation_head` and the identity computed there. INV-3,
D-GP-Evidence, D-GP-Acceptance and this table all mean this anchor wherever
they say "the approved identity" or "the item's current implementation head".
A fact is **current** when the implementation identity computed at its `head`
equals the anchor identity. Precondition: `head` must resolve locally and the
local `HEAD` must contain it (`git merge-base --is-ancestor head HEAD`); the
ingest otherwise refuses with `pr_head_unknown` (does not resolve) or
`pr_head_not_in_branch` (not an ancestor; remedy: fetch and merge the PR head).
Local `HEAD` ahead of the PR head (a bounded fix not yet pushed) is legal; the
older head's fact is then *behind* the moved anchor: non-current and not
actionable **for a reopening** (see "Position relative to the anchor" below),
and **never** accepted for an automatic acceptance (D-GP-Acceptance,
requirement 4).

**One cause table (`LPR-R2-001`).** Every reopen cause has one row here; the
key definitions, `38d`'s condition and `/apply-pr-review`'s branches all read
this table and nothing else.

| cause | key (the semantic identity) | actionable when | `/apply-pr-review` branch |
| --- | --- | --- | --- |
| `content_changed` | `(pr.number, "content_changed", head, identity_at_head)` | the identity at `head` differs from the anchor identity **and** `head` is not an ancestor of the anchor commit (`git merge-base --is-ancestor head anchor` fails): the PR carries content the anchor does not | stale the technical approval, then `post-fix` on the local `HEAD`, which already contains the PR head; **no edit and no findings classification** |
| `changes_requested` | `(pr.number, "changes_requested", head, reviewed_head, review_id)` | decision `CHANGES_REQUESTED`, `reviewed_head` equals `head`, and the fact is current | classify `findings` (untrusted text): no code change, bounded fix or broad fix |
| `checks_failed` | `(pr.number, "checks_failed", head, sorted(checks.failing))` | `checks.state` `failure` and the fact is current | the same three-way classification |

**Actionability honors the policy and the PR state (`LPR-R23-001`).** The
"actionable when" column is only the *evidential* condition. A key is
**actionable** only when, in addition, all three policy conditions hold,
evaluated by **one shared predicate** (`pr_key_actionable(policy, fact, key)`)
that both the query paths that store a `workflow_gh` fact (to decide whether to reopen) and row `38d` (to decide
whether to emit `pr.apply_review`) call, never two restatements: (1)
`pr_review.enabled` is true in the policy in effect at evaluation; (2) the cause
is reopening under that policy (`content_changed` whenever (1) holds;
`changes_requested`/`checks_failed` only when listed in `reopen_on`); (3) the
PR's `state` is `open` (`closed` and unmerged: recorded only, as the
ingest table says; `merged`: refused with `pr_merged`). **The predicate reads
only the `gate_evidence.pr` (`workflow_gh`) fact, its key and its own `state`
(`LPR-R28-001`, D-GP-Trust principle 2)**; it never reads a reported
(`orchestrator_forge`) fact's state, head or keys, so there is no cross-slot
state rule and no source priority. A reported `merged`, `closed` or `open` fact
neither makes a `workflow_gh` key non-actionable nor makes a `workflow_gh`
`closed` key actionable; it can only trigger the fresh Workflow query (principle
3), which stores a newer `workflow_gh` fact that this predicate then reads.
`reopen_work_item`'s merged-PR refusal reads the same `workflow_gh` fact. A stored key that fails
the predicate stays recorded and is **never** emitted by `38d`, whether it was
stored with its fact or is a deferred fact; it becomes actionable only
if the policy or state later satisfies the predicate (for example a fresh Workflow query that
finds the PR open again, or `reopen_on` widened), and `38d` re-evaluates it on every pass
because it reads the stored key and the *current* policy, not a flag written at
ingest. **This holds at `MILESTONE_COMPLETE` too (`LPR-R24-001`)**: `38d` also
matches a completed item (see its row), so a red fact recorded while the policy
disabled its cause is acted on once the policy enables the cause, with no further
fact needed. **It never acts on a stale PR fact there** (`LPR-R25-002`): the
stored key says what was red, not whether the PR is still open, and nothing
queries the forge after completion (in this repository's own flow the PR is
merged after acceptance), so `pr.apply_review` at `MILESTONE_COMPLETE` first
re-queries the forge (D-GP-Reopen).

**Position relative to the anchor (`LPR-R3-001`).** Every fact has one of
three positions, computed once and recorded in the cause table's own helper:
*equal identity* (the identity at `head` equals the anchor identity: current),
*ahead* (identity differs and `head` is not an ancestor of the anchor commit:
new content) or *behind* (identity differs and `head` is an ancestor of the
anchor commit: an older head, as when a bounded fix is approved locally and the
PR is polled before the push). A *behind* fact is recorded and non-current, is
**not actionable** for any reopening cause, and is awaited like a new head. It
is **not ignored by the acceptance gate (I1)**: requirement 4 of D-GP-Acceptance
(`pr_fact_current`) needs a fact at a head that descends from the anchor with
equal identity, so a *behind* fact (a known red PR whose head is older than the
approved implementation) **blocks automatic acceptance** until a fact for the
current head is reported, and it satisfies neither `pr_approved` nor
`ci_green`. Only an *ahead* fact is `content_changed`.

A fact is tested against `content_changed` first: a changed identity reopens
with that cause only, and the review decision and checks on a non-current head
are not acted on. The stored fact keeps a `fact_id` (sha256 of its canonical
bytes, an audit handle only). **Consumption is keyed on the semantic key**,
never on those bytes (they include `observed_at` and verbatim `findings`). Two
separate sets are kept once per item in `gate_evidence.pr_keys`, shared by both
slots (a key is a semantic identity, not a slot): `reopened_for` (keys that
caused a reopening entry) and `applied` (keys `/apply-pr-review` has dealt
with). Re-ingesting a fact with unchanged semantic content writes **no second reopening**
(its key is already in `reopened_for`) but **is still stamped with a fresh
`ingest_seq`**, because a report is a signal to re-query: a green report after a
`pending` query result (GitHub lag) is newer than the stored `workflow_gh` fact
and so reaches `38h`, once per report (`LPR-R12-optional`). A new head, new review id or
different failing set is a new key. A review decision applies only when
`reviewed_head` equals `head`; a decision on an earlier head is outdated and
reads as `REVIEW_REQUIRED`.

**Phases at ingest, and how a recorded-only fact is acted on later
(`LPR-R2-002`, mechanism (b); restated under `LPR-R28-001`).** A reported
(`orchestrator_forge`) fact **never reopens at ingest, at any phase**: it is
recorded, stamped with its `ingest_seq`, and may arm the query trigger
(D-GP-Trust principle 3). A `workflow_gh` fact stored by a Workflow query path
that reopens (`acceptance.satisfy`'s, `LPR-R26-001`) and actionable under the
table at `AWAITING_FUNCTIONAL_REVIEW` or `MILESTONE_COMPLETE` reopens through
`reopen_work_item` (D-GP-Reopen) inside the same critical section that stores
it, **except** the fresh fact `pr.apply_review` stores, whose store suppresses
this reopen so the action's steps 2-3 make the one decision (`LPR-R26-001`). At
any other phase (for example `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` after a
post-fix, or `IMPLEMENTING`) every fact is **recorded only**: no phase change, no
staling and no refusal. (A `workflow_gh` fact stored at `MILESTONE_COMPLETE` that
is *not* actionable then, because the policy disables its cause, is likewise
recorded only, and is acted on by `38d` when the policy later enables it,
`LPR-R24-001`.) A stored fact is acted on by an explicit, read-from-state row,
not by a hidden phase hook: row `38d` (D-GP-Rows) matches (a) a stored
`workflow_gh` key that is actionable under the table and **not in `applied`**,
whether or not it is in `reopened_for`, **or** (b) the query trigger (D-GP-Trust
principle 3), and emits `pr.apply_review`. **The trigger takes precedence over a
stored key (`LPR-R30-001`):** whenever `pr_query_trigger` holds, alone or together
with (a), at either phase, the action first runs the fresh Workflow query, and the
stored key is neither reopened from nor applied before it. For (a) **alone** (no
trigger holding) at `AWAITING_FUNCTIONAL_REVIEW` that action's first step calls
`reopen_work_item` through the same writer when the key is not yet in
`reopened_for`; at `MILESTONE_COMPLETE`, and whenever the trigger holds (case (b),
with or without (a)) at either phase, the action first runs the fresh Workflow
query (D-GP-Reopen) and then
reopens when the fresh `workflow_gh` fact yields an actionable unapplied key
(the key may already be in `reopened_for` from an earlier reopening that a human
then accepted over once reopening was disabled; `LPR-R25-optional`). At
`AWAITING_FUNCTIONAL_REVIEW` the phase stays; at `MILESTONE_COMPLETE` it moves
there. The entry's `from_phase` records either phase. So a `CHANGES_REQUESTED`
fact the Workflow queried at `IMPLEMENTING` that is current at
`AWAITING_FUNCTIONAL_REVIEW` is never silently skipped, a reported fact that
differs from it is never silently skipped either (it arms the trigger), a human is
never offered row 39 over either, and no orchestrator re-poll obligation is added.

| trigger | evidence that stays | evidence that goes stale | effect |
| --- | --- | --- | --- |
| `head` changed and the implementation identity at `head` equals the anchor identity | technical approval, functional evidence, plan approval | the PR-bound facts (decision, checks) | none; new facts are awaited |
| `head` is an ancestor of the anchor commit and its identity differs (*behind*, an unpushed bounded fix) | all | the fact is non-current | recorded only; not actionable; no reopen and no `pr.apply_review`; **automatic acceptance stays blocked** (`pr_fact_current`, I1) until a fact for the current head is reported; a new head is awaited (`LPR-R3-001`) |
| `head` changed, the identity differs from the anchor identity and `head` is not an ancestor of the anchor commit (*ahead*) | plan approval | functional evidence and PR facts (non-current); the technical approval is **never staled at ingest** | cause `content_changed` (table above); technical review repeats; full functional validation repeats |
| `CHANGES_REQUESTED`, actionable under the table, and `reopen_on` includes it | — | nothing is staled yet; `/apply-pr-review` stales the technical approval before it edits | cause `changes_requested` |
| `checks.state` `failure`, actionable, and `reopen_on` includes it | — | as above | cause `checks_failed` |
| `checks.state` `pending` or `success`, decision `APPROVED` | all | none | recorded; satisfies `pr_approved` (a `workflow_gh` fact only) when both hold and the head is current at the anchor (a `pending` check still blocks `ci_green`) |
| `state` `closed`, not merged | all | none | recorded; `requires_pr_approved` blocks (`pr_closed`) |
| `state` `merged` | all | none | recorded; a reopen is refused (`pr_merged`), because the follow-up is a new work item |
| `state` `open` after `closed` (reopened PR) | as the head rules | as the head rules | a `workflow_gh` fact is handled as a new fact; a **reported** `open` after a stored `workflow_gh` `closed` arms the query trigger, so the fresh Workflow query decides, at any phase including `MILESTONE_COMPLETE` (`LPR-R28-001`) |

After a reopen, full functional validation is required once any code changed
(`OD-W2-8`). `pr_review.enabled` false records the fact and reopens nothing.

### D-GP-Reopen: reopening the same work item

`reopen_work_item(state, work_item_id, *, cause, fact, now)` is the new
writer. It is called from the PR-fact ingest's critical section and from
`pr.apply_review`'s first step (D-GP-Invalidation). It is legal from
`AWAITING_FUNCTIONAL_REVIEW` (the phase stays) and from `MILESTONE_COMPLETE`
(`OD-W2-6`), and refuses a merged PR, an item with a still-incomplete child,
and (for a `MILESTONE_COMPLETE` item) a plan path that does not resolve
(`reopen_plan_archived`, see below). It:

1. appends to the item's `reopenings` list `{n, at, from_phase, cause,
   pr_number, pr_head, fact_id, key}` and adds `key` to `reopened_for`
   (the cause is `changes_requested`, `checks_failed` or `content_changed`);
2. sets the phase to `AWAITING_FUNCTIONAL_REVIEW`, leaving the technical
   approval `CURRENT` (staling is the fix command's job, as for functional
   findings);
3. does **not** touch `active_work_item_id` (a top-level field the exhaustive
   commit validators refuse to see changed; D-GP-Compat, `LPR-R3-002`): every
   command and `next-action` call names the item explicitly.

**Archival semantics (`LPR-R2-003`).** `/accept-milestone` step 5 currently
says "Archive ... to `docs/milestones/completed/`" without saying copy or
move, and a repository that moves the plan leaves `plan_path` unresolvable, so
the post-acceptance reopen `OD-W2-6` recommends would be refused in the common
case (this repository never ran step 5, so its own evidence does not show it).
This release pins the semantics: step 5 **copies** (never moves) the plan, the
item's `plan_path`, registry and mapping stay where the state names them, and
the amended text says so (a documentation-only delta, D-GP-Compat). A
repository that already moved a plan keeps the refusal `reopen_plan_archived`,
with the remedy to restore the file from `docs/milestones/completed/` to
`plan_path`. Plan-approval currency on a reopened item reads `plan_path`, and
row `38a` reports `plan_content_drifted` on a read failure, as it does today.
A re-acceptance updates, never duplicates, the archive copy and the roadmap row
for the work item id.

**What a reopen does not undo.** The completion side effects stay: the roadmap
row stays complete and `docs/ACTIVE_MILESTONE.md` stays cleared until the item
is accepted again. `GATE_POLICY.md` says so, so an operator is not misled by
the narrative files. A reopened item completes again through the same gate,
automatic or human; `complete_work_item` is unchanged. A re-completion
overwrites `acceptance_satisfaction` (the new writer sets it in the same mutator
on every automatic acceptance). `complete_work_item` writes
`completion_obligations_accepted` only `if verdicts`
(`workflow_state.py:12700`), so a re-acceptance that declares no obligations
**keeps** the first acceptance's record rather than overwriting it, and this plan
states that as written (`LPR-R4-003`). CP5 reads `accept-milestone.md` and tests
a second acceptance for no duplicate entries.

**Durable ordering of every branch that stales (`LPR-R4-001`).** The
generation-record validators do not admit `technical_approval` in their field
sets (`ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS`,
`RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS`), and the plan does not widen them:
a `post-fix` generation-record commit must never carry the STALE write. The
existing bounded fix is durable only because its STALE write is made durable
**before** the generation commit
(`TestFunctionalReviewBoundedFixReachesRecordBundleGeneration`: the stale marking
is its own state-only commit, which becomes the generation-record commit's git
parent). `/apply-pr-review` writes the ordering out and does not rely on
`/apply-functional-review`'s text, which says "persist" in step 1 and "commit the
fix" in step 3 without saying where the state write is committed. In **every**
branch that stales (`content_changed` and the bounded fix):

1. `reopen_work_item` when needed, then `mark_technical_approval_stale`, both in
   one `state_transaction`;
2. a plain **state-only commit** of that state, staged item-scoped
   (D-GP-Compat, `LPR-R5-001`): this item's reopening, its own ingest residue and
   the STALE approval, and nothing of another item's (no trailer, as in the
   existing bounded fix, so no validator is run over it);
3. the fix commit (a bounded fix only; `content_changed` has none, the local
   `HEAD` already contains the PR head);
4. `record_bundle_generation` `post-fix` with the key added to `applied` in the
   **same** mutator, then the generation-record commit. Its field diff is the
   ordinary role's fields plus `gate_evidence`, which D-GP-Compat admits, and
   never `technical_approval`; it is staged item-scoped too.

The no-code branch stales nothing and writes only `gate_evidence.pr_keys.applied`
(this item's own residue, carried by the next commit of this item); a broad fix writes
the child and the parent's `pr_keys.applied` key, committed by the remediation child's
own commits as today. CP5 tests the `content_changed` branch's
generation-record commit with `validate_bundle_generation_record_commit` and the
technical-approval commit that follows it with
`validate_technical_approval_commit`.

**Started at `MILESTONE_COMPLETE` (`LPR-R25-001`, `LPR-R25-002`) or by the
query trigger (`LPR-R28-001`).** The invocation does only the reopen and ends there, so that the action has one
forward edge and the branches of the cause table run at
`AWAITING_FUNCTIONAL_REVIEW`, where `38d` matches again (the key is then in
`reopened_for` and not in `applied`) and every branch above applies unchanged.
Its steps, in order:

1. **fresh forge query**: the Workflow's fixed `workflow_gh` query, the same one
   `acceptance.satisfy` runs, stored with the same field writes (a fresh
   `ingest_seq`, and it is the Workflow-owned `workflow_gh` fact in `pr`, the only
   fact the shared predicate reads, `LPR-R28-001`) **but without the ingest-time
   reopen** (`LPR-R26-001`). The writer's side effects are named here: applied,
   the fact's store and `ingest_seq`; suppressed, `reopen_work_item` and its
   `reopenings` entry, which only steps 2-3 may write. So the action makes
   exactly one reopen decision, and a red fresh fact that carries a *different*
   actionable key reopens nothing at this step. Refusals of this step all **store
   nothing, leave the key out of `applied` and the phase at `MILESTONE_COMPLETE`**
   (`no_progress`, bounded by the consumer's retry bound; the remedy for the
   first three is a fetch or a retry): `forge_unavailable`; `forge_undecidable`
   (an unsafe `gh` path, a full page, or more than one open PR);
   `pr_head_unknown` and `pr_head_not_in_branch` (the fresh head was pushed after
   acceptance and is not fetched: the likely `content_changed` case at a completed
   item, remedy `git fetch`);
2. **the one decision rule (`LPR-R31-001`).** Call **S** the stored
   `workflow_gh` fact's actionable unapplied key as it stood *before* step 1's
   query (none when the stored fact was not actionable or its key was already in
   `applied`); S is read once, before the query, and is the only key this rule
   ever adds to `applied`. The key the action reopens on is **K**: when the action
   was started from `38d` case (a) alone, K is S and is reopened only if the fresh
   fact is `open` and still yields it (the same key tuple of the cause table at
   the fresh head, for the same cause); when the query trigger holds (a reported
   fact arming it, with or without a stored key, `LPR-R30-001`), K is whichever
   actionable unapplied key the fresh `workflow_gh` fact yields, if any, never the
   stale stored S. The outcome, one table for both phases and both entries:

   | fresh `workflow_gh` fact | S existed | result |
   | --- | --- | --- |
   | `open`, yields an actionable unapplied key K | either | proceeds to step 3 (reopen on K); in case (a) alone only when K is S |
   | `merged` | yes | refusal `pr_merged`; S **not** added to `applied` |
   | `merged` | no | recorded result `pr_fact_refreshed` |
   | `closed`, or `open` yielding no actionable unapplied key (a green PR, a new head with no red key) | yes | refusal `pr_fact_superseded`, which **adds nothing to `applied`** (`LPR-R32-001`): S stays unapplied, because a `closed` or green answer does not remediate S, so a PR that later reopens red at the same head, yielding S again, reaches step 3. The loop terminates because step 1 stored the fresh fact in `pr`: `38d` case (a) reads only the stored `workflow_gh` fact, which is now `closed` or green and so not actionable, and the greater `ingest_seq` clears the trigger |
   | `closed`, or `open` yielding no actionable unapplied key | no | recorded result `pr_fact_refreshed`; nothing added to `applied` |

   So `pr_fact_refreshed` applies only when no stored actionable unapplied key
   existed, and `pr_fact_superseded` only when one did; **neither adds a key to
   `applied`, so no result of this step ever consumes a key a fix did not handle**
   (only `/apply-pr-review`'s own fix branches add to `applied`). In case (a) alone, an
   open fresh fact yielding a *different* actionable key K2 is the superseded row
   for S (K2 is not S). The fresh fact stays stored: if it yields a *different* actionable key
   K2 (a red PR at a new head), the phase stays `MILESTONE_COMPLETE`, S and K2 are not in
   `applied`, and the **next `38d` pass acts on K2** (two passes by design: this
   pass is `no_progress`, the next is a different decision at a new
   `state_identity`, so it does not count toward the retry bound);
3. `reopen_work_item`, the **only** writer of a `reopenings` entry in this
   action, so exactly one entry results, `from_phase` `MILESTONE_COMPLETE`, even
   when the key was not yet in `reopened_for` (step 1 wrote none). Its own
   refusals (an incomplete child, `reopen_plan_archived`) end the action the same
   way, leaving the phase at `MILESTONE_COMPLETE`; on success the phase becomes
   `AWAITING_FUNCTIONAL_REVIEW` and the action ends.

**The query trigger path (`LPR-R28-001`).** When row `38d` matched by the trigger
(D-GP-Trust principle 3), **whether or not a stored actionable key also matches it
(`LPR-R30-001`; the trigger takes precedence, so a stored key never bypasses the
query, at `AWAITING_FUNCTIONAL_REVIEW` as at `MILESTONE_COMPLETE`)**, the action is the
same one: step 1's fresh query is its first and decisive step **at either phase**
(`AWAITING_FUNCTIONAL_REVIEW` or `MILESTONE_COMPLETE`), and a reported fact
decides nothing before it. It recomputes the trigger from state, so the same
state always runs the same path. After step 1 the stored key is not used as the reopen key: the fresh fact
decides, so a `merged` or `closed` answer prevents any reopening of the stale key,
and a refused query (`gh` unavailable) blocks with nothing reopened. The result is
the one table of step 2, stated once (`LPR-R31-001`): a fresh fact whose predicate
yields an actionable unapplied key proceeds to steps 2-3 (at
`AWAITING_FUNCTIONAL_REVIEW` the branches of the cause table then run, the item
having been reopened first when the key is not in `reopened_for`); when a stored
actionable unapplied key S existed before the query, a `closed` answer, or an open
one that no longer yields a key, ends in the refusal `pr_fact_superseded` with
**S left unapplied** (`LPR-R32-001`), and a `merged` one in `pr_merged`; only when **no** such
S existed does a fact that yields none (a `closed` PR, a green PR, or a `merged`
PR at an item whose key was never red) end in the **recorded result
`pr_fact_refreshed`**: no refusal, no phase change, nothing added to `applied`,
the fresh fact stored with its greater `ingest_seq`, which clears the trigger so
the next `38d` pass does not match and the item reads `complete` (at
`MILESTONE_COMPLETE`) or proceeds to the rows after `38d`. When the query refuses (`forge_unavailable`,
`forge_undecidable`, `pr_head_unknown`, `pr_head_not_in_branch`) nothing is stored,
the trigger still holds and `38d` emits the action again, bounded by the
consumer's retry bound: **a reported fact never resolves to "nothing to do"
without the Workflow's own query having run** (principle 4). `reconcile` takes
`pr_fact_refreshed` over the unchanged edge as `no_progress`, with a new
`state_identity` (the stored fact and `ingest_seq` changed), so it does not count
toward the retry bound.

A refusal at step 1, 2 or 3 leaves the phase where the action started:
`MILESTONE_COMPLETE`, or `AWAITING_FUNCTIONAL_REVIEW` when the trigger started it
there. At `AWAITING_FUNCTIONAL_REVIEW` the `reopenings` entry's `from_phase` is
that starting phase and, once the key is reopened (or already in `reopened_for`),
the action continues into the branches of the cause table instead of ending
(`LPR-R31-optional`); the wording "leaves the phase at `MILESTONE_COMPLETE`" in
steps 1 and 3 above is that phase only when the action started there. Residual:
a stored key at a completed item is acted on only after step 1's fresh query, so
a key whose PR has since been merged, with no merged fact ever reported, never
reopens the item, and enabling a cause in the policy cannot reopen a completed
item from a fact of any age (`GATE_POLICY.md` says so). A second residual
(`LPR-R33-001`, `LPR-R34-001`): an item whose PR, after a `closed` or green answer,
reopens red at the same head, with no stored actionable key and no report, is
reached by a Workflow query only on the paths of this table:

| Phase and acceptance mode | Workflow query path with no orchestrator report | Result |
|---|---|---|
| `AWAITING_FUNCTIONAL_REVIEW`, automatic acceptance | `/satisfy-gate acceptance` (`acceptance.satisfy`), `38f`'s remedy after the `closed` answer (the stored fact fails `pr_fact_current` and is at least as new as `pr_reported`, so the item matches `38f`, not `38h`); `38h` instead after a green answer when every other requirement holds | stores S and reopens once; `from_phase` `AWAITING_FUNCTIONAL_REVIEW` |
| `AWAITING_FUNCTIONAL_REVIEW`, human acceptance, `requires_pr_approved: true` | `/accept-milestone` step 2a. It stores S but does not reopen (the store reopens only on `acceptance.satisfy`'s path). For a `CHANGES_REQUESTED` S step 2a refuses, the item stays, and `38d` (a) reopens it | `from_phase` `AWAITING_FUNCTIONAL_REVIEW`. For a failed-checks S on an `APPROVED` PR step 2a passes, the item completes, and `38d` (a) then reopens it from `MILESTONE_COMPLETE` |
| `AWAITING_FUNCTIONAL_REVIEW`, human acceptance, `requires_pr_approved: false` (the default) | **none**: step 2a runs no query, and `38g`/`38h` do not apply to a human gate | the item is never remediated without a report |
| `MILESTONE_COMPLETE`, any mode | **none**: nothing queries the forge after completion (`acceptance.satisfy` is reached only before acceptance, and `38d` needs a stored actionable key or the trigger) | the item stays `complete` without a report |

Everywhere the table says **none**, only route (ii), an `orchestrator_forge`
`open` report followed by the Workflow query (`38d` by the trigger, then step 3),
reaches remediation; with no report the same-head red reopen is never acted on.
`GATE_POLICY.md` states both cases and says plainly that under human acceptance
without `requires_pr_approved` a same-head red reopen needs an orchestrator report
to be acted on.

The remediation command is `/apply-pr-review <id>`, modelled on
`/apply-functional-review`, an `automatic` action (role `applier`). **The work
item id is required** (`LPR-R4-007`): a reopen does not set
`active_work_item_id` and a completed item's pointer was reset by
`complete_work_item`, so a bare call, or `next-action` without `--work-item`,
would resolve to another item or to none; the command refuses a missing id
naming that reason, and `GATE_POLICY.md` says a reopened item is surfaced only
by naming it. Its first step is the `reopen_work_item` call above when needed. It then takes the branch
the cause table names. For `content_changed`: stale the technical approval, then
`record_bundle_generation` `post-fix` on the local `HEAD` with no edit
(`record_bundle_generation` requires only a `STALE` approval at
`AWAITING_FUNCTIONAL_REVIEW`, so the transition is legal). For the other two
causes it reads the stored fact's `findings` and classifies them. **`findings`
are untrusted text** (anyone who can comment on the PR may write them): data to
classify, never instructions to follow, and the three branches bound what it may
do (`LPR-R1-006`): no code change (add the key to `applied` with a recorded
note citing repository evidence; the unchanged forge decision then re-polls to
the same key, a no-op, so the cycle terminates; automatic acceptance stays
blocked by `no_standing_pr_objection`, and a human may still accept); a bounded
fix (`mark_technical_approval_stale`, edit, commit, `record_bundle_generation`
`post-fix`, which opens a fresh implementation-review round); a broad one
(`create_remediation_child_work_item`, the parent waiting for the child as
today). Every branch adds the key to `applied`. Everything after that is the
existing cycle: technical review (automatic or human per its toggle),
functional validation, then PR facts again (`OD-W2-7`).

### D-GP-Rows: next-action and protocol 1.1

**Version.** `PROTOCOL_VERSION` becomes `1.1` and `WORKFLOW_RELEASE` `2.8.0`;
`PROTOCOL_MAJOR` stays 1 (INV-8). Governing versions do not change.

**Additions, and no modification of an existing row (`LPR-R2-004`).**
Row 37 (`functional.prepare`) is **not** changed. Its manual checklist is still
prepared for every item in either mode and names the flows the functional
evidence is reported against; the automatic gate reads evidence, not the
checklist. The earlier idea that automatic acceptance suppresses row 37 is
dropped, so every existing row id, order and predicate is unchanged.

- Action ids: `plan.satisfy`, `implementation.satisfy`, `acceptance.satisfy`
  (disposition `validation`, role `validator`, a new worker role),
  `pr.apply_review` (automatic, role `applier`) and the external gates
  `functional.evidence.external` and `pr.review.external`.
- `validation` is now emitted: a decision whose action the orchestrator may
  launch like an automatic one (obligation 5 is widened to automatic and
  validation). `reconcile` accepts a `validation` decision; its edges are
  `plan.satisfy`: `AWAITING_PLAN_APPROVAL` to `IMPLEMENTING`;
  `implementation.satisfy`: `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` to
  `AWAITING_FUNCTIONAL_REVIEW`; `acceptance.satisfy`:
  `AWAITING_FUNCTIONAL_REVIEW` to `MILESTONE_COMPLETE`; `pr.apply_review`: the
  `functional.apply_findings` edges plus `MILESTONE_COMPLETE` to
  `AWAITING_FUNCTIONAL_REVIEW` (the reopen at a completed item, `LPR-R24-001`)
  **plus the unchanged `MILESTONE_COMPLETE` edge** (`_unchanged`, every version)
  for each refusal or `pr_fact_refreshed` result at a completed item (and the
  same-phase edge `AWAITING_FUNCTIONAL_REVIEW` to itself for `pr_fact_refreshed`
  there, `LPR-R28-001`), with `proof: None` and
  `allowed_results: _PROGRESS_GATE_NONE`. Started at `MILESTONE_COMPLETE` the
  action ends after the reopen or at a refusal (D-GP-Reopen), so those two are
  the only edges it can take from there; the branches of the cause table end
  at `AWAITING_FUNCTIONAL_REVIEW` and use the existing edges
  (`LPR-R25-001`). A refusal is `no_progress` (the next decision is again `38d`
  at the same phase, or `complete`), the reopen is `progress`. **Each `.satisfy` action also has a
  same-phase (unchanged) edge (`LPR-R13-002`)**, built with `_unchanged` as
  every existing action whose outcome can leave the phase alone does
  (`workflow_protocol.py:1722-1723`), because `reconcile` checks
  `edge_is_legal` first (`:2139`) and every refusal leaves the phase unchanged:
  `plan.satisfy` from and to `AWAITING_PLAN_APPROVAL` at versions 2.1 and 2.2;
  `implementation.satisfy` from and to `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`
  at 2.2; `acceptance.satisfy` from and to `AWAITING_FUNCTIONAL_REVIEW` at every
  version (the versions of D-GP-Gates' table, each forward edge's own). CP7 adds
  all six edges (three forward, three unchanged) to the spec's edge table, each
  with its versions, `proof` and `allowed_results`. **Each also has an `EDGES` `proof` and
  `allowed_results` (`LPR-R12-004`):** `plan.satisfy`, `implementation.satisfy`
  and `acceptance.satisfy` take `proof: None` and `allowed_results: progress,
  gate_reached, no_progress` (`_PROGRESS_GATE_NONE`). A refusal reconciles
  through the unchanged edge, never `illegal_edge`, and its class is the
  **existing classifier's own** (`LPR-R14-001`; `reconcile`,
  `workflow_protocol.py:2169-2174`: `gate_reached` only when the new decision's
  disposition is `human_gate` or `external_gate`, else `progress` on a phase
  change or a same-phase proof, else `no_progress`; `_same_phase_proof(None,
  ...)` is always `False`, and the three `.satisfy` actions take `proof: None`).
  The classes are therefore, by where the refusal's next decision lands:
  `progress` when the act reaches the forward target (the phase advances);
  `gate_reached` when the next decision is a human or external gate (`38f` and
  `38g`, external; rows 15, 29 and 39, human -- an `acceptance.satisfy` refusal
  while CI is pending stores a pending fact and goes to `38f`; a refusal after a
  toggle turned human goes to row 15, 29 or 39); and `no_progress` otherwise
  (`38h` after `forge_unavailable`, `38i` after a stored failed-checks or
  `CHANGES_REQUESTED` fact, `38d` after a stored red fact that reopened the
  item (an ingest, not `pr.apply_review`'s own store) or after a
  `pr_fact_superseded` refusal (the next decision is then `38d` only for a new-head
  key, otherwise the item's next row; the class is `no_progress` either way), and `14b`/`28b` after a `plan.satisfy`/`implementation.satisfy`
  refusal). **The plan adds no `proof` and changes no classifier line**: a `38d`
  or `38i` ending changes the stored facts and the next action's id and
  `state_identity`, yet reconciles `no_progress`, and that is correct for a
  `1.0` consumer too (INV-8). The spec's edge table (CP7) is the one place that
  defines each new action's classes; this paragraph cites it.
  `pr.apply_review` takes the `functional.apply_findings` entry's `proof: None`
  and `allowed_results: _PROGRESS_GATE_NONE`. An `acceptance.satisfy` that
  reaches `MILESTONE_COMPLETE` is `progress`, and row 40 still reports the
  completion: **`reconcile` still has no `complete` class**, which is what the
  spec passage amended in CP7 (the "Completion is reported by `next-action`"
  paragraph of `ORCHESTRATION_PROTOCOL.md` section 7) now says.
- Catalogue rows. Each label follows the catalogue's own convention (a later
  row takes a letter suffix after its base row, as `1a`, `6a` and `38a` to
  `38c` do), so each new row sits **after** its base row and the evaluation
  order is the printed order (`LPR-R4-006`). Each row of a gate returns no
  match when that gate is human, except `38d` (no gate-mode condition) and
  `38g` (which also matches a human acceptance with `requires_pr_approved`,
  delta 9 of D-GP-Compat), so the human rows 15, 29 and 39 are reached
  unchanged otherwise. Evaluation order is 14, `14a`, `14b`, 15; 28, `28a`, `28b`, 29;
  and 38c, `38d`, `38e` to `38i`, 39.
  - `14a`, `14b`, after 14 and before 15: `AWAITING_PLAN_APPROVAL` for items
    governed by 2.1 and 2.2 with the plan gate `automatic`: `14a` when
    `satisfiable` → `validation`, `plan.satisfy`; `14b` only when the existing wrapper is `reachable` and a
    policy requirement is unmet → `blocked`, reason
    `gate_evidence_unmet`, naming each unmet requirement and the remedy (turn
    the plan toggle to human and run `/approve-review plan`, or fix the
    evidence). **When `distinct_reviewer_models` is the unmet requirement,
    `14b` names two remedies, each executable at `AWAITING_PLAN_APPROVAL`**
    (`LPR-R16-003`, `LPR-R17-001`, `LPR-R18-001`; D-GP-Ingest): (1) turn the
    plan gate human, which is immediate with no adoption and is the
    single-subscription path; (2) withdraw with `/milestone-plan <id>`, edit and
    regenerate, and repeat both review stages, noting the withdrawn content is
    consumed. Recording a review of a second family is not offered here:
    `/record-manual-plan-review` refuses at this phase. It is the ingest-time
    form, when the missing or equal family is refused while the stage is open.
    `/adopt-gate-policy` is **not** named as a remedy here: its commit moves
    `HEAD` past the open bundle's `generation_head`, so the wrapper would be
    unreachable and the item would fall to row 16 (D-GP-Policy, "Bundle
    generation"); the row says that adoption is for before the bundle is
    generated. For `review_evidence_audited`, the remedies are the same two. An **unreachable** wrapper matches neither `14a` nor `14b` and
    falls through 15 to 16 unchanged, so row 16's cause-specific remedy is
    kept under the default (`LPR-R5-003`);
  - `28a`, `28b`, after 28 and before 29: the same, including the
    `reachable` scoping of `28b` and the two remedies of `14b` as executable at
    this phase (the technical toggle, and the implementation withdrawal and
    regeneration; the second-family record is the ingest-time form of
    D-GP-Ingest, and the adoption is not a remedy at an open bundle,
    `LPR-R18-001`), for `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`
    at 2.2 and `implementation.satisfy`; an unreachable wrapper falls through 29
    to 30, keeping each row-30 cause's own remedy and alternatives
    (`implementation.recover_provenance`, `implementation.apply_review`,
    regeneration; `LPR-R5-003`);
  - `38d`, after 38c and before 39 (every governing version): either (a) a stored
    `workflow_gh` PR fact (`gate_evidence.pr`, the only slot any decision reads,
    `LPR-R28-001`) whose key is actionable under the cause table **and the shared
    policy/state predicate** (`LPR-R23-001`: `pr_review.enabled`, `reopen_on`,
    PR `open`, read from that same fact) with the key not in `applied`
    (D-GP-Invalidation), **or** (b) the **query trigger** (D-GP-Trust principle 3), which takes precedence when
    both hold (`LPR-R30-001`: the fresh query runs before any reopen or
    application of the stored key, at either phase):
    `pr_query_trigger` (D-GP-Trust principle 3, defined once on the `pr` and
    `pr_reported` slots as wholes: `pr_review.enabled`, `pr_reported.ingest_seq`
    greater than `pr.ingest_seq` or `pr` empty, and the reported PR number,
    state, head, review decision, reviewed head, checks or cause keys differing
    from the `pr` fact's; never keyed by PR number) → automatic `pr.apply_review`, whose first decisive step is the
    Workflow's fresh query in case (b) and at `MILESTONE_COMPLETE` (D-GP-Reopen). A
    reported fact is never read for the predicate in case (a) and never decides
    case (b)'s outcome. The row matches at `MILESTONE_COMPLETE` too, so a
    completed item cannot read `complete` while a trigger holds; when `gh` is
    unavailable the trigger keeps matching and blocks (principle 4). It
    has **no gate-mode condition** (`LPR-R3-003`: `pr_review` is independent of
    `human_approval`), so it matches under all-human too, unlike `14a`, `28a` and
    `38e` to `38i`. Rows 37 (`functional.prepare`) and 38
    (`functional.apply_findings`) are evaluated before it, so a reopened item
    whose checklist evidence no longer matches, or with unconsumed
    `FUNCTIONAL_REVIEW.md` findings, gets those actions first; that is accepted
    (`LPR-R3-006`). It
    does not require the fact to be current for `content_changed`, and it
    matches a deferred fact (key not in `reopened_for`) as well as a reopened
    one (`LPR-R2-001`, `LPR-R2-002`). A reopen is therefore followed by
    `pr.apply_review`, never by row 39;
  - `38e`, `38f`, `38g`, after `38d` and before 39: the **acceptance gate's
    obtainable evidence**, in this fixed order, each an `external_gate`: `38e` when the
    acceptance gate is automatic and `functional_flows_passed` is unmet for want
    of evidence (none, stale or nothing current) → `functional.evidence.external`,
    `satisfied_by: functional_evidence`; `38f` when automatic and the **stored `workflow_gh`**
    pull-request fact, **at least as new as `pr_reported`** (by `ingest_seq`), is
    `state: none`, *behind* the anchor or otherwise not
    current (`pr_fact_current`, I1), or `ci_green` is required and its checks are
    `pending` → `pr.review.external`, `satisfied_by: pr_review_result`, which here
    means a **trigger and never evidence** (`LPR-R11-001`): the remedy names how
    to obtain it (open or push, wait for the checks, then have the orchestrator
    report a fresh `pr_review_result`, or run `/satisfy-gate acceptance`, which
    re-queries GitHub itself). A reported fact **newer** than the stored one
    moves the item to `38h` (below), so the report is acted on by one query and
    `38f` is not matched again until the query has stored a newer fact
    (`LPR-R9-002`); `38g` when `pr_approved` is required (automatic or human
    acceptance) and the stored `workflow_gh` fact is **at least as new as
    `pr_reported`** (by `ingest_seq`) and not `APPROVED` (the same newer-than rule
    for both modes, `LPR-R12-002`) → `pr.review.external`, the same
    `satisfied_by` (a trigger). Its remedy for an automatic gate is the `38f`
    remedy; for a **human** gate it names `/accept-milestone`, whose step 2a
    re-queries GitHub itself and stores its fact (`/satisfy-gate` refuses while the
    gate is human). With **no** stored `workflow_gh` fact, or one **older** than
    `pr_reported` (`ingest_seq`), neither row matches: the requirements are
    *pending the query* (D-GP-Acceptance). An automatic gate then reaches `38h`;
    a **human** gate has no `38h` and falls through to row 39, so a newer report
    clears `38g` and the person's `/accept-milestone` runs the query;
  - `38h`, after `38g` and before 39: acceptance automatic and `satisfiable` (every
    requirement met, the PR requirements read from a stored `workflow_gh` fact no
    older than `pr_reported`, or pending the query) → `validation`, `acceptance.satisfy`, whose act re-runs the
    query and may still refuse;
  - `38i`, after `38h` and before 39: acceptance automatic and not `satisfiable` with nothing
    obtainable (a failed flow or failed checks, a standing PR objection, a stale
    technical approval) → `blocked`, reason `gate_evidence_unmet`, naming each
    unmet requirement and the remedy (fix through `/apply-functional-review`,
    or turn the acceptance toggle to human);
  - Row 39's human gate follows only for a human acceptance gate.
  - **`38d` also matches at `MILESTONE_COMPLETE` (`LPR-R24-001`)**, evaluated
    before the terminal `complete` report: a completed item with a stored
    `workflow_gh` PR key that is actionable under the shared predicate
    (`pr_key_actionable`) against the *current* policy and not in `applied`, **or
    with the query trigger holding** (`LPR-R28-001`), gets `pr.apply_review`, whose first
    step is the fresh forge query of D-GP-Reopen (`LPR-R25-002`), then
    `reopen_work_item` (legal from `MILESTONE_COMPLETE`, `OD-W2-6`), which moves
    the item to `AWAITING_FUNCTIONAL_REVIEW` and ends the action; the branch then
    runs from `38d` again at that phase (`LPR-R25-001`). The reopen happens
    whether or not the key is already in `reopened_for`. This is how a red fact
    recorded while `pr_review.enabled` was false, or its cause was omitted from
    `reopen_on`, is reconsidered when the policy is later changed to enable it,
    without another fact arriving. When the query or `reopen_work_item` refuses (`forge_unavailable`,
    merged PR, a superseded fact, incomplete child, `reopen_plan_archived`) the
    action ends in a refusal naming its reason at `MILESTONE_COMPLETE`, which
    reconciles through the unchanged edge as `no_progress` (never
    `illegal_edge`). `38d` keeps matching only while the key stays actionable
    and unapplied: a merged or superseded result stops it (the fresh fact it stores
    is the newest for the PR, and it is `merged`, `closed` or yields no actionable
    key; the stale key is **not** added to `applied`, `LPR-R32-001`), and `forge_unavailable`
    leaves it matching (the trigger case too), bounded by the consumer's retry bound (as do
    `forge_undecidable`, `pr_head_unknown` and `pr_head_not_in_branch`, which also
    store nothing). A completed item
    with no actionable unapplied `workflow_gh` key and no query trigger still stays
    `complete`; a reported fact never reopens it directly (a `pr_fact_refreshed`
    result clears the trigger and the item stays `complete`).
- `next-action` gets an optional `policy` object on a decision:
  `{source, digest, gate, mode}`, plus `gate_lowering: {sha256, adopted_at,
  lowered}` while the newest adoption is a gate-lowering event (D-GP-Policy,
  D-GP-ThreatModel). It appears **only** on the new rows, never on
  an existing row, so a human-gate decision is byte-identical to 2.7.0's
  (INV-1).
- `record-external-result` moves `functional_evidence` and `pr_review_result`
  from reserved to supported (`external_result_kinds`), with the stage enum
  widened in the schema; `pr_review_result` additionally requires the `forge`
  provenance block (D-GP-Invalidation) and is refused without it, and what it
  stores is tighten-only (`LPR-R9-002`). Both kinds
  are accepted under every policy (`OD-W2-9`).
- `verify` gets a `gate_policy` check; `describe` gets the new capabilities
  and the 1.1 version. Gate-policy evaluation errors map to `refused`.
- An unaware `1.0` consumer meets unknown action ids (`blocked`, obligation 3)
  and the `validation` disposition (a known enum value that obligation 5 keeps it
  from running: a stalled item), as INV-8 states.

### D-GP-Compat: states, downgrade and the default

**Exhaustive list of intentional deltas (`LPR-R1-005`).** With every gate
human (INV-1's configuration), everything equals 2.7.0's except exactly:

1. `protocol_version` in every response envelope (`1.0` to `1.1`) and the
   `workflow_release` constant (`2.8.0`);
2. `record-external-result`: `functional_evidence` and `pr_review_result` are
   no longer refused with `unsupported_result_kind` (`OD-W2-9`);
3. `verify` gains a `gate_policy` check, advisory only: `pass` when no file is
   present, `warn`/`fail` as D-GP-Policy states, never changing the overall
   status (`LPR-R2-007`);
4. `describe` lists the new capabilities and the version;
5. `accept-milestone.md` step 5 says copy, not move (documentation only,
   `LPR-R2-003`).

6. **Only once a `pr_review_result` is reported or a PR is queried** (`LPR-R3-003`):
   the fact is stored (`gate_evidence.pr` for the Workflow's own query, or
   `gate_evidence.pr_reported` for an orchestrator's forge fact, `LPR-R10-002`);
   a stored `workflow_gh` key, or a reported fact that arms the query trigger
   (`LPR-R28-001`), makes `38d` emit `pr.apply_review` instead of row 39, whatever
   the gate modes, and the Workflow's own query may then reopen the item. A repository
   that reports no PR fact sees none of it.
7. **Only once a policy is adopted or a floor is recorded** (`LPR-R4-004`;
   D-GP-Policy recommends adopting a human policy to make it durable): the state
   gains the top-level `gate_policy_adoption` (an adoption, with one adoption
   commit carrying the `Workflow-Gate-Policy-Adoption` trailer) or
   `gate_policy_floor` (a committing evaluation, `/satisfy-gate`, observed a
   stricter setting in the file, with one floor commit carrying the
   `Workflow-Gate-Policy-Floor` trailer). Under all-human nothing runs
   `/satisfy-gate`, so only an adoption or a file read by a committing
   evaluation writes either. The state bytes then differ from 2.7.0's.
   `next-action` is unaffected, because `state_identity` covers the item only
   (`workflow_protocol.py:295`). The adopted all-human fixture of CP6 states
   this delta.
8. **Item-scoped staging (`LPR-R6-002`)**: with another item's uncommitted
   residue present, a validated commit stages item-scoped and succeeds where
   2.7.0's commit was refused after it landed (two concurrent 2.2 items between
   review stages, no fact, no adoption); with no foreign residue the bytes are
   unchanged. CP1 carries the commit-level fixture (a two-concurrent-2.2-items
   case) and CP7's update simulation re-runs it; CP6's protocol-output golden
   comparison is unaffected by it. Only validated commits are scoped; the
   unvalidated state commits keep 2.7.0's whole-file staging and bytes
   (`LPR-R7-001`).

9. **Only when `requires_pr_approved` is set on a human acceptance
   (`LPR-R13-003`)**, a setting that is off by default: `/accept-milestone`
   gains step 2a's pre-flight `gh` query and its refusal, which **writes state**
   (the stored `gate_evidence.pr` fact), and `next-action` emits `38g`
   (`external_gate`) before row 39 where 2.7.0 emits row 39. This fact comes from
   the Workflow's own query with no report at all, unlike delta 6. The CP6 golden
   comparison keeps INV-1's configuration at the default acceptance options and
   adds one all-human golden case with `requires_pr_approved: true`, which shows
   only this delta.

Nothing else under all-human (including under the new default `require`, which
applies only to an automatic gate, `LPR-R16-002`): no `Reviewer model:` line, no ledger key, no
state field (except as items 6, 7 and 9 and a reported functional fact or
pull-request fact write `gate_evidence`, `gate_policy_adoption`,
`gate_policy_floor`; item 8 changes only which bytes a validated
commit stages), no `next-action` `policy` object, no changed row. The CP6 golden
comparison covers `next-action`, `verify`, `describe` and
`record-external-result`, plus the bytes of `REVIEW_FEEDBACK.md` from the
reviewer commands, with this list the only allowed differences. Fixtures
include the all-human configuration as an unadopted file and as an adopted one,
and a no-file, an unadopted-file and an invalid-file case for the `verify`
output.

**The default is different, on purpose.** Updating an existing repository to
2.8.0 switches its three gates to automatic unless it turns human approval on
(`GATE_POLICY.json` with `"human_approval": true`). The deltas, beyond the nine
above (items 6 to 8 apply to the default as well; item 9 does not, because
`requires_pr_approved` is off unless set), for a repository with no policy file: at `AWAITING_PLAN_APPROVAL`
(items governed by 2.1 and 2.2) `next-action` emits `plan.satisfy`
(`validation`) or a `blocked` explanation instead of the human `plan.approve`
gate; at `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (2.2) the same for
`implementation.satisfy`; at `AWAITING_FUNCTIONAL_REVIEW` it emits the
evidence gates (`functional.evidence.external`, `pr.review.external`),
`acceptance.satisfy` or a `blocked` explanation instead of the human
`functional.review` gate; the satisfying commands write `POLICY_SATISFIED`
approvals and an `acceptance_satisfaction` record in place of a person's
confirmation. Items governed by `1`, and the technical gate of 2.1 items, stay
human (no ledger evidence). The update changes no state file by itself. The
operator guide, the compatibility notes and the update simulation say this
plainly, test both configurations, and name the one-line way back
(`"human_approval": true`). Two further deltas belong to the default, by the
user's decision on `OD-W2-17` (b), 2026-10-03 (`LPR-R16-003`): the reviewer
commands (`/review-plan`, `/review-implementation`) and `record-external-result`
write the `Reviewer model:` line and the `reviewer_model` ledger key for an
automatic gate, and the review-request wrapper asks the reviewer for the line;
and a manual `APPROVE` ingest that states no family, or the same family as the
other stage, is refused while its stage is still open (D-GP-Ingest, with its two
remedies: the second family and the toggle); a ledger recorded before the gate was automatic blocks at
`14b`/`28b` with `distinct_reviewer_models` unmet until a remedy executable at
that phase is taken. A 2.7.0 item in flight, updated under
the default, can be blocked by both `review_evidence_audited` and
`distinct_reviewer_models`; the notes and the update simulation name both and
their remedies together.

**A residual of the toggle on a legacy declaration (`LPR-R19-O1`,
`LPR-R20-002`).** The toggle is a working-tree edit of
`docs/ai-workflow/GATE_POLICY.json`, often creating the file. A declaration
generated from 2.7.0's template excludes the `docs/ai-workflow/` prefix at both
stages, so it classifies the file. An older hand-authored declaration that does
not exclude that prefix (for example `workflow-v2-1-core-artifacts.json`) leaves
a new or changed `GATE_POLICY.json` unclassified, and every classifier then
raises `UnclassifiedPathError`. The failure is closed (INV-6 is not at risk),
but the toggle blocks the gate it was meant to unblock for that in-flight item.
The remedy depends on the phase, because the declaration is bound content.
**Committing the file is never a remedy at any phase** (`LPR-R21-001`): both
classification gates diff the work item's fixed `base_commit` against the
working tree (`_changed_tracked_paths` is `git diff --name-only <base_commit>`),
so a committed `GATE_POLICY.json` is still a changed path and still raises
`UnclassifiedPathError` under a declaration that names neither the path nor its
prefix; and the commit also moves `HEAD`.

- **Before the stage's bundle is generated:** classify the path in the
  declaration for the stage, by excluding the `docs/ai-workflow/` prefix or the
  exact path `docs/ai-workflow/GATE_POLICY.json` (the change comes before
  generation, so it is part of the content the bundle binds). That is the only
  remedy.
- **With the stage's bundle open** (the toggle's usual phases: the ingest phase,
  `14b`/`28b`, and an in-flight 2.7.0 item updated at `AWAITING_PLAN_APPROVAL`
  or `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`): the toggle **cannot be used for
  that item**, and neither classifying the path nor committing the file helps.
  Editing the declaration changes the `review_content_id` (the protected and
  exclusion sets are in the hashed projection), so the readers refuse with
  `ReviewedContentDriftError` or an unverified bundle; committing leaves the
  path changed against `base_commit` (the classifier still refuses it) and moves
  `HEAD`, so the readers refuse too (`LPR-R18-001`). The
  remedies are the withdrawal or regeneration that `14b`/`28b` already name
  (`/milestone-plan <id>` at plan stage; the implementation stage's own
  withdrawal and regeneration, or `/recover-implementation-provenance`), with
  the prefix excluded in the declaration before the regeneration; the operator
  guide says so.

It is stated here, in the operator guide and in section 10. The terminal
`TOOLING_AMBIENT_EXCLUDED_PATHS` exact-path fallback is not widened for it: that
is a change to the 2.7.0 classifier's fail-closed scope, not taken in this
release (declined in round 19 and again in round 20). CP7's update simulation
includes one legacy-declared in-flight item and asserts both halves through the
real generation check.

**New fields.** Every field this release adds to a state or a record
(`LPR-R2-006`): the top-level `gate_policy_adoption` and `gate_policy_floor`;
an item's `gate_evidence` (`functional`, `pr` and `pr_reported`, each with its
forge `provenance` and `ingest_seq`, and `pr_keys` with `reopened_for`, `applied`
and the `ingest_seq` counter, `LPR-R11-002`),
`reopenings` and `acceptance_satisfaction`; a ledger entry's `verdict_sha256`,
`run_ref` and `reviewer_model`; an approval's `policy_evidence`; and the basis
`POLICY_SATISFIED`. They are written when the mechanism is used: an adoption, a
floor, an ingested fact, an automatic satisfaction, a reopening, a policy that
requires distinct models. The ledger audit keys are written only while that
stage's gate is automatic, so the all-human ledger bytes are 2.7.0's. A repository whose gates are all human, that reports no
fact and adopts no policy keeps a state byte-identical to 2.7.0's.

**Durability of each new writer (`LPR-R3-002`, `LPR-R4-001`, `LPR-R4-002`, `LPR-R5-001`, `LPR-R5-002`).**
The repository's commit contracts are exhaustive
(`validate_technical_approval_commit` against `TECHNICAL_APPROVAL_COMMIT_FIELDS`,
`validate_bundle_generation_record_commit` against
`ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS` and
`RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS`, and `_forbidden_state_mutation`,
which refuses any changed top-level field and any change to another work item's
entry). `record_external_result` makes no commit today, so each new write is
designed here, not left as residue. The last column says **which item's next
commit carries it**, so the cross-item case is visible beside the same-item one:

| writer | fields | durability | which item's next commit carries it |
| --- | --- | --- | --- |
| evidence ingest (`functional`), PR-fact ingest (`pr`, `pr_reported`, `pr_keys`) for item X | X's `gate_evidence` | **(b)** residue admitted for the same item: `gate_evidence` joins the three field sets, as the ledger fields did in 2.5.0 CP12; **(a')** item-scoped staging for every other item's commit (below) | X's own next technical-approval or generation-record commit, and only X's |
| `reopen_work_item`, `/apply-pr-review` (`applied`) for item X | X's `reopenings`, `gate_evidence.pr_keys.applied`, and for a reopen X's `phase` | **(b)** `reopenings` joins the three field sets for the same item; the reopen's `phase` change is X's own field and is never staged by another item's commit (below). `reopen_work_item` **no longer sets `active_work_item_id`** (a top-level field `_forbidden_state_mutation` refuses): every command and `next-action` carries the explicit work item id (`D1`) | X's own next commit; `/apply-pr-review`'s STALE write is committed on its own first (D-GP-Reopen, `LPR-R4-001`) |
| `/adopt-gate-policy` | the top-level `gate_policy_adoption`, and the reset `gate_policy_floor` | **(a)** its own commit with the dedicated trailer `Workflow-Gate-Policy-Adoption`, staged top-level-scoped (below, `LPR-R5-002`), and its own validator `validate_gate_policy_adoption_commit` (the state diff is exactly those two top-level keys; no work item changes), run by the command right after the commit and again on discovery. Neither widened validator admits an adoption. Both fields are verified at evaluation time by their content and the chain of their changes, which still holds once the commit is squash-merged and its trailer is gone (`verify_gate_policy_provenance`, D-GP-Policy) | its own commit |
| `record_gate_policy_floor`, called by `/satisfy-gate` after its satisfying commit (`LPR-R18-001`) | the top-level `gate_policy_floor` | **(a)** its own state-only commit with the trailer `Workflow-Gate-Policy-Floor`, staged top-level-scoped and validated by `validate_gate_policy_floor_commit` (the diff is exactly that key and the floor is no looser than the parent's); a squash merge that folds it among other changes, with a blank body, is still verified by monotonicity (D-GP-Policy) | its own commit |
| automatic satisfaction | `POLICY_SATISFIED` approval, `acceptance_satisfaction` | inside the existing technical-approval and plan-approval commits (the record fields are already in the sets). The completion commit **has no field contract** (`accept-milestone.md` step 6: "No command currently re-discovers this trailer by search"), so `acceptance_satisfaction` needs no widening and no new validator (`LPR-R4-003`) | the item's own commit |

**Cross-item residue: item-scoped staging (`LPR-R4-002`, `LPR-R5-001`,
`LPR-R5-002`; reviewer option (a); revision 5's closed foreign-residue set and
`admit_foreign_residue` are dropped).** Uncommitted work-item residue in
`WORKFLOW_STATE.json` is the normal state of this release, not an exception:
every ingest writes `gate_evidence`, a reopen writes `reopenings` and `phase`,
and a 2.2 item between its review stages holds `phase` and
`implementation_review_stages` residue (`record_local_implementation_review` and
`record_manual_implementation_review` make no commit; the manual-stage ledger
write sits "uncommitted until the very next commit", `TECHNICAL_APPROVAL_COMMIT_FIELDS`'s
own comment). Widening each validator by one more residue kind per round never
ends, and the review-round fields (a `phase` forward edge, a ledger stage) are
exactly what item 267 forbids one item's commit to carry for another. So the
class is closed at the **staging** step, where a commit for item Z is made:

- **`stage_scoped_state(repo_root, scope)`** in `workflow_state.py`, where
  `scope` is a work item id, the top-level pair `gate_policy_adoption` and
  `gate_policy_floor` (the adoption scope) or the top-level key
  `gate_policy_floor` alone (the floor scope). It reads `HEAD`'s committed state
  and the working-tree state. If they differ only inside `work_items[Z]` (or,
  for the two top-level scopes, only in those keys) it returns without acting and the caller's ordinary single-path
  `git add` runs, so the bytes of every repository with no foreign residue,
  all-human included, are unchanged (INV-1). Otherwise it builds the blob from
  `HEAD`'s state with only `work_items[Z]` (respectively only the scope's
  top-level keys; a pending floor is therefore never carried by an item's commit)
  taken from the working tree, serialized by the module's own canonical
  serializer, writes it with `git hash-object -w` and stages it with `git
  update-index --cacheinfo`, the primitive `pin_plan_approval_state_blob`
  already uses (`workflow_state.py:4041`, `:4082`), and **leaves the
  working-tree file untouched**. It refuses with the existing
  `DirtyIndexBeforeStagingError` when the state path is already staged and
  differs from `HEAD`. **The floor commit and the adoption commit also refuse a
  non-empty index apart from the state path (`LPR-R18-O1`)**, before they commit,
  with the same error naming the staged paths: both commit the whole index, and
  a user's own staged paths (a staged plan draft at plan stage) would otherwise
  be swept into a commit that `validate_gate_policy_floor_commit`/
  `validate_gate_policy_adoption_commit` could only reject after it landed.
- **Who calls it (`LPR-R6-001`, `LPR-R7-001`).** The rule: every commit whose
  validator calls `_forbidden_state_mutation` (`validate_technical_approval_commit`,
  `validate_bundle_generation_record_commit`), plus `/apply-pr-review`'s
  state-only commit and the adoption. A reader checks membership against that
  rule. Every command step that stages `WORKFLOW_STATE.json` for such a commit
  uses it in place of the bare `git add` of that path:
  `approve-review.md` (the technical-approval commit only),
  `milestone-implement.md` (step 4's generation-record commit only),
  `apply-implementation-review.md`, `apply-functional-review.md`,
  `recover-implementation-provenance.md`, `apply-pr-review.md` (both its
  state-only commit and its generation-record commit) and `adopt-gate-policy.md`
  (the adoption scope). Each gains one sentence, a no-op without foreign residue.
  **Unvalidated state commits keep 2.7.0's whole-file staging**: the checkpoint
  commit and the self-review transition commit of `milestone-implement.md`,
  `/request-plan-amendment`'s state commit (carrying only a `Workflow-Work-Item`
  trailer, `request-plan-amendment.md` step 3) and the plan approval. No
  validator runs over them, so there is no foreign-residue refusal to avoid, and
  their committed bytes are unchanged under all-human, delta 8 included. A test
  keeps the list derived from the rule: it greps each command for the commit
  trailers whose validator calls `_forbidden_state_mutation` and requires the
  `stage_scoped_state` sentence exactly there and nowhere else.
- **What this does to the validators.** Nothing: `_forbidden_state_mutation`,
  `validate_technical_approval_commit`, `validate_bundle_generation_record_commit`
  and `validate_gate_policy_adoption_commit` are **unchanged** and still refuse
  any other item's change and any top-level change (item 267 is not weakened:
  a hand-built commit carrying another item's `phase`, ledger, approval or any
  top-level field is still refused, and a test pins it). A foreign item's
  residue never enters the commit, so there is nothing to admit.
- **Why foreign residue stays durable.** It stays in the working-tree file,
  which no scoped commit rewrites (and no scoped step writes committed bytes back
  over; the plan-approval transaction's step 6c does, below, and is not scoped),
  until the item's own next commit flushes it
  (X's technical-approval, generation-record or `/apply-pr-review` commit; Y's
  review-round fields reach Y's technical-approval commit exactly as in 2.7.0).
  An item that never commits again (a `MILESTONE_COMPLETE` item with a functional
  record or a non-actionable PR fact) keeps that fact on disk only; it gates nothing
  for any other item, and the orchestrator re-derives it from the forge by
  re-polling, so a clone or checkout that loses it loses a re-derivable fact. A
  fact that matters reopens the item, and the reopen's commits carry it. This
  is stated in `GATE_POLICY.md`.
- **Adoption with residue (`LPR-R5-002`, `LPR-R9-003`).** `/adopt-gate-policy`
  stages with the adoption scope: only the two top-level keys
  `gate_policy_adoption` and `gate_policy_floor` (the reset floor) go on top of
  `HEAD`'s state, so another item's `gate_evidence` or ledger residue is
  neither committed nor refused, and the adoption commit passes
  `validate_gate_policy_adoption_commit` (diff exactly those two keys, the
  contract D-GP-Policy states once) in every state. The command runs the validator right after the commit; discovery
  re-runs it.
- **The plan-approval journal is not scoped (`LPR-R6-001`).** `/approve-review
  plan` keeps 2.7.0's whole-file pin: `open_plan_approval_journal`'s
  `expected_post_state = apply_plan_approval(pre_state, ...)` with `pre_state` the
  working-tree file. `verify_plan_approval_commit` never calls
  `_forbidden_state_mutation`, so that commit has no foreign-residue problem; it
  legitimately commits this item's top-level `active_work_item_id` (set by
  `/milestone-plan`, uncommitted until then); and step 6c writes the committed
  bytes back over the working-tree file after a whole-file compare-and-swap, so
  scoping the pin would delete other items' residue and this item's own pointer
  from the working tree, or stall the compare-and-swap. Therefore: the
  plan-approval commit carries the whole working-tree state, including foreign
  residue, and no validator refuses it; a later validated commit by the
  residue's owner is unaffected, because its parent then already holds the
  residue and `_forbidden_state_mutation` compares that commit with its parent.
  The first plan approval's committed bytes, top-level `active_work_item_id`
  included, equal 2.7.0's. A foreign change landing between journal open and
  the pin is the existing journal's own race, caught by its staged and committed
  sha256 checks; this release adds no new window there.

The plan-approval transaction's 4a and 6a member and verification checks are
reviewed for a fact ingested at a plan phase and admit this item's own
`gate_evidence` (CP2). Each widening, and the item-scoped staging above, is a
delta. The widenings are invisible under all-human until a fact is reported or
an adoption is made; item-scoped staging is visible under all-human with no
fact and no adoption whenever another item holds residue, and is delta 8.

**Downgrade posture.** 2.7.0 refuses a state that carries any new field or the
new basis, loudly at `validate_state` (an unknown key or basis), and never
silently drops the evidence (`OD-W2-13`). Because the default is now automatic,
those fields appear in ordinary operation (the first automatic satisfaction or
the first ingested fact), so a downgrade to 2.7.0 is supported only for a
repository that has not yet written one; after that the state needs 2.8.0 or
later. The validators widen to accept the new optional keys and the new basis.

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | options | recommendation |
| --- | --- | --- | --- |
| `OD-W2-1` | Where the policy lives | (a) its own file, `GATE_POLICY.json`; (b) a section of `WORKFLOW_CONFIG.json`; (c) per work item | **(a).** The config validator and its downgrade behavior stay untouched, the file is easy to review in a pull request, and (c) would let an item loosen its own gate. |
| `OD-W2-2` | What stops an agent loosening a gate | (a) the effective policy is the stricter of the committed, provenance-verified adopted policy, a recorded floor (a ratchet of every setting observed in the file) and the file, and only the user-only adoption loosens; (b) rely on the file digest alone (an edited file falls back to the default); (c) rely on pull-request review of the file | **(a).** It applies the user's rule: switching a gate to human applies immediately, switching back needs the user-only command, and a human setting the Workflow has seen survives an edit or deletion of the file (B1). The adopted policy and the floor are verified by their content and the chain of their changes, not by a commit message, so they survive this repository's squash merges, and a mismatch fails closed to all gates human (B2, `LPR-R9-001`). (b) would let deleting the file restore an automatic default after a human policy; (c) is not visible to the Workflow at run time. The residuals (a setting never observed durably, including one committed and deleted inside a single squashed branch; a hand-built self-consistent adoption record, which is outside the threat model of D-GP-ThreatModel and is reported as a gate-lowering event) are stated in D-GP-Policy. |
| `OD-W2-3` | What "independent cross-model" means | (a) a declared `Reviewer model:` family per stage, which must differ, required when the effective policy lists `distinct_reviewer_models` for an automatic gate (the default does, `OD-W2-17`); (b) an allowlist of reviewer identities; (c) nothing beyond the two stages | **(a).** The Workflow cannot verify a model, and (b) would claim a verification it cannot make. The two-stage ledger already requires a second, externally sourced review; (a) adds the one checkable fact, on by default and configurable (`OD-W2-17`). State the limit in the guide. |
| `OD-W2-4` | Who runs the functional evidence and CI | (a) the orchestrator runs the flows and reports them, and CI and pull-request facts come from GitHub through the one fixed query the Workflow ships (D-GP-Trust); (b) the Workflow runs commands a repository file names | **(a).** (b) executes commands named in a repository file, a supply-chain risk the adoption step would then have to cover. The built-in query names nothing from a repository file. The Workflow guarantees binding and audit, not execution of a flow. |
| `OD-W2-5` | Automatic milestone acceptance | (a) ship it as an evidence mode, now, with the evidence of D-GP-Acceptance and a per-gate PR policy; (b) keep acceptance human | **(a), by the user's decision of 2026-10-03.** The evidence is: every checkpoint `COMPLETE`, a current technical approval, current functional evidence with every flow passing, and a GitHub-sourced pull-request fact for the exact approved head with green checks and no `CHANGES_REQUESTED` (and, per gate option, an approved PR). |
| `OD-W2-6` | Reopening a `MILESTONE_COMPLETE` item | (a) allowed, with refusals for a merged PR, an open child and an unresolvable plan path; (b) only before acceptance | **(a).** The roadmap's own text says completion is not irreversible, and most review defects arrive after acceptance. Step 5 of `/accept-milestone` is pinned to copy, so the plan path still resolves; the completion side effects are not undone and a re-acceptance completes again. |
| `OD-W2-7` | How deep a reopening goes | (a) the existing bounded post-fix edge, with the remediation child for broad defects; (b) reopen to `IMPLEMENTING` and amend the plan | **(a).** It reuses proven edges and adds one command. (b) needs a new legal edge and re-opens the plan-approval gate for a code-review defect. |
| `OD-W2-8` | Re-validation after a content change | (a) full; (b) targeted by changed paths | **(a).** Targeted validation needs a mapping from paths to flows the Workflow does not have. The policy schema can add it later without a protocol change. |
| `OD-W2-9` | The two evidence kinds under any policy | (a) accepted and recorded under every policy, including all-human; (b) refused `not_applicable` under a policy that does not read them | **(a).** The default is automatic now, so the kinds must be accepted; `functional_evidence` is an inert record under a human gate; a `pr_review_result` (with forge provenance) reopens under `pr_review` whatever the gate modes (`LPR-R3-003`). One visible change from 2.7.0, listed in D-GP-Compat (`unsupported_result_kind` no longer returned). The earlier `not_applicable` refusal is withdrawn. |
| `OD-W2-10` | A new governing version or a major protocol bump | (a) neither: protocol `1.1`, governing versions unchanged, a minor release; (b) governing version `2.3` | **(a).** The protocol change is additive and the toggle restores every human gate. The default's behavior change is deliberate (the user's decision) and is stated in the compatibility notes; a new governing version would split every item's commands for no behavioral reason. |
| `OD-W2-11` | How `/satisfy-gate` reuses the approval and acceptance transactions | (a) cite `/approve-review`'s and `/accept-milestone`'s steps by number; (b) extract the transactions into functions both commands call | **(a).** The transactions are long, journaled and prose-driven; extracting them is a refactor of the riskiest code in the release. A test checks that the cited step numbers exist. |
| `OD-W2-12` | A policy change and approvals already recorded | (a) not retroactive; the evidence names the old digest; (b) re-evaluate on read | **(a).** An approval is a historical fact. (b) would make a past approval vanish when a policy tightens. |
| `OD-W2-13` | The shape of the new state fields | (a) new optional keys in the state file, readable only by 2.8.0 or later; (b) a sidecar evidence file | **(a).** The state is the single authority and the state identity must change when evidence does (stale-decision detection). A sidecar would fork the authority. |
| `OD-W2-14` | What "the exact implementation head" means for evidence | (a) the implementation identity at the evidence's head equals the anchor identity (an excluded-path commit does not stale it; a pull-request head must also descend from the anchor); (b) the evidence head equals local `HEAD` literally | **(a).** (b) stales functional evidence on every bookkeeping commit (the checklist-evidence commit, the roadmap), which acceptance itself creates. The user may overrule. |
| `OD-W2-15` | The default for `require_ci` | (a) `true`: automatic acceptance needs `checks.state` `success` on the GitHub-sourced pull-request fact; (b) `false`: failing checks still block, `pending` does not | **(a).** It is part of the user's stated evidence. The cost: a repository with no CI blocks at acceptance until it adopts `require_ci: false`, or makes acceptance human. |
| `OD-W2-16` | The default for `pr_review` | (a) enabled, reopening on both causes; (b) disabled | **(a).** With automatic acceptance a red or changes-requested PR is the safety net, and nothing happens until a fact is reported. |
| `OD-W2-17` | Whether `distinct_reviewer_models` is on by default for the automatic plan and technical gates (`LPR-R3-004`) | (a) opt-in: the default `require` is empty and any two `APPROVE` ledger entries satisfy the gate; (b) on by default for automatic plan and technical gates, so the default needs two declared, differing reviewer families (the roadmap's "independent cross-model review evidence", `docs/ROADMAP.md:650`), turning it off needs an adoption | **Decided (b), by the user's decision of 2026-10-03:** "Allow it to be configurable, to choose, by default its b. But not every user nor me will always have access to both subscriptions." The default `require` of both gates is `["distinct_reviewer_models"]`; removing it is a loosening through the user-only `/adopt-gate-policy`, a gate-lowering event. Because not every user has both subscriptions, the single-subscription remedies are first-class and documented: record a review from a second declared family (at ingest, while the stage is open), turn that gate human (immediate, no adoption), or adopt a policy without the requirement (before the stage's bundle is generated: an adoption commit moves `HEAD` and stales an open bundle, `LPR-R18-001`). The plan no longer deviates from `docs/ROADMAP.md:650`. |
| `OD-W2-18` | Whether automatic acceptance needs a pull request | (a) always: requirement `pr_fact_current` needs a GitHub-sourced fact for the current approved head, so the pull request is opened before acceptance; (b) only when `requires_pr_approved` | **(a), by the user's decision of 2026-10-03** (CI and pull-request facts come from GitHub, and a fact for an older head blocks). The cost: this repository's own pull-request-after-acceptance flow keeps acceptance human; a repository with no pull request flow keeps it human too. |
| `OD-W2-19` | The trust given to review verdicts and functional evidence | (a) trusted from the orchestrator, with a guaranteed audit trail and a stated boundary (binding, freshness and audit, not provenance); human approval is the stronger mode; (b) produce them in CI | **(a), by the user's decision of 2026-10-03.** (b) is explicitly not wanted in this release and is not offered as a policy option. |

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Gate policy model: GATE_POLICY.json schema with master switch and per-gate overrides, automatic default, tighten-only effective policy with a recorded floor, content-verified adoption that survives squash merges, verify check, roadmap refresh | - | 3 | 1 |
| CP2 | Automatic plan and technical approvals: evaluate_gate, POLICY_SATISFIED basis, reviewer-model and verdict audit evidence, /satisfy-gate plan and implementation, audit record | CP1 | 3 | 1 |
| CP3 | Functional evidence and GitHub-sourced pull-request facts: identity-bound ingest, forge provenance and the Workflow-owned stale-evidence table | CP1 | 3 | 1 |
| CP4 | Automatic milestone acceptance: acceptance evaluation, acceptance_satisfaction record, /satisfy-gate acceptance, accept-milestone changes | CP2, CP3 | 3 | 1 |
| CP5 | Reopening the same work item into remediation: reopen_work_item, /apply-pr-review, re-completion | CP3, CP4 | 3 | 1 |
| CP6 | Protocol 1.1: gate rows, actions, validation disposition, schema, all-human equivalence golden matrix | CP2, CP4, CP5 | 3 | 1 |
| CP7 | Specification, operator guide, update simulation of both configurations and lifecycle end-to-end tests | CP6 | 2 | 1 |
| CP8 | Release 2.8.0: manifest, conformance CI for the new suite, release-constant, roadmap | CP7 | 2 | 1 |

All paths in the checkpoints are release-source paths (`payload/…`,
`templates/…`, `manifest.json`) unless stated otherwise. The installation
copies under the repository root are never edited. Each checkpoint runs the
payload's eight existing suites in a release-source conformance fixture
(`tools/release/release.py stage-conformance`), plus the new suite from CP1
onwards, and `workflow-manager verify .` on the checkout.

<!-- CP1 -->
### CP1 — Gate policy model: toggles, default, tighten-only, adoption, `verify`, roadmap refresh

**Files:**

- `payload/scripts/workflow_gate_policy.py` (new, stdlib-only): the policy
  schema and `validate_policy`, `DEFAULT_POLICY`, `policy_digest`, the resolved
  (flat) form, `stricter`/`loosened_fields`, `effective_policy(repo_root,
  state)` with the table of D-GP-Policy, `record_gate_policy_floor`,
  `verify_gate_policy_provenance`, `gate_lowering_event(repo_root, state)`
  (the recomputed lowering of the newest adoption-changing commit, never the
  record's label, D-GP-Policy) and `evaluate_gate`'s skeleton (the `human`
  result).
- `payload/scripts/workflow_state.py`: the optional top-level
  `gate_policy_adoption` (`{sha256, adopted_at, confirmation, policy,
  history, lowered}`, `lowered` the gate-lowering label, D-GP-Policy) and `gate_policy_floor` (`{policy, digest, recorded_at,
  observed}`) and their validators; `validate_gate_policy_confirmation`;
  `record_gate_policy_adoption` (which also resets the floor);
  `record_gate_policy_floor`'s state write; the adoption's own commit with the
  `Workflow-Gate-Policy-Adoption` trailer and `validate_gate_policy_adoption_commit`
  (`LPR-R3-002`), the floor's own commit with the `Workflow-Gate-Policy-Floor`
  trailer and `validate_gate_policy_floor_commit`;
  `assert_gate_policy_fields_unchanged_or_tightened`, called after each
  unvalidated whole-file state commit (the plan approval, the checkpoint and
  self-review commits, `/request-plan-amendment`'s commit; one added sentence in
  each command, and a call inside `verify_plan_approval_commit`) and by
  `verify_gate_policy_provenance`; `stage_scoped_state` (item-scoped, adoption-
  and floor-scoped staging, D-GP-Compat, `LPR-R5-001`, `LPR-R5-002`), called by the adoption
  command and by every command step that stages the state file for a validated
  commit (one sentence each in `approve-review.md` (technical-approval commit),
  `milestone-implement.md` (step 4's generation-record commit),
  `apply-implementation-review.md`, `apply-functional-review.md`,
  `recover-implementation-provenance.md`, `apply-pr-review.md`); unvalidated
  state commits keep whole-file staging (`LPR-R7-001`);
  `_forbidden_state_mutation` and the four commit validators are unchanged.
  `APPROVAL_STAGES` is **not** changed.
- `payload/.claude/commands/adopt-gate-policy.md` (new, `user_only`; its
  confirmation shows the floor and the effective-policy difference, and lists
  every open plan-stage and implementation-stage bundle of any work item that the
  adoption commit will stale, with the way out of each; the commit refuses a
  non-empty index apart from the state path, `LPR-R18-001`, `LPR-R18-O1`).
- `payload/scripts/workflow_gate_policy_test.py` (new suite).
- `docs/ROADMAP.md`: the roadmap refresh. The W1 row's "the cutover remains"
  is done (v2.7.0 was published from `d14e0a7`, pinned by
  `workflow-manager#13`, Manager v1.3.0), so the row reads complete without
  the cutover clause; the W2 row becomes in progress (milestone
  `gate-policy-and-reopening`); the "Where things stand" paragraph is
  brought to 2.7.0. `docs/ROADMAP.md:176` ("The `Release` workflow publishes it
  when its pull request merges") is also stale (v2.7.0 exists at `d14e0a7`) and
  is corrected. The roadmap is excluded from reviewed content at both stages, so
  the docs check below is its only guard (`LPR-R1-008`).

**Tests:**

- no file: every gate resolves to automatic and `source` is `default`;
  `{"human_approval": true}` resolves all three human; each per-gate override
  (plan only human, acceptance only human, and the master on with two gates
  overridden to automatic) resolves as D-GP-Policy states;
- **tighten-only:** with no adoption, a file that turns a gate human, adds a
  `require` entry, a flow, `requires_pr_approved` is effective at once; after an
  adoption of a human policy, an edit back to automatic, a deleted file and an
  invalid file each leave the adopted value in effect (every row of the table,
  including `file_tightened`, `file_loosening_ignored`, `floor` and
  `provenance_failed`); an invalid file never raises;
- **B1, a user-activated human setting survives removal:** with **no**
  adoption, a file turning a gate human, observed by one committing evaluation
  (a `/satisfy-gate` run that made its satisfying commit, for another gate, then
  records and commits the floor after it, `LPR-R18-001`; a human gate is never
  satisfied by it, and a refused run records nothing), then (a) deleted,
  (b) edited back to automatic and (c) deleted *and* the deletion committed,
  each leaves that gate human, and a read-only `next-action` computes the same
  floor virtually from the working tree, `HEAD` and history; a file committed
  once and then deleted by a commit before any evaluation is still seen through
  the history scan; only `/adopt-gate-policy` lowers the floor; the residuals
  (a setting never observed durably, and a human setting committed and deleted
  inside one squashed branch, below) are pinned by tests that document them;
- **B2, adopted policy and floor by content and chain:** an edit of
  `gate_policy_adoption` (replace, loosen, remove) and of `gate_policy_floor`
  (loosen, remove) fails closed to all gates human with `source:
  provenance_failed`, tested **in the working tree** (the base is read from
  `HEAD`, so a working-tree edit changes nothing), **in a commit that changes
  the field without a valid chain or a self-consistent record** (trailer or no
  trailer), and in each unvalidated whole-file state commit (the plan-approval
  commit, `milestone-implement.md`'s checkpoint and self-review commits and
  `/request-plan-amendment`'s commit), each refused by
  `assert_gate_policy_fields_unchanged_or_tightened`; a commit whose trailer
  digest does not match the field is a failure, and a commit with **no** trailer
  whose record is self-consistent and chained verifies; a floor change folded
  into a squash commit verifies by monotonicity; a new `/adopt-gate-policy` commit
  restores a normal state; `verify` reports the failing field and commit and
  names that remedy;
- **the floor's range (`LPR-R10-001`):** a floor loosened by a hand-built commit
  and then tightened in a *different* field by a later `/satisfy-gate` floor
  commit **still fails** verification (each floor change is compared with its own
  first parent, so the later tightening hides nothing); a floor loosening
  **before** a valid adoption commit stops failing once that adoption is the
  newest change (the adoption is the lower bound of the range); a loosening
  *after* the adoption fails; with no adoption ever, the range runs to the root;
- **concurrent branches (`LPR-R10-004`), on a constructed repository with an
  update from `main` followed by a squash:** (a) two branches record different
  floors from the same base, the second updates from `main` and resolves the
  conflict to the field-wise stricter of both sides, and its squash verifies;
  resolved to the looser side, the squash fails closed (`provenance_failed`) and
  a new `/adopt-gate-policy` commit restores a normal state; (b) two branches
  each adopt from the same base: the first squash verifies, the second fails the
  chain check and fails closed, and re-adopting after updating from `main`
  chains onto the first adoption and verifies (also when the update merge's
  adoption conflict was resolved to the branch's own record: the stated
  resolution is "take `main`'s record, then re-adopt"); (c) **an adoption on one
  side (`LPR-R11-003`):** A adopts policy P, which lowers the floor, and
  squash-merges; B, cut earlier, recorded a stricter floor; B updates from `main`
  and the merge resolves to A's reset floor, dropping B's: `verify` **fails
  closed on B at the merge commit** (the reset exemption does not apply to an
  adoption another parent already holds, and B itself changed those fields),
  before any squash; resolving to the stricter floor **for the fields B
  recorded**, or re-adopting, restores a normal state; a
  non-merge adoption commit still resets as before; `verify`'s message names the
  re-adoption remedy, and `GATE_POLICY.md` and the operator guide state the merge
  rule; (c2) **an adoption on `main` while B is in flight, B recorded
  nothing (`LPR-R13-001`):** with no agent activity, `main` holds a human floor
  F_old; B is cut and changes neither `gate_policy_floor` nor
  `gate_policy_adoption`; the user adopts a policy P on another branch that
  lowers the floor to F_P, and it squash-merges; B updates from `main` by an
  automatic merge (taking `main`'s floor): B **verifies**, B's squash leaves
  `main`'s floor at F_P (no loosening, no revert), and the gate the adoption
  made automatic stays automatic; a variant where B recorded a stricter value
  for one field only keeps that field at the merge and takes `main`'s for the
  rest; (c3) **a criss-cross merge (`LPR-R14-O4`):** a merge whose parents have
  two merge bases with different floors **fails closed**, naming the merge and
  both bases, in every configuration, and the same history with one base
  verifies as before; (d) **a loosening before an adoption-bringing update merge
  (`LPR-R12-001`):** on branch B a hand-built commit loosens the floor (B fails
  closed); `main` then adopts, B updates from `main`, and the merge resolves the
  floor to the stricter of both parents' floors for the fields B changed: B **still fails closed**,
  because that merge is not an adoption-introducing commit, so the loosening stays
  in the floor range; a re-adoption on B (an adoption-introducing commit) restores
  a normal state. The same case for the file-history scan: a human
  `GATE_POLICY.json` setting committed on B before such a merge is still scanned
  into the floor; **the imported lowering stays visible (`LPR-R23-002`):** in
  scenario (c2) and in this one, after B's update merge makes a human gate
  automatic, `verify` warns naming the imported adoption's digest and each
  lowered field (recomputed against the merge's first parent, with an earlier
  adoption on B present to prove it is not the one reported), `next-action`'s
  `policy.gate_lowering` carries that digest and fields, and a later automatic
  satisfaction's `policy_evidence` copies it;
- **the squash case (`LPR-R9-001`), with this repository's merge settings (a
  blank squash body, the branch deleted), built from a constructed repository:**
  a branch makes an adoption commit and is squash-merged by recreating the
  squash commit (one commit on `main`'s parent, the branch's net diff, an empty
  body, no trailer); `verify_gate_policy_provenance` passes on `main` and on a
  new branch cut from it, `source` is `adopted`, and the adopted policy and the
  floor are in effect, for both `gate_policy_adoption` and an
  **adoption-lowered `gate_policy_floor`** (a recorded human floor reset to an
  automatic adopted policy: accepted exactly because the same commit changes the
  adoption validly); the same squash commit with the adoption record edited (a
  broken digest, a broken chain, a removed record) or the floor loosened without
  an adoption **fails closed** (`provenance_failed`); two adoptions folded into
  one squash verify through the chain (`history` begins with the parent's);
  a floor recorded on a branch survives its squash and a later file deletion on
  a new branch; a human setting committed and deleted inside one squashed branch
  with no committing evaluation between is **not** recovered (the documented
  residual): the test asserts the default applies and `verify` stays `pass`;
- **an adoption that lowers a recorded floor passes
  `validate_gate_policy_adoption_commit`** with the two-key diff
  (`gate_policy_adoption`, `gate_policy_floor`), and the validator refuses an
  adoption diff of the adoption key alone (the reset floor missing), of the floor
  alone, or with any third key or work-item change (`LPR-R9-003`);
- re-adoption of a looser file is the only path to a looser effective policy;
  the adoption record stores the body and a history;
- `DEFAULT_POLICY` is valid; the all-human configuration is valid;
- the adoption command's guard refuses an empty or non-naming confirmation
  and a model-run invocation path (the front matter flag);
- a repository with no adoption has no `gate_policy_adoption` key and an
  adoption round-trips through `validate_state`; the adoption commit passes
  `validate_gate_policy_adoption_commit`, and a technical-approval or
  generation commit that also carries an adoption is refused by
  `_forbidden_state_mutation` (`LPR-R3-002`);
- **adoption with residue (`LPR-R5-002`):** an adoption while another item
  carries `gate_evidence` residue and a 2.2 review-round ledger and `phase`
  residue stages only the two top-level keys, the commit passes
  `validate_gate_policy_adoption_commit`, the other item's residue is still in
  the working-tree file afterwards and absent from the commit; with no foreign
  residue the plain `git add` path runs and the bytes equal the unscoped
  result;
- `stage_scoped_state`: item scope takes only `work_items[Z]` from the working
  tree (a foreign entry and every top-level field come from `HEAD`), refuses a
  dirty index, leaves the working-tree bytes untouched, and is a no-op when only
  `work_items[Z]` differs;
- the all-human fixtures include two concurrent 2.2 items between review stages
  (no fact, no adoption): 2.8.0 stages scoped and the commit passes where the
  2.7.0 fixture's commit is refused after landing, as D-GP-Compat's delta 8
  states (`LPR-R6-002`; this is the commit-level check, CP7's update simulation
  re-runs it);
- **unvalidated commits stay whole-file (`LPR-R7-001`):** under all-human, with
  another item's residue present, an amendment-request commit and
  `milestone-implement.md`'s checkpoint and self-review commits have the same
  committed bytes as 2.7.0's; a grep test requires the `stage_scoped_state`
  sentence only in the commands and steps D-GP-Compat's rule names;
- an adopted all-human policy's state is checked against D-GP-Compat's delta
  list (the top-level `gate_policy_adoption` and the adoption commit, and
  nothing else; `state_identity` and `next-action` unchanged, `LPR-R4-004`);
- the roadmap text (a docs check) names W1 complete and W2 in progress, and no
  longer says the `Release` workflow will publish v2.7.0;
- `validate_gate_policy_confirmation` refuses a text lacking the literal or the
  digest prefix; `APPROVAL_STAGES` is unchanged;
- `verify`'s `gate_policy` check: `pass` with no file, `warn` for an unadopted
  differing file, for an ignored loosening and for an unrecorded or orphaned
  floor, `fail` for an invalid file and for a failed provenance, and none of
  them changes the overall status;
- **gate-lowering events (D-GP-Policy, D-GP-ThreatModel):** an adoption that
  lowers a gate (a human plan gate adopted automatic; a requirement removed)
  writes a non-empty `lowered` naming each field, and an adoption that lowers
  nothing (a tightening, or the file equal to the adopted policy) writes an empty
  one; `verify`'s `gate_policy` check is a `warn` naming the digest, the commit
  and the lowered fields for a lowering, and does not change the overall status;
  `gate_lowering_event` reads the lowering **from history, not from the label**;
  **a hand-built, self-consistent adoption commit that resets an already
  recorded human floor** (the Blocking finding's attempt: a valid digest, a
  confirmation naming it, a chain, the floor reset in the same commit) **is
  accepted by provenance, as the threat model states, and is reported as a
  gate-lowering event even when its `lowered` label is empty or omitted**, with a
  second `warn` for the label that disagrees; the same adoption squash-merged
  reports the same event against the squash's own first parent; `next-action`'s
  `policy` object carries `gate_lowering` on a new row while the newest adoption
  is a lowering event, an existing row never carries it, and `lowered` is not read
  as a precondition anywhere;
- **the default `require` (`OD-W2-17` (b), `LPR-R16-001`):** with no file,
  `plan_approval` and `technical_approval` each resolve `require` to
  `["distinct_reviewer_models"]` and the other fields to `DEFAULT_POLICY`'s; a
  file with `require: []` is `file_loosening_ignored` and leaves the requirement
  in effect; an adoption without it is accepted, writes `lowered` naming the
  field, and is a gate-lowering event reported by `verify` and `next-action`;
  `{"human_approval": true}` still lists the requirement in the resolved policy
  but the gates are human, so it is not evaluated (CP2 pins the bytes);
- the **threat-model statement** is present in `GATE_POLICY.md` and the protocol
  document (CP7's docs check) and is not weakened by a test: a test documents
  that the hand-built adoption above passes provenance, so the limit is pinned
  rather than implied.

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Automatic plan and technical approvals, with audit evidence

**Files:**

- `payload/scripts/workflow_gate_policy.py`: `evaluate_gate` for
  `plan_approval` and `technical_approval`; `distinct_reviewer_models`.
- `payload/scripts/workflow_fingerprint.py`: `parse_review_feedback_header`
  returns `reviewer_model`.
- `payload/scripts/workflow_state.py`: `POLICY_SATISFIED` in
  `APPROVAL_BASES`; `build_approval_record` / `validate_approval_record` for
  it; `resolve_policy_approval_basis`; `validate_policy_satisfied_confirmation`;
  the optional `reviewer_model`, `verdict_sha256` and `run_ref` keys in the
  two ledgers' entries and validators (the audit keys written only while that
  stage's gate is automatic, `reviewer_model` only when that stage's gate is
  automatic and its `require` lists `distinct_reviewer_models`);
  the `review_evidence_audited` requirement; the `trust` block of
  `policy_evidence` (D-GP-Trust); the ingest refusal of D-GP-Ingest (a
  precondition of the two manual-stage recording writers, raised before any
  write).
- `payload/.claude/commands/satisfy-gate.md` (new; the `plan` and
  `implementation` stages here, `acceptance` added in CP4); `approve-review.md`
  (a pointer sentence); `review-plan.md`, `review-implementation.md`,
  `record-manual-plan-review.md`, `record-manual-implementation-review.md`
  (the `Reviewer model:` line, requested as `<vendor>/<model>`; the ingest
  refusal of D-GP-Ingest in the two `record-manual-*` commands).
- `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`: the optional header line, and
  the request that the reviewer state it when the gate is automatic and requires
  distinct models; the `REVIEW_REQUEST.md` text that the author commands
  (`milestone-plan.md`, `apply-plan-review.md`, `milestone-implement.md`,
  `apply-implementation-review.md`) instruct the author to write carries the
  same request (`LPR-R16-003`).

**Tests:**

- an all-human configuration: no ledger key, no new basis, `/approve-review`
  records are unchanged (golden equality with 2.7.0 fixtures); the default
  writes a `POLICY_SATISFIED` record where 2.7.0 wrote `EXTERNAL_APPROVE`, in a
  fixture whose two ledger stages declare two differing families (the default
  `require` is `distinct_reviewer_models`, `OD-W2-17` (b));
- **the default `distinct_reviewer_models` (`LPR-R16-002`, `LPR-R16-003`):** all
  human under the new default (`"human_approval": true`, no adoption) writes no
  `Reviewer model:` line and no `reviewer_model` key (golden bytes); the default
  with two differing declared families satisfies the gate; one family, or a
  missing line, is `14b`/`28b` with `distinct_reviewer_models` unmet and the
  two remedies of the phase named, which `evaluate_gate`'s unmet
  `distinct_reviewer_models` `detail` names exactly (the human toggle and the
  withdrawal, `LPR-R20-001`); an `require: []` adopted **before the
  bundle is generated** satisfies the gate with one family; the review-request wrapper asks for the line only when the gate is
  automatic and requires it;
- `evaluate_gate` is `satisfiable` exactly when the mode is automatic, the
  wrapper is `reachable`, the verdict is `APPROVE` with a matching bundle id,
  and each `require` entry is met; each failing input (a `USER_OVERRIDE`
  situation, a stale ledger, equal or missing model families when required, a
  drifted bundle) is unsatisfiable and, at the gate, a `blocked` evaluation
  (never a pass);
- **the ingest refusal and its remedies, end to end (`LPR-R17-001`,
  `LPR-R18-001`), through the real generation check:** every remedy test below
  runs against a real repository with a **generated bundle**, from the phase
  where the remedy is named, calling the 2.7.0
  `assert_local_generation_matches` (never a stubbed or skipped guard). At
  `AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW` and its implementation analogue, under
  the default, a manual `APPROVE` with no `Reviewer model:` line, and one whose
  family equals the other stage's, are each refused with `WORKFLOW_STATE.json`
  byte-identical, the phase unchanged and exactly D-GP-Ingest's two remedies named (the
  second-family record and the toggle), the adoption asserted **absent** from the
  message (`LPR-R19-001`); then, for
  each remedy, the test runs it and re-submits: (1) the same verdict with a
  second family is recorded and `plan.satisfy`/`implementation.satisfy` is
  reached; (2) the gate toggled human admits the same verdict with no line and
  no key (2.7.0's bytes) and `/approve-review` is reached. **The adoption is
  tested as the refusal it is at an open bundle:** an `/adopt-gate-policy` made
  at that phase leaves the re-submitted ingest refused with
  `WorktreeOrHeadMismatchError`, `WORKFLOW_STATE.json` byte-identical, and the
  adoption's confirmation text lists the open bundle and its way out; an
  adoption made **before** the bundle was generated admits the ingest and
  reaches `plan.satisfy`. A `REVISE` ingest is
  admitted with no line. Under all-human nothing is refused (golden bytes). An
  ingest under an automatic gate always carries `verdict_sha256`, so
  `review_evidence_audited` is never left unmet by it;
- **the declared form and header-only parsing (`LPR-R17-O1`, `LPR-R17-O2`):**
  `/review-plan` and `/review-implementation` write `Reviewer model:` as
  `<vendor>/<model>` (golden bytes), the wrapper text requests that form, a
  verdict whose header lacks the line but whose body quotes `Reviewer model:
  openai/x` at the start of a line parses as declaring none, and the same line
  in the header block parses;
- an item governed by `1`, and the technical gate of a 2.1 item, always
  evaluate human;
- a satisfied approval's record validates, carries the digest, source and every
  requirement, and the plan commit carries both trailers and
  `Workflow-Gate-Satisfied-By`;
- the technical commit passes `validate_technical_approval_commit`, including
  with `policy_evidence` and a plan-phase `gate_evidence` ingest as same-item
  residue, and the plan-approval transaction's 4a and 6a checks admit that
  residue (`LPR-R3-002`); a plan approval while another item
  carries review-round and `gate_evidence` residue commits the whole file (the
  journal stays whole-file, `LPR-R6-001`), the residue is still in the working
  tree after step 6c, the journal closes, and the other item's next
  technical-approval or generation-record commit passes its unchanged
  validator; the all-human first plan approval's committed bytes, top-level
  `active_work_item_id` included, equal 2.7.0's;
- re-evaluation inside the transaction refuses when the toggle was turned human
  meanwhile and writes nothing;
- the command text cites existing `/approve-review` step numbers, and every
  cited step that branches on basis or confirmation states its automatic-mode
  behavior;
- a `POLICY_SATISFIED` record passes validation; an approval record with
  `stage="gate_policy"` is refused; a pinned `BLOCK` refuses `/satisfy-gate`;
  `resolve_policy_approval_basis` never returns `USER_OVERRIDE`;
- the reviewer commands write no `Reviewer model:` line unless that stage's
  gate is automatic and the effective policy requires distinct models (golden
  bytes of `REVIEW_FEEDBACK.md`; none under all-human);
- **the trust boundary and the audit trail (INV-9):** a ledger entry written
  while its gate is automatic carries `verdict_sha256` and `run_ref` (`session:local`
  and the artifact path in a standalone session, the reporter's value through
  the protocol), and one written while the gate is human is byte-identical to
  2.7.0's; `evaluate_gate` is unsatisfiable with `review_evidence_audited` unmet
  for a stage that lacks them; every automatic satisfaction's `policy_evidence`
  holds the verdict hash, the ledger-entry hash, the bundle id, the content id
  and the run reference of both stages, and `trust: review_verdicts:
  orchestrator`; **fabricated inputs:** a manual `APPROVE` submitted through the
  model-invocable `/record-manual-plan-review` and `record-external-result`
  paths, matching the bundle and content ids, **does** satisfy an automatic
  gate (the boundary is stated, not hidden) and the resulting record names its
  hash and reporter, while the same inputs under the human toggle (or the master
  switch) satisfy nothing; a mismatched bundle id, a stale content id or a
  verdict with no hash does not satisfy it.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Functional evidence, GitHub-sourced pull-request facts and the stale-evidence table

**Files:**

- `payload/scripts/workflow_forge.py` (new, stdlib-only, D-GP-Trust): the one
  fixed `gh` argv as a constant (with `--limit 200`) and `FORGE_PR_LIST_LIMIT`,
  `resolve_gh(repo_root)` (the absolute path, refused inside the repository, a
  worktree, the temp directory or a world-writable directory; the executable's
  sha256), `query_forge_pr_facts(repo_root, queried_commit, *, run=...)` (no
  shell, a 30-second timeout, the `origin` repository parsed and validated, the
  resolved absolute path run; `run` is the injectable runner, the module's test
  seam, exactly as the existing suites inject through `mock.patch.object` and
  explicit arguments, so no test needs a fake executable on `PATH`),
  `parse_forge_raw(raw, repository, queried_commit)` (the single parser both
  sources use, refusing a full page), and the errors `ForgeUnavailableError` and
  `ForgeUndecidableError`.
- `payload/scripts/workflow_gate_policy.py`: `ingest_functional_evidence`,
  `ingest_pr_facts` (forge provenance required; the stored orchestrator fact is recorded and can only arm the query trigger, `LPR-R28-001`), `pr_query_trigger(state, policy)` (the single predicate rows `38d` and `pr.apply_review` both call, on the `pr` and `pr_reported` slots as wholes, `LPR-R29-001`), `INVALIDATION_RULES` and its
  applier, the cause table (key functions per cause), the `current_at_anchor`
  predicate and the position function (equal, ahead, behind).
- `payload/scripts/workflow_state.py`: the item's optional `gate_evidence`
  (`functional`, `pr` and `pr_reported` with their `provenance` and `ingest_seq`, and
  `pr_keys` with `reopened_for`, `applied` and the `ingest_seq` counter, the shape
  D-GP-Invalidation pins once; unknown keys rejected) and its validator; `gate_evidence` added to `TECHNICAL_APPROVAL_COMMIT_FIELDS` and to
  the ordinary and recovered bundle-generation field sets (same-item residue).
  Another item's residue is kept out of a commit by item-scoped staging
  (CP1's `stage_scoped_state`), not by a widened validator (D-GP-Compat,
  `LPR-R3-002`, `LPR-R5-001`).
- `payload/scripts/workflow_protocol.py`: `record-external-result` accepts
  the two kinds and delegates (the wiring lands in CP6; CP3 ships the
  library calls and their tests).

**Tests:**

- identity is recomputed at `head`; a reporter's claim is never read;
- a commit that changes only excluded paths keeps evidence current, one that
  changes protected content stales it;
- every row of the invalidation table, driven by constructed repositories
  (same-content head change, changed-content head change, outdated review,
  failed checks, merged, closed, reopened PR);
- an unresolvable head refuses (`pr_head_unknown`, `evidence_head_unknown`); a
  head the local branch does not contain refuses (`pr_head_not_in_branch`,
  `evidence_head_not_in_branch`);
- a fact arriving at each non-reopenable phase is recorded only, with no state
  effect, and a `CHANGES_REQUESTED` fact recorded at `IMPLEMENTING` is actionable
  under the cause table once the item is at `AWAITING_FUNCTIONAL_REVIEW`
  (`LPR-R2-002`);
- the cause table: the three key functions are deterministic and the key of a
  `content_changed` fact is `(pr.number, "content_changed", head,
  identity_at_head)`; re-polling the same content-changed head (new
  `observed_at`) is a no-op (`LPR-R2-001`);
- a content-changed PR head on a `MILESTONE_COMPLETE` item is actionable and
  never leaves a `STALE` approval on a terminal item;
- re-polling an unchanged `CHANGES_REQUESTED` and failed-check fact (new
  `observed_at`, same key) is idempotent;
- a failed flow, a pull-request fact with `pending` checks and a fact at a stale
  head are each recorded and each not current-and-passing; a re-reported passing
  flow replaces the earlier record;
- **forge provenance (D-GP-Trust, INV-9), with the Workflow's own query driven
  through the injected runner (`query_forge_pr_facts(..., run=<fake>)` and
  `resolve_gh` patched to return a fixed path outside the repository and temp,
  never a fake `gh` on `PATH`, round 15 Blocking 2):** the query's argv is
  exactly the built-in constant, `--limit 200` included, and no repository file, policy or environment value can alter it;
  every pull-request field is **derived from `raw`**, so a reporter-supplied
  `state`, `head`, `review_decision` or `checks` that disagrees is not read;
  an input without the `forge` block (`forge_provenance_required`), with a
  `raw_sha256` that does not match (`forge_digest_mismatch`), naming another
  repository (`forge_repository_mismatch`), with an unparseable `raw`
  (`forge_unparseable`) or with two open pull requests for the commit
  (`forge_undecidable`) is refused and writes nothing; a fabricated `green` fact
  built by hand with no `raw` is refused; **a hand-built forge block with a
  self-consistent `raw` and `raw_sha256` (GitHub-shaped JSON, `headRefOid` at the
  anchor, all checks `SUCCESS`, no `CHANGES_REQUESTED`, `fetched_at` now) is
  accepted and stored as `orchestrator_forge`, and is tighten-only
  (`LPR-R9-002`): `pr_fact_current`, `ci_green` and `pr_approved` read it as
  absent, so it does not satisfy automatic acceptance with `gh` available (the
  act's own fake-`gh` query decides) nor with `gh` unavailable (the act
  refuses naming `forge_unavailable` and the gate does not pass); the same block showing `CHANGES_REQUESTED` or
  failed checks **reopens nothing by itself** (`LPR-R28-001`): it arms the query
  trigger, `38d` emits `pr.apply_review`, and only the fake-`gh` fresh query's
  `workflow_gh` fact decides (red there: reopens; green there: `pr_fact_refreshed`,
  nothing reopens);** **one slot per source
  (`LPR-R10-002`):** a red `workflow_gh` fact followed by a self-consistent
  all-green `orchestrator_forge` fact leaves both stored
  (`gate_evidence.pr` and `gate_evidence.pr_reported`), and row `38d` still emits
  `pr.apply_review` for the red key under a **human** acceptance gate, with row 39
  not offered; the reverse order (a reported red fact, then a green `workflow_gh`
  fact) leaves no trigger and no actionable key, and an orchestrator-only red fact
  emits `38d` through the trigger and reopens only if the Workflow's query shows it
  red; **fail closed:** `gh` not installed,
  not authenticated, exiting non-zero, timing out, printing non-JSON or naming
  another repository each raises and writes nothing, and the acceptance
  evaluation is unsatisfied (`forge_unavailable`), never falling back to a
  stored orchestrator fact, of any age; a standalone query's fact is stored with
  provenance `workflow_gh`, including when the gate is then refused, and a query
  that finds no pull request stores `state: none`;
- **which `gh` runs (safeguard, D-GP-ThreatModel):** the stored `workflow_gh`
  provenance carries `gh_path` and `gh_sha256` (the validator requires both; the
  sha256 equals the executable's); **a `gh` resolved inside the repository, inside
  a linked worktree, inside the temporary directory, or in a world-writable
  directory (or itself world-writable) is refused `forge_undecidable`** naming
  the path, writes nothing, and the acceptance gate does not pass, each of the
  four tested with a real executable file created in that location and
  `PATH` pointing at it (resolution only, the executable is never run in the
  refused case); a `gh` not found stays `forge_unavailable`; a symlink in a safe
  directory pointing into the repository or temp is refused by its resolved
  target; a safe path is accepted and the runner is called with the **absolute**
  path, not the bare name; the same refusal applies to
  `/accept-milestone` step 2a's pre-flight;
- **a full page is undecidable (round 15 Important finding):** a runner returning
  exactly 200 records (one green match, with a red match possibly beyond the
  page) refuses `forge_undecidable` and stores nothing, and the argv passed to the
  runner carries `--limit 200`; 199 records with one green match is decidable;
  `parse_forge_raw` applies the same refusal to an orchestrator's `raw` of 200 or
  more records (`forge_undecidable`);
- **fabricated functional evidence (the stated boundary):** a
  `functional_evidence` record submitted through the model-invocable ingest, with
  a matching head, **is** accepted as the orchestrator's word and its `log_digest`,
  `reporter` and `run_ref` are kept for the audit record; a head that does not
  resolve, is not contained in `HEAD` or has a different identity is refused or
  non-current; no CI-produced functional or review evidence is accepted or offered
  as an option (a test greps the schema and the policy vocabulary for it);
- with `pr_review.enabled` false the fact is recorded and reopens nothing;
- **the shared actionability predicate (`LPR-R23-001`):** both a `workflow_gh`
  fact stored by an immediate query path and a deferred one (queried at
  `IMPLEMENTING`, evaluated by `38d` at `AWAITING_FUNCTIONAL_REVIEW`) are checked with `pr_review.enabled` false, with
  a cause omitted from `reopen_on`, and with a `closed`, unmerged red PR: none
  reopens, and `38d` never emits `pr.apply_review` for it; re-enabling the
  policy (or a fresh Workflow query finding the PR open) makes the same stored
  key actionable again; a **reported** fact in the same three conditions arms
  nothing at `38d` while `pr_review.enabled` is false;
- **a completed item reconsidered on a policy change (`LPR-R24-001`):** record a
  red `CHANGES_REQUESTED` (and a `checks_failed`) fact for a `MILESTONE_COMPLETE`
  item while reopening is disabled (and again with the cause omitted from
  `reopen_on`): the item stays `complete` and `next-action` reports `complete`;
  enable the cause in the policy and, **without submitting another fact**,
  `next-action` returns `38d` `pr.apply_review`, and the action reopens the item
  to `AWAITING_FUNCTIONAL_REVIEW` once (the key enters `reopened_for`, then
  `applied` after the apply). Also: a merged PR or archived plan path ends the
  action in its named refusal, and an `applied` key is never re-emitted; **the key
  already in `reopened_for` at `MILESTONE_COMPLETE`** (reopened, accepted over
  with reopening disabled, policy re-enabled) is reopened again and the entry's
  `from_phase` is `MILESTONE_COMPLETE`;
- **a completed item's stored key against a stale PR fact (`LPR-R25-002`):** an
  open red key stored for a completed item whose PR has since been merged, with
  **no** merged fact reported: enabling the cause makes `38d` emit
  `pr.apply_review`, whose fresh query returns `merged`, the item is **not**
  reopened (`pr_merged`), the fresh fact is stored and `38d` no longer matches.
  A fresh query returning a green PR ends in `pr_fact_superseded` with the key
  **not** in `applied` (`LPR-R32-001`). **A red open PR at a new head (`LPR-R26-001`)**: phase stays
  `MILESTONE_COMPLETE`, no `reopenings` entry, K1 not in `applied`, the fresh fact
  stored, `reconcile` `no_progress`, and the next `38d` pass emits
  `pr.apply_review` for the new key K2 and reopens once. **A deferred key (not in
  `reopened_for`) reopened from `MILESTONE_COMPLETE` writes exactly one
  `reopenings` entry** (`from_phase` `MILESTONE_COMPLETE`). The fresh store at
  step 1 never reopens by itself. Step-1 refusals `forge_unavailable`,
  `forge_undecidable` and `pr_head_unknown` (also `pr_head_not_in_branch`) store
  nothing, leave the key out of `applied` and the phase at `MILESTONE_COMPLETE`;
- **the single principle, one test per case (`LPR-R28-001`, resolving rounds 4 to
  6): an `orchestrator_forge` fact never decides and can only trigger the
  Workflow's own query.** Each case below runs at `AWAITING_FUNCTIONAL_REVIEW`
  and at `MILESTONE_COMPLETE`, with the cause enabled, and asserts which fact the
  predicate read:
  1. *completed-item stored key (round 4):* the stale-fact case above, unchanged;
  2. *reported `merged`/`closed` after a Workflow-observed open red key (round 5,
     `LPR-R27-001`; result table `LPR-R31-001`):* an open red `workflow_gh` key S
     in `pr`, then a newer `orchestrator_forge` `merged` (and, separately,
     `closed`) report for the same PR: the key stays actionable (the predicate
     reads `pr` only), `38d` emits `pr.apply_review`, and the fresh Workflow query
     runs before the item can stay complete. Assert, at both phases, the single
     result per fresh answer and S's `applied` membership: fake-`gh` `merged` ->
     refusal `pr_merged`, S **not** in `applied`; fake-`gh` `closed` (or an open
     green PR) -> refusal `pr_fact_superseded`, S **not** in `applied`
     (`LPR-R32-001`); open red -> reopens; each refusal with no reopening and no
     `reopenings` entry, and `38d` no longer matching (the stored fact is now
     `closed` or green). **Then the PR reopens red at the same head, yielding S
     again** (`LPR-R33-001`, `LPR-R34-001`, `LPR-R34-002`). Each route below
     names an invocation path that exists at the phase, acceptance mode and
     options it is asserted for (D-GP-Reopen's second-residual table). Route (i),
     a Workflow query alone, with no report:
     - *automatic acceptance, `AWAITING_FUNCTIONAL_REVIEW`:* after the `closed`
       answer assert that `next-action` emits `38f` (`external_gate`; the stored
       `closed` fact fails `pr_fact_current` and is at least as new as
       `pr_reported`), never `38h`, and that `38f`'s remedy `/satisfy-gate
       acceptance` (the `acceptance.satisfy` act) on the reopened red PR stores S
       and reopens once, `from_phase` `AWAITING_FUNCTIONAL_REVIEW`. After a green
       answer assert the item lands on `38h` when every other requirement holds;
     - *human acceptance, `requires_pr_approved: true`:* a `CHANGES_REQUESTED` S:
       `/accept-milestone` step 2a stores S and refuses, the item stays at
       `AWAITING_FUNCTIONAL_REVIEW`, and `38d` (a) reopens it once, `from_phase`
       `AWAITING_FUNCTIONAL_REVIEW`. A failed-checks S on an `APPROVED` PR: step 2a
       stores S and passes, the item completes, and `38d` (a) then reopens it once,
       `from_phase` `MILESTONE_COMPLETE`;
     - *human acceptance, `requires_pr_approved: false` (the default):* no Workflow
       query runs at either phase (assert no query and no `reopenings` entry, the
       stated residual; `38g`/`38h` do not match a human gate);
     - *`MILESTONE_COMPLETE`, any mode:* no query path exists, so a same-head red
       reopen with **no** report leaves the item `complete` (no `38d` match, no
       `reopenings` entry; the stated residual).

     Route (ii), an `orchestrator_forge` `open` report followed by the Workflow
     query (`38d` by the trigger, then step 3), reaches remediation in every case
     above, including each "none": exactly one `reopenings` entry, `from_phase` the
     phase the item was at, S still not in `applied` until `/apply-pr-review`
     applies it; the report alone never suppresses the query. A control: S already in `applied` (a fix handled it)
     is not reopened by the same reopened PR;
  3. *reported `open` after a Workflow-observed `closed` (round 6):* a completed
     item with a stored `workflow_gh` `closed` fact (as `pr.apply_review`'s fresh
     query stores it), then a newer `orchestrator_forge` `open` fact for the same
     PR carrying a distinct red key: the next `next-action` is `38d`
     `pr.apply_review` (never `complete`, never row 39), the action runs the fresh
     Workflow query first, and a fake-`gh` `open` red result reopens the item once
     (`from_phase` `MILESTONE_COMPLETE`) while a fake-`gh` `closed` result ends in
     `pr_fact_refreshed` with the item still `complete` and no further `38d` match;
  4. *the reported fact never decides, in either direction:* a `merged`
     `workflow_gh` fact in `pr` plus an **older** (lower `ingest_seq`) open red
     `orchestrator_forge` key: no key is actionable, no trigger holds, and `38d`
     does not match; the same reported fact **newer** and differing arms the
     trigger and `38d` emits the query, which stores a newer `workflow_gh` fact
     that decides; a reported fact **equal** to the stored `workflow_gh` fact (same
     state, head, decision, checks and keys) arms nothing at `38d`;
  5. *`gh` unavailable (principle 4):* in cases 2, 3 and 4's newer-and-differing
     variant the query refuses `forge_unavailable` and stores nothing, `38d` keeps
     matching and the consumer's retry bound ends in `blocked`; the item is never
     reported `complete`, never reopened and never accepted from the reported
     fact; with `pr_review.enabled` false no trigger arms and nothing changes;
  6. *no loop:* after the query stores its `workflow_gh` fact the trigger is
     cleared (greater `ingest_seq`), so one report causes at most one successful
     query, and `reconcile` classifies `pr_fact_refreshed` `no_progress` at a new
     `state_identity` that the retry bound does not count;
  7. *stored actionable key and trigger together (round 7, `LPR-R30-001`; results
     `LPR-R31-001`):* the same state as case 2 (it is the case-2 state, asserted
     here for the ordering, not for a second result): at
     `AWAITING_FUNCTIONAL_REVIEW` (and `MILESTONE_COMPLETE`), `38d` emits
     `pr.apply_review`, whose first step is the fresh query, never
     `reopen_work_item` from the stored key, and the results are exactly case 2's
     (`merged`: `pr_merged`, S not in `applied`; `closed`: `pr_fact_superseded`,
     S not in `applied`); a fake-`gh` open red result reopens at most once; and with
     `gh` unavailable (`forge_unavailable`) nothing is reopened or applied and the
     trigger blocks. The contrasting `pr_fact_refreshed` is asserted only where no
     stored actionable key existed (case 3, and a stored green or `closed` fact);
- both kinds are accepted and recorded under the all-human configuration;
  functional evidence has no decision effect, and an actionable
  `CHANGES_REQUESTED` `workflow_gh` fact reopens an eligible item under all-human
  too, and a reported `CHANGES_REQUESTED` fact makes `38d` emit `pr.apply_review`
  (never row 39) whose query decides (`LPR-R3-003`, `LPR-R28-001`, golden case:
  all-human plus a reported `CHANGES_REQUESTED` fact and a fake-`gh` red answer);
- **position relative to the anchor (`LPR-R3-001`):** polling an unpushed
  bounded fix's old PR head after the new technical approval records it and
  neither reopens nor emits `pr.apply_review` (*behind*); a PR head with new
  protected content still reopens with `content_changed` (*ahead*); a *behind*
  fact is never `pr_fact_current` and never satisfies `pr_approved` or `ci_green`
  (**I1**: its failed checks or `CHANGES_REQUESTED` are not ignored, see CP4);
- **commit contracts (`LPR-R3-002`):** a technical-approval commit and a
  `post-fix` generation-record commit, each after an ingest of both kinds at
  `IMPLEMENTING`, pass their exhaustive validators with `gate_evidence`
  residue;
- **cross-item residue (`LPR-R4-002`, `LPR-R5-001`):** an ingest of both kinds
  for a `MILESTONE_COMPLETE` item X, then another item Y's technical-approval
  commit and its generation-record commit, each passes its **unchanged**
  validator and the commit's state blob contains no change to X; the same with a
  non-actionable fact (a *behind* head, a re-poll with a new `observed_at`, a
  functional record); the reverse, X's own commits passing while Y carries
  `gate_evidence` residue; X's residue is still in the working-tree file
  afterwards; and a hand-built commit carrying a foreign `technical_approval`,
  a foreign forward `phase` edge, a foreign ledger write, a foreign unrelated
  field or any top-level change is still refused (item 267 unweakened);
- **the `gate_evidence` shape (`LPR-R11-002`):** `pr_reported` and `pr_keys`
  round-trip through `validate_state` and an unknown key is rejected; replacing
  either slot (a `workflow_gh` re-query, a newer reported fact) keeps
  `pr_keys.reopened_for`, `applied` and `ingest_seq`; an `ingest_seq` is assigned
  by the Workflow, strictly increasing, and independent of the reporter's
  `fetched_at`; `pr_keys` never holds a key derived from a reported fact.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Automatic milestone acceptance

**Files:**

- `payload/scripts/workflow_gate_policy.py`: `evaluate_gate('acceptance')`
  with the requirements of D-GP-Acceptance (checkpoints, technical approval,
  functional flows, `pr_fact_current`, `no_standing_pr_objection`, `ci_green`
  and `pr_approved`; the library predicate, for
  example `assert_acceptance_evidence_current`, shipped and tested here,
  `LPR-R2-005`), including the `obtainable` set.
- `payload/scripts/workflow_state.py`: the item's optional
  `acceptance_satisfaction` and its validator; the writer that records it in
  the same mutator as `complete_work_item`.
- `payload/.claude/commands/satisfy-gate.md`: the `acceptance` stage, citing
  `/accept-milestone`'s steps by number, the step every acceptance opens with:
  the Workflow's own forge query (`query_forge_pr_facts`, D-GP-Trust, over the
  resolved `gh` of D-GP-ThreatModel), whose failure (`forge_unavailable`, or
  `forge_undecidable` for an unsafe `gh` or a full page) blocks the gate, and the
  step every stage **closes** with, in the order of D-GP-Satisfy "Order of the
  floor" (`LPR-R23-003`): evaluate against the virtual floor, perform the
  satisfying commit, and only **afterwards**, if the committing evaluation
  observed a setting stricter than `gate_policy_floor`, record it
  (`record_gate_policy_floor`) in its own floor commit
  (D-GP-Policy, "Bundle generation"), so `HEAD` never moves past an open plan or
  technical bundle before the gate is satisfied; a test pins that the floor
  commit follows the satisfying commit and that the open bundle still verifies at
  the satisfying step.
- `payload/.claude/commands/accept-milestone.md`: the added `requires_pr_approved`
  pre-flight at step 2a for a human acceptance, step 5 pinned to copy
  (`LPR-R2-003`), and a pointer sentence naming `/satisfy-gate acceptance`.
- `payload/.claude/commands/apply-functional-review.md`: a cross-reference.

**Tests:**

- `evaluate_gate('acceptance')` is `satisfiable` exactly when the toggle is
  automatic and every requirement holds; each one failing alone makes it
  unsatisfiable: an outstanding checkpoint, a stale or missing technical
  approval, no functional flow, a failed flow, a missing `required_flows` entry,
  no pull-request fact, a stored `orchestrator_forge` fact (any age, any content),
  a `pending` or failed check (`ci_green`), an unapproved or closed PR when
  `requires_pr_approved`, a standing `CHANGES_REQUESTED` objection;
- **I1, a red PR behind a local fix:** after a bounded fix is approved locally
  and the functional evidence is current, with the last stored `workflow_gh` PR fact still
  red (failed checks or `CHANGES_REQUESTED`) at the **older** head (*behind* the
  approved implementation), automatic acceptance is **blocked**
  (`pr_fact_current` unmet, with the push-and-report remedy), and row `38f`, not
  `acceptance.satisfy`, is emitted (with only an `orchestrator_forge` fact stored, `38d`
  emits the query when PR review is enabled and the report differs, else `38h` is
  emitted, and the act's query then decides, `LPR-R10-003`, `LPR-R28-001`); a fact for an older **green** head blocks the
  same way; a fact at a head that descends from the anchor with equal identity
  and green checks satisfies it; a fact at the current head that is red or
  `CHANGES_REQUESTED` is `no_standing_pr_objection`-unmet and not obtainable
  (blocked, `38i`); a fact for different protected content (*ahead*) does not
  satisfy it;
- **the trust boundary at acceptance:** a fabricated `functional_evidence`
  record and a fabricated forge fact each go through the paths of CP3; only the
  first can satisfy the gate (the second is tighten-only, `LPR-R9-002`), and the
  acceptance record names its `log_digest`, `run_ref` and the pull-request fact's
  provenance (`workflow_gh`) and `raw_sha256`; `/satisfy-gate acceptance` run
  with `gh` unavailable **refuses** (the gate does not pass) and writes nothing, whatever
  `orchestrator_forge` facts are stored, including a self-consistent all-green
  one; with `gh` available the same fabricated fact changes nothing: the act's
  fresh query decides, and a stored `workflow_gh` fact is overwritten by the
  newer query; a human `/accept-milestone` with `requires_pr_approved` runs the
  same query at step 2a and refuses with `gh` unavailable;
- the evidence is recomputed at evaluation time: tampering with a stored record
  (a forged identity) does not satisfy it;
- `obtainable` lists exactly the missing or pending kinds, and a failed or
  stale-and-unfixable requirement is not obtainable;
- the acceptance record validates, carries the digest, source, requirements and
  inputs, and is written only when `complete_work_item` succeeds (a refusal for
  an incomplete child, checkpoint or obligation leaves the state byte-identical);
- the completion commit carries `Workflow-Gate-Satisfied-By`;
- re-evaluation inside the transaction refuses when the toggle was turned human
  meanwhile;
- a human acceptance behaves as 2.7.0 (golden), plus the `requires_pr_approved`
  pre-flight only when set; `/accept-milestone`'s step 5 text says copy;
- the command text cites existing `/accept-milestone` step numbers;
- a remediation child can be accepted automatically and its parent unblocks.

<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Reopening the same work item into remediation

**Files:**

- `payload/scripts/workflow_state.py`: `reopen_work_item`, the item's
  optional `reopenings` list and validator; `reopenings` added to the three
  commit field sets (D-GP-Compat, `LPR-R3-002`); the item-scoped staging
  of the state-only and generation-record commits (`LPR-R5-001`; the helper is
  CP1's).
- `payload/scripts/workflow_gate_policy.py`: the call from the PR-fact ingest.
- `payload/.claude/commands/apply-pr-review.md` (new): the reopen first step
  and the branches of the cause table.
- `payload/.claude/commands/accept-milestone.md`: a re-acceptance updates the
  archive copy and roadmap row, never duplicating them.

**Tests:**

- reopen from `AWAITING_FUNCTIONAL_REVIEW` (phase unchanged) and from
  `MILESTONE_COMPLETE`; refusals for a merged PR, an incomplete child, an
  unresolvable plan path, `pr_review` disabled, and a consumed key;
- **a reopen after a real step-5 archival (`LPR-R2-003`):** the plan copied to
  `docs/milestones/completed/` leaves `plan_path` resolving and the reopen
  succeeds; a plan that was moved is refused with `reopen_plan_archived` and
  the restore remedy;
- the same changes-requested fact never reopens twice; a fix then a new fact
  reopens again;
- **a `content_changed` reopen is followed by `pr.apply_review` (row `38d`), not
  by row 39, and re-polling the same head is a no-op** (`LPR-R2-001`);
- **`/apply-pr-review`'s `content_changed` branch:** stale, then `post-fix` on a
  local `HEAD` that contains the PR head, with no edit and no findings
  classification (`LPR-R2-001`);
- **a deferred fact (`LPR-R2-002`):** a fact recorded at `IMPLEMENTING` that is
  actionable at `AWAITING_FUNCTIONAL_REVIEW` is acted on by row `38d`, whose
  action calls `reopen_work_item` first, and is not silently skipped;
- **row precedence (`LPR-R3-006`):** the "followed by `pr.apply_review`"
  fixtures are built with rows 37 and 38 non-matching (checklist evidence matches
  and no unconsumed `FUNCTIONAL_REVIEW.md` findings), and a second fixture shows
  rows 37 and 38 winning when they match;
- **commit contracts (`LPR-R3-002`, `LPR-R4-001`):** a `post-fix`
  generation-record commit after a reopen and after the `/apply-pr-review`
  no-code branch passes its validator; **the `content_changed` branch follows
  the ordering of D-GP-Reopen** (state-only commit of the reopening and the
  STALE approval, then the `post-fix` mutator, then the generation-record
  commit), that generation-record commit passes
  `validate_bundle_generation_record_commit` (its diff has no
  `technical_approval`), and the technical-approval commit after it passes
  `validate_technical_approval_commit`; the bounded-fix branch's ordering is
  asserted the same way, from a `MILESTONE_COMPLETE` item (two invocations: the
  first reopens and ends, the second runs the branch at
  `AWAITING_FUNCTIONAL_REVIEW`, `LPR-R25-001`) as well as from
  `AWAITING_FUNCTIONAL_REVIEW`; a completion commit after a re-acceptance has no
  field contract to pass (`LPR-R4-003`), and the test asserts only that the
  state is valid and `complete_work_item` ran unchanged;
- **cross-item commits (`LPR-R4-002`, `LPR-R5-001`):** after an ingest and a
  reopen for a `MILESTONE_COMPLETE` item X, another item Y's generation-record
  and technical-approval commits pass, and X's own `/apply-pr-review` commits
  (state-only and generation-record) pass while Y carries `gate_evidence`
  residue; **review-round residue in both directions:** X's re-review round
  (`/review-implementation` `APPROVE` then `/record-manual-implementation-review`
  `APPROVE`, uncommitted `phase` and `implementation_review_stages`)
  overlapping Y's generation-record and technical-approval commits, and Y
  mid-review overlapping X's `/apply-pr-review` state-only and generation-record
  commits and X's technical-approval commit; each commit passes its unchanged
  validator, contains only its own item's change, and leaves the other item's
  residue in the working-tree file until that item's own commit flushes it;
- `/apply-pr-review` without an id is refused naming the reason
  (`LPR-R4-007`);
- the no-code branch of `/apply-pr-review` terminates: the re-polled unchanged
  decision is a no-op, and automatic acceptance stays blocked by
  `no_standing_pr_objection`;
- a second acceptance leaves no duplicate archive entry or roadmap row,
  overwrites `acceptance_satisfaction`, and keeps `completion_obligations_accepted`
  when it declares no obligations (`LPR-R4-003`);
- `findings` text containing instructions is treated as data (a fixture);
- `/apply-pr-review`'s three findings branches, each ending in the existing edges
  (stale approval, `post-fix`, remediation child);
- after the full cycle the item reaches `MILESTONE_COMPLETE` again through the
  acceptance gate (automatic and human) with no change to `complete_work_item`.

<!-- /CP5 -->

<!-- CP6 -->
### CP6 — Protocol 1.1: rows, actions, `validation`, schema, human equivalence

**Files:**

- `payload/scripts/workflow_protocol.py`: `PROTOCOL_VERSION` `1.1`,
  `WORKFLOW_RELEASE` `2.8.0`, the new actions and role, the rows of
  D-GP-Rows, the `EDGES` entries, the `policy` field, `verify`'s
  `gate_policy` check, the two result kinds wired into
  `record-external-result` (`pr_review_result` refused without its forge block).
- `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`: the new
  action ids, role, `satisfied_by` values, result stage, the `forge` provenance
  block and the `policy` object.
- `payload/scripts/workflow_protocol_test.py`.

**Tests:**

- **the golden matrix (INV-1):** for every persisted phase, every governing
  version and each of a fixed set of constructed states, the 2.7.0
  `next-action`, `verify`, `describe` and `record-external-result` outputs
  (stored as fixtures, produced by the 2.7.0 module) equal the 2.8.0 outputs
  under the all-human configuration (as an unadopted and as an adopted file),
  byte for byte, apart from the deltas listed in D-GP-Compat. Row 37 and every
  existing row are unchanged;
- the default configuration's `next-action` per phase equals the expected
  automatic decisions (`plan.satisfy`, `implementation.satisfy`,
  `acceptance.satisfy`, the evidence external gates, `gate_evidence_unmet`
  blocked) and each is the only difference from the all-human matrix. **Under the
  default `require` (`OD-W2-17` (b)):** a ledger with two differing declared
  families emits `plan.satisfy`/`implementation.satisfy`; a ledger recorded before the gate was
  automatic with one family, or no `Reviewer model:` line, emits `14b`/`28b`
  with `distinct_reviewer_models` unmet and only remedies executable at that
  phase named (the human toggle and the withdrawal; `evaluate_gate`'s unmet
  `distinct_reviewer_models` `detail` names exactly those two, `LPR-R20-001`),
  **and each of them is run
  end to end, against a real repository with a generated bundle and through
  the 2.7.0 generation check, from that phase to a satisfied gate** (the toggle
  to `/approve-review`, the withdrawal through both stages again to
  `plan.satisfy`; the implementation analogue for `28b`, `LPR-R17-001`,
  `LPR-R18-001`); **an `/adopt-gate-policy` made at that phase is run too, and
  stales the bundle:** the wrapper reports `bundle_generation_mismatch`, the item
  falls to row 16 (plan) or row 30 (implementation) with that cause's remedy,
  and the withdrawal (or `implementation.recover_provenance`) then reaches
  `plan.satisfy`; the same stale ledger with `review_evidence_audited` unmet is
  tested the same way for its remedies; an `require: []` adopted before the
  bundle was generated emits `plan.satisfy` with one family (`LPR-R16-003`);
- **the floor commit never stales a needed bundle (`LPR-R18-001`):** at
  `AWAITING_PLAN_APPROVAL` and `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`, with a
  generated bundle and a `GATE_POLICY.json` that carries a tightening not yet in
  `gate_policy_floor` (an added `required_flows`, `requires_pr_approved: true`, a
  larger `reopen_on`), `/satisfy-gate plan|implementation` evaluates against the
  virtual floor, makes its satisfying commit (its own wrapper passes the
  generation check at the bundle's `HEAD`), and only then makes the non-empty
  floor commit, which passes `validate_gate_policy_floor_commit`; a refused or
  `blocked` run makes no commit, so the bundle still verifies and the wrapper is
  still `reachable` afterwards; and the floor commit, like the adoption commit,
  refuses a non-empty index apart from the state path (`LPR-R18-O1`);
- **the all-human golden case under the new default (`LPR-R16-002`):** the
  all-human configuration (an unadopted file and an adopted one) resolves
  `require` to `["distinct_reviewer_models"]`, yet its `record-external-result`
  and reviewer-command outputs write no `Reviewer model:` line and no
  `reviewer_model` ledger key, byte for byte as 2.7.0 (INV-1);
- each per-gate toggle changes only its own gate's rows, and the gate-by-version
  table of D-GP-Gates holds for every governing version (rows `14a`/`14b` at 2.1
  and 2.2, `28a`/`28b` at 2.2, `38e` to `38i` at every version, `38b` and `38c`
  winning first; `LPR-R4-005`);
- **unreachable wrappers keep their remedies under the default
  (`LPR-R5-003`):** at `AWAITING_PLAN_APPROVAL` and
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` with the default policy, an
  unreachable wrapper matches neither `14a`/`14b` nor `28a`/`28b` and reaches row
  16 and, for each row-30 cause (`bundle_generation_mismatch`,
  `implementation_provenance_stale`, `review_blocked`, `review_block_pinned`,
  `bundle_unverified`), row 30 with that cause's remedy and alternatives
  (`implementation.recover_provenance`, `implementation.apply_review`,
  regeneration), equal to the all-human decision; `14b`/`28b` appear only for a
  `reachable` wrapper with an unmet requirement;
- totality still holds with the new rows; the printed order is the
  evaluation order (14, `14a`, `14b`, 15; 28, `28a`, `28b`, 29; `38c`, `38d`,
  `38e` to `38i`, 39); every new label follows its base row, so no existing
  row's position changes (`LPR-R4-006`);
- with only an `orchestrator_forge` fact stored (any content, including all-green
  or red), the acceptance rows emit `38h` (`acceptance.satisfy`), never
  `38f`/`38g` (`LPR-R10-003`); `38d` reads that fact only as the query trigger
  (it emits `pr.apply_review` ahead of `38h` when PR review is enabled and the
  report differs from the stored `workflow_gh` fact, `LPR-R28-001`) and never for
  actionability or reopening;
- **the trigger is cleared by any successful query (`LPR-R29-001`):** run at
  `AWAITING_FUNCTIONAL_REVIEW` and at `MILESTONE_COMPLETE`, with a stored
  `workflow_gh` fact for PR X and a newer reported fact naming PR Y; the fake-`gh`
  query returns (a) `state: none` and, separately, (b) PR X. Assert that
  `38d` emits `pr.apply_review` once, that the action ends in `pr_fact_refreshed`
  (the stored fact's `ingest_seq` now exceeds the report's), that the next
  `next-action` is not `38d`, that a completed item reads `complete`, and that an
  item at `AWAITING_FUNCTIONAL_REVIEW` reaches `38h`/row 39 as its other rows
  dictate;
- **a reported fact newer than the stored `workflow_gh` fact (`LPR-R11-001`):**
  with a stored `workflow_gh` fact that is `state: none` or has `pending` checks,
  a newer reported `pr_review_result` makes `next-action` emit `38h`
  (`acceptance.satisfy`), not `38f`; its act re-queries, stores a fresh
  `workflow_gh` fact with a greater `ingest_seq` (also when it refuses) and
  acceptance completes once the checks are green. Repeated `next-action` calls
  with no new report and an unchanged stored fact emit `38f` (or `38i`) and do
  not loop on the query; each new report triggers at most one successful query. `ingest_seq`
  is Workflow-assigned: a reporter's `fetched_at` far in the future or the past
  changes nothing;
- **a human acceptance with `requires_pr_approved` (`LPR-R12-002`):** a stored
  non-`APPROVED` `workflow_gh` fact followed by a newer report emits row 39, not
  `38g`; with the fact at least as new as the report it emits `38g`, whose
  remedy names `/accept-milestone`; `/accept-milestone` step 2a stores its fact;
- **`gh` unavailable (`LPR-R12-003`):** `acceptance.satisfy` refuses naming
  `forge_unavailable` and stores nothing; the next `next-action` emits `38h`
  again (the stated retry contract), `reconcile` classifies the refusal
  `no_progress`, and "at most one successful query per report" holds;
- **`reconcile` of the `.satisfy` refusals (`LPR-R12-004`, `LPR-R13-002`):** an
  `acceptance.satisfy` refusal ending at `38f` (CI pending), row 39 (the toggle
  turned human), `38h`, `38i` and `38d` (a red fact the act stored), and a
  `plan.satisfy` / `implementation.satisfy` refusal after the toggle turned
  human, are each legal (a same-phase edge), never `invalid` and never
  `illegal_edge`, and classify **exactly** as the existing classifier computes
  (`LPR-R14-001`): `38f`, `38g` and rows 15, 29 and 39 are `gate_reached`;
  `38h` (`forge_unavailable`), `38i`, `38d` and `14b`/`28b` are `no_progress`;
  reaching the forward target is `progress`. A consumer-simulation case: a `38d`
  ending is a different action at a new `state_identity`, so it does not count
  toward CP7's retry bound (consecutive `no_progress` of the **same** action id
  at an unchanged `state_identity`); a
  `.satisfy` that reaches `MILESTONE_COMPLETE` is `progress`; each new action's
  `proof` and `allowed_results` equal the spec's table;
- **`reconcile` of `pr.apply_review` started at `MILESTONE_COMPLETE`
  (`LPR-R25-001`):** each outcome is legal (never `illegal_edge`) and gives the
  stated class: the reopen (to `AWAITING_FUNCTIONAL_REVIEW`, `progress`); a
  refusal for `pr_merged`, `pr_fact_superseded` (including a red newer-head
  fresh fact, `LPR-R26-001`), `forge_unavailable`, `forge_undecidable`,
  `pr_head_unknown`, `pr_head_not_in_branch`, an incomplete child and `reopen_plan_archived` (the unchanged
  `MILESTONE_COMPLETE` edge, `no_progress`); and the second invocation at
  `AWAITING_FUNCTIONAL_REVIEW` for the no-code branch, a bounded fix,
  `content_changed` and a broad fix, over the existing `functional.apply_findings`
  edges, per version;
- row `38f`'s external gate is emitted for a stored `workflow_gh` fact, at least
  as new as `pr_reported`, that is `state: none`, pending
  or *behind* (I1), never for an absent or orchestrator-only fact (those are
  *pending the query* and reach `38h`), and its remedy names a fresh report or
  the Workflow's own query (an orchestrator's forge fact never satisfies, only
  triggers); a current red fact reaches `38i`
  (blocked), never `acceptance.satisfy`; no `ci.evidence.external` action id or
  `ci_result` kind exists in the schema;
- every response validates against the schema;
- `validation` decisions reconcile; an unaware-consumer simulation maps each
  unknown action id to `blocked` (obligation 3) and each `validation` decision
  to a stalled item through obligation 5 (`LPR-R2-008`);
- `describe` lists the new capabilities and `1.1`.

<!-- /CP6 -->

<!-- CP7 -->
### CP7 — Specification, operator guide, update simulation, lifecycle end to end

**Files:**

- `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`: section 9 shrinks
  to what is still reserved, a gate-policy and reopening section (which states
  the trust boundary and refers to the threat model of D-GP-Trust and
  D-GP-ThreatModel), the catalogue and edge tables, the 1.1 compatibility notes (stating that the
  default switches the gates to automatic), and the "Completion is reported by
  `next-action`, never by `reconcile`" passage of section 7, amended: the
  `.satisfy` actions are automatic-or-validation actions with an edge to
  `MILESTONE_COMPLETE` (`acceptance.satisfy`), whose arrival is `progress`, and
  `/accept-milestone` remains the writer only for a human gate (`LPR-R12-004`);
  the edge table gains the three `.satisfy` forward edges **and** their three
  same-phase edges with versions (`LPR-R13-002`), and `pr.apply_review`'s
  `MILESTONE_COMPLETE` to `AWAITING_FUNCTIONAL_REVIEW` edge and its unchanged
  `MILESTONE_COMPLETE` edge, every version (`LPR-R25-001`), and the consumer obligations
  gain a recommendation that a `1.1` consumer bound its consecutive `no_progress`
  results of the **same** action id at an unchanged `state_identity` (not any
  `no_progress` result: a `38d` or `38i` ending changes `state_identity` and
  hands off to `pr.apply_review` or a `blocked` explanation); the edge table
  also states each new action's `reconcile` classes in the classifier's own
  terms (`LPR-R14-001`).
- `payload/docs/ai-workflow/GATE_POLICY.md` (new): the toggles, the safety
  rule, the evidence, the order for `requires_pr_approved`, the one-line way
  back to human gates, the note that a reopened item's roadmap and
  narrative files keep their completed state, and that a reopened item is
  surfaced only by naming it (`/apply-pr-review <id>`, `next-action
  --work-item`; `LPR-R4-007`); that enabling a reopening cause never reopens a
  completed item from a stored fact alone, because `/apply-pr-review` re-queries
  the forge first (`LPR-R25-002`); the second residual of D-GP-Reopen
  (`LPR-R33-001`, `LPR-R34-001`): a same-head red reopen with no orchestrator
  report is never remediated at `MILESTONE_COMPLETE`, nor, under human acceptance
  without `requires_pr_approved`, at `AWAITING_FUNCTIONAL_REVIEW`, where no
  Workflow query runs, and a human-acceptance repository must have an
  orchestrator report it to have it acted on (the table of D-GP-Reopen names every
  query path); a **trust-boundary section** (D-GP-Trust) that
  says in plain words that CI and pull-request facts come from GitHub (the
  Workflow's one fixed query; an orchestrator's forge fact only tightens) and a gate
  that cannot decide blocks, that review verdicts and functional evidence are
  trusted from the orchestrator that reports them, that the Workflow guarantees
  binding, freshness and audit and not provenance, what each audit record names
  (the verdict hash, the bundle and content ids, the run reference), and that
  **turning human approval on is the stronger mode**; a **threat-model section**
  (D-GP-ThreatModel) that names it and states in plain words that the guarantees
  of INV-5, INV-6 and the GitHub-sourced facts hold against an agent acting
  through the Workflow's commands and protocol and **not** against an agent that
  deliberately forges commits, trailers or state by hand or replaces system
  programs (the same limit as `/approve-review` and `/accept-milestone`), that no
  signed commits or GitHub-side adoption are provided, which `gh` is trusted (the
  resolution rule and what it records), what a **gate-lowering event** is and
  where it is reported (`verify`, `next-action`, the audit record), and that
  human approval is the stronger mode; the floor, the provenance
  failure (`provenance_failed`) and its way out; that automatic acceptance needs
  an open pull request first (`OD-W2-18`); that `distinct_reviewer_models` is
  **on by default** for the automatic plan and technical gates and configurable
  (`OD-W2-17` (b), decided by the user on 2026-10-03), with the **single-subscription
  remedies as first-class paths**: record a review from a second declared
  family at ingest, while the stage is open (a manual `APPROVE` without a
  distinct `Reviewer model:` is refused there, D-GP-Ingest); turn that gate
  human (immediate, no adoption, and it avoids any gate-lowering signal;
  returning that gate to automatic later is itself a loosening and a
  gate-lowering event, and the floor keeps it human for later items until an
  adoption, `LPR-R17-O3`); or adopt a policy without the requirement through
  `/adopt-gate-policy` **before the stage's bundle is generated** (adopting
  while a bundle is open stales it, `LPR-R18-001`: the guide names the
  withdrawal, or `/recover-implementation-provenance` at the implementation
  stage, as the way out), which is a gate-lowering event and shows as a
  permanent `warn` and a `gate_lowering` object while that adoption is the
  newest, the expected and legitimate signal for that setup (`LPR-R16-O3`); what a family is
  meant to be (a vendor-level identity such as `anthropic/...` against
  `openai/...`) and that values are declared and unverified (`LPR-R16-O4`,
  `OD-W2-3`); `MILESTONE_WORKFLOW.md`,
  `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`, `REVIEW_PROTOCOL.md` as they
  reference gates. **No file under `docs/ai-workflow/` quotes a governing
  version list in quotes or in the `only` forms the installed sweep
  forbids; versions are written unquoted.**
- `payload/scripts/workflow_integration_test.py` or
  `workflow_protocol_test.py`: the end-to-end tests.

**Tests:**

- the spec's mirrored tables equal the code's;
- a docs check requires `GATE_POLICY.md` and the protocol document to state the
  trust boundary and the stronger human mode in the words above, requires
  `GATE_POLICY.md` to carry the named threat-model section with its three
  statements (what is guaranteed, what is not, the safeguards) and the
  gate-lowering event, and requires that neither offers CI-produced functional or
  review evidence, and requires `GATE_POLICY.md` to state both reopening
  residuals, the second with its human-acceptance case (`LPR-R34-003`);
- **update simulation, both configurations:** a disposable repository at 2.7.0
  with items in several phases is updated to 2.8.0. (a) With no policy file:
  no file other than the managed ones changes, the state is unchanged, and each
  item's `next-action` changes exactly as D-GP-Compat's default list says (the
  human gates become the automatic or `blocked` decisions). It includes one
  in-flight item whose declaration predates the `docs/ai-workflow/` exclusion
  (`LPR-R19-O1`, `LPR-R20-002`), run through the real generation check in two
  cases: (i) **before generation**, the toggle's new `GATE_POLICY.json` raises
  `UnclassifiedPathError`; committing the file on top of `base_commit` still
  raises `UnclassifiedPathError` in both the plan-stage and the
  implementation-stage classifiers, and declaring the `docs/ai-workflow/` prefix
  or the exact path clears it (`LPR-R21-001`); (ii) **with a generated bundle**, at
  `AWAITING_PLAN_APPROVAL` and at its implementation analogue
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`, adding the prefix to the declaration
  leaves the readers refusing, and committing the file leaves them refusing; each
  assertion accepts any of `UnclassifiedPathError`, `ReviewedContentDriftError`,
  an unverified bundle or `WorktreeOrHeadMismatchError`, and pins none, because
  the error raised depends on check order; the withdrawal route (with the prefix
  excluded before regeneration) reaches the gate. The
  simulation covers the default path: an in-flight 2.7.0 item whose ledger lacks the audit
  keys and any `Reviewer model:` line blocks at `14b`/`28b` on **both**
  `review_evidence_audited` and `distinct_reviewer_models`, with their remedies
  named together; the route the commands allow is run: the human toggle then
  `/approve-review` (or the technical approval) reaches the gate immediately,
  and the withdrawal route reaches `plan.satisfy` after both stages are
  re-recorded with a declared family each (no command re-records one stage in
  place; D-GP-Ingest). Both are run against the simulation's real generated
  bundle, through the generation check. **The adoption is not a route at that
  phase** (`LPR-R18-001`): the simulation runs it and asserts that it stales the
  bundle (`bundle_generation_mismatch`), so only the toggle and the withdrawal
  are real routes for an in-flight item; the guide says adoption is for before
  the bundle is generated. (b) With
  `"human_approval": true`: every item's `next-action` is unchanged apart from
  the version fields. The downgrade posture is tested: 2.7.0 refuses a state
  holding a new field or basis, and reads a state that holds none;
- **automatic lifecycle, protocol-only, default policy:** plan reviewed by two
  reviewers and satisfied automatically; implementation likewise; flows
  reported and a forge fact for the approved head reported with provenance;
  acceptance satisfied automatically (including the sequence **acceptance
  attempted while CI is pending**: the act refuses and stores a `workflow_gh`
  fact with `pending` checks, `next-action` emits `38f`, CI goes green, the
  orchestrator reports a fresh `pr_review_result`, `next-action` emits `38h`, its
  act re-queries and acceptance completes, `LPR-R11-001`); a changes-requested fact
  reopens the item; remediation, re-review, re-validation, completion again;
- **mixed lifecycle:** only the plan human, and only the acceptance human, each
  stops at exactly that gate and runs the others automatically;
- **all-human lifecycle:** every gate stops for a person as in 2.7.0, and a
  reported `CHANGES_REQUESTED` fact triggers the Workflow's query, and a red
  answer reopens the item and is followed by `pr.apply_review` (`LPR-R3-003`,
  `LPR-R28-001`);
- the installed documentation sweeps pass over the new documents.

<!-- /CP7 -->

<!-- CP8 -->
### CP8 — Release 2.8.0

**Files:**

- `manifest.json`: `workflow_version: "2.8.0"`; entries for
  `scripts/workflow_gate_policy.py`, `docs/ai-workflow/GATE_POLICY.md` and
  the new commands (`adopt-gate-policy`, `satisfy-gate`, `apply-pr-review`;
  `distribution`), `scripts/workflow_gate_policy_test.py` (`conformance`);
  refreshed `sha256`/`size` for every changed file; `counts`; each changed
  entry's `rationale` names W2.
- `templates/.github/workflows/workflow-conformance.yml` and
  `.github/workflows/workflow-ci.yml`: a step for the new suite; the
  template's digest in `manifest.templates`.
- `docs/ROADMAP.md`: W2 complete pending cutover; a "Workflow 2.8.0" entry;
  the two roadmap sections marked delivered.
- `docs/RELEASING.md` only if a sentence is needed.

**Order.** The manifest digests are committed **before** the
bundle-generation record, so the reviewed head already carries correct
digests.

**Verification:**

- `release.py build --commit HEAD` reports 2.8.0 and the release-constant
  guard accepts `WORKFLOW_RELEASE`;
- `check-title "feat: Workflow 2.8.0 with toggleable gates, automatic
  acceptance and PR reopening" --agree` and `check-pending` report
  `2.7.0 -> 2.8.0 (minor)`;
- all nine release-source suites are green in the staged fixture;
- `release_test.py` is green, including the earlier-release reproductions;
- `workflow-manager verify .` is clean.

<!-- /CP8 -->

## 6. Tests and verification summary

| what | where | when |
| --- | --- | --- |
| policy schema, toggles, default, tighten-only table, adoption | `workflow_gate_policy_test.py`, `workflow_state_test.py` | CP1 |
| roadmap refresh | docs check | CP1 |
| satisfiable evaluation, `POLICY_SATISFIED`, audit record, commit trailers, reviewer model | `workflow_gate_policy_test.py`, `workflow_state_test.py`, `workflow_fingerprint_test.py` | CP2 |
| evidence identity, cause table, invalidation table | `workflow_gate_policy_test.py` | CP3 |
| acceptance evidence, `acceptance_satisfaction`, step 5 copy | `workflow_gate_policy_test.py`, `workflow_state_test.py` | CP4 |
| reopening, remediation, re-completion, deferred facts | `workflow_gate_policy_test.py`, `workflow_state_test.py` | CP5 |
| golden all-human equivalence matrix, rows, schema, `validation` | `workflow_protocol_test.py` | CP6 |
| spec equals code, update simulation (both configurations), lifecycles, doc sweeps | `workflow_protocol_test.py`, `workflow_integration_test.py`, `workflow_state_test.py` | CP7 |
| package, build guard, conformance fixture, pinned Manager | `release_test.py`, `release.py`, CI | CP8 |
| the existing suites stay green | release-source conformance fixture | every checkpoint |
| installation untouched | `workflow-manager verify .` | every checkpoint, acceptance |

## 7. Release and follow-ups (owner actions, after acceptance)

1. Open the pull request with the title `feat: Workflow 2.8.0 with toggleable
   gates, automatic acceptance and PR reopening` (impact `minor`, agreeing with
   2.7.0 to 2.8.0). Merge it when `aggregate`, `Conventional Commit title` and
   `workflow-conformance` are green; `Release` then publishes `v2.8.0`.
2. Open a `workflow-manager` pull request that pins 2.8.0 (the archive and
   manifest digests, `CI_SUITES["2.8.0"]` with nine suites and their exact
   counts, the portability-exceptions entry).
3. Afterwards, install 2.8.0 here with `workflow-manager update`, in its own
   pull request. **That update switches this repository's gates to automatic**
   unless it first adds a `GATE_POLICY.json` with human approval on; the update
   pull request decides, and this repository's own pull-request-after-acceptance
   flow is a reason to keep acceptance human there.
4. **The Controller, until C10.** Controller releases that pin script hashes
   refuse 2.8.0 until they admit it. An unaware `1.0` consumer stalls at a
   `validation` decision (INV-8). A repository on 2.8.0 is driven by people until
   then.

## 8. Risks

| risk | mitigation |
| --- | --- |
| A repository updated to 2.8.0 starts accepting its own gates automatically | stated plainly in the compatibility notes, the operator guide and the update simulation; the one-line way back (`"human_approval": true`); every satisfaction is audited (INV-4) |
| The all-human configuration drifts from 2.7.0 | INV-1; the golden matrix and the update simulation; the delta list is exhaustive and tested |
| An agent loosens a gate by editing, deleting or corrupting the policy file, or by editing the adopted policy or the floor in the state | the effective policy is the stricter of the committed adopted policy, a recorded floor and the file, so a setting the Workflow has seen survives the file's deletion or edit; the adopted policy and the floor are verified by their content and the chain of their changes, which survives this repository's squash merges, and a mismatch fails closed to all gates human; only the user-only adoption loosens; `verify` reports ignored loosenings and a failed provenance. Residuals: a setting never observed durably (including one committed and deleted inside a single squashed branch), and a hand-built self-consistent adoption record, outside the threat model (D-GP-ThreatModel) and reported as a gate-lowering event by `verify`, `next-action` and the audit record (stated in D-GP-Policy; human approval is the stronger mode) |
| An agent deliberately forges commits, trailers or state by hand, or replaces a system program (`gh`, `git`) | **outside the threat model** the user decided on 2026-10-03 (D-GP-ThreatModel): the Workflow's guarantees hold against an agent acting through its commands and protocol, the same limit as today's user-only gates; no signed commits and no GitHub-side adoption are added. Safeguards: `gh` resolves to an absolute path and is refused when inside the repository, a worktree, the temp directory or a world-writable directory (its path and sha256 recorded); every gate-lowering adoption is flagged and reported; human approval is the stronger mode |
| A truncated `gh pr list` hides a matching red pull request | an explicit `--limit 200`; a full page is `forge_undecidable`, in the query and in `parse_forge_raw` |
| Automatic satisfaction weakens a precondition | `evaluate_gate` requires the existing wrappers and predicates first (and `complete_work_item`'s refusals at acceptance); tests for each failing input |
| Missing or stale evidence passes a gate | an automatic gate with unmet evidence is `blocked` or an `external_gate`, never passed; evidence is recomputed at evaluation, never read back |
| `/satisfy-gate` and `/approve-review` or `/accept-milestone` drift | the command cites step numbers; a test checks they exist; the shared transaction is not copied |
| Review verdicts or functional evidence are reported but never happened | stated boundary (`OD-W2-4`, `OD-W2-19`, D-GP-Trust): trusted from the orchestrator, the Workflow guarantees binding, freshness and audit, not provenance; every automatic satisfaction records the verdict hash, the bundle and content ids and the run reference; `required_flows` pins what must exist; human approval is the stronger mode |
| A repository with no CI, no pull request or no `gh` blocks at acceptance | `blocked` with the remedy named, or, for an unavailable `gh`, an `acceptance.satisfy` refusal naming `forge_unavailable` that `reconcile` classifies `no_progress` (`OD-W2-15`, `OD-W2-18`, `LPR-R12-003`): a CI or pull-request fact that satisfies a gate is never taken from an agent's word (an orchestrator's forge fact only tightens, `LPR-R9-002`), and a gate that cannot decide fails closed |
| Under the default, nothing requires a person or a second model family between an agent-authored plan and its approval | the two-stage ledger needs a second reviewer stage, but the `MANUAL_EXTERNAL_*` stage is not user-gated (`/record-manual-plan-review` has no `disable-model-invocation`; `record-external-result` ingests orchestrator-supplied text), so it is trusted as reported by whoever drives the ingest; `distinct_reviewer_models` is on by default for the automatic plan and technical gates (`OD-W2-17` (b), decided by the user on 2026-10-03), though the families are declared and unverified (`OD-W2-3`); a person can turn any gate human |
| Declared model families are not verified | stated limit (`OD-W2-3`); the evidence records the declared values |
| A reopen after completion meets an archived plan or open child | explicit refusals with remedies (D-GP-Reopen), step 5 pinned to copy, each tested |
| An unpushed bounded fix makes the old PR head look like new content, or hides a red PR | the position relative to the anchor: a head behind the anchor is recorded, non-current and not actionable for a reopening (`LPR-R3-001`), and it **blocks automatic acceptance** (`pr_fact_current`, I1) until a fact for the current head is reported |
| New state writes become residue that an exhaustive commit validator refuses | each writer's durability is designed in D-GP-Compat, with the item whose commit carries it: residue admitted for `gate_evidence` and `reopenings`, the adoption in its own commit, no top-level write from a reopen, item-scoped staging so another item's ingest, reopen and review-round residue never enters a commit (the adoption staged top-level-scoped), and the STALE write committed on its own before the generation commit; tested per writer and across items in both directions (`LPR-R3-002`, `LPR-R4-001`, `LPR-R4-002`, `LPR-R5-001`, `LPR-R5-002`) |
| The PR head is not in the repository or branch | `pr_head_unknown` / `pr_head_not_in_branch` with the fetch remedy |
| PR `findings` text carries instructions | treated as untrusted data; the applier has three bounded branches (`LPR-R1-006`) |
| A review decision for an earlier head reopens the item | decisions apply only when `reviewed_head` equals `head` |
| The same fact reopens twice, or a reopen hides itself from `38d` | consumption keyed on a semantic identity per cause, with separate `reopened_for` and `applied` sets and one cause table (`LPR-R1-001`, `LPR-R2-001`) |
| A state written by 2.8.0 meets 2.7.0 | refused loudly by its validator, never partially read (`OD-W2-13`); the downgrade posture is stated |
| The installed documentation sweep fails on a new document | versions are written unquoted; CP7 runs the sweeps over the new files |
| Manifest digests are stale at the reviewed head | CP8 commits them before the bundle-generation record |
| The release-source freeze while 2.8.0 is pending | publish promptly after merging |

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/gate-policy-and-reopening-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | A declarative gate policy: a closed schema, an automatic default, a master human-approval switch and per-gate overrides for the plan, implementation and acceptance gates, a default that requires distinct reviewer model families for the automatic plan and technical gates (configurable; removing it is a loosening), and user-only adoption by digest | CP1 |
| REQ-2 | Safety: an agent can never loosen a gate; the effective policy is never looser than the committed adopted policy or the recorded floor of every setting observed in the file, an edited, deleted or invalid file never loosens it, and the adopted policy and the floor are verified by their content and the chain of their changes, which survives squash merges, with a stated merge rule for concurrent branches (a floor conflict resolves to the stricter side for the fields both changed and to the changed side otherwise, a concurrent second adoption is re-adopted; a mismatch fails closed to all gates human); the guarantee is stated under the named threat model (an agent acting through the commands and protocol, not one forging state by hand), and every gate-lowering adoption is flagged in its record and reported by verify and next-action | CP1 |
| REQ-3 | Human equivalence: with every gate human, behavior equals 2.7.0's apart from the listed deltas; the update to 2.8.0 is stated and simulated for both the default and the all-human configuration | CP6, CP7 |
| REQ-4 | Plan and implementation approvals satisfied automatically by current local and external review evidence, with every existing precondition retained, distinct declared reviewer families by default, the single-family remedies named when it blocks, and an auditable record | CP2 |
| REQ-5 | Functional flows and GitHub-sourced pull-request facts (CI is the fact's checks) ingested as identity-bound evidence; the Workflow owns every invalidation rule and the next legal action | CP3, CP6 |
| REQ-6 | Milestone acceptance satisfied automatically by evidence (every checkpoint complete, a current technical approval, passing functional flows, and a GitHub-sourced pull-request fact for the exact approved head with no failing checks and no `CHANGES_REQUESTED`, and by policy green and approved), audited, and blocked when evidence is missing, stale, behind a local fix or undecidable | CP4 |
| REQ-7 | A red or changes-requested pull request reopens the same work item into remediation, with re-review and re-validation, and the item completes again | CP5 |
| REQ-8 | Protocol 1.1: additive rows, actions and kinds, `validation` emitted, schema, `describe`, unaware consumers fail closed or stall | CP6, CP7 |
| REQ-9 | Specification, operator guide and lifecycle end-to-end tests (automatic, mixed and all-human); installed documentation sweeps pass | CP7 |
| REQ-10 | 2.8.0 releasable: manifest, conformance CI for the new suite, release-constant guard | CP8 |
| REQ-11 | The roadmap refresh: W1 complete including the cutover, W2 in progress, then complete pending cutover | CP1, CP8 |
| REQ-12 | The trust boundary: CI and pull-request facts that satisfy a gate come only from GitHub through the Workflow's one fixed query run in the satisfying transaction (an orchestrator's forge fact is tighten-only: it can only trigger that query, never decide or satisfy) and a gate that cannot decide blocks; review verdicts and functional evidence are trusted from the orchestrator with a stated boundary and an audit trail (verdict hash, bundle and content ids, run reference); human approval is documented as the stronger mode; no CI-produced evidence; the Workflow resolves gh to an absolute path and refuses one inside the repository, a worktree, the temp directory or a world-writable directory (recording its path and sha256), and a full page of pull requests is undecidable | CP2, CP3, CP4, CP7 |

## 10. Artifact classification

`docs/ai-workflow/registry/gate-policy-and-reopening-artifacts.json` comes
from the `process` template and is fitted to this plan's footprint. It is
unchanged by this revision.

**Plan stage.**

- The template as generated, plus these exclusions: `manifest.json`,
  `docs/RELEASING.md`, `payload/`, `fixtures/`, `templates/` and `tools/`,
  the same set W1 added. The plan document itself, the registry and the
  mapping are the protected plan-stage paths.
- Every path this plan names is classified at the plan stage: `payload/…`,
  `templates/…`, `fixtures/…`, `tools/…`, `manifest.json` and
  `docs/RELEASING.md` (excluded above), `docs/ROADMAP.md` and every
  `docs/ai-workflow/…` file (excluded by the template), `docs/milestones/completed/`
  (a path in a repository that follows `/accept-milestone` step 5, named only as
  data), `.github/…` (excluded by the template's prefix), and this plan, the
  registry and the mapping (protected). CP1 of the implementation runs
  `classify_path` over every path in this document as a check.

**Implementation stage.** Added to the protected set: `manifest.json`,
`docs/RELEASING.md`, the prefixes `payload/`, `fixtures/`, `templates/` and
`tools/`, and the exact path `.github/workflows/workflow-ci.yml`. The
template's protected `scripts/` and `.claude/commands/` prefixes (the
installation) stay protected, and any change there would be reviewed.
`docs/ROADMAP.md` stays excluded as bookkeeping.

**A residual (`LPR-R19-O1`, `LPR-R20-002`).** A declaration that predates the
`docs/ai-workflow/` default exclusion does not classify a new or changed
`docs/ai-workflow/GATE_POLICY.json`; the toggle then raises
`UnclassifiedPathError` for that in-flight item. Before the stage's bundle is
generated, the only remedy is to classify the path in the declaration (exclude
the prefix or the exact path); committing the file never clears it (the path is
still changed against `base_commit`, and the commit moves `HEAD`). With a bundle
open, neither works (the declaration is bound content) and the toggle cannot be used for that item: the remedies are the
withdrawal or regeneration of `14b`/`28b` (D-GP-Compat).

## 11. Review rounds and decisions

### User decisions

- **2026-10-03, gate toggles and automatic acceptance.** The user decided, in
  the words quoted in section 1, to add automatic acceptance now and to make
  the human gates (plan, implementation, milestone acceptance) toggleable, by
  default off, with a master switch and a per-gate override. This supersedes
  the earlier instruction that the default must reproduce 2.7.0's gates, and
  replaces the earlier plan text that said acceptance stays human (that text is
  removed: no user statement said it, and it was this plan's own reading).
  Applied in: INV-1, INV-5, INV-6, INV-7, D-GP-Policy, D-GP-Acceptance,
  `OD-W2-2`, `OD-W2-5`, `OD-W2-9`, D-GP-Compat, CP4 and the registry (a new CP4).

- **2026-10-03, the trust model.** The user decided, after the manual external
  review of revision 8 found that evidence ingestion could be fabricated, that
  (a) CI and pull-request facts used by an automatic gate come from GitHub and
  never from an agent's word: in a standalone session the Workflow's own step
  queries GitHub with one fixed, built-in `gh` invocation for the exact head and
  repository (not a command named in a repository file, so `OD-W2-4` holds),
  through the protocol a fact is accepted only with the forge provenance a
  deterministic orchestrator such as the Controller's forge module supplies,
  **for recording, reopening and blocking only: such a fact is tighten-only and
  never satisfies a gate** (confirmed by the user's decision below), and
  a gate that cannot decide because `gh` is unavailable or the answer is
  undecidable **blocks**; (b) review verdicts (local and external) and
  functional evidence are **trusted from the orchestrator**: the Workflow
  guarantees binding, freshness and audit, not provenance, every automatic
  satisfaction keeps an audit trail (the verdict's hash, the bundle and content
  ids, a reference to the producing run's log), and turning human approval on is
  the stronger mode, which the operator guide says; (c) functional or review
  evidence is **not** produced in CI in this release, and is not planned as a
  policy option either. Applied in: INV-9, D-GP-Trust, D-GP-Evidence,
  D-GP-Invalidation, D-GP-Acceptance, `OD-W2-4`, `OD-W2-15`, `OD-W2-18`,
  `OD-W2-19`, CP2 to CP4 and CP7, REQ-12.

- **2026-10-03, the threat model (option A).** The user was told that an agent
  running on the same machine can write any file, make any commit and install
  any program, so no local mechanism can tell the user's `/adopt-gate-policy`
  from a perfect hand-built forgery, or the real `gh` from a fake one, and that
  today's user-only gates (`/approve-review`, `/accept-milestone`:
  `disable-model-invocation` plus the confirmation text) have the same limit.
  The user decided: (1) the threat model is the same as today's human gates:
  Workflow 2.8.0's guarantees (INV-5, INV-6 and the GitHub-sourced facts) hold
  against agents acting through the Workflow's commands and protocol, not
  against an agent deliberately forging commits, trailers or state by hand or
  replacing system programs; this is an explicit, named threat-model section
  (D-GP-ThreatModel), referenced from INV-6, the trust boundary, the operator
  guide and the residuals list; the external review's two Blocking findings are
  resolved by this statement plus the safeguards below, and the plan adds **no**
  signed commits and **no** GitHub-side adoption; (2) the cheap safeguards: (a)
  `gh` resolves to an absolute path and is refused (`forge_undecidable`, so the
  gate blocks) when inside the repository, any worktree, the temp directory or a
  world-writable directory, and the GitHub fact records the resolved path and
  the executable's sha256; the CP3 tests inject the runner instead of a fake
  `gh` on `PATH`; (b) every adoption that lowers any gate is flagged in its audit
  record and reported by `verify` and `next-action` as a gate-lowering event.
  Applied in: INV-6, INV-9, D-GP-ThreatModel, D-GP-Policy, D-GP-Trust,
  D-GP-Rows, `OD-W2-2`, CP1, CP3, CP4, CP7, REQ-2, REQ-12 and the risks table.

- **2026-10-03, `OD-W2-17` (b): `distinct_reviewer_models` is configurable and on
  by default.** The user decided option (b) for the automatic plan and technical
  gates, in these words: "Allow it to be configurable, to choose, by default its
  b. But not every user nor me will always have access to both subscriptions."
  The default `require` of both gates is `["distinct_reviewer_models"]`.
  Switching it off is a loosening, so it goes through the user-only
  `/adopt-gate-policy` and is reported as a gate-lowering event; a file cannot
  do it. The single-subscription remedies are first-class and documented:
  record a review from a second declared family; turn that gate human
  (immediate, no adoption); or adopt a policy without the requirement. The
  `Reviewer model:` line is written only for an automatic gate that requires it,
  so INV-1 holds under all-human. Applied in: D-GP-Policy, D-GP-Gates,
  D-GP-Compat, D-GP-Rows `14b`/`28b`, `OD-W2-3`, `OD-W2-17`, CP1, CP2, CP6, CP7,
  the risks table, REQ-1 and REQ-4.

- **2026-10-03, `LPR-R9-002`: keep tighten-only.** The user decided to keep the
  round 9 design. An orchestrator-supplied forge fact is tighten-only: it is
  recorded, and can only trigger the Workflow's own query; it never decides and never satisfies a gate (restated as one principle by `LPR-R28-001`). Only
  the Workflow's own fixed `gh` query, run inside the satisfying transaction,
  satisfies one. Confirms INV-9, D-GP-Trust, D-GP-Invalidation and REQ-12 as
  written.

### Round 1 (local model plan review, revision 1 to 2)

All of `LPR-R1-001` to `LPR-R1-008` were accepted, each validated against the
release source (`payload/scripts/workflow_state.py` `APPROVAL_STAGES`,
`resolve_approval_basis`, `validate_user_confirmation`;
`payload/scripts/workflow_protocol.py` `unsupported_result_kind`,
`protocol_version`; `docs/ROADMAP.md:176`).

- `LPR-R1-001`: consumption is keyed on a semantic identity with separate
  `reopened_for` and `applied` sets (D-GP-Invalidation, D-GP-Rows `38d`); tests
  added to CP3 and CP5.
- `LPR-R1-002`: the anchor is defined once; the identity-changed row reopens
  with `content_changed` and never stales in place; every phase's ingest
  behavior is specified; tests added to CP3.
- `LPR-R1-003`: `resolve_policy_approval_basis`,
  `validate_gate_policy_confirmation` and
  `validate_policy_satisfied_confirmation` replace the reuse; `APPROVAL_STAGES`
  is unchanged; tests added to CP1 and CP2.
- `LPR-R1-004`: acceptance enforcement is recomputed at acceptance time, never
  read back (now the six requirements of D-GP-Acceptance, CP4).
- `LPR-R1-005`: INV-1/INV-8 restated with the exhaustive delta list in
  D-GP-Compat (rewritten in revision 3 for the new default); the
  `Reviewer model:` line is written only when a policy requires it.
- `LPR-R1-006`: `findings` are untrusted data (D-GP-Reopen).
- `LPR-R1-007`: the order and the `checks` semantics are stated (D-GP-Acceptance).
- `LPR-R1-008`: the CP1 roadmap refresh covers `docs/ROADMAP.md:176`.

### Round 2 (local model plan review, revision 2 to 3)

Revision 3 also applies the user decision above, which reshaped D-GP-Policy,
the acceptance design and the checkpoints. Every finding below was validated
against the release source before applying.

- `LPR-R2-001` (accepted): `content_changed` has a key, a row in the single
  cause table (D-GP-Invalidation), a `38d` condition that does not require
  currency for it, and an `/apply-pr-review` branch (stale, then `post-fix` with
  no edit, which `record_bundle_generation` allows at
  `AWAITING_FUNCTIONAL_REVIEW` for a `STALE` approval). Tests in CP3 and CP5.
  The architecture concern (three per-cause definitions in three places) is
  answered by that one table.
- `LPR-R2-002` (accepted, mechanism (b)): row `38d` matches a stored actionable
  fact whose key is not in `applied`, and its action calls `reopen_work_item`
  first. No phase hook and no orchestrator re-poll obligation. Test in CP3 and
  CP5.
- `LPR-R2-003` (accepted): `payload/.claude/commands/accept-milestone.md:149-150`
  does say "Archive ... to `docs/milestones/completed/`" without copy or move.
  Step 5 is pinned to copy (CP4, listed as a delta); the refusal stays as the
  fallback for an already-moved plan, with a restore remedy. Test after a real
  step-5 archival in CP5. The usability concern (the roadmap and narrative
  keep their completed state after a reopen) is stated in D-GP-Reopen and
  `GATE_POLICY.md`.
- `LPR-R2-004` (accepted, resolved by a design change): row 37 is not modified.
  The checklist stays in every mode and names the flows; the automatic gate
  reads evidence. D-GP-Rows "no existing row changes" is therefore true as
  written, and no test of suppression is needed.
- `LPR-R2-005` (accepted): the library predicate ships and is tested in CP4
  with the command wiring, so CP4 passes its own test list (the earlier CP3/CP4
  split no longer exists).
- `LPR-R2-006` (accepted): D-GP-Compat's field list names every new field,
  including `acceptance_satisfaction` (the earlier `functional_validation`
  record was merged into the acceptance gate).
- `LPR-R2-007` (accepted): D-GP-Policy and D-GP-Compat state `pass`/`warn`/`fail`
  as advisory only; CP1 and CP6 fixtures cover no file, an unadopted file and an
  invalid file.
- `LPR-R2-008` (accepted): INV-8 and the CP6 unaware-consumer test are restated
  against obligation 5 (a known enum value that stalls the item).
- `LPR-R2-009` (accepted): "the anchor" replaces "the item's head" in the rows
  and the table.

### Round 3 (local model plan review, revision 3 to 4)

Every finding was validated against the release source: the cited validators
(`workflow_state.py` `TECHNICAL_APPROVAL_COMMIT_FIELDS` at line 14286,
`_forbidden_state_mutation` at 14254, the bundle-generation field sets at 14109
and 14126), `record_external_result` and `_check_result_kind` in
`workflow_protocol.py`, and `docs/ROADMAP.md:650` all read as the review states.

- `LPR-R3-001` (accepted): the cause table gains the ancestor condition and a
  "position relative to the anchor" rule (equal identity, ahead, behind); a
  behind head is recorded, non-current and not actionable; a stale-evidence row
  and the CP3 tests were added.
- `LPR-R3-002` (accepted): D-GP-Compat now carries a durability table. Residue
  (`gate_evidence`, `reopenings`) is admitted by the three field sets; the
  adoption gets its own commit, trailer and validator; `reopen_work_item` no
  longer writes the top-level `active_work_item_id`, so `_forbidden_state_mutation`
  stays unchanged. Tests in CP1, CP2, CP3 and CP5.
- `LPR-R3-003` (accepted, decided once): a PR fact acts under any gate mode
  (`pr_review` is independent of `human_approval`). `OD-W2-9`, D-GP-Evidence, the
  `38d` row, D-GP-Compat (new delta 6), the CP3 test and the CP7 all-human
  lifecycle say so, with a golden case.
- `LPR-R3-004` (raised as an open decision for the user, `OD-W2-17`):
  **decided (b) by the user on 2026-10-03** (section 11, "User decisions"): on by
  default, configurable, with the single-subscription remedies first-class
  (revision 17, `LPR-R16-001` to `LPR-R16-003`). Until then the plan kept
  opt-in and recorded the deviation from `docs/ROADMAP.md:650`; both are gone.
- `LPR-R3-005` (accepted): `/satisfy-gate implementation` is restated as step 0,
  steps 1 to 4 and the implementation branch of step 6 with the added trailer,
  and CP2 confirms `validate_technical_approval_commit` admits the record.
- `LPR-R3-006` (accepted): rows 37 and 38 precede `38d`, stated in D-GP-Rows;
  the CP5 fixture builds them as non-matching and a second fixture shows them
  winning.

### Round 4 (local model plan review, revision 4 to 5)

Every finding was validated against the release source before applying:
`workflow_state.py` `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS` (14109),
`RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS` (14126), `_forbidden_state_mutation`
(14254), `validate_technical_approval_commit` (14350),
`validate_bundle_generation_record_commit` (14394, which calls
`_forbidden_state_mutation` first), `complete_work_item` (12700), the end-to-end
test `TestFunctionalReviewBoundedFixReachesRecordBundleGeneration`
(`workflow_state_test.py:5128`), and the catalogue in `workflow_protocol.py`
(rows 14, 28, 38b `_V1`, 38c two-stage, 39 `ALL_VERSIONS`).

- `LPR-R4-001` (accepted): the STALE write of every staling `/apply-pr-review`
  branch is committed on its own, state-only, before the generation commit
  (D-GP-Reopen, "Durable ordering"); the generation sets are not widened for
  `technical_approval`. CP5 tests both generation-record and technical-approval
  commits for `content_changed` and the bounded fix.
- `LPR-R4-002` (accepted at revision 5 with option (c); **superseded at
  revision 6 by item-scoped staging**, round 5, `LPR-R5-001`): an opt-in
  `admit_foreign_residue` on `_forbidden_state_mutation`, passed only by the two
  commit validators, admits another item's `gate_evidence`, `reopenings`,
  `state_revision`, `last_transition` and the single reopen phase edge. Option (a) was rejected at revision 5 and adopted at revision 6 (round 5); see
  `LPR-R5-001`. The durability table
  gains the "which item's next commit carries it" column. Tests in CP3 and CP5.
- `LPR-R4-003` (accepted): the completion commit has no field contract
  (`accept-milestone.md` step 6); both sentences are restated, and the
  `completion_obligations_accepted` behavior is stated as written.
- `LPR-R4-004` (accepted): the adoption is delta 7 of D-GP-Compat, with a CP1
  test; the "New fields" sentence is corrected.
- `LPR-R4-005` (accepted): D-GP-Gates has a gate-by-version table naming the
  rows scoped to each version; acceptance is automatic at every governing
  version. CP6 tests it.
- `LPR-R4-006` (accepted): the new rows are relabelled `14a`/`14b`, `28a`/`28b`
  and `38e` to `38i` (and `38d`), each after its base row. No `39*` or `15*`/`29*`
  label remains.
- `LPR-R4-007` (accepted): `/apply-pr-review` requires the id; `GATE_POLICY.md`
  says a reopened item is surfaced only by naming it. CP5 tests the refusal.
- `LPR-R4-008` (accepted): the artifacts file's reason now names CP8.

### Round 5 (local model plan review, revision 5 to 6)

Every finding was validated against the release source before applying:
`record_local_implementation_review`/`record_manual_implementation_review` (no
commit of their own), `TECHNICAL_APPROVAL_COMMIT_FIELDS`'s comment
(`workflow_state.py:14286`), `_forbidden_state_mutation` (`:14254`, compares
other items' whole entries), `pin_plan_approval_state_blob` (`:4041`, the
existing hash-object plus `update-index --cacheinfo` staging primitive), and the
catalogue's rows 16 (`workflow_protocol.py:1250`) and 30 (`:1408`).

- `LPR-R5-001` (accepted, reviewer option (a)): the premise holds. A 2.2 item's
  review round leaves `phase` and `implementation_review_stages` uncommitted
  until its technical-approval commit, and the closed set admitted neither; the
  defect already exists in 2.7.0 for two concurrent 2.2 items, and a reopen
  makes it structural. Option (b) is rejected: a `phase` forward edge among the
  review phases moves another item's gate, which item 267 forbids. Option (c) is
  rejected: it leaves refused-after-landing commits as the common case.
  D-GP-Compat now specifies `stage_scoped_state` (item-scoped staging from
  `HEAD`'s state plus only `work_items[Z]`), names the commands that call it,
  states that the validators and `_forbidden_state_mutation` are unchanged and
  `admit_foreign_residue` and the closed set are removed, and states why foreign
  residue stays durable and what happens to an item that never commits again.
  CP1 (helper tests), CP3 and CP5 (both directions, ledger and phase residue)
  are extended.
- `LPR-R5-002` (accepted): the adoption stages top-level-scoped, so other items'
  residue is neither committed nor refused; the validator runs right after the
  commit and on discovery. CP1 tests an adoption with `gate_evidence` and
  ledger residue present.
- `LPR-R5-003` (accepted): `14b`/`28b` are scoped to a `reachable` wrapper with
  an unmet requirement; an unreachable wrapper falls through 15/29 to 16/30
  with the existing cause-specific remedies. CP6 tests each row-30 cause under
  the default policy.

### Round 6 (local model plan review, revision 6 to 7)

Validated against the release source: `verify_plan_approval_commit` and
`open_plan_approval_journal` (`workflow_state.py:2798`, `:3071`) never call
`_forbidden_state_mutation`, which only `validate_technical_approval_commit`
(`:14350`) and `validate_bundle_generation_record_commit` (`:14394`) do; step 6c
writes committed bytes via `materialize_plan_approval_state` (`:4127`) after the
whole-file compare-and-swap (`:4241`).

- `LPR-R6-001` (accepted, reviewer's first option): the plan-approval journal is
  removed from `stage_scoped_state`'s callers and keeps 2.7.0's whole-file pin.
  D-GP-Compat states that the plan-approval commit carries the whole state and
  that a residue owner's later commit is unaffected, the "no scoped commit
  rewrites" sentence is corrected, and the caller list is tied to the
  `_forbidden_state_mutation` rule. CP2's test is replaced by the residue and
  all-human-bytes tests.
- `LPR-R6-002` (accepted): item-scoped staging is delta 8; the "invisible"
  sentence is corrected; CP6 gains a two-concurrent-2.2-items all-human fixture.
- Optional finding (accepted): the Round 4 `LPR-R4-002` bullet is reworded.

### Round 7 (local model plan review, revision 7 to 8)

Validated against the release source: `request-plan-amendment.md` step 3 and
`milestone-implement.md`'s checkpoint and self-review commits carry only a
`Workflow-Work-Item` trailer and no validator runs over them; only
`validate_technical_approval_commit` and `validate_bundle_generation_record_commit`
call `_forbidden_state_mutation`.

- `LPR-R7-001` (accepted): `request-plan-amendment.md` is removed from the caller
  lists, `milestone-implement.md` is limited to step 4's generation-record
  commit, and D-GP-Compat states that unvalidated state commits keep 2.7.0's
  whole-file staging. CP1 gains the all-human bytes test and a grep test that
  derives the caller list from the rule.
- Optional findings (accepted): stale revision line, "beyond the six" wording,
  delta 8's description of state writes, and delta 8's test placement (now CP1,
  re-run by CP7) are corrected. The bundle's `REVIEW_REQUEST.md` is refreshed.

### Round 8 (manual external plan review, revision 8 to 9)

The verdict was `REVISE` (three blocking findings, one important), with the user's
trust-model decision above applied alongside. Every finding was validated against
the plan text and the release source before applying (`payload/scripts/workflow_state.py`'s
`discover_approval_commits`, `validate_technical_approval_commit`,
`_forbidden_state_mutation`, `verify_plan_approval_commit`;
`payload/.claude/commands/review-plan.md`, `record-manual-plan-review.md`, which
carry no `disable-model-invocation`).

- **Blocking 1** (accepted): the premise held; revision 8 let an agent delete an
  unadopted human setting. D-GP-Policy adds the **floor**, a ratchet of every
  setting observed in the file (working tree, `HEAD` and history), recorded in
  the state by `record_gate_policy_floor` in a committing evaluation, so the
  setting survives the file's deletion or edit; only `/adopt-gate-policy` lowers
  it. The residual (a setting never observed durably) is stated, tested and
  documented. Tests in CP1.
- **Blocking 2** (accepted): the premise held; the plan excluded a hand edit of
  `gate_policy_adoption` and no whole-file commit validator rejected it. The
  adopted policy and the floor are now verified against their recording commits
  (`verify_gate_policy_provenance`, the approval records' trailer-plus-digest
  technique; the base is read from `HEAD`, never the working tree); a mismatch
  fails closed to all gates human (`provenance_failed`); the unvalidated
  whole-file commits gain `assert_gate_policy_fields_unchanged_or_tightened`; the
  validated ones already refuse a top-level change. The honest limit (a forged
  trailer) is stated. Tests in CP1.
- **Blocking 3** (accepted in part, by the user's decision): the premise held. The
  trust model above replaces "the orchestrator reports": CI and PR facts come from
  GitHub (D-GP-Trust, a fixed built-in query, or forge provenance, fail closed);
  review verdicts and functional evidence stay trusted from the orchestrator with a
  stated boundary, an audit trail and human approval named the stronger mode; the
  reviewer's suggestion of CI-produced evidence is **not** adopted (the user's
  decision, and not offered as an option). `ci_result` is removed as a kind: CI is
  the forge fact's checks. Tests in CP2 to CP4.
- **Important** (accepted): the premise held; the behind-fact exclusion let a known
  red PR be ignored while a local fix was approved. Automatic acceptance now needs
  a GitHub-sourced fact for the current approved head (`pr_fact_current`, no failing
  checks, no `CHANGES_REQUESTED`, the head descending from the anchor with equal
  identity); a fact for an older head blocks. Reopening is unchanged (a behind
  fact is still not actionable, so no reopen loop). `OD-W2-18` records that this
  makes a pull request a precondition of automatic acceptance. Tests in CP3, CP4
  and CP6.
- **Missing tests** (all added): removal and edits of the policy file and of the
  adopted policy in the working tree and in unvalidated whole-file commits (CP1);
  fabricated manual review, functional and forge inputs (CP2 to CP4); acceptance
  after a bounded fix while the reported PR head is red and behind (CP4).

### Round 9 (local model plan review, revision 9 to 10)

The verdict was `REVISE` (two blocking findings, one important, one optional).
Each premise was validated against the repository before applying:
`.github/repository/merge-settings.json` sets `"squash_merge_commit_message":
"BLANK"` and `delete_branch_on_merge: true` (and `docs/RELEASING.md` says squash
only), so a branch's commits and trailers do not reach `main`;
`discover_approval_commits` is scoped to one item's `base_commit..head`
(`payload/scripts/workflow_state.py:2072-2086`); `record-external-result` carries
no `disable-model-invocation`, so the origin of a `raw` block cannot be verified.

- `LPR-R9-001` (accepted): the premise held. Provenance no longer depends on a
  commit message or on a branch commit surviving. `gate_policy_adoption` verifies
  by self-consistency (digest, confirmation) and a `history` chain against the
  first parent's value; `gate_policy_floor` verifies by monotonicity, with the
  adoption-lowered floor accepted exactly when the same commit changes the
  adoption validly. The trailers remain audit labels, checked when present and
  never required. The history-scan floor's guarantee is restated to what a squash
  leaves: a setting persists once a committing evaluation recorded it in
  `gate_policy_floor`; a setting committed and deleted inside one squashed branch
  with no such evaluation is a stated, tested residual. D-GP-Policy ("What
  survives a squash merge"), INV-6, the durability table, `OD-W2-2`, the risk
  row, and CP1 (the squash case, with the adoption-lowered floor and two
  adoptions folded into one squash) are updated.
- `LPR-R9-002` (accepted, the reviewer's first option, which stays within the
  user's decision (a)): the premise held. An orchestrator's forge fact is
  **tighten-only**: recorded, able to reopen and to block, never able to satisfy
  `pr_fact_current`, `ci_green` or `pr_approved`. Satisfaction reads only the
  Workflow's own fixed query run inside the satisfying transaction, and with `gh`
  unavailable the act refuses and the gate does not pass. `FORGE_FACT_MAX_AGE_SECONDS` and
  `forge_fact_expired` are removed (nothing relies on the freshness of an
  unauthenticated fact). `next-action` stays read-only: the PR requirements are
  *pending the query* until a stored `workflow_gh` fact exists, rows `38f`/`38g`
  read only a `workflow_gh` fact, and `38h`'s act re-queries. INV-9, D-GP-Trust,
  D-GP-Acceptance, D-GP-Invalidation, D-GP-Rows, REQ-12 and the CP3/CP4 tests
  (a self-consistent hand-built block, with `gh` available and unavailable) are
  updated. **Decided by the user on 2026-10-03: keep** (section 11, "User
  decisions"). The earlier decision (a) says a fact is accepted "through the
  protocol ... with the forge provenance" of an orchestrator; it is accepted for
  recording, reopening and blocking only, and only the Workflow's own fixed `gh`
  query satisfies a gate.
- `LPR-R9-003` (accepted): the adoption commit's diff contract is stated once, in
  D-GP-Policy (exactly the two keys `gate_policy_adoption` and
  `gate_policy_floor`); "Adoption with residue" now refers to it. CP1 tests an
  adoption that lowers a recorded floor, and the validator's refusals of the key
  alone or with a third key.
- Optional (accepted): the durability table's first row reads `functional` only.

### Round 10 (local model plan review, revision 10 to 11)

The verdict was `REVISE` (one blocking finding, three important, one optional).
Each premise was validated against the repository: `.github/repository/ruleset-main.json`
sets `strict_required_status_checks_policy: true` (line 30) and `docs/RELEASING.md`
describes the up-to-date rule, so a branch normally updates from `main` before its
squash; the plan text at the cited places did say "newest" in the introduction
and "every" in the floor bullet, and "the latest fact wins, whatever its source"
and "makes the acceptance gate name `pr.review.external`" as quoted.

- `LPR-R10-001` (accepted): the premise held. D-GP-Policy now states the ranges
  once: the adoption is checked at the newest adoption-changing commit (the chain
  carries the rest); the floor at every floor-changing first-parent commit since
  and including that newest adoption-changing commit, or since the root. A valid
  adoption is the reset point, so the re-adoption remedy works, and a later
  tightening cannot hide a loosening. CP1 tests both of the reviewer's cases.
- `LPR-R10-002` (accepted, the reviewer's first option): one slot per source.
  `gate_evidence.pr` holds `workflow_gh` facts and `gate_evidence.pr_reported`
  holds `orchestrator_forge` facts; the cause table and `38d` read an actionable,
  unapplied key from either, while `pr_fact_current`, `ci_green`, `pr_approved`
  and rows `38f`/`38g` read only `gate_evidence.pr`. The `reopened_for` and
  `applied` sets are per item and shared. D-GP-Trust, D-GP-Invalidation, D-GP-Rows
  and the CP3/CP5 tests (red `workflow_gh` then green `orchestrator_forge`) are
  updated.
- `LPR-R10-003` (accepted): D-GP-Trust now says an orchestrator fact makes the
  next evaluation re-query (row `38h`), agreeing with D-GP-Rows and
  D-GP-Acceptance; the CP4 I1 test names a `workflow_gh` fact, and CP6 tests that
  an orchestrator-only fact emits `38h`, not `38f`/`38g`.
- `LPR-R10-004` (accepted): D-GP-Policy states the merge rule once (a floor
  conflict resolves to the field-wise stricter of both sides; a concurrent second
  adoption fails closed and is re-adopted after updating from `main`), `verify`'s
  message names the remedy, and `GATE_POLICY.md` and the operator guide point to
  it. CP1 tests both cases on a constructed repository with an update from `main`
  and a squash.
- Optional (accepted): the stale-evidence table's `APPROVED` row says
  "(a `workflow_gh` fact only)".
- **Decided by the user on 2026-10-03:** the round 9 reading of decision (a)
  (orchestrator facts accepted for reopening and blocking only), kept, and
  `OD-W2-17`, decided (b); both are recorded in section 11, "User decisions".

### Round 11 (local model plan review, revision 11 to 12)

The verdict was `REVISE` (one blocking finding, two important, two optional). Each
premise was validated against the plan text at the cited places: rows `38f`/`38g`
did read only the stored `workflow_gh` fact, `38h` did match only when none was
stored, and the `reopened_for`/`applied` sets were placed inside the `pr` slot in
D-GP-Reopen, the durability table, CP3 Files and D-GP-Compat.

- `LPR-R11-001` (accepted): the premise held (a stall, never a pass). A reported
  fact whose Workflow-assigned `ingest_seq` is greater than the stored
  `workflow_gh` fact's puts requirements 4 to 6 back to *pending the query*, so
  `38h` emits `acceptance.satisfy`, whose act re-queries and stores a fresh
  `workflow_gh` fact (also when it refuses) with a greater `ingest_seq`. Each
  report triggers at most one query; `38f`/`38g` match only while the stored fact
  is at least as new as `pr_reported`. `satisfied_by: pr_review_result` is
  documented as a trigger, never evidence. D-GP-Trust, D-GP-Acceptance, D-GP-Rows
  and the CP6/CP7 tests (including "acceptance attempted while CI is pending")
  agree.
- `LPR-R11-002` (accepted): the shape is pinned once in D-GP-Invalidation:
  `gate_evidence: {functional, pr, pr_reported, pr_keys: {reopened_for, applied,
  ingest_seq}}`; replacing a slot never touches `pr_keys`. D-GP-Reopen, D-GP-Compat
  (New fields, delta 6), the durability table and CP3 Files agree; CP3 tests
  round-trip, preservation across slot replacement and the no-code branch.
- `LPR-R11-003` (accepted): the premise held: a merge commit that brings in an
  adoption would pass as a reset. The reset exemption now applies only to an
  adoption no other parent holds; at such a merge the floor must be no looser than
  the field-wise stricter of both parents' floors. The adoption-conflict
  resolution is stated ("take `main`'s record, then re-adopt"). CP1 case (c) tests
  it.
- Optional (accepted): the header's plan revision and the section 8 residual
  wording (a hand-built self-consistent adoption record) are corrected.
- **Decided by the user on 2026-10-03:** the round 9 reading of decision (a)
  (orchestrator facts accepted for reopening and blocking only), kept, and
  `OD-W2-17`, decided (b); both are recorded in section 11, "User decisions".

### Round 12 (local model plan review, revision 12 to 13)

The verdict was `REVISE` (one blocking finding, three important, two optional).
Each premise was validated against the plan text: the floor range, the history
scan and the reset exemption were each bounded by "the newest commit that changed
`gate_policy_adoption`", `38g` read the stored fact as is for a human gate, the
failed query stored nothing while the text claimed one query per report, and the
new actions had edges only.

- `LPR-R12-001` (accepted): "adoption-introducing commit" is defined once in
  D-GP-Policy (a commit that changes `gate_policy_adoption` and whose new digest no
  other parent holds). It is the single lower bound of the floor range, the file
  history scan and the reset exemption; the adoption chain check stays at the
  newest adoption-changing commit. An update merge is never a reset point. CP1
  case (d) tests the loosening before an adoption-bringing merge, and the history
  scan variant.
- `LPR-R12-002` (accepted): the newer-than rule applies to a human gate too: `38g`
  matches only while the stored `workflow_gh` fact is at least as new as
  `pr_reported`; otherwise a human gate falls through to row 39. A human `38g` names
  `/accept-milestone`, and step 2a stores its fact. CP6 tests it.
- `LPR-R12-003` (accepted, restated rather than a marker): a failed query stores
  nothing; the act's refusal names `forge_unavailable`, `reconcile` classifies it
  `no_progress`, and retrying is the consumer's job. "At most one **successful**
  query per report" replaces the unconditional claim (D-GP-Trust, D-GP-Acceptance,
  CP6, the section 8 row). No durable marker was added, so `gate_evidence` and the
  2.8.0 state contract are unchanged. CP6 tests `gh` unavailable.
- `LPR-R12-004` (accepted): D-GP-Rows gives each new action its `proof` and
  `allowed_results` and states that a `.satisfy` reaching `MILESTONE_COMPLETE` is
  `progress`; CP7 amends the spec's completion passage; CP6 reconciles each
  refusal outcome.
- Optional (accepted): CP1's residue test says "the two top-level keys". A
  re-reported fact with unchanged semantic content gets no second reopening but a
  fresh `ingest_seq` (one query per report).
- **Decided by the user on 2026-10-03:** the round 9 reading of decision (a)
  (orchestrator facts accepted for reopening and blocking only), kept, and
  `OD-W2-17`, decided (b); both are recorded in section 11, "User decisions".

### Round 13 (local model plan review, revision 13 to 14)

The verdict was `REVISE` (one blocking finding, two important, four optional).
Each premise was validated against the plan text and the release source: the
floor's merge bound ignored a non-first parent's adoption, the `.satisfy` actions
had forward edges only (`reconcile` checks `edge_is_legal` first), and the row
rule contradicted `38d` and `38g`.

- `LPR-R13-001` (accepted): at a merge whose new adoption came from a non-first
  parent the floor is bound three-way against the merge base; a field the branch
  did not change takes the incoming value, a field it changed stays no looser
  than the stricter of both parents. CP1 case (c2).
- `LPR-R13-002` (accepted): each `.satisfy` action gets an `_unchanged` edge at
  its versions; CP7 adds all six edges to the spec.
- `LPR-R13-003` (accepted): D-GP-Rows names `38d` and `38g` as the exceptions;
  D-GP-Compat gains delta 9.
- Optional (accepted): header revision, the `no_progress` retry bound as advice
  plus a CP7 recommendation, CP3/CP4 wording, "19 decisions".

### Round 14 (local model plan review, revision 14 to 15)

The verdict was `REVISE` (no blocking finding, two important, four optional).
Each premise was validated against the release source and the plan text.

- `LPR-R14-001` (accepted, option one: no new `proof`): `reconcile` gives
  `gate_reached` only for a `human_gate` or `external_gate` next decision and
  `_same_phase_proof(None, ...)` is always `False`
  (`payload/scripts/workflow_protocol.py:2059-2072`, `:2169-2174`), and the three
  `.satisfy` actions take `proof: None`; so a refusal ending at `38i`, `38d`,
  `38h`, `14b` or `28b` is `no_progress`, not `gate_reached`. D-GP-Rows states
  each ending's class in the classifier's own terms and the spec's edge table
  (CP7) is the one place that defines them; CP6 asserts the exact class per
  ending plus a consumer simulation (a `38d` ending does not count toward the
  retry bound); CP7's recommendation bounds consecutive `no_progress` of the
  **same** action id at an unchanged `state_identity`. A same-phase proof was
  rejected: it would add a `proof` value to the spec table and the schema, and
  the existing classifier is already correct for a `1.0` consumer (INV-8).
- `LPR-R14-002` (accepted): the mapping's REQ-2 now carries section 9's text
  (stricter side for the fields both changed, the changed side otherwise).
- Optional (accepted): this section's round 13 entry; D-GP-Compat's "nine" and
  which items apply to the default; the criss-cross merge: `git merge-base --all`
  and a fail-closed verdict on more than one base, with CP1 case (c3); the
  request wrapper's round reference.
- **Decided by the user on 2026-10-03:** the round 9 reading of decision (a)
  (orchestrator facts accepted for reopening and blocking only), kept, and
  `OD-W2-17`, decided (b); both are recorded in section 11, "User decisions".

### Round 15 (manual external plan review, revision 15 to 16)

The verdict was `REVISE` (two blocking findings, one important, no optional), with
the user's threat-model decision of 2026-10-03 (section 11, option A) applied
alongside. Every premise was validated against the plan text and, for the
Important finding, the reference Controller (`workflow-controller`,
`controller/forge.py`: `PR_LIST_LIMIT = 200`, a full page refused as
undecidable).

- **Blocking 1, a forged adoption lowers a human gate** (accepted as a statement,
  not a mechanism): the premise holds and is already acknowledged in D-GP-Policy;
  a hand-built, self-consistent adoption is the same bytes as the user's own, and
  no local mechanism can tell them apart. Resolved by the named threat model
  (D-GP-ThreatModel, the user's decision), with the gate-lowering event as the
  safeguard: the lowering is recomputed from history, so a forged adoption is
  reported by `verify`, `next-action` and the audit record. CP1 pins both facts
  with tests (the forgery passes provenance, and is reported). No signed commits
  and no GitHub-side adoption, by the user's decision.
- **Blocking 2, an agent-supplied `gh`** (accepted as a statement plus a
  safeguard): the premise holds (the CP3 tests put a fake `gh` on `PATH`).
  D-GP-Trust now resolves `gh` to an absolute path and refuses
  (`forge_undecidable`) one inside the repository, a worktree, the temp directory
  or a world-writable directory, recording `gh_path` and `gh_sha256`; the CP3
  tests inject the runner and add the refusal cases. A `gh` replaced in a
  directory the user alone controls is outside the threat model.
- **Important, a truncated PR list** (accepted): the argv carries `--limit 200`
  and a full page is `forge_undecidable`, in the query and in `parse_forge_raw`;
  CP3 tests 200 records (a green match with a red one possibly beyond) and 199.
- Round 1 evidence-binding and behind-head findings were confirmed resolved by the
  reviewer; no checkpoint-path classification gap was found.
- **Decided by the user on 2026-10-03:** the round 9 reading of decision (a)
  (orchestrator facts accepted for reopening and blocking only), kept, and
  `OD-W2-17`, decided (b); both are recorded in section 11, "User decisions".

### Round 16 (local model plan review, revision 16 to 17)

Applied from the orchestrator's relay of the two user decisions of 2026-10-03,
recorded in "User decisions".

- `LPR-R16-001` (accepted): the premise held, the text specified opt-in
  everywhere. `DEFAULT_POLICY`, the schema text, `OD-W2-3`, `OD-W2-17`, CP7 and
  the risks table now say on by default, and removing it is a loosening only
  `/adopt-gate-policy` makes. CP1 pins the default, `file_loosening_ignored` for
  `require: []`, and a gate-lowering adoption.
- `LPR-R16-002` (accepted): the `Reviewer model:` line and the `reviewer_model`
  key are written only when the stage's gate is automatic **and** its `require`
  lists the requirement. D-GP-Gates, D-GP-Compat and CP2 say so; CP2/CP6 add the
  all-human golden case.
- `LPR-R16-003` (accepted): the review-request text and `REVIEW_PROTOCOL.md` ask
  for the line; `14b`/`28b` named three remedies (reduced to the two executable ones in round 17); `GATE_POLICY.md` states
  them; CP2 and CP6 test two families, one family, a missing line and an adopted
  `require: []`; D-GP-Compat adds the default's deltas; the CP7 update
  simulation covers the default path and both blockers of an in-flight item.
- `LPR-R16-004` (accepted): section 11 records both decisions, no text calls
  either open, and section 1 lists them as decided.
- `LPR-R16-O1` (accepted): the header says revision 17 and so does the
  metadata line. `LPR-R16-O2`: the `REVIEW_REQUEST.md` is regenerated with this
  revision. `LPR-R16-O3`, `LPR-R16-O4` (accepted): stated in the `GATE_POLICY.md`
  list of CP7.

### Round 17 (local model plan review, revision 17 to 18)

- `LPR-R17-001` (accepted; the premise held: `14b`/`28b` fire only at a
  reachable wrapper, `AWAITING_PLAN_APPROVAL` or
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`, and `/record-manual-*-review` and
  `/review-*` refuse there on their phase guards,
  `payload/scripts/workflow_state.py:15200`, `record-manual-plan-review.md:73-75`).
  Chosen once, in D-GP-Ingest: option (a), the refusal of a manual `APPROVE`
  with a missing or equal family while the stage is open, with the three
  remedies working at that phase; plus option (c)'s honesty for the closed
  stage (the in-flight and later-change cases): `14b`/`28b`, the
  `review_evidence_audited` detail, D-GP-Compat and the CP7 update simulation
  now name only executable remedies, and the withdrawal is stated as what it
  is, with the consumed content. Option (b), a new transition, was not taken:
  it needs an action id, edges and an implementation analogue for a case the
  ingest refusal prevents. No ingest refusal for `review_evidence_audited` is
  added, since an automatic-gate ingest writes the keys by construction. CP2,
  CP6 and CP7 test each remedy end to end.
- `LPR-R17-O1` (accepted): the requested form is `<vendor>/<model>`, in the
  wrapper text and the reviewer commands, with a CP2 golden test.
- `LPR-R17-O2` (accepted): `reviewer_model` is parsed header-only like
  `review_content_id`, tested with a body-quoted line.
- `LPR-R17-O3` (accepted): the `GATE_POLICY.md` remedy sentence says that
  returning a human gate to automatic is a loosening and a gate-lowering event.

### Round 18 (local model plan review, revision 18 to 19)

- `LPR-R18-001` (accepted; the premise held: `assert_local_generation_matches`
  compares `HEAD` for exact equality,
  `payload/scripts/workflow_fingerprint.py:3160-3214`, and is called by both gate
  wrappers, `payload/scripts/workflow_state.py:13089` and `:13165`, and by the
  manual-ingest guards at `:16795`/`:16810`; the adoption and floor commits move
  `HEAD`). Chosen once, in D-GP-Policy ("Bundle generation") and listed in
  section 2: option (c)'s honest restatement for the adoption, plus option (b)'s
  ordering for the floor. The 2.7.0 check is not relaxed (option (a) was not
  taken: it widens a guard that an excluded-only `HEAD` move is meant to fail
  closed, and adds a first-parent-descent validator to two wrappers and two
  ingest guards for a case an ordering removes). `/satisfy-gate` evaluates
  against the virtual floor and records the floor in its own commit **after** its
  satisfying commit, so it can never stale the bundle it needs, and a refused run
  commits nothing. The adoption is no longer offered as an at-phase remedy
  (D-GP-Ingest, `14b`/`28b`, `OD-W2-17`, CP2, CP6, CP7, `GATE_POLICY.md`); it is
  advice for before the bundle is generated, and its confirmation lists the open
  bundles it stales with their way out. The cost is stated: the floor records a
  human setting at the next satisfying run of any gate, not at a run refused
  because that gate is human. CP2, CP6 and CP7 run every remedy against a real
  generated bundle through the real generation check, test the adoption as the
  staling act it is, and test `/satisfy-gate` with a non-empty floor.
- `LPR-R18-O1` (accepted): both commits refuse a non-empty index apart from the
  state path, before committing (`stage_scoped_state` paragraph, CP1).

### Round 19 (local model plan review, revision 19 to 20)

- `LPR-R19-001` (accepted; the three passages named the old remedy set, checked
  at the quoted lines). D-GP-Policy's `require` bullet now states the remedies by
  phase, matching D-GP-Ingest and `14b`/`28b`, and says the adoption is advice
  for before the bundle is generated; D-GP-Compat's delta and CP2's refusal
  assertion name D-GP-Ingest's two remedies, and CP2 asserts the adoption is
  absent from the message. Section 11's historical entries are unchanged.
- `LPR-R19-O1` (accepted as the stated residual, not the classifier change):
  the exact-path fallback would widen the 2.7.0 classifier's fail-closed scope.
  Stated in D-GP-Compat and section 10; CP7's update simulation gains a
  legacy-declared in-flight item.
- `LPR-R19-O2` (accepted): INV-6 now says "has ever recorded".
- `LPR-R19-O3` (accepted): D-GP-Satisfy states the approval stands and the floor
  stays virtual when the post-approval floor commit fails.

### Round 20 (local model plan review, revision 20 to 21)

- `LPR-R20-001` (accepted; D-GP-Gates requirement 3 said "the three of
  D-GP-Rows" while `14b`/`28b` name two). It now names the two and points to
  D-GP-Ingest as the place the set is stated. Sections 1-10 were re-swept for any
  count of remedies; no other passage counts them (the remaining "three" matches
  are the three gates, three-way bounds and three branches).
- `LPR-R20-002` (accepted; checked against the 2.7.0 behavior the review cites:
  the declaration's prefixes are in the hashed projection, and a commit moves
  `HEAD`). The `LPR-R19-O1` residual is restated by phase in D-GP-Compat and
  section 10: before the bundle is generated, exclude the prefix or commit; with
  a bundle open the toggle cannot be used for that item and only the withdrawal
  or regeneration of `14b`/`28b` remains. CP7's legacy-declared case asserts both
  halves through the real generation check. The exact-path
  `TOOLING_AMBIENT_EXCLUDED_PATHS` option stays declined, stated as such. CP2 and
  CP6 assert the unmet `detail` names exactly the two remedies.
- `LPR-R20-O1` (accepted): REVIEW_REQUEST leads with rounds 20, 19 and 18.
  `LPR-R20-O2` (accepted): the CP2 typo. `LPR-R20-O3` (accepted): rounds 16-19 now
  run forward like rounds 1-15.
- Architecture note: the per-phase remedy set is stated once in D-GP-Ingest and
  D-GP-Gates, `14b`/`28b` and CP2/CP6 follow it; a full pointer-only rewrite of
  every restatement is not taken, the sweep above is the check.

### Round 21 (local model plan review, revision 21 to 22)

- `LPR-R21-001` (accepted; verified in `payload/scripts/workflow_fingerprint.py`:
  `_changed_tracked_paths` is `git diff --name-only <base_full>` (`:683-685`) and
  both `assert_all_changed_paths_classified_worktree` (`:1472`) and the
  implementation-stage builder use it, so a committed file stays in the changed
  set). "Or commit the file" is dropped from D-GP-Compat, section 10 and the
  REVIEW_REQUEST; the only before-generation remedy is declaring the prefix or
  the exact path `docs/ai-workflow/GATE_POLICY.json`. The open-bundle bullet
  states the real reason (still changed against `base_commit`, and `HEAD`
  moves). CP7 case (i) asserts a committed file still raises
  `UnclassifiedPathError` in both classifiers and that declaring clears it; case
  (ii) accepts any of the four refusals and pins none. Sections 1-10 were
  re-swept: the other "commit the file" passage (durability of a human setting,
  D-GP-Rows) is about recording the setting, not the classifier, and stands.
- `LPR-R21-O1` (accepted): `OD-W2-17` now says "at ingest, while the stage is
  open" for the second-family remedy.

### Round 22 (manual external plan review, revision 22 to 23)

The verdict was `REVISE` (no blocking finding, three important, one optional).
Each premise was validated against the plan text.

- `LPR-R23-001` (accepted; the cause table's "actionable when" column carried
  only the evidential condition and row `38d` read stored keys). D-GP-Invalidation
  now defines one shared predicate, `pr_key_actionable`, that checks
  `pr_review.enabled`, `reopen_on` and PR `open` state, called by the ingest and by
  `38d`, re-evaluated against the current policy on each pass. `38d`'s row text
  names it, and D-GP-Ingest's test list adds the immediate and deferred cases with
  reopening disabled, a cause omitted from `reopen_on` and a closed unmerged PR.
- `LPR-R23-002` (accepted; the plan defined the lowering event on the newest
  *adoption-introducing* commit while an imported adoption is deliberately not
  one). The recomputation now uses the newest adoption-changing commit, the same
  commit D-GP-Policy already checks the chain at, against its own first parent
  (the branch's pre-import policy). `gate_lowering_event` in CP1 follows it, and
  the in-flight-branch merge tests (c2, d) assert `verify`, `next-action` and a
  later `policy_evidence` all carry the imported lowering.
- `LPR-R23-003` (accepted; CP4 said `/satisfy-gate` "opens with" the floor
  commit, against D-GP-Satisfy "Order of the floor"). CP4 now states the order
  satisfy, then floor commit, with a test pinning that the open bundle still
  verifies at the satisfying step.
- Optional (accepted): the metadata `Plan revision` line now says 23.

### Round 23 (manual external plan review, revision 23 to 24)

The verdict was `REVISE` (one important finding). The premise was validated:
row `38d` was scoped to `AWAITING_FUNCTIONAL_REVIEW` and the plan stated that no
row exists for `MILESTONE_COMPLETE`.

- `LPR-R24-001` (accepted). `38d` now also matches at `MILESTONE_COMPLETE`, before
  the terminal report, on a stored key that is actionable under the current policy
  and not in `applied`; `pr.apply_review`'s first step reopens through
  `reopen_work_item` (the `MILESTONE_COMPLETE` to `AWAITING_FUNCTIONAL_REVIEW`
  edge is added to `reconcile`'s edges for it). The "no row for
  `MILESTONE_COMPLETE`" bullet is replaced, D-GP-Invalidation says the
  re-evaluation holds at completed items, and D-GP-Ingest's test list adds the
  missing case (recorded while disabled, policy enabled, no new fact).

### Round 24 (local model plan review, revision 24 to 25)

The verdict was `REVISE` (two important findings and one optional). Both premises
were validated against `payload/scripts/workflow_protocol.py`: `reconcile` checks
`edge_is_legal` first (`:2139-2141`), and the plan's `pr.apply_review` had only
the `functional.apply_findings` edges plus one `MILESTONE_COMPLETE` edge.

- `LPR-R25-001` (accepted, the second remedy). Started at `MILESTONE_COMPLETE`,
  `pr.apply_review` ends after the reopen (or at a refusal), so it needs exactly
  two edges there: `MILESTONE_COMPLETE` to `AWAITING_FUNCTIONAL_REVIEW` and the
  unchanged `MILESTONE_COMPLETE` edge, every version, listed in D-GP-Rows and
  CP7's edge table. The branches run at `AWAITING_FUNCTIONAL_REVIEW` on the next
  `38d` pass and use the existing edges. CP6 gains the `reconcile` cases for
  every outcome; CP5's bounded-fix test is two invocations.
- `LPR-R25-002` (accepted, the first remedy plus the cross-slot rule).
  `pr.apply_review` at `MILESTONE_COMPLETE` first runs the Workflow's fixed
  `workflow_gh` query and reopens only for an `open` PR whose fresh facts still
  yield the key; `merged` refuses with `pr_merged`, anything else supersedes the
  key (`pr_fact_superseded`, key added to `applied`, which terminates the loop),
  `forge_unavailable` refuses and stores nothing. The predicate's PR state is
  read only from `pr` per `LPR-R28-001`.
  `GATE_POLICY.md` states that enabling a cause never reopens a completed item
  from an old fact alone. Tests added to D-GP-Ingest's list.
- `LPR-R26-001` (accepted, the first remedy). `pr.apply_review`'s step-1 store
  suppresses the ingest-time reopen, so steps 2-3 make the one reopen decision
  and `reopen_work_item` writes the only `reopenings` entry. A red fresh fact
  with a different key K2 ends in `pr_fact_superseded` for K1 (`no_progress`)
  and `38d` acts on K2 on the next pass (stated two-pass behavior). The Optional
  finding is accepted: `forge_undecidable`, `pr_head_unknown` and
  `pr_head_not_in_branch` are named step-1 refusals that store nothing. The
  architecture concern is applied: D-GP-Reopen names the writer's applied and
  suppressed side effects. Tests and CP6 `reconcile` cases added.
- Optional (accepted): the reopen condition reads "the key is not in
  `reopened_for`, or the item is at `MILESTONE_COMPLETE`", `from_phase` covers
  both phases, and the case is tested.
- `LPR-R27-001` (accepted, Important). The predicate's PR state came from the
  newest `ingest_seq` fact across both slots, so an unauthenticated
  `orchestrator_forge` `merged` report newer than a red `workflow_gh` fact could
  make the red key non-actionable and `38d` would skip the fresh Workflow query,
  contradicting tighten-only. The state is now read from the `workflow_gh` fact in
  `pr` when one is stored, and from the newest `orchestrator_forge` fact only when
  none is; an orchestrator report can never suppress a Workflow-observed red key,
  while a `merged` `workflow_gh` fact still retires an older orchestrator key.
  **Superseded in mechanism by `LPR-R28-001` below** (the source-priority rule is
  removed; its test stays as case 2 of the principle's tests).
  The reverse test is added to the completed-item stale-fact cases. The Optional
  metadata finding is accepted: the header and `Plan revision` line both say 27.

### Round 27 (manual external plan review, revision 27 to 28)

The verdict was `REVISE` (one important finding, one missing test). The premise
was validated against the plan text: the round 27 rule read the PR state from the
stored `workflow_gh` fact, so a `workflow_gh` `closed` fact (which
`pr.apply_review`'s fresh query stores for a completed item) hid a newer reported
`open` with a new red key, and neither the ingest nor row `38d` triggered a query,
leaving the item complete.

- `LPR-R28-001` (accepted, **resolving rounds 4 to 6 by one principle instead of
  a fourth patch**). Rounds 4, 5 and 6 each patched which source's PR state wins
  between the `workflow_gh` and `orchestrator_forge` slots, and each patch opened
  the mirror-image gap (round 5: a reported `merged` hid a Workflow-observed red
  key; round 6: a Workflow-observed `closed` hid a newer reported reopen). Any
  rule that reads two sources and picks one has such a gap. The principle follows
  from the user's 2026-10-03 trust decision (`LPR-R9-002`, orchestrator facts are
  tighten-only) and replaces every cross-slot precedence rule:
  (1) an `orchestrator_forge` fact never decides PR state, actionability or
  completion; it is recorded and can only **trigger** the Workflow's own fixed
  query, never suppress one; (2) every decision (actionability, reopen, row `38d`,
  acceptance) is computed from `workflow_gh` facts only; (3) a newer reported fact
  (greater `ingest_seq` than the `pr` slot's, `LPR-R29-001`) whose PR number,
  state, head or keys differ from the `pr` fact (a reported `open` after a `closed`, a reported `merged` or `closed` after an
  open red key) makes the next step a fresh Workflow query before any decision, at
  any phase including `MILESTONE_COMPLETE`, through the existing `pr.apply_review`
  action (row `38d`) or row `38h`; (4) with `gh` unavailable the trigger blocks
  (`forge_unavailable`) and never resolves to nothing to do. Applied in: INV-9,
  D-GP-Trust (item 2, the principle), the trust table, D-GP-Invalidation (one
  predicate reading `pr` only; no cross-slot state rule; the ingest-time reopen
  is limited to `workflow_gh` facts), D-GP-Reopen (the trigger path and the
  recorded result `pr_fact_refreshed`), D-GP-Rows (`38d` cases (a) and (b), the
  `reconcile` edges), the CP3 and CP4 and CP6 tests, the risks and REQ-12 rows. The
  round 5 test (reported `merged` after a Workflow red key), the round 6 test
  (reported `open` after a Workflow `closed`, the missing test the reviewer asked
  for) and the round 4 completed-item test are all cases of the principle
  (CP3's "single principle" test list, cases 1 to 3), with the `gh`-unavailable
  and no-loop cases added. The orchestrator-only key and the no-code-branch note
  for an empty `pr` slot are removed: `pr_keys` holds only Workflow-queried keys.

- `LPR-R29-001` (accepted, Important). Revision 28 keyed the trigger by PR number
  ("newer than the stored `workflow_gh` fact for that PR number, or with none for
  it"). `gate_evidence.pr` holds one fact, and a query that finds no pull request
  stores `state: none`, which has no PR number, so a reported fact naming PR Y
  followed by a query that stored PR X or `state: none` left "no `workflow_gh`
  fact for Y" true: the trigger held again, `38d` re-matched, and every pass
  carried a new `state_identity`, so the retry bound never counted it. Validated
  against D-GP-Trust principle 3, D-GP-Rows `38d` case (b) and D-GP-Acceptance's
  "Pending the query" (which already compared slot `ingest_seq`s, so the plan held
  two definitions of "newer"). Fixed as the reviewer's first remedy: one
  definition, `pr_query_trigger`, on the slots as wholes (`pr_reported.ingest_seq`
  greater than `pr.ingest_seq` or `pr` empty, and the facts differing in PR number,
  state, head, decision, reviewed head, checks or keys), stated in D-GP-Trust and
  referenced by D-GP-Invalidation, D-GP-Acceptance, `38d` and the CP3 module note.
  Any successful query clears it. The `queried_commit`-at-ingest alternative is
  not adopted: it would add a refusal and leave the two definitions in place. The
  Optional finding is applied too: the `pr_review.enabled` condition is now in the
  principle. The reviewer's missing test is added to CP3 (the reported-PR-Y case
  with a `state: none` and a PR X answer, at both phases).
- `LPR-R30-001` (accepted, Important). Row `38d` matched a stored actionable key
  or the trigger, but the fresh-query path was specified only for a trigger
  without a stored key, so at `AWAITING_FUNCTIONAL_REVIEW` a stored open red key
  plus a newer report of `merged`/`closed` took path (a): `reopen_work_item`
  from the stale key with no query, and an unavailable `gh` never blocked.
  Validated against D-GP-Rows `38d`, D-GP-Reopen's query-trigger path and
  `pr_review.enabled` principle 4: the finding is right. Fixed: the trigger takes
  precedence over a stored key at both phases, stated in D-GP-Reopen (both the
  matching paragraph and the trigger path), in `38d`, and in a new CP3 test
  case 7. The Optional finding is applied: the plan metadata names the revision.
- `LPR-R31-001` (accepted, Important). The trigger-path paragraph said a fresh
  `closed` answer ends in the recorded result `pr_fact_refreshed` with nothing
  added to `applied`, while step 2 and CP3 case 7 said `pr_fact_superseded` with
  the key added; step 2 did not say which key. Validated against D-GP-Reopen
  steps 1-3, the trigger-path paragraph and `LPR-R25-002` (a refusal that adds the
  key to `applied` is what terminates the loop at the same red head): the finding
  is right, and the two readings differ in whether a PR reopened at the same red
  head can reopen the item again. Fixed with the reviewer's recommended rule,
  stated once as a table in D-GP-Reopen step 2: S, the stored actionable unapplied
  key read before the query, is added to `applied` by `pr_fact_superseded`
  (`closed`, or an open fact yielding no key), `pr_merged` adds nothing, and
  `pr_fact_refreshed` applies only when no S existed. The trigger-path paragraph
  now points to that table; CP3 case 2 asserts the result code and S's `applied`
  membership at both phases, and case 7 asserts only the ordering and defers its
  results to case 2 (the overlap is removed, not duplicated). The Optional
  finding is applied: the refusal sentences now say the phase is the starting
  phase, and that at `AWAITING_FUNCTIONAL_REVIEW` the action continues into the
  cause-table branches (`LPR-R31-optional`).

### Round 31 (manual external plan review, revision 31 to 32)

The verdict was `REVISE` (one important finding, one missing test). The premise
was validated against D-GP-Reopen step 2 and the `38d` definition: step 1 stores
the fresh fact in `pr`, and `38d` case (a) reads only the stored `workflow_gh`
fact, so after a `closed` or green answer `38d` no longer matches whether or not S
is in `applied`. Adding S to `applied` therefore did no loop-terminating work, and
it permanently consumed a key that no fix handled: a PR closed and later reopened
red at the same head (same key S) could never reopen the item.

- `LPR-R32-001` (accepted, Important, and the missing test). `pr_fact_superseded`
  now adds **nothing** to `applied` (the `LPR-R31-001` table keeps its result
  codes and its S, which is still read once before the query to choose between
  `pr_fact_superseded` and `pr_fact_refreshed`; `LPR-R25-002`'s "key added to
  `applied`, which terminates the loop" is superseded in mechanism). Only
  `/apply-pr-review`'s fix branches add to `applied`. Applied in D-GP-Reopen
  step 2 (the table row and the paragraph after it), the trigger-path paragraph,
  D-GP-Rows' `38d` stop condition, and CP3: the `closed`/green assertions say S is
  **not** in `applied`, and case 2 replaces the same-red-head non-reopening
  assertion with a reopened-red-at-the-same-head case that must reach remediation
  by a Workflow query alone and by an orchestrator report followed by a Workflow
  query, plus the control that an `applied` S is not reopened.

### Round 32 (local model plan review, revision 32 to 33)

The verdict was `REVISE` (one important finding, one non-substantive finding, one
optional).

- `LPR-R33-001` (accepted, Important). CP3 case 2's route (i), "a Workflow query
  alone", has no invocation path at `MILESTONE_COMPLETE`. Validated against
  D-GP-Reopen ("nothing queries the forge after completion"), D-GP-Acceptance
  (`acceptance.satisfy` is reached only at `38h`, before acceptance) and `38d`
  (case (a) reads the stored `closed` fact, which is not actionable; case (b) needs
  a newer report, which is route (ii)): the finding is right. Fixed with the
  reviewer's first remedy, no new post-completion query is designed: route (i) is
  scoped to `AWAITING_FUNCTIONAL_REVIEW` (`38h`'s `acceptance.satisfy`, or
  `/accept-milestone` step 2a), CP3 case 2 asserts it there under automatic and
  human acceptance, and at `MILESTONE_COMPLETE` asserts that only route (ii)
  reaches remediation and that a same-head red reopen with no report leaves the
  item `complete`. D-GP-Reopen's residual paragraph states this second residual
  and `GATE_POLICY.md` names it.
- `LPR-R33-002` (accepted, non-substantive). The review request's change summary
  described `LPR-R31-001`'s superseded rule. It now describes revision 32's
  `LPR-R32-001` change and this revision's, with the earlier entries under
  "Previous".
- Optional (accepted): the `no_progress` list for `pr_fact_superseded` no longer
  implies `38d` re-matches; it names `38d` only for a new-head key.

### Round 33 (local model plan review, revision 33 to 34)

The verdict was `REVISE` (one important finding, two non-substantive findings, one
optional).

- `LPR-R34-001` (accepted, Important). CP3 case 2's human half of route (i) named
  `/accept-milestone` step 2a's query as an invocation path at
  `AWAITING_FUNCTIONAL_REVIEW`. Validated against D-GP-Acceptance's human path
  (step 2a queries only when `requires_pr_approved` is true, default `false`),
  D-GP-Trust 1 (the store reopens only on `acceptance.satisfy`'s path) and
  D-GP-Rows (`38g` needs `pr_approved` required, a human gate has no `38h`): the
  finding is right on both counts. Fixed with the reviewer's first remedy, no new
  human-path query (INV-1): D-GP-Reopen's second residual is now a table of every
  Workflow query path by phase and acceptance mode. Human acceptance with
  `requires_pr_approved: true` reaches `38d` (a) from `AWAITING_FUNCTIONAL_REVIEW`
  for a `CHANGES_REQUESTED` S (step 2a refuses), and from `MILESTONE_COMPLETE` for a
  failed-checks S on an `APPROVED` PR (step 2a passes and the item completes); with
  the default `false`, and at `MILESTONE_COMPLETE`, only route (ii) reaches
  remediation. CP3 case 2 is split by mode and option, with the missing tests the
  review lists.
- `LPR-R34-002` (accepted, non-substantive). After a `closed` answer the stored
  fact fails `pr_fact_current` and is at least as new as `pr_reported`, so the item
  matches `38f` (remedy `/satisfy-gate acceptance`), not `38h` (D-GP-Rows). Route
  (i)'s automatic path now names `38f`, asserts it as the intermediate decision,
  and names `38h` only for a green answer.
- `LPR-R34-003` (accepted, non-substantive). CP7's `GATE_POLICY.md` deliverable now
  lists the second residual with the human-acceptance case, and the CP7 docs check
  requires both residuals.
- Optional and the architecture note (accepted): the metadata `Plan revision` line
  says 34, and the per-phase, per-mode query table the reviewer proposed is in
  D-GP-Reopen, cited by CP3 case 2 and CP7.
