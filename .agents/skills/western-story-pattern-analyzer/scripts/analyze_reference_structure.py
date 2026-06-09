#!/usr/bin/env python3
"""Analyze high-level structure from split reference chapters.

The script writes compact pattern notes. It does not quote or reproduce prose.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path


WORD_RE = re.compile(r"\b[\w'-]+\b")
CHAPTER_RE = re.compile(r"(?:chapter|ctp)[-_ ]?(\d+)", re.IGNORECASE)
ACTION_WORDS = {
    "hit",
    "struck",
    "shot",
    "fired",
    "grabbed",
    "pulled",
    "kicked",
    "rode",
    "ran",
    "moved",
    "opened",
    "closed",
    "stepped",
    "turned",
}
CONFLICT_WORDS = {
    "gun",
    "rifle",
    "pistol",
    "blood",
    "dead",
    "killed",
    "law",
    "jail",
    "fight",
    "shot",
    "wound",
    "threat",
    "wanted",
    "outlaw",
    "ranger",
    "sheriff",
}


@dataclass(frozen=True)
class ChapterStats:
    path: Path
    number: int
    words: int
    paragraphs: int
    dialogue_lines: int
    conflict_hits: int
    opening_type: str
    ending_type: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze reference chapter rhythm without copying prose."
    )
    parser.add_argument("chapter_folder", help="Folder containing split chapter .md files.")
    parser.add_argument(
        "--output",
        help="Analysis output folder. Defaults to <reference-root>/analysis.",
    )
    return parser.parse_args()


def chapter_number(path: Path) -> int:
    match = CHAPTER_RE.search(path.stem)
    return int(match.group(1)) if match else 999


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def body_blocks(text: str) -> list[str]:
    blocks = []
    for block in re.split(r"\n\s*\n", text.strip()):
        cleaned = "\n".join(
            line.strip()
            for line in block.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ).strip()
        if cleaned:
            blocks.append(cleaned)
    return blocks


def classify_block(block: str) -> str:
    stripped = block.strip()
    lower = stripped.lower()
    first_word = WORD_RE.search(lower)
    action_score = sum(1 for word in ACTION_WORDS if re.search(rf"\b{re.escape(word)}\b", lower))
    if stripped.startswith(('"', "'")):
        return "dialogue pressure"
    if action_score or (first_word and first_word.group(0) in ACTION_WORDS):
        return "physical action"
    if any(word in lower for word in ("thought", "remembered", "knew", "wanted")):
        return "interior reflection"
    return "setting or narration"


def analyze_file(path: Path) -> ChapterStats:
    text = path.read_text(encoding="utf-8")
    blocks = body_blocks(text)
    dialogue_lines = sum(1 for line in text.splitlines() if line.strip().startswith(('"', "'")))
    lower = text.lower()
    conflict_hits = sum(len(re.findall(rf"\b{re.escape(word)}\b", lower)) for word in CONFLICT_WORDS)
    return ChapterStats(
        path=path,
        number=chapter_number(path),
        words=word_count(text),
        paragraphs=len(blocks),
        dialogue_lines=dialogue_lines,
        conflict_hits=conflict_hits,
        opening_type=classify_block(blocks[0]) if blocks else "unknown",
        ending_type=classify_block(blocks[-1]) if blocks else "unknown",
    )


def pacing_class(words: int, median_words: float) -> str:
    if words < median_words * 0.65:
        return "lean"
    if words > median_words * 1.35:
        return "expanded"
    if words > median_words * 1.15:
        return "long-standard"
    return "standard"


def stats_table(chapters: list[ChapterStats], median_words: float) -> list[str]:
    lines = ["| Chapter | Words | Pacing Class | Paragraphs | Dialogue Lines | Conflict Signals |", "| --- | ---: | --- | ---: | ---: | ---: |"]
    for chapter in chapters:
        lines.append(
            f"| {chapter.number} | {chapter.words} | {pacing_class(chapter.words, median_words)} | "
            f"{chapter.paragraphs} | {chapter.dialogue_lines} | {chapter.conflict_hits} |"
        )
    return lines


def rhythm_notes(chapters: list[ChapterStats]) -> list[str]:
    words = [chapter.words for chapter in chapters]
    median_words = statistics.median(words)
    longest = sorted(chapters, key=lambda item: item.words, reverse=True)[:3]
    shortest = sorted(chapters, key=lambda item: item.words)[:3]
    return [
        f"- Reference chapters: {len(chapters)}",
        f"- Total words: {sum(words)}",
        f"- Average chapter words: {round(statistics.mean(words))}",
        f"- Median chapter words: {round(median_words)}",
        f"- Shortest chapter: Chapter {shortest[0].number} at {shortest[0].words} words",
        f"- Longest chapter: Chapter {longest[0].number} at {longest[0].words} words",
        "- Long chapters cluster around: "
        + ", ".join(f"Chapter {chapter.number} ({chapter.words})" for chapter in longest),
        "- Short chapters cluster around: "
        + ", ".join(f"Chapter {chapter.number} ({chapter.words})" for chapter in shortest),
    ]


def render_reference_pattern(chapters: list[ChapterStats]) -> str:
    return "\n".join(
        [
            "# Reference Pattern",
            "",
            "This file captures high-level craft observations only. Do not copy prose, plot, names, scenes, voice, or exact structure from the reference.",
            "",
            "## Use",
            "",
            "- Use as optional pacing calibration for Western manuscripts.",
            "- Keep the current book's source files as the source of truth.",
            "- Apply only broad rhythm lessons: uneven chapter length, escalation, quiet recovery, and varied openings/endings.",
            "",
            "## Pattern Notes",
            "",
            "- Chapter lengths vary naturally instead of landing on one repeated size.",
            "- Short chapters can function as hooks, aftermaths, transitions, or teasers.",
            "- Longer chapters should be reserved for supported confrontation, multi-step escalation, or consequence.",
            "- Dialogue and action density should rise or fall with story pressure, not with a fixed target.",
        ]
    )


def render_chapter_rhythm(chapters: list[ChapterStats]) -> str:
    words = [chapter.words for chapter in chapters]
    median_words = statistics.median(words)
    lines = ["# Chapter Rhythm", "", *rhythm_notes(chapters), "", *stats_table(chapters, median_words)]
    return "\n".join(lines)


def render_scene_density(chapters: list[ChapterStats]) -> str:
    lines = [
        "# Scene Density",
        "",
        "Paragraph and dialogue counts are structural signals only; they are not quality scores.",
        "",
        "| Chapter | Paragraphs | Dialogue Lines | Words Per Paragraph |",
        "| --- | ---: | ---: | ---: |",
    ]
    for chapter in chapters:
        wpp = round(chapter.words / chapter.paragraphs) if chapter.paragraphs else 0
        lines.append(f"| {chapter.number} | {chapter.paragraphs} | {chapter.dialogue_lines} | {wpp} |")
    return "\n".join(lines)


def render_openings_endings(chapters: list[ChapterStats]) -> str:
    lines = [
        "# Opening And Ending Patterns",
        "",
        "Labels are heuristic. Use them to vary chapter entrances and exits without quoting reference prose.",
        "",
        "| Chapter | Opening Type | Ending Type |",
        "| --- | --- | --- |",
    ]
    for chapter in chapters:
        lines.append(f"| {chapter.number} | {chapter.opening_type} | {chapter.ending_type} |")
    return "\n".join(lines)


def render_conflict_map(chapters: list[ChapterStats]) -> str:
    median_conflict = statistics.median([chapter.conflict_hits for chapter in chapters])
    lines = [
        "# Conflict Escalation Map",
        "",
        "Conflict signals are keyword-based and only show where visible pressure may rise or fall.",
        "",
        "| Chapter | Conflict Signals | Pressure Class |",
        "| --- | ---: | --- |",
    ]
    for chapter in chapters:
        if chapter.conflict_hits > median_conflict * 1.35:
            pressure = "high"
        elif chapter.conflict_hits < max(1, median_conflict * 0.65):
            pressure = "low"
        else:
            pressure = "medium"
        lines.append(f"| {chapter.number} | {chapter.conflict_hits} | {pressure} |")
    return "\n".join(lines)


def render_pacing_calibration(chapters: list[ChapterStats]) -> str:
    words = [chapter.words for chapter in chapters]
    median_words = statistics.median(words)
    lean_cap = round(median_words * 0.75)
    expanded_floor = round(median_words * 1.2)
    return "\n".join(
        [
            "# Pacing Calibration",
            "",
            "Use these as elastic guidance, not commands. If a current book's source material does not support the range, stop short.",
            "",
            f"- Reference median: about {round(median_words)} words.",
            f"- Lean chapters in this reference tend to fall below about {lean_cap} words.",
            f"- Expanded chapters in this reference tend to rise above about {expanded_floor} words.",
            "- Recommended manuscript classes:",
            "  - `lean`: short setup, aftermath, transition, epilogue, or teaser.",
            "  - `standard`: normal investigation, travel, town pressure, or character movement.",
            "  - `expanded`: action, reveal, moral pressure, or multi-scene escalation.",
            "  - `major`: climax, rescue, siege, central confrontation, or major reversal.",
            "- Do not make every chapter match the average.",
            "- Do not use reference rhythm to add unsupported events.",
        ]
    )


def write_outputs(output_dir: Path, chapters: list[ChapterStats]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "reference-pattern.md": render_reference_pattern(chapters),
        "chapter-rhythm.md": render_chapter_rhythm(chapters),
        "scene-density.md": render_scene_density(chapters),
        "opening-and-ending-patterns.md": render_openings_endings(chapters),
        "conflict-escalation-map.md": render_conflict_map(chapters),
        "pacing-calibration.md": render_pacing_calibration(chapters),
    }
    for filename, content in outputs.items():
        (output_dir / filename).write_text(content.rstrip() + "\n", encoding="utf-8")


def default_output_dir(chapter_folder: Path) -> Path:
    parent = chapter_folder.parent
    if parent.name:
        return parent / "analysis"
    return chapter_folder / "analysis"


def main() -> int:
    args = parse_args()
    chapter_folder = Path(args.chapter_folder)
    if not chapter_folder.exists() or not chapter_folder.is_dir():
        print(f"Error: chapter folder not found: {chapter_folder}", file=sys.stderr)
        return 2

    chapter_paths = sorted(chapter_folder.glob("*.md"), key=chapter_number)
    if not chapter_paths:
        print(f"Error: no .md chapter files found in {chapter_folder}", file=sys.stderr)
        return 2

    chapters = [analyze_file(path) for path in chapter_paths]
    output_dir = Path(args.output) if args.output else default_output_dir(chapter_folder)
    write_outputs(output_dir, chapters)

    print(f"# Reference Structure Analysis")
    print()
    print(f"- **Chapter Folder:** `{chapter_folder}`")
    print(f"- **Output Folder:** `{output_dir}`")
    for line in rhythm_notes(chapters):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
