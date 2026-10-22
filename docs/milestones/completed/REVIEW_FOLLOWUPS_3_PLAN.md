# W17: Workflow 2.18.3 — review follow-up clean-up 3 (Revision 2)

- **Work item:** `review-followups-3` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator; the owner said go on 2026-10-21. It is row 20
  of `docs/ROADMAP.md` (status `Current` from this plan, `Done` at acceptance).
- **Issue:** RodrigoFAbreu/workflow#71.
- **Branch:** `milestone/review-followups-3`
- **Base commit:** `6b63dcc` (main after #74: the release source is Workflow 2.18.2; this
  repository's own installation is also 2.18.2, automatic gates, default `2.2`, no
  `GATE_POLICY.json`, no backlog file declared, so the prose roadmap applies)
- **Plan revision:** 2. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 1. Goal

Ship Workflow 2.18.3, a patch release (`fix:`), that clears the two items W16 left open in #71:

1. **The `state_transaction` docstring.** Its opening clause says "The original exception
   propagates;" without the exception the same sentence then states (a `KeyboardInterrupt` or
   `SystemExit` from `on_failure` replaces the original). The clause must carry its own
   exception, and the test must pin the complete corrected wording.
2. **The suites loop in `docs/RELEASING.md`.** `for suite in $suites` splits the nine names
   only under bash; pasted into zsh it runs once with the names joined and fails. The block
   must work under both shells.

Why `fix:` and not `feat:` (OD-1): nothing here adds a capability. One is a docstring (no
behaviour), the other a maintainer document that is not part of the installed release. A patch
keeps the version change in step with the pull-request title.

### Hard limits (invariants)

