# W15: Workflow 2.18.1 — review follow-up clean-up (Revision 5)

- **Work item:** `review-followups-cleanup` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner decided on 2026-10-16 that
  Optional review findings never hold acceptance but a milestone clears them from time to
  time, and asked for this one on 2026-10-20. It is row 18 of `docs/ROADMAP.md` (marked
  Current by this plan).
- **Issues:** RodrigoFAbreu/workflow#31, #39, #45, #52, #56, #60, #64.
- **Branch:** `milestone/review-followups-cleanup`
- **Base commit:** `e1be478` (main after #67: the release source is Workflow 2.18.0; this
  repository's own installation is also 2.18.0, automatic gates, default `2.2`, no
  `GATE_POLICY.json`)
- **Plan revision:** 4. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.1, a patch release (`fix:`), that clears the contained, clearly specified
items of the seven `review-follow-up` issues: code and refusal-message defects (each with a
regression test), the review-baseline undo that runs outside the state lock, test hardening,
release-tooling edge cases, the sharded conformance step's log and wording, and wording in
the shipped documents and the manifest's rationales. The items that need a protocol or
release-policy decision are deferred, and the duplicates and the ones that no longer apply
are closed.

Why `fix:` and not `feat:`: nothing here adds a capability. Every change corrects a defect,
hardens a test, or rewords text; no script gains a command, no document a contract. The one
new keyword (`on_failure` on the internal `state_transaction`) is the lock-scope correction
of 39a, not a feature. A patch also keeps the version change in step with the pull-request
title (`fix:` is a patch impact).

### Hard limits (invariants)

- **No state field, ledger, phase, trailer, commit shape or protocol change.** No new
  refusal code, no new `describe` or envelope field. A refusal keeps its exception class and
  code; only its wording or next-step text may change. Section 3 names every wording that
  changes (45a, 52b, 52f, 56d) and the documents that change (CP4).
