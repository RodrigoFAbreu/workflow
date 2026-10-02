"""Staging and building a Workflow release package (`D-W0-Stage`, `D-W0-Builder`).

A package for version `V` is three release assets:

    workflow-V.tar.gz           gzip-compressed POSIX tar; one top-level
                                directory, `workflow-V/`, holding exactly the
                                release directory
    workflow-V.manifest.json    a byte copy of that release's manifest.json
    SHA256SUMS                  `sha256sum -c` lines for the two files above

This is the build half of the Workflow Manager's `package.py`
(`D-Package-Format`), ported rather than imported: the producer owns the
format it publishes, and the Manager's own `package verify` and `bootstrap`
check what this module builds (CI's `package` job). The tar stream is fully
determined by the release directory. The deflate bytes are not determined by
the format, only by the implementation, and every published archive was
deflated by zlib-ng, so the archive is written with raw deflate from the
pinned `zlib-ng` wheel (`deflate-requirements.txt`, `D-W0-Deflate`) inside
the gzip framing `gzip.GzipFile(filename="", mtime=0, compresslevel=9)`
writes. There is no fallback to `zlib`.

Every release is read from `git archive <commit> manifest.json payload
fixtures templates`, extracted into a scratch directory -- never from the
working tree, which also holds this repository's own installation.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import tarfile
import tempfile
import zlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

#: The four release-source paths, at the repository root (`D-W0-Stage`).
RELEASE_SOURCE_PATHS = ("manifest.json", "payload", "fixtures", "templates")

SUMS_NAME = "SHA256SUMS"
MANIFEST_NAME = "manifest.json"
DIR_MODE = 0o755
EXECUTABLE_MODE = 0o755
FILE_MODE = 0o644

#: The deflate runtime every published archive was built with (`D-W0-Deflate`).
PINNED_ZLIB_NG_VERSION = "2.2.5"
COMPRESS_LEVEL = 9
#: `GzipFile(filename="", mtime=0, compresslevel=9)`'s header: magic, deflate,
#: no flags, mtime 0, XFL 2 (maximum compression), OS 255 (unknown).
GZIP_HEADER = b"\x1f\x8b\x08\x00" + struct.pack("<I", 0) + b"\x02\xff"

#: `\Z`, not `$`: `$` also matches before a trailing newline.
VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

#: Payload categories the Manager's `full` install profile installs, and the
#: release-owned templates that belong to one (the Manager's `release.py`).
FULL_PROFILE_CATEGORIES = ("distribution", "conformance")
RELEASE_TEMPLATES = {".github/workflows/workflow-conformance.yml": "conformance"}
GITIGNORE_TEMPLATE = ".gitignore.workflow-fragment"
#: The state templates the Manager's conformance fixture places: its
#: `STATE_TEMPLATES` under `docs/ai-workflow/`, named, so a future template
#: there is not placed by prefix.
CONFORMANCE_STATE_TEMPLATES = ("docs/ai-workflow/WORKFLOW_STATE.json",
                               "docs/ai-workflow/WORKFLOW_CONFIG.json")

GIT_TIMEOUT = 120

#: The installed script that states its own release (Workflow 2.7.0 and
#: later), and the literal it states it with (the release-constant guard).
RELEASE_CONSTANT_TARGET = "scripts/workflow_protocol.py"
RELEASE_CONSTANT_RE = re.compile(r'^WORKFLOW_RELEASE = "([^"\n]*)"$', re.MULTILINE)


class PackageError(RuntimeError):
    """A release that cannot be staged, verified or built. Never guessed past."""


class DeflateRuntimeError(PackageError):
    """The pinned `zlib_ng` is missing or is not the pinned version."""


def archive_name(version: str) -> str:
    return f"workflow-{version}.tar.gz"


def manifest_asset_name(version: str) -> str:
    return f"workflow-{version}.manifest.json"


def asset_names(version: str) -> tuple[str, str, str]:
    """The exact three asset names of release `version`, sorted."""
    return tuple(sorted((archive_name(version), manifest_asset_name(version), SUMS_NAME)))


def top_directory(version: str) -> str:
    return f"workflow-{version}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256sums_text(files: Iterable[Path]) -> str:
    """`sha256sum`'s text format (`<hex>  <name>`), one line per file, sorted by name."""
    paths = sorted((Path(p) for p in files), key=lambda p: p.name)
    return "".join(f"{file_sha256(p)}  {p.name}\n" for p in paths)


