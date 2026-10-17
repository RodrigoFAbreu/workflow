# Active Milestone

## Milestone

W10: `finding-dispositions` (`process`, governing version `2.2`), branch
`milestone/finding-dispositions`, base `f8eea78` (main after #42: the release
source is Workflow 2.13.0 and this repository's own installation is the
published 2.13.0). Roadmap row 11. The plan is
`docs/ai-workflow/FINDING_DISPOSITIONS_PLAN.md`, approved by gate policy at
plan revision 5. The previous milestone, W9 (`review-loop-fixes`, Workflow
2.13.0), is complete.

## Goal

Workflow 2.14.0, a minor release (`feat:`), in five checkpoints:

1. **CP1, CP2** every Optional finding of every recorded verdict is kept in the
   item's state (workflow#34); acceptance refuses while one has no disposition
   (`fixed`, `dropped` with a reason, or a `follow-up` with a link), and the
   dispositions go into the completed-milestone record.
2. **CP3** `verify` and `/adopt-gate-policy` name the cause of a gate-policy
   adoption merged with a merge commit (workflow#37).
3. **CP4** a plan whose artifact declaration leaves a path named in a Files
   paragraph unclassified is refused before review (workflow#40).
4. **CP5** release 2.14.0 bookkeeping. The Orchestration Protocol stays 1.4.

## Current checkpoint

CP1 is complete: `workflow_fingerprint.parse_optional_findings` reads the
`## Optional findings` section (top-level entries only; identity is the whole
entry as written, label included, whitespace collapsed; the key is `F-` plus 12
hex characters of its sha256). `workflow_state.merge_optional_findings` and the
new `verdict_text` keyword on `record_local_plan_review`,
`record_manual_plan_review`, `record_local_implementation_review` and
`record_manual_implementation_review` record an `APPROVE` or `REVISE` verdict's
findings into the work item's `optional_findings` in the verdict's own
transaction (a `BLOCK`, or a call without `verdict_text`, records nothing);
`ingest_manual_review_verdict` passes the text, `/review-plan` and
`/review-implementation` say to. `validate_state` checks the key's shape
(`InvalidOptionalFindingsError`). `optional_findings` is admitted by the four
closed commit-field sets (`REVIEW_STAGE_WRITE_COMMIT_FIELDS`,
`TECHNICAL_APPROVAL_COMMIT_FIELDS`, `ORDINARY_BUNDLE_GENERATION_RECORD_FIELDS`,
`RECOVERED_BUNDLE_GENERATION_RECORD_FIELDS`). Audit of the file's other closed
field sets (`LEGACY_RETIREMENT_FIELDS`, `RESUME_IMPLEMENTATION_FIELDS`,
`_ACCEPTANCE_SATISFACTION_FIELDS`, `_ACCEPTANCE_INPUT_FIELDS`, `_REOPENING_FIELDS`):
none concerns a verdict's write; unchanged. `REVIEW_PROTOCOL.md` carries the
"Optional findings are recorded" paragraph and the declared limits.
