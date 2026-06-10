# Guided Agent Manuscript Workflow

This project currently uses a guided agent workflow for manuscript planning, drafting, expansion, validation, and polish. It is not a fully autonomous loop yet. The agent can do most of the work once prompted, but the user still decides when to start a pass, what goal to prioritize, and whether the result is acceptable.

## What This Workflow Is

The current system is a semi-autonomous manuscript workflow.

It has strong reusable parts:

- `books/<book-slug>/phase-0.md` as the main story source.
- `rulebook.md` for continuity, character facts, source hierarchy, unknowns, and length rules.
- `mood-lock.md` for tone, vocabulary, style, and prose constraints.
- `chapter-summaries.md` for chapter-level movement.
- `chapter-pacing-plan.md` for optional elastic chapter pacing and uneven chapter rhythm.
- `chapters/chapter-XX/scene-breakdown.md` for approved chapter beats.
- `chapters/chapter-XX/chapter-XX.md` for chapter drafts.
- `chapters/epilogue/epilogue.md` for the epilogue draft.
- `.agents/skills/manuscript-workflow-orchestrator/` for workflow process.
- `.agents/skills/western-story-pattern-analyzer/` for optional reference rhythm analysis.
- `.agents/skills/western-manuscript-style/` for Western prose, POV, dialogue, and style rules.
- `.agents/skills/humanizer/` for removing AI-sounding prose after continuity and style are already correct.
- Validator scripts for context and length checks.

The system is guided because the user still prompts the next action, such as:

- create or refresh the rulebook
- generate chapter summaries
- make scene breakdowns
- draft a chapter
- expand the whole manuscript
- validate everything
- adjust final length
- create or refresh a chapter pacing plan
- clean AI-sounding prose

## What This Workflow Is Not Yet

This is not a fully autonomous loop.

A fully autonomous loop would repeatedly scan, draft, validate, repair, re-check, and stop when all target conditions are met without the user needing to prompt each step.

Right now, the agent can behave like a loop inside one requested task, but the user still starts the loop manually through chat.

## Standard Book Folder Shape

Use this layout for a book project:

```text
books/<book-slug>/
├── phase-0.md
├── rulebook.md
├── mood-lock.md
├── chapter-summaries.md
├── chapter-pacing-plan.md
└── chapters/
    ├── chapter-01/
    │   ├── scene-breakdown.md
    │   ├── drafting-plan.md
    │   └── chapter-01.md
    ├── chapter-02/
    │   ├── scene-breakdown.md
    │   ├── drafting-plan.md
    │   └── chapter-02.md
    └── epilogue/
        ├── scene-breakdown.md
        ├── drafting-plan.md
        └── epilogue.md
```

For Tex Cade, the active folder is:

```text
books/tex-cade/
```

## Source Priority

Use sources in this order:

1. The user's current instruction.
2. `books/<book-slug>/phase-0.md`.
3. `books/<book-slug>/rulebook.md`.
4. `books/<book-slug>/mood-lock.md`.
5. `books/<book-slug>/chapter-summaries.md`.
6. `books/<book-slug>/chapter-pacing-plan.md` when present.
7. The chapter's `scene-breakdown.md`.
8. The current chapter draft.
9. `docs/workflow-v5.md` for long-form workflow guidance.
10. Optional local reference analysis under `references/<name>/analysis/` for craft rhythm only.

If a fact is missing, do not invent it. Mark it as `UNKNOWN` in planning files, or ask the user if the missing fact blocks drafting.

Reference analysis is never a story source. It may guide pacing rhythm, but it must not override the current book folder.

## Normal Guided Flow

Use this flow when the user says something like "do this book," "expand the book," "validate everything," or "continue the manuscript."

1. Scan the book folder.
2. Read `phase-0.md`.
3. Read or create `rulebook.md`.
4. Read or create `mood-lock.md`.
5. Read or create `chapter-summaries.md`.
6. Read or create `chapter-pacing-plan.md` when uneven rhythm or reference-guided pacing is needed.
7. Read or create each chapter's `scene-breakdown.md`.
8. Draft or expand chapter files from their own scene breakdowns.
9. Run context validation.
10. Run length validation.
11. Run style-risk scan.
12. Fix any failures or warnings that matter.
13. Report final status clearly.

## Drafting Rules

Draft and expand from approved beats only.

Add source-supported material through:

- physical blocking
- tactical movement
- setting texture
- consequence after violence
- restrained dialogue pressure
- town reaction
- practical transitions
- behavior-driven emotion

Do not add:

- unsupported names
- new locations
- new motives
- new lore
- new backstory
- new relationships
- new plot turns
- filler just to hit length

## Length Rules

Length is book-level guidance only.

