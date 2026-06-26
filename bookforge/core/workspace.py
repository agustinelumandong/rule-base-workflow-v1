"""Provider workspace naming helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_provider_workspace_name(book_folder: Path, workspace_name: str | None = None) -> str:
    """Return the provider workspace name for a BookForge book folder."""
    if workspace_name and workspace_name.strip():
        return workspace_name.strip()

    parts = Path(book_folder).parts
    if "books" in parts:
        index = len(parts) - 1 - parts[::-1].index("books")
        relative_parts = parts[index + 1 :]
        if relative_parts:
            return "/".join(relative_parts)

    return Path(book_folder).name
