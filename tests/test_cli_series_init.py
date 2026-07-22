#!/usr/bin/env python3
"""CLI tests for current-directory series initialization."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bookforge.core import series
from bookforge import cli


class TestCliSeriesInit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.empty_series_dir = Path(self.temp_dir.name) / "the-calling"
        self.empty_series_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_init_uses_current_directory(self):
        with patch("bookforge.cli.Path.cwd", return_value=self.empty_series_dir):
            self.assertEqual(cli.main(["init"]), 0)
        self.assertTrue((self.empty_series_dir / "series.json").exists())

    def test_cli_book_init_uses_current_series_directory(self):
        series.initialize_series_workspace(self.empty_series_dir)
        with patch("bookforge.cli.Path.cwd", return_value=self.empty_series_dir):
            self.assertEqual(cli.main(["book-init", "book-1"]), 0)
        self.assertTrue((self.empty_series_dir / "books" / "book-1").is_dir())

    def test_cli_book_init_returns_error_for_invalid_slug(self):
        series.initialize_series_workspace(self.empty_series_dir)
        with patch("bookforge.cli.Path.cwd", return_value=self.empty_series_dir):
            self.assertEqual(cli.main(["book-init", "Book 1"]), 1)


if __name__ == "__main__":
    unittest.main()
