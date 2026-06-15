#!/usr/bin/env python3
"""Check for chapter structure and file gaps.

Compares the chapter list in phase-0.md against actual folders and files in
the chapters/ directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_manuscript_context as validator  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify chapter folder and planning file structure."
    )
    parser.add_argument("book_folder", help="Book folder containing phase-0.md and chapters/.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    # Parse what phase-0.md expects
    try:
        expected_chapters = validator.parse_phase_chapters(book_folder)
    except Exception as e:
        print(f"Error parsing phase-0.md: {e}", file=sys.stderr)
        return 2

    # Parse what actual folders/files exist
    actual_chapters = {c.slug: c for c in validator.discover_chapters(book_folder)}

    has_failures = False
    has_warnings = False

    print(f"Checking chapter structure for {book_folder.name}...\n")

    # 1. Expected vs Actual
    for expected_slug in sorted(expected_chapters.keys()):
        if expected_slug not in actual_chapters:
            print(f"FAIL: Expected folder '{expected_slug}' is missing.")
            has_failures = True
        else:
            chapter = actual_chapters[expected_slug]
            # Check draft and planning files existence
            if not chapter.scene_breakdown.exists():
                print(f"WARN: {expected_slug} is missing scene-breakdown.md")
                has_warnings = True
            if not chapter.drafting_plan.exists():
                print(f"WARN: {expected_slug} is missing drafting-plan.md")
                has_warnings = True
            if not chapter.draft.exists():
                print(f"WARN: {expected_slug} is missing draft file ({chapter.draft.name})")
                has_warnings = True
            elif chapter.draft.exists() and not chapter.draft.read_text(encoding="utf-8").strip():
                print(f"WARN: {expected_slug} draft file exists but is empty.")
                has_warnings = True

    # 2. Unexpected Folders
    chapters_dir = book_folder / "chapters"
    if chapters_dir.exists():
        for item in sorted(chapters_dir.iterdir()):
            if item.is_dir() and item.name not in expected_chapters:
                print(f"WARN: Extra/unexpected folder '{item.name}' found in chapters/.")
                has_warnings = True

    print("\nSummary:")
    if has_failures:
        print("Chapter gaps check: FAIL")
        return 2
    elif has_warnings:
        print("Chapter gaps check: WARNING (structure check passed with warnings)")
        return 1
    
    print("Chapter gaps check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
