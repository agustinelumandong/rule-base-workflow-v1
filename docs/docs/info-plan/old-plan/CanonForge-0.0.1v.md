# CanonForge Current Workflow And Usage

Version example: `0.0.1`

CanonForge `0.0.1` is a local-first, file-based Python core engine for a
canon-grounded fiction production pipeline. The current version proves the
engine workflow with importable Python modules and tests. It does not include a
CLI, UI, dashboard, API server, database, queue, or hosted model dependency.

## What It Does Today

CanonForge currently proves one deterministic story workflow:

```text
story bible
-> story folder
-> indexed bible chunks
-> chapter context package
-> deterministic draft
-> deterministic humanized chapter
-> QA report
-> diff report
-> approval checkpoint
-> final chapter
-> Markdown story export
```

The built-in proof target is:

- story: `lone-star-reckoning`
- bible version: `version-1`
- chapter: `8`
- source bible: `docs/example-bible.md`
- current package version: `0.0.1`

## Current Features

- Local story initialization from a source bible.
- File-based story structure under `stories/<story_id>/`.
- Bible indexing into versioned local canon chunks.
- Strict context building from retrieved canon chunks.
- Deterministic draft generation through `WriterAgent`.
- Deterministic humanization through `HumanizerAgent`.
- QA reporting through deterministic validators and `QAAgent`.
- AI-ish fiction phrase pattern reporting for reviewer visibility.
- Markdown diff report between draft and humanized chapter.
- Approval checkpoint before final chapter/export.
- Markdown export after approval.
- Trace events written to local JSONL memory.
- Docker and Docker Compose support for runtime and tests.

## Safety Rules

The engine keeps these v1 rules:

- No `story_id`, no generation.
- No `bible_version`, no generation.
- No retrieved canon chunks, no grounded generation.
- No path access outside the configured story root.
- No cross-story reads or fallback.
- No generated canon change becomes official without approval.
- No final export from unapproved chapters.
- No endless retry loops.

## Tech Stack

- Python `>=3.11`
- `uv` for dependency and command execution
- Pydantic v2 for artifact schemas
- PyYAML for YAML artifacts
- pytest for tests
- ruff for linting
- black for formatting checks
- Docker and Docker Compose for containerized runtime/test execution

There is no model server, vector database, web framework, or external service in
the current version.

## Project Architecture

```text
book_system/
  schemas/      artifact contracts
  pipeline/     flow control, context, jobs, paths, approval, orchestration
  stages/       work units that produce artifacts
  agents/       deterministic intelligence used by stages
  rag/          local bible chunking, versioning, retrieval
  validators/   deterministic checks
  storage/      local file read/write/version helpers
  exporters/    deterministic deliverable output
  prompts/      future model prompt contracts
  skills/       prose, continuity, QA, and review guidance
tests/
  unit/
  integration/
  regression/
docs/
```

The public proof API is:

```python
run_lone_star_chapter_08_proof(project_root, source_bible)
```

## Workflow Artifacts

Running the proof pipeline creates a local story tree like this:

```text
stories/lone-star-reckoning/
  config.yaml
  bible/
    version-1/
      chunks.json
  chapters/
    chapter-08/
      context.json
      draft.md
      humanized.md
      qa_report.json
      diff.md
      approval.yaml
      final.md
  exports/
    lone-star-reckoning.md
  memory/
    L1/
      trace.jsonl
```

The export only happens after approval has written `approval.yaml` and
`final.md`.

## How To Use It Locally

Install dependencies:

```bash
uv sync
```

Run the test suite:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
```

Run lint and format checks:

```bash
uv run ruff check .
uv run black --check .
```

Check the current package version:

```bash
uv run python -c "import book_system; print('canonforge', book_system.__version__)"
```

Expected output:

```text
canonforge 0.0.1
```

## Run The Proof Pipeline

Use the importable Python API:

```python
from pathlib import Path

from book_system.pipeline.orchestrator import run_lone_star_chapter_08_proof

result = run_lone_star_chapter_08_proof(
    project_root=Path("/tmp/canonforge-proof"),
    source_bible=Path("docs/example-bible.md"),
)

print(result.status)
print(result.artifacts)
```

Expected status:

```text
exported
```

Example one-liner:

```bash
uv run python - <<'PY'
from dataclasses import asdict
from pathlib import Path
from book_system.pipeline.orchestrator import run_lone_star_chapter_08_proof

result = run_lone_star_chapter_08_proof(
    project_root=Path("/tmp/canonforge-proof"),
    source_bible=Path("docs/example-bible.md"),
)
print(asdict(result))
PY
```

## Docker Usage

Build and run the runtime image:

```bash
docker build --target runtime -t canonforge:local .
docker run --rm canonforge:local
```

Expected output:

```text
canonforge 0.0.1
```

Run tests in Docker:

```bash
docker build --target test -t canonforge:test .
docker run --rm canonforge:test
```

## Docker Compose Usage

Run the runtime service:

```bash
docker compose run --rm canonforge
```

Run the test service:

```bash
docker compose --profile test run --rm test
```

The current Compose setup includes:

- `canonforge`: runtime import/version check
- `test`: pytest service behind the `test` profile
- `canonforge-stories`: named volume reserved for future local story artifacts

Future scalable services such as local model server, vector store, queue, API,
and dashboard are documented as deferred, not active.

## What Is Deferred

These are intentionally not part of `0.0.1`:

- CLI wrapper
- UI or dashboard
- API server
- database
- queue worker
- hosted model integration
- local model server integration
- vector database integration
- DOCX or EPUB export
- multi-user workflow

The intended order is core engine first, then CLI wrapper, then UI/dashboard
after the tested local engine is stable.
