# Active Milestone

## Milestone

**Implementing.** W2: `gate-policy-and-reopening` (`process`, governing
version `2.2`), branch `milestone/gate-policy-and-reopening`, base `d14e0a7`
(W1's squash merge; Workflow 2.7.0 is published and pinned by
`workflow-manager#13`, Manager v1.3.0). The plan is
`docs/ai-workflow/GATE_POLICY_AND_REOPENING_PLAN.md` (revision 34, approved;
local and manual external plan review both `APPROVE`).

## Goal

Workflow 2.8.0 on Orchestration Protocol 1.1: a declarative gate policy
(plan and technical approval satisfiable by current local plus independent
cross-model review evidence, functional validation by configured evidence,
acceptance still human) and post-validation reopening of the same work item
when a pull request is red or has `CHANGES_REQUESTED`. Default policy equals
today's gates exactly.

## Current checkpoint

`CP1` (gate policy model), `CP2` (automatic plan and technical approvals
with audit evidence), `CP3` (functional evidence, GitHub-sourced
pull-request facts and the stale-evidence table), `CP4` (automatic
milestone acceptance), `CP5` (reopening the same work item into
remediation) and `CP6` (Protocol 1.1: the gate rows, actions, `validation`,
schema and the all-human equivalence matrix) and `CP7` (specification,
`GATE_POLICY.md`, update simulation, lifecycle end-to-end tests) are implemented; their records,
deviations and deferrals are in the requirements ledger,
`docs/ai-workflow/requirements/gate-policy-and-reopening-ledger.md`. CP8 is not started. One checkpoint is implemented per `/milestone-implement`
invocation.

### CP2 evidence: 2.6.0 reads a 2.7.0-written state (2026-10-02)

The plan's one-off downgrade check. `STATE` was the
`TestConsumedPlanReviewHistory` migration scenario (a 2.6.0-shaped item,
slot `b…b` only, then publish and bind `a…a` and a local `REVISE` of it),
written by CP2's `workflow_state.py` and dumped to a temporary file; its
history was `["a…a", "b…b"]`. Run from the repository root:

```text
d=$(mktemp -d)
git show v2.6.0:payload/scripts/workflow_state.py > "$d/workflow_state.py"
git show v2.6.0:payload/scripts/workflow_fingerprint.py > "$d/workflow_fingerprint.py"
python3 -c 'import json, sys; sys.path.insert(0, sys.argv[1]); import workflow_state as w; s = json.load(open(sys.argv[2])); w.validate_state(s); print("ACCEPTED", sorted(k for i in s["work_items"].values() for k in i if k == "consumed_plan_review_content_ids"))' "$d" "$STATE"
```

Output, exit code 0:

```text
ACCEPTED ['consumed_plan_review_content_ids']
```

2.6.0 blobs: `payload/scripts/workflow_state.py` `fed844fc70c54bac8787ebea8f77cb67cd7c2f05`,
`payload/scripts/workflow_fingerprint.py` `565f24bb2dcc21227cb5abf52e0549d7091b8525`.

## Functional review checklist

W1 is a `process` milestone: the "product" is Workflow 2.7.0 (the
orchestration protocol CLI, the two follow-ups, and the package). Everything
below runs offline, on this machine, in a scratch installation outside the
checkout. Nothing here pushes, opens a pull request, changes GitHub settings
or publishes a release; the cutover (plan section 7) is the owner's and comes
after this review. The release source and the repository's own installation
are not modified by any step.

**Setup**

S1. On branch `milestone/orchestration-protocol-v1`, clean tree. Set the
    pinned runtime (Python 3.12, `zlib-ng` 1.0.0, Workflow Manager 1.2.0) and
    a scratch directory:
    ```bash
    V=/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv
    S=$(mktemp -d /tmp/w1-review.XXXX); echo $S
    REPO=$PWD; R=tools/release/release.py
    ```
    Run every step from the repository root unless it says `cd "$S/target"`.
S2. Build the 2.7.0 package and install it into a scratch repository:
    ```bash
    $V/bin/python $R build --commit HEAD --out $S/build
    $V/bin/workflow-manager package verify $S/build/workflow-2.7.0.tar.gz \
        --sha256 "$(grep tar.gz $S/build/SHA256SUMS | cut -d' ' -f1)"
    mkdir $S/rel && tar -xzf $S/build/workflow-2.7.0.tar.gz -C $S/rel
    mkdir $S/target && git -C $S/target init -q \
        && git -C $S/target -c user.name=t -c user.email=t@t commit -q --allow-empty -m init
    $V/bin/workflow-manager --release-dir $S/rel/workflow-2.7.0 bootstrap $S/target
    $V/bin/workflow-manager --release-dir $S/rel/workflow-2.7.0 verify $S/target
    ```
    Expected: `version=2.7.0`, `files=74`, `zlib_ng=2.2.5`; `release 2.7.0,
    73 files, verified`; `bootstrapped workflow 2.7.0 (full)`; `installation
    matches workflow 2.7.0`. (The Manager has no pin for 2.7.0 yet, hence
    `--release-dir`.)
