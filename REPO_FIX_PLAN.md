# Rule-Base-Workflow v1 — Repo Repair Plan

A prioritized, concrete plan to fix the structural, correctness, and hygiene problems
identified in the codebase audit. Each item lists the **problem**, the **fix**, the
**files touched**, **how to verify**, plus **effort** and **risk**.

The plan is organized into phases. Do them in order. Phase 0 is zero-risk and should
land first; later phases get progressively more invasive.

---

## Current State (verified, not assumed)

| Area | Finding |
|---|---|
| Orchestration entry surface | 13 scripts in `.agents/skills/manuscript-workflow-orchestrator/scripts/` are 17–21 line **shims** that do `from bookforge.core.X import *` then call `main()`. Not parallel implementations — but fragile and duplicated. |
| Stale default book folder | `books/tex-cade` is referenced as a default in **22 files** but does not exist. Only `books/book-example/` exists. |
| Exception swallowing | **45** bare `except Exception` sites across `bookforge/core/` (12 in `notebooklm.py` alone). A broken check silently looks like a clean check. |
| God module | `bookforge/core/validator.py` is **1,505 lines**. |
| Half-finished type migration | `bookforge/core/issue.py` defines `ManuscriptIssue`/`LoopDecision`/`Severity`, but `loop.classify()` still duck-types `object` (`book_failures: list[object]`, `_message_of(issue: object)`, `_severity_of(issue: object)`). |
| Git hygiene | `.gitignore` excludes `tests/` and `docs/`, so neither tests nor the canonical workflow docs are version-controlled. |
| Scratch pollution | `compile_helper.py`, `scratch_test_regex.py`, `scratch_test_runner.py` at repo root reference `books/tex-cade/books-2`. |
| Platform mismatch | Repo runs on **win32**, but `tui.py` uses POSIX-only `termios`/`tty`; install scripts are all `.sh`. `bf` with no args defaults to the TUI → crashes on Windows. |
| Config provenance | `outline_feedback_analysis.md` (root) is the design post-mortem that motivated `settings.json`. Currently orphaned documentation. |

---

## Guiding Principles

1. **One canonical engine.** `bookforge.core` is the engine. The `bf` CLI is the primary
   interface. The skill scripts either become real shims or are removed; we do not maintain
   two contract surfaces.
2. **Defaults must resolve.** No default path may point at a folder that doesn't exist.
3. **A validator must never lie.** Replace silent `except Exception` with specific
   exceptions or explicit logged fallbacks. A failed check is never "no issues."
4. **Preserve behavior, then improve types.** Fix correctness first; finish the
   `ManuscriptIssue` migration second; refactor the god module last.
5. **Version what matters.** Tests and docs are part of the system; they get tracked.

---

## Phase 0 — Zero-Risk Hygiene (do first, no behavior change)

### 0.1 Remove repo-root scratch files
- **Problem:** `compile_helper.py`, `scratch_test_regex.py`, `scratch_test_runner.py`
  hardcode `books/tex-cade/books-2` and clutter the root.
- **Fix:** Move them to a gitignored `scratch/` dir, or delete if no longer needed.
- **Verify:** `git status` shows only the intended move; `python compile_helper.py`-style
  references in docs updated or removed.
- **Effort:** S. **Risk:** None — these are throwaway.

### 0.2 Stop gitignoring `tests/` and `docs/`
- **Problem:** `.gitignore` excludes `tests/` and `docs/`, so the canonical workflow
  docs and any tests are local-only.
- **Fix:** Remove `tests/` and `docs/` lines from `.gitignore`. Add `docs/_build/` or
  similar if a build artifact dir is the real concern.
- **Verify:** `git check-ignore -v docs/workflow-v5.md` returns nothing; `git status`
  shows `docs/` staged.
- **Effort:** S. **Risk:** Low — review for any genuinely-private local docs first.

### 0.3 Document the design intent of `outline_feedback_analysis.md`
- **Problem:** Root-level post-mortem with no link from README or AGENTS.
- **Fix:** Either (a) move to `docs/design/outline-feedback-postmortem.md` and reference it,
  or (b) fold its conclusions into `docs/workflow-v5.md`. Keep the `settings.json`
  rationale discoverable.
- **Verify:** `grep -r outline_feedback` finds the new location; README links it.
- **Effort:** S. **Risk:** None.

---

## Phase 1 — Stale Defaults (high value, low risk)

### 1.1 Rename `books/tex-cade` defaults → `books/book-example` everywhere
- **Problem:** 22 files reference `books/tex-cade`, which does not exist. Anyone running
  the documented defaults gets `Error: book folder not found`.
