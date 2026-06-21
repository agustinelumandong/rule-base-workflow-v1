# BookForge Loop Remediation Plan

**Date:** 2026-06-19
**Status:** Analysis Complete - Awaiting Implementation Approval
**Source:** System feedback analysis + codebase review + Oracle review

---

## Executive Summary

The current manuscript loop system allows valid goals to fight each other, creating an autonomous editing treadmill that can never reach a terminal state. The book can be exactly 30,000 words, pass validation, and still return `NEEDS_PACING_REBALANCE`.

**Root Cause:** No separation between hard blockers and soft quality warnings. No iteration budgets. No chapter freezing. No hysteresis on word count targets.

**Fix:** Add a loop governor with explicit terminal states, severity-segregated issues, and bounded phases.

---

## Problem Diagnosis

### The Evidence

From system feedback, the loop trace shows:
- `build_context_packet.py`: 137 calls
- `validate_manuscript_context.py`: 115 calls
- `run_manuscript_loop.py`: 100 calls
- `STYLE_SCAN_RE` checks: 216
- File edits: 130

The same chapters recur: Chapter 1, 2, 5, 4, 11, 8, 6, 7 — repeatedly.

**Final state in logs:**
```
Book is now exactly 30000 words.
Context validator: PASS
Internal style scan: NO_INTERNAL_STYLE_MATCHES
Loop: NEEDS_PACING_REBALANCE, not DONE
```

### The Core Loop Problem

```python
# Current dangerous pattern
while loop_state != "DONE":
    target = loop.pick_target()
    edit(target)
    validate(target)
    validate_book()
    check_length()
    check_style()
    loop_state = loop.run()  # Can always find another improvement
```

### Conflicting Completion Criteria

The system has three definitions of success that don't align:
1. Deterministic validation passes
2. Word count reaches 30,000
3. Loop state becomes DONE

**Result:** Book can satisfy #1 and #2 while loop still says #3 is not met.

### Length/Pacing Oscillation

```
trim to fix pacing
→ manuscript below target
→ expand to fix length
→ expansion harms pacing
→ trim again
```

### Micro-Edit Chasing

```
33 words short
24 words short
13 words short
4 words short
1 word short
```

This is not good book generation behavior — it turns the LLM into a word-count patcher.

---

## Current Architecture

### Loop Flow (`bookforge/core/loop.py`)

```
run_loop_check()
├── build_length_state()        → LengthState
├── validate_required_book_files() → book_passes, book_failures
├── discover_chapters()         → chapters[]
├── validate_chapter()          → reports[] (FAIL/WARN/PASS)
├── scan_style_issues()         → style_issues[]
├── check_continuity_chain()    → continuity_failures[]
├── narrative_quality.analyze() → narrative_issues[]
├── check_chapter_rhythm.analyze() → rhythm_report
└── classify()                  → status, reason
```

### Files Involved

| File | Purpose |
|------|---------|
| `bookforge/core/loop.py` | Main loop controller, classify() function |
| `bookforge/core/validator.py` | Context validation, style scanning |
| `bookforge/core/rhythm.py` | Chapter rhythm analysis |
| `bookforge/core/narrative_quality.py` | Narrative quality heuristics |
| `bookforge/core/length.py` | Word count checking |
| `bookforge/core/chain.py` | Continuity chain validation |

---

## Root Causes

### 1. `classify()` Treats All Issues as Hard Blockers

**Location:** `bookforge/core/loop.py` lines 175-210

```python
def classify(...) -> tuple[str, str]:
    if rhythm_issues:
        return "NEEDS_PACING_REBALANCE", f"Rhythm checker found {len(rhythm_issues)} issue(s)."
    if narrative_issues:
        return "NEEDS_PACING_REBALANCE", "Narrative quality checks flagged..."
    return "DONE", "Manuscript is within target range..."
```

**Problem:** Rhythm issues are WARN-level, not FAIL-level, but the loop treats them identically.

### 2. No Word Count Hysteresis

**Location:** `bookforge/core/loop.py` lines 202-205

```python
if length_state.total_words < length_state.target_min:
    return "NEEDS_EXPANSION", "Manuscript is below target minimum."
if length_state.total_words > length_state.target_max:
    return "BLOCKED", "Manuscript is above target maximum..."
```

**Problem:** With target_min=30,000 and target_max=31,000, expansion can overshoot, triggering trim, which triggers expansion again.

### 3. No Chapter Freezing

**Location:** `loop.py` - `action_chapter()` function

