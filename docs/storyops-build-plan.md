# StoryOps Build Plan — Connected to the Current BookForge System

> **Status:** Approved with revisions. Derived from `docs/storyops-engine-vs-bookforge.md`
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
- **Scene folder layout:** nested folder per scene (Option B):
  ```
  changes/chapter-NN/scenes/scene-MM/
    manifest.yml
    generation-packet.md
    draft.md
    validation.json
    patch-packet.md
    replacement.md
    guard-log.jsonl
  ```

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
  already computes projected output tokens and enforces the global cap.
- It is currently only invoked by the standalone `bf check-persona` CLI. We must wire it into
  the active drafting/packet generation entry points (see Step P2) so the guard is active.

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
3. Threshold must be **configurable**, not a flat number.
4. Calculate projected output tokens based on target words rather than input tokens when target words are available:
   ```python
   projected_output_tokens = int(target_words * 1.35)
   ```
   (Otherwise, fall back to `projected_input_tokens // 4` or general heuristics).

**Tests:**
- advisory mode returns `True` and writes a log line
- hard mode returns `False` when exceeding the cap
- cap is read from settings, not hardcoded
- non-operator persona + draft action is unaffected

**Acceptance:**
```bash
bf check-persona --persona extractor --model gpt-4o --action draft --projected-tokens 4000
# advisory mode: warning printed + guard-log.jsonl line written
# hard mode: refused with a "use the provider-web lane" hint
```

---

## Step P1 — Scene Manifests + Scene Folder Addressing

**Generate by scene, not whole chapter.** Add the stable folder layout that patches and the queue
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
- `bookforge/core/packet/helpers.py:91` `chapter_folder()` resolves `changes/<slug>` →
  `chapters/<slug>` — scene resolution mirrors this.

**Changes:**
1. New `bookforge/core/scene.py`:
   - `@dataclass SceneManifest` — fields: `scene_id`, `chapter`, `target_words`, `status`,
     `required_beats: list[str]`, `forbidden: list[str]`, `research_questions: list[str]`,
     `inputs: dict`.
   - Implement paths as **calculated Python properties** on `SceneManifest` rather than static serialized fields:
     - `scene_folder` -> `changes/chapter-NN/scenes/scene-MM/`
     - `packet_path` -> `scene_folder / "generation-packet.md"`
     - `draft_path` -> `scene_folder / "draft.md"`
     - `validation_path` -> `scene_folder / "validation.json"`
     - `patch_packet_path` -> `scene_folder / "patch-packet.md"`
     - `replacement_path` -> `scene_folder / "replacement.md"`
   - `manifest_path(chapter_folder, scene_id) -> Path` →
     `chapter_folder / "scenes" / scene_id / "manifest.yml"` (folder-per-scene layout).
   - `init_scene_manifest(chapter_folder, scene_id, target_words=3500)` — writes a template
     manifest and creates the directory.
   - `load_scene_manifest(path) -> SceneManifest` and `save_scene_manifest(manifest)` — YAML
     round-trip via existing `yaml.safe_load` / `save_yaml_file` from `canon/io.py`.
   - `parse_scene_id(slug) -> tuple[str, str]` — split `chapter-08/scene-02` or `ch08_sc02`
     or bare `scene-02` (context-implied) into `(chapter_slug, scene_id)`.
   - `discover_scenes(chapter_folder) -> list[SceneManifest]` — glob `scenes/*/manifest.yml`.

2. Add to `helpers.py`:
   - `scene_folder(book_folder, chapter_slug, scene_id) -> Path` — resolves
     `changes/<chapter>/scenes/<scene>` else `chapters/<chapter>/scenes/<scene>`.
   - `scene_draft_path(scene_folder, scene_id) -> Path` — `<scene_folder>/draft.md`.

3. Template `bookforge/templates/scene-manifest.yml` with the doc's structure.

**Tests:**
- `init_scene_manifest` creates the folder and file at the correct nested path
- load/save round-trip without corruption
- `parse_scene_id` handles `chapter-08/scene-02`, `ch08_sc02`, and bare `scene-02`
- `discover_scenes` finds manifests and orders them

**Acceptance:** manifests can be created, written, and read back at the nested path
(`changes/chapter-NN/scenes/scene-MM/manifest.yml`).

---

## Step P2 — `bf packet --scene` (scene-scoped generation packet)

**Produce the packet that gets pasted into provider web.**

**Files to touch:**
- extend `bookforge/core/packet/builder.py`
- extend `bookforge/cli.py` (new `bf scene` group + extend `bf packet` / `bf validate`)
- new cases in `tests/test_packet.py`

**Existing seam (verified):**
- `bookforge/core/packet/builder.py:render_packet()` builds a parts list and trims to budget.
- Excerpt helpers in `packet/excerpt.py` are reusable.

