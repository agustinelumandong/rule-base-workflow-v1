"""BookForge NotebookLM Integration Client."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
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
    except (subprocess.SubprocessError, OSError) as e:
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
    except (subprocess.SubprocessError, OSError, ValueError, AttributeError):
        return []


def create_new_notebook(title: str) -> str | None:
    """Creates a new notebook with the given title and returns its UUID."""
    if not is_nlm_available():
        return None

    try:
        res = subprocess.run(
            ["nlm", "notebook", "create", title, "--json"],
            capture_output=True,
            text=True,
            check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            try:
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    # Check for different possible keys in the JSON response
                    nb_id = data.get("id") or data.get("notebook_id") or data.get("notebook", {}).get("id")
                    if nb_id:
                        return str(nb_id)
            except json.JSONDecodeError:
                pass
        
        # Fallback to parsing text output if JSON option is not respected or fails
        output = res.stdout + "\n" + res.stderr
        match = re.search(
            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
            output,
            re.IGNORECASE
        )
        if match:
            return match.group(1)
            
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def query_notebook(notebook_id: str, query: str) -> str:
    """Queries the given notebook with a specific question using `nlm notebook query`."""
    from bookforge.core.adapters.research import NotebookLMBackend
    backend = NotebookLMBackend(Path("."), notebook_id=notebook_id)
    return backend.query(query)
