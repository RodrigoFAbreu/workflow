# Active Milestone

## Milestone

**Awaiting functional review.** W54: `bundle-revision-sections` (`process`, governing version `2.2`), Workflow 2.29.6, a `fix:`
patch, roadmap row 47 (`Current` until acceptance). Issue RodrigoFAbreu/workflow#142. Branch `milestone/bundle-revision-sections`.
The plan is `docs/ai-workflow/BUNDLE_REVISION_SECTIONS_PLAN.md` (revision 4). The previous item's narrative (W53,
`test-hardening-owner-points`) is in `docs/milestones/completed/` and in git history.

## Goal

An implementation bundle of revision N shows the test record and the fixes of every revision up to N, in a stable documented form.
The change is the text a worker follows (`milestone-implement.md`, `apply-implementation-review.md`, `apply-functional-review.md`,
`apply-pr-review.md`) and the contract a reviewer reads (`REVIEW_PROTOCOL.md`), with the tests that pin them. The generator
(`prepare-ai-review.sh`), the fingerprint, the state, the identifiers and every check do not change.

## Outcome

- CP1 (the form, the four commands, the contract, the tests) and CP2 (release 2.29.6: manifest, protocol constant, history row,
  release tests) are both `COMPLETE`.
- The plan was approved by gate policy; the technical approval is recorded by policy (`POLICY_SATISFIED`).
- Implementation review reached `APPROVE` at round 3 (implementation revision 3, reviewed head `1986d78`). Revision 3's bundle
  generation is recorded at `d7f7cff`.
- Nothing under `.claude/`, `scripts/`, `.workflow-manager/`, `.github/` or `CLAUDE.md` changed. `docs/ai-workflow` lists only this
  item's plan, registry, mapping, artifact and state files.

## Next action

Run the checklist below. Findings go to `.ai-review/bundle-revision-sections/feedback/FUNCTIONAL_REVIEW.md`, then
`/apply-functional-review`. When testing is clean, `/accept-milestone` is the acceptance command; every checkpoint is `COMPLETE`, so
it is available.

## Functional review checklist

**Scope.** The change is text in four command files and `REVIEW_PROTOCOL.md`, the tests that pin them, and release 2.29.6's
records. The generator, fingerprint and state scripts are byte-identical to the base commit `7a52f49`. No flow touches GitHub, a
forge, the network, `claude`, `codex` or `ssh`.

**Automated verification.** Nothing in `payload/`, `tools/`, `fixtures/`, `templates/` or `manifest.json` changed after the reviewed
head `1986d78`, so the last verification of that tree stands. Re-checked at `HEAD` for this checklist: the nine payload suites
from a staged fixture (flow 10 below) all pass (`workflow_acceptance_matrix_test.py` `OK`, 20 skipped; `workflow_protocol_test.py`
`OK`, 19 skipped; the other six `OK`, and `workflow_state_test.py` exits 0), and the flows 1 to 9.

### Setup

Run from the product clone root. `S` is a scratch directory outside the clone; no flow writes inside the clone.

1. `export S="$(mktemp -d)" REPO="$PWD" B=7a52f49f100b843f5b77ceaa66018a7c3397f7b2`
2. `mkdir -p "$S/base" "$S/cand" "$S/drv"`
3. `git -C "$REPO" archive "$B" payload | tar -x -C "$S/base"` and `git -C "$REPO" archive HEAD payload | tar -x -C "$S/cand"`
   (the payloads are then `$S/base/payload` and `$S/cand/payload`).
4. Save the driver below as `$S/drv/drive.py`. Run it only as `python3 -I "$S/drv/drive.py" <payload-dir> bundle old 1` (the form
   and the count are separate arguments: `old` or `new`, then `1`, `2` or `3`).

