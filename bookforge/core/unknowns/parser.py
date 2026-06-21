"""Parsing helpers and context readers for Unknowns resolver."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+)$")


class BookContext(NamedTuple):
    genre: str          # e.g. "Classic Western"
    setting: str        # e.g. "Powder River country, Wyoming"
    time_period: str    # e.g. "1800s"
    title: str          # book title
    raw: str            # full rulebook text


def _find_section_bounds(text: str, section_aliases: tuple[str, ...]) -> tuple[int, int, int]:
    """Return (heading_start, body_start, body_end) for the named section.

    Returns (-1, -1, -1) if not found.
    """
    aliases = {a.strip().lower() for a in section_aliases}
    headings = list(_HEADING_RE.finditer(text))
    for idx, m in enumerate(headings):
        title = m.group(2).strip().lower()
        if title not in aliases:
            continue
        level = len(m.group(1))
        body_start = m.end()
        body_end = len(text)
        for nxt in headings[idx + 1:]:
            if len(nxt.group(1)) <= level:
                body_end = nxt.start()
                break
        return m.start(), body_start, body_end
    return -1, -1, -1


def parse_unknowns(rulebook_text: str) -> list[str]:
    """Return each bullet item in the ## Unknowns section as a string."""
    _, body_start, body_end = _find_section_bounds(rulebook_text, ("Unknowns",))
    if body_start == -1:
        return []
    section_body = rulebook_text[body_start:body_end]
    items: list[str] = []
    for line in section_body.splitlines():
        m = _BULLET_RE.match(line)
        if m:
            item = m.group(1).strip()
            if item:
                items.append(item)
    return items


def parse_resolved_answers(rulebook_text: str) -> dict[str, str]:
    """Return {question_text: answer_text} from the ## Resolved Unknowns section."""
    _, body_start, body_end = _find_section_bounds(rulebook_text, ("Resolved Unknowns",))
    if body_start == -1:
        return {}
    section_body = rulebook_text[body_start:body_end]
    answers: dict[str, str] = {}
    current_question: str | None = None
    for line in section_body.splitlines():
        q_match = re.match(r"^\s*[-*]\s+\*\*Q:\*\*\s+(.+)$", line)
        a_match = re.match(r"^\s+[-*]\s+\*\*A:\*\*\s+(.+)$", line)
        if q_match:
            current_question = q_match.group(1).strip()
        elif a_match and current_question:
            answers[current_question] = a_match.group(1).strip()
            current_question = None
    return answers


def _extract_field(text: str, *labels: str) -> str:
    """Pull the value after any of the given bold-label patterns, e.g. **Genre/Length Target:**"""
    for label in labels:
        pattern = rf"\*\*{re.escape(label)}[:/]?\*\*\s*(.+)"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).split("\n")[0].strip().rstrip(".")
    return ""


def read_book_context(rulebook_text: str) -> BookContext:
    genre = _extract_field(rulebook_text, "Genre/Length Target", "Genre", "Subgenre")
    setting = _extract_field(rulebook_text, "Primary Setting", "Setting", "Region")
    time_period = _extract_field(rulebook_text, "Time Period", "Era", "Period")
    title_m = re.match(r"#\s+(.+)", rulebook_text)
    title = title_m.group(1).strip() if title_m else "Unknown Book"
    return BookContext(
        genre=genre or "Western",
        setting=setting or "frontier",
        time_period=time_period or "1800s",
        title=title,
        raw=rulebook_text,
    )
