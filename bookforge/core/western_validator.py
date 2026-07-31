from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class ValidationMode(Enum):
    OUTLINE = "outline"
    SCENE = "scene"
    CHAPTER = "chapter"
    MANUSCRIPT = "manuscript"
    DIALOGUE = "dialogue"
    HISTORICAL = "historical"


MODE_REFERENCES: dict[ValidationMode, list[str]] = {
    ValidationMode.OUTLINE: [
        "validation-modes.md",
        "story-logic-and-causality.md",
        "scene-chapter-and-pacing.md",
        "western-tone-and-subgenres.md",
        "historical-authenticity.md",
        "continuity-outlines-and-scoring.md",
    ],
    ValidationMode.SCENE: [
        "validation-modes.md",
        "scene-chapter-and-pacing.md",
        "character-dialogue-and-prose.md",
        "western-tone-and-subgenres.md",
        "story-logic-and-causality.md",
    ],
    ValidationMode.CHAPTER: [
        "validation-modes.md",
        "scene-chapter-and-pacing.md",
        "character-dialogue-and-prose.md",
        "western-tone-and-subgenres.md",
        "story-logic-and-causality.md",
        "continuity-outlines-and-scoring.md",
    ],
    ValidationMode.MANUSCRIPT: [
        "validation-modes.md",
        "story-logic-and-causality.md",
        "scene-chapter-and-pacing.md",
        "character-dialogue-and-prose.md",
        "western-tone-and-subgenres.md",
        "continuity-outlines-and-scoring.md",
        "historical-authenticity.md",
    ],
    ValidationMode.DIALOGUE: [
        "validation-modes.md",
        "character-dialogue-and-prose.md",
        "western-tone-and-subgenres.md",
    ],
    ValidationMode.HISTORICAL: [
        "validation-modes.md",
        "historical-authenticity.md",
        "western-tone-and-subgenres.md",
    ],
}


def _references_dir() -> Path:
    root = Path(__file__).resolve().parent.parent.parent
    return root / ".agents" / "skills" / "western-manuscript-validator" / "references"


def _find_book_folder(path: Path) -> Path | None:
    for parent in [path] + list(path.parents):
        if (parent / "rulebook.md").exists() and (parent / "chapters").is_dir():
            return parent
    return None


def _find_chapter_folder(path: Path) -> Path | None:
    if re.match(r"^chapter-\d+$", path.name) and path.is_dir():
        return path
    return None


def determine_mode(path: Path, mode_arg: str | None = None) -> tuple[ValidationMode, str]:
    if mode_arg:
        try:
            return ValidationMode(mode_arg.lower()), f"User-specified mode: {mode_arg}"
        except ValueError:
            pass

    path = path.resolve()

    if not path.exists():
        return ValidationMode.MANUSCRIPT, "Path not found; defaulting to manuscript mode."

    if path.is_file():
        content = path.read_text(encoding="utf-8")
        name_lower = path.name.lower()
        if "dialogue" in name_lower or "dialog" in name_lower:
            return ValidationMode.DIALOGUE, "Detected dialogue file from filename."
        if any(kw in name_lower for kw in ["outline", "phase-0", "phase-00"]):
            return ValidationMode.OUTLINE, "Detected outline file from filename."
        if "historical" in name_lower or "history" in name_lower:
            return ValidationMode.HISTORICAL, "Detected historical file from filename."

    if path.is_dir():
        chapter_folder = _find_chapter_folder(path)
        if chapter_folder:
            draft = _find_draft(chapter_folder)
            scene = chapter_folder / "scene-breakdown.md"
            if scene.exists():
                return ValidationMode.SCENE, f"Chapter folder with scene-breakdown: {chapter_folder.name}"
            if draft and draft.exists():
                return ValidationMode.CHAPTER, f"Chapter folder with draft: {chapter_folder.name}"
            return ValidationMode.SCENE, f"Chapter folder: {chapter_folder.name}"

        book_folder = _find_book_folder(path)
        if book_folder:
            phase = _find_phase_source(book_folder)
            if path == phase or (phase and path.parent == book_folder):
                return ValidationMode.OUTLINE, "Outline source file in book folder."
            chapters_root = book_folder / "chapters"
            if chapters_root.is_dir():
                chapter_dirs = [d for d in chapters_root.iterdir() if d.is_dir() and re.match(r"^chapter-\d+$", d.name)]
                if len(chapter_dirs) >= 1:
                    return ValidationMode.MANUSCRIPT, f"Book folder with {len(chapter_dirs)} chapters."
            return ValidationMode.MANUSCRIPT, "Book folder (minimal structure)."

    return ValidationMode.MANUSCRIPT, "Defaulting to manuscript mode."


