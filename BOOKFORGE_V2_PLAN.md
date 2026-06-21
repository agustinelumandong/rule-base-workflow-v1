# BookForge v2 — Merged Architecture (draft — not frozen)

> **One line:** Event-sourced canon, gated by validate-before-apply, fed by a swappable
> persistent-memory tier (Headroom as reference), driven through an agent-agnostic `bf` CLI,
> orchestrated by a model-routing harness (OpenCode as reference) that sends cheap models at
> extraction and strong models at prose. One engine, layered vocabularies, no tool lock-in.

This supersedes both prior drafts (`REPO_FIX_PLAN.md` folds into M0 + M3). Two layers were
missing in earlier drafts and are now first-class: the **Persistent Memory Tier** (Headroom
et al.) and the **Harness / Model-Routing Layer** (OpenCode et al.). Model routing is encoded
in the repo, not assumed.

> **Status — not frozen.** This is the current merged draft, not a frozen architecture. The
> command-surface fixes from review (canon/memory split, proposal-based learning) are applied
> below. The load-bearing unknown is **fold-engine feasibility for narrative state** (see §13)
> — prototype that on a real book's `continuity-out.md` chain before treating this as final.

> **Execution order — where `REPO_FIX_PLAN.md` fits.** `REPO_FIX_PLAN.md` is **not** a separate
> predecessor. It is the foundation slice of this plan — every phase of it is absorbed into a
> v2 milestone (full mapping in Appendix B). Execute it *as* M0, not as a standalone project:
>
> ```
> M0   = REPO_FIX_PLAN Phase 0, 1, 7   ← do FIRST (hygiene, defaults, golden tests)
> M1   = REPO_FIX_PLAN Phase 3         ← decouple (entry surface, AGENTS.md → bf)
> M2   = NEW v2 work                   ← event-sourced canon
> M2.5 = NEW v2 work                   ← persistent memory tier
> M3   = REPO_FIX_PLAN Phase 2, 4, 5, 6 ← cleanup (exceptions, validator, adapters)
> M4, M5
> ```
>
> Golden tests must be captured in M0 **before** the M2/M3 refactor — that is the one hard
> sequencing constraint. See Appendix B for the phase-by-phase mapping.

---

## 1. The Five-Layer Architecture

```
LAYER 5 — AGENT HARNESS (OpenCode as reference; Claude Code / Codex / Cursor / Copilot / Zed)
  ├─ model routing: small_model → extraction/alias/continuity; strong model → prose only
  ├─ subagents + MCP connections
  └─ reads AGENTS.md + a generated per-agent instruction file
        │ calls
        ▼
LAYER 4 — bf CLI (the agent-agnostic contract; any agent can drive it)
        │ uses
        ▼
LAYER 3 — PERSISTENT MEMORY TIER
  ├─ MemoryBackend Protocol: retrieve(query) / learn(failed_session) / stats()
  ├─ HeadroomBackend (reference) — usable as Python library OR as MCP server
  ├─ LocalEmbeddingBackend (zero-dep fallback)
  ├─ VectorDBBackend (future)
  └─ two exposure modes:
       bf memory search/resolve/learn  (default, agent-agnostic)
       bf memory serve --mcp           (opt-in, for agents that prefer agent-driven calls)
        │ reads/writes (semantic retrieval over canon + drafts + accumulated history)
        ▼
LAYER 2 — THE GATE (OpenSpec invariant; non-negotiable)
  bf validate MUST pass → bf apply is the ONLY canon mutation path
        │ protects
        ▼
LAYER 1 — CANON TIER (event-sourced)
  entities (static defs) + events (append-only) + fold(snapshot, derived/rebuildable)
```

**Hard rules:** Layer 2 is non-negotiable (no drift). Layer 3 never *is* canon — it retrieves
and compresses *around* it. Layer 5 is swappable (no lock-in to OpenCode or any one harness).

---

## 2. Why the Merge Works

### 2.1 Four vocabularies, one engine (git-flow / event-sourcing / save-state / OpenSpec)

