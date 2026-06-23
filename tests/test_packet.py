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
        workspace_temp = Path("scratch_test_temp")
        workspace_temp.mkdir(exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(dir=workspace_temp))
        
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
        workspace_temp = Path("scratch_test_temp")
        if workspace_temp.exists() and not any(workspace_temp.iterdir()):
            workspace_temp.rmdir()

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

    def create_mock_chapter(self, slug="chapter-01"):
        folder = self.temp_dir / "changes" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "proposal.md").write_text("Scene 1: Harlan goes to the saloon.", encoding="utf-8")
        (folder / "draft.md").write_text("Harlan walked to the saloon.", encoding="utf-8")
        (folder / "beats.md").write_text("- beat 1", encoding="utf-8")
        (folder / "continuity-out.md").write_text("unresolved_stakes:\n  - harlan_is_still_alive\n", encoding="utf-8")
        
        (self.temp_dir / "phase-0.md").write_text("# Phase 0\n## chapter-01\nAnchor content\n", encoding="utf-8")
        (self.temp_dir / "chapter-summaries.md").write_text("# Chapter Summaries\n## chapter-01\nSummary content\n", encoding="utf-8")
        (self.temp_dir / "mood-lock.md").write_text("Mood lock text", encoding="utf-8")
        (self.temp_dir / "chapter-pacing-plan.md").write_text("Pacing info", encoding="utf-8")
        return folder

    def test_render_packet_all(self):
        self.create_mock_chapter()
        pkt = packet.render_packet(self.temp_dir, "chapter-01", "all")
        self.assertIn("# Context Packet: chapter-01", pkt)
        self.assertIn("## Compressed Style Lock", pkt)
        self.assertIn("## Source Chapter Anchor", pkt)
        self.assertIn("## Chapter Summary", pkt)
        self.assertIn("## Relevant Rulebook Facts", pkt)
        self.assertIn("## Review Focus", pkt)
        self.assertIn("## Mood And Tone Summary", pkt)
        self.assertIn("## Scene Breakdown", pkt)

    def test_render_packet_draft_prose(self):
        self.create_mock_chapter()
        pkt = packet.render_packet(self.temp_dir, "chapter-01", "draft-prose")
        self.assertIn("# Context Packet: chapter-01", pkt)
        self.assertIn("Task: `draft-prose`", pkt)
        self.assertIn("## Compressed Style Lock", pkt)
        self.assertIn("## Relevant Rulebook Facts", pkt)
        self.assertIn("## Review Focus", pkt)
        self.assertIn("## Scene Breakdown", pkt)
        self.assertNotIn("## Canon Snapshot", pkt)

    def write_character_profile(
        self,
        relative_path,
        *,
        char_id,
        canonical_name,
        category,
        body,
        aliases=None,
        role="Gunman",
        pov_allowed=False,
    ):
        aliases = aliases or []
        path = self.temp_dir / "characters" / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        alias_lines = "\n".join(f"  - {alias}" for alias in aliases) if aliases else "  []"
        path.write_text(
            f"""---
id: {char_id}
canonical_name: {canonical_name}
aliases:
{alias_lines}
category: {category}
story_role: {role}
pov:
  allowed: {str(pov_allowed).lower()}
---
# {canonical_name}

{body}
""",
            encoding="utf-8",
        )
        return path

    def test_draft_packet_includes_active_character_profile(self):
        self.create_mock_chapter()
        folder = self.temp_dir / "changes" / "chapter-01"
        (folder / "proposal.md").write_text("Scene 1: Harlan arrives in town.", encoding="utf-8")
        self.write_character_profile(
            "main/harlan.md",
            char_id="harlan",
            canonical_name="Harlan Stone",
            category="main",
            aliases=["Marshal Harlan"],
            body="Harlan profile from character file. Carries a Colt.",
            pov_allowed=True,
        )
        self.write_character_profile(
            "supporting/darin.md",
            char_id="darin",
            canonical_name="Darin Mayweather",
            category="supporting",
            body="Darin profile should not be selected.",
        )

        pkt = packet.render_packet(self.temp_dir, "chapter-01", "draft-prose")

        self.assertIn("## Relevant Character Profiles", pkt)
        self.assertIn("Harlan profile from character file", pkt)
        self.assertNotIn("Darin profile should not be selected", pkt)

    def test_draft_packet_falls_back_to_main_profiles_when_no_character_matches(self):
        self.create_mock_chapter()
        folder = self.temp_dir / "changes" / "chapter-01"
        (folder / "proposal.md").write_text("Scene 1: A rider arrives.", encoding="utf-8")
        self.write_character_profile(
            "main/harlan.md",
            char_id="harlan",
            canonical_name="Harlan",
            category="main",
            body="Main profile fallback text.",
        )
        self.write_character_profile(
            "supporting/darin.md",
            char_id="darin",
            canonical_name="Darin Mayweather",
            category="supporting",
            body="Supporting fallback should not appear.",
        )

        pkt = packet.render_packet(self.temp_dir, "chapter-01", "draft-prose")

        self.assertIn("## Relevant Character Profiles", pkt)
        self.assertIn("Main profile fallback text", pkt)
        self.assertNotIn("Supporting fallback should not appear", pkt)

    def test_draft_packet_omits_character_profiles_when_folder_missing(self):
        self.create_mock_chapter()

        pkt = packet.render_packet(self.temp_dir, "chapter-01", "draft-prose")

        self.assertNotIn("## Relevant Character Profiles", pkt)

    def test_draft_packet_warns_but_does_not_crash_on_malformed_character_front_matter(self):
        self.create_mock_chapter()
        path = self.temp_dir / "characters" / "main" / "harlan.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            """---
