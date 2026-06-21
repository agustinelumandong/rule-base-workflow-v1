# BookForge Phase 6 Production Operations Brief

**Status:** accepted implementation
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13
**Scope:** production operations foundation for the approved Phase 0-5 service/API/review application

## Rule

Phase 6 moves BookForge from local review application mode toward a production-capable operational foundation. It may add transactional metadata storage, durable job execution, authentication and authorization, audit records, object storage, telemetry, backup and restore, team review workflow, comments, assignments, locking, and a hardened sandbox worker where predefined services cannot satisfy approved analysis or export requirements.

Phase 6 must preserve all prior authority boundaries. The database, worker, queue, object storage, API, browser app, and sandbox are operational infrastructure. They do not own canon truth, approval authority, publication readiness, model policy, validator bypasses, or artifact meaning.

Portable artifact records remain authoritative content records unless an explicit migration contract says otherwise. Production metadata may index, reference, lock, audit, recover, and transact around artifacts, but it must not create competing truth.

## Scope Clarification

This brief defines the authorized Phase 6 implementation scope after Phase 5 acceptance. It does not authorize Phase 7 retrieval, research, series memory, pgvector retrieval, graph search, cross-book production, or advanced research workflows.

Phase 6 may add:

- PostgreSQL-backed transactional metadata.
- Alembic or equivalent migration discipline.
- Relationship and workflow state tables needed by existing project, artifact, review, run, policy, and publication surfaces.
- Durable worker and queue for authorized long-running jobs.
- Authentication, authorization, and audit records.
- Object storage adapter or equivalent durable artifact storage abstraction.
- Telemetry for jobs, costs, provider health, failures, and recovery state.
- Backup, restore, retention, and project export operational procedures.
- Team review, comments, assignments, and chapter locking.
- Hardened sandbox worker for approved restricted analysis/export tasks.
- Production-oriented local/container topology for API, review app, database, queue, worker, object storage, telemetry, backup, and restore.

Phase 6 must not add:

- ResearchCore evidence workflows, claim extraction, historical-fact review, or period-pack maintenance.
- pgvector retrieval, vector search service, graph store, RAG service, or full retrieval platform.
- Series memory, cross-book production engine, cross-book validation, or series-level source promotion.
- Billing, marketplace, hosted multi-tenant commercial operations, fine-tuning, MCP integrations, or external ecosystem features.
- Model autonomy for approval, canon mutation, memory promotion, policy weakening, publication readiness, or validator bypass.

Phase 7 remains unauthorized until Phase 6 passes and the project owner authorizes the next implementation brief.

## Required Work

- Production configuration model for environment, storage roots, database URL, queue URL, object storage URL, telemetry settings, auth settings, and external-model defaults.
- PostgreSQL schema and migrations for project metadata, artifacts, artifact lineage, policy snapshots, review decisions, accepted risks, validation findings, model/run traces, jobs, locks, comments, assignments, audit events, and publication gates.
- Repository layer that maps database metadata to existing service contracts without moving business rules into SQL or route handlers.
- Migration tests proving schema creation, upgrade, downgrade where supported, and idempotent bootstrapping.
- Durable job model for queued, running, succeeded, failed, canceled, and retryable work.
- Worker service that executes only registered job types through existing services and records deterministic recovery state.
- Queue adapter abstraction with a local deterministic adapter and production Redis or equivalent adapter.
- Authentication service boundary with local single-user development mode and production identity adapter contract.
- Authorization service for project, book, artifact, review, policy, export, admin, worker, and sandbox capabilities.
- Audit service recording who did what, when, against which project/book/artifact/policy/version, from which surface, and with which result.
- Team review service for comments, assignments, reviewer identity, chapter locking, lock expiry, lock release, and conflict handling.
- Object storage adapter that stores and retrieves artifact payloads while preserving content hashes, lineage, project scope, and portable export support.
- Telemetry service for job status, failures, retries, provider budget/cost usage, queue depth, worker health, API health, and export/recovery state.
- Backup and restore service for database metadata, artifact payloads, policy records, review decisions, traces, and export packages.
- Project export and import package that preserves approved artifacts, lineage, hashes, policies, review decisions, audit references, and recovery markers.
- Hardened sandbox worker for approved restricted analysis/export tasks with scoped input, resource limits, denied network by default, cleanup, and immutable result records.
- Production container topology for API, review app, PostgreSQL, Redis or queue equivalent, worker, object storage equivalent, telemetry, backup, and restore.
- Operational runbooks for setup, migration, seed/demo data, backup, restore, worker recovery, failed job retry, and incident rollback.

