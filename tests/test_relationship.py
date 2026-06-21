#!/usr/bin/env python3
"""Unit tests for BookForge Typed Relationships and Graph Memory."""

import unittest
from pathlib import Path
import tempfile
import json
import shutil

from bookforge.core import relationship as relationship_module
from bookforge.core import packet as packet_module
from bookforge.core import validator as context_validator


class TestTypedRelationships(unittest.TestCase):
    def setUp(self):
        workspace_tmp = Path(__file__).resolve().parent / "tmp_test_dir"
        workspace_tmp.mkdir(exist_ok=True)
        self.test_dir = Path(tempfile.mkdtemp(dir=str(workspace_tmp)))
        self.book_folder = self.test_dir / "my-book"
        self.book_folder.mkdir()
        
        # Setup basic folders
        self.chapters_dir = self.book_folder / "chapters"
        self.chapters_dir.mkdir()
        self.chap_dir = self.chapters_dir / "chapter-01"
        self.chap_dir.mkdir()
        
        # Setup world state
        self.world_state_path = self.book_folder / "world-state.json"
        self.world_state = {
            "characters": {
                "harlan": {"location": "saloon", "inventory": ["colt_45"], "status": "alive"},
                "darin": {"location": "saloon", "inventory": [], "status": "alive"}
            },
            "locations": ["saloon"]
        }
        self.world_state_path.write_text(json.dumps(self.world_state, indent=2), encoding="utf-8")

        # Setup scene breakdown
        self.breakdown_path = self.chap_dir / "scene-breakdown.md"
        self.breakdown_content = """# Scene Breakdown

## Scene 1: The Meet
* Location: saloon
* POV: Harlan
* Character Locations: harlan:saloon, darin:saloon
"""
        self.breakdown_path.write_text(self.breakdown_content, encoding="utf-8")

        # Setup basic rulebook template
        self.rulebook_path = self.book_folder / "rulebook.md"
        self.rulebook_content = """# Book Rules

## Characters
- **Harlan**: The protagonist.
- **Darin**: The secondary character.
"""
        self.rulebook_path.write_text(self.rulebook_content, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_save_add_relationship(self):
        # Empty originally
        rels = relationship_module.load_relationships(self.book_folder)
        self.assertEqual(len(rels), 0)

        # Add one relationship
        relationship_module.add_relationship(
            book_folder=self.book_folder,
            subject="harlan",
            relation="distrusts",
            obj="darin",
            source_artifact="chapter-01"
        )

        rels = relationship_module.load_relationships(self.book_folder)
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]["subject"], "harlan")
        self.assertEqual(rels[0]["relation"], "distrusts")
        self.assertEqual(rels[0]["object"], "darin")

    def test_validate_conflict_rule(self):
        scene = {
            "id": "scene-1",
            "title": "Scene 1: The Meet",
            "character_locations": "harlan:saloon, darin:saloon"
        }
        
        # Valid prose
        prose_ok = "Harlan glared at Darin. They stood in the dust."
        failures, warnings = relationship_module.validate_relationships_prose(
            scene=scene,
            scene_draft=prose_ok,
            relationships=[{"subject": "harlan", "relation": "distrusts", "object": "darin"}]
        )
        self.assertEqual(len(failures), 0)

        # Friendly prose should fail
        prose_fail = "Harlan smiled. \"Get in here,\" he laughed, and they hugged. Darin was his partner."
        failures, warnings = relationship_module.validate_relationships_prose(
            scene=scene,
            scene_draft=prose_fail,
            relationships=[{"subject": "harlan", "relation": "distrusts", "object": "darin"}]
        )
        self.assertTrue(len(failures) > 0)
        self.assertIn("Relationship Conflict Failure", failures[0])

    def test_validate_knowledge_boundary_rule(self):
        scene = {
            "id": "scene-1",
            "title": "Scene 1: The Meet",
            "character_locations": "harlan:saloon, darin:saloon"
        }

        # Darin does not know about Harlan's silver watch secret
        relationships = [{"subject": "silver_watch", "relation": "does_not_know", "object": "darin"}]

        # Ok prose: Darin talks about the weather
        prose_ok = "Darin asked for water."
        failures, warnings = relationship_module.validate_relationships_prose(
            scene=scene,
            scene_draft=prose_ok,
            relationships=relationships
        )
        self.assertEqual(len(failures), 0)

        # Bad prose: Darin references the silver watch
        prose_fail = "Darin wanted the silver_watch. He reached for it."
        failures, warnings = relationship_module.validate_relationships_prose(
            scene=scene,
            scene_draft=prose_fail,
            relationships=relationships
        )
        self.assertTrue(len(failures) > 0)
        self.assertIn("Knowledge Boundary Failure", failures[0])

    def test_context_injection(self):
        # Add a relationship
        relationship_module.add_relationship(
            book_folder=self.book_folder,
            subject="harlan",
            relation="distrusts",
            obj="darin"
        )
        
        # Build context packet
        packet = packet_module.build_context_packet(
            book_folder=self.book_folder,
            rulebook_text=self.rulebook_content,
            scene_breakdown_text=self.breakdown_content,
            slug="chapter-01"
        )
        
        # Verify relationship section is in context packet
        self.assertIn("Active Character Relationships", packet)
        self.assertIn("- **harlan** distrusts **darin**", packet)

    def test_subgenre_context_injection(self):
        # Configure subgenre in world-state.json
        self.world_state["genre"] = "western"
        self.world_state["subgenre"] = "classic"
        self.world_state_path.write_text(json.dumps(self.world_state, indent=2), encoding="utf-8")
        
        # Build context packet
        packet = packet_module.build_context_packet(
            book_folder=self.book_folder,
            rulebook_text=self.rulebook_content,
            scene_breakdown_text=self.breakdown_content,
            slug="chapter-01"
        )
        # Check classic guidelines are injected
        self.assertIn("Active Subgenre Guidelines: Western (Classic)", packet)
        self.assertIn("Tone: heroic, moral, direct", packet)

    def test_historical_etymology_validator(self):
        # Create setting with year 1850
        phase_0_content = """# Title
- **Historical / Time Period:** 1850
"""
        (self.book_folder / "phase-0.md").write_text(phase_0_content, encoding="utf-8")
        
        # Create draft with anachronistic word 'flashlight' (invented in 1899)
        draft_path = self.chap_dir / "draft.md"
        draft_path.write_text("Harlan lit his flashlight.", encoding="utf-8")
        
        from bookforge.core import validator as val_module
        from bookforge.core.validator import ChapterFiles
        
        chap_files = ChapterFiles(self.chap_dir)
        issues = val_module.validate_draft(chap_files)
        
        # Verify etymology warning is raised
        self.assertTrue(any("flashlight" in issue.message for issue in issues))

    def test_prose_weapon_capacity(self):
        # Create a mock action plan with combatants using colt revolver (capacity 6)
        plan_path = self.chap_dir / "action-plan-scene-1.json"
        plan_data = {
            "combatants": {
                "harlan": {"weapon": "colt revolver", "ammo_loaded": 6}
            },
            "shot_sequence": [
                {"shooter": "harlan", "shots_fired": 3}
            ],
            "reloads": []
        }
        plan_path.write_text(json.dumps(plan_data, indent=2), encoding="utf-8")
        
        # Prose draft with Harlan firing 7 shots without reload
        draft_path = self.chap_dir / "draft.md"
        draft_path.write_text("Harlan fired. He fired again. He shot. Harlan shot his gun. Harlan shot the wall. Harlan shot the glass. Harlan shot again.", encoding="utf-8")
        
        from bookforge.core import action as action_module
        passes, warnings, failures = action_module.validate_scene_combat(draft_path, plan_path)
        
        # Verify weapon capacity failure is raised
        self.assertTrue(any("exceeding weapon capacity" in f for f in failures))

    def test_nested_outline_structure(self):
        # Create a nested outline folder structure
        book_folder = self.test_dir / "nested-book"
        book_folder.mkdir()
        phase_0_dir = book_folder / "phase-0"
        phase_0_dir.mkdir()
        
        outline_file = phase_0_dir / "my-series-outline.md"
        outline_file.write_text("# Nested Series Outline", encoding="utf-8")
        
        from bookforge.core.scanner import source_path
        resolved_path = source_path(book_folder)
        
        # Verify it resolves to the nested file
        self.assertEqual(resolved_path, outline_file)


if __name__ == "__main__":
    unittest.main()
