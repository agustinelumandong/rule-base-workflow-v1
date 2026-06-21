# BookForge Start-To-End Testing Guide

**Status:** current Phase 0-8 verification guide
**Scope:** local deterministic test flow, CLI smoke checks, browser workflow smoke checks, and optional containers

Use this guide to verify the current BookForge project from a clean checkout through the local API/review workspace.

## 1. Install Dependencies

```bash
cd /home/cshan28/Dev/Projects/Experimental/BookForge
pip install -e ".[dev]"
python -m playwright install chromium
```

BookForge requires Python 3.11 or newer.

## 2. Run Full Offline Acceptance Tests

```bash
python -m pytest
```

Expected current result:

```text
409 passed
```

This is the main deterministic proof for Phase 0 through Phase 8. It does not require external model access.

## 3. Run Lint Check

```bash
python -m ruff check .
```

Expected result:

```text
All checks passed!
```

## 4. Run CLI Smoke Checks

```bash
python bookforge/cli/app.py --help
python bookforge/cli/app.py policy --help
python bookforge/cli/app.py validate --help
python bookforge/cli/app.py demo --help
```

These commands verify that the CLI entry point and main command groups are importable and wired.

## 5. Seed Demo Project Data

```bash
python bookforge/cli/app.py demo seed project-a --root .bookforge
```

This creates local demo data under `.bookforge` for the review API and browser workspace.

## 6. Run API And Review App

```bash
BOOKFORGE_ALLOW_EXTERNAL_MODELS=false \
BOOKFORGE_STORAGE_ROOT=.bookforge \
python -m uvicorn bookforge.api.app:app --reload
```

Open the browser workspace:

```text
http://127.0.0.1:8000/review-app/
```

You should see the review UI. Use the seeded demo data, or click the UI seed button.

## 7. Run The Browser Author Workflow Smoke Test

```bash
python scripts/smoke_browser_workflow.py
```

This starts a temporary local API server with external models disabled, opens `/review-app/` in Chromium, creates `browser-smoke-book`, imports a chapter, drafts a deterministic candidate, approves it, exports a manuscript, and validates the resulting artifacts, decision, trace, and blocker state.

Use these options when needed:

```bash
python scripts/smoke_browser_workflow.py --headed
python scripts/smoke_browser_workflow.py --storage-root .bookforge-browser-smoke --keep-storage
python scripts/smoke_browser_workflow.py --port 8011
```

To test the browser file picker and export download path with a real local chapter file:

```bash
mkdir -p /tmp/bookforge-downloads
python scripts/smoke_browser_workflow.py \
  --chapter-file chapter1.txt \
  --download-dir /tmp/bookforge-downloads
```

Expected successful output includes these artifacts:

```text
artifact:browser-smoke-book:chapter-001:v1
artifact:browser-smoke-book:chapter-001-draft:v1
artifact:browser-smoke-book:chapter-001-draft-approved:v1
artifact:browser-smoke-book:manuscript-book-1:v1
```

## 8. Optional Container Checks

Run the local Phase 5 API/review-app containers:

```bash
docker compose -f compose.phase5.yaml up --build
```

Run the Phase 6 production-style topology:

```bash
docker compose -f compose.phase6.yaml up --build
```

The containers default to deterministic local behavior:

```text
BOOKFORGE_ALLOW_EXTERNAL_MODELS=false
BOOKFORGE_SANDBOX_NETWORK=false
```

## Short Version

For the core all-phase verification, run:

```bash
python -m pytest && python -m ruff check .
```

Current expected result:

```text
409 passed
All checks passed!
```
