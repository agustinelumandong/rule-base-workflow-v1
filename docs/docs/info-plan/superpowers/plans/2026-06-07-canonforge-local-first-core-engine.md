# CanonForge Local-First Core Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build CanonForge as a local-first, file-based Python core engine that can prove one canon-grounded chapter pipeline end to end before adding any CLI, UI, dashboard, hosted service, database, or autonomous agent layer.

**Architecture:** CanonForge v1 is an importable Python package with typed services, Pydantic schemas for persisted artifacts, deterministic modules for path safety, bible indexing, retrieval, context building, drafting stubs, validation, diffing, approval, trace logging, memory updates, and Markdown export. Tests are the first execution surface; CLI commands are a later wrapper over the same public engine functions.

**Tech Stack:** Python 3.11+, `uv`, Pydantic, PyYAML, pytest, Ruff, Black, pathlib, dataclasses, Markdown/YAML/JSON/JSONL artifacts, local files only for v1.

---

## Source Of Truth

Implement against these docs in this order:

1. `docs/local-first-core-engine-plan.md` overrides any earlier CLI-first wording.
2. `CanonForge.md` defines engine contracts, artifact formats, build order, and non-negotiable rules.
3. `docs/my-plan-to-build.md` defines broader product intent: controlled automation, story bible discipline, human review, humanization, diff review, local-first scaling.

Hard v1 constraints:

- No CLI in the first milestone.
- No UI, dashboard, web app, API server, auth, queue, or database in the first milestone.
- No network services or hosted models required for the first proof target.
- No generation without `story_id`, `bible_version`, and retrieved canon chunks.
- No story worker may read or write outside its `allowed_root`.
- No cross-story fallback.
- No unapproved chapter can be exported.
- No endless retry loop.

## Target V1 Proof

The first completed implementation must pass one integration test that performs this local-only flow:

```text
docs/example-bible.md
-> stories/lone-star-reckoning/
-> bible/version-1/chunks.json
-> chapters/chapter-08/context.json
-> chapters/chapter-08/draft.md
-> chapters/chapter-08/qa_report.json
-> chapters/chapter-08/diff.md
-> chapters/chapter-08/approval.yaml
-> chapters/chapter-08/final.md
-> exports/lone-star-reckoning.md
```

The test must prove the Chapter 8 context retrieves Darin Mayweather, Jed "Deadeye" Harlan, Act 2, Chapter 8, and Western style rules from `docs/example-bible.md`.

## Planned File Structure

Create this structure during implementation:

```text
pyproject.toml
README.md
book_system/
  __init__.py
  pipeline/
    __init__.py
    approval.py
    context_builder.py
    diff.py
    errors.py
    events.py
    exporter.py
    jobs.py
    orchestrator.py
    paths.py
    story_template.py
  rag/
    __init__.py
    bible_indexer.py
    chunker.py
    retriever.py
    versioning.py
  agents/
    __init__.py
    writer_agent.py
    humanizer_agent.py
    continuity_agent.py
    diff_agent.py
    qa_agent.py
    export_agent.py
  validators/
    __init__.py
    bible_version_validator.py
    forbidden_words_validator.py
    path_scope_validator.py
    retrieved_chunk_validator.py
    story_identity_validator.py
    structure_validator.py
    word_count_validator.py
  schemas/
    __init__.py
    approval.py
    chunk.py
    context.py
    job.py
    qa_report.py
    story_config.py
    trace.py
  prompts/
    write_scene.md
    humanize_chapter.md
    check_continuity.md
    summarize_chapter.md
    diff_summary.md
    create_story_bible.md
    build_chapter_plan.md
  skills/
    western_dialogue.md
    prose_humanization.md
    continuity_checking.md
    hallucination_detection.md
    diff_review.md
  templates/
    story_template/
      config.yaml
      bible/raw.md
      outline.md
      style_guide.md
      chapters/.gitkeep
      memory/L1/.gitkeep
      memory/L2/chapter_summaries.md
      memory/L3/story_state.md
      memory/L3/timeline.md
      memory/L3/character_states.md
      memory/L3/unresolved_threads.md
      reports/.gitkeep
      exports/.gitkeep
tests/
  conftest.py
  fixtures/
    wrong-story-chunks.json
  integration/
    test_lone_star_chapter_08_pipeline.py
  unit/
    test_approval.py
    test_chunker.py
    test_context_builder.py
    test_diff.py
    test_exporter.py
    test_paths.py
    test_retriever.py
    test_schemas.py
    test_validators.py
```

