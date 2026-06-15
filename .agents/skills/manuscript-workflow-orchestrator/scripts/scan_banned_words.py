#!/usr/bin/env python3
"""Standalone banned-word and style scanner.

Faster feedback than running the full validator. Run against a single file or
a whole book folder to see all style violations with exact line numbers.

Usage:
    python scan_banned_words.py books/tex-cade/chapters/chapter-08/chapter-08.md
    python scan_banned_words.py books/tex-cade
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import validate_manuscript_context as validator  # noqa: E402


# ---------------------------------------------------------------------------
# Violation categories
# ---------------------------------------------------------------------------

CATEGORIES: list[tuple[str, list[str]]] = [
    ("BANNED WORD", validator.BANNED_AI_ECHO_WORDS),
    ("MODERN TERM", validator.MODERN_OR_CLINICAL_WORDS),
    ("INTERNAL MONO", validator.INTERNAL_MONOLOGUE_PHRASES),
    ("UNRESOLVED", validator.UNRESOLVED_MARKERS),
]

ING_OPENER_RE = re.compile(r"^([A-Z][a-z]{5,}ing)[\s,]")
DIALOGUE_TAG_RE = validator.DIALOGUE_TAG_RE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan draft files for Western style violations with line numbers."
    )
    parser.add_argument(
        "target",
        help="A single .md draft file or a book folder to scan all chapter drafts.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output.",
    )
    return parser.parse_args()


def find_draft_files(target: Path) -> list[Path]:
    """Return draft .md files from a single file or a book folder's chapters."""
    if target.is_file():
        return [target]
    chapters_root = target / "chapters"
    if not chapters_root.exists():
        return []
    drafts: list[Path] = []
    for chapter_dir in sorted(chapters_root.iterdir(), key=validator.chapter_sort_key):
        if not chapter_dir.is_dir():
            continue
        if chapter_dir.name == "epilogue":
            candidate = chapter_dir / "epilogue.md"
        else:
            candidate = chapter_dir / f"{chapter_dir.name}.md"
        if candidate.exists():
            drafts.append(candidate)
    return drafts


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return (line_number, category, excerpt) for each violation found."""
    violations: list[tuple[int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return violations

    for line_num, line in enumerate(lines, start=1):
        lower = line.lower()
        stripped = line.strip()

        # Check each term category
        for category, terms in CATEGORIES:
            for term in terms:
                if term.lower() in lower:
                    violations.append((line_num, category, stripped[:120]))
                    break

        # Dialogue tags
        if DIALOGUE_TAG_RE.search(line):
            violations.append((line_num, "DIALOGUE TAG", stripped[:120]))

        # -ing opener
        if ING_OPENER_RE.match(stripped):
            violations.append((line_num, "ING OPENER", stripped[:120]))

    return violations


def render(path: Path, violations: list[tuple[int, str, str]], use_color: bool) -> list[str]:
    if not violations:
        return []
    lines: list[str] = []
    for line_num, category, excerpt in violations:
        tag = f"[{category}]"
        if use_color:
            tag = f"\033[33m{tag}\033[0m"
        lines.append(f"  {path.name}:{line_num:<5} {tag:<22} — {excerpt}")
    return lines


def main() -> int:
    args = parse_args()
    use_color = not args.no_color and sys.stdout.isatty()
    target = Path(args.target)

    if not target.exists():
        print(f"Error: path not found: {target}", file=sys.stderr)
        return 2

    draft_files = find_draft_files(target)
    if not draft_files:
        print(f"No draft files found at: {target}", file=sys.stderr)
        return 2

    total_violations = 0
    for draft_path in draft_files:
        violations = scan_file(draft_path)
        if violations:
            header = str(draft_path)
            if use_color:
                header = f"\033[1m{header}\033[0m"
            print(header)
            for line in render(draft_path, violations, use_color):
                print(line)
            print()
            total_violations += len(violations)

    if total_violations == 0:
        print(f"Clean — no style violations found in {len(draft_files)} draft file(s).")
        return 0

    print(f"Found {total_violations} violation(s) across {len(draft_files)} draft file(s).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
