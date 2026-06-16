# Chapter Rhythm Checker

Use the rhythm checker after context validation and length checks when the manuscript should avoid artificial same-size chapters.

## Command

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_rhythm.py books/<book-slug>
```

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_narrative_quality.py books/<book-slug>
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

## Targeted Rhythm Rebalance Pass

When `NEEDS_PACING_REBALANCE` appears, run one full check pass before opening a wider repair loop:

- identify the flagged overlong/high-variance chapter
- compress repeated systems-only passages
- anchor every non-combat transition with action + sensory detail
- preserve character-facing consequence beats and required source facts
