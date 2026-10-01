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
the transcript is below. Next: `CP4` (settings, documentation, cutover
runbook). Evidence: the requirements ledger,
`docs/ai-workflow/requirements/workflow-repository-setup-ledger.md`.

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
implementing).

## Functional review checklist

Empty. `/prepare-functional-review` writes the numbered checklist for the
active work item into this section; `/apply-functional-review` and
`/accept-milestone` read it back from here.

<!--
This file is `workflow_state.FUNCTIONAL_CHECKLIST_PATH`. It is
repository-local state: workflow-manager generates it once at bootstrap and
never overwrites it on update.
-->
