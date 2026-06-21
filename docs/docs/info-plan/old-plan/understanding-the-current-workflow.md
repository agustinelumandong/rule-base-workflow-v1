# CanonForge Current System: Caveman Map

Branch checked: `dev`  
HEAD: `07f9978`, tagged `v0.0.2`  
Scope: code and tests working now. Future work marked `LATER`.

## One-Line Meaning

CanonForge = local Python engine proving canon-grounded book-production plumbing.

```text
story bible
-> isolated story files
-> canon chunks
-> grounded chapter context
-> deterministic draft
-> deterministic cleanup
-> QA report
-> diff
-> approval record
-> final Markdown export
```

Purpose: stop story drift. Force chapter work to carry correct story identity,
bible version, retrieved canon, visible checks, approval, auditable files.

## What Exists Now

- Importable Python 3.11+ package.
- Pydantic schemas for persisted artifacts.
- Local Markdown, JSON, YAML, JSONL files.
- Tests as main execution surface.
- One complete hard-coded proof: Lone Star Reckoning, Chapter 8.
- Deterministic agents. Same input gives same output.
- No network, database, model server, CLI, UI, API, queue, or auth.

Not full author product. Not chatbot. Not high-quality novel generator yet.

## Current Proof

```text
story_id       = lone-star-reckoning
bible_version  = version-1
chapter_number = 8
chapter_title  = Rooftop Duel
source_bible   = docs/example-bible.md
```

Public proof function:

```python
run_lone_star_chapter_08_proof(project_root, source_bible)
```

Success returns `status="exported"`.

## Architecture

```text
book_system/
  schemas/      strict artifact shapes
  pipeline/     orchestration, paths, approval, memory, trace, retry
  stages/       small pipeline work units
  rag/          bible chunking, versioning, keyword retrieval
  agents/       writer, humanizer, QA, diff, export helpers
  validators/   deterministic checks
  storage/      local file helpers
  exporters/    approved Markdown compilation
  prompts/      future model prompt contracts
  skills/       future editorial guidance
  templates/    story folder starters
```

Core split:

```text
engine code != story data
```

Story data belongs under `stories/<story_id>/`.

## Full Workflow

### 1. Initialize Story

`initialize_story()` creates:

```text
stories/<story_id>/
  config.yaml
  bible/raw.md
  outline.md
  style_guide.md
  chapters/
  memory/L1/trace.jsonl
  memory/L2/chapter_summaries.md
  memory/L3/story_state.md
  memory/L3/timeline.md
  memory/L3/character_states.md
  memory/L3/unresolved_threads.md
  reports/
  exports/
```

Default config: 40,000 book words, 20 chapters, 2,000 words per chapter,
10% tolerance, 2 auto retries, `local-default` model labels.

Existing story blocks initialization unless `force=True`.

### 2. Index Bible

`index_bible()` reads `bible/raw.md`. `chunk_bible()` extracts known Markdown
sections:

- style rule
- setting
- character
- antagonist
- premise
- act
- chapter summary

Every chunk stores `chunk_id`, `story_id`, `bible_version`, section metadata,
source file, text.

Outputs:

```text
bible/version-1/chunks.json
bible/version-1/meta.json
```

Chunker is format-specific. Bible headings must match expected patterns.

### 3. Retrieve Canon

Current retrieval = keyword and section matching. No embeddings. No vector DB.

Query uses character names, chapter title, Western style, current chapter,
previous chapter, next chapter, matching act.

Retriever stops on:

- missing story ID
- missing bible version
- request/index identity mismatch
- wrong-story chunk
- wrong-version chunk
- empty required canon result

This is primitive local RAG. Strong identity checks, simple search.

### 4. Build Context

`build_chapter_context()` writes:

```text
chapters/chapter-08/context.json
```

Context contains story ID, bible version, chapter, task, system role, current
plan, previous/next summaries, retrieved chunks, style rules, forbidden changes,
output contract.

Pydantic requires at least one retrieved chunk.

Current forbidden rules are Chapter-8-specific: keep Darin weapons, Shadow Ridge,
left-arm wound, and no unsupported characters.

### 5. Draft

`WriterAgent` refuses empty canon. It writes `draft.md` containing:

