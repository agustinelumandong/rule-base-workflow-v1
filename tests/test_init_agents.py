#!/usr/bin/env python3
"""Unit tests for the BookForge init --agents and git integration."""

import unittest
import shutil
import subprocess
from pathlib import Path
from argparse import Namespace

from bookforge.cli import cmd_init


class TestInitAgents(unittest.TestCase):
    def setUp(self):
        # Create a workspace-friendly temp directory for testing init
        self.tmp_dir = Path("tests/temp_test_init")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # Clean up any potential generated global agent files to avoid pollution
        self.agent_files = [
            Path("CLAUDE.md"),
            Path(".cursorrules"),
            Path("copilot-instructions.md"),
            Path("GEMINI.md"),
            Path(".opencode.yml"),
            Path("CODEX.md"),
            Path("ZED.md"),
        ]
        self.backups = {}
        for f in self.agent_files:
            if f.exists():
                self.backups[f] = f.read_text(encoding="utf-8")
                f.unlink()

    def tearDown(self):
        # Clean up temp test directory
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

        # Remove generated agent files
        for f in self.agent_files:
            if f.exists():
                f.unlink()

        # Restore backups
        for f, content in self.backups.items():
            f.write_text(content, encoding="utf-8")

        # Clean up git if initialized in the root by tests
        # We don't initialize git in root, only in temp dir, but if any git files leak, we handle it.

    def test_init_creates_spec_model_routing(self):
        args = Namespace(
            book_folder=str(self.tmp_dir / "my-new-book"),
            carry_from=None,
            agents=None,
            git=False
        )
        code = cmd_init(args)
        self.assertEqual(code, 0)
        
        # Verify model-routing.yml was created in spec directory
        spec_routing = self.tmp_dir / "my-new-book" / "spec" / "model-routing.yml"
        self.assertTrue(spec_routing.exists())
        self.assertIn("personas:", spec_routing.read_text(encoding="utf-8"))

    def test_init_with_agents_creates_files(self):
        args = Namespace(
            book_folder=str(self.tmp_dir / "my-agent-book"),
            carry_from=None,
            agents="claude,cursor,opencode,gemini",
            git=False
        )
        code = cmd_init(args)
        self.assertEqual(code, 0)

        # Verify agent files exist at project root (simulated relative paths)
        self.assertTrue(Path("CLAUDE.md").exists())
        self.assertTrue(Path(".cursorrules").exists())
        self.assertTrue(Path(".opencode.yml").exists())
        self.assertTrue(Path("GEMINI.md").exists())

        # Verify content of .opencode.yml mapping
        opencode_content = Path(".opencode.yml").read_text(encoding="utf-8")
        self.assertIn("small_model:", opencode_content)
        self.assertIn("persona: extractor", opencode_content)

    def test_init_with_git(self):
        # Create a nested temp directory so git is initialized in a self-contained repo
        repo_dir = self.tmp_dir / "test-git-repo"
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        # We must run it from within the repo_dir or specify path.
        # However, cmd_init uses Path("CLAUDE.md") relative to current working directory,
        # so for this unit test we run it normally and check if git subprocess runs successfully.
        args = Namespace(
            book_folder=str(repo_dir / "book-folder"),
            carry_from=None,
            agents="claude",
            git=True
        )
        # Note: running git init might fail if git CLI is not installed, so we wrap it
        # but in this environment it is linux and git is available.
        code = cmd_init(args)
        self.assertEqual(code, 0)
        
        # Check if book folder and spec were created
        self.assertTrue((repo_dir / "book-folder" / "spec" / "model-routing.yml").exists())


if __name__ == "__main__":
    unittest.main()
