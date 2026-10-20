# W16: Workflow 2.18.2 — review follow-up clean-up 2 (Revision 1)

- **Work item:** `review-followups-2` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner asked for it on 2026-10-20
  ("apply the fixes"). It is row 19 of `docs/ROADMAP.md` (added by this plan with the status `Next`).
- **Issues:** RodrigoFAbreu/workflow#60 (item 60e), #64 (item 64c), #68.
- **Branch:** `milestone/review-followups-2`
- **Base commit:** `a0ec8cf` (main after #70: the release source is Workflow 2.18.1; this
  repository's own installation is also 2.18.1, automatic gates, default `2.2`, no
  `GATE_POLICY.json`, no backlog file declared, so the prose roadmap applies)
- **Plan revision:** 1. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.2, a patch release (`fix:`), that clears what W15 deferred or found:

1. **60e.** `/milestone-plan` refuses a declared-backlog protected-path collision
   (`declaration_conflict`) in step 1, before it creates the work item or writes the registry
   and mapping.
2. **64c.** The long guard lines of the six user-only command bodies are re-wrapped to the
   files' usual width, a pure re-wrap.
3. **#68, command forms.** One short "verification commands" section that functional
   checklists for this repository copy from, with command forms that run as written.
4. **#68, the four Optional findings:** the `state_transaction` docstring, three regular
   expressions that accept a trailing newline (two of them only latently), and the release
   history's list of what stayed open.

Why `fix:` and not `feat:` (OD-1): nothing here adds a capability. 60e moves an existing
refusal (same code, same exception class, same text) earlier; 64c changes line breaks; the
rest corrects a docstring, hardens patterns and corrects documents. A patch keeps the version
change in step with the pull-request title.

### Hard limits (invariants)

- **No state field, ledger, phase, trailer, commit shape or protocol change.** No new refusal
  code: 60e reuses `declaration_conflict`. No new `describe` or envelope field, no new script
  command.