def _find_draft(chapter_folder: Path) -> Path | None:
    slug = chapter_folder.name
    draft = chapter_folder / f"{slug}.md"
    if draft.exists():
        return draft
    return None


def _find_phase_source(book_folder: Path) -> Path | None:
    for name in ["phase-0.md", "phase-00.md", "outline.md", "chapter-outline.md"]:
        p = book_folder / name
        if p.exists():
            return p
    return None


def load_reference(name: str) -> str:
    ref_path = _references_dir() / name
    if not ref_path.exists():
        return f"Reference not found: {name}"
    return ref_path.read_text(encoding="utf-8")


def references_for_mode(mode: ValidationMode) -> list[str]:
    return MODE_REFERENCES.get(mode, MODE_REFERENCES[ValidationMode.MANUSCRIPT])


def available_references() -> list[str]:
    ref_dir = _references_dir()
    if not ref_dir.exists():
        return []
    return sorted(f.name for f in ref_dir.iterdir() if f.suffix == ".md")


def _collect_content(path: Path, mode: ValidationMode) -> dict[str, str]:
    content: dict[str, str] = {}
    path = path.resolve()

    if mode == ValidationMode.OUTLINE:
        if path.is_file():
            content["source"] = path.read_text(encoding="utf-8")
        elif path.is_dir():
            src = _find_phase_source(path) or _find_phase_source(_find_book_folder(path) or path)
            if src:
                content["source"] = src.read_text(encoding="utf-8")
            else:
                content["source"] = "No outline file found."

    elif mode in (ValidationMode.SCENE, ValidationMode.CHAPTER):
        chapter_folder = _find_chapter_folder(path) or path
        if chapter_folder.is_dir():
            scene = chapter_folder / "scene-breakdown.md"
            if scene.exists():
                content["scene_breakdown"] = scene.read_text(encoding="utf-8")
            draft = _find_draft(chapter_folder)
            if draft:
                content["draft"] = draft.read_text(encoding="utf-8")
            continuity = chapter_folder / "continuity-out.md"
            if continuity.exists():
                content["continuity_out"] = continuity.read_text(encoding="utf-8")
            # Book-level context
            book_folder = _find_book_folder(path)
            if book_folder:
                for fname in ["rulebook.md", "mood-lock.md", "chapter-summaries.md"]:
                    fp = book_folder / fname
                    if fp.exists():
                        content[fname.replace(".md", "")] = fp.read_text(encoding="utf-8")
        if path.is_file():
            ext = path.suffix.lower()
            if ext == ".md":
                content["file"] = path.read_text(encoding="utf-8")
            elif ext in (".json", ".yaml", ".yml", ".txt"):
                content["file"] = path.read_text(encoding="utf-8")

    elif mode == ValidationMode.MANUSCRIPT:
        if path.is_dir():
            book_folder = _find_book_folder(path) or path
            for fname in ["rulebook.md", "mood-lock.md", "chapter-summaries.md", "series-bible.md"]:
                fp = book_folder / fname
                if fp.exists():
                    content[fname.replace(".md", "")] = fp.read_text(encoding="utf-8")
            chapters_root = book_folder / "chapters"
            if chapters_root.is_dir():
                chapter_drafts: dict[str, str] = {}
                for d in sorted(chapters_root.iterdir()):
                    if d.is_dir() and re.match(r"^chapter-\d+$|^epilogue$", d.name):
                        draft = _find_draft(d)
                        if draft:
                            chapter_drafts[d.name] = draft.read_text(encoding="utf-8")
                if chapter_drafts:
                    content["drafts"] = "\n\n---\n\n".join(
                        f"### {slug}\n{draft}" for slug, draft in chapter_drafts.items()
                    )
                scene_breakdowns: dict[str, str] = {}
                for d in sorted(chapters_root.iterdir()):
                    if d.is_dir() and re.match(r"^chapter-\d+$|^epilogue$", d.name):
                        sb = d / "scene-breakdown.md"
                        if sb.exists():
                            scene_breakdowns[d.name] = sb.read_text(encoding="utf-8")
                if scene_breakdowns:
                    content["scene_breakdowns"] = "\n\n---\n\n".join(
                        f"### {slug}\n{sb}" for slug, sb in scene_breakdowns.items()
                    )
        elif path.is_file():
            content["file"] = path.read_text(encoding="utf-8")

    elif mode == ValidationMode.DIALOGUE:
        if path.is_file():
            content["file"] = path.read_text(encoding="utf-8")

    elif mode == ValidationMode.HISTORICAL:
        if path.is_file():
            content["file"] = path.read_text(encoding="utf-8")
        elif path.is_dir():
            book_folder = _find_book_folder(path) or path
            for fname in ["series-research-pack.md", "research-pack.md"]:
                fp = book_folder / fname
                if fp.exists():
                    content[fname.replace(".md", "")] = fp.read_text(encoding="utf-8")

    return content


