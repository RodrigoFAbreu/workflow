# W0: Set up the `workflow` repository for development (Revision 6)

- **Work item:** `workflow-repository-setup` (`process`, governing version `2.2`)
- **Roadmap step:** W0 (`docs/ROADMAP.md`, "At a glance")
- **Branch:** `milestone/workflow-repository-setup`
- **Base commit:** `bf51137` (Workflow 2.6.0 installed, #2)
- **Plan revision:** 6 (revision 1 → 2: local plan review round 1; 2 → 3:
  manual external plan review round 1; 3 → 4: manual external plan review
  round 2; 4 → 5: plan amendment 0, after CP1; 5 → 6: plan amendment 0,
  checkpoint anchors; section 11)

## 1. Goal

Make this repository able to develop and publish Workflow releases on its own,
so that W1 (Workflow 2.7) is the first release built here rather than in
`workflow-manager`. After W0:

1. every pull request and every `main` push runs CI over the **release source**
   (not only over this repository's installed 2.6.0 copy);
2. a merge to `main` whose manifest names a new, unpublished version publishes
   exactly one immutable GitHub release `vV` with its three assets, from a
   deterministic commit and a pinned compression runtime, and any other merge
   publishes nothing; while that version is pending, the release source
   cannot change, and a failed publication is recoverable;
3. `main` is protected: squash-only, Conventional-Commit pull-request titles,
   required checks, no bypass; a required check verifies this repository's
   installation (`workflow-manager verify .`), so the separation between the
   two copies is enforced, not only stated;
4. the release model is written down (`docs/RELEASING.md`, `README.md`,
   `CLAUDE.md`).

W0 releases nothing. The release source stays byte-identical to `v2.6.0`.

### Already done (not in scope)

The roadmap's W0 row also names `CLAUDE.md`, this repository's own Workflow
installation kept apart from the release source, and this roadmap. Those
landed in #1 and #2. W0 only updates `CLAUDE.md`'s repository-owned text where
the new CI and protection make it stale ("Until W0 lands, `main` has no
required checks").

### Non-goals

- Any change to the release source (`manifest.json`, `payload/`, `fixtures/`,
  `templates/`). That is W1's work.
- Any change to this repository's installation (`.claude/`, `scripts/`,
  `docs/ai-workflow/` Workflow documents, `.workflow-manager/`, the managed
  blocks of `CLAUDE.md`/`.gitignore`, `.github/workflows/workflow-conformance.yml`).
  `workflow-manager verify .` must stay clean throughout; from CP2 on, CI
  enforces it (D-W0-Installation).
- Moving a tag, replacing an asset, or re-publishing any of `v2.3.1`-`v2.6.0`.
- A `workflow-manager` pull request. W0 publishes no release, so there is no
  pin to add. `docs/RELEASING.md` documents the pin follow-up for W1.
- A nightly run, badges, or release notes beyond a fixed sentence.

## 2. What exists today (facts this plan relies on)

- **Two trees at the repository root.** Since #2 the root holds both the
  release source (`manifest.json`, `payload/`, `fixtures/`, `templates/`) and
  the installation. A release directory must contain only what its manifest
  lists: the Workflow Manager's `build_package` run on the root refuses with
  "untracked file in release" for every installation file and `README.md`.
- **The staged release source reproduces every published package.** Checked
  while planning: for each tag `v2.3.1`, `v2.4.0`, `v2.5.0`, `v2.5.1`, `v2.6.0`,
  `git archive v<V> manifest.json payload fixtures templates`, extracted and
  built with the Manager's `package.build_package`, gives an archive and
  manifest asset whose sha256 equal `workflow-manager`'s pins
  (`src/workflow_manager/published_releases.json`). HEAD's staged release
  source reproduces 2.6.0 (`dc86a796…`, manifest `d92517a2…`). That check
  ran under Python 3.14 linked against zlib-ng's zlib-compatible library
  (`zlib.ZLIB_RUNTIME_VERSION` `1.3.1.zlib-ng`).
- **The archive digest depends on the deflate implementation; the tar
  stream does not.** Re-checked for revision 3: the same five builds under
  Python 3.12 with stock zlib 1.3.2 give five *different* archive digests
  (2.6.0: `af28b52b…`), while the uncompressed tar streams and the manifest
  assets are byte-identical in both runtimes. Every published archive was
  deflated by zlib-ng. Writing the same gzip framing with raw deflate from
  the PyPI `zlib-ng` 1.0.0 wheel (`cp312` manylinux x86_64, sha256
  `5332f945…`, bundled zlib-ng 2.2.5) under Python 3.12 reproduces all five
  published archive digests; so does the system zlib-ng 2.3.3.
- **The package format** (`D-Package-Format`, owned today by
  `workflow-manager`'s `src/workflow_manager/package.py`): a gzip tar with one
  top directory `workflow-V/`, members taken from the manifest (not a
  directory walk), sorted, `mtime=0`, owner `0:0`, mode `0755`/`0644`, PAX
  only where USTAR cannot hold a path, gzip `mtime=0`, no file name, level 9;
  plus a byte copy of `manifest.json` as `workflow-V.manifest.json`, and
  `SHA256SUMS` sorted by name.
- **The conformance fixture** (`workflow-manager`'s `fixture.build_conformance_repo`):
  a fresh Git repository holding the `full`-profile payload, the
  `host-evidence` fixtures, the state templates and the `.gitignore`
  fragment, committed once. The frozen suites run green in it.
- **The installed CI** (`.github/workflows/workflow-conformance.yml`, job
  `workflow-conformance`) runs the *installation's* seven suites from
  `scripts/`. It is managed, so it is not edited here, and it tests 2.6.0's
  installed copy, not the release source a W1 pull request changes.
- **Releases** were published by hand (`workflow-manager` `RELEASING.md` K2)
  as `gh release create v<V> --verify-tag --title "Workflow <V>" --notes
  "Workflow release <V>."` with the three assets. Release immutability is on.
  `gh release create` with assets is not one operation: it makes separate
  API calls to create a draft, upload each asset and publish, and
  immutability applies only once published — a draft, and the tag associated
  with it, can still be modified or deleted (`gh release create --help`).
  `gh release delete <tag>` leaves the tag unless `--cleanup-tag` is given.
- **Nothing in CI verifies the installation.** The installed
  `workflow-conformance` job runs the installed suites only. In a scratch
  worktree of HEAD, `workflow-manager verify .` exits 0; with one line
  appended to `.claude/commands/accept-milestone.md` it exits 1 (`modified:
  .claude/commands/accept-milestone.md`), while that change would leave every
  check revision 2 proposed green.
- **`workflow-manager` already has the shapes to follow**: `pr-title.yml`
  (job `Conventional Commit title`), `.github/repository/merge-settings.json`
  and `ruleset-main.json` applied by the owner with `gh api`, and a
  `workflow_run`-triggered `release.yml`.

## 3. Design decisions

### D-W0-Version: the manifest is the version authority

A Workflow release's version is a property of its bytes: `manifest.json`'s
`workflow_version` is inside the package, and `workflow-manager` installs and
reports by it. So, unlike the Manager (whose version is derived from tags and
commit subjects), the Workflow's version is set **by hand in the release
source**, in the same pull request that changes the release source, and the
tag follows it:

- `main`'s manifest names `V` and `V` is published → nothing to release,
  once the published release is read back intact (D-W0-Target). The release
  source must then be **unchanged** since `vV` (D-W0-Immutable).
- `main`'s manifest names `V` and `V` is not published → `V` is **pending**:
  release `V` (D-W0-Target). `V` must be strictly greater than the highest
  published version, and that version's tag must be an ancestor of the
  released commit. While `V` is pending the release source is frozen
  (D-W0-Pending).

**Published** means a non-draft GitHub release `vV` exists *and* the tag
`vV` exists. A tag alone, or a draft with or without its tag, is **not** a
publication: it is the residue of a failed publication (D-W0-Recovery), and
the version stays pending. A published release whose tag is missing from
the fetched tags is inconsistent and refuses. The tools never call the
GitHub API themselves: they read the release list (`gh release list --json
tagName,isDraft --limit 1000`, saved by the workflow) as an input file next
to the local Git tags, so every case is testable on scratch repositories.
A `contents: read` token does not see drafts; the release job's `contents:
write` token does.

A **version change** is always measured between a commit and its first
parent: on a pull request, the merge ref against its base (`HEAD^1`, the base
branch tip the checks ran against); on a `main` push, the squash commit
against the previous `main` tip (`HEAD^1`, linear history). Tags play no part
in it. A version change must be **exactly** the next patch, minor or major of
the parent's version (`2.6.0` → `2.6.1`, `2.7.0` or `3.0.0`); anything else
(`2.6.0` → `2.8.0`, `2.6.0` → `2.7.1`, a decrease, a malformed version) is
refused.

This is `OD-W0-1` below; it is the recommendation, not a silent choice.

### D-W0-Title: titles agree with the version change

Pull-request titles are Conventional Commits, with the Manager's grammar and
impact table (`feat` minor, `fix`/`perf`/`refactor`/`build`/`revert` patch,
`!` major, `docs`/`chore`/`ci`/`test`/`style` none). Because the manifest
already decides the version, the title check also **checks agreement**: it
compares the pull request's manifest `workflow_version` with its **base's**
(D-W0-Version: `HEAD^1` of the merge ref, never the highest tag) and requires
the title's impact to equal that version change's level (`none` when the
version is unchanged). A `feat:` pull request that does not bump the minor
version fails; a `ci:` pull request that edits `payload/` without a bump
passes the title check but fails D-W0-Pending/D-W0-Immutable, and with a bump
fails the title check. Because the baseline is the base's manifest, a pull
request that does not touch the version is `none`-impact whether or not a
release is pending, so a fix to `release.yml` or `tools/release/` while `V`
is pending is titled `ci:`, not `feat:`. Impact titles are therefore reserved
for release-source changes; repository tooling, CI and documentation are
always `ci:`/`chore:`/`docs:`/`test:`. This keeps the squash subjects on
`main` a truthful changelog of the release source. (`OD-W0-1` covers the
alternative.)

### D-W0-Immutable: a published version's release source never changes

For a manifest version `V` that is already published, CI requires both:

1. **offline:** `git diff --quiet v<V> HEAD -- manifest.json payload fixtures templates`;
2. **online:** the package rebuilt from HEAD's staged release source, in
   the pinned compression runtime (D-W0-Deflate), equals the published
   assets of `v<V>` byte-for-byte (`gh release download`, then require
   exactly the three asset names — a missing or extra asset refuses, naming
   it — and compare `SHA256SUMS` and both digests). On a mismatch it also compares the
   decompressed tar streams and reports which differs, so a release-source
   change and a compression-runtime drift are told apart in the failure
   message; either fails the check.

A pull request can therefore change the release source only together with a
version bump to an unpublished version, which is exactly what W1 does.

### D-W0-Pending: a pending version's release source is frozen until published

D-W0-Immutable protects a published version; this protects the window between a
bump to `V` merging and `vV` being published (minutes normally, indefinitely
after a failed `Release` run). Let `P` be the parent's (`HEAD^1`) manifest
version:

- if `P` is published, a release-source change is allowed only together
  with a valid version change (D-W0-Version), and D-W0-Immutable applies to
  an unchanged version;
- if `P` is not published (`P` is pending, including after a failed
  publication that left a draft or a tag), **any** release-source change
  between `HEAD^1` and `HEAD` is refused, including a further bump: `vP` must
  be published first. Recovery from a failed release therefore never needs a
  release-source change: re-run `Release`, or fix `release.yml`/
  `tools/release/` in a `ci:` pull request, which this rule allows.

Every commit on `main`'s first-parent history from the one that introduced
`P` to the tip therefore carries byte-identical release source, which is what
makes D-W0-Target deterministic. The check runs on the pull request (against
its base) and again on the `main` push (against the previous tip), so a
violation that slipped past a stale pull-request check still turns `main`'s
CI red, and a red push run never releases (D-W0-Target).

### D-W0-Target: the release is published from a defined commit

The release job does not publish whichever triggering `head_sha` it was
handed. It resolves, on `main`'s first-parent history: the tip's manifest
version `V`; if `V` is published, it reads `vV` back (below) and, only if
that passes, there is nothing to release; if a draft `vV` or a
tag `vV` exists without a published release, it refuses, naming what it
found and the recovery (D-W0-Recovery) — never "nothing to release", which
would strand `V`; otherwise the **introducing commit** `C_V`, the oldest first-parent commit whose manifest names `V` and
whose parent's does not. It refuses unless the release source at the
triggering commit equals the one at `C_V` (`git diff --quiet`; D-W0-Pending
guarantees it) and the triggering commit's `Workflow CI` push run succeeded.
It builds from `C_V` and creates `vV` with `--target C_V`. Two competing runs
therefore resolve the same `V`, the same `C_V` and the same bytes; the job's
concurrency group serializes them, and the second finds `V` published and
publishes nothing. After `gh release create` the job reads the release back
(not a draft, three assets whose digests equal the built ones, tag `vV` at
`C_V`) and fails loudly otherwise. Because a published release cannot be
repaired, a failed read-back must not turn into "nothing to release" on the
next run: whenever `V` is already published, the job repeats the same
read-back — it builds from `C_V`, downloads `vV` and runs `check-published`
— and a published release with a missing, extra or differing asset, or its
tag elsewhere than `C_V`, fails the run, naming what differs and the
supersession recovery (D-W0-Recovery). Every later `Release` run, and every
pull request's and `main` push's `immutability` job (D-W0-Immutable), stays
red until `V` is superseded. Unlike the Manager's `resolve-target` (newest green commit), the
tag lands on the reviewed bump commit itself, so `vV` points at the commit
whose pull request reviewed `V`.

### D-W0-Stage: build only from the staged release source

Every build, conformance run and verification reads the release source from
`git archive <commit> manifest.json payload fixtures templates`, extracted into
a scratch directory — never from the working tree (which has the installation,
`README.md`, `__pycache__/` and `.ai-review/` around it).

### D-W0-Builder: this repository owns its builder; the Manager verifies it

The producer owns the package format it publishes, so this repository carries
a builder in `tools/release/` — the build half of the Manager's
`package.py` (and the part of `Release.verify()` it needs), ported, not
imported. It is stdlib-only except for the deflate step (D-W0-Deflate).
Drift between producer and consumer is caught, not trusted away:

- the builder's tests reproduce all five published releases from their tags
  byte-for-byte, in the pinned compression runtime (their tar-stream,
  archive and manifest digests are test constants: published bytes never
  change);
- CI and the release job run the **Workflow Manager's own** `package verify`
  on the built archive, and `bootstrap --release-dir` + `verify` on a scratch
  repository, with a pinned Manager release (`OD-W0-2`).

### D-W0-Deflate: the compression runtime is pinned, not ambient

The package format fixes the tar stream and the gzip framing, but the
deflate bytes are whatever the linked deflate implementation emits, and
the five published archives were deflated by zlib-ng (section 2). CI's
`actions/setup-python` Python links stock zlib, which reproduces none of
them. So the builder does not use `gzip.GzipFile`: it writes the same
10-byte gzip header `GzipFile(filename="", mtime=0, compresslevel=9)`
writes (`1f8b 08 00 00000000 02 ff`, checked byte-equal in section 2's
experiment), raw deflate from `zlib_ng.zlib_ng.compressobj(9, DEFLATED,
-15, 8, 0)`, and the CRC-32/size trailer. The `zlib-ng` wheel is pinned by
version and sha256 in `tools/release/deflate-requirements.txt`, installed
with `pip install --require-hashes`, wherever a package is built: the
`tooling`, `package` and `immutability` jobs, the release job, and a
developer's local run.

`build` refuses unless `zlib_ng` imports and reports the pinned zlib-ng
version (`2.2.5`); there is no silent fallback to `zlib`. The reproduction
tests fail (they do not skip) without it. Tar-stream and manifest digests
are asserted separately from the archive digest, so a failure says whether
the source or the deflate changed. If the pinned wheel ever gave different
bytes on a CI runner than locally (for example through CPU-specific code
paths), the archive tests fail on that runner, closed, before any required
check depends on them (CP2). This is `OD-W0-6`.

### D-W0-Recovery: a failed publication is detected and recoverable

Two failures are distinguished: **residue** (a draft or a tag, never
published), which is deleted and the same `V` published again, and an
**incomplete published release** (published, but its read-back fails),
which is immutable and is superseded by a new version.

`gh release create` with assets is a draft, uploads and a publish (section
2), so a run that fails part-way can leave a draft `vV`, with some assets,
with or without the tag `vV`. Neither counts as a publication
(D-W0-Version), so `V` stays pending and the release source stays frozen.
`next-release` refuses on that residue rather than answering "nothing to
release", naming each part it found. Recovery is the owner's
(`docs/RELEASING.md`):

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

**Supersession of an incomplete published release `vV`** (`Release` and
`immutability` red, naming `vV` and what differs):

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
pin are what tell operators not to use it.

### D-W0-Installation: CI enforces the installation's integrity

The separation between the two copies (`CLAUDE.md`) is enforced on every
pull request and `main` push: `workflow-ci.yml`'s `installation` job installs
the pinned Manager wheel (`OD-W0-2`) and runs `workflow-manager verify .` on
the clean checkout, and `aggregate` requires it. A pull request that edits
an installed command, a managed block or any other managed file fails the
required check, whatever its other changes. The installation changes only
through `workflow-manager update`, which a later pull request may carry;
that requires the pinned Manager to know the target release, so such a pull
request bumps `manager-pin.json` first or together (`docs/RELEASING.md`).

### D-W0-Checks: one aggregate required check

`workflow-ci.yml` runs several jobs and ends in a job named `aggregate` that
needs all of them and fails unless every one succeeded. Required checks on
`main` are `aggregate` and `Conventional Commit title` (the Manager's names),
plus the installed `workflow-conformance` job, which already reports on every
pull request. Adding a CI job later never touches the ruleset.

### D-W0-Settings: settings are reviewed data, applied by the owner

`.github/repository/merge-settings.json` and `ruleset-main.json` are the
Manager's files with this repository's required checks, and one deliberate
difference: `strict_required_status_checks_policy: true` (`OD-W0-5`). The
owner applies them with `gh api`; CI and agents never do. A check becomes
required only after it has reported under that exact name on an open pull
request.

`strict` matters here and not in the Manager: the Manager derives its version
after merge from commit subjects, but this repository decides the version,
the title agreement, D-W0-Pending and D-W0-Immutable **before** merge, on the
merge ref the checks last ran against, and `PR title` re-runs only on
`opened, edited, reopened, synchronize`, never when `main` moves. Without
`strict`, two pull requests that each bump `2.6.0` → `2.7.0` with different
payload changes merge in turn on stale green checks (their
`workflow_version` edits are identical; the digest lines differ), and
`main` then carries an unreviewed combination as `2.7.0`. With `strict`, the
second must be updated to the new base, which re-runs every check
(`synchronize`) and fails it under D-W0-Pending. The cost for a
single-maintainer repository is one `gh pr update-branch` (or "Update
branch") before merging a pull request whose base moved; GitHub auto-merge
does not update the branch itself.

## 4. Open decisions (for the plan reviewer and the user)

This repository has no `docs/TECHNICAL_DECISIONS.md`; these are the decisions
this plan would otherwise finalize silently. Each has a recommendation the
plan is written against.

| id | decision | options | recommendation |
| --- | --- | --- | --- |
| `OD-W0-1` | Version authority | (a) manifest `workflow_version`, set by hand, title must agree (D-W0-Title); (b) Manager-style: tag derived from titles, a build step rewrites the manifest | **(a).** The version is inside the released bytes and the manifest's digests; rewriting it at build time would make the released manifest differ from the reviewed one. |
| `OD-W0-2` | How CI gets the Workflow Manager for the consumer check | (a) download a pinned Manager release wheel (version + sha256 in `tools/release/manager-pin.json`), check it, `pip install`; (b) check out `workflow-manager` at a pinned commit; (c) no consumer check | **(a).** Tests the artifact users actually run; a sha256 pin keeps it reproducible; bumping it is a reviewed one-line change. |
| `OD-W0-3` | Who presses the release button | (a) automatic on a green `main` push (`workflow_run`), like the Manager; (b) manual `workflow_dispatch` only | **(a)**, because a release needs a deliberate manifest bump in a reviewed pull request anyway; `workflow_dispatch` is added too, as the re-run path: it resolves the target exactly as D-W0-Target does and additionally refuses unless a successful `Workflow CI` **push** run exists for the dispatched `main` tip sha (`gh api repos/{repo}/actions/runs?head_sha=<sha>&event=push`), since it bypasses the `workflow_run` gate. |
| `OD-W0-4` | Required checks | `aggregate` + `Conventional Commit title` only, or also `workflow-conformance` | **All three.** The installed suites are the regression net for the installation that runs this repository's own milestones. |
| `OD-W0-5` | `strict_required_status_checks_policy` | (a) on: a pull request must be up to date with `main` before merging; (b) off, like the Manager, relying on the `main`-push re-check alone | **(a).** Version, title agreement, D-W0-Pending and D-W0-Immutable are decided before merge on the merge ref; off, stale green checks merge two conflicting bumps (D-W0-Settings). (b)'s push re-check catches it only after `main` is already wrong. |
| `OD-W0-6` | How the archive's deflate bytes are made reproducible (D-W0-Deflate) | (a) a pinned `zlib-ng` wheel (version + sha256, `--require-hashes`) driving raw deflate under the builder's own gzip framing; (b) a pinned container image whose Python links zlib-ng; (c) reproduce only the tar stream and manifest, and compare published archives after decompression | **(a).** Measured to reproduce all five published digests (section 2); a hash-pinned wheel is smaller and easier to audit than an image; (c) would stop proving the published bytes themselves. |

## 5. Checkpoints

| id | name | depends_on | complexity | session_target |
| --- | --- | --- | --- | --- |
| CP1 | Release tooling: release-source staging, deterministic package build, title grammar, release decision, with tests | - | 3 | 1 |
| CP2 | CI: release-source checks, release-source conformance suites, package immutability, installation integrity, PR title check, aggregate | CP1 | 3 | 1 |
| CP3 | Release workflow: publish an immutable release when main's manifest names an unpublished version | CP1, CP2 | 2 | 1 |
| CP4 | Repository settings as reviewed data, RELEASING.md, README, cutover runbook | CP2, CP3 | 2 | 1 |

<!-- CP1 -->
### CP1 — Release tooling

**Files (new):**

- `tools/release/__init__.py`
- `tools/release/package.py` — stdlib builder (D-W0-Builder):
  `stage(commit, dest)` (D-W0-Stage: `git archive` of the four release-source
  paths, extracted with `filter="data"`); `verify_release(dir)` (manifest
  schema, every listed file present with its sha256 and mode, nothing
  unlisted, no unsafe path, no link); `build(dir, out)` → the three assets,
  deterministic per section 2, deflated per D-W0-Deflate (refuses without
  the pinned `zlib_ng`); `stage_conformance(release_dir, dest)` (the
  conformance fixture: `full`-profile payload — categories `distribution` and
  `conformance` — plus `host-evidence` fixtures, the state templates and the
  `.gitignore` fragment, in a fresh Git repository, one commit).
- `tools/release/release.py` — CLI, stdlib only (the deflate step aside), exit codes 0 ok / 1 refusal /
  2 usage, every undecidable input refuses:
  - `check-title TITLE [--agree]` — grammar and impact; with `--agree`,
    also the D-W0-Title agreement check: the title's impact must equal the
    level of the version change from `HEAD^1`'s manifest to `HEAD`'s
    (D-W0-Version: exact next patch/minor/major, else refused);
  - every command below that needs to know what is published takes
    `--releases FILE` (the saved `gh release list` JSON, D-W0-Version) and
    reads tags from the local Git repository;
  - `check-pending --releases FILE` — D-W0-Version and D-W0-Pending between
    `HEAD^1` and `HEAD`: a version change must be an exact next version; a
    release-source change without a valid version change, or any
    release-source change while `HEAD^1`'s version is not published,
    refuses naming the paths and the pending version;
  - `build --commit SHA --out DIR` — stage, verify, build twice and require
    identical bytes, extract and require a round-trip-identical tree; prints
    the evidence row (version, files, zlib-ng version, tar-stream, archive
    and manifest digests);
  - `check-immutable --releases FILE [--published DIR]` — D-W0-Immutable,
    when the manifest version is published: the offline diff always; with
    `--published` (the downloaded assets), exactly the three asset names
    (a missing or extra one refuses, naming it) and the byte comparison,
    reporting tar-stream vs archive on a mismatch;
  - `next-release --trigger SHA --releases FILE` — D-W0-Target on `main`'s
    first-parent history: prints `state=pending`, `version=V` and
    `target=C_V` when the tip's manifest version is not published, has no
    draft and no tag, and is valid (greater than the highest published
    version, whose tag is an ancestor of `C_V`); prints `state=published`,
    `version=V` and `target=C_V` when `V` is published (the release job then
    reads `vV` back, D-W0-Target; it never prints an empty "nothing"
    answer); refuses anything else,
    naming it (a draft `vV`, a tag `vV` with no published release, a
    published release whose tag is missing, a lower or equal version, a
    non-ancestor tag, a malformed manifest, a trigger not on the
    first-parent history, a trigger whose release source differs from
    `C_V`'s);
  - `check-published --version V --target SHA --releases FILE --assets DIR
    --downloaded DIR` — the release job's read-back, after publishing and
    again on every later run while `V` is published: `vV` published, not a
    draft, exactly the three assets, each byte-equal to the built one, and
    tag `vV` at `SHA`; a refusal names what differs and the supersession
    procedure (D-W0-Recovery), never "nothing to release";
  - `stage-conformance --commit SHA --out DIR` — the conformance fixture.
- `tools/release/manager-pin.json` — `{version, wheel, sha256}` of the
  Workflow Manager release CI uses (`OD-W0-2`), at the newest published
  Manager release when CP1 is implemented.
- `tools/release/deflate-requirements.txt` — the one hash-pinned line
  `zlib-ng==1.0.0 --hash=sha256:5332f945…` (full digest), for Python 3.12 on
  manylinux x86_64 (`OD-W0-6`).
- `tools/release/release_test.py` — `unittest`, stdlib plus the pinned
  `zlib_ng`, hermetic except for the local Git history it reads (release
  lists are fixture JSON files):
  - title grammar and impact table (valid, invalid, `!`, scopes, the
    diagnostic for a near-miss);
  - D-W0-Title agreement on scratch repositories (base = `HEAD^1`): no bump
    + `ci:` passes; no bump + `feat:` fails; patch bump + `fix:` passes;
    patch bump + `ci:` fails; minor bump + `fix:` fails; major bump +
    `feat!:` passes; a version lower than the base's refuses; while the
    base's version is pending (unpublished), a `ci:` change outside the release
    source passes and is `none`-impact (no `feat:` needed);
  - bump level (D-W0-Version): `2.6.0` → `2.6.1`/`2.7.0`/`3.0.0` accepted as
    patch/minor/major; `2.6.0` → `2.8.0`, `2.6.0` → `2.7.1`, `2.6.0` →
    `3.0.1`, `2.6.0` → `2.6.0.1` and a decrease refused;
  - `check-pending` on scratch repositories: published base + payload
    change + valid bump passes; published base + payload change without
    bump refuses;
    pending base + payload change refuses (with and without a further bump);
    pending base + change only under `tools/` or `.github/` passes;
  - **reproduction:** each of `v2.3.1` … `v2.6.0`, staged from its tag and
    built, equals its published tar-stream, archive and manifest digests
    (test constants), and two builds are byte-identical; the test fails,
    rather than skips, when `zlib_ng` is missing or not the pinned version,
    and the builder's gzip header equals `gzip.GzipFile`'s for the same
    parameters;
  - round trip: the extracted tree equals the staged source (files, bytes,
    modes);
  - `verify_release` refuses an unlisted file, a wrong digest, a missing
    file, a `..` location, a symlink;
  - `next-release` on scratch repositories: published → `state=published`
    with `V` and `C_V`;
    unpublished higher → `V` and the introducing commit; unpublished
    lower/equal → refusal;
    highest tag not an ancestor → refusal; **competing runs**: with the bump
    commit followed by two `ci:` commits, triggers at each of the three
    commits all resolve the same `V` and the same `C_V`, and once `V` is
    published every trigger resolves `state=published` with that `V` and
    `C_V`; a trigger whose release source
    differs from `C_V`'s refuses;
  - **failed publication** (D-W0-Recovery), `next-release` on scratch
    repositories with fixture release lists: a draft `vV` with the tag
    `vV` → refusal naming both; a draft without a tag → refusal; a tag
    without any release → refusal; a published release whose tag is
    missing → refusal; then, from the draft-and-tag state, the recovery
    (draft dropped from the list, tag deleted) → resolves `V` and `C_V` again,
    and after the release is published → `state=published`; the tag-only
    recovery (tag deleted, no release ever existed) likewise resolves `V`
    and `C_V`; `check-pending` while only
    a draft or a stray tag exists still treats the version as pending and
    refuses a release-source change;
  - `check-published`: a draft, a missing or extra asset, a differing asset
    byte, and a tag at another commit each refuse, naming the supersession
    procedure;
  - **incomplete published release** (D-W0-Recovery, supersession), on a
    scratch repository whose release list shows `vV` published with its tag
    at `C_V` and whose downloaded fixture assets lack `SHA256SUMS`: a rerun
    is not reported as success — `next-release` answers `state=published`
    (never an empty answer), `check-published` refuses naming the missing
    asset, and `check-immutable --published` refuses naming it; then the
    supersession bump (manifest to the next patch `V'`, no other
    release-source change, titled `fix:`) passes `check-title --agree` and
    `check-pending`, `check-immutable` does not apply to `V'`, and
    `next-release` resolves `state=pending`, `V'` and `C_V'`; with `vV'`
    published and complete, `check-published` for `V'` passes;
  - `check-immutable`: unchanged → ok; a changed payload byte at a published
    version → refusal naming the path; a missing or an extra downloaded
    asset → refusal naming it.

**Verification:** with the pinned wheel installed in a Python 3.12 virtual
environment, `python3 tools/release/release_test.py` green;
`python3 tools/release/release.py build --commit HEAD --out <tmp>` prints
2.6.0's published digests; the same `build` without `zlib_ng` refuses;
`workflow-manager verify .` clean.

<!-- /CP1 -->

<!-- CP2 -->
### CP2 — CI

**Files (new):**

- `.github/workflows/workflow-ci.yml`, name `Workflow CI`, on `pull_request`,
  `push: [main]` and `workflow_dispatch`; `permissions: contents: read`;
  Python 3.12 on `ubuntu-latest` (x86_64). Every job that builds a package
  first runs `pip install --require-hashes -r
  tools/release/deflate-requirements.txt` (D-W0-Deflate). Jobs:
  - `tooling` — `python3 tools/release/release_test.py` (full history
    checkout, tags fetched), so the five-release archive reproduction runs
    in CI's own runtime on every run;
  - `package` — `release.py build --commit HEAD`; install the pinned Manager
    wheel (download, `sha256sum -c` against `manager-pin.json`, `pip
    install`); `workflow-manager package verify <archive> --sha256 <digest>`;
    `git init` a scratch repository, `workflow-manager --release-dir <staged>
    bootstrap <scratch>`, then `workflow-manager --release-dir <staged>
    verify <scratch>` (the global flag again: without it `verify` resolves
    the installed version through the Manager's pins, which refuse a
    version the pinned Manager does not know, so W1's unpublished 2.7.0
    would fail there first); upload the three assets as a workflow
    artifact;
  - `immutability` — save `gh release list --json tagName,isDraft --limit
    1000` (`GH_TOKEN` from `github.token`); `release.py check-pending
    --releases` (D-W0-Pending, against `HEAD^1`), then `release.py
    check-immutable --releases`; when the manifest version is published,
    `gh release download v<V>` into a scratch directory, then
    `check-immutable --published`;
  - `installation` — install the pinned Manager wheel as in `package`, then
    `workflow-manager verify .` on the checkout (D-W0-Installation);
  - `release-source-conformance` — `release.py stage-conformance --commit
    HEAD`, then the release source's own seven frozen suites (the same list
    `workflow-conformance.yml` runs) inside the fixture;
  - `aggregate` — `needs` all five, `if: always()`, fails unless each result
    is `success`.
- `.github/workflows/pr-title.yml`, name `PR title`, job name
  `Conventional Commit title`, on `pull_request` `[opened, edited, reopened,
  synchronize]`; the title passed through `env`, never interpolated; runs
  `release.py check-title "$TITLE" --agree` on the pull request's merge ref
  (fetch depth 0, tags fetched).

**Verification:** `actionlint` if available, else a YAML parse; each job's
command run locally against HEAD under Python 3.12 with the pinned wheel
(the immutability job with assets fetched by `gh release download v2.6.0`);
the conformance fixture's seven suites green locally. The `installation`
job's command, in a scratch worktree of HEAD: clean → exit 0; one line
appended to `.claude/commands/accept-milestone.md` → exit 1 naming the file
(a planning-time run already showed this, section 2). The `package` job's Manager steps run once more against an
**unpinned** version: a scratch commit of the staged release source with
`workflow_version` set to `2.99.0`, built, then `workflow-manager
--release-dir <staged> bootstrap <scratch>` and `workflow-manager
--release-dir <staged> verify <scratch>` both pass, and `verify` without
`--release-dir` is shown to refuse (the reason the flag is spelled out).
The real CI evidence is the cutover pull request (section 7): its `tooling`
job reproduces the five archive digests on a GitHub runner, and its
`immutability` job matches the downloaded `v2.6.0` assets byte-for-byte.

<!-- /CP2 -->

<!-- CP3 -->
### CP3 — Release workflow

**File (new):** `.github/workflows/release.yml`, name `Release`:

- triggers: `workflow_run` of `Workflow CI`, `types: [completed]`,
  `branches: [main]`, job guarded by `event == 'push' && conclusion ==
  'success'`; and `workflow_dispatch` (re-run path, `main` only), whose
  trigger is `main`'s tip and which first refuses unless a successful
  `Workflow CI` push run exists for that sha (`OD-W0-3`);
- job-level `concurrency: {group: workflow-release, cancel-in-progress:
  false}`; `permissions: contents: write, actions: read`;
- steps: check out `main` with full history and tags; `release.py
  next-release --trigger <sha>` (D-W0-Target) yields `state`, `V` and
  `C_V`; `release.py build --commit <C_V>`;
- `state=published`: the read-back only — save the release list, `gh
  release download v<V>`, `release.py check-published --version V --target
  <C_V>`; success ends the job green with the notice "nothing to release
  (vV read back intact)", a refusal fails it naming what differs and the
  supersession procedure (D-W0-Recovery);
- `state=pending`: the Manager `package verify` and bootstrap/verify
  as in CP2; then `gh release create v<V> --target <C_V> --title
  "Workflow <V>" --notes "Workflow release <V>." --latest <assets…>`; then
  the read-back: save the release list again, `gh release download v<V>`,
  `release.py check-published` (D-W0-Target). `gh release create` is a
  draft, uploads and a publish, not one atomic call: a failure inside it
  can leave a draft and a tag, which the next run's `next-release` refuses
  on (D-W0-Recovery); a failure before it leaves nothing;
- the release list is saved with the job's `contents: write` token, so
  drafts are visible to `next-release`;
- the build steps install the pinned deflate wheel (D-W0-Deflate);
- never `--clobber`, never `gh release upload`, never `gh release delete`,
  never `git tag`/`git push`, never a manifest change: the job never repairs
  a failed publication or supersedes a version itself.

**Verification:** a dry run of the decision steps against HEAD locally
(`next-release` prints `state=published`, `version=2.6.0`,
`target=2d5b760…`, and the published-path read-back of `v2.6.0` passes);
the CP1
scratch-repository tests already cover the pending case, competing
triggers and every failed-publication residue. **Recovery rehearsal**, live,
in a throwaway private repository the owner creates, authorizes for this
and deletes afterwards (never this repository), with release immutability
on and a release source whose manifest names `0.0.1`:

1. reproduce the failed-publication state: `gh release create v0.0.1
   --draft --target <C_V>` with one of the three assets, and the tag
   `v0.0.1` pushed at `C_V`;
2. `next-release` (release list saved with a write token) refuses, naming
   the draft and the tag;
3. apply D-W0-Recovery's steps 1-3 exactly as `docs/RELEASING.md` will
   state them; both inspections then find nothing;
4. `next-release` resolves `0.0.1` and `C_V`; the release job's publish and
   read-back commands succeed; `next-release` then answers
   `state=published`, and the published-path read-back passes.

**Supersession rehearsal**, in the same throwaway repository:

5. reproduce an incomplete published release: bump the manifest to `0.0.2`
   on the throwaway `main`, then `gh release create v0.0.2 --target
   <C_0.0.2>` with only the archive and manifest assets (published, so
   immutable, but without `SHA256SUMS`);
6. the release job's published-path commands (`next-release`, then the
   read-back) fail, naming the missing `SHA256SUMS` and the supersession
   procedure — not "nothing to release" — and so does `check-immutable
   --published`;
7. apply D-W0-Recovery's supersession steps 1-4 exactly as
   `docs/RELEASING.md` will state them: a `0.0.3` bump commit with no other
   release-source change passes `check-title --agree` (`fix:`) and
   `check-pending`; `next-release` resolves `0.0.3`; publish and read-back
   succeed; `v0.0.2` is unchanged (`gh release view v0.0.2 --json
   assets,isDraft` before and after).

The transcript goes in `docs/ACTIVE_MILESTONE.md`. The live proof on this
repository is that the cutover merge's `Release` run ends green with
"nothing to release (v2.6.0 read back intact)" after reading `v2.6.0` back.

<!-- /CP3 -->

<!-- CP4 -->
### CP4 — Settings, documentation, cutover runbook

**Files:**

- `.github/repository/merge-settings.json` (new) — the Manager's file:
  squash only, `PR_TITLE`/`BLANK`, auto-merge on, delete branch on merge.
- `.github/repository/ruleset-main.json` (new) — the Manager's ruleset with
  required checks `aggregate`, `Conventional Commit title` and
  `workflow-conformance` (`OD-W0-4`),
  `strict_required_status_checks_policy: true` (`OD-W0-5`), no bypass
  actors.
- `docs/RELEASING.md` (new) — how a release happens (D-W0-Version, the
  manifest bump in the release-source pull request, the title rule), what
  CI checks, the pending-release freeze (D-W0-Pending) and the release
  target (D-W0-Target), the `strict` "update branch" step, the release job,
  when nothing is released, failure recovery (fix forward in a `ci:` pull
  request; D-W0-Recovery's four steps verbatim: inspect the draft **and**
  the tag separately, delete both with `gh release delete v<V> --yes
  --cleanup-tag` and, if the tag survives, `git push origin --delete
  refs/tags/v<V>`, confirm both are gone, re-run via `workflow_dispatch`;
  never touch a published release; the tag-only variant that skips `gh
  release delete`), the supersession of an incomplete published release
  (D-W0-Recovery's five steps verbatim, including "never add a
  `workflow-manager` pin for `V`") with an initially empty "Superseded
  releases" table (version, superseded by, read-back failure, date), the pinned compression runtime and how
  to run the build locally (D-W0-Deflate), the installation check and the
  Manager-pin bump an installation update needs (D-W0-Installation), the
  `workflow-manager` pin follow-up (pointing at
  the Manager's own "Workflow packages: adding a pin"), applying and reading
  back the repository settings, and this milestone's cutover (section 7).
- `README.md` — what this repository is, the two copies of the Workflow, the
  current release, and links to `docs/RELEASING.md` and `docs/ROADMAP.md`.
  (It still says "Workflow 2.6.0 … release 2.6.0", which was the tag-tree
  README.)
- `CLAUDE.md` — repository-owned text only: replace "Until W0 lands, `main`
  has no required checks" with the required checks and a pointer to
  `docs/RELEASING.md`. The managed blocks are not touched.

**Verification:** the JSON files parse and match the Manager's shape
(except `strict`, `OD-W0-5`);
`workflow-manager verify .` clean; every command in `docs/RELEASING.md` is
one CP1-CP3 actually provide, and its recovery and supersession commands
are the ones the CP3 rehearsals ran.

<!-- /CP4 -->

## 6. Tests and verification summary

| what | where | when |
| --- | --- | --- |
| tooling unit and reproduction tests, five archive digests in the pinned deflate runtime | `tools/release/release_test.py` | CP1, then every CI run (`tooling`) |
| failed-publication residue refused; recovery (draft, and tag-only) restores a publishable state | `release_test.py` (fixtures); CP3 rehearsal (live, throwaway repository) | CP1, CP3 |
| incomplete published release fails every rerun's read-back, never "nothing to release"; supersession by the next patch version publishes | `release_test.py` (fixtures); CP3 supersession rehearsal (live, throwaway repository) | CP1, CP3 |
| package builds, Manager verifies it, bootstrap/verify a scratch repo | CI `package` | every CI run |
| release source unchanged at a published version; frozen while a version is pending; exact next-version bumps | CI `immutability` (`check-immutable`, `check-pending`) | every CI run |
| release source's own frozen suites | CI `release-source-conformance` | every CI run |
| installation's suites (existing) | `workflow-conformance` | every CI run |
| title grammar and agreement | `PR title` | every pull request |
| release decision, deterministic target, published read-back (after publishing, and of an already-published `V` on every run) | `Release` | every green `main` push |
| installation intact | CI `installation` (`workflow-manager verify .`), and locally | every CI run; each checkpoint, acceptance |

## 7. Cutover (owner actions, after functional review, before acceptance)

Each step is the repository owner's, or one the owner explicitly authorizes;
an agent states the commands and reads results back. Evidence goes in
`docs/ACTIVE_MILESTONE.md`.

1. Push the branch and open the pull request titled `ci: CI, releases and
   main protection for the workflow repository` (impact `none`; the manifest
   stays at 2.6.0).
2. Confirm on the pull request's final head that `aggregate`, `Conventional
   Commit title` and `workflow-conformance` all reported green under exactly
   those names (`gh pr checks <n> --json name,state`), that the `tooling`
   job reproduced all five archive digests, that the `immutability` job
   compared against the downloaded `v2.6.0` assets, and that the
   `installation` job ran `workflow-manager verify .`.
3. Apply `merge-settings.json`, then create the ruleset (`gh api`, per
   `docs/RELEASING.md`), and read both back.
4. **Installation-integrity proof:** open a draft pull request from a
   throwaway branch based on the cutover branch whose only change is one
   line appended to `.claude/commands/accept-milestone.md`; confirm the
   `installation` job fails naming that file, `aggregate` fails, and the
   pull request is blocked from merging
   (`gh pr view <n> --json mergeStateStatus`); then close it and delete the
   branch.
5. After `/accept-milestone`, squash-merge.
6. Confirm `main`'s `Workflow CI` push run is green and the `Release` run it
   triggers ends green with "nothing to release (v2.6.0 read back intact)",
   having downloaded and read back `v2.6.0`, and that `gh release list`
   still shows `v2.6.0` as latest with no new release or tag.

## 8. Risks

| risk | mitigation |
| --- | --- |
| The ported builder drifts from the Manager's format | five-release byte reproduction in tests; Manager `package verify` + bootstrap in CI and in the release job |
| The release-source conformance fixture differs from the Manager's, so suites fail for fixture reasons | built from the same manifest categories and templates as `build_conformance_repo`; verified green against 2.6.0 in CP2 before CI depends on it |
| A required check that never reports locks `main` | ruleset applied only after all three names reported on the cutover pull request; no bypass actors, so recovery is editing the ruleset (documented) |
| Release job publishes from a commit that is no longer `main`, or two runs publish different bytes | D-W0-Target: target is the introducing commit `C_V` on first-parent history, release source checked equal at the trigger; job-level concurrency; pinned deflate (D-W0-Deflate); read-back of the published release and its tag |
| A failed publication leaves a draft and/or a tag, and the next run publishes nothing | a draft or a tag is not a publication (D-W0-Version); `next-release` refuses on the residue, naming it; D-W0-Recovery deletes both and is rehearsed live (CP3) |
| CI's compression runtime differs from the one that built the published archives | pinned, hash-checked `zlib-ng` wheel (D-W0-Deflate, `OD-W0-6`); five-release archive reproduction runs in CI's own runtime on every run, failing closed; tar-stream digests separate source changes from deflate drift |
| A release-source or tooling pull request also changes an installed file | CI `installation` job (`workflow-manager verify .`) under the required `aggregate` (D-W0-Installation); proven on a throwaway pull request at cutover |
| A publication completes but its read-back fails (missing, extra or differing asset; tag elsewhere), and a rerun reports "nothing to release" | an already-published `V` is read back on every `Release` run and compared byte-for-byte by `immutability` on every CI run, so both stay red; the release is never repaired in place: D-W0-Recovery's supersession publishes the next patch version, records the superseded one in `docs/RELEASING.md` and never pins it in `workflow-manager`; tested in CP1 and rehearsed live (CP3) |
| `workflow_run` releases from a stale trigger | `next-release` reads the tags and the release list afresh; an already-published version is read back and publishes nothing |
| Release-source change merged while `V` is pending | D-W0-Pending on the pull request and again on the `main` push; `strict` (`OD-W0-5`) keeps pull-request checks current |
| Two pull requests bump to the same `V` on stale checks | `strict` forces an update and re-run; the second then fails D-W0-Pending |
| The Manager pin goes stale | it only has to verify and bootstrap; bumping it is a one-line reviewed change, documented |
| Network or API failure in `immutability` | the job fails (fail closed); the offline diff still runs first and names the path |
| A release run fails after the bump merged, leaving `main` at an unpublished `V` | the release source is frozen (D-W0-Pending) but tooling fixes are `ci:` (D-W0-Title's base baseline); re-run `Release` (`workflow_dispatch`) after D-W0-Recovery, documented in `docs/RELEASING.md` |

## 9. Requirements

Mapping: `docs/ai-workflow/requirements/workflow-repository-setup-mapping.json`.

| id | requirement | checkpoints |
| --- | --- | --- |
| REQ-1 | Release source staged apart from the installation; deterministic package, in a pinned compression runtime, reproducing 2.3.1-2.6.0 byte-for-byte | CP1 |
| REQ-2 | Conventional-Commit titles, one stdlib implementation, impact agrees with the version change | CP1, CP2 |
| REQ-3 | CI over the release source and the installation: conformance suites, package build + Manager verify/bootstrap, immutability, `workflow-manager verify .`, `aggregate` | CP2 |
| REQ-4 | Release workflow publishes `vV` exactly when `main`'s manifest names an unpublished `V`; never moves a published tag or replaces an asset; a failed publication is detected and recoverable; an incomplete published release fails every rerun and is superseded by a new version | CP3 |
| REQ-5 | `main` protection recorded as reviewed data, applied by the owner | CP4 |
| REQ-6 | `docs/RELEASING.md` and `README.md` document the release model, the two copies, the pin follow-up and the cutover | CP4 |

## 10. Artifact classification

`docs/ai-workflow/registry/workflow-repository-setup-artifacts.json`, from the
`process` template, reviewed against this plan's footprint:

- **plan stage:** the template as generated, plus the exclusions plan
  amendment 0 added (section 11): `tools/`, `docs/RELEASING.md`, and the
  release source (`manifest.json`, `payload/`, `fixtures/`, `templates/`).
  Every path this item's checkpoints write is therefore classified at
  both stages. Planning touches only this plan, the registry, the mapping
  (protected), the declarations file, the state file and
  `docs/ACTIVE_MILESTONE.md` (excluded).
- **implementation stage:** added to the protected set — `tools/` (prefix);
  the exact paths `.github/workflows/workflow-ci.yml`, `pr-title.yml`,
  `release.yml`, `.github/repository/merge-settings.json`,
  `ruleset-main.json` (carved out of the template's shared `.github/`
  exclusion, which still covers the managed `workflow-conformance.yml`);
  `docs/RELEASING.md`; `README.md` and `CLAUDE.md` (moved from excluded,
  since this item authors them); and the release source, `manifest.json`,
  `payload/`, `fixtures/`, `templates/`, protected rather than excluded so
  that any change W0 must not make is visible to review. The template's
  protected `scripts/` and `.claude/commands/` (the installation) stay
  protected; W0 does not change them.

## 11. Review rounds and decisions

### Local plan review, round 1 (revision 1 → 2): `REVISE`, all findings accepted

Each finding was checked against this repository and `workflow-manager`
(`eeb1de6`) before being applied.

- **IMP-1 (pending-release state): accepted.** Confirmed: revision 1's
  D-W0-Immutable began "For a manifest version `V` that is already tagged",
  D-W0-Title measured from the highest tag, and its own last risk row
  conceded that a pending `V` demanded a releasing title from every pull
  request. Applied as the reviewer's (a)-(c), with (b) made stricter: the
  version change is measured against `HEAD^1` (D-W0-Version, D-W0-Title);
  **any** release-source change, a further bump included, is refused while
  the base's version is pending (D-W0-Pending) — rather than allowing a bump
  beyond `V`, so that no merged version is ever skipped unpublished; and the
  release is built and tagged at the introducing commit `C_V`
  (D-W0-Target). CP1 gains `check-pending` and the competing-trigger,
  pending-base and `ci:`-while-pending tests; CP2's `immutability` job runs
  `check-pending`; CP3 resolves the target through `next-release
  --trigger`.
- **IMP-2 (`strict` off): accepted, `strict` on** (`OD-W0-5`,
  D-W0-Settings). Confirmed: the Manager's `ruleset-main.json` has
  `"strict_required_status_checks_policy": false`, and its `release.yml`
  derives the version after merge (`next-version`, `resolve-target`). One
  premise corrected: GitHub auto-merge does not update a stale branch, so the
  cost is an explicit `gh pr update-branch`, documented in
  `docs/RELEASING.md`.
- **OPT-1 (bump level for non-adjacent versions): accepted.** A version
  change must be exactly the next patch, minor or major (D-W0-Version); CP1
  test rows added.
- **OPT-2 (dispatch must require green CI): accepted.** `OD-W0-3` and CP3:
  the dispatch path refuses without a successful `Workflow CI` push run for
  its sha; `actions: read` added.
- **OPT-3 (draft-release residue): accepted** in CP4's `docs/RELEASING.md`
  recovery section. Not reproduced here (it needs a failing upload against a
  live repository); documenting the check costs nothing.
- **Missing test (`verify` needs `--release-dir`): accepted.** Confirmed in
  `workflow-manager`'s `src/workflow_manager/cli.py`: `_release_for_target`
  calls `_resolve`, which uses `local_release` only when `args.release_dir`
  is set and otherwise `ReleaseCache.resolve`, which refuses an unpinned
  version. CP2 now spells out both commands with the global flag and adds a
  verification against an unpinned `2.99.0`.
- **Architecture note (template rationale strings):** no action. The
  plan-stage artifact declaration is the generated `process` template; its
  rationale strings are template boilerplate, not claims about this
  repository.

### Manual external plan review, round 1 (revision 2 → 3): `REVISE`, all findings accepted

Bundle `e8f6af92…`, `review_content_id` `29cffe01…`. No blocking or
optional findings. Each important finding was reproduced in this
repository before being applied.

- **IMP-1 (byte-for-byte proof is runtime-dependent): accepted.**
  Reproduced: building all five tags with the Manager's `build_package`
  under Python 3.12 / stock zlib 1.3.2 gives five archive digests that
  differ from the published ones (2.6.0: `af28b52b…`), while the tar streams
  and manifest assets are identical to those built under Python 3.14 /
  zlib-ng, which reproduces the published digests. Raw deflate from the
  PyPI `zlib-ng` 1.0.0 wheel (bundled zlib-ng 2.2.5) under Python 3.12, with
  the builder writing `GzipFile`'s header and trailer, reproduces all five
  (section 2). Applied as D-W0-Deflate and `OD-W0-6`: a hash-pinned wheel in
  `tools/release/deflate-requirements.txt`, no fallback to `zlib`,
  reproduction tests that fail rather than skip, tar-stream digests asserted
  separately, and the reproduction run in CI's own runtime by the `tooling`
  job on every run (the reviewer's missing test). Whether the wheel's output
  is identical on GitHub's runners is proven at the cutover pull request,
  not assumed; until then it is a stated risk that fails closed.
- **IMP-2 (failed publication can strand a version): accepted.** Confirmed
  in `gh release create --help` (gh 2.101.0): with assets it creates a
  draft, uploads, then publishes, in separate API calls, and a draft's tag
  is mutable; `gh release delete --help`: the tag is deleted only with
  `--cleanup-tag`. Revision 2's "a draft has no tag" and "creates the tag
  atomically with the release" (CP3, CP4, risk table) were wrong and are
  removed. Applied: "published" now means a non-draft release *and* its
  tag (D-W0-Version), so residue keeps `V` pending and frozen;
  `next-release` refuses on a draft or a stray tag instead of answering
  "nothing to release"; D-W0-Recovery inspects and deletes both; the
  release job reads the published release back (`check-published`). Tested
  hermetically in CP1 (every residue, then recovery, then a successful
  resolution) and rehearsed live in CP3 in a throwaway repository, never
  this one, since reproducing it here would mean creating a real `v2.6.1`
  draft and tag.
- **IMP-3 (required CI does not verify the installation): accepted.**
  Confirmed: `workflow-conformance.yml` runs the installed suites only, and
  in a scratch worktree `workflow-manager verify .` exits 1 for one line
  appended to `.claude/commands/accept-milestone.md` — a change revision 2's
  required checks would pass. Applied as D-W0-Installation: an
  `installation` job under `aggregate` on every pull request and `main`
  push, plus a cutover proof on a throwaway draft pull request (the
  reviewer's missing test). `workflow-conformance.yml` itself stays as
  installed.
- **Usability concern (recovery runbook):** covered by D-W0-Recovery's step
  1, which inspects the draft and the tag separately, and CP4's
  `docs/RELEASING.md` text.

### Manual external plan review, round 2 (revision 3 → 4): `REVISE`, all findings accepted

Bundle `d5ca6b5b…`, `review_content_id` `6a17b0ad…`. No blocking findings.
Each finding was checked against revision 3 before being applied.

- **Important (an incomplete published release reads as "nothing to
  release"): accepted.** Confirmed in revision 3: CP1's `next-release`
  "prints nothing when `V` is published", CP3 ended the job green on empty
  output, and D-W0-Recovery step 2 said only "a wrong one is superseded by a
  new version", with no procedure. A published release whose
  `check-published` failed was therefore green on every later run. (CI's
  `immutability` job would have gone red on the next run, but revision 3 did
  not require exactly three downloaded assets, so a missing `SHA256SUMS`
  was not named.) Applied: `next-release` answers `state=published` with
  `V` and `C_V` and never answers with empty output; the release job reads an
  already-published `V` back on every run (D-W0-Target, CP3);
  `check-immutable --published` requires exactly the three assets
  (D-W0-Immutable); D-W0-Recovery gains the supersession procedure (leave
  `vV`, never pin it, bump to the next patch in a `fix:` pull request,
  record it in `docs/RELEASING.md`'s "Superseded releases"); REQ-4, the
  risk table, CP4 and the cutover's step 6 follow. One premise checked:
  supersession needs no exception to D-W0-Pending or D-W0-Immutable, since
  `HEAD^1`'s `V` counts as published and the bump's `V'` is not.
- **Optional (tag-only recovery runs `gh release delete` first):
  accepted.** D-W0-Recovery step 3 now branches on step 1's inspection: a
  tag with no release skips `gh release delete` (which fails with "release
  not found" before reaching the tag) and runs only `git push origin
  --delete`; CP1 adds the tag-only recovery resolution test, and CP4 the
  variant in `docs/RELEASING.md`.
- **Missing test (published release with a missing asset): accepted.**
  CP1's "incomplete published release" fixture test (read-back refuses, a
  rerun answers `state=published` and is not reported as success, the
  supersession bump passes every check and resolves `V'`), and CP3's live
  supersession rehearsal in the throwaway repository (an immutable `v0.0.2`
  published without `SHA256SUMS`, superseded by `v0.0.3`, `v0.0.2` left
  unchanged).
- **Architecture concern (the deflate wheel runs beside a write-capable
  token): acknowledged, no change in this revision.** The reviewer states
  the limit correctly: the sha256 pin rules out substitution and the
  five-digest reproduction proves output parity, but neither proves the
  wheel's provenance. The release job's token is this repository's
  `GITHUB_TOKEN` with `contents: write, actions: read` only, and every
  asset it publishes is then checked byte-for-byte (`check-published`) and
  verified by the pinned Manager. Splitting the build (read-only token,
  wheel installed) from the publish (write token, stdlib only) is the
  stronger shape; it needs `next-release`'s draft detection to run a second
  time under the write token, so it is recorded here as a candidate for a
  later roadmap step rather than widening W0.
- **Migration/data-integrity and usability concerns:** covered by the
  supersession procedure (no in-place repair; superseded versions recorded
  and never pinned) and the two recovery variants in `docs/RELEASING.md`.

### Plan amendment 0 (revision 4 → 5): plan-stage classification, after CP1

Requested from `IMPLEMENTING` after CP1 (`75b66f6`). Revision 4's
plan-stage declaration was the `process` template unchanged, and it left
unclassified the implementation paths that only section 10's
implementation-stage additions named: `tools/`, `docs/RELEASING.md` and the
release source. The plan-stage digest classifies every path changed since
the base commit (`bf51137`). Once CP1 committed `tools/release/*`, every
plan-stage check, including the plan-approval check, raised
`UnclassifiedPathError: tools/release/__init__.py`.

- **Change:** `plan_stage.excluded_prefixes` gains `tools/`, `payload/`,
  `fixtures/` and `templates/`, and `plan_stage.excluded_paths` gains
  `docs/RELEASING.md` and `manifest.json`. These are implementation
  deliverables, or content W0 must leave unchanged, and are already
  protected at the implementation stage. They are not plan design content.
  The implementation-stage declaration is unchanged. Checked: every tracked
  path, together with every new file the checkpoints name, now matches a
  classification at both stages.
- **Unchanged:** goal, design decisions, open decisions, checkpoints
  (re-generated at revision 5), requirements and mapping. CP1 stays
  `COMPLETE`; CP2-CP4 are unchanged.
- **Why exclusion rather than protection at plan stage:** protecting
  `tools/` at plan stage would put CP1's implementation into the plan
  digest. Every later implementation commit would then make a plan
  approval stale. That is the coupling the two-stage split exists to
  avoid.

### Plan amendment 0, revision 5 → 6: checkpoint anchors

`/approve-review plan` refused revision 5 with
`AmendmentAnchorCoverageError: CP1 has no well-formed anchor pair in the
plan document being approved`. An amended plan must delimit every registry
checkpoint id with a `<!-- CPn -->`/`<!-- /CPn -->` anchor pair
(`MILESTONE_WORKFLOW.md`, `AMENDING_PLAN`; `request-plan-amendment.md`).
The item was withdrawn from `AWAITING_PLAN_APPROVAL` to `AMENDING_PLAN` to
fix that.

- **Change:** each section in section 5, `CP1` to `CP4`, is wrapped in one
  `<!-- CPn -->`/`<!-- /CPn -->` pair, running from its `### CPn` heading
  to the line before the next checkpoint heading (for `CP4`, the line
  before section 6). The title's `(Revision N)` marker and the header's
  plan-revision line move to 6 to match the registry. Nothing else in the
  plan changes.
- **Consequence for CP1:** revision 4, the pre-amendment plan, has no
  anchors. Reconciliation therefore cannot match CP1's content and treats
  it conservatively as changed. At approval CP1 moves from `COMPLETE` to
  `NEEDS_REVALIDATION`, and `/milestone-implement` re-runs it. This
  replaces revision 5's statement above that "CP1 stays `COMPLETE`". CP1's
  scope, files and tests are unchanged, so revalidation re-runs its
  verification against the existing commit `75b66f6`.
