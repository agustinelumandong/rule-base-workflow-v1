"""Relevant excerpt builders (rulebook, pacing, research) for packet context."""

from __future__ import annotations

import json
import re
import yaml
from pathlib import Path

from bookforge.core import world as world_module
from bookforge.core import characters as characters_module
from bookforge.core.packet.helpers import (
    read_optional,
    word_excerpt,
    chapter_number,
    extract_heading_section,
    extract_matching_lines,
    neighbor_slug,
    chapter_folder,
)


def optimize_character_profiles(rulebook_text: str, active_characters: list[str], all_characters: list[str]) -> str:
    """Removes details for characters that are not active in this chapter's breakdown."""
    inactive_characters = [c for c in all_characters if c not in active_characters]
    optimized_text = rulebook_text
    for char in inactive_characters:
        pattern = re.compile(
            r"^(#{2,4})\s+(" + re.escape(char) + r"|character:\s*" + re.escape(char) + r")\s*$",
            re.MULTILINE | re.IGNORECASE
        )
        headings = list(pattern.finditer(optimized_text))
        for h in reversed(headings):
            level = len(h.group(1))
            title = h.group(2)
            next_heading_pattern = re.compile(
                r"^#{1," + str(level) + r"}\s+(.+?)\s*$",
                re.MULTILINE
            )
            section_tail = optimized_text[h.end():]
            next_headings = list(next_heading_pattern.finditer(section_tail))
            end = len(optimized_text)
            if next_headings:
                end = h.end() + next_headings[0].start()
            optimized_text = (
                optimized_text[:h.start()]
                + f"\n[Profile for inactive character '{title}' excluded to optimize context budget]\n"
                + optimized_text[end:]
            )
    return optimized_text


def relevant_rulebook_excerpt_from_text(book_folder: Path, slug: str, rulebook_text: str, scene_breakdown_text: str) -> str:
    parts = []
    for label in ("Source Hierarchy", "Length Handling", "Do Not Invent", "POV", "Expansion Rules"):
        section = extract_named_section(rulebook_text, label)
        if section:
            parts.append(section)

    char_section = extract_named_section(rulebook_text, "Characters") or extract_named_section(rulebook_text, "Dramatis Personae")
    if char_section:
        world_state = world_module.load_world_state(book_folder)
        all_chars = list(world_state.get("characters", {}).keys())
        active_chars = [
            char for char in all_chars
            if re.search(rf"\b{re.escape(char)}\b", scene_breakdown_text, re.IGNORECASE)
        ] or all_chars
        parts.append(optimize_character_profiles(char_section, active_chars, all_chars))

        from bookforge.core import relationship as relationship_module
        active_rels = []
        for rel in relationship_module.load_relationships(book_folder):
            sub = rel.get("subject", "").lower()
            obj = rel.get("object", "").lower()
            if sub in active_chars and obj in active_chars:
                active_rels.append(rel)
        if active_rels:
            rel_lines = ["\n### Active Character Relationships"]
            for rel in active_rels:
                rel_lines.append(f"- **{rel['subject']}** {rel['relation']} **{rel['object']}**")
            parts.append("\n".join(rel_lines))

        subgenre_rules = load_subgenre_rules(book_folder)
        if subgenre_rules:
            parts.append(subgenre_rules)

    chapter_section = extract_heading_section(rulebook_text, slug)
    if chapter_section:
        parts.append(chapter_section)
    if not parts:
        parts.append(extract_matching_lines(rulebook_text, ["source", "length", "invent", "pov", slug]))
    return word_excerpt("\n\n".join(part for part in parts if part.strip()), 900)


def relevant_rulebook_excerpt(book_folder: Path, slug: str, scene_breakdown_text: str = "") -> str:
    text = read_optional(book_folder / "rulebook.md")
    if not text:
        return "MISSING: rulebook.md"
    parts = []
    for label in ("Source Hierarchy", "Length Handling", "Do Not Invent", "POV", "Expansion Rules"):
        section = extract_named_section(text, label)
        if section:
            parts.append(section)
            
    char_section = extract_named_section(text, "Characters") or extract_named_section(text, "Dramatis Personae")
    if char_section:
        world_state = world_module.load_world_state(book_folder)
        all_chars = list(world_state.get("characters", {}).keys())
        
        active_chars = []
        for char in all_chars:
            if re.search(rf"\b{re.escape(char)}\b", scene_breakdown_text, re.IGNORECASE):
                active_chars.append(char)
                
        if not active_chars:
            active_chars = all_chars
            
        opt_char_section = optimize_character_profiles(char_section, active_chars, all_chars)
        parts.append(opt_char_section)

        from bookforge.core import relationship as relationship_module
        all_rels = relationship_module.load_relationships(book_folder)
        active_rels = []
        for rel in all_rels:
            sub = rel.get("subject", "").lower()
            obj = rel.get("object", "").lower()
            if sub in active_chars and obj in active_chars:
                active_rels.append(rel)
        if active_rels:
            rel_lines = ["\n### Active Character Relationships"]
            for rel in active_rels:
                rel_lines.append(f"- **{rel['subject']}** {rel['relation']} **{rel['object']}**")
            parts.append("\n".join(rel_lines))

        subgenre_rules = load_subgenre_rules(book_folder)
        if subgenre_rules:
            parts.append(subgenre_rules)

    chapter_section = extract_heading_section(text, slug)
    if chapter_section:
        parts.append(chapter_section)
    if not parts:
        parts.append(extract_matching_lines(text, ["source", "length", "invent", "pov", slug]))
    return word_excerpt("\n\n".join(part for part in parts if part.strip()), 900)


