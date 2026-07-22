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

    def test_chapter_titles_accepts_em_dash_separator(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            summaries = Path(tmp) / "chapter-summaries.md"
            summaries.write_text(
                "## Chapter 1 — First Steps\n", encoding="utf-8"
            )

            self.assertEqual(compiler.chapter_titles(Path(tmp)), {1: "First Steps"})

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

    def test_discover_drafts_excludes_chapter_review_records(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            chapter_dir = book_folder / "chapters" / "chapter-01"
            chapter_dir.mkdir(parents=True)
            (chapter_dir / "chapter-01.md").write_text(
                "Chapter one draft prose.", encoding="utf-8"
            )
            (chapter_dir / "chapter-review.md").write_text(
                "# Chapter Review\n\nNot manuscript prose.", encoding="utf-8"
            )

            self.assertEqual(
                compiler.discover_drafts(book_folder), [chapter_dir / "chapter-01.md"]
            )

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

<<<<<<< Updated upstream
=======
    def test_compile_docx_writes_reopenable_manuscript_with_book_layout(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            self.create_two_chapter_book(book_folder)
            output_file = book_folder / "manuscript.docx"

            draft_count, word_count = compiler.compile_docx(
                book_folder, output_file, include_title=True
            )

            self.assertEqual(draft_count, 2)
            self.assertGreater(word_count, 0)
            self.assertTrue(output_file.exists())

            document = Document(output_file)
            paragraph_texts = [paragraph.text for paragraph in document.paragraphs]
            self.assertEqual(paragraph_texts[0], "Test Saga")
            self.assertEqual(paragraph_texts[1], "Test Title")
            self.assertEqual(paragraph_texts[2], "Book 7")
            self.assertLess(paragraph_texts.index("Chapter 1: First Steps"), paragraph_texts.index("Chapter one body prose."))
            self.assertLess(
                paragraph_texts.index("Chapter one body prose."),
                paragraph_texts.index("Chapter 2: Last Steps"),
            )
            self.assertLess(paragraph_texts.index("Chapter 2: Last Steps"), paragraph_texts.index("Chapter two body prose."))

            for title_paragraph in document.paragraphs[:3]:
                self.assertEqual(title_paragraph.alignment, 1)
                self.assertTrue(title_paragraph.runs[0].bold)
            self.assertGreater(document.paragraphs[1].runs[0].font.size, Pt(12))

            normal_style = document.styles["Normal"]
            self.assertEqual(normal_style.font.name, "Times New Roman")
            self.assertEqual(normal_style.font.size, Pt(12))

            body_paragraph = next(
                paragraph
                for paragraph in document.paragraphs
                if paragraph.text == "Chapter one body prose."
            )
            self.assertEqual(body_paragraph.paragraph_format.line_spacing, 1)
            self.assertEqual(body_paragraph.paragraph_format.first_line_indent, Inches(0))
            self.assertTrue(document.element.body.xpath(".//w:br[@w:type='page']"))

    def test_book2_title_page_uses_reader_facing_metadata(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text(
                "# The Calling: A Search for Kin\n\n"
                "Book 002 of The Calling series\n",
                encoding="utf-8",
            )
            chapter_dir = book_folder / "chapters" / "chapter-01"
            chapter_dir.mkdir(parents=True)
            (chapter_dir / "chapter-01.md").write_text(
                "# Chapter 1\n\nReader-facing body.", encoding="utf-8"
            )

            output_file = book_folder / "book-2.docx"
            compiler.compile_docx(book_folder, output_file, include_title=True)

            paragraph_texts = [
                paragraph.text for paragraph in Document(output_file).paragraphs
            ]
            self.assertEqual(
                paragraph_texts[:3], ["The Calling", "A Search for Kin", "Book 2"]
            )
            self.assertNotIn("Phase 0: Product Definition", paragraph_texts)

    def test_compile_docx_omits_title_page_when_requested(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            self.create_two_chapter_book(book_folder)
            output_file = book_folder / "manuscript-without-title.docx"

            compiler.compile_docx(book_folder, output_file, include_title=False)

            document = Document(output_file)
            paragraph_texts = [paragraph.text for paragraph in document.paragraphs]
            self.assertNotIn("Test Title", paragraph_texts)
            self.assertNotIn("Test Saga", paragraph_texts)
            self.assertEqual(paragraph_texts[0], "Chapter 1: First Steps")

    def test_compile_docx_does_not_duplicate_plain_chapter_heading(self):
        compiler = load_compiler()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text("# Test Title", encoding="utf-8")
            (book_folder / "chapter-summaries.md").write_text(
                "### ch-001: First Steps\n", encoding="utf-8"
            )
            chapter_dir = book_folder / "chapters" / "chapter-01"
            chapter_dir.mkdir(parents=True)
            (chapter_dir / "chapter-01.md").write_text(
                "Chapter 1: First Steps\n\nChapter body prose.", encoding="utf-8"
            )

            output_file = book_folder / "manuscript.docx"
            compiler.compile_docx(book_folder, output_file, include_title=False)
            paragraph_texts = [paragraph.text for paragraph in Document(output_file).paragraphs]

            self.assertEqual(paragraph_texts.count("Chapter 1: First Steps"), 1)

    def test_validate_output_extension_rejects_mismatched_format(self):
        compiler = load_compiler()

        with self.assertRaisesRegex(RuntimeError, r"\.md"):
            compiler.validate_output_extension(Path("manuscript.docx"), "markdown")

        with self.assertRaisesRegex(RuntimeError, r"\.docx"):
            compiler.validate_output_extension(Path("manuscript.md"), "docx")

    def test_validate_output_extension_accepts_matching_format(self):
        compiler = load_compiler()

        compiler.validate_output_extension(Path("manuscript.md"), "markdown")
        compiler.validate_output_extension(Path("manuscript.docx"), "docx")

>>>>>>> Stashed changes

if __name__ == "__main__":
    unittest.main()
