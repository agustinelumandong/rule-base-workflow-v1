# BookForge Master Plan

**Status:** Frozen authoritative full-product capability blueprint
**Version:** v2026-06-13
**Updated:** 2026-06-13
**Sources:** Current BookForge notes, legacy CanonForge plans, workflow studies, reference packs, and Superpowers implementation plans under `docs/info-plan/`
**Purpose:** Define the complete BookForge product, what it must eventually support, what belongs in each delivery phase, and what must not be built prematurely.

## 1. Product Vision

This plan is the BookForge north-star architecture. It is not permission to implement every capability at once. Implementation must follow the assigned phase and the focused briefs:

- `docs/info-plan/phases/phase-0-contracts.md`
- `docs/info-plan/phases/phase-1-local-proof-engine.md`
- `docs/info-plan/phase-roadmap-index.md`
- `docs/info-plan/containerization-strategy.md`
- `docs/info-plan/western-profile-v1.md`
- `docs/info-plan/implementation-rules-for-ai-agent.md`

For Phase 0 and Phase 1, advanced capabilities are contracts or fixtures only unless explicitly assigned.

Containerization is also phased. Phase 0/1 may define a single deterministic local test container, but API, UI, database, worker, queue, object storage, telemetry, and Kubernetes-style production infrastructure remain later-phase work.

BookForge is a human-supervised fiction production platform for planning, generating, transforming, validating, revising, reviewing, and publishing books without losing control of canon, prose quality, or editorial intent.

It supports two major outcomes:

1. Create a new book or connected series from an approved concept, research set, story bible, outline, and editorial direction.
2. Transform an existing manuscript through canon extraction, humanization, line or developmental editing, continuity review, targeted revision, and publishing export.

BookForge is not a chatbot and not a single large prompt. It is a stateful production system where:

```text
approved sources and decisions
-> structured plans and scoped context
-> model-assisted creative work
-> deterministic and model-assisted checks
-> targeted revision
-> human judgment
-> approved, traceable publication artifacts
```

The system should increase author and editorial throughput while preserving the decisions that make each book coherent and distinct. Automation serves creative control; it does not replace it.

## 2. Product Identity And Boundaries

**BookForge** is the complete product. **CanonForge** becomes the historical prototype and conceptual origin of **CanonCore**, BookForge's canon and continuity subsystem.

BookForge is one modular product with clear internal capability boundaries:

| Capability | Responsibility |
| --- | --- |
| **ProjectHub** | Projects, series, users, roles, settings, lifecycle, and status |
| **PolicyCenter** | Typed project, book, style, memory, retrieval, provider, validation, review, security, budget, and export policies |
| **CanonCore** | Approved facts, characters, locations, objects, timeline, rules, relationships, and canon change control |
| **ResearchCore** | Source ingestion, evidence, historical research, citations, freshness, and research approval |
| **StoryEngine** | Premise, arcs, outlines, chapter plans, scene cards, beats, setup/payoff, and unresolved threads |
| **ProseForge** | Drafting, expansion, humanization, developmental editing, line editing, voice, and targeted revision |
| **JudgePanel** | Deterministic validation, model-assisted evaluation, quality gates, and risk classification |
| **MemoryVault** | Trace, summaries, story state, retrieval, embeddings, relationships, and series memory |
| **Intelligence Layer** | Bounded ingestion, retrieval, research, notebook, visualization, sandboxed analysis, and assistant capabilities |
| **ReviewDesk** | Diffs, comments, approvals, rejections, revision requests, and editorial checkpoints |
| **Publisher** | Manuscript assembly, metadata, formatting, and export |
| **Operations** | Jobs, queues, provider routing, budgets, telemetry, recovery, and administration |

These are logical modules. They remain in a modular monolith until measured scale, ownership, or reliability needs justify another deployment boundary.

The Intelligence Layer is cross-cutting infrastructure, not a new authority. It may assemble context, search approved knowledge, execute permitted analysis, explain findings, and expose assistant commands. CanonCore owns truth, application services own workflow state, ReviewDesk owns human decisions, and Publisher enforces publication gates.

PolicyCenter is also cross-cutting. ProjectHub owns policy identity and scope; Operations resolves and enforces runtime configuration. CLI, API, UI, workers, prompts, providers, and adapters consume the same validated policy services rather than interpreting settings independently.

## 3. Actors And Product Surfaces

### Actors

- **Author:** Defines creative intent, reviews plans and prose, approves canon and final content.
- **Editor:** Reviews structure, continuity, voice, diffs, and publication readiness.
- **Researcher:** Collects evidence, resolves historical questions, and approves research facts.
- **Project owner:** Controls project policy, budgets, model access, roles, and release gates.
- **Operator:** Monitors jobs, failures, costs, storage, queues, and provider health.
- **Automation worker:** Executes only authorized stages with explicitly scoped inputs and tools.

One person may hold all human roles in local single-user mode.

### Surfaces

- Importable Python application services
- Local CLI for author and administrative workflows
- FastAPI service boundary
- Browser-based planning and review workspace
- Background workers for long-running jobs
- Project artifact directory for portable, inspectable content
- Export packages for publishing and archival use

All surfaces call the same application services. CLI, API, UI, and workers must not duplicate pipeline rules or create competing sources of truth.

## 4. Non-Negotiable Product Principles

1. **Explicit identity:** Every operation carries project ID, series/book ID when applicable, canon version, stage, and allowed scope.
2. **No canon, no grounded generation:** Creative work requiring story facts cannot proceed without approved context.
3. **No cross-project contamination:** Files, database records, indexes, caches, and model context are always project-scoped.
4. **Approved truth outranks similarity:** Structured canon and approved plans override retrieved text or model suggestions.
5. **Meaningful story units:** Fiction is segmented by series, book, act, chapter, scene, beat, and paragraph purpose, not arbitrary token boundaries alone.
6. **Smallest sufficient context:** Each call receives only the approved material needed for its task.
7. **Durable artifacts:** Every significant input, output, validation result, approval, and transition is saved and versioned.
8. **Models are replaceable workers:** Models never own workflow state, memory, permissions, or approval policy.
9. **Structured output is untrusted:** Schema-constrained responses still require parsing and validation before persistence.
10. **Deterministic checks first:** Cheap, reliable checks run before subjective or expensive evaluators.
11. **Report before repair:** Validators identify evidence and risk; revision is a separate, explicitly authorized action.
12. **Targeted revision:** Fix reported dimensions while preserving clean text, plot, order, POV, and approved facts.
13. **Human control at high-value gates:** Canon, major plans, risky changes, and publication require human approval.
14. **Bounded automation:** Retry, revision, cost, and tool usage always have limits.
15. **Restartable stages:** Failures preserve prior successful artifacts and can resume without corrupting state.
16. **Engine before interfaces:** Stable services and artifact contracts precede convenience interfaces.
17. **Evidence over marketing claims:** Model, prompt, and architecture choices are selected through benchmarks and observed needs.
18. **Manual final judgment:** BookForge can assist final polish, but publication remains an accountable human decision.
19. **Prompts are product artifacts:** Prompts are versioned, reviewed, tested, and traced like schemas and code.
20. **Compressed context is not truth:** Compression may reduce what a model reads, but it never replaces canonical files, approved artifacts, policy records, review decisions, or validator source material.

## 5. Complete Product Workflows

### 5.1 New book generation

```text
Project intake
-> concept and constraints
-> research plan and approved evidence
-> canon and story bible
-> premise and book architecture
-> act and chapter outline
-> chapter plans
-> scene cards and beats
-> sample chapter calibration
-> scene/chapter drafting
-> humanization and voice passes
-> continuity, style, and reader-experience evaluation
-> targeted revision
-> chapter approval
-> memory and story-state update
-> book-level evaluation
-> manual final polish
-> publication approval
-> export and archive
```

Before bulk generation, the author or editor approves a representative sample for tone, POV, dialogue, pacing, character interpretation, and chapter structure.

### 5.2 Existing manuscript transformation

```text
Import manuscript
-> parse and preserve structural boundaries
-> extract proposed canon, timeline, characters, and summaries
-> review and approve extracted truth
-> classify requested edit mode
-> process by meaningful story unit
-> validate meaning and canon preservation
-> show textual and semantic diffs
-> request targeted revisions
-> approve chapters
-> run manuscript-wide consistency checks
-> manual final polish
-> export
```

Transformation modes include humanization, Westernization or genre alignment, developmental editing, line editing, dialogue/voice editing, continuity repair, and constrained expansion.

### 5.3 Series development

```text
Series premise and rules
-> series bible
-> book-level arcs
-> Book 1 production
-> approved consequences and unresolved promises
-> series memory update
-> next-book planning from approved state
-> cross-book validation
```

Series generation never treats a previous book as an unstructured text dump. It uses approved summaries, character evolution, relationship state, timeline, unresolved threads, promises, deaths, injuries, objects, secrets, and setup/payoff records.

### 5.4 Research-grounded fiction

```text
Research question
-> trusted-source search or import
-> source snapshot and metadata
-> extracted claims with evidence
-> researcher approval
-> approved research fact
-> scoped use in planning or drafting
-> citation and provenance audit
```

The model must flag missing evidence instead of inventing historical details. Research facts and fictional canon remain distinguishable even when both influence prose.

### 5.5 Collaborative review

```text
Artifact ready for review
-> assigned reviewer
-> findings, comments, and diff
-> approve, reject, or request revision
-> new artifact version
-> findings resolved or accepted
-> gate completion
```

Approval applies only to the exact reviewed artifact version. A later change invalidates approval where configured policy requires re-review.

## 6. Creative Planning Model

### Story hierarchy

```text
Series
-> Book
-> Act or Part
-> Chapter
-> Scene
-> Beat
-> Paragraph or line-edit region
```

Each level has a clear purpose. A chapter may optionally act as an installment or sub-book, but it still declares its relationship to the parent book and shared canon.

### Scene cards

Every planned scene should be able to declare:

- Scene ID and sequence
- POV character
- Location and timeline position
- Narrative purpose
- Entry state and exit state
- Required facts and prior dependencies
- Required events or beats
- Conflict and obstacle
- Emotional turn
- Character intent and change
- Setup, payoff, foreshadowing, or unresolved thread effects
- Forbidden changes
- Exit hook
- Target chapter contribution, without a rigid scene word quota

Scene word quotas are advisory only. They must not encourage filler or distort natural pacing.

### Beat planning

Beat plans include plot movement, emotional movement, sensory or environmental purpose, conflict, and a short rule check for common failure modes. BookForge should not generate action-only beat lists that omit emotional and thematic progression.

Every meaningful beat must be detailed enough to draft without invention. A draftable beat declares what happens, who is present, where it happens, the scene goal, conflict source, required reveal or action, emotional movement, physical action, state change, continuity impact, forbidden changes, and connection to the next beat.

Thin beats such as `he investigates the town` or `Darin talks to the sheriff` block drafting when plot, canon, or continuity are at risk. StoryEngine returns a beat-completeness report instead of asking ProseForge to invent missing structure.

### Layered slow-burn beats

Slow-burn Western scenes may use a `LayeredBeatProfile`. It breaks a quiet task into layers such as physical work, environmental detail, character behavior, social contact, plot pressure, visual threat, and restrained reaction.

The goal is controlled pacing: grounded action, character revelation, environmental realism, social pressure, and plot movement without rushing into exposition or immediate violence. A layered profile declares required layers, allowed omissions, escalation order, and forbidden shortcuts such as sudden exposition dumps, unsupported gunfights, or abstract emotional explanation.

### Action logistics planning

Complex action scenes, fights, chases, and gunfights require an approved `ActionScenePlan` before drafting. The plan records scene type, location layout, entrances, exits, cover, hazards, participants, starting positions, weapons, ammunition, available supplies, movement limits, sequence of actions, results, injuries, state changes, and forbidden impossibilities.

Gunfight plans additionally track participant count, weapon ownership, ammunition at start, spare ammunition, shot order, line of sight, reload feasibility, distance, cover, movement plausibility, injury results, and post-fight state updates. ProseForge may dramatize the plan, but it may not add enemies, shots, reloads, movement, injuries, or deaths that the approved plan and current state do not support.

### Setup and payoff tracking

StoryEngine tracks:

- Setup origin and intended payoff
- Expected payoff window
- Current status: planned, planted, reinforced, paid off, intentionally unresolved, or abandoned with approval
- Related characters, objects, secrets, and promises

### Theme governance

`ThemeGovernancePolicy` treats theme as story pressure rather than decoration. Before full-book plotting, each book declares a `ThemeProfile` with primary themes, secondary themes, theme statements, forbidden handling, preferred handling, and review strictness.

Themes answer what value is being tested, what price a character pays, and what choice proves the story's moral pressure. For Western fiction, common themes include justice, redemption, survival, honor, revenge, law versus lawlessness, land and ownership, family, duty, violence and consequence, isolation, and moral choice.

Themes must be dramatized, not explained. They should appear through choices, violence, mercy, refusal, silence, sacrifice, land disputes, broken law, family pressure, survival decisions, and consequences after action. The policy rejects moral lectures, sermon-like dialogue, abstract theme summaries, and characters stating the lesson too cleanly.

