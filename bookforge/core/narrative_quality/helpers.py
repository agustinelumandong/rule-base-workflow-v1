"""Parsing and validation helpers for narrative quality checks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from bookforge.core import validator
from bookforge.core.issue import IssueCategory, ManuscriptIssue, Severity, compute_fingerprint
from bookforge.core.narrative_quality.constants import (
    NARRATIVE_RULE_META,
    TITLE_WORDS,
    GENERIC_CHARACTER_HEADINGS,
    EXPECTED_RECURRING_FIRST_NAMES,
)

BEAT_RE = re.compile(r"(?im)^##\s*BEAT\s+\d+\b.*$")
SECTION_RE = re.compile(r"(?im)^##\s+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
CHARACTER_HEADING_RE = re.compile(r"(?m)^###\s+(.+?)\s*$")


def _make_narrative_issue(
    rule_id: str,
    chapter: Optional[str],
    file: Optional[Path],
    **format_kwargs,
) -> ManuscriptIssue:
    severity, base_message = NARRATIVE_RULE_META.get(rule_id, (Severity.INFO, "Narrative issue"))
    message = base_message.format(**format_kwargs)
    return ManuscriptIssue(
        severity=severity,
        category=IssueCategory.NARRATIVE,
        chapter=chapter,
        file=file,
        rule_id=rule_id,
        message=message,
        fingerprint=compute_fingerprint(rule_id, file, None, None),
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _configured_antagonists() -> dict[str, dict[str, set[str]]]:
    settings = validator.load_project_settings()
    narrative_quality = settings.get("narrative_quality", {})
    if not isinstance(narrative_quality, dict):
        return {}
    antagonists = narrative_quality.get("antagonists", {})
    if not isinstance(antagonists, dict):
        return {}

    profiles: dict[str, dict[str, set[str]]] = {}
    for raw_key, raw_profile in antagonists.items():
        if not isinstance(raw_profile, dict):
            continue
        key = str(raw_key).strip().lower()
        markers = set(_string_list(raw_profile.get("markers")))
        tactical_motifs = set(_string_list(raw_profile.get("tactical_motifs")))
        if key and markers and tactical_motifs:
            profiles[key] = {
                "markers": markers,
                "tactical_motifs": tactical_motifs,
            }
    return profiles


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_RE.split(text.strip()) if s.strip()]


def _contains_any(text: str, terms: set[str] | list[str]) -> bool:
    return any(term in text for term in terms)


def _stake_name_aliases(line: str) -> list[str]:
    match = re.match(r"^\s*-\s*([^:\n]+):", line)
    if not match:
        return []
    name = match.group(1).strip()
    if not name or name.lower().startswith("character name"):
        return []

    aliases = {name.lower()}
    first = name.split()[0].strip(" ,.;")
    if first:
        aliases.add(first.lower())
    return sorted(aliases, key=len, reverse=True)


def _extract_section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    start = text.find("\n", start)
    if start < 0:
        return ""
    start += 1
    next_match = SECTION_RE.search(text[start:])
    if not next_match:
        return text[start:].strip()
    return text[start : start + next_match.start()].strip()


def _extract_beats(scene_text: str) -> list[str]:
    markers = list(BEAT_RE.finditer(scene_text))
    if not markers:
        return []

    beats: list[str] = []
    for index, marker in enumerate(markers):
        start = marker.start()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(scene_text)
        block = scene_text[start:end].strip()
        if block:
            beats.append(block)
    return beats


def _extract_character_section(text: str) -> str:
    for heading in ("## Characters", "## Character Profiles"):
        start = text.find(heading)
        if start >= 0:
            start = text.find("\n", start)
            if start < 0:
                return ""
            start += 1
            next_match = SECTION_RE.search(text[start:])
            return text[start : start + next_match.start()].strip() if next_match else text[start:].strip()
    return ""


def _clean_character_name(raw_name: str) -> str:
    name = raw_name.strip().strip("# ").strip()
    name = re.sub(r"\s+\(.*?\)\s*$", "", name).strip()
    name = re.sub(r"\s+-\s+.*$", "", name).strip()
    return name


def _first_name(name: str) -> str:
    lower_name = name.lower()
    if "'s" in lower_name and any(term in lower_name for term in (" son", " daughter", " child")):
        return ""
    parts = [part.strip('"“”.,;:') for part in name.split() if part.strip('"“”.,;:')]
    while parts and parts[0].lower() in TITLE_WORDS:
        parts.pop(0)
    return parts[0].lower() if parts else ""


def _rulebook_character_names(rulebook_path: Path) -> set[str]:
    if not rulebook_path.exists():
        return set()
    section = _extract_character_section(rulebook_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for match in CHARACTER_HEADING_RE.finditer(section):
        name = _clean_character_name(match.group(1))
        lower = name.lower()
        if not name or lower in GENERIC_CHARACTER_HEADINGS:
            continue
        if lower.startswith("chapter ") or lower.startswith("from book "):
            continue
        names.add(name)
    return names


def _world_state_character_names(world_state_path: Path) -> set[str]:
    if not world_state_path.exists():
        return set()
    try:
        data = json.loads(world_state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return set()
    characters = data.get("characters")
    if not isinstance(characters, dict):
        return set()
    names: set[str] = set()
    for key, value in characters.items():
        if isinstance(value, dict):
            display = value.get("name") or value.get("full_name") or value.get("fullName") or key
        else:
            display = key
        display = str(display).replace("_", " ").strip()
        if display:
            names.add(display.title())
    return names


def _book_character_names(book_folder: Path) -> set[str]:
    return _rulebook_character_names(book_folder / "rulebook.md") | _world_state_character_names(
        book_folder / "world-state.json"
    )


def _book_order_key(book_folder: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)$", book_folder.name)
    return (int(match.group(1)) if match else 10**9, book_folder.name)
