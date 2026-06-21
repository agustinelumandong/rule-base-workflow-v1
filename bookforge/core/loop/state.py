"""Length and pacing target state representation for the loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from bookforge.core import length as length_checker


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
    except (OSError, UnicodeDecodeError):
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