- **No Controller or Manager change.** `min_manager_version` stays 1.13.0, and the CI pin in
  `tools/release/manager-pin.json` must EQUAL it (owner decision 2026-10-20 on #39); it does
  today, and no checkpoint changes either.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`,
  `docs/ai-workflow/` managed documents, `.workflow-manager/`, the managed blocks of
  `CLAUDE.md` and `.gitignore`, and `.github/workflows/workflow-conformance.yml`. Fixes go to
  `payload/`, `tools/`, `docs/` user documents and `manifest.json`. The one `CLAUDE.md` line
  CP2 adds sits outside the managed block.
- **Undeclared repositories are unchanged.** The new step 1 text sits in a `[2.1]` bullet,
  so the golden digest of the steps 1 to 5 an undeclared repository reads
  (`workflow_integration_test.py`, the `814f7c63…` constant) must NOT move, and the
  undeclared declaration digests (`_GOLDEN_UNDECLARED_DIGESTS`) stay as they are.
- **Size:** three checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test, written first and shown to fail against
  the unfixed code where the item is a defect (the "red first" rule); the nine payload suites
  from a staged fixture; the `tools/release` tests (in the zlib-ng environment); the
  `tools/docs` tests and checker; the per-file whitespace-normalised equality of the six
  re-wrapped command files; every command form of the new section actually run; `workflow-manager
  verify .` clean.
- **Aids (never a stop):** the line-length census of CP1; the per-record hunk reading of the
  manifest rationales against `git diff` (CP3).

**Red first.** For every defect item the checkpoint runs the new test against the pre-fix code
before applying the fix and records the failure. A test that passes without the fix does not
count; where a pin cannot fail first (a pattern already protected by its call site), the
checkpoint says so instead of claiming red (section 2).

## 2. Facts this plan relies on (re-checked against `a0ec8cf`)

- **60e today.** `declaration_conflict` is raised only inside
  `generate_artifacts_declarations` (`_classify_declared_backlog` →
  `workflow_backlog.protected_conflicts`), which `/milestone-plan` step 3 calls after step 1
  has created the work item (`route_work_item`) and step 3 has written the registry and
  mapping. The check depends only on facts known at step 1: the declared paths (read from
  `WORKFLOW_CONFIG.json`), the id, the three artifact paths and the work item type. The
  function writes nothing (it returns the template), so calling it early is a pure check.
  The acceptance pre-flight runs the same predicate through `check_declaration_conflict`.
- **The undeclared hash is over steps 1 to 5 with the `[2.1]` bullets stripped.**
  `_strip_bracketed_2_1_bullets` removes the "Derive a `work_item_id` slug" bullet, which is
  where `route_work_item` is called; text added there does not move the constant. Text added
  to the version-independent "Backlog declared" bullet would.
- **64c census.** Lines over 90 columns, outside the front matter, code fences and tables:
  accept-milestone.md 4 lines
  (longest 770), approve-review.md 14 (longest 770), adopt-gate-policy.md 4, request-plan-amendment.md 5
  (longest 479), resume-implementation.md 6, retire-legacy-work-item.md 5. Exactly one of those lines cannot
  be re-wrapped: `approve-review.md` line 322 is a 3-space indent plus one span with no space
  inside it (`` `workflow_fingerprint.compute_review_content_id_plan_stage[_at_commit[_for_work_item]]`/ ``),
  91 columns in all. It is the single unbreakable line (OD-3, D-64c). The front matter's
  `description:` lines (94 to 200 columns) are YAML single-line values a harness parses;
  they are not guard lines and are left alone (OD-3). Lines inside code fences and table rows
  are also left alone. The guard pin tests fold whitespace (`_squash`), so a re-wrap cannot
  break them; the golden hashes (`_GOLDEN_COMMAND_FILE_SHA256`, seven entries move: these six
  and `milestone-plan.md`) are re-recorded.
- **The trailing-newline class is two real cases and one latent one.**
  `release.py` `TAG_RE` is used with `.match` (lines 297, 302) and `package._SHA256_RE` with
  `.match` (line 215): `$` accepts a trailing newline there, so these are defects.
  `manager_block._MANAGER_VERSION_RE` is used only with `fullmatch`, which already rejects
  `"1.13.0\n"`; switching it to `\Z` is consistency (matching `package.VERSION_RE`) and its
  test is a pin that cannot fail first. `manager_block._TAG_RE` and `_VERSION_RE` are
  likewise `fullmatch`-only and were handled by W15; they are left alone.
- **The docstring.** `state_transaction`'s `on_failure` text says an exception raised by
  `on_failure` is suppressed; the code suppresses `contextlib.suppress(Exception)`, so a
  `KeyboardInterrupt` or `SystemExit` raised by `on_failure` replaces the original.
- **Command forms (each run at this base).** `release.py check-manager-block` fails without
  `--manager-releases` (usage error) and prints `ok: 2.18.1 carries a valid manager block…`
  with `--commit HEAD --manager-releases tools/release/manager-releases.json`;
  `python3 -m unittest discover tools/docs` runs 0 tests, and `-s tools/docs -p '*_test.py'`
  runs 34; `workflow-manager verify .` prints `installation matches workflow 2.18.1` here
  because the user release cache holds the installed release.
- **Where the section lives.** `docs/RELEASING.md` is maintainer content: not shipped, not a
  user page for the docs checker (excluded: no header or id rules), and it already holds
  "Building locally" and the CI command lines. `docs/README.md` is a user page with link and
  id rules and would pull maintainer commands into the user map.
- **The 2.18.1 history row** lists "39j … and 64c" as still open; 60e was open too (deferred
  with 64c, W15 OD-9).

## 3. Design decisions

### D-Patch: the version is 2.18.2, `fix:`

`manifest.json` `workflow_version` 2.18.2; `WORKFLOW_RELEASE` and its two pinned assertions
in `workflow_protocol_test.py` follow, with the matching `ORCHESTRATION_PROTOCOL.md` edits
(tested-releases list, envelope example, protocol-1.5 note); the protocol version stays.

**Downgrade posture.** An older release reads every state, ledger and file 2.18.2 writes:
nothing it reads changes. Per area, `workflow-manager update` back to 2.18.1 restores:
the collision refused at step 3 instead of step 1 (after the work item exists; the refusal
and its text are the same); the unwrapped guard lines (the same words); the docstring (no
behaviour). The release tooling (`tools/`) and `docs/` are not part of the installed
release. CP3 writes this into the manifest `manager` block and the release history.

### D-60e: a write-free dry call in the `[2.1]` bullet that routes the work item

The "Derive a `work_item_id` slug" bullet gains, **before** its "Call
`workflow_state.route_work_item(...)`" sentence, a **Declared-backlog collision check**:
call `workflow_state.generate_artifacts_declarations(<work_item_id>, <plan_path>,
<registry_path>, <mapping_path>, work_item_type=<this item's own work_item_type>,
repo_root=<repo_root>)` with the four facts just derived, and discard the result. It writes
nothing. A refusal (`workflow_backlog.BacklogError` with code `declaration_conflict`, or
`workflow_state.BacklogScriptUnavailableError`, code `declaration_invalid`) is reported
verbatim, with its next step, and the run **stops with nothing written**: no work item, no
registry, no mapping.

Why this form (OD-2): it runs the very predicate step 3 will run, on the very template step 3
will generate, so the two cannot disagree; the alternatives either add a script command
(a protocol-visible surface this patch forbids) or rebuild the template by hand (a second
copy of `_classify_declared_backlog`). Why unconditional: for an undeclared repository the
call returns the template unchanged and does nothing, so there is no `declared` branch to
get wrong, and the explicit work-item-id forms (which never read the backlog file) are
covered the same way. Step 3's generation stays, because it produces the file.

### D-64c: a deterministic re-wrap, proven by whitespace-normalised equality

A scratch script (in `$TMPDIR`, not a deliverable) rewrites, in each of the six files, every
line over 90 columns that is neither front matter, a code-fence line, a table row nor a
heading, into lines of at most 78 columns, breaking only at spaces (never inside a word,
never at a hyphen), continuing at the line's own leading indentation plus its list-marker
width. A line that cannot be broken at a space to fit, because everything past its
indentation is one span with no space inside it, is left as it is: the only such line is
`approve-review.md` line 322 (91 columns, see section 2). The scratch script lists every line
it leaves. Shorter lines are untouched, so the diff holds only the long lines. CP1 proves "no
word changed" per file with `' '.join(old.split()) == ' '.join(new.split())` against
`git show a0ec8cf:<file>`, and a permanent test asserts that no non-exempt line of the six
files exceeds 90 columns, so the files do not drift back. The test's exemptions are the
front matter, code-fence lines, table rows, headings, and a line whose only content past its
indentation is one span with no space inside it (it cannot be broken at a space).

### D-Commands-Doc: the section is in `docs/RELEASING.md`, pointed to from `CLAUDE.md`

A new `## Verification commands` section (CP2) gives the exact runnable forms, in a code
block per form with one line each saying what it checks and when it matters:

- payload suites: `python3 tools/release/release.py stage-conformance --commit HEAD --out
  "$TMPDIR/fixture"`, then each `python3 -B "$TMPDIR/fixture/scripts/<suite>_test.py"` of
  the nine suites (never `payload/scripts/*_test.py`, which also picks up the opt-in
  historical demo suites); a checkpoint that changed a shipped file before the release
  checkpoint stages from a scratch clone with adjusted manifest records, and says so;
- `tools/release` tests with the zlib-ng environment's Python
  (`python -m unittest discover -s tools/release -p '*_test.py'` or the file name), with the
  zlib-ng note and a pointer to "Building locally"; and `tools/docs`
  (`python3 -m unittest discover -s tools/docs -p '*_test.py'`), plus
  `python3 tools/docs/check_docs.py`; the sentence that a bare `discover tools/release` runs
  zero tests;
- `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases
  tools/release/manager-releases.json`;
- `workflow-manager verify .`, with the note that offline it needs the installed release's
  assets in the release cache (`--release-cache` / `$WORKFLOW_MANAGER_RELEASE_CACHE`).

A test in `release_test.py` pins each command form as a needle and that
`payload/scripts/*_test.py` appears only in the "never" sentence. The shipped
`/prepare-functional-review` is not changed (OD-4): its text is generic to every
repository, and a pointer in it would be a command-file change in a patch whose command
changes are 60e and 64c. The checklist author is pointed to the section from this
repository's own `CLAUDE.md` ("Releases" bullet list, outside the managed block). This
milestone's own functional-review checklist uses these forms.

### D-Optional: the four findings

- **`on_failure` wording: narrow it** (OD-5) to "an `Exception` raised by `on_failure` is
  suppressed". Suppressing `BaseException` would swallow a `KeyboardInterrupt` during an
  undo, which hides an operator interrupt behind the original error; the narrow wording
  matches the code and changes no behaviour. A needle test in `workflow_state_test.py`
  pins the corrected phrase and that a `KeyboardInterrupt` from `on_failure` propagates.
- **`\Z` in the three patterns** with a trailing-newline rejection test each (red first for
  `TAG_RE` and `_SHA256_RE`; a pin for `_MANAGER_VERSION_RE`, section 2).
- **The history rows** (OD-6): the 2.18.1 row's "Still open" sentence gains 60e (it was open
  then; the omission is a plain error, corrected), and the 2.18.2 row says 60e and 64c are
  fixed by this release, with what stays open (39j is decided separately; nothing else).

