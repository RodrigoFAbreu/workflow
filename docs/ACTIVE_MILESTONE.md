# Active Milestone

## Milestone

**Self-reviewing implementation** (plan revision 1, plan approved; CP1 to CP5 complete). W6: `functional-fix-commit-order`
(`process`, governing version `2.2`), branch
`milestone/functional-fix-commit-order`, base `04d155a` (the release source is
Workflow 2.9.1; this repository's own installation is also 2.9.1 with automatic
gates and no `GATE_POLICY.json`). The plan is
`docs/ai-workflow/FUNCTIONAL_FIX_COMMIT_ORDER_PLAN.md`. The previous milestone,
W4 (`review-stage-write-durability`, Workflow 2.9.1), is complete. W5
(`retire-21-for-new-work`) is paused at its plan review in another worktree and
resumes after this release.

## Goal

Workflow 2.9.2, a patch release that fixes
[RodrigoFAbreu/workflow#19](https://github.com/RodrigoFAbreu/workflow/issues/19)
and [#20](https://github.com/RodrigoFAbreu/workflow/issues/20):

1. **#19.** `/apply-functional-review`'s bounded branch commits the post-fix
   generation record, then updates the checklist in `docs/ACTIVE_MILESTONE.md`
   after it. That commit moves `HEAD` past the bundle's generation head, and the
   next implementation review stops with `bundle_generation_mismatch`. The
   bounded branch now commits the stale technical-approval write before the
   first edit (it was persisted only, and a record commit that sweeps it up is
   refused), then the fix, then the narrative and checklist, and the
   generation record last. Nothing is committed after it.
2. **#20.** Every command that states the trailer rule (`OPUS-R129-001`) says
   plainly that `Co-Authored-By:`/`Claude-Session:` lines go in their own
   paragraph before the `Workflow-*` trailers, because a generation record's
   trailer set is checked exactly. The refusal message names the cause and the
   remedy.

The read side stays strict, the Orchestration Protocol stays 1.2, no state or
commit shape is added, and the Manager lane's order (checklist committed before
the record) keeps working.

## Current checkpoint

CP1 to CP4 complete. CP1: `/apply-functional-review`'s bounded branch
commits the stale technical-approval write before the first edit, runs steps 5
and 6 before the one regeneration, and says no commit follows the record. CP2:
all 14 commands that state `OPUS-R129-001` say the trailers are the final
paragraph and nothing else is in it, with `Co-Authored-By:`/`Claude-Session:`
lines in an earlier paragraph; the six generation-record writers add why (the
record's trailer set is checked exactly); the trailer-set refusal names the
cause and remedy; golden hashes, the two trailer-shape classes and a static
wording test updated or added. CP3: `FunctionalFixCommitOrderProcess` and
`...Product` in `workflow_acceptance_matrix_test.py` (11 scenarios each) drive
the bounded branch through the command's own commits to the next review and the
technical approval: the issue's case for a `"2.2"` item, a `"2.1"` item, a
`same_content` round, two findings in one round, a mixed round with a child's
uncommitted entry, the Manager lane's order and a committed stale write
(compatibility pins), both traps pinned (checklist after the record gives row
25a `bundle_generation_mismatch`; an uncommitted stale write makes the record
refused), and recovery plus an ordinary record in the corrected trailer layout,
each also refused with `Co-Authored-By:` in the trailer paragraph and then
validated after the message rewrite. Verified in a scratch conformance fixture
(v2.9.1 plus the working-tree payload): the integration (289), acceptance-matrix
(353), state, protocol (314), fingerprint (257), generalization (105),
gate-policy (292), completion-obligations (106) and harness (22) suites pass;
the two demo suites need real-repository history the fixture lacks and were
not run. CP4: `REVIEW_PROTOCOL.md` gains "A generation record is the last
commit, and its trailer paragraph" (D-Last-Commit with the bounded fix's order
as the example, D-Trailers' paragraph rule, the strict read side and the
2.9.1 downgrade posture); `MILESTONE_WORKFLOW.md` and the operator reference
name the bounded fix's order; `docs/common-problems.md` gains the
`bundle_generation_mismatch`-after-a-functional-fix and trailer-set entries.
A stray `**` in `apply-functional-review.md`'s no-commit-after-the-record
paragraph (CP1) is fixed and its golden hash updated. `check_docs.py` is clean;
the protocol (314), state (1090), integration (289), acceptance-matrix (353),
fingerprint (257), generalization, gate-policy, completion-obligations and
harness suites pass in a scratch fixture (working tree over the repository).
CP5: release 2.9.2: `manifest.json` names 2.9.2 with every changed `sha256`/`size`
refreshed from the bytes (`counts` and the derivation text are unchanged: no
artifact is added), `WORKFLOW_RELEASE` is `2.9.2` (`PROTOCOL_VERSION` stays
`1.2`, `manager-pin.json` untouched), `ORCHESTRATION_PROTOCOL.md` lists 2.9.2
among the tested releases, the protocol test pins the release, and
`docs/release-history.md` has the 2.9.2 row with the downgrade paragraph. The
stock `release.py stage-conformance` accepts the tree, and the nine suites pass
in that fixture. `ROADMAP.md` marks W6 Done at acceptance.

## Next action

Full milestone diff self-reviewed (no blocking or important finding; the
roadmap's W6 status now reads "implementation in review"). Next: the full
verification and the implementation-review bundle, then the local and manual
implementation reviews.
