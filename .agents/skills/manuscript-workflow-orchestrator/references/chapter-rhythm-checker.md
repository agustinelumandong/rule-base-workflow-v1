# Chapter Rhythm Checker

Use the rhythm checker after context validation and length checks when the manuscript should avoid artificial same-size chapters.

## Command

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_rhythm.py books/<book-slug>
```

## What It Flags

- every normal chapter at or above 2000 words
- chapter spread too narrow
- too few lean chapters below 1800 words
- too many chapters above 2400 words
- mismatch between `chapter-pacing-plan.md` class and draft length

## Repair Rule

Rhythm repair is compression/rebalancing, not expansion.

Trim or compress:

- repeated physical action
- overlong aftermath
- loose transitions
- duplicated setting texture
- dialogue that repeats known pressure

Keep:

- source facts
- required story movement
- continuity in/out
- POV
- style lock

Run context validation again after rhythm repair.
