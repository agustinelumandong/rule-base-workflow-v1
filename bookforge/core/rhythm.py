#!/usr/bin/env python3
"""BookForge Rhythm Core Module.

Checks chapter lengths for natural rhythm/contrast and low variance risk.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bookforge.core import length as length_checker
from bookforge.core.issue import IssueCategory, ManuscriptIssue, Severity, compute_fingerprint

PACING_ROW_RE = re.compile(r"^\|\s*(Chapter\s+\d+|Epilogue)\s*\|\s*([^|]+?)\s*\|", re.MULTILINE)

RHYTHM_RULE_META = {
    "RHYTHM_UNIFORM_FLOOR": (Severity.SOFT, "Chapter word counts lack rhythm variation; all chapters are too even."),
    "RHYTHM_LOW_VARIANCE": (Severity.SOFT, "Chapter spread is narrow; add lean/long contrast through trim/rebalance."),
    "RHYTHM_TOO_FEW_LEAN": (Severity.SOFT, "Too few lean chapters; expected at least {expected} lean chapters."),
    "RHYTHM_TOO_MANY_LONG": (Severity.SOFT, "Too many chapters are over 2400 words; too many carry long treatment."),
    "RHYTHM_PACING_MISMATCH": (Severity.SOFT, "{label} is `{pacing_class}` in pacing plan but has {words} words."),
    "RHYTHM_EXPANDED_OVERSIZED": (Severity.INFO, "{label} is `expanded` but has {words} words; consider trimming unless source demands it."),
    "RHYTHM_EPILOGUE_OVERSIZED": (Severity.INFO, "{label} is `epilogue/teaser` but has {words} words."),
}


def _make_rhythm_issue(
    rule_id: str,
    chapter: Optional[str],
    file: Optional[Path],
    **format_kwargs,
) -> ManuscriptIssue:
    severity, base_message = RHYTHM_RULE_META.get(rule_id, (Severity.INFO, "Rhythm issue"))
    message = base_message.format(**format_kwargs)
    return ManuscriptIssue(
        severity=severity,
        category=IssueCategory.RHYTHM,
        chapter=chapter,
        file=file,
        rule_id=rule_id,
        message=message,
        fingerprint=compute_fingerprint(rule_id, file, None, None),
    )


@dataclass(frozen=True)
class RhythmReport:
    book_folder: Path
    counts: list[length_checker.DraftCount]
    issues: tuple[ManuscriptIssue, ...]
    average: int
    median: int
    minimum: int
    maximum: int
    stdev: int
    under_1800: int
    over_2400: int
    pacing_classes: dict[str, str]

    @property
    def status(self) -> str:
        hard_issues = [i for i in self.issues if i.severity == Severity.HARD]
        return "FAIL" if hard_issues else ("WARN" if self.issues else "PASS")


def slug_for_label(label: str) -> str:
    if label == "Epilogue":
        return "epilogue"
    match = re.search(r"Chapter\s+(\d+)", label)
    if match:
        return f"chapter-{int(match.group(1)):02d}"
    return label.lower().replace(" ", "-")


def parse_pacing_classes(book_folder: Path) -> dict[str, str]:
    path = book_folder / "chapter-pacing-plan.md"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    classes: dict[str, str] = {}
    for label, pacing_class in PACING_ROW_RE.findall(text):
        classes[slug_for_label(label)] = pacing_class.strip()
    return classes


def analyze(
    book_folder: Path,
    minimum_lean_chapters: int = 2,
    uniform_floor: int = 2000,
    low_variance_stdev: int = 350,
) -> RhythmReport:
    counts = length_checker.find_drafts(book_folder)
    normal = [item for item in counts if not item.is_epilogue]
    if not normal:
        raise RuntimeError("No normal chapter drafts found.")

    values = [item.words for item in normal]
    average = round(statistics.mean(values))
    median = round(statistics.median(values))
    minimum = min(values)
    maximum = max(values)
    stdev = round(statistics.pstdev(values))
    under_1800 = sum(1 for value in values if value < 1800)
    over_2400 = sum(1 for value in values if value > 2400)
    pacing_classes = parse_pacing_classes(book_folder)

    issues: list[ManuscriptIssue] = []
    if all(value >= uniform_floor for value in values):
        issues.append(_make_rhythm_issue(
            "RHYTHM_UNIFORM_FLOOR",
            chapter=None,
            file=book_folder,
        ))
    if stdev < low_variance_stdev:
        issues.append(_make_rhythm_issue(
            "RHYTHM_LOW_VARIANCE",
            chapter=None,
            file=book_folder,
        ))
    if under_1800 < minimum_lean_chapters:
        issues.append(_make_rhythm_issue(
            "RHYTHM_TOO_FEW_LEAN",
            chapter=None,
            file=book_folder,
            expected=minimum_lean_chapters,
        ))
    high_chapter_limit = max(len(normal) // 2, len(normal) - 4)
    if over_2400 > high_chapter_limit:
        issues.append(_make_rhythm_issue(
            "RHYTHM_TOO_MANY_LONG",
            chapter=None,
            file=book_folder,
        ))

    for item in normal:
        slug = slug_for_label(item.label)
        pacing_class = pacing_classes.get(slug)
        if pacing_class in {"lean", "standard"} and item.words > 2200:
            issues.append(_make_rhythm_issue(
                "RHYTHM_PACING_MISMATCH",
                chapter=slug,
                file=None,
                label=item.label,
                pacing_class=pacing_class,
                words=item.words,
            ))
        if pacing_class == "expanded" and item.words > 2600:
            issues.append(_make_rhythm_issue(
                "RHYTHM_EXPANDED_OVERSIZED",
                chapter=slug,
                file=None,
                label=item.label,
                words=item.words,
            ))
        if pacing_class == "epilogue/teaser" and item.words > 900:
            issues.append(_make_rhythm_issue(
                "RHYTHM_EPILOGUE_OVERSIZED",
                chapter=slug,
                file=None,
                label=item.label,
                words=item.words,
            ))

    return RhythmReport(
        book_folder=book_folder,
        counts=counts,
        issues=tuple(issues),
        average=average,
        median=median,
        minimum=minimum,
        maximum=maximum,
        stdev=stdev,
        under_1800=under_1800,
        over_2400=over_2400,
        pacing_classes=pacing_classes,
    )


def trim_candidates(report: RhythmReport) -> list[length_checker.DraftCount]:
    normal = [item for item in report.counts if not item.is_epilogue]
    def score(item: length_checker.DraftCount) -> tuple[int, int]:
        pacing_class = report.pacing_classes.get(slug_for_label(item.label), "")
        class_weight = {"lean": 5, "standard": 4, "expanded": 3, "major": 1}.get(pacing_class, 3)
        distance_to_lean = -abs(item.words - 1900)
        return (class_weight, distance_to_lean)

    candidates = [item for item in normal if item.words >= 2000]
    return sorted(candidates, key=score, reverse=True)


def render_report(report: RhythmReport) -> str:
    lines = [
        "# Chapter Rhythm Report",
        "",
        f"- **Book Folder:** `{report.book_folder}`",
        f"- **Status:** {report.status}",
        f"- **Average Normal Chapter Words:** {report.average}",
        f"- **Median Normal Chapter Words:** {report.median}",
        f"- **Minimum Normal Chapter Words:** {report.minimum}",
        f"- **Maximum Normal Chapter Words:** {report.maximum}",
        f"- **Normal Chapter Stdev:** {report.stdev}",
        f"- **Normal Chapters Under 1800:** {report.under_1800}",
        f"- **Normal Chapters Over 2400:** {report.over_2400}",
        "",
        "## Draft Rhythm",
        "",
        "| Section | Words | Pacing Class |",
        "| --- | ---: | --- |",
    ]
    for item in report.counts:
        pacing_class = report.pacing_classes.get(slug_for_label(item.label), "not planned")
        lines.append(f"| {item.label} | {item.words} | {pacing_class} |")

    lines.extend(["", "## Warnings", ""])
    if report.issues:
        lines.extend(f"- {issue.message}" for issue in report.issues)
    else:
        lines.append("- No chapter rhythm warnings.")

    lines.extend(["", "## Rebalance Candidates", ""])
    candidates = trim_candidates(report)
    if candidates:
        for item in candidates[:8]:
            pacing_class = report.pacing_classes.get(slug_for_label(item.label), "not planned")
            lines.append(
                f"- {item.label}: {item.words} words, pacing `{pacing_class}`. Best lean-candidate trim target; compress repeated action, overlong aftermath, or loose transitions first."
            )
    else:
        lines.append("- No trim candidates above 2200 words.")

    lines.extend(
        [
            "",
            "## Rules",
            "",
            "- Rebalance by trimming or compressing approved material, not by inventing new story.",
            "- Keep major chapters longer only when source movement justifies it.",
            "- Preserve context validator PASS after any rhythm repair.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Check whether chapter lengths have natural rhythm.")
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/tex-cade",
        help="Book folder containing chapters/ and optional chapter-pacing-plan.md.",
    )
    parser.add_argument(
        "--minimum-lean-chapters",
        type=int,
        default=2,
        help="Expected minimum number of normal chapters below 1800 words.",
    )
    parser.add_argument(
        "--uniform-floor",
        type=int,
        default=2000,
        help="Warn when every normal chapter is at or above this word count.",
    )
    parser.add_argument(
        "--low-variance-stdev",
        type=int,
        default=350,
        help="Warn when normal chapter standard deviation is below this value.",
    )
    args = parser.parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    try:
        report = analyze(
            book_folder,
            minimum_lean_chapters=args.minimum_lean_chapters,
            uniform_floor=args.uniform_floor,
            low_variance_stdev=args.low_variance_stdev,
        )
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(render_report(report))
    return 0

