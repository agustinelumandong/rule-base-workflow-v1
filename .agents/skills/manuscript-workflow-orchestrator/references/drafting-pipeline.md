# Drafting Pipeline

Use this to create chapter-folder drafting plans and guide Phase 1 through Phase 4 execution.

## Phase 1: Foundation And Beat-Mapping

- Start from the target folder source file.
- Build or refresh `rulebook.md` and `mood-lock.md`.
- Create `chapter-summaries.md`.
- Create or refresh `chapter-pacing-plan.md` when the user wants reference-guided rhythm or when chapters are becoming artificially similar in length.
- Create chapter beats with plot movement plus emotional/thematic pressure.
- Use any capable AI coding agent as primary (see `AGENTS.md`).
- Treat a secondary model as optional review only.

## Phase 2: Structural Review And Continuity

- Build `chapters/chapter-XX/scene-breakdown.md`.
- Verify the three mandatory workflow checks:
  1. **Hallucinations:** No unauthorized backstory, character lore, or motives not in the outline/bible.
  2. **Plot Consistency:** Names, roles, and locations are consistent. Avoid modern terminology.
  3. **Temporal Logic:** Travel duration is realistic, time of day is tracked logically, and injury recovery timeline is believable.
- Check names, locations, weapons, injuries, horses, timeline, and character knowledge.
- Check prior sibling books for major-character first-name collisions before approving sequel character names. If a new major character repeats a prior important first name, rename them or document why the reuse is intentional.
- Enforce current-book name locks inside the active target book's new outline, planning artifacts, and drafts by default. Rewrite prior books, compiled manuscripts, old context packets, or research packs only when the user explicitly asks for a series-wide or system-forward cleanup and accepts that old-book compatibility is not required.
- For frame-up, sabotage, counterfeit, altered-brand, planted-proof, or witness-confession plots, verify the practical logic before drafting: who knows the truth, why they know it, what physical proof exists, how the tactic gets discovered, and why the antagonist's action does not destroy the evidence they need.
- Add transition notes between scenes.
- Run a pre-draft beat verification pass before any scene prose is drafted.
- For each beat, confirm Source Anchor, Continuity In, Required Story Movement, Continuity Out, Do Not Invent, and Context Match Check.
- If a beat fails context match, revise the beat before drafting prose.
- Mark unresolved facts as `UNKNOWN`.
- Ask the user only when an unknown blocks drafting.
- Build or refresh `chapters/chapter-XX/context-packet.md` after the chapter scene breakdown is approved.

## Phase 3: Drafting And Micro-Editing

- Choose a prompt mode before loading files: `drafting`, `repair`, `style`, `validation`, or `expansion`.
- For chapter-level work, load `context-packet.md`, the chapter draft, and `scene-breakdown.md` instead of the full manuscript.
- Draft one scene at a time.
- Do not require fixed numeric lengths for scenes.
- Use pacing guidance only to decide whether approved beats deserve lean, standard, expanded, or major treatment. Never treat elastic ranges as hard targets.
- After drafting or expanding a chapter, run the context validator before treating the chapter as approved.
- After drafting or expanding a chapter, run the length checker to measure book-level progress without turning the result into a scene target.
- Lock each scene to the selected POV.
- Run a post-beat context check before drafting each scene. Confirm the scene follows the approved beat and does not add unsupported characters, locations, motives, or backstory. Verify:
  1. **Hallucinations:** The scene does not add unauthorized lore, backstory, or motives not in the outline/bible.
  2. **Plot Consistency:** Consistent character names, roles, and locations. No modern terminology.
  3. **Temporal Logic:** Travel duration, time of day, and chronological sequence of events (e.g. injury recovery) are realistic.
  4. **Conflict Variety:** No syndicates, land grabs, water rights fights, or shady business schemes. Focuses on classic Western adventures.
- Use `.agents/skills/western-manuscript-style/` for Western prose, dialogue, action, and revision rules.
- When drafting in-story notes, letters, telegrams, posted warnings, or written messages, do not use backticks or code blocks. Introduce the text with `The note read:` or `The message read:` so it cannot look like a prompt in compiled manuscript output.
- After each scene, run targeted checks for continuity, dialogue voice, POV drift, and style drift.
- Use `.agents/skills/humanizer/` only after the Western style pass if the scene still sounds generic, padded, promotional, overstructured, or AI-written.
- Humanizer cleanup must keep the same scene events, facts, POV, paragraph coverage, and Western tone.
- End each pass with the Agent Checkpoint fields: Source Used, Mode, Changes Made, Risks, Next Action, Stop/Continue.

## Phase 4: Compilation And Human Polish

- Compile scenes into a chapter only after scene-level checks pass.
- Preserve all intended plot content.
- Smooth transitions without flattening voice.
- Run the context validator before final acceptance of any compiled or revised chapter.
- Run the length checker after compilation or revision to identify underdrafted chapters and total gap to the book-level target.
- Before final compile, run chapter rhythm and narrative-quality checks and correct any `NEEDS_PACING_REBALANCE` issues.
- Run a final AI pass for continuity and obvious errors.
- Run a final humanizer pass only for AI slop patterns, filler, repetitive structure, promotional language, or unnatural rhythm.
- Create or update `chapters/chapter-XX/continuity-out.md` after chapter drafting or expansion.
- Leave final taste, pacing, and emotional polish to the human author.

## Phase 5: Autonomous Loop

Use `scripts/run_manuscript_loop.py` after every draft, expansion, repair, or final validation pass when the user wants an autonomous workflow.