**Changes:**
1. In `builder.py`, add `render_scene_packet(book_folder, chapter_slug, scene_id, task="draft-prose") -> str`:
   - Wire in the **Operator-Prose Guard** (P0): if this method is called, trigger `check_persona_capabilities` to log or refuse if an operator attempts a large prose generation task.
   - Load the `SceneManifest` (P1). Its fields become the packet's core.
   - Emit a **provider-web-ready** packet with an explicit Output Contract block:
     ```
     ## Output Contract
     - Generate exactly N words (target_words).
     - Use only this packet. Do not research. Do not validate. Do not explain.
     - Return only the story prose.
     ```
2. Write the packet to `<scene_folder>/generation-packet.md`.
3. Add `SCENE_TASK_BUDGETS = {"draft-prose": 2500, "revise-style": 1200, "patch": 800}`.
4. In `cli.py`:
   - Extend `bf packet` parser with `--scene SCENE_ID` (routes to `render_scene_packet` when set).
   - New `bf scene` subcommand group: `init <chapter> --scene <id> [--target-words N]`, `list <chapter>`, `packet <chapter> <scene>`.
   - Extend `bf validate` to support scene-level validation:
     ```bash
     bf validate --chapter chapter-08 --scene scene-02
     # or
     bf validate --scene chapter-08/scene-02
     ```
     This reads and validates only the scene-level draft.md.

**Tests:**
- scene packet renders with the Output Contract block
- respects manifest fields and budgets
- fails cleanly if manifest is missing
- guard gets triggered at packet generation boundaries

**Acceptance:**
```bash
bf scene init chapter-08 --scene scene-02
bf packet --chapter chapter-08 --scene scene-02 --task draft-prose
# → writes changes/chapter-08/scenes/scene-02/generation-packet.md
# (paste into ChatGPT web; save returned prose to draft.md)
bf validate --chapter chapter-08 --scene scene-02
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
- `bf validate` produces `ManuscriptIssue`s. We localize these to draft spans and build a tiny packet.

**Changes:**
1. New `bookforge/core/patch.py`:
   - `localize_issues(issues: list[ManuscriptIssue], scene_manifest) -> list[dict]` — resolve issue `file`+`line` to a paragraph index (blank-line separated).
   - `build_patch_packet(scene_manifest, localized_issues) -> str` — emit the splice-safe format:
     ```
     ## Patch Target: <scene_id> paragraphs 14–17
     <<<<<<< PATCH_TARGET ch08_sc02_p014_p017
     (instructions: return replacement prose only; preserve surrounding context)
     >>>>>>> PATCH_TARGET
     ```
     Plus a per-patch validator checklist.
   - `apply_patch(draft_path, scene_id, paragraph_range, replacement) -> None`:
     - **Safety Checks:** Reject replacement files that contain explanations, markdown headings, or missing/malformed patch markers.
     - **Verification:** Confirm original paragraphs match target hashes/lines before splicing.
     - Deterministically splice the replacement back in.

2. In `builder.py`, add the `patch` task branch.

3. In `cli.py`:
   - Add `patch` to choices.
   - New `bf patch --chapter <chapter> --scene <scene>` — writes `<scene_folder>/patch-packet.md`.
   - New `bf patch apply --chapter <chapter> --scene <scene> --from-file replacement.md` — splices replacement into the draft.

**Tests:**
- a draft with violations localizes to correct paragraphs
- `apply_patch` rejects conversational output or headings
- `apply_patch` splices replacement cleanly or aborts if the original paragraphs mismatch hashes

**Acceptance:**
```bash
bf patch --chapter chapter-08 --scene scene-02
bf patch apply --chapter chapter-08 --scene scene-02 --from-file replacement.md
bf validate --chapter chapter-08 --scene scene-02
```

---

## Cross-cutting

- **`AGENTS.md`** gets updated with instructions on the new scene workflow.
- **`docs/storyops-engine-vs-bookforge.md`** gets a status update.
- **Code conventions:** Standard `from __future__ import annotations`, specific exception classes, `encoding="utf-8"`, frozen dataclasses.
- **Tests:** pytest.

---

## Execution order

```
P0a: guard logic (check_persona_capabilities)
P0b: guard log + settings (style.py DEFAULT_SETTINGS)
P1: scene folder + manifest (scene.py, templates)
P2: scene packet + guard call site (builder.py, cli.py)
P3a: issue localization (patch.py)
P3b: patch packet (builder.py)
P3c: safe patch apply (patch.py, cli.py)
```

---

## MVP definition (done = this works end-to-end)

```
1.  bf scene init chapter-08 --scene scene-02
2.  (edit manifest: beats / forbidden / inputs)
3.  bf packet --chapter chapter-08 --scene scene-02 --task draft-prose
4.  paste packet into ChatGPT web
5.  save generated prose to changes/chapter-08/scenes/scene-02/draft.md
6.  bf validate --chapter chapter-08 --scene scene-02
7.  bf patch --chapter chapter-08 --scene scene-02          (if failures exist)
8.  paste patch packet into ChatGPT web
9.  bf patch apply --chapter chapter-08 --scene scene-02 --from-file replacement.md
10. bf validate --chapter chapter-08 --scene scene-02
11. bf apply change <book> chapter-08                        (commit the scene)
```
