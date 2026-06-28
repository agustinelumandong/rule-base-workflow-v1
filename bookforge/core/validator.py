#!/usr/bin/env python3
"""BookForge Validator Core Module.

Deterministic context and style check tools.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from bookforge.core.issue import (
    IssueCategory,
    IssueStatus,
    ManuscriptIssue,
    Severity,
    compute_fingerprint,
)
from bookforge.core.prompts import load_prompt_template
from bookforge.core import action
from bookforge.core import world as world_module
from bookforge.core import voice as voice_module
from bookforge.core import unknowns as unknowns_module

REQUIRED_BOOK_FILES = ["rulebook.md", "mood-lock.md", "chapter-summaries.md"]
BEAT_REQUIRED_MARKERS = ["### Source Context Lock", "### Beat Instructions"]
RULEBOOK_SECTION_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)

REQUIRED_RULEBOOK_SECTIONS: dict[str, tuple[str, ...]] = {
    "Source Hierarchy": ("Source Hierarchy",),
    "Length Handling Rules": ("Length Handling Rules",),
    "Do Not Invent": ("Do Not Invent",),
    "Chapter Continuity Ledger": ("Chapter Continuity Ledger", "Continuity Ledger"),
    "Unknowns": ("Unknowns",),
    "Characters": ("Characters", "Character Profiles"),
}
RULEBOOK_UNKNOWN_ALLOWED_SECTIONS = {
    "characters",
    "character profiles",
    "unknowns",
    "world and setting",
}

UNRESOLVED_MARKERS = ["UNKNOWN", "TBD", "TODO", "FIXME"]
FORBIDDEN_LENGTH_LANGUAGE = ["word count", "words", "quota", "target"]

BANNED_AI_ECHO_WORDS = [
    "absolutely",
    "completely",
    "relentless",
    "massive",
    "sharp",
    "heavy",
    "pure",
    "extremely",
    "perfectly",
]

MODERN_OR_CLINICAL_WORDS = [
    "velocity",
    "fraction",
    "trajectory",
    "impact",
    "visible",
    "resolving",
]

INTERNAL_MONOLOGUE_PHRASES = ["he felt", "he realized", "he thought", "she felt", "she realized", "she thought"]

FORBIDDEN_CONFLICT_PATTERNS = {
    "water rights": r"\bwater\s+rights?\b",
    "syndicate": r"\bsyndicates?\b",
    "land grab": r"\bland\s*grabs?\b",
    "business scheme": r"\bbusiness\s+schemes?\b",
    "organized corruption": r"\borganized\s+corruption\b",
    "property dispute": r"\bproperty\s+disputes?\b",
    "business conspiracy": r"\bbusiness\s+conspirac(?:y|ies)\b",
    "syndicate-style": r"\bsyndicate-style\b",
    "voss": r"\bvoss\b",
}

PROJECT_RULE_BANNED_NAME_LABELS = {"voss"}

DEFAULT_SETTINGS: dict[str, Any] = {
    "operator_prose_guard": {
        "enabled": True,
        "mode": "advisory",
        "output_token_cap": 500,
        "operator_personas": ["extractor", "reviewer", "planner"],
        "prose_actions": ["draft", "draft_prose", "expand"],
    },
    "name_policy": {
        "banned_names": [],
        "allowed_names": [],
        "scope": "system_forward",
    },
    "style_review": {
        "enabled": True,
        "review_only": True,
        "max_summary_words_without_dialogue": 120,
        "analysis_terms": [
            "realized",
            "processed",
            "understood",
            "psychological",
            "emotional",
            "motif",
            "symbolism",
        ],
        "formal_dialogue_terms": [
            "traverse",
            "obscures",
            "therefore",
            "endeavor",
            "proceed",
        ],
        "time_jump_terms": [
            "hours later",
            "days later",
            "weeks later",
            "after some time",
        ],
        "warn_short_sentence_runs": True,
        "thought_over_behavior": {
            "enabled": True,
            "review_only": True,
            "max_findings": 8,
            "phrase_role": "reference_seeds",
            "phrases": [
                "that mattered",
                "that counted",
                "that meant",
                "careful was worth",
                "respect showed",
                "none of it made",
                "it made use",
                "useful, dangerous",
                "did not become kind",
                "became careful",
                "worth more",
                "began to see",
                "understood",
                "realized",
            ],
            "meaning_markers": [
                "meant",
                "proved",
                "showed",
                "counted",
                "mattered",
                "changed",
            ],
            "abstract_labels": [
                "respect",
                "trust",
                "fear",
                "danger",
                "kindness",
                "useful",
                "mercy",
                "welcome",
            ],
            "explanation_shapes": [
                "that was why",
                "that was not",
                "none of it",
                "it made",
                "made him",
                "made her",
                "made them",
                "he understood",
                "she understood",
                "they understood",
                "he realized",
                "she realized",
                "they realized",
            ],
        },
        "banned_terms": [
            "no clean answer",
            "tactical position",
            "leverage",
            "pressure point",
            "emotional cost",
            "control the ground",
            "move fast",
            "stay focused",
            "legalese",
            "cost center",
            "synergy",
            "bandwidth",
            "stakeholder",
            "deliverable",
            "action item",
            "team player",
            "circle back",
            "move the needle",
            "low-hanging fruit",
            "deep dive",
            "take offline",
            "game changer",
            "paradigm",
            "disruption",
        ],
    },
    "historical_terms": {
        "banned": ["cost center"],
        "warn": [],
        "context_required": [
            "appeal",
            "civil judgment",
            "cooperation will be recorded",
            "custody",
            "exhibit",
            "foreclosure petition",
            "mortgage lien",
            "sequestration",
            "writ",
        ],
        "review_only": [
            "bank packet",
            "bond",
            "court",
            "hearing",
            "petition",
            "signature page",
            "warrant",
            "witness list",
        ],
    },
    "style_profiles": {
        "fallback_profile": "default",
        "year_buckets": [
            {"name": "frontier_1880s", "start": 1880, "end": 1899},
            {"name": "frontier_transition_1900s", "start": 1900, "end": 1912},
        ],
        "profiles": {
            "default": {
                "voice": {
                    "banned_slang": ["y'all", "howdy", "partner", "reckon", "drawl"],
                },
            },
            "frontier_1880s": {
                "voice": {
                    "banned_slang": ["y'all", "howdy", "partner", "reckon", "drawl"],
                },
            },
            "frontier_transition_1900s": {
                "voice": {
                    "banned_slang": ["y'all", "drawl", "reckon"],
                },
            },
        },
    },
    "plot_mode_review": {
        "enabled": True,
        "review_only": True,
        "legal_procedure_threshold": 6,
        "ban_markers": [
            "no courtroom",
            "no courtrooms",
            "no trial",
            "no trial scene",
            "no legal-procedure",
            "no legal procedure",
        ],
        "legal_procedure_terms": [
            "appeal",
            "bond",
            "civil judgment",
            "court",
            "courtroom",
            "custody",
            "exhibit",
            "foreclosure",
            "hearing",
            "judge",
            "legal",
            "lien",
            "mortgage",
            "petition",
            "sequestration",
            "trial",
            "warrant",
            "witness list",
            "writ",
        ],
    },
}

DIALOGUE_TAG_RE = re.compile(
    r'"[^"]*"\s*(?:—\s*)?(?:[A-Z][A-Za-z\'-]*\s+)?'
    r"(said|asked|shouted|whispered|cried|replied|exclaimed|called|muttered|grumbled|demanded)\b"
    r'|'
    r"\b(said|asked|shouted|whispered|cried|replied|exclaimed|called|muttered|grumbled|demanded)\s*,\s*\"[^\"]*\"",
    re.IGNORECASE,
)

PHASE_CHAPTER_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?(Chapter\s+(\d+)|Epilogue(?:\s+Teaser)?)(?:\*\*)?(?:\s*[:\-].*)?$"
)

FIELD_RE = re.compile(r"^- \*\*(Source Anchor|Required Story Movement):\*\* (.+)$", re.MULTILINE)
EXIT_HOOK_PREFIX_RE = re.compile(r"^Exit hook / transition required by source:\s*", re.IGNORECASE)

ING_OPENER_RE = re.compile(r"(?m)^([A-Z][A-Za-z]{2,}ing)\b[\s,]")
ING_OPENER_EXCLUSIONS = {
    "during", "bring", "ring", "sing", "thing", "spring",
    "morning", "evening", "nothing", "something", "everything", "anything",
    "king", "wing", "sling", "string", "cling", "fling", "sting", "swing", "wring",
    "lightning", "awning", "ceiling", "lining", "sterling", "cunning", "darling",
    "sibling", "sapling", "farthing", "inkling", "shilling", "herring", "pudding"
}
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
PRONOUN_FIXED = frozenset({"he", "she", "they", "it"})
PRONOUN_LOOP_MIN_RUN = 3

CONTEXT_LOCK_MARKER = "### Source Context Lock"
CONTEXT_LOCK_END_MARKER = "###"

STOPWORDS = {
    "about", "after", "again", "against", "all", "and", "any", "are", "because", "been", "before",
    "being", "between", "both", "but", "came", "come", "did", "down", "each", "few", "for", "from",
    "had", "has", "have", "her", "here", "him", "his", "how", "into", "its", "just", "like", "many",
    "more", "most", "off", "once", "only", "other", "our", "out", "over", "same", "she", "should",
    "some", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "those", "through", "too", "under", "until", "upon", "very", "was", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your",
}

BEAT_RE = re.compile(r"^##\s+BEAT\s+\d+[:\s]", re.MULTILINE | re.IGNORECASE)


@dataclass(frozen=True)
class RuleMeta:
    rule_id: str
    severity: Severity
    category: IssueCategory
    suggested_fix_type: Optional[str] = None


RULE_META: dict[str, RuleMeta] = {
    "VALIDATOR_MISSING_OUTLINE": RuleMeta("VALIDATOR_MISSING_OUTLINE", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_BOOK_FILE": RuleMeta("VALIDATOR_MISSING_BOOK_FILE", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_RULEBOOK_SECTION": RuleMeta("VALIDATOR_MISSING_RULEBOOK_SECTION", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_EMPTY_RULEBOOK_SECTION": RuleMeta("VALIDATOR_EMPTY_RULEBOOK_SECTION", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_UNKNOWNS_IN_RULEBOOK": RuleMeta("VALIDATOR_UNKNOWNS_IN_RULEBOOK", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_CONTINUITY_LEDGER": RuleMeta("VALIDATOR_MISSING_CONTINUITY_LEDGER", Severity.HARD, IssueCategory.CONTINUITY),
    "VALIDATOR_UNRESOLVED_UNKNOWN": RuleMeta("VALIDATOR_UNRESOLVED_UNKNOWN", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_SCENE_BREAKDOWN": RuleMeta("VALIDATOR_MISSING_SCENE_BREAKDOWN", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_NO_BEATS": RuleMeta("VALIDATOR_NO_BEATS", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_BEAT_MARKER": RuleMeta("VALIDATOR_MISSING_BEAT_MARKER", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_CONTEXT_LOCK": RuleMeta("VALIDATOR_MISSING_CONTEXT_LOCK", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_CONTEXT_LOCK_UNKNOWN": RuleMeta("VALIDATOR_CONTEXT_LOCK_UNKNOWN", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_DRAFTING_PLAN": RuleMeta("VALIDATOR_MISSING_DRAFTING_PLAN", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_DRAFT": RuleMeta("VALIDATOR_MISSING_DRAFT", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_EMPTY_DRAFT": RuleMeta("VALIDATOR_EMPTY_DRAFT", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_FORBIDDEN_LENGTH_LANGUAGE": RuleMeta("VALIDATOR_FORBIDDEN_LENGTH_LANGUAGE", Severity.HARD, IssueCategory.STYLE, "remove_forbidden_language"),
    "VALIDATOR_UNRESOLVED_MARKER": RuleMeta("VALIDATOR_UNRESOLVED_MARKER", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_FORBIDDEN_CONFLICT": RuleMeta("VALIDATOR_FORBIDDEN_CONFLICT", Severity.HARD, IssueCategory.NARRATIVE),
    "VALIDATOR_BANNED_ECHO_WORD": RuleMeta("VALIDATOR_BANNED_ECHO_WORD", Severity.SOFT, IssueCategory.STYLE, "replace_word"),
    "VALIDATOR_MODERN_WORD": RuleMeta("VALIDATOR_MODERN_WORD", Severity.SOFT, IssueCategory.STYLE, "replace_word"),
    "VALIDATOR_INTERNAL_MONOLOGUE": RuleMeta("VALIDATOR_INTERNAL_MONOLOGUE", Severity.SOFT, IssueCategory.STYLE, "remove_internal_monologue"),
    "VALIDATOR_UNWANTED_DIALOGUE_TAG": RuleMeta("VALIDATOR_UNWANTED_DIALOGUE_TAG", Severity.SOFT, IssueCategory.STYLE, "remove_dialogue_tag"),
    "VALIDATOR_ING_OPENER": RuleMeta("VALIDATOR_ING_OPENER", Severity.SOFT, IssueCategory.STYLE, "fix_sentence_opener"),
    "VALIDATOR_PRONOUN_LOOP": RuleMeta("VALIDATOR_PRONOUN_LOOP", Severity.SOFT, IssueCategory.STYLE, "fix_pronoun_loop"),
    "VALIDATOR_EM_DASH_ANCHOR": RuleMeta("VALIDATOR_EM_DASH_ANCHOR", Severity.SOFT, IssueCategory.STYLE, "fix_em_dash_anchor"),
    "VALIDATOR_ANACHRONISM": RuleMeta("VALIDATOR_ANACHRONISM", Severity.SOFT, IssueCategory.STYLE, "replace_anachronism"),
    "VALIDATOR_UNPROFILED_PERIOD_TERM": RuleMeta("VALIDATOR_UNPROFILED_PERIOD_TERM", Severity.INFO, IssueCategory.CONTEXT),
    "VALIDATOR_MISSING_COMBAT_PLAN": RuleMeta("VALIDATOR_MISSING_COMBAT_PLAN", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_WORLD_STATE_VIOLATION": RuleMeta("VALIDATOR_WORLD_STATE_VIOLATION", Severity.SOFT, IssueCategory.CONTINUITY),
    "VALIDATOR_RELATIONSHIP_VIOLATION": RuleMeta("VALIDATOR_RELATIONSHIP_VIOLATION", Severity.SOFT, IssueCategory.CONTINUITY),
    "VALIDATOR_MISSING_CONTINUITY_OUT": RuleMeta("VALIDATOR_MISSING_CONTINUITY_OUT", Severity.SOFT, IssueCategory.CONTINUITY),
    "VALIDATOR_EMPTY_CONTINUITY_OUT": RuleMeta("VALIDATOR_EMPTY_CONTINUITY_OUT", Severity.SOFT, IssueCategory.CONTINUITY),
    "VALIDATOR_WEAK_SOURCE_COVERAGE": RuleMeta("VALIDATOR_WEAK_SOURCE_COVERAGE", Severity.SOFT, IssueCategory.CONTEXT),
    "VALIDATOR_WEAK_BEAT_COVERAGE": RuleMeta("VALIDATOR_WEAK_BEAT_COVERAGE", Severity.SOFT, IssueCategory.CONTEXT),
    "CHAPTER_REVIEW_MISSING": RuleMeta("CHAPTER_REVIEW_MISSING", Severity.HARD, IssueCategory.RHYTHM),
    "CHAPTER_REVIEW_NOT_READY": RuleMeta("CHAPTER_REVIEW_NOT_READY", Severity.HARD, IssueCategory.RHYTHM),
    "BEAT_UNDERDEVELOPED": RuleMeta("BEAT_UNDERDEVELOPED", Severity.HARD, IssueCategory.RHYTHM),
    "CHAPTER_RANGE_TRIPWIRE": RuleMeta("CHAPTER_RANGE_TRIPWIRE", Severity.SOFT, IssueCategory.RHYTHM),
    "CHAPTER_LONG_BLOCK": RuleMeta("CHAPTER_LONG_BLOCK", Severity.SOFT, IssueCategory.RHYTHM),
    "CHAPTER_BREAK_OPPORTUNITY": RuleMeta("CHAPTER_BREAK_OPPORTUNITY", Severity.INFO, IssueCategory.RHYTHM),
    "VALIDATOR_NO_MATCHING_SOURCE": RuleMeta("VALIDATOR_NO_MATCHING_SOURCE", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_POV_VIOLATION": RuleMeta("VALIDATOR_POV_VIOLATION", Severity.HARD, IssueCategory.STYLE),
    "VALIDATOR_SENTENCE_OPENER_ISSUE": RuleMeta("VALIDATOR_SENTENCE_OPENER_ISSUE", Severity.SOFT, IssueCategory.STYLE),
    "VALIDATOR_STYLE_REVIEW_SIGNAL": RuleMeta("VALIDATOR_STYLE_REVIEW_SIGNAL", Severity.SOFT, IssueCategory.STYLE),
    "VALIDATOR_DIRECT_RULEBOOK_EDIT_DEPRECATED": RuleMeta("VALIDATOR_DIRECT_RULEBOOK_EDIT_DEPRECATED", Severity.SOFT, IssueCategory.CONTEXT),
    "VALIDATOR_REPEATED_PROSE": RuleMeta("VALIDATOR_REPEATED_PROSE", Severity.SOFT, IssueCategory.STYLE),
    "VALIDATOR_PLOT_MODE_RISK": RuleMeta("VALIDATOR_PLOT_MODE_RISK", Severity.SOFT, IssueCategory.NARRATIVE),
    "VALIDATOR_OUTLINE_LIFE_STATE_CONTRADICTION": RuleMeta("VALIDATOR_OUTLINE_LIFE_STATE_CONTRADICTION", Severity.SOFT, IssueCategory.CONTINUITY),
}


def _make_issue(
    rule_id: str,
    message: str,
    chapter: str | None = None,
    file: Path | None = None,
    line: int | None = None,
    span: str | None = None,
    severity: Severity | None = None,
) -> ManuscriptIssue:
    meta = RULE_META.get(rule_id, RuleMeta(rule_id, Severity.INFO, IssueCategory.CONTEXT))
    return ManuscriptIssue(
        severity=severity if severity is not None else meta.severity,
        category=meta.category,
        chapter=chapter,
        file=file,
        line=line,
        span=span,
        rule_id=rule_id,
        message=message,
        suggested_fix_type=meta.suggested_fix_type,
        fingerprint=compute_fingerprint(rule_id, file, line, span),
    )


@dataclass(frozen=True, init=False)
class ChapterFiles:
    slug: str
    label: str
    folder: Path
    draft: Path
    scene_breakdown: Path
    drafting_plan: Path
    continuity_out: Path
    chapter_review: Path

    def __init__(
        self,
        slug: str | Path,
        label: str | None = None,
        folder: Path | None = None,
        draft: Path | None = None,
        scene_breakdown: Path | None = None,
        drafting_plan: Path | None = None,
        continuity_out: Path | None = None,
        chapter_review: Path | None = None,
    ):
        if isinstance(slug, Path) and label is None and folder is None:
            folder = slug
            slug_value = folder.name
        else:
            slug_value = str(slug)
            folder = folder or Path(slug_value)

        if label is None:
            if slug_value == "epilogue":
                label = "Epilogue"
            else:
                match = re.match(r"chapter-(\d+)", slug_value)
                label = f"Chapter {int(match.group(1)):02d}" if match else slug_value.replace("-", " ").title()

        fallback_folder = None
        if "changes" in folder.parts:
            parts = list(folder.parts)
            try:
                idx = parts.index("changes")
                parts[idx] = "chapters"
                fallback_folder = Path(*parts)
            except ValueError:
                pass

        if draft is None:
            draft_options = ["draft.md", f"{slug_value}.md", "epilogue.md" if slug_value == "epilogue" else f"{slug_value}.md"]
            draft = folder / draft_options[0]
            found = False
            for opt in draft_options:
                p = folder / opt
                if p.exists():
                    draft = p
                    found = True
                    break
            if not found and fallback_folder:
                for opt in draft_options:
                    p = fallback_folder / opt
                    if p.exists():
                        draft = p
                        break

        if scene_breakdown is None:
            proposal_path = folder / "proposal.md"
            scene_bd_path = folder / "scene-breakdown.md"
            if proposal_path.exists():
                scene_breakdown = proposal_path
            elif scene_bd_path.exists():
                scene_breakdown = scene_bd_path
            elif fallback_folder:
                fallback_proposal = fallback_folder / "proposal.md"
                fallback_scene_bd = fallback_folder / "scene-breakdown.md"
                scene_breakdown = fallback_proposal if fallback_proposal.exists() else fallback_scene_bd
            else:
                scene_breakdown = proposal_path

        if drafting_plan is None:
            beats_path = folder / "beats.md"
            drafting_plan_path = folder / "drafting-plan.md"
            if beats_path.exists():
                drafting_plan = beats_path
            elif drafting_plan_path.exists():
                drafting_plan = drafting_plan_path
            elif fallback_folder:
                fallback_beats = fallback_folder / "beats.md"
                fallback_drafting_plan = fallback_folder / "drafting-plan.md"
                drafting_plan = fallback_beats if fallback_beats.exists() else fallback_drafting_plan
            else:
                drafting_plan = beats_path

        if continuity_out is None:
            continuity_out_path = folder / "continuity-out.md"
            if continuity_out_path.exists():
                continuity_out = continuity_out_path
            elif fallback_folder:
                fallback_continuity = fallback_folder / "continuity-out.md"
                continuity_out = fallback_continuity if fallback_continuity.exists() else continuity_out_path
            else:
                continuity_out = continuity_out_path

        if chapter_review is None:
            chapter_review_path = folder / "chapter-review.md"
            if chapter_review_path.exists():
                chapter_review = chapter_review_path
            elif fallback_folder:
                fallback_review = fallback_folder / "chapter-review.md"
                chapter_review = fallback_review if fallback_review.exists() else chapter_review_path
            else:
                chapter_review = chapter_review_path

        object.__setattr__(self, "slug", slug_value)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "folder", folder)
        object.__setattr__(self, "draft", draft)
        object.__setattr__(self, "scene_breakdown", scene_breakdown)
        object.__setattr__(self, "drafting_plan", drafting_plan)
        object.__setattr__(self, "continuity_out", continuity_out)
        object.__setattr__(self, "chapter_review", chapter_review)


@dataclass
class ChapterReport:
    chapter: ChapterFiles
    passes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.failures:
            return "FAIL"
        if self.warnings:
            return "WARN"
        return "PASS"


@dataclass(frozen=True)
class BeatMetadata:
    label: str
    weight: str | None
    development_floor: int | None
    why_this_matters: str | None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_project_root(start: Path | None = None) -> Path:
    """Find the nearest project root that can own settings.json."""
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (
            (candidate / "settings.json").exists()
            or (candidate / "pyproject.toml").exists()
            or (candidate / "AGENTS.md").exists()
        ):
            return candidate
    return Path.cwd().resolve()


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _read_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _deep_merge_settings(defaults: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, value in defaults.items():
        if isinstance(value, dict):
            override_value = override.get(key, {})
            merged[key] = _deep_merge_settings(value, override_value if isinstance(override_value, dict) else {})
        else:
            merged[key] = override.get(key, value)
    for key, value in override.items():
        if key not in merged:
            merged[key] = value
    return merged


def load_project_settings(start: Path | None = None) -> dict[str, Any]:
    """Load root settings.json, falling back to safe defaults."""
    settings_path = find_project_root(start) / "settings.json"
    if not settings_path.exists():
        return _deep_merge_settings(DEFAULT_SETTINGS, {})
    try:
        loaded = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid settings.json: {settings_path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise RuntimeError(f"Invalid settings.json: {settings_path}: root value must be an object")
    return _deep_merge_settings(DEFAULT_SETTINGS, loaded)


_TIME_PERIOD_FIELD_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:\*{0,2})?"
    r"(time period|era|period)"
    r"(?:\*{0,2})?\s*[:/\-]?\s*(.+)$"
)
_YEAR_RE = re.compile(r"\b(?:19[0-9]{2}|18[0-9]{2})\b")
_DECADE_RE = re.compile(r"\b((?:18|19)\d)0s\b", re.IGNORECASE)


def _extract_time_period_text(rulebook_text: str) -> str:
    try:
        match = re.search(r"\*\*(Time Period|Era|Period)[:/]?\*\*\s*(.+)", rulebook_text, re.IGNORECASE)
        if match:
            return match.group(2).split("\n")[0].strip()
    except Exception:
        pass

    for line in rulebook_text.splitlines():
        match = _TIME_PERIOD_FIELD_RE.match(line)
        if match:
            return match.group(2).split("\n")[0].strip()
    return ""


def _extract_year_from_text(value: str) -> int | None:
    if not value:
        return None
    normalized = value.strip()
    match = _YEAR_RE.search(normalized)
    if match:
        return _read_int(match.group(0))
    decade_match = _DECADE_RE.search(normalized)
    if decade_match:
        return _read_int(f"{decade_match.group(1)}0")
    return None


def _extract_book_year_from_rulebook(rulebook_text: str) -> int | None:
    return _extract_year_from_text(_extract_time_period_text(rulebook_text))


def _extract_book_year_from_source_text(source_text: str) -> int | None:
    match = re.search(r"(?i)Period:\s*.*?(\d{4})", source_text)
    if match:
        year = _read_int(match.group(1))
        if year is not None:
            return year
    return _extract_year_from_text(source_text)


def _extract_book_year_from_book_folder(project_root: Path) -> int | None:
    try:
        rulebook_path = project_root / "rulebook.md"
        if rulebook_path.exists():
            rulebook_text = rulebook_path.read_text(encoding="utf-8")
            year = _extract_book_year_from_rulebook(rulebook_text)
            if year is not None:
                return year
    except OSError:
        pass

    try:
        from bookforge.core.scanner import source_path

        source = source_path(project_root)
        if source and source.exists():
            source_text = source.read_text(encoding="utf-8")
            year = _extract_book_year_from_source_text(source_text)
            if year is not None:
                return year
    except Exception:
        pass

    return None


def resolve_style_profile(
    settings_start: Path | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Resolve era profile + merged style/historical/voice settings."""
    settings = load_project_settings(settings_start)
    project_root = find_project_root(settings_start)

    style_profiles = _as_dict(settings.get("style_profiles"))
    year_buckets = style_profiles.get("year_buckets")
    if not isinstance(year_buckets, list):
        year_buckets = []
    profiles = _as_dict(style_profiles.get("profiles"))
    fallback_profile = "default"
    configured_fallback = style_profiles.get("fallback_profile")
    if isinstance(configured_fallback, str) and configured_fallback.strip():
        fallback_profile = configured_fallback.strip()
    if fallback_profile not in profiles:
        fallback_profile = "default"

    book_year = _extract_book_year_from_book_folder(project_root)
    profile_name = fallback_profile
    if isinstance(book_year, int):
        for bucket in year_buckets:
            if not isinstance(bucket, dict):
                continue
            name = bucket.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            start = _read_int(bucket.get("start"))
            end = _read_int(bucket.get("end"))
            if start is None:
                continue
            if end is None:
                end = start
            if start > end:
                start, end = end, start
            if start <= book_year <= end:
                profile_name = name.strip()
                break

    if profile_name not in profiles:
        profile_name = "default"

    base_style = _as_dict(settings.get("style_review"))
    base_historical = _as_dict(settings.get("historical_terms"))
    profile_settings = _as_dict(profiles.get(profile_name))
    resolved_style_review = _deep_merge_settings(base_style, _as_dict(profile_settings.get("style_review")))
    resolved_historical_terms = _deep_merge_settings(base_historical, _as_dict(profile_settings.get("historical_terms")))
    voice_settings = _as_dict(profile_settings.get("voice"))

    return profile_name, resolved_style_review, resolved_historical_terms, voice_settings


