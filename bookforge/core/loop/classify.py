"""Status classification logic for the manuscript loop."""

from __future__ import annotations

import re
from bookforge.core import rhythm as check_chapter_rhythm
from bookforge.core import validator as context_validator
from bookforge.core import length as length_checker
from bookforge.core.issue import Severity
from bookforge.core.loop.state import LengthState, soft_length_bounds, StyleIssue


def mode_for_status(status: str) -> str:
    if status in ("NEEDS_BOOK_REPAIR", "NEEDS_CONTEXT_REPAIR", "NEEDS_CONTINUITY_REPAIR"):
        return "repair"
    if status == "NEEDS_STYLE_REPAIR":
        return "style"
    if status == "NEEDS_EXPANSION":
        return "expansion"
    if status == "NEEDS_PACING_REBALANCE":
        return "repair"
    if status in ("DONE", "DONE_WITH_WARNINGS"):
        return "final"
    return "blocked"


def action_chapter(
    status: str,
    context_problem_chapters: list[str],
    expansion_chapter: str,
    style_issues: list[StyleIssue],
    continuity_failures: list[str],
    rebalance_chapter: str = "NONE",
) -> str | None:
    if status == "NEEDS_CONTEXT_REPAIR" and context_problem_chapters:
        return context_problem_chapters[0]
    if status == "NEEDS_CONTINUITY_REPAIR" and continuity_failures:
        match = re.match(r"(chapter-\d+|epilogue)", continuity_failures[0])
        if match:
            return match.group(1)
    if status == "NEEDS_EXPANSION" and expansion_chapter != "NONE":
        return expansion_chapter
    if status == "NEEDS_PACING_REBALANCE" and rebalance_chapter != "NONE":
        return rebalance_chapter
    if status == "NEEDS_STYLE_REPAIR" and style_issues:
        for part in style_issues[0].path.parts:
            if part.startswith("chapter-") or part == "epilogue":
                return part
    return None


def issue_chapters(reports: list[context_validator.ChapterReport]) -> list[str]:
    chapters: list[str] = []
    for report in reports:
        if report.failures or report.warnings:
            chapters.append(report.chapter.slug)
    return chapters


def hard_issue_chapters(reports: list[context_validator.ChapterReport]) -> list[str]:
    chapters: list[str] = []
    for report in reports:
        if report.failures:
            chapters.append(report.chapter.slug)
    return chapters


def choose_expansion_chapter(
    reports: list[context_validator.ChapterReport],
    counts: list[length_checker.DraftCount],
) -> str:
    words_by_chapter = {}
    for item in counts:
        if item.label == "Epilogue":
            words_by_chapter["epilogue"] = item.words
        else:
            match = re.search(r"Chapter\s+(\d+)", item.label)
            if match:
                words_by_chapter[f"chapter-{int(match.group(1)):02d}"] = item.words

    valid_slugs = [report.chapter.slug for report in reports if report.status == "PASS" and report.chapter.slug != "epilogue"]
    if not valid_slugs:
        return "NONE"
    return min(valid_slugs, key=lambda slug: words_by_chapter.get(slug, 10**9))


def choose_rebalance_chapter(counts: object) -> str:
    if hasattr(counts, "counts"):
        candidates = check_chapter_rhythm.trim_candidates(counts)
        if not candidates:
            return "NONE"
        selected = candidates[0]
    elif counts:
        candidates = [item for item in counts if not item.is_epilogue and item.words >= 2000]
        if not candidates:
            return "NONE"
        selected = max(candidates, key=lambda item: item.words)
    else:
        return "NONE"

    match = re.search(r"Chapter\s+(\d+)", selected.label)
    return f"chapter-{int(match.group(1)):02d}" if match else selected.label


def _severity_of(issue: object) -> Severity:
    severity = getattr(issue, "severity", None)
    if isinstance(severity, Severity):
        return severity
    if isinstance(severity, str):
        return Severity.HARD if severity.upper() == "HARD" else Severity.SOFT
    level = getattr(issue, "level", None)
    if isinstance(level, str):
        return Severity.HARD if level.upper() in {"FAIL", "HARD"} else Severity.SOFT
    return Severity.SOFT


def _message_of(issue: object) -> str:
    return str(getattr(issue, "message", issue))


def classify(
    length_state: LengthState,
    book_failures: list[object],
    reports: list[context_validator.ChapterReport],
    style_issues: list[StyleIssue],
    repair_attempts: dict[str, int],
    max_repair_attempts: int,
    continuity_failures: list[str],
    narrative_issues: list[object] | tuple[object, ...] | None = None,
    rhythm_issues: list[object] | tuple[object, ...] | None = None,
) -> tuple[str, str]:
    narrative_issues = list(narrative_issues or [])
    rhythm_issues = list(rhythm_issues or [])
    problem_chapters = hard_issue_chapters(reports)
    repeated_blockers = [
        slug for slug in problem_chapters if repair_attempts.get(slug, 0) >= max_repair_attempts
    ]

    hard_book_issues = [issue for issue in book_failures if _severity_of(issue) == Severity.HARD]
    if hard_book_issues:
        return "NEEDS_BOOK_REPAIR", "Book-level hard issues must be fixed before expansion."
    if book_failures:
        return "DONE_WITH_WARNINGS", "Book-level soft warnings remain; autonomous loop stops with soft warnings."
    if repeated_blockers:
        return "BLOCKED", f"Repair attempt limit reached for: {', '.join(repeated_blockers)}."
    if any(report.failures for report in reports):
        return "NEEDS_CONTEXT_REPAIR", "Context validator reported chapter failures."
    if continuity_failures:
        return "NEEDS_CONTINUITY_REPAIR", f"Continuity chain check failed: {continuity_failures[0]}."
    if style_issues:
        return "NEEDS_STYLE_REPAIR", "Style-risk scan found flagged draft lines."

    soft_min, soft_max = soft_length_bounds(length_state.target_min, length_state.target_max)
    if length_state.total_words < soft_min:
        return "NEEDS_EXPANSION", "Manuscript is below target soft minimum."
    if length_state.total_words > soft_max:
        return "BLOCKED", "Manuscript is above soft maximum; request trim/review before continuing."

    soft_warnings: list[str] = []
    if length_state.total_words < length_state.target_min:
        soft_warnings.append("Manuscript is within soft tolerance below target minimum.")
    elif length_state.total_words > length_state.target_max:
        soft_warnings.append("Manuscript is within soft tolerance above target maximum.")
    soft_warnings.extend(report.warnings[0] for report in reports if report.warnings)
    soft_warnings.extend(_message_of(issue) for issue in rhythm_issues if _severity_of(issue) != Severity.HARD)
    soft_warnings.extend(_message_of(issue) for issue in narrative_issues if _severity_of(issue) != Severity.HARD)

    hard_rhythm = [issue for issue in rhythm_issues if _severity_of(issue) == Severity.HARD]
    hard_narrative = [issue for issue in narrative_issues if _severity_of(issue) == Severity.HARD]
    if hard_rhythm or hard_narrative:
        return "NEEDS_PACING_REBALANCE", "Hard rhythm or narrative checks require repair."
    if soft_warnings:
        return "DONE_WITH_WARNINGS", "Manuscript is within stop range with soft warnings only."
    return "DONE", "Manuscript is within target range with clean deterministic checks."
