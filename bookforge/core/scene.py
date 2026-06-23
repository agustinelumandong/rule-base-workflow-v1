"""Core scene manifests module for BookForge."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from bookforge.core.canon.io import load_yaml_file, save_yaml_file


@dataclass
class SceneManifest:
    scene_id: str
    chapter: str
    target_words: int
    status: str
    required_beats: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    research_questions: list[str] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)
    book_folder: Path = field(default_factory=Path)

    @property
    def scene_folder(self) -> Path:
        from bookforge.core.packet.helpers import scene_folder
        return scene_folder(self.book_folder, self.chapter, self.scene_id)

    @property
    def packet_path(self) -> Path:
        return self.scene_folder / "generation-packet.md"

    @property
    def draft_path(self) -> Path:
        return self.scene_folder / "draft.md"

    @property
    def validation_path(self) -> Path:
        return self.scene_folder / "validation.json"

    @property
    def patch_packet_path(self) -> Path:
        return self.scene_folder / "patch-packet.md"

    @property
    def replacement_path(self) -> Path:
        return self.scene_folder / "replacement.md"

    @property
    def guard_log_path(self) -> Path:
        return self.scene_folder / "guard-log.jsonl"


def manifest_path(chapter_folder: Path, scene_id: str) -> Path:
    """Returns the path to the manifest file for a given scene."""
    return chapter_folder / "scenes" / scene_id / "manifest.yml"


def init_scene_manifest(book_folder: Path, chapter: str, scene_id: str, target_words: int = 3500) -> Path:
    """Initializes a new scene manifest and folder layout under changes/."""
    scene_dir = book_folder / "changes" / chapter / "scenes" / scene_id
    scene_dir.mkdir(parents=True, exist_ok=True)

    m_path = scene_dir / "manifest.yml"
    if m_path.exists():
        return m_path

    # Attempt to load from template
    template_path = Path(__file__).parent.parent / "templates" / "scene-manifest.yml"
    if template_path.exists():
        try:
            content = template_path.read_text(encoding="utf-8")
            # Replace placeholders
            content = content.replace("scene_id: scene-01", f"scene_id: {scene_id}")
            content = content.replace("chapter: chapter-01", f"chapter: {chapter}")
            content = content.replace("target_words: 3500", f"target_words: {target_words}")
            m_path.write_text(content, encoding="utf-8")
            return m_path
        except OSError:
            pass

    # Fallback default dict
    fallback_data = {
        "scene_id": scene_id,
        "chapter": chapter,
        "target_words": target_words,
        "status": "draft",
        "required_beats": [
            "Beat 1: Describe the initial setup or tension.",
            "Beat 2: Introduce the main interaction or conflict.",
            "Beat 3: End with a solid link/cliffhanger to the next scene."
        ],
        "forbidden": ["modern slang"],
        "research_questions": [],
        "inputs": {
            "characters": [],
            "locations": []
        }
    }
    save_yaml_file(m_path, fallback_data)
    return m_path


def load_scene_manifest(path: Path, book_folder: Path = Path()) -> SceneManifest:
    """Loads a scene manifest from a YAML file."""
    data = load_yaml_file(path)
    return SceneManifest(
        scene_id=data.get("scene_id", path.parent.name),
        chapter=data.get("chapter", path.parent.parent.parent.name),
        target_words=data.get("target_words", 3500),
        status=data.get("status", "draft"),
        required_beats=data.get("required_beats", []),
        forbidden=data.get("forbidden", []),
        research_questions=data.get("research_questions", []),
        inputs=data.get("inputs", {}),
        book_folder=book_folder
    )


def save_scene_manifest(manifest: SceneManifest, path: Path | None = None) -> None:
    """Saves a scene manifest back to a YAML file."""
    if path is None:
        path = manifest.scene_folder / "manifest.yml"
    data = {
        "scene_id": manifest.scene_id,
        "chapter": manifest.chapter,
        "target_words": manifest.target_words,
        "status": manifest.status,
        "required_beats": manifest.required_beats,
        "forbidden": manifest.forbidden,
        "research_questions": manifest.research_questions,
        "inputs": manifest.inputs
    }
    save_yaml_file(path, data)


def parse_scene_id(slug: str) -> tuple[str, str]:
    """Parse scene identifiers.
    
    Examples:
      - 'chapter-08/scene-02' -> ('chapter-08', 'scene-02')
      - 'ch08_sc02'           -> ('chapter-08', 'scene-02')
      - 'scene-02'            -> ('', 'scene-02')
    """
    slug = slug.strip()

    # 1. Slash separation
    if "/" in slug:
        parts = slug.split("/", 1)
        ch = parts[0].strip()
        sc = parts[1].strip()
        if ch.startswith("ch") and not ch.startswith("chapter-"):
            num_match = re.search(r"\d+", ch)
            if num_match:
                ch = f"chapter-{int(num_match.group(0)):02d}"
        return ch, sc

    # 2. Combined patterns like ch08_sc02, ch-08-sc-02, chapter-08_scene-02
    match = re.search(r"(?:chapter|ch)[-_]?(\d+)[_-]?(?:scene|sc)[-_]?(\d+)", slug, re.IGNORECASE)
    if match:
        return f"chapter-{int(match.group(1)):02d}", f"scene-{int(match.group(2)):02d}"

    # 3. Bare scene slug
    return "", slug


def discover_scenes(chapter_folder: Path, book_folder: Path = Path()) -> list[SceneManifest]:
    """Finds and loads all scene manifests under the chapter's scenes/ subdirectories."""
    scenes_dir = chapter_folder / "scenes"
    if not scenes_dir.exists():
        return []

    manifests = []
    for path in scenes_dir.glob("*/manifest.yml"):
        try:
            manifests.append(load_scene_manifest(path, book_folder))
        except Exception:
            pass

    def scene_sort_key(m: SceneManifest) -> tuple[int, str]:
        num_match = re.search(r"\d+", m.scene_id)
        if num_match:
            return (int(num_match.group(0)), m.scene_id)
        return (999, m.scene_id)

    return sorted(manifests, key=scene_sort_key)
