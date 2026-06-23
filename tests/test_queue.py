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

if __name__ == "__main__":
    unittest.main()
