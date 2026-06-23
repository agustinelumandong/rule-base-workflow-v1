#!/usr/bin/env python3
"""Unit tests for the BookForge scene and patch CLI commands."""

import io
import os
import shutil
import unittest
from argparse import Namespace
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
import yaml

from bookforge.cli import cmd_scene, cmd_patch


class TestScenePatchCli(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("tests/temp_test_cli").resolve()
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # Write default world-state.json
        (self.tmp_dir / "world-state.json").write_text("{}", encoding="utf-8")
        (self.tmp_dir / "rulebook.md").write_text("# Rulebook\n", encoding="utf-8")

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_cmd_scene_init(self):
        args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            scene_command="init",
            target_words=3000
        )
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cmd_scene(args)

        self.assertEqual(code, 0)
        m_path = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "manifest.yml"
        self.assertTrue(m_path.exists())
        data = yaml.safe_load(m_path.read_text(encoding="utf-8"))
        self.assertEqual(data["target_words"], 3000)

    def test_cmd_scene_packet(self):
        # First init the manifest
        init_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            scene_command="init",
            target_words=2000
        )
        cmd_scene(init_args)

        # Now test packet generation
        packet_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            scene_command="packet"
        )
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cmd_scene(packet_args)

        self.assertEqual(code, 0)
        packet_path = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01" / "generation-packet.md"
        self.assertTrue(packet_path.exists())
        content = packet_path.read_text(encoding="utf-8")
        self.assertIn("# Scene Context Packet: scene-01 (chapter-01)", content)

    def test_cmd_patch_build_and_splice(self):
        # Init manifest
        init_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            scene_command="init",
            target_words=100
        )
        cmd_scene(init_args)

        # Create original draft
        folder = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01"
        draft_p = folder / "draft.md"
        draft_p.write_text("Hello world.\nThe original draft goes here.\nGoodbye world.", encoding="utf-8")

        # Build patch
        patch_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            patch_command="build",
            failed_rules=["Rule X failed"],
        )
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = cmd_patch(patch_args)

        self.assertEqual(code, 0)
        self.assertTrue((folder / "patch-packet.md").exists())

        # Write replacement draft to replacement.md
        # This has word count 105 which is within 80-120 range (±20% of 100)
        # Note: word count of clean draft is 105 words.
        clean_text = "A replacement segment of prose is placed here. " * 12
        (folder / "replacement.md").write_text(
            f"```markdown\n"
            f"The original draft goes here.\n"
            f"{clean_text}\n"
            f"Goodbye world.\n"
            f"```",
            encoding="utf-8"
        )

        # Splice patch
        splice_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            patch_command="splice"
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cmd_patch(splice_args)

        self.assertEqual(code, 0, f"Splice failed: {stderr.getvalue()}")
        self.assertTrue(draft_p.exists())
        self.assertIn("A replacement segment", draft_p.read_text(encoding="utf-8"))

    def test_patch_apply_self_copy(self):
        # Init manifest
        init_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            scene_command="init",
            target_words=100
        )
        cmd_scene(init_args)

        # Create original draft
        folder = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01"
        draft_p = folder / "draft.md"
        draft_text = "Hello world.\nThe original draft goes here.\nGoodbye world."
        draft_p.write_text(draft_text, encoding="utf-8")

        # Copy the replacement file to target path replacement.md directly
        repl_p = folder / "replacement.md"
        clean_text = "A replacement segment of prose is placed here. " * 12
        repl_p.write_text(
            f"```markdown\n"
            f"The original draft goes here.\n"
            f"{clean_text}\n"
            f"Goodbye world.\n"
            f"```",
            encoding="utf-8"
        )

        # Now apply patch by passing --from-file pointing directly to the replacement.md
        apply_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            patch_command="apply",
            from_file=str(repl_p),
            force=True
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cmd_patch(apply_args)

        # It should succeed (exit code 0) and not raise SameFileError
        self.assertEqual(code, 0, f"Apply self-copy failed: {stderr.getvalue()}")
        self.assertTrue(draft_p.exists())
        self.assertIn("A replacement segment", draft_p.read_text(encoding="utf-8"))

    def test_invalid_prose_does_not_mutate_draft(self):
        # Init manifest
        init_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            scene_command="init",
            target_words=1000
        )
        cmd_scene(init_args)

        # Create original draft
        folder = self.tmp_dir / "changes" / "chapter-01" / "scenes" / "scene-01"
        draft_p = folder / "draft.md"
        original_draft = "Hello world.\nThe original draft goes here.\nGoodbye world."
        draft_p.write_text(original_draft, encoding="utf-8")

        # Write too short replacement (invalid merged prose)
        repl_p = folder / "replacement.md"
        repl_p.write_text(
            f"```markdown\n"
            f"The original draft goes here.\n"
            f"Replacement is too short.\n"
            f"Goodbye world.\n"
            f"```",
            encoding="utf-8"
        )

        # Apply patch
        apply_args = Namespace(
            book_folder=str(self.tmp_dir),
            scene_id="scene-01",
            chapter="chapter-01",
            patch_command="apply",
            from_file=None,
            force=True
        )
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = cmd_patch(apply_args)

        # It should fail validation and return non-zero exit code
        self.assertNotEqual(code, 0)
        # The original draft file must NOT be mutated
        self.assertEqual(draft_p.read_text(encoding="utf-8"), original_draft)


if __name__ == "__main__":
    unittest.main()

