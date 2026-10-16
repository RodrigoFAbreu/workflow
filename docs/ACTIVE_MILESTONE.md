# Active Milestone

## Milestone

**Planning.** W8: `review-convergence` (`process`, governing version `2.2`),
branch `milestone/review-convergence`, base `f30e352` (main after the CI
change #27: the release source is Workflow 2.11.0; this repository's own
installation is also 2.11.0 with automatic gates, default "2.2" and no
`GATE_POLICY.json`). Requested by the Controller lane; the owner approved the
slot on 2026-10-14. The plan is `docs/ai-workflow/REVIEW_CONVERGENCE_PLAN.md`.
The previous milestone, W7 (`checkpoint-anchors-early`, Workflow 2.11.0), is
complete.

## Goal

Workflow 2.12.0, a minor release (`feat:`), roadmap row 9. Review loops are
about two thirds of the Controller's worker cost; this release makes them
cheaper and shorter without changing what an approval binds:

1. **Incremental re-review.** From round 2 a bundle carries
   `CHANGES_SINCE_REVIEW.md`: the diff of the protected content since the
   last reviewed bundle and that round's findings, at both stages, for the
   local and the manual reviewer. A round may review only the changes to
   return `REVISE`; every `APPROVE` is a full review of the whole bundle.
2. **Severity rule.** A `REVISE` must name a Blocking or Important finding,
   and an `APPROVE` may not declare a changes-only review; otherwise the
   verdict is refused as malformed and reissued, never converted. A round
   with only optional findings is an `APPROVE` with the findings recorded.
3. **Round field.** Orchestration Protocol 1.4 adds `review_round` to the
   `next-action` snapshot (the plan and implementation round, and which
   review stage is waiting), so an orchestrator can stop at its own cap.
   Accepting at a cap stays a person's step; the plan's OD-1 names the gap
   for two-stage items.
4. **Small plans.** `/milestone-plan` asks for few checkpoints and warns,
   without blocking, above six.

Nothing new is persisted in state; approvals, gates and who may approve are
unchanged.

## Current checkpoint

