# BookForge Phase 3 Model-Assisted Author Workflow Brief

**Status:** implementation brief  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Scope:** model-assisted local author workflow behind services, not a hosted platform

## Rule

Phase 3 introduces optional model assistance for drafting, humanization, report-only evaluation, authenticity checks, and constrained export. It must preserve the Phase 0-2 service boundaries: models are replaceable workers, services own workflow state, validators compare against approved originals, and humans approve state changes.

Offline deterministic tests must remain the default safety baseline. Real provider paths are allowed only behind adapters, policy, trace, budget, and benchmark gates. Unsafe model output must become findings or failed attempts, not approved truth.

Headroom or any context-compression adapter remains optional experiment scope only. Compression may target logs, tool output, validator reports, QA reports, and retrieval previews, but must not replace canon, profiles, timelines, locks, approvals, final manuscript text, or validator source material.

## Scope Clarification

This brief defines the authorized Phase 3 implementation scope after Phase 2 acceptance. It does not authorize API, browser UI, database infrastructure, full-book generation, production workers, RAG/vector/graph retrieval, unrestricted research automation, marketplace behavior, or series-level memory.

Phase 4 remains unauthorized until Phase 3 passes and the project owner authorizes the next implementation brief.

## Required Work

- Provider adapter interface with deterministic fallback and optional local/cloud adapters.
- Provider policy service for allowed provider IDs, task permissions, privacy class, budget limits, timeout limits, and fallback behavior.
- Prompt/model trace records that include provider, model ID, prompt ID, persona, capability, policy snapshot, budget usage, input artifacts, output artifact, and validation findings.
- Budget control service that rejects runs exceeding configured project, stage, or task budget.
- Benchmark suite comparing deterministic fallback and model-assisted paths against required safety thresholds.
- Real drafting and humanization service that only uses approved plan, summary, context, style, persona, and policy inputs.
- Report-only continuity, voice, Western style, and authenticity evaluation services.
- Event extraction service that proposes evidenced object, inventory, resource, continuity, and character-state transitions without auto-promotion.
- Research-needed request output for missing period-authenticity evidence.
- Cultural, environmental, travel, settlement, law/custom, supply, and cultural-review authenticity findings with evidence and human-review requirements.
- Western style evaluation for behavioral emotion, reader inference, dialogue, dialect, vocabulary, and modernism risk.
- Restricted analysis services with explicit input contracts and prohibited effects.
- DOCX export service for approved artifacts only.
- Optional context-compression experiment for non-canonical presentation material.

## Suggested Module Boundaries

Keep provider, budget, benchmark, and model-run behavior in services. CLI may expose commands later, but must not own rules.

```text
bookforge/providers/
  __init__.py
  base.py
  deterministic.py
  local_stub.py

bookforge/services/
  provider_policy_service.py
  budget_service.py
  benchmark_service.py
  model_run_service.py
  model_drafting_service.py
  report_evaluation_service.py
  event_extraction_service.py
  authenticity_evaluation_service.py
  restricted_analysis_service.py
  docx_export_service.py
  compression_experiment_service.py

bookforge/cli/
  app.py
```

These names are guidance, not mandatory filenames. Use existing local service patterns if a better shape emerges.

## Required Tests

- Provider adapter interface runs deterministic fallback without network or secrets.
- Real provider adapter cannot run unless policy explicitly allows that provider and task.
- Provider policy blocks unknown provider IDs, disallowed tasks, missing privacy approval, and unsafe fallback behavior.
- Budget service rejects runs over project, stage, and task budgets.
- Model-run trace records provider, model ID, prompt, persona, capability, policy snapshot, budget usage, inputs, output, and findings.
- Drafting and humanization refuse unapproved plan, summary, context, style, persona, or policy inputs.
- Drafting and humanization produce candidate artifacts only; they do not approve, export, promote memory, or mutate locks.
- Report-only continuity, voice, style, and authenticity evaluators create findings only.
- Event extraction creates proposed state updates only; promotion still requires Phase 2 review/approval services.
- Research-needed requests are emitted when period evidence is missing.
- Authenticity findings include domain, evidence, source artifact, confidence, and human-review requirement.
- Western style evaluation detects behavioral emotion, dialogue drift, dialect overuse, vocabulary modernism, and reader-inference violations.
- Benchmark suite fails model-assisted paths that increase canon violations, unsupported facts, style regressions, or human-review risk above threshold.
- DOCX export rejects unapproved artifacts.
- Optional compression experiment refuses canonical source replacement and records original source IDs and versions.
- Existing offline deterministic tests still pass with model features disabled.

## Must Not Build In Phase 3

- FastAPI service.
- Browser review application.
- PostgreSQL, production migrations, object storage, worker queues, or production deployment.
- Vector store, graph store, RAG service, or full retrieval platform.
- Unrestricted external research automation.
- Full-book generation engine.
- Series-level memory.
- Auth, billing, tenancy, marketplace, or hosted collaboration.
- Required Headroom, LiteLLM middleware, or MCP compression adapter.
- Any path where a model can approve artifacts, mutate canon, promote memory, weaken policy, bypass validators, or replace canonical source material.

## Acceptance

Phase 3 is accepted when optional model-assisted drafting, humanization, report-only evaluation, event extraction, benchmark, trace, budget, and approved DOCX export paths operate behind services while deterministic offline tests still pass.

Model paths must meet benchmark thresholds. Unsafe changes must remain blocked or reported. Humans remain the approval authority for artifacts, memory, locks, and state updates.

Compression experiments, if implemented, must remain optional, disabled by default, and limited to non-canonical presentation material.

## Next Phase Rule

After Phase 3 passes and the project owner authorizes expansion, create:

```text
docs/info-plan/phases/phase-4-full-book-engine.md
```

Do not implement Phase 4 behavior from this brief.
