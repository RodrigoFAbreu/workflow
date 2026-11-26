# Active Milestone

## Milestone

W64: `payload-polish-4` (`process`, governing version `2.2`), branch `milestone/payload-polish-4`, base
`f4926525ef73cc80eef3e5951f669591f8f76d23`. Release Workflow 2.29.15, a `fix:` patch. Row 57 of `docs/ROADMAP.md`. Issues
RodrigoFAbreu/workflow#143, #119 and #113 (the still-open test pins). The plan is `docs/ai-workflow/PAYLOAD_POLISH_4_PLAN.md`
(revision 2).

## Goal

Pin the errno text and the permissions hint of the `remove_failed` refusals of the remove command's delete step. No refusal
order, command, exit code, message or working path changes.

## Progress

- CP1 (the errno and permissions pins of the remove delete step): complete. `test_t4_...` (`RetentionErrorPathsTwo`) pins the
  exact message and next step of the open arm; `test_t12_...` (`RetentionRemove`) pins the `unlink`, in-folder `rmdir`,
  not-empty `rmdir` and last `rmdir` arms, each in its own subtest. Only
  `payload/scripts/workflow_state_completion_obligations_test.py` changes in `payload/`. Mutations m1 to m6 on scratch copies
  fail exactly the subtests the plan names; the obligations suite still counts 322.
- CP2 (release 2.29.15): complete. `WORKFLOW_RELEASE` and the protocol document's lines name 2.29.15 (protocol 1.5); the manifest
  carries the version, the posture and the four changed records' sentence, `sha256` and `size`; the history row and stamp, the
  `PayloadPolishFourReleaseTest` class (the 2.29.14 class gives up the pins a newer release owns) and roadmap row 57 (`Done`).
- Self-review: the `unlink fails` subtest of `test_t12` now carries the no-write proof (the archive's bytes, `.ai-review/w00`
  absent, the leftover minus 3 entries, the clean second run) and checks that the shown path is an entry of the folder whose
  basename is the failing third call's, as D-Pins item 2 says; the `observed_run` docstring names its three arguments. The
  manifest record of the obligations test moves with it (`sha256`, `size`); m1 still fails only that subtest.

- Implementation review: `LOCAL_MODEL_IMPLEMENTATION_REVIEW` (round 1) and `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW` (round 1) both
  APPROVE the implementation bundle at `9fd9c5757ffa4c1b846f67b478526baea089b083`. The item is at `AWAITING_FUNCTIONAL_REVIEW`.

## Functional review checklist

Reviewed unit: the `payload-polish-4` implementation at `9fd9c5757ffa4c1b846f67b478526baea089b083` (implementation revision 1,
plan revision 2). This is a `process` item with no running application: every flow below runs the tests and checks the release
source. Nothing here pushes, opens a pull request, publishes, or runs a remove or prune command against a real repository.

### Setup

- Repository `~/Workspace/workflow`, branch `milestone/payload-polish-4`. Python 3 with the standard library only; no network,
  no real GitHub, no real `claude`, `codex` or `ssh`.
- Use a scratch directory `$S` under `$TMPDIR` for every copy. Never write inside the clone except through the test runs, which
  build their own scratch repositories.
- Host-only prerequisites (flows 6 and 7): the pinned zlib-ng runtime (`zlib_ng` 1.0.0, zlib-ng 2.2.5, see
  `tools/release/deflate-requirements.txt`) and the Manager's `reaper.py` from the `workflow-manager` repository. Neither is
  importable or present in a sandbox without them.

### Test data

None to seed. The obligations suite builds its own review folders and archives in scratch repositories (`RetentionRemove` and
`RetentionErrorPathsTwo`).

### Flows

1. **Payload scope.** `git diff --stat f4926525ef73cc80eef3e5951f669591f8f76d23 -- payload`. Expect four files:
   `payload/scripts/workflow_state_completion_obligations_test.py`, `payload/scripts/workflow_protocol.py`,
   `payload/scripts/workflow_protocol_test.py` and `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`. Nothing else.
