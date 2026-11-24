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
- CP3 (release 2.29.13): not started.
