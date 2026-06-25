# The AI-Assisted Manuscript Workflow

## Recommended Tool Stack

- **Primary agent:** Any capable AI coding agent (Codex CLI, Claude Code, Gemini CLI, Cursor, Copilot CLI, Zed, OpenCode, or equivalent) for structural mapping, prompt creation, manuscript drafting, error detection, editing passes, compilation, and final polish. BookForge is agent-agnostic; the `bf` CLI is the contract, not any specific agent.
- **Secondary model (optional):** A second model for an extra review pass on structural mapping, continuity checking, prompt review, or error detection.
- **Substitution:** Any preferred AI tool works. See `AGENTS.md` and `BOOKFORGE_V2_PLAN.md` §3 (Model Routing) for the agent-agnostic contract.

## Token-Balanced Operating Rules

- Choose a prompt mode before loading context: `planning`, `drafting`, `repair`, `style`, `validation`, `expansion`, or `final`.
- For chapter-level work, use `chapters/chapter-XX/context-packet.md` plus the chapter draft and scene breakdown instead of loading the full manuscript.
- Do not load the full rulebook unless rebuilding planning artifacts, resolving a blocked source fact, or doing final review.
- Refresh the context packet after changing `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, or the chapter `scene-breakdown.md`.
- Use the compressed style lock for routine prompts: Literal Western prose; no AI echo words; no modern/clinical terms; no dialogue tags when action anchors are requested; behavior over thought; source-locked.
- Validate context before style repair. Run style repair before length expansion.
- Compiled chapters now require `chapter-review.md` before the loop can treat them as complete.
- End agent passes with: Source Used, Mode, Changes Made, Risks, Next Action, and Stop/Continue.

## Reference-Guided Pacing

- Optional reference books, such as `references/timber`, may be analyzed for high-level rhythm only: chapter length variation, scene density, opening/ending patterns, conflict escalation, quiet beats, and long/short chapter placement.
- Root `references/` may be local and git-ignored. Missing reference books or generated reference analysis must not block the manuscript workflow.
- Never copy reference prose, plot, characters, voice, exact scenes, exact turns, or exact chapter structure.
- The current book source always wins: `phase-0.md`, `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, and chapter `scene-breakdown.md`.
- Use `chapter-pacing-plan.md` to prevent every chapter from landing around the same size.
- Elastic ranges are planning guidance. `~1000` means a natural supported range such as roughly `900-1200`, not an exact target.
- Never pad, force uniform chapter length, or invent unsupported story to hit a range.
- Optional beat-level pacing fields such as `Beat Weight`, `Beat Development Floor`, and `Why This Beat Matters` are review tripwires, not draft-time quotas.

## Context Packet And Rolling Continuity

- A context packet is a compact chapter source bundle. It is not a new source of truth.
- Each packet should include the source chapter anchor, chapter summary, relevant rulebook facts, mood/style summary, prior continuity out, next continuity need, and current scene breakdown.
- After drafting or expanding a chapter, create or update `chapters/chapter-XX/continuity-out.md`.
- The continuity-out file should record who is alive or injured, where key characters end, what changed, unresolved pressure, and what the next chapter must preserve.
- The next chapter should use prior `continuity-out.md` instead of loading the full prior chapter draft.

## Prompt Modes

- **Planning:** Build or refresh rulebook, mood lock, chapter summaries, scene breakdowns, and drafting plans.
- **Drafting:** Write prose from the context packet and approved scene breakdown only.
- **Repair:** Fix validator, loop, source-drift, continuity, or beat-coverage issues only.
- **Style:** Apply Western style and humanizer cleanup without changing story facts.
- **Validation:** Compare draft against source files, rulebook, chapter summary, and scene breakdown.
- **Chapter Review:** Read the compiled chapter start to finish, record slow spots, rushed spots, and break opportunities in `chapter-review.md`, and set decision to `ready`, `needs-rhythm-fix`, or `needs-beat-expansion`.
- **Expansion:** Deepen approved beats after validation passes; never add unsupported story.
- **Final:** Whole-book review, compilation, or cross-chapter checks.

## Phase 0: Pre-Production & World-Building

