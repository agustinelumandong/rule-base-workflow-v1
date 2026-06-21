"""Interactive Q&A Wizard and write-back functionality for Unknowns."""

from __future__ import annotations

import sys
from pathlib import Path

from bookforge.core.unknowns.parser import (
    _find_section_bounds,
    _BULLET_RE,
    parse_unknowns,
    read_book_context,
)
from bookforge.core.unknowns.engine import suggest


def _ensure_resolved_section(text: str) -> str:
    """Add ## Resolved Unknowns section if it doesn't exist yet."""
    if "## Resolved Unknowns" in text:
        return text
    return text.rstrip() + "\n\n## Resolved Unknowns\n\n"


def write_resolved_answer(rulebook_path: Path, question: str, answer: str) -> None:
    """Append a Q/A pair to ## Resolved Unknowns and remove the item from ## Unknowns."""
    text = rulebook_path.read_text(encoding="utf-8")

    # 1. Remove the bullet from ## Unknowns
    _, body_start, body_end = _find_section_bounds(text, ("Unknowns",))
    if body_start != -1:
        section_body = text[body_start:body_end]
        new_body_lines = []
        for line in section_body.splitlines(keepends=True):
            m = _BULLET_RE.match(line.rstrip("\n"))
            if m and m.group(1).strip() == question:
                continue  # drop this bullet
            new_body_lines.append(line)
        text = text[:body_start] + "".join(new_body_lines) + text[body_end:]

    # 2. Ensure ## Resolved Unknowns exists
    text = _ensure_resolved_section(text)

    # 3. Append the Q/A pair inside the resolved section
    _, body_start2, body_end2 = _find_section_bounds(text, ("Resolved Unknowns",))
    if body_start2 != -1:
        qa_block = f"- **Q:** {question}\n  - **A:** {answer}\n"
        existing_body = text[body_start2:body_end2]
        new_body = existing_body.rstrip() + "\n" + qa_block
        text = text[:body_start2] + new_body + text[body_end2:]

    rulebook_path.write_text(text, encoding="utf-8")


def check_unknowns(book_folder: Path) -> list[str]:
    """Return a list of failure strings if unresolved Unknowns items exist."""
    rulebook_path = book_folder / "rulebook.md"
    if not rulebook_path.exists():
        return []

    text = rulebook_path.read_text(encoding="utf-8")
    items = parse_unknowns(text)
    if not items:
        return []

    failures: list[str] = []
    for item in items:
        failures.append(
            f"Rulebook `## Unknowns` has unresolved item: \"{item}\" — "
            f"run `bf resolve-unknowns <book_folder>` to answer it before proceeding."
        )
    return failures


_DIVIDER = "  " + "─" * 58


def _print_header(total: int) -> None:
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║      BookForge — Unknowns Resolver Wizard                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\n  Found {total} unresolved item(s) in rulebook.md → ## Unknowns.")
    print("  Pick a suggestion (1–3), enter 4 for a custom answer,")
    print("  or type SKIP to leave an item unresolved.")
    print("  Press Ctrl+C at any time to abort without saving.\n")


def _prompt_choice(item: str, choices: list[str], idx: int, total: int) -> str | None:
    """Present the question with numbered choices. Returns the final answer string,
    or None if skipped, or raises KeyboardInterrupt to abort.
    """
    print(_DIVIDER)
    print(f"  [{idx}/{total}] UNKNOWN: {item}\n")
    for n, choice in enumerate(choices, start=1):
        words = choice.split()
        lines: list[str] = []
        line: list[str] = []
        length = 0
        for word in words:
            if length + len(word) + 1 > 72:
                lines.append(" ".join(line))
                line = [word]
                length = len(word)
            else:
                line.append(word)
                length += len(word) + 1
        if line:
            lines.append(" ".join(line))
        first_line = lines[0]
        rest = lines[1:]
        print(f"    {n}. {first_line}")
        for l in rest:
            print(f"       {l}")
        print()
    print(f"    4. What's on your mind? (type your own answer)")
    print()

    while True:
        try:
            raw = input("  Choose [1–4] or SKIP: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt

        if raw.upper() == "SKIP" or raw == "":
            return None  # skip

        if raw in ("1", "2", "3"):
            answer = choices[int(raw) - 1]
            print(f"\n  ✓ Selected: {answer[:80]}{'...' if len(answer) > 80 else ''}\n")
            return answer

        if raw == "4":
            try:
                custom = input("  Your answer: ").strip()
            except (EOFError, KeyboardInterrupt):
                raise KeyboardInterrupt
            if not custom:
                print("  (empty — treated as SKIP)\n")
                return None
            print(f"\n  ✓ Custom answer recorded.\n")
            return custom

        print("  Please enter 1, 2, 3, 4, or SKIP.\n")


def run_unknowns_wizard(book_folder: Path) -> int:
    """Interactively resolve all unresolved Unknowns in the rulebook.

    Returns 0 if all resolved, 1 if any remain unresolved.
    """
    rulebook_path = book_folder / "rulebook.md"
    if not rulebook_path.exists():
        print(f"Error: rulebook.md not found in '{book_folder}'.", file=sys.stderr)
        return 1

    text = rulebook_path.read_text(encoding="utf-8")
    unknowns = parse_unknowns(text)

    if not unknowns:
        print("✓ No unresolved Unknowns found in rulebook.md — pipeline is clear to proceed.")
        return 0

    ctx = read_book_context(text)
    _print_header(len(unknowns))

    resolved_count = 0
    skipped: list[str] = []

    for idx, item in enumerate(unknowns, start=1):
        choices = suggest(item, ctx)
        try:
            answer = _prompt_choice(item, choices, idx, len(unknowns))
        except KeyboardInterrupt:
            print("\n\n  Aborted. No changes saved.")
            return 1

        if answer is None:
            skipped.append(item)
            print("  → Skipped.\n")
            continue

        write_resolved_answer(rulebook_path, item, answer)
        resolved_count += 1

    print(_DIVIDER)
    print(f"\n  Summary: {resolved_count} resolved, {len(skipped)} skipped.")

    if skipped:
        print("\n  The following items remain unresolved (pipeline still blocked):")
        for item in skipped:
            print(f"    • {item}")
    else:
        print("\n  ✓ All Unknowns resolved. The pipeline is now clear to proceed.")

    return 0 if not skipped else 1
