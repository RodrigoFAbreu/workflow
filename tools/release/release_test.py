#!/usr/bin/env python3
"""Tests for `package.py` and `release.py`.

Stdlib plus the pinned `zlib_ng` (`deflate-requirements.txt`). Hermetic
except for this repository's own Git history, which the reproduction tests
read: every other test builds scratch repositories, and every release list
is a fixture JSON file. Without the pinned `zlib_ng` the build tests fail;
they never skip.

    python3 tools/release/release_test.py
"""

from __future__ import annotations

import contextlib
import gzip
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import manager_block  # noqa: E402
import package  # noqa: E402
import release  # noqa: E402

#: The published packages' digests. Published bytes never change, so these
#: are constants: the uncompressed tar stream (the release source), the
#: archive (the tar stream deflated by the pinned zlib-ng) and the manifest
#: asset. They equal `workflow-manager`'s `published_releases.json` pins.
PUBLISHED = {
    "2.3.1": ("c1418a367d5801625ed557173f05c2e9b2325846765b7fbb10e4934095ec20d0",
              "1e732b957dd8cc8119d1f05b197ac96f6d9278877764cb2d9e9acdaae9f6dbd3",
              "f9e14159e0f2db11366d526d7e01d7da6de152b2034227e178b6c7768302d32e"),
    "2.4.0": ("845c2e6cf27ca63abdc17678b56f60d6140d75fca2a4d222b45a3a6db66aac2e",
              "097fb7145dd56091529aa2cf7bf0303345776fd00e11c04b0df6bfbc11f4f7d2",
              "84b6407aa2c3d70c0cfd7270c180b3ecd3286629e5273632e17c3510ddbd707a"),
    "2.5.0": ("1fdc7f10edffe285b2d153cfd50cc8c7d67ab20aca526646c4c482987b37b69d",
              "d1112f852216e5506290a46c5186d412fc0195619bbce493ede8cb32b430392f",
              "3886c7f7e62c4ef00d910fc0f66976c3d9d96d5e16a4af09e1e7a97b0c43ff19"),
    "2.5.1": ("8d4abcecfa2c97877736c4bbd2fb708c548d76fac807b9af8c6165e9731e8be2",
              "8427d895e2e6f9f77e18042128342e95d22b2469bab43a49baa3d8043f948b4e",
              "917a1b00fd699cec57eebdb34548dc96c2b258482ca13c6fcebf37a08fcb8e73"),
    "2.6.0": ("1b8a3e790dee2ffc03782c6b2138780aa041b7f59de34864026bb2bdc70ce348",
              "dc86a7965949c5da9cb7a9d8f2999b138828245aa835bf7c79887e7352e99f61",
              "d92517a27a9287b3edc40636d427a6935954f7090a2578ad055979620f84fc2e"),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_cli(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = release.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def write_release(root: Path, version: str, payload: str = "payload v1\n",
                  extra: dict[str, str] | None = None) -> None:
    """A minimal, valid release source at `root`: one payload file, one
    executable, one fixture, one template, and the manifest describing them."""
    files = {
        "payload/scripts/tool.py": (payload, True),
        "payload/docs/guide.md": ("guide\n", False),
        "fixtures/host.md": ("host evidence\n", False),
        "templates/.gitignore.workflow-fragment": (".ai-review/\n", False),
    }
    for location, text in (extra or {}).items():
        files[location] = (text, False)
    artifacts, templates = [], []
    for location, (text, executable) in files.items():
        path = root / location
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755 if executable else 0o644)
        record = {"location": location, "sha256": _sha(text.encode()), "size": len(text.encode())}
        if location.startswith("templates/"):
            templates.append(dict(record, target_path=location.removeprefix("templates/")))
        else:
            category = "host-evidence" if location.startswith("fixtures/") else "distribution"
            artifacts.append(dict(record, target_path=location.split("/", 1)[1],
                                  executable=executable, category=category))
    manifest = {"schema_version": 1, "workflow_version": version,
                "artifacts": artifacts, "templates": templates}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


class ScratchRepo:
    """A throwaway Git repository holding a release source."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")
        for key, value in (("user.email", "test@example.invalid"), ("user.name", "Test"),
                           ("commit.gpgsign", "false"), ("tag.gpgsign", "false"),
                           ("maintenance.auto", "false"), ("gc.auto", "0")):
            self.git("config", key, value)

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def release_commit(self, version: str, message: str, payload: str = "payload v1\n") -> str:
        write_release(self.root, version, payload)
        return self.commit(message)

    def touch(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def tag(self, version: str, commit: str) -> None:
        self.git("tag", f"v{version}", commit)

    def untag(self, version: str) -> None:
        self.git("tag", "-d", f"v{version}")


class ScratchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="release-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.repo = ScratchRepo(self.tmp / "repo")
        self._lists = 0

    def releases(self, *entries: tuple[str, bool]) -> str:
        """A saved `gh release list --json tagName,isDraft` file."""
        self._lists += 1
        path = self.tmp / f"releases-{self._lists}.json"
        path.write_text(json.dumps([{"tagName": f"v{v}", "isDraft": d} for v, d in entries]))
        return str(path)

    def cli(self, *argv: str) -> tuple[int, str, str]:
        return run_cli("--repo", str(self.repo.root), *argv)

    def assert_ok(self, *argv: str) -> str:
        code, out, err = self.cli(*argv)
        self.assertEqual(code, release.EXIT_OK, f"{argv} refused: {err}")
        return out

    def assert_refused(self, *argv: str, naming: tuple[str, ...] = ()) -> str:
        code, out, err = self.cli(*argv)
        self.assertEqual(code, release.EXIT_FAIL, f"{argv} was not refused: {out}{err}")
        for text in naming:
            self.assertIn(text, err)
        return err

    def outputs(self, text: str) -> dict[str, str]:
        return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)

    def build(self, commit: str, name: str) -> Path:
        out = self.tmp / name
        self.assert_ok("build", "--commit", commit, "--out", str(out))
        return out


# -- titles ------------------------------------------------------------------------


class TitleGrammarTest(unittest.TestCase):
    def test_valid_titles_and_impact(self):
        for title, impact in [("feat: add a thing", "minor"), ("fix(state): repair it", "patch"),
                              ("perf: faster", "patch"), ("refactor: tidy", "patch"),
                              ("build: pin", "patch"), ("revert: undo", "patch"),
                              ("docs: explain", "none"), ("chore: tidy", "none"),
                              ("ci: run it", "none"), ("test: cover", "none"),
                              ("style: format", "none"), ("feat!: drop", "major"),
                              ("ci(release)!: break", "major"),
                              ("fix(a.b_c/d-e): scoped", "patch"),
                              ("  docs: padded  ", "none")]:
            with self.subTest(title=title):
                self.assertEqual(release.parse_title(title).impact, impact)
                code, out, _ = run_cli("check-title", title)
                self.assertEqual(code, release.EXIT_OK)
                self.assertIn(f"impact={impact}", out)

    def test_invalid_titles_name_the_problem(self):
        for title, diagnostic in [("Add a thing", "no 'type: description' shape"),
                                  ("Feat: x", "type 'Feat' must be lowercase"),
                                  ("feature: x", "unknown type 'feature'"),
                                  ("feat(): x", "empty scope '()'"),
                                  ("feat(Scope): x", "scope 'Scope' may only contain"),
                                  ("feat:x", "no space after the colon"),
                                  ("feat:  x", "more than one space after the colon"),
                                  ("feat: ", "empty description")]:
            with self.subTest(title=title):
                with self.assertRaises(release.InvalidTitle) as caught:
                    release.parse_title(title)
                self.assertIn(diagnostic, str(caught.exception))
                code, _, err = run_cli("check-title", title)
                self.assertEqual(code, release.EXIT_FAIL)
                self.assertIn(diagnostic, err)

    def test_usage_error_exits_2(self):
        self.assertEqual(run_cli("check-title")[0], release.EXIT_USAGE)
        self.assertEqual(run_cli("no-such-command")[0], release.EXIT_USAGE)


class BumpLevelTest(unittest.TestCase):
    def test_exact_next_versions(self):
        self.assertEqual(release.bump_level("2.6.0", "2.6.0"), "none")
        self.assertEqual(release.bump_level("2.6.0", "2.6.1"), "patch")
        self.assertEqual(release.bump_level("2.6.0", "2.7.0"), "minor")
        self.assertEqual(release.bump_level("2.6.0", "3.0.0"), "major")
        self.assertEqual(release.bump_level("2.6.3", "2.7.0"), "minor")

    def test_anything_else_refused(self):
        for new in ("2.8.0", "2.7.1", "3.0.1", "2.6.0.1", "2.5.9", "1.0.0", "2.6", "v2.6.1",
                    "02.6.1", "2.6.1\n"):
            with self.subTest(new=new), self.assertRaises(release.ReleaseError):
                release.bump_level("2.6.0", new)


class TitleAgreementTest(ScratchTestCase):
    def setUp(self):
        super().setUp()
        self.base = self.repo.release_commit("2.6.0", "base")

    def agree(self, title: str) -> tuple[int, str, str]:
        return self.cli("check-title", title, "--agree")

    def test_no_bump(self):
        self.repo.touch("tools/x.py", "x\n")
        self.repo.commit("ci: tooling")
        self.assertEqual(self.agree("ci: tooling")[0], release.EXIT_OK)
        code, _, err = self.agree("feat: tooling")
        self.assertEqual(code, release.EXIT_FAIL)
        self.assertIn("2.6.0 -> 2.6.0 is none", err)

    def test_patch_bump(self):
        self.repo.release_commit("2.6.1", "fix", payload="v2\n")
        self.assertEqual(self.agree("fix: repair")[0], release.EXIT_OK)
        self.assertEqual(self.agree("ci: repair")[0], release.EXIT_FAIL)

    def test_minor_bump(self):
        self.repo.release_commit("2.7.0", "feat", payload="v2\n")
        self.assertEqual(self.agree("feat: add")[0], release.EXIT_OK)
        self.assertEqual(self.agree("fix: add")[0], release.EXIT_FAIL)

    def test_major_bump(self):
        self.repo.release_commit("3.0.0", "major", payload="v2\n")
        self.assertEqual(self.agree("feat!: break")[0], release.EXIT_OK)
        self.assertEqual(self.agree("feat: break")[0], release.EXIT_FAIL)

    def test_lower_version_refused(self):
        self.repo.release_commit("2.5.9", "down", payload="v2\n")
        _, _, err = self.agree("fix: down")
        self.assertIn("not the next patch, minor or major", err)

    def test_base_is_first_parent_not_highest_tag(self):
        # The base's 2.7.0 is pending (no tag, no release): a tooling change on
        # top of it is none-impact and needs no feat: title.
        self.repo.tag("2.6.0", self.base)
        self.repo.release_commit("2.7.0", "feat", payload="v2\n")
        self.repo.touch(".github/workflows/x.yml", "x\n")
        self.repo.commit("ci: fix release tooling")
        self.assertEqual(self.agree("ci: fix release tooling")[0], release.EXIT_OK)
        self.assertEqual(self.agree("feat: fix release tooling")[0], release.EXIT_FAIL)

    def test_root_commit_refused(self):
        _, _, err = self.cli("check-title", "ci: x", "--agree", "--head", self.base)
        self.assertIn("has no parent", err)


# -- check-pending -----------------------------------------------------------------


class CheckPendingTest(ScratchTestCase):
    def setUp(self):
        super().setUp()
        self.base = self.repo.release_commit("2.6.0", "base")

    def published_base(self) -> str:
        self.repo.tag("2.6.0", self.base)
        return self.releases(("2.6.0", False))

    def test_published_base_payload_change_with_bump(self):
        releases = self.published_base()
        self.repo.release_commit("2.7.0", "feat", payload="v2\n")
        out = self.assert_ok("check-pending", "--releases", releases)
        self.assertIn("2.6.0 -> 2.7.0 (minor)", out)

    def test_published_base_payload_change_without_bump(self):
        releases = self.published_base()
        self.repo.release_commit("2.6.0", "sneak", payload="v2\n")
        self.assert_refused("check-pending", "--releases", releases,
                            naming=("without a version change", "payload/scripts/tool.py",
                                    "manifest.json"))

    def test_published_base_invalid_bump(self):
        releases = self.published_base()
        self.repo.release_commit("2.8.0", "skip", payload="v2\n")
        self.assert_refused("check-pending", "--releases", releases,
                            naming=("not the next patch, minor or major",))

    def test_published_base_unchanged(self):
        releases = self.published_base()
        self.repo.touch("README.md", "x\n")
        self.repo.commit("docs: x")
        self.assert_ok("check-pending", "--releases", releases)

    def test_pending_base_payload_change_refused(self):
        releases = self.published_base()
        self.repo.release_commit("2.7.0", "feat", payload="v2\n")
        self.repo.release_commit("2.7.0", "more", payload="v3\n")
        self.assert_refused("check-pending", "--releases", releases,
                            naming=("version 2.7.0 is pending", "payload/scripts/tool.py"))

    def test_pending_base_further_bump_refused(self):
        releases = self.published_base()
        self.repo.release_commit("2.7.0", "feat", payload="v2\n")
        self.repo.release_commit("2.8.0", "feat again", payload="v3\n")
        self.assert_refused("check-pending", "--releases", releases,
                            naming=("version 2.7.0 is pending",))

    def test_pending_base_tooling_change_passes(self):
        releases = self.published_base()
        self.repo.release_commit("2.7.0", "feat", payload="v2\n")
        self.repo.touch("tools/release/x.py", "x\n")
        self.repo.touch(".github/workflows/release.yml", "x\n")
        self.repo.commit("ci: fix")
        out = self.assert_ok("check-pending", "--releases", releases)
        self.assertIn("release source unchanged", out)

    def test_never_published_base_is_pending(self):
        self.repo.release_commit("2.6.0", "change", payload="v2\n")
        self.assert_refused("check-pending", "--releases", self.releases(),
                            naming=("version 2.6.0 is pending",))


# -- build -------------------------------------------------------------------------


class ReproductionTest(unittest.TestCase):
    """Every published release, staged from its tag, rebuilds byte-for-byte."""

    def test_pinned_deflate_runtime(self):
        zlib_ng = package.deflate_runtime()
        self.assertEqual(zlib_ng.ZLIBNG_RUNTIME_VERSION, package.PINNED_ZLIB_NG_VERSION)

    def test_gzip_header_equals_gzipfile(self):
        buffer = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0,
                           compresslevel=9) as stream:
            stream.write(b"x" * 1000)
        self.assertEqual(buffer.getvalue()[:10], package.GZIP_HEADER)
        data = os.urandom(5000) + b"y" * 5000
        self.assertEqual(gzip.decompress(package.gzip_bytes(data)), data)

    def test_published_releases_reproduce(self):
        for version, (tar_digest, archive_digest, manifest_digest) in PUBLISHED.items():
            with self.subTest(version=version), tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                source = package.stage(REPO_ROOT, f"refs/tags/v{version}", tmp / "src")
                first = package.build(source, tmp / "one")
                second = package.build(source, tmp / "two")
                self.assertEqual(first.version, version)
                self.assertEqual(first.tar_sha256, tar_digest, "the tar stream differs")
                self.assertEqual(first.manifest_sha256, manifest_digest)
                self.assertEqual(first.archive_sha256, archive_digest,
                                 "the archive differs with the same tar stream: deflate drift")
                for name in package.asset_names(version):
                    self.assertEqual((tmp / "one" / name).read_bytes(),
                                     (tmp / "two" / name).read_bytes())
                self.assertEqual(
                    (tmp / "one" / "SHA256SUMS").read_text(),
                    f"{manifest_digest}  workflow-{version}.manifest.json\n"
                    f"{archive_digest}  workflow-{version}.tar.gz\n")

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = package.stage(REPO_ROOT, "HEAD", tmp / "src")
            built = package.build(source, tmp / "out")
            tree = package.extract_tree(built.archive, tmp / "extracted")
            self.assertEqual(tree.name, f"workflow-{built.version}")
            self.assertEqual(package.tree_listing(tree), package.tree_listing(source))
            self.assertEqual(len(package.tree_listing(tree)), built.files)

    def test_build_command_prints_the_evidence_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = run_cli("--repo", str(REPO_ROOT), "build", "--commit",
                                     "refs/tags/v2.6.0", "--out", tmp)
            self.assertEqual(code, release.EXIT_OK, err)
            tar_digest, archive_digest, manifest_digest = PUBLISHED["2.6.0"]
            for line in ("version=2.6.0", "zlib_ng=2.2.5", f"tar_sha256={tar_digest}",
                         f"archive_sha256={archive_digest}",
                         f"manifest_sha256={manifest_digest}"):
                self.assertIn(line, out.splitlines())

    def test_build_refuses_without_the_pinned_runtime(self):
        saved = sys.modules.get("zlib_ng")
        sys.modules["zlib_ng"] = None  # makes `import zlib_ng` raise ImportError
        try:
            with self.assertRaises(package.DeflateRuntimeError):
                package.gzip_bytes(b"x")
            with tempfile.TemporaryDirectory() as tmp:
                code, _, err = run_cli("--repo", str(REPO_ROOT), "build", "--commit", "HEAD",
                                       "--out", tmp)
                self.assertEqual(code, release.EXIT_FAIL)
                self.assertIn("zlib_ng is not installed", err)
                self.assertEqual(list(Path(tmp).iterdir()), [])
        finally:
            if saved is None:
                del sys.modules["zlib_ng"]
            else:
                sys.modules["zlib_ng"] = saved


class VerifyReleaseTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="verify-release-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        write_release(self.root, "1.2.3")

    def refused(self, text: str):
        with self.assertRaises(package.PackageError) as caught:
            package.verify_release(self.root)
        self.assertIn(text, str(caught.exception))

    def edit_manifest(self, change):
        manifest = json.loads((self.root / "manifest.json").read_text())
        change(manifest)
        (self.root / "manifest.json").write_text(json.dumps(manifest))

    def test_intact(self):
        self.assertEqual(package.verify_release(self.root), "1.2.3")

    def test_unlisted_file(self):
        (self.root / "payload" / "stray.txt").write_text("x")
        self.refused("untracked file in release: payload/stray.txt")

    def test_wrong_digest(self):
        (self.root / "payload/docs/guide.md").write_text("changed\n")
        self.refused("digest mismatch: payload/docs/guide.md")

    def test_missing_file(self):
        (self.root / "fixtures/host.md").unlink()
        self.refused("missing: fixtures/host.md")

    def test_executable_bit(self):
        (self.root / "payload/scripts/tool.py").chmod(0o644)
        self.refused("executable bit differs from the manifest: payload/scripts/tool.py")

    def test_dotdot_location(self):
        self.edit_manifest(lambda m: m["artifacts"][0].update(location="payload/../../x"))
        self.refused("unsafe path")

    def test_absolute_location(self):
        self.edit_manifest(lambda m: m["artifacts"][0].update(location="/etc/passwd"))
        self.refused("unsafe path")

    def test_symlink(self):
        (self.root / "payload/link").symlink_to("docs/guide.md")
        self.refused("link in release: payload/link")

    def test_listed_symlink(self):
        target = self.root / "payload/docs/guide.md"
        real = self.root.parent / f"{self.root.name}-outside.md"
        real.write_bytes(target.read_bytes())
        self.addCleanup(real.unlink)
        target.unlink()
        target.symlink_to(real)
        self.refused("link or outside the release: payload/docs/guide.md")

    def test_malformed_manifest(self):
        self.edit_manifest(lambda m: m.update(workflow_version="2.6"))
        self.refused("is not X.Y.Z")
        self.edit_manifest(lambda m: m.update(workflow_version="1.2.3", schema_version=2))
        self.refused("schema_version")

    def test_repeated_location(self):
        self.edit_manifest(lambda m: m["artifacts"].append(dict(m["artifacts"][0])))
        self.refused("twice")


class ReleaseConstantGuardTest(unittest.TestCase):
    """`build` refuses a release whose `WORKFLOW_RELEASE` is not its manifest
    version; a release without `scripts/workflow_protocol.py` is unaffected."""

    PROTOCOL = "payload/scripts/workflow_protocol.py"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="release-constant-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def release(self, version: str, protocol: str | None) -> Path:
        root = self.tmp / "release"
        write_release(root, version,
                      extra=None if protocol is None else {self.PROTOCOL: protocol})
        return root

    def refused(self, root: Path, *texts: str) -> None:
        with self.assertRaises(package.PackageError) as caught:
            package.build(root, self.tmp / "out")
        for text in texts:
            self.assertIn(text, str(caught.exception))
        self.assertFalse((self.tmp / "out").exists(), "a refused build wrote nothing")

    def test_match(self):
        root = self.release("2.7.0", '"""Protocol."""\n\nWORKFLOW_RELEASE = "2.7.0"\n')
        self.assertEqual(package.build(root, self.tmp / "out").version, "2.7.0")

    def test_mismatch_names_both(self):
        root = self.release("2.7.1", 'WORKFLOW_RELEASE = "2.7.0"\n')
        self.refused(root, self.PROTOCOL, "'2.7.0'", "'2.7.1'")

    def test_missing_or_repeated_literal(self):
        for text in ("RELEASE = '2.7.0'\n",
                     'WORKFLOW_RELEASE = "2.7.0"\nWORKFLOW_RELEASE = "2.7.0"\n'):
            with self.subTest(text=text):
                shutil.rmtree(self.tmp / "release", ignore_errors=True)
                self.refused(self.release("2.7.0", text), "exactly once")

    def test_absent_before_2_7_0(self):
        self.assertEqual(package.build(self.release("2.6.0", None), self.tmp / "out").version,
                         "2.6.0")
        for version in PUBLISHED:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as tmp:
                source = package.stage(REPO_ROOT, f"refs/tags/v{version}", Path(tmp) / "src")
                targets = {record["target_path"] for record in
                           package.manifest_records(package.load_manifest(source)).values()}
                self.assertNotIn(package.RELEASE_CONSTANT_TARGET, targets)
                package.check_release_constant(source)

    def test_head_states_its_manifest_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = package.stage(REPO_ROOT, "HEAD", Path(tmp) / "src")
            package.check_release_constant(source)


# -- next-release ------------------------------------------------------------------



class ConformanceFixtureTest(unittest.TestCase):
    def test_places_only_the_managers_state_templates(self):
        tmp = Path(tempfile.mkdtemp(prefix="conformance-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        write_release(tmp / "release", "1.2.3", extra={
            "templates/docs/ai-workflow/WORKFLOW_STATE.json": "{}\n",
            "templates/docs/ai-workflow/WORKFLOW_CONFIG.json": "{}\n",
            "templates/docs/ai-workflow/FUTURE_TEMPLATE.md": "future\n",
            "templates/docs/ACTIVE_MILESTONE.md": "active\n",
        })
        fixture = package.stage_conformance(tmp / "release", tmp / "fixture")
        files = subprocess.run(["git", "-C", str(fixture), "ls-files"], check=True,
                               capture_output=True, text=True).stdout.split()
        self.assertEqual(sorted(files), [
            ".gitignore", "docs/ai-workflow/WORKFLOW_CONFIG.json",
            "docs/ai-workflow/WORKFLOW_STATE.json", "docs/guide.md", "host.md",
            "scripts/tool.py"])


class ConformanceTemplate(unittest.TestCase):
    """The managed conformance job (D-Conformance-Job): concurrency, parallel step."""

    GROUP = ("workflow-conformance-${{ github.event_name == 'pull_request' && github.ref "
             "|| format('{0}-{1}', github.run_id, github.run_attempt) }}")
    CANCEL = "${{ github.event_name == 'pull_request' }}"

    @classmethod
    def setUpClass(cls):
        cls.text = (REPO_ROOT / "templates/.github/workflows/workflow-conformance.yml").read_text()

    def step_body(self):
        lines = self.text.splitlines()
        start = lines.index("        run: |") + 1
        return "\n".join(l[10:] for l in lines[start:]) + "\n"

    def suites(self):
        for line in self.step_body().splitlines():
            if line.startswith("suites="):
                return line[len("suites="):].strip('"').split()
        self.fail("no suites= line")

    @staticmethod
    def evaluate(expr, ctx):
        """The constructs the expressions use: ==, &&, ||, format, github.*, literals."""
        import re

        def atom(t):
            t = t.strip()
            if t.startswith("'"):
                return t[1:-1]
            if t.startswith("github."):
                return ctx[t[7:]]
            m = re.fullmatch(r"format\('([^']*)',(.*)\)", t)
            if m:
                args = [atom(a) for a in m.group(2).split(",")]
                return re.sub(r"\{(\d)\}", lambda g: str(args[int(g.group(1))]), m.group(1))
            raise AssertionError(f"unsupported expression {t!r}")

        def eq(t):
            if "==" in t:
                a, b = t.split("==")
                return atom(a) == atom(b)
            return atom(t)

        def conj(t):
            parts = t.split("&&")
            for p in parts[:-1]:
                if not eq(p):
                    return False
            return eq(parts[-1])

        # "||" only separates the and-expression from the fallback atom here.
        left, sep, right = expr.partition("||")
        value = conj(left)
        return value if value or not sep else atom(right)

    def inner(self, line):
        self.assertTrue(line.startswith("${{ ") or "${{ " in line)
        return line[line.index("${{ ") + 4:line.rindex(" }}")]

    def group_for(self, **ctx):
        prefix = "workflow-conformance-"
        expr = self.inner(self.GROUP)
        return prefix + str(self.evaluate(expr, ctx))

    def test_one_job_without_a_name(self):
        jobs = self.text.split("\njobs:\n", 1)[1]
        ids = [l for l in jobs.splitlines() if l.startswith("  ") and not l.startswith("   ")]
        self.assertEqual(ids, ["  workflow-conformance:"])
        self.assertNotIn("\n    name:", jobs)

    def test_concurrency_expressions_are_exact(self):
        self.assertIn("\nconcurrency:\n  group: " + self.GROUP + "\n  cancel-in-progress: "
                      + self.CANCEL + "\n", self.text)

    def test_group_semantics(self):
        push = dict(event_name="push", ref="refs/heads/main")
        a = self.group_for(run_id="1", run_attempt="1", **push)
        b = self.group_for(run_id="2", run_attempt="1", **push)
        c = self.group_for(run_id="1", run_attempt="2", **push)
        self.assertEqual(len({a, b, c}), 3)
        pr = dict(event_name="pull_request", ref="refs/pull/7/merge", run_attempt="1")
        self.assertEqual(self.group_for(run_id="1", **pr), self.group_for(run_id="9", **pr))
        self.assertNotIn(self.group_for(run_id="1", **pr), {a, b, c})
        cancel = self.inner(self.CANCEL)
        self.assertTrue(self.evaluate(cancel, dict(event_name="pull_request")))
        self.assertFalse(self.evaluate(cancel, dict(event_name="push")))

    def test_suite_list_is_the_shipped_conformance_suites(self):
        manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        shipped = sorted(
            Path(a["target_path"]).name for a in manifest["artifacts"]
            if a["target_path"].startswith("scripts/workflow_")
            and a["target_path"].endswith("_test.py")
            and not a["target_path"].endswith("_demo_test.py"))
        self.assertEqual(sorted(self.suites()), shipped)
        self.assertEqual(len(self.suites()), 9)

    @staticmethod
    def with_constants(body, width_cap=4, shards=0, longest=None):
        """The kit's textual substitution: only the two constant lines change (and, for a
        test of the fallback order, the `longest=` list)."""
        for name, value in (("width_cap", width_cap), ("shards", shards)):
            line = f"\n{name}="
            assert body.count(line) == 1, name
            start = body.index(line) + len(line)
            end = body.index("\n", start)
            body = body[:start] + str(value) + body[end:]
        if longest is not None:
            line = "\nlongest="
            assert body.count(line) == 1
            start = body.index(line) + len(line)
            end = body.index("\n", start)
            body = body[:start] + '"' + longest + '"' + body[end:]
        return body

    ACCEPTANCE = "workflow_acceptance_matrix_test.py"

    # The suites that `longest` starts first when the shard names do not match the run
    # (shards=2 here): the suites among the nine that `longest` lists, in its order.
    LONGEST_SUITES = ["workflow_protocol_test.py", "workflow_state_test.py",
                      "workflow_gate_policy_test.py",
                      "workflow_fingerprint_generalization_test.py"]

    # Median seconds per unit over the twelve green runs of the managed job, 2026-10-14 to
    # 2026-10-21 (the per-run timings were a scratch artifact; this table is the record).
    MEASURED = {
        "workflow_protocol_test.py": 645, "workflow_state_test.py": 486,
        "acceptance-1of4": 463.5, "acceptance-2of4": 405, "acceptance-3of4": 420.5,
        "acceptance-4of4": 439, "workflow_gate_policy_test.py": 335,
        "workflow_fingerprint_generalization_test.py": 218,
        "workflow_state_completion_obligations_test.py": 39, "workflow_integration_test.py": 15,
        "workflow_fingerprint_test.py": 13, "workflow_test_harness_test.py": 5}

    @staticmethod
    def makespan(order, durations, width=4):
        """Greedy list scheduling: each unit starts on the earliest-free slot, as the queue does."""
        free = [0.0] * width
        for unit in order:
            slot = free.index(min(free))
            free[slot] += durations[unit]
        return max(free)

    def longest_names(self):
        for line in self.step_body().splitlines():
            if line.startswith("longest="):
                return line[len("longest="):].strip('"').split()
        self.fail("no longest= line")

    STANDIN_ACCEPTANCE = (
        "import os, pathlib, time, unittest\n"
        "C = pathlib.Path(@COUNTER@)\n"
        "def work(case):\n"
        "    name = case.id()\n"
        "    (C / name).write_text('')\n"
        "    time.sleep(0.3)\n"
        "    running = len([p for p in C.iterdir() if not p.name.startswith('peak-')])\n"
        "    (C / ('peak-' + name)).write_text(str(running))\n"
        "    (C / name).unlink()\n"
        "    pathlib.Path('..', 'MARKER-' + name).write_text(name)\n"
        "    pathlib.Path(os.environ['TMPDIR'], 'T-' + name).write_text(name)\n"
        "    pathlib.Path(os.environ['HOME'], 'H-' + name).write_text(name)\n"
        "class First(unittest.TestCase):\n"
        "    def test_one(self): work(self)\n"
        "    def test_two(self): work(self)\n"
        "class Second(unittest.TestCase):\n"
        "    def test_one(self): work(self)\n"
        "    def test_two(self): work(self)\n"
        "class Third(unittest.TestCase):\n"
        "    def test_one(self): work(self)\n"
        "class Fourth(unittest.TestCase):\n"
        "    def test_one(self): work(self)\n"
        "    def test_fails(self):\n"
        "        work(self)\n"
        "        self.assertTrue(@FAIL@)\n")

    def run_body(self, fail=(), uncopyable=False, shards=0, width_cap=4, failing_test=False,
                 acceptance_extra="", check_stub="", longest=None):
        tmp = Path(tempfile.mkdtemp(prefix="conformance-job-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        ws, runner, counter = tmp / "ws", tmp / "runner", tmp / "counter"
        (ws / "scripts").mkdir(parents=True)
        counter.mkdir()
        (ws / "MARKER").write_text("original\n")
        if uncopyable:
            (ws / "UNREADABLE").write_text("x\n")
            (ws / "UNREADABLE").chmod(0)
        for name in self.suites():
            if shards and name == self.ACCEPTANCE:
                (ws / "scripts" / name).write_text(
                    self.STANDIN_ACCEPTANCE.replace("@COUNTER@", repr(str(counter)))
                    .replace("@FAIL@", "False" if failing_test else "True") + acceptance_extra)
                continue
            (ws / "scripts" / name).write_text(
                "import os, sys, time, pathlib\n"
                f"name = {name!r}\n"
                f"c = pathlib.Path({str(counter)!r})\n"
                "(c / name).write_text('')\n"
                "time.sleep(0.4)\n"
                "running = len([p for p in c.iterdir() if not p.name.startswith('peak-')])\n"
                "(c / ('peak-' + name)).write_text(str(running))\n"
                "(c / name).unlink()\n"
                "pathlib.Path('..', 'MARKER-' + name).write_text(name)\n"
                "pathlib.Path(os.environ['TMPDIR'], 'T-' + name).write_text(name)\n"
                "pathlib.Path(os.environ['HOME'], 'H-' + name).write_text(name)\n"
                f"print('output of ' + name)\n"
                f"sys.exit({1 if name in fail else 0})\n")
        runner.mkdir()
        summary = tmp / "summary.md"
        env = dict(os.environ, GITHUB_WORKSPACE=str(ws), RUNNER_TEMP=str(runner),
                   GITHUB_STEP_SUMMARY=str(summary))
        body = self.with_constants(self.step_body(), width_cap, shards, longest)
        if check_stub:
            body = self.stub_check(check_stub) + body
        proc = subprocess.run(["bash", "-eo", "pipefail", "-c", body],
                              env=env, capture_output=True, text=True, cwd=tmp)
        return proc, ws, runner, counter, summary.read_text() if summary.exists() else ""

    @staticmethod
    def stub_check(output, rc=1):
        """A shell function standing in for `shards.py check`: prints `output`, exits `rc`."""
        if isinstance(output, tuple):
            output, rc = output
        return ("python3() { if [ \"$2\" = check ]; then printf '%s' " + shlex.quote(output)
                + f"; return {rc}; fi; command python3 \"$@\"; }}\n")

    def assert_check_verdict_fails_the_job(self, run_body):
        # `check` dies after its total row, or exits non-zero after reporting ok: the exit
        # status is the tool's own verdict and must fail the job whatever rows follow.
        for output, rows in (("total\t7\t0\t2\t0\tbad\n", ("FAILED (see the shard rows)",
                                                            "FAILED (the shard check exited 1)")),
                             ("total\t7\t7\t2\t0\tok\n", ("FAILED (the shard check exited 1)",))):
            with self.subTest(output=output):
                proc, ws, runner, counter, summary = run_body(shards=2, check_stub=output)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("suite(s) failed", proc.stdout)
                for row in rows:
                    self.assertIn("| " + row + " |", summary)
                self.assertNotIn("did not run", summary + proc.stdout)

    def test_sharded_step_fails_when_the_check_verdict_is_bad_without_any_shard_row(self):
        self.assert_check_verdict_fails_the_job(self.run_body)

    def assert_bad_total_with_exit_zero_is_worded_as_the_total(self, run_body):
        proc, ws, runner, counter, summary = run_body(
            shards=2, check_stub=("total\t7\t0\t2\t0\tbad\n", 0))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("::error title=acceptance check failed::the acceptance coverage total is "
                      "not ok, though the shard check exited 0", proc.stdout)
        self.assertIn("| FAILED (the coverage total is not ok) |", summary)
        self.assertNotIn("without a failing shard row", proc.stdout)
        self.assertNotIn("exited 0)", summary)

    def test_sharded_step_words_a_bad_total_with_exit_zero_as_the_total(self):
        self.assert_bad_total_with_exit_zero_is_worded_as_the_total(self.run_body)

    def assert_a_failed_copy_is_in_the_units_log(self, run_body):
        proc, ws, runner, counter, summary = run_body(uncopyable=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        # The failure report echoes the unit's log, which now holds the copy's own error.
        report = proc.stdout.split("::error title=", 1)[1]
        self.assertIn("UNREADABLE", report)
        self.assertIn("Permission denied", report)

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-0 file, so the copy cannot fail")
    def test_a_failed_copy_is_in_the_units_log(self):
        self.assert_a_failed_copy_is_in_the_units_log(self.run_body)

    def test_step_body_all_pass(self):
        proc, ws, runner, counter, summary = self.run_body()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for name in self.suites():
            self.assertIn(f"::group::{name} passed in", proc.stdout)
            self.assertIn(f"| {name} | passed |", summary)
        self.assertNotIn("::error", proc.stdout)

    def test_step_body_failure_runs_everything_and_unfolds_the_failure(self):
        bad = "workflow_state_test.py"
        proc, ws, runner, counter, summary = self.run_body(fail=(bad,))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        out = proc.stdout
        self.assertIn(f"::error title={bad} failed::exit 1 after", out)
        after = out.split(f"::error title={bad} failed::", 1)[1].splitlines()
        self.assertEqual(after[1], f"output of {bad}")
        self.assertNotIn(f"::group::{bad}", out)
        for name in self.suites():
            self.assertTrue((runner / "workflow-conformance" / name / "result").exists())
            if name != bad:
                self.assertIn(f"::group::{name} passed in", out)
        self.assertIn("1 suite(s) failed", out)
        self.assertEqual(summary.count("\n| workflow_"), 9)

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-0 file, so the copy cannot fail")
    def test_step_body_reports_every_suite_whose_setup_failed(self):
        # Under Actions' `bash -eo pipefail`, a suite whose copy fails exits
        # before writing its result; the throttle's `wait -n` must not end
        # the step there, so every suite is still reported, logs and summary.
        proc, ws, runner, counter, summary = self.run_body(uncopyable=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        for name in self.suites():
            self.assertIn(f"::error title={name} failed::exit missing after", proc.stdout)
        self.assertIn("9 suite(s) failed", proc.stdout)
        self.assertEqual(summary.count("\n| workflow_"), 9)

    def test_step_body_is_parallel_and_isolated(self):
        proc, ws, runner, counter, _ = self.run_body()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        peaks = [int((counter / f"peak-{n}").read_text()) for n in self.suites()]
        self.assertLessEqual(max(peaks), 4)
        self.assertGreater(max(peaks), 1)
        self.assertEqual(sorted(p.name for p in ws.iterdir()), ["MARKER", "scripts"])
        self.assertEqual(sorted(p.name for p in (ws / "scripts").iterdir()),
                         sorted(self.suites()))
        for name in self.suites():
            d = runner / "workflow-conformance" / name
            self.assertEqual([p.name for p in (d / "tmp").iterdir()], [f"T-{name}"])
            self.assertEqual([p.name for p in (d / "home").iterdir()], [f"H-{name}"])
            markers = sorted(p.name for p in d.joinpath("repo").glob("MARKER*"))
            self.assertEqual(markers, ["MARKER", f"MARKER-{name}"])


    # ---- the candidate scheduling: constants, the shard tool, the sharded step ----

    def test_each_constant_is_alone_on_one_line_and_substituting_changes_only_it(self):
        body = self.step_body()
        for line in ("width_cap=4", "shards=4"):
            self.assertEqual(body.splitlines().count(line), 1, line)
            self.assertEqual(body.count("\n" + line + "\n"), 1, line)
        out = self.with_constants(body, width_cap=2, shards=8)
        changed = [(a, b) for a, b in zip(body.splitlines(), out.splitlines()) if a != b]
        self.assertEqual(changed, [("width_cap=4", "width_cap=2"), ("shards=4", "shards=8")])
        self.assertEqual(len(body.splitlines()), len(out.splitlines()))
        proc = subprocess.run(["bash", "-n"], input=out, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.with_constants(body, 4, 4), body)

    def test_constants_are_the_outcome_the_evidence_selects(self):
        """CP2: the shipped constants are the measured outcome O1 (width 4, 4 shards)."""
        body = self.step_body()
        self.assertEqual(self.with_constants(body, 4, 4), body)
        evidence = (REPO_ROOT / "docs/ai-workflow/CONFORMANCE_SHARDING_EVIDENCE.md").read_text()
        self.assertIn("**Outcome O1: sharding is adopted. `width_cap` = 4, `shards` = 4 (variant v3).**",
                      evidence)
        self.assertIn('"outcome": "O1", "shards": 4, "undecided_not_chosen": ["v4", "v5"], '
                      '"variant": "v3", "width_cap": 4}', evidence)

    def shards_source(self):
        body = self.step_body()
        start = body.index("<<'PY'\n") + len("<<'PY'\n")
        return body[start:body.index("\nPY\n", start) + 1]

    def test_the_suites_line_and_the_concurrency_block_are_untouched(self):
        self.assertEqual(self.text.count('suites="'), 1)
        self.assertEqual(len(self.suites()), 9)
        self.assertIn("\nconcurrency:\n  group: " + self.GROUP + "\n  cancel-in-progress: "
                      + self.CANCEL + "\n", self.text)

    STANDIN_MODULE = (
        "import unittest\n"
        "class Base(unittest.TestCase):\n"
        "    def test_inherited(self): pass\n"
        "class SubA(Base):\n"
        "    def test_a1(self): pass\n"
        "    def test_a2(self): pass\n"
        "class SubB(Base):\n"
        "    def test_b(self): pass\n"
        "@unittest.skip('whole class')\n"
        "class Decorated(unittest.TestCase):\n"
        "    def test_d1(self): pass\n"
        "    def test_d2(self): pass\n"
        "class Skipper(unittest.TestCase):\n"
        "    def test_skips(self): self.skipTest('reason')\n"
        "    @unittest.expectedFailure\n"
        "    def test_expected(self): self.fail('expected')\n"
        "class Subtests(unittest.TestCase):\n"
        "    def test_passing(self):\n"
        "        for i in range(2):\n"
        "            with self.subTest(i=i): pass\n"
        "    def test_skipped_subtest(self):\n"
        "        with self.subTest(i=1): self.skipTest('sub')\n"
        "class Empty(unittest.TestCase): pass\n")

    VARIANTS = {
        "failing test": (
            "class Failing(unittest.TestCase):\n    def test_fails(self): self.fail('no')\n"
            "    def test_ok(self): pass\n", ["failed: standin_mod.Failing.test_fails"]),
        "failing subtest": (
            "class SubFail(unittest.TestCase):\n    def test_sub(self):\n"
            "        for i in range(2):\n            with self.subTest(i=i): self.assertEqual(i, 0)\n",
            ["failed: standin_mod.SubFail.test_sub"]),
        "setUpClass error": (
            "class SetupError(unittest.TestCase):\n    @classmethod\n"
            "    def setUpClass(cls): raise RuntimeError('boom')\n    def test_s(self): pass\n",
            ["failed: setUpClass (standin_mod.SetupError)",
             "missing: standin_mod.SetupError.test_s"]),
        "setUpClass SkipTest": (
            "class SetupSkip(unittest.TestCase):\n    @classmethod\n"
            "    def setUpClass(cls): raise unittest.SkipTest('no')\n    def test_s(self): pass\n",
            ["not in the plan: setUpClass (standin_mod.SetupSkip)",
             "missing: standin_mod.SetupSkip.test_s"]),
        "unexpected success": (
            "class Unexpected(unittest.TestCase):\n    @unittest.expectedFailure\n"
            "    def test_u(self): pass\n", ["failed: standin_mod.Unexpected.test_u"]),
    }

    class ShardFlow:
        """plan -> run every shard -> check, with the heredoc's real Python text."""

        def __init__(self, case, extra="", shards=3, module_source=None):
            self.case = case
            self.tmp = Path(tempfile.mkdtemp(prefix="shard-flow-"))
            case.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
            self.scripts, self.base = self.tmp / "scripts", self.tmp / "base"
            self.scripts.mkdir()
            self.base.mkdir()
            (self.scripts / "standin_mod.py").write_text(
                module_source if module_source is not None else case.STANDIN_MODULE + extra)
            (self.base / "shards.py").write_text(case.shards_source())
            self.shards = shards
            self.plan_path = self.base / "plan.json"

        def tool(self, *args, cwd=None):
            return subprocess.run([sys.executable, str(self.base / "shards.py"), *args],
                                  cwd=cwd or self.scripts, capture_output=True, text=True)

        def plan(self, directory=".", module="standin_mod.py", out=None):
            return self.tool("plan", "--dir", str(directory), "--module", module, "--shards",
                             str(self.shards), "--out", str(out or self.plan_path))

        def spec(self):
            return json.loads(self.plan_path.read_text())

        def run_all(self, status=None):
            for shard in self.spec()["shards"]:
                folder = self.base / shard["unit"]
                folder.mkdir()
                proc = self.tool("run", "--plan", str(self.plan_path), "--unit", shard["unit"],
                                 "--out", str(folder / "shard.json"))
                (folder / "result").write_text(
                    f"{proc.returncode if status is None else status} 1\n")

        def check(self):
            proc = self.tool("check", "--plan", str(self.plan_path), "--base", str(self.base))
            rows = [line.split("\t") for line in proc.stdout.splitlines() if line]
            return proc, rows

        def shard_file(self, index):
            return self.base / self.spec()["shards"][index]["unit"] / "shard.json"

        def done(self):
            proc = self.plan()
            self.case.assertEqual(proc.returncode, 0, proc.stderr)
            self.run_all()
            return self.check()

    def test_shard_tool_passes_a_complete_run_and_records_every_outcome(self):
        flow = self.ShardFlow(self)
        proc, rows = flow.done()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        expected = flow.spec()["expected"]
        self.assertEqual(rows[0], ["total", str(len(expected)), str(len(expected)), "3",
                                   "1", "ok"])
        self.assertTrue(all(r[0] == "shard" and r[4] == "ok" for r in rows[1:]), rows)
        outcomes = {}
        for index in range(3):
            outcomes.update(json.loads(flow.shard_file(index).read_text())["outcomes"])
        self.assertEqual(sorted(outcomes), sorted(expected))
        for name in ("Decorated.test_d1", "Decorated.test_d2", "Skipper.test_skips",
                     "Subtests.test_skipped_subtest"):
            self.assertEqual(outcomes["standin_mod." + name], "skip", name)
        self.assertEqual(outcomes["standin_mod.Skipper.test_expected"], "xfail")
        self.assertEqual(outcomes["standin_mod.Subtests.test_passing"], "ok")
        for owner in ("Base", "SubA", "SubB"):
            self.assertEqual(outcomes[f"standin_mod.{owner}.test_inherited"], "ok", owner)

    def test_shard_partition_is_exact_deterministic_and_balanced(self):
        flow = self.ShardFlow(self, shards=2)
        self.assertEqual(flow.plan().returncode, 0)
        first = flow.plan_path.read_bytes()
        again = flow.base / "again.json"
        self.assertEqual(flow.plan(out=again).returncode, 0)
        self.assertEqual(first, again.read_bytes())
        spec = flow.spec()
        baseline = json.loads(subprocess.run(
            [sys.executable, "-B", "-c",
             "import json, unittest, standin_mod\n"
             "def flat(s):\n"
             "    for t in s:\n"
             "        yield from (flat(t) if isinstance(t, unittest.TestSuite) else [t])\n"
             "print(json.dumps([t.id() for t in flat(unittest.TestLoader()"
             ".loadTestsFromModule(standin_mod))]))"],
            cwd=flow.scripts, capture_output=True, text=True, check=True).stdout)
        self.assertEqual(spec["expected"], baseline)
        self.assertEqual(sorted(i for s in spec["shards"] for i in s["ids"]), sorted(baseline))
        classes = [c for s in spec["shards"] for c in s["classes"]]
        self.assertEqual(sorted(classes), sorted(set(classes)))
        self.assertNotIn("Empty", classes)
        sizes = [len(s["ids"]) for s in spec["shards"]]
        self.assertLessEqual(max(sizes) - min(sizes), 3)
        for shard in spec["shards"]:
            for test_id in shard["ids"]:
                self.assertIn(test_id.split(".")[1], shard["classes"])
        self.assertEqual([s["unit"] for s in spec["shards"]], ["acceptance-1of2", "acceptance-2of2"])
        many = self.ShardFlow(self, shards=50)
        self.assertEqual(many.plan().stdout.strip(), str(len(set(classes))))

    def test_shard_plan_refuses_module_hooks(self):
        for hook in ("def load_tests(loader, tests, pattern):\n    return tests\n",
                     "def setUpModule():\n    pass\n", "def tearDownModule():\n    pass\n"):
            name = hook.split("(")[0].split()[-1]
            with self.subTest(hook=name):
                flow = self.ShardFlow(self, extra=hook)
                proc = flow.plan()
                self.assertEqual(proc.returncode, 1)
                self.assertIn(name, proc.stderr)
                self.assertFalse(flow.plan_path.exists())

    def test_shard_check_fails_naming_the_shard_and_the_original_ids(self):
        for label, (extra, expected) in self.VARIANTS.items():
            with self.subTest(label):
                flow = self.ShardFlow(self, extra=extra)
                proc, rows = flow.done()
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertEqual(rows[0][-1], "bad")
                bad = [r for r in rows if r[0] == "shard" and r[4] == "bad"]
                self.assertTrue(bad, rows)
                text = " | ".join(r[5] for r in bad)
                for piece in expected:
                    self.assertIn(piece, text)
                for row in bad:
                    self.assertRegex(row[2], r"^acceptance \d/3$")
                    self.assertTrue(row[5].startswith(row[2] + " (classes "), row[5])

    def corrupt(self, label, change, expect):
        flow = self.ShardFlow(self)
        self.assertEqual(flow.plan().returncode, 0)
        flow.run_all()
        change(flow)
        proc, rows = flow.check()
        self.assertEqual(proc.returncode, 1, label)
        bad = [r for r in rows if r[0] == "shard" and r[4] == "bad"]
        self.assertEqual(len(bad), 1, (label, rows))
        self.assertIn(expect, bad[0][5], label)
        self.assertTrue(bad[0][5].startswith(bad[0][2] + " (classes "), label)

    def test_shard_check_rejects_every_incomplete_or_inconsistent_shard_file(self):
        def edit(index, mutate):
            def go(flow):
                path = flow.shard_file(index)
                data = json.loads(path.read_text())
                mutate(data, flow)
                path.write_text(json.dumps(data))
            return go

        def duplicate(data, flow):
            other = json.loads(flow.shard_file(1).read_text())["outcomes"]
            data["outcomes"][next(iter(other))] = "ok"

        def drop(data, flow):
            data["outcomes"].pop(next(iter(data["outcomes"])))

        cases = {
            "missing file": (lambda f: f.shard_file(0).unlink(), "no complete shard file"),
            "truncated file": (lambda f: f.shard_file(0).write_text(
                f.shard_file(0).read_text()[:40]), "no complete shard file"),
            "not completed": (edit(0, lambda d, f: d.update(completed=False)),
                              "no complete shard file"),
            "another shard's class list": (edit(0, lambda d, f: d.update(classes=["Other"])),
                                           "no complete shard file"),
            "no result": (lambda f: (f.base / f.spec()["shards"][0]["unit"] / "result").unlink(),
                          "did not finish"),
            "duplicated id": (edit(0, duplicate), "not in the plan: standin_mod."),
            "extra id": (edit(0, lambda d, f: d["outcomes"].update(
                {"standin_mod.Ghost.test_x": "ok"})), "not in the plan: standin_mod.Ghost.test_x"),
            "a planned id started twice": (edit(0, lambda d, f: d["started"].append(
                next(iter(d["outcomes"])))), "executed more than once: standin_mod."),
            "missing id": (edit(0, drop), "missing: standin_mod."),
            "started and never finished": (edit(0, lambda d, f: d["started"].append(
                "standin_mod.Ghost.test_y")), "started and never finished: standin_mod.Ghost.test_y"),
            "a failed outcome under a zero exit": (edit(0, lambda d, f: d["outcomes"].update(
                {d["classes"] and next(iter(d["outcomes"])): "unexpected_success"})), "failed: "),
            "a nonzero exit": (lambda f: (f.base / f.spec()["shards"][0]["unit"] / "result")
                               .write_text("3 1\n"), "exit 3"),
        }
        for label, (change, expect) in cases.items():
            with self.subTest(label):
                self.corrupt(label, change, expect)

    def test_shard_check_rejects_a_test_executed_twice_within_one_shard(self):
        twice = ("class Twice(unittest.TestCase):\n"
                 "    def run(self, result=None):\n"
                 "        super().run(result)\n"
                 "        return super().run(result)\n"
                 "    def test_t(self): pass\n")
        flow = self.ShardFlow(self, extra=twice)
        proc, rows = flow.done()
        self.assertEqual(proc.returncode, 1, proc.stdout)
        bad = [r for r in rows if r[0] == "shard" and r[4] == "bad"]
        self.assertEqual(len(bad), 1, rows)
        self.assertIn("executed more than once: standin_mod.Twice.test_t", bad[0][5])

    def test_real_acceptance_module_partitions_exactly(self):
        scripts = REPO_ROOT / "payload/scripts"
        manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        counted = manifest["manager"]["conformance"]["suites"][self.ACCEPTANCE]
        probe = subprocess.run(
            [sys.executable, "-B", "-c",
             "import json, unittest, workflow_acceptance_matrix_test as m\n"
             "def flat(s):\n"
             "    for t in s:\n"
             "        yield from (flat(t) if isinstance(t, unittest.TestSuite) else [t])\n"
             "ids = [t.id() for t in flat(unittest.TestLoader().loadTestsFromModule(m))]\n"
             "inherited = sorted({type(t).__name__ for t in flat(unittest.TestLoader()"
             ".loadTestsFromModule(m)) if t._testMethodName not in type(t).__dict__})\n"
             "print(json.dumps([ids, inherited]))"],
            cwd=scripts, capture_output=True, text=True, check=True)
        ids, inherited = json.loads(probe.stdout)
        self.assertEqual(len(ids), counted)
        self.assertTrue(inherited, "the module has classes that run inherited tests")
        for count in (1, 2, 4, 8):
            with self.subTest(shards=count):
                flow = self.ShardFlow(self, shards=count, module_source="")
                proc = flow.plan(directory=scripts, module=self.ACCEPTANCE)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                spec = flow.spec()
                self.assertEqual(int(proc.stdout), len(spec["shards"]))
                self.assertEqual(sorted(i for s in spec["shards"] for i in s["ids"]), sorted(ids))
                self.assertEqual(spec["expected"], ids)
                classes = [c for s in spec["shards"] for c in s["classes"]]
                self.assertEqual(len(classes), len(set(classes)))
                for shard in spec["shards"]:
                    for test_id in shard["ids"]:
                        self.assertIn(test_id.split(".")[1], shard["classes"])
                for name in inherited:
                    owners = [s for s in spec["shards"] if name in s["classes"]]
                    self.assertEqual(len(owners), 1, name)
                    self.assertTrue(any(i.split(".")[1] == name for i in owners[0]["ids"]))

    def peaks(self, counter):
        return [int(p.read_text()) for p in counter.iterdir() if p.name.startswith("peak-")]

    @staticmethod
    def started(out):
        return [(m.group(1), int(m.group(2))) for m in
                re.finditer(r"^start (\S+) running (\d+)$", out, re.M)]

    def test_sharded_step_all_pass_reports_nine_rows_and_the_coverage(self):
        proc, ws, runner, counter, summary = self.run_body(shards=2)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(summary.count("\n| workflow_"), 9)
        self.assertIn("| workflow_acceptance_matrix_test.py | passed (2 shards, 7 tests) |",
                      summary)
        self.assertIn("coverage: expected 7, recorded 7", proc.stdout)
        for i in (1, 2):
            self.assertIn(f"| acceptance {i}/2 | passed |", summary)
            self.assertIn(f"::group::acceptance {i}/2 passed in", proc.stdout)
        order = [l.split("|")[1].strip() for l in summary.splitlines()[2:]]
        self.assertEqual(order[0], self.ACCEPTANCE)
        self.assertEqual(order[1:3], ["acceptance 1/2", "acceptance 2/2"])
        self.assertNotIn("::error", proc.stdout)
        units = [u for u, _ in self.started(proc.stdout)]
        self.assertEqual(units[:4], self.LONGEST_SUITES)
        self.assertEqual(sorted(units[4:6]), ["acceptance-1of2", "acceptance-2of2"])
        self.assertEqual(len(units), 2 + 8)
        self.assertNotIn(self.ACCEPTANCE, units)

    def test_sharded_step_fails_for_each_of_the_nine_suites_in_turn(self):
        for name in self.suites():
            with self.subTest(name):
                if name == self.ACCEPTANCE:
                    proc, *_, summary = self.run_body(shards=2, failing_test=True)
                    self.assertRegex(proc.stdout,
                                     r"::error title=acceptance \d/2 failed::acceptance \d/2 "
                                     r"\(classes [^)]*\): exit 1; failed: [^\n]*Fourth\.test_fails")
                    self.assertIn("workflow_acceptance_matrix_test.py | FAILED (see the shard "
                                  "rows) |", summary)
                else:
                    proc, *_, summary = self.run_body(shards=2, fail=(name,))
                    self.assertIn(f"::error title={name} failed::exit 1 after", proc.stdout)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("1 suite(s) failed", proc.stdout)
                self.assertEqual(summary.count("\n| workflow_"), 9)
                self.assertEqual(proc.stdout.count("::group::"), 2 + 8 - 1)

    def test_sharded_step_failing_shard_unfolds_its_log_and_runs_everything(self):
        proc, ws, runner, counter, summary = self.run_body(shards=2, failing_test=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("AssertionError", proc.stdout)
        self.assertRegex(summary, r"\| acceptance \d/2 \| FAILED \(acceptance \d/2 \(classes ")
        self.assertIn("coverage: expected 7, recorded 7", proc.stdout)
        for name in self.suites():
            if name != self.ACCEPTANCE:
                self.assertIn(f"::group::{name} passed in", proc.stdout)

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-0 file, so the copy cannot fail")
    def test_sharded_step_reports_every_unit_whose_copy_failed(self):
        proc, ws, runner, counter, summary = self.run_body(shards=2, uncopyable=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        for name in self.suites():
            if name != self.ACCEPTANCE:
                self.assertIn(f"::error title={name} failed::exit missing after", proc.stdout)
        for i in (1, 2):
            self.assertIn(f"::error title=acceptance {i}/2 failed::acceptance {i}/2 (classes ",
                          proc.stdout)
        self.assertIn("10 suite(s) failed", proc.stdout)
        self.assertEqual(summary.count("\n| workflow_"), 9)
        self.assertEqual(summary.count("| FAILED"), 10 + 1)

    def test_sharded_step_never_exceeds_the_width_with_shards_and_suites_queued_together(self):
        for cap in (2, 3):
            with self.subTest(width_cap=cap):
                proc, ws, runner, counter, _ = self.run_body(shards=4, width_cap=cap)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                width = min(cap, len(os.sched_getaffinity(0)))
                started = self.started(proc.stdout)
                self.assertEqual(len(started), 4 + 8)
                self.assertEqual(max(k for _, k in started), width)
                self.assertLessEqual(max(self.peaks(counter)), width)
                self.assertGreater(max(self.peaks(counter)), 1)

    def test_sharded_step_isolates_each_shard_like_a_suite(self):
        proc, ws, runner, counter, _ = self.run_body(shards=2)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(sorted(p.name for p in ws.iterdir()), ["MARKER", "scripts"])
        self.assertEqual(sorted(p.name for p in (ws / "scripts").iterdir()),
                         sorted(self.suites()))
        spec = json.loads((runner / "workflow-conformance" / "plan.json").read_text())
        seen = set()
        for shard in spec["shards"]:
            d = runner / "workflow-conformance" / shard["unit"]
            ids = set(shard["ids"])
            self.assertEqual({p.name for p in (d / "tmp").iterdir()}, {f"T-{i}" for i in ids})
            self.assertEqual({p.name for p in (d / "home").iterdir()}, {f"H-{i}" for i in ids})
            markers = {p.name for p in d.joinpath("repo").glob("MARKER*")}
            self.assertEqual(markers, {"MARKER"} | {f"MARKER-{i}" for i in ids})
            seen |= ids
        self.assertEqual(seen, set(spec["expected"]))

    def test_a_test_executed_twice_within_a_shard_fails_the_job(self):
        twice = ("class Twice(unittest.TestCase):\n"
                 "    def run(self, result=None):\n"
                 "        super().run(result)\n"
                 "        return super().run(result)\n"
                 "    def test_t(self): pass\n")
        proc, *_, summary = self.run_body(shards=2, acceptance_extra=twice)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("executed more than once: ", proc.stdout + summary)

    def test_sharded_step_fails_the_job_when_the_plan_fails(self):
        proc, ws, runner, counter, summary = self.run_body(
            shards=2, acceptance_extra="def setUpModule():\n    pass\n")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("::error title=acceptance plan failed::", proc.stdout)
        self.assertIn("setUpModule", proc.stderr)
        self.assertEqual(self.started(proc.stdout), [])
        self.assertEqual(list(counter.iterdir()), [])

    def test_the_measured_order_starts_the_longest_unit_first_and_beats_the_old_order(self):
        by_duration = sorted(self.MEASURED, key=lambda u: -self.MEASURED[u])
        self.assertEqual(by_duration[:6], [
            "workflow_protocol_test.py", "workflow_state_test.py", "acceptance-1of4",
            "acceptance-4of4", "acceptance-3of4", "acceptance-2of4"])
        proc, *_ = self.run_body(shards=4)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        started = [u for u, _ in self.started(proc.stdout)]
        self.assertEqual(started, by_duration)
        old = [f"acceptance-{i}of4" for i in (1, 2, 3, 4)] + [
            u for u in self.suites() if u != self.ACCEPTANCE]
        by_index = ["workflow_protocol_test.py", "workflow_state_test.py"] + [
            f"acceptance-{i}of4" for i in (1, 2, 3, 4)] + [
            u for u in self.suites() if u not in (self.ACCEPTANCE, "workflow_protocol_test.py",
                                                  "workflow_state_test.py")]
        lower = max(max(self.MEASURED.values()), sum(self.MEASURED.values()) / 4)
        new = self.makespan(started, self.MEASURED)
        self.assertEqual(self.makespan(old, self.MEASURED), 1050)
        self.assertLess(self.makespan(by_index, self.MEASURED), self.makespan(old, self.MEASURED))
        self.assertLessEqual(new, lower * 1.01)
        self.assertLessEqual(new, self.makespan(old, self.MEASURED) - 120)

    def test_every_name_in_longest_is_a_unit_of_the_run_and_listed_once(self):
        names = self.longest_names()
        self.assertEqual(len(names), len(set(names)))
        shards = next(int(l[len("shards="):]) for l in self.step_body().splitlines()
                      if l.startswith("shards="))
        units = set(self.suites()) | {f"acceptance-{i}of{shards}" for i in range(1, shards + 1)}
        for name in names:
            self.assertIn(name, units)
        self.assertEqual(names[0], self.ACCEPTANCE)
        self.assertEqual(set(self.MEASURED),
                         (set(names) | set(self.suites())) - {self.ACCEPTANCE})

    def test_a_stale_or_empty_longest_still_runs_every_unit_once(self):
        for label, kwargs in (("empty", dict(shards=4, longest="")),
                              ("shard count not named", dict(shards=2)),
                              ("unknown names", dict(shards=4, longest="nothing.py acceptance-9of9"))):
            with self.subTest(label):
                proc, ws, runner, counter, summary = self.run_body(**kwargs)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                units = [u for u, _ in self.started(proc.stdout)]
                shards = kwargs["shards"]
                self.assertEqual(sorted(units), sorted(
                    [f"acceptance-{i}of{shards}" for i in range(1, shards + 1)]
                    + [u for u in self.suites() if u != self.ACCEPTANCE]))
                self.assertIn("coverage: expected 7, recorded 7", proc.stdout)
                self.assertNotIn("::error", proc.stdout)
        proc, *_ = self.run_body(shards=4, longest="")
        units = [u for u, _ in self.started(proc.stdout)]
        self.assertEqual(units[:4], [f"acceptance-{i}of4" for i in (1, 2, 3, 4)])

    def test_shards_zero_runs_nine_units_and_no_shard_tool(self):
        proc, ws, runner, counter, summary = self.run_body(shards=0)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        started = self.started(proc.stdout)
        self.assertEqual(sorted(u for u, _ in started), sorted(self.suites()))
        self.assertEqual(started[0][0], self.ACCEPTANCE)
        self.assertEqual([u for u, _ in started][:4], [self.ACCEPTANCE] + self.LONGEST_SUITES[:3])
        self.assertLessEqual(max(k for _, k in started), min(4, len(os.sched_getaffinity(0))))
        self.assertFalse((runner / "workflow-conformance" / "plan.json").exists())
        self.assertNotIn("coverage:", proc.stdout)
        self.assertEqual(summary.count("\n| "), 9 + 1)
        self.assertEqual(summary.count("| passed |"), 9)


class WorkflowCI(unittest.TestCase):
    """`Workflow CI`: the consolidated `checks` job, the parallel source suites and `aggregate`."""

    @classmethod
    def setUpClass(cls):
        cls.text = (REPO_ROOT / ".github/workflows/workflow-ci.yml").read_text()
        cls.lines = cls.text.splitlines()

    def job(self, name):
        start = self.lines.index(f"  {name}:")
        end = next((i for i in range(start + 1, len(self.lines))
                    if self.lines[i].startswith("  ") and not self.lines[i].startswith("   ")
                    and self.lines[i].strip().endswith(":")), len(self.lines))
        return "\n".join(self.lines[start:end])

    def test_five_jobs(self):
        jobs = self.text.split("\njobs:\n", 1)[1]
        ids = [l for l in jobs.splitlines() if l.startswith("  ") and not l.startswith("   ")
               and l.strip().endswith(":")]
        self.assertEqual(ids, ["  changes:", "  checks:", "  release-source-conformance:",
                               "  update-fixture:", "  aggregate:"])

    def test_triggers_permissions_and_concurrency_are_kept(self):
        self.assertIn("name: Workflow CI\n", self.text)
        self.assertIn("on:\n  pull_request:\n  push:\n    branches: [main]\n"
                      "  workflow_dispatch:\n", self.text)
        self.assertIn("permissions:\n  contents: read\n", self.text)
        self.assertIn("  group: workflow-ci-${{ github.event_name }}-${{ github.event_name == "
                      "'pull_request' && github.ref || github.sha }}\n"
                      "  cancel-in-progress: ${{ github.event_name == 'pull_request' }}\n",
                      self.text)
        self.assertIn("defaults:\n  run:\n    shell: bash\n", self.text)
        self.assertEqual(self.text.count('python-version: "3.12"'), 4)

    def test_checks_job_keeps_every_command_as_a_named_step(self):
        checks = self.job("checks")
        self.assertIn("fetch-depth: 0", checks)
        self.assertEqual(checks.count("actions/checkout@v4"), 1)
        self.assertIn("--require-hashes -r tools/release/deflate-requirements.txt", checks)
        self.assertIn("tools/release/manager-pin.json", checks)
        self.assertIn('echo "$sha256  $wheel" | sha256sum -c', checks)
        for name in ("workflow-manager verify .", "Build the package",
                     "Verify the package with the Workflow Manager",
                     "Bootstrap and verify a scratch repository", "Save the release list",
                     "Pending release source is frozen", "Published release source is unchanged",
                     "Published assets are unchanged", "check_docs_test.py", "check_docs.py",
                     "release_test.py"):
            self.assertIn(f"      - name: {name}\n", checks, name)
        for command in ("release.py check-pending", "release.py check-immutable",
                        "release.py build --commit HEAD", "package verify",
                        "tools/docs/check_docs_test.py", "tools/release/release_test.py"):
            self.assertIn(command, checks)
        self.assertIn("name: package", checks)
        self.assertIn("if-no-files-found: error", checks)
        self.assertNotIn("continue-on-error", self.text)
        for gone in ("update-fixture", "Update fixture"):
            self.assertNotIn(gone, checks)
        for kept in ("Manager block is valid and measured", "Manager release list is current"):
            self.assertIn(f"      - name: {kept}\n", checks)

    def test_the_update_fixture_previous_release_skips_prereleases(self):
        self.assertIn("gh release list --json tagName,isDraft,isPrerelease --limit 1000", self.text)
        self.assertIn('if not r["isDraft"] and not r["isPrerelease"] and re.fullmatch', self.text)

    def test_checks_blocks_run_after_an_unrelated_failure(self):
        checks = self.job("checks")
        steps = checks.split("\n      - ")[1:]
        conditions = {}
        for step in steps:
            head = step.splitlines()[0]
            cond = next((l.strip()[4:] for l in step.splitlines() if l.startswith("        if: ")), None)
            conditions[head] = cond
        # Every step after setup is guarded by !cancelled() and names only its own prerequisites.
        for head, cond in list(conditions.items())[1:]:
            if head.startswith("uses: actions/setup-python") or head.startswith("name: Install the pinned deflate"):
                continue
            self.assertIsNotNone(cond, head)
            self.assertIn("!cancelled()", cond, head)
        docs = conditions["name: check_docs.py"]
        self.assertNotIn("manager", docs)
        self.assertNotIn("deflate", docs)
        self.assertEqual(conditions["name: release_test.py"].count("steps."), 1)
        self.assertIn("steps.deflate.outcome", conditions["name: release_test.py"])
        self.assertNotIn("manager", conditions["name: Build the package"])
        self.assertIn("steps.manager.outcome", conditions["name: workflow-manager verify ."])
        self.assertNotIn("deflate", conditions["name: workflow-manager verify ."])

    def aggregate(self, changes, changed, checks, conformance, update):
        body = _step_script(self.job("aggregate"), "Require every job")
        env = dict(os.environ, CHANGES=changes, CHANGED=changed, CHECKS=checks,
                   CONFORMANCE=conformance, UPDATE_FIXTURE=update)
        return subprocess.run(["bash", "-eo", "pipefail", "-c", body], env=env,
                              capture_output=True, text=True)

    def test_aggregate_needs_every_job_and_always_runs(self):
        aggregate = self.job("aggregate") + "\n"
        self.assertIn("    needs: [changes, checks, release-source-conformance, update-fixture]\n",
                      aggregate)
        self.assertIn("    if: always()\n", aggregate)
        for variable, job in (("CHANGES", "changes"), ("CHECKS", "checks"),
                              ("CONFORMANCE", "release-source-conformance"),
                              ("UPDATE_FIXTURE", "update-fixture")):
            self.assertIn(f"{variable}: ${{{{ needs.{job}.result }}}}\n", aggregate)
        self.assertIn("CHANGED: ${{ needs.changes.outputs.changed }}\n", aggregate)

    def test_aggregate_when_the_release_source_changed(self):
        for checks, conformance, update, code in (
                ("success", "success", "success", 0), ("failure", "success", "success", 1),
                ("success", "failure", "success", 1), ("success", "success", "failure", 1),
                ("success", "success", "cancelled", 1), ("cancelled", "success", "success", 1),
                ("skipped", "success", "success", 1), ("", "success", "success", 1),
                ("success", "skipped", "success", 1), ("success", "success", "skipped", 1),
                ("success", "skipped", "skipped", 1)):
            with self.subTest(checks=checks, conformance=conformance, update=update):
                proc = self.aggregate("success", "true", checks, conformance, update)
                self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)

    def test_aggregate_accepts_a_skip_only_when_changes_succeeded_and_said_unchanged(self):
        proc = self.aggregate("success", "false", "success", "skipped", "skipped")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("::error", proc.stdout)
        for changes, changed in (("failure", "false"), ("cancelled", "false"),
                                 ("skipped", "false"), ("", "false"), ("success", "true"),
                                 ("success", ""), ("success", "False"), ("success", "no"),
                                 ("failure", ""), ("failure", "true")):
            with self.subTest(changes=changes, changed=changed):
                proc = self.aggregate(changes, changed, "success", "skipped", "skipped")
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                for job in ("release-source-conformance", "update-fixture"):
                    self.assertIn(f"::error::the {job} job concluded skipped", proc.stdout)

    def test_aggregate_truth_table(self):
        """Every combination of the results and `changed`, against a model of the rule."""
        results = ("success", "failure", "cancelled", "skipped")
        for changes in results + ("",):
            for changed in ("true", "false", ""):
                for checks in ("success", "failure", "skipped"):
                    for conformance in results:
                        for update in results:
                            unchanged = changes == "success" and changed == "false"
                            expected = [f"the {job} job concluded {result}" for job, result in (
                                ("changes", changes), ("checks", checks))
                                if result != "success"]
                            expected += [f"the {job} job concluded {result}" for job, result in (
                                ("release-source-conformance", conformance),
                                ("update-fixture", update))
                                if result != "success" and not (result == "skipped" and unchanged)]
                            proc = self.aggregate(changes, changed, checks, conformance, update)
                            context = (changes, changed, checks, conformance, update)
                            self.assertEqual(proc.returncode, 1 if expected else 0,
                                             f"{context}: {proc.stdout}{proc.stderr}")
                            self.assertEqual(
                                [l.removeprefix("::error::") for l in proc.stdout.splitlines()
                                 if l.startswith("::error::")], expected, context)

    def test_aggregate_names_each_rejected_job_and_its_result(self):
        proc = self.aggregate("failure", "", "cancelled", "skipped", "failure")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.splitlines(), [
            "::error::the changes job concluded failure",
            "::error::the checks job concluded cancelled",
            "::error::the release-source-conformance job concluded skipped",
            "::error::the update-fixture job concluded failure"])

    # ---- the candidate-suite jobs run only when the release source or its CI changed

    def test_the_candidate_suite_jobs_wait_for_changes_and_run_only_when_it_says_changed(self):
        for name in ("release-source-conformance", "update-fixture"):
            job = self.job(name) + "\n"
            self.assertIn("\n    needs: changes\n", job, name)
            self.assertIn("\n    if: ${{ needs.changes.outputs.changed == 'true' }}\n", job, name)
        for name in ("changes", "checks"):
            self.assertNotRegex(self.job(name), r"(?m)^    (if|needs):", name)

    def test_the_changes_job_asks_the_subcommand_over_two_commits(self):
        job = self.job("changes") + "\n"
        self.assertIn("      - uses: actions/checkout@v4\n        with:\n          fetch-depth: 2\n",
                      job)
        self.assertIn("    timeout-minutes: 5\n", job)
        self.assertIn("    outputs:\n      changed: ${{ steps.decide.outputs.changed }}\n", job)
        self.assertIn("          EVENT_NAME: ${{ github.event_name }}\n", job)
        self.assertIn('        run: python3 tools/release/release.py release-source-changed '
                      '--event "$EVENT_NAME" | tee -a "$GITHUB_OUTPUT"\n', job)
        self.assertNotIn("permissions", job)

    def test_the_update_fixture_job_keeps_its_installs_timeout_and_upload(self):
        job = self.job("update-fixture") + "\n"
        self.assertIn("    timeout-minutes: 45\n", job)
        self.assertIn("--require-hashes -r tools/release/deflate-requirements.txt", job)
        self.assertIn("tools/release/manager-pin.json", job)
        self.assertIn('echo "$sha256  $wheel" | sha256sum -c', job)
        self.assertIn("gh release list --json tagName,isDraft,isPrerelease --limit 1000", job)
        self.assertIn("name: update-fixture-logs", job)
        self.assertIn("path: ${{ runner.temp }}/source-conformance-logs/", job)
        self.assertIn("        if: ${{ !cancelled() }}\n", job)
        order = [job.index(f"- name: {n}\n") for n in (
            "Save the release list", "Update the previous release to HEAD",
            "Run the frozen suites over the updated repository",
            "workflow-manager verify the updated repository")]
        self.assertEqual(order, sorted(order))
        self.assertLess(order[-1], job.index("actions/upload-artifact@v4"))

    def test_the_suites_and_verify_run_only_when_an_update_was_built(self):
        job = self.job("update-fixture") + "\n"
        suites = job.split("- name: Run the frozen suites over the updated repository\n")[1]
        self.assertTrue(suites.startswith(
            "        if: ${{ steps.update.outputs.built == 'true' }}\n        run: |\n"))
        # Verify also runs after failed suites, so one run shows both results.
        verify = job.split("- name: workflow-manager verify the updated repository\n")[1]
        self.assertTrue(verify.startswith(
            "        if: ${{ !cancelled() && steps.update.outputs.built == 'true' }}\n"
            '        run: workflow-manager --release-dir "$RUNNER_TEMP/candidate" verify '
            '"$RUNNER_TEMP/fixture"\n'))

    def test_the_candidate_suite_paths_are_the_release_source_plus_its_tooling_ci_and_archive_rules(self):
        self.assertEqual(release.CANDIDATE_PATHS, (
            "manifest.json", "payload", "fixtures", "templates",
            "tools/release", ".github/workflows/workflow-ci.yml", ".gitattributes"))
        self.assertEqual(release.CANDIDATE_PATHS,
                         (*package.RELEASE_SOURCE_PATHS, "tools/release",
                          ".github/workflows/workflow-ci.yml", ".gitattributes"))


