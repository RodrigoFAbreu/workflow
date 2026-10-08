# Active Milestone

## Milestone

**Implementing** (CP1 to CP6 complete). W3: `legacy-retire-and-default-version` (`process`, governing
version `2.2`), branch `milestone/legacy-retire-and-default-version`, base
`f00c1c3` (the release source is Workflow 2.8.0; this repository's own
installation is also 2.8.0 with automatic gates and no `GATE_POLICY.json`).
The plan is `docs/ai-workflow/LEGACY_RETIRE_AND_DEFAULT_VERSION_PLAN.md`
(revision 1). W3 goes first, ahead of the update tools, to unblock RepFlow.

## Goal

Workflow 2.9.0 on Orchestration Protocol 1.2, a minor release with three parts:

1. **`/retire-legacy-work-item <id>`**, a new user-only command that moves a
   dormant `LEGACY_READY` work item to `MILESTONE_COMPLETE` as already
   finished, keeping its `LEGACY_V1` technical approval untouched, with an
   auditable commit (`Workflow-Legacy-Retirement` and `Workflow-Work-Item`
   trailers). It refuses any other phase, an active item and unfinished
   children, and never runs the stale-approval or promotion checks. The
   protocol reports it as a user-only alternative of blocked row 3, never as
   automatic. The motivating case is RepFlow's `milestone-8`.
2. **Default governing version 2.2 for new installations** (the bootstrap
   template; `default_config()`, the pre-activation fail-safe, is unchanged,
   see `OD-W3-2`). An update never rewrites an existing config, and items keep
   their version. It matters because a 2.1 item keeps a human technical gate
   under the 2.8.0 gate policy.
3. **Defect `v2.6.0-003`**: a phase-aware `IncompleteOwnCheckpointsError`
   message; a governing-`1` item with a state entry can reach review from
   `IMPLEMENTING` and pass acceptance (no `1` command text changes); and a new
   `/resume-implementation` returns a 2.1/2.2 item with an outstanding
   checkpoint from `AWAITING_FUNCTIONAL_REVIEW` to `IMPLEMENTING`.
   `PLANNING`/`AMENDING_PLAN` at `1` stay reported (`OD-W3-7`).

## Current checkpoint

**Implementing.** The plan (revision 6) is approved; CP1 to CP6 are complete.

`CP6` (documentation, roadmap and release 2.9.0) complete, in the release source only:
`manifest.json` names `2.9.0`, lists the two new commands (`retire-legacy-work-item`,
`resume-implementation`), refreshes every changed `sha256`/`size` (including the
template) and `counts`, and carries W3 rationales; `WORKFLOW_RELEASE` is `2.9.0`;
`MILESTONE_WORKFLOW.md` describes the resume and retire entries; `docs/troubleshooting.md`
and `docs/install.md` state the older-release limit of retirement and the two new
commands; `docs/ROADMAP.md` gains the W3 row, a "Workflow 2.9.0" entry and the
`v2.6.0-003` disposition (corrected origin; fixed except the two `1` planning phases).
`tools/release/manager-pin.json` is unchanged (Manager 1.4.0).

`CP5` (`v2.6.0-003` (b)) complete, in the release source only: the user-only
`/resume-implementation <id>` (`disable-model-invocation: true`, `state_writer: true`,
a current-turn confirmation naming the exact id and `resumption`). The writer
`workflow_state.resume_implementation` validates the confirmation first
(`validate_user_only_confirmation`), holds `lifecycle_lock` and runs
`_enforce_claim_lifecycle` (it joins the claim side, `v2.4.0-002`), then makes one
`state_transaction` around the pure `resume_implementation_state`. That moves a
`2.1`/`2.2` item from `AWAITING_FUNCTIONAL_REVIEW` with an outstanding checkpoint
and a `CURRENT` covering plan approval to `IMPLEMENTING`, marking the technical
approval `STALE` (an already-`STALE` one is accepted, none is refused), and writes
only `phase`, `technical_approval.status`, `state_revision` and `last_transition`;
`validate_resume_implementation_commit` checks its commit (a `Resume-Confirmation:`
line and the `Workflow-Work-Item` trailer). Protocol `1.2` gains the user-only
`implementation.resume` action (no edge, never automatic) as the first alternative
of row 38c, which stays `blocked` with a rewritten text (the hand-constructed
origin, not a legacy promotion) and remedy. `accept-milestone.md` step 2a and
`apply-functional-review.md` name the command in their 2.1/2.2 spans; the
operator reference, protocol document and schema are updated. Tests: writer
fields, refusals and confirmation order, the real registry and a promoted-shape
refusal, commit validation, linked-worktree lifecycle witnesses, the resumed item
reaching a claim and self-review, the census, the command text, row 38c and its
alternative, and the 1.1-consumer model.

`CP4` (`v2.6.0-003` (a, implementation entry) and (c)) complete, in the release
source only: `record_bundle_generation` accepts `implementation` from
`IMPLEMENTING` for a governing-`1` item alone (the five ordinary fields, no
checkpoint-status write; the record commit validates and the provenance interval
is reachable); `IncompleteOwnCheckpointsError` is phase- and version-aware
(`_incomplete_own_checkpoints_route`); row 6a keeps its shape (`blocked`,
unconditional, no `EDGES`) with phase-aware text and a `milestone-implement`
remedy at `IMPLEMENTING`; row 38b's text states the residual; the protocol
document matches. Tests: the `1` entry, the commit/interval, `IMPLEMENTING`
staying illegal for 2.1/2.2 and `post-fix`, step 2a for a registry-less `1` item
(passes) and a non-terminal registry (refused), `verify` healthy past the entry,
no edge from `IMPLEMENTING` at `1`, the message variants, and the `V280`
equivalence with the 6a/38b exemptions. No command text is edited.

