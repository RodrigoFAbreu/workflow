# Active Milestone

## Milestone

**Awaiting functional review.** W57: `command-wording-pins` (`process`, governing version `2.2`), branch `milestone/command-wording-pins`,
roadmap row 50 (RodrigoFAbreu/workflow#190 points 1 and 2, #123 point 6). The plan is `docs/ai-workflow/COMMAND_WORDING_PINS_PLAN.md`
(revision 1, approved by gate policy). The change is a release, Workflow 2.29.8, a `fix:` patch: the `Publish` workflow publishes it once the
pull request is merged to `main`.

## Goal

Wording only: shipped text says what the code does. Three command files and the two `cross_device` refusals of `workflow_retention.py`
change; nothing the code does changes. Not taken: #190 point 3 (owner decision) and #190 point 4 (not in the brief).

## Outcome

- CP1 (the wording, its pins, roadmap row 50) and CP2 (release 2.29.8) are `COMPLETE`.
- The plan and the technical approval are `CURRENT`, both recorded by gate policy.
- Automated verification: `.ai-review/command-wording-pins/current/TEST_RESULTS.md` (implementation revision 1, commit `1e63824`) records
  the nine suites, the `tools/release` and `tools/docs` tests, `check-manager-block`, `build`, `check-title` and the seven mutations, all as expected.
  Since that commit only `docs/ACTIVE_MILESTONE.md` and `docs/ai-workflow/WORKFLOW_STATE.json` have changed: no code, payload or installation file.

## Functional review checklist

The flows run offline. They write only under a scratch directory and never inside the repository.

### Setup

- Repository root, branch `milestone/command-wording-pins`, clean working tree. The base commit is
  `c2068ca7ec4c04c262b706375d0e07c616b15538`.
- Tools: `git`, the system `python3`, and `zstd` on `PATH`. Without `zstd` the two engine tests skip, which is not a pass.
- `S=$(mktemp -d)`. Every Python command below runs with `-B` (or `PYTHONDONTWRITEBYTECODE=1` for `unittest`), so that no `__pycache__`
  is written into the repository.
- No forge call, no network, no `claude`, `codex` or `ssh` is needed. F1 to F7 run in the functional sandbox. F8 and F9 need the pinned
  zlib-ng interpreter and the `workflow-manager` repository, so they are user-only and not sandbox flows.
- The fixture that `stage-conformance` writes under `$S` is a fresh `git init` repository, not a clone of the product. Writes to it are
  writes outside the product clone.

### Test data

Nothing is seeded. Build the staged fixture from `HEAD` once, from the repository root:

```bash
python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"
```

Expect exit 0. F5 and F6 run from `"$S/fixture/scripts"` (F6's `.claude/commands` edits are made in `"$S/fixture"`). F1 to F4 and F7
run from the repository root and only read.

### Flows

**F1. Scope.** `git diff --stat c2068ca -- payload`

Expect the three command files, `payload/scripts/workflow_retention.py`, and the two test suites (`workflow_integration_test.py`,
`workflow_state_completion_obligations_test.py`). Also expect `workflow_protocol.py`, its test and `ORCHESTRATION_PROTOCOL.md` (the release-version lines).

**F2. The repository's own installation is untouched.** `git diff --name-only c2068ca -- .claude scripts .workflow-manager .github CLAUDE.md`

Expect no output.

**F3. The engine change is wording only.** `git diff c2068ca -- payload/scripts/workflow_retention.py | grep '^[-+][^-+]'`

Expect two hunks, both inside the `cross_device` refusals: the selection step and the `EXDEV` of the rename. Only string literals change. The new
next step reads: "run the engine by hand with an --archive-root on the repository's file system (archive there, then remove), or leave the folder;
nothing was moved".

**F4. The command wording.** Read `git diff c2068ca -- payload/.claude/commands/`.

- `apply-pr-review.md`, step 4 of "Durable ordering": every round is said to be ordinary (`record_bundle_generation` is called without an
  outcome). Sections and entries 1 to `N-1` are restored from the newest `current.rejected-*` sibling, checked to run from 1 to `N-1`. With no
  quarantine, the entry says so. Check: `git diff c2068ca -- payload/.claude/commands/apply-pr-review.md | grep '^+' | grep -c same_content`
  prints `0`.
- `apply-implementation-review.md` step 7 and `apply-functional-review.md` (bounded branch, step 4): the parenthesis gains "a `"same_content"`
  round keeps `N` and rewrites section `N` with its new commit and results, appending none".

**F5. The pins pass on the new wording.** In `"$S/fixture/scripts"`:

```bash
python3 -B workflow_integration_test.py TestCommandWordingPins
python3 -B workflow_state_completion_obligations_test.py RetentionCrossDeviceWording
```

Expect `Ran 2 tests` and `OK` for each, with no skips.

**F6. Each pin fails on the old wording.** Work in `"$S/fixture"` only, never in the product clone. For each row, make the one edit, run the
named class, expect the named failure, then re-stage the fixture before the next row.

| Row | Edit in `"$S/fixture"` | Run | Expect |
| --- | --- | --- | --- |
| m1 | `.claude/commands/apply-pr-review.md`: replace `checking they run from 1 to `N-1`` with `checking nothing` | `workflow_integration_test.py TestCommandWordingPins` | the c1 subtest for "checking they run from 1 to `N-1`" fails, and the golden-hash test for `apply-pr-review.md` |
| m2 | same file: replace `with no quarantine say so in the entry` with `say nothing of any quarantine` | same | the c1 subtest for the quarantine clause fails, and the golden-hash test for that file |
| m3 | same file: delete the sentence that begins "This command records every round" and ends "rewrites an earlier section." | same | both c1 subtests for that file fail, and the golden-hash test |
| m4 | `.claude/commands/apply-implementation-review.md`: delete `; a `"same_content"` round keeps `N` and rewrites section `N` with its new commit and results, appending none` | same | the c2 subtest for that file fails, and its golden-hash test |
| m5 | `.claude/commands/apply-functional-review.md`: the same deletion | same | the c2 subtest for that file fails, and its golden-hash test |
| m6 | `scripts/workflow_retention.py`, the selection-step literal near line 1752: restore the `c2068ca` text (`git show c2068ca:payload/scripts/workflow_retention.py \| grep -n "keep the archive store"`) | `workflow_state_completion_obligations_test.py RetentionCrossDeviceWording RetentionRemove RetentionTestPins` | e1 fails (both subtests), and `RetentionRemove` and `RetentionTestPins` stay `OK` |
| m7 | the same file, the `EXDEV` literal near line 1887: the same restoration | same | e2 fails, and `RetentionRemove` and `RetentionTestPins` stay `OK` |

The unmutated baseline is `OK` for both class sets. Golden-hash failures under m1 to m5 are expected by design.

**F7. Read-only release checks.** From the repository root, with the system `python3`, bytecode off:

```bash
python3 -B tools/docs/check_docs.py
python3 -B tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json
python3 -B tools/release/release.py check-title "fix: make the bundle-record wording of the apply commands and the cross_device next step say what the code does" --agree --head 1e63824
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/docs -p '*_test.py'
```

`--agree` compares `HEAD^1 -> HEAD`; the branch tip is a docs-only commit with no version change, so the title is checked against `1e63824`, the commit that bumps 2.29.7 -> 2.29.8 (functional-review finding F7: a checklist correction, no code change).

Expect exit 0 for each of the first three commands. The first prints nothing on success. The second prints
`ok: 2.29.8 carries a valid manager block that matches the measurement`. The third prints `impact=patch` and `version 2.29.7 -> 2.29.8 (patch) agrees with the title`.
The `unittest` run: 34 tests, `OK`.

**F8. Orphan check (user-only).** In `"$S/fixture/scripts"`, using the `workflow-manager` clone:
`python3 -I -S /home/rodrigo/Workspace/workflow-manager/tests/parallel/reaper.py --report "$S/R.json" --chunk-id wording -- python3 -B workflow_state_completion_obligations_test.py RetentionCrossDeviceWording`

Expect chunk status 0 and orphans only `[git]` processes, all `exited`.

**F9. Full environment (user-only).** The nine suites from the staged fixture, as `docs/RELEASING.md` "Verification commands" gives them; the
`tools/release` tests with the zlib-ng interpreter (`python -m unittest discover -s tools/release -p '*_test.py'`); `release.py build --commit HEAD --out "$(mktemp -d)"`
under the same interpreter; and `workflow-manager verify .`.

Expect all of them to pass. `workflow-manager verify .` reports `installation matches workflow 2.29.7`. That is correct: this repository's own
installation is not changed by this item.

### Known limitations and out-of-scope behaviour

- No behaviour changes. The `cross_device` code and error message are unchanged; only the next step text differs.
- #190 point 3 is not taken (owner decision). #190 point 4 is not in the brief.
- W1 does not copy the `same_content` rule into `apply-pr-review.md`. Every round there is ordinary, so the sentence states that
  (`docs/ai-workflow/COMMAND_WORDING_PINS_PLAN.md`, D-Pr-Outcome). This is a deliberate departure from the issue's literal request.
- This repository's own installation (`.claude/`, `scripts/`, managed documents, the managed blocks) stays at 2.29.7 until the Manager's
  lock and install pull requests. The retention pages, the Manager and the Controller are untouched.
- Acceptance edits `docs/ROADMAP.md` row 50 from `Current` to `Done`. This checklist does not.

## Next action

Run the flows above. Put any findings in `.ai-review/command-wording-pins/feedback/FUNCTIONAL_REVIEW.md`. If testing is clean, run
`/accept-milestone`, the only acceptance command. If a finding needs a fix, run `/apply-functional-review`.
