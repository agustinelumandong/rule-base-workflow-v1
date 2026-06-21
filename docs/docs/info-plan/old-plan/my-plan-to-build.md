# AI Book Generation & Humanization Pipeline

## Canonical Project Brief

---

# 1. Project Overview

## 1.1 What This Project Is

This project is an automated AI-assisted book production pipeline designed to help the team produce more books per week without collapsing quality, consistency, or review capacity.

The original business goal is aggressive:

> Produce at least 5 books per week.

The current manual or semi-manual AI workflow cannot reliably hit that quota because books are long, context-heavy, and quality degrades when large manuscripts are processed carelessly.

The project is not simply “ask AI to write a book.” The actual target system is a structured production pipeline that can take a story concept, chapter summaries, character information, tone rules, and editorial instructions, then generate or rewrite book-length content in a controlled, reviewable, scalable way.

The intended output is polished, natural-sounding storybooks that feel conversational, coherent, and Western/American in phrasing, dialogue, pacing, and tone.

---

## 1.2 Core Vision

The vision is to build a repeatable factory-style pipeline for book creation and book editing.

The pipeline should:

1. Take a story idea, summary, or AI-assisted manuscript.
2. Break it into manageable sections.
3. Maintain story continuity across chapters.
4. Rewrite or expand content into natural, human-quality prose.
5. Detect inconsistencies, hallucinations, tone drift, and continuity errors.
6. Show differences between versions using a git-style diff.
7. Allow human reviewers to approve, reject, or revise outputs.
8. Store project memory per story so the AI does not confuse one book or story universe with another.
9. Scale from one book to many books per week.

The long-term goal is not just automation. The goal is **controlled automation**.

Quality, context discipline, reviewability, and scalability matter more than raw generation speed.

---

## 1.3 Intended Workflow

The simplified workflow discussed is:

```text
Upload story material / summary / manuscript
        ↓
Pipeline processes the book
        ↓
Human review
        ↓
Final output
```

But internally, the pipeline should be more detailed:

```text
Story intake
        ↓
Story bible creation
        ↓
Chapter planning
        ↓
Chapter-by-chapter generation or rewriting
        ↓
Continuity validation
        ↓
Style/humanization pass
        ↓
Dialogue and Western phrasing pass
        ↓
Diff review
        ↓
Human editor review
        ↓
Final manuscript export
```

---

# 2. Ideas & Concepts Gathered

## 2.1 Summary-to-Book Expansion

A major clarification was that the input may not always be a full manuscript.

Instead, the team may receive:

* A story summary.
* Hero details.
* Antagonist details.
* Supporting characters.
* World/background details.
* Chapter summaries.
* Tone requirements.
* Target word count.

From there, the pipeline should expand the material into a full book.

Example target structure:

```text
Length: Approximately 40,000 words

20 chapters total
~2,000 words per chapter

Chapters 1–6:  ~12,000 words
Chapters 7–14: ~16,000 words
Chapters 15–20: ~12,000 words
```

This means the pipeline must support both:

1. **Rewrite mode** — input is an existing manuscript.
2. **Expansion mode** — input is a structured summary and chapter outline.

These are different workflows and should not be treated the same.

---

## 2.2 Story Bible

A recurring idea is the need for a persistent story memory file.

This should not be the AI’s vague memory. It should be an explicit structured document stored inside the project folder.

The story bible should include:

* Title.
* Genre.
* Target reader.
* POV.
* Tense.
* Tone.
* Setting.
* Main character profiles.
* Antagonist profile.
* Relationship map.
* Character motivations.
* Character secrets.
* Timeline.
* World rules.
* Important locations.
* Naming conventions.
* Recurring themes.
* Forbidden contradictions.
* Style requirements.
* Dialogue rules.

The story bible becomes the source of truth for every generation or rewrite pass.

Without a story bible, the AI will eventually forget or distort details.

---

## 2.3 Chapter Summaries

Each chapter should have its own structured summary.

A chapter summary should include:

* Chapter number.
* Chapter title.
* Purpose of the chapter.
* Main events.
* Emotional arc.
* Character changes.
* New facts introduced.
* Continuity dependencies from earlier chapters.
* Foreshadowing for later chapters.
* Required scene beats.
* Ending hook.
* Approximate target word count.

For a 20-chapter book, this means the pipeline does not generate blindly. It generates against a blueprint.

---

## 2.4 Hierarchical Book Planning

The book should be managed at multiple levels:

```text
Book level
    ↓
Act level
    ↓
Chapter level
    ↓
Scene level
    ↓
Paragraph / prose level
```

This is critical because a full book cannot be controlled reliably from one prompt.

A good pipeline separates planning from prose generation.

The system should first understand the whole story, then plan chapters, then generate or rewrite each chapter, then validate continuity.

---

## 2.5 “Each Chapter as a Book” Concern

One important clarification was that in some cases, each “chapter” may behave like its own book or major installment, while still belonging to the same larger story universe.

Example structure discussed:

```text
Story: Life of Rizal/
    1st-book-or-chapter/
        context
        characters
        POV
        chapter material
    2nd-book-or-chapter/
        context
        characters
        POV
        chapter material
```

This means the system needs project-level memory and sub-book/chapter-level memory.

The AI should not rely on remembering things from previous runs. The repo/folder structure should provide the memory.

---

## 2.6 Per-Story Folder / Repo Structure

The project should be organized like a local repository.

Example:

```text
stories/
    life-of-rizal/
        story_bible.md
        style_guide.md
        characters.yaml
        timeline.yaml
        glossary.md
        outline.md
        chapters/
            chapter-01/
                input.md
                plan.md
                draft.md
                revised.md
                final.md
                diff.md
                review_notes.md
            chapter-02/
                input.md
                plan.md
                draft.md
                revised.md
                final.md
                diff.md
                review_notes.md
        memory/
            chapter_summaries.md
            continuity_log.md
            unresolved_questions.md
        outputs/
            book_v1.md
            book_v1.docx
            book_v1.pdf
```

