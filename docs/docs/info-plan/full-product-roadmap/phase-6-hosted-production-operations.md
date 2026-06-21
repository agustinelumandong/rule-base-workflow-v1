# Phase 6 Hosted Production Operations Completion

**Current state:** production operations contracts/foundations exist  
**Product-complete state:** hosted/team mode is durable, secure, observable, recoverable, and contract-compatible with local mode.

## Already Done

- [x] Modules exist for production config, migrations, repositories, jobs, queues, workers, object storage, telemetry, backup/restore, auth, authorization, audit, team review, locks, sandbox, and project packages.
- [x] Operational runbooks exist.
- [x] Local queue adapter exists.

## Missing For Full Product

- [ ] Real PostgreSQL-backed repositories used by API/workers.
- [ ] Real Redis or durable queue adapter; current Redis adapter is a placeholder.
- [ ] Durable background worker runtime wired to production jobs.
- [ ] Authentication and authorization enforced on API and UI routes.
- [ ] Team review comments, assignments, and locks exposed in ReviewDesk.
- [ ] Object storage wired for large artifacts while preserving portable project bundles.
- [ ] Backup, restore, retention, and project export tested against real storage.
- [ ] Telemetry dashboards or reports for safe metadata.
- [ ] Recovery tests that interrupt generation, validation, memory update, and export.

## Implementation Checklist

- [ ] Wire PostgreSQL repositories behind the same service contracts used by local file-backed mode.
- [ ] Implement Redis or equivalent queue adapter with tests.
- [ ] Add worker process that executes approved jobs and records resumable state.
- [ ] Add auth middleware and authorization checks for every API route.
- [ ] Add team review UI for comments, assignments, lock ownership, and lock release.
- [ ] Add backup/restore integration tests.
- [ ] Add failure injection tests for interrupted workflow recovery.

## Exit Gate

- [ ] Hosted team mode preserves project isolation, approval rules, artifact portability, audit, and publication gates.
- [ ] Local single-user and hosted team modes use the same application contracts.
- [ ] Security, isolation, recovery, backup, retention, audit, budgets, and observability are tested.
