import unittest

from bookforge.core import pacing


def load_pacing():
    # Legacy shims have been removed; return the canonical pacing module.
    return pacing


class ChapterPacingTests(unittest.TestCase):
    def test_explicit_scene_pacing_overrides_classification_terms(self):
        pacing = load_pacing()

        scene = """# Scene Breakdown

- **Pacing Class:** expanded
- **Elastic Range:** ~1,150 source guidance; source guidance only, not quota.
- **Setup / Payoff:** This template word should not force lean pacing.
"""

        pacing_class, elastic_range = pacing.explicit_scene_pacing(scene)

        self.assertEqual(pacing_class, "expanded")
        self.assertEqual(elastic_range, "~1,150 source guidance")

    def test_extract_beat_metadata_reads_weight_and_floor(self):
        pacing = load_pacing()

        scene = """# Scene Breakdown

## BEAT 1: Cabin Work

### Source Context Lock

- **Source Anchor:** Chapter 14 cabin claim.
- **Continuity In:** Jake has reached the valley.
- **Required Story Movement:** Jake secures shelter.
- **Continuity Out:** Cabin is habitable.
- **Do Not Invent:** New settlers or new threats.

### Pacing Guidance

- **Beat Weight:** money
- **Beat Development Floor:** >= 180 words
- **Why This Beat Matters:** This is the emotional landing and earned survival payoff.

### Beat Instructions

Write the beat.
"""

        beats = pacing.extract_beat_metadata(scene)

        self.assertEqual(len(beats), 1)
        self.assertEqual(beats[0].label, "Cabin Work")
        self.assertEqual(beats[0].weight, "money")
        self.assertEqual(beats[0].development_floor, 180)
        self.assertIn("emotional landing", beats[0].why_this_matters)


if __name__ == "__main__":
    unittest.main()
