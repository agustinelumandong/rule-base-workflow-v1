# Headroom Context Compression Plan For BookForge

**Status:** reference plan  
**Source:** BookForge owner review note, Headroom public repository, and Headroom LiteLLM integration docs  
**Scope:** optional context optimization, not a core writing engine  
**Decision:** evaluate Headroom safely as a context-compression adapter, but do not make it required infrastructure until BookForge benchmarks prove no canon or review-quality regression.

## Summary

Headroom is worth tracking for BookForge because it targets a real pressure point: long context, noisy tool output, repeated validator reports, large retrieval results, and expensive model calls. Its repository describes it as a context compression layer for AI agents that can compress tool outputs, logs, RAG chunks, files, and conversation history before they reach an LLM. The README also describes library, proxy, agent wrapper, and MCP modes, plus local-first reversible compression with cached originals available for retrieval.

BookForge should not treat Headroom as a writing engine, reviewer, canon authority, memory authority, or source-of-truth store. It should be an optional adapter inside a broader BookForge context optimization layer.

## Safety Rule

Compressed context is not truth.

```text
canonical source remains unchanged
-> selected context may be compressed for presentation
-> model reads the scoped package
-> validators compare output against original approved sources
-> humans approve final changes
```

BookForge must never replace these with compressed text:

- Canon bible
- Character profiles
- Timeline
- Continuity locks
- Chapter contracts
- Plot lock files
- Approval records
- Final manuscript text

These may be summarized for display or prompt budgeting only when the original source IDs and versions remain linked, retrievable, and used by validators.

## Why It Fits

BookForge will produce and consume large context surfaces:

- Chapter context packages
- Canon and style excerpts
- Validator reports
- QA reports
- Diff output
- Agent logs
- RAG or knowledge-base previews
- Previous chapter summaries
- Local tool output

The safest first use is compressing non-canonical presentation material: logs, tool output, validator reports, diff summaries, QA reports, retrieval previews, and agent scratch context.

The unsafe use is direct compression of canonical narrative source as the only model input. Long-form fiction depends on small details. If compression drops a weapon count, relationship boundary, location fact, injury state, timeline fact, or naming rule, the writing model can produce plausible but wrong prose.

## Proposed BookForge Architecture

Headroom, if used, should sit behind BookForge services:

```text
BookForge stage service
-> Context Builder
-> Context Ranker
-> Context Budgeter
-> Optional Context Compressor
-> Context Audit Log
-> Provider adapter
-> Validators against original sources
-> ReviewDesk approval
```

The compressor is replaceable. BookForge owns policy, provenance, validation, review, and artifact state.

## Phase Placement

### Phase 2

Allowed:

- Context-compression policy placeholder
- No-op compression service boundary
- Compression disabled by default
- Tests proving compression cannot be required for local operation
- Tests proving canonical sources are not replaced

Not allowed:

- Headroom dependency
- LiteLLM middleware
- Real model provider path
- RAG compression dependency
- Any compressor as a required part of local author workflow

### Phase 3

Allowed as experiment:

- Compress validator reports
- Compress tool output
- Compress logs
- Compress QA reports
- Compress retrieval previews
- Compare compressed vs uncompressed model runs

Promotion gate:

- No increase in canon violations
- No unsupported-fact regression
- No style-quality regression
- No worse human review score
- Clear token or latency benefit
- Retrieval fallback works
- Original source IDs and versions are preserved in trace

### Phase 7

Allowed after retrieval benchmarks:

- RAG chunk compression
- Context deduplication around retrieval previews
- Compression-aware retrieval fallback
- Optional MCP adapter if it remains useful

## Policy Shape

Example future policy:

```yaml
context_compression:
  enabled: false
  provider: headroom
  mode: library
  compress_tool_output: true
  compress_logs: true
  compress_validator_reports: true
  compress_diff_summaries: true
  compress_retrieval_previews: false
  compress_canon: false
  compress_character_profiles: false
  compress_timeline: false
  compress_approval_records: false
  require_retrieval_fallback: true
  require_original_source_ids: true
  promotion_requires_benchmark: true
```

The default is disabled. No narrower policy scope may enable compression for canonical source replacement.

## Benchmark Plan

Run the same fixture twice:

```text
same project
same source artifact
same canon version
same prompt
same persona
same model/provider
same validator set
one run uncompressed
one run compressed
```

Compare:

- Canon violations
- Unsupported facts
- Meaning preservation
- Character voice drift
- Style score
- Human review score
- Reviewer override rate
- Token usage
- Latency
- Retrieval fallback rate
- Trace completeness

Token savings alone do not justify promotion.

## Recommended Integration Order

1. Validator report compression
2. Tool and log compression
3. QA and diff summary compression
4. Retrieval preview compression
5. Agent scratch-context compression
6. Optional LiteLLM middleware after provider routing exists
7. Optional MCP tools after BookForge has a real agent surface

Do not compress manuscript text or canonical truth as the only source until dedicated narrative-fact preservation tests exist and pass.

## References

- Headroom GitHub repository: https://github.com/chopratejas/headroom
- Headroom README claims checked 2026-06-13: context compression for tool outputs, logs, RAG chunks, files, and conversation history; library, proxy, agent wrapper, MCP mode; local-first reversible compression; published token-savings and benchmark examples.
- Headroom LiteLLM integration docs: https://github.com/chopratejas/headroom/blob/main/docs/content/docs/litellm.mdx
- LiteLLM integration claims checked 2026-06-13: callback compression before provider calls, proxy middleware option, direct `compress()` usage, and provider-router placement.
- BookForge master plan integration point: `docs/info-plan/BOOKFORGE-MASTER-PLAN.md`, sections on compressed context, context optimization and compression, context compression policy, evaluation benchmarks, Phase 2, and Phase 3.
