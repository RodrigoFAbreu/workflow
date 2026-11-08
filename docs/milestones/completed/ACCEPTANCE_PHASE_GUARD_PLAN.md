# W44: Workflow 2.29.1 — the acceptance phase guard, in the library and inside the lock (Revision 2)

- **Work item:** `acceptance-phase-guard` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-07: RodrigoFAbreu/workflow#158 item 1; `docs/ROADMAP.md` row 39
  (`Current` with this plan, `Done` at acceptance). Row 38's closing sentence announced it
  (`docs/milestones/completed/ACCEPTANCE_FLOOR_COMMIT_PLAN.md`).
- **Branch:** `milestone/acceptance-phase-guard`
- **Base commit:** `bee00609379aa6ab29a7f9076987bb5bfb7dd5de` (main after #166: release source and own installation are 2.29.0; automatic gates,
  default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 2 (amendment of the approved revision; reason in the revision history below). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair. Items 2 and 3 of #158 (wording) are out of scope.

### Revision history

- **Revision 1 -> 2 (round 1 of the manual external review):** I1 and the optional P2 case accepted (D-Tests).
- **Amendment (revision 2, from `IMPLEMENTING`):** CP1 edits `payload/.claude/commands/accept-milestone.md`, whose SHA-256 is pinned in `_GOLDEN_COMMAND_FILE_SHA256` (`TestGoldenCommandFileHashes`) in
  `payload/scripts/workflow_integration_test.py`; the plan listed four payload files and missed it (the item 500f68b updated the same line). Added: that file in CP1/CP2, the manifest record, and the scope statements and flows (new flow 14). The design and CP1's content do not change.

## 0. Phase 1: the investigation (before any design)

Measured on scratch repositories built by hand with the base's `payload/scripts` staged by `release.py stage-conformance` (probes kept outside the repository, not shipped).

### 0a. What `complete_work_item` completes from today

| | |
| --- | --- |
| Refusals it has | an incomplete child (`IncompleteChildWorkItemError`), an own registry that is not terminal or not resolvable (`IncompleteOwnCheckpointsError`, `RegistryCoverageError`), an unsatisfied completion obligation, an undispositioned finding. **No refusal on the phase** |
| Measured (item with a terminal registry, each of the 20 phases of `KNOWN_PHASES`) | **it completes from all twenty**, `PLANNING` and `LEGACY_READY` included, and again from `MILESTONE_COMPLETE` (it rewrites `state_revision`, `last_transition` and the obligation record). Only `AWAITING_FUNCTIONAL_REVIEW` and `AWAITING_USER_ACCEPTANCE` are reachable by the documented gate (`milestone_complete_gate_reachable`) |
| Callers in code | one: `apply_acceptance_satisfaction`, inside the mutator of `satisfy_acceptance_gate`. `/accept-milestone` step 2a calls it on the re-read state inside its transaction; `workflow_protocol.py` never calls it, so the Controller never does |

### 0b. Which phases any caller, test or documented flow depends on

All nine suites ran on the base with a probe that logs the phase at each call, then again with the candidate prototype (the library guard, the in-lock stage guard).

| Phase at the call | Calls in the nine suites | Depends on completing? |
| --- | --- | --- |
| `AWAITING_FUNCTIONAL_REVIEW` | 84 (the matrix, protocol, gate-policy and state suites) | yes, the reachable phase: unchanged |
| `AWAITING_USER_ACCEPTANCE` | 20 (`workflow_state_test.py`, the obligations suite; legacy-governed fixtures) | yes, the other reachable phase: unchanged |
| `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` | 18, all in `workflow_gate_policy_test.py` | **a fixture artifact**: `EvidenceRepo` builds its item at that phase and `AcceptanceRepo` never moves it. `test_a_re_acceptance_overwrites_the_record` moves it to `AWAITING_FUNCTIONAL_REVIEW` by hand before the second completion, as the reopen flow does |
| `IMPLEMENTING` | 3, all `workflow_state_test.py`, all expecting a refusal | no: they expect `IncompleteOwnCheckpointsError` with `Finish it with /milestone-implement` (`test_message_is_phase_and_version_aware`), or any refusal (an item resumed to `IMPLEMENTING`) |
| `MILESTONE_COMPLETE` | 0 | no. The findings record and the floor commit (`--write-findings-record`, `--commit-gate-policy-floor`) run after the completion and **never call it** (the AST of the base has one caller, 0a). `--satisfy-acceptance` already refuses it (`work_item_terminal`) |

Result of the prototype: the other eight suites pass with `workflow_integration_test.py` changed only in the golden hash of `accept-milestone.md` (the matrix suite included, 453 tests; without that line `TestGoldenCommandFileHashes` fails on the edited command); `workflow_gate_policy_test.py` fails 15 tests, all explained: 14 complete from the fixture's phase and
`test_s8_the_report_and_the_command_call_one_function` pins the source of the CLI. The fixture's phase set to `AWAITING_FUNCTIONAL_REVIEW` (one line) fixes 12; two more assert the old phase after a refusal; with `test_s8` that is three test edits. **No shipped command text, protocol operation or document flow depends on completing from another phase**:
`accept-milestone.md` step 2a and `satisfy-gate.md` both refuse before the call.

### 0c. What the refusal looks like

The report and the flag already have the vocabulary: `AcceptancePreflightError` with `code` `work_item_terminal`, `registry_unresolvable` or `phase_not_reachable`, printed as
`{"code", "error", "message", "state_changed"}` with exit 1 (`_satisfy_acceptance_cli`). The library has no such class. Where the guard sits matters because two refusals already name the phase:
`IncompleteOwnCheckpointsError`'s message branches on `IMPLEMENTING` (`_incomplete_own_checkpoints_route`) and two tests pin it, so a library guard placed before the registry check would change a released error class for an item that is still being implemented.

### 0d. What the race can do (deterministic, no sleep)

The flag takes `now` as a test seam; the base calls `now()` after the stage's phase guard and before the lock. A seam that writes the state file lands a writer exactly in that gap. On the base,
item at `AWAITING_FUNCTIONAL_REVIEW`, with the full gate fixture (`AcceptanceRepo`): the racing writer sets `IMPLEMENTING` → **exit 0, phase `MILESTONE_COMPLETE`, `acceptance_satisfaction` recorded**; sets
`MILESTONE_COMPLETE` → exit 0, completed again (record overwritten). On the hand-built item of §5 (no technical approval) the same seam makes the base fail later with `forge_undecidable` and
`state_changed: true`: it got past the guard and only the missing anchor stopped it. The library alone is exposed the same way: a `state_transaction` whose mutator is `complete_work_item` completes from whatever phase the re-read state holds (flow 3).

### 0e. Does closing it change a released behaviour? Patch or minor

Yes, and it is said loudly: **a direct Python caller of `complete_work_item` (or of `satisfy_acceptance_gate`) from any phase but the two acceptance phases gets an error where 2.29.0 completed the item.** Affected, by measurement: nobody
in the shipped commands, the protocol, the Controller (it launches commands and never calls the function), or the nine suites except the fixture above. Unaffected: the flag's JSON for every refusal that exists today (same class, same codes, same
`state_changed`), the acceptance stage's order, the record and the trailer. Two observable differences: a phase refusal of the flag now takes the state lock (it creates `.ai-review/runtime/WORKFLOW_STATE.lock` on first use, which the old early refusal did not), and a refusal
caused by a writer that landed in the gap reports `state_changed: true` (the file did change, by that writer; the command wrote nothing, and the command text already says that any other `true` means another writer). **Decision: a `fix:` patch, 2.29.1**
(the library is brought to the contract `accept-milestone.md` step 2a and `MILESTONE_WORKFLOW.md` already state through `milestone_complete_gate_reachable`: completion only from the gate's phases; no document, flow or test relied on the opposite). The owner may choose a minor instead (§3). **Protocol: stays 1.5. Controller: no change.**

## 1. Goal, release, scope

`complete_work_item` refuses unless the item is at `AWAITING_FUNCTIONAL_REVIEW` or `AWAITING_USER_ACCEPTANCE`, and the acceptance stage's phase and registry check moves from before the lock to the first statement of the mutator, so a writer
landing before the lock can no longer make the library complete from a phase it must refuse. One mechanism (a phase guard, in two places that share one rule). **Out of scope:** #158 items 2 and 3, the optional `next-action` evidence line, any change to the gate's requirements,
the plan-stage and implementation-stage floors, the Controller.

## 2. Design decisions

### D-Library: the guard in `complete_work_item`

New `CompletionPhaseNotReachableError(Exception)` carrying `code`. Checked **after** the child check and the own-registry check and **before** the obligations and the dispositions: `MILESTONE_COMPLETE` → `work_item_terminal`; any phase for which
`milestone_complete_gate_reachable(phase=..., is_terminal=True)` is false → `phase_not_reachable`, message `the phase is <phase>; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW` (the report's wording). The order keeps every released refusal for
an item whose registry is not terminal (0c) and changes the outcome only where the library used to complete. The function stays pure (it returns a new state or raises), so a refusal writes nothing, and it runs inside the caller's critical section.

### D-Lock: the stage's guard inside the mutator

`satisfy_acceptance_gate`'s mutator makes `_acceptance_reachability_blocker` its first statement (before the anchor, the query, the stored fact and the reopening) and raises `AcceptancePreflightError(code, detail)`; the mutator runs on the state re-read under the lock, so the
phase it judges is the phase it completes from. `_satisfy_acceptance_cli` drops its own call (one home for the rule; the report, `acceptance_gate_report`, keeps calling the same function). The Python path of the command text gets the same guard, which closes the "library
does not" sentence. D-Library stays as the defence for every other caller (the human path, direct calls).

### D-Refusal: shapes

The flag's refusals keep their JSON byte for byte (`AcceptancePreflightError`, the same three codes, `state_changed` from the digest taken after the context and before the transaction). The library's error is a different class with the same codes, so a caller can branch on `code`
alone; on the human path it surfaces as the exception, and `accept-milestone.md` step 2a lists it among the stops. No JSON is added for the library (it has none).

### D-Order: the refusal order, in one place

Flag/stage: unknown item, state missing or malformed (before the lock, unchanged) → in the lock: `registry_unresolvable` / `work_item_terminal` / `phase_not_reachable` (the blocker's order, unchanged) → anchor, query, evaluation, `complete_work_item`. Library: incomplete child → own registry →
**phase** → obligations → dispositions. Both orders are pinned by tests (P2, P4).

### D-Tests (P1 to P6 in `payload/scripts/workflow_gate_policy_test.py`, class `TestCompletionPhaseGuard`, which runs from the stock staged fixture; P7 in `tools/release/release_test.py`; written and run red first)

- **P1 per phase:** every phase of `KNOWN_PHASES` on the `AcceptanceRepo` item: the two acceptance phases complete, `MILESTONE_COMPLETE` is `work_item_terminal`, the other seventeen `phase_not_reachable`; the input state is deep-equal afterwards (no-write proof, per refusal).
- **P2 order:** `IMPLEMENTING` with an outstanding checkpoint is still `IncompleteOwnCheckpointsError`; `IMPLEMENTING` with a terminal registry is the new error; `MILESTONE_COMPLETE` with an incomplete child is `IncompleteChildWorkItemError`; **`IMPLEMENTING` with a terminal registry and an unsatisfied completion obligation is `CompletionPhaseNotReachableError`, not the obligation error** (this case alone tells the guard before the obligations from the guard after them, m5).
- **P3 library race:** the snapshot is read at `AWAITING_FUNCTIONAL_REVIEW`, a writer sets `IMPLEMENTING` (then `MILESTONE_COMPLETE`), then `state_transaction(root, complete)`: refused, and the file is byte-equal to the writer's.
- **P4 stage race:** the flag with a `now` seam that writes the phase (both phases): exit 1, `AcceptancePreflightError`, the code, `state_changed: true`, no query, no `acceptance_satisfaction`, file byte-equal to the writer's. **In-lock proof:** a spy on `_acceptance_reachability_blocker` tries `fcntl.flock(LOCK_EX|LOCK_NB)` on the lock file and records that it is held. Python path:
  `satisfy_acceptance_gate` from `IMPLEMENTING` raises `AcceptancePreflightError`, no query, file unchanged.
- **P5 unchanged shapes:** the three refusals of `test_s2_a_refusal_before_the_call_writes_nothing_and_never_queries` keep `(1, code, False, [])`; the only new file is the lock; the real-resolver tests (s6) and the exclusive group (s5) are untouched.
- **P6 texts (shipped documents only):** `satisfy-gate.md` no longer says `the library does not` and says the check runs inside the transaction; `accept-milestone.md` names `CompletionPhaseNotReachableError`. Both are manifest artifacts, so the stock `stage-conformance` fixture holds them. `docs/exit-codes.md` is a maintainer page with no manifest record: the fixture does not materialize it (`tools/release/package.py`, `stage_conformance`), so no suite of the shipped payload reads it.
- **P7 (repository-only):** the 2.29.1 class of `tools/release/release_test.py` (CP2), which already reads `docs/exit-codes.md` for its "Last checked with" line, also asserts that the refusal row says the check is made inside the state lock. Until CP2 the wording is verified at CP1 by the repository grep named in its verification, run in the disposable clone; no maintainer document is added to the installed release and the assertion is not skipped.
- **Existing tests edited (three, named):** `AcceptanceRepo.__enter__` sets `AWAITING_FUNCTIONAL_REVIEW` (the fixture's one line); the two assertions of the old phase after a refusal; `test_s8` asserts the mutator and the report call `_acceptance_reachability_blocker` and the CLI does not.
- **Failure-only mutations** (each run on a scratch copy; the named test fails and no other): m1 the library guard removed → P1; m2 `IMPLEMENTING` added to the reachable set → P1; m3 `MILESTONE_COMPLETE` given `phase_not_reachable` → P1; m4 guard before the registry check → P2; m5 guard after the obligations → P2;
  m6 the mutator guard removed and the CLI's outside call restored → P4; m7 the mutator guard after the forge query → P4 (a query is made); m8 the CLI's `state_changed` taken after the transaction instead of before → P4/P5; m9 the code of the library's terminal refusal swapped → P1.

### D-Command and D-Docs

`satisfy-gate.md`: the paragraph after the `--satisfy-acceptance` block says the phase and registry check is the transaction's first act, inside the lock, before anything is queried; that the library refuses the same phases; that such a refusal takes the lock; and keeps the `state_changed` guidance. `accept-milestone.md`
step 2a: one stop, `CompletionPhaseNotReachableError`, no write. `docs/exit-codes.md`: the refusal row says "inside the state lock". `docs/ROADMAP.md`: row 39 narrowed to the measurements and `Done` at acceptance. No milestone id in any `docs/*.md` page but the roadmap.

### D-Release

2.29.1, the procedure of `docs/milestones/completed/ACCEPTANCE_FLOOR_COMMIT_PLAN.md` (D-Release) with these differences: `manifest.json` `workflow_version` and the changed records (`workflow_state.py`, `workflow_gate_policy_test.py`, `workflow_integration_test.py` (digest only: the hash line keeps the file's size, and its test count 15 and `conformance.suites` entry do not move), `satisfy-gate.md`, `accept-milestone.md`, `workflow_protocol.py`, its test,
`ORCHESTRATION_PROTOCOL.md`) take `sha256` and `size`; `conformance.suites` moves for `workflow_gate_policy_test.py` only (the integration suite's count is unchanged); `WORKFLOW_RELEASE` becomes 2.29.1 with its pinned assertions; `tools/release/release_test.py` gets a 2.29.1 class and the 2.29.0 class gives up the current-release pins;
`docs/release-history.md` row (a patch: the way back to 2.29.0 restores completion from any phase and the check before the lock; no state to undo); the protocol document's release list and one sentence that the protocol stays 1.5 and no operation changed. The Manager block's posture is rewritten with the downgrade guidance carried
over sentence for sentence, the closing sentence "The release tooling and the maintainer documents are not part of the installed release." kept (§3), and each record's `rationale` carries `acceptance-phase-guard (workflow-2.29.1)`.

### D-Staging

CP1 changes shipped files whose manifest records move at CP2, so it verifies in a disposable clone under `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w44-tmp` (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging, and the
count handling of the lstat-errors plan): recompute `sha256` and `size` of the changed records (`workflow_integration_test.py` included), measure `conformance.suites` (only the gate-policy count moves), commit in the clone, then run the "Verification commands" of `docs/RELEASING.md`; the `tools/release` tests use
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`. **The one expected failure at CP1:** the 2.29.0 class pins the gate-policy count; it is named at implementation and released in CP2. The new tests run again under the
Manager's orphan rule (reaper).

## 3. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Reversible choices: **patch or minor** (0e: patch, as no document or flow relied on the opposite; a minor changes nothing else in the plan); **the guard after the registry check** (0c, to keep two pinned messages; the owner may
prefer it first, which changes `IncompleteOwnCheckpointsError` for an item still implementing); **the stage keeps no early check outside the lock** (D-Lock; the cost is that a phase refusal takes the lock and creates the lock file once); **`state_changed: true` on a race refusal**
(D-Refusal; the alternative is a digest taken inside the lock, which needs a hook in `satisfy_acceptance_gate`, a second mechanism); **the 2.29.1 posture keeps the closing sentence**, which settles #158 item 3 for this release only.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The phase guard in the library and inside the lock, tests, command text and pages | - | 3 | 1 |
| CP2 | Release 2.29.1 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The phase guard in the library and inside the lock, tests, command text and pages

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py`, `payload/scripts/workflow_integration_test.py`, `payload/.claude/commands/satisfy-gate.md`, `payload/.claude/commands/accept-milestone.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): P1 to P6 written and run red against the unedited tree; mutations m1 to m9 each fail the named test on a scratch copy and the results are recorded.
- **The change** (D-Library, D-Lock, D-Refusal, D-Order): `CompletionPhaseNotReachableError`, the guard in `complete_work_item`, the first statement of the mutator, the removal of the CLI's outside call; nothing else in the library. The three named existing tests are the only edits to existing tests in `workflow_gate_policy_test.py`; `workflow_integration_test.py` gets one changed line: the `accept-milestone.md` value of `_GOLDEN_COMMAND_FILE_SHA256` (the new SHA-256 of the shipped file); no comment line is added, so the diff of that file is exactly one line.
- **The command text and the pages** (D-Command and D-Docs). `check_docs.py` stays clean.
- **No other mechanism:** `git diff bee0060 --stat -- payload` lists `workflow_state.py`, `workflow_gate_policy_test.py`, `workflow_integration_test.py`, `satisfy-gate.md` and `accept-milestone.md` only, and `git diff bee0060 -- payload/scripts/workflow_integration_test.py` is exactly one changed line (one `-`, one `+`: the golden hash, no comment or other line); the other eight suites pass, none edited except that one line; `docs/ROADMAP.md` carries row 39.

**Verification:** the new tests as the suite runs them, from the stock staged fixture (P1 to P6 read shipped files only); the `docs/exit-codes.md` wording checked from the repository: `grep -c 'inside the state lock' docs/exit-codes.md` is at least 1 in the clone (asserted for good by P7 at CP2); D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block` (with `--manager-releases`), `tools/release` (zlib-ng interpreter, no patch, no skip, with the one expected failure of D-Staging); the new tests again under the Manager's orphan rule (reaper).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.1

**Files:** `manifest.json`, `payload/scripts/workflow_integration_test.py` (its manifest record only: CP1 made the edit), `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.29.1 with its pinned assertions and the protocol-document edits (protocol stays `1.5`; D-Release).
- `manifest.json` 2.29.1: `workflow_version`, the changed records (`workflow_integration_test.py` takes a new `sha256`; its `size` and suite count are unchanged), `conformance.suites`; the Manager block's posture and each record's `rationale` sentence.
- `docs/release-history.md`: the 2.29.1 row and its "Last checked with" line; that of `docs/exit-codes.md` moves too.
- `tools/release/release_test.py`: a 2.29.1 class pinning the posture, the `rationale` sentence, `CHANGED` (it lists `scripts/workflow_integration_test.py`), the suite counts and (P7, D-Tests) the `docs/exit-codes.md` refusal-row wording; the 2.29.0 class gives up the current-release pins.

**Verification:** the new tests again; the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Every flow runs offline: no network, no real `gh`, no install, no socket, no zlib-ng, no Python 3.12 (the last three flows need the full environment and say so); nothing runs against the real repository, its `.ai-review/` or the forge.**
Setup, once, under `$TMPDIR` (`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w44-tmp`): `base/payload` from `git archive bee00609379aa6ab29a7f9076987bb5bfb7dd5de payload/scripts payload/.claude/commands`, `cand/payload` the working tree's `payload/scripts` and `payload/.claude/commands` copied, both **absolute**:
`export BASE="$TMPDIR/base/payload/scripts" CAND="$TMPDIR/cand/payload/scripts"`. The fake `gh` (it only proves **no** forge call) lives outside `/tmp`, `/var/tmp`, `/dev/shm` and `$TMPDIR`, mode 0755:

```sh
export W44_BIN="$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w44-bin"
mkdir -p "$W44_BIN" && printf '#!/bin/sh\necho "gh called: $*" >> "$GH_LOG"\nexit 1\n' > "$W44_BIN/gh" && chmod 755 "$W44_BIN/gh"
export GH_LOG="$W44_BIN/gh.log"; : > "$GH_LOG"
cat > "$TMPDIR/flow.py" <<'PY'
import contextlib, hashlib, io, json, os, subprocess, sys
scripts, cmd, arg = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "AWAITING_FUNCTIONAL_REVIEW")
sys.path.insert(0, scripts)
import workflow_state as ws
W = "wi"; NOW = "2026-11-06T10:00:00Z"
def git(root, *a): subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True)
def write(root, state): open(f"{root}/docs/ai-workflow/WORKFLOW_STATE.json", "wb").write(ws._serialize_state(state))
def mk(phase):  # a scratch repository built by hand: one registry-less item at <phase>
    root = f"{os.environ['TMPDIR']}/f-{cmd}-{phase}"; subprocess.run(["rm", "-rf", root]); os.makedirs(f"{root}/docs/ai-workflow")
    git(root, "init", "-q", "-b", "main"); git(root, "config", "user.email", "t@t"); git(root, "config", "user.name", "t")
    open(f"{root}/.gitignore", "w").write(".ai-review/\n__pycache__/\n")
    write(root, {"schema_version": 1, "active_work_item_id": W, "work_items": {W: {"work_item_id": W, "phase": phase,
        "registry_path": None, "governing_workflow_version": "2.2"}}})
    git(root, "add", "-A"); git(root, "commit", "-q", "-m", "base"); return root
def sha(root): return hashlib.sha256(open(f"{root}/docs/ai-workflow/WORKFLOW_STATE.json", "rb").read()).hexdigest()[:12]
def files(root): return sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) if ".git" not in d.split(os.sep) for f in fs)
def complete(s): return ws.complete_work_item(s, W, NOW, repo_root=root_)
def verdict(fn):
    try: return "completes -> " + fn()["work_items"][W]["phase"]
    except Exception as e: return f"refuses {type(e).__name__} code={getattr(e, 'code', None)}"
if cmd == "phases":
    for p in sorted(ws.KNOWN_PHASES):
        root_ = mk(p); print(f"{p:46s}", verdict(lambda: complete(json.load(open(f'{root_}/docs/ai-workflow/WORKFLOW_STATE.json')))))
elif cmd == "mk": print(mk(arg))
elif cmd == "txn":  # a writer lands after an earlier read and before the transaction
    root_ = mk("AWAITING_FUNCTIONAL_REVIEW"); racer = json.load(open(f"{root_}/docs/ai-workflow/WORKFLOW_STATE.json"))
    racer["work_items"][W]["phase"] = arg; write(root_, racer); raced = sha(root_)
    print("transaction:", verdict(lambda: ws.state_transaction(root_, complete)), "| file == the writer's bytes:", sha(root_) == raced,
          "| phase on disk:", json.load(open(f"{root_}/docs/ai-workflow/WORKFLOW_STATE.json"))["work_items"][W]["phase"])
elif cmd == "race":  # the flag's `now` test seam writes the phase: after the old guard, before the lock
    root_ = mk("AWAITING_FUNCTIONAL_REVIEW"); before, tree, queries, out = sha(root_), set(files(root_)), [], io.StringIO()
    def racing_now():
        s = json.load(open(f"{root_}/docs/ai-workflow/WORKFLOW_STATE.json")); s["work_items"][W]["phase"] = arg; write(root_, s); return NOW
    os.chdir(root_)
    with contextlib.redirect_stdout(out):
        code = ws._satisfy_acceptance_cli(W, now=racing_now, run=lambda a, t: queries.append(a) or "[]")
    body = json.loads(out.getvalue())
    print("exit", code, {k: body.get(k) for k in ("error", "code", "state_changed")}, "| queries:", len(queries),
          "| state bytes unchanged:", sha(root_) == before, "| new files:", sorted(set(files(root_)) - tree))
PY
cli() { # cli <scripts> <phase>: the real flag as a subprocess in a fresh item, the fake gh first on PATH
  r=$(python3 -I "$TMPDIR/flow.py" "$1" mk "$2"); b=$(sha256sum "$r/docs/ai-workflow/WORKFLOW_STATE.json" | cut -c1-12)
  (cd "$r" && PATH="$W44_BIN:$PATH" python3 "$1/workflow_state.py" --satisfy-acceptance wi; echo "exit $?")
  echo "state bytes unchanged: $([ "$b" = "$(sha256sum "$r/docs/ai-workflow/WORKFLOW_STATE.json" | cut -c1-12)" ] && echo yes || echo NO)" \
       "| ignored: $(cd "$r" && git status --porcelain --ignored | tr '\n' ' ')| gh calls: $(wc -l < "$GH_LOG")"; }
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `for s in "$BASE" "$CAND"; do python3 -I "$TMPDIR/flow.py" "$s" phases; done` (the library on each of the 20 phases) | base: **all twenty** `completes -> MILESTONE_COMPLETE`. Candidate: only `AWAITING_FUNCTIONAL_REVIEW` and `AWAITING_USER_ACCEPTANCE` complete; `MILESTONE_COMPLETE` refuses `CompletionPhaseNotReachableError code=work_item_terminal`; the other seventeen `code=phase_not_reachable` |
| 2 | `for s in "$BASE" "$CAND"; do python3 -I "$TMPDIR/flow.py" "$s" txn IMPLEMENTING; done` (a writer moved the item, then the library runs in `state_transaction`) | base: `completes -> MILESTONE_COMPLETE`, file rewritten (the race, at the library). Candidate: `refuses ... code=phase_not_reachable`, `file == the writer's bytes: True`, phase on disk `IMPLEMENTING` (no-write proof) |
| 3 | the same with `MILESTONE_COMPLETE` as the writer's phase | base completes again; candidate `code=work_item_terminal`, bytes equal the writer's |
| 4 | `for s in "$BASE" "$CAND"; do python3 -I "$TMPDIR/flow.py" "$s" race IMPLEMENTING; done`, then with `MILESTONE_COMPLETE` | base: passes the guard and stops later: `ForgeUndecidableError`, `forge_undecidable`, `state_changed` true (the full-gate version that **completes** is test P4). Candidate: `AcceptancePreflightError`, `phase_not_reachable` (`work_item_terminal` for the second), `state_changed` true, `queries: 0`, `state bytes unchanged: False` only because of the writer, new file only `.ai-review/runtime/WORKFLOW_STATE.lock` |
| 5 | `for s in "$BASE" "$CAND"; do for p in IMPLEMENTING AWAITING_LOCAL_IMPLEMENTATION_REVIEW; do cli "$s" $p; done; done` | both: one JSON line `{"code": "phase_not_reachable", "error": "AcceptancePreflightError", "message": "the phase is <p>; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW", "state_changed": false}`, `exit 1`, `state bytes unchanged: yes`, `gh calls: 0`. Only difference: the candidate's `ignored:` shows `!! .ai-review/` (the lock) |
| 6 | `for s in "$BASE" "$CAND"; do cli "$s" MILESTONE_COMPLETE; done` | both: `code` `work_item_terminal`, message `wi is already MILESTONE_COMPLETE`, `state_changed` false, exit 1, bytes unchanged, 0 gh calls |
| 7 | `for s in "$BASE" "$CAND"; do cli "$s" AWAITING_FUNCTIONAL_REVIEW; done` (the guard passes) | both identical: `forge_undecidable`, message `wi: no anchor commit ...`, `state_changed` false, exit 1, bytes unchanged, 0 gh calls (nothing past the guard changed) |
| 8 | `for s in "$BASE" "$CAND"; do d=$(mktemp -d "$TMPDIR/ng.XXXX"); (cd "$d" && python3 "$s/workflow_state.py" --satisfy-acceptance wi; echo "exit $?"; ls -A "$d"; python3 "$s/workflow_state.py" --satisfy-acceptance; echo "exit $?"); done` (a directory that is not a Git repository, then no id) | both: outside Git one JSON object with an `error`, `exit 1`, the directory still empty; no id: argparse usage error, `exit 2` |
| 9 | mutation: `command cp -a "$CAND" "$TMPDIR/mut"`, delete in `$TMPDIR/mut/workflow_state.py` the block of `complete_work_item` that raises `CompletionPhaseNotReachableError`, run flows 1 and 2 on `$TMPDIR/mut` | the mutant behaves like the base: completes from `IMPLEMENTING` (the guard is what flow 1 and 2 prove) |
| 10 | `for s in "$BASE" "$CAND"; do tr '\n' ' ' < "$s/../.claude/commands/satisfy-gate.md" \| grep -o "the library does not" \| wc -l; grep -c CompletionPhaseNotReachableError "$s/../.claude/commands/accept-milestone.md"; done` | base: `1` then `0`. Candidate: `0` then a count of at least `1` (step 2a) |
| 11 | **Full environment (the repository and `python3`; the nine suites).** `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the loop of `docs/RELEASING.md` over `manifest.json`'s suites, from inside the fixture (from a scratch clone with adjusted records at CP1, D-Staging) | all nine suites pass; `TestCompletionPhaseGuard` is among the gate-policy tests |
| 12 | **Full environment (zlib-ng).** `python -m unittest discover -s tools/release -p '*_test.py'` with the zlib-ng venv; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | all pass (at CP1 the one expected failure of D-Staging) |
| 13 | **Scope (full environment).** `git diff bee0060 --stat` at CP1, then at CP2 | CP1: the seven files of CP1 (`payload/scripts/workflow_integration_test.py` among them, one line) plus the plan, registry, mapping, artifacts and state files; nothing under `.claude/`, `scripts/`, `docs/ai-workflow/` managed documents or `.workflow-manager/`; `workflow_protocol.py`, `manifest.json` and `tools/` untouched until CP2 |
| 14 | **Golden hash (offline).** `sha256sum payload/.claude/commands/accept-milestone.md`; `grep -n '"accept-milestone.md":' payload/scripts/workflow_integration_test.py`; `git diff bee0060 --numstat -- payload/scripts/workflow_integration_test.py`; `git diff bee0060 -U0 -- payload/scripts/workflow_integration_test.py \| grep -c '^[-+][^-+]'`; then `python3 -m unittest workflow_integration_test.TestGoldenCommandFileHashes` from the staged fixture | the grep shows exactly the digest the `sha256sum` printed; numstat `1 1` and the count `2` (one line replaced, nothing else in the file); the test passes. Mutation: put the old digest `3e67bc6b...` back on a scratch copy: the test fails naming `accept-milestone.md` |
