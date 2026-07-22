# The Calling Book 2 Complete Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair `books/the-calling/book-2` into one internally consistent, style-locked manuscript and regenerate matching Markdown and DOCX outputs from its fifteen chapter drafts.

**Architecture:** Establish one explicit Book 2 continuity ledger in the rulebook before editing prose. Repair continuity and scene logic in chronological order, then run a source-locked style pass chapter by chapter. Rebuild planning metadata only after canon is stable, and compile only from the repaired chapter drafts; never patch generated files as a substitute for source repairs.

**Tech Stack:** Markdown chapter sources, existing BookForge compiler, `python-docx`, project manuscript workflow scripts, `rg`, and `pytest` for compiler regressions.

## Live Completion Status

- [x] Task 1 — repair authority established and reviewed.
- [x] Task 2 — Chapters 1–3 continuity repairs reviewed.
- [x] Task 3 — Chapters 4–9 route and rescue-entry repairs reviewed.
- [x] Task 4 — Chapters 10–13 consequence, identity, letter, and ring repairs reviewed.
- [x] Task 5 — Chapters 14–15 ending repairs reviewed.
- [x] Task 6 — metadata, continuity artifacts, and validator schema repairs reviewed.
- [x] Task 7 — Chapters 1–8 prose/style pass reviewed and approved.
- [x] Task 8 — Chapters 9–15 prose/style pass reviewed and approved.
- [x] Task 9 — final Markdown/DOCX compilation and verification reviewed and approved.

## Global Constraints

- Scope is only `books/the-calling/book-2/` and the new plan/design documents; do not touch Book 1 or untracked Book 3.
- Preserve the core story: Duke learns Emily is alive, travels with Preacher, rescues her, returns home, accepts Creed's Las Vegas doctor offer, and receives the Bishop threat.
- Do not invent plot, character history, medical facts, weapons, geography, or motives not supported by `phase-0.md`, `rulebook.md`, chapter material, or an explicitly recorded repair decision.
- Use third-limited Duke POV, literal Western prose, short direct dialogue, behavior over thought, and period-grounded vocabulary.
- Do not add institutional-villain, property-rights, water-rights, mineral-rights, business-conspiracy, or trial-story material.
- Do not pad scenes or impose scene word counts. Retain only prose that performs approved plot, character, setting, or transition work.
- Treat `report-issues-book-2.md` as read-only audit evidence. Do not alter it to make findings disappear.
- Keep generated compiled files out of the repair source of truth. Chapter drafts are canonical; regenerate compiled Markdown/DOCX only after source repair.
- Do not commit, push, or publish without a separate user request.

---

## File Structure

- Modify: `books/the-calling/book-2/rulebook.md` — add the source hierarchy, continuity ledger, explicit no-invention rules, character state, and workflow sections required for source-locked repair.
- Create: `books/the-calling/book-2/mood-lock.md` — concise, book-local Western style authority used in every repair packet.
- Create: `books/the-calling/book-2/chapter-summaries.md` — one source-supported purpose and exit state for each of the fifteen repaired chapters.
- Modify: `books/the-calling/book-2/chapters/chapter-01` through `chapter-15` — repair prose, scene breakdowns, and continuity outputs in chronological order.
- Create: `books/the-calling/book-2/chapters/chapter-XX/chapter-review.md` — one review record per chapter, following the existing validator decision format.
- Regenerate: `books/the-calling/book-2/compiled/book-2-final.md` and `books/the-calling/book-2/compiled/A-Search-for-Kin-Book-2-I-Passed.docx` — generated only from repaired chapter drafts.
- Modify: `books/the-calling/book-2/compiled/validation-summary.md` — replace the stale, contradictory summary with the actual final verification results.
- Preserve: `books/the-calling/book-2/report-issues-book-2.md` — immutable audit input.

## Canonical Repair Decisions

These decisions resolve the verified contradictions without changing the book's central plot. Record them in the rulebook before prose edits.

