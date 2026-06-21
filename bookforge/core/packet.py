#!/usr/bin/env python3
"""BookForge Chapter Context Packet Builder Core Module."""

from __future__ import annotations

import json
import re
from pathlib import Path

from bookforge.core.adapters.compression import get_compression_backend
from bookforge.core import world as world_module
from bookforge.core.scanner import source_path

def compress_text(text: str) -> str:
    return get_compression_backend().compress(text)

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
    changes_path = book_folder / "changes" / slug
    if changes_path.exists():
        return changes_path
    return book_folder / "chapters" / slug


def chapter_draft_path(folder: Path, slug: str) -> Path:
    draft_options = ["draft.md", f"{slug}.md", "epilogue.md" if slug == "epilogue" else f"{slug}.md"]
    for opt in draft_options:
        p = folder / opt
        if p.exists():
            return p
    return folder / draft_options[0]



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


def build_context_packet(
    book_folder: Path,
    rulebook_text: str | None = None,
    scene_breakdown_text: str | None = None,
    slug: str = "chapter-01",
) -> str:
    if rulebook_text is None and scene_breakdown_text is None:
        return render_packet(book_folder, slug)

    scene_breakdown_text = scene_breakdown_text or ""
    rulebook_text = rulebook_text if rulebook_text is not None else read_optional(book_folder / "rulebook.md")
    rulebook_excerpt = relevant_rulebook_excerpt_from_text(book_folder, slug, rulebook_text, scene_breakdown_text)
    return "\n".join(
        [
            f"# Context Packet: {slug}",
            "",
            "## Relevant Rulebook Facts",
            "",
            rulebook_excerpt,
            "",
            "## Scene Breakdown",
            "",
            scene_breakdown_text,
        ]
    ).rstrip() + "\n"


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

        # Inject active relationships
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

        # Inject subgenre guidelines
        subgenre_rules = load_subgenre_rules(book_folder)
        if subgenre_rules:
            parts.append(subgenre_rules)

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


