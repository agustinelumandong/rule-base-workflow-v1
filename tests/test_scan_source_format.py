import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "manuscript-workflow-orchestrator"
    / "scripts"
    / "scan_source_format.py"
)


def load_scanner():
    spec = importlib.util.spec_from_file_location("scan_source_format", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SourceFormatScanTests(unittest.TestCase):
    def test_act_word_count_does_not_become_book_target(self):
        scanner = load_scanner()

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
        scanner = load_scanner()

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
