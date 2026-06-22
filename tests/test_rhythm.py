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
