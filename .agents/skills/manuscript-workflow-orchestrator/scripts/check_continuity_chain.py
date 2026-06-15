#!/usr/bin/env python3
"""Check the continuity handoff chain across all chapters.

Walks every chapter folder in sort order and checks if continuity-out.md exists,
is non-empty, and contains the required template sections.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_manuscript_context as validator  # noqa: E402

REQUIRED_SECTIONS = [
    "## Characters",
    "## Locations",
    "## Changes",
    "## Unresolved Pressure",
    "## Next Chapter Must Know",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the continuity handoff chain across chapter folders."
    )
    parser.add_argument("book_folder", help="Book folder containing chapters/.")
    return parser.parse_args()


def check_continuity_out_content(path: Path) -> list[str]:
    """Verify that the continuity-out file has all required template sections and content."""
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ["Unable to read file."]

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"Missing section: {section}")
            continue

        # Check if the section actually has content underneath it (not just template notes)
        start_idx = text.find(section) + len(section)
        # Find next section or end of file
        next_indices = [text.find(sec, start_idx) for sec in REQUIRED_SECTIONS if text.find(sec, start_idx) != -1]
        end_idx = min(next_indices) if next_indices else len(text)
        
        section_content = text[start_idx:end_idx].strip()
        lines = [line.strip() for line in section_content.splitlines() if line.strip()]
        
        # Filter out comments/placeholders
        real_content = [l for l in lines if not l.startswith("[") and not l.endswith("]")]
        if not real_content:
            errors.append(f"Section {section} has no actual content.")

    return errors


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    chapters = validator.discover_chapters(book_folder)
    if not chapters:
        print(f"No chapters discovered in: {book_folder}/chapters", file=sys.stderr)
        return 0

    print(f"Checking continuity chain for {book_folder.name}...")
    print(f"{'Chapter':<15} | {'Draft':<6} | {'continuity-out.md':<18} | {'Status':<8}")
    print("-" * 60)

    has_failures = False
    for index, chapter in enumerate(chapters):
        draft_exists = "YES" if chapter.draft.exists() else "NO"
        continuity_path = chapter.folder / "continuity-out.md"
        
        if not chapter.draft.exists():
            print(f"{chapter.slug:<15} | {draft_exists:<6} | {'—':<18} | OK (no draft)")
            continue

        if not continuity_path.exists():
            print(f"{chapter.slug:<15} | {draft_exists:<6} | {'MISSING':<18} | FAIL")
            has_failures = True
            continue

        content_errors = check_continuity_out_content(continuity_path)
        if content_errors:
            print(f"{chapter.slug:<15} | {draft_exists:<6} | {'INVALID SECTIONS':<18} | FAIL")
            for err in content_errors:
                print(f"  - {err}")
            has_failures = True
        else:
            print(f"{chapter.slug:<15} | {draft_exists:<6} | {'VALID':<18} | PASS")

    if has_failures:
        print("\nContinuity chain check: FAIL")
        return 1
    
    print("\nContinuity chain check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
