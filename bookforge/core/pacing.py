#!/usr/bin/env python3
"""BookForge Chapter Pacing Planner Core Module."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bookforge.core.scanner import first_target, source_path

CHAPTER_RE = re.compile(r"chapter-(\d+)", re.IGNORECASE)

CLASS_RANGES = {
    "lean": "~900 (roughly 700-1200 when source-supported)",
    "standard": "~1600 (roughly 1300-1900 when source-supported)",
    "expanded": "~2200 (roughly 1900-2600 when source-supported)",
    "major": "~2900 (roughly 2500-3400 when source-supported)",
    "epilogue/teaser": "~600 (roughly 300-900 when source-supported)",
}
PACING_CLASS_RE = re.compile(r"(?im)^-\s+\*\*Pacing Class:\*\*\s+(.+?)\s*$")
ELASTIC_RANGE_RE = re.compile(r"(?im)^-\s+\*\*Elastic Range:\*\*\s+(.+?)\s*$")
BEAT_HEADING_RE = re.compile(r"(?im)^##\s+BEAT\s+\d+\s*:\s*(.+?)\s*$")
BEAT_WEIGHT_RE = re.compile(r"(?im)^-\s+\*\*Beat Weight:\*\*\s+(.+?)\s*$")
BEAT_DEVELOPMENT_FLOOR_RE = re.compile(r"(?im)^-\s+\*\*Beat Development Floor:\*\*\s+(.+?)\s*$")
BEAT_MATTERS_RE = re.compile(r"(?im)^-\s+\*\*Why This Beat Matters:\*\*\s+(.+?)\s*$")

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


@dataclass(frozen=True)
class BeatMetadata:
    label: str
    weight: str
    development_floor: int | None
    why_this_matters: str | None


def read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


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
    slugs = set()
    changes_root = book_folder / "changes"
    if changes_root.exists():
        for path in changes_root.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                slugs.add(path.name)
    chapters_root = book_folder / "chapters"
    if chapters_root.exists():
        for path in chapters_root.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                slugs.add(path.name)
    
    chapter_folders = []
    for slug in sorted(slugs, key=lambda s: chapter_sort_key(Path(s))):
        changes_path = changes_root / slug
        chapters_path = chapters_root / slug
        if changes_path.exists():
            chapter_folders.append(changes_path)
        else:
            chapter_folders.append(chapters_path)
    return chapter_folders


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
        return "No source-format-scan.md found; run `bf init` before planning when possible."
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


def explicit_scene_pacing(scene_text: str) -> tuple[str | None, str | None]:
    class_match = PACING_CLASS_RE.search(scene_text)
    range_match = ELASTIC_RANGE_RE.search(scene_text)
    pacing_class = class_match.group(1).strip().rstrip(".") if class_match else None
    elastic_range = None
    if range_match:
        elastic_range = range_match.group(1).split(";", 1)[0].strip()
    return pacing_class, elastic_range


def _parse_floor(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d[\d,]*)", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def extract_beat_metadata(scene_text: str) -> list[BeatMetadata]:
    headings = list(BEAT_HEADING_RE.finditer(scene_text))
    beats: list[BeatMetadata] = []
    for index, heading in enumerate(headings):
        start = heading.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(scene_text)
        section = scene_text[start:end]
        weight_match = BEAT_WEIGHT_RE.search(section)
        floor_match = BEAT_DEVELOPMENT_FLOOR_RE.search(section)
        matters_match = BEAT_MATTERS_RE.search(section)
        beats.append(
            BeatMetadata(
                label=heading.group(1).strip(),
                weight=(weight_match.group(1).strip().lower() if weight_match else "standard"),
                development_floor=_parse_floor(floor_match.group(1).strip() if floor_match else None),
                why_this_matters=matters_match.group(1).strip() if matters_match else None,
            )
        )
    return beats


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
        proposal_path = folder / "proposal.md"
        scene_bd_path = folder / "scene-breakdown.md"
        scene = read_optional(proposal_path if proposal_path.exists() or not scene_bd_path.exists() else scene_bd_path)
        summary_section = extract_heading_section(summaries, slug)
        source_section = extract_heading_section(source_text, slug)
        source_scope = "\n\n".join([source_section, summary_section]).strip()
        combined = "\n\n".join([source_scope, scene])
        beat_count = count_beats(scene)
        explicit_class, explicit_range = explicit_scene_pacing(scene)
        if explicit_class in CLASS_RANGES:
            pacing_class = explicit_class
            reason = "explicit source-locked pacing from chapter scene breakdown"
        else:
            pacing_class, reason = classify(slug, source_scope or combined, beat_count)
        elastic_range = explicit_range or chapter_word_guidance(source_section) or CLASS_RANGES[pacing_class]
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
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Build a source-locked chapter pacing plan.")
    parser.add_argument("book_folder", help="Book folder such as books/book-example.")
    parser.add_argument(
        "--reference-analysis",
        default="references/timber/analysis/pacing-calibration.md",
        help="Optional reference pacing calibration file.",
    )
    args = parser.parse_args()
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
