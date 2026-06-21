# CanonForge Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the full `docs/roadmap-canonforge.md` roadmap in controlled version phases while preserving CanonForge's local-first, file-based engine rules.

**Architecture:** CanonForge stays an importable Python core engine first. Each phase must add one layer over the existing artifact pipeline, keep deterministic tests passing offline, and stop at a review gate before the next version starts.

**Tech Stack:** Python 3.11+, Pydantic, PyYAML, pytest, ruff, black, Docker Compose, optional future Typer CLI, optional future Ollama/llama.cpp providers, optional future Chroma/FAISS vector stores, optional future LlamaIndex-style adapter.

---

## How To Use This Plan

This is a master implementation checklist for the roadmap in `docs/roadmap-canonforge.md`.

Rules for execution:

- Complete only one version phase at a time.
- Stop after every phase at the marked `STOP GATE`.
- Do not begin the next phase until tests pass, docs are updated, and the project owner approves continuing.
- Keep future version numbers as planning labels until each phase is implemented and tagged.
- Do not add UI, dashboard, database, queue, API server, hosted model dependency, or cross-story retrieval unless the phase explicitly allows it.
- Keep `run_lone_star_chapter_08_proof(project_root, source_bible)` stable unless a later accepted plan explicitly replaces it with a compatibility layer.

## Current Status

| Version | Status | Meaning |
| --- | --- | --- |
| `v0.0.1` | `[x] done` | Local deterministic proof engine exists and is tagged. |
| `v0.0.2` | `[x] done` | Better deterministic output and QA usefulness. |
| `v0.0.3` | `[ ] not started` | CLI wrapper over tested engine functions. |
| `v0.0.4` | `[ ] not started` | Local model routing behind `ModelRouter`. |
| `v0.0.5` | `[ ] not started` | Local vector retrieval / LlamaIndex-style RAG. |
| `v0.0.6` | `[ ] not started` | Real humanization and continuity checks. |
| `v0.0.7` | `[ ] not started` | Benchmarks and evaluation workflow. |
| `v0.1.0` | `[ ] not started` | First usable local author workflow. |
| Later | `[ ] not started` | Dashboard, queue, database, multi-user workflows. |

## Baseline: v0.0.1 Local Deterministic Proof Engine

**Status:** `[x] done`

**Current proof behavior:**

```text
docs/example-bible.md
-> stories/lone-star-reckoning/
-> bible/version-1/chunks.json
-> chapters/chapter-08/context.json
-> chapters/chapter-08/draft.md
-> chapters/chapter-08/humanized.md
-> chapters/chapter-08/qa_report.json
-> chapters/chapter-08/diff.md
-> chapters/chapter-08/approval.yaml
-> chapters/chapter-08/final.md
-> exports/lone-star-reckoning.md
```

**Existing source surface:**

- `book_system/pipeline/orchestrator.py`
- `book_system/stages/*.py`
- `book_system/agents/*.py`
- `book_system/rag/*.py`
- `book_system/validators/*.py`
- `book_system/storage/*.py`
- `book_system/exporters/markdown.py`
- `tests/unit/`
- `tests/integration/test_lone_star_chapter_08_pipeline.py`
- `tests/regression/test_non_negotiable_rules.py`

**Baseline verification:**

- [x] `pyproject.toml` version is `0.0.1`.
- [x] `book_system/__init__.py` version is `0.0.1`.
- [x] Public proof API exists.
- [x] Deterministic tests run offline.
- [x] No CLI/UI/API/database/queue/hosted model is required.

