#!/usr/bin/env python3
"""Unit tests for the BookForge Multi-Book Series features."""

import json
import unittest
import tempfile
import shutil
from pathlib import Path

from bookforge.core import series


class TestSeriesContinuity(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("tests/temp_test_series")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.books_dir = self.tmp_dir / "books"
        self.books_dir.mkdir()

        # Set up a mock series structure:
        # books/
        #   test-saga/
        #     series.json
        #     series-bible.md
        #     series-research-pack.md
        #     book-1/
        #     book-2/
        self.series_dir = self.books_dir / "test-saga"
        self.series_dir.mkdir()

        self.series_json = {
            "name": "Test Family Saga",
            "books": ["book-1", "book-2"]
        }
        (self.series_dir / "series.json").write_text(json.dumps(self.series_json), encoding="utf-8")
        (self.series_dir / "series-bible.md").write_text("# Series Bible\nShared lore.", encoding="utf-8")
        (self.series_dir / "series-research-pack.md").write_text("# Research\nShared history.", encoding="utf-8")

        self.book1_dir = self.series_dir / "book-1"
        self.book1_dir.mkdir()
        self.book2_dir = self.series_dir / "book-2"
        self.book2_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_get_series_info(self):
        # Override parent.parent.name in test to match 'books' by mocking or using exact layout
        # Since book1_dir is series_dir/book-1, and series_dir is books_dir/test-saga,
        # book1_dir.parent.parent.name will be 'books'. This matches the structure!
        info = series.get_series_info(self.book1_dir)
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "Test Family Saga")
        self.assertEqual(Path(info["path"]).resolve(), self.series_dir.resolve())

        # Standalone book under books_dir/standalone
        standalone = self.books_dir / "standalone"
        standalone.mkdir()
        standalone_info = series.get_series_info(standalone)
        self.assertIsNone(standalone_info)

    def test_parse_continuity_sections(self):
        continuity_text = """
## Characters
[Who is alive/dead]
- John Doe is wounded.
- Jane Smith is well.

## Locations
- The saloon is intact.

## Changes
- The gang was defeated.

## Unresolved Pressure
- The gold is still missing.

## Next Chapter Must Know
- Watch out for deputies.
"""
        sections = series.parse_continuity_sections(continuity_text)
        self.assertEqual(sections["Characters"], "- John Doe is wounded.\n- Jane Smith is well.")
        self.assertEqual(sections["Locations"], "- The saloon is intact.")
        self.assertEqual(sections["Changes"], "- The gang was defeated.")
        self.assertEqual(sections["Unresolved Pressure"], "- The gold is still missing.")

    def test_copy_shared_series_resources(self):
        # Delete default setup folders, re-initialize new ones to verify copy
        target_book = self.book2_dir
        rulebook = target_book / "rulebook.md"
        research_pack = target_book / "research-pack.md"

        self.assertFalse(rulebook.exists())
        self.assertFalse(research_pack.exists())

        # Copy resources
        copied = series.copy_shared_series_resources(target_book)
        self.assertTrue(rulebook.exists())
        self.assertTrue(research_pack.exists())
        self.assertEqual(rulebook.read_text(encoding="utf-8"), "# Series Bible\nShared lore.")
        self.assertEqual(research_pack.read_text(encoding="utf-8"), "# Research\nShared history.")
        self.assertIn("Initialized rulebook.md from series-bible.md", copied)
        self.assertIn("Initialized research-pack.md from series-research-pack.md", copied)

    def test_carry_forward_book_continuity(self):
        # Create mock chapter in book-1
        chapters_dir = self.book1_dir / "chapters"
        chapters_dir.mkdir()
        chap1_dir = chapters_dir / "chapter-01"
        chap1_dir.mkdir()

        # Create mock draft and continuity-out
        (chap1_dir / "chapter-01.md").write_text("Prose content.", encoding="utf-8")
        continuity_text = """
## Characters
- Darin Mayweather is alive.

## Locations
- The ranch.

## Changes
- Darin arrived at the ranch.

## Unresolved Pressure
- Darin needs ammunition.
"""
        (chap1_dir / "continuity-out.md").write_text(continuity_text, encoding="utf-8")

        # Run carry-forward into book-2
        (self.book2_dir / "rulebook.md").write_text("# Book 2 Rulebook\n", encoding="utf-8")
        
        msg = series.carry_forward_book_continuity(self.book1_dir, self.book2_dir)
        self.assertIn("Successfully carried forward", msg)

        rulebook_content = (self.book2_dir / "rulebook.md").read_text(encoding="utf-8")
        self.assertIn("Series Carry-Over Continuity (from book-1)", rulebook_content)
        self.assertIn("- Darin Mayweather is alive.", rulebook_content)
        self.assertIn("- Darin arrived at the ranch.", rulebook_content)
        self.assertIn("- Darin needs ammunition.", rulebook_content)


if __name__ == "__main__":
    unittest.main()
