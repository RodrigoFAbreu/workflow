# Active Milestone

## Milestone

**In progress.** W12: `conformance-sharding` (`process`, governing version `2.2`), branch
`milestone/conformance-sharding`, base `971ea16` (main after #54: the release source is
Workflow 2.15.0 and this repository's own installation is the published 2.15.0).
Roadmap row 15. The plan is `docs/ai-workflow/CONFORMANCE_SHARDING_PLAN.md`, approved by
gate policy at plan revision 4. The previous milestone, W11 (`review-round-counts`,
Workflow 2.15.0), is complete.

## Goal

Workflow 2.16.0 (a template change, `feat:`), decided by a measurement: the managed
`workflow-conformance` job is the long pole of every managed repository's pull request
(14-20 minutes here), and the acceptance-matrix suite (415 tests) is the long pole inside
it. The milestone builds the owner's requested scheduling as a candidate (whole test
classes in shards, run as processes of the one job under one global width), measures it
on GitHub runners (sharded at widths 3 and 4 against unsharded, compared only on the same CPU type), records the numbers in
`docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md`, and ships exactly what the numbers
support (O1 sharded, O3 no change and no release).

1. **CP1** the sharded scheduler as a candidate in the managed template, its tests and
   the measurement kit.
2. **CP2** measure, record the evidence and apply the decision to the template.
3. **CP3** the same scheduling in this repository's release-source conformance, and the
   user document.
4. **CP4** release 2.16.0: manifest, release history, downgrade posture.

## Current checkpoint

CP3 is complete: `release-source-conformance` in `.github/workflows/workflow-ci.yml` now runs the
template's scheduling over the staged fixture (`$RUNNER_TEMP/fixture`), never the installed
`scripts/`: `width_cap=4`, `shards=4`, the acceptance suite in four shards of whole test classes
and the eight other suites in one queue under one limit, the coverage gate, and no fall-back to
the unsharded suite. The Python heredoc is byte-identical to the template's (D-Same-Text); the
step differs only in the fixture paths, the `source-conformance` base and the log collection that
copies every unit's log, result and shard file, the plan and the check output into the unchanged
`source-conformance-logs` upload. `release.py stage-conformance --commit HEAD`, the 60-minute
timeout, the triggers, permissions, concurrency, job names and `aggregate` are untouched.
`docs/RELEASING.md` describes the sharded step, the diagnostics and where a shard failure shows.

Tests (`tools/release/release_test.py`, `SourceConformanceRunner`, 9 to 18 tests): the embedded
shard tool equals the template's byte for byte; the step equals the template's step after the
path substitutions and the two log-collection blocks (nothing else differs); constants and
suites line equal the template's; the job keeps its stage, timeout, upload and `aggregate`; the
nine-suite unsharded path (`shards=0`) keeps its earlier tests; the sharded path: nine rows plus
the coverage line and the uploaded shard files, each of the nine suites failing in turn, a
failing shard's log and result kept, a failed plan fails the job with no fall-back, and shards
and suites share one limit.

Verified: `tools/release/release_test.py` 187 tests, 186 pass; the one error is the same
`ReproductionTest.test_round_trip` digest mismatch CP2 recorded (it ends when CP4 updates the
manifest digests). `tools/docs` tests (34) and checker pass; `workflow-manager verify .` is
clean. A local run of the CI step body against a staged scratch fixture (nine payload suites
included, `package.stage` of `HEAD` with the scratch manifest's digests rewritten, outside the
repository) passed: `coverage: expected 415, recorded 415`, shards 3/4/1/2 finished in 74 to 114
s, all nine suites passed, and the upload directory held every unit's files, `plan.json`,
`check.out` and `check.err`.

CP2 (earlier):

CP2 is complete: the measurement (revision 5, four rounds, 45 jobs, all valid, every sharded job
covering 415 of 415 test ids) selected **O1**, `width_cap` 4 and `shards` 4 (variant v3: median
979 s against 1203 s unsharded on the EPYC 7763, 606 s against 833.5 s on the EPYC 9V45; worst
same-CPU ratio 0.8074). It is recorded, with the validator's output and the records, in
`docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md`. The template already carries those
constants, so its bytes are unchanged; `tools/release/release_test.py` gains a pin that the
shipped constants and the evidence's selected outcome agree.

