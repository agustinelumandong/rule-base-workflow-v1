# BookForge Ecosystem Evaluation

**Purpose:** Track external projects as architecture references or potential adapters without allowing tool popularity to determine BookForge's design.
**Policy:** Verify current official documentation, license, security posture, maintenance status, and compatibility immediately before adoption.

> Use this evaluation as a constraint document, not as a shopping list. Listed projects may be studied for architecture ideas, but they may become dependencies only when they solve a measured BookForge deficiency, pass license and risk review, integrate behind a BookForge-owned adapter, preserve deterministic test paths, and cannot mutate canon, approve artifacts, bypass validation, or publish.

## Decision Rules

- BookForge domain schemas, canon lifecycle, artifact lineage, workflow state, approvals, and publication gates remain authoritative.
- External systems integrate behind BookForge-owned interfaces.
- Auto-extracted facts, claims, relationships, and graph edges remain proposed until reviewed.
- Project isolation and provenance filters apply to every adapter.
- A reference becomes a dependency only through a documented architecture decision and benchmark.
- License ambiguity blocks code, prompt, or asset reuse until resolved from authoritative repository files.

## Evaluated References

| Project | Potential value | Main risks | Earliest phase | Decision |
| --- | --- | --- | --- | --- |
| **DeepTutor** | Full-stack patterns for document ingestion, provider settings, memory, citations, visualization, and tool execution | Education-specific domain, agent-first authority, RAG-first assumptions, license must be rechecked | Phase 5 reference; selected adapters Phase 7+ | Architecture inspiration only; do not clone |
| **LlamaIndex** | Document loaders, indexing, retrieval abstractions, and research ingestion | Framework coupling and accidental elevation of retrieval to authority | Phase 7 | Optional ingestion/retrieval adapter |
| **LightRAG** | Graph-enhanced retrieval and entity/relation exploration | Auto-extracted graph pollution, infrastructure complexity, canon conflicts | Phase 7 | Evaluate against BookForge graph and retrieval benchmarks |
| **AutoAgent** | Agent utility and tool-loop concepts | Self-directed workflow, uncontrolled effects, provenance and budget risk | Phase 8 research | Do not use as workflow authority |
| **AI-Researcher** | Research-question decomposition, source gathering, claim extraction, and cited synthesis | Scientific-discovery assumptions and excessive autonomy | Phase 7 | ResearchCore design reference; adapt heavily |
| **nanobot** | Lightweight assistant, tool registry, routing, MCP, and local UI patterns | Assistant becoming product authority or bypassing gates | Phase 5 or 8 | Interface inspiration behind capability registry |
| **ManimCat / Manim** | Future timeline, lore, relationship, or educational visual assets | Low relevance and code-execution surface | Phase 8 | Not part of core BookForge |

## DeepTutor Translation

```text
DeepTutor pattern:
documents -> knowledge base -> RAG/graph -> agents -> learning output

BookForge translation:
approved canon and plans -> scoped context -> controlled worker
-> validators -> targeted revision -> human approval -> publication artifact
```

Concepts worth studying:

- Multi-provider configuration
- Local install, web app, and container packaging
- Document and office-file ingestion
- Citation and provenance memory
- Graph and timeline visualization
- Restricted execution workers
- Long-running task progress

Concepts explicitly rejected as BookForge foundations:

- Education-specific learner/session domain models
- Agents owning workflow state or truth
- RAG or graph extraction defining canon
- Unrestricted tools or generated code
- Automatic approval or publication
- Multi-channel chat before the production engine is stable

## Adapter Boundaries

Potential adapters must implement BookForge contracts rather than leaking framework types into application modules:

```text
ingestion: web, PDF, DOCX, EPUB, Markdown, approved archives
retrieval: structured, lexical, full-text, vector, graph
research: search, source snapshot, claim extraction, evidence linking
assistant: command translation, tool registry, permissions
export: predefined document formatters and restricted analysis workers
```

### Adapter output states