## Suggested Module Boundaries

Keep workflow authority in services. Database repositories, workers, queue adapters, auth adapters, telemetry, and sandbox code are infrastructure around service contracts.

```text
bookforge/config/
  production.py

bookforge/db/
  migrations/
  models.py
  repositories.py

bookforge/operations/
  jobs.py
  queues.py
  workers.py
  audit.py
  telemetry.py
  backup_restore.py
  object_storage.py
  sandbox.py

bookforge/security/
  authentication.py
  authorization.py

bookforge/review/
  team_review.py
  locks.py

containers/
  postgres/
  worker.Dockerfile
  sandbox.Dockerfile
```

These names are guidance, not mandatory filenames. Use existing local patterns where they fit better.

## Required Tests

- Production configuration defaults disable external model access and reject missing required production secrets/settings.
- Database migrations create required metadata tables and preserve project-scoped uniqueness constraints.
- Repository layer rejects cross-project artifact, policy, review, trace, job, and lock access.
- Artifact metadata stored in PostgreSQL preserves content hash, lineage, storage pointer, state, project ID, version, and approval linkage.
- Existing artifact directory records remain portable and exportable.
- Queue adapter records job lifecycle transitions and rejects unknown job types.
- Worker executes only registered job types through existing services and records recovery state.
- Worker retries respect retry limits, budget policy, provider policy, and approval gates.
- Authentication identifies local dev user in development mode and refuses anonymous production requests.
- Authorization blocks unauthorized project, artifact, policy, review, export, admin, worker, and sandbox actions.
- Audit records are immutable append-only records for policy changes, review decisions, accepted risks, lock events, job transitions, exports, and admin actions.
- Team comments and assignments are project-scoped and cannot mutate canon, artifact text, or approval state.
- Chapter locks prevent conflicting review/edit actions and expire or release deterministically.
- Object storage adapter validates content hashes and rejects cross-project object access.
- Telemetry reports job health, queue depth, failures, retries, cost/budget usage, provider health, and recovery state without exposing secrets.
- Backup captures database metadata and artifact payloads; restore reproduces project state, hashes, approvals, traces, jobs, and export readiness.
- Project export/import round trip preserves approved artifacts, lineage, policies, review decisions, audit references, and recovery markers.
- Sandbox worker receives only scoped inputs, denies network by default, enforces resource limits, cleans workspaces, and cannot mutate canon, policy, memory, locks, or approval state.
- API/UI continue to route meaningful actions through services after repository/worker infrastructure is introduced.
- Existing offline deterministic tests still pass with external model access disabled.

## Must Not Build In Phase 6

- ResearchCore claim/evidence workflows.
- Period-pack maintenance and historical-fact review workflows.
- pgvector retrieval, vector search service, graph store, graph search, RAG service, or full retrieval platform.
- Series memory, cross-book planning, cross-book validation, or series-level source promotion.
- Billing, marketplace, fine-tuning, external MCP ecosystem, or hosted multi-tenant commercial operations.
- Model autonomy for approval, publication readiness, canon mutation, memory promotion, lock mutation, policy weakening, validator bypass, or audit deletion.

## Acceptance

Phase 6 is accepted when BookForge can run with production-style operational infrastructure while preserving all Phase 0-5 authority boundaries.

Isolation and approval rules must survive the move to database-backed metadata, durable jobs, object storage, authentication, authorization, audit, telemetry, backup/restore, team review, and sandbox workers.

Failure recovery and operational runbooks must be tested. Existing deterministic offline tests must still pass with external model access disabled.

## Acceptance Result

Phase 6 is accepted as a production operations foundation.

Implemented artifacts include production configuration, migration contracts, metadata repositories, durable jobs, worker execution, queue adapters, authentication, authorization, audit records, team review, comments, assignments, chapter locks, object storage, telemetry, backup/restore, project export/import packages, sandbox worker boundaries, container topology, and operational runbooks.

The accepted scope remains infrastructure around the Phase 0-5 service model. Phase 6 does not authorize Phase 7 retrieval, research, graph search, series memory, or cross-book production behavior.

## Next Phase Rule

After Phase 6 passes and the project owner authorizes expansion, create:

```text
docs/info-plan/phases/phase-7-retrieval-research-and-series.md
```

Do not implement Phase 7 behavior from this brief.