S3. Define the protocol shorthand and the live-release fixture (the five
    published releases, no drafts):
    ```bash
    P() { (cd $S/target && $V/bin/python scripts/workflow_protocol.py "$@"); }
    cat > $S/releases.json <<'JSON'
    [{"isDraft":false,"tagName":"v2.6.0"},{"isDraft":false,"tagName":"v2.5.1"},{"isDraft":false,"tagName":"v2.5.0"},{"isDraft":false,"tagName":"v2.4.0"},{"isDraft":false,"tagName":"v2.3.1"}]
    JSON
    ```
    (If pasting the heredoc indented, remove the indentation.)

No test data to seed: the scratch repository starts with no work item, and
the lifecycle driver (F4) seeds its own.

**Flows**

F1. Package reproducibility.
    `$V/bin/python $R build --commit HEAD --out $S/build2` and
    `diff $S/build/SHA256SUMS $S/build2/SHA256SUMS`.
    Expected: no difference. `tar_sha256=6a5f7c7e…`,
    `archive_sha256=c287323f…`, `manifest_sha256=f62fb261…` (at commit
    `048482f`; a later evidence commit changes only `docs/ACTIVE_MILESTONE.md`,
    which is not in the release source, so the digests do not move).
    Then `$V/bin/python $R build --commit v2.6.0 --out $S/b260`:
    `archive_sha256=dc86a796…`, `manifest_sha256=d92517a2…` (the published
    2.6.0, still reproduced bit for bit).
F2. `describe` (reads nothing from the repository):
    `P describe`.
    Expected: exit 0, one JSON envelope, `workflow_release` `2.7.0`,
    `protocol_version` `1.0`, `supported_protocol_majors` `[1]`,
    `supported_governing_versions` `["1","2.1","2.2"]`; `operations` are
    `describe, next-action, reconcile, record-external-result,
    resolve-artifact, verify`; `external_result_kinds`
    `implementation_review_verdict, plan_review_verdict`;
    `reserved_result_kinds` `functional_evidence, pr_review_result`.
    Then `P --protocol-major 2 describe; echo rc=$?`: an `ok: false` envelope,
    `error.code` `unsupported_protocol`, `rc=3`.
F3. `verify`, `next-action`, `reconcile`, `resolve-artifact` and
    `record-external-result` on the empty scratch installation:
    - `P verify`: `healthy: true`, seven checks all `pass`
      (`installation_release_matches` says `installed release 2.7.0`).
    - `P next-action`: row `1`, action `plan.start`, disposition
      `automatic`, invocation `/milestone-plan`.
    - `P next-action > $S/dec.json; P reconcile --decision $S/dec.json`:
      class `no_progress`, `invalid_reasons` `[]` (nothing was done).
    - `P resolve-artifact --work-item nope --kind review_feedback; echo rc=$?`:
      `unknown_work_item`, `rc=3`.
    - `echo x > $S/v.txt; P record-external-result --work-item nope --kind functional_evidence --input $S/v.txt`:
      `unsupported_result_kind` (reserved kind), exit 3; with `--kind
      plan_review_verdict` instead: `unknown_work_item`, exit 3.
    - Missing arguments (e.g. `P reconcile`): `invalid_request`, exit 2.
    Every call prints exactly one JSON envelope on stdout, whatever the exit.
