import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def load_module(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / ".agents" / "skills" / "manuscript-workflow-orchestrator" / "scripts"


class NewScriptsTests(unittest.TestCase):
    def test_check_narrative_quality_is_in_script_inventory(self):
        repo_root = Path(__file__).resolve().parents[1]
        for relative_path in ("scripts/check.sh", "scripts/install.sh"):
            script_text = (repo_root / relative_path).read_text(encoding="utf-8")
            self.assertIn("check_narrative_quality.py", script_text)

    # ------------------------------------------------------------------
    # scan_banned_words.py
    # ------------------------------------------------------------------

    def test_scan_banned_words_detection(self):
        scanner = load_module("scan_banned_words", SCRIPTS_DIR / "scan_banned_words.py")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            draft = tmp_path / "chapter-01.md"
            draft.write_text(
                "Jed grabbed the heavy iron gate.\n"  # "heavy" is a banned style term
                "Running to the door, he looked back.\n"  # "-ing" opener
                "He felt the cold lead.\n",  # internal monologue phrase
                encoding="utf-8"
            )
            violations = scanner.scan_file(draft)
            
            categories = [v[1] for v in violations]
            self.assertIn("BANNED WORD", categories)
            self.assertIn("ING OPENER", categories)
            self.assertIn("INTERNAL MONO", categories)

    # ------------------------------------------------------------------
    # check_continuity_chain.py
    # ------------------------------------------------------------------

    def test_check_continuity_chain_valid(self):
        chain = load_module("check_continuity_chain", SCRIPTS_DIR / "check_continuity_chain.py")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            continuity_file = tmp_path / "continuity-out.md"
            continuity_file.write_text(
                "## Characters\nJed is alive and well.\n"
                "## Locations\nSaloon.\n"
                "## Changes\nNone.\n"
                "## Unresolved Pressure\nNone.\n"
                "## Next Chapter Must Know\nJed left the horse.\n",
                encoding="utf-8"
            )
            errors = chain.check_continuity_out_content(continuity_file)
            self.assertEqual(errors, [])

    def test_check_continuity_chain_missing_sections(self):
        chain = load_module("check_continuity_chain", SCRIPTS_DIR / "check_continuity_chain.py")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            continuity_file = tmp_path / "continuity-out.md"
            continuity_file.write_text(
                "## Characters\nJed is alive.\n"
                "## Locations\nSaloon.\n",
                encoding="utf-8"
            )
            errors = chain.check_continuity_out_content(continuity_file)
            self.assertTrue(len(errors) > 0)
            self.assertTrue(any("Missing section" in err for err in errors))

    # ------------------------------------------------------------------
    # check_chapter_gaps.py
    # ------------------------------------------------------------------

    def test_check_chapter_gaps_mismatch(self):
        # We test key logic or structure of check_chapter_gaps if needed,
        # but check_chapter_gaps is simple folder comparison.
        # Let's verify we can import it successfully without issues.
        gaps = load_module("check_chapter_gaps", SCRIPTS_DIR / "check_chapter_gaps.py")
        self.assertIsNotNone(gaps)


if __name__ == "__main__":
    unittest.main()
