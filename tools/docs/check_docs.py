#!/usr/bin/env python3
"""Offline documentation checks (standard library only).

Run ``python3 tools/docs/check_docs.py [--root DIR]``: exit 0 when clean, 1
with one line per problem. ``tools/docs/check_docs_test.py`` runs it on the
repository and exercises every rule on synthetic trees. Nothing here touches
the network.

Rules (the first and third are shared with the workflow-manager and
workflow-controller repositories):

1. Links and anchors: every relative Markdown link and ``#anchor`` in the
   user pages resolves to a file and, for Markdown targets, to a heading
   slug (GitHub's ``github-slugger`` rule). Links into the sibling
   repositories are checked for form only; other hosts must be allow-listed.
2. Slash commands: every ``/command`` a user page names exists as
   ``payload/.claude/commands/<command>.md``.
3. Page header, and no internal ids on user pages.

Out of scope: docs/ROADMAP.md, docs/ACTIVE_MILESTONE.md, docs/RELEASING.md,
docs/ai-workflow/ (this repository's own installation) and payload/.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import typing
from pathlib import Path
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

#: The user pages: header, internal-id and slash-command rules, and links.
USER_GLOBS = ("README.md", "docs/*.md", "docs/releases/*.md")
#: Pages the checks skip: Workflow commands rewrite the first two, the third
#: is maintainer content.
EXCLUDED = ("docs/ROADMAP.md", "docs/ACTIVE_MILESTONE.md", "docs/RELEASING.md")
COMMANDS_DIR = "payload/.claude/commands"

#: External hosts allowed besides github.com repository links.
ALLOWED_HOSTS = frozenset({"claude.com"})
GITHUB_OWNER = "RodrigoFAbreu"
GITHUB_REPOS = frozenset({"workflow-controller", "workflow-manager", "workflow"})

HEADER_RE = re.compile(r"^> For: .+\. Last checked with: .+\.$")
INTERNAL_ID_RES = (re.compile(r"\bCP\d+\b"), re.compile(r"\b[A-Z]{2,5}-R\d+-\d+\b"))


# ---------------------------------------------------------------------------
# Markdown reading.
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")


def split_fences(text: str) -> list[tuple[str, str, list[str]]]:
    """``[(kind, info, lines)]`` with ``kind`` ``"text"`` or ``"fence"``;
    ``info`` is a fence's info string. A fence closes on a line of the same
    character, at least as long, with nothing after it."""
    out: list[tuple[str, str, list[str]]] = []
    current: list[str] = []
    fence: tuple[str, int, str] | None = None
    for line in text.split("\n"):
        m = _FENCE_RE.match(line)
        if fence is None:
            if m:
                if current:
                    out.append(("text", "", current))
                current = []
                fence = (m.group(1)[0], len(m.group(1)), m.group(2).strip())
            else:
                current.append(line)
        else:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and not m.group(2).strip():
                out.append(("fence", fence[2], current))
                current = []
                fence = None
            else:
                current.append(line)
    if fence is not None:
        out.append(("fence", fence[2], current))
    elif current:
        out.append(("text", "", current))
    return out


def prose(text: str) -> str:
    """The text outside code fences."""
    return "\n".join("\n".join(lines) for kind, _, lines in split_fences(text) if kind == "text")


_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
_LINK_TEXT_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def headings(text: str) -> list[tuple[int, str]]:
    """``[(level, heading text)]`` for every ATX heading outside fences."""
    found = []
    for line in prose(text).split("\n"):
        m = _HEADING_RE.match(line)
        if m:
            found.append((len(m.group(1)), m.group(2)))
    return found


def slug_base(heading: str) -> str:
    """``github-slugger``: link markup reduced to its text, inline-code
    backticks removed but the code text kept, lowercased, every character
    but letters, digits, underscores, hyphens and spaces removed, spaces
    become hyphens."""
    text = _LINK_TEXT_RE.sub(r"\1", heading).replace("`", "")
    text = text.lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(text: str) -> list[str]:
    """Every anchor of a page, in heading order. A slug already taken gets
    the first ``-N`` (N from 1) that is itself not taken."""
    used: set[str] = set()
    result = []
    for _, heading in headings(text):
        base = slug_base(heading)
        slug = base
        n = 0
        while slug in used:
            n += 1
            slug = f"{base}-{n}"
        used.add(slug)
        result.append(slug)
    return result


_INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1", re.S)
# One scanner for CommonMark's inline-link grammar (spec 0.31.2, 6.3 "Links")
# and link-reference-definition grammar (4.7). Both forms share one
# destination and one title sub-grammar, so they cannot drift apart:
#   destination: ``<...>`` (no line break, spaces allowed) or a non-empty run
#                of non-space characters with balanced parentheses;
#   title:       ``"..."``, ``'...'`` or ``(...)``.
# Link text may contain balanced brackets. Backslash escapes the next character.
_DEFINITION_START_RE = re.compile(r"^(?:[ \t]{0,3}>)*[ \t]{0,3}\[(?!\^)([^\]\n]+)\]:", re.M)
_BLOCK_QUOTE_PREFIX_RE = re.compile(r"(?:[ \t]{0,3}>)*[ \t]*")
_SPACE_RE = re.compile(r"\s*")
_BLANKS_RE = re.compile(r"[ \t]*")


class LinkSpan(typing.NamedTuple):
    kind: str  # "inline" or "definition"
    label: str  # the definition's label; "" for an inline link
    target: str
    target_span: tuple[int, int]
    span: tuple[int, int]  # the whole link, from ``[`` to the closing ``)``/title


def _parse_destination(s: str, i: int) -> tuple[str, int, int] | None:
    """``(destination, start, end)`` of the destination at ``i``, or ``None``."""
    n = len(s)
    if i < n and s[i] == "<":
        j = i + 1
        while j < n and s[j] not in "<>\n":
            j += 2 if s[j] == "\\" else 1
        if j < n and s[j] == ">" and j > i + 1:
            return s[i + 1:j], i + 1, j + 1
        return None
    j, depth = i, 0
    while j < n and not s[j].isspace():
        c = s[j]
        if c == "\\" and j + 1 < n:
            j += 2
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            if depth == 0:
                break
            depth -= 1
        j += 1
    if j == i or depth != 0:
        return None
    return s[i:j], i, j


def _parse_title(s: str, i: int) -> int | None:
    """The end of the title starting at ``i``, or ``None``."""
    n = len(s)
    if i >= n or s[i] not in "\"'(":
        return None
    close = ")" if s[i] == "(" else s[i]
    j = i + 1
    while j < n and s[j] != close:
        if s[j] == "\\":
            j += 1
        elif s[i] == "(" and s[j] == "(":
            return None
        j += 1
    return j + 1 if j < n else None


def _matching_bracket(s: str, i: int) -> int | None:
    """The index of the ``]`` closing the ``[`` at ``i`` (brackets balance)."""
    depth = 0
    j = i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 1
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return None


def _inline_link(s: str, i: int) -> tuple[int, str, int, int] | None:
    """``(close, destination, start, stop)`` for the inline link opening at
    ``s[i] == "["`` (``stop`` is the index after ``)``)."""
    close = _matching_bracket(s, i)
    if close is None or close + 1 >= len(s) or s[close + 1] != "(":
        return None
    j = _SPACE_RE.match(s, close + 2).end()
    dest = _parse_destination(s, j)
    if dest is None:
        return None
    target, start, j = dest
    k = _SPACE_RE.match(s, j).end()
    if k > j:
        title_end = _parse_title(s, k)
        if title_end is not None:
            k = _SPACE_RE.match(s, title_end).end()
    if k < len(s) and s[k] == ")":
        return close, target, start, k + 1
    return None


def _scan_inline(s: str, lo: int, hi: int) -> list[tuple[int, int, int, int, str, bool]]:
    """Inline links opening in ``s[lo:hi]``: ``(open, start, stop, tstart,
    target, image)``. A link may not contain another link, so an outer link
    holding an inner (non-image) link is dropped."""
    found = []
    i = lo
    while i < hi:
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == "[":
            m = _inline_link(s, i)
            if m is not None:
                close, target, tstart, stop = m
                image = i > 0 and s[i - 1] == "!"
                inner = _scan_inline(s, i + 1, close)
                found.extend(inner)
                if image or not any(not x[5] for x in inner):
                    found.append((i, i, stop, tstart, target, image))
                i = stop
                continue
        i += 1
    return found


def _scan_definitions(s: str) -> list[LinkSpan]:
    found = []
    for m in _DEFINITION_START_RE.finditer(s):
        j = m.end()
        k = _BLANKS_RE.match(s, j).end()
        if k < len(s) and s[k] == "\n":
            k = _BLOCK_QUOTE_PREFIX_RE.match(s, k + 1).end()
        dest = _parse_destination(s, k)
        if dest is None:
            continue
        target, start, end = dest
        stop = None
        for candidate in (_title_on_line(s, end), end):
            if candidate is None:
                continue
            rest = _BLANKS_RE.match(s, candidate).end()
            if rest >= len(s) or s[rest] == "\n":
                stop = rest
                break
        if stop is not None:
            found.append(LinkSpan("definition", m.group(1), target, (start, end), (m.start(), stop)))
    return found


def _title_on_line(s: str, end: int) -> int | None:
    k = _BLANKS_RE.match(s, end).end()
    return _parse_title(s, k) if k > end else None


def scan_links(text: str) -> list[LinkSpan]:
    """Every inline link (in order) then every link-reference definition (in
    order) of ``text``."""
    inline = [LinkSpan("inline", "", target, (tstart, tstart + len(target)), (o, stop))
              for o, _, stop, tstart, target, _ in sorted(_scan_inline(text, 0, len(text)))]
    return inline + _scan_definitions(text)


# A label starting with ``^`` is a GitHub footnote, not a link.
# ``a[i][j]`` (a word character right before the ``[``) is prose, not a
# reference link; put such text in a code span.
_REFERENCE_RE = re.compile(r"(?<![\w\]])\[(?!\^)((?:[^\]\n]|\n)+?)\]\[([^\]\n]*)\]")
_AUTOLINK_RE = re.compile(r"<([a-z][a-z0-9+.-]*:[^<>\s]+)>", re.I)
# GFM extended autolinks: a bare ``http(s)://`` or ``www.`` URL in prose.
_BARE_URL_RE = re.compile(r"(?<![\w/@.=-])((?:https?://|www\.)[^\s<]+)", re.I)


def _body(text: str) -> str:
    """Prose with inline code blanked out."""
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), prose(text))


def _label(label: str) -> str:
    return " ".join(label.lower().split())


def _blank(match: re.Match) -> str:
    return " " * len(match.group(0))


def _trim_bare_url(url: str) -> str:
    """GFM: drop trailing punctuation and an unbalanced closing ``)``."""
    while url:
        last = url[-1]
        if last in "?!.,:*_~;'\"":
            url = url[:-1]
        elif last == ")" and url.count(")") > url.count("("):
            url = url[:-1]
        else:
            break
    return url


def bare_urls(text: str) -> list[str]:
    """Bare URLs of ``text`` (already free of inline links, definitions,
    reference links and ``<...>`` autolinks, which are blanked first)."""
    for link in reversed(sorted(scan_links(text), key=lambda x: x.span)):
        text = text[:link.span[0]] + " " * (link.span[1] - link.span[0]) + text[link.span[1]:]
    for pattern in (_REFERENCE_RE, _AUTOLINK_RE):
        text = pattern.sub(_blank, text)
    found = []
    for m in _BARE_URL_RE.finditer(text):
        url = _trim_bare_url(m.group(1))
        found.append("https://" + url if url.lower().startswith("www.") else url)
    return found


def links(text: str) -> list[str]:
    """The target of every link form outside code fences and inline code:
    inline links, reference-link definitions, ``<...>`` autolinks and bare
    URLs."""
    body = _body(text)
    found = [link.target for link in scan_links(body)]
    found += [m.group(1) for m in _AUTOLINK_RE.finditer(body)]
    found += bare_urls(body)
    return found


def blank_link_targets(text: str) -> str:
    """``text`` with every link target (all forms of :func:`links`) removed,
    so a target is never scanned as prose."""
    for link in sorted(scan_links(text), key=lambda x: x.target_span, reverse=True):
        text = text[:link.target_span[0]] + text[link.target_span[1]:]
    text = _AUTOLINK_RE.sub(lambda m: m.group(0).replace(m.group(1), ""), text)
    return _BARE_URL_RE.sub(lambda m: m.group(0).replace(_trim_bare_url(m.group(1)), ""), text)


def undefined_references(text: str) -> list[str]:
    """Labels used by ``[text][label]`` / ``[label][]`` with no definition."""
    body = _body(text)
    defined = {_label(link.label) for link in scan_links(body) if link.kind == "definition"}
    missing = []
    for m in _REFERENCE_RE.finditer(body):
        label = _label(m.group(2) or m.group(1))
        if label not in defined:
            missing.append(label)
    return missing


# ---------------------------------------------------------------------------
# Rule 1: links and anchors.
# ---------------------------------------------------------------------------


def link_pages(root: Path) -> list[Path]:
    found: set[Path] = set()
    for pattern in USER_GLOBS:
        found.update(p for p in root.glob(pattern) if p.is_file())
    excluded = {root / e for e in EXCLUDED}
    return sorted(p for p in found if p not in excluded)


def external_link_problem(target: str) -> str | None:
    """``None`` when the external link is acceptable."""
    m = re.match(r"^https?://([^/?#]+)(/[^?#]*)?(?:[?#].*)?$", target)
    if not m:
        return "malformed URL"
    host = m.group(1).lower()
    path = (m.group(2) or "").strip("/")
    if host in ALLOWED_HOSTS:
        return None
    if host != "github.com":
        return f"host {host!r} is not allow-listed"
    parts = path.split("/") if path else []
    if len(parts) < 2 or parts[0] != GITHUB_OWNER:
        return f"github.com link must name {GITHUB_OWNER}/<repository>"
    repo = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
    if repo not in GITHUB_REPOS:
        return f"unknown repository {repo!r} (known: {', '.join(sorted(GITHUB_REPOS))})"
    rest = parts[2:]
    if not rest:
        return None
    kind = rest[0]
    if kind in ("blob", "tree"):
        need = 3 if kind == "blob" else 2
        if len(rest) >= need:
            return None
        return f"{kind} link needs a ref" + (" and a file path" if kind == "blob" else "")
    if kind == "releases":
        return None
    if kind in ("issues", "pull"):
        return None if len(rest) == 2 and rest[1].isdigit() else f"{kind} link needs a number"
    return f"unsupported github.com path form {kind!r}"


def check_links(root: Path) -> list[str]:
    problems: list[str] = []
    cache: dict[Path, list[str]] = {}

    def page_anchors(path: Path) -> list[str]:
        if path not in cache:
            cache[path] = anchors(path.read_text(encoding="utf-8"))
        return cache[path]

    for page in link_pages(root):
        rel = page.relative_to(root).as_posix()
        page_text = page.read_text(encoding="utf-8")
        for label in undefined_references(page_text):
            problems.append(f"{rel}: reference link [{label}] has no definition")
        for target in links(page_text):
            if target.startswith("mailto:"):
                continue
            if re.match(r"^[a-z][a-z0-9+.-]*://", target, re.I):
                problem = external_link_problem(target)
                if problem:
                    problems.append(f"{rel}: external link {target!r}: {problem}")
                continue
            path_part, _, fragment = target.partition("#")
            path_part = unquote(path_part)
            dest = page if path_part == "" else (page.parent / path_part).resolve()
            if not dest.exists():
                problems.append(f"{rel}: link {target!r} points at a missing file")
                continue
            if fragment and dest.is_file() and dest.suffix == ".md":
                if fragment not in page_anchors(dest):
                    problems.append(f"{rel}: link {target!r} points at a missing heading")
    return problems


# ---------------------------------------------------------------------------
# Rule 3: page header and internal ids.
# ---------------------------------------------------------------------------


def work_item_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    state = root / "docs/ai-workflow/WORKFLOW_STATE.json"
    if state.is_file():
        try:
            ids.update(json.loads(state.read_text(encoding="utf-8")).get("work_items", {}))
        except (ValueError, AttributeError):
            pass
    completed = root / "docs/milestones/completed"
    if completed.is_dir():
        ids.update(p.stem for p in completed.glob("*.md"))
    return ids


def header_problem(text: str) -> str | None:
    lines = prose(text).split("\n")
    for i, line in enumerate(lines):
        if re.match(r"^# \S", line):
            for following in lines[i + 1:]:
                if following.strip():
                    return None if HEADER_RE.match(following.strip()) else (
                        "the first line after the title must be '> For: <reader>. Last checked with: <versions>.'")
            return "no header after the title"
    return "no H1 title"


def internal_id_problems(text: str, ids: set[str]) -> list[str]:
    body = blank_link_targets(text)
    found = []
    for pattern in INTERNAL_ID_RES:
        found.extend(sorted({m.group(0) for m in pattern.finditer(body)}))
    for item in sorted(ids):
        if re.search(r"(?<![\w-])" + re.escape(item) + r"(?![\w-])", body):
            found.append(item)
    return found


_SLASH_COMMAND_RE = re.compile(r"(?:^|(?<=[\s`(]))/([a-z][a-z0-9-]*)(?![\w/.-]|\w)", re.M)


def slash_commands(text: str) -> list[str]:
    """Every ``/command`` named in ``text``, in prose, inline code and fences."""
    body = blank_link_targets(text)
    return sorted({m.group(1) for m in _SLASH_COMMAND_RE.finditer(body)})


# ---------------------------------------------------------------------------
# Rule 2: slash commands.
# ---------------------------------------------------------------------------


def check_commands(root: Path) -> list[str]:
    problems = []
    for page in link_pages(root):
        rel = page.relative_to(root).as_posix()
        for name in slash_commands(page.read_text(encoding="utf-8")):
            if not (root / COMMANDS_DIR / f"{name}.md").is_file():
                problems.append(f"{rel}: /{name} is not a command in {COMMANDS_DIR}/")
    return problems


def check_pages(root: Path) -> list[str]:
    problems = []
    ids = work_item_ids(root)
    for page in link_pages(root):
        rel = page.relative_to(root).as_posix()
        text = page.read_text(encoding="utf-8")
        problem = header_problem(text)
        if problem:
            problems.append(f"{rel}: {problem}")
        for found in internal_id_problems(text, ids):
            problems.append(f"{rel}: internal id {found!r} on a user page")
    return problems


def check_tree(root: Path) -> list[str]:
    """Every problem in the tree at ``root``."""
    return check_links(root) + check_commands(root) + check_pages(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline documentation checks.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root to check")
    args = parser.parse_args(argv)
    problems = check_tree(Path(args.root).resolve())
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
