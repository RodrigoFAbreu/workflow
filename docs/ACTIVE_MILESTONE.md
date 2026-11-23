# Active Milestone

## Milestone

**Awaiting functional review.** W62: `workflow-docs-wording` (`process`, governing version `2.2`), branch
`milestone/workflow-docs-wording`. It has no `docs/ROADMAP.md` row, and the roadmap is untouched. Issues RodrigoFAbreu/workflow#173
point 1 and #161 point 1. The plan is `docs/ai-workflow/WORKFLOW_DOCS_WORDING_PLAN.md` (revision 1).

## Goal

Two documentation sentences say what the engine already does. No product behaviour, payload file, manifest field, command, message,
roadmap row or release changes.

- `docs/common-problems.md`, "An approval became stale after a change": the plan route now says that a plan amendment is possible only
  at `IMPLEMENTING` or `SELF_REVIEWING_IMPLEMENTATION`.
- `docs/release-history.md`, the 2.28.0 row: `--write-findings-record` exits 0 with the paths to stage (the record, and the dispositions
  file when it exists; `[]` for an item with no finding). The row said "the record path (or nothing, for an item with no finding)".

The release tests gain assertions inside two existing methods. No test method is added or removed.

## Outcome

- CP1 (`1fcad47`) and CP2 (`0bc3d5a`) are complete. The plan was approved by gate policy at revision 1.
- Implementation review round 1 is APPROVE from both the local and the external reviewer. The technical approval was recorded by
  policy (`3c67a85`).
- Verification at `0bc3d5a`, recorded in `.ai-review/workflow-docs-wording/current/TEST_RESULTS.md`: the nine payload suites, `tools/release`
  (386 tests), `tools/docs` (34 tests), `check_docs.py`, `check-manager-block`, `workflow-manager verify .`, `check-title` (`impact=none`),
  the reaper on the two pin classes, and a failure-only mutation of each page. All pass. The commits after it (`61565b7`, `3c67a85`) change
  only `docs/ai-workflow/WORKFLOW_STATE.json`, so the verified tree is unchanged.
- Not taken: #173 points 2 and 3, and #161 points 2 and 3 (fixed on main, or a finished item's plan prose). See the plan, section 0 and
  section 5.
- Nothing is pushed, merged or published. There is no Workflow release and no Manager pin.

## Next action

Test by the checklist below. Put findings, if any, at `.ai-review/workflow-docs-wording/feedback/FUNCTIONAL_REVIEW.md`. Then run
`/apply-functional-review` for each finding. Once testing is clean, `/accept-milestone` is the only acceptance command, and it needs every
checkpoint in this item's registry to be `COMPLETE`. Both checkpoints are complete, so no checkpoint is outstanding.

## Functional review checklist

The checklist content is committed in the checklist-evidence commit named in the `/prepare-functional-review` report. Test that commit,
or the working tree after it, which must be clean.

### Setup

- Check out `milestone/workflow-docs-wording` at its HEAD. `git status --short` must print nothing.
- The base commit `7a486a296617a60cea51d8437d2718335c4b7ed0` must be in the local object store: `git cat-file -t 7a486a2` prints `commit`.
- Needed: `git` and Python 3 (standard library only). No build, no install, no feature flag and no network. No GitHub call is made.
- Read-only flows write nothing. The failure-only flow in step 9 writes only to a scratch directory.

### Test data

None. The data is the git history: the base commit `7a486a2` and the branch HEAD.

### Flows

Run from the repository root. Each step gives the expected result.

1. **Scope of the change.** `git diff 7a486a2 --stat -- docs/common-problems.md docs/release-history.md tools`
   - Expect 3 files: `docs/common-problems.md` (5 lines changed), `docs/release-history.md` (2), `tools/release/release_test.py` (7).
     Summary: `3 files changed, 11 insertions(+), 3 deletions(-)`.
2. **Nothing shipped moved.** `git diff 7a486a2 --name-only -- manifest.json payload .claude scripts .workflow-manager .github CLAUDE.md`
   - Expect no output.
