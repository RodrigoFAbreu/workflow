# W5: Workflow 2.10.0 — new work items stop starting on "2.1", and a faster conformance job (Revision 2)

- **Work item:** `retire-21-for-new-work` (`process`, governing version `2.2`)
- **Roadmap step:** W5, "Retire "2.1" for new work items", in `docs/ROADMAP.md`'s
  "What's next" table. The approval named it row 6; since W6 (Workflow 2.9.2)
  was inserted as row 6, W5 is row 7. This plan makes row 7 the current item.
- **Branch:** `milestone/retire-21-for-new-work`
- **Base commit:** `b854a0b` (main after W6: the release source is Workflow
  2.9.2, and this repository's own installation is 2.9.2 with automatic gates,
  default "2.2" and no `GATE_POLICY.json`)
- **Plan revision:** 2. This is a re-plan. W5 was planned once on `04d155a`
  (2.9.1) and reached a local-model APPROVE at its revision 3, never committed,
  before W6 went first. Its decisions are carried over here where they still
  hold, re-checked against today's code (section 2), and that review's six
  optional findings are adopted (section 11).
- **Precondition met:** RepFlow, the last repository that defaulted to "2.1",
  already runs "2.2" (now on Workflow 2.9.2).

## 1. Goal

Ship Workflow 2.10.0, a minor release (`feat:` title: it changes behavior for
new work only), with three parts:

1. **No new work item is created on governing version "2.1"**, while every
   existing "2.1" item keeps working to completion and nothing already
   governed changes. 2.9.0 made "2.2" the default for new installations, but an
   update never rewrites an existing `WORKFLOW_CONFIG.json`. A repository whose
   configuration still names `default_workflow_version: "2.1"` keeps starting
   new items on "2.1", and on a "2.1" item the technical approval stays with a
   person even under 2.8's automatic gates.
2. **The managed `workflow-conformance.yml` gets cheaper and faster.** A new
   push to a pull request cancels the superseded run of that pull request
   (push and other runs are never cancelled), and the nine suites run in
   parallel inside the one `workflow-conformance` job instead of one after
   another (about 22 minutes down to about 9 to 10).
3. **Two wording fixes W6's functional review deferred (R3-1)**, made
   version-aware.

**The one rule for part 1.** A new work item's governing version comes from
the configuration's `default_workflow_version`, exactly as today. When that
default is "2.1", creating a new work item **refuses before any write**, with a
named error and one next step: change the default to "2.2". The Workflow never
picks a version the configuration does not name, and never rewrites the
configuration itself.

### Hard requirements (invariants)

- **INV-1, refusal, never a move.** No path creates a "2.1" item from the
  configuration, and no path silently creates a "2.2" item while the
  configuration says "2.1". Every refusal happens before the first write of
  the branch that creates the item. For `/milestone-plan` and
  `/apply-functional-review` that is before any write of the command. For
  `/apply-pr-review`, its step 1 (`begin_pr_review`) has already written (a
  stored fact, or the reopen); that write stands, and the refusal writes
  nothing after it (D-Paths).
- **INV-2, existing items untouched.** No persisted field of any existing work
  item changes, and every command that drives an existing "2.1" item (plan
  revision, plan review and approval, implementation, implementation review,
  technical approval, functional review and its in-place fixes, acceptance,
  plan amendment, reopening) behaves as in 2.9.2. Only the creation of a *new*
  item is affected.
- **INV-3, legacy adoption untouched.** `promote_legacy_work_item` still moves
  an adopted item to the literal "2.1" (it is not new work).
- **INV-4, a "2.2" (or "1") default unchanged.** Every path behaves as in
  2.9.2 when the default is not "2.1".
- **INV-5, configuration stays valid.** A configuration that names "2.1" as
  its default still loads and validates (existing items need it), and "2.1"
  stays in `supported_versions`.
- **INV-6, additive protocol.** Orchestration Protocol 1.3 only adds a row, a
  reason code and an advisory `verify` check (D-Protocol).
- **INV-7, one required check, every suite.** The managed workflow keeps
  exactly one job, `workflow-conformance` (a required check in this
  repository's ruleset; its name does not change and the ruleset is not
  touched). Every suite still runs, every suite's failure still fails the job,
  and each failure shows that suite's own output.

### Non-goals

- Changing any existing item's governing version, or offering a way to.
- Retiring "1" for new work. A "1" default is the pre-activation state, in
  which `/milestone-plan` creates no tracked item (the roadmap's "deprecation
  policy for very old governing versions" is a later item).
- Splitting the conformance job, adding runners, or changing the ruleset.
- Changing this repository's own `Workflow CI` (`.github/workflows/workflow-ci.yml`,
  not managed, not part of the release; see OD-10).
- Editing this repository's installation (`scripts/`, `.claude/`,
  `docs/ai-workflow/`'s managed files, the managed blocks,
  `.github/workflows/workflow-conformance.yml`). It stays Workflow 2.9.2 and
  `workflow-manager verify .` stays clean.
- The `workflow-manager doctor` warning, and the Manager's own test changes:
  they ship in the Manager pin pull request (D-Manager-Handoff).
- Publishing, pushing, pinning in `workflow-manager`, or changing the
  Controller.

## 2. What exists today (facts this plan relies on)

Read in the release source (`payload/`, `templates/`, `tools/`) at `b854a0b`,
not in the installation.

- **Two functions turn the configuration's default into a new item's
  governing version** (`payload/scripts/workflow_state.py`), and no other code
  does:
  - `route_work_item`, fresh-id branch: after `identity_reference_admits`, it
    runs `validate_governing_version(config["default_workflow_version"],
    config)`, then `default_work_item(..., governing_workflow_version=config[
    "default_workflow_version"])`. Its resume branch reads the stored version
    and never the configuration. Callers: `/milestone-plan` step 1 and,
    through it, the protocol's `plan.start`.
  - `create_remediation_child_work_item`: the same two lines. Callers:
    `/apply-functional-review`'s broad branch and `/apply-pr-review`'s broad
    fix (one mutator with `mark_pr_key_applied`).
- **Every other creator uses a literal, not the configuration:**
  `import_legacy_work_item` ("1", a dormant `LEGACY_READY` entry),
  `bootstrap-workflow-v2.md` (`workflow-v2-1-core`, "1"), and
  `promote_legacy_work_item`, which is not a creation: it moves a dormant
  entry from "1" to the literal "2.1", by design (its docstring: an adopted
  item is already past both implementation-review stages, and the version is
  never `config["default_workflow_version"]`).
- **Bootstrap of a fresh repository.** `templates/docs/ai-workflow/WORKFLOW_CONFIG.json`
  defaults to "2.2" since 2.9.0, and the state template has no work items.
  `default_config()` (no configuration file, before activation) defaults to
  "1". Neither produces a "2.1" default.
- **Configuration transforms.** `build_activated_config` and
  `build_rolled_back_config` have no caller in the release outside their unit
  tests; the documented way to change the default is a hand edit
  (`IMPLEMENTATION_REVIEW_WORKFLOW.md`, "Activating "2.2"": the default and
  `supported_versions` in one commit with a `Workflow-Activation: 2.2`
  trailer; "Rolling back" is its inverse).
- **`supported_versions`** is read in two places only: `validate_config` (the
  default must be a member) and `validate_governing_version` (creation).
  Existing items are checked against the module's own version tables.
