#!/usr/bin/env python3
"""BookForge Chapter Context Packet Builder Core Module."""

from __future__ import annotations

import re
from pathlib import Path

from bookforge.core.headroom import compress_text
from bookforge.core import world as world_module

SOURCE_NAMES = ("phase-0.md", "phase-00.md", "outline.md", "chapter-outline.md")
COMPRESSED_STYLE_LOCK = (
    "Literal Western prose; no AI echo words; no modern/clinical terms; "
    "no dialogue tags when action anchors are requested; behavior over thought; source-locked."
)


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


def optimize_character_profiles(rulebook_text: str, active_characters: list[str], all_characters: list[str]) -> str:
    """Removes details for characters that are not active in this chapter's breakdown."""
    inactive_characters = [c for c in all_characters if c not in active_characters]
    optimized_text = rulebook_text
    for char in inactive_characters:
        # Match ### CharName or ## CharName headings
        pattern = re.compile(
            r"^(#{2,4})\s+(" + re.escape(char) + r"|character:\s*" + re.escape(char) + r")\s*$",
            re.MULTILINE | re.IGNORECASE
        )
        headings = list(pattern.finditer(optimized_text))
        for h in reversed(headings):
            level = len(h.group(1))
            title = h.group(2)
            # Find next heading with same or higher level
            next_heading_pattern = re.compile(
                r"^(#{1," + str(level) + r"})\s+(.+?)\s*$",
                re.MULTILINE
            )
            next_headings = list(next_heading_pattern.finditer(optimized_text[h.start() + 1:]))
            end = len(optimized_text)
            if next_headings:
                end = h.start() + 1 + next_headings[0].start()
            optimized_text = (
                optimized_text[:h.start()]
                + f"\n[Profile for inactive character '{title}' excluded to optimize context budget]\n"
                + optimized_text[end:]
            )
    return optimized_text


def relevant_rulebook_excerpt(book_folder: Path, slug: str, scene_breakdown_text: str = "") -> str:
    text = read_optional(book_folder / "rulebook.md")
    if not text:
        return "MISSING: rulebook.md"
    parts = []
    for label in ("Source Hierarchy", "Length Handling", "Do Not Invent", "POV", "Expansion Rules"):
        section = extract_named_section(text, label)
        if section:
            parts.append(section)
            
    # Optimize Character Profiles using world-state
    char_section = extract_named_section(text, "Characters") or extract_named_section(text, "Dramatis Personae")
    if char_section:
        world_state = world_module.load_world_state(book_folder)
        all_chars = list(world_state.get("characters", {}).keys())
        
        # Scan scene breakdown for active character mentions
        active_chars = []
        for char in all_chars:
            if re.search(rf"\b{re.escape(char)}\b", scene_breakdown_text, re.IGNORECASE):
                active_chars.append(char)
                
        # If no active characters were parsed (e.g. empty breakdown), fallback to all
        if not active_chars:
            active_chars = all_chars
            
        opt_char_section = optimize_character_profiles(char_section, active_chars, all_chars)
        parts.append(opt_char_section)

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


def pacing_excerpt(book_folder: Path, slug: str) -> str:
    text = read_optional(book_folder / "chapter-pacing-plan.md")
    if not text:
        return "No chapter-pacing-plan.md found. Use source scope only; do not force uniform chapter length."
    labels = [slug]
    number = chapter_number(slug)
    if slug == "epilogue":
        labels.append("Epilogue")
    elif number is not None:
        labels.extend([f"Chapter {number}", f"Chapter {number:02d}"])
    lines = extract_matching_lines(text, labels + ["Source Rule", "Length Rule"], limit=16)
    return lines or "No matching pacing row found. Use source scope only; do not force uniform chapter length."


def relevant_research_excerpt(book_folder: Path, scene_breakdown_text: str) -> str:
    research_file = book_folder / "research-pack.md"
    if not research_file.exists():
        return ""
    
    content = research_file.read_text(encoding="utf-8")
    sections = re.split(r"^##\s+", content, flags=re.MULTILINE)
    
    section_map: dict[str, str] = {}
    for section in sections[1:]:
        lines = section.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        section_map[title] = "## " + section.strip()
        
    keyword_map = {
        "Weapons & Ammo": ["weapon", "ammo", "gun", "rifle", "pistol", "revolver", "shoot", "fire", "shot", "colt", "winchester", "sharps", "bullet", "cartridge"],
        "Travel & Transport": ["travel", "transport", "stagecoach", "horse", "ride", "gallop", "train", "wagon", "rail", "road", "track", "trail", "saddle", "stage"],
        "Medicine & Survival": ["medicine", "survival", "doctor", "wound", "treat", "injured", "hurt", "acid", "carbolic", "pain", "whiskey", "morphia", "laudanum", "bandage", "bleed"],
        "Clothing & Gear": ["clothing", "gear", "garb", "shirt", "trousers", "boots", "hat", "canvas", "leather", "belt", "holster"]
    }
    
    breakdown_words = set(re.findall(r"\b[a-zA-Z]+\b", scene_breakdown_text.lower()))
    
    active_sections: list[str] = []
    for title, sec_content in section_map.items():
        keywords = keyword_map.get(title, [])
        title_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", title) if len(w) > 3]
        keywords.extend(title_words)
        
        if any(kw in breakdown_words for kw in keywords):
            active_sections.append(sec_content)
            
    if not active_sections:
        return ""
        
    return "\n\n".join(active_sections)


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

    source_sec_comp = compress_text(source_section)
    chapter_sum_comp = compress_text(chapter_summary)
    rulebook_excerpt = relevant_rulebook_excerpt(book_folder, slug, scene_breakdown)
    rulebook_comp = compress_text(rulebook_excerpt)
    mood_lock_comp = compress_text(mood_lock)
    pacing_guidance = pacing_excerpt(book_folder, slug)
    pacing_comp = compress_text(pacing_guidance)
    prior_cont = prior_continuity(book_folder, slug)
    prior_comp = compress_text(prior_cont)
    next_cont = next_continuity_need(book_folder, slug)
    next_comp = compress_text(next_cont)
    scene_bd_comp = compress_text(scene_breakdown or "MISSING: scene-breakdown.md")
    
    research_excerpt = relevant_research_excerpt(book_folder, scene_breakdown or "")
    research_comp = compress_text(research_excerpt)

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
        word_excerpt(source_sec_comp, 700),
        "",
        "## Chapter Summary",
        "",
        word_excerpt(chapter_sum_comp, 450),
        "",
        "## Relevant Rulebook Facts",
        "",
        word_excerpt(rulebook_comp, 900),
        "",
        "## Relevant Research Facts",
        "",
        word_excerpt(research_comp, 600),
        "",
        "## Mood And Tone Summary",
        "",
        word_excerpt(mood_lock_comp, 450),
        "",
        "## Pacing Guidance",
        "",
        pacing_comp,
        "",
        "## Prior Continuity Out",
        "",
        word_excerpt(prior_comp, 450),
        "",
        "## Next Continuity Need",
        "",
        word_excerpt(next_comp, 350),
        "",
        "## Scene Breakdown",
        "",
        word_excerpt(scene_bd_comp, 2200),
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
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Build a compact chapter context packet.")
    parser.add_argument("book_folder", help="Book folder such as books/tex-cade.")
    parser.add_argument("--chapter", required=True, help="Chapter slug such as chapter-01 or epilogue.")
    args = parser.parse_args()
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