`ThemeArc` records how a theme develops from opening position through midpoint pressure, climax test, and final expression. `ThemeBeat` records active theme pressure inside a chapter or scene beat: theme question, dramatized-through actions, visible cost, state change, and forbidden lecture behavior.

StoryEngine connects themes to character profiles, antagonist design, relationship pressure, setup/payoff, and continuity locks. An antagonist may embody a distorted version of a theme, and theme consequences must carry forward through memory rather than disappearing after the scene.

### Character-driven plotting gate

Before generating a full-book outline, StoryEngine requires approved profiles for the protagonist, antagonist, major POV characters, major allies and rivals, relationship-critical family members, and recurring side characters already required by the premise.

StoryEngine derives and records:

- Motivation and goal map
- Conflict matrix between important characters
- Relationship tensions and incompatible needs
- Fears, weaknesses, loyalties, and pressure points
- Likely behavior under pressure
- Betrayal, alliance, refusal, sacrifice, and escalation risks
- Arc positions and required turning points
- Character-driven setup/payoff opportunities

The plotting gate fails with a reviewable missing-profile report rather than inventing undeclared key characters or random conflict. New key characters discovered during planning enter the proposed-profile workflow and must be approved before dependent outline sections are approved.

### Antagonist design

A primary antagonist requires an approved `AntagonistProfile` before full-book plotting. It extends `CharacterProfile` with external goal, internal need, motive, moral code, fear, weakness, threat method, cruelty and escalation rules, mercy rules, speech constraints, relevant equipment, pressure response, and forbidden behavior.

The antagonist must create conflict through comprehensible goals, methods, choices, and pressure rather than random cruelty. Cartoon speeches, unexplained reversals, arbitrary violence, and sudden panic are invalid unless an approved arc event supports them.

### Supporting-cast purpose

Every non-incidental supporting character declares at least one active story function, entry reason, required-until point, exit condition, and unresolved obligation. Functions may include revealing information, creating conflict, helping or betraying someone, representing community pressure, testing a value, carrying a secret, delaying progress, mirroring another character, or delivering a consequence.

When a function is complete, StoryEngine must retire the character, merge the role through an approved plan change, or assign a new approved function. Recurring appearances without an active purpose produce a cast-utility finding.

### Character arc planning

Each main, major supporting, and materially evolving recurring character has an approved arc plan with baseline traits, starting state, desired or possible end state, pressure points, turning points, allowed growth, forbidden jumps, regression conditions, and relationship dependencies.

Behavioral change requires an evidenced `CharacterChangeEvent`, such as pressure, loss, trauma, victory, decision, revelation, relationship shift, moral choice, survival event, or consequence. Growth may be nonlinear, but abrupt change without sufficient cause is character drift.

## 7. CanonCore

CanonCore is the authority for approved story truth.

### Canon types

- Character profiles, voice rules, reference rules, roles, and durable identity
- Relationships and knowledge boundaries
- Locations and physical constraints
- Timeline events and relative chronology
- Objects, weapons, possessions, injuries, and status
- World rules, institutions, cultures, and naming rules
- Setting period, geography, technology, material-culture, and approved intentional-anachronism rules
- Plot constraints and forbidden changes
- Secrets and who knows them
- Promises, setups, and unresolved threads
- Style, POV, tense, genre, and audience rules
- Series-level facts and book-specific overrides

### Character profiles

Every named, recurring, or plot-relevant character is a first-class CanonCore entity with a stable `character_id`. Character profiles are structured records rather than unvalidated story-bible notes.

The profile model is tiered so incidental characters do not create unnecessary overhead:

| Tier | Use | Minimum detail |
| --- | --- | --- |
| **Main** | Protagonists, antagonists, and major POV characters | Full identity, appearance, personality, motivations, voice, references, roles, arc, relationships, and forbidden changes |
| **Major supporting** | Recurring allies, rivals, family, and mentors | Identity, role, distinguishing traits, voice guidance, relationships, and continuity constraints |
| **Recurring side** | Recurring officials, workers, neighbors, informants, and community figures | Medium profile with purpose, traits, voice, relationships, pressure behavior, and continuity constraints |
| **Minor named** | Plot-relevant witness, courier, deputy, or other limited named role | Lightweight profile with identity, purpose, role, voice summary, relationships, and continuity notes |
| **Incidental** | One-scene background people with no continuity effect | Controlled descriptor only; no full profile required |

A descriptor such as `the older woman behind the desk` is valid only while the person has no recurring or plot-relevant identity. A character requires at least a lightweight profile when they recur, affect plot, possess or reveal important information, hold a significant object, or create continuity consequences.

Character contracts include:

- Project, series, book scope, stable ID, aliases, canonical name where known, and display label
- Tier, story role, social role, age representation, gender when relevant, and appearance
- Personality, motivations, values, fears, flaws, arc, and forbidden changes
- Story purpose, mannerisms, behavior under pressure, dialogue importance, and equipment references
- Voice profile covering tone, diction, sentence patterns, vocabulary, dialogue habits, and approved samples
- Reference rules with allowed, forbidden, and context-specific names or descriptors
- Source artifacts, canon lifecycle, version, and approval record

Age may be exact, approximate, ranged, or apparent. An unnamed character is not assigned a name unless an approved change introduces one. Story role and in-world social role remain separate.

Character data is split by ownership:

```text
CanonCore:
  durable identity, baseline traits, appearance, roles, voice,
  reference rules, arc constraints, and approved facts

MemoryVault:
  current location, condition, injuries, possessions, emotional state,
  relationship state, knowledge state, secrets known, and arc position
```

The initial contract may keep lightweight fields together in `CharacterProfile`, but its identifiers and boundaries must allow later extraction into `CharacterVoiceProfile`, `CharacterReferenceRules`, `CharacterMannerismProfile`, `CharacterMotivationProfile`, `CharacterPressureBehavior`, `CharacterRelationship`, `CharacterKnowledgeState`, and `CharacterContinuityState` without changing consumers.

### Character governance

`CharacterGovernancePolicy` controls naming, profile depth, cast growth, promotion, and plot-readiness rules.

Core rules:

- Every proper-named fictional character requires a stable ID and at least a proposed profile before the name may appear in a candidate artifact.
- An approved artifact cannot introduce an unprofiled named character.
- Main and major supporting characters require full approved profiles before full-book plotting.
- Recurring side characters require approved medium profiles before recurring use.
- Minor named characters require approved lightweight profiles before approval of the artifact that names them.
- Incidental people remain descriptor-only unless naming or promotion is justified by plot, continuity, relationship, dialogue, or later-scene relevance.

Incidental descriptors are scene-scoped records with stable descriptor IDs, function, display label, naming permission, and continuity relevance. They may use labels such as `the rider`, `the woman at the counter`, or `the livery hand` without creating false cast importance.

Promotion from incidental to minor named or recurring side requires a `CharacterPromotionRequest` describing why the person now matters, proposed tier, profile additions, affected artifacts, and reviewer decision. Promotion preserves the original descriptor lineage and does not silently rewrite prior prose.

Generated names and profiles remain proposals. A model cannot approve a character, promote a tier, or expand its own naming allowance.

### Object and resource profiles

Every continuity-relevant weapon, possession, vehicle, animal, document, key, evidence item, consumable, or other resource has a stable `object_id` and an approved durable profile. CanonCore owns identity and rules such as type, name, capacity, permitted uses, consumption behavior, prerequisites, and immutable physical constraints.

Objects are classified by continuity impact:

| Class | Meaning | Validation expectation |
| --- | --- | --- |
| **Critical** | Incorrect state can break plot or make an action impossible | Complete state and prerequisite validation |
| **Important** | State materially affects realism, access, movement, health, or scene logic | State validation when used or changed |
| **Ambient** | Primarily descriptive flavor | Track only when promoted by story consequences |
| **Untracked** | Generic background item with no continuity value | No durable state record |

Only critical and important objects require routine state tracking. Ambient or untracked details are promoted when they recur, affect plot, carry evidence or information, transfer ownership, constrain action, or otherwise create continuity consequences.

An object profile may declare resources and rules such as maximum capacity, unit, amount consumed per use, reload or replenishment requirements, valid holders, location constraints, and terminal states. Current counts, holders, locations, conditions, and availability belong to MemoryVault rather than the durable profile.

### Canon lifecycle

```text
proposed -> under_review -> approved -> superseded
                       -> rejected
```

Canon is versioned. Superseding a fact preserves its history and identifies the approving decision. Generated facts remain proposals until approved.

### Canon change rules

- A model cannot directly approve, mutate, or delete canon.
- A draft may propose a new fact and must report it explicitly.
- Contradictory approved facts block grounded generation until resolved or explicitly scoped.
- Validators report contradictions; they do not rewrite canon.
- Canon used by a run is pinned to exact versions for reproducibility.

## 8. ResearchCore

ResearchCore provides evidence-grounded knowledge without becoming an unrestricted browsing agent.

### Required capabilities

- Research briefs and questions
- Source ingestion for web pages, PDFs, books, notes, and approved archives
- Source metadata, snapshot date, author, publisher, URL or local reference, and rights notes
- Claim extraction linked to evidence passages
- Confidence and review status
- Historical timeline and terminology checks
- Period research packs scoped by date range, geography, culture, and category
- Historical fact records with temporal and geographic validity, evidence, confidence, and approval state
- Availability profiles for technology, weapons, ammunition, transport, medicine, clothing, occupations, law, communication, money, food, and material culture
- Stale-source detection when an external source changes or disappears
- Separation of sourced fact, inference, disputed claim, and fictional adaptation
- Project-scoped retrieval and citation provenance

### Research policy

- Prefer primary and authoritative sources.
- Do not copy copyrighted reference prose into generated books.
- Public-domain style references may inform analysis, but BookForge must avoid close imitation of a living author's distinctive style.
- Research is approved before it becomes hard constraints for planning or validation.
- Notebook or external research tools may assist but never become BookForge's source of truth.

### Authenticity packs and historical facts

A historical, cultural, or environmentally sensitive project requires an approved `AuthenticityPack` before grounded drafting. `PeriodResearchPack` is its period-focused profile. The pack is scoped to the story's exact date or date range, location hierarchy, environment, relevant cultures or communities, and declared authenticity strictness.

ResearchCore stores historical knowledge separately from fictional canon:

```text
HistoricalFact:
  what existed, where, when, for whom, and under what conditions

CanonCore:
  what exists, is owned, is known, or happens inside this story
```

Each `HistoricalFact` records its category, claim, valid-from and valid-until dates where known, geographic and cultural scope, evidence references, source quality, uncertainty, review status, and whether it is approved for drafting. Absence from an approved pack means `research_needed`, not automatic historical impossibility.

Authenticity packs contain approved, blocked, disputed, and research-required entries. They may cover setting, geography, weather, terrain, seasons, technology, weapons and ammunition, transport, realistic travel distance and time, clothing and materials, medicine, health and survival, occupations, law enforcement, town or settlement structure, money and trade, food and supplies, communication, religion, speech, social customs, and relationships among Indigenous, settler, migrant, and frontier communities.

If a detail materially affects realism, plot, culture, movement, survival, law, conflict, or technology, BookForge does not guess. It creates a `ResearchNeededRequest` unless the active pack or an approved fictional exception supports the detail.

Cultural and social authenticity checks combine approved sources, community-specific context, sensitivity policy, and accountable human review. Model output may identify evidence-backed risks or stereotypes, but it cannot declare a culture authentic or approve a representation by itself.

Intentional anachronisms are explicit project exceptions with reason, scope, approving actor, affected artifacts, and expiry or supersession rules. They do not disable unrelated period checks.

## 9. MemoryVault And Context Engineering

MemoryVault is a product name for concrete, versioned records. It is not chatbot memory and does not store vague model recollections. Its implementation consists of approved canon, source provenance, append-only traces, hierarchical summaries, current story state, retrieval indexes, and series relationships.

### Memory layers

```text
L0: approved source artifacts and canon
L1: append-only run and transition trace
L2: scene, chapter, act, and book summaries
L3: current story state, timeline, character states, relationships, objects, and unresolved threads
L4: selective retrieval over narrative, style, and research artifacts
L5: series relationship graph and cross-book memory
```

L0-L3 are structured and authoritative. L4-L5 support discovery and reasoning but never override approved facts.

### Memory updates

After an approved scene, chapter, or book, the system proposes:

- Summary and plot advancement
- Character and relationship changes
- Emotional state changes
- Timeline updates
- New facts or research dependencies
- Injuries, deaths, possessions, and location changes
- Setups, payoffs, promises, secrets, and unresolved threads
- Future constraints

Updates are transactional. If a memory update fails, the prior memory remains valid and is marked stale rather than partially replaced.

### Character state

Character state is temporal and separate from the durable CanonCore profile. Each update records its source artifact, story position, prior state, proposed changes, approval status, and validity interval.

Tracked state may include location, health, injuries, possessions, emotional condition, relationship status, facts known or suspected, secrets, titles, social standing, and arc position. Baseline personality or voice changes require a CanonCore change proposal; temporary behavior caused by current circumstances remains story state.

