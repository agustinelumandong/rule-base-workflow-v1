# CanonForge Build Blueprint

## 1. Project Name And Purpose

**Name:** CanonForge

**Definition:** CanonForge is a local-first, canon-grounded AI book production
pipeline for generating, rewriting, humanizing, validating, reviewing, and
exporting long-form books while staying grounded in approved story canon.

CanonForge is not a chatbot. It is not a manual prompt-loop workflow. It is not
a SaaS-first dashboard. It is a production pipeline for books.

Primary goal:

```text
source bible / outline / chapter plan
-> grounded context package
-> chapter or scene generation
-> validation and checker loop
-> diff and human review
-> approved final manuscript
```

The system should solve the long-form drift problem: when a book grows to
40,000+ words across many chapters, the model must keep using the approved
story bible instead of inventing unsupported details.

The first concrete reference story is:

```text
story_id: lone-star-reckoning
source bible: docs/example-bible.md
first target chapter: Chapter 8, Rooftop Duel
```

## 2. Core Operating Model

CanonForge uses a strict separation between the engine and story data.

```text
main branch = pipeline engine, prompts, validators, templates, documentation
story folders = individual book projects and generated artifacts
```

Every pipeline job must include:

```yaml
story_id: lone-star-reckoning
bible_version: version-1
chapter_number: 8
allowed_root: stories/lone-star-reckoning
```

Hard execution rules:

- No `story_id`, no generation.
- No `bible_version`, no generation.
- No retrieved canon chunks, no grounded generation.
- No worker can read outside `allowed_root`.
- No worker can silently fall back to another story.
- No generated canon change becomes official without approval.
- No endless retry loop.

This is how CanonForge prevents one story from leaking into another.

Bad:

```text
write next chapter
```

Good:

```text
write chapter 8 using story_id=lone-star-reckoning and bible_version=version-1
```

## 3. Full Tech Stack

Use a local-first Python stack. Keep the first production-quality version
boring, inspectable, and file-based.

| Area | Required Choice | Notes |
| --- | --- | --- |
| Language | Python 3.11+ | Typed Python for pipeline code |
| Package manager | `uv` | Fast local env and dependency management |
| CLI | Typer | Commands such as `canonforge draft-chapter` |
| Data models | Pydantic | External schemas, configs, reports, jobs |
| Internal objects | dataclasses | Lightweight internal-only structures |
| Config | PyYAML | Human-readable YAML configs |
| Source files | Markdown | Bibles, outlines, chapters, prompts, reports |
| Metadata | JSON/YAML | Stable machine-readable artifacts |
| RAG pipeline | LlamaIndex-style | Use simple local fallback before heavy integration |
| Vector store | Chroma first, FAISS fallback | Local per-story indexes only |
| Embeddings | sentence-transformers or Ollama embeddings | Local and reproducible |
| Local LLM | Ollama or llama.cpp | Drafting, checking, summaries, diff notes |
| Cloud LLM | Optional later | Final polish or hard chapters only |
| Diff | `difflib` plus optional `git diff` | Human-reviewable change reports |
| Export | Pandoc | Markdown to DOCX/PDF |
| Tests | pytest | Unit, integration, regression, golden tests |
| Formatting | Ruff and Black | Consistent Python formatting |
| UI | None first | CLI first; dashboard only after pipeline works |

Do not start with:

- full dashboard
- SaaS auth
- PostgreSQL
- global vector DB
- multi-user mode
- autonomous agent swarm
- fine-tuning
- publishing automation

Those are later layers, not the foundation.

## 4. Repository Layout

Target engine layout:

