#!/usr/bin/env python3
"""BookForge Action Logistics & Gunfight Planning Core Module."""

from __future__ import annotations

import json
import re
from pathlib import Path


def discover_combat_scenes(scene_breakdown_path: Path) -> list[dict[str, str]]:
    """Finds combat scenes containing [COMBAT] tag in scene-breakdown.md.
    
    Returns a list of dicts with 'id' (slug) and 'title'.
    """
    if not scene_breakdown_path.exists():
        return []
    
    try:
        content = scene_breakdown_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    combat_scenes = []
    
    # Match headings like "## Scene 2: Showdown [COMBAT]" or "### Scene 3 [COMBAT]"
    for line in content.splitlines():
        if (line.startswith("## ") or line.startswith("### ")) and "[combat]" in line.lower():
            title = line.lstrip("#").strip()
            # Extract a slug/id like "scene-2" from "Scene 2: Showdown [COMBAT]"
            match = re.search(r"(?i)scene\s+(\d+|\w+)", title)
            if match:
                scene_id = f"scene-{match.group(1).lower()}"
            else:
                # slugify fallback
                scene_id = "scene-" + re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            
            # Remove duplicate slashes/tags for id
            scene_id = scene_id.replace("-combat", "")
            
            combat_scenes.append({
                "id": scene_id,
                "title": title
            })
    return combat_scenes


def get_action_plan_path(chapter_folder: Path, scene_id: str) -> Path:
    """Returns the path to the action plan JSON file for a given scene."""
    return chapter_folder / f"action-plan-{scene_id}.json"


def init_action_plan(chapter_folder: Path, scene_id: str) -> Path:
    """Initializes a new template action plan JSON file for the scene."""
    plan_path = get_action_plan_path(chapter_folder, scene_id)
    if plan_path.exists():
        return plan_path

    template = {
        "scene_id": scene_id,
        "combatants": {
            "Darin": {
                "weapon": "Colt Single Action Army",
                "ammo_loaded": 6,
                "spare_ammo": 12,
                "starting_cover": "wooden table",
                "health": "healthy"
            },
            "Harlan": {
                "weapon": "Winchester 1873",
                "ammo_loaded": 10,
                "spare_ammo": 15,
                "starting_cover": "bar counter",
                "health": "healthy"
            }
        },
        "shot_sequence": [
            {
                "shooter": "Harlan",
                "target": "Darin",
                "shots_fired": 1,
                "result": "miss",
                "ammo_after": 9
            },
            {
                "shooter": "Darin",
                "target": "Harlan",
                "shots_fired": 1,
                "result": "hit (shoulder)",
                "ammo_after": 5
            }
        ],
        "reloads": [
            {
                "combatant": "Darin",
                "ammo_added": 1,
                "ammo_after": 6
            }
        ],
        "injuries": {
            "Harlan": "flesh wound in right shoulder"
        },
        "post_combat_state": {
            "Darin": {
                "ammo_loaded": 6,
                "spare_ammo": 11,
                "health": "healthy"
            },
            "Harlan": {
                "ammo_loaded": 9,
                "spare_ammo": 15,
                "health": "wounded"
            }
        }
    }

    chapter_folder.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(template, indent=2), encoding="utf-8")
    return plan_path


