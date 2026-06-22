# Context Packets

Use context packets to keep chapter work token-balanced. A packet is a compact source bundle for one chapter. It is not a new source of truth and must not add story facts.

## Command

```bash
bf packet books/<book-slug> --chapter chapter-XX
```

Output:

```text
books/<book-slug>/chapters/chapter-XX/context-packet.md
```

## Packet Contents

Each packet should include:

- source chapter anchor from `phase-0.md` or fallback outline
- chapter summary
- relevant rulebook facts only
- compressed mood and style lock
- current chapter pacing guidance from `chapter-pacing-plan.md` when available
- prior chapter `continuity-out.md` or prior scene continuity-out lines
- next chapter continuity need
- current chapter `scene-breakdown.md`
- `continuity-out.md` Human Stakes Carried bullets for named characters carrying pressure into the next chapter
- prior hero-cost, supporting-agency, or proof/consequence notes when already established by chapter artifacts
- source-supported prior experience, wound, debt, guilt, duty, or pressure that should affect character choices in this chapter
- expected conversations that should be dramatized instead of summarized when they carry planning, bonding, friction, proof, or moral decisions
- major travel, route, message, or time transition that needs a physical bridge through labor, scouting, weather, fatigue, repairs, sign reading, or camp movement
- chapter-specific frontier-mechanics risks, such as ferries, wagons, horses, firearms, tracking clues, wounds, legal papers, brands, ledgers, or terrain
- agent checkpoint template

## Use Rules

- Use the packet for chapter drafting, repair, style cleanup, validation, and expansion.
- Do not load the full manuscript for normal chapter work.
- Do not load the full rulebook unless rebuilding planning artifacts or resolving a missing source fact.
- Refresh the packet after changing `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, `chapter-pacing-plan.md`, or the chapter `scene-breakdown.md`.
- If the packet says a fact is missing, mark it `UNKNOWN` or ask if it blocks drafting.
- If a betrayal, confession, witness turn, route arrival, or proof reveal lacks a setup/payoff reason, do not fill the gap from imagination. Mark it `UNKNOWN` and repair the outline, scene breakdown, or packet before drafting the beat.

## Rolling Continuity

After drafting or expanding a chapter, create or update:

```text
chapters/chapter-XX/continuity-out.md
```

Include:

- who is alive, injured, captured, missing, or newly committed
- where key characters end the chapter
- what changed in plot or power balance
- weapons, horses, wounds, evidence, or town facts that must persist
- hero-cost and supporting-agency consequences that must affect later choices
- unresolved pressure for the next chapter
- what the next chapter must preserve
- prior experience carried forward and the next choice it should influence, when source-supported
- proof, witness, route, or mechanics facts that later chapters must not contradict

The next chapter packet should use this summary instead of loading the full prior chapter draft.
