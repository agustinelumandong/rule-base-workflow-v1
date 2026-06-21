# BookForge Implementation Rules For AI Agents

**Status:** mandatory implementation guardrail  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13

## Master Rule

The BookForge Master Plan is authoritative, but an AI agent must only implement the assigned phase.

Do not implement all BookForge capabilities at once.

Only phases with an explicit implementation brief are authorized for coding.

If a phase exists in the master plan but has no implementation brief, treat it as future product direction, not build scope.

Do not create infrastructure for future phases unless the current phase contract explicitly requires an interface, schema, fixture, or placeholder.

## Phase 0-1 Allowed Work

Allowed:

- Contracts and schemas.
- File-backed artifacts.
- Deterministic tests.
- Prompt registry.
- Policy resolver.
- Capability registry.
- Persona registry.
- Context package builder.
- Deterministic provider.
- Validators.
- Review records.
- Approval records.
- Markdown export.

## Phase 0-1 Forbidden Work

Forbidden unless explicitly assigned:

- Browser UI.
- FastAPI API.
- PostgreSQL.
- Vector database.
- Graph database.
- RAG pipeline.
- External research automation.
- Autonomous multi-agent workflows.
- Model-provider marketplace.
- EPUB or PDF export.
- Full-book engine.
- Full series memory.
- Production workers, queues, auth, telemetry, backup, or billing.
- Multi-service Docker Compose production stack.
- Kubernetes or production orchestration.

## Containerization Rule

For Phase 0-1, provide only a local deterministic Docker environment capable of running tests and the file-backed proof engine.

Do not add PostgreSQL, Redis, Celery, FastAPI, frontend, vector database, graph database, object storage, Kubernetes, or external model services unless the current phase explicitly requires them.

The default container command must run offline deterministic tests.

## Authority Boundaries

- CanonCore owns truth.
- PolicyCenter owns settings resolution.
- MemoryVault owns current story state.
- StoryEngine owns structure.
- ProseForge writes and revises.
- JudgePanel validates.
- ReviewDesk approves.
- Publisher exports only approved artifacts.
- Personas advise; they do not command.
- External tools adapt; they do not own the product.

## Development Discipline

- Read `BOOKFORGE-MASTER-PLAN.md` before starting.
- Read the assigned phase brief before editing code.
- Keep changes scoped to the assigned phase.
- Write failing tests before behavior changes.
- Prefer deterministic offline tests.
- Do not introduce external services into Phase 0 or Phase 1.
- Preserve legacy planning folders as provenance.
- Report files changed, tests run, artifacts produced, known limitations, and next phase.

## Stop Rule

If a desired capability belongs to a later phase, represent it as a contract only or stop and ask for explicit phase expansion.
