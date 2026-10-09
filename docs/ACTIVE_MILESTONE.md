# Active Milestone

## Milestone

**Implementation self-review** (`SELF_REVIEWING_IMPLEMENTATION`). W4: `review-stage-write-durability`
(`process`, governing version `2.2`), branch
`milestone/review-stage-write-durability`, base `576dfd5` (the release source is
Workflow 2.9.0; this repository's own installation is also 2.9.0 with automatic
gates and no `GATE_POLICY.json`). The plan is
`docs/ai-workflow/REVIEW_STAGE_WRITE_DURABILITY_PLAN.md` (revision 4, approved). The
previous milestone, W3 (`legacy-retire-and-default-version`, Workflow 2.9.0),
is complete.

## Goal

Workflow 2.9.1, a patch release that fixes
[RodrigoFAbreu/workflow#13](https://github.com/RodrigoFAbreu/workflow/issues/13):

1. **REVISE.** A review stage that returns REVISE persists its phase write and
   never commits it; `/apply-implementation-review`'s post-fix
   generation-record commit then picks it up, shows no `phase` change and is
   refused ("must always transition phase", OPUS-R101-001). The REVISE branches
   of `/review-implementation` and `/record-manual-implementation-review`
   commit their write alone (a `Workflow-Work-Item` trailer), and
   `/apply-implementation-review` commits a still-pending one before its first
   fix commit, doing nothing when an orchestrator already committed it.
2. **APPROVE.** The opposite rule is written down: an APPROVE write is never
   committed on its own, because HEAD past the generation record makes
   `/satisfy-gate` and `/approve-review` refuse (`bundle_generation_mismatch`).
3. **Plan stage.** Checked for the same gap; none (no generation-record
   commit), so its rule (writes stay uncommitted until the plan-approval
   commit) is written down and tested.

The read side stays strict, the Orchestration Protocol stays 1.2, and 2.9.1
accepts no commit shape 2.9.0 refuses.

## Current checkpoint

**Implementation self-review** (`SELF_REVIEWING_IMPLEMENTATION`). CP1 to CP5 are complete. CP1:
`payload/scripts/workflow_state.py` gains
`commit_pending_applying_review_feedback_entry`,
`REVIEW_STAGE_WRITE_COMMIT_FIELDS` and `ReviewStageWriteNotCommittableError`
(the scoped-state construction is extracted from `stage_scoped_state` into
`_scoped_state_from`, behavior unchanged), with 15 unit tests. CP2: the REVISE
branches of `review-implementation.md` (A6) and
`record-manual-implementation-review.md` (step 7) commit through the helper and
their APPROVE branches say to leave the write uncommitted;
`apply-implementation-review.md` step 1 calls the helper after the binding check
and before the `BLOCK` pin; `review-plan.md`, `record-manual-plan-review.md` and
`apply-plan-review.md` carry the plan-stage sentence. Golden hashes updated and
`TestReviewStageWriteCommitRuleConformance` added in
`workflow_integration_test.py`. Verified: the nine payload suites green in a
scratch conformance fixture (the two `*_demo_test.py` files need this
repository's history and are not among them), whole-file diff against `v2.9.0`
shows only the listed hunks, `workflow-manager verify .` clean. CP3:
`workflow_acceptance_matrix_test.py` gains `ReviewStageWriteDurabilityProcess`
and `...Product` (18 scenarios each, plan CP3 scenarios 1 to 15 plus the
helper-removed negatives `s06b` and `s10b`, which show 2.9.0's texts are refused
by the generator with OPUS-R101-001) and `Item.generate_impl_bundle` gains an
opt-in `scoped_staging` that stages through `stage_scoped_state`. Verified: the
36 new tests green and the nine payload suites green in a scratch conformance
fixture built from the checkpoint's tree (327 acceptance-matrix tests, 18
skipped as before).
CP4: `REVIEW_PROTOCOL.md` gains "Which review-stage writes are committed"
(the commit-rule table, the helper and its refusals); `IMPLEMENTATION_REVIEW_WORKFLOW.md`,
`PLAN_REVIEW_WORKFLOW.md` and the operator reference carry one paragraph each
pointing at it; `docs/common-problems.md` gains three entries (REVISE refused
with "must always transition phase", the APPROVE counterpart, and the helper's
`ReviewStageWriteNotCommittableError`). Verified: `tools/docs/check_docs.py`
clean; the integration, protocol, fingerprint and gate-policy suites green in a
scratch conformance fixture (the operator-reference symbol check caught a
backticked `bundle_generation_mismatch` in the first draft, reworded).
CP5: `WORKFLOW_RELEASE` is `2.9.1` (`PROTOCOL_VERSION` stays `1.2`; `ORCHESTRATION_PROTOCOL.md` names 2.9.1 among
the tested releases and `workflow_protocol_test.py` pins `2.9.1`, both beyond
the plan's file list, required by the protocol suite);
`manifest.json` names `2.9.1` with the refreshed `sha256`/`size` of the 17
changed records (counts unchanged, `tools/release/manager-pin.json` untouched);
`docs/release-history.md` gains the 2.9.1 row. `docs/ROADMAP.md` marks W4 Done
at acceptance. Verification: see the CP5 commit and the implementation bundle's
`TEST_RESULTS.md`.
Self-review of the whole milestone diff: one documentation fix. The
`docs/common-problems.md` remedy for a REVISE round already refused with "must
always transition phase" said to re-run `/apply-implementation-review`; a probe
in a disposable repository showed that does nothing once the refused record
commit exists (the helper returns `None` and post-fix generation refuses the
source phase), so the entry now says what 2.9.1 prevents and points at the
forward repair in issue #13. The APPROVE entry now names
`/recover-implementation-provenance` and its cost (stale verdicts).

## Functional review checklist

Item: `review-stage-write-durability` (Workflow 2.9.1, issue #13), implementation
revision 4. Automated verification is current; this list is the manual,
independent run. This is round 2 of functional review: every flow is re-run,
not only the ones round 1 touched. Everything runs in disposable places; nothing is pushed.

**Rules for the executor.** Work only in a disposable clone of this repository
(`git clone --no-hardlinks /home/rodrigo/Workspace/workflow $W/clone`, then
check out nothing: the clone's `HEAD` already is this branch) or in scratch
repositories you build yourself. Never use `git stash`, `reset`, `rebase` or
`checkout`, never push, never edit a verdict. `cp` and `rm` are aliased
interactive: use `command cp -f` and `command rm -f`. Keep driver scripts in
`$W/drivers`, never inside a scratch repository or an extracted package; run
Python that reads untrusted trees with `-I`. Record, for every step, the exact
command and its output. A step passes only if the stated result holds.

### F0. Setup

1. `W=$(mktemp -d)`; `git clone --no-hardlinks /home/rodrigo/Workspace/workflow $W/clone`;
   `cd $W/clone && git rev-parse HEAD` (note it) and `git status --short` (empty).
2. Release-source conformance fixture (the 2.9.1 payload's tooling, tests included):
   `python3 tools/release/release.py --repo $W/clone stage-conformance --commit HEAD --out $W/conf`
   prints `fixture=$W/conf`; its `scripts/` holds `workflow_state.py`,
   `workflow_acceptance_matrix_test.py`, `workflow_test_harness.py` and the rest.
3. The command texts under test are the package's, not the installation's:
   `$W/clone/payload/.claude/commands/{review-implementation,record-manual-implementation-review,apply-implementation-review,review-plan,record-manual-plan-review,apply-plan-review}.md`
   and `$W/clone/payload/docs/ai-workflow/REVIEW_PROTOCOL.md`.
4. Scratch builder: in `$W/drivers`, write scripts that
   `sys.path.insert(0, "$W/conf/scripts")`, `import workflow_acceptance_matrix_test as m`,
   `import workflow_state as ws`, and use `m.Scratch()` (a git repo with the 2.9.1
   tooling copied in) and `m.Item(scratch, "process", governing="2.2")`. Reproduce
   the fixture `start()` of `ReviewStageWriteDurabilityProcess` (read
   `payload/scripts/workflow_acceptance_matrix_test.py`, class at the end of the
   file): seed, enable `2.2` in `WORKFLOW_CONFIG.json`, `milestone_plan`,
   `generate_plan_bundle`, plan APPROVE, `record_plan_reviews`, `approve_plan`,
   `implement_checkpoint("CP1", ...)`, `generate_impl_bundle("implementation")`.
   Result: phase `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, `generation_head` (in the
   bundle's `MANIFEST.md`, not in the state) = `HEAD`.
   Review writes use `ws.record_local_implementation_review` /
   `ws.record_manual_implementation_review` inside `ws.state_transaction`, exactly as
   the class's `local_review` / `manual_review` do; the REVISE-branch commit is
   `ws.commit_pending_applying_review_feedback_entry(root, wid)`.
5. Cross-check, once: `cd $W/conf/scripts && python3 workflow_acceptance_matrix_test.py ReviewStageWriteDurabilityProcess ReviewStageWriteDurabilityProduct`
   expects 36 tests, `OK`. Failures here end the review as FAIL.

For every flow below, "follow the command text literally" means: read the named
`.md` step by step and perform exactly its calls, in its order, with the
arguments it names; do not call the helper anywhere the text does not.

### F1. Local-stage REVISE, 2.2 (issue #13 dead end gone)

1. Build the F0.4 scratch at `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`.
2. `review-implementation.md` A6, `REVISE` branch: write `REVIEW_FEEDBACK.md`
   (status REVISE), then `record_local_implementation_review(..., verdict="REVISE")`.
   Check: item phase is `APPLYING_REVIEW_FEEDBACK`; `git status` shows the state file
   modified; then perform the text's next call, the helper.
3. Expect: helper returns a SHA equal to `git rev-parse HEAD`; commit count +1;
   subject `chore(workflow): record entry into APPLYING_REVIEW_FEEDBACK for proc-item`;
   `git log -1 --format=%B` final paragraph is exactly `Workflow-Work-Item: proc-item`;
   `git show --stat HEAD` lists only `docs/ai-workflow/WORKFLOW_STATE.json`.
4. `apply-implementation-review.md` step 1: after the binding check call the helper
   again: returns `None`, no new commit.
5. Make one fix commit touching the deliverable (`scripts/feature.py`) with a
   `Workflow-Work-Item: proc-item` trailer, then post-fix generation
   (`item.generate_impl_bundle("post-fix", expect_outcome="ordinary")`, which runs
   `prepare-ai-review.sh` and `record_bundle_generation` and its record commit).
6. Expect: exit 0; no `OPUS-R101-001`; `ws.validate_bundle_generation_record_commit`
   passes; `implementation_provenance_interval_reachable` is true; phase
   `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`; `implementation_revision` 2 (was 1).
7. Negative control (do on a second scratch, same steps but skip step 2's helper call,
   i.e. 2.9.0 behaviour): post-fix generation exits non-zero with `OPUS-R101-001`
   ("must always transition phase"). This proves the fix is what changed the result.

### F2. Manual external-stage REVISE, 2.2

1. Scratch at `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`; local `APPROVE`
   (`record_local_implementation_review(..., verdict="APPROVE")`), left uncommitted
   (phase `AWAITING_MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`; `HEAD` unchanged).
2. `record-manual-implementation-review.md` step 7 `REVISE`:
   `record_manual_implementation_review(..., verdict="REVISE", ...)` then the helper.
3. Expect: one new commit, trailer-final-paragraph as in F1.3, state file only; the
   committed state carries the local-APPROVE ledger (`implementation_review_stages`
   non-null) and phase `APPLYING_REVIEW_FEEDBACK`.
4. Fix commit, post-fix generation as F1.5-6: succeeds, revision +1.

### F3. APPROVE at both stages left uncommitted; gate reachable

1. Scratch at the local-review phase; write an APPROVE `REVIEW_FEEDBACK.md` as
   the matrix's `write_feedback("APPROVE")` does; local `APPROVE`, manual `APPROVE`
   (texts: `review-implementation.md` A6 / `record-manual-implementation-review.md`
   step 7 `APPROVE` branches, which say to leave the write uncommitted).
2. Expect: phase `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`; `git rev-parse HEAD` equals
   the `generation_head` recorded in the bundle's `MANIFEST.md`; commit count unchanged since
   generation; `ws.technical_approval_gate_status(root, state, wid)` returns
   `reachable: True`.
3. Counter-check (the trap, scratch only): commit the state file alone with
   `git add -- docs/ai-workflow/WORKFLOW_STATE.json && git commit -m x -m "Workflow-Work-Item: proc-item"`;
   the gate status is `reachable: False`, cause `bundle_generation_mismatch`.

### F4. Helper idempotency (each ends with exactly one entry commit)

1. Already-committed REVISE: after F1.2, commit the state file yourself (whole file,
   trailer final paragraph). Helper returns `None`; commit count unchanged; post-fix
   generation succeeds.
2. Same, with extra orchestrator trailers: the commit's final paragraph is
   `Workflow-Work-Item: proc-item` followed by lines such as
   `Orchestrator-Run: r1` and `Orchestrator-Lane: w4` in the same paragraph, after a
   `Co-Authored-By:` paragraph. Helper `None`; no second commit; generation succeeds.
3. Crash after persist: F1.2 then stop (no helper); run `apply-implementation-review.md`
   step 1's helper call only: returns a SHA, exactly one entry commit, then F1.5-6.
4. Crash after scoped staging, with another item's residue: after F1.2 add an
   `other-item` entry to the working state file (as `add_foreign_residue` does:
   `work_item_id`, `work_item_type: "process"`, `phase: "PLANNING"`,
   `state_revision: 1`, `last_transition`). Make `git commit` fail inside the helper
   (as `interrupt_after_staging` does: wrap `ws._run`, raise on `["git","commit",...]`).
   Expect: no new commit; `git diff --name-only --cached` is exactly the state file;
   `git show :docs/ai-workflow/WORKFLOW_STATE.json` has no `other-item`. Re-run the
   helper: returns one SHA, one commit; the committed state has no `other-item`, the
   working file still has it; a third call returns `None`. Then fix commit and
   post-fix generation with `scoped_staging=True` succeeds, residue still uncommitted.
5. Repeat 4 for the F2 shape (manual REVISE with the local-APPROVE ledger).

### F5. Refusals (HEAD and index byte-identical before and after each)

Record `git rev-parse HEAD`, `git diff --cached --name-only` and
`git write-tree` before, assert equal after.
1. APPROVE-shaped write (local APPROVE persisted, uncommitted): helper raises
   `ReviewStageWriteNotCommittableError` (message mentions leaving it uncommitted).
2. Unrelated staged content: after F1.2, `git add` a new unrelated file; helper raises
   `DirtyIndexBeforeStagingError`; the file stays staged, no commit made. Also with a
   different content staged on the state file itself: same error.
3. Forbidden null-valued field, add: after F1.2 add `"probe_field": null` to the item
   in the working state file; helper raises `ReviewStageWriteNotCommittableError`
   naming `probe_field`.
4. Forbidden null-valued field, delete: pick a key outside
   `ws.REVIEW_STAGE_WRITE_COMMIT_FIELDS` whose value in `HEAD` is `null`
   (find one with a short script; if none exists, first commit one as a setup
   commit before F1.2), delete it from the working state file after F1.2; the same
   refusal. (An absent key and a null key are different; this is the 2d2fd7e/bcf2a42
   fix.)
5. A crash-left `technical_review_block_pins` entry: refusal naming it; committing that
   pin alone and re-running then succeeds.
6. The refusal's two message shapes: when `technical_review_block_pins` is stray, the
   message's remedy is to commit the whole state file; otherwise (e.g. F5.3/F5.4) the
   message says the write is 'not a pure review-stage entry'. Check both texts appear
   in the right cases and neither in the other.

### F6. 2.1 and 1 step-0 entry route

1. Scratch with `governing="2.1"`, phase `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`
   (no review stage writes REVISE). Follow `apply-implementation-review.md` step 0
   (`enter_applying_review_feedback`) then step 1's helper: one entry commit,
   trailer as F1.3; fix commit; post-fix generation succeeds. Without the helper it
   is refused with `OPUS-R101-001` (matrix `s10b`).
2. Same for a governing `"1"` item. If `m.Item` cannot seed `"1"`, build it by routing
   (`route_work_item` with version `"1"`) or report precisely why not; that is a
   limitation to report, not a pass.

### F7. Plan stage unchanged

1. `review-plan.md`, `record-manual-plan-review.md`, `apply-plan-review.md` each carry
   the one added sentence and no commit call; `git diff v2.9.0..HEAD -- payload/.claude/commands/{review-plan,record-manual-plan-review,apply-plan-review}.md`
   shows only that sentence per file (15 insertions across the three files, one
   sentence each).
2. Drive a plan stage: local plan APPROVE, manual plan APPROVE, then plan approval.
   Expect state writes uncommitted until the approval commit, commit count +1 only
   for it, the plan gate reachable. Counter-check: a state-only commit before the
   approval raises `bundle_generation_mismatch` at the plan gate.

### F8. 2.9.1 package builds and verifies

1. `V=$W/venv; python3 -m venv $V && $V/bin/pip install --require-hashes -r $W/clone/tools/release/deflate-requirements.txt`
   (the system Python lacks `zlib_ng`; do not install into it).
2. `$V/bin/python $W/clone/tools/release/release.py --repo $W/clone build --commit HEAD --out $W/out`
   prints `version=2.9.1`, a `files=` count, `zlib_ng=` and three hashes;
   `$W/out` holds `workflow-2.9.1.tar.gz`, `workflow-2.9.1.manifest.json`, `SHA256SUMS`.
3. `workflow-manager package verify $W/out/workflow-2.9.1.tar.gz` succeeds.
4. In the clone: `jq -r .workflow_version manifest.json` is `2.9.1`;
   `grep -n 'PROTOCOL_VERSION = ' payload/scripts/workflow_protocol.py` is `"1.2"`;
   `grep -n 'WORKFLOW_RELEASE = ' payload/scripts/workflow_protocol.py` is `"2.9.1"`.
5. Scratch install: new empty git repo, `workflow-manager --release-dir <extracted tree of the package> bootstrap <repo>`
   then `workflow-manager --release-dir <same> verify <repo>` reports
   `installation matches workflow 2.9.1`. `manifest.json` records' `sha256`/`size`
   match the files (`package verify` covers it).
6. `release_test.py` with the zlib-ng venv's Python (not the system `python3`)
   and `python3 tools/docs/check_docs.py` from the clone: both clean.

### F9. Documentation accuracy

1. `REVIEW_PROTOCOL.md` "Which review-stage writes are committed" (it names
   `DirtyIndexBeforeStagingError`; the two summaries, `review-implementation.md`'s and
   `record-manual-implementation-review.md`'s, say "or step 0's own entry"): every row of the
   table matches the behavior observed in F1-F7 (REVISE yes-alone; step-0 entry
   yes-alone; APPROVE no; BLOCK nothing; plan no), and the helper description
   (subject, trailer, `None`, refusals, `REVIEW_STAGE_WRITE_COMMIT_FIELDS`) matches
   `workflow_state.py`. The recovered-`"2.2"`-HEAD qualification in row 2 is
   exercised by matrix `s09`.
2. `docs/common-problems.md`: three new entries, carrying the 2.9.1 stamp and the
   docs' new remedy text; the 2.9.0 remedy text
   (commit the state file alone before the first fix commit) works on a scratch
   built without the helper; the claim that re-running `/apply-implementation-review`
   after a refused record commit does nothing is reproduced (helper `None`, post-fix
   generation still refused).
3. `docs/release-history.md`: the 2.9.1 row says what F1-F6 showed, names Protocol 1.2,
   and its link text matches `v2.9.1`; "Last checked with" says 2.9.1; the 2.9.1 claim
   "accepts no commit shape 2.9.0 refuses" holds for what F1-F4 committed (2.9.0's
   `validate_bundle_generation_record_commit`, taken from the `v2.9.0` tag's
   `workflow_state.py`, accepts the F1 history).
4. `python3 tools/docs/check_docs.py` (F8.6) covers links and symbols.

### F10. This repository's own installation unchanged

In `/home/rodrigo/Workspace/workflow` (read-only commands only):
`workflow-manager --version` is 1.6.0 (the PATH one);
`workflow-manager verify .` prints `.: installation matches workflow 2.9.0`;
`git diff 9a532e5..HEAD --stat -- .claude scripts docs/ai-workflow/*.md .workflow-manager .github`
(`9a532e5` is the 2.9.0 install commit; the `v2.9.0` tag carries the 2.8.0 installation)
shows no change to the installation files except this item's own plan, registry,
mapping, artifacts and `WORKFLOW_STATE.json` (work-item state, not the installation).

**Known limits.** The review commands are prose for an agent; the helper's calls are
driven in the order the texts name, not by a live model. `s10`/`1` coverage depends on
the harness seeding a `"1"` item. The two `*_demo_test.py` suites need this
repository's history and are not part of the fixture run. No release is published here.

## Open decisions

OD-1 to OD-5 of the plan, each with a recommendation: fix shape (recommended:
the review step commits its REVISE write, `/apply-*` commits a pending one,
through one idempotent helper; the generation check is not loosened), helper
versus prose, the APPROVE trap, the plan stage, and the version.