1. **Duke's identity:** Caleb Harlan is his birth name. Duke Rowan is the name he adopted after fleeing his past. Emily calls him Caleb in private; narration and public-facing scenes use Duke Rowan.
2. **Ruth:** A Trinidad sheriff murdered Ruth. Preacher hunted that sheriff for three years. Delete the later fever death account rather than replacing the earlier established history.
3. **Clara's ring:** Clara gives Duke her grandmother's gold ring before he rides south. Duke returns it to Clara in Chapter 13; from that moment Clara wears it. Duke must not possess it in Chapters 14–15.
4. **Waystation:** Duke and Preacher decide to scout it quietly, then do so in Chapter 6 before heading toward the stronghold. Remove language claiming they bypass it entirely.
5. **Escape:** Duke and Emily descend a survivable broken ledge/sand slope rather than jumping fifty to sixty feet. Duke carries a sore shoulder and strained knee; Emily has cuts, bruising, exhaustion, and no implausibly instant recovery.
6. **Mission:** No unnamed girl dies at the abandoned mission. Duke's Chapter 13 reflection concerns Emily's condition and his inability to save everyone in general, without claiming a nonexistent death.
7. **Mother's letter:** Its only quoted wording is: “My son, I know you are alive. I need you to know there is nothing you have done that cannot be forgiven. Be faithful to the man you are becoming.”
8. **Ending:** Chapter 14 contains the sole arrival in Santa Fe and the sole Creed offer. Clara travels with Duke, Emily, and Preacher. Chapter 15 begins after that decision and moves the group into Las Vegas; it must not re-stage Santa Fe, Creed's office, the offer, or the Bishop warning. Clara stays present in the Las Vegas transition and is never described as waiting back at the settlement.

## Task 1: Establish the repair baseline and enforce canon

**Files:**
- Modify: `books/the-calling/book-2/rulebook.md`
- Create: `books/the-calling/book-2/mood-lock.md`
- Create: `books/the-calling/book-2/chapter-summaries.md`
- Preserve: `books/the-calling/book-2/report-issues-book-2.md`

**Interfaces:**
- Consumes: the verified issue report, `phase-0.md`, all chapter drafts, and the current rulebook.
- Produces: one repair authority that later chapter work can follow without reopening resolved contradictions.

- [ ] **Step 1: Snapshot the current evidence without modifying it**

Run:

```bash
sha256sum books/the-calling/book-2/report-issues-book-2.md \
  books/the-calling/book-2/compiled/book-2-final.md \
  books/the-calling/book-2/compiled/A-Search-for-Kin-Book-2-I-Passed.docx
git status --short
```

Expected: hashes are recorded in the repair session notes; the issue report remains unchanged; pre-existing modified/untracked files remain visible and are not discarded.

- [ ] **Step 2: Add required repair authority to `rulebook.md`**

Add these sections, each with explicit Book 2 facts rather than placeholders:

```markdown
## Source Hierarchy

1. Current user-approved repair decisions.
2. This rulebook's Continuity Ledger.
3. phase-0.md for approved chapter purpose.
4. Chapter prose, scene breakdown, and adjacent continuity outputs.
5. report-issues-book-2.md as audit evidence only.

## Do Not Invent

- Do not add a second Ruth death, a second Santa Fe meeting, another mission death, or a second ring transfer.
- Do not change Duke's birth name, Clara's role, Emily's captivity/rescue, or Creed's one-year doctor offer.
- Do not add historical or medical facts beyond approved material.

## Length Handling Rules

- Repair for clarity, continuity, and style; never add filler to satisfy a count.
- Preserve necessary action, recovery, travel, and quiet humanizing beats.

## Unknowns

None. Stop and ask the user if a repair requires a new fact not covered by this rulebook.
```

Then add `## Characters` and `## Chapter Continuity Ledger` entries containing all eight canonical repair decisions above, with a Chapter 1–15 row that identifies Duke, Emily, Preacher, Clara, the ring, active injuries, location, and the required next-chapter state.

- [ ] **Step 3: Create the compact mood lock and chapter summaries**

Write `mood-lock.md` with: third-limited Duke POV; literal physical prose; no banned AI echo words; no modern/clinical language; short direct dialogue; behavior over thought; and source-locked action/injury tracking.

Write `chapter-summaries.md` with fifteen entries. Each entry must name the existing chapter's purpose, concrete event, ending state, ring state, and unresolved pressure. Do not copy the stale chapter names in `compiled/validation-summary.md`; derive the entries from the actual chapter drafts and approved continuity ledger.

