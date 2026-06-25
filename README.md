# BookForge v2 — Rule-Based Event-Sourced Manuscript Workflow

BookForge is a structured writing system and automation pipeline for planning, drafting, expanding, validating, and polishing fiction with AI assistance. It organizes story facts, enforces styling constraints, and maintains character/location continuity across chapters.

---

## 1. Architectural Foundations: The 5-Layer Model

The system operates on a **5-layer model** to ensure narrative consistency and prevent logic/style drift:

```
┌────────────────────────────────────────────────────────┐
│  Layer 5: Series (Sequel continuity, name checking)     │
├────────────────────────────────────────────────────────┤
│  Layer 4: Book (Outline phase-0, rules, pacing plan)   │
├────────────────────────────────────────────────────────┤
│  Layer 3: Chapter (Staging changes/ priority workflow) │
├────────────────────────────────────────────────────────┤
│  Layer 2: Scene (Pacing constraints, beat structures)  │
├────────────────────────────────────────────────────────┤
│  Layer 1: Event/Canon (Replay ledger, status, locales) │
└────────────────────────────────────────────────────────┘
```

- **Layer 5 (Series)**: Series configuration, multi-book constraints, name check across sequels.
- **Layer 4 (Book)**: Outline (`phase-0.md`), rules/mood-locks, and pacing plan.
- **Layer 3 (Chapter)**: The staging priority change unit (`changes/chapter-NN/`).
- **Layer 2 (Scene)**: Beat-by-beat scene progression and pacing constraints.
- **Layer 1 (Event / Canon)**: Event replay ledger, character status, and geographical consistency.

---

## 2. Core Concepts

*   **Durable Identity vs. Current State**: Durable character details (who they are) live in `canon/entities/characters.yml`. Per-chapter mutable states (where they are, injuries, inventory) are calculated dynamically by a **folding engine** that replays chapter events from `canon/events/` into a single state snapshot (`canon/state/snapshot.yml`).
*   **Staging-Priority Change Workflow**: Active writing is performed under `changes/chapter-NN/` using a **Proposal-Beat-Draft** lifecycle. It is validated, compiled into the canonical `chapters/chapter-NN/` folder, reviewed through `chapter-review.md`, and only then treated as ready for loop completion or promotion.
*   **Swappable Persistent Memory Tier**: Manages semantic search and name alias resolution (`bf memory *`) using a swappable backend (Headroom or zero-dependency local embedding fallback).

---

## 3. Quick Start

### 1. Run the Installer
Run the cross-platform Python installer to verify dependencies, install the local `bookforge` package, and configure optional NotebookLM MCP settings:
```bash
python scripts/install.py
```

### 2. Initialize a Book Workspace
Prepare a book directory and generate agent-specific configuration shims (e.g. `CLAUDE.md`, `GEMINI.md`, `.cursorrules`):
```bash
bf init --agents gemini,claude,cursor
```

### 3. Draft/Edit in Staging
Work on a chapter inside the staging directory `changes/chapter-NN/`:
- `proposal.md`: Scene-breakdown outlining beats/scenes.
- `beats.md`: Active drafting plan.
- `draft.md`: Active draft prose.
- `continuity-out.md`: Unresolved stakes and character/location status updates.

### 4. Validate
Before committing, run validation and continuity checks on the chapter:
```bash
bf validate --chapter chapter-NN
```

Compiled chapter folders now require `chapter-review.md`. This read-through artifact records slow spots, rushed spots, break opportunities, and a final decision before the loop can treat the chapter as done.

### 5. Promote & Apply
Once validation checks pass cleanly, apply the staging changes to the canonical directory:
```bash
bf apply change books/book-example chapter-NN
```
This automatically appends chapter events to the canon events log, re-runs the fold engine to update the snapshot, compiles the draft files, and archives the staging folder.

---

## 4. Key CLI Commands

Always use the unified `bf` CLI command set. Avoid invoking legacy python scripts directly as they are deprecated.

| Command Group | Command | Description |
| :--- | :--- | :--- |
| **Validation & Gate** | `bf validate [--chapter N]` | Runs all canon and manuscript validators |
| | `bf apply change <book> <chapter-id>` | Validates, compiles, and commits staging folder |
| **Canon Fold** | `bf canon build` | Rebuilds current snapshot from entities and event log |
| | `bf canon validate` | Validates schema integrity and state consistency |
| **Memory Tier** | `bf memory search "<query>"` | Semantic search over canon, drafts, and history |
| | `bf memory resolve "<alias>"` | Decodes character aliases to canonical IDs |
| | `bf memory serve --mcp` | Launches the optional MCP memory tools server |
| **Loop & Build** | `bf loop` | Runs autonomous compiler and repair loops |

---

## 5. Directory Structure

```text
books/<book-slug>/
  canon/
    entities/               # Durable definitions (characters, aliases, locations, objects)
    events/                 # Chapter event logs (append-only timeline mutations)
    state/
      snapshot.yml          # Compiled current state snapshot (rebuildable)
  spec/
    premise.md              # High-level story premise
    guardrails.md           # Plot and structural rules
    chapters.yml            # Book structure and chapter plan
    model-routing.yml       # Model configuration mapping
  changes/
    chapter-NN/             # Staging workspace for active chapter drafting
  chapters/
    chapter-NN/             # Canonical compiled chapter drafts
      chapter-review.md     # Required compiled-chapter pacing/read-through review
```

---

## 6. Testing

Run the automated test suite to verify code correctness and validator performance:
```bash
python -m pytest tests/
```
