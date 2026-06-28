#!/usr/bin/env python3
"""Unit tests for BookForge Advanced Style and Voice Gating."""

import json
import tempfile
import unittest
from pathlib import Path
from bookforge.core import voice


class TestVoiceGating(unittest.TestCase):
    def test_validate_dialogue_style_tags(self):
        # Discouraged tag warning
        draft = '"Get on the horse," said Harlan.'
        failures, warnings = voice.validate_dialogue_style(draft)
        self.assertEqual(len(failures), 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Dialogue Tag Warning", warnings[0])

    def test_validate_dialogue_style_slang(self):
        # Disallowed slang warning
        draft = '"Howdy, partner," Harlan muttered.'
        failures, warnings = voice.validate_dialogue_style(draft)
        self.assertTrue(len(warnings) >= 2)  # howdy, partner, muttered
        self.assertTrue(any("Texas slang" in w for w in warnings))

    def test_validate_dialogue_style_frontier_profile_slang_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_profiles": {
                            "fallback_profile": "frontier_1880s",
                            "year_buckets": [{"name": "frontier_1880s", "start": 1880, "end": 1899}],
                            "profiles": {
                                "frontier_1880s": {
                                    "voice": {"banned_slang": ["partner"]},
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "rulebook.md").write_text("**Time Period:** 1883\n", encoding="utf-8")

            failures, warnings = voice.validate_dialogue_style('"All right, partner."', root)

        self.assertEqual(len(failures), 0)
        self.assertTrue(any("Texas slang" in warning for warning in warnings))

    def test_validate_dialogue_style_transitional_profile_relaxes_slang(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_profiles": {
                            "fallback_profile": "frontier_transition_1900s",
                            "year_buckets": [{"name": "frontier_transition_1900s", "start": 1900, "end": 1909}],
                            "profiles": {
                                "frontier_transition_1900s": {
                                    "voice": {"banned_slang": []},
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "rulebook.md").write_text("**Time Period:** 1903\n", encoding="utf-8")

            failures, warnings = voice.validate_dialogue_style('"Howdy, partner."', root)

        self.assertEqual(len(failures), 0)
        self.assertEqual(warnings, [])

    def test_validate_dialogue_em_dash_spacing(self):
        # Spaced em dash action anchor -> valid
        draft_valid = '"Get on the horse." — Harlan tightened the cinch.'
        failures, warnings = voice.validate_dialogue_style(draft_valid)
        self.assertEqual(len(failures), 0)

        # Missing spacing around the em dash -> failure
        draft_invalid1 = '"Get on the horse."—Harlan tightened the cinch.'
        failures, warnings = voice.validate_dialogue_style(draft_invalid1)
        self.assertEqual(len(failures), 1)
        self.assertIn("Em Dash Formatting Failure", failures[0])

        draft_invalid2 = '"Get on the horse." -- Harlan tightened the cinch.'
        failures, warnings = voice.validate_dialogue_style(draft_invalid2)
        self.assertEqual(len(failures), 1)
        self.assertIn("Em Dash Formatting Failure", failures[0])

    def test_validate_pov_locking(self):
        all_chars = ["harlan", "darin"]
        
        # Harlan POV: Harlan feels -> allowed
        draft_ok = "Harlan felt the cold wind. Darin stood by the window."
        failures = voice.validate_pov_locking(draft_ok, "harlan", all_chars)
        self.assertEqual(len(failures), 0)

        # Harlan POV: Darin feels -> head-hopping failure
        draft_fail = "Harlan walked in. Darin felt extremely nervous and thought of running."
        failures = voice.validate_pov_locking(draft_fail, "harlan", all_chars)
        self.assertEqual(len(failures), 1)
        self.assertIn("POV Head-Hopping Failure", failures[0])
        self.assertIn("Darin", failures[0])

    def test_validate_sentence_openers(self):
        # -ing opener -> failure
        draft_ing = "Walking down the road, Harlan saw the sheriff."
        failures, warnings = voice.validate_sentence_openers(draft_ing)
        self.assertEqual(len(failures), 1)
        self.assertIn("Sentence Opener Failure", failures[0])

        # Name/Pronoun loop -> warning
        draft_loop = "Harlan walked in. Harlan sat down. Harlan ordered a drink."
        failures, warnings = voice.validate_sentence_openers(draft_loop)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Pronoun Loop Warning", warnings[0])


if __name__ == "__main__":
    unittest.main()
