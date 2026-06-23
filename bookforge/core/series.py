#!/usr/bin/env python3
"""BookForge Multi-Book Series Core Module."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from bookforge.core import validator as context_validator


def get_series_info(book_folder: Path) -> dict[str, str] | None:
    """Determines if a book folder belongs to a series.
    
    Returns a dictionary with 'name' and 'path' if nested under a series folder.
    """
    parent = book_folder.resolve().parent
    # Check if parent resides in a directory named 'books'
    if parent.name and parent.parent.name == "books":
        series_json_path = parent / "series.json"
        series_name = parent.name.replace("-", " ").title()
        if series_json_path.exists():
            try:
                data = json.loads(series_json_path.read_text(encoding="utf-8"))
                if "name" in data:
                    series_name = data["name"]
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass
        return {
            "name": series_name,
            "path": str(parent)
        }
    return None


def parse_continuity_sections(text: str) -> dict[str, str]:
    """Parse sections from a continuity-out.md text."""
    sections = {}
    headers = ["Characters", "Locations", "Changes", "Unresolved Pressure", "Next Chapter Must Know"]
    
    for header in headers:
        # Search for header at start of line
        pattern = rf"(?im)^##\s+{re.escape(header)}\s*$"
        match = re.search(pattern, text)
        if not match:
            continue
        
        start_idx = match.end()
        # Find start of next header to bound content
        next_start = len(text)
        for next_header in headers:
            next_match = re.search(rf"(?im)^##\s+{re.escape(next_header)}\s*$", text[start_idx:])
            if next_match:
                next_start = min(next_start, start_idx + next_match.start())
        
        content = text[start_idx:next_start].strip()
        # Filter out comments/placeholders like [Who is alive...]
        lines = []
        for line in content.splitlines():
            line_strip = line.strip()
            if not (line_strip.startswith("[") and line_strip.endswith("]")):
                lines.append(line)
        sections[header] = "\n".join(lines).strip()
        
    return sections


def carry_forward_book_continuity(from_book: Path, to_book: Path) -> str:
    """Carries forward continuity-out from the last chapter of from_book into to_book's rulebook."""
    if not from_book.exists():
        raise FileNotFoundError(f"Source book folder not found: {from_book}")
    if not to_book.exists():
        raise FileNotFoundError(f"Target book folder not found: {to_book}")

    # Discover chapters in source book to find the last one
    chapters = context_validator.discover_chapters(from_book)
    if not chapters:
        return "No chapters found in source book; no continuity to carry forward."

    # Sort chapters to identify the final one
    # Note: epilogue is appended/sorted last by validate check, let's locate the last draft chapter
    draft_chapters = [chap for chap in chapters if chap.draft.exists()]
    if not draft_chapters:
        return "No drafted chapters found in source book; no continuity to carry forward."

    # Identify last chapter by sort key
    last_chap = max(draft_chapters, key=lambda c: context_validator.chapter_sort_key(c.folder))
    continuity_path = last_chap.continuity_out
    if not continuity_path.exists():
        return f"Continuity file missing in last chapter: {last_chap.slug}/continuity-out.md"

    try:
        content = continuity_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return f"Failed to read continuity file: {e}"

    sections = parse_continuity_sections(content)
    
    char_state = sections.get("Characters", "No carry-over character state recorded.")
    loc_state = sections.get("Locations", "No carry-over location state recorded.")
    unresolved_state = sections.get("Unresolved Pressure", "No carry-over unresolved setups recorded.")
    changes_state = sections.get("Changes", "No carry-over chronology changes recorded.")

    carry_over_block = f"""

## Series Carry-Over Continuity (from {from_book.name})

### Characters Handoff State
{char_state}

### Locations Handoff State
{loc_state}

### Unresolved Story Pressures & Setup
{unresolved_state}

### Major Changes & Chronology
{changes_state}
"""

    rulebook_path = to_book / "rulebook.md"
    try:
        if rulebook_path.exists():
            existing_text = rulebook_path.read_text(encoding="utf-8")
            # Don't append if already carried forward once
            if f"Series Carry-Over Continuity (from {from_book.name})" not in existing_text:
                rulebook_path.write_text(existing_text + carry_over_block, encoding="utf-8")
        else:
            rulebook_path.write_text(f"# Rulebook\n" + carry_over_block, encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return f"Failed to update target rulebook: {e}"

    return f"Successfully carried forward continuity from {from_book.name} ({last_chap.slug}) into {to_book.name} rulebook."


def copy_shared_series_resources(to_book: Path) -> list[str]:
    """Copies any shared series files (series-bible.md, series-research-pack.md) from parent to book folder."""
    series_info = get_series_info(to_book)
    if not series_info:
        return []

    parent_path = Path(series_info["path"])
    copied = []

    # Copy series bible to rulebook if rulebook doesn't exist yet
    series_bible = parent_path / "series-bible.md"
    rulebook = to_book / "rulebook.md"
    if series_bible.exists() and not rulebook.exists():
        try:
            shutil.copy2(series_bible, rulebook)
            copied.append(f"Initialized rulebook.md from series-bible.md")
        except OSError:
            pass

    # Copy series research pack to research-pack.md
    series_research = parent_path / "series-research-pack.md"
    research_pack = to_book / "research-pack.md"
    if series_research.exists() and not research_pack.exists():
        try:
            shutil.copy2(series_research, research_pack)
            copied.append(f"Initialized research-pack.md from series-research-pack.md")
        except OSError:
            pass

    return copied
