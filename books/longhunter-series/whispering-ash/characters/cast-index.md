# Cast Index - Whispering Ash

This folder is the detailed character layer for Book One. Keep `phase-0.md` as the story outline, keep `rulebook.md` as the compact drafting contract, and use these files for full reusable character records.

## Ownership Rules

- `phase-0.md`: high-level cast summary and story role only.
- `characters/**/*.md`: approved character details, source extracts, relationships, locks, and phase-spanning continuity.
- `rulebook.md`: compressed facts used by drafting packets, especially POV, physical markers, voice, motive, and hard locks.
- `chapters/chapter-XX/continuity-out.md`: chapter-specific changes after drafting.

When a character fact changes, update the character file first, then mirror only drafting-critical facts into `rulebook.md`.

## Main Characters

| Character | Role | Profile |
| --- | --- | --- |
| Jake Moses | Protagonist; captive farm boy becomes an independent Long Hunter | `main/jake-moses.md` |
| Thorn Blackroot | Mentor; elder hunter who trains Jake | `main/thorn-blackroot.md` |
| Caleb Thorne | Ally; reclusive scout and cautious partner after escape | `main/caleb-thorne.md` |

## Antagonists And Rivals

| Character | Role | Profile |
| --- | --- | --- |
| War Chief Red Hollow | Recurring antagonist; leader with a personal stake in Jake's escape | `antagonists/red-hollow.md` |
| Winston McCrea | Rival; opportunistic trapper introduced late in Book One | `antagonists/winston-mccrea.md` |

## Supporting Characters

| Character | Role | Profile |
| --- | --- | --- |
| Anna Ray | Trading-post widow; brief pull toward white society without romance in Book One | `supporting/anna-ray.md` |

## Archetypes And Role Notes

| Archetype | Use |
| --- | --- |
| `archetypes/long-hunter.md` | Jake's final role and skill identity |
| `archetypes/frontier-mentor.md` | Thorn's functional role without softening the hierarchy |
| `archetypes/trading-post-widow.md` | Anna's role boundary and no-romance guardrail |

## Phase Connection

Phase documents should reference character files by path instead of duplicating full profiles. Chapter plans should continue naming active characters in source context locks. Future validation can check that each named character in a chapter plan has a profile here and that each POV character is marked `pov.allowed: true`.