## Task 1: Project Foundation

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `book_system/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Add package metadata and tooling**

Create `pyproject.toml` with:

```toml
[project]
name = "canonforge"
version = "0.0.1"
description = "Local-first canon-grounded book production engine"
requires-python = ">=3.11"
dependencies = [
  "pydantic>=2.7,<3",
  "PyYAML>=6.0,<7",
]

[dependency-groups]
dev = [
  "pytest>=8.2,<9",
  "ruff>=0.5,<1",
  "black>=24.4,<25",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.black]
line-length = 88
target-version = ["py311"]
```

- [ ] **Step 2: Add README scope guard**

Create `README.md` stating:

```markdown
# CanonForge

CanonForge is a local-first, canon-grounded book production engine.

V1 is an importable Python package with tests as the first execution surface.
There is no CLI, UI, dashboard, API server, queue, or database in the first
milestone.
```

- [ ] **Step 3: Add package init**

Create `book_system/__init__.py`:

```python
"""CanonForge local-first core engine."""

__all__ = ["__version__"]

__version__ = "0.0.1"
```

- [ ] **Step 4: Add pytest shared fixture root**

Create `tests/conftest.py`:

```python
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]
```

- [ ] **Step 5: Verify foundation**

Run:

```bash
uv run pytest -q
```

Expected: pytest starts and reports no tests collected or all current tests passing.

## Task 2: Core Schemas

**Files:**
- Create: `book_system/schemas/story_config.py`
- Create: `book_system/schemas/job.py`
- Create: `book_system/schemas/chunk.py`
- Create: `book_system/schemas/context.py`
- Create: `book_system/schemas/qa_report.py`
- Create: `book_system/schemas/approval.py`
- Create: `book_system/schemas/trace.py`
- Create: `book_system/schemas/__init__.py`
- Create: `tests/unit/test_schemas.py`

- [ ] **Step 1: Write schema tests**

`tests/unit/test_schemas.py` must assert:

```python
from book_system.schemas import (
    ApprovalRecord,
    BibleChunk,
    ChapterContext,
    Job,
    QAReport,
    StoryConfig,
    TraceEvent,
)


def test_story_config_requires_identity_and_allowed_root():
    config = StoryConfig.model_validate(
        {
            "schema_version": 1,
            "story_id": "lone-star-reckoning",
            "title": "Lone Star Reckoning",
            "genre": "Traditional Western",
            "target_word_count": 40000,
            "chapter_count": 20,
            "default_bible_version": "version-1",
            "language": "en",
            "paths": {
                "allowed_root": "stories/lone-star-reckoning",
                "bible_raw": "bible/raw.md",
                "outline": "outline.md",
                "style_guide": "style_guide.md",
            },
            "generation": {
                "default_mode": "draft",
                "max_auto_retries": 2,
                "chapter_word_target": 2000,
                "word_count_tolerance_percent": 10,
            },
            "models": {
                "draft": "local-default",
                "humanize": "local-default",
                "continuity_check": "local-default",
                "final_polish": "premium-optional",
            },
            "rules": {
                "require_retrieved_canon": True,
                "require_human_approval_for_new_canon": True,
                "forbid_cross_story_reads": True,
            },
        }
    )

    assert config.story_id == "lone-star-reckoning"
    assert config.default_bible_version == "version-1"
    assert config.paths.allowed_root == "stories/lone-star-reckoning"


def test_context_requires_retrieved_chunks():
    chunk = BibleChunk(
        chunk_id="chunk-character-darin-mayweather",
        story_id="lone-star-reckoning",
        bible_version="version-1",
        section_type="character",
        section_name="Darin Mayweather",
        source_file="bible/raw.md",
        text="Darin Mayweather, 38, U.S. Marshal.",
    )

    context = ChapterContext(
        story_id="lone-star-reckoning",
        bible_version="version-1",
        chapter_number=8,
        task="draft_chapter",
        system_role="You are a grounded Western fiction chapter writer.",
        current_chapter_plan={
            "title": "Rooftop Duel",
            "summary": "Mayweather fights Deadeye across rooftops.",
        },
        previous_chapter_summary="Mayweather captured Billy.",
        next_chapter_summary="Rufus discovers Billy missing.",
        retrieved_canon_chunks=[chunk],
        style_rules=["Traditional Western tone."],
        forbidden_changes=["Do not change the left-arm wound."],
        output_contract={
            "format": "markdown",
            "must_include": ["chapter_text", "generation_notes"],
            "must_not_include": ["unapproved_new_canon"],
        },
    )

    assert context.retrieved_canon_chunks[0].chunk_id == chunk.chunk_id