id: [not valid
canonical_name: Harlan
---
# Harlan

Malformed profile body.
""",
            encoding="utf-8",
        )

        pkt = packet.render_packet(self.temp_dir, "chapter-01", "draft-prose")

        self.assertIn("## Relevant Character Profiles", pkt)
        self.assertIn("WARNING: Could not parse character profile", pkt)

    def test_render_packet_continuity_check(self):
        self.create_mock_chapter()
        pkt = packet.render_packet(self.temp_dir, "chapter-01", "continuity-check")
        self.assertIn("# Context Packet: chapter-01", pkt)
        self.assertIn("Task: `continuity-check`", pkt)
        self.assertIn("## Chapter Content", pkt)
        self.assertIn("## Prior Continuity Out", pkt)
        self.assertIn("## Canon Snapshot", pkt)
        self.assertNotIn("## Compressed Style Lock", pkt)

    def test_render_packet_extract_memory(self):
        self.create_mock_chapter()
        pkt = packet.render_packet(self.temp_dir, "chapter-01", "extract-memory")
        self.assertIn("# Context Packet: chapter-01", pkt)
        self.assertIn("Task: `extract-memory`", pkt)
        self.assertIn("## Memory Extraction Schema", pkt)
        self.assertIn("## Chapter Draft", pkt)
        self.assertNotIn("## Compressed Style Lock", pkt)

    def test_render_packet_revise_style(self):
        self.create_mock_chapter()
        pkt = packet.render_packet(self.temp_dir, "chapter-01", "revise-style")
        self.assertIn("# Context Packet: chapter-01", pkt)
        self.assertIn("Task: `revise-style`", pkt)
        self.assertIn("## Style Guide", pkt)
        self.assertIn("## Chapter Draft", pkt)
        self.assertNotIn("## Canon Snapshot", pkt)

    def test_render_packet_validate_change(self):
        self.create_mock_chapter()
        pkt = packet.render_packet(self.temp_dir, "chapter-01", "validate-change")
        self.assertIn("# Context Packet: chapter-01", pkt)
        self.assertIn("Task: `validate-change`", pkt)
        self.assertIn("## Validation Results", pkt)
        self.assertIn("## Staging Elements", pkt)
        self.assertNotIn("## Compressed Style Lock", pkt)

    def test_render_packet_budget_trimming(self):
        self.create_mock_chapter()
        
        # Write a massive draft to exceed the draft-prose limit of 2500 tokens
        massive_draft = "word " * 15000
        folder = self.temp_dir / "changes" / "chapter-01"
        (folder / "draft.md").write_text(massive_draft, encoding="utf-8")
        
        # Limit rulebook excerpt or scene breakdown to trigger scale down / trimming
        # (Scene breakdown limit in draft-prose is 2200)
        massive_scene_breakdown = "scene " * 12000
        (folder / "proposal.md").write_text(massive_scene_breakdown, encoding="utf-8")
        
        pkt = packet.render_packet(self.temp_dir, "chapter-01", "draft-prose")
        
        # Check that the BUDGET_WARNING was appended
        self.assertIn("BUDGET_WARNING", pkt)
        self.assertIn("[Excerpt trimmed for token budget.]", pkt)


    def test_build_scene_packet(self):
        from bookforge.core.scene import init_scene_manifest
        from bookforge.core.packet.builder import build_scene_packet
        import yaml

        # Initialize a mock scene manifest under changes/chapter-01/scenes/scene-01
        m_path = init_scene_manifest(self.temp_dir, "chapter-01", "scene-01", 3000)
        self.assertTrue(m_path.exists())

        # Populate custom manifest values
        manifest_data = yaml.safe_load(m_path.read_text(encoding="utf-8"))
        manifest_data["required_beats"] = ["Beat A: Harlan drinks whiskey.", "Beat B: Darin enters saloon."]
        manifest_data["forbidden"] = ["space laser"]
        manifest_data["research_questions"] = ["Did salons sell beer?"]
        manifest_data["inputs"] = {
            "characters": ["harlan"]
        }
        with open(m_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest_data, f)

        # Write harlan profile
        self.write_character_profile(
            "main/harlan.md",
            char_id="harlan",
            canonical_name="Harlan Stone",
            category="main",
            aliases=["Marshal Harlan"],
            body="Harlan profile from character file.",
            pov_allowed=True,
        )

        pkt = build_scene_packet(self.temp_dir, "chapter-01", "scene-01")

        self.assertIn("# Scene Context Packet: scene-01 (chapter-01)", pkt)
        self.assertIn("## Required Beats", pkt)
        self.assertIn("Beat A: Harlan drinks whiskey.", pkt)
        self.assertIn("## Forbidden Elements", pkt)
        self.assertIn("space laser", pkt)
        self.assertIn("## Research Questions", pkt)
        self.assertIn("Did salons sell beer?", pkt)
        self.assertIn("## Compressed Style Lock", pkt)
        self.assertIn("## Relevant Character Profiles", pkt)
        self.assertIn("Harlan profile from character file", pkt)


if __name__ == "__main__":
    unittest.main()