class SourceConformanceRunner(unittest.TestCase):
    """The source-conformance step of `Workflow CI`, run with stand-in suites.

    It is the managed template's scheduling (D-Same-Text) over the staged
    fixture: the same shard tool text, the same constants, the same queue.
    """

    SUITES = ["workflow_acceptance_matrix_test.py", "workflow_protocol_test.py",
              "workflow_state_test.py", "workflow_gate_policy_test.py",
              "workflow_fingerprint_generalization_test.py",
              "workflow_state_completion_obligations_test.py", "workflow_integration_test.py",
              "workflow_fingerprint_test.py", "workflow_test_harness_test.py"]
    ACCEPTANCE = ConformanceTemplate.ACCEPTANCE

    @classmethod
    def setUpClass(cls):
        text = (REPO_ROOT / ".github/workflows/workflow-ci.yml").read_text()
        lines = text.splitlines()
        marker = lines.index("      - name: Run the source conformance suites")
        start = lines.index("        run: |", marker) + 1
        end = next(i for i in range(start, len(lines))
                   if lines[i] and not lines[i].startswith("          "))
        cls.body = "\n".join(l[10:] for l in lines[start:end]) + "\n"
        cls.template = (REPO_ROOT / "templates/.github/workflows/workflow-conformance.yml"
                        ).read_text()
        tlines = cls.template.splitlines()
        tstart = tlines.index("        run: |") + 1
        cls.template_body = "\n".join(l[10:] for l in tlines[tstart:]) + "\n"

    @staticmethod
    def heredoc(body):
        start = body.index("<<'PY'\n") + len("<<'PY'\n")
        return body[start:body.index("\nPY\n", start) + 1]

    def run_body(self, fail=(), uncopyable=False, nproc=None, drop_result=(), shards=0,
                 width_cap=4, failing_test=False, acceptance_extra="", check_stub="",
                 longest=None):
        tmp = Path(tempfile.mkdtemp(prefix="source-conformance-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        runner, counter = tmp / "runner", tmp / "counter"
        fixture = runner / "fixture"
        (fixture / "scripts").mkdir(parents=True)
        counter.mkdir()
        (fixture / "MARKER").write_text("original\n")
        if uncopyable:
            (fixture / "UNREADABLE").write_text("x\n")
            (fixture / "UNREADABLE").chmod(0)
        for name in self.SUITES:
            if shards and name == self.ACCEPTANCE:
                (fixture / "scripts" / name).write_text(
                    ConformanceTemplate.STANDIN_ACCEPTANCE.replace("@COUNTER@", repr(str(counter)))
                    .replace("@FAIL@", "False" if failing_test else "True") + acceptance_extra)
                continue
            (fixture / "scripts" / name).write_text(
                "import os, sys, time, pathlib\n"
                f"name = {name!r}\n"
                f"c = pathlib.Path({str(counter)!r})\n"
                "(c / name).write_text('')\n"
                "time.sleep(0.4)\n"
                "running = len([p for p in c.iterdir() if not p.name.startswith('peak-')])\n"
                "(c / ('peak-' + name)).write_text(str(running))\n"
                "(c / name).unlink()\n"
                "pathlib.Path('..', 'MARKER-' + name).write_text(name)\n"
                "pathlib.Path(os.environ['TMPDIR'], 'T-' + name).write_text(name)\n"
                "pathlib.Path(os.environ['HOME'], 'H-' + name).write_text(name)\n"
                "print('output of ' + name)\n"
                f"sys.exit({1 if name in fail else 0})\n")
        summary = tmp / "summary.md"
        body = ConformanceTemplate.with_constants(self.body, width_cap, shards, longest)
        if nproc is not None:
            body = f"nproc() {{ echo {nproc}; }}\n" + body
        if check_stub:
            body = ConformanceTemplate.stub_check(check_stub) + body
        if drop_result:
            # A suite that dies without recording a result: its result file never appears.
            body = body.replace('echo "$status $((SECONDS - start))" >"$d/result"',
                                'case " ' + " ".join(drop_result) + ' " in *" $1 "*) ;; '
                                '*) echo "$status $((SECONDS - start))" >"$d/result" ;; esac')
        env = dict(os.environ, RUNNER_TEMP=str(runner), GITHUB_STEP_SUMMARY=str(summary))
        proc = subprocess.run(["bash", "-eo", "pipefail", "-c", body], env=env,
                              capture_output=True, text=True, cwd=tmp)
        return proc, fixture, runner, counter, summary.read_text() if summary.exists() else ""

    def test_sharded_step_fails_when_the_check_verdict_is_bad_without_any_shard_row(self):
        ConformanceTemplate.assert_check_verdict_fails_the_job(self, self.run_body)

    def test_the_scheduler_words_a_bad_total_with_exit_zero_as_the_total(self):
        ConformanceTemplate.assert_bad_total_with_exit_zero_is_worded_as_the_total(self, self.run_body)

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-0 file, so the copy cannot fail")
    def test_a_failed_copy_is_in_the_units_log(self):
        ConformanceTemplate.assert_a_failed_copy_is_in_the_units_log(self, self.run_body)

    def peaks(self, counter):
        return [int(p.read_text()) for p in counter.iterdir() if p.name.startswith("peak-")]

    @staticmethod
    def started(out):
        return ConformanceTemplate.started(out)

    # ---- the step is the template's step ----

    def test_the_embedded_shard_tool_is_the_templates_byte_for_byte(self):
        mine, theirs = self.heredoc(self.body), self.heredoc(self.template_body)
        self.assertTrue(theirs.startswith("import argparse\n"))
        self.assertEqual(mine, theirs)
        self.assertEqual(self.body.count("<<'PY'\n"), 1)

    def test_the_step_is_the_templates_step_over_the_staged_fixture(self):
        """Only the paths, the log collection and the comment differ from the template."""
        expected = self.template_body
        for old, new in (
                ('base="$RUNNER_TEMP/workflow-conformance"\nrm -rf "$base"; mkdir -p "$base"\n',
                 'src="$RUNNER_TEMP/fixture"\nbase="$RUNNER_TEMP/source-conformance"; '
                 'logs="$RUNNER_TEMP/source-conformance-logs"\n'
                 'rm -rf "$base" "$logs"; mkdir -p "$base" "$logs"\n'),
                ("$GITHUB_WORKSPACE/scripts", "$src/scripts"),
                ('cp -a "$GITHUB_WORKSPACE/." "$d/repo" >>"$d/log" 2>&1',
                 'cp -a "$src/." "$d/repo" >>"$d/log" 2>&1')):
            self.assertEqual(expected.count(old), 1, old)
            expected = expected.replace(old, new)
        mine = self.body
        for block in (
                "# The diagnostic upload: every unit's log, result and shard file, the plan and "
                "the check.\n"
                'for u in $units; do\n  for f in log result shard.json; do\n'
                '    if [ -f "$base/$u/$f" ]; then cp "$base/$u/$f" "$logs/$u.$f"; fi\n'
                '  done\ndone\n'
                'if [ -f "$base/plan.json" ]; then cp "$base/plan.json" "$logs/plan.json"; fi\n',
                'for f in check.out check.err; do\n'
                '  if [ -f "$base/$f" ]; then cp "$base/$f" "$logs/$f"; fi\ndone\n'):
            self.assertEqual(mine.count(block), 1, block)
            mine = mine.replace(block, "")
        self.assertEqual(mine, expected)

    def test_the_update_fixture_job_runs_the_same_step_over_the_updated_repository(self):
        """Same text, byte for byte: the two jobs can never drift apart. The update job puts
        the updated repository where this job stages the conformance fixture."""
        text = (REPO_ROOT / ".github/workflows/workflow-ci.yml").read_text()
        mine = _step_script(_job_section(text, "update-fixture"),
                            "Run the frozen suites over the updated repository")
        self.assertEqual(mine, self.body)
        self.assertEqual(self.heredoc(mine), self.heredoc(self.template_body))
        self.assertIn('src="$RUNNER_TEMP/fixture"\n', mine)
        update_step = _step_script(_job_section(text, "update-fixture"),
                                   "Update the previous release to HEAD")
        self.assertIn('--keep "$RUNNER_TEMP/fixture"', update_step)

    def test_the_constants_and_the_suites_are_the_templates(self):
        for line in ("width_cap=4", "shards=4"):
            self.assertEqual(self.body.splitlines().count(line), 1, line)
            self.assertEqual(self.template_body.splitlines().count(line), 1, line)
        self.assertEqual(ConformanceTemplate.with_constants(self.body, 4, 4), self.body)
        suites = next(l for l in self.body.splitlines() if l.startswith("suites="))
        self.assertEqual(suites, next(l for l in self.template_body.splitlines()
                                      if l.startswith("suites=")))

    def test_the_job_keeps_its_stage_timeout_upload_and_the_aggregate(self):
        lines = (REPO_ROOT / ".github/workflows/workflow-ci.yml").read_text().splitlines()
        job = "\n".join(lines[lines.index("  release-source-conformance:"):
                              lines.index("  update-fixture:")])
        self.assertIn("timeout-minutes: 60", job)
        self.assertIn("release.py stage-conformance --commit HEAD --out "
                      '"$RUNNER_TEMP/fixture"', job)
        self.assertIn("name: source-conformance-logs", job)
        self.assertIn("path: ${{ runner.temp }}/source-conformance-logs/", job)
        self.assertIn("if: ${{ !cancelled() }}", job)
        self.assertNotIn("GITHUB_WORKSPACE", self.body)

    # ---- the unsharded path (shards=0), as the nine-suite runner always was ----

    def test_all_nine_pass(self):
        proc, _, runner, _, summary = self.run_body()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for name in self.SUITES:
            self.assertIn(f"::group::{name} passed in", proc.stdout)
            self.assertIn(f"| {name} | passed |", summary)
        self.assertNotIn("::error", proc.stdout)
        self.assertEqual(summary.count("\n| workflow_"), 9)
        self.assertEqual(sorted(p.name for p in (runner / "source-conformance-logs").glob("*.log")),
                         sorted(n + ".log" for n in self.SUITES))

    def test_each_suite_failing_alone_fails_the_runner_with_its_log(self):
        for bad in self.SUITES:
            with self.subTest(suite=bad):
                proc, _, runner, _, summary = self.run_body(fail=(bad,))
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                out = proc.stdout
                self.assertIn(f"::error title={bad} failed::exit 1 after", out)
                after = out.split(f"::error title={bad} failed::", 1)[1].splitlines()
                self.assertEqual(after[1], f"output of {bad}")
                self.assertNotIn(f"::group::{bad} passed", out)
                self.assertEqual(out.count("::error"), 1)
                for name in self.SUITES:
                    self.assertTrue((runner / "source-conformance-logs" / f"{name}.result").exists())
                    if name != bad:
                        self.assertIn(f"::group::{name} passed in", out)
                self.assertIn("1 suite(s) failed", out)
                self.assertIn(f"| {bad} | FAILED (exit 1) |", summary)
                self.assertEqual(summary.count("\n| workflow_"), 9)

    def test_multiple_failures_are_all_named(self):
        bad = (self.SUITES[0], self.SUITES[4], self.SUITES[8])
        proc, _, _, _, summary = self.run_body(fail=bad)
        self.assertEqual(proc.returncode, 1)
        for name in bad:
            self.assertIn(f"::error title={name} failed::exit 1 after", proc.stdout)
        self.assertIn("3 suite(s) failed", proc.stdout)
        self.assertEqual(summary.count("FAILED"), 3)

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-0 file, so the copy cannot fail")
    def test_a_copy_failure_is_reported_for_every_suite(self):
        proc, _, _, _, summary = self.run_body(uncopyable=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        for name in self.SUITES:
            self.assertIn(f"::error title={name} failed::exit missing after", proc.stdout)
        self.assertIn("9 suite(s) failed", proc.stdout)
        self.assertEqual(summary.count("\n| workflow_"), 9)

    def test_a_missing_result_fails_the_runner(self):
        lost = self.SUITES[3]
        proc, _, _, _, summary = self.run_body(drop_result=(lost,))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn(f"::error title={lost} failed::exit missing after", proc.stdout)
        self.assertIn("1 suite(s) failed", proc.stdout)
        self.assertIn(f"| {lost} | FAILED (exit missing) |", summary)

    def test_width_is_never_exceeded_and_longest_run_first(self):
        proc, _, _, counter, _ = self.run_body()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertLessEqual(max(self.peaks(counter)), 4)
        self.assertGreater(max(self.peaks(counter)), 1)
        starts = [u for u, _ in self.started(proc.stdout)]
        self.assertEqual(starts, self.SUITES)
        self.assertEqual(starts[:4], ["workflow_acceptance_matrix_test.py",
                                      "workflow_protocol_test.py", "workflow_state_test.py",
                                      "workflow_gate_policy_test.py"])

    def test_the_sharded_queue_starts_the_units_in_decreasing_measured_duration(self):
        proc, *_ = self.run_body(shards=4)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        measured = ConformanceTemplate.MEASURED
        self.assertEqual([u for u, _ in self.started(proc.stdout)],
                         sorted(measured, key=lambda u: -measured[u]))

    def test_width_follows_a_smaller_nproc(self):
        proc, _, _, counter, _ = self.run_body(nproc=2)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertLessEqual(max(self.peaks(counter)), 2)
        proc, _, _, counter, _ = self.run_body(nproc=1)
        self.assertEqual(max(self.peaks(counter)), 1)

    def test_suites_are_isolated_and_the_fixture_is_untouched(self):
        proc, fixture, runner, _, _ = self.run_body()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(sorted(p.name for p in fixture.iterdir()), ["MARKER", "scripts"])
        self.assertEqual(sorted(p.name for p in (fixture / "scripts").iterdir()),
                         sorted(self.SUITES))
        for name in self.SUITES:
            d = runner / "source-conformance" / name
            self.assertEqual([p.name for p in (d / "tmp").iterdir()], [f"T-{name}"])
            self.assertEqual([p.name for p in (d / "home").iterdir()], [f"H-{name}"])
            self.assertEqual(sorted(p.name for p in d.joinpath("repo").glob("MARKER*")),
                             ["MARKER", f"MARKER-{name}"])

    def test_the_suites_are_the_shipped_conformance_suites(self):
        manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        shipped = sorted(
            Path(a["target_path"]).name for a in manifest["artifacts"]
            if a["target_path"].startswith("scripts/workflow_")
            and a["target_path"].endswith("_test.py")
            and not a["target_path"].endswith("_demo_test.py"))
        self.assertEqual(sorted(self.SUITES), shipped)
        self.assertIn('suites="' + " ".join(self.SUITES) + '"', self.body)
        self.assertNotIn("/scripts/", self.body.replace("/repo/scripts", "").replace("$src/scripts", ""))

    # ---- the sharded path ----

    def test_sharded_all_pass_reports_nine_rows_the_coverage_and_uploads_the_shard_files(self):
        proc, fixture, runner, counter, summary = self.run_body(shards=2)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(summary.count("\n| workflow_"), 9)
        self.assertIn("| workflow_acceptance_matrix_test.py | passed (2 shards, 7 tests) |", summary)
        self.assertIn("coverage: expected 7, recorded 7", proc.stdout)
        for i in (1, 2):
            self.assertIn(f"| acceptance {i}/2 | passed |", summary)
        self.assertNotIn("::error", proc.stdout)
        units = [u for u, _ in self.started(proc.stdout)]
        self.assertEqual(units[:4], ConformanceTemplate.LONGEST_SUITES)
        self.assertEqual(sorted(units[4:6]), ["acceptance-1of2", "acceptance-2of2"])
        self.assertEqual(len(units), 2 + 8)
        self.assertNotIn(self.ACCEPTANCE, units)
        logs = runner / "source-conformance-logs"
        names = {p.name for p in logs.iterdir()}
        for unit in units:
            self.assertTrue({f"{unit}.log", f"{unit}.result"} <= names, unit)
        for i in (1, 2):
            shard = json.loads((logs / f"acceptance-{i}of2.shard.json").read_text())
            self.assertTrue(shard["completed"])
        self.assertTrue({"plan.json", "check.out", "check.err"} <= names)
        self.assertEqual(sorted(p.name for p in fixture.iterdir()), ["MARKER", "scripts"])

    def test_sharded_fails_for_each_of_the_nine_suites_in_turn(self):
        for name in self.SUITES:
            with self.subTest(name):
                if name == self.ACCEPTANCE:
                    proc, *_, summary = self.run_body(shards=2, failing_test=True)
                    self.assertRegex(proc.stdout,
                                     r"::error title=acceptance \d/2 failed::acceptance \d/2 "
                                     r"\(classes [^)]*\): exit 1; failed: [^\n]*Fourth\.test_fails")
                else:
                    proc, *_, summary = self.run_body(shards=2, fail=(name,))
                    self.assertIn(f"::error title={name} failed::exit 1 after", proc.stdout)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                self.assertIn("1 suite(s) failed", proc.stdout)
                self.assertEqual(summary.count("\n| workflow_"), 9)

    def test_a_failing_shard_keeps_its_log_and_result_in_the_upload(self):
        proc, _, runner, _, summary = self.run_body(shards=2, failing_test=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("AssertionError", proc.stdout)
        self.assertRegex(summary, r"\| acceptance \d/2 \| FAILED \(acceptance \d/2 \(classes ")
        self.assertIn("coverage: expected 7, recorded 7", proc.stdout)
        logs = runner / "source-conformance-logs"
        failing = [p for p in logs.glob("acceptance-*.result") if p.read_text().startswith("1 ")]
        self.assertEqual(len(failing), 1)
        self.assertIn("AssertionError", failing[0].with_suffix(".log").read_text())
        for name in self.SUITES:
            if name != self.ACCEPTANCE:
                self.assertIn(f"::group::{name} passed in", proc.stdout)

    def test_a_test_executed_twice_within_a_shard_fails_the_job(self):
        twice = ("class Twice(unittest.TestCase):\n"
                 "    def run(self, result=None):\n"
                 "        super().run(result)\n"
                 "        return super().run(result)\n"
                 "    def test_t(self): pass\n")
        proc, *_, summary = self.run_body(shards=2, acceptance_extra=twice)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("executed more than once: ", proc.stdout + summary)

    def test_a_failed_plan_fails_the_job_and_there_is_no_fallback(self):
        proc, _, _, counter, _ = self.run_body(
            shards=2, acceptance_extra="def setUpModule():\n    pass\n")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("::error title=acceptance plan failed::", proc.stdout)
        self.assertEqual(self.started(proc.stdout), [])
        self.assertEqual(list(counter.iterdir()), [])

    def test_shards_and_suites_share_one_limit(self):
        for cap in (2, 3):
            with self.subTest(width_cap=cap):
                proc, _, _, counter, _ = self.run_body(shards=4, width_cap=cap)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                width = min(cap, len(os.sched_getaffinity(0)))
                started = self.started(proc.stdout)
                self.assertEqual(len(started), 4 + 8)
                self.assertEqual(max(k for _, k in started), width)
                self.assertLessEqual(max(self.peaks(counter)), width)


class MainHistoryCase(ScratchTestCase):
    """`main`: v2.6.0 published at `base`; `C_V` bumps to 2.7.0; two ci: commits."""

    def setUp(self):
        super().setUp()
        self.base = self.repo.release_commit("2.6.0", "base")
        self.repo.tag("2.6.0", self.base)
        self.bump = self.repo.release_commit("2.7.0", "feat: 2.7.0", payload="v2\n")
        self.repo.touch("tools/a.py", "a\n")
        self.ci1 = self.repo.commit("ci: one")
        self.repo.touch("tools/b.py", "b\n")
        self.ci2 = self.repo.commit("ci: two")
        self.published_260 = ("2.6.0", False)

    def next_release(self, releases: str, trigger: str = "HEAD") -> dict[str, str]:
        return self.outputs(self.assert_ok("next-release", "--trigger", trigger,
                                           "--releases", releases))


class NextReleaseTest(MainHistoryCase):
    def test_pending_resolves_the_introducing_commit(self):
        releases = self.releases(self.published_260)
        self.assertEqual(self.next_release(releases),
                         {"state": "pending", "version": "2.7.0", "target": self.bump})

    def test_competing_triggers_resolve_the_same_target(self):
        releases = self.releases(self.published_260)
        for trigger in (self.bump, self.ci1, self.ci2):
            with self.subTest(trigger=trigger):
                self.assertEqual(self.next_release(releases, trigger),
                                 {"state": "pending", "version": "2.7.0", "target": self.bump})
        self.repo.tag("2.7.0", self.bump)
        published = self.releases(self.published_260, ("2.7.0", False))
        for trigger in (self.bump, self.ci1, self.ci2):
            with self.subTest(trigger=trigger):
                self.assertEqual(self.next_release(published, trigger),
                                 {"state": "published", "version": "2.7.0",
                                  "target": self.bump})

    def test_published_tip(self):
        self.repo.tag("2.7.0", self.bump)
        releases = self.releases(self.published_260, ("2.7.0", False))
        self.assertEqual(self.next_release(releases),
                         {"state": "published", "version": "2.7.0", "target": self.bump})

    def test_lower_or_equal_unpublished_version_refused(self):
        # 2.8.0 published elsewhere (its tag an ancestor), main still at 2.7.0.
        self.repo.tag("2.8.0", self.base)
        releases = self.releases(self.published_260, ("2.8.0", False))
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases", releases,
                            naming=("not greater than the highest published version 2.8.0",))
        self.repo.untag("2.8.0")
        self.repo.tag("2.7.0", self.base)
        # 2.7.0 published (non-draft, tagged) is never "pending": equal is published.
        releases = self.releases(self.published_260, ("2.7.0", False))
        self.assertEqual(self.next_release(releases)["state"], "published")

    def test_highest_tag_not_an_ancestor_refused(self):
        self.repo.git("checkout", "-q", "-b", "side", self.base)
        self.repo.touch("side.txt", "x\n")
        side = self.repo.commit("side")
        self.repo.git("checkout", "-q", "main")
        self.repo.untag("2.6.0")
        self.repo.tag("2.6.0", side)
        releases = self.releases(self.published_260)
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases", releases,
                            naming=("v2.6.0's tag", "is not an ancestor of"))

    def test_unpublished_predecessor_version_refused(self):
        # 2.7.0 merged on a red push run and never published; 2.8.0 bumps it.
        self.repo.release_commit("2.8.0", "feat: 2.8.0", payload="v3\n")
        releases = self.releases(self.published_260)
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases", releases,
                            naming=("version 2.7.0", "is not published",
                                    "v2.7.0 must be published before 2.8.0"))
        self.repo.tag("2.7.0", self.bump)
        releases = self.releases(self.published_260, ("2.7.0", False))
        self.assertEqual(self.next_release(releases)["state"], "pending")

    def test_trigger_whose_release_source_differs_refused(self):
        self.repo.release_commit("2.7.0", "slipped past", payload="v3\n")
        releases = self.releases(self.published_260)
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases", releases,
                            naming=("release source differs", "payload/scripts/tool.py"))

    def test_trigger_not_on_first_parent_history_refused(self):
        self.repo.git("checkout", "-q", "-b", "side", self.ci2)
        self.repo.touch("side.txt", "x\n")
        side = self.repo.commit("side")
        self.repo.git("checkout", "-q", "main")
        self.assert_refused("next-release", "--trigger", side, "--releases",
                            self.releases(self.published_260),
                            naming=("not on the first-parent history",))

    def test_malformed_manifest_refused(self):
        (self.repo.root / "manifest.json").write_text("{not json")
        self.repo.commit("break")
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases",
                            self.releases(self.published_260), naming=("malformed",))

    def test_malformed_release_list_refused(self):
        path = self.tmp / "bad.json"
        path.write_text(json.dumps([{"tagName": "v2.6.0"}]))
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases", str(path),
                            naming=("tagName/isDraft",))


