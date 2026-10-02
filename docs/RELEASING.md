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

The release tooling is `tools/release/` (`release.py`, `package.py`, their
tests and two pins), and the workflows are `.github/workflows/workflow-ci.yml`
(`Workflow CI`), `pr-title.yml` (`PR title`) and `release.yml` (`Release`).
The `D-W0-*` names below are that plan's design decisions.

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
3. `main`'s `Workflow CI` push run checks the merged commit again.
4. When that run completes green, `Release` starts (`workflow_run`). If
   `main` has meanwhile moved on to a commit whose own push run has not
   succeeded, it defers to that commit's run. Otherwise it checks out `main`'s
   tip, reads its first-parent history and every tag and release, and decides
   (`release.py next-release`):
   - `main`'s manifest names `V` and `vV` is **published**: there is nothing
     to release, once `vV` reads back intact (below);
   - `vV` is **not published**: `V` is pending. `Release` builds the package
     from the **introducing commit** `C_V` (the oldest first-parent commit
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
including a fix to `release.yml` or `tools/release/` while a release is
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

## What CI checks

`Workflow CI` runs on every pull request, every `main` push and on
`workflow_dispatch`, under Python 3.12 on `ubuntu-latest`. Its jobs:

| job | checks |
| --- | --- |
| `tooling` | `tools/release/release_test.py`, including the byte-for-byte reproduction of every published release (`v2.3.1` to `v2.6.0`) in the pinned deflate runtime |
| `package` | `release.py build --commit HEAD`; the pinned Workflow Manager's `package verify` of the archive; `--release-dir` bootstrap and verify of a scratch repository; uploads the three assets as the `package` artifact |
| `immutability` | `release.py check-pending` and `check-immutable` against the saved release list; when the manifest version is published, `check-immutable --published` against the downloaded `vV` assets |
| `installation` | `workflow-manager verify .` with the pinned Manager |
| `release-source-conformance` | `release.py stage-conformance --commit HEAD`, then the release source's own eight frozen suites in that fixture |
| `aggregate` | fails unless every job above succeeded |

`PR title` runs `release.py check-title "$TITLE" --agree` on every pull
request (`opened`, `edited`, `reopened`, `synchronize`). The installed
`workflow-conformance` job runs the installation's suites.

The required checks on `main` are `aggregate`, `Conventional Commit title` and
`workflow-conformance`. Adding a job to `Workflow CI` means adding it to
`aggregate`'s `needs` and its result list, never to the ruleset.

### A published version never changes

When `main`'s (or a pull request's) manifest version `V` is published, the
`immutability` job requires both:

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

`Release` (`.github/workflows/release.yml`) runs after every **successful
`Workflow CI` push run on `main`** (`workflow_run`), and on
`workflow_dispatch` on `main`, the re-run path. It has two jobs.

The `gate` job checks out nothing and runs none of this repository's code. It
reads `main`'s current tip through the API and passes it on only once that
tip has a successful `Workflow CI` push run: the triggering run itself when
the tip is the triggering commit, otherwise one the API lists for the tip's
sha. A green run only covers its own commit, and `release.yml` executes the
release tooling of the commit it checks out, so a newer tooling-only commit
whose push run is red or still running is never executed. A `workflow_run`
whose commit `main` has moved past, with no green run for the tip yet, ends
there with a notice: the tip's own push run, once green, starts `Release`
again. A dispatch on a tip without one fails.

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
- A pull request's `Workflow CI` run, a failed or cancelled `main` push run,
  or a dispatch on any branch other than `main`: the job does not run.
- A `workflow_run` whose commit `main` has moved past, while the new tip has
  no successful `Workflow CI` push run: the `gate` job ends green with a
  notice and nothing else runs; the tip's own run decides.
- A dispatch whose `main` tip has no successful `Workflow CI` push run: the
  `gate` job fails before anything is checked out.

`next-release` never answers an empty "nothing": a draft or a tag without a
published release refuses, and a published release that does not read back
fails the run, so neither is ever mistaken for "nothing to release".

### When something goes wrong

- **Red `main`: fix forward.** A red push run releases nothing. Fix it in a
  pull request: a tooling or CI fix is `ci:` (or `test:`/`docs:`), and is
  allowed while a version is pending; a release-source fix needs its own
  version bump once the pending version is published.
- **A failed `Release` run before `gh release create`** leaves nothing:
  re-run it (`workflow_dispatch`, below). If the failure was the tooling's,
  fix it first in a `ci:` pull request; its merge's green push run starts
  `Release` again.
- **A failed run inside or after `gh release create`**: see the next two
  sections. `next-release` names which one applies.

Re-run `Release` through `workflow_dispatch` on `main`:

```bash
gh workflow run release.yml --ref main
gh run list --workflow release.yml --limit 5
```

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
4. re-run `Release` through `workflow_dispatch`; it resolves the same `V`
   and `C_V` (D-W0-Target) and publishes.

Never touch a published release. Recovery never needs a release-source
change: if the failure came from `release.yml` or `tools/release/`, fix it in
a `ci:` pull request, which the pending-version freeze allows, then re-run.

W0's CP3 rehearsed this procedure live, for a draft with its tag, in a
throwaway repository (`docs/ai-workflow/requirements/workflow-repository-setup-ledger.md`,
`CP3`).

## Superseding an incomplete published release

A publication can complete while its read-back fails: a missing, extra or
differing asset, or the tag `vV` somewhere other than `C_V`. A published
release cannot be repaired, so it is never deleted, edited or re-uploaded.
Every later `Release` run and every `immutability` job then stays red, naming
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
4. once merged, `Release` publishes `V'` normally (`V'` is greater than the
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

The other commands CI and `Release` run work locally the same way, against a
saved release list:

```bash
gh release list --json tagName,isDraft --limit 1000 > /tmp/releases.json
python tools/release/release.py check-pending --releases /tmp/releases.json
python tools/release/release.py check-immutable --releases /tmp/releases.json
python tools/release/release.py next-release --trigger HEAD --releases /tmp/releases.json
python tools/release/release.py stage-conformance --commit HEAD --out "$(mktemp -d)"
```

A token without write access does not see drafts, so locally a draft is
invisible to `next-release`; the `Release` job saves the list with its write
token.

## The installation check

This repository's installation must stay exactly the published Workflow
release it records. The `installation` job installs the pinned Workflow
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
`Release` install (`version`, `wheel`, `sha256`). The Manager only has to
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
`sha256` to the wheel's digest. The `package` and `installation` jobs
download the wheel from that release and check it with `sha256sum -c` before
installing it.

## After a release: the `workflow-manager` pin

A published release reaches users only once `workflow-manager` pins it. After
`Release` publishes `vV`, open the small `workflow-manager` pull request that
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

   and, in the `Workflow CI` run's logs, that the `tooling` job reproduced
   all five archive digests, that the `immutability` job compared against
   the downloaded `v2.6.0` assets ("the rebuilt package equals the published
   assets of v2.6.0"), and that the `installation` job ran `workflow-manager
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

   Confirm the `installation` job fails naming that file (`modified:
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
