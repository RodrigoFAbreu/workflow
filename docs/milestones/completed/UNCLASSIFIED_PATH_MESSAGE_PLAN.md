# W39: Workflow 2.25.7 — an unclassified path is refused with a message that names the way forward (Revision 5)

- **Work item:** `unclassified-path-message` (`process`, governing version `2.2`)
- **Requested by:** the Manager Super Orchestrator, owner order of 2026-11-04: RodrigoFAbreu/workflow#146. Row 34 of
  `docs/ROADMAP.md` is added with this plan (`Current` now, `Done` at acceptance).
- **Issue:** RodrigoFAbreu/workflow#146 (no comments). **Branch:** `milestone/unclassified-path-message`
- **Base commit:** `dd565f0f5d223228984771c546378f3d9885a391` (main after #151: release source and own installation are
  2.25.6; automatic gates, default `2.2`, no `GATE_POLICY.json`, no backlog file, so the prose roadmap applies)
- **Plan revision:** 5 (rounds 1 to 4 of the local plan review: B01, I01, I02, O01 to O03, LPR-R2-I01, I02, O01, O02, LPR-R3-I01, I02, O01, O02 and LPR-R4-I01, O01 to O04 dispositioned, sections 8 to 11). Every checkpoint section carries its `<!-- CPn -->`/`<!-- /CPn -->` pair.

## 0. The defect, checked against main (Workflow 2.25.6)

Reproduced on `dd565f0` with the scratch harness of section 6 (a hand-built git repository, no state file, no network).

| Where | State on main | Disposition |
| --- | --- | --- |
| `classify_path` (`workflow_fingerprint.py` 1460) and `classify_path_implementation_stage` (1846) | **open**: `raise UnclassifiedPathError(path)`; `str(exc)` is the bare path, e.g. `other/mystery.txt` | **this item**: the two raise sites carry the new text |
| the six production paths that know the work item: `compute_review_content_id_plan_stage`, `…_plan_stage_at_commit`, `…_implementation_stage`, `…_implementation_stage_at_commit`, and the two that call `any_protected_path_dirty` / `any_protected_path_changed_since` before any of those: `technical_approval_gate_status` (`workflow_state.py` 14242) and `promote_legacy_work_item` (18862) | **open**: the same bare path escapes, though `work_item_id` is in scope | **this item**: each re-raises the same class with the declaration file resolved |
| the catch in `_classify_generation_record_interval` (`workflow_state.py` 15823) | **open**: re-wraps as `ProtectedPathInProvenanceIntervalError` with `classified 'unclassified', not excluded` and drops everything else | **this item**: the re-wrapped message appends the resolved text **in its own interval form** (D-Message): that check accepts only `excluded`, so the generic route would send the reader into a second refusal |
| the catches in `assert_plan_artifact_declaration_coverage` (4972, 4978) | already name each path, both stages and `PLAN_DECLARATION_NEXT_STEP` (which names `docs/ai-workflow/registry/<id>-artifacts.json`) | **unchanged**, byte for byte, pinned by a test: they do not hide the text, they replace it with their own |
| the catch in `_implementation_diff` (`workflow_fingerprint.py` 3590) | `continue`: no message exists | unchanged |

**Out of scope (said plainly):** what is refused (no classification changes); the declaration format and the generated
template; any command file; any other exception; the exception's code and every exit code. The plan-time gaps #40
closed stay closed.

## 1. Goal

Ship Workflow 2.25.7, a **`fix:` patch** (the manifest's version change and the pull-request title agree), with one
mechanism: **an unclassified path is refused with a message that names the way forward.** The message names (a) the
path, (b) the artifact-declaration file that must list it, (c) the sanctioned route that adds it. Nothing else moves:
the class `UnclassifiedPathError` (an `Exception`, same module), where it is raised, who catches it, every exit code and
every other output stay as they are. **Every other output stays byte-identical**; the only byte-different outputs are
`str()` of an `UnclassifiedPathError`, the message of the `ProtectedPathInProvenanceIntervalError` raised at 15823
for an unclassified path, and any message that quotes one (e.g. `PlanApprovalClosureProofError`, which includes
`{type(exc).__name__}: {exc}`, `workflow_state.py` 2950 to 2958).

### Hard limits (the owner's sizing rule)

- One mechanism (one message builder, used at the two raise sites, six wrapped callers and one catch); the plan stays under
  about 350 lines. One review surface. **Two checkpoints** (CP1 the change, tests and page; CP2 the release 2.25.7).
- This repository's own installation (`.claude/`, `scripts/`, managed `docs/ai-workflow/` documents, `.workflow-manager/`,
  managed blocks, the conformance workflow) stays untouched; the shipped copies under `payload/` change.

## 2. Facts this plan relies on (re-read at `dd565f0`)

- `UnclassifiedPathError(Exception)` has no `__init__`; both raise sites pass the path as the only argument. Existing
  tests assert `assertRaises(UnclassifiedPathError)` and `assertIn(path, str(exc))` only; no test compares the whole text.