`CharacterArcState` records baseline values, current values, approved change events, earned capabilities or limitations, active pressure, relationship-dependent changes, allowed next movement, and forbidden jumps. It distinguishes temporary mood from durable development and validates every transition against the approved arc plan.

### Character evolution across books

After each approved book, BookForge proposes a `CharacterEvolutionDelta` for every continuing important character. It may include physical changes, scars and limitations, fears and trauma, beliefs, skills, relationships, allies and enemies, reputation, lessons, obligations, promises, secrets, and unresolved consequences.

Series character state is layered rather than reset:

```text
base character profile
+ approved Book 1 evolution delta
-> Book 2 starting state
+ approved Book 2 evolution delta
-> Book 3 starting state
```

Each delta cites source artifacts and change events, is reviewed before promotion, and becomes a carry-forward constraint for later books. A later book cannot silently revert a scar, relationship, belief, reputation, learned skill, or consequence without an approved explanation or change event.

### Resource, inventory, and state continuity

BookForge tracks continuity-relevant objects, resources, inventories, injuries, locations, knowledge, and state transitions. Story logic is represented explicitly:

```text
approved before-state
-> evidenced story event
-> proposed transition
-> prerequisite and invariant validation
-> approved after-state
```

Core contracts include `ObjectProfile`, `ObjectState`, `ResourceState`, `InventoryState`, `StoryEvent`, `StateTransition`, and `ContinuityRule`.

An object state records its current holder or owner, location, condition, availability, resource quantities, last relevant event, source artifact, story position, version, and approval state. A transition records:

- Stable transition, project, book, chapter, scene, actor, and target IDs
- Action and event type
- Before value, delta or transfer, and after value
- Required preconditions and invariants
- Source evidence and artifact version
- Proposed, approved, rejected, or superseded lifecycle state

Examples include ammunition consumption and reloading, money or medicine use, object transfer or destruction, acquiring or losing keys and evidence, vehicle or animal movement, injury and healing, death, and knowledge revelation.

State transitions are transactional and ordered by story position. They fail when the prior state or prerequisites do not match, and they never partially update inventory. Extractors may propose events and transitions after a scene or chapter, but confidence alone cannot approve them. The local workflow requires review; a later project policy may promote only deterministic low-risk transitions from an approved source artifact with complete provenance, audit, rollback, and no canon conflict.

### Continuity locks

`ContinuityLockPolicy` identifies approved details that cannot change silently. A `LockedDetail` is a versioned constraint over CanonCore or MemoryVault truth, not a separate truth store. It references the authoritative record, property path, value or invariant, source artifact, story position, lock level, scope, version, and approval record.

Lock levels are:

| Level | Meaning | Examples |
| --- | --- | --- |
| **Strict** | Requires an explicit valid event or approved canon change before the value may differ | Character and horse identity, ammunition, money, ownership, death, destroyed objects |
| **Guarded** | May evolve, but the change requires evidence, transition logic, and review according to policy | Injuries, motivations, relationships, personality development, supplies, social standing |
| **Soft** | Consistency is preferred; variation produces a review signal rather than an automatic block | Mood, replaceable clothing, incidental descriptive details |

Default lockable domains include character names and aliases, animal identities, weapons and ammunition, injuries, health, money, supplies, inventory, locations, travel state, timeline, motivations, relationships, personality baselines, secrets, knowledge boundaries, objects, documents, promises, and setup/payoff threads.

A lock changes only through an approved `StateTransition`, canon change, or scoped override with reason and audit. For example, an approved shot may update ammunition from three to two; a later claim of three rounds is invalid unless an approved reload or acquisition transition intervenes.

The lock projection is rebuilt from authoritative records and validated for staleness. Deleting or editing a lock cannot mutate canon or story state.

### Numeric continuity locks

`NumericLock` is a specialized locked detail for plot-relevant numbers. It tracks counts, distances, days, quantities, money, supplies, ammunition, enemies, horses, wagons, rooms, documents, livestock, injuries, people present, and similar values when they affect plot, logistics, survival, combat, travel, cost, or continuity.

Each numeric lock records subject, property, value, scope, source artifact, lock level, allowed transition events, and approval status. A `NumberTransition` records before value, delta or replacement, after value, reason, source event, and validation status.

Flavor numbers may remain soft. Approximate phrases such as `a few stars`, `a handful of dust`, or `dozens of flies` are not strict locks unless they become plot-relevant. Once a number controls story logic, a later contradictory number requires an approved arrival, departure, death, reveal, correction, spending, consumption, travel, or other transition event.

### Typed relationships and graph memory

BookForge designs for graph-shaped story knowledge from the beginning but does not require a graph database. Early phases store approved entities, facts, and typed relationships as files or relational records.

```json
{
  "subject": "character:darin_mayweather",
  "relation": "distrusts",
  "object": "character:deadeye_harlan",
  "source_artifact": "chapter_006_summary_v1",
  "canon_status": "approved",
  "valid_from": "chapter:006",
  "valid_until": null
}
```

A relationship record includes:

- Project, series, and book scope
- Subject, relation type, and object
- Source artifact and evidence
- Canon lifecycle state
- Valid-from and optional valid-until story position
- Confidence for extracted proposals
- Approving actor and version where approved

Important relationship domains include:

- Trust, conflict, loyalty, betrayal, kinship, and emotional debt
- Knowledge boundaries: knows, suspects, hides-from, and revealed-in
- Ownership, possession, location, injury, death, and status
- Event causality and consequences
- Setup, promise, payoff, and unresolved-thread dependencies

Graph memory follows the same canon lifecycle as every other fact. A model may propose a relationship or state transition, but it cannot promote it to approved truth.

The relational implementation remains authoritative. A later graph layer is a derived projection used for traversal and explanation, not a second writable canon source.

Graph-powered product uses are limited to concrete needs:

1. Continuity checks across relationships, injuries, objects, locations, and knowledge states
2. Context selection for the active scene or chapter
3. Setup, payoff, promise, and unresolved-thread tracking
4. Cross-book consequence and series planning
5. Reviewer explanations showing the relationship path behind a finding

Graph data does not replace chapter summaries, scene cards, prose samples, style guides, voice examples, or human review.

### Context package

Every model call receives a typed context package containing only applicable sections:

1. Role and operation
2. Project, book, chapter, scene, and canon identity
3. Hard rules and permissions
4. Approved canon and evidence
5. Progress summaries and relevant state
6. Local plan and source artifact
7. Adjacent context such as previous scene/chapter and next planned unit
8. Retrieved context with provenance
9. Forbidden changes
10. Output contract and validation checklist

Every context package records all source IDs and versions. Missing required context produces a clear failure or review request, never silent invention.

Context optimization may compress selected presentation context for model efficiency, but the original source artifacts remain canonical. Compressed text is a derived view, not an approved fact source. Validators, review gates, memory promotion, and publication checks compare output against original approved sources and recorded source IDs, not against compressed summaries.

For scene work, character context is selected rather than dumped wholesale. It includes only the POV character, characters present, materially mentioned absent characters, applicable motivations, story functions, antagonist constraints, pressure behavior, arc state and allowed movement, relationship and knowledge constraints, speaker voice and reference rules, current continuity state, and forbidden changes. Incidental descriptors are included only when required by the scene plan.

The context also carries naming rules: whether new named characters are forbidden, which proposed characters are allowed, which background roles must remain descriptor-only, and whether a descriptor has an approved promotion request. The model must not invent a proper name merely to add flavor.

Object and resource context is also selected by scene relevance. It includes only objects used, transferred, constrained, or materially referenced in the scene, together with current holder, location, condition, resource counts, applicable rules, prerequisites, and forbidden state changes. The model must not increase a resource, restore an object, move an item, or change ownership without an evidenced event.

Drafting context uses the current `canonical_working_source` for prior prose and approved memory. Superseded rough originals are excluded from normal retrieval to prevent regression into old wording, old continuity errors, or unapproved facts.

Beat context includes the detailed beat, layered-beat requirements where active, missing-field status, forbidden events, continuity impact, and connection to adjacent beats. A plot-critical beat with missing required fields blocks drafting.

Theme context includes only the active themes relevant to the scene, including the theme question, character pressure, moral choice, visible cost, preferred dramatization methods, and forbidden lecture behavior. ProseForge must not turn theme guidance into narration that explains the lesson directly.

Action-scene context includes the approved logistics plan, participants, starting positions, weapon and ammunition state, line of sight, movement limits, sequence constraints, numeric locks, and required post-scene transitions. ProseForge may not exceed the approved action plan without returning a revision or planning request.

Period-sensitive calls include a `period_lock` containing the applicable date or range, location, cultures, strictness, approved research-pack version, relevant allowed and blocked details, approved intentional exceptions, and a rule to return `research_needed` when evidence is missing or disputed. Approved historical facts outrank model assumptions.

Generation and validation calls also receive a scoped `locked_continuity` projection containing only relevant strict and guarded details, their authoritative record versions, applicable transition rules, and permitted change paths. Missing or stale lock data blocks grounded generation when the affected detail is required.

When a Western style profile is active, relevant calls also receive behavior-first narration rules, dialogue and dialect settings, character-specific voice constraints, blocked modernisms, approved interiority exceptions, and only the scene-relevant glossary entries. The full glossary is never dumped into every prompt.

Western calls also receive a compact `prime_directive` field before detailed instructions: consistent, physical, era-accurate, and character-driven. It lists the active `must_not` constraints and `must_show_through` channels for the current operation, then points to the specific policy sections that provide enforceable rules.

### Context optimization and compression

BookForge may include a context optimization layer for reducing token load and noise before a model call. Its responsibilities are:

- Context ranking
- Context budgeting
- Safe compression of non-canonical presentation material
- Context audit logging
- Retrieval fallback to original source material
- Compression quality checks

Adapters such as Headroom may be evaluated as optional compressors, but no compressor is core writing authority. A compressor cannot approve canon, change artifact state, mutate memory, weaken policy, or become the only copy of any source-of-truth material.

Safe early compression targets:

- Tool output
- Logs
- Validator reports
- Diff summaries
- QA reports
- Retrieval previews
- Agent scratch context

Unsafe default compression targets:

- Canon bible
- Character profiles
- Timeline and continuity locks
- Chapter contracts and plot locks
- Approval records
- Final manuscript text

These unsafe targets may be summarized for display or prompt budgeting only when the original remains linked and retrievable, the context package records the original source IDs and versions, and validators still check against the original approved sources.

The correct pattern is:

```text
canonical source remains unchanged
-> selected context is optionally compressed for presentation
-> model output is generated from the scoped package
-> validators compare output against original approved sources
-> humans approve final changes
```

### Retrieval evolution

1. Structured context selection from approved records
2. Per-project lexical retrieval with strict identity and version filters
3. Per-project embeddings only after context and provenance contracts are stable
4. PostgreSQL plus pgvector for production retrieval after benchmarked need
5. Optional dedicated vector service only after measured scale or filtering limitations
6. PostgreSQL relationship and state queries after product persistence exists
7. Derived graph projection for complex series traversal after structured series memory works
8. Specialized graph database only if benchmarks show relational queries and projections are insufficient

No global retrieval across projects is permitted by default.

### Project knowledge base

Each project has one isolated knowledge base containing approved and reviewable material:

- Story bible and canon records
- Research sources, claims, and evidence
- Style guide and approved voice samples
- Plans, scene cards, and editorial decisions
- Approved chapters and hierarchical summaries
- Validation reports and accepted-risk records

The knowledge base is a scoped view over BookForge artifacts, not a separate truth store. Early retrieval uses structured selection and lexical search. Full-text, vector, and graph adapters arrive only in their assigned phases and must preserve project, version, approval, and provenance filters.

## 10. Intelligence Layer

The Intelligence Layer adapts useful platform patterns from document-grounded AI systems while preserving BookForge's stricter fiction-production controls.

### Capability registry

Automation is granted named capabilities rather than unrestricted tools:

```yaml
capability: humanize_chapter
allowed_tools:
  - read_artifact
  - read_canon
  - write_candidate_artifact
  - run_diff
  - run_validators
forbidden_tools:
  - approve_artifact
  - mutate_canon
  - publish_export
required_gates:
  - canon_approved
  - source_artifact_exists
  - style_guide_loaded
max_attempts: 2
max_cost_usd: 0.50
```

Every capability declares actors, inputs, outputs, permitted tools, prohibited effects, required gates, budgets, retry limits, and audit events. The registry is enforced by application services; prompt instructions alone are not a security boundary.

### Persona registry

BookForge supports versioned agent personas for role discipline. A persona is a behavior and judgment lens, not a permission source and not a workflow engine.

The architecture rule is:

```text
Personas shape judgment. Capabilities grant permission. Services mutate state. Humans approve high-value decisions.
```

Personas prevent generic model behavior by giving each model run a narrow professional stance. They must not override CanonCore, MemoryVault, PolicyCenter, workflow state, validators, capabilities, permissions, publication gates, or human approval.

The initial `PersonaRegistry` stores versioned persona definitions, prompt bindings, capability mappings, and evaluation fixtures:

```yaml
persona_id: western_prose_editor
version: 1.0.0
purpose: Improve Western prose style while preserving canon, meaning, POV, tense, and sequence.
domain_focus:
  - physical action
  - Western dialogue
  - period tone
  - reduced over-explanation
authority_level: advisory_worker
allowed_capabilities:
  - evaluate_style
  - suggest_revision
  - rewrite_candidate_text
forbidden_capabilities:
  - approve_artifact
  - mutate_canon
  - invent_plot_events
  - publish_export
required_inputs:
  - source_text
  - approved_canon
  - style_profile
  - character_profiles
  - period_policy
output_contract:
  - revised_text
  - change_report
  - risks
  - proposed_questions
```

The starting personas are:

- **Researcher:** verifies historical, cultural, environmental, weapon, travel, clothing, law, and period details; may create research questions, summarize sources, extract claims, and propose research facts; may not invent facts, approve research facts, convert unverified research into canon, or copy source prose into manuscripts.
- **Canon Editor:** protects approved story truth across canon extraction, conflict detection, relationship state, knowledge boundaries, object state, injury state, and status consistency; may not approve canon, silently change canon, or resolve contradictions without review.
- **Story Architect:** builds coherent plot, chapter plans, scene cards, beats, setup/payoff, theme pressure, antagonist pressure, supporting-character purpose, and character-driven causality; may not draft final prose, ignore approved motivations, or add unapproved named characters.
- **Western Prose Editor:** makes prose physical, blunt, restrained, and Western while preserving meaning; may support humanization, Westernization, line editing, show-don't-tell revision, physical grounding, and modernism cleanup; may not add plot, canon, modern slang, purple prose, or cartoon dialect.
- **Continuity Auditor:** finds broken story logic across ammunition, injuries, money, supplies, animal identities, locations, timeline, enemy count, travel distance, state transitions, and series memory; reports findings and evidence unless explicitly assigned a targeted revision capability.

Later personas may include `dialogue_editor`, `character_keeper`, and `publisher`, but early BookForge should use one controlled engine with many personas and staged capabilities, not autonomous agents chatting with each other.

Persona selection is stage-bound:

```text
stage selects persona
stage selects capability
capability grants tools
service enforces rules
validator checks output
human approves important changes
```

Every model run records persona metadata for traceability:

```json
{
  "model_run_id": "run_123",
  "stage": "humanize_chapter",
  "persona_id": "western_prose_editor",
  "persona_version": "1.0.0",
  "prompt_id": "humanize_western.v1",
  "capability": "humanize_chapter",
  "context_package_id": "ctx_456",
  "provider": "local",
  "model": "qwen-local",
  "artifact_output": "chapter_008_humanized_v2"
}
```

Persona fixtures test behavior and limits. Example checks include: Western Prose Editor preserves plot facts and avoids dialect overuse; Continuity Auditor detects ammunition mismatch and injury disappearance without rewriting prose; Researcher flags uncertain historical detail, separates evidence from inference, and does not approve facts.

### Adapter boundaries

External frameworks and services integrate behind BookForge-owned contracts:

```text
bookforge/
  ingestion/
    web_source.py
    pdf_source.py
    office_source.py
  retrieval/
    structured_context.py
    lexical.py
    full_text.py
    vector.py
    graph.py
  research_adapters/
    web_search.py
    document_index.py
    graph_retrieval.py
  agent_interface/
    commands.py
    tool_registry.py
    permissions.py
    assistant_loop.py
```

LlamaIndex-style ingestion, LightRAG-style retrieval, external research systems, MCP tools, or local assistant frameworks may be evaluated as adapters. None may own canon, workflow state, approvals, artifact lineage, or publication readiness.

### Review notebook and decision log

BookForge keeps persistent institutional memory for:

- Approved and rejected creative decisions
- Editorial comments and character interpretations
- Manual overrides and accepted risks
- Model or provider failures that affected a decision
- Style calibration and sample-chapter decisions
- Publication notes

Notebook entries are project-scoped, searchable, attributable, timestamped, linked to artifacts or findings, and immutable after signing except through a superseding entry. Important decisions may be promoted into CanonCore or project policy only through their normal approval lifecycle.

### Sandboxed analysis and export tools

The initial implementation uses predefined deterministic services. A later restricted execution worker may support word-count analysis, structural reports, charts, DOCX/EPUB/PDF packaging, and other derived outputs.

Allowed workers may read scoped project artifacts, write derived reports, and export approved content. They may not mutate canon, approve artifacts, access other projects, execute unrestricted shell commands, or contact unapproved external services. Workspaces are ephemeral, resource-limited, network-restricted by policy, and cleaned after completion.

### Assistant interface

A lightweight author/operator assistant may translate natural-language requests into explicit BookForge commands such as showing chapter blockers, running an authorized humanization stage, or summarizing proposed canon changes. It remains a convenience interface over the engine and cannot bypass permissions, gates, budgets, or approval.

### Visualization

The review application may visualize character relationships, knowledge boundaries, timelines, setup/payoff state, chapter dependencies, canon conflicts, revision history, validation severity, cost, and throughput. Visualizations are derived read models and never writable canon sources.

## 11. ProseForge

### Writing modes

- Constrained scene or chapter drafting
- Source-supported expansion
- Humanization and AI-pattern cleanup
- Developmental editing
- Line editing
- Dialogue and character-voice editing
- Genre and tone alignment
- Continuity-aware repair
- Compression and pacing adjustment
- Final polish assistance

Each mode declares what it may change. Humanization, line editing, and voice editing operate in **no-invention mode** unless the user explicitly authorizes structural changes.

### Humanization rules

Humanization may improve wording, rhythm, specificity, dialogue naturalness, emotional clarity, transitions, and sentence variation. It may not silently add events, characters, locations, backstory, relationships, objects, historical claims, or plot resolutions.

### Period-authentic writing rules

When authenticity controls are enabled, ProseForge uses the effective `AuthenticityPolicy`, approved `AuthenticityPack` and applicable `PeriodResearchPack` profile, CanonCore world rules, and relevant object profiles. It may not introduce unsupported technology, weapons, ammunition, transport, medicine, clothing, law, occupations, money, communication methods, customs, slang, environmental conditions, or cultural claims.

When evidence is missing or conflicting, ProseForge reports `research_needed` and identifies the affected passage or planned detail rather than guessing. Approved intentional anachronisms are permitted only in their recorded scope. Historical validity does not automatically make a phrase suitable for the project's genre voice.

### Western prose and dialogue policy

Historical Western projects may enable a versioned `WesternStyleProfile`. This is a genre-writing policy, separate from historical accuracy and individual character voice:

The first rule of the profile is the **Western Manuscript Prime Directive**:

```text
A Western manuscript must be consistent, physical, era-accurate, and character-driven.

The story must feel lived-in, historically grounded, and driven by people under pressure.
Preserve continuity, avoid modernity, respect the year, and show meaning through action
and consequence rather than explanation.
```

The prime directive is enforced by concrete policies rather than prompt wording alone:

- **Consistent:** CanonCore, MemoryVault, continuity locks, numeric locks, character arc state, and state transitions preserve story reality.
- **Physical:** Western prose style, layered beats, action plans, and ProseForge prompts ground scenes in action, dialogue, silence, tools, horses, guns, weather, distance, work, and consequence.
- **Era-accurate:** authenticity policy, period research packs, Western glossary, ResearchCore, and anachronism checks prevent wrong-year weapons, tools, customs, tactics, language, and details.
- **Character-driven:** character profiles, antagonist design, supporting-character functions, arc state, theme pressure, and StoryEngine prevent random plot and unearned behavior.

The first official genre pack is the Western pack at `docs/info-plan/genre-packs/western/`. It formalizes the uploaded Western writing guide into machine-usable BookForge artifacts:

- `western_style_guide.md` for the genre operating rules.
- `western_prompt_blocks.md` for modular generation and revision instructions.
- `western_validation_checklist.md` for QA and human review.
- `western_subgenre_config.yaml` for classic, historical, frontier romance, revisionist, outlaw, and weird-west routing.
- `western_dialogue_rules.md`, `western_era_accuracy_rules.md`, and `western_character_rules.md` for specialized controls.

The pack must be injected before drafting and reused during planning, beat expansion, drafting, style revision, dialogue revision, authenticity review, continuity review, and final Western prime-directive validation.

```text
Period accuracy:
  Is the detail supported for the time and place?

Western prose style:
  Is the writing direct, physical, restrained, and behavior-driven?

Character voice:
  Would this specific character speak, notice, or act this way?
```

The default Western prose rules are:

- Reveal emotion primarily through behavior, choices, movement, silence, dialogue, physical reaction, and interaction with objects.
- Prefer literal, concrete, controlled action over abstract emotional labels, decorative metaphor, or dramatic summary.
- Let readers infer danger, fear, anger, grief, tension, and loyalty from observable scene evidence.
- Use changes in posture, distance, eye contact, room activity, speech, and handling of objects to communicate social pressure.
- Avoid repeating an emotional explanation after the scene has already demonstrated it.
- Avoid purple prose, modern therapeutic language, modern corporate language, and unsupported tactical terminology.

Behavior-first narration does not prohibit interior thought. Direct interiority is permitted when POV, character arc, pacing, or scene clarity requires it. The rule prevents redundant spoon-feeding, not psychological depth.

Western dialogue should be plainspoken, concise, character-specific, and lightly rough where appropriate. It may use contractions, limited dropped auxiliaries, regional vocabulary, and imperfect grammar supported by the character profile. It must avoid caricature, heavy phonetic spelling, eye dialect, repetitive apostrophes, and generic `pardner`-style parody.

Dialogue policy includes configurable dialect intensity, maximum nonstandard density, allowed constructions, blocked modernisms, and readability requirements. No validator should rewrite a grammatically complete sentence merely to make it look less educated; social background and character voice remain authoritative.

### Western glossary and word bank

Western projects maintain an approved, source-linked glossary covering period objects, horses and tack, weapons and ammunition, clothing, settlements and frontier institutions, occupations, law, transport, money, trade, supplies, landscape, and regional speech.

Each entry records term, meaning, date and geographic scope where applicable, approved and blocked forms, source evidence, usage notes, related object or historical-fact IDs, and project status. Terms enter writing context only when relevant to the scene and valid for its year, location, culture, character, and object state.

The glossary exists for consistency and authenticity, not ornament. ProseForge must not force archaic terminology, overload a passage with specialized vocabulary, or use a broadly Western term that the active period pack has not approved.

### Western dialogue skill

An optional `WesternDialogueSkill` may rewrite dialogue and nearby narration for directness, mild dialect, period-aware vocabulary, and character-specific rhythm. It is a reviewed prompt package, not workflow authority.

It may change wording, rhythm, dialogue directness, limited dialect, and approved terminology. It may not change plot, canon, relationships, knowledge boundaries, story state, or weapon and technology details. Required validation includes meaning preservation, canon preservation, dialogue naturalness, modernism checks, dialect-overuse checks, and period-glossary checks.

### Voice pass

A dedicated voice pass checks whether major characters remain distinguishable in vocabulary, rhythm, directness, formality, emotional avoidance, and dialogue habits. It must avoid reducing voice to repetitive catchphrases or stereotypes.

### Final polish

The final stage may surface line-level suggestions and remaining risks. It should not automatically loop a fully approved manuscript through repeated broad rewrites. The author or editor performs or approves final changes.

## 12. JudgePanel

### Deterministic validators

- Schema validity
- Identity and canon-version match
- Path and project scope
- Required context and provenance
- Canonical working source selection and no superseded-source retrieval for normal context
- Required files and headings
- Beat completeness for plot-critical beats
- Theme profile, theme arc, and theme-pressure completeness before full plotting
- Required theme beat fields for plot-critical moral-pressure scenes
- Layered-beat required-layer coverage where a layered profile is active
- Empty or truncated output
- Word-count ranges at chapter and book level
- Repetition and duplicated passages
- Placeholder and banned phrase patterns
- Character identity, name, alias, title, age, and allowed-reference rules
- Unapproved invented names for unnamed characters
- Named-character profile existence, required tier depth, and approval-state checks
- Descriptor-only naming restrictions and approved promotion requirements
- Duplicate or near-duplicate character identity and alias checks
- Supporting-character active function, required-until, and exit-condition checks
- Required antagonist profile and required arc-plan completeness before full plotting
- Resource quantities, capacity bounds, consumption, replenishment, and transfer arithmetic
- Numeric-lock arithmetic and allowed transition checks
- Inventory ownership, holder, location, availability, and terminal-state consistency
- State-transition prerequisites and before/after invariants
- Action-scene participant, position, weapon, ammunition, shot-order, movement, reload, and post-fight state checks
- Injury, healing, death, movement, and object-use feasibility where structured rules exist
- Date, location, technology-availability, and approved blocked-term checks from the active period pack
- Weapon, ammunition, transport, and resource compatibility with approved historical and object profiles
- Travel distance and duration against transport, terrain, weather, route, rest, supplies, and animal or character condition
- Location, settlement structure, law, money, supply, clothing, and environment rules where structured evidence exists
- Strict and guarded continuity-lock agreement with approved canon and current story state
- Western glossary consistency, blocked modern vocabulary, and inconsistent object or occupation terminology
- Formatting and export readiness
- Approval requirements
- Missing or duplicate chapters
- Missing action-scene plans for configured fight, chase, or gunfight scenes
- Unsupported artifact references
- Budget and retry limits

