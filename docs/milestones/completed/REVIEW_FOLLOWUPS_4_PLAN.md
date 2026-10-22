# W18: Workflow 2.18.4 — review follow-up clean-up 4 (Revision 7)

- **Work item:** `review-followups-4` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner said go on 2026-10-22. It is row 22
  of `docs/ROADMAP.md` (status `Current` from this plan, `Done` at acceptance).
- **Issues:** RodrigoFAbreu/workflow#50, plus the "Small wording fixes for the next release" item
  under Later in the roadmap. #55 was moved out of this milestone (section 1).
- **Branch:** `milestone/review-followups-4`
- **Base commit:** `75c3749` (main after #78: the release source is Workflow 2.18.3; this
  repository's own installation is also 2.18.3, automatic gates, default `2.2`, no
  `GATE_POLICY.json`, no backlog file declared, so the prose roadmap applies)
- **Plan revision:** 7 (local review round 6 applied: RF4-L6-I01, O01, O02, resolved by moving #55 out (owner decision 2026-10-22); revision 6 applied manual external review round 1, EPR-001 to EPR-005; round 4: RF4-L4-I01, O01; round 3: RF4-L3-I01, I02, O01; round 2: RF4-L2-I01, O01, O02; round 1: RF4-L1-I01 to I03, O01, O02). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.4, a patch release (`fix:`), that clears three items:

1. **Managed conformance order.** The managed `workflow-conformance` template says its units run
   "longest first", but since 2.16.0 its queue starts the acceptance shards first, so
   `workflow_protocol_test.py` (the longest unit) starts only when the first shard ends. Measured:
   a job was observed at about 975-995 s, and a width-4 simulation over the measured medians
   (section 2) gives a queue makespan of 1050 s for that order against 874.5 s for longest
   first (lower bound max(645, 3484/4) = 871 s). The scheduler must start
   the units longest first, so the header is true.
2. **#50.** 2.14.0's downgrade posture understates the limit of moving back to 2.13.0. The
   published manifest cannot change, so 2.18.4's release history and downgrade posture state the
   real limit and the safe procedure.
3. **Wording.** For an unknown work-item id, `/retire-legacy-work-item` and
   `/resume-implementation` refuse with a `...WrongPhaseError` whose message says "names no work
   item", but their command files describe that error only as a phase problem.

Why `fix:` and not `feat:` (OD-1): no state key, phase, trailer, commit shape, protocol field,
persisted vocabulary or refusal code is added; the way back is stated in D-Patch.

### Moved out of this milestone: #55 (owner decision 2026-10-22)

#55 (a checkpoint start that its own plan forbids completing cannot be released, so
`/request-plan-amendment` is unreachable) is removed from W18 and gets its own milestone right after
this one (W19), planned fresh; it may choose the issue's other design, a separate user-confirmed
release step outside the amendment's guard. This plan carries no #55 checkpoint, test, requirement
or file, and changes neither `payload/scripts/workflow_state.py` nor `request-plan-amendment.md`.
What six review rounds learned, for W19: a live same-worktree `1f-commit` owner can reclaim a
replaced guard before the claim is unlinked and recreate the checkpoint through
`complete_checkpoint`; a failed claim cleanup leaves a live owner able to overwrite the amendment;
any refusal before the state publish must release the guard by `lease_id`; and `owner_mutation`
checks ownership, not phase. RF4-L6-I01 and RF4-L6-O01 (both about that guard window) are resolved
by this removal; RF4-L6-O02 (the arithmetic) is fixed in Goal item 1.

### Hard limits (invariants)