```python
def action_chapter(status, context_problem_chapters, expansion_chapter, ...):
    if status == "NEEDS_EXPANSION" and expansion_chapter != "NONE":
        return expansion_chapter  # Same chapter can be selected forever
```

**Problem:** Chapters that have been edited successfully can be selected again indefinitely.

### 4. No Iteration Budget / Phase Boundaries

**Location:** `loop.py` - `run_loop_check()`

No tracking of:
- Maximum total iterations
- Maximum iterations per chapter
- Phase completion flags
- Global stop conditions beyond BLOCKED

### 5. Validator Output is Opaque

**Location:** `loop.py` lines 73-88

```python
def scan_style_issues(book_folder: Path) -> list[StyleIssue]:
    # Returns only (path, line_number, line)
    # No information about which term triggered, which rule, severity, or suggested fix
```

**Problem:** LLM must guess what to fix, leading to iterative re-selection.

### 6. Rhythm Issues Have No Severity

**Location:** `bookforge/core/rhythm.py` lines 85-139

All issues are "WARN" level, but some are soft quality preferences, not hard blockers.

---

## Remediation Plan

### Phase 1: Issue Classification Infrastructure

#### 1.1 Create `bookforge/core/issue.py`

Define a unified issue structure with issue fingerprints:

```python
@dataclass(frozen=True)
class ManuscriptIssue:
    severity: str           # HARD, SOFT, INFO
    category: str           # context, style, length, rhythm, narrative, continuity
    chapter: str | None     # None for book-level issues
    file: Path | None
    line: int | None
    span: str | None        # The matched text
    rule_id: str | None     # e.g., "STYLE_ABSTRACT_META", "RHYTHM_UNEVEN"
    message: str
    suggested_fix_type: str | None  # e.g., "replace_with_physical_action"

    # Issue tracking for deduplication
    fingerprint: str         # hash(rule_id + file + line_context + span)
    first_seen_iteration: int = 0
    last_seen_iteration: int = 0
    status: str = "open"    # open, resolved, accepted, ignored
```

**Fingerprint calculation:**
```python
fingerprint = hashlib.sha256(
    f"{rule_id}:{file}:{line}:{span}".encode()
).hexdigest()[:16]
```

**Purpose:** Track same issue recurring, new issues introduced, old issues resolved, soft warnings accepted.

#### 1.2 Update `validator.py`

Replace current style scan with one that returns `ManuscriptIssue` objects with full metadata:
- Which specific term triggered the match
- Which rule/banned list it came from
- Severity level
- Suggested fix type
- Issue fingerprint

#### 1.3 Update `rhythm.py`

Distinguish severity levels:
- **HARD**: Chapters way outside bounds (e.g., >3000 words when max should be 2400)
- **SOFT**: Rhythm preferences (stdev too low, too many chapters above 2400)
- **INFO**: Advisory notes

#### 1.4 Update `narrative_quality.py`

Add severity levels — some issues are blockers, others are suggestions.

---

### Phase 2: Governor / Loop Controller Rewrite

#### 2.1 Create `bookforge/core/governor.py`

```python
@dataclass
class LoopGovernor:
    book_folder: Path
    max_total_iterations: int = 25
    max_iterations_per_chapter: int = 3
    max_same_state_repeats: int = 2
    stop_if_only_soft_warnings: bool = True  # DEFAULT: True for autonomous runs

    # State tracking
    phase: str = "drafting"  # drafting → context_repair → expansion → rebalance → final_verify → terminal
    iteration_count: int = 0
    state_history: list[str] = field(default_factory=list)

    # Issue tracking
    open_issues: dict[str, ManuscriptIssue] = field(default_factory=dict)  # fingerprint -> issue

    def should_continue(self, issues: list[ManuscriptIssue]) -> tuple[bool, str]:
        """Returns (continue, reason)"""

    def record_iteration(self, status: str) -> None:
        """Record iteration for budget tracking"""

    def update_issue_tracking(self, issues: list[ManuscriptIssue]) -> None:
        """Update fingerprints, track resolved vs new vs recurring"""

    def terminal_state(self, issues: list[ManuscriptIssue]) -> str:
        """Determine terminal state: DONE, DONE_WITH_WARNINGS, BLOCKED"""
```

#### 2.2 Create `LoopDecision` dataclass

Replace string-based status returns with structured decisions:

```python
@dataclass(frozen=True)
class LoopDecision:
    status: str                    # DONE, DONE_WITH_WARNINGS, BLOCKED, NEEDS_*
    terminal: bool                 # True if autonomous loop should stop
    phase: str                     # Current phase
    hard_issues: list[ManuscriptIssue]   # Must fix before terminal
    soft_issues: list[ManuscriptIssue]     # Warnings only
    recommended_action: str | None  # e.g., "expand_chapter", "repair_context", "stop"
    target_chapter: str | None      # Which chapter to edit
    reason: str                     # Human-readable explanation
```

