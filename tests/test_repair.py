#!/usr/bin/env python3
"""Unit tests for BookForge Interactive Repair Wizard."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json
import shutil

from bookforge.core import repair
from bookforge.core import validator as context_validator


class TestRepairWizard(unittest.TestCase):
    def setUp(self):
        # Create temp workspace
        self.test_dir = Path(tempfile.mkdtemp())
        self.book_folder = self.test_dir / "my-book"
        self.book_folder.mkdir()
        
        # Setup basic directories
        self.chapters_dir = self.book_folder / "chapters"
        self.chapters_dir.mkdir()
        self.chap_dir = self.chapters_dir / "chapter-01"
        self.chap_dir.mkdir()

        # Write dummy files
        self.breakdown_path = self.chap_dir / "scene-breakdown.md"
        self.breakdown_content = """# Scene Breakdown chapter-01

## Scene 1: The Saloon
* Location: saloon
* POV: Harlan
* Character Locations: harlan:saloon

This is the first scene.

## Scene 2: The Stables
* Location: stables
* POV: Harlan
* Character Locations: harlan:stables

This is the second scene.
"""
        self.breakdown_path.write_text(self.breakdown_content, encoding="utf-8")
        
        self.draft_path = self.chap_dir / "chapter-01.md"
        self.draft_path.write_text("# Chapter 01\n\nDraft content.\n", encoding="utf-8")
        
        # Write dummy world-state.json
        self.world_state_path = self.book_folder / "world-state.json"
        self.world_state = {
            "characters": {
                "harlan": {
                    "location": "saloon",
                    "inventory": ["colt_45"]
                }
            }
        }
        self.world_state_path.write_text(json.dumps(self.world_state, indent=2), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_insert_tag_in_scene(self):
        tag = "[TRAVEL: harlan from saloon to stables]"
        success = repair.insert_tag_in_scene(self.breakdown_path, "Scene 1: The Saloon", tag)
        self.assertTrue(success)
        
        new_content = self.breakdown_path.read_text(encoding="utf-8")
        self.assertIn("* [TRAVEL: harlan from saloon to stables]", new_content)
        # Ensure it went under Scene 1, not Scene 2
        lines = new_content.splitlines()
        scene_1_idx = [i for i, line in enumerate(lines) if "## Scene 1" in line][0]
        scene_2_idx = [i for i, line in enumerate(lines) if "## Scene 2" in line][0]
        tag_idx = [i for i, line in enumerate(lines) if tag in line][0]
        self.assertTrue(scene_1_idx < tag_idx < scene_2_idx)

    @patch("sys.stdin.readline")
    @patch("bookforge.core.validator.validate_chapter")
    def test_run_repair_wizard_teleport(self, mock_validate, mock_readline):
        # Setup mock report
        mock_chapter = context_validator.discover_chapters(self.book_folder)[0]
        
        # Setup mock validate_chapter outputs
        # 1st call: returns teleportation failure
        # 2nd call: returns no failures (simulating successful fix)
        report_fail = MagicMock()
        report_fail.failures = ["[Scene 2: The Stables] Teleportation Error: Harlan is traveling from 'sheriff_office' but their current location is 'saloon'."]
        
        report_pass = MagicMock()
        report_pass.failures = []
        
        mock_validate.side_effect = [report_fail, report_pass]
        
        # Simulate user selecting option 1 (insert tag) for failure 1, then 'q' just in case
        mock_readline.side_effect = ["1", "1", "q"]
        
        code = repair.run_repair_wizard(self.book_folder, "chapter-01")
        self.assertEqual(code, 0)
        
        # Verify tag was inserted into scene-breakdown
        updated_content = self.breakdown_path.read_text(encoding="utf-8")
        self.assertIn("[TRAVEL: harlan from saloon to sheriff_office]", updated_content)


if __name__ == "__main__":
    unittest.main()
