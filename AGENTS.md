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

## 4. Spoon-Feeding Prevention (Narrator Explanation Cuts)

**Rule**: Cut any sentence that tells the reader what to think about action already shown through physical evidence.

### What "Spoon-Feeding" Means

After showing tracks, camp layout, supplies, and movement, the narrator explains the conclusion. This kills tension and insults the reader.

### Trigger Phrases to Scan

| Pattern | Example | Why It's Spoon-Feeding |
|---------|---------|----------------------|
| "They had…" | "They had been watching." | Explains what tracks already show |
| "He knew…" / "He saw…" | "Jake saw it as they had seen it." | Labels realization instead of showing |
| "That meant…" | "That meant he was with them." | Explains what evidence proves |
| "The kind…" | "The kind of place a man could hold." | Lectures after showing |
| "A man could…" | "A man could hold it against three." | Explains tactics after showing them |
| "Not enough…" | "Not enough food. Not enough powder." | Repeats what supply count already proves |
| "He was…" | "He was leading them." | Labels motive/status already shown |

### Example Fix

**Bad** (spoon-feeding):
```
McCrea slept between the warriors.
Not as a prisoner. Not as a guide who kept his distance. He had slept in the center of the camp, close to the fire, among them. His boot prints mingled with the moccasin tracks around the fire ring, stepping over the same stones, crossing the same ash. He was with them. He was leading them.
```

**Good** (trusts the reader):
```
McCrea slept between the warriors.

His boot prints crossed the ash near the fire ring and turned toward the river with theirs. No drag mark. No scuffle. No sign of a bound man. His heel had pressed deep beside the pemmican wrappers, close to the warmest stones.
```

### Enforcement

- All fix agents must scan for trigger phrases before making edits
- Cut sentences that restate what physical evidence already communicates
- Do NOT cut every plain sentence — only those that tell the reader what to think
- Preserve essential narrative transitions and pacing breaks

## 5. Constraints & Guardrails
- **No Direct Canon Mutations**: Never manually edit files in `canon/state/snapshot.yml`. All canon updates must be applied via bookforge-mcp tools.
- **Zero-Trust Input**: Never guess details or invent story facts. If facts are unknown, query them via `bookforge-mcp_query_research_cache`.
- **Validation is the Gate**: Any validation failures (`bookforge-mcp_validate_scene`) must be resolved before applying changes.
- **Pacing Guidance is Elastic**: Beat weights and chapter ranges are planning tripwires, not padding quotas. Use them to notice rushed or bloated treatment, never to force exact length.
- **Locked Books Are Sacred**: Never modify a book with `STATUS.md` set to `LOCKED`. See Section 3.
- **Spoon-Feeding Prevention**: Cut narrator explanations that restate what physical evidence already shows. See Section 4.

---

## 6. Web Driver Fallback (Manual Mode)

When browser-based automation is disabled (`use_web_driver: false`), the runner pipeline bypasses the provider web MCP browser calls and halts at a manual review state.

### How it Works
- **Generation Mode**:
  - The runner builds the generation packet and project kit locally.
  - It checks for the existence of `draft.md` in the scene changes directory.
  - If `draft.md` **does not exist**, the runner transitions to `needs_manual_review` (stopped reason `manual_drafting_pending`). You or the operator must manually write the initial draft in that location.
  - If `draft.md` **exists**, the runner automatically runs `validate_scene`. If validation passes, the scene is completed. If validation fails, the runner transitions to `needs_manual_review` (stopped reason `manual_review_pending`).
- **Repair Mode**:
  - The runner builds the patch packet and project kit locally.
  - It immediately transitions to `needs_manual_review` (stopped reason `manual_repair_pending`). You or the operator must manually edit `draft.md` to address the validation issues.