def relevant_character_profiles(book_folder: Path, scene_breakdown_text: str, limit: int = 700) -> str:
    profiles, warnings = characters_module.load_character_profiles(book_folder)
    if not profiles and not warnings:
        return ""

    active_profiles = [
        profile
        for profile in profiles
        if _profile_is_active(profile, scene_breakdown_text)
    ]
    if not active_profiles:
        active_profiles = [profile for profile in profiles if profile.category == "main"]

    parts: list[str] = []
    parts.extend(warnings)
    for profile in active_profiles:
        parts.append(_render_character_profile_excerpt(profile))

    return word_excerpt("\n\n".join(part for part in parts if part.strip()), limit)


def _profile_is_active(profile: characters_module.CharacterProfile, scene_breakdown_text: str) -> bool:
    if not scene_breakdown_text.strip():
        return False
    for term in profile.match_terms:
        if _term_in_text(term, scene_breakdown_text):
            return True
    return False


def _term_in_text(term: str, text: str) -> bool:
    normalized_term = re.escape(term).replace(r"\ ", r"[\s_-]+").replace(r"\-", r"[\s_-]+")
    return bool(re.search(rf"(?<![A-Za-z0-9]){normalized_term}(?![A-Za-z0-9])", text, re.IGNORECASE))


def _render_character_profile_excerpt(profile: characters_module.CharacterProfile) -> str:
    aliases = ", ".join(profile.aliases) if profile.aliases else "None"
    pov = "yes" if profile.pov_allowed else "no"
    header = [
        f"### {profile.canonical_name}",
        f"- **ID:** {profile.id}",
        f"- **Category:** {profile.category}",
        f"- **Role:** {profile.story_role or 'Not specified'}",
        f"- **POV Allowed:** {pov}",
        f"- **Aliases:** {aliases}",
        f"- **Profile:** `{profile.path}`",
    ]
    body = profile.body.strip()
    return "\n".join(header + (["", body] if body else []))


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
    if not continuity and "changes" in folder.parts:
        parts = list(folder.parts)
        try:
            idx = parts.index("changes")
            parts[idx] = "chapters"
            fallback_folder = Path(*parts)
            continuity = read_optional(fallback_folder / "continuity-out.md")
        except ValueError:
            pass
    if continuity:
        return word_excerpt(continuity, 450)
    proposal_path = folder / "proposal.md"
    scene_bd_path = folder / "scene-breakdown.md"
    scene = read_optional(proposal_path if proposal_path.exists() or not scene_bd_path.exists() else scene_bd_path)
    lines = extract_matching_lines(scene, ["Continuity Out", "Required Story Movement"], limit=40)
    return lines or f"No continuity-out.md found for {prior}; review its scene breakdown if needed."


def next_continuity_need(book_folder: Path, slug: str) -> str:
    next_slug = neighbor_slug(book_folder, slug, 1)
    if not next_slug:
        return "No next chapter in this book folder."
    folder = chapter_folder(book_folder, next_slug)
    proposal_path = folder / "proposal.md"
    scene_bd_path = folder / "scene-breakdown.md"
    scene = read_optional(proposal_path if proposal_path.exists() or not scene_bd_path.exists() else scene_bd_path)
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
    from bookforge.core.research import get_research_pack_path
    research_file = get_research_pack_path(book_folder)
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


def load_subgenre_rules(book_folder: Path) -> str:
    try:
        world_state = world_module.load_world_state(book_folder)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
        world_state = {}
    genre = world_state.get("genre", "western").lower()
    subgenre = world_state.get("subgenre", "classic").lower()
    
    config_path = Path(__file__).resolve().parent.parent.parent / "genre_packs" / genre / f"{genre}_subgenre_config.yaml"
    if not config_path.exists():
        return ""
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        sub_info = config.get("subgenres", {}).get(subgenre)
        if not sub_info:
            return ""
            
        rules = [
            f"### Active Subgenre Guidelines: {genre.capitalize()} ({subgenre.capitalize()})",
            f"- Tone: {sub_info.get('tone', 'unknown')}",
            f"- Focus: {sub_info.get('focus', 'unknown')}",
            "- **Typical Conflicts:** " + ", ".join(sub_info.get("common_conflicts", []))
        ]
        
        prompt_blocks_path = Path(__file__).resolve().parent.parent.parent / "genre_packs" / genre / f"{genre}_prompt_blocks.md"
        if prompt_blocks_path.exists():
            rules.append(f"\n{prompt_blocks_path.read_text(encoding='utf-8')}")
            
        return "\n".join(rules)
    except (yaml.YAMLError, OSError, UnicodeDecodeError, KeyError, AttributeError) as e:
        return f"\n[Error loading subgenre rules: {e}]\n"
