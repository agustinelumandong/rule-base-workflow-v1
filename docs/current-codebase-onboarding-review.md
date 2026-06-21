# Current Codebase Onboarding Review

**Reviewed:** 2026-06-20  
**Repository:** `current-workflow`  
**Scope:** Current implementation, request flow, validation and state boundaries, modification risks, and working conventions

## 1. Overview

BookForge is a local, human-supervised manuscript production pipeline. It converts approved outlines and story rules into chapter plans, drafts, validation results, continuity handoffs, and compiled manuscripts. It is currently a Python CLI and file-backed workflow, not a web service.

Evidence:

- `README.md` identifies the project as a manuscript workflow for planning, drafting, expanding, validating, and polishing Western fiction.
- `docs/BOOKFORGE-MASTER-PLAN.md` describes the broader goal as a human-supervised fiction production platform.
- `setup.py` installs the `bookforge` and `bf` console commands.

### Problem Being Solved

The project turns a loose AI-assisted writing process into a repeatable workflow with explicit sources, chapter planning, scoped context, deterministic checks, continuity handoffs, and compilation. Its main concerns are:

- preventing unsupported invention and continuity drift;
- keeping planning separate from prose generation;
- enforcing Western tone and project-specific restrictions;
- deciding whether a manuscript needs repair, expansion, review, or no further action;
- keeping chapter-level model context smaller than the complete manuscript;
- preserving inspectable Markdown and JSON artifacts instead of hiding state inside an AI conversation.

### High-Level Structure

| Location | Responsibility |
| --- | --- |
| `bookforge/cli.py` | CLI argument parsing and command dispatch |
| `bookforge/core/` | Orchestration, validation, compilation, context packets, state, research, pacing, and narrative checks |
| `bookforge/genre_packs/western/` | Western-specific prompts, rules, and validation material |
| `.agents/skills/manuscript-workflow-orchestrator/` | Agent-facing workflow instructions and compatibility scripts |
| `books/` | File-backed book and series workspaces |
| `settings.json` | Repository-level configurable name, style, and narrative review policy |
| `docs/` | Current workflow documentation and future product plans |
| `tests/` | Focused tests for core modules and packaged script shims |

The local scripts under `.agents/skills/manuscript-workflow-orchestrator/scripts/` are generally thin compatibility shims. For example, `run_manuscript_loop.py` imports and delegates to `bookforge.core.loop`, while `validate_manuscript_context.py` delegates to `bookforge.core.validator`. The package under `bookforge/core/` is therefore the implementation source of truth.

### Current Implementation Versus Product Plan

`docs/BOOKFORGE-MASTER-PLAN.md` is a future-facing blueprint. It describes APIs, browser interfaces, background workers, databases, policy services, and other later-phase capabilities. The current checkout is a local modular Python application using Markdown and JSON files. Roadmap capabilities must not be presented as already implemented.

## 2. Request Flow

A representative request is:

```bash
bf run-loop books/tex-cade/books-4
```

### Step 1: Console Entry Point

`setup.py` maps both `bookforge` and `bf` to `bookforge.cli:main`.

### Step 2: CLI Parsing and Dispatch

`bookforge/cli.py:main()` constructs the command parser. The `run-loop` parser accepts the book folder, target range, repair-attempt overrides, and maximum repair attempts. The resulting command is dispatched to `cmd_run_loop()` through the `commands` dictionary.

### Step 3: Request Normalization

`cmd_run_loop()`:

1. converts the supplied folder to `Path`;
2. rejects a missing folder;
3. parses `chapter-slug:attempt-count` overrides;
4. calls `bookforge.core.loop.run_loop_check()`;
5. prints the returned Markdown report;
6. returns exit code `2` only when the status is `BLOCKED`.

Actionable states such as `NEEDS_CONTEXT_REPAIR` and `NEEDS_EXPANSION` still return exit code `0`, so callers must inspect the report status rather than interpreting zero as manuscript completion.

### Step 4: Persistent Loop State and Length

`run_loop_check()` loads repair counts from `<book-folder>/loop-state.json` through `load_persistent_repairs()`. CLI overrides replace matching persistent values.

It then calls `build_length_state()`, which uses:

- `bookforge.core.length.find_target()` to resolve the word target;
- `bookforge.core.scanner.source_path()` to locate `phase-0.md`, `phase-00.md`, `outline.md`, or `chapter-outline.md`;
- `bookforge.core.length.find_drafts()` to count `chapters/chapter-*/chapter-*.md` and an optional epilogue.

### Step 5: Book and Chapter Discovery

The controller validates required book files and parses source chapter sections:

