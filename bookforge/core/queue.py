"""Core queue module for BookForge."""

from __future__ import annotations

import re
from pathlib import Path
from bookforge.core.canon.io import load_yaml_file, save_yaml_file
from bookforge.core.validators.format import discover_chapters, chapter_sort_key
from bookforge.core.scene import discover_scenes, manifest_path, load_scene_manifest, parse_scene_id

def get_queue_path(book_folder: Path) -> Path:
    """Returns the path to the queue file for a given book."""
    return book_folder / "queue.yml"

def build_queue(book_folder: Path) -> Path:
    """Discovers all chapters and scenes in the book and compiles the queue."""
    # Load existing queue if it exists to preserve status, attempts, etc.
    existing_queue = load_queue(book_folder)
    existing_scenes = {s["scene_key"]: s for s in existing_queue.get("scenes", [])}

    # Discover all chapters
    chapters = discover_chapters(book_folder)
    
    # We will accumulate all scene info in sequential order
    scene_list = []
    
    for chapter in chapters:
        # 1. Look for existing scene manifests in changes and chapters folders
        scenes = discover_scenes(chapter.folder, book_folder)
        
        # 2. Fallback: parse scene-breakdown.md if no manifests exist
        if not scenes and chapter.scene_breakdown.exists():
            try:
                content = chapter.scene_breakdown.read_text(encoding="utf-8")
                # Parse headers like "## Scene 1" or "### Scene 02"
                for line in content.splitlines():
                    if line.startswith("## ") or line.startswith("### "):
                        title = line.lstrip("#").strip()
                        # Extract a scene id
                        match = re.search(r"(?i)scene\s*[:\-]?\s*(\d+|\w+)", title)
                        if match:
                            num_str = match.group(1).zfill(2)
                            sc_id = f"scene-{num_str}"
                            # Create a dummy scene object or dict representation
                            from dataclasses import dataclass
                            @dataclass
                            class DummyScene:
                                scene_id: str
                                chapter: str
                                target_words: int
                                status: str
                            scenes.append(DummyScene(scene_id=sc_id, chapter=chapter.slug, target_words=3500, status="draft"))
            except Exception:
                pass
        
        # Ensure scenes are sorted numerically within the chapter
        scenes = sorted(scenes, key=lambda s: s.scene_id)
        
        for scene in scenes:
            scene_key = f"{chapter.slug}/{scene.scene_id}"
            
            # Paths relative to book folder
            scene_dir_rel = f"changes/{chapter.slug}/scenes/{scene.scene_id}"
            if not (book_folder / scene_dir_rel).exists() and (book_folder / f"chapters/{chapter.slug}/scenes/{scene.scene_id}").exists():
                scene_dir_rel = f"chapters/{chapter.slug}/scenes/{scene.scene_id}"

            # Default attributes
            target_words = getattr(scene, "target_words", 3500)
            status = "ready_for_generation"
            provider = "manual-web"
            attempts = {"generation": 0, "patch": 0}
            dependencies = []

            # If it already existed in the queue, preserve its state
            if scene_key in existing_scenes:
                existing = existing_scenes[scene_key]
                status = existing.get("status", status)
                provider = existing.get("provider", provider)
                attempts = existing.get("attempts", attempts)
                dependencies = existing.get("dependencies", dependencies)
                target_words = existing.get("target_words", target_words)
            else:
                # Check manifest.yml if it exists on disk
                m_path = manifest_path(book_folder / "changes" / chapter.slug, scene.scene_id)
                if not m_path.exists():
                    m_path = manifest_path(book_folder / "chapters" / chapter.slug, scene.scene_id)
                if m_path.exists():
                    try:
                        manifest = load_scene_manifest(m_path, book_folder)
                        target_words = manifest.target_words
                        if manifest.status == "clean":
                            status = "validation_passed"
                    except Exception:
                        pass
                
                # Check validation.json if it exists on disk to update status
                val_json = book_folder / scene_dir_rel / "validation.json"
                if val_json.exists():
                    try:
                        import json
                        val_data = json.loads(val_json.read_text(encoding="utf-8"))
                        status = "validation_passed" if val_data.get("status") == "clean" else "validation_failed"
                    except Exception:
                        pass
                
                # Check if draft exists to mark as ready_for_validation
                draft_file = book_folder / scene_dir_rel / "draft.md"
                if draft_file.exists() and status == "ready_for_generation":
                    status = "ready_for_validation"

            scene_entry = {
                "scene_key": scene_key,
                "status": status,
                "provider": provider,
                "target_words": target_words,
                "packet_path": f"{scene_dir_rel}/generation-packet.md",
                "draft_path": f"{scene_dir_rel}/draft.md",
                "validation_path": f"{scene_dir_rel}/validation.json",
                "patch_packet_path": f"{scene_dir_rel}/patch-packet.md",
                "attempts": attempts,
                "dependencies": dependencies,
            }
            scene_list.append(scene_entry)

    # Re-link dependencies sequentially
    for idx, scene_entry in enumerate(scene_list):
        if idx > 0:
            scene_entry["dependencies"] = [scene_list[idx - 1]["scene_key"]]
        else:
            scene_entry["dependencies"] = []

    queue_data = {
        "book": book_folder.name,
        "scenes": scene_list
    }
    
    q_path = get_queue_path(book_folder)
    save_yaml_file(q_path, queue_data)
    return q_path

def load_queue(book_folder: Path) -> dict:
    """Loads the queue configuration for the book."""
    q_path = get_queue_path(book_folder)
    if not q_path.exists():
        return {"book": book_folder.name, "scenes": []}
    return load_yaml_file(q_path)

def save_queue(book_folder: Path, queue_data: dict) -> None:
    """Saves the queue configuration for the book."""
    q_path = get_queue_path(book_folder)
    save_yaml_file(q_path, queue_data)

def update_queue_scene(
    book_folder: Path,
    scene_key: str,
    status: str | None = None,
    provider: str | None = None,
    inc_generation: bool = False,
    inc_patch: bool = False,
    target_words: int | None = None,
) -> bool:
    """Updates specific fields of a scene in the queue."""
    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])
    
    found = False
    for scene in scenes:
        if scene["scene_key"] == scene_key:
            if status is not None:
                scene["status"] = status
            if provider is not None:
                scene["provider"] = provider
            if target_words is not None:
                scene["target_words"] = target_words
            if inc_generation:
                scene["attempts"]["generation"] = scene["attempts"].get("generation", 0) + 1
            if inc_patch:
                scene["attempts"]["patch"] = scene["attempts"].get("patch", 0) + 1
            found = True
            break
            
    if found:
        save_queue(book_folder, queue_data)
    return found
