# Active Milestone

## Milestone

**Complete** (accepted by policy; the release follows the merge). W5: `retire-21-for-new-work` (`process`,
governing version `2.2`), branch `milestone/retire-21-for-new-work`, base
`b854a0b` (the release source is Workflow 2.9.2; this repository's own
installation is also 2.9.2 with automatic gates and no `GATE_POLICY.json`). The
plan is `docs/ai-workflow/RETIRE_21_FOR_NEW_WORK_PLAN.md`. The previous
milestone, W6 (`functional-fix-commit-order`, Workflow 2.9.2), is complete.
This is a re-plan: W5 was planned once on 2.9.1 and paused at its plan review
while W6 went first; that work was never committed.

## Goal

Workflow 2.10.0, a minor release (`feat:`), roadmap row 7:

1. **New work items stop starting on "2.1".** While `WORKFLOW_CONFIG.json`
   names "2.1" as the default, creating a new work item (a fresh
   `/milestone-plan`, or a broad remediation child from
   `/apply-functional-review` or `/apply-pr-review`) refuses before any write
   with `DefaultWorkflowVersionRetiredError` and one next step: set the default
   to "2.2" in a `Workflow-Activation: 2.2` commit. Existing "2.1" items keep
   working to completion, legacy adoption still targets "2.1", "2.1" stays in
   `supported_versions`, and nothing persisted changes. Orchestration Protocol
   1.3 adds row 1b (`blocked`, `plan_start_default_retired`) and an advisory
   `verify` check, `default_workflow_version`.
2. **A faster managed conformance job.** `workflow-conformance.yml` cancels a
   pull request's superseded run on a new push (push runs are never cancelled)
   and runs the nine suites in parallel inside the one `workflow-conformance`
   job, each in its own copy of the checkout with its own `TMPDIR` and `HOME`,
   every failure shown and annotated.
3. **Two version-aware wording fixes** W6 deferred:
   `recover-implementation-provenance.md`'s introduction and
   `MILESTONE_WORKFLOW.md`'s broad-branch line.

The Manager side (the `workflow-manager doctor` warning, and the Manager's
template test pattern) ships in the Manager pin pull request; the plan's
D-Manager-Handoff says exactly what.

## Current checkpoint

