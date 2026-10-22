# Active Milestone

## Milestone

**In progress** (self-reviewing the implementation). W18: `review-followups-4` (`process`,
governing version `2.2`), branch `milestone/review-followups-4`, roadmap row 22
(RodrigoFAbreu/workflow#50). Plan: `docs/ai-workflow/REVIEW_FOLLOWUPS_4_PLAN.md` (revision 7,
approved by gate policy). The goal is Workflow 2.18.4, a patch release (`fix:`). The previous milestone, W17 `review-followups-3`, is
accepted (its record is in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The managed conformance runs longest first | **complete** |
| CP2 | The unknown-id wording in the two command files | **complete** |
| CP3 | Release 2.18.4 | **complete** |

### CP1 verified state

- The managed conformance step (`templates/.github/workflows/workflow-conformance.yml`, and the
  same text in both steps of `.github/workflows/workflow-ci.yml`) builds its queue from a fixed
  `longest` list taken from measured durations, with the duration table in a comment; a name that
  is not a unit of the run is skipped, and every other unit keeps its order. The header says
  "longest first, in a fixed order taken from measured durations". `docs/RELEASING.md` says the
  same.
- `tools/release/release_test.py`: the stale `units[:2]` pins follow the new order; new tests pin
  the measured table (start order, width-4 simulation within 1% of the lower bound and 120 s under
  the old order), the names in `longest`, and the fallback for an emptied or unmatched list.
  Red first: 8 failures against the unedited step.
- Verified in a disposable clone (D-Staging); the results are in the implementation bundle.

### CP2 verified state

- Step 3 of `retire-legacy-work-item.md` and `resume-implementation.md` each gain one clause: the
  same `...WrongPhaseError` is raised, with the message "<id> names no work item", for an id that
  is not a key of `work_items`. The user-only guard lines are untouched.
- `workflow_integration_test.py`: `test_the_unknown_id_refusal_is_described_in_step_three` pins the
  clause and the guard phrases (red first: 2 failures before the wording); the two content-hash
  rows follow with an intentional-change comment.
- `docs/ROADMAP.md`: the Later "Small wording fixes" paragraph is removed; row 22 drops #55 and the
  #55 issue-table line names W19.
- Verified in a disposable clone (D-Staging): the nine suites pass (the integration suite after
  re-wrapping the clause to the 90-column limit), `tools/docs` tests and `check_docs.py` pass.

### CP3 verified state

- `WORKFLOW_RELEASE` is 2.18.4 with its two pinned assertions and the `ORCHESTRATION_PROTOCOL.md`
  edits (tested-releases list, envelope example, protocol 1.5 note); the protocol version stays 1.5.
- `manifest.json` 2.18.4: digests and sizes of the seven changed records (the conformance
  template, the two command files, `workflow_integration_test.py`, `workflow_protocol.py` and its
  test, `ORCHESTRATION_PROTOCOL.md`), a `review-followups-4 (workflow-2.18.4)` sentence on each of
  the six artifact records (the template has no rationale), the posture (job order, wording, the
  real 2.14.0 limit, the safe procedure and its command), and `conformance.suites` measured by
  `release.py manager-block` from a staging of this content (integration suite 348 -> 349).
- `docs/release-history.md`: the 2.18.4 row (closes #50, leaves #55 open) and "Last checked with".
- `tools/release/release_test.py`: `ReviewFollowups4ReleaseTest` (version, constant, counts,
  digests, sentences, posture, row, and the comparison command run on scratch repositories with a
  commit that adds the key, one that changes a ledger's value, one that adds a null key, and none);
  the 2.18.3 class keeps only what stays true of that release.
- Verified in a disposable clone (D-Staging): nine suites from a `stage-conformance` fixture,
  `tools/release` tests (263, zlib-ng environment), `release.py build`, `check-manager-block`,
  `tools/docs` tests and checker; `workflow-manager verify .` clean here.

### Self-review of the full diff

- The template record's `derivation` lists every change to the managed conformance step, but
  CP3 left 2.18.4 out of it (the template has no rationale, so the sentence check skipped it):
  it now ends with a `review-followups-4 (workflow-2.18.4)` clause, and
  `ReviewFollowups4ReleaseTest` pins it (red first: 1 failure against the CP3 manifest).
- The 2.18.4 release-history row wrote `"<id> names no work item"` as bare text, which GitHub
  renders as an HTML tag and drops, so the sentence lost the id: it is now a code span.
- No other finding: the three step copies are equal, the reorder keeps every unit exactly once,
  the counts and digests match, and nothing in the installation was touched.

## Functional review checklist

This milestone changes workflow files only (no app), so every flow below runs offline from a
scratch directory; none needs a pull request, `gh`, `claude`, `codex`, `ssh` or the network. The
product clone is read-only: write only under `$TMPDIR`. Use `python3 -B` and run from the
repository root unless a step says otherwise.

### Setup

- Branch `milestone/review-followups-4`, clean working tree, `export T=$(mktemp -d)`.
- No feature flags or seed data. The `tools/release` tests need the pinned zlib-ng Python and are
  out of reach in a sandbox without it: flow 6 is skipped there and the implementation bundle's
  recorded result stands.

### Flows

1. **The conformance step orders longest first (CP1).**
   Extract the step's `run:` script from `templates/.github/workflows/workflow-conformance.yml`
   (lines from `suites=` to just before `run_suite() {`), set `GITHUB_WORKSPACE=$T` and print
   `$units` (or run `sed -n '/^ *longest=/p'` and read it).
   Expected: with `shards=4` the start order follows the `longest` list:
   protocol, state, acceptance-1of4, 4of4, 3of4, 2of4, gate_policy, fingerprint_generalization,
   then the rest in `suites=` order; each unit appears exactly once.
2. **A stale or empty `longest` degrades safely.**
   Repeat flow 1 with `longest=""`, then with `longest="no_such_unit workflow_state_test.py"`.
   Expected: empty -> the original order unchanged; unmatched name skipped, `workflow_state_test.py`
   first, no duplicates, no unit lost.
3. **The three copies of the step are equal.**
   `diff` the step text in the template against both steps of `.github/workflows/workflow-ci.yml`
   (the CI file is the release source's own, not the managed block).
   Expected: the added `longest` block and `ordered` loops are identical in all three.
4. **The unknown-id wording (CP2).**
   `grep -n "names no work item" payload/.claude/commands/retire-legacy-work-item.md
   payload/.claude/commands/resume-implementation.md`.
   Expected: step 3 of each says the same `...WrongPhaseError` is raised with the message
   "`<id>` names no work item" for an id that is not a key of `work_items`; the user-only guard
   lines are unchanged (`git diff 75c3749..HEAD -- payload/.claude/commands/` shows one added
   clause per file).
5. **The nine payload suites pass (CP1-CP3).**
   Run the "nine payload suites" block of `docs/RELEASING.md` "Verification commands" with
   `TMPDIR=$T`. Expected: every suite exits 0 (long: the acceptance suite is about 30 minutes;
   run the others, or one shard, if time is short, and say which).
6. **Release 2.18.4 is consistent (CP3).**
   `python3 tools/release/release.py check-manager-block` and
   `python3 -m unittest discover -s tools/release -p '*_test.py'` (zlib-ng Python).
   Expected: both pass. Then `python3 -c "import json;print(json.load(open('manifest.json'))['version'])"`
   -> `2.18.4`, and the `docs/release-history.md` 2.18.4 row shows the quoted id
   `<id> names no work item` as a code span, closes #50 and leaves #55 open.
7. **Docs checks.** `python3 -m unittest discover -s tools/docs -p '*_test.py'` and
   `python3 tools/docs/check_docs.py`. Expected: both pass.
8. **The installation is untouched.** `workflow-manager verify .` (skip if the tool is not on
   `PATH`) and `git diff 75c3749..HEAD --stat -- .claude scripts docs/ai-workflow/*.md` show no
   installation change. Expected: verify clean; only the work item's own plan, registry and
   state files appear under `docs/ai-workflow/`.

### Known limitations and out of scope

- The release is not published by this milestone: publishing happens when the pull request merges
  and the `Release` workflow runs; the `workflow-manager` pin is a separate pull request.
- The new order is measured, not adaptive: a change to the acceptance shard assignment needs a
  re-measure (comment in the step; issue #55 remains open for the other wording fixes, W19).
- CI wall-clock gains cannot be observed offline; the width-4 simulation in `release_test.py` is
  the offline evidence.
