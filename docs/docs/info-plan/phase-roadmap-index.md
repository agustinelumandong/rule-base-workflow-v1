# BookForge Phase Roadmap Index

**Status:** roadmap index  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Purpose:** show that all phases exist while keeping implementation scope limited.

## Rule

Only phases with an explicit implementation brief are authorized for coding.

If a phase exists in the master plan but has no implementation brief, treat it as future product direction, not build scope.

Do not create infrastructure for future phases unless the current phase contract explicitly requires an interface, schema, fixture, or placeholder.

## Phase Status

| Phase | Name | Status | Brief |
| --- | --- | --- | --- |
| 0 | Product contracts | Implementation-ready | `phases/phase-0-contracts.md` |
| 1 | Local proof engine | Implementation-ready after Phase 0 passes | `phases/phase-1-local-proof-engine.md` |
| 2 | Useful local engine | Implementation-ready after Phase 1 passes | `phases/phase-2-useful-local-engine.md` |
| 3 | Model-assisted author workflow | Implementation-ready after Phase 2 passes | `phases/phase-3-model-assisted-author-workflow.md` |
| 4 | Full-book engine | Implementation-ready after Phase 3 passes | `phases/phase-4-full-book-engine.md` |
| 5 | Review application | Accepted local implementation | `phases/phase-5-review-application.md` |
| 6 | Production operations | Accepted production operations foundation | `phases/phase-6-production-operations.md` |
| 7 | Retrieval, research, and series | Accepted retrieval, research, and series foundation | `phases/phase-7-retrieval-research-and-series.md` |
| 8 | Scale and ecosystem | Accepted scale and ecosystem foundation | `phases/phase-8-scale-and-ecosystem.md` |

## Correct Reading

`BOOKFORGE-MASTER-PLAN.md` is the full product blueprint. It contains all phases and the final architecture direction.

The Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 6, Phase 7, and Phase 8 briefs are the current implementation scope. They exist because those phases form the local foundation, first model-assisted workflow, full-book engine, review application, production operations foundation, retrieval/research/series foundation, and scale/ecosystem foundation:

- Phase 0 defines contracts, schemas, policies, validators, prompt metadata, persona metadata, and approval records.
- Phase 1 proves the engine locally with deterministic tests and a small fixture.
- Phase 2 turns that proof into a useful local author engine with generalized services, versioned artifacts, reviewer-friendly QA, approved memory updates, and CLI wrappers over the service layer.
- Phase 3 adds model-assisted drafting and evaluation behind service boundaries while preserving deterministic fallback, benchmark gates, human review, and approved-source protection.
- Phase 4 adds full-book planning, chapter orchestration, sliding context, book-level validation, approved manuscript assembly, and manual final-polish workflow while preserving local service boundaries.
- Phase 5 adds a local FastAPI boundary and browser review workspace over existing services while preserving portable authoritative artifacts, exact-version approvals, policy floors, and read-only derived visualizations.
- Phase 6 adds production operations infrastructure for database-backed metadata, durable jobs, authentication, authorization, audit, object storage, telemetry, backup/restore, team review, and sandbox workers while preserving service authority and artifact portability.
- Phase 7 adds attributable research workflows, evaluated retrieval, source snapshots, claim extraction, period-pack maintenance, series memory, relational story-state queries, derived graph projections, cross-book validation, and advanced export profiles while preserving approved artifacts and canon as source authority.
- Phase 8 adds scale-readiness, controlled integration boundaries, multi-channel assistant contracts, specialized local serving contracts, fine-tuning eligibility records, portfolio analytics, and ecosystem governance while preserving all prior approval, attribution, audit, and authority boundaries.

Containerization follows the same rule. Use `containerization-strategy.md` as the phased guide: one deterministic local test container for Phase 0/1, optional CLI/model environment later, API/UI containers in Phase 5, and production services in Phase 6.

Later phase briefs should be created only after the prior phase passes its gate and the project owner authorizes the next phase.

## Next Brief Rule

After Phase 8 passes, no further phase brief is authorized by the current master plan.

Do not create implementation-ready briefs beyond Phase 8 unless the project owner updates the master plan.
