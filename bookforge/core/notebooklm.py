"""BookForge NotebookLM Integration Core Module."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def is_nlm_available() -> bool:
    """Verifies that the `nlm` CLI executable is installed and available in PATH."""
    return shutil.which("nlm") is not None


def get_auth_status() -> dict[str, str | bool]:
    """Checks the auth status of `nlm` by running `nlm login --check` and parsing output."""
    if not is_nlm_available():
        return {"authenticated": False, "email": "", "error": "nlm CLI not installed"}

    try:
        res = subprocess.run(
            ["nlm", "login", "--check"],
            capture_output=True,
            text=True,
            check=False
        )
        output = res.stdout + "\n" + res.stderr
        
        # Look for typical email patterns or confirmation text
        # Example output: "Session active for user@gmail.com" or "Logged in as user@gmail.com"
        email_match = re.search(r"([\w\.-]+@[\w\.-]+\.\w+)", output)
        if email_match and res.returncode == 0:
            return {
                "authenticated": True,
                "email": email_match.group(1),
                "error": ""
            }
        
        # Check if output contains a known success indicator
        if "configured" in output.lower() or "active" in output.lower():
            return {
                "authenticated": True,
                "email": email_match.group(1) if email_match else "unknown",
                "error": ""
            }

        return {
            "authenticated": False,
            "email": "",
            "error": "Not authenticated. Run 'nlm login' to sign in."
        }
    except Exception as e:
        return {
            "authenticated": False,
            "email": "",
            "error": f"Error checking auth: {str(e)}"
        }


def list_notebooks() -> list[dict[str, str]]:
    """Runs `nlm notebook list --json` and returns parsed notebooks."""
    if not is_nlm_available():
        return []

    try:
        res = subprocess.run(
            ["nlm", "notebook", "list", "--json"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            try:
                data = json.loads(res.stdout)
                if isinstance(data, list):
                    return [
                        {
                            "id": str(nb.get("id", nb.get("notebook_id", ""))),
                            "title": str(nb.get("title", nb.get("name", "Untitled Notebook"))),
                            "sources": str(nb.get("source_count", nb.get("sources", "0")))
                        }
                        for nb in data
                    ]
            except json.JSONDecodeError:
                pass

        # Fallback to parsing text output line by line if JSON fails or is not returned
        # Typical text output: "  * UUID - Title (X sources)"
        notebooks = []
        for line in res.stdout.splitlines():
            # Match UUID (8-4-4-4-12) and titles
            match = re.search(
                r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\s*-\s*([^(]+)(?:\((\d+)\s+sources?\))?",
                line,
                re.IGNORECASE
            )
            if match:
                notebooks.append({
                    "id": match.group(1),
                    "title": match.group(2).strip(),
                    "sources": match.group(3) or "0"
                })
        return notebooks
    except Exception:
        return []


def get_associated_notebook(book_folder: Path) -> dict[str, str] | None:
    """Reads `loop-state.json` inside the book folder to fetch linked notebook details."""
    state_file = book_folder / "loop-state.json"
    if not state_file.exists():
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        nb_id = data.get("notebook_id")
        nb_title = data.get("notebook_title")
        if nb_id:
            return {"id": nb_id, "title": nb_title or "Associated Notebook"}
    except Exception:
        pass
    return None


def set_associated_notebook(book_folder: Path, notebook_id: str, title: str) -> None:
    """Persists the linked notebook ID and title inside `loop-state.json`."""
    state_file = book_folder / "loop-state.json"
    data = {}
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    data["notebook_id"] = notebook_id
    data["notebook_title"] = title
    data["last_status_update"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def query_notebook(notebook_id: str, query: str) -> str:
    """Queries the given notebook with a specific question using `nlm notebook query`."""
    if not is_nlm_available():
        return "Error: nlm CLI is not installed or available."

    try:
        res = subprocess.run(
            ["nlm", "notebook", "query", notebook_id, query],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0:
            return res.stdout.strip()
        else:
            return f"Query failed with exit code {res.returncode}:\n{res.stderr.strip()}"
    except Exception as e:
        return f"Error during query execution: {str(e)}"


def sync_research_to_pack(book_folder: Path, notebook_id: str) -> bool:
    """Queries NotebookLM for key context and writes/syncs it to the local `research-pack.md` file."""
    prompt = (
        "Consolidate all historical details, facts, names, timeline events, and canon settings "
        "present in the sources into a structured reference guide. Format this response in markdown "
        "using clean headers and bullet points. Do not invent any outside info."
    )
    result = query_notebook(notebook_id, prompt)
    if result.startswith("Error") or "Query failed" in result:
        return False

    # Try to parse as JSON to extract clean markdown answer
    clean_result = result
    try:
        data = json.loads(result)
        if isinstance(data, dict) and "answer" in data:
            clean_result = data["answer"]
    except json.JSONDecodeError:
        pass

    from bookforge.core.research import get_research_pack_path, merge_research_pack_contents
    research_pack_path = get_research_pack_path(book_folder)
    
    # Read existing content if it exists to do incremental merge
    old_body = ""
    if research_pack_path.exists():
        old_text = research_pack_path.read_text(encoding="utf-8")
        match = re.search(r"^#+\s+", old_text, re.MULTILINE)
        if match:
            first_header_idx = match.start()
            if old_text[first_header_idx:].startswith("# Research Pack"):
                next_header = re.search(r"^##+\s+", old_text[first_header_idx + len("# Research Pack"):], re.MULTILINE)
                if next_header:
                    old_body = old_text[first_header_idx + len("# Research Pack") + next_header.start():]
                else:
                    old_body = old_text[first_header_idx:]
            else:
                old_body = old_text[first_header_idx:]

    new_body = clean_result
    match = re.search(r"^##+\s+", clean_result, re.MULTILINE)
    if match:
        new_body = clean_result[match.start():]

    # Merge body sections
    merged_body = merge_research_pack_contents(old_body, new_body)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"""# Research Pack

> [!NOTE]
> Automatically synced from NotebookLM notebook (ID: `{notebook_id}`) on {timestamp}.

{merged_body.strip()}
"""
    research_pack_path.write_text(content, encoding="utf-8")
    return True


def upload_local_sources(book_folder: Path, notebook_id: str) -> list[str]:
    """Uploads the local rules, mood-lock, outline, and drafts as sources to NotebookLM.
    
    Returns a list of filenames that were successfully processed/uploaded.
    """
    if not is_nlm_available():
        return []

    files_to_upload: list[Path] = []
    
    # Core outline/summaries
    for name in ("rulebook.md", "mood-lock.md", "chapter-summaries.md"):
        path = book_folder / name
        if path.exists():
            files_to_upload.append(path)

    # We also check for outlines in the phase-0 folder
    phase_0_dir = book_folder / "phase-0"
    if phase_0_dir.is_dir():
        files_to_upload.extend(phase_0_dir.glob("*.md"))

    # Drafts
    chapters_dir = book_folder / "chapters"
    if chapters_dir.is_dir():
        files_to_upload.extend(chapters_dir.glob("chapter-*/chapter-*.md"))
        epilogue_path = chapters_dir / "epilogue" / "epilogue.md"
        if epilogue_path.exists():
            files_to_upload.append(epilogue_path)

    uploaded = []
    for filepath in sorted(files_to_upload):
        try:
            res = subprocess.run(
                ["nlm", "source", "add", notebook_id, "--file", str(filepath), "--wait"],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                uploaded.append(filepath.name)
        except Exception:
            pass

    return uploaded
