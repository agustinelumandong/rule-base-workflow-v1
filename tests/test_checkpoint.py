import pytest
import shutil
from pathlib import Path
from bookforge.core import checkpoint as chk


@pytest.fixture
def temp_book_folder(tmp_path):
    book_dir = tmp_path / "book-test"
    book_dir.mkdir()

    # Create tracked directories
    (book_dir / "changes").mkdir()
    (book_dir / "state").mkdir()
    (book_dir / "spec").mkdir()

    # Add initial files
    (book_dir / "changes" / "chapter-01.md").write_text("Hello Chapter 1", encoding="utf-8")
    (book_dir / "state" / "loop.json").write_text('{"status": "ok"}', encoding="utf-8")
    (book_dir / "spec" / "guardrails.md").write_text("No syndicates allowed.", encoding="utf-8")

    return book_dir


def test_save_and_load_checkpoint(temp_book_folder):
    # Save checkpoint
    chk.save_checkpoint(temp_book_folder, "snap1")

    checkpoint_dir = temp_book_folder / ".bookforge" / "checkpoints" / "snap1"
    assert checkpoint_dir.exists()
    assert (checkpoint_dir / "changes" / "chapter-01.md").read_text(encoding="utf-8") == "Hello Chapter 1"
    assert (checkpoint_dir / "spec" / "guardrails.md").read_text(encoding="utf-8") == "No syndicates allowed."

    # Modify files in current state
    (temp_book_folder / "changes" / "chapter-01.md").write_text("Modified Chapter 1", encoding="utf-8")
    (temp_book_folder / "spec" / "guardrails.md").unlink()
    (temp_book_folder / "state" / "new_file.txt").write_text("Added file", encoding="utf-8")

    # Load/Restore checkpoint
    chk.load_checkpoint(temp_book_folder, "snap1")

    # Verify original state is restored
    assert (temp_book_folder / "changes" / "chapter-01.md").read_text(encoding="utf-8") == "Hello Chapter 1"
    assert (temp_book_folder / "spec" / "guardrails.md").read_text(encoding="utf-8") == "No syndicates allowed."
    assert not (temp_book_folder / "state" / "new_file.txt").exists()


def test_diff_checkpoint(temp_book_folder):
    # Save checkpoint
    chk.save_checkpoint(temp_book_folder, "snap1")

    # Modify a file
    (temp_book_folder / "changes" / "chapter-01.md").write_text("Modified Chapter 1", encoding="utf-8")

    # Add a file
    (temp_book_folder / "state" / "added.txt").write_text("Staged", encoding="utf-8")

    # Delete a file
    (temp_book_folder / "spec" / "guardrails.md").unlink()

    # Generate diff
    diff_text = chk.diff_checkpoint(temp_book_folder, "snap1")

    # Check additions, deletions, modifications
    assert "Modified Chapter 1" in diff_text
    assert "+++ New File: state/added.txt" in diff_text
    assert "--- Deleted File: spec/guardrails.md" in diff_text
    assert "No syndicates allowed." in diff_text


def test_cli_checkpoint_commands(temp_book_folder, monkeypatch):
    from bookforge.cli import main
    import sys

    # 1. Save checkpoint via CLI
    monkeypatch.setattr(sys, "argv", ["bookforge", "checkpoint", "save", "snap_cli", str(temp_book_folder)])
    assert main() == 0

    checkpoint_dir = temp_book_folder / ".bookforge" / "checkpoints" / "snap_cli"
    assert checkpoint_dir.exists()

    # 2. Modify and Diff via CLI
    (temp_book_folder / "changes" / "chapter-01.md").write_text("Modified via CLI", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["bookforge", "checkpoint", "diff", "snap_cli", str(temp_book_folder)])
    assert main() == 0

    # 3. Load via CLI
    monkeypatch.setattr(sys, "argv", ["bookforge", "checkpoint", "load", "snap_cli", str(temp_book_folder)])
    assert main() == 0
    assert (temp_book_folder / "changes" / "chapter-01.md").read_text(encoding="utf-8") == "Hello Chapter 1"

    # 4. Restore via CLI
    (temp_book_folder / "changes" / "chapter-01.md").write_text("Modified again", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["bookforge", "checkpoint", "restore", "snap_cli", str(temp_book_folder)])
    assert main() == 0
    assert (temp_book_folder / "changes" / "chapter-01.md").read_text(encoding="utf-8") == "Hello Chapter 1"
