# Outline Repair Report

| Issue | Fix Type | Original Snippet | Corrected Snippet | Confidence | Action Needed |
| --- | --- | --- | --- | --- | --- |
| Canonical title carried working-copy label in reference outline | Heading normalization | `# Book One: Whispering Ash - outline 2` | `# Book One: Whispering Ash` | High | None |
| Book-level target could be misread from first chapter target if no manuscript target exists | Lossless metadata insertion | No book-level target section present in `copy-phase-0.md` | Added `## Book Target` with `Approximate Manuscript Target: 54,800 words total from the source outline.` | High | Human may confirm whether 54,800 remains the desired advisory target |
| Drafting guardrails from review context were not structurally captured in the short outline form | Lossless note insertion | Global style note only | Added second `[!NOTE]` preserving no-romance, behavior-over-explanation, and independence guardrails | High | None |
| Chapter 7 used direct emotional/mental phrasing that conflicted with the included behavioral note | Structural safety normalization with preserved intent | `Kills in combat but flashes back to his own family.` and `Return with spoils but deep guilt.` | `Killing in combat physically brings back pressure from his own family loss.` and `Return with spoils, with guilt shown through behavior instead of explanation.` | Medium | Confirm wording if the exact original phrases must remain verbatim |
| Chapter 7 escape-preparation line used direct calculation language while adjacent note requested physical behavior | Structural safety normalization with preserved intent | `Jake calculates surviving alone if he runs.` | `Jake begins preparing for survival alone if he runs.` | Medium | Confirm wording if exact original phrasing must remain verbatim |
| Chapter 12 lacked explicit core goal in reference form | Required field completion from existing content | Chapter 12 started at `Target` and `Scene Beats` | Added `Core Goal: Test Jake against settlement contact and show him reject easy return.` | High | None |
| Anna Ray role label implied romance in Book One | Character-role correction from review context | `Anna Ray (Romantic Interest: Introduced late Book One)` and `Sparks interest and human connection.` | `Anna Ray (Trading-Post Widow: Introduced late Book One)` and `Brief human connection and pull toward white society, but no romance begins in Book One.` | High | None |
| Several chapters lacked explicit anti-invention constraints | Guardrail insertion | No `Do Not Invent` line in reference outline | Added chapter-local `Do Not Invent` lines to preserve source boundaries | High | None |
| Smart punctuation differed between pasted reference and normalized file | Markdown normalization | Curly quotes and apostrophes in copied text | Straight quotes and apostrophes in normalized file | High | None |

## Ambiguous Items Preserved For Review

| Issue | Fix Type | Original Snippet | Corrected Snippet | Confidence | Action Needed |
| --- | --- | --- | --- | --- | --- |
| Local threat in Chapter 11 remained unspecified | Frontier-logic cleanup | `mutual rescue from a local threat` | Resolved as a flash-flood or river-accident sequence | High | None |
| Rival warrior in Chapter 8 remains unnamed | Reviewer flag preserved | `rival warrior` | Preserved and protected by `Do Not Invent` | High | Name only if later rulebook or drafting requires it |
| Weaker captive in Chapter 2 remains unnamed | Reviewer flag preserved | `weaker captive` | Preserved and protected by `Do Not Invent` | High | Name only if user approves or a later artifact requires it |