- chapter heading and summary
- required beats, when present
- story ID and bible version
- retrieved chunk IDs
- deterministic model label
- prompt version `write_scene_v2`

Important: this is reviewable draft artifact, not full novel prose. Writer exposes
plan and grounding instead of inventing scene detail.

### 6. Humanize

`HumanizerAgent` writes `humanized.md`.

Current work only:

- collapse repeated blank lines
- replace two exact stock-phrase sentences
- append humanization notes
- preserve canon and grounding text

No real model rewrite. No broad voice or style transformation.

### 7. QA

`QAAgent` writes `qa_report.json`.

Checks wired now:

1. Story identity present/matching.
2. Bible version present/matching.
3. Retrieved canon exists.
4. Required Markdown sections exist.
5. Known AI phrase patterns absent.

Pattern examples: `storm of emotions`, `words hung in the air`, `for what felt
like an eternity`, `little did she know`, `couldn't help but`, `in that moment`,
`everything changed`.

Each issue stores severity, type, message, evidence, recommendation.

```text
no issues             -> passed
low/medium/high issue -> needs_review
critical issue        -> exception, stage stops
```

### 8. Diff

`diff_chapter()` uses `difflib.unified_diff`:

```text
draft.md vs humanized.md -> diff.md
```

Reviewer can see exact cleanup change.

### 9. Approval

Approval loads QA report. High or critical issue blocks approval. Low or medium
issue does not block.

On approval:

```text
humanized.md -> final.md
approval.yaml created
```

Current proof auto-calls approval with `approved_by=editor` and fixed timestamp.
Gate is simulated. No real human pause or review interface.

### 10. Export

Exporter scans sorted `chapter-*` folders. Every chapter needs:

- `approval.yaml`
- `approved: true`
- `final.md`

Any missing/unapproved chapter stops export. Approved finals join into:

```text
exports/<story_id>.md
```

Markdown only. No DOCX/PDF now.

### 11. Trace

Orchestrator appends events to `memory/L1/trace.jsonl`:

```text
story_initialized
bible_indexed
context_built
draft_written
humanized_written
qa_written
diff_written
chapter_approved
story_exported
```

Proof timestamps, story, chapter are hard-coded.

## Looping Truth

Current proof is linear:

```text
init -> index -> context -> draft -> humanize -> QA -> diff -> approve -> export
```

No connected revise-until-pass loop exists.

Standalone helper exists:

```python
run_with_retry_limit(max_auto_retries, operation)
```

With `max_auto_retries=2`, total attempts = 3. It retries any exception, then
raises last error. Regression test proves no endless loop.

But orchestrator never calls helper. QA never sends failed text back to writer or
humanizer. Real correction loop is `LATER`:

```text
draft -> QA -> revise failed areas -> QA again -> retry cap -> human review
```

## Validation: Wired and Unwired

Wired into QA:

- story ID
- bible version
- retrieved canon presence
- Markdown structure
- AI phrase patterns

Built but not wired into QA:

- word-count tolerance
- forbidden words
- path-scope issue conversion
- continuity agent

Current QA compares context story ID to itself and bible version to itself. This
mostly proves non-empty values, not mismatch against separate job/config truth.
Retriever performs stronger real index/chunk identity checks.

## Path Safety and Isolation

`StoryPathService` rejects paths escaping `allowed_root`, including `../escape.md`.
Tests prove helper.

Gap: most runtime stages build paths directly. They do not route every read/write
through `StoryPathService`. Full path rule enforcement not complete.

Retriever gives strongest story isolation: request, index, and every chunk must
share story ID and bible version. No cross-story fallback.

Gap: generalized untrusted `story_id` still needs stricter validation because it
becomes a path segment.

## Memory

Designed layers:

```text
L1 = trace events
L2 = chapter summaries
L3 = story state, timeline, character states, unresolved threads
```

Now:

- L1 updates in proof.
- L2/L3 starter files created.
- `update_memory_after_approval()` can update L2/L3.
- L3 uses temp-file replacement.

Gap: orchestrator never calls memory update. End-to-end proof leaves L2/L3 mostly
empty.

## Models, Prompts, Skills

`ModelRouter` maps `local-default` to `deterministic-stub`. Unknown model gives
explicit error. Writer/humanizer do not use router yet.

