# BookForge Phase 8 Scale And Ecosystem Brief

**Status:** accepted implementation
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13
**Scope:** scale-readiness and controlled ecosystem foundation for the accepted Phase 0-7 system

## Rule

Phase 8 adds scale and ecosystem foundations only after Phase 7 acceptance. It may add dedicated search or workflow infrastructure contracts, controlled external tool integration boundaries, multi-channel assistant interfaces, specialized local serving contracts, fine-tuning eligibility records, portfolio analytics, and integration ecosystem governance.

Phase 8 must preserve every prior authority boundary. External tools, assistant channels, analytics, local serving endpoints, fine-tuning datasets, and integration adapters are infrastructure around BookForge services. They must not own canon truth, approval authority, publication readiness, policy weakening, research attribution, graph mutation, memory promotion, lock mutation, audit deletion, or validator bypass.

Every ecosystem capability must be explicitly enabled, auditable, project-scoped, and reversible. Default deterministic tests must remain offline with external model access disabled.

## Scope Clarification

This brief defines the authorized Phase 8 implementation scope after Phase 7 acceptance. The current master plan has no Phase 9; do not create one from this brief.

Phase 8 may add:

- Scale-readiness contracts for dedicated search, workflow, queue, cache, and background execution infrastructure.
- Integration registry for controlled external tool/API/MCP-style connectors.
- Capability grants, policy checks, audit records, and project scoping for integrations.
- Multi-channel assistant interface contracts for CLI, API, chat, editor, and background assistant surfaces.
- Specialized local serving contracts for local model/runtime endpoints that remain disabled by default in tests.
- Fine-tuning eligibility records, dataset manifests, consent gates, redaction reports, and evaluation gates.
- Portfolio analytics for project health, accepted-output cost, review throughput, quality trends, retrieval quality, research coverage, and production bottlenecks.
- Ecosystem governance records for connector review, revocation, quarantine, incident records, and compatibility status.
- Integration package export/import manifests that preserve permissions, versions, audit references, and disabled-by-default safety.

Phase 8 must not add:

- Uncontrolled external tool execution.
- Network-dependent required tests.
- Autonomous publication, canon mutation, policy weakening, accepted-risk creation, memory promotion, research approval, graph mutation, lock mutation, audit deletion, or validator bypass.
- Fine-tuning job execution without explicit eligibility, consent, redaction, evaluation, and human approval records.
- Hosted multi-tenant commercial billing, marketplace payment flows, or user-facing ecosystem marketplace operations beyond governance contracts.
- Any Phase 9 or post-master-plan implementation scope.

## Required Work

1. Scale infrastructure contracts for dedicated search, workflow, cache, queue, and local serving infrastructure readiness.
2. Integration registry service for external tool/API/MCP-style connectors with disabled-by-default state, version metadata, capability declarations, and compatibility status.
3. Integration capability grant service that enforces project scope, actor identity, allowed capability, policy status, and revocation.
4. Integration audit and incident service for connector use, failures, quarantine, revocation, compatibility breaks, and recovery actions.
5. Multi-channel assistant interface contracts for CLI, API, chat, editor, and background assistants without giving any channel direct authority over canon or approval state.
6. Local serving contract for specialized local runtime endpoints with explicit opt-in, health checks, budget policy, provider policy, and deterministic offline fallback.
7. Fine-tuning eligibility service for dataset manifests, consent gates, redaction reports, evaluation gates, approval records, and rejection reasons.
8. Portfolio analytics service for project health, review throughput, accepted-output cost, validation quality trends, retrieval quality, research coverage, and production bottlenecks.
9. Ecosystem governance service for connector review, compatibility status, quarantine, revocation, and reapproval.
10. Integration package export/import manifest that preserves connector metadata, capability grants, audit references, versions, disabled state, and project scope.
11. API/service boundary additions for scale, integrations, assistants, serving, fine-tuning eligibility, analytics, and governance without moving business rules into route handlers.
12. Operational documentation for safe connector setup, revocation, incident response, fine-tuning eligibility, analytics interpretation, and local serving rollback.
13. Phase 8 acceptance cleanup proving external integrations are controlled, analytics are derived, fine-tuning remains gated, assistant channels preserve authority boundaries, and existing deterministic offline tests pass.

## Suggested Module Boundaries

Keep ecosystem capabilities behind service contracts. Connectors, assistant surfaces, analytics, and serving endpoints are infrastructure around approved BookForge services.

```text
bookforge/scale/
  infrastructure.py
  local_serving.py

bookforge/ecosystem/
  registry.py
  grants.py
  audit.py
  governance.py
  packages.py

bookforge/assistants/
  channels.py

bookforge/training/
  eligibility.py

bookforge/analytics/
  portfolio.py
```

These names are guidance, not mandatory filenames. Use existing local patterns where they fit better.

## Required Tests

- Scale infrastructure contracts remain disabled or local/deterministic by default and never require external network services.
- Integration registry rejects enabled connectors without explicit compatibility, policy, and approval records.
- Capability grants reject cross-project access, unknown capabilities, revoked connectors, and disabled connectors.
- Integration audit records are append-only and include actor, project, connector, capability, target, result, and recovery state.
- Quarantined or revoked connectors cannot execute capabilities.
- Assistant channels can request actions only through service contracts and cannot mutate canon, approval, publication, memory, research, graph, or policy state directly.
- Local serving remains opt-in and respects budget policy, provider policy, health checks, and deterministic fallback.
- Fine-tuning eligibility rejects datasets without consent, redaction, evaluation, source lineage, and human approval.
- Portfolio analytics are derived from approved/audited records and cannot mutate source records.
- Integration package export/import preserves connector metadata, grants, versions, audit references, disabled state, and project scope.
- API routes delegate to service boundaries and contain no business-rule implementation.
- Existing offline deterministic tests still pass with external model access disabled.

## Must Not Build In Phase 8

- Uncontrolled external integration execution.
- Required network-dependent tests.
- Hosted marketplace payment flows or commercial billing.
- Autonomous approval, canon mutation, publication readiness, research approval, memory promotion, graph mutation, policy weakening, validator bypass, lock mutation, or audit deletion.
- Fine-tuning execution without eligibility, consent, redaction, evaluation, and human approval gates.
- Any Phase 9 or post-master-plan feature scope.

## Acceptance

Phase 8 is accepted when BookForge can describe, register, gate, audit, revoke, package, and monitor scale/ecosystem capabilities while preserving all Phase 0-7 authority boundaries.

External integrations must be controlled and disabled by default. Assistant channels must route through services. Analytics must be derived and non-mutating. Fine-tuning must remain eligibility-gated. Local serving must be opt-in and deterministic tests must remain offline.

Existing deterministic offline tests must still pass with external model access disabled.

## Acceptance Result

Phase 8 is accepted as the scale and ecosystem foundation.

Implemented artifacts include scale infrastructure contracts, integration registry, capability grants, integration audit and incidents, assistant channels, local serving contracts, fine-tuning eligibility, portfolio analytics, ecosystem governance, integration packages, API/service boundaries, and operational runbooks.

The accepted scope remains controlled infrastructure around the Phase 0-7 service model. Phase 8 does not authorize uncontrolled external integration execution, network-dependent required tests, hosted marketplace payment flows, autonomous authority changes, or any post-master-plan phase.

## Next Phase Rule

The current master plan ends at Phase 8.

Do not create additional implementation-ready phase briefs unless the project owner updates `BOOKFORGE-MASTER-PLAN.md`.
