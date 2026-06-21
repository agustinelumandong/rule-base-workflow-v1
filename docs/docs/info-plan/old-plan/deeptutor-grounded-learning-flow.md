# DeepTutor Grounded Learning Flow

This note explains what happens after a learner puts documents into DeepTutor, without route names or low-level API chatter. It is written to prevent hallucination: every major idea below is backed by the public DeepTutor docs and the local codebase shape.

## Short Map

User upload to Knowledge Base.

Background worker chew file.

LlamaIndex make chunks and embeddings.

Embeddings go into `version-N`.

KB become ready.

Later `rag` tool search it.

Model use found chunks to answer.

That is the small story. The bigger story is this:

Knowledge Base is not just file storage. It is the grounding layer. Agent pipelines, memory, Book Engine, and Co-Writer all use it so DeepTutor has source text to stand on instead of guessing.

## Knowledge Base And RAG

When user adds documents to a Knowledge Base, DeepTutor first treats the original files as source material. File stays raw. Then background work starts.

The worker does four main jobs:

1. Validate and stage the documents.
2. Route each file type to the right extractor.
3. Ask LlamaIndex to build the searchable index.
4. Mark the KB ready only after the index is usable.

LlamaIndex is the RAG backbone. It reads the source text, cuts it into useful chunks, embeds the chunks, and stores a vector index. New writes use flat index folders like `version-1`, `version-2`, and so on. Each version carries metadata about the embedding setup, so DeepTutor can notice when the embedder changed and warn about re-indexing.

When chat later needs the document, the model does not magically remember the file. It calls the `rag` tool. The tool searches the selected KB, retrieves relevant chunks, and gives those chunks back to the model. Then the model writes an answer from retrieved evidence.

This matters because hallucination gets blocked at the source:

- If KB is not selected, RAG should not invent from it.
- If KB index is stale or embedding mismatch is detected, system can flag re-index.
- If retrieval finds weak context, answer should be cautious.
- If user asks beyond the documents, model should say what is known and what is not grounded.

## Agent Pipelines

DeepTutor has simple tools and bigger capabilities.

Tools are one-shot actions. Example: `rag`, `web_search`, `code_execution`, `read_source`, `read_memory`, `write_note`.

Capabilities are turn-owning pipelines. They run multiple stages and decide how tools fit into the answer.

Main pipeline pattern:

1. User sends goal.
2. `UnifiedContext` carries message, session, KBs, attachments, memory, skills, and config.
3. `ChatOrchestrator` picks a capability.
4. Capability runs stages.
5. `StreamBus` emits progress, tool calls, content, and final result.
6. Session runtime stores the turn so UI can resume, regenerate, or replay.

Important capabilities:

- `chat`: agentic loop. It can think, call tools, observe results, and finish.
- `deep_solve`: plan, reason, write. Good for hard problems.
- `deep_question`: generate quiz questions or follow up on one quiz item.
- `deep_research`: rephrase, decompose, research subtopics, then report with citations.
- `visualize`: analyze request, generate visual code, review output.
- `math_animator`: analyze concept, design scene, generate Manim code, retry render, summarize.
- `auto`: router. It chooses another capability when user intent is unclear.

RAG plugs into these pipelines as a grounding tool. Research can use RAG plus web and paper search. Solve can use RAG for source context. Chat can call RAG only when the selected KB is useful. Book Engine uses KB retrieval to compile pages.

Good mental model:

Pipeline is the worker brain.

Tools are worker hands.

RAG is worker memory of documents.

StreamBus is worker mouth telling UI what is happening.

## Memory Pipeline

DeepTutor memory is separate from Knowledge Base.

Knowledge Base stores external documents.

Memory stores what happened with the learner.

Memory has three layers:

| Layer | Caveman meaning | Real job |
| --- | --- | --- |
| L1 | Raw footprints | Append-only trace of interactions by surface and day |
| L2 | Clean notes per place | Per-surface summaries with citations back to L1 |
| L3 | Big learner picture | Cross-surface synthesis: recent, profile, scope, preferences |

Surfaces feeding memory include chat, notebook, quiz, KB, book, tutorbot, and cowriter.

Flow:

1. User chats, studies, writes, quizzes, indexes KB, or reads book.
2. L1 records what happened.
3. Consolidator reads L1 and writes cleaner L2 facts.
4. L3 synthesizes across L2 into learner profile, recent timeline, knowledge scope, and preferences.
5. At chat start, L3 can be injected into the system prompt.
6. During a turn, model can use `read_memory`.
7. If user explicitly states a preference, model can use `write_memory`.

Memory Workbench exists so user can inspect this. User can see L1, L2, L3, memory graph, and resolve citations. This is anti-hallucination because memory claims are not just vibes. They should trace backward: L3 claim -> L2 evidence -> L1 event.

Important boundary:

Memory is about the learner and their activity.

Knowledge Base is about uploaded source documents.

RAG answers from KB.

Memory personalizes and remembers learning context.

## Book Engine

Book Engine turns a KB-backed topic into an interactive living book.

Flow:

1. User gives topic and points at KB.
2. Book pipeline proposes outline.
3. It retrieves source passages from KB.
4. It builds chapter tree.
5. It plans pages.
6. It compiles blocks.
7. User reads, quizzes, edits outline, and chats beside pages.

Book is not just static text. It can contain prose, callouts, quizzes, flash cards, code, figures, deep dives, animations, interactive demos, timelines, concept graphs, sections, and user notes.

Book pages are fingerprinted against the KB. If source documents change, health checks can report stale pages. This protects against silent drift: old page may no longer match new KB.

Anti-hallucination rule for Book:

Book should be only as strong as the KB behind it. If KB lacks source coverage, Book should not pretend full coverage.

## Co-Writer

Co-Writer is Markdown workspace with AI help.

It has two main agents:

- Edit Agent: user selects text, agent rewrites, expands, condenses, changes tone, fixes grammar, or translates.
- Narrator Agent: user puts cursor somewhere, agent continues writing, fills outline, explains concept, or cites from KB.

Co-Writer can attach context:

- Knowledge Base for grounded citations.
- History session for previous chat or research turn.
- Notebook records for saved snippets.

So Co-Writer is not only "make text pretty." It can ground writing in KB and previous work. This helps avoid hallucination because generated claims can be pulled from attached KB or known session material instead of free invention.

Good boundary:

If user asks Co-Writer to cite from KB, it should retrieve from KB.

If user asks style-only edit, it should preserve meaning.

If source is missing, it should not fake citation.

## Settings

Settings controls the engines behind all of this.

Most important settings for grounded behavior:

- LLM profile: what model writes and reasons.
- Embedding profile: what model turns KB chunks into vectors.
- Search profile: what provider powers web search.
- Capability settings: budgets, chunking, max iterations, citation/reference policy.
- Memory settings: whether consolidator runs, cadence, and token budget.
- Tools settings: which optional tools user allows.

Settings uses draft/apply style. This matters because changing embeddings or models is not small. If embedder changes, old KB vector index may no longer match. Then DeepTutor should ask for re-index rather than silently mixing wrong vectors.

## How These Parts Stop Hallucination

DeepTutor reduces hallucination by separating jobs:

- KB stores source truth.
- RAG retrieves source chunks.
- Agent pipeline decides when source is needed.
- Memory stores learner context with traceable layers.
- Book fingerprints pages against KB.
- Co-Writer can pull from KB/history/notebooks.
- Settings controls which models, embedders, tools, and budgets are active.

No single part is magic. The safety comes from chain of evidence.

Best grounded answer path:

User question -> selected KB -> RAG retrieves chunks -> model sees chunks -> model answers with limits.

Best memory path:

User activity -> L1 trace -> L2 cited summary -> L3 synthesis -> chat personalization.

Best Book path:

Topic -> KB retrieval -> outline -> page blocks -> fingerprint -> drift check.

Best Co-Writer path:

Selection or cursor -> attached context -> edit/generate -> keep source meaning and cite if grounded.

## Cheat Sheet

| User action | What DeepTutor does | Why it matters |
| --- | --- | --- |
| Upload to KB | Save raw file, chunk, embed, version index | Makes document searchable |
| Ask with KB attached | RAG retrieves chunks, model answers from chunks | Grounds answer |
| Study/chat/write | L1 traces event | Keeps real history |
| Run memory consolidator | L1 becomes L2, L2 becomes L3 | Builds inspectable learner memory |
| Build book from KB | Multi-agent pipeline retrieves, outlines, compiles pages | Turns documents into learning object |
| Use Co-Writer | Edit or narrator agent works in Markdown with optional KB context | Writes with source support |
| Change embeddings | KB may need re-index | Prevents bad retrieval |

## Source Notes

Public docs checked:

- https://deeptutor.info/docs/explore/memory/
- https://deeptutor.info/docs/explore/knowledge/
- https://deeptutor.info/docs/explore/book/
- https://deeptutor.info/docs/explore/co-writer/
- https://deeptutor.info/docs/explore/settings/

Local code areas checked:

- Knowledge upload and background tasks: `deeptutor/api/routers/knowledge.py`
- KB initialization: `deeptutor/knowledge/initializer.py`
- RAG service and tool: `deeptutor/services/rag/service.py`, `deeptutor/tools/rag_tool.py`
- Index versions: `deeptutor/services/rag/index_versioning.py`
- Capability/runtime architecture: `deeptutor/runtime`, `deeptutor/capabilities`, `deeptutor/agents`
- Memory router and services: `deeptutor/api/routers/memory.py`, `deeptutor/services/memory`