# -- git ---------------------------------------------------------------------------


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PackageError(f"git {' '.join(args)} failed: {exc}") from exc
    if proc.returncode != 0:
        raise PackageError(
            f"git {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout if binary else proc.stdout.decode("utf-8")


# -- staging -----------------------------------------------------------------------


def stage(repo: Path, commit: str, dest: Path) -> Path:
    """Extract `commit`'s release source into `dest`, which must not exist.

    Reads `git archive <commit> manifest.json payload fixtures templates`
    and extracts it with tarfile's `data` filter, so nothing outside those
    four paths, and nothing the commit does not record, is ever packaged.
    """
    dest = Path(dest)
    if dest.exists() or dest.is_symlink():
        raise PackageError(f"{dest} already exists")
    stream = _git(repo, "archive", "--format=tar", commit, "--", *RELEASE_SOURCE_PATHS,
                  binary=True)
    dest.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(stream), mode="r:") as tar:
        tar.extractall(dest, filter="data")
    return dest


# -- verifying ---------------------------------------------------------------------


def _relative_parts(name: str) -> tuple[str, ...]:
    """`name` split into components, refused unless it is a plain relative
    path: not absolute, no `..`, no empty or `.` component, no NUL or `\\`."""
    if not isinstance(name, str) or not name or "\0" in name or "\\" in name \
            or name.startswith("/"):
        raise PackageError(f"unsafe path {name!r}")
    parts = tuple(name.split("/"))
    if any(part in ("", ".", "..") for part in parts):
        raise PackageError(f"unsafe path {name!r}")
    return parts


