#!/usr/bin/env python3
"""BookForge Issue Types and Structures.

Unified issue representation for the manuscript loop with severity classification,
fingerprinting for deduplication, and structured decision types.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class LoopDecision:
    status: str
    terminal: bool
    phase: str
    hard_issues: tuple[ManuscriptIssue, ...] = field(default_factory=tuple)
    soft_issues: tuple[ManuscriptIssue, ...] = field(default_factory=tuple)
    recommended_action: Optional[str] = None
    target_chapter: Optional[str] = None
    reason: str = ""

    @property
    def has_hard_issues(self) -> bool:
        return len(self.hard_issues) > 0

    @property
    def has_soft_issues(self) -> bool:
        return len(self.soft_issues) > 0

    @property
    def has_any_issues(self) -> bool:
        return self.has_hard_issues or self.has_soft_issues

    @property
    def should_stop(self) -> bool:
        return self.terminal or self.recommended_action == "stop"

    def issues_for_chapter(self, chapter: str) -> tuple[ManuscriptIssue, ...]:
        return tuple(i for i in self.hard_issues + self.soft_issues if i.chapter == chapter)

    def hard_issues_for_chapter(self, chapter: str) -> tuple[ManuscriptIssue, ...]:
        return tuple(i for i in self.hard_issues if i.chapter == chapter)

    def soft_issues_for_chapter(self, chapter: str) -> tuple[ManuscriptIssue, ...]:
        return tuple(i for i in self.soft_issues if i.chapter == chapter)


STATUS_DONE = "DONE"
STATUS_DONE_WITH_WARNINGS = "DONE_WITH_WARNINGS"
STATUS_BLOCKED = "BLOCKED"
STATUS_NEEDS_CONTEXT_REPAIR = "NEEDS_CONTEXT_REPAIR"
STATUS_NEEDS_CONTINUITY_REPAIR = "NEEDS_CONTINUITY_REPAIR"
STATUS_NEEDS_STYLE_REPAIR = "NEEDS_STYLE_REPAIR"
STATUS_NEEDS_EXPANSION = "NEEDS_EXPANSION"
STATUS_NEEDS_PACING_REBALANCE = "NEEDS_PACING_REBALANCE"
STATUS_NEEDS_TRIM = "NEEDS_TRIM"

PHASE_DRAFTING = "drafting"
PHASE_CONTEXT_REPAIR = "context_repair"
PHASE_EXPANSION = "expansion"
PHASE_REBALANCE = "rebalance"
PHASE_FINAL_VERIFY = "final_verify"
PHASE_TERMINAL = "terminal"

VALID_PHASE_TRANSITIONS: dict[str, set[str]] = {
    PHASE_DRAFTING: {PHASE_CONTEXT_REPAIR, PHASE_EXPANSION},
    PHASE_CONTEXT_REPAIR: {PHASE_EXPANSION, PHASE_REBALANCE},
    PHASE_EXPANSION: {PHASE_REBALANCE, PHASE_FINAL_VERIFY},
    PHASE_REBALANCE: {PHASE_FINAL_VERIFY},
    PHASE_FINAL_VERIFY: {PHASE_TERMINAL},
    PHASE_TERMINAL: set(),
}

ACTION_STOP = "stop"
ACTION_EXPAND_CHAPTER = "expand_chapter"
ACTION_REPAIR_CONTEXT = "repair_context"
ACTION_REPAIR_STYLE = "repair_style"
ACTION_REPAIR_CONTINUITY = "repair_continuity"
ACTION_REBALANCE_CHAPTER = "rebalance_chapter"
ACTION_TRIM_CHAPTER = "trim_chapter"


def create_done_decision(
    phase: str = PHASE_TERMINAL,
    soft_issues: tuple[ManuscriptIssue, ...] = (),
    reason: str = "Manuscript is complete and within target range.",
) -> LoopDecision:
    return LoopDecision(
        status=STATUS_DONE,
        terminal=True,
        phase=phase,
        hard_issues=(),
        soft_issues=soft_issues,
        recommended_action=ACTION_STOP,
        target_chapter=None,
        reason=reason,
    )


def create_done_with_warnings_decision(
    soft_issues: tuple[ManuscriptIssue, ...],
    phase: str = PHASE_TERMINAL,
    reason: str = "Manuscript is within target range with soft warnings only.",
) -> LoopDecision:
    return LoopDecision(
        status=STATUS_DONE_WITH_WARNINGS,
        terminal=True,
        phase=phase,
        hard_issues=(),
        soft_issues=soft_issues,
        recommended_action=ACTION_STOP,
        target_chapter=None,
        reason=reason,
    )


def create_blocked_decision(
    reason: str,
    hard_issues: tuple[ManuscriptIssue, ...] = (),
    phase: str = PHASE_TERMINAL,
) -> LoopDecision:
    return LoopDecision(
        status=STATUS_BLOCKED,
        terminal=True,
        phase=phase,
        hard_issues=hard_issues,
        soft_issues=(),
        recommended_action=ACTION_STOP,
        target_chapter=None,
        reason=reason,
    )


def create_needs_action_decision(
    status: str,
    action: str,
    target_chapter: str | None,
    hard_issues: tuple[ManuscriptIssue, ...],
    soft_issues: tuple[ManuscriptIssue, ...],
    phase: str,
    reason: str,
) -> LoopDecision:
    return LoopDecision(
        status=status,
        terminal=False,
        phase=phase,
        hard_issues=hard_issues,
        soft_issues=soft_issues,
        recommended_action=action,
        target_chapter=target_chapter,
        reason=reason,
    )