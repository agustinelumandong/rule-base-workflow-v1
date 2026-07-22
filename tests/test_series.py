#!/usr/bin/env python3
"""Unit tests for the BookForge Multi-Book Series features."""

import json
import unittest
import tempfile
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from bookforge import config
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


class TestSeriesWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.empty_series_dir = Path(self.temp_dir.name) / "the-calling"
        self.empty_series_dir.mkdir()
        self.uninitialized_dir = Path(self.temp_dir.name) / "uninitialized"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialize_series_workspace_creates_only_series_files(self):
        created = series.initialize_series_workspace(self.empty_series_dir)

        for name in (
            "series.json",
            "series-bible.md",
            "series-research-pack.md",
            "settings.json",
            "AGENTS.md",
        ):
            self.assertTrue((self.empty_series_dir / name).exists())
        self.assertTrue((self.empty_series_dir / "books").is_dir())
        self.assertTrue((self.empty_series_dir / "proposed").is_dir())
        self.assertFalse((self.empty_series_dir / "books" / "book-1").exists())
        self.assertIn("Created series workspace", created[0])

        agents = (self.empty_series_dir / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(
            "Approved canon paths: series-bible.md, settings.json, and each book's phase-0.md and rulebook.md.",
            agents,
        )
        self.assertIn("Research is approved reference material, not canon.", agents)

        initialized = series.initialize_series_workspace(self.empty_series_dir)
        self.assertEqual(
            initialized,
            [f"Series workspace already initialized: {self.empty_series_dir}"],
        )

    def test_initialize_series_workspace_rejects_unowned_nonempty_folder(self):
        (self.empty_series_dir / "notes.md").write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            series.initialize_series_workspace(self.empty_series_dir)

    def test_initialize_book_in_series_creates_book_below_books_dir(self):
        series.initialize_series_workspace(self.empty_series_dir)
        series.initialize_book_in_series(self.empty_series_dir, "book-1")
        book = self.empty_series_dir / "books" / "book-1"

        for name in (
            "phase-0.md",
            "rulebook.md",
            "mood-lock.md",
            "chapter-summaries.md",
        ):
            self.assertTrue((book / name).exists())
        self.assertTrue((book / "chapters").is_dir())
        self.assertEqual(
            json.loads((self.empty_series_dir / "series.json").read_text(encoding="utf-8"))["books"],
            ["book-1"],
        )

    def test_initialize_book_in_series_rejects_bad_slug_and_missing_series(self):
        with self.assertRaises(ValueError):
            series.initialize_book_in_series(self.empty_series_dir, "Book 1")
        with self.assertRaises(FileNotFoundError):
            series.initialize_book_in_series(self.uninitialized_dir, "book-1")

    def test_initialize_book_in_series_validates_series_data_before_scaffolding(self):
        series.initialize_series_workspace(self.empty_series_dir)

        for series_data, error, book_slug in (
            ("{", json.JSONDecodeError, "book-1"),
            (json.dumps({"books": {}}), ValueError, "book-2"),
        ):
            with self.subTest(series_data=series_data):
                (self.empty_series_dir / "series.json").write_text(series_data, encoding="utf-8")
                with self.assertRaises(error):
                    series.initialize_book_in_series(self.empty_series_dir, book_slug)
                self.assertFalse((self.empty_series_dir / "books" / book_slug).exists())

    def test_bundled_templates_include_book_scaffold_files(self):
        for name in (
            "phase-0.md",
            "rulebook.md",
            "mood-lock.md",
            "chapter-summaries.md",
        ):
            self.assertTrue((config.BUNDLED_TEMPLATES_DIR / name).is_file())

    def test_distribution_includes_book_templates(self):
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as dist_dir:
            build_dir = Path(dist_dir) / "build"
            subprocess.run(
                [
                    sys.executable,
                    "setup.py",
                    "egg_info",
                    "--egg-base",
                    dist_dir,
                    "build",
                    "--build-base",
                    str(build_dir),
                    "bdist_wheel",
                    "--bdist-dir",
                    str(build_dir),
                    "--dist-dir",
                    dist_dir,
                ],
                cwd=project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            wheel = next(Path(dist_dir).glob("bookforge-*.whl"))
            with zipfile.ZipFile(wheel) as archive:
                names = archive.namelist()

        for name in (
            "phase-0.md",
            "rulebook.md",
            "mood-lock.md",
            "chapter-summaries.md",
        ):
            self.assertIn(f"bookforge/templates/{name}", names)


if __name__ == "__main__":
    unittest.main()
