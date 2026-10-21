# Active Milestone

## Milestone

**In progress.** W16: `review-followups-2` (`process`, governing version `2.2`), branch
`milestone/review-followups-2`, roadmap row 19 (RodrigoFAbreu/workflow#60 item 60e, #64 item
64c, #68). Plan: `docs/ai-workflow/REVIEW_FOLLOWUPS_2_PLAN.md` (revision 1, approved by gate
policy). The goal is Workflow 2.18.2, a patch release (`fix:`). The previous milestone, W15
`review-followups-cleanup`, is accepted (its record is in git history and
`docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | Command files: the early collision check and the guard re-wrap | **complete** (60e, 64c) |
| CP2 | Verification commands and the Optional findings | **complete** (#68, Optional findings) |
| CP3 | Release 2.18.2 | **complete** (release 2.18.2) |

### CP1 verified state

- 60e: `milestone-plan.md` step 1's `[2.1]` bullet carries a "Declared-backlog collision check"
  before the `route_work_item` call: a discarded `generate_artifacts_declarations(...,
  repo_root=<repo_root>)` call whose refusal stops the run with nothing written. The needle test
  (`test_plan_refuses_a_declared_backlog_collision_before_routing`) failed against the unedited
  command file (substring not found) and passes now; the behavioural tests in
  `workflow_state_test.py` (a colliding declaration leaves the tree byte-identical, for both work
  item types; an undeclared repository gets the plain template) pass by design, as the plan says.
  The undeclared steps-1-to-5 digest (`814f7c63...`) did not move.
- 64c: the six user-only command files are re-wrapped to at most 78 columns on every prose line
  that was over 90. `TestUserOnlyCommandLineWidth` failed on the base files (32 lines) and
  passes on the re-wrapped ones. Per file, `' '.join(old.split()) == ' '.join(new.split())`
  against the base holds for all six. The one line left is `approve-review.md`'s unbreakable
  91-column single-span line (OD-3); front matter, code fences, tables and headings are exempt.
- `_GOLDEN_COMMAND_FILE_SHA256` is re-recorded for the seven changed files.

Verified in a disposable clone (D-Staging): the nine payload suites, the `tools/release` and
`tools/docs` tests (see the checkpoint commit's report for the exact results).

### CP2 verified state

- #68: `docs/RELEASING.md` has a `## Verification commands` section (the nine suites from a staged
  fixture, run from inside the fixture; the `tools/release` tests with the zlib-ng Python; the
  `tools/docs` tests and checker; `check-manager-block` with `--manager-releases`; `workflow-manager
  verify .`), and `CLAUDE.md`'s "Releases" list points to it, outside the managed block.
  `VerificationCommandsSectionTest` pins the forms and that `payload/scripts/*_test.py` appears only in
  the "never" sentence. Each form was run: `stage-conformance` exit 0 and `fixture=...`; a suite from
  the fixture exit 0 (`Ran 344 tests ... OK`); `unittest discover -s tools/docs -p '*_test.py'` exit 0
  (34 tests; the bare `discover tools/docs` ran 0 tests); `check_docs.py` exit 0;
  `check-manager-block` exit 0 (`ok: 2.18.1 carries a valid manager block ...`) and exit 2 without
  `--manager-releases` (usage error); `workflow-manager verify .` exit 0 (`installation matches workflow
  2.18.1`) and, with an empty `--release-cache` and a missing `--release-source`, exit 1 (`error: cannot
  fetch ...`). Running the integration suite from this repository's root instead of the fixture fails
  (it reads the installed commands); the section now says to run from inside the fixture.
- Optional findings: `state_transaction`'s `on_failure` docstring now says an `Exception` is suppressed
  and a `KeyboardInterrupt`/`SystemExit` propagates (needle test red first; the interrupt test passes by
  design, it pins the code). `\Z` replaces `$` in `TAG_RE`, `_SHA256_RE` (both red first: a `v2.18.2\n`
  tag was taken as a release, a `sha256` with a trailing newline was accepted) and `_MANAGER_VERSION_RE`
  (its call site uses `fullmatch`, so no behaviour was wrong; its pattern-level test is a consistency pin).

Verified in a disposable clone (D-Staging): the nine payload suites (integration from inside the
fixture), `tools/release` (zlib-ng Python), `tools/docs` and `check_docs.py`, `check-manager-block`.

### CP3 verified state

- Release 2.18.2: `manifest.json` `workflow_version`, sha256/size and a `review-followups-2 (workflow-2.18.2)`
  sentence on each of the 13 changed records, the posture, and `conformance.suites` measured by
  `release.py manager-block --write` (state 1201, integration 348; the others unchanged, so the
  acceptance-matrix count in `docs/RELEASING.md` stays 453). `WORKFLOW_RELEASE`, its two pinned
  assertions and the `ORCHESTRATION_PROTOCOL.md` mentions follow; the protocol stays 1.5. The history
  has the 2.18.2 row, the corrected 2.18.1 sentence (60e) and the "Last checked" line;
  `release_test.py` has `ReviewFollowups2ReleaseTest` and the 2.18.1 class no longer pins the current
  version.
