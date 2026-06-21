#!/usr/bin/env python3
"""BookForge Scanner Core Module.

Contains source outline parsing and file style scanning.
"""

from __future__ import annotations

import re
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


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def source_path(book_folder: Path) -> Path | None:
    for name in SOURCE_NAMES:
        path = book_folder / name
        if path.exists():
            return path
    
    # Try checking inside phase-0/ subdirectory
    phase_0_dir = book_folder / "phase-0"
    if phase_0_dir.is_dir():
        md_files = list(phase_0_dir.glob("*.md"))
        if md_files:
            md_files.sort()
            return md_files[0]
            
    return None


def normalize_target(match: re.Match[str]) -> int:
    raw_number = match.group(1).replace(",", "")
    words = int(raw_number)
    unit = match.group(2)
    if unit and unit.lower() in {"k", "thousand"}:
        words *= 1000
    return words


def first_target(text: str) -> tuple[int, str] | None:
    for line in text.splitlines():
        match = TARGET_RE.search(line)
        if match:
            return normalize_target(match), match.group(0).strip()
    return None


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


# ----------------------------------------------------------------------
# Standalone Banned Style Scanning (from scan_banned_words.py)
# ----------------------------------------------------------------------

from bookforge.core import validator

CATEGORIES: list[tuple[str, list[str]]] = [
    ("BANNED WORD", validator.BANNED_AI_ECHO_WORDS),
    ("MODERN TERM", validator.MODERN_OR_CLINICAL_WORDS),
    ("INTERNAL MONO", validator.INTERNAL_MONOLOGUE_PHRASES),
    ("UNRESOLVED", validator.UNRESOLVED_MARKERS),
]

ING_OPENER_RE = re.compile(r"^([A-Z][A-Za-z]{2,}ing)\b[\s,]")
ING_OPENER_EXCLUSIONS = {"during", "bring", "ring", "sing", "thing", "spring"}
DIALOGUE_TAG_RE = validator.DIALOGUE_TAG_RE


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    violations: list[tuple[int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return violations

    for line_num, line in enumerate(lines, start=1):
        lower = line.lower()
        stripped = line.strip()

        for category, terms in CATEGORIES:
            for term in terms:
                if term.lower() in lower:
                    violations.append((line_num, category, stripped[:120]))
                    break

        if DIALOGUE_TAG_RE.search(line):
            violations.append((line_num, "DIALOGUE TAG", stripped[:120]))

        opener = ING_OPENER_RE.match(stripped)
        if opener and opener.group(1).lower() not in ING_OPENER_EXCLUSIONS:
            violations.append((line_num, "ING OPENER", stripped[:120]))

    return violations


def check_gaps(book_folder: Path) -> tuple[list[str], list[str]]:
    expected_chapters = validator.parse_phase_chapters(book_folder)
    actual_chapters = {c.slug: c for c in validator.discover_chapters(book_folder)}
    failures: list[str] = []
    warnings: list[str] = []

    for expected_slug in sorted(expected_chapters.keys()):
        if expected_slug not in actual_chapters:
            failures.append(f"Expected folder '{expected_slug}' is missing.")
        else:
            chapter = actual_chapters[expected_slug]
            if not chapter.scene_breakdown.exists():
                warnings.append(f"{expected_slug} is missing scene-breakdown.md")
            if not chapter.drafting_plan.exists():
                warnings.append(f"{expected_slug} is missing drafting-plan.md")
            if not chapter.draft.exists():
                warnings.append(f"{expected_slug} is missing draft file ({chapter.draft.name})")
            elif chapter.draft.exists() and not chapter.draft.read_text(encoding="utf-8").strip():
                warnings.append(f"{expected_slug} draft file exists but is empty.")

    chapters_dir = book_folder / "chapters"
    if chapters_dir.exists():
        for item in sorted(chapters_dir.iterdir()):
            if item.is_dir() and item.name not in expected_chapters:
                warnings.append(f"Extra/unexpected folder '{item.name}' found in chapters/.")

    return failures, warnings


def main_gaps() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Verify chapter folder and planning file structure."
    )
    parser.add_argument("book_folder", help="Book folder containing phase-0.md and chapters/.")
    args = parser.parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    failures, warnings = check_gaps(book_folder)

    has_failures = bool(failures)
    has_warnings = bool(warnings)

    print(f"Checking chapter structure for {book_folder.name}...\n")
    for f in failures:
        print(f"FAIL: {f}")
    for w in warnings:
        print(f"WARN: {w}")

    print("\nSummary:")
    if has_failures:
        print("Chapter gaps check: FAIL")
        return 2
    elif has_warnings:
        print("Chapter gaps check: WARNING (structure check passed with warnings)")
        return 1
    
    print("Chapter gaps check: PASS")
    return 0


def main_banned_words() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Scan draft files for Western style violations with line numbers."
    )
    parser.add_argument(
        "target",
        help="A single .md draft file or a book folder to scan all chapter drafts.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output.",
    )
    args = parser.parse_args()
    use_color = not args.no_color and sys.stdout.isatty()
    target = Path(args.target)

    if not target.exists():
        print(f"Error: path not found: {target}", file=sys.stderr)
        return 2

    def find_draft_files(t: Path) -> list[Path]:
        if t.is_file():
            return [t]
        chapters_root = t / "chapters"
        if not chapters_root.exists():
            return []
        drafts: list[Path] = []
        for chapter_dir in sorted(chapters_root.iterdir(), key=validator.chapter_sort_key):
            if not chapter_dir.is_dir():
                continue
            if chapter_dir.name == "epilogue":
                candidate = chapter_dir / "epilogue.md"
            else:
                candidate = chapter_dir / f"{chapter_dir.name}.md"
            if candidate.exists():
                drafts.append(candidate)
        return drafts

    draft_files = find_draft_files(target)
    if not draft_files:
        print(f"No draft files found at: {target}", file=sys.stderr)
        return 2

    total_violations = 0
    for draft_path in draft_files:
        violations = scan_file(draft_path)
        if violations:
            header = str(draft_path)
            if use_color:
                header = f"\033[1m{header}\033[0m"
            print(header)
            for line_num, category, excerpt in violations:
                tag = f"[{category}]"
                if use_color:
                    tag = f"\033[33m{tag}\033[0m"
                print(f"  {draft_path.name}:{line_num:<5} {tag:<22} — {excerpt}")
            print()
            total_violations += len(violations)

    if total_violations == 0:
        print(f"Clean — no style violations found in {len(draft_files)} draft file(s).")
        return 0

    print(f"Found {total_violations} violation(s) across {len(draft_files)} draft file(s).")
    return 1