```text
book_system/
  __init__.py

  cli.py

  pipeline/
    __init__.py
    orchestrator.py
    jobs.py
    context_builder.py
    model_router.py
    events.py
    paths.py
    approval.py
    exporter.py

  rag/
    __init__.py
    bible_indexer.py
    retriever.py
    chunker.py
    versioning.py
    embeddings.py
    vector_store.py

  agents/
    __init__.py
    intake_agent.py
    architect_agent.py
    writer_agent.py
    humanizer_agent.py
    continuity_agent.py
    diff_agent.py
    qa_agent.py
    export_agent.py

  validators/
    __init__.py
    path_scope_validator.py
    story_identity_validator.py
    bible_version_validator.py
    retrieved_chunk_validator.py
    canon_validator.py
    continuity_validator.py
    style_validator.py
    word_count_validator.py
    structure_validator.py
    forbidden_words_validator.py

  schemas/
    __init__.py
    story_config.py
    job.py
    chunk.py
    context.py
    qa_report.py
    approval.py
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
      reports/.gitkeep
      exports/.gitkeep
```

Target story layout:

```text
stories/
  lone-star-reckoning/
    config.yaml

    bible/
      raw.md
      version-1/
        chunks.json
        meta.json
        embeddings/

    outline.md
    style_guide.md

    chapters/
      chapter-08/
        input.md
        plan.md
        job.yaml
        context.json
        draft.md
        humanized.md
        qa_report.json
        diff.md
        approval.yaml
        final.md

    memory/
      L1/
        trace.jsonl
      L2/
        chapter_summaries.md
      L3/
        story_state.md
        timeline.md
        character_states.md
        unresolved_threads.md

    reports/
      chapter-08-check.md
      chapter-08-diff.md

    exports/
      lone-star-reckoning.md
      lone-star-reckoning.docx
      lone-star-reckoning.pdf
```

## 5. Required File Formats

### `config.yaml`

Story-level config. This is the source of operational truth for a story.

```yaml
schema_version: 1
story_id: lone-star-reckoning
title: Lone Star Reckoning
genre: Traditional Western
target_word_count: 40000
chapter_count: 20
default_bible_version: version-1
language: en

paths:
  allowed_root: stories/lone-star-reckoning
  bible_raw: bible/raw.md
  outline: outline.md
  style_guide: style_guide.md

generation:
  default_mode: draft
  max_auto_retries: 2
  chapter_word_target: 2000
  word_count_tolerance_percent: 10

models:
  draft: local-default
  humanize: local-default
  continuity_check: local-default
  final_polish: premium-optional

rules:
  require_retrieved_canon: true
  require_human_approval_for_new_canon: true
  forbid_cross_story_reads: true
```

### `job.yaml`

One pipeline run for one stage.

```yaml
schema_version: 1
job_id: lone-star-reckoning-chapter-08-draft
story_id: lone-star-reckoning
bible_version: version-1
chapter_number: 8
stage: draft-chapter
mode: draft
allowed_root: stories/lone-star-reckoning
status: queued
max_auto_retries: 2
retry_count: 0
created_at: 2026-06-07T00:00:00Z
updated_at: 2026-06-07T00:00:00Z
inputs:
  chapter_plan: chapters/chapter-08/plan.md
  context: chapters/chapter-08/context.json
outputs:
  draft: chapters/chapter-08/draft.md
  trace: memory/L1/trace.jsonl
```

### `context.json`

Context package passed to a writer, humanizer, or checker.

```json
{
  "schema_version": 1,
  "story_id": "lone-star-reckoning",
  "bible_version": "version-1",
  "chapter_number": 8,
  "task": "draft_chapter",
  "system_role": "You are a grounded Western fiction chapter writer.",
  "current_chapter_plan": {
    "title": "Rooftop Duel",
    "summary": "Deadeye spots movement. A running gunfight across rooftops at dawn. Mayweather is winged in the left arm but puts a .45 slug through Deadeye's good eye."
  },
  "previous_chapter_summary": "Mayweather captured Billy after slipping into the saloon through the roof.",
  "next_chapter_summary": "Rufus discovers Billy missing and starts blaming Vance.",
  "retrieved_canon_chunks": [
    {
      "chunk_id": "chunk-character-darin-mayweather",
      "section_type": "character",
      "section_name": "Darin Mayweather",
      "text": "Darin Mayweather, 38, U.S. Marshal..."
    },
    {
      "chunk_id": "chunk-antagonist-deadeye",
      "section_type": "antagonist",
      "section_name": "Jed \"Deadeye\" Harlan",
      "text": "Jed \"Deadeye\" Harlan - sharpshooter..."
    }
  ],
  "style_rules": [
    "Traditional Western tone.",
    "Direct physical action.",
    "No unsupported new characters."
  ],
  "forbidden_changes": [
    "Do not change Darin's weapons.",
    "Do not move the chapter out of Shadow Ridge.",
    "Do not change the left-arm wound."
  ],
  "output_contract": {
    "format": "markdown",
    "must_include": ["chapter_text", "generation_notes"],
    "must_not_include": ["unapproved_new_canon"]
  }
}
```

