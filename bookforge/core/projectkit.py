"""Project Kit builder for provider-ready context folders."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from bookforge.core.canon.io import load_yaml_file, get_state_dir
from bookforge.core.packet.helpers import read_optional, chapter_slugs, chapter_sort_key
from bookforge.core.packet.compress import COMPRESSED_STYLE_LOCK
from bookforge.core.queue import load_queue, build_queue
from bookforge.core.research_cache import ResearchCacheEntry
from bookforge.core.characters import load_character_profiles
from bookforge.core.scanner import source_path

PROVIDERS = ("chatgpt", "claude", "gemini", "generic")

PROVIDER_INSTRUCTIONS = {
    "chatgpt": (
        "Prefer the active scene packet over general project memory.\n"
        "Do not use stale archived scene packets as current instructions."
    ),
    "claude": (
        "Prioritize literary continuity, restraint, subtext, and emotional logic."
    ),
    "gemini": (
        "Prioritize consistency across long context and flag ambiguity only if explicitly asked."
    ),
    "generic": "",
}


def project_kit_folder(book_folder: Path, provider: str) -> Path:
    return book_folder / "project-kits" / provider


def _read(path: Path) -> str:
    return read_optional(path)


def _load_snapshot(book_folder: Path) -> dict:
    snap = get_state_dir(book_folder) / "snapshot.yml"
    if snap.exists():
        return load_yaml_file(snap) or {}
    return {}


def render_project_instructions(book_folder: Path, provider: str) -> str:
    lines = [
        "# BookForge Provider-Web Writing Lane",
        "",
        "You are the prose generator only.",
        "Use the project files and the active scene packet.",
        "Do not invent canon.",
        "Do not perform research.",
        "Do not validate facts.",
        "Do not explain your process.",
        "Return only the requested prose or patch replacement.",
        "",
        "BookForge is the source of truth.",
        "If the packet conflicts with older project context, obey the active packet.",
        "If a detail is missing, leave it implicit rather than inventing new canon.",
        "",
        "---",
        "",
        f"## Provider Notes ({provider})",
        "",
        PROVIDER_INSTRUCTIONS.get(provider, ""),
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_story_bible(book_folder: Path) -> str:
    snapshot = _load_snapshot(book_folder)
    rulebook = _read(book_folder / "rulebook.md")
    phase0 = _read(source_path(book_folder) or Path("/dev/null"))

    lines = ["# Story Bible (Compiled)", ""]

    # Premise from rulebook or phase-0
    lines.append("## Premise")
    lines.append("")
    premise_source = rulebook or phase0
    if premise_source:
        # Take first ~20 lines as premise excerpt
        excerpt = "\n".join(premise_source.splitlines()[:20])
        lines.append(excerpt)
    else:
        lines.append("No premise source found.")
    lines.append("")

    # Characters from snapshot
    chars = snapshot.get("characters", {})
    if chars:
        lines.append("## Major Characters")
        lines.append("")
        for cid, cdata in chars.items():
            name = cdata.get("canonical", cid)
            status = cdata.get("status", "alive")
            location = cdata.get("location", "unknown")
            lines.append(f"- **{name}** — {status}, at {location}")
        lines.append("")

    # Locations
    locs = snapshot.get("locations", {})
    if locs:
        lines.append("## Locations")
        lines.append("")
        for lid, ldata in locs.items():
            name = ldata.get("canonical", lid)
            lines.append(f"- {name}")
        lines.append("")

    # Unresolved pressure
    pressure = snapshot.get("unresolved_pressure", [])
    if pressure:
        lines.append("## Core Conflict / Unresolved Pressure")
        lines.append("")
        for p in pressure:
            lines.append(f"- {p}")
        lines.append("")

    # World rules from rulebook
    if rulebook:
        lines.append("## World Rules")
        lines.append("")
        lines.append("See rulebook.md for full constraints.")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_character_states(book_folder: Path) -> str:
    snapshot = _load_snapshot(book_folder)
    chars = snapshot.get("characters", {})

    lines = ["# Character States", ""]

    if not chars:
        lines.append("No character data in canon snapshot.")
        return "\n".join(lines).rstrip() + "\n"

    for cid, cdata in chars.items():
        name = cdata.get("canonical", cid)
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"- **Status:** {cdata.get('status', 'alive')}")
        lines.append(f"- **Location:** {cdata.get('location', 'unknown')}")
        lines.append(f"- **Emotional State:** {cdata.get('emotional_state', 'neutral')}")

        inv = cdata.get("inventory", [])
        if inv:
            lines.append(f"- **Inventory:** {', '.join(inv)}")

        injuries = cdata.get("injuries", {})
        active_injuries = {k: v for k, v in injuries.items() if v.get("status") == "active"}
        if active_injuries:
            inj_list = [f"{v.get('description', k)} ({v.get('severity', 'unknown')})" for k, v in active_injuries.items()]
            lines.append(f"- **Injuries:** {'; '.join(inj_list)}")

        secrets = cdata.get("secrets", [])
        if secrets:
            lines.append(f"- **Known Secrets:** {'; '.join(secrets)}")

        rels = cdata.get("relationships", {})
        if rels:
            rel_lines = [f"{rid}: {rval}" for rid, rval in rels.items()]
            lines.append(f"- **Relationships:** {'; '.join(rel_lines)}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_timeline(book_folder: Path) -> str:
    snapshot = _load_snapshot(book_folder)
    chapters = chapter_slugs(book_folder)

    lines = ["# Timeline (Compiled)", ""]

    lines.append("## Chapter Sequence")
    lines.append("")
    for slug in chapters:
        lines.append(f"- {slug}")
    lines.append("")

    # Current locations from snapshot
    chars = snapshot.get("characters", {})
    if chars:
        lines.append("## Current Character Locations")
        lines.append("")
        for cid, cdata in chars.items():
            name = cdata.get("canonical", cid)
            loc = cdata.get("location", "unknown")
            lines.append(f"- {name}: {loc}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_style_rules(book_folder: Path) -> str:
    mood_lock = _read(book_folder / "mood-lock.md")
    rulebook = _read(book_folder / "rulebook.md")

    lines = ["# Style Rules", ""]

    lines.append("## Compressed Style Lock")
    lines.append("")
    lines.append(COMPRESSED_STYLE_LOCK)
    lines.append("")

    if mood_lock:
        lines.append("## Mood Lock")
        lines.append("")
        lines.append(mood_lock)
        lines.append("")

    # Extract dialogue rules from rulebook
    if rulebook:
        lines.append("## Rulebook Excerpts")
        lines.append("")
        in_dialogue = False
        dialogue_lines = []
        for line in rulebook.splitlines():
            if "dialogue" in line.lower() and line.startswith("#"):
                in_dialogue = True
                dialogue_lines.append(line)
            elif in_dialogue and line.startswith("#") and "dialogue" not in line.lower():
                break
            elif in_dialogue:
                dialogue_lines.append(line)
        if dialogue_lines:
            lines.append("\n".join(dialogue_lines))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_hard_guardrails(book_folder: Path) -> str:
    rulebook = _read(book_folder / "rulebook.md")

    lines = ["# Hard Guardrails", ""]
    lines.append("These rules are absolute. Violating them invalidates the output.")
    lines.append("")

    lines.append("## Forbidden Reveals")
    lines.append("- Do not reveal endings or major twists not established in the active packet.")
    lines.append("")

    lines.append("## Forbidden Inventions")
    lines.append("- Do not invent canon facts not present in the project files.")
    lines.append("- Do not introduce new characters, locations, or objects without explicit packet instruction.")
    lines.append("")

    lines.append("## Canon Mutation Rules")
    lines.append("- Only BookForge may update canon via `bf apply change`.")
    lines.append("- Never modify canon snapshot or event files directly.")
    lines.append("")

    lines.append("## Language Constraints")
    lines.append("- No modern or clinical phrasing.")
    lines.append("- No unsupported technology or anachronisms.")
    lines.append("- No POV violation.")
    lines.append("")

    lines.append("## Scene Constraints")
    lines.append("- Do not change required scene outcomes specified in the packet.")
    lines.append("- Do not skip required beats.")
    lines.append("")

    if rulebook:
        # Extract guardrail-like sections
        in_guards = False
        guard_lines = []
        for line in rulebook.splitlines():
            lower = line.lower()
            if any(kw in lower for kw in ("forbidden", "must not", "never", "do not", "lock")):
                in_guards = True
            if in_guards:
                guard_lines.append(line)
                if line.startswith("#") and "forbidden" not in lower and "must not" not in lower and "lock" not in lower and len(guard_lines) > 2:
                    guard_lines.pop()
                    in_guards = False
        if guard_lines:
            lines.append("## From Rulebook")
            lines.append("")
            lines.append("\n".join(guard_lines[:30]))
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_world_reality_rules(book_folder: Path) -> str:
    cache_dir = book_folder / "research_cache"
    lines = ["# World Reality Rules", ""]
    lines.append("Only accepted research facts are included.")
    lines.append("")

    if not cache_dir.exists():
        lines.append("No research cache found.")
        return "\n".join(lines).rstrip() + "\n"

    entries: list[dict] = []
    for yml_file in sorted(cache_dir.rglob("*.yml")):
        try:
            data = yaml.safe_load(yml_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("canon_status") == "accepted":
                entries.append(data)
        except Exception:
            pass

    if not entries:
        lines.append("No accepted research entries found.")
        return "\n".join(lines).rstrip() + "\n"

    # Group by category
    by_category: dict[str, list[dict]] = {}
    for entry in entries:
        cat = entry.get("category", "general")
        by_category.setdefault(cat, []).append(entry)

    for cat in sorted(by_category):
        lines.append(f"## {cat.title()}")
        lines.append("")
        for entry in by_category[cat]:
            subject = entry.get("subject", entry.get("key", "unknown"))
            answer = entry.get("answer", "")
            provenance = entry.get("source_backend", "manual")
            source_key = entry.get("key", "")
            lines.append(f"### {subject.title()}")
            lines.append(f"Status: accepted")
            lines.append(f"Use: {answer[:200]}")
            lines.append(f"Source: research_cache/{source_key}.yml")
            lines.append(f"Backend: {provenance}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_current_outline(book_folder: Path) -> str:
    src = source_path(book_folder)
    lines = ["# Current Outline", ""]

    if src and src.exists():
        content = src.read_text(encoding="utf-8")
        # Extract first 60 lines as outline summary
        excerpt = "\n".join(content.splitlines()[:60])
        lines.append(excerpt)
    else:
        lines.append("No source outline found.")

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_previous_chapter_summaries(book_folder: Path) -> str:
    summaries = _read(book_folder / "chapter-summaries.md")
    lines = ["# Previous Chapter Summaries", ""]

    if summaries:
        lines.append(summaries)
    else:
        lines.append("No chapter summaries found.")

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_unresolved_hooks(book_folder: Path) -> str:
    snapshot = _load_snapshot(book_folder)
    lines = ["# Unresolved Hooks", ""]

    pressure = snapshot.get("unresolved_pressure", [])
    if pressure:
        lines.append("## Open Promises / Unresolved Pressure")
        lines.append("")
        for p in pressure:
            lines.append(f"- {p}")
        lines.append("")

    invariants = snapshot.get("chapter_invariants", [])
    if invariants:
        lines.append("## Chapter Invariants")
        lines.append("")
        for inv in invariants:
            lines.append(f"- {inv}")
        lines.append("")

    # Extract unknowns from rulebook
    rulebook = _read(book_folder / "rulebook.md")
    if rulebook:
        in_unknowns = False
        unknown_lines = []
        for line in rulebook.splitlines():
            if "unknown" in line.lower() and line.startswith("#"):
                in_unknowns = True
            if in_unknowns:
                unknown_lines.append(line)
                if line.startswith("#") and "unknown" not in line.lower() and len(unknown_lines) > 2:
                    unknown_lines.pop()
                    in_unknowns = False
        if unknown_lines:
            lines.append("## Unknowns from Rulebook")
            lines.append("")
            lines.append("\n".join(unknown_lines[:30]))
            lines.append("")

    if not pressure and not invariants and not (rulebook and "unknown" in rulebook.lower()):
        lines.append("No unresolved hooks found.")

    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_generation_queue(book_folder: Path) -> str:
    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])

    lines = ["# Generation Queue", ""]

    if not scenes:
        lines.append("No scenes in queue. Run `bf queue build` first.")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    completed_statuses = {"clean", "validation_passed", "committed"}
    active_statuses = {"ready_for_generation", "generation_packet_ready", "ready_for_validation",
                       "validation_failed", "ready_for_patch", "patch_packet_ready"}

    active = []
    done = []
    pending = []

    status_map = {s["scene_key"]: s["status"] for s in scenes}

    for s in scenes:
        key = s["scene_key"]
        status = s["status"]
        deps = s.get("dependencies", [])
        deps_met = all(status_map.get(d) in completed_statuses for d in deps)

        if status in completed_statuses:
            done.append(s)
        elif status in active_statuses and deps_met:
            active.append(s)
        else:
            pending.append(s)

    if active:
        lines.append("## Active")
        lines.append("")
        for s in active:
            lines.append(f"- {s['scene_key']} — {s['status']}")
        lines.append("")

    if done:
        lines.append("## Done")
        lines.append("")
        for s in done:
            lines.append(f"- {s['scene_key']} — {s['status']}")
        lines.append("")

    if pending:
        lines.append("## Pending")
        lines.append("")
        for s in pending:
            dep_str = f" (waiting on: {', '.join(s.get('dependencies', []))})" if s.get("dependencies") else ""
            lines.append(f"- {s['scene_key']} — {s['status']}{dep_str}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _find_active_scene(queue_data: dict) -> str | None:
    """Return the scene_key of the active scene, or None."""
    scenes = queue_data.get("scenes", [])
    active_statuses = {"generation_packet_ready", "ready_for_validation",
                       "validation_failed", "ready_for_patch", "patch_packet_ready"}

    for s in scenes:
        if s["status"] in active_statuses:
            return s["scene_key"]
    return None


def _scene_key_to_filename(scene_key: str, suffix: str) -> str:
    """Convert chapter-10/scene-01 to chapter-10_scene-01_<suffix>."""
    safe = scene_key.replace("/", "_")
    return f"{safe}_{suffix}"


# Statuses where only the generation packet is relevant
_GENERATION_STATUSES = {"ready_for_generation", "generation_packet_ready", "ready_for_validation"}

# Statuses where only the patch packet is relevant
_REPAIR_STATUSES = {"validation_failed", "ready_for_patch", "patch_packet_ready"}


def sync_active_and_archive_packets(book_folder: Path, provider: str) -> None:
    """Copy active scene packet to active/, completed to archive/.

    Status-aware:
      - generation/ready_for_validation: only generation packet in active/
      - validation_failed/patch: only patch packet in active/
      - completed: move both to archive/
    """
    kit_dir = project_kit_folder(book_folder, provider)
    active_dir = kit_dir / "active"
    archive_dir = kit_dir / "archive"

    active_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])
    completed_statuses = {"clean", "validation_passed", "committed"}

    active_scene = _find_active_scene(queue_data)

    for s in scenes:
        key = s["scene_key"]
        status = s["status"]
        packet_path = book_folder / s.get("packet_path", "")
        patch_path = book_folder / s.get("patch_packet_path", "")

        if key == active_scene:
            if status in _GENERATION_STATUSES:
                if packet_path.exists():
                    dest = active_dir / _scene_key_to_filename(key, "generation-packet.md")
                    shutil.copy2(packet_path, dest)
                # Remove stale patch packet from active if scene is in generation state
                stale_patch = active_dir / _scene_key_to_filename(key, "patch-packet.md")
                if stale_patch.exists():
                    stale_patch.unlink()
            elif status in _REPAIR_STATUSES:
                if patch_path.exists():
                    dest = active_dir / _scene_key_to_filename(key, "patch-packet.md")
                    shutil.copy2(patch_path, dest)
                # Remove stale generation packet from active if scene is in repair state
                stale_gen = active_dir / _scene_key_to_filename(key, "generation-packet.md")
                if stale_gen.exists():
                    stale_gen.unlink()

        elif status in completed_statuses:
            if packet_path.exists():
                dest = archive_dir / _scene_key_to_filename(key, "generation-packet.md")
                shutil.copy2(packet_path, dest)
            if patch_path.exists():
                dest = archive_dir / _scene_key_to_filename(key, "patch-packet.md")
                shutil.copy2(patch_path, dest)


def build_project_kit(book_folder: Path, provider: str) -> Path:
    """Build the complete project kit folder for a given provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Must be one of: {', '.join(PROVIDERS)}")

    kit_dir = project_kit_folder(book_folder, provider)
    kit_dir.mkdir(parents=True, exist_ok=True)

    # Ensure queue is built
    build_queue(book_folder)

    files = {
        "00_project_instructions.md": render_project_instructions(book_folder, provider),
        "01_story_bible_compiled.md": render_story_bible(book_folder),
        "02_character_states.md": render_character_states(book_folder),
        "03_timeline_compiled.md": render_timeline(book_folder),
        "04_style_rules.md": render_style_rules(book_folder),
        "05_hard_guardrails.md": render_hard_guardrails(book_folder),
        "06_world_reality_rules.md": render_world_reality_rules(book_folder),
        "07_current_outline.md": render_current_outline(book_folder),
        "08_previous_chapter_summaries.md": render_previous_chapter_summaries(book_folder),
        "09_unresolved_hooks.md": render_unresolved_hooks(book_folder),
        "10_generation_queue.md": render_generation_queue(book_folder),
    }

    for filename, content in files.items():
        (kit_dir / filename).write_text(content, encoding="utf-8")

    # Sync active/archive packets
    sync_active_and_archive_packets(book_folder, provider)

    return kit_dir
