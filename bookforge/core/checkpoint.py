"""BookForge Checkpoint Management Core Module."""

from __future__ import annotations

import difflib
import os
import shutil
from pathlib import Path

# Directories to track in checkpoints
TRACKED_DIRS = ["changes", "state", "spec"]


def get_checkpoint_dir(book_folder: Path, name: str) -> Path:
    """Returns the path to a specific checkpoint directory."""
    return book_folder / ".bookforge" / "checkpoints" / name


def save_checkpoint(book_folder: Path, name: str) -> None:
    """Saves the current state of tracked directories to a named checkpoint."""
    checkpoint_dir = get_checkpoint_dir(book_folder, name)
    if checkpoint_dir.exists():
        shutil.rmtree(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    for dname in TRACKED_DIRS:
        src = book_folder / dname
        if src.exists():
            dst = checkpoint_dir / dname
            shutil.copytree(src, dst)


def load_checkpoint(book_folder: Path, name: str) -> None:
    """Loads/Restores tracked directories from a named checkpoint."""
    checkpoint_dir = get_checkpoint_dir(book_folder, name)
    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"Checkpoint '{name}' does not exist.")

    for dname in TRACKED_DIRS:
        dst = book_folder / dname
        src = checkpoint_dir / dname
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.exists():
            shutil.copytree(src, dst)


def restore_checkpoint(book_folder: Path, name: str) -> None:
    """Resets the current state to match a named checkpoint (alias/wrapper for load)."""
    load_checkpoint(book_folder, name)


def diff_checkpoint(book_folder: Path, name: str) -> str:
    """Generates unified diff representation between the current state and a checkpoint."""
    checkpoint_dir = get_checkpoint_dir(book_folder, name)
    if not checkpoint_dir.exists():
        raise FileNotFoundError(f"Checkpoint '{name}' does not exist.")

    diff_lines = []

    # Get all files currently under the tracked directories
    current_files: set[Path] = set()
    for dname in TRACKED_DIRS:
        dpath = book_folder / dname
        if dpath.exists():
            for p in dpath.rglob("*"):
                if p.is_file():
                    current_files.add(p.relative_to(book_folder))

    # Get all files in the checkpoint
    checkpoint_files: set[Path] = set()
    for dname in TRACKED_DIRS:
        dpath = checkpoint_dir / dname
        if dpath.exists():
            for p in dpath.rglob("*"):
                if p.is_file():
                    checkpoint_files.add(p.relative_to(checkpoint_dir))

    all_files = sorted(current_files.union(checkpoint_files))

    for rel_path in all_files:
        curr_file = book_folder / rel_path
        chk_file = checkpoint_dir / rel_path

        # Case 1: Added in current (does not exist in checkpoint)
        if curr_file.exists() and not chk_file.exists():
            diff_lines.append(f"+++ New File: {rel_path}")
            try:
                content = curr_file.read_text(encoding="utf-8").splitlines()
                for line in content:
                    diff_lines.append(f"+ {line}")
            except (OSError, UnicodeDecodeError) as e:
                diff_lines.append(f"+ [Binary or unreadable file: {e}]")
            diff_lines.append("")

        # Case 2: Deleted in current (exists in checkpoint but not current)
        elif not curr_file.exists() and chk_file.exists():
            diff_lines.append(f"--- Deleted File: {rel_path}")
            try:
                content = chk_file.read_text(encoding="utf-8").splitlines()
                for line in content:
                    diff_lines.append(f"- {line}")
            except (OSError, UnicodeDecodeError) as e:
                diff_lines.append(f"- [Binary or unreadable file: {e}]")
            diff_lines.append("")

        # Case 3: Exists in both, check for changes
        else:
            try:
                curr_content = curr_file.read_text(encoding="utf-8").splitlines()
                chk_content = chk_file.read_text(encoding="utf-8").splitlines()
                if curr_content != chk_content:
                    file_diff = list(
                        difflib.unified_diff(
                            chk_content,
                            curr_content,
                            fromfile=f"checkpoint/{rel_path}",
                            tofile=f"current/{rel_path}",
                            lineterm=""
                        )
                    )
                    if file_diff:
                        diff_lines.extend(file_diff)
                        diff_lines.append("")
            except (OSError, UnicodeDecodeError):
                # Fallback if binary file
                pass

    return "\n".join(diff_lines)