class FailedPublicationTest(MainHistoryCase):
    """D-W0-Recovery: residue of a failed publication of 2.7.0 is refused, and
    removing it makes 2.7.0 publishable again."""

    def test_draft_with_tag_refused_then_recovered(self):
        self.repo.tag("2.7.0", self.bump)
        residue = self.releases(self.published_260, ("2.7.0", True))
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases", residue,
                            naming=("a draft release v2.7.0", "the tag v2.7.0",
                                    "Recovering from a failed publication"))
        # Recovery: the draft deleted (gone from the list) and the tag deleted.
        self.repo.untag("2.7.0")
        recovered = self.releases(self.published_260)
        self.assertEqual(self.next_release(recovered),
                         {"state": "pending", "version": "2.7.0", "target": self.bump})
        # Re-run publishes.
        self.repo.tag("2.7.0", self.bump)
        published = self.releases(self.published_260, ("2.7.0", False))
        self.assertEqual(self.next_release(published)["state"], "published")

    def test_draft_without_tag_refused(self):
        residue = self.releases(self.published_260, ("2.7.0", True))
        err = self.assert_refused("next-release", "--trigger", "HEAD", "--releases", residue,
                                  naming=("a draft release v2.7.0",))
        self.assertNotIn("the tag v2.7.0", err)

    def test_tag_without_release_refused_then_recovered(self):
        self.repo.tag("2.7.0", self.bump)
        releases = self.releases(self.published_260)
        err = self.assert_refused("next-release", "--trigger", "HEAD", "--releases", releases,
                                  naming=("the tag v2.7.0",))
        self.assertNotIn("draft", err)
        self.repo.untag("2.7.0")
        self.assertEqual(self.next_release(releases),
                         {"state": "pending", "version": "2.7.0", "target": self.bump})

    def test_published_release_without_tag_refused(self):
        releases = self.releases(self.published_260, ("2.7.0", False))
        self.assert_refused("next-release", "--trigger", "HEAD", "--releases", releases,
                            naming=("release v2.7.0 is published but the tag v2.7.0 is missing",))

    def test_check_pending_treats_residue_as_pending(self):
        self.repo.release_commit("2.7.0", "more", payload="v3\n")
        draft_only = self.releases(self.published_260, ("2.7.0", True))
        self.assert_refused("check-pending", "--releases", draft_only,
                            naming=("version 2.7.0 is pending", "a draft release v2.7.0"))
        self.repo.tag("2.7.0", self.bump)
        stray_tag = self.releases(self.published_260)
        self.assert_refused("check-pending", "--releases", stray_tag,
                            naming=("version 2.7.0 is pending", "the tag v2.7.0"))