### `chunks.json`

Versioned bible chunks.

```json
{
  "schema_version": 1,
  "story_id": "lone-star-reckoning",
  "bible_version": "version-1",
  "source_file": "bible/raw.md",
  "chunks": [
    {
      "chunk_id": "chunk-character-darin-mayweather",
      "story_id": "lone-star-reckoning",
      "bible_version": "version-1",
      "section_type": "character",
      "section_name": "Darin Mayweather",
      "source_file": "bible/raw.md",
      "text": "Darin Mayweather, 38, U.S. Marshal..."
    }
  ]
}
```

### `qa_report.json`

Machine-readable validation report.

```json
{
  "schema_version": 1,
  "story_id": "lone-star-reckoning",
  "bible_version": "version-1",
  "chapter_number": 8,
  "status": "needs_review",
  "retry_count": 2,
  "issues": [
    {
      "severity": "high",
      "type": "unsupported_fact",
      "message": "Output introduces a new named deputy not present in retrieved canon.",
      "evidence": "Clara saved him",
      "recommendation": "Remove Clara or require human canon approval."
    }
  ],
  "passed_checks": ["story_id", "bible_version", "path_scope"],
  "failed_checks": ["canon_validator"]
}
```

### `approval.yaml`

Human approval record.

```yaml
schema_version: 1
story_id: lone-star-reckoning
bible_version: version-1
chapter_number: 8
approved: true
approved_by: editor
approved_at: 2026-06-07T00:00:00Z
approved_files:
  - chapters/chapter-08/final.md
notes: "Approved after removing unsupported deputy."
new_canon_approved: []
```

### `trace.jsonl`

Append-only raw trace. One JSON object per line.

```jsonl
{"ts":"2026-06-07T00:00:00Z","event":"job_started","story_id":"lone-star-reckoning","chapter_number":8,"stage":"draft-chapter"}
{"ts":"2026-06-07T00:00:02Z","event":"canon_retrieved","story_id":"lone-star-reckoning","chunk_ids":["chunk-character-darin-mayweather","chunk-antagonist-deadeye"]}
{"ts":"2026-06-07T00:00:30Z","event":"draft_written","story_id":"lone-star-reckoning","output":"chapters/chapter-08/draft.md"}
```

## 6. Pipeline Stages

| Stage | Input | Output | Success Status | Failure Behavior |
| --- | --- | --- | --- | --- |
| `init-story` | `story_id`, optional bible file | story folder | `initialized` | fail if story exists unless `--force` |
| `index-bible` | `bible/raw.md` | `bible/version-N/chunks.json`, `meta.json` | `indexed` | fail if raw bible missing |
| `build-context` | story config, chapter number, index | `context.json` | `context_ready` | fail if no canon chunks |
| `plan-chapter` | bible, outline, chapter target | `plan.md` | `planned` | mark `needs_review` if missing canon |
| `draft-chapter` | `context.json`, prompt | `draft.md` | `drafted` | retry only if validator says fixable |
| `humanize-chapter` | `draft.md`, style guide | `humanized.md` | `humanized` | fail if meaning drift detected |
| `check-chapter` | output, context, canon | `qa_report.json` | `passed` or `needs_review` | never hide high-severity issues |
| `diff-chapter` | source and revised files | `diff.md` | `diff_ready` | fail if compared files missing |
| `approve-chapter` | final candidate, QA report | `approval.yaml`, `final.md` | `approved` | reject if QA high-risk unresolved |
| `summarize-chapter` | approved final chapter | L2 summary update | `summarized` | mark memory stale if summary fails |
| `update-memory` | trace and summaries | L3 story state | `memory_updated` | keep old L3 and report failure |
| `export-story` | approved chapters | final exports | `exported` | fail if chapters missing/unapproved |