### Model-assisted evaluators

- Canon contradiction and unsupported invention
- Character voice, personality, role, and arc drift
- Cast clutter and unnecessary naming of background people
- Motivation, mannerism, pressure-behavior, and character-purpose inconsistency
- Antagonist goal, motive, moral-code, threat-style, cruelty, speech, and pressure-response inconsistency
- Supporting-character utility loss, unresolved exit obligations, and unnecessary recurring appearances
- Unearned growth, forbidden arc jumps, unsupported regression, and missing character-change events
- Cross-book reset of approved scars, skills, beliefs, relationships, reputation, or consequences
- Relationship, knowledge-boundary, and secret-revelation errors
- Timeline, location, object, weapon, resource, inventory, and injury inconsistency
- Missing or unsupported state-changing events in prose
- Source regression into superseded rough text or previously corrected errors
- Thin beats, missing beat layers, or drafting beyond approved beat scope
- Missing theme pressure, underdeveloped theme arcs, or beats that avoid the active moral question
- Theme lecturing, sermon-like dialogue, abstract moral summary, or characters stating the lesson too cleanly
- Violence without consequence where violence-and-consequence is an active theme
- Moral-choice scenes without real cost, tradeoff, refusal, sacrifice, or consequence
- Theme continuity drift where a theme consequence, belief change, or moral debt disappears without resolution
- Gunfight, fight, chase, movement, reload, injury, enemy-count, or logistics implausibility
- Numeric continuity drift for enemies, money, days, distance, horses, supplies, bullets, documents, or people present
- POV and tense drift
- Tone and genre mismatch
- Dialogue naturalness
- Emotional continuity
- Required beat coverage
- Scene purpose and narrative movement
- Pacing, tension, stakes, curiosity, and reader pull
- Meaning preservation during transformation
- Research accuracy against approved evidence
- Period authenticity and anachronism risk across technology, material culture, institutions, behavior, and language
- Cultural and social representation risks against approved evidence and sensitivity policy, always requiring human review
- Weather, terrain, town structure, travel feasibility, law/custom, and supply realism
- Silent changes to locked motivations, relationships, personality baselines, knowledge, injuries, possessions, or setup/payoff state
- Genre-voice authenticity for historically possible but project-inappropriate wording
- Behavioral emotion, physical grounding, unnecessary inner-thought explanation, and reader spoon-feeding
- Western dialogue directness, excessive polish, dialect overuse, caricature, and modern phrasing
- Purple prose, abstract action, forced archaism, and unnatural glossary insertion
- Setup/payoff and unresolved-thread integrity
- Whole-book coherence and style unification

### Western prime directive validator

`WesternPrimeDirectiveValidator` is a rollup evaluator for Western chapters and books. It does not replace lower-level validators. It summarizes whether the manuscript remains consistent, physical, era-accurate, and character-driven by collecting blocking findings and quality findings from canon, continuity, numeric locks, authenticity, Western style, character governance, character arc, theme, beat, and action-logistics checks.

The validator may block approval when high-severity findings violate the prime directive, such as wrong-period details, modern language, character drift, unprofiled named characters, unsupported state changes, impossible weapon or ammunition logic, unexplained number changes, or action logistics failures. Lower-severity style findings route to Western prose revision or review.

### Evaluation contract

Each finding includes:

- Stable issue ID
- Validator and version
- Severity and confidence
- Artifact location
- Evidence
- Violated rule or canon reference
- Recommended action
- Whether it blocks approval

Invalid model output is retried within policy and then recorded as an evaluator failure. It is never interpreted loosely and silently accepted.

### Severity policy

- **Critical:** Security, project contamination, data loss, or severe canon corruption; stage stops.
- **High:** Material canon, plot, meaning, or research failure; approval blocked.
- **Medium:** Important quality issue; review or revision normally required.
- **Low:** Editorial suggestion; does not block approval by default.

Policies may be stricter per project but cannot weaken security or isolation rules.

## 13. Revision And Checker Loop

```text
artifact
-> deterministic validation
-> model-assisted evaluation where configured
-> classify findings
-> targeted revision request
-> new artifact version
-> re-run affected checks plus regression checks
-> human review when limits or risk require it
```

Rules:

- Every revision references issue IDs.
- Clean regions stay unchanged where possible.
- Canon, meaning, scene order, and required beats are preserved unless the approved request changes them.
- Automatic revisions stop at maximum attempts, maximum cost, or repeated failure.
- A revision never overwrites an approved or prior artifact.
- Resolved findings remain in the audit history.

## 14. ReviewDesk And Human Gates

### Standard gates

- Research fact approval
- Canon and story-bible approval
- Premise and outline approval
- Sample chapter calibration
- Chapter or batch approval
- Approval of proposed canon changes
- Book-level quality approval
- Publication approval

Projects may configure intermediate gates, but final publication approval cannot be removed.

### Review workspace

Reviewers need:

- Artifact content and lineage
- Side-by-side and unified text diff
- Semantic change summary
- Added, removed, or changed facts
- Character arc state, change-event evidence, supporting-function status, and antagonist consistency
- Theme arc position, theme beat pressure, moral-choice evidence, and lecture or underdevelopment findings
- Proposed book-end character evolution deltas and cross-book carry-forward differences
- Validation findings with evidence
- Model, prompt, context, cost, and run metadata
- Comments and assignments
- Approve, reject, accept-risk, and request-revision actions
- Filters for unresolved blockers and changed canon-sensitive regions

Accepting risk requires a reviewer identity, reason, and timestamp.

## 15. Publisher

### Supported outputs

Delivery sequence:

1. Markdown
2. DOCX
3. EPUB and HTML
4. PDF and print-oriented packages

### Publication package

- Title and copyright metadata
- Author or pen name
- Front matter
- Table of contents
- Approved chapters in order
- Back matter
- Cover and asset references where supplied
- Export profile and formatter version
- Content manifest and hashes
- Optional validation and provenance archive kept outside the reader-facing manuscript

Publisher exports approved content only. It fails when chapters are missing, out of order, unapproved, or blocked by publication checks.

## 16. Operations And Provider Routing

### PolicyCenter and configuration

BookForge settings are backend contracts before they are interface controls. Phase 0 defines typed schemas, validated YAML or JSON files, resolution services, and immutable policy snapshots. CLI, API, and browser settings pages arrive later as management surfaces over those contracts.

Policy families include:

- Project, series, and book identity and lifecycle settings
- Genre, tone, audience, POV, tense, prose style, and content limits
- Canon and no-invention rules
- Memory update, review, and promotion policy
- Knowledge-source and retrieval policy
- Prompt and skill-package policy
- Provider routing, privacy, fallback, and budget policy
- Validation severity and blocking gates
- Review, accepted-risk, approval, and publication rules
- Security, retention, external-service, and data-handling policy
- Export profiles and formatting settings

Settings use layered scope:

```text
system defaults
-> workspace policy
-> project policy
-> series policy
-> book policy
-> explicitly authorized run override
```

The resolver produces one typed effective policy. More specific scopes may override ordinary creative and operational defaults, but they cannot weaken immutable floors for project isolation, secret handling, canon authority, provenance, capability permissions, critical validation, or final publication approval. Conflicts and invalid combinations fail before a run starts.

Every run records the effective policy ID, version, content hash, contributing scopes, and authorized overrides. Policy edits are versioned, attributable, validated, diffable, and auditable. Existing runs retain their original policy snapshot for reproducibility.

Initial project configuration is portable and inspectable:

```text
projects/<project-id>/config/
  project.yaml
  style.yaml
  canon-policy.yaml
  character-policy.yaml
  character-arc-policy.yaml
  theme-policy.yaml
  source-promotion-policy.yaml
  beat-policy.yaml
  action-logistics-policy.yaml
  numeric-continuity-policy.yaml
  memory-policy.yaml
  retrieval-policy.yaml
  validation-policy.yaml
  review-policy.yaml
  provider-routing.yaml
  security-policy.yaml
  export-profile.yaml
```

Hosted production may store transactional policy metadata and active-version pointers in the database, while preserving exportable files and readable manifests.

Every setting must affect generation, validation, memory, retrieval, review, security, cost, provider routing, or export behavior. Decorative toggles and settings interpreted only by prompts are rejected.

### Genre, tone, style, and audience policy

Creative policy supplies ProseForge, JudgePanel, StoryEngine, and context packages with approved genre, subgenre, tone, avoided tendencies, POV, tense, dialogue style, narration style, audience, age rating, and content limits. These settings guide generation and evaluation but cannot override canon or approved scene facts.

Genre profiles such as `WesternStyleProfile` are versioned policy bundles with rules, examples, anti-patterns, dialogue settings, glossary references, validators, and approved exceptions. Projects may extend them through the normal policy resolver, but narrower settings cannot weaken canon, period evidence, meaning preservation, or character-voice constraints.

### Theme governance policy

`ThemeGovernancePolicy` defines required theme profiles, theme arc depth, chapter or scene theme-pressure requirements, anti-lecture rules, moral-choice requirements, and validator severity. It also defines when theme absence blocks drafting or becomes a review finding.

The default Western profile requires themes to be expressed through action, conflict, consequence, setting, silence, sacrifice, restraint, and character decisions rather than direct moral explanation. Policy may allow direct statement only when it is character-true, dramatically earned, and not a clean summary of the lesson.

### Period authenticity policy

`PeriodSettingPolicy` defines whether period controls are enabled, authenticity strictness, story date or date range, geographic scope, relevant cultures or communities, required research categories, and whether intentional anachronisms may be proposed for approval.

The policy distinguishes:

- **Historical validity:** whether a detail is supported for the applicable time, place, culture, and circumstances.
- **Genre and voice authenticity:** whether historically possible wording or behavior still conflicts with the project's approved narrative and dialogue style.
- **Fictional exception:** an intentional, reviewed departure from history that is valid only within its declared scope.

High-strictness projects block unsupported period-sensitive details. Lower strictness may produce review findings instead, but it cannot convert unsupported claims into approved facts. Uncertainty produces a `ResearchNeededRequest` with the question, affected text or plan, category, risk, and required evidence.

The broader `AuthenticityPolicy` configures historical, cultural, social, geographic, and environmental categories. It defines required pack coverage, source and review requirements, strictness, modernism rules, travel and survival assumptions, cultural-sensitivity gates, and intentional-fiction exceptions.

### Continuity lock policy

`ContinuityLockPolicy` enables domains and default lock levels for identity, animals, objects, resources, injuries, money, supplies, location, travel, timeline, motivation, personality, relationships, secrets, knowledge, documents, and story threads. It also defines which changes require deterministic validation, human review, or both.

Policy may strengthen locks for a project or book but cannot permit silent contradiction of approved canon or state. Strict locks block approval on mismatch. Guarded locks require an evidenced transition or approved explanation. Soft locks generate non-blocking findings unless another rule raises severity.

### Character governance policy

`CharacterGovernancePolicy` defines whether named characters require profiles, which profile depth each tier requires, whether unprofiled names block approval, which key profiles must exist before plotting, descriptor-only defaults, promotion requirements, and cast-clutter warning thresholds.

The default policy blocks unprofiled proper names, uses descriptors for incidental people, and requires approved full profiles before full-book plotting for main and major supporting characters. Projects may tighten naming rules but cannot approve a named character without a stable identity and minimum tier profile.

### Character arc and continuity policy

`CharacterArcContinuityPolicy` defines required antagonist profile sections, supporting-character function and exit rules, arc-plan depth by tier, accepted change-event categories, review requirements for durable development, and series carry-forward behavior.

Default rules require:

- A primary antagonist with approved goal, motive, code, threat style, escalation logic, speech constraints, and consistency rules before full plotting
- Every supporting character to retain an active approved function while recurring
- Durable personality, motivation, relationship, or capability changes to reference an approved change event
- A reviewed character evolution delta after each completed book for continuing important characters
- The next book to resolve its starting character state from the base profile plus all approved prior deltas

Policy may allow regression or apparent contradiction when explicitly planned and evidenced. It cannot permit unexplained drift or silent cross-book reset.

### Source promotion policy

`SourcePromotionPolicy` defines when an artifact becomes the canonical working source, what it supersedes, and which artifact roles are eligible for context, memory extraction, revision, export, or comparison. Approved edited versions become the default source for future work. Preserved originals remain available for audit but are excluded from normal context.

### Beat and action policy

`BeatPlanningPolicy` defines required fields by beat risk level, chapter stage, genre, and scene type. It blocks drafting from thin beats when plot, canon, or continuity could be invented by the model.

`ActionLogisticsPolicy` defines which scenes require action plans, what logistics must be specified, and which numeric, spatial, weapon, injury, movement, and post-scene state updates must be validated before approval.

