#!/usr/bin/env python3
"""Narrative quality heuristics for manuscript workflow checks."""

from __future__ import annotations

import re
from itertools import combinations
from dataclasses import dataclass
from pathlib import Path

from bookforge.core import validator

ANTAGONIST_MARKERS = {
    "vex": ["silas vex", "vex"],
    "klyne": ["jethro klyne", "klyne"],
    "rooke": ["thaddeus rooke", "thaddeus", "rooke"],
    "fane": ["darrow fane", "fane"],
    "draven": ["milo draven", "draven"],
}

ANTAGONIST_TACTICAL_MOTIFS = {
    "vex": {
        "blackmail",
        "frame",
        "evidence",
        "payoff",
        "legacy",
        "debt",
        "network",
        "field",
        "deal",
        "remnant",
        "remnants",
        "mark",
        "ledger",
        "rumor",
        "warrant",
    },
    "klyne": {
        "leak",
        "watch",
        "trail",
        "report",
        "warrant",
        "tracker",
        "range",
        "dispatch",
        "surveillance",
        "involvement",
        "surface",
        "route",
    },
    "rooke": {
        "survey",
        "rail",
        "paperwork",
        "displace",
        "claim",
        "legal",
        "statement",
        "deposition",
        "witness",
        "hearing",
        "pressure",
    },
    "fane": {
        "enforcer",
        "clash",
        "ambush",
        "intimidate",
        "confront",
        "duel",
        "bar",
        "pushing",
        "pressure",
    },
    "draven": {
        "rustler",
        "horse",
        "supply",
        "raid",
        "smoke",
        "ring",
        "forage",
        "rustling",
        "involvement",
        "surface",
    },
}

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


@dataclass(frozen=True)
class NarrativeIssue:
    chapter: str
    dimension: str
    level: str
    message: str


@dataclass(frozen=True)
class NarrativeReport:
    book_folder: Path
    issues: list[NarrativeIssue]


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
    issues: list[NarrativeIssue],
) -> str:
    if not beats and chapter_words >= 1200:
        issues.append(
            NarrativeIssue(
                chapter_slug,
                "Tension Diversity",
                "WARN",
                "Missing scene-breakdown beats; add intent-locked beats before continuing.",
            )
        )
        return "systems-only"

    chapter_intents: list[str] = []
    for beat in beats:
        chapter_intents.extend(_extract_intents(beat))

    if beats:
        unique_intents = sorted(set(chapter_intents))
        if len(unique_intents) == 1 and len(chapter_intents) >= 2:
            issues.append(
                NarrativeIssue(
                    chapter_slug,
                    "Tension Diversity",
                    "WARN",
                    "Uniform beat intent pattern in chapter; alternate action and consequence modes.",
                )
            )
        if len(unique_intents) == 0 and chapter_words >= 1000:
            issues.append(
                NarrativeIssue(
                    chapter_slug,
                    "Tension Diversity",
                    "WARN",
                    "No explicit emotional, tactical, or institutional intent markers in scene beats.",
                )
            )

        if chapter_words >= 2400 and all(_extract_intents(beat) == ["high-intensity action"] for beat in beats):
            issues.append(
                NarrativeIssue(
                    chapter_slug,
                    "Tension Diversity",
                    "WARN",
                    "Large chapter shows repeated high-intensity processing; trim duplicate pressure loops.",
                )
            )

    if beats and all(_systems_only(beat) for beat in beats) and chapter_words >= 900:
        issues.append(
            NarrativeIssue(
                chapter_slug,
                "Tension Diversity",
                "WARN",
                "Scene progression reads as systems-only; every pressure phase needs a direct character-beat consequence.",
            )
        )

    return chapter_intents[0] if chapter_intents else "systems-only"


