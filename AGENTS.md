# Manuscript Agent Instructions

Use these rules when helping with manuscript planning, drafting, editing, validation, or workspace management in this project. These guidelines apply to all developers, AI assistants, and autonomous agents (e.g. Gemini, Claude, Cursor, OpenCode).

---

## 1. The BookForge Contract: CLI-Driven Workflow

As an AI agent, you do not need to read the entire repository, full outlines, or comprehensive rulebooks. Instead, you operate via a lightweight, token-budgeted contract.

Your core workflow is strictly procedural:

1. **Check Status**: Run `bf status` to see where the project currently stands and what task is next.
2. **Identify Task & Chapter**: Locate the chapter (e.g. `chapter-03` or `epilogue`) and the current active task (e.g. `draft-prose`, `revise-style`, `continuity-check`).
3. **Render Task Packet**: Run `bf packet --chapter <chapter-slug> --task <task>` to generate a token-budgeted context packet under the chapter folder (e.g. `changes/chapter-03/context-packet.md`).
4. **Execute Narrowly**: Read ONLY `context-packet.md` for this task. It contains the specific subset of style guides, pacing, research facts, active character profiles, and continuity needed for the task.
5. **Validate**: Before submitting or moving to the next phase, run validation:
   ```bash
   bf validate --chapter <chapter-slug>
   ```
6. **Apply Change**: Promote the validated changes to canon:
   ```bash
   bf apply change <book-folder> <chapter-slug>
   ```

---

## 2. Constraints & Guardrails
- **No Direct Canon Mutations**: Never manually edit files in `canon/state/snapshot.yml`. All canon updates must be applied via `bf apply change`.
- **Zero-Trust Input**: Never guess details or invent story facts. If facts are unknown, query them via `bf memory search "<query>"` or resolve aliases via `bf memory resolve "<name>"`.
- **Validation is the Gate**: Any validation failures (`bf validate`) must be resolved before executing `bf apply`.
