# BookForge Validation Engine Developer Instructions

Use these rules when modifying consistency checkers, style validators, schema formats, or orchestration modules under `bookforge/core/validators/`.

---

## 1. Exception Handling & Consolidated Reports

- **Never Raise Exceptions**: Individual validation functions or checker loops must never raise raw exceptions (e.g. `ValueError`, `KeyError`) during standard validation.
- All failures, warnings, and errors must be caught and appended as issues (`ValidatorIssue` or `Issue`) inside a consolidated `ValidatorReport` object.
- System failures (e.g., missing essential configurations) should return a validation issue marked with `Severity.HARD`.

---

## 2. Validator Structure & Responsibility

- **`style.py`**:
  - Validates style-lock compliance (e.g., banned words, dialogue tags, modern/clinical terminology).
  - Implements suffix openers analysis (e.g., starting sentences with "-ing" verbs) and sentence opener variety checks.
  - Keeps regex compilation cached at the module level for optimal validation performance.
- **`format.py`**:
  - Enforces frontmatter structure and mandatory section checks (e.g. Setting Function, Story Pattern, Hard Guardrails, Ending State).
  - Validates Markdown syntax compliance, headings (`h1` counts), and file structure layout.
- **`continuity.py`**:
  - Cross-references character references, location mentions, and item holdings in draft prose against the event-sourced `snapshot.yml`.
  - Flags dead characters performing actions, teleportation warnings, and item ownership conflicts.
- **`orchestration.py`**:
  - Discovers validation units (`chapters/` and `changes/` directories).
  - Sequences execution of checks, merging all issues into the final validator report returned to the CLI.

---

## 3. Performance & Determinism

- Validation must remain fully deterministic, local, and fast.
- Do not make external API requests or run deep learning models inside validators. Use regular expressions, schema parsers, and YAML validations instead.