### D-Staging: scratch staging for CP1 and CP2 (the procedure W15 used)

`release.py stage-conformance` and `tools/release/release_test.py` verify the manifest against
the tree, and CP1 and CP2 change shipped files whose digests the committed manifest records
only at CP3. So each verifies in a **disposable clone** (`$TMPDIR/cpN/repo`, a full
`git clone` of this repository): a scratch script recomputes `sha256` and `size` of every
`artifacts` record whose file differs from its record, measures and rewrites
`manager.conformance.suites` (the same discovery `release.py manager-block --release-dir
<scratch> --write` uses), commits it in the clone, and the nine suites run from the clone's
`stage-conformance` fixture, with `TMPDIR` and `HOME` set to scratch directories, followed by
the `tools/release` tests (zlib-ng Python) and the `tools/docs` tests. The count assertion in
`release_test.py` is preserved, not edited: the scratch manifest carries the measured counts,
which is what CP3 does for the committed one. No rationale is touched in the scratch.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
|---|---|---|
| OD-1 | The version: patch 2.18.2 (`fix:`) or minor | **Patch, `fix:`.** An existing refusal moves earlier with the same code and text; the rest is a re-wrap, hardening and documents. No capability, state, protocol or document contract is added. |
| OD-2 | 60e: dry call of `generate_artifacts_declarations` in step 1, a new script command, or a hand-built template | **The dry call.** It is the same predicate on the same template as step 3, adds no surface, and writes nothing. |
| OD-3 | 64c scope: which lines | **Every prose line over 90 columns in the six files, except the YAML front matter, code fences, tables, headings and a line whose only content past its indentation is one span with no space inside it (`approve-review.md` line 322).** The front matter `description:` is a parsed single-line value; folding it is a format change. The remaining exempt lines are listed in CP1's report. |
| OD-4 | Where the command forms live, and whether `/prepare-functional-review` points to them | **`docs/RELEASING.md`, pointed to from `CLAUDE.md`; no change to the shipped command.** The command is generic to every repository, and these forms are this repository's. |
| OD-5 | `on_failure`: narrow the wording or suppress `BaseException` | **Narrow the wording.** No behaviour change, and an interrupt during an undo is not hidden. |
| OD-6 | The 2.18.1 history row: leave and note in 2.18.2, or correct | **Correct the 2.18.1 sentence (add 60e) and say in the 2.18.2 row that this release fixes 60e and 64c.** The omission is a factual error in a document, not a published artifact (the row is not part of any release package). |
| OD-7 | The manager CI pin | **No change.** `manager-pin.json` (1.13.0) equals `min_manager_version` (1.13.0), as the owner decided on #39. |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does
not exist in this repository's release source).

