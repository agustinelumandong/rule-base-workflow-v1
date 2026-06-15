#!/usr/bin/env python3
"""BookForge Interactive Repair Wizard Core Module."""

from __future__ import annotations

import re
import sys
from pathlib import Path
import json

from bookforge.core import validator as context_validator
from bookforge.core import scanner as scanner_module
from bookforge.core import world as world_module


def insert_tag_in_scene(breakdown_path: Path, scene_title: str, tag: str) -> bool:
    """Inserts a tag (e.g. * [TRAVEL: ...]) into the matching scene header in scene-breakdown.md."""
    if not breakdown_path.exists():
        return False
        
    content = breakdown_path.read_text(encoding="utf-8")
    
    # Split content by scene headers (e.g., ## Scene 1 or ### Scene 1)
    # Using lookahead to keep the headers in split parts
    parts = re.split(r"(?m)^(?=##|###)", content)
    
    modified = False
    new_parts = []
    
    for part in parts:
        # Check if this part belongs to the target scene
        # We clean the header to match the scene_title
        lines = part.splitlines()
        if lines and re.search(re.escape(scene_title), lines[0], re.IGNORECASE):
            # Insert the tag right after the header line (or after location/pov metadata)
            insert_idx = 1
            # Find the best insertion point (after standard metadata bullet points)
            for idx, line in enumerate(lines[1:], 1):
                if line.strip().startswith(("* Location:", "* POV:", "* Character Locations:")):
                    insert_idx = idx + 1
                else:
                    break
            lines.insert(insert_idx, f"* {tag}")
            part = "\n".join(lines)
            modified = True
        new_parts.append(part)
        
    if modified:
        breakdown_path.write_text("\n".join(new_parts), encoding="utf-8")
        return True
        
    return False