This solves several issues:

* Prevents cross-story contamination.
* Makes every output auditable.
* Allows version control.
* Enables git diff.
* Makes the project easier to debug.
* Allows one story to be run independently.
* Supports scaling across many stories.

---

## 2.7 Git Diff for Manuscripts

A key idea discussed was using a git-style diff system to show what changed between manuscript versions.

This is valuable because human reviewers need to know:

* What the AI changed.
* Whether meaning was preserved.
* Whether new hallucinated content was inserted.
* Whether character details were altered.
* Whether dialogue was improved or damaged.
* Whether tone was made more natural.
* Whether important details were removed.

The system should support diffs between:

```text
original.md → rewritten.md
draft.md → revised.md
revised.md → final.md
chapter_v1.md → chapter_v2.md
```

Recommended diff types:

1. **Line-level diff** — useful for technical review.
2. **Paragraph-level diff** — better for prose.
3. **Semantic diff** — highlights meaning-level changes.
4. **Change summary** — AI-generated explanation of what changed.
5. **Risk flags** — warnings where meaning may have shifted.

---

## 2.8 Humanization / Naturalization Pass

The project includes a humanization stage, but it should be defined properly.

The goal is not merely to “hide AI writing.” The responsible and practical goal is:

> Improve prose so it sounds natural, varied, emotionally grounded, and appropriate for the target audience.

This includes:

* Less generic phrasing.
* More natural dialogue.
* Better sentence rhythm.
* Fewer repetitive transitions.
* Less over-explaining.
* More grounded emotion.
* Stronger scene texture.
* Western/American conversational phrasing when required.
* Reduced robotic symmetry.
* Less formulaic paragraph structure.
* Better idioms and casual speech patterns.

The humanization pass should preserve:

* Plot facts.
* Character intent.
* Timeline.
* POV.
* Chapter purpose.
* Genre expectations.

It should not randomly rewrite story logic.

---

## 2.9 Western Tone / Dialogue Style Rules

The team specifically discussed a Western or American conversational tone.

This should become a style guide, not just a vague prompt.

The style guide should define:

* How characters speak.
* Level of casualness.
* Whether contractions are preferred.
* Whether slang is allowed.
* How much profanity is allowed.
* Dialogue pacing.
* Emotional restraint vs. melodrama.
* Idioms to use sparingly.
* Phrases to avoid.
* Overused AI-like constructions to avoid.

Example rules:

```text
Prefer:
“I don’t know what you want from me.”

Avoid:
“I am uncertain as to what it is you desire from me.”

Prefer:
“She looked away before he could answer.”

Avoid:
“She averted her gaze, her emotions swirling like a tempest.”
```

The style guide should be used by every rewrite/generation pass.

---

## 2.10 Skills.md / Agent.md / Rules-Based Prompting

Another idea was to use modern agent-style project files such as:

* `AGENTS.md`
* `skills.md`
* `style_guide.md`
* `workflow.md`
* `rules.md`
* `editorial_policy.md`

These files act like operating instructions for the AI.

This approach is similar to an agentic development workflow where the AI reads project-level instructions before performing a task.

For this project, useful skill files could include:

```text
skills/
    western_dialogue.md
    chapter_expansion.md
    continuity_checking.md
    hallucination_detection.md
    prose_humanization.md
    line_editing.md
    developmental_editing.md
    summary_generation.md
    diff_review.md
```

Each skill file should define:

* Purpose.
* Inputs.
* Outputs.
* Rules.
* Examples.
* Failure modes.
* Validation checklist.

This makes the system more reusable and less dependent on one massive prompt.

---

## 2.11 Agentic Workflow

The project does not need “agents” for everything, but an agentic workflow can help when the task naturally separates into roles.

Possible specialized agents/modules:

1. **Intake Agent**
   Reads uploaded material and extracts structure.

2. **Story Architect Agent**
   Builds story bible, outline, and chapter plans.

3. **Chapter Writer Agent**
   Expands chapter summaries into prose.

4. **Humanization Agent**
   Rewrites prose for naturalness and Western tone.

5. **Continuity Agent**
   Checks facts, timeline, character consistency, and contradictions.

6. **Diff Agent**
   Compares versions and summarizes changes.

7. **QA Agent**
   Runs final validation against acceptance criteria.

8. **Reviewer Assistant Agent**
   Presents changes to the human editor.

The recommendation is to keep these as pipeline modules rather than autonomous uncontrolled agents.

In other words:

> Use agentic structure, but keep deterministic orchestration.

The system should not let agents freely run forever or make hidden decisions.

---

## 2.12 Visualization / Pipeline Dashboard

The team discussed wanting visual tracking similar to tools that show who or what is working now.

The desired dashboard should show:

* Which story is running.
* Which chapter is being processed.
* Which stage each chapter is in.
* Which model handled each stage.
* Which files were produced.
* Which checks passed or failed.
* Which chapters need human review.
* Current queue status.
* Error logs.
* Token/cost usage.
* Throughput per book.

Example visual flow:

```text
Story: Life of Rizal

Chapter 01  [Generated] → [Humanized] → [QA Passed] → [Reviewed]
Chapter 02  [Generated] → [Humanized] → [QA Failed] → [Needs Fix]
Chapter 03  [In Progress]
Chapter 04  [Queued]
```

This is not cosmetic. It becomes operational infrastructure once the team is running many books.

---

## 2.13 Tools Discussed

Several tools or tool categories were mentioned as possible inspiration:

* `lean-ctx`
* `archon`
* `obsidian-mind`
* `mempalace`
* `ADK`
* `graphify`
* Routa-like visual pipeline concepts
* Git-style version control
* Local LLM serving with llama.cpp
* NVIDIA model playground / free development APIs
* Local models
* Cloud models
* Vector databases
* RAG-style retrieval
* Knowledge graph / memory graph tools

