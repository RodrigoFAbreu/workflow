# Active Milestone

## Milestone

**In progress.** W34: `retention-polish` (`process`, governing version `2.2`), branch `milestone/retention-polish`,
roadmap row 29 (RodrigoFAbreu/workflow#123 items 2 and 4, #132 items 1 and 2). Plan:
`docs/ai-workflow/RETENTION_POLISH_PLAN.md` (revision 2, approved by gate policy). The goal, Workflow 2.25.2 (a `fix:`
patch): wording and test pins of finished retention work, no behaviour change. Base commit `586c86c`.

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | The four in-scope items: wording, three assertions | **complete** |
| CP2 | Release 2.25.2 | **complete** |

## Verified state

- CP1: the operator reference's Writes line for `/archive-finished-item`, the `RetentionRemove.stat_refused` prefix
  assertion and the new preview-pairs test. Verified from a scratch-staged fixture (D-Staging): the nine suites pass
  (integration 377); mutations m1 to m7 each fail as the plan says; `workflow_retention.py` and `payload/.claude` are
  byte-identical to the base.

- CP2: Workflow 2.25.2 (manifest, the six records, the posture, `conformance.suites` integration 377; the release
  constant, its assertions and the protocol document; the 2.25.2 and corrected 2.25.1 history rows; the
  `RetentionPolishReleaseTest` class and the nine docstring pointers). Verified from a squashed scratch clone of the
  candidate: the nine suites from `stage-conformance`, `build`, `check-manager-block`, the `tools/release` tests (299)
  and `tools/docs`; m8 fails `RetentionPolishReleaseTest` and the baseline passes.

## Functional review checklist

Candidate: Workflow 2.25.2, release commit `49926f8` (the implementation head that passed both implementation-review
stages). Automated verification is current: the only working-tree difference from the reviewed state is the
uncommitted row 29 of `docs/ROADMAP.md`, which is not in the reviewed or shipped content.

### Setup

Offline only. Nothing here needs `gh`, `claude`, `codex`, `ssh`, a forge or the network, and no flow writes inside the
product clone or `.ai-review/`. Use a scratch directory:

```bash
export S="$TMPDIR/fr" && mkdir -p "$S"
python3 tools/release/release.py stage-conformance --commit 49926f8 --out "$S/fixture"
```

Every mutation flow edits its own copy: `command cp -rf "$S/fixture" "$S/<id>"`, then runs from `"$S/<id>/scripts"`.

Flows 1 and 6 also need a Python with the pinned `zlib_ng` (`tools/release/deflate-requirements.txt`: zlib-ng 1.0.0,
cp312 wheel). Without it the `tools/release` tests and `build` refuse. That is an environment limit, not a defect.
Flows 2 to 5, 7 and 8 do not need it.

### Test data

None. The flows read the staged fixture and the repository's own text.

### Flows

1. **Automated suites.** The nine suites from the fixture (`docs/RELEASING.md`, "Verification commands", first block),
   then `python -m unittest discover -s tools/release -p '*_test.py'` with the zlib-ng Python, then
   `python3 tools/docs/check_docs.py`.
   **Expect:** all pass; `workflow_integration_test.py` runs 377 tests.
2. **Command step 2 pins (m1 to m5).** In a copy, change `.claude/commands/archive-finished-item.md` one at a time:
   m1 the first pair's `not_archived` becomes `cross_device`; m2 the second pair's `already_archived` becomes
   `not_archived`; m3 delete "Nothing is applied and no sentence is asked for."; m4 move the catch-all bullet above the
   first pair; m5 the first pair's "archive then remove" becomes "remove only". Run
   `python3 -B -m unittest workflow_integration_test.TestArchiveFinishedItemCommand` from each copy's `scripts/`.
   **Expect:** the unmodified fixture passes (7 tests); each mutation fails `test_the_preview_result_pairs_and_the_catch_all_stop_are_pinned`.
3. **Writes line (m6).** In a copy, restore "nothing in the repository and no state" to the archive section's Writes
   line of `docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`. Run the class from flow 2.
   **Expect:** fails `test_the_documents_list_it`; the unmodified fixture passes.
4. **Helper prefix (m7).** In a copy, change `_lstat_at` in `scripts/workflow_retention.py` so the message reads "look at"
   instead of "check the permissions of". Run `python3 -B -m unittest workflow_state_completion_obligations_test.RetentionRemove`.
   **Expect:** fails. In a second copy, delete the new `assertIn("check the permissions of", ...)` line of
   `stat_refused` and run it again: **expect** it passes, which is the gap the line closes.
5. **Wording read.** In the repository's `payload/docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md`, the archive
   command's Writes line reads "no tracked file and no state. The engines write the archive and its index line in the
   archive store, and `remove` takes the untracked `.ai-review/<id>/` folder away." `RetentionRemove.stat_refused`
   asserts "check the permissions of" in the next step, as the archive class's helper does.
6. **Release history (m8).** Make a disposable clone and check out the candidate:
   `git clone -q "$PWD" "$S/repo" && git -C "$S/repo" checkout -q 49926f8`. Read the 2.25.1 and 2.25.2 rows of
   `docs/release-history.md` in it. Then, in `$S/repo/docs/release-history.md`, remove the `.ai-review/<id>` entry from
   the 2.25.1 row's list, and run `RetentionPolishReleaseTest` from `$S/repo/tools/release` with the zlib-ng Python.
   **Expect:** the 2.25.1 row names the archive-directory entry, the `.removing` entry and the `.ai-review/<id>` entry;
   the 2.25.2 row names #123 and #132, the absence of behaviour change and the way back; the unmodified clone passes,
   and m8 fails the class.
7. **Pointers and scope.** `grep -n '(2\.25\.[01])\."""' tools/release/release_test.py` prints nothing;
   `grep -c '(2\.25\.2)\."""' tools/release/release_test.py` prints 9; `git diff 586c86c --stat -- payload scripts .claude`
   lists only the six `payload/` files (`WORKFLOW_V2_1_OPERATOR_REFERENCE.md`, `ORCHESTRATION_PROTOCOL.md`,
   `workflow_integration_test.py`, `workflow_protocol.py`, `workflow_protocol_test.py`,
   `workflow_state_completion_obligations_test.py`), so the installed copies in `scripts/` and `.claude/` are untouched.
8. **Engine and command files.** `git diff 586c86c -- payload/scripts/workflow_retention.py payload/.claude` is empty.

### Known limitations and out of scope

- Out of scope by the plan (section 2): #123 items 5 and 6, #126 items 4 and 5, #129 items 1 and 2. The
  `cross_device` next step is an engine message, and this item changes no engine behaviour or message. Requirements
  mappings and checklist text of finished items are not edited.
- The manifest record of `scripts/workflow_retention.py` repeats the 2.25.1 history sentence that the 2.25.2 row
  corrects. It is left alone, as the plan states; the reviewers recorded it as an optional finding.
- The installed copies (`.claude/`, `scripts/`, `docs/ai-workflow/`) stay at 2.25.1 until a release is merged and
  installed with `workflow-manager update`. This item does not publish a release or add a `workflow-manager` pin.
- `docs/ROADMAP.md` row 29 becomes Done at acceptance, not before.

## Next action

Run the checklist above offline. Findings go to the functional-review path that `/prepare-functional-review` prints
(resolved by `python3 scripts/workflow_fingerprint.py --resolve-feedback-path retention-polish`), then
`/apply-functional-review` routes each one. When testing is clean, `/accept-milestone` is the only acceptance command.
