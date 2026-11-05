# Active Milestone

## Milestone

**Awaiting functional review.** W39: `unclassified-path-message` (`process`, governing version `2.2`), branch
`milestone/unclassified-path-message`, roadmap row 34 (RodrigoFAbreu/workflow#146). Plan:
`docs/ai-workflow/UNCLASSIFIED_PATH_MESSAGE_PLAN.md` (revision 5, approved by gate policy). The goal, Workflow 2.25.7
(a `fix:` patch, released after the merge of the pull request): an unclassified path is refused with a message that
names the path, the artifact-declaration file that must list it and the sanctioned route that adds it, qualified by
stage and phase. The class, where it is raised, who catches it and every exit code stay as they are. Base commit
`dd565f0`; the previous milestone, W38 `retention-report-unreadable`, is accepted (Workflow 2.25.6).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The message, tests and page | **complete** (see the commit of this checkpoint) |
| CP2 | Release 2.25.7 | **complete** (see the commit of this checkpoint) |

## Verified state

- CP1: tests T1 to T9 written first and run red against the unedited tree, then green; failure-only mutations m1 to
  m20 each fail the named tests on a scratch copy. `workflow_fingerprint_generalization_test` (148),
  `workflow_fingerprint_test` (283) pass; `workflow_state_test` (1248) passes except two tests that read the live
  state file from the `payload/` tree and fail identically on the base. `tools/docs/check_docs.py` is clean.
- CP1 did not run: the D-Staging disposable-clone verification (nine suites from a staged fixture, `tools/release`
  with the zlib-ng interpreter, `check-manager-block`). CP2's stock `stage-conformance` run is the real proof.

- CP2: `WORKFLOW_RELEASE` 2.25.7 with its assertions and the protocol document; `manifest.json` 2.25.7 (seven changed
  records, posture, `conformance.suites` measured by `manager-block --write`: `workflow_state_test` 1248,
  `workflow_fingerprint_generalization_test` 148); `docs/release-history.md` row; `docs/common-problems.md` pin;
  `tools/release/release_test.py` 2.25.7 class. Verified from a scratch clone holding the CP2 commit: `check-manager-block`
  ok, `tools/docs` and `check_docs.py` clean, `release.py build` succeeds, `tools/release` (309, zlib-ng interpreter) OK.
- Self-review: the plan's flows 1 to 7 and mutations m1 to m20 re-run on scratch copies. Three gaps against D-Tests and one
  against the row's neighbours fixed in one commit: T5 now pins the whole coverage refusal (it also passes on the base
  engine), T6 calls the real amendment guard and reads the command file's order, the 2.25.7 history row names #146.
  `workflow_state_test` is 1249; `manifest.json` re-records the test file. m21 to m23 cover the new assertions.
- Full verification at the reviewed head `80c90cc` (run after the self-review commit, which the CP2 run predates), from a
  staged fixture of `HEAD` in a scratch directory: the nine payload suites pass (exit 0); `check-manager-block` with
  `--manager-releases` is ok; `tools/docs` tests (34) pass; `check_docs.py` exits 0. **Not run:** the `tools/release` tests,
  because the pinned zlib-ng 2.2.5 module (`zlib_ng`) is not installed in this environment. `workflow-manager verify .` reports
  the installation matches 2.25.6. Flows 1 to 7 of section 6 re-run on `base` and `cand` copies with their expected results.

## Next action

Manual functional review, by the checklist below. Findings go to `.ai-review/unclassified-path-message/feedback/FUNCTIONAL_REVIEW.md`
and `/apply-functional-review` routes each one. Once testing is clean, `/accept-milestone` is the only acceptance command; it
needs every checkpoint `COMPLETE` (CP1 and CP2 are).

## Functional review checklist

**Reviewed content:** branch `milestone/unclassified-path-message`, implementation revision 1, reviewed implementation head
`80c90cc`, plan revision 5. Test against the checklist-evidence commit that carries this section; its SHA and blob are
reported with this checklist, not written here (a commit cannot name itself).

### What changes for you

Only the text of one refusal. An unclassified path (a changed file that the artifact declaration does not list) used to be
reported as the bare path. Now the refusal names the path, the declaration file to edit and the sanctioned route, qualified by
stage and phase. What is refused, the exception class, the exit codes and every other output are unchanged.

### Setup (scratch only)

- Work only under a new scratch directory `$T` (`mktemp -d`). Do not run anything inside the product clone, its `.ai-review/`
  or against the real forge. Nothing needs the network, `gh`, `claude`, `codex` or `ssh`. Needs `git` and Python 3.12.
- Copy the Python block of section 6 of `docs/ai-workflow/UNCLASSIFIED_PATH_MESSAGE_PLAN.md` to `$T/flow.py`.
- `base`: `git archive dd565f0f5d223228984771c546378f3d9885a391 payload/scripts | tar -x -C $T/base`
- `cand`: `git archive <checklist-evidence-commit> payload/scripts | tar -x -C $T/cand` (the working tree is clean, so these are
  the bytes that were reviewed).
