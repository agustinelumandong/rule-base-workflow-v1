# The Calling Book 2 Final Continuity and Export Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the final reader-reported chronology, animal, time, factual, and export-title defects in Book 2, then regenerate matching Markdown and DOCX outputs.

**Architecture:** Repair chapter sources and their companion continuity artifacts before compiling. Treat Chapter 8 as the bridge between Murdock's information and the stronghold entry; move only the premature planning scene from Chapter 7, without changing the established Chapter 9 diversion. Establish explicit post-ambush animal inventory and a single captivity timeline, then validate against all later chapters before export.

**Tech Stack:** Markdown chapter sources, BookForge compiler functions, `python-docx`, `pandoc` text extraction, manuscript context scripts, `rg`, and `unittest` compiler tests.

## Global Constraints

- Scope: `books/the-calling/book-2/`, BookForge compiler/title tests only when needed for the title-page defect, and this plan.
- Preserve the approved central story, the Chapter 9 east-side diversion/north-wall culvert entry, and all prior repair decisions.
- Keep third-limited Duke POV and literal Western prose; do not create new animals, travel, injuries, deaths, backstory, or a flashback.
- `report-issues-book-2.md` remains read-only audit evidence.
- Chapter drafts remain source of truth; never hand-edit generated output as a substitute for source repair.
- Do not commit, push, or publish without a separate user request.

---

## File Structure

- Modify: `books/the-calling/book-2/phase-0.md` — replace internal title-page heading with reader-facing series title, book title, and number used by the compiler.
- Modify: `books/the-calling/book-2/chapters/chapter-07/chapter-07.md` and companions — end at Murdock intelligence, not the already-completed stronghold camp plan.
- Modify: `books/the-calling/book-2/chapters/chapter-08/chapter-08.md` and companions — retain ambush, then place the dry-wash map/culvert/diversion plan after it.
- Modify: `books/the-calling/book-2/chapters/chapter-09` through `chapter-13` and companions — maintain a real animal inventory, coherent time references, correct Hecht attribution, Emily's knowledge, ring location, and copy facts.
- Modify: `books/the-calling/book-2/rulebook.md` and `chapter-summaries.md` — lock corrected chronology, animal state, and timeline.
- Modify only if title output requires it: `bookforge/core/compiler.py` and `tests/test_compile_manuscript.py`.
- Regenerate: compiled Markdown/DOCX and `compiled/validation-summary.md` after source repair.

## Task 1: Correct reader-facing title metadata and prove compiler rendering

**Files:** `books/the-calling/book-2/phase-0.md`, `books/the-calling/book-2/rulebook.md`, optionally `bookforge/core/compiler.py`, `tests/test_compile_manuscript.py`.

- [ ] Change the phase-0 first heading from the internal product-definition label to `# The Calling: A Search for Kin`, and add a separate `Book 002` metadata line in the exact form consumed by `read_book_metadata()`.
- [ ] Update any Book 2 title reference in the rulebook that would reintroduce the internal heading.
- [ ] Add/adjust a compiler regression test that asserts the DOCX title-page paragraphs are `The Calling`, `A Search for Kin`, and `Book 2` (or the agreed single-title rendering), never `Phase 0: Product Definition`.
- [ ] Compile a temporary DOCX with `compile_docx(..., include_title=True)`, extract the first-page text with Pandoc, and confirm it contains the reader-facing title and book number only.

## Task 2: Repair the Chapter 7–8 chronology without a flashback

**Files:** Chapter 07–08 drafts, `scene-breakdown.md`, `continuity-out.md`, `chapter-review.md`, `rulebook.md`, `chapter-summaries.md`.

- [ ] In Chapter 7, retain the ranch conversation and Murdock's culvert intelligence; remove the dry-wash camp, map, moon-down, and east-side-fire planning sequence that makes the men already adjacent to the stronghold.
- [ ] In Chapter 8, retain the "a day out from Murdock's ranch" ambush and Duke's bay's death; after the ambush and gear transfer, insert the preserved dry-wash/map/culvert/diversion planning sequence before the approach to Chapter 9.
- [ ] Update the Chapter 7 exit state to: Murdock has supplied the lead; Duke and Preacher are travelling toward stronghold country, not camped a mile from it. Update Chapter 8 exit state to: post-ambush, Preacher owns the east diversion and Duke owns the north-wall culvert.
- [ ] Run `check_continuity_chain.py`, then verify only Chapter 8 contains the final moon-down/culvert commitment and Chapter 9 begins after Preacher's fire.

