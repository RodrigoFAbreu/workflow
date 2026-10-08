# W3: Workflow 2.9.0 — retire a dormant legacy item, default version 2.2 for new installations, and the v2.6.0-003 fix (Revision 6)

- **Work item:** `legacy-retire-and-default-version` (`process`, governing version `2.2`)
- **Roadmap step:** W3 (`docs/ROADMAP.md`; added by CP6). It goes first, ahead of the update tools, to unblock RepFlow.
- **Branch:** `milestone/legacy-retire-and-default-version`
- **Base commit:** `f00c1c3` (the release source is Workflow 2.8.0, which this repository's own installation also runs, with automatic gates and no `GATE_POLICY.json`)
- **Plan revision:** 6

## 1. Goal

Ship Workflow 2.9.0, a minor release (a new command, so a `feat:` title), with
Orchestration Protocol 1.2 (an additive bump of 1.1). Three parts, approved by
the user on 2026-10-04:

1. **`/retire-legacy-work-item <id>`.** A new user-only command that moves a
   dormant `LEGACY_READY` work item to `MILESTONE_COMPLETE` as already
   finished, without adopting it. The motivating case is RepFlow's
   `milestone-8` (governing `1`, `LEGACY_READY`, a `LEGACY_V1` technical
   approval at an old commit): `promote_legacy_work_item` refuses it with
   `LegacyAdoptionStaleApprovalError` because the product code changed since,
   and 2.8.0 has no retire route.
2. **Default governing version 2.2 for new installations.** The bootstrap
   template's `WORKFLOW_CONFIG.json` changes from default 2.1 to default 2.2,
   so new installations and the work items created in them are 2.2. It matters
   because under the 2.8.0 gate policy a 2.1 item always keeps a human
   technical gate (protocol rows 29 and 33; the automatic technical gate, rows
   28a/28b, exists only at 2.2), so a freshly bootstrapped repository could
   never run its implementation approval automatically. RepFlow's owner agreed
   on 2026-10-04.
3. **Defect `v2.6.0-003`** (Defect Disposition Summary, `docs/ROADMAP.md`;
   protocol rows 6a, 38b and 38c): the narrowest safe fix, D-Fix-003.

### Hard requirements (invariants)

- **INV-1, nothing existing changes meaning.** Existing repositories'
  `WORKFLOW_CONFIG.json` is never rewritten by an update; every work item keeps
  its governing version; no existing command's text changes except where a
  checkpoint of this plan says so. Every `next-action` decision for a state
  that is not `LEGACY_READY`, a retired legacy item with pull-request evidence (revision 5: only its row-38d disposition), a governing-`1` item at `IMPLEMENTING`/the
  functional gate, or a 2.1/2.2 item at the functional gate with an outstanding
  checkpoint (revision 3: only the `reason`/`remedy` text of those rows and the
  added alternatives change; no disposition changes) is byte-identical to 2.8.0's, for every gate-policy configuration.
  The all-human equivalence of 2.8.0 is preserved. **The proof (revision 4,
  `I1`)** is a new `v2.8.0`-anchored comparison, `TestEquivalenceAgainstV280`
  with a `V280` loader that mirrors `V270` (it reads the published 2.8.0
  modules from the immutable tag `v2.8.0` and runs them as a subprocess), over
  the scenario set of D-INV1-Proof, comparing `next-action`, `verify` and
  `describe` byte for byte minus the enumerated exemption list of D-INV1-Proof.
  There is no "2.8.0 golden matrix" to re-run: the existing harness
  (`TestAllHumanEquivalence`, `V270`) is anchored at `v2.7.0`.
- **INV-2, retirement is a human act and never automatic.** `/retire-legacy-work-item`
  carries `disable-model-invocation: true`; the writer itself
  takes the user's own current-turn confirmation and refuses (writing nothing)
  unless it names the work item id and the stage word `retirement`, and the
  retirement commit's message body records that confirmation, which its
  validator checks; the id must appear as an **exact token**, never as a
  substring of a longer id (revision 5, `I3`); `next-action` reports it only as an `alternatives` entry
  whose worker is `user_only`, never as a row's own action and never
  `automatic`; no `EDGES` entry exists for it.
- **INV-6, a retired item stays closed (revision 5, `I1`).** A retired item is
  recognized by a structural, enduring predicate, never by the initial absence of
  gate evidence: `is_retired_legacy_item(work_item)` is true exactly when the phase
  is `MILESTONE_COMPLETE`, `governing_workflow_version` is `"1"` and
  `technical_approval.basis` is `LEGACY_V1`. (A promotion sets the version to
  `2.1`, so an item promoted and then accepted never matches; no 2.8.0 writer
  produces the combination otherwise. CP2 proves both.) Later pull-request
  evidence may still be *recorded* on it (`record_pr_fact` is tighten-only and
  harmless), but no model-invocable path reopens it: `reopen_work_item` and
  `begin_pr_review` refuse it with `reopen_retired_legacy_item`, and row 38d never
  matches it, so no decision for it is `automatic`. The one limit is an older
  release, D-Downgrade.
- **INV-3, retirement does not adopt.** It never runs the stale-approval check,
  the branch-reconciliation check or any promotion step, and never touches the
  `technical_approval` record (basis `LEGACY_V1`), the governing version, the
  plan, the registry or `active_work_item_id` (it refuses when the item is
  active).
- **INV-4, every new state write is auditable and downgrade-safe.** Retirement
  writes only fields that exist in 2.8.0's state schema, and its audit is its
  own commit with a dedicated trailer. A state written by 2.9.0 is a state
  2.8.0 and earlier read as legal (D-Downgrade).
- **INV-5, the v1-inert command texts stay inert.** No `1`-branch step of
  `/milestone-plan`, `/milestone-implement` or `/apply-plan-review` changes, so
  the base-commit equality tests of `workflow_integration_test.py`
  (`TestGoldenV1BehaviorAgainstPreV21BaseCommit`) stay green unedited.

### Non-goals

- Changing `default_config()` (D-Default-Version explains why; `OD-W3-2`).
- Rewriting any existing repository's configuration, or moving any existing
  item to another governing version.
- A `1`-branch change to `/milestone-plan` (`PLANNING`/`AMENDING_PLAN` at
  governing `1`, `OD-W3-7`).
- Editing this repository's installation (`scripts/`, `.claude/`,
  `docs/ai-workflow/`'s managed files, the managed blocks); it stays Workflow
  2.8.0 and `workflow-manager verify .` stays clean.
- Publishing, pushing, pinning in `workflow-manager`, or changing the
  Controller.

## 2. What exists today (facts this plan relies on)

- `promote_legacy_work_item` (`payload/scripts/workflow_state.py`, "WF-M8b"):
  from `LEGACY_READY` only; re-verifies branch reconciliation and the legacy
  approval's freshness (`any_protected_path_changed_since`), raising
  `LegacyAdoptionStaleApprovalError`; on success sets the version `"1"` to
  `"2.1"` and `AWAITING_FUNCTIONAL_REVIEW`. `import_legacy_work_item` creates
  the dormant entry, governing `1`, with a `LEGACY_V1` `technical_approval`.
  `LEGACY_READY` is a non-terminal phase; only `MILESTONE_COMPLETE` is terminal.
- `complete_work_item` is the only writer of `MILESTONE_COMPLETE`. It checks
  incomplete children, the own registry's checkpoints and the completion
  obligations. A dormant legacy item has none of the evidence those need, which
  is why retirement is its own writer and not a call to it.
- `validate_user_confirmation(text, work_item_id=, stage=)` accepts only the
  stages in `APPROVAL_STAGES` (`plan`, `implementation`, `acceptance`), a plain
  substring test, and `UserConfirmationRejectedError` otherwise. `APPROVAL_STAGES`
  also types the approval records, so it is not extended (D-Retire-Confirmation).
- The user-only guard, as `/accept-milestone` uses it: frontmatter
  `disable-model-invocation: true` and `state_writer: true`; the id is resolved
  from `$ARGUMENTS` and never from the confirmation text; the commit carries
  `Workflow-Work-Item: <id>` as the message's last paragraph, after any
  `Co-Authored-By:` lines (`OPUS-R129-001`).
- Protocol: `ACTIONS` marks `plan.approve`, `implementation.approve` and
  `milestone.accept` `user_only` (role `user`, a command file whose frontmatter
  disables model invocation, checked by `workflow_protocol_test.py`).
  `milestone.accept` appears only as an alternative of row 39. Row 3 is
  `LEGACY_READY`, every governing version, `blocked`, `legacy_item_not_activated`,
  no alternatives. `PROTOCOL_VERSION` is `1.1`, `WORKFLOW_RELEASE` is `2.8.0`.
- The shipped template `templates/docs/ai-workflow/WORKFLOW_CONFIG.json` is
  default 2.1 with the supported list of 1 and 2.1. `default_config()` is a
  different thing: `load_config`'s **pre-activation fail-safe** (a missing or
  corrupt config before any activation event reads as default `1`), whose
  default is `PRE_ACTIVATION_FAILSAFE_VERSION` (`1`).
  `validate_config` requires the default to be in the supported list.
- `v2.6.0-003`: `record_bundle_generation` accepts `implementation` only from
  `SELF_REVIEWING_IMPLEMENTATION`, but the `1` branch of `/milestone-implement`
  step 4 calls it from `IMPLEMENTING` (`IllegalBundleGenerationSourcePhaseError`);
  the `1` branch writes no checkpoint statuses, so a `1` item with a registry
  fails `/accept-milestone` step 2a; `transition_checkpoint_in_progress` and
  `claim_checkpoint` are legal only at `IMPLEMENTING` (a deliberate guard that
  closes the amendment-claim race, `v2.4.0-002`), so nothing completes an
  outstanding checkpoint from `AWAITING_FUNCTIONAL_REVIEW`;
  `IncompleteOwnCheckpointsError`'s one raise site, in `complete_work_item`,
  advises `/milestone-implement`, which cannot start a checkpoint there.

## 3. Design decisions

### D-Retire: the retirement writer

`retire_legacy_work_item(state, work_item_id, now, user_confirmation)`, a pure
mutator run inside `state_transaction` (`import_legacy_work_item` is the
precedent for a legacy writer that takes `user_confirmation`):

- refuses (`UserConfirmationRejectedError`, through
  `validate_user_only_confirmation`) a missing, empty or wrong confirmation,
  one that does not name the id and the word `retirement`, before any other
  check and writing nothing, so the writer itself, not only the command file,
  is the guard (revision 2, `I1`);
- refuses (`LegacyRetirementWrongPhaseError`) unless the item exists and its
  phase is exactly `LEGACY_READY`: an `AWAITING_FUNCTIONAL_REVIEW` item that
  was promoted, a `MILESTONE_COMPLETE` item (already retired or finished) and
  every other phase;
- refuses (`LegacyRetirementActiveItemError`) when `active_work_item_id` is the
  item (a `LEGACY_READY` item is dormant by construction, so this is a
  defensive guard against a hand-edited pointer);
- refuses (`LegacyRetirementUnfinishedChildrenError`) when
  `incomplete_children(state, id)` is non-empty;
- sets `phase` to `MILESTONE_COMPLETE`, `current_checkpoint_id` to `null`,
  bumps `state_revision` and sets `last_transition`. **Nothing else changes**:
  `technical_approval` (basis `LEGACY_V1`), `governing_workflow_version`,
  `checkpoints`, the paths and every other field are left byte-identical; no
  `completion_obligations_accepted` is written;
- never calls `complete_work_item`, `promote_legacy_work_item`,
  `verify_legacy_branch_reconciliation` or `any_protected_path_changed_since`;
