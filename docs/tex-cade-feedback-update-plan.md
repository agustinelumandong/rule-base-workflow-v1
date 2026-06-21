# Tex Cade Feedback Update Plan

This file converts the ChatGPT and Gemini feedback in `docs/comments.md` into a possible upcoming revision pass for `books/tex-cade/compiled-manuscript.md`.

The current manuscript is structurally valid. This plan is not a rebuild. It is a controlled polish pass focused on prose variation, character pressure, villain presence, and ending clarity while preserving the approved story.

## Current Status

- Manuscript: `books/tex-cade/compiled-manuscript.md`
- Source chapters: `books/tex-cade/chapters/`
- Current function: complete Western novella / serialized pulp story
- Current strength: clear town-liberation arc, strong Ranger protagonist, readable action, strong Blackwater atmosphere
- Main update target: variation and depth, not plot replacement

## Feedback Summary

### Strengths To Preserve

- Keep the classic lone Ranger Western structure.
- Preserve Tex Cade as restrained, observant, dangerous, and duty-bound.
- Preserve Blackwater Crossing as the emotional center of the story.
- Keep Sarah, Buck, Lila, and Sarah's son as the main supporting cast.
- Keep the clean escalation from arrival, intimidation, retaliation, hostage crisis, posse, street purge, jailhouse showdown, and departure.
- Preserve the Iron Spur / larger network hook unless the user chooses to revise it.

### Main Issues To Improve

- Prose rhythm is too repetitive across the full manuscript.
- Many scenes follow a similar pattern: Tex enters, observes, outlaw threatens, Tex answers briefly, violence erupts, town reacts.
- Tex can feel too untouchable.
- Crowe acts mostly through other men until the final showdown.
- Supporting characters can read as archetypes more than fully pressured people.
- Some thematic lines explain what the action already shows.
- The ending hook may feel too vague if the important name stays hidden.

## Verified Pattern Risks

These are not fatal issues, but they support the feedback:

- `did not` appears often enough to become noticeable.
- `No one` and `Nobody` are repeated as emphasis devices.
- The sentence rhythm leans hard on short declarative lines.
- The hard Western voice works, but it needs more variation over a 30,000+ word manuscript.

## Revision Goals

1. Improve sentence and paragraph rhythm without softening the Western tone.
2. Reduce repeated negative framing such as `did not`, `No one`, and `Nobody`.
3. Give supporting characters more pressure, choice, or flaw through behavior.
4. Make Crowe feel more present before the final jailhouse confrontation.
5. Give Tex at least one stronger cost, misread, or consequence without making him incompetent.
6. Keep the manuscript source-locked and avoid adding unsupported story.
7. Preserve the current length range unless a user-approved story change requires more prose.

## Pass 1: Rhythm And Repetition Polish

### Scope

Run chapter by chapter. Do not rewrite the whole manuscript at once.

### Fixes

- Combine some short sentence clusters where the rhythm becomes too clipped.
- Replace repeated `Tex did not...` lines with direct action where possible.
- Replace repeated `No one...` / `Nobody...` emphasis with visible behavior from the crowd.
- Keep short punch lines for violence, decisions, and chapter endings.
- Preserve literal prose. Do not add decorative metaphors or modern phrasing.

### Example Direction

Instead of:

```md
No one moved. Nobody spoke. Tex did not answer.
```

Prefer:

```md
Boots held to the boards. Men watched the dust between Tex and the gunman. Tex let the silence do the work.
```

Use this only as a pattern example, not exact manuscript text.

## Pass 2: Character Pressure Polish

### Sarah

- Show her control through store work, wounds, ledgers, her son, and hard choices.
- Let her disagree with Tex when stakes touch the town or her family.
- Avoid making her only the moral anchor or romantic possibility.

### Buck

- Show his age and limitation through practical choices, not speeches.
- Let his scout experience solve problems Tex cannot solve alone.
- Give him small moments of friction when Tex pushes too hard.

### Lila

- Preserve restraint around her backstory.
- Show her grudge through risk, aim, silence, and decisions.
- Avoid turning her into only the saloon-girl helper.

### Sarah's Son

- Keep him useful but not magically brave.
- Let him make one age-appropriate mistake or near-mistake if supported by the chapter context.
- Use him as the town's future, not as a sidekick.