- [ ] **Step 4: Run the baseline intake, gap, and authority validation**

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_source_format.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_gaps.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/the-calling/book-2
```

Expected: the source-format scan checks `phase-0.md` intake structure; chapter gaps remains `PASS`; and the context validator reports `rulebook.md`, `mood-lock.md`, and `chapter-summaries.md` present.

## Task 2: Repair Chapters 1–3 and lock the departure sequence

**Files:**
- Modify: `books/the-calling/book-2/chapters/chapter-01/chapter-01.md`
- Modify: `books/the-calling/book-2/chapters/chapter-02/chapter-02.md`
- Modify: `books/the-calling/book-2/chapters/chapter-03/chapter-03.md`
- Modify: their `scene-breakdown.md` and `continuity-out.md` files
- Create: their `chapter-review.md` files

**Interfaces:**
- Consumes: Task 1 ledger; Chapter 1 departure state; phase-0 Chapters 1–3.
- Produces: one clean Clara/ring transfer, one Ruth history, and one Purgatoire crossing.

- [ ] **Step 1: Repair Chapter 1's ring timing and opening narration**

Delete every ring reference before Clara physically hands Duke the cloth-wrapped ring. Keep the first ring reference immediately after that handoff. Trim the nearby repeated thought-summary material about his future, the knot in his chest, and what he might become; replace only where needed with action, dialogue, or a visible decision to ride south.

Update `continuity-out.md` to lock: Duke possesses Clara's wrapped ring; Clara remains at the settlement; the letter remains sealed; Duke and Preacher leave at dawn.

- [ ] **Step 2: Repair Chapter 2's Ruth dialogue without changing its established event**

Keep the sheriff-murder account and the three-year hunt. Reduce the repeated “fire in your chest / fed it for three years / will not bring your sister back faster” speech to one complete warning plus one short response beat. Do not introduce fever, a church burial, or a different town.

Update `continuity-out.md` to lock Ruth's murder as Preacher's only account and Duke's continued possession of the ring.

- [ ] **Step 3: Repair Chapter 3's duplicated Purgatoire movement**

Keep the first complete crossing: Preacher enters, Duke follows, both reach the far bank. Delete the second “Duke started across” paragraph. Preserve the border transition, Duke's concern that Emily may not recognize him, and the continuation into Chapter 4.

Update `continuity-out.md` to lock both men and the mule south of the Purgatoire, in New Mexico Territory, with no active injury from the crossing.

- [ ] **Step 4: Validate the repaired departure sequence**

Run:

```bash
for chapter in chapter-01 chapter-02 chapter-03; do
  python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py books/the-calling/book-2 --chapter "$chapter"
  python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/the-calling/book-2 --chapter "$chapter" --ai-prompt
done
rg -n -i 'fever took her|Ruth.*fever|Duke started across|ring in his pocket' \
  books/the-calling/book-2/chapters/chapter-{01,02,03}/chapter-*.md
