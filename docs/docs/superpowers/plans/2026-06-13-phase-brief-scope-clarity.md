# Phase Brief Scope Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify that `phase-0-contracts.md` and `phase-1-local-proof-engine.md` are first authorized implementation slices, while `BOOKFORGE-MASTER-PLAN.md` remains the full phase-gate authority.

**Architecture:** This is a documentation-only clarification. The master plan and roadmap index stay unchanged; the two phase briefs gain explicit scope notes, gate references, and next-step rules so future agents do not declare Phase 0 or Phase 1 complete from the starter slices alone.

**Tech Stack:** Markdown documentation, shell verification with `rg`, `sed`, `git diff`, and no runtime dependencies.

---

## Scope Check

This plan changes only phase-scope wording. It does not implement BookForge code, create Phase 2, change the master blueprint, or change the roadmap status table.

Current evidence:

- `docs/info-plan/BOOKFORGE-MASTER-PLAN.md:11-22` says the master plan is the north-star blueprint and Phase 0/1 advanced capabilities are contracts or fixtures unless assigned.
- `docs/info-plan/BOOKFORGE-MASTER-PLAN.md:1844-1900` defines the full Phase 0 gate.
- `docs/info-plan/BOOKFORGE-MASTER-PLAN.md:1902-1933` defines the full Phase 1 gate.
- `docs/info-plan/phase-0-contracts.md:13-29` defines a smaller minimum Phase 0 cut.
- `docs/info-plan/phase-1-local-proof-engine.md:13-54` defines a smaller first proof story and required tests.
- `docs/info-plan/phase-roadmap-index.md:9-13` says only phases with explicit implementation briefs are authorized.

## File Structure

- Modify: `docs/info-plan/phase-0-contracts.md`
  - Responsibility: declare the Phase 0 brief as the first authorized implementation slice, not the full Phase 0 completion gate.
- Modify: `docs/info-plan/phase-1-local-proof-engine.md`
  - Responsibility: declare the Phase 1 brief as the first authorized proof slice, not the full Phase 1 completion gate.
- Do not modify: `docs/info-plan/BOOKFORGE-MASTER-PLAN.md`
  - Responsibility: remains the full product blueprint and full phase-gate source.
- Do not modify: `docs/info-plan/phase-roadmap-index.md`
  - Responsibility: remains the phase authorization index.

## Task 1: Clarify Phase 0 Brief Scope

**Files:**
- Modify: `docs/info-plan/phase-0-contracts.md:7-15`

- [ ] **Step 1: Open current Phase 0 brief**

Run:

```bash
sed -n '1,80p' docs/info-plan/phase-0-contracts.md
```

Expected: output includes `## Rule`, `## Minimum Phase 0 Cut`, and no `## Scope Clarification` section.

- [ ] **Step 2: Insert scope clarification after containerization rule**

Edit `docs/info-plan/phase-0-contracts.md` so lines after:

```markdown
Containerization, if added in Phase 0, is limited to a deterministic local test environment contract. Do not add production services.
```

become:

```markdown
Containerization, if added in Phase 0, is limited to a deterministic local test environment contract. Do not add production services.

## Scope Clarification

This brief defines the first authorized implementation slice for Phase 0. It does not replace the full Phase 0 gate in `BOOKFORGE-MASTER-PLAN.md`.

After this slice passes, expand this brief or create a follow-up Phase 0 completion brief before declaring Phase 0 complete.

The master-plan Phase 0 gate includes broader contracts such as authenticity, continuity locks, Western profile, character governance, character arc, theme, source promotion, beat planning, action scene, numeric lock, model-run, persona fixture, prompt fixture, and deterministic `Lone Star Reckoning` fixture contracts.
```

- [ ] **Step 3: Tighten section heading**

Change:

```markdown
## Minimum Phase 0 Cut
```

to:

```markdown
## First Authorized Phase 0 Cut
```

- [ ] **Step 4: Verify Phase 0 wording**

Run:

```bash
rg -n "Scope Clarification|first authorized implementation slice|follow-up Phase 0 completion brief|First Authorized Phase 0 Cut" docs/info-plan/phase-0-contracts.md
```

Expected: four matches, one for each required phrase.

- [ ] **Step 5: Commit Phase 0 clarification**

Run:

```bash
git add docs/info-plan/phase-0-contracts.md
git commit -m "docs: clarify phase 0 brief scope"
```

Expected: commit succeeds and includes only `docs/info-plan/phase-0-contracts.md`.

## Task 2: Clarify Phase 1 Brief Scope

**Files:**
- Modify: `docs/info-plan/phase-1-local-proof-engine.md:7-15`

- [ ] **Step 1: Open current Phase 1 brief**

Run:

```bash
sed -n '1,90p' docs/info-plan/phase-1-local-proof-engine.md
```

Expected: output includes `## Rule`, `## First Proof Story Scope`, `## Required Proof Flow`, and no `## Scope Clarification` section.

- [ ] **Step 2: Insert scope clarification after containerization rule**

Edit `docs/info-plan/phase-1-local-proof-engine.md` so lines after:

```markdown
If containerized, Phase 1 uses one local `bookforge-dev` service whose default command runs offline deterministic tests.
```

become:

```markdown
If containerized, Phase 1 uses one local `bookforge-dev` service whose default command runs offline deterministic tests.

## Scope Clarification

This brief defines the first authorized proof slice for Phase 1. It does not replace the full Phase 1 gate in `BOOKFORGE-MASTER-PLAN.md`.

After this slice passes, expand this brief or create a follow-up Phase 1 completion brief before declaring Phase 1 complete.

The master-plan Phase 1 gate includes broader fixture coverage for approved key cast, antagonist profile, supporting-character function, file-backed policies, authenticity, period pack, continuity locks, Western style, persona-bound fixtures, character governance, character arc, theme governance, source promotion, beat completeness, numeric locks, QA, diff, trace, simulated approval, and Markdown export.
```