def validate_scene_combat(draft_path: Path, plan_path: Path) -> tuple[list[str], list[str], list[str]]:
    """Validates the drafted chapter prose against the action plan JSON.
    
    Returns (passes, warnings, failures).
    """
    passes = []
    warnings = []
    failures = []

    if not plan_path.exists():
        failures.append(f"Missing action plan file: {plan_path.name}")
        return passes, warnings, failures

    if not draft_path.exists():
        failures.append(f"Missing chapter draft file: {draft_path.name}")
        return passes, warnings, failures

    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        draft = draft_path.read_text(encoding="utf-8")
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        failures.append(f"Failed to read/parse action plan or draft: {e}")
        return passes, warnings, failures

    # 1. Check combatant presence
    combatants = plan.get("combatants", {})
    for name in combatants:
        # Check if the name appears in the prose (case insensitive)
        if name.lower() not in draft.lower():
            warnings.append(f"Combatant '{name}' is in the action plan but not mentioned in the draft.")
        else:
            passes.append(f"Combatant '{name}' is mentioned in the draft.")

    # 2. Check weapons presence
    for name, data in combatants.items():
        weapon = data.get("weapon", "")
        if weapon:
            # Check for weapon brand/type mentions (e.g. Colt, Winchester, rifle, revolver)
            terms = [weapon.lower()]
            brand = weapon.split()[0].lower()
            if brand not in terms:
                terms.append(brand)
            
            # Add general synonyms
            if "winchester" in weapon.lower() or "rifle" in weapon.lower():
                terms.extend(["rifle", "lever-action"])
            if "colt" in weapon.lower() or "pistol" in weapon.lower() or "revolver" in weapon.lower():
                terms.extend(["revolver", "pistol", "six-gun", "colt", "gun"])

            if not any(term in draft.lower() for term in terms):
                warnings.append(f"Weapon '{weapon}' for combatant '{name}' is not referenced in the draft.")
            else:
                passes.append(f"Weapon '{weapon}' for combatant '{name}' is referenced in the draft.")

    # 3. Check Shot Sequence & Bullet Counts
    shot_sequence = plan.get("shot_sequence", [])
    total_plan_shots = sum(item.get("shots_fired", 0) for item in shot_sequence)
    
    # Simple count of shot/firing keywords
    shot_keywords = [
        "fired", "shot", "shoot", "shootout", "discharged", "squeezed", "cracked", "bang", "report", 
        "blast", "detonated", "let loose", "sent lead", "hammer fell", "gunfire"
    ]
    prose_shot_mentions = 0
    for word in shot_keywords:
        prose_shot_mentions += len(re.findall(rf"\b{re.escape(word)}\w*", draft.lower()))

    WEAPON_CAPACITIES = {
        "colt": 6,
        "revolver": 6,
        "six-gun": 6,
        "winchester": 15,
        "henry": 16,
        "spencer": 7,
        "remington": 6,
        "shotgun": 2,
        "derringer": 2,
        "springfield": 1
    }

    # Check for excessive ammunition usage relative to capacity
    for name, data in combatants.items():
        weapon = data.get("weapon", "").lower()
        max_cap = data.get("ammo_loaded", 6)
        for w_key, cap in WEAPON_CAPACITIES.items():
            if w_key in weapon:
                max_cap = cap
                break

        # Calculate shots fired by this person in the plan
        shooter_shots = sum(item.get("shots_fired", 0) for item in shot_sequence if item.get("shooter") == name)
        
        # Check if shooter fired more than capacity without reloads in plan
        reloads_count = sum(r.get("ammo_added", 0) for r in plan.get("reloads", []) if r.get("combatant") == name)
        
        if shooter_shots > max_cap + reloads_count:
            failures.append(
                f"Combatant '{name}' fired {shooter_shots} shots in action plan, which exceeds loaded capacity ({max_cap}) plus reloads ({reloads_count})."
            )
        else:
            passes.append(f"Combatant '{name}' plan shot counts ({shooter_shots}) are within weapon capacity constraint.")

        # Check actual prose shots vs capacity
        sentences = re.split(r"[.!?]\s+", draft)
        prose_shots = 0
        prose_reloads = 0
        active_subject = False
        
        shot_kws = ["fired", "shot", "shoot", "blasted", "discharged", "cracked", "squeezed", "let loose", "report", "bang"]
        reload_kws = ["reload", "reloaded", "reloading", "shoved", "stuffed", "fed", "loaded"]
        
        # Determine all combatant names to detect subject switching
        all_names = [n.lower() for n in combatants.keys()]
        
        for sent in sentences:
            sent_lower = sent.lower()
            if name.lower() in sent_lower:
                active_subject = True
            elif any(other in sent_lower for other in all_names if other != name.lower()):
                active_subject = False
                
            if active_subject:
                if any(kw in sent_lower for kw in shot_kws):
                    prose_shots += 1
                if any(kw in sent_lower for kw in reload_kws):
                    prose_reloads += 1
                    
        if prose_shots > max_cap and prose_reloads == 0:
            failures.append(
                f"Prose validation: Combatant '{name}' fired ~{prose_shots} times in the prose, exceeding weapon capacity ({max_cap}) without any reload described."
            )
        elif prose_shots > 0:
            passes.append(f"Prose validation: Combatant '{name}' fired {prose_shots} times (capacity {max_cap}, reloads {prose_reloads}) in the draft.")

    # Warn if the shot density seems mismatched
    if total_plan_shots > 0:
        if prose_shot_mentions == 0:
            warnings.append(
                f"Action plan lists {total_plan_shots} shots fired, but the draft does not contain any typical shooting keywords."
            )
        elif prose_shot_mentions < total_plan_shots // 2:
            warnings.append(
                f"Low shooting descriptions: Action plan lists {total_plan_shots} shots, but found only {prose_shot_mentions} mentions of firing in prose."
            )
        else:
            passes.append(f"Draft prose contains adequate shooting descriptions ({prose_shot_mentions} keywords for {total_plan_shots} planned shots).")

    # 4. Check Injuries
    injuries = plan.get("injuries", {})
    for name, injury_desc in injuries.items():
        if injury_desc and injury_desc.lower() != "none":
            # Check if name and some injury terms appear
            injury_terms = ["wound", "hit", "shatter", "blood", "bleed", "pain", "cripple", "limp", "hurt", "lead"]
            if name.lower() in draft.lower() and not any(term in draft.lower() for term in injury_terms):
                warnings.append(f"Injury for '{name}' ('{injury_desc}') is planned but no injury/pain terms found in draft.")
            else:
                passes.append(f"Injury for '{name}' is referenced in draft.")

    return passes, warnings, failures
