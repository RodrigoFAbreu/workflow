# Active Milestone

## Milestone

**Awaiting functional review.** W24: `interleaving-pins` (`process`, governing version `2.2`), branch
`milestone/interleaving-pins`, roadmap row 26a (RodrigoFAbreu/workflow#97 items 4 and 5 and the two pins of
#100). Plan: `docs/ai-workflow/INTERLEAVING_PINS_PLAN.md` (revision 2, approved by gate policy). The goal is
Workflow 2.19.1, a `fix:` patch that adds four pins to the shipped test suites and changes no behaviour. The
previous milestone, W23 `checkpoint-start-command`, is accepted (Workflow 2.19.0).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The four pins and their evidence | **complete** |
| CP2 | Release 2.19.1 | **complete** |

## Verified state

- CP1: seven new tests in `payload/scripts/workflow_state_test.py` (`test_p1_*`, four `test_p2_*`,
  `test_the_journal_refusal_names_no_release_command`, `test_p4_*`) and the worker mode `crash_at_unlink`; each is
  shown red against its own mutant (M1a to M7) and green unmutated, recorded with its exact substitutions in
  `docs/ai-workflow/INTERLEAVING_PINS_EVIDENCE.md`. `payload/scripts/workflow_state.py` is unchanged.
- Verified in a disposable clone (D-Staging): the nine suites, the whole `workflow_state_test.py` chunk and the new
  tests under the orphan wrapper (no orphan beyond Git), the `tools/release` and `tools/docs` tests, `check_docs.py`
  and `check-manager-block`; `workflow-manager verify .` is clean.
- CP2: Workflow 2.19.1 (`fix:`): `WORKFLOW_RELEASE`, its two pinned assertions and the Orchestration Protocol
  lists name 2.19.1 (protocol stays 1.5); `manifest.json` moves the four changed records (digest, size, an
  `interleaving-pins (workflow-2.19.1)` sentence), the posture and the measured `workflow_state_test.py` count
  (1232 to 1239); the release-history row (closes nothing), the invariants page and a 2.19.1 release class in
  `tools/release/release_test.py`. Counts stay (80, 6).

## Functional review checklist

Gate: `AWAITING_FUNCTIONAL_REVIEW`, a manual gate for the user. The milestone changes tests, version constants and
documents only, so no command, state key, phase, trailer or message of the Workflow changes. The flows check that
the four pins are real, that each fails against the mutant it names, and that the release bookkeeping agrees.

**Setup**

- Repository `/home/rodrigo/Workspace/workflow`, branch `milestone/interleaving-pins`, clean working tree, Python 3.14.
- `TMPDIR` is an empty scratch directory outside the clone. Every fixture and mutant copy goes there; never write
  inside the clone.
- No network, GitHub, `gh`, `claude`, `codex` or `ssh` is needed. F1 to F4 and F6 run offline. F3 needs the Manager
  checkout at `~/Workspace/workflow-manager`. F5 needs the zlib-ng environment (RELEASING.md, "Building locally").
  F7 needs the 2.19.0 release cache. A missing one is an environment gap, not a finding.
- Nothing is seeded. The fixture is staged from `HEAD`.

**Flows and expected results**

- **F1. The new tests pass in the staged fixture.** From the repository root:
  `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then from
  `"$TMPDIR/fixture/scripts"`: `python3 -B -m unittest -v workflow_state_test.TestReleaseCheckpointStart
  workflow_state_test.TestReleaseCheckpointStartCommand workflow_state_test.TestAmendmentResolutionReservation`.
  Expected: 38 tests, `OK`.
- **F2. Each mutant fails exactly the tests it names.** For the control and each of M1a, M1b, M1c, M2 to M7: copy
  `payload/` to a fresh `"$TMPDIR/mutant-<id>"`, apply the substitution(s) recorded under that heading in
  `docs/ai-workflow/INTERLEAVING_PINS_EVIDENCE.md` (each old text must occur exactly once in
  `scripts/workflow_state.py`), then run the command recorded there from the copy's `scripts/`. Expected: the control
  exits 0 with `OK`; each mutant exits 1 and fails only the named tests.
- **F3. No process is left behind.** From `"$TMPDIR/fixture/scripts"`, run the three classes of F1 under
  `python3 -I -S -B ~/Workspace/workflow-manager/tests/parallel/reaper.py --report "$TMPDIR/orphans-new.json"
  --chunk-id new-tests -- python3 -B -m unittest ...`, then `python3 -B workflow_state_test.py` under the same wrapper
  with `--report "$TMPDIR/orphans-chunk.json" --chunk-id state-chunk --`. Expected: 38 tests `OK`, then 1239 tests `OK`
  (1 skipped), chunk status 0 both times. Each report lists only `[git]` processes and
  `git maintenance run --auto --quiet --detach`.
- **F4. The nine payload suites pass.** Run the loop in RELEASING.md, "The nine payload suites", from the fixture
  staged in F1. Expected: each suite exits 0 with `OK`. Recorded counts: `workflow_acceptance_matrix_test.py` 453
  (20 skipped), `workflow_protocol_test.py` 344 (19 skipped), `workflow_gate_policy_test.py` 316,
  `workflow_fingerprint_generalization_test.py` 142, `workflow_state_completion_obligations_test.py` 193,
  `workflow_integration_test.py` 361, `workflow_fingerprint_test.py` 283, `workflow_test_harness_test.py` 27,
  `workflow_state_test.py` 1239 (1 skipped).
- **F5. The tools and the manager block agree.** With the zlib-ng Python, from the repository root:
  `python -m unittest discover -s tools/release -p '*_test.py'` (all `OK`). Then `python3 -m unittest discover -s
  tools/docs -p '*_test.py'` (34 `OK`), `python3 tools/docs/check_docs.py` (exit 0), and `python3
  tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`
  (`ok: 2.19.1 carries a valid manager block that matches the measurement`).
- **F6. The release bookkeeping agrees, and no production code changed.** `git diff e8aff0a -- payload/scripts/workflow_state.py`
  is empty. `manifest.json` `workflow_version` and `WORKFLOW_RELEASE` in `payload/scripts/workflow_protocol.py` both
  read 2.19.1. The 2.19.1 row of `docs/release-history.md` closes nothing, names the four pins, says no behaviour
  changes and gives the way back. `docs/CONCURRENCY_INVARIANTS.md` names the new pins and "Last checked with:
  Workflow 2.19.1".
- **F7. The installation still matches the recorded release (outside the sandbox).** `workflow-manager verify .` with
  the 2.19.0 release cache (`--release-cache` or `$WORKFLOW_MANAGER_RELEASE_CACHE`). Expected:
  `installation matches workflow 2.19.0`. Without the cache it exits 1 with `cannot fetch`, which is expected offline.

**Known limitations and out-of-scope behaviour**

- No behaviour changes. No production code, state key, phase, trailer, command or message changes.
- The release closes nothing: #97 items 4 and 5 and the two pins of #100 are partly done. Row 26b (the #100 wording and
  message fixes) is not done.
- The mutant runs of F2 happen in scratch copies. They are neither shipped nor committed.
- `TestGlobalLockOrderItem372h` does not independently fail M1a or M1b. The evidence file records this as information,
  not as a gate.
- `docs/ai-workflow/INTERLEAVING_PINS_EVIDENCE.md` (CP1, protected) still prints `ok: 2.19.0` for
  `check-manager-block`; at HEAD the line reads `2.19.1`, as F5 states.

**Findings:** place them in `.ai-review/interleaving-pins/feedback/FUNCTIONAL_REVIEW.md`. `/apply-functional-review`
routes each one: a same-scope fix takes its bounded branch, and a new or wider one takes an
`interleaving-pins-remediation-<n>` child.

## Next action

Manual functional review of the checklist above. When testing is clean, `/accept-milestone` is the only acceptance
command. It requires every checkpoint of this item to be `COMPLETE`; CP1 and CP2 are, so none is outstanding.