`NumericContinuityPolicy` defines which number categories are strict, guarded, or soft, and which transition events may change them.

### Knowledge and memory policy

Knowledge policy defines permitted source classes, rejected or unreviewed exclusions, retrieval modes, and approval/provenance filters. Retrieval remains evidence selection, not truth.

Memory policy defines when summaries and state changes are proposed, which updates require review, and whether any deterministic low-risk update may be promoted under explicit policy. New characters, deaths, injuries, relationship changes, object transfers, secret revelations, timeline changes, and other canon-sensitive updates require review by default.

Context compression policy defines whether compression is enabled, which source classes may be compressed, which source classes are forbidden, whether retrieval fallback is required, maximum compression ratio, audit requirements, and benchmark gates before promotion. It defaults to disabled. It must not allow canonical sources, approvals, or final manuscript text to be replaced by compressed text.

### Skills and prompt packages

BookForge skills are versioned prompt, example, tool, schema, and test packages. They are not the workflow engine and cannot grant themselves permissions.

Each package declares its ID, version, allowed tasks, allowed and forbidden changes, required inputs, requested capabilities, validators, output contract, fixtures, and provenance. Imported packages remain disabled until schema validation, security review, regression tests, and project-owner approval succeed. Application services enforce all permissions even if package instructions request otherwise.

### Policy service boundary

The initial implementation should expose BookForge-owned policy interfaces through focused modules:

```text
bookforge/policies/
  resolver.py
  project_policy.py
  style_policy.py
  canon_policy.py
  authenticity_policy.py
  period_policy.py
  continuity_lock_policy.py
  character_governance_policy.py
  character_arc_policy.py
  theme_policy.py
  source_promotion_policy.py
  beat_policy.py
  action_logistics_policy.py
  numeric_continuity_policy.py
  memory_policy.py
  retrieval_policy.py
  validation_policy.py
  review_policy.py
  provider_policy.py
  security_policy.py
  export_policy.py
```

### Prompt registry and directory

Prompts are first-class versioned files, not long strings hidden inside Python modules. The initial repository layout should include:

```text
bookforge/prompts/
  drafting/
    scene-draft.v1.md
    chapter-draft.v1.md
  editing/
    humanize.v1.md
    line-edit.v1.md
    dialogue-voice.v1.md
  evaluation/
    canon-check.v1.md
    voice-drift.v1.md
    meaning-preservation.v1.md
  extraction/
    canon-extract.v1.md
    chapter-summary.v1.md
```

Every prompt declares machine-readable metadata:

```yaml
id: humanize
version: 1.0.0
task: manuscript_transformation
allowed_changes:
  - wording
  - rhythm
  - dialogue_naturalness
required_inputs:
  - source_artifact
  - approved_canon
  - style_guide
output_schema: transformed_text_with_change_report
validation_rules:
  - preserve_meaning
  - preserve_canon
failure_modes:
  - missing_context
  - unsupported_invention
```

The prompt loader validates metadata, renders typed inputs, records prompt ID and version on every model run, and fails when required inputs are missing. Prompt changes use regression fixtures and benchmark comparison before promotion.

A reviewed Western dialogue package may use:

```text
bookforge/skills/western-dialogue/
  skill.yaml
  prompt.md
  examples.md
  glossary.yaml
  blocked-modernisms.yaml
  tests.yaml
```

Its manifest declares allowed tasks and wording-level changes, forbidden canon and story-state changes, required period/style/character inputs, requested tools, and mandatory validators. Installation never activates the package automatically; it follows the skill-package review and promotion lifecycle.

### Provider boundary

BookForge owns a provider-neutral protocol for:

- Text generation and transformation
- Schema-constrained output
- Embeddings
- Usage, cost, and latency metadata
- Streaming where useful
- Cancellation and timeouts
- Normalized errors

Provider SDKs, LiteLLM, OpenRouter, local servers, or direct APIs may sit behind this boundary. Application modules do not depend directly on vendor payloads.

### Model routing

Routes are configured by task, project policy, privacy, context need, benchmark results, budget, and availability.

Typical strategy:

- Python only for deterministic checks
- Local or inexpensive models for extraction, summaries, classification, first-pass QA, and experiments
- Strong reasoning models for canon architecture and difficult consistency analysis
- Strong prose models for drafting, voice, emotional scenes, and final editorial assistance
- Long-context models for manuscript-wide analysis when compressed memory is insufficient

No provider or model is assigned permanently based on reputation. It must pass BookForge's evaluation set for the intended task.

### Jobs and queues

All substantial operations produce a run record even while execution is synchronous. Production workers add:

- Queued, leased, running, awaiting-input, completed, failed, cancelled, and expired states
- Idempotency keys
- Heartbeats and lease recovery
- Priority and concurrency controls
- Dependency and approval waits
- Bounded retry with backoff
- Cancellation without partial artifact promotion

### Cost controls

- Project, book, chapter, and stage budgets
- Maximum automatic attempts
- Provider and fallback allowlists
- Estimated cost before bulk runs
- Actual cost per accepted output
- Alerts and hard stops
- No hidden fallback to a more expensive provider

## 17. Data And Artifact Architecture

### Source of truth

- Versioned files remain portable, inspectable content artifacts.
- The relational database owns transactional metadata, workflow state, permissions, indexes, and queryable relationships in product phases.
- Neither layer may claim completion until coordinated persistence succeeds.
- Content hashes and manifests detect mutation and support reproducibility.

### Source promotion

`SourcePromotionPolicy` controls which approved artifact is the canonical working source for future context, revision, memory extraction, and export. Approved edited artifacts outrank rough originals. Rough originals remain preserved for provenance and audit, but they are not retrieved as working context after an approved edited version supersedes them unless an explicit recovery or comparison operation requests them.

Artifact source roles include:

- `preserved_original`
- `candidate_revision`
- `approved_revision`
- `canonical_working_source`
- `export_source`
- `superseded_source`

Promotion records the promoted artifact, parent artifact, superseded artifacts, approval record, content hash, and whether the artifact is usable for context, memory extraction, export, or comparison only.

For series work, the final edited book becomes the source for the next book through derived approved memory, not by dumping the whole prior manuscript into context:

```text
final edited book
-> approved summaries
-> character evolution deltas
-> unresolved threads
-> relationship, object, injury, resource, reputation, and consequence state
-> next-book constraints
```

### Core entities

- Workspace and user
- Project and series
- Book, act, chapter, scene, and beat
- Detailed beat, layered beat, beat completeness report, action scene plan, and gunfight plan
- Theme profile, theme arc, theme beat, theme pressure, theme expression, theme finding, and theme continuity record
- Research source, claim, and evidence
- Authenticity policy, authenticity pack, period research profile, historical fact, availability profile, and research-needed request
- Intentional-anachronism exception and anachronism finding
- Genre style profile, Western glossary entry, dialogue policy, style anti-pattern, and approved interiority exception
- Genre pack, genre-pack version, subgenre profile, prompt block, validation checklist, and genre-pack finding
- Western prime directive, prime-directive finding, and manuscript-level Western rollup report
- Canon entity, fact, relationship, timeline event, and change proposal
- Character profile, voice profile, reference rules, role profile, and appearance profile
- Character tier, motivation profile, mannerism profile, pressure behavior, incidental descriptor, and promotion request
- Character governance policy, plot-readiness report, unprofiled-name finding, and cast-clutter finding
- Antagonist profile, threat style, cruelty profile, supporting-character function, and exit condition
- Character arc plan, arc state, change event, evolution delta, series character memory, drift finding, and supporting-cast finding
- Character knowledge state, continuity state, relationship state, and validity interval
- Object profile, object state, resource state, inventory state, story event, and state transition
- Numeric lock, numeric state, number transition, group profile, and action logistics finding
- Locked detail, continuity-lock policy, continuity finding, and lock projection
- Location state, travel state, supply state, injury state, motivation state, and setup/payoff state
- Continuity rule, knowledge state, thread state, and relationship validity interval
- Plan and story thread
- Artifact and artifact dependency
- Source promotion record, canonical source role, canonical working source, and series source memory
- Prompt and prompt version
- Agent persona, persona version, persona capability map, persona prompt binding, persona run record, and persona evaluation fixture
- Policy definition, policy version, effective-policy snapshot, and authorized override
- Skill package, package version, capability request, and promotion decision
- Provider profile and model run
- Validation run and finding
- Capability definition, tool grant, notebook entry, and accepted-risk record
- Review, comment, revision request, and approval
- Workflow run, stage run, and event
- Export and publication package
- Budget and usage record

### Artifact requirements

Every artifact records:

- Stable ID, type, project, and hierarchy location
- Version and parent version
- Producing stage and run
- Input artifact, canon, research, prompt, provider, and model references
- Storage path or object key
- Content hash and size
- Created-by actor
- Validation and approval state
- Created and superseded timestamps

### Filesystem evolution

The proof and local workflow use project directories with Markdown, YAML, JSON, and JSONL. Hosted production may add object storage, but must retain exportable project bundles and readable manifests.

## 18. Lifecycle And State Model

### Artifact state

```text
draft -> validating -> needs_revision -> awaiting_review -> approved -> superseded
                    -> blocked
                    -> rejected
```

### Book state

```text
intake
-> research
-> canon_design
-> planning
-> calibration
-> drafting
-> editorial_review
-> final_review
-> publication_ready
-> published
-> archived
```

Transitions require explicit prerequisites. For example, drafting requires approved canon and plans; publication requires approved chapters and book-level checks.

### Failure and recovery

- Retryable infrastructure failures preserve stage inputs and resume safely.
- Invalid model output creates a failed attempt, not a malformed artifact.
- Partial writes remain temporary and are never promoted.
- Stale memory, index, or export state is visible and rebuildable.
- Manual intervention is available for blocked jobs.
- Recovery actions are audited.

## 19. Security, Privacy, And Trust Boundaries

- Validate project identifiers and all user-controlled paths.
- Enforce project scope at filesystem, database, cache, queue, retrieval, and object-storage layers.
- Separate tenant data before multi-user hosting.
- Restrict agent tools by stage and least privilege.
- Enforce capability registry permissions in code rather than trusting prompts or model behavior.
- Treat personas as advisory role lenses only; never allow persona text to grant tools, mutate state, approve artifacts, or bypass validators.
- Store secrets in environment or secret-management systems, never artifacts or logs.
- Redact secrets and sensitive manuscript content from operational error logs.
- Validate type, size, and structure of uploads.
- Scan archives and prevent path traversal during extraction.
- Preserve deletion, export, and retention controls for private manuscripts.
- Record approval and administrative actions in an audit log.
- Treat external sources and retrieved text as untrusted content, not executable instructions.
- Apply rate, concurrency, and budget limits at trust boundaries.
- Define provider data-retention policy per project before sending manuscript content externally.

## 20. Observability And Administration

Operators need visibility into:

- Run and stage status
- Queue depth, duration, retries, and failure categories
- Provider health and fallback use
- Token usage, cost, and accepted-output cost
- Validation pass rates and common findings
- Approval latency and revision cycles
- Retrieval coverage and missing-context failures
- Storage, index, and memory freshness
- Export failures and publication blockers
- Security and isolation events

Telemetry must reference IDs and safe metadata rather than exposing full manuscript content by default.

## 21. Evaluation And Quality Program

BookForge must evaluate models, prompts, retrievers, and pipeline changes against stable fixtures.

Context compressors are evaluated like other pipeline changes. They are optional infrastructure, not trusted intelligence. A compressor can be promoted only after compressed and uncompressed runs are compared on the same inputs, prompts, models, and policies.

### Benchmark cases

- Clean chapter
- Missing required beat
- Unsupported canon fact
- Character voice drift
- Timeline, location, injury, weapon, or object conflict
- AI-pattern-heavy prose
- Meaning-changing humanization
- Historical claim unsupported by approved evidence
- Date/place anachronism, unavailable technology, and period-language mismatch
- Western emotional over-explanation, abstract action, polished-modern dialogue, excessive dialect, and forced glossary usage
- Western prime directive rollup failure
- Antagonist inconsistency, purposeless supporting cast, unearned character change, and cross-book character reset
- Cross-project retrieval attempt
- Compression that drops or distorts canon-sensitive facts
- Truncated and malformed structured output
- Full-book setup/payoff and continuity cases

### Metrics

- Canon drift and unsupported fact count
- Required beat coverage
- Validator precision and false-positive rate where measurable
- Meaning preservation
- Voice and style reviewer scores
- Reader-experience rubric scores
- Output length without filler
- Revision count and unresolved issues
- Human acceptance and override rate
- Time and cost per accepted chapter/book
- Retrieval provenance coverage
- Compression token savings, latency change, fallback rate, and canon-preservation delta
- Failure and recovery rate

Default tests stay fast, offline, and deterministic. Model benchmarks are opt-in, record environment and model versions, and never silently update golden expectations.

Compression benchmarks must track canon violations, unsupported facts, style quality, token cost, latency, human review score, and reviewer override rate. Token savings alone never justify promotion.

### Product success measures

Initial success is quality and repeatability, not maximum volume. Once quality gates are stable, measure:

- Time from approved plan to approved chapter
- Time from manuscript import to approved transformation
- Percentage of chapters accepted without broad rewrite
- Canon defects found before publication
- Human review time per chapter
- Cost per approved chapter and book
- Sustainable weekly book throughput for the chosen quality tier

The legacy aspiration of five books per week is a capacity target to validate, not a requirement that may reduce editorial quality.

## 22. Capability Priority Matrix

### Phase 0 minimal contract cut

The first implementation cut is intentionally small:

- Project identity
- Artifact identity, version, lineage, and hash
- Canon profile basics
- Character profile basics
- Context package
- Prompt registry
- Policy resolver
- Capability registry
- Persona registry
- Validation finding
- Review approval
- Deterministic provider
- Markdown export

### Phase 0-1 forbidden work

Do not build these during Phase 0 or Phase 1 unless a later instruction explicitly expands scope:

- Browser UI
- FastAPI service
- PostgreSQL
- Vector database
- Graph database
- RAG pipeline
- External research automation
- Autonomous multi-agent workflows
- Model-provider marketplace
- EPUB/PDF export
- Full-book engine
- Full series memory
- Production workers, queues, auth, telemetry, backup, or billing

### Required foundation

- Project isolation and safe paths
- Typed schemas and explicit identity
- Entity, fact, and typed relationship contracts with canon lifecycle and temporal validity
- Tiered character-profile contracts with stable identity, voice, references, roles, and CanonCore/MemoryVault ownership boundaries
- Character-governance, incidental-descriptor, promotion, cast-clutter, and profile-before-plot contracts
- Antagonist, supporting-function, arc-state, change-event, evolution-delta, and series-character-memory contracts
- Continuity-relevant object, resource, inventory, event, transition, and prerequisite contracts
- Authenticity-policy, authenticity-pack, period-setting, historical-fact, availability, exception, and research-needed contracts
- Locked-detail, lock-level, lock-projection, continuity-policy, travel-state, and supply-state contracts
- Versioned Western style-profile, dialogue-policy, source-linked glossary, and style-finding contracts
- Western prime-directive configuration, context payload, rollup finding, and manuscript report contracts
- Artifact versioning, lineage, hashes, and trace
- Versioned prompt registry with metadata validation
- Typed PolicyCenter schemas, precedence, immutable floors, validation, versioning, and effective-policy snapshots
- AgentPersona, PersonaRegistry, PersonaCapabilityMap, PersonaPromptBinding, PersonaRunRecord, and persona fixture contracts
- Reviewed prompt and skill-package contracts that cannot grant workflow authority
- Capability registry with explicit tools, effects, gates, budgets, and retry limits
- Canon and style intake with approval
- Structured context builder
- Deterministic provider for tests
- Persona-bound deterministic tests for `western_prose_editor`, `continuity_auditor`, and `canon_editor`
- Stage orchestration and bounded retries
- Deterministic validation
- Diff, approval, and Markdown export
- Automated unit, integration, regression, and security tests

### Required for a useful local author product

- CLI over stable services
- Optional real provider routing
- Drafting and humanization
- Continuity and voice reports
- Character identity, reference, knowledge, relationship, and state checks
- Named-character, tier-depth, descriptor-only, promotion, plot-readiness, and cast-clutter checks
- Antagonist consistency, supporting-cast utility, earned-arc transition, and cross-book evolution checks
- Resource arithmetic, inventory transfer, object availability, and transition-prerequisite checks
- Period-lock, historical availability, anachronism, and genre-authenticity checks
- Cultural, environmental, travel, settlement, law/custom, and supply-authenticity checks
- Strict, guarded, and soft continuity-lock validation
- Behavior-first narration, physical grounding, dialogue directness, dialect moderation, and glossary-consistency checks for Western projects
- Targeted revision loop
- L1-L3 memory updates
- Review notebook and decision log
- Project knowledge base with structured and lexical lookup
- Model and prompt traceability
- CLI policy inspection, validation, diff, and controlled update commands
- Evaluation fixtures
- DOCX export
- Recovery and usage documentation

### Required for full-book quality

- Hierarchical planning and scene cards
- Sample chapter calibration
- Chapter summaries and sliding context
- Setup/payoff and unresolved-thread tracking
- Book-level continuity and reader-experience evaluation
- Manual final polish workflow
- Complete manuscript assembly

### Required for production platform

- FastAPI services and browser review workspace
- Artifact, timeline, relationship, conflict, and workflow visualizations
- PostgreSQL migrations and transactional metadata
- Durable workers and queue
- Authentication, authorization, and audit
- Comments, assignments, and chapter locking
- Operational telemetry, budgets, and provider administration
- Object storage or equivalent durable artifact storage
- Backup, restore, retention, and project export

### Required for advanced product

- ResearchCore
- Source-backed period research packs, historical-fact approval, availability profiles, and authenticity audits
- Controlled ingestion and research adapter boundaries
- pgvector-backed retrieval
- Series memory, relational story-state queries, and derived relationship graph
- Multi-book planning and cross-book validation
- EPUB, HTML, PDF, and publishing profiles
- Team analytics and portfolio operations

### Optional after demonstrated need

- Dedicated vector database
- LangGraph or Temporal
- MCP servers for controlled external integration
- Local GPU serving with vLLM
- Semantic diff enhancements
- Specialized graph database such as Neo4j; PostgreSQL plus an in-process projection may remain sufficient permanently
- Fine-tuned evaluators or models
- Plugin or integration ecosystem
- Multi-channel assistant integrations
- Sandboxed model-generated scripts beyond predefined export and analysis services

### Rejected as starting architecture

- One giant prompt
- Fully autonomous book generation
- Uncontrolled agent-to-agent conversations
- Personas as permission grants
- Skills as the workflow engine
- Global cross-project memory
- Random token chunking as the primary fiction structure
- Silent canon mutation
- Automatic approval
- Unlimited rewrite loops
- UI-owned business logic
- Database-only manuscript storage with no portable artifacts
- Microservices, Kubernetes, or distributed infrastructure before measured need
- Complex RAG before structured canon and context contracts
- Choosing models from hype instead of evaluation
- External frameworks owning canon, workflow, approvals, or publication state

## 23. Delivery Roadmap And Stop Gates

Each phase must deliver usable evidence, pass verification, document limitations, and receive project-owner approval before the next phase begins.

The roadmap index at `docs/info-plan/phase-roadmap-index.md` records which phases are implementation-ready. Only phases with an explicit implementation brief are authorized for coding. Phases listed here without a brief are future product direction, not current build scope.

### Phase 0: Product contracts

Deliver:

- Domain schemas, states, error taxonomy, and policy configuration
- Policy families, scope precedence, immutable safety floors, and effective-policy snapshot contracts
- AuthenticityPolicy, AuthenticityPack, PeriodSettingPolicy, HistoricalFact, availability-profile, authenticity-finding, and ResearchNeededRequest contracts
- ContinuityLockPolicy, LockedDetail, lock-level, lock-projection, TravelState, SupplyState, and ContinuityFinding contracts
- WesternStyleProfile, WesternDialoguePolicy, WesternGlossaryEntry, and WesternStyleFinding contracts
- CharacterGovernancePolicy, CharacterTier, IncidentalCharacterDescriptor, CharacterPromotionRequest, and PlotReadinessReport contracts
- CharacterArcContinuityPolicy, AntagonistProfile, SupportingCharacterFunction, CharacterArcState, CharacterChangeEvent, CharacterEvolutionDelta, and SeriesCharacterMemory contracts
- ThemeGovernancePolicy, ThemeProfile, ThemeArc, ThemeBeat, ThemePressure, ThemeExpression, ThemeFinding, ThemeLectureFinding, and ThemeUnderdevelopmentFinding contracts
- SourcePromotionPolicy, CanonicalSourceRole, DetailedBeat, LayeredBeatProfile, ActionScenePlan, GunfightPlan, NumericLock, NumericState, and NumberTransition contracts
- Initial schema modules for project, canon, chapter, artifact, context package, validation, review, and model run
- Entity, fact, relationship, character-profile, object-profile, resource-state, inventory-state, story-event, state-transition, knowledge-state, continuity-state, and thread-state schemas
- Source-promotion, detailed-beat, action-logistics, numeric-lock, group-profile, and canonical-working-source schemas
- Project path and artifact contracts
- Stage, provider, validator, approval, and export protocols
- Capability registry and enforceable permission contract
- AgentPersona, PersonaRegistry, PersonaCapabilityMap, PersonaPromptBinding, PersonaRunRecord, and persona evaluation fixture contracts
- Prompt directory, metadata schema, loader contract, and deterministic prompt fixtures
- Deterministic fixtures based on `Lone Star Reckoning`

The first implementation contracts should be represented explicitly:

```text
bookforge/schemas/
  project.py
  canon.py
  character.py
  character_governance.py
  character_arc.py
  theme.py
  object.py
  story_state.py
  historical.py
  authenticity.py
  continuity_lock.py
  style_profile.py
  source_promotion.py
  beat.py
  action_scene.py
  numeric_lock.py
  chapter.py
  artifact.py
  context_package.py
  policy.py
  validation.py
  review.py
  model_run.py
  persona.py
```

Gate:

- Contracts are internally consistent and tested.
- No interface or infrastructure layer bypasses them.

### Phase 1: Local proof engine

Deliver:

- One project, one approved bible/style set, one imported chapter, and one context package
- Approved protagonist, antagonist, and major-supporting profiles sufficient for the proof plot gate
- Approved antagonist goal/threat profile and supporting-character function records
- Validated file-backed project, style, canon, validation, review, provider, security, and export policies
- Deterministic or fixture-driven humanization of the imported chapter
- Meaning-preservation and canon-preservation checks
- Deterministic fixture for one continuity-relevant object and an impossible resource transition
- Approved fixture period pack for the proof story, including clearly synthetic allowed, blocked, and research-required entries
- Synthetic authenticity fixture covering travel, terrain, weather, settlement, law/custom, supply, and cultural-review requirements
- Strict, guarded, and soft continuity-lock fixtures
- Western style fixture with behavior-first, direct-action, dialogue, dialect-intensity, and glossary rules
- Persona-bound fixtures for `western_prose_editor`, `continuity_auditor`, and `canon_editor`
- Character-governance fixtures for an approved key cast, an unprofiled name, unnecessary background names, and descriptor promotion
- Character-arc fixtures for antagonist consistency, supporting-cast purpose, earned growth, regression, and series carry-forward
- Theme-governance fixtures for an approved theme profile, a missing-theme beat, a lectured theme, and violence without consequence
- Source-promotion fixture proving approved edited prose becomes the canonical working source and rough originals are excluded from normal context
- Beat-completeness fixture proving a thin plot-critical beat blocks drafting
- Numeric-lock fixture for ammunition and enemy-count contradictions
- QA report, diff, simulated approval, trace, and Markdown export
- Tests as the primary execution surface
- Optional second proof: expand one approved chapter summary into a constrained chapter artifact

Gate:

- Runs offline and deterministically.
- Wrong story/version, missing canon, path escape, blocking QA, and unapproved export all fail.
- The transformed chapter preserves plot, facts, order, POV, and required constraints.
- No CLI, API, UI, database, vector store, or external model service is required.

### Phase 2: Useful local engine

Deliver:

- Generalized project and chapter services
- Versioned artifacts and connected retry/revision flow
- Approved L1-L3 memory updates
- Better deterministic output and reviewer-friendly QA
- CLI wrapper
- CLI commands to show, validate, diff, and update settings through PolicyCenter services
- CLI character-governance checks for profile completeness, plot readiness, cast clutter, and promotion requests
- CLI arc-state, supporting-function, change-event, and evolution-delta review commands
- CLI source promotion, beat validation, action-plan validation, and numeric-lock inspection commands
- Reviewed installation and activation of local prompt or skill packages
- Persona-aware model-run metadata and trace inspection
- Reviewed Western dialogue skill fixture with no-invention and character-voice constraints
- Constrained chapter generation from an approved plan or summary
- Review notebook and project knowledge-base lookup
- Manual review and approval of extracted object, inventory, resource, and continuity-state updates
- Lock projection rebuild, stale-lock detection, and reviewed lock-level changes
- Context-compression policy placeholder and no-op service boundary, with compression disabled by default

Gate:

- The CLI contains no business logic.
- A real local author can operate the complete artifact chain.
- Compression cannot be required for local operation, and no compressor may replace canonical source material.

### Phase 3: Model-assisted author workflow

Deliver:

- Optional local and cloud provider adapters
- Real drafting and humanization
- Report-only continuity, voice, and style evaluation
- Prompt/model trace and budget controls
- Benchmark suite and DOCX export
- Predefined restricted analysis and export services
- Event extraction that proposes evidenced state transitions without automatically promoting them
- Model-assisted period-authenticity evaluation that can return research-needed requests
- Model-assisted cultural, environmental, travel, settlement, and supply authenticity findings with evidence and human-review requirements
- Model-assisted Western style evaluation for behavioral emotion, reader inference, dialogue, dialect, and vocabulary
- Optional context-compression experiment for logs, tool output, validator reports, QA reports, and retrieval previews