## 5. Checkpoints

Three checkpoints. CP1 and CP2 are independent; CP3 is the release. CP1 and CP2 verify as
D-Staging says.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Command files: the early collision check and the guard re-wrap | - | 3 | 1 |
| CP2 | Verification commands and the Optional findings | - | 3 | 1 |
| CP3 | Release 2.18.2 | CP1, CP2 | 3 | 1 |

<!-- CP1 -->
### CP1 — Command files: the early collision check and the guard re-wrap

**Files:** `payload/.claude/commands/milestone-plan.md`,
`payload/.claude/commands/accept-milestone.md`,
`payload/.claude/commands/approve-review.md`,
`payload/.claude/commands/adopt-gate-policy.md`,
`payload/.claude/commands/request-plan-amendment.md`,
`payload/.claude/commands/resume-implementation.md`,
`payload/.claude/commands/retire-legacy-work-item.md`,
`payload/scripts/workflow_integration_test.py`, `payload/scripts/workflow_state_test.py`.

- **60e** (D-60e). Red first, in `workflow_integration_test.py` beside the backlog
  command-text tests: a test that `milestone-plan.md` carries the "Declared-backlog
  collision check", that it names `generate_artifacts_declarations` with `repo_root`, the
  refusal codes and "nothing written", and that it precedes the `route_work_item` call
  sentence (index order). In `workflow_state_test.py`, in
  `GeneratedDeclarationsBacklogClassificationTest`'s neighbourhood, a test that runs the
  documented sequence in a scratch repository with a colliding declaration (fresh id, both
  work item types): the dry call raises `declaration_conflict`, and afterwards the state file,
  the registry, the mapping and the artifacts file are all unchanged (absent), where
  running `route_work_item` first would have created the entry; and that for an undeclared
  repository the dry call equals the plain template. **Done:** the needle test fails against
  the unedited command file; the behavioural test passes (it pins the contract the text
  relies on); the undeclared steps-1-to-5 digest constant did NOT change.
