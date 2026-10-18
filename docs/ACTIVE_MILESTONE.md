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
on GitHub runners against width 2 and width 4 without sharding, records the numbers in
`docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md`, and ships exactly what the numbers
support (O1 sharded, O2 a lower width, O3 no change and no release).

1. **CP1** the sharded scheduler as a candidate in the managed template, its tests and
   the measurement kit.
2. **CP2** measure, record the evidence and apply the decision to the template.
3. **CP3** the same scheduling in this repository's release-source conformance, and the
   user document.
4. **CP4** release 2.16.0: manifest, release history, downgrade posture.

## Current checkpoint

CP1 is complete: `templates/.github/workflows/workflow-conformance.yml` now carries the
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

## Next action

CP2: the orchestrator runs the measurement from the kit's README on a throwaway branch
and the CP2 worker records the evidence and applies the decision. CP1 changes no payload
byte and no manifest byte; `manifest.json` stays at 2.15.0 until CP4.
