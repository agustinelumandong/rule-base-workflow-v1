# ChatGPT Project Workflow

## Purpose

Capture the proven live workflow for `provider-web-driver-mcp` when the built-in ChatGPT workspace helpers are too brittle for the current ChatGPT UI.

## Preconditions

- Use the local `provider-web-driver-mcp` checkout.
- Use ChatGPT only.
- Reuse the repo's own modules:
  - `src/browser/launch.ts`
  - `src/browser/page.ts`
  - `src/providers/chatgpt/prompt.ts`
- Assume the persistent ChatGPT profile is already logged in.

## Proven fallback flow

1. Launch the persistent ChatGPT browser context with `launchBrowser("chatgpt")`.
2. Reuse or create a tab with `findOrCreateTab(context, "chatgpt.com")`.
3. Navigate directly to `https://chatgpt.com/projects`.
4. List existing projects from the Projects page rows, not from the older sidebar helper.
   - Normalize row text before matching names because the Projects table can append date text such as `TodayToday` or month/day strings directly onto the project name.
5. If the target project does not exist:
   - Click the visible `New` button or `aria-label="New project"` button.
   - Fill `input[name="projectName"]` or `#project-name`.
   - Click `Create project`.
6. Open the target project from the Projects page.
7. Start a fresh chat thread for each prompt:
   - Click `New chat` if the control is visible.
   - If the project home already exposes an empty composer, that page can be used as the fresh thread.
   - Do not reuse the prior in-flight conversation for the next generation/query.
8. Submit the prompt using `submitPrompt`.
9. Poll for a stable assistant response by checking:
   - `button[aria-label="Stop streaming"]` for stream state
   - visible assistant markdown blocks for latest text
10. Return:
   - `workspaces_before`
   - `workspace_name`
   - `created`
   - `project_url`
   - `response_text`

## Current DOM patterns that worked

- Existing project rows:
  - `[role="row"].group.EhAptG_selectableRow`
- New project controls:
  - `button[aria-label="New project"]`
  - `button:has-text("New")`
  - `input[name="projectName"]`
  - `#project-name`
  - `button:has-text("Create project")`
- Composer:
  - `#prompt-textarea`
  - `[data-testid="composer-input"]`
  - `div.ProseMirror[contenteditable="true"]`

## Known issues

- `provider_list_workspaces` can fail on a brittle home/sidebar click path.
- The repo helper `getLatestAssistantText` may fail in some contexts; a local manual DOM poller is safer when the current page shape changes.
- A stale persistent Chromium instance can lock the ChatGPT profile. Kill the process using the repo profile path and retry once.
- Reusing the same chat thread for consecutive project prompts can collide with an active `Thinking` state or return stale/truncated content. The safe default is one project plus a fresh chat thread per prompt.
