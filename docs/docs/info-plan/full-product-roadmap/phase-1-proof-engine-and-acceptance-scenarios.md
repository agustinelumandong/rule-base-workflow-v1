# Phase 1 Proof Engine And Acceptance Scenario Completion

**Current state:** deterministic proof foundation implemented  
**Product-complete state:** proof fixtures cover the full master-plan acceptance scenarios and catch product regressions before UI/API work.

## Already Done

- [x] Deterministic proof fixture exists for `Lone Star Reckoning`.
- [x] Offline tests validate context package behavior, deterministic humanization, canon/meaning checks, capability limits, diff, approval, and Markdown export.
- [x] Default verification does not require network access.

## Missing For Full Product

- [ ] Proof fixture for complete book production, not just a chapter-level proof.
- [ ] Proof fixture for structured manuscript transformation with chapter preservation.
- [ ] Proof fixture for research-needed behavior and approved research fact use.
- [ ] Proof fixture for series carry-forward into a second book.
- [ ] Proof fixture for publication approval blocking export.
- [ ] Proof fixture for interrupted generation/validation/export recovery.
- [ ] Proof fixture for assistant authority rejection: no canon mutation, no approval, no publication, no cross-project access.

## Implementation Checklist

- [ ] Add a small multi-chapter book fixture with bible, outline, scene cards, sample approval, two chapter plans, and expected export.
- [ ] Add structured manuscript import fixture with headings and source offsets.
- [ ] Add research fixture with one approved fact, one disputed fact, and one missing-evidence request.
- [ ] Add series fixture with Book 1 final state and Book 2 starting-state expectations.
- [ ] Add failure fixtures for publication without approval and interrupted workflow recovery.
- [ ] Add tests that map each master-plan section 25 acceptance scenario to at least one deterministic fixture.

## Exit Gate

- [ ] Proof fixtures demonstrate full book creation and existing manuscript transformation without requiring API, UI, database, vector search, graph search, or external models.
- [ ] Proof fixtures fail when canon, policy, project isolation, publication approval, or authority boundaries are violated.