- **is deliberately outside the lifecycle-witness mechanism** (revision 6, `R5-I1`):
  it takes no `lifecycle_lock` and runs no `_evaluate_lifecycle` side. The
  amendment-race guard (`v2.4.0-002`) protects routes into a checkpoint claim;
  retirement is not one. A `LEGACY_READY` item is dormant by construction: it has no
  checkpoints, so no claim can exist or be made (`checkpoints` and
  `current_checkpoint_id` are empty/`null`), and a plan amendment is requested only
  from `IMPLEMENTING`/`SELF_REVIEWING_IMPLEMENTATION`, which it is not in. The write
  touches four fields of that one item and none of the witness files, and a sibling's
  open amendment or claim is covered by the unfinished-children refusal
  (`LegacyRetirementUnfinishedChildrenError`). The CP2 test asserts that, with a
  witness `OPEN`/`RESOLVING` for a sibling in another worktree, the writer's outcome
  is exactly the unfinished-children refusal (child present) or success (child
  absent), and that the witness files are byte-identical afterwards.

The command file `payload/.claude/commands/retire-legacy-work-item.md`
(frontmatter `disable-model-invocation: true`, `state_writer: true`):

1. resolve the id from `$ARGUMENTS` only (never from the confirmation text);
   refuse when it is missing or not a `work_items` key;
2. require the user's current-turn confirmation (naming the id and the word
   `retirement`), never fabricated or carried over, and pass it verbatim to the
   writer, which validates it with `validate_user_only_confirmation`;
3. run the writer in `state_transaction`; report the refusal and stop on any
   error, writing nothing;
4. commit alone: stage exactly the state file with
   `stage_scoped_state(repo_root, <id>)` (item-scoped staging). The message
   body records the user's confirmation text verbatim (a line
   `Retirement-Confirmation: <text>`; the plan adds no state field, INV-3 and
   INV-4), then the trailers `Workflow-Legacy-Retirement: <id>` and
   `Workflow-Work-Item: <id>` as the message's last paragraph (after
   `Co-Authored-By:`);
5. print what was retired, that the legacy approval was kept untouched, and
   that nothing was adopted.

`discover_legacy_retirement_commit(repo_root, work_item_id)` and
`validate_legacy_retirement_commit(...)` find the commit by its trailer and
check that it changed only that item's `phase`, `current_checkpoint_id`,
`state_revision` and `last_transition` in `WORKFLOW_STATE.json`, touched no
other path, and that its recorded `Retirement-Confirmation` passes
`validate_user_only_confirmation` for the id (a commit without one, or whose
text does not name the id and `retirement`, is refused). **No `verify` report** (revision 3, `I3`). Revision 2 said the protocol's
`verify` operation would report a `LEGACY_V1` completed item "as informational".
That report has no home: `verify`'s result is a closed shape (the check ids are
an `enum` in `orchestration-protocol-v1.schema.json`, `additionalProperties:
false`, statuses `pass|warn|fail|skip`, and only ids in `ADVISORY_VERIFY_CHECKS`
are outside `healthy`), a new id would be a schema change a `1.1` consumer
validating against its own schema rejects, and a `LEGACY_V1` completed item is
legitimate without a retirement commit (an item completed by `/accept-milestone`
after a promotion keeps its legacy approval). The report is dropped:
`verify`, its schema and `ADVISORY_VERIFY_CHECKS` are untouched, and
`discover_legacy_retirement_commit` is the audit query.

**A retired item is not reopened** (revision 5, `I1`, replacing revision 3's `O2`
argument). Revision 3 argued that a retirement writes no `gate_evidence`, so row 38d
has no match and `reopen_work_item` has no fact. That held only until the first
pull-request evidence arrived: `record_pr_fact` accepts evidence for any item,
`_row_38d` covers `MILESTONE_COMPLETE`, `EDGES` legalizes `MILESTONE_COMPLETE ->
AWAITING_FUNCTIONAL_REVIEW`, and `begin_pr_review`/`reopen_work_item` then reopen it
(`REOPENABLE_PHASES` includes `MILESTONE_COMPLETE`), keeping `LEGACY_V1`; the reviewer
reproduced it in a scratch repository. The guard is now enduring and enforced where
the reopen happens (INV-6):

- `is_retired_legacy_item(work_item)` is defined once, beside `REOPENABLE_PHASES` in
  `workflow_gate_policy.py`, as INV-6 states it;
- `reopen_work_item` and `begin_pr_review` raise `EvidenceRefusedError`
  `reopen_retired_legacy_item` for it, at their phase check, before any query,
  store or write (no state change, no `reopenings` entry);
- `_row_38d` returns no match for it, so `decide` never reports `pr.apply_review`
  for a retired item (the decision is the ordinary completed-item one). It evaluates
  the predicate by a **direct pure call on `ctx.work_item`**, as it already reads
  `gate_evidence_of`, never through `ctx.call` (revision 6, `R5-O1`): so
  `CONDITION_CALLS["38d"]` (`workflow_protocol.py:807`),
  `_CONDITION_FUNCTION_MODULES` (`:817`) and the spec's condition-call table
  (`ORCHESTRATION_PROTOCOL.md:666-668`) are unchanged and the spec-equals-code test
  needs no edit for it;
- `record_pr_fact` is unchanged: recording evidence is harmless once nothing acts
  on it, and refusing it would change an evidence path INV-1 protects.

CP2 tests, with a real `record_pr_fact` of a red pull-request report on a retired
item: the evidence is recorded, `decide` is not `automatic`, `reopen_work_item` and
`begin_pr_review` refuse by code writing nothing, and the state still validates;
`reopen_for_stored_fact` (the store-time route, which reaches `reopen_work_item` and
catches `EvidenceRefusedError`) returns `{"refused": "reopen_retired_legacy_item"}`
with the fact stored and the phase and `reopenings` unchanged (revision 6,
`R5-O2`); and that an item promoted and then accepted (`2.1`, `LEGACY_V1`) is
**not** matched, so its reopening is unchanged. 2.8.0 and earlier have no such
guard (D-Downgrade). The normative surfaces that name row 38d's match set and the
refusal codes change with it, by name, in CP2 (revision 6, `R5-I2`).

**What "unfinished children" means.** `incomplete_children` (the existing
function `complete_work_item` uses): any work item whose `parent_work_item_id`
is the id and whose phase is not `MILESTONE_COMPLETE`.

### D-Retire-Confirmation: the stage word and the exact id token

The words `retirement` (here) and `resumption` (`/resume-implementation`, section
3.3) are validated by a new function with its own closed stage set,
`USER_ONLY_ACTION_STAGES = {"retirement", "resumption"}`:
`validate_user_only_confirmation(text, *, work_item_id, stage)`, raising
`UserConfirmationRejectedError`. **It is stricter than `validate_user_confirmation`
by design** (revision 5, `I3`): the existing function tests `work_item_id not in
text`, so a confirmation naming `milestone-80` authorizes `milestone-8`. The new
validator requires the id as an **exact token** (the id not adjacent to a character
of the id alphabet `[A-Za-z0-9_-]`, `WORK_ITEM_ID_RE`'s class, case-insensitively; a
sentence-ending full stop is allowed) and the stage word likewise as a whole word.
It is used by both writers and by both commit validators (the audit reader), so a
confirmation naming only a prefix-related id is refused everywhere.
`validate_user_confirmation`, `APPROVAL_STAGES` and every approval record validator
are untouched (approval-command semantics unchanged; no approval record is written:
retirement is not an approval). CP2 tests prefix-related ids in both directions
(`milestone-8`/`milestone-80`, `milestone-8`/`milestone-8-b`), by the writer and by
`validate_legacy_retirement_commit`. `OD-W3-3`.

### D-Retire-Protocol: reported as an alternative, protocol 1.2

- New action `legacy.retire` in `ACTIONS` (`user_only` true, role `user`,
  invocation `/retire-legacy-work-item {id}`), absent from `EDGES`
  (`AUTOMATIC_ACTION_IDS` unchanged), so `reconcile` and `record-external-result`
  treat it exactly as they treat `plan.approve`.
- Row 3 stays `blocked` with reason `legacy_item_not_activated`, its text
  extended to name both routes (promote through `/prepare-functional-review`,
  or retire), and carries `alternatives: [legacy.retire]`, the way row 39 carries
  `milestone.accept`. The rendered alternative's worker has `user_only: true`.
  A `1.1` consumer already ignores unknown alternatives (they are action
  objects; an unknown id is `blocked` for it, its obligation 3), so the
  decision stays safe for it. `OD-W3-4`.
- `PROTOCOL_VERSION` becomes `1.2`; the schema's `action.id` enums gain
  `legacy.retire`; the spec's action table gains a row. The test constant
  `NEW_ACTION_IDS` (the 1.0 to 1.1 delta against `v2.7.0`) is **not touched**;
  a separate `NEW_1_2_ACTION_IDS = ("legacy.retire", "implementation.resume")`
  records the 1.1 to 1.2 delta (revision 4, `I1`; CP3 adds the constant with
  `legacy.retire`, CP5 adds `implementation.resume`). `OD-W3-5`.
- Nothing else about row 3 changes, and no row 3 decision is ever `automatic`.

### D-Default-Version: the new default for new installations

- `templates/docs/ai-workflow/WORKFLOW_CONFIG.json` becomes default 2.2 with the
  supported list of 1, 2.1 and 2.2 (`validate_config` requires the default in
  the list), so the template validates and a work item created in a new
  installation is governed by 2.2. The template's digest in
  `manifest.json`'s `templates` section is refreshed.
