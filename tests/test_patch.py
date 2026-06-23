#!/usr/bin/env python3
"""Unit tests for the BookForge Patching and Splicing engine."""

import unittest
from pathlib import Path

from bookforge.core.scene import SceneManifest
from bookforge.core.patch import build_patch_packet, splice_prose, validate_merged_prose


class TestPatchingEngine(unittest.TestCase):
    def test_build_patch_packet(self):
        manifest = SceneManifest(
            scene_id="scene-01",
            chapter="chapter-01",
            target_words=2000,
            status="draft",
            required_beats=["Beat A", "Beat B"],
            forbidden=["magic"]
        )
        packet = build_patch_packet(manifest, ["Rule 1 failed", "Rule 2 failed"])
        self.assertIn("# Patch Packet for: scene-01 (chapter-01)", packet)
        self.assertIn("- Rule 1 failed", packet)
        self.assertIn("- Beat A", packet)
        self.assertIn("- magic", packet)

    def test_splice_prose_anchors(self):
        original = (
            "The sun was setting over the ridge.\n"
            "Harlan stood near the fence, watching the dust settle.\n"
            "He spit into the dirt and wiped his forehead.\n"
            "The horses in the stable whinnied softly."
        )

        # Replacement with overlapping prefix and suffix anchors
        replacement = (
            "```markdown\n"
            "Harlan stood near the fence, watching the dust settle.\n"
            "He spit into the dirt and drank from his canteen instead of wiping.\n"
            "The horses in the stable whinnied softly.\n"
            "```"
        )

        success, result = splice_prose(original, replacement)
        self.assertTrue(success)
        self.assertIn("drank from his canteen instead of wiping", result)
        self.assertNotIn("wiped his forehead", result)
        self.assertIn("The sun was setting", result)

    def test_splice_prose_search_replace(self):
        original = "Line A\nLine B\nLine C"
        replacement = (
            "SEARCH\n"
            "Line B\n"
            "REPLACE\n"
            "Line B Modified"
        )
        success, result = splice_prose(original, replacement)
        self.assertTrue(success)
        self.assertEqual(result.strip(), "Line A\nLine B Modified\nLine C")

    def test_multiline_replacement_parse(self):
        original = "First line of draft.\nTarget section to replace.\nLast line of draft."
        # SEARCH / ======= / replacement / EOF format
        replacement = (
            "SEARCH\n"
            "Target section to replace.\n"
            "=======\n"
            "This is a longer replacement body that has multiple words and lines.\n"
            "It should not be truncated to only 16 words, but keep the full content."
        )
        success, result = splice_prose(original, replacement)
        self.assertTrue(success)
        self.assertIn("This is a longer replacement body", result)
        self.assertIn("but keep the full content.", result)
        self.assertIn("First line of draft.", result)

    def test_splice_prose_no_match(self):
        original = "Line A\nLine B\nLine C"
        replacement = "Line X\nLine Y\nLine Z"
        success, reason = splice_prose(original, replacement)
        self.assertFalse(success)
        self.assertIn("Could not identify splice anchors", reason)

    def test_validate_merged_prose(self):
        # 1. Valid merged prose
        prose_ok = "The quick brown fox jumps over the lazy dog. " * 30 # 270 words
        errors = validate_merged_prose(prose_ok, 300)
        self.assertEqual(len(errors), 0)

        # 2. Word count too low
        errors_short = validate_merged_prose(prose_ok, 1000)
        self.assertTrue(any("word count" in err.lower() for err in errors_short))

        # 3. Conversational line at the start
        prose_conv = "Here is the corrected scene.\n" + prose_ok
        errors_conv = validate_merged_prose(prose_conv, 300)
        self.assertTrue(any("conversational" in err.lower() for err in errors_conv))

        # 4. Nested code block markers
        prose_code = prose_ok + "\n```\nsome code\n```"
        errors_code = validate_merged_prose(prose_code, 300)
        self.assertTrue(any("code block" in err.lower() for err in errors_code))


if __name__ == "__main__":
    unittest.main()
