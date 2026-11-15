# Active Milestone

## Milestone

**Awaiting functional review** (W52, `acceptance-gate-robustness`, `process`, governing version `2.2`), branch
`milestone/acceptance-gate-robustness`, roadmap row 45. The plan is `docs/ai-workflow/ACCEPTANCE_GATE_ROBUSTNESS_PLAN.md`
(revision 5, approved by gate policy). Implementation revision 1; CP1 and CP2 are complete. The change is Workflow patch
release **2.29.5** (a `fix:` change; the release is published after the merge).

## Goal

The plain acceptance report never ends in an error for an absent pull-request head, its requirement partition is pinned by a
test, and the path messages name the right file and phases. The gate does not change: `evaluate_gate` and every library
function return what they returned before.

## Outcome (what changed)

1. **D-Report:** a stored pull-request fact whose head the repository lacks gives a named, blocked report
   (`stored_pr_fact_unresolvable`, `ready` false) instead of an `AmbiguousBaseError` error object.
2. **D-Partition:** a test pins that every acceptance requirement id is in exactly one of the two report lists.
3. **D-Wording:** `phase_not_reachable` no longer says the phase is wrong when it is one the acceptance stage accepts
   (the outstanding-checkpoint case only; other phases keep their released text).
4. **D-Path:** the unclassified-path message and the helper share one template, and `promote_legacy_work_item` names the
   file it really read.
5. **D-Phase:** the plan-stage sentence says "of a two-stage item", and the plan-stage text is five lines, not one.

## Automated verification (current)

Last full run: `.ai-review/acceptance-gate-robustness/current/TEST_RESULTS.md`, against `991df27` (CP2). Since then only
`docs/ai-workflow/WORKFLOW_STATE.json` changed (the implementation approval and the bundle record), so no script, test or
document moved. Recorded results: the nine payload suites pass from a staged fixture (453, 344, 1250, 429, 151, 308, 377,
283 and 27 tests); `tools/release` 337 pass under the zlib-ng interpreter; `tools/docs` 34 pass; `check_docs.py` exit 0; the
mutations m1 to m11 each fail their named tests.

## Functional review checklist

Scope: the acceptance report, the requirement partition, and the three messages. Nothing here touches the real repository,
a forge or the network. Every flow builds its own scratch repository with the test file's `AcceptanceRepo` helper.

### Setup

Run from the repository root, with a clean tree.

```sh
S="${TMPDIR:-$HOME/.cache}/w52-check"; rm -rf "$S"; mkdir -p "$S/base" "$S/cand" "$S/fakebin" "$S/drv"
git archive 9d37c60434b50528f041c43717d3252060d6c830 payload/scripts | tar -x -C "$S/base"   # 2.29.4, the base
git archive HEAD payload/scripts | tar -x -C "$S/cand"                                          # the candidate (2.29.5)
cp /home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w52-tmp/drv/drive.py \
   /home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w52-tmp/drv/msg.py "$S/drv/"
printf '#!/bin/sh\necho "gh called: $*" >> "%s/gh.log"\nexit 1\n' "$S" > "$S/fakebin/gh"; chmod 0755 "$S/fakebin/gh"
export PATH="$S/fakebin:$PATH"   # trap gh: every flow must leave $S/gh.log absent
```

- `drive.py` and `msg.py` are scratch helpers from the orchestrator. They are **not** committed to this repository; the
  copies above are the ones the automated run used. Run them only as `python3 -I`.
- No test data to seed: each case builds its state in a scratch repository.
- Each flow below says what to compare. "Tree unchanged" means the `drive.py` JSON field `unchanged` is `true`.

### Flows

Flows 1 to 10 run offline and need only `python3`, `git` and the trap `gh`. Flows 11 and 12 are verification commands.

**1. Ready is unchanged.** `python3 -I "$S/drv/drive.py" "$S/base/payload/scripts" ready` and the same with
`"$S/cand/payload/scripts"`.
Expect: identical output; exit 0, `ready` true, no blockers, tree unchanged, no `gh.log`.

**2. Absent stored head is a blocked report.** `drive.py ... absent` with `base` and then `cand`.
Expect: base: exit 1, `error` `AmbiguousBaseError`, no report. Cand: exit 0, `ready` false, exactly one blocker
`stored_pr_fact_unresolvable` whose detail names the head `0123456789abcdef0123456789abcdef01234567` and says "fetch it";
`stored_pr_fact.unmet` is `["pr_fact_current"]`; tree unchanged; no `gh.log`.

**3. The same at an early phase.** `drive.py ... absent-early` with `cand`.
Expect: blockers in this order: `phase_not_reachable`, then `stored_pr_fact_unresolvable`; `ready` false; tree unchanged.

**4. The library did not change.** `drive.py ... library` with `base`, then `cand`.
Expect: both print `library: AmbiguousBaseError`.

**5. The outstanding-checkpoint wording.** `drive.py ... outstanding AWAITING_FUNCTIONAL_REVIEW`, then
`outstanding AWAITING_USER_ACCEPTANCE`, then `outstanding IMPLEMENTING`, each with `base` and `cand`.
Expect: for the first two, base reads "the phase is X; the acceptance stage needs AWAITING_FUNCTIONAL_REVIEW and every
checkpoint complete (outstanding: CP1)"; cand reads "the phase is X, which the acceptance stage accepts, but not every
checkpoint is complete (outstanding: CP1)". For `IMPLEMENTING`, base and cand are identical.

