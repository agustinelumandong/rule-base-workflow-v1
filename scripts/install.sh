#!/usr/bin/env bash
# =============================================================================
# Project Install / Repair Script — current-workflow
#
# Usage:
#   bash scripts/install.sh           # Detect and fix all missing components
#   bash scripts/install.sh --dry-run # Show what would be installed, no action
#   bash scripts/install.sh --force   # Reinstall everything even if present
#
# What this auto-installs:
#   - bookforge Python package (pip install -e .)
#   - headroom-ai optional compressor (pip install headroom-ai)
#   - pytest test runner (pip install pytest)
#   - notebooklm-mcp-cli via uv
#   - NotebookLM MCP auth (interactive: nlm login)
#   - NotebookLM MCP registration with Antigravity
#   - NotebookLM AI skill for Antigravity
#
# What requires manual action (printed as reminders):
#   - Python ≥3.8 (system-level, install via mise/pyenv/system)
#   - uv (curl -LsSf https://astral.sh/uv/install.sh | sh)
#   - git (system package manager)
#   - Missing skill folders or orchestrator scripts (git restore)
# =============================================================================

DRY=false
FORCE=false
for arg in "$@"; do
  [[ "$arg" == "--dry-run" ]] && DRY=true
  [[ "$arg" == "--force" ]] && FORCE=true
done

PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLED=0
SKIPPED=0
MANUAL=0
ERRORS=0

# ── Helpers ──────────────────────────────────────────────────────────────────

run_or_dry() {
  # run_or_dry <label> <command...>
  local label="$1"; shift
  if [[ "$DRY" == true ]]; then
    echo "  [dry-run]  $label"
    echo "             → $*"
  else
    echo "  ⚙️   $label"
    if "$@"; then
      echo "  ✅  Done"
      ((INSTALLED++)) || true
    else
      echo "  ❌  Failed: $*"
      ((ERRORS++)) || true
    fi
  fi
  echo ""
}

already() { echo "  ✅  Already installed — $1"; ((SKIPPED++)) || true; echo ""; }
manual()  { echo "  ⚠️   Manual required — $1"; ((MANUAL++)) || true; echo ""; }
section() {
  echo ""
  echo "── $1 $(printf '%.0s─' {1..50})" | head -c 58
  echo ""
}