F4. Every operation end to end, through the real CLI. The installed
    lifecycle tests drive a `2.2` item from no work item to
    `MILESTONE_COMPLETE` (REVISE rounds at both review stages, two
    checkpoints, manual verdicts), and two `"1"` runs, with *every* protocol
    call replaced by a subprocess of `scripts/workflow_protocol.py`:
    ```bash
    cat > $S/cli_lifecycle.py <<'PY'
    import json, subprocess, sys, unittest
    from collections import Counter
    sys.path.insert(0, "scripts")
    import workflow_protocol_test as t
    calls = []
    def call(*argv):
        p = subprocess.run([sys.executable, "scripts/workflow_protocol.py", *argv],
                           capture_output=True, text=True)
        body = json.loads(p.stdout)
        t.assert_valid(body)
        calls.append(body["operation"])
        return body, p.returncode
    t.call = call
    suite = unittest.defaultTestLoader.loadTestsFromNames(
        ["TestLifecycleEndToEnd2_2", "TestLifecycleEndToEndV1"], t)
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    print("CLI calls by operation:", dict(Counter(calls)))
    sys.exit(0 if res.wasSuccessful() else 1)
    PY
    (cd $S/target && $V/bin/python $S/cli_lifecycle.py)
    ```
    (Remove the heredoc's indentation if pasting.) Expected: `Ran 5 tests`,
    `OK`, and `CLI calls by operation` showing `next-action`, `reconcile`
    and `record-external-result` (80, 32 and 11 on the reviewer's run).
    This covers `next-action` row order and `plan.start` through
    `functional.review`, `reconcile` classes (`progress`, `gate_reached`), a
    gate decision refused by `reconcile` with `invalid_request`, and
    `record-external-result` for both stages.
F5. `resolve-artifact` for each kind, on a seeded item. Inside the same
    scratch module, with the item the lifecycle builds:
    ```bash
    cd $S/target && $V/bin/python - <<'PY'
    import sys; sys.path.insert(0, "scripts")
    import workflow_protocol_test as t, workflow_test_harness as h, json
    with h.ScratchRepo() as repo:
        t._seed_unrouted(repo, "2.2")
        run = t._Lifecycle(__import__("unittest").TestCase(), repo, dict.fromkeys(
            ["plan.local","plan.manual","implementation.local","implementation.manual"], ["APPROVE"]*3))
        run.drive(until="human_gate")  # plan approval gate
        for kind in ["review_feedback","functional_review","review_bundle","plan_review_inputs","plan_document","functional_checklist"]:
            body, code = t.call("--repo-root", str(repo.root), "resolve-artifact", "--work-item", t.WI, "--kind", kind)
            print(kind, code, json.dumps(body["result"]))
    PY
    cd - >/dev/null
    ```
    Expected: six lines, exit code 0 each, each with `kind`, a
    repository-relative `path`, an `exists` boolean and the decision `basis`
    (phase `AWAITING_PLAN_APPROVAL`). `plan_document`
    (`docs/ai-workflow/WORKFLOW_V2_PLAN.md`), `review_bundle`
    (`.ai-review/wi/current`, the plan-stage bundle at this phase) and
    `review_feedback` exist; `review_feedback` and `functional_review` sit
    under `.ai-review/wi/feedback/`; `plan_review_inputs` is
    `.ai-review/wi/plan-inputs`; `functional_checklist` is
    `docs/ACTIVE_MILESTONE.md`; the last three do not exist in this seed.
    If the inline script is awkward, F4 plus `P resolve-artifact` calls in
    `workflow_protocol_test.py`'s `TestResolveArtifact` (run it with
    `cd $S/target && $V/bin/python scripts/workflow_protocol_test.py TestResolveArtifact`)
    cover the same ground.
F6. Follow-up `v2.6.0-001` (consumed-content re-bind refusal) and
    `v2.6.0-002` (label alias), on the installed scripts:
    ```bash
    cat > $S/followups_demo.py <<'PY'
    import sys
    sys.path.insert(0, "scripts")
    import workflow_fingerprint as fp
    import workflow_state as ws
    import workflow_state_test as t
    A, B = t._CP4_A, t._CP4_B
    s = t._base_state(wi=t._cp4_item(version="2.2", phase="AWAITING_LOCAL_PLAN_REVIEW", plan_revision=2,
        record=t._cp4_record("BOUND", consumed=None, published={"review_content_id": A, "plan_revision": 2},
                             bound=t._cp4_binding(A, t._CP4_C, 2))))
    def publish_bind(s, rcid, rev):
        s = ws.publish_plan_revision(s, "wi", rev, "t", review_content_id=rcid)
        return ws.bind_plan_review_bundle(s, "wi", binding=t._cp4_binding(rcid, t._CP4_D, rev), now="t")
    rev = lambda s, r: ws.record_local_plan_review(s, "wi", verdict="REVISE", bundle_id=t._CP4_D,
                                                   review_content_id=r, round=1, now="t")
    s = rev(s, A); s = publish_bind(s, B, 3); s = rev(s, B)
    print("history == [A, B]:", s["work_items"]["wi"][ws.CONSUMED_PLAN_REVIEW_CONTENT_IDS_KEY] == [A, B])
    try:
        ws.publish_plan_revision(s, "wi", 4, "t", review_content_id=A); print("A RE-BOUND: FAIL")
    except ws.ConsumedPlanReviewContentError as e:
        print("restored A refused:", type(e).__name__)
    s = publish_bind(s, "e" * 64, 4)
    print("after an edit:", s["work_items"]["wi"]["phase"])
    H = "a" * 64
    for name, text in [
        ("pinned label", f"Status: APPROVE\nReviewed review_content_id: {H}\n\n## F\n"),
        ("legacy alias", f"Status: APPROVE\nReviewed review content ID: {H}\n\n## F\n"),
        ("bare form", f"Status: APPROVE\nreview_content_id: {H}\n\n## F\n"),
        ("under ## Review Decision", f"## Review Decision\nStatus: APPROVE\nReviewed review_content_id: {H}\n\n## F\n"),
        ("id only after a later ##", f"Status: APPROVE\n\n## F\nReviewed review_content_id: {H}\n"),
        ("two labels, two values", f"Reviewed review_content_id: {H}\nReviewed review content ID: {'b'*64}\n")]:
        print(f"{name:28}", fp.parse_feedback_review_content_id(text))
    PY
    (cd $S/target && $V/bin/python $S/followups_demo.py)
    ```
    Expected: `history == [A, B]: True`; `restored A refused:
    ConsumedPlanReviewContentError`; `after an edit:
    AWAITING_LOCAL_PLAN_REVIEW`; the first four labels print the 64-`a` id,
    the last two print `None`. Then run the dedicated tests:
    `cd $S/target && $V/bin/python scripts/workflow_state_test.py TestConsumedPlanReviewHistory`
    (`Ran 8 tests`, `OK`) and
    `$V/bin/python scripts/workflow_fingerprint_test.py TestPinnedReviewContentIdLabel`
    (`OK`).
F7. Downgrade check (the CP2 evidence above): 2.6.0's `validate_state` accepts
    a 2.7.0-written state. Repeat it from the section's command block, or
    accept the recorded output.
F8. Release decision: a `feat:` title releases 2.7.0. The checks compare a
    commit with its first parent, so on the branch tip they report
    `2.7.0 -> 2.7.0`; the pull request is a squash onto `main`. Simulate it
    in a scratch clone (the checkout is not touched):
    ```bash
    git clone -q --no-hardlinks . $S/squash && cd $S/squash
    git checkout -q main && git fetch -q origin milestone/orchestration-protocol-v1
    git -c user.name=s -c user.email=s@s merge --squash -q origin/milestone/orchestration-protocol-v1
    git -c user.name=s -c user.email=s@s -c commit.gpgsign=false commit -q \
        -m "feat: Workflow 2.7.0 with Orchestration Protocol v1"
    RR=$REPO/$R; PY=$V/bin/python
    $PY $RR check-title "feat: Workflow 2.7.0 with Orchestration Protocol v1" --agree
    for t in "fix: x" "docs: x" "feat!: x"; do $PY $RR check-title "$t" --agree; echo rc=$?; done
    $PY $RR check-pending --releases $S/releases.json
    $PY $RR check-immutable --releases $S/releases.json
    $PY $RR next-release --trigger HEAD --releases $S/releases.json
    $PY $RR build --commit HEAD --out $S/sq | grep -E 'version|archive|manifest'
    cd $REPO
    ```
    Expected: `impact=minor` and `version 2.6.0 -> 2.7.0 (minor) agrees with
    the title` (exit 0); `fix:`, `docs:` and `feat!:` each refused, `rc=1`
    (impact patch/none/major disagrees with the minor change);
    `check-pending` `ok: 2.6.0 -> 2.7.0 (minor); release source changed: …`;
    `check-immutable` `ok: version 2.7.0 is not published; D-W0-Immutable
    does not apply`; `next-release` `state=pending`, `version=2.7.0`,
    `target=<the squash commit>` (so `Release` would publish 2.7.0 from it);
    the squash's build has the same `archive_sha256`/`manifest_sha256` as F1.
F9. Automated suites, as CI would run them: stage and run the eight
    release-source suites, and the tooling tests:
    ```bash
    $V/bin/python $R stage-conformance --commit HEAD --out $S/fx
    (cd $S/fx/scripts && for f in workflow_fingerprint workflow_state workflow_test_harness \
        workflow_integration workflow_acceptance_matrix workflow_state_completion_obligations \
        workflow_fingerprint_generalization workflow_protocol; do
      echo "$f"; $V/bin/python ${f}_test.py 2>&1 | grep -E '^(Ran|OK|FAILED)'; done)
    $V/bin/python tools/release/release_test.py 2>&1 | tail -3
    ```
    These are exactly CI's eight suites, in its order (the `*_demo_test.py`
    files in the fixture are not CI suites and need a real-repository history
    the fixture lacks; do not run them). Expected: every suite `OK`, none
    `FAILED`; `Ran` counts: fingerprint 256, state 1011, test harness 22,
    integration 267, acceptance matrix 291 (`skipped=18`), completion
    obligations 106, fingerprint generalization 105, protocol 217;
    `release_test.py` `Ran 75 tests`, `OK`. (The state and
    acceptance-matrix suites take several minutes.)