## 7. CLI Contract

CLI name:

```bash
canonforge
```

Required commands:

```bash
canonforge init-story lone-star-reckoning --bible docs/example-bible.md
canonforge index-bible lone-star-reckoning
canonforge build-context lone-star-reckoning --chapter 8
canonforge plan-chapter lone-star-reckoning --chapter 8
canonforge draft-chapter lone-star-reckoning --chapter 8
canonforge humanize-chapter lone-star-reckoning --chapter 8
canonforge check-chapter lone-star-reckoning --chapter 8
canonforge diff-chapter lone-star-reckoning --chapter 8
canonforge approve-chapter lone-star-reckoning --chapter 8
canonforge export-story lone-star-reckoning
```

Command output should be short and machine-readable enough for scripts:

```text
status=indexed story_id=lone-star-reckoning bible_version=version-1 chunks=32
```

For failures:

```text
status=failed reason=no_retrieved_canon story_id=lone-star-reckoning chapter=8
```

CLI must never ask the model to guess missing identity. If the command lacks
required story information, fail early.

## 8. RAG And Bible Grounding

The story bible is the source of truth. RAG retrieves approved canon; it does
not decide story direction by itself.

Chunk by meaning:

```text
setting
character
antagonist
premise
act
chapter_summary
style_rule
forbidden_change
```

Do not use random token chunks as the primary chunking method for fiction.
Fiction depends on story units.

Every chunk must have:

```yaml
chunk_id: chunk-antagonist-deadeye
story_id: lone-star-reckoning
bible_version: version-1
section_type: antagonist
section_name: Jed "Deadeye" Harlan
source_file: bible/raw.md
text: Jed "Deadeye" Harlan - sharpshooter...
```

Retrieval rules:

- Filter by `story_id`.
- Filter by `bible_version`.
- Reject chunks whose metadata does not match the job.
- Include chunk IDs in every output provenance record.
- If retrieval is weak, mark the context package as risky.

For Chapter 8 of `lone-star-reckoning`, expected retrieval includes:

- `Darin Mayweather`
- `Jed "Deadeye" Harlan`
- `Act 2 - Shadow War`
- `Chapter 8: Rooftop Duel`
- Chapter 7 summary if available
- Chapter 9 summary if available
- Western tone/style rules

## 9. Context Package Builder

Every generation prompt receives a context package. The prompt should not be
assembled by manual copy/paste.

Context package sections:

```text
SYSTEM ROLE
TASK
STORY IDENTITY
RETRIEVED CANON CHUNKS
CURRENT CHAPTER PLAN
PREVIOUS CHAPTER SUMMARY
NEXT CHAPTER SUMMARY
STYLE GUIDE
FORBIDDEN CHANGES
OUTPUT CONTRACT
```

Prompt assembly order:

1. system role
2. non-negotiable rules
3. story identity
4. retrieved canon
5. current task
6. local chapter input
7. output format
8. validation checklist

Rule: retrieved canon must be visible before the model writes.

## 10. Agents As Deterministic Modules

Agents are pipeline modules. They do not freely browse, switch stories, or run
hidden loops.