Gate:

- Offline deterministic tests still pass.
- Model paths meet benchmark thresholds.
- Unsafe changes remain blocked.
- Compressed and uncompressed benchmark runs show no canon-preservation or review-quality regression before any compressor is promoted.

### Phase 4: Full-book engine

Deliver:

- Hierarchical outlines, scene cards, emotional beats, and setup/payoff tracking
- Full-book plotting from approved motivation maps, conflict matrices, relationship tensions, pressure behavior, and character arcs
- Full-book plotting from approved theme profiles, theme arcs, and chapter-level theme pressure
- Detailed beats for every plot-critical chapter and approved action plans for fights, chases, and gunfights
- Book-level antagonist consistency, supporting-cast utility, and earned-character-development review
- Book-level theme presence, moral-choice, violence-consequence, theme-lecture, and theme-continuity review
- Reviewed character evolution deltas produced at book completion
- Multi-chapter orchestration and sliding context
- Chapter approval and memory consolidation
- Book-level validation, assembly, and manual final polish
- Cross-chapter resource, inventory, injury, location, knowledge, and prerequisite validation
- Cross-chapter continuity-lock validation for identity, money, supplies, travel, motivations, relationships, secrets, and story threads
- Cross-chapter numeric-lock validation for enemies, ammunition, money, distance, days, horses, wagons, supplies, documents, and people present
- Full-book period-lock validation across technology, material culture, institutions, travel, and language
- Full-book Western style-drift and glossary-consistency review where the profile is active
- Western prime directive rollup review before chapter, batch, book, or publication approval where the Western profile is active

Gate:

- A complete book can be produced or transformed without hidden state or unbounded context.
- All chapters and publication checks are approved.

### Phase 5: Review application

Deliver:

- FastAPI service layer
- Browser project, planning, chapter, diff, findings, approval, and export views
- Browser policy views for project/book settings, style, canon, memory, knowledge, skills/prompts, providers, validation, review, security, budgets, and export profiles
- Run status and recovery controls
- Persona and model-run metadata display for reviewer traceability
- Read-only timeline, relationship, setup/payoff, and canon-conflict visualizations

Gate:

- UI actions map to existing application services.
- Artifacts remain portable and authoritative content records.

### Phase 6: Production operations

Deliver:

- PostgreSQL, migrations, relationship/state tables, durable workers, authentication, authorization, audit, object storage, telemetry, backup, and restore
- Team review, comments, assignments, and locking
- Hardened sandbox worker where predefined services cannot satisfy approved analysis or export requirements

Gate:

- Isolation and approval rules survive migration.
- Failure recovery and operational runbooks are tested.

### Phase 7: Retrieval, research, and series

Deliver:

- ResearchCore and evidence workflows
- Source snapshots, claim extraction, historical-fact review, period-pack maintenance, and research-needed resolution
- pgvector narrative/style/research retrieval
- Series memory, relational story-state queries, derived graph projection, and cross-book validation
- Cross-book character evolution, reputation, consequence, obligation, and relationship carry-forward
- Series-level source promotion from final edited books into approved summaries, state, and source memory
- Cross-book numeric, resource, action-consequence, and canonical-working-source continuity
- Evaluated ingestion, retrieval, and research adapters behind BookForge contracts
- Advanced export profiles

Gate:

- Retrieval quality is benchmarked.
- Research claims remain attributable.
- Series state is reproducible from approved books and canon changes.
- Graph projections are rebuildable from approved relational records and cannot mutate canon directly.
- A specialized graph database is adopted only if traversal benchmarks and product queries demonstrate a concrete need.

### Phase 8: Scale and ecosystem

Consider only after usage proves demand:

- Dedicated search or workflow infrastructure
- External tool integrations through controlled APIs or MCP
- Multi-channel assistant interfaces
- Specialized local serving
- Fine-tuning
- Portfolio analytics and integration ecosystem

## 24. Verification And Release Discipline

At every phase:

- Write failing tests before behavior changes.
- Run targeted tests, full tests, static checks, and formatting checks.
- Run container/runtime verification when those surfaces exist.
- Confirm default tests require no external model service.
- Verify the representative end-to-end artifact chain.
- Inspect diffs and generated artifacts.
- Update usage, architecture, limitations, and recovery documentation.
- Keep package, runtime, documentation, and tag versions synchronized.
- Confirm ignored-file rules do not exclude required tests or docs.
- Report completed version, files changed, tests run, artifacts produced, preserved rules, known limitations, and next phase.
- Stop for project-owner approval before crossing a phase gate.

## 25. Acceptance Scenarios

### Transformation-first proof

- Import one existing chapter while preserving its structural boundaries.
- Load the approved canon and style guide for the correct project and version.
- Build and persist a context package with exact source references.
- Humanize the chapter in no-invention mode.
- Detect a seeded meaning change and unsupported canon fact.
- Produce a targeted corrected version without changing clean regions.
- Save validation results, diff, approval record, trace, and Markdown export.
- Record persona, prompt, capability, model, context package, and validator metadata for the transformation run.
- Complete the workflow offline through tests without CLI, API, UI, database, RAG, or model service.

### Grounded chapter proof

Using `Lone Star Reckoning`, bible `version-1`, and Chapter 8:

- Retrieve Darin Mayweather, Deadeye Harlan, Act 2, the Chapter 8 plan, adjacent summaries, and Western rules.
- Retrieve only applicable character profiles, voice and reference rules, relationships, knowledge boundaries, and current states for the scene.
- Reject wrong-story or wrong-version chunks.
- Generate no chapter when required canon is absent.
- Detect a seeded invented name, forbidden reference, wrong age, voice drift, knowledge leak, unsupported character, or changed injury.
- Confirm the selected persona can only use capabilities granted by the active stage.
- Block an unprofiled proper name, replace an unnecessary background name with an approved descriptor, and approve a justified descriptor-to-character promotion with lineage preserved.
- Refuse full-book plotting when a required key profile is missing, then pass after approving the profile and rebuilding the motivation and conflict maps.
- Refuse full-book plotting when required primary themes, theme statements, theme arcs, or forbidden lecture rules are missing.
- Attach `justice_vs_revenge` or equivalent synthetic theme pressure to a scene beat and confirm context includes only the active theme constraints.
- Reject a paragraph that directly explains the moral lesson instead of dramatizing it through action, choice, cost, or consequence.
- Flag a violent scene with no visible consequence when violence-and-consequence is an active theme, then pass after adding an approved consequence beat or carry-forward state.
- Verify a minor named character needs only the configured lightweight profile while recurring side and major characters require deeper profiles.
- Reject an antagonist reversal, cruelty spike, panic response, or monologue that lacks support from the approved antagonist profile and arc state.
- Flag a recurring supporting character whose function ended, then pass after retiring the character or approving a new function and exit condition.
- Reject a seeded courage, trust, or personality jump without an approved pressure or change event; accept the same development after the event is reviewed.
- Produce an approved Book 1 character evolution delta, construct the Book 2 starting state from it, and reject an attempted reset of scars, relationships, reputation, beliefs, or unresolved obligations.
- Promote an approved edited chapter to `canonical_working_source`, preserve the rough original, and prove future context excludes the rough source unless comparison is explicitly requested.
- Reject a draft request from a plot-critical thin beat, then pass after adding location, characters present, goal, conflict, reveal, state change, forbidden events, and next-beat connection.
- Validate a layered slow-burn Western beat sequence with physical task, environmental pressure, character behavior, social contact, plot pressure, visual threat, and restrained reaction.
- Require an approved gunfight plan before drafting a fight scene; reject extra enemies, impossible movement, unsupported reloads, wrong shot order, and shots beyond available ammunition.
- Lock a gang count at ten, reject a later twenty-man claim without arrival, reveal, or correction event, and pass after an approved numeric transition.
- Load an approved 1849 California period fixture and reject seeded future technology, unsupported ammunition behavior, and modern-feeling language according to its synthetic test rules.
- Reject a seeded impossible travel duration and unsupported town, law, supply, weather, or terrain detail according to the synthetic authenticity fixture.
- Route a seeded cultural-representation risk to evidence-backed human review rather than automatically approving or rejecting the portrayal.
- Rewrite a seeded emotional explanation into observable behavior without changing intended emotion, event, POV, canon, or character state.
- Detect redundant explanation after demonstrated behavior, overly polished dialogue, caricature dialect, purple prose, and forced glossary terminology.
- Permit an approved interior thought where the scene requires clarity, proving the profile does not ban all interiority.
- Apply character voice, Western style, and period accuracy independently and report which layer each violation belongs to.
- Run the Western prime directive validator and confirm it summarizes consistency, physicality, era accuracy, and character-driven findings without hiding the underlying issue IDs.
- Return `research_needed` instead of inventing when a period-sensitive detail is absent or disputed in the active research pack.
- Approve one scoped intentional anachronism and confirm it does not disable unrelated period checks.
- Start a revolver at three rounds, approve one fired-shot transition, confirm two remain, and reject a later three-round claim without reload or ammunition-acquisition evidence.
- Verify strict identity and resource locks block unexplained changes, guarded injury or motivation locks require an evidenced transition, and soft mood or clothing locks produce configurable review findings.
- Rebuild locked continuity from authoritative records and prove editing the projection cannot mutate canon or story state.
- Reject use of an unavailable, transferred, destroyed, empty, or wrong-location object unless an approved intervening transition makes the action possible.
- Revise only the reported issue.
- Preserve all versions and show the diff.
- Require approval before export.

### Existing manuscript transformation

- Import a structured manuscript without flattening chapters.
- Extract proposed canon and require approval.
- Humanize one chapter without changing plot or facts.
- Detect a seeded meaning change.
- Review and approve the corrected version.
- Export matching approved content.

### Full-book production

- Approve story bible, outline, and sample chapter.
- Produce all chapters with approved context and memory updates.
- Detect an unresolved setup, duplicate passage, timeline conflict, and voice drift.
- Resolve or accept each finding with audit records.
- Pass publication checks and export the complete manuscript.

### Project isolation

- Run two projects with overlapping names and similar content.
- Confirm files, canon, database records, caches, retrieval results, and prompts never cross project boundaries.

### Policy resolution and enforcement

- Resolve system, workspace, project, series, book, and authorized run settings into one validated effective policy.
- Record the exact policy versions and hash on generated artifacts and model runs.
- Reject an invalid setting combination before execution.
- Attempt to disable project isolation, canon approval, critical validation, capability enforcement, and final publication approval from a narrower scope; reject and audit every attempt.
- Change a style, provider, budget, or review setting through the service layer and confirm CLI, worker, API, and later UI surfaces observe the same behavior.
- Import a skill package that requests canon mutation or undeclared tools; keep it disabled and report the violated policy.

### Recovery

- Interrupt generation, validation, memory update, and export at controlled points.
- Resume safely without promoting partial artifacts or losing prior approved versions.

### Intelligence-layer authority

- Grant an assistant the `humanize_chapter` capability and verify only its declared tools are available.
- Attempt canon mutation, approval, cross-project access, unrestricted execution, and publication from that capability; reject and audit each attempt.
- Rebuild a visualization and retrieval index from approved artifacts without changing canon or workflow state.
- Supersede a notebook decision and preserve both entries with attribution and lineage.

## 26. Full-Product Definition Of Done

BookForge reaches full-product readiness when:

- Authors can create or transform complete books through supported workflows.
- Canon, research, narrative state, and series memory remain explicit and reproducible.
- Models can be changed without rewriting product logic.
- External intelligence, research, retrieval, and assistant frameworks can be replaced without changing BookForge authority or domain contracts.
- Every model-assisted output has provenance, validation, lineage, and review state.
- Reviewers can understand what changed, why it changed, and what risks remain.
- Critical failures block approval and publication.
- Complete books pass chapter-level and book-level quality gates.
- Publication artifacts are generated from approved versions only.
- Local single-user and hosted team modes use the same application contracts.
- Security, isolation, recovery, backup, retention, audit, budgets, and observability are tested.
- Benchmark results support model, prompt, retrieval, and scaling decisions.
- The system improves throughput without making quality, canon integrity, or human accountability optional.

## 27. Source Interpretation

The documents under `docs/info-plan/old-plan/` and `docs/info-plan/superpowers/` remain unchanged as provenance. Their strongest durable ideas are incorporated here:

- Local-first, engine-first delivery
- Explicit story and bible identity
- Strict project isolation
- Semantic fiction-aware chunking
- Structured context packages
- Layered trace, summary, and story-state memory
- Deterministic offline fallbacks
- Report-only continuity review
- Diff and approval before export
- Editorial beat, voice, and manual-polish practices
- Benchmarks before model or infrastructure commitments
- Phase stop gates and release verification

Legacy implementation history, stale versions, duplicate plans, transcript narration, and technology suggestions that conflict with this blueprint are not authoritative. Before adopting any external library or service, verify its current official documentation and evaluate it against BookForge's internal contracts.

External ecosystem candidates are tracked in `docs/references/ecosystem-evaluation.md`. Inclusion there means "evaluate as a reference or adapter," not "adopt as a dependency."