These tools should not be blindly adopted.

The practical recommendation is:

> Borrow ideas from these tools, but build the first version around a simple repo-based pipeline with explicit files, repeatable steps, logs, diffs, and human review.

Complex agent frameworks should come later only if the simpler pipeline becomes limiting.

---

# 3. Problems & Challenges Identified

## 3.1 Context Window Overload

Large books can be 10,000 to 120,000+ words.

Dumping the full book into one prompt causes:

* Token overflow.
* Expensive calls.
* Slow generation.
* Lost details.
* Lower quality output.
* Contradictions.
* Repetition.
* Hallucination.
* Weak endings.
* Style drift.
* Chapter inconsistency.

Even if a model supports a very large context window, quality often degrades when the prompt becomes too large and unfocused.

The problem is not just “can the model fit the text?”

The real problem is:

> Can the model reliably use the right parts of the text at the right time without confusing itself?

Usually, the answer is no if the whole book is dumped into one prompt.

---

## 3.2 Hallucination

Hallucination risks include:

* Inventing new plot events.
* Changing character backstories.
* Adding unsupported facts.
* Rewriting motivations incorrectly.
* Creating timeline contradictions.
* Changing names or relationships.
* Forgetting previous chapter events.
* Misinterpreting a summary.
* Over-expanding a scene beyond the outline.
* Adding culturally inappropriate idioms.
* Adding facts that were never provided.

For fiction, hallucination does not always mean “factually false.” It often means “not supported by the established story canon.”

---

## 3.3 Continuity Drift

Across a long book, the AI may drift on:

* Character personality.
* Relationships.
* Emotional stakes.
* Locations.
* Timeline.
* Tone.
* POV.
* Tense.
* Genre.
* Naming.
* Magic/system rules, if applicable.
* Character goals.
* Unresolved plot threads.

This is one of the biggest risks in chapter-by-chapter generation.

---

## 3.4 Tone Inconsistency

Different chapters may sound like they were written by different writers.

This can happen when:

* Different models are used.
* Prompts vary too much.
* Chapter summaries differ in quality.
* Context is missing.
* Style guide is not enforced.
* Humanization is done inconsistently.
* The AI overfits to local chapter tone and forgets book-level tone.

---

## 3.5 Over-Automation Risk

Trying to fully automate the entire book pipeline too early is dangerous.

Risks:

* Poor outputs at scale.
* Hidden errors.
* Reviewers overwhelmed by bad drafts.
* No audit trail.
* No ability to identify which step failed.
* Inconsistent quality.
* Expensive reruns.
* Loss of trust from stakeholders.

The system should automate the repetitive work while keeping humans in the approval loop.

---

## 3.6 Cost and Speed

The team wants high throughput.

Problems:

* High-tier models are expensive.
* Local models are cheaper but may be weaker.
* Long context calls are costly.
* Rewriting full chapters repeatedly can multiply cost.
* Multiple QA passes add cost.
* Manual review time can become the bottleneck.
* Local hardware has VRAM limits.

The system needs a tiered model strategy and smart routing.

---

## 3.7 Local Hardware Constraints

The user has discussed local inference with an RTX 4060 8 GB VRAM, 32 GB RAM, and llama.cpp.

A tested configuration included Qwen3-Coder-30B-A3B-Instruct-GGUF with llama.cpp, reaching roughly 19–20 tokens/sec under the given setup.

This shows local generation is possible, but there are constraints:

* 8 GB VRAM is limiting.
* Quantized models are necessary.
* Larger models may be slow or partially offloaded.
* Long context reduces speed.
* Local models may be good enough for drafts, checks, summaries, and mechanical editing, but not always best for final creative quality.

---

## 3.8 Model Quality Uncertainty

The team asked whether to use:

* OpenAI.
* Google.
* Grok.
* Chinese/open models such as DeepSeek, MiniMax, Kimi, GLM, Qwen.
* Local models.
* NVIDIA-hosted free/development models.

The core concern is:

> Which model is good enough for long-form book generation and humanization without costing too much?

The answer is not one model. It should be a model routing strategy.

---

## 3.9 Review Bottleneck

Even if generation is automated, final quality depends on human review.

If the system produces too much unstructured output, humans become the bottleneck.

The pipeline must make review easier through:

* Diffs.
* Change summaries.
* QA flags.
* Continuity reports.
* Chapter status.
* Risk scoring.
* Side-by-side review.

---

## 3.10 Cross-Story Contamination

If the system handles many stories, it must not mix context between them.

Risks:

* Character names from another book appearing.
* Tone rules leaking between projects.
* Previous story bible influencing a new story.
* Memory contamination.
* Wrong genre assumptions.

This is why per-story folders and explicit context loading are important.

---

# 4. Proposed Solutions

## 4.1 Use a Pipeline, Not One Giant Prompt

The core solution is to replace the “one huge prompt” approach with a staged pipeline.

Recommended stages:

```text
1. Intake
2. Story bible extraction / creation
3. Outline validation
4. Chapter planning
5. Scene planning
6. Draft generation or rewrite
7. Humanization pass
8. Continuity check
9. Style check
10. Diff generation
11. Human review
12. Final assembly
```

Each stage should have:

* Clear input.
* Clear output.
* Clear rules.
* Validation criteria.
* Logs.
* Versioned files.

---

## 4.2 Use Explicit Project Memory

Instead of relying on model memory, every story gets persistent files.

Minimum memory files:

```text
story_bible.md
characters.yaml
timeline.yaml
style_guide.md
outline.md
chapter_summaries.md
continuity_log.md
```

These files are loaded selectively into prompts depending on the current task.

This prevents the AI from needing the full book in context every time.

---

## 4.3 Use Chunking

Books should be split into chapters and scenes.

