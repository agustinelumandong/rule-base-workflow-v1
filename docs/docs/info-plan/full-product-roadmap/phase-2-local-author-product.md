# Phase 2 Local Author Product Completion

**Current state:** local engine foundation plus project/book/chapter CLI and browser slices  
**Product-complete state:** a real local author can operate the complete book artifact chain without hidden manual steps.

## Already Done

- [x] Project, book, chapter import, deterministic draft, approval, manuscript assembly/export, and ReviewDesk browser smoke flow exist.
- [x] Browser workflow can import `.txt`/`.md` and download an exported Markdown manuscript.
- [x] CLI wrappers exist over many services.
- [x] Versioned artifacts, traces, review records, and local storage are present.
- [x] Structured manuscript import CLI/API preserves chapter source mapping and creates approved preserved-original chapter artifacts.
- [x] Local CLI/API extraction can create reviewable story-bible, character, and canon-fact memory proposals from approved imported chapter artifacts.
- [x] Local CLI/API review can approve or reject extracted memory proposals before promotion.
- [x] Local CLI/API extraction can create reviewable timeline, chapter summary, object state, state fact, and continuity-lock proposals.
- [x] Local CLI/API project intake can create a project/book from concept and constraints.
- [x] Local CLI/API story bible creation can persist a draft bible from an approved intake record.
- [x] Local CLI/API outline creation can validate and persist an outline after a story bible exists.
- [x] Local CLI/API scene-card creation can validate and persist scene cards against a saved outline.

## Missing For Full Product

- [ ] Local commands and UI for sample chapter approval, chapter plans, and book production state.
- [ ] Browser review workflow for approving extracted truth before transformation.
- [ ] Local targeted revision loop that uses findings and preserves clean regions.
- [ ] Local publication gate that blocks export until chapter/book/publication approvals pass.
- [ ] Recovery command for interrupted local workflows.

## Implementation Checklist

- [ ] Add `bookforge/cli/app.py` commands for `sample approve`, `book produce`, and `publication approve`.
- [ ] Add service tests proving CLI handlers remain thin wrappers over services.
- [ ] Extend ReviewDesk workflow to show book production state, not just chapter import/draft/export.
- [ ] Add local smoke script that starts from a concept fixture and exports a multi-chapter approved book.
- [ ] Add local smoke script that imports a structured manuscript, transforms one chapter, approves, and exports.

## Exit Gate

- [ ] A local author can create or transform a complete book through documented CLI/browser steps.
- [ ] Exported manuscript content is generated from approved artifact versions only.
- [ ] The full local workflow is repeatable with `python -m pytest`, `python -m ruff check .`, `npm --prefix review-app run check`, and browser smoke verification.
