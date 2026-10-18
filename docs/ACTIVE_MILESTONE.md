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

## Functional review checklist

Item `review-round-counts`, implementation revision 2, branch
`milestone/review-round-counts`. All four checkpoints (CP1-CP4) are complete; the
release source is 2.15.0 (this repository's own installation stays 2.14.0 and is not
under test).

### Setup

- Work from the repository root on branch `milestone/review-round-counts`, clean tree.
- Run the release source scripts, not the installed ones: `payload/scripts/`
  (`workflow_state.py`, `workflow_protocol.py`). Use a scratch copy of the repository
  or a temp directory for any state you mutate; never write to this repository's
  `docs/ai-workflow/WORKFLOW_STATE.json`.
- Automated suites: run them from the staged fixture, not the source layout. Stage it
  with `python3 tools/release/release.py stage-conformance --commit HEAD --out
  "$TMPDIR/fixture"`, then run `python3 -m unittest workflow_state_test` and
  `workflow_protocol_test` in the fixture's `scripts/`. In the source-layout
  `payload/scripts` the state suite errors in two tests that read the live
  `WORKFLOW_STATE.json`, which the source layout lacks (they pass in the fixture), and
  the 18 protocol failures that compare release strings and digests also appear; all of
  these are expected outside the staged fixture.
- `python3 tools/docs/check_docs.py` must be clean.

### Test data

A scratch repository bootstrapped with the release source holding one `2.2` work item
(two-stage plan and implementation review) and one `2.1` item (plan stage only has two
stages), plus one item created before 2.15.0 (no `review_round_counts` key).

### Flows and expected results

1. **Fresh `2.2` item.** Run `next-action` for it. Expect `review_round` to carry
   `plan_local`, `plan_external`, `implementation_local`, `implementation_external`
   all `0`, alongside unchanged `plan`, `implementation`, `current`; protocol version
   `1.5`.
2. **Counting at the plan stage (the C10a case).** Record three local plan-review
   verdicts (`REVISE`, `REVISE`, `APPROVE` or the equivalent sequence) and one external
   plan verdict. Expect `plan_local` 3 and `plan_external` 1 in the next snapshot;
   `plan` unchanged from what 2.14.0 would return.
3. **BLOCK does not count.** Record a `BLOCK` verdict. Expect no counter change and
   the ingest otherwise as before.
4. **Implementation stage.** Record local and external implementation verdicts
   (`APPROVE`/`REVISE`). Expect `implementation_local`/`implementation_external` to
   rise by one each, `plan_*` unaffected.
5. **Pre-2.15.0 item (key absent).** `next-action` returns `null` for all four fields
   and does not refuse; recording a verdict leaves the absent key absent.
6. **Item whose stage is `null`** (e.g. a `2.1` item's implementation stage): that
   stage reads `null`, the other stage counts.
7. **Malformed counter.** Hand-edit a scratch state so `review_round_counts` is
   malformed. Expect `next-action` and `record-external-result` still work (fields
   `null`), the writers leave the value untouched, and `verify` alone reports
   `state_valid: fail` with an `InvalidReviewRoundCountsError` naming the malformed key.
8. **Monotonic.** A count never decreases and never returns to `null` once numeric,
   including across a new plan revision or implementation revision.
9. **Schema and docs.** `orchestration-protocol-v1.schema.json` requires the four
   properties in `review_round`; `ORCHESTRATION_PROTOCOL.md` is version 1.5 and its
   section 5.4 example illustrates an item with earlier plan reviews (`plan_local` 2,
   `plan_external` 2, implementation 0/0; the all-zero expectation belongs to flow 1
   only); the glossary and the three new
   `docs/common-problems.md` entries read correctly.
10. **Release bookkeeping.** `manifest.json` is 2.15.0 with a `manager` block
    (`min_manager_version` 1.13.0, `review-round-counts` state-key signal,
    one `new_work_only` entry); `docs/release-history.md` has the 2.15.0 row;
    `docs/ROADMAP.md` row 14 is still Current; `workflow-manager verify .` is clean
    (installation untouched).
11. **Downgrade posture.** In the state tests, 2.15.0's helpers accept a committed
    counter-bearing recovered generation record and 2.14.0's field sets refuse it
    (`TestReviewRoundCountsDowngrade`); the "Implementation approval fails with
    `MalformedBundleGenerationRecordCommitError`" entry in common-problems matches. The
    2.14.0 refusal comes from the published 2.14.0 release, which cannot change; the
    expected next step is that documented troubleshooting entry, not a next step in the
    refusal message. The 2.15.0 tampered-head/revision refusals are pre-existing messages
    this milestone does not change (a review-follow-up issue covers adding a next step to
    the recovered-role refusals).

### Known limitations / out of scope

- Counts are exact only from the verdicts recorded after 2.15.0; earlier verdicts of an
  existing item cannot be reconstructed (reads `null`, or lower than expected).
- The round caps (local 6, external 4) are enforced by the Controller
  (workflow-controller#88), not here.
- `BLOCK` verdicts are not counted; `plan`, `implementation`, `current` are unchanged.
- Downgrade to 2.14.0 is supported only to the boundary the manifest's `posture` states;
  a counter-bearing generation record cannot be approved there.
- The 18 release-string/digest failures in `workflow_protocol_test` outside the staged
  fixture are not a defect of this milestone.

### Functional review round 1

Checklist corrections only; no source, test or bundle change, and `technical_approval`
is untouched. Setup now runs the suites from the staged fixture (finding 1); flow 7
expects `state_valid: fail` with `InvalidReviewRoundCountsError` (finding 2); flow 9
expects the section 5.4 example's earlier-plan-review counts, all-zero stays in flow 1
(finding 3); flow 11 expects the documented troubleshooting entry (finding 4, expected
behavior). Re-test flows 7, 9 and 11.
