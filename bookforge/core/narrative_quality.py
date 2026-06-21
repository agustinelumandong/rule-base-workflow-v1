#!/usr/bin/env python3
"""Narrative quality heuristics for manuscript workflow checks."""

from __future__ import annotations

import json
import re
from itertools import combinations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from bookforge.core import validator
from bookforge.core.issue import IssueCategory, ManuscriptIssue, Severity, compute_fingerprint

NARRATIVE_RULE_META = {
    "NARRATIVE_NAME_COLLISION": (Severity.SOFT, "First name '{first}' appears in current character '{current}' and prior character(s): {prior}. Rename or document intentional reuse."),
    "NARRATIVE_MISSING_BEATS": (Severity.SOFT, "Missing scene-breakdown beats; add intent-locked beats before continuing."),
    "NARRATIVE_UNIFORM_INTENT": (Severity.SOFT, "Uniform beat intent pattern in chapter; alternate action and consequence modes."),
    "NARRATIVE_NO_INTENT_MARKERS": (Severity.SOFT, "No explicit emotional, tactical, or institutional intent markers in scene beats."),
    "NARRATIVE_REPEATED_INTENSITY": (Severity.SOFT, "Large chapter shows repeated high-intensity processing; trim duplicate pressure loops."),
    "NARRATIVE_SYSTEMS_ONLY": (Severity.SOFT, "Scene progression reads as systems-only; every pressure phase needs a direct character-beat consequence."),
    "NARRATIVE_MISSING_STAKES": (Severity.SOFT, "Add a 'Human Stakes Carried' section in continuity-out.md for named characters carrying next-chapter pressure."),
    "NARRATIVE_NO_STAKE_ENTRIES": (Severity.SOFT, "Human Stakes Carried has no named character entries."),
    "NARRATIVE_NO_PRESSURE_WORDING": (Severity.SOFT, "{name} stake entry exists but has no pressure/cost wording."),
    "NARRATIVE_NO_SCENE_PRESSURE": (Severity.SOFT, "{name} has no direct scene pressure line in draft."),
    "NARRATIVE_ANTAGONIST_NO_TACTICS": (Severity.SOFT, "{name} is present but lacks distinct tactical markers; show tactical intent and chosen pressure method."),
    "NARRATIVE_ANTAGONIST_OVERLAP": (Severity.SOFT, "Active antagonists are framed with overlapping pressure posture; separate intent by tactic and emotional effect."),
    "NARRATIVE_ANTAGONIST_NO_COST": (Severity.SOFT, "At least one antagonist pressure scene is missing explicit emotional cost on named characters."),
    "NARRATIVE_WEAK_DECISIONS": (Severity.SOFT, "{count} decision transitions lack sensory/action grounding."),
    "NARRATIVE_NO_ROTATION": (Severity.SOFT, "Three consecutive chapters share one dominant scene intent; rotate intent class across chapters."),
}


@dataclass(frozen=True)
class NarrativeIssue:
    chapter: str
    dimension: str
    level: str
    message: str


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

ANTAGONIST_COST_TERMS = {
    "cost",
    "wound",
    "fear",
    "loss",
    "grief",
    "choice",
    "anger",
    "pain",
    "hurt",
    "blood",
    "death",
    "ruin",
    "burn",
    "pressure",
    "watch",
    "route",
    "count",
    "line",
    "ring",
    "horse",
    "claim",
    "statement",
    "shadow",
    "mark",
    "network",
    "threat",
}


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

INTENT_KEYWORDS = {
    "high-intensity action": [
        "fire",
        "shot",
        "raid",
        "ambush",
        "fight",
        "duel",
        "chase",
        "pursuit",
    ],
    "alliance/strategy": [
        "alliance",
        "council",
        "pact",
        "coordination",
        "plan",
        "strategy",
        "map",
        "signal",
    ],
    "emotional consequence": [
        "choice",
        "fear",
        "grief",
        "jealous",
        "trust",
        "loyal",
        "hesitate",
        "guilt",
    ],
    "institutional pressure": [
        "hearing",
        "witness",
        "statement",
        "court",
        "evidence",
        "law",
        "deposition",
        "paperwork",
    ],
    "recovery/repair": [
        "wound",
        "care",
        "stabil",
        "repair",
        "rest",
        "blood",
        "debrief",
        "aftercare",
    ],
}

