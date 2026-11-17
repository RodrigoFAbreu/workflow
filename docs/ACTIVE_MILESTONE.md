# Active Milestone

## Milestone

**Awaiting functional review** (`AWAITING_FUNCTIONAL_REVIEW`). W56: `retention-docs-notes` (`process`, governing version `2.2`), branch
`milestone/retention-docs-notes`, roadmap row 49. The plan is `docs/ai-workflow/RETENTION_DOCS_NOTES_PLAN.md` (revision 2, approved by
gate policy). The implementation review (revision 1) is approved and the technical approval is current, by gate policy.

## Goal

Three documentation points, no release (a `docs:` pull request, impact none): the 2.25.5 row of `docs/release-history.md` says a downgrade
also restores the `UnicodeDecodeError` tracebacks; `docs/RETENTION.md` says a refusal after the rename puts the folder back into `.ai-review/`;
the two raw reaper reports of `TEST_HARDENING_OWNER_POINTS_EVIDENCE.md` are kept next to it, with the unsaved A12/A15 mutation logs said to be
unrecoverable (RodrigoFAbreu/workflow#143 points 1 and 2, #188).

## Outcome

- CP1 (the three notes and roadmap row 49) is complete. Nothing under `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changed.
- Self-review (`ac05114`): the evidence file now names both scratch files the two JSON reports were copied from.
- At `ac05114`: the `tools/docs` tests, `check_docs.py`, the `tools/release` tests, `check-manager-block`, `check-title`
  (`impact=none`), `workflow-manager verify .` and the nine payload suites pass.
- Implementation review: `LOCAL_MODEL_IMPLEMENTATION_REVIEW` approved (round 1), and the technical approval is current by gate policy (`176f035`).

## Functional review checklist

Test the committed content of the checklist-evidence commit (its SHA and blob are reported when this checklist is prepared, not written
here). Write nothing inside the repository: put any output in a scratch directory (`$TMPDIR`).

### Setup

- Check out the evidence commit in a clean worktree. Docs only: no build and no install.
- Needs `git`, `python3` (standard library only), `sha256sum` and `wc`. No network, GitHub, `gh`, `claude`, `codex` or `ssh` is needed.
- Flow F2 runs from a conformance fixture. From the repository root:
  `python3 tools/release/release.py stage-conformance --commit <evidence-sha> --out "$TMPDIR/fixture"`

### Test data

Nothing to seed. The two raw reports are committed (`docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_REAPER_REPORT.json` and
`docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_REAPER_INVESTIGATION.json`). The retention tests build their own folders in the scratch fixture.

### Flows

**F1: the 2.25.5 downgrade note (#143 point 1)**

1. In `docs/release-history.md`, read the 2.25.5 row. Its sentence on going back to 2.25.4 says the downgrade restores the
   `UnicodeDecodeError` traceback for a state file that is not valid UTF-8, and for a tracked path that is not UTF-8 under a UTF-8 locale
   (under a single-byte locale 2.25.4 counts such a path again).
2. `git show v2.25.4:payload/scripts/workflow_retention.py | grep -c UnicodeDecodeError` prints `0`.
   `git show v2.25.5:payload/scripts/workflow_retention.py | grep -c UnicodeDecodeError` prints `2`.
3. In the same 2.25.4 file, the `git ls-files` call passes `text=True`, so a single-byte locale decodes a non-UTF-8 path without error.

Expected: the row's claim matches the 2.25.4 and 2.25.5 source.

**F2: the refusal after the rename (#143 point 2)**

1. In `docs/RETENTION.md`, the `remove` section (around line 575), read the sentence that says that after the rename the folder is
   renamed back into `.ai-review/`, the message says "the folder is back in" its place, and a leftover whose verification could not complete
   stays in `.removing/<id>`.
2. `grep -n "back in" payload/scripts/workflow_retention.py` shows the message appended after the restore, and a leftover whose
   verification did not complete is raised without a restore.
3. From the staged fixture's `scripts/` directory, run (one line):
   `python3 -B workflow_state_completion_obligations_test.py RetentionRemove.test_w37_t5_an_unreadable_symlink_after_the_rename_puts_the_folder_back RetentionRemove.test_w37_t5b_an_unreadable_symlink_in_a_leftover_keeps_it_where_it_is RetentionRemove.test_w37_t5c_an_unreadable_symlink_at_the_recheck_puts_an_incomplete_leftover_back RetentionErrorPathsTwo.test_t3b_a_failed_hash_walk_after_the_rename_puts_the_folder_back RetentionTestPins.test_p5_a_stat_only_change_after_the_hash_puts_the_folder_back_and_deletes_nothing </dev/null`

Expected: `Ran 5 tests` and `OK`. The preparer ran this on a fixture staged from `176f035` and got that result.

**F3: the raw reaper reports (#188)**

1. `sha256sum` of the two JSON files prints `f965db8e91df0c93df73488fa243295ef98688ee29f9333b6869295485572ec9` for
   `TEST_HARDENING_OWNER_POINTS_REAPER_REPORT.json` and `615de6f7173b2a3b3b83b49b6c5d2aca8e126c864e662a26a12561d0472b7d04` for
   `TEST_HARDENING_OWNER_POINTS_REAPER_INVESTIGATION.json`. `wc -c` prints 4136 and 4192.
2. Both files parse as JSON with `chunk_status` 0 and `supported` true, and each has 79 `orphans`, all with `fate` `exited`. The REPORT
   has 78 `[git]` and 1 `git maintenance`; the INVESTIGATION has 77 `[git]` and 2 `git maintenance`.
3. In `docs/ai-workflow/TEST_HARDENING_OWNER_POINTS_EVIDENCE.md`, read "The raw reports of Point 1 are kept next to this file". It says the
   REPORT is a later run and not the run the text calls "this run", that the INVESTIGATION is the investigation run, and that the A12/A15
   mutation logs were never saved and cannot be reconstructed.

Expected: digests, sizes and counts match, and the text says which run each file is.

**F4: docs only, no release (R3)**

1. `git diff --name-only 9aacb87 <evidence-sha> -- payload tools fixtures templates manifest.json` prints nothing.
2. `git diff 9aacb87 <evidence-sha> -- docs/release-history.md` changes one row only, the 2.25.5 row.

Expected: no shipped file changed, so there is no release.

**Automated checks (step 1 of the command)**

- From the repository root: `python3 -B tools/docs/check_docs.py` exits 0, and `python3 -B -m unittest discover -s tools/docs -p '*_test.py'` prints `OK`.
- The nine payload suites last passed at `ac05114`. No shipped file has changed since (F4), so that result stands.

### Known limitations (out of scope for this milestone)

- No release: no change to `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json`. The pull request is `docs:` with impact none.
- The A12/A15 mutation logs were never saved and cannot be reconstructed. The evidence table is the only record of those runs.
- The two reaper runs came from `workflow-manager`'s `tests/parallel/reaper.py`, which is not in this repository. Their raw output can be checked here; the command cannot be rerun here.
- The write times in the evidence (12:58:17Z and 12:22:39Z) come from the scratch files. The JSON does not hold them, so the repository cannot check them.
- This milestone closes no issue, posts no comment and opens no pull request. #170 point 2 stays open.

## Next action

The user runs F1 to F4 and the automated checks above, then places findings at `.ai-review/retention-docs-notes/feedback/FUNCTIONAL_REVIEW.md`.
If testing is clean, `/accept-milestone` is the only acceptance command, and CP1 is the only checkpoint and is `COMPLETE`. If a finding needs a
fix, `/apply-functional-review` routes it.
