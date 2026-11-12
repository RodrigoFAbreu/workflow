# Active Milestone

## Milestone

**In progress.** W47: `wording-pass-plain-commands` (`process`, governing version `2.2`), branch `milestone/wording-pass-plain-commands`,
roadmap row 41 (RodrigoFAbreu/workflow#168, #165, #161 and #152 item 1). The plan is
`docs/ai-workflow/WORDING_PASS_PLAIN_COMMANDS_PLAN.md` (revision 2, approved by gate policy).

## Goal

Workflow 2.29.3 (a `fix:` patch): one pass over the stale wording of the plain acceptance commands. Every statement the four issues call
stale and the investigation found still false or misleading is corrected by the smallest true wording; the only changed output is the
detail of a library refusal (`complete_work_item`'s `phase_not_reachable`), which no plain flag prints. The protocol stays 1.5; the
Controller does not change.

## Checkpoints

- CP1 (the wording corrections, the library detail, the pins, the tests and row 41): complete (verified in a scratch fixture, see the commit).
- CP2 (release 2.29.3): complete (verified in a scratch clone, see the commit).

CP1 changes: `payload/scripts/workflow_state.py` (one string), `payload/scripts/workflow_gate_policy_test.py` (P7, P8; R6's needles),
`payload/scripts/workflow_integration_test.py` (two golden hashes), `payload/.claude/commands/satisfy-gate.md`, `accept-milestone.md`,
`apply-pr-review.md`, `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, `audit/WORKFLOW_DEFECT_LEDGER.md`, `docs/exit-codes.md`,
`docs/common-problems.md`, `docs/ROADMAP.md` (row 41).

CP2 changes: `manifest.json` (version 2.29.3, the eleven changed records, gate-policy count 424, the posture),
`payload/scripts/workflow_protocol.py` and its test (`WORKFLOW_RELEASE` 2.29.3), `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`
(release list, envelope example, protocol 1.5 note; names no changed message), `docs/release-history.md` (the 2.29.3 row),
`docs/exit-codes.md` and `docs/common-problems.md` ("Last checked with" lines), `tools/release/release_test.py` (the 2.29.3 class;
the 2.29.2 and 2.25.7 classes give up the current-release pins).

Self-review (phase `SELF_REVIEWING_IMPLEMENTATION`): CP1's E8 edit of `accept-milestone.md` step 5a dropped "both `false`", leaving
"with the content of both files is unchanged"; restored ("with both `false` the content of both files is unchanged", as in
`satisfy-gate.md`), its golden hash and the two manifest records follow, and the 2.29.3 release test pins the sentence in both commands.
Row 41 names `docs/common-problems.md` among the corrected pages.

## Functional review checklist

Scope under test: the wording of the plain acceptance commands' documents, and one library refusal detail
(`complete_work_item`'s `phase_not_reachable` text, `scripts/workflow_state.py:13759`). Nothing else changes: no flag, JSON key,
exit code, phase, command or Controller behaviour (protocol 1.5). The plain flags' own output must be byte-identical to the base.

### Setup

- Repository at `milestone/wording-pass-plain-commands`, checked out clean. Python 3 and `git` only; no network, no install, no
  zlib-ng, no Python 3.12, and no real `gh`, `claude`, `codex` or `ssh` (flow 4 writes its own logging `gh` stand-in).
- `export TMPDIR=<an empty scratch directory outside the repository>`. The flows write only there; none writes inside the clone.
- Build the two trees exactly as in `docs/ai-workflow/WORDING_PASS_PLAIN_COMMANDS_PLAN.md`, section 5 ("Functional review"):
  the base `payload/scripts`, `payload/.claude/commands` and `payload/docs` from `git archive da8c68e6b55765a95d37a974a5f396821329859e`
  into `$TMPDIR/base/`, the working tree's same three directories copied into `$TMPDIR/cand/`; `export BASE=... CAND=...`.
  Create `stmts.py`, `lib.py`, `flags.sh` from the same section (verbatim).

### Test data

Nothing to seed. Flow 4 builds its own scratch repository and state file; flow 3 uses an in-memory state; flows 1, 2, 5 and 6 read the two trees.

### Flows

| # | Do | Expect |
| --- | --- | --- |
| 1 | `for r in BASE CAND; do echo "== $r"; python3 -I "$TMPDIR/stmts.py" $r x; done` | BASE: every `old=` is `1` and every `new=` is `0`. CAND: every `old=` is `0` and every `new=` is `1`. |
| 2 | In the repository root, run the grep pairs of plan section 5, flow 2 (exit-codes page, `docs/common-problems.md` with newlines folded, roadmap row 41) against `git show da8c68e:<file>` and the working tree. | BASE: `1` for each of the four old phrases and the old common-problems sentence; `0` for the roadmap row. CAND: `0` for each old phrase and the old sentence; `1` for the new common-problems sentence and the roadmap row. |
| 3 | `for r in BASE CAND; do for p in IMPLEMENTING MILESTONE_COMPLETE; do python3 -I "$TMPDIR/lib.py" "$(eval echo \$$r)/scripts" $p "$TMPDIR"; done; done` | IMPLEMENTING: BASE says `needs AWAITING_FUNCTIONAL_REVIEW`; CAND says `needs AWAITING_FUNCTIONAL_REVIEW or AWAITING_USER_ACCEPTANCE`; both keep `phase_not_reachable` and `state unchanged: True`. MILESTONE_COMPLETE: `work_item_terminal`, identical on both sides. |
| 4 | `for s in BASE CAND; do sh "$TMPDIR/flags.sh" "$(eval echo \$$s)/scripts"; done` | The two digests printed for BASE equal the two printed for CAND (the plain flags' bytes do not move). `--satisfy-acceptance` exits 1 and its message still reads "the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW"; `--acceptance-gate` exits 0 with `ready: false`. `gh calls 0`, and `git status --short` in the scratch repository is empty. |
| 5 | Diffs of the trees (plan section 5, flow 5): `scripts/workflow_state.py`, `.claude/commands`, `docs`, `ORCHESTRATION_PROTOCOL.md`. | One changed line in `workflow_state.py`. Commands differ only in `accept-milestone.md`, `apply-pr-review.md`, `satisfy-gate.md`. Docs differ only in `REVIEW_PROTOCOL.md`, `audit/WORKFLOW_DEFECT_LEDGER.md`, `ORCHESTRATION_PROTOCOL.md`; the last shows exactly three changed hunks (release list, envelope example, protocol-1.5 note). |
| 6 | `grep -c 'needs AWAITING\|CompletionPhaseNotReachable'` on both `ORCHESTRATION_PROTOCOL.md` and `orchestration-protocol-v1.schema.json`, both trees; `grep -c 'PROTOCOL_VERSION = "1.5"' "$CAND/scripts/workflow_protocol.py"`. | `0` for both files on both sides; `1` for the protocol-version line. |
| 7 | Mutation check (plan section 5, flow 7): copy the candidate to `$TMPDIR/mut`, put the old E6 sentence back into its `satisfy-gate.md`, rerun flow 1 on it. | Exactly that statement reads `old=1 new=0`; the other rows are unchanged. |

Flows 8 to 11 of plan section 5 (the nine suites, the `tools/release` and `tools/docs` tests, the scope diff) need the full
environment: the nine suites, `tools/release` needs the pinned zlib-ng runtime (`docs/RELEASING.md`). They are automated
verification, not functional flows, and are not part of this checklist.

### Known limitations and deliberate non-changes

- Deliberately kept, out of scope: `satisfy-gate.md`'s human-path list (around line 321); the 2.28.0 row of
  `docs/release-history.md` (it records what that release said); test `P3`'s name; the "another writer changed the state"
  sentence of the other plain flags (no issue names them). No behaviour changes. Plan section 0a lists the rest.
- The library detail (flow 3) is reached only by a direct caller of `complete_work_item`; no plain flag prints it.
- Release 2.29.3 is the candidate on this branch. Nothing is published, tagged or merged.

### Findings

Put findings at `.ai-review/wording-pass-plain-commands/feedback/FUNCTIONAL_REVIEW.md` (the path `ensure_feedback_dir` prints
when this checklist is prepared). `/apply-functional-review` then routes each one: a same-scope fix to its bounded branch, new or wider
scope to a `<parent-id>-remediation-<n>` child work item.

## Next action

User functional testing against the checklist above. Once testing is clean, `/accept-milestone` is the only acceptance command.
Both checkpoints (CP1, CP2) are already `COMPLETE`, so nothing outstanding blocks it.
