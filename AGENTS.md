# Manuscript Agent Instructions

Use these rules when helping with manuscript planning, drafting, editing, or workflow files in this project.

## Core Workflow

- Before drafting, use the available outline, series bible, character details, setting details, tone requirements, and chapter breakdown as source material.
- Plan before drafting: break chapters into beats or scenes before writing full prose.
- Include both plot beats and emotional or thematic beats so the story does not become only mechanical action.
- Review and refine beats before moving into full scene drafting.
- Draft scene by scene instead of generating an entire chapter at once.
- Do not use fixed numeric length targets for individual scenes during drafting; let the scene reach its natural length.
- Keep each scene locked to the requested POV. Avoid head-hopping or switching perspectives mid-scene.
- After drafting, run a continuity pass for names, timeline, setting, character facts, injuries, weapons, and prior events.
- Run a dialogue and voice pass so each character keeps a distinct voice, dialect, and manner of speaking.
- When compiling scenes, preserve all intended story content and make transitions smooth.
- When revising, preserve the established tone and style. Do not flatten the prose with generic cleanup.
- For final polish, prefer targeted/manual edits over full regeneration unless the user explicitly asks for a rewrite.

## Western Prose Style Lock

- Use literal prose. Avoid metaphors, similes, and personification unless the user asks otherwise.
- Avoid these AI echo words: absolutely, completely, relentless, massive, sharp, heavy, pure, extremely, perfectly.
- Prefer blue-collar 1800s vocabulary: iron, leather, dirt, lead, bone, granite.
- Avoid modern or clinical words such as velocity, fraction, trajectory, impact, visible, resolving.
- Avoid Texas slang unless the user specifically requests it.
- Keep dialogue short and direct.
- Avoid dialogue tags like "said," "asked," and "shouted" when the user requests em dash action anchors.
- When using em dash action anchors, format them with spacing like: `"Get on the horse." — Harlan tightened the cinch.`
- Avoid "-ing" sentence openers.
- Avoid repeated Name/Pronoun sentence loops, such as several consecutive sentences beginning with the same name or pronoun.
- Mix sentence lengths to create an uneven rhythm.
- Show objective action and result. Do not over-explain obvious details.
- Avoid internal monologue unless requested.
- Do not use "He felt," "He realized," or "He thought" when the user wants behavior-driven prose.
- Open chapter beats with mechanical action, sound, or physical strain instead of weather or scenery.
- Keep combat fast, grounded, and brutal. Avoid micro-mechanics, fleeing or begging survivors, and formulaic aftermaths.

## Templates

- Keep long reusable templates, such as the Series Bible template or Master Beat Generation prompt, in separate Markdown files instead of embedding them here.
- Treat `docs/workflow-v5.md` as the current source for the manuscript workflow and prompt templates.
- Use the local `.agents/skills/manuscript-workflow-orchestrator/` skill for full book workflow tasks: scanning a book folder, reading `phase-0.md`, creating rulebooks, setting mood locks, breaking down chapters, making scenes, and preparing drafting plans.
- Use the local `.agents/skills/western-manuscript-style/` skill for reusable Western prose drafting, beat generation, dialogue cleanup, continuity review, and style-lock enforcement.
- Use the local `.agents/skills/humanizer/` skill after Western style and continuity passes when a draft sounds generic, padded, promotional, overstructured, or AI-written. Preserve plot facts, POV, paragraph coverage, and Western tone.
- Treat `books/<book-slug>/phase-0.md` as the default book source pattern.

## Validation Commands

- After generating or changing `scene-breakdown.md`, chapter drafts, chapter expansions, or compiled chapters, run the context validator:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>
  ```
- Use the context validator before the length checker. Fix `FAIL` results before continuing; treat `WARN` results as review or expansion targets.
- For deeper chapter review, generate an AI semantic review prompt:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug> --chapter chapter-02 --ai-prompt
  ```
- After context validation passes or only warns, run the length checker:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>
  ```
- Use length results only as book-level planning guidance. Never pad scenes, force fixed beat/chapter word counts, or invent unsupported story to close the gap.