SYSTEM_TERMS = {
    "pressure",
    "route",
    "routes",
    "watch",
    "mapping",
    "ledger",
    "testimony",
    "statement",
    "evidence",
    "coordination",
    "assign",
    "stabilize",
    "patrol",
}

SENSORY_ACTION_TERMS = {
    "dust",
    "horse",
    "leather",
    "iron",
    "rope",
    "timber",
    "mud",
    "water",
    "trail",
    "ridge",
    "boots",
    "shot",
    "fire",
    "blood",
    "fist",
    "door",
    "lamp",
    "rain",
    "sun",
    "wind",
    "saddle",
    "breath",
    "torch",
    "mud",
    "ridge",
    "jaw",
}

ACTION_VERBS = {
    "grip",
    "tied",
    "pulled",
    "loaded",
    "drove",
    "fired",
    "crossed",
    "pushed",
    "bent",
    "sealed",
    "bound",
    "tracked",
    "routed",
    "reached",
    "gripped",
    "struck",
    "leaned",
    "kicked",
    "dropped",
}

DECISION_TERMS = {
    "decide",
    "decides",
    "decided",
    "chooses",
    "choose",
    "resolve",
    "resolved",
}

STAKES_TERMS = {
    "risk",
    "cost",
    "burden",
    "choice",
    "stakes",
    "pressure",
    "wound",
    "fear",
    "loyal",
    "protect",
}

