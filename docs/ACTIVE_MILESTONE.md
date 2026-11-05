# Active Milestone

## Milestone

**In progress (implementing).** W39: `unclassified-path-message` (`process`, governing version `2.2`), branch
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

## Next action

Self-review of the full diff, the full verification and the implementation-review bundle (`/milestone-implement unclassified-path-message` again).
