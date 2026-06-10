#!/usr/bin/env python3
"""Create an elastic chapter pacing plan for a manuscript folder."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from scan_source_format import first_target


SOURCE_NAMES = ("phase-0.md", "phase-00.md", "outline.md", "chapter-outline.md")
CHAPTER_RE = re.compile(r"chapter-(\d+)", re.IGNORECASE)

CLASS_RANGES = {
    "lean": "~900 (roughly 700-1200 when source-supported)",
    "standard": "~1600 (roughly 1300-1900 when source-supported)",
    "expanded": "~2200 (roughly 1900-2600 when source-supported)",
    "major": "~2900 (roughly 2500-3400 when source-supported)",
    "epilogue/teaser": "~600 (roughly 300-900 when source-supported)",
}

MAJOR_TERMS = {
    "climax",
    "climactic",
    "showdown",
    "siege",
    "battle",
    "duel",
}
EXPANDED_TERMS = {
    "attack",
    "ambush",
    "assault",
    "confrontation",
    "raid",
    "reveal",
    "rescue",
    "betrayal",
    "hostage",
    "escape",
    "gunfight",
    "firefight",
    "wounded",
    "death",
    "moral",
    "pressure",
}
LEAN_TERMS = {
    "setup",
    "aftermath",
    "farewell",
    "departure",
    "epilogue",
    "teaser",
    "transition",
    "arrival",
}


@dataclass(frozen=True)
class ChapterPacing:
    slug: str
    label: str
    pacing_class: str
    elastic_range: str
    reason: str
    beat_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a source-locked chapter pacing plan.")
    parser.add_argument("book_folder", help="Book folder such as books/tex-cade.")
    parser.add_argument(
        "--reference-analysis",
        default="references/timber/analysis/pacing-calibration.md",
        help="Optional reference pacing calibration file.",
    )
    return parser.parse_args()


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def source_path(book_folder: Path) -> Path | None:
    for name in SOURCE_NAMES:
        path = book_folder / name
        if path.exists():
            return path
    return None


def chapter_number(slug: str) -> int | None:
    match = CHAPTER_RE.search(slug)
    return int(match.group(1)) if match else None


def chapter_sort_key(path: Path) -> tuple[int, str]:
    if path.name == "epilogue":
        return (999, path.name)
    number = chapter_number(path.name)
    return (number if number is not None else 998, path.name)


def chapter_label(slug: str) -> str:
    if slug == "epilogue":
        return "Epilogue"
    number = chapter_number(slug)
    return f"Chapter {number}" if number is not None else slug


def chapter_patterns(slug: str) -> list[re.Pattern[str]]:
    if slug == "epilogue":
        return [re.compile(r"\bEpilogue\b", re.IGNORECASE)]
    number = chapter_number(slug)
    if number is None:
        return [re.compile(re.escape(slug), re.IGNORECASE)]
    return [
        re.compile(rf"\bChapter\s+{number}\b", re.IGNORECASE),
        re.compile(rf"\bChapter\s+{number:02d}\b", re.IGNORECASE),
        re.compile(re.escape(slug), re.IGNORECASE),
    ]


def extract_heading_section(text: str, slug: str) -> str:
    headings = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", text, re.MULTILINE))
    patterns = chapter_patterns(slug)
    for index, heading in enumerate(headings):
        title = heading.group(2)
        if not any(pattern.search(title) for pattern in patterns):
            continue
        level = len(heading.group(1))
        end = len(text)
        for next_heading in headings[index + 1 :]:
            if len(next_heading.group(1)) <= level:
                end = next_heading.start()
                break
        return text[heading.start() : end].strip()
    return ""


def chapters(book_folder: Path) -> list[Path]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        return []
    return [path for path in sorted(chapters_root.iterdir(), key=chapter_sort_key) if path.is_dir()]


def count_beats(scene_breakdown: str) -> int:
    return len(re.findall(r"^##\s+BEAT\b", scene_breakdown, re.MULTILINE | re.IGNORECASE))


def has_any(text: str, terms: set[str]) -> list[str]:
    lower = text.lower()
    return [term for term in sorted(terms) if re.search(rf"\b{re.escape(term)}\b", lower)]


def classify(slug: str, combined_text: str, beat_count: int) -> tuple[str, str]:
    if slug == "epilogue":
        return "epilogue/teaser", "epilogue or teaser material should stay lean unless source demands more closure"
    major_hits = has_any(combined_text, MAJOR_TERMS)
    expanded_hits = has_any(combined_text, EXPANDED_TERMS)
    lean_hits = has_any(combined_text, LEAN_TERMS)
    if major_hits:
        return "major", "source includes major pressure: " + ", ".join(major_hits[:4])
    if expanded_hits or beat_count >= 7:
        reason = "source supports expanded treatment"
        if expanded_hits:
            reason += ": " + ", ".join(expanded_hits[:4])
        if beat_count >= 7:
            reason += f"; {beat_count} beat sections"
        return "expanded", reason
    if lean_hits and beat_count <= 2:
        return "lean", "source appears lean: " + ", ".join(lean_hits[:4])
    return "standard", "source supports normal chapter treatment without forced expansion"


def expansion_permission(pacing_class: str) -> str:
    if pacing_class == "lean":
        return "Add only necessary setup, aftermath, transition, or consequence."
    if pacing_class == "standard":
        return "Add source-supported action, dialogue pressure, setting texture, and transitions."
    if pacing_class == "expanded":
        return "Deepen approved conflict, consequence, tactical movement, and emotional pressure."
    if pacing_class == "major":
        return "Allow the longest treatment only for approved climax, rescue, siege, reversal, or confrontation beats."
    return "Keep closure compact unless the source requires a longer handoff."


def source_scan_status(book_folder: Path) -> str:
    scan_path = book_folder / "source-format-scan.md"
    if not scan_path.exists():
        return "No source-format-scan.md found; run scan_source_format.py before planning when possible."
    scan_text = read_optional(scan_path)
    if "Individual Chapter Word Counts:** present" in scan_text:
        return "Loaded source-format-scan.md; source contains individual chapter word-count guidance."
    return "Loaded source-format-scan.md; source does not appear to contain individual chapter word counts."


def chapter_word_guidance(text: str) -> str | None:
    target = first_target(text)
    if not target:
        return None
    words, evidence = target
    return f"source suggests ~{words:,} words from `{evidence}` (elastic guidance only; do not force)"


def build_plan(book_folder: Path, reference_analysis: Path) -> str:
    src = source_path(book_folder)
    if src is None:
        raise RuntimeError("Missing phase-0.md, phase-00.md, outline.md, or chapter-outline.md.")
    chapter_folders = chapters(book_folder)
    if not chapter_folders:
        raise RuntimeError("Missing chapters folder or chapter subfolders.")

    source_text = read_optional(src)
    summaries = read_optional(book_folder / "chapter-summaries.md")
    reference_note = read_optional(reference_analysis)
    reference_status = (
        f"Loaded optional reference analysis from `{reference_analysis}`."
        if reference_note
        else f"No optional reference analysis found at `{reference_analysis}`."
    )
    scan_status = source_scan_status(book_folder)

    pacing: list[ChapterPacing] = []
    for folder in chapter_folders:
        slug = folder.name
        scene = read_optional(folder / "scene-breakdown.md")
        summary_section = extract_heading_section(summaries, slug)
        source_section = extract_heading_section(source_text, slug)
        source_scope = "\n\n".join([source_section, summary_section]).strip()
        combined = "\n\n".join([source_scope, scene])
        beat_count = count_beats(scene)
        pacing_class, reason = classify(slug, source_scope or combined, beat_count)
        elastic_range = chapter_word_guidance(source_section) or CLASS_RANGES[pacing_class]
        pacing.append(
            ChapterPacing(
                slug=slug,
                label=chapter_label(slug),
                pacing_class=pacing_class,
                elastic_range=elastic_range,
                reason=reason,
                beat_count=beat_count,
            )
        )

    lines = [
        "# Chapter Pacing Plan",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Source File:** `{src}`",
        f"- **Source Format Scan:** {scan_status}",
        f"- **Reference Guidance:** {reference_status}",
        "- **Source Rule:** Current book source wins. Reference rhythm is optional craft guidance only.",
        "- **Length Rule:** Elastic ranges are not strict targets. Never pad or invent story to match them.",
        "",
        "## Chapter Classes",
        "",
        "| Chapter | Pacing Class | Elastic Range | Beat Count | Reason | Expansion Permission |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for item in pacing:
        lines.append(
            f"| {item.label} | {item.pacing_class} | {item.elastic_range} | {item.beat_count} | "
            f"{item.reason} | {expansion_permission(item.pacing_class)} |"
        )

    lines.extend(
        [
            "",
            "## Beat Guidance",
            "",
            "- Add `Pacing Class`, `Elastic Range`, `Why This Beat Is Short/Long`, `Expansion Permission`, and `Reference Rhythm Note` only when useful.",
            "- A `~1000` beat means a natural range such as roughly `900-1200`, not an exact target.",
            "- If the source supports less, stop short. If the source supports more, allow more.",
            "- Validate context before using pacing guidance for expansion.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists() or not book_folder.is_dir():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2
    try:
        content = build_plan(book_folder, Path(args.reference_analysis))
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    output = book_folder / "chapter-pacing-plan.md"
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
