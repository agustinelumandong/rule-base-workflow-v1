# Series Workspace Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `bookforge init` initialize the current directory as an isolated series workspace, and add `bookforge book-init book-1` to create a book inside it.

**Architecture:** Keep the existing file-based workflow. A series folder owns shared canon and settings; each book remains under its `books/` directory. AI prose remains normal chapter drafts, while AI-suggested canon changes are written under `proposed/` and never overwrite approved canon.

**Tech Stack:** Python standard library, argparse, unittest, existing BookForge validator and series helpers.

## Global Constraints

- No new dependency, database, server, or copied skill implementation.
- `bookforge init` runs inside the intended empty series directory.
- `bookforge book-init book-1` runs inside an initialized series directory.
- Approved canon is `series-bible.md`, `settings.json`, and each book's `phase-0.md` and `rulebook.md`.
- `proposed/` is not loaded as canon by validation or context generation.

---

## Files

| Path | Responsibility |
| --- | --- |
| `bookforge/core/series.py` | Create series and book workspaces. |
| `bookforge/cli.py` | Expose the two short commands. |
| `bookforge/config.py` | Resolve bundled templates independently of the user's current directory. |
| `bookforge/templates/*.md` | Neutral, source-safe files for each newly created book. |
| `tests/test_series.py` | Filesystem and CLI regression tests. |
| `README.md` | Document the normal workflow. |

### Task 1: Add the series workspace initializer

**Files:**
- Modify: `bookforge/core/series.py`
- Modify: `bookforge/config.py`
- Create: `bookforge/templates/phase-0.md`
- Create: `bookforge/templates/rulebook.md`
- Create: `bookforge/templates/mood-lock.md`
- Create: `bookforge/templates/chapter-summaries.md`
- Test: `tests/test_series.py`

**Interfaces:**
- `initialize_series_workspace(series_folder: Path) -> list[str]`
- `is_series_workspace(series_folder: Path) -> bool`

- [ ] **Step 1: Write failing filesystem tests**

Add a new `TemporaryDirectory` fixture and these tests:

```python
def test_initialize_series_workspace_creates_only_series_files(self):
    created = series.initialize_series_workspace(self.empty_series_dir)

    for name in ("series.json", "series-bible.md", "series-research-pack.md",
                 "settings.json", "AGENTS.md"):
        self.assertTrue((self.empty_series_dir / name).exists())
    self.assertTrue((self.empty_series_dir / "books").is_dir())
    self.assertTrue((self.empty_series_dir / "proposed").is_dir())
    self.assertFalse((self.empty_series_dir / "books" / "book-1").exists())
    self.assertIn("Created series workspace", created[0])

def test_initialize_series_workspace_rejects_unowned_nonempty_folder(self):
    (self.empty_series_dir / "notes.md").write_text("keep", encoding="utf-8")
    with self.assertRaises(FileExistsError):
        series.initialize_series_workspace(self.empty_series_dir)
```

- [ ] **Step 2: Verify the tests fail**

Run: `python -m pytest tests/test_series.py -q`

Expected: FAIL because the new functions do not exist.

- [ ] **Step 3: Implement the minimal scaffold**

In `series.py`, create exactly:

```text
series.json
series-bible.md
series-research-pack.md
settings.json
AGENTS.md
books/
proposed/
```

Use this minimal `series.json` shape:

```json
{"name": "<folder title>", "books": []}
```

`AGENTS.md` must only state the approved canon paths, that AI canon suggestions belong in `proposed/`, and that chapter drafts are editable. Do not copy the repository's long AGENTS file or any Tex Cade facts.

Return `Created series workspace: <path>`. If `series.json` is already present, return `Series workspace already initialized: <path>`; otherwise refuse a nonempty folder.

- [ ] **Step 4: Run focused verification**

Run: `python -m pytest tests/test_series.py -q`

Expected: PASS.

### Task 2: Initialize a book inside the current series

**Files:**
- Modify: `bookforge/core/series.py`
- Test: `tests/test_series.py`

**Interfaces:**
- `initialize_book_in_series(series_folder: Path, book_slug: str) -> list[str]`
- Destination is always `series_folder / "books" / book_slug`.

- [ ] **Step 1: Write failing tests**

```python
def test_initialize_book_in_series_creates_book_below_books_dir(self):
    series.initialize_series_workspace(self.empty_series_dir)
    series.initialize_book_in_series(self.empty_series_dir, "book-1")
    book = self.empty_series_dir / "books" / "book-1"

    for name in ("phase-0.md", "rulebook.md", "mood-lock.md",
                 "chapter-summaries.md"):
        self.assertTrue((book / name).exists())
    self.assertTrue((book / "chapters").is_dir())

def test_initialize_book_in_series_rejects_bad_slug_and_missing_series(self):
    with self.assertRaises(ValueError):
        series.initialize_book_in_series(self.empty_series_dir, "Book 1")
    with self.assertRaises(FileNotFoundError):
        series.initialize_book_in_series(self.uninitialized_dir, "book-1")
```

