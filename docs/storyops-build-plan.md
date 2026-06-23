# StoryOps Build Plan — Connected to the Current BookForge System

> **Status:** Draft for review. Derived from `docs/storyops-engine-vs-bookforge.md`
> (P0–P3 MVP pipeline). Covers the four steps needed to prove the provider-web +
> patch workflow end-to-end. P4–P7 (research cache, generation queue, Project Kit,
> MCP) are deliberately deferred — they build *on top* of these four.

## Goal

Turn BookForge into a high-throughput scene-pipeline:

```
produce clean scene packet → provider web generates prose → patch only broken parts
```

Protect Codex/Antigravity quota by enforcing the operator-vs-generator lane. **No
greenfield rewrite** — every step extends existing modules at verified seams.

## User decisions (locked)

- **Guard mode:** advisory + log by default; a settings flag flips to hard-refuse.
- **Scene layout:** scenes nested inside the chapter folder
  (`changes/chapter-NN/scenes/sc-MM.manifest.yml`).

## Non-goals (explicitly deferred)

Research cache (P4), generation queue (P5), Project Kit (P6), MCP server (P7). Those are
the next milestones after this MVP is proven. This plan also makes no changes to canon
fold/apply, validators, or the loop controller beyond *reading their output*, and no
provider-web automation (paste/upload stays manual per the manual-first caution in the
mapping doc).

---

## Step P0 — Operator-Prose Guard (advisory + log)

**Protect quota first.** Codex/Antigravity become the **operator**, never the novelist.

**Files to touch:**
- `bookforge/core/persona.py` (extend `check_persona_capabilities`)
- `bookforge/core/validators/style.py` (extend `DEFAULT_SETTINGS`)
- `tests/test_persona.py` (new cases)

**Existing seam (verified):**
- `check_persona_capabilities(book_folder, persona_name, model, action, projected_input_tokens)`
  already computes projected output tokens (`projected_input_tokens // 4`) and enforces the
  global cap.
- It is currently only invoked by the standalone `bf check-persona` CLI — **not wired into the
  drafting loop.** The guard hook needs a new call site (added later as the scene packet path
  lands).

**Changes:**
1. Add a new top-level key to `DEFAULT_SETTINGS` in `validators/style.py`:
   ```python
   "operator_prose_guard": {
       "enabled": True,
       "mode": "advisory",          # "advisory" | "hard"
       "output_token_cap": 500,
       "operator_personas": ["extractor", "reviewer", "planner"],
       "prose_actions": ["draft", "draft_prose", "expand"],
   }
   ```
2. Extend `check_persona_capabilities` to accept optional `projected_output_tokens` and the
   settings dict, and add a guard branch:
   - **advisory mode** (default) → still return `(True, "AUTHORIZED (advisory guard warning logged): …")`
     but append a JSON line to a new `book_folder/state/guard-log.jsonl`
     (timestamp, persona, model, action, projected tokens, mode).
   - **hard mode** → return
     `(False, "REFUSED: operator persona <p> cannot draft_prose above N tokens; use the provider-web lane (bf packet --scene ...).")`
3. Threshold must be **configurable**, not a flat number — the operator path legitimately
   writes short prose fragments (splice glue), so 500 is a sane default the user can tune.

**Tests:**
- advisory mode returns `True` and writes a log line
- hard mode returns `False`
- cap is read from settings, not hardcoded
- non-operator persona + draft action is unaffected

**Acceptance:**
```bash
bf check-persona --persona extractor --model gpt-4o --action draft --projected-tokens 4000
# advisory mode: warning printed + guard-log.jsonl line written
# hard mode: refused with a "use the provider-web lane" hint
```

---

## Step P1 — Scene Manifests + Scene Addressing

**Generate by scene, not whole chapter.** Add the stable address that patches and the queue
will key off.

**Files to touch:**
- new `bookforge/core/scene.py`
- extend `bookforge/core/packet/helpers.py`
- new `bookforge/templates/scene-manifest.yml`
- new `tests/test_scene.py`

**Existing foundation (verified):**
- `bookforge/core/action.py:discover_combat_scenes()` already parses `## Scene N` headers and
  slugs them to `scene-N`.
- `bookforge/core/action.py:init_action_plan(chapter_folder, scene_id)` writes
  `action-plan-scene-N.json` keyed on `scene_id` — proves the per-scene file pattern.
- `bookforge/core/issue.py:50` `ManuscriptIssue` already has `chapter`, `file`, `line`,
  `span` fields (no `scene` field yet — added conceptually via the manifest).
- `bookforge/core/packet/helpers.py:91` `chapter_folder()` resolves `changes/<slug>` →
  `chapters/<slug>` — scene resolution mirrors this.