| Agent | Purpose | Input | Output | Must Not Do |
| --- | --- | --- | --- | --- |
| `IntakeAgent` | Parse source material | bible/raw.md | extracted metadata | invent missing canon |
| `StoryArchitectAgent` | Build outline/plans | bible, summary | outline, chapter plans | override approved bible silently |
| `WriterAgent` | Draft prose | context.json | draft.md | add unsupported canon |
| `HumanizerAgent` | Improve prose | draft.md, style guide | humanized.md | change plot facts |
| `ContinuityAgent` | Check consistency | output, canon, memory | continuity issues | rewrite the chapter |
| `DiffAgent` | Compare versions | two files | diff.md | hide semantic changes |
| `QAAgent` | Combine checks | validator outputs | qa_report.json | approve high-risk output |
| `ExportAgent` | Assemble book | approved chapters | exports | include unapproved chapters |

Each agent must log:

- input files
- output files
- model used
- prompt version
- retrieved chunk IDs
- status
- errors

## 11. Skills And Prompt Files

Skills are reusable instruction files. They prevent one giant fragile prompt.

Required skills:

```text
skills/western_dialogue.md
skills/prose_humanization.md
skills/continuity_checking.md
skills/hallucination_detection.md
skills/diff_review.md
```

Required prompts:

```text
prompts/write_scene.md
prompts/humanize_chapter.md
prompts/check_continuity.md
prompts/summarize_chapter.md
prompts/diff_summary.md
prompts/create_story_bible.md
prompts/build_chapter_plan.md
```

Each prompt file must use this format:

```markdown
# Prompt Name

## Purpose

What this prompt does.

## Inputs

- `story_id`
- `bible_version`
- `context_json`
- `chapter_number`

## Hard Rules

- Do not invent unsupported canon.
- Do not switch story.
- Do not change approved facts.

## Output Format

Describe exact Markdown, JSON, or YAML output.

## Failure Mode

What the model should do when information is missing.

## Validation Checklist

- Canon preserved
- POV preserved
- Timeline preserved
- Output format followed
```

## 12. Validators And Checker Loop

Use Python validators first where deterministic checks are possible.

Python validators:

- path scope validator
- story ID validator
- bible version validator
- retrieved chunk validator
- word count validator
- structure validator
- forbidden words validator
- continuity metadata validator

AI validators:

- unsupported fact detector
- character drift checker
- timeline contradiction checker
- tone checker
- scene-to-summary checker

Checker loop:

```text
generate
-> validate
-> if minor fixable issue, retry
-> validate again
-> retry at most 2 times
-> if still failing, mark needs_review
```

Severity policy:

| Severity | Meaning | Action |
| --- | --- | --- |
| low | formatting or minor style issue | may auto-fix |
| medium | possible drift or weak evidence | retry or review |
| high | unsupported fact, wrong story, wrong canon | needs review |
| critical | cross-story contamination or path escape | fail immediately |

New canon facts require human approval.

Example high-risk flags:

- New character appears without support.
- Darin's Colt becomes a Glock.
- Shadow Ridge becomes Denver.
- Deadeye wounds the left arm in canon, but output says right arm.
- Vance is dead in one chapter but alive later without explanation.

## 13. Memory Design

CanonForge memory is story-scoped. There is no global story memory.

```text
L1 raw trace = what happened
L2 chapter summaries = compressed approved progress
L3 story state = current canon-aware state
```

L1 writes after every job:

- job started
- context built
- chunks retrieved
- model called
- output written
- validators run
- approval/rejection recorded

L2 writes after each approved chapter:

- chapter summary
- scene summary
- new facts introduced
- character changes
- timeline changes
- unresolved threads

L3 writes after L2 update:

- current timeline
- character states
- location states
- open plot threads
- resolved plot threads
- approved canon updates

Chapter 20 should receive:

- bible canon
- Chapter 20 plan
- previous chapter summary
- L3 story state
- retrieved relevant chunks

It should not receive the whole 40,000-word manuscript unless a specific
full-book review stage requires it.

## 14. Code Style And Formatting

Python rules:

- Use typed functions.
- Use Pydantic for external-facing schemas.
- Use dataclasses only for lightweight internal objects.
- Use `pathlib.Path` for paths.
- Resolve paths through a path service before reading/writing.
- Do not pass raw string paths around after resolution.
- Do not keep global mutable state for the current story.
- Do not silently fall back to another story.
- Raise explicit errors for missing `story_id`, missing `bible_version`, and empty retrieval.
- Keep functions small enough to test.

Markdown rules:

- Use clear headings.
- Use fenced code blocks with language labels.
- Use tables only where they make comparison easier.
- Keep examples concrete.

JSON/YAML rules:

- Include `schema_version`.
- Use stable keys.
- Use human-readable IDs.
- Include `story_id` and `bible_version` on story-scoped artifacts.
- Keep machine reports parseable.

## 15. Testing Strategy

Unit tests:

- chunker detects setting, character, antagonist, act, and chapter summary chunks
- retriever filters by `story_id`
- retriever filters by `bible_version`
- path service rejects traversal and cross-story reads
- validators catch wrong metadata
- word count validator handles tolerance
- forbidden words validator catches configured terms

Integration tests:

- initialize `lone-star-reckoning`
- index `docs/example-bible.md`
- build Chapter 8 context
- draft with deterministic stub
- check draft
- create diff
- approve final
- export final Markdown

Regression tests:

- wrong story chunks are rejected
- missing `story_id` fails
- missing `bible_version` fails
- no retrieved canon fails
- retry loop stops at `max_auto_retries`

Golden tests using `docs/example-bible.md`:

- index creates `version-1`
- Chapter 8 retrieval includes Darin
- Chapter 8 retrieval includes Deadeye
- Chapter 8 retrieval includes Act 2
- Chapter 8 retrieval includes Chapter 8 summary
- wrong weapon/location/arm injury are flagged
- final export is created only from approved chapters

## 16. Documentation Requirements

This file is the master blueprint.

Add these docs later:

```text
docs/canonforge-architecture.md
docs/canonforge-cli.md
docs/canonforge-story-folder-format.md
docs/canonforge-rag-and-memory.md
docs/canonforge-validator-guide.md
docs/canonforge-model-routing.md
docs/canonforge-prompt-and-skill-guide.md
docs/canonforge-testing-guide.md
```

Each doc should include:

- purpose
- expected users
- file examples
- command examples
- failure examples
- acceptance checks

## 17. Build Order

Build in this order:

1. Story template.
2. Path scoping service.
3. Pydantic schemas.
4. Bible chunker.
5. Bible versioning.
6. Retriever with strict story/version filter.
7. Context package builder.
8. Deterministic draft stub.
9. Python validators.
10. QA report writer.
11. Diff generator.
12. Approval workflow.
13. Markdown export.
14. Local model router.
15. LlamaIndex integration.
16. Chroma/FAISS integration.
17. Humanizer agent.
18. Continuity AI checker.
19. Memory L2/L3 consolidator.
20. Optional dashboard only after CLI pipeline works.

First proof target:

```text
one story
one bible
one chapter
one context package
one draft
one QA report
one diff
one approval
one export
```

## 18. Future Production Path

After the local pipeline works:

1. Add queue support for many chapters.
2. Add model routing by task.
3. Add cost and token tracking.
4. Add dashboard for status and review.
5. Add database only when file folders become painful.
6. Add global search only after per-story isolation is proven.
7. Add multi-user permissions only after single-user production works.

Production should still preserve the same rule:

```text
story identity first
canon retrieval second
generation third
validation fourth
human approval before canon mutation
```

## 19. Non-Negotiable Rules

- No chat-first design.
- No cross-story retrieval.
- No generation without `story_id`.
- No generation without `bible_version`.
- No generation without retrieved canon.
- No hidden canon mutation.
- No endless model loops.
- No global story memory.
- No database-first architecture.
- No dashboard before pipeline works.
- No final export from unapproved chapters.

CanonForge succeeds only if every output can answer:

```text
Which story?
Which bible version?
Which canon chunks?
Which prompt?
Which model?
Which validator results?
Which human approval?
```

If the system cannot answer those questions, the output is not production
ready.
