# Phase 7 Research Retrieval And Series Product Completion

**Current state:** research, retrieval, and series foundations exist  
**Product-complete state:** research-grounded fiction and series development are usable workflows with attribution, approved facts, reproducible state, and benchmarked retrieval.

## Already Done

- [x] Modules exist for source snapshots, research tasks, claims, fact review, period packs, retrieval adapters, vector retrieval, benchmarks, series memory, story state, graph projection, cross-book continuity, and source promotion.
- [x] Tests cover foundational services.

## Missing For Full Product

- [ ] Research question workflow from UI/CLI/API.
- [ ] Trusted-source search/import and source snapshot approval workflow.
- [ ] Claim extraction review that distinguishes evidence, inference, disputed claims, missing evidence, and fictional canon.
- [ ] Period-pack maintenance workflow with approved historical facts and availability profiles.
- [ ] Drafting/planning context that uses approved research facts and returns `research_needed` instead of inventing.
- [ ] Retrieval benchmark gate before using vector retrieval for production context.
- [ ] Series bible and next-book planning workflow.
- [ ] Book 1 final state to Book 2 starting state workflow.
- [ ] Cross-book validation visible in ReviewDesk.

## Implementation Checklist

- [ ] Add research workflow API and ReviewDesk views.
- [ ] Add source import/search adapters behind controlled service boundaries.
- [ ] Add claim review UI and approval records.
- [ ] Add period-pack maintenance UI and tests.
- [ ] Add retrieval quality benchmark command and required promotion gate.
- [ ] Add series planning workflow from approved book state.
- [ ] Add browser smoke test for series carry-forward rejection of invalid resets.

## Exit Gate

- [ ] Research claims remain attributable and cannot silently become canon.
- [ ] Retrieval quality is benchmarked before production use.
- [ ] Series state is reproducible from approved books and canon changes.
- [ ] Next-book planning cannot reset scars, relationships, reputation, beliefs, unresolved obligations, resources, or locks without approved events.
