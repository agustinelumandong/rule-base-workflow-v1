# BookForge Phase 2 Useful Local Engine Brief

**Status:** implementation brief  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Scope:** useful local author engine over Phase 0/1 contracts, not a hosted product

## Rule

Phase 2 turns the deterministic Phase 1 proof into a real local workflow a single author can operate. It must generalize project, chapter, artifact, revision, QA, memory, trace, lock, policy, and skill-package behavior while keeping the implementation local and review-gated.

CLI is allowed in Phase 2, but only as a wrapper over stable application services. The CLI must not contain pipeline rules, validation logic, policy interpretation, artifact mutation rules, memory promotion rules, or retry/revision business logic.

By default Phase 2 remains deterministic and offline. Real provider routing, hosted APIs, browser UI, database persistence, vector retrieval, graph retrieval, workers, production operations, and external research remain future-phase scope unless a later brief explicitly authorizes them.

## Scope Clarification

This brief defines the authorized Phase 2 implementation scope after Phase 1 acceptance. It does not replace the full master plan.

Phase 2 is complete only when the master-plan gate is satisfied: the CLI contains no business logic, a real local author can operate the complete artifact chain, compression cannot be required for local operation, and no compressor may replace canonical source material.

Phase 3 remains unauthorized until Phase 2 passes and the project owner authorizes the next implementation brief.

## Required Work

- Generalized project and chapter services that are no longer hard-coded to one proof fixture.
- File-backed versioned artifacts with lineage, artifact type, project identity, source version, approval state, and trace references.
- Connected retry and revision flow that records the failed artifact, findings, proposed correction, reviewer decision, and accepted replacement.
- Approved L1-L3 memory update proposals with manual review before promotion.
- Reviewer-friendly QA output, validation findings, artifact diffs, and Markdown review notebook entries.
- CLI wrapper over services for local author and administrative workflows.
- CLI settings commands to show, validate, diff, and update settings only through PolicyCenter services.
- CLI character-governance checks for profile completeness, plot readiness, cast clutter, and promotion requests.
- CLI arc-state, supporting-function, change-event, and evolution-delta review commands.
- CLI source-promotion, beat-validation, action-plan-validation, and numeric-lock inspection commands.
- Reviewed installation and activation of local prompt or skill packages.
- Persona-aware model-run metadata and trace inspection.
- Reviewed Western dialogue skill fixture with no-invention and character-voice constraints.
- Constrained chapter generation from an approved plan or summary using local deterministic behavior.
- Review notebook and project knowledge-base lookup over approved local artifacts.
- Manual review and approval of extracted object, inventory, resource, and continuity-state updates.
- Lock projection rebuild, stale-lock detection, and reviewed lock-level changes.
- Context-compression policy placeholder and no-op service boundary, with compression disabled by default.

## Suggested Module Boundaries

Keep business logic in services and domain modules, not in command handlers.

```text
bookforge/services/
  artifact_store.py
  chapter_service.py
  character_governance_service.py
  context_compression_service.py
  knowledge_service.py
  lock_service.py
  memory_service.py
  policy_service.py
  project_service.py
  qa_service.py
  revision_service.py
  skill_package_service.py
  trace_service.py

bookforge/cli/
  __init__.py
  app.py
```

These names are guidance, not mandatory filenames. Use existing patterns if the codebase has already established a better local structure.

## Required Tests

- Multiple project fixtures resolve through services without cross-project leakage.
- Wrong project, wrong source version, missing canon, and path escape remain rejected.
- Artifact versions preserve lineage and do not mutate approved prior versions.
- Retry/revision flow records failed findings and accepted replacement artifacts.
- Unapproved artifacts cannot be exported, promoted to memory, used as lock projections, or used as chapter-generation inputs.
- L1-L3 memory updates require explicit approval before promotion.
- CLI commands call services and contain no independent validation or policy logic.
- Policy commands show, validate, diff, and update settings through PolicyCenter services.
- Character governance reports profile completeness, plot readiness, cast clutter, and promotion requests.
- Arc-state and supporting-character commands report change events and evolution deltas.
- Source promotion, beat validation, action-plan validation, and numeric-lock inspection are service-backed.
- Western dialogue fixture enforces no-invention and character-voice constraints.
- Constrained chapter generation refuses unapproved plans or summaries.
- Review notebook and knowledge lookup return only approved local project artifacts.
- Lock projection rebuild detects stale locks and requires reviewed lock-level changes.
- Trace inspection shows persona, capability, prompt metadata, policy snapshot, validation findings, provider identity, and artifact lineage.
- Context-compression policy defaults to disabled.
- No-op compression returns canonical source text unchanged and records original source IDs and versions.
- Local operation passes with compression disabled and without any compression dependency.
- Canon bible, character profiles, timeline, continuity locks, chapter contracts, plot locks, approval records, and final manuscript text cannot be replaced by compressed text.

## Must Not Build In Phase 2

- FastAPI service.
- Browser review app.
- PostgreSQL or other database dependency.
- Vector store, graph store, RAG service, or external research automation.
- Headroom dependency, LiteLLM middleware, MCP compression adapter, or required compressor path.
- Real external model provider routing unless a later brief explicitly authorizes it.
- Background workers, queues, production deployment, or multi-service Docker Compose production stack.
- Authentication, billing, tenancy, or hosted collaboration.
- EPUB/PDF export.
- Full-book generation engine.
- Series-level memory or ecosystem marketplace.

## Acceptance

Phase 2 is accepted when a local author can operate the complete artifact chain from project/chapter selection through constrained generation, QA, revision, approval, memory proposal, lock review, trace inspection, and approved Markdown export.

All behavior must be reachable through services. CLI commands may expose the behavior, but must not own the rules.

Compression must remain optional and disabled by default. Phase 2 may define policy and a no-op service boundary only; it must prove local operation does not require Headroom or any other compressor, and must prove canonical source material is never replaced by compressed text.

Verification must run deterministically offline through project-native tests and lint checks.

## Next Phase Rule

After Phase 2 passes and the project owner authorizes expansion, create:

```text
docs/info-plan/phases/phase-3-model-assisted-author-workflow.md
```

Do not implement Phase 3 behavior from this brief.
