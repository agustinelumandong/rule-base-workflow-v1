"""Helper functions for packet building, paths, and chapter slugs."""

from __future__ import annotations

import re
from pathlib import Path


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def word_excerpt(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return text.strip()
    return " ".join(words[:limit]).strip() + "\n\n[Excerpt trimmed for token budget.]"


def chapter_number(slug: str) -> int | None:
    match = re.search(r"chapter-(\d+)", slug)
    return int(match.group(1)) if match else None


def chapter_label_patterns(slug: str) -> list[str]:
    if slug == "epilogue":
        return [r"\bEpilogue\b", r"\bEpilogue Teaser\b"]
    number = chapter_number(slug)
    if number is None:
        return [re.escape(slug)]
    return [
        rf"\bChapter\s+{number}\b",
        rf"\bChapter\s+{number:02d}\b",
        rf"\b{slug}\b",
    ]


def extract_heading_section(text: str, slug: str) -> str:
    if not text.strip():
        return ""
    headings = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, re.MULTILINE))
    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in chapter_label_patterns(slug)]
    for index, heading in enumerate(headings):
        title = heading.group(2)
        if not any(pattern.search(title) for pattern in patterns):
            continue
        level = len(heading.group(1))
        end = len(text)
        for next_heading in headings[index + 1 :]:
            if len(next_heading.group(1)) <= level:
                end = next_heading.start()
                break
        return text[heading.start() : end].strip()
    return ""


def extract_matching_lines(text: str, labels: list[str], limit: int = 80) -> str:
    if not text.strip():
        return ""
    matches: list[str] = []
    for line in text.splitlines():
        if any(label.lower() in line.lower() for label in labels):
            matches.append(line)
    return "\n".join(matches[:limit]).strip()


def chapter_sort_key(path: Path) -> tuple[int, str]:
    if path.name == "epilogue":
        return (999, path.name)
    number = chapter_number(path.name)
    return (number if number is not None else 998, path.name)


def chapter_slugs(book_folder: Path) -> list[str]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        return []
    return [path.name for path in sorted(chapters_root.iterdir(), key=chapter_sort_key) if path.is_dir()]


def neighbor_slug(book_folder: Path, slug: str, offset: int) -> str | None:
    slugs = chapter_slugs(book_folder)
    if slug not in slugs:
        return None
    index = slugs.index(slug) + offset
    if index < 0 or index >= len(slugs):
        return None
    return slugs[index]


def chapter_folder(book_folder: Path, slug: str) -> Path:
    changes_path = book_folder / "changes" / slug
    if changes_path.exists():
        return changes_path
    return book_folder / "chapters" / slug


def chapter_draft_path(folder: Path, slug: str) -> Path:
    draft_options = ["draft.md", f"{slug}.md", "epilogue.md" if slug == "epilogue" else f"{slug}.md"]
    for opt in draft_options:
        p = folder / opt
        if p.exists():
            return p
    return folder / draft_options[0]
