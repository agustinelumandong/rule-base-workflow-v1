# Context Packets

Use context packets to keep chapter work token-balanced. A packet is a compact source bundle for one chapter. It is not a new source of truth and must not add story facts.

## Command

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py books/<book-slug> --chapter chapter-XX
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
- prior chapter `continuity-out.md` or prior scene continuity-out lines
- next chapter continuity need
- current chapter `scene-breakdown.md`
- agent checkpoint template

## Use Rules

- Use the packet for chapter drafting, repair, style cleanup, validation, and expansion.
- Do not load the full manuscript for normal chapter work.
- Do not load the full rulebook unless rebuilding planning artifacts or resolving a missing source fact.
- Refresh the packet after changing `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, or the chapter `scene-breakdown.md`.
- If the packet says a fact is missing, mark it `UNKNOWN` or ask if it blocks drafting.

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
- unresolved pressure for the next chapter
- what the next chapter must preserve

The next chapter packet should use this summary instead of loading the full prior chapter draft.
