# CanonForge Local-First Core Engine Plan

## Summary

CanonForge v1 starts as a local-first core engine, not a UI product and not a
CLI product. The first milestone is a file-based Python pipeline that can be
imported, tested, and verified through project-native tests.

This plan supersedes any earlier "CLI first" wording for the first milestone.
The CLI should be added later as a thin wrapper over already-tested engine
functions. A UI, dashboard, or web app should come only after the core engine
and CLI are stable.

## V1 Direction

- Build importable Python modules first.
- Use local files as the operating interface.
- Keep all story inputs and outputs in Markdown, YAML, and JSON.
- Use tests as the first execution surface.
- Prove the core pipeline before adding command wrappers.
- Do not build a UI, dashboard, web app, API server, or CLI in the first
  milestone.

## Deferred Interfaces

### CLI

The CLI is a later wrapper around tested engine functions. It should not own
pipeline behavior, validation rules, path scoping, model routing, or artifact
formats.

When the core engine is proven, CLI commands can call the same public Python
functions used by tests.

### UI And Dashboard

The UI/dashboard is deferred until after the local core engine and CLI are
stable. It should display and operate on existing story artifacts rather than
becoming the source of truth.

No dashboard, web app, SaaS shell, auth layer, queue UI, or review interface is
part of the first milestone.

## First Proof Target

The first proof target remains intentionally small:

- one story
- one bible
- one chapter
- one context package
- one deterministic draft stub
- one QA report
- one diff
- one approval
- one Markdown export

The proof target should be runnable locally through tests without requiring a
CLI, UI, hosted model, external database, or network service.

## Core Principles

- Story identity comes first.
- Bible version comes second.
- Retrieved canon comes before generation.
- Validation comes before approval.
- Human approval comes before final export.
- File artifacts remain auditable and reproducible.
- No cross-story reads are allowed.
- No generated canon change becomes official without approval.

## Acceptance Checks

- This file exists at `docs/local-first-core-engine-plan.md`.
- The plan clearly overrides earlier "CLI first" wording for v1.
- The plan does not start engine implementation work.
- The project remains local-first and file-based.
- CLI and UI are explicitly deferred until after the core engine is proven.