def run_repair_wizard(book_folder: Path, chapter_slug: str) -> int:
    """Runs the interactive repair wizard CLI flow."""
    print(f"\n=== BookForge Repair Wizard: {chapter_slug} ===")
    
    # 1. Discover target chapter
    chapters = context_validator.discover_chapters(book_folder)
    target_chap = None
    for c in chapters:
        if c.slug == chapter_slug:
            target_chap = c
            break
            
    if not target_chap:
        print(f"Error: Chapter slug '{chapter_slug}' not found in {book_folder}/chapters", file=sys.stderr)
        return 1

    # Load source outline sections
    outline_path = scanner_module.source_path(book_folder)
    phase_sections = {}
    if outline_path:
        phase_sections = scanner_module.scan_source_sections(outline_path.read_text(encoding="utf-8"))

    while True:
        report = context_validator.validate_chapter(target_chap, phase_sections)
        failures = report.failures
        
        # Filter for repairable logistics/world state failures
        repairable = []
        for f in failures:
            # Match: [Scene 1: The Stables] Teleportation Error: ...
            # Match: [Scene 2: The Saloon] Inventory Inconsistency: ...
            match = re.match(r"^\[([^\]]+)\]\s+(Teleportation Error|Inventory Inconsistency):\s+(.*)$", f)
            if match:
                repairable.append({
                    "raw": f,
                    "scene": match.group(1),
                    "type": match.group(2),
                    "details": match.group(3)
                })

        if not repairable:
            print(f"\n[PASS] No repairable logistics failures remaining in {chapter_slug}!")
            break

        print(f"\nFound {len(repairable)} repairable logistics failure(s):")
        for idx, item in enumerate(repairable, 1):
            print(f"  {idx}. [{item['scene']}] {item['type']}: {item['details']}")
            
        print(f"\nSelect a failure to repair (1-{len(repairable)}) or press 'q' to quit: ", end="")
        sys.stdout.flush()
        choice = sys.stdin.readline().strip().lower()
        if choice == 'q':
            print("Exiting repair wizard.")
            break
            
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(repairable):
                print("Invalid selection.")
                continue
        except ValueError:
            print("Invalid input.")
            continue

        selected = repairable[choice_idx]
        scene_name = selected["scene"]
        details = selected["details"]
        
        if selected["type"] == "Teleportation Error":
            # Parse: Harlan is traveling from 'sheriff_office' but their current location is 'saloon'
            travel_match = re.search(r"(\w+)\s+is\s+traveling\s+from\s+'([^']+)'\s+but\s+their\s+current\s+location\s+is\s+'([^']+)'", details, re.IGNORECASE)
            if travel_match:
                char = travel_match.group(1).lower()
                frm = travel_match.group(2).lower()
                current = travel_match.group(3).lower()
                
                print(f"\n--- Repair Teleportation Error: {char.capitalize()} ---")
                print(f"  Current known location: '{current}'")
                print(f"  Attempted departure:    '{frm}'")
                print("\nOptions:")
                print(f"  1. Insert travel transition: `[TRAVEL: {char} from {current} to {frm}]` at start of '{scene_name}'")
                print(f"  2. Force change {char.capitalize()}'s location to '{frm}' in world-state.json")
                print("  3. Cancel")
                
                print("Choose option (1-3): ", end="")
                sys.stdout.flush()
                opt = sys.stdin.readline().strip()
                
                if opt == '1':
                    tag = f"[TRAVEL: {char} from {current} to {frm}]"
                    if insert_tag_in_scene(target_chap.scene_breakdown, scene_name, tag):
                        print(f"✔ Successfully inserted transition tag to scene breakdown.")
                    else:
                        print("✘ Error inserting tag.")
                elif opt == '2':
                    world_state = world_module.load_world_state(book_folder)
                    if char in world_state.get("characters", {}):
                        world_state["characters"][char]["location"] = frm
                        world_module.save_world_state(book_folder, world_state)
                        print(f"✔ Successfully moved {char.capitalize()} to '{frm}' in world-state.json.")
                    else:
                        print(f"Character {char} not found in world state.")
                else:
                    print("Repair cancelled.")
                    
        elif selected["type"] == "Inventory Inconsistency":
            # Parse: Harlan uses a 'winchester_rifle' in the prose but does not own it (possesses: [...])
            inv_match = re.search(r"(\w+)\s+uses\s+a\s+'([^']+)'\s+in\s+the\s+prose\s+but\s+does\s+not\s+own\s+it", details, re.IGNORECASE)
            if inv_match:
                char = inv_match.group(1).lower()
                item = inv_match.group(2).lower()
                
                print(f"\n--- Repair Inventory Inconsistency: {char.capitalize()} ---")
                print(f"  Missing item: '{item}'")
                print("\nOptions:")
                print(f"  1. Insert acquire transition: `[ACQUIRE: {char} {item}]` at start of '{scene_name}'")
                print(f"  2. Add '{item}' directly to {char.capitalize()}'s inventory in world-state.json")
                print("  3. Cancel")
                
                print("Choose option (1-3): ", end="")
                sys.stdout.flush()
                opt = sys.stdin.readline().strip()
                
                if opt == '1':
                    tag = f"[ACQUIRE: {char} {item}]"
                    if insert_tag_in_scene(target_chap.scene_breakdown, scene_name, tag):
                        print(f"✔ Successfully inserted acquire tag to scene breakdown.")
                    else:
                        print("✘ Error inserting tag.")
                elif opt == '2':
                    world_state = world_module.load_world_state(book_folder)
                    if char in world_state.get("characters", {}):
                        if item not in world_state["characters"][char]["inventory"]:
                            world_state["characters"][char]["inventory"].append(item)
                        world_module.save_world_state(book_folder, world_state)
                        print(f"✔ Successfully added '{item}' to {char.capitalize()}'s inventory.")
                    else:
                        print(f"Character {char} not found in world state.")
                else:
                    print("Repair cancelled.")
                    
    return 0