**Key rule:** `terminal = True` when `status in (DONE, DONE_WITH_WARNINGS, BLOCKED)`.

#### 2.3 Update `loop.py`

Replace `classify()` with governor-based logic returning `LoopDecision`:

```python
def run_loop_check(governor: LoopGovernor, ...) -> LoopDecision:
    # Collect ALL issues with severity
    all_issues = collect_all_issues(...)

    # Separate hard vs soft
    hard_issues = [i for i in all_issues if i.severity == "HARD"]
    soft_issues = [i for i in all_issues if i.severity == "SOFT"]

    # Update issue tracking
    governor.update_issue_tracking(all_issues)

    # Check if should stop
    if governor.stop_if_only_soft_warnings and not hard_issues:
        return LoopDecision(
            status="DONE_WITH_WARNINGS",
            terminal=True,
            phase=governor.phase,
            hard_issues=[],
            soft_issues=soft_issues,
            recommended_action="stop",
            target_chapter=None,
            reason="Soft warnings only. Autonomous loop stops here."
        )

    # ... rest of logic returning LoopDecision
```

---

### Phase 3: Hysteresis & Tolerance Bands

#### 3.1 Update `length.py` - Two-Range Model

**Do NOT silently violate contractual word count.** Use two ranges:

```python
@dataclass(frozen=True)
class LengthRanges:
    contract_min: int   # User-specified minimum (e.g., 30000)
    contract_max: int   # User-specified maximum (e.g., 31000)
    soft_min: int       # Acceptable floor (contract_min - 1%)
    soft_max: int       # Acceptable ceiling (contract_max + 1%)

# For 30k book:
# contract_min = 30000
# contract_max = 31000
# soft_min = 29700
# soft_max = 31300
```

**Decision matrix:**

| Word Count | Status | Notes |
|------------|--------|-------|
| 30,000–31,000 | DONE | Within contractual range |
| 29,700–29,999 | DONE_WITH_WARNINGS | Slightly under, user may permit |
| 31,001–31,300 | DONE_WITH_WARNINGS | Slightly over, user may permit |
| below 29,700 | NEEDS_EXPANSION | Below soft floor, must expand |
| above 31,300 | NEEDS_TRIM/BLOCKED | Above soft ceiling, must trim |

#### 3.2 Update `rhythm.py` tolerance bands

```python
# Tolerance bands per pacing class (HARD threshold = trim required)
LEAN_MAX_HARD = 2500
STANDARD_MAX_HARD = 2900
EXPANDED_MAX_HARD = 3300

# SOFT threshold = warning only
LEAN_MAX_SOFT = 2200
STANDARD_MAX_SOFT = 2600
EXPANDED_MAX_SOFT = 3000
```

---

### Phase 4: Chapter Freezing with Modes

#### 4.1 Update `loop-state.json` schema with freeze modes

```json
{
  "repair_attempts": {"chapter-01": 2},
  "frozen_chapters": {
    "chapter-03": {
      "frozen_for_expansion": true,
      "frozen_for_rebalance": true,
      "allow_hard_validator_repairs": true
    },
    "chapter-07": {
      "frozen_for_expansion": true,
      "frozen_for_rebalance": false,
      "allow_hard_validator_repairs": true
    }
  },
  "total_iterations": 15,
  "phase": "rebalance",
  "state_history": ["NEEDS_EXPANSION", "NEEDS_EXPANSION", "NEEDS_PACING_REBALANCE"],
  "last_run": "2026-06-19T...",
  "last_status": "DONE_WITH_WARNINGS"
}
```

**Key principle:** Frozen chapters cannot receive padding or subjective rebalance edits. But if a HARD continuity error appears, the system MUST still patch it.

#### 4.2 Update `action_chapter()` to respect freeze modes

```python
def action_chapter(
    decision: LoopDecision,
    freeze_modes: dict[str, dict[str, bool]],
    hard_issues: list[ManuscriptIssue]
) -> str | None:
    target = decision.target_chapter
    if not target:
        return None

    # Check if chapter is frozen for this action type
    freeze = freeze_modes.get(target, {})
    action = decision.recommended_action

    if action == "expand_chapter" and freeze.get("frozen_for_expansion"):
        # Find next best unfrozen chapter
        return select_next_unfrozen_chapter(...)
    if action == "rebalance_chapter" and freeze.get("frozen_for_rebalance"):
        return select_next_unfrozen_chapter(...)

    # HARD issues override freezing
    hard_for_target = [i for i in hard_issues if i.chapter == target]
    if hard_for_target:
        return target  # Must repair even if frozen

    return target
```

