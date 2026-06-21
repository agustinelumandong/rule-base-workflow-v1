# Golden Output Baseline

Captured by **M0.5** of `BOOKFORGE_V2_PLAN.md` — the regression net for the M2/M3 engine
refactor (event-sourced canon, validator decomposition, type migration).

## What's here

| File | Command | What it captures |
|---|---|---|
| `bf-status.txt` | `bf status books/book-example` | File validation, structure gaps, continuity chain, rhythm |
| `bf-run-loop.txt` | `bf run-loop books/book-example --target-min 30000 --target-max 31000` | Loop controller status, decision, reason, next action, length state, book-level issues |
| `validate-manuscript-context.txt` | `validate_manuscript_context.py books/book-example` | Book files validation, chapter status table |

## What the output means

The captured FAILs are **expected and correct** — they reflect the `book-example` template's
intended state:
- `book-example/rulebook.md` ships with `UNKNOWN` markers in `## Do Not Invent` and unresolved
  items in `## Unknowns`. These are *placeholders a real book resolves*; the template correctly
  flags them.
- `book-example` has no `chapters/` folder, so structure-gap and rhythm warnings are expected.

If a refactor (M2/M3) changes this output, that is a behavior change requiring investigation.
If the refactor is intentional, regenerate these files and note the reason in the commit.

## How to use

```bash
# After an engine change, re-run and diff:
python -c "import sys; sys.argv=['bf','status','books/book-example']; from bookforge.cli import main; sys.exit(main())" | diff - tests/golden/bf-status.txt
python -c "import sys; sys.argv=['bf','run-loop','books/book-example','--target-min','30000','--target-max','31000']; from bookforge.cli import main; sys.exit(main())" | diff - tests/golden/bf-run-loop.txt
python -c "import sys; sys.argv=['v','books/book-example']; from bookforge.core.validator import main; sys.exit(main())" | diff - tests/golden/validate-manuscript-context.txt
```

Empty diff = no behavior change. Non-empty = investigate before proceeding.

## Captured against

- Branch: `dev2v-windows`
- Date: 2026-06-21
- BookForge commit: post-M0.4 (scratch removal + tex-cade rename + cli default fix)
- Python: 3.12, pytest 9.1.1, pyyaml installed
