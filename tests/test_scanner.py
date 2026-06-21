"""Tests for the manuscript scanner (bookforge.core.scanner).

Migrated from the removed `scan_banned_words.py` shim; targets the core
module directly.
"""
import tempfile
import unittest
from pathlib import Path

from bookforge.core import scanner


class ScannerTests(unittest.TestCase):
    def test_scan_file_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            draft = tmp_path / "chapter-01.md"
            draft.write_text(
                "Jed grabbed the heavy iron gate.\n"  # "heavy" is a banned style term
                "Running to the door, he looked back.\n"  # "-ing" opener
                "He felt the cold lead.\n",  # internal monologue phrase
                encoding="utf-8",
            )
            violations = scanner.scan_file(draft)

            categories = [v[1] for v in violations]
            self.assertIn("BANNED WORD", categories)
            self.assertIn("ING OPENER", categories)
            self.assertIn("INTERNAL MONO", categories)


if __name__ == "__main__":
    unittest.main()
