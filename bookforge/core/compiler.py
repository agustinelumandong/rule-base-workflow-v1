#!/usr/bin/env python3
"""BookForge Compilation Core Module.

Compiles draft md files into a single manuscript.
"""

from __future__ import annotations

import re
from pathlib import Path

DEFAULT_OUTPUT_NAME = "compiled-manuscript.md"


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


<<<<<<< Updated upstream
=======
def read_book_metadata(book_folder: Path) -> tuple[str | None, str | None, str | None]:
    """Return series title, book title, and display book number from phase-0.md."""
    from bookforge.core.scanner import source_path

    phase_path = source_path(book_folder)
    if not phase_path:
        return None, None, None

    text = phase_path.read_text(encoding="utf-8")
    heading = next(
        (line[2:].strip() for line in text.splitlines() if line.startswith("# ")),
        None,
    )
    series_from_heading: str | None = None
    book_title = heading
    if heading and ":" in heading:
        series_from_heading, book_title = (part.strip() for part in heading.split(":", 1))
    match = re.search(r"(?im)^book\s+(\d+)\s+of\s+(.+?)\s*$", text)
    if not match:
        return series_from_heading, book_title, None
    series_title = series_from_heading or match.group(2).strip()
    if series_title.lower().endswith(" series"):
        series_title = series_title[:-7].rstrip()
    return series_title, book_title, f"Book {int(match.group(1))}"


def chapter_titles(book_folder: Path) -> dict[int, str]:
    """Read source-approved chapter titles from chapter-summaries.md."""
    summaries_path = book_folder / "chapter-summaries.md"
    if not summaries_path.exists():
        return {}

    titles: dict[int, str] = {}
    pattern = re.compile(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:ch-|chapter\s+)(\d{1,3})\s*(?::|—|–)\s*(.+?)(?:\*\*)?\s*$"
    )
    for match in pattern.finditer(summaries_path.read_text(encoding="utf-8")):
        titles[int(match.group(1))] = match.group(2).strip().rstrip("*").strip()
    return titles


>>>>>>> Stashed changes
def discover_drafts(book_folder: Path) -> list[Path]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        raise RuntimeError("Missing chapters folder.")

    draft_paths = sorted(
        (
            path
            for path in chapters_root.glob("chapter-*/chapter-*.md")
            if re.fullmatch(r"chapter-\d+\.md", path.name)
        ),
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

    # Post-process for final book layout (draft-only rendering)
    # 1. Remove all Beat subheaders (e.g., "## Beat 1: ...")
    manuscript = re.sub(r"(?m)^## Beat.*$\n*", "", manuscript)

    # 2. Clean up dialogue em-dash spacing: replace '" — ' or '” — ' with '" ' or '” '
    manuscript = re.sub(r'([\"”])\s*—\s*', r'\1 ', manuscript)

    # 3. Collapse multiple consecutive blank lines to at most one blank line
    manuscript = re.sub(r"\n{3,}", "\n\n", manuscript)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manuscript, encoding="utf-8")

    return len(draft_paths), len(manuscript.split())


<<<<<<< Updated upstream
=======
def compile_docx(book_folder: Path, output_path: Path, include_title: bool) -> tuple[int, int]:
    """Compile chapter drafts into a manuscript-formatted DOCX file."""
    draft_paths = discover_drafts(book_folder)
    document = Document()
    normal_style = document.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(12)
    normal_style.paragraph_format.line_spacing = 1
    normal_style.paragraph_format.first_line_indent = Inches(0)

    rendered_text: list[str] = []
    if include_title:
        series_title, book_title, book_number = read_book_metadata(book_folder)
        for text, size in ((series_title, 18), (book_title, 24), (book_number, 14)):
            if not text:
                continue
            title_paragraph = document.add_paragraph()
            title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = title_paragraph.add_run(text)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(size)
            rendered_text.append(text)
        document.add_page_break()

    titles = chapter_titles(book_folder)
    for index, path in enumerate(draft_paths):
        if index > 0:
            document.add_page_break()

        chapter_match = re.search(r"chapter-(\d+)", path.name)
        chapter_number = int(chapter_match.group(1)) if chapter_match else None
        heading_text = (
            f"Chapter {chapter_number}: {titles[chapter_number]}"
            if chapter_number in titles
            else f"Chapter {chapter_number}" if chapter_number else None
        )
        if heading_text:
            heading = document.add_paragraph()
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = heading.add_run(heading_text)
            run.bold = True
            run.font.name = "Times New Roman"
            run.font.size = Pt(16)
            rendered_text.append(heading_text)

        source_heading_consumed = False
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped_line = line.strip()
            if not stripped_line or stripped_line == "---":
                continue

            if not source_heading_consumed and (
                line.startswith("# ")
                or re.fullmatch(r"Chapter\s+\d+(?::\s*.+)?", stripped_line)
            ):
                source_heading_consumed = True
                continue

            body = document.add_paragraph(line)
            body.paragraph_format.line_spacing = 1
            body.paragraph_format.first_line_indent = Inches(0)
            rendered_text.append(stripped_line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path)
    return len(draft_paths), len(" ".join(rendered_text).split())


def validate_output_extension(output_path: Path, output_format: str) -> None:
    expected_suffix = {"markdown": ".md", "docx": ".docx"}[output_format]
    if output_path.suffix != expected_suffix:
        raise RuntimeError(
            f"Output path must use the {expected_suffix} extension for {output_format} format."
        )


>>>>>>> Stashed changes
def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Compile chapter drafts and epilogue into one Markdown manuscript."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/tex-cade",
        help="Book folder containing phase-0.md and chapters/.",
    )
    parser.add_argument(
        "--output",
        help=f"Output Markdown path. Defaults to <book_folder>/{DEFAULT_OUTPUT_NAME}.",
    )
    parser.add_argument(
        "--no-title",
        action="store_true",
        help="Do not prepend the book title from phase-0.md.",
    )
    args = parser.parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    output_path = Path(args.output) if args.output else book_folder / DEFAULT_OUTPUT_NAME

    try:
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
    print(f"- **Draft Files Compiled:** {draft_count}")
    print(f"- **Compiled Words:** {word_count}")
    return 0