2. **No retention behaviour change.** `git diff f4926525ef73cc80eef3e5951f669591f8f76d23 -- payload/scripts/workflow_retention.py`.
   Expect empty output.
3. **The two touched classes.** Stage the fixture (`python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"`),
   then `cd "$S/fixture/scripts" && python3 -B workflow_state_completion_obligations_test.py RetentionRemove RetentionErrorPathsTwo`.
   Expect `OK`. The subtests named in the plan (`test_t4_...` open arm; `test_t12_...` subtests "the unlink fails", "a directory
   that cannot be removed", "a directory that is not empty", "the folder itself cannot be removed") all pass.
4. **The nine payload suites** from the staged fixture, exactly the loop in `docs/RELEASING.md`, "Verification commands", run from
   `$S/fixture/scripts`. Expect every suite to exit 0. The obligations suite still counts 322 test cases.
5. **Mutation checks (optional, deeper).** For each of m1 to m6, copy the fixture to its own `$S/mN`, make the one edit to
   `workflow_retention.py` the plan names (`docs/ai-workflow/PAYLOAD_POLISH_4_PLAN.md`, D-Pins, "Failure-only mutations"), and run the
   whole obligations suite there. Expect exactly the subtests the plan lists to fail, and every other test to pass. The original
   fixture passes throughout.
6. **Reaper orphan check (host-only).** `reaper.py --report R.json --chunk-id polish4 -- python3 -B workflow_state_completion_obligations_test.py RetentionRemove RetentionErrorPathsTwo`
   run from the staged fixture's `scripts` directory. Expect status 0 and orphans only `[git]`, all `exited`.
7. **Release gates (host-only for the `tools/release` tests).** From the clone, with the zlib-ng interpreter:
   `python -m unittest discover -s tools/release -p '*_test.py'`; `python3 -m unittest discover -s tools/docs -p '*_test.py'`;
   `python3 tools/docs/check_docs.py`; `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`;
   and `python3 tools/release/release.py check-title "fix: pin the errno text and the permissions hint of the remove delete step's refusals" --agree --head HEAD`.
   Expect all to pass; `manifest.json` names `2.29.15`; the title agrees with the `fix:` patch.
8. **Installation untouched.** `git diff --name-only f4926525ef73cc80eef3e5951f669591f8f76d23 -- .claude scripts .workflow-manager .github CLAUDE.md`.
   Expect empty output. `workflow-manager verify .` must stay clean (it needs the release cache; offline it exits 1, which is a
   host step, not a failure of this change).

### Expected results, in short

- The change adds pins only: no refusal order, command, exit code, message or working path changes. Items #143 1 to 3, #119 4b to 4d
  and 6b to 6f, and #113 5 were already true on `main` and are not part of this change.
- The release is `2.29.15`, a `fix:` patch. Nothing is published by this round.

### Known limitations and out-of-scope behaviour

- The recorded optional findings (in `docs/ai-workflow/WORKFLOW_STATE.json`, `implementation_review_stages`) do not change
  behaviour. One of them (the unlink subtest's no-write proof checks the surviving entries by path, not by their values) is deferred
  to a later item, because the release version is frozen.
- The advice for an archive that cannot be repaired (#119 point 6b) is left as it is: a design question, not a message fix.
- The sandbox does not have the zlib-ng runtime or the Manager's `reaper.py`, so flows 6 and 7 are host steps.

## Next action

Functional review: run the checklist above on the reviewed commit. Put any findings in
`.ai-review/payload-polish-4/feedback/FUNCTIONAL_REVIEW.md`, then run `/apply-functional-review payload-polish-4`. Once testing is clean
and every checkpoint is `COMPLETE` (CP1 and CP2 are), `/accept-milestone payload-polish-4` is the only acceptance command.
Nothing is pushed, merged or published.
