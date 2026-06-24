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

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


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
    continuity_path = chapter.continuity_out
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


def check_equipment_state_contradictions(text: str) -> list[str]:
    """Detect items lost/damaged reappearing without acquisition scene."""
    findings: list[str] = []

    lost_patterns = [
        (r"(?:hat|帽子)\s+(?:fell|was shot|blew|knocked|lifted|went)\s+(?:off|away|gone)",
         r"(?:hat|帽子)"),
        (r"(?:rifle|gun|colt|winchester|revolver|pistol)\s+(?:fell|was dropped|lost|gone|left behind)",
         r"(?:rifle|gun|colt|winchester|revolver|pistol)"),
        (r"(?:saddle|pack|bag|coat|jacket|vest)\s+(?:fell|was lost|left|gone|lost on)",
         r"(?:saddle|pack|bag|coat|jacket|vest)"),
    ]

    paragraphs = re.split(r"\n\s*\n", text.strip())
    lost_items: dict[str, int] = {}

    for i, para in enumerate(paragraphs):
        para_lower = para.lower()
        for pattern, item_pattern in lost_patterns:
            if re.search(pattern, para_lower):
                match = re.search(item_pattern, para_lower)
                if match:
                    lost_items[match.group(0)] = i

        for item, lost_idx in list(lost_items.items()):
            if i <= lost_idx:
                continue
            if re.search(rf"\b{re.escape(item)}\b", para_lower):
                has_acquisition = any(
                    kw in para_lower
                    for kw in ["found a", "picked up", "bought", "borrowed", "replacement", "new " + item, "got a " + item]
                )
                if not has_acquisition:
                    snippet = para[:120]
                    findings.append(
                        f"Continuity warning: '{item}' was lost/damaged at paragraph {lost_idx + 1} "
                        f"but reappears at paragraph {i + 1} without an acquisition scene: '{snippet}...'"
                    )
                    if len(findings) >= 5:
                        return findings

    return findings


def check_dead_character_actions(text: str) -> list[str]:
    """Detect characters performing actions after being described as dead/dying."""
    findings: list[str] = []

    death_descriptions = [
        r"dead\b",
        r"died\b",
        r"killed\b",
        r"corpse\b",
        r"lifeless\b",
        r"no longer breathing\b",
        r"drowned\b",
        r"bled out\b",
        r"fell dead\b",
    ]

    paragraphs = re.split(r"\n\s*\n", text.strip())
    dead_characters: dict[str, int] = {}

    for i, para in enumerate(paragraphs):
        para_lower = para.lower()
        for death_pattern in death_descriptions:
            death_match = re.search(
                rf"(\b[A-Z][a-z]+\b).{{0,40}}{death_pattern}",
                para_lower,
            )
            if death_match:
                char_name = death_match.group(1)
                if char_name.lower() not in ("he", "she", "they", "the", "a", "an"):
                    dead_characters[char_name] = i

        for char_name, death_idx in list(dead_characters.items()):
            if i <= death_idx:
                continue
            action_verbs = (
                r"\b(?:said|spoke|answered|replied|told|called|shouted|whispered|"
                r"moved|walked|ran|rode|climbed|stood|sat|reached|grabbed|fired|shot|"
                r"grabbed|pulled|pushed|lifted|carried|dragged|drove|led|followed|"
                r"reached|checked|examined|looked|stared|watched|turned|faced)\b"
            )
            if re.search(rf"\b{re.escape(char_name)}\b.{0,60}{action_verbs}", para_lower):
                snippet = para[:120]
                findings.append(
                    f"Continuity error: '{char_name}' performs action at paragraph {i + 1} "
                    f"but was described as dead/dying at paragraph {death_idx + 1}: '{snippet}...'"
                )
                if len(findings) >= 5:
                    return findings

    return findings


def check_character_behavior_contradictions(text: str) -> list[str]:
    """Detect same character described with opposite behaviors in close proximity."""
    findings: list[str] = []

    behavior_pairs = [
        (r"looked?\s+(?:toward|at|over|back)", r"never\s+(?:looked?|turned|glanced)"),
        (r"spoke|said|answered|replied", r"silent|said nothing|didn(?:'t|t)\s+speak|never\s+(?:spoke|said|answered)"),
        r"(?:always|kept|never\s+left)", r"(?:left|abandoned|walked away|forgot)",
    ]

    paragraphs = re.split(r"\n\s*\n", text.strip())

    for i in range(len(paragraphs) - 1):
        para1 = paragraphs[i].lower()
        para2 = paragraphs[i + 1].lower()

        if abs(len(para1.split()) - len(para2.split())) > 20:
            continue

        subjects = re.findall(r"\b([A-Z][a-z]+)\b", paragraphs[i])
        for subject in subjects:
            if subject.lower() in ("he", "she", "they", "the", "a", "an", "his", "her"):
                continue
            if re.search(rf"\b{re.escape(subject.lower())}\b", para2):
                for pair in behavior_pairs:
                    if isinstance(pair, tuple):
                        pattern1, pattern2 = pair
                    else:
                        continue
                    if re.search(pattern1, para1) and re.search(pattern2, para2):
                        snippet = paragraphs[i + 1][:100]
                        findings.append(
                            f"Behavior contradiction: '{subject}' at paragraph {i + 1} vs {i + 2}: "
                            f"'{snippet}...'"
                        )
                        if len(findings) >= 5:
                            return findings

    return findings


def check_wound_direction_consistency(text: str) -> list[str]:
    """Flag back-entry wound descriptions when shooter is positioned in front."""
    findings: list[str] = []

    wound_patterns = [
        r"(?:ball|bullet|shot|wound)\s+.*(?:in|entered)\s+.*(?:low\s+and\s+back|from\s+behind|in\s+the\s+back)",
        r"(?:entry|entered|going\s+in)\s+.*(?:back|rear|behind)",
    ]

    front_shooter_patterns = [
        r"(?:facing|faced|toward|in\s+front\s+of|from\s+(?:the\s+)?(?:porch|front|yard|door))",
        r"(?:kneeling|standing|sitting|lying)\s+.*(?:facing|toward|looking\s+at)",
    ]

    paragraphs = re.split(r"\n\s*\n", text.strip())

    for i, para in enumerate(paragraphs):
        para_lower = para.lower()

        has_front_shooter = any(
            re.search(p, para_lower) for p in front_shooter_patterns
        )
        has_back_wound = any(
            re.search(p, para_lower) for p in wound_patterns
        )

        if has_front_shooter and has_back_wound:
            snippet = para[:120]
            findings.append(
                f"Wound direction warning: Front-positioned shooter with back-entry wound at paragraph {i + 1}: "
                f"'{snippet}...'"
            )
            if len(findings) >= 3:
                return findings

    return findings
