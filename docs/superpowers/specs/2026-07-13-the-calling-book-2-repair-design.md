# The Calling Book 2 Repair Design

## Goal

Repair `books/the-calling/book-2` into a continuity-consistent, style-locked
final manuscript while preserving its existing central story: Duke finds and
rescues Emily, returns home, receives Creed's offer, and begins the Las Vegas
doctor assignment under the Bishop threat.

## Scope

This repair covers all fifteen chapter drafts, the compiled manuscript, and
the final DOCX export. It includes verified continuity contradictions,
duplicate/merged-draft material, implausible action logic, and the broader
Western prose style cleanup identified by the project validators.

It does not create new plotlines, major characters, historical claims, or
unapproved backstory. It does not treat missing planning artifacts as prose
repair work; those workflow files are tracked separately.

## Source Authority

Use sources in this order when a repair decision is needed:

1. The user's current request and explicit preservation constraints.
2. `books/the-calling/book-2/phase-0.md`.
3. `books/the-calling/book-2/rulebook.md`.
4. The chapter draft, its `scene-breakdown.md`, and neighboring
   `continuity-out.md` files.
5. The verified issue report and the compiled manuscript as evidence of what
   must be reconciled, not as authority to invent new facts.

## Repair Architecture

### Pass 1: Structural and continuity repair

Repair contradictions before any line-level polish. Resolve the ring timeline,
the duplicated Purgatoire crossing, waystation route logic, Chapter 9 tactical
assignment, Ruth's contradictory death accounts, Duke's alias/birth-name
conflict, the unsupported mission death, the altered mother's letter, the
Chapter 14–15 competing endings, Clara's travel and ring state, and the
unbelievable cliff escape.

For every change, preserve the chapter's approved movement and update the
affected `continuity-out.md` file so the next chapter inherits one clear state.

### Pass 2: Sequential prose and style repair

Repair Chapters 1 through 15 in order, using a fresh chapter context packet.
Remove duplicate beats and copy-paste prose. Replace thought-over-behavior
explanation, banned AI echo words, modern or clinical wording, excessive
metaphor/personification, unwanted dialogue tags, and repetitive sentence
openers where they occur. Preserve POV, dialogue intent, action order, and
source-supported facts.

### Pass 3: Compilation and evidence gates

Compile from the repaired chapter sources only. Verify that the compiled
Markdown and DOCX contain the same normalized manuscript text, all fifteen
chapters appear once and in order, and no rejected ending material remains.
Run context, continuity, narrative-quality, banned-word, chapter-gap, and
length checks. Report workflow metadata failures separately from prose and
continuity findings.

## Verified Repair Inventory

- Chapter 1: ring appears before Clara gives it; thought-heavy opening.
- Chapter 2: repeated Ruth/fire warning.
- Chapter 3: duplicate Purgatoire crossing.
- Chapters 5–6: waystation route contradiction.
- Chapter 9: reversed diversion assignment.
- Chapters 10–12: revise the cliff escape and its injury aftermath into a
  physically credible, source-compatible escape.
- Chapters 12 and 14: reconcile Ruth's death and Duke's name history.
- Chapter 13: remove or source the invented mission-girl death; retain one
  coherent ring state.
- Chapters 14–15: select one Santa Fe/Creed sequence, one Clara travel state,
  one mother-letter quotation, and one route into Las Vegas.
- Chapters 1–15: perform the ordered style pass and update continuity outputs.

## Acceptance Criteria

- Every verified issue has a documented repair location and a source-supported
  resolution.
- The manuscript contains one Purgatoire crossing, one Ruth death account,
  one Duke identity explanation, one mother-letter wording, and one Santa Fe /
  Creed sequence.
- Clara's ring possession and location remain consistent from Chapter 1
  through Chapter 15.
- The final escape sequence has survivable mechanics and injuries carried
  through subsequent chapters.
- The compilation contains each chapter once, in order, with no stale merged
  material.
- Validator outputs distinguish missing workflow artifacts from remaining
  manuscript defects.

## Out of Scope

- Changing the story's central premise or series setup.
- Adding unsupported historical weapon, medical, or geographic detail.
- Repairing unrelated books or untracked Book 3 material.
- Committing, pushing, or publishing the work.