- **`default_config()` is deliberately not changed** (`OD-W3-2`, a correction of
  the request's wording): it is the pre-activation fail-safe, default `1`, and
  changing it would make every existing repository with a missing or corrupt
  config read as 2.2 instead of `1`, which is exactly the rewrite of existing
  behavior the user ruled out. The new-installation default lives in the
  template, which is what `workflow-manager bootstrap` copies.
- An update never rewrites an existing `WORKFLOW_CONFIG.json` (it is
  repo-local state) and an item keeps its governing version for life. That
  behavior belongs to `workflow-manager`, not to this release source:
  `src/workflow_manager/install.py` (`update`, the `state_templates()` loop)
  writes a state template only when the target file is missing and leaves an
  existing one "untouched". `payload/scripts/` tests cannot run it, so the proof
  is two-part (revision 2, `O1`): the payload tests prove the template
  validates, a work item created from it is 2.2, and `default_config()` is
  unchanged; CP6's scratch repository, bootstrapped from a release built from
  this branch and then `update`d with the pinned Manager and `--release-dir`,
  proves an existing old-template config and an existing 2.1 item survive
  byte-identical, with the Manager's cited behavior as the stated basis.
  One residual, stated beside `OD-W3-6`: a repository that deleted its config
  (reading the `1` fail-safe) gets the new 2.2 template created by `update`
  ("created missing state"), the same class of change as today's 2.1 template;
  INV-1's "never rewritten" means an existing file, not a missing one.
- **Manifest provenance** (`O2`). The template's `manifest.json` entry has the
  derivation "identity: frozen `docs/ai-workflow/WORKFLOW_CONFIG.json` ...",
  and the matching `exclusions` entry carries the frozen upstream's
  `upstream_sha256`. A 2.2-default template is no longer an identity of it, so
  CP1/CP6 rewrite the derivation text (a repository-generic configuration whose
  default is 2.2) and refresh the template's `sha256`/`size`; no release check
  in `tools/release/` or `payload/scripts/` compares the two digests (checked
  at plan time by search for `upstream_sha256`), and CP6's `release_test.py`
  run confirms it. The `exclusions` entry is left as the record of the frozen
  upstream.
- Docs: the `Activating 2.2` section of `IMPLEMENTATION_REVIEW_WORKFLOW.md`
  says a fresh install stays at 2.1; it gets a dated 2.9.0 note. The user
  guide's gate table (`docs/gates.md`) and overview name 2.1 as the default of a
  freshly bootstrapped repository; they are updated. Governing-version lists are
  never quoted as a JSON-like list in `docs/ai-workflow/*.md` (a W1 lesson);
  versions are written one at a time, unquoted.
- A residual to state: a fresh install has no `Workflow-Activation` commit, so
  `ConfigMissingAfterActivationError`'s hard stop is not armed by the template
  alone (a missing config still reads as the `1` fail-safe until an activation
  commit exists). It is today's behavior for any template-installed 2.1
  repository; this milestone does not add an activation commit (`OD-W3-6`).

### D-Fix-003: the narrowest safe fix for `v2.6.0-003`

The principle: **no `1`-branch command text changes** (INV-5) and no existing
phase guard widens for any version except the one the `1` command already
assumes. Three symptoms, three decisions:

**(c) The message.** `IncompleteOwnCheckpointsError`'s text becomes
phase-aware: at `IMPLEMENTING` it keeps "finish it with /milestone-implement";
at `AWAITING_FUNCTIONAL_REVIEW` and `AWAITING_USER_ACCEPTANCE` it says that no
command completes a checkpoint from that phase, names `/resume-implementation`
(2.1/2.2 items, a user-only command, revision 3) and `/apply-functional-review` for a finding.
**The text is also version-aware** (revision 4, `O2`): `complete_work_item` raises
the error for a `1` item too, and a `1` item has no resume route
(`resume_implementation` refuses it), so for governing `1` the message names no
command and states the open residual, as row 38b does (the item cannot be accepted until
its registry is terminal). The message test pins the `1` text: it names neither
`/resume-implementation` nor `/milestone-implement` as a route. It keeps the
substrings the 2.8.0 test pins (`/apply-functional-review`, `bounded`,
`remediation child work item`) and still never names the retired
`/accept-scoped-remediation`. No state is written.

**(a) A `1` item with a state entry.** Revision 2 narrows this to the
implementation entry alone (`OD-W3-8` (b), after `B1`/`B2`):

- *Implementation entry.* `record_bundle_generation` gains one legal source
  phase for one case: stage `implementation` from `IMPLEMENTING` **only when
  the item's governing version is `1`** (`/milestone-implement`'s `1` step 4 is
  documented to call it from there, the command text is unchanged). Every other
  version and stage still refuses exactly as before; the source-phase table
  keeps its entries, and a version-aware check is added beside it. The call
  writes exactly the five fields of the ordinary bundle-generation record
  (`phase`, `reviewed_implementation_head`, `implementation_revision`,
  `state_revision`, `last_transition`), a subset of
  `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS`, so the `Workflow-Bundle-Generation-Record`
  commit validates under `validate_bundle_generation_record_commit` and
  `/approve-review implementation`'s provenance interval passes. It needs no
  `repo_root` and no registry: the signature and the unchanged `1` step-4 call
  are untouched.
- *No checkpoint statuses are written.* The previous revision wrote
  `COMPLETE` statuses in this entry. That would put `checkpoints` and
  `last_completed_checkpoint_id` into the record commit's field diff (the
  validator refuses it) and would make the protocol's `verify` check 5,
  `checkpoint_completions_provable`, fail for the item until
  `MILESTONE_COMPLETE`, because `1` commits carry no `Workflow-Checkpoint`
  trailers. Both are refusals in 2.8.0 and 2.9.0 alike, so the design is
  withdrawn rather than patched with version-specific carve-outs in three
  places.
- *The acceptance half of symptom (a) stays open.* A `1` item **with a
  registry** and non-`COMPLETE` checkpoints still fails `/accept-milestone`
  step 2a. A `1` item without a registry (the usual `1`) passes. The defect is
  recorded as fixed for the `IMPLEMENTING` entry and for `1` items without a
  registry, and open for a `1` item with a registry, and for `PLANNING`/
  `AMENDING_PLAN` at `1`. A follow-up may design a provable `1` checkpoint
  trail.
- *The decision for `(IMPLEMENTING, "1")` in 1.2* (revision 3, `B1`). Row 6a
  (`workflow_protocol.py`, today `("PLANNING", "AMENDING_PLAN", "IMPLEMENTING")`,
  `_V1`, `blocked`, `unconditional`) is the only row that covers a `1` item at
  `IMPLEMENTING`; rows 22-24 and the `implementation.*` actions are two-stage
  only. Narrowing it would leave that pair with no row and make
  `evaluate_catalogue` raise (and `test_every_phase_and_version_reaches_an_unconditional_row`
  fail). So **row 6a keeps its three phases, its `blocked` disposition, its
  `unconditional` flag and its absence from `EDGES`**; only its text changes. At
  `IMPLEMENTING` it reports `v1_state_not_advanced` with the reason "the \"1\"
  `/milestone-implement` runs by hand; the orchestrator does not drive governing
  `1`" and the remedy `/milestone-implement` (the row's `remedy_commands`
  becomes a function of the phase: `("milestone-implement",)` at `IMPLEMENTING`,
  `("none_exists",)` at `PLANNING`/`AMENDING_PLAN`, as row 5 already does).
  Nothing is `automatic` for a `1` item, so there is no new action, no `EDGES`
  entry, and `reconcile`/`record-external-result` have nothing to legalize (they
  validate an edge for a decision's action; a `blocked` decision has none, and
  `1` is human-run). "The registry case" of the earlier text is **removed**:
  with or without a registry a `1` item at `IMPLEMENTING` is the same `blocked`
  row, and both reach review through the (now working) hand-run command. The
  unconditional-coverage test stays green unedited.
- *`PLANNING` and `AMENDING_PLAN` at `1`* stay reported `blocked` with the
  existing `none exists` remedy (the `"1"` branch of `/milestone-plan` writes no
  state). `/milestone-plan`'s `1` branch is pinned byte-for-byte by the
  pre-2.1 base-commit test, and the state is reachable only from a remediation
  child created under a `1` default (rare after D-Default-Version). `OD-W3-7`.
- Row 38b (a `1` item at the functional gate with a non-terminal registry) stays
  `blocked` and its text says that the item cannot be accepted until its
  registry is terminal, and names the open residual instead of promising a
  route.

**(b) An outstanding checkpoint at `AWAITING_FUNCTIONAL_REVIEW`, 2.1/2.2.**
Not "complete it from there" (the race guard of `v2.4.0-002` stays closed and
`/request-plan-amendment` is not widened) but a new, explicit, **user-only** way
back: `/resume-implementation <id>`, with the writer `resume_implementation`.

*The premise, corrected (revision 3, `I1`).* Revisions 1-2 and the 2.7.0 record
named "a legacy promotion or a hand-constructed state" as the origins of this
state. A promotion is not one: `import_legacy_work_item` writes only a
`LEGACY_V1` `technical_approval` and `promote_legacy_work_item` adds no
`plan_approval`, so for a promoted item with a registry
`resolve_own_registry_completion_status` raises `StalePlanApprovalRegistryReadError`
("has no CURRENT plan_approval", via `_assert_registry_covered_by_current_plan_approval`),
which row 38a reports first; row 38c is never reached, and
`/milestone-implement` step 1a would refuse at `IMPLEMENTING` with
`plan_approval_not_current` in any case. Ordinary flow cannot leave
`IMPLEMENTING` with a checkpoint outstanding either. The one origin left is a
**hand-constructed or hand-edited state** that carries a `CURRENT` plan approval
covering its registry. Row 38c's text, CP6's Defect Disposition Summary text and
the roadmap record say so; the 2.7.0 record's "legacy promotion" claim is
recorded as wrong.

*Re-decision of `OD-W3-9` on the corrected premise.* An automatic action that
marks a technical approval `STALE` for a state only a hand edit produces is
hard to justify, so the action is **user-only** (`OD-W3-9` (b)):

- the writer `resume_implementation(repo_root, work_item_id, now, user_confirmation)`
  (public entry: lifecycle check, then `state_transaction` around its pure mutator,
  see the lifecycle bullet below) first validates the confirmation (**the second user-only mechanism, revision 5, `I2`**):
  `validate_user_only_confirmation(..., stage="resumption")`, refusing a missing,
  empty, generic or wrong-item confirmation with `UserConfirmationRejectedError`,
  before any other check and writing nothing, so the writer itself, as well as the
  command file, is the guard; it is legal
  only from `AWAITING_FUNCTIONAL_REVIEW`, for a 2.1 or 2.2 item, and its
  **precondition on the plan approval is explicit**: it calls
  `resolve_own_registry_completion_status`, so it requires a `CURRENT`
  `plan_approval` covering the registry (otherwise `StalePlanApprovalRegistryReadError`
  propagates, as for row 38a) and a non-terminal registry; it refuses every other
  phase, every other version and a terminal registry, writing nothing;
- it writes `phase` `IMPLEMENTING`, `technical_approval.status` `STALE` (the
  marker `mark_technical_approval_stale` writes for the bounded fix; the
  approval's content is untouched and a re-approval follows the normal gate
  because the checkpoint's work changes protected content; **revision 4, `O1`:**
  `mark_technical_approval_stale` raises `InvalidApprovalRecordError` when there is
  no `technical_approval` record, so the writer **refuses**, writing nothing
  (`ResumeWithoutTechnicalApprovalError`), a hand-built functional-gate state with
  none, rather than writing the phase alone: the resume's whole purpose is to
  invalidate a gate that was passed, and a state with no record to stale is not
  one this milestone can vouch for. An already-`STALE` record, the bounded-fix
  branch mid-flight, is accepted **idempotently**: the writer leaves the record as
  it is and writes the phase), bumps
  `state_revision` and sets `last_transition`; `current_checkpoint_id` stays
  `null` and the plan approval is untouched. **It writes nothing else.**
- **Lifecycle witnesses: the resume joins the claim side** (revision 6, `R5-I1`,
  option (a)). `/resume-implementation` is a new route into `IMPLEMENTING`, the
  phase from which a checkpoint is claimed, so it must not bypass the amendment-race
  guard (`v2.4.0-002`) that protects every other such route. Its public entry,
  `resume_implementation`, therefore holds `lifecycle_lock(repo_root, work_item_id)`
  and calls `_enforce_claim_lifecycle` (that is, `_evaluate_lifecycle` with the
  existing `LIFECYCLE_SIDE_CLAIM`, no new side) **before** its `state_transaction`,
  in the same order `claim_checkpoint` uses (`workflow_state.py:5861-5862`); the
  state mutator inside the transaction is the pure check-and-write the bullets above
  describe. The lifecycle check runs after the confirmation check (so a bad
  confirmation still refuses first, writing nothing) and before any state write.
  The refusal classes are the claim side's own, unchanged and unextended:
  `AmendmentInFlightError` (an `OPEN`/`RESOLVING` witness anywhere in the
  repository), `StaleLifecycleStateError` (this worktree's `HEAD` is behind the
  recorded resolution), `LaggingWorktreeAmendmentError` and
  `AmendmentWitnessUnavailableError`. An outstanding checkpoint claim needs no
  separate refusal: the resume starts from `AWAITING_FUNCTIONAL_REVIEW` with
  `current_checkpoint_id` `null`, and a claim held for a *sibling* item is that
  item's own lifecycle. The command file and the docs state this, and
  CP5's test asserts exactly these classes.