- [ ] **Step 2: Verify the tests fail**

Run: `python -m pytest tests/test_series.py -q`

Expected: FAIL because the function does not exist.

- [ ] **Step 3: Add four neutral bundled templates**

Create the four files under `bookforge/templates/`. They must contain placeholders only, no `books/book-example` paths, character names, plot facts, banned conflict examples, or per-chapter word targets. The rulebook template must retain the existing required headings:

```text
## Source Hierarchy
## Length Handling Rules
## Do Not Invent
## Characters
## Chapter Continuity Ledger
## Unknowns
```

- [ ] **Step 4: Implement the smallest book scaffold**

Accept only `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Refuse a nonempty destination.

Set a package-relative template path in `config.py`, using `Path(__file__).resolve().parent / "templates"`, so templates can be found while the current directory is a user's series folder. Copy the four bundled templates for only `phase-0.md`, `rulebook.md`, `mood-lock.md`, and `chapter-summaries.md`; create `chapters/`. Do not copy a completed draft, continuity file, or series bible into a book.

Add the slug to `series.json["books"]` after creation succeeds.

- [ ] **Step 5: Run focused verification**

Run: `python -m pytest tests/test_series.py -q`

Expected: PASS.

### Task 3: Expose `init` and `book-init` from the current directory

**Files:**
- Modify: `bookforge/cli.py`
- Test: `tests/test_series.py`

**Interfaces:**
- `bookforge init` calls `initialize_series_workspace(Path.cwd())`.
- `bookforge book-init BOOK_SLUG` calls `initialize_book_in_series(Path.cwd(), BOOK_SLUG)`.

- [ ] **Step 1: Write failing CLI tests**

Make `main` accept `argv: list[str] | None = None` if it does not already, so the tests can call it without changing process arguments:

```python
def test_cli_init_uses_current_directory(self):
    with patch("bookforge.cli.Path.cwd", return_value=self.empty_series_dir):
        self.assertEqual(cli.main(["init"]), 0)
    self.assertTrue((self.empty_series_dir / "series.json").exists())

def test_cli_book_init_uses_current_series_directory(self):
    series.initialize_series_workspace(self.empty_series_dir)
    with patch("bookforge.cli.Path.cwd", return_value=self.empty_series_dir):
        self.assertEqual(cli.main(["book-init", "book-1"]), 0)
    self.assertTrue((self.empty_series_dir / "books" / "book-1").is_dir())
```

- [ ] **Step 2: Verify the tests fail**

Run: `python -m pytest tests/test_series.py -q`

Expected: FAIL because `init` still requires a path and `book-init` is unknown.

- [ ] **Step 3: Implement command parsing and errors**

Replace the old book-folder init parser with:

```python
subparsers.add_parser(
    "init", help="Initialize the current directory as a series workspace"
)
parser_book_init = subparsers.add_parser(
    "book-init", help="Initialize a book in the current series workspace"
)
parser_book_init.add_argument("book_slug")
```

Add `cmd_book_init`. Print return messages. For `FileExistsError`, `FileNotFoundError`, or `ValueError`, print one stderr error and return `1`.

- [ ] **Step 4: Run focused verification**

Run: `python -m pytest tests/test_series.py -q`

Expected: PASS.

### Task 4: Document and verify the workflow

**Files:**
- Modify: `README.md`
- Test: `tests/test_series.py`

- [ ] **Step 1: Replace the initialization quick start**

Document only this normal path:

```bash
mkdir my-series
cd my-series
bookforge init
bookforge book-init book-1
```

State that `init` creates series canon/settings/AGENTS plus `books/` and `proposed/`; `book-init` creates one book; prose drafts may be saved automatically, while canon suggestions remain in `proposed/` until approved.

- [ ] **Step 2: Run regression checks**

Run:

```bash
python -m pytest tests/test_series.py -q
python -m pytest -q
git diff --check
```

Expected: all tests PASS and no whitespace errors.

- [ ] **Step 3: Smoke test outside the repository**

Run in a temporary directory, using the repository's absolute CLI path:

```bash
tmp_dir=$(mktemp -d)
cd "$tmp_dir"
PYTHONPATH=/home/cshan28/Dev/Projects/Experimental/rule-base-workflow-v1 \
  python -m bookforge.cli init
PYTHONPATH=/home/cshan28/Dev/Projects/Experimental/rule-base-workflow-v1 \
  python -m bookforge.cli book-init book-1
test -f series.json
test -f books/book-1/phase-0.md
```

Expected: all created files are below the temporary directory.

## Self-review

- The plan provides exactly the requested two commands and preserves the existing file-based workflow.
- It intentionally excludes automatic AI generation, a database, copied skills, and a canon-promotion command. The `proposed/` directory is the safe destination for canon suggestions within this scope.
- It intentionally changes the existing `bookforge init PATH` behavior. Tests and README change in the same implementation.
