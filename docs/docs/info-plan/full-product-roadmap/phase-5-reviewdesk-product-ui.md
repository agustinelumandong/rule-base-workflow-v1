# Phase 5 ReviewDesk Product UI Completion

**Current state:** local ReviewDesk review/workflow UI exists  
**Product-complete state:** ReviewDesk exposes the complete author/editor workflow over service-backed records without owning business logic.

## Already Done

- [x] FastAPI service boundary exists.
- [x] Browser ReviewDesk can load project state, review records, policies, traces, diffs, blockers, lineage, and local author workflow actions.
- [x] Browser can import chapter files and download exported Markdown.
- [x] API and UI containers exist for local Phase 5 workflow.

## Missing For Full Product

- [ ] Intake, bible, outline, scene-card, chapter-plan, sample approval, book validation, final polish, and publication approval views.
- [ ] Structured manuscript import and extraction review UI.
- [ ] Rich diff view with side-by-side/unified modes and semantic change summaries.
- [ ] Traceability panel for every model-created artifact.
- [ ] Policy management surfaces backed by controlled policy update services.
- [ ] Run recovery controls for real resumable jobs.
- [ ] Timeline, relationship, setup/payoff, chapter dependency, canon conflict, cost, quality, and throughput visualizations.
- [ ] UX for resolving findings, requesting targeted revision, accepting risk with reason, and proving blocker closure.

## Implementation Checklist

- [ ] Add ReviewDesk route/view sections for the complete book workflow.
- [ ] Add API read models for production workflow state.
- [ ] Add static and browser smoke tests for the complete book workflow UI.
- [ ] Add UI controls for provider selection that only show approved provider options.
- [ ] Add UI controls for publication approval and export blocking state.

## Exit Gate

- [ ] A real author/editor can operate the full book creation or transformation workflow from the browser.
- [ ] UI actions call services and do not duplicate workflow rules.
- [ ] Reviewers can understand what changed, why it changed, and what risks remain.