- **The command file** `resume-implementation.md` (`disable-model-invocation: true`,
  `state_writer: true`) follows `request-plan-amendment.md`'s user-only text:
  it resolves the id from `$ARGUMENTS` only (never from the confirmation), states
  that Claude must never invoke it on the user's behalf, including as a step of
  another command, and **refuses to write anything unless the user's own
  current-turn message supplies confirmation text naming the exact resolved
  `work_item_id` and the word `resumption`**. It never fabricates, infers or reuses
  a confirmation from a previous turn or from other command output; a missing one is
  asked for, naming the id, and the command stops. It passes the text verbatim to the
  writer, restates the resolved id and the transition (`AWAITING_FUNCTIONAL_REVIEW`
  to `IMPLEMENTING`, approval marked `STALE`) in its report, and its commit records
  the confirmation as a `Resume-Confirmation: <text>` body line, which
  `validate_resume_implementation_commit` checks with the same validator.
- from there `/milestone-implement` runs unchanged: claim, `IN_PROGRESS`,
  `complete_checkpoint`, `SELF_REVIEWING_IMPLEMENTATION`, bundle, both reviews,
  technical approval, functional review.
- **A later round: earlier evidence is already identity-bound** (revision 3,
  `I2`; this replaces revision 2's `O4` design, which cleared
  `implementation_review_stages` and "the implementation-gate entries of
  `gate_evidence`"). `gate_evidence` has exactly the keys `functional`, `pr`,
  `pr_reported` and `pr_keys` (`GATE_EVIDENCE_KEYS`, `workflow_gate_policy.py`);
  none is per gate, `reopenings_errors` requires every `reopenings[].key` to be in
  `gate_evidence.pr_keys.reopened_for`, and `pr_keys.ingest_seq` orders later facts, so
  clearing any of it would corrupt `reopenings` or break the tighten-only ordering.
  It is also unnecessary: the automatic technical gate reads the
  `implementation_review_stages` ledger matched against the **current**
  `review_content_id` and bundle (`evaluate_gate`/`technical_approval_gate_reachable`);
  functional evidence counts only when the identity recomputed at its `head`
  equals the anchor's (`_acceptance_functional`); pull-request facts are classified
  by position against the anchor (`apply_invalidation`). A previous round's
  evidence can therefore never satisfy a gate for new content. **The resume
  writer clears nothing**, neither `gate_evidence` nor
  `implementation_review_stages` (the latter is harmless but redundant and a
  larger write surface than the single `STALE` marker the bounded fix writes).
- the action is `implementation.resume` (`user_only`, role `user`), **absent from
  `EDGES`** like `plan.approve` and `legacy.retire`, reported as an **alternative**
  of row 38c, which stays `blocked` (a `1.1` consumer ignores an unknown
  alternative). `AUTOMATIC_ACTION_IDS` is unchanged. It leaves its own
  state-only commit with the trailer `Workflow-Work-Item: <id>` (no new trailer:
  the transition is fully described by the state diff plus the recorded
  confirmation, validated by `validate_resume_implementation_commit`).
- *Row order* (revision 3, `O1`). Row 37 (`functional.prepare`, automatic) is
  evaluated before row 38c, so at a functional gate with no committed checklist
  evidence an orchestrator first prepares a checklist and only then meets row 38c.
  That is intended and harmless: the checklist evidence is keyed to
  `implementation_revision` (`discover_current_functional_checklist_evidence`),
  so after the resume's next bundle it is stale against the new revision and a new
  checklist is prepared; and INV-1 exempts this state from byte-identity. The
  resume row is not moved ahead of 37. Row 38c's `remedy_commands`/
  `refusing_commands` are rewritten: remedy `resume-implementation`,
  `apply-functional-review`, `review-functional`; refusing `milestone-implement`,
  `request-plan-amendment`, `accept-milestone`.

`OD-W3-9` keeps (a) automatic and (c) widening as rejected alternatives.

### D-Downgrade: what an older release does with what 2.9.0 writes

- **Retirement.** The state is `MILESTONE_COMPLETE` with a `LEGACY_V1` approval,
  every field existing in 2.8.0: 2.8.0 and earlier read it as a terminal item;
  the trailer is an unknown trailer they ignore, and 2.9.0 is never needed to read
  it. **The limit (revision 5, `I1`):** 2.8.0 and earlier have no retirement guard.
  In a repository downgraded to 2.8.0 a later red pull-request report on a retired
  item takes row 38d and `/apply-pr-review` can reopen it to
  `AWAITING_FUNCTIONAL_REVIEW`, keeping `LEGACY_V1`; the state stays valid and
  2.9.0's guard closes it again only for a reopen not yet performed. `TestEquivalenceAgainstV280`
  includes the retired-item-plus-red-PR scenario and records the two sides (2.8.0:
  row 38d; 2.9.0: not automatic) on its exemption list; CP6's installation and
  troubleshooting docs state the limit and the remedy (do not report pull-request
  facts for a retired item on 2.8.0 or earlier, or stay on 2.9.0).
- **Default version.** A 2.2 item in a repository on 2.8.0 is ordinary (2.8.0
  already supports it). A repository updated down never has its config touched.
- **`1` implementation entry.** It writes the phase
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` and the ordinary five fields, all
  of which 2.8.0 accepts, and the commit is an ordinary bundle-generation
  record that 2.8.0's `validate_bundle_generation_record_commit` accepts (the
  field diff is a subset of the ordinary set). No checkpoint statuses are
  written, so `verify` check 5 is unaffected. The one residual: 2.8.0's own
  `record_bundle_generation` still refuses the `IMPLEMENTING` source phase for
  `1`, so a downgraded repository meets `v2.6.0-003` again for a new `1`
  entry; the state already written stays legal.
- **Resume.** `IMPLEMENTING` with a `STALE` technical approval is a state
  2.8.0 and earlier already legalize (the bounded fix writes `STALE`); a 2.1/2.2
  item continues with its own `/milestone-implement`. A `1` item is not touched
  by this writer.
- **Protocol 1.2.** A `1.1` consumer meets the two new alternatives
  (`legacy.retire` on row 3, `implementation.resume` on row 38c) as unknown
  action ids (`blocked` for it, obligation 3) and never runs a `user_only`
  action. Revision 3 makes **no disposition automatic**: rows 3, 38c and 6a stay
  `blocked`, so nothing a `1.1` consumer does changes (revision 2's automatic
  row 38c is withdrawn). The `(IMPLEMENTING, "1")` row 6a changes only its text
  and remedy.
- **Retirement commit, resume commit.** An older release ignores their trailers
  and the `Retirement-Confirmation` body line; it has no check that refuses
  them.
- **Gate-policy default equivalence.** No gate predicate, policy file reader or
  evaluation changes; the all-human and the default configurations behave as in
  2.8.0 (INV-1, re-proved by `TestEquivalenceAgainstV280`, D-INV1-Proof).

### D-INV1-Proof: how INV-1 is proved against 2.8.0 (revision 4, `I1`)

The existing harness is `TestAllHumanEquivalence` with the `V270` loader
(`workflow_protocol_test.py`), which runs the **published 2.7.0 modules** as its
old side and pins the 2.7.0 to 2.8.0 delta (`NEW_ACTION_IDS`, the `("1.0", "1.1")`
version pairs, `TestUnawareConsumer.KNOWN_1_0_ACTIONS`, and the assertion that
`set(NEW_ACTION_IDS) - set(wp.EDGES)` is exactly two ids). Re-running it proves
nothing about 2.9.0 against 2.8.0. Each protocol minor version has anchored its
proof at the immediately preceding release; 1.2 does the same.

- **A `V280` loader and `TestEquivalenceAgainstV280`.** It mirrors `V270`: it reads the **complete dependency closure** of the protocol (revision 5, `O1`) --
  `workflow_fingerprint.py`, `workflow_forge.py`, `workflow_gate_policy.py`,
  `workflow_state.py` and `workflow_protocol.py` (the tagged protocol imports
  `workflow_forge` and `workflow_gate_policy`, and state imports
  `workflow_gate_policy`) -- from
  the tag `v2.8.0` into a scratch directory, runs them as a subprocess, and is
  skipped, like `V270`, when the tag is absent from the checkout. It compares
  `next-action`, `verify` and `describe` byte for byte against the 2.9.0 code over
  the scenario set of `equivalence_scenarios()`, plus the **added scenarios**:
  a `LEGACY_READY` item at every governing version, a governing-`1` item at
  `IMPLEMENTING` with and without a registry, and a retired item with and without a
  red pull-request report (`I1`). Without them the exemptions below
  would be vacuous and nothing would test that the exempt states are the only
  cells that change.
- **The exemption list**, enumerated in the test (a cell not on it must match
  byte for byte, so the list is the only thing that may differ):
  - row 3 (`LEGACY_READY`, every version): `reason`/`remedy` text and
    `alternatives`;
  - row 6a at `IMPLEMENTING` (governing `1`): `reason`/`remedy` text and
    `remedy_commands`;
  - row 38b (`1` at the functional gate with a non-terminal registry): `reason`/
    `remedy` text;
  - row 38d for a retired item with reported pull-request evidence (a `MILESTONE_COMPLETE`
    governing-`1` `LEGACY_V1` item, an added scenario): `disposition`, `action` and
    `reason` may differ (2.8.0 `automatic` `pr.apply_review`, 2.9.0 not automatic) -- the
    one exemption that changes a disposition, because it is the I1 closure;
  - row 38c (2.1/2.2 at the functional gate with an outstanding checkpoint, which
    includes the `functional-incomplete@2.1` and `@2.2` scenarios whenever they
    reach it): `reason`/`remedy` text, `remedy_commands`, `refusing_commands` and
    `alternatives`.
  For every exempt cell except the retired-item row-38d cell the `row`, the
  `disposition`, the `action` and the `reason` code still must match. In `describe`, the delta is exactly the
  protocol version, `NEW_1_2_ACTION_IDS` and the row text changes; `verify` is
  byte-identical in every cell.
- **The `V270` tests are kept**, as the 1.1 history. They stay anchored at
  `v2.7.0` and keep `NEW_ACTION_IDS` (the 1.0 to 1.1 delta) and its
  `set(NEW_ACTION_IDS) - set(wp.EDGES)` assertion untouched. Only the pins the 1.2
  bump changes are widened: where a test compares the current protocol version or
  action list against 2.7.0, `NEW_1_2_ACTION_IDS` is added to the expected set and
  the version pairs naming the current protocol version are re-pointed at 1.2.
  Scenarios that reach an exempt row are compared against 2.7.0 on disposition and
  action only, as they already are where 2.8.0 changed text by design.
- **A 1.1-consumer model**, `KNOWN_1_1_ACTIONS = frozenset(wp.ACTION_IDS) -
  frozenset(NEW_1_2_ACTION_IDS)`, beside `TestUnawareConsumer`: it walks every
  scenario, including the added ones, and shows a 1.1 consumer meets
  `legacy.retire` and `implementation.resume` as unknown actions, treats the
  decision as `blocked` (obligation 3) and never runs either. This tests the
  D-Downgrade protocol claim, which nothing tests today.

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | options | recommendation |
| --- | --- | --- | --- |
| `OD-W3-1` | The release number | (a) 2.9.0, protocol 1.2; (b) 3.0.0 | **(a).** Everything is additive; the title is `feat:` (a minor). |
| `OD-W3-2` | What "the default" means in `default_config()` | (a) change only the template; leave `default_config()` (the pre-activation fail-safe, default `1`); (b) also change `default_config()` | **(a).** `default_config()` is not "2.1"; it is the fail-safe for a missing or corrupt config and reads `1`. Changing it rewrites the behavior of every existing repository without a config. The request named `default_config()`, so this is a **correction of its premise** for the user to confirm; (b) is mechanical if the user still wants it. |
| `OD-W3-3` | How `retirement` is confirmed | (a) a separate stage set and validator; (b) add `retirement` to `APPROVAL_STAGES` | **(a).** `APPROVAL_STAGES` types approval records and the gate code; (b) would admit a `retirement` approval record nowhere meant. |
| `OD-W3-4` | How `next-action` reports it | (a) an alternative of blocked row 3; (b) a new human-gate row 3a replacing row 3's decision | **(a).** Row 3's decision stays `blocked`, so only an added alternative changes; (b) turns a `blocked` decision into a gate for 1.1 consumers. The request's wording ("as an alternative to blocked row 3") is (a). |
| `OD-W3-5` | The protocol version | (a) 1.2; (b) keep 1.1 | **(a).** A new action id is a protocol change; the schema enums and `describe` change. |
| `OD-W3-6` | An activation commit for new installations | (a) none, state the residual; (b) the bootstrap writes `Workflow-Activation: 2.2` | **(a).** The Manager's bootstrap is outside this repository; today's 2.1 template has the same residual. |
| `OD-W3-7` | `PLANNING`/`AMENDING_PLAN` at `1` | (a) leave reported `blocked`, defect stays open for these two; (b) a `1` branch change to `/milestone-plan` | **(a).** (b) breaks the byte-equality test of the `1` branch and serves a state reachable only from a remediation child created under a `1` default. |
| `OD-W3-8` | Statuses for a `1` item's checkpoints | (a) write them in the `1` implementation entry, attested in the commit message; (b) leave them, so a `1` item with a registry still cannot be accepted | **(b)** (revised from (a) after the plan review's `B1`/`B2`). (a) writes fields outside the bundle-generation-record field set, which the record validator refuses, and unprovable `COMPLETE` statuses that fail `verify` check 5, in 2.8.0 and 2.9.0 alike; a sound (a) needs a provable `1` checkpoint trail (a version-aware `verify` and validator, with the attestation recorded where `verify` can read it), a larger change than this milestone. The acceptance half of symptom (a) is recorded as still open, for a `1` item with a registry only. |
| `OD-W3-9` | The way back for an outstanding checkpoint | (a) `/resume-implementation`, automatic, back to `IMPLEMENTING` with a `STALE` approval; (b) the same, user-only, an alternative of blocked row 38c; (c) widen `/request-plan-amendment` or the checkpoint-start guard; (d) withdraw CP5 and keep row 38c `blocked` with corrected text | **(b)** (revised from (a) after the round-2 review's `I1`). The state is reachable only by a hand edit (a promoted legacy item never reaches row 38c: it has no `plan_approval`, so row 38a reports it and the writer refuses), so an automatic action that stales a technical approval surprises the operator; (b) keeps the user-approved scope, reuses every proven edge and writes no new field. (d) is the fallback if the user prefers less surface. (c) reopens the `v2.4.0-002` race the guard closes. |
| `OD-W3-10` | The audit trailer for retirement | (a) `Workflow-Legacy-Retirement: <id>` plus `Workflow-Work-Item`, no state field; (b) also a state field | **(a).** A new state field is refused by 2.8.0's validator (the `OD-W2-13` posture); the commit is the audit. |
| `OD-W3-11` | `verify` and a `LEGACY_V1` completed item with no retirement commit | (a) a new informational `verify` check; (b) no `verify` report, `discover_legacy_retirement_commit` is the audit query | **(b)** (revised from (a) after the round-2 review's `I3`). `verify`'s result is a closed schema (check-id enum, `additionalProperties: false`); a new id is a schema change a `1.1` consumer rejects, and `/accept-milestone` after a promotion legitimately completes such an item. |

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | New installations default to 2.2: template and docs | - | 1 | 1 |
| CP2 | Retire a dormant legacy item: writer, confirmation, commit validation, command | - | 3 | 1 |
| CP3 | Protocol 1.2: legacy.retire action, row 3 alternative, schema, specification | CP2 | 2 | 1 |
| CP4 | v2.6.0-003 (a, implementation entry) and (c): the 1 implementation entry and the phase-aware message | - | 3 | 1 |
| CP5 | v2.6.0-003 (b): user-only /resume-implementation and row 38c alternative | CP4 | 3 | 1 |
| CP6 | Documentation, roadmap and release 2.9.0 | CP1, CP3, CP5 | 2 | 1 |

All paths in the checkpoints are release-source paths (`payload/…`,
`templates/…`, `manifest.json`) unless stated otherwise. The installation
copies under the repository root are never edited. Each checkpoint runs the
payload's nine existing suites in a release-source conformance fixture
(`tools/release/release.py stage-conformance`), and `workflow-manager verify .`
on the checkout. Package builds use the Manager venv
`~/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv`.

<!-- CP1 -->
### CP1 — New installations default to 2.2

**Files:**

- `templates/docs/ai-workflow/WORKFLOW_CONFIG.json`: default 2.2, supported
  1, 2.1 and 2.2.
- `payload/docs/ai-workflow/IMPLEMENTATION_REVIEW_WORKFLOW.md`: the dated 2.9.0
  note in "Activating 2.2".
- `docs/gates.md`, `docs/overview.md`, `docs/glossary.md`, `docs/install.md`
  where they name 2.1 as a fresh repository's default (checked with
  `tools/docs/check_docs.py`).
- `payload/scripts/workflow_state_test.py` and `workflow_integration_test.py`:
  the template validates under `validate_config`, a work item created from it is
  2.2, and `default_config()` is unchanged (default `1`). The update's
  behavior is the Manager's and is proved in CP6 (section 3, D-Default-Version).
- `manifest.json`: the template's digest and derivation text (committed in CP6,
  before the bundle-generation record).

**Verification:** the nine suites green in the staged fixture; `check_docs.py`
clean; a scratch repository bootstrapped from the staged template creates a 2.2
item through `route_work_item`.

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Retire a dormant legacy item

**Files:**

- `payload/scripts/workflow_state.py`: `retire_legacy_work_item` (with
  `user_confirmation`),
  `USER_ONLY_ACTION_STAGES`, `validate_user_only_confirmation`, `is_retired_legacy_item` (in `workflow_gate_policy.py`) and its enforcement in `reopen_work_item`/`begin_pr_review`/`_row_38d`, the
  three refusal classes, `discover_legacy_retirement_commit`,
  `validate_legacy_retirement_commit`, the trailer constant
  `LEGACY_RETIREMENT_TRAILER`; the phase-writer census entry
  (`EXPECTED_WRITERS`) for `MILESTONE_COMPLETE`.
- `payload/scripts/workflow_gate_policy.py`: `is_retired_legacy_item`; `payload/scripts/workflow_protocol.py`
  `_row_38d` returns no match for it (the row-38d disposition difference is on
  CP3's exemption list).
- `payload/.claude/commands/retire-legacy-work-item.md` (new; its commit step uses
  `stage_scoped_state`).
- **The normative surfaces the retired-item guard changes** (revision 6, `R5-I2`;
  INV-1 lets no command's text change unless a checkpoint names it, and this
  checkpoint does), four edits, each naming `reopen_retired_legacy_item` where the
  refusal codes are listed:
  1. `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, row 38d's condition (`:754`):
     the closing "matches a completed item too" gains "except a retired legacy item
     (`is_retired_legacy_item`)", and the action table / row text that names the
     match set agrees; this is the spec a `1.2` consumer reads. No condition-call
     table row changes (the predicate is a direct call, D-Retire, `R5-O1`).
  2. `payload/.claude/commands/apply-pr-review.md`: the step-1 phase sentence (`:37-39`,
     "both phases row `38d` can match at") says a retired legacy item is not matched
     at `MILESTONE_COMPLETE`, and the step-1 refusal list (`:62-66`) gains
     `reopen_retired_legacy_item` with its remedy (none: a retired item is closed by
     design, INV-6; report and stop, and start a new work item for any further work).
     The file's hash is **re-recorded in the roster** (`manifest.json` and the
     roster tests that pin command hashes). `apply-pr-review.md` arrived in 2.8.0,
     after the pre-2.1 base commit, so it is not among the commands whose `1`
     branch `TestGoldenV1BehaviorAgainstPreV21BaseCommit` pins and has no `1`-inert
     span; CP2 runs that test and, if any hash-pinned span were found to contain
     either sentence, drops the edit and keeps the code and the spec row only.
  3. `payload/docs/ai-workflow/GATE_POLICY.md:304`: "`38d` then reopens from
     `MILESTONE_COMPLETE`" gains "(never a retired legacy item)".
  4. `reopen_work_item`'s docstring (`workflow_state.py:19324-19329`): the stable-code
     list gains `reopen_retired_legacy_item` (a `MILESTONE_COMPLETE` item with governing
     version `1` and a `LEGACY_V1` basis; `begin_pr_review` raises it too).