- **No state field, ledger, phase, trailer, commit shape or protocol change.** Refusal codes keep
  their names and no new one is added. No Controller or Manager change: `min_manager_version`
  stays 1.13.0, and the CI pin in `tools/release/manager-pin.json` must EQUAL it (owner decision
  2026-10-20 on #39); no checkpoint changes either.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`,
  `docs/ai-workflow/` managed documents, `.workflow-manager/`, the managed blocks of `CLAUDE.md`
  and `.gitignore`, and `.github/workflows/workflow-conformance.yml`. Fixes go to `payload/`,
  `templates/`, `tools/`, `docs/` user documents, `.github/workflows/workflow-ci.yml` (this
  repository's own CI, not the installation) and `manifest.json`.
- **Size:** three checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test, shown to fail against the unfixed text first
  (the "red first" rule); the nine payload suites from a staged fixture; the `tools/release`
  tests (in the zlib-ng environment); the `tools/docs` tests and checker; `check-manager-block`
  with `--manager-releases`; `workflow-manager verify .` clean. Every command form is copied
  from `docs/RELEASING.md`, "Verification commands".
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against
  `git diff` (CP3).

## 2. Facts this plan relies on (re-checked against `75c3749`)

- **The queue today** (`templates/.github/workflows/workflow-conformance.yml`): with `shards > 0`
  the units are the acceptance shards, then the other suites in `suites=` order. Width is
  `min(width_cap, nproc)` = 4, so the four shards fill the width and `workflow_protocol_test.py`
  (median 645 s) starts when the first shard ends (about 405 s): 405 + 645 = 1050 s of queue
  critical path (a simulated makespan from medians; the 975-995 s above is the observed range of
  whole-job wall time per run, a different measure, so only the simulated figures are compared,
  here and in the test). `.github/workflows/workflow-ci.yml` carries the same step twice
  (`release-source-conformance`, `update-fixture`); `tools/release/release_test.py` pins both to
  the template byte for byte (`test_the_step_is_the_templates_step_over_the_staged_fixture`,
  `test_the_update_fixture_job_runs_the_same_step_over_the_updated_repository`).
- **Measured durations** (median seconds per unit over the twelve green runs of the managed job,
  2026-10-14 to 2026-10-21; the per-run timings file is a scratch artifact of the investigation
  and is not in the repository, so the table in the CP1 test is the durable record). Each figure
  keeps its unit's identity: `workflow_protocol_test.py` 645, `workflow_state_test.py` 486,
  `acceptance-1of4` 463.5, `acceptance-2of4` 405, `acceptance-3of4` 420.5, `acceptance-4of4` 439,
  `workflow_gate_policy_test.py` 335, `workflow_fingerprint_generalization_test.py` 218,
  `workflow_state_completion_obligations_test.py` 39, `workflow_integration_test.py` 15,
  `workflow_fingerprint_test.py` 13, `workflow_test_harness_test.py` 5. The shards are **not**
  in decreasing order of their index (shard 2 is the shortest), which is why the start order
  below names them one by one. The whole acceptance suite unsharded is about the sum of the four
  shards (1728 s). Width-4 simulation over these figures (EPR-001): 1050 s for the 2.18.3 order
  (shards in index order, then the suites), 902.5 s for protocol, state, then the shards in index
  order, and 874.5 s for decreasing duration (lower bound 871 s).
- **The scheduler tests** (`ConformanceTemplate` and `WorkflowCI` in `release_test.py`) pin
  `units[:2] == ["acceptance-1of2", "acceptance-2of2"]` (the stale order) and, unsharded,
  `starts == SUITES`, `started[0] == ACCEPTANCE`, and the first four starts.
- **#50.** 2.14.0 admits `optional_findings` in the bundle-generation-record field sets; 2.13.0
  re-validates committed generation-record commits and refuses one carrying it
  (`MalformedBundleGenerationRecordCommitError`). The 2.15.0 text already states the same limit
  for `review_round_counts`; the 2.14.0 text and manifest posture say a clean `git diff HEAD` is
  enough.
- **Command-file pins.** `workflow_integration_test.py` keeps a content hash for each of
  `resume-implementation.md` and `retire-legacy-work-item.md`; editing them updates their rows with
  an intentional-change comment. The six user-only guard lines are pinned by phrase; they are not
  touched.

## 3. Design decisions

### D-Patch: the version is 2.18.4, `fix:`

`manifest.json` `workflow_version` 2.18.4; `WORKFLOW_RELEASE` and its two pinned assertions in
`workflow_protocol_test.py` follow, with the matching `ORCHESTRATION_PROTOCOL.md` edits (tested
releases list, envelope example, protocol-1.5 note); the protocol version stays.

**Downgrade posture.** 2.18.4 writes no state, ledger or file an older release cannot read: it
changes a CI template, two command files' wording and release bookkeeping. `workflow-manager update`
back to 2.18.3 restores the older job order and the older wording. The posture also carries the #50
correction (D-Downgrade-50).

### D-Order: a fixed start order from the measured durations

The step keeps `suites=` (the summary and the manifest's order), and builds `units` from a fixed
`longest` list written next to it:

`workflow_acceptance_matrix_test.py workflow_protocol_test.py workflow_state_test.py
acceptance-1of4 acceptance-4of4 acceptance-3of4 acceptance-2of4 workflow_gate_policy_test.py
workflow_fingerprint_generalization_test.py`

a list of **unit names**, in decreasing measured duration (the table in section 2). The first name
is the whole acceptance suite: it is a unit only when `shards = 0`, where it is the longest (about
1730 s) and so goes first; with `shards = 4` it names no unit and is skipped. The four shard units
are named one by one in the order 1, 4, 3, 2, because their durations are not in index order.
The step builds `units` as it does today (the shards, then the other suites in `suites=` order),
then reorders: every name of `longest` that is a unit of this run, in `longest` order, and then
every other unit in the order it already had. A name that is not a unit of this run is skipped,
so a changed shard count (the names say `of4`) or a suite added to `suites=` without an update
here still runs every unit, only in a slower order. The duration table sits in a comment above
the list; the comment also says that the shard-to-duration assignment rests on the planner's
greedy test-count binning, so a change to the planner's binning or to the acceptance tests can
change which shard is longest, and the list and the test table are then re-measured together.
Everything else is unchanged: width, shards, the coverage gate, isolation, the one heredoc text
and the summary. The header paragraph says "longest first, in a fixed order taken from measured
durations".

**Why fixed (OD-2).** A job cannot know durations before it runs; an adaptive order would add
state and a failure mode to a gate. A stale fixed order is harmless to correctness (only wall
time) and a test pins the claim, below.

**Proof.** The scheduler tests are extended, not weakened. The stale `units[:2]` pins become the
new order for every shard count; a new test holds the measured table of section 2 **keyed by unit
name** and (a) asserts the sharded start order of the step equals the units sorted by decreasing
measured seconds (so shards 1, 4, 3, 2), (b) derives the width-4 queue simulation from the same
table for the old order, the index-order variant and the new order, and asserts the new makespan
is within 1% of the lower bound `max(longest unit, total / width)` (874.5 against 871) and at least
120 s shorter than the old (1050), (c) asserts every name in `longest` is either a suite in
`suites=` or a unit name of the form `acceptance-<i>of<N>` with `N` equal to the step's `shards=`
(and, for `shards = 0`, the whole acceptance suite), and appears once, (d) runs the step with
`longest` emptied and with a shard count that no name matches and shows every unit still runs
exactly once, the coverage gate passing, and (e) runs it with `shards=0` and asserts the whole
acceptance suite starts first. `test_width_is_never_exceeded_and_longest_run_first` keeps its width
assertions and gains the measured-order assertion. The two byte-for-byte pins are unchanged and
now pin the new text in the three places.

### D-Downgrade-50: the real limit and the safe procedure

The 2.18.4 release history row and manager posture state: committed generation records that carry
`optional_findings` are refused by 2.13.0, so a clean `git diff HEAD` (the 2.14.0 text) is not
enough. Move back below 2.14.0 only when (a) every item's pending state is committed and shows no
`optional_findings` hunk, and (b) no non-terminal item has a committed bundle-generation-record
commit (ordinary or recovered) whose `optional_findings` differs from its first parent's, in its open
implementation-stage provenance interval; if one has, finish that item's implementation approval, or accept it, under the newer
release first. The text gives a command that compares the item's field between each generation-record commit
and its first parent, because `git log -S`/`-G` only see changes to the count or lines of the
literal `optional_findings` and miss a commit that adds a finding to a ledger already present or
changes a disposition or reference in it (`optional_findings` is a dict keyed by finding id). Over
the item's interval `<base_commit>..HEAD` (a superset of the open provenance interval, so it can
only over-report):

```
for c in $(git log --format=%H --grep '^Workflow-Bundle-Generation-Record:' <base_commit>..HEAD -- docs/ai-workflow/WORKFLOW_STATE.json); do
  python3 -I - "$c" <work_item_id> optional_findings review_round_counts <<'PY'
import json, subprocess, sys
c, wid, *fields = sys.argv[1:]
def item(rev):
    try:
        raw = subprocess.check_output(["git", "show", f"{rev}:docs/ai-workflow/WORKFLOW_STATE.json"])
    except subprocess.CalledProcessError:
        return {}
    return json.loads(raw)["work_items"].get(wid, {})
new, old = item(c), item(c + "^")
for f in fields:
    if (f in new, new.get(f)) != (f in old, old.get(f)):
        print(c, f)
PY
done
```

The comparison includes key presence (EPR-005): a key that appears with a null or empty value is a
difference, as the 2.13.0 field-diff check sees it. Any line it prints is a commit the older release refuses (`review_round_counts` only matters for
a move below 2.15.0). CP3 runs it on a scratch repository holding such a commit and on one
without, and the scratch repository includes the "key already present, value changed" commit and
a commit that adds the key (also with a null value), and the release test pins the wording and that the command reports
all of them. The sentence on `review_round_counts` for 2.15.0 is already stated in the 2.15.0
text. The 2.14.0 manifest and history row are not
edited; the release history keeps that row as published and the 2.18.4 row corrects it.
The existing regressions for committed key-bearing ordinary and recovered records
(`test_optional_findings_residue_rides_into_the_ordinary_record_commit` and the recovered one)
already pin the current field sets; no new code test is needed for the wording.

### D-Wording: say what the unknown-id refusal is

`retire-legacy-work-item.md` step 3 and `resume-implementation.md` step 3 each name the error as
phase-only. Each gains one clause: the same `...WrongPhaseError` is raised, with the message
"<id> names no work item", for an id that is not a key of `work_items` (the commands refuse that
earlier in step 1 or 0 when they can, and the writer repeats it). The user-only guard lines are not
touched. A test pins the clause in both files and that the existing guard phrases remain.
`docs/ROADMAP.md` loses the Later paragraph.

### D-Staging: scratch staging for CP1 and CP2 (the procedure W16 and W17 used)

`release.py stage-conformance` and `tools/release/release_test.py` verify the manifest against the
tree, and CP1 and CP2 change shipped files whose digests the committed manifest records only at CP3.
So each verifies in a disposable clone (a full `git clone` of this repository under `$TMPDIR`): a
scratch script recomputes `sha256` and `size` of every `artifacts` and `templates` record whose
file differs from its record, measures and rewrites `manager.conformance.suites` (the same
discovery `release.py manager-block --release-dir <scratch> --write` uses), commits it in the clone,
and the "Verification commands" blocks run from there. No rationale is touched in the scratch.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
|---|---|---|
| OD-1 | The version: patch 2.18.4 (`fix:`) or minor | **Patch, `fix:`.** No protocol or persisted-vocabulary change is needed (see Goal); say otherwise in review and the release becomes a `feat:` minor. |
| OD-2 | Order: a fixed measured list or an adaptive order | **A fixed, documented list**, pinned by a test against the measured table. |
| OD-3 | The manager CI pin | **No change.** `manager-pin.json` (1.13.0) equals `min_manager_version` (1.13.0). |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does not
exist in this repository's release source).

## 5. Checkpoints

Three checkpoints. CP1 and CP2 verify as D-Staging says; CP3 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The managed conformance runs longest first | - | 3 | 1 |
| CP2 | The unknown-id wording in the two command files | CP1 | 1 | 1 |
| CP3 | Release 2.18.4 | CP2 | 3 | 1 |

<!-- CP1 -->
### CP1 — The managed conformance runs longest first

**Files:** `templates/.github/workflows/workflow-conformance.yml`,
`.github/workflows/workflow-ci.yml`, `tools/release/release_test.py`, `docs/RELEASING.md`.

- **Template** (D-Order). Red first: the extended scheduler tests (the new sharded start order and
  the measured-table test) fail against the unedited step, then pass after the edit. The header
  says "longest first, in a fixed order taken from measured durations". **Done:** the failure is
  recorded; `git diff` of the template is the header, the `longest` list with its measured-seconds
  comment, and the `units` construction only; the heredoc text is unchanged.
- **This repository's CI.** The same edit, byte for byte, in both copies of the step in
  `.github/workflows/workflow-ci.yml` (`release-source-conformance` and `update-fixture`); the
  existing pins that make the three copies equal stay and pass (they are the fence of the CI file,
  which the `.github/` prefix leaves outside `technical_approval`). `.github/workflows/workflow-conformance.yml`
  (the installation) is untouched: `git status` shows it clean.
- **Tests.** In `tools/release/release_test.py`: the stale `units[:2]` pins in both classes become
  the new order; the measured table test (keyed by unit name), the simulation, the name-membership test, the
  fallback test (emptied `longest`, unmatched shard count) and the `shards=0` test of D-Order are added to `ConformanceTemplate`; `WorkflowCI`
  gains the sharded start-order assertion over the staged fixture.
  `test_width_is_never_exceeded_and_longest_run_first` keeps every assertion it has.
- **`docs/RELEASING.md`:** the scheduling paragraph says longest first instead of "acceptance
  shards first".

**Verification:** D-Staging in a disposable clone: the nine suites, the `tools/release` and
`tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — The unknown-id wording in the two command files

**Files:** `payload/.claude/commands/retire-legacy-work-item.md`,
`payload/.claude/commands/resume-implementation.md`,
`payload/scripts/workflow_integration_test.py`, `docs/ROADMAP.md`.

- **Wording** (D-Wording): one clause in each file's step 3; the six user-only guard lines intact.
- **Tests, red first:** a needle test in `workflow_integration_test.py` pins the clause in both
  files and that the existing guard phrases are still present; the two content-hash rows are
  updated with an intentional-change comment.
- **Roadmap:** the "Small wording fixes for the next release" paragraph under Later is removed; row
  22 drops #55, and the #55 line of the issue table names W19 (the W19 row itself is placed by the
  orchestrator in its own roadmap change).

**Verification:** D-Staging in a disposable clone.
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Release 2.18.4

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/RELEASING.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.18.4 with its two pinned assertions in
  `workflow_protocol_test.py` and the matching `ORCHESTRATION_PROTOCOL.md` edits; the protocol
  version stays.
- `manifest.json` 2.18.4: `workflow_version`; `sha256` and `size` of every record changed in CP1 to
  CP3 (the conformance template, `workflow_integration_test.py`, `retire-legacy-work-item.md`,
  `resume-implementation.md`, `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`); `counts` unchanged; a `review-followups-4 (workflow-2.18.4)`
  sentence on **each** changed artifact record, true of THAT file and read against
  `git diff 75c3749..HEAD -- <file>`; the `manager` block: `min_manager_version` 1.13.0 (equal to
  the CI pin), `downgrade_boundary.posture` per D-Patch and D-Downgrade-50, `signals`,
  `new_work_only` and `gate_default_change` empty, `conformance.suites` (digests, sizes and test
  counts) measured by `release.py manager-block --release-dir <scratch> --write` from a staging of
  CP3's own content, never typed.
- `docs/release-history.md`: the 2.18.4 row (it closes #50 only and leaves #55 open for W19; names the order, the real 2.14.0 limit
  with the safe procedure, the wording fix and the way back) and the "Last checked with" line; `docs/RELEASING.md`: any test count it states follows the measured
  count, no other change.
- `tools/release/release_test.py`: a 2.18.4 release class (version, release constant, the posture
  needles for both corrections, the history row, counts, the safe-procedure command checked on a
  scratch repository with a commit that adds the key, a commit that changes an existing ledger's value, and without either); the 2.18.3 class
  keeps what stays true of that release and no longer pins the current version, constant or
  posture.
- `docs/ROADMAP.md` is not written by this checkpoint: row 22 is `Current` from this plan and
  becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD`
fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs` is
clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP3 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
|---|---|---|---|
| Row 22, managed order | The queue starts the units longest first; header true; three copies updated and pinned | CP1 | D-Order |
| #55 | Moved to its own milestone (W19); stays open | - | section 1 |
| Wording (Later) | The two command files describe the unknown-id refusal | CP2 | D-Wording |
| #50 | Release history and posture state the real 2.14.0 limit and the procedure | CP3 | D-Downgrade-50 |
| Release | 2.18.4 bookkeeping, closes #50 only | CP3 | D-Patch |

The artifact declaration `docs/ai-workflow/registry/review-followups-4-artifacts.json` is generated
by `workflow_state.generate_artifacts_declarations`; the plan, the registry and the mapping are its
plan-stage protected paths, and self-review checked that every path named in a Files paragraph is
classified at both stages.