F10. Installation untouched: `$V/bin/workflow-manager verify .` prints
    `installation matches workflow 2.6.0`, and `git status --short` is
    empty (after the evidence commit).
F11. Read the documents the milestone ships: `payload/docs/ai-workflow/
    ORCHESTRATION_PROTOCOL.md` (spec) against `F2`/`F3`/`F4` behavior; its
    tables are pinned to the code by tests, so the review is whether the
    prose is understandable to an orchestrator author. Also skim
    `docs/ROADMAP.md`'s W1 row, the "Workflow 2.7.0" entry, and the
    `v2.6.0-003` open row.

**Known limitations / out of scope**

- Nothing is published: no push, no pull request, no GitHub settings, no
  release. The first real CI and `Release` run is the cutover.
- The Workflow Manager has no 2.7.0 pin; installation uses `--release-dir`.
  The Manager pin pull request (archive and manifest digests,
  `CI_SUITES["2.7.0"]`) is an owner action after publication.
- This repository's own installation stays 2.6.0; updating it follows
  publication and the Manager pin.
- The Controller 1.5.0 refuses 2.7.0 until it admits it (plan section 7,
  item 4); not exercised here.
- `functional_evidence` and `pr_review_result` are reserved result kinds and
  refuse by design in protocol 1.0.
