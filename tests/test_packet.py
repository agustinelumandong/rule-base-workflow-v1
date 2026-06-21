#!/usr/bin/env python3
"""Unit tests for BookForge smart context selection (character profile optimization)."""

import unittest
import tempfile
import json
import shutil
from pathlib import Path

from bookforge.core import packet


class TestSmartContextSelection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Write default world-state.json
        self.world_state = {
            "characters": {
                "harlan": {
                    "location": "saloon",
                    "inventory": ["colt_45"],
                    "status": "alive"
                },
                "darin": {
                    "location": "saloon",
                    "inventory": ["winchester_rifle"],
                    "status": "alive"
                }
            },
            "locations": ["saloon", "stables"]
        }
        (self.temp_dir / "world-state.json").write_text(json.dumps(self.world_state, indent=2), encoding="utf-8")
        
        # Write mock rulebook.md with character profiles
        self.rulebook_content = """# Rulebook
        
## Dramatis Personae
        
### Harlan
Harlan is a quiet gunman. He wears leather boots and carries a Colt.
        
### Darin
Darin Mayweather is a sheriff's deputy. He distrusts Harlan and carries a Winchester.
        
## Source Hierarchy
Always follow outline.
"""
        (self.temp_dir / "rulebook.md").write_text(self.rulebook_content, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_optimize_character_profiles(self):
        char_section = """
### Harlan
Harlan is a quiet gunman. He wears leather boots.

### Darin
Darin Mayweather is a sheriff's deputy.
"""
        # Exclude Darin (only Harlan is active)
        opt_text = packet.optimize_character_profiles(char_section, ["harlan"], ["harlan", "darin"])
        
        self.assertIn("Harlan", opt_text)
        self.assertNotIn("Darin Mayweather", opt_text)
        self.assertIn("[Profile for inactive character 'Darin' excluded to optimize context budget]", opt_text)

    def test_relevant_rulebook_excerpt_filtering(self):
        # Scenario 1: Only Harlan is in the breakdown
        breakdown_harlan = "Scene 1: Harlan arrives in town."
        excerpt_harlan = packet.relevant_rulebook_excerpt(self.temp_dir, "chapter-01", breakdown_harlan)
        
        self.assertIn("Harlan", excerpt_harlan)
        self.assertNotIn("Darin Mayweather", excerpt_harlan)
        self.assertIn("inactive character 'Darin'", excerpt_harlan)
        
        # Scenario 2: Both are in the breakdown
        breakdown_both = "Scene 1: Harlan meets Darin."
        excerpt_both = packet.relevant_rulebook_excerpt(self.temp_dir, "chapter-01", breakdown_both)
        
        self.assertIn("Harlan", excerpt_both)
        self.assertIn("Darin Mayweather", excerpt_both)
        self.assertNotIn("excluded to optimize context budget", excerpt_both)


if __name__ == "__main__":
    unittest.main()
