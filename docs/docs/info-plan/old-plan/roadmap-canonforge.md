# CanonForge Roadmap

Current version: `0.0.1`

CanonForge is being built in layers. The goal is not to start with a dashboard
or a chatbot shell. The goal is to build a trustworthy local book-production
engine first, then add wrappers and richer interfaces after the core artifacts
and safety rules are stable.

## Roadmap At A Glance

```text
v0.0.1  Local deterministic proof engine
v0.0.2  Better engine output and QA usefulness
v0.0.3  CLI wrapper over tested engine functions
v0.0.4  Local model routing behind ModelRouter
v0.0.5  Local vector retrieval / LlamaIndex-style RAG
v0.0.6  Real humanization and continuity checks
v0.0.7  Benchmarks and evaluation workflow
v0.1.0  First usable local author workflow
later   Dashboard, queue, database, multi-user workflows
```

The important rule is simple:

```text
engine first -> CLI second -> models after stable interfaces -> UI last
```

## How To Read This Roadmap

`v0.0.1` is the current implemented proof. The later version numbers are
planning labels, not existing tagged releases. They organize the source-backed
phase order into smaller releases that are easier to reason about.

The phase order comes from the CanonForge docs: local core first, CLI wrapper
after the core is stable, local models and retrieval after stable interfaces,
humanization and continuity after model routing, and dashboard/database layers
only after the local workflow proves useful.

One recommendation is intentionally pragmatic: `v0.0.2` improves engine output
before adding the CLI. The older deferred phase list says the CLI can come after
the core is stable. Both are compatible, but better artifacts make the CLI more
useful when it arrives.

## Source-Backed Phase Map

| Roadmap area | Source-backed basis | Roadmap interpretation |
| --- | --- | --- |
| Foundation/core proof | `docs/local-first-core-engine-plan.md`, current tests, `README.md` | `v0.0.1` proves one local deterministic pipeline. |
| Better engine output | Current `v0.0.1` output is intentionally stub-like | `v0.0.2` is a recommended bridge before CLI. |
| CLI wrapper | Deferred Phase A and `docs/CanonForge.md` CLI contract | `v0.0.3` adds Typer-style commands over engine functions. |
| Local LLM and vector search | Deferred Phase B and `docs/CanonForge.md` tech choices | `v0.0.4` adds model routing; `v0.0.5` adds retrieval/RAG. |
| Humanization, continuity, benchmarks | Deferred Phase C and `docs/my-plan-to-build.md` | `v0.0.6` and `v0.0.7` make editorial checks useful and measurable. |
| Queue, dashboard, database, multi-user | Deferred Phase D and product docs | Later layers operate on engine artifacts, not the other way around. |

## Current State: v0.0.1

`v0.0.1` proves that the local pipeline works end to end. It is not meant to be
the final writing experience yet.

What it does today:

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

This version proves the plumbing:

- story initialization works
- bible chunking works
- local context building works
- deterministic drafting runs
- deterministic humanization runs
- QA reporting runs
- diff output is created
- approval is required before export
- final Markdown export works
- tests can verify the whole flow without a CLI, UI, API, database, queue, or
  model server

What `v0.0.1` does not mean:

- It does not yet write high-quality novel chapters.
- It does not yet call a real local LLM.
- It does not yet provide a command-line product.
- It does not yet have a dashboard or review UI.
- It does not yet scale to many chapters as a production workflow.

## v0.0.2: Better Engine Output And QA Usefulness

Recommended next target: improve the engine output before wrapping it with a
CLI.

Why this comes next:

The current engine works, but the writer and humanizer are still deterministic
and stub-like. Before adding a command interface, the generated artifacts should
be more useful to inspect.

Goals:

- Make `draft.md` more chapter-like while remaining deterministic.
- Use more of the retrieved canon context in the draft.
- Make the draft show which bible chunks influenced it.
- Improve deterministic humanization cleanup without changing plot facts.
- Make `qa_report.json` easier for a reviewer to understand.
- Add better test fixtures for clean chapters and intentionally bad chapters.
- Keep the public proof API stable:

```python
run_lone_star_chapter_08_proof(project_root, source_bible)
```

Possible improvements:

- stronger chapter title and section structure
- required beat coverage in draft output
- clearer grounding statements
- more concrete QA recommendations
- stronger AI-pattern phrase reporting
- clearer distinction between review issues and blocking failures

Not yet:

- no CLI
- no UI
- no API server
- no hosted model
- no database
- no vector database
- no cross-story retrieval

Acceptance idea:

`v0.0.2` should still run fully offline and should still produce the same core
artifact chain, but the draft, humanized output, and QA report should be more
useful to read.

## v0.0.3: CLI Wrapper

Goal: add a thin command-line wrapper over already-tested engine functions.