# -- check-published, check-immutable, supersession ---------------------------------


class PublishedCase(ScratchTestCase):
    """2.6.0 published at `base` with exactly its built assets."""

    def setUp(self):
        super().setUp()
        self.base = self.repo.release_commit("2.6.0", "base")
        self.repo.tag("2.6.0", self.base)
        self.built = self.build(self.base, "built")
        self.downloaded = self.tmp / "downloaded"
        shutil.copytree(self.built, self.downloaded)
        self.published = self.releases(("2.6.0", False))

    def check_published(self, releases: str | None = None, target: str | None = None,
                        version: str = "2.6.0", built: Path | None = None):
        return ("check-published", "--version", version, "--target", target or self.base,
                "--releases", releases or self.published, "--assets", str(built or self.built),
                "--downloaded", str(self.downloaded))


class PublishedReadBackTest(PublishedCase):
    def test_intact(self):
        self.assert_ok(*self.check_published())

    def test_draft_refused(self):
        self.assert_refused(*self.check_published(self.releases(("2.6.0", True))),
                            naming=("not a published release (it is a draft)",
                                    "Superseding an incomplete published release"))

    def test_missing_asset_refused(self):
        (self.downloaded / "SHA256SUMS").unlink()
        self.assert_refused(*self.check_published(),
                            naming=("missing asset SHA256SUMS", "supersede"))

    def test_extra_asset_refused(self):
        (self.downloaded / "notes.txt").write_text("x")
        self.assert_refused(*self.check_published(),
                            naming=("extra asset notes.txt", "supersede"))

    def test_differing_byte_refused(self):
        manifest = self.downloaded / "workflow-2.6.0.manifest.json"
        manifest.write_bytes(manifest.read_bytes() + b" ")
        self.assert_refused(*self.check_published(),
                            naming=("asset workflow-2.6.0.manifest.json differs", "supersede"))

    def test_archive_difference_names_its_cause(self):
        archive = self.downloaded / "workflow-2.6.0.tar.gz"
        tar_data = package.decompressed_tar(archive)
        archive.write_bytes(gzip.compress(tar_data, mtime=0, compresslevel=1))
        self.assert_refused(*self.check_published(),
                            naming=("with an identical tar stream", "compression runtime"))
        archive.write_bytes(gzip.compress(tar_data + b"\0" * 512, mtime=0))
        self.assert_refused(*self.check_published(),
                            naming=("differs in its tar stream", "release source differs"))

    def test_tag_elsewhere_refused(self):
        self.repo.touch("README.md", "x\n")
        other = self.repo.commit("docs: x")
        self.assert_refused(*self.check_published(target=other),
                            naming=(f"is at {self.base}, not {other}", "supersede"))

    def test_check_immutable(self):
        self.repo.touch("tools/x.py", "x\n")
        self.repo.commit("ci: tooling")
        out = self.assert_ok("check-immutable", "--releases", self.published,
                             "--published", str(self.downloaded))
        self.assertIn("equals the published assets of v2.6.0", out)
        (self.downloaded / "SHA256SUMS").unlink()
        self.assert_refused("check-immutable", "--releases", self.published,
                            "--published", str(self.downloaded),
                            naming=("missing asset SHA256SUMS",))
        shutil.copy(self.built / "SHA256SUMS", self.downloaded / "SHA256SUMS")
        (self.downloaded / "extra.bin").write_bytes(b"x")
        self.assert_refused("check-immutable", "--releases", self.published,
                            "--published", str(self.downloaded),
                            naming=("extra asset extra.bin",))

    def test_check_immutable_refuses_a_changed_payload_byte(self):
        self.repo.release_commit("2.6.0", "sneak", payload="payload v1!\n")
        self.assert_refused("check-immutable", "--releases", self.published,
                            naming=("differs from v2.6.0", "payload/scripts/tool.py"))

    def test_check_immutable_does_not_apply_to_an_unpublished_version(self):
        out = self.assert_ok("check-immutable", "--releases", self.releases())
        self.assertIn("is not published", out)