- **The 2.9.2 command order around the broad branch.**
  `/apply-functional-review` decides each finding's branch (no code change,
  bounded, broad) "before touching any source/test file". Under 2.9.2 a
  bounded finding then commits the stale technical-approval write alone,
  commits its fix, and only then are the round's broad findings routed (the
  child created) before the checklist commit and, last, the generation
  record. A refusal at child creation would therefore come *after* bounded
  commits; the refusal has to be checked at the decision point (D-Paths).
  `/apply-pr-review` step 1 (`begin_pr_review`) reopens or stores a fact;
  from `MILESTONE_COMPLETE` the first invocation ends after the reopen
  (`LPR-R25-001`) and the next one continues from `already_reopened`.
- **The protocol.** `next-action` with no item named or active uses row 1
  (`plan.start`, `automatic`) when the default is "2.1" or "2.2", and row 1a
  (`blocked`, `plan_start_not_tracked`) otherwise. `verify` has eight checks;
  `gate_policy` is advisory (`ADVISORY_VERIFY_CHECKS`), and
  `orchestration-protocol-v1.schema.json` enumerates the check ids.
  `PROTOCOL_VERSION` is `1.2`, `WORKFLOW_RELEASE` is `2.9.2`.
- **The test suites create "2.1" items through the real creation path.** A
  probe on `b854a0b` (a refusal patched into both functions in a scratch
  conformance fixture outside the repository) broke 282 of the acceptance
  matrix's 353 tests, through its `Item` fixture (`Item` defaults to
  `governing="2.1"`, seeds the configuration's default from it, and
  `Item.milestone_plan` and the module-level `cp4_route` create the item
  through `route_work_item`), one test in `workflow_state_test.py`
  (`test_child_enters_the_plan_review_stage_its_own_governing_version_selects`,
  its "2.1" sub-test) and one in `workflow_fingerprint_generalization_test.py`
  (`test_creation_branch_end_to_end_through_real_bundle_generation`). The
  fingerprint, harness, integration, completion-obligation, gate-policy and
  protocol suites stayed green. W6's new scenarios use a "2.2" default and are
  unaffected.
- **The managed conformance workflow.** `templates/.github/workflows/workflow-conformance.yml`
  (installed as `.github/workflows/workflow-conformance.yml`, a release-owned
  `conformance` template in `manifest.json`'s `templates`, `sha256` and
  `size` recorded) has one job, `workflow-conformance`, with no `name:` (so
  the check is the job id), no `concurrency`, and nine steps that each run one
  suite with `working-directory: scripts`. A failing step skips every later
  suite. No payload suite reads the template; `tools/release/package.py`
  places it in the conformance fixture (`RELEASE_TEMPLATES`).
