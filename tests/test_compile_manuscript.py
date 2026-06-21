import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "manuscript-workflow-orchestrator"
    / "scripts"
    / "compile_manuscript.py"
)


def load_compiler():
    spec = importlib.util.spec_from_file_location("compile_manuscript", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CompileManuscriptTests(unittest.TestCase):
    def test_read_title_present(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text("# The Iron Trail\nSome details.", encoding="utf-8")
            
            title = compiler.read_title(book_folder)
            self.assertEqual(title, "# The Iron Trail")

    def test_read_title_missing(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            title = compiler.read_title(book_folder)
            self.assertIsNone(title)

    def test_discover_drafts_and_compile(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text("# Test Title", encoding="utf-8")
            
            chapters_dir = book_folder / "chapters"
            
            # create chapter-01
            ch1_dir = chapters_dir / "chapter-01"
            ch1_dir.mkdir(parents=True)
            (ch1_dir / "chapter-01.md").write_text("Chapter one draft prose.", encoding="utf-8")
            
            # create chapter-02
            ch2_dir = chapters_dir / "chapter-02"
            ch2_dir.mkdir(parents=True)
            (ch2_dir / "chapter-02.md").write_text("Chapter two draft prose.", encoding="utf-8")

            # create epilogue
            epi_dir = chapters_dir / "epilogue"
            epi_dir.mkdir(parents=True)
            (epi_dir / "epilogue.md").write_text("Epilogue draft prose.", encoding="utf-8")

            output_file = book_folder / "output.md"
            draft_count, word_count = compiler.compile_manuscript(book_folder, output_file, include_title=True)
            
            self.assertEqual(draft_count, 3)
            compiled_content = output_file.read_text(encoding="utf-8")
            
            self.assertIn("# Test Title", compiled_content)
            self.assertIn("Chapter one draft prose.", compiled_content)
            self.assertIn("Chapter two draft prose.", compiled_content)
            self.assertIn("Epilogue draft prose.", compiled_content)
            
            # Verify ordering: Title first, then ch1, then ch2, then epilogue
            parts = compiled_content.split("\n\n---\n\n")
            self.assertEqual(len(parts), 4)
            self.assertEqual(parts[0], "# Test Title")
            self.assertEqual(parts[1], "Chapter one draft prose.")
            self.assertEqual(parts[2], "Chapter two draft prose.")
            self.assertEqual(parts[3].strip(), "Epilogue draft prose.")

    def test_compile_raises_on_missing_or_empty_draft(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            chapters_dir = book_folder / "chapters"
            ch1_dir = chapters_dir / "chapter-01"
            ch1_dir.mkdir(parents=True)
            # empty file
            (ch1_dir / "chapter-01.md").write_text("   ", encoding="utf-8")

            output_file = book_folder / "output.md"
            with self.assertRaises(RuntimeError):
                compiler.compile_manuscript(book_folder, output_file, include_title=False)


if __name__ == "__main__":
    unittest.main()
