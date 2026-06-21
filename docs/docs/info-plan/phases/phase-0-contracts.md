# BookForge Phase 0 Contracts Brief

**Status:** implementation brief  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Scope:** contracts only, no runtime platform buildout

## Rule

Phase 0 exists to freeze the domain contracts before any larger engine work. Do not build UI, database infrastructure, RAG, graph memory, external research automation, autonomous agents, or production export pipelines in this phase.

Containerization, if added in Phase 0, is limited to a deterministic local test environment contract. Do not add production services.

## Scope Clarification

This brief defines the first authorized implementation slice for Phase 0. It does not replace the full Phase 0 gate in `BOOKFORGE-MASTER-PLAN.md`.

After this slice passes, do not declare Phase 0 complete. Any additional Phase 0 implementation scope requires a project-owner-authorized follow-up brief aligned with the full Phase 0 gate in `BOOKFORGE-MASTER-PLAN.md`.

The master-plan Phase 0 gate includes broader contracts such as authenticity, continuity locks, Western profile, character governance, character arc, theme, source promotion, beat planning, action scene, numeric lock, model-run, persona fixture, prompt fixture, and deterministic `Lone Star Reckoning` fixture contracts.

## First Authorized Phase 0 Cut

Implement or define these first:

- Project identity and project path rules.
- Artifact identity, version, lineage, hash, and role.
- Canon profile basics for entities, facts, relationships, timeline, and approval state.
- Character profile basics for identity, voice, references, role, motivation, and continuity constraints.
- Context package contract with scoped inputs and source references.
- Prompt registry contract with prompt ID, version, inputs, output contract, and tests.
- Policy resolver contract with precedence, immutable floors, and effective-policy snapshots.
- Capability registry contract with allowed tools, forbidden effects, gates, budgets, and retries.
- Persona registry contract with persona ID, version, prompt binding, capability map, and run metadata.
- Validation finding contract with issue ID, severity, confidence, evidence, violated rule, recommendation, and blocking status.
- Review approval contract with reviewer, decision, artifact version, findings, accepted risks, and timestamp.
- Deterministic provider contract for offline proof tests.
- Markdown export contract for approved artifacts only.

## Contract Files

The first implementation should represent these explicitly:

```text
bookforge/schemas/
  project.py
  artifact.py
  canon.py
  character.py
  context_package.py
  prompt.py
  policy.py
  capability.py
  persona.py
  validation.py
  review.py
  provider.py
  export.py
```

## Must Not Build In Phase 0

- Browser UI.
- FastAPI service layer.
- PostgreSQL or production migrations.
- Vector database.
- Graph database.
- External research automation.
- Multi-agent chat.
- Model-provider marketplace.
- EPUB or PDF export.
- Full series memory.
- Production workers, queues, telemetry, backup, or auth.
- Multi-service Docker Compose production stack.

## Acceptance

This first authorized Phase 0 cut is accepted when the listed contracts are internally consistent, schema-validated, covered by deterministic tests, and no interface or infrastructure layer can bypass policy, capability, validation, review, or approval contracts.

Phase 0 itself is complete only when the full Phase 0 gate in `BOOKFORGE-MASTER-PLAN.md` is satisfied.
