# Manuscript Agent Instructions

Use these rules when helping with manuscript planning, drafting, editing, validation, or workspace management in this project. These guidelines apply to all developers, AI assistants, and autonomous agents (e.g. Gemini, Claude, Cursor, OpenCode).

---

## 1. Architectural Foundations: The 5-Layer Model

To maintain narrative cohesion, consistency, and style quality, the BookForge system operates on a **5-layer architecture**:

```
┌────────────────────────────────────────────────────────┐
│  Layer 5: Series (Sequel continuity, name checking)     │
├────────────────────────────────────────────────────────┤
│  Layer 4: Book (Outline phase-0, rules, pacing plan)   │
├────────────────────────────────────────────────────────┤
│  Layer 3: Chapter (Staging changes/ priority workflow) │
├────────────────────────────────────────────────────────┤
│  Layer 2: Scene (Pacing constraints, beat structures)  │
├────────────────────────────────────────────────────────┤
│  Layer 1: Event/Canon (Replay ledger, status, locales) │
└────────────────────────────────────────────────────────┘
```

### Layer 5: Series
- Enforce name uniqueness across books in the series. Before approving any outline or character addition, ensure no new emotionally important character shares a first name with a prior major character unless explicitly documented.

### Layer 4: Book
- Grounded in the outline (`phase-0.md` or nested `phase-0/` outlines), the global `rulebook.md`, `mood-lock.md`, and the pacing/chapter list.
- Use `bf pacing` to generate or consult the `chapter-pacing-plan.md` to avoid artificial same-size chapters.

### Layer 3: Chapter (The Change Workspace Unit)
- Active authoring is performed in the staging workspace under `changes/chapter-NN/` using a **Proposal-Beat-Draft** lifecycle:
  - `proposal.md` (scene-breakdown outlining beats/scenes)
  - `beats.md` (active drafting plan)
  - `draft.md` (active draft prose)
  - `continuity-out.md` (unresolved stakes, character/location status updates)
- Prioritize reading and validating under `changes/chapter-NN/` first. Once complete, promote/apply it to the canonical `chapters/chapter-NN/` directory.

### Layer 2: Scene
- Scene beats contain plot movements and emotional/thematic anchors. Avoid head-hopping, enforce strict single-POV per scene, and vary beat counts based on chapter movement (e.g. 2-3 for transition/setup, 4-6 for action/climax).

### Layer 1: Event/Canon (State mutations)
- The state is event-sourced under `canon/events/*.event.yml`. `snapshot.yml` is the deterministic fold of all validated events.
- Never edit `snapshot.yml` manually. Rebuild it using `bf canon build` or compile events via `bf apply`.

---

## 2. Core Workflow Commands

Always use the unified `bf` CLI command set. The legacy orchestrator scripts under `.agents/skills/manuscript-workflow-orchestrator/scripts/` **have been removed** — `bf` is now the sole entry surface. Do not invent or call those script paths.

| Removed Legacy Script            | Use instead                   | Notes                                                  |
| :------------------------------- | :---------------------------- | :----------------------------------------------------- |
| `scan_source_format.py`          | `bf init`                     | Initializes or scans book folder config                |
| `validate_manuscript_context.py` | `bf validate`                 | Runs all deterministic, style, and canon validations   |
| `check_manuscript_length.py`     | `bf validate`                 | Length constraints are part of full validation         |
| `check_continuity_chain.py`      | `bf validate` / `bf status`   | Continuity check runs inline in both                   |
| `check_chapter_rhythm.py`        | `bf status`                   | Rhythm analysis runs inline in status                  |
| `check_chapter_gaps.py`          | `bf status`                   | Gap check runs inline in status                        |
| `check_narrative_quality.py`     | `bf validate` / `bf run-loop` | Narrative quality runs in validation and the loop      |
| `check_context_budget.py`        | `bf validate` / `bf run-loop` | Budget check folded into validation/loop               |
| `scan_banned_words.py`           | `bf validate`                 | Banned-word/style scan is part of validation           |
| `plan_chapter_pacing.py`         | `bf pacing`                   | Generates a source-locked pacing plan                  |
| `build_context_packet.py`        | `bf packet`                   | Renders a chapter context packet                       |
| `compile_manuscript.py`          | `bf compile`                  | Compiles drafts into a single manuscript               |
| `run_manuscript_loop.py`         | `bf run-loop`                 | Checks loop state and prints the next action           |
| `resolve_unknowns.py`            | `bf resolve-unknowns`         | Runs the unknowns resolution wizard                    |
| `apply_chapter_event` / scripts  | `bf apply change`             | Validates, appends event, re-folds, compiles, archives |

