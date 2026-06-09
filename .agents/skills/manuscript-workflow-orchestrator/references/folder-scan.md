# Folder Scan

Use this before creating or updating manuscript workflow artifacts.

## Target Folder

- If the user names a folder, use that folder.
- If the user names a book slug, use `books/<book-slug>/`.
- If the user says "this book" and only one folder exists under `books/`, use that folder.
- If multiple book folders exist and the user did not choose one, ask which book folder to use.

## Source File Priority

Read the first source file that exists in the target folder:

1. `phase-0.md`
2. `phase-00.md`
3. `outline.md`
4. `chapter-outline.md`

If none exist, stop and report the missing source file. Do not infer a manuscript from unrelated files.

## Output Paths

Create or update these files in the same target folder:

- `rulebook.md`
- `mood-lock.md`
- `chapter-summaries.md`
- `chapters/chapter-XX/scene-breakdown.md`
- `chapters/chapter-XX/drafting-plan.md`
- `chapters/chapter-XX/chapter-XX.md`

Do not put book-specific artifacts in the project root.

## Scan Checklist

Before writing artifacts, identify:

- Book title and genre target.
- Length target if present.
- Core premise.
- Chapter list.
- Epilogue or teaser material.
- Character breakdowns.
- Setting, location, weapons, horse, faction, and series-arc facts.

If a needed fact is absent, write `UNKNOWN` in generated artifacts unless it blocks the next drafting step.
