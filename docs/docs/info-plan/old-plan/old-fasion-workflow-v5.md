# The AI-Assisted Manuscript Workflow - v5

## Recommended Tool Stack

- **Gemini**: Structural mapping, prompt creation, error detection, and editing passes.
- **Claude**: Primary manuscript drafter.
- **Note**: You can substitute these with any preferred AI tools.

## Phase 0: Pre-Production & World-Building

- **Create a Series Bible**: Before drafting a single word, establish a master document to ensure consistency. This must include your characters' physical descriptions, backstories, and highly specific setting details.
- **Establish the Tone**: Include specific "Western" tonal requirements in your initial foundation prompts to firmly establish the correct historical and regional atmosphere from the very start.

## Phase 1: Foundation & Beat-Mapping

- **Start with the Chapter Breakdown**: Begin with your established chapter outline (for example, your breakdown for Book 3, Blood on the Alkali).
- **Generate Chapter Beats** (Tool: Gemini): Prompt the AI to create a beat-by-beat breakdown for each chapter.
  - Copy and Paste Master Beat Template for AI to create a beat for each chapter with that setting. (Below)
  - **NOTE**: Plot and Emotion: In addition to plot beats, explicitly prompt the AI to include "emotional beats" or "thematic check-ins" to ensure narrative resonance isn't lost to pure mechanics.
  - **Word Counts**: Broad word count targets can be applied at this stage.
- **Operator Intervention**: Review and manually edit these beats as they are generated to ensure the narrative stays on track before moving to the drafting phase.

## Phase 2: Structural Review & Continuity

- Now, shift to Claude to begin writing the manuscript using the constructed prompts.
- **The Golden Rule of Scene Generation**: Moving forward, do not apply word count instructions to individual scenes. This prevents the AI from inserting unnecessary fluff and filler words.
- **Continuity Pass** (Tool: Gemini): Feed the drafted material back into the AI to scan specifically for continuity errors.
- **Scene-by-Scene Structuring** (Tool: Gemini): Have the AI break the chapter down scene-by-scene, adding transitional bridges and applying fixes for any continuity errors detected in the previous step.

## Phase 3: Drafting & Micro-Editing

- **Scene Drafting** (Tool: Claude): Prompt the AI to write out the chapter one scene at a time based on the new, error-free breakdown.
  - **Control the POV**: Explicitly instruct the AI on the exact "Point of View" (POV) for that specific scene. This is crucial to avoid "head-hopping" (switching perspectives mid-scene), which is a common AI error.
- **Microscopic Error Detection** (Tool: Gemini): Once the chapter is drafted, run a highly detailed error-detection pass. The AI's only job here is to flag inconsistencies or grammatical issues and suggest solutions.
- **Dialogue & Voice Pass** (Tool: Gemini): Before compiling, run a pass specifically focused on dialogue. Ask the AI to ensure each character has a distinct "voice" or "dialect," which is vital for the authenticity of a Western manuscript.
- **Compilation & Integration** (Tool: Claude): Use those suggested solutions as your next prompt. Have the AI apply the fixes and compile the individual scenes into one seamless, cohesive chapter. Note: don't include word count instruction let the scene write itself.
- **The Final AI Pass** (Tool: Gemini): Run one last automated read-through on the compiled chapter to catch any final glaring errors.

## Phase 4: The Human Polish

- **Manual Read-Through**: The author must do a final, comprehensive read-through. The AI will still make mistakes, and human intuition is required for pacing and emotional resonance.
- **Manual Edits Only**: When you spot an error at this stage, change it manually. Do not feed the text back through the AI, or you risk flattening the established tone and losing the specific results you've built.

## The End Result

By following this method, you will comfortably hit—and likely exceed—your target word count without relying on filler. This leaves your human editor with a rich, massive manuscript, giving them free rein to cut, polish, and get the book 100% ready for publication.

---

# Simplified Workflow

## Step 1: Getting Ready (The Prep Work)

- **Create a Rulebook**: Before you write anything, make a "Series Bible" that lists your characters' looks, backstories, and the specific settings of your world.
- **Set the Mood**: Make sure to tell the AI exactly what kind of historical or Western tone you want from the very beginning.

## Step 2: Planning the Chapter (The Blueprint)

- **Start with an Outline**: Take your general chapter idea and use an AI (like Gemini) to break it down into smaller, step-by-step "beats".
- **Add Emotion**: Tell the AI to include emotional moments, not just plot actions. You can give the AI a general target word count at this stage.
- **Check the Work**: Read through these beats yourself and fix any mistakes so the story stays on track.

## Step 3: Writing and Fixing (The Assembly Line)

- **Drop the Word Counts**: Switch to your writing AI (like Claude) to start drafting. Stop telling the AI how many words to write for each scene so it doesn't add useless filler.
- **Write Scene by Scene**: Have the AI write one scene at a time, making sure you tell it exactly which character's perspective to use.
- **Check for Errors and Voices**: Use Gemini to hunt for continuity mistakes and make sure every character's dialogue sounds distinct and authentic.
- **Stitch It Together**: Use Claude to combine all the fixed scenes into one complete, seamless chapter without leaving anything out.

## Step 4: The Final Polish (The Human Touch)

- **Read It Yourself**: Sit down and read the whole chapter with your own eyes. The AI won't get the pacing or emotions perfectly right every time.
- **Fix It By Hand**: If you see a mistake, type in the fix yourself. Do not put the text back into the AI to fix it, or you risk ruining the unique style and tone you've worked hard to build.

---

# The Master Series Bible Template

## 1. Series Overview

