# Manuscript Agent Instructions

Use these rules when helping with manuscript planning, drafting, editing, validation, or workspace management in this project. These guidelines apply to all developers, AI assistants, and autonomous agents (e.g. Gemini, Claude, Cursor, OpenCode).

---

## 1. The BookForge Contract: MCP-Driven Workflow

As an AI agent, you do not need to read the entire repository, full outlines, or comprehensive rulebooks. Instead, you operate via a lightweight, token-budgeted contract using bookforge-mcp tools.

Your core workflow is strictly procedural:

0. **LOCK CHECK (mandatory)**: Before ANY write operation on a book, run:
   ```
   ./scripts/check-book-lock.sh books/<series>/<book>
   ```
   If exit code is 1 → **STOP**. Book is locked. Report "Book is locked. No modifications permitted." Do not proceed.
1. **Check Status**: Use `bookforge-mcp_get_queue_status` to see scene statuses and the active scene.
2. **Identify Task & Chapter**: Locate the chapter (e.g. `chapter-03` or `epilogue`) and the current active task (e.g. `draft-prose`, `revise-style`, `continuity-check`).
3. **Render Task Packet**: Use `bookforge-mcp_build_generation_packet` with chapter and task parameters to generate a token-budgeted context packet.
4. **Execute Narrowly**: Read ONLY `context-packet.md` for this task. It contains the specific subset of style guides, pacing, research facts, active character profiles, and continuity needed for the task.
5. **Chapter Review**: After compiling a chapter draft, create or refresh `chapter-review.md`. It must include read-through notes, slow spots, rushed spots, break opportunities, and a final decision of `ready`, `needs-rhythm-fix`, or `needs-beat-expansion`.
6. **Validate**: Before submitting or moving to the next phase, run validation:
   ```
   bookforge-mcp_validate_scene (chapter: <chapter-slug>)
   ```
7. **Apply Change**: Promote validated prose via `bookforge-mcp_apply_patch` or `bookforge-mcp_save_draft`.

---

## 2. Chapter-Level Fix Agents

For style fixes on compiled chapter files, use the dedicated fix agents. These agents should stay narrow, inspect prose directly, and avoid oversized shell or regex scans.

### Available Fix Agents

| Agent | Use for | Tools |
|-------|---------|-------|
| bf-staccato-fixer | 3+ consecutive short fragments | read, bash or edit, grep, glob |
| bf-style-fixer | personification, internal thought, -ing openers, pronoun loops | read, bash or edit, grep, glob |
| bf-phase-auditor | missing beats, weak coverage (read-only) | read, grep, glob |
| bf-rhythm-adjuster | expand/trim to hit word target | read, bash or edit, grep, glob |

### Dispatching Fix Agents

Use the runtime's available orchestration path only. If no `task` tool exists, do the chapter-level pass directly in the current run instead of attempting subagent dispatch.

Example:
```
Read the target chapter, inspect the prose directly, apply the narrow fix, and verify it. Do not assume subagent support exists in the runtime.
```

### Runtime Guardrails

- Never assume a `task` tool exists.
- Reserve `bash` for short edit scripts or tiny verification commands.
- Do not send giant `rg`/`grep` alternation patterns through `bash`.
- Detect personification by reading and judgment, not by noun/verb mega-regex lists.

---

## 3. Book Lock (Immutable Finished Books)

When a book is complete, it is **locked**. A locked book must never be modified.

### How to Check
Before any write operation on a book, check for `STATUS.md` in the book's root directory:
```
books/<series>/<book>/STATUS.md
```
If this file exists and contains `Status: LOCKED`, the book is immutable.

### Locked Means
- No edits to `compiled-manuscript.md`
- No edits to `world-state.json`
- No edits to `canon/events/*` or `canon/state/snapshot.yml`
- No edits to `phase-0.md` or `rulebook.md`
- No scene generation, patching, or validation
- Queue can be archived but not reactivated

### Enforcement
- All agents, AI assistants, and autonomous tools must check `STATUS.md` before any write.
- If locked, refuse the operation and report: "Book is locked. No modifications permitted."
- This is irreversible. A locked book should never be unlocked.

### Creating a Lock
When a book is finished, create `STATUS.md` with:
```markdown
# Book Status: LOCKED
## State
- **Status:** LOCKED (immutable)
- **Book:** <book title>
- **Locked At:** <date>
- **Reason:** <why the book is complete>
```

---

## 4. Constraints & Guardrails
- **No Direct Canon Mutations**: Never manually edit files in `canon/state/snapshot.yml`. All canon updates must be applied via bookforge-mcp tools.
- **Zero-Trust Input**: Never guess details or invent story facts. If facts are unknown, query them via `bookforge-mcp_query_research_cache`.
- **Validation is the Gate**: Any validation failures (`bookforge-mcp_validate_scene`) must be resolved before applying changes.
- **Pacing Guidance is Elastic**: Beat weights and chapter ranges are planning tripwires, not padding quotas. Use them to notice rushed or bloated treatment, never to force exact length.
- **Locked Books Are Sacred**: Never modify a book with `STATUS.md` set to `LOCKED`. See Section 3.
