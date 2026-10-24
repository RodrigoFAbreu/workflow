# Active Milestone

## Milestone

**In progress.** W23: `checkpoint-start-command` (`process`, governing version `2.2`), branch
`milestone/checkpoint-start-command`, roadmap row 24c (RodrigoFAbreu/workflow#55 and the three command items of
#97). Plan: `docs/ai-workflow/CHECKPOINT_START_COMMAND_PLAN.md` (revision 3, approved by gate policy).
The goal is Workflow 2.19.0, a minor release (`feat:`): the user-only command
`/release-checkpoint-start <work-item-id> <checkpoint-id>`, which releases an uncommitted checkpoint start by
calling the W22 engine after a confirmation bound to the claim the user was shown. The previous milestone, W22
`checkpoint-start-engine`, is accepted (Workflow 2.18.7).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The command, its confirmation, the amendment message and their tests | **complete** |
| CP2 | Release 2.19.0 | **complete** |

## Verified state

- CP1: `observe_checkpoint_start_release`, `release_checkpoint_start_confirmed`, the sentence builder and
  validator, `claim_reference` and the engine keyword `confirmed_claim_ref` are in
  `payload/scripts/workflow_state.py`; both `AmendmentCheckpointActiveError` raise sites name the command.
  `TestReleaseCheckpointStartCommand` (C1 to C5) was shown red against the unedited code and passes;
  `TestReleaseCheckpointStartCommandFile` (C6) pins the command file; the command file, `COMMAND_FILES.md`, the
  operator reference, `MILESTONE_WORKFLOW.md`, `request-plan-amendment.md` and the census tests are updated.
- CP2: `manifest.json` names 2.19.0 (80 artifacts, 54 distribution; the command file has its record; every
  changed record has its digest, size and `checkpoint-start-command (workflow-2.19.0)` sentence; the manager
  block's posture and measured suite counts are rewritten); `WORKFLOW_RELEASE` and its two pinned assertions,
  `ORCHESTRATION_PROTOCOL.md` (protocol stays 1.5), `docs/release-history.md`, `docs/CONCURRENCY_INVARIANTS.md`,
  `docs/common-problems.md` and a 2.19.0 class in `tools/release/release_test.py` are updated.
- No lock, guard, claim, `os.link` or `flock` site was added.
- Verified in a disposable clone (D-Staging): see the commit message of CP1 for the exact runs.

## Functional review checklist

Reviewed: implementation revision 2, reviewed implementation head `2c7446c` (base `ad1121a`). Both
implementation-review stages approved it, and the nine staged suites passed on that head. Since then only
`docs/ai-workflow/WORKFLOW_STATE.json` changed.

### Setup

- A clean checkout of `milestone/checkpoint-start-command`. Python 3 and git; no network and no GitHub.
- Manual flows run in a scratch clone under `$TMPDIR`, never in this checkout: the command writes the
  working-tree `docs/ai-workflow/WORKFLOW_STATE.json`.
- Automated suites: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`,
  then the nine suites from inside `$TMPDIR/fixture/scripts` (`docs/RELEASING.md`, "Verification commands").

### Test data

- A scratch work item with one checkpoint started and not committed, built the way
  `TestReleaseCheckpointStart._start` builds it: `claim_checkpoint`, then an `owner_mutation` window at step
  `1d` around `transition_checkpoint_in_progress`. Note the work item id, the checkpoint id and the claim
  reference (`owner_token[:12]`) before you start.
- A second copy of the same scratch state, for the stale-sentence flow.

### Flows

Automated (offline; the functional tester can run these):

- **A1** `TestReleaseCheckpointStartCommand` (C1 to C5). Expect: the sentence is built and validated (case
  and whitespace free, every near-miss refused); observation before the release; the entry and the claim are
  gone afterwards; nothing is committed.
- **A2** the same class, the interruption cases. Expect: a second run after an interruption completes; an
  interruption after the claim unlink reports `released` with nothing written; a commit carrying the
  checkpoint's trailer refuses the release.
- **A3** the same class, the stale sentence. Expect: a sentence for an earlier claim is refused;
  `request_plan_amendment` is accepted after the release, and before it the refusal names
  `/release-checkpoint-start <work-item-id> <checkpoint-id>`.
- **A4** `workflow_state_test.py` under the Manager's orphan wrapper. Expect: no new orphan.
- **A5** the nine suites, `tools/release` and `tools/docs`, `check_docs.py`, `check-manager-block`. Expect: all
  pass (`tools/release` needs the pinned zlib-ng Python; see the sandbox notes below).
- **A6** the user-only command lists agree. Expect: `COMMAND_FILES.md`, the operator reference,
  `MILESTONE_WORKFLOW.md`, `request-plan-amendment.md`, the protocol sentence and `common-problems.md` all
  name the same seven user-only commands, `/release-checkpoint-start` included.

Manual (a person, in Claude Code, in the scratch clone):

- **M1** Run `/request-plan-amendment <work-item-id>` on the scratch item. Expect: refused with
  `AmendmentCheckpointActiveError`, naming `/release-checkpoint-start <work-item-id> <checkpoint-id>` and
  saying to run it from the worktree that holds the claim.
- **M2** Run `/release-checkpoint-start <work-item-id> <checkpoint-id>`. Expect, before any question: the
  claim (checkpoint, worktree, `claimed_at`, adopted or not, `claim_ref`), the kind `entry`, the guard
  (none, or its step, class and holder state), the probe result, what the sentence attests, the interruption
  wording, and then the exact sentence to send back.
- **M3** Send a wrong sentence (another checkpoint, or the sentence without the attestation). Expect:
  refused with the expected sentence printed; `git status` shows no change to the state file; the claim is
  still present.
- **M4** Send the exact sentence. Expect: the report names the entry restored to `HEAD`'s state (absent, or
  the demoted entry), the claim removed, nothing committed, and `/request-plan-amendment` or
  `/milestone-implement` as the next step. `git log` is unchanged.
- **M5** Run `/request-plan-amendment <work-item-id>` again. Expect: it is no longer refused for the released
  start.
- **M6** Run `/release-checkpoint-start` once more. Expect: the `released` outcome, with no question asked and
  nothing written.

### Expected results for the whole review

A flow passes when the stated expectation holds and the working tree is clean apart from the scratch state
file. Any refusal with a `defect` cause goes to `FUNCTIONAL_REVIEW.md`.

### Known limitations and out of scope

- **The attestation is text, not a check** (`D-Residual`). The command cannot see an owner session that is
  alive and idle. A test must not expect a refusal for that case.
- Nothing is committed by the command, and the protocol version stays at 1.5.
- The release itself (the `2.19.0` tag, the GitHub release and the `main` merge) is outside this review: it
  runs through the `Release` workflow on merge, and needs GitHub.
- `workflow-manager verify .` needs the installed release's assets in the release cache; a missing cache is
  an environment issue, not a product defect.

### Sandbox notes (for the functional tester)

- A1 to A4, and the offline parts of A5 and A6, run with no network, no `gh` and no `claude`.
- M1 to M6 need a live Claude Code session; the functional tester runs the engine-level A flows instead.
- `tools/release` needs the pinned zlib-ng Python; if the sandbox `PATH` does not include it, the refusal is
  an `environment` limit, not a `defect`.
- `workflow-manager verify .` needs the installed binary and its release cache; if either is missing from the
  sandbox, the refusal is `environment`.
- A link-deleting tool in the clone (the output folder) is an `environment` refusal, as the sandbox note says.

## Next action

Functional review: run the checklist above and place any findings in
`.ai-review/checkpoint-start-command/feedback/FUNCTIONAL_REVIEW.md`. Then `/apply-functional-review` for each
finding, or `/accept-milestone` once everything passes (both checkpoints are `COMPLETE`).
