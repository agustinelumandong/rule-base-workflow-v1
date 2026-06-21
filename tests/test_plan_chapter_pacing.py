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


if __name__ == "__main__":
    unittest.main()