def test_report_approval_job_and_trace_models_are_parseable():
    job = Job(
        job_id="lone-star-reckoning-chapter-08-draft",
        story_id="lone-star-reckoning",
        bible_version="version-1",
        chapter_number=8,
        stage="draft-chapter",
        mode="draft",
        allowed_root="stories/lone-star-reckoning",
        status="queued",
        max_auto_retries=2,
        retry_count=0,
        created_at="2026-06-07T00:00:00Z",
        updated_at="2026-06-07T00:00:00Z",
        inputs={"context": "chapters/chapter-08/context.json"},
        outputs={"draft": "chapters/chapter-08/draft.md"},
    )
    report = QAReport(
        story_id="lone-star-reckoning",
        bible_version="version-1",
        chapter_number=8,
        status="passed",
        retry_count=0,
        issues=[],
        passed_checks=["story_id"],
        failed_checks=[],
    )
    approval = ApprovalRecord(
        story_id="lone-star-reckoning",
        bible_version="version-1",
        chapter_number=8,
        approved=True,
        approved_by="editor",
        approved_at="2026-06-07T00:00:00Z",
        approved_files=["chapters/chapter-08/final.md"],
        notes="Approved.",
        new_canon_approved=[],
    )
    trace = TraceEvent(
        ts="2026-06-07T00:00:00Z",
        event="job_started",
        story_id="lone-star-reckoning",
        chapter_number=8,
        stage="draft-chapter",
    )

    assert job.schema_version == 1
    assert report.status == "passed"
    assert approval.approved is True
    assert trace.event == "job_started"
```

- [ ] **Step 2: Implement Pydantic schemas**

Implement the named models with `schema_version: int = 1`, stable field names from `CanonForge.md`, and `extra="forbid"` model config.

- [ ] **Step 3: Export schemas**

`book_system/schemas/__init__.py` must import and expose:

```python
from book_system.schemas.approval import ApprovalRecord
from book_system.schemas.chunk import BibleChunk, BibleChunkIndex
from book_system.schemas.context import ChapterContext
from book_system.schemas.job import Job
from book_system.schemas.qa_report import QAIssue, QAReport
from book_system.schemas.story_config import StoryConfig
from book_system.schemas.trace import TraceEvent

__all__ = [
    "ApprovalRecord",
    "BibleChunk",
    "BibleChunkIndex",
    "ChapterContext",
    "Job",
    "QAIssue",
    "QAReport",
    "StoryConfig",
    "TraceEvent",
]
```

- [ ] **Step 4: Verify schemas**

Run:

```bash
uv run pytest tests/unit/test_schemas.py -q
```

Expected: all schema tests pass.

## Task 3: Story Template And Path Scoping

**Files:**
- Create: `book_system/pipeline/errors.py`
- Create: `book_system/pipeline/paths.py`
- Create: `book_system/pipeline/story_template.py`
- Create: `book_system/pipeline/__init__.py`
- Create: `tests/unit/test_paths.py`

- [ ] **Step 1: Write path and template tests**

`tests/unit/test_paths.py` must cover:

```python
from pathlib import Path

import pytest

from book_system.pipeline.errors import PathScopeError
from book_system.pipeline.paths import StoryPathService
from book_system.pipeline.story_template import initialize_story


def test_path_service_resolves_inside_allowed_root(tmp_path: Path):
    story_root = tmp_path / "stories" / "lone-star-reckoning"
    story_root.mkdir(parents=True)
    service = StoryPathService(project_root=tmp_path, allowed_root=story_root)

    resolved = service.resolve("bible/raw.md")

    assert resolved == story_root / "bible" / "raw.md"


