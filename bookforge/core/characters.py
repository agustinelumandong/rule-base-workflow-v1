"""Character profile scaffolding for BookForge book folders."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^\s*[-*]\s+\*\*(.+?)(?::)?\*\*:?\s*(.+?)\s*$", re.MULTILINE)
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.DOTALL)


@dataclass(frozen=True)
class CharacterSeed:
    name: str
    role: str
    section: str
    source_body: str
    rulebook_body: str = ""

    @property
    def slug(self) -> str:
        return slugify(self.name)

    @property
    def category(self) -> str:
        section_l = self.section.lower()
        role_l = self.role.lower()
        if "main" in section_l or "protagonist" in role_l or "pov" in role_l:
            return "main"
        if any(term in role_l for term in ("antagonist", "rival", "villain", "war chief")):
            return "antagonist"
        if "antagonist" in section_l and "supporting" not in section_l:
            return "antagonist"
        return "supporting"

    @property
    def folder_name(self) -> str:
        if self.category == "antagonist":
            return "antagonists"
        if self.category == "main":
            return "main"
        return "supporting"

    @property
    def path_suffix(self) -> str:
        return f"{self.folder_name}/{self.slug}.md"


@dataclass(frozen=True)
class CharacterProfile:
    id: str
    canonical_name: str
    aliases: tuple[str, ...]
    category: str
    story_role: str
    pov_allowed: bool
    path: Path
    body: str

    @property
    def match_terms(self) -> tuple[str, ...]:
        terms = [self.id, self.id.replace("-", " "), self.path.stem, self.path.stem.replace("-", " ")]
        terms.append(self.canonical_name)
        first_name = self.canonical_name.split()[0] if self.canonical_name.split() else ""
        if len(first_name) >= 3:
            terms.append(first_name)
        terms.extend(self.aliases)
        normalized: list[str] = []
        seen: set[str] = set()
        for term in terms:
            cleaned = str(term).strip()
            if not cleaned or cleaned.lower() in seen:
                continue
            seen.add(cleaned.lower())
            normalized.append(cleaned)
        return tuple(normalized)


def slugify(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "character"


def _clean_heading(value: str) -> str:
    return re.sub(r"[*_`]+", "", value).strip(" -:\t")


def _split_name_role(title: str) -> tuple[str, str]:
    cleaned = _clean_heading(title)
    match = re.match(r"(.+?)\s*\((.+?)\)\s*$", cleaned)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return cleaned, ""


def _heading_blocks(text: str) -> list[tuple[int, str, int, int]]:
    headings = list(HEADING_RE.finditer(text))
    blocks: list[tuple[int, str, int, int]] = []
    for index, heading in enumerate(headings):
        level = len(heading.group(1))
        title = _clean_heading(heading.group(2))
        end = len(text)
        for next_heading in headings[index + 1 :]:
            if len(next_heading.group(1)) <= level:
                end = next_heading.start()
                break
        blocks.append((level, title, heading.end(), end))
    return blocks


def _fields(body: str) -> dict[str, str]:
    return {match.group(1).strip().lower(): match.group(2).strip() for match in FIELD_RE.finditer(body)}


def extract_character_seeds(source_text: str, rulebook_text: str = "") -> list[CharacterSeed]:
    """Extract character profile seeds from outline-style character sections."""
    source_blocks = _heading_blocks(source_text)
    rulebook_profiles = _rulebook_profiles(rulebook_text)
    seeds: list[CharacterSeed] = []

    for level, section_title, body_start, body_end in source_blocks:
        if level > 2 or not _is_character_section(section_title):
            continue
        section_body = source_text[body_start:body_end]
        for child_level, child_title, child_body_start, child_body_end in _heading_blocks(section_body):
            if child_level <= level:
                continue
            name, role = _split_name_role(child_title)
            body = section_body[child_body_start:child_body_end].strip()
            fields = _fields(body)
            role = role or fields.get("role", "")
            rulebook_body = _match_rulebook_body(name, rulebook_profiles)
            seeds.append(
                CharacterSeed(
                    name=name,
                    role=role or "Character",
                    section=section_title,
                    source_body=body,
                    rulebook_body=rulebook_body,
                )
            )

    return _dedupe_seeds(seeds)


def _is_character_section(title: str) -> bool:
    lowered = title.lower()
    return "character" in lowered or "cast" in lowered or "dramatis personae" in lowered


def _rulebook_profiles(rulebook_text: str) -> dict[str, str]:
    profiles: dict[str, str] = {}
    for level, section_title, body_start, body_end in _heading_blocks(rulebook_text):
        if level > 2 or not _is_character_section(section_title):
            continue
        section_body = rulebook_text[body_start:body_end]
        for child_level, child_title, child_body_start, child_body_end in _heading_blocks(section_body):
            if child_level <= level:
                continue
            name, _role = _split_name_role(child_title)
            profiles[name] = section_body[child_body_start:child_body_end].strip()
    return profiles


def _match_rulebook_body(name: str, profiles: dict[str, str]) -> str:
    target = slugify(name)
    for profile_name, body in profiles.items():
        if slugify(profile_name) == target:
            return body
    for profile_name, body in profiles.items():
        profile_slug = slugify(profile_name)
        if target in profile_slug or profile_slug in target:
            return body
    return ""


def _dedupe_seeds(seeds: list[CharacterSeed]) -> list[CharacterSeed]:
    seen: set[str] = set()
    deduped: list[CharacterSeed] = []
    for seed in seeds:
        if seed.slug in seen:
            continue
        seen.add(seed.slug)
        deduped.append(seed)
    return deduped


def scaffold_character_files(book_folder: Path) -> list[Path]:
    """Create writer-facing character files from existing outline/rulebook data."""
    source_path = _source_path(book_folder)
    if source_path is None:
        return []

    source_text = source_path.read_text(encoding="utf-8")
    rulebook_text = (book_folder / "rulebook.md").read_text(encoding="utf-8") if (book_folder / "rulebook.md").exists() else ""
    seeds = extract_character_seeds(source_text, rulebook_text)
    if not seeds:
        return []

    characters_dir = book_folder / "characters"
    created: list[Path] = []
    support_files = [
        "_schema.character.yml",
        "cast-index.md",
    ]
    if not any((characters_dir / "archetypes").glob("*.md")):
        support_files.append("archetypes/role-notes.md")

    for relative in support_files:
        path = characters_dir / relative
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_support_file_text(relative, seeds), encoding="utf-8")
        created.append(path)

    for seed in seeds:
        path = characters_dir / seed.path_suffix
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_character_profile(seed), encoding="utf-8")
        created.append(path)

    return created


def load_character_profiles(book_folder: Path) -> tuple[list[CharacterProfile], list[str]]:
    """Load writer-facing Markdown character profiles without touching canon state."""
    characters_dir = book_folder / "characters"
    if not characters_dir.exists():
        return [], []

    profiles: list[CharacterProfile] = []
    warnings: list[str] = []
    for folder_name in ("main", "supporting", "antagonists"):
        folder = characters_dir / folder_name
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            try:
                profiles.append(parse_character_profile(path, book_folder))
            except (OSError, UnicodeDecodeError, yaml.YAMLError, TypeError, ValueError) as exc:
                try:
                    display_path = path.relative_to(book_folder)
                except ValueError:
                    display_path = path
                warnings.append(f"WARNING: Could not parse character profile `{display_path}`: {exc}")
    return profiles, warnings


def parse_character_profile(path: Path, book_folder: Path | None = None) -> CharacterProfile:
    text = path.read_text(encoding="utf-8")
    metadata: dict = {}
    body = text
    match = FRONT_MATTER_RE.match(text)
    if match:
        raw_metadata, body = match.groups()
        parsed = yaml.safe_load(raw_metadata) if raw_metadata.strip() else {}
        if parsed is None:
            parsed = {}
        if not isinstance(parsed, dict):
            raise ValueError("front matter root must be a mapping")
        metadata = parsed

    category = str(metadata.get("category") or _category_from_profile_path(path))
    char_id = str(metadata.get("id") or slugify(path.stem))
    canonical_name = str(metadata.get("canonical_name") or _first_markdown_heading(body) or path.stem.replace("-", " ").title())
    aliases = metadata.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = [str(aliases)]
    story_role = str(metadata.get("story_role") or "")
    pov_data = metadata.get("pov") or {}
    pov_allowed = bool(pov_data.get("allowed")) if isinstance(pov_data, dict) else False

    return CharacterProfile(
        id=char_id,
        canonical_name=canonical_name,
        aliases=tuple(str(alias) for alias in aliases if str(alias).strip()),
        category=category,
        story_role=story_role,
        pov_allowed=pov_allowed,
        path=path.relative_to(book_folder) if book_folder else path,
        body=body.strip(),
    )


def _category_from_profile_path(path: Path) -> str:
    parent = path.parent.name
    if parent == "antagonists":
        return "antagonist"
    if parent == "main":
        return "main"
    return "supporting"


def _first_markdown_heading(text: str) -> str:
    match = HEADING_RE.search(text)
    return _clean_heading(match.group(2)) if match else ""


def _source_path(book_folder: Path) -> Path | None:
    for name in ("phase-0.md", "phase-00.md", "outline.md", "chapter-outline.md"):
        path = book_folder / name
        if path.exists():
            return path
    return None


def _support_file_text(relative: str, seeds: list[CharacterSeed]) -> str:
    if relative == "_schema.character.yml":
        return CHARACTER_SCHEMA
    if relative == "cast-index.md":
        return render_cast_index(seeds)
    return ARCHETYPE_NOTES


def render_cast_index(seeds: list[CharacterSeed]) -> str:
    lines = [
        "# Cast Index",
        "",
        "Detailed character files live here. Keep the source outline focused on story movement, keep `rulebook.md` focused on drafting constraints, and update these profiles when character facts change.",
        "",
        "## Profiles",
        "",
        "| Character | Category | Role | Profile |",
        "| --- | --- | --- | --- |",
    ]
    for seed in seeds:
        lines.append(f"| {seed.name} | {seed.category} | {seed.role} | `{seed.path_suffix}` |")
    lines.extend(
        [
            "",
            "## Update Rule",
            "",
            "Update the character profile first. Mirror only drafting-critical facts into `rulebook.md`: POV, physical marker, voice, motive, and hard locks.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_character_profile(seed: CharacterSeed) -> str:
    fields = _fields(seed.source_body)
    rulebook_fields = _fields(seed.rulebook_body)
    appearance = fields.get("appearance") or rulebook_fields.get("physical markers") or "Not specified in source."
    personality = fields.get("personality") or "Not specified in source."
    voice = fields.get("voice") or rulebook_fields.get("voice") or "Not specified in source."
    motive = rulebook_fields.get("private motive") or "Not specified in source."
    age = fields.get("age", "Not specified in source.")
    arc = fields.get("arc in book one") or fields.get("arc") or "Not specified in source."
    function = fields.get("key function") or fields.get("role") or seed.role
    pov_rule = rulebook_fields.get("pov rules", "None specified.")

    aliases = _aliases(seed.name)
    alias_block = "\n".join(f"  - {alias}" for alias in aliases) if aliases else "  []"
    return f"""---