**6. The partition.** `drive.py "$S/cand/payload/scripts" partition` prints three lists.
Expect: the `blocking` and `pr` lists are disjoint and their union is the seven acceptance requirement ids.
Then the mutation: copy `$S/cand` to `$S/mut`, append `"ci_green"` to `_ACCEPTANCE_REPORT_BLOCKING_REQUIREMENTS` in
`$S/mut/payload/scripts/workflow_state.py`, and run
`cd "$S/mut/payload/scripts" && python3 -B -m unittest workflow_gate_policy_test.TestAcceptanceGateReport.test_t4_every_requirement_is_in_exactly_one_of_the_two_report_lists`.
Expect: that test fails. Recorded run: `test_t1` and `test_t2` also fail, because the duplicate makes `ci_green` an extra
blocker there; this is explained, not a weak test.

**7. Messages are unchanged except the one sentence and the line breaks.** With `msg.py`:
`python3 -I "$S/drv/msg.py" <scripts> digests` for `base` and `cand`.
Expect: the first four lines (implementation known, implementation unknown, interval, helper) are identical. The
`plan known` line differs, as intended.
Then `msg.py <scripts> plan demo-item` and `msg.py <scripts> plan -` for both.
Expect: base is one line (1079 characters for the known form, 1158 for the unknown). Cand is five lines, each under 400
characters. Rejoined with spaces, the only words that differ are "of a two-stage item".

**8. The promotion names the file it read.**
`msg.py "$S/cand/payload/scripts" promote docs/ai-workflow/registry/legacy-core-artifacts.json`, and the same with
`.../demo-item-artifacts.json`, and both with `base`.
Expect: base names `demo-item-artifacts.json` for both. Cand names `legacy-core-artifacts.json` for the first, and for the
second the same text as base.

**9. The sentence is gone from the release source and the page.** Run from the repository root:
`git grep -n "other phase neither command is" 9d37c60434b50528f041c43717d3252060d6c830 -- payload` and
`git grep -n "other phase neither command is" -- payload docs/common-problems.md`.
Expect: the base commit matches in the script and in two test files. The working tree no longer matches in
`workflow_fingerprint.py` or the page; the page reads "of a two-stage item". One match remains, in
`workflow_fingerprint_generalization_test.py`, where T8 rebuilds the 2.29.4 sentence on purpose.

**10. Pages are clean.** `python3 tools/docs/check_docs.py` exits 0.

**11. The nine payload suites (verification; needs `python3` and `git`).** From the repository root:

```sh
python3 tools/release/release.py stage-conformance --commit HEAD --out "$S/fixture"
suites=$(python3 -c "import json; print(*json.load(open('manifest.json'))['manager']['conformance']['suites'], sep='\n')") && test -n "$suites" && ( cd "$S/fixture/scripts" && while read -r suite; do python3 -B "$S/fixture/scripts/$suite" </dev/null || exit 1; done <<< "$suites" )
```

Expect: every suite exits 0 and none is skipped beyond its own environment conditions. Recorded counts: 453, 344, 1250,
429, 151, 308, 377, 283 and 27.

**12. Tools and manager checks (verification; needs the zlib-ng interpreter and the `workflow-manager` tool; the sandbox
does not have them).** `<zlib-ng venv>/bin/python -m unittest discover -s tools/release -p '*_test.py'` expects 337 OK;
`python3 -m unittest discover -s tools/docs -p '*_test.py'` expects 34 OK;
`python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json`
expects `ok: 2.29.5 carries a valid manager block`; `workflow-manager verify .` expects exit 0.

### Known limitations and out of scope

- **Forge:** no flow uses a real pull request, GitHub or `gh`. The absent-head case is reproduced with a stored fact in a
  scratch repository, not on a live forge.
- **The `--satisfy-acceptance` refusal** uses the same function as the report's detail, but the tests that pin its wording
  call that function directly, not the CLI. A reviewer recorded this as an optional missing test; it is not addressed here.
- **Byte identity** of the base and the candidate is checked on the working paths with commit SHAs and timestamps
  normalised, because each scratch repository has new ones. T3 pins the present-head report by readiness and blocker
  absence, not byte for byte.
- **Kept unchanged on purpose (`KEEP`):** `python3 -B` in the messages, and the `phase_not_reachable` wording of every phase
  other than the accepted ones with an outstanding checkpoint.
- **Not re-run in this session:** `release.py build` (the CP2 session ran it).
- **Controller:** the Controller reads none of the changed text; its contract is out of scope.

## Next step

Report the findings in `.ai-review/acceptance-gate-robustness/feedback/FUNCTIONAL_REVIEW.md` (the path resolves per
`docs/ai-workflow/REVIEW_PROTOCOL.md`). Once testing is clean, `/accept-milestone` is the only acceptance command. It needs
every checkpoint of this item to be `COMPLETE`, which CP1 and CP2 now are. If a checkpoint is outstanding, run
`/milestone-implement`, finish it, and return to this gate. No command records acceptance of a partial round. Findings
route through `/apply-functional-review`: a same-scope fix takes its bounded branch, and new or wider scope takes its broad
branch as an `acceptance-gate-robustness-remediation-<n>` work item.