```

Expected: no Ruth fever account; only one Purgatoire crossing remains; every pre-handoff ring occurrence is gone.

## Task 3: Repair Chapters 4–9 and make the search route coherent

**Files:**
- Modify: `books/the-calling/book-2/chapters/chapter-04` through `chapter-09` chapter drafts, scene breakdowns, and continuity outputs
- Create: `books/the-calling/book-2/chapters/chapter-04` through `chapter-09` chapter reviews

**Interfaces:**
- Consumes: Task 2 location/ring state and Task 1 canon ledger.
- Produces: a single route from border country to quiet waystation scouting, ranch intelligence, infiltration, and rescue preparation.

- [ ] **Step 1: Retain the Chapter 4–5 lead chain and remove only style duplication**

Keep the captured-raider lead, village healing, and the build toward the waystation. Cut repeated ring reminders, redundant internal summary, and filler transitions while preserving Duke's healer identity and Preacher's mentor role.

- [ ] **Step 2: Repair the Chapter 5–6 waystation contradiction**

Change the Chapter 5 departure logic to: they will not attack the waystation loudly; they will approach, scout it quietly, obtain information, and leave before Vargas understands their purpose. Remove any statement that says they are avoiding or bypassing the waystation entirely.

Ensure Chapter 6 begins with Duke and Preacher watching the same waystation from a ridge, then exiting toward the stronghold with new information. Update both continuity outputs with that exact route.

- [ ] **Step 3: Preserve Chapter 7–8 information flow and repair local prose**

Keep the ranch/stronghold intelligence, Murdock's warning, and the culvert plan. Remove copied ring lines and overexplained interior narration. Do not add a property-control conspiracy: Murdock's role remains personal/outlaw pressure within the approved story.

- [ ] **Step 4: Correct Chapter 9's tactical assignment**

Replace the reversed opening line with the established plan: Preacher creates the diversion at the east side; Duke enters through the north-wall culvert and has the agreed time window to reach Emily. Ensure later action follows those same positions and no line assigns Duke to draw attention outside while he crawls through the culvert.

- [ ] **Step 5: Validate the search route and tactical plan**

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_continuity_chain.py books/the-calling/book-2
rg -n -i 'not going to the waystation|avoiding the waystation|scout it quiet|draw them to the east|culvert|diversion' \
  books/the-calling/book-2/chapters/chapter-{05,06,07,08,09}/chapter-*.md
```

Expected: the route says quiet scouting, not bypass; Preacher owns the diversion; Duke owns the culvert entry.

## Task 4: Repair Chapters 10–13 and preserve credible rescue consequences

**Files:**
- Modify: `books/the-calling/book-2/chapters/chapter-10` through `chapter-13` chapter drafts, scene breakdowns, and continuity outputs
- Create: `books/the-calling/book-2/chapters/chapter-10` through `chapter-13` chapter reviews

**Interfaces:**
- Consumes: Task 3 rescue entry state, Task 1 identity/ring canon, and the established mission sequence.
- Produces: a survivable escape, consistent injury recovery, a single Duke identity explanation, a single Ruth history, and a coherent homecoming.

- [ ] **Step 1: Replace the fatal cliff jump with a survivable descent**

Keep the pursuit, the mesa edge, Preacher's covering fire, and the need for Duke and Emily to escape. Replace the fifty-to-sixty-foot free fall with a source-compatible descent through a broken lower ledge and steep sand slope. Keep Duke's shoulder and knee strain and Emily's cuts/bruising/exhaustion, then adjust later riding, treatment, and recovery language so neither character moves as though unhurt.

- [ ] **Step 2: Remove the unsupported mission-girl death**

In Chapter 13, remove the statement that a girl died at the mission. Replace it only with an existing supported reflection: Duke could not control every loss, Emily's condition frightened him, and healing has limits. Do not create a new named casualty to fill the gap.

- [ ] **Step 3: Fix Duke's name and Ruth's later account**

In the mission and return material, change the line that treats “Duke” as his mother's birth-name choice. Emily may call him Caleb and recognize the family name; narration retains Duke Rowan as the alias he lives under. Replace the later fever story of Ruth with the sheriff-murder account or remove the repeated history entirely.

- [ ] **Step 4: Complete the Chapter 13 ring return**

Show or clearly state Duke returning the ring to Clara. Once Clara places it on her finger, remove every later Duke possession reference. In `continuity-out.md`, lock: Clara wears the ring; Emily is home and recovering; Duke, Clara, Emily, and Preacher's departure state is ready for Creed's message.

- [ ] **Step 5: Validate injuries, identity, and ring state**

Run:

```bash
rg -n -i 'fifty feet|sixty feet|jumped|fell|Ruth.*fever|fever took her|She named you well.*Duke|girl.*mission|ring in his pocket' \
  books/the-calling/book-2/chapters/chapter-{10,11,12,13}/chapter-*.md
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_continuity_chain.py books/the-calling/book-2
```

Expected: no fatal-height jump, no mission-girl death, no Ruth fever account, no birth-name contradiction, and no Duke ring possession after Clara wears it.

## Task 5: Repair Chapters 14–15 into one ending sequence

**Files:**
- Modify: `books/the-calling/book-2/chapters/chapter-14/chapter-14.md`
- Modify: `books/the-calling/book-2/chapters/chapter-15/chapter-15.md`
- Modify: their scene breakdowns and continuity outputs
- Create: their chapter reviews

