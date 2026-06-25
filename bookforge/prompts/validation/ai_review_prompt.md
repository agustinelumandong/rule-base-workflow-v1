# AI Chapter Context Review Prompt

Use any capable AI agent as the primary reviewer. A secondary model is optional for an extra review pass.

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
9. **Conflict Variety Check:** Does the chapter avoid syndicates, water rights fights, land grabs, property disputes, and shady business schemes or conspiracies? Does it focus on classic Western adventures (e.g. outlaws, manhunts, robberies, betrayals, trail survival, border trouble)?
10. **Hallucination Check:** Does the chapter introduce any unauthorized character history, lore, or backstory not present in the outline/bible?
11. **Plot and Character Consistency Check:** Are character names, roles, and locations consistent? Are all modern concepts, vocabulary, and slang avoided?
12. **Temporal Logic Check:** Is the travel duration realistic? Is the time of day and chronological order of events clear? Is there a believable timeline for injury recovery, arrivals, and confrontations?
13. **Dialogue and Summary Check:** Does important planning, bonding, friction, proof, or moral decision material happen in character voice when the reader needs the exchange, rather than only narrative summary?
14. **Behavior Over-Analysis Check:** Does the narration explain psychology, symbolism, motives, status, or subtext where action, silence, work, or direct speech would be stronger? Flag places where the prose first shows behavior, then adds a lesson or conclusion line unless that line adds new story information. Example phrases such as what mattered, counted, meant, proved, or changed are reference hints, not the full rule.
15. **Frontier Mechanics Check:** Are wagons, ferries, horses, reins, firearms, wounds, tracking clues, written proof, brands, ledgers, terrain, and weather physically plausible for the scene?
16. **Causality Check:** If the chapter uses betrayal, confession, witness knowledge, planted proof, route timing, or a villain mistake, does the source context support how it happens?
17. **Physical-Clue Inference Check:** Do tracks, wounds, drag marks, gear, clothing, and other physical signs support only conclusions the POV character could plausibly make? Flag any exact age, identity, motive, timing, or condition inferred from weak sign if later source facts contradict or narrow it.
18. **Distinct Voice and Age-Pressure Check:** Do major speakers sound distinct in phrasing and rhythm? For children, hostages, wounded people, frightened civilians, guides, and lawmen, does the dialogue match their age, role, fear, work, and pressure instead of making everyone sound like the same controlled adult?
19. **Character Development Check:** Do characters' decisions and reactions connect to their established past experiences, traumas, or personal history? Are emotional responses earned through prior setup rather than appearing without foundation? Does each return to a character issue add a new angle: fear, anger, disappointment, love, resignation, or moral challenge?
20. **Unsupported Expertise Check:** When a character tracks, predicts, or judges another person, is the evidence shown first? The reader must see why the character knows — through track sign, terrain, horse condition, witness report, prior knowledge, or direct observation. Flag any conclusion that sounds like magical knowledge.
21. **Chapter Pacing Check:** When read start to finish as one compiled chapter, where does the chapter drag, where does it rush, and does the emotional landing get enough on-page treatment?
22. **Break Opportunity Check:** Does any long uninterrupted passage hide a natural scene break created by a time shift, sleep/wake transition, location change, or handoff in pressure?

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

## Chapter Review Notes

- [State the strongest boredom point, rushed point, and any break opportunity in short direct bullets.]
```

If a fact is missing from source, mark it `UNKNOWN`; do not invent it.