def test_path_service_rejects_traversal(tmp_path: Path):
    story_root = tmp_path / "stories" / "lone-star-reckoning"
    story_root.mkdir(parents=True)
    service = StoryPathService(project_root=tmp_path, allowed_root=story_root)

    with pytest.raises(PathScopeError):
        service.resolve("../other-story/bible/raw.md")


def test_initialize_story_creates_local_folder_contract(tmp_path: Path):
    bible = tmp_path / "example-bible.md"
    bible.write_text("# Title: Lone Star Reckoning\n", encoding="utf-8")

    story_root = initialize_story(
        project_root=tmp_path,
        story_id="lone-star-reckoning",
        title="Lone Star Reckoning",
        genre="Traditional Western",
        source_bible=bible,
    )

    assert (story_root / "config.yaml").exists()
    assert (story_root / "bible" / "raw.md").read_text(encoding="utf-8").startswith("# Title")
    assert (story_root / "chapters").exists()
    assert (story_root / "memory" / "L1" / "trace.jsonl").exists()
```

- [ ] **Step 2: Implement explicit errors**

`book_system/pipeline/errors.py` must define:

```python
class CanonForgeError(Exception):
    """Base error for CanonForge engine failures."""


class PathScopeError(CanonForgeError):
    """Raised when a path escapes the configured story root."""


class StoryIdentityError(CanonForgeError):
    """Raised when story identity is missing or mismatched."""


class BibleVersionError(CanonForgeError):
    """Raised when bible version is missing or mismatched."""


class RetrievedCanonError(CanonForgeError):
    """Raised when retrieved canon is empty or invalid."""


class ApprovalError(CanonForgeError):
    """Raised when approval rules block an operation."""
```

- [ ] **Step 3: Implement path service**

`StoryPathService.resolve()` must join relative paths to the story root, call `.resolve()`, and raise `PathScopeError` if the resolved path is not inside `allowed_root.resolve()`.

- [ ] **Step 4: Implement story initialization**

`initialize_story()` must create `stories/<story_id>`, copy the source bible to `bible/raw.md`, create chapter/memory/report/export directories, write `config.yaml`, and fail if the story folder already exists unless `force=True`.

- [ ] **Step 5: Verify path safety**

Run:

```bash
uv run pytest tests/unit/test_paths.py -q
```

Expected: all path and template tests pass.

## Task 4: Bible Chunking And Versioning

**Files:**
- Create: `book_system/rag/chunker.py`
- Create: `book_system/rag/versioning.py`
- Create: `book_system/rag/bible_indexer.py`
- Create: `book_system/rag/__init__.py`
- Create: `tests/unit/test_chunker.py`

- [ ] **Step 1: Write chunking tests**

`tests/unit/test_chunker.py` must assert that `docs/example-bible.md` produces chunks whose `section_type` includes `setting`, `character`, `antagonist`, `premise`, `act`, `chapter_summary`, and `style_rule`.

- [ ] **Step 2: Implement meaning-based chunker**

The chunker must parse Markdown headings and known labels from `docs/example-bible.md`:

- `## Setting` -> `setting`
- `## Hero` -> `character`
- `## Main Antagonists` plus bullet names -> `antagonist`
- `## Core Premise` -> `premise`
- `## Act N ...` -> `act`
- `**Chapter N: Title**` -> `chapter_summary`
- genre/tone/length metadata and Western phrasing notes -> `style_rule`

Chunk IDs must be deterministic slugs like `chunk-character-darin-mayweather`.

- [ ] **Step 3: Implement versioning**

`next_bible_version(story_root: Path) -> str` must return `version-1` when no bible version directories exist and increment to `version-N` after that.

- [ ] **Step 4: Implement index writer**

`index_bible(project_root, story_id, bible_version=None)` must write:

```text
stories/<story_id>/bible/<version>/chunks.json
stories/<story_id>/bible/<version>/meta.json
```

The chunks file must match the `BibleChunkIndex` schema and include `story_id`, `bible_version`, `source_file`, and `chunks`.

- [ ] **Step 5: Verify chunker and indexer**

Run:

```bash
uv run pytest tests/unit/test_chunker.py -q
```

Expected: all chunking and versioning tests pass.

## Task 5: Strict Retriever

**Files:**
- Create: `book_system/rag/retriever.py`
- Create: `tests/unit/test_retriever.py`
- Create: `tests/fixtures/wrong-story-chunks.json`