- **What the suites touch.** They read their own checkout through
  `Path(__file__)` (`scripts/`, `.claude/commands/`, `docs/ai-workflow/`, the
  live `WORKFLOW_STATE.json`), create their scratch repositories with
  `tempfile` (so under `TMPDIR`), and run Git with
  `GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM` defaulted to `/dev/null` where they
  build repositories (`setdefault`, so a caller's value wins). None writes
  `git config --global`. `workflow_protocol_test.py`'s 2.7.0/2.8.0 comparisons
  read tags from the directory above the checkout and skip when it is not a
  Git repository (as in every installation).
- **Parallel safety is already exercised.** The Workflow Manager runs these
  same frozen suites class by class, four workers per CI shard, each chunk
  with a private `TMPDIR` (`tests/parallel/` in `workflow-manager`), and its
  2026-10-11 CI timings (run 38140982424, 2.9.1's suites) rank them: the
  acceptance matrix about 890 s of contended time, the protocol suite about
  490 s, the state suite about 340 s, the gate-policy suite about 230 s, the
  generalization suite about 60 s, and the other four under 25 s each.
  The probe above also ran the nine suites four at a time with the runner
  D-Conformance-Job describes; the results are in section 11.

## 3. Design decisions

### D-Refuse: refuse, never move (OD-1)

One check, in `workflow_state.py`:

- `NEW_WORK_RETIRED_VERSIONS = frozenset({"2.1"})`, the versions a new work
  item can no longer be created on.
- `DefaultWorkflowVersionRetiredError`, a new error.
- `assert_default_admits_new_work_item(config) -> str` runs
  `validate_governing_version` on the default, raises
  `DefaultWorkflowVersionRetiredError` when the default is in
  `NEW_WORK_RETIRED_VERSIONS`, and otherwise returns the default.
- `RETIRED_DEFAULT_NEXT_STEP`, the one sentence every surface prints (the
  error, the protocol's remedy, the `verify` detail), so the wording has one
  home:

  > Set `default_workflow_version` to "2.2" in
  > `docs/ai-workflow/WORKFLOW_CONFIG.json` (with "2.2" in
  > `supported_versions`), commit it with the trailer `Workflow-Activation:
  > 2.2`, then run the command again. Existing "2.1" work items are not
  > affected.

The error message names the configured default, says new work items no longer
start on it, and ends with that sentence.

Why refuse rather than move: a move would make the configuration say one
version while new items get another, which is exactly a silent change of
governance, and an operator reading `WORKFLOW_CONFIG.json` would be wrong about
what their next item runs. A refusal costs one edit, once per repository, and
the error says which. Afterwards the configuration and every new item agree.

### D-Paths: every path, decided (OD-2)

| path | 2.10.0 behavior under a "2.1" default |
| --- | --- |
| `/milestone-plan` for a fresh milestone (and the protocol's `plan.start`) | Refuses. `route_work_item`'s fresh branch calls `assert_default_admits_new_work_item` in place of its two lines, before any write. `milestone-plan.md` step 0's fresh-milestone sentence says so and names the error, so the run stops before step 1 writes anything. |
| `/milestone-plan <existing id>` (resume branch, including a remediation child created earlier) | Unchanged: the stored version governs; the configuration is not read for it. |
| Remediation child, `/apply-functional-review` broad branch | Refuses, whatever the parent's version: a child is new work. `apply-functional-review.md` adds one check at the point where it already decides every finding's branch "before touching any source/test file": if any finding is broad, call `assert_default_admits_new_work_item(config)` first; a refusal stops the round with nothing written (no stale write, no bounded commit, no child), so a re-run after the edit starts from the same point. The refusal holds the whole round, bounded and no-code-change findings included: the edit unblocks the round, not only the broad finding. This is deliberate: under 2.9.2's order the bounded commits come before the child is created, so a later check would leave a half-applied round. After the edit the child is a "2.2" item, exactly as a "2.2" default already makes it in 2.9.2 for a "2.1" parent (no code couples a child's version to its parent's); its plan then goes to `AWAITING_LOCAL_PLAN_REVIEW`, and its implementation to `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` (both are the "2.2" entry phases). |
| Remediation child, `/apply-pr-review` broad fix | Refuses inside its one mutator, so neither the child nor `mark_pr_key_applied` is written. Step 1's write stands: the stored fact, or the reopen. From `MILESTONE_COMPLETE` the first invocation only reopens and ends (`LPR-R25-001`), so the refusal comes on the next one, at `AWAITING_FUNCTIONAL_REVIEW`, with the key in `reopened_for` and not in `applied`; row 38d keeps matching until the edit is made, and the re-run after the edit gets `already_reopened` and continues into the same branch. `apply-pr-review.md` says so in one sentence. |
| Bounded and no-code-change remediation of an existing "2.1" item, in a round with no broad finding | Unchanged (no item is created). |
| Bootstrap of a fresh repository | Unchanged: the template's default is "2.2". A test pins that the template's default is not in `NEW_WORK_RETIRED_VERSIONS`. |
| No configuration file (pre-activation, `default_config()`, default "1") | Unchanged. |
| `import_legacy_work_item`, `bootstrap-workflow-v2.md` (literal "1") | Unchanged: not configuration-derived. |
| `promote_legacy_work_item` (literal "2.1") | Unchanged, deliberately: it adopts an existing item past both review stages; it is not new work (INV-3). |
| `build_activated_config`, `build_rolled_back_config` | Unchanged (no caller). `IMPLEMENTATION_REVIEW_WORKFLOW.md`'s "Rolling back" gains one sentence: a `Workflow-Rollback: 2.2` leaves a "2.1" default, under which new work items are refused. |

### D-Existing: existing "2.1" items (OD-3)

Nothing persisted changes: no migration, no new field, no new value, and no
existing field is rewritten. Every governing-version branch already keys on the
item's stored `governing_workflow_version`, and the only code changed is the
two creation sites. So an existing "2.1" item, under a "2.1" or a "2.2"
default, runs every remaining step as in 2.9.2: its plan revisions go to
`AWAITING_LOCAL_PLAN_REVIEW` (the two-stage plan review covers "2.1"), its
implementation rounds go to `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (the
"2.1" single-stage implementation review) with a person's technical approval,
and its plan amendments, bounded functional fixes (in 2.9.2's commit order)
and acceptance are unchanged. The one difference for a "2.1" parent is the
broad remediation child above: it needs the configuration edit first, and is
then a "2.2" item.

### D-Config-Checks: `supported_versions` and the warning (OD-4)

- "2.1" stays in `supported_versions` (the template, existing configurations,
  the protocol's `supported_governing_versions`). Removing it would make a
  "2.1" default fail `validate_config`, and every command for an existing item
  loads the configuration.
- `validate_config` does not refuse a "2.1" default (INV-5); the refusal is at
  creation only.
- The Workflow's own checks warn: `verify` gains a ninth, advisory check,
  `default_workflow_version`: `warn` when the default is in
  `NEW_WORK_RETIRED_VERSIONS` (detail: the default, that new work items are
  refused, and `RETIRED_DEFAULT_NEXT_STEP`), `pass` otherwise, `skip` when the
  configuration is unreadable (check `config_valid` already fails). Like
  `gate_policy`, it never changes `healthy` and is not part of
  `protocol_ready`: an existing "2.1" item is still driven normally.

### D-Protocol: Orchestration Protocol 1.3, additive

- Row 1 matches a two-stage default that is not in `NEW_WORK_RETIRED_VERSIONS`
  (today "2.2"). A new row **1b**, after row 1 and before row 1a: no item named
  or active and the default is in `NEW_WORK_RETIRED_VERSIONS`, `blocked`,
  reason `plan_start_default_retired`, remedy `RETIRED_DEFAULT_NEXT_STEP`. Row
  1a is unchanged (the "1" default). Without row 1b the protocol would keep
  emitting `plan.start` for a run that refuses. Row 1b is evaluated before row
  1a although its letter sorts after it: `1a` is the unconditional
  fall-through and row ids are stable, so this is the first catalogue position
  where a letter suffix is out of alphabetical order. It is deliberate; the
  protocol notes say so, and `PRINTED_ROW_ORDER` pins the position.
- **Rows 38 and 38d after a refused broad branch: a documented
  `no_progress`, no new row.** `functional.apply_findings` (row 38) and
  `pr.apply_review` (row 38d) are `automatic` appliers. When their broad
  branch refuses, nothing is written (row 38) or only step 1's write is (row
  38d), the phase is unchanged, and `reconcile` classifies the run
  `no_progress` (both rows allow it). From `MILESTONE_COMPLETE`, row 38d's
  first run only reopens (a legal `pr.apply_review` edge to
  `AWAITING_FUNCTIONAL_REVIEW`), so `reconcile` classifies that run
  `progress`, and the repeated `no_progress` begins with the next dispatch.
  The next `next-action` matches the same row and dispatches the same action.
  The protocol cannot see the broad/bounded classification ahead of time (the
  worker makes it by reading the findings), so no row can pre-empt it, and a
  state-dependent signal would write new state (INV-6). The refusal is
  surfaced where the Controller already looks: the worker's output names
  `DefaultWorkflowVersionRetiredError` and `RETIRED_DEFAULT_NEXT_STEP`, the
  advisory `default_workflow_version` `warn` names the same remedy, and the
  protocol notes say that a repeated `no_progress` from row 38 or 38d while
  `verify` reports that `warn` is the refusal, not a stall to retry, and that
  the remedy is the operator's configuration edit. This follows the
  "report instead of looping" reasoning of rows 7a/16a/25b/30a/35a without a
  new row.
- The `verify` check above; `VERIFY_CHECK_IDS`, `ADVISORY_VERIFY_CHECKS` and
  the schema's check-id list gain it.
- `PROTOCOL_VERSION` becomes `1.3`. Section 1 allows a minor bump for new ids
  and codes, and 1.1 set the precedent of a minor bump that changes which
  decision an existing input gets when the Workflow's own behavior changes. A
  1.2 consumer meets a `blocked` decision with an unknown reason code and a
  `verify` check id it does not know: it stops, it does not misact.
- `ORCHESTRATION_PROTOCOL.md`: the header's version, section 1's tested
  releases (Workflow 2.10.0, protocol 1.3), section 5.2's check list, section
  6.3's condition row for 1b, the catalogue rows 1 and 1b and the notes, and a
  section 10 compatibility note. `workflow_protocol_test.py`'s mirror tests pin
  them.

### D-Fixtures: how the tests get an existing "2.1" item

A real repository's "2.1" items were created by an earlier release, so a test
that needs one seeds it the same way. `workflow_test_harness.py` (the shared,
shipped harness) gains two seeds, each pinned against the real creator:

- `seed_existing_work_item(state, *, ...)`: the entry the fresh branch writes
  (`default_work_item(...)` with the given governing version, `feedback_layout:
  "scoped"`, the active pointer claimed when free). Parity test: equal, field
  for field, to `route_work_item`'s output for the same inputs under a "2.2"
  default, with only the version different. The seed deliberately skips
  `identity_reference_admits`: the id it stands for was admitted by the earlier
  release that created it (no matrix scenario depends on that check; its tests
  are unit tests in `workflow_state_test.py`).
- `seed_existing_remediation_child(state, parent_id, *, ...)`: the entry
  `create_remediation_child_work_item` writes: the deterministic
  `<parent>-remediation-<n>` id, `parent_work_item_id`, the given
  `base_commit`, `plan_revision` 1, **no** `active_work_item_id` claim, and
  the `RemediationChildAlreadyExistsError` collision check. Parity test: equal,
  field for field and including the unclaimed pointer and the collision
  refusal, to `create_remediation_child_work_item`'s output under a "2.2"
  default, with only the version different.

How each scenario gets its item, by one principle: **a scenario keeps the real
creator when its subject is the creation; otherwise it seeds the item an
earlier release created.**

- **Fresh items in the acceptance matrix.** `Item.milestone_plan` and the
  module-level `cp4_route` (whose callers include `milestone_plan_real_order`)
  both go through one helper: when the item has no entry yet and the
  configuration's default is in `NEW_WORK_RETIRED_VERSIONS`, it seeds the entry
  with `seed_existing_work_item` and makes no `route_work_item` call; otherwise
  it calls `route_work_item` exactly as today (so every resume call, including
  `cp4_route`'s `amendment=True` callers, is unchanged). The seed consumes the
  same single `Item.now()` tick the fresh call did and writes the entry at
  `state_revision` 1 and `PLANNING`, so each scenario's later revision and
  timestamp sequence is exactly 2.9.2's (a resume call would advance
  `state_revision` and shift every later tick). Every existing scenario keeps
  its meaning: it drives an existing "2.1" item. CP1 searches the test files
  for any absolute `state_revision` or timestamp pin; none is expected, and one
  found is a fixture bug, not an assertion to edit.
- **Scenarios whose subject is the child's creation keep the real call**, with
  their scratch configuration flipped to a "2.2" default first, in a
  `Workflow-Activation: 2.2` commit, which is exactly the post-edit path this
  release prescribes. They then create a "2.2" child of a "2.1" parent, as
  D-Existing states. They are three: `test_c6_broad_remediation_child` (the
  `/apply-functional-review` broad branch creates a child; it stops at
  creation), the child's first-generation layout scenario, and
  `test_remediation_child_re_declaration_at_planning_still_succeeds`. Each
  stops at or near plan binding, so none needs a "2.2" implementation cycle.
  Where an assertion there names the child's version, it changes from "2.1" to
  "2.2", listed in CP1 by test name; no other assertion changes.
- **`test_c7_remediation_child_runs_its_own_cycle` is seeded.** Its subject is
  the child's whole cycle to `MILESTONE_COMPLETE` and the parent's acceptance
  after it, not the child's creation, and it drives that cycle with `Item`'s
  "2.1" path, which does not record the two implementation-review stages a
  "2.2" item needs. `seed_existing_remediation_child` makes the child a
  pre-existing "2.1" one, exactly what an earlier release created, so `test_c7`
  is also a direct regression pin for INV-2 (an existing "2.1" child keeps
  running on "2.1"). Only its child-creation line changes; its later
  `child.milestone_plan()` takes the resume branch, which fills `mapping_path`
  and never reads the configuration, so its assertions and comments stay true.
  The real-creation-then-full-cycle case moves to CP4 scenario 2.
- **Other scenarios that merely need a pre-existing "2.1" child** seed it with
  `seed_existing_remediation_child`. CP1 lists each, found by searching for
  every `create_remediation_child_work_item` call and every `-remediation-` id
  in the test files, with the treatment it got.
- **The two unit tests** the probe broke: the `workflow_state_test.py` sub-test
  tests what the child's version selects, so its "2.1" case seeds the child;
  the `workflow_fingerprint_generalization_test.py` test tests creation, so it
  runs under a "2.2" default, and a new sibling asserts the refusal under "2.1".

### D-Conformance-Job: one job, cancelled when superseded, suites in parallel (OD-8, OD-9)

The template keeps its triggers, `actions/checkout@v4`, `actions/setup-python@v5`
with Python 3.12, and the one job id `workflow-conformance` (no `name:`). Two
changes:

**Concurrency (part A).** A workflow-level block, in the shape this
repository's own `workflow-ci.yml` already uses, except that a run outside a
pull request is keyed by its own run identity, not by its commit:

```yaml
concurrency:
  group: workflow-conformance-${{ github.event_name == 'pull_request' && github.ref || format('{0}-{1}', github.run_id, github.run_attempt) }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

A pull request's runs share one group per pull request (`github.ref` is
`refs/pull/<n>/merge`), and a new push cancels the run in progress. Every
other run (a push to `main`) gets a group of its own, from `github.run_id` and
`github.run_attempt`, so no two runs ever share one and none is cancelled. The
key is the run, not the commit and not the ref, because GitHub replaces a
*pending* run in a group even with `cancel-in-progress: false`: three quick
pushes to `main` under a per-ref group would cancel the middle one's run, and
under a per-commit group so would pushing `main` to the same SHA repeatedly
(restoring it after a rewind, say). A numeric run key cannot collide with a
`refs/pull/...` key, so the event name is not part of the group.

**Parallel suites (part B).** The nine suite steps become one step,
`Run the conformance suites`, `shell: bash`, whose body (about 40 lines of
plain bash, no new tool, no new file in the release) does this:

- **The list.** The nine suites, longest first by the measured times above:
  acceptance matrix, protocol, state, gate policy, generalization, completion
  obligations, integration, fingerprint, test harness. The order changes only
  the wall time, never the result.
- **Width.** `min(4, nproc)` suites at a time: 4 on the 4-vCPU runner a public
  repository gets, 2 on a 2-vCPU private one. A new suite starts as soon as one
  ends (`wait -n`), so the acceptance matrix starts first and the rest fill the
  other slots. The floor is the acceptance matrix's own time (about 9 to 10
  minutes); the other eight together take less than that on three slots.
- **Isolation.** Each suite gets its own directory under
  `$RUNNER_TEMP/workflow-conformance/<suite>/`:
  - `repo/`, a full copy of the checkout (`cp -a "$GITHUB_WORKSPACE/." ...`,
    its `.git` included), and the suite runs in `repo/scripts`. The suites read
    their own checkout through `Path(__file__)` and write `__pycache__`, lock
    files and any scratch output next to it, so a copy each means no suite can
    see another's writes, and each sees exactly the tree it sees today.
  - `tmp/`, exported as `TMPDIR`: every scratch repository a suite creates
    (`tempfile`) is private to it.
  - `home/`, exported as `HOME`: Git's user-level configuration
    (`~/.gitconfig`, and `~/.config/git/config` since the runner leaves
    `XDG_CONFIG_HOME` unset) resolves inside it, so even a suite that wrote a
    global Git setting could not reach another suite.
  - `GIT_CONFIG_GLOBAL` is deliberately **not** set: the suites default it to
    `/dev/null` with `setdefault` where they build repositories, and setting it
    would override that. Everything else is the step's environment, unchanged.
- **Readable output.** While suites run, one line per start and per finish
  (suite, exit status, seconds), so a person watching sees progress. Each
  suite's stdout and stderr go to its own log. When all have ended, every log
  is printed in the list's order: a passed suite inside a collapsed
  `::group::<suite> passed in <n>s`, a failed one unfolded, preceded by an
  `::error title=<suite> failed::exit <status> after <n>s` annotation, so the
  pull request's checks page names the failing suite. A summary table (suite,
  result, seconds) is appended to `$GITHUB_STEP_SUMMARY`.
- **Failure.** Every suite always runs to its end (better than today, where the
  first failure skips the rest). Each suite's exit status is written to its own
  file by the subshell that ran it, which itself always exits 0, so the
  script never depends on `set -e`/`pipefail` to see a failure. The step exits
  1 when any suite failed (or its result file is missing), naming how many,
  and 0 otherwise. The job's result is the step's result, so INV-7 holds.

Why parallel inside one job, not a split: the job name is a required check in
this repository's ruleset and the gate every managed repository waits on;
several jobs would each need a runner and a ruleset change. One job keeps the
check, the runner count and the ruleset as they are.

### D-Wording: the two deferred wording fixes (C)

- `payload/.claude/commands/recover-implementation-provenance.md`'s
  introduction says the phase "stays exactly
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` throughout" and that the command
  recovers "from `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` itself". Its step 2
  already admits, for a "2.2" item, any of `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`,
  `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` and
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`. The introduction says: the phase
  never changes; it is `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` for a "1" or
  "2.1" item, and any of those three implementation-review phases for a "2.2"
  item, as step 2 lists.
- `payload/docs/ai-workflow/MILESTONE_WORKFLOW.md`'s broad-branch bullet says a
  child "routes through the full normal cycle (`AWAITING_EXTERNAL_PLAN_REVIEW`
  → ... → `MILESTONE_COMPLETE`)". It says: a "2.1" or "2.2" child's first plan
  review is `AWAITING_LOCAL_PLAN_REVIEW` (two-stage plan review), a "1" child's
  is `AWAITING_EXTERNAL_PLAN_REVIEW`, and that from 2.10.0 a new child cannot be
  "2.1" (it takes the configuration's default, which can no longer be "2.1").
- Neither file's text is pinned by a golden hash
  (`_GOLDEN_COMMAND_FILE_SHA256` does not list
  `recover-implementation-provenance.md`); CP6 runs the suites that read
  `MILESTONE_WORKFLOW.md`.

### D-Downgrade: what an older release does with this release's state (OD-5)

2.10.0 writes no new state, no new field and no new value, and it never writes
`WORKFLOW_CONFIG.json`. The operator's edit to a "2.2" default is a
configuration 2.9.x already reads. The workflow template change is CI only. The
paragraph for the release notes:

> Workflow 2.10.0 refuses to create a new work item while
> `WORKFLOW_CONFIG.json` names "2.1" as the default, and writes nothing new:
> no state field, no value, no configuration change. A repository on 2.10.0 can
> be read and driven by 2.9.2. Moving back to 2.9.2 restores creation under a
> "2.1" default, so a repository that wants to stay off "2.1" for new work
> keeps its default at "2.2". Moving back also restores 2.9.2's
> `workflow-conformance.yml`, which runs the suites one after another and
> never cancels a run; nothing else depends on the workflow's shape.

The Orchestration Protocol becomes 1.3, additively (D-Protocol).

### D-Manager-Handoff: what the Manager pin pull request carries (OD-6)

Not in this repository. The Manager pin pull request for 2.10.0 (Manager
1.10.0) does three things:

- **The `workflow-manager doctor` warning.** Warn when the target repository's
  `docs/ai-workflow/WORKFLOW_CONFIG.json` has `default_workflow_version: "2.1"`,
  whatever release is installed: on 2.10.0 or later the text says new work
  items are refused; on an earlier release, that they will be after updating to
  2.10.0. `update --dry-run` to 2.10.0 or later shows the same warning. A
  warning, not an error: existing "2.1" items keep working. Next step,
  verbatim from `RETIRED_DEFAULT_NEXT_STEP`: set `default_workflow_version` to
  "2.2" (with "2.2" in `supported_versions`) and commit it with the trailer
  `Workflow-Activation: 2.2`. The Manager does not make the edit (an update
  never rewrites the configuration).
- **The template's suite names.** The Manager's
  `TestAuthoredReleaseCiTemplateSuiteNames` reads each release's suites from
  the template with `run:\s*python3\s+(\S+_test\.py)`. 2.10.0's template names
  them in the step's list instead, so that pattern finds none. The pin pull
  request widens it to every `workflow_[a-z_]+_test\.py` token in the template,
  which gives the same set for every earlier template too (the comment's
  `*_demo_test.py` does not match), and records 2.10.0's `CI_SUITES` counts.
  This loosens the coupling rather than deepening it: the Manager then needs
  only the names, not the step layout.
- **Ordering and protocol.** Versions compare numerically (2.10.0 after
  2.9.2). Releases on protocol 1.3 add row 1b and the advisory
  `default_workflow_version` check.

Nothing here needs a per-release Manager change beyond the pin itself, so the
planned move to a release-agnostic Manager is not affected.

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | recommendation |
| --- | --- | --- |
| OD-1 | Under a "2.1" default, refuse new work items or start them on "2.2" | **Refuse**, with `DefaultWorkflowVersionRetiredError` and one next step (D-Refuse). A move silently changes governance and makes the configuration wrong about what new items run. |
| OD-2 | Which paths the rule covers | **Both configuration-derived creators**, `route_work_item`'s fresh branch and `create_remediation_child_work_item`, with their command callers stopping before any write of the creating branch; literal-version paths, bootstrap and legacy adoption unchanged (D-Paths). |
| OD-3 | A broad remediation child of an existing "2.1" parent | **Refused like any new item**; after the edit it is a "2.2" item, as 2.9.2 already makes it under a "2.2" default. No inheritance: a child is new work, and inheritance would keep creating "2.1" items. Existing "2.1" items otherwise run unchanged (D-Existing). |
| OD-4 | `supported_versions` and a warning | **"2.1" stays supported** and a "2.1" default stays valid; `verify` gains an advisory `warn` check (D-Config-Checks). |
| OD-5 | Downgrade and protocol version | **Nothing new is written**; protocol **1.3**, additive (D-Downgrade, D-Protocol). |
| OD-6 | The Manager side | **A handoff note** for the Manager pin pull request: the doctor warning and the template-suite-name pattern (D-Manager-Handoff). |
| OD-7 | Release version | **2.10.0**, a minor, `feat:` title. Not a patch (new behavior, a new protocol minor), not a major (nothing persisted or already governed changes). The workflow template change is compatible either way. |
| OD-8 | The concurrency group's shape | **Per pull request, and per run (`run_id` and `run_attempt`) for every other event** (D-Conformance-Job), not per ref and not per commit, so a non-PR run is never replaced while pending, even when `main` is pushed to the same SHA repeatedly. |
| OD-9 | How the suites run in parallel | **Inside the one job, `min(4, nproc)` at a time, longest first, each in its own copy of the checkout with its own `TMPDIR` and `HOME`**, plain bash in the template, every log shown in order with failures unfolded and annotated (D-Conformance-Job). |
| OD-10 | This repository's own `release-source-conformance` job (`workflow-ci.yml`), which runs the same nine suites one after another | **Unchanged here.** It is not managed, not part of the release, and not in this milestone's approval; it now bounds this repository's own pull requests. A follow-up can give it the same step body. Its comment "in the same order as workflow-conformance.yml" stays true until this repository installs 2.10.0. |

## 5. Checkpoints

Each checkpoint runs the payload's nine suites in a release-source conformance
fixture and `workflow-manager verify .` on the checkout, with
`TMPDIR=$HOME/.cache/w5-tmp` (`/tmp` is a nearly full shared tmpfs). Package
builds use the Manager venv
`~/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv`.
The installation under `scripts/`, `.claude/` and `docs/ai-workflow/`'s
managed files is never edited.

**Conformance at a checkpoint** (the W4 procedure). `release.py
stage-conformance` exports a committed tree and refuses changed payload bytes
while `manifest.json` still carries 2.9.2's digests, which CP7 refreshes. CP1
to CP6 therefore stage a scratch release from the checkpoint's own commit
(`package.stage` with the venv's Python, into an empty directory outside the
repository), rewrite `sha256` and `size` of every `artifacts` and `templates`
record of the scratch `manifest.json` from the bytes on disk with a throw-away
script kept outside the repository, then run `package.stage_conformance` and
the nine suites in that fixture. CP7 runs the stock `release.py
stage-conformance --commit <CP7 commit>`, and the scratch digests must equal
CP7's committed ones for the same tree.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The refusal at creation, and the test fixtures that seed existing 2.1 items | - | 4 | 1 |
| CP2 | Orchestration Protocol 1.3: row 1b and the advisory verify check | CP1 | 3 | 1 |
| CP3 | Command texts: /milestone-plan, /apply-functional-review and /apply-pr-review stop before any write | CP1 | 2 | 1 |
| CP4 | Regression scenarios end to end: every creation path, existing 2.1 items, a 2.2 default, legacy adoption | CP1, CP2, CP3 | 3 | 1 |
| CP5 | The managed conformance job: cancel superseded pull-request runs, run the suites in parallel | - | 3 | 1 |
| CP6 | Documentation: the rule, the next step, the warning, and the two version-aware wording fixes | CP2, CP3 | 2 | 1 |
| CP7 | Release 2.10.0: manifest, release constant, release history and roadmap | CP1, CP2, CP3, CP4, CP5, CP6 | 2 | 1 |

<!-- CP1 -->
### CP1 — The refusal at creation, and the test fixtures that seed existing "2.1" items

**Files:**

- `payload/scripts/workflow_state.py`: `NEW_WORK_RETIRED_VERSIONS`,
  `DefaultWorkflowVersionRetiredError`, `RETIRED_DEFAULT_NEXT_STEP`,
  `assert_default_admits_new_work_item`; `route_work_item`'s fresh branch and
  `create_remediation_child_work_item` call it in place of their two lines.
  Docstrings updated; nothing else in the module changes.
- `payload/scripts/workflow_test_harness.py`: `seed_existing_work_item` and
  `seed_existing_remediation_child` (D-Fixtures).
- `payload/scripts/workflow_state_test.py`, `workflow_test_harness_test.py`:
  unit tests: `route_work_item` (fresh id) and
  `create_remediation_child_work_item` (with a "2.1" and with a "2.2" parent)
  refuse under a "2.1" default, raise before returning any state, and their
  message ends with `RETIRED_DEFAULT_NEXT_STEP`; both create under a "2.2" and
  under a "1" default exactly as 2.9.2 (the "2.2" entry compared field for
  field); the resume branch for an existing "2.1" item under a "2.1" default
  still advances; `validate_config` accepts a "2.1" default;
  `promote_legacy_work_item` still writes "2.1" under a "2.1" and a "2.2"
  default; the template's default is not retired; every `default_work_item`
  caller in the module either goes through `assert_default_admits_new_work_item`
  or passes a literal (a source scan, so a third creator cannot appear
  unnoticed); the two parity tests (D-Fixtures).
- `payload/scripts/workflow_acceptance_matrix_test.py`,
  `workflow_fingerprint_generalization_test.py`, `workflow_state_test.py`: the
  fixture changes D-Fixtures decides (the one seeding helper behind
  `Item.milestone_plan` and `cp4_route`; the three real-creator scenarios under
  a "2.2" default set by a `Workflow-Activation: 2.2` commit, with their
  child-version assertions changed to "2.2"; `test_c7` and every other
  pre-existing child seeded; the two unit tests).

**Verification:** the nine suites green in the scratch fixture; the
acceptance matrix's test count is 2.9.2's 353 plus the new tests only; a
whole-file diff of each changed test file against `v2.9.2` shows only fixture
seeding, the three named scenarios' default flip and child-version assertions,
the two unit tests, and new tests. No assertion of any other existing scenario
changes, and no scenario whose subject is a child's creation stops calling the
real creator.

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Orchestration Protocol 1.3: row 1b and the advisory `verify` check

**Files:**

- `payload/scripts/workflow_protocol.py`: row 1 narrowed to a default not in
  `NEW_WORK_RETIRED_VERSIONS`, row 1b (`plan_start_default_retired`, remedy
  `RETIRED_DEFAULT_NEXT_STEP`, both read from `workflow_state`), the
  `default_workflow_version` check in `VERIFY_CHECK_IDS` and
  `ADVISORY_VERIFY_CHECKS`, its condition-call table entry,
  `PROTOCOL_VERSION = "1.3"`.
- `payload/docs/ai-workflow/orchestration-protocol-v1.schema.json`: the new
  check id.
- `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`: D-Protocol's edits,
  including the note that row 1b is evaluated before row 1a on purpose and the
  note on rows 38 and 38d after a refused broad branch.
- `payload/scripts/workflow_protocol_test.py`: row 1b for a "2.1" default
  (blocked, the reason code, the remedy, no action); row 1 for "2.2" and row 1a
  for "1" unchanged; `verify` `warn`/`pass`/`skip`, and `healthy` unchanged by
  a `warn`; the catalogue and schema mirror tests; `PRINTED_ROW_ORDER` places
  `1b` between `1` and `1a`, and the two notes are pinned by the mirror tests;
  `describe`'s `supported_governing_versions` still lists "2.1".

**Verification:** the nine suites green in the scratch fixture; the
document-to-code mirror tests green.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Command texts

**Files:**

- `payload/.claude/commands/milestone-plan.md` step 0: a fresh milestone under
  a "2.1" default stops with `DefaultWorkflowVersionRetiredError` and its next
  step, before step 1 (the same refusal `route_work_item` makes).
- `payload/.claude/commands/apply-functional-review.md`: the check at the
  branch decision, before the first bounded sub-step (D-Paths).
- `payload/.claude/commands/apply-pr-review.md`: the broad fix's refusal, that
  step 1's write stands and the item stays at `AWAITING_FUNCTIONAL_REVIEW`, and
  the re-run after the edit from `already_reopened`.
- `payload/scripts/workflow_integration_test.py`: `_GOLDEN_COMMAND_FILE_SHA256`
  for `milestone-plan.md` and `apply-functional-review.md` (changed), and a new,
  deliberate pin for `apply-pr-review.md`, which the table does not carry
  today; static conformance tests that each command names the error and the
  check, and that the `apply-functional-review.md` check precedes the bounded
  branch's first sub-step (the stale write).

**Verification:** the nine suites green; a whole-file diff of each changed
command against `v2.9.2` shows only these sentences.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Regression scenarios, end to end

**Files:** `payload/scripts/workflow_acceptance_matrix_test.py` (its `Item`
fixtures and real generator), a new `RetiredDefaultVersion` class for each
work-item type, driving the functions and commits the command texts name, in
order:

1. **New items under a "2.1" default, every path:** a fresh `/milestone-plan`
   (`route_work_item`), the protocol's `next-action` (row 1b, no `plan.start`),
   a broad functional-review child (the check at the branch decision leaves the
   round unwritten, in a round that also has a bounded finding), and a broad
   pull-request child (the mutator writes neither the child nor `applied`).
   Each refuses with the error. `WORKFLOW_STATE.json` and `HEAD` are unchanged
   for the fresh milestone and the functional-review round; for the
   pull-request child the state is measured from after step 1. For the
   pull-request path from `MILESTONE_COMPLETE`: the first run reopens and ends,
   the second refuses, and the re-run after the edit continues from
   `already_reopened`. For rows 38 and 38d, the `reconcile` class of each run
   (`no_progress` for a refused run; for row 38d from `MILESTONE_COMPLETE`,
   `progress` for the reopen run, then `no_progress`), that the next
   `next-action` matches the same row, and that `verify` reports the `warn`.
2. **The edit, then the same paths:** the configuration changed to "2.2" in a
   `Workflow-Activation: 2.2` commit (exactly `RETIRED_DEFAULT_NEXT_STEP`),
   made on the parent's branch while the parent is at
   `AWAITING_FUNCTIONAL_REVIEW` (no generation gate is armed there). Each path
   then creates a "2.2" item: the fresh milestone, whose plan goes to
   `AWAITING_LOCAL_PLAN_REVIEW`; the functional-review re-run classifies and
   acts on the same findings (the bounded one in 2.9.2's commit order) and
   creates a "2.2" child of the "2.1" parent; the pull-request re-run does the
   same from `already_reopened`. The "2.2" child is driven through its own full
   cycle to `MILESTONE_COMPLETE` with an `Item` bound to it: plan review to
   approval, implementation, the local and the manual implementation-review
   records (the bodies of the suite's `local_review`/`manual_review` helpers,
   `record_local_implementation_review` and
   `record_manual_implementation_review`, run against the child), then
   `Item.approve_implementation`, `prepare_functional_review` and
   `accept_milestone`, as `test_s03_...` and `test_c7` do. Only then is the
   parent accepted (`complete_work_item` refuses while a child is open).
3. **An existing "2.1" item under a "2.1" default, through its remaining
   steps, in one run:** seeded at `PLANNING`, then a plan REVISE and revision
   (back to `AWAITING_LOCAL_PLAN_REVIEW`), plan approval, implementation, the
   "2.1" implementation review at `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` and
   the human technical approval, a plan amendment from `IMPLEMENTING`, the
   functional gate with a bounded fix in 2.9.2's order (stale write alone, fix,
   checklist, generation record last), and acceptance. Its
   `governing_workflow_version` is "2.1" at every step. (The CP1-migrated `Item`
   scenarios already run each "2.1" step under a "2.1" default; this one
   chains them for one item.)
4. **The same item under a "2.2" default:** the same run, and it stays "2.1".
5. **A "2.2" default unchanged:** a fresh milestone and a broad child create
   "2.2" items as in 2.9.2.
6. **Legacy adoption unchanged:** an imported `LEGACY_READY` item promoted
   under a "2.1" and under a "2.2" default becomes "2.1" at
   `AWAITING_FUNCTIONAL_REVIEW`, as in 2.9.2.
7. **Bootstrap:** a repository seeded from the shipped templates creates a
   "2.2" item, and `verify` passes the new check.

**Verification:** scenarios 1 and 2 fail against 2.9.2 (they expect the
refusal) and pass now; 3 to 6 pass against 2.9.2 and now, and are named as
regression pins. Scenario 7 is split: its bootstrap assertion (the shipped
templates seed an item that is "2.2") passes against 2.9.2 and now, and is a
regression pin; its `verify`-passes-the-new-check assertion cannot run against
2.9.2, which lacks that check (`payload/scripts/workflow_protocol.py:392`), so
it is a new assertion that fails there and passes now.

<!-- /CP4 -->

<!-- CP5 -->
### CP5 — The managed conformance job

**Files:**

- `templates/.github/workflows/workflow-conformance.yml`: the `concurrency`
  block and the one parallel step (D-Conformance-Job); the header comment says
  how the suites run (in parallel, each isolated, every one always run). The
  job id, triggers, checkout and Python setup are unchanged.
- `tools/release/release_test.py` (run by this repository's `tooling` job; no
  payload suite changes, so the suites' own counts are unaffected by this
  checkpoint), a new `ConformanceTemplate` class:
  - the template has exactly one job, `workflow-conformance`, with no `name:`,
    and the `concurrency` group and `cancel-in-progress` expressions above,
    character for character;
  - the group expression, evaluated by a small interpreter in the test for
    exactly the constructs it uses (`==`, `&&`, `||`, `format`, the `github`
    context): two distinct `push` runs with the same event and SHA (different
    `run_id`, or the same `run_id` with different `run_attempt`) get different
    groups, so neither can replace the other; two `pull_request` runs of one
    pull request (same `github.ref`, different `run_id`) get the same group and
    `cancel-in-progress` is true; a pull request's group differs from any push
    run's; for a push `cancel-in-progress` is false;
  - the step's suite list equals the conformance suites the release ships (the
    manifest's `scripts/workflow_*_test.py` artifacts minus the two
    `*_demo_test.py`), so a suite added later without being listed fails here;
  - the step body, cut out of the template and run with `bash` against a stub
    checkout of nine stub suites, with `GITHUB_WORKSPACE`, `RUNNER_TEMP` and
    `GITHUB_STEP_SUMMARY` pointed into a scratch directory: all pass, exit 0;
    one fails, exit 1, every suite still ran, the failing suite's own output
    appears unfolded after its `::error` line, the passing ones inside
    `::group::`; at most four ran at once (each stub records itself in a shared
    counter directory); each stub saw its own `HOME`, `TMPDIR` and tree and
    none saw another's marker; the original checkout is unchanged; the summary
    table lists all nine.

**Verification:** the full `release_test.py` cannot run on the CP5 commit as
committed: its `test_round_trip` stages `HEAD` of `REPO_ROOT`
(`release_test.py:390`) and `package.py:267` rejects `manifest.json`'s stale
digests, which only CP7 refreshes. The release digest checks are neither
skipped nor weakened. Instead, the full suite runs in a **scratch Git
checkout**: a clone of the repository at the CP5 commit, outside the
repository, in which the throw-away script above rewrites `sha256` and `size`
of every `artifacts` and `templates` record of `manifest.json` from the bytes
on disk and the result is committed in the clone only. `REPO_ROOT` derives from
the test file's own location, so `python3 -m unittest tools/release/release_test.py`
run from the clone reads the clone's refreshed manifest and `HEAD`, and every
digest guard runs unmodified. That run is green; the real `release_test.py` on
the real tree runs at CP7, after the committed digests are refreshed, and must
be green there too. The nine payload suites, run by this
step body against the CP5 scratch fixture (the same isolation, four at a
time), green, with the wall time recorded in the checkpoint's commit message
next to the sequential time; `workflow-manager verify .` clean (the installed
copy is untouched).

<!-- /CP5 -->

<!-- CP6 -->
### CP6 — Documentation

**Files:**

- `payload/docs/ai-workflow/IMPLEMENTATION_REVIEW_WORKFLOW.md` ("Activating
  "2.2"" and "Rolling back"), `WORKFLOW_V2_1_OPERATOR_REFERENCE.md` (creation
  and remediation children), `MILESTONE_WORKFLOW.md` (the `PLANNING` entry, and
  D-Wording's broad-branch fix): one paragraph each; no list of governing
  versions is quoted.
- `payload/.claude/commands/recover-implementation-provenance.md`: D-Wording's
  introduction fix.
- `docs/install.md`, `docs/gates.md`: an existing configuration that still
  names "2.1" must be changed before the next new item, and for
  `/apply-functional-review` the edit unblocks the whole round.
- `docs/common-problems.md`: "A new work item was refused: the default is
  "2.1"", with the next step and where to commit it: on the new work's branch
  where there is one; for the two remediation-child paths, on the parent's
  branch while the parent is at `AWAITING_FUNCTIONAL_REVIEW` (no generation gate
  is armed there; `bundle_generation_mismatch` is checked only at the plan and
  implementation gates, and `WORKFLOW_CONFIG.json` is excluded in the template's
  implementation-stage classification); otherwise where no item is awaiting a
  review or gate, naming `/recover-implementation-provenance` for the case
  where it already happened. Also the `verify` warning.

**Verification:** `tools/docs/check_docs.py` clean; the operator-reference and
command-text tests green; a whole-file diff of the two D-Wording files shows
only those sentences.

<!-- /CP6 -->

<!-- CP7 -->
### CP7 — Release 2.10.0

**Files:** `manifest.json` (version `2.10.0`, every changed `sha256`/`size`,
the conformance template's record and derivation text, `counts`; **committed
before the bundle-generation record**), `payload/scripts/workflow_protocol.py`
(`WORKFLOW_RELEASE` `2.10.0`), `payload/scripts/workflow_protocol_test.py`
(the release pin), `docs/release-history.md` (the 2.10.0 row: the refusal and
its next step, the faster conformance job, the downgrade paragraph, protocol
1.3, and that this repository's own installed copy of the workflow changes only
when it updates to 2.10.0), `docs/ROADMAP.md` (row 7 marked Done at
acceptance), `docs/ACTIVE_MILESTONE.md`.

**Verification:** the full `tools/release` tests (`release_test.py`, now against the committed, refreshed digests) and the package build with the venv;
`release.py check-title --agree` for a `feat:` title against the 2.9.2 to
2.10.0 change; `workflow-manager verify .` clean.
`tools/release/manager-pin.json` stays at 1.9.0: this repository's
installation stays 2.9.2, which that Manager pins, and the release is built
from source (`docs/RELEASING.md` bumps the pin only when an installation update
needs a newer Manager).

<!-- /CP7 -->

## 6. Tests and verification summary

CP1 unit tests and the fixture migration, CP2 protocol tests, CP3 static
conformance and golden hashes, CP4 end-to-end scenarios (seven above), CP5 the
template tests and a parallel run of the real suites, the nine suites green,
`check_docs.py`, the release package build, and `workflow-manager verify .`.

## 7. Release and follow-ups (owner actions, after acceptance)

Pull request titled `feat: ...`, squash merge; the `Release` workflow publishes
2.10.0 when `main`'s manifest names it. Then the Manager pin pull request in
`workflow-manager` (Manager 1.10.0), carrying D-Manager-Handoff. Consumers get
the refusal and the new conformance workflow through `workflow-manager update`;
this repository's own installed copy changes only when it updates to 2.10.0.
Any repository whose configuration still names "2.1" (the doctor finds it)
makes the one edit before its next new item. A possible follow-up: give
`workflow-ci.yml`'s `release-source-conformance` job the same step body (OD-10).

## 8. Risks

- **An operator meets the refusal mid-command.** Every caller stops before the
  first write of the branch that creates the item, and the error carries the
  next step. `/apply-pr-review` has already written in step 1, so its item is
  left at `AWAITING_FUNCTIONAL_REVIEW` until the edit is made. CP4 scenario 1
  checks the state is unchanged from after step 1.
- **An automatic row re-dispatches the refused action.** Rows 38 and 38d
  classify a refused broad run `no_progress` and match again (D-Protocol); the
  worker's error, the `verify` `warn` and the protocol notes name the remedy,
  and CP4 pins the behavior.
- **The configuration commit lands in another item's review interval.** Any
  commit after an in-flight item's generation record makes that item's gate
  refuse with `bundle_generation_mismatch`. CP6's documentation says where to
  make the edit and names the recovery. No code change: the read side stays
  strict.
- **A hidden creation path.** Only two functions read the default for a new
  item (section 2); CP1's source scan keeps it that way.
- **Fixture drift.** Both seeds are pinned against the real creators.
- **An unaware protocol consumer.** It meets a `blocked` row and an unknown
  advisory check: it stops (D-Protocol).
- **A suite that is not parallel-safe.** The Manager already runs these suites
  four at a time, and each suite here gets its own tree, `TMPDIR` and `HOME`;
  CP5 runs the real suites through the step body. If one still flakes under
  contention, the fix is in that suite, not in serializing the job.
- **The Manager's template test.** It finds no suite names in the new template
  until the pin pull request widens its pattern (D-Manager-Handoff); that pull
  request is where 2.10.0 is first tested in the Manager anyway.
- **Golden hashes and manifest digests drift.** CP3 and CP7 own them; the
  manifest is committed before the generation record.

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/retire-21-for-new-work-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | Creating a new work item under a "2.1" default refuses before any write, with a named error and one next step, on every configuration-derived path | CP1, CP3, CP4 |
| REQ-2 | Existing "2.1" items, legacy adoption, and "2.2" and "1" defaults behave as in 2.9.2; nothing persisted changes | CP1, CP4 |
| REQ-3 | "2.1" stays supported; the protocol reports the refusal (row 1b) and the Workflow's own checks warn | CP2 |
| REQ-4 | The managed conformance job cancels superseded pull-request runs and runs every suite in parallel inside the one `workflow-conformance` job, isolated, with each failure shown | CP5 |
| REQ-5 | The rule, the next step, the two version-aware wording fixes, the downgrade posture and the Manager handoff are written down | CP6, CP7 |
| REQ-6 | 2.10.0 is releasable | CP7 |

## 10. Artifact classification

`docs/ai-workflow/registry/retire-21-for-new-work-artifacts.json` comes from
the `process` template and is fitted to this plan's footprint, as W6's was.

**Plan stage.** Protected: this plan document, the registry and the mapping.
Excluded beyond the template: `manifest.json`, `docs/RELEASING.md`,
`docs/release-history.md`, `docs/common-problems.md`, `docs/install.md`,
`docs/gates.md` and the prefixes `payload/`, `fixtures/`, `templates/` and
`tools/`. `docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`, `docs/ai-workflow/…`
(this plan's own protected paths are matched first), `.workflow-manager/`,
`.github/` and the installation's `scripts/` and `.claude/commands/` are
classified by the template. Every repository path this document names is run
through the classifier before the bundle is generated.

**Implementation stage.** Protected: `manifest.json`, `docs/RELEASING.md`,
`docs/release-history.md`, `docs/common-problems.md`, `docs/install.md`,
`docs/gates.md`, the prefixes `payload/`, `fixtures/`, `templates/` and
`tools/`, the installation prefixes `.claude/commands/` and `scripts/` (never
edited here; protecting them makes a stray edit visible to the technical
approval), and the declarations file's own path. `docs/ROADMAP.md` and
`docs/ACTIVE_MILESTONE.md` stay excluded as bookkeeping, and `.github/` stays
excluded (this repository's own CI is not changed; the managed template lives
under `templates/`).

## 11. Re-plan notes and review rounds

### Revision 2: manual external review round 1 (REVISE)

- **I1 accepted.** The non-PR concurrency group is keyed by `run_id` and
  `run_attempt` (D-Conformance-Job, OD-8, CP5's expression pin); a regression
  test covers distinct non-PR runs with the same event and SHA, and the
  complementary pull-request sharing and cancellation.
- **I2 accepted.** CP5 runs the full `release_test.py` in a scratch Git
  checkout with refreshed digests; the digest guards are unchanged. The real
  tree runs it at CP7.
- **O1 accepted.** CP4's scenario 7 is split into an unchanged bootstrap pin and
  a new `verify`-check assertion.

### What changed from the 2.9.1 plan (revision 3, local APPROVE, never committed)

- Re-based on `b854a0b` (2.9.2). Every fact in section 2 was re-checked there;
  the probe was re-run (282 of 353 matrix tests broken, against 280 of 331
  before; the same two unit tests).
- **2.9.2's commit order moved the functional-review check.** The bounded
  branch now commits before broad findings are routed, so the check sits at the
  branch decision, before the first bounded sub-step, and CP4 drives a mixed
  round (D-Paths).
- **The previous round-3 optional findings, adopted.** R3-001: D-Fixtures'
  `test_c7` rationale now says what `Item`'s "2.1" path does not record, not
  that `Item` cannot drive "2.2". R3-002: CP4 scenario 2 names the drivers that
  can run the child (the review-record bodies against a child `Item`), not
  `start(governing="2.2")`, which reseeds the state. R3-003: the real-creator
  list names `test_c6` once. R3-004: `cp4_route` and `milestone_plan_real_order`
  go through the same seeding helper as `Item.milestone_plan`, resume calls
  excepted. R3-005: the seed's omission of `identity_reference_admits` is
  stated. R3-006: the header's revision is correct.
- **Added scope (2026-10-11):** D-Conformance-Job and CP5 (parts A and B),
  D-Wording folded into CP6 (part C), REQ-4, OD-8 to OD-10, and the template
  pattern in D-Manager-Handoff. The release checkpoint is now CP7.

### Parallel trial (planning)

The probe above was run through a prototype of D-Conformance-Job's step body
(four at a time, each suite in its own copy with its own `TMPDIR` and `HOME`,
logs printed per suite), on a 16-CPU workstation capped at four:

- **The probe** (the refusal patched in): the runner reported exactly the three
  failing suites, each with its own `::error` line and unfolded log, ran every
  other suite to its end, and exited 1.
- **An unpatched run of `b854a0b`'s release source:** all nine suites green, so
  none interferes with another under this isolation. The wall time was 255 s,
  exactly the acceptance matrix's own time (the floor), against 580 s for the
  nine per-suite times added up (matrix 255, protocol 141, state 90, gate
  policy 66, generalization 17, completion obligations 5, fingerprint 3,
  integration 2, harness 1). A GitHub runner is slower per CPU; the same ratio
  gives the expected 22 to about 10 minutes there.
