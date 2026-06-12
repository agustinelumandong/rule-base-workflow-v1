# Prompt Modes

Choose one mode before loading context. The mode controls which files should be read and what kind of output is allowed.

## Modes

- `planning`: create or refresh rulebook, mood lock, chapter summaries, scene breakdowns, or drafting plans.
- `drafting`: write or expand scene/chapter prose from a context packet and approved scene breakdown.
- `repair`: fix validator, loop, source-drift, continuity, or beat-coverage issues only.
- `style`: apply Western style and humanizer cleanup without changing story facts.
- `validation`: compare draft against source files, rulebook, chapter summary, and scene breakdown.
- `expansion`: deepen approved beats after validation passes, without adding unsupported story.
- `final`: final whole-book read, compilation, or cross-chapter review.

## Mode Rules

- Planning can load broad source files.
- Drafting should load `context-packet.md`, `scene-breakdown.md`, and the chapter draft only.
- Repair should target the flagged chapter, line, beat, or continuity field.
- Style should preserve plot facts, POV, paragraph coverage, and Western tone.
- Validation should report findings before edits.
- Expansion must happen after context validation and style scan.
- Final mode is the only normal mode that may load the full manuscript.

## Compressed Style Lock

Use this short style lock in active prompts unless a full style pass is required:

```text
Literal Western prose; no AI echo words; no modern/clinical terms; no dialogue tags when action anchors are requested; behavior over thought; source-locked.
```

Load the full Western style references only for major drafting, style repair, final polish, or when the compressed lock is not enough to resolve a style issue.

## Agent Checkpoint

End every pass with:

```md
## Agent Checkpoint

- **Source Used:**
- **Mode:**
- **Changes Made:**
- **Risks:**
- **Next Action:**
- **Stop/Continue:**
```

The autonomous loop uses this as the human-readable handoff between cycles.