Implementing, plan revision 9. CP1 (verdict shape) is complete:
`assert_verdict_well_formed`, `parse_review_scope` and
`MalformedVerdictError` in `workflow_fingerprint.py`, called by
`ingest_manual_review_verdict` at a two-stage row and by the two local review
commands before they write; the two manual commands report a refusal and ask
for a reissue; `REVIEW_PROTOCOL.md` states the severity meanings and the
rule. `workflow_protocol.py` needed no change: a `MalformedVerdictError` maps
to `refused` by default. Verified in a scratch release fixture: the nine
conformance suites pass. CP2 (the changes file) is complete:
`workflow_fingerprint.write_changes_since_review` builds
`CHANGES_SINCE_REVIEW.md` (preamble, previous findings, pinned-option diff) at
the plan stage (outgoing `.pin` against the staging pin, carried forward on a
wrapper-only regeneration, promoted or removed with `AMENDMENT_DIFF.patch`) and
at the implementation stages (previous round's reviewed head against the
working tree, from the outgoing manifest copy `prepare-ai-review.sh` keeps; a
same-content republication leaves it alone); the archive carries it; the
review and request commands and the three protocol documents state the review
rule. `load_implementation_stage_classification` gained `at_commit`. Thirteen
tests in `workflow_fingerprint_generalization_test.py` (`TestChangesSinceReview`).
CP3 (protocol 1.4) is complete: `workflow_protocol._review_round` adds the
snapshot's `review_round` (`plan` an exact count from the consumed-content
history and the binding record, or `null` for every shape not shown complete;
`implementation`; `current`), `PROTOCOL_VERSION` is `1.4`, the schema gained the
property, and `ORCHESTRATION_PROTOCOL.md` states the field, the exactness
boundary, the round cap (8.1), the verdict courier (8.2) and a 1.4 note. Nine
tests in `workflow_protocol_test.py` (`TestReviewRoundField`), including the
generator-driven drive; `without_release()` strips the field. The suite's 16
failures (a stale `workflow_release` of 2.9.0 in the update-simulation tests)
are the same at the CP2 commit. CP4 (plan-size guidance) is complete:
`workflow_state.PLAN_CHECKPOINT_SOFT_LIMIT` (6) and `plan_size_advisory`, printed
at the publication point of `/milestone-plan` and `/apply-plan-review` (a
`[2.1]` step 3 sentence keeps the `"1"` output unchanged); the
`validate_local_plan_review_preconditions` refusal names `/milestone-plan <id>`
or `/apply-plan-review <id>` at a non-ready phase; `docs/RELEASING.md`'s
`stage-conformance` example uses `--out "$(mktemp -d)/fixture"`; the over-long
line in `milestone-plan.md` step 6 is rewrapped. Two tests in
`workflow_state_test.py`; golden hashes refreshed. Verified in a scratch release
fixture: the nine conformance suites pass. CP5 (release 2.12.0) is complete:
`manifest.json` 2.12.0 with refreshed digests, `WORKFLOW_RELEASE`, the
tested-releases list, the release-history row with the downgrade posture and
the courier clarification (closes workflow#28), and the common-problems, gates
and glossary entries.

Every checkpoint is complete; the phase is `SELF_REVIEWING_IMPLEMENTATION`.
The self-review of the whole milestone diff fixed three documentation
defects: `REVIEW_PROTOCOL.md` and the glossary said `Review scope: changes` is
valid on a `REVISE` only, where the check, the commands and the other documents
accept it on a `REVISE` or a `BLOCK`; and the protocol's 1.4 compatibility note
now says that a consumer validating against its own copy of the 1.3 schema
(whose `snapshot` has `additionalProperties: false`) rejects the new field, as
the plan's risk section requires. Manifest digests refreshed for the two
payload documents.

## Next action

The implementation review: the bundle is generated at
`AWAITING_LOCAL_IMPLEMENTATION_REVIEW`, then `/review-implementation
review-convergence`.

## Functional review checklist

This is a `process` milestone: there is no app to run. The "product" is the
Workflow release source (`payload/`), exercised through a scratch fixture so
that this repository's own installation is never touched.

### Setup

1. On branch `milestone/review-convergence`, clean tree.
2. Build the conformance fixture outside the repository:
   `python tools/release/release.py stage-conformance --commit HEAD --out "$(mktemp -d)/fixture"`
   (`<fixture>` below is the path it prints/creates).
3. `workflow-manager verify .` must stay clean (this repository's
   installation is unchanged by the milestone). With no network it needs an
   offline release source: point `WORKFLOW_MANAGER_RELEASE_SOURCE` at a local
   mirror of the published 2.11.0 release.
4. No feature flags or seed data are needed; tests build their own scratch
   repositories.

### Flows and expected results

1. **Suites.** In `<fixture>`, run the nine frozen suites
   (`scripts/*_test.py`). *Expected:* all pass. (Known: the in-repo
   update-simulation tests with a stale `workflow_release` of 2.9.0 fail
   identically at the CP2 commit; they are not caused by this milestone.)
2. **Verdict shape (CP1).** In `<fixture>`, feed
   `workflow_fingerprint.assert_verdict_well_formed` (or run the
   `TestMalformed*` tests) with: a `REVISE` listing only optional findings;
   an `APPROVE` with `Review scope: changes`; a punctuation-only
   "none" placeholder. *Expected:* the first two raise
   `MalformedVerdictError` (reported as `refused`, never converted); the
   punctuation-only entry is treated as "none". An `APPROVE` with only
   optional findings is accepted and the findings are recorded.
3. **Changes file (CP2).** Drive a work item to round 2 of a plan review and
   of an implementation review (the `TestChangesSinceReview` tests do this).
   *Expected:* the bundle contains `CHANGES_SINCE_REVIEW.md` with preamble,
   previous findings and the diff since the last reviewed bundle; round 1 has
   none; a same-content republication leaves it unchanged. The file is a
   sibling of `current/` (at `.ai-review/<id>/CHANGES_SINCE_REVIEW.md`),
   included at the archive root and outside both identity inputs.
4. **Round field (CP3).** Run `python3 scripts/workflow_protocol.py
   next-action` (or the `TestReviewRoundField` tests) at a plan-review and an
   implementation-review wait. *Expected:* `protocol_version` is `1.4`;
   `snapshot.review_round` shows `plan`, `implementation`, `current`
   (`plan` is `null` where the count cannot be shown exact) and validates
   against `orchestration-protocol-v1.schema.json`.
5. **Plan-size advisory (CP4).** Publish a plan with 7+ checkpoints via
   `plan_size_advisory` (or `/milestone-plan` in the fixture). *Expected:* a
   non-blocking warning naming the limit 6; at 6 or fewer, no warning; a
   `"1"` item's output is unchanged.
6. **Release metadata (CP5).** Check `manifest.json` version `2.12.0`,
   digests current, `WORKFLOW_RELEASE`, release-history row and the
   downgrade posture. *Expected:* consistent; `release.py check-pending`
   validates the version/source transition (it prints `ok: 2.12.0 -> 2.12.0`
   for an unchanged release source). For the unpublished check, run
   `release.py check-immutable` with an offline `--releases` inventory
   (expect `version 2.12.0 is not published`); publishing is a later owner
   step.
7. **Docs read-through.** Skim `REVIEW_PROTOCOL.md` (severity meanings,
   review-scope rule), `ORCHESTRATION_PROTOCOL.md` (field, round cap 8.1,
   courier 8.2, 1.4 note) and the three review commands. *Expected:* the
   rules agree with each other and with the behavior seen in flows 2-4;
   `Review scope: changes` is valid on a `REVISE` or a `BLOCK`.

### Known limitations / out of scope

- Nothing new is persisted in state; approvals, gates and who may approve
  are unchanged.
- Accepting at a round cap stays a person's step; for two-stage items the
  plan's OD-1 records the gap (no new command).
- `review_round.plan` is `null` for shapes not shown complete (by design).
- A consumer validating against its own copy of the 1.3 schema rejects the
  new field (documented in the 1.4 compatibility note).
- Publishing 2.12.0 and the `workflow-manager` pin are separate, later steps.

### Functional review round 1

- **Fixed** (documentation only, no behavior change): the
  `ORCHESTRATION_PROTOCOL.md` examples (envelope release `2.12.0` with
  protocol `1.4`; the IMPLEMENTING decision shows `review_round.current` null);
  `REVIEW_PROTOCOL.md` and `assert_verdict_well_formed`'s docstring now state
  exactly what the shape check enforces (an `APPROVE` with a Blocking finding
  is refused; one with an Important entry is not, and the entry stays
  recorded) and that a punctuation-only entry is a "none" placeholder.
  Checklist flows 3 and 6 and setup step 3 corrected.
- **Deferred to a later release:** refusing an `APPROVE` that lists Important
  findings; wrapped or prefixed placeholders such as `- (none)` (LIR-R4-001).
- **Re-test:** flows 3, 6 and 7.
