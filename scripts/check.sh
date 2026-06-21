#!/usr/bin/env bash
# =============================================================================
# Project Health Check — current-workflow
#
# Usage:
#   bash scripts/check.sh           # Full check
#   bash scripts/check.sh --quick   # Skip pytest (faster)
#   bash scripts/check.sh --nlm     # Only NotebookLM MCP section
#
# Sections:
#   1. System — Python, uv
#   2. BookForge — package install, CLI commands, core module imports
#   3. Agent Skills — all .agents/skills/ SKILL.md files present
#   4. Orchestrator — all runner scripts present and importable
#   5. Books — at least one book project found
#   6. Headroom — module import, local compressor, optional headroom-ai
#   7. Test Suite — pytest (skipped with --quick)
#   8. NotebookLM MCP — install, auth, Antigravity config, AI skill
# =============================================================================

QUICK=false
NLM_ONLY=false
for arg in "$@"; do
  [[ "$arg" == "--quick" ]] && QUICK=true
  [[ "$arg" == "--nlm" ]] && NLM_ONLY=true
done

PASS="✅"
FAIL="❌"
WARN="⚠️ "
SKIP="⏭️ "
ERRORS=0
WARNINGS=0

check_pass() { echo "  $PASS  $1"; }
check_fail() { echo "  $FAIL  $1"; ((ERRORS++)) || true; }
check_warn() { echo "  $WARN  $1"; ((WARNINGS++)) || true; }
check_skip() { echo "  $SKIP  $1 (skipped)"; }

PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

print_header() {
  echo ""
  echo "── $1 $(printf '%.0s─' {1..50})" | head -c 54
  echo ""
}

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║       current-workflow — Project Health Check        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo "  Project: $PROJ_ROOT"
echo ""

# ═══════════════════════════════════════════════════════════
# Section 1 — System
# ═══════════════════════════════════════════════════════════
if [[ "$NLM_ONLY" == false ]]; then
  print_header "1. System"

  # Python
  if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    PY_MIN_OK=$(python3 -c "import sys; print('ok' if sys.version_info >= (3,8) else 'fail')" 2>/dev/null)
    if [[ "$PY_MIN_OK" == "ok" ]]; then
      check_pass "Python $PY_VER (≥3.8 required)"
    else
      check_fail "Python version too old — need ≥3.8, got $PY_VER"
    fi
  else
    check_fail "python3 not found"
  fi

  # uv
  if command -v uv &>/dev/null; then
    check_pass "uv $(uv --version 2>/dev/null | head -1)"
  else
    check_warn "uv not installed (needed for NotebookLM MCP and tool management)"
  fi

  # git
  if command -v git &>/dev/null; then
    BRANCH=$(git -C "$PROJ_ROOT" branch --show-current 2>/dev/null || echo "unknown")
    check_pass "git — branch: $BRANCH"
  else
    check_warn "git not found"
  fi

  # pip
  if command -v pip &>/dev/null || command -v pip3 &>/dev/null; then
    check_pass "pip available"
  else
    check_warn "pip not found — bookforge may not be installable"
  fi
fi