**Interfaces:**
- Consumes: Task 4's homecoming/ring state and Task 1's ending canon.
- Produces: one Santa Fe meeting, one Creed offer, one Bishop warning, and one unbroken move to Las Vegas.

- [ ] **Step 1: Keep Chapter 14 as the only Santa Fe / Creed scene**

Retain the Creed letter, Duke's choice to go to Santa Fe, the group travelling together, Creed's one-year Las Vegas doctor offer, and Creed's Bishop warning. Delete the altered quotation of the mother's letter and use only the canonical wording from Task 1. Keep Clara visibly present through the chapter's departure state and make it explicit that she carries/wears the returned ring.

- [ ] **Step 2: Rewrite Chapter 15's opening transition, not the story's outcome**

Delete the second Santa Fe arrival, second Creed office scene, repeated offer, repeated warning, and any line implying Clara stayed at the settlement. Begin after the accepted offer, on the road to or arrival in Las Vegas. Keep Duke, Clara, Emily, and Preacher physically accounted for; if Preacher departs, show the departure once and update the continuity output.

Keep the Las Vegas clinic start, Duke treating the injured boy, the rider's Bishop news, and Emily asking what Duke will do. Change any ring-in-pocket language to Clara's visible ring or to Duke thinking of her without taking possession of it.

- [ ] **Step 3: Finalize the ending continuity outputs**

Chapter 14 must lock: Creed's offer accepted; Bishop warning heard once; all four travel onward; Clara wears the ring. Chapter 15 must lock: Duke has begun the Las Vegas doctor role; Emily is safe; Clara's location is explicit; Preacher's location is explicit; Bishop is the unresolved Book 3 pressure.

- [ ] **Step 4: Verify the one-ending rule**

Run:

```bash
rg -n -i 'Santa Fe|Marshal Creed|Las Vegas|Bishop|ring in his pocket|Be the man I raised' \
  books/the-calling/book-2/chapters/chapter-{14,15}/chapter-*.md
```

Expected: one Santa Fe arrival, one Creed meeting, one offer, one Bishop warning, no Duke ring possession, and no altered mother-letter quotation.

## Task 6: Normalize scene breakdowns, continuity outputs, and chapter reviews

**Files:**
- Modify: `books/the-calling/book-2/chapters/chapter-01` through `chapter-15` `scene-breakdown.md` and `continuity-out.md`
- Create: `books/the-calling/book-2/chapters/chapter-01` through `chapter-15` `chapter-review.md`

**Interfaces:**
- Consumes: the repaired chapter text and the Task 1 ledger.
- Produces: validator-readable planning and review records that reflect the manuscript rather than stale or generic metadata.

- [ ] **Step 1: Rebuild each scene breakdown from the repaired chapter**

For every chapter, replace generic or malformed sections with the validator-supported structure:

```markdown
## BEAT 1: [short factual label]

### Source Context Lock

- [approved fact, current character/location/item state]

### Beat Instructions

- **Source Anchor:** [phase-0 or rulebook-supported chapter movement]
- **Required Story Movement:** [what this beat must accomplish]
- **Continuity In:** [what the chapter inherits]
- **Continuity Out:** [what the next beat/chapter must inherit]
- **Do Not Invent:** [specific prohibited additions]
```

Use 2–3 beats for quiet/travel chapters, 3–4 for investigation/infiltration chapters, and 4–6 only where the source provides distinct action stages. Do not manufacture beats to hit a number.

- [ ] **Step 2: Rewrite all `continuity-out.md` files using the required template**

Each output must contain non-empty `Characters`, `Locations`, `Changes`, `Human Stakes Carried`, `Unresolved Pressure`, and `Next Chapter Must Know` sections. Track the ring, Duke/Emily injuries, Preacher's location, Clara's location, travel state, and the Creed/Bishop chain where applicable.

- [ ] **Step 3: Create one chapter review per repaired chapter**

Each `chapter-review.md` records: source used, repair mode, continuity result, POV result, style result, remaining risks, and a `ready` decision only if the chapter has no unresolved source or continuity failure. Do not mark an unresolved fact ready.