- **Run a Source Format Scan:** Before building the rulebook, scan the source bible or outline and create `source-format-scan.md`. Use it to identify which sections are present, which fields are missing, whether the chapter list has titles/summaries/hooks/tension/transition notes, and whether the source provides individual chapter word counts.
- **Resolve the Book-Level Target:** Use a user-provided target first, then the source bible target, then an existing rulebook target. If none exists, default to `~30,000 words` as book-level planning guidance only.
- **Do Not Force Uniform Length:** If the source has chapter word counts, preserve them as elastic guidance. If the source only has a total target, do not turn it into per-chapter quotas.
- **Create a Series Bible:** Before drafting a single word, establish a master document to ensure consistency. This must include your characters' physical descriptions, backstories, and highly specific setting details.
- **Establish the Tone:** Include specific "Western" tonal requirements in your initial foundation prompts to firmly establish the correct historical and regional atmosphere from the very start.

## Phase 1: Foundation & Beat-Mapping

- **Start with the Chapter Breakdown:** Begin with your established chapter outline (for example, your breakdown for Book 3, Blood on the Alkali).
- **Generate Chapter Beats:** Prompt the AI to create a beat-by-beat breakdown for each chapter.
  - Copy and Paste Master Beat Template for AI to create a beat for each chapter with that setting. (Below)
  - **NOTE: Plot and Emotion:** In addition to plot beats, explicitly prompt the AI to include "emotional beats" or "thematic check-ins" to ensure narrative resonance isn't lost to pure mechanics.
  - **Scope Guidance:** Use broad book or chapter targets only for planning. Do not require fixed numeric lengths for beats or scenes.
  - **Source-Determined Beat Count:** Do not force every chapter into the same number of beats. Create one beat for each meaningful required story movement, emotional turn, tactical transition, or continuity exit in the source chapter. Add a transition beat only when needed. Stop when the chapter's required movement and continuity out are complete. Quiet setup, aftermath, travel, or mystery-pressure chapters usually need 2-3 beats; standard investigation, alliance, rescue setup, scouting, or infiltration chapters usually need 3-4 beats; action, chase, siege, crossing, climax, major reveal, or turning-point chapters usually need 4-6 beats, with 5-7 allowed only when the source has enough distinct stages. If every chapter has the same beat count, treat that as a planning defect and rebalance before drafting.
  - **Elastic Pacing:** If `chapter-pacing-plan.md` exists, use its pacing class to decide which chapters and beats deserve lean, standard, expanded, or major treatment. Treat all ranges as flexible and source-supported.
  - **Token Balance:** For chapter-level beat work, use the chapter context packet when available instead of loading the full manuscript or full rulebook.
- **Operator Intervention:** Review and manually edit these beats as they are generated to ensure the narrative stays on track before moving to the drafting phase.

## Phase 2: Structural Review & Continuity

- Now, use your AI agent to begin writing the manuscript using the constructed prompts.
- **The Golden Rule of Scene Generation:** Moving forward, do not apply word count instructions to individual scenes. This prevents the AI from inserting unnecessary fluff and filler words.
- **Continuity Pass:** Feed the drafted material back into the AI to scan specifically for continuity errors.
- **Scene-by-Scene Structuring:** Have the AI break the chapter down scene-by-scene, adding transitional bridges and applying fixes for any continuity errors detected in the previous step.

## Phase 3: Drafting & Micro-Editing

- **Pre-Draft & Pre-Finalization Checks:** Before drafting and before finalizing each chapter, run these three mandatory workflow checks:
  1. **Hallucinations:** Ensure the draft does not introduce unauthorized backstory, character lore, motives, or relationships not defined in the outline/bible.
  2. **Plot Consistency:** Verify character names, roles, and locations remain consistent. Avoid modern concepts and vocabulary.
  3. **Temporal Logic:** Ensure realistic travel times, track the time of day, and keep chronological sequences (such as injury recovery and arrivals) believable.
- **Scene Drafting:** Prompt the AI to write out the chapter one scene at a time based on the new, error-free breakdown.
  - **Control the POV:** Explicitly instruct the AI on the exact "Point of View" (POV) for that specific scene. This is crucial to avoid "head-hopping" (switching perspectives mid-scene), which is a common AI error.