- **No state field, ledger, phase, trailer, commit shape or protocol change.** Refusal codes are
  unchanged. No command-file change. No Controller or Manager change: `min_manager_version`
  stays 1.13.0, and the CI pin in `tools/release/manager-pin.json` must EQUAL it (owner
  decision 2026-10-20 on #39); it does today and no checkpoint changes either.
- **This repository's own installation stays untouched:** `.claude/`, `scripts/`,
  `docs/ai-workflow/` managed documents, `.workflow-manager/`, the managed blocks of
  `CLAUDE.md` and `.gitignore`, and `.github/workflows/workflow-conformance.yml`. Fixes go to
  `payload/`, `tools/`, `docs/` user documents and `manifest.json`.
- **Size:** two checkpoints including the release one.

### What is a gate and what is an aid

- **Gates (a failure stops work):** each new test, shown to fail against the unfixed text first
  (the "red first" rule); the nine payload suites from a staged fixture; the `tools/release`
  tests (in the zlib-ng environment); the `tools/docs` tests and checker; every block of the
  "Verification commands" section run in sequence under **both** bash and zsh, each exiting 0
  with the working directory at the repository root; `check-manager-block`; `workflow-manager
  verify .` clean.
- **Aids (never a stop):** the per-record hunk reading of the manifest rationales against
  `git diff` (CP2).

## 2. Facts this plan relies on (re-checked against `6b63dcc`)

- **The docstring today** (`payload/scripts/workflow_state.py`, `state_transaction`): "...
  before the exception propagates -- the undo of a side effect ... between the failure and the
  undo. The original exception propagates; an `Exception` raised by `on_failure` is
  suppressed, but a `BaseException` that is not an `Exception` (`KeyboardInterrupt`,
  `SystemExit`) is not -- it propagates and replaces the original, so an operator interrupt
  during an undo is never hidden. Never called on success." The code suppresses
  `contextlib.suppress(Exception)`, so the sentence is right in substance and wrong in its
  first clause. The existing test
  (`test_the_docstring_says_an_exception_not_a_base_exception_is_suppressed`) pins only the
  phrase "an `Exception` raised by `on_failure` is suppressed", so an unqualified opening
  clause would pass it.
- **The suites block today** (`docs/RELEASING.md`, "Verification commands"):
  `suites=$(python3 -c "...print(*...)")` then
  `( cd "$TMPDIR/fixture/scripts" && for suite in $suites; do ...; done )`. zsh does not split
  an unquoted parameter expansion on whitespace, so the loop body runs once with one word. The
  section's test (`VerificationCommandsSectionTest` in `tools/release/release_test.py`) pins
  the `for suite in $suites` form as a needle, so that pin changes with the block (it is
  strengthened, not weakened: the new needle is the shell-neutral loop and a second needle
  forbids the old one).
- **Two pins to update, none to weaken.** `payload/scripts/workflow_state_test.py` keeps
  its `KeyboardInterrupt` test and the suppression test, and gains the complete-wording pin.
  `release_test.py` keeps every other needle of the section.

## 3. Design decisions

### D-Patch: the version is 2.18.3, `fix:`

`manifest.json` `workflow_version` 2.18.3; `WORKFLOW_RELEASE` and its two pinned assertions in
`workflow_protocol_test.py` follow, with the matching `ORCHESTRATION_PROTOCOL.md` edits
(tested-releases list, envelope example, protocol-1.5 note); the protocol version stays.

**Downgrade posture.** An older release reads every state, ledger and file 2.18.3 writes:
nothing it reads changes. `workflow-manager update` back to 2.18.2 restores the docstring
(no behaviour) and the release constant `WORKFLOW_RELEASE` 2.18.2, which the protocol envelope
reports as `workflow_release` (LPR-003). The release tooling (`tools/`) and `docs/` are not part of the installed
release. CP2 writes this into the manifest `manager` block and the release history.

### D-Docstring: the exception is stated in the clause that needs it

The opening clause of the sentence becomes: "The original exception propagates unless
`on_failure` raises a `BaseException` that is not an `Exception` (`KeyboardInterrupt`,
`SystemExit`), which then replaces it, so an operator interrupt during an undo is never hidden;
an `Exception` raised by `on_failure` is suppressed." The consequence ("so an operator interrupt
... is never hidden") stays on the clause that causes it, the non-`Exception` `BaseException`
replacing the original, as today's text has it (LPR-001); the redundant "but ... is not -- it
propagates and replaces the original" tail is folded into the first clause, so the sentence says
each thing once and agrees with `contextlib.suppress(Exception)`. In the docstring, "an
`Exception` raised by `on_failure` is suppressed" stays on ONE physical line, because the
existing phrase pin reads the raw docstring (LPR-004). No behaviour changes (OD-2:
narrow wording, not suppression of `BaseException`, which would hide an interrupt behind the
original error).

**The pin** is on the COMPLETE sentence, whitespace-normalised
(`" ".join(doc.split())`): the test asserts that the normalised docstring contains the whole
corrected sentence above, and that the old unqualified opening ("The original exception
propagates; an `Exception`") is absent. The absence check runs on the whitespace-normalised
text too: in today's docstring that text spans a line break, so a raw-text `assertNotIn` would
pass even against the unfixed docstring and would not be red first (LPR-004). A later edit that reintroduces an unqualified clause, or
drops the exception from the clause, fails. The existing phrase pin and the `KeyboardInterrupt`
behaviour test stay as they are.

### D-Shell: one name per line and `while read -r`, which both shells split

The block becomes (the stage command is unchanged):

```bash
suites=$(python3 -c "import json; print(*json.load(open('manifest.json'))['manager']['conformance']['suites'], sep='\n')") && test -n "$suites" && ( cd "$TMPDIR/fixture/scripts" && while read -r suite; do python3 -B "$TMPDIR/fixture/scripts/$suite" </dev/null || exit 1; done <<< "$suites" )
```

Why this form (OD-3): `while read -r` over a here-string reads one line per iteration in bash
and zsh alike, whereas an unquoted `$suites` is split by bash only; `</dev/null` keeps a suite
from consuming the remaining names from the here-string; the `test -n` guard turns an empty list
(the manifest read failing) into a failure instead of a loop that runs zero times and "passes".
Saying "bash" above the block would leave zsh, this repository's maintainers' shell, with a block
that must be rewritten by hand. The prose below the block says the block runs under bash and zsh.

**Proof by running.** CP1 runs the section's blocks in sequence, once under `bash` and once under
`zsh`, in a scratch clone: stage, suites, `tools/release` tests (zlib-ng Python first on `PATH`),
`tools/docs` tests, `check_docs.py`, `check-manager-block`, and `workflow-manager verify .`
where the cache allows. Each exits 0, and `pwd` is the repository root after each block.

### D-Staging: scratch staging for CP1 (the procedure W16 used)

`release.py stage-conformance` and `tools/release/release_test.py` verify the manifest against
the tree, and CP1 changes shipped files (`workflow_state.py` and its test) whose digests the
committed manifest records only at CP2. So CP1 verifies in a **disposable clone**
(`$TMPDIR/cp1/repo`, a full `git clone` of this repository): a scratch script recomputes
`sha256` and `size` of every `artifacts` record whose file differs from its record, measures and
rewrites `manager.conformance.suites` (the same discovery `release.py manager-block
--release-dir <scratch> --write` uses), commits it in the clone, and the section's blocks run
from there with `TMPDIR` and `HOME` set to scratch directories. The count assertion in
`release_test.py` is preserved, not edited: the scratch manifest carries the measured counts,
which is what CP2 does for the committed one. No rationale is touched in the scratch.

## 4. Open decisions (for the plan reviewer and the owner)

| Id | Decision | Recommendation |
|---|---|---|
| OD-1 | The version: patch 2.18.3 (`fix:`) or minor | **Patch, `fix:`.** A docstring and a maintainer document; no capability, state, protocol or document contract is added. |
| OD-2 | Docstring: narrow the wording or suppress `BaseException` | **Narrow the wording** (as W16's OD-5 decided): no behaviour change, and an interrupt during an undo is not hidden. |
| OD-3 | Suites loop: say "bash" above the block, or a shell-neutral loop | **The shell-neutral loop** (`while read -r` over one name per line), with the empty-list guard and `</dev/null`. |
| OD-4 | The manager CI pin | **No change.** `manager-pin.json` (1.13.0) equals `min_manager_version` (1.13.0), as the owner decided on #39. |

None of these finalizes an "Open decision" row of `docs/TECHNICAL_DECISIONS.md` (the file does
not exist in this repository's release source).

## 5. Checkpoints

Two checkpoints. CP1 verifies as D-Staging says; CP2 is the release.

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The docstring clause and the shell-neutral suites loop | - | 2 | 1 |
| CP2 | Release 2.18.3 | CP1 | 3 | 1 |

<!-- CP1 -->
### CP1 — The docstring clause and the shell-neutral suites loop

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_state_test.py`,
`docs/RELEASING.md`, `tools/release/release_test.py`.

- **Docstring** (D-Docstring). Red first: the complete-wording test in `workflow_state_test.py`
  fails against the unedited docstring, then passes after the edit; the existing phrase pin and
  `KeyboardInterrupt` test stay green unmodified. **Done:** the failure is recorded; the
  docstring reads as D-Docstring says; `git diff` of `workflow_state.py` is the docstring
  only.
- **Suites loop** (D-Shell). Red first: the `release_test.py` needles for the new loop and the
  absence of `for suite in $suites` fail against the unedited block. The prose under the block
  says it runs under bash and zsh. **Done:** the section's blocks run in sequence under bash and
  under zsh in the scratch clone, each exiting 0 with the repository root as working directory
  after each block (the report prints both runs' exit codes and `pwd`); the old block is shown
  to fail under zsh, for the record.

**Verification:** D-Staging in a disposable clone: the nine suites, the `tools/release` and
`tools/docs` tests, `check_docs.py`, `check-manager-block`.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.18.3

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`,
`payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
`docs/RELEASING.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.18.3 with its two pinned assertions in
  `workflow_protocol_test.py` and the matching `ORCHESTRATION_PROTOCOL.md` edits; the protocol
  version stays.
- `manifest.json` 2.18.3: `workflow_version`; `sha256` and `size` of every record changed
  (`workflow_state.py` and its test, `workflow_protocol.py` and its test,
  `ORCHESTRATION_PROTOCOL.md`); `counts` unchanged; a `review-followups-3 (workflow-2.18.3)`
  sentence on **each** changed record, true of THAT file and read against `git diff
  6b63dcc..HEAD -- <file>` (the protocol and release-constant records say the release constant
  and nothing about the docstring); the `manager` block: `min_manager_version` 1.13.0 (equal to
  the CI pin), `downgrade_boundary.posture` per D-Patch, `signals`, `new_work_only` and
  `gate_default_change` empty, `conformance.suites` (digests, sizes and test counts) measured by
  `release.py manager-block --release-dir <scratch> --write` from a staging of CP2's own
  content, never typed.
- `docs/release-history.md`: the 2.18.3 row (it closes #71) and the "Last checked with" line;
  `docs/RELEASING.md`: any test count it states follows the measured count, no other change.
- `tools/release/release_test.py`: a 2.18.3 release class (version, release constant, the
  posture needles, the history row, counts); the 2.18.2 class keeps what stays true of that
  release and no longer pins the current version, constant or posture.
- `docs/ROADMAP.md` is not written by this checkpoint (LPR-002): row 20 is `Current` from this
  plan and becomes Done at acceptance.

**Verification:** the nine suites pass in a stock `release.py stage-conformance --commit HEAD`
fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` is clean; `tools/docs`
is clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment;
the section's blocks are re-run once more from the committed tree under bash and zsh.
<!-- /CP2 -->

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
|---|---|---|---|
| #71 docstring | Opening clause carries its exception; complete wording pinned | CP1 | D-Docstring |
| #71 suites loop | Shell-neutral loop, run under bash and zsh | CP1 | D-Shell |
| Release | 2.18.3 bookkeeping, closes #71 | CP2 | D-Patch |

The artifact declaration `docs/ai-workflow/registry/review-followups-3-artifacts.json` is
generated by `workflow_state.generate_artifacts_declarations`; the plan, the registry and the
mapping are its plan-stage protected paths, and self-review checked that every path named in a
Files paragraph is classified at both stages.
