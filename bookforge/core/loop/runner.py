"""Main loop execution control and persistence."""

from __future__ import annotations

import json
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path

from bookforge.core import chain as check_continuity_chain
from bookforge.core import narrative_quality
from bookforge.core import rhythm as check_chapter_rhythm
from bookforge.core import validator as context_validator
from bookforge.core.issue import IssueCategory, ManuscriptIssue, Severity

from bookforge.core.loop.state import (
    StyleIssue,
    LengthState,
    soft_length_bounds,
    build_length_state,
)
from bookforge.core.loop.classify import (
    mode_for_status,
    action_chapter,
    hard_issue_chapters,
    choose_expansion_chapter,
    choose_rebalance_chapter,
    _message_of,
    classify,
)

STYLE_TERMS = (
    context_validator.BANNED_AI_ECHO_WORDS
    + context_validator.MODERN_OR_CLINICAL_WORDS
    + context_validator.FORBIDDEN_LENGTH_LANGUAGE
    + context_validator.UNRESOLVED_MARKERS
    + context_validator.INTERNAL_MONOLOGUE_PHRASES
)
STYLE_SCAN_RE = re.compile("|".join(re.escape(term) for term in STYLE_TERMS), re.IGNORECASE)


def scan_style_issues(book_folder: Path) -> list[StyleIssue]:
    chapters = context_validator.discover_chapters(book_folder)
    issues: list[StyleIssue] = []
    for chapter in chapters:
        if chapter.draft.exists():
            try:
                content = chapter.draft.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for index, line in enumerate(content.splitlines(), start=1):
                if STYLE_SCAN_RE.search(line) or context_validator.DIALOGUE_TAG_RE.search(line):
                    issues.append(StyleIssue(path=chapter.draft, line_number=index, line=line.strip()))
    return issues


def load_persistent_repairs(book_folder: Path) -> dict[str, int]:
    state_file = book_folder / "state" / "loop.json"
    legacy_file = book_folder / "loop-state.json"
    
    target_file = state_file
    if not state_file.exists() and legacy_file.exists():
        target_file = legacy_file
        
    if not target_file.exists():
        return {}
    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
        return data.get("repair_attempts", {})
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}


