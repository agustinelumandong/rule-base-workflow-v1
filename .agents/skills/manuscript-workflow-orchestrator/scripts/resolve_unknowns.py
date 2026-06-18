#!/usr/bin/env python3
"""Shim delegate for resolve_unknowns.py to bookforge package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bookforge.core.unknowns import *

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Interactive wizard to resolve rulebook Unknowns.")
    parser.add_argument("book_folder", nargs="?", default="books/tex-cade", help="Path to book folder.")
    args = parser.parse_args()
    raise SystemExit(run_unknowns_wizard(Path(args.book_folder)))
