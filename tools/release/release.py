#!/usr/bin/env python3
"""Conventional Commit titles, manifest versions and releases for the Workflow.

The one implementation the pull-request title check, CI and the release
workflow call (`docs/ai-workflow/WORKFLOW_REPOSITORY_SETUP_PLAN.md`). Stdlib
only, except that building a package needs the pinned `zlib-ng` wheel
(`deflate-requirements.txt`, `D-W0-Deflate`).

The release source's `manifest.json` is the only version authority
(`D-W0-Version`): a version change is measured between a commit and its
first parent, and must be exactly the next patch, minor or major. A version
`V` is *published* when a non-draft GitHub release `vV` exists and the tag
`vV` exists; a draft or a tag alone is the residue of a failed publication,
and `V` stays pending. The GitHub release list is never fetched here: it is
read from the file `gh release list --json tagName,isDraft --limit 1000`
saved (`--releases`), and tags are read from the local repository.

Subcommands:

    check-title TITLE [--agree]   validate a title, print its impact; with
                                  --agree, require it to match HEAD^1 -> HEAD's
                                  version change (D-W0-Title)
    check-pending                 D-W0-Version and D-W0-Pending, HEAD^1 -> HEAD
    build                         stage, verify and build a commit's package
    check-immutable               D-W0-Immutable for HEAD's manifest version
    next-release                  D-W0-Target: state, version and target commit
    check-published               the release job's read-back of vV
    stage-conformance             the release source's conformance fixture

Exit codes: 0 success; 1 invalid title or refusal; 2 usage error. Every
undecidable input refuses.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import package  # noqa: E402

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

GIT_TIMEOUT = 120

#: The Workflow Manager's title grammar, applied to the stripped subject.
TITLE_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9._/-]+)\))?(?P<breaking>!)?: (?P<description>\S.*)$"
)
#: A looser shape used only to name what is wrong with an invalid title.
_LOOSE_TITLE_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?:(?P<rest>.*)$")

MAJOR, MINOR, PATCH, NONE = "major", "minor", "patch", "none"

#: Release impact per type (the Workflow Manager's table). `!` on any type is
#: a major release.
TYPE_IMPACT = {
    "feat": MINOR,
    "fix": PATCH,
    "perf": PATCH,
    "refactor": PATCH,
    "build": PATCH,
    "revert": PATCH,
    "docs": NONE,
    "chore": NONE,
    "ci": NONE,
    "test": NONE,
    "style": NONE,
}

ACCEPTED_FORM = (
    "expected '<type>[(<scope>)][!]: <description>', type one of "
    + ", ".join(sorted(TYPE_IMPACT))
)

TAG_RE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

RECOVERY = ("a failed publication: remove the residue and re-run Release "
            "(docs/RELEASING.md, \"Recovering from a failed publication\")")
SUPERSESSION = ("a published release cannot be repaired: leave it as it is, never pin it in "
                "workflow-manager, and supersede it with the next patch version "
                "(docs/RELEASING.md, \"Superseding an incomplete published release\")")


class ReleaseError(Exception):
    """A refusal. Exit 1."""


class UsageError(Exception):
    """A malformed invocation. Exit 2."""


# -- titles ----------------------------------------------------------------------


@dataclass(frozen=True)
class Title:
    type: str
    scope: str | None
    breaking: bool
    description: str

    @property
    def impact(self) -> str:
        return MAJOR if self.breaking else TYPE_IMPACT[self.type]


class InvalidTitle(ValueError):
    """A title that is not a Conventional Commit; the message names why."""


def parse_title(title: str) -> Title:
    subject = title.strip()
    match = TITLE_RE.match(subject)
    if match and match["type"] in TYPE_IMPACT:
        return Title(match["type"], match["scope"], bool(match["breaking"]), match["description"])
    raise InvalidTitle(_diagnose(subject))


def _diagnose(subject: str) -> str:
    loose = _LOOSE_TITLE_RE.match(subject)
    if not loose:
        return "no 'type: description' shape"
    type_ = loose["type"]
    if type_ != type_.lower():
        return f"type '{type_}' must be lowercase"
    if type_ not in TYPE_IMPACT:
        return f"unknown type '{type_}'"
    scope = loose["scope"]
    if scope is not None:
        if scope == "":
            return "empty scope '()'"
        if not re.fullmatch(r"[a-z0-9._/-]+", scope):
            return f"scope '{scope}' may only contain a-z, 0-9, '.', '_', '/' and '-'"
    rest = loose["rest"]
    if not rest.strip():
        return "empty description"
    if not rest.startswith(" "):
        return "no space after the colon"
    return "more than one space after the colon"


# -- versions --------------------------------------------------------------------


def parse_version(text: object) -> tuple[int, int, int]:
    match = package.VERSION_RE.match(text) if isinstance(text, str) else None
    if not match:
        raise ReleaseError(f"version {text!r} is not X.Y.Z")
    return int(match[1]), int(match[2]), int(match[3])


def bump_level(old: str, new: str) -> str:
    """The level of the version change `old` -> `new` (`D-W0-Version`):
    `none` when equal, else exactly the next patch, minor or major."""
    o, n = parse_version(old), parse_version(new)
    if n == o:
        return NONE
    if n == (o[0], o[1], o[2] + 1):
        return PATCH
    if n == (o[0], o[1] + 1, 0):
        return MINOR
    if n == (o[0] + 1, 0, 0):
        return MAJOR
    raise ReleaseError(
        f"version change {old} -> {new} is not the next patch, minor or major of {old} "
        f"({o[0]}.{o[1]}.{o[2] + 1}, {o[0]}.{o[1] + 1}.0 or {o[0] + 1}.0.0)")


# -- git -------------------------------------------------------------------------


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                              timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseError(f"git {' '.join(args)} failed: {exc}") from exc
    if check and proc.returncode != 0:
        raise ReleaseError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc


def resolve_commit(repo: Path, ref: str) -> str:
    proc = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False)
    if proc.returncode != 0:
        raise ReleaseError(f"{ref} is not a commit")
    return proc.stdout.strip()


def first_parent(repo: Path, commit: str) -> str:
    proc = _git(repo, "rev-parse", "--verify", "--quiet", f"{commit}^1", check=False)
    if proc.returncode != 0:
        raise ReleaseError(f"{commit} has no parent to measure a change against")
    return proc.stdout.strip()


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    proc = _git(repo, "merge-base", "--is-ancestor", ancestor, descendant, check=False)
    if proc.returncode in (0, 1):
        return proc.returncode == 0
    raise ReleaseError(f"cannot decide whether {ancestor} is an ancestor of {descendant}: "
                       f"{proc.stderr.strip()}")


def manifest_version_at(repo: Path, commit: str) -> str:
    """The `workflow_version` of `commit`'s `manifest.json`; refuses a missing
    or malformed manifest."""
    proc = _git(repo, "show", f"{commit}:{package.MANIFEST_NAME}", check=False)
    if proc.returncode != 0:
        raise ReleaseError(f"{commit} has no {package.MANIFEST_NAME}")
    try:
        manifest = json.loads(proc.stdout)
    except ValueError as exc:
        raise ReleaseError(f"{commit}'s {package.MANIFEST_NAME} is malformed: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ReleaseError(f"{commit}'s {package.MANIFEST_NAME} is malformed: not an object")
    version = manifest.get("workflow_version")
    parse_version(version)
    return version


def release_source_changes(repo: Path, old: str, new: str) -> list[str]:
    """Release-source paths that differ between `old` and `new`."""
    proc = _git(repo, "diff", "--name-only", "--no-renames", old, new, "--",
                *package.RELEASE_SOURCE_PATHS)
    return [line for line in proc.stdout.splitlines() if line]


def _first_parent_history(repo: Path, tip: str) -> list[str]:
    return _git(repo, "rev-list", "--first-parent", tip).stdout.split()


# -- what is published ------------------------------------------------------------


@dataclass(frozen=True)
class VersionStatus:
    version: str
    published: bool
    draft: bool
    tag: str | None

    def residue(self) -> list[str]:
        found = []
        if self.draft:
            found.append(f"a draft release v{self.version}")
        if self.tag is not None:
            found.append(f"the tag v{self.version} at {self.tag}")
        return found


class Releases:
    """What is published: the saved GitHub release list, and the local tags."""

    def __init__(self, repo: Path, releases_file: Path):
        self.repo = repo
        try:
            entries = json.loads(Path(releases_file).read_text())
        except (OSError, ValueError) as exc:
            raise ReleaseError(f"cannot read the release list {releases_file}: {exc}") from exc
        if not isinstance(entries, list):
            raise ReleaseError(f"release list {releases_file} is not a JSON list")
        self.drafts: set[str] = set()
        self.releases: set[str] = set()
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("tagName"), str) \
                    or not isinstance(entry.get("isDraft"), bool):
                raise ReleaseError(f"release list entry {entry!r} has no tagName/isDraft")
            tag = entry["tagName"]
            if tag in seen:
                raise ReleaseError(f"release list names {tag} twice")
            seen.add(tag)
            if not TAG_RE.match(tag):
                continue
            (self.drafts if entry["isDraft"] else self.releases).add(tag[1:])
        self.tags: dict[str, str] = {}
        for tag in _git(repo, "tag", "--list", "v*").stdout.split():
            if TAG_RE.match(tag):
                self.tags[tag[1:]] = resolve_commit(repo, f"refs/tags/{tag}")
        for version in sorted(self.releases):
            if version not in self.tags:
                raise ReleaseError(
                    f"release v{version} is published but the tag v{version} is missing from "
                    f"the fetched tags: fetch every tag, or inspect the release by hand")

    def status(self, version: str) -> VersionStatus:
        return VersionStatus(version=version, published=version in self.releases,
                             draft=version in self.drafts, tag=self.tags.get(version))

    def is_published(self, version: str) -> bool:
        return version in self.releases

    def highest_published(self) -> str | None:
        if not self.releases:
            return None
        return max(self.releases, key=parse_version)


# -- assets ----------------------------------------------------------------------


def compare_assets(version: str, built: Path, downloaded: Path) -> list[str]:
    """Differences between the built assets of `version` and the downloaded
    ones: exactly the three asset names, each byte-equal. A differing archive
    is reported as a tar-stream difference (a release-source change) or as a
    deflate difference with an identical tar stream (compression drift)."""
    expected = set(package.asset_names(version))
    problems = []
    try:
        present = {p.name for p in Path(downloaded).iterdir()}
    except OSError as exc:
        return [f"cannot read the downloaded assets in {downloaded}: {exc}"]
    for name in sorted(expected - present):
        problems.append(f"missing asset {name}")
    for name in sorted(present - expected):
        problems.append(f"extra asset {name}")
    for name in sorted(expected & present):
        mine, theirs = Path(built) / name, Path(downloaded) / name
        if not theirs.is_file() or theirs.is_symlink():
            problems.append(f"asset {name} is not a regular file")
            continue
        if package.file_sha256(mine) == package.file_sha256(theirs):
            continue
        if name == package.archive_name(version):
            try:
                same_tar = package.decompressed_tar(mine) == package.decompressed_tar(theirs)
            except package.PackageError as exc:
                problems.append(f"asset {name} differs: {exc}")
                continue
            if same_tar:
                problems.append(f"asset {name} differs, with an identical tar stream: the "
                                f"compression runtime drifted (D-W0-Deflate)")
            else:
                problems.append(f"asset {name} differs in its tar stream: the release "
                                f"source differs")
        else:
            problems.append(f"asset {name} differs")
    return problems


def _build_commit(repo: Path, commit: str, scratch: Path, out: Path) -> package.Package:
    source = package.stage(repo, commit, scratch / "release")
    return package.build(source, out)


# -- subcommands -----------------------------------------------------------------


def cmd_check_title(args) -> int:
    try:
        title = parse_title(args.title)
    except InvalidTitle as exc:
        print(f"invalid pull-request title {args.title.strip()!r}: {exc}; {ACCEPTED_FORM}",
              file=sys.stderr)
        return EXIT_FAIL
    print(f"impact={title.impact}")
    if not args.agree:
        return EXIT_OK
    head = resolve_commit(args.repo, args.head)
    base = first_parent(args.repo, head)
    old, new = manifest_version_at(args.repo, base), manifest_version_at(args.repo, head)
    level = bump_level(old, new)
    if level != title.impact:
        raise ReleaseError(
            f"title impact is {title.impact}, but the manifest version change {old} -> {new} "
            f"is {level}: a {level} change needs "
            + ("a docs/chore/ci/test/style title" if level == NONE
               else f"a title of {level} impact") + " (D-W0-Title)")
    print(f"version {old} -> {new} ({level}) agrees with the title")
    return EXIT_OK


def cmd_check_pending(args) -> int:
    releases = Releases(args.repo, args.releases)
    head = resolve_commit(args.repo, args.head)
    base = first_parent(args.repo, head)
    old, new = manifest_version_at(args.repo, base), manifest_version_at(args.repo, head)
    level = bump_level(old, new)
    changed = release_source_changes(args.repo, base, head)
    base_status = releases.status(old)
    if changed and not base_status.published:
        residue = base_status.residue()
        raise ReleaseError(
            f"version {old} is pending (not published"
            + (f"; found {' and '.join(residue)}" if residue else "")
            + f"): its release source is frozen until v{old} is published, and this change "
            f"touches {', '.join(changed)} (D-W0-Pending)")
    if changed and level == NONE:
        raise ReleaseError(
            f"the release source changed ({', '.join(changed)}) without a version change "
            f"from {old}: bump manifest.json's workflow_version (D-W0-Pending)")
    print(f"ok: {old} -> {new} ({level}); "
          + (f"release source changed: {', '.join(changed)}" if changed
             else "release source unchanged"))
    return EXIT_OK


def cmd_build(args) -> int:
    commit = resolve_commit(args.repo, args.commit)
    out = Path(args.out)
    with tempfile.TemporaryDirectory(prefix="workflow-build-") as tmp:
        scratch = Path(tmp)
        source = package.stage(args.repo, commit, scratch / "release")
        built = package.build(source, out)
        package.build(source, scratch / "again")
        for name in package.asset_names(built.version):
            if package.file_sha256(out / name) != package.file_sha256(scratch / "again" / name):
                raise ReleaseError(f"two builds of {commit} differ in {name}")
        tree = package.extract_tree(built.archive, scratch / "extracted")
        if package.tree_listing(tree) != package.tree_listing(source):
            raise ReleaseError(f"the archive of {commit} does not round-trip to its release "
                               f"source")
    zlib_ng = package.deflate_runtime()
    print(f"version={built.version}")
    print(f"commit={commit}")
    print(f"files={built.files}")
    print(f"zlib_ng={zlib_ng.ZLIBNG_RUNTIME_VERSION}")
    print(f"tar_sha256={built.tar_sha256}")
    print(f"archive_sha256={built.archive_sha256}")
    print(f"manifest_sha256={built.manifest_sha256}")
    return EXIT_OK


def cmd_check_immutable(args) -> int:
    releases = Releases(args.repo, args.releases)
    head = resolve_commit(args.repo, args.head)
    version = manifest_version_at(args.repo, head)
    if not releases.is_published(version):
        print(f"ok: version {version} is not published; D-W0-Immutable does not apply")
        return EXIT_OK
    tag = f"refs/tags/v{version}"
    changed = release_source_changes(args.repo, tag, head)
    if changed:
        raise ReleaseError(
            f"version {version} is published, and the release source differs from v{version} "
            f"in {', '.join(changed)}: a published release never changes; bump the version "
            f"(D-W0-Immutable)")
    print(f"ok: release source unchanged since v{version}")
    if args.published is None:
        return EXIT_OK
    with tempfile.TemporaryDirectory(prefix="workflow-immutable-") as tmp:
        scratch = Path(tmp)
        _build_commit(args.repo, head, scratch, scratch / "assets")
        problems = compare_assets(version, scratch / "assets", Path(args.published))
    if problems:
        raise ReleaseError(f"the published assets of v{version} differ from the rebuilt "
                           f"package: {'; '.join(problems)}; {SUPERSESSION}")
    print(f"ok: the rebuilt package equals the published assets of v{version}")
    return EXIT_OK


def introducing_commit(repo: Path, history: list[str], version: str) -> str:
    """The oldest commit of the run of first-parent commits, from the tip,
    whose manifest names `version` (`C_V`)."""
    target = None
    for commit in history:
        if manifest_version_at(repo, commit) != version:
            break
        target = commit
    if target is None:
        raise ReleaseError(f"the tip's manifest does not name {version}")
    return target


def cmd_next_release(args) -> int:
    releases = Releases(args.repo, args.releases)
    tip = resolve_commit(args.repo, args.tip)
    trigger = resolve_commit(args.repo, args.trigger)
    history = _first_parent_history(args.repo, tip)
    if trigger not in history:
        raise ReleaseError(f"trigger {trigger} is not on the first-parent history of {tip}")
    version = manifest_version_at(args.repo, tip)
    status = releases.status(version)
    if not status.published and status.residue():
        raise ReleaseError(
            f"version {version} is not published, but found {' and '.join(status.residue())}: "
            f"{RECOVERY}")
    target = introducing_commit(args.repo, history, version)
    changed = release_source_changes(args.repo, target, trigger)
    if changed:
        raise ReleaseError(
            f"trigger {trigger}'s release source differs from {target}'s, the commit that "
            f"introduced {version}, in {', '.join(changed)}")
    if not status.published:
        highest = releases.highest_published()
        if highest is not None:
            if parse_version(version) <= parse_version(highest):
                raise ReleaseError(f"version {version} is not greater than the highest "
                                   f"published version {highest}")
            if not _is_ancestor(args.repo, releases.tags[highest], target):
                raise ReleaseError(f"v{highest}'s tag ({releases.tags[highest]}) is not an "
                                   f"ancestor of {target}, the commit that introduced {version}")
            # D-W0-Pending, independently of CI: `C_V`'s parent's version is
            # published, so no version is ever skipped.
            parent = history[history.index(target) + 1:][:1]
            previous = manifest_version_at(args.repo, parent[0]) if parent else None
            if previous is not None and not releases.is_published(previous):
                raise ReleaseError(f"version {previous}, which {target}'s parent names, is not "
                                   f"published: v{previous} must be published before {version} "
                                   f"(D-W0-Pending)")
    print(f"state={'published' if status.published else 'pending'}")
    print(f"version={version}")
    print(f"target={target}")
    return EXIT_OK


def cmd_check_published(args) -> int:
    version = args.version
    parse_version(version)
    target = resolve_commit(args.repo, args.target)
    releases = Releases(args.repo, args.releases)
    status = releases.status(version)
    problems = []
    if not status.published:
        problems.append(f"v{version} is not a published release"
                        + (" (it is a draft)" if status.draft else ""))
    if status.tag is None:
        problems.append(f"the tag v{version} does not exist")
    elif status.tag != target:
        problems.append(f"the tag v{version} is at {status.tag}, not {target}")
    built = Path(args.assets)
    for name in package.asset_names(version):
        if not (built / name).is_file():
            raise ReleaseError(f"the built assets in {built} lack {name}")
    problems += compare_assets(version, built, Path(args.downloaded))
    if problems:
        raise ReleaseError(f"v{version} does not read back as built: {'; '.join(problems)}; "
                           f"{SUPERSESSION}")
    print(f"ok: v{version} is published at {target} with exactly its three built assets")
    return EXIT_OK


def cmd_stage_conformance(args) -> int:
    commit = resolve_commit(args.repo, args.commit)
    with tempfile.TemporaryDirectory(prefix="workflow-conformance-") as tmp:
        source = package.stage(args.repo, commit, Path(tmp) / "release")
        fixture = package.stage_conformance(source, Path(args.out))
    print(f"fixture={fixture}")
    return EXIT_OK


# -- entry point -----------------------------------------------------------------


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise UsageError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="release.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", type=Path, default=Path("."),
                        help="the Git repository to read (default: the current directory)")
    sub = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)

    p = sub.add_parser("check-title")
    p.add_argument("title")
    p.add_argument("--agree", action="store_true")
    p.add_argument("--head", default="HEAD")
    p.set_defaults(func=cmd_check_title)

    p = sub.add_parser("check-pending")
    p.add_argument("--releases", required=True, type=Path)
    p.add_argument("--head", default="HEAD")
    p.set_defaults(func=cmd_check_pending)

    p = sub.add_parser("build")
    p.add_argument("--commit", required=True)
    p.add_argument("--out", required=True, type=Path)
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("check-immutable")
    p.add_argument("--releases", required=True, type=Path)
    p.add_argument("--published", type=Path)
    p.add_argument("--head", default="HEAD")
    p.set_defaults(func=cmd_check_immutable)

    p = sub.add_parser("next-release")
    p.add_argument("--trigger", required=True)
    p.add_argument("--releases", required=True, type=Path)
    p.add_argument("--tip", default="HEAD")
    p.set_defaults(func=cmd_next_release)

    p = sub.add_parser("check-published")
    p.add_argument("--version", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--releases", required=True, type=Path)
    p.add_argument("--assets", required=True, type=Path)
    p.add_argument("--downloaded", required=True, type=Path)
    p.set_defaults(func=cmd_check_published)

    p = sub.add_parser("stage-conformance")
    p.add_argument("--commit", required=True)
    p.add_argument("--out", required=True, type=Path)
    p.set_defaults(func=cmd_stage_conformance)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        return args.func(args)
    except UsageError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (ReleaseError, package.PackageError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
