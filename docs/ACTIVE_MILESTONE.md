# Active Milestone

## Milestone

**Complete** (accepted; the release follows the merge). W8: `review-convergence` (`process`, governing version `2.2`),
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

None. All five checkpoints (verdict shape, the changes file, protocol 1.4,
plan-size guidance, release 2.12.0) are complete and the milestone was accepted
after two functional review rounds. The plan is archived at
`docs/milestones/completed/REVIEW_CONVERGENCE_PLAN.md`.

## Next action

Row 10 (the Controller's C10) and row 11 (M3) wait on the Controller. The next
repository milestone is row 12, acceptance-matrix sharding and managed
conformance width, once the owner schedules it: `/milestone-plan`. Publishing
2.12.0 follows the pull request merge, then the `workflow-manager` pin.

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