`CP1` (new installations default to 2.2) complete: the template
`templates/docs/ai-workflow/WORKFLOW_CONFIG.json` now defaults to `"2.2"` with
supported versions `1`, `2.1`, `2.2`; `default_config()` is unchanged. Tests in
`workflow_state_test.py` and `workflow_integration_test.py` prove the template
validates and an item created from it is 2.2. `docs/gates.md`, `docs/overview.md`
and `docs/install.md` and the payload's `IMPLEMENTATION_REVIEW_WORKFLOW.md` carry
the 2.9.0 default. The template digest and derivation text in `manifest.json` are
refreshed in CP6, as planned.

`CP3` (Protocol 1.2) complete, in the release source only: `PROTOCOL_VERSION`
`1.2`; the user-only action `legacy.retire` (no `EDGES` entry, so never
automatic); row 3 stays `blocked`, names both routes in its remedy and carries
`alternatives: [legacy.retire]` (remedy command `retire-legacy-work-item`); the
schema's two `action.id` enums and the specification (action table, row 3, version
statements) match. Tests: row 3 at every governing version, `NEW_1_2_ACTION_IDS`,
a 1.1-consumer model (`TestUnaware1_1Consumer`), and the `V280` loader with
`TestEquivalenceAgainstV280` (INV-1 against the published 2.8.0 modules, with the
enumerated exemptions and the added `LEGACY_READY`, governing-`1` `IMPLEMENTING`
and retired-item scenarios). The whole protocol suite is green. `WORKFLOW_RELEASE`
stays `2.8.0` until CP6.

`CP2` (retire a dormant legacy item) complete, in the release source only:
`retire_legacy_work_item(state, id, now, user_confirmation)` (pure, run in
`state_transaction`; confirmation checked first, then phase exactly
`LEGACY_READY`, not active, no unfinished children; changes only `phase`,
`current_checkpoint_id`, `state_revision`, `last_transition`), with
`USER_ONLY_ACTION_STAGES` and the exact-token `validate_user_only_confirmation`,
the three refusal classes, `discover_legacy_retirement_commit`,
`validate_legacy_retirement_commit` and `LEGACY_RETIREMENT_TRAILER`; the
user-only command `retire-legacy-work-item.md` and its operator-reference
section. INV-6: `is_retired_legacy_item` (`workflow_gate_policy.py`) is enforced
in `reopen_work_item` and `begin_pr_review` (`reopen_retired_legacy_item`) and
in `_row_38d` (a direct call), with the four normative edits (protocol row 38d,
`apply-pr-review.md`, `GATE_POLICY.md`, the `reopen_work_item` docstring).
Registration: the command count is 21, `TestCommandSentences.SCOPED` and the
derivation test cover the new trailer, the phase-writer census lists the new
writer. One addition the plan did not name: the two child-lifecycle completeness
tests exempt `retire-legacy-work-item.md` (`_CHILD_SEQUENCE_EXEMPT_COMMANDS`; it
still must take a work-item id), because a remediation child is never a legacy
item. The `manifest.json` digests, including the new command and the
`apply-pr-review.md` roster hash, are refreshed in CP6, as planned.

## Current blockers

None. Open decisions for the reviewer and the user are in the plan's section 4
(`OD-W3-2` is a correction of the request's wording: `default_config()` is the
fail-safe, default `1`, not 2.1).

## Active plan

`docs/ai-workflow/LEGACY_RETIRE_AND_DEFAULT_VERSION_PLAN.md`.

## Next action

Plan review (`/review-plan legacy-retire-and-default-version`), then the user's
plan approval (`/approve-review plan legacy-retire-and-default-version`) unless
the plan gate is automatic. The sections below are the completed W2 and W1
milestones' records.

## Functional review checklist

W2 is a `process` milestone: the "product" is Workflow 2.8.0 (the gate policy,
automatic approvals and acceptance, reopening, protocol 1.1, and the package).
Every flow runs **offline, in a disposable scratch directory or clone**, never in
this checkout. Nothing here pushes, opens a pull request, calls real GitHub
(`gh` is simulated through the test seams and a parser fed raw output),
changes GitHub settings or publishes a release; the cutover (plan section 7) is
the owner's and comes after acceptance. Never use `git stash`.

**Precondition (a W1 lesson):** any step that needs local `main` first runs
`git fetch origin` and uses `origin/main` (the base `d14e0a7` is `origin/main`'s
tip; verify with `git rev-parse origin/main`). No flow below needs a local
`main`; the clones of S3 take it from `origin`.

**Round 2** (after the bounded F1 fix `007f13b`, implementation revision 3,
technical approval `104e65f`). Round 1's F1 was that an uncommitted
`GATE_POLICY.json` was reported adopted while the committed policy stayed in
force; the fix refuses it (`GatePolicyFileUncommittedError`) and updates
`GATE_POLICY.md`, `adopt-gate-policy.md` and the operator reference. Which
flows the fix could affect, so the executor re-runs those and cites round-1
evidence for the rest (the fix touched `workflow_state.py`'s preview and
adoption, `workflow_gate_policy.py`'s file-versus-`HEAD` comparison, the
gate-policy test file, three documents and the manifest digests):

| Flow | Round 2 | Why |
|---|---|---|
| F1 default policy | cite round 1 | no preview or adoption is involved |
| F2 toggles, floor, adoption | **re-run** | its adoption step commits the file first, and it runs the gate-policy classes |
| F3 adoption order | **re-run (changed: now a real flow)** | the fixed behavior itself |
| F4 CLI lifecycles | cite round 1 | protocol and lifecycle paths untouched; re-run if any F11 suite fails |
| F5 automatic plan and technical approval | cite round 1 | row 38i remedy text only changed in documents |
| F6 automatic acceptance, forge | cite round 1 | untouched |
| F7 reopening | cite round 1 | untouched |
| F8 protocol 1.1 | cite round 1 | untouched |
| F9 all-human equals 2.7.0 | cite round 1 | the all-human path never adopts a file |
| F10 package, update from 2.7.0 | **re-run** | the manifest digests changed (the 2.8.0 digests below are the preparation run's, not round 2's: compare reproducibility, and report the new digests) |
| F11 automated suites | **re-run (the gate-policy suite, 284 before the fix plus the new regression test(s); the others may cite round 1 only if their `Ran` counts are unchanged)** | the regression test is in `workflow_gate_policy_test.py` |
| F12 installation and documents | **re-run (changed: ROADMAP docs check added)** | documents changed, and the ROADMAP check is new |