def contains_any(text: str, words: list[str], case_sensitive: bool = False) -> list[str]:
    found = []
    text_to_search = text if case_sensitive else text.lower()
    for word in words:
        term = word if case_sensitive else word.lower()
        if term in text_to_search:
            found.append(word)
    return sorted(found)


def key_terms(text: str) -> set[str]:
    text_clean = re.sub(r"[^A-Za-z0-9\s-]", "", text)
    terms = set()
    for word in text_clean.split():
        word_lower = word.lower()
        if (
            len(word_lower) > 3
            and word_lower not in STOPWORDS
            and not word_lower.startswith("chapter-")
        ):
            terms.add(word_lower)
    return terms


def coverage(source_text: str, target_text: str) -> tuple[float, list[str]]:
    source_words = key_terms(source_text)
    target_words = key_terms(target_text)
    if not source_words:
        return 1.0, []
    matches = source_words.intersection(target_words)
    missing = sorted(list(source_words.difference(target_words)))
    return len(matches) / len(source_words), missing


def chapter_sort_key(path: Path) -> tuple[int, str]:
    if path.name == "epilogue":
        return 999, path.name
    match = re.search(r"chapter-(\d+)", path.name)
    if match:
        return int(match.group(1)), path.name
    return 998, path.name


def discover_chapters(book_folder: Path) -> list[ChapterFiles]:
    slugs = set()
    changes_dir = book_folder / "changes"
    if changes_dir.exists():
        for path in changes_dir.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                slugs.add(path.name)

    chapters_dir = book_folder / "chapters"
    if chapters_dir.exists():
        for path in chapters_dir.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                slugs.add(path.name)

    chapters = []
    for slug in sorted(slugs, key=lambda s: chapter_sort_key(Path(s))):
        changes_path = changes_dir / slug
        chapters_path = chapters_dir / slug
        if changes_path.exists():
            chapters.append(ChapterFiles(changes_path))
        else:
            chapters.append(ChapterFiles(chapters_path))
    return chapters


