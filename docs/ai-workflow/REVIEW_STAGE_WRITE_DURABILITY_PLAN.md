# W4: Workflow 2.9.1 — review-stage state writes are committed when they must be, and left alone when they must be (Revision 4)

- **Work item:** `review-stage-write-durability` (`process`, governing version `2.2`)
- **Roadmap step:** W4 (`docs/ROADMAP.md`), a small fix release before the Manager's and the Controller's next steps.
- **Branch:** `milestone/review-stage-write-durability`
- **Base commit:** `576dfd5` (the release source is Workflow 2.9.0, which this repository's own installation also runs, with automatic gates and no `GATE_POLICY.json`)
- **Plan revision:** 4
- **Issue:** RodrigoFAbreu/workflow#13 and its correction comment.

## 1. Goal

Ship Workflow 2.9.1, a patch release (a bug fix, so a `fix:` title), that
makes the command texts, followed in order, reach the next gate for **both**
outcomes of an implementation review, for every governing version that has the
step-0 route (`"1"`, `"2.1"` and `"2.2"`; the REVISE half below is `"2.2"`
only, because only the two-stage implementation review exists for `"2.2"`):

- **REVISE.** A review stage that returns REVISE persists its phase write and
  never commits it. `/apply-implementation-review` then commits the post-fix
  `Workflow-Bundle-Generation-Record` "alone", and that commit picks the
  uncommitted REVISE write up. Its net diff against its parent has no `phase`
  change (`AWAITING_LOCAL_IMPLEMENTATION_REVIEW` to the same), and the
  ordinary-role check refuses it (`workflow_state.py`, "an ordinary
  bundle-generation-record commit must always transition phase
  (OPUS-R101-001)"). No order of the command texts leads out.
- **APPROVE.** The opposite rule holds. A review-stage APPROVE write committed
  on its own, after the generation record, puts HEAD past the MANIFEST's
  `generation_head`: `/satisfy-gate implementation` and
  `/approve-review implementation` refuse with `bundle_generation_mismatch`,
  and the only remedy, `/recover-implementation-provenance`, changes the
  `bundle_id` and stales both verdicts. The working path is to leave APPROVE
  writes uncommitted so the approval commit picks them up.

A third path shares the REVISE dead end and is not version-specific:
`/apply-implementation-review` step 0's own entry into `APPLYING_REVIEW_FEEDBACK`
(`enter_applying_review_feedback`, the "late problem" route from the terminal
`AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`). For a `"1"`/`"2.1"` item this is the
**ordinary** route: the generation record `T` commits
`AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` (`bundle_generation_target_phase`),
step 0 persists `APPLYING_REVIEW_FEEDBACK` through `state_transaction` and no
step commits it, and step 7's post-fix record then has the net phase
`AWAITING_EXTERNAL_…` to `AWAITING_EXTERNAL_…`, refused by the version-independent
ordinary-role check. The payload's tests hide the gap by inserting the missing
commit by hand (`workflow_protocol_test.py` `implementation_apply_review`:
`h.commit_state(self.repo, "enter APPLYING_REVIEW_FEEDBACK")`;
`workflow_acceptance_matrix_test.py` `enter_applying_feedback`;
`workflow_state_test.py` `_enter_applying_review_feedback`). 2.9.0 keeps an
existing installation's default version, so live `"2.1"` items take this route.
This release covers it (LPR-R2-001).

Neither rule is written in any command text today. This release writes both
down, makes the REVISE branch do its part itself, and adds a safety net that
keeps the Controller and the Manager lane (which already commit the REVISE
write alone) working unchanged.

### Hard requirements (invariants)

- **INV-1, the read side stays strict.** No generation, provenance or
  gate-reachability check accepts a commit shape it refused in 2.9.0. HEAD
  must still equal the generation-record commit `T` exactly
  (`verify_implementation_provenance_interval`, condition 1), `MANIFEST.md`'s
  `generation_head` must still equal HEAD (`assert_local_generation_matches`),
  and `validate_bundle_generation_record_commit` is untouched.
- **INV-2, APPROVE is never committed on its own.** Nothing this release adds
  commits an APPROVE write *unless the same commit moves the item into
  `APPLYING_REVIEW_FEEDBACK`* (an uncommitted APPROVE ledger that precedes a
  REVISE, or a step-0 late-problem entry, rides in with that move, as it does
  in 2.9.0), and the new helper refuses an APPROVE-shaped pending write (a
  working phase other than `APPLYING_REVIEW_FEEDBACK`).
- **INV-6, the safety net never refuses a route into `APPLYING_REVIEW_FEEDBACK`
  that 2.9.0 accepts.** It classifies by the *working* phase and the HEAD
  phase's membership in
  `bundle_generation_recovered_role_legal_committed_phases(<the item's own
  governing version>)` (D-Helper), not by HEAD's phase alone. For `"1"`/`"2.1"`
  that set is `{AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW}`, exactly the HEAD
  phase of their step-0 route; for `"2.2"` it is the three-phase set.
- **INV-3, idempotent.** A REVISE write that is already committed (by the
  Controller, the Manager lane, or an earlier run of the new step) is a
  no-op, not an error.
- **INV-4, additive protocol, no new accepted shape.** Orchestration Protocol
  stays 1.2. See D-Downgrade.
- **INV-5, the plan stage is not changed in behavior.** It is checked, found to
  have no dead end, written down and pinned by a test (D-Plan-Stage).

### Non-goals

- Loosening any check on the read side (candidate (c)); see OD-1.
- Changing what `/recover-implementation-provenance` does.
- Editing this repository's installation (`scripts/`, `.claude/`,
  `docs/ai-workflow/`'s managed files, the managed blocks); it stays Workflow
  2.9.0 and `workflow-manager verify .` stays clean.
- Publishing, pushing, pinning in `workflow-manager`, or changing the
  Controller.

## 2. What exists today (facts this plan relies on)

All of this was read in the release source (`payload/`), not the installation.

- **The four review-stage state writers** (`payload/scripts/workflow_state.py`):
  `record_local_plan_review`, `record_manual_plan_review`,
  `record_local_implementation_review`, `record_manual_implementation_review`.
  Their commands persist through `state_transaction` and stop; none of
  `review-plan.md` step 8, `record-manual-plan-review.md` step 7,
  `review-implementation.md` A6 or `record-manual-implementation-review.md`
  step 7 says to commit, or to leave uncommitted.
- **Implementation stage, REVISE.** `record_local_implementation_review(...,
  verdict="REVISE")` and `record_manual_implementation_review(...,
  verdict="REVISE")` set `APPLYING_REVIEW_FEEDBACK` and bump
  `state_revision`/`last_transition`; the local stage writes no ledger entry
  on REVISE. `/apply-implementation-review` step 0 skips
  `enter_applying_review_feedback` (the phase is already
  `APPLYING_REVIEW_FEEDBACK`), step 1 may commit a `BLOCK` pin alone, and step
  7 commits `record_bundle_generation`'s write alone through
  `stage_scoped_state`.
- **Step 0, every version.** `/apply-implementation-review` step 0 calls
  `enter_applying_review_feedback` (legal only from
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`) for `"1"`, `"2.1"` and `"2.2"`
  items alike and persists it through `state_transaction`; nothing commits the
  entry. For `"1"`/`"2.1"` this is the only route into
  `APPLYING_REVIEW_FEEDBACK` after an external review; the dead end of the
  first bullet applies to it unchanged.
- **Implementation stage, APPROVE.** The ledger entries and the phase moves
  (`AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`, then the terminal
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`) stay uncommitted. This is the
  designed positive path, not an accident: `TECHNICAL_APPROVAL_COMMIT_FIELDS`
  (`workflow_state.py`, CP12 comment) was widened precisely because the
  manual stage's ledger write "sits uncommitted until the very next commit,
  which for a 2.2 item is always `/approve-review implementation`'s own
  technical-approval commit". `/satisfy-gate implementation` commits the same
  way (`stage_scoped_state`).
- **The two checks that make the APPROVE trap.** `assert_local_generation_matches`
  (`workflow_fingerprint.py`) compares `MANIFEST.md`'s `generation_head` with
  HEAD, and `verify_implementation_provenance_interval` requires live HEAD to
  equal the discovered generation-record commit `T` exactly. Both are called by
  the gate wrappers and, for the first, by the review and manual-ingest
  commands themselves.
- **Where REVISE is safe to commit.** In the ordinary case
  `record_bundle_generation(stage="post-fix", head=HEAD)` sets
  `P = reviewed_implementation_head` to the last fix commit, so the REVISE
  commit sits before `P`, in `base..P`, where `WORKFLOW_STATE.json` is excluded
  at the implementation stage. It lands strictly inside `P..T` only on the
  `same_content` outcome, where every non-terminal commit must classify
  implementation-stage excluded-only, and this one does. The Controller and the
  Manager lane commit the REVISE write alone today and their rounds pass.
- **Plan stage.** None of `/review-plan`, `/record-manual-plan-review` or
  `/apply-plan-review` commits state (only `apply-plan-review.md` and
  `milestone-plan.md` make a git call, `git add -N`; `review-plan.md` and
  `record-manual-plan-review.md` make none), and `/milestone-plan` says "Do not commit them". The plan stage has no
  generation-record commit, so the ordinary-role check never applies. The
  plan-approval commit (`/approve-review plan`, `/satisfy-gate plan`) reads the
  working-tree state as its `pre_state`, pins the whole blob and commits it, so
  every earlier plan-stage write (a REVISE, the CONSUMED record, PUBLISHED,
  BOUND) rides into it. `plan_approval_gate_status` runs the same
  `assert_local_generation_matches`, so a plan-stage write committed alone
  after the bundle was generated would raise `bundle_generation_mismatch`
  there too. The plan stage has no dead end; it has an unwritten rule.
- **Other writers.** `/request-plan-amendment` already commits its own write.
  `record_technical_review_block_pin` is committed alone (apply step 1).
  `/review-functional` writes no state; `/apply-functional-review` commits with
  `stage_scoped_state`. No other review-verdict writer exists.
- **Release mechanics.** `_GOLDEN_COMMAND_FILE_SHA256`
  (`workflow_integration_test.py`) pins command-file hashes; `manifest.json`
  carries every payload digest, the release string and the derivation text;
  `WORKFLOW_RELEASE` (`workflow_protocol.py`) is `2.9.0`, `PROTOCOL_VERSION`
  is `1.2`.

## 3. Design decisions

### D-Rule: the commit rule for a review-stage write

Written down once, in `REVIEW_PROTOCOL.md`, and pointed to from the command
texts:

| Write | Stage | Commit? | Why |
| --- | --- | --- | --- |
| REVISE (a 2.2 item) | local or manual implementation review | **Yes, alone, before any fix commit** | a fix commit and the post-fix generation record would otherwise sweep it up and the record would not transition `phase` |
| entry into `APPLYING_REVIEW_FEEDBACK` by `/apply-implementation-review` step 0 (`enter_applying_review_feedback`, from the terminal `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`; **every governing version**: for `"1"`/`"2.1"` this is the ordinary route, HEAD at `T` with phase `AWAITING_EXTERNAL_…`; for `"2.2"` it is the late-problem route, either HEAD at `T` (`AWAITING_LOCAL_…`) with the APPROVE writes uncommitted, or HEAD at a recovered-role record (`AWAITING_EXTERNAL_…`)) | implementation | **Yes, alone, before any fix commit** (any uncommitted APPROVE ledgers ride in with it) | same dead end as REVISE on every route where the entry leaves the item at its target phase: the post-fix record would otherwise sweep the move up with a net no-change phase (`AWAITING_EXTERNAL_…` to the same for `"1"`/`"2.1"`; `AWAITING_LOCAL_…` to the same for `"2.2"` from HEAD at `T`). From a `"2.2"` HEAD recovered at `AWAITING_EXTERNAL_…` the post-fix record already shows a real transition to `AWAITING_LOCAL_…`; committing the entry is harmless there and keeps one rule |
| APPROVE | local or manual implementation review | **No** | the approval commit (`/approve-review implementation` or `/satisfy-gate implementation`) picks it up; a commit of its own puts HEAD past `generation_head` |
| BLOCK | either | nothing to commit (no state write) | |
| any write | plan stage | **No** | no generation record exists; the plan-approval commit takes the whole working-tree state; a commit of its own raises `bundle_generation_mismatch` at the plan-approval gate |

### D-Helper: one idempotent helper (OD-2)

`workflow_state.commit_pending_applying_review_feedback_entry(repo_root,
work_item_id, *, attribution=())` returns the new commit's SHA, or `None` when
there is nothing to commit. It is not a state writer (it writes no state; it
stages and commits what `state_transaction` already wrote).

1. Read `HEAD`'s `work_items[work_item_id]` and the working tree's. If the
   two entries are equal, return `None` (nothing pending: the write was
   committed already, or none was made). There is no governing-version early
   return: the version only selects the set in step 2 (LPR-R2-001).
2. Classify by the *working* phase and `HEAD`'s phase, not by `HEAD`'s phase
   alone (INV-6); the helper infers the writer from that phase pair and does
   not know it (LPR-R2-002). The pending write is a committable "entry into
   `APPLYING_REVIEW_FEEDBACK`" when the working phase is
   `APPLYING_REVIEW_FEEDBACK` and `HEAD`'s phase is in
   `bundle_generation_recovered_role_legal_committed_phases(<the item's own
   governing version>)`: for `"2.2"` `AWAITING_LOCAL_…`,
   `AWAITING_MANUAL_EXTERNAL_…` or the terminal
   `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`; for `"1"`/`"2.1"` the terminal
   phase only. That one rule covers a local REVISE, a manual REVISE and step
   0's entry, from HEAD at `T` or from a HEAD that
   `/recover-implementation-provenance` left at `AWAITING_EXTERNAL_…`, for
   every version. If `HEAD`'s phase is already
   `APPLYING_REVIEW_FEEDBACK`, return `None` (the entry is committed; any other
   difference, such as a `BLOCK` pin, belongs to its own commit). Any other
   difference, including a working phase other than `APPLYING_REVIEW_FEEDBACK`
   (an uncommitted APPROVE: HEAD `AWAITING_LOCAL_…`, working
   `AWAITING_MANUAL_EXTERNAL_…`), refuses with
   `ReviewStageWriteNotCommittableError`, naming both phases and, for an
   APPROVE-shaped write, the D-Rule row that says to leave it (INV-2). The
   classification table lives next to
   `bundle_generation_recovered_role_legal_committed_phases` in
   `workflow_state.py`, and the helper reads that function's set rather than
   restating it, so the two cannot drift apart.
3. The item's field diff must be a subset of
   `REVIEW_STAGE_WRITE_COMMIT_FIELDS` (`phase`, `state_revision`,
   `last_transition`, `implementation_review_stages`, `gate_evidence`,
   `reopenings`, the same set the recovered-role record already admits, so a
   local APPROVE that was left uncommitted rides in with the manual REVISE).
   Anything else, for example `reviewed_implementation_head`, refuses. The
   error message, and the `docs/common-problems.md` entry (CP4), name the
   remedy for a crash-left foreign field: a persisted but uncommitted
   `technical_review_block_pins` entry is committed alone first, as
   `/apply-implementation-review` step 1 does, then the command is re-run.
4. Require an index with nothing staged but the state file
   (`DirtyIndexBeforeStagingError` otherwise), then stage, then commit. The
   staging is **resumable** (EPR-001): `stage_scoped_state` stages a
   target-only blob when foreign work-item residue is present and then refuses
   a retry, because the state path is "already staged and differs from
   `HEAD`". A crash between that staging and the commit would therefore leave
   the safety net refusing its own earlier work. So the helper first computes
   the blob that scoped staging would stage (`HEAD`'s state with only this
   item's entry taken from the working tree, serialized by the module's one
   canonical serializer; this construction is extracted from
   `stage_scoped_state` into a private function that both call, with no change
   to `stage_scoped_state`'s behavior or bytes) and compares it with the
   *staged* blob of the state path:
   - nothing staged: call `stage_scoped_state(repo_root, work_item_id)` (the
     ordinary single-path `git add` of the working file when it returns
     `False`);
   - the staged blob equals the expected target-only blob (or, when scoped
     staging does nothing, the working file's bytes): this is the helper's own
     interrupted staging; skip staging and go to the commit;
   - the state path is staged with any other content, or any other path is
     staged: `DirtyIndexBeforeStagingError`, unchanged, so unrelated staged
     content is still refused and never committed.

   Commit with the subject
   `chore(workflow): record entry into APPLYING_REVIEW_FEEDBACK for <id>`, the
   caller's attribution lines, and `Workflow-Work-Item: <id>` as the final
   paragraph. No other trailer: this commit is not a generation record. The
   first line of a retry that finds `HEAD` already carrying the entry returns
   `None` (step 1: the entries are equal), so a crash after the commit is also
   safe and exactly one entry commit ever exists. Foreign work-item residue
   stays in the working tree and out of the commit in every case.

### D-Commands: where it is called

- `review-implementation.md` A6, `REVISE`: after the persist, call the helper.
  `APPROVE`: a new sentence, "leave it uncommitted; do not commit it; the
  approval commit picks it up", with the reason.
- `record-manual-implementation-review.md` step 7: the same two sentences.
- `apply-implementation-review.md` step 1 (OD-1, candidate (b) as a safety net):
  after step 0 (so after `enter_applying_review_feedback` on the step-0 route,
  for every governing version) and the binding check, and before the `BLOCK`
  pin, call the same helper. It is a no-op for every orchestrator that already
  committed the write, it commits step 0's own entry (`"1"`/`"2.1"` ordinary
  route and `"2.2"` late-problem route alike), and it
  repairs a crash between the persist and the commit, or between the staging and the commit (D-Helper step 4), so the dead end cannot
  be re-entered by any ordering of the texts.
- `review-plan.md` step 8, `record-manual-plan-review.md` step 7 and
  `apply-plan-review.md`: one sentence each, "plan-stage writes are not
  committed here; the plan-approval commit takes them" (D-Plan-Stage).

### D-Read-Strict: nothing on the read side changes (OD-1, OD-3)

Candidate (c) would have `bundle_generation_mismatch` and the provenance
interval tolerate a recognized state-only commit past the generation record.
It is rejected: it loosens two checks that several callers and the Controller
rely on, touches the protocol's `verify`/`next-action` outputs (INV-1 of
earlier releases is a byte-equality proof), and the written rule plus the
helper's refusal already remove the trap for anyone who follows the texts.

### D-Plan-Stage: checked, unchanged, written down (OD-4)

The plan stage has no generation-record commit and no phase-transition check,
and the plan-approval commit sweeps every earlier write, so there is nothing to
fix there. Committing a plan-stage REVISE would not help and would risk
`bundle_generation_mismatch` at the plan-approval gate. The cost is that a
plan-stage REVISE history lives only in the working tree until approval (a
`git checkout` loses it); that is the existing design, stated in the rule and
pinned by a test, not changed here.

### D-Downgrade: what 2.9.0 does with what 2.9.1 writes (OD-5)

2.9.1 accepts no commit shape that 2.9.0 refuses: the read side is unchanged
and the REVISE commit, like the step-0 entry commit for `"1"`/`"2.1"` items
(a state-only, `Workflow-Work-Item`-only commit before `P`, which the payload's
own tests already create by hand), is exactly the shape the Controller and the Manager
lane already create and 2.9.0 passes (a state-only commit carrying
`Workflow-Work-Item`, in the interval before the generation record). A state
or history written by 2.9.1 is read as legal by 2.9.0. A repository downgraded
to 2.9.0 keeps working but loses the new step: its command texts again
persist REVISE and the step-0 entry without committing, so the dead end returns for a person
following those texts (orchestrators that commit the write alone are
unaffected). The CLAUDE.md-style paragraph for the release notes:

> Workflow 2.9.1 changes command texts and adds one helper; it accepts no
> commit shape that 2.9.0 refuses, and writes none that 2.9.0 would refuse. A
> repository on 2.9.1 can be read and driven by 2.9.0. Moving back to 2.9.0
> restores the 2.9.0 command texts, which do not commit a REVISE write, so a
> person must commit it alone, before the fix commits, by hand.

Orchestration Protocol stays **1.2**: no action, decision, row or schema
changes. The protocol's `describe` reports the release string, which becomes
`2.9.1` (additive).

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | recommendation |
| --- | --- | --- |
| OD-1 | Fix shape: (a) the REVISE branches commit their own write alone, APPROVE stays uncommitted and is written down; (b) `/apply-*-review` commits a pending write alone before its first fix commit; (c) the generation and provenance checks tolerate a recognized state-only review-record commit | **(a) plus (b) as an idempotent safety net, through one helper.** (a) makes the review step durable; (b) costs one no-op call and covers a crash between persist and commit. Reject (c): it loosens the read side and is not cheap. |
| OD-2 | Helper in code, or the commit steps written only as prose git commands | **Helper.** Idempotence, the field allow-list and the APPROVE refusal are then testable instead of hoped for. |
| OD-3 | Remove the APPROVE trap beyond the written rule | **Written rule plus the helper's APPROVE refusal.** No new read-side hint; a hint changes `next-action` text and the equivalence proofs. |
| OD-4 | Plan stage: leave writes uncommitted, or commit REVISE there too | **Leave uncommitted**, write it down, pin it by a test. |
| OD-5 | Version and protocol | **2.9.1, protocol 1.2.** A patch: no new command, action or accepted shape. |

## 5. Checkpoints

Each checkpoint runs the payload's nine existing suites in a release-source
conformance fixture, and `workflow-manager verify .` on the checkout. Package
builds use the Manager venv `~/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv`.
The installation under `scripts/`, `.claude/` and `docs/ai-workflow/`'s managed
files is never edited.

**Conformance at a checkpoint (EPR-002).** `release.py stage-conformance`
exports a *committed* tree and `package.stage_conformance` verifies the
exported `manifest.json` digests before it builds the fixture, so a checkpoint
that changes payload bytes while the real manifest still carries 2.9.0's
digests (they are refreshed in CP5, which owns `manifest.json`) is refused;
exporting the unchanged base instead would test the old payload. CP1 to CP4
therefore stage a **scratch** release from the checkpoint's own commit and
refresh the digests in the scratch copy only:

1. `package.stage(repo, <checkpoint commit>, <scratch>/release)` with the
   venv's Python, the scratch directory empty and outside the repository.
2. A throw-away script kept outside the repository (never committed, not part
   of any protected path) rewrites `sha256` and `size` of every `artifacts`
   record of `<scratch>/release/manifest.json` from the bytes now on disk
   (and `executable` is read, not changed), so the scratch manifest describes
   exactly the checkpoint's payload; the repository's `manifest.json` is not
   touched.
3. `package.stage_conformance(<scratch>/release, <scratch>/fixture)` then the
   nine suites in that fixture. They run against the checkpoint's actual bytes.
4. CP5 does not use the scratch route: the committed `manifest.json` carries
   the real digests and the stock `release.py stage-conformance --commit <CP5
   commit>` is run, which also proves the digests are right. The scratch
   script's refreshed digests must equal CP5's committed ones for the same
   tree (a check, not an assumption).

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The committing helper: commit_pending_applying_review_feedback_entry, its field allow-list and its refusals | - | 3 | 1 |
| CP2 | Command texts: REVISE commits its own write, APPROVE is left uncommitted, /apply-implementation-review safety net, plan-stage wording | CP1 | 3 | 1 |
| CP3 | Regression tests: REVISE and APPROVE at both stages through the commit steps, already-committed REVISE, strict read side | CP1, CP2 | 3 | 1 |
| CP4 | Documentation: the written commit rule for review-stage writes, troubleshooting, operator reference | CP2 | 2 | 1 |
| CP5 | Release 2.9.1: manifest, release constant, roadmap and conformance | CP1, CP2, CP3, CP4 | 2 | 1 |

<!-- CP1 -->
### CP1 — The committing helper

**Files:**

- `payload/scripts/workflow_state.py`: `ReviewStageWriteNotCommittableError`,
  `REVIEW_STAGE_WRITE_COMMIT_FIELDS`, `commit_pending_applying_review_feedback_entry`
  per D-Helper.
- `payload/scripts/workflow_state_test.py`: unit tests in a disposable git
  repository: REVISE pending (local source, manual source, manual REVISE with
  an uncommitted local APPROVE ledger) commits alone with exactly the
  `Workflow-Work-Item` trailer as the final paragraph and the scoped staging;
  already committed returns `None`; nothing pending returns `None`; a `"2.1"`
  item (and a `"1"` item, where the fixture supports it) with HEAD at
  `AWAITING_EXTERNAL_…` and working `APPLYING_REVIEW_FEEDBACK` commits, while
  the same item with HEAD at `AWAITING_LOCAL_…` refuses (that phase is not in
  its set); the version-independent "no governing-version early return"
  is pinned by a test named for the step-0 entry, not the deferral; an APPROVE-shaped write refuses and commits nothing (a
  working phase other than `APPLYING_REVIEW_FEEDBACK` with HEAD at a review
  phase, e.g. HEAD `AWAITING_LOCAL_…` and working
  `AWAITING_MANUAL_EXTERNAL_…`, an uncommitted local APPROVE); HEAD at the
  terminal `AWAITING_EXTERNAL_…` with working `APPLYING_REVIEW_FEEDBACK`
  commits (the recovered source phase); a crash-left `technical_review_block_pins`
  entry refuses with the message naming the remedy; a
  stray field (`reviewed_implementation_head`) refuses; a dirty index refuses;
  foreign work-item residue is left uncommitted; **interrupted staging**
  (EPR-001): with another work item's uncommitted residue present, the helper
  is stopped after the scoped staging and before the commit (the commit step
  patched to raise), the index then holds only the target-only state blob and
  no entry commit exists; a retry recognizes the staged blob, commits exactly
  once, the committed state blob is the target-only one and the foreign
  residue is still in the working tree and absent from the commit; a further
  call returns `None` and creates no second commit; the same interruption with
  an *unrelated* staged path or a staged state blob that is not the target-only
  one still refuses with `DirtyIndexBeforeStagingError` and commits nothing; a
  case without foreign residue (plain `git add` interrupted) resumes too.

**Verification:** the new tests green; the nine suites green in the staged
fixture, staged by the procedure in section 5 ("Conformance at a checkpoint").

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Command texts

**Files:**

- `payload/.claude/commands/review-implementation.md` (A6, A7),
  `record-manual-implementation-review.md` (step 7, step 8),
  `apply-implementation-review.md` (step 1): D-Commands.
- `payload/.claude/commands/review-plan.md`, `record-manual-plan-review.md`,
  `apply-plan-review.md`: the plan-stage sentence.
- `payload/scripts/workflow_integration_test.py`: `_GOLDEN_COMMAND_FILE_SHA256`
  entries for the changed files; static conformance tests that each REVISE
  branch names the helper, each APPROVE branch says "uncommitted", the apply
  safety net precedes the `BLOCK` pin, and the plan texts carry the sentence.

In `apply-implementation-review.md` the only hunk in the version-shared step 1
is the helper call; the `"1"`/`"2.1"` dual-mode enumeration in step 0 stays
byte-unchanged.

**Verification:** the nine suites green; the 2.1 and 1 branches of the
changed commands are unchanged from 2.9.0 (apart from that one call), checked by a whole-file diff of
each changed command against its 2.9.0 bytes (read from the release tag
`v2.9.0`) whose only permitted hunks are the sentences and calls listed
above, so no branch needs delimiting inside a file.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Regression tests

**Files:** `payload/scripts/workflow_acceptance_matrix_test.py` (the item
fixtures and real generator are already there), driving each path through the
functions and commits the command texts name, in the texts' order:

1. Implementation, local REVISE: `record_local_implementation_review` then the
   helper, a fix commit, `record_bundle_generation` and its record commit;
   `validate_bundle_generation_record_commit` passes and the provenance
   interval is reachable.
2. Implementation, manual REVISE after an uncommitted local APPROVE: the same.
3. Implementation, both APPROVE left uncommitted: the gate is reachable and
   the technical-approval commit validates (`bundle_generation_mismatch`
   absent).
4. The trap, pinned: an APPROVE write committed alone raises
   `bundle_generation_mismatch` at the technical-approval gate (the strict read
   side, INV-1), and the helper refuses to commit it.
5. Idempotent: a REVISE write already committed (by a stand-in orchestrator)
   makes the helper return `None` and the same path still passes.
6. Crash case: a REVISE write persisted and never committed; the apply
   safety-net call repairs it before the first fix commit.
7. Plan stage, local REVISE then regeneration, local and manual APPROVE, all
   uncommitted, then plan approval: passes; a plan-stage write committed
   alone raises `bundle_generation_mismatch` at the plan-approval gate.
8. Step-0 late-problem entry from HEAD at `T` (`AWAITING_LOCAL_…`) with both
   APPROVE ledgers and the terminal phase uncommitted: step 0's
   `enter_applying_review_feedback`, the helper (it commits the ledgers and the
   move together), a fix commit, `record_bundle_generation` and its record
   commit; the record validates and the provenance interval is reachable.
9. The same entry from a HEAD that `/recover-implementation-provenance` left at
   `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`: the helper does not refuse and
   the path reaches a validating post-fix generation record, as in 2.9.0.
10. A `"2.1"` item (and a `"1"` item, if the fixture supports it) through the
    ordinary step-0 route: generation record `T` at `AWAITING_EXTERNAL_…`, step
    0's `enter_applying_review_feedback`, the helper (it commits the entry),
    a fix commit, `record_bundle_generation` and its record commit; the record
    validates and the provenance interval is reachable. Without the helper the
    same sequence is refused with the OPUS-R101-001 message (checked by
    removing the helper call), and the hand-inserted commit of the payload's
    existing tests is no longer needed.
11. Interrupted staging (EPR-001), end to end: foreign work-item residue in
    the working tree, a REVISE write persisted, the helper stopped after the
    scoped staging; the retry (the apply safety net) commits exactly once, the
    foreign residue stays uncommitted, a call after the commit returns `None`,
    and the path then reaches a validating post-fix generation record.
12. A helper-driven `same_content` round: the REVISE entry commit lands inside
    `P..T`, the post-fix record is `same_content`, and
    `validate_bundle_generation_record_commit` and the provenance interval
    classify the entry commit as implementation-stage excluded-only.
13. An already-committed REVISE with additional attribution trailers after
    `Workflow-Work-Item` and a subject unlike the helper's (the Controller's
    actual message shape, copied from its fixture or run evidence when
    available; otherwise a representative shape with a `Co-Authored-By`
    trailer): the helper returns `None` and the path still passes.
14. Plan stage, a manual plan REVISE (`record_manual_plan_review`), then the
    regeneration, a fresh local and manual APPROVE and the plan-approval
    commit: passes with every plan-stage write uncommitted.
15. The same as scenario 1 for a manual REVISE with an uncommitted local
    APPROVE ledger, through the interrupted-staging variant of scenario 11.

**Verification:** the scenarios that exercise the new commit (1, 2, 6, 8, 10, 11, 12, 13, 15) fail against 2.9.0's texts and code (checked by running
them with the helper removed) and pass now; the positive/unchanged scenarios
(3, 5, 9, and the plan-stage 7 and 14) already pass against 2.9.0 and are
regression pins, stated as such in the test names; scenario 4 pins the strict
read side, which also passes at 2.9.0.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Documentation

