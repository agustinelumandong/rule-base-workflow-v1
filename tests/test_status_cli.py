#!/usr/bin/env python3
"""Tests for BookForge status argument handling."""

import io
import os
import shutil
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from bookforge.cli import cmd_status


class TestStatusCli(unittest.TestCase):
    def setUp(self):
        self.original_cwd = Path.cwd()
        self.tmp_dir = self.original_cwd / "tests/temp_test_status"
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True)
        os.chdir(self.tmp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_status_requires_book_argument_and_lists_available_books(self):
        Path("books/tex-cade").mkdir(parents=True)
        Path("books/book-example").mkdir(parents=True)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cmd_status(Namespace(book_folder=None))

        self.assertEqual(code, 2)
        self.assertIn("Error: status requires a book name or folder.", stderr.getvalue())
        self.assertIn("Usage: bf status <book-name>", stdout.getvalue())
        self.assertIn("book-example", stdout.getvalue())
        self.assertIn("tex-cade", stdout.getvalue())

    def test_status_resolves_bare_leaf_book_name_under_books_folder(self):
        Path("books/my-book").mkdir(parents=True)
        (Path("books/my-book") / "rulebook.md").write_text("# Rulebook\n", encoding="utf-8")

        with (
            mock.patch("bookforge.cli.context_validator.validate_required_book_files", return_value=([], [])) as validate,
            mock.patch("bookforge.cli.scanner_module.check_gaps", return_value=([], [])),
            mock.patch("bookforge.cli.chain_module.analyze_chain", return_value=(True, [])),
            mock.patch("bookforge.cli.rhythm_module.analyze", side_effect=ValueError("not a leaf book")),
        ):
            code = cmd_status(Namespace(book_folder="my-book"))

        self.assertEqual(code, 0)
        validate.assert_called_once_with(Path("books/my-book"))

    def test_status_lists_child_books_for_series_folder(self):
        Path("books/tex-cade/books-1").mkdir(parents=True)
        Path("books/tex-cade/books-4").mkdir(parents=True)
        (Path("books/tex-cade/books-1") / "rulebook.md").write_text("# Rulebook\n", encoding="utf-8")
        (Path("books/tex-cade/books-4") / "phase-0.md").write_text("# Outline\n", encoding="utf-8")
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            code = cmd_status(Namespace(book_folder="tex-cade"))

        self.assertEqual(code, 0)
        self.assertIn("Available books in tex-cade:", stdout.getvalue())
        self.assertIn("tex-cade/books-1", stdout.getvalue())
        self.assertIn("tex-cade/books-4", stdout.getvalue())

    def test_status_preserves_explicit_books_path(self):
        Path("books/tex-cade/books-4").mkdir(parents=True)
        stdout = io.StringIO()

        with (
            redirect_stdout(stdout),
            mock.patch("bookforge.cli.context_validator.validate_required_book_files", return_value=([], [])) as validate,
            mock.patch("bookforge.cli.scanner_module.check_gaps", return_value=([], [])),
            mock.patch("bookforge.cli.chain_module.analyze_chain", return_value=(True, [])),
            mock.patch("bookforge.cli.rhythm_module.analyze", side_effect=ValueError("not ready")),
        ):
            code = cmd_status(Namespace(book_folder="books/tex-cade/books-4"))

        self.assertEqual(code, 0)
        validate.assert_called_once_with(Path("books/tex-cade/books-4"))
        self.assertIn("Run 'bf run-loop books/tex-cade/books-4'", stdout.getvalue())

    def test_status_prints_chapter_review_summary_from_rhythm_report(self):
        Path("books/my-book").mkdir(parents=True)
        (Path("books/my-book") / "rulebook.md").write_text("# Rulebook\n", encoding="utf-8")
        stdout = io.StringIO()
        rhythm_report = mock.Mock()
        rhythm_report.issues = []
        rhythm_report.review_states = {"chapter-01": "ready", "chapter-02": "needs-rhythm-fix"}

        with (
            redirect_stdout(stdout),
            mock.patch("bookforge.cli.context_validator.validate_required_book_files", return_value=([], [])),
            mock.patch("bookforge.cli.scanner_module.check_gaps", return_value=([], [])),
            mock.patch("bookforge.cli.chain_module.analyze_chain", return_value=(True, [])),
            mock.patch("bookforge.cli.rhythm_module.analyze", return_value=rhythm_report),
        ):
            code = cmd_status(Namespace(book_folder="my-book"))

        self.assertEqual(code, 0)
        self.assertIn("Chapter Review:", stdout.getvalue())
        self.assertIn("chapter-02: needs-rhythm-fix", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
