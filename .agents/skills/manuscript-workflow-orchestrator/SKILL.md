---
name: manuscript-workflow-orchestrator
description: Run a manuscript project workflow from a book folder source file into rulebook, mood lock, chapter summaries, scene breakdowns, drafting plan, and review passes. Use when the user asks to do this book, scan a book folder, create a rulebook, set the mood, break down chapters, make scenes, create beats, run the manuscript workflow, draft from phase-0/phase-00/outline files, or add humanized cleanup after AI drafting.
---

# Manuscript Workflow Orchestrator

Use this skill to run the project workflow from book-folder source material into planning artifacts and drafting instructions.

## Source Priority

1. User request and named target folder.
2. `books/<book-slug>/phase-0.md`.
3. Fallback files in the target folder: `phase-00.md`, `outline.md`, `chapter-outline.md`.
4. Project workflow source: `docs/workflow-v5.md`.
5. Local style skill: `.agents/skills/western-manuscript-style/`.
6. Local cleanup skill: `.agents/skills/humanizer/`.

If no phase or outline source exists, stop and report the missing source. Do not invent book facts.

## Default Outputs

For a target folder such as `books/tex-cade/`, create or update:

- `rulebook.md`
- `mood-lock.md`
- `chapter-summaries.md`
- `chapters/chapter-XX/scene-breakdown.md`
- `chapters/chapter-XX/drafting-plan.md`
- `chapters/chapter-XX/chapter-XX.md`

## References

- Load [references/folder-scan.md](references/folder-scan.md) before choosing source and output paths.
- Load [references/rulebook-generation.md](references/rulebook-generation.md) for `rulebook.md` and `mood-lock.md`.
- Load [references/chapter-breakdown.md](references/chapter-breakdown.md) for chapter summaries, beats, emotional beats, and scene breakdowns.
- Load [references/drafting-pipeline.md](references/drafting-pipeline.md) for Phase 1 through Phase 4 drafting, review, and polish.
- Load [references/context-validator.md](references/context-validator.md) after chapter drafting, expansion, compilation, or revision to validate source match structure and generate AI semantic review prompts.
- Load [references/length-checker.md](references/length-checker.md) after drafting, expansion, compilation, or revision passes to measure progress toward the book-level target.
- Load [references/autonomous-loop.md](references/autonomous-loop.md) when the user asks to run the book, finish the manuscript, keep going until valid, or use an autonomous manuscript loop.

## Operating Rules

- Use Codex / ChatGPT 5.5 as the primary tool.
- Treat Gemini as optional secondary review only.
- Use broad book or chapter targets only for planning.
- Do not require fixed numeric lengths for beats or scenes.
- Run context validation before using length results to guide expansion.
- Use the length checker as an advisory progress report only; never pad or invent story to satisfy a target.
- Use the autonomous loop controller to decide stop/continue state after draft, repair, expansion, and validation passes. Codex performs prose edits; the script controls state and next action.
- For a full book check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>`
- For a length check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>`
- For an autonomous loop check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/<book-slug> --target-min 30000 --target-max 31000`
- Mark missing facts as `UNKNOWN` unless the missing detail blocks drafting, then ask the user.
- Use `.agents/skills/western-manuscript-style/` whenever drafting or revising Western prose.
- Use `.agents/skills/humanizer/` after style/continuity passes when the draft sounds generic, padded, promotional, overexplained, or AI-written.
- Humanizer cleanup must preserve plot, continuity, POV, Western tone, and source facts; it is a polish pass, not a rewrite license.