Implementing (plan revision 2, approved). CP1 (the refusal at creation, and the
fixtures that seed existing "2.1" items) is complete: `workflow_state.py` gains
`NEW_WORK_RETIRED_VERSIONS`, `RETIRED_DEFAULT_NEXT_STEP`,
`DefaultWorkflowVersionRetiredError` and `assert_default_admits_new_work_item`,
which `route_work_item`'s fresh branch and `create_remediation_child_work_item`
call; the harness gains `seed_existing_work_item` and
`seed_existing_remediation_child`; the acceptance matrix creates its items
through one `route_item` helper, and the three real-creator child scenarios run
under a `Workflow-Activation: 2.2` default. CP2 (Orchestration Protocol 1.3) is
complete: `workflow_protocol.py` narrows row 1 to a default that is not retired,
adds row 1b (`plan_start_default_retired`, remedy `RETIRED_DEFAULT_NEXT_STEP`,
evaluated between rows 1 and 1a) and the advisory `default_workflow_version`
`verify` check, and `PROTOCOL_VERSION` is `1.3`; the protocol document, the
schema's check-id list and the protocol suite's mirror and release-comparison
tests follow. CP3 (command texts) is complete: `milestone-plan.md` step 0 stops a fresh
milestone under a "2.1" default before step 1, `apply-functional-review.md`
checks `assert_default_admits_new_work_item` before the first bounded sub-step,
and `apply-pr-review.md`'s broad fix names the refusal, that step 1's write
stands, and the re-run from `already_reopened`; the integration suite updates
two golden hashes, pins `apply-pr-review.md`, and adds static conformance tests.
CP4 (regression scenarios) is complete: the acceptance matrix gains
`RetiredDefaultVersionProcess`/`...Product` (14 scenarios each): the refusal on
every creation path under a "2.1" default (fresh milestone, row 1b, a broad
functional-review child, a broad pull-request child, with the `reconcile`
classes and the `verify` warning), the same paths after the
`Workflow-Activation: 2.2` edit (the "2.2" child driven through its own cycle to
`MILESTONE_COMPLETE`, then the "2.1" parent accepted), an existing "2.1" item
run to completion under a "2.1" default and under a "2.2" default, a "2.2" and
a "1" default unchanged, legacy adoption unchanged, and the shipped templates.
`Item.approve_implementation` gains an opt-in `scoped_staging`. The matrix runs
381 tests (353 + 28), all green. CP5 (managed conformance job) is complete: the
template gains the `concurrency` block (a pull request's runs share one group
and cancel; any other run is keyed by `run_id`/`run_attempt`) and one
`Run the conformance suites` step that runs the nine suites `min(4, nproc)` at a
time, longest first, each in its own checkout copy with its own `TMPDIR` and
`HOME`, every suite always run, failures unfolded with an `::error` line;
`release_test.py` gains `ConformanceTemplate` (7 tests). Verified in a scratch
clone with refreshed digests: the full `release_test.py` (86 tests, Python 3.12)
green; the step body on the nine real suites green in 4m09s wall against 572s
sequential. The committed manifest digests are refreshed at CP7. CP6
(documentation) is complete: `IMPLEMENTATION_REVIEW_WORKFLOW.md`, the operator
reference and `MILESTONE_WORKFLOW.md` (the `PLANNING` entry) gain one paragraph
each on the retired "2.1" default; the two D-Wording fixes land in
`recover-implementation-provenance.md`'s introduction and
`MILESTONE_WORKFLOW.md`'s broad-branch bullet; `docs/install.md`,
`docs/gates.md` and `docs/common-problems.md` state the next step and where to
commit it. `check_docs.py` is clean; in a scratch fixture of the working tree
(refreshed digests) seven of the nine suites are green, and
`workflow_fingerprint_demo_test` and `workflow_state_demo_test` fail identically
on the unmodified CP5 commit (they need the repository's full history, which the
fixture lacks). CP7 (release 2.10.0) is complete: `manifest.json` names
2.10.0 with every changed digest and the conformance template's derivation text
refreshed, `WORKFLOW_RELEASE` is `2.10.0` (the protocol suite's release pin
follows), and `docs/release-history.md` gains the 2.10.0 row; the roadmap row 7
is marked Done at acceptance. In a scratch clone of the CP7 tree the full
`release_test.py` (86 tests) is green, the stock `stage-conformance` fixture
runs the nine suites green, `check_docs.py` is clean, `check-title --agree`
accepts a `feat:` title for 2.9.2 to 2.10.0, and `workflow-manager verify .`
is clean.

Self-review (`SELF_REVIEWING_IMPLEMENTATION`) of the full milestone diff fixed
two defects. In the template's step body, Actions runs `bash -eo pipefail`, so
a suite whose checkout copy failed (and so wrote no result) made the throttle's
`wait -n`, and then the failure branch's `cat` of its missing log, end the
step before any other suite was reported; both now tolerate it, and a new
`ConformanceTemplate` test (an uncopyable checkout) pins that all nine are
still reported, with the manifest's template digest refreshed. And
`docs/common-problems.md` and `docs/install.md` named `workflow-manager verify`
as the source of the `default_workflow_version` warning, which is the
Workflow's own `verify` check; `common-problems.md` also says that
`/apply-pr-review`'s first-step write stands.

## Next action

W5 is accepted. Merge pull request #24 (squash, `feat:` title); the `Release`
workflow then publishes Workflow 2.10.0. The next roadmap item (row 8,
Controller C10) waits on the Controller, so there is no milestone to
`/milestone-plan` yet.

## Functional review checklist

Automated verification is current: the working tree is unchanged since the
implementation bundle (only state-recording commits follow the last code
commit, `d2d2091`).

### Setup

- Branch `milestone/retire-21-for-new-work`, clean tree. Python 3.12. No build
  step; no feature flags. The release source (`payload/`, `templates/`,
  `manifest.json`, `tools/release/`) is what changed; this repository's own
  installation stays 2.9.2.
- Scratch work only in a throwaway directory (`mktemp -d`), never in this tree.
- Flow 8 needs the pinned compression runtime: `pip install --require-hashes
  -r tools/release/deflate-requirements.txt` (a virtual environment is fine).
  Without `zlib_ng`, `tools/release/release_test.py` fails 25 tests with
  `zlib_ng is not installed`; with it, all 87 pass.

### Test data

