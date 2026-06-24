"""Unit tests for BookForge MCP tool implementations."""

import json
import shutil
import unittest
from pathlib import Path

from bookforge.core.scene import init_scene_manifest
from bookforge.core.queue import build_queue, update_queue_scene


class TestMCPTools(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("tests/temp_test_mcp_tools")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        (self.tmp_dir / "changes").mkdir(parents=True, exist_ok=True)
        (self.tmp_dir / "chapter-summaries.md").write_text("# Chapter Summaries", encoding="utf-8")
        (self.tmp_dir / "rulebook.md").write_text("# Rulebook\n\nTest rules.", encoding="utf-8")
        (self.tmp_dir / "mood-lock.md").write_text("# Mood Lock\n\nTest mood.", encoding="utf-8")
        (self.tmp_dir / "phase-0.md").write_text("# Phase 0\n\nPeriod: 1800\n\n## chapter-01\n\nTest outline.", encoding="utf-8")

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def _init_scene(self, chapter="chapter-01", scene_id="scene-01", words=3500):
        init_scene_manifest(self.tmp_dir, chapter, scene_id, words)
        build_queue(self.tmp_dir)

    def _write_draft(self, chapter="chapter-01", scene_id="scene-01", text=None):
        if text is None:
            text = "The morning broke cold over the ridge. " * 200
        scene_dir = self.tmp_dir / "changes" / chapter / "scenes" / scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)
        (scene_dir / "draft.md").write_text(text, encoding="utf-8")

    def test_get_queue_status_returns_structured_counts(self):
        self._init_scene()
        from bookforge.mcp.tools import get_queue_status
        result = get_queue_status(self.tmp_dir, {})
        self.assertTrue(result.ok)
        self.assertEqual(result.tool, "get_queue_status")
        self.assertEqual(result.data["book"], self.tmp_dir.name)
        self.assertIn("counts", result.data)
        self.assertIn("active_scene", result.data)

    def test_get_queue_status_with_include_scenes(self):
        self._init_scene()
        from bookforge.mcp.tools import get_queue_status
        result = get_queue_status(self.tmp_dir, {"include_scenes": True})
        self.assertTrue(result.ok)
        self.assertIn("scenes", result.data)
        self.assertEqual(len(result.data["scenes"]), 1)

    def test_get_active_scene_returns_queue_active(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import get_active_scene
        result = get_active_scene(self.tmp_dir, {})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["scene"], "chapter-01/scene-01")
        self.assertEqual(result.data["status"], "generation_packet_ready")

    def test_get_active_scene_no_active_returns_error(self):
        self._init_scene()
        from bookforge.mcp.tools import get_active_scene
        result = get_active_scene(self.tmp_dir, {})
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "NO_ACTIVE_SCENE")

    def test_build_generation_packet_returns_path(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import build_generation_packet
        result = build_generation_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result.ok)
        self.assertIn("packet_path", result.data)
        self.assertIn("packet_tokens", result.data)
        self.assertTrue(Path(result.data["packet_path"]).exists())

    def test_build_generation_packet_no_scene_specified(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import build_generation_packet
        result = build_generation_packet(self.tmp_dir, {})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["scene"], "chapter-01/scene-01")

    def test_build_generation_packet_queue_blocked(self):
        self._init_scene()
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 3500)
        build_queue(self.tmp_dir)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import build_generation_packet
        result = build_generation_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-02"})
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "QUEUE_BLOCKED")

    def test_validate_scene_returns_failures_and_warnings(self):
        self._init_scene()
        self._write_draft()
        from bookforge.mcp.tools import validate_scene
        result = validate_scene(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result.ok)
        self.assertIn("status", result.data)
        self.assertIn("failures", result.data)
        self.assertIn("warnings", result.data)
        self.assertEqual(result.data["scene"], "chapter-01/scene-01")

    def test_validate_scene_no_draft_returns_hard_failure(self):
        self._init_scene()
        from bookforge.mcp.tools import validate_scene
        result = validate_scene(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["status"], "validation_failed")
        self.assertTrue(len(result.data["failures"]) > 0)

    def test_build_patch_packet_returns_path(self):
        self._init_scene()
        self._write_draft()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="validation_failed")
        val_json = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "validation.json"
        val_json.write_text(json.dumps({"status": "failed", "failures": ["SCENE_WORD_COUNT_VIOLATION"]}), encoding="utf-8")
        from bookforge.mcp.tools import build_patch_packet
        result = build_patch_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result.ok)
        self.assertIn("patch_packet_path", result.data)
        self.assertTrue(Path(result.data["patch_packet_path"]).exists())

    def test_build_patch_packet_no_failures_returns_error(self):
        self._init_scene()
        self._write_draft()
        from bookforge.mcp.tools import build_patch_packet
        result = build_patch_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "VALIDATION_FAILED")

    def test_readonly_blocks_save_draft(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import save_draft
        result = save_draft(self.tmp_dir, {"text": "test"}, readonly=True)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "READONLY_MODE")

    def test_readonly_blocks_apply_patch(self):
        self._init_scene()
        from bookforge.mcp.tools import apply_patch
        result = apply_patch(self.tmp_dir, {"replacement_text": "test"}, readonly=True)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "READONLY_MODE")

    def test_allow_write_save_draft(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import save_draft
        text = "The morning broke cold over the ridge. " * 200
        result = save_draft(self.tmp_dir, {"text": text}, readonly=False)
        self.assertTrue(result.ok)
        self.assertIn("draft_path", result.data)
        self.assertGreater(result.data["word_count"], 0)
        draft_path = Path(result.data["draft_path"])
        self.assertTrue(draft_path.exists())

    def test_allow_write_save_draft_empty_text(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import save_draft
        result = save_draft(self.tmp_dir, {"text": ""}, readonly=False)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "BUILD_ERROR")

    def test_apply_patch_does_not_mutate_on_invalid_replacement(self):
        self._init_scene()
        self._write_draft()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="validation_failed")
        original_draft = (self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "draft.md").read_text(encoding="utf-8")
        from bookforge.mcp.tools import apply_patch
        result = apply_patch(self.tmp_dir, {"replacement_text": "COMPLETELY UNRELATED TEXT WITH NO ANCHORS"}, readonly=False)
        self.assertFalse(result.ok)
        current_draft = (self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "draft.md").read_text(encoding="utf-8")
        self.assertEqual(original_draft, current_draft)

    def test_get_scene_report_returns_structured_data(self):
        self._init_scene()
        self._write_draft()
        from bookforge.mcp.tools import get_scene_report
        result = get_scene_report(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["scene"], "chapter-01/scene-01")
        self.assertIn("word_count", result.data)
        self.assertIn("failures", result.data)
        self.assertIn("warnings", result.data)

    def test_query_research_cache_returns_empty(self):
        from bookforge.mcp.tools import query_research_cache
        result = query_research_cache(self.tmp_dir, {"query": "test query"})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["entries"], [])

    def test_tool_errors_are_structured(self):
        from bookforge.mcp.tools import get_active_scene
        result = get_active_scene(self.tmp_dir, {})
        self.assertFalse(result.ok)
        self.assertIn("error_code", result.to_dict())
        self.assertIn("message", result.to_dict())
        self.assertEqual(result.tool, "get_active_scene")

    def test_get_active_scene_multiple_active_returns_violation(self):
        self._init_scene()
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 3500)
        build_queue(self.tmp_dir)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        update_queue_scene(self.tmp_dir, "chapter-01/scene-02", status="ready_for_validation")
        from bookforge.mcp.tools import get_active_scene
        result = get_active_scene(self.tmp_dir, {})
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "QUEUE_INVARIANT_VIOLATION")

    def test_force_required_for_blocked_scene(self):
        self._init_scene()
        from bookforge.mcp.tools import build_generation_packet
        result = build_generation_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01", "force": True})
        self.assertTrue(result.ok)
        self.assertIn("packet_path", result.data)

    def test_build_generation_packet_idempotent_for_active_scene(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import build_generation_packet
        result1 = build_generation_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result1.ok)
        result2 = build_generation_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result2.ok)
        self.assertEqual(result1.data["packet_path"], result2.data["packet_path"])

    def test_build_generation_packet_uses_manifest_target_words(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 1100)
        build_queue(self.tmp_dir)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.mcp.tools import build_generation_packet
        result = build_generation_packet(self.tmp_dir, {"chapter": "chapter-01", "scene": "scene-01"})
        self.assertTrue(result.ok)
        self.assertEqual(result.data["target_words"], 1100)

    def test_project_kit_generation_state_active_contains_only_generation_packet(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        from bookforge.core.packet.builder import build_scene_packet
        from bookforge.core.packet.helpers import scene_folder
        folder = scene_folder(self.tmp_dir, "chapter-01", "scene-01")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "generation-packet.md").write_text("# Packet", encoding="utf-8")
        (folder / "patch-packet.md").write_text("# Patch", encoding="utf-8")
        from bookforge.mcp.tools import build_project_kit
        result = build_project_kit(self.tmp_dir, {"provider": "chatgpt"})
        self.assertTrue(result.ok)
        active_files = result.data["active_files"]
        gen_files = [f for f in active_files if "generation-packet" in f]
        patch_files = [f for f in active_files if "patch-packet" in f]
        self.assertTrue(len(gen_files) > 0, "Generation packet should be in active/")
        self.assertEqual(len(patch_files), 0, "Patch packet should NOT be in active/ for generation state")

    def test_project_kit_repair_state_active_contains_patch_packet(self):
        self._init_scene()
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="patch_packet_ready")
        from bookforge.core.packet.helpers import scene_folder
        folder = scene_folder(self.tmp_dir, "chapter-01", "scene-01")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "generation-packet.md").write_text("# Packet", encoding="utf-8")
        (folder / "patch-packet.md").write_text("# Patch", encoding="utf-8")
        from bookforge.mcp.tools import build_project_kit
        result = build_project_kit(self.tmp_dir, {"provider": "chatgpt"})
        self.assertTrue(result.ok)
        active_files = result.data["active_files"]
        patch_files = [f for f in active_files if "patch-packet" in f]
        gen_files = [f for f in active_files if "generation-packet" in f]
        self.assertTrue(len(patch_files) > 0, "Patch packet should be in active/ for repair state")
        self.assertEqual(len(gen_files), 0, "Generation packet should NOT be in active/ for repair state")


if __name__ == "__main__":
    unittest.main()