- **Registration tests** (revision 5, `O2`): `workflow_integration_test.py`'s
  operator-reference test (the on-disk command count, now 20, becomes 22 once both
  new commands exist: CP2 raises it to 21 and adds the operator-reference section;
  CP5 to 22) and `workflow_gate_policy_test.py`'s `TestCommandSentences.SCOPED`
  (`retire-legacy-work-item.md` joins the set because it stages through
  `stage_scoped_state`; CP5 adds `resume-implementation.md` for the same reason), with
  `test_the_list_is_derived_from_the_rule` extended so the new commit types
  (`Workflow-Legacy-Retirement`, the resume commit) are covered by the rule it checks,
  not merely listed. The operator reference (`WORKFLOW_V2_1_OPERATOR_REFERENCE.md`)
  gains one section per new command in CP2/CP5 so the section list equals the
  on-disk list.
- `payload/scripts/workflow_state_test.py`: every refusal (each non-
  `LEGACY_READY` phase, active, unfinished child, missing or wrong
  confirmation, unknown id) writes nothing, and the writer itself, called
  directly, refuses a missing, empty or wrong confirmation (`I1`); success
  changes exactly the four
  fields; the `LEGACY_V1` record is byte-identical; the stale-approval case of
  the motivating item (product code changed since the reviewed commit) retires
  where `promote_legacy_work_item` still refuses; commit discovery and
  validation (a commit that changed anything else, or that records no
  confirmation or one not naming the id and `retirement`, is refused); the
  command file's frontmatter; **exact-token confirmation** (`I3`): a confirmation
  naming only `milestone-80` (or `milestone-8-b`) for `milestone-8` is refused by the
  writer and by `validate_legacy_retirement_commit`, while `milestone-8` as a whole
  token (with trailing punctuation) is accepted; `validate_user_confirmation` is
  untouched (its substring behavior is pinned by an unchanged test); **lifecycle
  witnesses** (`O3`, D-Retire, lifecycle bullet).

  A retired item stays closed (`I1`): after a real `record_pr_fact` of a red report, `decide`
  returns no automatic action, `reopen_work_item` and `begin_pr_review` refuse
  (`reopen_retired_legacy_item`) writing nothing, `reopen_for_stored_fact` returns
  `{"refused": "reopen_retired_legacy_item"}` with the fact stored and the phase and
  `reopenings` unchanged (`R5-O2`), and `is_retired_legacy_item` is false
  for an item promoted and then accepted. A text test pins that `apply-pr-review.md`'s
  step-1 refusal list names `reopen_retired_legacy_item` and that row 38d's spec
  condition and `GATE_POLICY.md` carry the retired-item exclusion (`R5-I2`). `verify`, its schema and `ADVISORY_VERIFY_CHECKS` are untouched
  (`I3`): a test asserts `verify` is `healthy` for a repository holding a retired
  item.