- [ ] **Step 1: Write retriever tests**

Tests must prove:

- retrieval filters by exact `story_id`
- retrieval filters by exact `bible_version`
- mismatched chunks are rejected
- Chapter 8 query returns Darin, Deadeye, Act 2, Chapter 8, and style rules
- empty retrieval raises `RetrievedCanonError` when `require_retrieved_canon=True`

- [ ] **Step 2: Implement local keyword retriever**

Implement deterministic local retrieval before vector search:

```python
retrieve_canon_chunks(
    index: BibleChunkIndex,
    story_id: str,
    bible_version: str,
    chapter_number: int,
    query_terms: list[str],
    require_retrieved_canon: bool = True,
) -> list[BibleChunk]
```

Use case-insensitive keyword matching over `section_name`, `section_type`, and `text`. Always include matching current chapter summary, surrounding chapter summaries, act chunk, and style rules when present.

- [ ] **Step 3: Verify retriever**

Run:

```bash
uv run pytest tests/unit/test_retriever.py -q
```

Expected: all strict retrieval tests pass.

## Task 6: Context Package Builder

**Files:**
- Create: `book_system/pipeline/context_builder.py`
- Create: `tests/unit/test_context_builder.py`

- [ ] **Step 1: Write context tests**

Tests must prove Chapter 8 context contains:

- `story_id = lone-star-reckoning`
- `bible_version = version-1`
- `chapter_number = 8`
- retrieved chunk IDs for Darin, Deadeye, Act 2, and Chapter 8
- previous chapter summary for Chapter 7 when available
- next chapter summary for Chapter 9 when available
- Western style rules
- forbidden changes from canon where available

- [ ] **Step 2: Implement builder**

`build_chapter_context(project_root, story_id, chapter_number, bible_version=None)` must load `config.yaml`, load the selected `chunks.json`, call the retriever, build `ChapterContext`, write `chapters/chapter-08/context.json`, and fail if no retrieved canon exists.

- [ ] **Step 3: Verify context builder**

Run:

```bash
uv run pytest tests/unit/test_context_builder.py -q
```

Expected: context builder tests pass.

## Task 7: Deterministic Writer And Humanizer Agents

**Files:**
- Create: `book_system/agents/writer_agent.py`
- Create: `book_system/agents/humanizer_agent.py`
- Create: `book_system/agents/__init__.py`
- Create: `tests/unit/test_writer_agent.py`

- [ ] **Step 1: Write deterministic drafting tests**

Tests must assert:

- `WriterAgent.write_draft(context)` refuses empty canon
- output Markdown includes `# Chapter 8: Rooftop Duel`
- output includes `## Chapter Text`
- output includes `## Generation Notes`
- output records used chunk IDs
- `HumanizerAgent.humanize()` preserves chapter title and adds `## Humanization Notes`

- [ ] **Step 2: Implement deterministic writer**

Do not call an LLM in v1. The writer must produce a deterministic stub from the context:

```markdown
# Chapter 8: Rooftop Duel

## Chapter Text

This deterministic draft is grounded in the approved context package for
`lone-star-reckoning`, bible `version-1`.

## Generation Notes

- story_id: lone-star-reckoning
- bible_version: version-1
- retrieved_chunk_ids:
  - chunk-character-darin-mayweather
```

- [ ] **Step 3: Implement deterministic humanizer**

The humanizer must copy draft text, append notes, and refuse to change plot facts. It is a pass-through module until a model router is introduced.

- [ ] **Step 4: Verify agents**

Run:

```bash
uv run pytest tests/unit/test_writer_agent.py -q
```

Expected: deterministic writer and humanizer tests pass.

## Task 8: Python Validators And QA Report

**Files:**
- Create: `book_system/validators/story_identity_validator.py`
- Create: `book_system/validators/bible_version_validator.py`
- Create: `book_system/validators/retrieved_chunk_validator.py`
- Create: `book_system/validators/path_scope_validator.py`
- Create: `book_system/validators/word_count_validator.py`
- Create: `book_system/validators/structure_validator.py`
- Create: `book_system/validators/forbidden_words_validator.py`
- Create: `book_system/validators/__init__.py`
- Create: `book_system/agents/qa_agent.py`
- Create: `tests/unit/test_validators.py`

