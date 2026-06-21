"""Event discovery and canon fold (event-sourcing replay) engine."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import List

from bookforge.core.canon.io import (
    load_yaml_file,
    save_yaml_file,
    load_characters,
    load_locations,
    load_objects,
    get_events_dir,
    get_state_dir,
)


def discover_events(book_folder: Path) -> List[Path]:
    """Return event files sorted by chapter number."""
    events_dir = get_events_dir(book_folder)
    if not events_dir.exists():
        return []

    def extract_chapter_num(path: Path) -> int:
        match = re.search(r"chapter[-_](\d+)", path.name, re.I)
        return int(match.group(1)) if match else 9999

    event_files = list(events_dir.glob("*.event.yml"))
    event_files.sort(key=extract_chapter_num)
    return event_files


def fold_canon(book_folder: Path) -> dict:
    """Fold durable entities + chapter events into current snapshot.

    Returns the computed snapshot dictionary.
    """
    characters = load_characters(book_folder)
    locations = load_locations(book_folder)
    objects = load_objects(book_folder)

    # Initialize character state
    char_state = {
        cid: {
            "canonical": info.get("canonical", cid.replace("_", " ").capitalize()),
            "tier": info.get("tier", "incidental"),
            "role": info.get("role", "none"),
            "status": "alive",
            "location": "unknown",
            "inventory": [],
            "injuries": copy.deepcopy(info.get("injuries", {})),
            "relationships": dict(info.get("relationships", {})),
            "secrets": list(info.get("secrets", [])),
            "emotional_state": "neutral",
        }
        for cid, info in characters.items()
    }

    # Initialize object state
    obj_state = {
        oid: {
            "canonical": info.get("canonical", oid.replace("_", " ").capitalize()),
            "type": info.get("type", "item"),
            "holder": None,
            "state": {},
        }
        for oid, info in objects.items()
    }

    # Initialize location occupants
    loc_state = {
        lid: {
            "canonical": info.get("canonical", lid.replace("_", " ").capitalize()),
            "occupants": [],
        }
        for lid, info in locations.items()
    }

    unresolved_pressure: list = []
    chapter_invariants: list = []

    for ep in discover_events(book_folder):
        event_data = load_yaml_file(ep)
        try:
            current_chapter = int(event_data.get("chapter", 1))
        except (ValueError, TypeError):
            current_chapter = 1

        # Age injuries
        for c_info in char_state.values():
            injuries = c_info["injuries"]
            healed = []
            for inj_id, inj in list(injuries.items()):
                rem = inj.get("healing_chapters_remaining")
                if rem is not None:
                    rem -= 1
                    if rem <= 0:
                        healed.append(inj_id)
                    else:
                        inj["healing_chapters_remaining"] = rem
            for inj_id in healed:
                injuries[inj_id]["status"] = "healed"

        for ev in event_data.get("events", []):
            ev_type = ev.get("type")

            if ev_type == "character_status":
                cid = ev.get("character_id")
                if cid in char_state:
                    status_val = ev.get("status", "alive")
                    char_state[cid]["status"] = status_val
                    if status_val == "dead":
                        char_state[cid]["inventory"] = []

            elif ev_type == "character_mutation":
                cid = ev.get("character_id")
                if cid in char_state:
                    new_loc = ev.get("location")
                    if new_loc:
                        old_loc = char_state[cid]["location"]
                        if old_loc in loc_state and cid in loc_state[old_loc]["occupants"]:
                            loc_state[old_loc]["occupants"].remove(cid)
                        char_state[cid]["location"] = new_loc
                        if new_loc in loc_state and cid not in loc_state[new_loc]["occupants"]:
                            loc_state[new_loc]["occupants"].append(cid)

                    inv = char_state[cid]["inventory"]
                    for item in ev.get("inventory_added", []):
                        if item not in inv:
                            inv.append(item)
                    for item in ev.get("inventory_removed", []):
                        if item in inv:
                            inv.remove(item)

                    injuries = char_state[cid]["injuries"]
                    for inj in ev.get("injuries_sustained", []):
                        inj_id = inj.get("id")
                        if inj_id:
                            injuries[inj_id] = {
                                "description": inj.get("description", ""),
                                "severity": inj.get("severity", "light"),
                                "healing_chapters_remaining": inj.get("healing_duration_chapters"),
                                "status": "active",
                            }
                    for inj_id in ev.get("injuries_healed", []):
                        if inj_id in injuries:
                            injuries[inj_id]["status"] = "healed"
                            injuries[inj_id]["healing_chapters_remaining"] = 0

                    for sec in ev.get("secrets_learned", []):
                        if sec not in char_state[cid]["secrets"]:
                            char_state[cid]["secrets"].append(sec)

                    for rel_cid, rel_val in ev.get("relationships_shifted", {}).items():
                        char_state[cid]["relationships"][rel_cid] = rel_val

                    est = ev.get("emotional_state")
                    if est:
                        char_state[cid]["emotional_state"] = est

            elif ev_type == "object_mutation":
                oid = ev.get("object_id")
                if oid in obj_state:
                    holder = ev.get("holder")
                    obj_state[oid]["holder"] = holder
                    if holder:
                        if holder in char_state and oid not in char_state[holder]["inventory"]:
                            char_state[holder]["inventory"].append(oid)
                    else:
                        for c_info in char_state.values():
                            if oid in c_info["inventory"]:
                                c_info["inventory"].remove(oid)
                    obj_state[oid]["state"].update(ev.get("state", {}))

            elif ev_type == "stakes":
                pressures = ev.get("unresolved_pressure")
                if pressures:
                    if isinstance(pressures, list):
                        unresolved_pressure.extend(pressures)
                    else:
                        unresolved_pressure.append(pressures)
                invars = ev.get("invariants")
                if invars:
                    if isinstance(invars, list):
                        chapter_invariants.extend(invars)
                    else:
                        chapter_invariants.append(invars)

    snapshot = {
        "characters": char_state,
        "locations": loc_state,
        "objects": obj_state,
        "unresolved_pressure": unresolved_pressure,
        "chapter_invariants": chapter_invariants,
    }
    save_yaml_file(get_state_dir(book_folder) / "snapshot.yml", snapshot)
    return snapshot