Every persisted adapter output follows an explicit lifecycle:

```text
raw_imported
-> parsed
-> extracted_candidate
-> normalized_candidate
-> under_review
-> approved | rejected
-> superseded
```

- `raw_imported` preserves the received source or response with provenance and content hash.
- `parsed` represents mechanically decoded content, not trusted meaning.
- `extracted_candidate` contains proposed claims, facts, relationships, summaries, or entities.
- `normalized_candidate` conforms to BookForge schemas but remains unapproved.
- `under_review` is frozen for a specific human or policy review.
- `approved` may influence authoritative workflows only within its declared scope.
- `rejected` remains auditable but cannot enter approved context.
- `superseded` preserves lineage to its replacement.

Schema validity, successful retrieval, model confidence, or adapter reputation must never promote an output automatically.

### Allowed adapter effects

- Read explicitly scoped project artifacts and approved indexes.
- Produce candidate artifacts with project, source, version, and provenance metadata.
- Return retrieval results with score, source, scope, and approval state.
- Propose claims, facts, relationships, summaries, or visual projections.
- Produce reports, visualizations, and export candidates.
- Request declared BookForge application services through the capability registry.

### Forbidden adapter effects

- Approve, mutate, supersede, or delete approved canon.
- Approve artifacts or accepted risks.
- Publish or mark an export publication-ready.
- Bypass validators, review gates, budgets, or workflow transitions.
- Access artifacts, indexes, credentials, or caches from another project or tenant.
- Call undeclared tools or expand its own permissions.
- Persist hidden memory, workflow state, or authoritative records outside BookForge.
- Perform undeclared network, filesystem, subprocess, or code-execution operations.

## Adoption Checklist

Before adopting any project:

- Confirm exact use case and measurable deficiency in existing BookForge services.
- Verify current license from the repository `LICENSE` and package metadata.
- Review dependency and supply-chain risk.
- Review network, filesystem, code-execution, and data-retention behavior.
- Confirm project and tenant isolation.
- Confirm offline or deterministic test substitutes.
- Define failure, timeout, cancellation, and fallback behavior.
- Benchmark quality, latency, cost, and operational complexity.
- Prove the adapter cannot mutate canon, approve artifacts, or publish.
- Record adopt, defer, reject, or replace decision with date and owner.

## Kill Criteria

Reject, remove, or replace a dependency when any of these conditions holds:

- It cannot preserve project and tenant isolation.
- Framework-specific types or lifecycle assumptions leak into core domain or application services.
- It cannot support deterministic or offline test substitutes where required.
- Its license, source provenance, maintenance, supply chain, or data-retention behavior creates unacceptable risk.
- It adds operational or conceptual complexity without measurable quality, reliability, cost, or throughput improvement.
- It cannot provide sufficient provenance and lineage for persisted outputs.
- It performs hidden or uncontrollable network, filesystem, subprocess, telemetry, or code-execution behavior.
- Its retrieval, extraction, or generation results fail BookForge's acceptance thresholds.
- It can bypass capability permissions, validation, review, approval, or publication gates.
- A simpler BookForge-owned implementation satisfies the measured requirement with lower long-term risk.

Adoption is reversible. The architecture decision must define removal conditions, owned data formats, migration or re-indexing strategy, and the BookForge interface that survives replacement.

## Reference Links

- DeepTutor: <https://github.com/HKUDS/DeepTutor>
- LlamaIndex: <https://github.com/run-llama/llama_index>
- LightRAG: <https://github.com/HKUDS/LightRAG>
- AutoAgent: <https://github.com/HKUDS/AutoAgent>
- AI-Researcher: <https://github.com/HKUDS/AI-Researcher>
- nanobot: <https://github.com/HKUDS/nanobot>
- Manim: <https://github.com/ManimCommunity/manim>

Links are discovery pointers only. Paths, casing, ownership, names, and licenses may change or redirect. Re-verify them from current authoritative repository and package metadata before use.
