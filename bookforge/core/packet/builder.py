"""Context packet builder orchestrator and budget controls."""

from __future__ import annotations

import sys
from pathlib import Path

from bookforge.core.scanner import source_path
from bookforge.core.packet.compress import compress_text, COMPRESSED_STYLE_LOCK
from bookforge.core.packet.helpers import (
    read_optional,
    word_excerpt,
    extract_heading_section,
    chapter_folder,
    chapter_draft_path,
)
from bookforge.core.packet.excerpt import (
    relevant_rulebook_excerpt_from_text,
    relevant_rulebook_excerpt,
    relevant_character_profiles,
    prior_continuity,
    next_continuity_need,
    pacing_excerpt,
    relevant_research_excerpt,
)

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


def review_focus_notes() -> str:
    return "\n".join(
        [
            "- Carry forward source-supported experience, wound, debt, guilt, duty, or pressure when it should affect this chapter's choices.",
            "- Dramatize planning, bonding, friction, proof, and moral-decision conversations when the reader needs to hear the exchange.",
            "- Bridge major travel, route, message, or time movement with physical work: scouting, weather, fatigue, repairs, camp movement, sign reading, or terrain hazards.",
            "- Check frontier mechanics for wagons, ferries, horses, firearms, wounds, tracking clues, legal papers, brands, ledgers, and terrain.",
            "- If betrayal, confession, witness knowledge, planted proof, route timing, or a villain mistake lacks setup/payoff support, mark it `UNKNOWN` instead of inventing it.",
        ]
    )


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
        character_profiles = relevant_character_profiles(book_folder, scene_breakdown or "")
        pacing_guidance = pacing_excerpt(book_folder, slug)
        prior_cont = prior_continuity(book_folder, slug)
        research_excerpt = relevant_research_excerpt(book_folder, scene_breakdown or "")

        parts = [
            {
                "name": "Header",
                "heading": f"# Context Packet: {slug}",
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- **Draft File:** `{draft_path}`\n- Task: `draft-prose`\n- **Purpose:** Context packet optimized for drafting chapter prose.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Compressed Style Lock", "heading": "## Compressed Style Lock", "body": COMPRESSED_STYLE_LOCK, "limit": 0, "critical": True},
            {"name": "Source Chapter Anchor", "heading": "## Source Chapter Anchor", "body": compress_text(source_section), "limit": 700, "critical": False},
            {"name": "Chapter Summary", "heading": "## Chapter Summary", "body": compress_text(chapter_summary), "limit": 450, "critical": False},
            {"name": "Relevant Rulebook Facts", "heading": "## Relevant Rulebook Facts", "body": compress_text(rulebook_excerpt), "limit": 900, "critical": False},
            {"name": "Relevant Character Profiles", "heading": "## Relevant Character Profiles", "body": compress_text(character_profiles), "limit": 700, "critical": False, "omit_if_empty": True},
            {"name": "Relevant Research Facts", "heading": "## Relevant Research Facts", "body": compress_text(research_excerpt), "limit": 600, "critical": False},
            {"name": "Mood And Tone Summary", "heading": "## Mood And Tone Summary", "body": compress_text(mood_lock), "limit": 450, "critical": False},
            {"name": "Pacing Guidance", "heading": "## Pacing Guidance", "body": compress_text(pacing_guidance), "limit": 300, "critical": False},
            {"name": "Prior Continuity Out", "heading": "## Prior Continuity Out", "body": compress_text(prior_cont), "limit": 450, "critical": False},
            {"name": "Review Focus", "heading": "## Review Focus", "body": review_focus_notes(), "limit": 0, "critical": True},
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
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- Task: `continuity-check`\n- **Purpose:** Context packet optimized for checking continuity and tracking state shifts.\n",
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
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- Task: `extract-memory`\n- **Purpose:** Context packet optimized for extracting canon mutations and state updates.\n",
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
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- Task: `revise-style`\n- **Purpose:** Context packet optimized for revising style-lock compliance.\n",
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
            from bookforge.core.issue import Severity
            chapters = context_validator.discover_chapters(book_folder)
            target_ch = [c for c in chapters if c.slug == slug]
            if target_ch:
                book_issues = context_validator.validate_required_book_file_issues(book_folder)
                book_passes = [i.message for i in book_issues if i.severity == Severity.INFO]
                book_failures = [i.message for i in book_issues if i.severity == Severity.HARD]
                book_warnings = [i.message for i in book_issues if i.severity == Severity.SOFT]
                phase_sections = context_validator.parse_phase_chapters(book_folder)
                report = context_validator.validate_chapter(target_ch[0], phase_sections)
                validation_report = context_validator.render_report(
                    book_folder,
                    book_passes,
                    book_failures,
                    book_warnings,
                    [report],
                )
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
                "body": f"- **Book Folder:** `{book_folder}`\n- **Chapter Folder:** `{folder}`\n- Task: `validate-change`\n- **Purpose:** Context packet optimized for reviewing validator outputs.\n",
                "limit": 0,
                "critical": True
            },
            {"name": "Validation Results", "heading": "## Validation Results", "body": validation_report, "limit": 1500, "critical": True},
            {"name": "Staging Elements", "heading": "## Staging Elements", "body": f"Proposal:\n{scene_breakdown or 'No proposal.'}\n\nBeats:\n{beats_content or 'No beats.'}\n\nDraft:\n{draft_content or 'No draft.'}", "limit": 2500, "critical": False},
        ]

    else:
        chapter_summary = extract_heading_section(summaries, slug) or "MISSING: chapter summary section."
        source_section = extract_heading_section(source_text, slug) or "MISSING: source chapter section."
        mood_lock = read_optional(book_folder / "mood-lock.md") or "MISSING: mood-lock.md"
        rulebook_excerpt = relevant_rulebook_excerpt(book_folder, slug, scene_breakdown)
        character_profiles = relevant_character_profiles(book_folder, scene_breakdown or "")
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
            {"name": "Relevant Character Profiles", "heading": "## Relevant Character Profiles", "body": compress_text(character_profiles), "limit": 700, "critical": False, "omit_if_empty": True},
            {"name": "Relevant Research Facts", "heading": "## Relevant Research Facts", "body": compress_text(research_excerpt), "limit": 600, "critical": False},
            {"name": "Mood And Tone Summary", "heading": "## Mood And Tone Summary", "body": compress_text(mood_lock), "limit": 450, "critical": False},
            {"name": "Pacing Guidance", "heading": "## Pacing Guidance", "body": compress_text(pacing_guidance), "limit": 300, "critical": False},
            {"name": "Prior Continuity Out", "heading": "## Prior Continuity Out", "body": compress_text(prior_cont), "limit": 450, "critical": False},
            {"name": "Next Continuity Need", "heading": "## Next Continuity Need", "body": compress_text(next_cont), "limit": 350, "critical": False},
            {"name": "Review Focus", "heading": "## Review Focus", "body": review_focus_notes(), "limit": 0, "critical": True},
            {"name": "Scene Breakdown", "heading": "## Scene Breakdown", "body": compress_text(scene_breakdown or f"MISSING: {scene_breakdown_file.name}"), "limit": 2200, "critical": True},
            {
                "name": "Agent Checkpoint",
                "heading": "## Agent Checkpoint",
                "body": "- **Source Used:**\n- **Mode:**\n- **Changes Made:**\n- **Risks:**\n- **Next Action:**\n- **Stop/Continue:**\n",
                "limit": 0,
                "critical": True
            },
        ]

    budget = TASK_BUDGETS.get(task, 8000)
    
    def get_rendered(part_list):
        rendered_states = []
        for part in part_list:
            hdr = part["heading"].strip()
            body = part["body"].strip()
            if not body and part.get("omit_if_empty"):
                continue
            if body:
                rendered_states.append(f"{hdr}\n\n{body}")
            else:
                rendered_states.append(hdr)
        return "\n\n".join(rendered_states)

    current_text = get_rendered(parts)
    current_tokens = estimate_tokens(current_text)

    if current_tokens > budget:
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

    return current_text.rstrip() + "\n"


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
        packet_content = render_packet(book_folder, args.chapter, args.task)
        folder = chapter_folder(book_folder, args.chapter)
        output_path = folder / "context-packet.md"
        output_path.write_text(packet_content, encoding="utf-8")
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {output_path}")
    return 0
