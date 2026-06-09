# Chapter Breakdown

Use this to create `chapter-summaries.md` and chapter-folder scene breakdowns.

## `chapter-summaries.md`

For each chapter and epilogue, include:

- Chapter number and title.
- One-paragraph summary.
- Main plot movement.
- Emotional or thematic turn.
- Continuity notes.
- Setup/payoff notes for later chapters.

Keep summaries concise and source-grounded.

## Beats

Generate beats from the source chapter outline. Each beat should contain:

- Beat title.
- Source Anchor: exact chapter, outline, or rulebook fact the beat comes from.
- Continuity In: what must already be true before the beat starts.
- Required action.
- Conflict or obstacle.
- Emotional or thematic pressure.
- Required Story Movement: what must change by the end of the beat.
- Continuity Out: what must remain true for the next beat or scene.
- Do Not Invent: names, places, motives, lore, or events the agent must not add.
- Context Match Check: source match, no skipped plot movement, no unsupported additions, prior continuity preserved, next beat set up without invented context.
- POV owner if clear from source; otherwise mark `UNKNOWN`.

Beat count is source-determined. Do not force every chapter into the same number of beats. Create one beat for each meaningful required story movement, emotional turn, tactical transition, or continuity exit in the source chapter. Add a transition beat only when the story would otherwise jump past necessary context. Stop when the chapter's required movement and continuity out are complete.

Do not use fixed numeric lengths. Use natural scope labels instead:

- `summary beat`
- `full scene beat`
- `transition beat`
- `action beat`
- `emotional beat`

Every beat must state the exact source chapter or scene detail it is based on. If a bridge fact is missing, write `UNKNOWN` instead of inventing the bridge.

## Beat Context Lock

Use this shape for every beat:

```md
## BEAT [Beat Number]: [Beat Title] (natural length, no padding)

### Source Context Lock

- **Source Anchor:** [Exact chapter/outline/rulebook fact this beat comes from.]
- **Continuity In:** [What must already be true before this beat starts.]
- **Required Story Movement:** [What must change by the end of this beat.]
- **Continuity Out:** [What must remain true for the next beat or scene.]
- **Do Not Invent:** [Names, places, events, motives, or lore the agent must not add.]

### Beat Instructions

- **Opener:** [Detail exactly how the beat must start.]
- **Action:** [Physical actions, setting details, and plot movements required in this beat.]
- **Conflict:** [Interpersonal tension, physical conflict, or obstacle to resolve/escalate.]
- **Emotional/Thematic Beat:** [The emotional pressure or theme this beat must carry.]
- **Rule Check:** [1-2 critical style or continuity rules for this beat.]

### Context Match Check

- It matches the source chapter summary.
- It does not skip required plot movement.
- It does not add unsupported characters, locations, motives, or backstory.
- It preserves prior continuity.
- It sets up the next beat without forcing invented context.
```

## `chapters/chapter-XX/scene-breakdown.md`

For each chapter, list scenes with:

- Scene number.
- POV.
- Location.
- Scene purpose.
- Opening action or pressure.
- Conflict.
- Required story facts.
- Emotional/thematic beat.
- Exit hook or transition.

If source detail is too thin, mark missing values as `UNKNOWN` rather than inventing.