- **64c** (D-64c). Re-wrap the six files with the scratch script; a test in
  `workflow_integration_test.py` that no non-exempt line of the six exceeds 90 columns, the exemptions being those of
  OD-3 including the unbreakable single-span line (red first: it fails on the base files). **Done:** per file,
  `' '.join(old.split()) == ' '.join(new.split())` against `git show a0ec8cf:<file>` (the
  report prints the six results), the guard pin tests stay green unmodified, the exempt
  lines left are listed, and `git diff --stat` shows only the six files and `milestone-plan.md`
  under the commands directory.
- **Golden hashes.** `_GOLDEN_COMMAND_FILE_SHA256` is re-recorded for the seven changed
  files, from the files, once, after the last edit; the `milestone-plan.md` entry and any
  needle that quotes it move together.

**Verification:** D-Staging in a disposable clone: the nine suites, the `tools/release` and
`tools/docs` tests; the byte-identity of every other command file against `a0ec8cf`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Verification commands and the Optional findings

**Files:** `docs/RELEASING.md`, `CLAUDE.md`, `payload/scripts/workflow_state.py`,
`payload/scripts/workflow_state_test.py`, `tools/release/release.py`,
`tools/release/manager_block.py`, `tools/release/package.py`,
`tools/release/release_test.py`.

