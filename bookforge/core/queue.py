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
            old_status = scene.get("status")
            if status is not None:
                scene["status"] = status
            if provider is not None:
                scene["provider"] = provider
            if target_words is not None:
                scene["target_words"] = target_words
            if inc_generation:
                # Only increment if transitioning to generation_packet_ready
                if old_status != "generation_packet_ready":
                    scene["attempts"]["generation"] = scene["attempts"].get("generation", 0) + 1
            if inc_patch:
                # Only increment if transitioning to patch_packet_ready
                if old_status != "patch_packet_ready":
                    scene["attempts"]["patch"] = scene["attempts"].get("patch", 0) + 1
            found = True
            break
            
    if found:
        save_queue(book_folder, queue_data)
    return found


def verify_scene_runnable(book_folder: Path, scene_key: str, force: bool = False) -> bool:
    """
    Checks if a scene is allowed to be run/activated.
    If force is True, bypasses checks.
    Otherwise:
      1. Scene must exist in queue.
      2. All dependencies of the scene must be completed (clean, validation_passed, committed).
      3. There must not be another ACTIVE scene in the queue that is different.
         (i.e. another scene in an active/in-progress status).
    """
    if force:
        return True
        
    q_path = get_queue_path(book_folder)
    if not q_path.exists():
        build_queue(book_folder)
        
    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])
    if not scenes:
        return True
        
    status_map = {s["scene_key"]: s["status"] for s in scenes}
    completed_statuses = {"clean", "validation_passed", "committed"}
    
    # 1. Find the target scene in the queue
    target_scene = None
    for s in scenes:
        if s["scene_key"] == scene_key:
            target_scene = s
            break
            
    if not target_scene:
        # If scene not in queue, build/rebuild the queue
        build_queue(book_folder)
        queue_data = load_queue(book_folder)
        scenes = queue_data.get("scenes", [])
        status_map = {s["scene_key"]: s["status"] for s in scenes}
        for s in scenes:
            if s["scene_key"] == scene_key:
                target_scene = s
                break
        if not target_scene:
            return False
            
    # 2. Check dependencies of target scene
    for dep in target_scene.get("dependencies", []):
        dep_status = status_map.get(dep)
        if dep_status not in completed_statuses:
            return False
            
    # 3. Check single-active invariant:
    # There should not be any OTHER scene that is active (in-progress) in the queue.
    # An active scene is one that is not completed and not ready_for_generation (not started).
    for s in scenes:
        if s["scene_key"] == scene_key:
            continue
        status = s["status"]
        if status not in completed_statuses and status != "ready_for_generation":
            # Another scene is active/in-progress!
            return False
            
    return True



def get_next_runnable_scene(book_folder: Path) -> dict | None:
    """Finds the first scene in the queue that is not completed and whose dependencies are all completed."""
    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])
    
    # Create a map of scene_key -> status for quick lookup
    status_map = {s["scene_key"]: s["status"] for s in scenes}
    
    for scene in scenes:
        status = scene.get("status")
        # Completed statuses
        if status in ("validation_passed", "committed", "clean"):
            continue
            
        # Check dependencies
        deps = scene.get("dependencies", [])
        blocked = False
        for dep in deps:
            dep_status = status_map.get(dep)
            if dep_status not in ("validation_passed", "committed", "clean"):
                blocked = True
                break
                
        if not blocked:
            return scene
            
    return None


def get_next_command(scene: dict) -> tuple[str, str]:
    """Returns a description and the next command to run for a given scene based on its status."""
    status = scene.get("status")
    scene_key = scene["scene_key"]
    parts = scene_key.split("/")
    chapter = parts[0]
    scene_id = parts[1]
    
    if status == "ready_for_generation":
        desc = "Generate the initial prompt/context packet for the provider web."
        cmd = f"bf packet --chapter {chapter} --scene {scene_id} --task draft-prose"
    elif status == "generation_packet_ready":
        desc = "Prose has been prepared. Paste packet into provider web, save draft to changes/{chapter}/scenes/{scene_id}/draft.md, then run validate."
        cmd = f"bf validate --chapter {chapter} --scene {scene_id}"
    elif status == "ready_for_validation":
        desc = "Validate the newly written/modified scene draft."
        cmd = f"bf validate --chapter {chapter} --scene {scene_id}"
    elif status == "validation_failed":
        desc = "The draft failed validation rules. Generate a patch repair packet."
        cmd = f"bf patch --chapter {chapter} --scene {scene_id}"
    elif status == "patch_packet_ready":
        desc = "Patch packet is ready. Paste it into the provider web, save replacement to changes/{chapter}/scenes/{scene_id}/replacement.md, and apply the patch."
        cmd = f"bf patch apply --chapter {chapter} --scene {scene_id} --from-file changes/{chapter}/scenes/{scene_id}/replacement.md"
    elif status in ("validation_passed", "clean"):
        desc = "Scene validation passed! Commit the scene changes to canon."
        cmd = f"bf apply change <book_folder> {chapter}"
    else:
        desc = f"Unknown scene status: {status}"
        cmd = "# No recommendation available."
        
    return desc, cmd