- **Fix:** Replace `books/tex-cade` → `books/book-example` in:
  - `bookforge/cli.py` (8 `default="books/tex-cade"` sites)
  - `bookforge/core/loop.py`, `validator.py`, `length.py`, `scanner.py`, `compiler.py`,
    `rhythm.py`, `pacing.py`, `narrative_quality.py`, `packet.py`, `budget.py`
  - `.agents/skills/manuscript-workflow-orchestrator/scripts/resolve_unknowns.py`
  - `AGENTS.md`, `README.md`, `SKILL.md`, reference docs
  - `compile_helper.py`, `scratch_test_regex.py` (after Phase 0.1)
- **Decision needed:** Is `book-example` really the intended default sample, or should we
  keep `tex-cade` as the canonical name and rename the *folder* instead? **Recommend: make
  the sample folder canonical and the code match it.** Pick one.
- **Verify:** `grep -rn tex-cade` returns only intentional historical references (commit
  messages, etc.); `bf status` (with no book arg) runs without error.
- **Effort:** M. **Risk:** Low. Behavior-only if folder and code move together.

### 1.2 Make `bf` (no args) safe on Windows
- **Problem:** `bf` with no args launches the TUI (`tui.py`), which uses `termios` — a
  POSIX-only module. On win32 it crashes on import.
- **Fix:** Two options:
  - **(a) Recommended:** Change the no-arg default from `tui` to `status` (a safe,
    cross-platform summary). Move TUI behind an explicit `bf tui` subcommand guarded by
    a POSIX check that prints a friendly message on Windows.
  - **(b)** Add a Windows console-input fallback in `get_key()` (e.g. `msvcrt`).
- **Verify:** On win32, `bf` with no args prints status and exits 0; `bf tui` prints a
  clear "not supported on Windows" or works via the fallback.
- **Effort:** S (option a). **Risk:** Low.

---

## Phase 2 — Validator Trustworthiness (correctness-critical)

> The loop controller is a *validator*. A silently-swallowed error turns a hard failure
> into an apparent pass. This is the most dangerous class of bug in the repo.

### 2.1 Replace bare `except Exception` with specific handling
- **Problem:** 45 swallow sites. Worst offenders by count:
  `notebooklm.py` (12), `analytics.py` (5), `loop.py` (5), `series.py` (5), `world.py` (4),
  `persona.py` (3), `validator.py` (3).
- **Fix, by category:**
  - **JSON load/save** (`loop.load_persistent_repairs`, `save_persistent_repairs`,
    `analytics`, `series`): catch `json.JSONDecodeError` / `OSError` specifically. On
    decode failure, treat as corrupt-state and *surface* it (return a sentinel, warn,
    or fail the loop) — do **not** silently return `{}`.
  - **Draft discovery** (`build_length_state` `except Exception: counts = []`):
    catch `(OSError, UnicodeDecodeError)`. An empty manuscript and an unreadable one
    are different states.
  - **Rhythm/narrative** (`run_loop_check` `except Exception: rhythm_report = None`):
    log the exception to the loop report as a `[WARN] analysis unavailable: <exc>`, not
    a silent pass.
  - **Subprocess/CLI** (`notebooklm.py`): catch `subprocess.CalledProcessError`,
  `FileNotFoundError`, `TimeoutError` explicitly.
- **Add a tiny logging helper** (stdlib `logging`) so failures are observable, not silent.
- **Verify:** Inject a malformed `loop-state.json` and confirm the loop reports a
  decode error instead of proceeding with empty repair attempts. Add a regression test.
- **Effort:** M. **Risk:** Medium — changes loop behavior on failure paths. Needs tests.

### 2.2 Fix false-positive risk in `FORBIDDEN_LENGTH_LANGUAGE`
- **Problem:** `FORBIDDEN_LENGTH_LANGUAGE = ["word count", "words", ...]` is scanned
  against **draft prose lines** in `loop.scan_style_issues`. The token `"words"` will
  match legitimate prose ("he spoke the words slowly").
- **Fix:** Distinguish *meta language about length* from the literal word. Either:
  - Restrict the length-language scan to **planning artifacts** (scene-breakdowns,
    drafting-plans), not drafts; or
  - Match only multi-word phrases (`"word count"`, `"word quota"`, `"target length"`)
    and drop bare `"words"`.
- **Verify:** Unit test: a draft sentence containing "words" is not flagged; a
  drafting-plan line saying "target word count 3000" is flagged.
- **Effort:** S. **Risk:** Low.

---

## Phase 3 — Consolidate the Entry Surface

