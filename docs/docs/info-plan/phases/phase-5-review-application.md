# BookForge Phase 5 Review Application Brief

**Status:** accepted local implementation
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13
**Scope:** local FastAPI service layer and browser review workspace over approved Phase 0-4 services

## Rule

Phase 5 turns the existing local services into a reviewable application surface. It may add a FastAPI boundary, browser workspace, API/UI containers, read-only visualizations, and reviewer actions that call the existing application services.

Phase 5 must not replace the artifact directory as the authoritative portable record. Artifacts, policy snapshots, approvals, traces, validation findings, and assembled manuscripts remain durable content records produced by the service layer. UI and API code are surfaces over those records, not competing workflow engines.

Browser actions must map to existing services. The review application may make work easier to inspect and approve, but it must not weaken canon authority, validation gates, policy floors, model budgets, artifact lineage, or publication approval.

## Scope Clarification

This brief defines the authorized Phase 5 implementation scope after Phase 4 acceptance. It does not authorize Phase 6 production operations.

Phase 5 may add local API and browser application structure, local development containers for the API and review app, derived read models, reviewer action routes, and browser views for planning, chapters, diffs, findings, approval, policy inspection, run status, recovery, and export.

Phase 5 must not add PostgreSQL, Redis, production migrations, durable workers, queues, object storage, authentication, authorization, billing, tenancy, hosted collaboration, production telemetry, backup/restore systems, vector or graph stores, unrestricted external research automation, or series-level production behavior.

Phase 6 remains unauthorized until Phase 5 passes and the project owner authorizes the next implementation brief.

## Required Work

- FastAPI service boundary that exposes existing application services without duplicating workflow rules.
- API routes for projects, books, planning artifacts, chapters, validation findings, review decisions, approvals, final-polish records, manuscript assembly status, export records, run traces, and recovery state.
- Browser workspace for project overview, planning review, chapter review, diff review, validation findings, approvals, final polish, and export readiness.
- Browser policy inspection views for project and book settings, style, canon, memory, knowledge, skill and prompt policy, providers, validation, review, security, budgets, and export profiles.
- Reviewer action flow for approve, reject, accept-risk, and request-revision actions using existing approval and review services.
- Accept-risk flow requiring reviewer identity, reason, timestamp, artifact version, finding IDs, and policy snapshot.
- Diff view supporting side-by-side and unified text comparison for approved source artifacts and candidate revisions.
- Semantic change summary view showing added, removed, or changed facts where available from existing findings or event proposals.
- Traceability view showing model provider, model ID, prompt ID, persona, capability, context package, budget usage, validation findings, and input/output artifacts.
- Run status and recovery controls over existing resumable execution state, with no hidden background worker requirement.
- Read-only timeline, relationship, setup/payoff, chapter dependency, canon-conflict, validation severity, cost, and throughput visualizations derived from approved records.
- Local API and review-app development containers following `containerization-strategy.md`.
- Documentation for running the API, browser app, deterministic tests, and local containers.

## Suggested Module Boundaries

Keep workflow authority in services. API handlers, UI actions, and container entrypoints must remain thin adapters.

```text
bookforge/api/
  __init__.py
  app.py
  routes/
    projects.py
    planning.py
    chapters.py
    findings.py
    review.py
    policies.py
    runs.py
    exports.py
  read_models/
    review_workspace.py
    visualizations.py

review-app/
  package.json
  src/

containers/
  api.Dockerfile
  review-app.Dockerfile
```

These names are guidance, not mandatory filenames. Use existing project layout if a better local pattern emerges.

## Required Tests

- API routes call existing services and do not duplicate approval, validation, assembly, export, or policy rules.
- API rejects wrong-project artifact access and cross-project IDs.
- API rejects stale artifact versions, stale policy snapshots, missing approvals, and invalid review transitions.
- Reviewer approval creates the same approval records as the service layer and remains tied to exact artifact versions.
- Reject and request-revision actions create review records without mutating canon, memory, locks, or publication state.
- Accept-risk requires reviewer identity, reason, timestamp, finding IDs, artifact version, and policy snapshot.
- Publication approval cannot be removed or bypassed through API or UI action.
- Browser project and book views load only derived data from service-backed records.
- Planning, chapter, diff, findings, approval, final-polish, and export views render required artifact lineage and blocker state.
- Diff views refuse missing source artifacts, stale revisions, and unapproved source versions where policy requires approval.
- Traceability views display provider, model, prompt, persona, capability, context, budget, validation, and artifact metadata.
- Policy views are read-only unless backed by existing controlled policy update services.
- Visualizations are read-only derived views and cannot mutate canon, timeline, relationships, setup/payoff, or conflict records.
- Run recovery controls operate only on recorded deterministic execution state and do not create hidden worker state.
- API and review-app local containers start without secrets and default external model access to disabled.
- Existing offline deterministic tests still pass with model features disabled.

## Must Not Build In Phase 5

- PostgreSQL, Redis, production migrations, object storage, background workers, queues, or production deployment.
- Authentication, authorization, hosted collaboration, comments/assignments, chapter locking, billing, tenancy, or marketplace behavior.
- Production telemetry, backup, restore, retention automation, or operational runbooks.
- Vector store, graph store, RAG service, unrestricted research automation, or full retrieval platform.
- Series-level memory, cross-book production engine, or advanced research workflows.
- Model autonomy for approval, publication readiness, canon mutation, memory promotion, lock mutation, policy weakening, or validator bypass.
- Writable visualization state that can become canon, timeline, relationship, setup/payoff, or conflict truth.

## Acceptance

Phase 5 is accepted when BookForge can be reviewed through a local browser workspace and FastAPI boundary while all meaningful actions still route through existing services.

The application must show project, planning, chapter, diff, findings, approval, policy, run, and export state with clear artifact lineage and blocker visibility. Reviewer actions must preserve exact-version approvals, accepted-risk evidence, policy floors, validation gates, and publication approval.

Artifacts remain portable authoritative records. Read-only visualizations remain derived from approved records. Existing deterministic offline tests must pass, and local API/UI containers must start with external model access disabled by default.

## Acceptance Review

**Reviewed:** 2026-06-14

Phase 5 is accepted for the local-first review application scope:

- FastAPI routes expose project, book, planning, chapter, diff/finding, review, policy, run, trace, export, final-polish, and demo-seed surfaces over existing services.
- Browser ReviewDesk shows project overview, planning, chapters, diffs, blockers, review decisions, policy categories, run traces, recovery state, export readiness, and read-only artifact lineage.
- Reviewer actions use service-backed review decision records and preserve exact artifact version, reviewer identity, timestamp, finding IDs, accepted-risk reason, and policy snapshot.
- Policy category views and artifact visualizations are read-only derived views.
- Demo seed data is deterministic and local, creating portable artifacts, diffs, traces, policy settings, and review decisions under the configured storage root.
- Local API and review-app containers default `BOOKFORGE_ALLOW_EXTERNAL_MODELS=false`.
- No Phase 6 production infrastructure was added: no database, durable worker, queue, object storage, authentication, authorization, telemetry, backup/restore, vector store, graph store, or hosted collaboration.
- Verified with `python -m pytest`, `python -m ruff check .`, and `npm --prefix review-app run check`.

## Next Phase Rule

After Phase 5 passes and the project owner authorizes expansion, create:

```text
docs/info-plan/phases/phase-6-production-operations.md
```

Do not implement Phase 6 behavior from this brief.
