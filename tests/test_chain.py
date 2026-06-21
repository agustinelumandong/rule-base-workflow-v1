"""Tests for the continuity-chain checker (bookforge.core.chain).

Migrated from the removed `check_continuity_chain.py` shim; targets the core
module directly.
"""
import tempfile
import unittest
from pathlib import Path

from bookforge.core import chain


class ContinuityChainTests(unittest.TestCase):
    def test_check_continuity_out_content_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            continuity_file = tmp_path / "continuity-out.md"
            continuity_file.write_text(
                "## Characters\nJed is alive and well.\n"
                "## Locations\nSaloon.\n"
                "## Changes\nNone.\n"
                "## Unresolved Pressure\nNone.\n"
                "## Next Chapter Must Know\nJed left the horse.\n",
                encoding="utf-8",
            )
            errors = chain.check_continuity_out_content(continuity_file)
            self.assertEqual(errors, [])

    def test_check_continuity_out_content_missing_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            continuity_file = tmp_path / "continuity-out.md"
            continuity_file.write_text(
                "## Characters\nJed is alive.\n"
                "## Locations\nSaloon.\n",
                encoding="utf-8",
            )
            errors = chain.check_continuity_out_content(continuity_file)
            self.assertTrue(len(errors) > 0)
            self.assertTrue(any("Missing section" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
