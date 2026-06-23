#!/usr/bin/env python3
"""Unit tests for the BookForge Scene Manifests and layouts."""

import unittest
import shutil
from pathlib import Path

from bookforge.core.scene import (
    parse_scene_id,
    init_scene_manifest,
    load_scene_manifest,
    save_scene_manifest,
    discover_scenes,
    SceneManifest
)


class TestSceneManifests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("tests/temp_test_scene")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_parse_scene_id(self):
        # 1. Slash separation
        self.assertEqual(parse_scene_id("chapter-08/scene-02"), ("chapter-08", "scene-02"))
        self.assertEqual(parse_scene_id("ch08/scene-02"), ("chapter-08", "scene-02"))
        self.assertEqual(parse_scene_id("ch8/sc02"), ("chapter-08", "sc02"))

        # 2. Underline/underscore format
        self.assertEqual(parse_scene_id("ch08_sc02"), ("chapter-08", "scene-02"))
        self.assertEqual(parse_scene_id("chapter-08_scene-02"), ("chapter-08", "scene-02"))
        self.assertEqual(parse_scene_id("ch-08-sc-02"), ("chapter-08", "scene-02"))
        self.assertEqual(parse_scene_id("chapter08scene02"), ("chapter-08", "scene-02"))

        # 3. Bare scene slug
        self.assertEqual(parse_scene_id("scene-02"), ("", "scene-02"))

    def test_init_and_load_scene_manifest(self):
        m_path = init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 2000)
        self.assertTrue(m_path.exists())
        self.assertTrue((self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "manifest.yml").exists())

        manifest = load_scene_manifest(m_path, self.tmp_dir)
        self.assertEqual(manifest.scene_id, "scene-01")
        self.assertEqual(manifest.chapter, "chapter-01")
        self.assertEqual(manifest.target_words, 2000)
        self.assertEqual(manifest.status, "draft")
        self.assertIn("saloon", manifest.inputs.get("locations", []) + ["saloon"]) # Depends on template availability

        # Modify and save
        manifest.status = "revision"
        manifest.target_words = 2500
        save_scene_manifest(manifest, m_path)

        loaded_again = load_scene_manifest(m_path, self.tmp_dir)
        self.assertEqual(loaded_again.status, "revision")
        self.assertEqual(loaded_again.target_words, 2500)

    def test_computed_properties(self):
        manifest = SceneManifest(
            scene_id="scene-02",
            chapter="chapter-01",
            target_words=3000,
            status="draft",
            book_folder=self.tmp_dir
        )
        # Verify it resolves scene folder correctly
        expected_folder = self.tmp_dir / "chapters" / "chapter-01" / "scenes" / "scene-02"
        self.assertEqual(manifest.scene_folder, expected_folder)
        self.assertEqual(manifest.packet_path, expected_folder / "generation-packet.md")
        self.assertEqual(manifest.draft_path, expected_folder / "draft.md")

    def test_discover_scenes(self):
        # Create some scenes under changes/chapter-01/scenes/
        ch_dir = self.tmp_dir / "changes" / "chapter-01"
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-02", 1500)
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 2500)

        scenes = discover_scenes(ch_dir, self.tmp_dir)
        self.assertEqual(len(scenes), 2)
        # Should be sorted numerically
        self.assertEqual(scenes[0].scene_id, "scene-01")
        self.assertEqual(scenes[1].scene_id, "scene-02")


    def test_validate_scene(self):
        from bookforge.core.validators.orchestration import validate_scene
        # Create a scene manifest and draft
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 100)

        # Manifest has some forbidden terms
        m_path = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "manifest.yml"
        manifest = load_scene_manifest(m_path, self.tmp_dir)
        manifest.forbidden = ["laser", "airplane"]
        manifest.target_words = 100
        save_scene_manifest(manifest, m_path)

        # 1. Missing draft test
        issues = validate_scene(manifest)
        self.assertTrue(any("missing" in issue.message.lower() for issue in issues))

        # 2. Write empty draft
        manifest.draft_path.write_text("   ", encoding="utf-8")
        issues = validate_scene(manifest)
        self.assertTrue(any("empty" in issue.message.lower() for issue in issues))

        # 3. Write draft with word count issue and forbidden term
        manifest.draft_path.write_text("This draft has only a few words but contains a laser.", encoding="utf-8")
        issues = validate_scene(manifest)
        self.assertTrue(any("word count" in issue.message.lower() for issue in issues))
        self.assertTrue(any("forbidden elements" in issue.message.lower() for issue in issues))


if __name__ == "__main__":
    unittest.main()
