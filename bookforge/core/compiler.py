#!/usr/bin/env python3
"""BookForge Compilation Core Module.

Compiles draft md files into a single manuscript.
"""

from __future__ import annotations

import re
import zipfile
from xml.sax.saxutils import escape
from pathlib import Path

DEFAULT_OUTPUT_NAME = "compiled-manuscript.md"
DEFAULT_FORMATTED_OUTPUT_NAME = "formatted-manuscript.docx"


def chapter_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"chapter-(\d+)", str(path))
    if match:
        return int(match.group(1)), path.name
    return 999, path.name


def read_title(book_folder: Path) -> str | None:
    from bookforge.core.scanner import source_path
    phase_path = source_path(book_folder)
    if not phase_path:
        return None

    for line in phase_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line.strip()
    return None


def default_output_path(book_folder: Path, formatted_doc: bool = False) -> Path:
    if formatted_doc:
        return book_folder / "docs" / DEFAULT_FORMATTED_OUTPUT_NAME
    return book_folder / DEFAULT_OUTPUT_NAME


def discover_drafts(book_folder: Path) -> list[Path]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        raise RuntimeError("Missing chapters folder.")

    draft_paths = sorted(
        chapters_root.glob("chapter-*/chapter-*.md"),
        key=chapter_sort_key,
    )

    epilogue_path = chapters_root / "epilogue" / "epilogue.md"
    if epilogue_path.exists():
        draft_paths.append(epilogue_path)

    if not draft_paths:
        raise RuntimeError("No chapter draft files found.")

    missing_or_empty = [
        str(path)
        for path in draft_paths
        if not path.exists() or not path.read_text(encoding="utf-8").strip()
    ]
    if missing_or_empty:
        raise RuntimeError("Missing or empty draft files: " + ", ".join(missing_or_empty))

    return draft_paths