Preferred chunking hierarchy:

```text
Book
    → Acts
        → Chapters
            → Scenes
                → Paragraph groups
```

For generation, the best unit is usually the scene or chapter.

For rewriting, the best unit may be:

* Scene-level for quality.
* Chapter-level for flow.
* Paragraph-level for line editing.

The pipeline should avoid processing random token chunks because fiction depends on scene structure.

---

## 4.4 Use Hierarchical Summaries

Every completed chapter should produce a summary.

The system should maintain:

1. Book summary.
2. Act summaries.
3. Chapter summaries.
4. Scene summaries.
5. Character state updates.
6. Timeline updates.
7. Open plot threads.
8. Resolved plot threads.

This allows later chapters to reference previous material without loading the entire manuscript.

---

## 4.5 Use Sliding Context Windows

When generating or rewriting Chapter 12, the model should not only see Chapter 12.

It should receive:

* Book-level story bible.
* Style guide.
* Chapter 12 plan.
* Summary of Chapters 1–11.
* Full text or summary of Chapter 11.
* Summary or plan of Chapter 13.
* Relevant character states.
* Relevant unresolved plot threads.

This creates a sliding window around the current chapter.

Example:

```text
Global context:
- Story bible
- Character sheet
- Style guide

Previous context:
- Summary of all prior chapters
- Full or partial previous chapter

Current context:
- Current chapter plan
- Current scene input

Forward context:
- Next chapter summary
- Future plot constraints
```

This reduces overload while preserving continuity.

---

## 4.6 Use RAG Selectively

The team asked whether RAG is involved.

The answer:

> RAG can be useful, but it should not be the core mechanism for generating a novel.

For fiction, structured memory is often more important than generic vector retrieval.

RAG is useful for:

* Retrieving relevant previous scenes.
* Finding all mentions of a character.
* Checking location descriptions.
* Looking up prior dialogue patterns.
* Finding unresolved plot threads.
* Pulling canon facts from the story bible.
* Searching long manuscripts during QA.

But RAG alone is not enough because semantic retrieval can miss important constraints.

Recommended approach:

```text
Primary memory: structured story bible, timeline, chapter summaries
Secondary memory: retrieval/search over manuscript chunks
Tertiary memory: knowledge graph for character/location relationships
```

RAG should support the pipeline, not replace planning.

---

## 4.7 Use Git-Style Version Control

Every major output should be versioned.

Example:

```text
chapter-03/input.md
chapter-03/draft_v1.md
chapter-03/humanized_v1.md
chapter-03/qa_fixed_v1.md
chapter-03/final.md
```

Git or git-like tracking allows:

* Rollback.
* Comparison.
* Audit.
* Review.
* Branching.
* Experimentation with different models/prompts.

This is especially important when testing model quality.

---

## 4.8 Use Human Review Checkpoints

The recommended production flow is not fully autonomous.

Human review should happen at key points:

1. After story bible generation.
2. After outline creation.
3. After sample chapter generation.
4. After full chapter draft.
5. After QA flags.
6. Before final export.

The most important checkpoint is early sample validation.

Before generating 40,000 words, the team should approve:

* Tone.
* POV.
* pacing.
* dialogue style.
* chapter structure.
* character interpretation.

This prevents expensive large-scale rework.

---

# 5. Context Overload Prevention

## 5.1 Core Principle

The pipeline should never send the whole book unless absolutely necessary.

Instead:

> Send only the smallest context package required to complete the current task correctly.

This is the single most important design principle.

---

## 5.2 Context Package Design

Each AI call should receive a structured context package.

Example:

```text
SYSTEM:
You are editing Chapter 7 of this book. Follow the style guide and preserve canon.

PROJECT CONTEXT:
- Story premise
- Genre
- POV
- Tone
- Target audience

CANON:
- Character facts
- Timeline facts
- Current emotional states
- Forbidden contradictions

PRIOR SUMMARY:
- Chapters 1–6 summarized

CURRENT TASK:
- Rewrite Chapter 7 for natural Western prose

CURRENT INPUT:
- Chapter 7 draft

OUTPUT FORMAT:
- Revised Chapter 7
- Change summary
- Continuity risks
```

This is much better than dumping 200 pages into one prompt.

---

## 5.3 Context Layers

Use context layers:

### Layer 1: Global Context

Always available:

* Story bible.
* Style guide.
* Character sheet.
* Genre rules.

### Layer 2: Progress Context

Updated as the book progresses:

* Chapter summaries.
* Timeline.
* Character state.
* Open threads.
* Resolved threads.

### Layer 3: Local Context

Specific to the current task:

* Current chapter.
* Current scene.
* Previous scene.
* Next scene.
* Specific rewrite instructions.

### Layer 4: Retrieved Context

Pulled only when needed:

* Similar prior scenes.
* Previous mentions of a location.
* Previous character dialogue.
* Timeline references.
* Canon facts.

---

## 5.4 Summarization Strategy

The system should summarize after each completed unit.

After each scene:

```text
Scene summary
Character changes
New facts introduced
Open questions
Continuity dependencies
```

After each chapter:

```text
Chapter summary
Plot advancement
Emotional arc
Character state updates
Timeline changes
New canon facts
Foreshadowing
Unresolved threads
```

After each act:

```text
Act summary
Major turning points
Character arcs
World state
Setup/payoff tracking
```

This creates a compressed memory that can be safely reused.

---

## 5.5 Sliding Window Strategy

For each chapter generation, include:

```text
Book bible
Style guide
Character states
Current chapter plan
Previous chapter summary or full previous chapter
Next chapter summary
Relevant retrieved canon
```

Avoid including all previous chapters unless the task specifically requires it.

---

## 5.6 Avoid Random Token Chunking

The system should not split manuscripts every 4,000 tokens blindly.

Bad:

```text
chunk_001.txt
chunk_002.txt
chunk_003.txt
```

Better:

```text
chapter_01_scene_01.md
chapter_01_scene_02.md
chapter_01_scene_03.md
```

Fiction depends on story units. Chunk by meaning, not by token count alone.

---

# 6. AI Hallucination Detection & Prevention

## 6.1 Define Hallucination for This Project

In this project, hallucination means:

> The model introduces, changes, or removes story facts without support from the approved canon, outline, or source material.

Examples:

* Changing a character’s age.
* Adding a sibling who never existed.
* Moving a scene to a new city without approval.
* Changing the antagonist’s motive.
* Killing a character too early.
* Resolving a plot thread that should remain open.
* Adding unsupported historical facts.
* Changing the tone or genre.

---

## 6.2 Prevention Techniques

### 6.2.1 Ground Every Generation in Canon

Every generation prompt should include:

* Relevant story bible sections.
* Current chapter plan.
* Character states.
* Timeline constraints.
* Forbidden changes.

The model should be explicitly told:

```text
Do not invent new canon.
Do not change character facts.
Do not resolve unresolved plot threads unless instructed.
Flag missing information instead of inventing.
```

---

### 6.2.2 Use Structured Outputs

After each generation, require the model to output a report:

```text
Generated text
Canon facts used
New facts introduced
Potential continuity risks
Questions for human review
```

This helps detect hidden changes.

---

### 6.2.3 Use Continuity Checker Pass

After a chapter is generated or rewritten, run a separate check:

```text
Input:
- Story bible
- Timeline
- Character sheet
- Chapter output

Task:
- Identify contradictions
- Identify unsupported new facts
- Identify changed relationships
- Identify timeline issues
- Identify tone violations
```

The checker should not be the same prompt as the writer. Ideally, it is a separate model call or even a different model.

---

### 6.2.4 Use Diff-Based Review

The diff system should flag:

* Added facts.
* Removed facts.
* Name changes.
* Location changes.
* Relationship changes.
* Timeline changes.
* Major semantic changes.
* Unexplained scene additions.

This makes hallucinations easier to catch.

---

### 6.2.5 Use Human Review for Canon Changes

Any new canon fact should require approval.

Example:

```text
New fact introduced:
Maria used to live in Chicago.

Status:
Needs approval.
```

The pipeline should maintain an approval log.

---

### 6.2.6 Use a Continuity Log

The continuity log should track:

* Important events.
* Character injuries.
* Promises.
* Secrets.
* Objects.
* Location changes.
* Relationship changes.
* Unresolved questions.
* Future payoffs.

This log becomes a QA source.

---

### 6.2.7 Use “No Invention” Modes

Some steps should be conservative.

For example, rewrite/humanization should not invent new plot.

Prompt rule:

```text
You may improve wording, rhythm, dialogue naturalness, and emotional clarity.
You may not add new events, characters, locations, backstory, or plot resolutions.
```

Expansion mode can invent more, but only within the approved chapter plan.

---

## 6.3 Detection Layers

Recommended hallucination detection stack:

```text
Layer 1: Prompt constraints
Layer 2: Structured canon files
Layer 3: Post-output self-report
Layer 4: Separate continuity checker
Layer 5: Diff analysis
Layer 6: Human review checkpoint
Layer 7: Final manuscript consistency scan
```

No single layer is enough.

---

# 7. Model Selection

## 7.1 Core Recommendation

The project should not depend on one model.

Use a tiered model strategy:

```text
Local / cheap models:
- Summaries
- Drafts
- QA checks
- formatting
- diff summaries
- metadata extraction
- low-risk rewrites

High-quality cloud models:
- final prose pass
- difficult chapters
- emotional scenes
- style calibration
- complex continuity fixes
- premium outputs
```

This gives the best balance of cost, quality, and speed.

---

## 7.2 Model Selection Criteria

Models should be judged by:

1. **Prose quality**
   Can it write natural long-form fiction?

2. **Instruction following**
   Does it obey constraints?

3. **Context handling**
   Can it use structured context accurately?

4. **Cost**
   Can the team afford many calls per book?

5. **Speed**
   Can it support weekly throughput?

6. **Local deployability**
   Can it run on available hardware?

7. **Long-context reliability**
   Does quality degrade badly with longer prompts?

8. **Editing ability**
   Can it preserve meaning while improving style?

9. **Consistency**
   Does it maintain voice and story facts?

10. **Tool compatibility**
    Can it work with local orchestration, JSON outputs, and validation?

---

## 7.3 Local Model Role

Local models are valuable for:

* Development.
* Experimentation.
* Cheap iteration.
* Summarization.
* Pre-processing.
* Draft generation.
* QA checks.
* Diff explanation.
* Style linting.
* Metadata extraction.

Given the user’s hardware constraints, local models should be used strategically, not expected to carry every final-quality writing task.

The local setup already tested Qwen3-Coder-30B-A3B-Instruct-GGUF through llama.cpp with good speed for a large quantized model. That is promising for pipeline tasks, although coder-tuned models may not always be the best final fiction prose models.

---

## 7.4 Cloud Model Role

Higher-tier models should be used where quality matters most:

* Final chapter polish.
* Complex emotional scenes.
* Dialogue refinement.
* High-stakes continuity repair.
* Full-book style unification.
* Sample chapter approval.
* Difficult rewrites.

The practical strategy is:

> Use cheap/local models to produce and inspect. Use premium models to refine the parts that matter most.

---

## 7.5 Candidate Model Categories

The team discussed or considered:

### Local / Open Models

* Qwen-family models.
* DeepSeek-family models.
* GLM-family models.
* Kimi-style models.
* MiniMax-style models.
* Llama-family models.
* Gemma-family models.
* Quantized GGUF models through llama.cpp.

### Hosted / API Models

* OpenAI models.
* Google models.
* Grok models.
* NVIDIA-hosted development models.
* Other low-cost hosted inference providers.

