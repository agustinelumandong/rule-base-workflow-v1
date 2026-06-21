# NotebookLM MCP Setup

Programmatic access to Google NotebookLM via the `nlm` CLI and MCP server.
Source: [jacob-bd/notebooklm-mcp-cli](https://github.com/jacob-bd/notebooklm-mcp-cli)

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- A Google account with access to [NotebookLM](https://notebooklm.google.com)
- Antigravity CLI (`agy`) installed and configured

---

## One-Time Setup

Run the provided script to install and configure everything:

```bash
bash scripts/setup-notebooklm-mcp.sh
```

Or follow the steps manually below.

---

## Manual Steps

### 1. Install the package

```bash
uv tool install notebooklm-mcp-cli
```

This installs two executables:
- `nlm` — CLI for scripting and interactive use
- `notebooklm-mcp` — MCP server binary for AI tools

### 2. Authenticate

```bash
nlm login
```

- Opens Google Chrome automatically
- Log in with your Google account (`esparagozagen@gmail.com`)
- Cookies are extracted and stored at `~/.notebooklm-mcp-cli/profiles/default`

Check auth status anytime:

```bash
nlm login --check
```

### 3. Register MCP with Antigravity

```bash
nlm setup add antigravity
```

Writes the MCP server entry to `~/.gemini/antigravity/mcp_config.json`.
**Restart Antigravity** after this step to activate.

### 4. Install the AI Skill (optional but recommended)

```bash
nlm skill install antigravity
```

Installs a NotebookLM expert skill to `~/.gemini/antigravity/skills/nlm-skill/`
so the AI assistant knows how to use all 35 MCP tools effectively.

---

## Upgrading

```bash
uv tool upgrade notebooklm-mcp-cli
```

Then restart your Antigravity session.

---

## Common Commands

```bash
# List all notebooks
nlm notebook list

# Create a notebook
nlm notebook create "My Research"

# Add a web source
nlm source add <notebook> --url "https://example.com"

# Query a notebook
nlm notebook query <notebook> "What are the key themes?"

# Generate a podcast
nlm audio create <notebook> --confirm

# Run deep research
nlm research start "topic here"

# Check auth
nlm login --check

# Diagnose issues
nlm doctor
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Auth expired | `nlm login` |
| MCP not showing in Antigravity | Restart `agy`, check `~/.gemini/antigravity/mcp_config.json` |
| Command not found: `nlm` | Ensure `~/.local/bin` is in `$PATH` or run `uv tool install notebooklm-mcp-cli` |
| Multiple Google accounts | Use `nlm login --profile work` and `nlm login switch work` |

Full docs: [github.com/jacob-bd/notebooklm-mcp-cli/blob/main/docs](https://github.com/jacob-bd/notebooklm-mcp-cli/tree/main/docs)