Why this comes after engine improvement:

The CLI should not become the source of business logic. It should only call
existing Python services and print clear status output. If the core behavior is
not stable first, the CLI becomes a place where pipeline rules can accidentally
split or duplicate.

Source-backed implementation note:

`docs/CanonForge.md` names Typer as the likely CLI tool. That is a good fit
later because it can expose small Python commands without turning the CLI into a
second orchestration layer.

Likely commands:

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

Rules:

- The CLI must wrap public engine functions.
- The CLI must not duplicate validation logic.
- The CLI must not bypass approval rules.
- The CLI must not read outside the story root.
- CLI output should be short and machine-readable where possible.

Not yet:

- no dashboard
- no web API
- no database
- no queue
- no hosted model requirement

Acceptance idea:

Each command should have tests proving it calls the same engine behavior already
covered by unit and integration tests.

## v0.0.4: Local Model Routing

Goal: add real model-provider routing behind `ModelRouter` while keeping the
deterministic fallback.

Why this comes after the CLI/core boundary:

Model calls are expensive, variable, and harder to test. The engine needs stable
input/output artifacts first so model-backed stages can be swapped in without
breaking the pipeline contract.

Likely additions:

- provider interface for local models
- optional local provider such as Ollama or llama.cpp
- model selection by task
- trace metadata for model name and provider name
- deterministic fallback provider for tests
- cloud LLM support only as an optional later path, not a required dependency

Example future routing:

```text
draft     -> local-default or local-writer
humanize  -> local-humanizer
qa        -> deterministic validators plus optional model reviewer
summary   -> deterministic fallback or local summarizer
```

Rules:

- Tests must still pass offline.
- Deterministic stubs remain the default for CI.
- Model failures must produce explicit errors.
- No endless retry loops.
- No model may guess missing `story_id`, `bible_version`, or canon context.

Not yet:

- no required cloud dependency
- no dashboard
- no database
- no multi-user workflow

Acceptance idea:

The same proof pipeline should still run without models, while optional local
model tests can run only when the required local model environment exists.

## v0.0.5: Local Vector Retrieval / LlamaIndex-Style RAG

Goal: improve retrieval with local embeddings and vector indexes while
preserving strict story isolation.

Why this comes after model routing:

Vector retrieval is useful only when the engine has stable artifact boundaries
and model/provider routing. Retrieval must be treated as infrastructure, not as
a license to let the model search everything.

Source-backed implementation note:

`docs/CanonForge.md` calls for a LlamaIndex-style RAG pipeline, but also says to
use a simple local fallback before heavy integration. For CanonForge, that means
the existing deterministic retriever remains the testable fallback while a later
RAG layer borrows LlamaIndex-style concepts: document loaders, chunk metadata,
embedding profiles, indexes, retrievers, and query-time provenance.

Likely additions:

- local embedding interface
- per-story vector index
- Chroma or FAISS adapter
- sentence-transformers or Ollama embeddings
- deterministic retrieval fallback for tests
- index metadata stored in local files
- optional LlamaIndex adapter only after the internal retrieval contract is
  stable

Rules:

- No cross-story retrieval.
- No fallback to another story.
- No generation if no retrieved canon chunks exist.
- Retrieved chunk IDs must be visible in context and trace artifacts.
- Vector results must remain scoped to the selected `story_id` and
  `bible_version`.
- RAG supports planning, grounding, QA, and search; it does not replace the
  structured story bible or chapter plan.

Not yet:

- no immediate hard dependency on LlamaIndex
- no global manuscript search across unrelated stories
- no hosted vector database
- no dashboard-first review workflow

Acceptance idea:

The engine can retrieve better canon context locally, but all existing
non-negotiable isolation tests still pass.

## Structured Memory Before Complex RAG

CanonForge should treat RAG as support infrastructure, not the main brain of the
book. Fiction needs explicit story memory because semantic retrieval can miss
important constraints.

Use this hierarchy:

```text
primary memory    story bible, outline, timeline, chapter summaries, approvals
secondary memory  retrieval/search over bible and manuscript chunks
tertiary memory   knowledge graph for relationships and cross-document insight
```

The practical rule is:

```text
structured canon first -> selective retrieval second -> graph memory later
```

This keeps generation grounded in approved story facts instead of whatever the
nearest vector chunks happen to return.

## v0.0.6: Real Humanization And Continuity Checks

Goal: make the model-backed editorial passes useful while keeping canon safety.

Why this comes after model routing and retrieval:

Humanization and continuity review need the right context. If model routing and
retrieval are unstable, prose cleanup can accidentally introduce canon drift or
unsupported changes.

Likely additions:

- model-backed humanizer provider
- continuity checker as a report-only reviewer
- hallucination/canon drift report improvements
- stronger diff explanation
- prompt version tracking
- model/provider trace metadata for each stage

