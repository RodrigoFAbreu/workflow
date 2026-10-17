"""The `manager` block of a release's `manifest.json`: validate, measure, check.

The Workflow Manager's release-metadata contract (schema version 1) lets a
release carry what the Manager used to hard-code per release. The block's
authored fields are written by hand in the release source's `manifest.json`;
`conformance.suites` is computed here, from the staged conformance fixture, and
CI checks all of it (`docs/RELEASING.md`, "The Manager metadata block").
Stdlib only.

    validate(block)            the contract's rules, as a list of problems
    measure_suites(fixture)    the test count of each suite the managed
                               conformance workflow names
    check(manifest, version, measured, manager_releases)
                               checks (a), (b), (c) and (e) of D-Manager
    check_pin(block, pin)      check (g): the pinned Manager is the minimum

Every problem names the key it is about. Nothing here raises for a malformed
block: it is reported.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

#: The newest release whose Manager data is built into the Manager: a manifest
#: at or below it never carries a block, a newer one always does.
LAST_BLOCKLESS = (2, 12, 0)
SCHEMA_VERSION = 1

CONFORMANCE_TEMPLATE = ".github/workflows/workflow-conformance.yml"
SUITES_RE = re.compile(r'^\s*suites="([^"\n]*)"\s*$', re.MULTILINE)
MEASURE_TIMEOUT = 900

_MANAGER_KEYS = ("schema_version", "min_manager_version", "downgrade_boundary",
                 "new_work_only", "gate_default_change", "conformance")
_BOUNDARY_KEYS = ("posture", "undetectable", "signals")
_SIGNAL_KEYS = ("name", "label", "detect")
_CONFORMANCE_KEYS = ("suites", "portability_exceptions")
_EXCEPTION_KEYS = ("suite", "test", "requires", "reason", "defect")

#: The closed detector vocabulary, version 1: kind -> its keys.
DETECTORS = {
    "state-key": ("key",),
    "state-value": ("key", "value"),
    "item-governing": ("value",),
    "item-phase": ("phases",),
    "item-field": ("key", "value"),
}

_MANAGER_VERSION_RE = re.compile(r"^[0-9]+(\.[0-9]+)*$")
_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_TAG_RE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

#: The record keys `gh release list --json tagName,isDraft,isPrerelease,publishedAt` writes.
RECORD_FIELDS = ("tagName", "isDraft", "isPrerelease", "publishedAt")


class MeasureError(RuntimeError):
    """The suites could not be counted."""


def version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


# -- the contract ----------------------------------------------------------------


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (str, bool)) or (
        isinstance(value, int) and not isinstance(value, bool))


def _unknown(obj: dict, allowed: tuple[str, ...], where: str) -> list[str]:
    return [f"{where}.{key}: unknown key" for key in obj if key not in allowed]


def _text(obj: dict, key: str, where: str, *, required: bool = False,
          nullable: bool = False) -> list[str]:
    if key not in obj:
        return [f"{where}.{key}: required"] if required else []
    value = obj[key]
    if isinstance(value, str) or (nullable and value is None):
        return []
    return [f"{where}.{key}: must be {'a string or null' if nullable else 'a string'}"]


def _detector(detect: object, where: str) -> list[str]:
    if not isinstance(detect, dict):
        return [f"{where}: must be an object"]
    kind = detect.get("kind")
    if kind not in DETECTORS:
        return [f"{where}.kind: {kind!r} is not a detector kind of the closed vocabulary "
                f"({', '.join(DETECTORS)})"]
    problems = _unknown(detect, ("kind",) + DETECTORS[kind], where)
    for key in DETECTORS[kind]:
        if key not in detect:
            problems.append(f"{where}.{key}: required by the {kind!r} detector")
        elif key == "key":
            if not isinstance(detect[key], str) or not detect[key]:
                problems.append(f"{where}.key: must be a non-empty string")
        elif key == "value" and kind == "item-governing":
            if not isinstance(detect[key], str):
                problems.append(f"{where}.value: must be a string for the {kind!r} detector")
        elif key == "value":
            if not _is_scalar(detect[key]):
                problems.append(f"{where}.value: must be a JSON scalar "
                                f"(string, integer, boolean or null)")
        elif key == "phases":
            phases = detect[key]
            if not (isinstance(phases, list) and phases
                    and all(isinstance(p, str) for p in phases)):
                problems.append(f"{where}.phases: must be a non-empty list of strings")
    return problems


def _boundary(boundary: object) -> list[str]:
    where = "manager.downgrade_boundary"
    if not isinstance(boundary, dict):
        return [f"{where}: must be an object"]
    problems = _unknown(boundary, _BOUNDARY_KEYS, where)
    problems += _text(boundary, "posture", where, required=True)
    problems += _text(boundary, "undetectable", where, nullable=True)
    signals = boundary.get("signals", [])
    if not isinstance(signals, list):
        return problems + [f"{where}.signals: must be a list"]
    for index, signal in enumerate(signals):
        at = f"{where}.signals[{index}]"
        if not isinstance(signal, dict):
            problems.append(f"{at}: must be an object")
            continue
        problems += _unknown(signal, _SIGNAL_KEYS, at)
        name = signal.get("name")
        if not isinstance(name, str) or not _KEBAB_RE.fullmatch(name):
            problems.append(f"{at}.name: must be a kebab-case string, got {name!r}")
        problems += _text(signal, "label", at, required=True)
        if "detect" not in signal:
            problems.append(f"{at}.detect: required")
        else:
            problems += _detector(signal["detect"], f"{at}.detect")
    return problems


def _conformance(conformance: object) -> list[str]:
    where = "manager.conformance"
    if not isinstance(conformance, dict):
        return [f"{where}: must be an object"]
    problems = _unknown(conformance, _CONFORMANCE_KEYS, where)
    for key in _CONFORMANCE_KEYS:
        if key not in conformance:
            problems.append(f"{where}.{key}: required (suites and portability_exceptions "
                            f"come together)")
    suites = conformance.get("suites")
    if "suites" in conformance:
        if not isinstance(suites, dict):
            problems.append(f"{where}.suites: must be an object")
        else:
            for name, count in suites.items():
                if not isinstance(name, str) or not name:
                    problems.append(f"{where}.suites: a suite name must be a non-empty string")
                elif not _is_count(count):
                    problems.append(f"{where}.suites[{name!r}]: must be a non-negative "
                                    f"integer, got {count!r}")
    exceptions = conformance.get("portability_exceptions")
    if "portability_exceptions" in conformance:
        if not isinstance(exceptions, list):
            problems.append(f"{where}.portability_exceptions: must be a list")
        else:
            for index, exc in enumerate(exceptions):
                at = f"{where}.portability_exceptions[{index}]"
                if not isinstance(exc, dict):
                    problems.append(f"{at}: must be an object")
                    continue
                problems += _unknown(exc, _EXCEPTION_KEYS, at)
                for key in ("suite", "test", "reason"):
                    problems += _text(exc, key, at, required=True)
                for key in ("requires", "defect"):
                    problems += _text(exc, key, at, nullable=True)
    return problems


def validate(block: object) -> list[str]:
    """The problems of `block` under the contract, schema version 1; empty
    when it is valid. Another schema version, an unknown key and an unknown
    detector kind are problems, never defaulted."""
    if not isinstance(block, dict):
        return ["manager: must be an object"]
    problems = _unknown(block, _MANAGER_KEYS, "manager")
    if "schema_version" not in block:
        problems.append("manager.schema_version: required")
    elif (not isinstance(block["schema_version"], int) or isinstance(block["schema_version"], bool)
          or block["schema_version"] != SCHEMA_VERSION):
        problems.append(f"manager.schema_version: must be {SCHEMA_VERSION}, got "
                        f"{block['schema_version']!r}")
    if "min_manager_version" in block:
        value = block["min_manager_version"]
        if not isinstance(value, str) or not _MANAGER_VERSION_RE.fullmatch(value):
            problems.append(f"manager.min_manager_version: must be digits separated by dots "
                            f"(1.13.0), got {value!r}")
    if "downgrade_boundary" in block:
        problems += _boundary(block["downgrade_boundary"])
    if "new_work_only" in block:
        notes = block["new_work_only"]
        if not (isinstance(notes, list) and all(isinstance(n, str) for n in notes)):
            problems.append("manager.new_work_only: must be a list of strings")
    problems += _text(block, "gate_default_change", "manager")
    if "conformance" in block:
        problems += _conformance(block["conformance"])
    return problems


# -- the publication evidence -----------------------------------------------------


def validate_evidence(evidence: object) -> list[str]:
    """The problems of the committed Manager release list: an object with the
    `repository`, the `taken` date and `releases`, each a complete record of
    the four fields `gh release list` writes. A record missing a field makes
    the evidence invalid; it is never counted."""
    if not isinstance(evidence, dict):
        return ["manager releases: must be an object"]
    problems = _unknown(evidence, ("repository", "taken", "releases"), "manager releases")
    for key in ("repository", "taken"):
        value = evidence.get(key)
        if not isinstance(value, str) or not value:
            problems.append(f"manager releases.{key}: must be a non-empty string")
    taken = evidence.get("taken")
    if isinstance(taken, str) and taken and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", taken):
        problems.append(f"manager releases.taken: must be a YYYY-MM-DD date, got {taken!r}")
    releases = evidence.get("releases")
    if not isinstance(releases, list):
        return problems + ["manager releases.releases: must be a list"]
    seen = set()
    for index, record in enumerate(releases):
        at = f"manager releases.releases[{index}]"
        if not isinstance(record, dict):
            problems.append(f"{at}: must be an object")
            continue
        problems += _unknown(record, RECORD_FIELDS, at)
        for key in RECORD_FIELDS:
            if key not in record:
                problems.append(f"{at}.{key}: required (an incomplete record is never counted)")
        for key in ("isDraft", "isPrerelease"):
            if key in record and not isinstance(record[key], bool):
                problems.append(f"{at}.{key}: must be a boolean")
        for key in ("tagName", "publishedAt"):
            if key in record and not (isinstance(record[key], str) and record[key]):
                problems.append(f"{at}.{key}: must be a non-empty string")
        tag = record.get("tagName")
        if isinstance(tag, str):
            if tag in seen:
                problems.append(f"{at}.tagName: {tag!r} appears twice")
            seen.add(tag)
    return problems


def published_versions(evidence: dict) -> list[str]:
    """The versions that count: an exact `vX.Y.Z` tag, neither draft nor
    prerelease (`workflow-manager-v1.0.0` and any other tag are ignored). Assumes
    `validate_evidence` found no problem."""
    counted = []
    for record in evidence["releases"]:
        match = _TAG_RE.match(record["tagName"])
        if match and not record["isDraft"] and not record["isPrerelease"]:
            counted.append(record["tagName"][1:])
    return counted


def newest_published(evidence: dict) -> str | None:
    counted = published_versions(evidence)
    return max(counted, key=version_tuple) if counted else None


# -- measurement ------------------------------------------------------------------

_MEASURE_SNIPPET = r"""
import importlib, json, sys, unittest
scripts = sys.argv[1]
sys.path.insert(0, scripts)
result = {}
for name in sys.argv[2:]:
    module = importlib.import_module(name[:-3])
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    failed, count = [], 0
    stack = [suite]
    while stack:
        item = stack.pop()
        if isinstance(item, unittest.TestSuite):
            stack.extend(item)
        elif type(item).__name__ == "_FailedTest":
            failed.append(item.id())
        else:
            count += 1
    result[name] = {"count": count, "failed": failed}
