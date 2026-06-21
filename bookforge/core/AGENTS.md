# BookForge Core Domain Developer Instructions

Use these rules when modifying core domain logic, scanners, state management, context packet builders, or pacing orchestrators under `bookforge/core/`.

---

## 1. State Mutations & Event Sourcing (`canon.py`)

- **Zero Direct Snapshot Mutations**: Never write functions that modify `snapshot.yml` or `world-state.json` directly. All updates must be appended as event records under `canon/events/`.
- Rebuild state only by folding the event stream from the beginning of the book's history.
- **Event Types**: Supported event types include `character_status`, `character_mutation` (travel, inventory changes, injuries, secrets learned, relationships), and `object_mutation`. Ensure any new event schema is supported by both `fold_canon()` and `validate_canon()`.

---

## 2. Smart Context & Token Budgeting (`packet.py`, `budget.py`)

- **Keep Packets Lean**: When editing context builders, ensure the task-specific logic isolates only the resources relevant to that task (e.g., draft-prose, continuity-check).
- **Token Estimation**: Keep the token estimator simple (`len(text) // 4`). Do not introduce external tokenizer dependencies (like tiktoken or transformers).
- **Enforce Budgets**: Any additions to context packets must be registered inside `TASK_BUDGETS` and run through the scaling/trimming pipeline. Trimming priority is:
  1. Truncate non-critical sections (e.g., large research lists, general notes).
  2. Drop non-critical sections entirely if the limit is still exceeded.
  3. Truncate critical sections (e.g., drafts, outline beats) as a last resort.

---

## 3. Path & Series Directory Resolution (`scanner.py`)

- Always resolve paths relative to the passed `book_folder` parameter.
- Support both legacy flat chapter directories (`chapters/chapter-NN/`) and staging directories (`changes/chapter-NN/`).
- Do not hardcode absolute system paths. Use `Path` objects from the standard library `pathlib`.
- Support series-level nesting: check parent directories for global `rulebook.md`, `mood-lock.md`, and shared `research-pack.md` assets if they do not exist inside the local `book_folder`.

---

## 4. Pacing & Chapter Rhythm (`pacing.py`)

- Keep chapter length pacing flexible. Ensure chapters vary in length based on dramatic beats, rather than using uniform target word counts.
- Generate and sync pacing metrics using the target `chapter-pacing-plan.md` outlines.

---

## 5. Memory & Unknowns Wizard (`memory.py`, `unknowns.py`)

- **Resolution Wizard**: When prompting or parsing characters/items during resolving loops, always check the canonical `aliases.yml` dictionary first.
- Query unknown narrative facts through historical searches rather than guessing.