Verified: `tools/release/release_test.py` 178 tests, 177 pass; the one error,
`ReproductionTest.test_round_trip`, stages `HEAD` and builds it, and the build refuses the
CP1 template because `manifest.json` still carries 2.15.0's digest (`digest mismatch:
templates/.github/workflows/workflow-conformance.yml`). It follows from the CP1 commit, not
from CP2 (which changes no template, payload or manifest byte), and ends when CP4 updates the
manifest digests. In the staged release fixture the committed template's step passes every
gate: `coverage: expected 415, recorded 415`, the four shards' skips 7 + 9 + 0 + 4 = 20 (the
serial run's `skipped=20`), and the eight other suites pass; `workflow-manager verify .` is
clean and `tools/docs` tests and checker pass.

CP1 (earlier):

`templates/.github/workflows/workflow-conformance.yml` now carries the
candidate scheduling. `width_cap=4` and `shards=4` are each alone on one line;
`shards=0` runs the acceptance suite as one unit as 2.15.0 does. A quoted heredoc writes
`$base/shards.py` (stdlib only) with `plan` (groups the tests of
`workflow_acceptance_matrix_test.py` by class, refuses a module that defines
`load_tests`, `setUpModule` or `tearDownModule`, partitions longest-processing-time on
test count into at most `N` shards, and writes the expected ids), `run` (loads exactly one
shard's classes with `loadTestsFromTestCase`, checks the loaded ids equal the plan,
records every test id's outcome, a failed subtest under its parent, and exits 1 unless
everything succeeded) and `check` (per shard: the process exit, a complete shard file
that names its shard and classes, no failed, missing, unexpected or never-finished id;
and the multiset of recorded ids equal to the expected ids). The shell scheduler queues
the shards first and the eight other suites after them, starts at most
`min(width_cap, nproc)` units at a time, prints `start <unit> running K` from the parent
for the V3 validity check, and keeps the summary's nine suite rows (the acceptance row
reads `passed (N shards, T tests)` and the shard rows follow it). A failed plan fails the
job; there is no fall-back to the unsharded suite. The concurrency block is unchanged.

Tests (`tools/release/release_test.py`, `ConformanceTemplate`, 8 to 24 tests): the
constants and the kit's substitution; the shard tool run from the extracted heredoc
against a stand-in module (inheritance, a class-decorator skip, a `skipTest`, passing and
skipped and failing subtests, an expected failure, an empty class): a complete run
records every outcome; the partition is exact, deterministic and balanced, and exact on
the real acceptance module for 1, 2, 4 and 8 shards (compared with the module's own
count and the manifest's `manager.conformance.suites`); `plan` refuses each module hook;
`check` fails naming the shard and the original ids for a failed test, a failed subtest,
a `setUpClass` error, a `setUpClass` `SkipTest`, an unexpected success, and for a missing,
truncated, incomplete, wrong-class, duplicated, extra, missing-id, never-finished,
nonzero-exit and no-result shard; the step body with stand-in suites: all pass, each of
the nine in turn failing, a failing shard, every unit whose copy failed, the width never
exceeded with shards and suites queued together, isolation of `TMPDIR`, `HOME` and the
repository copy per shard, a failed plan failing the job, and `shards=0` reproducing the
nine-unit behaviour.

Verified: `tools/release/release_test.py` 177 tests pass (Python 3.12 and 3.14 for the
template tests). A local run of the sharded step (v3) on the staged release tree passes
every gate: `coverage: expected 415, recorded 415`, the same 20 skipped ids with the same
reasons as the serial run (415 tests, `OK (skipped=20)`); the acceptance row took 108 s
in the four-shard run against 354 s serial on this machine (both while other runs shared the CPUs). The nine payload suites pass
in the staged release fixture (the same local run; CP1 changes no payload byte). The measurement kit (not committed; generator,
collector, validator and the 23 self-checks) is prepared outside the repository for the
orchestrator.

### CP4 -- Release 2.16.0 (complete)

Release identity: `WORKFLOW_RELEASE` is `"2.16.0"` in `payload/scripts/workflow_protocol.py`,
the two pinning assertions in `workflow_protocol_test.py` follow, and
`ORCHESTRATION_PROTOCOL.md` changes in its three places (tested-releases list, the unpinned
`workflow_release` example, the protocol `1.5` history entry); the protocol version stays `1.5`.
`manifest.json` is 2.16.0 with the digests of the template and the three changed payload files
refreshed, the template derivation extended with W12, and the `manager` block rewritten
(`min_manager_version` 1.13.0, a template-plus-constant posture whose way back is
`workflow-manager update` to 2.15.0, no signals, no new-work-only note, no gate default
change). `release.py manager-block --release-dir <scratch stage> --write` measured the nine
suite counts and they are unchanged from 2.15.0 (415, 341, 1183, 315, 142, 106, 317, 280, 27).
`docs/release-history.md` has the 2.16.0 row with the measured numbers (medians 1212.5 s to
979 s on the EPYC 7763 type, 833.5 s to 606 s on the EPYC 9V45 type); `docs/common-problems.md`
explains a failing or missing shard. `docs/ROADMAP.md` is untouched (Current/Done is at
acceptance).

## Functional review checklist

Implementation revision 4. Verified before this checklist: `tools/release/release_test.py`
192 tests pass (Python 3.12 with the pinned `zlib-ng` runtime; on Python 3.14 without it 29
reproduction tests error, an environment limit, not a defect), `tools/docs` tests (34) pass,
`workflow-manager verify .` is clean.

**Setup.** On branch `milestone/conformance-sharding`, clean tree. Use Python 3.12 with the
pinned runtime: `python3.12 -m venv /tmp/wf-venv && /tmp/wf-venv/bin/pip install
--require-hashes -r tools/release/deflate-requirements.txt`. No feature flags.

**Test data.** None to seed; the real acceptance module
(`payload/scripts/workflow_acceptance_matrix_test.py`, 415 tests) and the staged release
fixture are the data.

**Flows and expected results.**

1. Release tool tests: `/tmp/wf-venv/bin/python tools/release/release_test.py` -> `Ran 192
   tests ... OK`.
2. Template constants: open `templates/.github/workflows/workflow-conformance.yml` -> `width_cap=4`
   and `shards=4` each alone on a line; `shards=0` is documented as the unsharded path.
3. Shard plan: extract the heredoc `shards.py` and run `plan` on the acceptance module with 4
   shards -> four shards of whole classes, ids summing to 415, deterministic across reruns.
4. Sharded step on a staged fixture (as CI runs it): the summary shows nine suite rows (the
   acceptance row `passed (4 shards, 415 tests)`), `coverage: expected 415, recorded 415`, all
   suites pass, and a failing test makes the job fail with the shard named (no fall-back to
   the unsharded suite).
5. Release-source job: in `.github/workflows/workflow-ci.yml`, `release-source-conformance`
   runs the same scheduling over the staged fixture, with the same Python heredoc as the
   template, the 60-minute timeout and `aggregate` unchanged.
6. Release identity: `manifest.json` is 2.16.0 with refreshed digests, `WORKFLOW_RELEASE`
   is `"2.16.0"`, `docs/release-history.md` has the 2.16.0 row (medians 1212.5 s to 979 s and
   833.5 s to 606 s), `docs/common-problems.md` explains a failing or missing shard.
7. Evidence: `docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md` selects O1, 45 jobs all
   valid, worst same-CPU ratio 0.8074.
8. Installation: `workflow-manager verify .` -> clean, 2.15.0 (this repository's own
   installation is untouched by the milestone).

**Known limitations / out of scope.** The wall-clock gain is measured on GitHub runners, not
reproducible locally (a local sharded run only shows the shard mechanics). The Python 3.14
environment cannot install the pinned `zlib-ng` wheel, so reproduction tests need Python 3.12.
Publishing 2.16.0, the `workflow-manager` pin and `docs/ROADMAP.md` are outside this
milestone (acceptance and release steps).

## Next action

All checkpoints are complete. Next: manual functional review against the checklist above;
findings go to the item's `FUNCTIONAL_REVIEW.md`, otherwise `/accept-milestone`.
