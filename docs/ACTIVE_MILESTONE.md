# Active Milestone

## Milestone

**In progress (implementing).** W38: `retention-report-unreadable` (`process`, governing version `2.2`), branch
`milestone/retention-report-unreadable`, roadmap row 33 (RodrigoFAbreu/workflow#113 item 1, #116 item 1 and #119
item 8). Plan: `docs/ai-workflow/RETENTION_REPORT_UNREADABLE_PLAN.md` (revision 3, approved by gate policy). The goal,
Workflow 2.25.6 (a `fix:` patch, released after the merge of the pull request): the retention report says
`archive unreadable` / `review folder unreadable` where it cannot tell (a partly counted folder is a lower bound),
`review folder in .removing` for a folder an interrupted removal left, and records the failed directory itself in
`read_errors`. The JSON, every refusal code and exit code stay as they are. Base commit `e687d51`; the previous
milestone, W37 `retention-error-paths`, is accepted (Workflow 2.25.5).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The report text, the recorded path, tests and page | **complete** (see the commit of this checkpoint) |
| CP2 | Release 2.25.6 | **complete** (see the commit of this checkpoint) |

## Verified state

- CP1: `RetentionReportUnreadable` (T1 to T6) was red on the unedited tree and is green under `python3` (3.14) and
  `/home/rodrigo/.local/bin/python3.12`; the failure-only mutations m1 to m12 each fail at least one named test.
- CP1 staged in a disposable clone (D-Staging): the nine suites, `tools/docs`, `check_docs.py` and
  `check-manager-block` pass; `tools/release` has one failure owned by CP2, the 2.25.5 release class's pin of the
  obligations suite count (284; it is now 290 with the six new tests). CP2 moves that pin.

- CP2 (release 2.25.6), verified in a disposable clone of the working tree committed there: `RetentionReportUnreadable`
  green under `python3` (3.14) and `/home/rodrigo/.local/bin/python3.12`; `tools/release` (307 tests, zlib-ng
  interpreter), `tools/docs` (34), `check_docs.py`, `check-manager-block --manager-releases` and `release.py build`
  pass; `workflow-manager verify .` reports the installation matches 2.25.5 (the installation is not touched). The nine
  suites run from the stock `stage-conformance` fixture; the result is recorded in the implementation bundle.
  `conformance.suites` was measured (obligations suite 290), not typed.

## Next action

Run `/milestone-implement retention-report-unreadable` again: every checkpoint is complete, so the next invocation
enters `SELF_REVIEWING_IMPLEMENTATION`.
