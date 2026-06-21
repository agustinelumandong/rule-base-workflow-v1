"""Canon mutation operations: legacy migration, chapter event application, continuity parsing."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from bookforge.core.canon.io import (
    save_yaml_file,
    get_entities_dir,
    get_events_dir,
    load_yaml_file,
)
from bookforge.core.canon.fold import fold_canon


def apply_chapter_event(book_folder: Path, chapter_id: str, change_data: dict) -> None:
    """Safely append a new chapter event and rebuild snapshot."""
    events_dir = get_events_dir(book_folder)
    events_dir.mkdir(parents=True, exist_ok=True)

    match = re.search(r"chapter[-_](\d+)", chapter_id, re.I)
    ch_num = int(match.group(1)) if match else 1

    event_file = events_dir / f"{chapter_id}.event.yml"
    save_yaml_file(event_file, {
        "chapter": ch_num,
        "events": change_data.get("events", [])
    })
    fold_canon(book_folder)


def parse_continuity_out_to_event(continuity_path: Path) -> dict:
    """Parse a legacy or generated continuity-out.md into a mutation event structure."""
    if not continuity_path.exists():
        return {"events": []}

    text = continuity_path.read_text(encoding="utf-8")
    events = []

    # Prefer explicit YAML blocks
    for block in re.findall(r"```yaml\s*\n(.*?)\n```", text, re.DOTALL):
        try:
            parsed = yaml.safe_load(block)
            if isinstance(parsed, dict) and "events" in parsed:
                events.extend(parsed["events"])
        except (yaml.YAMLError, ValueError, TypeError):
            pass

    # Section parser fallback
    current_section = ""
    pressures = []
    for line in text.splitlines():
        line_strip = line.strip()
        if not line_strip:
            continue
        if line_strip.startswith("##"):
            current_section = line_strip.lower()
            continue

        clean_line = line_strip.lstrip("-* ").strip()
        if not clean_line:
            continue

        if "characters" in current_section:
            match_dead = re.search(r"(\w+(?:\s+\w+)?)\s+dead", clean_line, re.I)
            if match_dead:
                events.append({
                    "type": "character_status",
                    "character_id": match_dead.group(1).lower().replace(" ", "_"),
                    "status": "dead"
                })
        elif "changes" in current_section or "locations" in current_section:
            match_travel = re.search(
                r"(\w+(?:\s+\w+)?)\s+(?:is at|traveled to|moves to|moved to)\s+([\w\s]+)",
                clean_line, re.I
            )
            if match_travel:
                events.append({
                    "type": "character_mutation",
                    "character_id": match_travel.group(1).lower().replace(" ", "_"),
                    "location": match_travel.group(2).strip().lower().replace(" ", "_").rstrip(".")
                })
        elif "unresolved" in current_section:
            pressures.append(clean_line)

    if pressures:
        events.append({"type": "stakes", "unresolved_pressure": pressures})

    return {"events": events}


def migrate_legacy_book(book_folder: Path) -> None:
    """Migrate legacy world-state.json, relationships.json to event-sourced structures.

    Creates canon/entities/* and initial events. Idempotent.
    """
    entities_dir = get_entities_dir(book_folder)
    events_dir = get_events_dir(book_folder)
    entities_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)

    # Load legacy world-state.json
    legacy_chars: dict = {}
    legacy_locs: list = []
    world_state_path = book_folder / "world-state.json"
    if world_state_path.exists():
        try:
            ws = json.loads(world_state_path.read_text(encoding="utf-8"))
            legacy_chars = ws.get("characters", {})
            legacy_locs = ws.get("locations", [])
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass

    # Load legacy relationships
    legacy_rels: list = []
    relationships_path = book_folder / "relationships.json"
    if relationships_path.exists():
        try:
            legacy_rels = json.loads(relationships_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass

    char_data: dict = {"characters": {}}
    alias_data: dict = {"aliases": {}}

    # Build characters.yml and aliases.yml
    for name, info in legacy_chars.items():
        cid = name.lower().replace(" ", "_")
        c_rels: dict = {}
        rels_list = legacy_rels.values() if isinstance(legacy_rels, dict) else legacy_rels
        for rel in rels_list:
            if not isinstance(rel, dict):
                continue
            if rel.get("subject", "").lower() == cid:
                c_rels[rel.get("object", "").lower()] = rel.get("relation", "")

        if cid in ("tex_cade", "tex", "harlan"):
            tier = "main"
        elif cid in ("darin", "mara_vale"):
            tier = "major_supporting"
        else:
            tier = "minor_named"

        char_data["characters"][cid] = {
            "canonical": info.get("canonical") or name.capitalize(),
            "tier": tier,
            "role": info.get("role", "protagonist" if tier == "main" else "ally"),
            "physical_marker": "unspecified",
            "voice": "clipped",
            "pov": "allowed" if tier == "main" else "disallowed",
            "first_seen": "chapter-01",
            "relationships": c_rels,
            "secrets": []
        }
        alias_data["aliases"][cid.replace("_", " ")] = cid
        alias_data["aliases"][name.lower()] = cid

    save_yaml_file(entities_dir / "characters.yml", char_data)

    # Build locations.yml
    loc_data: dict = {"locations": {}}
    for loc_name in legacy_locs:
        lid = loc_name.lower().replace(" ", "_")
        loc_data["locations"][lid] = {
            "canonical": loc_name.capitalize(),
            "function": "narrative point",
            "description": f"The {loc_name} setting."
        }
        alias_data["aliases"][loc_name.lower()] = lid
    save_yaml_file(entities_dir / "locations.yml", loc_data)

    # Build objects.yml from character inventories
    obj_data: dict = {"objects": {}}
    for name, info in legacy_chars.items():
        for item in info.get("inventory", []):
            oid = item.lower().replace(" ", "_")
            if oid not in obj_data["objects"]:
                obj_data["objects"][oid] = {
                    "canonical": item.replace("_", " ").capitalize(),
                    "type": "weapon" if any(k in oid for k in ("colt", "rifle", "gun")) else "item"
                }
                alias_data["aliases"][item.lower().replace("_", " ")] = oid
    save_yaml_file(entities_dir / "objects.yml", obj_data)
    save_yaml_file(entities_dir / "aliases.yml", alias_data)

    # Create initial chapter-01.event.yml from legacy states
    event_yaml_path = events_dir / "chapter-01.event.yml"
    if not event_yaml_path.exists():
        init_events = []
        for name, info in legacy_chars.items():
            cid = name.lower().replace(" ", "_")
            loc = info.get("location")
            inv = info.get("inventory", [])
            init_events.append({
                "type": "character_mutation",
                "character_id": cid,
                "location": loc.lower().replace(" ", "_") if loc else None,
                "inventory_added": [item.lower().replace(" ", "_") for item in inv]
            })
            for item in inv:
                oid = item.lower().replace(" ", "_")
                init_events.append({"type": "object_mutation", "object_id": oid, "holder": cid})

        save_yaml_file(event_yaml_path, {"chapter": 1, "events": init_events})

    fold_canon(book_folder)
