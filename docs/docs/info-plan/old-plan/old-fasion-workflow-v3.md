# The AI-Assisted Manuscript Workflow - v3

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
  - Plot and Emotion: In addition to plot beats, explicitly prompt the AI to include "emotional beats" or "thematic check-ins" to ensure narrative resonance isn't lost to pure mechanics.
  - Word Counts: Broad word count targets can be applied at this stage.
- **Operator Intervention**: Review and manually edit these beats as they are generated to ensure the narrative stays on track before moving to the drafting phase.

## Phase 2: Structural Review & Continuity

- **Shift to Claude**: Begin writing the manuscript using the constructed prompts.
- **The Golden Rule of Scene Generation**: Moving forward, do not apply word count instructions to individual scenes. This prevents the AI from inserting unnecessary fluff and filler words.
- **Continuity Pass** (Tool: Gemini): Feed the drafted material back into the AI to scan specifically for continuity errors.
- **Scene-by-Scene Structuring** (Tool: Gemini): Have the AI break the chapter down scene-by-scene, adding transitional bridges and applying fixes for any continuity errors detected in the previous step.

## Phase 3: Drafting & Micro-Editing

- **Scene Drafting** (Tool: Claude): Prompt the AI to write out the chapter one scene at a time based on the new, error-free breakdown.
  - Control the POV: Explicitly instruct the AI on the exact "Point of View" (POV) for that specific scene. This is crucial to avoid "head-hopping" (switching perspectives mid-scene), which is a common AI error.
- **Microscopic Error Detection** (Tool: Gemini): Once the chapter is drafted, run a highly detailed error-detection pass. The AI's only job here is to flag inconsistencies or grammatical issues and suggest solutions.
- **Dialogue & Voice Pass** (Tool: Gemini): Before compiling, run a pass specifically focused on dialogue. Ask the AI to ensure each character has a distinct "voice" or "dialect," which is vital for the authenticity of a Western manuscript.
- **Compilation & Integration** (Tool: Claude): Use those suggested solutions as your next prompt. Have the AI apply the fixes and compile the individual scenes into one seamless, cohesive chapter. Note: don't include word count instruction; let the scene write itself.
- **The Final AI Pass** (Tool: Gemini): Run one last automated read-through on the compiled chapter to catch any final glaring errors.

## Phase 4: The Human Polish

- **Manual Read-Through**: The author must do a final, comprehensive read-through. The AI will still make mistakes, and human intuition is required for pacing and emotional resonance.
- **Manual Edits Only**: When you spot an error at this stage, change it manually. Do not feed the text back through the AI, or you risk flattening the established tone and losing the specific results you've built.

## The End Result

By following this method, you will comfortably hit—and likely exceed—your target word count without relying on filler. This leaves your human editor with a rich, massive manuscript, giving them free rein to cut, polish, and get the book 100% ready for publication.

## The Master Series Bible Template (MODIFY IF NEEDED)

### 1. Series Overview

- **Series Title**: [Title]
- **Working Titles** (Books 1-X): [List]
- **Logline**: [One to two sentences summarizing the overarching plot of the entire series]
- **Core Themes**: [e.g., Revenge, redemption, frontier justice, survival]
- **Tone & Atmosphere**: [Specific keywords to feed the AI for the overall vibe—e.g., gritty, atmospheric, historically grounded, slow-burn tension]
- **Historical/Time Period Anchor**: [Exact year or era to ensure the AI uses era-appropriate technology and references]

### 2. Character Profiles (Duplicate for each character)

- **Name & Aliases**: [Name]
- **Role in Story**: [e.g., Protagonist, Antagonist, Primary Love Interest, Lawman]
- **Physical Appearance**: [Age, build, eye/hair color, distinct scars, typical clothing style. Be as specific as possible to prevent AI hallucinations]
- **Personality & Demeanor**: [e.g., Highly introverted, observant, blunt, quick-tempered]
- **Distinctive Voice & Dialect**: [How do they speak? Do they use specific regional slang, formal speech, short clipped sentences, or a specific accent? Crucial for the Phase 3 Dialogue Pass]
- **Signature Gear & Mount**:
  - Weapons: [Specific makes and models, e.g., Winchester Model 1873, .45 Colt]
  - Horse: [Breed, color, temperament, e.g., large black gelding, steady Texas bay]
  - Other: [Signature knives, specific hats, pocket watches]
- **Backstory/Lore**: [Where did they come from? What formed them?]
- **Internal Conflict/Secret**: [What is driving them emotionally, or what are they hiding?]
- **POV Rules**: [Are we allowed in their head? What are the strict limitations of their perspective?]

### 3. World-Building & Settings

- **Primary Locations**: [Names of towns, saloons, specific ranches, or hideouts]
- **Geography & Terrain**: [e.g., Alkali flats, dense pine forests, dusty border towns. Describe the weather and environmental hazards]
- **Law & Order**: [How does justice work in this setting? Describe the local syndicates, marshals, bounty hunters, or governing forces]
- **Societal Norms & Tensions**: [Ongoing feuds, economic struggles, railroad expansions]

### 4. Undercurrents & Special Mechanics

- **Hidden Elements**: [Are there subtle supernatural undertones, binding contracts, or hidden identities the reader knows but the characters don't?]
- **Key Items/MacGuffins**: [Specific objects that drive the plot forward]

### 5. Overarching Series Arc

- **Book 1 Core Plot**: [Summary]
- **Book 2 Core Plot**: [Summary]
- **Book 3 Core Plot**: [Summary]
- **The Final Destination**: [Where does the main character end up by the final book?]
