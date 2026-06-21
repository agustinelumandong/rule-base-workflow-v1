# Rulebook Generation

Use this to create or update `rulebook.md` and `mood-lock.md` from the target book source.

Read `source-format-scan.md` first. If it does not exist, run:

```bash
bf init books/<book-slug>
```

## `rulebook.md`

Create a durable series bible with these sections:

- Source format: source file used, detected source sections, chapter-list detail, length target source, and missing source fields.
- Series overview: title, genre, length target, premise, core themes.
- Returning character profiles: name, aliases, role, appearance, personality, backstory, internal conflict, skills, weaknesses, gear, weapons, horse, voice, POV rules, and current physical condition carried from the prior book.
- New character profiles: for every character introduced in this book, include — name, aliases, role in the story (wagon member, gunman, driver, etc.), one physical marker for quick identification, voice note (how they speak), and private motive or secret (what they really want or hide).
- World and setting: primary locations, geography, law and order, social pressure, economy, hazards. Include a **Setting Pressure List**: the specific terrain features, crossings, weather events, supply limits, or repair demands that will force decisions in this book.
- Continuity facts: timeline, prior wounds, alliances, grudges, dead characters, known secrets.
- Series arc: recurring conflict, unresolved betrayal, future threat, romantic tension, next-book hook.
- Current Book Locks: book-specific banned names, allowed exceptions, plot-mechanics constraints, and style priorities for the current target book by default. Do not use this section to bypass project-level bans such as globally banned names. Broader series/system cleanup must be explicit.
- Plot Mechanics Guardrails: when the source uses a frame-up, counterfeit item, false evidence, altered brand, planted clue, hidden saboteur, or witness confession, state the practical mechanism and proof path. Name who can know the truth, why they know it, what physical evidence exists, and how the tactic preserves rather than destroys the evidence needed for discovery.
- Ending State for Book N+1: bullet list of where each major character stands at the book's close — who is dead/alive/escaped/compromised, what secrets are destroyed or still hidden, what debts or obligations carry forward, any world-level change, and any named hook for the next book.
- Unknowns: important missing facts marked as `UNKNOWN`.

## Length Target Source

Use this priority when filling the rulebook length target:

1. User-provided target.
2. Source bible or outline target.
3. Existing rulebook target.
4. Default `~30,000 words`.

Store the target source in the rulebook. Treat the target as book-level planning guidance only.

If the source includes individual chapter word counts, preserve them as source guidance. Do not convert a total book target into uniform chapter quotas.

## `mood-lock.md`

Create a short tone file with:

- Genre and atmosphere.
- Historical/time-period assumptions from source.
- Prose style constraints.
- Vocabulary direction.
- Dialogue direction.
- Violence/action direction.
- What the manuscript must avoid.

For Western books, reference `.agents/skills/western-manuscript-style/` and its reference files for style, dialogue, and revision rules.

## No Invention Rule

Do not invent named places, backstory events, relationships, or series mythology beyond the source. If a fact is necessary but absent, mark it as `UNKNOWN` and continue where possible.

## Current-Book Name Locks

If the user gives a current-book banned name, add it to `rulebook.md` under `Current Book Locks` and apply it to the active book's new outline, planning artifacts, and drafts by default. Run a broader replacement through prior books, compiled manuscripts, research packs, or old context packets only when the user explicitly asks for a series-wide or system-forward cleanup and accepts that old-book compatibility is not required.

If a requested book-local exception conflicts with `AGENTS.md` or another project-level rule, do not bypass the project rule through a local setting. Flag the conflict in `Unknowns` or ask the user to approve changing the higher-priority rule.

## Frame-Up And Evidence Mechanics

When a book uses a setup such as altered cattle brands, counterfeit goods, planted proof, forged papers, or a witness confession:

- record the antagonist's practical tactic,
- record why the evidence survives long enough to be discovered,
- record who knows the antagonist's identity and why,
- record any physical proof the protagonist can inspect,
- keep the villain's power personal, outlaw, coercive, or tactical rather than institutional, property-based, business-based, or political.

## Outline Quality Gate

Before generating the rulebook, verify the source outline meets the standards in [outline-generation.md](outline-generation.md). If the outline is missing required sections (Setting Function, Story Pattern, Hard Story Guardrails, Ending State for Book N+1), flag them as `UNKNOWN` in the rulebook and ask the user whether to fill them now or proceed with gaps.