- `"1"` items with a registry cannot advance through the protocol; it
  reports them `blocked` (`v2.6.0-003`, open by design).
- `--protocol-major` is read as a global option before the operation; placing
  it after the operation is a known minor quirk (ledger self-review).
- The `verify` operation does not check installation digests; that is
  `workflow-manager verify`.

## Current blockers

None.

## Active plan

None, because the milestone is complete. The plan document stays at
`docs/ai-workflow/ORCHESTRATION_PROTOCOL_V1_PLAN.md` (revision 13, plan
approval `CURRENT`) instead of being archived, as W0's did: the release
source (`payload/scripts/workflow_protocol.py`, `workflow_state.py`, the
test harness and suites) and the artifact registry cite it as the design
record.

## Functional review round 1

The orchestrator-run functional review (`FUNCTIONAL_REVIEW.md`, evidence
commit `ee86188`) passed S1-S3 and F1-F11 with one finding, F1: three
wording points in `docs/ROADMAP.md` (the W0 row's cutover steps, the W1 row's
premature COMPLETE, and the `v2.6.0-001` tense). Classified as documentation,
no code change; fixed in `docs/ROADMAP.md`, which both stages exclude, so
`technical_approval` stays CURRENT and no bundle is regenerated. Nothing was
deferred to a remediation child. Re-test: re-read the three ROADMAP lines.

## Next action

`orchestration-protocol-v1` is complete. Next:
1. The cutover (plan section 7), the owner's actions: open the pull request
   from this branch titled `feat: Workflow 2.7.0 with Orchestration Protocol
   v1` and merge it once `aggregate`, `Conventional Commit title` and
   `workflow-conformance` are green, so `Release` publishes and reads back
   `v2.7.0`; then the `workflow-manager` pin pull request; then install
   2.7.0 here with `workflow-manager update`, in its own pull request; and
   write `v2.6.0-003` in `workflow-manager`'s `docs/defects/`. Do not update
   a Controller-driven repository to 2.7.0 before the Controller's C9.
2. Then run `/milestone-plan` for W2 in `docs/ROADMAP.md`: Workflow 2.8,
   declarative gate policy, and a red or changes-requested pull request
   reopening the same work item.

---

# Previous milestone record: W0 `workflow-repository-setup`

### Milestone

**Complete.** W0: `workflow-repository-setup` (`process`, governing version `2.2`),
branch `milestone/workflow-repository-setup`, base `bf51137`.

### Goal

Set this repository up for development: CI over the release source, a
release workflow that publishes an immutable release when `main`'s manifest
names an unpublished version, and `main` protection with Conventional-Commit
titles. W0 itself releases nothing.

### Current checkpoint

**Milestone complete.** `workflow-repository-setup` reached
`MILESTONE_COMPLETE` through `/accept-milestone` on 2026-10-01, with the
owner's confirmation, and `active_work_item_id` is cleared.
- **Checkpoints:** CP1-CP4 are complete.
- **Technical approval:** commit `cc20d69`, both implementation-review
  stages approved at round 3 (reviewed head `06cb6d7`).
- **Functional review:** the owner accepted the milestone after the
  functional review against the checklist below (evidence commit
  `dca51ce`), with no findings routed through `/apply-functional-review`.
- **Cutover:** steps 1-4 are done; the evidence is under "Cutover
  evidence" below. Steps 5 and 6 (squash-merge, then the `main` read-back)
  come after this acceptance.

The checkpoint log below is this milestone's permanent record.

#### Checkpoint log

`CP1` (release tooling) complete: `tools/release/` builds the release
source into a package that reproduces every published release (2.3.1 to
2.6.0) byte-for-byte under the pinned `zlib-ng` 1.0.0 wheel; 62 tests green.
After plan amendment 0, CP1 was revalidated at plan revision 6 with its code
unchanged.

`CP2` (CI) complete: `.github/workflows/workflow-ci.yml` (`Workflow CI`:
`tooling`, `package`, `immutability`, `installation`,
`release-source-conformance`, `aggregate`) and `.github/workflows/pr-title.yml`
(`Conventional Commit title`, with `--agree`). Each job's commands ran green
locally against HEAD under Python 3.12 with the pinned wheels; the real CI
evidence is the cutover pull request (plan section 7).

`CP3` (release workflow) complete: `.github/workflows/release.yml`
(`Release`). The local dry run against HEAD and both live rehearsals passed;
the transcript is below.

