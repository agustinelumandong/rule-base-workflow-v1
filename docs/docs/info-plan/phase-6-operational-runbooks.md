# BookForge Phase 6 Operational Runbooks

**Status:** Phase 6 operations procedure
**Scope:** production-style local/container operations for the Phase 0-6 system

These runbooks describe how to operate the Phase 6 foundation without changing BookForge authority boundaries. Services, queues, databases, object storage, telemetry, and sandbox workers are infrastructure only. Canon truth, approval state, validation decisions, publication readiness, and policy changes must continue to flow through approved services.

## Safety Rules

- Keep `BOOKFORGE_ALLOW_EXTERNAL_MODELS=false` unless the project owner explicitly authorizes external model use for the environment.
- Keep sandbox network access disabled by default with `BOOKFORGE_SANDBOX_NETWORK=false`.
- Do not edit database records by hand to bypass approvals, policy gates, locks, review decisions, or publication gates.
- Treat portable project exports as recovery artifacts. Verify hashes before trusting restored payloads.
- Record operational actions in audit events when they affect projects, artifacts, policy state, jobs, locks, review state, exports, backups, or restores.

## Setup

1. Build the production-style topology with `compose.phase6.yaml`.
2. Provide production configuration through environment variables:
   `BOOKFORGE_ENV`, `BOOKFORGE_DATABASE_URL`, `BOOKFORGE_QUEUE_URL`, `BOOKFORGE_OBJECT_STORAGE_URL`,
   `BOOKFORGE_AUTH_SECRET`, and telemetry settings.
3. Start the infrastructure services: PostgreSQL, Redis or equivalent queue, object storage, API, review app, worker, sandbox, telemetry, and backup.
4. Confirm the API and worker reject missing production secrets before serving requests.
5. Confirm external model access and sandbox network access are disabled unless explicitly authorized.

## Migration

1. Stop job intake before applying migrations.
2. Snapshot the database and object storage before schema changes.
3. Run the Phase 6 migration bootstrapper against the configured database.
4. Verify required metadata tables exist for projects, artifacts, lineage, policies, review decisions, risks, validation findings, traces, jobs, locks, comments, assignments, audit events, and publication gates.
5. Restart job intake after migration verification passes.

## Seed And Demo Data

1. Seed only development or review environments.
2. Use deterministic seed content that keeps external model access disabled.
3. Mark demo users, projects, review decisions, and jobs as demo data.
4. Do not seed production with fake approvals, fake accepted risks, fake publication gates, or fake audit authority.
5. Remove or archive demo data before production acceptance checks.

## Backup

1. Pause destructive maintenance and record the backup start event.
2. Capture database metadata, artifact payloads, policy records, review decisions, traces, jobs, audit references, lock state, and export packages.
3. Store the backup manifest with content hashes, project IDs, object pointers, and timestamped recovery markers.
4. Verify every captured object hash before marking the backup usable.
5. Record backup completion in audit and telemetry.

## Restore

1. Restore into an isolated environment first.
2. Load database metadata and artifact payloads from the backup manifest.
3. Recompute payload hashes and compare them with manifest hashes.
4. Verify approved artifacts, lineage, policies, review decisions, audit references, traces, jobs, and export readiness.
5. Keep job intake disabled until recovery markers and publication gates are verified.
6. Record restore completion and any skipped records in audit and telemetry.

## Worker Recovery

1. Stop the affected worker and leave queue data intact.
2. Inspect telemetry for queue depth, failed job count, retry count, worker health, and recovery markers.
3. Requeue only retryable jobs whose retry limits, budget policy, provider policy, and approval gates still allow execution.
4. Cancel jobs that require unavailable inputs, invalid locks, revoked policy, or expired authorization.
5. Restart workers and verify no unknown job type is executed.

## Failed Job Retry

1. Identify the failed job, registered job type, project scope, artifact scope, retry count, and last recovery state.
2. Confirm the failure is retryable and does not require manual approval, policy weakening, validator bypass, or canon mutation.
3. Requeue through the queue adapter so lifecycle transitions are recorded.
4. Verify audit and telemetry capture the retry, result, and final state.
5. Escalate non-retryable failures to manual review instead of forcing success.

## Incident Rollback

1. Stop job intake and sandbox execution.
2. Preserve current logs, telemetry, audit records, queue state, database snapshot, object storage snapshot, and export packages.
3. Roll back to the last verified migration and backup pair.
4. Restore object payloads only when their hashes match the backup manifest.
5. Reopen review locks and assignments only through the lock and review services.
6. Record the rollback cause, affected projects, affected artifacts, skipped jobs, and recovery result.

## Acceptance Checks

- Full deterministic test suite passes with external model access disabled.
- Ruff passes.
- Migration bootstrap is idempotent.
- Backup and restore round trip preserves hashes, lineage, policies, review decisions, audit references, and recovery markers.
- Worker recovery handles retryable and non-retryable jobs without bypassing policy or approval gates.
- Sandbox worker denies network access by default and cannot mutate canon, policy, memory, locks, or approval state.
