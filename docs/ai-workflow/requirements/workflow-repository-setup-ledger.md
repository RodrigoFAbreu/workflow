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
