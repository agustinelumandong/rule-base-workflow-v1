---
name: provider-web-chatgpt-workspaces
description: Use when Codex must manage ChatGPT Projects through the local provider-web-driver checkout only, especially for requests like "list workspaces", "list projects", "open workspace", "create workspace", "create if not exists", "ensure this project exists", or "switch ChatGPT to this project". This skill is for workspace/project management only and should not be used for prompt/response capture.
---

# Provider Web ChatGPT Workspaces

## Overview

Manage ChatGPT Projects in the local `provider-web-driver-mcp` checkout without sending prompts. Use the helper script to list existing projects, open a named project, or create and open it when missing.

## Workflow

1. Confirm the target repo is the local `provider-web-driver-mcp` checkout.
2. Use `scripts/chatgpt_workspace.sh` for the normal path.
3. Return the important JSON fields instead of raw command output.
4. If the flow breaks because the UI drifted, read `references/chatgpt-workspaces.md` and adapt inside the same repo/tooling.

## Commands

List projects:

```bash
./.agents/skills/provider-web-chatgpt-workspaces/scripts/chatgpt_workspace.sh \
  --repo /abs/path/to/provider-web-driver-mcp \
  --list
```

Ensure a project exists and is opened:

```bash
./.agents/skills/provider-web-chatgpt-workspaces/scripts/chatgpt_workspace.sh \
  --repo /abs/path/to/provider-web-driver-mcp \
  --workspace "longhunter-series/book-2" \
  --ensure
```

Open only:

```bash
./.agents/skills/provider-web-chatgpt-workspaces/scripts/chatgpt_workspace.sh \
  --repo /abs/path/to/provider-web-driver-mcp \
  --workspace "longhunter-series/book-2" \
  --open
```

## Output Contract

Summarize the result for the user with:

- workspace list when requested
- workspace name
- whether it already existed
- whether it was created
- whether it was opened
- optionally the project URL

## Failure Handling

- If the browser profile is locked, stop the stale Chromium process using the repo profile path and retry once.
- If ChatGPT is not logged in, report that directly and stop.

## References

- Read `references/chatgpt-workspaces.md` when the normal script fails or when you need current selector details.
