# StoryOps Engine ↔ BookForge: Concept Mapping & Gap Analysis

> **One line:** The "StoryOps Engine" you brainstormed is **mostly the system you already
> have.** BookForge already is a canon compiler with a validate-gate, token-budgeted
> generation packets, NotebookLM-backed reality research, and model routing. What it does
> **not** have yet is (1) a generator-lane guard keeping the IDE/Codex out of long-form prose,
> (2) addressable scene/beat units, (3) patch-instead-of-regenerate, (4) a structured research
> cache, (5) a generation/throughput queue, (6) a provider-web Project Kit, and (7) a unified
> provider-neutral MCP.

This doc maps each idea from the StoryOps Engine brainstorm onto what exists in the repo,
marks what is **already built** vs **genuinely missing**, and proposes how to build the gaps
on top of the existing architecture — not as a greenfield rewrite.

> **Correction log (review pass):** the first draft overclaimed that "the generator never
> sees unvalidated context." Softened to provenance-aware packet assembly. The Project Kit is
> renamed from "generator" to "context bundle" and treated manual-first. MCP is split into
> local/operator vs remote/provider-web surfaces. Scene/beat addressing is promoted ahead of
> patching. The guardrail is promoted to P0. A 7th gap (generation queue) was added. "Five
> books/day" is clarified to mean **raw draft throughput**, not publish-ready manuscripts.

---

## 1. The Punchline: BookForge Already *Is* the StoryOps Engine

The brainstorm reached this architecture:

```
Markdown canon  →  Story Engine (compile/retrieve/validate)  →  compact Packet  →  Generator  →  Validator  →  Patch
 (source code)         (compiler)                              (binary)           (runtime)       (test suite)
```

That is a near-exact description of what BookForge v2 already ships:

| StoryOps idea            | BookForge reality                                                        | Status |
| ------------------------ | ------------------------------------------------------------------------ | :----: |
| Markdown story bible     | `books/<slug>/` + `canon/` (entities+events+fold) + `spec/`              | ✅ built |
| Compiler metaphor        | Event-sourced canon: `bf canon build` folds events → `snapshot.yml`      | ✅ built |
| Compiled "binary" packet | `bf packet --chapter <slug> --task <task>` → token-budgeted `context-packet.md` | ✅ built |
| Hard validators (code)   | `bf validate` + `bookforge/core/validators/` (format/style/continuity)   | ✅ built |
| Validator = test suite   | The `bf validate` → `bf apply` gate (Layer 2, non-negotiable)            | ✅ built |
| NotebookLM = reality     | `bf nlm *` + `adapters/research.py` (`NotebookLMBackend`/`ManualBackend`) | ✅ built |
| Retrieval/memory tier    | `bf memory *` (Headroom + local embedding) + `bf memory serve --mcp`     | ✅ built |
| Model routing            | `spec/model-routing.yml` (extractor/reviewer/writer) + `bf check-persona` | ✅ built |
| Three-tier severity      | `Severity.HARD / SOFT / INFO` (blocks / warns / signals)                 | ✅ built |

So you are **not** designing a new system. You are extending a working one with the pieces
the brainstorm correctly identified as load-bearing for your real goal: **generating ~5
complete raw book drafts per day without draining Codex/Antigravity quota on long-form
prose.**

> **Honest scope on the goal.** "Five books/day" means five **complete raw first drafts**
> with automated validation and patch passes — **not** five final, fully edited,
> canon-perfect, publish-ready manuscripts. The throughput target is for raw draft
> generation; finishing remains a separate, slower stage.

---

## 2. The Real Bottleneck (from your clarification)

> "My problem is generating the whole thing, the whole book… five times a day… even RAG /
> Headroom doesn't solve it. The generator quota drains."

Correct. Retrieval is **already solved** (`bf memory`, `bf packet` budgets to ≤8k tokens).
The unsolved problem is **long-form generation throughput**. Two things drain quota:

1. **Regenerating whole chapters when a patch would do** — the rework *multiplier* (a 2×–4×
   regeneration tax on every failed draft).
2. **Spending expensive generator tokens on facts a cheaper layer could have checked.**

The fix is **not** "RAG harder." It is:

> *Never spend a long-form generation call unless the packet is already correct, and never
> regenerate full chapters when a patch will do.*

BookForge already addresses #2 — validate-before-generate is the gate. But "packet built
after `bf validate`" is **not** the same as "the generator sees only fully-validated
context." A packet can still carry:

- stale drift in `chapter-summaries.md`,
- soft (`Severity.SOFT`) warnings that passed the gate,
- flat `research-pack.md` facts that were never canon-approved,
- NotebookLM answers that are source-grounded but not canon-accepted.

So the next maturity step is **provenance-aware packet assembly**: each packet section should
declare its trust level (canon / derived summary / research cache / pending proposal /
soft-warning). The missing piece for #1 is **patch packets** and **scene/beat-level
addressing** — the real new work below.

---

## 3. Concept-by-Concept Mapping (what already exists)

### 3.1 "Generation Packet" → `bf packet` ✅ EXISTS

The brainstorm's "compiled binary" packet is **literally `bf packet`**. It already:

- Reads outline, rulebook, character profiles, mood-lock, pacing, prior continuity,
  research facts, and scene breakdown.
- Compresses each section with `compress_text()`.
- Enforces a **token budget** per task (`TASK_BUDGETS`: draft-prose=2500, all=8000, …).
- Trims non-critical sections to fit, then critical-only as a last resort.
- Has **task-typed packets**: `draft-prose`, `continuity-check`, `extract-memory`,
  `revise-style`, `validate-change`.

The packet even already includes "Review Focus" hard rules and a "Scene Breakdown" section.
**Caveat:** it does not yet tag each section with provenance/trust level (see §4 Gap 2).

**File:** `bookforge/core/packet/builder.py`

### 3.2 "Hard validators by code" → `bf validate` + `validators/` ✅ EXISTS

The brainstorm lists: forbidden words, POV violation, timeline contradiction, character
location contradiction, knowledge-state contradiction, output length, required beats
missing. All of these map to existing checks:

- Forbidden/style → `validators/style.py` (`BANNED_AI_ECHO_WORDS`, `MODERN_OR_CLINICAL_WORDS`, …)
- Continuity/location/teleportation → `validators/continuity.py` + `chain.py` + `repair.py`
- Length → `core/length.py` + `loop/state.py`
- Canon contradiction (dead character acting, alias misuse) → `canon/validate.py`
- Graded severity (hard block vs soft warn vs info signal) → `issue.py` Severity enum

### 3.3 "NotebookLM = reality validator" → `bf nlm` ✅ EXISTS

The brainstorm wants NotebookLM to answer "could this gun exist in this year?" / "is this
mountain pass traversable by horse?" That already works:

- `bf nlm link <notebook_id>` — attach a research notebook to a book.
- `bf nlm query "<question>"` — source-grounded answer.
- `bf nlm sync-research` — pull NotebookLM facts into `research-pack.md`.
- `bf nlm sync-sources` — upload local canon/drafts as notebook sources.
- `bf nlm generate-outline` — end-to-end research-grounded outline generation.

**File:** `adapters/research.py` (`NotebookLMBackend.query/ingest`).

### 3.4 "Retrieval/memory tier" → `bf memory` ✅ EXISTS

- `bf memory build/search/resolve` — semantic retrieval over canon + drafts + history.
- `bf memory learn` → produces **proposals only**; `bf memory apply-learning` mutates
  `AGENTS.md`/`spec/` after validation (never writes the contract directly).
- `bf memory serve --mcp` — exposes the backend as MCP tools (currently
  `headroom_retrieve` / `headroom_stats`).

### 3.5 "Model routing: strong models only for prose" → `model-routing.yml` ✅ EXISTS

- `spec/model-routing.yml` declares extractor (cheap) / reviewer (mid) / writer (strong).
- `bf check-persona --persona writer --model <m> --action draft` enforces the registry,
  including a **global budget cap** (`global_budget_cap_usd`) and per-persona token limits.

### 3.6 "Compiler pipeline, not chatbot pipeline" → the gate ✅ EXISTS (structure; provenance pending)

> "pre-resolve as much uncertainty as possible before the generator ever sees the prompt."

That is the intent of the `bf validate` → `bf apply` gate. But "built after validate" ≠
"contains only validated material" — see the caveat in §2 and Gap 2 below.

---

## 4. What Is Genuinely Missing (the real new work)

Seven gaps, ordered foundational-first (addressing before patching; cheap guards before
expensive integrations).

### Gap 1 — Generator-Lane Guard ❌ ADVISORY ONLY (promote to P0)