- A scratch fixture repository from the harness
  (`payload/scripts/workflow_test_harness.py`: `seed_existing_work_item`,
  `seed_existing_remediation_child`) or the acceptance matrix's
  `RetiredDefaultVersionProcess` scenarios; one config with
  `default_workflow_version: "2.1"`, one with `"2.2"`.

### Flows

1. **Refusal at creation under a "2.1" default.** In a fixture whose
   `WORKFLOW_CONFIG.json` default is `"2.1"`, run `/milestone-plan` for a fresh
   milestone. Expected: stops at step 0 before any write, raises
   `DefaultWorkflowVersionRetiredError`, one next step: set the default to
   "2.2" in a `Workflow-Activation: 2.2` commit. `WORKFLOW_STATE.json` unchanged.
2. **Broad remediation children refuse too.** Under the same default, a broad
   `/apply-functional-review` finding and a broad `/apply-pr-review` fix.
   Expected: the same refusal before the first write (for `apply-pr-review`,
   step 1's reopen write stands and the re-run resumes from `already_reopened`).
   Bounded functional fixes are unaffected.
3. **After activating "2.2".** Edit the default to "2.2", commit with
   `Workflow-Activation: 2.2`, repeat flows 1-2. Expected: items are created as
   "2.2" and run through their cycle.
4. **Existing "2.1" items, legacy adoption and other defaults unchanged.** An
   already-seeded "2.1" item completes under a "2.1" default and under a "2.2"
   default; legacy adoption still lands on `"2.1"`; "2.1" remains in
   `supported_versions`; "2.2" and "1" defaults behave as before.
5. **Orchestration Protocol 1.3.** Under a "2.1" default the protocol returns
   row 1b (`blocked`, `plan_start_default_retired`) with the remedy text; under
   "2.2" row 1 applies. `verify` shows the advisory `default_workflow_version`
   warning (and none under "2.2").
6. **Managed conformance job.** Read
   `templates/.github/workflows/workflow-conformance.yml`: `concurrency`
   cancels a pull request's superseded run but never a push run; one
   `Run the conformance suites` step runs the nine suites in parallel, each in
   its own checkout copy with its own `TMPDIR`/`HOME`; every failure is shown
   and annotated with `::error` even if one suite's copy fails.
7. **Wording fixes.** `recover-implementation-provenance.md`'s introduction and
   `MILESTONE_WORKFLOW.md`'s broad-branch bullet read correctly for both "2.1"
   and "2.2" items. `docs/install.md`, `docs/gates.md` and
   `docs/common-problems.md` state the next step and where to commit it, and
   attribute the `default_workflow_version` warning to the Workflow's own
   `verify`.
8. **Release 2.10.0.** `manifest.json` names 2.10.0, `WORKFLOW_RELEASE` is
   `2.10.0`, `docs/release-history.md` has the 2.10.0 row; `python3
   tools/release/release_test.py` (in the environment from Setup) and
   `check_docs.py` are clean.

### Functional review round 1

Flows 1-8 passed; three wording findings, no code defect.

- **Fixed (wording only, commit `393a80e`):** `docs/gates.md` now says to set
  `default_workflow_version` to `"2.2"` (with `"2.2"` in `supported_versions`)
  in a commit carrying `Workflow-Activation: 2.2`, that the Workflow's own
  `verify` warns `default_workflow_version` while the default is `"2.1"`, and
  links to `common-problems.md` for where to commit it.
  `MILESTONE_WORKFLOW.md`'s broad-branch bullet no longer says the default
  "can no longer be `"2.1"`": while it is `"2.1"`, creating the child refuses
  with `DefaultWorkflowVersionRetiredError`, writing nothing. A sweep of the
  release payload and `docs/` found no other such sentence.
- **Checklist correction (no code change):** Setup now names the compression
  runtime flow 8 needs.
- **Re-test:** flow 7 (the three documents and the `MILESTONE_WORKFLOW.md`
  bullet) and flow 8 with the prerequisite installed. Flows 1-6 are unaffected.

### Known limitations / out of scope

- The `workflow-manager doctor` warning and the Manager's template test pattern
  ship in the Manager pin pull request (D-Manager-Handoff), not here.
- This repository's own installation is not updated until 2.10.0 is published
  and installed; roadmap row 7 is marked Done at acceptance.
- `workflow_fingerprint_demo_test` and `workflow_state_demo_test` need full
  repository history and fail in history-less scratch fixtures (identically on
  the unmodified CP5 commit).