- **No Controller or Manager change.** `min_manager_version` stays 1.13.0.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`,
  `docs/ai-workflow/` managed documents, `.workflow-manager/`, the managed blocks of
  `CLAUDE.md` and `.gitignore`, and `.github/workflows/workflow-conformance.yml`. Fixes go to
  `payload/`, `templates/`, `tools/` and `manifest.json`. `.github/workflows/workflow-ci.yml`
  is this repository's own CI (not the installation) and changes for 39i, 56a and 56d.
- **No command file moves.** `payload/.claude/commands/` is byte-identical to the base in
  every checkpoint, so no golden hash is re-recorded (64c is deferred, section 4).
- **Size:** five checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new regression test, written first and shown to
  fail against the unfixed code where the item is a defect (the "red first" rule below);
  the nine payload suites from a staged fixture; the `tools/release` tests (in the zlib-ng
  environment); the `tools/docs` tests and checker; the byte-identity check of the command
  files; `workflow-manager verify .` clean.
- **Aids (never a stop):** the inventory's sizes and risk notes; the per-record hunk reading
  of the manifest rationales against `git diff` (CP5); the suggested test shapes in section 5
  where a done rule says "or an equivalent".

**Red first.** For every defect item the checkpoint runs the new test against the pre-fix
code before applying the fix and records the failure in its report. A test that passes
without the fix does not count. This is the rule that makes 39a's "a test that would fail
without the fix" checkable.

## 2. Facts this plan relies on (re-checked against `e1be478`)

The orchestrator's inventory (`inventory.md`, 35 items) is a starting point. Each item below
was re-read against the code and the issue text; these are the findings that differ from, or
add to, the inventory.

- **The issue bodies hold more than the inventory's 35 items.** Re-read in full at revision 2
  (local plan review round 1, `LPR-R1-001`): #60's body carries five items before the comment
  with 60a/60b, and #64's first bullet is a stale command-file count. They are items 60c to 60g
  and 64h in section 6. Each was checked against the code: `_check_plain(..., flow=True)`
  refuses `:` only and `_PLAIN_FORBIDDEN` is `"[]{},"` (60c); `protected_conflicts` tests the
  page prefix through the one representative `docs/items/x.md` (60d); the
  `declaration_conflict` check runs in `/milestone-plan` step 3 (60e); no test or document
  pins a trailing comment on `items:` or `depends_on:` (60f); the way-back section of
  `BACKLOG_FILE.md` does not mention the copied script's header (60g); and
  `WORKFLOW_V2_1_OPERATOR_REFERENCE.md` states the count in four places: "holds 16 files
  today, and all 16" (line 251), "The number 16 itself is *not* derived" (line 266),
  `assertEqual(len(on_disk), 16)` (line 267) and "roster of 16" (line 1006), while the
  directory and the test (`workflow_integration_test.py:7034`) hold 22 (64h; `LPR-R2-001`).
- **Backlog tests sit in two files.** The unit tests are in
  `payload/scripts/workflow_state_completion_obligations_test.py`: `BacklogParser` (the
  refusal table `test_refusals_name_their_line`, the accepted forms
  `test_empty_backlog_and_top_level_order`), `BacklogDeclaration`
  (`test_protected_conflicts_predicate`), `BacklogDeclarationConflict` and `BacklogDocument`
  (every `BACKLOG_FILE.md` needle, `_BACKLOG_DOC_REL`). The end-to-end lifecycle tests are in
  `workflow_acceptance_matrix_test.py`: `BacklogLifecycle`, `BacklogLifecycleDeclaredGenerator`,
  `BacklogProtectedDeclaredPath` and `BacklogUndeclared`; it has no refusal table.
  `workflow_integration_test.py` holds no `BACKLOG_FILE.md` needle. There is no
  `workflow_backlog_test.py`; the inventory's file name for 60a and 60b is wrong
  (`LPR-R2-002`).
- **60a needs a malformed file within the 2,000-line cap.** `MAX_LINES` is 2000, so a valid
  item (four fields) cannot chain 999 deep; two-line items that carry only `id` and
  `depends_on` can. The regression test builds that file and must hit `RecursionError`
  against the unfixed code.
- **`docs/common-problems.md` is not shipped** (no manifest record, no `payload/` copy). So
  52f's "pointer to the common-problems entry" would point a target repository at a page it
  does not have; this plan gives the refusal a plain next step in words instead (OD-3).
- **64a counts:** 16 records carry a `workflow-2.18.0` sentence; 15 of them lead with the
  shared "the model is named \"the agent\"" text (13 verbatim, `MILESTONE_WORKFLOW.md` and the
  operator reference with a tailored tail) and `COMMAND_FILES.md` has its own. Four 2.18.0
  records have no sentence: `workflow_integration_test.py`, `workflow_protocol.py`,
  `workflow_protocol_test.py` and `workflow_state_test.py`.
- **The template digest is the only "golden" a template change moves.** The manifest's
  `templates` record for `workflow-conformance.yml` holds a `sha256` and `size`. The installed
  copy and `.workflow-manager/installation.json` are 2.18.0's and are not touched.
- **No document test checks the protocol example against the schema.** 31d is a prose
  example fix; the specification tests parse only the mirrored tables.
- **The pass detail of `state_valid` is not pinned** by any test or document (52b): the
  string `validate_state accepts the state` occurs once, in `workflow_protocol.py`.
- **31a is a recorded decision.** `assert_verdict_well_formed`'s docstring and
  `REVIEW_PROTOCOL.md` state that an `APPROVE` with an Important entry is deliberately not
  refused. The issue text still asks for the refusal, so it is closed as decided.
- **52d lives in an immutable manifest.** The `review-round-counts` label is in the published
  2.15.0 manifest; the current `manager.downgrade_boundary.signals` is empty.

## 3. Design decisions

### D-Patch: the version is 2.18.1, `fix:`

`WORKFLOW_RELEASE` becomes 2.18.1; the Orchestration Protocol stays 1.5. `min_manager_version`
stays 1.13.0, `new_work_only` stays empty, `gate_default_change` stays empty, `signals` stays
empty. The manifest gains no record and loses none, so `counts` keep their artifact and
category totals; only digests, sizes, rationales, the template record, the posture and the
measured suite counts move.

**Downgrade posture, per changed area** (CP5 writes it into the manifest and the release
history; an older release reads every state, ledger and file 2.18.1 writes, because nothing it reads changes; the one exception is the verdict input of 31b, which is feedback text and not a file 2.18.1 writes):

| Area | What 2.18.1 changes | Moving back to 2.18.0 |
|---|---|---|
| Verdict shape (31b) | A wrapped or prefixed "none" placeholder (`(none)`, `[none]`, `"None"`, `— None`, `~~none~~`) is a placeholder, not a finding, in the shape check and in the Optional-finding recording. | 2.18.1 and 2.18.0 accept different verdict sets; each treats a wrapped placeholder differently, and neither set contains the other (`EPR-002`, `LPR-R4-001`). (1) An `APPROVE` whose Blocking section holds only a wrapped placeholder such as `- (none)` is accepted by 2.18.1 and **refused** by 2.18.0 (the base treats it as a Blocking finding, so `assert_verdict_well_formed` refuses the approval); after a move back to 2.18.0 such feedback must be reissued (the placeholder removed or written as plain `None`) before it is ingested again. (2) A `REVISE` whose only Blocking or Important entry is such a placeholder is refused by 2.18.1 with `MalformedVerdictError` and accepted by 2.18.0; and 2.18.0 records a wrapped placeholder under Optional as a finding that then needs a disposition, which 2.18.1 does not. Only direction (1) needs action after a downgrade. A ledger already written is read unchanged. |
| Acceptance refusal (45a) | The refusal prints each undispositioned finding's first line, cut to 240 characters. | The older refusal prints the whole stored text. The recorded finding is unchanged either way. |
| Review baseline (39a) | The undo of a failed manual ingest's baseline runs inside the state lock. | No state or file shape differs; 2.18.0 keeps the small race window. |
| `verify` detail (52b) | The `state_valid` pass detail names both checks. | Older wording; the check id, status and schema are the same. |
| Recovered-role refusal (52f) | The refusal ends with a next step. | The older message ends at the explanation. Same exception class. |
| Backlog script (60a to 60d) | A malformed backlog with a deep `depends_on` chain reports its violations instead of crashing; a rollback restores the file mode; a `?` in a plain flow-list entry is refused as a format error; an artifact declaration that protects an exact page path, or a protected prefix, under `docs/items/` is a `declaration_conflict`. | 2.18.0 crashes (exit 1, no JSON) on the deep file, may leave a changed mode after a refused generator run, accepts the `?` entry (the id is then refused by validation, as today) and misses the exact-page and prefix conflicts. Nothing persisted differs. |
| Managed conformance job (56a, 56d) | A failed checkout copy keeps its diagnostics in the unit's log; a bad shard total is worded as such. | `workflow-manager update` restores 2.18.0's job text. Diagnostics only. |
| Documents (31b, 31c, 31d, 39c to 39f, 60f, 60g, 64b, 64f, 64h) | Wording; one example corrected; the placeholder rule in `REVIEW_PROTOCOL.md` states the leading, trailing and wrapping form. | Older wording (the 2.18.0 protocol text describes the narrower trailing-only rule, which is what 2.18.0 enforces). |

### D-31b: the placeholder test strips both ends

In `_is_placeholder` (`payload/scripts/workflow_fingerprint.py`), after the existing removal
of markdown emphasis characters and whitespace folding, strip characters whose Unicode
category starts with `P`, `S` or `Z` from **both** ends (today only the end), then test the
set `{none, n/a, -, none identified}` and the "no findings" pattern as before. An entry that
reduces to nothing is still a placeholder. Only an entry that is *wholly* a placeholder after
stripping changes class; `none of the tests were run` and `"None" handling is wrong` stay
findings. The same function serves the shape check (`_section_has_finding`) and the Optional
parser, so both treat the new forms alike; the docstring of `assert_verdict_well_formed` is
reworded to say "leading, trailing and wrapping". The widening applies to `APPROVE` as well as
`REVISE`: an `APPROVE` with only `- (none)` under Blocking was refused by the base and is
accepted now, which is the downgrade exception recorded in D-Patch (`EPR-002`). The normative sentence in
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md` ("trailing punctuation or symbols on `None` are
ignored, and an entry made only of punctuation or symbols is also a placeholder") states the
old, narrower rule, so CP1 rewrites it in the same checkpoint to "leading, trailing and
wrapping punctuation or symbols on `None` are ignored" (the entry made only of punctuation or
symbols stays a placeholder), and `workflow_integration_test.py` pins it with a needle
(`LPR-R1-002`).

### D-39a: the baseline undo runs inside the lock

`state_transaction` gains an optional keyword `on_failure`, a no-argument callable run **inside
the lock** when the mutator, the monotonicity check, `before_publish` or the publish raises,
before the exception propagates. "Raises" means any `BaseException`, as today's
`except BaseException` wrapper does, so a `KeyboardInterrupt` during `before_publish` still
removes the baseline (`LPR-R1-O3`). The original exception always propagates; an exception from
`on_failure` is suppressed (its only caller is a never-raising best-effort undo). On success
it is never called. `_ingest_two_stage_manual_verdict` passes the existing
`remove_stage_baseline(..., only_state_revision=...)` undo as `on_failure` and drops the
`except BaseException` wrapper that ran after the lock was released. The alternative the issue
names (also compare `recorded_at`) is rejected: two ingests can carry the same second, so it
narrows the race without closing it. No state, file or protocol shape changes.

### D-45a: the refusal shows a bounded label

`_finding_label` prints the finding's **first line**, at most 240 characters (a longer line is
cut to 239 characters plus `…`), per the finding-dispositions plan's D-Parse. The ledger entry,
the dispositions skeleton and the rendered record keep the whole text. The
`--finding-dispositions` CLI listing deliberately keeps printing the whole stored `text` in its
JSON: cutting it would change an output schema, which a patch release does not do
(`LPR-R1-O4`).

### D-52: message and detail wording (which text changes)