- `validator.validate_required_book_files()` checks the outline, `rulebook.md`, `mood-lock.md`, `chapter-summaries.md`, required rulebook headings, continuity-ledger coverage, and unresolved unknowns.
- `validator.parse_phase_chapters()` converts recognized source chapter headings into keys such as `chapter-01` and `epilogue`.
- `validator.discover_chapters()` discovers directories beneath `chapters/` and constructs `ChapterFiles` records.

This flow depends on exact file and directory naming conventions.

### Step 6: Chapter Validation

Each discovered chapter is passed to `validator.validate_chapter()`. That function coordinates:

- required `drafting-plan.md` checks;
- beat and source-context markers in `scene-breakdown.md`;
- combat action-plan discovery and validation;
- `world-state.json` location, inventory, injury, and transition checks;
- relationship validation;
- draft style and forbidden-content checks;
- lexical overlap with the matching outline section and required movements;
- presence of `continuity-out.md`.

Results are accumulated in a `ChapterReport` containing passes, warnings, and failures.

### Step 7: Whole-Book Checks

The loop additionally runs:

- `loop.scan_style_issues()` for banned terms and unwanted dialogue tags;
- `chain.check_continuity_out_content()` for required continuity sections;
- `narrative_quality.analyze()` for tension rotation, character distinctiveness, antagonist contrast, and weak decision writing;
- `rhythm.analyze()` for chapter word distribution and pacing classes.

### Step 8: Classification

`loop.classify()` applies this effective priority:

1. book-level hard repair;
2. exhausted repair attempts and `BLOCKED`;
3. chapter context repair;
4. continuity repair;
5. style repair;
6. expansion when below the soft minimum;
7. blocking when above the soft maximum;
8. hard narrative or rhythm rebalance;
9. `DONE_WITH_WARNINGS`;
10. `DONE`.

### Step 9: State Persistence and Target Selection

When context repair is required, the first failing chapter's attempt count is incremented. Clean chapters have their counters reset. `save_persistent_repairs()` then rewrites `loop-state.json` with repair attempts, UTC run time, and last status.

The controller selects:

- the first failing chapter for context repair;
- the first continuity failure for continuity repair;
- the first style issue for style repair;
- the shortest passing non-epilogue chapter for expansion;
- a rhythm trim candidate for pacing rebalance.

### Step 10: Response

The response is a Markdown report containing status, stop/continue decision, reason, prompt mode, next action, length state, and selected quality notes.

The loop does not generate prose. It reports an action contract for a person or coding agent. Chapter work normally uses `bookforge.core.packet.render_packet()` to combine the source section, chapter summary, rulebook excerpt, research, mood lock, pacing, continuity handoffs, and scene breakdown into `context-packet.md`.

After edits, validation runs again. Final manuscript assembly uses `bookforge.core.compiler.compile_manuscript()`, which discovers drafts, joins them, removes beat headings, normalizes dialogue-anchor spacing, and writes the compiled Markdown file.

## 3. Risk Areas

### High: Validation Mutates World State

`validator.validate_chapter()` calls `world.validate_scene_world_state()`, which applies declared transitions directly to the supplied state object, then calls `world.save_world_state()`. Running validation can therefore change `world-state.json` and affect later validation runs.

Recommended direction: make validation operate on a copy and persist state only through an explicitly named mutation or approval command.

### High: Loop Inspection Mutates Repair State

Every successful `run_loop_check()` calls `save_persistent_repairs()`. A command described as checking the next action therefore changes `loop-state.json`, including repair counters and timestamps.

This is particularly risky when debugging against active manuscript folders. Use temporary fixtures for tests and review `loop-state.json` diffs after real runs.

### High: Book-Issue Severity Is Flattened

`validator.validate_required_book_files()` returns all issue messages in a list named `failures`, regardless of original severity. `loop._required_book_file_issues()` then reconstructs every string as a `HARD` issue.

This loses the `ManuscriptIssue` severity assigned by the validator and makes the soft-book-warning branch in `classify()` unreliable. The loop should consume `validate_required_book_file_issues()` directly.

### Medium: Broad Exception Handling Hides Invalid State

Several boundaries catch `Exception` and continue with empty or default data:

- outline parsing can silently become an empty chapter map;
- malformed `loop-state.json` becomes empty repair history;
- rhythm analysis failures disappear from loop classification;
- failed state writes are ignored;
- invalid `world-state.json` is replaced by default empty state.

These fallbacks can produce plausible reports from incomplete evidence. Expected errors should be caught narrowly, while malformed authoritative state should generate an explicit hard issue.

### Medium: Heuristic Parsing Is Format-Sensitive

The system relies on regular expressions and lexical overlap for several important contracts:

- chapter heading recognition;
- beat and context-lock extraction;
- source-alignment scores;
- scene splitting;
- combat-scene detection;
- world-state transition tags;
- relationship and style signals.

Minor Markdown formatting changes can therefore alter behavior. Format changes need parser fixtures before existing documents are migrated.

