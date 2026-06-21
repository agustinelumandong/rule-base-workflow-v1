# BookForge Phase 1 Local Proof Engine Brief

**Status:** implementation brief  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Scope:** one deterministic local proof, not a full product

## Rule

Phase 1 proves that BookForge can transform one chapter through controlled context, deterministic output, validation, review, and Markdown export. It must run offline through tests and must not require CLI, API, UI, database, RAG, graph, or external model service.

If containerized, Phase 1 uses one local `bookforge-dev` service whose default command runs offline deterministic tests.

## Scope Clarification

This brief defines the minimum proof required for Phase 1 implementation. It does not replace the full Phase 1 gate in `BOOKFORGE-MASTER-PLAN.md`.

Phase 1 must not be declared complete unless the full master-plan Phase 1 deliverables and gate are satisfied.

This wording does not create a separate Phase 1 follow-up brief path; after Phase 1, the next implementation brief is Phase 2 as defined in `docs/info-plan/phase-roadmap-index.md`.

The master-plan Phase 1 gate includes broader fixture coverage for approved key cast, antagonist profile, supporting-character function, file-backed policies, authenticity, period pack, continuity locks, Western style, persona-bound fixtures, character governance, character arc, theme governance, source promotion, beat completeness, numeric locks, QA, diff, trace, simulated approval, and Markdown export.

## Minimum Proof Story Scope

Use a tiny `Lone Star Reckoning` fixture:

- One project.
- One imported chapter.
- One protagonist.
- One antagonist.
- One supporting character.
- One weapon.
- One ammunition-count contradiction.
- One unprofiled-name contradiction.
- One Western style violation.
- One approval.
- One Markdown export.

## Required Proof Flow

```text
import chapter
-> load approved project, canon, style, policy, persona, and prompt fixtures
-> build scoped context package
-> run deterministic humanization or fixture provider
-> validate meaning, canon, style, capability, and continuity
-> produce targeted corrected artifact
-> save diff, findings, trace, review decision, and approval
-> export approved Markdown
```

## Required Tests

- Wrong project or version is rejected.
- Missing canon blocks grounded work.
- Path escape is rejected.
- Unapproved export is rejected.
- Meaning-changing humanization is detected.
- Unsupported canon fact is detected.
- Unprofiled proper name is blocked.
- Western style violation is reported.
- Revolver starts with three rounds, one fired shot transitions to two, and a later three-round claim is rejected unless a reload or ammunition acquisition is approved.
- Selected persona can only use capabilities granted by the active stage.
- Model run records prompt, persona, capability, context package, provider, artifact output, validation results, and policy snapshot.

## Must Not Build In Phase 1

- Full-book generation.
- Browser review app.
- FastAPI service.
- PostgreSQL.
- Vector or graph retrieval.
- External research automation.
- Real provider routing unless explicitly assigned.
- Multi-agent workflows.
- EPUB/PDF export.
- Series-level memory.
- Multi-service Docker Compose production stack.

## Acceptance

This minimum Phase 1 proof is accepted when the proof runs deterministically offline, preserves plot and canon, blocks the seeded failures, exports only approved Markdown, and produces a trace that a reviewer can inspect.

Phase 1 itself is complete only when the full Phase 1 gate in `BOOKFORGE-MASTER-PLAN.md` is satisfied.
