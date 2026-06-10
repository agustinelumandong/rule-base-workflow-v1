#!/usr/bin/env python3
"""Scan a book source file and report its bible/outline structure."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SOURCE_NAMES = ("phase-0.md", "phase-00.md", "outline.md", "chapter-outline.md")
DEFAULT_TARGET_WORDS = 30000

TARGET_RE = re.compile(
    r"(?i)(?:~|about|approximately|approx\.?|around)?\s*"
    r"(\d{1,3}(?:,\d{3})+|\d{4,6}|\d{1,3})\s*(k|thousand)?\s+words?"
)
BOOK_TARGET_CONTEXT_RE = re.compile(
    r"(?i)\b(?:book(?:-level)?|manuscript|novel|novella|total|target|length|word\s+count)\b"
)
NON_BOOK_TARGET_CONTEXT_RE = re.compile(r"(?i)\b(?:act|chapter|ch\.?|epilogue|scene|beat)\b")
TITLE_FIELD_RE = re.compile(r"(?im)^\s*(?:\*\*)?title(?:\*\*)?\s*[:\-]\s*(.+?)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
CHAPTER_HEADING_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:chapter|ch\.?)\s+(\d{1,3})(?:\s*[:\-]\s*(.+?))?\s*$"
)
CHAPTER_LINE_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?(?:chapter|ch\.?)\s+(\d{1,3})(?:\*\*)?"
    r"(?:\s*[:\-]\s*(.+?))?\s*$"
)
EPILOGUE_RE = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?(?:epilogue|epilogue teaser)\b")


SECTION_PATTERNS: dict[str, list[str]] = {
    "Premise": [r"\bpremise\b", r"\blogline\b", r"\bcore plot\b"],
    "Setting": [r"\bsetting\b", r"\blocation\b", r"\bworld\b", r"\bgeography\b"],
    "Characters": [r"\bcharacters?\b", r"\bcast\b", r"\bprotagonist\b", r"\bantagonist\b"],
    "Chapter List": [r"\bchapter\b", r"\boverall structure\b", r"\bplot outline\b"],
    "Act Structure": [r"\bact\b", r"\bthree-act\b", r"\b3-act\b"],
    "Epilogue": [r"\bepilogue\b", r"\bteaser\b"],
    "Weapons / Horses": [r"\bweapons?\b", r"\bhorse\b", r"\bmount\b", r"\bsignature gear\b"],
    "Factions": [r"\bfactions?\b", r"\bgang\b", r"\boutlaws?\b", r"\brecurring antagonists?\b"],
    "Series Arc": [r"\bseries arc\b", r"\bseries potential\b", r"\brecurring conflict\b"],
}


@dataclass(frozen=True)
class TargetInfo:
    words: int
    source: str
    evidence: str


@dataclass(frozen=True)
class SourceScan:
    book_folder: Path
    source_path: Path
    title: str
    target: TargetInfo
    detected_sections: dict[str, bool]
    chapter_count: int
    has_chapter_titles: bool
    has_chapter_summaries: bool
    has_chapter_word_counts: bool
    has_hooks: bool
    has_tension_notes: bool
    has_transition_notes: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan a manuscript bible/outline source format.")
    parser.add_argument("book_folder", help="Book folder such as books/tex-cade.")
    parser.add_argument(
        "--target-words",
        type=int,
        help="Optional user-provided book-level target. Overrides source and rulebook targets.",
    )
    return parser.parse_args()


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def source_path(book_folder: Path) -> Path | None:
    for name in SOURCE_NAMES:
        path = book_folder / name
        if path.exists():
            return path
    return None


def normalize_target(match: re.Match[str]) -> int:
    raw_number = match.group(1).replace(",", "")
    words = int(raw_number)
    unit = match.group(2)
    if unit and unit.lower() in {"k", "thousand"}:
        words *= 1000
    return words


def first_target(text: str) -> tuple[int, str] | None:
    match = TARGET_RE.search(text)
    if not match:
        return None
    return normalize_target(match), match.group(0).strip()


def first_book_target(text: str) -> tuple[int, str] | None:
    for line in text.splitlines():
        if not BOOK_TARGET_CONTEXT_RE.search(line):
            continue
        if NON_BOOK_TARGET_CONTEXT_RE.search(line):
            continue
        match = TARGET_RE.search(line)
        if match:
            return normalize_target(match), match.group(0).strip()
    return None


def resolve_target(book_folder: Path, source_text: str, user_target: int | None = None) -> TargetInfo:
    if user_target:
        return TargetInfo(user_target, "user", f"--target-words {user_target}")

    source_target = first_book_target(source_text)
    if source_target:
        words, evidence = source_target
        return TargetInfo(words, "source", evidence)

    rulebook_text = read_optional(book_folder / "rulebook.md")
    rulebook_target = first_book_target(rulebook_text)
    if rulebook_target:
        words, evidence = rulebook_target
        return TargetInfo(words, "rulebook", evidence)

    return TargetInfo(DEFAULT_TARGET_WORDS, "default", "No user/source/rulebook target found.")


def detect_title(text: str, source_path_value: Path) -> str:
    title_match = TITLE_FIELD_RE.search(text)
    if title_match:
        return clean_inline(title_match.group(1))
    heading_match = HEADING_RE.search(text)
    if heading_match:
        return clean_inline(heading_match.group(2))
    return source_path_value.parent.name.replace("-", " ").title()


def clean_inline(value: str) -> str:
    value = re.sub(r"[*_`]+", "", value)
    return value.strip(" -:\t")


def headings(text: str) -> list[str]:
    return [clean_inline(match.group(2)).lower() for match in HEADING_RE.finditer(text)]


def section_present(text: str, heading_values: list[str], patterns: list[str]) -> bool:
    for pattern in patterns:
        compiled = re.compile(pattern, re.IGNORECASE)
        if any(compiled.search(heading) for heading in heading_values):
            return True
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def chapter_matches(text: str) -> list[re.Match[str]]:
    matches = list(CHAPTER_HEADING_RE.finditer(text))
    if matches:
        return matches
    return list(CHAPTER_LINE_RE.finditer(text))


def chapter_sections(text: str, matches: list[re.Match[str]]) -> list[str]:
    sections: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append(text[match.start() : end].strip())
    return sections


def has_summary_sections(sections: list[str]) -> bool:
    return any(len(section.split()) >= 35 for section in sections)


def scan_source(book_folder: Path, user_target: int | None = None) -> SourceScan:
    src = source_path(book_folder)
    if src is None:
        raise RuntimeError("Missing phase-0.md, phase-00.md, outline.md, or chapter-outline.md.")

    text = src.read_text(encoding="utf-8")
    heading_values = headings(text)
    detected_sections = {
        name: section_present(text, heading_values, patterns)
        for name, patterns in SECTION_PATTERNS.items()
    }
    chapters = chapter_matches(text)
    sections = chapter_sections(text, chapters)
    chapter_title_count = sum(1 for match in chapters if match.group(2) and clean_inline(match.group(2)))
    chapter_word_count_hits = [
        section
        for section in sections
        if re.search(r"(?i)(?:~|about|around|approximately|approx\.?)?\s*\d[\d,]*\s*(?:k|thousand)?\s+words?", section)
    ]

    return SourceScan(
        book_folder=book_folder,
        source_path=src,
        title=detect_title(text, src),
        target=resolve_target(book_folder, text, user_target),
        detected_sections=detected_sections,
        chapter_count=len(chapters) + (1 if EPILOGUE_RE.search(text) else 0),
        has_chapter_titles=chapter_title_count > 0,
        has_chapter_summaries=has_summary_sections(sections),
        has_chapter_word_counts=bool(chapter_word_count_hits),
        has_hooks=bool(re.search(r"(?i)\bhook\b", text)),
        has_tension_notes=bool(re.search(r"(?i)\btension\b", text)),
        has_transition_notes=bool(re.search(r"(?i)\btransition\b", text)),
    )


def yes_no(value: bool) -> str:
    return "present" if value else "missing"


def build_report(scan: SourceScan) -> str:
    missing = [name for name, present in scan.detected_sections.items() if not present]
    present = [name for name, present in scan.detected_sections.items() if present]

    lines = [
        "# Source Format Scan",
        "",
        f"- Book Folder: `{scan.book_folder}`",
        f"- Source File Used: `{scan.source_path}`",
        f"- Detected Title: {scan.title or 'UNKNOWN'}",
        f"- Book-Level Target: ~{scan.target.words:,} words",
        f"- Target Source: {scan.target.source}",
        f"- Target Evidence: {scan.target.evidence}",
        "",
        "## Detected Sections",
        "",
    ]

    for name in SECTION_PATTERNS:
        lines.append(f"- **{name}:** {yes_no(scan.detected_sections[name])}")

    lines.extend(
        [
            "",
            "## Missing Sections",
            "",
        ]
    )
    if missing:
        lines.extend(f"- {name}" for name in missing)
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Chapter List Detail",
            "",
            f"- **Chapter Entries Detected:** {scan.chapter_count}",
            f"- **Chapter Titles:** {yes_no(scan.has_chapter_titles)}",
            f"- **Detailed Chapter Summaries:** {yes_no(scan.has_chapter_summaries)}",
            f"- **Individual Chapter Word Counts:** {yes_no(scan.has_chapter_word_counts)}",
            f"- **Hooks:** {yes_no(scan.has_hooks)}",
            f"- **Tension Notes:** {yes_no(scan.has_tension_notes)}",
            f"- **Transition Notes:** {yes_no(scan.has_transition_notes)}",
            "",
            "## Extraction Notes",
            "",
            "- Treat this scan as an intake map, not a story source.",
            "- Use the source file as the highest authority for story facts.",
            "- Preserve source-provided chapter word counts only as elastic planning guidance.",
            "- If no source or rulebook target exists, use the default `~30,000 words` as book-level guidance.",
            "- Do not turn the total target into per-chapter quotas.",
            "- Mark missing premise, setting, motivation, lore, relationship, or continuity facts as `UNKNOWN`.",
        ]
    )

    if present:
        lines.extend(["", "## Present Section Summary", ""])
        lines.extend(f"- {name}" for name in present)

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists() or not book_folder.is_dir():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    try:
        scan = scan_source(book_folder, args.target_words)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    output = book_folder / "source-format-scan.md"
    output.write_text(build_report(scan), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
