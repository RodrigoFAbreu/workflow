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
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

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
    this is its only guard (W2 CP1, `LPR-R1-008`). W2's CP8 moved its row to
    complete, pending cutover."""

    def setUp(self):
        self.text = (REPO_ROOT / "docs" / "ROADMAP.md").read_text()

    def row(self, step: str) -> str:
        rows = [line for line in self.text.splitlines() if line.startswith(f"| {step} |")]
        self.assertEqual(len(rows), 1, step)
        return rows[0]

    def test_w1_is_complete_and_its_cutover_is_done(self):
        row = self.row("W1")
        self.assertIn("**COMPLETE**", row)
        self.assertNotIn("the cutover remains", row)
        self.assertIn("workflow-manager#13", row)

    def test_w2_is_complete_pending_cutover(self):
        row = self.row("W2")
        self.assertIn("**COMPLETE, pending cutover**", row)
        self.assertNotIn("**IN PROGRESS**", row)
        self.assertIn("gate-policy-and-reopening", row)

    def test_it_has_a_workflow_2_8_0_entry_and_marks_both_sections_delivered(self):
        self.assertIn("## Workflow 2.8.0", self.text)
        for heading in ("## Gate and validation policy must be declarative",
                        "## Post-validation reopening and PR-review defects"):
            start = self.text.index(heading)
            self.assertIn("**Delivered in Workflow 2.8.0**",
                          self.text[start:start + 400], heading)

    def test_where_things_stand_is_brought_to_2_7_0(self):
        start = self.text.index("**Where things stand")
        paragraph = self.text[start:self.text.index("**In order:**")]
        self.assertIn("Releases 2.3.1 to 2.7.0", paragraph)
        self.assertIn("`main` ends at 2.7.0", paragraph)
        self.assertNotIn("ends at 2.6.0", paragraph)

    def test_it_no_longer_says_the_release_workflow_will_publish_2_7_0(self):
        section = self.text[self.text.index("## Workflow 2.7.0"):]
        status = section[:section.index("Delivered:")]
        self.assertNotIn("publishes it when its pull request merges", status)
        self.assertIn("tag `v2.7.0`", status)
        self.assertNotIn("once its pin is added", status)


if __name__ == "__main__":
    unittest.main()