**The idea:** Codex/Antigravity are **operators** (files, packets, validators, patch
instructions, continuity checks) and must **never** write 3,500-word chapters. Provider web
UIs are the generator. Directly enforces your business rule: "Codex/Antigravity are
operators, not novelists."

**BookForge today:** `model-routing.yml` + `bf check-persona` enforce model→task mapping,
but enforcement is **advisory**. Nothing refuses a long-form prose call from the IDE layer.

**Proposed:** extend `persona.py` `check_persona_capabilities` with an
**operator-prose cap** — refuse when `persona ∈ {operator}` and `action = draft_prose` and
`projected_output_tokens` exceeds a threshold. Start **advisory + logged** (default), with a
config flag to flip to **hard-refuse** once stable. Threshold must be configurable, not a
flat number — the operator path legitimately needs short prose fragments (splice glue,
scene beats), so ~500 is a sane default but must be overridable.

**Build anchors:** `persona.py` already computes projected cost and enforces budgets; this is
a small additional rule. Cheap and protective → build first.

### Gap 2 — Provenance-Aware Packet Sections ⚠️ PARTIAL

**The idea:** each packet section declares whether it comes from canon, derived summary,
research cache, pending proposal, or soft-warning context, so the generator (and the
archiver) knows what is trustworthy.

**BookForge today:** `packet/builder.py` assembles sections from many sources but tags none
with trust level. A packet can carry stale summaries or soft-warning material with no signal
to the consumer.

**Proposed:** add a provenance tag to each packet part (`{"source": "canon|summary|research|
proposal|soft_warning", "trust": "high|medium|low"}`) and render it inline. The packet
trimmer should prefer high-trust sections when budget is tight. This also lets the
Project-Kit archiver (Gap 6) know what is safe to keep as a stable source vs what must roll.

**Build anchors:** extend the `parts` dicts in `packet/builder.py` and the renderer.

### Gap 3 — Scene/Beat/Paragraph Address System ❌ NOT BUILT (foundational)

**The idea:** the generation and patching unit should be **scene or beat**, not full chapter.
A 3,500-word scene should internally decompose into a beat map. Most importantly, **stable
addresses are the foundation patches need** — you cannot patch what you cannot address.

**BookForge today:** packets are **chapter-level** (`--chapter chapter-NN`). Partial
foundation exists: `beats.md` + `action.py` track beats, and `repair.py` already localizes
failures to scenes (`[Scene 1: The Stables]`). But there is **no stable paragraph-level ID
system** and no scene-level packet scope. The loop is **sequential per chapter**.

**Proposed:**
- A scene manifest format (declarative `scene_id`, `target_words`, `inputs`,
  `required_beats`, `forbidden`, `research_questions`, `validation`) that drives the whole
  pipeline and is the **stable address** everything else keys off.
- `bf packet --scene ch08_sc02 --task draft-prose` (scene-level scope).
- Paragraph/beat IDs embedded in drafts so patches can target exact spans.

**Build anchors:** `action.py` already initializes beat-level action plans; the scene manifest
is a small new schema alongside `proposal.md`/`beats.md`. **Build before or alongside Gap 4.**

### Gap 4 — Patch Packet (regenerate only what's broken) ❌ NOT BUILT

**The idea:**
```
generate full draft → validate → patch 3 paragraphs → validate patch only
```
instead of:
```
generate → validate → regenerate full → validate → regenerate full
```
This is the **single biggest lever for reducing rework tokens** — it kills the regeneration
*multiplier*. (Base output tokens remain unavoidable: 5 × ~70k-word drafts ≈ 350k words of
output before any repair. Patching prevents the 2×–4× tax on top of that, not the base cost.)

**BookForge today:** the loop controller routes to repair, and `bf repair` is an interactive
wizard for *logistics* failures (teleportation/inventory). There is **no** "build a minimal
revision packet for the broken beat/scene only" capability; `revise-style` regenerates the
whole chapter draft.

**Proposed:** `bf patch --chapter <slug> --failures <json>` with a strict output contract:

```
Patch packet must include:
- failing issue IDs
- affected scene/beat/paragraph range (from Gap 3 addresses)
- immutable surrounding context
- exact replacement boundary markers
- instructions: return replacement text only
- validator checklist for the patch
```

The returned patch uses a **splice-safe** format so BookForge can apply it deterministically:

```
<<<<<<< PATCH_TARGET ch08_sc02_p014_p017
replacement prose here
>>>>>>> PATCH_TARGET
```

**Build anchors:** extend `packet/builder.py` with a `patch` task; reuse `validators/` to
localize failures (already emits scene tags); reuse `canon/fold.py` + `apply.py` to splice.
**Depends on Gap 3** for stable addresses — fragile without it.

### Gap 5 — Structured Research Cache ❌ PARTIAL

**The idea:** every NotebookLM fact check becomes reusable, provenance-tagged canon-eligible
evidence under `research_cache/{weapons,locations,social_customs}/...`, so NotebookLM is a
**miss-only** path. Critical distinction: `research_cache` = **evidence**; `canon` =
**accepted story truth**. NotebookLM answers must **not** auto-become canon — only become
packet-eligible after BookForge marks them accepted.

**BookForge today:** `research-pack.md` is **one flat file**. `ManualBackend.query()` does
keyword section matching, but there's no dedup, no structured taxonomy, no "was this exact
question already answered?" lookup, and no provenance/expiry.

**Proposed:** a structured cache with deterministic keys and full provenance:

```yaml
question: "Could a horse safely traverse this mountain route?"
normalized_key: "locations/mountain_pass/horse_travel/1890s"
answer: "..."
source_notebook_id: "..."
source_titles: ["..."]
confidence: high
canon_status: accepted | pending | rejected   # pending by default; never auto-canon
created_at: "..."
last_verified_at: "..."
expires: never | date | on_canon_change
used_by: [ch08_sc02]
```

**Build anchors:** `adapters/research.py` already has the `ResearchBackend` Protocol; add a
caching front-end that writes structured files, short-circuits on hit, and exposes
`canon_status` so the packet builder (Gap 2 provenance) can label research sections correctly.

### Gap 6 — Generation Queue / Throughput Scheduler ❌ NOT BUILT

**The idea:** for 5 drafts/day with parallelization, BookForge must **track the production
state of every scene** — not just run a sequential chapter loop.

**BookForge today:** `run_loop_check` + `state/loop.json` track **chapter** `repair_attempts`
and loop status. That is a *sequential chapter controller*, not a *parallel scene scheduler*.
Once you run many books/scenes concurrently it becomes manual chaos.

**Proposed:** a per-scene production record:

```yaml
scene_id: ch08_sc02
status: ready_for_generation | generating | needs_patch | validated | committed
provider: chatgpt | claude | gemini | manual
packet_path: packets/ch08_sc02.md
draft_path:   drafts/ch08_sc02.md
validation_path: validation/ch08_sc02.json
dependencies: [ch08_sc01]
parallelizable: true
```

This is **separate from MCP** (MCP exposes tools; the queue coordinates production). The
queue is what turns BookForge from "compiles packets" into "tracks the production state of
every scene."

**Build anchors:** extend `loop/state.py` from chapter-scoped to scene-scoped; reuse the
scene manifests (Gap 3) as queue units.

### Gap 7 — Provider-Web Project Kit / Context Bundle ❌ NOT BUILT

**The idea:** ChatGPT/Claude/Gemini *web* should be the generator. Per-book/volume, a
**provider Project** holds stable context as Project sources; each scene packet is temporary
and archived after the scene completes. This is a **context bundle renderer**, not a prose
generator.

**BookForge today:** `bf packet` writes a `context-packet.md` you **paste manually** into
whatever UI. There is no stable-vs-rolling-source split, no provider bundle, no archive step.

**Proposed:** a new `bf project-kit build --provider <chatgpt|claude|gemini> --book <slug>`
that compiles a provider-ready bundle:

```
packets/<book>/<provider>-project/
  00_project_instructions.md          # stable
  01_story_bible_compiled.md          # stable  ← from canon/state/snapshot.yml
  02_character_states.md              # stable
  03_timeline_compiled.md             # stable
  04_style_rules.md                   # stable  ← from western-manuscript-style
  05_hard_guardrails.md               # stable
  06_world_reality_rules.md           # stable  ← from research-pack.md (accepted only)
  07_current_outline.md               # rolling
  08_previous_chapter_summaries.md    # rolling ← from chapter-summaries.md
  09_unresolved_hooks.md              # rolling ← from continuity-out chain
  10_generation_queue.md              # rolling ← from the queue (Gap 6)
  scenes/
    ch08_sc02_generation_packet.md    # temporary (the compiled "binary")
    ch08_sc02_research_packet.md      # temporary
    ch08_sc02_validation_checklist.json
```

