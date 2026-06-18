---
name: manuscript-workflow-orchestrator
description: Run a manuscript project workflow from a book folder source file into rulebook, mood lock, chapter summaries, scene breakdowns, drafting plan, and review passes. Use when the user asks to do this book, scan a book folder, create a rulebook, set the mood, break down chapters, make scenes, create beats, run the manuscript workflow, draft from phase-0/phase-00/outline files, or add humanized cleanup after AI drafting.
---

# Manuscript Workflow Orchestrator

Use this skill to run the project workflow from book-folder source material into planning artifacts and drafting instructions.

## Source Priority

1. User request and named target folder.
2. `books/<book-slug>/phase-0.md`.
3. Fallback files in the target folder: `phase-00.md`, `outline.md`, `chapter-outline.md`.
4. Project workflow source: `docs/workflow-v5.md`.
5. Optional reference pattern skill: `.agents/skills/western-story-pattern-analyzer/`.
6. Local style skill: `.agents/skills/western-manuscript-style/`.
7. Local cleanup skill: `.agents/skills/humanizer/`.

If no phase or outline source exists, stop and report the missing source. Do not invent book facts.

## Default Outputs

For a target folder such as `books/tex-cade/`, create or update:

- `source-format-scan.md`
- `rulebook.md`
- `mood-lock.md`
- `chapter-summaries.md`
- `chapters/chapter-XX/scene-breakdown.md`
- `chapters/chapter-XX/drafting-plan.md`
- `chapters/chapter-XX/chapter-XX.md`

## References

- Load [references/folder-scan.md](references/folder-scan.md) before choosing source and output paths.
- Load [references/outline-generation.md](references/outline-generation.md) when generating a new outline, reviewing an existing outline before rulebook creation, or checking whether a source outline meets the required quality standard.
- Load [references/rulebook-generation.md](references/rulebook-generation.md) for `rulebook.md` and `mood-lock.md`.
- Load [references/chapter-breakdown.md](references/chapter-breakdown.md) for chapter summaries, beats, emotional beats, and scene breakdowns.
- Load [references/drafting-pipeline.md](references/drafting-pipeline.md) for Phase 1 through Phase 4 drafting, review, and polish.
- Load [references/context-validator.md](references/context-validator.md) after chapter drafting, expansion, compilation, or revision to validate source match structure and generate AI semantic review prompts.
- Load [references/length-checker.md](references/length-checker.md) after drafting, expansion, compilation, or revision passes to measure progress toward the book-level target.
- Load [references/autonomous-loop.md](references/autonomous-loop.md) when the user asks to run the book, finish the manuscript, keep going until valid, or use an autonomous manuscript loop.
- Load [references/context-packets.md](references/context-packets.md) before chapter-level drafting, repair, validation, style cleanup, or expansion.
- Load [references/prompt-modes.md](references/prompt-modes.md) when choosing between planning, drafting, repair, style, validation, expansion, or final review work.
- Load [references/token-budget.md](references/token-budget.md) when the task risks loading the full manuscript, full rulebook, or unrelated chapter files.
- Load [references/pacing-ranges.md](references/pacing-ranges.md) when the user asks for uneven chapter rhythm, reference-guided pacing, elastic beat ranges, or help deciding which chapters deserve longer treatment.
- Load [references/continuity-out-template.md](references/continuity-out-template.md) when writing or reviewing `continuity-out.md` files after chapter drafting.

## Operating Rules

- **No Outline Protocol (e.g., Book 3):** If a target book lacks an outline source file (e.g. `phase-0.md`), do NOT automatically proceed with plot generation or loop execution. Instead, first ask the user in chat: **"Do you want me to create an outline for Book 3?"** (or whichever book number is next).
  - If approved, read the prior book's final `continuity-out.md` and `rulebook.md` to establish end state, character names, wounds, and unresolved pressure before writing anything.
  - Generate a fresh, fully original outline. Fill all 17 required sections from [references/outline-generation.md](references/outline-generation.md): Title, Continuity Source, Classic Western Inspiration, Time Period, Primary Setting, Setting Function, Tone and Style Direction, Story Pattern (with chapter function rule), Hard Story Guardrails (embedded in the outline), Premise, Book Target, Returning Characters, New Characters, Core Conflicts, Act Structure, Chapter Outline, and Ending State for Book N+1.
  - Choose a story pattern not used in the prior book. Vary the structural shape book-to-book.
  - Exclude copyright details, recognizable story elements from films, and strictly ban these elements: **syndicates as institutional villains, water rights, mineral rights, trial scenes**.
  - Use original character names, conflicts, and setting. Check new major character first names against prior book major characters. Rename if there is a collision.
  - Run the outline quality checks from [references/outline-generation.md](references/outline-generation.md) before presenting.
  - Present the full completed outline to the user for explicit approval. Do not begin rulebook generation, mood lock, or scene breakdowns until the user approves.
