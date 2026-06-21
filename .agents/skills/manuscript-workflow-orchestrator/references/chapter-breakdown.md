# Chapter Breakdown

Use this to create `chapter-summaries.md` and chapter-folder scene breakdowns.

Read `source-format-scan.md` before generating chapter summaries or beats. Use it to determine whether the source chapter list includes titles, summaries, hooks, tension notes, transition notes, or individual chapter word counts.

If `source-format-scan.md` says a chapter detail is missing, do not invent it. Mark missing values as `UNKNOWN` unless the chapter source itself implies the detail clearly.

## `chapter-summaries.md`

For each chapter and epilogue, include:

- Chapter number and title.
- **Chapter Function:** A single-phrase label stating what this chapter structurally accomplishes within the story pattern (e.g., `moves the party`, `exposes a secret`, `worsens trust`, `tightens pursuit`, `closes the distance`, `reveals a lead`, `turns an ally`, `exhausts a resource`). Use the story pattern's chapter function rule from the source outline. If no chapter function rule exists in the source, derive the label from the chapter's dominant required movement.
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
- Do Not Invent: names, places, motives, lore, events, or corporate/business/syndicate/property disputes the agent must not add.
- Context Match Check: source match, no skipped plot movement, no unsupported additions, prior continuity preserved, next beat set up without invented context, and no introduction of forbidden business/syndicate schemes (plots must focus on classic Western adventure).
- POV owner if clear from source; otherwise mark `UNKNOWN`.
- Optional pacing fields when useful: Pacing Class, Elastic Range, Why This Beat Is Short/Long, Expansion Permission, and Reference Rhythm Note.
- Optional series-strength fields when source-supported: Hero Cost, Villain Presence, Supporting Agency, Quiet Humanizing Beat, Legacy Pressure Payoff, Proof/Consequence Payoff, and Evidence/Frame-Up Logic.

Beat count is source-determined. Do not force every chapter into the same number of beats. Create one beat for each meaningful required story movement, emotional turn, tactical transition, or continuity exit in the source chapter. Add a transition beat only when the story would otherwise jump past necessary context. Stop when the chapter's required movement and continuity out are complete.

For books with split POV threads (e.g., two protagonists on separate routes converging), maintain a **POV Thread Tracker** at the top of `chapter-summaries.md`. List each thread's current position and the target convergence chapter. When generating beats for split-POV chapters, label each beat with its thread (`Thread A`, `Thread B`, or `Converged`) and verify the threads are moving at a compatible pace toward the convergence point.

Use a variable beat-count policy:

- Quiet setup, aftermath, travel, or mystery-pressure chapters usually need 2-3 beats.
- Standard investigation, alliance, rescue setup, scouting, or infiltration chapters usually need 3-4 beats.
- Action, chase, siege, crossing, climax, major reveal, or turning-point chapters usually need 4-6 beats.
- Major climaxes may use 5-7 beats only when the source has enough distinct stages.
- Never add filler beats to hit a count.
- Never compress distinct action stages, tactical turns, or emotional consequences into one beat just to keep chapters uniform.
- After generating all chapter breakdowns, scan the beat-count spread. If every chapter has the same count, treat that as a planning defect and rebalance before drafting.

## Scene Intent Rotation

Every beat should include an explicit intent label from this set:

- `high-intensity action`
- `alliance/strategy`
- `emotional consequence`
- `institutional pressure`
- `recovery/repair`

Rotate these intents across chapters where source supports it. Do not leave three consecutive chapters with the same dominant intent without a direct character consequence shift.
- If a beat is systems-heavy, it must still close with a concrete consequence for at least one named character before moving to the next beat.
- If systems-only transitions happen, add a sensory/action anchor line before the chapter transition.

Do not use fixed numeric lengths. Use natural scope labels instead:

- `summary beat`
- `full scene beat`
- `transition beat`
- `action beat`
- `emotional beat`

When a chapter pacing plan exists, use it to avoid artificial same-size chapters. Pacing guidance is elastic. A `~1000` beat means a natural range such as roughly `900-1200`, not an exact target. If the source supports less, stop short. If the source supports more, allow more. Never pad, force uniform chapter length, or invent story to hit a range.

