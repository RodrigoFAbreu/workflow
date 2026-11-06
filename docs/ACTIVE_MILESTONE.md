# Active Milestone

## Milestone

**Complete (accepted by policy).** W43: `acceptance-floor-commit` (`process`, governing version `2.2`), branch
`milestone/acceptance-floor-commit`, roadmap row 38 (RodrigoFAbreu/workflow#148, the last Python call). The plan is
`docs/ai-workflow/ACCEPTANCE_FLOOR_COMMIT_PLAN.md` (revision 5, approved by gate policy). The previous milestone, W42
`acceptance-findings-floor` (Workflow 2.28.0), is complete. The release follows the merge.

## Goal

Workflow 2.29.0 (a `feat:` minor): `python3 scripts/workflow_state.py --commit-gate-policy-floor <id>` calls
`commit_gate_policy_floor` (unchanged, byte for byte) and, when that answers `None`, a new sibling
`commit_pending_gate_policy_floor` that commits a floor already waiting in the state file after six preconditions;
prints `{commit, recovered}`. It refuses unless the item is `MILESTONE_COMPLETE` and `HEAD` holds its completed copy. The
acceptance stage then has no inline Python call; the protocol stays 1.5.

## Checkpoints

- CP1 (the floor flag, its recovery, tests, the command text and the pages): implemented, verified state below.
- CP2 (release 2.29.0): implemented, verified state below.

CP1 verified state: `TestCommitFloorCommand` (29 tests at that commit) passes on the working tree, alongside the 2.26.0 to 2.28.0 command
classes; the source of `commit_gate_policy_floor` hashes to the base's value (pinned by F8). The staged-fixture run of the nine
suites, `tools/docs`, `check_docs.py`, `check-manager-block` and `tools/release` ran under D-Staging (the one expected failure is the
2.28.0 release class's suite-count pin, released in CP2). The CP1 commit carries no report of them, and no record of the failure-only
mutations survives from CP1: they were run in self-review, below.

CP2 verified state: `manifest.json` is 2.29.0 (six records, posture, suite count 402 for `workflow_gate_policy_test.py`), `WORKFLOW_RELEASE`
is 2.29.0, the protocol document, release history and exit-codes page follow, and `tools/release/release_test.py` has the 2.29.0 class
with the 2.28.0 class demoted. In a disposable clone: all nine suites pass from a stock `stage-conformance` fixture, `release.py build`
succeeds (zlib-ng interpreter), `check-manager-block` (with `--manager-releases`) is ok, `tools/docs` tests and `check_docs.py` are clean,
`tools/release` tests pass (317). `workflow-manager verify .` is clean against the installed 2.28.0.

Self-review (`/milestone-implement`, full diff), three gaps fixed, no engine change. (1) The command text lacked D-Output's sentence on
`state_changed: true` with `commit: null`, which means something else than on the flags before it: `satisfy-gate.md` and `docs/exit-codes.md`
now say it, and R6 pins it. (2) Mutants m14 (dispatch after the shared `git rev-parse`, and the empty id) survived: the class called the CLI
function directly, past the parser. F7's parser test now covers both. (3) F7 did not pin the five existing flags' output, so m16 survived;
`test_f7_the_existing_flags_print_what_they_printed` is new. The suite count for `workflow_gate_policy_test.py` is 404. The series m1 to m26 now
runs, each mutant failing a named test; the results are in the implementation bundle's `TEST_RESULTS.md`.

## Functional review checklist

Gate: `AWAITING_FUNCTIONAL_REVIEW`, implementation revision 2 (reviewed head `aa46d07`), plan revision 5. The candidate is the
`payload/scripts` tree of the commit under test; the base is `d6e6cb07f1c97837dd98a43cb2f3c198dade47dc`. The checklist's
evidence commit (its SHA and blob) is reported by `/prepare-functional-review` and read back by `/review-functional`.

Every flow runs offline, against a scratch repository and the fake `gh`. Nothing runs in the product clone, its `.ai-review/`
or the forge. Flows 15 and 16 need the full environment and are not sandbox flows.

### Setup

1. Run the setup block of `docs/ai-workflow/ACCEPTANCE_FLOOR_COMMIT_PLAN.md` section 5 (the code block from `Setup, once` to
   its closing fence). It defines `$BASE`, `$CAND`, the fake `gh`, `$GH_LOG` and the helpers `mk`, `cpy`, `snap`, `py`, `cli`,
   `refuse`, `crash`. Use them verbatim.
2. Sandbox adaptation: `TMPDIR` and `W43_BIN` are the writable scratch directories the sandbox grants, not the plan's
   `$HOME/.claude/...` paths. Keep `W43_BIN` outside `/tmp`, `/var/tmp`, `/dev/shm` and `$TMPDIR`. If the sandbox's own `gh`
   refusal stand-in is used in place of the fake, flow F14 reads that stand-in's log instead of `$GH_LOG`.
3. Before starting: `git -C <clone> status --porcelain` is empty and `HEAD` is the commit under test.
4. Run Python as `python3 -I`, with no zlib-ng and no Python 3.12 needed for flows F1 to F14.

### Test data

Nothing is seeded in the product clone. Scratch repositories come from `mk <dir> <case>`: `ready` (the item `wi` at
`MILESTONE_COMPLETE`, committed, with a stricter gate policy in the working tree), `plain` (no policy file), `early`
(`IMPLEMENTING`), `afr` (`AWAITING_FUNCTIONAL_REVIEW`), `uncommitted` (`HEAD` at `IMPLEMENTING`, the working file at
`MILESTONE_COMPLETE`), `nostate`, `corrupt`. Each flow starts from a fresh `mk` unless it says otherwise. `cpy` makes the
copies that the base's Python call runs on.

### Flows and expected results

- **F1, the floor is committed.** `mk r ready`; `cpy r r2`; `cli $BASE r`; `py $BASE r2`; `cli $CAND r`.
  Expect: base exit 2 (argparse's "one of the arguments" refusal). `py` on `r2` prints a sha. Candidate exit 0, stdout exactly
  `{"commit": "<sha>", "recovered": false}`. The subject and final paragraph of `git -C r show -s --format=%B HEAD` and of `r2`
  are identical: `chore: record gate policy floor <12>` and `Workflow-Gate-Policy-Floor: <digest>`. The two state files differ
  only in the `recorded_at` line. `git -C r diff-tree --name-only -r HEAD` lists the state file alone; `git -C r status --porcelain`
  shows only the untracked policy file.
- **F2, nothing to commit is a no-op.** On F1's `r`: `snap r > before`; `cli $CAND r`; `snap r > after`. Then `mk r plain`;
  `snap r > b2`; `cli $CAND r`; `snap r > a2`. Expect: both runs exit 0 with `{"commit": null, "recovered": false}`; `diff`
  of before/after and of b2/a2 is empty; no `.ai-review` in the second. `py $BASE` on a copy of `plain` prints `None`. Then
  `mk r ready`; `cli $CAND r`; edit only the `recorded_at` line of the working state file (`grep -c recorded_at` prints 1); `cli $CAND r`.
  Expect: exit 0, `{"commit": null, "recovered": false}`, `HEAD` unmoved.
- **F3, refusals before anything is written.** `mk r early`, `mk q afr`, `mk s uncommitted`. For each, `cpy` to a copy and run
  `py $BASE` there (the base commits: it has no phase or order check). Then `snap`, `cli $CAND <repo>`, `snap`.
  Expect: candidate exit 1 for each, one JSON object with `"error": "FloorCommitPreflightError"`, `commit` null,
  `state_changed` false. `early` and `afr` give code `work_item_not_complete`; `uncommitted` gives `completion_not_committed`.
  Snapshots identical; no `.ai-review`.
- **F4, dirty index refused.** `mk r ready`; `echo x > r/x.md; git -C r add x.md`; `snap r`; `cli $CAND r`; `snap r`.
  Expect: exit 1, `DirtyIndexBeforeStagingError` naming `x.md`, `commit` null, `state_changed` false, snapshots identical.
- **F5, recovery after a stop before the state commit.** `mk r ready`; `crash r state`; `git -C r status --porcelain`; `cpy r r2`;
  `py $CAND r2`; `cli $CAND r`; `cli $CAND r`. Expect: after the stop, ` M` on the state file and no new commit. `py $CAND r2`
  prints `None` and leaves the file dirty (the measured blindness). Candidate: exit 0, `{"commit": "<sha>", "recovered": true}`,
  state file clean, subject and trailer as F1. The second `cli` prints `{"commit": null, "recovered": false}`.
- **F6, stop after staging.** `mk r ready`; `crash r stage`; `git -C r status --porcelain` (expect `M ` staged, no commit);
  `cli $CAND r` (expect `recovered: true` and a commit of the state file alone). Then `mk r ready`; `crash r stage`; add a foreign
  work item to the working state file, serialized with `workflow_state._serialize_state` (the floor stays staged, the foreign
  edit does not); `cli $CAND r`. Expect exit 1, `DirtyIndexBeforeStagingError`, `commit` null. Then
  `git -C r restore --staged docs/ai-workflow/WORKFLOW_STATE.json` and `cli $CAND r`: expect the floor committed with
  `recovered: true`, and the foreign edit left uncommitted.
- **F7, a stop after the floor commit.** `mk r ready`; `crash r validate`; `git -C r log --oneline -2`; `cli $CAND r`.
  Expect: the floor commit exists after the stop; the candidate exits 0 with `{"commit": null, "recovered": false}` and `HEAD` unmoved.
- **F8, unrelated staged file during recovery.** `mk r ready`; `crash r state`; `echo x > r/x.md; git -C r add x.md`; `snap r`;
  `cli $CAND r`; `snap r`. Expect: exit 1, `DirtyIndexBeforeStagingError`, `commit` null, `state_changed` false (the floor was
  already in the file), floor not committed, snapshots identical. Then `git -C r rm -q --cached x.md; command rm -f r/x.md`
  and `cli $CAND r` commits the floor with `recovered: true`.
- **F9, validator refusal after the commit landed.** `mk r ready`; `refuse r`; `git -C r log --oneline -2`; `cli $CAND r`.
  Expect: `refuse` exits 1 with one JSON object: `"error": "MalformedGatePolicyFloorCommitError"`, `"commit"` equal to
  `git -C r rev-parse HEAD`, `"state_changed": true`; exactly one commit added. The following `cli` prints
  `{"commit": null, ...}`.
- **F10, bad arguments and bad state.** `cli $CAND r unknown`; `cli $CAND r ""`; `mk n nostate`, then `py $BASE` on a copy and
  `cli $CAND n`; `mk c corrupt`, then `cli $CAND c`; write `[]`, then `{}`, into the state file of a `ready` repository and run
  `cli $CAND` on each; run `cli $CAND` from a directory outside any repository. Expect: exit 1 each, one JSON object, with the
  classes `UnknownWorkItem`, `UnknownWorkItem`, `StateMissing`, `CorruptJsonError`, `StateMalformed`, `StateMalformed`, and a
  class name (no traceback) outside Git; `commit` null, `state_changed` false, trees unchanged. The base on `nostate` creates a
  state file and commits it.
- **F11, the five old flags are unchanged.** `mk r ready`. For each of `--finding-dispositions wi`,
  `--plan-review-publication-status wi`, `--acceptance-gate wi`, `--satisfy-acceptance wi` and `--write-findings-record wi`, run
  base and candidate and compare stdout and exit. (For `--plan-review-publication-status`, which prints nothing and exits 1 with a
  traceback on this item, compare the exit only.) Then run `--commit-gate-policy-floor wi --acceptance-gate wi` and
  `--commit-gate-policy-floor wi --write-findings-record wi` with the candidate. Expect: the five old flags match exactly; both
  combined invocations exit 2 with "not allowed with argument".
- **F12, the sibling proves before it stages.** Build each case in its own `mk` repository, named as given, then run
  `snap <repo>`, `cli $CAND <repo>`, `snap <repo>`, `git -C <repo> diff --cached --name-only`.
  - (a) `r`: floor committed; the working floor's `digest` set to 64 zeros.
  - (b) `b`: `mk b plain`; no floor in `HEAD`; the working file holds a floor record with a malformed `policy`.
  - (c) `c`: a malformed floor commit (provenance fails); then the working floor set to the default policy.
  - (d) `d`: floor committed; the working floor's `digest` key deleted.
  - (e) `e`: as (a), plus `echo x > x.md; git add x.md`.
  - (f) `f`: malformed floor commit; the working floor equal to `HEAD`'s.
  - (i) `i`: as (c), plus `x.md` staged.
  - (l) `l`: `mk l plain`; no floor in `HEAD`, no policy file, `x.md` staged.
  - (m) `m`: committed floor with only `recorded_at` edited; `x.md` staged.
  Expect: exit 1 for (a) to (f) and (i); exit 0 with `{"commit": null, "recovered": false}` for (l) and (m), with `x.md` still
  staged. `FloorRecoveryRefusedError` with `floor_record_invalid` for (a), (b), (d), (e), and `floor_provenance_failed` for (c),
  (f), (i). In (e) the answer is `FloorRecoveryRefusedError`, not `DirtyIndexBeforeStagingError`. Every case: `commit` null,
  `state_changed` false, snapshots identical, no `KeyError`. Contrast: the base's Python call on a copy of (a) answers `None`,
  where the old design would have committed.
- **F13, the command text.** `grep -n -e '--commit-gate-policy-floor' -e 'commit_gate_policy_floor' payload/.claude/commands/satisfy-gate.md`.
  Then in `mk r early`, `cpy "$CAND" r/scripts`, run the documented line verbatim from `r` with the id substituted.
  Expect: the flag appears in "Plain commands first" and in the acceptance stage's step 5, after the findings-record paragraph.
  `commit_gate_policy_floor` stays named for the plan and implementation stages. The documented line has no `python3 -I`, runs
  without `ModuleNotFoundError`, and refuses with `work_item_not_complete`. `grep -c 'one Python call'` on that file prints 0 for
  the acceptance stage's text, and `grep -n 'for the floor, one Python call\|is the one Python call that remains'` finds nothing.
- **F14, the function is untouched and nothing reached the forge.** `cat "$GH_LOG"`; then
  `python3 -I -c` printing `hashlib.sha256(inspect.getsource(ws.commit_gate_policy_floor).encode()).hexdigest()` with `$BASE`
  and with `$CAND`. Expect: the log is empty; the two digests are equal.
- **F15, CP1's scope (offline).** `git diff d6e6cb07f1c97837dd98a43cb2f3c198dade47dc d14ea5b --stat -- payload docs manifest.json`.
  Expect 11 files: `workflow_state.py`, `workflow_gate_policy_test.py`, `satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`,
  `docs/ACTIVE_MILESTONE.md`, the plan, the registry, the mapping, the artifacts declaration and the state. No `workflow_protocol.py`, no manifest.
- **F16, full environment only (not a sandbox flow).** The nine payload suites from a staged fixture, `tools/docs` and its checker,
  `check-manager-block` with `--manager-releases`, and the `tools/release` tests with the zlib-ng interpreter. Expect: all pass;
  the protocol and matrix suites report their deliberate skips, and `tools/release` fails rather than skips. Then
  `git diff d6e6cb07f1c97837dd98a43cb2f3c198dade47dc --stat` at CP2 (`67943b3`) matches the list in the plan's section 5:
  `manifest.json`, `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`,
  `docs/exit-codes.md`, `tools/release/release_test.py`. The protocol stays `1.5`. If this cannot run, record it as not run.

### Known limitations and out of scope

- The forge path is never exercised. `gh` is a stand-in that only proves no forge call was made; no pull request, no real
  GitHub, no real `claude`, `codex` or `ssh`.
- F7 is the documented residual: after a stop that follows the floor commit, the validator is not run again.
- Optional findings `LOCAL-IMPL-R1-004` and `-005` (command wording in `satisfy-gate.md`) are not applied; they change a
  shipped record and need their own wording review. The functional review may raise them.
- F16 needs the full environment. It is not run in the sandbox.
- The `recorded_at` value differs between the two runs of F1, since the flag stamps the real clock. This is expected.
- The flag does not itself record acceptance. Acceptance is `/accept-milestone` only.

## Next action

W43 is accepted by policy. Roadmap row 38 is Done; no further incomplete item follows it in `docs/ROADMAP.md`'s table, and the
release (Workflow 2.29.0) follows the merge of PR #164.