### 3.1 Decide the canonical interface and update `AGENTS.md`
- **Problem:** `AGENTS.md` (the agent's primary instruction set) tells the agent to run
  long script paths:
  `python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py`
  ...even though those are now shims and `bf` is the real CLI.
- **Fix:** Rewrite the `AGENTS.md` command examples to use `bf` equivalents
  (`bf run-loop`, `bf status`, `bf compile`, `bf resolve-unknowns`, etc.). Keep the
  script paths as a "legacy" note only if compatibility is required.
- **Verify:** Every command block in `AGENTS.md` uses `bf` and runs successfully.
- **Effort:** M. **Risk:** Low — documentation, but high-leverage (it's what the agent
  actually follows).

### 3.2 Harden the shim scripts (or remove them)
- **Problem:** The 13 shim scripts use `from bookforge.core.X import *`, which is fragile
  (pollutes namespace, hides intent, breaks if a name is renamed). `resolve_unknowns.py`
  even redefines its own `argparse` + default book folder instead of delegating fully.
- **Fix, two clean options:**
  - **(a) Keep as compat shims:** replace `import *` with explicit, narrow delegation:
    ```python
    from bookforge.core import loop
    if __name__ == "__main__":
        raise SystemExit(loop.main())
    ```
    Remove the duplicate argparse/default-folder logic from `resolve_unknowns.py`.
  - **(b) Remove entirely:** if `AGENTS.md` now points at `bf`, delete the shim files and
    add a one-line note that the old paths are gone.
- **Recommend (a)** if external muscle-memory/automation calls the script paths;
  **(b)** if nothing outside the repo references them.
- **Verify:** `python .agents/skills/.../run_manuscript_loop.py books/book-example`
  still produces the same report as `bf run-loop books/book-example`.
- **Effort:** S. **Risk:** Low (a) / Low-Medium (b, if anything external calls them).

---

## Phase 4 — Finish the Type Migration

### 4.1 Thread `ManuscriptIssue` through `loop.classify`
- **Problem:** `issue.py` defines a clean typed model (`Severity`, `IssueCategory`,
  `ManuscriptIssue`), but `loop.py` still operates on `list[object]` and recovers
  severity/message by duck-typing (`_severity_of`, `_message_of`). The migration is
  half done.
- **Fix:**
  - Change `classify()` signature from `book_failures: list[object]` to
    `book_failures: list[ManuscriptIssue]` (and the same for narrative/rhythm issue lists).
  - Have `_required_book_file_issues` already returns `ManuscriptIssue` (it does) —
    propagate that type instead of re-duck-typing.
  - Replace `_severity_of` / `_message_of` with direct attribute access.
  - Where rhythm/narrative modules return their own issue dataclasses, either adopt
    `ManuscriptIssue` there or add a single adapter at the boundary.
- **Verify:** `mypy bookforge/core/loop.py` (or a `# type: ignore`-free strict pass) is
  clean; existing loop behavior is unchanged (golden-file test the loop report before
  and after).
- **Effort:** M. **Risk:** Medium — touches the core decision function. Needs a
  snapshot/golden test of `run_loop_check` output captured *before* the change.

---

## Phase 5 — Decompose the God Module

### 5.1 Split `validator.py` (1,505 lines) into focused submodules
- **Problem:** One file holds required-file checks, rulebook parsing, banned-word tables,
  conflict regexes, chapter validation, unknowns delegation, and the `--ai-prompt`
  generator. Hard to navigate, hard to test.
- **Fix:** Split by responsibility, keeping a thin public facade for back-compat:
  - `bookforge/core/validator_lexicon.py` — `BANNED_AI_ECHO_WORDS`,
    `MODERN_OR_CLINICAL_WORDS`, `FORBIDDEN_LENGTH_LANGUAGE`, `UNRESOLVED_MARKERS`,
    `INTERNAL_MONOLOGUE_PHRASES`, `FORBIDDEN_CONFLICT_PATTERNS`, `DIALOGUE_TAG_RE`,
    `STYLE_*` compiled regexes.
  - `bookforge/core/validator_rulebook.py` — `REQUIRED_RULEBOOK_SECTIONS`,
    `RULEBOOK_SECTION_HEADING_RE`, rulebook parsing/validation.
  - `bookforge/core/validator_chapter.py` — chapter discovery, beat/scene validation,
    `ChapterReport`.
  - `bookforge/core/validator_aiprompt.py` — the `--ai-prompt` generator.
  - `bookforge/core/validator.py` — re-exports the public API (`validate_chapter`,
    `validate_required_book_files`, `parse_phase_chapters`, `discover_chapters`,
    `chapter_sort_key`) so `from bookforge.core import validator` still works.
- **Verify:** Import-compatibility test (`loop.py`, `tui.py`, shims all import unchanged);
  golden-file the validator output before/after.
- **Effort:** M-L. **Risk:** Medium. Do **after** Phase 4 so the type model is stable.
  Capture golden outputs first.

---

## Phase 6 — Platform & Ops

### 6.1 Cross-platform install path
- **Problem:** `scripts/install.sh` and `scripts/check.sh` are bash-only; project is run
  on Windows.
- **Fix:** Either (a) add a `scripts/install.ps1` / `scripts/install.py` (preferred — a
  single `install.py` works everywhere), or (b) document that install requires Git Bash /
  WSL. Update README accordingly.
- **Verify:** `python scripts/install.py --dry-run` runs on win32.
- **Effort:** M. **Risk:** Low.

### 6.2 Isolate the NotebookLM dependency
- **Problem:** `notebooklm.py` (573 lines, 12 bare excepts) assumes the `nlm` CLI, `uv`,
  Antigravity/Gemini, and browser-auth cookies at `$HOME/.notebooklm-mcp-cli/...`. It's a
  large, fragile, platform-specific surface in an otherwise stdlib-only project.
- **Fix:** Confirm NotebookLM is genuinely optional (graceful degradation already exists
  via `is_nlm_available()`). Gate all `bf nlm` subcommands behind that check with clear
  errors, and move the heavy import/subprocess work so it only loads when invoked.
  Apply Phase 2.1 exception fixes here first (it has the most).
- **Verify:** `bf status` works with `nlm` absent; `bf nlm status` prints a clear
  "NotebookLM CLI not installed" message.
- **Effort:** S-M. **Risk:** Low.

---

## Phase 7 — Regression Safety Net (enables all the above)

### 7.1 Add golden-file + unit tests before refactoring
- **Problem:** No tracked tests (gitignored) and no behavior snapshots. Every refactor in
  Phases 2/4/5 is currently unverifiable.
- **Fix, in this order:**
  1. Un-ignore `tests/` (Phase 0.2).
  2. Capture **golden outputs**: run `bf run-loop`, `bf status`, `bf compile`,
     `validate_manuscript_context.py` against `books/book-example` and save the reports
     as `tests/golden/*.txt`.
  3. Add unit tests for pure functions: `soft_length_bounds`, `classify`, `choose_expansion_chapter`,
     `choose_rebalance_chapter`, `mode_for_status`, `compute_fingerprint`, and the
     lexicon regexes.
  4. Add the Phase 2.1 regression test (malformed `loop-state.json`).
- **Verify:** `python scratch_test_runner.py` (or `pytest`) passes; CI-ready.
- **Effort:** M. **Risk:** None — purely additive. **Should be done in parallel with
  Phase 0/1, before the riskier phases.**

---

## Suggested Execution Order

```
Week 1:  Phase 0 (hygiene) + Phase 7 (golden tests)        ← safe, unblocks everything
Week 1:  Phase 1 (defaults + Windows-safe bf)              ← high value, low risk
Week 2:  Phase 2 (exception + false-positive fixes)        ← correctness
Week 2:  Phase 3 (entry surface + AGENTS.md)               ← clarity for the agent
Week 3:  Phase 4 (type migration)                          ← needs golden tests
Week 3:  Phase 5 (decompose validator)                     ← needs Phase 4 + golden tests
Week 4:  Phase 6 (install.ps1/py + NotebookLM isolation)   ← ops polish
```

---

## Acceptance Criteria — "Done" means

- [ ] `grep -rn "tex-cade"` returns no live code/default references (only historical).
- [ ] `bf` with no args runs on Windows without crashing.
- [ ] No bare `except Exception: pass`/`return []` in `bookforge/core/` outside
      `notebooklm.py` subprocess code (and those catch specific exceptions).
- [ ] Injecting a malformed `loop-state.json` surfaces an error, not a silent pass.
- [ ] A draft sentence containing the word "words" is not style-flagged.
- [ ] `AGENTS.md` command examples all use `bf` and run successfully.
- [ ] `loop.classify` has no `list[object]` / duck-typed severity recovery.
- [ ] `validator.py` is a thin facade over focused submodules; all existing imports work.
- [ ] `tests/` and `docs/` are tracked; golden-file tests exist and pass.
- [ ] `bf status` works end-to-end on a clean clone on Windows with only stdlib.

---

## Open Decisions (need your call before starting)

1. **Canonical sample name:** keep `book-example`, or restore `tex-cade` as the real
   sample and rename the folder? *(Recommend: pick one canonical name.)*
2. **Shim scripts:** keep as hardened compat shims (Phase 3.2a) or delete them (3.2b)?
3. **NotebookLM:** keep as first-class integration, or demote to a clearly-optional plugin?
4. **Type checking:** adopt `mypy`/strict typing as a gate, or leave optional?
