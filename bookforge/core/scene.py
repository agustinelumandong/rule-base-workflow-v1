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
        try:
            manifest = load_scene_manifest(m_path, book_folder)
            if manifest.target_words != target_words:
                manifest.target_words = target_words
                save_scene_manifest(manifest, m_path)
        except Exception:
            pass
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


SCENE_HEADING_RE = re.compile(r"(?im)^##\s+Scene\s+(\d+)\s*:?\s*(.*?)\s*$")
BEAT_HEADING_RE = re.compile(r"(?im)^###\s+BEAT\s*:?\s*(.*?)\s*$")
TARGET_WORDS_RE = re.compile(
    r"(?i)(?:target words?|estimated words?|elastic range)\D{0,40}(\d[\d,]*)"
)
PACING_ROW_RE = re.compile(r"^\|\s*(Chapter\s+\d+|Epilogue)\s*\|(.+?)\|$", re.IGNORECASE)
CHAPTER_TARGET_RE = re.compile(r"~?\s*(\d[\d,]*)\s+words?", re.IGNORECASE)

PACING_CLASS_TARGETS = {
    "lean": 900,
    "standard": 1600,
    "expanded": 2200,
    "major": 2900,
    "epilogue/teaser": 600,
}


@dataclass(frozen=True)
class BreakdownScene:
    scene_id: str
    title: str
    text: str
    required_beats: list[str]
    explicit_target_words: int | None = None


def _round_to_nearest_50(value: float) -> int:
    return max(50, int(round(value / 50.0) * 50))


def _parse_int(value: str) -> int:
    return int(value.replace(",", ""))


def parse_scene_breakdown_scenes(text: str) -> list[BreakdownScene]:
    """Parse top-level scene sections from a chapter scene-breakdown.md file."""
    headings = list(SCENE_HEADING_RE.finditer(text))
    scenes: list[BreakdownScene] = []
    for index, heading in enumerate(headings):
        number = int(heading.group(1))
        title = heading.group(2).strip() or f"Scene {number}"
        start = heading.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[start:end].strip()
        beats = [
            beat.group(1).strip()
            for beat in BEAT_HEADING_RE.finditer(section)
            if beat.group(1).strip()
        ]
        target_match = TARGET_WORDS_RE.search(section)
        scenes.append(
            BreakdownScene(
                scene_id=f"scene-{number:02d}",
                title=title,
                text=section,
                required_beats=beats,
                explicit_target_words=_parse_int(target_match.group(1)) if target_match else None,
            )
        )
    return scenes


def _chapter_pacing_targets(book_folder: Path) -> dict[str, tuple[int | None, str | None]]:
    path = book_folder / "chapter-pacing-plan.md"
    if not path.exists():
        return {}

    targets: dict[str, tuple[int | None, str | None]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PACING_ROW_RE.match(line.strip())
        if not match:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in {"chapter", "---"}:
            continue
        chapter_label = cells[0]
        pacing_class = cells[1].lower()
        range_text = cells[2]
        target_match = CHAPTER_TARGET_RE.search(range_text)
        target = _parse_int(target_match.group(1)) if target_match else None
        slug = "epilogue"
        chapter_match = re.search(r"chapter\s+(\d+)", chapter_label, re.IGNORECASE)
        if chapter_match:
            slug = f"chapter-{int(chapter_match.group(1)):02d}"
        targets[slug] = (target, pacing_class)
    return targets


def _chapter_target_words(book_folder: Path, chapter: str) -> int:
    target, pacing_class = _chapter_pacing_targets(book_folder).get(chapter, (None, None))
    if target:
        return target
    if pacing_class:
        return PACING_CLASS_TARGETS.get(pacing_class, 3500)
    return 3500


def estimate_scene_target_words(
    book_folder: Path,
    chapter: str,
    scenes: list[BreakdownScene],
) -> dict[str, int]:
    """Estimate scene targets from explicit scene values or chapter pacing guidance."""
    explicit_targets = {scene.scene_id: scene.explicit_target_words for scene in scenes if scene.explicit_target_words}
    if len(explicit_targets) == len(scenes):
        return {scene_id: int(target) for scene_id, target in explicit_targets.items()}

    chapter_target = _chapter_target_words(book_folder, chapter)
    remaining_scenes = [scene for scene in scenes if scene.scene_id not in explicit_targets]
    remaining_target = max(50 * len(remaining_scenes), chapter_target - sum(explicit_targets.values()))
    weights = [max(1, len(scene.required_beats)) for scene in remaining_scenes]
    total_weight = sum(weights) or len(remaining_scenes) or 1

    targets: dict[str, int] = {scene_id: int(target) for scene_id, target in explicit_targets.items()}
    running = 0
    for index, scene in enumerate(remaining_scenes):
        if index == len(remaining_scenes) - 1:
            target = max(50, remaining_target - running)
        else:
            target = _round_to_nearest_50(remaining_target * (weights[index] / total_weight))
            running += target
        targets[scene.scene_id] = target
    return targets


def bootstrap_scene_manifests_from_breakdowns(book_folder: Path) -> int:
    """Create scene manifests from chapter scene-breakdown.md files when absent."""
    created = 0
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        return created

    for chapter_dir in sorted(chapters_root.iterdir(), key=lambda p: p.name):
        if not chapter_dir.is_dir() or chapter_dir.name.startswith("."):
            continue
        breakdown_path = chapter_dir / "scene-breakdown.md"
        if not breakdown_path.exists():
            continue
        scenes = parse_scene_breakdown_scenes(breakdown_path.read_text(encoding="utf-8"))
        if not scenes:
            continue
        targets = estimate_scene_target_words(book_folder, chapter_dir.name, scenes)
        for scene in scenes:
            manifest_file = book_folder / "changes" / chapter_dir.name / "scenes" / scene.scene_id / "manifest.yml"
            if manifest_file.exists():
                continue
            manifest = SceneManifest(
                scene_id=scene.scene_id,
                chapter=chapter_dir.name,
                target_words=targets.get(scene.scene_id, 3500),
                status="draft",
                required_beats=scene.required_beats,
                forbidden=["modern slang"],
                inputs={},
                book_folder=book_folder,
            )
            manifest_file.parent.mkdir(parents=True, exist_ok=True)
            save_scene_manifest(manifest, manifest_file)
            created += 1
    return created


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