def load_manifest(release_dir: Path) -> dict:
    path = Path(release_dir) / MANIFEST_NAME
    if path.is_symlink() or not path.is_file():
        raise PackageError(f"no regular {MANIFEST_NAME} in {release_dir}")
    try:
        manifest = json.loads(path.read_bytes())
    except ValueError as exc:
        raise PackageError(f"{path} is not JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise PackageError(f"{path} is not a JSON object")
    return manifest


def manifest_version(manifest: dict) -> str:
    version = manifest.get("workflow_version")
    if not isinstance(version, str) or not VERSION_RE.match(version):
        raise PackageError(f"manifest workflow_version {version!r} is not X.Y.Z")
    return version


def manifest_records(manifest: dict) -> dict[str, dict]:
    """Every file the manifest lists, by location, `manifest.json` aside.

    Refuses a malformed record, an unsafe or repeated location."""
    if manifest.get("schema_version") != 1:
        raise PackageError(f"manifest schema_version {manifest.get('schema_version')!r} is not 1")
    by_location: dict[str, dict] = {}
    for section in ("artifacts", "templates"):
        records = manifest.get(section)
        if not isinstance(records, list):
            raise PackageError(f"manifest {section} is not a list")
        for record in records:
            if not isinstance(record, dict):
                raise PackageError(f"manifest {section} entry {record!r} is not an object")
            location = record.get("location")
            _relative_parts(location)
            if not isinstance(record.get("target_path"), str):
                raise PackageError(f"manifest entry {location} has no target_path")
            if not isinstance(record.get("sha256"), str) or not _SHA256_RE.match(record["sha256"]):
                raise PackageError(f"manifest entry {location} has no valid sha256")
            size = record.get("size")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                raise PackageError(f"manifest entry {location} has no valid size")
            executable = record.get("executable", False)
            if section == "artifacts" and not isinstance(record.get("executable"), bool):
                raise PackageError(f"manifest entry {location} has no boolean executable")
            if not isinstance(executable, bool):
                raise PackageError(f"manifest entry {location} has a non-boolean executable")
            if location == MANIFEST_NAME or location in by_location:
                raise PackageError(f"manifest lists {location} twice")
            by_location[location] = record
    return by_location


def _parent_directories(locations: Iterable[str]) -> set[str]:
    parents = set()
    for location in locations:
        parts = _relative_parts(location)
        for depth in range(1, len(parts)):
            parents.add("/".join(parts[:depth]))
    return parents


def _record_mode(record: dict) -> int:
    return EXECUTABLE_MODE if record.get("executable") else FILE_MODE


def verify_release(release_dir: Path) -> str:
    """Refuse unless `release_dir` is exactly the release its manifest
    describes; return the version.

    The manifest is well-formed; every listed file is a regular file (no
    link anywhere on its path) with the recorded sha256, size and executable
    bit; and nothing else is there -- no unlisted file, no stray directory,
    no link of any kind.
    """
    root = Path(release_dir)
    manifest = load_manifest(root)
    version = manifest_version(manifest)
    records = manifest_records(manifest)
    problems = []
    for location, record in sorted(records.items()):
        path = root / location
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            problems.append(f"link or outside the release: {location}")
            continue
        if not path.is_file():
            problems.append(f"missing: {location}")
            continue
        data = path.read_bytes()
        if sha256_bytes(data) != record["sha256"] or len(data) != record["size"]:
            problems.append(f"digest mismatch: {location}")
        executable = bool(path.stat().st_mode & 0o111)
        if executable != bool(record.get("executable")):
            problems.append(f"executable bit differs from the manifest: {location}")
    expected_files = set(records) | {MANIFEST_NAME}
    expected_dirs = _parent_directories(records)
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            problems.append(f"link in release: {relative}")
        elif path.is_dir():
            if relative not in expected_dirs:
                problems.append(f"unexpected directory in release: {relative}")
        elif relative not in expected_files:
            problems.append(f"untracked file in release: {relative}")
    if problems:
        raise PackageError(f"release {version} at {root} fails verification: "
                           + "; ".join(problems))
    return version


def check_release_constant(release_dir: Path) -> None:
    """Refuse unless the release's own `WORKFLOW_RELEASE` names its manifest
    version (the release-constant guard).

    Applies only when the manifest lists `scripts/workflow_protocol.py`,
    which no release before 2.7.0 has, so every published release still
    builds. The file must hold exactly one `WORKFLOW_RELEASE = "<v>"` line.
    """
    root = Path(release_dir)
    manifest = load_manifest(root)
    version = manifest_version(manifest)
    records = [record for record in manifest_records(manifest).values()
               if record["target_path"] == RELEASE_CONSTANT_TARGET]
    if not records:
        return
    location = records[0]["location"]
    try:
        text = (root / location).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PackageError(f"cannot read {location}: {exc}") from exc
    found = RELEASE_CONSTANT_RE.findall(text)
    if len(found) != 1:
        raise PackageError(
            f"{location} must state WORKFLOW_RELEASE exactly once, found {len(found)} "
            f"(manifest version {version})")
    if found[0] != version:
        raise PackageError(
            f"{location} states WORKFLOW_RELEASE = {found[0]!r}, but the manifest version is "
            f"{version!r}: set both to the release being built")


# -- building ----------------------------------------------------------------------


def _tarinfo(name: str, *, directory: bool, mode: int, size: int = 0) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
    info.mode = mode
    info.size = size
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def tar_stream(release_dir: Path) -> tuple[str, bytes]:
    """The verified release's uncompressed tar stream, and its version.

    Members are `manifest.json`, every manifest location and every parent
    directory of those, sorted, with `mtime = 0`, owner `0:0` and no owner
    names, mode `0755` for directories and executables and `0644` otherwise;
    USTAR, with a PAX header only where USTAR cannot hold a path.
    """
    root = Path(release_dir)
    version = verify_release(root)
    manifest = load_manifest(root)
    records = manifest_records(manifest)
    manifest_bytes = (root / MANIFEST_NAME).read_bytes()
    top = top_directory(version)
    members: dict[str, tuple[tarfile.TarInfo, bytes | None]] = {
        top: (_tarinfo(top, directory=True, mode=DIR_MODE), None)}
    for directory in _parent_directories(records):
        name = f"{top}/{directory}"
        members[name] = (_tarinfo(name, directory=True, mode=DIR_MODE), None)
    for location, record in records.items():
        data = (root / location).read_bytes()
        if sha256_bytes(data) != record["sha256"] or len(data) != record["size"]:
            raise PackageError(f"{location} changed while it was being packed")
        name = f"{top}/{location}"
        members[name] = (_tarinfo(name, directory=False, mode=_record_mode(record),
                                  size=len(data)), data)
    name = f"{top}/{MANIFEST_NAME}"
    members[name] = (_tarinfo(name, directory=False, mode=FILE_MODE,
                              size=len(manifest_bytes)), manifest_bytes)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for member_name in sorted(members):
            info, data = members[member_name]
            tar.addfile(info, io.BytesIO(data) if data is not None else None)
    return version, buffer.getvalue()


def deflate_runtime():
    """The pinned `zlib_ng.zlib_ng` module; refuses anything else."""
    try:
        from zlib_ng import zlib_ng
    except ImportError as exc:
        raise DeflateRuntimeError(
            "zlib_ng is not installed: install the pinned compression runtime with "
            "`pip install --require-hashes -r tools/release/deflate-requirements.txt`"
        ) from exc
    version = getattr(zlib_ng, "ZLIBNG_RUNTIME_VERSION", None)
    if version != PINNED_ZLIB_NG_VERSION:
        raise DeflateRuntimeError(
            f"zlib_ng reports zlib-ng {version!r}, the pinned compression runtime is "
            f"{PINNED_ZLIB_NG_VERSION} (tools/release/deflate-requirements.txt)")
    return zlib_ng


def gzip_bytes(data: bytes) -> bytes:
    """`data` in `GzipFile(filename="", mtime=0, compresslevel=9)`'s framing,
    deflated by the pinned zlib-ng (`D-W0-Deflate`)."""
    zlib_ng = deflate_runtime()
    compressor = zlib_ng.compressobj(COMPRESS_LEVEL, zlib_ng.DEFLATED, -zlib_ng.MAX_WBITS,
                                     zlib_ng.DEF_MEM_LEVEL, 0)
    body = compressor.compress(data) + compressor.flush()
    trailer = struct.pack("<II", zlib.crc32(data) & 0xFFFFFFFF, len(data) & 0xFFFFFFFF)
    return GZIP_HEADER + body + trailer


@dataclass(frozen=True)
class Package:
    """The three assets of one built package, and the digests of its parts."""

    version: str
    archive: Path
    manifest: Path
    sums: Path
    files: int
    tar_sha256: str
    archive_sha256: str
    manifest_sha256: str


def build(release_dir: Path, out_dir: Path) -> Package:
    """Pack the verified `release_dir` into its three assets in `out_dir`.

    Refuses a release whose `WORKFLOW_RELEASE` differs from its manifest
    version (`check_release_constant`) before writing anything."""
    deflate_runtime()
    root = Path(release_dir)
    verify_release(root)
    check_release_constant(root)
    version, tar_data = tar_stream(root)
    archive_data = gzip_bytes(tar_data)
    manifest_data = (root / MANIFEST_NAME).read_bytes()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    archive = out / archive_name(version)
    manifest = out / manifest_asset_name(version)
    sums = out / SUMS_NAME
    _write_atomically(archive, archive_data)
    _write_atomically(manifest, manifest_data)
    _write_atomically(sums, sha256sums_text([archive, manifest]).encode("utf-8"))
    return Package(
        version=version, archive=archive, manifest=manifest, sums=sums,
        files=len(manifest_records(load_manifest(root))) + 1,
        tar_sha256=sha256_bytes(tar_data), archive_sha256=sha256_bytes(archive_data),
        manifest_sha256=sha256_bytes(manifest_data))


def _write_atomically(path: Path, data: bytes) -> None:
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, FILE_MODE)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def decompressed_tar(archive: Path) -> bytes:
    """An archive's tar stream (stdlib `zlib` inflates any deflate stream)."""
    data = Path(archive).read_bytes()
    try:
        return zlib.decompress(data, 16 + zlib.MAX_WBITS)
    except zlib.error as exc:
        raise PackageError(f"{archive} is not a gzip stream: {exc}") from exc


