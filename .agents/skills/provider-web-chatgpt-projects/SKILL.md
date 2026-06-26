---
name: provider-web-chatgpt-projects
description: Use when Codex must operate ChatGPT Projects through the local provider-web-driver checkout only, especially for requests like "Use provider-web-driver only", "provider=chatgpt", "list workspaces/projects", "open workspace", "create if not exists", "send this prompt", "wait for the response", or "return captured text with workspace name". This skill is for live browser-driven ChatGPT Project workflows, not generic chat advice.
---

# Provider Web ChatGPT Projects

## Overview

Run a live ChatGPT Project workflow against the local `provider-web-driver-mcp` checkout. Prefer the helper script in this skill so the agent follows the same proven path: list existing projects, open or create the target project, submit the prompt, wait for a stable answer, and return captured text plus workspace metadata.

## Workflow

1. Confirm the target repo is the local `provider-web-driver-mcp` checkout.
2. Use `scripts/chatgpt_project_roundtrip.sh` for the normal path.
3. Return the important fields from the JSON result instead of raw command noise.
4. If the script fails because the provider UI drifted, read `references/chatgpt-project-workflow.md` and adapt inside the same repo/tooling rather than switching to unrelated tools.

## Command

Run from the repo root:

```bash
./.agents/skills/provider-web-chatgpt-projects/scripts/chatgpt_project_roundtrip.sh \
  --repo /abs/path/to/provider-web-driver-mcp \
  --workspace "longhunter-series/book-2" \
  --prompt "Say READY only."
```

Optional flags:

- `--timeout-ms <ms>`: Override the default 600000 ms wait window.

## Output Contract

Summarize the result for the user with:

- workspace name
- whether it was created during this run
- captured response text
- optionally the project URL if it helps

Do not dump the entire JSON unless the user asks for raw output.

## Failure Handling

- If the browser profile is locked, stop the stale Chromium process using the repo profile path and retry once.
- If the high-level MCP workspace methods fail, keep using the local `provider-web-driver` modules and the lower-level Projects page flow documented in `references/chatgpt-project-workflow.md`.
- If ChatGPT is not logged in, report that directly and stop.

## References

- Read `references/chatgpt-project-workflow.md` when the normal script fails or when you need to patch the flow for UI drift.
