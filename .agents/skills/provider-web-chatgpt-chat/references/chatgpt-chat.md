# ChatGPT Chat Workflow

## Purpose

Capture the live ChatGPT prompt/response workflow for sending a prompt and waiting for the final assistant text.

## Supported operations

- Send a prompt in the current chat
- Optionally enter a named ChatGPT Project first
- Wait for a stable assistant response
- Return the captured response text

## Current selectors and behaviors

- Home chat page: `https://chatgpt.com/`
- Projects page when targeting a workspace: `https://chatgpt.com/projects`
- Composer selectors:
  - `#prompt-textarea`
  - `[data-testid="composer-input"]`
  - `div.ProseMirror[contenteditable="true"]`
- Streaming stop button:
  - `button[aria-label="Stop streaming"]`
- Assistant content candidates:
  - `[data-message-author-role="assistant"]`
  - `article[data-testid^="conversation-turn-"] .markdown`
  - `div[data-message-id] .markdown`
  - `.markdown`

## Workspace targeting

When a workspace is specified:

1. Go to the Projects page.
2. Normalize project row text before matching names.
3. Create the workspace only when `--ensure-workspace` is set and the name is missing.
4. Open the matching project before sending the prompt.

## Failure notes

- The repo helper `getLatestAssistantText` may not always work against the current page shape; a local DOM poller is safer.
- Some project pages require clicking `New chat` before the composer appears.
- A stale persistent Chromium instance can lock the ChatGPT profile; kill it and retry once.