The model decision should be based on testing, not hype.

---

## 7.6 Recommended Model Testing Plan

Before committing, test models using the same benchmark tasks:

### Test 1: Chapter Expansion

Input:

```text
Story bible + chapter summary
```

Output:

```text
2,000-word chapter
```

Evaluate:

* Plot obedience.
* Natural prose.
* Dialogue quality.
* Pacing.
* No unsupported inventions.

### Test 2: Humanization

Input:

```text
AI-sounding chapter draft
```

Output:

```text
Natural Western-style rewrite
```

Evaluate:

* Meaning preservation.
* Less robotic tone.
* Better rhythm.
* No plot changes.

### Test 3: Continuity Check

Input:

```text
Story bible + generated chapter
```

Output:

```text
List of contradictions and risks
```

Evaluate:

* Catch rate.
* False positives.
* Specificity.

### Test 4: Diff Explanation

Input:

```text
Original + rewritten chapter
```

Output:

```text
Change summary and risk flags
```

Evaluate:

* Accuracy.
* Usefulness for editors.

### Test 5: Cost/Speed

Measure:

* Tokens/sec.
* Cost per chapter.
* Cost per book.
* Rerun cost.
* Failure rate.

---

## 7.7 Practical Model Routing

Recommended routing:

```text
Story bible extraction:
Local or mid-tier cloud

Chapter planning:
Local or mid-tier cloud

First draft generation:
Local if quality is acceptable; otherwise mid-tier cloud

Humanization:
Mid-tier or high-tier model

Continuity checking:
Local + high-tier spot checks

Final polish:
High-tier model for approved chapters only

Diff summaries:
Local model

Dashboard metadata:
Local model or deterministic scripts
```

---

# 8. Optimization Strategy

## 8.1 Prompt Engineering

Prompts should be modular.

Instead of one giant prompt, use reusable templates:

```text
prompts/
    create_story_bible.md
    expand_chapter.md
    rewrite_humanized.md
    check_continuity.md
    summarize_chapter.md
    generate_diff_summary.md
    final_polish.md
```

Each prompt should include:

* Role.
* Input contract.
* Output contract.
* Rules.
* Constraints.
* Examples.
* Validation checklist.

---

## 8.2 Use Acceptance Criteria

Every stage should have pass/fail criteria.

Example for chapter generation:

```text
Chapter passes if:
- 1,800–2,200 words
- Follows chapter plan
- No new unapproved characters
- Maintains POV
- Maintains tense
- Advances plot
- Ends with intended hook
- Dialogue sounds natural
- No unresolved formatting issues
```

Example for humanization:

```text
Rewrite passes if:
- Meaning preserved
- No unsupported plot changes
- More natural sentence rhythm
- Dialogue improved
- AI-like repetition reduced
- Tone matches style guide
```

---

## 8.3 Use Iteration Loops Carefully

The system should support revision loops, but with limits.

Bad:

```text
Keep improving until perfect.
```

Better:

```text
Run maximum 2 automatic revision passes.
If still failing, send to human review.
```

This prevents runaway cost and endless AI self-editing.

---

## 8.4 Use Quality Gates

Recommended quality gates:

```text
Gate 1: Story bible approved
Gate 2: Outline approved
Gate 3: Sample chapter approved
Gate 4: Chapter draft passes structure check
Gate 5: Humanized chapter passes meaning preservation check
Gate 6: Continuity checker passes
Gate 7: Human editor approves
Gate 8: Final manuscript consistency scan passes
```

---

## 8.5 Cost Reduction

Cost can be reduced by:

* Using local models for low-risk tasks.
* Caching summaries and context files.
* Avoiding full-book prompts.
* Reusing story bible and style guide.
* Only rerunning failed sections.
* Running QA before expensive final polish.
* Using smaller models for extraction and classification.
* Using premium models only for final or difficult tasks.
* Measuring cost per chapter and cost per book.

---

## 8.6 Speed Optimization

Speed can be improved by:

* Processing independent chapters in parallel after outline approval.
* Processing scenes independently where possible.
* Running QA checks asynchronously within the local pipeline.
* Avoiding unnecessary long context.
* Using local inference for batch checks.
* Caching model outputs.
* Keeping prompts short and structured.
* Using deterministic scripts where AI is not needed.

---

## 8.7 Output Validation

Use both AI and non-AI validation.

Non-AI checks:

* Word count.
* Chapter count.
* File existence.
* Markdown structure.
* Duplicate chapter titles.
* Name consistency.
* Basic regex checks.
* Diff size.
* Repeated phrases.
* Formatting.
* Missing sections.

AI checks:

* Tone consistency.
* Continuity.
* Character behavior.
* Plot coherence.
* Meaning preservation.
* Dialogue naturalness.

---

## 8.8 Prompt Versioning

Prompts should be versioned like code.

Example:

```text
prompts/rewrite_humanized_v1.md
prompts/rewrite_humanized_v2.md
prompts/rewrite_humanized_v3.md
```

Each output should record:

```text
model: qwen-local
prompt_version: rewrite_humanized_v2
temperature: 0.7
date: 2026-06-07
input_file: chapter-03/draft.md
output_file: chapter-03/humanized.md
```

This makes failures traceable.

---

## 8.9 Evaluation Dataset

The team should create a small internal benchmark set.

Minimum benchmark:

```text
3 story bibles
5 chapter summaries
5 AI-sounding drafts
5 expected humanized examples
5 continuity-error examples
```

Use this to compare models before scaling.

---

# 9. Scalability Plan

## 9.1 Scalable Architecture

The system should be modular.

Recommended architecture:

```text
Frontend / Dashboard
        ↓
Pipeline Orchestrator
        ↓
Job Queue
        ↓
Worker Modules
        ↓
Model Router
        ↓
Storage / Repo / Database
        ↓
Review Interface
```

---

## 9.2 Modular Pipeline

