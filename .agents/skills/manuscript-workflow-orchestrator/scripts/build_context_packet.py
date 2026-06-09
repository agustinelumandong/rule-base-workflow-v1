#!/usr/bin/env python3
"""Build a compact chapter context packet for manuscript work.

The packet is source material for Codex. It does not generate prose.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SOURCE_NAMES = ("phase-0.md", "phase-00.md", "outline.md", "chapter-outline.md")
COMPRESSED_STYLE_LOCK = (
    "Literal Western prose; no AI echo words; no modern/clinical terms; "
    "no dialogue tags when action anchors are requested; behavior over thought; source-locked."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a compact chapter context packet.")
    parser.add_argument("book_folder", help="Book folder such as books/tex-cade.")
    parser.add_argument("--chapter", required=True, help="Chapter slug such as chapter-01 or epilogue.")
    return parser.parse_args()


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


def source_path(book_folder: Path) -> Path | None:
    for name in SOURCE_NAMES:
        path = book_folder / name
        if path.exists():
            return path
    return None


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
    return book_folder / "chapters" / slug


def chapter_draft_path(folder: Path, slug: str) -> Path:
    if slug == "epilogue":
        return folder / "epilogue.md"
    return folder / f"{slug}.md"


def relevant_rulebook_excerpt(book_folder: Path, slug: str) -> str:
    text = read_optional(book_folder / "rulebook.md")
    if not text:
        return "MISSING: rulebook.md"
    parts = []
    for label in ("Source Hierarchy", "Length Handling", "Do Not Invent", "POV", "Expansion Rules"):
        section = extract_named_section(text, label)
        if section:
            parts.append(section)
    chapter_section = extract_heading_section(text, slug)
    if chapter_section:
        parts.append(chapter_section)
    if not parts:
        parts.append(extract_matching_lines(text, ["source", "length", "invent", "pov", slug]))
    return word_excerpt("\n\n".join(part for part in parts if part.strip()), 900)


def extract_named_section(text: str, name_fragment: str) -> str:
    headings = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, re.MULTILINE))
    for index, heading in enumerate(headings):
        if name_fragment.lower() not in heading.group(2).lower():
            continue
        level = len(heading.group(1))
        end = len(text)
        for next_heading in headings[index + 1 :]:
            if len(next_heading.group(1)) <= level:
                end = next_heading.start()
                break
        return text[heading.start() : end].strip()
    return ""


def prior_continuity(book_folder: Path, slug: str) -> str:
    prior = neighbor_slug(book_folder, slug, -1)
    if not prior:
        return "No prior chapter in this book folder."
    folder = chapter_folder(book_folder, prior)
    continuity = read_optional(folder / "continuity-out.md")
    if continuity:
        return word_excerpt(continuity, 450)
    scene = read_optional(folder / "scene-breakdown.md")
    lines = extract_matching_lines(scene, ["Continuity Out", "Required Story Movement"], limit=40)
    return lines or f"No continuity-out.md found for {prior}; review its scene breakdown if needed."


def next_continuity_need(book_folder: Path, slug: str) -> str:
    next_slug = neighbor_slug(book_folder, slug, 1)
    if not next_slug:
        return "No next chapter in this book folder."
    folder = chapter_folder(book_folder, next_slug)
    scene = read_optional(folder / "scene-breakdown.md")
    lines = extract_matching_lines(scene, ["Continuity In", "Required Story Movement", "Source Anchor"], limit=40)
    if lines:
        return lines
    summaries = read_optional(book_folder / "chapter-summaries.md")
    section = extract_heading_section(summaries, next_slug)
    return word_excerpt(section, 350) if section else f"No next continuity detail found for {next_slug}."


def render_packet(book_folder: Path, slug: str) -> str:
    src = source_path(book_folder)
    if src is None:
        raise RuntimeError("Missing phase-0.md, phase-00.md, outline.md, or chapter-outline.md.")
    folder = chapter_folder(book_folder, slug)
    if not folder.exists():
        raise RuntimeError(f"Missing chapter folder: {folder}")

    summaries = read_optional(book_folder / "chapter-summaries.md")
    source_text = read_optional(src)
    scene_breakdown = read_optional(folder / "scene-breakdown.md")
    draft_path = chapter_draft_path(folder, slug)

    chapter_summary = extract_heading_section(summaries, slug) or "MISSING: chapter summary section."
    source_section = extract_heading_section(source_text, slug) or "MISSING: source chapter section."
    mood_lock = read_optional(book_folder / "mood-lock.md") or "MISSING: mood-lock.md"

    lines = [
        f"# Context Packet: {slug}",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Source File:** `{src}`",
        f"- **Chapter Folder:** `{folder}`",
        f"- **Draft File:** `{draft_path}`",
        "- **Purpose:** Compact source bundle for chapter-level manuscript work.",
        "",
        "## Prompt Mode Use",
        "",
        "- Use this packet for `drafting`, `repair`, `style`, `validation`, and `expansion` work on this chapter.",
        "- Do not load the full manuscript or full rulebook unless final review or source rebuilding requires it.",
        "",
        "## Compressed Style Lock",
        "",
        COMPRESSED_STYLE_LOCK,
        "",
        "## Source Chapter Anchor",
        "",
        word_excerpt(source_section, 700),
        "",
        "## Chapter Summary",
        "",
        word_excerpt(chapter_summary, 450),
        "",
        "## Relevant Rulebook Facts",
        "",
        relevant_rulebook_excerpt(book_folder, slug),
        "",
        "## Mood And Tone Summary",
        "",
        word_excerpt(mood_lock, 450),
        "",
        "## Prior Continuity Out",
        "",
        prior_continuity(book_folder, slug),
        "",
        "## Next Continuity Need",
        "",
        next_continuity_need(book_folder, slug),
        "",
        "## Scene Breakdown",
        "",
        word_excerpt(scene_breakdown or "MISSING: scene-breakdown.md", 2200),
        "",
        "## Agent Checkpoint",
        "",
        "- **Source Used:**",
        "- **Mode:**",
        "- **Changes Made:**",
        "- **Risks:**",
        "- **Next Action:**",
        "- **Stop/Continue:**",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    try:
        packet = render_packet(book_folder, args.chapter)
        folder = chapter_folder(book_folder, args.chapter)
        output_path = folder / "context-packet.md"
        output_path.write_text(packet, encoding="utf-8")
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
