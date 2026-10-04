"""Tests for ``tools/docs/check_docs.py``: the repository's own documentation
is clean, and every rule fails on a synthetic tree that breaks it and passes
on one that does not."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_spec = importlib.util.spec_from_file_location("check_docs", REPO_ROOT / "tools" / "docs" / "check_docs.py")
check_docs = importlib.util.module_from_spec(_spec)
sys.modules["check_docs"] = check_docs
_spec.loader.exec_module(check_docs)

HEADER = "> For: readers. Last checked with: Workflow 2.8.0, Workflow Manager 1.4.0."


class Tree:
    """A throwaway documentation tree."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def check(self) -> list[str]:
        return check_docs.check_links(self.root)

    def close(self) -> None:
        self._tmp.cleanup()


class TreeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tree = Tree()
        self.addCleanup(self.tree.close)


class LiveRepositoryTest(TreeTestCase):
    def test_the_repository_documentation_is_clean(self) -> None:
        self.assertEqual(check_docs.check_tree(REPO_ROOT), [])

    def test_the_command_line_entry_point_exits_zero_on_the_repository(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_docs.main(["--root", str(REPO_ROOT)]), 0)

    def test_the_command_line_entry_point_exits_one_with_a_problem(self) -> None:
        self.tree.write("README.md", "# T\n\n[x](missing.md)\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_docs.main(["--root", str(self.tree.root)]), 1)


class SlugTest(unittest.TestCase):
    def test_underscores_and_literal_hyphens_are_kept(self) -> None:
        self.assertEqual(check_docs.slug_base("A_B-c d"), "a_b-c-d")
        self.assertEqual(check_docs.slug_base("Exit 10: gate (human)"), "exit-10-gate-human")

    def test_inline_code_headings_keep_the_code_text(self) -> None:
        self.assertEqual(check_docs.anchors("### `WORKFLOW_QUERY_FAILED` and `workflow_query_failed`\n"),
                         ["workflow_query_failed-and-workflow_query_failed"])

    def test_collisions_are_allocated_against_used_anchors(self) -> None:
        self.assertEqual(check_docs.anchors("# foo-1\n# foo\n# foo\n"), ["foo-1", "foo", "foo-2"])

    def test_headings_in_fences_are_not_anchors(self) -> None:
        self.assertEqual(check_docs.anchors("# a\n```\n# b\n```\n"), ["a"])


class LinkRuleTest(TreeTestCase):
    def test_a_good_tree_passes(self) -> None:
        self.tree.write("README.md", "# R\n\n[g](docs/guide/g.md#sub-title) [self](#r)\n")
        self.tree.write("docs/guide/g.md", "# G\n\n## Sub title\n")
        self.assertEqual(self.tree.check(), [])

    def test_a_missing_file_fails(self) -> None:
        self.tree.write("README.md", "# R\n\n[g](docs/none.md)\n")
        self.assertTrue(any("missing file" in p for p in self.tree.check()))

    def test_a_missing_anchor_fails(self) -> None:
        self.tree.write("README.md", "# R\n\n[g](docs/guide/g.md#nope)\n")
        self.tree.write("docs/guide/g.md", "# G\n")
        self.assertTrue(any("missing heading" in p for p in self.tree.check()))

    def test_anchors_are_case_sensitive(self) -> None:
        self.tree.write("README.md", "# R\n\n[g](docs/guide/g.md#Upgrade)\n")
        self.tree.write("docs/guide/g.md", "# G\n\n## Upgrade\n")
        self.assertTrue(self.tree.check())

    def test_links_in_code_are_skipped(self) -> None:
        self.tree.write("README.md", "# R\n\n`[a](gone.md)`\n\n```\n[b](gone.md)\n```\n")
        self.assertEqual(self.tree.check(), [])


    def test_excluded_pages_are_out_of_scope(self) -> None:
        self.tree.write("docs/ROADMAP.md", "# R\n\n[x](gone.md)\n")
        self.tree.write("docs/ACTIVE_MILESTONE.md", "# R\n\n[x](gone.md)\n")
        self.tree.write("docs/RELEASING.md", "# R\n\n[x](gone.md)\n")
        self.tree.write("docs/ai-workflow/a.md", "# R\n\n[x](gone.md)\n")
        self.tree.write("payload/docs/a.md", "# R\n\n[x](gone.md)\n")
        self.assertEqual(self.tree.check(), [])

    def test_reference_links_are_validated(self) -> None:
        self.tree.write("README.md", "# R\n\n[g][g] [h][] [s][s]\n\n[g]: docs/guide/g.md#sub\n[h]: #r\n[s]: #r\n")
        self.tree.write("docs/guide/g.md", "# G\n\n## Sub\n")
        self.assertEqual(self.tree.check(), [])
        self.tree.write("README.md", "# R\n\n[g][g]\n\n[g]: docs/missing.md\n")
        self.assertTrue(any("missing file" in p for p in self.tree.check()))
        self.tree.write("README.md", "# R\n\n[g][g]\n\n[g]: #missing\n")
        self.assertTrue(any("missing heading" in p for p in self.tree.check()))
        self.tree.write("README.md", "# R\n\n[g][nope]\n")
        self.assertTrue(any("no definition" in p for p in self.tree.check()))

    def test_autolinks_are_validated(self) -> None:
        self.tree.write("README.md", "# R\n\n<https://github.com/RodrigoFAbreu/workflow>\n")
        self.assertEqual(self.tree.check(), [])
        self.tree.write("README.md", "# R\n\n<https://github.com/RodrigoFAbreu/SignalHub>\n")
        self.assertTrue(any("unknown repository" in p for p in self.tree.check()))
        self.tree.write("README.md", "# R\n\n<https://example.com/x>\n")
        self.assertTrue(any("not allow-listed" in p for p in self.tree.check()))

    def test_bare_urls_are_validated(self) -> None:
        ok = "https://github.com/RodrigoFAbreu/workflow"
        self.tree.write("README.md", f"# R\n\nSee {ok}. And ({ok}), or {ok}/.\n")
        self.assertEqual(self.tree.check(), [])
        self.tree.write("README.md", "# R\n\nSee https://github.com/RodrigoFAbreu/SignalHub here.\n")
        self.assertTrue(any("unknown repository" in p for p in self.tree.check()))
        self.tree.write("README.md", "# R\n\nSee https://example.com/x for more.\n")
        self.assertTrue(any("not allow-listed" in p for p in self.tree.check()))
        self.tree.write("README.md", "# R\n\nSee www.example.com/x for more.\n")
        self.assertTrue(any("not allow-listed" in p for p in self.tree.check()))

    def test_bare_urls_skip_code_and_are_not_double_counted(self) -> None:
        self.tree.write("README.md", "# R\n\n`https://example.com/a`\n\n```\nhttps://example.com/b\n```\n")
        self.assertEqual(self.tree.check(), [])
        self.assertEqual(check_docs.links("[https://example.com/x](https://example.com/x)\n"),
                         ["https://example.com/x"])
        self.assertEqual(check_docs.links("<https://example.com/x> [a][g]\n\n[g]: https://example.com/y\n"),
                         ["https://example.com/y", "https://example.com/x"])
        self.assertEqual(check_docs.links("a https://example.com/x.\n"), ["https://example.com/x"])

    def test_block_quoted_definitions_resolve_and_are_validated(self) -> None:
        self.tree.write("README.md", "# R\n\n> [g][g]\n>\n> [g]: docs/g.md\n")
        self.tree.write("docs/g.md", "# G\n")
        self.assertEqual(self.tree.check(), [])
        self.tree.write("README.md", "# R\n\n> [g][g]\n>\n> [g]: docs/missing.md\n")
        self.assertTrue(any("missing file" in p for p in self.tree.check()))

    def test_definitions_with_parenthesized_titles_and_next_line_destinations(self) -> None:
        self.tree.write("docs/g.md", "# G\n\n## Sub\n")
        forms = ["[g]: {t} (Guide)\n", "[g]:\n  {t}\n", "[g]:\n  {t} (Guide)\n"]
        for form in forms:
            for use in ("[g]", "[guide][g]"):
                def put(target: str) -> list[str]:
                    self.tree.write("README.md", f"# R\n\n{use}\n\n" + form.format(t=target))
                    return self.tree.check()
                self.assertEqual(put("docs/g.md#sub"), [], (form, use))
                self.assertTrue(any("missing file" in p for p in put("docs/missing.md")), (form, use))
                self.assertTrue(any("missing heading" in p for p in put("#missing")), (form, use))
                self.assertTrue(any("missing heading" in p for p in put("docs/g.md#nope")), (form, use))
        self.tree.write("README.md", "# R\n\n[guide][g]\n\n[g]: #r (Guide)\n")
        self.assertEqual(self.tree.check(), [])
        self.tree.write("README.md", "# R\n\n[guide][nope]\n\n[g]: #r (Guide)\n")
        self.assertTrue(any("no definition" in p for p in self.tree.check()))

    # One row per production of CommonMark's inline-link and link-reference-
    # definition grammar: (name, form with {t} for the target, directory-and-
    # file stem of the existing target page). A missing form is a missing row.
    LINK_FORMS = (
        ("inline", "[x]({t})\n", "docs/g.md"),
        ("inline, double-quoted title", '[x]({t} "Title")\n', "docs/g.md"),
        ("inline, single-quoted title", "[x]({t} 'Title')\n", "docs/g.md"),
        ("inline, parenthesized title", "[x]({t} (Title))\n", "docs/g.md"),
        ("inline, title on the next line", '[x]({t}\n  "Title")\n', "docs/g.md"),
        ("inline, angle-bracket destination", "[x](<{t}>)\n", "docs/g.md"),
        ("inline, angle-bracket destination with a space", "[x](<{t}>)\n", "docs/g file.md"),
        ("inline, angle-bracket destination and title", '[x](<{t}> "Title")\n', "docs/g file.md"),
        ("inline, balanced parentheses in the destination", "[x]({t})\n", "docs/a_(b).md"),
        ("inline, bracketed link text", "[a [b] c]({t})\n", "docs/g.md"),
        ("inline, image inside the link text", "[![i](docs/i.png)]({t})\n", "docs/g.md"),
        ("definition", "[g]\n\n[g]: {t}\n", "docs/g.md"),
        ("definition, full reference", "[x][g]\n\n[g]: {t}\n", "docs/g.md"),
        ("definition, double-quoted title", '[g]\n\n[g]: {t} "Title"\n', "docs/g.md"),
        ("definition, single-quoted title", "[g]\n\n[g]: {t} 'Title'\n", "docs/g.md"),
        ("definition, parenthesized title", "[g]\n\n[g]: {t} (Title)\n", "docs/g.md"),
        ("definition, destination on the next line", "[g]\n\n[g]:\n  {t}\n", "docs/g.md"),
        ("definition, angle-bracket destination", "[g]\n\n[g]: <{t}>\n", "docs/g.md"),
        ("definition, angle-bracket destination with a space", "[g]\n\n[g]: <{t}>\n", "docs/g file.md"),
        ("definition, balanced parentheses", "[g]\n\n[g]: {t}\n", "docs/a_(b).md"),
        ("block-quoted definition", "> [g]\n>\n> [g]: {t}\n", "docs/g.md"),
        ("block-quoted definition, next-line destination", "> [g]\n>\n> [g]:\n> {t}\n", "docs/g.md"),
        ("block-quoted definition, next-line angle destination",
         "> [g]\n>\n> [g]:\n> <{t}>\n", "docs/g file.md"),
    )

    def test_every_link_form_is_validated(self) -> None:
        for name, form, page in self.LINK_FORMS:
            with self.subTest(name):
                self.tree.write(page, "# G\n\n## Sub\n")
                self.tree.write("docs/i.png", "")

                def put(target: str) -> list[str]:
                    self.tree.write("README.md", "# R\n\n" + form.format(t=target))
                    return self.tree.check()

                self.assertEqual(put(page), [])
                self.assertEqual(put(page + "#sub"), [])
                self.assertTrue(any("missing file" in p for p in put("docs/missing file.md"
                                                                      if " " in page else "docs/missing.md")))
                self.assertTrue(any("missing heading" in p for p in put(page + "#nope")))
                self.assertTrue(any("missing heading" in p for p in put("#missing")))

    def test_inline_links_with_nested_links_and_malformed_forms(self) -> None:
        links = check_docs.links
        # An outer link may not contain another link; an image may.
        self.assertEqual(links("[a [b](x.md) c](y.md)\n"), ["x.md"])
        self.assertEqual(links("[![i](i.png)](y.md)\n"), ["y.md", "i.png"])
        # Not links: no destination, an unclosed destination, an unclosed title.
        self.assertEqual(links("[x]() [y](a.md \"t) [z](a.md\n"), [])
        self.assertEqual(links("[x](<a.md) [y](<a\nb.md>)\n"), [])

    def test_footnotes_and_prose_subscripts_are_not_links(self) -> None:
        self.tree.write("README.md", "# R\n\nNote[^1] and a[i][j] and [^1][x].\n\n[^1]: Note.\n")
        self.assertEqual(self.tree.check(), [])

    def test_a_blob_link_needs_a_file_path(self) -> None:
        base = "https://github.com/RodrigoFAbreu/workflow"
        self.assertIsNotNone(check_docs.external_link_problem(base + "/blob/main"))
        self.assertIsNotNone(check_docs.external_link_problem(base + "/blob"))
        self.assertIsNone(check_docs.external_link_problem(base + "/blob/main/a.md"))
        self.assertIsNone(check_docs.external_link_problem(base + "/tree/main"))

    def test_external_links(self) -> None:
        good = ["https://github.com/RodrigoFAbreu/workflow-manager#readme",
                "https://github.com/RodrigoFAbreu/workflow",
                "https://github.com/RodrigoFAbreu/workflow-controller/releases",
                "https://github.com/RodrigoFAbreu/workflow-controller/blob/main/README.md",
                "https://github.com/RodrigoFAbreu/workflow-controller/issues/3",
                "https://github.com/RodrigoFAbreu/workflow-controller/pull/24",
                "https://claude.com/claude-code"]
        bad = ["https://github.com/RodrigoFAbreu/SignalHub",
               "https://github.com/Other/workflow",
               "https://github.com/RodrigoFAbreu/workflow-controller/issues/x",
               "https://github.com/RodrigoFAbreu/workflow-controller/wiki",
               "https://example.com/x",
               "https://github.com/RodrigoFAbreu"]
        for url in good:
            self.assertIsNone(check_docs.external_link_problem(url), url)
        for url in bad:
            self.assertIsNotNone(check_docs.external_link_problem(url), url)


class PageRuleTest(TreeTestCase):
    def page(self, rel: str, body: str, header: str | None = HEADER) -> None:
        self.tree.write(rel, "# Title\n\n" + (header + "\n\n" if header else "") + body + "\n")

    def test_a_good_page_passes(self) -> None:
        self.page("docs/glossary.md", "Words.")
        problems = check_docs.check_pages(self.tree.root)
        self.assertFalse([p for p in problems if "glossary" in p])

    def test_missing_header_fails(self) -> None:
        self.page("docs/glossary.md", "Words.", header=None)
        self.assertTrue(any("first line after the title" in p for p in check_docs.check_pages(self.tree.root)))

    def test_header_must_be_first_after_the_title(self) -> None:
        self.tree.write("docs/glossary.md", "# Title\n\nIntro.\n\n" + HEADER + "\n")
        self.assertTrue([p for p in check_docs.check_pages(self.tree.root) if "glossary" in p])

    def test_internal_ids_fail(self) -> None:
        self.page("docs/glossary.md", "See CP3 and LPR-R1-002 and the-real-item.")
        self.tree.write("docs/milestones/completed/the-real-item.md", "# x\n")
        problems = [p for p in check_docs.check_pages(self.tree.root) if "glossary" in p]
        self.assertEqual(len(problems), 3)

    def test_work_item_ids_from_state_are_flagged_as_whole_tokens(self) -> None:
        self.tree.write("docs/ai-workflow/WORKFLOW_STATE.json", json.dumps({"work_items": {"item-one": {}}}))
        self.page("docs/glossary.md", "item-one and item-one-more and `workflow-controller-tests/timings-local.json`.")
        problems = [p for p in check_docs.check_pages(self.tree.root) if "glossary" in p]
        self.assertEqual(len(problems), 1)
        self.assertIn("'item-one'", problems[0])

    def test_link_targets_are_not_scanned(self) -> None:
        self.tree.write("docs/milestones/completed/the-real-item.md", "# x\n")
        self.page("docs/glossary.md", "[plan](milestones/completed/the-real-item.md)")
        self.assertFalse([p for p in check_docs.check_pages(self.tree.root) if "glossary" in p])

    def test_definition_autolink_and_bare_targets_are_not_scanned(self) -> None:
        self.tree.write("docs/milestones/completed/the-real-item.md", "# x\n")
        self.page("docs/glossary.md",
                  "[p][m] <https://github.com/RodrigoFAbreu/workflow/the-real-item> "
                  "and https://github.com/RodrigoFAbreu/workflow/the-real-item.\n\n"
                  "[m]: milestones/completed/the-real-item.md\n> [n]: milestones/completed/the-real-item.md\n")
        self.assertFalse([p for p in check_docs.check_pages(self.tree.root) if "glossary" in p])

class SlashCommandRuleTest(TreeTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tree.write("payload/.claude/commands/milestone-plan.md", "x\n")

    def page(self, body: str) -> list[str]:
        self.tree.write("README.md", "# T\n\n" + HEADER + "\n\n" + body + "\n")
        return check_docs.check_commands(self.tree.root)

    def test_an_existing_command_passes_in_every_place(self) -> None:
        self.assertEqual(self.page("Run `/milestone-plan`, or /milestone-plan x.\n\n```text\n/milestone-plan id\n```"), [])

    def test_an_unknown_command_fails(self) -> None:
        problems = self.page("Run `/milestone-plans` now.")
        self.assertEqual(len(problems), 1)
        self.assertIn("/milestone-plans", problems[0])

    def test_paths_and_urls_are_not_commands(self) -> None:
        self.assertEqual(self.page("See docs/ai-workflow/x.md, `/path/to/repo` and [a](https://github.com/RodrigoFAbreu/workflow/blob/main/a.md)."), [])


if __name__ == "__main__":
    unittest.main()
