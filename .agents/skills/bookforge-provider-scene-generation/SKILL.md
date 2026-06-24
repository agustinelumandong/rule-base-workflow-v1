---
name: bookforge-provider-scene-generation
description: Use when the user asks to run an active-scene drafting loop through BookForge MCP and provider-web-driver, sync a provider workspace from a BookForge project kit, send a generation packet, save returned prose through BookForge, and validate or patch the scene without writing prose directly.
---

# BookForge Provider Scene Generation

Use this skill when prose must come from the provider-web lane while BookForge remains the source of truth for scene state, packets, drafts, and validation.

## Core Rule

- BookForge chooses the scene, builds the packet, saves the draft, and validates the result.
- `provider-web-driver` is only the prose-generation transport.
- The agent must not write story prose itself and must not write BookForge-managed files directly.

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

## Guardrails

- Do not choose a different scene than the one returned by `get_active_scene`.
- Do not replace BookForge packet text with an improvised prompt.
- Do not manually edit `draft.md`, `validation.json`, `queue.yml`, `state/loop.json`, or canon files.
- Do not summarize, rewrite, or "clean up" the provider prose before `save_draft` unless the user explicitly requests a separate revision pass.
- Do not switch to CLI or local file writes when the user constrained the run to BookForge MCP and `provider-web-driver`.
- If the provider returns refusal text, meta commentary, or no usable prose, stop and report the provider result instead of inventing prose.

## Workspace Rules

- Use the provider workspace name requested by the user.
- For BookForge book workspaces, prefer `book/<book-slug>` unless the user names a different workspace.
- Sync the stable kit files returned by `build_project_kit`.
- For this loop, the generation packet is normally sent as chat prompt text; do not assume the active packet file must be uploaded unless the user asks for that variant.

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
- Validation fails on word count or rule checks: build the patch packet and report it.
- Provider output drifts from packet intent: do not repair it manually in the same generation loop unless the user asks for a patch/revision loop.