def save_persistent_repairs(book_folder: Path, repair_attempts: dict[str, int], status: str) -> None:
    state_dir = book_folder / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "loop.json"
    
    data = {}
    legacy_file = book_folder / "loop-state.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass
    elif legacy_file.exists():
        try:
            data = json.loads(legacy_file.read_text(encoding="utf-8"))
            legacy_file.unlink(missing_ok=True)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            pass
            
    data["repair_attempts"] = repair_attempts
    data["last_run"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    data["last_status"] = status
    try:
        state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass


def _required_book_file_issues(book_folder: Path) -> tuple[list[str], list[object]]:
    """Preserve validator issue severity so soft book warnings do not block the loop."""
    passes, _failures = context_validator.validate_required_book_files(book_folder)
    return passes, list(context_validator.validate_required_book_file_issues(book_folder))


def run_loop_check(
    book_folder: Path,
    target_min: int | None = None,
    target_max: int | None = None,
    cli_attempts: dict[str, int] | None = None,
    max_repair_attempts: int = 3,
) -> tuple[str, str, str]:
    if cli_attempts is None:
        cli_attempts = {}
    persistent_attempts = load_persistent_repairs(book_folder)
    repair_attempts = {**persistent_attempts, **cli_attempts}

    length_state = build_length_state(book_folder, target_min, target_max)
    _book_passes, book_failures = _required_book_file_issues(book_folder)

    try:
        phase_sections = context_validator.parse_phase_chapters(book_folder)
    except (yaml.YAMLError, OSError, KeyError, AttributeError):
        phase_sections = {}
    chapters = context_validator.discover_chapters(book_folder)
    reports = [context_validator.validate_chapter(chapter, phase_sections) for chapter in chapters]

    style_issues = scan_style_issues(book_folder)

    continuity_failures: list[str] = []
    for chapter in chapters:
        if chapter.draft.exists() and chapter.draft.read_text(encoding="utf-8").strip():
            continuity_path = chapter.continuity_out
            if not continuity_path.exists():
                continuity_failures.append(f"{chapter.slug} is missing continuity-out.md")
            else:
                errors = check_continuity_chain.check_continuity_out_content(continuity_path)
                if errors:
                    continuity_failures.append(f"{chapter.slug} has invalid continuity-out.md: {', '.join(errors)}")

    narrative_issues = narrative_quality.analyze(book_folder).issues
    try:
        rhythm_report = check_chapter_rhythm.analyze(book_folder)
        rhythm_issues = rhythm_report.issues
    except (OSError, ValueError, KeyError, AttributeError, TypeError, UnicodeDecodeError):
        rhythm_report = None
        rhythm_issues = []

    status, reason = classify(
        length_state,
        book_failures,
        reports,
        style_issues,
        repair_attempts,
        max_repair_attempts,
        continuity_failures,
        narrative_issues,
        rhythm_issues,
    )

    context_problem_chapters = hard_issue_chapters(reports)
    if status == "NEEDS_CONTEXT_REPAIR" and context_problem_chapters:
        current_repairing = context_problem_chapters[0]
        repair_attempts[current_repairing] = repair_attempts.get(current_repairing, 0) + 1

    for report in reports:
        slug = report.chapter.slug
        if not report.failures and not report.warnings and slug in repair_attempts:
            repair_attempts[slug] = 0

    save_persistent_repairs(book_folder, repair_attempts, status)

    book_failure_messages = [_message_of(issue) for issue in book_failures]
    expansion_chapter = choose_expansion_chapter(reports, length_state.counts)
    rebalance_chapter = choose_rebalance_chapter(rhythm_report or length_state.counts)
    prompt_mode = mode_for_status(status)
    next_chapter = action_chapter(
        status,
        context_problem_chapters,
        expansion_chapter,
        style_issues,
        continuity_failures,
        rebalance_chapter,
    )

    decision = "STOP" if status in ("DONE", "DONE_WITH_WARNINGS", "BLOCKED") else "CONTINUE"
    if status == "DONE":
        next_action = "No manuscript action needed. Report final status to the user."
    elif status == "DONE_WITH_WARNINGS":
        next_action = "Stop autonomous editing and report remaining soft warnings to the user."
    elif status == "NEEDS_BOOK_REPAIR":
        next_action = "Repair book-level rulebook, source, or configuration issues before chapter work."
    elif status == "NEEDS_CHAPTER_REVIEW":
        next_action = f"Read the compiled chapter and write `{next_chapter or context_problem_chapters[0]}/chapter-review.md` before continuing."
    elif status == "NEEDS_CONTEXT_REPAIR":
        next_action = f"Repair context issues in `{context_problem_chapters[0]}` before length or style work."
    elif status == "NEEDS_CONTINUITY_REPAIR":
        next_action = f"Write or repair the missing/invalid `continuity-out.md` for `{next_chapter}`."
    elif status == "NEEDS_STYLE_REPAIR":
        next_action = f"Rewrite flagged style line `{style_issues[0].path}:{style_issues[0].line_number}`."
    elif status in ("NEEDS_PACING_REBALANCE", "NEEDS_RHYTHM_REBALANCE"):
        next_action = f"Run narrative rebalance repair on `{next_chapter}` by trimming repeated procedural pressure."
    elif status == "NEEDS_EXPANSION":
        next_action = f"Expand `{expansion_chapter}` from its approved scene breakdown."
    else:
        next_action = "Stop and ask the user for direction."

    soft_min, soft_max = soft_length_bounds(length_state.target_min, length_state.target_max)
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
        f"- **Contract Range:** {length_state.target_min:,} - {length_state.target_max:,}",
        f"- **Soft Range:** {soft_min:,} - {soft_max:,}",
    ]

    if book_failure_messages:
        lines.extend(["", "## Book-Level Issues", ""])
        lines.extend(f"- {message}" for message in book_failure_messages)

    if rhythm_report and rhythm_report.issues:
        lines.extend(["", "## Rhythm Notes", ""])
        for issue in rhythm_report.issues:
            lines.append(f"- {_message_of(issue)}")

    if narrative_issues:
        lines.extend(["", "## Narrative Quality Notes", ""])
        for issue in narrative_issues[:12]:
            chapter = getattr(issue, "chapter", "book")
            dimension = getattr(issue, "dimension", getattr(getattr(issue, "category", ""), "name", "Narrative"))
            lines.append(f"- {chapter}: {dimension} - {_message_of(issue)}")

    return status, reason, "\n".join(lines)


def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Autonomous Manuscript Loop: reports next agent action."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/book-example",
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

    status, _reason, report = run_loop_check(
        book_folder=book_folder,
        target_min=args.target_min,
        target_max=args.target_max,
        cli_attempts=cli_attempts,
        max_repair_attempts=args.max_repair_attempts,
    )
    print(report)
    return 2 if status == "BLOCKED" else 0
