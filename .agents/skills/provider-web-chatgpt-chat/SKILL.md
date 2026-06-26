---
name: provider-web-chatgpt-chat
description: Use when Codex must send prompts to live ChatGPT through the local provider-web-driver checkout only, then wait and capture the assistant response. Trigger this for requests like "chat with ChatGPT", "send this prompt", "get the response", "wait for ChatGPT", "capture the latest answer", or "run this in workspace X and return the text". This skill is for prompt/response execution, not standalone workspace management.
---

# Provider Web ChatGPT Chat

## Overview

Send prompts to live ChatGPT in the local `provider-web-driver-mcp` checkout and capture the final assistant response. Use the helper script for the normal path; it can optionally target a ChatGPT Project before sending the prompt.

## Workflow

1. Confirm the target repo is the local `provider-web-driver-mcp` checkout.
2. Use `scripts/chatgpt_chat.sh` for the normal path.
3. Pass `--workspace` only when the user names a ChatGPT Project to use.
4. Return the important JSON fields instead of raw command output.
5. If the flow breaks because the UI drifted, read `references/chatgpt-chat.md` and adapt inside the same repo/tooling.

## Commands

Chat without changing workspace:

```bash
./.agents/skills/provider-web-chatgpt-chat/scripts/chatgpt_chat.sh \
  --repo /abs/path/to/provider-web-driver-mcp \
  --prompt "Say READY only."
```

Chat inside a named workspace, creating it if missing:

```bash
./.agents/skills/provider-web-chatgpt-chat/scripts/chatgpt_chat.sh \
  --repo /abs/path/to/provider-web-driver-mcp \
  --workspace "longhunter-series/book-2" \
  --ensure-workspace \
  --prompt "Say READY only."
```

## Output Contract

Summarize the result for the user with:

- workspace name if one was used
- whether the workspace was created during this run
- captured response text
- optionally the conversation or project URL

## Failure Handling

- If the browser profile is locked, stop the stale Chromium process using the repo profile path and retry once.
- If ChatGPT is not logged in, report that directly and stop.
- If targeting a workspace and the workspace navigation fails, use the same Projects-page selectors documented in `references/chatgpt-chat.md`.

## References

- Read `references/chatgpt-chat.md` when the normal script fails or when you need current selector details.
