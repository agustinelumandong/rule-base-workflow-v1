"""Narrative quality heuristics for manuscript workflow checks."""

from __future__ import annotations

from pathlib import Path
from bookforge.core import validator
from bookforge.core.issue import ManuscriptIssue
from bookforge.core.narrative_quality.models import NarrativeIssue, NarrativeReport
from bookforge.core.narrative_quality.helpers import _extract_beats
from bookforge.core.narrative_quality.checks import (
    _check_series_name_collisions,
    _check_tension_diversity,
    _check_rotation,
    _check_character_distinctiveness,
    _check_antagonist_contrast,
    _check_sensory_decision,
)


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
        continuity_path = chapter.continuity_out
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
