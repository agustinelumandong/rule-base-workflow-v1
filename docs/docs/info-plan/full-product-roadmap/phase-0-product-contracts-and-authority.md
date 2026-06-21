# Phase 0 Product Contracts And Authority Completion

**Current state:** foundation implemented  
**Product-complete state:** every later product workflow has explicit contracts, authority boundaries, policy floors, and audit metadata.

## Already Done

- [x] Core schema modules exist for project, canon, character, chapter, artifact, context, policy, validation, review, model run, persona, source promotion, historical/authenticity, locks, theme, object, story state, and numeric locks.
- [x] Capability, provider, persona, policy, artifact, approval, and trace boundaries exist.
- [x] Deterministic tests cover many contract-level constraints.

## Missing For Full Product

- [ ] Contract coverage audit for the full master-plan acceptance scenarios.
- [ ] Publication approval contract that is separate from chapter approval and cannot be bypassed by CLI/API/UI.
- [ ] Complete policy snapshot hashing on every generated, transformed, reviewed, and exported artifact.
- [ ] Explicit full-book workflow state contracts: concept, bible, outline, sample chapter, chapter plan, chapter batch, publication gate, archive package.
- [ ] Structured manuscript import contracts that preserve chapters, scenes, headings, front matter, and source mapping.
- [ ] Hosted/team actor contract parity with local single-user mode.
- [ ] Product-wide authority matrix documenting which service can mutate canon, memory, story state, review decisions, publication state, research facts, locks, and policy.

## Implementation Checklist

- [ ] Add contract tests for every item in `BOOKFORGE-MASTER-PLAN.md` section 25.
- [ ] Add `PublicationApproval` and `PublicationGateReport` schemas.
- [ ] Add `BookProductionState`, `ManuscriptImportMap`, and `WorkflowAuthorityMatrix` schemas.
- [ ] Ensure CLI, API, UI, workers, and assistant surfaces reference the same service-owned authority model.
- [ ] Add docs explaining which records are authoritative and which records are derived views.

## Exit Gate

- [ ] All full-product workflows can be represented without ad hoc dictionaries or UI-only state.
- [ ] Every authority-changing operation records actor, project, scope, policy snapshot, input artifact versions, output artifact versions, and audit reference.
- [ ] Existing tests pass with external model access disabled.