def parse_phase_chapters(book_folder: Path) -> dict[str, str]:
    from bookforge.core.scanner import source_path
    phase_path = source_path(book_folder)
    if not phase_path:
        raise RuntimeError("Missing outlining source.")
    text = read_text(phase_path)
    matches = list(PHASE_CHAPTER_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1)
        start = match.end()
        next_chapter_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        next_heading = re.search(r"^##\s+", text[start:next_chapter_start], re.MULTILINE)
        end = start + next_heading.start() if next_heading else next_chapter_start
        body = text[start:end].strip()
        if heading.lower().startswith("epilogue"):
            slug = "epilogue"
        else:
            number = int(match.group(2))
            slug = f"chapter-{number:02d}"
        sections[slug] = body
    return sections


def extract_scene_fields(scene_text: str) -> list[str]:
    fields: list[str] = []
    for match in FIELD_RE.finditer(scene_text):
        field = match.group(2).strip()
        field = EXIT_HOOK_PREFIX_RE.sub("", field).strip()
        if field:
            fields.append(field)
    return fields


def check_ing_openers(text: str) -> list[str]:
    samples: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"([A-Z][A-Za-z]{2,}ing)\b[\s,]", stripped)
        if match and match.group(1).lower() not in ING_OPENER_EXCLUSIONS:
            samples.append(stripped[:100])
            if len(samples) >= 5:
                break
    return samples


def extract_proper_names(text: str, word_limit: int = 200) -> set[str]:
    words = text.split()[:word_limit]
    names: set[str] = set()
    for word in words:
        clean = re.sub(r"[^A-Za-z]", "", word)
        if clean and clean[0].isupper() and len(clean) > 3 and clean.lower() not in STOPWORDS:
            names.add(clean.lower())
    return names