- Use Codex / ChatGPT 5.5 as the primary tool.
- Treat Gemini as optional secondary review only.
- Before rulebook or chapter planning, run the source format scan:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_source_format.py books/<book-slug>`
- Use `source-format-scan.md` to identify present/missing bible sections, chapter-list detail, and target source before normalizing artifacts.
- Before approving sequel planning artifacts, compare major character names against prior sibling book folders. Avoid reusing the same first name for a new major emotional-stakes character unless it is intentional and documented.
- If no user, source, or rulebook word target exists, default to `~30,000 words` as book-level planning guidance only.
- Use broad book or chapter targets only for planning.
- Do not require fixed numeric lengths for beats or scenes.
- For rescue, hostage, family-duty, or revenge arcs, require one source-supported quiet humanizing beat where possible before the rescue or climax. Keep it brief and physical; do not invent biography.
- For series-arc villains tied to the protagonist's prior wound, require one source-supported legacy-pressure beat before the final confrontation. Ground it in a concrete name, sign, command, wound, ledger, or memory already present in source.
- Use optional reference analysis only for high-level pacing and rhythm guidance; never copy reference prose, plot, characters, voice, or exact structure.
- Use `chapter-pacing-plan.md` to avoid artificial same-size chapters, while keeping the current book source as the authority.

- Run context validation before using length results to guide expansion.
- Use the length checker as an advisory progress report only; never pad or invent story to satisfy a target.
- Use the autonomous loop controller to decide stop/continue state after draft, repair, expansion, and validation passes. Codex performs prose edits; the script controls state and next action.
- For chapter-level work, build or refresh `chapters/chapter-XX/context-packet.md` and use prompt modes to keep context compact.
- For a full book check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>`
- For a narrative quality pass, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_narrative_quality.py books/<book-slug>`
- For a length check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>`
- For an autonomous loop check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/<book-slug> --target-min 30000 --target-max 31000`
- For a context packet, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py books/<book-slug> --chapter chapter-XX`
- For a context budget check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_context_budget.py books/<book-slug> --chapter chapter-XX --mode drafting`
- For a chapter pacing plan, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/plan_chapter_pacing.py books/<book-slug>`
- Mark missing facts as `UNKNOWN` unless the missing detail blocks drafting, then ask the user.
- Use `.agents/skills/western-manuscript-style/` whenever drafting or revising Western prose.
- Use `.agents/skills/humanizer/` after style/continuity passes when the draft sounds generic, padded, promotional, overexplained, or AI-written.
- Humanizer cleanup must preserve plot, continuity, POV, Western tone, and source facts; it is a polish pass, not a rewrite license.
- After drafting or expanding a chapter, write `continuity-out.md` using the required template in [references/continuity-out-template.md](references/continuity-out-template.md).
- For a fast style scan (with line numbers), run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_banned_words.py books/<book-slug>`
- For a continuity chain check, run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_continuity_chain.py books/<book-slug>`
- For a chapter gap check (source vs folders), run:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_gaps.py books/<book-slug>`
- For a resolve-unknowns check (run first, before any drafting or loop work), run:
  `bf resolve-unknowns books/<book-slug>` — but if there are unresolved items, resolve them in chat using the format below, not with the CLI wizard.

## Unknowns Resolution (Chat Q&A Protocol)

When the validator or loop reports unresolved `## Unknowns` items in `rulebook.md`, resolve them in **chat** using this exact format. Do NOT use the CLI wizard's hardcoded suggestions.

### Batch Presentation Rule

- Present unknowns in **batches of up to 4** per response.
- Show all questions in the batch together in a single response.
- Wait for the user to answer all questions in the batch before writing to the rulebook and presenting the next batch.
- For 7 unknowns: show [1–4] first, then [5–7] after.
- The user answers a batch by replying with one choice per line or as a comma-separated list (e.g., `1, 2, 1, 3`).
- After receiving all answers for a batch, write them all to the rulebook, then present the next batch.

### Required Q&A Format

For each unknown in the batch, present:

1. A heading: `**[N/total] <unknown item text>**`
2. One line of context grounded in the actual outline and rulebook (what clues exist, what the setting implies).
3. A numbered list of exactly 3 suggestions — each with a **bolded short answer** followed by an em-dash and a **one-sentence reason** pulled from the source material. Mark the strongest choice with `*(Recommendation)*` at the end.
4. Option 4: `Something else — what's on your mind?`

Close the batch with a single line: `Reply with your choices for [1–4] (e.g., 1, 2, 1, 3):`

**Example — Batch 1 of 2 (questions 1–4):**

---

**[1/7] Exact year.**

Based on the outline (rail spur stronghold, Wyoming Territory, federal marshals active, freight roads):

1. **1878** — early enough that Wyoming Territory law is thin and the rail network is still expanding into Powder River country
2. **1881** — the year the Northern Pacific was pushing into Wyoming, making Harlan's rail-spur stronghold and prisoner transport realistic *(Recommendation)*
3. **1883** — post-railhead boom when freight roads were being consolidated and local law had already been broken or bought off
4. Something else — what's on your mind?

---

**[2/7] Main antagonist's appearance.**

Based on the outline (Harlan boards a prisoner train, confronts Pilar personally, holds a public execution):

1. **Tall, lean, mid-50s, pale gray eyes, iron-gray hair, black coat** — fits Harlan's calculated, public-performance style of violence *(Recommendation)*
2. **Broad, early 40s, ex-Confederate, dark beard, scar on chin** — grounds Harlan as a war-era man who never stopped fighting
3. **Stocky, late 40s, ruddy face, thick mustache** — ties him geographically to Tex's Texas background
4. Something else — what's on your mind?

---

*(continue remaining questions in batch...)*

Reply with your choices for [1–2] (e.g., 2, 1):

---

### Rules for Generating Suggestions

- Read `phase-0.md` (or its equivalent outline file) and `rulebook.md` before generating suggestions.
- Each suggestion must be grounded in actual facts from those files: events, locations, character roles, timeline clues, or setting details.
- Do not invent facts that are not implied by the source material.
- Keep each reason to one sentence.
- Mark the single strongest suggestion with `*(Recommendation)*` — the one best supported by the outline's timeline, setting, and story logic.
- After receiving all answers for a batch, write them all to the rulebook at once: remove each item from `## Unknowns` and append to `## Resolved Unknowns` as Q/A pairs.
- Then present the next batch immediately without waiting for a separate prompt.
- After all unknowns are resolved, confirm: "All Unknowns resolved. The pipeline is now clear."
