# Active Milestone

## Milestone

**Implementing.** W11: `review-round-counts` (`process`, governing version `2.2`),
branch `milestone/review-round-counts`, base `16c2599` (main after #49: the release
source is Workflow 2.14.0 and this repository's own installation is the published
2.14.0). Roadmap row 14. The plan is `docs/ai-workflow/REVIEW_ROUND_COUNTS_PLAN.md`,
approved by gate policy at plan revision 3. The previous milestone, W10
(`finding-dispositions`, Workflow 2.14.0), is complete.

## Goal

Workflow 2.15.0, a minor release (`feat:`), in four checkpoints: `next-action`
reports how many **local** and how many **external** review rounds an item has had
at each stage (`plan_local`, `plan_external`, `implementation_local`,
`implementation_external`), from one persisted counter `review_round_counts`
written in the verdict's own state transaction. Orchestration Protocol becomes 1.5,
additive.

1. **CP1** the counter in the state and the four review writers.
2. **CP2** the four snapshot fields, schema and protocol constant 1.5.
3. **CP3** the Protocol 1.5 specification and the user documents.
4. **CP4** release 2.15.0 bookkeeping and the downgrade posture.

## Current checkpoint

CP1 is complete: `workflow_state.initial_review_round_counts` (written by
`default_work_item`: `plan` is a zero pair for a two-stage plan-review version,
`implementation` for `2.2`, else `null`), `review_round_counts_errors`,
`validate_review_round_counts` and `InvalidReviewRoundCountsError` (none of them
called from `validate_state`, so a malformed counter never refuses an operational
path), and the private `_count_review_round`, called by the four review writers for
`APPROVE` and `REVISE` only. An absent key, a `null` stage or a malformed value is
left exactly as it was. `review_round_counts` joins the four closed commit-field sets
that name `optional_findings`; the audit of the file's other closed sets
(`LEGACY_RETIREMENT_FIELDS`, `RESUME_IMPLEMENTATION_FIELDS`,
`_ACCEPTANCE_SATISFACTION_FIELDS`) is unchanged. Tests: `TestReviewRoundCounts` and
`TestReviewRoundCountsDowngrade` in `workflow_state_test.py`, including the
downgrade regression (2.15.0's helpers accept a committed counter-bearing recovered
generation record; helpers with 2.14.0's field sets refuse it).

CP2 is complete: `workflow_protocol.PROTOCOL_VERSION` is `1.5`; `_review_round` adds
`plan_local`, `plan_external`, `implementation_local` and `implementation_external`
after `current`, each from `_role_round`, which returns the persisted integer or
`None` (an absent key, a `null` stage or a malformed key) and never raises, so a
damaged counter cannot refuse `next-action` or `record-external-result`. `plan`,
`implementation` and `current` are unchanged. `op_verify` calls
`validate_review_round_counts` inside the `state_valid` check, so `verify` alone
reports a malformed key. The schema's `review_round` requires the four properties.
Tests: `TestPerRoleRoundFields` in `workflow_protocol_test.py` (the C10a sequence,
a complete implementation approval, `None` cases, the malformed-key fallback through
`next-action`, `record-external-result` and `verify`, the golden fields, the schema)
and every protocol-version assertion moved to 1.5.

CP3 is complete: `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` is at version
`1.5` (header and history sentence, section 1's release list, the envelope example,
the section 5.4 snapshot example and `review_round` bullet with the four per-role
fields, the ledger `round` correction, section 5.2's `state_valid` check naming
`validate_review_round_counts` and its not being applied by `validate_state`, section
8.1 per stage and role with the missing-versus-stale distinction, and a "Protocol
`1.5`" note in section 10). `docs/glossary.md` names the per-role counts;
`docs/common-problems.md` gains "A review-round count reads null", "A review-round
count reads lower than expected" and "Implementation approval fails with
`MalformedBundleGenerationRecordCommitError` after a move back to 2.14.0".
Verified: `tools/docs/check_docs.py` clean; `workflow_protocol_test` run from
`payload/scripts` (341 tests) passes every test that parses the specification; the 18
failures there are release-string and digest comparisons (a spot check of two of the
failing classes on a clean `HEAD` fails the same way; they need the staged fixture,
which CP4 runs against the committed manifest).

CP4 is complete: `manifest.json` is 2.15.0 with the digests, sizes and rationale of the
seven changed records refreshed (`counts` unchanged) and the `manager` block authored
as D-Downgrade states it (`min_manager_version` `1.13.0`, the supported downgrade
boundary as `posture`, the `undetectable` text, the `review-round-counts` `state-key`
signal, one `new_work_only` entry, no gate default change);
`conformance.suites` was written by `release.py manager-block --release-dir <scratch
directory> --write` from a staging of CP4's own content (protocol 341, state 1183). The
release constant in `workflow_protocol.py` is 2.15.0, with the protocol document's
envelope example and the two assertions of `workflow_protocol_test.py`. `docs/release-history.md` has the
2.15.0 row. `docs/ROADMAP.md` stays Current until acceptance.