**Changes:**
1. New `bookforge/core/scene.py`:
   - `@dataclass SceneManifest` — fields: `scene_id`, `chapter`, `target_words`, `status`,
     `required_beats: list[str]`, `forbidden: list[str]`, `research_questions: list[str]`,
     `inputs: dict`, `packet_path`, `draft_path`, `validation_path`.
   - `manifest_path(chapter_folder, scene_id) -> Path` →
     `chapter_folder / "scenes" / f"{scene_id}.manifest.yml"` (nested layout).
   - `init_scene_manifest(chapter_folder, scene_id, target_words=3500)` — writes a template
     manifest (mirrors `init_action_plan`'s template pattern).
   - `load_scene_manifest(path) -> SceneManifest` and `save_scene_manifest(manifest)` — YAML
     round-trip via existing `yaml.safe_load` / `save_yaml_file` from `canon/io.py`.
   - `parse_scene_id(slug) -> tuple[str, str]` — split `chapter-08/scene-02` or `ch08_sc02`
     or bare `scene-02` (context-implied) into `(chapter_slug, scene_id)`.
   - `discover_scenes(chapter_folder) -> list[SceneManifest]` — glob `scenes/*.manifest.yml`.

2. Add to `helpers.py`:
   - `scene_folder(book_folder, chapter_slug, scene_id) -> Path` — resolves
     `changes/<chapter>/scenes/<scene>` else `chapters/<chapter>/scenes/<scene>` (mirrors
     `chapter_folder` changes→chapters precedence).
   - `scene_draft_path(scene_folder, scene_id) -> Path` — `<scene_folder>/draft.md`
     (fallback `<scene_id>.md`).

3. Template `bookforge/templates/scene-manifest.yml` with the doc's structure
   (`scene_id`, `chapter`, `target_words`, `status`, `required_beats`, `forbidden`,
   `research_questions`, `inputs`).

**Tests:**
- `init_scene_manifest` creates the file at the right nested path
- load/save round-trip without corruption
- `parse_scene_id` handles `chapter-08/scene-02`, `ch08_sc02`, and bare `scene-02`
- `discover_scenes` finds manifests and orders them

**Acceptance:** manifests can be created, written, and read back at the nested path
(`changes/chapter-NN/scenes/scene-MM.manifest.yml`).

---

## Step P2 — `bf packet --scene` (scene-scoped generation packet)

**Produce the packet that gets pasted into provider web.**

**Files to touch:**
- extend `bookforge/core/packet/builder.py`
- extend `bookforge/cli.py` (new `bf scene` group + extend `bf packet`)
- new cases in `tests/test_packet.py`

**Existing seam (verified):**
- `bookforge/core/packet/builder.py:render_packet(book_folder, slug, task)` already takes a
  `slug` + `task`, reads the chapter folder, builds a parts list, applies `TASK_BUDGETS`, and
  trims to budget (`builder.py:27-34`, `builder.py:290-338`). The scene version is a thin
  sibling.
- Excerpt helpers in `packet/excerpt.py` (`relevant_character_profiles`,
  `relevant_rulebook_excerpt`, `prior_continuity`, `pacing_excerpt`,
  `relevant_research_excerpt`) are reusable, scoped by manifest `inputs`.

**Changes:**
1. In `builder.py`, add `render_scene_packet(book_folder, chapter_slug, scene_id, task="draft-prose") -> str`:
   - Load the `SceneManifest` (P1). Its `required_beats`, `forbidden`,
     `research_questions`, `inputs`, `target_words` *become* the packet's core.
   - Reuse existing excerpt helpers, scoped to the manifest's `inputs` (e.g. only the
     characters the manifest lists).
   - Emit a **provider-web-ready** packet with an explicit Output Contract block:
     ```
     ## Output Contract
     - Generate exactly N words (target_words).
     - Use only this packet. Do not research. Do not validate. Do not explain.
     - Return only the story prose.
     ```
   - Reuse `compress_text`, `word_excerpt`, and the existing over-budget trimmer.
2. Write the packet to `<scene_folder>/generation-packet.md` (nested in the chapter folder).
3. Add `SCENE_TASK_BUDGETS = {"draft-prose": 2500, "revise-style": 1200, "patch": 800}`.
4. In `cli.py`:
   - Extend `bf packet` parser with `--scene SCENE_ID` (routes to `render_scene_packet` when
     set, `render_packet` otherwise).
   - New `bf scene` subcommand group: `init <chapter> --scene <id> [--target-words N]`,
     `list <chapter>`, `packet <chapter> <scene>` (convenience alias for
     `bf packet --scene`).

**Tests:**
- scene packet renders with the Output Contract block
- respects manifest `forbidden` / `required_beats`
- stays within `SCENE_TASK_BUDGETS`
- fails cleanly if manifest missing

**Acceptance — the P0→P3 MVP front half:**
```bash
bf scene init chapter-08 --scene scene-02
# (edit manifest: fill beats / forbidden / inputs)
bf packet --chapter chapter-08 --scene scene-02 --task draft-prose
# → writes changes/chapter-08/scenes/scene-02/generation-packet.md
# (paste into ChatGPT web; save returned prose to draft.md)
bf validate --chapter chapter-08
```

---

## Step P3 — `bf patch --scene` (minimal repair packet, not full regenerate)

**The biggest rework-token saver.** Patch only the broken paragraphs.