- [ ] **Step 4: Run deterministic workflow checks**

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_continuity_chain.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_gaps.py books/the-calling/book-2
```

Expected: no missing mood lock, chapter summaries, chapter review, continuity-out sections, or scene-breakdown beat-structure failures. Remaining style findings are routed to Tasks 7–8.

## Task 7: Perform the ordered style repair for Chapters 1–8

**Files:**
- Modify: `books/the-calling/book-2/chapters/chapter-01` through `chapter-08` chapter drafts and reviews

**Interfaces:**
- Consumes: Tasks 1–6's locked continuity and scene structure.
- Produces: first-half chapters with the same approved events but cleaner literal Western prose.

- [ ] **Step 1: Repair one chapter at a time with a compact context packet**

For each chapter from `chapter-01` through `chapter-08`, run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/build_context_packet.py books/the-calling/book-2 --chapter chapter-XX
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_context_budget.py books/the-calling/book-2 --chapter chapter-XX --mode style
```

Replace `chapter-XX` with the active chapter. Read only that packet, the chapter prose, its breakdown, and its continuity output before editing.

- [ ] **Step 2: Apply the style lock without flattening the chapter**

For each chapter, remove or rewrite only flagged prose that is genuinely weak:

- thought-over-behavior explanation (`He felt`, `He thought`, `He realized`, or abstract summaries) when action, silence, work, or direct dialogue can carry the meaning;
- banned AI echo words and modern/clinical terms;
- unnecessary similes, metaphor, and personification;
- repeated sentence starts, repeated internal beats, and copied sentences;
- dialogue tags where an action anchor or clear exchange already identifies the speaker.

Keep necessary medical action, concrete emotional stakes, and source-supported quiet beats. Do not turn every sentence into the same clipped rhythm.

- [ ] **Step 3: Run a focused style scan after each chapter**

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_banned_words.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/the-calling/book-2 --chapter chapter-XX --ai-prompt
```

Expected: the active chapter's newly introduced warnings are zero; any remaining heuristic warnings are reviewed against the prose rather than blindly deleted.

## Task 8: Perform the ordered style repair for Chapters 9–15

**Files:**
- Modify: `books/the-calling/book-2/chapters/chapter-09` through `chapter-15` chapter drafts and reviews

**Interfaces:**
- Consumes: Tasks 1–7.
- Produces: a consistent rescue, aftermath, homecoming, and ending with no style regression.

- [ ] **Step 1: Repair Chapters 9–11 under action and recovery constraints**

Keep combat fast, clear, and grounded. Track who is firing, where Duke enters, what Preacher covers, where Emily is, and how injuries affect motion. Remove catalog-like weapon detail, abstract threat commentary, and repeated tactical explanation without obscuring physical cause and result.

- [ ] **Step 2: Repair Chapters 12–13 under recovery and homecoming constraints**

Keep the quiet humanizing beats between Duke and Emily, but remove repeated reflection loops. Preserve realistic fatigue and injury recovery. Keep the return, Clara's recognition, and the ring return concrete and sequential.

- [ ] **Step 3: Repair Chapters 14–15 under ending constraints**

Keep the moral choice, group travel, Las Vegas doctor work, and Bishop hook. Remove duplicate setup and narrative explanation that repeats what the reader already witnessed. Do not add a second antagonist plot or a new Book 3 premise.

- [ ] **Step 4: Run final narrative and style checks**

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_narrative_quality.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/scan_banned_words.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_continuity_chain.py books/the-calling/book-2
```

Expected: no unresolved continuity chain problem; no direct contradiction with the Task 1 ledger; remaining style notes are explicit editorial choices, not overlooked errors.

## Task 9: Regenerate and verify the final manuscript outputs

**Files:**
- Regenerate: `books/the-calling/book-2/compiled/book-2-final.md`
- Regenerate: `books/the-calling/book-2/compiled/A-Search-for-Kin-Book-2-I-Passed.docx`
- Modify: `books/the-calling/book-2/compiled/validation-summary.md`

**Interfaces:**
- Consumes: only repaired chapter drafts and Task 6's review records.
- Produces: matching final Markdown/DOCX artifacts and a truthful validation summary.