## Pass 3: Tex Vulnerability And Cost

Tex should remain competent. The goal is not to weaken him, but to make victory cost something.

Possible source-safe options:

- A townsperson is wounded because Tex cannot control every angle.
- Tex misreads timing and must recover through discipline.
- Tex chooses order over comfort and someone resents him for it.
- Tex carries a visible physical cost through later chapters.
- Tex must accept help instead of solving the pressure alone.

Avoid:

- New tragic backstory.
- New romance drama.
- New personal villain connection unless already supported.
- Making Tex careless or foolish just to create drama.

## Pass 4: Crowe Presence Polish

Crowe does not need many direct scenes, but his pressure should be felt earlier.

Possible source-safe methods:

- Strengthen how Crowe's orders change the town's behavior.
- Show his control through ledgers, tolls, burned property, hostage choices, and men repeating his rules.
- Give his lieutenants more specific fear of failing him.
- Let townsfolk react differently when Crowe's name is spoken.
- Make the jailhouse confrontation feel like the visible form of pressure already present all book.

Avoid:

- Adding unsupported Crowe POV.
- Adding a new direct meeting if it breaks the approved outline.
- Explaining his full network too early.

## Pass 5: Theme Cleanup

Keep the theme of fear becoming resistance, but trust action first.

Review and reduce lines that explain the theme after the scene already shows it.

Watch for summary statements like:

- fear as arithmetic
- town learning courage
- law as order
- roads, tolls, and ownership explained too directly

Keep the best of these lines. Remove or convert the weaker repeats into action.

## Pass 6: Ending Hook Decision

The current ending with the hidden name creates mystery. It may also frustrate readers.

Two acceptable options:

### Option A: Keep The Name Hidden

Use if the goal is a pulp serial cliffhanger.

Requirements:

- Make sure the withheld name feels intentional.
- Keep the final image strong.
- Do not over-explain Iron Spur.

### Option B: Reveal The Name

Use if the goal is cleaner reader satisfaction.

Requirements:

- Reveal the name.
- Keep its meaning unclear.
- Do not explain the next book's plot.
- Preserve the sense that the next trouble has already begun.

## Revision Rules

- Edit source chapter files first, then recompile `compiled-manuscript.md`.
- Do not edit `compiled-manuscript.md` directly unless doing final formatting only.
- Preserve `phase-0.md`, `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, and scene breakdown facts.
- Do not add unsupported names, motives, backstory, locations, lore, relationships, or plot turns.
- Do not pad to hit word count.
- Keep the manuscript above 30,000 words and around the current natural range.
- Keep Western style locked: literal prose, direct dialogue, behavior over internal monologue.

## Suggested Chapter Priority

1. Chapters 1-3: reduce repeated arrival/threat/violence pattern early.
2. Chapters 4-6: deepen Lila, Sarah, and hostage consequences.
3. Chapters 7-8: vary rhythm around ambush, posse, and quiet preparation.
4. Chapters 9-10: keep action fast but reduce repeated negative framing.
5. Chapters 11-12: strengthen emotional cost and refusal without overexplaining.
6. Epilogue: decide whether to reveal or withhold the name.

## Validation After Each Pass

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/tex-cade
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/tex-cade
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_rhythm.py books/tex-cade
python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/tex-cade --target-min 30000 --target-max 31000
```

Run style scan:

```bash
rg -n "absolutely|completely|relentless|massive|sharp|heavy|pure|extremely|perfectly|\bsaid\b|\basked\b|\bshouted\b|He felt|He realized|He thought|UNKNOWN|TBD|TODO|strict[ ]word count|Min[ ]Words|Max[ ]Words" books/tex-cade/chapters/*/chapter-*.md books/tex-cade/chapters/epilogue/epilogue.md
```

Recompile:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/compile_manuscript.py books/tex-cade
```

## Acceptance Criteria

- Context validator remains `PASS`.
- Final manuscript remains above 30,000 words.
- Chapter rhythm remains natural, not artificially even.
- Repetition of `did not`, `No one`, and `Nobody` is reduced where practical.
- Supporting characters show more pressure through behavior.
- Crowe's presence is felt earlier without adding unsupported scenes.
- Tex remains competent but victory carries more cost.
- The ending hook is intentionally chosen, not accidental.
