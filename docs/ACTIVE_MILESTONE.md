# Active Milestone

## Milestone

**In progress.** W41: `acceptance-completion-command` (`process`, governing version `2.2`), branch
`milestone/acceptance-completion-command`, roadmap row 36 (RodrigoFAbreu/workflow#148, the second half). The plan is
`docs/ai-workflow/ACCEPTANCE_COMPLETION_COMMAND_PLAN.md` (revision 3, approved by gate policy). The previous milestone,
W40 `acceptance-plain-command` (Workflow 2.26.0), is complete.

## Goal

Workflow 2.27.0 (a `feat:` minor): `python3 scripts/workflow_state.py --satisfy-acceptance <id>` makes the stage's step 2a
phase and registry check, then runs `satisfy_acceptance_gate` in one `state_transaction` and prints `{record, trailer}`.
Gate semantics do not change; the protocol stays 1.5. The findings record and the floor commit are row 37.

## Checkpoints

- **CP1 (the completion flag, its tests, the command text and the pages): complete.** `_acceptance_reachability_blocker`
  is shared by the report and the command; `AcceptancePreflightError`, `_satisfy_acceptance_cli` and the fourth flag in
  the exclusive group are in `payload/scripts/workflow_state.py`; `TestSatisfyAcceptanceCommand` (S1 to S8, 13 tests)
  is in `payload/scripts/workflow_gate_policy_test.py` (suite 346 to 359 tests, all passing); `satisfy-gate.md` and
  `docs/exit-codes.md` name the flag. Verified in the disposable clone of D-Staging.
- **CP2 (release 2.27.0): complete.** `WORKFLOW_RELEASE` 2.27.0 (protocol stays 1.5), `manifest.json` (version, six records' `sha256`/`size`/`rationale`, posture, `workflow_gate_policy_test.py` 359), `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`, and a 2.27.0 class in `tools/release/release_test.py`. Verified in a scratch clone: stock `stage-conformance` and the nine suites pass, `build` succeeds, `check-manager-block`, `tools/docs`, `check_docs.py` and `tools/release` (313 tests) pass; `workflow-manager verify .` clean.

- **Self-review (all checkpoints complete): two fixes.** Mutations m1 to m16 had no durable record, so they were run on a scratch fixture: every one fails a named test except **m9, which survived** (S2's outside-Git case called the CLI function directly, past the dispatch). S5 now runs the real CLI outside Git, and m9 fails it. The plan also names S1 for m1, but S1 cannot fail there (its six states hold no phase refusal); S2 is the proof. `--help` no longer says "Writes nothing" without saying of which option. The results are in the implementation bundle's `TEST_RESULTS.md`.

## Next action

Manual functional review of `acceptance-completion-command` (gate `AWAITING_FUNCTIONAL_REVIEW`). Run the checklist below
and place any findings at `.ai-review/acceptance-completion-command/feedback/FUNCTIONAL_REVIEW.md`. Once testing is clean,
`/accept-milestone` is the only acceptance command. Both checkpoints are `COMPLETE`, so nothing is outstanding.

## Functional review checklist

**Reviewed content:** implementation revision 3, reviewed implementation head `65776dd`, base `b2db092`, plan revision 3.
The checklist's evidence commit SHA and blob are reported by `/prepare-functional-review` (its trailer
`Workflow-Functional-Checklist: acceptance-completion-command/3/<blob>`); the blob is `git rev-parse HEAD:docs/ACTIVE_MILESTONE.md`.

**What is under test:** `python3 payload/scripts/workflow_state.py --satisfy-acceptance <id>` (the release source; the
repository's installed `scripts/` copy has no such flag until 2.27.0 is installed). The gate semantics are unchanged; the
command adds the stage's phase and registry pre-flight, runs `satisfy_acceptance_gate` in one `state_transaction`, and
prints `{record, trailer}`.

**Constraints:** every flow runs offline in scratch repositories with a fake `gh`. Nothing runs against this repository,
its `.ai-review/`, or GitHub, and no flow writes inside the product clone.

### 1. Setup

1. **Automated state is current.** No file under `payload/`, `scripts/` or `manifest.json` changed after the
   revision-3 run in `.ai-review/acceptance-completion-command/current/TEST_RESULTS.md`; since `21b6d29` the only
   change is one line of `tools/release/release_test.py`. Rerun the suites (`docs/RELEASING.md`, "Verification
   commands") only if you edit a payload file.
2. **Scratch and fake `gh`** (the fake lives outside `/tmp`, `/var/tmp`, `/dev/shm` and `$TMPDIR`, mode 0755):

```sh
export CAND="$(git rev-parse --show-toplevel)/payload/scripts"   # read only
export W41="$(mktemp -d)"                                        # scratch root
export W41_BIN="$HOME/w41-bin"                                   # fake gh
mkdir -p "$W41_BIN" && cat > "$W41_BIN/gh" <<'EOF'
#!/bin/sh
echo "gh called: $*" >> "$GH_LOG"
case "$GH_MODE" in
  fail) echo "boom" >&2; exit 1 ;;
  empty) echo '[]'; exit 0 ;;
  red) printf '[{"number":7,"url":"https://github.com/o/r/pull/7","state":"OPEN","headRefOid":"%s","reviewDecision":"CHANGES_REQUESTED","reviews":[{"id":"R1","state":"CHANGES_REQUESTED","body":"please fix x","commit":{"oid":"%s"}}],"statusCheckRollup":[{"name":"ci","status":"COMPLETED","conclusion":"SUCCESS"}]}]\n' "$8" "$8"; exit 0 ;;
esac
printf '[{"number":7,"url":"https://github.com/o/r/pull/7","state":"OPEN","headRefOid":"%s","reviewDecision":"","reviews":[],"statusCheckRollup":[{"name":"ci","status":"COMPLETED","conclusion":"SUCCESS"}]}]\n' "$8"
EOF
chmod 755 "$W41_BIN/gh"
export GH_LOG="$W41/gh.log"; : > "$GH_LOG"
```

3. **Fixture.** Save this as `$W41/fixture.py`. It builds a scratch repository on the test suite's `AcceptanceRepo`,
   with the phase given as an argument:

```python
import shutil, sys, pathlib
sys.path.insert(0, sys.argv[1])
import workflow_gate_policy_test as t
phase, dest = sys.argv[2], pathlib.Path(sys.argv[3])
with t.AcceptanceRepo() as ev:
    ev.set_state(phase=phase)
    if phase == "AWAITING_FUNCTIONAL_REVIEW":
        ev.ready()
    shutil.copytree(ev.root, dest, symlinks=True)
print("built", dest, phase)
```

   Then: `cd "$W41" && python3 -I fixture.py "$CAND" AWAITING_FUNCTIONAL_REVIEW ready`,
   `python3 -I fixture.py "$CAND" IMPLEMENTING early` and `python3 -I fixture.py "$CAND" MILESTONE_COMPLETE term`.
   **Every run mutates its repository**, so each flow starts from a fresh `cp -a "$W41/ready" "$W41/<case>"`.

4. **Helpers** (shell functions for the flows):

```sh
run()  { (cd "$W41/$1" && shift && PATH="$W41_BIN:$PATH" python3 "$CAND/workflow_state.py" "$@"); }
snap() { (cd "$W41/$1" && git rev-parse HEAD && find . \( -path ./.git -o -path ./.ai-review/runtime \) -prune -o -type f -print0 | sort -z | xargs -0 sha256sum); }
```

   Take `snap <case> > before` before a run and `snap <case> > after` after it, then `diff before after`. The `.ai-review/runtime/`
   lock is excluded on purpose. The `gh` line count is `wc -l < "$GH_LOG"`.

### 2. Flows

Expected results marked **(smoke-checked)** were observed on the scratch repositories while preparing this checklist.
The others are the plan's section 5 expectations and still need your run.

| # | Run | Expect |
| --- | --- | --- |
| F1 | `run ready --satisfy-acceptance wi` | exit 0 **(smoke-checked: exit 0, one `gh pr list` call, the record printed)**. Stdout is only `{record, trailer}`, `trailer` is `policy:` plus the first 12 hex of `record.policy_digest`. The item is `MILESTONE_COMPLETE`. The diff shows only `docs/ai-workflow/WORKFLOW_STATE.json` changed, and `HEAD` is unchanged. |
| F2 | `run early --satisfy-acceptance wi` | exit 1: `{"code": "phase_not_reachable", "error": "AcceptancePreflightError", "message": "the phase is IMPLEMENTING; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW", "state_changed": false}` **(smoke-checked)**. Snapshot unchanged, zero `gh` calls. |
| F3 | `run term --satisfy-acceptance wi` | exit 1: `work_item_terminal`, `state_changed` false **(smoke-checked)**. Snapshot unchanged. |
| F4 | `ready` with `badregistry`: delete the registry file the state names | exit 1: `registry_unresolvable` with the registry error text, `state_changed` false, snapshot unchanged, zero `gh` calls. *(plan; not smoke-checked)* |
| F5 | `ready` with `GH_MODE=fail` exported | exit 1: `ForgeUnavailableError`, `code` `forge_unavailable`, `state_changed` false, snapshot unchanged. *(plan)* |
| F6 | `ready` with `GH_MODE=empty` exported | exit 1: the fact is `state: none`, the gate refuses as `pr_fact_current` unmet, `state_changed` true. *(plan)* |
| F7 | `ready` with `PATH` holding only a symlink to `git` (`mkdir "$W41/nogh" && ln -s "$(command -v git)" "$W41/nogh/git"`) and the absolute python3 | exit 1: `forge_unavailable`, snapshot unchanged. *(plan)* |
| F8 | `ready` with a copy of the fake `gh` in `$W41/gh-tmp` first on `PATH` | exit 1: `forge_undecidable` naming the path inside the temporary directory, snapshot unchanged. *(plan)* |
| F9 | `--satisfy-acceptance nope`; `--satisfy-acceptance ""`; state file deleted; state file `{` ; state file `[]` | exit 1 each, one JSON object: `UnknownWorkItem` (`nope`), `UnknownWorkItem` (empty id, not "absent"), `StateMissing`, `CorruptJsonError`, `StateMalformed` **(all five smoke-checked, error classes and messages as named; exit codes not captured, expect 1)**. Snapshot unchanged, zero `gh` calls. The state file `{}` (`StateMalformed`) is the plan's case, not smoke-checked. |
| F10 | Run outside any Git repository | one JSON object with `"error": "CalledProcessError"` and `state_changed` false, no traceback **(smoke-checked)**. |
| F11 | `run ready --satisfy-acceptance wi --acceptance-gate wi`, and the same with `--finding-dispositions` or `--plan-review-publication-status` | exit 2, "not allowed with argument". The three existing flags print byte-identical output and exit codes to the base (`git archive b2db092 payload/scripts` extracted to `$W41/base`). *(plan)* |
| F12 | `grep -n -e '--satisfy-acceptance' -e '--acceptance-gate' -e 'satisfy_acceptance_gate' payload/.claude/commands/satisfy-gate.md`, then run the documented `python3 scripts/workflow_state.py --satisfy-acceptance <id>` line from the candidate's `scripts/` against the `early` repository | the flag precedes the first `satisfy_acceptance_gate`; the step-0 `preflight-accept` sentence precedes the flag; no `python3 -I` on the line; it runs (no `ModuleNotFoundError`) and refuses with `phase_not_reachable`. *(plan)* |
| F13 | `git diff b2db092 --stat -- payload docs` | the changed files are the flag's, the test file, `satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `manifest.json`, the plan, registry, mapping and artifact declarations and the state. No `workflow_protocol.py` change beyond the release constant. *(plan)* |

The gate-level cases (no functional flow, undispositioned findings, a human approval, a standing `CHANGES_REQUESTED`) need
fixture variants beyond this checklist. The automated `TestSatisfyAcceptanceCommand` class (13 tests, S1 to S8 in
`payload/scripts/workflow_gate_policy_test.py`) covers them in-process against the Python path: exact parity, byte-equal state
on refusals, and the output contract. Run it as the automated check for those cases.

### 3. Known limitations and out of scope

- **The Python path still has the phase gap.** `satisfy_acceptance_gate` (and so `complete_work_item`) completes from
  `IMPLEMENTING` and from `MILESTONE_COMPLETE`. Only the new flag refuses those phases. Closing the gap in the library is a
  follow-up on roadmap row 37, and it is not a defect of this milestone.
- **Not in this milestone:** the findings record and the floor commit (row 37, so the worker still calls those in Python),
  and the optional `next-action` evidence line (declined; it stays open on RodrigoFAbreu/workflow#148).
- **No real forge.** The pull-request fact comes from the fake `gh`. A real `gh` on a real repository is not exercised here.
- **Release and environment checks are not part of this offline pass:** the nine suites from a staged fixture, the
  `tools/release` tests with the zlib-ng interpreter, `check-manager-block`, and `workflow-manager verify .`. The revision-3
  record in `TEST_RESULTS.md` covers them.

### 4. Reporting and next steps

- Record each flow as pass, fail or not-run, with the output that decided it.
- Findings go to `.ai-review/acceptance-completion-command/feedback/FUNCTIONAL_REVIEW.md`, the path that
  `python3 scripts/workflow_fingerprint.py --resolve-feedback-path acceptance-completion-command` reports.
  `/apply-functional-review` then routes each one: the bounded branch for a same-scope fix, or the broad branch (a
  `acceptance-completion-command-remediation-<n>` child work item) for new or wider scope.
- When testing is clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint in this
  item's registry to be `COMPLETE`, which holds now. No command records acceptance of a partial round.