3. **The 2.28.0 row changes one clause.** `git diff --word-diff 7a486a2 -- docs/release-history.md`
   - Expect one line, the 2.28.0 row, with one change: `record path (or nothing, for an item with no finding)` is replaced by
     `paths to stage (the record, and the dispositions file when it exists; `[]` for an item with no finding)`.
   - `git diff 7a486a2 --stat -- docs/release-history.md` prints `1 insertion(+), 1 deletion(-)`. No other row changes.
4. **The common problems sentence reads correctly.** Open `docs/common-problems.md` at "An approval became stale after a change", lines 11
   to 18 (the line numbers may shift by one).
   - Expect the plan route to end "...and the plan approval (a plan amendment is possible only while the work item is at `IMPLEMENTING`
     or `SELF_REVIEWING_IMPLEMENTATION`; at any other phase `/request-plan-amendment` refuses and names the phase); for code, ...".
   - Check by eye that the sentence is grammatical and the parenthesis closes. The code route after the semicolon is unchanged.
5. **The page says nothing else new.** `git diff -U0 7a486a2 -- docs/common-problems.md`
   - Expect one hunk. Its only added words are the parenthesis in step 4. The "Last checked with: Workflow 2.29.5." line is unchanged.
6. **The sentence matches the engine (read-only).** `grep -n "_AMENDMENT_REQUEST_ALLOWED_PHASES" payload/scripts/workflow_state.py`
   - Expect the frozenset at line 14828 to hold exactly `IMPLEMENTING` and `SELF_REVIEWING_IMPLEMENTATION`.
7. **The pins pass.** `python3 -m unittest tools.release.release_test.WordingPassPlainCommandsReleaseTest tools.release.release_test.AcceptanceFindingsFloorReleaseTest`
   - Expect `Ran 7 tests`, `OK`.
8. **The release title and docs check.** `python3 tools/release/release.py check-title "docs: state the amendment phase limit and the findings-record output"`
   then `python3 tools/docs/check_docs.py`
   - Expect `impact=none` and exit 0, then exit 0.
9. **The pins catch a reverted sentence (failure-only, scratch copy).** Repeat for each page:
   `scratch=$(mktemp -d); git archive HEAD | tar -x -C "$scratch"; git show 7a486a2:docs/common-problems.md > "$scratch/docs/common-problems.md"; (cd "$scratch" && python3 -m unittest tools.release.release_test.WordingPassPlainCommandsReleaseTest tools.release.release_test.AcceptanceFindingsFloorReleaseTest)`
   - Common problems: expect one failure, in `test_the_pages_carry_the_corrected_wording_and_their_last_checked_line`.
   - Release history: use `git show 7a486a2:docs/release-history.md` in a fresh scratch directory. Expect one failure, in
     `test_the_release_history_rows_name_the_release_and_the_way_back`.
   - Expect the other pins to pass in each run.
10. **The wider release and docs suites (optional).** `python3 -m unittest discover -s tools/release -p '*_test.py'` and
    `python3 -m unittest discover -s tools/docs -p '*_test.py'`
    - Expect `OK`. The recorded counts are 386 and 34. The implementation bundle ran `tools/release` under a specific interpreter (see
      `TEST_RESULTS.md`). If plain `python3` cannot import it in your environment, record that as an environment limit and do not count
      it as a failure.
11. **Installation and manager block (operator, on the host).** `workflow-manager verify .` and
    `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`
    - Expect `.: installation matches workflow 2.29.11`, exit 0, and `ok: 2.29.11 carries a valid manager block ...`, exit 0.
    - `workflow-manager` is not on the sandbox's PATH, so this flow runs on the host.
12. **Manual read of the two pages.** Read the changed sentence in `docs/common-problems.md` and the 2.28.0 row in `docs/release-history.md`
    as a user would. Expect each to say what the step 4 and step 3 results say, with no contradiction in the rest of the paragraph or row.

### Known limitations and out of scope

- Not taken: #173 points 2 and 3, and #161 points 2 and 3 (see the plan, section 0). The plan's line numbers for the 2.28.0 row
  (23, now 25) are historical; the implementer found the row by its text.
- No `docs/ROADMAP.md` row, no release, no Manager pin, no push or merge.
- The nine payload suites are not part of this review's flows. The payload is unchanged since `0bc3d5a`, and they passed there.
- The reaper check in the plan's verification list runs on the Manager's `tests/parallel/reaper.py`, outside this repository. It is an
  operator check on the host.