> **Note:** `analyze_reference_structure.py` under `western-story-pattern-analyzer/scripts/` is **not** a legacy shim — it is a standalone reference-analysis tool for that skill and remains in place.

### Core CLI Workflow Execution Order:
1. **Initialize**: Prepare the workspace:
   ```bash
   bf init --agents gemini,claude,cursor
   ```
2. **Draft / Edit**: Perform writing inside staging `changes/chapter-NN/` (working on `proposal.md`, `beats.md`, `draft.md`).
3. **Validate**: Run validation before committing:
   ```bash
   bf validate --chapter chapter-NN
   ```
4. **Apply Change**: Commit/apply staging changes once validation passes:
   ```bash
   bf apply change <book-folder> chapter-NN
   ```

---

## 3. Western Conflict & Narrative Variety

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

---

## 4. Western Prose Style Lock

- Use literal prose. Avoid metaphors, similes, and personification unless the user asks otherwise.
- Avoid these AI echo words: absolutely, completely, relentless, massive, sharp, heavy, pure, extremely, perfectly, voss (the name Voss is strictly banned for characters, families, or settings).
- Prefer blue-collar 1800s vocabulary: iron, leather, dirt, lead, bone, granite.
- Avoid modern or clinical words such as velocity, fraction, trajectory, impact, visible, resolving.
- Avoid Texas slang unless the user specifically requests it.
- Keep dialogue short and direct.
- Make travel and search sequences active and engaging: ensure characters interact with the environment, encounter hazards, make significant discoveries, or actively scout rather than describing passive movement.
- Avoid dialogue tags like "said," "asked," and "shouted" when the user requests em dash action anchors.
- Don't use em dash on-action anchors for spacing like: `"Get on the horse." — Harlan tightened the cinch.`
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
  - Avoid gun-catalog overload. Keep weapon details active and sensory (e.g., "the blue worn silver at the muzzle").
  - All historical details and weapon names must be sourced from the resolved `research-pack.md` in the book folder (or the global series research-pack) to maintain historical accuracy and prevent hallucination.
  - When referencing twin weapons in action, avoid confusion by specifying left/right identifiers rather than a generic "the Colt" (e.g., "his right-hand Peacemaker", "the left Colt", "the revolver").

---

## 5. Outline Quality Standards

Apply these rules whenever generating, reviewing, or approving any book outline (`phase-0.md` or equivalent).

### Required Outline Sections
Every approved outline must include all of the following. If any are missing, flag them before proceeding to rulebook generation:
- **Setting Function**: Explicitly states how the landscape acts as pressure, not decoration. Must name at least three specific terrain or resource elements that force decisions: crossings, weather, wheel damage, supply depletion, repair work, dead drops, night watches, choke points, or sign reading. Characters must engage with the environment through labor.
- **Story Pattern with Chapter Function Rule**: Names the structural pattern (road-pressure, manhunt, siege-and-break, etc.) and states a repeating chapter function rule. Every chapter must do one of a defined set of things. If the book has a split POV structure, the outline must name the convergence point and describe how both threads contribute to it.
- **Hard Story Guardrails block embedded in the outline**: The outline itself must contain a guardrails block listing every active constraint (no institutional villain, no resource-rights scheme, no trial scene, no em-dashes, no modern vocabulary, etc.).
- **New Character entries with physical marker, voice note, and private motive/secret**: Each new character must have all three.
- **Ending State for Book N+1**: A bullet list of where each major character stands at the close: who is dead/alive/escaped/compromised, what secrets are revealed or destroyed, what debts or obligations carry forward, and at least one unnamed hook for the next book.

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