**Verification:** CP2 also runs the `v2.8.0` comparison for the retired-item scenarios once CP3 adds the loader (a CP3 verification line); a scratch reproduction of RepFlow's `milestone-8` shape
(governing `1`, `LEGACY_READY`, stale `LEGACY_V1`) is promoted-refused and then
retired by the writer; the resulting state validates; the protocol's `verify`
stays `healthy`; `discover_legacy_retirement_commit` finds the commit.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Protocol 1.2

**Files:**

- `payload/scripts/workflow_protocol.py`: `ACTIONS["legacy.retire"]`
  (`user_only`), `_row_3`'s alternative and text, `PROTOCOL_VERSION` 1.2.
- `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`: the two
  `action.id` enums.
- `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`: the action table row,
  row 3's text, the version statements.
- `payload/scripts/workflow_protocol_test.py`: a
  `LEGACY_READY` item at every governing version yields `blocked` with one
  alternative whose worker is user-only; no decision is ever `automatic`;
  `ACTION_IDS`/`AUTOMATIC_ACTION_IDS` expectations; the spec tables equal the
  code. **INV-1's proof** (revision 4, `I1`, D-INV1-Proof; the loader reads all five modules, revision 5 `O1`): the `V280` loader and
  `TestEquivalenceAgainstV280`, the enumerated exemptions and the added
  `LEGACY_READY` and `(IMPLEMENTING, "1")` scenarios; the new constant
  `NEW_1_2_ACTION_IDS` (CP3 adds `legacy.retire`) and the 1.1 to 1.2 version
  pairs; a **1.1-consumer model**, `KNOWN_1_1_ACTIONS =
  frozenset(wp.ACTION_IDS) - NEW_1_2_ACTION_IDS`, beside `TestUnawareConsumer`,
  showing a 1.1 consumer meets `legacy.retire` as unknown and never runs it.
  The `V270` tests keep their disposition (D-INV1-Proof).

**Verification:** the protocol suite is green; `describe` lists `legacy.retire`
and protocol 1.2; the command's frontmatter equals the action's `user_only`.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — `v2.6.0-003` (a, implementation entry) and (c)

**Files:**

- `payload/scripts/workflow_state.py`: the version-aware source-phase rule in
  `record_bundle_generation`; the phase-aware `IncompleteOwnCheckpointsError`
  message. No checkpoint-status write.
- `payload/scripts/workflow_protocol.py`: row 6a keeps `PLANNING`,
  `AMENDING_PLAN` and `IMPLEMENTING` at `1`, `blocked`, `unconditional`, no
  `EDGES` entry; its text is phase-aware and its `remedy_commands` a function of
  the phase (`milestone-implement` at `IMPLEMENTING`, `none_exists` otherwise);
  row 38b's text (D-Fix-003, `B1`).
- `payload/scripts/workflow_state_test.py`, `workflow_protocol_test.py`: a `1`
  item at `IMPLEMENTING` with and without a registry reaches
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` writing exactly the five ordinary
  fields; a real `Workflow-Bundle-Generation-Record` commit of that write
  validates under `validate_bundle_generation_record_commit` and
  `verify_implementation_provenance_interval` (so `/approve-review
  implementation` passes for a `1` item with a registry); a `1` item without a
  registry then passes `/accept-milestone` step 2a, and a `1` item with a
  non-terminal registry is still refused there (the stated residual); the
  protocol's `verify` stays `healthy` for a `1` item past its implementation
  entry (no `COMPLETE` status, so check 5 passes vacuously); every refusal of
  the 2.8.0 tests for `2.1`/`2.2` and for the other stages stays; the message
  test becomes phase-aware. Protocol (`B1`): `test_every_phase_and_version_reaches_an_unconditional_row`
  stays green unedited; `decide` returns a `blocked` `v1_state_not_advanced`
  decision, no action, for a `1` item at `IMPLEMENTING` with and without a
  registry, naming `/milestone-implement`; and the `reconcile` of a `1` item whose
  state moved from `IMPLEMENTING` to `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`
  after a `blocked` decision is refused as having no action to reconcile
  (nothing legalizes the edge because no automatic action emits it).
- `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`: the rows table for 6a (kept, new text) and 38b.

- `payload/scripts/workflow_protocol_test.py`: the `(IMPLEMENTING, "1")`
  scenarios of D-INV1-Proof (with and without a registry), whose row 6a text and
  remedy are on the exemption list; the `1` text of the message test (`O2`).

**Verification:** the `TestGoldenV1BehaviorAgainstPreV21BaseCommit` equality
tests and the command-file hash roster are green with no command text edited;
`TestEquivalenceAgainstV280` is green with the CP4 exemptions (row 6a at
`IMPLEMENTING`, row 38b) exercised, not vacuous.

<!-- /CP4 -->

<!-- CP5 -->
### CP5 — `v2.6.0-003` (b)

**Files:**

- `payload/scripts/workflow_state.py`: `resume_implementation` (takes and validates
  `user_confirmation` first, then holds `lifecycle_lock` and runs
  `_enforce_claim_lifecycle`, then the transaction; writes `phase`,
  `technical_approval.status`, `state_revision`, `last_transition` only; clears
  nothing), its refusal classes, `validate_resume_implementation_commit`; the
  census entry for `IMPLEMENTING`.
- `payload/scripts/workflow_protocol_test.py`: `implementation.resume` is added to
  `NEW_1_2_ACTION_IDS` (never to `NEW_ACTION_IDS`, so `:4999`'s
  `set(NEW_ACTION_IDS) - set(wp.EDGES)` assertion is untouched); the
  `functional-incomplete@2.1`/`@2.2` scenarios of `V280` reach row 38c and are on
  the exemption list; the 1.1-consumer test covers both new alternatives (`I1`).
- `payload/.claude/commands/resume-implementation.md` (new, **user-only**:
  `disable-model-invocation: true`, `state_writer: true`, **and the current-turn
  confirmation guard naming the resolved id and `resumption`**, with the
  fabrication and previous-turn prohibition, `I2`).
- `payload/scripts/workflow_protocol.py`: `ACTIONS["implementation.resume"]`
  (`user_only`, role `user`, absent from `EDGES`), row 38c stays `blocked` with
  the action as an alternative, its text and `remedy_commands`/`refusing_commands`
  rewritten (origin: a hand-constructed state with a `CURRENT` plan approval).
- `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `orchestration-protocol-v1.schema.json`:
  the action and row 38c.
- Registration (`O2`): the operator-reference command count (22) and section, `TestCommandSentences.SCOPED` (`resume-implementation.md`), as in CP2.
- `payload/.claude/commands/accept-milestone.md` step 2a and
  `apply-functional-review.md`'s remediation sentence: name the new command
  (their hashes are re-recorded in the roster). **Neither file's `1` branch text
  is touched** (revision 4, `O3`): both edits land in the 2.1/2.2 spans (step 2a's
  own-checkpoint advice, reached only for a two-stage item, and the
  functional-review remediation sentence), outside every `1`-inert span, so
  `TestGoldenV1BehaviorAgainstPreV21BaseCommit` (INV-5) stays green unedited. CP5
  runs it; if either edit would fall inside a `1`-inert span the edit is dropped
  and the command is named in the message and row text only.
- Tests: the full lifecycle for 2.1 and 2.2 from a hand-built functional-gate
  state with an outstanding checkpoint (resume, claim, complete, self-review,
  bundle, review, approval, functional review, acceptance); refusals; the
  `STALE` approval cannot satisfy acceptance until re-approved; the command
  file's frontmatter equals the action's `user_only`; `implementation.resume` is
  never automatic. **Confirmation** (`I2`): the writer called directly, and the command's own
  text, refuse with no state change a missing, empty, generic (`yes`, `confirm`),
  wrong-item (including a prefix-related id) and wrong-stage (`retirement`,
  `amendment`) confirmation, each tested **before** any state read changes anything;
  `validate_resume_implementation_commit` refuses a commit recording none or a
  wrong one; the command file's text is pinned to name the exact id, the word
  `resumption`, and the no-fabrication/no-reuse rule. **Technical approval** (`O1`): the writer refuses, writing
  nothing, a functional-gate state with no `technical_approval`, and accepts an
  already-`STALE` one idempotently. **Promoted legacy item** (`I1`): a promoted legacy item with
  a registry at `AWAITING_FUNCTIONAL_REVIEW` is reported by row 38a
  (`plan_content_drifted`), not 38c, and the resume writer refuses it
  (`StalePlanApprovalRegistryReadError`), writing nothing. **Identity binding**
  (`I2`, `O4`): at 2.2, a resume cycle from a state holding
  `implementation_review_stages`, functional evidence and a `reopenings` entry
  leaves `gate_evidence`, `reopenings` and the stages byte-identical and
  `validate_state` clean; the previous round's ledger cannot satisfy rows
  28a/28b, and the previous round's functional evidence cannot satisfy the
  automatic acceptance gate, for the new `review_content_id`. **Row order**
  (`O1`): at a functional gate with no committed checklist, `decide` returns row
  37 before 38c; with the checklist committed it returns 38c with the alternative.

**Lifecycle witnesses** (revision 5, `O3`; decided in revision 6, `R5-I1`):
CP5's unchanged amendment-race tests (`v2.4.0-002`) do not execute either new
writer, so CP2 (retirement) and CP5 (resume) each add linked-worktree tests of
their writer against the lifecycle witnesses, asserting what D-Retire and
D-Fix-003 state. **Resume joins the claim side** (D-Fix-003, lifecycle bullet):
`resume_implementation` holds `lifecycle_lock` and runs `_enforce_claim_lifecycle`
before its `state_transaction`. CP5's tests, from a hand-built functional-gate state,
in a linked worktree set-up like the existing amendment-race tests: with an
`OPEN`/`RESOLVING` witness the writer raises `AmendmentInFlightError`; with the
resolution committed elsewhere and not merged into this `HEAD` it raises
`StaleLifecycleStateError`; a lagging worktree and a torn/unreadable witness raise
`LaggingWorktreeAmendmentError` and `AmendmentWitnessUnavailableError`; each writes
nothing (state bytes and witness unchanged), and a bad confirmation still refuses
first with `UserConfirmationRejectedError`. With no witness, a clean resume then a
`claim_checkpoint` succeeds. **Retirement is unaffected** (D-Retire, lifecycle
bullet): CP2's tests assert the unfinished-children refusal or success and
byte-identical witness files. The command files and the docs state both behaviors.

**Verification:** `workflow_acceptance_matrix_test.py` lifecycle green;
`TestPersistedPhaseWriterCensus` updated deliberately; the amendment-race tests
(`v2.4.0-002`) green and unedited.

<!-- /CP5 -->

<!-- CP6 -->
### CP6 — Documentation, roadmap and release 2.9.0

**Files:**

