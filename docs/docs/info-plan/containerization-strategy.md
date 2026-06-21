# BookForge Containerization Strategy

**Status:** implementation strategy  
**Source:** `BOOKFORGE-MASTER-PLAN.md` v2026-06-13  
**Scope:** phased containerization, not a production stack

## Rule

Containerize BookForge in layers, not all at once.

The first container proves deterministic Phase 0/1 behavior. It must not introduce production infrastructure before the engine works.

## Phase Strategy

```text
Phase 0-1:
  one local container for deterministic tests and the file-backed proof engine

Phase 2-3:
  add optional model/provider environment variables
  add a CLI runner container if useful

Phase 5:
  add API container and review-app container

Phase 6:
  add Postgres, worker, object storage, queue, and telemetry
```

Do not start with Kubernetes. Do not start with microservices. Do not start with a production stack before the Phase 0/1 engine works.

## Phase 0-1 Container Goal

The first container should prove:

- Same Python version.
- Same dependencies.
- Same tests.
- Same file-backed artifacts.
- Same deterministic behavior.
- No external model required.

The first container should run:

```bash
pytest
```

and optionally:

```bash
python -m bookforge
```

## Initial Structure

When Phase 0/1 code exists, the first containerization commit should add:

```text
Dockerfile
docker-compose.yml
.dockerignore
.env.example
Makefile
pyproject.toml
```

The first Compose service should be:

```text
bookforge-dev
```

Later services may include:

```text
bookforge-api
bookforge-worker
postgres
redis
minio
review-app
```

Do not create later services during Phase 0/1.

## Initial Dockerfile Target

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

RUN pip install --upgrade pip \
    && pip install -e ".[dev]"

COPY . .

CMD ["pytest", "-q"]
```

If `pyproject.toml` is not ready, a temporary `requirements-dev.txt` is acceptable, but `pyproject.toml` is preferred.

## Initial Docker Compose Target

```yaml
services:
  bookforge-dev:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bookforge-dev
    working_dir: /app
    volumes:
      - .:/app
    environment:
      BOOKFORGE_ENV: development
      BOOKFORGE_STORAGE_ROOT: /app/projects
      BOOKFORGE_ALLOW_EXTERNAL_MODELS: "false"
    command: pytest -q
```

Expected commands:

```bash
docker compose up --build
docker compose run --rm bookforge-dev pytest -q
docker compose run --rm bookforge-dev bash
```

## Initial `.dockerignore`

```dockerignore
.git
.venv
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.coverage
dist
build
*.egg-info

.env
.env.*
.DS_Store

projects/*/exports
projects/*/runs
projects/*/tmp
projects/*/.cache

node_modules
```

Do not ignore docs when docs are part of the planning source.

## Baseline Dependencies

For Phase 0/1, keep dependencies boring:

```toml
[project]
name = "bookforge"
version = "0.1.0"
description = "Human-supervised fiction production engine"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.0",
  "pyyaml>=6.0",
  "rich>=13.0",
  "typer>=0.12",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-cov>=5.0",
  "ruff>=0.5",
  "mypy>=1.10",
]

[project.scripts]
bookforge = "bookforge.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

Do not add LangChain, LlamaIndex, vector databases, FastAPI, Celery, Redis, Postgres, or model SDKs until the assigned phase requires them.

## Verification Commands

The first containerization commit should support:

```makefile
build:
	docker compose build

test:
	docker compose run --rm bookforge-dev pytest -q

shell:
	docker compose run --rm bookforge-dev bash

lint:
	docker compose run --rm bookforge-dev ruff check .

typecheck:
	docker compose run --rm bookforge-dev mypy bookforge

verify:
	docker compose run --rm bookforge-dev sh -c "ruff check . && mypy bookforge && pytest -q"
```

`make verify` becomes the standard container verification command once code exists.

## Later Phase Evolution

### Phase 2-3

Add optional model/provider environment variables only:

```yaml
environment:
  BOOKFORGE_MODEL_PROVIDER: local
  BOOKFORGE_OPENAI_API_KEY: ${BOOKFORGE_OPENAI_API_KEY:-}
  BOOKFORGE_OPENROUTER_API_KEY: ${BOOKFORGE_OPENROUTER_API_KEY:-}
  BOOKFORGE_ALLOW_EXTERNAL_MODELS: "false"
```

The test suite must still pass with:

```text
BOOKFORGE_ALLOW_EXTERNAL_MODELS=false
```

### Phase 5

Only when ReviewDesk exists, add API and review-app containers.

### Phase 6

Only when production operations exist, add Postgres, Redis, object storage, worker, telemetry, backup, and restore services.

## Security Rules

- Never bake secrets into images.
- Keep `.env` and `.env.*` ignored.
- Allow `.env.example`.
- Default external model access to disabled.
- Do not send unnecessary files into Docker build context.

Example `.env.example`:

```bash
BOOKFORGE_ENV=development
BOOKFORGE_STORAGE_ROOT=/app/projects
BOOKFORGE_ALLOW_EXTERNAL_MODELS=false
OPENAI_API_KEY=
OPENROUTER_API_KEY=
```

## First Containerization Milestone

A clean developer can clone the repo, run `docker compose up --build`, and see deterministic Phase 0/1 tests pass without installing Python locally and without using external models.

Do not containerize the future platform yet. Containerize the proof engine first.