**Rule:** stable sources maintain continuity across the book; the active scene packet holds
temporary task context. After a scene completes, its packet is **archived** out of the active
set or the Project accumulates stale context and retrieves outdated canon. Provenance (Gap 2)
decides what is safe to keep as stable vs what must roll.

> **Manual-first caution.** Do **not** assume BookForge can programmatically create provider
> Projects, upload/remove Project files, or archive them unless an official supported API for
> that specific action is confirmed. Provider Projects (e.g. ChatGPT Projects) are operated
> through their web UI; there is no guaranteed stable public automation API for Project
> source management. **MVP = generate a provider-ready folder for manual upload/use.**
> Automate file/project sync later, only through official supported APIs/connectors if and
> when they exist.

**Build anchors:** reuse `packet/builder.py` compression, `canon/io.py` snapshot read,
`scanner/` for outline/summaries, `notebooklm/` for research facts. Mostly a *new renderer*
over existing data, gated by provenance tags from Gap 2.

---

## 5. Provider-Neutral Story MCP — Two Surfaces, Not One ❌ NOT BUILT

The brainstorm wants one MCP server exposing ~8 high-level tools over a **shared core** with
thin provider adapters. Correct — but the security posture differs by transport, so split it
into two surfaces over the same `bf` core:

**Why "thin adapters, shared core" matters:** if you build separate logic per provider you
maintain N story systems. MCP avoids that fragmentation. BookForge's agent-agnostic `bf`
contract already *is* the shared core — the MCP is a thin JSON-RPC surface over the same
functions the CLI calls.

**BookForge today:** `bf memory serve --mcp` exists but exposes **only memory tools**
(`headroom_retrieve` / `headroom_stats`). Packet/validate/research/canon capabilities exist
only as **CLI commands**, not MCP tools.

### Surface A — Local / Operator MCP (Codex, Antigravity, Gemini CLI, local agents)

Can expose **stronger write tools** because it runs in a trusted local context:

```
create_generation_packet   validate_scene_plan     validate_draft
query_reality_research     get_relevant_canon      get_character_state
create_patch_packet        commit_generation_result
```

### Surface B — Remote / Provider-Web MCP (ChatGPT/Claude/Gemini web where supported)

Must expose **narrower, safer** tools. Provider developer modes (e.g. ChatGPT developer mode
over SSE/streaming HTTP) are powerful but risky for write actions and prompt injection, and
full write-MCP support is plan/rollout-dependent. **Start read/generate-only:**

```
create_generation_packet   query_reality_research   get_relevant_canon
get_character_state        create_patch_packet
```

Hold back from remote until later:

```
commit_generation_result   apply_canon_change   write_draft_file   delete/archive_project_context
```

**Build anchors:** mirror `memory/mcp_server.py`'s JSON-RPC stdio/HTTP pattern; each tool
delegates to the existing `packet/`, `validators/`, `adapters/research.py`, `canon/` code.
Do **not** expose the 30–50 raw NotebookLM tools — wrap them in `query_reality_research`.

---

## 6. The Generator Lane vs Operator Lane (role split)

The brainstorm's sharpest design decision, matched to BookForge roles:

| Role                          | StoryOps name | BookForge persona | Does                                       | Must NOT do                  |
| ----------------------------- | ------------- | ----------------- | ------------------------------------------ | ---------------------------- |
| **Generator** (web UIs)       | the runtime   | `writer`          | 3,500-word prose from a packet             | research, validate, decide canon |
| **Operator** (Codex/Antigravity) | the engineer  | `extractor`/`reviewer` | files, packets, validators, patches, continuity | long-form prose (quota drain) |
| **Reality** (NotebookLM)      | the fact-checker | (adapter)      | "does this gun/place/custom exist?"        | prose, canon mutation        |
| **Canon** (BookForge core)    | the source of truth | (gate)       | the only mutation path (`bf apply`)        | be bypassed                  |

The golden rule, already true in BookForge, made sharper:

> *A premium generator should never think about information a cheaper layer already knows.*
> Code checks structure. NotebookLM checks reality. Memory retrieves canon. The operator
> edits files. The **generator only writes prose**.

---

## 7. Recommended Build Order