When the source scan shows individual chapter word counts, preserve those counts as advisory source guidance in pacing fields. When the source scan shows no individual chapter word counts, do not create exact chapter targets from the book-level target.

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

### Pacing Guidance

- **Pacing Class:** [lean, standard, expanded, major, epilogue/teaser, or UNKNOWN.]
- **Elastic Range:** [Optional natural range such as `~1000`, meaning roughly `900-1200` only if source-supported.]
- **Why This Beat Is Short/Long:** [Story reason based on source movement, not word-count pressure.]
- **Expansion Permission:** [What may be deepened without adding unsupported story.]
- **Reference Rhythm Note:** [Optional high-level rhythm note; do not copy reference content.]

### Western Series Strength

- **Hero Cost:** [If source-supported, the protagonist's mistake, guilt, hard choice, or emotional cost beyond wounds; otherwise `UNKNOWN`.]
- **Villain Presence:** [If source-supported, how the villain appears through personal threat, outlaw leverage, or direct pressure; never through land, property, business, or political-machine control.]
- **Supporting Agency:** [If source-supported, what a supporting character chooses, risks, studies, resists, or changes without waiting for the protagonist.]
- **Quiet Humanizing Beat:** [If source-supported, the brief lower-pressure beat that makes a rescued, hostage, family, or revenge-stake character feel like a person before the climax; otherwise `UNKNOWN`.]
- **Legacy Pressure Payoff:** [If source-supported, the concrete prior wound, dead ally, old command, mark, ledger, or remembered sign that makes a series-arc villain confrontation personal; otherwise `UNKNOWN`.]
- **Proof/Consequence Payoff:** [If source-supported, evidence, public courage, exposed truth, reputation cost, rescue consequence, or moral result beyond gunfire.]
- **Evidence/Frame-Up Logic:** [If source-supported, how planted evidence, altered brands, forged papers, counterfeit goods, witness knowledge, or sabotage works in practical terms. Identify who knows what, why they know it, and what physical proof survives. If not relevant, write `UNKNOWN`.]

### Beat Instructions

- **Opener:** [Detail exactly how the beat must start.]
- **Action:** [Physical actions, setting details, and plot movements required in this beat. Include at least one terrain or environmental element that forces a decision, slows movement, causes damage, or reveals character through labor: a crossing, a repair, a weather change, a supply problem, a dead drop, a sign read. Do not allow the setting to be passive scenery.]
- **Conflict:** [Interpersonal tension, physical conflict, or obstacle to resolve/escalate.]
- **Emotional/Thematic Beat:** [The emotional pressure or theme this beat must carry.]
- **Chapter Function:** [Single-phrase label from the source story pattern that names what this chapter accomplishes. Must match the chapter-summaries Chapter Function label.]
- **Rule Check:** [1-2 critical style or continuity rules for this beat.]

### Context Match Check

- It matches the source chapter summary.
- It does not skip required plot movement.
- It does not add unsupported characters, locations, motives, or backstory.
- It preserves prior continuity.
- It sets up the next beat without forcing invented context.
- It does not introduce plots or details centered around syndicates, water rights, land grabs, property disputes, organized corruption, business conspiracies, or business schemes. All conflicts must focus on classic Western adventure themes (outlaws, bounty hunters, manhunts, betrayals, trail survival).
- It preserves current-book name locks by default, and rewrites prior-book continuity only when a series-wide or system-forward cleanup is explicitly in scope.
- If the beat relies on a confession, planted clue, stampede, altered brand, counterfeit object, or frame-up, the mechanism is practical and source-supported.
```

## `chapters/chapter-XX/scene-breakdown.md`

For each chapter, list scenes with:

- Scene number.
- POV.
- Location.
- Scene purpose.
- Pacing class and elastic range when useful.
- Opening action or pressure.
- Conflict.
- Required story facts.
- Emotional/thematic beat.
- Exit hook or transition.

If source detail is too thin, mark missing values as `UNKNOWN` rather than inventing.
