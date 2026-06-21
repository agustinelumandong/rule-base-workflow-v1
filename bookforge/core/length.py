#!/usr/bin/env python3
"""BookForge Length Core Module."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bookforge.core.issue import IssueCategory, ManuscriptIssue, Severity, compute_fingerprint
from bookforge.core.scanner import TargetInfo, resolve_target, source_path


DEFAULT_CONTRACT_MIN = 30000
DEFAULT_CONTRACT_MAX = 31000
DEFAULT_SOFT_MARGIN_RATIO = 0.01


@dataclass(frozen=True)
class DraftCount:
    label: str
    words: int
    is_epilogue: bool = False


@dataclass(frozen=True)
class LengthIssue:
    rule_id: str
    severity: Severity
    message: str
    chapter: Optional[str] = None
    file: Optional[Path] = None


LENGTH_RULE_META = {
    "LENGTH_UNDER_SOFT_MIN": (Severity.HARD, "Total draft is below soft minimum ({soft_min} words); expansion is required."),
    "LENGTH_ABOVE_SOFT_MAX": (Severity.HARD, "Total draft is above soft maximum ({soft_max} words); trimming is required."),
    "LENGTH_UNDER_CONTRACT_MIN": (Severity.SOFT, "Total draft is below contract minimum ({target_min} words) but inside soft tolerance."),
    "LENGTH_ABOVE_CONTRACT_MAX": (Severity.SOFT, "Total draft is above contract maximum ({target_max} words) but inside soft tolerance."),
    "LENGTH_CHAPTER_BELOW_AVERAGE": (Severity.SOFT, "{label} is far below the current chapter average; revisit approved beats for source-supported expansion."),
}


def _make_length_issue(
    rule_id: str,
    chapter: Optional[str],
    file: Optional[Path],
    **format_kwargs,
) -> ManuscriptIssue:
    severity, base_message = LENGTH_RULE_META.get(rule_id, (Severity.INFO, "Length issue"))
    message = base_message.format(**format_kwargs)
    return ManuscriptIssue(
        severity=severity,
        category=IssueCategory.LENGTH,
        chapter=chapter,
        file=file,
        rule_id=rule_id,
        message=message,
        fingerprint=compute_fingerprint(rule_id, file, None, None),
    )


def word_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def find_target(book_folder: Path) -> TargetInfo:
    src = source_path(book_folder)
    source_text = src.read_text(encoding="utf-8") if src else ""
    return resolve_target(book_folder, source_text)


def chapter_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"chapter-(\d+)", str(path))
    if match:
        return (int(match.group(1)), path.name)
    return (999, path.name)


def find_drafts(book_folder: Path) -> list[DraftCount]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        raise RuntimeError("Missing chapters folder; no manuscript drafts found.")

    counts: list[DraftCount] = []
    chapter_paths = sorted(
        chapters_root.glob("chapter-*/chapter-*.md"),
        key=chapter_sort_key,
    )
    for path in chapter_paths:
        label = path.parent.name.replace("-", " ").title()
        counts.append(DraftCount(label=label, words=word_count(path)))

    epilogue_path = chapters_root / "epilogue" / "epilogue.md"
    if epilogue_path.exists():
        counts.append(DraftCount(label="Epilogue", words=word_count(epilogue_path), is_epilogue=True))

    if not counts:
        raise RuntimeError("No manuscript draft files found.")

    return counts


def pct(value: float) -> str:
    return f"{value:.1f}%"


def contract_range(target: TargetInfo) -> tuple[int, int]:
    target_min = target.words or DEFAULT_CONTRACT_MIN
    return target_min, target_min + 1000


def soft_range(target_min: int, target_max: int) -> tuple[int, int]:
    soft_margin = int(target_min * DEFAULT_SOFT_MARGIN_RATIO)
    return target_min - soft_margin, target_max + soft_margin


def analyze_length(book_folder: Path, target: TargetInfo, counts: list[DraftCount]) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    total = sum(item.words for item in counts)
    normal_chapters = [item for item in counts if not item.is_epilogue]
    target_min, target_max = contract_range(target)
    soft_min, soft_max = soft_range(target_min, target_max)

    if total < soft_min:
        issues.append(_make_length_issue(
            "LENGTH_UNDER_SOFT_MIN",
            chapter=None,
            file=book_folder,
            soft_min=soft_min,
        ))
    elif total > soft_max:
        issues.append(_make_length_issue(
            "LENGTH_ABOVE_SOFT_MAX",
            chapter=None,
            file=book_folder,
            soft_max=soft_max,
        ))
    elif total < target_min:
        issues.append(_make_length_issue(
            "LENGTH_UNDER_CONTRACT_MIN",
            chapter=None,
            file=book_folder,
            target_min=target_min,
        ))
    elif total > target_max:
        issues.append(_make_length_issue(
            "LENGTH_ABOVE_CONTRACT_MAX",
            chapter=None,
            file=book_folder,
            target_max=target_max,
        ))

    if normal_chapters:
        chapter_average = round(sum(item.words for item in normal_chapters) / len(normal_chapters))
        low_chapter_threshold = round(chapter_average * 0.70) if chapter_average else 0

        for item in normal_chapters:
            if low_chapter_threshold and item.words < low_chapter_threshold:
                issues.append(_make_length_issue(
                    "LENGTH_CHAPTER_BELOW_AVERAGE",
                    chapter=item.label,
                    file=None,
                    label=item.label,
                ))

    return tuple(issues)


def build_report(book_folder: Path, target: TargetInfo, counts: list[DraftCount]) -> str:
    total = sum(item.words for item in counts)
    remaining = max(target.words - total, 0)
    complete = (total / target.words * 100) if target.words else 0
    normal_chapters = [item for item in counts if not item.is_epilogue]
    chapter_average = (
        round(sum(item.words for item in normal_chapters) / len(normal_chapters))
        if normal_chapters
        else 0
    )
    low_chapter_threshold = round(chapter_average * 0.70) if chapter_average else 0

    issues = analyze_length(book_folder, target, counts)
    target_min, target_max = contract_range(target)
    soft_min, soft_max = soft_range(target_min, target_max)

    lines = [
        "# Manuscript Length Report",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Target Words:** {target.words}",
        f"- **Target Source:** {target.source}",
        f"- **Target Evidence:** {target.evidence}",
        f"- **Current Words:** {total}",
        f"- **Remaining Words:** {remaining}",
        f"- **Complete:** {pct(complete)}",
        f"- **Average Chapter Words:** {chapter_average}",
        f"- **Contract Range:** {target_min:,} - {target_max:,} words",
        f"- **Soft Range:** {soft_min:,} - {soft_max:,} words",
        "",
        "## Draft Counts",
        "",
        "| Section | Words |",
        "| --- | ---: |",
    ]

    for item in counts:
        lines.append(f"| {item.label} | {item.words} |")

    lines.extend(["", "## Warnings", ""])

    hard_issues = [i for i in issues if i.severity == Severity.HARD]
    soft_issues = [i for i in issues if i.severity == Severity.SOFT]

    if hard_issues:
        for issue in hard_issues:
            lines.append(f"- FAIL: {issue.message}")
    if soft_issues:
        for issue in soft_issues:
            lines.append(f"- WARN: {issue.message}")

    if not issues:
        lines.append("- No length warnings.")

    lines.extend(
        [
            "",
            "## Expansion Guidance",
            "",
            "- Revisit approved scene breakdowns before expanding prose.",
            "- Add only source-supported action, consequence, conflict, dialogue, setting texture, and transition.",
            "- Do not add unsupported events, names, motives, lore, or backstory to close the gap.",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(
        description="Check manuscript draft progress against the book-level word target."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/book-example",
        help="Book folder containing phase-0.md, rulebook.md, and chapters/.",
    )
    args = parser.parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    try:
        target = find_target(book_folder)
        counts = find_drafts(book_folder)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(build_report(book_folder, target, counts))
    return 0
