"""Unit tests for the BookForge Queue module."""

import unittest
import shutil
from pathlib import Path
import json

from bookforge.core.queue import build_queue, load_queue, update_queue_scene, get_queue_path
from bookforge.core.scene import init_scene_manifest

class TestQueue(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("tests/temp_test_queue")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # Create a basic book-like structure
        (self.tmp_dir / "changes").mkdir(parents=True, exist_ok=True)
        # Create chapter summaries to make it look like a valid book folder
        (self.tmp_dir / "chapter-summaries.md").write_text("# Chapter Summaries", encoding="utf-8")

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_build_and_update_queue(self):
        # 1. Initialize two scenes
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 2000)
        
        # 2. Build the queue
        q_path = build_queue(self.tmp_dir)
        self.assertTrue(q_path.exists())
        self.assertEqual(q_path, get_queue_path(self.tmp_dir))
        
        # 3. Load and inspect the queue
        queue = load_queue(self.tmp_dir)
        self.assertEqual(queue["book"], self.tmp_dir.name)
        scenes = queue["scenes"]
        self.assertEqual(len(scenes), 2)
        
        # Sorted order should be scene-01 then scene-02
        self.assertEqual(scenes[0]["scene_key"], "chapter-01/scene-01")
        self.assertEqual(scenes[1]["scene_key"], "chapter-01/scene-02")
        
        # Dependency check
        self.assertEqual(scenes[0]["dependencies"], [])
        self.assertEqual(scenes[1]["dependencies"], ["chapter-01/scene-01"])
        
        # Attempt count defaults
        self.assertEqual(scenes[0]["attempts"]["generation"], 0)
        self.assertEqual(scenes[0]["attempts"]["patch"], 0)
        self.assertEqual(scenes[0]["status"], "ready_for_generation")

        # 4. Update the queue
        success = update_queue_scene(
            self.tmp_dir,
            "chapter-01/scene-01",
            status="ready_for_patch",
            provider="chatgpt_web",
            inc_generation=True
        )
        self.assertTrue(success)

        # 5. Reload and check updates
        updated_queue = load_queue(self.tmp_dir)
        updated_scene = updated_queue["scenes"][0]
        self.assertEqual(updated_scene["status"], "ready_for_patch")
        self.assertEqual(updated_scene["provider"], "chatgpt_web")
        self.assertEqual(updated_scene["attempts"]["generation"], 1)
        self.assertEqual(updated_scene["attempts"]["patch"], 0)

        # 6. Rebuild queue and ensure it preserves updates!
        rebuilt_path = build_queue(self.tmp_dir)
        rebuilt_queue = load_queue(self.tmp_dir)
        rebuilt_scene = rebuilt_queue["scenes"][0]
        self.assertEqual(rebuilt_scene["status"], "ready_for_patch")
        self.assertEqual(rebuilt_scene["provider"], "chatgpt_web")
        self.assertEqual(rebuilt_scene["attempts"]["generation"], 1)

    def test_next_runnable_scene(self):
        # Initialize two scenes
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 2000)
        build_queue(self.tmp_dir)

        from bookforge.core.queue import get_next_runnable_scene, get_next_command

        # Initially, the first scene should be runnable (dependencies are empty)
        next_scene = get_next_runnable_scene(self.tmp_dir)
        self.assertIsNotNone(next_scene)
        self.assertEqual(next_scene["scene_key"], "chapter-01/scene-01")

        # Mock mark the first scene as validation_passed
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="validation_passed")

        # Now, the second scene should be runnable
        next_scene = get_next_runnable_scene(self.tmp_dir)
        self.assertIsNotNone(next_scene)
        self.assertEqual(next_scene["scene_key"], "chapter-01/scene-02")
        self.assertEqual(next_scene["status"], "ready_for_generation")

        desc, cmd = get_next_command(next_scene)
        self.assertIn("Generate the initial prompt/context packet", desc)
        self.assertEqual(cmd, "bf packet --chapter chapter-01 --scene scene-02 --task draft-prose")

    def test_valid_patch_advances_queue_and_single_active_constraint(self):
        # 1. Initialize two scenes
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3000)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 2000)
        build_queue(self.tmp_dir)

        from bookforge.core.queue import verify_scene_runnable

        # Initially, scene-01 should be runnable
        self.assertTrue(verify_scene_runnable(self.tmp_dir, "chapter-01/scene-01"))

        # Initially, scene-02 is NOT runnable because its dependency (scene-01) is not completed
        self.assertFalse(verify_scene_runnable(self.tmp_dir, "chapter-01/scene-02"))

        # Transition scene-01 to generation_packet_ready (in-progress)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")

        # Now scene-01 is in-progress (active)
        # Verify single-active constraint: scene-02 cannot be run.
        self.assertFalse(verify_scene_runnable(self.tmp_dir, "chapter-01/scene-02"))

        # Now transition scene-01 to validation_passed (completed)
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="validation_passed")

        # Now that scene-01 is completed, there are no active scenes in the queue.
        # Next eligible scene (scene-02) becomes runnable.
        self.assertTrue(verify_scene_runnable(self.tmp_dir, "chapter-01/scene-02"))

    def test_build_queue_falls_back_to_validator_aligned_beat_breakdown(self):
        chapter_dir = self.tmp_dir / "chapters" / "chapter-01"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        (self.tmp_dir / "phase-0.md").write_text("# Outline\n\n## Chapter 01\nText\n", encoding="utf-8")
        (chapter_dir / "scene-breakdown.md").write_text(
            "# Scene Breakdown\n\n"
            "## BEAT 1: Arrival\n\n"
            "### Source Context Lock\n- **Source Anchor:** Chapter 1.\n\n"
            "### Beat Instructions\n- **Action:** Ride in.\n\n"
            "### Context Match Check\n- Matches source.\n\n"
            "## BEAT 2: Confrontation\n\n"
            "### Source Context Lock\n- **Source Anchor:** Chapter 1.\n\n"
            "### Beat Instructions\n- **Action:** Face the sheriff.\n\n"
            "### Context Match Check\n- Matches source.\n",
            encoding="utf-8",
        )

        build_queue(self.tmp_dir)

        queue = load_queue(self.tmp_dir)
        self.assertEqual(
            [scene["scene_key"] for scene in queue["scenes"]],
            ["chapter-01/scene-01", "chapter-01/scene-02"],
        )

    def test_build_queue_bootstraps_scene_manifests_from_scene_breakdown(self):
        chapter_dir = self.tmp_dir / "chapters" / "chapter-01"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        (self.tmp_dir / "chapter-pacing-plan.md").write_text(
            "| Chapter | Pacing Class | Elastic Range | Beat Count | Reason | Expansion Permission |\n"
            "| --- | --- | --- | ---: | --- | --- |\n"
            "| Chapter 1 | expanded | source suggests ~3,000 words from `3,000 words` | 4 | test | test |\n",
            encoding="utf-8",
        )
        (chapter_dir / "scene-breakdown.md").write_text(
            "## Scene 1: Cabin Check\n\n"
            "### BEAT: Jake checks the cabin\n\n"
            "## Scene 2: Discovery\n\n"
            "### BEAT: Finds tracks\n"
            "### BEAT: Reads gait\n"
            "### BEAT: Finds camp\n",
            encoding="utf-8",
        )

        build_queue(self.tmp_dir)

        queue = load_queue(self.tmp_dir)
        self.assertEqual(
            [scene["scene_key"] for scene in queue["scenes"]],
            ["chapter-01/scene-01", "chapter-01/scene-02"],
        )
        self.assertEqual(sum(scene["target_words"] for scene in queue["scenes"]), 3000)
        self.assertTrue(
            (self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "manifest.yml").exists()
        )


if __name__ == "__main__":
    unittest.main()
