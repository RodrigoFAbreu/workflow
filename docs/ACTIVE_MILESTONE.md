# Active Milestone

## Milestone

**Implemented and implementation-approved, awaiting functional review.** W21: `live-guard-visibility` (`process`, governing version `2.2`),
branch `milestone/live-guard-visibility`, roadmap row 24a (RodrigoFAbreu/workflow#91). Plan:
`docs/ai-workflow/LIVE_GUARD_VISIBILITY_PLAN.md` (revision 2, approved by gate policy). The goal is Workflow
2.18.6, a patch release (`fix:`): a live owner's guard is visible and not reclaimable, in both the claim guard
and the plan-approval journal guard. The previous milestone, W20 `takeover-fence`, is accepted (its record is
in git history and `docs/release-history.md`).

## Checkpoints

| id | name | state |
| --- | --- | --- |
| CP1 | A live holder's guard is visible and not reclaimable | **complete** |
| CP2 | Release 2.18.6 | **complete** |

## Verified state

- The holder of a guard keeps a non-blocking `flock` on the guard's inode for its window; the own-leftover
  reclaim of each guard refuses while another process holds it, and `guard_holder_is_running` answers whether
  a window is running. Release 2.18.6 bookkeeping is in `manifest.json`, `docs/release-history.md`,
  `docs/CONCURRENCY_INVARIANTS.md` and `tools/release/release_test.py`.
- Verified in a disposable clone (D-Staging): the nine suites, `check-manager-block`, `check_docs.py`, the
  `tools/docs` tests, `release.py build --commit HEAD`, and the `tools/release` tests in the zlib-ng
  environment; `workflow-manager verify .` is clean.
- Implementation review, revision 2 (`APPROVE`, `MANUAL_EXTERNAL_IMPLEMENTATION_REVIEW`): the nine staged suites
  pass (3,329 tests, 40 skipped), as do the `tools/release` (267) and `tools/docs` (34) tests.
- Re-run at `7795c34` for this checklist: `TestLiveGuardVisibility`, `TestSameWorktreeConcurrencyRealProcesses`
  and `TestLiveGuardVisibilityJournal` in a staged fixture, `Ran 14 tests`, `OK`.

## Functional review checklist

Scope: the live-owner guard behaviour of Workflow 2.18.6, tested on the release source's own staged fixture. This
is not the repository's installation, which stays at 2.18.5; test the fixture, not `scripts/`.

### Setup

Work only in a scratch directory. The product clone is read-only: it is cloned, never written to.

```bash
SCR=$(mktemp -d)
export HOME=$SCR/home TMPDIR=$SCR/tmp XDG_CONFIG_HOME=$SCR/xdg-config XDG_CACHE_HOME=$SCR/xdg-cache XDG_DATA_HOME=$SCR/xdg-data
mkdir -p "$HOME" "$TMPDIR" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"
git clone -q --no-hardlinks --branch milestone/live-guard-visibility /home/rodrigo/Workspace/workflow "$SCR/clone"
cd "$SCR/clone" && python3 tools/release/release.py stage-conformance --commit HEAD --out "$SCR/fixture"
```

Save the following as `$SCR/lgv_windows.py`. It is a two-window driver for the claim guard: `hold` is one
window, `enter` is another window of the same owner token.

```python
import subprocess
import sys
from pathlib import Path

import workflow_state as ws


def setup(root):
    root.mkdir(parents=True, exist_ok=True)
    git = ["git", "-C", str(root)]
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(git + ["config", "user.email", "test@example.com"], check=True)
    subprocess.run(git + ["config", "user.name", "Test"], check=True)
    (root / ".gitignore").write_text(".ai-review/\n")
    (root / "README.md").write_text("base\n")
    subprocess.run(git + ["add", "README.md", ".gitignore"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "base"], check=True)
    print(ws.claim_checkpoint(root, "wi", "CP", now="t1")["owner_token"])


def hold(root, token):
    lease = ws.acquire_guard(root, "wi", holder_owner_token=token, checkpoint_id="CP",
                             step="1f-commit", step_class=ws.DESTRUCTIVE, now="t-hold")
    print(f"window A open: lease {lease['lease_id']}, probe from A itself "
          f"{ws.guard_holder_is_running(root, 'wi')}", flush=True)
    input("press Enter to end window A ")
    ws.release_guard(root, "wi", lease)
    print("window A released", flush=True)


def enter(root, token):
    try:
        with ws.owner_mutation(root, "wi", token, checkpoint_id="CP", step="1d",
                               step_class=ws.DESTRUCTIVE, now="t2"):
            print("window B entered")
    except ws.CheckpointOwnershipUnavailableError as exc:
        print(f"window B refused: {exc}")
    print("probe:", ws.guard_holder_is_running(root, "wi"))


if __name__ == "__main__":
    command, repo = sys.argv[1], Path(sys.argv[2])
    if command == "setup":
        setup(repo)
    elif command == "hold":
        hold(repo, sys.argv[3])
    elif command == "enter":
        enter(repo, sys.argv[3])
    else:
        sys.exit(f"unknown command {command}")
```

Every command below runs with `export PYTHONPATH="$SCR/fixture/scripts"` set, from `$SCR`.

### Flows

**F1: automated live-guard suites (offline; no forge, claude, codex or ssh needed).**

```bash
cd "$SCR/fixture/scripts" && python3 -B -m unittest workflow_state_test.TestLiveGuardVisibility workflow_state_test.TestSameWorktreeConcurrencyRealProcesses workflow_integration_test.TestLiveGuardVisibilityJournal
```

- Expected: `Ran 14 tests`, `OK`. This covers the claim guard and journal guard refusals, the crash reclaim, the
  release path, the fork cases and descriptor hygiene.

**F2: a live owner's second window is refused (claim guard, `1f-commit`).**

```bash
python3 "$SCR/lgv_windows.py" setup "$SCR/repo-release"  # prints the owner token; call it T
T=<token printed above>
mkfifo "$SCR/fifo-a"
python3 "$SCR/lgv_windows.py" hold "$SCR/repo-release" "$T" < "$SCR/fifo-a" &   # window A
exec 3>"$SCR/fifo-a"            # keeps window A's stdin open
```

Wait until window A prints `window A open`, then run window B:

```bash
python3 "$SCR/lgv_windows.py" enter "$SCR/repo-release" "$T"                  # window B
```

- Expected in B: `window B refused`, naming the lease shown in A, step `1f-commit`, "still running", and a
  `fuser <guard path>` hint. The body does not run. `probe: True`.
- Then end window A: `echo >&3; exec 3>&-`. A prints `window A released`. Run B again: it enters, and
  `probe: False`.

**F3: a crashed owner's leftover is reclaimed (claim guard).**

```bash
T=$(python3 "$SCR/lgv_windows.py" setup "$SCR/repo-crash")
mkfifo "$SCR/fifo-crash"
python3 "$SCR/lgv_windows.py" hold "$SCR/repo-crash" "$T" < "$SCR/fifo-crash" & A_PID=$!
exec 4>"$SCR/fifo-crash"
```

Wait until window A prints `window A open`, then:

```bash
python3 "$SCR/lgv_windows.py" enter "$SCR/repo-crash" "$T"   # refused while A lives
kill -9 $A_PID; wait $A_PID 2>/dev/null; exec 4>&-
python3 "$SCR/lgv_windows.py" enter "$SCR/repo-crash" "$T"   # entered; no further step
```

- Expected: the first `enter` is refused. After the kill, the second `enter` enters without any other step, and
  `probe: False`.

**F4: the journal guard and the fork cases.** Covered by F1 (`TestLiveGuardVisibilityJournal` and the fork and
descriptor cases of `TestLiveGuardVisibility`). Nothing further to run by hand.

### Not testable in this sandbox

These need a forge, a real `claude` or `codex`, or the zlib-ng environment. The operator performs them outside the
sandbox:

- `/accept-milestone`, the merge, and the `Release` workflow that publishes 2.18.6.
- `workflow-manager update` from 2.18.6 back to 2.18.5 (the downgrade posture in the plan's D-Patch).
- `release.py build --commit HEAD` (needs the pinned zlib-ng environment).

### Known limitations and out of scope

- Two threads of one process are not told apart: a same-token acquisition from a second thread still reclaims the
  first thread's guard. This is the known gap stated in the plan.
- A guard published by a release before 2.18.6 keeps no lock. `guard_holder_is_running` answers `False` for it, and
  it is reclaimable as before.
- A 2.18.5 acquirer ignores a 2.18.6 holder's lock, so mixed installs get no protection from it.
- `guard_holder_is_running` has no CLI and no caller yet. The checkpoint-start release (#55) is a later milestone.
- The journal (plan-approval) guard has no public probe; its reclaim uses the private helper.
- The refusal text reads `'wi''s mutation guard`. That comes from the existing `{work_item_id!r}'s` pattern of the
  neighbouring refusals, which this milestone did not change. It is cosmetic.
- No new command, state field, phase, ledger, trailer or refusal class was added.

## Next action

Functional review: run the checklist above, and put any findings in
`.ai-review/live-guard-visibility/feedback/FUNCTIONAL_REVIEW.md`. Once testing is clean, `/accept-milestone`; then
merge, let the `Release` workflow publish Workflow 2.18.6, and plan roadmap row 24 (W19, `/milestone-plan`).
