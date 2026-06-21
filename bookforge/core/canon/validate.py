"""Canon validation: entity schemas, event timelines, prose alias resolution."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from bookforge.core.issue import ManuscriptIssue, Severity, IssueCategory
from bookforge.core.canon.io import (
    load_characters,
    load_aliases,
    load_locations,
    load_objects,
    load_yaml_file,
    get_events_dir,
)
from bookforge.core.canon.fold import discover_events

# Proper nouns that are not manuscript entity IDs and should not trigger warnings
_COMMON_PROPER_NOUNS = {
    "Tex", "Cade", "I", "He", "She", "It", "They", "We", "You", "The", "A", "An", "But",
    "And", "Or", "If", "Then", "When", "Where", "Why", "How", "No", "Yes", "So", "Monday",
    "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "January", "February",
    "March", "April", "May", "June", "July", "August", "September", "October", "November",
    "December", "Colt", "Winchester", "Bowie", "Ranger", "Sheriff", "Marshal", "President"
}


def validate_canon(book_folder: Path) -> List[ManuscriptIssue]:
    """Validate entity schemas, event timelines, coherence, and alias resolution."""
    issues: List[ManuscriptIssue] = []
    if not (book_folder / "canon").exists():
        return issues

    characters = load_characters(book_folder)
    locations = load_locations(book_folder)
    objects = load_objects(book_folder)
    aliases = load_aliases(book_folder)

    # --- Phase 1: Timeline integrity ---
    char_locations_by_chapter: dict = {}
    char_inventories_by_chapter: dict = {}
    char_statuses_by_chapter: dict = {}

    temp_char = {cid: {"status": "alive", "location": "unknown", "inventory": []} for cid in characters}
    temp_obj = {oid: {"holder": None} for oid in objects}

    chapters_seen: set = set()
    prev_chapter = 0

    for ep in discover_events(book_folder):
        event_data = load_yaml_file(ep)
        ch_num = event_data.get("chapter")

        if ch_num is None:
            issues.append(ManuscriptIssue(
                severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                rule_id="canon_missing_chapter_number",
                message=f"Event file {ep.name} is missing a 'chapter' number field."
            ))
            continue

        try:
            ch_num = int(ch_num)
        except (ValueError, TypeError):
            issues.append(ManuscriptIssue(
                severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                rule_id="canon_invalid_chapter_number",
                message=f"Event file {ep.name} has invalid 'chapter' value: {ch_num}."
            ))
            continue

        if ch_num in chapters_seen:
            issues.append(ManuscriptIssue(
                severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                rule_id="canon_duplicate_chapter_event",
                message=f"Duplicate event file for chapter {ch_num}: {ep.name}."
            ))
        chapters_seen.add(ch_num)

        if ch_num < prev_chapter:
            issues.append(ManuscriptIssue(
                severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                rule_id="canon_out_of_order_events",
                message=f"Event file {ep.name} for chapter {ch_num} appears out of chronological order (previous was {prev_chapter})."
            ))
        prev_chapter = ch_num

        for ev in event_data.get("events", []):
            ev_type = ev.get("type")

            if ev_type == "character_status":
                cid = ev.get("character_id")
                if cid in temp_char:
                    status_val = ev.get("status", "alive")
                    temp_char[cid]["status"] = status_val
                    if status_val == "dead":
                        temp_char[cid]["inventory"] = []
                else:
                    issues.append(ManuscriptIssue(
                        severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                        rule_id="canon_invalid_character_reference",
                        message=f"Character status event references unknown character ID: '{cid}'."
                    ))

            elif ev_type == "character_mutation":
                cid = ev.get("character_id")
                if cid in temp_char:
                    loc = ev.get("location")
                    if loc:
                        if loc in locations:
                            temp_char[cid]["location"] = loc
                        else:
                            issues.append(ManuscriptIssue(
                                severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                                rule_id="canon_invalid_location_reference",
                                message=f"Character mutation event references unknown location ID: '{loc}'."
                            ))
                    inv = temp_char[cid]["inventory"]
                    for item in ev.get("inventory_added", []):
                        if item not in inv:
                            inv.append(item)
                    for item in ev.get("inventory_removed", []):
                        if item in inv:
                            inv.remove(item)
                else:
                    issues.append(ManuscriptIssue(
                        severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                        rule_id="canon_invalid_character_reference",
                        message=f"Character mutation event references unknown character ID: '{cid}'."
                    ))

            elif ev_type == "object_mutation":
                oid = ev.get("object_id")
                if oid in temp_obj:
                    holder = ev.get("holder")
                    temp_obj[oid]["holder"] = holder
                    if holder:
                        if holder in temp_char:
                            if oid not in temp_char[holder]["inventory"]:
                                temp_char[holder]["inventory"].append(oid)
                        else:
                            issues.append(ManuscriptIssue(
                                severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                                rule_id="canon_invalid_character_reference",
                                message=f"Object mutation event references unknown character holder: '{holder}'."
                            ))
                else:
                    issues.append(ManuscriptIssue(
                        severity=Severity.HARD, category=IssueCategory.CONTINUITY, file=ep,
                        rule_id="canon_invalid_object_reference",
                        message=f"Object mutation event references unknown object ID: '{oid}'."
                    ))

        char_locations_by_chapter[ch_num] = {cid: info["location"] for cid, info in temp_char.items()}
        char_inventories_by_chapter[ch_num] = {cid: list(info["inventory"]) for cid, info in temp_char.items()}
        char_statuses_by_chapter[ch_num] = {cid: info["status"] for cid, info in temp_char.items()}

    # --- Phase 2: Prose alias resolution ---
    from bookforge.core.validator import discover_chapters
    for ch in discover_chapters(book_folder):
        match = re.search(r"chapter[-_](\d+)", ch.slug, re.I)
        if not match:
            continue
        ch_num = int(match.group(1))

        ch_char_locs = char_locations_by_chapter.get(ch_num, {})
        ch_char_invs = char_inventories_by_chapter.get(ch_num, {})
        ch_char_status = char_statuses_by_chapter.get(ch_num, {})

        if not ch.draft.exists():
            continue
        try:
            draft_text = ch.draft.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Name resolution
        for cand in set(re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", draft_text)):
            cand_lower = cand.lower().strip()
            if cand in _COMMON_PROPER_NOUNS or len(cand) <= 1:
                continue
            if cand_lower in aliases or cand_lower in characters or cand_lower in locations or cand_lower in objects:
                continue

            resolved = any(
                alias_name.replace("_", " ") in cand_lower or cand_lower in alias_name.replace("_", " ")
                for alias_name in aliases
            ) or any(
                cid.replace("_", " ") in cand_lower or cand_lower in cid.replace("_", " ")
                for cid in characters
            ) or any(
                lid.replace("_", " ") in cand_lower or cand_lower in lid.replace("_", " ")
                for lid in locations
            ) or any(
                oid.replace("_", " ") in cand_lower or cand_lower in oid.replace("_", " ")
                for oid in objects
            )

            if not resolved:
                issues.append(ManuscriptIssue(
                    severity=Severity.SOFT, category=IssueCategory.CONTINUITY,
                    chapter=ch.slug, file=ch.draft,
                    rule_id="canon_unresolved_alias",
                    message=f"Proper noun '{cand}' in draft cannot be resolved against characters, locations, objects, or aliases."
                ))

        # Character state checks
        for cid, info in characters.items():
            canon_name = info.get("canonical", cid)
            pattern = re.compile(rf"\b{re.escape(canon_name)}\b", re.I)
            if not pattern.search(draft_text):
                continue

            # Dead actor dialogue check
            if ch_char_status.get(cid, "alive") == "dead":
                dialogue_pattern = re.compile(
                    rf'("[^"]*",?\s*(?:says|said|asked|shouted|replied)\s+{re.escape(canon_name)}|'
                    rf'{re.escape(canon_name)}\s*(?:says|said|asked|shouted|replied)\s*,?\s*"[^"]*")',
                    re.I
                )
                if dialogue_pattern.search(draft_text):
                    issues.append(ManuscriptIssue(
                        severity=Severity.HARD, category=IssueCategory.CONTINUITY,
                        chapter=ch.slug, file=ch.draft,
                        rule_id="canon_dead_actor_dialogue",
                        message=f"Dead character '{canon_name}' speaks in chapter {ch.slug} draft."
                    ))

            # Location check
            loc = ch_char_locs.get(cid, "unknown")
            if loc == "unknown":
                issues.append(ManuscriptIssue(
                    severity=Severity.SOFT, category=IssueCategory.CONTINUITY,
                    chapter=ch.slug, file=ch.draft,
                    rule_id="canon_character_unknown_location",
                    message=f"Character '{canon_name}' is active in draft but their folded location is unknown."
                ))
            else:
                expected_loc_canonical = locations.get(loc, {}).get("canonical", loc)
                expected_pattern = re.compile(rf"\b{re.escape(expected_loc_canonical)}\b", re.I)
                mismatched = [
                    other_info.get("canonical", other_lid)
                    for other_lid, other_info in locations.items()
                    if other_lid != loc and re.search(rf"\b{re.escape(other_info.get('canonical', other_lid))}\b", draft_text, re.I)
                ]
                if mismatched and not expected_pattern.search(draft_text):
                    issues.append(ManuscriptIssue(
                        severity=Severity.SOFT, category=IssueCategory.CONTINUITY,
                        chapter=ch.slug, file=ch.draft,
                        rule_id="canon_location_mismatch",
                        message=f"Character '{canon_name}' location is set to '{expected_loc_canonical}', but the draft mentions '{', '.join(mismatched)}' instead."
                    ))

            # Inventory/object check
            char_inv = ch_char_invs.get(cid, [])
            sentences = re.split(r"[.!?]+", draft_text)
            for oid, obj_info in objects.items():
                if oid in char_inv:
                    continue
                obj_canonical = obj_info.get("canonical", oid)
                obj_pattern = re.compile(rf"\b{re.escape(obj_canonical)}\b", re.I)
                for sentence in sentences:
                    if pattern.search(sentence) and obj_pattern.search(sentence):
                        owner = next(
                            (other_cid for other_cid, other_inv in ch_char_invs.items() if oid in other_inv),
                            None
                        )
                        if owner and owner != cid:
                            owner_name = characters.get(owner, {}).get("canonical", owner)
                            issues.append(ManuscriptIssue(
                                severity=Severity.SOFT, category=IssueCategory.CONTINUITY,
                                chapter=ch.slug, file=ch.draft,
                                rule_id="canon_object_ownership_conflict",
                                message=f"Draft mentions '{canon_name}' using '{obj_canonical}', which belongs to '{owner_name}''s inventory."
                            ))
                            break

    return issues
