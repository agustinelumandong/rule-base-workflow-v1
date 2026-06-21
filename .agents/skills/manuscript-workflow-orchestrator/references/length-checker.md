# Length Checker

Use the length checker after drafting, expansion, compilation, or revision passes to measure progress toward the book-level target.

## Command

```bash
bf validate books/tex-cade
```

Length constraints are part of full validation. Replace `books/tex-cade` with the target book folder.

## Rules

- Treat the reported target as book-level planning guidance only.
- Never use the report to force fixed chapter, scene, or beat lengths.
- A short total is an expansion signal, not a reason to pad.
- Expand by revisiting approved scene breakdowns and adding source-supported action, consequence, conflict, dialogue, setting texture, and transition.
- Do not add unsupported events, names, motives, lore, or backstory to close the gap.

## Output

The checker reports:

- target words
- current words
- remaining words
- percent complete
- per-chapter draft counts
- average chapter count excluding epilogue
- warnings for under-target manuscripts
- warnings for chapters far below the current chapter average

The checker excludes planning files and counts only manuscript draft files under chapter folders.
