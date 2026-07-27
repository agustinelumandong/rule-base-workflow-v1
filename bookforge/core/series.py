#!/usr/bin/env python3
"""BookForge Multi-Book Series Core Module."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from bookforge import config
from bookforge.core import validator as context_validator


SERIES_AGENTS_TEMPLATE = """# BookForge Series Workflow

**Persona:** You are a manuscript operator and writer. Execute the book pipeline from approved outline through final draft without inventing plot, characters, or setting facts beyond the approved source. Work systematically and do not skip phases.

## Source of Truth

Approved canon paths: `series-bible.md`, `settings.json`, and each book's `phase-0.md` and `rulebook.md`.
Research is approved reference material, not canon. Use `series-research-pack.md` for shared period research and `books/<book-slug>/research-pack.md` for book-specific research; record a historical fact before relying on it in planning or prose.
AI canon suggestions belong in `proposed/`. Drafts and compiled manuscripts are editable output, not canon by themselves.
If sources conflict, keep approved canon unchanged and ask the user or place a proposed change in `proposed/`.

## Central Skills

Use the centrally installed `manuscript-workflow-orchestrator` skill for book planning, context checks, and drafting workflow when it is available.
Use `western-manuscript-style` for prose and continuity passes; use `humanizer` only after source, continuity, and style checks.
Do not copy or modify central skills inside this series folder. If a named skill is unavailable, follow the required order below without inventing a replacement workflow.

## End-to-End Workflow

### Phase 1: Outline Review

Before any artifact generation, verify `phase-0.md` contains:

1. **Setting Function** — at least 3 specific terrain/resource elements that force decisions.
2. **Story Pattern + Chapter Function Rule** — a named structural pattern and a repeating chapter function rule.
3. **Hard Story Guardrails** — embedded restrictions appropriate to the book.
4. **Every new character** — physical marker, voice note, private motive or secret.
5. **No vague chapter summaries** — each names a specific action, revelation, or change.
6. **Split POV** — if used, convergence point named.
7. **Ending State for Book N+1** — character states, unresolved obligations, world changes, and a hook.
8. **Name check** — new character names checked against `settings.json` banned names.

### Phase 2: Source Scan

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_source_format.py books/<book-slug>
```

Read `source-format-scan.md` to identify present/missing bible sections, chapter-list detail, and length target source.

### Phase 3: Planning Artifacts

Generate or refresh:

1. **rulebook.md** — source hierarchy, length handling rules, do-not-invent inventory, returning character profiles (with carryover injuries/relationships), new character profiles (physical marker + voice note + private motive), world and setting pressure, continuity facts, series arc, current book locks, plot-mechanics guardrails, chapter continuity ledger, ending state, and unknowns.
2. **mood-lock.md** — genre and atmosphere, historical/time-period assumptions, prose style constraints, vocabulary direction, dialogue direction, violence/action direction, and what the manuscript must avoid.
3. **chapter-summaries.md** — for each chapter (and epilogue): chapter number and title, chapter function, one-paragraph summary, main plot movement, emotional/thematic turn, continuity notes, and setup/payoff notes.

### Phase 4: Chapter Breakdowns

For each chapter, create `chapters/chapter-XX/scene-breakdown.md` with scene number, POV, location, purpose, pacing class, opening pressure, conflict, required facts, emotional/thematic beat, and exit hook.

Then create `chapters/chapter-XX/beats.md` using the full beat structure:

```md
## BEAT [N]: [Title] (pacing class)

### Source Context Lock
- Source Anchor, Continuity In, Required Story Movement, Continuity Out, Do Not Invent

### Pacing Guidance
- Pacing Class, Elastic Range, Why This Beat Is Short/Long, Expansion Permission

### Western Series Strength
- Hero Cost, Villain Presence, Supporting Agency, Quiet Humanizing Beat, Legacy Pressure Payoff, Proof/Consequence Payoff, Evidence/Frame-Up Logic