| Concept | git-flow | event sourcing | save-state | OpenSpec |
|---|---|---|---|---|
| Canonical state | main branch | aggregate state | save file | specs/ |
| Unit of change | feature branch | event | checkpoint | change |
| Validation | CI on PR | validate-on-apply | load+check | openspec validate |
| Promote | merge | append event | save | openspec apply |

All four are the same machine. Exposed as Layer-4 CLI aliases so writers, collaborators,
architects, and agents each get their vocabulary.

### 2.2 Three memory options, one subsystem

| Want | First-class tier | Headroom MCP | Pluggable adapter |
|---|---|---|---|
| Agent-agnostic (no MCP dependency) | ✅ | ❌ | ✅ |
| Reuse Headroom's existing MCP | ❌ | ✅ | ⚠️ only if it's a backend |
| Swappable / no tool privileged | ⚠️ Headroom privileged | ❌ Headroom-only | ✅ |
| Works even when agent doesn't speak MCP | ✅ | ❌ | ✅ |

**Merge:** one `MemoryBackend` Protocol; Headroom is the reference backend exposed both as a
library (via `bf memory`) and optionally as an MCP server (`bf memory serve --mcp`); cheap
models do extraction via the harness.

---

## 3. Model Routing (the "strong models only for prose" goal, encoded)

The harness (OpenCode et al.) does the routing, but BookForge *declares* the intent so it's
agent-agnostic and reproducible.

```yaml
# spec/model-routing.yml (or persona-registry.json, migrated)
personas:
  extractor:                 # cheap/local — memory extraction, alias resolution, summaries
    model_class: cheap
    examples: [gemini-flash, gpt-4o-mini, local-7b]
    tasks: [memory_build, resolve_alias, summarize_continuity, classify_beats]
  reviewer:                  # mid — validation review, style flags
    model_class: mid
    examples: [gpt-4o, claude-haiku]
    tasks: [validate_review, style_scan_semantic]
  writer:                    # strong — PROSE ONLY
    model_class: strong
    examples: [claude-sonnet, gpt-4o, opus]
    tasks: [draft_prose]
```

- `AGENTS.md` references this; `bf init --agents opencode` emits an OpenCode config that maps
  `small_model` → extractor, default model → writer; `bf init --agents claude` emits a subagent
  definition; `bf init --agents codex` emits a task-type hint file.
- `bf check-persona --persona writer` (already in `persona.py`) enforces this registry.

**Layer 5 is optional.** The model-routing tier is a cost optimization, not a requirement.
BookForge fully works without OpenCode or any routing-capable harness. Any agent that can read
files and run shell commands — Codex CLI, Claude Code, Gemini CLI, Cursor, Copilot CLI, ZCode,
Zed, or equivalent — can drive the full cycle by reading `AGENTS.md` and calling `bf`.

Without a routing harness, the workflow still functions, but one model handles all
model-assisted tasks. The only lost optimization is automatic task routing: extraction, alias
resolution, and summaries no longer go to a cheap model automatically, while prose no longer
routes separately to a stronger model. The architecture remains valid because `bf` is the
contract; model routing is only an efficiency layer.

```
Minimum viable agent layer:   Any shell-capable agent + AGENTS.md + bf
Optimized agent layer:        OpenCode or equivalent harness + model routing
Core product:                 BookForge CLI + canon + validation + memory
```

---

## 4. Canon Model (Layer 1 — event-sourced)

```
books/<book-slug>/
  canon/
    entities/                      # STATIC definitions
      characters.yml               # canonical name, role, physical marker, voice, POV, first_seen
      aliases.yml                  # alias -> entity (Tex -> tex_cade)
      locations.yml                # places + function
      objects.yml                  # MacGuffins/signature gear
    events/                        # APPEND-ONLY — Layer 1
      chapter-01.event.yml         # structured continuity-out
      chapter-02.event.yml
    state/
      snapshot.yml                 # DERIVED fold (rebuildable; bf memory build regenerates it)
  spec/
    premise.md  guardrails.md  tone.md  chapters.yml  model-routing.yml
  changes/
    chapter-NN/  proposal.md  beats.md  draft.md  continuity-out.md  packet.md
  state/  loop.json  analytics.json
  research-pack.md
```

