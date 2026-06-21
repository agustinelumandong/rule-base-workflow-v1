import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "manuscript-workflow-orchestrator"
    / "scripts"
)
SCRIPT_PATH = SCRIPT_DIR / "plan_chapter_pacing.py"


def load_pacing():
    sys.path.insert(0, str(SCRIPT_DIR))
    spec = importlib.util.spec_from_file_location("plan_chapter_pacing", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