---

### Phase 5: Batching & Issue Aggregation

#### 5.1 Update loop to collect ALL issues before deciding

```python
def run_loop_check(...):
    # Collect ALL issues first
    all_style_issues = scan_style_issues(book_folder)
    all_rhythm_issues = rhythm_report.issues
    all_narrative_issues = narrative_issues

    # Batch by chapter
    issues_by_chapter = defaultdict(list)
    for issue in all_style_issues:
        issues_by_chapter[issue.chapter].append(issue)

    # Return all issues in report, not just first one
```

#### 5.2 Update report output

Include all issues in the loop report, not just the first one found.

---

### Phase 6: Phase Boundary Rules

Phases are **one-way**. Transitions:

```
drafting → context_repair → expansion → rebalance → final_verify → terminal
```

**Rules:**
- Once drafting is complete, do not regenerate whole chapters.
- Once expansion is complete, do not expand frozen chapters.
- Once rebalance is complete, only HARD-blocker repairs are allowed.
- After final_verify, stop unless user explicitly overrides.

**This prevents:** expand → trim → expand → trim oscillation.

---

## Implementation Order (Revised)

| Priority | Step | Status | File | Changes |
| -------: | ---- | ------ |------ |--------- |
| 1 | [ ] | 1.1 | `bookforge/core/issue.py` | Create - `ManuscriptIssue` with fingerprints + `Severity` enum |
| 2 | [ ] | 2.1 | `bookforge/core/issue.py` | Add `LoopDecision` dataclass |
| 3 | [ ] | 1.2 | `bookforge/core/validator.py` | Update - Structured issue output with rule metadata + fingerprints |
| 4 | [ ] | 1.3 | `bookforge/core/rhythm.py` | Update - Severity levels and tolerance bands |
| 5 | [ ] | 1.4 | `bookforge/core/narrative_quality.py` | Update - Severity levels |
| 6 | [ ] | 3.1 | `bookforge/core/length.py` | Update - Two-range model (contract + soft) |
| 7 | [ ] | 2.2 | `bookforge/core/governor.py` | Create - Governor with budgets, issue tracking, phase state machine |
| 8 | [ ] | 2.3 | `bookforge/core/loop.py` | Update - Use governor, return `LoopDecision`, implement freezing |
| 9 | [ ] | 4.1 | `bookforge/core/loop-state.json` | Update schema - Add freeze_modes, phase, state_history |
| 10 | [ ] | 4.2 | `bookforge/core/action_chapter()` | Update - Respect freeze modes, allow HARD override |
| 11 | [ ] | 5.1 | `bookforge/core/loop.py` | Update - Collect ALL issues before deciding |
| 12 | [ ] | 5.2 | `bookforge/core/loop.py` | Update - Report output includes all issues |
| 13 | [ ] | S1 | `bookforge/core/__init__.py` | Update - Export new types |
| 14 | [ ] | S2 | `bookforge/config.py` | Update - Add governor configuration defaults |
| 15 | [ ] | T1 | Tests | Add regression tests for exact failure cases |

---

## Design Decisions Required

Before implementation, confirm:

- [x] **Terminal State Policy:** `DONE_WITH_WARNINGS` is terminal for autonomous runs. User can manually request additional passes.
- [x] **Iteration Budget Defaults:** max_total=25, max_per_chapter=3, max_same_state=2
- [x] **Chapter Freezing Strategy:** Use freeze modes (not absolute). HARD issues always override.
- [x] **Hysteresis Band:** Two ranges - contract (30k-31k) and soft (29.7k-31.3k). Contract range = official DONE.
- [x] **Soft Warning Handling:** `stop_if_only_soft_warnings: bool = True` — correct default for autonomous runs.
- [x] **Issue Fingerprints:** Add to `ManuscriptIssue` for deduplication tracking.
- [x] **LoopDecision:** Return structured decisions, not string status.

---

## Regression Tests Required

### Test 1: Valid manuscript with rhythm warnings stops

```
Given:
- 30,000 words (within contract range)
- context PASS
- style PASS
- rhythm SOFT warnings only

Expected:
status = DONE_WITH_WARNINGS
terminal = true
target_chapter = None
recommended_action = "stop"
```

### Test 2: Soft warnings do not trigger chapter edits

