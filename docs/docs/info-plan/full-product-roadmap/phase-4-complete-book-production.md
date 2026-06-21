# Phase 4 Complete Book Production Completion

**Current state:** full-book service foundations exist  
**Product-complete state:** BookForge can produce or transform a complete book with approved planning, bounded context, chapter generation, validation, final polish, and publication approval.

## Already Done

- [x] Service modules exist for outline, orchestration, scene cards, plot readiness, sliding context, book memory, book validation, manuscript assembly, final polish, and chapter approval.
- [x] Tests cover foundational full-book services.
- [x] Manuscript assembly from approved artifacts exists.

## Missing For Full Product

- [ ] End-to-end book production workflow from concept to export.
- [ ] Story bible approval workflow.
- [ ] Outline and chapter plan approval workflow.
- [ ] Scene cards and beat plans as first-class author/reviewer artifacts.
- [ ] Sample chapter calibration before bulk production.
- [ ] Multi-chapter generation loop with bounded context and resumable state.
- [ ] Book-level quality gate integrated into export/publication approval.
- [ ] Complete final-polish workflow that supersedes versions and records publication readiness.
- [ ] Full-book smoke test that exports multiple approved chapters.

## Implementation Checklist

- [ ] Add service-level `BookProductionWorkflow` that coordinates intake, bible, outline, sample, chapter plans, chapter generation, chapter approval, memory proposals, book validation, final polish, publication approval, and export.
- [ ] Add API routes for book production state and actions.
- [ ] Add ReviewDesk author workflow screens for bible, outline, scene cards, sample approval, chapter batch status, and publication gate.
- [ ] Add tests for missing required approvals at each gate.
- [ ] Add browser smoke workflow for a two-chapter complete book.

## Exit Gate

- [ ] A complete book can be produced without hidden state or unbounded context.
- [ ] Every chapter and publication check is approved or accepted with audit evidence.
- [ ] Complete manuscript export is blocked until the publication gate passes.
