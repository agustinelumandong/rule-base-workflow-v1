"""Data models for narrative quality reporting."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from bookforge.core.issue import ManuscriptIssue

@dataclass(frozen=True)
class NarrativeIssue:
    chapter: str
    dimension: str
    level: str
    message: str


@dataclass(frozen=True)
class NarrativeReport:
    book_folder: Path
    issues: tuple[ManuscriptIssue, ...]
