#!/usr/bin/env python3
"""BookForge Context Budget Core Module."""

from __future__ import annotations

from pathlib import Path

MODES = ("planning", "drafting", "repair", "style", "validation", "expansion", "final")


def chapter_folder(book_folder: Path, slug: str | None) -> Path | None:
    if not slug:
        return None
    changes_path = book_folder / "changes" / slug
    if changes_path.exists():
        return changes_path
    return book_folder / "chapters" / slug


def chapter_draft(folder: Path, slug: str) -> Path:
    draft_options = ["draft.md", f"{slug}.md", "epilogue.md" if slug == "epilogue" else f"{slug}.md"]
    for opt in draft_options:
        p = folder / opt
        if p.exists():
            return p
    return folder / draft_options[0]


def source_file(book_folder: Path) -> Path:
    from bookforge.core.scanner import source_path
    path = source_path(book_folder)
    return path if path else book_folder / "phase-0.md"


def mode_files(book_folder: Path, slug: str | None, mode: str) -> tuple[list[Path], list[str]]:
    folder = chapter_folder(book_folder, slug)
    chapter_files = []
    if folder and slug:
        proposal_path = folder / "proposal.md"
        scene_bd_path = folder / "scene-breakdown.md"
        scene_breakdown = proposal_path if proposal_path.exists() or not scene_bd_path.exists() else scene_bd_path

        chapter_files = [
            folder / "context-packet.md",
            scene_breakdown,
            chapter_draft(folder, slug),
        ]


    if mode == "planning":
        return (
            [
                source_file(book_folder),
                book_folder / "rulebook.md",
                book_folder / "mood-lock.md",
                book_folder / "chapter-summaries.md",
                book_folder / "chapter-pacing-plan.md",
            ],
            ["chapter drafts", "full manuscript compilation"],
        )
    if mode == "drafting":
        return (
            chapter_files,
            ["full rulebook", "full manuscript", "unrelated chapter drafts"],
        )
    if mode == "repair":
        return (
            chapter_files + ([book_folder / "rulebook.md"] if not (folder and (folder / "context-packet.md").exists()) else []),
            ["full manuscript", "unrelated chapters", "fresh expansion before repair"],
        )
    if mode == "style":
        return (
            chapter_files + [Path(".agents/skills/western-manuscript-style/references/style-lock.md")],
            ["phase source unless checking facts", "full rulebook unless style issue depends on facts"],
        )
    if mode == "validation":
        return (
            [
                source_file(book_folder),
                book_folder / "rulebook.md",
                book_folder / "mood-lock.md",
                book_folder / "chapter-summaries.md",
            ]
            + chapter_files,
            ["full manuscript unless final cross-chapter review is requested"],
        )
    if mode == "expansion":
        return (
            chapter_files
            + ([book_folder / "chapter-pacing-plan.md"] if (book_folder / "chapter-pacing-plan.md").exists() else [])
            + ([folder / "continuity-out.md"] if folder else []),
            ["new story sources", "full manuscript", "fixed scene or beat word targets"],
        )
    return (
        [
            book_folder / "rulebook.md",
            book_folder / "mood-lock.md",
            book_folder / "chapter-summaries.md",
            book_folder / "chapters",
        ],
        ["source rebuilding prompts", "new unsupported story material"],
    )


def render_report(book_folder: Path, slug: str | None, mode: str) -> str:
    files, avoid = mode_files(book_folder, slug, mode)
    lines = [
        "# Context Budget Report",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Mode:** `{mode}`",
        f"- **Chapter:** `{slug or 'not chapter-specific'}`",
        "",
        "## Recommended Context",
        "",
    ]
    for path in files:
        status = "exists" if path.exists() else "missing"
        lines.append(f"- `{path}` ({status})")
    lines.extend(["", "## Avoid Loading", ""])
    lines.extend(f"- {item}" for item in avoid)
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "- Load the smallest source set that can complete the current mode.",
            "- Build or refresh the chapter's `context-packet.md` using the task-specific parameters:",
            "  * Drafting, Repair, or Expansion: run `bf packet --task draft-prose`",
            "  * Style check: run `bf packet --task revise-style`",
            "  * Validation check: run `bf packet --task validate-change`",
            "  * Continuity validation: run `bf packet --task continuity-check`",
            "  * Memory extraction: run `bf packet --task extract-memory`",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Check recommended manuscript context loading.")
    parser.add_argument("book_folder", help="Book folder such as books/book-example.")
    parser.add_argument("--chapter", help="Chapter slug such as chapter-01 or epilogue.")
    parser.add_argument("--mode", required=True, choices=MODES, help="Prompt mode to budget for.")
    args = parser.parse_args()
    book_folder = Path(args.book_folder)

    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    if args.mode != "planning" and args.mode != "final" and not args.chapter:
        print("Error: --chapter is required for this mode.", file=sys.stderr)
        return 2
    print(render_report(book_folder, args.chapter, args.mode))
    return 0