**Re-run before starting any future phase:**

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
uv run ruff check .
uv run black --check .
docker compose --profile test run --rm test
docker compose run --rm canonforge
```

Expected:

```text
47 passed
All checks passed!
56 files would be left unchanged.
canonforge 0.0.1
```

### STOP GATE: v0.0.1

- [x] Stop here unless the user explicitly starts `v0.0.2`.
- [x] Do not backfill CLI, UI, model, RAG, database, or queue work into `v0.0.1`.

---

## Phase v0.0.2: Better Engine Output And QA Usefulness

**Status:** `[x] done`

**Goal:** Make the deterministic artifacts more useful to read while keeping the engine local, file-based, and model-free.

**Allowed changes:**

- Improve deterministic draft structure.
- Improve deterministic humanization cleanup.
- Improve QA report readability.
- Add richer fixtures for clean and bad chapters.
- Preserve current artifact paths and public proof API.

**Still not allowed:**

- No CLI.
- No UI.
- No API server.
- No hosted model.
- No vector database.
- No database.
- No cross-story retrieval.

### Task 1: Add Chapter Plan Coverage To Deterministic Drafts

**Files:**

- Modify: `book_system/agents/writer_agent.py`
- Modify: `tests/unit/test_writer_agent.py`
- Check: `book_system/schemas/context.py`

- [x] **Step 1: Read the current context schema**

Run:

```bash
sed -n '1,220p' book_system/schemas/context.py
sed -n '1,220p' tests/unit/test_writer_agent.py
```

Expected: identify the exact fields available on `ChapterContext`, especially `current_chapter_plan` and `retrieved_canon_chunks`.

- [x] **Step 2: Write failing tests for richer draft structure**

Add tests proving `WriterAgent.write_draft()` includes:

- chapter title
- chapter summary
- required beats when present
- grounding section with retrieved chunk IDs
- no draft when retrieved chunks are empty

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/unit/test_writer_agent.py -q
```

Expected: new tests fail before implementation.

- [x] **Step 3: Implement deterministic draft expansion**

Update `WriterAgent.write_draft()` to produce a stable Markdown artifact:

```text
# Chapter N: Title

## Draft

[deterministic chapter-like prose based on summary and beats]

## Required Beats Covered

- beat text

## Grounding

- story_id: ...
- bible_version: ...
- retrieved_chunk_ids:
  - ...

## Generation Notes

- model: deterministic-stub
- prompt_version: write_scene_v2
```

Implementation rules:

- Use only fields already present in `ChapterContext`.
- Do not invent new canon facts.
- Do not call a model.
- Keep output deterministic.

- [x] **Step 4: Verify draft tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/unit/test_writer_agent.py -q
```

Expected: all writer tests pass.

### Task 2: Improve Deterministic Humanization Without Canon Changes

**Files:**

- Modify: `book_system/agents/humanizer_agent.py`
- Modify: `tests/unit/test_stages.py`
- Add or modify: `tests/unit/test_humanizer_agent.py`

- [x] **Step 1: Read current humanizer behavior**

Run:

```bash
sed -n '1,220p' book_system/agents/humanizer_agent.py
sed -n '1,260p' tests/unit/test_stages.py
```

Expected: confirm whether humanization is pass-through or deterministic cleanup.

- [x] **Step 2: Add tests for safe cleanup**

Test deterministic cleanup for:

- repeated blank lines
- obvious AI-ish filler phrases already covered by skill guidance
- preservation of headings
- preservation of `story_id`, `bible_version`, and retrieved chunk IDs

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/unit/test_humanizer_agent.py tests/unit/test_stages.py -q
```

Expected: new cleanup tests fail before implementation if behavior is missing.

- [x] **Step 3: Implement minimal cleanup**

Implementation rules:

- Do not rewrite plot facts.
- Do not change names.
- Do not change canon references.
- Do not remove grounding notes.
- Keep deterministic behavior.

