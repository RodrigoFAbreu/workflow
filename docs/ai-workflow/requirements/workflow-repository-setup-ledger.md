# `workflow-repository-setup` Requirements Ledger

Mutable, human-readable execution record for the `workflow-repository-setup`
work item (W0). Physically separate from the immutable, machine-readable
`workflow-repository-setup-mapping.json` in this same directory: the mapping
is the approved requirement↔checkpoint binding and is plan-stage protected;
this ledger resolves under the excluded prefix `docs/ai-workflow/requirements/`,
so editing it never stales an approval.

Each checkpoint appends one section here as it completes. This is a log, not
a status source: `WORKFLOW_STATE.json`'s `checkpoints[id]` remains the sole
record of checkpoint status.

## `CP1` — Release tooling

Requirements: REQ-1 (staged release source, deterministic package in a
pinned compression runtime, reproducing 2.3.1-2.6.0), REQ-2 (title grammar
and agreement; the CI wiring is CP2's).

- **Implementation** (all new, under `tools/release/`):
  - `package.py`: `stage` (`git archive <commit> manifest.json payload
    fixtures templates`, extracted with the `data` filter), `verify_release`
    (manifest schema; every listed file present with its sha256, size and
    executable bit; nothing unlisted; no stray directory; no unsafe path; no
    link), `tar_stream` and `build` (the Manager's `D-Package-Format`; the
    archive is `GzipFile(filename="", mtime=0, compresslevel=9)`'s header,
    raw deflate from the pinned `zlib_ng`, and the CRC-32/size trailer;
    refuses without `zlib_ng` reporting zlib-ng `2.2.5`, no fallback), and
    `stage_conformance` (the Manager's `build_conformance_repo`).
  - `release.py`: `check-title [--agree]`, `check-pending`, `build`,
    `check-immutable [--published]`, `next-release`, `check-published`,
    `stage-conformance`; exit 0/1/2; `--repo` selects the repository. The
    release list is read from a saved `gh release list --json
    tagName,isDraft` file, tags from the local repository. A version is
    published only as a non-draft release with its tag; a draft or a tag
    alone is pending residue, and a non-draft release without its tag
    refuses.
  - `deflate-requirements.txt`: `zlib-ng==1.0.0` with the full sha256 of
    the cp312 manylinux x86_64 wheel (`5332f945…439f`, checked against
    PyPI).
  - `manager-pin.json`: Workflow Manager `1.2.0`, the newest published
    Manager release, wheel `workflow_manager-1.2.0-py3-none-any.whl`,
    sha256 `f7ab05a2…4139` (checked against the release's `SHA256SUMS` and
    by `sha256sum` of the downloaded wheel).
  - `release_test.py`: 62 tests, every row CP1 names.
- **Verification** (Python 3.12.14 virtual environment, pinned wheel
  installed with `pip install --only-binary=:all: --require-hashes -r
  tools/release/deflate-requirements.txt`):
  - `python tools/release/release_test.py`: `Ran 62 tests`, `OK`.
  - The same suite under Python 3.12 without `zlib_ng`: 12 failures, 8
    errors, none skipped (the build tests fail closed).
  - `release.py build --commit HEAD --out <tmp>`: `version=2.6.0`,
    `files=70`, `zlib_ng=2.2.5`, `tar_sha256=1b8a3e79…e348`,
    `archive_sha256=dc86a796…9f61`, `manifest_sha256=d92517a2…fc2e`, the
    published 2.6.0 digests; without `zlib_ng` it refuses (`zlib_ng is not
    installed`, exit 1).
  - All five tags reproduce: archive and manifest digests equal
    `workflow-manager`'s `published_releases.json` pins; the tar-stream
    digests are recorded as test constants.
  - Against the live `v2.6.0` (`gh release download v2.6.0`, release list
    saved with `gh release list`): `next-release --trigger HEAD` prints
    `state=published`, `version=2.6.0`, `target=2d5b760…`;
    `check-immutable --published` and `check-published --version 2.6.0
    --target 2d5b760` both pass; `check-pending` passes.
  - `stage-conformance --commit HEAD`: the fixture's `git ls-files -s`
    equals that of the Manager's `build_conformance_repo` for the same
    staged release (same paths, modes and blobs);
    `workflow_fingerprint_test.py` (242 tests) and
    `workflow_state_completion_obligations_test.py` (106 tests) green in it
    (the seven-suite run is CP2's verification).
  - `workflow-manager verify .`: `installation matches workflow 2.6.0`.
- **Review**: the diff touches only `tools/release/` and this work item's
  narrative files. No release-source or installation file changed.

### `CP1` revalidation (plan revision 6)

Plan amendment 0 (revisions 5 and 6) added the plan-stage exclusions and the
`<!-- CPn -->` anchors. Revision 4 had no anchors, so approving revision 6
moved CP1 to `NEEDS_REVALIDATION`. CP1's scope, files and tests are
unchanged, and `tools/` is byte-identical between `75b66f6` and `3f576d9`
(`git diff --stat 75b66f6 3f576d9 -- tools/` is empty). Nothing was
re-implemented. The verification was re-run at `3f576d9`:

- `python tools/release/release_test.py` in a fresh Python 3.12 virtual
  environment, with the pinned wheel installed with `pip install
  --require-hashes -r tools/release/deflate-requirements.txt`
  (`zlib-ng 1.0.0`): `Ran 62 tests`, `OK`.
- `release.py build --commit HEAD --out <tmp>`: `version=2.6.0`,
  `files=70`, `zlib_ng=2.2.5`, `tar_sha256=1b8a3e79…e348`,
  `archive_sha256=dc86a796…9f61`, `manifest_sha256=d92517a2…fc2e`. These
  equal the published 2.6.0 digests (`release_test.py`'s constants).
- The same `build` under Python 3.12 without `zlib_ng` refuses:
  `zlib_ng is not installed`, exit 1.
- `workflow-manager verify .`: `installation matches workflow 2.6.0`.

## `CP2` — CI

Requirements: REQ-2 (the title check's CI wiring), REQ-3 (CI over the
release source and the installation).

- **Implementation** (both new):
  - `.github/workflows/workflow-ci.yml`, `Workflow CI`, on `pull_request`,
    `push: [main]` and `workflow_dispatch`; `permissions: contents: read`;
    Python 3.12 on `ubuntu-latest`; `shell: bash` by default, so `-o
    pipefail` applies. Jobs:
    - `tooling`: full history and tags, the pinned deflate wheel, then
      `release_test.py`;
    - `package`: `release.py build --commit HEAD`, `package.stage` of HEAD,
      the pinned Manager wheel (downloaded from the `workflow-manager`
      release, checked with `sha256sum -c` against `manager-pin.json`,
      installed), `workflow-manager package verify <archive> --sha256
      <digest>`, then `--release-dir <staged> bootstrap` and `--release-dir
      <staged> verify` of a fresh `git init` scratch repository; the three
      assets are uploaded as the `package` artifact;
    - `immutability`: the release list saved with `gh release list --json
      tagName,isDraft --limit 1000`, then `check-pending` and
      `check-immutable`; when the manifest version is a non-draft release,
      `gh release download v<V>` and `check-immutable --published`;
    - `installation`: the pinned Manager wheel, then `workflow-manager
      verify .`;
    - `release-source-conformance`: `release.py stage-conformance --commit
      HEAD`, then the seven suites `workflow-conformance.yml` runs, in the
      same order, in the fixture's `scripts/`;
    - `aggregate`: `needs` all five, `if: always()`, fails naming every
      job whose result is not `success`.
  - `.github/workflows/pr-title.yml`, `PR title`, job `Conventional Commit
    title`, on `pull_request` `[opened, edited, reopened, synchronize]`:
    full-history checkout of the merge ref, the title through `env`, then
    `release.py check-title "$TITLE" --agree`.
- **Verification** (Python 3.12 virtual environment with `zlib-ng 1.0.0`
  installed with `--only-binary=:all: --require-hashes`, and the Workflow
  Manager `1.2.0` wheel downloaded from its release, `sha256sum -c` `OK`
  against `manager-pin.json`):
  - `actionlint` 1.7.12 on all three workflows: clean. Its first run caught
    a real defect, the plain scalar `--only-binary=:all: --require-hashes`
    (a YAML mapping), now a block scalar.
  - `tooling`: `Ran 62 tests`, `OK`.
  - `package`: `build --commit HEAD` gave the published 2.6.0 digests
    (`archive_sha256=dc86a796…9f61`, `manifest_sha256=d92517a2…fc2e`,
    `zlib_ng=2.2.5`); `package verify` `release 2.6.0, 69 files,
    verified`; bootstrap `workflow 2.6.0 (full)`, then `verify` `installation
    matches workflow 2.6.0`, both exit 0.
  - `immutability`: against the live release list (five non-draft
    releases, `v2.3.1` to `v2.6.0`), `check-pending` `ok: 2.6.0 -> 2.6.0
    (none); release source unchanged`; `check-immutable` `ok: release source
    unchanged since v2.6.0`; with `gh release download v2.6.0` (exactly the
    three assets), `check-immutable --published` `ok: the rebuilt package
    equals the published assets of v2.6.0`.
  - `installation`: `workflow-manager verify .` (Manager 1.2.0):
    `installation matches workflow 2.6.0`. In a scratch clone of HEAD,
    clean gives exit 0; one line appended to
    `.claude/commands/accept-milestone.md` gives exit 1, `modified:
    .claude/commands/accept-milestone.md`. A clone was used rather than a
    linked worktree so that the Workflow's worktree-scoped lifecycle state
    was not touched.
  - `release-source-conformance`: the fixture (`workflow v2.6.0
    conformance fixture`, one commit), all seven suites exit 0:
    `workflow_fingerprint_test.py` 242 OK, `workflow_state_test.py` 972 OK,
    `workflow_test_harness_test.py` 19 OK, `workflow_integration_test.py`
    267 OK, `workflow_acceptance_matrix_test.py` 291 OK (18 skipped),
    `workflow_state_completion_obligations_test.py` 106 OK,
    `workflow_fingerprint_generalization_test.py` 105 OK. The fixture's
    tree stayed clean.
  - `PR title`: at HEAD, `check-title "ci: CI, releases and main
    protection for the workflow repository" --agree` gives `impact=none`,
    exit 0; `feat: something` is refused (exit 1, a `none` version change
    needs a `docs/chore/ci/test/style` title).
  - **Unpinned version:** a scratch repository of HEAD's staged release
    source with `workflow_version` set to `2.99.0`, committed and built
    (`archive_sha256=7e614e9b…7c3c`): `package verify` passes;
    `--release-dir <staged> bootstrap` and `--release-dir <staged> verify`
    both exit 0; `verify` without `--release-dir` exits 1 (`release 2.99.0
    is not published: this Manager has no pin for it`), which is why the
    `package` job spells out the flag.
  - The GitHub-runner evidence (the five archive digests reproduced on a
    runner, the `v2.6.0` comparison, the three check names) is the cutover
    pull request's (plan section 7).
- **Review**: the diff adds only the two workflow files and this work
  item's narrative files. `workflow-conformance.yml`, the release source and
  the installation are unchanged; `workflow-manager verify .` is clean.

## `CP3` — Release workflow

Requirements: REQ-4.

Status: **complete**. The local verification and both live rehearsals
passed.

- **Implementation** (new): `.github/workflows/release.yml`, `Release`:
  - triggers: `workflow_run` of `Workflow CI` (`completed`, `branches:
    [main]`), with the job guarded by `event == 'push' && conclusion ==
    'success'`; and `workflow_dispatch`, on `main` only. A dispatch takes
    `main`'s tip as the trigger and first refuses unless `gh api
    repos/<repo>/actions/workflows/workflow-ci.yml/runs?head_sha=<sha>&event=push&status=success`
    reports at least one run;
  - job-level `concurrency: {group: workflow-release, cancel-in-progress:
    false}`; job `permissions: contents: write, actions: read` (the
    workflow default stays `contents: read`);
  - checks out `main` with full history and tags; installs the pinned
    deflate wheel; saves the release list with the job's write token, so
    drafts are visible; `release.py next-release --trigger <sha>` writes
    `state`, `version` and `target` to the step outputs; `release.py build
    --commit <C_V>`, refusing if the built version is not `V`;
  - `state=pending`: the pinned Manager wheel, `package verify`, then
    `--release-dir <staged C_V>` bootstrap and verify of a scratch
    repository, as in CP2; then `gh release create v<V> --target <C_V>
    --title "Workflow <V>" --notes "Workflow release <V>." --latest` with
    the three assets;
  - both states: fetch the tag `v<V>`, save the release list again, `gh
    release download v<V>`, `release.py check-published`. On
    `state=published` success, the notice is "nothing to release (v<V> read
    back intact)";
  - never `--clobber`, `gh release upload`, `gh release delete`, `git tag`,
    `git push` or a manifest change.
- **Verification** (Python 3.12.14, `zlib-ng` 1.0.0 with zlib-ng
  2.2.5, Workflow Manager 1.2.0):
  - `actionlint` 1.7.12 on `release.yml`, `workflow-ci.yml` and
    `pr-title.yml`: clean.
  - The decision and the published-path read-back, run locally against HEAD
    with the live release list: `next-release --trigger HEAD` prints
    `state=published`, `version=2.6.0`, `target=2d5b760a…`; `build --commit
    2d5b760a…` gives the published 2.6.0 digests (`archive_sha256=dc86a796…`,
    `manifest_sha256=d92517a2…`); after `gh release download v2.6.0`,
    `check-published --version 2.6.0 --target 2d5b760a…` passes: "ok: v2.6.0
    is published at 2d5b760a… with exactly its three built assets".
  - The dispatch gate's `gh api` query was not run: `workflow-ci.yml` is
    not on the remote `main` yet.
  - `workflow-manager verify .`: `installation matches workflow 2.6.0`.
- **Live rehearsals** (2026-10-01), in `RodrigoFAbreu/workflow-release-rehearsal`.
  This is a throwaway private repository the owner authorized, with release
  immutability on. It held HEAD's release source and `tools/release/`, with
  the manifest at `0.0.1`. A local driver ran the `release` job's commands
  unchanged, with `GH_REPO` pinned to that repository. The dispatch's CI gate
  was not rehearsed, because the repository has no CI. The full transcript is
  in `docs/ACTIVE_MILESTONE.md`, "CP3 rehearsal transcript".
  - Recovery (steps 1-4). A draft `v0.0.1` with one asset plus the pushed
    tag made `next-release` refuse, naming both. `gh release delete v0.0.1
    --yes --cleanup-tag` removed the draft and the tag, and both
    inspections then found nothing. The job then published `v0.0.1` and
    read it back. A rerun reported "nothing to release (v0.0.1 read back
    intact)".
  - Supersession (steps 5-7). `v0.0.2` was published without `SHA256SUMS`.
    The job's read-back and `check-immutable --published` both refused with
    "missing asset SHA256SUMS" and the supersession procedure. Neither
    reported "nothing to release". A manifest-only `fix: supersede
    incomplete release 0.0.2` commit passed `check-title --agree` (patch)
    and `check-pending`. The job published `v0.0.3` and read it back.
    `gh release view v0.0.2 --json assets,isDraft` was unchanged.
  - Not rehearsed live: the recovery branch for a tag with no release. CP1's
    fixtures cover it.
- **Review**: the diff adds `release.yml` and this work item's narrative
  files. The release source, the installation, `workflow-ci.yml` and
  `pr-title.yml` are unchanged. Nothing touched `RodrigoFAbreu/workflow`'s
  releases, tags or settings.

## `CP4` — Settings, documentation, cutover runbook

Requirements: REQ-5 (`main` protection as reviewed data, applied by the
owner), REQ-6 (`docs/RELEASING.md` and `README.md`).

- **Implementation**:
  - `.github/repository/merge-settings.json` (new): byte-identical to
    `workflow-manager`'s: squash only, `PR_TITLE`/`BLANK`, auto-merge on,
    delete branch on merge.
  - `.github/repository/ruleset-main.json` (new): `workflow-manager`'s
    ruleset with two changes: the required checks are `aggregate`,
    `Conventional Commit title` and `workflow-conformance` (`OD-W0-4`), and
    `strict_required_status_checks_policy: true` (`OD-W0-5`). No bypass
    actors.
  - `docs/RELEASING.md` (new): the two copies; how a release happens
    (D-W0-Version: the manifest bump in the release-source pull request,
    published vs. residue, the version change from `HEAD^1`); the title rule
    and agreement (D-W0-Title); the `strict` "update branch" step; what CI
    checks, including D-W0-Immutable and D-W0-Pending; the release job and
    its target (D-W0-Target); when nothing is released; fix-forward;
    "Recovering from a failed publication" (D-W0-Recovery's four steps
    verbatim, including the tag-only variant) and "Superseding an
    incomplete published release" (its five steps verbatim) with an empty
    "Superseded releases" table (version, superseded by, read-back failure,
    date); the pinned deflate runtime and a local build (D-W0-Deflate); the
    installation check and the Manager-pin bump (D-W0-Installation); the
    `workflow-manager` pin follow-up, pointing at that repository's
    "Workflow packages: adding a pin"; applying and reading back the
    settings; and W0's cutover (plan section 7) as runnable steps. The two
    section titles are the ones `release.py`'s refusals cite.
  - `README.md`: what the repository is, the two copies, the current release
    (2.6.0), links to `docs/RELEASING.md` and `docs/ROADMAP.md`.
  - `CLAUDE.md`: below the managed-block marker only, "Until W0 lands,
    `main` has no required checks" replaced with the protection, the three
    required checks and a pointer to `docs/RELEASING.md`.
- **Verification**:
  - Both JSON files parse. `merge-settings.json` equals the Manager's; in
    `ruleset-main.json` everything but the required-check list and `strict`
    equals the Manager's (compared as parsed JSON).
  - The recovery and supersession procedures in `docs/RELEASING.md` equal
    D-W0-Recovery's text (whitespace-normalized comparison against the plan),
    and their commands are the ones the CP3 rehearsals ran (`gh release view
    … --json isDraft,tagName,assets`, `git ls-remote --tags origin`, `gh
    release delete v<V> --yes --cleanup-tag`, `git push origin --delete
    refs/tags/v<V>`, the manifest-only `fix: supersede incomplete release V`
    bump).
  - The local commands `docs/RELEASING.md` gives, run at HEAD (`35019b9`) in
    a fresh Python 3.12 virtual environment with the pinned `zlib-ng` 1.0.0:
    `release_test.py` `Ran 62 tests`, `OK`; `build --commit HEAD` the
    published 2.6.0 digests (`archive_sha256=dc86a796…9f61`,
    `manifest_sha256=d92517a2…fc2e`, `zlib_ng=2.2.5`); against the live
    release list, `check-pending` `ok: 2.6.0 -> 2.6.0 (none)`,
    `check-immutable` `ok: release source unchanged since v2.6.0`,
    `next-release --trigger HEAD` `state=published`, `version=2.6.0`,
    `target=2d5b760a…`; `stage-conformance` exit 0; `check-title "feat: …"`
    `impact=minor`, and with `--agree` refused (exit 1) since the version is
    unchanged. `gh pr update-branch`, `gh workflow run --ref`, `gh pr checks
    --json` exist in the installed `gh`; the Manager's `v1.2.0` release
    carries `SHA256SUMS` and the wheel, as the pin-bump steps assume.
  - `workflow-manager verify .` with the pinned Manager 1.2.0 (wheel
    `sha256sum -c` `OK`): `installation matches workflow 2.6.0`.
  - The settings are not applied here: that is cutover step 3, the owner's.
- **Review**: the diff adds the two settings files and `docs/RELEASING.md`,
  rewrites `README.md`, changes one bullet of `CLAUDE.md`'s
  repository-owned text, and this work item's narrative files. The release
  source, the installation and the three workflows are unchanged.