`continuity-out.md` → event mapping:

| continuity-out section | Event mutation |
|---|---|
| Characters (alive/injured/absent) | status mutations |
| Changes (possessions/injuries/secrets/alliances/resources) | inventory/relationship/secret mutations |
| Locations (where key characters end) | location mutations |
| Human Stakes Carried / Unresolved Pressure | carried-forward state (part of the fold) |
| Next Chapter Must Know | invariants the next event must not violate |

`bf memory build` folds entities+events into `snapshot.yml` (lossless rebuild — delete it,
regenerate from events). This is the OpenSpec invariant made literal: source of truth is only
ever reached by replaying validated events.

### Entity memory (~200–500 tokens per packet)

```yaml
# canon/entities/characters.yml
characters:
  tex_cade:
    canonical: "Tex Cade"
    role: protagonist
    physical_marker: "scar on left hand"
    voice: "clipped, few words, Texas plain"
    pov: allowed
    first_seen: chapter-01
  mara_vale:
    canonical: "Mara Vale"
    role: ally
    physical_marker: "red bandana, braided hair"
    voice: "formal, educated"
    pov: disallowed
    first_seen: chapter-02

# canon/entities/aliases.yml
aliases:
  tex: tex_cade
  cade: tex_cade
  "mr. cade": tex_cade
  miss vale: mara_vale
  mara: mara_vale
```

---

## 5. CLI Surface (Layers 2/3/4 — one engine, aliased vocabularies)

```
# Gate (Layer 2 — non-negotiable)
bf validate [<book>] [--chapter N] [--review-prompt]
bf apply change <book> <chapter-id>          # append event + re-fold, only if validate passes

# Writer verbs (Layer 4 aliases over the gate)
bf checkpoint save|load|diff|restore

# Canon fold (Layer 1 — deterministic state; never touches the memory tier)
bf canon build <book>                        # re-fold entities + events into canon/state/snapshot.yml
bf canon validate <book>                     # validate entities, events, snapshot coherence

# Persistent memory (Layer 3 — semantic/retrieval; NEVER is canon)
bf memory build <book>                       # build/refresh semantic index over canon + drafts + history
bf memory search <book> "<query>"            # semantic retrieval (Headroom retrieve / local embedding)
bf memory resolve <book> "<name>"            # alias -> canonical entity
bf memory learn <book> <failed-session>      # produce a learning PROPOSAL; does NOT mutate AGENTS.md
bf memory apply-learning <book> <proposal-id>  # validate + promote approved rule into AGENTS.md / spec/
bf memory serve --mcp [--transport stdio|http]  # expose active backend as MCP tools (opt-in)
bf memory stats [<book>]

# Inspection / loop / compile
bf status  bf packet render|compress  bf loop  bf compile

# Setup / adapters / config
bf init <book> [--from <prior>] [--agents opencode,claude,codex,cursor,zed] [--git]
bf migrate <book>
bf adapter list                              # compression + research + memory backends
bf config show|set|get                       # selects active backends + routing
bf check-persona --persona <p> --action <a>  # enforce model-routing.yml
```

---

## 6. Agent Integration (Layer 5 — harness-aware, not harness-locked)

- **Primary:** `AGENTS.md` — agent-neutral, references `bf` + canon + model-routing.
- **Per-agent shims** (generated by `bf init --agents ...`): `CLAUDE.md`, `.cursor/rules`,
  `copilot-instructions.md`, `GEMINI.md`, **and an OpenCode config** that wires `small_model`
  → extractor persona. Each is a thin importer of `AGENTS.md` plus a tool-specific note.
- OpenCode is *privileged as the reference harness* (because of its model routing) but **not
  required** — any file-reading agent works. No Codex/Antigravity/Gemini/OpenCode names
  hardcoded in the engine or canonical docs.