**Files to touch:**
- new `bookforge/core/patch.py`
- extend `bookforge/core/packet/builder.py` (`patch` task branch)
- extend `bookforge/cli.py`
- new `tests/test_patch.py`

**Existing seam (verified):**
- `bf validate` (via `bookforge/core/validators/`) produces `ManuscriptIssue`s that already
  carry `chapter`, `file`, `line`, `span` (`issue.py:50-72`). `render_report` serializes
  them. The patch system localizes these issues to draft spans and builds a tiny packet.
- `bookforge/core/repair.py` already localizes failures to scenes
  (`[Scene 1: The Stables]` regex) — same instinct, generalized to paragraphs.
- `bookforge/core/canon/apply.py:apply_chapter_event` is the analog precedent: append →
  refold. The patch splicer is the prose-span version.

**Changes:**
1. New `bookforge/core/patch.py`:
   - `localize_issues(issues: list[ManuscriptIssue], scene_manifest) -> list[dict]` — for
     each failing issue, resolve its `file`+`line` to a **paragraph index** in the draft by
     splitting on blank lines (drafts are blank-line separated). Attach the failing paragraph
     text + N paragraphs of immutable surrounding context.
   - `build_patch_packet(scene_manifest, localized_issues) -> str` — emit the **splice-safe**
     format:
     ```
     ## Patch Target: <scene_id> paragraphs 14–17
     <<<<<<< PATCH_TARGET ch08_sc02_p014_p017
     (instructions: return replacement prose only; preserve surrounding context)
     >>>>>>> PATCH_TARGET
     ```
     Plus a per-patch validator checklist (re-derived from the originating issue's `rule_id`).
     Patch budget = 800 tokens — a fraction of a full-chapter packet.
   - `apply_patch(draft_path, scene_id, paragraph_range, replacement) -> None` — splice the
     returned replacement back into the draft at the addressed paragraph range,
     deterministically. The prose-span analog of `canon/apply.py`'s append-and-refold.

2. In `builder.py`, add the `patch` task branch (chapter-level patch falls back to full
   revision for now) and register it in `SCENE_TASK_BUDGETS`.

3. In `cli.py`:
   - Add `patch` to the `bf packet --task` `choices`.
   - New `bf patch --chapter <chapter> --scene <scene>` — runs `bf validate --chapter`
     (or reads a pre-written validation json), localizes failures, writes
     `<scene_folder>/patch-packet.md`.
   - New `bf patch apply --chapter <chapter> --scene <scene> --from-file replacement.md` —
     splices the returned replacement into the draft.

**Tests:**
- a draft with a known style violation localizes to the correct paragraph
- the patch packet is small (<800 tokens) and contains the splice markers
- `apply_patch` splices replacement without corrupting surrounding paragraphs
- a clean draft produces no patch packet (or an all-clear stub)

**Acceptance — the MVP back half:**
```bash
bf patch --chapter chapter-08 --scene scene-02
# → writes changes/chapter-08/scenes/scene-02/patch-packet.md (small, targeted)
# (paste into ChatGPT web; save returned prose to replacement.md)
bf patch apply --chapter chapter-08 --scene scene-02 --from-file replacement.md
# → splices replacement into draft.md at the addressed paragraphs
bf validate --chapter chapter-08
```

---

## Cross-cutting

- **`AGENTS.md`** gets a short new section documenting the scene workflow
  (`bf scene init` → `bf packet --scene` → paste-to-web → `bf patch --scene`) so any agent
  reads the lane split.
- **`docs/storyops-engine-vs-bookforge.md`** gets a Status footer marking P0–P3 done and
  pointing back to this plan.
- **Code conventions** (matching existing modules):
  - `from __future__ import annotations` at the top
  - specific exception classes only — no bare `except Exception` (per the M3 cleanup)
  - `encoding="utf-8"` on all file I/O
  - frozen dataclasses where the codebase uses them
- **Tests:** pytest, run via `python -m pytest tests/` (existing convention). Each step ships
  with tests before it is marked done.

## Execution order

```
P0 (guard)      — independent, ships first; cheap + protective
P1 (manifests)  — foundation P2 and P3 both depend on
P2 (scene packet) — depends on P1
P3 (patch)      — depends on P1 + P2
```

## MVP definition (done = this works end-to-end)

```
1.  bf scene init chapter-08 --scene scene-02
2.  (edit manifest: beats / forbidden / inputs)
3.  bf packet --chapter chapter-08 --scene scene-02 --task draft-prose
4.  paste packet into ChatGPT web
5.  save generated prose to changes/chapter-08/scenes/scene-02/draft.md
6.  bf validate --chapter chapter-08
7.  bf patch --chapter chapter-08 --scene scene-02          (if failures exist)
8.  paste patch packet into ChatGPT web
9.  bf patch apply --chapter chapter-08 --scene scene-02 --from-file replacement.md
10. bf validate --chapter chapter-08
11. bf apply change <book> chapter-08                        (commit the scene)
```

That is the workflow to prove first. Once it works for one scene, the throughput layer
(queue, research cache, Project Kit, MCP) layers on top.
