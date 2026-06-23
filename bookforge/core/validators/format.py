"""Format and structure related validation functions and constants."""

from __future__ import annotations

import json
import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from bookforge.core.issue import (
    IssueCategory,
    Severity,
    ManuscriptIssue,
    compute_fingerprint,
)
from bookforge.core import unknowns as unknowns_module
from bookforge.core.validators.style import DEFAULT_SETTINGS

# File constants
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
CONTEXT_LOCK_MARKER = "### Source Context Lock"
CONTEXT_LOCK_END_MARKER = "###"
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
    "VALIDATOR_DIRECT_RULEBOOK_EDIT_DEPRECATED": RuleMeta("VALIDATOR_DIRECT_RULEBOOK_EDIT_DEPRECATED", Severity.SOFT, IssueCategory.CONTEXT),
    "VALIDATOR_REPEATED_PROSE": RuleMeta("VALIDATOR_REPEATED_PROSE", Severity.SOFT, IssueCategory.STYLE),
    "VALIDATOR_PLOT_MODE_RISK": RuleMeta("VALIDATOR_PLOT_MODE_RISK", Severity.SOFT, IssueCategory.NARRATIVE),
    "VALIDATOR_OUTLINE_LIFE_STATE_CONTRADICTION": RuleMeta(
        "VALIDATOR_OUTLINE_LIFE_STATE_CONTRADICTION", Severity.SOFT, IssueCategory.CONTINUITY
    ),
    "SCENE_MISSING_DRAFT": RuleMeta("SCENE_MISSING_DRAFT", Severity.HARD, IssueCategory.CONTEXT),
    "SCENE_EMPTY_DRAFT": RuleMeta("SCENE_EMPTY_DRAFT", Severity.HARD, IssueCategory.CONTEXT),
    "SCENE_WORD_COUNT_VIOLATION": RuleMeta("SCENE_WORD_COUNT_VIOLATION", Severity.HARD, IssueCategory.STYLE),
    "SCENE_FORBIDDEN_ELEMENT": RuleMeta("SCENE_FORBIDDEN_ELEMENT", Severity.HARD, IssueCategory.NARRATIVE),
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
    resolved_severity = severity if severity is not None else meta.severity
    return ManuscriptIssue(
        severity=resolved_severity,
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

    def __init__(
        self,
        slug: str | Path,
        label: str | None = None,
        folder: Path | None = None,
        draft: Path | None = None,
        scene_breakdown: Path | None = None,
        drafting_plan: Path | None = None,
        continuity_out: Path | None = None,
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
            # Look for draft.md or default names ({slug_value}.md, epilogue.md)
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
        
        # Staging proposal.md takes priority over scene-breakdown.md
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
                if fallback_proposal.exists():
                    scene_breakdown = fallback_proposal
                else:
                    scene_breakdown = fallback_scene_bd
            else:
                scene_breakdown = proposal_path

        # Staging beats.md takes priority over drafting-plan.md
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
                if fallback_beats.exists():
                    drafting_plan = fallback_beats
                else:
                    drafting_plan = fallback_drafting_plan
            else:
                drafting_plan = beats_path

        if continuity_out is None:
            continuity_out_path = folder / "continuity-out.md"
            if continuity_out_path.exists():
                continuity_out = continuity_out_path
            elif fallback_folder:
                fallback_cont_out = fallback_folder / "continuity-out.md"
                if fallback_cont_out.exists():
                    continuity_out = fallback_cont_out
                else:
                    continuity_out = continuity_out_path
            else:
                continuity_out = continuity_out_path

        object.__setattr__(self, "slug", slug_value)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "folder", folder)
        object.__setattr__(self, "draft", draft)
        object.__setattr__(self, "scene_breakdown", scene_breakdown)
        object.__setattr__(self, "drafting_plan", drafting_plan)
        object.__setattr__(self, "continuity_out", continuity_out)


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


def chapter_sort_key(path: Path) -> tuple[int, str]:
    if path.name == "epilogue":
        return (999, path.name)
    match = re.search(r"chapter-(\d+)", path.name)
    number = int(match.group(1)) if match else None
    return (number if number is not None else 998, path.name)


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



PHASE_CHAPTER_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?(Chapter\s+(\d+)|Epilogue(?:\s+Teaser)?)(?:\*\*)?(?:\s*[:\-].*)?$"
)


def parse_phase_chapters(book_folder: Path) -> dict[str, str]:
    from bookforge.core.scanner import source_path
    src = source_path(book_folder)
    if not src or not src.exists():
        return {}
    
    text = src.read_text(encoding="utf-8")
    sections = {}
    matches = list(PHASE_CHAPTER_RE.finditer(text))
    for i, match in enumerate(matches):
        label = match.group(1).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        
        slug = label.lower().replace(" ", "-")
        if "chapter" in slug:
            number = int(match.group(2))
            slug = f"chapter-{number:02d}"
        sections[slug] = body
    return sections


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


def validate_required_book_file_issues(book_folder: Path) -> tuple[ManuscriptIssue, ...]:
    from bookforge.core.validators.continuity import _extract_rulebook_section, _extract_unknown_markers, _ledger_has_chapter_entry
    issues: list[ManuscriptIssue] = []

    from bookforge.core.scanner import source_path
    src = source_path(book_folder)
    if not src or not src.exists() or not src.read_text(encoding="utf-8").strip():
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
            except (yaml.YAMLError, OSError, KeyError, AttributeError):
                expected_chapters = []
            for chapter_slug in expected_chapters:
                if not _ledger_has_chapter_entry(ledger_text, chapter_slug):
                    issues.append(_make_issue(
                        "VALIDATOR_MISSING_CONTINUITY_LEDGER",
                        f"Rulebook `Chapter Continuity Ledger` is missing `{chapter_slug}` coverage.",
                        file=rulebook_path,
                    ))

        # Check if rulebook.md is edited directly (modified in git)
        import subprocess
        try:
            res = subprocess.run(["git", "status", "--porcelain", str(rulebook_path)], capture_output=True, text=True, check=True)
            if res.stdout.strip():
                issues.append(_make_issue(
                    "VALIDATOR_DIRECT_RULEBOOK_EDIT_DEPRECATED",
                    "Direct editing of rulebook.md is deprecated. Please use the event-sourced change workflow (bf memory learn/apply-learning) instead.",
                    file=rulebook_path,
                ))
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass

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
    from bookforge.core.validators.continuity import check_context_lock_unknowns
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
