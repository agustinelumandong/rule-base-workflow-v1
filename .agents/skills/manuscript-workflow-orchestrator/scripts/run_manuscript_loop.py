#!/usr/bin/env python3
"""Report the next autonomous manuscript loop action.

This script does not write prose. It scans the book folder, checks deterministic
state, and tells the agent whether to stop, repair, expand, or ask for help.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_manuscript_length as length_checker  # noqa: E402
import validate_manuscript_context as context_validator  # noqa: E402


STYLE_TERMS = (
    context_validator.BANNED_AI_ECHO_WORDS
    + context_validator.MODERN_OR_CLINICAL_WORDS
    + context_validator.FORBIDDEN_LENGTH_LANGUAGE
    + context_validator.UNRESOLVED_MARKERS
    + context_validator.INTERNAL_MONOLOGUE_PHRASES
)
STYLE_SCAN_RE = re.compile("|".join(re.escape(term) for term in STYLE_TERMS), re.IGNORECASE)


@dataclass(frozen=True)
class StyleIssue:
    path: Path
    line_number: int
    line: str


@dataclass(frozen=True)
class LengthState:
    target: int
    target_min: int
    target_max: int
    total_words: int
    remaining_to_min: int
    counts: list[length_checker.DraftCount]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the manuscript loop scanner and report the next agent action."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/tex-cade",
        help="Book folder containing phase-0.md, rulebook.md, and chapters/.",
    )
    parser.add_argument(
        "--target-min",
        type=int,
        help="Minimum acceptable manuscript words. Defaults to detected book target.",
    )
    parser.add_argument(
        "--target-max",
        type=int,
        help="Maximum preferred manuscript words. Defaults to target-min + 1000.",
    )
    parser.add_argument(
        "--repair-attempt",
        action="append",
        default=[],
        metavar="CHAPTER=COUNT",
        help="Record current repair attempts for a chapter, e.g. chapter-08=2.",
    )
    parser.add_argument(
        "--max-repair-attempts",
        type=int,
        default=3,
        help="Block if the same chapter reaches this many context repair attempts.",
    )
    return parser.parse_args()


def parse_repair_attempts(raw_attempts: list[str]) -> dict[str, int]:
    attempts: dict[str, int] = {}
    for raw in raw_attempts:
        if "=" not in raw:
            raise RuntimeError(f"Invalid --repair-attempt value `{raw}`; expected CHAPTER=COUNT.")
        chapter, count_text = raw.split("=", 1)
        chapter = chapter.strip()
        try:
            count = int(count_text.strip())
        except ValueError as error:
            raise RuntimeError(f"Invalid repair count in `{raw}`.") from error
        if not chapter or count < 0:
            raise RuntimeError(f"Invalid --repair-attempt value `{raw}`.")
        attempts[chapter] = count
    return attempts


def build_length_state(book_folder: Path, target_min_arg: int | None, target_max_arg: int | None) -> LengthState:
    target = length_checker.find_target(book_folder)
    target_min = target_min_arg or target
    target_max = target_max_arg or target_min + 1000
    if target_min <= 0:
        raise RuntimeError("--target-min must be greater than zero.")
    if target_max < target_min:
        raise RuntimeError("--target-max must be greater than or equal to --target-min.")

    counts = length_checker.find_drafts(book_folder)
    total_words = sum(item.words for item in counts)
    return LengthState(
        target=target,
        target_min=target_min,
        target_max=target_max,
        total_words=total_words,
        remaining_to_min=max(target_min - total_words, 0),
        counts=counts,
    )


def build_context_reports(book_folder: Path) -> tuple[list[str], list[str], list[context_validator.ChapterReport]]:
    book_passes, book_failures = context_validator.validate_required_book_files(book_folder)
    phase_sections = context_validator.parse_phase_chapters(book_folder)
    chapters = context_validator.discover_chapters(book_folder)
    reports = [context_validator.validate_chapter(chapter, phase_sections) for chapter in chapters]
    return book_passes, book_failures, reports


def scan_style_issues(book_folder: Path) -> list[StyleIssue]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        return []

    draft_paths = sorted(chapters_root.glob("chapter-*/chapter-*.md"), key=context_validator.chapter_sort_key)
    epilogue_path = chapters_root / "epilogue" / "epilogue.md"
    if epilogue_path.exists():
        draft_paths.append(epilogue_path)

    issues: list[StyleIssue] = []
    for path in draft_paths:
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if STYLE_SCAN_RE.search(line) or context_validator.DIALOGUE_TAG_RE.search(line):
                issues.append(StyleIssue(path=path, line_number=index, line=line.strip()))
    return issues


def chapter_word_map(counts: list[length_checker.DraftCount]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for item in counts:
        if item.label == "Epilogue":
            mapping["epilogue"] = item.words
        else:
            match = re.search(r"Chapter\s+(\d+)", item.label)
            if match:
                mapping[f"chapter-{int(match.group(1)):02d}"] = item.words
    return mapping


def issue_chapters(reports: list[context_validator.ChapterReport]) -> list[str]:
    chapters: list[str] = []
    for report in reports:
        if report.failures or report.warnings:
            chapters.append(report.chapter.slug)
    return chapters


def choose_expansion_chapter(
    reports: list[context_validator.ChapterReport],
    counts: list[length_checker.DraftCount],
) -> str:
    words_by_chapter = chapter_word_map(counts)
    valid_slugs = [report.chapter.slug for report in reports if report.status == "PASS" and report.chapter.slug != "epilogue"]
    if not valid_slugs:
        return "NONE"
    return min(valid_slugs, key=lambda slug: words_by_chapter.get(slug, 10**9))


def mode_for_status(status: str) -> str:
    if status == "NEEDS_CONTEXT_REPAIR":
        return "repair"
    if status == "NEEDS_STYLE_REPAIR":
        return "style"
    if status == "NEEDS_EXPANSION":
        return "expansion"
    if status == "DONE":
        return "final"
    return "blocked"


def action_chapter(status: str, context_problem_chapters: list[str], expansion_chapter: str, style_issues: list[StyleIssue]) -> str | None:
    if status == "NEEDS_CONTEXT_REPAIR" and context_problem_chapters:
        return context_problem_chapters[0]
    if status == "NEEDS_EXPANSION" and expansion_chapter != "NONE":
        return expansion_chapter
    if status == "NEEDS_STYLE_REPAIR" and style_issues:
        for part in style_issues[0].path.parts:
            if part.startswith("chapter-") or part == "epilogue":
                return part
    return None


def classify(
    length_state: LengthState,
    book_failures: list[str],
    reports: list[context_validator.ChapterReport],
    style_issues: list[StyleIssue],
    repair_attempts: dict[str, int],
    max_repair_attempts: int,
) -> tuple[str, str]:
    problem_chapters = issue_chapters(reports)
    repeated_blockers = [
        slug for slug in problem_chapters if repair_attempts.get(slug, 0) >= max_repair_attempts
    ]
    if book_failures:
        return "BLOCKED", "Required book files are missing or empty."
    if repeated_blockers:
        return "BLOCKED", f"Repair attempt limit reached for: {', '.join(repeated_blockers)}."
    if any(report.failures or report.warnings for report in reports):
        return "NEEDS_CONTEXT_REPAIR", "Context validator reported chapter failures or warnings."
    if style_issues:
        return "NEEDS_STYLE_REPAIR", "Style-risk scan found flagged draft lines."
    if length_state.total_words < length_state.target_min:
        return "NEEDS_EXPANSION", "Manuscript is below target minimum."
    if length_state.total_words > length_state.target_max:
        return "BLOCKED", "Manuscript is above target maximum; request trim/review before continuing."
    return "DONE", "Manuscript is within target range with clean deterministic checks."


def render_report(
    book_folder: Path,
    length_state: LengthState,
    book_passes: list[str],
    book_failures: list[str],
    reports: list[context_validator.ChapterReport],
    style_issues: list[StyleIssue],
    status: str,
    reason: str,
) -> str:
    context_status = context_validator.overall_status(book_failures, reports)
    expansion_chapter = choose_expansion_chapter(reports, length_state.counts)
    context_problem_chapters = issue_chapters(reports)
    prompt_mode = mode_for_status(status)
    next_chapter = action_chapter(status, context_problem_chapters, expansion_chapter, style_issues)
    packet_command = (
        f"python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py {book_folder} --chapter {next_chapter}"
        if next_chapter
        else "not needed"
    )
    budget_command = (
        f"python .agents/skills/manuscript-workflow-orchestrator/scripts/check_context_budget.py {book_folder} --chapter {next_chapter} --mode {prompt_mode}"
        if next_chapter and prompt_mode != "blocked"
        else "not needed"
    )

    if status == "DONE":
        decision = "STOP"
        next_action = "No manuscript action needed. Report final status to the user."
    elif status == "NEEDS_CONTEXT_REPAIR":
        decision = "CONTINUE"
        next_action = (
            f"Repair context issues in `{context_problem_chapters[0]}` before length or style work."
            if context_problem_chapters
            else "Repair context issues reported by the validator before length or style work."
        )
    elif status == "NEEDS_STYLE_REPAIR":
        decision = "CONTINUE"
        issue = style_issues[0]
        next_action = f"Rewrite flagged style line `{issue.path}:{issue.line_number}` without changing story facts."
    elif status == "NEEDS_EXPANSION":
        decision = "CONTINUE"
        next_action = (
            f"Expand `{expansion_chapter}` from its approved scene breakdown using source-supported action, consequence, dialogue pressure, setting texture, and transition."
        )
    else:
        decision = "STOP"
        next_action = "Stop and ask the user for direction before editing prose."

    lines = [
        "# Autonomous Manuscript Loop Report",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Status:** {status}",
        f"- **Decision:** {decision}",
        f"- **Reason:** {reason}",
        f"- **Prompt Mode:** `{prompt_mode}`",
        f"- **Next Action:** {next_action}",
        f"- **Context Packet Command:** `{packet_command}`",
        f"- **Context Budget Command:** `{budget_command}`",
        "",
        "## Length State",
        "",
        f"- **Detected Target:** {length_state.target}",
        f"- **Target Min:** {length_state.target_min}",
        f"- **Target Max:** {length_state.target_max}",
        f"- **Current Words:** {length_state.total_words}",
        f"- **Remaining To Min:** {length_state.remaining_to_min}",
        "",
        "| Section | Words |",
        "| --- | ---: |",
    ]
    for item in length_state.counts:
        lines.append(f"| {item.label} | {item.words} |")

    lines.extend(
        [
            "",
            "## Context State",
            "",
            f"- **Context Status:** {context_status}",
        ]
    )
    if context_problem_chapters:
        lines.append(f"- **Chapters Needing Context Repair:** {', '.join(context_problem_chapters)}")
    else:
        lines.append("- **Chapters Needing Context Repair:** none")
    for failure in book_failures:
        lines.append(f"- FAIL: {failure}")
    for report in reports:
        for failure in report.failures:
            lines.append(f"- FAIL `{report.chapter.slug}`: {failure}")
        for warning in report.warnings:
            lines.append(f"- WARN `{report.chapter.slug}`: {warning}")

    lines.extend(["", "## Style State", ""])
    if style_issues:
        lines.append(f"- **Style Status:** WARN")
        for issue in style_issues[:10]:
            lines.append(f"- `{issue.path}:{issue.line_number}`: {issue.line}")
        if len(style_issues) > 10:
            lines.append(f"- ...and {len(style_issues) - 10} more style issue(s).")
    else:
        lines.append("- **Style Status:** clean")

    lines.extend(
        [
            "",
            "## Loop Rules",
            "",
            "- Codex performs prose edits; this script only reports state and next action.",
            "- Build or refresh the context packet before chapter-level prose edits.",
            "- Fix context before style; fix style before expansion.",
            "- Expand only from approved source files and scene breakdowns.",
            "- Never pad prose, invent unsupported story, or force beat/scene word counts.",
            "- Stop if status is `DONE` or `BLOCKED`.",
        ]
    )
    return "\n".join(lines)


def render_blocked_report(book_folder: Path, reason: str) -> str:
    return "\n".join(
        [
            "# Autonomous Manuscript Loop Report",
            "",
            f"- **Book Folder:** `{book_folder}`",
            "- **Status:** BLOCKED",
            "- **Decision:** STOP",
            f"- **Reason:** {reason}",
            "- **Prompt Mode:** `blocked`",
            "- **Next Action:** Restore or create the missing source material before drafting, repair, style, or length work.",
            "",
            "## Loop Rules",
            "",
            "- Codex performs prose edits; this script only reports state and next action.",
            "- Required source files must exist before autonomous work can continue.",
            "- After sources exist, build context packets before chapter-level prose edits.",
            "- Never pad prose, invent unsupported story, or force beat/scene word counts.",
        ]
    )


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(render_blocked_report(book_folder, "Book folder not found."))
        return 2

    try:
        repair_attempts = parse_repair_attempts(args.repair_attempt)
        length_state = build_length_state(book_folder, args.target_min, args.target_max)
        book_passes, book_failures, reports = build_context_reports(book_folder)
        style_issues = scan_style_issues(book_folder)
        status, reason = classify(
            length_state,
            book_failures,
            reports,
            style_issues,
            repair_attempts,
            args.max_repair_attempts,
        )
    except RuntimeError as error:
        print(render_blocked_report(book_folder, str(error)))
        return 2

    print(render_report(book_folder, length_state, book_passes, book_failures, reports, style_issues, status, reason))
    return 2 if status == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