### Beat Instructions
- Opener, Action, Conflict, Emotional/Thematic Beat, Chapter Function, Rule Check

### Context Match Check
- Matches source, no skipped movement, no unsupported additions, prior continuity preserved, sets up next beat, no banned plot elements, name locks preserved
```

### Phase 5: Drafting

1. Load `western-manuscript-style` before drafting.
2. Use the book's approved style lock: literal prose; no metaphors, similes, or personification; blue-collar period vocabulary; no AI echo words or modern/clinical language; no Texas slang unless requested; no `-ing` sentence openers; avoid repeated Name/Pronoun loops; mix sentence lengths; no internal monologue; and show through action, posture, silence, and choices.
3. Keep dialogue short and direct. Use em-dash action anchors only when the active book's style lock calls for them.
4. Draft one scene at a time to `chapters/chapter-XX/draft.md`.
5. Do not use fixed numeric scene lengths. Track relevant injuries, possessions, animals, weapons, and knowledge as required by the approved material.
6. Use prose, not backticks or code blocks, for in-story notes, letters, telegrams, and written messages.
7. Keep each scene to its requested POV. Do not hardcode a series-wide character or book-specific POV into this guide.
8. Use the research pack for historical or period-sensitive details.

### Phase 6: Continuity Tracking

After each chapter draft, update `chapters/chapter-XX/continuity-out.md` with:

```md
# Continuity Out: chapter-XX

## Characters
[Who is alive, injured, present, or absent. Include current physical condition.]

## Locations
[Where key characters end this chapter.]

## Changes
[What changed: possessions transferred, injuries gained, secrets revealed, alliances shifted. Include resource changes.]

## Human Stakes Carried
[Character: direct pressure/cost + requirement for next chapter.]

## Unresolved Pressure
[What tension, obligation, or threat carries forward.]

## Next Chapter Must Know
[Specific facts the next chapter must not contradict.]
```

### Phase 7: Validation

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>
```

Fix hard FAILs before proceeding. Treat WARN results as review or expansion targets.