- [ ] **Step 3: Tighten section heading**

Change:

```markdown
## First Proof Story Scope
```

to:

```markdown
## First Authorized Proof Story Scope
```

- [ ] **Step 4: Verify Phase 1 wording**

Run:

```bash
rg -n "Scope Clarification|first authorized proof slice|follow-up Phase 1 completion brief|First Authorized Proof Story Scope" docs/info-plan/phase-1-local-proof-engine.md
```

Expected: four matches, one for each required phrase.

- [ ] **Step 5: Commit Phase 1 clarification**

Run:

```bash
git add docs/info-plan/phase-1-local-proof-engine.md
git commit -m "docs: clarify phase 1 brief scope"
```

Expected: commit succeeds and includes only `docs/info-plan/phase-1-local-proof-engine.md`.

## Task 3: Verify Cross-Document Consistency

**Files:**
- Inspect: `docs/info-plan/BOOKFORGE-MASTER-PLAN.md`
- Inspect: `docs/info-plan/phase-roadmap-index.md`
- Inspect: `docs/info-plan/phase-0-contracts.md`
- Inspect: `docs/info-plan/phase-1-local-proof-engine.md`

- [ ] **Step 1: Confirm master plan still says phase briefs control implementation**

Run:

```bash
rg -n "not permission to implement every capability|Implementation must follow the assigned phase|For Phase 0 and Phase 1, advanced capabilities are contracts or fixtures" docs/info-plan/BOOKFORGE-MASTER-PLAN.md
```

Expected: matches from the Product Vision section.

- [ ] **Step 2: Confirm roadmap index still blocks later phases**

Run:

```bash
rg -n "Only phases with an explicit implementation brief|Future; do not implement yet|Do not create implementation-ready briefs for Phase 3" docs/info-plan/phase-roadmap-index.md
```

Expected: matches prove Phase 2-8 are still future-only and no phase authorization changed.

- [ ] **Step 3: Confirm both briefs reference full master-plan gates**

Run:

```bash
rg -n "does not replace the full Phase [01] gate|before declaring Phase [01] complete" docs/info-plan/phase-0-contracts.md docs/info-plan/phase-1-local-proof-engine.md
```

Expected: four matches total, two in each brief.

- [ ] **Step 4: Inspect diff**

Run:

```bash
git diff -- docs/info-plan/phase-0-contracts.md docs/info-plan/phase-1-local-proof-engine.md
```

Expected: diff shows only the new `## Scope Clarification` sections and heading renames. It must not change forbidden-work lists, acceptance text, roadmap status, or master-plan phase gates.

- [ ] **Step 5: Commit verification note if needed**

If Task 1 and Task 2 commits already contain all changes, do not create another commit.

If small wording fixes were made during verification, run:

```bash
git add docs/info-plan/phase-0-contracts.md docs/info-plan/phase-1-local-proof-engine.md
git commit -m "docs: align phase brief completion gates"
```

Expected: commit succeeds only if verification edits existed.

## Task 4: Final Review

**Files:**
- Inspect: `docs/info-plan/phase-0-contracts.md`
- Inspect: `docs/info-plan/phase-1-local-proof-engine.md`
- Inspect: `docs/info-plan/phase-roadmap-index.md`

- [ ] **Step 1: Run final text scan for banned ambiguity**

Run:

```bash
rg -n "Phase 0 is complete|Phase 1 is complete|first authorized|full Phase [01] gate|follow-up Phase [01] completion brief" docs/info-plan/phase-0-contracts.md docs/info-plan/phase-1-local-proof-engine.md
```

Expected: output shows old acceptance language plus new clarification language. The combination should make it clear the briefs are starter slices and completion still depends on full gate coverage.

- [ ] **Step 2: Confirm no accidental Phase 2 authorization**

Run:

```bash
rg -n "phase-2-useful-local-engine.md|Implementation-ready|Future; do not implement yet" docs/info-plan/phase-roadmap-index.md docs/info-plan/phase-0-contracts.md docs/info-plan/phase-1-local-proof-engine.md
```

Expected: `phase-roadmap-index.md` still lists Phase 2 as future and only says the Phase 2 brief is created after Phase 1 passes.

- [ ] **Step 3: Report final result**

Final response must include:

```text
Changed:
- docs/info-plan/phase-0-contracts.md
- docs/info-plan/phase-1-local-proof-engine.md

Preserved:
- docs/info-plan/BOOKFORGE-MASTER-PLAN.md
- docs/info-plan/phase-roadmap-index.md

Verified:
- Phase 0/1 briefs now read as first authorized slices.
- Full phase completion still points back to BOOKFORGE-MASTER-PLAN.md.
- Phase 2 remains future-only.
```

## Self-Review

Spec coverage:

- Covers user decision: patch phase briefs, not master plan.
- Keeps roadmap index unchanged.
- Preserves Phase 2+ future-only rule.
- Adds exact wording for Phase 0 and Phase 1 ambiguity.
- Includes verification commands and expected output.

Placeholder scan:

- No prohibited placeholder markers or vague validation instructions.
- Every edit step contains exact Markdown text.

Type and name consistency:

- File names match current repo paths.
- Phase 0 and Phase 1 wording uses same pattern.
- Commit names are docs-only and scoped.