print("MEASURED " + json.dumps(result))
"""


def suite_names(template_text: str) -> list[str]:
    """The suite files the managed conformance workflow names (its one
    `suites="..."` line)."""
    found = SUITES_RE.findall(template_text)
    if len(found) != 1:
        raise MeasureError(f"the conformance workflow has {len(found)} suites=\"...\" lines, "
                           f"expected exactly one")
    names = found[0].split()
    if not names:
        raise MeasureError("the conformance workflow names no suite")
    for name in names:
        if not re.fullmatch(r"[A-Za-z0-9_]+\.py", name):
            raise MeasureError(f"the conformance workflow names {name!r}, not a suite file")
    return names


def measure_suites(fixture: Path) -> dict[str, int]:
    """The number of test cases of each suite the conformance workflow names,
    loaded as `unittest.main()` loads a module (`loadTestsFromModule`), in one
    subprocess with `scripts/` as its working directory and bytecode off. A suite
    that does not exist, does not import or holds a loader error (a
    `_FailedTest`) is refused."""
    fixture = Path(fixture)
    workflow = fixture / CONFORMANCE_TEMPLATE
    if not workflow.is_file():
        raise MeasureError(f"{fixture} has no {CONFORMANCE_TEMPLATE}")
    names = suite_names(workflow.read_text())
    scripts = fixture / "scripts"
    for name in names:
        if not (scripts / name).is_file():
            raise MeasureError(f"the conformance workflow names {name}, which {scripts} lacks")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([sys.executable, "-B", "-c", _MEASURE_SNIPPET, str(scripts), *names],
                              cwd=scripts, env=env, capture_output=True, text=True,
                              timeout=MEASURE_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MeasureError(f"cannot count the suites: {exc}") from exc
    line = next((l for l in reversed(proc.stdout.splitlines()) if l.startswith("MEASURED ")), None)
    if proc.returncode != 0 or line is None:
        raise MeasureError(f"counting the suites failed (exit {proc.returncode}): "
                           f"{(proc.stderr or proc.stdout).strip()[-1500:]}")
    result = json.loads(line[len("MEASURED "):])
    counts = {}
    for name in names:
        failed = result[name]["failed"]
        if failed:
            raise MeasureError(f"{name} has loader errors: {', '.join(failed)}")
        counts[name] = result[name]["count"]
    return counts


# -- the checks -------------------------------------------------------------------


def check(manifest: dict, version: str, measured: dict | None, manager_releases: object) -> list[str]:
    """Checks (a), (b), (c) and (e) of D-Manager, as a list of problems.

    (e) a manifest at or below 2.12.0 has no block, a newer one has one;
    (a) the block is valid; (b) `suites` equals `measured`; (c)
    `min_manager_version` is not newer than the newest published Manager release
    in the committed evidence `manager_releases` (invalid evidence is a problem).
    `measured` is `None` only when the caller could not measure (then (b) is
    not judged)."""
    if not _VERSION_RE.match(version):
        return [f"version {version!r} is not X.Y.Z"]
    old = tuple(int(p) for p in version.split(".")) <= LAST_BLOCKLESS
    block = manifest.get("manager") if isinstance(manifest, dict) else None
    if old:
        return ([f"manifest {version} has a manager block: releases up to "
                 f"{'.'.join(map(str, LAST_BLOCKLESS))} are published without one and never "
                 f"gain one"] if "manager" in manifest else [])
    if "manager" not in manifest:
        return [f"manifest {version} has no manager block: every release after "
                f"{'.'.join(map(str, LAST_BLOCKLESS))} carries one"]
    problems = validate(block)
    if problems:
        return problems
    conformance = block.get("conformance")
    if measured is not None:
        if not isinstance(conformance, dict) or "suites" not in conformance:
            problems.append("manager.conformance.suites: required in a release's block "
                            "(computed by release.py manager-block --write)")
        elif conformance["suites"] != measured:
            problems.append(f"manager.conformance.suites differs from the measurement: "
                            f"{_suites_diff(conformance['suites'], measured)}; run "
                            f"release.py manager-block --write")
    minimum = block.get("min_manager_version")
    if minimum is not None:
        evidence = validate_evidence(manager_releases)
        if evidence:
            problems += evidence
        else:
            newest = newest_published(manager_releases)
            if newest is None:
                problems.append("manager.min_manager_version: the evidence lists no published "
                                "Manager release")
            elif version_tuple(minimum) > version_tuple(newest):
                problems.append(f"manager.min_manager_version {minimum} is newer than the "
                                f"newest published Manager release {newest} in "
                                f"tools/release/manager-releases.json: publish that Manager "
                                f"first, then refresh the evidence")
    return problems


def _suites_diff(recorded: dict, measured: dict) -> str:
    parts = []
    for name in sorted(set(recorded) | set(measured)):
        if recorded.get(name) != measured.get(name):
            parts.append(f"{name} recorded {recorded.get(name, 'absent')}, "
                         f"measured {measured.get(name, 'absent')}")
    return "; ".join(parts)


def check_pin(block: dict, pin: object) -> list[str]:
    """Check (g): the Manager `tools/release/manager-pin.json` pins is exactly
    the block's `min_manager_version`, so the update fixture and the whole
    `checks` job run the minimum Manager the release says it needs."""
    minimum = block.get("min_manager_version") if isinstance(block, dict) else None
    if minimum is None:
        return []
    version = pin.get("version") if isinstance(pin, dict) else None
    if version != minimum:
        return [f"tools/release/manager-pin.json pins Manager {version!r}, but "
                f"manager.min_manager_version is {minimum}: advance the pin"]
    return []


# -- writing the computed field ------------------------------------------------------


def replace_suites(manifest_text: str, measured: dict[str, int]) -> str:
    """`manifest_text` with the value of the block's `conformance.suites`
    replaced by `measured`, every other byte untouched. The manifest is the
    two-space-indented JSON the release tooling writes; the block, its
    `conformance` and its `suites` must already exist."""
    decoder = json.JSONDecoder()
    marker = '\n  "manager": '
    start = manifest_text.find(marker)
    if start == -1:
        raise MeasureError("manifest.json has no top-level manager block to write suites into")
    block_start = start + len(marker)
    _, block_end = decoder.raw_decode(manifest_text, block_start)
    conformance_marker = '\n    "conformance": '
    c = manifest_text.find(conformance_marker, block_start, block_end)
    if c == -1:
        raise MeasureError("the manager block has no conformance object to write suites into")
    c_start = c + len(conformance_marker)
    _, c_end = decoder.raw_decode(manifest_text, c_start)
    suites_marker = '\n      "suites": '
    s = manifest_text.find(suites_marker, c_start, c_end)
    if s == -1:
        raise MeasureError("manager.conformance has no suites to replace")
    s_start = s + len(suites_marker)
    _, s_end = decoder.raw_decode(manifest_text, s_start)
    rendered = json.dumps(measured, indent=2).replace("\n", "\n      ")
    return manifest_text[:s_start] + rendered + manifest_text[s_end:]
