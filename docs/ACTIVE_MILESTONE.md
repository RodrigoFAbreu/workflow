# Active Milestone

## Milestone

**In progress** (implementing). W27: `retention-report` (`process`, governing version `2.2`), branch
`milestone/retention-report`, roadmap row 27b (RodrigoFAbreu/workflow#84, step 2). Plan:
`docs/ai-workflow/RETENTION_REPORT_PLAN.md` (revision 2, approved by gate policy). The goal is Workflow 2.20.0, a
`feat:` minor that adds one read-only script, `scripts/workflow_retention.py report`, listing the finished work items
by the rule of `docs/RETENTION.md`, the size of their untracked review folders and the archives older than the time
to live. The archive command (row 27c) and the prune (row 27d) are not part of this item. The previous milestone,
W25 `command-wording`, is accepted (Workflow 2.19.2).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The report script, its tests and the documents | **complete** (verified in a scratch clone, see below) |
| CP2 | Release 2.20.0 | **complete** (verified in a scratch clone, see below) |

## Verified state

- CP1: `payload/scripts/workflow_retention.py` (`# state_writer: false`, stdlib plus `workflow_forge`;
  `build_report` and `main`), the `RetentionReport` tests in `workflow_state_completion_obligations_test.py`
  (193 -> 208), `docs/RETENTION.md` (the section "The report" and the re-targeted row references) and
  `docs/exit-codes.md`. Each mutation the plan lists (open items queried, the stored fact trusted, an exception
  aborting the run, `>=` for `>`, a symlink followed, a write to the archive directory, a write only in the
  query-failure handler, a write only on a refusal path, the bytecode assignment moved after the sibling import,
  `archives` in directory order) fails at least one test in a scratch copy.
- Verified in a disposable clone (D-Staging, the adjusted staging reported): `tools/release` (277, with the one
  declared scratch patch of the two pinned counts), `tools/docs` (34), `check_docs.py`, `check-manager-block`, and the
  nine suites from the staged fixture (see the implementation bundle's `TEST_RESULTS.md`).

- CP2: `manifest.json` 2.20.0 (the added `scripts/workflow_retention.py` record, counts 81/6, `distribution` 55, the posture,
  `conformance.suites` measured by `release.py manager-block --write`, `workflow_state_completion_obligations_test.py` 208),
  `WORKFLOW_RELEASE` 2.20.0 with its two pinned assertions and the `ORCHESTRATION_PROTOCOL.md` edits, the 2.20.0 row of
  `docs/release-history.md`, and the 2.20.0 release class of `tools/release/release_test.py` (the 2.19.2 class keeps what
  stays true of it). Verified in a scratch clone holding the CP2 commit: the nine suites from a stock `stage-conformance`
  fixture, `tools/release` (279, zlib-ng 2.2.5), `tools/docs` (34), `check_docs.py`, `check-manager-block`,
  `release.py build --commit HEAD`; `workflow-manager verify .` clean in the checkout.

## Functional review checklist

Scope: the read-only script `scripts/workflow_retention.py report` (in this release source: `payload/scripts/workflow_retention.py`).
It writes nothing. Each flow below states what the script must print and which exit status it must return.

**Automated state:** the implementation is at revision 2 (`EIR-001` fixed, regression tests included). The external
implementation review (round 3, `APPROVE`) ran the full verification on this tree. On `468aaf8` the 16 `RetentionReport`
tests were re-run and pass (`python3 -B -m unittest workflow_state_completion_obligations_test.RetentionReport`, from
`payload/scripts`).

### Setup

Work in a scratch directory `$S`, outside the repository. Stage a fixture from the release source:

```
python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"
cd "$S/fixture" && git remote add origin https://github.com/example/retention-fixture.git
mkdir -p "$S/archives/retention-fixture" "$S/home"
```

The origin is a URL only: nothing is fetched, and the `gh` stand-in refuses every forge call. Pass
`--archive-root "$S/archives"` to every run, so no run touches the real `~/.local/share/workflow-archive`.

**Test data.** Replace `docs/ai-workflow/WORKFLOW_STATE.json` in the fixture with a `work_items` mapping of five entries.
The report reads only `phase`, `parent_work_item_id`, `last_transition`, `reviewed_implementation_head` and
`technical_approval` (`reviewed_content_commit` with `approved_review_content_id`):

- `alpha`: `MILESTONE_COMPLETE`, `last_transition` `2026-10-01T00:00:00Z`, `reviewed_implementation_head` set to a 40-hex commit.
- `beta`: `MILESTONE_COMPLETE`, `last_transition` `2026-10-05T00:00:00Z`, same kind of head.
- `delta`: `AWAITING_FUNCTIONAL_REVIEW`, no parent.
- `gamma`: `MILESTONE_COMPLETE`, `last_transition` `2026-10-09T00:00:00Z`, `parent_work_item_id` `delta`.
- `open-one`: `AWAITING_FUNCTIONAL_REVIEW`, `last_transition` `2026-10-20T00:00:00Z`.

Record `git hash-object` of the state file before each flow that changes it, so the read-only check of F5 covers it.

### Flows

**F1. Refusals (offline).** Each run exits `2` and prints `error: <code>: <message>` and `next step: ...` on stderr, nothing on stdout:
- in a copy of the fixture with no `origin` remote: `repository_unknown`;
- in a copy with no `WORKFLOW_STATE.json`: `state_missing`;
- in a copy whose state file is `{not json`: `state_invalid`;
- `report --ttl-days 0`, `report --ttl-days abc` and `report --ttl-days 3651`: `usage` (the documented range is 1 to 3650).

**F2. Listing with the forge refusing (offline).** In the fixture with the test data, run `python3 -I scripts/workflow_retention.py report --archive-root "$S/archives"`, then with `--json`.
- Exit `0`. The text output names the repository `example/retention-fixture`, the archive directory and the TTL (30 days).
- `alpha` and `beta` are queried, and each is in `not_finished` with `query_failed:<code>`, never `finished`. The `<code>` is the forge error code the stand-in produces: record it.
- `gamma` is `family_open` (its parent `delta` is open) and is not queried. `open-one` is `open_phase` and is not queried. The stand-in's log shows calls only for the anchors of `alpha` and `beta`, newest first (`beta`, then `alpha`).
- `--json`: `schema_version` 1, `kind` `retention-report`, `keep_recent` 3, `complete` true, `read_errors` `[]`, `finished` and `kept_recent` empty, and `totals` with zero `finished`. The keys are sorted and the output ends in a newline.

**F3. Archives and the TTL (offline).** Create four files in `"$S/archives/retention-fixture/"` (empty files are enough; the sizes are then 0). Set their mtimes with `touch -d`:
`alpha.tar.zst` 31 days old, `beta.tar.zst` 30 days and 23 hours old, `open-one.tar.zst` 40 days old, `ghost.tar.zst` 1 day old; add `notes.txt` too.
- With the default TTL of 30, the `archives` list has four entries (`notes.txt` is not listed). `alpha`, `beta` and `open-one` are `not_finished` in this flow, so their `item` is `open`. `ghost` names no item, so its `item` is `other`.
- `prunable` is `true` for `alpha` (31 days) and `open-one` (40 days), and `false` for `beta` (30 days 23 hours, rounded down to 30) and `ghost`. `totals.archives` is 4 and `totals.prunable` is 2.
- With `--ttl-days 60`, `totals.prunable` is `0`.
- A prunable `open` archive is still listed as prunable: the report is not the prune, and row 27d must not remove it on the report's say-so.

**F4. Unreadable path (offline, run as a non-root user; `id -u` must not be `0`).** `chmod 000 "$S/archives/retention-fixture"`, run the report, then restore the mode.
- Exit `0`. `complete` is `false`, `read_errors` names the archive directory, the text ends with an `INCOMPLETE:` section, and `warning: incomplete:` goes to stderr.
- The directory is not reported as absent: an unreadable archive directory is not shown as "no archives", and `totals` are lower bounds.

**F5. Nothing written (offline).** Before and after F1 to F4, record a checksum of every file under the fixture (skip `.git`, which only Git's read-only commands refresh), under `$S/archives` and under `$S/home`:
`find "$S/fixture" -path '*/.git' -prune -o -type f -print0 | sort -z | xargs -0 sha256sum`, and the same for the other two trees.
- The two listings are identical. No `__pycache__` appears in `$S/fixture/scripts`, because the script is run as `python3 -I`.
- The state file's `git hash-object` is unchanged.

**F6. Owner-run: the forge facts (NOT sandbox-runnable).** These need a real, authenticated `gh` (read-only `gh pr list`), so the Controller's sandbox cannot run them. Run them in your own clone, from `scripts/workflow_retention.py` once this release is installed (see the limitation below), or from a staged fixture.
- A finished item: a merged pull request. `finished` gives its `number` and `url`, `review_folder` gives `present`, `files`, `bytes` and `tracked_files`, and `archive` gives `present`, `bytes`, `modified` and `age_days`.
- A closed, unmerged pull request: `pr_not_merged:closed`.
- With at least four merged items, the three newest are `kept_recent`, and the older ones are `finished`.
- A symlink inside a review folder is not followed: its target's bytes are not counted. `tracked_files` counts the tracked paths under `.ai-review/<id>/`.
- `git status --porcelain` and the archive directory are unchanged after the run.

### Expected results: summary

- Every flow above exits `0` except the refusals of F1 (`2`).
- No flow writes anything (F5).
- No item is `finished` without a merged pull request (F2, F6).

### Known limitations and out of scope

- **Not installed in this repository yet.** `scripts/workflow_retention.py` exists only in the release source and in a staged fixture. Until Workflow 2.20.0 is installed by `workflow-manager update`, `python3 scripts/workflow_retention.py` in this repository fails with a missing file. This is by design (the repository's own installation changes only through `workflow-manager update`).
- **Read-only, and that is all.** No archive command (row 27c), no prune (row 27d), no tracked-file command, no link check, no `verify` check, and no retention limit. The Manager's `status`/`doctor` wiring is row 17, outside this item.
- **Forge cost.** One `gh pr list` query per `MILESTONE_COMPLETE` item, one at a time, each with a 30-second timeout. Run the report between work items.
- **A failed forge query is not finished.** With `gh` unavailable, every queried item is `not_finished` with `query_failed:<code>`, and the exit status stays `0`. This is intended.
- **The stored `gate_evidence.pr` is ignored.** It is stale for every finished item, so the report always asks the forge.
- **The archives in F3 are empty placeholders.** Row 27c writes the real `.tar.zst` files, so the sizes in F3 are `0`.
- **Bytecode.** The CLI form leaves no bytecode. A program that imports `workflow_retention` for `build_report` must set `sys.dont_write_bytecode = True` before the first import.
- **Runtime.** Python 3.14, stdlib only plus `workflow_forge`.

## Next action

Functional review. Testing is by hand, against the commit named in the checklist evidence (step 4 of the preparation
reports the exact SHA and blob). Findings go to `.ai-review/retention-report/feedback/FUNCTIONAL_REVIEW.md`, and
`/apply-functional-review` routes them. Once testing is clean, `/accept-milestone` is the only acceptance command, and it needs every checkpoint `COMPLETE` (CP1 and CP2 are).