class IncompletePublishedReleaseTest(PublishedCase):
    """2.6.0 was published without SHA256SUMS: every rerun fails its read-back,
    and the supersession bump to 2.6.1 publishes normally."""

    def setUp(self):
        super().setUp()
        (self.downloaded / "SHA256SUMS").unlink()

    def test_rerun_is_not_success_and_supersession_publishes(self):
        out = self.assert_ok("next-release", "--trigger", "HEAD", "--releases", self.published)
        self.assertEqual(self.outputs(out),
                         {"state": "published", "version": "2.6.0", "target": self.base})
        self.assert_refused(*self.check_published(),
                            naming=("missing asset SHA256SUMS",
                                    "never pin it in workflow-manager"))
        self.assert_refused("check-immutable", "--releases", self.published, "--published",
                            str(self.downloaded), naming=("missing asset SHA256SUMS",))

        superseding = self.repo.release_commit("2.6.1", "fix: supersede incomplete release 2.6.0")
        self.assert_ok("check-title", "fix: supersede incomplete release 2.6.0", "--agree")
        self.assert_ok("check-pending", "--releases", self.published)
        self.assertIn("2.6.1 is not published",
                      self.assert_ok("check-immutable", "--releases", self.published))
        out = self.assert_ok("next-release", "--trigger", "HEAD", "--releases", self.published)
        self.assertEqual(self.outputs(out),
                         {"state": "pending", "version": "2.6.1", "target": superseding})

        built = self.build(superseding, "built-2.6.1")
        shutil.rmtree(self.downloaded)
        shutil.copytree(built, self.downloaded)
        self.repo.tag("2.6.1", superseding)
        both = self.releases(("2.6.0", False), ("2.6.1", False))
        self.assert_ok(*self.check_published(both, superseding, "2.6.1", built))



# -- the Release workflow's gate ---------------------------------------------------


RELEASE_YML = REPO_ROOT / ".github" / "workflows" / "release.yml"

#: A stand-in `gh`: `main`'s tip is `$GH_TIP`; a sha has a successful
#: `Workflow CI` push run exactly when it is listed in `$GH_GREEN`.
FAKE_GH = r"""#!/usr/bin/env bash
[ "$1" = api ] || exit 9
case "$2" in
  */commits/main) echo "$GH_TIP" ;;
  */actions/workflows/workflow-ci.yml/runs\?*event=push\&status=success)
    sha="${2#*head_sha=}"; sha="${sha%%&*}"
    if [ "${GH_COUNT+set}" ]; then printf '%s\n' "$GH_COUNT"; exit 0; fi
    case " $GH_GREEN " in *" $sha "*) echo 1 ;; *) echo 0 ;; esac ;;
  *) exit 9 ;;
esac
"""


def _job_section(text: str, job: str) -> str:
    start = text.index(f"\n  {job}:\n")
    end = text.find("\n  ", start + 1)
    while end != -1 and text[end + 3] == " ":
        end = text.find("\n  ", end + 1)
    return text[start:] if end == -1 else text[start:end]


def _step_script(text: str, name: str) -> str:
    """The `run: |` block of the step called `name`, dedented."""
    lines = text.splitlines()
    index = lines.index(f"      - name: {name}")
    while lines[index].strip() != "run: |":
        index += 1
    indent = len(lines[index]) - len(lines[index].lstrip()) + 2
    body = []
    for line in lines[index + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) < indent:
            break
        body.append(line[indent:])
    return "\n".join(body) + "\n"


