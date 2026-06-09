# Token Budget

Use this reference when a task risks loading too much manuscript context.

## Budget Rule

Load the smallest source set that can safely complete the current prompt mode.

## Checker

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_context_budget.py books/<book-slug> --chapter chapter-XX --mode drafting
```

Modes:

- `planning`
- `drafting`
- `repair`
- `style`
- `validation`
- `expansion`
- `final`

## Loading Rules

- Do not load the full manuscript unless final review or compilation requires it.
- Do not load the full rulebook unless generating or rebuilding planning artifacts.
- For chapter work, prefer `context-packet.md`, the chapter draft, and the chapter `scene-breakdown.md`.
- If a large source must be used, summarize the relevant section before drafting.
- Context validation comes before style repair.
- Style repair comes before length expansion.
- Length expansion never justifies padding, fixed beat/scene word counts, or unsupported invention.

## Stop Conditions

Stop and ask or report `BLOCKED` when:

- source files are missing
- the packet has `UNKNOWN` for a fact that blocks drafting
- validator failures repeat on the same chapter
- manuscript is above the target maximum and trimming would affect story
