# The Calling Book 4 Outline Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Book 4's canonical outline satisfy the local 17-section outline contract without changing its prisoner-escort premise.

**Architecture:** Keep `phase-0.md` as the single source of truth. Add the missing contract sections, normalize the existing characters and chapters into the required schema, and preserve Book 3 canon that Duke's federal warrant is cleared.

**Tech Stack:** Markdown; local manuscript workflow scripts; Git diff checks.

## Global Constraints

- Preserve the prisoner escort, Ledbetter's guilt, and Merritt Crane as a personal six-rider threat.
- Duke's warrant is cleared; federal pressure concerns the public record, identity disclosure, and Crane evidence.
- Do not use a banned new name; do not create an institutional villain, resource-rights scheme, or trial scene.
- Do not add em dashes to the outline.

---

### Task 1: Repair the outline contract and continuity

**Files:**
- Modify: `books/the-calling/book-4/phase-0.md`

**Interfaces:**
- Consumes: `books/the-calling/book-3/rulebook.md` ending state and `settings.json` name policy.
- Produces: A 17-section Book 4 outline ready for rulebook generation.

- [x] **Step 1: Add the missing contract sections**

Add Time Period, Primary Setting, Setting Function, Tone and Style Direction, Core Conflicts, Act Structure, and Ending State for Book 5. State the road-pressure chapter function rule and complete embedded guardrails.

- [x] **Step 2: Repair character and canon contracts**

Replace Deputy Marshal Nathan Cole with a name outside `settings.json`'s banned list. Add required role, physical marker, voice, motive, condition, goal, and knowledge fields. Replace every reference to an unresolved warrant with a cleared warrant and a federal record review.

- [x] **Step 3: Normalize chapter entries**

Give each chapter an advisory word target and a specific paragraph explaining what happens, what moves, and what changes. Keep all existing causal beats.

### Task 2: Validate the repaired outline

**Files:**
- Modify: `books/the-calling/book-4/phase-0.md`

**Interfaces:**
- Consumes: The repaired outline.
- Produces: Evidence that required sections, name policy, style guardrails, and working-tree formatting pass.

- [x] **Step 1: Run source-format intake**

Run `python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_source_format.py books/the-calling/book-4` and inspect the generated scan.

- [x] **Step 2: Run targeted static checks**

Run `rg -n --fixed-strings 'Nathan Cole' books/the-calling/book-4/phase-0.md`, `rg -n --fixed-strings '—' books/the-calling/book-4/phase-0.md`, and `git diff --check -- books/the-calling/book-4/phase-0.md`. Expected result: no matches and no diff errors.

- [x] **Step 3: Remove the generated intake artifact**

Delete `books/the-calling/book-4/source-format-scan.md` so the requested change remains limited to the outline.
