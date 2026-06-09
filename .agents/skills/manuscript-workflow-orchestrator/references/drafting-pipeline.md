# Drafting Pipeline

Use this to create chapter-folder drafting plans and guide Phase 1 through Phase 4 execution.

## Phase 1: Foundation And Beat-Mapping

- Start from the target folder source file.
- Build or refresh `rulebook.md` and `mood-lock.md`.
- Create `chapter-summaries.md`.
- Create or refresh `chapter-pacing-plan.md` when the user wants reference-guided rhythm or when chapters are becoming artificially similar in length.
- Create chapter beats with plot movement plus emotional/thematic pressure.
- Use Codex / ChatGPT 5.5 as primary.
- Use Gemini only as optional secondary review.

## Phase 2: Structural Review And Continuity

- Build `chapters/chapter-XX/scene-breakdown.md`.
- Check names, locations, weapons, injuries, horses, timeline, and character knowledge.
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
- Run a post-beat context check before drafting each scene. Confirm the scene follows the approved beat and does not add unsupported characters, locations, motives, or backstory.
- Use `.agents/skills/western-manuscript-style/` for Western prose, dialogue, action, and revision rules.
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
- If the loop recommends chapter work, refresh that chapter's context packet before editing prose.
- If the loop reports `DONE`, stop and report the final state.
- If the loop reports `BLOCKED`, stop and ask for user direction.

Codex performs prose edits. The loop controller only scans, prioritizes, reports state, and recommends the next action.

## No Word Count Padding

Use broad book or chapter targets only as planning context. Never add filler to satisfy a scene or beat length. If a beat is short because the source is short, keep it short and source-grounded.

## Reference-Guided Pacing

Use `scripts/plan_chapter_pacing.py` to create `chapter-pacing-plan.md` when chapter lengths need natural variation. The plan may use optional reference analysis from `.agents/skills/western-story-pattern-analyzer/`, but current book source remains authoritative. Longer treatment must be justified by approved source movement such as confrontation, rescue, siege, reveal, reversal, consequence, or moral pressure.

## Length Progress Check

Use `scripts/check_manuscript_length.py` from the orchestrator skill to report current words, remaining words, per-chapter counts, and pacing warnings. Treat warnings as planning signals. Expand from approved beats and continuity facts only.

## Context Validation Check

Use `scripts/validate_manuscript_context.py` from the orchestrator skill to verify required files, chapter draft presence, scene-breakdown beat structure, automated `phase-0.md` source overlap, beat-to-draft coverage, forbidden fixed-count language, unresolved markers, and style-risk warnings. Use `--ai-prompt --chapter chapter-XX` to generate a Codex / ChatGPT 5.5 semantic review prompt when a chapter needs deeper source-match review.

## Token-Balanced Context

Use `scripts/build_context_packet.py` before chapter-level work and `scripts/check_context_budget.py` when unsure what to load. Full manuscripts and full rulebooks are for planning rebuilds, final review, or source-blocking repairs; normal chapter work should use the compact packet.