**Files:**

- `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`: the D-Rule table.
- `payload/docs/ai-workflow/IMPLEMENTATION_REVIEW_WORKFLOW.md`,
  `PLAN_REVIEW_WORKFLOW.md`, `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`: one
  paragraph each pointing at the rule (no governing-version list is quoted).
- `docs/common-problems.md`: "my REVISE round was refused with 'must always
  transition phase'" and the APPROVE counterpart, with the remedy, and the
  helper's refusal for a crash-left foreign field (commit the pin alone, then
  re-run).

**Verification:** `tools/docs/check_docs.py` clean; the operator-reference
tests green.

<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Release 2.9.1

**Files:** `manifest.json` (version `2.9.1`, every changed `sha256`/`size`,
`counts`, the derivation text; **committed before the bundle-generation
record**), `payload/scripts/workflow_protocol.py` (`WORKFLOW_RELEASE` `2.9.1`;
`PROTOCOL_VERSION` stays `1.2`), `docs/release-history.md`,
`docs/ROADMAP.md` (W4 marked Done at acceptance), `docs/ACTIVE_MILESTONE.md`.

**Verification:** `tools/release` tests and `package` build with the venv;
`workflow-manager verify .` clean. `tools/release/manager-pin.json` stays at
the current pin (1.5.0): this repository's installation stays 2.9.0, which that
Manager knows, and CI's `package` job verifies the staged 2.9.1 package with
`--release-dir`, so no Manager bump is needed (`docs/RELEASING.md` bumps the
pin only "when an installation update needs a newer Manager").