print_banner() {
  echo ""
  echo "╔══════════════════════════════════════════════════════╗"
  if [[ "$DRY" == true ]]; then
    echo "║    current-workflow — Install (DRY RUN)              ║"
  else
    echo "║       current-workflow — Install / Repair            ║"
  fi
  echo "╚══════════════════════════════════════════════════════╝"
  echo "  Project: $PROJ_ROOT"
  [[ "$DRY" == true ]] && echo "  Mode:    --dry-run (no changes will be made)"
  [[ "$FORCE" == true ]] && echo "  Mode:    --force (reinstalling everything)"
  echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
print_banner

# ── Section 1: System prerequisites ──────────────────────────────────────────
section "1. System Prerequisites"

# Python
if command -v python3 &>/dev/null; then
  PY_OK=$(python3 -c "import sys; print('ok' if sys.version_info >= (3,8) else 'fail')" 2>/dev/null)
  if [[ "$PY_OK" == "ok" ]]; then
    already "Python $(python3 --version 2>&1) (≥3.8)"
  else
    manual "Python too old ($(python3 --version 2>&1)) — install ≥3.8 via mise/pyenv/system"
  fi
else
  manual "python3 not found — install via: mise use python@3.12 OR sudo apt install python3"
fi

# uv
if command -v uv &>/dev/null; then
  already "uv $(uv --version 2>/dev/null | head -1)"
else
  echo "  ⚠️   uv not found — needed for NotebookLM MCP"
  echo "       Install with:"
  echo "         curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "       Then re-run this script."
  ((MANUAL++)) || true
  echo ""
fi

# git
if command -v git &>/dev/null; then
  already "git ($(git --version))"
else
  manual "git not found — install via system package manager (sudo apt install git)"
fi

# ── Section 2: BookForge ──────────────────────────────────────────────────────
section "2. BookForge Package"

BF_INSTALLED=false
if pip show bookforge &>/dev/null 2>&1; then
  BF_INSTALLED=true
fi

if [[ "$BF_INSTALLED" == true && "$FORCE" == false ]]; then
  already "bookforge v$(pip show bookforge 2>/dev/null | grep '^Version:' | awk '{print $2}')"
else
  if [[ ! -f "$PROJ_ROOT/setup.py" ]]; then
    echo "  ❌  setup.py not found in $PROJ_ROOT — cannot install bookforge"
    ((ERRORS++)) || true
    echo ""
  else
    run_or_dry "Installing bookforge (pip install -e .)" \
      pip install -e "$PROJ_ROOT" --quiet
  fi
fi

# ── Section 3: Agent Skills ───────────────────────────────────────────────────
section "3. Agent Skills (.agents/skills/)"

SKILLS_DIR="$PROJ_ROOT/.agents/skills"
REQUIRED_SKILLS=(
  "humanizer"
  "manuscript-workflow-orchestrator"
  "western-classic-writing-style"
  "western-historical-writing-style"
  "western-manuscript-style"
  "western-outlaw-writing-style"
  "western-revisionist-writing-style"
  "western-romance-writing-style"
  "western-story-pattern-analyzer"
  "western-weird-writing-style"
)

MISSING_SKILLS=()
for skill in "${REQUIRED_SKILLS[@]}"; do
  [[ ! -f "$SKILLS_DIR/$skill/SKILL.md" ]] && MISSING_SKILLS+=("$skill")
done

if [[ ${#MISSING_SKILLS[@]} -eq 0 ]]; then
  already "All ${#REQUIRED_SKILLS[@]} skill folders present"
else
  echo "  ❌  Missing ${#MISSING_SKILLS[@]} skill(s):"
  for s in "${MISSING_SKILLS[@]}"; do
    echo "       - $s"
  done
  echo ""
  manual "Skill folders are part of the git repo. Restore with:"
  echo "         git restore .agents/skills/"
  echo ""
fi

# ── Section 4: Orchestrator Scripts ──────────────────────────────────────────
section "4. Orchestrator Scripts"

ORC_DIR="$PROJ_ROOT/.agents/skills/manuscript-workflow-orchestrator/scripts"
REQUIRED_SCRIPTS=(
  "build_context_packet.py"   "check_chapter_gaps.py"
  "check_chapter_rhythm.py"   "check_context_budget.py"
  "check_continuity_chain.py" "check_manuscript_length.py"
  "compile_manuscript.py"     "plan_chapter_pacing.py"
  "run_manuscript_loop.py"    "scan_banned_words.py"
  "scan_source_format.py"     "validate_manuscript_context.py"
)

MISSING_SCRIPTS=()
for script in "${REQUIRED_SCRIPTS[@]}"; do
  [[ ! -f "$ORC_DIR/$script" ]] && MISSING_SCRIPTS+=("$script")
done

if [[ ${#MISSING_SCRIPTS[@]} -eq 0 ]]; then
  already "All ${#REQUIRED_SCRIPTS[@]} orchestrator scripts present"
else
  echo "  ❌  Missing ${#MISSING_SCRIPTS[@]} script(s):"
  for s in "${MISSING_SCRIPTS[@]}"; do
    echo "       - $s"
  done
  echo ""
  manual "Scripts are part of the git repo. Restore with:"
  echo "         git restore .agents/skills/manuscript-workflow-orchestrator/scripts/"
  echo ""
fi

# ── Section 5: Headroom ───────────────────────────────────────────────────────
section "5. Headroom (Context Compression)"

# Core module (part of bookforge — handled in section 2)
HEADROOM_CORE=$(python3 -c "from bookforge.core.headroom import compress_text; print('ok')" 2>&1)
if [[ "$HEADROOM_CORE" == "ok" ]]; then
  already "bookforge.core.headroom (built-in, no extra install)"
else
  echo "  ❌  bookforge.core.headroom not importable — bookforge may not be installed"
  echo "       → Re-run section 2 fix: pip install -e ."
  ((ERRORS++)) || true
  echo ""
fi

# headroom-ai optional package
HAS_OFFICIAL=$(python3 -c "from bookforge.core.headroom import HAS_OFFICIAL_HEADROOM; print('yes' if HAS_OFFICIAL_HEADROOM else 'no')" 2>/dev/null)
if [[ "$HAS_OFFICIAL" == "yes" && "$FORCE" == false ]]; then
  HVER=$(python3 -c "import headroom; print(getattr(headroom, '__version__', 'unknown'))" 2>/dev/null)
  already "headroom-ai v${HVER} (enhanced compression)"
else
  run_or_dry "Installing headroom-ai (optional, enhanced compression)" \
    pip install headroom-ai --quiet
fi

# ── Section 6: Test Runner ────────────────────────────────────────────────────
section "6. Test Runner (pytest)"

if python3 -m pytest --version &>/dev/null 2>&1 && [[ "$FORCE" == false ]]; then
  PYTEST_VER=$(python3 -m pytest --version 2>&1 | head -1)
  already "$PYTEST_VER"
else
  run_or_dry "Installing pytest" \
    pip install pytest --quiet
fi

# ── Section 7: NotebookLM MCP ─────────────────────────────────────────────────
section "7. NotebookLM MCP"

if ! command -v uv &>/dev/null; then
  echo "  ⏭️   Skipping NotebookLM MCP — uv not available (see Section 1)"
  echo ""
else
  # 7a. Package
  NLM_INSTALLED=$(uv tool list 2>/dev/null | grep -c "notebooklm-mcp-cli" || true)
  if [[ "$NLM_INSTALLED" -gt 0 && "$FORCE" == false ]]; then
    PKG_VER=$(uv tool list 2>/dev/null | grep "notebooklm-mcp-cli" | awk '{print $2}')
    already "notebooklm-mcp-cli $PKG_VER"
  elif [[ "$FORCE" == true ]]; then
    run_or_dry "Force-reinstalling notebooklm-mcp-cli" \
      uv tool install notebooklm-mcp-cli --force
  else
    run_or_dry "Installing notebooklm-mcp-cli" \
      uv tool install notebooklm-mcp-cli
  fi

  # 7b. Auth
  AUTH_FILE="$HOME/.notebooklm-mcp-cli/profiles/default/cookies.json"
  if [[ -f "$AUTH_FILE" && "$FORCE" == false ]]; then
    AUTH_CHECK=$(nlm login --check 2>&1)
    if echo "$AUTH_CHECK" | grep -qi "authenticated\|valid\|✓\|success"; then
      ACCOUNT=$(echo "$AUTH_CHECK" | grep -iE "@[a-z]" | head -1 | sed 's/^[[:space:]]*//')
      already "Auth valid${ACCOUNT:+ ($ACCOUNT)}"
    else
      echo "  ⚠️   Auth cookies exist but may be expired"
      if [[ "$DRY" == false ]]; then
        echo "  ⚙️   Re-authenticating (browser will open)..."
        echo ""
        nlm login && echo "  ✅  Auth refreshed" || echo "  ❌  Auth failed — run: nlm login"
      else
        echo "  [dry-run]  Would run: nlm login"
      fi
      echo ""
    fi
  else
    if [[ "$DRY" == true ]]; then
      echo "  [dry-run]  Would run: nlm login  (opens browser)"
      echo ""
    else
      echo "  ⚙️   Authenticating with NotebookLM (browser will open)..."
      echo ""
      nlm login && { echo "  ✅  Auth complete"; ((INSTALLED++)) || true; } \
                || { echo "  ❌  Auth failed — run: nlm login"; ((ERRORS++)) || true; }
      echo ""
    fi
  fi

  # 7c. Antigravity MCP registration
  MCP_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"
  if [[ -f "$MCP_CONFIG" ]] && grep -q "notebooklm" "$MCP_CONFIG" 2>/dev/null && [[ "$FORCE" == false ]]; then
    already "MCP registered in Antigravity (~/.gemini/antigravity/mcp_config.json)"
  else
    run_or_dry "Registering MCP with Antigravity (nlm setup add antigravity)" \
      nlm setup add antigravity
  fi

  # 7d. AI Skill
  SKILL_FILE="$HOME/.gemini/antigravity/skills/nlm-skill/SKILL.md"
  if [[ -f "$SKILL_FILE" && "$FORCE" == false ]]; then
    already "NotebookLM AI skill (~/.gemini/antigravity/skills/nlm-skill/)"
  else
    run_or_dry "Installing NotebookLM AI skill (nlm skill install antigravity)" \
      nlm skill install antigravity
  fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                      Summary                         ║"
echo "╠══════════════════════════════════════════════════════╣"

if [[ "$DRY" == true ]]; then
  echo "║  ℹ️   Dry run complete — no changes made.            ║"
  echo "║      Re-run without --dry-run to apply.             ║"
elif [[ $ERRORS -gt 0 ]]; then
  printf "║  ❌  %d install error(s). Check output above.%*s║\n" "$ERRORS" $((12 - ${#ERRORS})) ""
elif [[ $MANUAL -gt 0 && $INSTALLED -eq 0 ]]; then
  echo "║  ✅  Nothing to install — project is fully set up.  ║"
elif [[ $INSTALLED -gt 0 ]]; then
  printf "║  ✅  %d component(s) installed/repaired.%*s║\n" "$INSTALLED" $((16 - ${#INSTALLED})) ""
else
  echo "║  ✅  Nothing to install — project is fully set up.  ║"
fi

if [[ $MANUAL -gt 0 ]]; then
  printf "║  ⚠️   %d item(s) need manual action (see above).%*s║\n" "$MANUAL" $((10 - ${#MANUAL})) ""
fi

echo "╠══════════════════════════════════════════════════════╣"
echo "║  Verify:  bash scripts/check.sh --quick             ║"
if [[ "$DRY" == false && $INSTALLED -gt 0 ]]; then
  echo "║  Restart Antigravity (agy) to activate MCP.        ║"
fi
echo "╚══════════════════════════════════════════════════════╝"
echo ""
