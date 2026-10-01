"""Проверки на истинските уроци и HTML страници.

Пускане от папка csharp-for-beginners:

    python -m unittest discover -s tools -v

Проверява, че HTML уроците са генерирани от текущия Markdown, съдържат целия
му текст, имат балансирани тагове и работещи линкове, че всеки урок има линк
от началната страница и програмата, и че речникът в Markdown и HTML съвпада.
"""

from __future__ import annotations

import html
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import build_html  # noqa: E402

ROOT = TOOLS.parent
VOID_TAGS = {"meta", "link", "br", "img", "hr", "input"}
SEPARATOR_RE = re.compile(r"^\|(\s*:?-+:?\s*\|)+$")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")


def lesson_paths() -> list[Path]:
    return sorted((ROOT / "lessons").glob("lesson-*.md"))


def visible_text(page: str) -> str:
    """Текстът в <article>, както го вижда читателят."""
    body = page.split('<article class="lesson">', 1)[1].split("</article>", 1)[0]
    body = re.sub(r"</?(code|strong)>", "", body)
    body = re.sub(r"<[^>]+>", " ", body)
    return " ".join(html.unescape(body).split())


def table_cells(line: str) -> list[str]:
    return [cell.strip().replace("\\|", "|") for cell in CELL_SPLIT_RE.split(line.strip().strip("|"))]


def markdown_lines(md_text: str) -> list[str]:
    """Редовете на Markdown урока без Markdown знаците, така както трябва да се виждат в HTML.

    Редовете в код блоковете остават както са (само интервалите се свиват): там `#` и `**` са част от кода.
    """
    result = []
    in_code = False
    for raw in md_text.split("\n"):
        line = raw.strip()
        if in_code:
            if line == "```":
                in_code = False
            else:
                result.append(" ".join(line.split()))
            continue
        if line.startswith("```"):
            in_code = True
            continue
        if not line or SEPARATOR_RE.match(line):
            continue
        if line.startswith("# "):
            label, _, heading = line[2:].partition(": ")
            result += [label, heading.replace("`", "")]
            continue
        if line.startswith("|"):
            result += [cell.replace("`", "") for cell in table_cells(line) if cell]
            continue
        line = re.sub(r"^(#{2,3} |> ?|- |\d+\. )", "", line)
        result.append(" ".join(line.replace("`", "").replace("**", "").split()))
    return [line for line in result if line]


class TagBalanceChecker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.problems: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.stack[-1] != tag:
            self.problems.append(f"</{tag}> на ред {self.getpos()[0]}, отворен е {self.stack[-1:]}")
        else:
            self.stack.pop()


class SiteTests(unittest.TestCase):
    def test_there_are_lessons(self):
        self.assertTrue(lesson_paths(), "няма уроци в lessons/")

    def test_generated_html_is_up_to_date(self):
        for md_path in lesson_paths():
            html_path = ROOT / "html" / "lessons" / (md_path.stem + ".html")
            with self.subTest(lesson=md_path.name):
                self.assertTrue(html_path.exists(), f"липсва {html_path.name}")
                expected = build_html.render_lesson(md_path.read_text(encoding="utf-8"), md_path.name)
                self.assertEqual(html_path.read_text(encoding="utf-8"), expected,
                                 "HTML не е генериран от текущия Markdown; пусни python tools/build_html.py")

    def test_html_contains_all_markdown_text(self):
        for md_path in lesson_paths():
            md_text = md_path.read_text(encoding="utf-8")
            text = visible_text(build_html.render_lesson(md_text, md_path.name))
            missing = [line for line in markdown_lines(md_text) if line not in text]
            with self.subTest(lesson=md_path.name):
                self.assertEqual(missing, [])

    def test_all_html_pages_have_balanced_tags(self):
        for page_path in sorted((ROOT / "html").rglob("*.html")):
            checker = TagBalanceChecker()
            checker.feed(page_path.read_text(encoding="utf-8"))
            checker.close()
            with self.subTest(page=page_path.relative_to(ROOT).as_posix()):
                self.assertEqual(checker.problems, [])
                self.assertEqual(checker.stack, [])

    def test_all_relative_links_point_to_existing_files(self):
        for page_path in sorted((ROOT / "html").rglob("*.html")):
            page = page_path.read_text(encoding="utf-8")
            for href in re.findall(r'href="([^"]+)"', page):
                if re.match(r"^(https?:|mailto:|#)", href):
                    continue
                target = (page_path.parent / href.split("#")[0].split("?")[0]).resolve()
                with self.subTest(page=page_path.name, href=href):
                    self.assertTrue(target.exists(), f"{href} не съществува")

    def test_every_lesson_is_linked_from_index_and_curriculum(self):
        index = (ROOT / "html" / "index.html").read_text(encoding="utf-8")
        curriculum = (ROOT / "html" / "docs" / "curriculum.html").read_text(encoding="utf-8")
        for md_path in lesson_paths():
            name = md_path.stem + ".html"
            with self.subTest(lesson=name):
                self.assertIn(f'href="lessons/{name}"', index)
                self.assertIn(f'href="../lessons/{name}"', curriculum)

    def test_glossary_markdown_matches_html(self):
        md_rows = []
        for line in (ROOT / "docs" / "glossary.md").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("|") and not SEPARATOR_RE.match(line):
                md_rows.append(table_cells(line))
        page = (ROOT / "html" / "docs" / "glossary.html").read_text(encoding="utf-8")
        html_rows = []
        for row in re.findall(r"<tr>(.*?)</tr>", page, re.S):
            cells = re.findall(r"<t[hd]>(.*?)</t[hd]>", row, re.S)
            html_rows.append([html.unescape(re.sub(r"</?code>", "`", cell)).strip() for cell in cells])
        self.assertEqual(md_rows, html_rows)


class MarkdownLinesTests(unittest.TestCase):
    def test_markdown_inside_code_blocks_is_left_as_it_is(self):
        md_text = (
            "# Урок 1: Тест\n\n## Код\n\n"
            '```csharp\nConsole.Write("**");\n```\n\n'
            "```text\n#  #\n```\n"
        )
        lines = markdown_lines(md_text)
        self.assertEqual(lines, ["Урок 1", "Тест", "Код", 'Console.Write("**");', "# #"])
        text = visible_text(build_html.render_lesson(md_text, "test.md"))
        self.assertEqual([line for line in lines if line not in text], [])


if __name__ == "__main__":
    unittest.main()