- `payload/docs/ai-workflow/GATE_POLICY.md`, `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
  `MILESTONE_WORKFLOW.md`, `REVIEW_PROTOCOL.md` where they describe the legacy
  lifecycle or the `v2.6.0-003` states; user docs (`docs/gates.md`,
  `docs/troubleshooting.md`, `docs/install.md`) and the docs checker's command rule;
  the older-release limit of retirement (D-Downgrade, `I1`) is stated in the install
  and troubleshooting guidance, not in the retirement design.
- `docs/ROADMAP.md`: a W3 row, a "Workflow 2.9.0" entry, the Defect Disposition
  Summary row for `v2.6.0-003` (its corrected origin: a hand-constructed state,
  never a legacy promotion; fixed in 2.9.0 except the two `1` planning
  phases), the RepFlow unblock note.
- `docs/ACTIVE_MILESTONE.md`: the milestone narrative kept current.
- `manifest.json`: `workflow_version` 2.9.0; the two new commands; refreshed
  `sha256`/`size` for every changed file and for the template; `counts`;
  rationales naming W3. **Committed before the bundle-generation record.**
- `payload/scripts/workflow_protocol.py`: `WORKFLOW_RELEASE` 2.9.0 (the
  release-constant guard).
- `tools/release/manager-pin.json`: stays at Manager 1.4.0 **only if** the CI
  steps pass against it locally (package build, `package verify`, bootstrap and
  `verify` of a scratch repository with `--release-dir`); otherwise the pin
  moves to a Manager release that knows 2.9.0, in its own `ci:` change, an
  owner dependency named in section 7.
- `payload/scripts/workflow_state_test.py` `EXPECTED_WRITERS`, the acceptance
  matrix's script list and the harness only if a new script is added (none is).

**Verification:** the **complete registration checks** (every payload suite, including the operator-reference count and `TestCommandSentences`, the docs checker, `release_test.py`) and a **working `V280` comparison harness** (not skipped: the `v2.8.0` tag present) are run and reported; `release.py build --commit HEAD` reports 2.9.0 and the guard
accepts `WORKFLOW_RELEASE`; `check-title "feat: Workflow 2.9.0 with legacy
retirement and a 2.2 default" --agree` and `check-pending` report
`2.8.0 -> 2.9.0 (minor)`; every suite green in the staged fixture;
`release_test.py` green; `workflow-manager verify .` clean; a scratch
repository bootstrapped from the built release and then `update`d with the
pinned Manager (`--release-dir`) keeps its old-template config and its 2.1 item
byte-identical (`O1`), and the template's manifest derivation reads as the
2.2-default template (`O2`).

<!-- /CP6 -->

## 6. Tests and verification summary

| what | where | when |
| --- | --- | --- |
| template validates, 2.2 item, `default_config()` unchanged | `workflow_state_test.py`, `workflow_integration_test.py` | CP1 |
| update leaves an existing config and a 2.1 item untouched (Manager behavior) | scratch bootstrap-then-`update` | CP6 |
| retirement writer, refusals, confirmation, commit validation, motivating case | `workflow_state_test.py` | CP2 |
| action, row 3 alternative, user-only, never automatic, schema, spec equals code | `workflow_protocol_test.py` | CP3 |
| `1` implementation entry and its record commit, `verify` healthy, message, row 6a coverage and decision at `(IMPLEMENTING, 1)` | `workflow_state_test.py`, `workflow_protocol_test.py` | CP4 |
| resume writer, user-only alternative of row 38c, promoted-item refusal, identity binding, lifecycles at 2.1 and 2.2 | `workflow_state_test.py`, `workflow_protocol_test.py`, `workflow_acceptance_matrix_test.py` | CP5 |
| retired item stays closed after PR evidence; exact-token confirmation; resume confirmation refusals; writers against lifecycle witnesses | `workflow_state_test.py`, `workflow_protocol_test.py`, `workflow_gate_policy_test.py` | CP2, CP5 |
| golden `1`-branch equality and command hashes | `workflow_integration_test.py` | CP4, CP5 |
| INV-1: `v2.8.0`-anchored `next-action`/`verify`/`describe` byte-equality minus the enumerated exemptions, with `LEGACY_READY` and `(IMPLEMENTING, "1")` scenarios (`V280`, `TestEquivalenceAgainstV280`) | `workflow_protocol_test.py` | CP3, CP4, CP5, CP6 |
| `V270` tests keep their pins; `NEW_1_2_ACTION_IDS` and a 1.1-consumer model | `workflow_protocol_test.py` | CP3, CP5 |
| `resume_implementation` with no and with a `STALE` technical approval; the message for a `1` item | `workflow_state_test.py` | CP4, CP5 |
| package, build guard, conformance fixture, pinned Manager | `release_test.py`, `release.py`, CI | CP6 |
| installation untouched | `workflow-manager verify .` | every checkpoint, acceptance |

## 7. Release and follow-ups (owner actions, after acceptance)

1. Open the pull request titled `feat: Workflow 2.9.0 with legacy retirement and
   a 2.2 default` (impact `minor`, agreeing with 2.8.0 to 2.9.0); merge it when
   `aggregate`, `Conventional Commit title` and `workflow-conformance` are
   green; `Release` publishes `v2.9.0`.
2. Open the `workflow-manager` pull request that pins 2.9.0 (and, if CP6 found
   it necessary, release a Manager that knows it).
3. RepFlow: update to 2.9.0, then `/retire-legacy-work-item milestone-8` with
   the owner's confirmation. Until the Manager pins 2.9.0 nothing reaches RepFlow.
4. This repository: install 2.9.0 later with `workflow-manager update`, in its
   own pull request.

## 8. Risks

