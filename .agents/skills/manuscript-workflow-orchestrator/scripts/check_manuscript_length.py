#!/usr/bin/env python3
"""Report manuscript draft length against a book-level target."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TARGET_RE = re.compile(
    r"(?i)(?:~|about|approximately|approx\.?)?\s*"
    r"(\d{1,3}(?:,\d{3})+|\d{4,6})\s+words?"
)


@dataclass(frozen=True)
class DraftCount:
    label: str
    words: int
    is_epilogue: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check manuscript draft progress against the book-level word target."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/tex-cade",
        help="Book folder containing phase-0.md, rulebook.md, and chapters/.",
    )
    return parser.parse_args()


def word_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def find_target(book_folder: Path) -> int:
    source_paths = [book_folder / "phase-0.md", book_folder / "rulebook.md"]
    existing_sources = [path for path in source_paths if path.exists()]
    if not existing_sources:
        raise RuntimeError("Missing phase-0.md or rulebook.md; cannot detect target.")

    for path in existing_sources:
        text = path.read_text(encoding="utf-8")
        match = TARGET_RE.search(text)
        if match:
            return int(match.group(1).replace(",", ""))

    raise RuntimeError("Could not detect a book-level word target.")


def chapter_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"chapter-(\d+)", str(path))
    if match:
        return (int(match.group(1)), path.name)
    return (999, path.name)


def find_drafts(book_folder: Path) -> list[DraftCount]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        raise RuntimeError("Missing chapters folder; no manuscript drafts found.")

    counts: list[DraftCount] = []
    chapter_paths = sorted(
        chapters_root.glob("chapter-*/chapter-*.md"),
        key=chapter_sort_key,
    )
    for path in chapter_paths:
        label = path.parent.name.replace("-", " ").title()
        counts.append(DraftCount(label=label, words=word_count(path)))

    epilogue_path = chapters_root / "epilogue" / "epilogue.md"
    if epilogue_path.exists():
        counts.append(DraftCount(label="Epilogue", words=word_count(epilogue_path), is_epilogue=True))

    if not counts:
        raise RuntimeError("No manuscript draft files found.")

    return counts


def pct(value: float) -> str:
    return f"{value:.1f}%"


def build_report(book_folder: Path, target: int, counts: list[DraftCount]) -> str:
    total = sum(item.words for item in counts)
    remaining = max(target - total, 0)
    complete = (total / target * 100) if target else 0
    normal_chapters = [item for item in counts if not item.is_epilogue]
    chapter_average = (
        round(sum(item.words for item in normal_chapters) / len(normal_chapters))
        if normal_chapters
        else 0
    )
    low_chapter_threshold = round(chapter_average * 0.70) if chapter_average else 0

    lines = [
        "# Manuscript Length Report",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Target Words:** {target}",
        f"- **Current Words:** {total}",
        f"- **Remaining Words:** {remaining}",
        f"- **Complete:** {pct(complete)}",
        f"- **Average Chapter Words:** {chapter_average}",
        "",
        "## Draft Counts",
        "",
        "| Section | Words |",
        "| --- | ---: |",
    ]

    for item in counts:
        lines.append(f"| {item.label} | {item.words} |")

    lines.extend(["", "## Warnings", ""])

    warnings: list[str] = []
    if total < target * 0.90:
        warnings.append(
            f"Total draft is below 90% of target; expansion is needed without padding or invented story."
        )

    for item in normal_chapters:
        if low_chapter_threshold and item.words < low_chapter_threshold:
            warnings.append(
                f"{item.label} is far below the current chapter average; revisit approved beats for source-supported expansion."
            )

    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- No length warnings.")

    lines.extend(
        [
            "",
            "## Expansion Guidance",
            "",
            "- Revisit approved scene breakdowns before expanding prose.",
            "- Add only source-supported action, consequence, conflict, dialogue, setting texture, and transition.",
            "- Do not add unsupported events, names, motives, lore, or backstory to close the gap.",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    try:
        target = find_target(book_folder)
        counts = find_drafts(book_folder)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(build_report(book_folder, target, counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
