#!/usr/bin/env python3
"""BookForge Loop Controller Core Module."""

from __future__ import annotations

import re
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from bookforge.core import validator as context_validator
from bookforge.core import length as length_checker
from bookforge.core import rhythm as check_chapter_rhythm
from bookforge.core import chain as check_continuity_chain

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
    target_source: str
    target_evidence: str
    target_min: int
    target_max: int
    total_words: int
    remaining_to_min: int
    counts: list[length_checker.DraftCount]


def build_length_state(book_folder: Path, target_min_arg: int | None, target_max_arg: int | None) -> LengthState:
    target = length_checker.find_target(book_folder)
    target_min = target_min_arg or target.words
    target_max = target_max_arg or target_min + 1000
    if target_min <= 0:
        raise RuntimeError("--target-min must be greater than zero.")
    if target_max < target_min:
        raise RuntimeError("--target-max must be greater than or equal to --target-min.")

    try:
        counts = length_checker.find_drafts(book_folder)
    except Exception:
        counts = []
    total_words = sum(item.words for item in counts)
    return LengthState(
        target=target.words,
        target_source=target.source,
        target_evidence=target.evidence,
        target_min=target_min,
        target_max=target_max,
        total_words=total_words,
        remaining_to_min=max(target_min - total_words, 0),
        counts=counts,
    )


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


def mode_for_status(status: str) -> str:
    if status in ("NEEDS_CONTEXT_REPAIR", "NEEDS_CONTINUITY_REPAIR"):
        return "repair"
    if status == "NEEDS_STYLE_REPAIR":
        return "style"
    if status == "NEEDS_EXPANSION":
        return "expansion"
    if status == "DONE":
        return "final"
    return "blocked"


def action_chapter(
    status: str,
    context_problem_chapters: list[str],
    expansion_chapter: str,
    style_issues: list[StyleIssue],
    continuity_failures: list[str],
) -> str | None:
    if status == "NEEDS_CONTEXT_REPAIR" and context_problem_chapters:
        return context_problem_chapters[0]
    if status == "NEEDS_CONTINUITY_REPAIR" and continuity_failures:
        match = re.match(r"(chapter-\d+|epilogue)", continuity_failures[0])
        if match:
            return match.group(1)
    if status == "NEEDS_EXPANSION" and expansion_chapter != "NONE":
        return expansion_chapter
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