def extract_tree(archive: Path, dest: Path) -> Path:
    """Extract a built archive's `workflow-V/` tree into `dest` (round trip)."""
    dest = Path(dest)
    dest.mkdir(parents=True)
    with tarfile.open(archive, mode="r:gz") as tar:
        tar.extractall(dest, filter="data")
    tops = [p for p in dest.iterdir()]
    if len(tops) != 1 or not tops[0].is_dir():
        raise PackageError(f"{archive} does not hold exactly one top-level directory")
    return tops[0]


def tree_listing(root: Path) -> dict[str, tuple[str, int]]:
    """Every file under `root`: relative path -> (sha256, permission bits)."""
    root = Path(root)
    listing = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink():
            listing[path.relative_to(root).as_posix()] = (
                file_sha256(path), path.stat().st_mode & 0o777)
    return listing


# -- conformance fixture -----------------------------------------------------------


def _place(root: Path, record: dict, dest: Path, mode: int) -> None:
    data = (root / record["location"]).read_bytes()
    if sha256_bytes(data) != record["sha256"]:
        raise PackageError(f"{record['location']} does not match its manifest entry")
    _relative_parts(record["target_path"])
    path = dest / record["target_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)


def stage_conformance(release_dir: Path, dest: Path) -> Path:
    """The conformance fixture for the verified release at `release_dir`.

    The Workflow Manager's `build_conformance_repo`: a fresh Git repository
    holding the `full`-profile payload (categories `distribution` and
    `conformance`, plus the release-owned conformance templates), the
    `host-evidence` fixtures, the two `docs/ai-workflow/` state templates and
    the `.gitignore` fragment as `.gitignore`, committed once.
    """
    root = Path(release_dir)
    version = verify_release(root)
    manifest = load_manifest(root)
    dest = Path(dest)
    if dest.exists() or dest.is_symlink():
        raise PackageError(f"{dest} already exists")
    dest.mkdir(parents=True)
    _git(dest, "init", "-q", "-b", "main")
    for key, value in (("user.email", "fixture@example.invalid"),
                       ("user.name", "Workflow Fixture"), ("commit.gpgsign", "false"),
                       ("maintenance.auto", "false"), ("gc.auto", "0")):
        _git(dest, "config", key, value)
    for record in manifest["artifacts"]:
        if record["category"] in FULL_PROFILE_CATEGORIES + ("host-evidence",):
            _place(root, record, dest, _record_mode(record))
    gitignore = None
    for record in manifest["templates"]:
        target = record["target_path"]
        if RELEASE_TEMPLATES.get(target) in FULL_PROFILE_CATEGORIES:
            _place(root, record, dest, FILE_MODE)
        elif target in CONFORMANCE_STATE_TEMPLATES:
            _place(root, record, dest, FILE_MODE)
        elif target == GITIGNORE_TEMPLATE:
            gitignore = record
    if gitignore is None:
        raise PackageError(f"release {version} has no {GITIGNORE_TEMPLATE} template")
    _place(root, dict(gitignore, target_path=".gitignore"), dest, FILE_MODE)
    _git(dest, "add", "-A")
    _git(dest, "commit", "-q", "-m", f"workflow v{version} conformance fixture")
    return dest


def remove_tree(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)
