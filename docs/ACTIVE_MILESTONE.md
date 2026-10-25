# Active Milestone

## Milestone

**In progress.** W25: `command-wording` (`process`, governing version `2.2`), branch `milestone/command-wording`,
roadmap row 26b (RodrigoFAbreu/workflow#100 wording and message items, and the documents part of #105). Plan:
`docs/ai-workflow/COMMAND_WORDING_PLAN.md` (revision 3, approved by gate policy). The goal is Workflow 2.19.2, a
`fix:` patch that makes the checkpoint-start command's documents and two messages say what the code does. The
previous milestone, W24 `interleaving-pins`, is accepted (Workflow 2.19.1).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The documents, the message and their pins | **complete** |
| CP2 | Release 2.19.2 | **complete** |

## Verified state

- CP1: W1, W2, W3 (invariants page), W5 and M1/M1b (the first `AmendmentCheckpointActiveError` raise and the
  unclaimed-`IN_PROGRESS` release refusal) edited; seven new/changed pins (five M1/M1b tests in
  `workflow_state_test.py`, three in `workflow_integration_test.py`, two in `tools/release/release_test.py`), each
  shown red against its restored `bebf2d2` file and green on the candidate, recorded in
  `docs/ai-workflow/COMMAND_WORDING_EVIDENCE.md`. The production diff of `workflow_state.py` is message text, one
  optional keyword and the choice of the named checkpoint.
- Verified in a disposable clone (D-Staging): the nine suites (the state suite as the whole chunk under the orphan
  wrapper, no orphan beyond Git), the `tools/release` (275) and `tools/docs` tests, `check_docs.py`,
  `check-manager-block`; `workflow-manager verify .` is clean.

- CP2: `manifest.json` 2.19.2 (nine changed records with their digests, sizes and a `command-wording
  (workflow-2.19.2)` sentence each; posture with the D-Downgrade clauses; suite counts measured by `release.py
  manager-block --release-dir ... --write`: `workflow_state_test.py` 1244, `workflow_integration_test.py` 364),
  `WORKFLOW_RELEASE` 2.19.2 with its two pinned assertions and the protocol document edits, the 2.19.2 history row
  and the two "Last checked with" lines, and `CommandWordingReleaseTest` (the 2.19.1 class keeps what stays true of
  it). Verified in a scratch clone of the committed content: `tools/release` (277) in the zlib-ng environment,
  `tools/docs` (34), `check_docs.py`, `check-manager-block` and `release.py build --commit HEAD`; the nine suites
  from a stock `stage-conformance` fixture (see the implementation bundle's `TEST_RESULTS.md`).
- Rerun at implementation revision 2 (HEAD `fe85528`, before this checklist): `stage-conformance` exit 0; the nine
  suites all OK (`workflow_acceptance_matrix_test.py` 453, skipped 20; `workflow_protocol_test.py` 344, skipped 19;
  `workflow_state_test.py` 1244, skipped 1; `workflow_gate_policy_test.py` 316; `workflow_fingerprint_generalization_test.py`
  142; `workflow_state_completion_obligations_test.py` 193; `workflow_integration_test.py` 364; `workflow_fingerprint_test.py`
  283; `workflow_test_harness_test.py` 27); the `workflow_state_test.py` chunk under the orphan wrapper OK, exit 0; `tools/release`
  277 OK under the zlib-ng runtime; `tools/docs` 34 OK; `check_docs.py` exit 0; `check-manager-block` ok; `workflow-manager verify .`
  exit 0 (`installation matches workflow 2.19.1`).

## Functional review checklist

Scope: the checkpoint-start command's documents and two messages (plan section 1: W1 to W5 and M1, with M1b). No
behaviour changes: the review checks wording and the pins that hold it. Implementation revision 2 (reviewed head
`5f585b1`); the evidence commit for this checklist is named in the reply that announced it.

### Setup

- The checkout at the checklist's evidence commit, branch `milestone/command-wording`, clean working tree.
- `git`, and `python3` for the nine suites and the `tools/docs` tests. The `tools/release` tests and
  `check-manager-block` run with the pinned zlib-ng runtime, `~/.cache/wf-release-venv/bin/python` (Python 3.12,
  zlib-ng 2.2.5), never the system Python (`docs/RELEASING.md`, "Building locally").
- `workflow-manager` on `PATH`, with the installed release's assets in the release cache (`--release-cache` or
  `$WORKFLOW_MANAGER_RELEASE_CACHE`) for an offline `workflow-manager verify .`.
- The Manager checkout at `~/Workspace/workflow-manager`, only for flow f3 (the orphan wrapper).
- Every write goes under `$TMPDIR`. Nothing in the checkout is written: a flow that needs an edited file copies the
  tree first.
- No network, no GitHub, no `gh`, no `claude`, `codex` or `ssh`. No flow here needs them. The base commit `bebf2d2`
  and `HEAD` must both be present in the local history.
- Test data: none to seed. Each flow builds its own scratch fixture under `$TMPDIR`.

### Flows

Each flow names its workspace. Flows f1 to f6 are the plan's section 7; f7 and f8 cover W1, W5 and the wording
reviewed by reading.

**f1. The new pins pass on the candidate.** Workspace: the staged conformance fixture of the candidate.

```bash
python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"
cd "$TMPDIR/fixture/scripts" && python3 -B -m unittest -v \
  workflow_state_test.TestReleaseCheckpointStartCommand workflow_state_test.TestAmendmentResolutionReservation \
  workflow_state_test.TestRequestPlanAmendment workflow_integration_test.TestReleaseCheckpointStartCommandFile \
  workflow_integration_test.TestUserOnlyCommandListings
```

Expected: every test `ok`, among them the five M1/M1b tests
(`test_m1_the_first_raise_names_an_in_progress_checkpoint`, `test_m1_the_two_added_facts_belong_to_the_in_progress_raise_only`,
`test_m1_epr001_adoption_is_promised_only_when_the_pointer_names_the_entry`,
`test_m1_epr002_the_guidance_for_a_claim_on_another_checkpoint_is_true`,
`test_m1b_the_unclaimed_release_refusal_states_the_pointer_condition`), and the unedited `test_c4_*` and `test_c5_*`.

**f2. Each changed text is pinned: it fails against its `bebf2d2` text (cases E1 to E5).** Workspace: one fixture
copy per case, with one file restored. The fixture is rooted at the shipped tree, so the restore path drops the
`payload/` prefix of `git show`.

| Case | Restore (`git show bebf2d2:<path>` into the copy) | Must fail |
| --- | --- | --- |
| E1 | `payload/scripts/workflow_state.py` → `scripts/workflow_state.py` | the five M1/M1b tests |
| E1, second subcase | only the unclaimed-`IN_PROGRESS` refusal's text in `scripts/workflow_state.py` | `test_m1b_the_unclaimed_release_refusal_states_the_pointer_condition` alone |
| E2 | `payload/docs/ai-workflow/COMMAND_FILES.md` → `docs/ai-workflow/COMMAND_FILES.md` | `TestUserOnlyCommandListings.test_the_command_files_row_states_the_number_of_flagged_commands` |
| E3 | `payload/.claude/commands/release-checkpoint-start.md` → `.claude/commands/release-checkpoint-start.md` | `TestReleaseCheckpointStartCommandFile.test_the_released_bullet_states_the_work_items_one_claim_in_any_worktree` |
| E4 | `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md` → `docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md` | `TestUserOnlyCommandListings.test_the_operator_reference_names_every_user_only_command` |
| E5 | `docs/CONCURRENCY_INVARIANTS.md` in a copy of the checkout (`git archive HEAD`), restored from `bebf2d2` | `tools.release.release_test.ConcurrencyInvariantsReleaseWindowRowTest` (`failures=2`) |

E5 runs in a copy, not a stash in the checkout, because the sandbox forbids writes inside the clone. Run each case's
named tests from the copy's `scripts/` with `python3 -B -m unittest`, and the control (no restore) with all of them
green.

**f3. The orphan wrapper leaves no orphan beyond Git.** Workspace: the staged fixture, from `scripts/`.

```bash
python3 -I -S -B ~/Workspace/workflow-manager/tests/parallel/reaper.py --report "$TMPDIR/reaper-state.json" \
  --chunk-id state-full -- python3 -B workflow_state_test.py
```

Expected: `Ran 1244 tests`, `OK (skipped=1)`, wrapper exit 0, `chunk_status: 0`. The report lists only `[git]`
processes and `git maintenance run --auto --quiet --detach`.

**f4. The nine payload suites.** Workspace: the staged fixture. Run the block of `docs/RELEASING.md`, "The nine
payload suites", verbatim. Expected, one `OK` per suite: `workflow_acceptance_matrix_test.py` (skipped 20),
`workflow_protocol_test.py` (skipped 19), `workflow_state_test.py`, `workflow_gate_policy_test.py`,
`workflow_fingerprint_generalization_test.py`, `workflow_state_completion_obligations_test.py`,
`workflow_integration_test.py`, `workflow_fingerprint_test.py`, `workflow_test_harness_test.py`.

**f5. The tools, docs and Manager block.** Workspace: the checkout, with the zlib-ng runtime for `tools/release`.

```bash
~/.cache/wf-release-venv/bin/python -m unittest discover -s tools/release -p '*_test.py'
python3 -m unittest discover -s tools/docs -p '*_test.py'
python3 tools/docs/check_docs.py
python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json
workflow-manager verify .
```

Expected: `tools/release` `OK` (277 tests); `tools/docs` `OK` (34); `check_docs.py` exit 0; `ok: 2.19.2 carries a valid
manager block that matches the measurement`; `workflow-manager verify .` exit 0, `installation matches workflow 2.19.1`.

**f6. The production diff is message text only.** Workspace: the checkout, read-only.

```bash
git diff bebf2d2 -- payload/scripts/workflow_state.py
git diff --stat bebf2d2..HEAD -- payload/ manifest.json docs/ tools/
```

Expected: the added lines of `workflow_state.py` are the text of two messages, the `entry_may_be_unclaimed` keyword of
`_release_start_next_step` and the `current_checkpoint_id in in_progress_ids` choice. No lock, `flock`, `os.link`,
claim or `resolve_claim` line is added. The 2.19.0 and 2.19.1 history rows are unchanged.

**f7. The user-only commands are seven, and the documents say so (W1, W5).** Workspace: the checkout, read-only.

```bash
grep -l '^disable-model-invocation: true' payload/.claude/commands/*.md | wc -l
```

Expected: `7`. `COMMAND_FILES.md`'s `disable-model-invocation` row reads "`true` (seven commands)", and the
`**User-only commands**` bullet of `WORKFLOW_V2_1_OPERATOR_REFERENCE.md` lists all seven: `/accept-milestone`,
`/adopt-gate-policy`, `/approve-review`, `/release-checkpoint-start`, `/request-plan-amendment`,
`/resume-implementation`, `/retire-legacy-work-item`.

**f8. Reading check (manual, not automated).** Read each changed sentence against the code it describes:

- `release-checkpoint-start.md` step 2, the `released` bullet: "the work item has no claim in any worktree". The code
  (`observe_checkpoint_start_release`, `resolve_claim` over the git common directory) tests one shared claim, and a
  claim held by another worktree is refused with `CheckpointOwnedByOtherWorktreeError`, never `released`.
- `workflow_state.py`, the first `AmendmentCheckpointActiveError` raise: the named checkpoint is
  `current_checkpoint_id` when it is `IN_PROGRESS`, else the first `IN_PROGRESS` id in dict order. The release refusal
  states the pointer condition, and the claim for another checkpoint is named.
- `docs/CONCURRENCY_INVARIANTS.md`, release-window row: the recovery cell gives the command's act to the command and the
  re-classification to the engine; the tests cell puts `test_p4_*` under `::TestReleaseCheckpointStartCommand`.
- `docs/release-history.md`, the 2.19.2 row: the way back to 2.18.7 (D-Downgrade).

### Known limitations and out of scope

- Behaviour is unchanged. `_classify_checkpoint_start`'s two `COMPLETE` refusals are not edited (plan section 2: both are accurate).
- Not done here: the first half of #105 (two uncovered statements of the `owner_mutation` pin). It stays open.
- The 2.18.7 finishing path (D-Downgrade) is documentation only. No flow runs it.
- A claim held by another worktree is covered by the refusal text and the pins, not by a live two-worktree run.
- Release publication (the 2.19.2 tag, release assets, the `workflow-manager` pin) happens after acceptance and merge,
  and is outside this checklist. The flows above cannot reach GitHub.
- Sandbox adaptations: E5 runs in a copy (above). f3 needs the Manager checkout; if it is absent, record it as an
  environment result, not a product defect.

## Next action

Functional review. Run the flows above and place findings at the feedback file named by
`python3 scripts/workflow_fingerprint.py --resolve-feedback-path command-wording` (`functional_review_path`).
Once testing is clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint `COMPLETE`,
and both are. If testing produces findings, `/apply-functional-review` routes each one: the bounded branch for a
same-scope fix, the broad branch for new or wider scope.
