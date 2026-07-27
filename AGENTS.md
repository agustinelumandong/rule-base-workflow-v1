# BookForge System Guide

## What This Repository Is

BookForge is a local, file-backed workflow for managing an AI-assisted fiction series. It is not a prose-writing prompt, a standalone validator, or a web service.

The system keeps story planning, approved canon, research, working drafts, and compiled manuscripts as separate files so that a change can be traced to its source and reviewed before it becomes canon.

The implementation lives in `bookforge/`. The command-line interface is `bookforge` (also available as `bf` when installed). The scripts under `.agents/skills/` are compatibility entry points around that implementation.

## Workspace Model

Run `bookforge init` in an empty directory to create a series workspace:

```text
series.json                 Series registry and metadata
series-bible.md             Approved series canon
series-research-pack.md     Shared historical/reference material
settings.json               Series configuration and policy data
AGENTS.md                   Generated series-local operating guide
books/                      Individual book workspaces
proposed/                   AI suggestions awaiting approval
```

Run `bookforge book-init <book-slug>` inside that series workspace to create:

```text
books/<book-slug>/
  phase-0.md                Approved outline
  rulebook.md               Book continuity and rules
  mood-lock.md              Book style and tone brief
  chapter-summaries.md      Approved chapter plan
  chapters/                 Chapter planning, drafts, and handoffs
```

Book-level `research-pack.md` files may be created from the series research pack when research is copied or synchronized for a book.

## Source and Approval Boundaries

Treat these as canonical only after explicit user approval:

1. `series-bible.md` and `settings.json`
2. A book's `phase-0.md` and `rulebook.md`

Research packs are approved reference material, not story canon. Chapter prose is editable working material, not canon. Put suggested canon changes in `proposed/`; do not silently turn an AI draft, research finding, or compiled manuscript into canon.

## System Flow

```text
approved outline → planning artifacts → chapter plans → editable drafts
       ↑                                                   ↓
  approved canon ← review and approval ← checks ← compile output
```

The normal sequence is:

1. Create or revise the approved outline.
2. Refresh book planning artifacts from that outline.
3. Create chapter-level plans and drafts.
4. Record continuity handoffs between chapters.
5. Run checks to identify structural, continuity, or style risks.
6. Compile approved drafts into reader-facing output.

Checks report conditions; they do not create canon. The loop controller selects the next action and stops at `DONE` or `BLOCKED`; it does not generate prose by itself.

## What to Update

| If this changes | Update the source of truth |
|---|---|
| Series-wide fact or policy | `series-bible.md` or `settings.json` |
| A book's plot, character fact, or continuity decision | that book's `phase-0.md` or `rulebook.md` |
| Historical or period reference | `series-research-pack.md` or the book's `research-pack.md` |
| Book tone or chapter plan | `mood-lock.md` or `chapter-summaries.md` |
| Chapter event or handoff | chapter plan/draft and `continuity-out.md` |
| Generated series instructions | `SERIES_AGENTS_TEMPLATE` in `bookforge/core/series.py` |
| Shared project behavior | the relevant module under `bookforge/core/` and its focused tests |

Never repair a compiled manuscript as a substitute for repairing its source draft or planning artifact. Regenerate outputs after source changes.

## Generated Series Guides

The root `AGENTS.md` is this system guide. `bookforge init` writes a separate series-local `AGENTS.md` from `SERIES_AGENTS_TEMPLATE` in `bookforge/core/series.py`.

The generated guide should explain the series workflow, canon boundary, available shared skills, and commands. It must remain generic: do not add a particular book number, character, POV, setting, or plot fact to the template. Existing generated files are not automatically updated when the template changes; update or regenerate them deliberately.

Shared skills stay centralized under `.agents/skills/`; `bookforge init` does not copy them into each series workspace.

## Maintenance Rules

- Prefer the smallest source-level change that fixes the real behavior.
- Read the affected module and its callers before changing system behavior.
- Keep templates, generated guidance, validators, and tests aligned when a file contract changes.
- Preserve user work and unrelated working-tree changes.
- Do not commit, publish, or overwrite a series workspace unless the user explicitly asks.
- Keep documentation honest about the current local Python/Markdown implementation; future roadmap documents are not proof of implemented features.

## Common Commands

```bash
# Run inside a new, empty series directory.
bookforge init
bookforge book-init book-1

# Run from the project or series workspace as appropriate.
bookforge status books/<book-slug>
bookforge run-loop books/<book-slug>
bookforge run-loop books/<book-slug> --prepare
bookforge run-loop books/<book-slug> --record-repair chapter-01
bookforge compile books/<book-slug>
```

`run-loop` only evaluates by default. `--prepare` writes a context packet for the selected chapter; it never changes drafts or canon. After a human or external agent attempts a repair, use `--record-repair` before evaluating again.

Use the focused checks named by the changed module or command. A successful compile and a successful validation are separate results; report them separately.
