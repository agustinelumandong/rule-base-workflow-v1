#!/usr/bin/env python3
"""Shim delegate for check_manuscript_length.py to bookforge package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("WARNING: This script is deprecated. Please use 'bf validate' instead.", file=sys.stderr)

from bookforge.core.length import *

if __name__ == "__main__":
    raise SystemExit(main())