class ReleaseGateTest(unittest.TestCase):
    """The `gate` job decides which commit the `release` job checks out and
    executes: only `main`'s tip, and only once its own push run is green."""

    def setUp(self):
        self.text = RELEASE_YML.read_text()
        self.tmp = Path(tempfile.mkdtemp(prefix="release-gate-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(FAKE_GH)
        (bin_dir / "gh").chmod(0o755)
        self.path = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
        self.script = _step_script(self.text, "Resolve the release commit")

    def gate(self, event: str, tip: str, green: tuple[str, ...] = (),
             run_sha: str = "", count: str | None = None) -> tuple[int, str, str]:
        output = self.tmp / "output"
        output.write_text("")
        env = {"PATH": self.path, "GITHUB_EVENT_NAME": event, "GITHUB_OUTPUT": str(output),
               "GITHUB_REPOSITORY": "owner/workflow", "RUN_SHA": run_sha,
               "GH_TIP": tip, "GH_GREEN": " ".join(green)}
        if count is not None:
            env["GH_COUNT"] = count
        proc = subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c", self.script], capture_output=True, text=True,
            env=env)
        return proc.returncode, output.read_text(), proc.stdout + proc.stderr

    def test_trigger_at_the_tip_is_released(self):
        self.assertEqual(self.gate("workflow_run", "T", run_sha="T")[:2], (0, "sha=T\n"))

    def test_newer_tip_without_a_green_push_run_defers(self):
        # A green trigger `T`, then a tooling-only commit `M` whose push run is
        # red or still running: nothing at `M` is executed.
        code, output, log = self.gate("workflow_run", "M", green=("T",), run_sha="T")
        self.assertEqual((code, output), (0, ""))
        self.assertIn("main moved from T to M", log)

    def test_newer_green_tip_is_released_not_the_trigger(self):
        self.assertEqual(self.gate("workflow_run", "M", green=("T", "M"), run_sha="T")[:2],
                         (0, "sha=M\n"))

    def test_dispatch_requires_a_green_tip(self):
        self.assertEqual(self.gate("workflow_dispatch", "M", green=("M",))[:2], (0, "sha=M\n"))
        code, output, log = self.gate("workflow_dispatch", "M", green=("T",))
        self.assertEqual((code, output), (1, ""))
        self.assertIn("has no successful Workflow CI push run", log)

    def test_malformed_run_count_fails_closed(self):
        # `total_count` that is not a count (`null`, empty, garbage) is never
        # read as green, on either trigger.
        for count in ("null", "", "1x", "-1"):
            for event, run_sha in (("workflow_dispatch", ""), ("workflow_run", "T")):
                with self.subTest(count=count, event=event):
                    code, output, log = self.gate(event, "M", run_sha=run_sha, count=count)
                    self.assertEqual((code, output), (1, ""))
                    self.assertIn("unexpected Workflow CI run count", log)

    def test_release_job_executes_only_the_gate_sha(self):
        gate = _job_section(self.text, "gate")
        self.assertNotIn("actions/checkout", gate)
        self.assertNotIn("tools/release", gate)
        job = _job_section(self.text, "release")
        self.assertIn("needs: gate", job)
        self.assertIn("if: needs.gate.outputs.sha != ''", job)
        self.assertIn("ref: ${{ needs.gate.outputs.sha }}", job)
        self.assertIn("TRIGGER: ${{ needs.gate.outputs.sha }}", job)
        self.assertNotIn("ref: main", self.text)
        # The checkout precedes every use of the repository's release tooling.
        self.assertLess(job.index("actions/checkout"), job.index("tools/release"))


class RoadmapTest(unittest.TestCase):
    """The roadmap text is excluded from reviewed content at both stages, so
    this is its only guard. It pins the structure and the done/next facts."""

    def setUp(self):
        self.text = (REPO_ROOT / "docs" / "ROADMAP.md").read_text()

    def section(self, heading: str) -> str:
        start = self.text.index(f"## {heading}")
        end = self.text.find("\n## ", start + 1)
        return self.text[start:] if end == -1 else self.text[start:end]

    def test_it_has_the_readable_sections_in_order(self):
        headings = ["How to read this roadmap", "What's next", "Done",
                    "Later (open items)", "Open defects", "Principles"]
        positions = [self.text.index(f"## {h}") for h in headings]
        self.assertEqual(positions, sorted(positions))

    def test_whats_next_lists_the_fix_release_then_c10_then_m3(self):
        table = self.section("What's next")
        self.assertIn("| Order | Item |", table)
        self.assertIn("v2.6.0-003", table)
        self.assertIn('"2.2"', table)
        self.assertLess(table.index("small Workflow fix release"), table.index("Controller C10"))
        self.assertLess(table.index("Controller C10"), table.index("M3"))

    def test_w2_and_workflow_2_8_0_are_done_with_the_cutover_done(self):
        done = self.section("Done")
        self.assertIn("**Workflow 2.8.0**", done)
        self.assertIn("gate policy", done)
        self.assertIn("pinned by Manager v1.4.0", done)
        self.assertIn("**Workflow 2.7.0**", done)
        self.assertNotIn("pending cutover", self.text)

    def test_the_only_open_defect_is_listed(self):
        rows = [l for l in self.section("Open defects").splitlines() if l.startswith("| `v")]
        self.assertEqual(len(rows), 1)
        self.assertIn("`v2.6.0-003`", rows[0])


class BacklogReleaseTest(unittest.TestCase):
    """Release 2.17.0 (backlog-file): the records, the counts, the downgrade
    posture, and the shipped script run from an installed `scripts/`."""

    SCRIPT = "scripts/workflow_backlog.py"
    DOCUMENT = "docs/ai-workflow/BACKLOG_FILE.md"

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.records = {r["target_path"]: r for r in self.manifest["artifacts"]}

    def test_the_release_keeps_the_two_2_17_0_distribution_records(self):
        for target, location in ((self.SCRIPT, "payload/scripts/workflow_backlog.py"),
                                 (self.DOCUMENT, "payload/docs/ai-workflow/BACKLOG_FILE.md")):
            with self.subTest(target):
                record = self.records[target]
                self.assertEqual((record["category"], record["location"], record["executable"]),
                                 ("distribution", location, False))
                self.assertRegex(target, record["rule"])
                self.assertEqual(record["sha256"], _sha((REPO_ROOT / location).read_bytes()))
        counts = self.manifest["counts"]
        by_category = {}
        for record in self.manifest["artifacts"]:
            by_category[record["category"]] = by_category.get(record["category"], 0) + 1
        self.assertEqual(counts["artifacts"], len(self.manifest["artifacts"]))
        self.assertEqual(counts["by_category"], by_category)

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        text = (REPO_ROOT / "docs" / "release-history.md").read_text()
        row = next(line for line in text.splitlines() if line.startswith("| 2.17.0 |"))
        for needle in ("backlog file", "tools/workflow_backlog.py", "2.16.0",
                       "Orchestration Protocol 1.5", "v2.17.0"):
            self.assertIn(needle, row)
        self.assertLess(text.index("| 2.17.0 |"), text.index("| 2.16.0 |"))

    def install(self, root: Path) -> None:
        for target in (self.SCRIPT, self.DOCUMENT):
            dest = root / target
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / self.records[target]["location"], dest)
        subprocess.run(["git", "init", "-q", str(root)], check=True)

    def backlog(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(root / self.SCRIPT), *args],
                              cwd=root, capture_output=True, text=True)

    def declare(self, root: Path) -> None:
        config = root / "docs/ai-workflow/WORKFLOW_CONFIG.json"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(json.dumps({"backlog": {"file": "docs/backlog.yaml"}}))
        (root / "docs/backlog.yaml").write_text(
            "version: 1\nitems:\n  - id: first-item\n    title: My first item\n"
            "    status: next\n    order: 1\n")

    def test_a_declared_backlog_runs_generate_next_accept_and_check_from_scripts(self):
        tmp = Path(tempfile.mkdtemp(prefix="backlog-release-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.install(tmp)
        self.declare(tmp)
        self.assertEqual(self.backlog(tmp, "generate", "--replace").returncode, 0)
        self.assertEqual(self.backlog(tmp, "check").returncode, 0)
        chosen = self.backlog(tmp, "next")
        self.assertEqual(chosen.returncode, 0, chosen.stderr)
        self.assertEqual(json.loads(chosen.stdout)["item"]["id"], "first-item")
        accepted = self.backlog(tmp, "accept", "first-item", "--release", "2.17.0")
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertEqual(json.loads(accepted.stdout)["status"], "done")
        self.assertIn("status: done", (tmp / "docs/backlog.yaml").read_text())
        self.assertEqual(self.backlog(tmp, "check").returncode, 0)
        (tmp / "docs/ROADMAP.md").write_text("edited by hand\n")
        stale = self.backlog(tmp, "check")
        self.assertEqual(stale.returncode, 1)
        self.assertIn("roadmap_stale", stale.stderr)

    def test_a_repository_without_a_declaration_is_unchanged(self):
        tmp = Path(tempfile.mkdtemp(prefix="backlog-release-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.install(tmp)
        for command in (("next",), ("check",), ("status",)):
            with self.subTest(command):
                done = self.backlog(tmp, *command)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertFalse(json.loads(done.stdout)["declared"])
        self.assertEqual(sorted(p.name for p in tmp.iterdir()), [".git", "docs", "scripts"])
        self.assertFalse((tmp / "docs/ROADMAP.md").exists())


class HarnessNeutralReleaseTest(unittest.TestCase):
    """Release 2.18.0 (harness-neutral-commands): the new record, the counts and
    the release-history row. The current version, release constant and posture
    are pinned by the class of the current release."""

    DOCUMENT = "docs/ai-workflow/COMMAND_FILES.md"

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.records = {r["target_path"]: r for r in self.manifest["artifacts"]}

    def test_the_release_keeps_the_2_18_0_distribution_record(self):
        location = "payload/docs/ai-workflow/COMMAND_FILES.md"
        record = self.records[self.DOCUMENT]
        self.assertEqual((record["category"], record["location"], record["executable"]),
                         ("distribution", location, False))
        self.assertRegex(self.DOCUMENT, record["rule"])
        self.assertEqual(record["sha256"], _sha((REPO_ROOT / location).read_bytes()))
        by_category = {}
        for entry in self.manifest["artifacts"]:
            by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1
        counts = self.manifest["counts"]
        self.assertEqual(counts["artifacts"], len(self.manifest["artifacts"]))
        self.assertEqual(counts["by_category"], by_category)

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        text = (REPO_ROOT / "docs" / "release-history.md").read_text()
        row = next(line for line in text.splitlines() if line.startswith("| 2.18.0 |"))
        for needle in ("COMMAND_FILES.md", "the agent", "$ARGUMENTS", "2.17.0",
                       "Orchestration Protocol 1.5", "v2.18.0"):
            self.assertIn(needle, row)
        self.assertLess(text.index("| 2.18.0 |"), text.index("| 2.17.0 |"))


class ReviewFollowupsReleaseTest(unittest.TestCase):
    """Release 2.18.1 (review-followups-cleanup): what stays true of it once a
    later release is current -- the counts' consistency, the template digest,
    the record sentences and the release-history row. The current counts are
    pinned by the current release's class (2.19.0 added a record)."""

    TEMPLATE = ".github/workflows/workflow-conformance.yml"

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())

    def test_the_release_added_no_record(self):
        by_category = {}
        for entry in self.manifest["artifacts"]:
            by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1
        counts = self.manifest["counts"]
        self.assertEqual(counts["artifacts"], len(self.manifest["artifacts"]))
        self.assertEqual(counts["templates"], len(self.manifest["templates"]))
        self.assertEqual(counts["by_category"], by_category)

    def test_the_template_record_names_the_change_and_its_digest_is_current(self):
        record = next(r for r in self.manifest["templates"] if r["target_path"] == self.TEMPLATE)
        data = (REPO_ROOT / record["location"]).read_bytes()
        self.assertEqual((record["sha256"], record["size"]), (_sha(data), len(data)))
        self.assertIn("workflow-2.18.1", record["derivation"])

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for record in self.manifest["artifacts"]:
            with self.subTest(record["target_path"]):
                data = (REPO_ROOT / record["location"]).read_bytes()
                self.assertEqual((record["sha256"], record["size"]), (_sha(data), len(data)))
        for target in ("scripts/workflow_state.py", "scripts/workflow_backlog.py",
                       "docs/ai-workflow/REVIEW_PROTOCOL.md"):
            record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
            self.assertIn("review-followups-cleanup (workflow-2.18.1)", record["rationale"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        text = (REPO_ROOT / "docs" / "release-history.md").read_text()
        row = next(line for line in text.splitlines() if line.startswith("| 2.18.1 |"))
        for needle in ("2.18.0", "39j", "60e", "64c", "- (none)", "Orchestration Protocol 1.5",
                       "v2.18.1"):
            self.assertIn(needle, row)
        self.assertLess(text.index("| 2.18.1 |"), text.index("| 2.18.0 |"))


class ReviewFollowups2ReleaseTest(unittest.TestCase):
    """Release 2.18.2 (review-followups-2): the rationale sentences it added and
    its release-history row. The current version, constant and posture are
    pinned by the class of the newest release."""

    CHANGED = (".claude/commands/accept-milestone.md", ".claude/commands/adopt-gate-policy.md",
               ".claude/commands/approve-review.md", ".claude/commands/milestone-plan.md",
               ".claude/commands/request-plan-amendment.md",
               ".claude/commands/resume-implementation.md",
               ".claude/commands/retire-legacy-work-item.md",
               "docs/ai-workflow/ORCHESTRATION_PROTOCOL.md", "scripts/workflow_integration_test.py",
               "scripts/workflow_protocol.py", "scripts/workflow_protocol_test.py",
               "scripts/workflow_state.py", "scripts/workflow_state_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("review-followups-2 (workflow-2.18.2)", record["rationale"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        text = (REPO_ROOT / "docs" / "release-history.md").read_text()
        row = next(line for line in text.splitlines() if line.startswith("| 2.18.2 |"))
        for needle in ("2.18.1", "60e", "64c", "39j", "Orchestration Protocol 1.5", "v2.18.2"):
            self.assertIn(needle, row)
        self.assertLess(text.index("| 2.18.2 |"), text.index("| 2.18.1 |"))


class ReviewFollowups3ReleaseTest(unittest.TestCase):
    """Release 2.18.3 (review-followups-3): what stays true of it once a later
    release is current -- the record sentences and the release-history row."""

    CHANGED = ("docs/ai-workflow/ORCHESTRATION_PROTOCOL.md", "scripts/workflow_protocol.py",
               "scripts/workflow_protocol_test.py", "scripts/workflow_state.py",
               "scripts/workflow_state_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("review-followups-3 (workflow-2.18.3)", record["rationale"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        text = (REPO_ROOT / "docs" / "release-history.md").read_text()
        row = next(line for line in text.splitlines() if line.startswith("| 2.18.3 |"))
        for needle in ("2.18.2", "#71", "zsh", "Orchestration Protocol 1.5", "v2.18.3"):
            self.assertIn(needle, row)
        self.assertLess(text.index("| 2.18.3 |"), text.index("| 2.18.2 |"))


class ReviewFollowups4ReleaseTest(unittest.TestCase):
    """Release 2.18.4 (review-followups-4): what stays true of it once a later
    release is current -- the record sentences, the #50 correction with its
    command, and the release-history row."""

    CHANGED = ("docs/ai-workflow/ORCHESTRATION_PROTOCOL.md",
               ".claude/commands/resume-implementation.md",
               ".claude/commands/retire-legacy-work-item.md",
               "scripts/workflow_integration_test.py", "scripts/workflow_protocol.py",
               "scripts/workflow_protocol_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.history = (REPO_ROOT / "docs" / "release-history.md").read_text()

    def row(self) -> str:
        return next(line for line in self.history.splitlines() if line.startswith("| 2.18.4 |"))

    def command(self) -> str:
        """The comparison command, as the release-history row states it."""
        match = re.search(r"`(for c in \$\(git log .*?; done)`", self.row())
        self.assertIsNotNone(match)
        return match.group(1)

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("review-followups-4 (workflow-2.18.4)", record["rationale"])
        template = next(r for r in self.manifest["templates"]
                        if r["target_path"] == ".github/workflows/workflow-conformance.yml")
        self.assertIn("review-followups-4 (workflow-2.18.4) starts the queue's units longest first",
                      template["derivation"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        for needle in ("2.18.3", "#50", "#55", "longest first", "names no work item",
                       "re-validates committed generation-record commits", "git diff HEAD",
                       "Orchestration Protocol 1.5", "v2.18.4"):
            self.assertIn(needle, self.row())
        self.assertLess(self.history.index("| 2.18.4 |"), self.history.index("| 2.18.3 |"))

    def run_command(self, repo: Path) -> str:
        base = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=repo,
                              capture_output=True, text=True, check=True).stdout.strip()
        script = self.command().replace("<base_commit>", base).replace("<work_item_id>", "w1")
        done = subprocess.run(["bash", "-c", script], cwd=repo, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def scratch_repo(self, steps: list[tuple[str, dict]]) -> Path:
        """A repository with a base commit and one generation-record commit per
        step; each step is (extra key, the work item's fields at that commit)."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(git[:1] + ["init", "-q"], cwd=tmp, check=True)
        state = tmp / "docs" / "ai-workflow" / "WORKFLOW_STATE.json"
        state.parent.mkdir(parents=True)
        for number, (label, fields) in enumerate([("base", {"x": 1})] + steps):
            state.write_text(json.dumps({"work_items": {"w1": fields}}))
            subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
            message = ("base" if number == 0 else
                       f"record {label}\n\nWorkflow-Bundle-Generation-Record: w1/{number}\n"
                       "Workflow-Work-Item: w1")
            subprocess.run(git + ["commit", "-q", "-m", message], cwd=tmp, check=True)
        return tmp

    def test_the_safe_procedure_reports_each_commit_the_older_release_refuses(self):
        repo = self.scratch_repo([
            ("adds the key with a finding", {"x": 1, "optional_findings": {"F-1": "open"}}),
            ("changes a disposition in the ledger already present",
             {"x": 1, "optional_findings": {"F-1": "fixed"}}),
            ("adds the key with a null value", {"x": 1, "optional_findings": {"F-1": "fixed"},
                                                 "review_round_counts": None}),
        ])
        hashes = subprocess.run(["git", "log", "--format=%H", "--reverse"], cwd=repo,
                                capture_output=True, text=True, check=True).stdout.split()
        lines = self.run_command(repo).splitlines()
        self.assertEqual(sorted(lines), sorted([
            f"{hashes[1]} optional_findings", f"{hashes[2]} optional_findings",
            f"{hashes[3]} review_round_counts"]))

    def test_the_safe_procedure_is_silent_without_such_a_commit(self):
        repo = self.scratch_repo([("unrelated", {"x": 2}), ("unrelated again", {"x": 3})])
        self.assertEqual(self.run_command(repo), "")


class TakeoverFenceReleaseTest(unittest.TestCase):
    """Release 2.18.5 (takeover-fence): what stays true of it once a later
    release is current -- the record sentences and the release-history row."""

    CHANGED = ("docs/ai-workflow/ORCHESTRATION_PROTOCOL.md",
               "scripts/workflow_integration_test.py", "scripts/workflow_protocol.py",
               "scripts/workflow_protocol_test.py", "scripts/workflow_state.py",
               "scripts/workflow_state_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.history = (REPO_ROOT / "docs" / "release-history.md").read_text()

    def row(self) -> str:
        return next(line for line in self.history.splitlines() if line.startswith("| 2.18.5 |"))

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("takeover-fence (workflow-2.18.5)", record["rationale"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        for needle in ("2.18.4", "#82", "#55", "takeover", "guard-release",
                       "Orchestration Protocol 1.5", "v2.18.5"):
            self.assertIn(needle, self.row())
        self.assertLess(self.history.index("| 2.18.5 |"), self.history.index("| 2.18.4 |"))


class LiveGuardVisibilityReleaseTest(unittest.TestCase):
    """Release 2.18.6 (live-guard-visibility): what stays true of it once a later
    release is current -- the record sentences and the release-history row."""

    CHANGED = ("docs/ai-workflow/ORCHESTRATION_PROTOCOL.md",
               "docs/ai-workflow/dry-run/verify_372h_raw_edge_derivation.py",
               "scripts/workflow_integration_test.py", "scripts/workflow_protocol.py",
               "scripts/workflow_protocol_test.py", "scripts/workflow_state.py",
               "scripts/workflow_state_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.history = (REPO_ROOT / "docs" / "release-history.md").read_text()

    def row(self) -> str:
        return next(line for line in self.history.splitlines() if line.startswith("| 2.18.6 |"))

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("live-guard-visibility (workflow-2.18.6)", record["rationale"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        for needle in ("2.18.5", "#91", "#55", "holder", "guard_holder_is_running",
                       "Orchestration Protocol 1.5", "v2.18.6"):
            self.assertIn(needle, self.row())
        self.assertLess(self.history.index("| 2.18.6 |"), self.history.index("| 2.18.5 |"))


class CheckpointStartEngineReleaseTest(unittest.TestCase):
    """Release 2.18.7 (checkpoint-start-engine): what stays true of it once a later
    release is current -- the record sentences and the release-history row."""

    CHANGED = ("docs/ai-workflow/ORCHESTRATION_PROTOCOL.md",
               "docs/ai-workflow/dry-run/verify_372h_lock_primitive_predicate.py",
               "docs/ai-workflow/dry-run/verify_372h_raw_edge_derivation.py",
               "scripts/workflow_protocol.py", "scripts/workflow_protocol_test.py",
               "scripts/workflow_state.py", "scripts/workflow_state_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.history = (REPO_ROOT / "docs" / "release-history.md").read_text()

    def row(self) -> str:
        return next(line for line in self.history.splitlines() if line.startswith("| 2.18.7 |"))

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("checkpoint-start-engine (workflow-2.18.7)", record["rationale"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        for needle in ("2.18.6", "#95", "#55", "release_checkpoint_start", "AmbiguousCheckpointTrailerError",
                       "subreaper", "Orchestration Protocol 1.5", "v2.18.7"):
            self.assertIn(needle, self.row())
        self.assertLess(self.history.index("| 2.18.7 |"), self.history.index("| 2.18.6 |"))


class CheckpointStartCommandReleaseTest(unittest.TestCase):
    """Release 2.19.0 (checkpoint-start-command): what stays true of it once a later
    release is current -- the record sentences and the release-history row. The
    current version, constant, counts and posture are pinned by the current release's
    class (2.19.1)."""

    CHANGED = (".claude/commands/release-checkpoint-start.md",
               ".claude/commands/request-plan-amendment.md",
               "docs/ai-workflow/COMMAND_FILES.md", "docs/ai-workflow/MILESTONE_WORKFLOW.md",
               "docs/ai-workflow/ORCHESTRATION_PROTOCOL.md",
               "docs/ai-workflow/WORKFLOW_V2_1_OPERATOR_REFERENCE.md",
               "scripts/workflow_integration_test.py", "scripts/workflow_protocol.py",
               "scripts/workflow_protocol_test.py", "scripts/workflow_state.py",
               "scripts/workflow_state_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.history = (REPO_ROOT / "docs" / "release-history.md").read_text()

    def row(self) -> str:
        return next(line for line in self.history.splitlines() if line.startswith("| 2.19.0 |"))

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("checkpoint-start-command (workflow-2.19.0)", record["rationale"])

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        for needle in ("2.18.7", "#55", "/release-checkpoint-start", "checkpoint_start_release_confirmation",
                       "R-i", "R-ii", "finish an interrupted release first",
                       "Orchestration Protocol 1.5", "v2.19.0"):
            self.assertIn(needle, self.row())
        self.assertLess(self.history.index("| 2.19.0 |"), self.history.index("| 2.18.7 |"))


class InterleavingPinsReleaseTest(unittest.TestCase):
    """Release 2.19.1 (interleaving-pins): the version, the release constant, the
    counts, the digests, the downgrade posture and the release-history row."""

    CHANGED = ("docs/ai-workflow/ORCHESTRATION_PROTOCOL.md", "scripts/workflow_protocol.py",
               "scripts/workflow_protocol_test.py", "scripts/workflow_state_test.py")

    def setUp(self):
        self.manifest = json.loads((REPO_ROOT / "manifest.json").read_text())
        self.history = (REPO_ROOT / "docs" / "release-history.md").read_text()

    def row(self) -> str:
        return next(line for line in self.history.splitlines() if line.startswith("| 2.19.1 |"))

    def test_the_release_names_2_19_1_and_adds_no_record(self):
        self.assertEqual(self.manifest["workflow_version"], "2.19.1")
        by_category = {}
        for entry in self.manifest["artifacts"]:
            by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1
        counts = self.manifest["counts"]
        self.assertEqual(counts["artifacts"], len(self.manifest["artifacts"]))
        self.assertEqual(counts["templates"], len(self.manifest["templates"]))
        self.assertEqual(counts["by_category"], by_category)
        self.assertEqual((counts["artifacts"], counts["templates"]), (80, 6))
        self.assertEqual(by_category["distribution"], 54)

    def test_the_release_constant_is_the_manifest_version(self):
        text = (REPO_ROOT / "payload/scripts/workflow_protocol.py").read_text()
        self.assertIn('WORKFLOW_RELEASE = "2.19.1"', text)

    def test_every_record_changed_by_the_release_carries_its_sentence(self):
        for section in ("artifacts", "templates"):
            for record in self.manifest[section]:
                with self.subTest(record["target_path"]):
                    data = (REPO_ROOT / record["location"]).read_bytes()
                    self.assertEqual((record["sha256"], record["size"]), (_sha(data), len(data)))
        for target in self.CHANGED:
            with self.subTest(target):
                record = next(r for r in self.manifest["artifacts"] if r["target_path"] == target)
                self.assertIn("interleaving-pins (workflow-2.19.1)", record["rationale"])
        others = [r["target_path"] for r in self.manifest["artifacts"]
                  if "interleaving-pins (workflow-2.19.1)" in r["rationale"]]
        self.assertEqual(sorted(others), sorted(self.CHANGED))

    def test_the_manager_block_states_the_patch_and_the_way_back_in_the_posture(self):
        block = self.manifest["manager"]
        self.assertEqual(block["min_manager_version"], "1.13.0")
        posture = block["downgrade_boundary"]["posture"]
        for needle in ("2.19.1", "2.19.0", "Orchestration Protocol stays 1.5",
                       "workflow-manager update back to 2.19.0", "WORKFLOW_RELEASE",
                       "workflow_state_test.py", "/release-checkpoint-start",
                       "before moving back below 2.19.0", "2.14.0"):
            self.assertIn(needle, posture)
        self.assertEqual(block["downgrade_boundary"]["signals"], [])
        self.assertEqual(block["new_work_only"], [])
        self.assertEqual(block["gate_default_change"], "")

    def test_the_release_history_row_names_the_release_and_the_way_back(self):
        self.assertIn("Last checked with: Workflow 2.19.1.", self.history)
        for needle in ("2.19.0", "#97", "#100", "crash_at_unlink", "changes no behaviour",
                       "AmendmentCheckpointActiveError", "Orchestration Protocol 1.5", "v2.19.1"):
            self.assertIn(needle, self.row())
        self.assertNotIn("closes #", self.row())
        self.assertLess(self.history.index("| 2.19.1 |"), self.history.index("| 2.19.0 |"))


# -- the Manager metadata block ----------------------------------------------------

SUITE_TWO = ("import unittest\n\n\nclass T(unittest.TestCase):\n"
             "    def test_a(self):\n        pass\n\n    def test_b(self):\n        pass\n")
SUITE_ONE = ("import unittest\n\n\nclass U(unittest.TestCase):\n"
             "    @unittest.skip('counted all the same')\n"
             "    def test_a(self):\n        pass\n")
SUITE_FAILS = ("import unittest\n\n\nclass F(unittest.TestCase):\n"
               "    def test_a(self):\n        self.fail('frozen suite failure')\n")
SUITE_LOAD_ERROR = ("import unittest\n\n\nclass T(unittest.TestCase):\n"
                    "    def test_a(self):\n        pass\n\n\n"
                    "def load_tests(loader, tests, pattern):\n    raise RuntimeError('boom')\n")
MAIN_GUARD = "\n\nif __name__ == \"__main__\":\n    unittest.main()\n"
SUITE_TWO, SUITE_ONE, SUITE_FAILS = (s + MAIN_GUARD for s in (SUITE_TWO, SUITE_ONE, SUITE_FAILS))
SUITE_IMPORT_ERROR = "raise RuntimeError('does not import')\n"
WORKFLOW_TEMPLATE = ("jobs:\n  workflow-conformance:\n    steps:\n      - run: |\n"
                     "          suites=\"{suites}\"\n          echo run\n")


def conformance_workflow(*names: str) -> str:
    return WORKFLOW_TEMPLATE.format(suites=" ".join(names))


def valid_block(suites: dict[str, int] | None = None, minimum: str = "1.13.0") -> dict:
    return {
        "schema_version": 1,
        "min_manager_version": minimum,
        "downgrade_boundary": {
            "posture": "", "undetectable": None,
            "signals": [{"name": "review-baselines", "label": "a baseline directory",
                         "detect": {"kind": "state-key", "key": "review_baselines"}}]},
        "new_work_only": ["the first manual round is a full review"],
        "gate_default_change": "",
        "conformance": {"suites": {"a_test.py": 2} if suites is None else suites,
                        "portability_exceptions": []},
    }


def evidence_for(*records: tuple[str, bool, bool]) -> dict:
    return {"repository": "RodrigoFAbreu/workflow-manager", "taken": "2026-10-17",
            "releases": [{"tagName": tag, "isDraft": draft, "isPrerelease": pre,
                          "publishedAt": "2026-10-17T00:00:00Z"} for tag, draft, pre in records]}


def managed_release(root: Path, version: str, suites: dict[str, str], block: dict | None) -> None:
    """A release source whose conformance workflow names `suites` (file name ->
    source) and whose manifest carries `block` (or none)."""
    extra = {f"payload/scripts/{name}": text for name, text in suites.items()}
    extra["templates/.github/workflows/workflow-conformance.yml"] = conformance_workflow(*suites)
    write_release(root, version, extra=extra)
    manifest = json.loads((root / "manifest.json").read_text())
    if block is not None:
        manifest["manager"] = block
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


class ConcurrencyInvariantsReleaseWindowRowTest(unittest.TestCase):
    """command-wording (W3): the release-window row of the invariants page gives the
    command's acts to the command and the re-classification to the engine, and attributes
    each test pin to the class it is in."""

    def row(self) -> str:
        text = (REPO_ROOT / "docs" / "CONCURRENCY_INVARIANTS.md").read_text()
        return " ".join(next(line for line in text.splitlines()
                             if line.startswith("| **Checkpoint-start release window**")).split())

    def test_the_recovery_cell_says_the_command_observes_and_the_engine_reclassifies(self):
        row = self.row()
        self.assertIn("the command observes the claim outside (9) and, while a claim exists, "
                      "asks for the same attestation with the fresh claim; the engine then "
                      "re-classifies under (9)", row)
        self.assertNotIn("the engine re-classifies under (9) and, while a claim exists, asks", row)

    def test_the_tests_cell_puts_the_p4_pin_under_the_command_class(self):
        row = self.row()
        self.assertIn("`::TestReleaseCheckpointStartCommand` (including the `test_p4_*` pin)", row)
        self.assertIn("`::TestAmendmentResolutionReservation` (the journal refusal)", row)
        self.assertNotIn("`::TestAmendmentResolutionReservation` (the `test_p4_*` pin", row)


class ManagerBlockContractTest(unittest.TestCase):
    def problems(self, mutate) -> str:
        block = valid_block()
        mutate(block)
        return "\n".join(manager_block.validate(block))

    def test_a_complete_block_is_valid(self):
        self.assertEqual(manager_block.validate(valid_block()), [])

    def test_every_top_level_key_is_optional_but_the_schema_version(self):
        self.assertEqual(manager_block.validate({"schema_version": 1}), [])
        self.assertIn("manager.schema_version: required", "\n".join(manager_block.validate({})))

    def test_each_rule_fails_naming_its_key(self):
        signal = lambda b: b["downgrade_boundary"]["signals"][0]
        cases = [
            (lambda b: b.pop("schema_version"), "manager.schema_version: required"),
            (lambda b: b.update(schema_version=2), "manager.schema_version: must be 1"),
            (lambda b: b.update(schema_version=True), "manager.schema_version"),
            (lambda b: b.update(extra=1), "manager.extra: unknown key"),
            (lambda b: b.update(min_manager_version="1.x"), "manager.min_manager_version"),
            (lambda b: b.update(min_manager_version=1.13), "manager.min_manager_version"),
            (lambda b: b.update(min_manager_version=""), "manager.min_manager_version"),
            (lambda b: b["downgrade_boundary"].pop("posture"),
             "manager.downgrade_boundary.posture: required"),
            (lambda b: b["downgrade_boundary"].update(undetectable=3),
             "manager.downgrade_boundary.undetectable"),
            (lambda b: b["downgrade_boundary"].update(signals={}),
             "manager.downgrade_boundary.signals: must be a list"),
            (lambda b: signal(b).update(name="Bad_Name"), "signals[0].name: must be a kebab-case string"),
            (lambda b: signal(b).pop("label"), "signals[0].label: required"),
            (lambda b: signal(b).pop("detect"), "signals[0].detect: required"),
            (lambda b: signal(b).update(detect={"kind": "state-regex", "key": "x"}),
             "signals[0].detect.kind: 'state-regex' is not a detector kind"),
            (lambda b: signal(b).update(detect={"kind": []}),
             "signals[0].detect.kind: [] is not a detector kind"),
            (lambda b: signal(b).update(detect={"kind": {}}),
             "signals[0].detect.kind: {} is not a detector kind"),
            (lambda b: signal(b).update(detect={"kind": "state-key"}),
             "signals[0].detect.key: required by the 'state-key' detector"),
            (lambda b: signal(b).update(detect={"kind": "state-value", "key": "k", "value": [1]}),
             "signals[0].detect.value: must be a JSON scalar"),
            (lambda b: signal(b).update(detect={"kind": "state-value", "key": "k", "value": 1.5}),
             "signals[0].detect.value: must be a JSON scalar"),
            (lambda b: signal(b).update(detect={"kind": "item-phase", "phases": []}),
             "signals[0].detect.phases: must be a non-empty list of strings"),
            (lambda b: signal(b).update(detect={"kind": "item-governing", "value": "2.2", "key": "x"}),
             "signals[0].detect.key: unknown key"),
            (lambda b: b.update(new_work_only="text"), "manager.new_work_only"),
            (lambda b: b.update(gate_default_change=None), "manager.gate_default_change"),
            (lambda b: b["conformance"].pop("portability_exceptions"),
             "manager.conformance.portability_exceptions: required"),
            (lambda b: b["conformance"].pop("suites"), "manager.conformance.suites: required"),
            (lambda b: b.update(conformance={}), "manager.conformance.suites: required"),
            (lambda b: b["conformance"]["suites"].update({"a_test.py": -1}),
             "manager.conformance.suites['a_test.py']: must be a non-negative integer"),
            (lambda b: b["conformance"]["suites"].update({"a_test.py": True}),
             "manager.conformance.suites['a_test.py']: must be a non-negative integer"),
            (lambda b: b["conformance"]["suites"].update({"a_test.py": 1.5}),
             "manager.conformance.suites['a_test.py']"),
            (lambda b: b["conformance"].update(portability_exceptions={}),
             "manager.conformance.portability_exceptions: must be a list"),
            (lambda b: b["conformance"].update(portability_exceptions=[{"suite": "s"}]),
             "portability_exceptions[0].test: required"),
        ]
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.problems(mutate))

    def test_the_forms_the_minimum_manager_refuses_are_refused(self):
        for name, mutate in self.MANAGER_REFUSED.items():
            with self.subTest(name):
                self.assertTrue(self.problems(mutate))

    MANAGER_REFUSED = {
        "a float schema version": lambda b: b.update(schema_version=1.0),
        "a non-string item-governing value": lambda b: b["downgrade_boundary"]["signals"][0]
        .update(detect={"kind": "item-governing", "value": 2}),
        "a signal name ending in a newline": lambda b: b["downgrade_boundary"]["signals"][0]
        .update(name="signal\n"),
        "a minimum version ending in a newline": lambda b: b.update(min_manager_version="1.13.0\n"),
    }

    def test_each_detector_kind_has_a_passing_form(self):
        for detect in ({"kind": "state-key", "key": "k"},
                       {"kind": "state-value", "key": "k", "value": None},
                       {"kind": "state-value", "key": "k", "value": True},
                       {"kind": "item-governing", "value": "2.2"},
                       {"kind": "item-phase", "phases": ["IMPLEMENTING"]},
                       {"kind": "item-field", "key": "k", "value": 3}):
            with self.subTest(detect=detect):
                block = valid_block()
                block["downgrade_boundary"]["signals"][0]["detect"] = detect
                self.assertEqual(manager_block.validate(block), [])

    def test_a_portability_exception_with_optional_keys_is_valid(self):
        block = valid_block()
        block["conformance"]["portability_exceptions"] = [
            {"suite": "s_test.py", "test": "C.t", "requires": None, "reason": "r", "defect": None}]
        self.assertEqual(manager_block.validate(block), [])

    def test_a_non_object_is_refused(self):
        self.assertEqual(manager_block.validate([]), ["manager: must be an object"])


class ManagerEvidenceTest(unittest.TestCase):
    def test_only_an_exact_published_vxyz_tag_counts(self):
        evidence = evidence_for(
            ("v1.12.0", False, False), ("v1.13.0", False, False),
            ("v1.14.0", True, False), ("v1.15.0", False, True),
            ("workflow-manager-v1.0.0", False, False), ("v2.0.0-rc1", False, False),
            ("v9.9", False, False))
        self.assertEqual(manager_block.validate_evidence(evidence), [])
        self.assertEqual(manager_block.published_versions(evidence), ["1.12.0", "1.13.0"])
        self.assertEqual(manager_block.newest_published(evidence), "1.13.0")

    def test_a_tag_with_a_trailing_newline_does_not_count(self):
        evidence = evidence_for(("v1.12.0", False, False), ("v1.13.0\n", False, False))
        self.assertEqual(manager_block.published_versions(evidence), ["1.12.0"])

    def test_the_newest_is_numeric_not_textual(self):
        evidence = evidence_for(("v1.9.0", False, False), ("v1.10.0", False, False))
        self.assertEqual(manager_block.newest_published(evidence), "1.10.0")

    def test_a_record_lacking_a_field_makes_the_evidence_invalid(self):
        for missing in ("isDraft", "isPrerelease", "publishedAt", "tagName"):
            with self.subTest(missing=missing):
                evidence = evidence_for(("v1.13.0", False, False))
                del evidence["releases"][0][missing]
                problems = manager_block.validate_evidence(evidence)
                self.assertTrue(any(f"releases[0].{missing}: required" in p for p in problems),
                                problems)

    def test_other_malformed_evidence_is_invalid(self):
        self.assertTrue(manager_block.validate_evidence([]))
        self.assertTrue(manager_block.validate_evidence(dict(evidence_for(), taken="yesterday")))
        self.assertTrue(manager_block.validate_evidence(
            evidence_for(("v1.0.0", False, False), ("v1.0.0", False, False))))
        bad = evidence_for(("v1.0.0", False, False))
        bad["releases"][0]["isDraft"] = "no"
        self.assertTrue(manager_block.validate_evidence(bad))


class ManagerCheckTest(unittest.TestCase):
    EVIDENCE = evidence_for(("v1.12.0", False, False), ("v1.13.0", False, False))

    def manifest(self, block="default"):
        manifest = {"workflow_version": "2.13.0"}
        if block is not None:
            manifest["manager"] = valid_block({"a_test.py": 2}) if block == "default" else block
        return manifest

    def check(self, manifest, measured=None, version="2.13.0", evidence=None):
        return manager_block.check(manifest, version, {"a_test.py": 2} if measured is None
                                   else measured, self.EVIDENCE if evidence is None else evidence)

    def test_a_good_release_has_no_problem(self):
        self.assertEqual(self.check(self.manifest()), [])

    def test_a_block_in_2_12_0_or_older_is_refused_and_no_block_there_is_fine(self):
        for version in ("2.12.0", "2.3.1", "1.0.0"):
            with self.subTest(version=version):
                self.assertTrue(any("never gain one" in p for p in self.check(
                    self.manifest(), version=version)))
                self.assertEqual(self.check(self.manifest(None), version=version), [])

    def test_a_missing_block_in_a_newer_manifest_is_refused(self):
        for version in ("2.12.1", "2.13.0", "3.0.0"):
            with self.subTest(version=version):
                self.assertTrue(any("has no manager block" in p for p in self.check(
                    self.manifest(None), version=version)))

    def test_an_invalid_block_is_reported_before_anything_else(self):
        block = valid_block({"a_test.py": 2})
        block["schema_version"] = 3
        self.assertIn("manager.schema_version", "\n".join(self.check(self.manifest(block))))

    def test_a_version_with_a_trailing_newline_is_refused(self):
        problems = self.check(self.manifest(), version="2.13.0\n")
        self.assertEqual(problems, ["version '2.13.0\\n' is not X.Y.Z"])

    def test_suites_must_equal_the_measurement(self):
        problems = "\n".join(self.check(self.manifest(), measured={"a_test.py": 3, "b_test.py": 1}))
        self.assertIn("a_test.py recorded 2, measured 3", problems)
        self.assertIn("b_test.py recorded absent, measured 1", problems)

    def test_the_count_refusal_names_a_command_the_real_parser_accepts(self):
        import re
        message = "\n".join(self.check(self.manifest(), measured={"a_test.py": 3}))
        printed = re.search(r"`python3 tools/release/release\.py ([^`]+)`", message)
        self.assertIsNotNone(printed, message)
        args = release._parser().parse_args(printed.group(1).split())
        self.assertEqual((args.commit, args.write), ("HEAD", True))
        self.assertIn("--release-dir <staged-release>", message)
        args = release._parser().parse_args(
            ["manager-block", "--release-dir", "staged", "--write"])
        self.assertEqual((args.release_dir, args.write), (Path("staged"), True))

    def test_a_block_without_suites_is_refused_once_measured(self):
        block = valid_block()
        del block["conformance"]
        self.assertIn("manager.conformance", "\n".join(self.check(self.manifest(block))))
        self.assertIn("manager.conformance.suites: required in a release's block",
                      "\n".join(self.check(self.manifest({"schema_version": 1}))))

    def test_the_minimum_manager_must_be_published(self):
        def with_minimum(minimum):
            return self.manifest(dict(valid_block({"a_test.py": 2}), min_manager_version=minimum))
        self.assertIn("is newer than the newest published Manager release 1.13.0",
                      "\n".join(self.check(with_minimum("1.14.0"))))
        self.assertEqual(self.check(with_minimum("1.13.0")), [])
        self.assertEqual(self.check(with_minimum("1.2.0")), [])

    def test_a_draft_a_prerelease_and_a_prefixed_tag_do_not_satisfy_the_minimum(self):
        evidence = evidence_for(("v1.12.0", False, False), ("v1.13.0", True, False),
                                ("v1.13.1", False, True),
                                ("workflow-manager-v1.13.2", False, False))
        self.assertIn("newest published Manager release 1.12.0",
                      "\n".join(self.check(self.manifest(), evidence=evidence)))

    def test_invalid_evidence_is_a_problem_never_a_pass(self):
        evidence = evidence_for(("v1.13.0", False, False))
        del evidence["releases"][0]["isPrerelease"]
        problems = self.check(self.manifest(), evidence=evidence)
        self.assertTrue(any("isPrerelease: required" in p for p in problems), problems)
        self.assertTrue(self.check(self.manifest(), evidence=evidence_for()))

    def test_the_pin_must_equal_the_minimum(self):
        block = valid_block()
        self.assertEqual(manager_block.check_pin(block, {"version": "1.13.0"}), [])
        self.assertIn("pins Manager '1.12.0'", manager_block.check_pin(
            block, {"version": "1.12.0"})[0])
        self.assertTrue(manager_block.check_pin(block, None))
        self.assertEqual(manager_block.check_pin({"schema_version": 1}, None), [])


class MeasureSuitesTest(unittest.TestCase):
    def fixture(self, suites: dict[str, str], names: list[str] | None = None) -> Path:
        root = Path(tempfile.mkdtemp(prefix="measure-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / ".github/workflows").mkdir(parents=True)
        (root / "scripts").mkdir()
        (root / ".github/workflows/workflow-conformance.yml").write_text(
            conformance_workflow(*(names if names is not None else suites)))
        for name, text in suites.items():
            (root / "scripts" / name).write_text(text)
        return root

    def test_it_counts_what_unittest_loads(self):
        fixture = self.fixture({"a_test.py": SUITE_TWO, "b_test.py": SUITE_ONE})
        self.assertEqual(manager_block.measure_suites(fixture), {"a_test.py": 2, "b_test.py": 1})
        self.assertFalse(list((fixture / "scripts").glob("__pycache__")), "bytecode was written")

    def test_a_demo_suite_the_workflow_does_not_name_is_ignored(self):
        fixture = self.fixture({"a_test.py": SUITE_TWO, "x_demo_test.py": SUITE_TWO},
                               names=["a_test.py"])
        self.assertEqual(manager_block.measure_suites(fixture), {"a_test.py": 2})

    def test_it_agrees_with_a_plain_unittest_run(self):
        fixture = self.fixture({"a_test.py": SUITE_TWO})
        proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "a_test"],
                              cwd=fixture / "scripts", capture_output=True, text=True)
        self.assertIn("Ran 2 tests", proc.stderr)
        self.assertEqual(manager_block.measure_suites(fixture), {"a_test.py": 2})

    def test_a_loader_error_is_refused(self):
        fixture = self.fixture({"a_test.py": SUITE_LOAD_ERROR})
        with self.assertRaisesRegex(manager_block.MeasureError, "a_test.py has loader errors"):
            manager_block.measure_suites(fixture)

    def test_a_suite_that_does_not_import_is_refused(self):
        fixture = self.fixture({"a_test.py": SUITE_IMPORT_ERROR})
        with self.assertRaisesRegex(manager_block.MeasureError, "counting the suites failed"):
            manager_block.measure_suites(fixture)

    def test_a_named_suite_that_is_missing_is_refused(self):
        fixture = self.fixture({"a_test.py": SUITE_TWO}, names=["a_test.py", "gone_test.py"])
        with self.assertRaisesRegex(manager_block.MeasureError, "gone_test.py"):
            manager_block.measure_suites(fixture)

    def test_the_workflow_must_name_its_suites_exactly_once(self):
        fixture = self.fixture({"a_test.py": SUITE_TWO})
        workflow = fixture / ".github/workflows/workflow-conformance.yml"
        workflow.write_text(workflow.read_text() * 2)
        with self.assertRaisesRegex(manager_block.MeasureError, "2 suites"):
            manager_block.measure_suites(fixture)
        workflow.write_text("jobs: {}\n")
        with self.assertRaisesRegex(manager_block.MeasureError, "0 suites"):
            manager_block.measure_suites(fixture)
        workflow.unlink()
        with self.assertRaisesRegex(manager_block.MeasureError, "has no .github"):
            manager_block.measure_suites(fixture)


class ManagerBlockCliTest(ScratchTestCase):
    SUITES = {"a_test.py": SUITE_TWO, "b_test.py": SUITE_ONE}
    COUNTS = {"a_test.py": 2, "b_test.py": 1}

    def setUp(self):
        super().setUp()
        self.evidence = self.tmp / "manager-releases.json"
        self.evidence.write_text(json.dumps(evidence_for(("v1.13.0", False, False))))

    def commit_release(self, version="2.13.0", block="default", pin="1.13.0") -> str:
        managed_release(self.repo.root, version, self.SUITES,
                        valid_block(self.COUNTS) if block == "default" else block)
        self.repo.touch("tools/release/manager-pin.json", json.dumps({"version": pin}))
        return self.repo.commit(f"release {version}")

    def test_check_accepts_a_good_release(self):
        commit = self.commit_release()
        out = self.assert_ok("check-manager-block", "--commit", commit,
                             "--manager-releases", str(self.evidence))
        self.assertIn("matches the measurement", out)

    def test_check_accepts_a_release_up_to_2_12_0_with_no_block(self):
        commit = self.commit_release("2.12.0", block=None)
        out = self.assert_ok("check-manager-block", "--commit", commit,
                             "--manager-releases", str(self.evidence))
        self.assertIn("has no manager block", out)

    def test_check_refuses_each_problem(self):
        wrong = dict(self.COUNTS, **{"a_test.py": 9})
        cases = {
            "a block in 2.12.0": dict(version="2.12.0", block=valid_block(self.COUNTS)),
            "no block in 2.13.0": dict(block=None),
            "counts differ": dict(block=valid_block(wrong)),
            "minimum unpublished": dict(
                block=dict(valid_block(self.COUNTS), min_manager_version="1.14.0"), pin="1.14.0"),
            "pin differs": dict(pin="1.12.0"),
            "invalid block": dict(block=dict(valid_block(self.COUNTS), schema_version=2)),
        }
        for name, kwargs in cases.items():
            with self.subTest(name):
                self.reset_repo()
                commit = self.commit_release(**kwargs)
                self.assert_refused("check-manager-block", "--commit", commit,
                                    "--manager-releases", str(self.evidence),
                                    naming=("is not valid",))

    def test_check_refuses_the_forms_the_minimum_manager_refuses(self):
        for name, mutate in ManagerBlockContractTest.MANAGER_REFUSED.items():
            with self.subTest(name):
                self.reset_repo()
                block = valid_block(self.COUNTS)
                mutate(block)
                commit = self.commit_release(block=block)
                self.assert_refused("check-manager-block", "--commit", commit,
                                    "--manager-releases", str(self.evidence),
                                    naming=("is not valid",))

    def reset_repo(self):
        shutil.rmtree(self.repo.root)
        self.repo = ScratchRepo(self.repo.root)

    def test_check_names_the_unreadable_evidence(self):
        commit = self.commit_release()
        self.assert_refused("check-manager-block", "--commit", commit,
                            "--manager-releases", str(self.tmp / "absent.json"),
                            naming=("cannot read the Manager release list",))

    def test_manager_block_release_dir_equals_commit(self):
        commit = self.commit_release()
        by_commit = self.assert_ok("manager-block", "--commit", commit)
        staged = package.stage(self.repo.root, commit, self.tmp / "staged")
        by_dir = self.assert_ok("manager-block", "--release-dir", str(staged))
        self.assertEqual(json.loads(by_commit), self.COUNTS)
        self.assertEqual(by_commit, by_dir)

    def test_manager_block_measures_a_directory_whose_commit_does_not_exist_yet(self):
        managed_release(self.tmp / "tree", "2.13.0", self.SUITES, valid_block({}))
        out = self.assert_ok("manager-block", "--release-dir", str(self.tmp / "tree"))
        self.assertEqual(json.loads(out), self.COUNTS)

    def test_commit_is_refused_while_its_digests_do_not_match(self):
        self.commit_release()
        (self.repo.root / "payload/scripts/a_test.py").write_text(SUITE_ONE)
        commit = self.repo.commit("drift")
        self.assert_refused("manager-block", "--commit", commit, naming=("digest mismatch",))

    def test_write_replaces_only_suites_and_keeps_every_other_byte(self):
        commit = self.commit_release(block=valid_block({"stale_test.py": 7, "a_test.py": 2}))
        manifest = self.repo.root / "manifest.json"
        before = manifest.read_text()
        self.assert_ok("manager-block", "--commit", commit, "--write")
        after = manifest.read_text()
        self.assertNotEqual(before, after)
        old, new = json.loads(before), json.loads(after)
        self.assertEqual(new["manager"]["conformance"]["suites"], self.COUNTS)
        old["manager"]["conformance"]["suites"] = new["manager"]["conformance"]["suites"]
        self.assertEqual(old, new)
        # Every byte outside the suites object is unchanged.
        head, _, tail = before.partition('      "suites": ')
        self.assertTrue(after.startswith(head + '      "suites": '))
        self.assertEqual(after.partition('      "suites": ')[2].partition("\n      }")[2],
                         tail.partition("\n      }")[2])
        self.assertEqual(after, json.dumps(new, indent=2) + "\n")
        self.assert_ok("manager-block", "--commit", commit, "--write")
        self.assertEqual(manifest.read_text(), after)

    def test_write_refuses_a_manifest_up_to_2_12_0(self):
        commit = self.commit_release("2.12.0", block=valid_block(self.COUNTS))
        before = (self.repo.root / "manifest.json").read_text()
        self.assert_refused("manager-block", "--commit", commit, "--write",
                            naming=("never gets a manager block",))
        self.assertEqual((self.repo.root / "manifest.json").read_text(), before)

    def test_write_refuses_a_manifest_with_no_block_to_fill(self):
        commit = self.commit_release("2.13.0", block=None)
        before = (self.repo.root / "manifest.json").read_text()
        self.assert_refused("manager-block", "--commit", commit, "--write",
                            naming=("no top-level manager block",))
        self.assertEqual((self.repo.root / "manifest.json").read_text(), before)

    def test_write_refuses_a_block_with_no_suites_to_replace(self):
        block = valid_block()
        del block["conformance"]["suites"]
        commit = self.commit_release(block=block)
        self.assert_refused("manager-block", "--commit", commit, "--write",
                            naming=("no suites to replace",))

    def test_exactly_one_source_is_required(self):
        code, _, err = self.cli("manager-block")
        self.assertEqual(code, release.EXIT_USAGE, err)
        code, _, err = self.cli("manager-block", "--commit", "HEAD", "--release-dir", "x")
        self.assertEqual(code, release.EXIT_USAGE, err)


class ManagerEvidenceCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="manager-evidence-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def listing(self, name: str, records) -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(records))
        return path

    def gh(self, *versions, draft=(), pre=()):
        return [{"tagName": f"v{v}", "isDraft": v in draft, "isPrerelease": v in pre,
                 "publishedAt": "2026-10-17T00:00:00Z"} for v in versions]

    def record(self, records):
        out = self.tmp / "saved.json"
        code, text, err = run_cli("record-manager-releases", "--out", str(out), "--listing",
                                  str(self.listing("gh.json", records)), "--taken", "2026-10-17")
        return code, out, err

    def test_record_writes_the_exact_format(self):
        code, out, err = self.record(self.gh("1.13.0", "1.2.0", draft=("1.2.0",)))
        self.assertEqual(code, release.EXIT_OK, err)
        saved = json.loads(out.read_text())
        self.assertEqual(saved["repository"], "RodrigoFAbreu/workflow-manager")
        self.assertEqual(saved["taken"], "2026-10-17")
        self.assertEqual([r["tagName"] for r in saved["releases"]], ["v1.13.0", "v1.2.0"])
        self.assertEqual(set(saved["releases"][0]),
                         {"tagName", "isDraft", "isPrerelease", "publishedAt"})
        self.assertEqual(manager_block.validate_evidence(saved), [])
        self.assertEqual(manager_block.newest_published(saved), "1.13.0")
        self.assertTrue(out.read_text().endswith("\n"))

    def test_record_refuses_an_incomplete_listing(self):
        records = self.gh("1.13.0")
        del records[0]["isPrerelease"]
        code, out, err = self.record(records)
        self.assertEqual(code, release.EXIT_FAIL)
        self.assertIn("isPrerelease: required", err)
        self.assertFalse(out.exists())

    def test_record_refuses_a_listing_that_is_not_a_list(self):
        code, out, err = self.record({"tagName": "v1.0.0"})
        self.assertEqual(code, release.EXIT_FAIL)
        self.assertIn("not a JSON list", err)

    def test_validation_needs_no_network(self):
        # The offline check reads the committed evidence only: with no `gh` and
        # no way to reach anything, it still decides.
        evidence = evidence_for(("v1.13.0", False, False))
        real_run, real_popen = subprocess.run, subprocess.Popen

        def refuse(*args, **kwargs):
            raise AssertionError(f"the offline check ran a subprocess: {args}")
        subprocess.run = subprocess.Popen = refuse
        try:
            self.assertEqual(manager_block.validate_evidence(evidence), [])
            self.assertEqual(manager_block.check(
                {"workflow_version": "2.13.0", "manager": valid_block({"a_test.py": 2})},
                "2.13.0", {"a_test.py": 2}, evidence), [])
        finally:
            subprocess.run, subprocess.Popen = real_run, real_popen

    def compare(self, saved_versions, live) -> tuple[int, str, str]:
        saved = self.tmp / "committed.json"
        saved.write_text(json.dumps(
            evidence_for(*[(f"v{v}", False, False) for v in saved_versions])))
        args = ["compare-manager-releases", "--manager-releases", str(saved)]
        if live is not None:
            args += ["--live", str(live)]
        return run_cli(*args)

    def test_compare_distinguishes_consistent_behind_and_unavailable(self):
        code, out, err = self.compare(["1.12.0", "1.13.0"], self.listing(
            "live.json", self.gh("1.12.0", "1.13.0")))
        self.assertEqual((code, out.strip()), (release.EXIT_OK, "outcome=consistent"), err)

        code, out, err = self.compare(["1.12.0"], self.listing(
            "live.json", self.gh("1.12.0", "1.13.0")))
        self.assertEqual(code, release.EXIT_OK, err)
        self.assertIn("outcome=snapshot-behind", out)
        self.assertIn("::warning::", out)
        self.assertIn("1.13.0", out)

        code, out, err = self.compare(["1.12.0"], self.tmp / "no-such-file.json")
        self.assertEqual(code, release.EXIT_OK, err)
        self.assertIn("outcome=unavailable", out)
        self.assertIn("::notice::", out)

        bad = self.tmp / "bad-live.json"
        bad.write_text("<html>rate limited</html>")
        code, out, err = self.compare(["1.12.0"], bad)
        self.assertEqual(code, release.EXIT_OK, err)
        self.assertIn("outcome=unavailable", out)

    def test_compare_ignores_a_live_draft_prerelease_and_prefixed_tag(self):
        live = self.listing("live.json", self.gh(
            "1.12.0", "1.13.0", "1.14.0", draft=("1.13.0",), pre=("1.14.0",)) + [
            {"tagName": "workflow-manager-v1.0.0", "isDraft": False, "isPrerelease": False,
             "publishedAt": "x"}])
        code, out, err = self.compare(["1.12.0"], live)
        self.assertEqual((code, out.strip()), (release.EXIT_OK, "outcome=consistent"), err)

    def test_compare_fails_only_on_invalid_saved_evidence(self):
        saved = self.tmp / "committed.json"
        records = evidence_for(("v1.13.0", False, False))
        del records["releases"][0]["isDraft"]
        saved.write_text(json.dumps(records))
        code, out, err = run_cli("compare-manager-releases", "--manager-releases", str(saved),
                                 "--live", str(self.tmp / "none.json"))
        self.assertEqual(code, release.EXIT_FAIL)
        self.assertIn("isDraft: required", err)

    def test_the_committed_evidence_is_valid_and_complete(self):
        evidence = json.loads((HERE / "manager-releases.json").read_text())
        self.assertEqual(manager_block.validate_evidence(evidence), [])
        self.assertIsNotNone(manager_block.newest_published(evidence))


class UpdateFixtureTest(ScratchTestCase):
    """The pre-publish update fixture, with a stand-in Manager that records
    what it was asked and installs a release directory's files."""

    MANAGER = '''#!/usr/bin/env python3
import json, shutil, sys
from pathlib import Path
args = sys.argv[1:]
assert args[0] == "--release-dir"
release, command, target = Path(args[1]), args[2], Path(args[3])
with open(Path(__file__).with_name("calls.log"), "a") as log:
    log.write(json.dumps([command, release.name]) + "\\n")
if command == "verify":
    sys.exit(0)
manifest = json.loads((release / "manifest.json").read_text())
for record in manifest["artifacts"] + manifest["templates"]:
    if record["target_path"].endswith(".workflow-fragment"):
        continue
    dest = target / record["target_path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(release / record["location"], dest)
print(command, "ok")
'''

    def setUp(self):
        super().setUp()
        self.manager = self.tmp / "manager" / "workflow-manager"
        self.manager.parent.mkdir()
        self.manager.write_text(self.MANAGER)
        self.manager.chmod(0o755)

    def previous_assets(self, version="2.12.0") -> Path:
        source = self.tmp / "previous-source"
        managed_release(source, version, {"a_test.py": SUITE_ONE}, None)
        out = self.tmp / "previous-assets"
        package.build(source, out)
        return out

    def run_fixture(self, candidate_suites, previous="2.12.0"):
        managed_release(self.repo.root, "2.13.0", candidate_suites, valid_block({}))
        commit = self.repo.commit("candidate")
        return self.cli("update-fixture", "--commit", commit, "--previous-assets",
                        str(self.previous_assets(previous)), "--previous-version", previous,
                        "--manager", str(self.manager))

    def calls(self):
        text = (self.manager.parent / "calls.log").read_text()
        return [json.loads(line) for line in text.splitlines()]

    def test_it_bootstraps_updates_runs_the_suites_and_verifies(self):
        code, out, err = self.run_fixture({"a_test.py": SUITE_TWO, "b_test.py": SUITE_ONE})
        self.assertEqual(code, release.EXIT_OK, out + err)
        self.assertEqual(self.calls(), [["bootstrap", "workflow-2.12.0"],
                                        ["update", "candidate"], ["verify", "candidate"]])
        self.assertIn("ok   a_test.py", out)
        self.assertIn("ok   b_test.py", out)
        self.assertIn("2.12.0 -> 2.13.0 updates cleanly and its 2 suites pass", out)

    def test_a_failing_frozen_suite_fails_the_fixture(self):
        code, out, err = self.run_fixture({"a_test.py": SUITE_TWO, "b_test.py": SUITE_FAILS})
        self.assertEqual(code, release.EXIT_FAIL, out)
        self.assertIn("FAIL b_test.py", out)
        self.assertIn("frozen suites failed in the updated repository: b_test.py", err)
        self.assertNotIn(["verify", "candidate"], self.calls())

    def test_the_candidates_bytes_are_what_runs_in_the_updated_repository(self):
        # The previous release has a passing a_test.py; the candidate's, which
        # `update` installs over it, fails.
        code, out, err = self.run_fixture({"a_test.py": SUITE_FAILS})
        self.assertEqual(code, release.EXIT_FAIL, out)
        self.assertIn("FAIL a_test.py", out)

    def test_a_manager_failure_is_reported(self):
        self.manager.write_text(self.MANAGER.replace(
            'print(command, "ok")', 'sys.stderr.write("no\\n"); sys.exit(3)'))
        code, out, err = self.run_fixture({"a_test.py": SUITE_TWO})
        self.assertEqual(code, release.EXIT_FAIL)
        self.assertIn("bootstrapping 2.12.0 failed (exit 3)", err)

    def test_the_previous_version_must_be_x_y_z(self):
        managed_release(self.repo.root, "2.13.0", {"a_test.py": SUITE_TWO}, valid_block({}))
        commit = self.repo.commit("candidate")
        self.assert_refused("update-fixture", "--commit", commit, "--previous-assets",
                            str(self.tmp), "--previous-version", "latest",
                            "--manager", str(self.manager), naming=("is not X.Y.Z",))

    # ---- --keep: build the updated repository and stop; CI runs the suites and verify ----

    def scheduler_workflow(self, names) -> Path:
        """A stand-in for `workflow-ci.yml` whose scheduler step runs `names`."""
        path = self.tmp / "scheduler" / "workflow-ci.yml"
        path.parent.mkdir(exist_ok=True)
        path.write_text("".join(f'          suites="{" ".join(names)}"\n' for _ in range(2)))
        return path

    def run_kept(self, candidate_suites, keep, previous="2.12.0", scheduler=None):
        managed_release(self.repo.root, "2.13.0", candidate_suites, valid_block({}))
        commit = self.repo.commit("candidate")
        scheduler = self.scheduler_workflow(candidate_suites if scheduler is None else scheduler)
        return self.cli("update-fixture", "--commit", commit, "--previous-assets",
                        str(self.previous_assets(previous)), "--previous-version", previous,
                        "--manager", str(self.manager), "--keep", str(keep),
                        "--scheduler-workflow", str(scheduler))

    def test_keep_leaves_the_updated_repository_and_runs_neither_suites_nor_verify(self):
        keep = self.tmp / "kept"
        # A suite that fails is not run here: CI runs it, with the scheduler.
        code, out, err = self.run_kept({"a_test.py": SUITE_FAILS, "b_test.py": SUITE_TWO}, keep)
        self.assertEqual(code, release.EXIT_OK, out + err)
        self.assertEqual(self.calls(), [["bootstrap", "workflow-2.12.0"], ["update", "candidate"]])
        self.assertNotIn("FAIL", out)
        self.assertNotIn("ok   a_test.py", out)
        self.assertEqual(self.outputs(out)["updated"], str(keep))
        self.assertIn("2.12.0 -> 2.13.0 updates cleanly; the updated repository, with 2 suites",
                      out)
        self.assertTrue((keep / ".git").is_dir())
        self.assertEqual((keep / "scripts/a_test.py").read_text(), SUITE_FAILS)
        self.assertEqual((keep / "scripts/b_test.py").read_text(), SUITE_TWO)
        log = subprocess.run(["git", "-C", str(keep), "log", "--format=%s"], check=True,
                             capture_output=True, text=True).stdout.split()
        self.assertEqual(log, ["update", "bootstrap"])
        self.assertEqual(subprocess.run(["git", "-C", str(keep), "status", "--porcelain"],
                                        check=True, capture_output=True, text=True).stdout, "")

    def test_keep_takes_an_empty_directory_and_creates_a_missing_one(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        code, out, err = self.run_kept({"a_test.py": SUITE_TWO}, empty)
        self.assertEqual(code, release.EXIT_OK, out + err)
        self.assertTrue((empty / "scripts/a_test.py").is_file())
        code, out, err = self.run_kept({"a_test.py": SUITE_TWO}, self.tmp / "nested" / "new")
        self.assertEqual(code, release.EXIT_OK, out + err)
        self.assertTrue((self.tmp / "nested" / "new" / "scripts/a_test.py").is_file())

    def test_keep_refuses_a_directory_that_is_not_empty_and_a_file(self):
        full = self.tmp / "full"
        full.mkdir()
        (full / "stray").write_text("x\n")
        managed_release(self.repo.root, "2.13.0", {"a_test.py": SUITE_TWO}, valid_block({}))
        commit = self.repo.commit("candidate")
        for keep in (full, full / "stray"):
            with self.subTest(keep=keep):
                err = self.assert_refused(
                    "update-fixture", "--commit", commit, "--previous-assets",
                    str(self.previous_assets()), "--previous-version", "2.12.0",
                    "--manager", str(self.manager), "--keep", str(keep),
                    naming=("is not an empty directory",))
                self.assertEqual((full / "stray").read_text(), "x\n")
        self.assertFalse((self.manager.parent / "calls.log").exists())

    def test_keep_refuses_an_updated_repository_whose_suites_are_not_the_schedulers(self):
        both = {"a_test.py": SUITE_TWO, "b_test.py": SUITE_ONE}
        for scheduler, naming in ((["a_test.py"], "runs a_test.py:"),
                                  (["a_test.py", "b_test.py", "c_test.py"], "c_test.py"),
                                  (["a_test.py", "c_test.py"], "c_test.py")):
            with self.subTest(scheduler=scheduler):
                keep = self.tmp / f"kept-{len(scheduler)}-{naming[:1]}"
                code, out, err = self.run_kept(both, keep, scheduler=scheduler)
                self.assertEqual(code, release.EXIT_FAIL, out)
                self.assertIn("names a_test.py b_test.py, but the scheduler step of", err)
                self.assertIn(naming, err)
                self.assertNotIn("updated=", out)

    def test_keep_takes_the_suites_in_any_order(self):
        code, out, err = self.run_kept({"a_test.py": SUITE_TWO, "b_test.py": SUITE_ONE},
                                       self.tmp / "kept", scheduler=["b_test.py", "a_test.py"])
        self.assertEqual(code, release.EXIT_OK, out + err)

    def test_the_scheduler_suites_come_from_every_suites_line_of_the_workflow(self):
        path = self.scheduler_workflow(["a_test.py", "b_test.py"])
        self.assertEqual(release.scheduler_suites(path), ["a_test.py", "b_test.py"])
        path.write_text(path.read_text() + '          suites="a_test.py"\n')
        with self.assertRaisesRegex(release.ReleaseError, "must name one non-empty"):
            release.scheduler_suites(path)
        path.write_text("no suites here\n")
        with self.assertRaisesRegex(release.ReleaseError, "must name one non-empty"):
            release.scheduler_suites(path)
        with self.assertRaisesRegex(release.ReleaseError, "cannot read the scheduler workflow"):
            release.scheduler_suites(self.tmp / "missing.yml")

    def test_the_default_scheduler_is_the_workflow_ci_workflow_and_names_the_nine_suites(self):
        self.assertEqual(release.SCHEDULER_WORKFLOW, REPO_ROOT / ".github/workflows/workflow-ci.yml")
        self.assertEqual(len(release.scheduler_suites(release.SCHEDULER_WORKFLOW)), 9)

    def test_keep_still_reports_a_manager_failure(self):
        self.manager.write_text(self.MANAGER.replace(
            'print(command, "ok")', 'sys.stderr.write("no\\n"); sys.exit(3)'))
        code, out, err = self.run_kept({"a_test.py": SUITE_TWO}, self.tmp / "kept")
        self.assertEqual(code, release.EXIT_FAIL)
        self.assertIn("bootstrapping 2.12.0 failed (exit 3)", err)

    # ---- the CI step around it, run for real with stand-in `gh` and Manager ----

    def run_ci_step(self, releases, block):
        """`Update the previous release to HEAD`, then (when it built) the verify step."""
        text = (REPO_ROOT / ".github/workflows/workflow-ci.yml").read_text()
        job = _job_section(text, "update-fixture")
        # The step passes no --scheduler-workflow: the candidate names the real nine suites.
        managed_release(self.repo.root, "2.13.0",
                        {n: SUITE_FAILS for n in release.scheduler_suites(release.SCHEDULER_WORKFLOW)},
                        valid_block({}) if block else None)
        self.repo.commit("candidate")
        (self.repo.root / "tools").symlink_to(REPO_ROOT / "tools")
        previous = self.previous_assets()
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        python = bin_dir / "python3"
        python.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n')
        gh = bin_dir / "gh"
        gh.write_text('#!/bin/sh\necho "$@" >> "$0.log"\n'
                      'test "$1 $2" = "release download" || exit 9\n'
                      'mkdir -p "$5"\n'
                      f'cp {shlex.quote(str(previous))}/* "$5"\n')
        for stub in (python, gh):
            stub.chmod(0o755)
        runner, output = self.tmp / "runner", self.tmp / "github-output"
        runner.mkdir()
        listing = [{"tagName": t, "isDraft": False, "isPrerelease": False} for t in releases]
        (runner / "releases.json").write_text(json.dumps(listing))
        env = dict(os.environ, PATH=f"{bin_dir}:{self.manager.parent}:{os.environ['PATH']}",
                   RUNNER_TEMP=str(runner), GITHUB_OUTPUT=str(output), GH_TOKEN="x")
        run = lambda script: subprocess.run(["bash", "-eo", "pipefail", "-c", script], env=env,
                                            cwd=self.repo.root, capture_output=True, text=True)
        update = run(_step_script(job, "Update the previous release to HEAD"))
        built = output.read_text() if output.exists() else ""
        verify = re.search(r"\n        run: (workflow-manager --release-dir .*)\n", job).group(1)
        return update, built, runner, gh, lambda: run(verify)

    def test_the_ci_step_builds_the_update_for_the_highest_earlier_release(self):
        update, built, runner, gh, run = self.run_ci_step(["v2.11.0", "v2.12.0", "v2.13.0"], True)
        self.assertEqual(update.returncode, 0, update.stdout + update.stderr)
        self.assertEqual(built, "built=true\n")
        self.assertEqual(Path(str(gh) + ".log").read_text().split()[:3],
                         ["release", "download", "v2.12.0"])
        self.assertEqual(self.calls(), [["bootstrap", "workflow-2.12.0"], ["update", "candidate"]])
        self.assertEqual((runner / "fixture/scripts/workflow_protocol_test.py").read_text(),
                         SUITE_FAILS)
        verify = run()
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        self.assertEqual(self.calls()[-1], ["verify", "candidate"])

    def test_the_ci_step_has_nothing_to_test_without_a_block(self):
        update, built, runner, gh, _ = self.run_ci_step(["v2.12.0"], False)
        self.assertEqual(update.returncode, 0, update.stdout + update.stderr)
        self.assertIn("no manager block, or no earlier published release; nothing to update-test",
                      update.stdout)
        self.assertEqual(built, "built=false\n")
        self.assertFalse(Path(str(gh) + ".log").exists())
        self.assertFalse((runner / "fixture").exists())

    def test_the_ci_step_has_nothing_to_test_without_an_earlier_release(self):
        update, built, runner, gh, _ = self.run_ci_step(["v2.13.0", "v2.14.0"], True)
        self.assertEqual(update.returncode, 0, update.stdout + update.stderr)
        self.assertIn("nothing to update-test", update.stdout)
        self.assertEqual(built, "built=false\n")
        self.assertFalse(Path(str(gh) + ".log").exists())

    def test_the_ci_step_fails_when_the_update_fails(self):
        self.manager.write_text(self.MANAGER.replace(
            'print(command, "ok")', 'sys.stderr.write("no\\n"); sys.exit(3)'))
        update, built, *_ = self.run_ci_step(["v2.12.0"], True)
        self.assertNotEqual(update.returncode, 0)
        self.assertEqual(built, "")


class CandidateSuitesDecisionTest(ScratchTestCase):
    """`release.py release-source-changed`: `Workflow CI`'s `changes` job. Only a pull request
    can skip the candidate-suite jobs; everything that cannot be decided runs them."""

    def setUp(self):
        super().setUp()
        self.repo.release_commit("2.13.0", "base")

    def decide(self, event="pull_request", *extra):
        code, out, err = self.cli("release-source-changed", "--event", event, *extra)
        self.assertEqual(code, release.EXIT_OK, out + err)
        return self.outputs(out)

    def change(self, path, text="changed\n"):
        self.repo.touch(path, text)
        self.repo.commit(f"edit {path}")

    def test_a_change_to_each_candidate_path_is_changed(self):
        for path in ("manifest.json", "payload/scripts/new.py", "payload/docs/guide.md",
                     "fixtures/new.md", "templates/new.txt", "tools/release/anything.py",
                     "tools/release/nested/deeper.txt", ".github/workflows/workflow-ci.yml",
                     ".gitattributes"):
            with self.subTest(path=path):
                self.change(path, f"changed {path}\n")
                found = self.decide()
                self.assertEqual(found["changed"], "true")
                self.assertIn(path, found["reason"])

    def test_a_gitattributes_change_alone_is_changed_because_it_changes_what_is_staged(self):
        """The root `.gitattributes` is read by `git archive`: an `export-ignore` line drops a
        payload file from the staged release source without touching any release-source path."""
        self.repo.touch("payload/scripts/kept.py", "kept\n")
        self.repo.commit("add a payload file")
        before = self.repo.git("rev-parse", "HEAD")
        self.change(".gitattributes", "payload/scripts/kept.py export-ignore\n")
        staged = package.stage(self.repo.root, "HEAD", self.tmp / "staged-after")
        self.assertFalse((staged / "payload/scripts/kept.py").exists())
        self.assertTrue((package.stage(self.repo.root, before, self.tmp / "staged-before")
                         / "payload/scripts/kept.py").is_file())
        found = self.decide()
        self.assertEqual(found["changed"], "true")
        self.assertIn(".gitattributes", found["reason"])

    def test_a_change_elsewhere_is_unchanged(self):
        for path in ("docs/ROADMAP.md", "README.md", "CLAUDE.md", ".claude/commands/x.md",
                     "scripts/workflow.py", "docs/ai-workflow/WORKFLOW_STATE.json",
                     ".workflow-manager/installed.json", ".github/workflows/workflow-conformance.yml",
                     ".github/workflows/release.yml", "tools/docs/check_docs.py",
                     "tools/releases/other.py", "payloads/a.txt", "manifest.json.bak"):
            with self.subTest(path=path):
                self.change(path)
                found = self.decide()
                self.assertEqual(found["changed"], "false", path)
                self.assertIn("no path of", found["reason"])

    def test_one_candidate_path_among_many_is_enough(self):
        self.repo.touch("docs/a.md", "a\n")
        self.repo.touch("tools/release/b.py", "b\n")
        self.repo.touch("README.md", "r\n")
        self.repo.commit("mixed")
        found = self.decide()
        self.assertEqual(found["changed"], "true")
        self.assertIn("tools/release/b.py", found["reason"])
        self.assertNotIn("docs/a.md", found["reason"])

    def test_only_the_last_commit_is_measured(self):
        """HEAD^1 -> HEAD: a candidate path changed by an earlier commit does not count."""
        self.change("payload/earlier.txt")
        self.change("docs/later.md")
        self.assertEqual(self.decide()["changed"], "false")

    def test_a_merge_ref_measures_the_pull_requests_net_change_against_the_base_tip(self):
        """HEAD^1 is the base tip: a release-source change that landed on the base after the
        pull request branched is not the pull request's."""
        self.repo.git("checkout", "-q", "-b", "pr")
        self.change("docs/pr.md")
        self.repo.git("checkout", "-q", "main")
        self.change("payload/landed-on-main.txt")
        self.repo.git("merge", "-q", "--no-ff", "-m", "merge ref", "pr")
        self.assertEqual(self.repo.git("rev-list", "--parents", "-1", "HEAD").count(" "), 2)
        self.assertEqual(self.decide()["changed"], "false")
        self.repo.git("checkout", "-q", "pr")
        self.change("fixtures/pr.md")
        self.repo.git("checkout", "-q", "main")
        self.repo.git("merge", "-q", "--no-ff", "-m", "merge ref 2", "pr")
        self.assertEqual(self.decide()["changed"], "true")

    def test_only_a_pull_request_can_answer_unchanged(self):
        self.change("docs/only.md")
        self.assertEqual(self.decide("pull_request")["changed"], "false")
        for event in ("push", "workflow_dispatch", "schedule", "", "Pull_Request",
                      "pull_request_target"):
            with self.subTest(event=event):
                found = self.decide(event)
                self.assertEqual(found["changed"], "true")
                self.assertIn("always runs everything", found["reason"])

    def test_an_undecidable_pull_request_is_changed(self):
        # No parent to measure against.
        lone = ScratchRepo(self.tmp / "lone")
        lone.touch("docs/a.md", "a\n")
        lone.commit("only commit")
        code, out, err = run_cli("--repo", str(lone.root), "release-source-changed",
                                 "--event", "pull_request")
        self.assertEqual(code, release.EXIT_OK, out + err)
        self.assertEqual(self.outputs(out)["changed"], "true")
        self.assertIn("no parent", self.outputs(out)["reason"])
        # A head that is no commit, and a directory that is no repository.
        self.change("docs/x.md")
        found = self.decide("pull_request", "--head", "no-such-ref")
        self.assertEqual(found["changed"], "true")
        self.assertIn("cannot decide", found["reason"])
        code, out, err = run_cli("--repo", str(self.tmp), "release-source-changed",
                                 "--event", "pull_request")
        self.assertEqual(code, release.EXIT_OK, out + err)
        self.assertEqual(self.outputs(out)["changed"], "true")

    def test_a_shallow_clone_to_the_parent_still_decides(self):
        self.change("docs/x.md")
        clone = self.tmp / "shallow"
        subprocess.run(["git", "clone", "-q", "--depth", "2", f"file://{self.repo.root}", str(clone)],
                       check=True, capture_output=True)
        code, out, err = run_cli("--repo", str(clone), "release-source-changed",
                                 "--event", "pull_request")
        self.assertEqual((code, self.outputs(out)["changed"]), (release.EXIT_OK, "false"), err)
        shallow_one = self.tmp / "shallow-one"
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{self.repo.root}",
                        str(shallow_one)], check=True, capture_output=True)
        code, out, err = run_cli("--repo", str(shallow_one), "release-source-changed",
                                 "--event", "pull_request")
        self.assertEqual((code, self.outputs(out)["changed"]), (release.EXIT_OK, "true"), err)

    def test_the_workflow_step_writes_the_answer_to_github_output(self):
        text = (REPO_ROOT / ".github/workflows/workflow-ci.yml").read_text()
        command = re.search(r"\n        run: (python3 tools/release/release.py "
                            r"release-source-changed .*)\n", _job_section(text, "changes")).group(1)
        command = command.replace("python3 tools/release/release.py",
                                  f"{shlex.quote(sys.executable)} {shlex.quote(str(HERE / 'release.py'))}")
        output = self.tmp / "github-output"
        self.change("docs/y.md")
        for event, expected in (("pull_request", "false"), ("push", "true")):
            output.write_text("")
            proc = subprocess.run(["bash", "-eo", "pipefail", "-c", command],
                                  env=dict(os.environ, EVENT_NAME=event, GITHUB_OUTPUT=str(output)),
                                  cwd=self.repo.root, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(self.outputs(output.read_text())["changed"], expected)
            self.assertEqual(output.read_text(), proc.stdout)


class ManagerBlockCiTest(unittest.TestCase):
    """The `Workflow CI` steps for the Manager block."""

    @classmethod
    def setUpClass(cls):
        cls.text = (REPO_ROOT / ".github/workflows/workflow-ci.yml").read_text()

    def test_the_two_steps_follow_the_tooling_step_in_the_checks_job(self):
        checks = _job_section(self.text, "checks")
        names = ["release_test.py", "Manager block is valid and measured",
                 "Manager release list is current"]
        positions = [checks.index(f"      - name: {n}\n") for n in names]
        self.assertEqual(positions, sorted(positions))

    def test_the_offline_check_reads_the_committed_evidence(self):
        self.assertIn("release.py check-manager-block --commit HEAD --manager-releases "
                      "tools/release/manager-releases.json", self.text)
        step = self.text.split("- name: Manager block is valid and measured")[1].split("- name:")[0]
        self.assertNotIn("GH_TOKEN", step)

    def test_the_live_comparison_is_its_own_step(self):
        self.assertIn("release.py compare-manager-releases --manager-releases "
                      "tools/release/manager-releases.json", self.text)
        self.assertNotIn("continue-on-error", self.text)

    def previous_selection(self) -> str:
        step = self.text.split("- name: Update the previous release to HEAD")[1]
        body = step.split("<<'PY'\n", 1)[1].split("\n          PY\n", 1)[0]
        return "\n".join(line[10:] for line in body.splitlines()) + "\n"

    def run_selection(self, version: str, with_block: bool, releases: list, prereleases=()) -> str:
        tmp = Path(tempfile.mkdtemp(prefix="ci-previous-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        repo = ScratchRepo(tmp / "repo")
        managed_release(repo.root, version, {"a_test.py": SUITE_TWO},
                        valid_block({}) if with_block else None)
        repo.commit("candidate")
        listing = tmp / "releases.json"
        listing.write_text(json.dumps([{"tagName": t, "isDraft": d, "isPrerelease": t in prereleases}
                                      for t, d in releases]))
        return subprocess.run([sys.executable, "-", str(listing)], input=self.previous_selection(),
                              cwd=repo.root, capture_output=True, text=True,
                              check=True).stdout.strip()

    def test_the_previous_release_is_the_highest_published_below_head(self):
        releases = [("v2.11.0", False), ("v2.12.0", False), ("v2.13.0", False),
                    ("v2.12.5", True), ("workflow-manager-v9.0.0", False), ("v2.9.0", False)]
        self.assertEqual(self.run_selection("2.13.0", True, releases), "2.12.0")
        self.assertEqual(self.run_selection("2.12.1", True, releases), "2.12.0")
        self.assertEqual(self.run_selection("2.10.0", True, releases), "2.9.0")
        self.assertEqual(self.run_selection("2.9.0", True, [("v2.9.0", False)]), "")
        # A prerelease is not a published release to update from.
        self.assertEqual(self.run_selection("2.13.0", True, releases, prereleases=("v2.12.0",)), "2.11.0")

    def test_a_release_without_a_block_is_not_update_tested(self):
        self.assertEqual(self.run_selection("2.12.0", False, [("v2.11.0", False)]), "")


class TrailingNewlineTest(ScratchTestCase):
    """review-followups-2: a pattern checked with `.match` must not accept a trailing newline."""

    def test_a_release_tag_ending_in_a_newline_is_not_a_release_tag(self):
        listing = self.tmp / "releases-newline.json"
        listing.write_text(json.dumps([{"tagName": "v2.18.2\n", "isDraft": False}]))
        self.repo.commit("candidate")
        found = release.Releases(self.repo.root, listing)
        self.assertEqual((found.releases, found.drafts, found.tags), (set(), set(), {}))
        self.assertIsNone(release.TAG_RE.match("v2.18.2\n"))
        self.assertIsNotNone(release.TAG_RE.match("v2.18.2"))

    def test_a_record_sha256_ending_in_a_newline_is_refused(self):
        manifest = {"schema_version": 1, "templates": [], "artifacts": [{
            "location": "payload/a.txt", "target_path": "a.txt", "size": 1, "executable": False,
            "sha256": "0" * 64 + "\n"}]}
        with self.assertRaisesRegex(package.PackageError, "no valid sha256"):
            package.manifest_records(manifest)
        manifest["artifacts"][0]["sha256"] = "0" * 64
        self.assertIn("payload/a.txt", package.manifest_records(manifest))

    def test_the_manager_version_pattern_rejects_a_trailing_newline(self):
        # A consistency pin: its only call site uses `fullmatch`, which already refuses the
        # newline (the "minimum version ending in a newline" case above), so no behaviour was
        # wrong; `\Z` makes the pattern itself agree with `package.VERSION_RE`.
        self.assertIsNone(manager_block._MANAGER_VERSION_RE.match("1.13.0\n"))
        self.assertIsNotNone(manager_block._MANAGER_VERSION_RE.match("1.13.0"))


class VerificationCommandsSectionTest(unittest.TestCase):
    """review-followups-2 (#68): `docs/RELEASING.md` gives the exact runnable verification forms."""

    def setUp(self):
        text = (REPO_ROOT / "docs/RELEASING.md").read_text()
        start = text.index("\n## Verification commands\n")
        end = text.find("\n## ", start + 1)
        self.section = text[start:end if end != -1 else len(text)]

    def test_every_command_form_is_present(self):
        for needle in (
            "python3 tools/release/release.py stage-conformance --commit HEAD --out",
            'python3 -B "$TMPDIR/fixture/scripts/$suite"',
            '( cd "$TMPDIR/fixture/scripts" && while read -r suite; do',
            '</dev/null || exit 1; done <<< "$suites" )',
            'test -n "$suites"',
            "runs under bash and zsh",
            "every block below runs, in order, from the repository root",
            "python -m unittest discover -s tools/release -p '*_test.py'",
            "python3 -m unittest discover -s tools/docs -p '*_test.py'",
            "python3 tools/docs/check_docs.py",
            "python3 tools/release/release.py check-manager-block --commit HEAD "
            "--manager-releases tools/release/manager-releases.json",
            "workflow-manager verify .",
            "--release-cache",
            "WORKFLOW_MANAGER_RELEASE_CACHE",
            "Building locally",
            "zlib-ng",
            "zero tests",
        ):
            self.assertIn(needle, self.section)

    def test_the_suites_loop_does_not_rely_on_word_splitting(self):
        self.assertNotIn("for suite in $suites", self.section)

    def test_the_payload_test_glob_appears_only_in_the_never_sentence(self):
        glob = "payload/scripts/*_test.py"
        lines = [line for line in self.section.splitlines() if glob in line]
        self.assertTrue(lines)
        for line in lines:
            self.assertIn("never", line.lower())

    def test_claude_md_points_to_the_section_outside_the_managed_block(self):
        text = (REPO_ROOT / "CLAUDE.md").read_text()
        line = next(line for line in text.splitlines() if "Verification commands" in line)
        self.assertIn("docs/RELEASING.md", line)
        self.assertGreater(text.index(line), text.index("<!-- workflow-manager:end -->"))


if __name__ == "__main__":
    unittest.main()
