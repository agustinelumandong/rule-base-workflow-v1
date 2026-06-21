# Phase 3 Real Model Workflow Completion

**Current state:** provider boundaries and opt-in OpenAI drafting path exist  
**Product-complete state:** real model-assisted drafting, humanization, evaluation, and revision operate through approved context, policy, benchmark, trace, and review gates.

## Already Done

- [x] Deterministic provider is default.
- [x] OpenAI provider path is opt-in.
- [x] Provider policy, budget, trace, benchmark, and model-run service foundations exist.
- [x] Model-assisted evaluation service foundations exist.

## Missing For Full Product

- [ ] Browser-visible provider selection and policy display for real drafting.
- [ ] Real humanization mode for existing manuscript transformation.
- [ ] Model-assisted continuity, voice, style, and authenticity evaluation wired into the author workflow.
- [ ] Prompt registry used for real model prompts instead of ad hoc prompt text.
- [ ] Benchmark gate that must pass before a provider/model/prompt can be used for a task.
- [ ] Targeted revision generation from specific findings.
- [ ] Model output provenance on every model-created artifact, visible in UI.
- [ ] Failure behavior for provider timeout, budget exceeded, policy denial, invalid structured output, and unsafe change.

## Implementation Checklist

- [ ] Add API and ReviewDesk controls for deterministic vs approved real provider runs.
- [ ] Add tests for model-run trace completeness: provider, model, prompt, persona, capability, context package, policy, budget, input artifacts, output artifacts.
- [ ] Add `humanize_chapter` provider workflow for existing manuscripts.
- [ ] Add report-only evaluator execution after draft/humanize.
- [ ] Add targeted revision service that accepts finding IDs and preserves clean regions.
- [ ] Add benchmark records and policy checks before provider execution.

## Exit Gate

- [ ] Real model-assisted output cannot bypass deterministic tests, policy gates, budget gates, validation, review, or publication approval.
- [ ] A model can be changed without rewriting workflow logic.
- [ ] Every model-assisted artifact has provenance, validation, lineage, and review state.