- Western-subgenre skills (Claude-Code `SKILL.md` convention with `compatibility`/
  `allowed-tools` frontmatter) move to agent-neutral markdown under `spec/` or `references/`.

---

## 7. Adapter Interfaces (Layers 3 + compression/research)

```python
# Layer 3 — Persistent Memory
class MemoryBackend(Protocol):
    def retrieve(self, query: str) -> list[Chunk]: ...
    def learn(self, failed_session) -> list[Rule]: ...
    def stats(self) -> MemoryStats: ...

class HeadroomMemoryBackend: ...      # reference; uses headroom retrieve/stats/learn + SharedContext
class LocalEmbeddingBackend: ...      # zero-dep fallback
class VectorDBBackend: ...            # future

# Compression (packet/context)
class CompressionBackend(Protocol):
    def compress(self, text: str) -> str: ...

class LocalRegexBackend: ...
class HeadroomBackend: ...

# Research
class ResearchBackend(Protocol):
    def query(self, q: str) -> str: ...
    def ingest(self, src) -> None: ...

class ManualBackend: ...
class NotebookLMBackend: ...
```

Engine core depends only on Protocols. `bf config` selects backends. `notebooklm.py`
(573 lines, 12 bare excepts) shrinks to one adapter.

---

## 8. Three-Layer Memory (target, expanded)

```
Agent Harness (OpenCode/Claude/Codex/Cursor/Copilot/Zed)  = workflow memory (ephemeral)
   |  reads AGENTS.md + model-routing, calls bf
   v
bf CLI (agent-agnostic contract)
   |
   ├─► Persistent Memory Tier (Headroom / local embedding) = working/semantic memory
   |     (retrieves & compresses AROUND canon; never is canon; cross-session; learns)
   |
   └─► Canon Tier (event-sourced entities + events + fold) = CANON memory (authoritative)
```

Canon never lives only in Headroom's embedded chunks. Headroom compresses/retrieves *around*
the canon files.

---

## 9. Milestones (re-phased; M2.5 is NEW for the memory tier)

### M0 — Foundation & Hygiene (~3 days, zero-risk)
- Remove root scratch files (`compile_helper.py`, `scratch_*.py`)
- Un-ignore `tests/` and `docs/` in `.gitignore`
- Fix `tex-cade` → `book-example` defaults (22 files)
- `bf` no-arg → `status` (Windows-safe; demote TUI to `bf tui`)
- Capture golden-file tests for current loop/validator output (regression net)
- **Shippable:** cleaner repo, works on Windows, tests tracked.

### M1 — Decouple from Agents + Model Routing Skeleton (~5 days, parallel with M2)
- Strip Codex/Antigravity/Gemini names from `AGENTS.md`, `docs/workflow-v5.md`, all
  `SKILL.md` files, `loop.py`/`cli.py` help text
- Establish `AGENTS.md` as primary; build `bf init --agents` to generate `CLAUDE.md` /
  `.cursor/rules` / `copilot-instructions.md` / `GEMINI.md` / **OpenCode config**
- **Define `spec/model-routing.yml`** (extractor/reviewer/writer personas); wire
  `bf check-persona` to enforce it; have `bf init --agents opencode` emit `small_model` mapping
- Convert 13 shim scripts to `bf` aliases or remove; rewrite `AGENTS.md` to `bf`
- Remove `.agents/skills/*/agents/openai.yaml`; consolidate skill content into agent-neutral md
- Demote TUI (carried from M0 if not done): `bf tui` opt-in with POSIX guard
- **Shippable:** any agent drives the system; model-routing intent declared in-repo.

### M2 — Event-Sourced Canon Core (Layers 1+2, ~6-8 days, parallel with M2.5/M3)
- Define `canon/entities/*.yml` schemas (characters, aliases, locations, objects) + validation
- Define `canon/events/chapter-NN.event.yml` schema (structured continuity-out → event)
- Build the **fold engine**: `bf canon build` re-derives `canon/state/snapshot.yml` from
  entities + events (canon fold is Layer 1, NOT the memory tier)
