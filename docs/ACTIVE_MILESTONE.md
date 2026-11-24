# Active Milestone

## Milestone

W63: `payload-polish-3` (`process`, governing version `2.2`), branch `milestone/payload-polish-3`, base
`9c22845cbf9b14978a6d101ac041a696207e5699`. Release Workflow 2.29.14, a `fix:` patch. Row 56 of `docs/ROADMAP.md`. Issue
RodrigoFAbreu/workflow#216 (points 1 to 3 done; point 4 not taken). The plan is `docs/ai-workflow/PAYLOAD_POLISH_3_PLAN.md`
(revision 1).

Previous: W62 `payload-polish-2` is accepted and complete; its record is `docs/milestones/completed/payload-polish-2-findings.md`.

## Goal

A message of the shipped payload says what is true, and a test pins each case the issue names. No refusal order, command, exit
code or working path changes.

## Status

- CP1 (the takeover arm of the plan-approval refusal and its pin), CP2 (the leftover-state pins and the `docs/RETENTION.md`
  sentence) and CP3 (release 2.29.14) are `COMPLETE`.
- The plan approval and the technical approval are `CURRENT` (recorded by policy). The technical approval's reviewed content is
  commit `f672324`; the working tree's shipped files are unchanged since it.
- Phase: `AWAITING_FUNCTIONAL_REVIEW`.
- Nothing is pushed, merged or published. Release 2.29.14 follows the merge to `main`.

## Functional review checklist

### Setup

- Work from `milestone/payload-polish-3` at the checklist evidence commit or later. `git cat-file -t
  9c22845cbf9b14978a6d101ac041a696207e5699` must print `commit`: the base needs full history.
- Create a scratch directory `$S` with `mktemp -d` under `$TMPDIR`. The product clone is read-only for these flows: they only
  read it, and every staged fixture or mutated copy goes under `$S`.
- Stock Python 3 only. No network, no `gh`, no real `claude`, `codex` or `ssh`, and no PID namespace. Each suite builds its own
  scratch repository; no flow runs an archive, remove or prune command against a real repository.
- The staged fixture for flows 3 to 6: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"`
  (see "Verification commands" in `docs/RELEASING.md`).
- Flow 6's `tools/release` tests need the pinned zlib-ng interpreter (`docs/RELEASING.md`, "Building locally"). If it is not
  reachable here, record that part as `environment`, not as a product result.

### Test data

Nothing to seed. The suites create their own scratch repositories.

### Flows

Run each command and compare with **Expect**. Record the exact output of any mismatch.

1. **Changed files.** `git diff --stat 9c22845 -- payload`
   **Expect:** six files, 87 insertions and 8 deletions: `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`,
   `payload/scripts/workflow_integration_test.py`, `payload/scripts/workflow_protocol.py`,
   `payload/scripts/workflow_protocol_test.py`, `payload/scripts/workflow_state.py` and
   `payload/scripts/workflow_state_completion_obligations_test.py`. `payload/scripts/workflow_retention.py` is absent.
2. **The one code change.** `git diff 9c22845 -- payload/scripts/workflow_state.py | grep '^[-+][^-+]'`
   **Expect:** the `if held.get("step_class") == DESTRUCTIVE:` line becomes `elif`, behind a new first arm,
   `if held.get("step") == "takeover":`, whose message reads "that guard is a takeover's: let a running takeover finish, or, if
   it died, re-run it: `workflow_state.plan_approval_takeover_evidence`, then
   `workflow_state.take_over_plan_approval_transaction` ...". No other line changes.
3. **The pins.** In the staged fixture, from inside it: `python3 -B workflow_integration_test.py` and
   `python3 -B workflow_state_completion_obligations_test.py RetentionErrorPathsTwo`.
   **Expect:** both `OK`. New subtests: `takeover` in
   `test_acquire_guard_refuses_when_held_under_the_current_epoch_by_a_different_token` (integration suite), and in
   `test_t7b4_every_stray_before_the_rename_says_nothing_was_renamed` (obligations suite) the two leftover-state index-read
   subtests (`pread`/`_index_ids`, `fstat`/`_judge_removal_archive`) and the early-selection subtest.
4. **Mutations.** Each on its own copy of the fixture under `$S`, never in the clone. Each must fail exactly what is named.
   - m1: remove the takeover arm from `payload/scripts/workflow_state.py`. **Expect:** only the `takeover` subtest of the
     integration test fails.
   - m1b: make the takeover arm apply to every guard. **Expect:** the `ordinary` and `destructive` subtests fail; `takeover`
     passes.
   - m2: in `payload/scripts/workflow_retention.py`, `_select_removal`, drop the `_add_leftover_note(...)` call of the
     `except OSError` arm. **Expect:** only the two new index-read subtests fail.
   - m3: in `_select_removal`, open the archive directory by path before the selection and pass it as `adir_fd`. **Expect:** only
     the early-selection subtest fails, at its whole-line `next step:` assertion.
5. **Orphan check.** Run the touched classes under the orchestrator's test reaper (`reaper.py`, which is not in this repository).
   **Expect:** status 0; orphans only `[git]`, all `exited`. If the reaper is not available, record this flow as not run.
6. **Full environment.** The nine payload suites from the staged fixture (the loop in `docs/RELEASING.md`, "The nine payload
   suites"); `python -m unittest discover -s tools/release -p '*_test.py'` with the zlib-ng interpreter;
   `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`;
   `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`;
   `python3 tools/release/release.py check-title "fix: name the takeover route in the plan-approval guard refusal and pin two retention cases" --agree --head f672324`.
   **Expect:** all pass. `manifest.json` names 2.29.14. The suite counts the plan names (1250, 429, 385 and 322) are unchanged.
   `check-manager-block` prints `ok: 2.29.14 ...`; `check-title` prints `impact=patch` and agrees.
7. **Installation untouched.** `git diff --name-only 9c22845 -- .claude scripts .workflow-manager .github CLAUDE.md`
   **Expect:** no output.

### Known limitations

- Point 4 of #216 is not taken (plan section 0, finding F1). The `.removing` row of the archive command's table in
  `docs/RETENTION.md` is correct and unchanged; no flow tests a change there.
- Point 1 is reached only by a takeover's own plan-approval guard. It is pinned by the integration subtest, not by a manual
  flow.
- Only messages, tests and one sentence of `docs/RETENTION.md` change. No refusal order, command, exit code or working path
  changes.
- Release 2.29.14 is not published. The installation (`.claude/`, `scripts/`, `.workflow-manager/`, managed blocks, `.github/`)
  is untouched, and `workflow-manager verify .` is not part of this checklist.
- No flow needs `gh`, the network or a PID namespace. A result that depends on the sandbox (a missing interpreter, a refused
  namespace, an absent reaper) is `environment`, not a product failure.

### Next steps

- Once every flow passes, `/accept-milestone` is the only acceptance command. It requires every checkpoint in this item's
  registry to be `COMPLETE`, which CP1 to CP3 already are.
- Findings go to `.ai-review/payload-polish-3/feedback/FUNCTIONAL_REVIEW.md`. `/apply-functional-review` routes each one: the
  bounded branch for a same-scope fix, or the broad branch (a `payload-polish-3-remediation-<n>` child item) for new or wider scope.
