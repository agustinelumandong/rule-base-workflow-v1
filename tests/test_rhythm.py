#!/usr/bin/env python3
"""Tests for chapter rhythm advisory wording."""

from pathlib import Path
from unittest import mock

from bookforge.core import rhythm
from bookforge.core.length import DraftCount


def test_expanded_oversized_message_does_not_recommend_trimming_by_default(tmp_path):
    book_folder = tmp_path / "books" / "my-book"
    book_folder.mkdir(parents=True)
    (book_folder / "chapter-pacing-plan.md").write_text(
        "| Chapter | Pacing Class |\n"
        "| --- | --- |\n"
        "| Chapter 04 | expanded |\n",
        encoding="utf-8",
    )
    counts = [
        DraftCount(label="Chapter 01", words=1900),
        DraftCount(label="Chapter 02", words=2100),
        DraftCount(label="Chapter 03", words=1800),
        DraftCount(label="Chapter 04", words=2602),
    ]

    with mock.patch("bookforge.core.rhythm.length_checker.find_drafts", return_value=counts):
        report = rhythm.analyze(book_folder)

    messages = [issue.message for issue in report.issues]
    expanded_message = next(message for message in messages if "Chapter 04" in message)
    assert "consider trimming" not in expanded_message
    assert expanded_message == "Chapter 04 is `expanded` and has 2602 words; verify the extra length is source-supported."


def test_analyze_adds_tripwire_warning_when_chapter_exceeds_explicit_range(tmp_path):
    book_folder = tmp_path / "books" / "my-book"
    chapter_folder = book_folder / "chapters" / "chapter-01"
    chapter_folder.mkdir(parents=True)
    (chapter_folder / "chapter-01.md").write_text("Word " * 2500, encoding="utf-8")
    (book_folder / "chapter-pacing-plan.md").write_text(
        "| Chapter | Pacing Class | Elastic Range |\n"
        "| --- | --- | --- |\n"
        "| Chapter 01 | standard | 900-1200 |\n",
        encoding="utf-8",
    )

    report = rhythm.analyze(book_folder)

    messages = [issue.message for issue in report.issues]
    assert any("outside planned range 900-1200" in message for message in messages)


def test_analyze_warns_on_long_uninterrupted_block_and_break_opportunity(tmp_path):
    book_folder = tmp_path / "books" / "my-book"
    chapter_folder = book_folder / "chapters" / "chapter-01"
    chapter_folder.mkdir(parents=True)
    long_lines = "\n".join(f"Jed worked the cabin line {i}." for i in range(260))
    chapter_text = (
        long_lines
        + "\n\nBy morning he crossed to the far meadow.\n\n"
        + "He slept hard and woke to the creek noise."
    )
    (chapter_folder / "chapter-01.md").write_text(chapter_text, encoding="utf-8")

    report = rhythm.analyze(book_folder)

    messages = [issue.message for issue in report.issues]
    assert any("long uninterrupted block" in message.lower() for message in messages)
    assert any("break opportunity" in message.lower() for message in messages)