Each module should do one job.

```text
modules/
    intake/
    story_bible/
    outline/
    chapter_planner/
    generator/
    humanizer/
    continuity_checker/
    diff_engine/
    reviewer/
    exporter/
```

This allows the team to improve one part without rewriting the whole system.

---

## 9.3 Job Queue

To scale beyond one book at a time, use a queue.

Each chapter or scene can become a job:

```text
job_id: story-001-chapter-07-humanize
status: running
model: local-qwen
input: chapter-07/draft.md
output: chapter-07/humanized.md
```

Job states:

```text
queued
running
completed
failed
needs_review
approved
rejected
```

---

## 9.4 Parallelization

The system can parallelize carefully.

Safe to parallelize:

* Summarization.
* Style checks.
* Diff generation.
* QA checks.
* Independent chapter rewrites after story bible approval.
* Metadata extraction.

Be careful parallelizing:

* First draft generation for chapters with heavy dependencies.
* Later chapters before earlier canon is approved.
* Major plot turns.
* Final continuity-sensitive revisions.

Recommended approach:

```text
Plan globally.
Generate locally.
Validate globally.
```

---

## 9.5 Scaling Production

To hit 5 books per week, the team needs throughput metrics.

Track:

* Average time per chapter.
* Average review time per chapter.
* Cost per chapter.
* Number of failed generations.
* Number of revision loops.
* Human approval rate.
* Final defect rate.
* Model performance by task.

The bottleneck will probably shift over time:

```text
Early stage bottleneck: generation quality
Middle stage bottleneck: human review
Later stage bottleneck: orchestration and QA
```

---

## 9.6 Local First vs Hosted

The recommended strategy:

### Start Local-First for Development

Use local models and local files to prototype cheaply.

Benefits:

* Low cost.
* Full control.
* Easy experimentation.
* No dependency on hosted APIs.
* Good for prompt and pipeline development.

### Add Hosted Models for Quality

Use cloud models for high-value steps.

Benefits:

* Better prose.
* Better instruction following.
* Stronger final polish.
* Better difficult-scene handling.

### Move to Hybrid Production

Final architecture should support both:

```text
local model workers
cloud model workers
manual review workers
```

The model router decides which model to use for which task.

---

## 9.7 Future Multi-User System

In the future, the system may support multiple users or editors.

Needed features:

* User accounts.
* Story ownership.
* Review assignments.
* Comment threads.
* Approval status.
* Role permissions.
* Audit logs.
* Version history.
* Export controls.

This is not required for the first version, but the architecture should not block it.

---

# 10. Any Other Key Points

## 10.1 MVP Recommendation

Do not start by building a huge agent platform.

The best MVP is:

```text
Local repo-based pipeline
+ story folder structure
+ prompt templates
+ chapter-by-chapter processing
+ summaries
+ continuity log
+ git diff
+ human review checklist
```

This is enough to prove the workflow.

---

## 10.2 Recommended MVP Flow

```text
1. Create story folder
2. Add story summary, characters, and chapter summaries
3. Generate story bible
4. Human approves story bible
5. Generate Chapter 1 sample
6. Human approves tone
7. Generate chapters 1–20
8. Summarize each chapter
9. Run humanization pass
10. Run continuity check
11. Generate diffs
12. Human reviews flagged chapters
13. Assemble final manuscript
```

---

## 10.3 Suggested File Structure

```text
book-pipeline/
    stories/
        story-name/
            config.yaml
            story_bible.md
            style_guide.md
            outline.md
            characters.yaml
            timeline.yaml
            continuity_log.md
            chapters/
                chapter-01/
                    input.md
                    plan.md
                    draft.md
                    humanized.md
                    qa_report.md
                    diff.md
                    final.md
                chapter-02/
                    input.md
                    plan.md
                    draft.md
                    humanized.md
                    qa_report.md
                    diff.md
                    final.md
            memory/
                chapter_summaries.md
                open_threads.md
                canon_updates.md
            exports/
                final.md
                final.docx
                final.pdf
    prompts/
        create_story_bible.md
        expand_chapter.md
        humanize_chapter.md
        check_continuity.md
        summarize_chapter.md
        diff_summary.md
    skills/
        western_dialogue.md
        prose_humanization.md
        continuity_checking.md
        chapter_expansion.md
    scripts/
        run_pipeline.py
        generate_diff.py
        assemble_book.py
        validate_outputs.py
```

---

## 10.4 Recommended Technology Stack

For MVP:

```text
Language:
Python

Storage:
Local folders + Git

Pipeline:
Simple Python orchestration first

Models:
llama.cpp local server + optional cloud APIs

Diff:
git diff, difflib, or semantic diff layer

Dashboard:
Start with CLI or simple web UI
Later: FastAPI + React or Next.js

Metadata:
YAML / JSON

Exports:
Markdown → DOCX / PDF
```

For later production:

```text
Queue:
Redis Queue, Celery, or similar

Database:
PostgreSQL

Vector search:
pgvector, Qdrant, Weaviate, or similar

Object storage:
S3-compatible storage

Dashboard:
Full web app

Auth:
Role-based access

Observability:
logs, metrics, traces, cost tracking
```

---

## 10.5 What Should Not Be Built Yet

Avoid overbuilding early.

Do not start with:

* Complex autonomous multi-agent systems.
* Heavy knowledge graphs.
* Full SaaS dashboard.
* Overcomplicated memory architecture.
* Fine-tuning before prompt/pipeline testing.
* Fully automated publishing.
* Complex RAG before structured memory works.
* Multiple model providers before benchmarks exist.

Build the boring reliable system first.

---

## 10.6 Key Operating Principle

The pipeline should behave like a production editorial system, not a chatbot.

That means:

```text
Every input is saved.
Every output is saved.
Every change is diffed.
Every model call is logged.
Every canon change is reviewed.
Every chapter has status.
Every final output is reproducible.
```