Rules:

- Humanization must preserve canon, POV, tense, scene order, required beats, and
  character voice.
- Continuity checks should report issues; they should not silently rewrite canon.
- High-risk canon issues should block approval.
- New canon facts still require human approval.

Not yet:

- no autonomous canon mutation
- no UI approval workflow as source of truth
- no database authority over file artifacts

Acceptance idea:

The engine can produce better prose and better continuity reports, while the
approval gate still prevents unsafe exports.

## v0.0.7: Benchmarks And Evaluation Workflow

Goal: compare quality, speed, grounding, and cost before scaling to many
chapters.

Why this comes before `v0.1.0`:

Once real models enter the system, output quality varies. Benchmarks keep the
project from choosing models or prompts based only on vibes.

Likely additions:

- benchmark fixtures for chapter expansion
- benchmark fixtures for humanization
- benchmark fixtures for continuity checks
- deterministic expected checks where possible
- opt-in benchmark outputs
- model/provider/prompt-version reporting

Metrics to track:

- canon drift count
- unresolved QA issues
- required beat coverage
- output length
- speed
- cost where applicable
- reviewer approval rate

Not yet:

- no production queue
- no dashboard requirement
- no cloud-only benchmark path

Acceptance idea:

CanonForge can compare model/prompt choices without changing the core pipeline
or requiring hosted services.

## v0.1.0: First Usable Local Author Workflow

Goal: make CanonForge useful as a real local author workflow, not just a proof.

Expected capabilities:

- initialize a story project
- ingest and version a bible
- build grounded chapter context
- generate or rewrite one or more chapters
- run deterministic and optional model-backed QA
- produce reviewable diffs
- require approval before final export
- export Markdown
- operate through a CLI
- remain local-first and file-based

What should be true by `v0.1.0`:

- The engine has stable artifact contracts.
- The CLI wraps engine functions cleanly.
- Tests pass without a model server.
- Optional local model providers are supported.
- Retrieval remains per-story and auditable.
- Approval remains mandatory before final export.

Not yet:

- no SaaS-first dashboard
- no required cloud model
- no database as primary source of truth
- no multi-user permission system unless file-based single-user production has
  already become limiting

## Later: Dashboard, Queue, Database, Multi-User

These are later layers, not the foundation.

Add them only after the local engine and CLI are useful with real story
production.

Possible later additions:

- queue support for many chapters
- dashboard for status and review
- database for indexed metadata if file folders become painful
- cost and token tracking
- multi-user permissions
- web app or SaaS workflow
- global search after per-story isolation is proven

Rules for later layers:

- They must operate on engine artifacts.
- They must not become the only source of truth too early.
- They must not bypass approval.
- They must not weaken story isolation.

## Why This Order

### 1. Engine First

CanonForge is a book-production engine. The important work is not buttons or
pages yet; it is reliable artifact flow:

```text
canon -> context -> draft -> QA -> approval -> export
```

If this flow is wrong, a CLI or dashboard only makes the wrong thing easier to
run.

### 2. CLI Second

A CLI is useful once the engine functions are stable. It gives a simple way to
operate the local workflow without introducing web app complexity.

The CLI should be a wrapper, not a second pipeline.

### 3. Models After Stable Interfaces

Model behavior is variable. Stable schemas, artifacts, validators, and approval
rules must exist before model output becomes part of the workflow.

The deterministic fallback remains important because tests must stay reliable.

### 4. UI Last

A dashboard is valuable for review, status, and approvals, but only after the
engine and CLI prove the workflow. The UI should display and operate on existing
artifacts rather than inventing a separate source of truth.

## Roadmap Basis

This roadmap is based on:

- `docs/local-first-core-engine-plan.md`: source of the local-first rule, the
  first proof target, tests-first execution surface, and CLI/UI deferral.
- `README.md`: current implemented scope, engine rules, Docker/Compose state,
  and deferred work list.
- `docs/CanonForge.md`: broader engine contract, pipeline stages, Typer CLI
  direction, LlamaIndex-style RAG, Chroma/FAISS, local LLM choices, and future
  build order.
- `docs/my-plan-to-build.md`: product intent around controlled editorial
  automation, humanization, selective RAG, structured memory, human review,
  dashboards later, and avoiding overbuilt early systems.
- `docs/CanonForge-0.0.1v.md`: current version explanation and usage guide.
- `docs/superpowers/plans/2026-06-07-canonforge-local-first-core-engine.md`:
  deferred phase order for CLI, local LLM/vector search, humanization and
  continuity benchmarks, then queue/dashboard/database/multi-user.

The roadmap turns those source documents into version-sized planning labels.
Only `v0.0.1` is the current implemented release. Future version labels should
be treated as planning checkpoints until they are implemented and tagged.
