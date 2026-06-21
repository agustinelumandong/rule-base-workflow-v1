"""BookForge Loop Controller Core Package."""

from bookforge.core.loop.state import (
    StyleIssue,
    LengthState,
    soft_length_bounds,
    build_length_state,
)
from bookforge.core.loop.classify import (
    mode_for_status,
    action_chapter,
    issue_chapters,
    hard_issue_chapters,
    choose_expansion_chapter,
    choose_rebalance_chapter,
    classify,
)
from bookforge.core.loop.runner import (
    STYLE_TERMS,
    STYLE_SCAN_RE,
    scan_style_issues,
    load_persistent_repairs,
    save_persistent_repairs,
    run_loop_check,
    main,
)

from bookforge.core import length as length_checker
from bookforge.core import narrative_quality
from bookforge.core.issue import IssueCategory, ManuscriptIssue, Severity

