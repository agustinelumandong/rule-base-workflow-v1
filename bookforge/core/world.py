#!/usr/bin/env python3
"""BookForge World State and Physical Inventory Tracking Subsystem."""

from __future__ import annotations

import json
import re
from pathlib import Path


DEFAULT_WORLD_STATE = {
    "characters": {},
    "locations": []
}


def load_world_state(book_folder: Path) -> dict:
    """Loads world-state.json from the book folder, or initializes an empty state."""
    state_path = Path(book_folder) / "world-state.json"
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    # Initialize default
    try:
        state_path.write_text(json.dumps(DEFAULT_WORLD_STATE, indent=2), encoding="utf-8")
    except Exception:
        pass
    return json.loads(json.dumps(DEFAULT_WORLD_STATE))


def save_world_state(book_folder: Path, state: dict):
    """Saves the world state back to world-state.json."""
    state_path = Path(book_folder) / "world-state.json"
    try:
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        pass


def parse_scene_transitions(scene_text: str) -> list[dict]:
    """Extracts state transition tags from the scene text.
    
    Supported:
      - [TRAVEL: harlan from saloon to stables]
      - [TRANSFER: silver_pocket_watch from darin to harlan]
      - [GIVE: colt_45 from harlan to darin]
      - [ACQUIRE: map by harlan]
      - [LOSE: colt_45 from harlan]
      - [INJURE: darin with shoulder wound]
      - [KILL: darin]
    """
    transitions = []
    
    travel_pattern = re.compile(r"\[TRAVEL:\s*(\w+)\s+from\s+(\w+)\s+to\s+(\w+)\]", re.IGNORECASE)
    transfer_pattern = re.compile(r"\[(TRANSFER|GIVE):\s*([\w_]+)\s+from\s+(\w+)\s+to\s+(\w+)\]", re.IGNORECASE)
    acquire_pattern = re.compile(r"\[ACQUIRE:\s*([\w_]+)\s+by\s+(\w+)\]", re.IGNORECASE)
    lose_pattern = re.compile(r"\[LOSE:\s*([\w_]+)\s+from\s+(\w+)\]", re.IGNORECASE)
    injure_pattern = re.compile(r"\[INJURE:\s*(\w+)\s+with\s+([^\]]+)\]", re.IGNORECASE)
    kill_pattern = re.compile(r"\[KILL:\s*(\w+)\]", re.IGNORECASE)

    for line in scene_text.splitlines():
        # TRAVEL
        for m in travel_pattern.finditer(line):
            transitions.append({
                "type": "travel",
                "character": m.group(1).lower(),
                "from": m.group(2).lower(),
                "to": m.group(3).lower()
            })
        # TRANSFER / GIVE
        for m in transfer_pattern.finditer(line):
            transitions.append({
                "type": "transfer",
                "item": m.group(2).lower(),
                "from": m.group(3).lower(),
                "to": m.group(4).lower()
            })
        # ACQUIRE
        for m in acquire_pattern.finditer(line):
            transitions.append({
                "type": "acquire",
                "item": m.group(1).lower(),
                "character": m.group(2).lower()
            })
        # LOSE
        for m in lose_pattern.finditer(line):
            transitions.append({
                "type": "lose",
                "item": m.group(1).lower(),
                "character": m.group(2).lower()
            })
        # INJURE
        for m in injure_pattern.finditer(line):
            transitions.append({
                "type": "injure",
                "character": m.group(1).lower(),
                "detail": m.group(2).strip()
            })
        # KILL
        for m in kill_pattern.finditer(line):
            transitions.append({
                "type": "kill",
                "character": m.group(1).lower()
            })

    return transitions


def parse_scene_location(scene_header_block: str) -> str | None:
    """Extracts Location field from scene details (e.g. '* Location: stables')."""
    location_match = re.search(r"(?i)^\s*[\-\*]\s*Location:\s*(\w+)", scene_header_block, re.MULTILINE)
    if location_match:
        return location_match.group(1).lower()
    return None


def discover_scenes_from_breakdown(breakdown_path: Path) -> list[dict]:
    """Parses scene-breakdown.md into a list of scene blocks.
    
    Each scene block contains its ID, Location, and raw text content (to extract transitions).
    """
    if not breakdown_path.exists():
        return []
    
    try:
        content = breakdown_path.read_text(encoding="utf-8")
    except Exception:
        return []
    
    # Split content by ## or ### headings
    sections = re.split(r"(?m)^(?=##|###)", content)
    scenes = []
    
    for section in sections:
        if not section.strip():
            continue
        
        first_line = section.splitlines()[0]
        if "scene" not in first_line.lower():
            continue
            
        # Extract scene ID
        match = re.search(r"(?i)scene[-_ ]*(\d+|\w+)", first_line)
        if match:
            scene_id = f"scene-{match.group(1).lower()}"
        else:
            scene_id = "scene-" + re.sub(r"[^a-z0-9]+", "-", first_line.lower()).strip("-")
            
        scene_id = scene_id.replace("-combat", "")
        
        # Parse location
        location = parse_scene_location(section)
        
        # Parse transitions
        transitions = parse_scene_transitions(section)
        
        scenes.append({
            "id": scene_id,
            "title": first_line.lstrip("#").strip(),
            "location": location,
            "transitions": transitions,
            "raw_text": section
        })
        
    return scenes