- [x] **Step 4: Verify humanizer tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/unit/test_humanizer_agent.py tests/unit/test_stages.py -q
```

Expected: all humanizer and stage tests pass.

### Task 3: Make QA Reports Easier To Review

**Files:**

- Modify: `book_system/agents/qa_agent.py`
- Modify: `book_system/schemas/qa_report.py` only if existing fields are insufficient
- Modify: `tests/unit/test_qa_agent.py`
- Modify: `tests/unit/test_validators.py`

- [x] **Step 1: Read QA schema and tests**

Run:

```bash
sed -n '1,220p' book_system/schemas/qa_report.py
sed -n '1,260p' tests/unit/test_qa_agent.py
sed -n '1,260p' tests/unit/test_validators.py
```

Expected: identify existing issue fields: type, severity, evidence, recommendation.

- [x] **Step 2: Add tests for reviewer-friendly issues**

Test that QA report output includes:

- stable issue type strings
- severity
- evidence
- recommendation
- passed checks
- failed checks
- `needs_review` for low/medium prose-pattern issues
- exception only for critical issues

- [x] **Step 3: Implement QA readability improvements**

Implementation rules:

- Prefer improving issue evidence/recommendations in validators before adding schema fields.
- Do not change high/critical behavior unless tests show the current behavior is wrong.
- Keep `qa_report.json` Pydantic-serializable.

- [x] **Step 4: Verify QA tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/unit/test_qa_agent.py tests/unit/test_validators.py -q
```

Expected: QA and validator tests pass.

### Task 4: Verify Full v0.0.2 Pipeline

- [x] **Step 1: Run full local checks**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
uv run ruff check .
uv run black --check .
docker compose --profile test run --rm test
```

Expected: all checks pass offline.

- [x] **Step 2: Run proof pipeline manually**

Run:

```bash
rm -rf /tmp/canonforge-proof
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

Expected:

```text
'status': 'exported'
'story_id': 'lone-star-reckoning'
'chapter_number': 8
```

- [x] **Step 3: Inspect artifacts**

Run:

```bash
sed -n '1,180p' /tmp/canonforge-proof/stories/lone-star-reckoning/chapters/chapter-08/draft.md
sed -n '1,220p' /tmp/canonforge-proof/stories/lone-star-reckoning/chapters/chapter-08/qa_report.json
```

Expected: draft and QA report are more useful than the `v0.0.1` stub, while preserving required artifact paths.

### STOP GATE: v0.0.2

- [x] Mark `v0.0.2` done in this plan only after verification passes.
- [x] Update `docs/roadmap-canonforge.md` current-status language only if the version is actually tagged.
- [x] Update `docs/CanonForge-0.0.1v.md` or create the next version doc only if the project owner wants a release note.
- [x] Do not start CLI work until the user explicitly approves `v0.0.3`.

---

## Phase v0.0.3: CLI Wrapper

**Status:** `[ ] not started`

**Goal:** Add a thin Typer-based CLI over tested engine functions without moving business logic into command handlers.

**Allowed changes:**

- Add optional Typer dependency.
- Add CLI module and command tests.
- Expose existing engine stages through commands.
- Keep tests passing without model servers or services.

**Still not allowed:**

- No dashboard.
- No API server.
- No database.
- No queue.
- No hosted model requirement.

### Task 1: Add Typer Dependency And CLI Entry Point

**Files:**

- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `book_system/cli.py`
- Create: `tests/unit/test_cli.py`

- [ ] **Step 1: Add Typer with uv**

Run:

```bash
uv add "typer>=0.12,<1"
```

Expected: `pyproject.toml` and `uv.lock` update.

- [ ] **Step 2: Add console script**

Update `pyproject.toml`:

```toml
[project.scripts]
canonforge = "book_system.cli:app"
```

- [ ] **Step 3: Create a minimal CLI app**

Create `book_system/cli.py` with a Typer app that can print the package version:

```python
import typer

from book_system import __version__

app = typer.Typer(no_args_is_help=True)


@app.command()
def version() -> None:
    typer.echo(f"canonforge {__version__}")
```

- [ ] **Step 4: Test version command**