```python
import pathlib, shutil, sys, tempfile
payload = pathlib.Path(sys.argv[1]).resolve()
case = sys.argv[2:]
sys.path.insert(0, str(payload / "scripts"))
import workflow_fingerprint as wf

root = pathlib.Path(tempfile.mkdtemp(prefix="drive-"))
bd = root / "bundle"
bd.mkdir()

def write(name, text):
    (bd / name).write_text(text)

def old_bundle():
    write("REVIEW_REQUEST.md", "# Review request\n\nstage: implementation\n")
    write("IMPLEMENTATION_SUMMARY.md", "implementation_revision: 1\n\nWhat was built: the checkpoint.\n")
    write("TEST_RESULTS.md", "Ran the suite: OK\n")
    write("CONTEXT_FILES.txt", "a.py\n")
    write("PLAN.md", "# Plan\n")
    write("MANIFEST.md", "# Manifest\n")

def new_bundle(n):
    write("REVIEW_REQUEST.md", "# Review request\n\nstage: implementation\n")
    summ = [f"implementation_revision: {n}", ""]
    for k in range(1, n + 1):
        summ += [f"## Round {k}", f"- applied: finding {k}", ""]
    write("IMPLEMENTATION_SUMMARY.md", "\n".join(summ) + "\n")
    rec = []
    for k in range(1, n + 1):
        rec += [f"## Implementation revision {k}", f"- commit: {'a' * 40}", "- commands: python3 -m unittest", "- result: OK", ""]
    write("TEST_RESULTS.md", "\n".join(rec) + "\n")
    write("CONTEXT_FILES.txt", "a.py\n")
    write("PLAN.md", "# Plan\n")
    write("MANIFEST.md", "# Manifest\n")

def verdict(n):
    try:
        wf.assert_stage_completeness(bd, "implementation", implementation_revision=n)
        return "ok"
    except wf.StageCompletenessError as e:
        return "StageCompletenessError: " + str(e)

if case[0] == "bundle":
    form, n = case[1], int(case[2])
    old_bundle() if form == "old" else new_bundle(3)
    digest, _ = wf.compute_bundle_id(bd)
    before = digest
    print("digest", digest)
    print("verdict", verdict(n))
    after = wf.compute_bundle_id(bd)[0]
    print("dir-unchanged", before == after)
    text = (bd / "IMPLEMENTATION_SUMMARY.md").read_text()
    print("label-lines", sum(1 for l in text.splitlines() if l.startswith("implementation_revision: ")))
```

### Flows (offline; the sandbox can run 1 to 10)

Each row is run from the clone root, with `$S` set as above.