## Task 3: Establish post-ambush animal inventory and repair rescue/mission continuity

**Files:** Chapter 08–11 drafts and companion artifacts; `rulebook.md`; `chapter-summaries.md`.

- [ ] Lock Chapter 8: Duke's bay dies; the pack mule survives and carries Duke's gear; Preacher retains his horse.
- [ ] At the Chapter 9 stronghold escape, establish two specific saddled horses taken from the stronghold: Preacher rides one; Duke rides one; Emily rides the surviving mule. Do not call Duke's replacement horse his mare or imply the bay survived.
- [ ] In Chapter 10, change the dead animal from "their mule" to one stolen stronghold horse, leaving the mule alive for Emily at the mission.
- [ ] Update continuity outputs, summaries, and ledger rows for Chapters 8–11 with the exact inventory and riders.
- [ ] Search `bay|mare|mule|dead horse|three riders` across Chapters 8–11 and manually verify every occurrence against the inventory.

## Task 4: Normalize captivity, relationship, and knowledge timeline

**Files:** Chapter 07, 09–13 drafts and companion artifacts; `rulebook.md`; `chapter-summaries.md`.

- [ ] Add one source-supported clarification that Emily was held for two years, moved to Vargas's canyon four months before the rescue, and tied to the chair in the final week. Do not repeat the entire explanation in later scenes.
- [ ] Replace the impossible "two months ago" canyon reference with the actual short post-rescue elapsed time.
- [ ] Replace the incorrect "twenty years" separation reference with twelve years.
- [ ] Replace Emily's claim that settlement women told her about Clara before arrival with a journey-grounded observation: Duke speaks of Clara and Preacher has told Emily enough to understand.
- [ ] Change Preacher's "Hecht told me" wording to an accurate attribution such as Duke telling him what Hecht once said, consistent with Hecht's Book 1 death.
- [ ] Update continuity artifacts and run focused searches for `two months|twenty years|asked about her at the settlement|Hecht told` plus the approved time values.

## Task 5: Resolve ring, weapon, emotional-beat, and grammar contradictions

**Files:** Chapter 02, 08, 11–13 drafts and companion artifacts; `rulebook.md`.

- [ ] Keep Clara's ring in Duke's coat pocket throughout the southbound journey; replace the saddlebag-storage claim in Chapter 12 and align companion artifacts.
- [ ] Select one established rifle designation for Preacher (Winchester or Henry), retain the historically sourced choice, and replace every conflicting reference.
- [ ] Change the later claim that Emily never cried to acknowledge that she cried when Duke found her; change any later "never heard her laugh" claim to preserve the earlier mission laugh.
- [ ] Correct `she had already chose something` to `she had already chosen something`.
- [ ] Run focused exact-text searches and inspect Chapter 13 against Chapters 9–11 to ensure later statements no longer negate earlier events.

## Task 6: Review, compile, compare, and promote final outputs

**Files:** all changed companion artifacts; `books/the-calling/book-2/compiled/book-2-final.md`; `books/the-calling/book-2/compiled/A-Search-for-Kin-Book-2-I-Passed.docx`; `compiled/validation-summary.md`.

- [ ] Build context packets and run focused context validation for each changed chapter; resolve source/continuity failures before compiling.
- [ ] Run `check_continuity_chain.py`, `check_chapter_gaps.py`, targeted contradiction searches, and `git diff --check`; record any configuration false positives separately from actual failures.
- [ ] Use the tested compiler functions to create temporary Markdown and DOCX from exactly 15 chapter drafts. Confirm the reader-facing title page, 15-draft count, and no duplicate DOCX chapter headings.
- [ ] Extract DOCX text with Pandoc; compare normalized prose against temporary Markdown while excluding Markdown-only `---` separators.
- [ ] Promote temporary outputs only if all source checks and cross-format comparison pass; write `validation-summary.md` with exact commands, pass/fail outcomes, and any remaining validator configuration caveats.

## Completion Checklist

- [x] The exported title page is reader-facing and contains no `Phase 0: Product Definition` text.
- [x] Chapter 8, not Chapter 7, owns the final post-ambush culvert/diversion planning scene.
- [x] The bay remains dead; the mule survives; every later rider and dead animal is accounted for.
- [x] Hecht, Emily's captivity, Duke/Emily's twelve-year separation, Clara knowledge, and ring storage are consistent.
- [x] Rifle naming, Emily's cry/laugh references, and grammar slip are corrected.
- [x] Compiled Markdown and DOCX are regenerated from 15 drafts and match after format-only normalization.