Add `tests/unit/test_cli.py` using `typer.testing.CliRunner`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/unit/test_cli.py -q
```

Expected: CLI version test passes.

### Task 2: Wrap Proof Pipeline

**Files:**

- Modify: `book_system/cli.py`
- Modify: `tests/unit/test_cli.py`

- [ ] **Step 1: Add a proof command**

Command shape:

```text
canonforge proof lone-star-chapter-08 --project-root /tmp/canonforge-proof --source-bible docs/example-bible.md
```

Implementation rule: call `run_lone_star_chapter_08_proof()` directly.

- [ ] **Step 2: Test proof command with temporary directory**

Test that command output includes:

```text
status=exported
story_id=lone-star-reckoning
chapter_number=8
```

- [ ] **Step 3: Verify no business logic lives in CLI**

Check:

```bash
sed -n '1,260p' book_system/cli.py
```

Expected: command handlers parse arguments and call engine functions only.

### Task 3: Add Stage-Level Commands Only Where Engine APIs Exist

**Files:**

- Modify: `book_system/cli.py`
- Modify: `tests/unit/test_cli.py`
- Modify or add pipeline service files only if a command needs a public function wrapper.

- [ ] **Step 1: List existing stage functions**

Run:

```bash
for f in book_system/stages/*.py; do echo "$f"; rg -n "^def " "$f"; done
```

Expected: know which stage functions are stable enough to wrap.

- [ ] **Step 2: Add commands incrementally**

Add only commands that call existing engine behavior:

```text
canonforge index-bible
canonforge build-context
canonforge draft-chapter
canonforge humanize-chapter
canonforge check-chapter
canonforge diff-chapter
canonforge approve-chapter
canonforge export-story
```

- [ ] **Step 3: Add tests per command**

Each test should prove:

- path arguments are accepted
- the command exits `0` on valid input
- invalid input returns nonzero
- approval cannot be bypassed for export

### STOP GATE: v0.0.3

- [ ] Run full verification.
- [ ] Confirm CLI is only a wrapper.
- [ ] Confirm proof API still works.
- [ ] Do not start model-provider work until the user explicitly approves `v0.0.4`.

---

## Phase v0.0.4: Local Model Routing

**Status:** `[ ] not started`

**Goal:** Add optional local model providers behind `ModelRouter` while keeping deterministic fallback as the default test path.

**Allowed changes:**

- Add provider protocols.
- Add optional Ollama provider.
- Add optional llama.cpp-compatible provider if it has a stable local interface.
- Add model trace metadata.
- Keep CI and default tests offline.

**Still not allowed:**

- No required cloud model.
- No dashboard.
- No database.
- No queue.
- No endless retries.

### Task 1: Strengthen Model Provider Contract

**Files:**

- Modify: `book_system/pipeline/model_router.py`
- Modify: `tests/unit/test_model_router.py`
- Add: `book_system/schemas/model.py` if persisted trace metadata needs schema validation.

- [ ] **Step 1: Add tests for provider selection**

Test:

- deterministic provider remains default
- unknown provider raises `ModelRouterError`
- task-specific routing returns expected provider
- trace metadata includes provider, model, task, and deterministic flag

- [ ] **Step 2: Update `ModelRouter`**

Implementation rules:

- No network call in constructor.
- No provider should be selected by guessing missing task names.
- Unknown provider errors must be explicit.

### Task 2: Add Optional Ollama Provider

**Files:**

- Add: `book_system/models/__init__.py`
- Add: `book_system/models/ollama.py`
- Add: `tests/unit/test_ollama_provider.py`

- [ ] **Step 1: Implement provider behind optional environment config**

Expected environment variables:

```text
CANONFORGE_MODEL_PROVIDER=ollama
CANONFORGE_OLLAMA_BASE_URL=http://localhost:11434
CANONFORGE_OLLAMA_MODEL=llama3.1
```

Rules:

- Unit tests mock HTTP.
- Default test suite must not require Ollama running.
- Provider must return clear errors on connection failure.

- [ ] **Step 2: Add opt-in integration marker**

Add pytest marker or environment-gated test so local model tests run only when explicitly enabled.

### Task 3: Integrate ModelRouter Into Agents Without Requiring Models

**Files:**

- Modify: `book_system/agents/writer_agent.py`
- Modify: `book_system/agents/humanizer_agent.py`
- Modify: `book_system/agents/qa_agent.py`
- Modify: `tests/unit/test_writer_agent.py`
- Modify: `tests/unit/test_qa_agent.py`

- [ ] **Step 1: Add dependency injection**

Agents should accept an optional router/provider but default to deterministic behavior.

- [ ] **Step 2: Test deterministic fallback**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest tests/unit/test_writer_agent.py tests/unit/test_qa_agent.py tests/unit/test_model_router.py -q
```

Expected: tests pass without model services.

### STOP GATE: v0.0.4

- [ ] Run full verification.
- [ ] Confirm default tests pass offline.
- [ ] Confirm model calls are optional.
- [ ] Confirm model trace metadata appears in generated artifacts where relevant.
- [ ] Do not start vector retrieval until the user explicitly approves `v0.0.5`.

---

## Phase v0.0.5: Local Vector Retrieval / LlamaIndex-Style RAG

**Status:** `[ ] not started`

**Goal:** Add local vector retrieval while preserving per-story and per-bible-version isolation.

**Allowed changes:**

- Add embedding protocol.
- Add deterministic embedding fallback.
- Add local Chroma or FAISS adapter.
- Store per-story index metadata locally.
- Borrow LlamaIndex-style concepts without requiring LlamaIndex immediately.

**Still not allowed:**

- No global cross-story search.
- No hosted vector database.
- No generation without retrieved canon chunks.
- No immediate hard dependency on LlamaIndex unless a separate approved plan chooses it.

### Task 1: Define Retrieval Interfaces

**Files:**

- Add: `book_system/rag/embeddings.py`
- Add: `book_system/rag/index.py`
- Modify: `book_system/rag/retriever.py`
- Add: `tests/unit/test_embeddings.py`
- Add: `tests/unit/test_vector_index.py`

- [ ] **Step 1: Add tests for deterministic embeddings**

Test:

- same text produces same vector
- different text produces different vector
- no network is required

- [ ] **Step 2: Add tests for per-story index metadata**

Test:

- index stores `story_id`
- index stores `bible_version`
- mismatched story raises `StoryIdentityError`
- mismatched bible version raises `BibleVersionError`

### Task 2: Add Local Vector Adapter

**Files:**

- Add: `book_system/rag/vector_store.py`
- Add: `tests/unit/test_vector_store.py`
- Modify: `pyproject.toml` only if the chosen adapter is added as an optional dependency group.

- [ ] **Step 1: Choose first adapter**

Decision rule:

- Prefer Chroma first if local persistence and metadata filtering are needed now.
- Prefer FAISS first if minimal local similarity search is enough and metadata can remain in CanonForge files.

- [ ] **Step 2: Keep deterministic fallback**

Existing lexical retrieval in `book_system/rag/retriever.py` must remain available for tests and emergency fallback.

### Task 3: Add LlamaIndex-Style Adapter Boundary

**Files:**

- Add: `book_system/rag/llamaindex_adapter.py` only if the internal retrieval contract is stable.
- Add: `tests/unit/test_llamaindex_adapter.py` only if adapter file is added.

- [ ] **Step 1: Implement adapter as optional**

Rules:

- CanonForge code imports must not fail when LlamaIndex is not installed.
- Adapter must translate CanonForge chunk metadata into retriever inputs.
- Adapter must preserve `story_id`, `bible_version`, and chunk IDs.

### STOP GATE: v0.0.5

- [ ] Run full verification.
- [ ] Confirm no cross-story retrieval.
- [ ] Confirm lexical fallback still passes.
- [ ] Confirm generation still blocks when no canon chunks are retrieved.
- [ ] Do not start real humanization/continuity work until the user explicitly approves `v0.0.6`.

---

## Phase v0.0.6: Real Humanization And Continuity Checks

**Status:** `[ ] not started`

**Goal:** Add useful model-backed prose and continuity review while preserving canon safety and approval gates.

**Allowed changes:**

- Model-backed humanizer behind `ModelRouter`.
- Report-only continuity checker.
- Prompt version tracking.
- Stronger hallucination/canon drift reporting.

**Still not allowed:**

- No autonomous canon mutation.
- No UI approval source of truth.
- No database authority over artifacts.

### Task 1: Add Prompt Version Trace

**Files:**

- Modify: `book_system/schemas/trace.py`
- Modify: `book_system/stages/humanize_chapter.py`
- Modify: `book_system/stages/qa_chapter.py`
- Add or modify: `tests/unit/test_trace.py`

- [ ] **Step 1: Test trace metadata**

Trace should include:

- stage name
- model provider
- model name
- prompt file
- prompt version
- input artifact paths
- output artifact paths

### Task 2: Add Continuity Report Stage

**Files:**

- Modify: `book_system/agents/continuity_agent.py`
- Add: `book_system/stages/continuity_stage.py`
- Add: `tests/unit/test_continuity_agent.py`
- Add: `tests/unit/test_continuity_stage.py`

- [ ] **Step 1: Test report-only behavior**

Continuity checks must report issues without silently rewriting chapter text.

- [ ] **Step 2: Test approval blocking for high-risk canon issues**

High-risk canon drift should block approval; low-risk prose notes should not.

### Task 3: Add Model-Backed Humanization Option

**Files:**

- Modify: `book_system/agents/humanizer_agent.py`
- Modify: `tests/unit/test_humanizer_agent.py`

- [ ] **Step 1: Keep deterministic default**

Default tests must still run without local model service.

- [ ] **Step 2: Add optional provider path**

Humanizer may call a model only when explicitly configured.

### STOP GATE: v0.0.6

- [ ] Run full verification.
- [ ] Confirm continuity does not mutate canon.
- [ ] Confirm approval still blocks unsafe exports.
- [ ] Confirm deterministic fallback works offline.
- [ ] Do not start benchmarking until the user explicitly approves `v0.0.7`.

---

## Phase v0.0.7: Benchmarks And Evaluation Workflow

**Status:** `[ ] not started`

**Goal:** Add repeatable evaluation for quality, grounding, speed, and cost before scaling the workflow.

**Allowed changes:**

- Add benchmark fixtures.
- Add opt-in benchmark commands or tests.
- Add benchmark output artifacts.
- Compare provider/prompt versions.

**Still not allowed:**

- No production queue.
- No dashboard requirement.
- No cloud-only benchmark path.

### Task 1: Add Evaluation Schema

**Files:**

- Add: `book_system/schemas/evaluation.py`
- Add: `book_system/evaluation/__init__.py`
- Add: `book_system/evaluation/metrics.py`
- Add: `tests/unit/test_evaluation_metrics.py`

- [ ] **Step 1: Define metrics**

Metrics:

- canon drift count
- unresolved QA issue count
- required beat coverage
- output length
- elapsed time
- provider name
- model name
- prompt version
- estimated cost when available

### Task 2: Add Benchmark Fixtures

**Files:**

- Add: `tests/fixtures/benchmark_bibles/`
- Add: `tests/fixtures/benchmark_chapters/`
- Add: `tests/regression/test_benchmark_workflow.py`

- [ ] **Step 1: Create deterministic fixture cases**

Create fixture cases for:

- clean chapter
- missing required beat
- canon drift
- AI-pattern-heavy prose
- continuity conflict

### Task 3: Add Opt-In Benchmark Runner

**Files:**

- Add: `book_system/evaluation/runner.py`
- Add: `tests/unit/test_evaluation_runner.py`

- [ ] **Step 1: Keep benchmark opt-in**

Default `pytest` should stay fast and deterministic.

- [ ] **Step 2: Add command**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m book_system.evaluation.runner
```

Expected: writes benchmark output under a local generated folder, not inside source unless explicitly configured.

### STOP GATE: v0.0.7

- [ ] Run full verification.
- [ ] Confirm default test suite remains deterministic and fast.
- [ ] Confirm benchmark outputs are ignored or placed outside source.
- [ ] Do not start `v0.1.0` workflow packaging until the user explicitly approves it.

---

## Phase v0.1.0: First Usable Local Author Workflow

**Status:** `[ ] not started`

**Goal:** Make CanonForge useful for a real single-user local author workflow.

**Expected capabilities:**

- Initialize a story project.
- Ingest and version a bible.
- Build grounded chapter context.
- Generate or rewrite one or more chapters.
- Run deterministic and optional model-backed QA.
- Produce reviewable diffs.
- Require approval before final export.
- Export Markdown.
- Operate through CLI.
- Remain local-first and file-based.

### Task 1: Stabilize Public Engine APIs

**Files:**

- Modify: `book_system/pipeline/orchestrator.py`
- Add: `book_system/pipeline/workflow.py`
- Add: `tests/integration/test_author_workflow.py`

- [ ] **Step 1: Define workflow functions**

Add public workflow functions for:

- story initialization
- bible indexing
- chapter context build
- chapter draft
- humanization
- QA
- diff
- approval
- export

Rules:

- Functions take explicit `Path`, `story_id`, `bible_version`, and `chapter_number`.
- Functions never infer missing identity.
- Functions return typed dataclasses or Pydantic models.

### Task 2: Make CLI Cover The Workflow

**Files:**

- Modify: `book_system/cli.py`
- Modify: `tests/unit/test_cli.py`
- Add: `tests/integration/test_cli_author_workflow.py`

- [ ] **Step 1: Add integration test**

Test a real local author workflow from CLI commands using a temporary folder.

- [ ] **Step 2: Verify artifact chain**

Expected outputs:

```text
context.json
draft.md
humanized.md
qa_report.json
diff.md
approval.yaml
final.md
exports/<story_id>.md
```

### Task 3: Write v0.1.0 Usage Documentation

**Files:**

- Add: `docs/CanonForge-0.1.0v.md`
- Modify: `README.md`
- Modify: `docs/roadmap-canonforge.md`

- [ ] **Step 1: Document exact workflow commands**

Documentation must say:

- what files are inputs
- what files are outputs
- what commands run the workflow
- what still does not exist
- how to run without local models
- how to enable optional local models

### STOP GATE: v0.1.0

- [ ] Run full verification.
- [ ] Run proof pipeline.
- [ ] Run CLI workflow.
- [ ] Update version to `0.1.0` only after project owner approves release.
- [ ] Create tag only after version files, docs, tests, and Docker checks match.
- [ ] Do not start dashboard/database/queue/multi-user work until local author workflow is proven useful.

---

## Later Phase: Dashboard, Queue, Database, Multi-User

**Status:** `[ ] not started`

**Goal:** Add operational layers only after the local engine and CLI are useful.

**Allowed later work:**

- Queue support for many chapters.
- Dashboard for status and review.
- Database for indexed metadata if file folders become painful.
- Cost and token tracking.
- Multi-user permissions.
- Web app or SaaS workflow.
- Global search only after per-story isolation is proven.

**Hard rules:**

- Later layers operate on engine artifacts.
- Later layers must not become the first source of truth too early.
- Later layers must not bypass approval.
- Later layers must not weaken story isolation.

### Later Task 1: Write A Separate Product Architecture Plan

**Files:**

- Add: `docs/superpowers/plans/YYYY-MM-DD-canonforge-dashboard-queue-database-plan.md`

- [ ] **Step 1: Plan before code**

Before any later-layer implementation, write a new plan covering:

- API boundary
- worker/queue boundary
- dashboard artifact read model
- database role, if any
- migration strategy from file artifacts
- permission model
- story isolation model
- approval gate preservation

### STOP GATE: Later Phase

- [ ] Do not implement later layers from this master plan alone.
- [ ] Require a new source-backed implementation plan before code.

---

## Release Checklist Template

Use this checklist at the end of every version phase.

- [ ] All phase tests pass.
- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] Black check passes.
- [ ] Docker test service passes.
- [ ] Runtime Docker/Compose check passes when relevant.
- [ ] README is updated if usage changed.
- [ ] Version-specific docs are updated if behavior changed.
- [ ] Roadmap status is updated only if the release is actually done.
- [ ] No banned scope was added early.
- [ ] Public proof API still works or has a documented compatibility path.
- [ ] Project owner approves moving to the next phase.

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
uv run ruff check .
uv run black --check .
docker compose --profile test run --rm test
docker compose run --rm canonforge
```

## Master Stop Rule

After every phase, stop and report:

```text
Version completed:
Files changed:
Tests run:
Artifacts produced:
Rules preserved:
Known limitations:
Recommended next phase:
Waiting for approval before continuing:
```

Do not continue into the next version automatically.
