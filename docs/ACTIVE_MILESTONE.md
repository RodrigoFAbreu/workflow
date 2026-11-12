# Active Milestone

## Milestone

**In progress.** W45: `plain-command-malformed-state` (`process`, governing version `2.2`), branch `milestone/plain-command-malformed-state`,
roadmap row 40 (RodrigoFAbreu/workflow#155, items 1 to 3). The plan is `docs/ai-workflow/PLAIN_COMMAND_MALFORMED_STATE_PLAN.md`
(revision 1, approved by gate policy). The previous milestone, W44 `acceptance-phase-guard` (Workflow 2.29.1), is complete.

## Goal

Workflow 2.29.2 (a `fix:` patch): the plain acceptance commands refuse a malformed state or registry with one JSON object instead of a
traceback. The shared state context (`_plain_command_state`) tells an absent state file (`StateMissing`) from one holding JSON `null`
(`StateMalformed`); `--finding-dispositions` uses it and answers every state refusal as one JSON object; the acceptance gate's
reachability blocker turns a malformed registry into `registry_unresolvable`. The protocol stays 1.5; the Controller does not change.

## Checkpoints

- CP1 (the shared state context, the dispositions flag and the blocker's catch, tests, command text and pages): complete.
- CP2 (release 2.29.2): implemented; verified state below.

CP1 changes: `payload/scripts/workflow_state.py`, `payload/scripts/workflow_gate_policy_test.py` (ten new tests), `payload/.claude/commands/satisfy-gate.md`,
`docs/exit-codes.md`, `docs/ROADMAP.md` (row 40).

CP2 changes: `manifest.json` (2.29.2: `workflow_version`, the six changed records' `sha256`/`size` and `rationale` sentence, the
gate-policy suite count 412 to 422, the posture), `payload/scripts/workflow_protocol.py` (`WORKFLOW_RELEASE`), its test,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md` (the 2.29.2 row), `docs/exit-codes.md` ("Last checked
with"), `tools/release/release_test.py` (`PlainCommandMalformedStateReleaseTest`; the 2.29.1 class gives up the current-release pins).

CP2 verification (scratch clone with the CP2 tree committed, D-Staging): `release.py stage-conformance` and the nine suites, `tools/release`
tests (323, zlib-ng interpreter), `tools/docs` tests and `check_docs.py`, `release.py build`, `check-manager-block` with `--manager-releases`;
`workflow-manager verify .` in this repository.

## Next action

Functional review (`AWAITING_FUNCTIONAL_REVIEW`): run the checklist below, then place findings at the path it names. Once testing is
clean, `/accept-milestone` is the only acceptance command.

## Functional review checklist

Product head under review: `997162c`, implementation revision 2 (reviewed implementation head `e6b77fc`, post-fix bundle `0db3ea5`).

**Automated verification, re-run at HEAD `997162c`** (after the LIR-R1-001 fix in `e6b77fc`, which changed `manifest.json` and
`docs/release-history.md` after the CP2 run):

- `release.py stage-conformance --commit HEAD` into a fresh fixture, then the nine suites from inside it: all exit 0.
- `tools/release` tests under the pinned zlib-ng Python (3.12.14, `zlib_ng` 1.0.0): 323 OK.
- `tools/docs` tests: 34 OK. `check_docs.py`: exit 0.
- `check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`: exit 0, the 2.29.2 block matches.
- `workflow-manager verify .`: exit 0, "installation matches workflow 2.29.1" (expected: 2.29.2 is neither published nor pinned in `workflow-manager` yet).

### Setup

1. Start from the repository root with a clean tree. Nothing below writes inside the product clone: every write goes under a scratch
   `$TMPDIR`. The flows need only `python3`, `git` and that directory. Each case is its own `git init` repository with no remote, so no
   origin is needed.
2. Build the base and candidate script trees (absolute paths):

   ```sh
   export TMPDIR="$(mktemp -d)"
   A8=a8d5b1140d7117d21d12c5027fbf9d0d9b56ec5d
   mkdir -p "$TMPDIR/base" "$TMPDIR/cand/payload/.claude"
   git archive "$A8" payload/scripts payload/.claude/commands | tar -x -C "$TMPDIR/base"
   cp -a payload/scripts "$TMPDIR/cand/payload/"
   cp -a payload/.claude/commands "$TMPDIR/cand/payload/.claude/"
   export BASE="$TMPDIR/base/payload/scripts" CAND="$TMPDIR/cand/payload/scripts"
   ```

3. Harness: copy verbatim the heredoc from `cat > "$TMPDIR/flow.py" <<'PY'` to its closing `PY` in
   `docs/ai-workflow/PLAIN_COMMAND_MALFORMED_STATE_PLAN.md`, section 5, then define the `run` helper from the same section:
   `run() { for s in "$BASE" "$CAND"; do echo "== $(basename "$(dirname "$(dirname "$s")")")"; python3 -I "$TMPDIR/flow.py" "$s" "$@"; done; }`.
4. The `gh` stand-in: the harness prepends `W45_BIN` to `PATH` and counts the lines of `GH_LOG`. Create the stand-in as section 5 gives it
   (it logs its arguments and exits 1) in the directory `W45_BIN` names, and set `GH_LOG` to its log. If the sandbox forbids that
   directory, use a writable one of its own and note the change. The harness counts only the stand-in it prepends, so also record any
   line the sandbox's own `gh` log gains during the run.

### Flows runnable in the sandbox (offline, against the stand-in `gh`): 1 to 10

Each flow is run against base, then candidate. Expect `gh calls=0` and `files changed=none` unless stated.

1. `run absent all`. Base: `--finding-dispositions` traceback; the other four `StateMissing`. Candidate: all five
   `{"error": "StateMissing"}` (the writers add `state_changed: false`), rc 1, no traceback.
2. `run null all`. Base: dispositions traceback; the other four `StateMissing` (the file exists). Candidate: all five `StateMalformed`;
   the `out=` digest of `--finding-dispositions` equals that of `--acceptance-gate`.
3. `for c in list object string items-null item-null; do echo "-- $c"; run $c all; done`. Candidate: five `StateMalformed` each, no
   traceback; the other four flags' `out=` digests equal the base's.
4. `for c in empty notjson unknown; do echo "-- $c"; run $c all; done`. Candidate: `empty` and `notjson` give five `CorruptJsonError`
   each; `unknown` gives five `UnknownWorkItem`; for `unknown` every `out=` digest equals the base's.
5. `run outside all; run empty-id --finding-dispositions --acceptance-gate`. Candidate: `outside` gives `CalledProcessError` from all
   five; `empty-id` gives `UnknownWorkItem` from both flags. No traceback, no files changed.
6. `for c in cps-str cps-null cps-list-int cps-missing deps-int regpath-int regpath-list approval-str; do echo "-- $c"; run $c --acceptance-gate --satisfy-acceptance; done`.
   Base: both flags rc 1, a bare `TypeError`, `KeyError` or `AttributeError` object, no `code`. Candidate: `--acceptance-gate` rc 0
   with a report, `ready` false, and `registry_unresolvable` first among the blockers. `--satisfy-acceptance` rc 1 with
   `{"code": "registry_unresolvable", "error": "AcceptancePreflightError", "state_changed": false}`; the only file changed is
   `.ai-review/runtime/WORKFLOW_STATE.lock`.
7. Golden comparison: `for c in wellformed implementing complete unknown reg-absent reg-null reg-notjson cps-sealed-ok; do run $c all > "$TMPDIR/o-$c"; done`,
   then `for c in wellformed implementing complete unknown reg-absent reg-null reg-notjson cps-sealed-ok; do diff <(sed -n '2,6p' "$TMPDIR/o-$c") <(sed -n '8,12p' "$TMPDIR/o-$c") && echo "$c identical"; done`.
   Expect every case to print `identical` and no `diff` output. Lines 2 to 6 are base, lines 8 to 12 candidate.
8. `run cps-implementing --acceptance-gate --satisfy-acceptance; run reg-absent --satisfy-acceptance`. Candidate: `registry_unresolvable`
   for `cps-implementing` (checked before `phase_not_reachable`), the same code as `reg-absent`. Base: a bare `TypeError` for
   `cps-implementing`.
9. Mutants. For each of `a`, `b`, `c`: `cp -a "$TMPDIR/cand" "$TMPDIR/mut-<x>"`, then apply exactly one literal replacement to
   `$TMPDIR/mut-<x>/payload/scripts/workflow_state.py`, asserting it matches once:
   - `a`: `if (repo_root / DEFAULT_STATE_PATH).exists():` becomes `if False:`
   - `b`: `except Exception as exc:  # a malformed registry shape` becomes `except ZeroDivisionError as exc:  # a malformed registry shape`
   - `c`: `if args.finding_dispositions is not None:` becomes `if args.finding_dispositions:`

   Use the one-liner `python3 -I -c 'import sys; p, x, y = sys.argv[1:4]; s = open(p).read(); assert s.count(x) == 1; open(p, "w").write(s.replace(x, y))' <file> <old> <new>`.
   Then run mutant `a` with flow 2 (`null all`), mutant `b` with flow 6, and mutant `c` with flow 5, passing the mutant's
   `payload/scripts` as the first argument to `python3 -I "$TMPDIR/flow.py"`. Expect each mutant to reproduce the base on its own
   flow (`a`: `StateMissing` for `null`; `b`: the bare `TypeError`; `c`: the `KeyError` traceback for the empty id) and the other two
   flows to pass as candidate.
10. `for s in "$BASE" "$CAND"; do tr '\n' ' ' < "$s/../.claude/commands/satisfy-gate.md" | grep -c 'never a traceback'; done; grep -c 'finding-dispositions' docs/exit-codes.md`.
    Expect base `0`, candidate at least `1`, and `docs/exit-codes.md` at least `3`.

### Full-environment flows: 11 to 13 (not runnable in the sandbox as written)

11. Nine suites from a staged fixture (`release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"`, then the loop in
    `docs/RELEASING.md`, "Verification commands"). Needs only `python3` and `git`, so the sandbox may run it. Already run at HEAD in the
    verification above: all exit 0. Expect `TestPlainCommandMalformedState` (`payload/scripts/workflow_gate_policy_test.py`, line 7123)
    among the gate-policy tests, and `workflow_integration_test.py` unedited.
12. Pinned zlib-ng runtime: the `tools/release` tests, the `tools/docs` tests, `check_docs.py` and `check-manager-block`. Needs the
    Python 3.12 environment with `zlib_ng` 1.0.0, which the sandbox does not have. Already passed at HEAD in the verification above.
13. Scope: `git diff a8d5b1140d7117d21d12c5027fbf9d0d9b56ec5d HEAD --stat` lists 17 files: the plan, the registry, the mapping, the
    artifacts file and `WORKFLOW_STATE.json` under `docs/ai-workflow/`, the release and doc files, `manifest.json`, the shipped
    `payload/` files, `tools/release/release_test.py`, and this file. Nothing under the repository's own `.claude/`, `scripts/`,
    `.workflow-manager/` or managed `docs/ai-workflow/` documents. `git diff ... -- payload/scripts/workflow_integration_test.py` is
    empty, and `workflow_gate_policy_test.py` has 244 insertions and no deletions.

### Test data

Nothing to seed. The harness builds each case in its own scratch repository, `$TMPDIR/f-<case>`, from the `CASES` table in its heredoc.

### Known limitations and out of scope

- `--plan-review-publication-status` keeps its traceback rows (the Controller-adjacent status, not in this patch). No flow tests it.
- No shape validator for the state or the registry. A well-formed JSON state or registry that is wrong in some other way is answered
  as before, not by a new check.
- A deliberate exit-code change: `--acceptance-gate` on a malformed registry now exits 0 with a report, where 2.29.1 exited 1 with a
  bare error. A script must read `blockers`.
- No forge: no flow touches a real `gh`, a pull request, or `/satisfy-gate` against GitHub. The gh-call count proves only that none
  was made.
- Orchestration Protocol 1.5 and the Controller are unchanged. Release 2.29.2 is neither published nor installed here (installed: 2.29.1).

### Findings and next steps

- Place findings at `.ai-review/plain-command-malformed-state/feedback/FUNCTIONAL_REVIEW.md`. `/apply-functional-review` routes each one:
  the bounded branch for a same-scope fix, the broad branch (a `plain-command-malformed-state-remediation-<n>` child item) for new or
  wider scope.
- Once testing is clean, `/accept-milestone` is the only acceptance command. It requires every checkpoint in this item's registry to be
  `COMPLETE` (CP1 and CP2 are). If a checkpoint is outstanding, finish it with `/milestone-implement` and return to this gate. No command
  records acceptance of a partial round.
