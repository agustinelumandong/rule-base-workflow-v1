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
5. Optional reference pattern skill: `.agents/skills/western-story-pattern-analyzer/`.
6. Local style skill: `.agents/skills/western-manuscript-style/`.
7. Local cleanup skill: `.agents/skills/humanizer/`.

If no phase or outline source exists, stop and report the missing source. Do not invent book facts.

## Default Outputs

For a target folder such as `books/tex-cade/`, create or update:

- `source-format-scan.md`
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
- Load [references/context-packets.md](references/context-packets.md) before chapter-level drafting, repair, validation, style cleanup, or expansion.
- Load [references/prompt-modes.md](references/prompt-modes.md) when choosing between planning, drafting, repair, style, validation, expansion, or final review work.
- Load [references/token-budget.md](references/token-budget.md) when the task risks loading the full manuscript, full rulebook, or unrelated chapter files.
- Load [references/pacing-ranges.md](references/pacing-ranges.md) when the user asks for uneven chapter rhythm, reference-guided pacing, elastic beat ranges, or help deciding which chapters deserve longer treatment.
- Load [references/continuity-out-template.md](references/continuity-out-template.md) when writing or reviewing `continuity-out.md` files after chapter drafting.

## Operating Rules

- Use Codex / ChatGPT 5.5 as the primary tool.
- Treat Gemini as optional secondary review only.
- Before rulebook or chapter planning, run the source format scan:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_source_format.py books/<book-slug>`
- Use `source-format-scan.md` to identify present/missing bible sections, chapter-list detail, and target source before normalizing artifacts.
- If no user, source, or rulebook word target exists, default to `~30,000 words` as book-level planning guidance only.
- Use broad book or chapter targets only for planning.
- Do not require fixed numeric lengths for beats or scenes.
- Use optional reference analysis only for high-level pacing and rhythm guidance; never copy reference prose, plot, characters, voice, or exact structure.
- Use `chapter-pacing-plan.md` to avoid artificial same-size chapters, while keeping the current book source as the authority.
- Run context validation before using length results to guide expansion.
- Use the length checker as an advisory progress report only; never pad or invent story to satisfy a target.
- Use the autonomous loop controller to decide stop/continue state after draft, repair, expansion, and validation passes. Codex performs prose edits; the script controls state and next action.
- For chapter-level work, build or refresh `chapters/chapter-XX/context-packet.md` and use prompt modes to keep context compact.
- For a full book check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>`
- For a narrative quality pass, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_narrative_quality.py books/<book-slug>`
- For a length check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>`
- For an autonomous loop check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/<book-slug> --target-min 30000 --target-max 31000`
- For a context packet, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py books/<book-slug> --chapter chapter-XX`
- For a context budget check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_context_budget.py books/<book-slug> --chapter chapter-XX --mode drafting`
- For a chapter pacing plan, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/plan_chapter_pacing.py books/<book-slug>`
- Mark missing facts as `UNKNOWN` unless the missing detail blocks drafting, then ask the user.
- Use `.agents/skills/western-manuscript-style/` whenever drafting or revising Western prose.
- Use `.agents/skills/humanizer/` after style/continuity passes when the draft sounds generic, padded, promotional, overexplained, or AI-written.
- Humanizer cleanup must preserve plot, continuity, POV, Western tone, and source facts; it is a polish pass, not a rewrite license.
- After drafting or expanding a chapter, write `continuity-out.md` using the required template in [references/continuity-out-template.md](references/continuity-out-template.md).
- For a fast style scan (with line numbers), run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_banned_words.py books/<book-slug>`
- For a continuity chain check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_continuity_chain.py books/<book-slug>`
- For a chapter gap check (source vs folders), run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_gaps.py books/<book-slug>`
