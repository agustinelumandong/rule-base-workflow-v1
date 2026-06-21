# Manuscript Agent Instructions

Use these rules when helping with manuscript planning, drafting, editing, or workflow files in this project.

## Core Workflow

- **No Outline Fallback Protocol (e.g. Book 3):** If a book has no outline source file (e.g. `phase-0.md`), do NOT automatically proceed with plot generation or loop execution. Instead, first ask the user in chat: **"Do you want me to create an outline for Book 3?"** (or whichever book number is next).
  - If approved, first perform web research via NotebookLM (`nlm research start` and `nlm research import`) to discover, retrieve, and ingest period-accurate historical events, outlaws, settings, or conflicts (e.g., stagecoach line robberies, harsh winter blizzards, frontier military outposts) to ground the story in authentic 1800s history.
  - Do not copy characters, names, scenes, dialogue, or recognizable story details from any copyrighted films.
  - The plot must be completely different from previous books and must **strictly exclude** the following elements:
    - A syndicate
    - Water rights
    - Mineral rights
    - A trial scene
  - Use new character names, original conflicts, and a differentiated setting to maintain a classic Western adventure feel without imitation.
  - Present the completed outline to the user for explicit approval before moving on to rulebook generation or the writing stage.
- Before drafting, use the available outline, series bible, character details, setting details, tone requirements, and chapter breakdown as source material.
- Before approving a sequel outline or rulebook, check prior books' major character names. Avoid giving a new emotionally important character the same first name as a prior major character unless the reuse is intentional and documented in the rulebook.
- Plan before drafting: break chapters into beats or scenes before writing full prose.
- Include both plot beats and emotional or thematic beats so the story does not become only mechanical action.
- For rescue, hostage, family-duty, or revenge plots, include at least one source-supported quiet humanizing beat before the rescue or climax when possible. This can be a short memory, campfire exchange, duty confession, or plain physical keepsake; do not turn it into a speech or invented backstory.
- For series-arc villains tied to the protagonist's old wound, place one source-supported legacy-pressure beat before the final confrontation. Use a named dead ally, remembered command, old sign, ledger mark, or concrete battlefield trace only if the source supports it.
- Beat count must vary by chapter purpose. Do not give every chapter the same number of beats just because a template is convenient. Use the source chapter's required movements:
  - quiet setup, aftermath, travel, or mystery pressure: usually 2-3 beats
  - standard investigation, alliance, rescue setup, or infiltration: usually 3-4 beats
  - action, chase, siege, crossing, climax, major reveal, or turning-point chapters: usually 4-6 beats, with 5-7 allowed only when the source contains enough distinct stages
  - never add beats just to hit a count; never compress distinct action stages into one beat just to keep a uniform pattern
- Review and refine beats before moving into full scene drafting.
- Draft scene by scene instead of generating an entire chapter at once.
- Do not use fixed numeric length targets for individual scenes during drafting; let the scene reach its natural length.
- Keep each scene locked to the requested POV. Avoid head-hopping or switching perspectives mid-scene.
- Before drafting and before finalizing each chapter, run these three mandatory workflow checks:
  1. **Hallucinations:** Verify that the prose contains no unauthorized facts, backstories, motives, or relationships not explicitly present in the outline/bible.
  2. **Plot Consistency:** Verify character names, roles, and locations remain consistent. Ensure all modern terms, concepts, and clinical language are strictly avoided.
  3. **Temporal Logic:** Verify travel times are realistic, time of day and sequence of events are tracked logically, and recovery timelines for injuries are believable.
- Run a dialogue and voice pass so each character keeps a distinct voice, dialect, and manner of speaking.
- When compiling scenes, preserve all intended story content and make transitions smooth.
- When revising, preserve the established tone and style. Do not flatten the prose with generic cleanup.
- For final polish, prefer targeted/manual edits over full regeneration unless the user explicitly asks for a rewrite.


## Western Conflict & Narrative Variety

- Do not use plots centered around land grabs, water rights fights, organized corruption, property disputes, business conspiracies, or shady business/corporate schemes.
- The banned villain type is any **institution or organization whose power comes from controlling property, money, business, or politics** — not individual danger or personal threat. Examples of banned villain setups:
  - A railroad or cattle company sending hired guns to seize land
  - A cartel or water-rights group controlling a region's resources
  - A crime hierarchy with a boss, lieutenants, and foot soldiers running a territory
  - A corrupt political machine using bribery and murder to hold power
- **The word "syndicate" itself is not banned.** It is banned only when it describes an institutional villain archetype as listed above. Use your judgment to apply the word correctly:
  - A group of outlaws riding together under one leader = **allowed** (a gang, not a syndicate)
  - A small criminal crew robbing stages or trains = **allowed**
  - A hero's allies, posse, partner, or deputized group = **always allowed**
  - An organized villain group whose power is personal threat and violence, not property or business control = **allowed**
- The quick test: **Is the villain's power coming from an institution or scheme? Banned. Is it coming from who they are as a person or outlaw? Allowed.**
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

## Western Prose Style Lock