- Build canon validators: alias resolution, timeline ordering, cross-event consistency (the
  "no dead character acting" check), entity-vs-event coherence
- Build `bf migrate` (old rulebook/world-state/relationships/continuity-out → entities +
  events, lossless, idempotent)
- **Build the gate (Layer 2):** `bf apply change` as the ONLY canon mutation path;
  `bf validate` must pass before append
- Separate `loop-state.json` into pure controller state (`state/loop.json`) — remove
  NotebookLM coupling
- **Shippable:** event-sourced canon with protected source of truth; entity lookup works;
  rollback is a fold replay.

### M2.5 — Persistent Memory Tier (Layer 3, ~4-5 days, parallel with M3) — NEW
- Define `MemoryBackend` Protocol (retrieve/learn/stats)
- `HeadroomMemoryBackend`: wraps `headroom.compress`/`retrieve`/`stats` + `headroom learn` +
  `SharedContext`; usable as library via `bf memory *`
- `LocalEmbeddingBackend`: zero-dep fallback (TF-IDF / keyword index over canon+drafts+history)
- `bf memory build/search/resolve/learn/apply-learning/stats`, where `learn` creates a
  proposal and `apply-learning` validates + promotes approved rules into `AGENTS.md` / `spec/`
- `bf memory serve --mcp`: expose the active backend as MCP tools (headroom_compress/
  retrieve/stats) for agents that prefer agent-driven calls — **opt-in, not required**
- `bf memory learn` writes corrective rules into `AGENTS.md` (the headroom-learn loop)
- **Shippable:** persistent cross-session semantic memory; Headroom first-class but swappable;
  agent-agnostic by default, MCP-optional.

### M3 — CLI Vocabularies + Adapters + Cleanup (Layer 4 + compression/research, ~6-8 days, parallel)
- Implement Layer 4 writer verbs as aliases over the gate: `bf checkpoint save/load/diff`,
  `bf restore`
- Implement Layer 4 opt-in: git-tracking guidance, `bf init --git` for branch-per-chapter
  workflow
- Reorganize `bf` subcommands per §5
- Implement adapter Protocols; move `headroom.py` and `notebooklm.py` behind
  `adapters/compression.py` and `adapters/research.py`
- Rewrite context-packet renderer to pull from `canon/` (fallback to old `rulebook.md`)
- Fix the 45 bare `except Exception` sites (specific exceptions + logging) — correctness-critical
- Fix `FORBIDDEN_LENGTH_LANGUAGE` `"words"` false-positive (restrict to planning artifacts)
- Finish `ManuscriptIssue` type migration in `loop.classify` (remove `list[object]` duck-typing)
- Decompose `validator.py` (1,505 lines) into focused submodules behind a facade
- **Shippable:** clean CLI, multi-vocabulary, adapter-pluggable, trustworthy validation.

### M4 — Full Change Workflow (~3-4 days, on top of M2+M2.5+M3)
- `changes/chapter-NN/proposal.md` + `beats.md` as the authoring unit
- `bf apply change <book> <id>` promotes: validate → append event → re-fold → compile draft →
  archive change
- `bf validate --chapter N` enforces chapter-vs-spec before apply (the OpenSpec
  "validate before merge")
- `bf apply` refuses if validation fails — the deterministic gate made visible
- **Shippable:** chapter work follows proposal→validate→apply discipline; canon stays clean.

### M5 — Polish, Docs, Deprecation (~2-3 days)
- Comprehensive `AGENTS.md` rewrite (agent-neutral, `bf`-based, references 5-layer model)
- Per-agent instruction generation finalized (incl. OpenCode `small_model` config)
- Deprecation warnings on old paths (`rulebook.md` direct edits, old script paths), then removal
- Full test suite: canon validators, fold engine, memory backends, adapters, golden files
- Cross-platform `scripts/install.py` (replaces bash-only `install.sh`)
- **Shippable:** documented, tested, portable, ready for any harness.

