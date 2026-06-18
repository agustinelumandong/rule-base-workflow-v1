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
    from bookforge.core import series
    series_info = series.get_series_info(book_folder)
    if series_info:
        return Path(series_info["path"]) / "research-pack.md"
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


def normalize_header(header_text: str) -> str:
    """Helper to normalize a header for duplicate-checking."""
    return header_text.replace("#", "").replace("*", "").replace("_", "").strip().lower()


def extract_bold_term(bullet_line: str) -> str | None:
    """Helper to extract a leading bold term from a bullet line."""
    match = re.search(r"^\s*[\*\-\+]\s+[\*_]{2}([^\*_]+)[\*_]{2}", bullet_line)
    if match:
        return match.group(1).strip().lower()
    return None


def merge_research_pack_contents(old_content: str, new_content: str) -> str:
    """Intelligently merges new research findings into existing research-pack.md content.
    
    It scans the new content for headers and bullet points. For each section, it appends 
    only new, unique items under matching headers in the old content, preserving existing content.
    """
    new_sections = {}
    current_header = ""
    for line in new_content.splitlines():
        line_strip = line.strip()
        if line_strip.startswith("#"):
            current_header = line_strip
            new_sections[current_header] = []
        elif current_header and line_strip:
            new_sections[current_header].append(line)

    if not old_content.strip() or old_content.strip() == "# Research Pack":
        return new_content

    merged_headers = set()
    old_lines = old_content.splitlines()
    merged_lines = []
    
    i = 0
    while i < len(old_lines):
        line = old_lines[i]
        line_strip = line.strip()
        
        if line_strip.startswith("#"):
            matching_new_header = None
            old_norm = normalize_header(line_strip)
            for new_h in new_sections:
                if normalize_header(new_h) == old_norm:
                    matching_new_header = new_h
                    break
            
            merged_lines.append(line)
            i += 1
            
            existing_section_lines = []
            while i < len(old_lines) and not old_lines[i].strip().startswith("#"):
                existing_section_lines.append(old_lines[i])
                i += 1
            
            if matching_new_header:
                merged_headers.add(matching_new_header)
                new_bullets = new_sections[matching_new_header]
                
                existing_terms = set()
                existing_raw_lines = set()
                for el in existing_section_lines:
                    el_strip = el.strip()
                    if el_strip:
                        term = extract_bold_term(el_strip)
                        if term:
                            existing_terms.add(term)
                        norm_line = re.sub(r"\s+", " ", el_strip.lower())
                        existing_raw_lines.add(norm_line)
                
                bullets_to_add = []
                for nb in new_bullets:
                    nb_strip = nb.strip()
                    if not nb_strip:
                        continue
                    
                    if nb_strip.startswith("* ") or nb_strip.startswith("- ") or nb_strip.startswith("+ "):
                        nb_term = extract_bold_term(nb_strip)
                        norm_nb_line = re.sub(r"\s+", " ", nb_strip.lower())
                        
                        if nb_term and nb_term in existing_terms:
                            continue
                        if norm_nb_line in existing_raw_lines:
                            continue
                        
                        bullets_to_add.append(nb)
                    else:
                        norm_nb_line = re.sub(r"\s+", " ", nb_strip.lower())
                        if norm_nb_line not in existing_raw_lines:
                            bullets_to_add.append(nb)
                
                merged_lines.extend(existing_section_lines)
                
                while merged_lines and not merged_lines[-1].strip():
                    merged_lines.pop()
                
                if bullets_to_add:
                    merged_lines.append("")
                    merged_lines.extend(bullets_to_add)
            else:
                merged_lines.extend(existing_section_lines)
        else:
            merged_lines.append(line)
            i += 1

    for new_h, new_bullets in new_sections.items():
        if new_h not in merged_headers:
            merged_lines.append("")
            merged_lines.append(new_h)
            merged_lines.extend(new_bullets)

    return "\n".join(merged_lines).strip() + "\n"


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