def build_validation_packet(path: Path, mode: ValidationMode | None = None) -> str:
    path = path.resolve()
    resolved_mode, mode_reason = determine_mode(path, mode.value if mode else None)

    content = _collect_content(path, resolved_mode)
    ref_names = references_for_mode(resolved_mode)

    ref_sections: list[str] = []
    for name in ref_names:
        text = load_reference(name)
        ref_sections.append(f"## Reference: {name}\n\n{text}")

    target_desc = f"**Path:** `{path}`"
    if path.is_file():
        target_desc += f"\n**Size:** {path.stat().st_size} bytes"
    elif path.is_dir():
        items = [p.name for p in path.iterdir()]
        target_desc += f"\n**Contents:** {', '.join(items[:20])}"
        if len(items) > 20:
            target_desc += f" … and {len(items) - 20} more"

    content_sections: list[str] = []
    for key, text in content.items():
        words = len(text.split())
        label = key.replace("_", " ").title()
        content_sections.append(f"## {label}\n\n{text}\n\n[*{words} words*]")

    lines = [
        "# Western Manuscript Validation Packet",
        "",
        "## Target Promise",
        "",
        target_desc,
        "",
        f"**Mode:** `{resolved_mode.value}`",
        "",
        f"**Mode Reason:** {mode_reason}",
        "",
        "**References Loaded:**",
    ]
    for name in ref_names:
        lines.append(f"- `{name}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Validation Criteria")
    lines.append("")
    lines.extend(ref_sections)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Content to Validate")
    lines.append("")
    if content_sections:
        lines.extend(content_sections)
    else:
        lines.append("No content found to validate.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("# Validation Report (fill below)")
    lines.append("")
    lines.append("## Target Promise")
    lines.append("")
    lines.append("- **Year/Period:** ")
    lines.append("- **Region:** ")
    lines.append("- **Subgenre:** ")
    lines.append("- **Series Position:** ")
    lines.append("- **Function:** ")
    lines.append("- **Pacing Register:** ")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append("**Verdict:** Good to go | Good with minor repairs | Needs focused revision | Needs structural revision | Not ready")
    lines.append("")
    lines.append("## Problems Found")
    lines.append("")
    lines.append("| # | Layer | Severity | Location | Problem |")
    lines.append("|---|-------|----------|----------|---------|")
    lines.append("|   |       |          |          |         |")
    lines.append("")
    lines.append("## What Changed")
    lines.append("")
    lines.append("## Logic and Continuity Flags")
    lines.append("")
    lines.append("## Historical Authenticity Flags")
    lines.append("")
    lines.append("## Repairs Prescribed")
    lines.append("")
    lines.append("| # | Location | Problem | Repair |")
    lines.append("|---|----------|---------|--------|")
    lines.append("|   |          |         |        |")
    lines.append("")
    lines.append("## Bottom Line")
    lines.append("")

    return "\n".join(lines)


def validate(path: Path, mode: ValidationMode | None = None) -> str:
    packet = build_validation_packet(path, mode)
    return (
        "# Western Manuscript Validation\n\n"
        f"# Western Manuscript Validation: {path.resolve().name}\n\n"
        f"Validation packet built. OpenCode skill loaded.\n\n"
        f"---\n\n{packet}"
    )


def cmd_validate_western(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"Error: path not found: {path}", file=sys.stderr)
        return 2

    mode = None
    if args.mode:
        try:
            mode = ValidationMode(args.mode.lower())
        except ValueError:
            valid = ", ".join(m.value for m in ValidationMode)
            print(f"Error: invalid mode '{args.mode}'. Valid: {valid}", file=sys.stderr)
            return 2

    output = validate(path, mode)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(output, encoding="utf-8")
        print(f"Wrote validation packet to {out_path}")
    else:
        print(output)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Western fiction against the western-manuscript-validator skill criteria."
    )
    parser.add_argument("path", help="Path to book folder, chapter folder, or file to validate.")
    parser.add_argument(
        "--mode",
        choices=[m.value for m in ValidationMode],
        help="Validation mode (auto-detected if omitted).",
    )
    parser.add_argument("--output", "-o", help="Write validation packet to file instead of stdout.")
    args = parser.parse_args()
    return cmd_validate_western(args)


if __name__ == "__main__":
    sys.exit(main())