### Suggested timeline (M1 / M2 / M2.5 / M3 overlap per the parallel priority)

```
Week 1:   M0 (foundation + golden tests)
Week 1-2: M1 (decouple + model-routing skeleton)
Week 2-3: M2 (event-sourced canon)  ┐
          M2.5 (persistent memory)  ├ parallel
          M3 (CLI + adapters)       ┘
Week 3:   merge + M4 (change workflow)
Week 4:   M5 (polish/docs/deprecation)
```

---

## 10. What Gets Removed / Deprecated

| Item | Fate | Milestone |
|---|---|---|
| `compile_helper.py`, `scratch_*.py` | Deleted | M0 |
| `tex-cade` defaults (22 files) | Replaced with `book-example` or real sample | M0 |
| Codex/Antigravity/Gemini names in docs/engine | Stripped | M1 |
| `.agents/skills/*/agents/openai.yaml` | Removed | M1 |
| 13 shim scripts | Thin `bf` aliases or removed | M1 |
| `notebooklm.py` (573 lines) | One adapter behind Protocol | M3 |
| `humanizer` Claude-Code frontmatter | Agent-neutral markdown | M1 |
| TUI as no-arg default | Opt-in `bf tui` | M0 |
| `rulebook.md` (monolithic) | Superseded by `canon/` + `spec/`; deprecated after M2 | M2/M5 |
| `world-state.json` / `relationships.json` | Migrated into `canon/entities/` + events | M2 |
| 45 bare `except Exception` | Specific exceptions + logging | M3 |

---

## 11. Acceptance Criteria — "v2 done" means

- [ ] Any agentic single-model agent — Codex CLI, Claude Code, Gemini CLI, Cursor, Copilot
      CLI, ZCode, Zed, or equivalent — can drive a full book cycle by reading only `AGENTS.md`
      and calling `bf`; **no routing harness is required.**
- [ ] *Optional optimization:* with OpenCode or any `small_model`-capable harness,
      `bf init --agents opencode` wires extraction, alias resolution, summaries, and continuity
      scanning to a cheap model while prose tasks route to a stronger model.
- [ ] Persistent memory tier exists: `bf memory search` returns semantic hits across canon +
      drafts + history; `bf memory serve --mcp` exposes it as MCP tools (opt-in)
- [ ] Headroom is the reference memory backend but swappable via `bf config` with zero
      engine-code changes
- [ ] `bf memory learn` produces proposals only; only `bf memory apply-learning` (after
      validation) mutates `AGENTS.md` — `learn` never writes the contract directly
- [ ] Canon is event-sourced: snapshot = fold of validated events; delete + rebuild losslessly
- [ ] `bf apply` is the only canon mutation path; `bf validate` is the non-negotiable gate
- [ ] `bf checkpoint save/load/diff` give writer-native verbs over the same engine
- [ ] `bf memory resolve "Tex"` returns canonical entity + aliases in <500 tokens
- [ ] No Codex/Antigravity/Gemini/OpenCode names hardcoded in engine or canonical docs
- [ ] `bf` works on Windows out of the box (no-arg = status, no termios crash)
- [ ] No bare `except Exception` in `bookforge/core/` outside adapter subprocess code
- [ ] Old workflow works during migration with deprecation warnings
- [ ] Tests + golden files tracked in git; `tests/` and `docs/` version-controlled

---

## 12. Migration Strategy (Non-Breaking)

1. New `canon/` structure **coexists** with old `rulebook.md` / `world-state.json` /
   `relationships.json` during migration.
2. `bf migrate <book>` reads old files and emits `canon/*.yml` + `events/*.event.yml`
   (lossless, idempotent).
3. Old files remain as fallback until a `bf config set canon.v2 native` flag flip.
4. Context packet renderer learns to read from `canon/` first, falls back to old `rulebook.md`.
5. Each milestone ships working; no big-bang rewrite.

---

## 13. Open Questions (resolve before the relevant milestone)

**Load-bearing — blocks architecture freeze:**