def classify(
    length_state: LengthState,
    book_failures: list[str],
    reports: list[context_validator.ChapterReport],
    style_issues: list[StyleIssue],
    repair_attempts: dict[str, int],
    max_repair_attempts: int,
    continuity_failures: list[str],
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
    if continuity_failures:
        return "NEEDS_CONTINUITY_REPAIR", f"Continuity chain check failed: {continuity_failures[0]}."
    if style_issues:
        return "NEEDS_STYLE_REPAIR", "Style-risk scan found flagged draft lines."
    if length_state.total_words < length_state.target_min:
        return "NEEDS_EXPANSION", "Manuscript is below target minimum."
    if length_state.total_words > length_state.target_max:
        return "BLOCKED", "Manuscript is above target maximum; request trim/review before continuing."
    return "DONE", "Manuscript is within target range with clean deterministic checks."


def load_persistent_repairs(book_folder: Path) -> dict[str, int]:
    state_file = book_folder / "loop-state.json"
    if not state_file.exists():
        return {}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return data.get("repair_attempts", {})
    except Exception:
        return {}


def save_persistent_repairs(book_folder: Path, repair_attempts: dict[str, int], status: str) -> None:
    state_file = book_folder / "loop-state.json"
    data = {
        "repair_attempts": repair_attempts,
        "last_run": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "last_status": status
    }
    try:
        state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def run_loop_check(
    book_folder: Path,
    target_min: int | None = None,
    target_max: int | None = None,
    cli_attempts: dict[str, int] | None = None,
    max_repair_attempts: int = 3
) -> tuple[str, str, str]:
    if cli_attempts is None:
        cli_attempts = {}
    persistent_attempts = load_persistent_repairs(book_folder)
    repair_attempts = {**persistent_attempts, **cli_attempts}

    length_state = build_length_state(book_folder, target_min, target_max)
    book_passes, book_failures, reports = context_validator.validate_required_book_files(book_folder), [], []
    
    phase_sections = context_validator.parse_phase_chapters(book_folder)
    chapters = context_validator.discover_chapters(book_folder)
    reports = [context_validator.validate_chapter(chapter, phase_sections) for chapter in chapters]
    book_passes, book_failures = context_validator.validate_required_book_files(book_folder)

    style_issues = scan_style_issues(book_folder)

    continuity_failures = []
    for chapter in chapters:
        if chapter.draft.exists() and chapter.draft.read_text(encoding="utf-8").strip():
            continuity_path = chapter.folder / "continuity-out.md"
            if not continuity_path.exists():
                continuity_failures.append(f"{chapter.slug} is missing continuity-out.md")
            else:
                errors = check_continuity_chain.check_continuity_out_content(continuity_path)
                if errors:
                    continuity_failures.append(f"{chapter.slug} has invalid continuity-out.md: {', '.join(errors)}")

    status, reason = classify(
        length_state,
        book_failures,
        reports,
        style_issues,
        repair_attempts,
        max_repair_attempts,
        continuity_failures,
    )

    context_problem_chapters = issue_chapters(reports)
    if status == "NEEDS_CONTEXT_REPAIR" and context_problem_chapters:
        current_repairing = context_problem_chapters[0]
        repair_attempts[current_repairing] = repair_attempts.get(current_repairing, 0) + 1

    for report in reports:
        slug = report.chapter.slug
        if not report.failures and not report.warnings and slug in repair_attempts:
            repair_attempts[slug] = 0

    save_persistent_repairs(book_folder, repair_attempts, status)

    # Render loop report output
    context_status = context_validator.overall_status(book_failures, reports)
    expansion_chapter = choose_expansion_chapter(reports, length_state.counts)
    prompt_mode = mode_for_status(status)
    next_chapter = action_chapter(status, context_problem_chapters, expansion_chapter, style_issues, continuity_failures)
    
    packet_command = f"bf run-loop {book_folder} (generates packet automatically)"
    budget_command = f"bf run-loop {book_folder} (budgets context automatically)"

    decision = "STOP" if status in ("DONE", "BLOCKED") else "CONTINUE"
    if status == "DONE":
        next_action = "No manuscript action needed. Report final status to the user."
    elif status == "NEEDS_CONTEXT_REPAIR":
        next_action = f"Repair context issues in `{context_problem_chapters[0]}` before length or style work."
    elif status == "NEEDS_CONTINUITY_REPAIR":
        next_action = f"Write or repair the missing/invalid `continuity-out.md` for `{next_chapter}`."
    elif status == "NEEDS_STYLE_REPAIR":
        next_action = f"Rewrite flagged style line `{style_issues[0].path}:{style_issues[0].line_number}`."
    elif status == "NEEDS_EXPANSION":
        next_action = f"Expand `{expansion_chapter}` from its approved scene breakdown."
    else:
        next_action = "Stop and ask the user for direction."

    lines = [
        "# BookForge Loop Report",
        "",
        f"- **Status:** {status}",
        f"- **Decision:** {decision}",
        f"- **Reason:** {reason}",
        f"- **Prompt Mode:** `{prompt_mode}`",
        f"- **Next Action:** {next_action}",
        "",
        "## Length State",
        f"- **Current Words:** {length_state.total_words} / Min target: {length_state.target_min}",
    ]
    
    # Rhythm advisory
    try:
        rhythm_report = check_chapter_rhythm.analyze(book_folder)
        if rhythm_report.issues:
            lines.extend(["", "## Rhythm Notes", ""])
            for issue in rhythm_report.issues:
                lines.append(f"- {issue.message}")
    except Exception:
        pass

    return status, reason, "\n".join(lines)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Autonomous Manuscript Loop: reports next Codex action."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/tex-cade",
        help="Book folder containing chapters/ and outline source.",
    )
    parser.add_argument("--target-min", type=int, help="Override target minimum words.")
    parser.add_argument("--target-max", type=int, help="Override target maximum words.")
    parser.add_argument(
        "--repair-attempt",
        help="Comma-separated list of repair overrides (e.g. chapter-01:3).",
    )
    parser.add_argument(
        "--max-repair-attempts",
        type=int,
        default=3,
        help="Max repair attempts allowed per chapter.",
    )
    args = parser.parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    cli_attempts = {}
    if args.repair_attempt:
        for pair in args.repair_attempt.split(","):
            if ":" in pair:
                slug, val = pair.split(":", 1)
                try:
                    cli_attempts[slug] = int(val)
                except ValueError:
                    pass

    status, reason, report = run_loop_check(
        book_folder=book_folder,
        target_min=args.target_min,
        target_max=args.target_max,
        cli_attempts=cli_attempts,
        max_repair_attempts=args.max_repair_attempts
    )
    print(report)
    return 2 if status == "BLOCKED" else 0

