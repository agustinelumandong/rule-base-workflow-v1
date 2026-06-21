#!/usr/bin/env python3
"""Unit tests for the BookForge Action Logistics and Combat validation."""

import json
import unittest
import shutil
from pathlib import Path

from bookforge.core import action


class TestActionLogistics(unittest.TestCase):
    def setUp(self):
        # Create a workspace-friendly temp directory
        self.tmp_dir = Path("tests/temp_test_action")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        self.scene_breakdown_path = self.tmp_dir / "scene-breakdown.md"
        self.draft_path = self.tmp_dir / "chapter-01.md"
        self.plan_path = self.tmp_dir / "action-plan-scene-2.json"

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_discover_combat_scenes(self):
        breakdown_content = """# Chapter 1 Breakdown

## Scene 1: Arrival
Normal travel scenes.

### Scene 2: Showdown [COMBAT]
Darin meets Harlan at the saloon.

## Scene 3 [combat]: Escape
Escaping under cover of smoke.
"""
        self.scene_breakdown_path.write_text(breakdown_content, encoding="utf-8")
        
        scenes = action.discover_combat_scenes(self.scene_breakdown_path)
        self.assertEqual(len(scenes), 2)
        
        self.assertEqual(scenes[0]["id"], "scene-2")
        self.assertEqual(scenes[0]["title"], "Scene 2: Showdown [COMBAT]")
        
        self.assertEqual(scenes[1]["id"], "scene-3")
        self.assertEqual(scenes[1]["title"], "Scene 3 [combat]: Escape")

    def test_init_action_plan(self):
        plan_file = action.init_action_plan(self.tmp_dir, "scene-2")
        self.assertTrue(plan_file.exists())
        self.assertEqual(plan_file.name, "action-plan-scene-2.json")
        
        # Parse it to make sure it's valid JSON
        data = json.loads(plan_file.read_text(encoding="utf-8"))
        self.assertEqual(data["scene_id"], "scene-2")
        self.assertIn("Darin", data["combatants"])

    def test_validate_scene_combat_pass(self):
        # Initialize standard template action plan
        action.init_action_plan(self.tmp_dir, "scene-2")
        
        # Create a matching draft prose
        draft_content = """
Darin drew his Colt Single Action Army revolver and fired a shot, the bullet missing Harlan by an inch.
Harlan was crouched behind the bar counter. He raised his Winchester 1873 rifle and cracked a shot back.
Darin took cover behind the wooden table, squeezed another round, and the lead hit Harlan in the right shoulder, 
leaving a flesh wound and blood running down his sleeve.
"""
        self.draft_path.write_text(draft_content, encoding="utf-8")
        
        passes, warnings, failures = action.validate_scene_combat(self.draft_path, self.plan_path)
        
        self.assertEqual(len(failures), 0)
        # Verify combatants and weapons passed checks
        self.assertTrue(any("Darin" in p for p in passes))
        self.assertTrue(any("Harlan" in p for p in passes))
        self.assertTrue(any("Colt" in p or "referenced" in p for p in passes))

    def test_validate_scene_combat_fails(self):
        # Setup plan where Darin has capacity of 6 shots and 0 reloads, but fires 8 shots in sequence
        plan_data = {
            "scene_id": "scene-2",
            "combatants": {
                "Darin": {
                    "weapon": "Colt .45",
                    "ammo_loaded": 6,
                    "spare_ammo": 6,
                    "starting_cover": "wood",
                    "health": "healthy"
                }
            },
            "shot_sequence": [
                {"shooter": "Darin", "target": "Harlan", "shots_fired": 8, "result": "miss", "ammo_after": -2}
            ],
            "reloads": [],
            "injuries": {}
        }
        self.plan_path.write_text(json.dumps(plan_data), encoding="utf-8")
        
        # Draft with no Colt reference
        draft_content = "Darin stood in the street and fired some shots."
        self.draft_path.write_text(draft_content, encoding="utf-8")
        
        passes, warnings, failures = action.validate_scene_combat(self.draft_path, self.plan_path)
        
        # Must fail because Darin fired more than capacity (8 > 6)
        self.assertTrue(any("exceeds loaded capacity" in f for f in failures))
        # Must warn about missing weapon brand
        self.assertTrue(any("Colt" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