- [ ] **Step 1: Write validator tests**

Tests must prove:

- wrong `story_id` is high severity
- wrong `bible_version` is high severity
- empty retrieved chunks is high severity
- path escape is critical severity
- word count outside configured tolerance is medium severity
- missing `## Chapter Text` is medium severity
- configured forbidden words are reported

- [ ] **Step 2: Implement validator result shape**

Use `QAIssue` from schemas for all validator output. Severity values are exactly `low`, `medium`, `high`, `critical`.

- [ ] **Step 3: Implement QA aggregation**

`QAAgent.check_chapter()` must combine validator outputs into `QAReport`:

- `status = passed` when no issues
- `status = needs_review` when low/medium/high issues exist
- raise a CanonForge error for critical issues

- [ ] **Step 4: Verify validators**

Run:

```bash
uv run pytest tests/unit/test_validators.py -q
```

Expected: validator and QA tests pass.

## Task 9: Diff, Approval, Trace, And Export

**Files:**
- Create: `book_system/pipeline/diff.py`
- Create: `book_system/pipeline/approval.py`
- Create: `book_system/pipeline/events.py`
- Create: `book_system/pipeline/exporter.py`
- Create: `book_system/agents/diff_agent.py`
- Create: `book_system/agents/export_agent.py`
- Create: `tests/unit/test_diff.py`
- Create: `tests/unit/test_approval.py`
- Create: `tests/unit/test_exporter.py`

- [ ] **Step 1: Write diff tests**

Tests must prove `create_markdown_diff(before, after)` returns a unified diff with `---`, `+++`, and changed Markdown lines.

- [ ] **Step 2: Write approval tests**

Tests must prove:

- approval fails when QA contains high or critical unresolved issues
- approval copies final candidate to `final.md` when report is passed
- approval writes `approval.yaml`

- [ ] **Step 3: Write export tests**

Tests must prove:

- export fails when a chapter has no `approval.yaml`
- export fails when `approved` is false
- export writes only approved chapter final text into `exports/<story_id>.md`

- [ ] **Step 4: Implement diff**

Use Python `difflib.unified_diff` for v1. Do not use git as a required dependency.

- [ ] **Step 5: Implement approval**

Approval must load `qa_report.json`, block unresolved high or critical issues, write `approval.yaml`, and copy the approved candidate to `final.md`.

- [ ] **Step 6: Implement trace logging**

`append_trace_event(path, event)` must append one compact JSON object per line to `memory/L1/trace.jsonl`.

- [ ] **Step 7: Implement Markdown export**

`export_story_markdown(project_root, story_id)` must concatenate approved `chapters/chapter-*/final.md` files in chapter order into `exports/<story_id>.md`.

- [ ] **Step 8: Verify review artifacts**

Run:

```bash
uv run pytest tests/unit/test_diff.py tests/unit/test_approval.py tests/unit/test_exporter.py -q
```

Expected: all diff, approval, trace, and export tests pass.

## Task 10: Orchestrator For V1 Proof Target

**Files:**
- Create: `book_system/pipeline/jobs.py`
- Create: `book_system/pipeline/orchestrator.py`
- Create: `tests/integration/test_lone_star_chapter_08_pipeline.py`

- [ ] **Step 1: Write integration test**

The integration test must use `tmp_path`, copy `docs/example-bible.md`, and call one public Python API:

```python
from book_system.pipeline.orchestrator import run_lone_star_chapter_08_proof


def test_lone_star_chapter_08_pipeline(project_root, tmp_path):
    result = run_lone_star_chapter_08_proof(
        project_root=tmp_path,
        source_bible=project_root / "docs" / "example-bible.md",
    )

    story_root = tmp_path / "stories" / "lone-star-reckoning"

    assert result.status == "exported"
    assert (story_root / "bible" / "version-1" / "chunks.json").exists()
    assert (story_root / "chapters" / "chapter-08" / "context.json").exists()
    assert (story_root / "chapters" / "chapter-08" / "draft.md").exists()
    assert (story_root / "chapters" / "chapter-08" / "qa_report.json").exists()
    assert (story_root / "chapters" / "chapter-08" / "diff.md").exists()
    assert (story_root / "chapters" / "chapter-08" / "approval.yaml").exists()
    assert (story_root / "chapters" / "chapter-08" / "final.md").exists()
    assert (story_root / "exports" / "lone-star-reckoning.md").exists()

    context_text = (story_root / "chapters" / "chapter-08" / "context.json").read_text(
        encoding="utf-8"
    )
    assert "Darin Mayweather" in context_text
    assert "Deadeye" in context_text
    assert "Act 2" in context_text
    assert "Rooftop Duel" in context_text
```