- **Microscopic Error Detection:** Once the chapter is drafted, run a highly detailed error-detection pass. The AI's only job here is to flag inconsistencies or grammatical issues and suggest solutions.
- **Dialogue & Voice Pass:** Before compiling, run a pass specifically focused on dialogue. Ask the AI to ensure each character has a distinct "voice" or "dialect," which is vital for the authenticity of a Western manuscript.
- **Compilation & Integration:** Use those suggested solutions as your next prompt. Have the AI apply the fixes and compile the individual scenes into one seamless, cohesive chapter. Note: don’t include word count instruction let the scene write itself.
- **The Final AI Pass:** Run one last automated read-through on the compiled chapter to catch any final glaring errors, then write `chapter-review.md`.

## Phase 4: The Human Polish

- **Manual Read-Through:** The author must do a final, comprehensive read-through. The AI will still make mistakes, and human intuition is required for pacing and emotional resonance.
- **Required Compiled-Chapter Review:** Even when the final human polish happens later, the workflow now requires a chapter review artifact before the loop can mark the chapter complete.
- **Manual Edits Only:** When you spot an error at this stage, change it manually. Do not feed the text back through the AI, or you risk flattening the established tone and losing the specific results you’ve built.

## The End Result

By following this method, you will comfortably hit—and likely exceed—your target word count without relying on filler. This leaves your human editor with a rich, massive manuscript, giving them free rein to cut, polish, and get the book 100% ready for publication.

# Simplified Manuscript Workflow

Simplified, easy-to-follow version manuscript workflow broken down into plain English.

## Step 1: Getting Ready (The Prep Work)

- **Create a Rulebook:** Before you write anything, make a "Series Bible" that lists your characters' looks, backstories, and the specific settings of your world.
- **Set the Mood:** Make sure to tell the AI exactly what kind of historical or Western tone you want from the very beginning.

## Step 2: Planning the Chapter (The Blueprint)

- **Start with an Outline:** Take your general chapter idea and use an AI agent to break it down into smaller, step-by-step "beats".
- **Add Emotion:** Tell the AI to include emotional moments, not just plot actions. Give scope guidance instead of fixed numeric lengths so the AI does not pad or invent context.
- **Check the Work:** Read through these beats yourself and fix any mistakes so the story stays on track.

## Step 3: Writing and Fixing (The Assembly Line)

- **Drop the Word Counts:** use your AI agent to start drafting. Stop telling the AI how many words to write for each scene so it doesn't add useless filler.
- **Run Mandatory Workflow Checks:** Before writing or compiling, verify there are no hallucinations (invented lore/backstory), no plot/concept inconsistencies, and no temporal logic errors (travel speed, time of day tracking, recovery timeline).
- **Write Scene by Scene:** Have the AI write one scene at a time, making sure you tell it exactly which character's perspective to use.
- **Check for Errors and Voices:** Use any capable AI agent, to hunt for continuity mistakes and make sure every character's dialogue sounds distinct and authentic.
- **Stitch It Together:** use your AI agent to combine all the fixed scenes into one complete, seamless chapter without leaving anything out.

## Step 4: The Final Polish (The Human Touch)

- **Read It Yourself:** Sit down and read the whole chapter with your own eyes. The AI won't get the pacing or emotions perfectly right every time.
- **Fix It By Hand:** If you see a mistake, type in the fix yourself. Do not put the text back into the AI to fix it, or you risk ruining the unique style and tone you've worked hard to build.

# The Master Series Bible Template (MODIFY IF NEEDED)

## 1. Series Overview

- **Series Title:**
- **Working Titles (Books 1-X):**
- **Logline:** (One to two sentences summarizing the overarching plot of the entire series).
- **Core Themes:** (e.g., Revenge, redemption, frontier justice, survival).
- **Tone & Atmosphere:** (Specific keywords to feed the AI for the overall vibe—e.g., gritty, atmospheric, historically grounded, slow-burn tension).
- **Historical/Time Period Anchor:** (Exact year or era to ensure the AI uses era-appropriate technology and references).

## 2. Character Profiles (Duplicate for each character)

- **Name & Aliases:**
- **Role in Story:** (e.g., Protagonist, Antagonist, Primary Love Interest, Lawman).
- **Physical Appearance:** (Age, build, eye/hair color, distinct scars, typical clothing style. Be as specific as possible to prevent AI hallucinations).
- **Personality & Demeanor:** (e.g., Highly introverted, observant, blunt, quick-tempered).
- **Distinctive Voice & Dialect:** (How do they speak? Do they use specific regional slang, formal speech, short clipped sentences, or a specific accent? Crucial for the Phase 3 Dialogue Pass.)
- **Signature Gear & Mount:**
  - **Weapons:** (Specific makes and models, e.g., Winchester Model 1873, .45 Colt).
  - **Horse:** (Breed, color, temperament, e.g., large black gelding, steady Texas bay).
  - **Other:** (Signature knives, specific hats, pocket watches).
