# Active Milestone

## Milestone

W0: `workflow-repository-setup` (`process`, governing version `2.2`),
branch `milestone/workflow-repository-setup`, base `bf51137`.

## Goal

Set this repository up for development: CI over the release source, a
release workflow that publishes an immutable release when `main`'s manifest
names an unpublished version, and `main` protection with Conventional-Commit
titles. W0 itself releases nothing.

## Current checkpoint

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
`06cb6d7`); technical approval recorded in `cc20d69`. Now awaiting the
owner's functional review.

## CP3 rehearsal transcript (2026-10-01)

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

## Current blockers

None.

## Active plan

`docs/ai-workflow/WORKFLOW_REPOSITORY_SETUP_PLAN.md` (revision 6, approved;
implementation technically approved; awaiting functional review).

## Functional review checklist

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