def _check_character_distinctiveness(
    chapter_slug: str,
    continuity_text: str,
    draft_text: str,
    issues: list[NarrativeIssue],
) -> None:
    stakes_block = _extract_section(continuity_text, "Human Stakes Carried")
    if not stakes_block:
        issues.append(
            NarrativeIssue(
                chapter_slug,
                "Character Distinctiveness",
                "WARN",
                "Add a 'Human Stakes Carried' section in continuity-out.md for named characters carrying next-chapter pressure.",
            )
        )
        return

    raw_stakes_lines = [line for line in stakes_block.splitlines() if line.strip().startswith("-")]
    stake_entries = [
        (raw_line, _stake_name_aliases(raw_line))
        for raw_line in raw_stakes_lines
    ]
    stake_entries = [(raw_line, aliases) for raw_line, aliases in stake_entries if aliases]

    if not stake_entries:
        issues.append(
            NarrativeIssue(
                chapter_slug,
                "Character Distinctiveness",
                "WARN",
                "Human Stakes Carried has no named character entries.",
            )
        )
        return

    draft_lower = draft_text.lower()
    for raw_line, aliases in stake_entries:
        display_name = raw_line.strip()[1:].split(":", 1)[0].strip()
        lower_line = raw_line.lower()
        if not _contains_any(lower_line, STAKES_TERMS):
            issues.append(
                NarrativeIssue(
                    chapter_slug,
                    "Character Distinctiveness",
                    "WARN",
                    f"{display_name} stake entry exists but has no pressure/cost wording.",
                )
            )
        if not any(alias in draft_lower for alias in aliases):
            issues.append(
                NarrativeIssue(
                    chapter_slug,
                    "Character Distinctiveness",
                    "WARN",
                    f"{display_name} has no direct scene pressure line in draft.",
                )
            )


def _collect_antagonist_contexts(text: str) -> dict[str, str]:
    lower = text.lower()
    contexts: dict[str, str] = {}
    for key, aliases in ANTAGONIST_MARKERS.items():
        for alias in aliases:
            for match in re.finditer(rf"\b{re.escape(alias)}\b", lower):
                start = max(0, match.start() - 220)
                end = min(len(lower), match.end() + 220)
                contexts[key] = contexts.get(key, "") + " " + lower[start:end]
    return contexts


def _check_antagonist_contrast(chapter_slug: str, source_text: str, issues: list[NarrativeIssue]) -> None:
    contexts = _collect_antagonist_contexts(source_text)
    mentioned = list(contexts.keys())
    if len(mentioned) <= 1:
        return

    goal_profiles: dict[str, set[str]] = {}
    missing_cost: list[str] = []
    for key, context in contexts.items():
        goal_hits = {goal for goal in ANTAGONIST_TACTICAL_MOTIFS[key] if goal in context}
        goal_profiles[key] = goal_hits
        if not goal_hits:
            issues.append(
                NarrativeIssue(
                    chapter_slug,
                    "Antagonist Contrast",
                    "WARN",
                    f"{key.title()} is present but lacks distinct tactical markers; show tactical intent and chosen pressure method.",
                )
            )
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
        issues.append(
            NarrativeIssue(
                chapter_slug,
                "Antagonist Contrast",
                "WARN",
                "Active antagonists are framed with overlapping pressure posture; separate intent by tactic and emotional effect.",
            )
        )
    if missing_cost:
        issues.append(
            NarrativeIssue(
                chapter_slug,
                "Antagonist Contrast",
                "WARN",
                "At least one antagonist pressure scene is missing explicit emotional cost on named characters.",
            )
        )


def _check_sensory_decision(chapter_slug: str, draft_text: str, issues: list[NarrativeIssue]) -> None:
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
        issues.append(
            NarrativeIssue(
                chapter_slug,
                "Sensory-to-Decision Anchoring",
                "WARN",
                f"{weak_count} decision transitions lack sensory/action grounding.",
            )
        )


def _check_rotation(history: list[str], chapter_idx: int, current_intent: str) -> list[NarrativeIssue]:
    issues: list[NarrativeIssue] = []
    if chapter_idx >= 2 and len({*history[-2:], current_intent}) == 1:
        issues.append(
            NarrativeIssue(
                f"chapter-{chapter_idx + 1:02d}",
                "Scene Intent Rotation",
                "WARN",
                "Three consecutive chapters share one dominant scene intent; rotate intent class across chapters.",
            )
        )
    return issues


def analyze(book_folder: Path) -> NarrativeReport:
    chapters = validator.discover_chapters(book_folder)
    issues: list[NarrativeIssue] = []
    chapter_intent_history: list[str] = []

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

    return NarrativeReport(book_folder=book_folder, issues=issues)


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
            lines.append(f"- **{issue.chapter}** [{issue.dimension}] {issue.message}")
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
        default="books/tex-cade",
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
