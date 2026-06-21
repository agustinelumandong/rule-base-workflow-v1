"""BookForge Scanner - Style Violation and Gap Checking."""

from __future__ import annotations

import re
from pathlib import Path
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
