---
name: bookforge-provider-scene-generation
description: Use when the user asks to run an active-scene drafting loop through BookForge MCP and provider-web-driver, sync a provider workspace from a BookForge project kit, send a generation packet, save returned prose through BookForge, and validate or patch the scene without writing prose directly.
---

# BookForge Provider Scene Generation

Use this skill when prose must come from the provider-web lane while BookForge remains the source of truth for scene state, packets, drafts, and validation.

## Core Rule

- BookForge chooses the scene, builds the packet, saves the draft, and validates the result.
- `provider-web-driver` is only the prose-generation transport when automated mode is active.
- The agent must not write story prose itself and must not write BookForge-managed files directly, *unless* the automated web driver is bypassed (`use_web_driver: false`). In bypass mode, the agent/operator is explicitly permitted to write or edit `draft.md` directly in the active scene directory based on the generated generation or patch packets.

## When to Use

- The user says to use BookForge MCP plus `provider-web-driver`.
- The user wants an active-scene loop, generation packet flow, ChatGPT project sync, or save-and-validate run.
- The user says not to generate prose directly.

Do not use this skill for manual drafting, non-BookForge scenes, or freeform prompt-writing outside the BookForge packet flow.

## Required Order

Load [references/scene-generation-loop.md](references/scene-generation-loop.md) before running the loop.

1. `get_active_scene`
2. `build_generation_packet` for that scene with `include_text=true`
3. `build_project_kit` for the requested provider
4. `provider_open_workspace`
5. If the workspace is missing, `provider_create_workspace` with the exact same name, then reopen it
6. `provider_sync_workspace_sources` using the BookForge kit `stable_files`
7. `provider_chat` with the generation packet text
8. `provider_fetch_latest_response`
9. `save_draft` with the fetched provider response
10. `validate_scene`
11. If validation fails, `build_patch_packet`

For ChatGPT projects, the workspace/project is created once and then reused. Each `provider_chat` call must run in a fresh chat session inside that same workspace rather than continuing the prior thread.

## Guardrails

- Do not choose a different scene than the one returned by `get_active_scene`.
- Do not replace BookForge packet text with an improvised prompt.
- Do not manually edit `draft.md` (except in bypass mode when `use_web_driver: false` is active, where editing `draft.md` is expected), `validation.json`, `queue.yml`, `state/loop.json`, or canon files.
- Do not summarize, rewrite, or "clean up" the provider prose before `save_draft` unless the user explicitly requests a separate revision pass.
- Do not switch to CLI or local file writes when the user constrained the run to BookForge MCP and `provider-web-driver` (unless web driver is bypassed, in which case local editing of `draft.md` is required).
- If the provider returns refusal text, meta commentary, or no usable prose, stop and report the provider result instead of inventing prose.

## Workspace Rules

- Use the provider workspace name requested by the user.
- For BookForge book workspaces, derive the default workspace from the book path:
  - `books/<series>/<book>` -> `<series>/<book>`
  - `books/<book>` -> `<book>`
- For `books/longhunter-series/book-2`, use `longhunter-series/book-2` unless the user names a different workspace.
- Create the workspace only once. After it exists, always reopen and reuse the same workspace name.
- Treat ChatGPT project reuse and chat-session reuse as separate things: same workspace, fresh chat each prompt.
- Sync the stable kit files returned by `build_project_kit`; this is normally one compiled source file to stay under provider source-count limits.
- For this loop, the generation packet is normally sent as chat prompt text; do not assume the active packet file must be uploaded unless the user asks for that variant.
- The active packet is one scene. Do not ask the provider to draft a full chapter in one response.

## Result Contract

Return a compact JSON result with:

- `scene`
- `provider`
- `workspace_name`
- `draft_path`
- `validation_status`

If validation fails, also return:

- `patch_packet_path`

## Common Failure Cases

- `provider_open_workspace` returns not found: create the exact workspace, reopen, continue.
- `provider_chat` or `provider_start_chat` reports `ACTIVE_CHAT_STILL_STREAMING`: wait for the same workspace session to finish `Thinking`, then retry the chat step. Do not create a new workspace and do not redirect the prompt into the previous still-running thread.
- `provider_chat` or `provider_start_chat` reports `CHAT_SESSION_PROOF_FAILED`: the provider could not prove that `New chat` created a different thread. Do not send another prompt blindly; reopen the same workspace, re-establish a fresh chat, and retry only after proof succeeds.
- Validation fails on word count or rule checks: build the patch packet and report it.
- Provider output drifts from packet intent: do not repair it manually in the same generation loop unless the user asks for a patch/revision loop.
