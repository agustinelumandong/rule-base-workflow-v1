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
    """Reads `state/notebooklm.json` (or legacy `loop-state.json`) inside the book folder to fetch linked notebook details."""
    state_file = book_folder / "state" / "notebooklm.json"
    legacy_file = book_folder / "loop-state.json"
    
    target_file = state_file
    if not state_file.exists() and legacy_file.exists():
        target_file = legacy_file
        
    if not target_file.exists():
        return None
    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
        nb_id = data.get("notebook_id")
        nb_title = data.get("notebook_title")
        if nb_id:
            return {"id": nb_id, "title": nb_title or "Associated Notebook"}
    except Exception:
        pass
    return None


def set_associated_notebook(book_folder: Path, notebook_id: str, title: str) -> None:
    """Persists the linked notebook ID and title inside `state/notebooklm.json`."""
    state_dir = book_folder / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "notebooklm.json"
    
    data = {}
    legacy_file = book_folder / "loop-state.json"
    
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    elif legacy_file.exists():
        try:
            data = json.loads(legacy_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    data["notebook_id"] = notebook_id
    data["notebook_title"] = title
    data["last_status_update"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")



def query_notebook(notebook_id: str, query: str) -> str:
    """Queries the given notebook with a specific question using `nlm notebook query`."""
    from bookforge.core.adapters.research import NotebookLMBackend
    backend = NotebookLMBackend(Path("."), notebook_id=notebook_id)
    return backend.query(query)


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
        # Typical text output: "Created notebook: Title (UUID: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)"
        output = res.stdout + "\n" + res.stderr
        match = re.search(
            r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
            output,
            re.IGNORECASE
        )
        if match:
            return match.group(1)
            
    except Exception:
        pass
    return None


def generate_research_outline(book_folder: Path) -> tuple[bool, str]:
    """Creates a unique notebook, uploads global research/rules, queries it for unique ideas, and generates a phase-0.md outline."""
    if not is_nlm_available():
        return False, "Error: nlm CLI not found in PATH."

    auth = get_auth_status()
    if not auth["authenticated"]:
        return False, f"Error: {auth['error']}"

    # 1. Ensure book_folder exists
    book_folder.mkdir(parents=True, exist_ok=True)

    # 2. Check if notebook is already linked
    nb = get_associated_notebook(book_folder)
    notebook_id = nb["id"] if nb else None
    
    if not notebook_id:
        # Generate new notebook title
        from bookforge.core import series as series_module
        series_info = series_module.get_series_info(book_folder)
        series_name = series_info["name"] if series_info else "western"
        nb_title = f"{series_name}-{book_folder.name}".lower().replace(" ", "-")
        
        notebook_id = create_new_notebook(nb_title)
        if not notebook_id:
            return False, "Error: Failed to create new NotebookLM notebook."
        set_associated_notebook(book_folder, notebook_id, nb_title)
    
    # 3. Identify and upload source files to build the research context
    files_to_upload: list[Path] = []
    
    # Check parent directory for research-pack.md
    parent_research = book_folder.parent / "research-pack.md"
    if parent_research.exists():
        files_to_upload.append(parent_research)
    
    # Check current directory research-pack.md
    local_research = book_folder / "research-pack.md"
    if local_research.exists():
        files_to_upload.append(local_research)

    # Check series-level or book-level rules/mood-lock to preserve continuity
    for parent in (book_folder.parent, book_folder):
        for name in ("rulebook.md", "mood-lock.md"):
            path = parent / name
            if path.exists():
                files_to_upload.append(path)

    # Check prior book's continuity/compiled drafts if carry-from or sequential
    state_file = book_folder / "state" / "notebooklm.json"
    loop_file = book_folder / "state" / "loop.json"
    legacy_file = book_folder / "loop-state.json"
    
    carry_from = None
    for sf in (state_file, loop_file, legacy_file):
        if sf.exists():
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
                carry_from = data.get("carry_from")
                if carry_from:
                    break
            except Exception:
                pass
                
    if carry_from:
        carry_path = Path(carry_from)
        if carry_path.exists():
            for name in ("rulebook.md", "mood-lock.md"):
                p = carry_path / name
                if p.exists():
                    files_to_upload.append(p)
            compiled = carry_path / f"{carry_path.name}-compiled.md"
            if compiled.exists():
                files_to_upload.append(compiled)


    # Unique files list (resolve absolute paths)
    unique_paths = []
    seen = set()
    for p in files_to_upload:
        abs_p = p.resolve()
        if abs_p not in seen:
            seen.add(abs_p)
            unique_paths.append(p)

    # Upload them using nlm source add
    uploaded_count = 0
    for filepath in unique_paths:
        try:
            res = subprocess.run(
                ["nlm", "source", "add", notebook_id, "--file", str(filepath), "--wait"],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode == 0:
                uploaded_count += 1
        except Exception:
            pass

    # 4. Conduct web research to discover and import authentic historical context
    try:
        from bookforge.core import series as series_module
        series_info = series_module.get_series_info(book_folder)
        series_name = series_info["name"] if series_info else "western"
        
        # Build research query matching period and series
        web_query = f"authentic late 1800s western historical events outlaws lawmen and frontier conflicts {series_name}"
        
        # Start research
        res_start = subprocess.run(
            ["nlm", "research", "start", web_query, "--notebook-id", notebook_id, "--quiet"],
            capture_output=True,
            text=True,
            check=False
        )
        if res_start.returncode == 0 and res_start.stdout.strip():
            task_id = res_start.stdout.strip()
            # Wait for completion (up to 120 seconds, polling via status)
            subprocess.run(
                ["nlm", "research", "status", notebook_id, "--task-id", task_id, "--max-wait", "120"],
                capture_output=True,
                text=True,
                check=False
            )
            # Import the found sources
            subprocess.run(
                ["nlm", "research", "import", notebook_id, task_id],
                capture_output=True,
                text=True,
                check=False
            )
    except Exception:
        pass

    # 5. Perform structured query to generate outline from all sources
    research_query = (
        "Identify 3-5 unique, authentic, period-accurate historical events, conflicts, settings, "
        "or character details present in the source documents. These details must feel grounded "
        "and typical of late 1800s Western history. Do not invent details not present in the sources. "
        "List them clearly."
    )
    research_response = query_notebook(notebook_id, research_query)
    
    # Load dynamic name policy if settings.json exists
    banned_names = ["Voss"]
    try:
        from bookforge.core.validator import load_project_settings
        settings = load_project_settings(book_folder)
        name_policy = settings.get("name_policy", {})
        config_banned = name_policy.get("banned_names", [])
        config_allowed = name_policy.get("allowed_names", [])

        active_banned = ["Voss"]
        allowed = {str(name).strip().lower() for name in config_allowed}

        for name in config_banned:
            name_str = str(name).strip()
            name_lower = name_str.lower()
            if name_str and name_lower not in allowed and name_lower not in [b.lower() for b in active_banned]:
                active_banned.append(name_str.capitalize())
        banned_names = active_banned
    except Exception:
        pass

    banned_names_list = []
    for b_name in banned_names:
        banned_names_list.append(f'- The name "{b_name}" (do not use "{b_name}" as a character name, location name, or family name)')
    banned_names_str = "\n".join(banned_names_list)

    # Construct the master prompt for outline generation
    generator_prompt = f"""
Based on the following historical details and context from the research sources:
---
{research_response}
---

Generate a fully original classic Western adventure outline.
Do not copy characters, names, scenes, dialogue, or recognizable story details from any copyrighted films.

The plot must be completely different from previous books and must strictly exclude:
- A syndicate (any institution whose power comes from controlling property, money, business, or politics)
- Water rights
- Mineral rights
- A trial scene
{banned_names_str}

Use new character names, original conflicts, and a differentiated setting. Make any travel or search sequences active and exciting by incorporating active scouting, environmental hazards, or significant discoveries.
The protagonist is Tex Cade. His gear/weapons: matched pair of Colt .45 Peacemakers, Bowie knife, Ranger star.

Structure the generated outline exactly in this markdown format:

# Book Outline: [Book Title]

## Overview
- Premise:
- Core Story Question:
- Themes:
- Tone and Style:
- Genre Promise:
- Expected Ending Direction:

## Continuity Position
[A detailed paragraph summarizing where this book begins in the series, what happened in the previous book, what consequences carry over, what names/elements return, and what unresolved conflicts or emotional burdens shape the opening of this story.]

## Character Profiles
- Tex Cade: Protagonist, matched pair of Colt .45 Peacemakers, Bowie knife, Ranger star. Laconic, carrying survivors' guilt, special attaché Ranger.
- [Key Character Name]: [Role in story, relationship to protagonist, motivation, conflict, and whether they are ally, enemy, or uncertain.]
- [Key Character Name]: [Description]

## World and Setting
- Primary Locations:
- Historical/Genre Details:
- Law and Order Situation:
- Main Threats:
- Travel, Terrain, and Survival Conditions:
- Weapons, Gear, and Important Objects:

## Main Conflict
[A detailed paragraph explaining the central threat of the book, who causes it, what the protagonist must stop or accomplish, what happens if they fail, and why the conflict matters personally.]

## Chapter Breakdown
Provide exactly 12 chapters in the following format:

### Chapter 1: [Chapter Title]
- The Plot & Action: [Detailed description of the plot and action of this chapter, including setting, character movement, danger, discoveries, reversals, and authentic genre details.]
- Character Work: [What this chapter reveals about the protagonist or another major character, including emotional pressure, moral choice, flaw, fear, loyalty, or growth.]
- Main Conflict: [The central conflict or obstacle driving this chapter.]
- Transition/Continuity: [How this chapter connects to the previous chapter and sets up the next one.]
- Hook/Cliffhanger: [The specific hook, reveal, danger, decision, or unanswered question that ends this chapter.]

### Chapter 2: [Chapter Title]
- The Plot & Action: [Detailed description]
- Character Work: [Details]
- Main Conflict: [Details]
- Transition/Continuity: [Details]
- Hook/Cliffhanger: [Hook/Cliffhanger]

... (Generate all 12 chapters using this exact formatting for each)

## Ending Direction
[A detailed paragraph describing how the final chapter should resolve the main conflict, what emotional or physical cost the protagonist pays, what changes in the world, and whether any thread remains open for the next book.]
"""


    outline_content = query_notebook(notebook_id, generator_prompt)
    if outline_content.startswith("Error") or "Query failed" in outline_content:
        return False, f"Failed to generate outline: {outline_content}"

    # Try to extract from json if returned as JSON
    clean_outline = outline_content
    try:
        data = json.loads(outline_content)
        if isinstance(data, dict) and "answer" in data:
            clean_outline = data["answer"]
    except json.JSONDecodeError:
        pass

    # 5. Write the generated outline to phase-0.md
    dest_outline = book_folder / "phase-0.md"
    dest_outline.write_text(clean_outline, encoding="utf-8")
    
    # Update loop state
    try:
        state_dir = book_folder / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "notebooklm.json"
        
        state_data = {}
        legacy_file = book_folder / "loop-state.json"
        
        if state_file.exists():
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
        elif legacy_file.exists():
            try:
                state_data = json.loads(legacy_file.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        state_data["notebook_id"] = notebook_id
        state_data["outline_generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        state_file.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
    except Exception:
        pass


    return True, f"Successfully created notebook, uploaded {uploaded_count} source files, and wrote outline to `{dest_outline.relative_to(book_folder.parent.parent)}`"
