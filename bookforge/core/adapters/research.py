"""BookForge Research Adapters Module."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Protocol


class ResearchBackend(Protocol):
    """Protocol defining the interface for research backends."""

    def query(self, query_str: str) -> str:
        """Queries the research database with a text query and returns findings."""
        ...

    def ingest(self, source_path: Path) -> None:
        """Ingests a new research source document/folder into the research database."""
        ...


class ManualBackend:
    """Zero-dependency local plain-text keyword scanner and markdown parser."""

    def __init__(self, book_folder: Path) -> None:
        self.book_folder = book_folder

    def _get_research_pack_path(self) -> Path:
        from bookforge.core.research import get_research_pack_path
        return get_research_pack_path(self.book_folder)

    def query(self, query_str: str) -> str:
        """Scans research-pack.md for matching headers or keywords, returning sections."""
        pack_path = self._get_research_pack_path()
        if not pack_path.exists():
            return "Error: research-pack.md does not exist."

        try:
            content = pack_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading research pack: {e}"

        # Parse sections by headers (e.g. ## Category)
        sections: list[tuple[str, str]] = []
        current_header = ""
        current_lines = []

        for line in content.splitlines():
            line_strip = line.strip()
            if line_strip.startswith("#"):
                if current_header:
                    sections.append((current_header, "\n".join(current_lines).strip()))
                current_header = line_strip
                current_lines = []
            elif current_header:
                current_lines.append(line)

        if current_header:
            sections.append((current_header, "\n".join(current_lines).strip()))

        # Match against query keywords (case-insensitive)
        keywords = [kw.lower() for kw in query_str.split() if len(kw) > 2]
        if not keywords:
            # Fallback to returning the entire pack or first few sections
            return "\n\n".join(f"{h}\n{c}" for h, c in sections[:3])

        matched_sections = []
        for h, c in sections:
            # Score section based on keyword matches
            score = 0
            combined = (h + "\n" + c).lower()
            for kw in keywords:
                if kw in combined:
                    score += 1
            if score > 0:
                matched_sections.append((score, h, c))

        # Sort by score descending
        matched_sections.sort(key=lambda x: x[0], reverse=True)

        if not matched_sections:
            return "No matching research items found."

        return "\n\n".join(f"{h}\n{c}" for _, h, c in matched_sections[:5])

    def ingest(self, source_path: Path) -> None:
        """Merges files or folder contents into the local research-pack.md."""
        from bookforge.core.research import ensure_research_pack, merge_research_pack_contents

        pack_path = ensure_research_pack(self.book_folder)
        try:
            old_content = pack_path.read_text(encoding="utf-8")
        except Exception:
            old_content = ""

        # Ingest single file or directory of markdown/text files
        new_content_blocks = []
        files_to_read = [source_path] if source_path.is_file() else list(source_path.rglob("*.md")) + list(source_path.rglob("*.txt"))

        for f in files_to_read:
            if f.is_file():
                try:
                    new_content_blocks.append(f.read_text(encoding="utf-8"))
                except Exception:
                    pass

        if not new_content_blocks:
            return

        combined_new = "\n\n".join(new_content_blocks)
        merged = merge_research_pack_contents(old_content, combined_new)
        pack_path.write_text(merged, encoding="utf-8")


class NotebookLMBackend:
    """Wrapper backend delegating research tasks to the NotebookLM CLI ('nlm')."""

    def __init__(self, book_folder: Path, notebook_id: str | None = None) -> None:
        self.book_folder = book_folder
        self.notebook_id = notebook_id

    def _get_notebook_id(self) -> str | None:
        if self.notebook_id:
            return self.notebook_id
        from bookforge.core.notebooklm import get_associated_notebook
        info = get_associated_notebook(self.book_folder)
        return info["id"] if info else None

    def query(self, query_str: str) -> str:
        notebook_id = self._get_notebook_id()
        if not notebook_id:
            # Fall back to ManualBackend query if no notebook is associated
            return ManualBackend(self.book_folder).query(query_str)

        try:
            res = subprocess.run(
                ["nlm", "notebook", "query", notebook_id, query_str],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                output = res.stdout.strip()
                # Parse JSON if output is JSON format
                try:
                    data = json.loads(output)
                    if isinstance(data, dict) and "answer" in data:
                        return str(data["answer"])
                except json.JSONDecodeError:
                    pass
                return output
            return f"Error: NotebookLM query failed: {res.stderr.strip()}"
        except Exception as e:
            return f"Error during NotebookLM query execution: {e}"

    def ingest(self, source_path: Path) -> None:
        notebook_id = self._get_notebook_id()
        if not notebook_id:
            # Fall back to ManualBackend ingestion
            ManualBackend(self.book_folder).ingest(source_path)
            return

        files_to_add = [source_path] if source_path.is_file() else list(source_path.rglob("*"))
        for f in files_to_add:
            if f.is_file():
                try:
                    subprocess.run(
                        ["nlm", "source", "add", notebook_id, "--file", str(f), "--wait"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                except Exception:
                    pass


def get_research_backend(book_folder: Path, backend_type: str = "default") -> ResearchBackend:
    """Returns the configured research backend."""
    from bookforge.core.notebooklm import is_nlm_available
    if backend_type == "notebooklm" or (backend_type == "default" and is_nlm_available()):
        # Check if actually associated with a notebook, otherwise fallback to local
        from bookforge.core.notebooklm import get_associated_notebook
        if get_associated_notebook(book_folder):
            return NotebookLMBackend(book_folder)
    return ManualBackend(book_folder)