BEAT_RE = re.compile(r"(?im)^##\s*BEAT\s+\d+\b.*$")
SECTION_RE = re.compile(r"(?im)^##\s+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

ROTATION_KEYS = tuple(INTENT_KEYWORDS.keys())
CHARACTER_HEADING_RE = re.compile(r"(?m)^###\s+(.+?)\s*$")
GENERIC_CHARACTER_HEADINGS = {
    "characters",
    "character profiles",
    "characters handoff state",
    "locations handoff state",
    "unresolved story pressures & setup",
    "major changes & chronology",
    "other source-locked roles",
    "from book 1",
    "from book 2",
    "from book 3",
}
EXPECTED_RECURRING_FIRST_NAMES = {"tex", "texas", "ghost"}
TITLE_WORDS = {"colonel", "old", "black", "jack"}


@dataclass(frozen=True)
class NarrativeReport:
    book_folder: Path
    issues: tuple[ManuscriptIssue, ...]


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
    except Exception:
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


def _check_series_name_collisions(book_folder: Path, issues: list[ManuscriptIssue]) -> None:
    current_names = _book_character_names(book_folder)
    if not current_names:
        return

    parent = book_folder.parent
    if not parent.exists():
        return

    prior_by_first: dict[str, set[str]] = {}
    current_order = _book_order_key(book_folder)
    for sibling in sorted(parent.iterdir()):
        if not sibling.is_dir() or sibling == book_folder:
            continue
        if _book_order_key(sibling) >= current_order:
            continue
        for name in _book_character_names(sibling):
            first = _first_name(name)
            if first and first not in EXPECTED_RECURRING_FIRST_NAMES:
                prior_by_first.setdefault(first, set()).add(name)

    for current_name in sorted(current_names):
        first = _first_name(current_name)
        if not first or first in EXPECTED_RECURRING_FIRST_NAMES:
            continue
        prior_names = {name for name in prior_by_first.get(first, set()) if name.lower() != current_name.lower()}
        if prior_names:
            issues.append(_make_narrative_issue(
                "NARRATIVE_NAME_COLLISION",
                chapter="book",
                file=book_folder / "rulebook.md",
                first=first.title(),
                current=current_name,
                prior=", ".join(sorted(prior_names)),
            ))


def _extract_intents(text: str) -> list[str]:
    lower = text.lower()
    intents: list[str] = []
    for key, keys in INTENT_KEYWORDS.items():
        if any(keyword in lower for keyword in keys):
            intents.append(key)
    return intents


def _systems_only(beat_text: str) -> bool:
    lower = beat_text.lower()
    return (
        any(term in lower for term in SYSTEM_TERMS)
        and not _contains_any(lower, SENSORY_ACTION_TERMS | ACTION_VERBS)
    )


def _check_tension_diversity(
    chapter_slug: str,
    beats: list[str],
    chapter_words: int,
    draft_text: str,
    issues: list[ManuscriptIssue],
) -> str:
    if not beats and chapter_words >= 1200:
        issues.append(_make_narrative_issue(
            "NARRATIVE_MISSING_BEATS",
            chapter=chapter_slug,
            file=None,
        ))
        return "systems-only"

    chapter_intents: list[str] = []
    for beat in beats:
        chapter_intents.extend(_extract_intents(beat))

    if beats:
        unique_intents = sorted(set(chapter_intents))
        if len(unique_intents) == 1 and len(chapter_intents) >= 2:
            issues.append(_make_narrative_issue(
                "NARRATIVE_UNIFORM_INTENT",
                chapter=chapter_slug,
                file=None,
            ))
        if len(unique_intents) == 0 and chapter_words >= 1000:
            issues.append(_make_narrative_issue(
                "NARRATIVE_NO_INTENT_MARKERS",
                chapter=chapter_slug,
                file=None,
            ))

        if chapter_words >= 2400 and all(_extract_intents(beat) == ["high-intensity action"] for beat in beats):
            issues.append(_make_narrative_issue(
                "NARRATIVE_REPEATED_INTENSITY",
                chapter=chapter_slug,
                file=None,
            ))

    if beats and all(_systems_only(beat) for beat in beats) and chapter_words >= 900:
        issues.append(_make_narrative_issue(
            "NARRATIVE_SYSTEMS_ONLY",
            chapter=chapter_slug,
            file=None,
        ))

    return chapter_intents[0] if chapter_intents else "systems-only"


def _check_character_distinctiveness(
    chapter_slug: str,
    continuity_text: str,
    draft_text: str,
    issues: list[ManuscriptIssue],
) -> None:
    stakes_block = _extract_section(continuity_text, "Human Stakes Carried")
    if not stakes_block:
        issues.append(_make_narrative_issue(
            "NARRATIVE_MISSING_STAKES",
            chapter=chapter_slug,
            file=None,
        ))
        return

    raw_stakes_lines = [line for line in stakes_block.splitlines() if line.strip().startswith("-")]
    stake_entries = [
        (raw_line, _stake_name_aliases(raw_line))
        for raw_line in raw_stakes_lines
    ]
    stake_entries = [(raw_line, aliases) for raw_line, aliases in stake_entries if aliases]

    if not stake_entries:
        issues.append(_make_narrative_issue(
            "NARRATIVE_NO_STAKE_ENTRIES",
            chapter=chapter_slug,
            file=None,
        ))
        return

    draft_lower = draft_text.lower()
    for raw_line, aliases in stake_entries:
        display_name = raw_line.strip()[1:].split(":", 1)[0].strip()
        lower_line = raw_line.lower()
        if not _contains_any(lower_line, STAKES_TERMS):
            issues.append(_make_narrative_issue(
                "NARRATIVE_NO_PRESSURE_WORDING",
                chapter=chapter_slug,
                file=None,
                name=display_name,
            ))
        if not any(alias in draft_lower for alias in aliases):
            issues.append(_make_narrative_issue(
                "NARRATIVE_NO_SCENE_PRESSURE",
                chapter=chapter_slug,
                file=None,
                name=display_name,
            ))


def _collect_antagonist_contexts(text: str) -> dict[str, str]:
    lower = text.lower()
    contexts: dict[str, str] = {}
    for key, profile in _configured_antagonists().items():
        for alias in profile["markers"]:
            for match in re.finditer(rf"\b{re.escape(alias)}\b", lower):
                start = max(0, match.start() - 220)
                end = min(len(lower), match.end() + 220)
                contexts[key] = contexts.get(key, "") + " " + lower[start:end]
    return contexts


def _check_antagonist_contrast(chapter_slug: str, source_text: str, issues: list[ManuscriptIssue]) -> None:
    antagonist_profiles = _configured_antagonists()
    if not antagonist_profiles:
        return
    contexts = _collect_antagonist_contexts(source_text)
    mentioned = list(contexts.keys())
    if len(mentioned) <= 1:
        return

    goal_profiles: dict[str, set[str]] = {}
    missing_cost: list[str] = []
    for key, context in contexts.items():
        goal_hits = {goal for goal in antagonist_profiles[key]["tactical_motifs"] if goal in context}
        goal_profiles[key] = goal_hits
        if not goal_hits:
            issues.append(_make_narrative_issue(
                "NARRATIVE_ANTAGONIST_NO_TACTICS",
                chapter=chapter_slug,
                file=None,
                name=key.title(),
            ))
        if not _contains_any(context, ANTAGONIST_COST_TERMS):
            missing_cost.append(key)

    non_empty_profiles = [v for v in goal_profiles.values() if v]
    overlap = False
    if len(non_empty_profiles) >= 2:
        for first, second in combinations(non_empty_profiles, 2):
            intersection = len(first.intersection(second))
            if (
                len(first) > 2
                and len(second) > 2
                and intersection >= 2
                and intersection >= min(len(first), len(second))
            ):
                overlap = True
                break
    if overlap:
        issues.append(_make_narrative_issue(
            "NARRATIVE_ANTAGONIST_OVERLAP",
            chapter=chapter_slug,
            file=None,
        ))
    if missing_cost:
        issues.append(_make_narrative_issue(
            "NARRATIVE_ANTAGONIST_NO_COST",
            chapter=chapter_slug,
            file=None,
        ))


def _check_sensory_decision(chapter_slug: str, draft_text: str, issues: list[ManuscriptIssue]) -> None:
    weak_count = 0
    for sentence in _split_sentences(draft_text):
        lower = sentence.lower()
        if not _contains_any(lower, DECISION_TERMS):
            continue
        if _contains_any(lower, {"shot", "fire", "blade", "killed", "ambush", "duel"}):
            continue
        if not _contains_any(lower, SENSORY_ACTION_TERMS | ACTION_VERBS):
            weak_count += 1

    if weak_count >= 2:
        issues.append(_make_narrative_issue(
            "NARRATIVE_WEAK_DECISIONS",
            chapter=chapter_slug,
            file=None,
            count=weak_count,
        ))


def _check_rotation(history: list[str], chapter_idx: int, current_intent: str) -> list[ManuscriptIssue]:
    issues: list[ManuscriptIssue] = []
    if chapter_idx >= 2 and len({*history[-2:], current_intent}) == 1:
        issues.append(_make_narrative_issue(
            "NARRATIVE_NO_ROTATION",
            chapter=f"chapter-{chapter_idx + 1:02d}",
            file=None,
        ))
    return issues


def analyze(book_folder: Path) -> NarrativeReport:
    chapters = validator.discover_chapters(book_folder)
    issues: list[ManuscriptIssue] = []
    chapter_intent_history: list[str] = []

    _check_series_name_collisions(book_folder, issues)

    for idx, chapter in enumerate(chapters):
        if not chapter.draft.exists():
            continue

        draft_text = chapter.draft.read_text(encoding="utf-8")
        scene_text = chapter.scene_breakdown.read_text(encoding="utf-8") if chapter.scene_breakdown.exists() else ""
        continuity_path = chapter.folder / "continuity-out.md"
        continuity_text = continuity_path.read_text(encoding="utf-8") if continuity_path.exists() else ""

        beats = _extract_beats(scene_text)
        dominant_intent = _check_tension_diversity(
            chapter.slug,
            beats,
            len(draft_text.split()),
            draft_text,
            issues,
        )
        issues.extend(_check_rotation(chapter_intent_history, idx, dominant_intent))
        chapter_intent_history.append(dominant_intent)
        if len(chapter_intent_history) > 2:
            chapter_intent_history = chapter_intent_history[-2:]

        _check_character_distinctiveness(chapter.slug, continuity_text, draft_text, issues)
        _check_antagonist_contrast(chapter.slug, f"{draft_text}\n{scene_text}\n{continuity_text}", issues)
        _check_sensory_decision(chapter.slug, draft_text, issues)

    return NarrativeReport(book_folder=book_folder, issues=tuple(issues))


def render_report(report: NarrativeReport) -> str:
    lines = [
        "# Narrative Quality Report",
        "",
        f"- **Book Folder:** `{report.book_folder}`",
        f"- **Issue Count:** {len(report.issues)}",
        "",
        "## Findings",
    ]
    if report.issues:
        for issue in report.issues:
            lines.append(f"- **{issue.chapter or 'book'}** [{issue.category.name}] {issue.message}")
    else:
        lines.append("- No narrative-quality flags.")
    return "\n".join(lines)


def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Check narrative quality gates for manuscript loop quality."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/book-example",
        help="Book folder containing chapter artifacts.",
    )
    args = parser.parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    report = analyze(book_folder)
    print(render_report(report))
    return 1 if report.issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