| risk | mitigation |
| --- | --- |
| A retired item is reopened by later PR evidence | `is_retired_legacy_item` guard at `reopen_work_item`, `begin_pr_review` and row 38d (INV-6); only an older release lacks it, documented |
| One item's confirmation authorizes another (`milestone-80` for `milestone-8`) | exact-token validator for both new writers and both commit validators |
| An agent retires an item it should not | user-only command, user's own confirmation naming id and `retirement`, `next-action` never automatic, refuses any phase but `LEGACY_READY`, refuses active and unfinished-child items |
| Retirement hides unfinished product work | it is a human decision about an item the human states is finished; the commit trailer is the audit; the legacy approval is kept as evidence of what was reviewed |
| The new default changes existing repositories | nothing rewrites a config or an item's version; the update simulation proves it; `default_config()` is untouched |
| Fresh installs are 2.2 and the human reviewers expect 2.1 | stated in the docs; the gate toggles are unchanged |
| A `1` item with a registry still cannot be accepted | no statuses are written (revision 2); the residual is named in D-Fix-003, the docs and `REQ-4`, and row 38b says so |
| `/resume-implementation` invalidates an approval it should keep | it is user-only (never automatic), needs the user's own current-turn confirmation naming the id and `resumption` (writer and command), writes only the `STALE` marker the bounded fix already writes, from a phase with an outstanding checkpoint (where acceptance is already impossible), and needs a `CURRENT` plan approval |
| The amendment-claim race returns | the checkpoint-start guard and `/request-plan-amendment` are untouched; their tests run unedited |
| A new command is not registered everywhere | CP3, CP5 and CP6 follow the registration list (command file, manifest, schema, spec table, tests, docs checker) |
| Manifest digests are stale at the reviewed head | CP6 commits them before the bundle-generation record |
| The pinned Manager does not know 2.9.0 | CP6 runs the CI steps locally; otherwise the pin moves, as an owner dependency |

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/legacy-retire-and-default-version-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | New installations (the template) and the work items created in them default to governing version 2.2; `default_config()`, existing configs and existing items are untouched (payload tests for the template and `default_config()`, CP6's scratch update for existing files and items) | CP1 |
| REQ-2 | `/retire-legacy-work-item`: user-only, guarded by the user's own confirmation naming the id and `retirement`; validates the confirmation with an exact id token (a prefix-related id never authorizes another item); moves only a `LEGACY_READY` item to `MILESTONE_COMPLETE`, which then stays closed under later pull-request evidence and every model-invocable reopen path (older-release limit documented), keeps its `LEGACY_V1` record, refuses active items and unfinished children, never runs the stale-approval or promotion checks, validates the confirmation in the writer itself, and leaves an auditable commit that records the confirmation and carries `Workflow-Legacy-Retirement` and `Workflow-Work-Item` | CP2 |
| REQ-3 | Protocol 1.2 reports a `LEGACY_READY` item with `legacy.retire` as a user-only alternative of blocked row 3 and never as automatic; every other 2.8.0 decision is unchanged | CP3 |
| REQ-4 | `v2.6.0-003` (a, implementation entry) and (c): a `1` item reaches review from `IMPLEMENTING` through a valid bundle-generation-record commit, keeps `verify` healthy, and a `1` item without a registry can pass acceptance step 2a; the message is phase-aware; the `1` command texts are unedited; **still open**: a `1` item with a registry (acceptance step 2a) and `PLANNING`/`AMENDING_PLAN` at `1`, which stay reported | CP4 |
| REQ-5 | `v2.6.0-003` (b): the user-only `/resume-implementation`, guarded by the user's own current-turn confirmation naming the resolved id and `resumption` (writer and command), returns an item with an outstanding checkpoint, a `CURRENT` plan approval and a 2.1/2.2 version from `AWAITING_FUNCTIONAL_REVIEW` to `IMPLEMENTING`, reported as an alternative of blocked row 38c (never automatic), writing only the phase and the `STALE` marker, with the race guard untouched | CP5 |
| REQ-6 | The downgrade posture and the unchanged all-human equivalence of 2.8.0 are stated and tested; documentation, roadmap and the 2.9.0 package are consistent | CP3, CP5, CP6 |
| REQ-7 | 2.9.0 is releasable: manifest digests, release-constant, conformance, a Manager that knows the release | CP6 |

## 10. Artifact classification

`docs/ai-workflow/registry/legacy-retire-and-default-version-artifacts.json`
comes from the `process` template and is fitted to this plan's footprint.

**Plan stage.** The protected paths are this plan document, the registry and
the mapping (every path this plan itself names is classified, including the plan
file). The template's exclusions apply, plus `manifest.json`,
`docs/RELEASING.md`, `payload/`, `fixtures/`, `templates/` and `tools/` (the
set W1 and W2 added). `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`, the user
docs under `docs/`, `docs/ai-workflow/…`, `.github/…` and the installation's
`scripts/` and `.claude/` are classified by the template. CP1 of the
implementation runs `classify_path` over every path in this document.

**Implementation stage.** Protected: `manifest.json`, `docs/RELEASING.md`, the
user docs `docs/gates.md`, `docs/overview.md`, `docs/glossary.md`,
`docs/install.md` and `docs/troubleshooting.md` (CP1, CP6 edit them), the
prefixes `payload/`, `fixtures/`, `templates/` and `tools/`, the installation
prefixes `.claude/commands/` and `scripts/`, which this plan never edits
(protecting them only makes a stray edit visible to the technical approval),
the declarations file's own path, and the exact path
`.github/workflows/workflow-ci.yml` (declared, though this plan edits no CI
file). `docs/ROADMAP.md` and `docs/ACTIVE_MILESTONE.md` stay excluded as
bookkeeping. The declarations file's implementation-stage rationales name W3
(revision 2, `O3`).

## 11. Review rounds and decisions

### Round 1 (LOCAL_MODEL_PLAN_REVIEW, `REVISE`) and its disposition (revision 2)

| finding | disposition |
| --- | --- |
| `B1` the `1` entry's status write breaks the record commit | **Accepted, verified.** `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS` (`payload/scripts/workflow_state.py:14197`) lacks `checkpoints`/`last_completed_checkpoint_id`, and `validate_bundle_generation_record_commit` refuses a wider diff (`:14532`). `OD-W3-8` switched to (b): no status write, so no registry or `repo_root` is needed. REQ-4, D-Fix-003, D-Downgrade, the risk table and CP4 rewritten; CP4 tests the record commit and the provenance interval. |
| `B2` unprovable `COMPLETE` statuses fail `verify` | **Accepted, verified.** `payload/scripts/workflow_protocol.py:535-558` fails `checkpoint_completions_provable` for any non-terminal item with a `COMPLETE` status and no trailer commit (`prove_checkpoint_completions`, `:459-464`). Resolved by the same switch; CP4 tests `verify` stays healthy. The acceptance half of symptom (a) is recorded as still open. |
| `I1` INV-2 versus a confirmation-less writer | **Accepted.** The writer takes and validates `user_confirmation`; the commit records it; its validator checks it; CP2 tests both. INV-2 and REQ-2 updated. |
| `O1` CP1's update simulation | **Accepted.** CP1 no longer claims it; the proof is the Manager's cited behavior (`install.py:507-517`) plus CP6's scratch bootstrap-then-`update`. The deleted-config residual is stated. |
| `O2` manifest provenance | **Accepted.** CP1/CP6 rewrite the derivation text; a search of `tools/` and `payload/scripts/` finds no check that compares `upstream_sha256` against the template digest (CP6's `release_test.py` run confirms it). |
| `O3` artifacts file disagrees with section 10 | **Accepted.** Section 10 now lists the user docs and installation prefixes; the declarations file's implementation-stage rationales are rewritten for W3 and the CP8 citation is removed (an excluded path at the plan stage, so it does not alter the reviewed content). |
| `O4` resume re-enters a later round | **Accepted.** The resume writer clears `implementation_review_stages` and the implementation-gate `gate_evidence`; CP5's 2.2 lifecycle test proves the automatic technical gate cannot be satisfied by earlier evidence. |

### Round 2 (LOCAL_MODEL_PLAN_REVIEW, `REVISE`) and its disposition (revision 3)

| finding | disposition |
| --- | --- |
| `B1` narrowing row 6a leaves `(IMPLEMENTING, "1")` uncovered | **Accepted, verified.** `Row("6a", ("PLANNING", "AMENDING_PLAN", "IMPLEMENTING"), _V1, "blocked", ..., unconditional=True)` is the only row for that pair; rows 22-24 are two-stage only and `evaluate_catalogue` raises on no match. Resolved by keeping 6a unchanged in shape (`blocked`, `unconditional`, no `EDGES`), with phase-aware text and a `milestone-implement` remedy at `IMPLEMENTING`; "the registry case" is removed; D-Downgrade's protocol bullet and CP4's tests updated. No action is added, so there is no edge to legalize. |
| `I1` `/resume-implementation`'s premise is false | **Accepted, verified.** `import_legacy_work_item` writes no `plan_approval` and `promote_legacy_work_item` adds none; `_assert_registry_covered_by_current_plan_approval` raises `StalePlanApprovalRegistryReadError` without a `CURRENT` one, so row 38a precedes 38c. Origin claim corrected in D-Fix-003, row 38c's text and CP6; `OD-W3-9` re-decided as (b) user-only, an alternative of blocked row 38c; the writer's `plan_approval` precondition stated; the promoted-item test added to CP5. |
| `I2` the `O4` fix clears nonexistent `gate_evidence` entries | **Accepted, verified.** `GATE_EVIDENCE_KEYS` is `functional`, `pr`, `pr_reported`, `pr_keys`; `reopenings_errors` requires `reopenings[].key` in `pr_keys.reopened_for`. `O4` restated as "already identity-bound" (gate reads the ledger against the current `review_content_id`, functional evidence against the anchor, PR facts by position). The resume writer clears nothing, neither `gate_evidence` nor `implementation_review_stages` (redundant). CP5 tests added. |
| `I3` the `verify` report has no home | **Accepted, verified.** The `verify` check ids are a schema `enum`, `additionalProperties: false`. The report is dropped; `discover_legacy_retirement_commit` is the audit query (`OD-W3-11` (b)); CP2 tests `verify` stays `healthy`. |
| `O1` row 37 precedes 38c | **Accepted.** Stated as intended and harmless (checklist evidence is keyed to `implementation_revision`); the row is not moved; the row's remedy/refusing commands rewritten; CP5 tests the order. |
| `O2` retirement and the reopen edge | **Accepted.** A retired item has no `gate_evidence`, so row 38d has no match and `reopen_work_item` has no fact to act on; stated in D-Retire and tested in CP2. |

### Round 3 (LOCAL_MODEL_PLAN_REVIEW, `REVISE`) and its disposition (revision 4)

| finding | disposition |
| --- | --- |
| `I1` INV-1 is proved by a harness anchored at `v2.7.0`; recording `legacy.retire` in `NEW_ACTION_IDS` breaks a test | **Accepted, verified.** `V270_TAG = "v2.7.0"`, `NEW_ACTION_IDS` is the 1.0 to 1.1 delta (`workflow_protocol_test.py:4183-4187`), `:4345` asserts the `describe` delta equals it and `:4999` asserts `set(NEW_ACTION_IDS) - set(wp.EDGES)` is exactly two ids; `KNOWN_1_0_ACTIONS` derives from it (`:5112`); `v2.8.0` is a tag. New D-INV1-Proof: a `V280`-anchored `TestEquivalenceAgainstV280` with an enumerated exemption list, added `LEGACY_READY` and `(IMPLEMENTING, "1")` scenarios, `V270` kept as 1.1 history with only the 1.2-affected pins widened, a separate `NEW_1_2_ACTION_IDS` covering both new actions (CP3 and CP5), and a `KNOWN_1_1_ACTIONS` consumer test. INV-1, D-Retire-Protocol, CP3, CP4, CP5, section 6 and D-Downgrade updated. |
| `O1` resume writer with no `technical_approval` | **Accepted, verified.** `mark_technical_approval_stale` raises `InvalidApprovalRecordError` without a record (`workflow_state.py:13977-13982`). The writer refuses, writing nothing, with `ResumeWithoutTechnicalApprovalError`; an already-`STALE` record is accepted idempotently; both tested in CP5. |
| `O2` the `IncompleteOwnCheckpointsError` text for a `1` item | **Accepted, verified.** `complete_work_item` (`:12648`) is the one raise site and serves every version. The text is version-aware; for `1` it names no route and states the residual; pinned in CP4's message test. |
| `O3` CP5's command-roster scope | **Accepted.** Stated: neither file's `1` branch text is touched, both edits land in 2.1/2.2 spans, `TestGoldenV1BehaviorAgainstPreV21BaseCommit` stays unedited and CP5 runs it; an edit that would fall in a `1`-inert span is dropped. |

### Round 4 (MANUAL_EXTERNAL_PLAN_REVIEW, `REVISE`) and its disposition (revision 5)

| finding | disposition |
| --- | --- |
| `I1` retirement's no-reopen guarantee is false | **Accepted, verified.** `record_pr_fact` (`workflow_state.py:19063`) accepts evidence for any item, `REOPENABLE_PHASES` includes `MILESTONE_COMPLETE` (`workflow_gate_policy.py:1321`), `_row_38d` (`workflow_protocol.py:1742`) matches on stored evidence and `begin_pr_review`/`reopen_work_item` reopen from that phase; revision 3's "no `gate_evidence`" argument held only until the first evidence. New INV-6: an enduring structural predicate `is_retired_legacy_item` (`MILESTONE_COMPLETE`, governing `1`, `LEGACY_V1`; a promoted item has version `2.1`, so it never matches), enforced in `reopen_work_item`, `begin_pr_review` and `_row_38d`; D-Retire, D-Downgrade (the older-release limit moved to install/troubleshooting guidance, CP6), the `V280` exemption list, CP2 tests and the risk table updated. |
| `I2` resume lacks the confirmation guard | **Accepted, verified.** `request-plan-amendment.md` requires literal current-turn confirmation naming the id and a stage word, with no fabrication or reuse; `approve-review.md` documents frontmatter's incomplete exposure assurance. `resume_implementation` takes `user_confirmation` (stage `resumption`), the command file carries the guard text, the commit records it, CP5 tests every refusal before any state change. |
| `I3` substring confirmation matches another item | **Accepted, verified.** `validate_user_confirmation` tests `work_item_id not in text` (`workflow_state.py:13267`). New `validate_user_only_confirmation` with an exact-token rule for both new writers and both commit validators (the audit reader); the existing function and `APPROVAL_STAGES` stay untouched; prefix tests in CP2. |
| `O1` V280 dependency closure | **Accepted, verified.** `workflow_protocol.py:42-44` imports `workflow_forge` and `workflow_gate_policy`; state imports the latter (`:194`). The loader reads all five modules. |
| `O2` registration tests | **Accepted, verified.** `workflow_integration_test.py:6587` pins 20 commands; `TestCommandSentences.SCOPED` (`workflow_gate_policy_test.py:1933`) equals the set naming `stage_scoped_state`. CP2/CP5 update both, with the derivation test extended; CP6 runs the full registration checks. |
| `O3` writers against lifecycle witnesses | **Accepted.** Linked-worktree tests of both writers against OPEN/RESOLVING witnesses, stale resolved state and outstanding claims, with the intended refusal behavior stated (CP5, D-Fix-003's lifecycle bullet; CP2). |

### Round 5 (LOCAL_MODEL_PLAN_REVIEW, `REVISE`) and its disposition (revision 6)

| finding | disposition |
| --- | --- |
| `R5-I1` resume has no lifecycle check, CP5 expects a refusal class | **Accepted, verified.** `_evaluate_lifecycle` runs only under `lifecycle_lock` with the sides `claim`/`amendment`/`resolution`/`advance` (`workflow_state.py:6804-6807`, `:7774`); `_enforce_claim_lifecycle` (`:8068`) is called after `lifecycle_lock` by `claim_checkpoint` (`:5861-5862`), adoption and takeover only, so the resume writer, a new route into `IMPLEMENTING`, had none. Option (a): `resume_implementation` holds `lifecycle_lock` and runs the existing claim side before its transaction, no new side, refusing with the claim side's four classes (D-Fix-003 lifecycle bullet; CP5 test asserts exactly those). Retirement is stated **unaffected** in D-Retire (no checkpoints, claims or amendments on a `LEGACY_READY` item; sibling lifecycles covered by the unfinished-children refusal) with its CP2 test. |
| `R5-I2` no checkpoint updates the normative surfaces | **Accepted, verified.** `ORCHESTRATION_PROTOCOL.md:754` ("matches a completed item too"), `apply-pr-review.md:37-39` and `:62-66`, `GATE_POLICY.md:304` and `reopen_work_item`'s docstring (`workflow_state.py:19324-19329`) all describe row 38d's match set or the refusal codes. CP2 now names the four edits, the roster re-recording of `apply-pr-review.md` and the `1`-inert-span check (the file arrived in 2.8.0, after the pre-2.1 base commit, so no golden span covers it; CP2 runs the golden test), and a text test. |
| `R5-O1` how `_row_38d` evaluates the predicate | **Accepted.** A direct pure call on `ctx.work_item`, not `ctx.call`, so `CONDITION_CALLS["38d"]`, `_CONDITION_FUNCTION_MODULES` and the spec's condition-call table do not change (D-Retire). |
| `R5-O2` pin `reopen_for_stored_fact` | **Accepted.** Added to CP2's retired-item tests: `{"refused": "reopen_retired_legacy_item"}`, fact stored, phase and `reopenings` unchanged. |
| `R5-O3` unresolved "section 3.x" references | **Accepted, verified.** Section 3's subsections are unnumbered `D-*` headings. Every "section 3.n" is replaced by the heading's name. |

### User decisions

- 2026-10-04: the three parts and their order (this first, to unblock RepFlow);
  RepFlow's owner agreed to the 2.2 default.
- Pending: `OD-W3-2` (the `default_config()` correction), `OD-W3-7`, `OD-W3-8`
  (now (b), revised by the round-1 review), `OD-W3-9` (now (b) user-only,
  revised by the round-2 review; (d), withdrawing CP5, is the fallback) and
  `OD-W3-11` (now (b), no `verify` report).