- **The section** (D-Commands-Doc): `## Verification commands` in `docs/RELEASING.md`, and one
  line under `CLAUDE.md`'s "Releases" list pointing to it, outside the managed block.
  **Every command form in it is run** as written in a scratch environment and the report
  states the exit code and the first output line of each (the stage-conformance form with a
  suite from its fixture; the unittest forms; `check-manager-block`; `workflow-manager verify
  .` online and, with an empty `--release-cache` and an offline `--release-source`, its
  failure as the section describes it). A `release_test.py` test pins the forms as needles.
- **`on_failure` wording** (D-Optional): `workflow_state.py`'s docstring corrected; the needle
  and `KeyboardInterrupt` tests in `workflow_state_test.py`.
- **Trailing newline** (D-Optional): `\Z` in `TAG_RE`, `_MANAGER_VERSION_RE` and
  `_SHA256_RE`; `release_test.py` rejection tests: a tag `"v2.18.2\n"` through the release
  list check that uses `TAG_RE` and a record whose `sha256` has a trailing newline through
  the package manifest check, each red against the unfixed code; the manager-version pin
  test states it is not red first.
- The 2.18.1 and 2.18.2 history rows are CP3's.

**Verification:** D-Staging in a disposable clone; `python3 tools/docs/check_docs.py` clean
(`docs/RELEASING.md` is outside its pages, so the section adds no link or id risk).
<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Release 2.18.2

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/RELEASING.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.18.2 with its two pinned assertions in
  `workflow_protocol_test.py` and the matching `ORCHESTRATION_PROTOCOL.md` edits; the
  protocol version stays.
- `manifest.json` 2.18.2: `workflow_version`; `sha256` and `size` of every record changed
  (the seven command files, the scripts and tests, `ORCHESTRATION_PROTOCOL.md`); `counts`
  unchanged; a `review-followups-2 (workflow-2.18.2)` sentence on **each** changed record,
  true of that file and read against `git diff a0ec8cf..HEAD -- <file>`; the `manager`
  block: `min_manager_version` 1.13.0, `downgrade_boundary.posture` per D-Patch, `signals`,
  `new_work_only` and `gate_default_change` empty, `conformance.suites` measured by
  `release.py manager-block --release-dir <scratch> --write` from a staging of CP3's own
  content, never typed.
- **Golden hashes** for the changed command files are already re-recorded in CP1 and are
  checked here against the committed files.
- `docs/release-history.md`: the 2.18.2 row and the corrected 2.18.1 sentence (OD-6) and the
  "Last checked with" line; `docs/RELEASING.md`: the acceptance-matrix test count it states
  follows the measured count (two places), no other count.
- `tools/release/release_test.py`: a 2.18.2 release class (version, release constant, the
  posture needles, the history row, counts); the 2.18.1 class keeps what stays true of that
  release and no longer pins the current version, constant or posture.
- `docs/ROADMAP.md` row 19 is added with this plan, with the status `Next`, and becomes Done at acceptance, not in
  this checkpoint.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit
HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` is clean;
`tools/docs` is clean; `workflow-manager verify .` is clean; the tools tests pass in the
zlib-ng environment; the new section's forms are re-run once more from the committed tree.
<!-- /CP3 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
|---|---|---|---|
| 60e | Declared-backlog collision refused at `/milestone-plan` step 1 | CP1 | D-60e |
| 64c | Re-wrap the six user-only guard bodies | CP1 | D-64c; front matter exempt (OD-3) |
| #68 commands | Verification commands section | CP2 | `docs/RELEASING.md` (OD-4) |
| #68 O1 | `on_failure` docstring | CP2 | narrowed (OD-5) |
| #68 O2 | `\Z` in three patterns | CP2 | two real, one latent (section 2) |
| #68 O3 | History row omits 60e | CP3 | OD-6 |
| 39j | CI pin against `min_manager_version` | - | decided by the owner (OD-7); not in this plan |

The artifact declaration `docs/ai-workflow/registry/review-followups-2-artifacts.json` is
generated by `workflow_state.generate_artifacts_declarations`; the plan, the registry and the
mapping are its plan-stage protected paths, and self-review checked that every path named in
a Files paragraph is classified at both stages.