<!-- /CP5 -->

## 6. Tests and verification summary

CP1 unit tests, CP2 static conformance and golden hashes, CP3 end-to-end
disposable-repository scenarios (15 above), the nine existing suites unchanged
and green, `check_docs.py`, the release package build, and
`workflow-manager verify .`.

## 7. Release and follow-ups (owner actions, after acceptance)

Pull request titled `fix: ...`, squash merge, the `Release` workflow publishes
2.9.1 when `main`'s manifest names it; a Manager pin pull request in
`workflow-manager`; the Controller's installed copy follows by update.

## 8. Risks

- **The safety net refuses a route 2.9.0 accepts.** Closed by classifying on
  the working phase and the recovered-phase set (INV-6, CP3 scenarios 8, 9, 10).
- **A foreign orchestrator commits REVISE with a different message.** Handled:
  the helper keys on state, not on messages (INV-3).
- **The helper commits too much.** Bounded by the field allow-list, scoped
  staging and the empty-index check.
- **A later review round meets a REVISE commit in the provenance interval.**
  It is excluded-only; the Controller's rounds already pass this way
  (CP3 scenarios 1, 2).
- **Golden hashes and manifest digests drift.** CP2 and CP5 own them; the
  manifest is committed before the generation record.

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/review-stage-write-durability-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | Implementation stage: the REVISE branches of `/review-implementation` and `/record-manual-implementation-review` commit the write alone through the helper; APPROVE is left uncommitted and the texts say so | CP1, CP2 |
| REQ-2 | `/apply-implementation-review` commits a pending REVISE write, and its own step-0 entry for every governing version, alone before any fix commit or `BLOCK` pin, resumes an interrupted staging of that commit without a refusal, and does nothing when it is already committed | CP1, CP2 |
| REQ-3 | The plan stage and every other review-stage writer are checked; the result and rule are written down and pinned | CP2, CP3, CP4 |
| REQ-4 | Following the texts in order reaches the next gate for REVISE and APPROVE at both stages; the read side stays strict; the already-committed case works | CP3 |
| REQ-5 | The commit rule, the downgrade posture and the unchanged protocol version are written down | CP4, CP5 |
| REQ-6 | 2.9.1 is releasable | CP5 |