This is what makes the system scalable.

---

# 11. Final Recommended Direction

## 11.1 Strategic Recommendation

The best path is a hybrid, repo-based, modular AI book pipeline.

Use:

* Structured story files for memory.
* Chapter/scene chunking for context control.
* Summaries for compression.
* Selective RAG for retrieval.
* Git-style diff for review.
* Local models for cheap processing.
* Cloud models for premium quality.
* Human checkpoints for canon and final approval.
* Dashboard later, after the file-based workflow works.

---

## 11.2 Immediate Next Steps

### Step 1: Define the MVP Input Format

Create a standard intake template:

```text
title:
genre:
target_audience:
tone:
pov:
tense:
word_count:
main_character:
antagonist:
supporting_characters:
setting:
story_summary:
chapter_summaries:
style_requirements:
forbidden_content:
```

---

### Step 2: Build the Folder Structure

Create the per-story repo/folder layout.

---

### Step 3: Create Core Prompt Templates

Start with:

```text
create_story_bible.md
expand_chapter.md
humanize_chapter.md
check_continuity.md
summarize_chapter.md
generate_diff_summary.md
```

---

### Step 4: Run One Book Manually Through the Pipeline

Do not automate everything immediately.

Run one 20-chapter / 40,000-word book through the process and track:

* Time.
* Cost.
* Quality.
* Failure points.
* Review effort.
* Model performance.

---

### Step 5: Automate Repetitive Steps

Automate only after the manual pipeline is proven.

First automate:

* File creation.
* Prompt assembly.
* Model calls.
* Output saving.
* Diff generation.
* Word count checks.
* QA report generation.

---

### Step 6: Add Dashboard

Only after the pipeline works from CLI/files, add a dashboard for:

* Story status.
* Chapter status.
* Worker status.
* Review status.
* Cost.
* Errors.
* Diffs.

---

# 12. Executive Summary

This project is not just about generating books faster.

It is about building a controlled AI editorial production system that can generate, rewrite, humanize, validate, and review long-form books at scale.

The winning architecture is not one giant prompt and not a chaotic swarm of agents.

The winning architecture is:

```text
Structured files
+ modular pipeline
+ context discipline
+ model routing
+ validation layers
+ human review
+ version control
```

The first milestone should be a working local/hybrid MVP that can take one story summary with 20 chapter summaries and produce a 40,000-word draft with reviewable diffs, continuity reports, and final export.

Once that works reliably, scaling to more books becomes an operations problem instead of a guessing game.

---

**Prompt: AI-Powered Long-Form Story Writing System**

You are an agent-native AI story writer and co-author. Your purpose is to expand chapter summaries into full, publication-ready prose while remaining strictly faithful to the source material — never hallucinating, never going off-context, and never over-writing.

---

**Phase 1 — Intake & Identification**

When I send you a Story Bible or chapter summaries, you will:
- Identify and catalog all characters (name, role, traits, relationships)
- Extract all settings (locations, time periods, atmosphere)
- Map the plot structure (arcs, turning points, themes)
- Index every detail into a structured knowledge base

This becomes your single source of truth. You never invent facts that aren't in it.

---

**Phase 2 — Word Count Planning**

Before writing, you will receive or calculate a word count target per chapter. Example:

> Total target: 40,000 words → Ch. 1–6: ~12,000 words | Ch. 7–8: ~14,000 words | etc.

You will distribute words proportionally based on chapter weight and story pacing. Confirm the breakdown with me before writing begins.

---

**Phase 3 — Expansion Rules**

When expanding each chapter, follow these rules strictly:

1. **Stay on-summary.** Every paragraph must trace back to the chapter summary. Do not add subplots, characters, or events that aren't in the source material.
2. **Carry forward context.** Begin each chapter with a brief internal recap of what happened before (used for your own coherence check, not necessarily printed). This prevents drift across long sessions.
3. **Three-layer memory:**
   - *Session history* — what's been written this session
   - *Knowledge base* — the indexed Bible/summary
   - *Learning state* — style and tone calibrations set by me
4. **No hallucination policy.** If something is unclear in the summary, flag it and ask — don't fill in the gap creatively.

---

**Phase 4 — Voice & Style**

Write in a humanized, Western-natural prose style:

- Use **simple, direct language.** If a sentence sounds too literary or ornate, rewrite it plainly.
- Use **natural contractions and informal speech patterns** where appropriate — e.g., *"em"* instead of *"them,"* *"gonna"* instead of *"going to,"* in dialogue and inner monologue.
- Avoid purple prose, over-metaphoring, and flowery descriptions.
- The tone should feel like a skilled storyteller talking to you — not a writing competition entry.

---

**Phase 5 — QA Loop**

After each chapter draft, run an internal quality check before delivering output:

- [ ] Does every scene/event appear in the source summary?
- [ ] Are character names, traits, and relationships consistent with the Bible?
- [ ] Is the word count within ±5% of the target?
- [ ] Is the prose free of over-creative or hallucinated content?
- [ ] Does the chapter ending set up the next one correctly?

Flag any failures and self-correct before output.

---

**Phase 6 — Co-Writing Workspace (Optional)**

If I highlight or paste a specific passage, you can:
- **Revise** — fix tone, clarity, or accuracy
- **Expand** — add detail while staying on-summary
- **Shorten** — trim without losing key beats
- **Ground** — cross-check the passage against the knowledge base and correct any drift

---

**How to send me work:**

1. Send the full Bible or summary first → I will index it
2. Confirm character/setting/plot breakdown with you
3. Agree on word count plan
4. Expand chapter by chapter, running QA after each

Ready to receive your Story Bible.

---

This prompt is clean, structured, and gives an AI system everything it needs to behave like a disciplined co-author rather than a creative free agent. Want me to also turn this into a working artifact — like an interactive app where you can paste your Bible and have it walk through each phase?