- Run the loop controller after context validation and length checks are available.
- Continue only when the loop report says `CONTINUE`.
- If the loop reports `NEEDS_CONTEXT_REPAIR`, repair the named chapter before style work or expansion.
- If the loop reports `NEEDS_STYLE_REPAIR`, rewrite only the flagged lines or passages.
- If the loop reports `NEEDS_EXPANSION`, expand the recommended chapter from approved scene breakdowns and source files only.
- Run narrative-quality and rhythm rebalance only after the manuscript is within the book-level target range.
- If the loop reports `NEEDS_PACING_REBALANCE`, run one targeted rebalance cycle on the recommended chapter before further expansion.
- If the loop reports `NEEDS_PACING_REBALANCE`, run:
  - `scripts/check_narrative_quality.py books/<book-slug>`
  - `scripts/check_chapter_rhythm.py books/<book-slug>`
- If the loop recommends chapter work, refresh that chapter's context packet before editing prose.
- If the loop reports `DONE`, stop and report the final state.
- If the loop reports `BLOCKED`, stop and ask for user direction.

## Reviewer Rubric (Two-Pass)

Use this before final handoff:

- **Pass 1 (Structure):** No unresolved continuity chain gaps (`check_continuity_chain`) and no mandatory marker-policy warnings from context validation.
- **Pass 2 (Narrative):**
  - each chapter has at least one non-procedural human-stakes carryover in `continuity-out.md`,
  - each chapter has at least one antagonistic pressure scene with distinct intent/tactic impact.

If either pass fails, run one targeted correction cycle before compile.

## Western Series Strength Rubric

Use this after deterministic checks pass and before final handoff. This rubric is advisory review guidance only; it must not create new loop states, hard validation failures, or padding pressure.

- **Pacing Breath:** After long action chains, confirm the manuscript includes source-supported quiet, recovery, grief, planning, or lower-pressure chapters where consequences settle.
- **Hero Cost:** Confirm the protagonist pays for at least one mistake, hard choice, misjudgment, or failure through guilt, changed behavior, damaged trust, lost time, or moral pressure, not only wounds.
- **Villain Presence:** Confirm the villain is shown directly through personal threat, outlaw leverage, coercion, intimidation, pursuit, hostage pressure, or tactical command. Do not convert this into land, property, business, or political-machine control.
- **Supporting Agency:** Confirm supporting characters make active choices, take risks, study problems, resist pressure, rescue others, withhold or reveal information, or change tactics without simply waiting for the protagonist.
- **Quiet Humanizing Beat:** For rescue, hostage, family-duty, or revenge stakes, confirm the manuscript includes at least one brief source-supported quiet beat that makes the person at risk concrete before the action resolves.
- **Legacy Pressure Payoff:** For series-arc villains tied to the protagonist's old wound, confirm at least one source-supported memory, name, command, mark, ledger, or physical sign appears before the final confrontation.
- **Proof/Consequence Payoff:** Confirm the ending or major turn pays off through proof, public courage, exposed truth, rescue consequence, reputation cost, moral result, or town/family resolve, not only gunfire.
- **Frame-Up Mechanics:** If the book uses planted evidence, altered brands, counterfeit items, a confession, a stampede, or sabotage, confirm the mechanism is practical and source-supported. The evidence must survive discovery, the person revealing facts must have a reason to know them, and the villain's tactic must remain outlaw/personal pressure rather than land, property, business, or political-machine control.

## Style And Pacing Feedback Rubric

Use this as human-facing review guidance, not a hard validator or loop blocker:

- **Rugged Dialogue:** Cowboys, lawmen, outlaws, and frontier families speak in short, direct, plain sentences unless the source gives a reason otherwise.
- **Show Conversations:** Do not summarize planning, friction, bonding, or moral-decision conversations when the reader needs to experience the exchange.
- **No Behavioral Over-Analysis:** Avoid explaining character psychology, motives, symbolism, or subtext in the narrative voice. Show choices through action, silence, work, and direct speech.
- **Continuous Transitions:** Bridge major travel or time jumps with source-supported labor, scouting, weather, fatigue, repairs, camp movement, sign reading, or hazard.

These items may guide manual revision or an AI semantic review prompt. They must not become hard automated failures until a focused test suite proves the checks are reliable and low-noise.

If the source does not support one of these strengths, mark it `UNKNOWN` in planning or review notes rather than inventing story to satisfy the rubric.

The agent performs prose edits. The loop controller only scans, prioritizes, reports state, and recommends the next action.

## No Word Count Padding

Use broad book or chapter targets only as planning context. Never add filler to satisfy a scene or beat length. If a beat is short because the source is short, keep it short and source-grounded.

## Reference-Guided Pacing

Use `scripts/plan_chapter_pacing.py` to create `chapter-pacing-plan.md` when chapter lengths need natural variation. The plan may use optional reference analysis from `.agents/skills/western-story-pattern-analyzer/`, but current book source remains authoritative. Longer treatment must be justified by approved source movement such as confrontation, rescue, siege, reveal, reversal, consequence, or moral pressure.

## Length Progress Check

Use `scripts/check_manuscript_length.py` from the orchestrator skill to report current words, remaining words, per-chapter counts, and pacing warnings. Treat warnings as planning signals. Expand from approved beats and continuity facts only.

## Context Validation Check

Use `scripts/validate_manuscript_context.py` from the orchestrator skill to verify required files, chapter draft presence, scene-breakdown beat structure, automated `phase-0.md` source overlap, beat-to-draft coverage, forbidden fixed-count language, unresolved markers, and style-risk warnings. Use `--ai-prompt --chapter chapter-XX` to generate a semantic review prompt (for any capable AI agent) when a chapter needs deeper source-match review.

## Token-Balanced Context

Use `scripts/build_context_packet.py` before chapter-level work and `scripts/check_context_budget.py` when unsure what to load. Full manuscripts and full rulebooks are for planning rebuilds, final review, or source-blocking repairs; normal chapter work should use the compact packet.
