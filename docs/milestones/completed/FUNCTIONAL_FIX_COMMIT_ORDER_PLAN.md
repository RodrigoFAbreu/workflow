# W6: Workflow 2.9.2 — a bounded functional fix commits in an order the next review accepts, and the trailer paragraph is stated plainly (Revision 1)

- **Work item:** `functional-fix-commit-order` (`process`, governing version `2.2`)
- **Roadmap step:** W6 (`docs/ROADMAP.md`), a small fix release placed before W5, which is paused at its plan review and resumes after this release.
- **Branch:** `milestone/functional-fix-commit-order`
- **Base commit:** `04d155a` (the release source is Workflow 2.9.1, which this repository's own installation also runs, with automatic gates and no `GATE_POLICY.json`)
- **Plan revision:** 1
- **Issues:** RodrigoFAbreu/workflow#19 (main) and RodrigoFAbreu/workflow#20.

## 1. Goal

Ship Workflow 2.9.2, a patch release (a bug fix, so a `fix:` title), after
which following `/apply-functional-review`'s text in order gets a bounded
functional fix with a checklist change to the next implementation review
with no orchestrator rule that the text leaves out, and after which the
trailer-paragraph rule (`OPUS-R129-001`) can no longer be read in a way
that the generation-record check refuses.

- **#19, the checklist commit after the record.** The bounded branch's
  sub-step 4 regenerates the bundle and commits the post-fix
  `Workflow-Bundle-Generation-Record` (`T`), then sub-step 5 stops the round
  ("Do not proceed to step 6/7"). Step 6, the checklist update in
  `docs/ACTIVE_MILESTONE.md`, therefore either never happens or happens
  after `T`. A commit after `T` moves `HEAD` past the bundle's
  `generation_head`, so the next local implementation review stops with
  `bundle_generation_mismatch` (protocol row 25a, `blocked`). The only
  remedy is the user-only `/recover-implementation-provenance`, which also
  changes the `bundle_id`. Every bounded functional fix then needs a person.
  The Controller lane hit it on 2026-10-10 (work item C8); the Manager lane
  avoided it only by committing the checklist before `T`.
- **A second unwritten rule in the same branch, found while planning.**
  Sub-step 1 persists `mark_technical_approval_stale` "on disk before any
  edit" but never commits it, and sub-step 3 commits "the fix". If the fix
  commit stages only the fix, as the text reads, the post-fix record commit
  sweeps the `STALE` write up, and `validate_bundle_generation_record_commit`
  refuses it: `technical_approval` is not in
  `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS` (reproduced for both item types
  in a disposable repository, section 2). The payload's own tests hide the gap:
  the acceptance matrix's `Item.mark_technical_approval_stale` commits the
  write by hand. `/apply-pr-review` already makes exactly this commit
  (its "Durable ordering" step 2, `LPR-R4-001`); `/apply-functional-review`
  does not.
- **#20, the trailer paragraph.** Every generation-record command says its
  trailers "must be the commit message's own final paragraph — after any
  `Co-Authored-By:`/`Claude-Session:` lines, never before them". That reads
  as "in the same paragraph, after them", and the payload's own
  trailer-shape tests call that layout the corrected one. Git then parses
  `Co-Authored-By` as a trailer, and `_bundle_generation_record_role` (an
  exact set comparison) refuses the commit: "carries trailer set
  [... 'Co-Authored-By' ...], not exactly the ordinary ... or the recovered
  ... set". The Controller lane hit it while recovering C8.

### Hard requirements (invariants)

- **INV-1, the read side stays strict.** No generation, provenance or
  gate-reachability check accepts a commit shape it refused in 2.9.1:
  `assert_local_generation_matches`, `verify_implementation_provenance_interval`,
  `_bundle_generation_record_role` and `validate_bundle_generation_record_commit`
  accept exactly what they accept today. The only read-side code change is
  one sentence added to one refusal message (D-Trailers).
- **INV-2, the generation record is the last commit of its invocation.**
  Nothing the command texts instruct is committed after `T` in the same
  invocation; work that must be committed in a bounded round is committed
  before the regeneration.
- **INV-3, compatible with existing orchestrators.** The order the Manager
  lane uses (checklist committed before `T`) keeps working, and so does a
  fix commit that carries the stale write (the payload tests' shape). The
  new commit of the stale write is skipped when there is nothing to commit.
- **INV-4, additive, no new state.** No new state field, no new commit
  shape (the stale-write commit is `/apply-pr-review`'s existing plain
  state-only commit), and the Orchestration Protocol stays 1.2. See
  D-Downgrade.

### Non-goals

- Loosening any read-side check, including the trailer-set check (OD-2).
- Having `/apply-functional-review` fold a post-record commit into a
  recovered-role record by itself (OD-1).
- Changing what `/recover-implementation-provenance` does, beyond the
  wording of its step 5.
- Editing this repository's installation (`scripts/`, `.claude/`,
  `docs/ai-workflow/`'s managed files, the managed blocks); it stays
  Workflow 2.9.1 and `workflow-manager verify .` stays clean.
- Publishing, pushing, pinning in `workflow-manager`, or changing the
  Controller or the Manager.

## 2. What exists today (facts this plan relies on)

All of this was read in the release source (`payload/`), not the
installation, at `04d155a`.

- **`/apply-functional-review`'s bounded branch**
  (`payload/.claude/commands/apply-functional-review.md`, step 4, replaced
  for state-tracked items). Sub-step 1 persists
  `mark_technical_approval_stale` and does not commit it. Sub-step 2 makes
  the fix, sub-step 3 commits it ("one coherent commit"). Sub-step 4 resolves
  the outcome, calls `record_bundle_generation(stage="post-fix")`, commits
  the state file alone with the record trailers, refreshes the two author
  lines and runs `prepare-ai-review.sh`. Sub-step 5 marks
  `FUNCTIONAL_REVIEW.md` consumed and stops ("Do not proceed to step 6/7 in
  this same invocation"). Top-level step 5 commits "no code change" fixes
  and step 6 updates the checklist in `docs/ACTIVE_MILESTONE.md`, both after
  step 4. The text does not say whether sub-step 4 runs once per finding or
  once per round; a second `record_bundle_generation` from
  `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` (or the terminal phase) is not a
  legal post-fix source, so in practice it is once per round.
- **What refuses a commit after `T`.** `assert_local_generation_matches`
  (`workflow_fingerprint.py`) compares `MANIFEST.md`'s `generation_head` with
  `HEAD`; `/review-implementation` runs it first, and the protocol's row 25a
  reports `blocked` with `bundle_generation_mismatch` and the alternative
  `implementation.recover_provenance`. Reproduced (a probe built on the
  acceptance-matrix harness, kept outside the repository): a
  `docs/`-only commit after the post-fix record makes the next approval
  refuse with `WorktreeOrHeadMismatchError`; the same commit before the
  record passes.
- **What refuses an uncommitted stale write.** The ordinary role's allow-list
  `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS` (`workflow_state.py`) is `phase`,
  `reviewed_implementation_head`, `implementation_revision`,
  `state_revision`, `last_transition`, `implementation_review_stages`,
  `gate_evidence`, `reopenings`; the recovered role's set is narrower.
  Reproduced: with the stale write persisted and not committed and a fix
  commit that stages only the fix, `validate_bundle_generation_record_commit`
  refuses the record ("field changes are [..., 'technical_approval'], not a
  non-empty subset of ..."), for a `process` and a `product` item.
  `mark_technical_approval_stale` may run again on an already `STALE`
  record (it bumps `state_revision` and `last_transition` only).
- **Where the stale write is already committed.** `/apply-pr-review` step 2,
  "Durable ordering of every branch that stales", commits it as "a plain
  state-only commit of that state, with no trailer" through
  `stage_scoped_state`, before the fix commit, because "the
  generation-record validators do not admit `technical_approval`".
- **A checklist commit before `T` is safe.** The `process` and `product`
  templates of `generate_artifacts_declarations` both exclude
  `docs/ACTIVE_MILESTONE.md` at the implementation stage. Before `T`, such a
  commit lands in `base..P` for the `ordinary` outcome
  (`record_bundle_generation` sets `P = reviewed_implementation_head` to the
  `HEAD` it is given), and inside `P..T` for the `same_content` outcome,
  where every non-terminal commit must classify implementation-stage
  excluded-only, which it does. The broad branch's
  `create_remediation_child_work_item` writes only the new child's entry
  (another work item's residue, which `stage_scoped_state` keeps out of the
  parent's record commit), and `mark_functional_review_consumed` writes a
  marker under the ignored `.ai-review/`, so neither needs a commit.
- **The other generation-record writers.** `/milestone-implement` updates
  the narrative record inside each checkpoint commit (step 1/1e), before step
  4's record, and step 5 reports and stops. `/apply-implementation-review`
  writes rejections into `<bundle_dir>/IMPLEMENTATION_SUMMARY.md` (not
  committed) and step 8 reports and stops. `/apply-pr-review` commits the
  stale write, the fix, then the record, and stops; its "no code change"
  branch writes a note but runs no generation. `/recover-implementation-provenance`
  commits the recovered-role record, regenerates, reports and stops. None of
  them instructs a commit after its record; only `/apply-functional-review`
  has the trap.
- **The trailer rule.** `OPUS-R129-001` is stated in 14 payload commands:
  `accept-milestone`, `adopt-gate-policy`, `apply-functional-review`,
  `apply-implementation-review`, `apply-pr-review`, `approve-review`,
  `bootstrap-workflow-v2`, `milestone-implement`, `prepare-functional-review`,
  `recover-implementation-provenance`, `request-plan-amendment`,
  `resume-implementation`, `retire-legacy-work-item`, `satisfy-gate`.
  `_commit_trailers` parses the message's last paragraph with
  `git interpret-trailers --parse`. Only `_bundle_generation_record_role`
  compares the whole trailer set; every other validator (checkpoint, plan
  and technical approval, functional checklist, retirement, resume, gate
  policy) reads its own keys and ignores others, so a `Co-Authored-By` in
  their final paragraph is harmless. `workflow_integration_test.py`'s
  `TestAcceptMilestoneCompletionCommitTrailerShape` and
  `TestBaselinePortabilityCommandsCommitTrailerShape` pin the same-paragraph
  layout as "corrected" and check only that Git parses the keys, never the
  role; several of its tests pin the current wording by literal substring.
- **A refused record is a dead end for the commands.** Probed: a
  recovered-role commit with `Co-Authored-By:` in its trailer paragraph is
  refused by `validate_bundle_generation_record_commit`, yet discovery still
  takes it as the current record, so a second `/recover-implementation-provenance`
  stops with `ImplementationProvenanceRecoveryNotApplicableError` ("nothing to
  recover"). The same commit in D-Trailers' layout validates. The only way
  out is to rewrite that one commit's message while it is still `HEAD` and
  unpublished.
- **Release mechanics.** `_GOLDEN_COMMAND_FILE_SHA256`
  (`workflow_integration_test.py`) pins command-file hashes; `manifest.json`
  carries every payload digest and the release string; `WORKFLOW_RELEASE`
  (`workflow_protocol.py`) is `2.9.1`, `PROTOCOL_VERSION` is `1.2`;
  `ORCHESTRATION_PROTOCOL.md` lists the tested releases and
  `workflow_protocol_test.py` pins the release string.
  `tools/release/manager-pin.json` names Manager 1.7.0.

## 3. Design decisions

### D-Order: the bounded branch's commit order (OD-1, OD-3)

The bounded branch commits, in this order, and nothing after the record:

1. **Sub-step 1, the stale write, committed alone.** After persisting
   `mark_technical_approval_stale`, commit the state file alone, exactly as
   `/apply-pr-review`'s step 2 does: `stage_scoped_state(repo_root, <id>)`
   (or the single-path `git add` when it returns `False`), a plain
   state-only commit with no trailer. When the staging leaves nothing staged
   (`git diff --cached --quiet`: an orchestrator committed the write, or this
   is a re-run), there is nothing to commit and the step does nothing. This is
   still "before any edit": the commit follows the persist and precedes the
   first source or test edit.
2. **Sub-steps 2 and 3, the fix, as today**, repeated for each bounded
   finding of the round (each starts with sub-step 1 again; a second stale
   write is legal and is committed the same way).
3. **New, before the regeneration: steps 5 and 6 for the whole round.**
   Commit the "no code change" fixes (step 5) and the checklist update in
   `docs/ACTIVE_MILESTONE.md` (step 6: what changed, any deferral to a
   remediation child by id, what needs re-testing). This is the last
   ordinary commit of the round.
4. **Sub-step 4, the regeneration, once per round**, after the last fix and
   the checklist commit. Its record commit `T` is the last commit of the
   invocation. The text says so: "No commit may follow this record in this
   invocation; anything still to commit belongs before it." What turns up
   after `T` belongs to the next round, or to
   `/recover-implementation-provenance` when it is excluded-only.
5. **Sub-step 5, as today**: mark consumed, report and stop. Top-level steps
   5 and 6 say that in a round where a finding took the bounded branch they
   already ran inside it, before the regeneration, and are not repeated.

The sub-step numbering of the bounded branch stays 1 to 5: the new work is
a paragraph at the end of sub-step 3, so `/apply-pr-review`'s reference to
"`/apply-functional-review`'s bounded branch step 4" stays true.

### D-Last-Commit: one rule for every generation-record writer (OD-4)

Written once in `REVIEW_PROTOCOL.md`: **a generation record is the last
commit of the invocation that writes it.** Every commit a round needs (fix,
narrative, checklist, a stale or review-stage state write) lands before the
record; the read side refuses anything after it (`bundle_generation_mismatch`)
and only `/recover-implementation-provenance` repairs that.
`/milestone-implement`, `/apply-implementation-review`, `/apply-pr-review`
and `/recover-implementation-provenance` already comply (section 2) and
their texts are not changed for #19.

### D-Trailers: the trailer paragraph, stated plainly (OD-2)

Every statement of `OPUS-R129-001`, in all 14 commands, says the same thing
in the same words: **the `Workflow-*` trailers the step names form the
message's final paragraph, and nothing else is in it; any
`Co-Authored-By:`/`Claude-Session:` lines go in their own paragraph before
it, separated by a blank line.** The reason clause stays (Git parses only the
last paragraph), and for the six generation-record writers
(`milestone-implement` step 4, `bootstrap-workflow-v2` step 3's
no-checkpoint branch, `apply-implementation-review` step 7,
`apply-functional-review` sub-step 4, `apply-pr-review`'s durable-ordering
item 4, `recover-implementation-provenance` step 5) one
more clause says why it is required there: the record's trailer set is
checked exactly, so a `Co-Authored-By:` line in that paragraph is refused.

The read side stays strict. One refusal message changes:
`validate_bundle_generation_record_commit`'s trailer-set refusal gains one
sentence naming the cause and the remedy ("every line of the final paragraph
counts: put `Co-Authored-By:`/`Claude-Session:` lines in an earlier
paragraph; while this commit is still the unpublished `HEAD`, rewrite its
message, because a later recovery cannot supersede it"). The exception class, the accepted sets and every other message
are unchanged.

For the commands whose validator reads only its own keys, the new wording
is stricter than they need, and harmless: a commit in the old same-paragraph
layout still validates there, so nothing already written is invalidated.
The two trailer-shape test classes are updated to the new layout and gain
the role check that was missing (see CP2).

### D-Downgrade: what 2.9.1 does with what 2.9.2 writes (OD-5)

2.9.2 adds no state field, no commit shape and no protocol change. The
stale-write commit is `/apply-pr-review`'s plain state-only commit, which
2.8.0 onward already makes and reads; a checklist commit before the record
is the Manager lane's existing order; a trailer paragraph without
`Co-Authored-By` is the shape every check has always accepted. The
CLAUDE.md-style paragraph for the release notes:

> Workflow 2.9.2 changes command texts and one refusal message. It adds no
> state, no commit shape and no protocol change: it accepts no commit that
> 2.9.1 refuses and writes none that 2.9.1 would refuse, so a repository on
> 2.9.2 can be read and driven by 2.9.1. Moving back to 2.9.1 restores its
> bounded functional-fix text, which leaves the stale technical-approval
> write uncommitted and updates the checklist after the generation record:
> a person or an orchestrator following it must commit the stale write
> alone before the first fix edit and commit the checklist before the
> regeneration, and must keep `Co-Authored-By:`/`Claude-Session:` lines
> out of a generation record's final paragraph, by hand.

Orchestration Protocol stays **1.2**: no action, decision, row or schema
changes. `describe` reports the release string, which becomes `2.9.2`
(additive).

## 4. Open decisions (for the plan reviewer and the user)

| id | decision | recommendation |
| --- | --- | --- |
| OD-1 | #19 fix shape: (a) reorder the text so the stale write, narrative and checklist are committed before the one regeneration and nothing follows the record; (b) let the command fold its own post-record excluded-only commit into a recovered-role record; (c) let the read side tolerate an excluded-only commit past `T` | **(a).** It needs no code, matches the Manager lane's order, and keeps the read side strict. (b) adds a code path and changes the `bundle_id` every round, staling verdicts; (c) loosens the read side, and 2.9.1 would refuse what 2.9.2 accepts. |
| OD-2 | #20 fix: (a) make the wording explicit in every statement of `OPUS-R129-001` and name the cause in the refusal message; (b) have the trailer-set check ignore `Co-Authored-By` and `Claude-Session` | **(a), read side strict.** (b) makes 2.9.1 refuse records 2.9.2 accepts. One trap remains that wording cannot remove: tooling that appends trailers to the last paragraph by itself (a `commit-msg` hook, `git commit --trailer` or `-s`). No lane reported it; the refusal message now names the cause and the remedy (section 2: rewrite the refused commit's message while it is still the unpublished `HEAD`). Revisit (b) only if a real lane needs it. |
| OD-3 | The stale-write commit's shape: plain, no trailer (as `/apply-pr-review` step 2) or with `Workflow-Work-Item` | **Plain, no trailer**: one shape for the same write in both commands. |
| OD-4 | Change the other generation-record writers' texts for #19 | **No.** None instructs a commit after its record (section 2); the rule is written once in `REVIEW_PROTOCOL.md` (D-Last-Commit). Their texts change only for #20's wording. |
| OD-5 | Version, protocol and Manager pin | **2.9.2, protocol 1.2, `manager-pin.json` stays at 1.7.0.** A patch with no new command, action or accepted shape. The installation stays 2.9.1, which Manager 1.7.0 knows, and CI's `package` job verifies the staged 2.9.2 package with `--release-dir`. |

## 5. Checkpoints

Each checkpoint runs the payload's nine existing suites in a release-source
conformance fixture, and `workflow-manager verify .` on the checkout. Package
builds use the Manager venv
`~/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv`.
The installation under `scripts/`, `.claude/` and `docs/ai-workflow/`'s
managed files is never edited.

**Conformance at a checkpoint (as in W4, EPR-002).** `release.py
stage-conformance` verifies the exported `manifest.json` digests, which keep
2.9.1's values until CP5. CP1 to CP4 therefore stage a **scratch** release
from the checkpoint's own commit and refresh the digests in the scratch copy
only:

1. `package.stage(repo, <checkpoint commit>, <scratch>/release)` with the
   venv's Python, the scratch directory empty and outside the repository.
2. A throw-away script kept outside the repository rewrites `sha256` and
   `size` of every `artifacts` record of `<scratch>/release/manifest.json`
   from the bytes on disk (`executable` is read, not changed); the
   repository's `manifest.json` is not touched.
3. `package.stage_conformance(<scratch>/release, <scratch>/fixture)`, then
   the nine suites in that fixture.
4. CP5 uses the stock `release.py stage-conformance --commit <CP5 commit>`;
   the scratch script's digests must equal CP5's committed ones for the same
   tree.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Bounded functional fix: the stale write and the checklist are committed before the regeneration, and the generation record is the round's last commit | - | 2 | 1 |
| CP2 | Trailer paragraph wording (OPUS-R129-001) made explicit in every command, and the generation-record refusal names the cause | - | 2 | 1 |
| CP3 | Regression tests: a bounded functional fix with a checklist change through the command's own commits to the next review, compatible orders, the trap pins and a recovery commit | CP1, CP2 | 3 | 1 |
| CP4 | Documentation: the last-commit rule, the trailer paragraph, troubleshooting | CP1, CP2 | 2 | 1 |
| CP5 | Release 2.9.2: manifest, release constant, roadmap and conformance | CP1, CP2, CP3, CP4 | 2 | 1 |

<!-- CP1 -->
### CP1 — The bounded branch's commit order

**Files:**

- `payload/.claude/commands/apply-functional-review.md`: D-Order. Sub-step 1
  gains the stale-write commit (with its "nothing to commit" case);
  sub-step 3 gains the closing paragraph that runs steps 5 and 6 for the
  whole round before the regeneration; sub-step 4 says it runs once per
  round and that no commit follows its record; top-level steps 5 and 6 say
  they already ran in a bounded round. The trailer sentence in sub-step 4 is
  CP2's, not this checkpoint's.
- `payload/scripts/workflow_integration_test.py`: the golden hash of
  `apply-functional-review.md`; a static conformance test
  (`TestFunctionalFixCommitOrderConformance`) that, in the bounded branch,
  sub-step 1 names the state-only commit and `stage_scoped_state`, the
  steps-5-and-6 paragraph precedes `record_bundle_generation`, the
  "No commit may follow" sentence is present, and top-level steps 5 and 6
  carry the bounded-round sentence; the comment that names "the bounded
  branch's step 5" stays correct.

**Verification:** the new tests green; the nine suites green in the scratch
fixture; a whole-file diff of `apply-functional-review.md` against the
`v2.9.1` tag shows only the hunks listed here.

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — The trailer paragraph

**Files:**

- The 14 payload commands that state `OPUS-R129-001` (section 2): D-Trailers'
  one wording, plus the generation-record clause in the six record writers.
  Nothing else in those files changes.
- `payload/scripts/workflow_state.py`: one sentence appended to
  `validate_bundle_generation_record_commit`'s trailer-set refusal message.
- `payload/scripts/workflow_integration_test.py`: the golden hashes of the
  changed commands; the literal-substring tests that pin the old wording
  move to the new one; `TestAcceptMilestoneCompletionCommitTrailerShape` and
  `TestBaselinePortabilityCommandsCommitTrailerShape` describe and build the
  new layout (the `Co-Authored-By`/`Claude-Session` paragraph before the
  trailer paragraph), and for the generation-record family additionally
  assert `_bundle_generation_record_role` returns `"ordinary"`/`"recovered"`
  for the new layout and `None` for the same-paragraph layout (the missing
  check that let #20 through); a static test that every payload command
  stating `OPUS-R129-001` carries the new wording and none carries the old
  phrase "after any `Co-Authored-By:`/`Claude-Session:` lines, never before
  them" without it.
- `payload/scripts/workflow_state_test.py`: the refusal message names the
  remedy; the accepted sets are unchanged (a same-paragraph
  `Co-Authored-By` still refuses).

**Verification:** the nine suites green in the scratch fixture; a whole-file
diff of each changed command against `v2.9.1` shows only the trailer
sentences.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Regression tests

**Files:** `payload/scripts/workflow_acceptance_matrix_test.py`: new classes
`FunctionalFixCommitOrderProcess` and `FunctionalFixCommitOrderProduct`,
driving each path through the functions and commits the command texts name,
in the texts' order. They do not use `Item.mark_technical_approval_stale`'s
built-in commit: the stale write is persisted with `state_transaction` and
committed by the test the way sub-step 1 now says, so the test follows the
text and not the harness. Generation-record and recovery commits are written
in D-Trailers' layout, with a `Co-Authored-By`/`Claude-Session` paragraph
before the trailers.

1. **The issue's case, `"2.2"`.** Technical approval, functional review with
   one finding, sub-step 1 (persist and commit the stale write), a fix commit
   that stages only the fix, a checklist edit of `docs/ACTIVE_MILESTONE.md`
   committed, the regeneration (record commit, then `prepare-ai-review.sh`).
   Then the next review: `assert_local_generation_matches` passes,
   `next-action` at `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` does not take row
   25a, and the local and manual `APPROVE` and the technical approval reach
   `AWAITING_FUNCTIONAL_REVIEW`.
2. The same for a `"2.1"` item (one implementation-review stage): the next
   stop, technical approval, is reachable and validates.
3. `same_content`: a bounded fix reverted before the regeneration, so only
   the stale write and the checklist commit are new; the record is
   recovered-role, validates, and the next review passes.
4. Two bounded findings in one round: two stale-write commits and two fix
   commits, one checklist commit, one regeneration; validates and the next
   review passes.
5. Mixed round: a broad finding (child created, its entry left uncommitted)
   and a bounded finding; the parent's record commit, staged with
   `stage_scoped_state`, validates without the child's entry, and the next
   review passes.
6. **Compatibility pins (INV-3), passing at 2.9.1 too:** the Manager lane's
   order (stale write carried in the fix commit, checklist committed before
   the record) passes; sub-step 1's commit is a no-op when the stale write is
   already committed (no extra commit is created).
7. **Trap pins (INV-1), the 2.9.1 text order:** a checklist commit after the
   record makes the next review refuse with `bundle_generation_mismatch`
   (row 25a, `blocked`); a stale write left uncommitted with a fix-only
   commit makes `validate_bundle_generation_record_commit` refuse the record.
8. **Recovery (#20).** From the trap state of scenario 7's first half,
   `/recover-implementation-provenance`'s steps with a commit message in
   D-Trailers' layout: the recovered-role commit validates, the provenance
   interval is reachable, and the next review passes after the
   regeneration. The same message with `Co-Authored-By:` inside the trailer
   paragraph is refused and the message names the remedy; rewriting that
   commit's message (same tree, D-Trailers' layout) then validates and the
   next review passes. The same pair for an ordinary post-fix record.

**Verification:** scenarios 1 to 5 and 8 pass; they fail against 2.9.1's
order (shown by scenario 7, which reproduces that order); 6 and 7 are
regression pins and say so in their names. The nine suites stay green in the
scratch fixture.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Documentation

**Files:**

- `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`: a short section after
  "Which review-stage writes are committed": D-Last-Commit (with the bounded
  functional fix's order as its example) and D-Trailers' paragraph rule.
- `payload/docs/ai-workflow/MILESTONE_WORKFLOW.md` and
  `WORKFLOW_V2_1_OPERATOR_REFERENCE.md`: the bounded-fix descriptions name the
  order (stale write committed, fix, checklist, then the regeneration, last).
  No governing-version list is quoted.
- `docs/common-problems.md`: "The next review stops with
  bundle_generation_mismatch after a functional fix" (cause: a commit after
  the record; prevention on 2.9.2 and by hand on 2.9.1; remedy
  `/recover-implementation-provenance` and its cost), and "A generation
  record is refused for its trailer set" (cause: `Co-Authored-By` in the
  trailer paragraph; remedy, as CP3 scenario 8 proves it: rewrite the
  refused commit's message while it is still the unpublished `HEAD`, since a
  later recovery cannot supersede it; once it is published or built on, ask
  the repository owner).

**Verification:** `tools/docs/check_docs.py` clean; the operator-reference
and protocol tests green in the scratch fixture.

<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Release 2.9.2

**Files:** `manifest.json` (version `2.9.2`, every changed `sha256`/`size`,
`counts`, the derivation text; **committed before the bundle-generation
record**), `payload/scripts/workflow_protocol.py` (`WORKFLOW_RELEASE`
`2.9.2`; `PROTOCOL_VERSION` stays `1.2`),
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (2.9.2 among the tested
releases, protocol 1.2), `payload/scripts/workflow_protocol_test.py` (the
release pin), `docs/release-history.md` (the 2.9.2 row, with D-Downgrade's
paragraph), `docs/ROADMAP.md` (W6 marked Done at acceptance),
`docs/ACTIVE_MILESTONE.md`.

**Verification:** `tools/release` tests and the `package` build with the
venv; the stock `release.py stage-conformance --commit <CP5 commit>` and the
nine suites; `workflow-manager verify .` clean. `tools/release/manager-pin.json`
is not changed (OD-5).

<!-- /CP5 -->

## 6. Tests and verification summary

CP1 and CP2 static conformance and golden hashes, the CP2 unit tests, the
CP3 end-to-end scenarios (8 above, for both item types), the nine existing
suites unchanged and green, `check_docs.py`, the release package build, and
`workflow-manager verify .`.

## 7. Release and follow-ups (owner actions, after acceptance)

Pull request titled `fix: ...`, squash merge, the `Release` workflow
publishes 2.9.2 when `main`'s manifest names it; a Manager pin pull request in
`workflow-manager`; the Controller's installed copy follows by update. Then
W5 resumes at its plan review.

## 8. Risks

- **An orchestrator relies on the old order.** None known: committing the
  checklist after the record never worked, and an orchestrator that commits
  the stale write with its fix commit still passes (CP3 scenario 6).
- **The stale-write commit lands where a check does not expect it.** It lands
  before the fix, in `base..P`, where the state file is excluded at the
  implementation stage; `/apply-pr-review` has made the same commit since
  2.8.0.
- **The wording change breaks a literal-substring test or a golden hash.**
  CP2 owns both.
- **W5 touches the same command files.** W5 is paused before implementation;
  it rebases its plan on 2.9.2 when it resumes.
- **A tool appends trailers to the last paragraph by itself.** Not fixed by
  wording (OD-2); the refusal message names it.

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/functional-fix-commit-order-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | `/apply-functional-review`'s bounded branch, followed in order, works with no hidden orchestrator rule: the stale write is committed alone before the first edit, the narrative and checklist commits come before the one regeneration of the round, and nothing is committed after the record | CP1, CP3 |
| REQ-2 | Every other generation-record writer is checked for the same trap; the result and the rule are written down once | CP1, CP4 |
| REQ-3 | #20: every statement of `OPUS-R129-001` puts `Co-Authored-By`/`Claude-Session` in an earlier paragraph; the trailer-set refusal names the cause; the read side stays strict | CP2, CP3 |
| REQ-4 | Orchestrators that already commit the checklist before the record, or carry the stale write in the fix commit, keep working | CP3 |
| REQ-5 | Regression tests drive a bounded functional fix with a checklist change through the command's own commits to the next review, for both item types and both review shapes, pin both traps, and validate a recovery commit in the corrected layout | CP3 |
| REQ-6 | The rules, the downgrade posture and the unchanged protocol version are written down | CP4, CP5 |
| REQ-7 | 2.9.2 is releasable | CP5 |

## 10. Artifact classification

`docs/ai-workflow/registry/functional-fix-commit-order-artifacts.json` comes
from the `process` template and is fitted to this plan's footprint, the same
fit as W4's.

**Plan stage.** Protected: this plan document, the registry and the mapping.
The template's exclusions apply (they cover `docs/ROADMAP.md`,
`docs/ACTIVE_MILESTONE.md`, `docs/ai-workflow/`, `CLAUDE.md` and the
installation's `scripts/` and `.claude/`), plus `manifest.json`,
`docs/RELEASING.md`, `docs/release-history.md`, `docs/common-problems.md` and
the prefixes `payload/`, `fixtures/`, `templates/` and `tools/`. Every path
this document names was run through `classify_path` at both stages while
planning; none is unclassified.

**Implementation stage.** Protected: `manifest.json`, `docs/RELEASING.md`,
`docs/release-history.md`, `docs/common-problems.md`, the prefixes
`payload/`, `fixtures/`, `templates/` and `tools/`, the installation
prefixes `.claude/commands/` and `scripts/` (never edited here; protecting
them only makes a stray edit visible to the technical approval), and the
declarations file's own path. `docs/ROADMAP.md` and `docs/ACTIVE_MILESTONE.md`
stay excluded as bookkeeping.

## 11. Review rounds and decisions

None yet.
