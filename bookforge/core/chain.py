#!/usr/bin/env python3
"""BookForge Continuity Handoff Chain Checker."""

from __future__ import annotations

import sys
from pathlib import Path

from bookforge.core import validator

REQUIRED_SECTIONS = [
    "## Characters",
    "## Locations",
    "## Changes",
    "## Unresolved Pressure",
    "## Next Chapter Must Know",
]


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

        # Check if the section actually has content underneath it
        start_idx = text.find(section) + len(section)
        next_indices = [text.find(sec, start_idx) for sec in REQUIRED_SECTIONS if text.find(sec, start_idx) != -1]
        end_idx = min(next_indices) if next_indices else len(text)
        
        section_content = text[start_idx:end_idx].strip()
        lines = [line.strip() for line in section_content.splitlines() if line.strip()]
        
        # Filter out placeholders like [Who is alive...]
        real_content = [l for l in lines if not l.startswith("[") and not l.endswith("]")]
        if not real_content:
            errors.append(f"Section {section} has no actual content.")

    return errors


def analyze_chain(book_folder: Path) -> tuple[bool, list[str]]:
    chapters = validator.discover_chapters(book_folder)
    if not chapters:
        return True, []

    logs = []
    has_failures = False
    for chapter in chapters:
        if not chapter.draft.exists() or not chapter.draft.read_text(encoding="utf-8").strip():
            continue
        continuity_path = chapter.continuity_out
        if not continuity_path.exists():
            logs.append(f"{chapter.slug}: continuity-out.md is MISSING.")
            has_failures = True
            continue
        errors = check_continuity_out_content(continuity_path)
        if errors:
            logs.append(f"{chapter.slug}: continuity-out.md is INVALID: {', '.join(errors)}")
            has_failures = True
    return not has_failures, logs


def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Verify the continuity handoff chain across chapter folders."
    )
    parser.add_argument("book_folder", help="Book folder containing chapters/.")
    args = parser.parse_args()
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
    for chapter in chapters:
        draft_exists = "YES" if chapter.draft.exists() else "NO"
        continuity_path = chapter.continuity_out
        
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