| Flow | Run | Expected output |
| --- | --- | --- |
| 1 | `git diff --quiet 7a52f49 -- payload/scripts/prepare-ai-review.sh payload/scripts/workflow_fingerprint.py payload/scripts/workflow_state.py; echo $?`, then `git diff 7a52f49 --stat -- payload` | `0`; the stat lists nine files: the four commands, `REVIEW_PROTOCOL.md`, `ORCHESTRATION_PROTOCOL.md`, `workflow_integration_test.py`, `workflow_protocol.py` and `workflow_protocol_test.py` |
| 2 | `git grep -c "Implementation revision" -- payload/.claude/commands payload/docs/ai-workflow/REVIEW_PROTOCOL.md`, then the same with `7a52f49` in place of the working tree (`git grep -c ... 7a52f49 -- ...`) | At `HEAD`: `1` in each of the four command files, `2` in `REVIEW_PROTOCOL.md` (the form and the rule that cites it). At `7a52f49`: no output. The count is unanchored: the headings sit indented inside the commands, so a `^` anchor matches nothing |
| 3 | `for f in milestone-implement apply-implementation-review apply-functional-review apply-pr-review; do sha256sum "payload/.claude/commands/$f.md"; done`, and the table at `payload/scripts/workflow_integration_test.py` (the four digest lines) | The four digests equal the table's entries: `2e5f544a…`, `698b8d86…`, `88e8bf5e…`, `526514e2…` |
| 4 | `python3 -I "$S/drv/drive.py" "$S/base/payload" bundle old 1` and the same with `$S/cand/payload` | Both: `digest 0be54dd2a60836bbae23dc7bb4cab39ab875c123357854e16a83fa460a5b15c1`, `verdict ok`, `dir-unchanged True` |
| 5 | `drive.py <payload> bundle new 3`, then `drive.py <payload> bundle new 2`, on base and cand | Both sides identical. At 3: `digest 8a8687c9…bd44`, `verdict ok`, `dir-unchanged True`. At 2: `verdict StageCompletenessError: …IMPLEMENTATION_SUMMARY.md states implementation_revision: 3, the work item's current counter is 2`, `dir-unchanged True` |
| 6 | Read the `label-lines` line of the `bundle new 3` run | `label-lines 1`: the three-section summary carries one label line, and the `## Round N` and `## Implementation revision N` headings do not match it |
| 7 | `grep -rn "TEST_RESULTS\|IMPLEMENTATION_SUMMARY" ~/.local/share/pipx/venvs/workflow-controller/lib/*/site-packages/controller` | `evidence.py` at 2203, 2258, 2296, 2680, 2742, 2784, 2799 (the file names and the recovery text) and `codex_carry.py` at 63 and 64 (a carried-file list). No parse of the text, no header or manifest field. Needs the installed Controller venv; if the sandbox cannot see it, run this on the host |
| 8 | `grep -n "^| 47 " docs/ROADMAP.md \| cut -c1-120`, `python3 -I tools/docs/check_docs.py`, `git grep -n "bundle-revision-sections" -- docs ':!docs/ACTIVE_MILESTONE.md' ':!docs/ai-workflow' ':!docs/ROADMAP.md' ':!docs/milestones'` | Row 47 is present and `Current`; `check_docs.py` exits `0`; the last command prints nothing (no shipped page names the id) |
| 9 | `git diff --name-only 7a52f49 -- .claude scripts .workflow-manager .github CLAUDE.md`, then `git diff --name-only 7a52f49 -- docs/ai-workflow` | The first prints nothing; the second lists only this item's plan, registry, mapping, artifact and state files |
| 10 | Stage the fixture: `python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"`, then the suites loop of `docs/RELEASING.md` ("The nine payload suites") with `TMPDIR="$S"` | All nine suites pass. Run them from inside `$S/fixture/scripts`, as CI does |

### Full environment only (not the sandbox)

- **11 (mutations).** In a scratch copy of the fixture, one of: remove the heading rule from one command; add a second
  `implementation_revision:` line to the sample summary; or restore the unscoped "ran in this session" sentence in the protocol. Each
  mutation fails only the tests it is meant to fail (`workflow_integration_test.py` T1 to T4, see the plan's D-Tests). Not run here.
- **12 (release tests).** `python -m unittest discover -s tools/release -p '*_test.py'` under the zlib-ng interpreter, and
  `python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`. Needs
  the pinned runtime described in `docs/RELEASING.md`. Not run here.
- **13 (installation).** `workflow-manager verify .`, with a release cache. Not run here.

### Checks only you can make

- **Read the new text as a worker would.** The four command files and the form in `REVIEW_PROTOCOL.md` ("Implementation
  revision N" sections, carried forward unchanged, the summary as one entry per round, the quarantine restore rule). The tests
  check the wording, not whether a worker following it writes a usable record.
- **The Controller recovery text.** `_implementation_bundle_recovery_steps` (`evidence.py` 2797 to 2800) still says "the exact commands
  and results of this round". The contract reads that as section N only. The plan calls for a Controller follow-up issue outside this
  item; confirm it exists before acceptance.

### Known limits

- The form is a worker convention pinned by tests. No check verifies a bundle has a heading per revision (D-NoCheck). A missing
  section is found by a reviewer, not refused by the generator.
- Only the text changes. No command was run end to end against a live worker in this checklist.
- Roadmap row 47 reads `Current` until acceptance.

### If testing finds something

Write the finding to `.ai-review/bundle-revision-sections/feedback/FUNCTIONAL_REVIEW.md` and run `/apply-functional-review`. A
same-scope fix takes its bounded branch; new or wider scope takes its broad branch, a `bundle-revision-sections-remediation-<n>`
child item.
