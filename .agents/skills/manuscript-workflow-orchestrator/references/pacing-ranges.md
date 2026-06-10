# Pacing Ranges

Use pacing ranges to avoid artificial same-size chapters while staying source-locked.

## Source Priority

1. Current book source: `phase-0.md`, fallback outline, and `source-format-scan.md`.
2. Current book planning artifacts: `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, and chapter `scene-breakdown.md`.
3. Current book `chapter-pacing-plan.md`.
4. Optional local reference analysis such as `references/timber/analysis/pacing-calibration.md`.

Reference rhythm is craft guidance only. It must not override the current book.

Root `references/` may be git-ignored and unavailable. If optional reference analysis is missing, build `chapter-pacing-plan.md` from the current book source, chapter summaries, and scene breakdowns only.

## Elastic Chapter Classes

- `lean`: setup, aftermath, simple transition, epilogue-style closure, or teaser.
- `standard`: investigation, travel, character movement, town pressure, or ordinary escalation.
- `expanded`: action chapter, major reveal, moral pressure, multi-scene escalation, or significant consequence.
- `major`: climax, siege, rescue, central confrontation, or major reversal.
- `epilogue/teaser`: short closure or forward hook.

## Elastic Range Rules

- Use `source-format-scan.md` to determine whether the source provides individual chapter word counts.
- Preserve source-provided chapter word counts as elastic guidance only.
- If the source only provides a book-level target, do not turn it into per-chapter quotas.
- `~1000` means a natural range, not an exact target.
- If source-supported material ends around `700`, stop at `700`.
- If the beat naturally needs `1300`, allow it when source-supported.
- Never pad to match a range.
- Never force uniform chapter length.
- Never invent characters, motives, lore, locations, or plot bridges to reach a range.

## Beat And Scene Fields

When pacing guidance is useful, add these optional fields to beats or scene breakdowns:

- `Pacing Class`
- `Elastic Range`
- `Why This Beat Is Short/Long`
- `Expansion Permission`
- `Reference Rhythm Note`

Keep these fields advisory. Context validation remains the gate before drafting or expansion.