- **52b:** `workflow_protocol.py` `verify`, check `state_valid`, pass detail becomes
  `validate_state and validate_review_round_counts accept the state`. Check id, status and
  the schema are unchanged.
- **52f:** the recovered-role field-set refusal in `workflow_state.py`
  (`MalformedBundleGenerationRecordCommitError`, class and code unchanged) gains a final
  clause: keep the commit's state change to the listed fields and put any other change in its
  own commit; if the repository was moved back to a release older than the one that wrote
  the commit, update to that release or later and run the command again. The published
  2.14.0 text is not changed. Issue #52 item 6 says "refusals" because
  `validate_bundle_generation_record_commit` has three recovered-role raises; only the
  field-set one gets the clause. It is the case the issue quotes (a commit written by a
  release that recovers more fields than the one now installed). The target-phase and
  parent-phase refusals keep their text: each already names the phase it found and the set it
  requires, which is the corrective information, and they are not the downgrade case the issue
  quotes (`LPR-R1-O1`).
- **56d:** the sharded step's annotation and summary row for "the shard `total` row is not
  `ok` but the check exited 0" are worded as the bad total they are; the exit-code wording
  stays for a non-zero exit.
- **45a** above. No other refusal text changes; 31a is closed.

### D-Staging: scratch staging for CP1 to CP4 (the procedure W14 used, section 5 there)

`release.py stage-conformance` and `tools/release/release_test.py` both verify the manifest
against the tree, and CP1 to CP4 change shipped files whose digests the committed manifest
records only at CP5. So each of CP1 to CP4 verifies in a **disposable clone**, never in the
repository:

1. `git clone --quiet /home/rodrigo/Workspace/workflow "$TMPDIR/cpN/repo"` (full history and
   tags; the clone's HEAD is the branch tip, which holds the checkpoint's commit).
2. In the clone, a scratch script (kept in `$TMPDIR`, not a deliverable) recomputes
   `sha256` and `size` of every `artifacts` and `templates` record whose file differs from
   its record, **and measures and rewrites `manager.conformance.suites`** (the per-suite
   discovered test counts, by the same discovery `release.py manager-block --release-dir
   <scratch> --write` uses), writes `manifest.json`, and `git commit`s it in the clone. A
   checkpoint that adds test methods (CP1 to CP4 all do) otherwise fails
   `test_real_acceptance_module_partitions_exactly` (`tools/release/release_test.py:1115`,
   which reads the recorded acceptance count and asserts `len(ids) == counted`) with e.g.
   `451 != 450` before CP5 (`EPR-001`). That count assertion is preserved, not edited or
   skipped: the scratch manifest carries the measured counts, which is what CP5 does for
   the committed one. No record is added or removed, so `counts` need no edit; no rationale
   is touched.
3. In the clone: `python3 tools/release/release.py stage-conformance --commit HEAD --out
   "$TMPDIR/cpN/fixture"`, then each of the nine suites from `$TMPDIR/cpN/fixture/scripts`
   (`python3 -B <suite>`), with `TMPDIR` and `HOME` set to scratch directories.
4. In the clone, with the zlib-ng environment's python
   (`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`):
   `python -m unittest tools/release/release_test.py`; and
   `python3 -m unittest tools/docs/check_docs_test.py`.
5. In the repository: `git diff --stat <base> -- payload/.claude/commands` is empty.

