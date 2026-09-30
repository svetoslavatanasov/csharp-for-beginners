#!/usr/bin/env python3
"""Генерира HTML версиите на уроците от Markdown.

Пускане от папка csharp-for-beginners:

    python tools/build_html.py

Чете всички lessons/lesson-*.md и записва html/lessons/lesson-*.html.
Поддържа само Markdown елементите, които уроците използват. Ако срещне
непознат елемент, спира с грешка (файл и ред), вместо тихо да развали
страницата. HTML уроците не се редактират на ръка.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAGE_HEAD = """<!doctype html>
<html lang="bg">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>__TITLE__</title>
  <link rel="stylesheet" href="../assets/course.css">
  <script>
    (function () {
      var version = Date.now().toString();

      function versionedUrl(href) {
        try {
          var url = new URL(href, window.location.href);
          if (url.origin !== window.location.origin) {
            return href;
          }
          url.searchParams.set("v", version);
          return url.href;
        } catch (error) {
          return href;
        }
      }

      function applyCacheBusting() {
        document.querySelectorAll("link[rel=\\"stylesheet\\"][href]").forEach(function (link) {
          link.setAttribute("href", versionedUrl(link.getAttribute("href")));
        });

        document.querySelectorAll("a[href]").forEach(function (link) {
          var href = link.getAttribute("href");
          if (/\\.html(?:$|[?#])/.test(href)) {
            link.setAttribute("href", versionedUrl(href));
          }
        });
      }

      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", applyCacheBusting);
      } else {
        applyCacheBusting();
      }
    }());
  </script>
</head>
<body>
  <main class="page">
    <nav class="top-nav" aria-label="Основна навигация">
      <div class="top-nav-title">C# за начинаещи</div>
      <div class="top-nav-links">
        <a href="../index.html">Начало</a>
        <a href="../docs/curriculum.html">Програма</a>
        <a href="../docs/glossary.html">Речник</a>
      </div>
    </nav>

    <article class="lesson">
      <header class="lesson-header">
        <div class="lesson-label">__LABEL__</div>
        <h1>__HEADING__</h1>
      </header>"""

PAGE_FOOT = """
      <footer class="footer-nav">
        Важни страници: <a href="../index.html">Начало</a>, <a href="../docs/curriculum.html">Програма</a>, <a href="../docs/glossary.html">Речник</a>.
      </footer>
    </article>
  </main>
</body>
</html>
"""

TITLE_RE = re.compile(r"^(Урок \d+): (.+)$")
HEADING_RE = re.compile(r"^(#+) (.+)$")
FENCE_RE = re.compile(r"^```(.*)$")
UL_RE = re.compile(r"^- (.*)$")
OL_RE = re.compile(r"^(\d+)\. (.*)$")
TABLE_SEPARATOR_RE = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")

CODE_CLASSES = {"csharp": ' class="language-csharp"', "text": "", "": ""}
SECTION_WRAPPERS = {"Практика": "practice-block", "Упражнения по трудност": "difficulty"}


class BuildError(Exception):
    """Markdown, който скриптът не може да преобразува."""


def render_inline(text: str) -> str:
    """Екранира текста и превръща `код` и **удебелено** в HTML."""
    parts = text.split("`")
    if len(parts) % 2 == 0:
        raise ValueError("незатворен ` в текста")
    out = []
    for index, part in enumerate(parts):
        escaped = html.escape(part, quote=False)
        if index % 2 == 1:
            out.append("<code>" + escaped + "</code>")
        else:
            out.append(BOLD_RE.sub(r"<strong>\1</strong>", escaped))
    return "".join(out)


def _starts_block(line: str) -> bool:
    return bool(
        FENCE_RE.match(line)
        or line.startswith(("#", ">", "|"))
        or UL_RE.match(line)
        or OL_RE.match(line)
    )


def _split_row(row: str) -> list[str]:
    inner = row.strip()[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [cell.strip().replace("\\|", "|") for cell in CELL_SPLIT_RE.split(inner)]


def parse_blocks(md_text: str, source: str) -> list[dict]:
    """Разделя Markdown на блокове. Всеки блок пази номера на реда си."""
    lines = [line.rstrip("\r") for line in md_text.split("\n")]
    blocks: list[dict] = []
    i = 0

    def fail(line_no: int, message: str) -> None:
        raise BuildError(f"{source}:{line_no}: {message}")

    def check_indent(index: int) -> None:
        if lines[index][:1] in (" ", "\t"):
            fail(index + 1, "ред с отстъп извън код блок (вложени списъци не се поддържат)")

    while i < len(lines):
        line = lines[i]
        line_no = i + 1
        if not line.strip():
            i += 1
            continue
        check_indent(i)

        fence = FENCE_RE.match(line)
        if fence:
            lang = fence.group(1).strip()
            if lang not in CODE_CLASSES:
                fail(line_no, f"непознат език на код блок: {lang!r}")
            body = []
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                body.append(lines[i])
                i += 1
            if i == len(lines):
                fail(line_no, "незатворен код блок")
            i += 1
            blocks.append({"type": "code", "lang": lang, "lines": body, "line": line_no})
            continue

        if line.startswith("#"):
            heading = HEADING_RE.match(line)
            if not heading:
                fail(line_no, "след # трябва да има интервал")
            level = len(heading.group(1))
            if level > 3:
                fail(line_no, "заглавия с #### и повече не се поддържат")
            blocks.append({"type": f"h{level}", "text": heading.group(2).strip(), "line": line_no})
            i += 1
            continue

        if line.startswith(">"):
            parts = []
            while i < len(lines) and lines[i].startswith(">"):
                parts.append(lines[i][1:].strip())
                i += 1
            text = " ".join(part for part in parts if part)
            blocks.append({"type": "quote", "text": text, "line": line_no})
            continue

        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            if len(rows) < 2 or not TABLE_SEPARATOR_RE.match(rows[1]):
                fail(line_no, "таблицата трябва да има ред със заглавия и ред |---|")
            header = _split_row(rows[0])
            body_rows = [_split_row(row) for row in rows[2:]]
            for offset, row in enumerate(body_rows):
                if len(row) != len(header):
                    fail(line_no + 2 + offset, "редът на таблицата има различен брой колони")
            blocks.append({"type": "table", "header": header, "rows": body_rows, "line": line_no})
            continue

        first_ul = UL_RE.match(line)
        first_ol = OL_RE.match(line)
        if first_ul or first_ol:
            item_re = UL_RE if first_ul else OL_RE
            items: list[dict] = []
            while i < len(lines):
                current = lines[i]
                item = item_re.match(current)
                if item:
                    items.append({"text": item.group(item.lastindex), "line": i + 1})
                    i += 1
                    continue
                if not current.strip():
                    next_index = i
                    while next_index < len(lines) and not lines[next_index].strip():
                        next_index += 1
                    if next_index < len(lines) and item_re.match(lines[next_index]):
                        i = next_index
                        continue
                    break
                if _starts_block(current):
                    break
                check_indent(i)
                items[-1]["text"] += " " + current.strip()
                i += 1
            block = {"type": "ul" if first_ul else "ol", "items": items, "line": line_no}
            block["start"] = int(first_ol.group(1)) if first_ol else 1
            blocks.append(block)
            continue

        parts = []
        while i < len(lines) and lines[i].strip():
            if parts and _starts_block(lines[i]):
                break
            check_indent(i)
            parts.append(lines[i].strip())
            i += 1
        blocks.append({"type": "p", "text": " ".join(parts), "line": line_no})

    return blocks


def _inline(block_text: str, source: str, line_no: int) -> str:
    try:
        return render_inline(block_text)
    except ValueError as error:
        raise BuildError(f"{source}:{line_no}: {error}") from None


def _render_block(block: dict, pad: str, source: str) -> list[str]:
    kind = block["type"]
    line_no = block["line"]
    if kind == "p":
        return [f"{pad}<p>{_inline(block['text'], source, line_no)}</p>"]
    if kind == "quote":
        return [f"{pad}<blockquote>{_inline(block['text'], source, line_no)}</blockquote>"]
    if kind == "code":
        code = "\n".join(html.escape(line, quote=False) for line in block["lines"])
        return [f"{pad}<pre><code{CODE_CLASSES[block['lang']]}>{code}</code></pre>"]
    if kind in ("ul", "ol"):
        opening = f"<{kind}>"
        if kind == "ol" and block["start"] != 1:
            opening = f'<ol start="{block["start"]}">'
        out = [pad + opening]
        for item in block["items"]:
            out.append(f"{pad}  <li>{_inline(item['text'], source, item['line'])}</li>")
        out.append(f"{pad}</{kind}>")
        return out
    if kind == "table":
        out = [f"{pad}<table>", f"{pad}  <thead>"]
        cells = "".join(f"<th>{_inline(cell, source, line_no)}</th>" for cell in block["header"])
        out += [f"{pad}    <tr>{cells}</tr>", f"{pad}  </thead>", f"{pad}  <tbody>"]
        for row in block["rows"]:
            cells = "".join(f"<td>{_inline(cell, source, line_no)}</td>" for cell in row)
            out.append(f"{pad}    <tr>{cells}</tr>")
        out += [f"{pad}  </tbody>", f"{pad}</table>"]
        return out
    raise BuildError(f"{source}:{line_no}: неочакван блок {kind}")


def render_lesson(md_text: str, source: str) -> str:
    """Превръща един Markdown урок в цяла HTML страница."""
    blocks = parse_blocks(md_text, source)
    if not blocks or blocks[0]["type"] != "h1":
        raise BuildError(f"{source}:1: урокът трябва да започва с '# Урок N: Заглавие'")
    title = TITLE_RE.match(blocks[0]["text"])
    if not title:
        raise BuildError(f"{source}:{blocks[0]['line']}: заглавието трябва да е '# Урок N: Заглавие'")
    rest = blocks[1:]
    if rest and rest[0]["type"] != "h2":
        raise BuildError(f"{source}:{rest[0]['line']}: текст преди първото ## заглавие")

    page_title = html.escape(blocks[0]["text"].replace("`", ""), quote=False)
    heading = _inline(title.group(2), source, blocks[0]["line"])
    out = [
        PAGE_HEAD.replace("__TITLE__", page_title)
        .replace("__LABEL__", title.group(1))
        .replace("__HEADING__", heading)
    ]

    wrapper = None
    wrapper_open = False
    section_open = False
    for block in rest:
        kind = block["type"]
        if kind == "h1":
            raise BuildError(f"{source}:{block['line']}: второ # заглавие")
        if kind == "h2":
            if wrapper_open:
                out.append("        </div>")
                wrapper_open = False
            if section_open:
                out.append("      </section>")
            out += ["", "      <section>"]
            out.append(f"        <h2>{_inline(block['text'], source, block['line'])}</h2>")
            section_open = True
            wrapper = SECTION_WRAPPERS.get(block["text"])
            continue
        if kind == "h3":
            if wrapper_open:
                out.append("        </div>")
            if not out[-1].lstrip().startswith("<h2>"):
                out.append("")
            h3 = f"<h3>{_inline(block['text'], source, block['line'])}</h3>"
            if wrapper:
                out.append(f'        <div class="{wrapper}">')
                out.append("          " + h3)
                wrapper_open = True
            else:
                out.append("        " + h3)
            continue
        pad = "          " if wrapper_open else "        "
        out += _render_block(block, pad, source)

    if wrapper_open:
        out.append("        </div>")
    if section_open:
        out.append("      </section>")
    return "\n".join(out) + "\n" + PAGE_FOOT


def build_all(root: Path = ROOT) -> list[Path]:
    """Генерира HTML за всички уроци и връща пътищата на записаните файлове."""
    written = []
    for md_path in sorted((root / "lessons").glob("lesson-*.md")):
        page = render_lesson(md_path.read_text(encoding="utf-8"), md_path.name)
        out_path = root / "html" / "lessons" / (md_path.stem + ".html")
        out_path.write_text(page, encoding="utf-8", newline="\n")
        written.append(out_path)
    return written


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        written = build_all()
    except BuildError as error:
        print(f"Грешка: {error}", file=sys.stderr)
        return 1
    for path in written:
        print("записан " + path.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
