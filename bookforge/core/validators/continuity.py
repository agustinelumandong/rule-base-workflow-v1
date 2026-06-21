"""Continuity-related validation functions and helpers."""

from __future__ import annotations

import re
from pathlib import Path

from bookforge.core.validators.format import (
    CONTEXT_LOCK_MARKER,
    CONTEXT_LOCK_END_MARKER,
    RULEBOOK_SECTION_HEADING_RE,
    RULEBOOK_UNKNOWN_ALLOWED_SECTIONS,
    UNRESOLVED_MARKERS,
    ChapterFiles,
    _make_issue,
)


def check_unprofiled_period_terms(text: str, book_folder: Path) -> list[str]:
    """Checks the draft for period-specific terms not documented in research-pack.md."""
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
    """Checks scene breakdown context-lock fields for unresolved markers (UNKNOWN, TBD, etc.)."""
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
    """Extracts the body of the first section that matches one of the given aliases."""
    headings = list(RULEBOOK_SECTION_HEADING_RE.finditer(text))
    aliases = {normalize_heading_name(alias) for alias in section_aliases}
    for index, heading in enumerate(headings):
        title = heading.group(2).strip()
        if normalize_heading_name(title) not in aliases:
            continue
        level = len(heading.group(1))
        end = len(text)
        for next_heading in headings[index + 1:]:
            if len(next_heading.group(1)) <= level:
                end = next_heading.start()
                break
        section_body_start = heading.end()
        return text[section_body_start:end].strip()
    return ""


def _extract_unknown_markers(text: str) -> list[str]:
    """Scans rulebook text for UNKNOWN/TBD/TODO/FIXME markers outside allowed sections."""
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
    """Returns True if the continuity ledger contains an entry for the given chapter slug."""
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


def validate_continuity_out_issues(chapter: ChapterFiles) -> tuple:
    """Validates that continuity-out.md exists and is non-empty for drafted chapters."""
    issues: list = []
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
    """Returns (passes, failures) lists for continuity-out validation."""
    issues = validate_continuity_out_issues(chapter)
    passes: list[str] = []
    failures: list[str] = []
    for issue in issues:
        from bookforge.core.issue import Severity
        if issue.severity == Severity.HARD:
            failures.append(issue.message)
        else:
            failures.append(issue.message)
    if not failures:
        passes.append("`continuity-out.md` is present and non-empty.")
    return passes, failures