`CP4` (settings, documentation, cutover runbook) complete:
`.github/repository/merge-settings.json` and `ruleset-main.json` (the
Manager's, plus `workflow-conformance` and `strict` on), `docs/RELEASING.md`
(the release model, CI, recovery, supersession, local build, installation
check, Manager pin, settings, and the cutover runbook), `README.md`, and
`CLAUDE.md`'s repository-owned release text. Every checkpoint is complete.

Implementation self-review complete: two minor defects fixed (a version
pattern that accepted a trailing newline, and an unset `$id` in
`docs/RELEASING.md`'s settings read-back), and the full verification ran
green. Evidence: the requirements ledger,
`docs/ai-workflow/requirements/workflow-repository-setup-ledger.md`.

Implementation review: both stages approved at round 3 (reviewed head
`06cb6d7`); technical approval recorded in `cc20d69`.

### CP3 rehearsal transcript (2026-10-01)

Where: `RodrigoFAbreu/workflow-release-rehearsal`, a throwaway private
repository the owner authorized for this. It had release immutability on
(`immutable-releases: enabled: true`) and was empty when the rehearsal
started. The owner deletes it after CP3. Nothing touched
`RodrigoFAbreu/workflow`'s releases, tags or settings.

Its `main` (`a2b7f21`) held this repository's HEAD release source
(`manifest.json`, `payload/`, `fixtures/`, `templates/`) and
`tools/release/`, with `workflow_version` set to `0.0.1`, plus a README.

How "the release job" was run: a local driver ran `release.yml`'s `release`
job commands, in order and unchanged, against a clone of the rehearsal
repository, with `GH_REPO` pinned to it. Each run started from a fresh
`RUNNER_TEMP`, with local tags dropped and refetched as in a fresh checkout.
The trigger was `main`'s tip, as on the dispatch path. The dispatch's
`Workflow CI` gate was not rehearsed, because the rehearsal repository runs
no CI. Toolchain: Python 3.12.14, `zlib-ng` 1.0.0 with zlib-ng 2.2.5, and
Workflow Manager 1.2.0 (the pinned wheel, sha256 checked).

**Recovery rehearsal**

1. Reproduce a failed publication. Ran `gh release create v0.0.1 --draft
   --target a2b7f21… --title "Workflow 0.0.1" --notes …
   workflow-0.0.1.tar.gz`, then pushed the tag `v0.0.1` at `a2b7f21…`.
   `gh release view v0.0.1` reported `{"isDraft":true,"tagName":"v0.0.1",
   "assets":["workflow-0.0.1.tar.gz"]}`, and `git ls-remote` showed
   `a2b7f21… refs/tags/v0.0.1`.
2. Release job, exit 1. The release list was `[{"isDraft":true,
   "tagName":"v0.0.1"}]`, and `next-release` printed: `refused: version
   0.0.1 is not published, but found a draft release v0.0.1 and the tag
   v0.0.1 at a2b7f21…: a failed publication: remove the residue and re-run
   Release (docs/RELEASING.md, "Recovering from a failed publication")`.
3. Ran D-W0-Recovery steps 1-3 for a draft with its tag. Step 1's two
   inspections found the draft and the tag, as in rehearsal step 1. Then
   `gh release delete v0.0.1 --yes --cleanup-tag`. Afterwards `git
   ls-remote` found no tag, so the conditional `git push origin --delete
   refs/tags/v0.0.1` was not needed. Confirmed: `gh release view v0.0.1`
   prints `release not found`, and `git ls-remote --tags origin
   refs/tags/v0.0.1` prints nothing.
4. Release job, exit 0, on the pending path. The release list was `[]`, and
   `next-release` printed `state=pending`, `version=0.0.1`,
   `target=a2b7f21…`. The build produced `version=0.0.1`, `files=70` and
   `archive_sha256=b03336c8…`. `package verify` printed `release 0.0.1, 69
   files, verified`, and the scratch bootstrap/verify printed `installation
   matches workflow 0.0.1`. `gh release create v0.0.1 --target a2b7f21…
   --latest` ran with the 3 assets, and the read-back printed `ok: v0.0.1
   is published at a2b7f21… with exactly its three built assets`. A rerun,
   exit 0, printed `state=published` and `nothing to release (v0.0.1 read
   back intact)`. `gh release view v0.0.1` showed `isImmutable: true` with
   the three assets.

**Supersession rehearsal**

5. Committed `fix: rehearsal bump to 0.0.2` (manifest only) on `main`
   (`1db4b90`) and built it (`archive_sha256=1200d5a3…`). Ran `gh release
   create v0.0.2 --target 1db4b90… --latest` with only
   `workflow-0.0.2.tar.gz` and `workflow-0.0.2.manifest.json`, which
   published it without `SHA256SUMS`. Before state of `gh release view
   v0.0.2 --json assets,isDraft`: `isDraft:false`, with the manifest asset
   at `sha256:96fc9a98…` and the archive at `sha256:1200d5a3…`.
6. Release job, exit 1. `next-release` printed `state=published` and
   `version=0.0.2`, and the read-back printed: `refused: v0.0.2 does not
   read back as built: missing asset SHA256SUMS; a published release cannot
   be repaired: leave it as it is, never pin it in workflow-manager, and
   supersede it with the next patch version (docs/RELEASING.md,
   "Superseding an incomplete published release")`. It did not report
   "nothing to release". `check-immutable --published <downloaded v0.0.2>`,
   exit 1: `refused: the published assets of v0.0.2 differ from the rebuilt
   package: missing asset SHA256SUMS; …` with the same supersession text.
7. Ran supersession steps 1-4. `v0.0.2` and its tag were left as they were,
   and there was no tooling defect to fix. Committed `fix: supersede
   incomplete release 0.0.2` (`d0fb200`), which changes only
   `manifest.json`. Its checks: `check-title --agree` printed
   `impact=patch` and `version 0.0.2 -> 0.0.3 (patch) agrees with the
   title`. `check-pending` printed `ok: 0.0.2 -> 0.0.3 (patch); release
   source changed: manifest.json`. `check-immutable` printed `ok: version
   0.0.3 is not published`. Pushed it to `main`. Release job, exit 0:
   `next-release` printed `state=pending`, `version=0.0.3`,
   `target=d0fb200…`. `package verify` and the scratch bootstrap/verify
   passed, `gh release create v0.0.3` published, and the read-back printed
   `ok: v0.0.3 is published at d0fb200… with exactly its three built
   assets`. A rerun printed `nothing to release (v0.0.3 read back intact)`.
   `gh release view v0.0.2 --json assets,isDraft` afterwards matched the
   before state byte for byte (`cmp`).

End state of the rehearsal repository: published releases `v0.0.1`,
`v0.0.2` (incomplete, superseded) and `v0.0.3` (Latest), with tags at
`a2b7f21`, `1db4b90` and `d0fb200`.

### Cutover evidence (2026-10-01)

Plan section 7 / `docs/RELEASING.md` "Cutover", steps 1-4, run by the
owner before acceptance and read back here.

1. Pull request #3, `ci: CI, releases and main protection for the workflow
   repository`, from `milestone/workflow-repository-setup` into `main`.
2. On its head `dca51ce`, `Workflow CI` run 36899558841 and the title check:
   `aggregate`, `Conventional Commit title` and `workflow-conformance` (and
   `tooling`, `package`, `immutability`, `installation`,
   `release-source-conformance`) all `SUCCESS`. Logs: `tooling` printed
   `Ran 70 tests` / `OK` with nothing skipped, so the five archive-digest
   reproductions ran; `package` printed
   `archive_sha256=dc86a796…` and `installation matches workflow 2.6.0` for
   the scratch install; `immutability` printed `ok: the rebuilt package
   equals the published assets of v2.6.0`; `installation` printed `.:
   installation matches workflow 2.6.0`. `mergeStateStatus` `CLEAN`.
3. Settings read back: `allow_squash_merge` true, `allow_merge_commit` and
   `allow_rebase_merge` false, squash title `PR_TITLE`, message `BLANK`.
   Ruleset `main` (id 24322847): target `branch`, enforcement `active`, no
   bypass actors, rules `deletion`, `non_fast_forward`,
   `required_linear_history`, `pull_request`, `required_status_checks`.
4. Installation-integrity probe: draft pull request #4 (head `a0a433c`,
   `Workflow CI` run 36901180854). `installation` failed with `modified:
   .claude/commands/accept-milestone.md`, and `aggregate` and
   `workflow-conformance` failed. The pull request is closed, unmerged.

### Current blockers

None.

### Active plan

None, because the milestone is complete. The plan document stays at
`docs/ai-workflow/WORKFLOW_REPOSITORY_SETUP_PLAN.md` (revision 6, plan
approval `CURRENT`) instead of being archived: `docs/RELEASING.md`,
`tools/release/release.py` and the three CI workflows cite it as the design
record.

### Next action

`workflow-repository-setup` is complete. Next:
1. Finish the cutover (plan section 7, steps 5-6): bring pull request #3 up
   to this acceptance commit, wait for its checks, squash-merge it, then
   confirm `main`'s `Workflow CI` push run is green and its `Release` run
   ends with "nothing to release (v2.6.0 read back intact)", with no new
   release or tag. These are the owner's actions.
2. Then run `/milestone-plan` for W1 in `docs/ROADMAP.md`: Workflow 2.7,
   the first release developed here (Orchestration Protocol v1, and the
   `v2.6.0-001` and `v2.6.0-002` follow-ups).

### Functional review checklist

W0 is a `process` milestone: the "product" is the release tooling, CI,
release workflow, settings data and runbook. Nothing here pushes, applies
settings or publishes; those are the cutover (plan section 7,
`docs/RELEASING.md` "Cutover"), which comes after this review.

**Setup**

S1. On branch `milestone/workflow-repository-setup`, clean tree, Linux
    x86_64 with Python 3.12 and an authenticated `gh` (read access to
    `RodrigoFAbreu/workflow` is enough).
S2. Create the pinned build runtime as `docs/RELEASING.md` "Building
    locally" says, but outside the checkout (`.venv-release` is not
    gitignored and would dirty the tree):
    ```bash
    python3.12 -m venv /tmp/w0-venv
    . /tmp/w0-venv/bin/activate
    python -m pip install --only-binary=:all: --require-hashes -r tools/release/deflate-requirements.txt
    ```
    Expected: the `zlib-ng` 1.0.0 wheel installs with its hash checked.
S3. Save the live release list once:
    `gh release list --json tagName,isDraft --limit 1000 > /tmp/releases.json`.

No test data to seed: the published tags `v2.3.1`..`v2.6.0` and their
assets are the data.

**Flows**

F1. Tooling tests: `python tools/release/release_test.py`.
    Expected: `Ran 70 tests`, `OK`, including the five archive-digest
    reproductions; none skipped.
F2. Reproduce the published 2.6.0 package:
    `python tools/release/release.py build --commit v2.6.0 --out "$(mktemp -d)"`.
    Expected: `version=2.6.0`, `zlib_ng=2.2.5`, `archive_sha256=dc86a796…`
    and `manifest_sha256=d92517a2…`, equal to the `SHA256SUMS` asset of the
    `v2.6.0` release.
F3. Build HEAD: `python tools/release/release.py build --commit HEAD --out "$(mktemp -d)"`.
    Expected: `commit=` is HEAD, and `files=70`, `tar_sha256`,
    `archive_sha256` and `manifest_sha256` equal F2's (the release source
    is unchanged on this branch).
F4. Title grammar and agreement (`check-title "<title>" --agree`):
    - `"ci: CI, releases and main protection for the workflow repository"`
      → exit 0, `impact=none`, `2.6.0 -> 2.6.0 (none) agrees`;
    - `"feat: something"` → exit 1, refused: impact minor but the version
      change is none;
    - `"Update stuff"` → exit 1, `invalid pull-request title`.
F5. Release decision on the live list:
    `python tools/release/release.py next-release --trigger HEAD --releases /tmp/releases.json`.
    Expected: exit 0, `state=published`, `version=2.6.0`,
    `target=2d5b760…` (the commit `v2.6.0` was published from), i.e.
    merging this branch would release nothing.
F6. Release-source guards:
    `check-pending --releases /tmp/releases.json` → `ok: 2.6.0 -> 2.6.0
    (none); release source unchanged`; `check-immutable --releases
    /tmp/releases.json` → `ok: release source unchanged since v2.6.0`.
F7. Negative guard (local only, then discard): edit any file under
    `payload/` without bumping `manifest.json`, commit it on a scratch
    branch, and rerun `check-immutable`.
    Expected: exit 1, `refused: version 2.6.0 is published, and the
    release source differs from v2.6.0 in <that path>: a published release
    never changes; bump the version (D-W0-Immutable)`. Then `git switch milestone/workflow-repository-setup` and delete
    the scratch branch.
F8. Release-source conformance fixture:
    `python tools/release/release.py stage-conformance --commit HEAD --out "$(mktemp -d)/fx"`
    (the `--out` path must not exist yet).
    Expected: exit 0, prints `fixture=<path>`; the staged fixture is what CI's
    `release-source-conformance` job runs its suites in.
F9. Installation integrity: `workflow-manager verify .`.
    Expected: `installation matches workflow 2.6.0`.
F10. Read the CI and release workflows
    (`.github/workflows/workflow-ci.yml`, `pr-title.yml`, `release.yml`).
    Expected: job names `tooling`, `package`, `immutability`,
    `installation`, `release-source-conformance`, `aggregate`; check name
    `Conventional Commit title`; `Release` triggers only on a green
    `Workflow CI` run on `main` and on `workflow_dispatch`, with job-level
    concurrency and no path that moves a tag or replaces an asset.
F11. Read `.github/repository/merge-settings.json` and `ruleset-main.json`.
    Expected: squash merges only (title = PR title, blank body); ruleset on
    the default branch with no deletion, no force-push, linear history,
    pull requests merged by squash only, required checks `aggregate`,
    `Conventional Commit title`, `workflow-conformance`, `strict` on, no
    bypass actors. These are what cutover step 3 applies.
F12. Read `docs/RELEASING.md` end to end, and `README.md`/`CLAUDE.md`'s
    release text. Expected: a release, recovery from a failed publication,
    supersession of an incomplete release, local build, Manager-pin bump
    and the cutover runbook are each understandable and executable as
    written, and agree with the CP3 rehearsal transcript above.
F13. Optional: inspect the rehearsal repository
    (`gh release list -R RodrigoFAbreu/workflow-release-rehearsal`).
    Expected: `v0.0.1`, `v0.0.2` (incomplete, superseded) and `v0.0.3`
    (Latest), as the transcript records; delete it afterwards as planned.

**Known limitations / out of scope**

- No real GitHub Actions run exists yet: CI and `Release` are proven by
  local runs of their commands and the CP3 rehearsal. The first real
  evidence is the cutover pull request (cutover steps 2 and 4).
- Repository settings and the ruleset are not applied; that is cutover
  step 3, owner-only.
- W0 publishes no release; the manifest stays at 2.6.0.
- Locally, a read-only token does not see draft releases, so F5 cannot
  show a draft residue; `release_test.py` and the CP3 rehearsal cover it.
- The `immutability` job's comparison against downloaded `v2.6.0` assets
  runs in CI; locally, F2 is the equivalent byte check.

<!--
This file is `workflow_state.FUNCTIONAL_CHECKLIST_PATH`. It is
repository-local state: workflow-manager generates it once at bootstrap and
never overwrites it on update.
-->
