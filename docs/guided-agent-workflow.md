# Guided Agent Manuscript Workflow

This project currently uses a guided agent workflow for manuscript planning, drafting, expansion, validation, and polish. It is not a fully autonomous loop yet. The agent can do most of the work once prompted, but the user still decides when to start a pass, what goal to prioritize, and whether the result is acceptable.

## What This Workflow Is

The current system is a semi-autonomous manuscript workflow.

It has strong reusable parts:

- `books/<book-slug>/phase-0.md` as the main story source.
- `rulebook.md` for continuity, character facts, source hierarchy, unknowns, and length rules.
- `mood-lock.md` for tone, vocabulary, style, and prose constraints.
- `chapter-summaries.md` for chapter-level movement.
- `chapters/chapter-XX/scene-breakdown.md` for approved chapter beats.
- `chapters/chapter-XX/chapter-XX.md` for chapter drafts.
- `chapters/epilogue/epilogue.md` for the epilogue draft.
- `.agents/skills/manuscript-workflow-orchestrator/` for workflow process.
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
6. The chapter's `scene-breakdown.md`.
7. The current chapter draft.
8. `docs/workflow-v5.md` for long-form workflow guidance.

If a fact is missing, do not invent it. Mark it as `UNKNOWN` in planning files, or ask the user if the missing fact blocks drafting.

## Normal Guided Flow

Use this flow when the user says something like "do this book," "expand the book," "validate everything," or "continue the manuscript."

1. Scan the book folder.
2. Read `phase-0.md`.
3. Read or create `rulebook.md`.
4. Read or create `mood-lock.md`.
5. Read or create `chapter-summaries.md`.
6. Read or create each chapter's `scene-breakdown.md`.
7. Draft or expand chapter files from their own scene breakdowns.
8. Run context validation.
9. Run length validation.
10. Run style-risk scan.
11. Fix any failures or warnings that matter.
12. Report final status clearly.

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

For a book with a target of about `30,000` words:

- Below `30,000`: not finished if the user requires `30,000+`.
- Around `30,000`: acceptable if context, style, and story pass.
- `30,300-30,900`: good natural finishing range.
- Avoid exact-looking targets such as `30,000` or `30,500` if the user wants a natural manuscript count.
- Avoid pushing far past `31,000` unless the user asks.

## Validation Commands

Run context validation after drafting, expanding, or revising:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>
```

Run length validation after context validation:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>
```

Run style-risk scan on chapter drafts:

```bash
rg -n "absolutely|completely|relentless|massive|sharp|heavy|pure|extremely|perfectly|\bsaid\b|\basked\b|\bshouted\b|He felt|He realized|He thought|UNKNOWN|TBD|TODO|strict word count|Min Words|Max Words" books/<book-slug>/chapters/*/chapter-*.md books/<book-slug>/chapters/epilogue/epilogue.md
```

Expected final state:

- context validator returns `PASS`
- length checker has no warnings
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
Add whatever is needed to hit the word count.
```

```text
Invent more backstory to make it longer.
```

## Stop Rules

Stop a guided pass when:

- the target length range is reached
- context validator passes
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
