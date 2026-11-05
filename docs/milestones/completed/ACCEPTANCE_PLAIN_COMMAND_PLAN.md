# W40: Workflow 2.26.0 — the acceptance gate has a plain, read-only report command (Revision 4)

- **Work item:** `acceptance-plain-command` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-05 (passed on from the RepFlow lane):
  RodrigoFAbreu/workflow#148 (no comments). Row 35 of `docs/ROADMAP.md` is added with this plan (`Current` now, `Done`
  at acceptance); row 36 states the part this item does not do.
- **Branch:** `milestone/acceptance-plain-command`
- **Base commit:** `16e33d1e67b70812c3ea9f2b8f495b49312d9b16` (main after #154: release source and own installation are
  2.25.7; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 4 (revisions 1 to 3 were each reviewed locally once: round 1's B1, B2, I1 to I4 and three optional findings, round 2's I1 to I3 and four optional findings, round 3's I1, I2 and three optional findings are applied, see sections 7 to 9). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. Phase 1: the investigation (before any design)

### 0a. What `/satisfy-gate acceptance` tells a worker to run, in order

The command text (`payload/.claude/commands/satisfy-gate.md`, lines 154 to 257) plus the steps of `/accept-milestone` it
cites by number (2, 2a, 2b, 3 to 8). Python calls only (`satisfy-gate.md` runs `/accept-milestone` steps "0, 2, 2a, 2b and 3 to 8"); each row says what it returns and whether it **writes**.

| # | Text | Call | Returns | Writes |
| --- | --- | --- | --- | --- |
| 0 | step 0 | `python3 scripts/workflow_backlog.py preflight-accept <id>` (already a plain command) | JSON, or a refusal on stderr (exit 2) | no |
| 1a | step 2a (`/accept-milestone`), the terminal-reachability pre-flight | `workflow_state.resolve_own_registry_completion_status(repo_root, work_item)` then `workflow_state.milestone_complete_gate_reachable(phase=, is_terminal=)` | `(is_terminal, outstanding_checkpoint_id)`, then a bool that is true **only at `AWAITING_FUNCTIONAL_REVIEW` or `AWAITING_USER_ACCEPTANCE`**; `RegistryCoverageError` / `StalePlanApprovalRegistryReadError` when the registry cannot be resolved | no |
| 1b | step 2a, the `requires_pr_approved` pre-flight | `workflow_state.assert_human_acceptance_pr_approved(…)`: a GitHub query that stores the fact; `None` when the option is off | `None` or `PullRequestNotApprovedError` | **yes**, when on (not evaluated by the report) |
| 1 | step 1 to 3 | `workflow_state.satisfy_acceptance_gate(repo_root, id, now=)`: **one** `state_transaction`, which runs, in order, `anchor_of`, `resolve_gh` and `query_forge_pr_facts` (the network), `store_workflow_pr_fact` (pure), `reopen_for_stored_fact` (may reopen), `evaluate_gate(…, "acceptance")`, then, only if satisfiable, `apply_acceptance_satisfaction` = `assert_acceptance_evidence_current`, `build_acceptance_satisfaction` and `complete_work_item` (children, own checkpoints, completion obligations, `assert_finding_dispositions_recorded`) | `{record, trailer}`; or `GateNotSatisfiableError` after the transaction (the stored PR fact and, when `reopen_for_stored_fact` reopens, the phase and `reopenings` are written), or a forge/completion refusal inside it (nothing written) | **yes**: the PR fact, a possible reopening; on success `phase` `MILESTONE_COMPLETE` and `acceptance_satisfaction` |
| 2 | step 2 (the worker's own reading) | `workflow_gate_policy.evaluate_gate(repo_root, state, id, "acceptance")` | `{mode, satisfiable, satisfiable_after_query, pending_query, obtainable, requirements[{id, met, detail}], …}` | no |
| 3 | step 3, first sentence (but `/accept-milestone` step 2a runs the dispositions pre-flight **before** rows 1a and 1b; the report's `blockers` order follows `satisfy-gate.md`, and `test_accept_milestone_runs_the_disposition_preflight_before_the_pr_preflight` pins 2a's) | `workflow_state.assert_finding_dispositions_recorded(repo_root, state, id)` | `None`, or `UndispositionedFindingsError` / `InvalidFindingDispositionsError` | no |
| 4 | step 4 (`/accept-milestone` 5a) | `workflow_state.write_finding_dispositions_record(repo_root, state, id)` | the paths the completion commit stages | **yes**: `docs/milestones/completed/<id>-findings.md` |
| 5 | step 4 (`/accept-milestone` 6) | `workflow_state.acceptance_satisfied_by_trailer(record)` | the `policy:<12 characters>` trailer value | no (a string) |
| 6 | step 5 | `workflow_state.commit_gate_policy_floor(…)`, only when the observed setting is stricter than the floor | a floor commit | **yes**: state and its own commit |

By hand, not Python: the roadmap and `docs/ACTIVE_MILESTONE.md` edits, the archive copy, the completion commit with its
trailers, `workflow_backlog.py accept`/`next`. So a worker improvises up to six calls plus a state load and a clock value,
in heredocs next to `gh`: the shape the auto-mode check refuses.

### 0b. What plain commands exist today

| Command | Does | Reads or writes |
| --- | --- | --- |
| `python3 scripts/workflow_state.py --finding-dispositions <id>` | lists every recorded Optional finding with its disposition and prints the skeleton for the missing ones; exit 0, or 1 with a JSON `error` | read-only |
| `python3 scripts/workflow_state.py --plan-review-publication-status <id>` | the plan-review table's row as JSON | read-only |
| `python3 scripts/workflow_protocol.py describe`, `verify`, `resolve-artifact`, `next-action`, `reconcile` | protocol envelope, exit 0, 1, 2 or 3 | read-only |
| `python3 scripts/workflow_protocol.py record-external-result` | stores a reported functional or PR fact | writes state |
| `python3 scripts/workflow_backlog.py preflight-accept`, `next`, `accept` | the backlog steps | the last writes |

Nothing evaluates the acceptance gate: `next-action` row 38h (`policy_satisfiable`) never reads the dispositions (the
command text says so at step 3) and `--finding-dispositions` knows nothing of the gate; a worker writes rows 2 and 3 itself.

### 0c. The rules for adding an operation or a flag (read, not assumed)

- `ORCHESTRATION_PROTOCOL.md` section 1: a **minor** bump "only adds things: optional response fields, new action ids,
  new error codes, new artifact or result kinds, or new **capabilities**". A new `workflow_protocol.py` **operation** is a
  new capability: `describe` lists `capabilities.operations`, the envelope schema and the Controller's own reading of the
  operations change, so it is a protocol `1.6`, a `describe`/schema/test change in `workflow_protocol.py` and the
  protocol document, and **the Controller lane must learn it**.
- A `workflow_state.py` CLI flag is **outside** the protocol: the document says the 2.6.0 query CLIs "are kept
  byte-compatible; the protocol does not replace them", and `--finding-dispositions` shipped in 2.14.0 with the protocol
  still `1.4` (the release list in section 1 puts 2.14.0 in the `1.4` group). `COMMAND_FILES.md` has no rule about flags;
  its `state_writer` key stays `true` for `/satisfy-gate` (the command still writes). So a flag is **additive**: no
  protocol version change, no change to the Controller's contract, nobody must adapt (the Controller may adopt it).

### 0d. Sizing decision (the owner's rule: one mechanism per item)

The read-only evaluation and the write completion are **two mechanisms**:

- the evaluation reads stored state and the tree and prints a report: nothing can be left half-written;
- the completion is a state writer: the network query, a possible reopen, the completion and the trust record
  (`acceptance_satisfaction`), then documents, archive copy, findings record, a commit with exact trailers and maybe a
  floor commit. It needs its own no-write and partial-failure proofs (the backlog `accept` refusal after the state is
  complete is already a documented recovery) and a concurrency story.

**This item plans only the read-only evaluation: one new flag, `workflow_state.py --acceptance-gate <id>`.** The write
completion (the one-process `state_transaction` around `satisfy_acceptance_gate` printing `{record, trailer}`, the
findings record and the floor, with the document edits and the commit still the worker's plain edits and `git`) is the
next item, row 36 (Next). **No protocol version bump and no Controller change is needed by this item**; if row 36 is
done as a `workflow_protocol.py` operation instead, that would be a bump (`1.6`) and the Controller lane must be told:
the plan for row 36 decides it, this one does not.

## 1. Goal, release, and what stays as it is

A worker reads the state of the acceptance gate with **one plain command** instead of improvised Python, and gets the
requirements met or not (each with its detail), the missing dispositions by key (with the skeleton) and a single
`ready` answer. The command text names it first and keeps the Python description as the specification.

- **Release: Workflow 2.26.0, a `feat:` minor.** A new, documented command surface (a flag a worker is told to run, in a
  command file and `docs/exit-codes.md`) is a feature, not a `fix:`; the manifest's `workflow_version` moves 2.25.7 to
  2.26.0 and the pull-request title says `feat:`. The protocol stays `1.5`.
- **Gate semantics do not change**: the report calls `evaluate_gate` and the dispositions functions the stage already
  calls; it re-implements no requirement. Same requirements, same refusals, same commits and trailers, same by-policy
  record: **no line of `satisfy_acceptance_gate`, `apply_acceptance_satisfaction`, `complete_work_item`,
  `evaluate_gate` or any command step other than the cited wording changes.**
- **Not done here (said plainly):** the write subcommand (row 36); the GitHub query (the stage's own step 1 still
  queries first and decides); `complete_work_item`'s own refusals (children, completion obligations: not a pure read);
  the backlog pre-flight (already plain); `/approve-review`; the **optional** `next-action` evidence line: declined, because row 38h's `ctx.call` table registers
  every function a row calls with its exception classes and pins them in `workflow_protocol_test.py`, and the line changes
  what the Controller reads, which is a second mechanism; it goes with row 36.

## 2. Design decisions

### D-Flag: the interface

`python3 scripts/workflow_state.py --acceptance-gate <work-item-id>`, the **plain** form, the one form named everywhere
(the roadmap row 35, the command text, the tests, section 5). It is **not** run under `python3 -I`: `-I` removes the
script's directory from `sys.path` and `workflow_state.py` line 193 does `import workflow_fingerprint`, so on the base
tree `python3 -I payload/scripts/workflow_state.py --finding-dispositions <id>` ends in `ModuleNotFoundError` (measured in
review). `--finding-dispositions` is already documented in the plain form, and this flag follows it; no import-path change
is planned. It is a third member of the existing mutually
exclusive group (`--plan-review-publication-status`, `--finding-dispositions`), so two flags together is the argparse
refusal (exit 2) as today. It takes no lock and calls no `state_transaction`, `git add`, `git commit` or `gh`.

Output: one JSON document, `sort_keys=True`, `indent=2`, exit **0** whenever a report is printed (also when not ready,
like `--finding-dispositions`):

| Key | Value |
| --- | --- |
| `work_item_id`, `phase` | the item and its phase |
| `gate` | `evaluate_gate(repo_root, state, id, "acceptance")` **verbatim** (mode, source, policy_digest, satisfiable, satisfiable_after_query, pending_query, obtainable, requirements with `id`, `met`, `detail`, evidence, digests). In `human` mode it is that function's own human result |
| `stored_pr_fact` | `{"unmet": [{"id", "detail"}…], "note": "information only: the stage's own query replaces the stored fact before it decides"}`: the unmet requirements among `pr_fact_current`, `no_standing_pr_objection`, `ci_green`, `pr_approved`, copied from `gate`. **Never a blocker**: only the stage's query (`satisfy_acceptance_gate` step 1) replaces `gate_evidence.pr`, and it runs before the gate is decided, so a stale `pending`, `none`, `CHANGES_REQUESTED`, failed-checks or older-head fact says nothing about what the stage will conclude (review B2, measured: all four complete on a green query) |
| `dispositions` | `{"missing": [{"key", "label"}], "invalid": null or the `InvalidFindingDispositionsError` text, "skeleton": the object `--finding-dispositions` prints, or null when none is missing}`; `label` is the refusal's own `_finding_label` text (`<key> (<stage> <role> round <n>): <first line>`). When `invalid` is set, `missing` is `[]` and `skeleton` is null: the library raises before any key is known |
| `blockers` | ordered list of `{"code", "detail"}`: `work_item_terminal` (phase `MILESTONE_COMPLETE`); otherwise the step-2a pre-flight of row 1a, using the existing predicate: `phase_not_reachable` (`milestone_complete_gate_reachable` is false: `detail` names the phase and, if not terminal, the outstanding checkpoint) or `registry_unresolvable` (`RegistryCoverageError` / `StalePlanApprovalRegistryReadError`, `detail` = the error text); then, from the gate, `human_gate` (mode human) or one `requirement_unmet` per unmet requirement **among `checkpoints_complete`, `technical_approval_current` and `functional_flows_passed` only** (`detail` = `"<id>: <detail>"`; these are the requirements no query replaces); then `dispositions_invalid`, or one `disposition_missing` per missing key (`detail` = the key) |
| `query_pending` | `gate.pending_query` and not `gate.satisfiable`; false in human mode |
| `ready` | `blockers` is empty: nothing this report can see refuses the stage. The phase and the registry pre-flight are inside it (row 1a), so an item at `IMPLEMENTING` is not ready |
| `not_checked` | the fixed list `["complete_work_item refusals: incomplete child work items, completion obligations", "the backlog pre-flight (scripts/workflow_backlog.py preflight-accept)", "the GitHub query and the pull-request requirements it replaces (the stage runs it first and it decides)", "the requires_pr_approved pre-flight (a query)"]`: `ready` never claims these |

Errors (exit **1**, one JSON object `{"error": <class name or code>, "message": …}` on stdout, nothing else, nothing
written): `UnknownWorkItem` (the id), `StateMissing` (no `WORKFLOW_STATE.json`), `CorruptJsonError` (unreadable state), `StateMalformed` (valid JSON that is not an object holding a `work_items` object: `{}`, `[]`; measured with `--finding-dispositions`, which gives a `KeyError`/`TypeError` traceback today, and which this item does not touch), and, for any other exception the library raises (running outside a Git repository raises from `_run`), the exception's **class name** with its message: never a traceback. **The dispatch comes before the shared `git rev-parse`**: `_plan_review_publication_status_cli` runs `repo_root = _run(["git", "rev-parse", "--show-toplevel"], …)` after `parse_args` and before any flag is handled (line 20260), so a flag added beside `--finding-dispositions` would end in a `CalledProcessError` traceback outside a Git repository. The dispatch tests `args.acceptance_gate is not None`, not truthiness (the existing idiom `if args.finding_dispositions:` would treat an empty id as absent and fall through to the publication-status path with `None`): an empty id is `UnknownWorkItem`. `--acceptance-gate` is therefore dispatched right after `parse_args`, and its own function finds the repository root inside the guard that produces the error object.
`InvalidFindingDispositionsError` is **not** an error: it is `dispositions.invalid` and a blocker, because the report
exists to say so; an unreadable `GATE_POLICY.json` is not an error either: `evaluate_gate` reads it as source
`invalid` and the report prints that result verbatim. Exit 2 stays the argparse code. The existing flags, their output and exit codes are byte-identical.

### D-Safety: why it writes nothing

`evaluate_gate` is documented as writing nothing, `finding_dispositions_report` and `read_finding_dispositions` only read,
and the report takes no `state_lock`, so it does not take or create `.ai-review/runtime/WORKFLOW_STATE.lock`. The proof is a
measurement, not a claim (T1): every path outside `.git`, **directories included** (path, kind, and for files size,
`mtime_ns`, sha256), the refs and `HEAD` are identical after each run, including every failure path; the lock file's
existence is asserted before and after (`.ai-review/` already exists when `AcceptanceRepo.__enter__` returns, so its
absence cannot be the check); and a `gh` placed first on `PATH` that records its calls is never called. Scope of "writes
nothing": the measurement runs with `PYTHONDONTWRITEBYTECODE=1`; a plain run inside an installed repository writes only
the Git-ignored `scripts/__pycache__`, which is harmless and is the same for `--finding-dispositions`.

### D-Command: the command text

`payload/.claude/commands/satisfy-gate.md` gains a short block at the top of "The acceptance stage" ("Plain commands
first"): run `python3 scripts/workflow_state.py --acceptance-gate <id>`, read `ready`, `blockers` and `dispositions` (the `stored_pr_fact` block is information the stage's query will replace);
`--finding-dispositions <id>` prints the same skeleton; steps 0 (`preflight-accept`) as today; then the existing steps.
**Every existing sentence stays**, including the Python call names, labelled "the specification": the existing tests pin
them (`test_satisfy_gate_specifies_the_acceptance_stage_and_no_longer_refuses_it` and the neighbours). A `ready: false`
report is the same stop as step 2's ("stop, write nothing"), and since no stored pull-request fact is a blocker it never
blocks the re-run that `satisfy-gate.md` step 2 and the row 38i remedy ("push the approved head and re-run
`/satisfy-gate acceptance`") ask for; `ready: true` still runs step 1, which queries GitHub and decides. The text states that this item's report is **read-only**, and that the completion (step 1 to 3's transaction)
is still the Python call until row 36's command exists. `state_writer: true` and `review-subject` stay.

### D-Tests

All in `payload/scripts/workflow_gate_policy_test.py`, class `TestAcceptanceGateReport` on `AcceptanceRepo` (a hand-built
scratch repository, a fake `run` for the one `ev.ready()` fact, no network), the CLI run as a subprocess like
`test_the_listing_option_prints_the_skeleton…`:

- **T1 no write**: for seven states (fresh, after-query, ready, missing, invalid, human, stale fact) plus each failure path
  of T7, the whole tree outside `.git` **with directories**, the refs and `HEAD` are identical before and after; the lock
  file `.ai-review/runtime/WORKFLOW_STATE.lock` exists or not exactly as before; the trap `gh` log is empty.
- **T2 gate verbatim**: the printed `gate` equals `ev.evaluate()` as JSON for the fresh and ready states; `blockers` has
  one `requirement_unmet` per unmet requirement among the three non-pull-request ids and never a met one; the unmet pull-request
  requirements appear in `stored_pr_fact.unmet` and in no blocker.
- **T3 dispositions** (item at `AWAITING_FUNCTIONAL_REVIEW`, which the test sets: `AcceptanceRepo` starts at
  `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`): two findings, none written: both keys with `label`, the skeleton equals `--finding-dispositions`',
  two blockers, `ready` false; one written: one left; all written: `missing` empty, `skeleton` null, `ready` true.
- **T4 the query is the stage's**: functional evidence recorded, no PR fact, phase `AWAITING_FUNCTIONAL_REVIEW`:
  `satisfiable` false, `satisfiable_after_query` true, `query_pending` true, no `requirement_unmet` blocker, `ready` true;
  `not_checked` lists the query.
- **T5 human gate**: a `human_approval: true` policy: `human_gate` blocker, `ready` false, `query_pending` false; an
  unreadable policy file: exit 0, the library's own result (`gate.source` `invalid`) printed verbatim.
- **T6 invalid dispositions**: a skeleton `"?"` entry: `invalid` holds the error text, `dispositions_invalid` blocker,
  exit 0, no traceback; `dispositions.missing` is `[]` and `skeleton` null.
- **T7 errors**: unknown id (`UnknownWorkItem`), no state file (`StateMissing`), corrupt state (`CorruptJsonError`), an empty id `--acceptance-gate ""` (`UnknownWorkItem`, not the publication-status path), a state file holding `{}` and one holding `[]` (`StateMalformed`), and a run in a directory that is not inside a Git repository (the class-name fallback, from `_run`'s `CalledProcessError`): exit 1, one JSON object with the error
  name, nothing else on stdout, no traceback, no write (T1's measurement covers each of them).
- **T8 interface**: two flags together exit 2; `--finding-dispositions` and `--plan-review-publication-status` print
  byte-identical output to their pre-change output on the same repository (captured by the test from the unchanged
  library functions); no flag exits non-zero.
- **T9 terminal and phase**: a `MILESTONE_COMPLETE` item: `work_item_terminal`, `ready` false. An otherwise-ready item at
  `IMPLEMENTING` and at `AWAITING_LOCAL_IMPLEMENTATION_REVIEW`: `phase_not_reachable`, `ready` false (measured: the
  predicate is false there and true at `AWAITING_FUNCTIONAL_REVIEW`); a registry that cannot be resolved:
  `registry_unresolvable`.
- **T10 command text**: `satisfy-gate.md` names `--acceptance-gate` before the first `satisfy_acceptance_gate`, keeps every
  pinned phrase and `state_writer: true`, says the report is read-only, and contains no `python3 -I` for this flag.
- **T12 the documented command line, exactly**: the test takes the command line from `satisfy-gate.md` (the line that
  names `--acceptance-gate`), substitutes the work item id and runs **that string** in the scratch repository with the
  candidate's `scripts/` directory; it exits 0 and prints the JSON report, and stderr holds no `ModuleNotFoundError`. (The
  model test, `test_the_listing_option_prints_the_skeleton…`, runs a plain command; this test pins the documented one.)
- **T11 parity with the stage** (the semantics guard): over the same six states, `ready` true if and only if
  `ws.satisfy_acceptance_gate(…, run=fake, resolve=fake)` on a copy completes. **Plus the stale-fact cases (B2)**: a fact
  stored at `AWAITING_FUNCTIONAL_REVIEW` with checks `pending`, with `state: none`, with `CHANGES_REQUESTED`, with failed
  checks, and for an older head, each with a fake query returning a green record: `ready` is true, the call completes, and
  `stored_pr_fact.unmet` lists the stale requirements. **Expectations on a refusal, separately**: a *disposition* refusal
  (`UndispositionedFindingsError`) leaves the state bytes unchanged; a *gate* refusal (`fresh`, `human`:
  `GateNotSatisfiableError`) raises after the transaction **and the state file changes** (the stored PR fact, possibly a
  reopening); the test asserts exactly that and no more. The phase is not covered by this parity (the library has no phase
  guard: it completes from `IMPLEMENTING`), so T9 owns it.

**Failure-only mutations** on a scratch copy, one per behaviour, each failing the named test (and, where it is also covered, T11's parity) and recorded: m1 the
report calls `state_transaction` or writes a file (T1); m2 a `met` flipped or a `detail` dropped from `gate` (T2); m3
`ready` ignores `missing` (T3); m4 a missing key dropped or the skeleton sorted differently (T3); m5 a pending-query
requirement reported as unmet, or an unmet one hidden (T4, T2); m6 human mode not a blocker (T5); m7 an invalid file
treated as complete or raised (T6); m8 unknown id exits 0, or the dispatch tests truthiness so an empty id falls through to the publication-status path (T7); m9 a corrupt state is a traceback (T7); m18 `StateMalformed` dropped, so `{}` or `[]` is a `KeyError`/`TypeError` traceback (T7); m19 the class-name fallback dropped or the dispatch moved after the shared `git rev-parse`, so a run outside a Git repository is a traceback (T7); m10 the flag
outside the exclusive group (T8); m11 an existing flag's output changed (T8); m12 a terminal item `ready` (T9); m13 the
command text drops the flag or moves it after the Python (T10); m14 `ready` true where the stage would refuse (T11); m15 a stored-fact pull-request requirement counted as a blocker
(T11, T2: B2); m16 the phase pre-flight dropped (T9); m17 the command text names the flag under `python3 -I` or the
exact line differs from a running one (T10, T12). m3, m6 and m7 also fail T11, whose parity covers the `missing`, `human` and `invalid` states.

### D-Docs

`docs/exit-codes.md`: the rows of the new flag (0 a report was printed, `ready` says whether to run the stage; 1 a JSON
`error`; 2 arguments); no milestone id. `payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md` (CP2): the release list and
one sentence that 2.26.0 adds a `workflow_state.py` flag that is not a protocol operation (protocol stays `1.5`).

### D-Release

2.26.0. `manifest.json`: `workflow_version`; the changed records (`satisfy-gate.md`, `workflow_state.py`,
`workflow_gate_policy_test.py`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`) take their `sha256` and
`size`; **no file is added or removed**, so counts and `distribution` do not move; `conformance.suites` by
`release.py manager-block --write`. `WORKFLOW_RELEASE` becomes 2.26.0 with its pinned assertions;
`tools/release/release_test.py` gets a 2.26.0 class, the 2.25.7 class gives up the current-release pins.
`docs/release-history.md`: the 2.26.0 row; the way back to 2.25.7 only removes the flag (nothing to migrate).

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w40-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): recompute `sha256` and `size` of every
record whose file differs (no record is added: counts and release-test counts do not move), measure `conformance.suites`,
commit in the clone, run the "Verification commands" of `docs/RELEASING.md`. `tools/release` tests use
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
CP2's stock `stage-conformance` run is the real proof.

## 3. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **No GitHub query in the report.** It keeps the item offline and read-only, at the price that a stale stored fact is
  reported in `stored_pr_fact`, not decided (`query_pending` is `gate.pending_query`, false for a stored fact). A `--query` option would add the forge trust surface; it is not planned.
- **`ready` is "nothing visible refuses"**, with `not_checked` saying what it does not claim; exit 0 whether ready or not
  (a worker reads the JSON); exit 1 for "not ready" would collide with the error code.
- **A flag, not a protocol operation** (0c): additive, no Controller work; row 36 revisits it for the write command.

## 4. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The report flag, its tests, the command text and the page | - | 2 | 1 |
| CP2 | Release 2.26.0 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The report flag, its tests, the command text and the page

**Files:** `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py`,
`payload/.claude/commands/satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): T1 to T12 written and run red against the unedited tree; mutations m1 to m19 each fail the
  named test on a scratch copy and the results are recorded.
- **The change** (D-Flag, D-Safety): `_acceptance_gate_report` and `_acceptance_gate_cli` in `workflow_state.py`, the third
  member of the exclusive group, dispatched right after `parse_args` and before the shared `git rev-parse` (D-Flag), nothing else; every existing test passes unmodified.
- **The command text and the page** (D-Command, D-Docs). `check_docs.py` stays clean.
- **No other mechanism:** `git diff 16e33d1 --stat -- payload` lists `workflow_state.py`, `workflow_gate_policy_test.py`
  and `satisfy-gate.md` only; `docs/ROADMAP.md` carries row 35 `Current` and row 36 `Next` (written with this plan; row 35
  becomes `Done` at acceptance).

**Verification:** the new tests as the suite runs them (the plain form, T12 included); D-Staging in a disposable clone: the nine suites from the staged
fixture, `tools/docs`, `check_docs.py`, `check-manager-block` (with `--manager-releases`), `tools/release` (zlib-ng
interpreter, no patch, no skip); the new tests again under the Manager's orphan rule (reaper).
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.26.0

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md`,
`tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.26.0 with its pinned assertions and the protocol-document edits (protocol stays `1.5`;
  the flag sentence of D-Docs).
- `manifest.json` 2.26.0 (D-Release): `workflow_version`, the changed records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.26.0 row and its "Last checked with" line; that of `docs/exit-codes.md` moves too.
- `tools/release/release_test.py`: a 2.26.0 class; the 2.25.7 class gives up the current-release pins.

**Verification:** the new tests again; the nine suites pass in a stock `release.py stage-conformance --commit HEAD`
fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs` are
clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 5. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its `.ai-review/`,
the real forge or the network.** Setup, once, under `$TMPDIR`
(`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w40-tmp`):
`base/` from `git archive 16e33d1 payload/scripts` and `cand/` from the working tree's `payload/scripts` (copy). A trap
`gh`, in a directory that is not under `/tmp`, `/var/tmp`, `/dev/shm` or `$TMPDIR` and not world-writable (mode 0755), put
first on `PATH`; it records any call, and **every flow ends by checking that its log is empty**:

```sh
mkdir -p "$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w40-bin"
cat > "$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w40-bin/gh" <<'EOF'
#!/bin/sh
echo "gh called: $*" >> "$TRAP_LOG"
exit 1
EOF
chmod 755 "$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w40-bin/gh"
export W40_BIN="$HOME/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w40-bin"
export TRAP_LOG="$W40_BIN/gh.log"; : > "$TRAP_LOG"   # flow.py reads the log unconditionally
```

`python3 -I flow.py <cand>/payload/scripts <cli-scripts> <case>` (`flow.py` itself may use `-I`: it inserts the candidate directory in `sys.path`) builds a scratch repository with the candidate suite's own
helper (`workflow_gate_policy_test.AcceptanceRepo`, a hand-built git repository; no network, the one stored PR fact comes
from the helper's fake `run`), then runs `python3 <cli-scripts>/workflow_state.py --acceptance-gate wi` (the plain form, **not** `-I`) in it with
`<cli-scripts>` = `base/payload/scripts` or `cand/payload/scripts`, prints the exit code and stdout, and a before/after
digest of the tree outside `.git`:

```python
import json, os, shutil, subprocess, sys, hashlib, tempfile
from pathlib import Path
cand, cli, case = sys.argv[1:4]; sys.path.insert(0, cand); sys.dont_write_bytecode = True
import workflow_gate_policy_test as t
def tree(root):  # directories included: a created empty directory shows
    return {str(p.relative_to(root)): ("dir",) if p.is_dir() else
            (p.stat().st_size, p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(Path(root).rglob("*")) if ".git" not in p.parts}
def cli_run(root, *args):
    env = dict(os.environ, PATH=os.environ["W40_BIN"] + ":" + os.environ["PATH"], TRAP_LOG=os.environ["TRAP_LOG"],
               PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, cli + "/workflow_state.py", *args], cwd=root, env=env, capture_output=True, text=True)
    print("exit", r.returncode); print(r.stdout.strip()); print("stderr:", r.stderr.strip()[:200])
with t.AcceptanceRepo() as ev:
    root = ev.root; rec = t.TestFindingDispositions(methodName="record"); state = root / "docs/ai-workflow/WORKFLOW_STATE.json"
    ev.set_state(phase="IMPLEMENTING" if case == "early" else "AWAITING_FUNCTIONAL_REVIEW")  # the helper starts at AWAITING_LOCAL_IMPLEMENTATION_REVIEW
    if case in ("ready", "human", "terminal", "missing", "partial", "invalid", "early"): ev.ready()
    if case == "stale": ev.ready(checks="pending")  # a stored fact whose checks are pending; the stage's query would find green
    if case == "stalenone": ev.flow(); ev.query([])
    if case == "after_query": ev.flow()
    if case in ("missing", "partial", "invalid"):
        keys = rec.record(ev, t.WI, "O1: add a test", "O2: second")
        if case != "missing": rec.write_dispositions(ev, {keys[0]: {"disposition": "fixed" if case == "partial" else "?"}})
    if case == "human": (root / t.POLICY_REL).write_text(json.dumps(t.HUMAN))
    if case == "terminal": ev.set_state(phase="MILESTONE_COMPLETE")
    if case == "oldflags": rec.record(ev, t.WI, "O1: add a test")
    if case == "malformed": state.write_text("[]")
    if case == "malformed_empty": state.write_text("{}")
    if case == "corrupt": state.write_text("{")
    if case == "nostate": state.unlink()
    if case == "nogit": shutil.rmtree(root / ".git"); root = Path(tempfile.mkdtemp(dir=os.environ["W40_BIN"]))  # not inside any Git repository: the class-name fallback
    if case == "badpolicy": (root / t.POLICY_REL).write_text("{")
    before = tree(root)
    if case == "unknown": cli_run(root, "--acceptance-gate", "nope")
    elif case == "emptyid": cli_run(root, "--acceptance-gate", "")
    elif case == "twoflags": cli_run(root, "--acceptance-gate", "wi", "--finding-dispositions", "wi")
    elif case == "oldflags": cli_run(root, "--finding-dispositions", "wi"); cli_run(root, "--plan-review-publication-status", "wi")
    else: cli_run(root, "--acceptance-gate", "wi")
    print("tree unchanged:", tree(root) == before, "| lock exists:", (root / ".ai-review/runtime/WORKFLOW_STATE.lock").exists(),
          "| gh calls:", Path(os.environ["TRAP_LOG"]).read_text().strip() or "none")
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `fresh` with base and cand (a scratch repository at `AWAITING_FUNCTIONAL_REVIEW`: automatic gate, current technical approval, no functional flow, no PR fact) | base: exit 2 and the argparse refusal `one of the arguments --plan-review-publication-status --finding-dispositions is required` (the required exclusive group is checked before unknown arguments, so the flag is not named; measured). cand: exit 0; `ready` false, `query_pending` true; blockers are one `requirement_unmet`, `functional_flows_passed`; `stored_pr_fact.unmet` lists `pr_fact_current`, `no_standing_pr_objection`, `ci_green` (information, not blockers); `gate.obtainable` is `["functional_evidence", "pr_review_result"]`; `tree unchanged: True`, `lock exists: False` (or as before), `gh calls: none` |
| 2 | `after_query` with cand (functional evidence recorded, no PR fact stored) | exit 0; `gate.satisfiable` false, `gate.satisfiable_after_query` true, `query_pending` true, `blockers` `[]`, `ready` true, `not_checked` names the GitHub query; tree unchanged, no `gh` call |
| 3 | `ready` with cand (flow and a stored current PR fact) | exit 0; all six requirements `met` with their details exactly as `ev.evaluate()` gives them; `ready` true, `query_pending` false, `dispositions.missing` `[]`, `skeleton` null; tree unchanged, no `gh` call |
| 4 | `missing` with cand (ready, two recorded Optional findings, no dispositions file) | exit 0; `dispositions.missing` holds the two keys in key order, each with `label` = `<key> (<stage> <role> round <n>): <first line>` (D-Flag); `skeleton.dispositions` is `{"<key>": {"disposition": "?"}}` for both; two `disposition_missing` blockers; `ready` false; the skeleton equals what `--finding-dispositions wi` prints; tree unchanged |
| 5 | `partial` and `invalid` with cand (the first key `fixed`; the first key left `"?"`) | `partial`: exit 0, `missing` holds only the second key, one `disposition_missing` blocker, `ready` false. `invalid`: exit 0, `dispositions.invalid` holds the error text naming the file, `missing` is `[]` and `skeleton` null, one `dispositions_invalid` blocker, no traceback, `ready` false |
| 6 | `human` with cand (a `GATE_POLICY.json` with `human_approval` true) | exit 0; `gate.mode` `human`, one requirement `human_gate` unmet; blockers `[human_gate]`; `query_pending` false; `ready` false |
| 7 | `terminal` and `early` with cand (the item at `MILESTONE_COMPLETE`; an otherwise-ready item at `IMPLEMENTING`) | `terminal`: exit 0; `phase` `MILESTONE_COMPLETE`; blockers begin with `work_item_terminal`; `ready` false. `early`: `flow.py` sets the phase to `IMPLEMENTING`; exit 0; blockers `[phase_not_reachable]` naming `IMPLEMENTING`; `ready` false |
| 7a | `stale` and `stalenone` with cand (a stored fact with checks `pending`; a stored `state: none`; the stage's query would be green) | exit 0 for both; `blockers` `[]`, `ready` true, `query_pending` false, `stored_pr_fact.unmet` non-empty (`ci_green`; `pr_fact_current`, `no_standing_pr_objection`, `ci_green`); tree unchanged, no `gh` call. Flow 11 then confirms the stage completes |
| 8 | `unknown`, `nostate`, `corrupt`, `malformed` (state `[]`), `malformed_empty` (state `{}`), `emptyid` (`--acceptance-gate ""`), `nogit` (a directory outside any Git repository) and `badpolicy` with cand | `unknown`, `nostate`, `corrupt`, `malformed` and `malformed_empty` exit 1 with one JSON object whose `error` is `UnknownWorkItem`, `StateMissing`, `CorruptJsonError`, `StateMalformed` and `StateMalformed`; `emptyid` exits 1 with `UnknownWorkItem` (not the publication-status path); `nogit` exits 1 with one JSON object whose `error` is the class name of the library's exception (`CalledProcessError`), nothing else on stdout and no traceback; none of these has a traceback; `badpolicy` exits 0 with `gate.source` `invalid` and `gate` equal to the library's result; `tree unchanged: True` for each, no `gh` call |
| 9 | `twoflags` with base and cand | both exit 2 with an argparse refusal (cand: "not allowed with argument"); nothing printed on stdout |
| 10 | `oldflags` with base and cand (`--finding-dispositions` and `--plan-review-publication-status` on the same repository) | stdout and exit code byte-identical between base and cand for both flags |
| 11 | parity: in a scratch repository from the `ready` case, run the report, then `ws.satisfy_acceptance_gate(root, "wi", now=…, run=<fake returning the helper's PR record>, resolve=<fake gh path>)`; repeat from `missing` | `ready` true then the call returns `{record, trailer}` and the item is `MILESTONE_COMPLETE`; from `missing` (`ready` false) the call raises `UndispositionedFindingsError` and `WORKFLOW_STATE.json` is byte-identical to its state before the call; from `fresh` or `human` (`ready` false) the call raises `GateNotSatisfiableError` and `WORKFLOW_STATE.json` **has changed** (the stored PR fact); from `stale` (checks pending stored) with a fake query returning a green record the report says `ready` true and the call returns `{record, trailer}` (the item is `MILESTONE_COMPLETE`) |
| 12 | `grep -n -e '--acceptance-gate' -e 'satisfy_acceptance_gate' payload/.claude/commands/satisfy-gate.md` (in the working tree: `cand/` holds `payload/scripts` only), then run the documented command line verbatim (cwd a scratch repository, `scripts/` the candidate's) | the flag is named in the acceptance stage before the first `satisfy_acceptance_gate`; the Python calls are still all named; the text says the report is read-only; the documented line is plain (no `-I`) and exits 0 with the JSON report, no `ModuleNotFoundError` |
| 13 | `git diff 16e33d1 --stat -- payload docs` in the working tree (CP1) | `workflow_state.py`, `workflow_gate_policy_test.py`, `satisfy-gate.md`, `docs/exit-codes.md`, `docs/ROADMAP.md`, the plan, registry, mapping, declaration and state; no `workflow_protocol.py`, no manifest |
| 14 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` and its checker, `check-manager-block` with `--manager-releases`, and the `tools/release` tests with the zlib-ng interpreter | all pass, no skip; the new tests run under the Manager's orphan rule (reaper) |
| 15 | (needs the full environment) scope: `git diff 16e33d1 --stat` at CP2 | CP2 adds `manifest.json`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/exit-codes.md` and `tools/release/release_test.py`; no file is added or removed from the manifest; the history row, manifest and page agree on 2.26.0 and the protocol is still `1.5` |

## 6. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #148 proposal, report | one plain command that evaluates the gate and prints requirements and missing dispositions by key | CP1 | D-Flag, T1 to T12 |
| #148 proposal, completion | one process doing the query, completion, findings record and floor | none: the next item | row 36, section 0d (two mechanisms) |
| #148 optional | `next-action` names the missing dispositions | none | declined, section 1; goes with row 36 |
| Row 35 | added `Current` with this plan, `Done` at acceptance; row 36 `Next` | CP1 | D-Docs |
| Release | `feat:` 2.26.0, protocol `1.5`, no Controller change | CP2 | D-Release, 0c |

## 7. Review round 1 (LOCAL_MODEL_PLAN_REVIEW, REVISE): disposition of each finding

Each premise was checked against the base tree (`16e33d1`) before it was applied.

| Finding | Verdict | Applied |
| --- | --- | --- |
| B1 `-I` cannot start the command | **accepted**, reproduced: `python3 -I payload/scripts/workflow_state.py --finding-dispositions x` ends in `ModuleNotFoundError: No module named 'workflow_fingerprint'` (`workflow_state.py` line 193 imports it with no path set) | plain form everywhere (D-Flag, D-Command, section 5, CP1); new T12 runs the documented line verbatim; m17 |
| B2 a stale stored fact makes `ready` false | **accepted**, read in `workflow_gate_policy.py` `_acceptance_pr` (lines 1902 to 1965): the PR requirements are `pr_fact_current`, `no_standing_pr_objection`, `ci_green`, `pr_approved`, recomputed from the stored `gate_evidence.pr`, which only the stage's query replaces | only the three non-PR requirements are blockers; the PR ones are `stored_pr_fact` information; stale-fact parity cases in T11; m15; flow 7a |
| I1 phase pre-flight missed | **accepted**, measured with `AcceptanceRepo`: `milestone_complete_gate_reachable` is false at `AWAITING_LOCAL_IMPLEMENTATION_REVIEW` and `IMPLEMENTING`, true at `AWAITING_FUNCTIONAL_REVIEW` | rows 1a and 1b in 0a; `phase_not_reachable` and `registry_unresolvable` blockers; T9, m16; the fixture phase is set in T3, T4, T11 and the flows |
| I2 T11 gate-refusal bytes | **accepted** | T11 and flow 11 separate the disposition refusal (bytes unchanged) from the gate refusal (stored fact written) |
| I3 `.ai-review/` already exists | **accepted** | T1 and `tree()` include directories and assert the lock file instead |
| I4 `label` | **accepted** | D-Flag and flow 4 agree on `_finding_label` |
| O1 malformed state | **accepted** | `StateMalformed` and a class-name fallback in D-Flag, T7, flow 8; `--finding-dispositions` is not changed |
| O2 `__pycache__` | **accepted** | D-Safety states the scope |
| O3 row 1 Writes cell | **accepted** | 0a row 1 says a reopening may be written |

## 8. Review round 2 (LOCAL_MODEL_PLAN_REVIEW, REVISE): disposition of each finding

Each premise was checked against the base tree (`16e33d1`); revision 3.

| Finding | Verdict | Applied |
| --- | --- | --- |
| I1 flow 1's base expectation | **accepted**, `workflow_state.py` line 20256: `add_mutually_exclusive_group(required=True)` is checked before unknown arguments | flow 1 expects the "one of the arguments" refusal |
| I2 flow 7 `early` never reaches `IMPLEMENTING` | **accepted**: `flow.py` skipped `set_state` for `early` | `flow.py` sets `IMPLEMENTING` for `early` |
| I3 error paths without tests | **accepted**, line 20260: `git rev-parse` runs after `parse_args` and before any flag | T7 gains `{}`, `[]` and the outside-Git run; m18 and m19; flow 8 gains `nogit`; D-Flag and CP1 say the dispatch precedes the shared `rev-parse`; the mapping names both mutations |
| O1 section 3 wording | **accepted** | section 3 points at `stored_pr_fact` |
| O2 "only its named test" | **accepted** | D-Tests says "the named test", and the m3/m6/m7 note names T11 |
| O3 `W40_BIN`/`TRAP_LOG` | **accepted** | section 5's setup exports both and creates the log |
| O4 `missing` when `invalid` | **accepted** | D-Flag states `[]` and null; T6 and flow 5 assert it |

## 9. Review round 3 (LOCAL_MODEL_PLAN_REVIEW, REVISE): disposition of each finding

Each premise was checked against the plan's own text (section 5's `flow.py` and flow table); revision 4.

| Finding | Verdict | Applied |
| --- | --- | --- |
| I1 `flow.py` truncates the report | **accepted**: `cli_run` printed `r.stdout.strip()[:3000]` and the sorted-key report puts `ready`, `query_pending` and `stored_pr_fact` after the large `gate` | the stdout cut is dropped; only stderr keeps a cut |
| I2 flows name cases the driver or setup lacks | **accepted**: `flow.py` had no `{}` case and `cand/` holds `payload/scripts` only | `malformed_empty` case, named in flow 8; flow 12 greps the working tree's `payload/.claude/commands/satisfy-gate.md` |
| O1 section 0a row 3 order | **accepted** | row 3 notes `/accept-milestone` step 2a's earlier position and the pinning test |
| O2 empty `--acceptance-gate ""` | **accepted**: the idiom `if args.finding_dispositions:` treats an empty id as absent | D-Flag dispatches on `is not None`; T7 and flow 8 (`emptyid`) cover `UnknownWorkItem` |
| O3 `REVIEW_REQUEST.md` says m1 to m17 | **accepted** | refreshed with the regenerated bundle (m1 to m19) |
