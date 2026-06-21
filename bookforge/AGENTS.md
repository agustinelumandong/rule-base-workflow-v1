# BookForge Core Package Developer Instructions

Use these rules when modifying CLI commands, configurations, user interfaces, templates, or high-level wrappers within the `bookforge/` directory.

---

## 1. Directory Structure & Architecture

```
bookforge/
├── AGENTS.md               <-- You are here
├── cli.py                  <-- CLI parser, routing, subcommands
├── tui.py                  <-- Text Terminal User Interface wrapper
├── config.py               <-- Shared settings, global configurations
├── templates/              <-- Standard markdown blueprints & skeletons
├── prompts/                <-- Prompt blocks used across LLM pipelines
└── core/                   <-- Narrative execution engines (State, Folding, Pacing)
```

- **`cli.py`**: The sole command-line interface entry point. Contains argument parsers and command routes. Keep command functions thin; delegate all business logic to sub-modules in `bookforge/core/`.
- **`tui.py`**: The interactive Terminal User Interface wrapper. Avoid coupling TUI display logic with core domain logic.
- **`templates/` & `prompts/`**: Static templates (e.g. `research-pack.md`) and prompt locks. Do not modify formatting tags without adjusting corresponding core parser/compiler patterns.

---

## 2. CLI Routing & Extensions (`cli.py`)

- Subcommands are structured using `argparse` nested subparsers.
- Each subcommand configuration block must follow the standard:
  ```python
  parser_name = subparsers.add_parser('cmd-name', help='help text')
  parser_name.add_argument('--option', ...)
  parser_name.set_defaults(func=handle_cmd_name)
  ```
- Command handlers (e.g., `handle_cmd_name(args)`) must:
  1. Extract and sanitize input parameters.
  2. Instantiate domain helpers relative to the target book directory.
  3. Call the relevant orchestrator function in `bookforge/core/`.
  4. Capture issues, format console output gracefully, and return `0` for success or `1` for failures.

---

## 3. TUI Development (`tui.py`)

- The TUI uses standard curses/text structures to drive the pipeline.
- Do not mix file I/O operations directly in user interaction frames; invoke core models to read/write state.
- Keep layout components modular: sidebar menu, main logging panel, and standard bottom status bar.

---

## 4. General Development Constraints

- **Do not introduce heavy external dependencies** without approval. Use Python's standard library or existing dependencies listed in `setup.py`.
- **Unit Tests**: All CLI commands must be mocked or have corresponding unit test assertions in `tests/`. Run tests before applying package changes.
