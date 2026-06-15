# AI Chapter Context Review Prompt

Use Codex / ChatGPT 5.5 as the primary reviewer. Gemini is optional secondary review only.

Review `{chapter_draft}` against these sources:

- `{phase_0}`
- `{rulebook}`
- `{mood_lock}`
- `{chapter_summaries}`
- `{scene_breakdown}`
- `research-pack.md` (if present in the context packet)

## Required Review

Answer these questions:

1. Does the chapter cover every approved beat in the scene breakdown?
2. Does any scene skip required story movement?
3. Does the chapter invent unsupported names, locations, motives, lore, backstory, or plot bridges?
4. Does continuity in/out match the prior and next chapter requirements?
5. Does POV stay controlled and avoid head-hopping?
6. Does the Western style lock hold?
7. Does the expansion deepen approved material instead of padding?
8. Are all period-specific details (weapons, transport, medical remedies, technology) historically accurate and grounded in the research facts? If any detail is missing, unverified, or incorrect, flag it as `[RESEARCH NEEDED]` in the Failures section.

## Output Format

Return a Markdown report with exactly these sections:

```md
# {chapter_label} Context Review

## Passes

- [List source-locked items that pass.]

## Warnings

- [List concerns that do not block drafting.]

## Failures

- [List source drift, skipped beats, unsupported invention, or style violations that must be fixed.]

## Required Fixes

- [List concrete edits needed before continuing.]
```

If a fact is missing from source, mark it `UNKNOWN`; do not invent it.
