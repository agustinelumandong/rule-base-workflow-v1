import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bookforge.core.western_validator import (
    ValidationMode,
    _find_book_folder,
    _find_chapter_folder,
    _find_draft,
    _find_phase_source,
    _references_dir,
    available_references,
    build_validation_packet,
    determine_mode,
    load_reference,
    references_for_mode,
    validate,
)


class DetermineModeTests(unittest.TestCase):
    def test_outline_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "phase-0.md"
            outline.write_text("# Outline")
            mode, reason = determine_mode(outline)
            self.assertEqual(mode, ValidationMode.OUTLINE)
            self.assertIn("outline", reason.lower())

    def test_outline_file_phase_00(self):
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "phase-00.md"
            outline.write_text("# Outline")
            mode, _ = determine_mode(outline)
            self.assertEqual(mode, ValidationMode.OUTLINE)

    def test_dialogue_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "dialogue-scene.md"
            f.write_text("Hello")
            mode, reason = determine_mode(f)
            self.assertEqual(mode, ValidationMode.DIALOGUE)
            self.assertIn("dialogue", reason.lower())

    def test_historical_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "historical-notes.md"
            f.write_text("History")
            mode, reason = determine_mode(f)
            self.assertEqual(mode, ValidationMode.HISTORICAL)

    def test_chapter_folder_with_scene(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01"
            chapter.mkdir()
            (chapter / "scene-breakdown.md").write_text("## BEAT 1")
            mode, reason = determine_mode(chapter)
            self.assertEqual(mode, ValidationMode.SCENE)

    def test_chapter_folder_with_draft_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01"
            chapter.mkdir()
            (chapter / "chapter-01.md").write_text("Draft text.")
            mode, reason = determine_mode(chapter)
            self.assertEqual(mode, ValidationMode.CHAPTER)

    def test_book_folder_manuscript(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp)
            (book / "rulebook.md").write_text("# Rules")
            (book / "chapters").mkdir()
            (book / "chapters" / "chapter-01").mkdir()
            mode, reason = determine_mode(book)
            self.assertEqual(mode, ValidationMode.MANUSCRIPT)

    def test_user_specified_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "random.md"
            f.write_text("x")
            mode, reason = determine_mode(f, "outline")
            self.assertEqual(mode, ValidationMode.OUTLINE)

    def test_user_specified_mode_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "x.md"
            f.write_text("x")
            mode, reason = determine_mode(f, "invalid")
            self.assertNotEqual(mode.value, "invalid")


class FindHelpersTests(unittest.TestCase):
    def test_find_book_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp)
            (book / "rulebook.md").write_text("")
            (book / "chapters").mkdir()
            result = _find_book_folder(book / "chapters" / "chapter-01" / "scene-breakdown.md")
            self.assertEqual(result, book)

    def test_find_book_folder_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _find_book_folder(Path(tmp) / "nonexistent")
            self.assertIsNone(result)

    def test_find_chapter_folder_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01"
            chapter.mkdir()
            folder = _find_chapter_folder(chapter)
            self.assertEqual(folder, chapter)

    def test_find_chapter_folder_no_match(self):
        folder = _find_chapter_folder(Path("/some/path/not-a-chapter"))
        self.assertIsNone(folder)

    def test_find_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01"
            chapter.mkdir()
            draft = chapter / "chapter-01.md"
            draft.write_text("x")
            result = _find_draft(chapter)
            self.assertEqual(result, draft)

    def test_find_draft_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01"
            chapter.mkdir()
            result = _find_draft(chapter)
            self.assertIsNone(result)

    def test_find_phase_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp)
            (book / "phase-0.md").write_text("")
            result = _find_phase_source(book)
            self.assertEqual(result, book / "phase-0.md")

    def test_find_phase_source_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp)
            (book / "outline.md").write_text("")
            result = _find_phase_source(book)
            self.assertEqual(result, book / "outline.md")

    def test_find_phase_source_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _find_phase_source(Path(tmp))
            self.assertIsNone(result)