Manifest verification is not weakened (the scratch manifest is verified in full); CP5 does the
same record updates in the committed `manifest.json`, which then stages unmodified, and runs
`tools/release` directly against the repository's `HEAD`.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
|---|---|---|
| OD-1 | The version: patch 2.18.1 (`fix:`) or minor | **Patch, `fix:`.** Corrections and test hardening only; no capability, state, protocol or document contract added. |
| OD-2 | 64c (re-wrapping the long guard lines of the six user-only command bodies) | **Defer.** It is cosmetic, moves six shipped command files, re-records their golden hashes and manifest digests, and risks the confirmation literal the guards pin, for a readability gain in files a harness reads as prompts. Reopen only if the owner wants it as its own item. |
| OD-3 | 52f: a pointer to `docs/common-problems.md` or a plain next step | **Plain next step in words** (D-52). That page is not shipped, so a shipped message must not depend on it. |
| OD-4 | 39a: `on_failure` inside `state_transaction`, or compare `recorded_at` | **`on_failure`** (D-39a): it closes the race instead of narrowing it, and adds no state field. |
| OD-5 | 31a: CLOSE or DEFER | **Close.** The decision is recorded in the docstring and `REVIEW_PROTOCOL.md`; refusing would change protocol-visible verdict acceptance. A design item is for the owner to open. |
| OD-6 | 39j (CI pin must equal `min_manager_version`, or be "at least") | **Defer to the owner.** It is a release-gating rule with release-process consequences. |
| OD-7 | 39c: a third reason string in the changes file, or a comment and a sentence | **Comment and one protocol sentence.** A new reason string changes bundle text that tests and reviewers read. |
| OD-8 | The cost of CP2 (backlog, tooling, CI and template together; nine fixes and one test-only pin after revision 2) | Kept as one checkpoint: every item is small, none depends on another. If CP2 overruns, 60b (mode restore, lowest priority) moves to DEFER with the reason "needs a misbehaving declared generator", not a sixth checkpoint. |
| OD-9 | 60e: run `protected_conflicts` in `/milestone-plan` step 1, before the work item is created | **Defer.** Step 1 is command-file text, and no command file moves in this release (hard limit; re-recording golden hashes is 64c's cost). The conflict is still refused, at step 3, before any plan review; only the earlier timing is lost. Reopen with 64c as the command-file clean-up item. |
| OD-10 | `EPR-005`: the `.review-w15/issue-*.md` snapshots were empty or comment-only for the external reviewer | **No plan change; rejected as a plan defect.** The plan's claims were each re-read against the repository (section 2) and the seven issue bodies are the inventory's source of truth (revision 2 added the six items the inventory missed). The snapshots are review inputs the orchestrator supplies outside the repository (`.review-w15/` does not exist in this tree, so there is nothing for a plan edit to fix); the orchestrator is asked to attach complete bodies and comments of #31, #39, #45, #52, #56, #60 and #64 to the next review round. |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does
not exist in this repository's release source).

## 5. Checkpoints

Five checkpoints. CP1 to CP4 are independent fixes grouped by file area; CP3 runs after CP1
because its tests exercise code CP1 changes; CP5 is the release. Each of CP1 to CP4 verifies
as D-Staging says; each leaves `payload/.claude/commands/` byte-identical.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Review-core defects and messages | - | 4 | 1 |
| CP2 | Backlog script, release tooling, CI and the conformance template | - | 3 | 1 |
| CP3 | Test hardening | CP1 | 3 | 1 |
| CP4 | Shipped documents and the tests that pin them | - | 2 | 1 |
| CP5 | Release 2.18.1 | CP1, CP2, CP3, CP4 | 3 | 1 |

<!-- CP1 -->
### CP1 — Review-core defects and messages

**Files:** `payload/scripts/workflow_fingerprint.py`, `payload/scripts/workflow_state.py`,
`payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_fingerprint_test.py`,
`payload/scripts/workflow_state_test.py`, `payload/scripts/workflow_gate_policy_test.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `payload/scripts/workflow_integration_test.py`
(the placeholder sentence and its needle, 31b only).

Items (each a code or message defect, so each has a red-first regression test):

- **31b** (D-31b). Test in `workflow_fingerprint_test.py`, beside the existing placeholder
  tests: a `REVISE` whose Blocking section holds only each of `- (none)`, `- [none]`,
  `- "None"`, `- — None`, `- ~~none~~` (and Important likewise, with only Optional content
  elsewhere) is refused with `MalformedVerdictError`; the same entries under Optional are
  not recorded as findings; `none of the tests were run` still counts as a finding; an `APPROVE` whose Blocking section
  holds only each of those placeholders is **accepted** (and the same `APPROVE` is shown to be
  refused by the unfixed code, the regression `EPR-002` asks for).
  `REVIEW_PROTOCOL.md`'s placeholder sentence is rewritten to "leading, trailing and wrapping
  punctuation or symbols on `None` are ignored, and an entry made only of punctuation or
  symbols is also a placeholder" (`LPR-R1-002`), and a needle in
  `workflow_integration_test.py`, beside the other `REVIEW_PROTOCOL.md` sentence needles
  (whitespace folded, as they do), pins the phrase "leading, trailing and wrapping
  punctuation or symbols on `None` are ignored".
  **Done:** all pass, and the unfixed code fails every placeholder form; the needle fails
  against the unrevised protocol text.
- **39a** (D-39a). Tests in `workflow_state_test.py`, in the manual-ingest group: (1) force
  `_store_manual_verdict` (the `before_publish` hook) to raise after the baseline is written;
  assert the undo ran **while `held_primitives()` contained the state lock** and that the
  record is gone; (2) a cross-process variant: a child process blocked on the lock writes a
  baseline with the same `state_revision` as soon as the lock is free, and the test asserts
  that record survives the failed ingest's undo (added if a child process can be driven
  reliably in the harness; (1) is the gate). **Done:** (1) fails against the unfixed code
  (the undo runs after the lock is released); a failure after `mutator` but before publish and
  a failure of the publish itself both trigger `on_failure`; a successful transaction never
  does; `state_transaction`'s other behaviour (re-read inside the lock, monotonic pin check,
  `before_publish` order) is unchanged and its existing tests pass. One more subtest raises
  `KeyboardInterrupt` from `before_publish` and asserts the baseline is removed (any
  `BaseException`, `LPR-R1-O3`).
- **45a** (D-45a). Test in `workflow_gate_policy_test.py` next to
  `test_no_key_passes_and_an_undispositioned_finding_refuses_naming_everything`: an input
  Optional entry of several lines whose total exceeds 1,200 characters and whose first line
  exceeds 240 (parsing already caps the **stored** text at `OPTIONAL_FINDING_TEXT_LIMIT`, 1,200,
  and `validate_state` rejects a longer ledger text, so the fixture respects that limit)
  refuses with a message that holds the first line cut to 239 characters plus `…`, no second
  line, and the key, stage and round; the ledger still holds the existing capped (1,200
  character) text, and the `--finding-dispositions` listing is asserted to print that same
  capped stored text unchanged (`LPR-R1-O4`, `EPR-004`). **Done:** the refusal assertions fail against the unfixed code;
  the listing assertion passes before and after.
- **52b** (D-52). Test in `workflow_protocol_test.py`: a healthy state's `state_valid` pass
  detail names both `validate_state` and `validate_review_round_counts`. **Done:** the detail
  is exactly the new string; the `verify` result schema test still passes.
- **52f** (D-52). Test in `workflow_state_test.py`: the recovered-role refusal for a commit
  that changes a field outside the recovered set ends with the next step (the text names
  "its own commit" and "update"); the exception class is unchanged; the ordinary-role
  refusals are unchanged. **Done:** fails against the unfixed code; any existing test that
  pinned the old tail is updated and listed in the checkpoint report.

**Verification:** the nine suites from the scratch fixture; `tools/release` and `tools/docs`
tests per D-Staging; every new test shown red first.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Backlog script, release tooling, CI and the conformance template

**Files:** `payload/scripts/workflow_backlog.py`,
`payload/scripts/workflow_acceptance_matrix_test.py`,
`payload/scripts/workflow_state_completion_obligations_test.py`,
`templates/.github/workflows/workflow-conformance.yml`, `.github/workflows/workflow-ci.yml`,
`tools/release/manager_block.py`, `tools/release/release_test.py`.

Items:

- **60a.** `_find_cycle` becomes an iterative depth-first search that returns the same cycle
  (same node order, same first-found cycle) as today. Test in the acceptance-matrix backlog
  class (end to end): a malformed backlog built at the longest chain the cap allows (the `version:` and
  `items:` lines, then 999 two-line items, `id` and `depends_on` only, chained: 2,000 lines),
  run through `status` the way the existing backlog tests run it, makes it exit with the
  collected violations (missing fields) and no traceback. The chain sits at the cap because
  anything shorter risks passing against the unfixed code near Python's default limit of
  1,000 frames (`LPR-R1-O5`). **Done:** the test fails with `RecursionError` against the unfixed
  code; every existing cycle message test is unchanged.
- **60b.** `_snapshot` captures the file mode with the bytes, `_restore` restores both
  (including when the bytes are equal and only the mode differs) and `_write_atomic` publishes
  a restored file with the snapshot mode; the backlog file is snapshotted the same way as the
  page. Test in the acceptance matrix's `BacklogLifecycleDeclaredGenerator`: a declared generator that changes only
  the page's (and, separately, the backlog file's) mode and then fails leaves the original
  mode and bytes after the refusal. **Done:** fails against the unfixed code.
- **60c.** `_check_plain(..., flow=True)` also refuses `?` (next to `:`), with a message in the
  same form (`a plain entry of a flow list cannot contain `?`; quote it`). PyYAML refuses the
  entry; no file reaches use because validation refuses the id, but the parser's own
  guarantee holds for validated files only (issue #60, item 1). Tests in
  `workflow_state_completion_obligations_test.py`, class `BacklogParser`: `depends_on: [a?b]`
  is a format error naming the line (a case added to the refusal table
  `test_refusals_name_their_line`), and a quoted `"a?b"` entry is still accepted by the parser. **Done:** the
  refusal test fails against the unfixed code.
- **60d.** `protected_conflicts` also reports any exact protected path (either stage) that
  starts with `docs/items/` (the item-page prefix), and any protected **prefix** that lies
  under it (`docs/items/team/`; a prefix that is `docs/items/` itself or shorter is already
  caught through the representative page), not only the representative `docs/items/x.md`
  (`EPR-003`). A reported prefix pair names the prefix as its path. The rule applies whenever
  `paths` holds a path under `docs/items/`; both callers pass `REPRESENTATIVE_ITEM_PAGE`, so
  it always fires for them. The two callers are `workflow_backlog` preflight/accept (line 856)
  and `workflow_state._classify_declared_backlog` (used by `generate_artifacts_declarations`),
  so the new rule also applies at `/milestone-plan` step 3, which is the intended effect
  (`LPR-R2-O1`). The docstring's "the `(stage, path)` pairs among `paths`" is reworded to
  "the `(stage, path)` pairs among `paths`, plus, for any path under the item-page prefix, the
  exact protected paths and protected prefixes under that prefix", since the new pair is not one of `paths`.
  `test_protected_conflicts_predicate` and `workflow_state_test.py`'s
  `test_the_item_page_prefix_is_checked_too` stay green unchanged. Tests: a predicate case in
  `workflow_state_completion_obligations_test.py` beside `test_protected_conflicts_predicate`
  and in `BacklogDeclarationConflict` (an artifact declaration protecting `docs/items/foo.md`
  exactly raises `declaration_conflict` naming that path and stage; one protecting the
  prefix `docs/items/team/` raises it naming that prefix; one protecting an unrelated exact
  path or prefix under `docs/` does not). **Done:** fails against the unfixed code (issue #60, item 2).
- **60f (test half).** The parser accepts `items: # x` and `depends_on: # x` (a trailing
  comment on a key with no inline value) as YAML does; two cases pin that in
  `workflow_state_completion_obligations_test.py`'s `BacklogParser`, beside
  `test_empty_backlog_and_top_level_order` (which already pins `items: [] # none`). No code changes; they pass before and after. The documentation half
  is in CP4.
