# Western Style Lock

Use these rules when drafting or revising Western prose, chapter beats, action passages, or style-locked prompts.

## Literal Prose

- Use literal prose by default.
- Avoid metaphors, similes, and personification unless the user asks otherwise.
- Do not give the environment feelings, plans, or intentions.
- Keep descriptions physical, concrete, and grounded in tools, terrain, bodies, animals, buildings, weather, and labor.
- Show objective action and result. Do not explain obvious psychology or teach the reader what an action means.
- Never state an emotion directly. Show the physical behavior that reveals it.
- Never use lines that summarize an atmosphere or emotion ("Fear, if fear had a smell"). Force the reader to rely on physical reactions only.
- Do not stack contradictory sensory details in one sentence. Make setting physical and simple before poetic.

## Banned AI Echo Words

Avoid these words unless they appear in quoted source material or the user explicitly wants them preserved:

- `absolutely`
- `completely`
- `relentless`
- `massive`
- `sharp`
- `heavy`
- `pure`
- `extremely`
- `perfectly`

## Vocabulary

Prefer plain 1800s blue-collar vocabulary:

- iron
- leather
- dirt
- lead
- bone
- granite
- timber
- dust
- rope
- sweat
- blood

Avoid modern or clinical terms when a plainer period-grounded word can do the job:

- `velocity`
- `fraction`
- `trajectory`
- `impact`
- `visible`
- `resolving`
- `cost center`
- `synergy`
- `bandwidth`
- `stakeholder`
- `deliverable`
- `action item`
- `team player`
- `circle back`
- `move the needle`
- `low-hanging fruit`
- `deep dive`
- `take offline`
- `game changer`
- `paradigm`
- `disruption`

Avoid Texas slang unless the user specifically requests it.

## Written Notes And Messages

- Do not format in-story notes, letters, telegrams, posted warnings, or written messages with backticks or code blocks.
- Introduce written text clearly in prose so it cannot be mistaken for a prompt or leftover instruction.
- Use `The note read:` or `The message read:` before the written text when the scene includes a note, message, telegram, posted warning, or letter.
- Use double quotes only when a character speaks the words aloud.
- Prefer this form:

```text
Tex lifted the folded note.

The note read, in a hard, square hand:

Texas Cade comes to Powder River for public hanging, or the woman and children die before the sun clears the wall.

No one spoke.
```

## Cadence

- Avoid `-ing` sentence openers.
- Avoid repeated Name/Pronoun loops, such as several consecutive sentences beginning with the same character name or pronoun.
- Mix sentence lengths to create an uneven rhythm.
- Cut generic AI transitions and filler.
- Keep chapter or beat openings active: start with mechanical action, sound, or physical strain instead of weather or scenery.

## Behavior Over Thought

- Avoid internal monologue when behavior-driven prose is requested.
- Avoid phrases like `He felt`, `He realized`, or `He thought` when the user wants externalized tension.
- Show principles and tension through action, posture, silence, choices, and what a character refuses to do.
- Do not add a narrator conclusion after behavior has already shown the change. Lines such as `That mattered`, `That counted`, `That meant`, `Respect showed itself`, or `None of it made trust. It made use.` are examples, not the full rule; any line that explains meaning, status, motive, or relationship after shown behavior needs review.
- Prefer replacing narrator conclusions with new observable behavior: who steps back, who stops shoving, who hands over better work, who refuses to smile, who keeps silent.
- Every tracking deduction, route prediction, or behavioral judgment must show evidence first: track sign, terrain, horse condition, witness report, or prior knowledge. The reader must see why the character knows.

Prefer:

```text
After the ring broke apart, the youngest boys watched him from farther off.
Men who had once tested his shoulder with small shoves no longer did it without looking first.
A woman handed him snare cord instead of the water bucket.
No one smiled.
```

Avoid:

```text
After the ring broke apart, the village did not become kind.
It became careful.
Careful was worth more.
```

## Continuity Discipline

- Items lost or damaged do not reappear without an acquisition scene.
- Wound entry direction must match shooter position (no back-entry from frontal shooter).
- Characters described as dead or dying do not perform subsequent actions.
- Same character should not perform same physical action twice in consecutive paragraphs.
- Track equipment state: hat, rifle, saddle, coat, ammunition, horse condition across chapters.
- Track wound progression: location, severity, treatment, healing stage across chapters.
- Track gang/opposition count progression across chapters (no phantom respawns).

## Violence And Action

- Keep combat fast, grounded, and brutal.
- Avoid micro-mechanics that slow the fight into choreography.
- Avoid fleeing or begging survivors unless the user explicitly asks for that beat.
- Avoid formulaic aftermaths.
- Track weapons, wounds, positions, and who can see what.
- **Weapon Detailing:**
  - **Introduction & Setup:** Use full specific names (e.g., "matched pair of Colt .45 Peacemakers", "Winchester '73", "top-break Schofield").
  - **Action & Movement:** Shorten names for speed (e.g., "Tex fired twice", "He reached for the rifle"). Avoid confusion with twin weapons by using left/right identifiers rather than a generic "the Colt" (e.g., "his right-hand Peacemaker", "the left Colt", "the revolver").
  - **Close Detail:** Focus on sensory properties (e.g., "the blue worn silver at the muzzle", "worn walnut grips", empty, loaded, jammed, hot, smoking). Avoid dry catalog-style list specifications.
  - **Source Lock:** All historical details and weapon names must be sourced from the resolved `books/tex-cade/research-pack.md` (or the global series research-pack) to maintain historical accuracy and prevent hallucination.


## Narrative Conflict Restrictions & Variety

- Do not write plots or conflicts around syndicates, water rights fights, land grabs, property disputes, organized corruption, business conspiracies, or shady business schemes.
- Prioritize classic Western adventure themes and situations, such as:
  - Gunfighters drifting into town
  - Marshals getting gunned down by murderers
  - Outlaws threatening a town
  - Bounty hunters tracking dangerous fugitives
  - Revenge plots
  - Rescue missions
  - Manhunts
  - Stagecoach or train robberies
  - Family feuds
  - Missing person cases
  - Strangers with violent pasts
  - Killers hiding in plain sight
  - Escaped convicts
  - Cattle rustlers
  - Border trouble
  - Personal betrayal
  - Survival on the trail