## 10. Artifact classification

`docs/ai-workflow/registry/review-stage-write-durability-artifacts.json` comes
from the `process` template and is fitted to this plan's footprint.

**Plan stage.** The protected paths are this plan document, the registry and
the mapping (every path this plan itself names is classified, including the
plan file). The template's exclusions apply, plus `manifest.json`,
`docs/RELEASING.md`, `docs/release-history.md`, `docs/common-problems.md` and
the prefixes `payload/`, `fixtures/`, `templates/` and `tools/`.
`docs/ROADMAP.md`, `docs/ACTIVE_MILESTONE.md`, `docs/ai-workflow/…` and the
installation's `scripts/` and `.claude/` are classified by the template. CP1
runs `classify_path` over every path in this document.

**Implementation stage.** Protected: `manifest.json`, `docs/RELEASING.md`,
`docs/release-history.md`, `docs/common-problems.md`, the prefixes `payload/`,
`fixtures/`, `templates/` and `tools/`, the installation prefixes
`.claude/commands/` and `scripts/` (never edited here; protecting them only
makes a stray edit visible to the technical approval), and the declarations
file's own path. `docs/ROADMAP.md` and `docs/ACTIVE_MILESTONE.md` stay
excluded as bookkeeping.

## 11. Review rounds and decisions