Do not use fixed scene, beat, or chapter word counts. Use length checks as planning signals, not padding instructions.

Do not make every chapter the same size. A natural manuscript should have lean, standard, expanded, major, and epilogue/teaser chapters depending on the source movement.

Elastic ranges are allowed only as planning guidance. For example, `~1000` means a natural supported range such as roughly `900-1200`, not an exact target. If the source supports less, stop short. If the source supports more, allow more only when the approved beat requires it.

For a book with a target of about `30,000` words:

- Below `30,000`: not finished if the user requires `30,000+`.
- Around `30,000`: acceptable if context, style, and story pass.
- `30,300-30,900`: good natural finishing range.
- Avoid exact-looking targets such as `30,000` or `30,500` if the user wants a natural manuscript count.
- Avoid pushing far past `31,000` unless the user asks.

## Reference-Guided Pacing

The optional `references/` folder can hold local reference books such as `references/timber`. This folder may be git-ignored and should not be required for normal book workflow.

Use reference books only for high-level craft analysis:

- chapter length variation
- scene density
- opening and ending patterns
- conflict escalation
- quiet beats and aftermath placement
- where long or short chapters naturally appear

Do not use reference books to copy:

- prose
- plot turns
- character names
- scene structure
- voice
- exact chapter pattern

Analyze split reference chapters with:

```bash
python .agents/skills/western-story-pattern-analyzer/scripts/analyze_reference_structure.py references/timber/timber-book-1-chapters
```

This writes optional local analysis under:

```text
references/timber/analysis/
```

If `references/` or `references/timber/analysis/` is missing, continue with the current book source only. Missing reference analysis must not block rulebook generation, scene breakdowns, drafting, validation, or expansion.

Generate a source-locked pacing plan with:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/plan_chapter_pacing.py books/<book-slug>
```

The output is:

```text
books/<book-slug>/chapter-pacing-plan.md
```

Use that file to decide which chapters deserve lean, standard, expanded, major, or epilogue/teaser treatment. The plan is advisory and must stay below `phase-0.md`, `rulebook.md`, `chapter-summaries.md`, and the chapter `scene-breakdown.md`.

## Validation Commands

Run context validation after drafting, expanding, or revising:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>
```

Run length validation after context validation:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>
```

Run chapter rhythm validation after length validation when chapter variation matters:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_rhythm.py books/<book-slug>
```

Run style-risk scan on chapter drafts:

```bash
rg -n "absolutely|completely|relentless|massive|sharp|heavy|pure|extremely|perfectly|\bsaid\b|\basked\b|\bshouted\b|He felt|He realized|He thought|UNKNOWN|TBD|TODO|strict[ ]word count|Min[ ]Words|Max[ ]Words" books/<book-slug>/chapters/*/chapter-*.md books/<book-slug>/chapters/epilogue/epilogue.md
```

Expected final state:

- context validator returns `PASS`
- length checker has no warnings
- rhythm checker has no warnings when natural chapter variation is part of the goal
- style-risk scan returns no matches

## How To Ask The Agent

Good guided prompts:

```text
Scan books/tex-cade and validate everything.
```

```text
Expand Chapter 6 from its scene-breakdown.md without adding new story facts.
```

```text
Expand the full book to around 30,300-30,900 words, not an exact-looking number, and validate after.
```

```text
Create a chapter pacing plan so the chapters do not all land around the same word count.
```

```text
Run a style cleanup pass using western-manuscript-style and humanizer, but preserve plot and POV.
```

```text
Check whether each chapter follows its scene-breakdown.md and report warnings.
```

Avoid prompts like:

```text
Make every chapter exactly 2,500 words.
```

```text
Make Tex Cade follow Timber's structure.
```

```text
Add whatever is needed to hit the word count.
```

```text
Invent more backstory to make it longer.
```

## Stop Rules

Stop a guided pass when:

- the target length range is reached
- context validator passes
- rhythm checker passes when chapter variation is required
- style-risk scan is clean
- the requested chapter or book task is complete

Pause and ask the user when:

- a missing fact blocks drafting
- the source files contradict each other
- a requested expansion would require inventing unsupported story
- three repair attempts fail on the same issue

## Current Autonomy Level

Current level: guided agent workflow.

The agent can run multi-step passes when prompted, but the user still controls when the pass starts and what goal matters most.

Future level: autonomous loop.

A future autonomous loop would add a controller command such as:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/<book-slug> --target-min 30300 --target-max 30900
```

That controller would:

1. scan the book folder
2. run validators
3. choose the next chapter needing work
4. generate an expansion or repair task
5. apply or request an LLM rewrite
6. re-run validators
7. repeat until stop rules pass
8. produce a final report

For now, keep using the guided workflow with explicit user prompts and validator-backed agent passes.