def validate_scene_world_state(
    scene: dict,
    draft_text: str,
    state: dict
) -> tuple[list[str], list[str]]:
    """Validates the scene draft and transitions against the current world state.
    
    Returns (failures, warnings).
    """
    failures = []
    warnings = []
    
    # 1. Update/Verify Transitions
    for t in scene.get("transitions", []):
        t_type = t["type"]
        
        if t_type == "travel":
            char = t["character"]
            frm = t["from"]
            to = t["to"]
            
            if char in state["characters"]:
                curr_loc = state["characters"][char]["location"]
                if curr_loc != frm:
                    failures.append(
                        f"Teleportation Error: {char.capitalize()} is traveling from '{frm}' but their current location is '{curr_loc}'."
                    )
                state["characters"][char]["location"] = to
            else:
                failures.append(f"Invalid Character: '{char}' is not registered in the world state.")
                
        elif t_type == "transfer":
            item = t["item"]
            frm = t["from"]
            to = t["to"]
            
            if frm in state["characters"] and to in state["characters"]:
                inv_from = state["characters"][frm]["inventory"]
                if item not in inv_from:
                    failures.append(
                        f"Missing Inventory Item: {frm.capitalize()} tries to transfer '{item}' to {to.capitalize()} but does not possess it."
                    )
                else:
                    inv_from.remove(item)
                    state["characters"][to]["inventory"].append(item)
            else:
                failures.append(f"Invalid characters in transfer: '{frm}' or '{to}' is not registered.")
                
        elif t_type == "acquire":
            item = t["item"]
            char = t["character"]
            if char in state["characters"]:
                if item not in state["characters"][char]["inventory"]:
                    state["characters"][char]["inventory"].append(item)
            else:
                failures.append(f"Invalid Character: '{char}' is not registered.")
                
        elif t_type == "lose":
            item = t["item"]
            char = t["character"]
            if char in state["characters"]:
                inv = state["characters"][char]["inventory"]
                if item in inv:
                    inv.remove(item)
                else:
                    failures.append(
                        f"Missing Inventory Item: {char.capitalize()} tries to lose '{item}' but does not possess it."
                    )
            else:
                failures.append(f"Invalid Character: '{char}' is not registered.")
                
        elif t_type == "kill":
            char = t["character"]
            if char in state["characters"]:
                state["characters"][char]["status"] = "dead"
            else:
                failures.append(f"Invalid Character: '{char}' is not registered.")

    # 2. Location Check (Prose vs State)
    scene_loc = scene.get("location")
    if scene_loc:
        # Check if character is mentioned in draft but location doesn't match
        for char_name, char_info in state["characters"].items():
            if char_info["status"] == "dead":
                continue
                
            # Quick check if character name is in draft
            char_pattern = re.compile(rf"\b{re.escape(char_name)}\b", re.IGNORECASE)
            if char_pattern.search(draft_text):
                char_loc = char_info["location"]
                if char_loc != scene_loc:
                    warnings.append(
                        f"Location Inconsistency: '{char_name.capitalize()}' is mentioned in the draft but is at '{char_loc}' (scene takes place at '{scene_loc}')."
                    )
                    break

    # 3. Item Presence in Prose Check
    # Verify that if a character is described using a weapon/item, they actually own it in inventory
    sentences = re.split(r"(?<=[.!?])\s+", draft_text)
    for char_name, char_info in state["characters"].items():
        inv = char_info["inventory"]
        
        # Check weapon usage in draft
        # e.g., if draft mentions "Darin shot" or "Darin raised his Colt", does Darin have a colt or revolver?
        char_pattern = re.compile(rf"\b{re.escape(char_name)}\b.*?\b(shot|fired|pulled|raised|drew)\b.*?\b(colt|winchester|rifle|pistol|revolver|pocket_watch|watch|key|map)\b", re.IGNORECASE)
        
        for sentence in sentences:
            match = char_pattern.search(sentence)
            if not match:
                continue
            used_keyword = match.group(2).lower()
            
            # Map prose keywords to inventory slugs
            item_match = False
            for item in inv:
                if used_keyword in item or item in used_keyword:
                    item_match = True
                    break
                    
            # Fallback for general weapons
            if used_keyword in ["colt", "revolver", "pistol"] and any("colt" in item or "revolver" in item for item in inv):
                item_match = True
            elif used_keyword in ["winchester", "rifle"] and any("winchester" in item or "rifle" in item or "repeater" in item for item in inv):
                item_match = True
            elif used_keyword in ["pocket_watch", "watch"] and any("watch" in item for item in inv):
                item_match = True
            elif used_keyword in ["key"] and any("key" in item for item in inv):
                item_match = True
            elif used_keyword in ["map"] and any("map" in item for item in inv):
                item_match = True
                
            if not item_match:
                failures.append(
                    f"Inventory Inconsistency: {char_name.capitalize()} uses a '{used_keyword}' in the prose but does not own it in inventory (possesses: {inv})."
                )

    return failures, warnings