- **39g.** In `manager_block._detector`, a `kind` that is not a string is reported as a
  problem, not raised as `TypeError`. Test: `kind` of `[]` and `{}` yields a problem list.
- **39h.** `_TAG_RE` and `_VERSION_RE` are applied with `fullmatch`, like the block fields.
  Test: `v1.2.3\n` and `1.2.3\n` are refused where they are read. **Done (39g, 39h):** both
  tests fail against the unfixed code.
- **39i.** In `.github/workflows/workflow-ci.yml` the "Update fixture" step's previous-release
  selector also filters prereleases, and the release list it reads includes `isPrerelease`
  (`gh release list --json tagName,isDraft,isPrerelease`). `release.py check-pending` and
  `check-immutable` tolerate the extra field (they read `tagName` and `isDraft` only). Test:
  a `release_test.py` assertion on the workflow text (the query field list and the filter).
- **56a.** In the sharded step, the checkout copy's output joins the unit's log:
  `cp -a "$GITHUB_WORKSPACE/." "$d/repo" >>"$d/log" 2>&1` in the template and
  `cp -a "$src/." "$d/repo" >>"$d/log" 2>&1` in the CI copy. Test in `ConformanceTemplate`:
  run the step with a `cp` shim that fails and prints an error; the unit's log, as echoed by
  the failure report, holds that error. If the harness cannot shim `cp`, a text assertion on
  both copies is the gate and the report says why.
- **56d.** The "total not ok but the check exited 0" case is worded as the bad coverage total
  it is (D-52), in both scheduler copies, identically. Test: a text assertion on both copies
  for both wordings (the exit-code wording is kept for a non-zero exit); a behaviour test if
  the shard check can be made to report a bad total with exit 0 in the existing harness.
- The manifest `derivation` text of the template record names this change (CP5 writes it).

The existing test that pins the CI scheduler equal to the template (with the `src` and log
substitutions) must pass unchanged in shape, so 56a and 56d are made identically in both
copies.

**Verification:** the nine suites from the scratch fixture (the template is not part of
them, so `release_test.py` in the clone is the gate for 56a and 56d); `tools/release` in the
zlib-ng environment; `tools/docs`; `workflow-manager verify .` clean (the installed
`.github/workflows/workflow-conformance.yml` is not touched).
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Test hardening

**Files:** `payload/scripts/workflow_state_test.py`.

Test-only; no production line changes, so there is no red-first requirement, but each test
must be shown to catch the regression it names (the report records a deliberate break that
makes it fail, then the break reverted in the scratch clone).

- **39b.** One end-to-end test in the manual-ingest group, using `_cp5_plan_at_manual` and
  `_cp5_ingest`: a real manual `REVISE` ingest, an edit of the plan, a republication and the
  real `prepare-ai-review.sh` (through the harness generator); assert the baseline record
  exists and `CHANGES_SINCE_REVIEW.md`'s `MANUAL_EXTERNAL_PLAN_REVIEW` section has a basis
  (`previous_review_content_id:` names the reviewed content), not "not available".
  **Done:** passes; fails if the ingest stops recording the baseline.
