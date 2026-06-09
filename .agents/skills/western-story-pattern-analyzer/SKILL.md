---
name: western-story-pattern-analyzer
description: Analyze reference Western books at a high level for reusable craft guidance such as chapter rhythm, pacing, scene density, openings/endings, and conflict escalation. Use for studying reference folders like references/timber without copying prose, plot, characters, voice, or exact structure.
---

# Western Story Pattern Analyzer

Use this skill when a reference Western should inform craft rhythm without becoming a source to imitate.

## Rules

- Analyze structure only: chapter rhythm, pacing, scene density, openings, endings, escalation, quiet beats, and long/short chapter placement.
- Do not copy or imitate reference prose, scenes, characters, names, voice, exact plot turns, or chapter structure.
- Keep outputs compact and reusable across books.
- Treat reference analysis as optional craft guidance. The current book's `phase-0.md`, `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, and `scene-breakdown.md` remain the source of truth.

## Default Workflow

1. Run the analyzer on a split reference chapter folder.
2. Store outputs under the reference folder's `analysis/` directory.
3. Use the generated analysis only to calibrate natural variation, not to force a book to match the reference.

## Command

```bash
python .agents/skills/western-story-pattern-analyzer/scripts/analyze_reference_structure.py references/timber/timber-book-1-chapters
```

## Outputs

The script writes compact analysis artifacts:

- `reference-pattern.md`
- `chapter-rhythm.md`
- `scene-density.md`
- `opening-and-ending-patterns.md`
- `conflict-escalation-map.md`
- `pacing-calibration.md`

Use `.agents/skills/manuscript-workflow-orchestrator/` when applying this guidance to a current book.
