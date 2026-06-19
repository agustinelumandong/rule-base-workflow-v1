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
        "warn_short_sentence_runs": False,
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
    "VALIDATOR_NO_MATCHING_SOURCE": RuleMeta("VALIDATOR_NO_MATCHING_SOURCE", Severity.HARD, IssueCategory.CONTEXT),
    "VALIDATOR_POV_VIOLATION": RuleMeta("VALIDATOR_POV_VIOLATION", Severity.HARD, IssueCategory.STYLE),
    "VALIDATOR_SENTENCE_OPENER_ISSUE": RuleMeta("VALIDATOR_SENTENCE_OPENER_ISSUE", Severity.SOFT, IssueCategory.STYLE),
    "VALIDATOR_STYLE_REVIEW_SIGNAL": RuleMeta("VALIDATOR_STYLE_REVIEW_SIGNAL", Severity.SOFT, IssueCategory.STYLE),
}


def _make_issue(
    rule_id: str,
    message: str,
    chapter: str | None = None,
    file: Path | None = None,
    line: int | None = None,
    span: str | None = None,
) -> ManuscriptIssue:
    meta = RULE_META.get(rule_id, RuleMeta(rule_id, Severity.INFO, IssueCategory.CONTEXT))
    return ManuscriptIssue(
        severity=meta.severity,
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

    def __init__(
        self,
        slug: str | Path,
        label: str | None = None,
        folder: Path | None = None,
        draft: Path | None = None,
        scene_breakdown: Path | None = None,
        drafting_plan: Path | None = None,
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

        if draft is None:
            draft_name = "epilogue.md" if slug_value == "epilogue" else f"{slug_value}.md"
            draft = folder / draft_name
            legacy_draft = folder / "draft.md"
            if not draft.exists() and legacy_draft.exists():
                draft = legacy_draft
        scene_breakdown = scene_breakdown or folder / "scene-breakdown.md"
        drafting_plan = drafting_plan or folder / "drafting-plan.md"

        object.__setattr__(self, "slug", slug_value)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "folder", folder)
        object.__setattr__(self, "draft", draft)
        object.__setattr__(self, "scene_breakdown", scene_breakdown)
        object.__setattr__(self, "drafting_plan", drafting_plan)


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
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        return []
    chapters = []
    for chapter_dir in sorted(chapters_root.iterdir(), key=chapter_sort_key):
        if not chapter_dir.is_dir():
            continue
        slug = chapter_dir.name
        if slug == "epilogue":
            label = "Epilogue"
            draft_name = "epilogue.md"
        else:
            match = re.match(r"chapter-(\d+)", slug)
            if match:
                label = f"Chapter {int(match.group(1)):02d}"
                draft_name = f"{slug}.md"
            else:
                label = slug.replace("-", " ").title()
                draft_name = f"{slug}.md"

        chapters.append(
            ChapterFiles(
                slug=slug,
                label=label,
                folder=chapter_dir,
                draft=chapter_dir / draft_name,
                scene_breakdown=chapter_dir / "scene-breakdown.md",
                drafting_plan=chapter_dir / "drafting-plan.md",
            )
        )
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


def check_style_review_signals(text: str, settings_start: Path | None = None) -> list[str]:
    settings = load_project_settings(settings_start)
    style_settings = settings.get("style_review", {})
    if not isinstance(style_settings, dict) or not style_settings.get("enabled", True):
        return []

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


def validate_continuity_out_issues(chapter: ChapterFiles) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    if not chapter.draft.exists():
        return tuple(issues)
    draft_text = chapter.draft.read_text(encoding="utf-8")
    if not draft_text.strip():
        return tuple(issues)
    continuity_path = chapter.folder / "continuity-out.md"
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
        passes.append("`continuity-out.md` present and non-empty.")
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
    from bookforge.core.scanner import source_path
    phase_0_path = source_path(book_folder)
    book_year = 1880
    if phase_0_path and phase_0_path.exists():
        p0_text = phase_0_path.read_text(encoding="utf-8")
        match = re.search(r"(?i)Period:\s*.*?(\d{4})", p0_text)
        if match:
            book_year = int(match.group(1))
        else:
            match_general = re.search(r"\b(18\d{2}|1900)\b", p0_text)
            if match_general:
                book_year = int(match_general.group(1))

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

    v_failures, v_warnings = voice_module.validate_dialogue_style(text)
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
