# Releasing the Workflow

This repository publishes one product: the Workflow, as immutable GitHub
releases `vV` of `RodrigoFAbreu/workflow`, each with three assets:
`workflow-V.tar.gz`, `workflow-V.manifest.json` and `SHA256SUMS`.
`workflow-manager` installs a release only once it pins it (see "After a
release: the `workflow-manager` pin" below). The design record is
`docs/ai-workflow/WORKFLOW_REPOSITORY_SETUP_PLAN.md` (W0), section 3.

The repository root holds two copies of the Workflow (`CLAUDE.md`):

- **the release source**, `manifest.json`, `payload/`, `fixtures/` and
  `templates/`: what a release ships. Every build, check and conformance run
  reads it from `git archive <commit> manifest.json payload fixtures
  templates`, never from the working tree;
- **this repository's own installation**, `.claude/`, `scripts/`,
  `docs/ai-workflow/`, `.workflow-manager/`, the managed blocks of
  `CLAUDE.md` and `.gitignore`, and `.github/workflows/workflow-conformance.yml`:
  the published Workflow that runs this repository's own milestones. It
  changes only through `workflow-manager update` (see "The installation
  check" below).

The release tooling is `tools/release/` (`release.py`, `package.py`,
`manager_block.py`, their tests, two pins and the committed Manager release
list), and the workflows are `.github/workflows/ci.yml` (`CI`), which calls
`tests.yml` (`Tests`) and `build-and-publish.yml` (`Build and publish`), and
`pr-title.yml` (`PR title`); see "GitHub Actions layout" below. The `D-W0-*` names below
are that plan's design decisions.

## How a release happens

The version is a property of the released bytes: `manifest.json`'s
`workflow_version` is inside the package and its digests, and
`workflow-manager` installs and reports by it. So the version is set **by
hand in the release source**, and the tag follows it. Nothing rewrites the
manifest at build time.

1. A pull request changes the release source **and** bumps
   `workflow_version` in `manifest.json`, in the same pull request. The bump
   must be exactly the next patch, minor or major of the base's version
   (`2.6.0` → `2.6.1`, `2.7.0` or `3.0.0`); anything else (`2.6.0` → `2.8.0`,
   `2.6.0` → `2.7.1`, a decrease, a malformed version) is refused.
2. Its title is a Conventional Commit whose impact equals that version change
   (below). It is merged into `main` by squash; the title becomes the squash
   commit's subject, with a blank body.
3. `main`'s `CI` push run checks the merged commit again (its `tests`
   job).
4. When those tests pass (the run's `aggregate`), the same run's
   `build-and-publish` job runs `Build and publish`. If `main` has meanwhile
   moved on to a newer commit, it defers to that commit's own run. Otherwise
   it checks out the validated commit, `main`'s tip, reads its first-parent
   history and every tag and release, and decides (`release.py next-release`):
   - `main`'s manifest names `V` and `vV` is **published**: there is nothing
     to release, once `vV` reads back intact (below);
   - `vV` is **not published**: `V` is pending. `Build and publish` builds the
     package from the **introducing commit** `C_V` (the oldest first-parent commit
     whose manifest names `V` and whose parent's does not), verifies it with
     the pinned Workflow Manager, publishes `vV` at `C_V` and reads it back.

**Published** means a non-draft GitHub release `vV` exists *and* the tag `vV`
exists. A tag alone, or a draft with or without its tag, is not a
publication: it is the residue of a failed publication (see "Recovering from
a failed publication"), and `V` stays pending. A published release whose tag
is missing refuses.

A version change is always measured between a commit and its first parent:
on a pull request, the merge ref against its base branch tip (`HEAD^1`); on a
`main` push, the squash commit against the previous `main` tip. Tags play no
part in it.

### Titles

Pull-request titles are Conventional Commits, `type(optional-scope)!:
description`, with the Workflow Manager's grammar and impact table:

| impact | types |
| --- | --- |
| **major** | any type with `!` (`feat!:`, `fix(payload)!:`) |
| **minor** | `feat` |
| **patch** | `fix`, `perf`, `refactor`, `build`, `revert` |
| **none** | `docs`, `chore`, `ci`, `test`, `style` |

The required `Conventional Commit title` check also requires **agreement**:
the title's impact must equal the level of the pull request's version change
from its base's manifest (`none` when the version is unchanged). A `feat:`
pull request that does not bump the minor version fails; a `ci:` pull request
that bumps the version fails.

Impact titles are therefore reserved for release-source changes. Repository
tooling, CI and documentation are always `ci:`, `chore:`, `docs:` or `test:`,
including a fix to `build-and-publish.yml` or `tools/release/` while a release is
pending. The squash subjects on `main` are a truthful changelog of the
release source. Check a title locally, on a commit whose first parent is the
base:

```bash
python3 tools/release/release.py check-title "feat: orchestration protocol v1"
python3 tools/release/release.py check-title "feat: orchestration protocol v1" --agree
```

### Keeping the branch up to date

`main` requires a pull request to be up to date with it before merging
(`strict`, below). The version, the title agreement and the release-source
rules are decided **before** merge, on the merge ref the checks last ran
against, and `PR title` does not re-run when `main` moves. Without `strict`,
two pull requests that each bump `2.6.0` → `2.7.0` with different payload
changes would merge in turn on stale green checks. When a pull request's base
has moved, update it before merging, which re-runs every check:

```bash
gh pr update-branch <number>
```

(or "Update branch" on the pull request). GitHub auto-merge does not update
the branch itself.

## GitHub Actions layout

Three repository-owned workflows, plus `PR title` and the managed
`workflow-conformance.yml`:

| file | name | role |
| --- | --- | --- |
| `ci.yml` | `CI` | the entry point: every pull request, `main` push and `workflow_dispatch` (with the input `dry-run`). Its jobs are `tests` (calls `tests.yml`), `aggregate` (the required check) and `build-and-publish` (calls `build-and-publish.yml`, only on `main` for a push or a dispatch, after `aggregate`) |
| `tests.yml` | `Tests` | tests and checks only: every check of the release source and of the installation ("What CI checks" below). Reusable (`workflow_call`) and runnable by itself (`workflow_dispatch`, which runs everything and reports no required check) |
| `build-and-publish.yml` | `Build and publish` | building and publishing only: the release gate and the release job ("The release job" below). Reusable and runnable by itself on `main` (`workflow_dispatch`), both with the inputs `validated` (set only by `ci.yml`) and `dry-run` |
| `pr-title.yml` | `PR title` | the required `Conventional Commit title` check |
| `workflow-conformance.yml` | `Workflow conformance` | the installation's suites, the required `workflow-conformance` check. Managed by the Workflow release: never edited here |

`aggregate` is a job of `ci.yml` itself, with no `name:`, because a job called
through `uses:` reports as `<caller job> / <called job>` (`tests / checks`):
only a job of the calling workflow reports under the bare name the ruleset
requires. It always runs and fails unless the `tests` job succeeded, so a
failed, skipped or cancelled test run fails it. The aggregation proper stays
in `tests.yml`'s `verdict` job, which fails that workflow, and with it
`aggregate`. No ruleset context names a called job, so the prefix (`tests /`,
`build-and-publish /`) is free to change.

A revision is validated once: `build-and-publish` runs in the same `CI` run,
only after its `aggregate` succeeded, and only on `main`, for a push or a
dispatch of `CI` (`validated: true`); a pull request never publishes. A
dispatch of `CI` on `main` is therefore the re-run path from the entry point:
it runs the same tests on `main`'s tip and then publishes it, and its
`dry-run` input verifies the whole publish path without creating a release. A
called workflow cannot exceed its caller job's permissions, so
`build-and-publish` is the one job that grants `contents: write` (and
`actions: read`); everything else reads only.
Only `ci.yml` sets the workflow-level concurrency: a pull request's run is
cancelled by its next push, and every other run is per event and commit and
never cancelled (a called workflow with its caller's group would deadlock).
Publications are serialized by the release job's own group.

One `CI` run starts at most four jobs at once, within the six runners per
repository allowed: `tests`' `checks`, `docs-tests`, `release-source-conformance`
and `update-fixture` (the last two wait for `changes`); `verdict`, `aggregate`
and the two `build-and-publish` jobs each wait for the previous one. No job has
a matrix; the conformance suites' shards are processes inside their job.
`release_test.py` computes this from the `needs:` graph and fails above six.

Shared workflows from `RodrigoFAbreu/action-workflows` are used only where their
semantics are exactly this repository's:

- `python-tests.yml` runs `tools/docs/`'s tests (`tests.yml`'s `docs-tests`
  job: Python 3.12, `test-directory: tools/docs`, `test-pattern: "*_test.py"`,
  which is `python -m unittest discover -s tools/docs -p '*_test.py'` in a fresh
  checkout; they need nothing else).
- `python-tests.yml` is not used for the rest: `tools/release/`'s tests need the
  pinned zlib-ng runtime, full history and tags, and the conformance suites run
  sharded in a staged fixture with a coverage gate.
- The shared `pr-title.yml` is not used: `pr-title.yml` runs this repository's
  own `release.py check-title --agree`, which also requires the title's impact
  to agree with the manifest's version change; `pr-check.yml` wraps that shared
  check and is a `pull_request` workflow, not a reusable one.
- The shared `validate.yml` (actionlint of that repository's own workflows) is
  not reusable, and the Java, JavaScript, npm, GitOps and image workflows do
  not apply.

Run them by hand:

```bash
gh workflow run tests.yml --ref <branch>                          # every check, nothing published
gh workflow run ci.yml --ref main -f dry-run=true                  # the tests, then every publish gate and the build, no release created
gh workflow run ci.yml --ref main                                  # the tests, then the publication (the re-run path, below)
gh workflow run build-and-publish.yml --ref main -f dry-run=true   # every gate and the build, no release created
gh workflow run build-and-publish.yml --ref main                   # the publication alone, for a tip a CI push run validated
```

## What CI checks

`CI` runs on every pull request, every `main` push and on
`workflow_dispatch`; its `tests` job runs `Tests`, under Python 3.12 on
`ubuntu-latest`. Its jobs:

| job | checks |
| --- | --- |
| `changes` | seconds long: `release.py release-source-changed` over `HEAD^1..HEAD` (on a pull request's merge ref, the base tip and the merge) answers whether the change touches `manifest.json`, `payload/`, `fixtures/`, `templates/`, `tools/release/`, `.github/workflows/ci.yml`, `tests.yml`, `build-and-publish.yml` or the root `.gitattributes` (`git archive` reads its `export-ignore` and `export-subst` lines, so it changes what is staged from the release source). A `push` to `main` and `workflow_dispatch` always answer yes (in a called workflow the event is the caller's), and so does a decision that cannot be computed (no parent, a git error) |
| `checks` | one checkout and one install of the pinned tools, then each check as its own named step: `workflow-manager verify .` with the pinned Manager; `release.py build --commit HEAD`, the Manager's `package verify` of the archive, a `--release-dir` bootstrap and verify of a scratch repository, and the three assets uploaded as the `package` artifact; `release.py check-pending` and `check-immutable` against the saved release list (and, when the manifest version is published, `check-immutable --published` against the downloaded `vV` assets); `tools/docs/`'s checker; and `tools/release/release_test.py`, including the byte-for-byte reproduction of every published release (`v2.3.1` to `v2.6.0`) in the pinned deflate runtime; and, for a release after 2.12.0, the Manager block checks ("The Manager metadata block" below) |
| `docs-tests` | `tools/docs/`'s tests, through the shared `python-tests.yml` ("GitHub Actions layout" above) |
| `release-source-conformance` | only when `changes` says yes: `release.py stage-conformance --commit HEAD`, then the release source's own nine frozen suites in that fixture, the acceptance-matrix suite in 4 shards, all under one limit |
| `update-fixture` | only when `changes` says yes: for a release that carries a Manager block, the pre-publish update fixture ("The Manager metadata block" below) builds the updated repository (previous published release, updated to HEAD with the pinned Manager), then runs the same nine frozen suites there with the same scheduler as `release-source-conformance` (the same step text, pinned equal by `release_test.py`), then the Manager's `verify` of it |
| `verdict` | fails unless `changes`, `checks` and `docs-tests` succeeded and each of `release-source-conformance` and `update-fixture` succeeded, or was skipped because `changes` succeeded and said the release source and its CI are unchanged (any other skip fails it, with an `::error` naming the job and its result). It fails `Tests`, and so `CI`'s required `aggregate` |

A pull request that touches none of those paths (documentation, the roadmap, an
installation of the Workflow in this repository) therefore skips the two jobs
that run the candidate's suites, and `aggregate` still passes; `checks` always
runs in full. The skip is the only weakening: a pull request that does touch
one of them runs both jobs exactly as a `main` push does.

In `checks`, a failed step does not hide an unrelated one: each later step
runs unless the run was cancelled or a step it depends on (the deflate
runtime, the Manager, the build, the release list) did not succeed, and no
step uses `continue-on-error`. The failing step is named in the log, and the
job fails.

`release-source-conformance` schedules the suites the way the installed
`workflow-conformance` job does (the managed template, Workflow 2.16.0), over
the staged fixture; the installed `scripts/` are never used. The
acceptance-matrix suite (the longest, 453 tests) is split into `shards = 4`
groups of whole test classes, balanced by test count, by a small stdlib-only
tool the step writes next to the scheduler; its text is the template's, byte
for byte, and `tools/release/release_test.py` pins them equal. The four
shards and the eight other suites form one queue, longest first in a fixed order
taken from measured durations (the `longest` list in the step), run
`min(width_cap, nproc)` at a time with `width_cap = 4`, each unit in its own
complete copy of the staged fixture with its own `TMPDIR` and `HOME`
(the copy is part of the measured time). Every unit runs to its end, all
results are collected before the step decides, and a unit that did not record
a result counts as failed. A coverage gate then requires every acceptance test
id to be recorded exactly once, with none failed, missing, unexpected or
started and never finished; a planning failure fails the job, and there is no
fall-back to the unsharded suite (`shards = 0` is only the kit's control
setting). A passing unit's log is a collapsed group; a failing unit gets an
`::error` annotation naming the shard, its classes and the failing test ids,
followed by its full log, so a shard failure shows under `acceptance N/4`
rather than under the suite file. The step summary has one row per suite
(the acceptance row reads `passed (4 shards, 453 tests)`) followed by one row
per shard, and the logs, results, shard files, the plan and the coverage
check are uploaded as the `source-conformance-logs` artifact whether the job
passed or failed (the `update-fixture` job's, which runs the same step, is
`update-fixture-logs`). No required check or ruleset changes.

`PR title` runs `release.py check-title "$TITLE" --agree` on every pull
request (`opened`, `edited`, `reopened`, `synchronize`). The installed
`workflow-conformance` job runs the installation's suites.

The required checks on `main` are unchanged: `aggregate`, `Conventional Commit
title` and `workflow-conformance`. Adding a job to `Tests` means adding it to
`verdict`'s `needs` and its result list, never to the ruleset.

### A published version never changes

When `main`'s (or a pull request's) manifest version `V` is published, the
`checks` job's immutability steps requires both:

1. the release source unchanged since the tag: `git diff --quiet v<V> HEAD --
   manifest.json payload fixtures templates`;
2. the package rebuilt from HEAD, in the pinned deflate runtime, equal to the
   published assets of `vV` byte-for-byte: exactly the three asset names (a
   missing or extra asset refuses, naming it), `SHA256SUMS` and both digests.
   On a mismatch it also compares the decompressed tar streams and reports
   which differs, so a release-source change and a deflate-runtime drift are
   told apart; either fails.

A pull request can therefore change the release source only together with a
bump to an unpublished version.

### A pending version is frozen until published

Let `P` be the base's (`HEAD^1`) manifest version. `check-pending` requires:

- if `P` is published, a release-source change only together with a valid
  version change;
- if `P` is **not** published (pending, including after a failed publication
  that left a draft or a tag), **no** release-source change at all between
  `HEAD^1` and `HEAD`, not even a further bump: `vP` must be published first.

Changes outside the release source (`tools/`, `.github/`, `docs/`) are always
allowed. The check runs on the pull request and again on the `main` push, and
a red push run never releases. So every commit on `main`'s first-parent
history from `C_P` to the tip carries byte-identical release source, which is
what makes the release target deterministic.

## The release job

`Build and publish` (`.github/workflows/build-and-publish.yml`) runs as the
`build-and-publish` job of every `CI` **push or dispatch run on `main` whose
`aggregate` succeeded** (`workflow_call`, with `validated: true`), and on its
own `workflow_dispatch` on `main`. It has two jobs, and only ever runs on
`refs/heads/main`.

The `gate` job checks out nothing and runs none of this repository's code. It
reads `main`'s current tip through the API and passes it on only once that
tip was validated. Called by `CI` (a push, or a dispatch of `ci.yml`, which
`github.event.workflow` names), the validation is that same run's
`aggregate`, which covers only its own commit: the tip is passed on only when
it is that commit. A run whose commit `main` has moved past ends there with a
notice, and the tip's own `CI` run, once its `aggregate` succeeds, publishes
it. Dispatched directly, nothing in its own run validated anything, so
`validated` stays false (a direct dispatch that sets it fails at once) and the
tip is passed on only when the API lists a `CI` push run for that exact sha
whose `aggregate` job succeeded; a dispatch on a tip without one fails.
(`aggregate`, not the whole run: a run whose own `build-and-publish` failed
still validated its commit, and the dispatch is what re-runs that
publication.) `build-and-publish.yml` executes the
release tooling of the commit it checks out, so a newer tooling-only commit
whose validation is red or still running is never executed.

The `dry-run` input (default false, on every way in; `CI` passes its own
dispatch input) runs every gate, the build, the Manager's verification and, for
a published version, the read-back, but skips `gh release create` with a
notice, and so the read-back of a pending version it did not create:

```bash
gh workflow run ci.yml --ref main -f dry-run=true                  # after the tests
gh workflow run build-and-publish.yml --ref main -f dry-run=true   # alone
```

The `release` job runs only with the gate's sha. Runs are serialized by one
concurrency group, `workflow-release`, and never cancelled. It checks out
that exact sha (never the moving `main`) with full history and tags, installs
the pinned deflate wheel, saves the release list with its `contents: write`
token (which sees drafts), and runs:

```bash
python3 tools/release/release.py next-release --trigger <sha> --releases releases.json
```

which prints `state`, `version` and `target`, or refuses, naming what it
found. The target is always the introducing commit `C_V`, never the
triggering commit; `next-release` refuses unless the trigger is on `main`'s
first-parent history and its release source equals `C_V`'s, `V` is greater
than the highest published version, that version's tag is an ancestor of
`C_V`, and the version `C_V`'s parent names is published (no version is ever
skipped, even if a red push run was merged). Two competing runs resolve the same `V`, `C_V` and bytes; the second
finds `V` published. Then:

- `release.py build --commit <C_V>` (refusing unless it builds version `V`);
- `state=pending`: the pinned Manager's `package verify`, and a
  `--release-dir` bootstrap and verify of a scratch repository; then

  ```bash
  gh release create "v$V" --target "$C_V" --title "Workflow $V" \
    --notes "Workflow release $V." --latest \
    "workflow-$V.tar.gz" "workflow-$V.manifest.json" SHA256SUMS
  ```

- both states: the **read-back**. It fetches the tag, saves the release list
  again, runs `gh release download v<V>`, then `release.py check-published
  --version V --target <C_V> --releases … --assets … --downloaded …`: `vV`
  published, not a draft, exactly the three assets, each byte-equal to the
  one built from `C_V`, and the tag `vV` at `C_V`. On `state=published` a
  pass ends the job green with "nothing to release (vV read back intact)".

The job never uses `--clobber`, `gh release upload`, `gh release delete`,
`git tag` or `git push`, and never changes the manifest: it never repairs a
failed publication or supersedes a version itself. Those are the owner's
procedures below.

### When nothing is released

- `main`'s manifest names a published version `V` and `vV` reads back
  intact: the job ends green with "nothing to release (vV read back
  intact)". This is every merge that does not bump the version.
- A pull request's `CI` run, a `CI` run (push or dispatch) whose `aggregate`
  failed or was cancelled, or a dispatch of `CI` or of `Build and publish` on
  any branch other than `main`: the job does not run.
- A `CI` push or dispatch run whose commit `main` has moved past: the `gate` job ends
  green with a notice and nothing else runs; the tip's own run decides.
- A direct dispatch of `Build and publish` whose `main` tip has no `CI` push
  run with a successful `aggregate`, or that sets `validated` itself: the
  `gate` job fails before anything is checked out.
- A dry run: nothing is created; for a pending version the job ends with
  "dry run: vV would be published at C_V; the release is not created".

`next-release` never answers an empty "nothing": a draft or a tag without a
published release refuses, and a published release that does not read back
fails the run, so neither is ever mistaken for "nothing to release".

### When something goes wrong

- **Red `main`: fix forward.** A red push run releases nothing. Fix it in a
  pull request: a tooling or CI fix is `ci:` (or `test:`/`docs:`), and is
  allowed while a version is pending; a release-source fix needs its own
  version bump once the pending version is published.
- **A failed `Build and publish` before `gh release create`** leaves nothing
  (the `CI` run that called it is red in its `build-and-publish` job only):
  re-run it (`workflow_dispatch` of `CI` or of `Build and publish`, below), or
  re-run the failed jobs of that `CI` run.
  If the failure was the tooling's, fix it first in a `ci:` pull request; its
  merge's push run validates it and publishes again.
- **A failed run inside or after `gh release create`**: see the next two
  sections. `next-release` names which one applies.

Re-run the publication through `workflow_dispatch` on `main` (a dry run
first, if in doubt): from the entry point, `CI`, which tests the tip again and
then publishes it, or `Build and publish` alone, which needs the tip's green
`CI` push run:

```bash
gh workflow run ci.yml --ref main -f dry-run=true
gh workflow run ci.yml --ref main
gh run list --workflow ci.yml --branch main --event workflow_dispatch --limit 5
gh workflow run build-and-publish.yml --ref main -f dry-run=true
gh workflow run build-and-publish.yml --ref main
gh run list --workflow build-and-publish.yml --limit 5
```

`gh run list --workflow build-and-publish.yml` lists its direct dispatches; a
publication called by `CI` is the `build-and-publish` job of that `CI` run
(`gh run list --workflow ci.yml --branch main --event push`, or
`--event workflow_dispatch`).

## Recovering from a failed publication

`gh release create` with assets is not one operation: it creates a draft,
uploads each asset, then publishes, and release immutability applies only
once published. A run that fails part-way can leave a draft `vV`, with some
assets, with or without the tag `vV`. Neither is a publication, so `V` stays
pending and the release source stays frozen. `next-release` refuses on that
residue, naming each part it found and this section. Recovery is the
owner's:

1. inspect both: `gh release view v<V> --json isDraft,tagName,assets` and
   `git ls-remote --tags origin refs/tags/v<V>`;
2. if a **published** release `vV` exists, it is never deleted, edited or
   re-uploaded: follow the supersession procedure below instead;
3. otherwise remove the residue, choosing by what step 1 found:
   - a draft (with or without its tag): `gh release delete v<V> --yes
     --cleanup-tag`, then, if `git ls-remote` still finds the tag, `git push
     origin --delete refs/tags/v<V>`;
   - a tag with no release at all (`gh release view` reports "release not
     found"): skip `gh release delete`, which would fail on the missing
     release before reaching the tag, and run only `git push origin
     --delete refs/tags/v<V>`;

   then confirm both commands in step 1 now find nothing. Deleting a tag
   that never belonged to a published release does not breach release
   immutability (which covers published releases only) or this
   repository's rule against moving a published tag;
4. re-run the publication through `workflow_dispatch` (of `CI` or of
   `Build and publish`); it resolves the same `V`
   and `C_V` (D-W0-Target) and publishes.

Never touch a published release. Recovery never needs a release-source
change: if the failure came from `build-and-publish.yml` or `tools/release/`, fix it in
a `ci:` pull request, which the pending-version freeze allows, then re-run.

W0's CP3 rehearsed this procedure live, for a draft with its tag, in a
throwaway repository (`docs/ai-workflow/requirements/workflow-repository-setup-ledger.md`,
`CP3`).

## Superseding an incomplete published release

A publication can complete while its read-back fails: a missing, extra or
differing asset, or the tag `vV` somewhere other than `C_V`. A published
release cannot be repaired, so it is never deleted, edited or re-uploaded.
Every later `Build and publish` run and every `checks` run's immutability steps then stay red, naming
`vV` and what differs, until `V` is superseded:

1. leave `vV` and its tag exactly as they are, and **never add a
   `workflow-manager` pin for `V`**: the Manager installs only pinned
   versions, so an incomplete `V` never reaches a user;
2. if the failure came from the tooling (a builder, workflow or `gh`
   defect), fix it; the fix may ride in the bump pull request below;
3. open a pull request bumping the manifest to the next patch version
   `V'` with no other release-source change, titled `fix: supersede
   incomplete release V` (patch impact, D-W0-Title). It passes CI:
   `HEAD^1`'s `V` is published, so the bump is allowed (D-W0-Pending), and
   `V'` is unpublished, so D-W0-Immutable does not apply;
4. once merged, `Build and publish` publishes `V'` normally (`V'` is greater than the
   highest published version `V`, whose tag is an ancestor of `C_V'`), and
   reads it back;
5. record `V` as superseded by `V'` in `docs/RELEASING.md`'s "Superseded
   releases" table, with the read-back failure, in a `docs:` pull request,
   and add the `workflow-manager` pin for `V'` only.

`vV` stays visible as a published GitHub release; the table and the absent
pin are what tell operators not to use it. W0's CP3 rehearsed this procedure
live in a throwaway repository.

### Superseded releases

| version | superseded by | read-back failure | date |
| --- | --- | --- | --- |

## Verification commands

The exact forms that verify this repository, each with what it checks and when it
matters. Run them from the repository root; `$TMPDIR` is a scratch directory.

**The nine payload suites**, from a staged fixture (the release source's own
conformance fixture, which is what CI runs):

```bash
python3 tools/release/release.py stage-conformance --commit HEAD --out "$TMPDIR/fixture"
suites=$(python3 -c "import json; print(*json.load(open('manifest.json'))['manager']['conformance']['suites'], sep='\n')") && test -n "$suites" && ( cd "$TMPDIR/fixture/scripts" && while read -r suite; do python3 -B "$TMPDIR/fixture/scripts/$suite" </dev/null || exit 1; done <<< "$suites" )
```

The fixture commands run in a subshell, so the working directory stays the repository root:
every block below runs, in order, from the repository root.

Run the suites from inside the fixture, as CI does: some of them read the repository
around the working directory (`git rev-parse --show-toplevel`), and from this
repository's root they would read its installed commands instead of the staged ones
and fail on any difference between the two.

The loop runs each of the nine suites the manifest's `manager.conformance.suites`
lists, one name per line, and runs under bash and zsh alike (an unquoted
parameter expansion in a `for` loop splits only under bash). `</dev/null` keeps a suite from
consuming the remaining names, and `test -n "$suites"` fails an empty list instead of
passing a loop that ran zero times. Never run `payload/scripts/*_test.py`: it also picks up the opt-in historical
demo suites, which are not part of conformance. `stage-conformance`
verifies the tree against the manifest, so a checkpoint that changed a shipped file
before the release checkpoint (which is where the manifest records move) cannot stage
from its own tree: stage from a scratch clone with the changed records' `sha256` and
`size` adjusted, and say so in the report.

**The `tools/release` and `tools/docs` tests.** The `tools/release` tests need the
pinned zlib-ng runtime (see "Building locally" below): run them with that
environment's Python, never the system one.

```bash
python -m unittest discover -s tools/release -p '*_test.py'
python3 -m unittest discover -s tools/docs -p '*_test.py'
python3 tools/docs/check_docs.py
```

A bare `python3 -m unittest discover tools/release` (or `tools/docs`) runs
zero tests, because the files are named `*_test.py`, not `test*.py`: pass `-s` and
`-p`, or name the file.

**The Manager metadata block**, against the committed list of Manager releases
(`--manager-releases` is required; without it the command is a usage error):

```bash
python3 tools/release/release.py check-manager-block --commit HEAD --manager-releases tools/release/manager-releases.json
```

**The installation**, which must match the Workflow release this repository records:

```bash
workflow-manager verify .
```

Offline it needs the installed release's assets in the release cache
(`--release-cache`, or `$WORKFLOW_MANAGER_RELEASE_CACHE`); with an empty cache and no
reachable release source it exits 1 with `error: cannot fetch <source>/<version>/SHA256SUMS`
and a `next:` line naming `--release-source`, rather than passing.

## Building locally: the pinned compression runtime

The package format fixes the tar stream and the gzip framing, but the
archive's deflate bytes depend on the deflate implementation. Every published
archive was deflated by zlib-ng; a Python linked against stock zlib
reproduces none of them. So the builder writes the gzip header and trailer
itself around raw deflate from the `zlib_ng` module, pinned by version and
sha256 in `tools/release/deflate-requirements.txt` (`zlib-ng` 1.0.0, the
cp312 manylinux x86_64 wheel, bundling zlib-ng 2.2.5). `build` refuses unless
`zlib_ng` imports and reports zlib-ng `2.2.5`; there is no fallback to
`zlib`, and the reproduction tests fail, not skip, without it.

Build and test locally with Python 3.12 on Linux x86_64, as CI does:

```bash
python3.12 -m venv .venv-release
. .venv-release/bin/activate
python -m pip install --only-binary=:all: --require-hashes -r tools/release/deflate-requirements.txt
python tools/release/release_test.py
python tools/release/release.py build --commit HEAD --out "$(mktemp -d)"
```

`build` stages the release source from the commit, verifies it, refuses
when the release ships `scripts/workflow_protocol.py` (2.7.0 and later) and
its `WORKFLOW_RELEASE` literal differs from the manifest's `workflow_version`
(the release-constant guard: bump both together), builds it twice and
requires identical bytes, checks the round trip, and prints the
evidence: `version`, `files`, `zlib_ng`, `tar_sha256`, `archive_sha256` and
`manifest_sha256`. At `v2.6.0`'s release source it prints the published
digests (`archive_sha256=dc86a796…`, `manifest_sha256=d92517a2…`). The tar
stream and manifest digests are independent of the deflate runtime, so when
only `archive_sha256` differs, the runtime drifted, not the source.

The other commands `Tests` and `Build and publish` run work locally the same way, against a
saved release list:

```bash
gh release list --json tagName,isDraft --limit 1000 > /tmp/releases.json
python tools/release/release.py check-pending --releases /tmp/releases.json
python tools/release/release.py check-immutable --releases /tmp/releases.json
python tools/release/release.py next-release --trigger HEAD --releases /tmp/releases.json
python tools/release/release.py stage-conformance --commit HEAD --out "$(mktemp -d)/fixture"
```

A token without write access does not see drafts, so locally a draft is
invisible to `next-release`; `Build and publish`'s `release` job saves the list with its write
token.

## The installation check

This repository's installation must stay exactly the published Workflow
release it records. The installation step of the `checks` job installs the pinned Workflow
Manager and runs `workflow-manager verify .` on every pull request and `main`
push, under the required `aggregate`. A pull request that edits an installed
command, a managed block or any other managed file fails it, whatever else it
changes. Run it locally with the same Manager:

```bash
workflow-manager verify .     # installation matches workflow <version>
```

The installation changes only through `workflow-manager update`, in its own
pull request. The pinned Manager must know the target release, so that pull
request bumps `tools/release/manager-pin.json` first or together.

### Bumping the Manager pin

`tools/release/manager-pin.json` names the Workflow Manager release CI and
`Build and publish` install (`version`, `wheel`, `sha256`). The Manager only has to
verify packages, bootstrap and verify a repository, and know the release this
repository's installation records; bump it when an installation update needs
a newer Manager, in a `ci:` pull request:

```bash
M=X.Y.Z    # the Manager release
d=$(mktemp -d)
gh release download "v$M" --repo RodrigoFAbreu/workflow-manager --dir "$d"
(cd "$d" && sha256sum -c --strict SHA256SUMS)
sha256sum "$d/workflow_manager-$M-py3-none-any.whl"
```

Set `version` to `M`, `wheel` to `workflow_manager-M-py3-none-any.whl` and
`sha256` to the wheel's digest. The `checks` job's package and installation steps
download the wheel from that release and check it with `sha256sum -c` before
installing it.

## The Manager metadata block

A release after 2.12.0 carries an optional-by-contract, required-by-this-repository
`manager` block in its `manifest.json`: what the Workflow Manager used to hard-code
per release (the minimum Manager, the downgrade posture and its signals, the
notes for new work, a gate default change, the frozen suites' counts and the
portability exceptions). The Manager's `docs/release-metadata.md` is the contract
(schema version 1). A manifest at 2.12.0 or older never has one.

The block is written in `manifest.json` itself, not in a separate file copied in by
the build: the committed manifest is what CI checks and what is published, so one
file has one author step.

| field | who sets it |
| --- | --- |
| `schema_version`, `min_manager_version`, `downgrade_boundary`, `new_work_only`, `gate_default_change`, `conformance.portability_exceptions` | **authored** by hand in the milestone's pull request |
| `conformance.suites` | **computed**, never written by hand |

`conformance.suites` is the number of test cases each of the nine suites the managed
conformance workflow names loads (`unittest`'s own loader, in the staged
conformance fixture; a `*_demo_test.py` file the workflow does not name is not
counted; a loader error refuses). Print it, or write it, with:

```bash
python tools/release/release.py manager-block --commit HEAD            # print
python tools/release/release.py manager-block --release-dir DIR --write  # record
```

`--commit` stages a commit, so its manifest digests must already match its bytes.
`--release-dir DIR` measures a directory staged from the working tree whose digests
are already refreshed, so a release can record its own counts before its commit
exists. `--write` replaces only the value of `suites` in the working tree's
`manifest.json`, keeping every other byte, and refuses a manifest at 2.12.0 or
older or one with no block to fill.

`Tests` runs `release.py check-manager-block --commit HEAD
--manager-releases tools/release/manager-releases.json`, which refuses when:

- (a) the block is not valid under the contract (schema 1, key types, the closed
  detector vocabulary, kebab-case signal names, version strings, `suites` a
  mapping of file names to non-negative integers);
- (b) `suites` differs from the measurement;
- (c) `min_manager_version` is newer than the newest published Manager release in
  `tools/release/manager-releases.json`: the saved output of `gh release list -R
  RodrigoFAbreu/workflow-manager --json tagName,isDraft,isPrerelease,publishedAt`
  (complete records, plus the date taken). Only an exact `vX.Y.Z` tag that is
  neither a draft nor a prerelease counts; a record missing a field makes the
  evidence invalid. The check is offline: it reads only the committed file;
- (e) the manifest is at 2.12.0 or older and has a block, or is newer and has none;
- (g) `tools/release/manager-pin.json` pins a Manager other than the block's
  `min_manager_version`.

Refresh the evidence with `release.py record-manager-releases --out
tools/release/manager-releases.json` after a Manager release is published. A
separate step, `release.py compare-manager-releases`, lists the live releases and
reports `consistent`, `snapshot-behind` (a warning) or `unavailable` (a notice);
none of them fails the job. Check (c) is therefore red until the Manager release a
Workflow release needs is published and recorded, which is the intended order.

The pre-publish **update fixture** (`release.py update-fixture --release-dir
DIR --previous-assets DIR --previous-version V --keep OUT`, in the
`update-fixture` job) bootstraps a scratch repository from the previous
published release (the highest non-draft, non-prerelease release below HEAD's
version) and runs `workflow-manager update` with the pinned Manager (held equal
to the minimum by check (g)) against the candidate. With `--keep OUT` it stops
there and leaves the updated repository in `OUT`, after checking that the suites
the updated repository's conformance workflow names are exactly the ones the
scheduler step in `tests.yml` runs (it refuses, naming both lists, when
they differ: a release that changes its suites changes the scheduler step with
it); the job then runs the candidate's nine frozen suites in it, scheduled exactly as in
`release-source-conformance` (the acceptance-matrix suite in 4 shards, the
coverage gate, one `::error` and one log per failed unit, the step summary
table), and then `workflow-manager --release-dir <candidate> verify OUT`, which
also runs when a suite failed. Without `--keep` the command does all of it
itself, the suites in four threads and then `verify`, and is the form to run
locally. A release without a block, or one with no earlier published release,
has nothing to update-test: the job concludes success with that message and
skips the suites and the verify.

Not checked: that a release which adds a persisted key, phase or status states a
downgrade posture. That is a judgment no tool can make here.

## After a release: the `workflow-manager` pin

A published release reaches users only once `workflow-manager` pins it. After
`Build and publish` publishes `vV`, open the small `workflow-manager` pull request that
adds its pin, following that repository's `docs/RELEASING.md`, "Workflow
packages: adding a pin"
(https://github.com/RodrigoFAbreu/workflow-manager/blob/main/docs/RELEASING.md).
Never pin a superseded version.

## Repository settings, as reviewed data

The merge settings and the `main` ruleset live in `.github/repository/` and
are applied by the repository owner with `gh api`, never by CI or an agent:

- `merge-settings.json`: squash merges only, the squash commit's subject is
  the pull request's title (`PR_TITLE`) and its body is blank (`BLANK`),
  auto-merge on, branches deleted on merge;
- `ruleset-main.json`: the ruleset `main` on the default branch, with no
  bypass actors: no deletion, no force push, linear history, pull requests
  merged by squash, and the required checks `aggregate`, `Conventional Commit
  title` and `workflow-conformance` with `strict_required_status_checks_policy:
  true`.

They are `workflow-manager`'s files with two deliberate differences: the
third required check, `workflow-conformance`, the installed suites that guard
the installation running this repository's own milestones; and `strict` on,
because this repository decides the version and the release-source rules
before merge (see "Keeping the branch up to date"). `workflow-manager`
derives its version after merge and leaves `strict` off.

Apply them:

```bash
repo=RodrigoFAbreu/workflow
gh api -X PATCH "repos/$repo" --input .github/repository/merge-settings.json
gh api -X POST "repos/$repo/rulesets" --input .github/repository/ruleset-main.json
```

To change the ruleset later, edit the file in a pull request, then replace
it:

```bash
id="$(gh api "repos/$repo/rulesets" --jq '.[] | select(.name == "main") | .id')"
gh api -X PUT "repos/$repo/rulesets/$id" --input .github/repository/ruleset-main.json
```

Read them back:

```bash
id="$(gh api "repos/$repo/rulesets" --jq '.[] | select(.name == "main") | .id')"
gh api "repos/$repo" --jq '{allow_squash_merge, allow_merge_commit,
  allow_rebase_merge, squash_merge_commit_title, squash_merge_commit_message,
  allow_auto_merge, delete_branch_on_merge}'
gh api "repos/$repo/rulesets/$id"
```

Never make a check required before it has reported under that exact name on
an open pull request: a required check that never reports blocks every merge.
There are no bypass actors, so an administrator recovers from a lockout by
editing or disabling the ruleset. Release immutability stays on in the
repository's settings.

## Cutover: W0, CI, releases and `main` protection

These steps run after W0's implementation is technically approved and its
functional review is done, before acceptance
(`docs/ai-workflow/WORKFLOW_REPOSITORY_SETUP_PLAN.md`, section 7). Each is the
repository owner's action, or one the owner explicitly authorizes; an agent
states the commands and reads results back. Record each step's evidence in
`docs/ACTIVE_MILESTONE.md`. A problem found here goes back through
`/apply-functional-review`.

This section is W0's record, kept as it ran: its `Workflow CI`
(`workflow-ci.yml`) and `Release` (`release.yml`) are now `CI` (`ci.yml`,
calling `tests.yml`) and `Build and publish` (`build-and-publish.yml`, called
by `CI`'s `build-and-publish` job), described in "GitHub Actions layout"
above. Today's equivalent of step 6's commands is `gh run list --workflow
ci.yml --branch main --event push --limit 1` and that run's
`build-and-publish` job's log.

1. Push the branch and open the pull request (impact `none`: the manifest
   stays at 2.6.0):

   ```bash
   git push -u origin milestone/workflow-repository-setup
   gh pr create --base main --head milestone/workflow-repository-setup \
     --title "ci: CI, releases and main protection for the workflow repository" \
     --body "Milestone workflow-repository-setup (W0)."
   ```

2. On the pull request's final head, confirm that `aggregate`, `Conventional
   Commit title` and `workflow-conformance` all reported green under exactly
   those names:

   ```bash
   gh pr checks <number> --json name,state
   ```

   and, in the `Workflow CI` run's logs, that the `checks` job's `release_test.py` step reproduced
   all five archive digests, that its immutability steps compared against
   the downloaded `v2.6.0` assets ("the rebuilt package equals the published
   assets of v2.6.0"), and that its installation step ran `workflow-manager
   verify .` ("installation matches workflow 2.6.0").
3. Apply `merge-settings.json`, then create the ruleset, and read both back
   (see "Repository settings, as reviewed data").
4. **Installation-integrity proof.** Open a draft pull request from a
   throwaway branch based on the cutover branch whose only change is one line
   appended to `.claude/commands/accept-milestone.md`:

   ```bash
   git switch -c w0-installation-probe milestone/workflow-repository-setup
   echo "probe" >> .claude/commands/accept-milestone.md
   git commit -am "test: installation integrity probe"
   git push -u origin w0-installation-probe
   gh pr create --draft --base main --head w0-installation-probe \
     --title "test: installation integrity probe" --body "W0 cutover step 4; closed unmerged."
   ```

   Confirm the installation step fails naming that file (`modified:
   .claude/commands/accept-milestone.md`) and the required `aggregate` check
   fails. That failing required check is the evidence that the pull request
   is blocked: a draft's `mergeStateStatus` reads `DRAFT` whatever its
   checks say, so it cannot show *why* merging is blocked on its own.

   ```bash
   gh pr checks <probe-number> --json name,state
   gh pr view <probe-number> --json mergeStateStatus
   ```

   Then close it and delete the branch:

   ```bash
   gh pr close <probe-number> --delete-branch
   git switch milestone/workflow-repository-setup
   git branch -D w0-installation-probe
   ```

5. After `/accept-milestone`, squash-merge the cutover pull request (update
   the branch first if `main` moved).
6. Confirm `main`'s `Workflow CI` push run is green and that the `Release`
   run it triggers ends green with "nothing to release (v2.6.0 read back
   intact)", having downloaded and read back `v2.6.0`; and that no new
   release or tag exists:

   ```bash
   gh run list --workflow workflow-ci.yml --branch main --event push --limit 1
   gh run list --workflow release.yml --limit 1
   gh run view <release-run-id> --log | grep "nothing to release"
   gh release list
   git ls-remote --tags origin
   ```

   `gh release list` must still show `v2.6.0` as latest.