- **Fold-engine feasibility for narrative state.** The fold model assumes events compose
  cleanly. Fiction state is fuzzier: "Mara is injured" — how injured, when does it heal, does
  it still hold in chapter 9? Software events are discrete; story state is graded and decays.
  Before freezing, prototype the fold on a real book's `continuity-out.md` chain and confirm
  narrative mutations compose without contradiction. If they don't, the fold model needs an
  explicit reconciliation/conflict-resolution step, not just append+reduce. This is the one
  question the command-surface fixes do NOT answer.

**Other — resolvable per-milestone:**

1. **Sample book name:** keep `book-example`, or restore `tex-cade` as the real sample?
2. **Event granularity:** one event per chapter (coarse, matches `continuity-out.md`), or
   one event per scene/beat (fine-grained, more rollback fidelity but more overhead)?
3. **Memory backend default:** Headroom (if installed) or LocalEmbedding? *Recommendation:
   LocalEmbedding default, Headroom when `bf config set memory.backend headroom`.*
4. **MCP exposure default-off?** *Recommendation: yes — `bf memory serve --mcp` is opt-in.*
5. **Routing enforcement:** advisory (`AGENTS.md` tells the harness) or hard (`bf` refuses to
   run writer tasks unless invoked by a strong-model persona)? *Recommendation: advisory first,
   hard enforcement as an M5 option.*

---

## 14. What Was Wrong With Earlier Drafts (for the record)

- **Draft 1 (OpenSpec transposition):** One metaphor. Too rigid for creative discovery; specs
  are stable but canon churns every chapter.
- **Draft 2 (merged four metaphors):** Better — recognized git-flow/event-sourcing/save-state/
  OpenSpec are one machine with different vocabularies. But **dropped Headroom as a first-class
  tier** (reduced it to "one compression adapter") and **had no persistent-memory subsystem**.
  Also dropped model routing.
- **This draft (final):** Adds Layer 3 (Persistent Memory Tier — Headroom as reference, MCP
  exposure opt-in) and Layer 5 (Harness / Model Routing — OpenCode as reference, small_model
  → extraction, strong model → prose). Both were in your original vision and got flattened in
  earlier drafts.

---

## Appendix A — Sources That Shaped This Plan

- **OpenSpec** (Fission-AI/OpenSpec) — files-as-contract + deterministic CLI +
  validate-before-apply + `init` adapts per-agent
- **Headroom** (chopratejas/headroom) — library/proxy/MCP compression + `retrieve`/`stats`/
  `learn` + `SharedContext` cross-agent memory + `headroom wrap` for claude/codex/cursor/
  aider/copilot
- **NotebookLM MCP CLI** (jacob-bd/notebooklm-mcp-cli) — the "one MCP server, N thin agent
  skill folders" packaging pattern
- **AGENTS.md ecosystem** — the converging agent-instruction standard (Codex, Claude Code,
  Gemini CLI all read it)

---

## Appendix B — Relationship to `REPO_FIX_PLAN.md`

`REPO_FIX_PLAN.md` (the earlier hygiene/correctness plan) is **not deleted** — it remains the
detailed reference for M0 and parts of M3:

- `REPO_FIX_PLAN.md` Phase 0 (hygiene) → BookForge v2 **M0**
- `REPO_FIX_PLAN.md` Phase 1 (stale defaults, Windows-safe `bf`) → BookForge v2 **M0**
- `REPO_FIX_PLAN.md` Phase 2 (exception swallowing, length-language false-positive) → **M3**
- `REPO_FIX_PLAN.md` Phase 3 (entry surface, `AGENTS.md` → `bf`) → **M1**
- `REPO_FIX_PLAN.md` Phase 4 (`ManuscriptIssue` migration) → **M3**
- `REPO_FIX_PLAN.md` Phase 5 (decompose `validator.py`) → **M3**
- `REPO_FIX_PLAN.md` Phase 6 (cross-platform install, NotebookLM isolation) → **M3 + M5**

Everything in `REPO_FIX_PLAN.md` is absorbed into this plan.
