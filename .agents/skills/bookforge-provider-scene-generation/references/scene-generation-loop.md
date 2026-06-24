# Scene Generation Loop

This reference defines the exact BookForge + `provider-web-driver` loop for provider-side scene drafting.

## Purpose

Keep scene generation aligned with BookForge state, provider workspace context, and validation gates.

## Inputs

- A BookForge-managed active scene
- A provider name such as `chatgpt`
- A provider workspace name such as `book/whispering-ash`

## Procedure

1. Ask BookForge for the active scene with `get_active_scene`.
2. Build the scene packet with `build_generation_packet` and request packet text in the response.
3. Build the provider kit with `build_project_kit`.
4. Open the target provider workspace.
5. If the workspace does not exist, create it with the same name and reopen it.
6. Sync the stable kit files into the provider workspace with `provider_sync_workspace_sources(confirm_sync=true)`.
7. Send the BookForge generation packet text through `provider_chat`.
8. Fetch the latest provider output with `provider_fetch_latest_response`.
9. Save that output through `save_draft`.
10. Validate through `validate_scene`.
11. If validation fails, build `build_patch_packet` from the failed rules and report the patch path.

## Data Mapping

- `scene`: from `get_active_scene`
- `packet_text`: from `build_generation_packet(include_text=true)`
- `stable_files`: resolve from `build_project_kit`
- `prose`: from `provider_fetch_latest_response.response_text`
- `draft_path`: from `save_draft`
- `validation_status`: from `validate_scene.status`
- `patch_packet_path`: from `build_patch_packet` when needed

## Non-Negotiable Constraints

- BookForge is the source of truth for scene selection and persistence.
- Provider output is saved as returned; the agent does not author the scene.
- Validation is part of the loop, not a separate optional step.
- A failed validation ends the generation loop in patch-packet state, not in "done" state.

## Output Shape

Use JSON:

```json
{
  "scene": "chapter-09/scene-01",
  "provider": "chatgpt",
  "workspace_name": "book/whispering-ash",
  "draft_path": "books/.../draft.md",
  "validation_status": "validation_passed"
}
```

If validation fails:

```json
{
  "scene": "chapter-09/scene-01",
  "provider": "chatgpt",
  "workspace_name": "book/whispering-ash",
  "draft_path": "books/.../draft.md",
  "validation_status": "validation_failed",
  "patch_packet_path": "books/.../patch-packet.md"
}
```