**Setup**

S1. On branch `milestone/gate-policy-and-reopening`, clean tree. Set the pinned
    runtime (Python 3.12, `zlib-ng` 1.0.0, Workflow Manager 1.2.0) and a scratch
    directory:
    ```bash
    git fetch -q origin
    V=/home/rodrigo/.claude/projects/-home-rodrigo-Workspace-workflow-manager/orchestrator-files/runs-workflow/w0-ext-impl-r1/venv
    S=$(mktemp -d /tmp/w2-review.XXXX); echo $S
    REPO=$PWD; R=tools/release/release.py
    new_target() { D=$S/$1; mkdir $D && git -C $D init -q \
        && git -C $D -c user.name=t -c user.email=t@t commit -q --allow-empty -m init \
        && $V/bin/workflow-manager --release-dir $S/rel/workflow-2.8.0 bootstrap $D >/dev/null; }
    ```
    Run every step from the repository root unless it says `cd`.
S2. Build the 2.8.0 package, verify it, and unpack it:
    ```bash
    $V/bin/python $R build --commit HEAD --out $S/build
    $V/bin/workflow-manager package verify $S/build/workflow-2.8.0.tar.gz \
        --sha256 "$(grep tar.gz $S/build/SHA256SUMS | cut -d' ' -f1)"
    mkdir $S/rel && tar -xzf $S/build/workflow-2.8.0.tar.gz -C $S/rel
    ```
    Expected: `version=2.8.0`, `files=81`, `zlib_ng=2.2.5`; `release 2.8.0, 80
    files, verified`.
S3. A disposable clone of the repository on the milestone branch, with its tags
    (the all-human equivalence and update-simulation tests read the `v2.7.0`
    tag from git):
    ```bash
    git clone -q --no-hardlinks . $S/clone
    git -C $S/clone checkout -q milestone/gate-policy-and-reopening
    git -C $S/clone tag | grep -x v2.7.0
    ```
S4. A scratch installation of 2.8.0 and the protocol shorthand:
    ```bash
    new_target t0
    P() { (cd $S/t0 && $V/bin/python scripts/workflow_protocol.py "$@"); }
    ```
    Expected: nothing printed by `new_target`; `$V/bin/workflow-manager
    --release-dir $S/rel/workflow-2.8.0 verify $S/t0` prints `installation
    matches workflow 2.8.0`.

No test data to seed: the scripts below build their own scratch repositories
and the test harness seeds its own work items.

**Flows**

F1. Default policy: gates automatic on evidence (no `GATE_POLICY.json`).
    `P verify` and the `gate_policy` section of `gp_flows.py` (script in F2).
    Expected: with no policy file, `P verify` is `healthy: true` and its
    `gate_policy` check is `pass`, detail `no gate policy file; the default
    applies`; `effective_policy` has `source=default` and `plan_approval`,
    `technical_approval` and `acceptance` all `automatic`.
    Then the disposition: `P next-action` (no work item) is row `1`, action
    `plan.start`, disposition `automatic`. The automatic path end to end is the
    lifecycle driver of F4 (`TestAutomaticLifecycle`: a `2.2` item planned,
    implemented and accepted with no person, then reopened by a
    `changes_requested` fact and completed again).