TASK_BUDGETS = {
    "all": 8000,
    "draft-prose": 2500,
    "continuity-check": 1500,
    "extract-memory": 1000,
    "revise-style": 1500,
    "validate-change": 1500,
}


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def render_packet(book_folder: Path, slug: str, task: str = "all") -> str:
    src = source_path(book_folder)
    if src is None:
        raise RuntimeError("Missing phase-0.md, phase-00.md, outline.md, or chapter-outline.md.")
    folder = chapter_folder(book_folder, slug)
    if not folder.exists():
        raise RuntimeError(f"Missing chapter folder: {folder}")

    summaries = read_optional(book_folder / "chapter-summaries.md")
    source_text = read_optional(src)
    proposal_path = folder / "proposal.md"
    scene_bd_path = folder / "scene-breakdown.md"
    scene_breakdown_file = proposal_path if proposal_path.exists() or not scene_bd_path.exists() else scene_bd_path
    scene_breakdown = read_optional(scene_breakdown_file)
    draft_path = chapter_draft_path(folder, slug)
    draft_content = read_optional(draft_path)

    parts = []

    if task == "draft-prose":
        chapter_summary = extract_heading_section(summaries, slug) or "MISSING: chapter summary section."
        source_section = extract_heading_section(source_text, slug) or "MISSING: source chapter section."
        mood_lock = read_optional(book_folder / "mood-lock.md") or "MISSING: mood-lock.md"
        rulebook_excerpt = relevant_rulebook_excerpt(book_folder, slug, scene_breakdown)
        pacing_guidance = pacing_excerpt(book_folder, slug)
        prior_cont = prior_continuity(book_folder, slug)
        research_excerpt = relevant_research_excerpt(book_folder, scene_breakdown or "")

        parts = [
            {
                "name": "Header",
                "heading": f"# Context Packet: {slug}",
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- **Draft File:** `{draft_path}`\n- **Task:** `draft-prose`\n- **Purpose:** Context packet optimized for drafting chapter prose.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Compressed Style Lock", "heading": "## Compressed Style Lock", "body": COMPRESSED_STYLE_LOCK, "limit": 0, "critical": True},
            {"name": "Source Chapter Anchor", "heading": "## Source Chapter Anchor", "body": compress_text(source_section), "limit": 700, "critical": False},
            {"name": "Chapter Summary", "heading": "## Chapter Summary", "body": compress_text(chapter_summary), "limit": 450, "critical": False},
            {"name": "Relevant Rulebook Facts", "heading": "## Relevant Rulebook Facts", "body": compress_text(rulebook_excerpt), "limit": 900, "critical": False},
            {"name": "Relevant Research Facts", "heading": "## Relevant Research Facts", "body": compress_text(research_excerpt), "limit": 600, "critical": False},
            {"name": "Mood And Tone Summary", "heading": "## Mood And Tone Summary", "body": compress_text(mood_lock), "limit": 450, "critical": False},
            {"name": "Pacing Guidance", "heading": "## Pacing Guidance", "body": compress_text(pacing_guidance), "limit": 300, "critical": False},
            {"name": "Prior Continuity Out", "heading": "## Prior Continuity Out", "body": compress_text(prior_cont), "limit": 450, "critical": False},
            {"name": "Scene Breakdown", "heading": "## Scene Breakdown", "body": compress_text(scene_breakdown or f"MISSING: {scene_breakdown_file.name}"), "limit": 2200, "critical": True},
        ]
        
    elif task == "continuity-check":
        prior_cont = prior_continuity(book_folder, slug)
        next_cont = next_continuity_need(book_folder, slug)
        
        snapshot_path = book_folder / "canon" / "state" / "snapshot.yml"
        if snapshot_path.exists():
            snapshot_content = snapshot_path.read_text(encoding="utf-8")
        else:
            old_state = book_folder / "world-state.json"
            snapshot_content = old_state.read_text(encoding="utf-8") if old_state.exists() else "No canon snapshot or world state exists."
        
        parts = [
            {
                "name": "Header",
                "heading": f"# Context Packet: {slug}",
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- **Task:** `continuity-check`\n- **Purpose:** Context packet optimized for checking continuity and tracking state shifts.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Chapter Content", "heading": "## Chapter Content", "body": f"Draft:\n{draft_content or 'No draft yet.'}\n\nScene Breakdown:\n{scene_breakdown or 'No scene breakdown yet.'}", "limit": 1500, "critical": True},
            {"name": "Prior Continuity Out", "heading": "## Prior Continuity Out", "body": compress_text(prior_cont), "limit": 450, "critical": True},
            {"name": "Next Continuity Need", "heading": "## Next Continuity Need", "body": compress_text(next_cont), "limit": 350, "critical": True},
            {"name": "Canon Snapshot", "heading": "## Canon Snapshot", "body": compress_text(snapshot_content), "limit": 1000, "critical": False},
        ]

    elif task == "extract-memory":
        extraction_schema = """You must extract character status, locations, inventory changes, and unresolved stakes from the draft, and format it exactly as a continuity-out.md proposal.

Format requirement:
```yaml
characters:
  <character_id>:
    status: <alive|injured|dead|absent>
    location: <location_id>
    inventory:
      - <item_id> (current list of carried items)
    secrets_revealed:
      - "..."
    relationships:
      - subject: <character_id>
        relation: <relation_desc>
        object: <character_id>

unresolved_stakes:
  - "..."
next_chapter_needs:
  - "..."
```"""
        parts = [
            {
                "name": "Header",
                "heading": f"# Context Packet: {slug}",
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- **Task:** `extract-memory`\n- **Purpose:** Context packet optimized for extracting canon mutations and state updates.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Memory Extraction Schema", "heading": "## Memory Extraction Schema", "body": extraction_schema, "limit": 0, "critical": True},
            {"name": "Chapter Draft", "heading": "## Chapter Draft", "body": draft_content or "No draft yet.", "limit": 2000, "critical": True},
        ]

    elif task == "revise-style":
        style_guide_path = Path(".agents/skills/western-manuscript-style/references/style-lock.md")
        if style_guide_path.exists():
            style_guide = style_guide_path.read_text(encoding="utf-8")
        else:
            style_guide = f"Detailed Style Lock rules: {COMPRESSED_STYLE_LOCK}"
            
        parts = [
            {
                "name": "Header",
                "heading": f"# Context Packet: {slug}",
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- **Task:** `revise-style`\n- **Purpose:** Context packet optimized for revising style-lock compliance.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Style Guide", "heading": "## Style Guide", "body": style_guide, "limit": 1200, "critical": True},
            {"name": "Chapter Draft", "heading": "## Chapter Draft", "body": draft_content or "No draft yet.", "limit": 2000, "critical": True},
        ]

    elif task == "validate-change":
        validation_report = ""
        try:
            from bookforge.core import validators as context_validator
            chapters = context_validator.discover_chapters(book_folder)
            target_ch = [c for c in chapters if c.slug == slug]
            if target_ch:
                phase_sections = context_validator.parse_phase_chapters(book_folder)
                report = context_validator.validate_chapter(target_ch[0], phase_sections)
                validation_report = context_validator.render_report([report])
            else:
                validation_report = f"No chapter folders or draft found for {slug}."
        except Exception as e:
            validation_report = f"Validator error: {e}"

        beats_path = folder / "beats.md"
        beats_content = read_optional(beats_path)

        parts = [
            {
                "name": "Header",
                "heading": f"# Context Packet: {slug}",
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- **Task:** `validate-change`\n- **Purpose:** Context packet optimized for reviewing validator outputs.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Validation Results", "heading": "## Validation Results", "body": validation_report, "limit": 1500, "critical": True},
            {"name": "Staging Elements", "heading": "## Staging Elements", "body": f"Proposal:\n{scene_breakdown or 'No proposal.'}\n\nBeats:\n{beats_content or 'No beats.'}\n\nDraft:\n{draft_content or 'No draft.'}", "limit": 2500, "critical": False},
        ]

    else:
        # Default all / legacy monolithic context packet
        chapter_summary = extract_heading_section(summaries, slug) or "MISSING: chapter summary section."
        source_section = extract_heading_section(source_text, slug) or "MISSING: source chapter section."
        mood_lock = read_optional(book_folder / "mood-lock.md") or "MISSING: mood-lock.md"
        rulebook_excerpt = relevant_rulebook_excerpt(book_folder, slug, scene_breakdown)
        pacing_guidance = pacing_excerpt(book_folder, slug)
        prior_cont = prior_continuity(book_folder, slug)
        next_cont = next_continuity_need(book_folder, slug)
        research_excerpt = relevant_research_excerpt(book_folder, scene_breakdown or "")

        parts = [
            {
                "name": "Header",
                "heading": f"# Context Packet: {slug}",
                "body": f"- **Book Folder:** `{book_folder}`\n- **Source File:** `{src}`\n- **Chapter Folder:** `{folder}`\n- **Draft File:** `{draft_path}`\n- **Purpose:** Compact source bundle for chapter-level manuscript work.\n\n## Prompt Mode Use\n- Use this packet for `drafting`, `repair`, `style`, `validation`, and `expansion` work on this chapter.\n- Do not load the full manuscript or full rulebook unless final review or source rebuilding requires it.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Compressed Style Lock", "heading": "## Compressed Style Lock", "body": COMPRESSED_STYLE_LOCK, "limit": 0, "critical": True},
            {"name": "Source Chapter Anchor", "heading": "## Source Chapter Anchor", "body": compress_text(source_section), "limit": 700, "critical": False},
            {"name": "Chapter Summary", "heading": "## Chapter Summary", "body": compress_text(chapter_summary), "limit": 450, "critical": False},
            {"name": "Relevant Rulebook Facts", "heading": "## Relevant Rulebook Facts", "body": compress_text(rulebook_excerpt), "limit": 900, "critical": False},
            {"name": "Relevant Research Facts", "heading": "## Relevant Research Facts", "body": compress_text(research_excerpt), "limit": 600, "critical": False},
            {"name": "Mood And Tone Summary", "heading": "## Mood And Tone Summary", "body": compress_text(mood_lock), "limit": 450, "critical": False},
            {"name": "Pacing Guidance", "heading": "## Pacing Guidance", "body": compress_text(pacing_guidance), "limit": 300, "critical": False},
            {"name": "Prior Continuity Out", "heading": "## Prior Continuity Out", "body": compress_text(prior_cont), "limit": 450, "critical": False},
            {"name": "Next Continuity Need", "heading": "## Next Continuity Need", "body": compress_text(next_cont), "limit": 350, "critical": False},
            {"name": "Scene Breakdown", "heading": "## Scene Breakdown", "body": compress_text(scene_breakdown or f"MISSING: {scene_breakdown_file.name}"), "limit": 2200, "critical": True},
            {
                "name": "Agent Checkpoint",
                "heading": "## Agent Checkpoint",
                "body": "- **Source Used:**\n- **Mode:**\n- **Changes Made:**\n- **Risks:**\n- **Next Action:**\n- **Stop/Continue:**\n",
                "limit": 0,
                "critical": True
            },
        ]

    # Enforce token budget by trimming
    budget = TASK_BUDGETS.get(task, 8000)
    
    def get_rendered(part_list):
        rendered_sections = []
        for part in part_list:
            hdr = part["heading"].strip()
            body = part["body"].strip()
            if body:
                rendered_sections.append(f"{hdr}\n\n{body}")
            else:
                rendered_sections.append(hdr)
        return "\n\n".join(rendered_sections)

    current_text = get_rendered(parts)
    current_tokens = estimate_tokens(current_text)

    if current_tokens > budget:
        import sys
        print(
            f"[Warning: context-packet.md rendering for task '{task}' exceeds budget of {budget} tokens "
            f"(estimated {current_tokens}). Trimming non-critical sections...]",
            file=sys.stderr
        )
        
        for part in parts:
            if not part["critical"] and part["limit"] > 0:
                new_limit = max(50, int(part["limit"] * 0.3))
                part["body"] = word_excerpt(part["body"], new_limit)
                part["limit"] = new_limit

        current_text = get_rendered(parts)
        current_tokens = estimate_tokens(current_text)
        
        if current_tokens > budget:
            parts = [p for p in parts if p["critical"]]
            current_text = get_rendered(parts)
            current_tokens = estimate_tokens(current_text)
            
            if current_tokens > budget:
                for part in parts:
                    if part["name"] not in ("Header", "Memory Extraction Schema") and part["body"]:
                        part["body"] = word_excerpt(part["body"], 250)
                current_text = get_rendered(parts)
                current_tokens = estimate_tokens(current_text)

        current_text = current_text.rstrip() + f"\n\n<!-- BUDGET_WARNING: Task packet was trimmed to fit {budget} tokens budget. -->\n"

    compressed_text = get_compression_backend().compress(current_text)
    return compressed_text.rstrip() + "\n"


def load_subgenre_rules(book_folder: Path) -> str:
    try:
        world_state = world_module.load_world_state(book_folder)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
        world_state = {}
    genre = world_state.get("genre", "western").lower()
    subgenre = world_state.get("subgenre", "classic").lower()
    
    import yaml
    config_path = Path(__file__).resolve().parent.parent / "genre_packs" / genre / f"{genre}_subgenre_config.yaml"
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
        
        prompt_blocks_path = Path(__file__).resolve().parent.parent / "genre_packs" / genre / f"{genre}_prompt_blocks.md"
        if prompt_blocks_path.exists():
            prompt_text = prompt_blocks_path.read_text(encoding="utf-8")
            rules.append(f"\n{prompt_text}")
            
        return "\n".join(rules)
    except (yaml.YAMLError, OSError, UnicodeDecodeError, KeyError, AttributeError) as e:
        return f"\n[Error loading subgenre rules: {e}]\n"


def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Build a compact chapter context packet.")
    parser.add_argument("book_folder", help="Book folder such as books/book-example.")
    parser.add_argument("--chapter", required=True, help="Chapter slug such as chapter-01 or epilogue.")
    parser.add_argument("--task", default="all", help="Task-specific context packet type")
    args = parser.parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    try:
        packet = render_packet(book_folder, args.chapter, args.task)
        folder = chapter_folder(book_folder, args.chapter)
        output_path = folder / "context-packet.md"
        output_path.write_text(packet, encoding="utf-8")
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {output_path}")
    return 0