- The classifiers receive only the path and the sets, never a work item, so at the raise site the item is unknown. The
  four `compute_review_content_id_*` functions named in section 0 receive `work_item_id` and call the classifiers
  (directly or through `assert_all_changed_paths_classified_*` and `_implementation_stage_protected_changed_paths`).
- The sanctioned routes are those of `payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, "Repairing an artifact declaration
  after an approval": before the plan approval, edit the declaration and run `/milestone-plan` again; after it, a
  `plan_stage` edit goes through a new plan revision. The command that starts it from an approved plan is
  `/request-plan-amendment` (step 4 of its command file: "the very next `/milestone-plan [work-item-id]` invocation
  resumes it"), then `/milestone-plan`, plan review and `/approve-review plan`. `/apply-plan-review` is **not** that
  route: it refuses at `IMPLEMENTING` (`PlanReviewPhaseNotPlanStageError`), and at `AMENDING_PLAN` it applies only a
  `REVISE` verdict, while an approved plan's latest plan verdict is an `APPROVE` (`FeedbackStatusNotApplicableError`); an `implementation_stage` edit leaves the plan-stage id unchanged, so it needs no amendment, and
  after the technical approval it goes through `mark_technical_approval_stale` and a post-fix round. `/request-plan-amendment`
  is legal only at `IMPLEMENTING` and `SELF_REVIEWING_IMPLEMENTATION` (`_AMENDMENT_REQUEST_ALLOWED_PHASES`,
  `workflow_state.py` 14802, refused elsewhere with `WrongPhaseForAmendmentRequestError`) and is **user-only** (the agent
  never invokes it). The message therefore never tells a reader to "run" it. "Neither command is admitted" at any other phase holds for two-stage items (governing versions `"2.1"` and `"2.2"`, every live item here): `assert_plan_review_entry_phase` returns early for a `"1"` item and admits it at any phase. No `"1"` item is live in this repository and the failure is safe (the reader is told to ask the user), so the text is not qualified further (LPR-R4-O03).
- `_classify_generation_record_interval` accepts only `excluded`; the branch below the 15823 catch refuses `protected`.
  `classify_path` has no protected prefixes at the plan stage: `protected_paths` entries are exact, but
  `excluded_prefixes` is honoured (`workflow_fingerprint.py` 1446; this item's own declaration excludes `payload/`,
  `tools/`, `fixtures/`, `templates/` that way). At the plan stage a deliverable is **excluded** (protecting a
  not-yet-written one raises `AbsentProtectedPathError`, and protecting an existing one stales the plan approval at
  every later implementation edit); it is protected at the implementation stage.

## 3. Design decisions

### D-Message: one builder, two forms

`workflow_fingerprint.unclassified_path_message(path, work_item_id=None, stage="plan", interval=False)` returns, for the
stage that refused (`stage` is `"plan"` at `classify_path` and `"implementation"` at `classify_path_implementation_stage`,
so the message names only the list that refused, which also keeps it short; recorded as a choice in section 4):

- **Known item:** `<path> is not classified by the <stage> stage of the artifact declaration of work item <id>, docs/ai-workflow/registry/<id>-artifacts.json. <route>`
- **Unknown item:** `<path> is not classified by the <stage> stage of the artifact declaration of the work item being worked, docs/ai-workflow/registry/<work_item_id>-artifacts.json (the work item is not known where this path was classified, so <work_item_id> stands for its id). <route>`
- **`<route>`, plan stage** (known item shown; the unknown form drops the ` <id>` after each command):
  `Add the path to plan_stage of that file as excluded, an exact path in excluded_paths or a directory prefix in excluded_prefixes (it is protected only if it is one of the plan's own documents; a deliverable is excluded here and protected at the implementation stage). At PLANNING, REVISING_PLAN, AMENDING_PLAN, AWAITING_LOCAL_PLAN_REVIEW, AWAITING_MANUAL_EXTERNAL_PLAN_REVIEW or AWAITING_PLAN_APPROVAL, whether or not an amendment is open: edit the file and run /milestone-plan <id> again. At IMPLEMENTING or SELF_REVIEWING_IMPLEMENTATION the plan is approved and the edit needs a new plan revision: the user runs /request-plan-amendment <id>, then /milestone-plan <id>, plan review and the plan approval (/approve-review plan, or /satisfy-gate when the plan gate is automatic); at any other phase neither command is admitted, so tell the user. See REVIEW_PROTOCOL.md, "Repairing an artifact declaration after an approval".`
  The route is qualified **by phase, not by approval history** (LPR-R3-I01): an open amendment has an approved plan on record and is at `AMENDING_PLAN` or a ready plan-review phase, where `/milestone-plan` is the admitted step. The three lists are exactly `PLAN_REVIEW_NON_READY_PHASES`, `PLAN_REVIEW_READY_PHASES` (`workflow_state.py` 316 to 321) and `_AMENDMENT_REQUEST_ALLOWED_PHASES` (14802); "neither command" is true only elsewhere (`AWAITING_FUNCTIONAL_REVIEW`, `AWAITING_EXTERNAL_IMPLEMENTATION_REVIEW`, `MILESTONE_COMPLETE` and the like, all refused by `assert_plan_review_entry_phase`).
- **`<route>`, implementation stage:**
  `Add the path to implementation_stage of that file, as a path or a directory prefix: protected for a deliverable, excluded for repository territory. The edit needs no plan amendment (the plan-stage id does not change); before the technical approval re-run the command that refused, after it the edit goes through mark_technical_approval_stale and a post-fix round. See REVIEW_PROTOCOL.md, "Repairing an artifact declaration after an approval".`
- **Interval form** (`interval=True`, used only at the 15823 catch, always with `stage="implementation"`: that catch belongs to the implementation-stage check, so its first sentence reads `... is not classified by the implementation stage of the artifact declaration of work item <id>, ...` like every other implementation-stage form): the same first sentence, then
  `A provenance interval may contain only excluded paths: exclude it in implementation_stage only if it is repository territory (a change to the declaration stales the technical approval, never widen an exclusion to avoid a re-review); for a deliverable the content needs a new implementation round, not a declaration entry. See REVIEW_PROTOCOL.md, "Repairing an artifact declaration after an approval".`

One principle: *the refusal says where the fact lives and how to change it; it never says more than the docs or the
code already do.* The two claims that appear in no document today (an exact path or a prefix per stage; a deliverable
is excluded at the plan stage) are pinned to the code instead: T9 classifies a prefix and a deliverable path at each
stage and asserts the clause is true of what the classifier returns. Every command named exists (`milestone-plan.md`,
`approve-review.md`, `satisfy-gate.md`, `request-plan-amendment.md`); `/apply-plan-review` is deliberately **not** named. 
`/request-plan-amendment` is presented as the user's command, only at the two phases that admit it, and always followed
by `/milestone-plan`. A test (T6) pins the three phase lists in the text to `PLAN_REVIEW_NON_READY_PHASES`, `PLAN_REVIEW_READY_PHASES` and
`_AMENDMENT_REQUEST_ALLOWED_PHASES`, and the order to the command file, so text and gate cannot drift. A reader at any other
phase is told plainly that neither command is admitted and to tell the user; no route is invented for them.

### D-Sites: where the text comes from

1. The two raise sites call `raise UnclassifiedPathError(unclassified_path_message(path, stage="plan"|"implementation"), path, stage)`; the class gets
   `__init__(self, message, path=None, stage=None)` that stores `self.path`, `self.stage` and calls `super().__init__(message)` (so `args`, `str()`,
   pickling and `except` clauses are unchanged in kind).
2. A context manager `naming_work_item(work_item_id)` (in `workflow_fingerprint`) wraps the body of each of the four
   entry points, the `any_protected_path_dirty` call in `technical_approval_gate_status` and the
   `any_protected_path_changed_since` call in `promote_legacy_work_item`: on an `UnclassifiedPathError` with a `path` it
   re-raises the same class with the known-item text for `exc.stage` (`from None`); anything else passes through. No behaviour other
   than the message changes. The direct classifier calls with no item (tests, helpers) keep the unknown form.
3. At 15823 the message becomes `<commit> in the provenance interval touches '<path>', classified 'unclassified', not
   excluded: ` followed by `unclassified_path_message(path, work_item_id, stage="implementation", interval=True)`. The exception class and the
   `classified` words stay as before.

### D-Tests

All offline, no network, no `gh`; they run as any user under `python3` here and need no zlib-ng or 3.12. **Tests first**, run
red against the unedited tree, then green. Exact strings are asserted, before (the bare path) and after.

| Test | Proves | File |
| --- | --- | --- |
| T1 | `classify_path("other/mystery.txt", …)` raises with the exact unknown-item plan-stage text (route as above); `.path` is set; the class and `args` length are unchanged | `workflow_fingerprint_generalization_test.py` |
| T2 | the same for `classify_path_implementation_stage`, with the implementation-stage route | same |
| T3 | each of the four entry points, on a scratch repository with one undeclared file, raises the exact known-item text of its own stage (`demo-item`), one subtest per entry point | same |
| T4 | `_classify_generation_record_interval` re-wraps with the exact `ProtectedPathInProvenanceIntervalError` text, commit and path included, naming `the implementation stage` (never `the plan stage`), ending in the interval form (no `/milestone-plan`, no `protected for a deliverable`; says a deliverable needs a new implementation round) | `workflow_state_test.py` |
| T6 | the plan-stage route, read by phase: the phases it lists for "edit the file and run `/milestone-plan` again" are exactly `PLAN_REVIEW_NON_READY_PHASES` and `PLAN_REVIEW_READY_PHASES`, and `assert_plan_review_entry_phase(…, command="/milestone-plan")` admits each of them (so also at `AMENDING_PLAN` with an approval on record); it names `/request-plan-amendment` only with every phase of `_AMENDMENT_REQUEST_ALLOWED_PHASES`, names the user as the one to run it, follows it with `/milestone-plan <id>` then plan review and the plan approval, `/approve-review plan` or `/satisfy-gate` when the plan gate is automatic (the order of the command file), names `/satisfy-gate` only in that position, says plainly that only other phases admit neither command (a sample of them, on a `"2.2"` item, is refused by both guards), and never names `/apply-plan-review`; it never says "run /request-plan-amendment" bare | `workflow_state_test.py` |
| T7 | (setup in the shared module-level `gate_case(ws, name)`, which uses only its `ws` argument and names that `dd565f0`'s scripts already have, so section 6 can run it on the base tree) `technical_approval_gate_status` on a scratch item with a dirty unclassified path raises the exact known-item text (not the placeholder form) | `workflow_state_test.py` |
| T8 | `promote_legacy_work_item` with an unclassified path changed since the reviewed commit raises the exact known-item text | `workflow_state_test.py` |
| T9 | the declaration advice is true as run: the plan-stage clause offers `excluded` (path or prefix) and never `protected for a deliverable`; `classify_path` with a deliverable path in `excluded_paths`, and with its directory in `excluded_prefixes`, returns `excluded`; the implementation-stage clause offers `protected` for a deliverable and `excluded` for territory, each as a path or prefix, and `classify_path_implementation_stage` agrees | `workflow_fingerprint_generalization_test.py` |
| T5 | no change where nothing is refused: a classified path returns what it did; a plain `ValueError` raised inside an entry point passes through `naming_work_item` unchanged (same object and text); `TOOLING_AMBIENT_EXCLUDED_PATHS` still excludes; the coverage refusal (4972/4978) text is byte-identical to the base text; the class is still a direct subclass of `Exception` | `workflow_fingerprint_generalization_test.py` |

**Failure-only mutations** (each on a scratch copy, one at a time; the named test fails and the unmutated tree passes):
m1 `classify_path` raises the bare path (T1); m2 `classify_path_implementation_stage` bare (T2); m3 to m6 one entry point
without `naming_work_item` (T3, one subtest each); m7 the 15823 message without the appended text (T4); m8 the known form
keeps the `<work_item_id>` placeholder (T3, T4); m9 the unknown form drops "the work item is not known" (T1, T2); m10 the
route sentence loses `/request-plan-amendment` (T1, the plan-stage subtests of T3, T6; T2 asserts the implementation-stage route, which never has it); m11 `naming_work_item` swallows a non-matching exception (T5,
a plain `ValueError` through an entry point). m12 `technical_approval_gate_status` without `naming_work_item` (T7); m13 `promote_legacy_work_item` without it (T8); m14 the route says bare "run /request-plan-amendment <id>" or drops one allowed phase (T6); m15 the interval site uses the generic route (T4); m16 the plan-stage route drops `/milestone-plan` after `/request-plan-amendment`, or names `/apply-plan-review` (T6); m17 the plan-stage clause says `protected for a deliverable` or drops the prefix (T9, T1); m18 a raise site passes the wrong `stage` or a wrapped caller drops `exc.stage` (T1 to T3); m19 the 15823 site drops `stage="implementation"` so the interval text says the plan stage (T4); m20 the plan-stage route lists a phase outside `PLAN_REVIEW_NON_READY_PHASES`/`PLAN_REVIEW_READY_PHASES`, or says "neither command" at `AMENDING_PLAN` (T6). The class also runs under the Manager's orphan rule (the reaper).

### D-Docs

`docs/common-problems.md`: the existing entry "UnclassifiedPathError when generating a bundle" (line 27) is rewritten in
place, not duplicated: what the message names and the stage- and phase-qualified route in the message's words (the plan-stage phase lists, "neither command" only where both refuse, the two declaration clauses of T9 and the order `/request-plan-amendment`, `/milestone-plan`, plan review, `/approve-review plan` or `/satisfy-gate` when the plan gate is automatic) (no internal milestone
id; `check_docs.py` stays clean). The entry's last sentence stays as it is ("For a new `GATE_POLICY.json` on an older declaration, exclude the `docs/ai-workflow/` prefix"): specific advice the message does not carry (LPR-R4-O04). The plan-time entry (line 203) is untouched. "Last checked with" moves in CP2.

### D-Release

2.25.7, a **`fix:` patch**. `manifest.json` `workflow_version` 2.25.7; the changed records (`workflow_fingerprint.py`,
`workflow_state.py`, the two test files, `workflow_protocol.py` and its test, `ORCHESTRATION_PROTOCOL.md`) take their
`sha256` and `size`; no file is added or removed, so counts and `distribution` do not move; `conformance.suites` is
measured by `release.py manager-block --write`. `WORKFLOW_RELEASE` becomes 2.25.7 with its pinned assertions and the
protocol document's example (protocol stays 1.5); `tools/release/release_test.py` gets a 2.25.7 class and the 2.25.6
class gives up the current-release pins. `docs/release-history.md`: the 2.25.7 row; the way back to 2.25.6 restores the
bare message (no state, no archive and no engine data changes).

### D-Staging

CP1 changes shipped files whose manifest records move only at CP2, so stock `stage-conformance` cannot stage it. CP1
verifies in a disposable clone under
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w39-tmp`
(procedure of `docs/milestones/completed/RETENTION_ARCHIVE_PLAN.md`, D-Staging): a scratch script recomputes `sha256`
and `size` of every record whose file differs from its record (no record is added, so the counts and the release-test
counts do not move), measures `conformance.suites` with `release.py manager-block --release-dir <scratch> --write`,
commits in the clone and runs the "Verification commands" of `docs/RELEASING.md` from there. `tools/release` tests use
`/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv/bin/python`.
CP2's stock `stage-conformance` run is the real proof.

## 4. Open decisions (for the plan reviewer and the owner)

None of the rows of `docs/TECHNICAL_DECISIONS.md` is touched. Choices that may be reversed:

- **The unknown form** (direct callers of a classifier) names `<work_item_id>` and says the item is not known, as the
  order asks, rather than threading `work_item_id` through every helper (a wider change). The six wrapped callers (four
  entry points, `technical_approval_gate_status`, `promote_legacy_work_item`) are every production path that knows the item;
  the remaining direct classifier calls are tests and helpers.
- **One phase-qualified route.** The raise sites do not know the phase, so the message states each documented route with
  the phase it is legal at, and the interval site gets its own form.
- **A `stage` argument** (LPR-R2-O02, accepted): the raise sites know which stage refused, so the message carries only that stage's clause. The exception stores `stage` beside `path` so the wrapped callers re-raise the right clause. `PLAN_DECLARATION_NEXT_STEP` keeps its older, looser wording and stays out of scope (changing it is a separate item).
- **The coverage refusal (4972/4978) is left alone**: it already names path, stage, declaration (with `<id>`) and the fix.

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | The message, tests and page | - | 2 | 1 |
| CP2 | Release 2.25.7 | CP1 | 2 | 1 |

<!-- CP1 -->
### CP1 — The message, tests and page

**Files:** `payload/scripts/workflow_fingerprint.py`, `payload/scripts/workflow_state.py`,
`payload/scripts/workflow_fingerprint_generalization_test.py`, `payload/scripts/workflow_state_test.py`,
`docs/common-problems.md`, `docs/ROADMAP.md`.

- **Tests first** (D-Tests): T1 to T9 written and run red against the unedited tree; mutations m1 to m20 each fail the
  named tests on a scratch copy and the results are recorded.
- **The change** (D-Message, D-Sites): the builder, the class's `__init__`, the context manager, the two raise sites,
  the six wrapped callers and the 15823 message. Every existing test passes unmodified; the diff of the two scripts
  touches only those places.
- **The page** (D-Docs). `check_docs.py` stays clean.
- **No other mechanism:** `git diff dd565f0 --stat -- payload` lists the two scripts and the two test files only;
  `docs/ROADMAP.md` carries row 34 as `Current` (written with this plan; `Done` at acceptance).

**Verification:** the new tests under `python3`; D-Staging in a disposable clone: the nine suites from the staged
fixture, `tools/docs`, `check_docs.py`, `check-manager-block` (with `--manager-releases`), `tools/release` (zlib-ng
interpreter, no patch, no skip); the new tests again under the Manager's orphan rule.
<!-- /CP1 -->

<!-- CP2 -->
### CP2 — Release 2.25.7

**Files:** `manifest.json`, `payload/scripts/workflow_protocol.py`, `payload/scripts/workflow_protocol_test.py`,
`payload/docs/ai-workflow/ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md`, `docs/common-problems.md`,
`tools/release/release_test.py`.

- `WORKFLOW_RELEASE` becomes 2.25.7 with its pinned assertions and the matching protocol-document edits (protocol 1.5).
- `manifest.json` 2.25.7 (D-Release): `workflow_version`, the changed records, the posture, `conformance.suites`.
- `docs/release-history.md`: the 2.25.7 row and its "Last checked with" line; that of `docs/common-problems.md` moves too.
- `tools/release/release_test.py`: a 2.25.7 class; the 2.25.6 class gives up the current-release pins.

**Verification:** the new tests again; the nine suites pass in a stock `release.py stage-conformance --commit HEAD`
fixture; `release.py build --commit HEAD` succeeds; `check-manager-block` (with `--manager-releases`) and `tools/docs`
are clean; `workflow-manager verify .` is clean; the tools tests pass in the zlib-ng environment.
<!-- /CP2 -->

## 6. Functional review (for the later checklist)

Commands from `docs/RELEASING.md`, "Verification commands". **Nothing runs against the real repository, its `.ai-review/`,
the real forge or the network.** Setup, once, under `$TMPDIR`: `base/` from `git archive dd565f0 payload/scripts` and
`cand/` from the working tree's `payload/scripts` (copy). For the `gate` case only, copy `cand/payload/scripts/workflow_state_test.py` over `base/payload/scripts/workflow_state_test.py` before running it: `gate_case` is new with T7 and T8 and base's copy cannot contain it, and the candidate's test module must still import against base's scripts (it does, because `gate_case` uses only its `ws` argument and names base already has; flow 7 fails if it does not). Save the harness outside any repository as `flow.py` and run
`python3 -I flow.py <base|cand>/payload/scripts <case>` for `direct`, `plan`, `impl`, `same`, `interval`, `gate`. An unknown case exits nonzero. It builds its
own scratch git repository (one committed file `src/a.txt`, one undeclared `other/mystery.txt`), and for `interval` the
suite's own scratch helpers (a throwaway repository, no state of this one).

```python
import os, re, subprocess, sys, tempfile
from pathlib import Path
scripts, case = sys.argv[1], sys.argv[2]; sys.path.insert(0, scripts)
sys.dont_write_bytecode = True
import workflow_fingerprint as wf
def git(root, *a): return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
def show(exc): print(type(exc).__module__ + "." + type(exc).__qualname__); print(str(exc))
root = Path(tempfile.mkdtemp(prefix="flow-repo-"))
git(root, "init", "-q"); (root / "src").mkdir(); (root / "src/a.txt").write_text("a\n"); git(root, "add", "-A"); git(root, "commit", "-qm", "base")
base = git(root, "rev-parse", "HEAD")
(root / "other").mkdir(); (root / "other/mystery.txt").write_text("x\n")      # a path no declaration names
sets = (frozenset({"src/a.txt"}), {}, {}), ({}, {"src/": "p"}, {}, {})
def run(fn):
    try: fn(); print("no refusal")
    except wf.UnclassifiedPathError as e: show(e)
if case == "plan":      # the plan-stage entry points, the item known
    run(lambda: wf.compute_review_content_id_plan_stage(root, base, "process", "demo-item", 1, *sets[0]))
    git(root, "add", "-A"); git(root, "commit", "-qm", "c")
    run(lambda: wf.compute_review_content_id_plan_stage_at_commit(root, base, "HEAD", "process", "demo-item", 1, *sets[0]))
elif case == "impl":   # the implementation-stage entry points, the item known
    run(lambda: wf.compute_review_content_id_implementation_stage(root, base, "process", "demo-item", *sets[1]))
    git(root, "add", "-A"); git(root, "commit", "-qm", "c")
    run(lambda: wf.compute_review_content_id_implementation_stage_at_commit(root, base, "HEAD", "process", "demo-item", *sets[1]))
elif case == "direct":  # the two classifiers called with no work item
    run(lambda: wf.classify_path("other/mystery.txt", *sets[0]))
    run(lambda: wf.classify_path_implementation_stage("other/mystery.txt", *sets[1]))
elif case == "same":    # what is classified, and the class, are unchanged
    print(wf.classify_path("src/a.txt", *sets[0]), wf.classify_path_implementation_stage("src/a.txt", *sets[1]))
    print(wf.classify_path(".workflow-manager/installation.json", *sets[0]))
    print(wf.UnclassifiedPathError.__mro__[1].__name__, wf.UnclassifiedPathError.__module__)
elif case == "interval":  # the provenance-interval catch: needs the test suite's own scratch helpers
    import unittest, workflow_state_test as t, workflow_state as ws
    with t.ScratchRepo() as repo:
        WI = "demo-item"
        t._write_test_artifacts_declaration(repo, WI); t._seed_base_provenance_state(repo, WI)
        p = repo.commit("protected fix", filename="src/Foo.kt")
        state = t._provenance_state(WI, reviewed_implementation_head=p, implementation_revision=1)
        t._commit_state_only(repo, WI, state, "record gen", trailers=t._record_trailers(WI, 1))
        t._write_and_commit(repo, "other/mystery.txt", "???\n", "add unclassified")
        t._run(["git", "rm", "-q", "other/mystery.txt"], cwd=repo.root); t._run(["git", "commit", "-q", "-m", "remove unclassified"], cwd=repo.root)
        try:
            ws.verify_implementation_provenance_recovery(repo.root, state | {"work_item_id": WI, "work_item_type": "process"}, base_commit=repo.base, head=repo.head())
        except Exception as e:
            print(type(e).__name__); print(re.sub(r"\b[0-9a-f]{40}\b", "<commit>", str(e)))
elif case == "gate":    # the two further callers, item known: needs the suite's own scratch helpers
    import workflow_state_test as t, workflow_state as ws
    for name in ("technical_approval_gate_status", "promote_legacy_work_item"):
        print("case-gate:", name)
        try: print("no refusal" if t.gate_case(ws, name) is None else "")   # T7/T8's own setup, module-level in workflow_state_test.py; on base, the candidate's copy of that file (section 6 setup)
        except wf.UnclassifiedPathError as e: show(e)
else:
    sys.exit("unknown case: " + case)
```

| Flow | Do | Expect |
| --- | --- | --- |
| 1 | `direct` with base and cand (the two classifiers, no work item) | base prints `other/mystery.txt` twice (the class `workflow_fingerprint.UnclassifiedPathError`). cand: the same class, and each message is the unknown-item text of D-Message for its stage (plan, then implementation): the path, `docs/ai-workflow/registry/<work_item_id>-artifacts.json`, the sentence that the work item is not known, and the route sentence |
| 2 | `plan` with base and cand (`compute_review_content_id_plan_stage` and `…_at_commit`, item `demo-item`) | base: the bare path, twice. cand: the known-item text twice, naming `docs/ai-workflow/registry/demo-item-artifacts.json`, `/milestone-plan demo-item` at the non-ready and ready plan-review phases (including `AMENDING_PLAN`), and `/request-plan-amendment demo-item` as the user's command at the two admitting phases only, followed by `/milestone-plan demo-item`, plan review and the plan approval (`/approve-review plan` or `/satisfy-gate`); no `/apply-plan-review` |
| 3 | `impl` with base and cand (the two implementation-stage entry points) | base: the bare path, twice. cand: the known-item implementation-stage text twice (`implementation_stage`, `protected for a deliverable, excluded for repository territory`, no `/request-plan-amendment`) |
| 4 | `interval` with base and cand (an unclassified path added then removed inside a provenance interval) | base: `<commit> in the provenance interval touches 'other/mystery.txt', classified 'unclassified', not excluded` and nothing more. cand: the same sentence, then `: other/mystery.txt is not classified by the implementation stage of the artifact declaration of work item demo-item, docs/ai-workflow/registry/demo-item-artifacts.json.` and the interval form (a deliverable needs a new implementation round); the class `ProtectedPathInProvenanceIntervalError` is the same |
| 5 | `same` with base and cand | identical byte for byte: `protected protected`, `excluded`, `Exception workflow_fingerprint` (a classified path, the ambient exclusion and the class's base are unchanged) |
| 6 | `git diff dd565f0 --stat -- payload docs` in the working tree (CP1) | the diff lists the two scripts, the two tests, `docs/common-problems.md`, `docs/ROADMAP.md`, the plan, registry, mapping and declaration, and state; no command file, no `docs/gates.md` |
| 7 | `gate` with base and cand (`gate_case(ws, name)`, the module-level setup T7 and T8 share in `workflow_state_test.py`: `technical_approval_gate_status` on an item with a dirty undeclared path, and `promote_legacy_work_item` with an undeclared path changed since the reviewed commit) | base (with the candidate's `workflow_state_test.py` copied over its own, section 6 setup; it imports against base's scripts and the case exits 0): the bare path, twice. cand: the known-item implementation-stage text twice, naming `demo-item`, not the placeholder |
| 8 | (needs the full environment) the nine payload suites from a staged fixture, `tools/docs` and its checker, `check-manager-block` with `--manager-releases`, and the `tools/release` tests with the zlib-ng interpreter | all pass, no skip; the new tests run under the Manager's orphan rule (reaper) |
| 9 | (needs the full environment) scope: `git diff dd565f0 --stat` at CP2 | CP2 adds `manifest.json`, `workflow_protocol.py`, its test, `ORCHESTRATION_PROTOCOL.md`, `docs/release-history.md` and `tools/release/release_test.py`; the history row, manifest and page agree on 2.25.7 |

## 7. Disposition of every item

| Item | What | Checkpoint | Note |
| --- | --- | --- | --- |
| #146 (a) | the refusal names each undeclared path | CP1 | T1 to T4 |
| #146 (b) | it names the declaration file, resolved from the item when known, said when not | CP1 | D-Message, T1 to T4, m8, m9 |
| #146 (c) | it names the sanctioned route, stage- and phase-qualified (by phase: `/milestone-plan` at the plan-stage phases, open amendment included; at the two admitting phases the user's `/request-plan-amendment` then `/milestone-plan`, plan review, `/approve-review plan` or `/satisfy-gate`; "neither command" only elsewhere; post-fix round after the technical approval), and the declaration advice is true at each stage | CP1 | D-Message, T6, T9, m10, m14, m16 to m20 |
| #146 (b) | known-item text at the two further callers | CP1 | T7, T8, m12, m13; flow 7 |
| Row 34 | class, code, exit code, who catches it and every other output unchanged | CP1 | T5, m11 |
| Row 34 | the release is a `fix:` patch, 2.25.7 | CP2 | D-Release |
| what is refused, the declaration format, any command file, any other exception | not here | out of scope | section 0 |

The artifact declaration `docs/ai-workflow/registry/unclassified-path-message-artifacts.json` is generated by
`workflow_state.generate_artifacts_declarations` and then extended by hand for `payload/`, `tools/`, `fixtures/`,
`templates/`, `manifest.json`, `docs/common-problems.md`, `docs/ROADMAP.md` and `docs/release-history.md`, as the earlier
retention items' were; every path a checkpoint's **Files** paragraph names is classified at both stages.

## 8. Round 1 of the local plan review (applied in revision 2)

| Finding | Disposition |
| --- | --- |
| B01 | accepted, checked: `_AMENDMENT_REQUEST_ALLOWED_PHASES` (`workflow_state.py` 14802) and `REVIEW_PROTOCOL.md` 615 to 652. D-Message rewritten phase-qualified; T6, m14 |
| I01 | accepted, wrapped: `technical_approval_gate_status` (14242) and `promote_legacy_work_item` (18862); sections 0, 4, D-Sites; T7, T8, m12, m13 |
| I02 | accepted: interval form of D-Message (a deliverable needs a new implementation round; no exclusion to avoid a re-review); T4, m15 |
| O01 | accepted: section 1 |
| O02 | accepted: D-Docs rewrites the entry at line 27 |
| O03 | accepted: the route says exact path at the plan stage |

## 9. Round 2 of the local plan review (applied in revision 3)

| Finding | Disposition |
| --- | --- |
| LPR-R2-I01 | accepted, checked: `assert_plan_review_entry_phase` refuses `/apply-plan-review` at `IMPLEMENTING`; at `AMENDING_PLAN` it needs a `REVISE` verdict; `request-plan-amendment.md` names `/milestone-plan [work-item-id]` as the resume. D-Message states the order and names `/apply-plan-review` nowhere; other post-approval phases are told plainly neither command is admitted; section 2, T6, m14, m16, flows 2 and 3, section 7 (c) moved with it |
| LPR-R2-I02 | accepted, checked against `classify_path` (1446) and this item's own declaration: each stage has its own clause (plan: `excluded`, path or prefix, `protected` only for the plan's own documents; implementation: `protected` for a deliverable, `excluded` for territory, path or prefix); T9, m17; D-Docs carries the same wording; the looser `PLAN_DECLARATION_NEXT_STEP` stays out of scope and the principle is restated to include "or the code" |
| LPR-R2-O01 | accepted: row 34 of `docs/ROADMAP.md` rewritten to the revised route and "six callers" |
| LPR-R2-O02 | accepted: the `stage` argument and `exc.stage`; section 4, T1 to T3, m18 |
| Missing tests | T6 (I01), T9 (I02), flow 7 for T7 and T8 (later flows renumbered) |

## 10. Round 3 of the local plan review (applied in revision 4)

| Finding | Disposition |
| --- | --- |
| LPR-R3-I01 | accepted, checked against `workflow_state.py` 316 to 321 and 14802: the route is qualified by phase (non-ready and ready plan-review phases: edit and `/milestone-plan`; the two amendment phases: `/request-plan-amendment` first; "neither command" only elsewhere). T6 pins the three lists to the code's sets and to `assert_plan_review_entry_phase`; m20; D-Docs, flow 2, section 7 (c), row 34 and mapping R1 moved with it |
| LPR-R3-I02 | accepted: (a) CP1 names T1 to T9 and m1 to m20; (b) one interval definition: D-Sites passes `stage="implementation"`, flow 4 names the implementation stage, T4 asserts it, m19; (c) m10 now names T1, T3's plan-stage subtests and T6; (d) the harness prints a `gate` case and an unknown case exits nonzero; (e) T5's row asserts the plain `ValueError` |
| LPR-R3-O01 | accepted: the route says `/approve-review plan` "or `/satisfy-gate` when the plan gate is automatic" |
| LPR-R3-O02 | not applied, with a reason: round 2 (LPR-R2-I02) required the stage's declaration clause to be in the message and T9 pins it to the classifier; moving the parenthesis to `docs/common-problems.md` would drop what the reader at the refusal needs and the page is not read where the error appears. The unknown-form message is longer by the phase split only; the owner's order sets no size limit |

## 11. Round 4 of the local plan review (applied in revision 5)

| Finding | Disposition |
| --- | --- |
| LPR-R4-I01 | accepted, checked: base's `workflow_state_test.py` cannot contain `gate_case` (new with T7 and T8). Section 6's setup copies the candidate's `workflow_state_test.py` over base's before the `gate` case; `gate_case` is required to use only its `ws` argument and names `dd565f0` already has (T7's row), so flow 7's base half prints the bare path twice and exits 0; flow 7 says so |
| LPR-R4-O01 | accepted: `satisfy-gate.md` joins the list of commands that exist; D-Docs, section 7 (c), row 34 of `docs/ROADMAP.md`, mapping R1 and T6's row name `/satisfy-gate` beside `/approve-review plan`; flow 2's repeated fragment is fixed |
| LPR-R4-O02 | not applied, with a reason: `REVIEW_PROTOCOL.md` is a shipped payload document, so editing it adds a manifest record and a third surface to a one-mechanism `fix:` patch whose scope the owner fixed (section 1); the stale clause ("`/apply-plan-review` (or `/milestone-plan` again)" in step 2, and no mention of `/request-plan-amendment`) is filed as a follow-up for the next release that touches that document |
| LPR-R4-O03 | accepted as a recorded limit in section 2 ("neither command is admitted" holds for two-stage items; a `"1"` item is admitted at any phase; none is live here); T6's refusal sample uses a `"2.2"` item |
| LPR-R4-O04 | accepted: D-Docs keeps the entry's last sentence about `GATE_POLICY.json` |