- **45b.** The two-item case in the optional-findings residue test asserts the exact
  expected diff (the other item's ledger hunk and nothing naming the committed item) instead
  of `assertNotIn(self.WID, diff)`.
- **52a.** `TestReviewRoundCountsDowngrade._release_2_14_helpers` freezes 2.14.0's four
  commit-field sets as literals, and a test asserts the current sets equal them plus exactly
  `review_round_counts`.
- **52c.** `test_block_and_a_refused_call_change_nothing` gains subtests, for the two manual
  writers, for a duplicate ingest (the same call on the post-state) and a stale content id
  (a mismatched feedback id); each raises and leaves the state and the counter unchanged.
- **52e.** `test_the_key_is_outside_both_content_identities` is replaced by a direct
  comparison: the plan-stage and implementation-stage `review_content_id` and `bundle_id` of
  the same repository are equal with and without a `review_round_counts` value on the item.
  The grep of `workflow_fingerprint.py` is removed.

**Verification:** the nine suites from the scratch fixture; the suite counts (CP5 records
them).
<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Shipped documents and the tests that pin them

**Files:** `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`,
`payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `payload/docs/ai-workflow/COMMAND_FILES.md`,
`payload/docs/ai-workflow/BACKLOG_FILE.md`,
`payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`,
`payload/scripts/workflow_fingerprint.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/scripts/workflow_integration_test.py`,
`payload/scripts/workflow_state_completion_obligations_test.py`, `docs/common-problems.md`.

Wording only; the one code touch is a comment (39c).

- **31c.** `ORCHESTRATION_PROTOCOL.md` section 8.2 condition 5 reads "it is enabled by the
  repository owner's configuration or by an explicit Controller default the owner accepted at
  setup; unset, the gate stops as today."
- **31d.** The `next-action` example in section 5.4 is made consistent: `plan_revision: 2`
  with `review_round.plan: 2` and the per-role counts `plan_local: 2`, `plan_external: 2`
  kept (a complete history reaches that as a local `APPROVE` plus an external `REVISE`, then
  a local `APPROVE` plus an external `APPROVE`; `plan` is the contents taken out of review
  plus one). The example held `plan_revision: 1` with `plan: 3`, which no complete history
  reaches. The needle pins the whole tuple (`LPR-R1-O2`).
- **39c.** A comment where the manual section's basis is refused because the baseline's
  `review_content_id` equals this generation's, and one `REVIEW_PROTOCOL.md` sentence: the
  round is identified, there is no change since it, and the section reads "cannot be
  identified". No new reason string.
- **39d.** `REVIEW_PROTOCOL.md`: at the plan stage `BASELINE.json`'s
  `classification.protected_paths` is a sorted list (the plan-stage metadata carries no
  reasons); at the implementation stage it is an object of path to reason.
- **39e.** `REVIEW_PROTOCOL.md`: at the implementation stage a `REVISE` record is known to the
  item's state when its revision is at most `implementation_revision`; an `APPROVE` record is
  known when the manual ledger entry's `bundle_id` equals the record's.
- **39f.** `REVIEW_PROTOCOL.md`: for a newly protected path the union diff also shows the
  edits made while the path was excluded; that is the safe direction.
- **56b.** `docs/common-problems.md`: `setUpModule` leaves the "not in the plan" causes
  (`plan` refuses an acceptance module that defines it); `setUpClass` and an out-of-test
  `SkipTest` stay.
- **64f.** `COMMAND_FILES.md`'s empty-case bullet adds "(except at the plan stage, where the
  id is required)" after the `prepare-review.md` default.
- **60f (document half).** `BACKLOG_FILE.md`'s accepted-form list states that a trailing
  comment is also allowed after `items:` and after `depends_on:` when the value is a block
  list on the following lines (the key has no inline value). The needle sits in
  `workflow_state_completion_obligations_test.py`'s `BacklogDocument`, beside the other
  `BACKLOG_FILE.md` needles.
- **60g.** The way-back section of `BACKLOG_FILE.md` gains one sentence: after moving back,
  the copied script's built-in page header and next-step lines still name
  `scripts/workflow_backlog.py`; that is expected, and they must not be hand-edited, because
  `check` compares the page byte for byte. Its needle sits in `BacklogDocument` too.
- **64h.** `WORKFLOW_V2_1_OPERATOR_REFERENCE.md` states the current count, 22, in all four
  places (`LPR-R2-001`): line 251 ("holds 22 files today, and all 22 are sectioned below"),
  line 266 ("The number 22 itself is *not* derived"), the line-267 quote of
  `assertEqual(len(on_disk), 22)` (matching `workflow_integration_test.py:7034`) and line 1006
  ("roster of 22"). The existing test
  `test_the_command_inventory_claim_states_the_real_guarantee` pins the old quote
  (`assertIn("assertEqual(len(on_disk), 16)", text)`), so it is updated to the new one and
  gains a guard: the text holds no `16` in the count sentences (it refuses "holds 16",
  "all 16", "number 16", "roster of 16" and `len(on_disk), 16`) and holds each of the four 22
  forms. That change is named in the checkpoint report.
- **64b.** The contract-document test gains needles (and keeps the existing ones) for
  "under every harness, is the literal-confirmation check", "An adapter that cannot tell
  refuses the command" and the 64f clause.

Tests (a document edit is gated by a needle, so a later edit cannot silently undo it):
31c and 31d in `workflow_protocol_test.py` beside the specification tests; 39c to 39f, 64b,
64f and 64h in `workflow_integration_test.py` beside the contract-document tests; 60f and 60g
in `workflow_state_completion_obligations_test.py`'s `BacklogDocument`, which holds every
`BACKLOG_FILE.md` needle (`workflow_integration_test.py` holds none). 56b has no
needle: the page is not shipped, and the `tools/docs` checker covers its form.

**Verification:** the nine suites from the scratch fixture; `tools/docs` checker clean; no
document states a list of governing versions.
<!-- /CP4 -->

<!-- CP5 -->
### CP5 — Release 2.18.1

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/RELEASING.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` in `workflow_protocol.py` becomes 2.18.1, with its two pinned
  assertions in `workflow_protocol_test.py` and the matching `ORCHESTRATION_PROTOCOL.md`
  edits (the tested-releases list, the envelope example, the protocol-1.5 note); the protocol
  version stays.
- `manifest.json` 2.18.1: `workflow_version`; `sha256` and `size` of every record a
  checkpoint changed (the shipped scripts and tests, the shipped documents CP1 and CP4 change, the template);
  `counts` unchanged (no record added or removed); a `review-followups-cleanup
  (workflow-2.18.1)` rationale sentence on **each** changed record, accurate for that file
  (what changed in it, from `git diff <base>..HEAD -- <file>`); the template record's
  `derivation` names the log and wording change; the `manager` block as below.
- **64a (OPT-1, both).** The 15 records that carry the shared 2.18.0 sentence get a
  sentence true of that file, taken from `git diff ad6f863 384e952 -- <file>` (the 2.18.0
  change), and the four records with none get one:

  | Record | Its 2.18.0 sentence says |
  |---|---|
  | `accept-milestone.md`, `retire-legacy-work-item.md` | the flag is an additional layer, the literal-confirmation check is the control, and "the agent must never invoke" is added |
  | `adopt-gate-policy.md`, `request-plan-amendment.md`, `resume-implementation.md` | the guard is restated the same way (check first, flag an additional layer) and the description says "the agent" |
  | `approve-review.md` | description and guard restated; the Claude Code coverage history moves to `COMMAND_FILES.md` |
  | `apply-pr-review.md`, `prepare-review.md` | `$ARGUMENTS` named in the body |
  | `review-plan.md`, `review-implementation.md`, `review-functional.md` | "any capable Claude model" becomes "any capable model" |
  | `REVIEW_PROTOCOL.md` | four prose mentions of the model say "the agent" |
  | `ORCHESTRATION_PROTOCOL.md` | the envelope example and the tested-releases note follow 2.18.0 |
  | `MILESTONE_WORKFLOW.md`, the operator reference | keep their tailored tails; the shared lead is replaced by their own change |
  | `workflow_protocol.py`, `workflow_protocol_test.py` | the release constant and its two assertions follow 2.18.0 (the test also follows "The agent" in an operator-document needle) |
  | `workflow_state_test.py` | one needle follows "The agent" |
  | `workflow_integration_test.py` | the command-file contract tests, the `$ARGUMENTS` and neutrality gates and the guard needles |

  A reviewer reads each against `git diff`; a record keeps no sentence it cannot support.
- **`manager` block:** `min_manager_version` 1.13.0; `downgrade_boundary.posture` states the
  per-area posture of D-Patch and that an older release reads every state, ledger and file 2.18.1 writes, that a verdict
  is not portable in both directions (`EPR-002`, `LPR-R4-001`): an `APPROVE` with a wrapped placeholder under Blocking (`- (none)`) is accepted by 2.18.1 and refused by 2.18.0
  and must be reissued after a move back, while the reverse differences (a `REVISE` with only such a placeholder, a placeholder under Optional) need no action; the text states no superset or subset relation between the two releases' accepted verdicts, and
  that `workflow-manager update` back to 2.18.0 restores the older job text and wording;
  `signals` empty; `new_work_only` empty; `gate_default_change` empty;
  `conformance.suites` computed by `release.py manager-block --release-dir <scratch> --write`
  from a staging of CP5's own content, never typed.
- `docs/release-history.md`: the 2.18.1 row (what it fixes, the posture, what stays open: 39j
  and 64c) and the "Last checked with" line; `docs/RELEASING.md`: the acceptance-matrix test
  count it states (two places) follows the measured count; no other count.
- `tools/release/release_test.py`: a 2.18.1 release class (version, release constant, the
  posture needles, the history row, the template digest, counts); the 2.18.0 class keeps
  what stays true of that release (its records and counts, its history row) and no longer
  pins the current version, release constant or posture.
- **Golden hashes:** none moves. No command file changes, so `_GOLDEN_COMMAND_FILE_SHA256`
  is untouched and the byte-identity check against the base is the gate; the template digest
  in the manifest's `templates` record is the one managed-file hash that changes.
- `docs/ROADMAP.md` row 18 is marked Current now (done with this plan) and Done at
  acceptance, not in this checkpoint.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD`
fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` is clean; the update
fixture passes; `tools/docs/check_docs.py` is clean; `workflow-manager verify .` is clean; the
tools tests pass in the zlib-ng environment; `git diff --stat <base> -- payload/.claude/commands`
is empty.
<!-- /CP5 -->

## 6. Disposition of every inventory item

"Fix" items are in the checkpoint named; the plan does not edit issues, so the orchestrator
closes or relabels each at the end.

| Id | Item | Disposition | Reason |
|---|---|---|---|
| 31a | Refuse an `APPROVE` with an Important entry | **CLOSE** | A recorded decision: the docstring and `REVIEW_PROTOCOL.md` state the `APPROVE` is deliberately not refused. Refusing is a protocol-visible change; the owner may open a design item. |
| 31b | Wrapped or prefixed placeholders | CP1 | Verified: all five forms are accepted as findings. |
| 31c | D-Courier condition 5 wording | CP4 | Still reads "it is opt-in". |
| 31d | Protocol example pairs revision 1 with round 3 | CP4 | Still present; not schema-tested. |
| 39a | Baseline undo outside the lock | CP1 | Verified at the `except` after `state_transaction`. |
| 39b | End-to-end manual `REVISE` test | CP3 | The scaffolding exists in `workflow_state_test.py`. |
| 39c | "Cannot be identified" when the ids are equal | CP4 | Comment and one sentence (OD-7). |
| 39d | `BASELINE.json` plan-stage list is sorted | CP4 | One sentence. |
| 39e | Implementation-stage "known to state" rule | CP4 | One sentence. |
| 39f | Union diff shows earlier excluded edits | CP4 | One clause. |
| 39g | `_detector` raises `TypeError` | CP2 | Verified. |
| 39h | `match` with `$` accepts a trailing newline | CP2 | Verified (both patterns). |
| 39i | CI previous-release selector ignores prereleases | CP2 | Verified; repository CI file. |
| 39j | Check (g) pin equal or at least | **DEFER** | A release-gating rule (exact versus "at least"); the owner's decision (OD-6). |
| 45a | Acceptance refusal prints the whole finding | CP1 | Verified. |
| 45b | Weak `assertNotIn(self.WID, diff)` | CP3 | Verified. |
| 52a | Freeze 2.14.0 field sets | CP3 | Verified. |
| 52b | `state_valid` pass detail | CP1 | Verified; not pinned anywhere. |
| 52c | Duplicate and stale-id refusal subtests | CP3 | Verified. |
| 52d | Manifest signal label | **CLOSE** | The label is in the published 2.15.0 manifest (immutable); the current `signals` list is empty. |
| 52e | Grep-based identity test | CP3 | Verified. |
| 52f | Recovered-role refusal names no next step | CP1 | Plain next step (OD-3). |
| 56a | `cp -a` output not in the unit's log | CP2 | Verified in the template and the CI copy. |
| 56b | `setUpModule` among the "not in the plan" causes | CP4 | Verified; `plan` refuses it. |
| 56c | Same as 56b (manual reviewer) | **CLOSE** | Duplicate of 56b. |
| 56d | "exited 0 without a failing shard row" wording | CP2 | Verified in both scheduler copies. |
| 60a | Backlog cycle detection recurses | CP2 | Needs a malformed file within the line cap (section 2). |
| 60b | Rollback restores bytes, not modes | CP2 | Lowest priority; first to move to DEFER if CP2 overruns (OD-8). |
| 60c | `?` accepted in a plain flow-list entry (#60 item 1) | CP2 | Verified: `_check_plain(..., flow=True)` refuses `:` only; `_PLAIN_FORBIDDEN` is `"[]{},"`. |
| 60d | Exact protected page path or protected prefix under `docs/items/` (#60 item 2) | CP2 | Verified: `protected_conflicts` tests only the representative `docs/items/x.md` through the prefix. |
| 60e | `declaration_conflict` before the work item is created (#60 item 3) | **DEFER** | Step 1 of `/milestone-plan` is command-file text and no command file moves (OD-9). |
| 60f | Pin a trailing comment on a key with no inline value (#60 item 4) | CP2 (tests) + CP4 (document) | Verified: accepted by the parser, pinned by no test or document. |
| 60g | Downgraded copy's page header names the old path (#60 item 5) | CP4 | One sentence in `BACKLOG_FILE.md`'s way-back section. |
| 64a | Per-record 2.18.0 rationales (both OPT-1) | CP5 | 15 records plus four with none. |
| 64b | Needles for the `COMMAND_FILES.md` sentences | CP4 | Verified: no needle matches either sentence. |
| 64c | Wrap the long guard lines | **DEFER** | OD-2: cosmetic, moves six shipped commands and their golden hashes. |
| 64d | Second OPT-1 (four more records) | **CLOSE** | Merged into 64a. |
| 64e | Needles (OPT-2) | **CLOSE** | Duplicate of 64b. |
| 64f | Empty-case bullet names the plan-stage exception | CP4 | Verified: absent. |
| 64g | Same as 64f (OPT-8) | **CLOSE** | Duplicate of 64f. |
| 64h | Stale command-file count in the operator reference (#64 first bullet) | CP4 | Verified: lines 251, 266, 267 and 1006 say 16; the directory and `workflow_integration_test.py:7034` hold 22. |

Counts: 41 items (the inventory's 35 plus the six the issue bodies add, revision 2), 32
fixed (CP1: 5, CP2: 9, CP3: 5, CP4: 11, CP5: 1, and 60f split between CP2 tests and CP4
document), 6 closed (31a, 52d, 56c, 64d, 64e, 64g), 3 deferred (39j, 60e, 64c). 32 + 6 + 3 = 41.
Section 6 now accounts for every item in the seven issues' bodies and comments.

**Issue end states** (for the orchestrator): #31 closes (31a closed as decided; the rest
fixed); #45, #52 and #56 close; #39 stays open narrowed to 39j; #60 stays open narrowed to
60e; #64 stays open narrowed to 64c.

## 7. Tests and verification summary

New tests sit in the files named in each checkpoint: `workflow_fingerprint_test.py` (31b),
`workflow_state_test.py` (39a, 52f, and CP3), `workflow_gate_policy_test.py` (45a),
`workflow_protocol_test.py` (52b, 31c, 31d), `workflow_acceptance_matrix_test.py` (60a, 60b end to end),
`workflow_state_completion_obligations_test.py` (60c, 60d, the 60f pins, and the 60f and 60g
needles), `workflow_integration_test.py` (the 31b protocol needle and the other CP4 needles) and `tools/release/release_test.py` (39g, 39h,
39i, 56a, 56d, and the CP5 class). CP5 records the measured counts of all nine suites (the
acceptance-matrix count also appears in `docs/RELEASING.md`). Nothing is tested only by
reading prose except the CP5 rationale sentences, which the reviewer reads against `git diff`.

## 8. Risks

- **`state_transaction` is the single write choke point.** A keyword that is unused by every
  other caller cannot change them; the existing transaction tests and the writer-discovery
  conformance check are in the gate, and the new keyword is exercised only by the manual
  ingest.
- **31b widens "placeholder".** A real finding could be lost if it reduced to a placeholder;
  the rule strips only punctuation, symbols and spaces at the ends and compares the whole
  remainder, and the test keeps real findings that begin with "none" or quote it.
- **A wording change breaks a needle.** Each changed message is searched for in the tests and
  documents before the edit; a pinned old tail is updated and named in the report.
- **A template change moves a digest.** The manifest record is refreshed in CP5; the
  installed copy is not touched, so `workflow-manager verify .` stays clean.
- **Scratch staging drifts from the committed manifest.** CP5 stages the committed
  `manifest.json` unmodified, which is the real check.
- **This repository runs 2.18.0.** The fixes are exercised in tests and fixtures here.

## 9. Requirements

| Id | Requirement | Checkpoints |
|---|---|---|
| R1 | The review-core defects 31b, 39a, 45a, 52b and 52f are fixed, each with a regression test shown red against the unfixed code, and `REVIEW_PROTOCOL.md`'s placeholder sentence states the leading, trailing and wrapping rule 31b enforces, pinned by a needle | CP1 |
| R2 | The backlog script reports a deep malformed chain instead of crashing, restores modes on rollback, refuses `?` in a plain flow entry and detects an exact protected page path or a protected prefix under `docs/items/` (60a to 60d), and its trailing-comment acceptance is pinned (60f tests); the release tooling, CI selector and conformance template are corrected (39g, 39h, 39i, 56a, 56d), each tested | CP2 |
| R3 | The test hardening items 39b, 45b, 52a, 52c and 52e are in place | CP3 |
| R4 | The shipped documents carry the wording of 31c, 31d, 39c to 39f, 56b, 60f, 60g, 64f and 64h, and tests pin 64b, 64f, 64h (no stale count) and the new sentences | CP4 |
| R5 | Release 2.18.1 bookkeeping: release constant and its two assertions, manifest digests, sizes, measured counts and per-record rationales including 64a, release history, per-area downgrade posture, the `manager` block | CP5 |
| R6 | The hard limits hold: no state, ledger, phase, trailer, commit-shape or protocol change; no refusal code changes; no command file moves; the installation is untouched | CP1, CP2, CP3, CP4, CP5 |

Every inventory id, and every item of the seven issues' bodies and comments (60c to 60g, 64h
included), maps to a checkpoint, CLOSE or DEFER in section 6.

## 10. Artifact classification

`docs/ai-workflow/registry/review-followups-cleanup-artifacts.json` is declared as the
earlier release-source items declared theirs (the generated template does not classify
`payload/`, `templates/`, `tools/`, `manifest.json` or the user documents). At the plan stage
the plan (`docs/ai-workflow/REVIEW_FOLLOWUPS_CLEANUP_PLAN.md`), the registry and the mapping
are protected; `payload/`, `templates/`, `tools/`, `manifest.json`, `.github/`, the user
documents (`docs/RELEASING.md`, `docs/release-history.md`, `docs/common-problems.md`) and
`docs/ROADMAP.md` are excluded. At the implementation stage `payload/`, `templates/`,
`fixtures/`, `tools/`, `manifest.json`, the user documents above, the CI file
`.github/workflows/workflow-ci.yml` (spelled out, as W12 did, ahead of the excluded `.github/`
prefix) and the declaration itself are protected; the plan, `docs/ROADMAP.md`,
`docs/ACTIVE_MILESTONE.md` and `docs/ai-workflow/` are excluded. Every path section 5 names is
classified at both stages, including this plan file; the declaration check runs at
publication and refuses otherwise.

## 11. Revision history

| Rev | Change |
|---|---|
| 1 | First plan for row 18. |
| 2 | Local plan review round 1 (`REVISE`): `LPR-R1-001` adds the six issue-body items the inventory missed (60c to 60g, 64h) with dispositions, corrects the counts, end states, R-rows and mapping; `LPR-R1-002` puts the `REVIEW_PROTOCOL.md` placeholder sentence and its needle in CP1 and lists 31b in the posture table. Optional findings accepted: `LPR-R1-O1` (D-52 says why the two phase refusals keep their text), `-O2` (31d's example becomes revision 2, round 2), `-O3` (`on_failure` for any `BaseException`, one `KeyboardInterrupt` subtest), `-O4` (the dispositions CLI listing deliberately unchanged), `-O5` (60a's chain at the cap). Nothing rejected. |
| 3 | Local plan review round 2 (`REVISE`): `LPR-R2-001` changes all four "16"s of the operator reference (lines 251, 266, 267, 1006) to 22 and adds a guard against any remaining stale count (64h, section 2, section 6); `LPR-R2-002` moves 60c's table case, 60d's predicate case and the 60f pins to `workflow_state_completion_obligations_test.py` (`BacklogParser`, `BacklogDeclarationConflict`) and the 60f and 60g needles to its `BacklogDocument`, adds that file to CP2's and CP4's `**Files:**`, and corrects section 2 and section 7. Optional `LPR-R2-O1` accepted: 60d states both callers, the always-on item-page rule, the reworded docstring and the unchanged existing tests. Nothing rejected. |
| 4 | External plan review round 1 (`REVISE`, manual): `EPR-001` makes D-Staging measure and rewrite `manager.conformance.suites` in the scratch manifest and keeps the count assertion; `EPR-002` corrects the 31b posture (D-Patch table, D-31b, CP5): an `APPROVE` with a wrapped placeholder under Blocking is accepted by 2.18.1 and refused by 2.18.0, needs reissuing after a downgrade, and has an APPROVE regression in CP1. Optional `EPR-003` accepted (60d also covers protected prefixes under `docs/items/`), `EPR-004` accepted (45a's fixture respects the 1,200-character storage cap). `EPR-005` rejected as a plan defect (OD-10). |
| 5 | Local plan review round 4 (`REVISE`): `LPR-R4-001` replaces the false "strictly larger set" opening of the 31b posture (D-Patch table, CP5 `manager` bullet) with an accurate two-direction statement: no superset or subset relation, only the APPROVE-refused-by-2.18.0 direction needs action after a downgrade. Optional `LPR-R4-O1` accepted (R2, the D-Patch backlog row and the 60d inventory row say "or a protected prefix"). |
