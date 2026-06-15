"""BookForge Research Module.

Provides functions to update and query the local research-pack.md file,
serving as the ingestion point for MCP and NotebookLM research adapters.
"""

from __future__ import annotations

import re
from pathlib import Path

DEFAULT_TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "research-pack.md"


def get_research_pack_path(book_folder: Path) -> Path:
    """Get the path to the research-pack.md file for a book."""
    return book_folder / "research-pack.md"


def ensure_research_pack(book_folder: Path) -> Path:
    """Ensure research-pack.md exists, copying template if missing."""
    path = get_research_pack_path(book_folder)
    if not path.exists():
        if DEFAULT_TEMPLATE_PATH.exists():
            path.write_text(DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            path.write_text("# Research Pack\n", encoding="utf-8")
    return path


def add_research_fact(book_folder: Path, category: str, claim: str) -> None:
    """Programmatically append a research claim under a category.
    
    If the category does not exist, it will be created.
    """
    path = ensure_research_pack(book_folder)
    content = path.read_text(encoding="utf-8")
    
    # Ensure category header matches format, e.g. "## Weapons & Ammo"
    clean_cat = category.strip()
    bullet = f"- {claim.strip()}"
    
    # Check if category exists
    cat_pattern = rf"^##\s+{re.escape(clean_cat)}\s*$"
    match = re.search(cat_pattern, content, re.MULTILINE | re.IGNORECASE)
    
    if match:
        # Category exists. Find the insert point (end of category section, before next header or EOF)
        start_idx = match.end()
        # Find next header (starting with #)
        next_header = re.search(r"^#", content[start_idx:], re.MULTILINE)
        if next_header:
            end_idx = start_idx + next_header.start()
        else:
            end_idx = len(content)
            
        section_text = content[start_idx:end_idx]
        # Check if bullet already exists to avoid duplicates
        if claim.strip() in section_text:
            return # Duplicate fact, skip
            
        # Insert bullet at the end of the section, ensuring clean spacing
        clean_section = section_text.rstrip()
        updated_section = f"{clean_section}\n{bullet}\n\n"
        content = content[:start_idx] + updated_section + content[end_idx:]
    else:
        # Category does not exist. Append to the end of the file.
        content = content.rstrip() + f"\n\n## {clean_cat}\n{bullet}\n"
        
    path.write_text(content, encoding="utf-8")
