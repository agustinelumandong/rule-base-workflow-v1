#!/usr/bin/env python3
"""Unit tests for BookForge Event-Sourced Canon Core."""

import unittest
import tempfile
import shutil
import yaml
import json
from pathlib import Path

from bookforge.core import canon
from bookforge.core.issue import Severity


class TestCanonCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.canon_dir = self.temp_dir / "canon"
        self.entities_dir = self.canon_dir / "entities"
        self.events_dir = self.canon_dir / "events"
        self.state_dir = self.canon_dir / "state"

        self.entities_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Write dummy entities
        self.chars = {
            "harlan": {
                "canonical": "Harlan",
                "status": "alive",
                "location": "saloon",
                "inventory": ["colt_peacemaker"]
            },
            "darin": {
                "canonical": "Darin",
                "status": "alive",
                "location": "camp",
                "inventory": []
            }
        }
        self.locs = {
            "saloon": {"canonical": "The Dusty Mug Saloon"},
            "camp": {"canonical": "The Creek Camp"},
            "canyon": {"canonical": "The Alkali Canyon"}
        }
        self.objs = {
            "colt_peacemaker": {"canonical": "Colt Peacemaker"}
        }
        self.aliases = {
            "darin": "darin",
            "harlan": "harlan"
        }

        with open(self.entities_dir / "characters.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump({"characters": self.chars}, f)
        with open(self.entities_dir / "locations.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump({"locations": self.locs}, f)
        with open(self.entities_dir / "objects.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump({"objects": self.objs}, f)
        with open(self.entities_dir / "aliases.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump({"aliases": self.aliases}, f)

        # Write dummy chapter events
        self.ch1_events = {
            "chapter": 1,
            "events": [
                {
                    "type": "character_mutation",
                    "character_id": "harlan",
                    "location": "camp"
                },
                {
                    "type": "character_mutation",
                    "character_id": "darin",
                    "location": "camp",
                    "inventory_added": ["colt_peacemaker"]
                }
            ]
        }
        with open(self.events_dir / "chapter-01.event.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(self.ch1_events, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_fold_canon_deterministic(self):
        # Run fold
        snapshot = canon.fold_canon(self.temp_dir)

        # Verify state updates
        self.assertEqual(snapshot["characters"]["harlan"]["location"], "camp")
        self.assertIn("colt_peacemaker", snapshot["characters"]["darin"]["inventory"])

        # Verify snapshot file exists
        snapshot_file = self.state_dir / "snapshot.yml"
        self.assertTrue(snapshot_file.exists())
        with open(snapshot_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.assertEqual(data["characters"]["harlan"]["location"], "camp")

    def test_injury_healing_decay(self):
        # Set harlan with healing chapters remaining in initial schema inside injuries dict
        self.chars["harlan"]["injuries"] = {
            "broken_leg": {
                "healing_chapters_remaining": 3,
                "status": "active"
            }
        }
        with open(self.entities_dir / "characters.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump({"characters": self.chars}, f)

        # Add event that doesn't affect healing to verify auto-decay
        snapshot = canon.fold_canon(self.temp_dir)
        self.assertEqual(snapshot["characters"]["harlan"]["injuries"]["broken_leg"]["healing_chapters_remaining"], 2)

    def test_canon_validation_clean(self):
        # Create a clean draft matching the final folded state
        # Harlan is at camp, Darin is at camp (with colt_peacemaker)
        chapters_dir = self.temp_dir / "chapters" / "chapter-01"
        chapters_dir.mkdir(parents=True, exist_ok=True)
        draft_file = chapters_dir / "chapter-01.md"
        draft_file.write_text("Harlan stood at the Creek Camp, holding nothing. Darin checked his Colt Peacemaker.", encoding="utf-8")

        issues = canon.validate_canon(self.temp_dir)
        self.assertEqual(len(issues), 0)

    def test_canon_validation_dead_actor_dialogue(self):
        # Set status to dead in a chapter event
        dead_event = {
            "chapter": 2,
            "events": [
                {
                    "type": "character_status",
                    "character_id": "darin",
                    "status": "dead"
                }
            ]
        }
        with open(self.events_dir / "chapter-02.event.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(dead_event, f)

        # Create draft where Darin speaks
        chapters_dir = self.temp_dir / "chapters" / "chapter-02"
        chapters_dir.mkdir(parents=True, exist_ok=True)
        draft_file = chapters_dir / "chapter-02.md"
        draft_file.write_text("Darin said, \"I'm still here.\"", encoding="utf-8")

        issues = canon.validate_canon(self.temp_dir)
        hard_issues = [i for i in issues if i.severity == Severity.HARD]
        self.assertTrue(any("dead character" in i.message.lower() for i in hard_issues))

    def test_canon_validation_unresolved_alias(self):
        chapters_dir = self.temp_dir / "chapters" / "chapter-01"
        chapters_dir.mkdir(parents=True, exist_ok=True)
        draft_file = chapters_dir / "chapter-01.md"
        # "Vance" is not registered in characters, locations, or aliases
        draft_file.write_text("Vance rode into town.", encoding="utf-8")

        issues = canon.validate_canon(self.temp_dir)
        soft_issues = [i for i in issues if i.severity == Severity.SOFT]
        self.assertTrue(any("proper noun 'vance'" in i.message.lower() for i in soft_issues))

    def test_migrate_legacy_book(self):
        # Write legacy files
        legacy_world = {
            "characters": {
                "mara": {
                    "location": "stables",
                    "inventory": ["winchester_73"],
                    "status": "alive"
                }
            },
            "locations": ["stables", "town"]
        }
        legacy_rel = {
            "mara_harlan": {
                "subject": "mara",
                "relation": "distrusts",
                "object": "harlan"
            }
        }
        with open(self.temp_dir / "world-state.json", "w", encoding="utf-8") as f:
            json.dump(legacy_world, f)
        with open(self.temp_dir / "relationships.json", "w", encoding="utf-8") as f:
            json.dump(legacy_rel, f)

        # Run migration
        canon.migrate_legacy_book(self.temp_dir)

        # Verify migrated files exist
        self.assertTrue((self.entities_dir / "characters.yml").exists())
        self.assertTrue((self.entities_dir / "locations.yml").exists())
        self.assertTrue((self.entities_dir / "aliases.yml").exists())

        # Load migrated character to verify
        with open(self.entities_dir / "characters.yml", "r", encoding="utf-8") as f:
            migrated_chars = yaml.safe_load(f)
            self.assertIn("mara", migrated_chars.get("characters", {}))
            self.assertEqual(migrated_chars.get("characters", {}).get("mara", {}).get("relationships", {}).get("harlan"), "distrusts")

    def test_parse_continuity_out_to_event(self):
        cont_text = """
## Unresolved Stakes
- Mara is angry at Tex

## Characters
- mara dead
- Tex moves to canyon
        """
        cont_path = self.temp_dir / "continuity-out.md"
        cont_path.write_text(cont_text, encoding="utf-8")

        events = canon.parse_continuity_out_to_event(cont_path)
        ev_list = events.get("events", [])
        self.assertTrue(any(e.get("type") == "character_status" and e.get("character_id") == "mara" and e.get("status") == "dead" for e in ev_list))
        self.assertTrue(any(e.get("type") == "stakes" for e in ev_list))


if __name__ == "__main__":
    unittest.main()