F2. Human approval restored by the toggles, and the tighten-only floor. Save
    this as `$S/gp_flows.py` (it drives the installed scripts directly and
    prints one line per step), then run it in a fresh target:
    ```bash
    cat > $S/gp_flows.py <<'PY'
    import json, subprocess, sys
    sys.path.insert(0, "scripts")
    import workflow_gate_policy as g
    import workflow_state as ws
    from pathlib import Path
    root = Path(".").resolve(); POL = root / "docs/ai-workflow/GATE_POLICY.json"
    GATES = ("plan_approval", "technical_approval", "acceptance")
    tick = [0]
    def now():
        tick[0] += 1; return f"2026-10-03T13:00:{tick[0]:02d}Z"
    def git(*a):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                              cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    def put(policy):
        if policy is None: POL.unlink(missing_ok=True)
        else: POL.write_text(json.dumps(policy))
    def show(label):
        e = g.effective_policy(root)
        print(f"{label:52} {e['source']:22}", {k: g.gate_mode(e, k, "2.2") for k in GATES})
    def verify():
        status, detail = g.verify_check(root)
        print(f"    verify gate_policy = {status}: {detail[:110]}")
    git("add", "-A"); git("commit", "-q", "-m", "install")
    print("== flow 1: default"); show("no GATE_POLICY.json"); verify()
    print("== flow 2: toggles (file edits, uncommitted)")
    put({"schema_version": 1, "human_approval": True}); show("human_approval true")
    put({"schema_version": 1, "gates": {"plan_approval": {"human": True}}}); show("only plan_approval human")
    put({"schema_version": 1, "gates": {"acceptance": {"human": True}}}); show("only acceptance human")
    put({"schema_version": 1, "human_approval": True, "gates": {"acceptance": {"human": False}}}); show("master human, acceptance forced automatic")
    print("== flow 3: tighten-only")
    put({"schema_version": 1, "human_approval": True}); git("add", "-A"); git("commit", "-q", "-m", "human policy")
    print("recorded floor commit:", (ws.commit_gate_policy_floor(root, now=now()) or "none")[:12])
    put({"schema_version": 1, "human_approval": False}); show("file edited back to automatic"); verify()
    put(None); show("file deleted"); verify()
    put({"schema_version": 1, "human_approval": False}); git("add", "-A"); git("commit", "-q", "-m", "loosened policy file")
    pv = ws.gate_policy_adoption_preview(root)
    print("preview: loosened", pv["loosened"], "| lowered", pv["lowered"], "| digest12", pv["digest"][:12])
    try: ws.adopt_gate_policy(root, confirmation="yes", now=now())
    except g.GatePolicyConfirmationRejectedError as e: print("wrong confirmation refused:", type(e).__name__)
    sha = ws.adopt_gate_policy(root, confirmation=f"I adopt gate_policy {pv['digest'][:12]}", now=now())
    print("adoption commit", sha[:12], "|", git("log", "-1", "--format=%b", sha).strip().splitlines()[-1][:60])
    show("after /adopt-gate-policy"); verify()
    print("    gate_lowering:", json.dumps(g.gate_lowering_event(root))[:240])
    PY
    new_target t3 && (cd $S/t3 && $V/bin/python $S/gp_flows.py)
    ```
    (Remove the heredoc's indentation if pasting.) Expected lines, in order:
    - `no GATE_POLICY.json`: `default`, all three `automatic`; `verify` `pass`.
    - `human_approval true`: `file_tightened`, all three `human`.
    - `only plan_approval human`: plan `human`, the other two `automatic`;
      `only acceptance human`: acceptance `human`, the other two `automatic`.
    - `master human, acceptance forced automatic`: plan and technical `human`,
      acceptance `automatic`.
    - After committing the human file and recording the floor (a commit sha is
      printed): `file edited back to automatic` is `file_loosening_ignored`
      with all three still `human`, and `verify gate_policy` is `warn`
      (`loosens ... the loosening is ignored (only /adopt-gate-policy
      loosens)`); `file deleted` is source `floor`, all three `human`,
      `verify` `warn` (`the recorded floor holds a setting ... no longer
      carries`).
    - (Round 2: the loosened file is committed before the preview; an
      uncommitted one is refused, which is F3.) The adoption preview lists the three `human` settings under `loosened`
      and the same three under `lowered`; the wrong confirmation is refused
      with `GatePolicyConfirmationRejectedError`; the adoption commit's last
      body line is `Workflow-Gate-Policy-Adoption: <64 hex>`; `after
      /adopt-gate-policy` is source `adopted`, all three `automatic`; `verify`
      is `warn` with `gate-lowering event: the adoption 1b76de4f95ab (commit
      ...) lowers plan_approval.human, ...`; `gate_lowering` is an object with
      `sha256`, `adopted_at`, `lowered` and `commit`. That `warn` and the object
      are the reported gate-lowering event.
    `/adopt-gate-policy` itself is a user-only command: the script calls its
    function (`workflow_state.adopt_gate_policy`) with the confirmation text
    inside a disposable repository, which is what a scratch test of the
    behavior needs; never run the slash command from this review.
    Then the dedicated tests, in the S4 installation:
    ```bash
    (cd $S/t0/scripts && $V/bin/python workflow_gate_policy_test.py TestPolicySchema \
        TestEffectivePolicy TestTightenOnlyAfterAdoption TestFloorRatchet TestProvenance \
        TestSquashMerge TestAdoptionCommit TestAdoptionCommand TestGateLoweringEvents \
        TestVerifyCheck TestAllHumanEquivalence 2>&1 | tail -4)
    ```
    Expected: `OK`, none failed.
F3. Adoption order: an uncommitted policy file is refused; a committed one
    is adopted (functional review F1, fixed in `007f13b`; round 2 turns the
    former probe into a flow with expected results). Two scripts, each in a
    fresh target. Case A, a modified file:
    ```bash
    cat > $S/adopt_order.py <<'PY'
    import hashlib, json, subprocess, sys
    sys.path.insert(0, "scripts")
    import workflow_gate_policy as g, workflow_state as ws
    from pathlib import Path
    root = Path(".").resolve(); POL = root / "docs/ai-workflow/GATE_POLICY.json"; STATE = root / "docs/ai-workflow/WORKFLOW_STATE.json"
    GATES = ("plan_approval", "technical_approval", "acceptance")
    def git(*a):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                              cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    def show(label):
        e = g.effective_policy(root)
        print(f"{label:46} {e['source']:22}", {k: g.gate_mode(e, k, "2.2") for k in GATES})
    def snap(): return (git("rev-parse", "HEAD"), hashlib.sha256(STATE.read_bytes()).hexdigest())
    def refused(label, fn):
        before = snap()
        try: fn(); print(f"{label:46} NOT REFUSED")
        except ws.GatePolicyFileUncommittedError as e: print(f"{label:46} refused {type(e).__name__}")
        print(f"    nothing written: {snap() == before} | gate_lowering event: {g.gate_lowering_event(root)}")
    def attempt(label):
        refused(label + " (preview)", lambda: ws.gate_policy_adoption_preview(root))
        refused(label + " (adopt)", lambda: ws.adopt_gate_policy(root, confirmation="I adopt gate_policy 000000000000", now="2026-10-03T13:00:09Z"))
    git("add", "-A"); git("commit", "-q", "-m", "install")
    print("== case A: a modified file")
    POL.write_text('{"schema_version": 1, "human_approval": true}'); git("add", "-A"); git("commit", "-q", "-m", "human policy")
    print("floor commit:", (ws.commit_gate_policy_floor(root, now="2026-10-03T13:00:01Z") or "none")[:12])
    POL.write_text('{"schema_version": 1, "human_approval": false}')       # edited, NOT committed
    attempt("loosened file uncommitted"); show("effective policy after the refusals")
    git("add", "-A"); git("commit", "-q", "-m", "loosened policy file")
    pv = ws.gate_policy_adoption_preview(root); print("preview after the commit: loosened", pv["loosened"], "| lowered", pv["lowered"])
    sha = ws.adopt_gate_policy(root, confirmation=f"I adopt gate_policy {pv['digest'][:12]}", now="2026-10-03T13:00:03Z")
    print("adoption commit", sha[:12]); show("after committing and adopting")
    ev = g.gate_lowering_event(root); print("    gate_lowering events:", 1 if ev else 0, json.dumps(ev)[:160])
    PY
    new_target t3b && (cd $S/t3b && $V/bin/python $S/adopt_order.py)
    ```
    Case B, a new file (no policy file committed before):
    ```bash
    cat > $S/adopt_new.py <<'PY'
    import hashlib, subprocess, sys
    sys.path.insert(0, "scripts")
    import workflow_gate_policy as g, workflow_state as ws
    from pathlib import Path
    root = Path(".").resolve(); POL = root / "docs/ai-workflow/GATE_POLICY.json"; STATE = root / "docs/ai-workflow/WORKFLOW_STATE.json"
    def git(*a):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *a],
                              cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    def snap(): return (git("rev-parse", "HEAD"), hashlib.sha256(STATE.read_bytes()).hexdigest())
    git("add", "-A"); git("commit", "-q", "-m", "install")
    print("== case B: a new file")
    POL.write_text('{"schema_version": 1, "human_approval": true}')        # new, NOT committed
    for label, fn in (("preview", lambda: ws.gate_policy_adoption_preview(root)),
                      ("adopt", lambda: ws.adopt_gate_policy(root, confirmation="I adopt gate_policy 000000000000", now="2026-10-03T13:00:09Z"))):
        before = snap()
        try: fn(); print(f"{label:8} NOT REFUSED")
        except ws.GatePolicyFileUncommittedError as e: print(f"{label:8} refused {type(e).__name__}")
        print(f"    nothing written: {snap() == before} | gate_lowering event: {g.gate_lowering_event(root)}")
    git("add", "-A"); git("commit", "-q", "-m", "policy file")
    pv = ws.gate_policy_adoption_preview(root); print("preview after the commit: loosened", pv["loosened"], "| lowered", pv["lowered"])
    PY
    new_target t3c && (cd $S/t3c && $V/bin/python $S/adopt_new.py)
    ```
    Expected, case A, in order: a floor commit sha is printed; `loosened file
    uncommitted (preview)` and `(adopt)` are each `refused
    GatePolicyFileUncommittedError`, and under each `nothing written: True |
    gate_lowering event: None` (HEAD and the state file's sha256 are
    unchanged); `effective policy after the refusals` is
    `file_loosening_ignored` with all three `human`; after committing the
    file, `preview after the commit` lists the three `human` settings under
    `loosened` and under `lowered`; an `adoption commit` sha is printed;
    `after committing and adopting` is source `adopted` with all three
    `automatic`; `gate_lowering events: 1` (exactly one, an object with
    `sha256`, `adopted_at`, `lowered`). Expected, case B: `preview` and
    `adopt` are each `refused GatePolicyFileUncommittedError` with `nothing
    written: True | gate_lowering event: None`; after committing the file the
    preview no longer refuses (it prints `loosened [] | lowered []`: the new
    file only tightens, so there is nothing to lower). Any `NOT REFUSED`, any
    `nothing written: False`, a lowering event before the commit, or more than
    one event after it is a finding. (The confirmation text in these scripts
    is a placeholder in the refused calls: the refusal precedes the
    confirmation check.) The same refusal and the committed adoption are
    pinned by the F2 gate-policy test classes (`TestAdoptionCommand`).
F4. Automatic, mixed and all-human lifecycles through the real protocol CLI.
    The installed lifecycle tests drive a `2.2` item with every protocol call
    replaced by a subprocess of `scripts/workflow_protocol.py`:
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
        ["TestLifecycleEndToEnd2_2", "TestLifecycleEndToEndV1", "TestAutomaticLifecycle",
         "TestMixedLifecycle", "TestAllHumanLifecycle"], t)
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    print("CLI calls by operation:", dict(Counter(calls)))
    sys.exit(0 if res.wasSuccessful() else 1)
    PY
    (cd $S/t0 && $V/bin/python $S/cli_lifecycle.py 2>&1 | tail -8)
    ```
    Expected: `Ran 11 tests`, `OK`, and `CLI calls by operation` showing
    `next-action`, `reconcile` and `record-external-result` (273, 107 and 36
    on the preparation run). The tests named: `TestAutomaticLifecycle` (planned,
    implemented and accepted with no person; a `changes_requested` fact reopens
    the item and it completes again), `TestMixedLifecycle` (only the plan human,
    only the technical gate human, only acceptance human each stop exactly at
    that gate and run the rest automatically), `TestAllHumanLifecycle` (every
    gate stops for a person; a red fact reopens the item).
F5. Automatic plan and technical approval, distinct reviewer families, and the
    single-family remedies. Run in the S4 installation:
    ```bash
    (cd $S/t0/scripts && $V/bin/python workflow_gate_policy_test.py -v TestEvaluateGateHuman \
        TestEvaluateGateAutomatic TestPolicySatisfiedRecord TestReviewerModelParsing \
        TestAuditKeysAndTheIngestRefusal TestTrustBoundaryAndPlanCommit \
        TestVerifyWarnsOnAnUnreferencedRun 2>&1 | grep -E "ok$|FAIL|ERROR|^Ran|^OK")
    ```
    Expected: `OK`, none failed, and in particular these pass:
    `test_a_satisfied_plan_gate` and `test_each_failing_input_is_unsatisfiable`
    (a gate is satisfied only with an `APPROVE` whose bundle id matches, the
    audit keys and distinct families); `test_a_human_gate_never_satisfies`;
    `test_governing_versions_that_have_no_ledger_stay_human`;
    `test_an_equal_family_is_refused_naming_the_value` and
    `test_the_default_refuses_a_manual_approve_without_a_model_and_writes_nothing`
    (an `APPROVE` with the same family, or none, is refused before any write);
    the remedies: `test_remedy_one_a_second_family_is_recorded_with_the_audit_keys`,
    `test_remedy_two_the_gate_turned_human_admits_the_same_verdict_with_2_7_0_bytes`,
    `test_no_require_adopted_before_the_bundle_admits_one_family`, and
    `test_an_adoption_at_the_open_phase_is_not_a_remedy`;
    `test_a_revise_is_admitted_with_no_line`.
    The reviewer-family rule in one line: `Reviewer model: anthropic/opus` and
    `anthropic/sonnet` are one family; `anthropic/...` against `openai/...` are
    two (`TestReviewerModelParsing`).
F6. Automatic acceptance: current evidence plus a GitHub-sourced pull-request
    fact; blocks on stale, red and undecidable. First the fixed query's parser,
    fed simulated `gh` output (no `gh`, no network). Save and run:
    ```bash
    cat > $S/forge_demo.py <<'PY'
    import json, sys
    sys.path.insert(0, "scripts")
    import workflow_forge as f
    C = "c" * 40
    def pr(n=1, state="OPEN", head=C, decision=None, checks=("SUCCESS",), reviews=()):
        return {"number": n, "url": f"https://github.com/o/r/pull/{n}", "state": state, "headRefOid": head,
                "reviewDecision": decision, "reviews": list(reviews),
                "statusCheckRollup": [{"name": f"job{i}", "status": "COMPLETED", "conclusion": c} for i, c in enumerate(checks)]}
    def run(label, raw):
        try:
            fa = f.parse_forge_raw(raw if isinstance(raw, str) else json.dumps(raw), "o/r", C)
            print(f"{label:34} state={fa['state']:7} head={str(fa['head'])[:4]} decision={fa['review_decision']} checks={fa['checks']['state']}")
        except f.ForgeError as e:
            print(f"{label:34} REFUSED {type(e).__name__}: {str(e)[:70]}")
    run("green open PR", [pr()])
    run("stale: PR head is another commit", [pr(head="d" * 40)])
    run("red checks", [pr(checks=("SUCCESS", "FAILURE"))])
    run("changes requested", [pr(decision="CHANGES_REQUESTED", reviews=[{"state": "CHANGES_REQUESTED", "id": "r1", "body": "fix x", "commit": {"oid": C}}])])
    run("pending checks", [pr(checks=("SUCCESS", "IN_PROGRESS"))])
    run("no pull request", [])
    run("merged", [pr(state="MERGED")])
    run("two open PRs (undecidable)", [pr(1), pr(2)])
    run("full page of 200 (undecidable)", [pr(i) for i in range(200)])
    run("not JSON (unparseable)", "oops")
    PY
    (cd $S/t0 && $V/bin/python $S/forge_demo.py)
    ```
    Expected, one line each: `green open PR` `state=open head=cccc
    decision=None checks=success`; `stale` `head=dddd` (a head other than the
    queried commit, which the gate treats as stale); `red checks`
    `checks=failure`; `changes requested` `decision=CHANGES_REQUESTED`;
    `pending checks` `checks=pending`; `no pull request` `state=none`; `merged`
    `state=merged`; the two open pull requests and the full page of 200
    `REFUSED ForgeUndecidableError`; `not JSON` `REFUSED ForgeUnparseableError`.
    Then the gate itself, with `gh` simulated by the tests' `run=` seam (the
    fixture's fake never touches GitHub), in the S4 installation:
    ```bash
    (cd $S/t0/scripts && $V/bin/python workflow_gate_policy_test.py TestForgeParser TestResolveGh \
        TestWorkflowQuery TestFunctionalEvidence TestReportedPullRequestFacts TestCauseTable \
        TestPositionRelativeToTheAnchor TestInvalidationTable TestQueryTrigger \
        TestEvaluateAcceptance TestSatisfyAcceptance TestHumanAcceptancePrApproved \
        TestAcceptanceCommandText 2>&1 | tail -4)
    ```
    Expected: `OK`, none failed. The behaviors, by test:
    `test_every_requirement_met_is_satisfiable` (acceptance needs
    `checkpoints_complete`, `technical_approval_current`,
    `functional_flows_passed`, `pr_fact_current`, `no_standing_pr_objection`,
    `ci_green`); `test_a_flow_recorded_at_other_protected_content_is_stale`;
    `test_i1_a_red_pull_request_behind_a_local_fix_blocks_and_stays_obtainable`
    and `test_a_green_fact_for_an_older_head_blocks_the_same_way` (stale);
    `test_a_standing_objection_at_the_current_head_is_not_obtainable` (red);
    `test_gh_unavailable_refuses_and_writes_nothing_whatever_is_stored` and
    `test_no_pull_request_fact_is_pending_the_query_and_never_satisfiable`
    (undecidable or absent: blocked, never passed);
    `test_a_stored_orchestrator_forge_fact_never_counts_whatever_its_content`
    and `test_a_fabricated_reported_fact_changes_nothing_the_fresh_query_decides`
    (an orchestrator-reported fact only tightens); `test_a_human_acceptance_is_never_satisfiable`.
F7. Reopening through `/apply-pr-review`, including from `MILESTONE_COMPLETE`.
    In the S4 installation:
    ```bash
    (cd $S/t0/scripts && $V/bin/python workflow_gate_policy_test.py -v TestReopenWorkItem \
        TestBeginPrReview TestStoreTimeReopen TestReopenCommitContracts \
        TestReopenCommandText 2>&1 | grep -E "ok$|FAIL|ERROR|^Ran|^OK")
    ```
    Expected: `OK`, none failed, including
    `test_a_reopen_from_milestone_complete_moves_the_phase_back` and
    `test_a_reopen_from_awaiting_functional_review_keeps_the_phase_and_the_approval`,
    `test_a_completed_item_runs_the_query_first_and_the_invocation_does_only_the_reopen`,
    `test_the_fresh_fact_decides_a_merged_closed_or_green_answer_stores_and_reopens_nothing`
    (a merged pull request is refused, a closed or green one reopens nothing),
    `test_the_same_fact_never_reopens_twice_at_awaiting_functional_review_and_a_new_fact_does`,
    and `test_findings_text_with_instructions_is_data_it_never_changes_the_decision`.
    The end-to-end reopening is in F4 (`TestAutomaticLifecycle` and
    `TestAllHumanLifecycle` reopen an item on a red fact).
F8. Protocol 1.1: `describe`, `next-action`, and a 1.0 consumer. Against the S4
    installation:
    ```bash
    P describe | $V/bin/python -c "import json,sys; d=json.load(sys.stdin); r=d['result']; \
        print(d['protocol'], r['protocol_version'], r['workflow_release'], r['supported_protocol_majors'], \
        r['supported_governing_versions'], r['capabilities']['external_result_kinds'], \
        r['capabilities']['reserved_result_kinds'], r['capabilities']['dispositions'])"
    P --protocol-major 2 describe; echo rc=$?
    P next-action | $V/bin/python -c "import json,sys; d=json.load(sys.stdin); r=d['result']; print(r['row'], r['action']['id'], r['disposition'])"
    ```
    Expected: protocol `{'name': 'workflow-orchestration', 'version': '1.1'}`,
    `protocol_version` `1.1`, `workflow_release` `2.8.0`, majors `[1]`, governing
    versions `['1', '2.1', '2.2']`, `external_result_kinds` `['functional_evidence',
    'implementation_review_verdict', 'plan_review_verdict', 'pr_review_result']`,
    `reserved_result_kinds` `[]`, `dispositions` including `validation`;
    the `--protocol-major 2` call prints an `ok: false` envelope with
    `unsupported_protocol` and `rc=3`; `next-action` prints `1 plan.start automatic`.
    Then the 1.0 consumer and the schema, in the S4 installation:
    ```bash
    (cd $S/t0/scripts && $V/bin/python workflow_protocol_test.py TestDescribe \
        TestProtocolSchemaAndDescribe TestUnawareConsumer TestEvidenceResultKinds \
        TestPlanAndTechnicalGateRows TestAcceptanceRows TestTriggerAndRemedyRuns \
        TestNewActionEdgesAndReconcile TestSpecificationTablesEqualTheCode 2>&1 | tail -4)
    ```
    Expected: `OK` (some skipped tests are fine, the equivalence ones need the
    tag and run in F9). `TestUnawareConsumer` shows a `1.0` consumer that does
    not know a new disposition or action id still works for every decision it
    understands, and stalls only at a `validation` decision (INV-8).
F9. All-human equals 2.7.0, in the disposable clone of S3 (it has the
    `v2.7.0` tag, so nothing is skipped; about 2.5 minutes):
    ```bash
    (cd $S/clone/payload/scripts && $V/bin/python workflow_protocol_test.py -v \
        TestAllHumanEquivalence TestUpdateSimulation27To28 TestUpdateSimulationLegacyDeclaration \
        TestUpdateSimulationInFlightDefault TestUnawareConsumer TestAutomaticLifecycle \
        TestMixedLifecycle TestAllHumanLifecycle 2>&1 | grep -E "skipped|FAIL|ERROR|^Ran|^OK")
    ```
    Expected: `Ran 33 tests`, `OK`, **no** `skipped` line. The equivalence
    tests prove that, with the human policy on, `next-action` is byte-equal to
    2.7.0's across every scenario and `describe` and `verify` differ only by the
    listed additions.
F10. The package: reproducible, verified, and the update from 2.7.0.
    ```bash
    $V/bin/python $R build --commit HEAD --out $S/build2
    diff $S/build/SHA256SUMS $S/build2/SHA256SUMS && echo REPRODUCIBLE
    $V/bin/python $R build --commit v2.7.0 --out $S/b270 | grep -E 'archive|manifest'
    mkdir $S/rel27 && tar -xzf $S/b270/workflow-2.7.0.tar.gz -C $S/rel27
    D=$S/t27; mkdir $D && git -C $D init -q \
        && git -C $D -c user.name=t -c user.email=t@t commit -q --allow-empty -m init
    $V/bin/workflow-manager --release-dir $S/rel27/workflow-2.7.0 bootstrap $D | head -2
    (cd $D && sha256sum docs/ai-workflow/WORKFLOW_STATE.json docs/ai-workflow/WORKFLOW_CONFIG.json) > $S/before.sum
    $V/bin/workflow-manager --release-dir $S/rel/workflow-2.8.0 update $D | head -2
    $V/bin/workflow-manager --release-dir $S/rel/workflow-2.8.0 verify $D
    (cd $D && sha256sum docs/ai-workflow/WORKFLOW_STATE.json docs/ai-workflow/WORKFLOW_CONFIG.json) | diff $S/before.sum - && echo STATE_AND_CONFIG_UNCHANGED
    test ! -e $D/docs/ai-workflow/GATE_POLICY.json && echo NO_POLICY_FILE_CREATED
    ```
    Expected: `REPRODUCIBLE`; the 2.7.0 build is `archive_sha256=c287323f...`,
    `manifest_sha256=f62fb261...` (W1's published bytes, still reproduced); the
    2.8.0 digests equal the preparation run's: `tar_sha256=c34a60f4...`,
    `archive_sha256=0dbd1b7d...`, `manifest_sha256=49005d4d...` (at commit
    `cae6577`; later evidence commits change only `docs/ACTIVE_MILESTONE.md`,
    which is not in the release source, so they do not move); `bootstrapped
    workflow 2.7.0 (full)`; `updated ... to workflow 2.8.0` (adds
    `GATE_POLICY.md`, `workflow_forge.py`, `workflow_gate_policy.py`, the
    `adopt-gate-policy`, `apply-pr-review` and `satisfy-gate` commands);
    `installation matches workflow 2.8.0`; `STATE_AND_CONFIG_UNCHANGED` and
    `NO_POLICY_FILE_CREATED` (the update changes no state file and writes no
    policy, so the default turns the gates automatic for the repository).
F11. Automated suites, as CI runs them (nine release-source suites plus the
    tooling tests), on the staged conformance fixture:
    ```bash
    $V/bin/python $R stage-conformance --commit HEAD --out $S/fx
    (cd $S/fx/scripts && for f in workflow_fingerprint workflow_state workflow_test_harness \
        workflow_integration workflow_acceptance_matrix workflow_state_completion_obligations \
        workflow_fingerprint_generalization workflow_protocol workflow_gate_policy; do
      echo "$f"; $V/bin/python ${f}_test.py 2>&1 | grep -E '^(Ran|OK|FAILED)'; done)
    $V/bin/python tools/release/release_test.py 2>&1 | tail -3
    ```
    Expected: every suite `OK`, none `FAILED`; `Ran` counts: fingerprint 257,
    state 1011, test harness 22, integration 275, acceptance matrix 291
    (`skipped=18`), completion obligations 106, fingerprint generalization 105,
    protocol 298 (`skipped=13`: the tag-dependent tests, which F9 runs), gate
    policy 284; `release_test.py` `Ran 80 tests`, `OK`. (The state and acceptance-matrix
    suites take several minutes; the staged fixture has no `v2.7.0` tag, hence
    the protocol skips.)
F12. Installation untouched and documents. In this checkout: `$V/bin/workflow-manager
    verify .` prints `installation matches workflow 2.6.0`, and `git status
    --short` is empty (after the evidence commit; the scratch work wrote nothing
    here). Read `payload/docs/ai-workflow/GATE_POLICY.md` against F1-F7 (the
    default, the toggles, the floor, the three single-family remedies, the
    residual table, the trust boundary), and skim the `Workflow 2.8.0` entry and
    the W2 row of `docs/ROADMAP.md`.
    Round 2 adds a docs check of `docs/ROADMAP.md` (the release source's
    documents are unchanged by it; this is the repository's own roadmap):
    ```bash
    grep -n "Workflow 2.8.0" docs/ROADMAP.md
    awk '/^## Workflow 2.8.0/,/^---$/' docs/ROADMAP.md
    awk '/^# 1.9 /,/^# 1.10 /' docs/ROADMAP.md | grep -n "2.8.0\|W2\|Controller\|gate policy\|human approval"
    grep -n "does not admit 2.8.0\|default policy equals\|behaviour is the 2.7.0" docs/ROADMAP.md
    ```
    Expected: the `Workflow 2.8.0` entry **and** section 1.9 (its W2 text,
    and the W2 row in the table) state the automatic default: human approval
    is **off** by default, so with no policy adopted the three gates are
    automatic on evidence, and a person restores the 2.7.0 gates by turning
    `human_approval` on (the master switch, or per gate). Neither may say the
    default policy equals the 2.7.0 gates, or that with no policy adopted
    behaviour is 2.7.0's. Neither may state `Controller 1.5.0 does not admit
    2.8.0` as the current state: the Controller 1.7.0, released with its C9,
    admits any Workflow whose `describe` answers protocol major 1 (a
    historical mention, dated and marked as past, is fine). The last `grep`
    printing a matching line in the 2.8.0 entry or in 1.9 is a finding to
    report with the line numbers (the `Workflow 2.7.0` entry's own
    statement about 1.5.0 is history and is not part of this check).
**Known limitations / out of scope**

- Nothing is published: no push, no pull request, no GitHub settings, no
  release. `gh` is never called; the forge is simulated by the parser and the
  tests' `run=` seam. The first real CI and `Release` run is the cutover.
- The Workflow Manager has no 2.8.0 pin; installation uses `--release-dir`.
  The Manager pin pull request is an owner action after publication.
- This repository's own installation stays 2.6.0; installing 2.8.0 here (which
  makes its gates automatic unless a `GATE_POLICY.json` with human approval is
  added first) is a later pull request. Controller releases that pin script
  hashes refuse 2.8.0 until they admit it; not exercised here.
- Automatic acceptance needs an open pull request first (`pr_fact_current`).
  A repository whose flow opens the pull request after acceptance keeps
  acceptance human (`GATE_POLICY.md`).
- With human acceptance and `requires_pr_approved` false, and at
  `MILESTONE_COMPLETE`, no Workflow query runs; only an orchestrator report
  arms one (the residual table in `GATE_POLICY.md`).
- `distinct_reviewer_models` families are declared, not verified.
- `/adopt-gate-policy` is user-only; F2 and F3 call its function in a
  disposable repository, never the slash command.

---

# Previous milestone record: W1 `orchestration-protocol-v1`

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

### Functional review checklist

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

### Current blockers

None.

### Active plan

None, because the milestone is complete. The plan document stays at
`docs/ai-workflow/ORCHESTRATION_PROTOCOL_V1_PLAN.md` (revision 13, plan
approval `CURRENT`) instead of being archived, as W0's did: the release
source (`payload/scripts/workflow_protocol.py`, `workflow_state.py`, the
test harness and suites) and the artifact registry cite it as the design
record.

### Functional review round 1

The orchestrator-run functional review (`FUNCTIONAL_REVIEW.md`, evidence
commit `ee86188`) passed S1-S3 and F1-F11 with one finding, F1: three
wording points in `docs/ROADMAP.md` (the W0 row's cutover steps, the W1 row's
premature COMPLETE, and the `v2.6.0-001` tense). Classified as documentation,
no code change; fixed in `docs/ROADMAP.md`, which both stages exclude, so
`technical_approval` stays CURRENT and no bundle is regenerated. Nothing was
deferred to a remediation child. Re-test: re-read the three ROADMAP lines.

### Next action

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