- **Backstory/Lore:** (Where did they come from? What formed them?)
- **Internal Conflict/Secret:** (What is driving them emotionally, or what are they hiding?)
- **POV Rules:** (Are we allowed in their head? What are the strict limitations of their perspective?)

## 3. World-Building & Settings

- **Primary Locations:** (Names of towns, saloons, specific ranches, or hideouts).
- **Geography & Terrain:** (e.g., Alkali flats, dense pine forests, dusty border towns. Describe the weather and environmental hazards).
- **Law & Order:** (How does justice work in this setting? Describe the local marshals, bounty hunters, or governing forces. Do not include local syndicates or organized corporate corruption).
- **Societal Norms & Tensions:** (Ongoing feuds, economic struggles, railroad expansions).

## 4. Undercurrents & Special Mechanics

- **Hidden Elements:** (Are there subtle supernatural undertones, binding contracts, or hidden identities the reader knows but the characters don't?)
- **Key Items/MacGuffins:** (Specific objects that drive the plot forward).

## 5. Overarching Series Arc

- **Book 1 Core Plot:**
- **Book 2 Core Plot:**
- **Book 3 Core Plot:**
- **The Final Destination:** (Where does the main character end up by the final book?)

# The Master Beat Generation Prompt Template (MODIFY IF NEEDED)

COPY AND PASTE THIS PROMPT TO GENERATE CHAPTER [X], BEAT [Y]:

Write Beat [Beat Number] for Chapter [Chapter Number] of the western series following the exact outline below. Write the beat at the natural length needed to cover the required action, conflict, and emotional turn. Do not pad for word count. Do not invent extra context to reach length. Use the chapter `context-packet.md` when available. Otherwise use only facts from `phase-0.md`, `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, and prior approved beats/scenes.

Before generating beats for a chapter, derive the beat count from the chapter source. Do not use a fixed beat count across chapters. Create one beat for each required story movement, emotional turn, tactical transition, or continuity exit. Add a transition beat only if the chapter would otherwise skip needed context. Quiet setup, aftermath, travel, or mystery-pressure chapters usually need 2-3 beats. Standard investigation, alliance, rescue setup, scouting, or infiltration chapters usually need 3-4 beats. Action, chase, siege, crossing, climax, major reveal, or turning-point chapters usually need 4-6 beats, with 5-7 allowed only when the source has enough distinct stages. After generating the book's chapter breakdowns, scan the beat-count spread; if every chapter has the same count, rebalance before drafting.

If `chapter-pacing-plan.md` exists, use it as optional pacing guidance. Add elastic pacing fields only when they help the chapter avoid artificial sameness. Do not treat `~1000`, `~1600`, or any range as a hard target. Stop short when the source runs out; allow more only when the approved beat requires it.

## SOURCE CONTEXT LOCK

- **Source Anchor:** [Exact chapter/outline/rulebook fact this beat comes from.]
- **Continuity In:** [What must already be true before this beat starts.]
- **Required Story Movement:** [What must change by the end of this beat.]
- **Continuity Out:** [What must remain true for the next beat or scene.]
- **Do Not Invent:** [Names, places, events, motives, or lore the AI must not add.]

## PACING GUIDANCE

- **Pacing Class:** [lean, standard, expanded, major, epilogue/teaser, or UNKNOWN.]
- **Elastic Range:** [Optional natural range such as `~1000`, meaning roughly `900-1200` only if source-supported.]
- **Why This Beat Is Short/Long:** [Story reason based on source movement, not word-count pressure.]
- **Expansion Permission:** [What may be deepened without adding unsupported story.]
- **Reference Rhythm Note:** [Optional high-level rhythm note; do not copy reference content.]

## NARRATIVE CONTEXT

[Insert Act/Arc Title here, e.g., ACT II: THE RANGER]. [Insert a 2-3 sentence summary of the current story situation, character roles, and immediate goals for this section of the book.]

## PROJECT LOCK – STRICT STYLISTIC CONSTRAINTS (DO NOT VIOLATE)

- **Narrative Conflict Restrictions:** STRICTLY FORBIDDEN from using plots centered around syndicates, water rights fights, land grabs, property disputes, organized corruption, business conspiracies, or shady business/corporate schemes. Keep plots locked to classic Western adventures (e.g. outlaws, bounty hunters, revenge, rescue, manhunts, stagecoach/train robberies, family feuds, escaped convicts, cattle rustlers, border trouble, betrayal, trail survival).
- **The Absolute Literalism Ban:** Prose must be 100% literal. Zero metaphors, similes, or personification. The environment does not have feelings or intentions (e.g., the wind does not "scream").
- **Purge AI Echo Words:** You are STRICTLY FORBIDDEN from using these words: absolutely, completely, relentless, massive, sharp, heavy, pure, extremely, perfectly.
- **Lexicon of Antiquity:** Use blue-collar, 1800s vocabulary (iron, leather, dirt, lead, bone, granite). Zero modern/clinical words (e.g., velocity, fraction, trajectory, impact, visible, resolving). Zero Texas slang.
- **Em Dash Continuity & Natural Dialogue:** ZERO dialogue tags (no "said," "asked," "shouted"). Dialogue must be short, direct, and anchored directly to a physical action using an em dash with proper spacing. (Example: "Get on the horse." — Harlan tightened the cinch.)
- **The Cadence & Variance Protocol:** ZERO "-ing" sentence openers. Eliminate all Name/Pronoun loops (e.g., do not start consecutive sentences with He... He... He...). Mix sentence lengths to create an uneven rhythm.
- **State Truth—Don't Teach It:** Show the objective result. Do not over-explain obvious details or feed the reader the psychological reasoning behind an action.
- **Behavior Over Thought:** Zero internal monologue. Do not use "He felt," "He realized," or "He thought." Show his principles and tension entirely through physical actions.
- **Chapter Openers Protocol:** The FIRST sentence of this chapter beat must be a mechanical tool action, a sound, or physical strain. Zero weather or scenery in the first paragraph.
- **The Character Lock:** [Insert Primary Character 1] and [Insert Primary Character 2] are the ONLY named characters. Minor roles must ONLY be referred to by their functional titles (e.g., the outlaw, the scout, the gang leader).
- **Violence Rules:** Combat must be fast, brutal, and grounded. No micro-mechanics. No fleeing or begging survivors. No formulaic aftermaths.

## BEAT [Beat Number]: [Beat Title] (natural length, no padding)

### Source Context Lock

- **Source Anchor:** [Exact chapter/outline/rulebook fact this beat comes from.]
- **Continuity In:** [What must already be true before this beat starts.]
- **Required Story Movement:** [What must change by the end of this beat.]
- **Continuity Out:** [What must remain true for the next beat or scene.]
- **Do Not Invent:** [Names, places, events, motives, or lore the AI must not add.]

### Pacing Guidance

- **Pacing Class:** [lean, standard, expanded, major, epilogue/teaser, or UNKNOWN.]
- **Elastic Range:** [Optional natural range such as `~1000`, meaning roughly `900-1200` only if source-supported.]
- **Why This Beat Is Short/Long:** [Story reason based on source movement, not word-count pressure.]
- **Expansion Permission:** [What may be deepened without adding unsupported story.]
- **Reference Rhythm Note:** [Optional high-level rhythm note; do not copy reference content.]

### Beat Instructions

- **Opener:** [Detail exactly how the beat must start. e.g., Start the chapter immediately on a mechanical action...]
- **Action:** [Describe the physical actions, setting details, and plot movements that must occur in this specific beat.]
- **Conflict:** [Describe the interpersonal tension, physical conflict, or obstacle to be resolved or escalated in this beat.]
- **Emotional/Thematic Beat:** [The emotional pressure or theme this beat must carry.]
- **Rule Check:** [Reiterate 1-2 critical rules the AI usually fails at for this specific beat type to ensure it pays attention. e.g., Ensure all dialogue strictly uses ONLY em dash action anchors. Absolutely zero "said" tags.]

### Context Match Check

Before accepting this beat, verify:

- It matches the source chapter summary.
- It does not skip required plot movement.
- It does not add unsupported characters, locations, motives, or backstory.
- It preserves prior continuity.
- It sets up the next beat without forcing invented context.
