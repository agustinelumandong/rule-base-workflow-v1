# BookForge Full-Product Roadmap Tracker

**Status:** full-product gap tracker  
**Source:** `docs/info-plan/BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Purpose:** track the difference between the accepted Phase 0-8 foundation and the complete BookForge product described in the master plan.

## Rule

This tracker does not create Phase 9. It reopens Phase 0-8 as product-completion tracks.

The accepted Phase 0-8 work remains valid foundation work. A phase is only product-complete when its checklist below is complete and its phase file exit gate passes.

## Summary

| Phase | Product Track | Current State | Product-Complete? | Phase File |
| --- | --- | --- | --- | --- |
| 0 | Product contracts and authority hardening | Foundation implemented | [ ] No | `phase-0-product-contracts-and-authority.md` |
| 1 | Proof engine and acceptance scenarios | Foundation implemented | [ ] No | `phase-1-proof-engine-and-acceptance-scenarios.md` |
| 2 | Local author product | Foundation plus CLI/API/browser slices | [ ] No | `phase-2-local-author-product.md` |
| 3 | Real model-assisted workflow | Provider boundary and opt-in OpenAI path exist | [ ] No | `phase-3-real-model-workflow.md` |
| 4 | Complete book production | Service foundations exist | [ ] No | `phase-4-complete-book-production.md` |
| 5 | ReviewDesk product UI | Local review UI exists | [ ] No | `phase-5-reviewdesk-product-ui.md` |
| 6 | Hosted production operations | Contracts/foundations exist | [ ] No | `phase-6-hosted-production-operations.md` |
| 7 | Research, retrieval, and series product | Foundations exist | [ ] No | `phase-7-research-retrieval-series-product.md` |
| 8 | Scale, ecosystem, and advanced publishing | Governance/foundation contracts exist | [ ] No | `phase-8-scale-ecosystem-advanced-publishing.md` |

## Current Verified Foundation

- [x] Typed schema and service foundations exist for Phase 0-8.
- [x] Deterministic offline test suite passes.
- [x] Local CLI can create project/book/chapter artifacts and export manuscript output.
- [x] ReviewDesk can create a local project/book, import `.txt`/`.md`, draft a candidate, approve it, export, and download Markdown.
- [x] OpenAI drafting is available as an opt-in provider path.
- [x] Documentation distinguishes accepted foundations from full product readiness.

## Product-Completion Gates

- [ ] Authors can start from a concept and produce a complete approved book.
- [ ] Authors can import a structured manuscript, extract proposed canon, approve it, transform chapters, and export approved content.
- [ ] Story bible, outline, scene cards, sample chapter approval, chapter plans, and chapter generation are first-class workflows.
- [ ] Every generated or transformed chapter carries provenance, context, validation, review, lineage, and approval state.
- [ ] Book-level quality gates block publication until unresolved setup, duplicate passage, timeline conflict, voice drift, continuity conflict, and policy blockers are resolved or accepted.
- [ ] Research facts and period packs can be searched/imported, snapshotted, claim-reviewed, approved, and used in planning/drafting with attribution.
- [ ] Series state can be built from approved books and used for next-book planning without resetting character state.
- [ ] Hosted team mode uses the same service contracts as local mode.
- [ ] Durable workers, queue, audit, object storage, backup/restore, retention, telemetry, auth, and authorization are wired beyond placeholders.
- [ ] Publication packages can be generated from approved versions only in Markdown, DOCX, EPUB, HTML, and PDF/profile outputs.

## Recommended Execution Order

1. Finish Phase 2 local author product gaps that make manual real-book testing credible.
2. Finish Phase 4 complete book production workflow because this is the core product promise.
3. Expand Phase 5 ReviewDesk to expose the complete author workflow.
4. Finish Phase 3 real model workflow so generated chapters can use approved context and providers safely.
5. Finish Phase 7 research/series workflows that affect book quality.
6. Finish Phase 6 hosted operations after local product workflow is coherent.
7. Finish Phase 8 ecosystem and advanced publishing after the core workflow works.
8. Re-audit Phase 0 and Phase 1 after higher phases expose missing contracts or proof cases.

## Definition Of Done For This Tracker

- [ ] Every phase file has all implementation checklist items checked.
- [ ] `python -m pytest` passes.
- [ ] `python -m ruff check .` passes.
- [ ] `npm --prefix review-app run check` passes.
- [ ] Browser smoke workflow passes with a real local chapter file and download directory.
- [ ] A full-book acceptance run produces an approved publication package from approved versions only.
