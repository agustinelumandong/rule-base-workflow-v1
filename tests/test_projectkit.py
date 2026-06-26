"""Unit tests for the BookForge Project Kit module."""

import shutil
import unittest
from pathlib import Path

import yaml

from bookforge.core.projectkit import (
    COMPILED_SOURCE_FILENAME,
    build_project_kit,
    project_kit_folder,
    render_compiled_project_source,
    render_project_instructions,
    render_story_bible,
    render_character_states,
    render_timeline,
    render_style_rules,
    render_hard_guardrails,
    render_world_reality_rules,
    render_current_outline,
    render_previous_chapter_summaries,
    render_unresolved_hooks,
    render_generation_queue,
    sync_active_and_archive_packets,
    PROVIDERS,
)
from bookforge.core.workspace import resolve_provider_workspace_name
from bookforge.core.queue import build_queue, update_queue_scene
from bookforge.core.scene import init_scene_manifest
from bookforge.core.canon.io import save_yaml_file, get_events_dir, get_entities_dir, get_state_dir


class TestProjectKit(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("tests/temp_test_projectkit")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # Create a minimal book structure
        (self.tmp_dir / "changes").mkdir(parents=True, exist_ok=True)
        (self.tmp_dir / "chapter-summaries.md").write_text(
            "# Chapter Summaries\n\n## chapter-01\nSummary of chapter one.\n",
            encoding="utf-8",
        )
        (self.tmp_dir / "mood-lock.md").write_text(
            "# Mood Lock\n\nGrim, sparse, frontier tone.\n",
            encoding="utf-8",
        )
        (self.tmp_dir / "rulebook.md").write_text(
            "# Rulebook\n\n## Characters\n\n### Harlan\n- Role: protagonist\n\n## Forbidden\n- No modern weapons.\n",
            encoding="utf-8",
        )
        # Source outline
        (self.tmp_dir / "phase-0.md").write_text(
            "# Phase 0\n\n## Chapter 01\nSource outline for chapter one.\n",
            encoding="utf-8",
        )

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_project_kit_folder(self):
        result = project_kit_folder(self.tmp_dir, "chatgpt")
        self.assertEqual(result, self.tmp_dir / "project-kits" / "chatgpt")

    def test_resolve_provider_workspace_name_for_series_book(self):
        self.assertEqual(
            resolve_provider_workspace_name(Path("books/longhunter-series/book-2")),
            "longhunter-series/book-2",
        )

    def test_resolve_provider_workspace_name_for_leaf_book(self):
        self.assertEqual(resolve_provider_workspace_name(Path("books/my-book")), "my-book")

    def test_resolve_provider_workspace_name_preserves_override(self):
        self.assertEqual(
            resolve_provider_workspace_name(Path("books/longhunter-series/book-2"), "custom/workspace"),
            "custom/workspace",
        )

    def test_render_project_instructions_chatgpt(self):
        text = render_project_instructions(self.tmp_dir, "chatgpt")
        self.assertIn("BookForge Provider-Web Writing Lane", text)
        self.assertIn("chatgpt", text.lower())
        self.assertIn("Prefer the active scene packet", text)
        self.assertIn("one scene only", text)

    def test_render_project_instructions_claude(self):
        text = render_project_instructions(self.tmp_dir, "claude")
        self.assertIn("literary continuity", text)

    def test_render_project_instructions_gemini(self):
        text = render_project_instructions(self.tmp_dir, "gemini")
        self.assertIn("long context", text)

    def test_render_story_bible(self):
        text = render_story_bible(self.tmp_dir)
        self.assertIn("Story Bible (Compiled)", text)
        # Premise comes from rulebook (preferred over phase-0)
        self.assertIn("Rulebook", text)

    def test_render_character_states_empty(self):
        text = render_character_states(self.tmp_dir)
        self.assertIn("Character States", text)
        # No canon snapshot yet
        self.assertIn("No character data", text)

    def test_render_character_states_with_snapshot(self):
        # Create a minimal canon snapshot
        state_dir = get_state_dir(self.tmp_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "characters": {
                "harlan": {
                    "canonical": "Harlan",
                    "status": "alive",
                    "location": "saloon",
                    "emotional_state": "tense",
                    "inventory": ["colt_45"],
                    "injuries": {},
                    "secrets": [],
                    "relationships": {},
                }
            },
            "locations": {},
            "objects": {},
            "unresolved_pressure": [],
            "chapter_invariants": [],
        }
        save_yaml_file(state_dir / "snapshot.yml", snapshot)

        text = render_character_states(self.tmp_dir)
        self.assertIn("Harlan", text)
        self.assertIn("alive", text)
        self.assertIn("saloon", text)
        self.assertIn("colt_45", text)

    def test_render_timeline(self):
        # Create chapter dirs
        (self.tmp_dir / "chapters" / "chapter-01").mkdir(parents=True, exist_ok=True)
        text = render_timeline(self.tmp_dir)
        self.assertIn("Timeline (Compiled)", text)
        self.assertIn("chapter-01", text)

    def test_render_style_rules(self):
        text = render_style_rules(self.tmp_dir)
        self.assertIn("Style Rules", text)
        self.assertIn("Mood Lock", text)

    def test_render_hard_guardrails(self):
        text = render_hard_guardrails(self.tmp_dir)
        self.assertIn("Hard Guardrails", text)
        self.assertIn("Forbidden Reveals", text)
        self.assertIn("Canon Mutation Rules", text)

    def test_render_world_reality_rules_empty(self):
        text = render_world_reality_rules(self.tmp_dir)
        self.assertIn("World Reality Rules", text)
        self.assertIn("No research cache found.", text)

    def test_render_world_reality_rules_with_accepted(self):
        # Create a research cache entry
        cache_dir = self.tmp_dir / "research_cache" / "weapons"
        cache_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": "weapons/winchester_1873",
            "category": "weapons",
            "subject": "winchester 1873",
            "period": "1870s",
            "question": "Was the Winchester 1873 available?",
            "answer": "Yes, plausible for late 1870s frontier.",
            "confidence": "high",
            "canon_status": "accepted",
            "source_backend": "manual",
        }
        (cache_dir / "winchester_1873.yml").write_text(
            yaml.safe_dump(entry, sort_keys=False), encoding="utf-8"
        )

        text = render_world_reality_rules(self.tmp_dir)
        self.assertIn("accepted", text)
        self.assertIn("winchester", text.lower())

    def test_render_world_reality_rules_excludes_pending(self):
        cache_dir = self.tmp_dir / "research_cache" / "weapons"
        cache_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": "weapons/test_pending",
            "category": "weapons",
            "subject": "test pending",
            "period": "1870s",
            "question": "Test?",
            "answer": "Test answer.",
            "confidence": "medium",
            "canon_status": "pending",
            "source_backend": "manual",
        }
        (cache_dir / "test_pending.yml").write_text(
            yaml.safe_dump(entry, sort_keys=False), encoding="utf-8"
        )

        text = render_world_reality_rules(self.tmp_dir)
        self.assertNotIn("test pending", text.lower())

    def test_render_world_reality_rules_excludes_rejected(self):
        cache_dir = self.tmp_dir / "research_cache" / "weapons"
        cache_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": "weapons/test_rejected",
            "category": "weapons",
            "subject": "test rejected",
            "period": "1870s",
            "question": "Test?",
            "answer": "Test answer.",
            "confidence": "low",
            "canon_status": "rejected",
            "source_backend": "manual",
        }
        (cache_dir / "test_rejected.yml").write_text(
            yaml.safe_dump(entry, sort_keys=False), encoding="utf-8"
        )

        text = render_world_reality_rules(self.tmp_dir)
        self.assertNotIn("test rejected", text.lower())

    def test_render_current_outline(self):
        text = render_current_outline(self.tmp_dir)
        self.assertIn("Current Outline", text)
        self.assertIn("Phase 0", text)

    def test_render_previous_chapter_summaries(self):
        text = render_previous_chapter_summaries(self.tmp_dir)
        self.assertIn("Previous Chapter Summaries", text)
        self.assertIn("chapter-01", text)

    def test_render_unresolved_hooks_empty(self):
        text = render_unresolved_hooks(self.tmp_dir)
        self.assertIn("Unresolved Hooks", text)

    def test_render_generation_queue_empty(self):
        text = render_generation_queue(self.tmp_dir)
        self.assertIn("Generation Queue", text)
        self.assertIn("No scenes in queue", text)

    def test_render_generation_queue_with_scenes(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 2000)
        build_queue(self.tmp_dir)

        text = render_generation_queue(self.tmp_dir)
        self.assertIn("chapter-01/scene-01", text)
        self.assertIn("chapter-01/scene-02", text)

    def test_project_kit_build_creates_expected_files(self):
        # Initialize scenes for the queue
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)

        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")
        self.assertTrue(kit_dir.exists())
        self.assertEqual(kit_dir, project_kit_folder(self.tmp_dir, "chatgpt"))

        stable_files = sorted(p.name for p in kit_dir.iterdir() if p.is_file() and p.name[0].isdigit())
        self.assertEqual(stable_files, [COMPILED_SOURCE_FILENAME])
        compiled = (kit_dir / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Default Provider Workspace", compiled)
        self.assertIn("## Source: 10_generation_queue.md", compiled)
        self.assertIn("chapter-01/scene-01", compiled)

    def test_compiled_project_source_contains_stable_sections(self):
        text = render_compiled_project_source(self.tmp_dir, "chatgpt")
        self.assertIn("## Source: 00_project_instructions.md", text)
        self.assertIn("## Source: 01_story_bible_compiled.md", text)
        self.assertIn("## Source: 10_generation_queue.md", text)

    def test_project_kit_build_removes_old_split_stable_files(self):
        kit_dir = project_kit_folder(self.tmp_dir, "chatgpt")
        kit_dir.mkdir(parents=True, exist_ok=True)
        (kit_dir / "01_story_bible_compiled.md").write_text("old", encoding="utf-8")

        build_project_kit(self.tmp_dir, "chatgpt")

        self.assertFalse((kit_dir / "01_story_bible_compiled.md").exists())
        self.assertTrue((kit_dir / COMPILED_SOURCE_FILENAME).exists())

    def test_active_folder_contains_only_active_scene_packet(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 3000)

        # Create dummy packet files
        s1_dir = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01"
        s1_dir.mkdir(parents=True, exist_ok=True)
        (s1_dir / "generation-packet.md").write_text("packet1", encoding="utf-8")

        s2_dir = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-02"
        s2_dir.mkdir(parents=True, exist_ok=True)
        (s2_dir / "generation-packet.md").write_text("packet2", encoding="utf-8")

        # Build queue first, then set statuses
        build_queue(self.tmp_dir)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="validation_passed")
        update_queue_scene(self.tmp_dir, "chapter-01/scene-02", status="generation_packet_ready")

        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")

        active_dir = kit_dir / "active"
        self.assertTrue(active_dir.exists())
        active_files = list(active_dir.glob("*.md"))
        self.assertEqual(len(active_files), 1)
        self.assertIn("scene-02", active_files[0].name)

    def test_done_scene_packets_go_to_archive(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 3000)

        # Create dummy packet files
        s1_dir = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01"
        s1_dir.mkdir(parents=True, exist_ok=True)
        (s1_dir / "generation-packet.md").write_text("packet1", encoding="utf-8")

        s2_dir = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-02"
        s2_dir.mkdir(parents=True, exist_ok=True)
        (s2_dir / "generation-packet.md").write_text("packet2", encoding="utf-8")

        # Build queue first, then set statuses
        build_queue(self.tmp_dir)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="validation_passed")
        update_queue_scene(self.tmp_dir, "chapter-01/scene-02", status="generation_packet_ready")

        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")

        archive_dir = kit_dir / "archive"
        self.assertTrue(archive_dir.exists())
        archive_files = list(archive_dir.glob("*.md"))
        self.assertEqual(len(archive_files), 1)
        self.assertIn("scene-01", archive_files[0].name)

    def test_accepted_research_included(self):
        cache_dir = self.tmp_dir / "research_cache" / "weapons"
        cache_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": "weapons/winchester_1873",
            "category": "weapons",
            "subject": "winchester 1873",
            "period": "1870s",
            "question": "Was the Winchester 1873 available?",
            "answer": "Yes, plausible.",
            "confidence": "high",
            "canon_status": "accepted",
            "source_backend": "manual",
        }
        (cache_dir / "winchester_1873.yml").write_text(
            yaml.safe_dump(entry, sort_keys=False), encoding="utf-8"
        )

        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")
        reality = (kit_dir / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
        self.assertIn("winchester", reality.lower())
        self.assertIn("accepted", reality)

    def test_pending_research_excluded(self):
        cache_dir = self.tmp_dir / "research_cache" / "weapons"
        cache_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": "weapons/pending_item",
            "category": "weapons",
            "subject": "pending item",
            "period": "1870s",
            "question": "Test?",
            "answer": "Test.",
            "confidence": "medium",
            "canon_status": "pending",
            "source_backend": "manual",
        }
        (cache_dir / "pending_item.yml").write_text(
            yaml.safe_dump(entry, sort_keys=False), encoding="utf-8"
        )

        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")
        reality = (kit_dir / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
        self.assertNotIn("pending item", reality.lower())

    def test_rejected_research_excluded(self):
        cache_dir = self.tmp_dir / "research_cache" / "weapons"
        cache_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "key": "weapons/rejected_item",
            "category": "weapons",
            "subject": "rejected item",
            "period": "1870s",
            "question": "Test?",
            "answer": "Test.",
            "confidence": "low",
            "canon_status": "rejected",
            "source_backend": "manual",
        }
        (cache_dir / "rejected_item.yml").write_text(
            yaml.safe_dump(entry, sort_keys=False), encoding="utf-8"
        )

        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")
        reality = (kit_dir / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
        self.assertNotIn("rejected item", reality.lower())

    def test_generation_queue_markdown_matches_queue_yml(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 3000)
        build_queue(self.tmp_dir)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="validation_passed")

        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")
        queue_md = (kit_dir / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
        self.assertIn("chapter-01/scene-01", queue_md)
        self.assertIn("validation_passed", queue_md)

    def test_provider_specific_instructions_render(self):
        for provider in PROVIDERS:
            kit_dir = build_project_kit(self.tmp_dir, provider)
            instructions = (kit_dir / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
            self.assertIn("BookForge Provider-Web Writing Lane", instructions)
            if provider != "generic":
                self.assertIn(provider, instructions.lower())

    def test_project_kit_clean_removes_old_active_files(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        kit_dir = build_project_kit(self.tmp_dir, "chatgpt")
        self.assertTrue(kit_dir.exists())

        # Clean
        shutil.rmtree(kit_dir)
        self.assertFalse(kit_dir.exists())

    def test_invalid_provider_raises(self):
        with self.assertRaises(ValueError):
            build_project_kit(self.tmp_dir, "invalid_provider")

    def test_multiple_providers_independent(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        kit_chatgpt = build_project_kit(self.tmp_dir, "chatgpt")
        kit_claude = build_project_kit(self.tmp_dir, "claude")

        self.assertNotEqual(kit_chatgpt, kit_claude)
        self.assertTrue(kit_chatgpt.exists())
        self.assertTrue(kit_claude.exists())

        instructions_chatgpt = (kit_chatgpt / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
        instructions_claude = (kit_claude / COMPILED_SOURCE_FILENAME).read_text(encoding="utf-8")
        self.assertIn("chatgpt", instructions_chatgpt.lower())
        self.assertIn("claude", instructions_claude.lower())


if __name__ == "__main__":
    unittest.main()
