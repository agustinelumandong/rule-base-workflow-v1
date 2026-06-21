#!/usr/bin/env python3
"""Unit tests for BookForge World State and Physical Logistics validation."""

import unittest
import tempfile
import json
import shutil
from pathlib import Path

from bookforge.core import world


class TestWorldLogistics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Write default world-state.json
        self.world_state = {
            "characters": {
                "harlan": {
                    "location": "saloon",
                    "inventory": ["colt_45", "silver_pocket_watch"],
                    "status": "alive"
                },
                "darin": {
                    "location": "saloon",
                    "inventory": ["winchester_rifle"],
                    "status": "alive"
                }
            },
            "locations": ["saloon", "stables", "sheriff_office", "dusty_road"]
        }
        (self.temp_dir / "world-state.json").write_text(json.dumps(self.world_state, indent=2), encoding="utf-8")
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_save_world_state(self):
        # Initial load (default)
        state = world.load_world_state(self.temp_dir)
        self.assertIn("harlan", state["characters"])
        self.assertEqual(state["characters"]["harlan"]["location"], "saloon")
        
        # Modify and save
        state["characters"]["harlan"]["location"] = "stables"
        world.save_world_state(self.temp_dir, state)
        
        # Reload and verify
        reloaded = world.load_world_state(self.temp_dir)
        self.assertEqual(reloaded["characters"]["harlan"]["location"], "stables")

    def test_parse_scene_transitions(self):
        scene_text = """
        ### Scene 1: The Poker Room
        * Location: saloon
        
        [TRAVEL: harlan from saloon to stables]
        [TRANSFER: silver_pocket_watch from darin to harlan]
        [GIVE: colt_45 from harlan to darin]
        [ACQUIRE: map by harlan]
        [LOSE: colt_45 from harlan]
        [INJURE: darin with shoulder wound]
        [KILL: darin]
        """
        transitions = world.parse_scene_transitions(scene_text)
        self.assertEqual(len(transitions), 7)
        
        self.assertEqual(transitions[0], {"type": "travel", "character": "harlan", "from": "saloon", "to": "stables"})
        self.assertEqual(transitions[1], {"type": "transfer", "item": "silver_pocket_watch", "from": "darin", "to": "harlan"})
        self.assertEqual(transitions[2], {"type": "transfer", "item": "colt_45", "from": "harlan", "to": "darin"})
        self.assertEqual(transitions[3], {"type": "acquire", "item": "map", "character": "harlan"})
        self.assertEqual(transitions[4], {"type": "lose", "item": "colt_45", "character": "harlan"})
        self.assertEqual(transitions[5], {"type": "injure", "character": "darin", "detail": "shoulder wound"})
        self.assertEqual(transitions[6], {"type": "kill", "character": "darin"})

    def test_validate_scene_world_state_valid(self):
        # Valid travel
        scene = {
            "location": "stables",
            "transitions": [
                {"type": "travel", "character": "harlan", "from": "saloon", "to": "stables"}
            ]
        }
        draft = "Harlan walked slowly into the stables, checking the horses."
        
        failures, warnings = world.validate_scene_world_state(scene, draft, self.world_state)
        self.assertEqual(len(failures), 0)
        self.assertEqual(len(warnings), 0)
        self.assertEqual(self.world_state["characters"]["harlan"]["location"], "stables")

    def test_validate_scene_world_state_teleportation(self):
        # Invalid travel (teleportation)
        scene = {
            "location": "stables",
            "transitions": [
                {"type": "travel", "character": "harlan", "from": "sheriff_office", "to": "stables"}
            ]
        }
        draft = "Harlan appeared in the stables."
        
        failures, warnings = world.validate_scene_world_state(scene, draft, self.world_state)
        self.assertEqual(len(failures), 1)
        self.assertIn("Teleportation Error", failures[0])

    def test_validate_scene_world_state_inventory_transfer(self):
        # Valid transfer
        scene = {
            "location": "saloon",
            "transitions": [
                {"type": "transfer", "item": "silver_pocket_watch", "from": "harlan", "to": "darin"}
            ]
        }
        draft = "Harlan handed the silver pocket watch to Darin."
        
        failures, warnings = world.validate_scene_world_state(scene, draft, self.world_state)
        self.assertEqual(len(failures), 0)
        self.assertNotIn("silver_pocket_watch", self.world_state["characters"]["harlan"]["inventory"])
        self.assertIn("silver_pocket_watch", self.world_state["characters"]["darin"]["inventory"])

    def test_validate_scene_world_state_missing_inventory(self):
        # Invalid transfer (missing item)
        scene = {
            "location": "saloon",
            "transitions": [
                {"type": "transfer", "item": "gold_coin", "from": "harlan", "to": "darin"}
            ]
        }
        draft = "Harlan tried to give a gold coin."
        
        failures, warnings = world.validate_scene_world_state(scene, draft, self.world_state)
        self.assertEqual(len(failures), 1)
        self.assertIn("Missing Inventory Item", failures[0])

    def test_validate_scene_world_state_prose_inventory_violation(self):
        # Harlan tries to use/shoot a winchester rifle, which he does not own
        scene = {
            "location": "saloon",
            "transitions": []
        }
        # "Harlan fired his Winchester rifle" -> should trigger inventory warning/failure
        draft = "Harlan fired his winchester rifle into the ceiling."
        
        failures, warnings = world.validate_scene_world_state(scene, draft, self.world_state)
        self.assertEqual(len(failures), 1)
        self.assertIn("Inventory Inconsistency", failures[0])
        
    def test_validate_scene_world_state_location_warning(self):
        # Darin is mentioned in draft at stables but he is at saloon
        scene = {
            "location": "stables",
            "transitions": []
        }
        draft = "Harlan looked at Darin standing next to him in the stables."
        
        failures, warnings = world.validate_scene_world_state(scene, draft, self.world_state)
        self.assertEqual(len(failures), 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Location Inconsistency", warnings[0])


if __name__ == "__main__":
    unittest.main()
