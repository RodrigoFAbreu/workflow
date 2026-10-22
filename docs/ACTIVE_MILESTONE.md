# Active Milestone

## Milestone

**Awaiting functional review.** W17: `review-followups-3` (`process`, governing version `2.2`),
branch `milestone/review-followups-3`, roadmap row 20 (RodrigoFAbreu/workflow#71). Plan:
`docs/ai-workflow/REVIEW_FOLLOWUPS_3_PLAN.md` (revision 2, approved by gate policy). The goal is
Workflow 2.18.3, a patch release (`fix:`). The previous milestone, W16 `review-followups-2`, is
accepted (its record is in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The docstring clause and the shell-neutral suites loop | **complete** |
| CP2 | Release 2.18.3 | **complete** |

### CP1 verified state

- The `state_transaction` docstring (`payload/scripts/workflow_state.py`) now says "The original
  exception propagates unless `on_failure` raises a `BaseException` that is not an `Exception`
  (`KeyboardInterrupt`, `SystemExit`), which then replaces it, so an operator interrupt during an
  undo is never hidden; an `Exception` raised by `on_failure` is suppressed." No behaviour change.
  `workflow_state_test.py` pins the complete whitespace-normalised sentence and the absence of the
  old unqualified opening.
- The suites block in `docs/RELEASING.md` "Verification commands" is a `while read -r` loop over
  one name per line (here-string, `</dev/null`, `test -n` guard), so it runs under bash and zsh.
  `VerificationCommandsSectionTest` pins the new loop and forbids `for suite in $suites`.

### CP2 verified state

- Release 2.18.3: `manifest.json` `workflow_version`, digests, sizes, measured suite counts,
  rationales and downgrade posture; `WORKFLOW_RELEASE` and its pinned assertions;
  `ORCHESTRATION_PROTOCOL.md` mentions (the protocol stays 1.5); the release-history row; and
  `ReviewFollowups3ReleaseTest` in `tools/release/release_test.py`.

## Functional review checklist

This is a process milestone (Workflow 2.18.3, a patch release); there is no app to run. The
manual check is that the changed docstring, document and release bytes behave as the CP verified
states say. Everything runs offline: no flow needs `gh`, `claude`, `codex`, `ssh` or the network.
The product clone may be read-only, so every flow that writes works in a scratch clone and
scratch `TMPDIR`/`HOME`; the read-only flows (1, 2, 5) run in place.

### Setup

- Branch `milestone/review-followups-3`, clean tree. Make a scratch clone for the flows that
  write: `git clone <this repository> "$TMPDIR/repo" && cd "$TMPDIR/repo"` (a local clone, no
  network). Do not run the suites from inside this repository's installed tree (the integration
  suite reads the installed commands); run them from the staged fixture.
- `bash` and `zsh` both on `PATH`; Python 3. The `tools/release` tests need the zlib-ng Python
  (`docs/RELEASING.md`, "Building locally"); if it is not available offline, say so and skip
  flow 4's `tools/release` line rather than substituting the system Python.

### Test data

None to seed.

### Flows

1. **Docstring wording.** Read `state_transaction`'s docstring in
   `payload/scripts/workflow_state.py` (around line 1980). Expected: the opening clause reads "The
   original exception propagates unless `on_failure` raises a `BaseException` that is not an
   `Exception` (`KeyboardInterrupt`, `SystemExit`), which then replaces it ..."; the phrase "an
   `Exception` raised by `on_failure` is suppressed" is still on one physical line; the old
   "The original exception propagates; an `Exception`" opening is gone.
2. **Docstring agrees with the code.** Read the `on_failure` handling below the docstring.
   Expected: it suppresses with `contextlib.suppress(Exception)`, so an `Exception` from
   `on_failure` is swallowed and a `KeyboardInterrupt`/`SystemExit` is not; no behaviour change
   against the 2.18.2 code (`git diff 6b63dcc -- payload/scripts/workflow_state.py` touches only
   the docstring).
3. **Suites block under both shells.** In the scratch clone, copy the "nine payload suites" block
   from `docs/RELEASING.md` "Verification commands" and run it once under `bash` and once under
   `zsh` (`TMPDIR` set to a scratch directory; a fresh `$TMPDIR/fixture` each time). Expected:
   in each shell `stage-conformance` exits 0, all nine suites run one after another (nine
   `Ran ... OK` results), the block exits 0, and `pwd` is the clone root afterwards. The staging
   step verifies the tree against the manifest, so a failure here on the committed tree is a
   defect in the release bytes.
4. **Remaining blocks in sequence.** From the clone root, run the other blocks of the section in
   order: `python -m unittest discover -s tools/release -p '*_test.py'` (zlib-ng Python; 220+
   tests OK), `python3 -m unittest discover -s tools/docs -p '*_test.py'` (34 OK),
   `python3 tools/docs/check_docs.py` (exit 0), and `check-manager-block --commit HEAD
   --manager-releases tools/release/manager-releases.json` (exit 0; exit 2 without
   `--manager-releases`). Expected: each exits as stated, and the working directory is the
   repository root after each.
5. **Empty-list guard.** In the scratch clone, run the suites block with the manifest's suites list
   emptied (edit the scratch copy only). Expected: the block exits non-zero instead of passing
   with zero iterations.
6. **Release 2.18.3 bytes.** Expected: `manifest.json` names `2.18.3`; `WORKFLOW_RELEASE` in
   `payload/scripts/workflow_protocol.py` is `2.18.3`; `min_manager_version` is still `1.13.0`;
   `python3 tools/release/release.py build` (zlib-ng Python) succeeds in the scratch clone;
   published tags (`v2.3.1` to `v2.18.2`) and assets are untouched (`git tag -l` shows no moved
   tag; the diff since `6b63dcc` touches no release asset). `workflow-manager verify .` (needs
   the release cache; skip if the binary or cache is absent offline) still matches 2.18.2, since
   this repository's installation is untouched.

### Known limitations / out of scope

- This repository's own installation (`.claude/`, `scripts/`, `docs/ai-workflow/` managed files)
  stays at 2.18.2 until 2.18.3 is published and installed through `workflow-manager update`.
- Publishing the release, the `workflow-manager` pin and the pull request are not part of this
  gate and need a forge; they cannot run in the offline sandbox.
- No state field, ledger, phase, trailer, commit shape, protocol or command-file change was made;
  none should be looked for.

## Next action

Manual functional testing of the checklist above. Findings go to
`.ai-review/review-followups-3/feedback/FUNCTIONAL_REVIEW.md`; when testing is clean,
`/accept-milestone`.
