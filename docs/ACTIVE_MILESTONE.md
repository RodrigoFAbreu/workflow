# Active Milestone

## Milestone

W62: `payload-polish-2` (`process`, governing version `2.2`), branch `milestone/payload-polish-2`, base
`d34217d63a6f429226c14cb8b08233090599cfd7`. Release Workflow 2.29.13, a `fix:` patch (at CP3). Row 55 of `docs/ROADMAP.md`. Issues
RodrigoFAbreu/workflow#213, #119 points 2a, 2b and 6d, and #113 points 6a and 6b. The plan is
`docs/ai-workflow/PAYLOAD_POLISH_2_PLAN.md` (revision 2).

## Goal

Message, test and doc-form points in the shipped payload. No refusal order, command, exit code or working path changes.

## Progress

- CP1 (the wording points, their pins and the roadmap row): complete. `workflow_retention.py` (the pre-rename stray refusal, the
  idempotent leftover note, the running command's name in the walk and the open), `workflow_state.py` (the plan-approval guard's
  true next step), three new tests in the obligations suite, the strengthened integration test, the `docs/RETENTION.md` sentence.
  Mutations m1 to m6b each fail exactly what the plan says.
- CP2 (the `pread` subtest and the two doc forms): complete. `test_t7b3` gains the "remove --apply, the read" subtest
  (`_call_fails("pread", "_index_ids", EIO)`) and the `_call_fails` docstring is widened; the four `docs/exit-codes.md` rows say
  `python3 -I scripts/workflow_retention.py <command>`; `docs/RETENTION.md`'s `archives` sentence names regular files and the
  kinds not listed. m7 fails the new subtest alone (at `assertTrue(counted)`); m8 is a doc revert, whose assertions ride with
  the release class in CP3. `tools/docs/check_docs.py` is clean.
- CP3 (release 2.29.13): complete. `manifest.json` 2.29.13 (the seven changed records take the `payload-polish-2 (workflow-2.29.13)`
  sentence, `sha256` and `size`; the obligations suite counts 322; the posture says the way back to 2.29.12), `WORKFLOW_RELEASE`
  2.29.13 and the protocol document's lines (protocol 1.5), the release-history row, the stamps of `docs/RETENTION.md`,
  `docs/exit-codes.md` and the history page, `PayloadPolishTwoReleaseTest` (with the D-Docs pins and the roadmap row), the 2.29.12
  and 2.29.5 classes' given-up pins, and row 55 of `docs/ROADMAP.md` is `Done`. Verified in a scratch clone: `check-manager-block`
  agrees, `build` succeeds, `tools/release` (393) and `tools/docs` pass in the zlib-ng environment, eight of the nine suites pass
  from the stock `stage-conformance` fixture (the acceptance-matrix suite was not run); m8 fails the new pin alone.

## Functional review checklist

Gate: `AWAITING_FUNCTIONAL_REVIEW` for `payload-polish-2` (governing `2.2`, plan revision 2, implementation revision 1). Technical
approval is `CURRENT` on implementation bundle `b41a6b7fcc5d505bcc16cd392a6d5d3985d24506fe316545f703a8dec556ddc3`. Review the
committed content of this checklist: its evidence commit carries the trailer `Workflow-Functional-Checklist:
payload-polish-2/1/<blob>` and is reported with its SHA and blob when the gate is prepared.

Write findings to `.ai-review/payload-polish-2/feedback/FUNCTIONAL_REVIEW.md`.

### Setup

1. Check the branch: `git branch --show-current` must print `milestone/payload-polish-2`. Do not run `git switch` when it already
   does: a sandboxed run cannot write inside the product clone. Tracked files must match `HEAD`, except
   `docs/ai-workflow/WORKFLOW_STATE.json`, which the Controller's run writes; the evidence commit is `HEAD`.
2. Stock Python 3 and git. Nothing here needs the network, a real GitHub, a real `claude`, `codex` or `ssh`. The suites run
   offline with their own stand-ins.
3. Stage the conformance fixture from `HEAD` into a new empty directory outside the repository, `$TMPDIR/fixture`:
   `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`. It stages without adjustment,
   because CP3 moved the manifest records.
4. Automated state at `HEAD`. The last code change is `7282ffb`; `git diff --stat 7282ffb HEAD` lists only
   the Workflow's own records, `docs/ACTIVE_MILESTONE.md` and `docs/ai-workflow/WORKFLOW_STATE.json`, and no file of
   `payload/`, `tools/`, `manifest.json` or the documents the release changed. Of the nine suites, eight passed at CP3. The acceptance-matrix suite was run on
   2026-11-24 from the staged fixture: 453 tests, OK, 20 skipped. The skips are the `SkipTest` guards of the type-independent
   rows (for example A4 and B6 to B13), which run only on the process item. The `tools/release` tests (zlib-ng interpreter)
   passed at CP3 and were not re-run here.

### Test data

Nothing to seed. Each flow below uses the suite's own scratch repositories and stand-in `gh`. Do not run any flow against
`~/Workspace/repflow-android` (read-only, out of scope), and do not write inside the product clone.

