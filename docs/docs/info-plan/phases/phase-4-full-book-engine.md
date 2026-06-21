# BookForge Phase 4 Full-Book Engine Brief

**Status:** implementation brief  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Scope:** local full-book planning, orchestration, validation, assembly, and final-polish workflow over approved Phase 0-3 services

## Rule

Phase 4 turns the local chapter engine into a controlled full-book engine. It may coordinate multiple chapters, book-level plans, scene cards, theme pressure, setup/payoff, sliding context, book-level checks, and complete manuscript assembly.

Phase 4 must not make the system autonomous. Full-book outputs remain candidate artifacts until reviewed and approved. Models may assist only through Phase 3 provider, policy, budget, benchmark, trace, and validation gates. Services own state and workflow authority. Humans remain the approval authority for chapters, book-level plans, memory consolidation, final polish, and publication readiness.

Full-book behavior must stay local and deterministic by default. It must work without API, browser UI, database infrastructure, worker queues, vector search, graph search, hosted collaboration, or production deployment.

## Scope Clarification

This brief defines the authorized Phase 4 implementation scope after Phase 3 acceptance. It does not authorize Phase 5 review application work or Phase 6 production operations.

Phase 4 may add service-level book orchestration and local files. It must not add FastAPI, browser UI, PostgreSQL, object storage, background workers, authentication, billing, tenancy, RAG/vector/graph retrieval, unrestricted research automation, series-level memory, or production deployment.

Phase 5 remains unauthorized until Phase 4 passes and the project owner authorizes the next implementation brief.

## Required Work

- Hierarchical book outline service for acts, chapters, plot-critical chapters, scene cards, emotional beats, setup/payoff records, unresolved threads, and chapter dependencies.
- Plot-readiness gate requiring approved motivation maps, conflict matrices, relationship tensions, pressure behavior, character arcs, antagonist profile, supporting-cast purpose, and theme profile before full-book plotting.
- Theme planning service for primary themes, secondary themes, theme statements, theme arcs, chapter-level theme pressure, forbidden lecture behavior, moral-choice pressure, and violence-consequence carry-forward.
- Scene-card validation for location, characters present, goal, conflict, reveal, state change, forbidden events, and next-beat connection.
- Plot-critical beat validation that rejects thin beats before drafting and requires enough grounding for action, conflict, continuity, and next-beat flow.
- Action-plan gate for fights, chases, gunfights, and complex logistics before drafting affected chapters.
- Multi-chapter orchestration service that builds chapter work batches from approved outline data and records deterministic execution state without hidden context.
- Sliding-context service that builds bounded context from approved canon, approved summaries, active locks, chapter dependencies, unresolved threads, setup/payoff records, style profile, theme pressure, and current story state.
- Chapter approval workflow that promotes only approved chapter versions into book assembly and memory consolidation inputs.
- Memory consolidation service that summarizes approved chapter consequences into reviewed book-level memory proposals without auto-promotion.
- Book-level continuity validation for identity, locations, injuries, relationships, motivations, secrets, knowledge boundaries, object state, inventory, resources, prerequisite transitions, setup/payoff, and unresolved threads.
- Book-level numeric-lock validation for enemies, ammunition, money, distance, days, horses, wagons, supplies, documents, and people present.
- Period-lock validation across technology, material culture, institutions, travel, supply, law/custom, language, and approved intentional exceptions.
- Book-level character review for antagonist consistency, supporting-cast utility, earned character development, reviewed evolution deltas, and invalid personality resets.
- Book-level theme review for theme presence, moral choice, dramatized cost, violence consequence, theme lecture risk, and theme continuity.
- Full-book Western review for style drift, glossary consistency, prime-directive rollup, dialogue moderation, behavioral emotion, reader inference, vocabulary modernism, and dialect overuse.
- Complete manuscript assembly service that accepts approved chapters only and preserves chapter order, artifact lineage, hashes, approval records, and trace references.
- Manual final-polish workflow that records polish findings, approved final changes, superseded chapter versions, and publication-readiness decision.

## Suggested Module Boundaries

Keep full-book behavior in services. CLI may expose commands later, but command handlers must remain thin wrappers over services.

```text
bookforge/services/
  book_outline_service.py
  plot_readiness_service.py
  theme_planning_service.py
  scene_card_service.py
  book_orchestration_service.py
  sliding_context_service.py
  book_memory_service.py
  book_validation_service.py
  manuscript_assembly_service.py
  final_polish_service.py

bookforge/cli/
  app.py
```