def clean_manuscript_text(text: str) -> str:
    # Post-process for final book layout (draft-only rendering)
    text = re.sub(r"(?m)^## Beat.*$\n*", "", text)
    text = re.sub(r"(?m)^##+\s+Scene\s+\d+(?:\s*:.*)?$\n*", "", text)
    text = re.sub(r'([\"”])\s*—\s*', r'\1 ', text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def chapter_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def markdown_anchor(title: str) -> str:
    anchor = re.sub(r"[^\w\s-]", "", title.lower())
    anchor = re.sub(r"\s+", "-", anchor.strip())
    return anchor


def compile_manuscript(book_folder: Path, output_path: Path, include_title: bool) -> tuple[int, int]:
    draft_paths = discover_drafts(book_folder)
    parts: list[str] = []

    if include_title:
        title = read_title(book_folder)
        if title:
            parts.append(title)

    for path in draft_paths:
        text = path.read_text(encoding="utf-8").strip()
        parts.append(text)

    manuscript = "\n\n---\n\n".join(parts).rstrip() + "\n"

    manuscript = clean_manuscript_text(manuscript) + "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manuscript, encoding="utf-8")

    return len(draft_paths), len(manuscript.split())


def format_manuscript_document(book_folder: Path, output_path: Path, include_title: bool) -> tuple[int, int]:
    draft_paths = discover_drafts(book_folder)
    chapters: list[tuple[str, str]] = []

    for path in draft_paths:
        raw_text = path.read_text(encoding="utf-8")
        cleaned = clean_manuscript_text(raw_text)
        fallback = "Epilogue" if path.name == "epilogue.md" else path.stem.replace("-", " ").title()
        chapters.append((chapter_title(cleaned, fallback), cleaned))

    manuscript_words = sum(len(text.split()) for _, text in chapters)
    book_title = read_title(book_folder) if include_title else None
    display_title = book_title[2:].strip() if book_title and book_title.startswith("# ") else "Untitled Manuscript"

    parts: list[str] = [
        f"# {display_title}",
        "**Formatted Manuscript**\n\n"
        f"**Book Folder:** `{book_folder}`\n\n"
        f"**Draft Files:** {len(chapters)}\n\n"
        f"**Manuscript Words:** {manuscript_words}",
        '<div style="page-break-after: always;"></div>',
        "## Contents\n\n"
        + "\n".join(f"- [{title}](#{markdown_anchor(title)})" for title, _ in chapters),
    ]

    for title, text in chapters:
        parts.append('<div style="page-break-after: always;"></div>')
        if text.lstrip().startswith("# "):
            parts.append(text)
        else:
            parts.append(f"# {title}\n\n{text}")

    document = "\n\n".join(parts).rstrip() + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")

    return len(draft_paths), manuscript_words


def docx_paragraph(text: str = "", style: str | None = None, page_break: bool = False) -> str:
    if page_break:
        return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

    properties = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    runs = "".join(docx_runs(text))
    return f"<w:p>{properties}{runs}</w:p>"


def docx_runs(text: str) -> list[str]:
    if not text:
        return ['<w:r><w:t></w:t></w:r>']

    runs: list[str] = []
    position = 0
    italic_re = re.compile(r"\*([^*\n]+)\*")

    for match in italic_re.finditer(text):
        if match.start() > position:
            runs.append(docx_run(text[position:match.start()]))
        runs.append(docx_run(match.group(1), italic=True))
        position = match.end()

    if position < len(text):
        runs.append(docx_run(text[position:]))

    return runs


def docx_run(text: str, italic: bool = False) -> str:
    run_properties = "<w:rPr><w:i/></w:rPr>" if italic else ""
    escaped = escape(text)
    space = ' xml:space="preserve"' if text[:1].isspace() or text[-1:].isspace() else ""
    return f"<w:r>{run_properties}<w:t{space}>{escaped}</w:t></w:r>"


def docx_body_from_markdown(markdown: str) -> str:
    blocks: list[str] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            blocks.append(docx_paragraph(" ".join(line.strip() for line in paragraph_lines)))
            paragraph_lines.clear()

    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            blocks.append(docx_paragraph(stripped[2:].strip(), "ChapterTitle"))
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            blocks.append(docx_paragraph(stripped[3:].strip(), "Heading2"))
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            blocks.append(docx_paragraph(stripped[2:].strip(), "ListParagraph"))
            continue
        paragraph_lines.append(stripped)

    flush_paragraph()
    return "\n".join(blocks)


def format_manuscript_docx(book_folder: Path, output_path: Path, include_title: bool) -> tuple[int, int]:
    draft_paths = discover_drafts(book_folder)
    chapters: list[tuple[str, str]] = []

    for path in draft_paths:
        raw_text = path.read_text(encoding="utf-8")
        cleaned = clean_manuscript_text(raw_text)
        fallback = "Epilogue" if path.name == "epilogue.md" else path.stem.replace("-", " ").title()
        chapters.append((chapter_title(cleaned, fallback), cleaned))

    manuscript_words = sum(len(text.split()) for _, text in chapters)
    book_title = read_title(book_folder) if include_title else None
    display_title = book_title[2:].strip() if book_title and book_title.startswith("# ") else "Untitled Manuscript"

    body_parts: list[str] = [
        docx_paragraph(display_title, "Title"),
        docx_paragraph(page_break=True),
        docx_paragraph("Contents", "Heading1"),
    ]

    for title, _ in chapters:
        body_parts.append(docx_paragraph(title))

    for _, text in chapters:
        body_parts.append(docx_paragraph(page_break=True))
        body_parts.append(docx_body_from_markdown(text))

    document_xml = DOCX_DOCUMENT_TEMPLATE.format(body="\n".join(body_parts))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
        archive.writestr("_rels/.rels", DOCX_ROOT_RELS)
        archive.writestr("word/_rels/document.xml.rels", DOCX_DOCUMENT_RELS)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", DOCX_STYLES)

    return len(draft_paths), manuscript_words


DOCX_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""


DOCX_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""


DOCX_DOCUMENT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""


DOCX_DOCUMENT_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
{body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
      <w:cols w:space="720"/>
      <w:docGrid w:linePitch="360"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


DOCX_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="160" w:line="360" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="240"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:jc w:val="center"/><w:spacing w:after="360"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="240" w:after="180"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:spacing w:before="200" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ChapterTitle">
    <w:name w:val="Chapter Title"/>
    <w:basedOn w:val="Heading1"/>
    <w:next w:val="Normal"/>
    <w:pPr><w:keepNext/><w:jc w:val="center"/><w:spacing w:before="240" w:after="300"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph">
    <w:name w:val="List Paragraph"/>
    <w:basedOn w:val="Normal"/>
    <w:pPr><w:ind w:left="720"/></w:pPr>
  </w:style>
</w:styles>
"""


def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Compile chapter drafts and epilogue into a manuscript file."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/book-example",
        help="Book folder containing phase-0.md and chapters/.",
    )
    parser.add_argument(
        "--output",
        help="Output path. Defaults to compiled Markdown, or docs/formatted-manuscript.docx with --formatted-doc.",
    )
    parser.add_argument(
        "--no-title",
        action="store_true",
        help="Do not prepend the book title from phase-0.md.",
    )
    parser.add_argument(
        "--formatted-doc",
        action="store_true",
        help="Generate a formatted Word .docx manuscript with title page and contents.",
    )
    args = parser.parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    output_path = Path(args.output) if args.output else default_output_path(book_folder, args.formatted_doc)

    try:
        if args.formatted_doc:
            draft_count, word_count = format_manuscript_docx(
                book_folder=book_folder,
                output_path=output_path,
                include_title=not args.no_title,
            )
        else:
            draft_count, word_count = compile_manuscript(
                book_folder=book_folder,
                output_path=output_path,
                include_title=not args.no_title,
            )
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print("# Manuscript Compile Report")
    print("")
    print(f"- **Book Folder:** `{book_folder}`")
    print(f"- **Output:** `{output_path}`")
    print(f"- **Format:** {'docx' if args.formatted_doc else 'compiled'}")
    print(f"- **Draft Files Compiled:** {draft_count}")
    print(f"- **Compiled Words:** {word_count}")
    return 0