- Flow 7 only: copy `$T/cand/payload/scripts/workflow_state_test.py` over `$T/base/payload/scripts/workflow_state_test.py`.
- From `$T`: `python3 -I flow.py base/payload/scripts <case>` and `python3 -I flow.py cand/payload/scripts <case>`, for the cases
  `direct`, `plan`, `impl`, `same`, `interval` and `gate`.

### Test data

Nothing to seed. Each case builds its own scratch repository (`src/a.txt` committed, an undeclared `other/mystery.txt`);
`interval` and `gate` use the suite's own scratch helpers.

### Flows

| # | Run | Expected on base | Expected on cand | Sandbox-runnable |
| --- | --- | --- | --- | --- |
| 1 | `direct` | the bare `other/mystery.txt`, twice; class `workflow_fingerprint.UnclassifiedPathError` | the same class; plan-stage text, then implementation-stage text, both in the unknown-item form: `docs/ai-workflow/registry/<work_item_id>-artifacts.json` and "the work item is not known" | yes |
| 2 | `plan` | the bare path, twice | known-item plan-stage text twice, naming `demo-item-artifacts.json`; `/milestone-plan demo-item` at the non-admitting phases; `/request-plan-amendment demo-item` (the user's command), then `/milestone-plan demo-item`, plan review and `/approve-review plan` or `/satisfy-gate`, only at `IMPLEMENTING` and `SELF_REVIEWING_IMPLEMENTATION`; no `/apply-plan-review` | yes |
| 3 | `impl` | the bare path, twice | known-item implementation-stage text twice: `implementation_stage`, "protected for a deliverable, excluded for repository territory"; no `/request-plan-amendment` | yes |
| 4 | `interval` | `... touches 'other/mystery.txt', classified 'unclassified', not excluded` and nothing more | the same sentence, then `: other/mystery.txt is not classified by the implementation stage ... demo-item ...` and the "A provenance interval may contain only excluded paths" sentence; class `ProtectedPathInProvenanceIntervalError` | yes |
| 5 | `same` | `protected protected` / `excluded` / `Exception workflow_fingerprint` | identical | yes |
| 6 | `git diff --stat dd565f0 -- payload docs`, in the checkout | (not applicable) | the two scripts, their two tests, `docs/common-problems.md`, `docs/ROADMAP.md`, the plan, the registry, mapping and declaration files, the state file, and this file; no command file, no `docs/gates.md` | yes (reads only) |
| 7 | `gate` | the bare path, twice, for `technical_approval_gate_status` and for `promote_legacy_work_item` | the implementation-stage known-item text twice, naming the item the case sets up: `wi` and `milestone-8`, not the `<work_item_id>` placeholder | yes |
| 8 | the nine payload suites from a staged fixture; `tools/docs` tests and `check_docs.py`; `check-manager-block --manager-releases`; the `tools/release` tests with the pinned zlib-ng 2.2.5 interpreter | all pass, none skipped | (the same run) | no, for the zlib-ng part: the interpreter is not in the sandbox |
| 9 | `git show --stat --format= ad8b23d` (checkpoint 2) | (not applicable) | the nine CP2 files: `docs/ACTIVE_MILESTONE.md`, `docs/ai-workflow/WORKFLOW_STATE.json`, `docs/common-problems.md`, `docs/release-history.md`, `manifest.json`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `payload/scripts/workflow_protocol.py` and its test, `tools/release/release_test.py` | yes (reads only) |

Flow 7's expected text names `wi` and `milestone-8` because `gate_case` sets up those items; section 6 of the plan says
`demo-item`, which is wrong for this flow. The check is that the item is named, not the placeholder.

### Reading the wording (you, not the harness)

- At each plan-stage phase, read the route in flow 2 as the reader in that phase would: is `/request-plan-amendment` offered
  only where it is admitted, and is the declaration file the right one? Cross-check against
  `docs/ai-workflow/REVIEW_PROTOCOL.md`, "Repairing an artifact declaration after an approval".
- The plan-stage refusal is long (about a thousand characters). Judge whether it reads at a terminal, and whether the
  sentences a reader needs come first.

### Known limitations and out of scope

- No classification changes: what is refused, the declaration format, the generated template, any command file and any other
  exception are as they were.
- `/apply-plan-review` is deliberately not named as a route: it refuses at these phases.
- Only the text changes. A message that quotes the error, such as `PlanApprovalClosureProofError`, is longer.
- Two tests in `workflow_state_test` read the live state file from the `payload/` tree and fail the same way on base; that
  predates this item.
- The release 2.25.7 is cut after the pull request merges. It is not part of this review.

### After testing

- Clean testing: `/accept-milestone` is the only acceptance command, and it needs every checkpoint `COMPLETE`.
- Findings: write them to `.ai-review/unclassified-path-message/feedback/FUNCTIONAL_REVIEW.md`, then `/apply-functional-review`.
  A same-scope fix takes the bounded branch; new or wider scope takes the broad branch (`unclassified-path-message-remediation-<n>`).
- No command records acceptance of a partial round.