def check_pronoun_loops(text: str) -> list[str]:
    sentences = SENTENCE_SPLIT_RE.split(text)
    proper_names = extract_proper_names(text)
    watch_tokens = PRONOUN_FIXED | proper_names
    findings: list[str] = []
    run_token: str | None = None
    run_count = 0
    for sentence in sentences:
        stripped = sentence.strip()
        if not stripped:
            run_token = None
            run_count = 0
            continue
        first_word_match = re.match(r"([A-Za-z]+)", stripped)
        if not first_word_match:
            run_token = None
            run_count = 0
            continue
        token = first_word_match.group(1).lower()
        if token not in watch_tokens:
            run_token = None
            run_count = 0
            continue
        if token == run_token:
            run_count += 1
        else:
            run_token = token
            run_count = 1
        if run_count == PRONOUN_LOOP_MIN_RUN:
            findings.append(
                f"{run_count}+ consecutive sentences starting with '{first_word_match.group(1)}'"
            )
    return findings


def dialogue_tags(text: str) -> list[str]:
    found: set[str] = set()
    for match in DIALOGUE_TAG_RE.finditer(text):
        tag = match.group(1) or match.group(2)
        if tag:
            found.add(tag.lower())
    return sorted(found)


def check_em_dash_anchors(text: str) -> list[str]:
    warnings: list[str] = []
    for line_num, line in enumerate(text.splitlines(), 1):
        if '"' in line:
            # Check for double/triple hyphens: -- or ---
            if '--' in line:
                warnings.append(f"Line {line_num}: Use em-dash `—` instead of double-hyphen `--`")
                continue
            for match in re.finditer(r'"[^"]*"\s*—\s*\S?', line):
                if not re.search(r'"[^"]*"\s—\s\S', match.group(0)):
                    warnings.append(
                        f"Line {line_num}: Incorrect em-dash anchor spacing. Use `\"Dialogue.\" — Action`."
                    )
    return warnings