- Use literal prose. Avoid metaphors, similes, and personification unless the user asks otherwise.
- Avoid these AI echo words: absolutely, completely, relentless, massive, sharp, heavy, pure, extremely, perfectly, voss (the name Voss is strictly banned for characters, families, or settings).
- Prefer blue-collar 1800s vocabulary: iron, leather, dirt, lead, bone, granite.
- Avoid modern or clinical words such as velocity, fraction, trajectory, impact, visible, resolving.
- Avoid Texas slang unless the user specifically requests it.
- Keep dialogue short and direct.
- Make travel and search sequences active and engaging: ensure characters interact with the environment, encounter hazards, make significant discoveries, or actively scout rather than describing passive movement.

- Avoid dialogue tags like "said," "asked," and "shouted" when the user requests em dash action anchors.
- Don't use em dash onaction anchors for spacing like: `"Get on the horse." — Harlan tightened the cinch.`
- For in-story notes, letters, telegrams, posted warnings, or written messages, do not use backticks or code blocks. Use prose such as `The note read:` or `The message read:` before the written text so it does not look like a prompt in Google Docs or compiled output.
- Avoid "-ing" sentence openers.
- Avoid repeated Name/Pronoun sentence loops, such as several consecutive sentences beginning with the same name or pronoun.
- Mix sentence lengths to create an uneven rhythm.
- Show objective action and result. Do not over-explain obvious details.
- Avoid internal monologue unless requested.
- Do not use "He felt," "He realized," or "He thought" when the user wants behavior-driven prose.
- Open chapter beats with mechanical action, sound, or physical strain instead of weather or scenery.
- Keep combat fast, grounded, and brutal. Avoid micro-mechanics, fleeing or begging survivors, and formulaic aftermaths.
- **Weapon & Material Detailing:**
  - Use general names in fast action (e.g., "Tex fired twice").
  - Use specific model names for mood and introduction (e.g., ".45 Peacemaker", "Winchester '73", "top-break Schofield").
  - Avoid gun-catalog overload (e.g., do not write "Colt Single Action Army .45 Long Colt 7½-inch cavalry model..."). Keep weapon details active and sensory (e.g., "the blue worn silver at the muzzle").
  - All historical details and weapon names must be sourced from the resolved `books/tex-cade/research-pack.md` (or the global series research-pack) to maintain historical accuracy and prevent hallucination.
  - When referencing twin weapons in action, avoid confusion by specifying left/right identifiers rather than a generic "the Colt" (e.g., "his right-hand Peacemaker", "the left Colt", "the revolver").



## Templates

- Keep long reusable templates, such as the Series Bible template or Master Beat Generation prompt, in separate Markdown files instead of embedding them here.
- Treat `docs/workflow-v5.md` as the current source for the manuscript workflow and prompt templates.
- Use the local `.agents/skills/manuscript-workflow-orchestrator/` skill for full book workflow tasks: scanning a book folder, reading `phase-0.md`, creating rulebooks, setting mood locks, breaking down chapters, making scenes, and preparing drafting plans.
- Use the local `.agents/skills/western-story-pattern-analyzer/` skill for reference Western analysis, chapter rhythm, scene density, opening/ending patterns, and reusable pacing calibration. Do not copy reference prose, plot, characters, voice, or exact structure.
- Use the local `.agents/skills/western-manuscript-style/` skill for reusable Western prose drafting, beat generation, dialogue cleanup, continuity review, and style-lock enforcement.
- Use the local `.agents/skills/humanizer/` skill after Western style and continuity passes when a draft sounds generic, padded, promotional, overstructured, or AI-written. Preserve plot facts, POV, paragraph coverage, and Western tone.
- Treat `books/<book-slug>/phase-0.md` as the default book source pattern.
- Treat root `references/` as optional local material that may be git-ignored. Missing reference books or generated reference analysis must not block normal manuscript workflow.
- Before creating or refreshing planning artifacts, run:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_source_format.py books/<book-slug>
  ```
- Use `source-format-scan.md` to identify bible/outline structure, missing fields, chapter-list detail, and length target source before generating `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, or scene breakdowns.
- If no user, source, or rulebook target exists, use `~30,000 words` as book-level planning guidance only. Do not turn that target into per-chapter quotas.

## Validation Commands

- After generating or changing `scene-breakdown.md`, chapter drafts, chapter expansions, or compiled chapters, run the context validator:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug>
  ```
- Use the context validator before the length checker. Fix `FAIL` results before continuing; treat `WARN` results as review or expansion targets.
- For deeper chapter review, generate an AI semantic review prompt:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/<book-slug> --chapter chapter-02 --ai-prompt
  ```
- After context validation passes or only warns, run the length checker:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/<book-slug>
  ```
- Use length results only as book-level planning guidance. Never pad scenes, force fixed beat/chapter word counts, or invent unsupported story to close the gap.

## Reference-Guided Pacing

- Analyze split reference chapters with:
  ```bash
  python .agents/skills/western-story-pattern-analyzer/scripts/analyze_reference_structure.py references/timber/timber-book-1-chapters
  ```
- Generate a source-locked pacing plan with:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/plan_chapter_pacing.py books/<book-slug>
  ```
