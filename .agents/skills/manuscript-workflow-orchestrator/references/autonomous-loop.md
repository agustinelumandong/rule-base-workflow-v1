# Autonomous Loop

Use this protocol when the user asks to run the book, finish the manuscript, keep going until valid, or use an autonomous manuscript loop.

The loop is agent-driven. Python controls scanning, status, prioritization, and reporting. Codex performs prose edits, repairs, and source-locked expansion.

## Loop Protocol

1. Scan the book folder and confirm required source files exist.
2. Run context validation before any length decision.
3. Run the style-risk scan against chapter drafts.
4. Check manuscript length against the book-level target range.
5. Check chapter rhythm so the book does not pass with artificial same-size chapters.
6. Decide the next state: `DONE`, `NEEDS_CONTEXT_REPAIR`, `NEEDS_STYLE_REPAIR`, `NEEDS_EXPANSION`, `NEEDS_PACING_REBALANCE`, or `BLOCKED`.
7. Codex performs the next recommended action only when the report says `CONTINUE`.
8. Re-run the loop after each draft, expansion, or repair pass.

Before chapter-level prose edits, refresh the chapter context packet:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py books/<book-slug> --chapter chapter-XX
```

## Source Lock

All revisions and expansions must use only:

- `phase-0.md`
- `rulebook.md`
- `mood-lock.md`
- `chapter-summaries.md`
- the chapter's `scene-breakdown.md`
- approved prior drafts

Do not add unsupported names, motives, backstory, locations, lore, relationships, or plot bridges. Mark missing facts as `UNKNOWN` unless the missing fact blocks drafting.

## Status Rules

`DONE` means:

- current word count is above the minimum and within the natural target range
- context validator is `PASS`
- style-risk scan is clean
- no unsupported invention appears

`NEEDS_CONTEXT_REPAIR` means:

- context validator reports `WARN` or `FAIL`
- repair the named chapter before style work or expansion
- use prompt mode `repair`

`NEEDS_STYLE_REPAIR` means:

- style scan catches banned words, dialogue tags, unresolved markers, internal-monologue phrases, fixed-count language, or modern/clinical terms
- rewrite only the flagged line or passage
- use prompt mode `style`

`NEEDS_EXPANSION` means:

- manuscript is below the target minimum
- expand the recommended chapter from approved beats only
- use prompt mode `expansion`

`NEEDS_PACING_REBALANCE` means:

- manuscript meets total target but chapter rhythm looks too even
- trim or compress recommended chapters from approved material only
- use prompt mode `repair`

`BLOCKED` means:

- required source files are missing
- no manuscript drafts exist
- a missing fact blocks drafting
- the same chapter has reached the repair-attempt limit
- manuscript is above the target maximum and needs user direction before trimming

## Command

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/tex-cade --target-min 30000 --target-max 31000
```

Optional repair-attempt tracking:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/run_manuscript_loop.py books/tex-cade --repair-attempt chapter-08=2
```

## Expansion Guidance

When the loop returns `NEEDS_EXPANSION`, expand only inside approved beat boundaries. Add physical blocking, tactical movement, consequence, town reaction, restrained dialogue pressure, setting texture, and transitions.

Do not pad. Do not force beat or scene word counts. Do not invent unsupported story to satisfy length.

## Agent Checkpoint

Every loop action should end with:

```md
## Agent Checkpoint

- **Source Used:**
- **Mode:**
- **Changes Made:**
- **Risks:**
- **Next Action:**
- **Stop/Continue:**
```