- [ ] **Step 1: Compile fresh Markdown and DOCX to temporary outputs**

Run:

```bash
python bookforge/core/compiler.py books/the-calling/book-2 \
  --format markdown \
  --output /tmp/the-calling-book-2-final.md
python bookforge/core/compiler.py books/the-calling/book-2 \
  --format docx \
  --output /tmp/A-Search-for-Kin-Book-2-I-Passed.docx
```

Expected: each report says `Draft Files Compiled: 15`; no source chapter is omitted.

- [ ] **Step 2: Compare both generated formats before promoting them**

Run:

```bash
pandoc /tmp/A-Search-for-Kin-Book-2-I-Passed.docx -t plain -o /tmp/the-calling-book-2.docx.txt
python - <<'PY'
from pathlib import Path
import re

markdown = Path('/tmp/the-calling-book-2-final.md').read_text(encoding='utf-8')
docx_text = Path('/tmp/the-calling-book-2.docx.txt').read_text(encoding='utf-8')

def normalize(text: str) -> str:
    text = text.replace('# ', '')
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('—', '--').replace('–', '-')
    return re.sub(r'\s+', ' ', text).strip()

assert normalize(markdown) == normalize(docx_text), 'Markdown and DOCX text differ'
print('PASS: normalized Markdown and DOCX text match')
PY
```

Expected: `PASS: normalized Markdown and DOCX text match`.

- [ ] **Step 3: Run final contradiction searches against the temporary Markdown**

Run:

```bash
rg -n -i 'Ruth.*fever|fever took her|girl.*mission|Be the man I raised|ring in his pocket|Duke started across|not going to the waystation' /tmp/the-calling-book-2-final.md
rg -n '^Chapter [0-9]+:' /tmp/the-calling-book-2-final.md
```

Expected: the contradiction search returns no matches; the heading search returns exactly fifteen chapter headings in numerical order.

- [ ] **Step 4: Promote verified outputs and write an honest validation summary**

Replace the current final Markdown/DOCX only after Steps 1–3 pass. Update `compiled/validation-summary.md` with the actual compile date, 15 compiled chapters, validation commands used, unresolved warnings if any, and no claim that missing reviews passed.

- [ ] **Step 5: Run final project verification and inspect the diff**

Run:

```bash
python .agents/skills/manuscript-workflow-orchestrator/scripts/validate_manuscript_context.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_narrative_quality.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_continuity_chain.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_chapter_gaps.py books/the-calling/book-2
python .agents/skills/manuscript-workflow-orchestrator/scripts/check_manuscript_length.py books/the-calling/book-2
git diff --check
git status --short
```

Expected: any remaining warnings are documented as deliberate editorial review items; no unresolved continuity contradiction, generated-format mismatch, missing required workflow artifact, or whitespace error remains.

## Acceptance Checklist

- [ ] All 13 verified report issues are resolved in chapter sources, not merely hidden in compiled output.
- [ ] All 15 chapters have valid scene breakdowns, continuity outputs, and chapter reviews.
- [ ] The rulebook names one source hierarchy and one continuity state for Ruth, Duke, Clara's ring, the waystation, the mission, and the ending.
- [ ] The book has one Purgatoire crossing, one Santa Fe/Creed meeting, one Creed offer, and one Bishop warning.
- [ ] Clara's ring possession and physical location are consistent through Chapter 15.
- [ ] Duke and Emily's escape and later movement reflect believable injuries and recovery.
- [ ] The prose is literal, source-locked, period-aware, and no longer dominated by repetitive internal explanation.
- [ ] Markdown and DOCX are regenerated from the repaired chapter drafts and match after normalization.
- [ ] `validation-summary.md` reports actual checks and outcomes.
- [ ] No unrelated book, report evidence file, or pre-existing user change is overwritten.

## Plan Self-Review

- **Coverage:** Tasks 1–6 cover canonical repair and validator artifacts; Tasks 7–8 cover all fifteen chapter style passes; Task 9 covers compilation and final proof.
- **No placeholders:** Every chapter range, canonical decision, file path, command, and completion check is specified.
- **Scope:** The plan repairs only Book 2 and its generated outputs. Book 3, Book 1, commits, and unrelated migration work remain out of scope.
