"""Specific narrative validation checks."""

from __future__ import annotations

import re
from itertools import combinations
from pathlib import Path

from bookforge.core.issue import ManuscriptIssue
from bookforge.core.narrative_quality.constants import (
    INTENT_KEYWORDS,
    SYSTEM_TERMS,
    SENSORY_ACTION_TERMS,
    ACTION_VERBS,
    DECISION_TERMS,
    STAKES_TERMS,
    ANTAGONIST_COST_TERMS,
    EXPECTED_RECURRING_FIRST_NAMES,
)
from bookforge.core.narrative_quality.helpers import (
    _make_narrative_issue,
    _configured_antagonists,
    _book_character_names,
    _book_order_key,
    _first_name,
    _contains_any,
    _extract_section,
    _stake_name_aliases,
    _split_sentences,
)


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