- [ ] **Step 2: Implement job result model**

`jobs.py` must expose a lightweight dataclass:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineResult:
    status: str
    story_id: str
    bible_version: str
    chapter_number: int
    artifacts: dict[str, str]
```

- [ ] **Step 3: Implement orchestrator**

`run_lone_star_chapter_08_proof()` must call the engine modules in this order:

1. `initialize_story`
2. `index_bible`
3. `build_chapter_context`
4. `WriterAgent.write_draft`
5. `HumanizerAgent.humanize`
6. `QAAgent.check_chapter`
7. `create_markdown_diff`
8. `approve_chapter`
9. `export_story_markdown`

It must write trace events after each stage.

- [ ] **Step 4: Verify V1 proof**

Run:

```bash
uv run pytest tests/integration/test_lone_star_chapter_08_pipeline.py -q
```

Expected: the complete local proof pipeline passes without CLI, UI, model server, database, or network.

## Task 11: Prompt And Skill Files

**Files:**
- Create: all files under `book_system/prompts/`
- Create: all files under `book_system/skills/`
- Create: `tests/unit/test_prompt_files.py`

- [ ] **Step 1: Write prompt file tests**

Tests must assert every prompt has these headings:

```text
# Prompt Name
## Purpose
## Inputs
## Hard Rules
## Output Format
## Failure Mode
## Validation Checklist
```

- [ ] **Step 2: Write required prompt files**

Create these prompt files with concrete rules from `CanonForge.md`:

- `write_scene.md`
- `humanize_chapter.md`
- `check_continuity.md`
- `summarize_chapter.md`
- `diff_summary.md`
- `create_story_bible.md`
- `build_chapter_plan.md`

- [ ] **Step 3: Write required skill files**

Create these skill files with purpose, inputs, outputs, rules, examples, failure modes, and validation checklist:

- `western_dialogue.md`
- `prose_humanization.md`
- `continuity_checking.md`
- `hallucination_detection.md`
- `diff_review.md`

- [ ] **Step 4: Verify prompt and skill files**

Run:

```bash
uv run pytest tests/unit/test_prompt_files.py -q
```

Expected: all required prompt and skill files pass heading checks.

## Task 12: Memory L2/L3 Consolidation

**Files:**
- Create: `book_system/pipeline/memory.py`
- Create: `tests/unit/test_memory.py`

- [ ] **Step 1: Write memory tests**

Tests must prove:

- L1 trace is append-only JSONL
- approved final chapter can update `memory/L2/chapter_summaries.md`
- L3 files are updated only after L2 update succeeds
- failed L3 update keeps old files unchanged

- [ ] **Step 2: Implement deterministic summary writer**

For v1, write deterministic summaries using chapter title, chapter number, approval status, and first paragraph excerpt. Do not call an LLM.

- [ ] **Step 3: Implement L3 updater**

Update:

- `memory/L3/story_state.md`
- `memory/L3/timeline.md`
- `memory/L3/character_states.md`
- `memory/L3/unresolved_threads.md`

Use atomic temp-file writes followed by replace.

- [ ] **Step 4: Verify memory**

Run:

```bash
uv run pytest tests/unit/test_memory.py -q
```

Expected: all memory tests pass.

## Task 13: Local Model Router Boundary

**Files:**
- Create: `book_system/pipeline/model_router.py`
- Create: `tests/unit/test_model_router.py`

- [ ] **Step 1: Write router tests**

Tests must prove:

- `local-default` resolves to deterministic stub provider by default
- unknown model name raises explicit error
- router records model name and provider name for trace metadata
- no network call is made during tests

- [ ] **Step 2: Implement model router interface**

Expose:

```python
class ModelProvider(Protocol):
    name: str

    def generate(self, prompt: str) -> str:
        ...
