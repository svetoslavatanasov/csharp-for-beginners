"""Тестове за правилата на build_html.py.

Пускане от папка csharp-for-beginners:

    python -m unittest discover -s tools -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import build_html  # noqa: E402


def lesson(body: str, title: str = "# Урок 7: Тест") -> str:
    return build_html.render_lesson(f"{title}\n\n{body}", "test.md")


def article(page: str) -> str:
    return page.split('<article class="lesson">', 1)[1].split("</article>", 1)[0]


class InlineTests(unittest.TestCase):
    def test_escapes_special_characters_everywhere(self):
        self.assertEqual(
            build_html.render_inline("Ако `a < b && c` е true, x > y & z"),
            "Ако <code>a &lt; b &amp;&amp; c</code> е true, x &gt; y &amp; z",
        )

    def test_bold(self):
        self.assertEqual(build_html.render_inline("Натисни **Run**."), "Натисни <strong>Run</strong>.")

    def test_bold_is_not_applied_inside_code(self):
        self.assertEqual(build_html.render_inline("`**x**`"), "<code>**x**</code>")

    def test_quotes_are_left_as_they_are(self):
        self.assertEqual(build_html.render_inline('Byte: "Здравей!"'), 'Byte: "Здравей!"')


class PageTests(unittest.TestCase):
    def test_title_label_and_heading(self):
        page = lesson("## Какво ще научиш\n\nТекст.\n", title="# Урок 6: `if`, `else` и решения")
        self.assertIn("<title>Урок 6: if, else и решения</title>", page)
        self.assertIn('<div class="lesson-label">Урок 6</div>', page)
        self.assertIn("<h1><code>if</code>, <code>else</code> и решения</h1>", page)

    def test_page_keeps_shared_head_navigation_and_footer(self):
        page = lesson("## А\n\nТекст.\n")
        self.assertTrue(page.startswith('<!doctype html>\n<html lang="bg">\n'))
        self.assertIn('<link rel="stylesheet" href="../assets/course.css">', page)
        self.assertIn('document.querySelectorAll("link[rel=\\"stylesheet\\"][href]")', page)
        self.assertIn("if (/\\.html(?:$|[?#])/.test(href)) {", page)
        self.assertIn('<a href="../docs/glossary.html">Речник</a>', page)
        self.assertIn('<footer class="footer-nav">', page)
        self.assertTrue(page.endswith("</html>\n"))

    def test_each_h2_is_a_section(self):
        page = lesson("## Първа\n\nЕдно.\n\n## Втора\n\nДве.\n")
        self.assertIn("      <section>\n        <h2>Първа</h2>\n        <p>Едно.</p>\n      </section>", page)
        self.assertIn("      <section>\n        <h2>Втора</h2>\n        <p>Две.</p>\n      </section>", page)

    def test_wrapped_paragraph_lines_are_joined(self):
        page = lesson("## А\n\nПърви ред\nвтори ред.\n")
        self.assertIn("<p>Първи ред втори ред.</p>", page)

    def test_code_blocks_are_escaped_and_classed(self):
        page = lesson("## А\n\n```csharp\nif (a < b && c)\n{\n}\n```\n\n```text\n[ x ] -> [ y ]\n```\n")
        self.assertIn('<pre><code class="language-csharp">if (a &lt; b &amp;&amp; c)\n{\n}</code></pre>', page)
        self.assertIn("<pre><code>[ x ] -&gt; [ y ]</code></pre>", page)

    def test_lists(self):
        page = lesson("## А\n\n- едно;\n- две.\n\n1. първо\n2. второ\n")
        self.assertIn("<ul>\n          <li>едно;</li>\n          <li>две.</li>\n        </ul>", page)
        self.assertIn("<ol>\n          <li>първо</li>\n          <li>второ</li>\n        </ol>", page)

    def test_ordered_list_keeps_start_number_and_merges_items_split_by_blank_lines(self):
        page = lesson("## А\n\n```text\nx\n```\n\n2. второ\n\n3. трето\n")
        self.assertIn('<ol start="2">\n          <li>второ</li>\n          <li>трето</li>\n        </ol>', page)

    def test_blockquote(self):
        page = lesson('## А\n\n> Byte: "Готово."\n')
        self.assertIn('<blockquote>Byte: "Готово."</blockquote>', page)

    def test_table_with_escaped_pipe(self):
        page = lesson("## А\n\n| Оператор | Значение |\n|---|---|\n| `\\|\\|` | или |\n")
        self.assertIn("<thead>\n            <tr><th>Оператор</th><th>Значение</th></tr>", page)
        self.assertIn("<tr><td><code>||</code></td><td>или</td></tr>", page)

    def test_practice_and_difficulty_subsections_are_wrapped(self):
        page = lesson(
            "## Практика\n\nУвод.\n\n### Намери бъга\n\nТекст.\n\n### Поправи кода\n\nОще.\n\n"
            "## Упражнения по трудност\n\n### ⭐ Easy\n\n1. Задача.\n"
        )
        self.assertIn("<h2>Практика</h2>\n        <p>Увод.</p>", page)
        self.assertIn('<div class="practice-block">\n          <h3>Намери бъга</h3>\n          <p>Текст.</p>\n        </div>', page)
        self.assertIn('<div class="practice-block">\n          <h3>Поправи кода</h3>', page)
        self.assertIn('<div class="difficulty">\n          <h3>⭐ Easy</h3>\n          <ol>', page)

    def test_other_h3_are_plain(self):
        page = lesson("## Чести грешки\n\n### Грешка 1: Нещо\n\nТекст.\n")
        self.assertIn("        <h3>Грешка 1: Нещо</h3>", page)
        self.assertNotIn("practice-block", page)
        self.assertNotIn('class="difficulty"', page)


class ErrorTests(unittest.TestCase):
    def assertBuildError(self, md_text: str, expected: str) -> None:
        with self.assertRaises(build_html.BuildError) as caught:
            build_html.render_lesson(md_text, "x.md")
        self.assertIn(expected, str(caught.exception))

    def test_missing_title(self):
        self.assertBuildError("## Само секция\n", "x.md:1:")

    def test_title_without_lesson_number(self):
        self.assertBuildError("# Заглавие\n\n## А\n", "x.md:1:")

    def test_text_before_first_section(self):
        self.assertBuildError("# Урок 1: А\n\nТекст.\n\n## Б\n", "x.md:3:")

    def test_h4_is_not_supported(self):
        self.assertBuildError("# Урок 1: А\n\n## Б\n\n#### В\n", "x.md:5:")

    def test_unclosed_code_block(self):
        self.assertBuildError("# Урок 1: А\n\n## Б\n\n```csharp\nint x = 1;\n", "x.md:5:")

    def test_unknown_code_language(self):
        self.assertBuildError("# Урок 1: А\n\n## Б\n\n```python\nx = 1\n```\n", "x.md:5:")

    def test_nested_list(self):
        self.assertBuildError("# Урок 1: А\n\n## Б\n\n- едно\n  - вложено\n", "x.md:6:")

    def test_unclosed_backtick(self):
        self.assertBuildError("# Урок 1: А\n\n## Б\n\nТекст с ` без край.\n", "x.md:5:")


if __name__ == "__main__":
    unittest.main()