Length check:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>
```

### Phase 8: Expansion and Polish

- If word count is below target, expand from approved scene-breakdown beats and source material only. Never pad.
- Use `western-manuscript-style` for style/continuity passes.
- Use `humanizer` only after source, continuity, and style checks pass. Preserve plot, continuity, POV, and tone.

## Required Order

1. Read series canon and the current book's `phase-0.md`, `rulebook.md`, `mood-lock.md`, and `chapter-summaries.md` before writing.
2. Plan the chapter with a scene breakdown before drafting prose.
3. Save AI prose only as an editable chapter draft.
4. Check continuity, source support, names, setting, time, and style before treating a draft as ready.
5. Keep the continuity record current after an approved chapter change.

## Canon Safety

Never overwrite `series-bible.md`, `settings.json`, `phase-0.md`, or `rulebook.md` with AI-generated facts unless the user explicitly approves the change.
Do not patch a compiled manuscript as a substitute for correcting its source draft or planning artifact.

## Commands

- Create a book: `bookforge book-init <book-slug>`
- Inspect a book: `bookforge status books/<book-slug>`
- Check the next workflow action: `bookforge run-loop books/<book-slug>` (read-only)
- Prepare a selected chapter's safe context packet: `bookforge run-loop books/<book-slug> --prepare`
- Record an actual human or external repair attempt: `bookforge run-loop books/<book-slug> --record-repair chapter-01`
- Compile drafts: `bookforge compile books/<book-slug>`
- Run source scan: `python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_source_format.py books/<book-slug>`
- Run context validation: `python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>`
- Run length check: `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>`
"""


def is_series_workspace(series_folder: Path) -> bool:
    """Return whether a folder has BookForge series ownership."""
    return (series_folder / "series.json").is_file()


def initialize_series_workspace(series_folder: Path) -> list[str]:
    """Create the minimal files required for a BookForge series workspace."""
    if is_series_workspace(series_folder):
        return [f"Series workspace already initialized: {series_folder}"]

    if series_folder.exists() and any(series_folder.iterdir()):
        raise FileExistsError(f"Refusing to initialize nonempty folder: {series_folder}")

    series_folder.mkdir(parents=True, exist_ok=True)
    (series_folder / "series.json").write_text(
        json.dumps({"name": series_folder.name.replace("-", " ").title(), "books": []}),
        encoding="utf-8",
    )
    (series_folder / "series-bible.md").write_text("# Series Bible\n", encoding="utf-8")
    (series_folder / "series-research-pack.md").write_text("# Series Research Pack\n", encoding="utf-8")
    (series_folder / "settings.json").write_text("{}\n", encoding="utf-8")
    (series_folder / "AGENTS.md").write_text(SERIES_AGENTS_TEMPLATE, encoding="utf-8")
    (series_folder / "books").mkdir()
    (series_folder / "proposed").mkdir()
    return [f"Created series workspace: {series_folder}"]


def initialize_book_in_series(series_folder: Path, book_slug: str) -> list[str]:
    """Create a blank book scaffold in an initialized series workspace."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", book_slug):
        raise ValueError(f"Invalid book slug: {book_slug}")
    if not is_series_workspace(series_folder):
        raise FileNotFoundError(f"Series workspace not found: {series_folder}")

    series_json_path = series_folder / "series.json"
    series_data = json.loads(series_json_path.read_text(encoding="utf-8"))
    if not isinstance(series_data, dict):
        raise ValueError(f"Invalid series data: {series_json_path}")
    books = series_data.setdefault("books", [])
    if not isinstance(books, list):
        raise ValueError(f"Invalid books list: {series_json_path}")

    book_folder = series_folder / "books" / book_slug
    if book_folder.exists() and any(book_folder.iterdir()):
        raise FileExistsError(f"Refusing to initialize nonempty book folder: {book_folder}")

    book_folder.mkdir(parents=True, exist_ok=True)
    for name in ("phase-0.md", "rulebook.md", "mood-lock.md", "chapter-summaries.md"):
        shutil.copyfile(config.BUNDLED_TEMPLATES_DIR / name, book_folder / name)
    (book_folder / "chapters").mkdir()

    books.append(book_slug)
    series_json_path.write_text(json.dumps(series_data), encoding="utf-8")
    return [f"Created book scaffold: {book_folder}"]


def get_series_info(book_folder: Path) -> dict[str, str] | None:
    """Determines if a book folder belongs to a series.
    
    Returns a dictionary with 'name' and 'path' if nested under a series folder.
    """
    parent = book_folder.resolve().parent
    # Check if parent resides in a directory named 'books'
    if parent.name and parent.parent.name == "books":
        series_json_path = parent / "series.json"
        series_name = parent.name.replace("-", " ").title()
        if series_json_path.exists():
            try:
                data = json.loads(series_json_path.read_text(encoding="utf-8"))
                if "name" in data:
                    series_name = data["name"]
            except Exception:
                pass
        return {
            "name": series_name,
            "path": str(parent)
        }
    return None


def parse_continuity_sections(text: str) -> dict[str, str]:
    """Parse sections from a continuity-out.md text."""
    sections = {}
    headers = ["Characters", "Locations", "Changes", "Unresolved Pressure", "Next Chapter Must Know"]
    
    for header in headers:
        # Search for header at start of line
        pattern = rf"(?im)^##\s+{re.escape(header)}\s*$"
        match = re.search(pattern, text)
        if not match:
            continue
        
        start_idx = match.end()
        # Find start of next header to bound content
        next_start = len(text)
        for next_header in headers:
            next_match = re.search(rf"(?im)^##\s+{re.escape(next_header)}\s*$", text[start_idx:])
            if next_match:
                next_start = min(next_start, start_idx + next_match.start())
        
        content = text[start_idx:next_start].strip()
        # Filter out comments/placeholders like [Who is alive...]
        lines = []
        for line in content.splitlines():
            line_strip = line.strip()
            if not (line_strip.startswith("[") and line_strip.endswith("]")):
                lines.append(line)
        sections[header] = "\n".join(lines).strip()
        
    return sections


def carry_forward_book_continuity(from_book: Path, to_book: Path) -> str:
    """Carries forward continuity-out from the last chapter of from_book into to_book's rulebook."""
    if not from_book.exists():
        raise FileNotFoundError(f"Source book folder not found: {from_book}")
    if not to_book.exists():
        raise FileNotFoundError(f"Target book folder not found: {to_book}")

    # Discover chapters in source book to find the last one
    chapters = context_validator.discover_chapters(from_book)
    if not chapters:
        return "No chapters found in source book; no continuity to carry forward."

    # Sort chapters to identify the final one
    # Note: epilogue is appended/sorted last by validate check, let's locate the last draft chapter
    draft_chapters = [chap for chap in chapters if chap.draft.exists()]
    if not draft_chapters:
        return "No drafted chapters found in source book; no continuity to carry forward."

    # Identify last chapter by sort key
    last_chap = max(draft_chapters, key=lambda c: context_validator.chapter_sort_key(c.folder))
    continuity_path = last_chap.folder / "continuity-out.md"
    if not continuity_path.exists():
        return f"Continuity file missing in last chapter: {last_chap.slug}/continuity-out.md"

    try:
        content = continuity_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Failed to read continuity file: {e}"

    sections = parse_continuity_sections(content)
    
    char_state = sections.get("Characters", "No carry-over character state recorded.")
    loc_state = sections.get("Locations", "No carry-over location state recorded.")
    unresolved_state = sections.get("Unresolved Pressure", "No carry-over unresolved setups recorded.")
    changes_state = sections.get("Changes", "No carry-over chronology changes recorded.")

    carry_over_block = f"""

## Series Carry-Over Continuity (from {from_book.name})

### Characters Handoff State
{char_state}

### Locations Handoff State
{loc_state}

### Unresolved Story Pressures & Setup
{unresolved_state}

### Major Changes & Chronology
{changes_state}
"""

    rulebook_path = to_book / "rulebook.md"
    try:
        if rulebook_path.exists():
            existing_text = rulebook_path.read_text(encoding="utf-8")
            # Don't append if already carried forward once
            if f"Series Carry-Over Continuity (from {from_book.name})" not in existing_text:
                rulebook_path.write_text(existing_text + carry_over_block, encoding="utf-8")
        else:
            rulebook_path.write_text(f"# Rulebook\n" + carry_over_block, encoding="utf-8")
    except Exception as e:
        return f"Failed to update target rulebook: {e}"

    return f"Successfully carried forward continuity from {from_book.name} ({last_chap.slug}) into {to_book.name} rulebook."


def copy_shared_series_resources(to_book: Path) -> list[str]:
    """Copies any shared series files (series-bible.md, series-research-pack.md) from parent to book folder."""
    series_info = get_series_info(to_book)
    if not series_info:
        return []

    parent_path = Path(series_info["path"])
    copied = []

    # Copy series bible to rulebook if rulebook doesn't exist yet
    series_bible = parent_path / "series-bible.md"
    rulebook = to_book / "rulebook.md"
    if series_bible.exists() and not rulebook.exists():
        try:
            shutil.copy2(series_bible, rulebook)
            copied.append(f"Initialized rulebook.md from series-bible.md")
        except Exception:
            pass

    # Copy series research pack to research-pack.md
    series_research = parent_path / "series-research-pack.md"
    research_pack = to_book / "research-pack.md"
    if series_research.exists() and not research_pack.exists():
        try:
            shutil.copy2(series_research, research_pack)
            copied.append(f"Initialized research-pack.md from series-research-pack.md")
        except Exception:
            pass

    return copied
