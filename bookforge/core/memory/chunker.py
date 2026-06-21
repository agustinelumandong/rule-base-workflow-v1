"""Book file scanner and chunker for memory indexing."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def scan_and_chunk_book(book_folder: Path) -> list[tuple[str, dict[str, Any]]]:
    """Scan book files and partition them into metadata-tagged chunks."""
    chunks: list[tuple[str, dict[str, Any]]] = []

    # 1. Rulebook
    rulebook_path = book_folder / "rulebook.md"
    if rulebook_path.exists():
        text = rulebook_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": "rulebook.md",
                    "type": "rulebook",
                    "chunk_index": idx
                }))

    # 2. Mood Lock
    mood_lock_path = book_folder / "mood-lock.md"
    if mood_lock_path.exists():
        text = mood_lock_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": "mood-lock.md",
                    "type": "mood_lock",
                    "chunk_index": idx
                }))

    # 3. Phase Outlines
    from bookforge.core.scanner import source_path
    outline_path = source_path(book_folder)
    if outline_path and outline_path.exists():
        text = outline_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": outline_path.name,
                    "type": "outline",
                    "chunk_index": idx
                }))

    # 4. Chapter Summaries
    summaries_path = book_folder / "chapter-summaries.md"
    if summaries_path.exists():
        text = summaries_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": "chapter-summaries.md",
                    "type": "chapter_summaries",
                    "chunk_index": idx
                }))

    # 5. Canon Snapshot
    snapshot_path = book_folder / "canon" / "state" / "snapshot.yml"
    if snapshot_path.exists():
        import yaml
        try:
            snapshot_data = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))
            if isinstance(snapshot_data, dict):
                for char_id, char_info in snapshot_data.get("characters", {}).items():
                    info_str = (
                        f"Character '{char_id}' ({char_info.get('canonical', char_id)}): "
                        f"tier={char_info.get('tier')}, role={char_info.get('role')}, "
                        f"status={char_info.get('status')}, location={char_info.get('location')}, "
                        f"inventory={char_info.get('inventory')}, injuries={char_info.get('injuries')}, "
                        f"emotional_state={char_info.get('emotional_state')}."
                    )
                    chunks.append((info_str, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_character",
                        "entity_id": char_id
                    }))
                for loc_id, loc_info in snapshot_data.get("locations", {}).items():
                    info_str = (
                        f"Location '{loc_id}' ({loc_info.get('canonical', loc_id)}): "
                        f"occupants={loc_info.get('occupants')}."
                    )
                    chunks.append((info_str, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_location",
                        "entity_id": loc_id
                    }))
                for obj_id, obj_info in snapshot_data.get("objects", {}).items():
                    info_str = (
                        f"Object '{obj_id}' ({obj_info.get('canonical', obj_id)}): "
                        f"type={obj_info.get('type')}, holder={obj_info.get('holder')}, "
                        f"state={obj_info.get('state')}."
                    )
                    chunks.append((info_str, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_object",
                        "entity_id": obj_id
                    }))
        except (yaml.YAMLError, OSError, KeyError, AttributeError):
            text = snapshot_path.read_text(encoding="utf-8")
            for idx, paragraph in enumerate(text.split("\n\n")):
                para = paragraph.strip()
                if para:
                    chunks.append((para, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_snapshot_raw",
                        "chunk_index": idx
                    }))

    # 6. Chapter events
    events_dir = book_folder / "canon" / "events"
    if events_dir.is_dir():
        for event_file in sorted(events_dir.glob("*.event.yml")):
            text = event_file.read_text(encoding="utf-8")
            chunks.append((f"Event Log {event_file.name}:\n{text}", {
                "source": f"canon/events/{event_file.name}",
                "type": "canon_event",
                "chapter": event_file.stem
            }))

    # 7. Chapter drafts
    chapters_dir = book_folder / "chapters"
    if chapters_dir.is_dir():
        for draft_file in sorted(chapters_dir.glob("chapter-*/chapter-*.md")):
            text = draft_file.read_text(encoding="utf-8")
            chapter_slug = draft_file.parent.name
            for idx, paragraph in enumerate(text.split("\n\n")):
                para = paragraph.strip()
                if para:
                    chunks.append((para, {
                        "source": f"chapters/{chapter_slug}/{draft_file.name}",
                        "type": "chapter_draft",
                        "chapter": chapter_slug,
                        "chunk_index": idx
                    }))
        epilogue_file = chapters_dir / "epilogue" / "epilogue.md"
        if epilogue_file.exists():
            text = epilogue_file.read_text(encoding="utf-8")
            for idx, paragraph in enumerate(text.split("\n\n")):
                para = paragraph.strip()
                if para:
                    chunks.append((para, {
                        "source": "chapters/epilogue/epilogue.md",
                        "type": "epilogue_draft",
                        "chunk_index": idx
                    }))

    return chunks
