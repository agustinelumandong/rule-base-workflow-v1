#!/usr/bin/env bash
# =============================================================================
# NotebookLM MCP — Health Check Script
#
# Usage:
#   bash scripts/check-notebooklm-mcp.sh
#
# Checks:
#   1. uv is installed
#   2. notebooklm-mcp-cli package is installed
#   3. nlm and notebooklm-mcp executables are available
#   4. Auth credentials exist and are valid
#   5. MCP is registered in Antigravity config
#   6. AI skill is installed
# =============================================================================

PASS="✅"
FAIL="❌"
WARN="⚠️ "

ERRORS=0
WARNINGS=0

check_pass() { echo "  $PASS  $1"; }
check_fail() { echo "  $FAIL  $1"; ((ERRORS++)) || true; }
check_warn() { echo "  $WARN  $1"; ((WARNINGS++)) || true; }

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║    NotebookLM MCP — Health Check             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. uv ────────────────────────────────────────────────────────────────────
echo "── Dependencies ─────────────────────────────────"

if command -v uv &>/dev/null; then
  UV_VER=$(uv --version 2>/dev/null | head -1)
  check_pass "uv installed ($UV_VER)"
else
  check_fail "uv not found — install: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# ── 2. notebooklm-mcp-cli package ────────────────────────────────────────────
if uv tool list 2>/dev/null | grep -q "notebooklm-mcp-cli"; then
  PKG_VER=$(uv tool list 2>/dev/null | grep "notebooklm-mcp-cli" | awk '{print $2}')
  check_pass "notebooklm-mcp-cli installed ($PKG_VER)"
else
  check_fail "notebooklm-mcp-cli not installed — run: bash scripts/setup-notebooklm-mcp.sh"
fi

echo ""
echo "── Executables ──────────────────────────────────"

# ── 3a. nlm CLI ──────────────────────────────────────────────────────────────
if command -v nlm &>/dev/null; then
  NLM_PATH=$(which nlm)
  check_pass "nlm CLI available ($NLM_PATH)"
else
  check_fail "nlm not in PATH — check: \$HOME/.local/bin is in \$PATH"
fi

# ── 3b. notebooklm-mcp server binary ─────────────────────────────────────────
if command -v notebooklm-mcp &>/dev/null; then
  MCP_PATH=$(which notebooklm-mcp)
  check_pass "notebooklm-mcp server available ($MCP_PATH)"
else
  check_fail "notebooklm-mcp binary not in PATH"
fi

echo ""
echo "── Authentication ───────────────────────────────"

# ── 4a. Auth token file exists ───────────────────────────────────────────────
AUTH_FILE="$HOME/.notebooklm-mcp-cli/profiles/default/cookies.json"
if [[ -f "$AUTH_FILE" ]]; then
  check_pass "Auth token file found"
else
  check_fail "Auth file missing ($AUTH_FILE) — run: nlm login"
fi

# ── 4b. Live auth check via nlm ──────────────────────────────────────────────
if command -v nlm &>/dev/null; then
  AUTH_STATUS=$(nlm login --check 2>&1)
  if echo "$AUTH_STATUS" | grep -qi "authenticated\|valid\|✓\|success"; then
    ACCOUNT=$(echo "$AUTH_STATUS" | grep -i "account\|email\|@" | head -1 | sed 's/^[[:space:]]*//')
    check_pass "Auth is valid${ACCOUNT:+ — $ACCOUNT}"
  elif echo "$AUTH_STATUS" | grep -qi "expired\|invalid\|not auth\|stale"; then
    check_fail "Auth expired — run: nlm login"
  else
    check_warn "Auth status unclear — run 'nlm login --check' manually"
  fi
fi

echo ""
echo "── Antigravity Integration ──────────────────────"

# ── 5. MCP registered in Antigravity config ───────────────────────────────────
MCP_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"
if [[ -f "$MCP_CONFIG" ]]; then
  if grep -q "notebooklm" "$MCP_CONFIG" 2>/dev/null; then
    check_pass "MCP registered in Antigravity ($MCP_CONFIG)"
  else
    check_fail "Antigravity config exists but notebooklm entry missing — run: nlm setup add antigravity"
  fi
else
  check_fail "Antigravity mcp_config.json not found — run: nlm setup add antigravity"
fi

# ── 6. AI Skill installed ─────────────────────────────────────────────────────
SKILL_PATH="$HOME/.gemini/antigravity/skills/nlm-skill/SKILL.md"
if [[ -f "$SKILL_PATH" ]]; then
  SKILL_VER=$(grep -m1 "version\|v[0-9]" "$SKILL_PATH" 2>/dev/null | head -1 | sed 's/^[[:space:]]*//' || echo "")
  check_pass "NotebookLM AI skill installed${SKILL_VER:+ ($SKILL_VER)}"
else
  check_warn "AI skill not installed (optional) — run: nlm skill install antigravity"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "── Summary ──────────────────────────────────────"

if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
  echo ""
  echo "  ✅  All checks passed — NotebookLM MCP is ready."
  echo ""
  echo "  Quick test:"
  echo "    nlm notebook list"
  echo ""
elif [[ $ERRORS -eq 0 ]]; then
  echo ""
  echo "  ⚠️   $WARNINGS warning(s) — mostly working, check items above."
  echo ""
else
  echo ""
  echo "  ❌  $ERRORS error(s) found — run the setup script to fix:"
  echo "      bash scripts/setup-notebooklm-mcp.sh"
  echo ""
fi