### Medium: Expansion Selection Ignores Dramatic Intent

`choose_expansion_chapter()` selects the shortest passing normal chapter. It does not use pacing class, source movement, chapter function, or the chapter pacing plan when choosing an expansion target.

Treat the returned chapter as a mechanical suggestion. Confirm it against `chapter-pacing-plan.md` and the approved source before editing prose.

### Medium: Packaging Does Not Declare All Runtime Dependencies

`setup.py` declares `install_requires=[]` and states that the package uses only the standard library. `packet.load_subgenre_rules()` imports `yaml`, and `headroom.py` optionally imports the third-party `headroom` package.

A clean installation may therefore behave differently or fail when loading genre configuration. Required and optional dependency groups should be declared explicitly.

### Medium: Integration Coverage Is Limited

The suite currently passes, but most coverage is focused on isolated helpers. There is no test that executes a complete realistic `run_loop_check()` across source parsing, chapter validation, persistence, selection, and report generation. CLI dispatch and the interactive TUI are also largely uncovered.

Current verification:

```text
109 passed, 2 warnings in 8.19s
```

The warnings came from SWIG-backed objects loaded by the optional Headroom dependency.

### Medium: Documentation Drift

The README says the repository is a guided workflow rather than a fully autonomous loop, while the current package contains a controller that classifies states, selects a target chapter, persists retry state, and reports `CONTINUE` or `STOP`.

The correct interpretation is that BookForge autonomously recommends the next bounded action, but a human or agent still performs prose changes. Documentation should use that distinction consistently.

### Operational: Active Manuscript Files Are Dirty

At review time, the `book/tex-cade` branch contained existing changes across Book 4 drafts, continuity files, context packets, manuscript output, and `loop-state.json`. Do not use that active tree as a disposable integration fixture or overwrite those changes during unrelated engineering work.

## 4. Synthesis

### Conventions to Follow

1. Treat `bookforge/core/` as implementation authority. Keep agent scripts as thin delegates.
2. Preserve the source hierarchy: user instruction, outline, rulebook, chapter plans, and continuity handoffs.
3. Preserve artifact names and directory conventions such as `chapter-01/chapter-01.md`.
4. Return structured `ManuscriptIssue` values from validation boundaries instead of flattening them to strings.
5. Keep deterministic checks before subjective or model-assisted review.
6. Separate validation from repair and persistence.
7. Use `context-packet.md` for normal chapter work instead of loading the full manuscript.
8. Keep configurable review signals in `settings.json`, but never let configuration weaken project-level bans.
9. Make targeted edits; avoid regenerating whole chapters to fix isolated validator findings.
10. Update `continuity-out.md` after chapter drafting or expansion.

### Pitfalls to Avoid

- Do not assume exit code `0` from `bf run-loop` means `DONE`.
- Do not modify only a shim when behavior belongs in `bookforge/core/`.
- Do not use validator `PASS` as proof of prose quality or historical accuracy.
- Do not accept the mechanically shortest chapter as an automatic expansion choice.
- Do not change heading formats without updating scanner, validator, packet, and tests.
- Do not run state-writing commands casually against an active dirty book folder.
- Do not treat the master plan's future API, UI, database, or worker architecture as implemented.
- Do not silently recover from corrupt authoritative files.

### How Changes Propagate

A change to a core manuscript artifact or format usually affects multiple layers:

```text
source or artifact contract
-> scanner and discovery
-> validator parsing and issue severity
-> context packet selection
-> loop classification and chapter selection
-> CLI/TUI report
-> compiler or generated manuscript
-> tests and workflow documentation
```

Examples:

- A new rulebook section requires validator, packet-extraction, template, example-book, and test changes.
- A new chapter naming pattern requires scanner, validator discovery, length counting, compiler discovery, pacing, and tests.
- A new issue type requires `issue.py`, the producing validator, loop priority, report rendering, and regression tests.
- A new state transition requires parser, world-state validation, persistence rules, repair behavior, and integration fixtures.

### Recommended Verification Sequence

For core workflow changes:

1. run the focused unit tests for the modified module;
2. run `python -m pytest -q`;
3. exercise the affected command against a temporary representative book fixture;
4. inspect all generated Markdown and JSON diffs;
5. confirm that validation did not mutate state unexpectedly;
6. confirm the selected next action matches the approved pacing and source material;
7. update user-facing workflow documentation when behavior changes.

## Review Result

The current implementation is a useful local proof engine with clear artifact boundaries and good focused test coverage. Its main engineering weakness is that validation, workflow decision-making, and state mutation are not consistently separated. The safest future work is to preserve the file contracts, carry typed issues across module boundaries, remove hidden mutation from checks, and add realistic end-to-end loop fixtures before expanding interfaces or automation.
