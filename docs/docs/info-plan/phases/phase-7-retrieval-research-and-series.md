# BookForge Phase 7 Retrieval, Research, And Series Brief

**Status:** accepted implementation
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13
**Scope:** retrieval, research, and series-state foundation for the accepted Phase 0-6 system

## Rule

Phase 7 adds retrieval, attributable research, and cross-book series intelligence around the accepted BookForge service model. It may add source snapshots, claim extraction, period-pack maintenance, research-needed resolution, evaluated retrieval adapters, relational story-state queries, derived graph projections, series memory, cross-book validation, and advanced export profiles.

Phase 7 must preserve all prior authority boundaries. Retrieval output, research findings, graph projections, and series summaries are advisory or derived records until a human-approved service promotes them into canon, policy, memory, or publication state.

Approved books, canon records, policy snapshots, accepted risks, review decisions, and artifact lineage remain the authoritative source. Retrieval indexes, graph projections, research notes, and period packs must be rebuildable or traceable from approved records and source snapshots.

## Scope Clarification

This brief defines the authorized Phase 7 implementation scope after Phase 6 acceptance. It does not authorize Phase 8 scale/ecosystem work.

Phase 7 may add:

- ResearchCore records for sources, snapshots, claims, citations, research tasks, source evaluations, and research decisions.
- Source snapshot storage that preserves hashes, timestamps, citation metadata, extraction metadata, and project/series scope.
- Claim extraction and historical-fact review services that keep every claim attributable to source snapshots.
- Period-pack maintenance for approved era, setting, language, technology, social, travel, weapon, and occupation constraints.
- Research-needed resolution workflow for validator findings or author/editor questions.
- Evaluated retrieval adapters for narrative, style, research, memory, and series-state lookup behind BookForge contracts.
- pgvector or equivalent local vector retrieval when tests prove it improves benchmarked retrieval quality.
- Series memory and cross-book approved-summary records derived from final edited books and approved canon changes.
- Relational story-state queries for characters, locations, resources, obligations, consequences, reputation, relationships, and unresolved arcs.
- Derived graph projection service that can rebuild graph records from approved relational records and cannot mutate canon directly.
- Cross-book continuity validation for numeric, resource, action-consequence, relationship, and canonical working-source continuity.
- Advanced export profiles for research packs, citation bundles, series bibles, continuity reports, and editor handoff packages.

Phase 7 must not add:

- Phase 8 external integration ecosystem, MCP integrations, marketplace workflows, portfolio analytics, fine-tuning, or hosted multi-tenant scale features.
- Graph database adoption unless traversal benchmarks and product queries demonstrate a concrete need beyond relational plus derived projections.
- Retrieval-generated canon, auto-approved research decisions, auto-promoted series memory, or model-owned publication readiness.
- Unattributed research claims, unverifiable source summaries, mutable source snapshots, or citation-free historical assertions.
- New external network research behavior in deterministic tests.
- Policy weakening, approval bypass, audit deletion, lock bypass, publication-gate bypass, or validator bypass.

## Required Work

1. ResearchCore schemas for source records, snapshots, claims, citations, research tasks, source evaluations, period packs, retrieval queries, retrieval results, series memory records, graph projection records, and advanced export profiles.
2. Source snapshot service that stores immutable source payloads or excerpts with hashes, citation metadata, extraction metadata, timestamps, and project/series scope.
3. Claim extraction service that converts approved source snapshots into attributable claims with confidence, topic, location, era, source pointer, and citation detail.
4. Historical-fact review service that compares manuscript or outline claims against approved claims and records unresolved, contradicted, unsupported, and accepted findings.
5. Period-pack maintenance service for era/setting constraints and approved updates from reviewed sources.
6. Research-needed resolution service that turns validator or reviewer questions into scoped research tasks and closes them only with attributable decisions.
7. Retrieval adapter contracts for narrative, style, research, memory, and series-state lookup with deterministic local adapters.
8. Retrieval benchmark service that evaluates precision, recall, attribution coverage, stale-index detection, and approved-source isolation.
9. Vector retrieval adapter behind the retrieval contract, optional by configuration and tested through deterministic fixtures rather than external services.
10. Series memory service that derives summaries and state only from final edited books, approved canon changes, and approved research decisions.
11. Relational story-state query service for cross-book characters, locations, resources, obligations, consequences, reputation, relationships, and unresolved arcs.
12. Derived graph projection service that rebuilds graph records from approved relational state and blocks direct canon mutation.
13. Cross-book continuity validation for numeric/resource continuity, canonical working source continuity, action-consequence continuity, and relationship/reputation carry-forward.
14. Series-level source promotion service that promotes final edited book facts into approved summaries, source memory, and series state only after human approval.
15. Advanced export profile service for research packs, citation bundles, series bibles, continuity reports, and editor handoff packages.
16. API/service boundary additions for research, retrieval, and series workflows without moving business rules into route handlers.
17. Phase 7 acceptance cleanup proving retrieval quality is benchmarked, research claims remain attributable, series state is reproducible, graph projections are rebuildable, and existing deterministic offline tests pass.