def main_source_format() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Scan a manuscript bible/outline source format.")
    parser.add_argument("book_folder", help="Book folder such as books/book-example.")
    parser.add_argument(
        "--target-words",
        type=int,
        help="Optional user-provided book-level target. Overrides source and rulebook targets.",
    )
    args = parser.parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists() or not book_folder.is_dir():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    try:
        scan = scan_source(book_folder, args.target_words)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    def build_report(s: SourceScan) -> str:
        def yes_no(val: bool) -> str:
            return "present" if val else "missing"
        missing = [name for name, present in s.detected_sections.items() if not present]
        present = [name for name, present in s.detected_sections.items() if present]

        lines = [
            "# Source Format Scan",
            "",
            f"- Book Folder: `{s.book_folder}`",
            f"- Source File Used: `{s.source_path}`",
            f"- Detected Title: {s.title or 'UNKNOWN'}",
            f"- Book-Level Target: ~{s.target.words:,} words",
            f"- Target Source: {s.target.source}",
            f"- Target Evidence: {s.target.evidence}",
            "",
            "## Detected Sections",
            "",
        ]

        for name in SECTION_PATTERNS:
            lines.append(f"- **{name}:** {yes_no(s.detected_sections[name])}")

        lines.extend(["", "## Missing Sections", ""])
        if missing:
            lines.extend(f"- {name}" for name in missing)
        else:
            lines.append("- None")

        lines.extend(
            [
                "",
                "## Chapter List Detail",
                "",
                f"- **Chapter Entries Detected:** {s.chapter_count}",
                f"- **Chapter Titles:** {yes_no(s.has_chapter_titles)}",
                f"- **Detailed Chapter Summaries:** {yes_no(s.has_chapter_summaries)}",
                f"- **Individual Chapter Word Counts:** {yes_no(s.has_chapter_word_counts)}",
                f"- **Hooks:** {yes_no(s.has_hooks)}",
                f"- **Tension Notes:** {yes_no(s.has_tension_notes)}",
                f"- **Transition Notes:** {yes_no(s.has_transition_notes)}",
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

    output = book_folder / "source-format-scan.md"
    output.write_text(build_report(scan), encoding="utf-8")
    print(f"Wrote {output}")
    return 0

