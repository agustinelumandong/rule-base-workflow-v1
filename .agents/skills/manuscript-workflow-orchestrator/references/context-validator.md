# Context Validator

Use the context validator after chapter drafting, chapter expansion, chapter compilation, or any revision that may affect story facts.

## Commands

Run the deterministic validator for the whole book:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/tex-cade
```

Generate an AI semantic review prompt for one chapter:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/tex-cade --chapter chapter-02 --ai-prompt
```

Replace `books/tex-cade` and `chapter-02` with the target book folder and chapter slug.

## What The Script Checks

- Required book files exist.
- Chapter drafts, scene breakdowns, and drafting plans exist.
- Each scene breakdown has complete beat context-lock structure.
- `phase-0.md` chapter sections are parsed and matched to each chapter folder.
- Each scene breakdown is checked for overlap with its matching `phase-0.md` chapter source.
- Each chapter draft is checked for overlap with its matching `phase-0.md` chapter source.
- Beat `Source Anchor` and `Required Story Movement` fields are checked for draft coverage.
- Drafts are non-empty.
- Drafts avoid forbidden fixed word-count language.
- Drafts avoid unresolved `UNKNOWN`, `TBD`, or `TODO` markers.
- Drafts are scanned for style warnings such as AI echo words, modern/clinical terms, unwanted dialogue tags, and internal-monologue phrases.

Low source overlap is treated as a warning unless required files or beat structures are missing. This keeps the checker useful for short first drafts while still flagging chapters that need review before expansion.

## Scope Boundaries

Current-book name locks, rugged-dialogue preferences, conversation-summary concerns, behavior-over-analysis concerns, travel-bridge quality, and frame-up plausibility are review concerns unless the source or rulebook makes them deterministic facts. Do not turn subjective prose or pacing feedback into hard validator blockers without explicit user approval and focused tests.

If a book-local name lock exists in `rulebook.md`, apply it to the active target book's new planning and draft files by default. Scan old books, compiled prior manuscripts, research archives, or prior context packets for replacement only when the user explicitly requests a series-wide or system-forward cleanup and accepts that old-book compatibility is not required.

## What AI Must Review

Use any capable AI agent for semantic review when the automated validator reports source-overlap warnings or after major expansion. A secondary model is optional review only.

The AI review must compare the chapter draft against `phase-0.md`, `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, and that chapter's `scene-breakdown.md`.

The AI must answer:

- Does the chapter cover every approved beat?
- Does any scene skip required story movement?
- Does the chapter invent unsupported names, locations, motives, lore, backstory, or plot bridges?
- Does continuity in/out match the prior and next chapter?
- Does POV stay controlled?
- Does Western style lock hold?
- Does expansion deepen approved material instead of padding?

If the AI reports failures, revise the chapter or scene breakdown before continuing.

## Relationship To Length Checker

Run context validation before using length pressure to guide expansion. The length checker can identify underdrafted chapters, but context validation protects source match and style lock.
