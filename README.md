# Rule Base Workflow1v

This repository is a manuscript workflow project for planning, drafting, expanding, validating, and polishing Western fiction with AI assistance.

## What this project is

It is not an app or a web service. It is a structured writing system built around:

- `books/<book-slug>/phase-0.md` as the main story source
- `rulebook.md` for continuity, character facts, and source priority
- `mood-lock.md` for tone and style rules
- `chapter-summaries.md` for chapter-level planning
- `scene-breakdown.md` and `drafting-plan.md` for chapter structure
- chapter draft files for the actual manuscript text
- workflow docs and local skills for planning, validation, and cleanup

The active sample book in this repo is `books/tex-cade/`.

## Why this workflow helps

This project improves the current writing workflow by:

- keeping story facts in one place
- reducing continuity mistakes
- separating planning from drafting
- enforcing tone and style rules before prose gets too far off track
- making it easier to validate chapters and length before final polish
- supporting repeatable chapter-by-chapter expansion instead of one-off drafting

In short: it turns a loose writing process into a repeatable system.

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/agustinelumandong/rule-base-workflow-v1
cd rule-base-workflow-v1
```

### 2. Open it in VS Code

```bash
code .
```

### 3. Pick a book folder

Start with `books/tex-cade/` or copy it to create your own book workspace.

### 4. Review the workflow docs

Read:

- `docs/guided-agent-workflow.md`
- `docs/workflow-v5.md`
- `books/tex-cade/phase-0.md`

### 5. Start experimenting

A simple path is:

1. update or create `phase-0.md`
2. refresh the `rulebook.md`
3. build `mood-lock.md`
4. create `chapter-summaries.md`
5. write `scene-breakdown.md` for each chapter
6. draft the chapter files
7. run validation and cleanup passes

## Validation commands

If you want to check the manuscript context and length, use:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/tex-cade
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/tex-cade
```

## Project layout

```text
books/
  tex-cade/
    phase-0.md
    rulebook.md
    mood-lock.md
    chapter-summaries.md
    chapters/
      chapter-01/
      chapter-02/
      ...
docs/
  guided-agent-workflow.md
  workflow-v5.md
references/
```

## If you want to use this on your own machine

- clone the repo
- open it in your editor
- duplicate the book folder you want to experiment with
- edit the source files for your own story
- run the validation scripts after drafting changes

## Best fit for this repo

Use this when you want a repeatable AI-assisted book workflow with:

- strong story continuity
- chapter planning before drafting
- tone and style control
- validation before polish
- a clean path from outline to manuscript

## Status

This is a guided workflow, not a fully autonomous loop. You still choose when to start each pass and what to focus on next.

Feel free to contribute improvements, fixes, or new workflow ideas.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.