```

Implement `DeterministicStubProvider` and `ModelRouter`.

- [ ] **Step 3: Wire agents through router**

Writer and humanizer agents should accept an optional router but keep deterministic stub behavior as default.

- [ ] **Step 4: Verify router**

Run:

```bash
uv run pytest tests/unit/test_model_router.py tests/unit/test_writer_agent.py -q
```

Expected: router and agents pass without external services.

## Task 14: Regression And Quality Gates

**Files:**
- Create: `tests/regression/test_non_negotiable_rules.py`

- [ ] **Step 1: Write regression tests**

Regression tests must assert:

- missing `story_id` fails
- missing `bible_version` fails
- no retrieved canon fails
- wrong-story chunks are rejected
- path traversal fails
- retry loop stops at `max_auto_retries`
- final export rejects unapproved chapters

- [ ] **Step 2: Add retry loop boundary**

If retry behavior is not already centralized, add `run_with_retry_limit(max_auto_retries, operation)` in `book_system/pipeline/jobs.py` and test that it calls the operation no more than `max_auto_retries + 1` times.

- [ ] **Step 3: Verify non-negotiable rules**

Run:

```bash
uv run pytest tests/regression/test_non_negotiable_rules.py -q
```

Expected: all regression tests pass.

## Task 15: Full Verification And Formatting

**Files:**
- Modify only files created by earlier tasks if format or lint failures require it.

- [ ] **Step 1: Run all tests**

Run:

```bash
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run Ruff**

Run:

```bash
uv run ruff check .
```

Expected: no lint errors.

- [ ] **Step 3: Run Black check**

Run:

```bash
uv run black --check .
```

Expected: all Python files are formatted.

- [ ] **Step 4: Confirm no CLI or UI landed**

Run:

```bash
find . -maxdepth 3 \( -iname '*cli*' -o -iname '*dashboard*' -o -iname '*web*' \) -print
```

Expected: no v1 CLI/UI implementation files. Documentation references are acceptable.

## Deferred Phase A: CLI Wrapper

Start only after Task 15 passes. The CLI must wrap public engine functions and must not duplicate business logic.

Required later commands:

```text
canonforge init-story
canonforge index-bible
canonforge build-context
canonforge draft-chapter
canonforge humanize-chapter
canonforge check-chapter
canonforge diff-chapter
canonforge approve-chapter
canonforge export-story
```

Acceptance: command tests prove the CLI returns short machine-readable status lines and uses the same engine functions as integration tests.

## Deferred Phase B: Real Local LLM And Vector Search

Start only after the deterministic local proof is stable.

- Add Ollama or llama.cpp provider behind `ModelRouter`.
- Add sentence-transformer or Ollama embeddings behind a local embedding interface.
- Add Chroma first and FAISS fallback for per-story indexes.
- Keep deterministic local fallback for tests.
- Never allow vector retrieval across story roots.

Acceptance: integration tests still pass offline with stub providers; optional model tests are marked and skipped unless local model env vars are set.

## Deferred Phase C: Humanization, Continuity AI Checks, And Model Benchmarks

Start only after model routing exists.

- Add real humanizer provider for natural Western prose.
- Add continuity AI checker as a report-only validator.
- Add benchmark fixtures for chapter expansion, humanization, continuity check, diff explanation, and cost/speed measurement.
- Record model name, provider, prompt version, and chunk IDs in trace events.

Acceptance: deterministic tests remain stable; benchmark outputs are opt-in artifacts.

## Deferred Phase D: Queue, Dashboard, Database, And Multi-User

Start only after the local engine and CLI are proven with real story production.

- Add queue support for many chapters.
- Add cost and token tracking.
- Add dashboard for status and review.
- Add database only when file folders become painful.
- Add global search only after per-story isolation is proven.
- Add multi-user permissions only after single-user production works.

Acceptance: dashboard/database layers operate on engine artifacts and do not become the source of truth.

## Completion Criteria

V1 is complete when:

- `uv run pytest -q` passes.
- `uv run ruff check .` passes.
- `uv run black --check .` passes.
- The integration proof creates one approved exported Markdown story from `docs/example-bible.md`.
- No CLI, UI, dashboard, API server, queue, database, or hosted model is required.
- Every generated artifact can answer:
  - Which story?
  - Which bible version?
  - Which canon chunks?
  - Which prompt?
  - Which model?
  - Which validator results?
  - Which human approval?