- **Series Title**: [Your Title]
- **Working Titles** (Books 1-X): [List]
- **Logline**: [One to two sentences summarizing the overarching plot of the entire series]
- **Core Themes**: e.g., Revenge, redemption, frontier justice, survival
- **Tone & Atmosphere**: Specific keywords to feed the AI for the overall vibe—e.g., gritty, atmospheric, historically grounded, slow-burn tension
- **Historical/Time Period Anchor**: Exact year or era to ensure the AI uses era-appropriate technology and references

## 2. Character Profiles

*(Duplicate for each character)*

- **Name & Aliases**: [Character Name]
- **Role in Story**: e.g., Protagonist, Antagonist, Primary Love Interest, Lawman
- **Physical Appearance**: Age, build, eye/hair color, distinct scars, typical clothing style. Be as specific as possible to prevent AI hallucinations.
- **Personality & Demeanor**: e.g., Highly introverted, observant, blunt, quick-tempered
- **Distinctive Voice & Dialect**: How do they speak? Do they use specific regional slang, formal speech, short clipped sentences, or a specific accent? Crucial for the Phase 3 Dialogue Pass.
- **Signature Gear & Mount**:
  - **Weapons**: Specific makes and models, e.g., Winchester Model 1873, .45 Colt
  - **Horse**: Breed, color, temperament, e.g., large black gelding, steady Texas bay
  - **Other**: Signature knives, specific hats, pocket watches
- **Backstory/Lore**: Where did they come from? What formed them?
- **Internal Conflict/Secret**: What is driving them emotionally, or what are they hiding?
- **POV Rules**: Are we allowed in their head? What are the strict limitations of their perspective?

## 3. World-Building & Settings

- **Primary Locations**: Names of towns, saloons, specific ranches, or hideouts
- **Geography & Terrain**: e.g., Alkali flats, dense pine forests, dusty border towns. Describe the weather and environmental hazards.
- **Law & Order**: How does justice work in this setting? Describe the local syndicates, marshals, bounty hunters, or governing forces.
- **Societal Norms & Tensions**: Ongoing feuds, economic struggles, railroad expansions

## 4. Undercurrents & Special Mechanics

- **Hidden Elements**: Are there subtle supernatural undertones, binding contracts, or hidden identities the reader knows but the characters don't?
- **Key Items/MacGuffins**: Specific objects that drive the plot forward

## 5. Overarching Series Arc

- **Book 1 Core Plot**: [Summary]
- **Book 2 Core Plot**: [Summary]
- **Book 3 Core Plot**: [Summary]
- **The Final Destination**: Where does the main character end up by the final book?

---

# The Master Beat Generation Prompt Template

**COPY AND PASTE THIS PROMPT TO GENERATE CHAPTER [X], BEAT [Y]:**

Write Beat [Beat Number] for Chapter [Chapter Number] of the western series following the exact outline below. You must generate the prose for this single beat, and it MUST have a strict word count of [Min Words]–[Max Words] words.

## Narrative Context

[Insert Act/Arc Title here, e.g., ACT II: THE RANGER]. [Insert a 2-3 sentence summary of the current story situation, character roles, and immediate goals for this section of the book.]

## Project Lock – Strict Stylistic Constraints (DO NOT VIOLATE)

- **The Absolute Literalism Ban**: Prose must be 100% literal. Zero metaphors, similes, or personification. The environment does not have feelings or intentions (e.g., the wind does not "scream").
- **Purge AI Echo Words**: You are STRICTLY FORBIDDEN from using these words: absolutely, completely, relentless, massive, sharp, heavy, pure, extremely, perfectly.
- **Lexicon of Antiquity**: Use blue-collar, 1800s vocabulary (iron, leather, dirt, lead, bone, granite). Zero modern/clinical words (e.g., velocity, fraction, trajectory, impact, visible, resolving). Zero Texas slang.
- **Em Dash Continuity & Natural Dialogue**: ZERO dialogue tags (no "said," "asked," "shouted"). Dialogue must be short, direct, and anchored directly to a physical action using an em dash with proper spacing. *(Example: "Get on the horse." — Harlan tightened the cinch.)*
- **The Cadence & Variance Protocol**: ZERO "-ing" sentence openers. Eliminate all Name/Pronoun loops (e.g., do not start consecutive sentences with He... He... He...). Mix sentence lengths to create an uneven rhythm.
- **State Truth—Don't Teach It**: Show the objective result. Do not over-explain obvious details or feed the reader the psychological reasoning behind an action.
- **Behavior Over Thought**: Zero internal monologue. Do not use "He felt," "He realized," or "He thought." Show his principles and tension entirely through physical actions.
- **Chapter Openers Protocol**: The FIRST sentence of this chapter beat must be a mechanical tool action, a sound, or physical strain. Zero weather or scenery in the first paragraph.
- **The Character Lock**: [Insert Primary Character 1] and [Insert Primary Character 2] are the ONLY named characters. Minor roles must ONLY be referred to by their functional titles (e.g., the outlaw, the scout, the gang leader).
- **Violence Rules**: Combat must be fast, brutal, and grounded. No micro-mechanics. No fleeing or begging survivors. No formulaic aftermaths.

## Beat [Beat Number]: [Beat Title]

*([Min Words]–[Max Words] words)*

- **Opener**: [Detail exactly how the beat must start. e.g., Start the chapter immediately on a mechanical action...]
- **Action**: [Describe the physical actions, setting details, and plot movements that must occur in this specific beat.]
- **Conflict**: [Describe the interpersonal tension, physical conflict, or obstacle to be resolved or escalated in this beat.]
- **Rule Check**: [Reiterate 1-2 critical rules the AI usually fails at for this specific beat type to ensure it pays attention. e.g., Ensure all dialogue strictly uses ONLY em dash action anchors. Absolutely zero "said" tags.]