```
Given:
- only SOFT rhythm issues
- stop_if_only_soft_warnings = true

Expected:
target_chapter = None
recommended_action = "stop"
```

### Test 3: Frozen chapter cannot be selected for expansion

```
Given:
- chapter-01 frozen_for_expansion = true
- chapter-01 is shortest chapter

Expected:
loop selects another chapter or stops
```

### Test 4: HARD issue overrides freezing

```
Given:
- chapter-01 frozen
- chapter-01 has HARD continuity failure

Expected:
chapter-01 can be selected for repair
```

### Test 5: Same state repeated twice blocks loop

```
Given:
- NEEDS_PACING_REBALANCE appears 3 times
- no new HARD issues introduced

Expected:
status = BLOCKED or DONE_WITH_WARNINGS
terminal = true
```

### Test 6: Word count at contract minimum = DONE

```
Given:
- 30,000 words exactly
- context PASS
- style PASS

Expected:
status = DONE (not NEEDS_PACING_REBALANCE)
```

### Test 7: Word count slightly under contract but in soft range

```
Given:
- 29,850 words
- context PASS
- style PASS

Expected:
status = DONE_WITH_WARNINGS
reason = "Within soft tolerance, slightly under contract minimum"
```

---

## Expected Outcomes

### Before Fix
```
Book: 30,000 words, PASS validation, clean style scan
Loop: NEEDS_PACING_REBALANCE
Result: Infinite loop potential
```

### After Fix
```
Book: 30,000 words, PASS validation, clean style scan
Loop: DONE_WITH_WARNINGS
terminal: true
recommended_action: "stop"
Warnings: [Rhythm stdev low, 2 chapters could be leaner]
Result: Terminal state - user can request rebalance or accept
```

---

## Key Protection Rule

> **If only soft warnings remain, the autonomous loop must stop.**

This is the rule that prevents the infinite editing treadmill.

---

## References

- Original feedback: System-generated analysis
- Oracle review: 2026-06-19
- Current loop implementation: `bookforge/core/loop.py`
- Style validation: `bookforge/core/validator.py`
- Rhythm checking: `bookforge/core/rhythm.py`
- Narrative quality: `bookforge/core/narrative_quality.py`
- Length checking: `bookforge/core/length.py`
- Loop reference: `.agents/skills/manuscript-workflow-orchestrator/references/autonomous-loop.md`

---

## Status History

| Date | Status | Notes |
|------|--------|-------|
| 2026-06-19 | Analysis Complete | Full root cause analysis and remediation plan documented |
| 2026-06-19 | Oracle Review | Corrections incorporated: fingerprints, freeze modes, two-range model, LoopDecision, phase rules |

---

## Progress Tracker

### Phase 1: Issue Classification Infrastructure

- [ ] 1.1 Create `bookforge/core/issue.py` - `ManuscriptIssue` with fingerprints + `Severity` enum
- [ ] 1.2 Update `validator.py` - Structured issue output with rule metadata + fingerprints
- [ ] 1.3 Update `rhythm.py` - Severity levels and tolerance bands
- [ ] 1.4 Update `narrative_quality.py` - Severity levels

### Phase 2: Governor / Loop Controller Rewrite

- [ ] 2.1 Create `bookforge/core/governor.py` - Governor with budgets, issue tracking, phase state machine
- [ ] 2.2 Create `bookforge/core/issue.py` - Add `LoopDecision` dataclass
- [ ] 2.3 Update `loop.py` - Use governor, return `LoopDecision`, implement freezing

### Phase 3: Hysteresis & Tolerance Bands

- [ ] 3.1 Update `length.py` - Two-range model (contract + soft)
- [ ] 3.2 Update `rhythm.py` - Tolerance bands per pacing class (HARD vs SOFT thresholds)

### Phase 4: Chapter Freezing with Modes

- [ ] 4.1 Update `loop-state.json` schema - Add freeze_modes, phase, state_history
- [ ] 4.2 Update `action_chapter()` - Respect freeze modes, allow HARD override

### Phase 5: Batching & Issue Aggregation

- [ ] 5.1 Update loop - Collect ALL issues before deciding
- [ ] 5.2 Update report output - Include all issues, not just first one

### Phase 6: Phase Boundary Rules

- [ ] 6.1 Add phase transition rules to governor
- [ ] 6.2 Prevent backward phase transitions

### Supporting Changes

- [ ] Update `bookforge/core/__init__.py` - Export new types
- [ ] Update `bookforge/config.py` - Add governor configuration defaults
- [ ] Add regression tests - 7 critical test cases