import unittest
from pathlib import Path

from bookforge.core import scanner


class SourceFormatScanTests(unittest.TestCase):
    def test_act_word_count_does_not_become_book_target(self):
        target = scanner.resolve_target(
            Path("books/test-book"),
            """# Test Book

## Overall Plot Outline

### Act 1: Trail Work (Chapters 1-7, ~7,400 words)

**Chapter 1: First Blood (~1,100 words)**
Chapter details.
""",
        )

        self.assertEqual(target.words, 30000)
        self.assertEqual(target.source, "default")

    def test_explicit_book_target_is_used(self):
        target = scanner.resolve_target(
            Path("books/test-book"),
            """# Test Book

Book-level target: ~30,000 words

### Act 1: Trail Work (Chapters 1-7, ~7,400 words)
""",
        )

        self.assertEqual(target.words, 30000)
        self.assertEqual(target.source, "source")


if __name__ == "__main__":
    unittest.main()