Foundational-first (addressing before patching; cheap guards before expensive integrations).
This ordering better matches the real bottleneck than the first draft.

```
P0  Gap 1 — Generator-lane guard (advisory→hard)
        Prevent Codex/Antigravity from writing long-form prose. Cheap, protective.

P1  Gap 3 — Scene/beat/paragraph address system + manifests
        Stable addresses are the foundation patches and the queue key off.

P2  Gap 2 — Provenance-aware packet sections
        Each section tagged canon/summary/research/proposal/soft_warning.

P3  Gap 4 — Patch packet system + splice mechanism
        Minimal repair packets; splice replacements deterministically. Depends on P1.

P4  Gap 5 — Structured research cache
        NotebookLM as miss-only; provenance + canon_status; research ≠ canon.

P5  Gap 6 — Generation queue / throughput scheduler
        Track per-scene production state, provider, packet/draft/validation paths.

P6  Gap 7 — Provider-web Project Kit (context bundle)
        Render provider-ready stable/rolling/temporary bundles. Manual-first.

P7  §5   — Provider-neutral Story MCP (two surfaces)
        Local/operator (strong) + remote/provider-web (narrow) over the bf core.
```

P0–P4 are pure throughput wins on the **existing** CLI. P5–P7 are the integration layer.

**Non-goal (do not do):** do not rebuild retrieval/RAG, do not rebuild the compiler, do not
build a parallel "story-engine-core" alongside BookForge. BookForge is the core; the gaps are
*extensions* to it.

---

## 8. What Stays Authoritative

- **Canon is the only truth.** `canon/` (entities + events + fold) and `spec/` remain the
  source of truth. Everything above Layer 1 (memory, packets, provider Projects, MCP,
  research cache) is a **view onto canon** and may never mutate it directly. Only `bf apply`
  mutates canon. Research cache is **evidence**, never auto-canon.
- **A provider Project maintains continuity, but BookForge decides canon.** The Project holds
  stable + rolling context; BookForge decides what is canon, what is updated, and what is
  archived.
- **The packet is a compiled artifact, treated like a binary.** Old generation packets are
  archived out of the active source set after a scene completes — otherwise the Project
  accumulates stale context and retrieves outdated canon.

---

## Appendix A — Idea Concept → BookForge Command Cheatsheet

| StoryOps idea              | Existing `bf` command (if any)              | Gap? |
| -------------------------- | ------------------------------------------- | :--: |
| Compile context packet     | `bf packet --chapter N --task draft-prose`  | — |
| Hard-validate scene plan   | `bf validate --chapter N`                   | — |
| Validate a draft           | `bf validate --chapter N`                   | — |
| Query reality research     | `bf nlm query "<q>"`                        | partial (cache: Gap 5) |
| Get relevant canon         | `bf memory search "<q>"`                    | — |
| Get character state        | `bf canon build` → `snapshot.yml`           | — |
| Create **patch** packet    | —                                           | ❌ Gap 4 |
| Commit generation result   | `bf apply change <book> <chapter>`          | — |
| Compare draft to outline   | `bf validate --chapter N --review-prompt`   | — |
| Update chapter memory      | `bf memory learn` / `apply-learning`        | — |
| Summarize completed chapter| `bf packet --task extract-memory`           | — |
| Track scene production     | (loop tracks chapters only)                 | ❌ Gap 6 |

## Appendix B — Key Files for Each Gap

| Gap | Primary files to touch / add |
| --- | --------------------------- |
| 1 — Lane guard | extend `persona.py` `check_persona_capabilities` (operator-prose cap, configurable threshold) |
| 2 — Provenance tags | extend `parts` dicts + renderer in `packet/builder.py` |
| 3 — Address system | **add** scene manifest schema; extend `packet/` (`--scene`); reuse `action.py` beats |
| 4 — Patch packet | extend `packet/builder.py` (`patch` task); reuse `validators/`, `canon/apply.py`; splice-safe format |
| 5 — Research cache | extend `adapters/research.py` with caching front-end + provenance |
| 6 — Generation queue | extend `loop/state.py` chapter→scene scope; reuse scene manifests |
| 7 — Project Kit | **add** `bookforge/core/projectkit/`; reuse `packet/builder.py`, `canon/io.py`, `scanner/` (manual-first) |
| §5 — Story MCP | **add** `bookforge/core/mcp_server.py` (sibling to `memory/mcp_server.py`); two surfaces |
