# bookforge/core/canon.py
"""Event-sourced canon and validation subsystem for BookForge."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import yaml

from bookforge.core.issue import ManuscriptIssue, Severity, IssueCategory


def get_canon_dir(book_folder: Path) -> Path:
    return book_folder / "canon"


def get_entities_dir(book_folder: Path) -> Path:
    return get_canon_dir(book_folder) / "entities"


def get_events_dir(book_folder: Path) -> Path:
    return get_canon_dir(book_folder) / "events"


def get_state_dir(book_folder: Path) -> Path:
    return get_canon_dir(book_folder) / "state"


def load_yaml_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_yaml_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_characters(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "characters.yml")
    return data.get("characters", {})


def load_aliases(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "aliases.yml")
    return data.get("aliases", {})


def load_locations(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "locations.yml")
    return data.get("locations", {})


def load_objects(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "objects.yml")
    return data.get("objects", {})


def discover_events(book_folder: Path) -> List[Path]:
    events_dir = get_events_dir(book_folder)
    if not events_dir.exists():
        return []
    
    # Sort files like chapter-01.event.yml, chapter-02.event.yml numerically
    event_files = list(events_dir.glob("*.event.yml"))
    
    def extract_chapter_num(path: Path) -> int:
        match = re.search(r"chapter[-_](\d+)", path.name, re.I)
        if match:
            return int(match.group(1))
        return 9999
    
    event_files.sort(key=extract_chapter_num)
    return event_files


def fold_canon(book_folder: Path) -> dict:
    """Folds the durable entities and chapter events to construct the current snapshot.
    
    Returns the computed snapshot dictionary.
    """
    characters = load_characters(book_folder)
    locations = load_locations(book_folder)
    objects = load_objects(book_folder)
    
    # Initialize character current state
    import copy
    char_state = {}
    for cid, info in characters.items():
        char_state[cid] = {
            "canonical": info.get("canonical", cid.replace("_", " ").capitalize()),
            "tier": info.get("tier", "incidental"),
            "role": info.get("role", "none"),
            "status": "alive",
            "location": "unknown",
            "inventory": [],
            "injuries": copy.deepcopy(info.get("injuries", {})),
            "relationships": dict(info.get("relationships", {})),
            "secrets": list(info.get("secrets", [])),
            "emotional_state": "neutral"
        }
        
    # Initialize object state
    obj_state = {}
    for oid, info in objects.items():
        obj_state[oid] = {
            "canonical": info.get("canonical", oid.replace("_", " ").capitalize()),
            "type": info.get("type", "item"),
            "holder": None,
            "state": {}
        }
        
    # Initialize location occupants
    loc_state = {}
    for lid, info in locations.items():
        loc_state[lid] = {
            "canonical": info.get("canonical", lid.replace("_", " ").capitalize()),
            "occupants": []
        }
        
    # Replay events sequentially
    event_files = discover_events(book_folder)
    unresolved_pressure = []
    chapter_invariants = []
    
    for ep in event_files:
        event_data = load_yaml_file(ep)
        ch_num_val = event_data.get("chapter", 1)
        try:
            current_chapter = int(ch_num_val)
        except (ValueError, TypeError):
            current_chapter = 1
            
        # Age injuries before applying the new chapter's events
        for cid, c_info in char_state.items():
            injuries = c_info["injuries"]
            healed_injuries = []
            for inj_id, inj in list(injuries.items()):
                # Decrement healing chapters remaining if defined
                rem = inj.get("healing_chapters_remaining")
                if rem is not None:
                    rem -= 1
                    if rem <= 0:
                        healed_injuries.append(inj_id)
                    else:
                        inj["healing_chapters_remaining"] = rem
            for inj_id in healed_injuries:
                injuries[inj_id]["status"] = "healed"
                
        events_list = event_data.get("events", [])
        for ev in events_list:
            ev_type = ev.get("type")
            
            if ev_type == "character_status":
                cid = ev.get("character_id")
                if cid in char_state:
                    status_val = ev.get("status", "alive")
                    char_state[cid]["status"] = status_val
                    if status_val == "dead":
                        # Dead characters drop their inventory
                        char_state[cid]["inventory"] = []
                        
            elif ev_type == "character_mutation":
                cid = ev.get("character_id")
                if cid in char_state:
                    # Travel mutation
                    new_loc = ev.get("location")
                    if new_loc:
                        old_loc = char_state[cid]["location"]
                        if old_loc in loc_state:
                            if cid in loc_state[old_loc]["occupants"]:
                                loc_state[old_loc]["occupants"].remove(cid)
                        char_state[cid]["location"] = new_loc
                        if new_loc in loc_state:
                            if cid not in loc_state[new_loc]["occupants"]:
                                loc_state[new_loc]["occupants"].append(cid)
                                
                    # Inventory added
                    for item in ev.get("inventory_added", []):
                        if item not in char_state[cid]["inventory"]:
                            char_state[cid]["inventory"].append(item)
                            
                    # Inventory removed
                    for item in ev.get("inventory_removed", []):
                        if item in char_state[cid]["inventory"]:
                            char_state[cid]["inventory"].remove(item)
                            
                    # Injuries sustained
                    for inj in ev.get("injuries_sustained", []):
                        inj_id = inj.get("id")
                        if inj_id:
                            duration = inj.get("healing_duration_chapters")
                            char_state[cid]["injuries"][inj_id] = {
                                "description": inj.get("description", ""),
                                "severity": inj.get("severity", "light"),
                                "healing_chapters_remaining": duration,
                                "status": "active"
                            }
                            
                    # Injuries healed manually
                    for inj_id in ev.get("injuries_healed", []):
                        if inj_id in char_state[cid]["injuries"]:
                            char_state[cid]["injuries"][inj_id]["status"] = "healed"
                            char_state[cid]["injuries"][inj_id]["healing_chapters_remaining"] = 0
                            
                    # Secrets learned
                    for sec in ev.get("secrets_learned", []):
                        if sec not in char_state[cid]["secrets"]:
                            char_state[cid]["secrets"].append(sec)
                            
                    # Relationships shifted
                    for rel_cid, rel_val in ev.get("relationships_shifted", {}).items():
                        char_state[cid]["relationships"][rel_cid] = rel_val
                        
                    # Emotional state
                    est = ev.get("emotional_state")
                    if est:
                        char_state[cid]["emotional_state"] = est
                        
            elif ev_type == "object_mutation":
                oid = ev.get("object_id")
                if oid in obj_state:
                    holder = ev.get("holder")
                    obj_state[oid]["holder"] = holder
                    # Sync with character inventory
                    if holder:
                        if holder in char_state:
                            if oid not in char_state[holder]["inventory"]:
                                char_state[holder]["inventory"].append(oid)
                    else:
                        # Dropped object, remove from anyone holding it
                        for cid, c_info in char_state.items():
                            if oid in c_info["inventory"]:
                                c_info["inventory"].remove(oid)
                    
                    # Update custom states
                    custom_state = ev.get("state", {})
                    obj_state[oid]["state"].update(custom_state)
                    
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
        "chapter_invariants": chapter_invariants
    }
    
    # Save the snapshot
    save_yaml_file(get_state_dir(book_folder) / "snapshot.yml", snapshot)
    return snapshot


def validate_canon(book_folder: Path) -> List[ManuscriptIssue]:
    """Validates the entity schemas, event timelines, coherence, and alias resolution.
    
    Returns a list of ManuscriptIssue objects.
    """
    issues = []
    canon_dir = get_canon_dir(book_folder)
    if not canon_dir.exists():
        return issues
        
    characters = load_characters(book_folder)
    locations = load_locations(book_folder)
    objects = load_objects(book_folder)
    aliases = load_aliases(book_folder)
    
    # 1. Timeline integrity and event ID coherence
    event_files = discover_events(book_folder)
    chapters_seen = set()
    prev_chapter = 0
    
    # Maintain character locations at each chapter stage
    char_locations_by_chapter = {}
    char_inventories_by_chapter = {}
    char_statuses_by_chapter = {}
    
    # Run a dry-run fold to capture snapshots per chapter
    temp_char_state = {}
    for cid, info in characters.items():
        temp_char_state[cid] = {
            "status": "alive",
            "location": "unknown",
            "inventory": []
        }
    temp_obj_state = {}
    for oid in objects:
        temp_obj_state[oid] = {"holder": None}
        
    for ep in event_files:
        event_data = load_yaml_file(ep)
        ch_num = event_data.get("chapter")
        if ch_num is None:
            issues.append(
                ManuscriptIssue(
                    severity=Severity.HARD,
                    category=IssueCategory.CONTINUITY,
                    file=ep,
                    rule_id="canon_missing_chapter_number",
                    message=f"Event file {ep.name} is missing a 'chapter' number field."
                )
            )
            continue
            
        try:
            ch_num = int(ch_num)
        except (ValueError, TypeError):
            issues.append(
                ManuscriptIssue(
                    severity=Severity.HARD,
                    category=IssueCategory.CONTINUITY,
                    file=ep,
                    rule_id="canon_invalid_chapter_number",
                    message=f"Event file {ep.name} has invalid 'chapter' value: {ch_num}."
                )
            )
            continue
            
        if ch_num in chapters_seen:
            issues.append(
                ManuscriptIssue(
                    severity=Severity.HARD,
                    category=IssueCategory.CONTINUITY,
                    file=ep,
                    rule_id="canon_duplicate_chapter_event",
                    message=f"Duplicate event file for chapter {ch_num}: {ep.name}."
                )
            )
        chapters_seen.add(ch_num)
        
        if ch_num < prev_chapter:
            issues.append(
                ManuscriptIssue(
                    severity=Severity.HARD,
                    category=IssueCategory.CONTINUITY,
                    file=ep,
                    rule_id="canon_out_of_order_events",
                    message=f"Event file {ep.name} for chapter {ch_num} appears out of chronological order (previous was {prev_chapter})."
                )
            )
        prev_chapter = ch_num
        
        # Apply mutations for this chapter to dry-run state
        events = event_data.get("events", [])
        for ev in events:
            ev_type = ev.get("type")
            if ev_type == "character_status":
                cid = ev.get("character_id")
                if cid in temp_char_state:
                    status_val = ev.get("status", "alive")
                    temp_char_state[cid]["status"] = status_val
                    if status_val == "dead":
                        temp_char_state[cid]["inventory"] = []
                else:
                    issues.append(
                        ManuscriptIssue(
                            severity=Severity.HARD,
                            category=IssueCategory.CONTINUITY,
                            file=ep,
                            rule_id="canon_invalid_character_reference",
                            message=f"Character status event references unknown character ID: '{cid}'."
                        )
                    )
            elif ev_type == "character_mutation":
                cid = ev.get("character_id")
                if cid in temp_char_state:
                    loc = ev.get("location")
                    if loc:
                        if loc in locations:
                            temp_char_state[cid]["location"] = loc
                        else:
                            issues.append(
                                ManuscriptIssue(
                                    severity=Severity.HARD,
                                    category=IssueCategory.CONTINUITY,
                                    file=ep,
                                    rule_id="canon_invalid_location_reference",
                                    message=f"Character mutation event references unknown location ID: '{loc}'."
                                )
                            )
                    # Handle inventory added/removed
                    for item in ev.get("inventory_added", []):
                        if item not in temp_char_state[cid]["inventory"]:
                            temp_char_state[cid]["inventory"].append(item)
                    for item in ev.get("inventory_removed", []):
                        if item in temp_char_state[cid]["inventory"]:
                            temp_char_state[cid]["inventory"].remove(item)
                else:
                    issues.append(
                        ManuscriptIssue(
                            severity=Severity.HARD,
                            category=IssueCategory.CONTINUITY,
                            file=ep,
                            rule_id="canon_invalid_character_reference",
                            message=f"Character mutation event references unknown character ID: '{cid}'."
                        )
                    )
            elif ev_type == "object_mutation":
                oid = ev.get("object_id")
                if oid in temp_obj_state:
                    holder = ev.get("holder")
                    temp_obj_state[oid]["holder"] = holder
                    if holder:
                        if holder in temp_char_state:
                            if oid not in temp_char_state[holder]["inventory"]:
                                temp_char_state[holder]["inventory"].append(oid)
                        else:
                            issues.append(
                                ManuscriptIssue(
                                    severity=Severity.HARD,
                                    category=IssueCategory.CONTINUITY,
                                    file=ep,
                                    rule_id="canon_invalid_character_reference",
                                    message=f"Object mutation event references unknown character holder: '{holder}'."
                                )
                            )
                else:
                    issues.append(
                        ManuscriptIssue(
                            severity=Severity.HARD,
                            category=IssueCategory.CONTINUITY,
                            file=ep,
                            rule_id="canon_invalid_object_reference",
                            message=f"Object mutation event references unknown object ID: '{oid}'."
                        )
                    )
                    
        # Record state for the chapter
        char_locations_by_chapter[ch_num] = {cid: info["location"] for cid, info in temp_char_state.items()}
        char_inventories_by_chapter[ch_num] = {cid: list(info["inventory"]) for cid, info in temp_char_state.items()}
        char_statuses_by_chapter[ch_num] = {cid: info["status"] for cid, info in temp_char_state.items()}
        
    # 2. Prose alias resolution and logic validator
    from bookforge.core.validator import discover_chapters
    chapters = discover_chapters(book_folder)
    
    common_proper_nouns = {
        "Tex", "Cade", "I", "He", "She", "It", "They", "We", "You", "The", "A", "An", "But",
        "And", "Or", "If", "Then", "When", "Where", "Why", "How", "No", "Yes", "So", "Monday",
        "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "January", "February",
        "March", "April", "May", "June", "July", "August", "September", "October", "November",
        "December", "Colt", "Winchester", "Bowie", "Ranger", "Sheriff", "Marshal", "President"
    }
    
    for ch in chapters:
        # Extract numerical chapter ID
        match = re.search(r"chapter[-_](\d+)", ch.slug, re.I)
        if not match:
            continue
        ch_num = int(match.group(1))
        
        # Get historical snapshot states for this chapter
        ch_char_locs = char_locations_by_chapter.get(ch_num, {})
        ch_char_invs = char_inventories_by_chapter.get(ch_num, {})
        ch_char_status = char_statuses_by_chapter.get(ch_num, {})
        
        if ch.draft.exists():
            try:
                draft_text = ch.draft.read_text(encoding="utf-8")
            except Exception:
                continue
                
            # Name resolution
            candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", draft_text)
            for cand in set(candidates):
                cand_lower = cand.lower().strip()
                if cand in common_proper_nouns or len(cand) <= 1:
                    continue
                if cand_lower in aliases or cand_lower in characters or cand_lower in locations or cand_lower in objects:
                    continue
                
                resolved = False
                for alias_name, canonical_id in aliases.items():
                    alias_norm = alias_name.replace("_", " ")
                    if alias_norm in cand_lower or cand_lower in alias_norm:
                        resolved = True
                        break
                if not resolved:
                    for cid in characters:
                        cid_norm = cid.replace("_", " ")
                        if cid_norm in cand_lower or cand_lower in cid_norm:
                            resolved = True
                            break
                if not resolved:
                    for lid in locations:
                        lid_norm = lid.replace("_", " ")
                        if lid_norm in cand_lower or cand_lower in lid_norm:
                            resolved = True
                            break
                if not resolved:
                    for oid in objects:
                        oid_norm = oid.replace("_", " ")
                        if oid_norm in cand_lower or cand_lower in oid_norm:
                            resolved = True
                            break
                        
                if not resolved:
                    issues.append(
                        ManuscriptIssue(
                            severity=Severity.SOFT,
                            category=IssueCategory.CONTINUITY,
                            chapter=ch.slug,
                            file=ch.draft,
                            rule_id="canon_unresolved_alias",
                            message=f"Proper noun '{cand}' in draft cannot be resolved against characters, locations, objects, or aliases."
                        )
                    )
                    
            # Check character states in draft
            for cid, info in characters.items():
                canon_name = info.get("canonical", cid)
                pattern = re.compile(rf"\b{re.escape(canon_name)}\b", re.I)
                
                # Check if character is mentioned in draft
                if pattern.search(draft_text):
                    # Status check: Dead character mentioned acting/dialogue
                    status = ch_char_status.get(cid, "alive")
                    if status == "dead":
                        # Check for dialogue: "..." says Darin or Darin says "..."
                        dialogue_pattern = re.compile(
                            rf'("[^"]*"\s*,?\s*(?:says|said|asked|shouted|replied)\s+{re.escape(canon_name)}|'
                            rf'{re.escape(canon_name)}\s*(?:says|said|asked|shouted|replied)\s*,?\s*"[^"]*")',
                            re.I
                        )
                        if dialogue_pattern.search(draft_text):
                            issues.append(
                                ManuscriptIssue(
                                    severity=Severity.HARD,
                                    category=IssueCategory.CONTINUITY,
                                    chapter=ch.slug,
                                    file=ch.draft,
                                    rule_id="canon_dead_actor_dialogue",
                                    message=f"Dead character '{canon_name}' speaks in chapter {ch.slug} draft."
                                )
                            )
                            
                    # Location/Teleportation check
                    loc = ch_char_locs.get(cid, "unknown")
                    if loc == "unknown":
                        issues.append(
                            ManuscriptIssue(
                                severity=Severity.SOFT,
                                category=IssueCategory.CONTINUITY,
                                chapter=ch.slug,
                                file=ch.draft,
                                rule_id="canon_character_unknown_location",
                                message=f"Character '{canon_name}' is active in draft but their folded location is unknown."
                            )
                        )
                    else:
                        # Check if draft matches their location:
                        # If their location is 'camp' but the draft only mentions 'saloon' or 'ridge', we check for consistency.
                        # We only warn if the draft contains a different known location but does not contain their expected location.
                        expected_loc_canonical = locations.get(loc, {}).get("canonical", loc)
                        expected_pattern = re.compile(rf"\b{re.escape(expected_loc_canonical)}\b", re.I)
                        
                        # Find other locations mentioned in the draft
                        mismatched_locations = []
                        for other_lid, other_info in locations.items():
                            if other_lid == loc:
                                continue
                            other_canonical = other_info.get("canonical", other_lid)
                            other_pattern = re.compile(rf"\b{re.escape(other_canonical)}\b", re.I)
                            if other_pattern.search(draft_text):
                                mismatched_locations.append(other_canonical)
                                
                        if mismatched_locations and not expected_pattern.search(draft_text):
                            # Warn about potential location mismatch
                            issues.append(
                                ManuscriptIssue(
                                    severity=Severity.SOFT,
                                    category=IssueCategory.CONTINUITY,
                                    chapter=ch.slug,
                                    file=ch.draft,
                                    rule_id="canon_location_mismatch",
                                    message=f"Character '{canon_name}' location is set to '{expected_loc_canonical}', but the draft mentions '{', '.join(mismatched_locations)}' instead."
                                )
                            )
                            
                    # Object/Inventory check
                    # Check if the text describes the character using/holding an object they don't have
                    char_inv = ch_char_invs.get(cid, [])
                    for oid, obj_info in objects.items():
                        obj_canonical = obj_info.get("canonical", oid)
                        obj_pattern = re.compile(rf"\b{re.escape(obj_canonical)}\b", re.I)
                        # Check proximity: is the object mentioned in a sentence that also mentions the character?
                        sentences = re.split(r'[.!?]+', draft_text)
                        for sentence in sentences:
                            if pattern.search(sentence) and obj_pattern.search(sentence):
                                if oid not in char_inv:
                                    # Look for owner
                                    owner = None
                                    for other_cid, other_inv in ch_char_invs.items():
                                        if oid in other_inv:
                                            owner = other_cid
                                            break
                                    if owner and owner != cid:
                                        owner_name = characters.get(owner, {}).get("canonical", owner)
                                        issues.append(
                                            ManuscriptIssue(
                                                severity=Severity.SOFT,
                                                category=IssueCategory.CONTINUITY,
                                                chapter=ch.slug,
                                                file=ch.draft,
                                                rule_id="canon_object_ownership_conflict",
                                                message=f"Draft mentions '{canon_name}' using '{obj_canonical}', which belongs to '{owner_name}''s inventory."
                                            )
                                        )
                                        break  # Report only once per character/object pair
                                    
    return issues


def migrate_legacy_book(book_folder: Path) -> None:
    """Migrates legacy world-state.json, relationships.json, and rulebook.md to event-sourced structures.
    
    Creates canon/entities/* and initial events. Idempotent.
    """
    canon_dir = get_canon_dir(book_folder)
    entities_dir = get_entities_dir(book_folder)
    events_dir = get_events_dir(book_folder)
    
    entities_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load legacy world-state.json
    world_state_path = book_folder / "world-state.json"
    legacy_chars = {}
    legacy_locs = []
    
    if world_state_path.exists():
        try:
            import json
            ws = json.loads(world_state_path.read_text(encoding="utf-8"))
            legacy_chars = ws.get("characters", {})
            legacy_locs = ws.get("locations", [])
        except Exception:
            pass
            
    # 2. Load legacy relationships
    relationships_path = book_folder / "relationships.json"
    legacy_rels = []
    if relationships_path.exists():
        try:
            import json
            legacy_rels = json.loads(relationships_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    # 3. Create characters.yml
    char_yaml_path = entities_dir / "characters.yml"
    char_data = {"characters": {}}
    alias_data = {"aliases": {}}
    
    # Populate characters.yml and aliases.yml
    for name, info in legacy_chars.items():
        cid = name.lower().replace(" ", "_")
        
        # Build relationships for character
        c_rels = {}
        rels_list = legacy_rels.values() if isinstance(legacy_rels, dict) else legacy_rels
        for rel in rels_list:
            if not isinstance(rel, dict):
                continue
            sub = rel.get("subject", "").lower()
            obj = rel.get("object", "").lower()
            relation = rel.get("relation", "")
            if sub == cid:
                c_rels[obj] = relation
                
        # Basic tier heuristics
        tier = "minor_named"
        if cid in ["tex_cade", "tex", "harlan"]:
            tier = "main"
        elif cid in ["darin", "mara_vale"]:
            tier = "major_supporting"
            
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
        
        # Add basic name alias
        alias_data["aliases"][cid.replace("_", " ")] = cid
        alias_data["aliases"][name.lower()] = cid
        
    save_yaml_file(char_yaml_path, char_data)
    
    # 4. Create locations.yml
    loc_yaml_path = entities_dir / "locations.yml"
    loc_data = {"locations": {}}
    for loc_name in legacy_locs:
        lid = loc_name.lower().replace(" ", "_")
        loc_data["locations"][lid] = {
            "canonical": loc_name.capitalize(),
            "function": "narrative point",
            "description": f"The {loc_name} setting."
        }
        alias_data["aliases"][loc_name.lower()] = lid
    save_yaml_file(loc_yaml_path, loc_data)
    
    # 5. Create objects.yml
    obj_yaml_path = entities_dir / "objects.yml"
    obj_data = {"objects": {}}
    
    # Scan character inventory to discover objects
    for name, info in legacy_chars.items():
        cid = name.lower().replace(" ", "_")
        for item in info.get("inventory", []):
            oid = item.lower().replace(" ", "_")
            if oid not in obj_data["objects"]:
                obj_data["objects"][oid] = {
                    "canonical": item.replace("_", " ").capitalize(),
                    "type": "weapon" if "colt" in oid or "rifle" in oid or "gun" in oid else "item"
                }
                alias_data["aliases"][item.lower().replace("_", " ")] = oid
    save_yaml_file(obj_yaml_path, obj_data)
    
    # Save aliases.yml
    save_yaml_file(entities_dir / "aliases.yml", alias_data)
    
    # 6. Create initial chapter-01.event.yml based on initial legacy states
    event_yaml_path = events_dir / "chapter-01.event.yml"
    if not event_yaml_path.exists():
        init_events = []
        # Populate initial character mutations (location, inventory)
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
            
            # Map object ownership
            for item in inv:
                oid = item.lower().replace(" ", "_")
                init_events.append({
                    "type": "object_mutation",
                    "object_id": oid,
                    "holder": cid
                })
                
        event_data = {
            "chapter": 1,
            "events": init_events
        }
        save_yaml_file(event_yaml_path, event_data)
        
    # Re-fold immediately
    fold_canon(book_folder)


def apply_chapter_event(book_folder: Path, chapter_id: str, change_data: dict) -> None:
    """Safely appends a new chapter event and rebuilds snapshot, if validation passes."""
    events_dir = get_events_dir(book_folder)
    events_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract chapter number
    match = re.search(r"chapter[-_](\d+)", chapter_id, re.I)
    ch_num = int(match.group(1)) if match else 1
    
    event_file = events_dir / f"{chapter_id}.event.yml"
    save_yaml_file(event_file, {
        "chapter": ch_num,
        "events": change_data.get("events", [])
    })
    
    # Fold state immediately
    fold_canon(book_folder)


def parse_continuity_out_to_event(continuity_path: Path) -> dict:
    """Parses a legacy or generated continuity-out.md into a mutation event structure."""
    if not continuity_path.exists():
        return {"events": []}
        
    text = continuity_path.read_text(encoding="utf-8")
    events = []
    
    # Parse explicit structured YAML blocks if present
    yaml_blocks = re.findall(r"```yaml\s*\n(.*?)\n```", text, re.DOTALL)
    for block in yaml_blocks:
        try:
            parsed = yaml.safe_load(block)
            if isinstance(parsed, dict) and "events" in parsed:
                events.extend(parsed["events"])
        except Exception:
            pass
            
    # Default section parser fallback
    current_section = ""
    pressures = []
    lines = text.splitlines()
    for line in lines:
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
                char_name = match_dead.group(1).lower().replace(" ", "_")
                events.append({
                    "type": "character_status",
                    "character_id": char_name,
                    "status": "dead"
                })
        elif "changes" in current_section or "locations" in current_section:
            match_travel = re.search(r"(\w+(?:\s+\w+)?)\s+(?:is at|traveled to|moves to|moved to)\s+([\w\s]+)", clean_line, re.I)
            if match_travel:
                char_name = match_travel.group(1).lower().replace(" ", "_")
                loc_name = match_travel.group(2).strip().lower().replace(" ", "_").rstrip(".")
                events.append({
                    "type": "character_mutation",
                    "character_id": char_name,
                    "location": loc_name
                })
        elif "unresolved" in current_section:
            pressures.append(clean_line)
            
    if pressures:
        events.append({
            "type": "stakes",
            "unresolved_pressure": pressures
        })
        
    return {"events": events}