- Verified in a disposable clone: the nine suites from a stock `stage-conformance` fixture (integration
  from inside the fixture) all OK; `tools/release` 220 tests OK (zlib-ng Python); `tools/docs` 34 OK;
  `check_docs.py` clean; `check-manager-block` ok; `release.py build` succeeds; `workflow-manager
  verify .` matches 2.18.1 (the installation is unchanged).

## Functional review checklist

This is a process milestone (Workflow 2.18.2, a patch release); there is no app to run. The
manual check is that the changed commands and documents behave as the CP verified states say.
Run everything from the repository root on branch `milestone/review-followups-2` with a clean tree.

### Setup

- A disposable clone or a scratch directory for the staged fixture; do not run the suites from
  inside this repository's installed tree (the integration suite reads the installed commands).
- Python 3 for the suites; the zlib-ng Python for `tools/release` (see `docs/RELEASING.md`,
  "Verification commands").

### Test data

None to seed. The staged fixture comes from `stage-conformance`; the collision flow below
needs a scratch repository whose declared backlog already holds an id you then try to plan.

### Flows

1. **Verification commands section.** Open `docs/RELEASING.md` "Verification commands" and
   `CLAUDE.md`'s "Releases" list. Expected: the section lists the nine suites (run from inside the
   staged fixture), the `tools/release` tests, the `tools/docs` tests and checker,
   `check-manager-block` with `--manager-releases`, and `workflow-manager verify .`; `CLAUDE.md`
   points to it outside the managed block.
2. **Run those commands as written.** Stage a fixture with `stage-conformance`, run one suite from
   inside it, then run `unittest discover -s tools/docs -p '*_test.py'`, `check_docs.py`, and
   `check-manager-block`. Expected: each exits 0 (a suite reports `OK`; `tools/docs` reports 34
   tests); `check-manager-block` without `--manager-releases` exits 2 (usage error).
3. **Early collision check (60e).** Read `payload/.claude/commands/milestone-plan.md` step 1's
   `[2.1]` bullet. Expected: a "Declared-backlog collision check" precedes the `route_work_item`
   call, and a refusal there stops the run with nothing written. Optionally, in a scratch
   repository, plan an id that collides with a declared backlog entry. Expected: refusal, tree
   byte-identical; an undeclared repository gets the plain template.
4. **Guard re-wrap (64c).** Check the six user-only command files (`accept-milestone`,
   `adopt-gate-policy`, `approve-review`, `request-plan-amendment`, `resume-implementation`,
   `retire-legacy-work-item`). Expected: no re-wrapped guard paragraph has a line over 78 columns except `approve-review.md`'s
   one unbreakable 91-column line (unchanged prose elsewhere in the files, e.g. `accept-milestone.md:121`, is out of
   scope); wording unchanged (whitespace-normalised text equals the base).
5. **Trailing-newline hardening.** Expected: `TAG_RE`, `_SHA256_RE` and `_MANAGER_VERSION_RE` end in
   `\Z`; a `v2.18.2\n` tag is not taken as a release.
6. **Release 2.18.2 bytes.** Expected: `manifest.json` names `2.18.2`; `release.py build` succeeds;
   `workflow-manager verify .` still matches 2.18.1 (this repository's installation is untouched
   until the release is published and installed); published tags and assets are not modified.

### Functional review round 1

- Flow 2 (doc defect, fixed): the "Verification commands" section changed into the staged fixture's
  `scripts` directory and never left it. It now runs the nine suites in a subshell (a loop over the
  manifest's `manager.conformance.suites`), so every block below it runs, in order, from the
  repository root; the `VerificationCommandsSectionTest` pin follows the new form. Every block was
  run in sequence in a scratch clone (zlib-ng venv Python for `tools/release`, scratch cache primed
  from `~/.cache/workflow-manager/releases/2.18.1`): block 1 (stage + nine suites) exit 0; block 2
  (220 `tools/release` tests, 34 `tools/docs` tests, `check_docs.py`) exit 0 each; block 3
  (`check-manager-block`) exit 0; block 4 (`workflow-manager verify .`) exit 0, installation matches
  2.18.1; the working directory stayed the repository root throughout. `docs/RELEASING.md` is not
  shipped, so no manifest record changed.
- Flow 4 (checklist, no code change): the width expectation now covers only the re-wrapped guard
  paragraphs; unchanged prose such as `accept-milestone.md:121` (80 columns) is out of scope.
- Re-test: flow 2 (run the section top to bottom from the repository root) and flow 4.

### Known limitations / out of scope

- This repository's own installation (`.claude/`, `scripts/`, `docs/ai-workflow/` managed files)
  stays at 2.18.1 until 2.18.2 is published and installed through `workflow-manager update`.
- Publishing the release, the `workflow-manager` pin and the pull request are not part of this gate.
- The one over-width line in `approve-review.md` is accepted (OD-3).

## Next action

All checkpoints complete. Run the checklist above, then `/accept-milestone review-followups-2` if
clean, or write findings to the feedback file and run `/apply-functional-review`.