### Round 1 (LOCAL_MODEL_PLAN_REVIEW, REVISE, revision 1 to 2)

- **LPR-R1-001, accepted.** Verified: `enter_applying_review_feedback`
  accepts only `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`, and
  `bundle_generation_recovered_role_legal_committed_phases("2.2")` admits it.
  The helper now classifies by working phase and that set (D-Helper step 2,
  INV-6); D-Rule gains the step-0 entry row; INV-2 is reworded; the helper and
  commit subject are renamed neutrally
  (`commit_pending_applying_review_feedback_entry`, "record entry into
  `APPLYING_REVIEW_FEEDBACK`"); CP3 gains scenarios 8 and 9 and CP1 the
  recovered-source and uncommitted-local-APPROVE cases.
- **LPR-R1-002, accepted.** Section 2 names both the `base..P` and the
  `same_content` `P..T` case.
- **LPR-R1-003, accepted.** `tools/release/manager-pin.json` is 1.5.0 and
  `docs/RELEASING.md` bumps it only when an installation update needs a newer
  Manager; this repository's installation stays 2.9.0. The bump is dropped from
  CP5 and REQ-6's mapping text no longer says "a Manager that knows the
  release".
- **LPR-R1-004, accepted.** Section 2 distinguishes the commands that make a
  `git add -N` call from those that make none.
- **LPR-R1-005, accepted.** D-Helper step 3 and CP4 name the remedy (commit the
  pin alone, then re-run); CP1 tests the message.
- **Missing tests, accepted.** CP3 scenarios 8, 9; CP1 refusal for a working
  phase other than `APPLYING_REVIEW_FEEDBACK`; CP2's check is now a whole-file
  diff against `v2.9.0` limited to the expected hunks.
- **Maintainability note, accepted.** The helper reads the recovered-phase set
  from `bundle_generation_recovered_role_legal_committed_phases` and the table
  sits beside it.

### Round 2 (LOCAL_MODEL_PLAN_REVIEW, REVISE, revision 2 to 3)

- **LPR-R2-001, accepted (recommended alternative: cover it).** Verified:
  `enter_applying_review_feedback` is legal only from
  `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW` and persists without a commit for
  every version; `bundle_generation_target_phase` gives that phase to
  `"1"`/`"2.1"` records, and the ordinary-role `phase`-must-change check is
  version-independent; the three payload tests the reviewer names insert the
  missing commit by hand. Changes: the goal and a new paragraph, a section 2
  fact, INV-6 and D-Rule keyed by the item's own version, D-Helper step 1
  (the `"2.2"` early return is deleted) and step 2, D-Commands, D-Downgrade,
  CP1 cases, CP2's single-hunk statement, CP3 scenario 10 and REQ-2.
- **LPR-R2-002, accepted.** D-Helper step 2 no longer claims to know the writer;
  it infers it from the phase pair.
- **LPR-R2-003, accepted.** The D-Rule step-0 row states the two HEAD phases
  plainly (HEAD at `T` with the APPROVE writes uncommitted; HEAD at a
  recovered-role record), plus the `"1"`/`"2.1"` ordinary route.
- **Missing tests, accepted.** CP1 and CP3 scenario 10 cover the `"2.1"`/`"1"`
  step-0 route.

### Round 3 (MANUAL_EXTERNAL_PLAN_REVIEW, REVISE, revision 3 to 4)

- **EPR-001, accepted.** Verified in the source: `stage_scoped_state`
  (`payload/scripts/workflow_state.py`, the `already` check) raises
  `DirtyIndexBeforeStagingError` whenever the state path is staged and differs
  from `HEAD`, which is exactly the target-only blob it staged itself when
  foreign residue exists. D-Helper step 4 now recognizes that blob by
  recomputing it (a private function extracted from `stage_scoped_state`,
  behavior unchanged) and resumes at the commit; any other staged content
  still refuses. CP1 and CP3 (scenarios 11, 15) gain the interruption,
  retry and post-commit call.
- **EPR-002, accepted.** Verified: `release.py` `cmd_stage_conformance`
  exports a commit and `package.stage_conformance` calls `verify_release`,
  which refuses changed bytes with stale digests; the changed payload digests
  belong to CP5. Section 5 now specifies the scratch-manifest procedure for
  CP1-CP4 and the stock command for CP5; the installation stays untouched.
- **Optional 1, accepted.** The D-Rule step-0 row distinguishes the routes
  where the phase is unchanged from the recovered `"2.2"` HEAD that already
  transitions.
- **Optional 2, accepted.** REQ-2's description (here and in the mapping)
  names step-0 coverage and the resumable staging.
- **Optional 3, accepted.** CP3's verification names which scenarios fail
  against 2.9.0 and which are regression pins.
- **Missing tests, accepted.** Scenarios 11-15.
