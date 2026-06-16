#!/usr/bin/env bash
# =============================================================================
# NotebookLM MCP Setup Script
# Source: https://github.com/jacob-bd/notebooklm-mcp-cli
#
# Usage:
#   bash scripts/setup-notebooklm-mcp.sh
#
# What this does:
#   1. Installs notebooklm-mcp-cli via uv
#   2. Opens browser for Google auth (you log in once)
#   3. Registers the MCP server with Antigravity
#   4. Installs the NotebookLM AI skill for Antigravity
# =============================================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║       NotebookLM MCP — Setup Script          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Check for uv ─────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  echo "❌  uv not found. Install it first:"
  echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

# ── Step 2: Install or upgrade the package ───────────────────────────────────
echo "📦  Installing notebooklm-mcp-cli..."
if uv tool list 2>/dev/null | grep -q "notebooklm-mcp-cli"; then
  echo "    Already installed — upgrading..."
  uv tool upgrade notebooklm-mcp-cli
else
  uv tool install notebooklm-mcp-cli
fi
echo "    ✓ Done"
echo ""

# ── Step 3: Authenticate ─────────────────────────────────────────────────────
echo "🔐  Authenticating with Google NotebookLM..."
echo "    A browser window will open — log in with your Google account."
echo "    The window closes automatically when done."
echo ""
nlm login
echo ""

# ── Step 4: Register MCP with Antigravity ────────────────────────────────────
echo "🔌  Registering MCP server with Antigravity..."
nlm setup add antigravity
echo ""

# ── Step 5: Install AI Skill ─────────────────────────────────────────────────
echo "🧠  Installing NotebookLM skill for Antigravity..."
nlm skill install antigravity
echo ""

# ── Done ─────────────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════╗"
echo "║   ✓ Setup complete!                          ║"
echo "║                                              ║"
echo "║   Restart Antigravity (agy) to activate.    ║"
echo "║                                              ║"
echo "║   Quick test:                                ║"
echo "║     nlm notebook list                        ║"
echo "║     nlm login --check                        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