id: {seed.slug}
canonical_name: {seed.name}
aliases:
{alias_block}
category: {seed.category}
story_role: {quote_yaml(seed.role)}
book_scope: book-1
first_appears: unknown
last_known_status: alive
pov:
  allowed: {str("strict third-person" in pov_rule.lower()).lower()}
  mode: {quote_yaml(pov_rule)}
  notes: {quote_yaml(pov_rule)}
age:
  notes: {quote_yaml(age)}
appearance:
  required_markers:
    - {quote_yaml(appearance)}
voice:
  summary: {quote_yaml(voice)}
personality:
  traits:
    - {quote_yaml(personality)}
motive:
  public: {quote_yaml(function)}
  private: {quote_yaml(motive)}
arc:
  start: Not specified in source.
  middle: Not specified in source.
  end: {quote_yaml(arc)}
locks:
  must_show: []
  must_not: []
source_refs:
  phase_0:
    - {quote_yaml(seed.section + " / " + seed.name)}
  rulebook:
    - {quote_yaml("Characters / " + seed.name)}
status: approved
---
# {seed.name}

## Writer Notes

- **Role:** {seed.role}
- **Function:** {function}

## Source Extract

From source outline:

{blockquote(seed.source_body)}
{rulebook_extract(seed.rulebook_body)}
"""


def _aliases(name: str) -> list[str]:
    match = re.search(r"\((.+?)\)", name)
    return [match.group(1).strip()] if match else []


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def blockquote(text: str) -> str:
    if not text.strip():
        return "> Not specified in source.\n"
    return "\n".join(f"> {line}" if line.strip() else ">" for line in text.strip().splitlines()) + "\n"


def rulebook_extract(text: str) -> str:
    if not text.strip():
        return ""
    return "\nFrom `rulebook.md`:\n\n" + blockquote(text)


CHARACTER_SCHEMA = """# Character profile schema.

required:
  - id
  - canonical_name
  - category
  - story_role
  - book_scope
  - first_appears
  - last_known_status
  - pov
  - appearance
  - voice
  - personality
  - motive
  - arc
  - locks
  - source_refs
  - status

categories:
  - main
  - supporting
  - antagonist
  - archetype

status_values:
  - draft
  - approved
  - superseded
"""


ARCHETYPE_NOTES = """# Character Archetype Notes

Use this file for reusable role guidance that is not a single person: mentor, rival, witness, trading-post owner, long hunter, scout, outlaw, or other story functions.

Keep these notes short. They should guide drafting without adding unauthorized canon.
"""