- Use `chapter-pacing-plan.md` to avoid artificial same-size chapters. The current book source remains the authority.
- If `references/` or `references/timber/analysis/` is missing, generate pacing from the current book source only.
- Elastic ranges such as `~1000` mean natural supported ranges, not exact targets.
- Longer chapters or beats must be justified by approved source movement: major conflict, reveal, consequence, moral pressure, rescue, siege, or climax.
- Short chapters or beats are valid for setup, aftermath, transition, epilogue-style closure, or teaser pressure.
- Never force uniform chapter length.

## Token-Balanced Context

- Choose a prompt mode before chapter work: `planning`, `drafting`, `repair`, `style`, `validation`, `expansion`, or `final`.
- Before chapter-level drafting, repair, style cleanup, validation, or expansion, build or refresh:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py books/<book-slug> --chapter chapter-XX
  ```
- Use the context packet, chapter draft, and chapter `scene-breakdown.md` for normal chapter work. Do not load the full manuscript or full rulebook unless rebuilding planning artifacts, resolving a blocking source fact, or doing final review.
- Check context budget when unsure what to load:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/check_context_budget.py books/<book-slug> --chapter chapter-XX --mode drafting
  ```
- Use the compressed style lock in routine prompts: Literal Western prose; no AI echo words; no modern/clinical terms; no dialogue tags when action anchors are requested; behavior over thought; source-locked.
- After drafting or expanding a chapter, create or update `chapters/chapter-XX/continuity-out.md` so the next chapter can avoid loading the full prior draft.
- End every manuscript pass with: Source Used, Mode, Changes Made, Risks, Next Action, and Stop/Continue.

## Autonomous Manuscript Loop

- For requests like "run the book," "finish the manuscript," "autonomous loop," or "keep going until valid," use the local `.agents/skills/manuscript-workflow-orchestrator/` loop controller.
- Run:
  ```bash
  python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/<book-slug> --target-min 30000 --target-max 31000
  ```
- Treat `DONE` as the stop condition and `CONTINUE` as permission for the next prose action by the agent (any agent).
- Fix context problems before style problems, and fix style problems before length expansion.
- If the loop reports `NEEDS_EXPANSION`, expand only inside approved chapter `scene-breakdown.md` beats using source-supported action, consequence, conflict, dialogue pressure, setting texture, and transitions.
- If the loop reports `BLOCKED`, stop and ask for user direction.
- The loop must never pad prose, invent unsupported facts, or create fixed beat/scene word counts.

## Outline Quality Standards

Apply these rules whenever generating, reviewing, or approving any book outline (`phase-0.md` or equivalent).

### Required Outline Sections

Every approved outline must include all of the following. If any are missing, flag them before proceeding to rulebook generation:

- **Setting Function** — explicitly states how the landscape acts as pressure, not decoration. Must name at least three specific terrain or resource elements that force decisions: crossings, weather, wheel damage, supply depletion, repair work, dead drops, night watches, choke points, or sign reading. Characters must engage with the environment through labor, not just pass through it.
- **Story Pattern with Chapter Function Rule** — names the structural pattern (road-pressure, manhunt, siege-and-break, etc.) and states a repeating chapter function rule. Every chapter must do one of a defined set of things (e.g., move the party, expose a secret, worsen trust, tighten pursuit). If the book has a split POV structure, the outline must name the convergence point and describe how both threads contribute to it.
- **Hard Story Guardrails block embedded in the outline** — the outline itself must contain a guardrails block, not just reference the project rules. The block must list every active constraint: no institutional villain, no resource-rights scheme, no trial scene, no em-dashes, no modern vocabulary, and any book-specific restrictions.
- **New Character entries with physical marker, voice note, and private motive/secret** — each new character must have all three. A physical marker is a single quick visual identifier. A voice note is how they speak (short, formal, silent, bitter, etc.). A private motive is what they actually want or hide, distinct from their stated purpose.
- **Ending State for Book N+1** — a bullet list of where each major character stands at the close: who is dead/alive/escaped/compromised, what secrets are revealed or destroyed, what debts or obligations carry forward, any world-level change (a route destroyed, a cache burned, a network severed), and at least one unnamed hook for the next book.

### Outline Review Checklist

Before approving any outline:

- [ ] Setting Function names at least three specific terrain or resource pressures that will force decisions in this book.
- [ ] Story Pattern includes a named structural shape and a chapter function rule with specific labels.
- [ ] Hard Story Guardrails are present inside the outline document, not only in external project rules.
- [ ] Every new character entry includes a physical marker, a voice note, and a private motive or secret.
- [ ] No chapter summary uses vague language. Each chapter entry must name a specific action, revelation, or change.
- [ ] If the book uses a split POV structure, the outline names the convergence chapter and states what both threads contribute.
- [ ] Ending State for Book N+1 is present and covers all major characters.
- [ ] No new major character shares a first name with a prior major character unless explicitly documented.
- [ ] No banned plot elements appear in any chapter summary or premise section.