def forbidden_length_language(text: str) -> list[str]:
    findings: list[str] = []
    patterns = {
        "word count": r"\bword counts?\b",
        "quota": r"\bquotas?\b",
        "target": r"\b(?:target|minimum|maximum)\s+(?:word|words|length)\b",
        "fixed words": r"\b\d[\d,]*\s+words?\b",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(label)
    return findings


def _configured_banned_name_patterns(settings: dict[str, Any]) -> dict[str, str]:
    name_policy = settings.get("name_policy", {})
    banned_names = name_policy.get("banned_names", [])
    allowed_names = name_policy.get("allowed_names", [])
    if not isinstance(banned_names, list):
        banned_names = []
    if not isinstance(allowed_names, list):
        allowed_names = []

    allowed = {str(name).strip().lower() for name in allowed_names if str(name).strip()}
    patterns: dict[str, str] = {}
    for raw_name in banned_names:
        name = str(raw_name).strip().lower()
        if not name:
            continue
        if name in allowed and name not in PROJECT_RULE_BANNED_NAME_LABELS:
            continue
        patterns[name] = rf"\b{re.escape(name)}\b"
    return patterns


def check_forbidden_conflicts(text: str, settings_start: Path | None = None) -> list[str]:
    findings: list[str] = []
    text_lower = text.lower()
    settings = load_project_settings(settings_start)

    patterns = {
        **FORBIDDEN_CONFLICT_PATTERNS,
        **_configured_banned_name_patterns(settings),
    }

    for label, pattern in patterns.items():
        if re.search(pattern, text_lower):
            if label == "voss":
                findings.append("Banned character/setting name 'voss' found.")
            elif label in _configured_banned_name_patterns(settings):
                findings.append(f"Configured banned name '{label}' found.")
            else:
                findings.append(f"Forbidden conflict theme/term '{label}' found in draft.")
    return findings


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _normalize_sentence(sentence: str) -> str:
    words = re.findall(r"\b[A-Za-z']+\b", sentence.lower())
    return " ".join(words)


def check_repeated_sentence_duplicates(text: str) -> list[str]:
    """Find likely copy-paste sentence duplicates without flagging tiny refrains."""
    findings: list[str] = []
    seen: dict[str, str] = {}
    for sentence in SENTENCE_SPLIT_RE.split(text.strip()):
        clean = sentence.strip()
        normalized = _normalize_sentence(clean)
        if len(normalized.split()) < 5:
            continue
        if normalized in seen:
            findings.append(f"Repeated sentence likely copy-paste: {seen[normalized][:120]}")
            if len(findings) >= 5:
                break
            continue
        seen[normalized] = clean
    return findings


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _term_hits(text_lower: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for term in terms:
        pattern = rf"\b{re.escape(term)}\b" if re.search(r"\w", term) else re.escape(term)
        if re.search(pattern, text_lower):
            hits.append(term)
    return sorted(set(hits))


def check_plot_mode_risk(text: str, book_folder: Path | None = None) -> list[str]:
    """Warn when a banned plot mode appears to dominate the draft."""
    settings = load_project_settings(book_folder)
    review_settings = settings.get("plot_mode_review", {})
    if not isinstance(review_settings, dict) or not review_settings.get("enabled", True):
        return []

    if book_folder is None:
        return []
    rulebook_path = Path(book_folder) / "rulebook.md"
    if not rulebook_path.exists():
        return []

    rulebook_text = rulebook_path.read_text(encoding="utf-8").lower()
    ban_markers = _as_string_list(review_settings.get("ban_markers"))
    if not any(marker in rulebook_text for marker in ban_markers):
        return []

    terms = _as_string_list(review_settings.get("legal_procedure_terms"))
    text_lower = text.lower()
    hits = _term_hits(text_lower, terms)
    threshold = review_settings.get("legal_procedure_threshold", 6)
    if not isinstance(threshold, int) or threshold < 1:
        threshold = 6
    if len(hits) < threshold:
        return []

    return [
        "Draft appears to lean into legal-procedure plot mode despite rulebook guardrails; "
        f"review before rewriting. Terms: {', '.join(hits[:10])}."
    ]


def check_similes_and_metaphors(text: str) -> list[str]:
    narrative = re.sub(r'"[^"]*"', "", text)
    sentences = SENTENCE_SPLIT_RE.split(narrative)
    simile_pat = re.compile(
        r"\b(as\s+if|as\s+though|like\s+(?:a|an|the|my|his|her|its|our|their|your|some|any|wet|old|dry|cold|hot|dark|bright|thin|thick|sharp|hard|soft|wild|dead|living|slow|fast|heavy|light|\w+))\b",
        re.IGNORECASE,
    )
    non_similes = {
        "like to", "like it", "like this", "like that", "like these", "like those",
        "like so", "like me", "like us", "like you", "like him", "like her", "like them",
        "would like", "should like", "could like", "does like", "did like", "do like",
        "nothing like", "anything like", "something like", "not like to", "don't like",
        "feel like", "feels like", "felt like", "seemed like", "seems like", "seem like",
        "look like", "looks like", "looked like",
    }

    findings: list[str] = []
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        for match in simile_pat.finditer(sentence_clean):
            matched_str = match.group(1).lower()
            is_non_simile = False
            if matched_str.startswith("like"):
                like_start = match.start()
                sentence_lower = sentence_clean.lower()
                pre_text = sentence_lower[:like_start + 4]
                for non_simile in non_similes:
                    if non_simile.endswith("like") and pre_text.endswith(non_simile):
                        is_non_simile = True
                        break
                if not is_non_simile:
                    post_text = sentence_lower[like_start:]
                    for non_simile in non_similes:
                        if non_simile.startswith("like") and post_text.startswith(non_simile):
                            next_char_idx = len(non_simile)
                            if next_char_idx >= len(post_text) or not post_text[next_char_idx].isalnum():
                                is_non_simile = True
                                break
            if not is_non_simile:
                snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
                findings.append(f"Simile/Metaphor detected in narrative: '{snippet}' (found '{match.group(1)}')")
                break
    return findings


def check_personification_of_objects(text: str) -> list[str]:
    narrative = re.sub(r'"[^"]*"', "", text)
    sentences = SENTENCE_SPLIT_RE.split(narrative)
    inanimate_nouns = (
        r"land|wind|dust|night|sun|sky|shadow|shadows|darkness|fire|smoke|stone|rock|paper|wood|wagon|wheel|carriage|train|"
        r"saddle|scabbard|bullet|lead|iron|steel|leather|rope|water|river|creek|mud|snow|trail|road|arroyo|valley|ridge|cliff|"
        r"mountain|hill|slope|wonder|fear|pain|silence|danger|memory|memories|thought|time|hour|hours|minute|minutes|day|"
        r"days|week|weeks|season|seasons|year|years|truth|lie|lies|voice|sound|word|words|name|names|blood|bloodstain|heat|"
        r"cold|winter|summer|spring|autumn|fall|weather|colt|rifle|gun|revolver|pistol|carbine|winchester|"
        r"habit|name|paper|room|door|window|fence|gate|wall|floor|ground|dirt|clay|sand|grass|brush|mesquite|cedar|pine|"
        r"oak|elm|cottonwood|sky|cloud|storm|rain|frost|ice|wind|breeze|gust|heat|cold|chill|warmth|"
        r"distance|miles|mile|league|day|night|dawn|dusk|twilight|sunrise|sunset|moon|stars|constellation"
    )
    agency_verbs = (
        r"speak|speaks|spoke|speaking|talk|talks|talked|talking|whisper|whispers|whispered|whispering|tell|tells|told|telling|"
        r"say|says|said|saying|want|wants|wanted|wanting|wish|wishes|wished|wishing|hope|hopes|hoped|hoping|know|knows|knew|"
        r"knowing|think|thinks|thought|thinking|believe|believes|believed|believing|wonder|wonders|wondered|wondering|waste|"
        r"wastes|wasted|wasting|watch|watches|watched|watching|creep|creeps|crept|creeping|breathe|breathes|breathed|breathing|"
        r"listen|listens|listened|listening|stare|stares|stared|staring|gaze|gazes|gazed|gazing|move|moves|moved|moving|stretch|"
        r"stretches|stretched|stretching|chase|chases|chased|chasing|put|puts|putting|hold|holds|held|holding|reach|reaches|reached|reaching|"
        r"cry|cries|cried|crying|laugh|laughs|laughed|laughing|weep|weeps|wept|weeping|call|calls|called|calling|scream|screams|screamed|screaming|"
        r"bite|bites|bit|biting|scratch|scratches|scratched|scratching|fight|fights|fought|fighting|kill|kills|killed|killing|"
        r"run|runs|ran|running|walk|walks|walked|walking|climb|climbs|climbed|climbing|wait|waits|waited|waiting|sleep|sleeps|slept|sleeping|dream|dreams|dreamed|dreaming"
    )
    personification_pat = re.compile(
        rf"\b({inanimate_nouns})\b(?:\s+(?:did\s+not|had|was|were|could|would|should|will|can|might)\b)?(?:\s+[a-z]+ly\b)?\s+\b({agency_verbs})\b",
        re.IGNORECASE,
    )
    metaphor_pat = re.compile(
        rf"\b(colt|rifle|gun|revolver|pistol|carbine|winchester)\b(?:\s+(?:was|were|is|are)\b)?\s+(?:a|an)\s+\b(curse|warning|blessing|promise|threat|enemy|friend|companion|partner)\b",
        re.IGNORECASE,
    )

    findings: list[str] = []
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        match = personification_pat.search(sentence_clean)
        if match:
            snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
            findings.append(
                f"Personification of inanimate object/concept '{match.group(1)}' with action '{match.group(2)}': '{snippet}'"
            )
            continue
        metaphor_match = metaphor_pat.search(sentence_clean)
        if metaphor_match:
            snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
            findings.append(
                f"Metaphorical/figurative description of weapon '{metaphor_match.group(1)}' as '{metaphor_match.group(2)}': '{snippet}'"
            )
    return findings


def check_abstract_internalization(text: str) -> list[str]:
    narrative = re.sub(r'"[^"]*"', "", text)
    sentences = SENTENCE_SPLIT_RE.split(narrative)
    subjects = r"he|she|they|jed|branton|harlan|tex|creed|lask|eleanor"
    internal_verbs = (
        r"knew|known|know|believed|believe|wondered|wonder|resolved|resolve|decided|decide|"
        r"expected|expect|doubted|doubt|suspected|suspect|predicted|predict|"
        r"sensed|sense|remembered|remember|forgot|forgotten|forget|wished|wish|hoped|hope|"
        r"recalled|recall|imagined|imagine|feared|fear"
    )
    internal_pat = re.compile(
        rf"\b({subjects})\b"
        rf"(?:\s+(?:had|was|were|did|could|would|should|will|can|might)\b)?"
        rf"(?:\s+(?:not|never)\b)?"
        rf"(?:\s+[a-z]+ly\b)?"
        rf"\s+\b({internal_verbs})\b",
        re.IGNORECASE,
    )

    findings: list[str] = []
    for sentence in sentences:
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        match = internal_pat.search(sentence_clean)
        if match:
            snippet = sentence_clean[:80] + "..." if len(sentence_clean) > 80 else sentence_clean
            findings.append(
                f"Abstract internalization / thought-summary detected for '{match.group(1)}' with '{match.group(2)}': '{snippet}'"
            )
    return findings


def _strip_dialogue(text: str) -> str:
    return re.sub(r'"[^"]*"', "", text)


def check_thought_over_behavior_narration(
    text: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    """Flag narrator-summary lines that explain meaning after behavior."""
    review_config = _as_dict(config)
    if not review_config.get("enabled", True):
        return []

    max_findings = _read_int(review_config.get("max_findings"))
    if max_findings is None or max_findings < 1:
        max_findings = 8

    phrases = _as_string_list(review_config.get("phrases")) or _as_string_list(
        DEFAULT_SETTINGS["style_review"]["thought_over_behavior"]["phrases"]
    )
    meaning_markers = _as_string_list(review_config.get("meaning_markers")) or _as_string_list(
        DEFAULT_SETTINGS["style_review"]["thought_over_behavior"]["meaning_markers"]
    )
    abstract_labels = _as_string_list(review_config.get("abstract_labels")) or _as_string_list(
        DEFAULT_SETTINGS["style_review"]["thought_over_behavior"]["abstract_labels"]
    )
    explanation_shapes = _as_string_list(review_config.get("explanation_shapes")) or _as_string_list(
        DEFAULT_SETTINGS["style_review"]["thought_over_behavior"]["explanation_shapes"]
    )

    def has_configured_hit(sentence_lower: str, terms: list[str]) -> bool:
        for term in terms:
            pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
            if re.search(pattern, sentence_lower):
                return True
        return False

    def is_summary_shape(sentence_lower: str, word_count: int) -> bool:
        if word_count > 24:
            return False
        has_marker = has_configured_hit(sentence_lower, meaning_markers)
        has_label = has_configured_hit(sentence_lower, abstract_labels)
        if has_configured_hit(sentence_lower, explanation_shapes):
            return True
        if has_marker and has_label:
            return True
        if has_marker and re.match(r"(?:that|this|it|none|everything|anything)\b", sentence_lower):
            return True
        if has_marker and re.search(r"\b(?:after that|because of it|around him|around her|around them)\b", sentence_lower):
            return True
        if has_label and re.search(r"\b(?:came|went|held|stayed|grew|became|made)\b", sentence_lower):
            return True
        return False

    findings: list[str] = []
    narrative = _strip_dialogue(text)
    for sentence in SENTENCE_SPLIT_RE.split(narrative):
        excerpt = " ".join(sentence.strip().split())
        if not excerpt:
            continue
        excerpt_lower = excerpt.lower()
        word_count = len(re.findall(r"\b[A-Za-z']+\b", excerpt))
        if has_configured_hit(excerpt_lower, phrases) or is_summary_shape(excerpt_lower, word_count):
            findings.append(
                "Thought-over-behavior narration: line explains meaning/status after behavior; "
                f"consider replacing with action, silence, work, or direct speech: '{excerpt[:120]}'"
            )
        if len(findings) >= max_findings:
            break

    return findings


def check_style_review_signals(text: str, settings_start: Path | None = None) -> list[str]:
    try:
        _, style_settings, historical_terms, _ = resolve_style_profile(settings_start)
    except Exception:
        settings = load_project_settings(settings_start)
        style_settings = settings.get("style_review", {})
        historical_terms = _as_dict(settings.get("historical_terms"))

    style_settings = _as_dict(style_settings)
    if not isinstance(style_settings, dict) or not style_settings.get("enabled", True):
        return []
    if not isinstance(historical_terms, dict):
        historical_terms = {}
    historical_terms = _as_dict(historical_terms)

    findings: list[str] = []
    max_summary_words = style_settings.get("max_summary_words_without_dialogue", 120)
    if not isinstance(max_summary_words, int) or max_summary_words < 1:
        max_summary_words = 120

    for paragraph in re.split(r"\n\s*\n", text.strip()):
        words = re.findall(r"\b[A-Za-z']+\b", paragraph)
        if len(words) >= max_summary_words and '"' not in paragraph:
            findings.append(
                f"Long narrative-summary stretch without dialogue ({len(words)} words); review whether an active exchange or physical beat is needed."
            )
            break

    text_lower = text.lower()
    analysis_terms = [term for term in _as_string_list(style_settings.get("analysis_terms")) if re.search(rf"\b{re.escape(term)}\b", text_lower)]
    if analysis_terms:
        findings.append(
            "Behavior-analysis language appears in draft; review for action/dialogue replacement: "
            + ", ".join(sorted(set(analysis_terms))[:8])
            + "."
        )

    formal_terms = _as_string_list(style_settings.get("formal_dialogue_terms"))
    dialogue_segments = re.findall(r'"([^"]+)"', text)
    formal_hits: set[str] = set()
    for segment in dialogue_segments:
        segment_lower = segment.lower()
        for term in formal_terms:
            if re.search(rf"\b{re.escape(term)}\b", segment_lower):
                formal_hits.add(term)
    if formal_hits:
        findings.append(
            "Formal dialogue terms appear inside quoted speech; review for rugged Western phrasing: "
            + ", ".join(sorted(formal_hits)[:8])
            + "."
        )

    time_jump_terms = [term for term in _as_string_list(style_settings.get("time_jump_terms")) if term in text_lower]
    if time_jump_terms:
        findings.append(
            "Abrupt time-jump wording appears; review whether the transition needs trail labor, scouting, camp movement, or consequence: "
            + ", ".join(sorted(set(time_jump_terms))[:8])
            + "."
        )

    banned_terms = [term for term in _as_string_list(style_settings.get("banned_terms")) if re.search(rf"\b{re.escape(term)}\b", text_lower)]
    if banned_terms:
        findings.append(
            "Forbidden modern or legalese/clinical terms appear in draft; replace with period-accurate phrasing: "
            + ", ".join(sorted(set(banned_terms))[:8])
            + "."
        )

    findings.extend(
        check_thought_over_behavior_narration(
            text,
            _as_dict(style_settings.get("thought_over_behavior")),
        )
    )

    severity_labels = (
        ("banned", "Banned historical/style terms"),
        ("warn", "Warn historical/style terms"),
        ("context_required", "Context-required historical/style terms"),
        ("review_only", "Review-only historical/style terms"),
    )
    for key, label in severity_labels:
        hits = _term_hits(text_lower, _as_string_list(historical_terms.get(key)))
        if hits:
            findings.append(f"{label} found; verify timeline and genre fit: {', '.join(hits[:8])}.")

    if style_settings.get("warn_short_sentence_runs", False):
        sentences = SENTENCE_SPLIT_RE.split(text)
        short_run = 0
        short_sentences_detected = []
        for sentence in sentences:
            clean_sentence = sentence.strip()
            if not clean_sentence:
                continue
            words = re.findall(r"\b[A-Za-z']+\b", clean_sentence)
            if len(words) > 0 and len(words) < 5:
                short_run += 1
                if short_run >= 3:
                    short_sentences_detected.append(clean_sentence)
            else:
                short_run = 0

        if short_sentences_detected:
            findings.append(
                "Consecutive short sentence fragments detected (rhythm feels too modern/clipped); review and combine for classic cadence: "
                + "; ".join(short_sentences_detected[:3])
                + "..."
            )

    return findings


def check_unprofiled_period_terms(text: str, book_folder: Path) -> list[str]:
    warnings: list[str] = []
    from bookforge.core.research import get_research_pack_path
    research_file = get_research_pack_path(book_folder)
    research_content = ""
    if research_file.exists():
        research_content = research_file.read_text(encoding="utf-8").lower()
        
    watchwords = [
        "winchester", "sharps", "colt", "peacemaker", "remington", "derringer", 
        "stagecoach", "locomotive", "telegraph", "carbolic", "laudanum", "morphia"
    ]
    
    draft_words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    
    for word in watchwords:
        if word in draft_words:
            if word not in research_content:
                warnings.append(
                    f"Draft mentions period term '{word}' which is not documented in research-pack.md. "
                    f"Please add it to the research pack to verify historical accuracy."
                )
    return warnings


def check_context_lock_unknowns(scene_text: str) -> list[str]:
    findings: list[str] = []
    in_lock = False
    for line in scene_text.splitlines():
        if CONTEXT_LOCK_MARKER in line:
            in_lock = True
            continue
        if in_lock and line.strip().startswith(CONTEXT_LOCK_END_MARKER):
            in_lock = False
            continue
        if in_lock:
            for marker in UNRESOLVED_MARKERS:
                if marker in line:
                    field_match = re.match(r"\s*-\s*\*\*(.+?):\*\*", line)
                    field_name = field_match.group(1) if field_match else "context field"
                    findings.append(f"`{field_name}` contains `{marker}`")
                    break
    return findings


def normalize_heading_name(heading: str) -> str:
    return re.sub(r"\s+", " ", heading.strip().lower())


def _extract_rulebook_section(text: str, section_aliases: tuple[str, ...]) -> str:
    headings = list(RULEBOOK_SECTION_HEADING_RE.finditer(text))
    aliases = {normalize_heading_name(alias) for alias in section_aliases}
    for index, heading in enumerate(headings):
        title = heading.group(2).strip()
        if normalize_heading_name(title) not in aliases:
            continue
        level = len(heading.group(1))
        end = len(text)
        for next_heading in headings[index + 1 :]:
            if len(next_heading.group(1)) <= level:
                end = next_heading.start()
                break
        section_body_start = heading.end()
        return text[section_body_start:end].strip()
    return ""


def _extract_unknown_markers(text: str) -> list[str]:
    findings: list[str] = []
    current_section = ""
    for line in text.splitlines():
        heading_match = RULEBOOK_SECTION_HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            section_title = normalize_heading_name(heading_match.group(2))
            if level <= 2:
                current_section = section_title
            continue
        for marker in UNRESOLVED_MARKERS:
            if re.search(rf"\b{re.escape(marker)}\b", line):
                if current_section not in RULEBOOK_UNKNOWN_ALLOWED_SECTIONS:
                    findings.append(f"{marker} in `{current_section or 'Unknown section'}`")
                break
    return findings


def _chapter_slug_to_label(slug: str) -> str:
    if slug == "epilogue":
        return "epilogue"
    if slug.startswith("chapter-"):
        return f"chapter {int(slug.split('-')[1])}"
    return slug


def _ledger_has_chapter_entry(ledger_section: str, chapter_slug: str) -> bool:
    label = _chapter_slug_to_label(chapter_slug)
    if label == "epilogue":
        pattern = r"(?im)^#{1,6}\s*Epilogue\b.*$"
    else:
        match = re.match(r"chapter-(\d+)", chapter_slug)
        if not match:
            return False
        number = int(match.group(1))
        pattern = rf"(?im)^#{{1,6}}\s*Chapter\s+0*{number}\b.*$"
    return bool(re.search(pattern, ledger_section))


KILLED_PERSON_RE = re.compile(
    r"\b(?:one|a|the)\s+([a-z][a-z\s-]{2,60}?)\s+(?:is|was)\s+killed\b",
    re.IGNORECASE,
)


def _normalize_person_descriptor(value: str) -> str:
    descriptor = re.sub(r"\b(?:same|exact|badly|seriously|wounded|injured|dead)\b", "", value.lower())
    descriptor = re.sub(r"\s+", " ", descriptor).strip(" .,:;")
    return descriptor


def validate_outline_life_state_issues(book_folder: Path) -> tuple[ManuscriptIssue, ...]:
    """Catch obvious outline cases where the same described person dies then acts later."""
    from bookforge.core.scanner import source_path

    src = source_path(book_folder)
    if not src or not src.exists():
        return ()

    text = src.read_text(encoding="utf-8")
    text_lower = text.lower()
    issues: list[ManuscriptIssue] = []

    for match in KILLED_PERSON_RE.finditer(text_lower):
        descriptor = _normalize_person_descriptor(match.group(1))
        if len(descriptor.split()) < 2:
            continue
        later_text = text_lower[match.end():]
        escaped = re.escape(descriptor)
        later_patterns = [
            rf"\binjured\s+{escaped}\b",
            rf"\btreats?\s+(?:the\s+)?(?:injured\s+)?{escaped}\b",
            rf"\b{escaped}\b.{0,100}\b(?:names?|speaks?|confesses?|reveals?|testif(?:y|ies))\b",
        ]
        if any(re.search(pattern, later_text, re.DOTALL) for pattern in later_patterns):
            issues.append(_make_issue(
                "VALIDATOR_OUTLINE_LIFE_STATE_CONTRADICTION",
                f"Outline may treat the same described person as killed and later active: `{descriptor}`.",
                file=src,
                span=descriptor,
            ))
            break

    return tuple(issues)


def validate_continuity_out_issues(chapter: ChapterFiles) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    if not chapter.draft.exists():
        return tuple(issues)
    draft_text = chapter.draft.read_text(encoding="utf-8")
    if not draft_text.strip():
        return tuple(issues)
    continuity_path = chapter.continuity_out
    if not continuity_path.exists():
        issues.append(_make_issue(
            "VALIDATOR_MISSING_CONTINUITY_OUT",
            "`continuity-out.md` is missing. The next chapter context packet will lack reliable handoff data.",
            chapter=chapter.slug,
            file=continuity_path,
        ))
    elif not continuity_path.read_text(encoding="utf-8").strip():
        issues.append(_make_issue(
            "VALIDATOR_EMPTY_CONTINUITY_OUT",
            "`continuity-out.md` exists but is empty.",
            chapter=chapter.slug,
            file=continuity_path,
        ))
    return tuple(issues)


def validate_continuity_out(chapter: ChapterFiles) -> tuple[list[str], list[str]]:
    issues = validate_continuity_out_issues(chapter)
    passes: list[str] = []
    warnings: list[str] = [issue.message for issue in issues]
    if (
        chapter.draft.exists()
        and chapter.draft.read_text(encoding="utf-8").strip()
        and not warnings
    ):
        passes.append("`continuity-out.md` is present and non-empty.")
    return passes, warnings


def validate_required_book_file_issues(book_folder: Path) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []

    from bookforge.core.scanner import source_path
    src = source_path(book_folder)
    if not src or not src.read_text(encoding="utf-8").strip():
        issues.append(_make_issue(
            "VALIDATOR_MISSING_OUTLINE",
            "Missing or empty outline source file (e.g. phase-0.md or phase-0/*.md).",
            file=src,
        ))
    else:
        issues.extend(validate_outline_life_state_issues(book_folder))

    for relative_path in REQUIRED_BOOK_FILES:
        path = book_folder / relative_path
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            issues.append(_make_issue(
                "VALIDATOR_MISSING_BOOK_FILE",
                f"Missing or empty `{relative_path}`.",
                file=path,
            ))

    rulebook_path = book_folder / "rulebook.md"
    if rulebook_path.exists():
        rulebook_text = rulebook_path.read_text(encoding="utf-8")
        for section_name, aliases in REQUIRED_RULEBOOK_SECTIONS.items():
            section_text = _extract_rulebook_section(rulebook_text, aliases)
            if not section_text:
                issues.append(_make_issue(
                    "VALIDATOR_MISSING_RULEBOOK_SECTION",
                    f"Rulebook missing required section `{section_name}`.",
                    file=rulebook_path,
                ))
            elif not section_text.strip():
                issues.append(_make_issue(
                    "VALIDATOR_EMPTY_RULEBOOK_SECTION",
                    f"Rulebook required section `{section_name}` is empty.",
                    file=rulebook_path,
                ))

        unknown_issues = _extract_unknown_markers(rulebook_text)
        for issue in unknown_issues:
            issues.append(_make_issue(
                "VALIDATOR_UNKNOWNS_IN_RULEBOOK",
                f"Rulebook marker policy violation: {issue}.",
                file=rulebook_path,
            ))

        ledger_text = _extract_rulebook_section(
            rulebook_text, REQUIRED_RULEBOOK_SECTIONS["Chapter Continuity Ledger"]
        )
        if ledger_text:
            try:
                expected_chapters = list(parse_phase_chapters(book_folder).keys())
            except Exception:
                expected_chapters = []
            for chapter_slug in expected_chapters:
                if not _ledger_has_chapter_entry(ledger_text, chapter_slug):
                    issues.append(_make_issue(
                        "VALIDATOR_MISSING_CONTINUITY_LEDGER",
                        f"Rulebook `Chapter Continuity Ledger` is missing `{chapter_slug}` coverage.",
                        file=rulebook_path,
                    ))

    unknown_failures = unknowns_module.check_unknowns(book_folder)
    for failure in unknown_failures:
        issues.append(_make_issue(
            "VALIDATOR_UNRESOLVED_UNKNOWN",
            failure,
            file=rulebook_path,
        ))

    return tuple(issues)


def validate_required_book_files(book_folder: Path) -> tuple[list[str], list[str]]:
    issues = validate_required_book_file_issues(book_folder)
    passes: list[str] = []
    failures: list[str] = [issue.message for issue in issues]
    if not failures:
        passes.append("Required book files are present.")
    return passes, failures


def validate_scene_breakdown(chapter: ChapterFiles) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    if not chapter.scene_breakdown.exists():
        issues.append(_make_issue(
            "VALIDATOR_MISSING_SCENE_BREAKDOWN",
            f"Missing `{chapter.scene_breakdown}`.",
            chapter=chapter.slug,
            file=chapter.scene_breakdown,
        ))
        return tuple(issues)

    text = read_text(chapter.scene_breakdown)
    beats = BEAT_RE.findall(text)
    if not beats:
        issues.append(_make_issue(
            "VALIDATOR_NO_BEATS",
            "Scene breakdown has no `## BEAT` sections.",
            chapter=chapter.slug,
            file=chapter.scene_breakdown,
        ))
    for marker in BEAT_REQUIRED_MARKERS:
        count = text.count(marker)
        if count == 0:
            issues.append(_make_issue(
                "VALIDATOR_MISSING_BEAT_MARKER",
                f"Scene breakdown missing `{marker}`.",
                chapter=chapter.slug,
                file=chapter.scene_breakdown,
            ))
        elif beats and count < len(beats):
            issues.append(_make_issue(
                "VALIDATOR_MISSING_CONTEXT_LOCK",
                f"Scene breakdown has {len(beats)} beat(s) but only {count} `{marker}` marker(s).",
                chapter=chapter.slug,
                file=chapter.scene_breakdown,
            ))

    lock_unknowns = check_context_lock_unknowns(text)
    for finding in lock_unknowns:
        issues.append(_make_issue(
            "VALIDATOR_CONTEXT_LOCK_UNKNOWN",
            f"Context-lock field has unresolved marker: {finding}",
            chapter=chapter.slug,
            file=chapter.scene_breakdown,
        ))

    return tuple(issues)


def _read_chapter_review(chapter: ChapterFiles) -> tuple[str | None, str | None]:
    if not chapter.chapter_review.exists():
        return None, None

    text = read_text(chapter.chapter_review)
    match = re.search(r"(?ims)^##\s+Decision\s*(.+?)\s*(?=^##\s+|\Z)", text)
    if not match:
        return text, None
    decision = match.group(1).strip().splitlines()[0].strip().lower()
    return text, decision


def _beat_window(text: str, phrase: str) -> tuple[int, int] | None:
    phrase_terms = [term for term in key_terms(phrase) if len(term) > 3]
    if not phrase_terms:
        return None

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    for index, paragraph in enumerate(paragraphs):
        paragraph_terms = key_terms(paragraph)
        overlap = len(set(phrase_terms).intersection(paragraph_terms))
        if overlap >= max(1, min(2, len(phrase_terms))):
            start = max(0, index - 1)
            end = min(len(paragraphs), index + 2)
            window_text = "\n\n".join(paragraphs[start:end])
            return len(window_text.split()), overlap
    return None


def extract_beat_metadata(scene_text: str) -> list[BeatMetadata]:
    beats: list[BeatMetadata] = []
    matches = list(re.finditer(r"(?im)^##\s+BEAT\s+\d+\s*:\s*(.+?)\s*$", scene_text))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(scene_text)
        body = scene_text[start:end]
        label = match.group(1).strip()

        weight_match = re.search(r"(?im)^\s*-\s+\*\*Beat Weight:\*\*\s+(.+?)\s*$", body)
        floor_match = re.search(r"(?im)^\s*-\s+\*\*Beat Development Floor:\*\*\s+>=?\s*(\d+)\s*words?\s*$", body)
        why_match = re.search(r"(?im)^\s*-\s+\*\*Why This Beat Matters:\*\*\s+(.+?)\s*$", body)

        beats.append(
            BeatMetadata(
                label=label,
                weight=weight_match.group(1).strip().lower() if weight_match else None,
                development_floor=int(floor_match.group(1)) if floor_match else None,
                why_this_matters=why_match.group(1).strip() if why_match else None,
            )
        )
    return beats


def validate_chapter_pacing(chapter: ChapterFiles) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    if not chapter.draft.exists() or not chapter.draft.name.startswith(chapter.slug):
        return tuple(issues)

    review_text, decision = _read_chapter_review(chapter)
    if review_text is None:
        issues.append(_make_issue(
            "CHAPTER_REVIEW_MISSING",
            f"Compiled chapter is missing required `chapter-review.md` at `{chapter.chapter_review}`.",
            chapter=chapter.slug,
            file=chapter.chapter_review,
        ))
        return tuple(issues)

    if decision and decision != "ready":
        issues.append(_make_issue(
            "CHAPTER_REVIEW_NOT_READY",
            f"`chapter-review.md` decision is `{decision}`, so the compiled chapter is not ready.",
            chapter=chapter.slug,
            file=chapter.chapter_review,
        ))

    scene_text = read_text(chapter.scene_breakdown) if chapter.scene_breakdown.exists() else ""
    draft_text = read_text(chapter.draft)
    for beat in extract_beat_metadata(scene_text):
        phrase = beat.why_this_matters or beat.label
        window = _beat_window(draft_text, phrase)
        if window is None:
            issues.append(_make_issue(
                "BEAT_UNDERDEVELOPED",
                f"Beat `{beat.label}` is underdeveloped or missing from the compiled chapter.",
                chapter=chapter.slug,
                file=chapter.draft,
            ))
            continue
        window_words, _ = window
        if beat.development_floor and window_words < beat.development_floor:
            severity = Severity.HARD if beat.weight == "money" else Severity.SOFT
            issues.append(_make_issue(
                "BEAT_UNDERDEVELOPED",
                f"Beat `{beat.label}` is underdeveloped: found about {window_words} words near the beat, below floor {beat.development_floor}.",
                chapter=chapter.slug,
                file=chapter.draft,
                severity=severity,
            ))

    return tuple(issues)


def validate_draft(chapter: ChapterFiles) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    if not chapter.draft.exists():
        issues.append(_make_issue(
            "VALIDATOR_MISSING_DRAFT",
            f"Missing draft `{chapter.draft}`.",
            chapter=chapter.slug,
            file=chapter.draft,
        ))
        return tuple(issues)

    text = read_text(chapter.draft)
    if not text.strip():
        issues.append(_make_issue(
            "VALIDATOR_EMPTY_DRAFT",
            f"Draft `{chapter.draft}` is empty.",
            chapter=chapter.slug,
            file=chapter.draft,
        ))
        return tuple(issues)

    forbidden_length = forbidden_length_language(text)
    for item in forbidden_length:
        issues.append(_make_issue(
            "VALIDATOR_FORBIDDEN_LENGTH_LANGUAGE",
            f"Draft contains forbidden length language: {item}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=item,
        ))

    unresolved = contains_any(text, UNRESOLVED_MARKERS, case_sensitive=True)
    for marker in unresolved:
        issues.append(_make_issue(
            "VALIDATOR_UNRESOLVED_MARKER",
            f"Draft contains unresolved marker(s): {', '.join(unresolved)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=marker,
        ))

    forbidden_conflicts = check_forbidden_conflicts(text, chapter.draft)
    for finding in forbidden_conflicts:
        issues.append(_make_issue(
            "VALIDATOR_FORBIDDEN_CONFLICT",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    echo_words = contains_any(text, BANNED_AI_ECHO_WORDS)
    for word in echo_words:
        issues.append(_make_issue(
            "VALIDATOR_BANNED_ECHO_WORD",
            f"Draft contains banned AI echo word(s): {', '.join(echo_words)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=word,
        ))

    modern_words = contains_any(text, MODERN_OR_CLINICAL_WORDS)
    for word in modern_words:
        issues.append(_make_issue(
            "VALIDATOR_MODERN_WORD",
            f"Draft contains modern/clinical word(s): {', '.join(modern_words)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=word,
        ))

    HISTORICAL_DICTIONARY = {
        "flashlight": 1899,
        "telephone": 1876,
        "teletype": 1902,
        "automobile": 1897,
        "subway": 1897,
        "zipper": 1893,
        "airplane": 1903,
        "radio": 1895,
        "motel": 1925,
        "cinema": 1895,
        "computer": 1940,
        "plastic": 1907,
        "radar": 1935,
        "television": 1927,
        "camera": 1888,
        "dynamite": 1867,
        "barbed wire": 1874,
        "barbed-wire": 1874,
        "phonograph": 1877,
        "typewriter": 1868,
    }

    book_folder = chapter.folder.parent.parent
    book_year = _extract_book_year_from_book_folder(book_folder) or 1880

    text_lower = text.lower()
    for word, invention_year in HISTORICAL_DICTIONARY.items():
        if invention_year > book_year:
            if re.search(rf"\b{re.escape(word)}\b", text_lower):
                issues.append(_make_issue(
                    "VALIDATOR_ANACHRONISM",
                    f"Draft contains era-inconsistent word(s) for year {book_year}: '{word}' (invented in {invention_year}).",
                    chapter=chapter.slug,
                    file=chapter.draft,
                    span=word,
                ))

    internal_phrases = contains_any(text, INTERNAL_MONOLOGUE_PHRASES)
    for phrase in internal_phrases:
        issues.append(_make_issue(
            "VALIDATOR_INTERNAL_MONOLOGUE",
            f"Draft contains internal-monologue phrase(s): {', '.join(internal_phrases)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=phrase,
        ))

    figurative_findings = check_similes_and_metaphors(text)
    for finding in figurative_findings:
        issues.append(_make_issue(
            "VALIDATOR_STYLE_REVIEW_SIGNAL",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    personification_findings = check_personification_of_objects(text)
    for finding in personification_findings:
        issues.append(_make_issue(
            "VALIDATOR_STYLE_REVIEW_SIGNAL",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    abstract_internalization_findings = check_abstract_internalization(text)
    for finding in abstract_internalization_findings:
        issues.append(_make_issue(
            "VALIDATOR_STYLE_REVIEW_SIGNAL",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    found_dialogue_tags = dialogue_tags(text)
    for tag in found_dialogue_tags:
        issues.append(_make_issue(
            "VALIDATOR_UNWANTED_DIALOGUE_TAG",
            f"Draft may contain unwanted dialogue tag(s): {', '.join(found_dialogue_tags)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=tag,
        ))

    ing_samples = check_ing_openers(text)
    for sample in ing_samples[:3]:
        issues.append(_make_issue(
            "VALIDATOR_ING_OPENER",
            f"Draft contains -ing sentence opener(s): {' | '.join(ing_samples[:3])}",
            chapter=chapter.slug,
            file=chapter.draft,
            span=sample[:50] if sample else None,
        ))

    pronoun_loops = check_pronoun_loops(text)
    for loop in pronoun_loops:
        issues.append(_make_issue(
            "VALIDATOR_PRONOUN_LOOP",
            f"Draft contains pronoun/name sentence loop(s): {'; '.join(pronoun_loops)}",
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    em_dash_warnings = check_em_dash_anchors(text)
    for warning in em_dash_warnings:
        issues.append(_make_issue(
            "VALIDATOR_EM_DASH_ANCHOR",
            warning,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    period_warnings = check_unprofiled_period_terms(text, book_folder)
    for warning in period_warnings:
        issues.append(_make_issue(
            "VALIDATOR_UNPROFILED_PERIOD_TERM",
            warning,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    repeated_sentences = check_repeated_sentence_duplicates(text)
    for finding in repeated_sentences:
        issues.append(_make_issue(
            "VALIDATOR_REPEATED_PROSE",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    plot_mode_risks = check_plot_mode_risk(text, book_folder)
    for finding in plot_mode_risks:
        issues.append(_make_issue(
            "VALIDATOR_PLOT_MODE_RISK",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    review_signals = check_style_review_signals(text, chapter.draft)
    for signal in review_signals:
        issues.append(_make_issue(
            "VALIDATOR_STYLE_REVIEW_SIGNAL",
            signal,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    pov_character = ""
    if chapter.scene_breakdown.exists():
        try:
            sb_text = read_text(chapter.scene_breakdown)
            pov_match = re.search(r"(?i)^\s*[\-\*]\s*POV:\s*(\w+)", sb_text, re.MULTILINE)
            if pov_match:
                pov_character = pov_match.group(1).lower()
        except Exception:
            pass

    all_chars = []
    world_state_path = book_folder / "world-state.json"
    if world_state_path.exists():
        try:
            world_state = world_module.load_world_state(book_folder)
            all_chars = list(world_state.get("characters", {}).keys())
        except Exception:
            pass

    v_failures, v_warnings = voice_module.validate_dialogue_style(text, chapter.draft)
    for failure in v_failures:
        issues.append(_make_issue(
            "VALIDATOR_DIALOGUE_STYLE",
            failure,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    if pov_character and all_chars:
        pov_failures = voice_module.validate_pov_locking(text, pov_character, all_chars)
        for failure in pov_failures:
            issues.append(_make_issue(
                "VALIDATOR_POV_VIOLATION",
                failure,
                chapter=chapter.slug,
                file=chapter.draft,
            ))

    so_failures, so_warnings = voice_module.validate_sentence_openers(text)
    for failure in so_failures:
        issues.append(_make_issue(
            "VALIDATOR_SENTENCE_OPENER_ISSUE",
            failure,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    return tuple(issues)


def validate_source_alignment(chapter: ChapterFiles, phase_sections: dict[str, str]) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    phase_source = phase_sections.get(chapter.slug)
    if not phase_source:
        issues.append(_make_issue(
            "VALIDATOR_NO_MATCHING_SOURCE",
            f"No matching `{chapter.slug}` section found in `phase-0.md`.",
            chapter=chapter.slug,
        ))
        return tuple(issues)

    if not chapter.scene_breakdown.exists() or not chapter.draft.exists():
        return tuple(issues)

    scene_text = read_text(chapter.scene_breakdown)
    draft_text = read_text(chapter.draft)
    scene_score, scene_missing = coverage(phase_source, scene_text)
    draft_score, draft_missing = coverage(phase_source, draft_text)

    if scene_score < 0.50:
        issues.append(_make_issue(
            "VALIDATOR_WEAK_SOURCE_COVERAGE",
            f"Scene breakdown has limited overlap with `phase-0.md` source ({scene_score:.0%}); check missing terms: {', '.join(scene_missing[:8])}.",
            chapter=chapter.slug,
            file=chapter.scene_breakdown,
        ))

    if draft_score < 0.35:
        issues.append(_make_issue(
            "VALIDATOR_WEAK_SOURCE_COVERAGE",
            f"Draft has limited overlap with `phase-0.md` source ({draft_score:.0%}); check missing terms: {', '.join(draft_missing[:8])}.",
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    weak_fields = []
    for field in extract_scene_fields(scene_text):
        field_terms = key_terms(field)
        if len(field_terms) < 3:
            continue
        field_score, field_missing = coverage(field, draft_text)
        if field_score < 0.25:
            weak_fields.append(f"{field[:80]}... missing {', '.join(field_missing[:5])}")

    if weak_fields:
        issues.append(_make_issue(
            "VALIDATOR_WEAK_BEAT_COVERAGE",
            "Some beat source anchors or required movements have weak draft coverage: " + " | ".join(weak_fields[:3]),
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    return tuple(issues)


def validate_chapter(chapter: ChapterFiles, phase_sections: dict[str, str]) -> ChapterReport:
    report = ChapterReport(chapter=chapter)
    if not chapter.drafting_plan.exists() or not read_text(chapter.drafting_plan).strip():
        report.failures.append(f"Missing or empty `{chapter.drafting_plan}`.")
    else:
        report.passes.append("Drafting plan exists.")

    scene_issues = validate_scene_breakdown(chapter)
    for issue in scene_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    if chapter.scene_breakdown.exists():
        combat_scenes = action.discover_combat_scenes(chapter.scene_breakdown)
        for c_scene in combat_scenes:
            scene_id = c_scene["id"]
            title = c_scene["title"]
            plan_path = action.get_action_plan_path(chapter.folder, scene_id)
            if not plan_path.exists():
                report.failures.append(f"Combat scene '{title}' is defined, but missing action plan: `{plan_path.name}`.")
            else:
                report.passes.append(f"Found combat plan for scene: {title}")
                if chapter.draft.exists():
                    c_passes, c_warnings, c_failures = action.validate_scene_combat(chapter.draft, plan_path)
                    report.passes.extend([f"[{title}] {p}" for p in c_passes])
                    report.warnings.extend([f"[{title}] {w}" for w in c_warnings])
                    report.failures.extend([f"[{title}] {f}" for f in c_failures])

    if chapter.scene_breakdown.exists() and chapter.draft.exists():
        book_folder = chapter.folder.parent.parent
        world_state_path = book_folder / "world-state.json"
        world_state = world_module.load_world_state(book_folder) if world_state_path.exists() else None

        from bookforge.core import relationship as relationship_module
        relationships = relationship_module.load_relationships(book_folder)

        scenes = world_module.discover_scenes_from_breakdown(chapter.scene_breakdown)
        draft_text = read_text(chapter.draft)

        scene_drafts = {}
        draft_sections = re.split(r"(?im)^(?=##|###|scene\s+\d+)", draft_text)
        current_key = "default"
        for sec in draft_sections:
            lines = sec.splitlines()
            if lines:
                match = re.search(r"(?i)scene[-_ ]*(\d+|\w+)", lines[0])
                if match:
                    current_key = f"scene-{match.group(1).lower()}".replace("-combat", "")
                    scene_drafts[current_key] = sec
                    continue
            scene_drafts[current_key] = scene_drafts.get(current_key, "") + "\n" + sec

        if world_state is not None:
            for scene in scenes:
                scene_id = scene["id"]
                title = scene["title"]
                scene_draft = scene_drafts.get(scene_id, draft_text)

                w_failures, w_warnings = world_module.validate_scene_world_state(scene, scene_draft, world_state)

                rel_failures, rel_warnings = relationship_module.validate_relationships_prose(scene, scene_draft, relationships)
                w_failures.extend(rel_failures)
                w_warnings.extend(rel_warnings)

                if not w_failures and not w_warnings:
                    report.passes.append(f"Physical logistics & relationships validated for scene: {title}")
                else:
                    report.failures.extend([f"[{title}] {f}" for f in w_failures])
                    report.warnings.extend([f"[{title}] {w}" for w in w_warnings])

            world_module.save_world_state(book_folder, world_state)

    draft_issues = validate_draft(chapter)
    for issue in draft_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    source_issues = validate_source_alignment(chapter, phase_sections)
    for issue in source_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    pacing_issues = validate_chapter_pacing(chapter)
    for issue in pacing_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    continuity_issues = validate_continuity_out_issues(chapter)
    for issue in continuity_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    return report


def collect_all_issues(book_folder: Path) -> tuple[ManuscriptIssue, ...]:
    all_issues: list[ManuscriptIssue] = []

    book_issues = validate_required_book_file_issues(book_folder)
    all_issues.extend(book_issues)

    phase_sections = parse_phase_chapters(book_folder)
    chapters = discover_chapters(book_folder)
    for chapter in chapters:
        all_issues.extend(validate_scene_breakdown(chapter))
        all_issues.extend(validate_draft(chapter))
        all_issues.extend(validate_source_alignment(chapter, phase_sections))
        all_issues.extend(validate_chapter_pacing(chapter))
        all_issues.extend(validate_continuity_out_issues(chapter))

    return tuple(all_issues)


def overall_status(book_failures: list[str], reports: list[ChapterReport]) -> str:
    if book_failures or any(report.failures for report in reports):
        return "FAIL"
    if any(report.warnings for report in reports):
        return "WARN"
    return "PASS"


def render_report(
    book_folder: Path,
    book_passes: list[str],
    book_failures: list[str],
    book_warnings: list[str],
    reports: list[ChapterReport],
) -> str:
    lines = [
        "# Manuscript Context Validation Report",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Overall Status:** {overall_status(book_failures, reports)}",
        "- **Length Status:** Run `bf status` or `bf status <book_folder>` to view rhythm and word limits.",
        "",
        "## Book Files",
        "",
    ]
    for item in book_passes:
        lines.append(f"- PASS: {item}")
    for item in book_warnings:
        lines.append(f"- WARN: {item}")
    for item in book_failures:
        lines.append(f"- FAIL: {item}")
    lines.extend(["", "## Chapter Status", "", "| Chapter | Status | Failures | Warnings |", "| --- | --- | ---: | ---: |"])
    for report in reports:
        lines.append(f"| {report.chapter.label} | {report.status} | {len(report.failures)} | {len(report.warnings)} |")
    lines.append("")
    for report in reports:
        lines.extend([f"## {report.chapter.label}", "", f"- **Status:** {report.status}"])
        for item in report.failures:
            lines.append(f"- FAIL: {item}")
        for item in report.warnings:
            lines.append(f"- WARN: {item}")
        if not report.failures and not report.warnings:
            lines.append("- PASS: Deterministic checks passed.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate manuscript context and style rules.")
    parser.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder.")
    parser.add_argument("--chapter", help="Limit checks to a single chapter slug (e.g. chapter-01).")
    parser.add_argument("--ai-prompt", action="store_true", help="Generate an AI semantic review prompt.")
    return parser.parse_args()


def build_ai_prompt(book_folder: Path, chapter: ChapterFiles) -> str:
    from bookforge.core.scanner import source_path
    src = source_path(book_folder)
    if not src:
        raise RuntimeError("Missing outlining source.")
    source_paths = [
        src,
        book_folder / "rulebook.md",
        book_folder / "mood-lock.md",
        book_folder / "chapter-summaries.md",
        chapter.scene_breakdown,
        chapter.draft,
    ]
    for path in source_paths:
        if not path.exists():
            raise RuntimeError(f"Cannot build AI prompt; missing `{path}`.")

    template = load_prompt_template("validation/ai_review_prompt.md")
    return template.format(
        chapter_draft=chapter.draft,
        phase_0=src,
        rulebook=book_folder / "rulebook.md",
        mood_lock=book_folder / "mood-lock.md",
        chapter_summaries=book_folder / "chapter-summaries.md",
        scene_breakdown=chapter.scene_breakdown,
        chapter_label=chapter.label,
    )


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    chapters = discover_chapters(book_folder)
    if args.chapter:
        chapters = [chapter for chapter in chapters if chapter.slug == args.chapter]
        if not chapters:
            print(f"Error: chapter not found: {args.chapter}", file=sys.stderr)
            return 2

    if args.ai_prompt:
        if len(chapters) != 1:
            print("Error: --ai-prompt requires exactly one chapter via --chapter.", file=sys.stderr)
            return 2
        try:
            print(build_ai_prompt(book_folder, chapters[0]))
        except RuntimeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        return 0

    book_issues = validate_required_book_file_issues(book_folder)
    book_passes = [i.message for i in book_issues if i.severity == Severity.INFO]
    book_failures = [i.message for i in book_issues if i.severity == Severity.HARD]
    book_warnings = [i.message for i in book_issues if i.severity == Severity.SOFT]

    phase_sections = parse_phase_chapters(book_folder)
    reports = [validate_chapter(chapter, phase_sections) for chapter in chapters]
    print(render_report(book_folder, book_passes, book_failures, book_warnings, reports))
    return 1 if overall_status(book_failures, reports) == "FAIL" else 0