### Flows

1. **Scope.** `git diff --stat d34217d -- payload` lists seven files: `ORCHESTRATION_PROTOCOL.md`,
   `workflow_integration_test.py`, `workflow_protocol.py`, `workflow_protocol_test.py`, `workflow_retention.py`,
   `workflow_state.py`, `workflow_state_completion_obligations_test.py`. `git diff --name-only d34217d -- .claude scripts
   .workflow-manager .github CLAUDE.md` lists nothing. **Expect:** exactly that.
2. **Retention code.** `git diff d34217d -- payload/scripts/workflow_retention.py | grep '^[-+][^-+]'`. **Expect:** only the
   no-rename constant and its helper `_before_the_rename`, the new `except OSError` arms (selection, the dry run's comparison,
   `_flow`), the single-note helper `_add_leftover_note`, the removed arm of `_judge_removal_archive`, and the `command`
   keyword of the walk, entry, scan and open helpers with its `remove` callers. No refusal order, exit code or archive text
   changes.
3. **State code.** `git diff d34217d -- payload/scripts/workflow_state.py | grep '^[-+][^-+]'`. **Expect:** one appended step in
   the plan-approval guard's final refusal, for the ordinary and the destructive guard; nothing else.
4. **Retention messages.** From `$TMPDIR/fixture/scripts`:
   `python3 -B workflow_state_completion_obligations_test.py RetentionErrorPathsTwo -v`. **Expect:** `Ran 23 tests`, `OK`,
   including `test_t7b3`, `test_t7b4`, `test_t7b5` and `test_t7d`. The new text says "this run renamed nothing" for every
   stray before the rename, and "renamed aside" never appears there. The walk and open refusals name `remove` for remove
   ("leave the review folder where it is") and `archive` for archive ("leave the item unarchived").
5. **Plan-approval guard step.** From `$TMPDIR/fixture/scripts`:
   `python3 -B workflow_integration_test.py -v -k test_acquire_guard_refuses_when_held_under_the_current_epoch_by_a_different_token`.
   **Expect:** `OK`. The refusal ends with its step: the takeover route for an ordinary guard, and for a destructive guard "let
   the owning session finish (no takeover authorization breaks a destructive window)" with no takeover command.
6. **Docs.** `grep -n 'workflow_retention.py' docs/exit-codes.md`: the rows for `report`, `archive`, `remove` and `prune` say
   `python3 -I scripts/workflow_retention.py <command>`, and no line has `python3 scripts/workflow_retention.py`. In
   `docs/RETENTION.md`, the `archives` sentence says it lists "every regular file named `*.tar.zst`" and that "a symlink or a
   directory of that name is not listed". **Expect:** both.
7. **Release bookkeeping.** `python3 tools/docs/check_docs.py` exits 0. `manifest.json` has `"workflow_version": "2.29.13"`.
   Row 55 of `docs/ROADMAP.md` reads `Done`. The release-history page has the 2.29.13 row. **Expect:** all four.

### Expected results, summary

Flows 1 to 3 show the change is confined to the named points. Flows 4 and 5 show the exact texts are pinned and pass. Flows 6
and 7 show the documentation and release bookkeeping. Any other result is a finding.

### Known limitations and out of scope

- No behaviour change. Refusal orders, exit codes, working paths and every message not named in the plan stay byte-identical.
- Not taken, by design (plan, sections 0 and 5): #119 6d (all three sub-points are true, or the advice would be false); the
  claim guard's final refusal, which names no step (F1); the advice for a manual `mv` back (F2); the `.removing` row of
  `docs/RETENTION.md` at line 475 (the doc twin of #119 2b), left for the next payload polish; `prune`, which never walks a
  review folder, so #119's "and prune" is not true and the command name is passed for `remove` only.
- The stray I/O errors and the lock-time duplicate-note path need an injected failure (`EIO`, a bad index). The suites inject
  them; they cannot be reproduced by hand on an ordinary host.
- Recorded, non-blocking optional findings (`optional_findings` in `WORKFLOW_STATE.json`, nine in all): the unreaped `zstd`
  child when `os.close(rfd)` fails after `Popen` in `_archive_table` (F-4967565c6d66), and the conditional pin of that subtest
  (F-f2f0cf92a893); two wording points about `docs/RETENTION.md` around lines 576 and 578, which say when the leftover is
  named and that it is named "once" (F-47f7462923a6, F-7d29fe83bf97). The last two are shipped doc sentences: check them
  when you test, and decide whether they block acceptance.
- Release `2.29.13` is not published. It is published only after this work is merged to `main`.

### Supported next steps

- Findings go to `.ai-review/payload-polish-2/feedback/FUNCTIONAL_REVIEW.md`. `/apply-functional-review` routes each one: the
  bounded branch for a fix inside this scope, the broad branch (a `payload-polish-2-remediation-<n>` child) for new or wider
  scope.
- Once testing is clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint of this item to be
  `COMPLETE`; CP1 to CP3 are, so nothing is outstanding. There is no command that accepts part of a round.