class ReferencesTests(unittest.TestCase):
    def test_references_dir_exists(self):
        ref_dir = _references_dir()
        self.assertTrue(ref_dir.is_dir(), f"References directory not found: {ref_dir}")

    def test_available_references(self):
        refs = available_references()
        self.assertIn("validation-modes.md", refs)
        self.assertIn("story-logic-and-causality.md", refs)
        self.assertIn("character-dialogue-and-prose.md", refs)
        self.assertIn("western-tone-and-subgenres.md", refs)
        self.assertIn("continuity-outlines-and-scoring.md", refs)
        self.assertIn("historical-authenticity.md", refs)

    def test_load_reference(self):
        text = load_reference("validation-modes.md")
        self.assertIn("mode", text.lower())

    def test_load_reference_missing(self):
        text = load_reference("nonexistent.md")
        self.assertIn("not found", text)

    def test_references_for_mode_outline(self):
        refs = references_for_mode(ValidationMode.OUTLINE)
        self.assertIn("story-logic-and-causality.md", refs)
        self.assertNotIn("character-dialogue-and-prose.md", refs)

    def test_references_for_mode_scene(self):
        refs = references_for_mode(ValidationMode.SCENE)
        self.assertIn("character-dialogue-and-prose.md", refs)

    def test_references_for_mode_manuscript(self):
        refs = references_for_mode(ValidationMode.MANUSCRIPT)
        self.assertEqual(len(refs), 7)


class ValidationPacketTests(unittest.TestCase):
    def test_build_packet_outline(self):
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "phase-0.md"
            outline.write_text("# Outline\n\nChapter 1 begins.")
            packet = build_validation_packet(outline)
            self.assertIn("Western Manuscript Validation Packet", packet)
            self.assertIn("Validation Mode", packet)
            self.assertIn("Validation Criteria", packet)
            self.assertIn("Content to Validate", packet)
            self.assertIn("Validation Report (fill below)", packet)

    def test_build_packet_manuscript(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp)
            (book / "rulebook.md").write_text("# Rules\n\nDo not invent.")
            (book / "mood-lock.md").write_text("Tone: gritty")
            (book / "chapter-summaries.md").write_text("## Chapter 1\nSetup")
            chapters = book / "chapters"
            chapters.mkdir()
            ch1 = chapters / "chapter-01"
            ch1.mkdir()
            (ch1 / "chapter-01.md").write_text("Alden rode into town.")
            (ch1 / "scene-breakdown.md").write_text("## BEAT 1\nAlden arrives.")
            packet = build_validation_packet(book)
            self.assertIn("Manuscript", packet)
            self.assertIn("rulebook", packet.lower() or "rules" in packet)

    def test_build_packet_with_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "phase-0.md"
            outline.write_text("# Outline")
            out_file = Path(tmp) / "report.md"
            from bookforge.core.western_validator import cmd_validate_western
            import argparse
            args = argparse.Namespace(path=str(outline), mode=None, output=str(out_file))
            rc = cmd_validate_western(args)
            self.assertEqual(rc, 0)
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("Western Manuscript Validation", content)

    def test_build_packet_nonexistent_path(self):
        from bookforge.core.western_validator import cmd_validate_western
        import argparse
        args = argparse.Namespace(path="/nonexistent/path", mode=None, output=None)
        rc = cmd_validate_western(args)
        self.assertEqual(rc, 2)

    def test_validate_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "dialogue-test.md"
            f.write_text("Howdy, partner.")
            result = validate(f, ValidationMode.DIALOGUE)
            self.assertIn("Validation packet built", result)


class CollectContentTests(unittest.TestCase):
    def test_outline_content_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            outline = Path(tmp) / "phase-0.md"
            outline.write_text("# Outline\nChapter 1 content.")
            packet = build_validation_packet(outline)
            self.assertIn("Chapter 1 content.", packet)

    def test_scene_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01"
            chapter.mkdir()
            (chapter / "scene-breakdown.md").write_text("## BEAT 1\nShootout.")
            packet = build_validation_packet(chapter)
            self.assertIn("Shootout.", packet)

    def test_chapter_content_with_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            chapter = Path(tmp) / "chapter-01"
            chapter.mkdir()
            (chapter / "chapter-01.md").write_text("Alden drew his revolver.")
            packet = build_validation_packet(chapter)
            self.assertIn("Alden drew his revolver.", packet)

    def test_book_content_with_rulebook(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp)
            (book / "rulebook.md").write_text("# Rulebook\nNo anachronisms.")
            (book / "chapters").mkdir()
            (book / "chapters" / "chapter-01").mkdir()
            packet = build_validation_packet(book)
            self.assertIn("No anachronisms.", packet)


if __name__ == "__main__":
    unittest.main()