# ═══════════════════════════════════════════════════════════
# Section 2 — BookForge Package
# ═══════════════════════════════════════════════════════════
if [[ "$NLM_ONLY" == false ]]; then
  print_header "2. BookForge Package"

  # Package installed?
  if pip show bookforge &>/dev/null 2>&1; then
    BF_VER=$(pip show bookforge 2>/dev/null | grep "^Version:" | awk '{print $2}')
    check_pass "bookforge installed (v$BF_VER)"
  else
    check_fail "bookforge not installed — run: pip install -e ."
  fi

  # CLI commands
  if command -v bookforge &>/dev/null; then
    check_pass "bookforge CLI available ($(which bookforge))"
  else
    check_fail "'bookforge' command not found — run: pip install -e ."
  fi

  if command -v bf &>/dev/null; then
    check_pass "bf alias available ($(which bf))"
  else
    check_warn "'bf' alias not found (minor — 'bookforge' still works)"
  fi

  # Core module imports
  IMPORT_CHECK=$(python3 -c "
from bookforge.core import (
    scanner, validator, loop, packet, analytics,
    headroom, compiler, pacing, budget, chain,
    action, persona, relationship, repair, research,
    rhythm, series, voice, world
)
print('ok')
" 2>&1)
  if [[ "$IMPORT_CHECK" == "ok" ]]; then
    check_pass "All bookforge.core modules import cleanly"
  else
    check_fail "Core import error: $IMPORT_CHECK"
  fi

  # NotebookLM core module
  NLM_IMPORT=$(python3 -c "from bookforge.core import notebooklm; print('ok')" 2>&1)
  if [[ "$NLM_IMPORT" == "ok" ]]; then
    check_pass "bookforge.core.notebooklm module importable"
  else
    check_warn "bookforge.core.notebooklm import issue: $NLM_IMPORT"
  fi

  # CLI entrypoint sanity (--help exits 0)
  if bookforge --help &>/dev/null 2>&1; then
    check_pass "bookforge --help runs OK"
  else
    check_warn "bookforge --help returned non-zero (may be a display issue)"
  fi
fi

# ═══════════════════════════════════════════════════════════
# Section 3 — Agent Skills
# ═══════════════════════════════════════════════════════════
if [[ "$NLM_ONLY" == false ]]; then
  print_header "3. Agent Skills (.agents/skills/)"

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

  SKILLS_FOUND=0
  for skill in "${REQUIRED_SKILLS[@]}"; do
    SKILL_MD="$SKILLS_DIR/$skill/SKILL.md"
    if [[ -f "$SKILL_MD" ]]; then
      ((SKILLS_FOUND++)) || true
    else
      check_fail "Missing skill: $skill (SKILL.md not found)"
    fi
  done

  if [[ $SKILLS_FOUND -eq ${#REQUIRED_SKILLS[@]} ]]; then
    check_pass "All ${#REQUIRED_SKILLS[@]} agent skills present"
  fi
fi

# ═══════════════════════════════════════════════════════════
# Section 4 — Manuscript Orchestrator CLI (bf)
# ═══════════════════════════════════════════════════════════
if [[ "$NLM_ONLY" == false ]]; then
  print_header "4. Manuscript Orchestrator CLI (bf)"

  # Legacy orchestrator scripts have been removed; the unified `bf` CLI is now
  # the sole entry surface. Verify the key subcommands are registered.
  REQUIRED_CMDS=(
    "init" "status" "validate" "compile" "pacing" "packet"
    "run-loop" "resolve-unknowns" "canon" "apply" "memory" "checkpoint"
  )

  CMDS_FOUND=0
  for cmd in "${REQUIRED_CMDS[@]}"; do
    if bf "$cmd" --help >/dev/null 2>&1 || python3 -m bookforge.cli "$cmd" --help >/dev/null 2>&1; then
      ((CMDS_FOUND++)) || true
    else
      check_fail "Missing bf subcommand: bf $cmd"
    fi
  done

  if [[ $CMDS_FOUND -eq ${#REQUIRED_CMDS[@]} ]]; then
    check_pass "All ${#REQUIRED_CMDS[@]} bf subcommands available"
  fi
fi

# ═══════════════════════════════════════════════════════════
# Section 5 — Books Directory
# ═══════════════════════════════════════════════════════════
if [[ "$NLM_ONLY" == false ]]; then
  print_header "5. Books"

  BOOKS_DIR="$PROJ_ROOT/books"
  if [[ -d "$BOOKS_DIR" ]]; then
    BOOK_COUNT=$(find "$BOOKS_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l)
    if [[ $BOOK_COUNT -gt 0 ]]; then
      check_pass "$BOOK_COUNT book project(s) found in books/"
      # Check each book for a phase-0 file
      while IFS= read -r book_dir; do
        BOOK_NAME=$(basename "$book_dir")
        HAS_PHASE0=false
        if [[ -f "$book_dir/phase-0.md" ]] || ls "$book_dir/phase-0/"*.md &>/dev/null 2>&1; then
          HAS_PHASE0=true
        fi
        if [[ "$HAS_PHASE0" == true ]]; then
          check_pass "  books/$BOOK_NAME — phase-0 source found"
        else
          check_warn "  books/$BOOK_NAME — no phase-0.md or phase-0/*.md"
        fi
      done < <(find "$BOOKS_DIR" -mindepth 1 -maxdepth 1 -type d)
    else
      check_warn "No book projects in books/ yet"
    fi
  else
    check_fail "books/ directory missing"
  fi

  # docs/ present
  if [[ -d "$PROJ_ROOT/docs" ]]; then
    DOC_COUNT=$(find "$PROJ_ROOT/docs" -name "*.md" | wc -l)
    check_pass "docs/ present ($DOC_COUNT markdown files)"
  else
    check_warn "docs/ directory missing"
  fi
fi

# ═══════════════════════════════════════════════════════════
# Section 6 — Headroom (Context Compression)
# ═══════════════════════════════════════════════════════════
if [[ "$NLM_ONLY" == false ]]; then
  print_header "6. Headroom (Context Compression)"

  # 6a. Module importable
  HEADROOM_IMPORT=$(python3 -c "
from bookforge.core.headroom import compress_text, compress_local, HAS_OFFICIAL_HEADROOM
print('has_official=' + str(HAS_OFFICIAL_HEADROOM))
" 2>&1)
  if echo "$HEADROOM_IMPORT" | grep -q "has_official="; then
    check_pass "bookforge.core.headroom imports cleanly"
  else
    check_fail "bookforge.core.headroom import failed: $HEADROOM_IMPORT"
  fi

  # 6b. Local compressor produces output (zero-dependency fallback)
  LOCAL_CHECK=$(python3 -c "
from bookforge.core.headroom import compress_local
result = compress_local('Please make sure to check the horse. The following is a detailed report.')
print('ok' if result and 'Please make sure to' not in result else 'fail')
" 2>&1)
  if [[ "$LOCAL_CHECK" == "ok" ]]; then
    check_pass "Local compressor (compress_local) works — strips filler phrases"
  else
    check_fail "Local compressor malfunction: $LOCAL_CHECK"
  fi

  # 6c. Lock-line preservation
  LOCK_CHECK=$(python3 -c "
from bookforge.core.headroom import compress_text
text = '### Source Context Lock\n- **Source Anchor:** Ch1\nPlease make sure to read this.'
result = compress_text(text)
print('ok' if '### Source Context Lock' in result and '- **Source Anchor:** Ch1' in result else 'fail')
" 2>&1)
  if [[ "$LOCK_CHECK" == "ok" ]]; then
    check_pass "Lock-line preservation works — Source Context Lock not compressed"
  else
    check_fail "Lock-line preservation broken: $LOCK_CHECK"
  fi

  # 6d. Optional headroom-ai package
  HAS_OFFICIAL=$(python3 -c "
from bookforge.core.headroom import HAS_OFFICIAL_HEADROOM
print('yes' if HAS_OFFICIAL_HEADROOM else 'no')
" 2>&1)
  if [[ "$HAS_OFFICIAL" == "yes" ]]; then
    HEADROOM_VER=$(python3 -c "import headroom; print(getattr(headroom, '__version__', 'unknown'))" 2>/dev/null)
    check_pass "headroom-ai (optional) installed${HEADROOM_VER:+ (v$HEADROOM_VER)} — enhanced compression active"
  else
    check_warn "headroom-ai not installed (optional) — using local fallback compressor"
    echo "         Install: pip install headroom-ai"
  fi

  # 6e. Headroom unit tests
  if [[ "$QUICK" == true ]]; then
    check_skip "Headroom unit tests (--quick mode)"
  else
    if python3 -m pytest --version &>/dev/null 2>&1; then
      HR_OUT=$(python3 -m pytest "$PROJ_ROOT/tests/test_headroom.py" --tb=short -q 2>&1)
      HR_SUMMARY=$(echo "$HR_OUT" | grep -E "passed|failed|error" | tail -1)
      if echo "$HR_OUT" | grep -q "failed\|error"; then
        check_fail "Headroom tests: $HR_SUMMARY"
        echo "$HR_OUT" | grep -A5 "FAILED\|ERROR" | sed 's/^/         /'
      else
        check_pass "Headroom tests: $HR_SUMMARY"
      fi
    fi
  fi
fi

# ═══════════════════════════════════════════════════════════
# Section 7 — Test Suite
# ═══════════════════════════════════════════════════════════
if [[ "$NLM_ONLY" == false ]]; then
  print_header "7. Test Suite (Full)"

  if [[ "$QUICK" == true ]]; then
    check_skip "pytest (--quick mode)"
  else
    if command -v python3 &>/dev/null && python3 -m pytest --version &>/dev/null 2>&1; then
      echo "  Running pytest..."
      PYTEST_OUT=$(python3 -m pytest "$PROJ_ROOT/tests/" --tb=no -q 2>&1)
      PYTEST_SUMMARY=$(echo "$PYTEST_OUT" | grep -E "passed|failed|error" | tail -1)

      if echo "$PYTEST_OUT" | grep -q "failed\|error"; then
        FAILED=$(echo "$PYTEST_OUT" | grep -oE "[0-9]+ failed" | head -1)
        check_fail "pytest: $PYTEST_SUMMARY"
      else
        PASSED=$(echo "$PYTEST_OUT" | grep -oE "[0-9]+ passed" | head -1)
        check_pass "pytest: $PYTEST_SUMMARY"
      fi
    else
      check_warn "pytest not available — run: pip install pytest"
    fi
  fi
fi

# ═══════════════════════════════════════════════════════════
# Section 8 — NotebookLM MCP
# ═══════════════════════════════════════════════════════════
print_header "8. NotebookLM MCP"

# uv (needed for nlm)
if ! command -v uv &>/dev/null && [[ "$NLM_ONLY" == false ]]; then
  check_warn "uv missing — NotebookLM MCP cannot be installed"
fi

# Package installed
if command -v uv &>/dev/null && uv tool list 2>/dev/null | grep -q "notebooklm-mcp-cli"; then
  PKG_VER=$(uv tool list 2>/dev/null | grep "notebooklm-mcp-cli" | awk '{print $2}')
  check_pass "notebooklm-mcp-cli installed ($PKG_VER)"
else
  check_fail "notebooklm-mcp-cli not installed — run: bash scripts/setup-notebooklm-mcp.sh"
fi

# Executables
if command -v nlm &>/dev/null; then
  check_pass "nlm CLI on PATH ($(which nlm))"
else
  check_fail "nlm not on PATH — check ~/.local/bin in \$PATH"
fi

if command -v notebooklm-mcp &>/dev/null; then
  check_pass "notebooklm-mcp server on PATH"
else
  check_fail "notebooklm-mcp binary not on PATH"
fi

# Auth file
AUTH_FILE="$HOME/.notebooklm-mcp-cli/profiles/default/cookies.json"
if [[ -f "$AUTH_FILE" ]]; then
  check_pass "Auth cookies file found"
else
  check_fail "Auth file missing ($AUTH_FILE) — run: nlm login"
fi

# Live auth check
if command -v nlm &>/dev/null; then
  AUTH_STATUS=$(nlm login --check 2>&1)
  if echo "$AUTH_STATUS" | grep -qi "authenticated\|valid\|✓\|success"; then
    ACCOUNT=$(echo "$AUTH_STATUS" | grep -iE "account|email|@[a-z]" | head -1 | sed 's/^[[:space:]]*//')
    check_pass "Auth valid${ACCOUNT:+ — $ACCOUNT}"
  elif echo "$AUTH_STATUS" | grep -qi "expired\|invalid\|not auth\|stale"; then
    check_fail "Auth expired — run: nlm login"
  else
    check_warn "Auth status unclear — run 'nlm login --check' manually"
  fi
fi

# Antigravity MCP config
MCP_CONFIG="$HOME/.gemini/antigravity/mcp_config.json"
if [[ -f "$MCP_CONFIG" ]] && grep -q "notebooklm" "$MCP_CONFIG" 2>/dev/null; then
  check_pass "MCP registered in Antigravity config"
else
  check_fail "MCP not in Antigravity config — run: nlm setup add antigravity"
fi

# AI Skill
SKILL_FILE="$HOME/.gemini/antigravity/skills/nlm-skill/SKILL.md"
if [[ -f "$SKILL_FILE" ]]; then
  check_pass "NotebookLM AI skill installed (~/.gemini/antigravity/skills/nlm-skill/)"
else
  check_warn "AI skill not installed (optional) — run: nlm skill install antigravity"
fi

# ═══════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                      Summary                         ║"
echo "╠══════════════════════════════════════════════════════╣"

if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
  echo "║  ✅  All checks passed — project is fully set up.   ║"
elif [[ $ERRORS -eq 0 ]]; then
  printf "║  ⚠️   %d warning(s) — mostly OK, see above.%*s║\n" "$WARNINGS" $((18 - ${#WARNINGS})) ""
else
  printf "║  ❌  %d error(s), %d warning(s) — action needed.%*s║\n" "$ERRORS" "$WARNINGS" $((7 - ${#ERRORS} - ${#WARNINGS})) ""
fi

echo "╠══════════════════════════════════════════════════════╣"
echo "║  Fix errors:  bash scripts/setup-notebooklm-mcp.sh  ║"
echo "║  Run tests:   python3 -m pytest tests/ -q            ║"
echo "║  Quick mode:  bash scripts/check.sh --quick          ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
