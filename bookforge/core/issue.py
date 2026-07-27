#!/usr/bin/env python3
"""BookForge Issue Types and Structures.

Unified issue representation for the manuscript loop with severity classification,
fingerprinting for deduplication, and structured decision types.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Optional


class Severity(Enum):
    HARD = auto()
    SOFT = auto()
    INFO = auto()


class IssueCategory(Enum):
    CONTEXT = auto()
    STYLE = auto()
    LENGTH = auto()
    RHYTHM = auto()
    NARRATIVE = auto()
    CONTINUITY = auto()


class IssueStatus(Enum):
    OPEN = auto()
    RESOLVED = auto()
    ACCEPTED = auto()
    IGNORED = auto()


def compute_fingerprint(rule_id: str | None, file: Path | None, line: int | None, span: str | None) -> str:
    components = [
        str(rule_id or ""),
        str(file) if file else "",
        str(line) if line else "",
        str(span) if span else "",
    ]
    return hashlib.sha256(":".join(components).encode()).hexdigest()[:16]


@dataclass(frozen=True)
class ManuscriptIssue:
    severity: Severity
    category: IssueCategory
    chapter: Optional[str] = None
    file: Optional[Path] = None
    line: Optional[int] = None
    span: Optional[str] = None
    rule_id: Optional[str] = None
    message: str = ""
    suggested_fix_type: Optional[str] = None
    fingerprint: str = ""
    first_seen_iteration: int = 0
    last_seen_iteration: int = 0
    status: IssueStatus = IssueStatus.OPEN

    def __post_init__(self) -> None:
        if not self.fingerprint:
            object.__setattr__(
                self,
                "fingerprint",
                compute_fingerprint(self.rule_id, self.file, self.line, self.span),
            )

    @property
    def is_hard(self) -> bool:
        return self.severity == Severity.HARD

    @property
    def is_soft(self) -> bool:
        return self.severity == Severity.SOFT

    @property
    def is_info(self) -> bool:
        return self.severity == Severity.INFO

    @property
    def is_book_level(self) -> bool:
        return self.chapter is None

    @property
    def is_chapter_level(self) -> bool:
        return self.chapter is not None

    def with_status(self, new_status: IssueStatus) -> ManuscriptIssue:
        return ManuscriptIssue(
            severity=self.severity,
            category=self.category,
            chapter=self.chapter,
            file=self.file,
            line=self.line,
            span=self.span,
            rule_id=self.rule_id,
            message=self.message,
            suggested_fix_type=self.suggested_fix_type,
            fingerprint=self.fingerprint,
            first_seen_iteration=self.first_seen_iteration,
            last_seen_iteration=self.last_seen_iteration,
            status=new_status,
        )

    def with_iteration(self, iteration: int) -> ManuscriptIssue:
        return ManuscriptIssue(
            severity=self.severity,
            category=self.category,
            chapter=self.chapter,
            file=self.file,
            line=self.line,
            span=self.span,
            rule_id=self.rule_id,
            message=self.message,
            suggested_fix_type=self.suggested_fix_type,
            fingerprint=self.fingerprint,
            first_seen_iteration=self.first_seen_iteration or iteration,
            last_seen_iteration=iteration,
            status=self.status,
        )
