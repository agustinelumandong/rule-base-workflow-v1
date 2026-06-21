#!/usr/bin/env bash
# =============================================================================
# Legacy Project Install / Repair Script — Delegating to scripts/install.py
# =============================================================================

echo "WARNING: scripts/install.sh is deprecated. Delegating to scripts/install.py..." >&2

# Determine python command
PYTHON_CMD="python3"
if ! command -v python3 &>/dev/null; then
    if command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        echo "Error: Python is not installed or not in PATH." >&2
        exit 1
    fi
fi

exec "$PYTHON_CMD" "$(dirname "$0")/install.py" "$@"