## Suggested Module Boundaries

Keep retrieval and research authority in services. Indexes, adapters, graph projections, and vector stores are derived infrastructure around approved records.

```text
bookforge/research/
  core.py
  snapshots.py
  claims.py
  fact_review.py
  period_packs.py
  tasks.py

bookforge/retrieval/
  adapters.py
  benchmarks.py
  vector.py

bookforge/series/
  memory.py
  story_state.py
  graph_projection.py
  continuity.py
  source_promotion.py

bookforge/publishing/
  advanced_exports.py
```

These names are guidance, not mandatory filenames. Use existing local patterns where they fit better.

## Required Tests

- ResearchCore schemas reject unattributed claims, mutable source snapshots, and cross-project/series scope leaks.
- Source snapshots preserve content hash, citation metadata, extraction metadata, timestamp, project ID, and optional series ID.
- Claim extraction produces claims that retain source snapshot pointers and citation detail.
- Historical-fact review distinguishes supported, contradicted, unresolved, unsupported, and accepted findings.
- Period-pack updates require reviewed sources and never weaken policy without approval.
- Research-needed tasks close only with attributable decisions or explicit human deferral.
- Retrieval adapters preserve approved-source isolation and return citation/source metadata with every research result.
- Retrieval benchmarks measure precision, recall, attribution coverage, stale-index detection, and isolation failures.
- Vector retrieval remains optional by configuration and deterministic in tests.
- Series memory is reproducible from final edited books, approved canon changes, and approved research decisions.
- Relational story-state queries preserve cross-book character evolution, reputation, consequence, obligation, resource, relationship, and unresolved-arc state.
- Graph projections rebuild from approved relational records and cannot mutate canon directly.
- Cross-book validation catches numeric, resource, action-consequence, relationship, reputation, and canonical working-source continuity errors.
- Series source promotion requires human approval and records lineage from final edited books to approved summaries/source memory.
- Advanced exports preserve citations, source hashes, series-state lineage, continuity findings, and reviewer decisions.
- Existing offline deterministic tests still pass with external model access disabled.

## Must Not Build In Phase 7

- Phase 8 external ecosystem integrations, marketplace workflows, hosted multi-tenant scale features, portfolio analytics, fine-tuning, or external MCP tools.
- Specialized graph database adoption without benchmark evidence and product-query need.
- Autonomous canon mutation, autonomous publication readiness, auto-approved research decisions, auto-promoted series memory, or model-owned approval.
- Unattributed historical assertions, mutable source snapshots, citation-free research findings, or unverifiable source summaries.
- Network-dependent tests or external research services as required test infrastructure.

## Acceptance

Phase 7 is accepted when BookForge can run attributable research workflows, evaluated retrieval, and reproducible series-state queries while preserving all Phase 0-6 authority boundaries.

Retrieval quality must be benchmarked. Research claims must remain attributable. Series state must be reproducible from approved books, canon changes, and research decisions. Graph projections must be rebuildable from approved relational records and unable to mutate canon directly.

Existing deterministic offline tests must still pass with external model access disabled.

## Acceptance Result

Phase 7 is accepted as the retrieval, research, and series-state foundation.

Implemented artifacts include ResearchCore schemas, immutable source snapshots, attributable claim extraction, historical-fact review, period-pack maintenance, research-needed task resolution, retrieval adapter contracts, retrieval benchmarks, optional deterministic vector retrieval, series memory, relational story-state queries, derived graph projections, cross-book continuity validation, series-level source promotion, advanced export profiles, and API/service boundary additions.

The accepted scope remains advisory and derived around the Phase 0-6 service model. Phase 7 does not authorize Phase 8 scale/ecosystem work, external integration marketplace behavior, fine-tuning, hosted multi-tenant ecosystem features, autonomous canon mutation, auto-approved research decisions, or graph database adoption without benchmark evidence.

## Next Phase Rule

After Phase 7 passes and the project owner authorizes expansion, create:

```text
docs/info-plan/phases/phase-8-scale-and-ecosystem.md
```

Do not implement Phase 8 behavior from this brief.
