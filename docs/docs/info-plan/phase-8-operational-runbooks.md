# BookForge Phase 8 Operational Runbooks

**Status:** Phase 8 operations procedure
**Scope:** scale and ecosystem operations for the accepted Phase 0-8 system

Phase 8 operations are controlled ecosystem procedures. Connectors, assistant channels, analytics, local serving, and fine-tuning eligibility are infrastructure around BookForge services. They do not own canon, approval, publication, policy, research, graph, lock, memory, or audit authority.

## Connector Setup

1. Register the connector disabled by default.
2. Record connector kind, version, declared capabilities, compatibility status, and project scope.
3. Review compatibility before enablement.
4. Grant only the exact capabilities required by the actor and project.
5. Record setup and first use in integration audit.

## Connector Revocation

1. Revoke capability grants before changing connector state.
2. Mark the connector revoked or quarantined.
3. Record actor, connector, capability, target, result, and recovery state.
4. Export a package manifest preserving connector metadata, grants, audit references, versions, disabled state, and project scope.

## Incident Response

1. Quarantine the connector immediately.
2. Stop assistant channels or jobs using the connector.
3. Record the incident in integration audit.
4. Review affected projects and revoke grants when needed.
5. Reapprove only after compatibility review and recovery evidence.

## Fine-Tuning Eligibility

1. Build dataset manifests from approved source lineage only.
2. Require consent records, redaction reports, evaluation reports, and human approval.
3. Record rejection reasons for missing gates.
4. Do not execute fine-tuning from eligibility records alone.

## Analytics Interpretation

1. Treat portfolio analytics as derived reports.
2. Use analytics to identify review throughput, accepted-output cost, quality trends, retrieval quality, research coverage, and production bottlenecks.
3. Do not mutate source records from analytics reports.
4. Recompute reports from approved/audited records when source data changes.

## Local Serving Rollback

1. Disable local serving contract.
2. Restore deterministic fallback.
3. Mark health status disabled or degraded.
4. Keep budget and provider policy gates intact.
5. Record rollback in audit when project behavior changes.

## Acceptance Checks

- Integrations are disabled by default.
- Capability grants are project-scoped and revocable.
- Assistant channels route through service contracts only.
- Fine-tuning eligibility remains gated and non-executing.
- Analytics remain derived and non-mutating.
- Local serving is opt-in and has deterministic fallback.