These names are guidance, not mandatory filenames. Use existing local service patterns if a better shape emerges.

## Required Tests

- Full-book plotting refuses missing main-character, antagonist, major supporting, recurring-side, motivation-map, conflict-matrix, relationship-tension, pressure-behavior, character-arc, supporting-function, or theme-profile inputs.
- Full-book plotting passes after required approved profiles, maps, theme arcs, and conflict inputs are provided.
- Theme planning rejects missing primary themes, theme statements, theme arcs, forbidden lecture rules, chapter pressure, moral-choice pressure, or violence-consequence carry-forward.
- Scene cards reject missing location, characters present, goal, conflict, reveal, state change, forbidden events, or next-beat connection.
- Plot-critical thin beats cannot be used for drafting until grounded enough for the configured chapter role.
- Fight, chase, and gunfight chapters require approved action plans before drafting.
- Gunfight validation rejects extra enemies, impossible movement, unsupported reloads, wrong shot order, shots beyond available ammunition, and unsupported injury results.
- Multi-chapter orchestration builds deterministic chapter batches from approved outline data and records resumable execution state.
- Sliding context includes only approved active canon, summaries, locks, dependencies, unresolved threads, setup/payoff records, style rules, theme pressure, and story state.
- Sliding context rejects wrong project, wrong book version, unapproved artifacts, stale summaries, and hidden unbounded context.
- Chapter approval promotes only approved chapter versions into assembly and memory consolidation.
- Memory consolidation emits reviewed proposals only and cannot auto-promote memory, locks, canon, or state.
- Book-level continuity checks detect cross-chapter identity drift, injury resets, location jumps, relationship resets, knowledge leaks, missing prerequisites, unresolved setup/payoff, and unsupported object or inventory state.
- Numeric-lock checks reject unsupported changes to enemies, ammunition, money, distance, days, horses, wagons, supplies, documents, and people present.
- Period-lock checks reject seeded future technology, unsupported material culture, unsupported travel behavior, unsupported law/custom, unsupported supply behavior, and modern-feeling language.
- Character review rejects unsupported antagonist reversals, cruelty spikes, panic responses, monologues, cast clutter, completed supporting functions with no exit or new function, and unearned personality jumps.
- Character evolution deltas are produced only from approved book completion data and remain reviewed proposals until approved.
- Theme review flags absent theme pressure, direct moral lectures, violence without consequence, missing moral choice, and theme continuity drops.
- Western rollup review detects style drift, glossary inconsistency, behavioral-emotion violations, reader-inference violations, dialect overuse, vocabulary modernism, and dialogue drift.
- Manuscript assembly rejects unapproved chapters, wrong-order chapters, missing chapter approvals, missing hashes, missing lineage, and stale source versions.
- Manual final polish records findings, final approved changes, superseded versions, and publication-readiness decision without bypassing validation.
- Existing offline deterministic tests still pass with model features disabled.

## Must Not Build In Phase 4

- FastAPI service.
- Browser review application.
- PostgreSQL, production migrations, object storage, background workers, queues, or production deployment.
- Vector store, graph store, RAG service, or full retrieval platform.
- Unrestricted external research automation.
- Series-level memory or cross-book production engine.
- Authentication, authorization, billing, tenancy, marketplace, hosted collaboration, or comments/assignments.
- Required Headroom, LiteLLM middleware, MCP compression adapter, or required compressor path.
- Model autonomy for approval, publication readiness, canon mutation, memory promotion, lock mutation, policy weakening, or validator bypass.
- EPUB/PDF export unless a later brief explicitly authorizes it.

## Acceptance

Phase 4 is accepted when BookForge can locally produce or transform a complete book through approved full-book planning, chapter orchestration, bounded sliding context, chapter approval, memory consolidation proposals, book-level validation, approved manuscript assembly, and manual final-polish workflow.

The engine must prove it has no hidden state or unbounded context. All chapters and publication checks must require approval. Unsafe model or orchestration output must remain blocked or reported. Existing deterministic offline tests must pass.

## Next Phase Rule

After Phase 4 passes and the project owner authorizes expansion, create:

```text
docs/info-plan/phases/phase-5-review-application.md
```

Do not implement Phase 5 behavior from this brief.
