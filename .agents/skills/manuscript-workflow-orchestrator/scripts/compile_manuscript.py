#!/usr/bin/env python3
"""Compile chapter draft files into one manuscript Markdown file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_OUTPUT_NAME = "compiled-manuscript.md"


def parse_args() -> argparse.Namespace:
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
    return parser.parse_args()


def chapter_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"chapter-(\d+)", str(path))
    if match:
        return (int(match.group(1)), path.name)
    return (999, path.name)


def read_title(book_folder: Path) -> str | None:
    phase_path = book_folder / "phase-0.md"
    if not phase_path.exists():
        return None

    for line in phase_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line.strip()
    return None


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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(manuscript, encoding="utf-8")

    return len(draft_paths), len(manuscript.split())


def main() -> int:
    args = parse_args()
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


if __name__ == "__main__":
    raise SystemExit(main())