Prompt contracts exist for bible creation, chapter planning, scene writing,
humanization, continuity, summary, diff summary.

Skill contracts exist for Western dialogue, prose humanization, continuity,
hallucination detection, diff review, AI-pattern cleanup.

These files are future guidance. Current runtime does not load them.

## Storage Helpers

`ArtifactStore` handles text, Markdown, JSON, YAML.

`ArtifactManifest` adds paths immutably. `next_versioned_path()` chooses
`draft.md`, then `draft.v2.md`, `draft.v3.md`.

Gap: proof uses fixed filenames and overwrites them. Manifest/version helper not
connected to orchestrator.

## Schemas

Pydantic models:

- `StoryConfig`
- `BibleChunk` and `BibleChunkIndex`
- `ChapterContext`
- `Job`
- `QAIssue` and `QAReport`
- `ApprovalRecord`
- `TraceEvent`

Most use `extra="forbid"`. Unknown artifact fields rejected. `TraceEvent` allows
extra metadata.

## Artifact Chain

```text
docs/example-bible.md
-> stories/lone-star-reckoning/config.yaml
-> bible/raw.md
-> bible/version-1/chunks.json
-> bible/version-1/meta.json
-> chapters/chapter-08/context.json
-> chapters/chapter-08/draft.md
-> chapters/chapter-08/humanized.md
-> chapters/chapter-08/qa_report.json
-> chapters/chapter-08/diff.md
-> chapters/chapter-08/approval.yaml
-> chapters/chapter-08/final.md
-> exports/lone-star-reckoning.md
```

## Non-Negotiable Rules

```text
No story_id               -> no generation
No bible_version          -> no generation
No retrieved canon        -> no grounded generation
Wrong story/version chunk -> stop
Path escape               -> stop when path service used
High/critical QA issue    -> no approval
No approval               -> no export
Retry cap reached         -> raise last error
```

## Tests and Docker

Tests cover unit modules, full Chapter-8 integration, and regression safety rules.
README expects `50 passed`.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run pytest -q
uv run ruff check .
uv run black --check .
```

Docker has `runtime` target for import/version check and `test` target for pytest.
Compose starts runtime or test only. Named story volume exists. No extra service.

## Honest Scorecard

| Area | State |
| --- | --- |
| Local file engine | Working |
| One Chapter-8 proof | Working |
| Bible chunking | Working, format-specific |
| Retrieval | Working, keyword-based |
| Context package | Working |
| Deterministic draft artifact | Working |
| Full prose generation | Not built |
| Tiny deterministic cleanup | Working |
| Real humanization | Not built |
| QA report | Working, partial checks |
| Revise/validate loop | Not connected |
| Retry cap helper | Working, standalone |
| Diff | Working |
| Approval artifact | Working |
| Real human approval pause | Not built |
| Markdown export | Working |
| DOCX/PDF | Not built |
| L1 trace | Working |
| L2/L3 helper | Working, not orchestrated |
| Real LLM | Not built |
| Semantic/vector RAG | Not built |
| CLI/UI/API/database/queue | Deferred |

## Version Truth

Git says `dev` at tag `v0.0.2`.

Package still says `0.0.1` in `pyproject.toml`, `book_system.__version__`, and
runtime output. Roadmap also calls `v0.0.1` current in places. Version metadata
and docs are not fully synchronized with tag.

## Planned Direction

```text
proof engine
-> CLI wrapper
-> real local model routing
-> local vector retrieval
-> real humanization and continuity
-> evaluation benchmarks
-> usable local author workflow
-> dashboard/queue/database/multi-user later
```

Engine owns truth. CLI/UI must wrap engine. Story files stay local and auditable.
Models never guess missing identity or canon.

## Final Caveman Summary

CanonForge now prove bones, not full body.

It can build story folder, split bible, retrieve correct canon, package context,
make deterministic draft, clean few phrases, run small QA set, show diff, record
approval, block unapproved export, compile Markdown, leave trace.

Safety idea strong. Artifact trail clear. Tests cover core rules.

Missing meat: real prose model, true correction loop, full continuity, all
validators wired, universal path enforcement, real human gate, memory update in
orchestrator, generalized jobs, CLI, semantic RAG.

Best current name:

```text
local deterministic proof engine for canon-grounded book production
```
