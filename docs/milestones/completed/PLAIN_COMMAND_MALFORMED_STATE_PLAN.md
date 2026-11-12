# W45: Workflow 2.29.2 — the plain acceptance commands refuse a malformed state or registry with one JSON object (Revision 1)

- **Work item:** `plain-command-malformed-state` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-12 ("sweep both repos and queue what's reported", ranked #1): RodrigoFAbreu/workflow#155 items 1 to 3; `docs/ROADMAP.md` row 40
  (`Current` with this plan, `Done` at acceptance). Row 39's plan left the item open (`docs/milestones/completed/ACCEPTANCE_PHASE_GUARD_PLAN.md`).
- **Branch:** `milestone/plain-command-malformed-state`
- **Base commit:** `a8d5b1140d7117d21d12c5027fbf9d0d9b56ec5d` (main after #169: release source and own installation are 2.29.1; automatic gates, default `2.2`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 1. Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair. #155 items 4 and 5 are out of scope; item 6 is out of scope too (0a).

## 0. Phase 1: the investigation (before any design)

Measured on scratch repositories built by hand, with the base's `payload/scripts` extracted by `git archive` (the probes live outside the repository and are not shipped): 34 state and registry inputs, each run against all six plain
commands that read the state (204 runs), then 13 more registry shapes sealed under a plan approval (78 runs). Each run recorded the exit code, whether stderr held a traceback, the JSON error class, and a digest of every file of the repository before and after.

### 0a. Each item of #155, checked on the base (Workflow 2.29.1)

| #155 | Claim | On the base | Decision |
| --- | --- | --- | --- |
| 1 | JSON `null` is reported as `StateMissing` | **still true**: all four flags that share the context helper print `StateMissing` ("does not exist") for a file holding `null` | in scope (D-State) |
| 2 | `{}` and `[]` give tracebacks on `--finding-dispositions`; outside Git raises from `_run` | **still true, and wider**: that one flag tracebacks on 16 of the 34 inputs of the first probe (12 state or environment inputs: absent, empty, not JSON, `null`, `[]`, `{}`, a string, a number, `work_items` null, the item null or a list, outside Git; and 4 wrong-typed `optional_findings`) plus the empty id; the four siblings are already JSON | in scope (D-Dispositions) |
| 3 | a malformed registry shape or a non-string `registry_path` exits 1 with a bare `TypeError` / `AttributeError` and no report | **still true**: 11 shapes (0c) | in scope (D-Registry) |
| 4 | a stored PR fact whose head is absent ends the report with `AmbiguousBaseError` | not examined, not touched | out of scope (the PR fact, owner's order) |
| 5 | test gaps (`RegistryCoverageError` row; every requirement id in exactly one of `blockers` and `stored_pr_fact`) | not examined; M4 pins the detail of the existing `RegistryCoverageError` clause only because the new clause sits beside it | out of scope |
| 6 | the `phase_not_reachable` detail reads as a contradiction; `python3 -B` in the documented form | the detail is built in the function D-Registry edits, but rewording it changes the bytes of a **well-formed** refusal, which this item must keep byte-identical | **out of scope**, left for the wording item; nothing dropped as already fixed |

### 0b. The state file and the environment (base; "JSON" is one object with `error` and `message`, exit 1)

| Input | `--finding-dispositions` | the four others (`--acceptance-gate`, `--satisfy-acceptance`, `--write-findings-record`, `--commit-gate-policy-floor`) |
| --- | --- | --- |
| file absent | **traceback** (`TypeError`) | JSON `StateMissing` |
| empty file, not JSON | **traceback** (`CorruptJsonError`) | JSON `CorruptJsonError` |
| `null` | **traceback** (`TypeError`) | JSON **`StateMissing`: the wrong class** (the file exists) |
| `[]`, `{}`, `"x"`, `5` | **traceback** (`TypeError`, `KeyError`) | JSON `StateMalformed` |
| `work_items` null | **traceback** | JSON `StateMalformed` |
| `work_items` `[]` | JSON `UnknownWorkItem` (by accident) | JSON `StateMalformed` |
| the target item null or `[]` | **traceback** (`AttributeError`) | JSON `StateMalformed` |
| unknown id | JSON `UnknownWorkItem` | JSON `UnknownWorkItem` |
| an empty id (`--finding-dispositions ""`) | **traceback** (`KeyError`: `args.finding_dispositions` is falsy, so it falls into the plan-review branch) | JSON `UnknownWorkItem` |
| outside a Git repository | **traceback** (`CalledProcessError` from `_run`) | JSON `CalledProcessError` (pinned by three released tests) |
| a directory at the state path (`IsADirectoryError`, like any `OSError`) | **traceback** | JSON with the class name |
| the item's `optional_findings` of a wrong type | **traceback** (`AttributeError`, `TypeError`, `KeyError`) | `--acceptance-gate`: JSON class name; the others never reach it before another refusal |

Nothing was written by any run except the lock file `--satisfy-acceptance` creates since 2.29.1 (`.ai-review/runtime/WORKFLOW_STATE.lock`, inside the ignored directory) when it passes the context. A wrong-typed `phase` (`123`, `["x"]`) is **already correct**
for the five flags (`phase_not_reachable`, `work_item_not_complete`, a report): dropped. `--plan-review-publication-status` tracebacks on every row above and on a list-typed phase; it is the one flag the Controller's reading of the status table sits behind, so it is
**left untouched** (D-Scope).

### 0c. The registry (base), reached only past the plan-approval coverage check

A malformed registry shape is judged by `registry_completion_status` only when the registry's bytes are the ones the current plan approval covers; otherwise the existing `StalePlanApprovalRegistryReadError` answers first (`registry_unresolvable`). The probe therefore seals
each registry under a hand-built approval (the manifest entry carries the file's blob). Result, `--acceptance-gate` and `--satisfy-acceptance` alike (JSON, exit 1, `{error: <bare class>}`, no report, no `code`):

| Input | Base |
| --- | --- |
| `checkpoints` `"x"`, `null`, `[1]`; a checkpoint with `depends_on` `5` | `TypeError` |
| the registry without the `checkpoints` key; an item without a `work_item_id` key | `KeyError` |
| `registry_path` `5`, `["a"]`, `{}` (the safe-path validator raises, not `InvalidPlanStageMetadataPathError`) | `AttributeError` |
| `plan_approval` `"x"` or `[]` | `AttributeError` |
| already refused as `registry_unresolvable`, byte for byte: file absent, `null`, `[]`, not JSON, `registry_path` `""`, no sealed approval, manifest `"x"` | unchanged |
| tolerated without any refusal: `checkpoints` `{}`; a checkpoint without `status` | unchanged |

The gate's own requirement already refuses every row above as an unmet `checkpoints_complete` (`_acceptance_registry_requirement` catches `Exception`); the **blocker** shared by the report and `--satisfy-acceptance` (`_acceptance_reachability_blocker`)
catches only two classes. The failing call is the same one (`resolve_own_registry_completion_status`); only the catch differs.

### 0d. The smallest place, and the prototype

Three places, no guard in any other function. (1) the shared context helper: split into the root lookup and `_plain_command_state(repo_root, id)` (absent vs `null`, the shape checks it has, the unknown id), which `--finding-dispositions` also calls; (2) `_finding_dispositions_cli` wraps what it
calls in the contract the siblings use (`_AcceptanceCliRefusal`, then any exception, as one JSON object), and the dispatch tests `is not None` and looks up the root inside the try; (3) `_acceptance_reachability_blocker` gets one `except Exception` branch to `registry_unresolvable`, as the gate's requirement does.
The prototype (about 25 changed lines of `workflow_state.py`, on a scratch copy) was run on the same 282 runs: **every traceback of 0b and 0c disappears; no input that was already one JSON object changes except `null` (to `StateMalformed`), the registry rows of 0c, an item without `work_item_id`
(`registry_unresolvable`, detail `KeyError: 'work_item_id'`), and `work_items` `[]` on `--finding-dispositions` (`UnknownWorkItem` becomes the siblings' `StateMalformed`)**. For eight well-formed or already-refused inputs (a registry-less item at three phases, an unknown id, four registry refusals) the five flags'
stdout is **byte-identical** before and after (flow 7). For a state refusal `--finding-dispositions` now prints the same bytes as `--acceptance-gate` (flow 2).

### 0e. Patch or minor, and the Controller

A traceback that becomes one JSON refusal, a wrong class name (`StateMissing` for `null`) that becomes the right one, and a bare `TypeError` that becomes the refusal the gate already makes are bug fixes: **a `fix:` patch, Workflow 2.29.2**. No flag, JSON key, code, phase, state key, command file but
`satisfy-gate.md`, trailer, commit shape or protocol field is added or removed. The one difference a script could notice: `--acceptance-gate` on a malformed registry printed an error object with exit 1 and now prints a report with exit 0 and a `registry_unresolvable` blocker, the shape every other unresolvable
registry already had (0c); a script that read exit 1 as "malformed registry" must read `blockers`. **The protocol stays 1.5 and the Controller's contract is not touched**: `workflow_protocol.py` never invokes these flags (`grep` finds none) and `--plan-review-publication-status`, the status the Controller reads, is not edited.

## 1. Goal, release, scope

Every plain command that reads the state or the registry answers a malformed one with one JSON object (the `{error, message[, code, state_changed]}` shape the flags already promise), exit 1 (`--acceptance-gate`: a report whose blockers name the registry, exit 0, as for every other
unresolvable registry), `state_changed` accurate, nothing written beyond the 2.29.1 lock file, never a traceback; an absent file is `StateMissing` and a file holding `null` is `StateMalformed`. One mechanism: the shared context and one catch. **Out of scope:** #155 items 4, 5 and 6, the engine's acceptance requirements, any gate change,
`--plan-review-publication-status`, a shape validator for `optional_findings` (its failures are the class-name JSON the fallbacks already print, now on every flag), the human path's direct Python calls.

## 2. Design decisions

### D-State: one context for the state checks

`_acceptance_cli_context(id)` keeps its signature and result, and becomes the root lookup plus `_plain_command_state(repo_root, id)`, which holds today's checks in today's order (`StateMissing`, `StateMalformed` for a non-object or a non-object `work_items`, `UnknownWorkItem`, `StateMalformed` for a non-object
item). The only new line distinguishes the two meanings of `None`: when `_load_json` answers `None` and the file exists, the refusal is `StateMalformed`, message `docs/ai-workflow/WORKFLOW_STATE.json holds JSON null, not an object holding a work_items object; restore it from Git`; an absent file stays `StateMissing`.
`_load_json` is not changed (twenty callers). The anchor line of the check is `if (repo_root / DEFAULT_STATE_PATH).exists():  # _load_json answers None for JSON null as well as for an absent file` (kept literally; flow 9 mutates it).

### D-Dispositions: `--finding-dispositions` uses it

`_finding_dispositions_cli(repo_root, id)` keeps its signature (two released tests call it directly) and its output for every well-formed input, and calls `_plain_command_state`, then `finding_dispositions_report`, inside a `try` that prints `{error, message}` and returns 1 for `_AcceptanceCliRefusal`,
for `InvalidFindingDispositionsError` (unchanged) and for any other exception. The dispatch tests `args.finding_dispositions is not None` (the siblings' rule: an empty id is not absent) and runs the root lookup inside a `try` printing the same object. Exit 2 for a usage error is argparse's, unchanged.

### D-Registry: the blocker's catch

`_acceptance_reachability_blocker` gets, after the two existing `except` clauses, `except Exception as exc:  # a malformed registry shape or registry_path: the gate's own requirement refuses it the same way`, returning `{code: "registry_unresolvable", detail: "the item's own registry cannot be resolved: <ClassName>: <message>"}`.
The two existing clauses keep their `str(exc)` detail (byte-identical). The order of the blocker is unchanged: `work_item_terminal`, then the registry, then `phase_not_reachable`; so a malformed registry at `IMPLEMENTING` is `registry_unresolvable`, as an absent registry file is today. `--satisfy-acceptance` needs no edit: the blocker is already the first statement of the transaction's mutator,
so the refusal is `AcceptancePreflightError`, code `registry_unresolvable`, `state_changed` false, the state file untouched, the lock file the only new file (as for 2.29.1's phase refusal).

### D-Scope: what is deliberately left

`--plan-review-publication-status` keeps its traceback rows (the Controller-adjacent status; the owner may order it separately). No shape validator is added for the state or the registry (`validate_state` has no caller among these plain commands -- its production callers are in `payload/scripts/workflow_protocol.py` (`load_valid_state`, the `verify` check, the decision path) -- and hand-built states would fail it: not reused). No message of an existing refusal changes except the `null` one.

### D-Tests (class `TestPlainCommandMalformedState` in `payload/scripts/workflow_gate_policy_test.py`, which runs from the stock staged fixture; written and run red first against the unedited tree; no existing test is edited)

- **M1 null:** `null` in the state file, each of the five flags through its `_cli` function with the seams: `StateMalformed`, the message names `null`, `state_changed` false where the flag has it, the state bytes unchanged, no query, no write; the absent file is still `StateMissing`.
- **M2 `--finding-dispositions` table:** through the real script as a subprocess (the siblings' `error()` helper), for empty, `{`, `null`, `[]`, `{}`, `"x"`, `work_items` null, item null, an unknown id, an empty id, outside Git: exit 1, stdout one JSON object with the class name, **no `Traceback` on stderr**, tree unchanged. The `--acceptance-gate` bytes equal the flag's bytes for each state refusal.
- **M3 registry shapes (sealed under the fixture's approval: the test re-seals the manifest entry with `git hash-object` after each edit, otherwise the stale-approval refusal answers first, which is a different row):** `checkpoints` `"x"`, `null`, `[1]`, a missing key, `depends_on` `5`; `registry_path` `5` and `["a"]`; `plan_approval` `"x"`.
  `--acceptance-gate`: exit 0, `registry_unresolvable` in `blockers`, the gate's `checkpoints_complete` requirement unmet (the two refusals agree), the detail names the class. `--satisfy-acceptance`: exit 1, `AcceptancePreflightError`, code `registry_unresolvable`, `state_changed` false, state bytes equal, the forge never queried.
- **M4 order:** a malformed registry at `IMPLEMENTING` and at `MILESTONE_COMPLETE` gives `registry_unresolvable` and `work_item_terminal` respectively (the blocker's order); the existing clauses keep their `str(exc)` detail (one `RegistryCoverageError` row pins that).
- **M5 golden:** the five flags on well-formed inputs of 0d (registry-less item at the three phases, an unknown id, four registry refusals): stdout equals literals captured from the base **before the first edit**; exit codes equal.
- **M6 texts (shipped files only):** `satisfy-gate.md` carries the new sentence; the maintainer page `docs/exit-codes.md` is checked from the repository (grep) at CP1 and pinned by the 2.29.2 release class at CP2 (it has no manifest record; the stock fixture does not materialize it).
- **Failure-only mutations** (each on a scratch copy; the named test must detect the mutation -- it fails; other relevant tests may fail too, since coverage intentionally overlaps, e.g. removing the new registry catch can fail both M3 and M4): m1 the `.exists()` line removed (null is `StateMissing`) → M1; m2 `--finding-dispositions` back to `_load_json` and subscripts → M2; m3 the new `except Exception` removed → M3; m4 it moved after the phase check → M4; m5 the dispatch back to a truthiness test → M2 (empty id);
  m6 the root lookup outside the `try` → M2 (outside Git); m7 the detail without the class name → M3; m8 the blocker's order swapped (phase before registry) → M4.

### D-Docs and D-Command

`payload/.claude/commands/satisfy-gate.md`: one sentence after the `--acceptance-gate` paragraph: a state file or registry that is malformed is answered with one JSON object (or, for the registry, a `registry_unresolvable` blocker), never a traceback, and an absent file differs from a `null` one; the same sentence is true of `--finding-dispositions`. The words `never a traceback` appear in it (flow 10 greps them).
`accept-milestone.md` is **not** edited (its SHA-256 is pinned by the integration suite's golden table). `docs/exit-codes.md`: a row group for `--finding-dispositions` (exit 0 the listing; 1 the JSON `error`/`message`; 2 the arguments did not parse), the `--acceptance-gate` row names `registry_unresolvable` among the blockers and says the registry class exits 0, the `null` case.
`docs/ROADMAP.md`: row 40 (added with this plan), `Done` at acceptance. No milestone id in any `docs/*.md` page but the roadmap.

### D-Release

2.29.2, by the procedure of `docs/milestones/completed/ACCEPTANCE_PHASE_GUARD_PLAN.md` (D-Release) with these differences: the changed records are `workflow_state.py`, `workflow_gate_policy_test.py`, `satisfy-gate.md`, `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md` (`sha256`, `size`, the `rationale` sentence `plain-command-malformed-state (workflow-2.29.2)`);
`conformance.suites` moves for `workflow_gate_policy_test.py` only, by the number of new tests; `WORKFLOW_RELEASE` becomes 2.29.2 with its pinned assertions; `tools/release/release_test.py` gets a 2.29.2 class and the 2.29.1 class gives up the current-release pins; `docs/release-history.md` row (a patch; the way back restores the tracebacks and the `null` class; no state to undo);
the Manager block's posture is rewritten with the downgrade guidance carried over sentence for sentence and the closing sentence "The release tooling and the maintainer documents are not part of the installed release." kept.

### D-Staging

CP1 changes shipped files whose manifest records move at CP2, so it verifies in a disposable clone under `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w45-tmp` (procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging, and the count handling of the lstat-errors plan): recompute `sha256` and `size`
of the changed records, measure the gate-policy count, commit in the clone, run the "Verification commands" of `docs/RELEASING.md`; `tools/release` uses `/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`. **The one expected failure at CP1:** the 2.29.1 class pins the gate-policy count;
it is named at implementation and released in CP2. The new tests run again under the Manager's orphan rule (reaper).

## 3. Open decisions (for the plan reviewer and the owner)

This repository has no `docs/TECHNICAL_DECISIONS.md`, so no Open decision row is touched. Reversible choices: **patch or minor** (0e: patch; the owner may choose a minor, which changes nothing else); **the registry class exits 0 on `--acceptance-gate`** (a report with a blocker, as every other unresolvable registry; the alternative is exit 1 with an error object, which would make
this one registry class the only one that prints no report); **`--plan-review-publication-status` left alone** (D-Scope); **item 6 left out** (0a); **an item without `work_item_id` reads as `registry_unresolvable`** (a side effect of the one catch, detail `KeyError: 'work_item_id'`, instead of a bare `KeyError`; it is a refusal either way);
**the lock file** a registry refusal of `--satisfy-acceptance` creates (2.29.1's design, unchanged).

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The shared state context, the dispositions flag and the blocker's catch, tests, command text and pages | - | 3 | 1 |
| CP2 | Release 2.29.2 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The shared state context, the dispositions flag and the blocker's catch, tests, command text and pages

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py`, `payload/.claude/commands/satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): the base's golden literals for M5 are captured before any edit; M1 to M6 are written and run red against the unedited tree; mutations m1 to m8 each fail the named test on a scratch copy and the results are recorded.
- **The change** (D-State, D-Dispositions, D-Registry): `_plain_command_state`, the shared helper's callers, the `_finding_dispositions_cli` try, the dispatch, the blocker's one `except`; nothing else in the library. The existing tests are not edited: `git diff a8d5b11 -- payload/scripts/workflow_gate_policy_test.py` has additions only.
- **The command text and the pages** (D-Command, D-Docs). `check_docs.py` stays clean.
- **No other mechanism:** `git diff a8d5b11 --stat -- payload` lists `workflow_state.py`, `workflow_gate_policy_test.py` and `satisfy-gate.md` only; `payload/scripts/workflow_integration_test.py` is untouched; the other eight suites pass unedited; `docs/ROADMAP.md` carries row 40.

**Verification:** the new tests as the suite runs them, from the stock staged fixture; the `docs/exit-codes.md` wording checked from the repository (`grep -c 'finding-dispositions' docs/exit-codes.md` is at least 3); D-Staging in a disposable clone: the nine suites from the staged fixture, `tools/docs`, `check_docs.py`, `check-manager-block` (with `--manager-releases`), `tools/release` (zlib-ng interpreter, no patch,
no skip, with the one expected failure of D-Staging); the new tests again under the Manager's orphan rule (reaper).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.29.2

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`, `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`, `tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.29.2 with its pinned assertions and the protocol-document edits (protocol stays `1.5`; D-Release).
- `manifest.json` 2.29.2: `workflow_version`, the changed records of CP1 and CP2 (`sha256`, `size`), the gate-policy suite count, the Manager block's posture and each record's `rationale` sentence.
- `docs/release-history.md`: the 2.29.2 row and its "Last checked with" line; that of `docs/exit-codes.md` moves too.
- `tools/release/release_test.py`: a 2.29.2 class pinning the posture, the `rationale` sentence, `CHANGED`, the suite counts and the `docs/exit-codes.md` wording of M6; the 2.29.1 class gives up the current-release pins.

**Verification:** the new tests again; the nine suites pass in a stock `release.py stage-conformance --commit HEAD` fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Every flow but the last three runs offline: no network, no real `gh`, no install, no socket, no zlib-ng, no Python 3.12; nothing runs against the real repository, its `.ai-review/` or the forge.** Setup, once, with `TMPDIR` set to
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w45-tmp`: `base/payload` from `git archive a8d5b1140d7117d21d12c5027fbf9d0d9b56ec5d payload/scripts payload/.claude/commands`, `cand/payload` the working tree's `payload/scripts` and `payload/.claude/commands` copied, both **absolute**:
`export BASE="$TMPDIR/base/payload/scripts" CAND="$TMPDIR/cand/payload/scripts"`. The fake `gh` (it only proves **no** forge call) lives outside `/tmp`, `/var/tmp`, `/dev/shm` and `$TMPDIR`, mode 0755 in a directory only its owner writes:

```sh
export W45_BIN="$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w45-bin"
export GH_LOG="$W45_BIN/gh.log"
mkdir -p "$W45_BIN" && printf '#!/bin/sh\necho "gh called: $*" >> "$GH_LOG"\nexit 1\n' > "$W45_BIN/gh" && chmod 755 "$W45_BIN/gh"
cat > "$TMPDIR/flow.py" <<'PY'
import hashlib, json, os, shutil, subprocess, sys
scripts, case, *flags = sys.argv[1:]
T, W, REG = os.environ["TMPDIR"], "wi", "docs/ai-workflow/registry/wi-registry.json"
def item(**kw): return {"work_item_id": W, "phase": "AWAITING_FUNCTIONAL_REVIEW", "registry_path": None, "governing_workflow_version": "2.2", **kw}
def S(wi): return json.dumps({"schema_version": 1, "active_work_item_id": W, "work_items": {W: wi}})
def R(cps): return json.dumps({"work_item_id": W, "checkpoints": cps})
def blob(t): return subprocess.run(["git", "hash-object", "--stdin"], input=t, capture_output=True, text=True).stdout.strip()
def sealed(reg, **kw):  # a registry the plan approval covers, so the coverage check passes and the shape is what is judged
    pa = {"status": "CURRENT", "review_content_manifest": [{"path": REG, "exists": True, "mode": "100644", "blob": blob(reg)}]}
    return S(item(registry_path=REG, plan_approval=pa, **kw)), reg
CASES = {"absent": (None, None), "empty": ("", None), "notjson": ("{oops", None), "null": ("null", None), "list": ("[]", None),
  "object": ("{}", None), "string": ('"x"', None), "items-null": ('{"work_items": null}', None), "item-null": (S(None), None),
  "unknown": ('{"work_items": {}}', None), "empty-id": (S(item()), None), "wellformed": (S(item()), None), "complete": (S(item(phase="MILESTONE_COMPLETE")), None),
  "implementing": (S(item(phase="IMPLEMENTING")), None), "outside": (S(item()), None),
  "regpath-int": (S(item(registry_path=5)), None), "regpath-list": (S(item(registry_path=["a"])), None),
  "approval-str": (S(item(registry_path=REG, plan_approval="x")), R([])),
  "cps-str": sealed(R("x")), "cps-null": sealed(R(None)), "cps-list-int": sealed(R([1])), "cps-missing": sealed(json.dumps({"work_item_id": W})),
  "deps-int": sealed(R([{"id": "CP1", "depends_on": 5}])), "cps-sealed-ok": sealed(R([])),
  "reg-absent": (S(item(registry_path=REG)), None), "reg-null": (S(item(registry_path=REG)), "null"), "reg-notjson": (S(item(registry_path=REG)), "{oops"),
  "cps-implementing": sealed(R("x"), phase="IMPLEMENTING")}
state, reg = CASES[case]
if flags == ["all"]: flags = ["--finding-dispositions", "--acceptance-gate", "--satisfy-acceptance", "--write-findings-record", "--commit-gate-policy-floor"]
def snap(root): return {os.path.relpath(os.path.join(d, f), root): hashlib.sha256(open(os.path.join(d, f), "rb").read()).hexdigest()[:8]
                        for d, _, fs in os.walk(root) if ".git" not in d.split(os.sep) for f in fs}
for flag in flags:
    root = f"{T}/f-{case}"; shutil.rmtree(root, ignore_errors=True); os.makedirs(f"{root}/docs/ai-workflow/registry")
    open(f"{root}/.gitignore", "w").write(".ai-review/\n")
    if state is not None: open(f"{root}/docs/ai-workflow/WORKFLOW_STATE.json", "w").write(state)
    if reg is not None: open(f"{root}/{REG}", "w").write(reg)
    if case != "outside":
        for a in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"], ["add", "-A"], ["commit", "-q", "-m", "base"]):
            subprocess.run(["git", "-C", root, *a], check=True, capture_output=True)
    before = snap(root); open(os.environ["GH_LOG"], "w").close()
    p = subprocess.run(["python3", "-B", f"{scripts}/workflow_state.py", flag, W if case != "empty-id" else ""], cwd=root, capture_output=True, text=True,
                       env={**os.environ, "PATH": os.environ["W45_BIN"] + ":" + os.environ["PATH"]})
    try:
        j = json.loads(p.stdout)
        what = ("report ready=%s blockers=%s" % (j["ready"], [b["code"] for b in j["blockers"]])) if "ready" in j else \
               json.dumps({k: j[k] for k in ("error", "code", "state_changed") if k in j}, sort_keys=True) if "error" in j else "ok-json"
    except ValueError: what = "stdout not one JSON object: %r" % p.stdout[:40]
    after = snap(root); changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    print(f"{flag:27s} rc={p.returncode} {what} | out={hashlib.sha256(p.stdout.encode()).hexdigest()[:10]} | traceback={'yes' if 'Traceback' in p.stderr else 'no'} | files changed={changed or 'none'} | gh calls={len(open(os.environ['GH_LOG']).read().splitlines())}")
PY
run() { for s in "$BASE" "$CAND"; do echo "== $(basename "$(dirname "$(dirname "$s")")")"; python3 -I "$TMPDIR/flow.py" "$s" "$@"; done; }  # run <case> <flags|all>
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `run absent all` | base: `--finding-dispositions` `traceback=yes`, `stdout not one JSON object`; the four others `StateMissing`. Candidate: all five `{"error": "StateMissing"}` (the three writers add `"state_changed": false`), `rc=1`, `traceback=no`, `files changed=none`, `gh calls=0` |
| 2 | `run null all` | base: the dispositions flag a traceback, the four others **`StateMissing`** (the file exists). Candidate: all five **`StateMalformed`**, `state_changed` false, `files changed=none`, `gh calls=0`; the `out=` digest of `--finding-dispositions` **equals** that of `--acceptance-gate` |
| 3 | `for c in list object string items-null item-null; do echo "-- $c"; run $c all; done` | base: the dispositions flag a traceback each time, the four others `StateMalformed`. Candidate: five `StateMalformed` each time, no traceback, `files changed=none`; the four others' `out=` digests are identical to the base's |
| 4 | `for c in empty notjson unknown; do echo "-- $c"; run $c all; done` | base: dispositions traceback for `empty` and `notjson`, `CorruptJsonError` on the four; `unknown` all `UnknownWorkItem`. Candidate: five `CorruptJsonError`, five `CorruptJsonError`, five `UnknownWorkItem`; for `unknown` every `out=` digest is identical to the base's |
| 5 | `run outside all; run empty-id --finding-dispositions --acceptance-gate` (a directory that is not a Git repository; an empty id) | base: the dispositions flag tracebacks in both (`CalledProcessError`; `KeyError`), the others one JSON object. Candidate: `CalledProcessError` from all five (the same class the released tests pin), `UnknownWorkItem` from both for the empty id, no traceback, `files changed=none` |
| 6 | `for c in cps-str cps-null cps-list-int cps-missing deps-int regpath-int regpath-list approval-str; do echo "-- $c"; run $c --acceptance-gate --satisfy-acceptance; done` | base: both flags rc 1, `{"error": "TypeError"}` or `KeyError` or `AttributeError` only, no report, no `code`. Candidate: `--acceptance-gate` `rc=0 report ready=False` with `registry_unresolvable` first among the blockers; `--satisfy-acceptance` `rc=1 {"code": "registry_unresolvable", "error": "AcceptancePreflightError", "state_changed": false}`, `files changed=['.ai-review/runtime/WORKFLOW_STATE.lock']` only (the state file is unchanged), `gh calls=0` |
| 7 | `for c in wellformed implementing complete unknown reg-absent reg-null reg-notjson cps-sealed-ok; do run $c all > "$TMPDIR/o-$c"; done` and compare the two halves of each file, e.g. `for c in wellformed complete reg-null; do diff <(sed -n '2,6p' "$TMPDIR/o-$c") <(sed -n '8,12p' "$TMPDIR/o-$c") && echo "$c identical"; done` | the golden proof: every line of the base half equals the candidate half (`out=` digests, exit codes, JSON, files changed), **byte-identical well-formed paths**; no `diff` output |
| 8 | `run cps-implementing --acceptance-gate --satisfy-acceptance; run reg-absent --satisfy-acceptance` | candidate: a malformed registry at `IMPLEMENTING` is `registry_unresolvable` (before `phase_not_reachable`), identical in code to the absent registry file; base: the bare `TypeError` / the same `registry_unresolvable` |
| 9 | mutations: `for m in a b c; do command rm -rf "$TMPDIR/mut-$m"; command cp -a "$TMPDIR/cand" "$TMPDIR/mut-$m"; done`, then in each `mut-*/payload/scripts/workflow_state.py` replace exactly one literal (`python3 -I` one-liner with `assert s.count(x) == 1`): (a) `if (repo_root / DEFAULT_STATE_PATH).exists():` by `if False:`; (b) `except Exception as exc:  # a malformed registry shape` by `except ZeroDivisionError as exc:  # a malformed registry shape`; (c) `if args.finding_dispositions is not None:` by `if args.finding_dispositions:`. Run flow 2 on (a), flow 6 on (b), flow 5 on (c) with the mutant path as the scripts directory | each mutant reproduces the base on its own flow only: (a) `StateMissing` for `null`; (b) the bare `TypeError`; (c) the dispositions flag's `KeyError` traceback for the empty id; the other two flows still pass on each mutant |
| 10 | `for s in "$BASE" "$CAND"; do tr '\n' ' ' < "$s/../.claude/commands/satisfy-gate.md" \| grep -c 'never a traceback'; done; grep -c 'finding-dispositions' docs/exit-codes.md` | base `0`, candidate at least `1`; the page counts at least 3 once CP1's rows exist |
| 11 | **Full environment (the repository and `python3`; the nine suites).** `python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the loop of `docs/RELEASING.md` over `manifest.json`'s suites, from inside the fixture (from a scratch clone with adjusted records at CP1, D-Staging) | all nine suites pass; `TestPlainCommandMalformedState` is among the gate-policy tests; the integration suite is unedited |
| 12 | **Full environment (zlib-ng).** `python -m unittest discover -s tools/release -p '*_test.py'` with the zlib-ng venv; `python3 -m unittest discover -s tools/docs -p '*_test.py'`; `python3 tools/docs/check_docs.py`; `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json` | all pass (at CP1 the one expected failure of D-Staging) |
| 13 | **Scope (full environment).** `git diff a8d5b11 --stat` at CP1, then at CP2 | CP1: the five files of CP1 plus the plan, registry, mapping, artifacts and state files; the test file's diff has additions only; nothing under `.claude/`, `scripts/`, `docs/ai-workflow/` managed documents or `.workflow-manager/`; `workflow_protocol.py`, `manifest.json` and `tools/` untouched until CP2 |
