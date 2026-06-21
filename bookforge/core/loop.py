#!/usr/bin/env python3
"""BookForge Loop Controller Core Module."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from bookforge.core import chain as check_continuity_chain
from bookforge.core import length as length_checker
from bookforge.core import narrative_quality
from bookforge.core import rhythm as check_chapter_rhythm
from bookforge.core import validator as context_validator
from bookforge.core.issue import IssueCategory, ManuscriptIssue, Severity


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


def soft_length_bounds(target_min: int, target_max: int) -> tuple[int, int]:
    soft_margin = int(target_min * 0.01)
    return target_min - soft_margin, target_max + soft_margin


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


def load_persistent_repairs(book_folder: Path) -> dict[str, int]:
    state_file = book_folder / "state" / "loop.json"
    legacy_file = book_folder / "loop-state.json"
    
    # Backward compatibility fallback
    target_file = state_file
    if not state_file.exists() and legacy_file.exists():
        target_file = legacy_file
        
    if not target_file.exists():
        return {}
    try:
        data = json.loads(target_file.read_text(encoding="utf-8"))
        return data.get("repair_attempts", {})
    except Exception:
        return {}


def save_persistent_repairs(book_folder: Path, repair_attempts: dict[str, int], status: str) -> None:
    state_dir = book_folder / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "loop.json"
    
    # Read existing if any (to preserve other keys like last_run/last_status)
    data = {}
    legacy_file = book_folder / "loop-state.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    elif legacy_file.exists():
        try:
            data = json.loads(legacy_file.read_text(encoding="utf-8"))
            # Clean up legacy file
            legacy_file.unlink(missing_ok=True)
        except Exception:
            pass
            
    data["repair_attempts"] = repair_attempts
    data["last_run"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    data["last_status"] = status
    try:
        state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass



def _required_book_file_issues(book_folder: Path) -> tuple[list[str], list[object]]:
    result = context_validator.validate_required_book_files(book_folder)
    if isinstance(result, tuple) and len(result) == 2 and all(isinstance(item, list) for item in result):
        passes, failures = result
        issues = [
            ManuscriptIssue(
                severity=Severity.HARD,
                category=IssueCategory.CONTEXT,
                message=failure,
            )
            for failure in failures
        ]
        return passes, issues
    return [], list(result)


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
    except Exception:
        phase_sections = {}
    chapters = context_validator.discover_chapters(book_folder)
    reports = [context_validator.validate_chapter(chapter, phase_sections) for chapter in chapters]

    style_issues = scan_style_issues(book_folder)

    continuity_failures: list[str] = []
    for chapter in chapters:
        if chapter.draft.exists() and chapter.draft.read_text(encoding="utf-8").strip():
            continuity_path = chapter.folder / "continuity-out.md"
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
    except Exception:
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
    elif status == "NEEDS_CONTEXT_REPAIR":
        next_action = f"Repair context issues in `{context_problem_chapters[0]}` before length or style work."
    elif status == "NEEDS_CONTINUITY_REPAIR":
        next_action = f"Write or repair the missing/invalid `continuity-out.md` for `{next_chapter}`."
    elif status == "NEEDS_STYLE_REPAIR":
        next_action = f"Rewrite flagged style line `{style_issues[0].path}:{style_issues[0].line_number}`."
    elif status == "NEEDS_PACING_REBALANCE":
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
