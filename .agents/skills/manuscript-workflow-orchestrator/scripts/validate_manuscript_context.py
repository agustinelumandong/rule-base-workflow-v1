#!/usr/bin/env python3
"""Validate manuscript chapter structure and produce context review prompts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_BOOK_FILES = [
    "phase-0.md",
    "rulebook.md",
    "mood-lock.md",
    "chapter-summaries.md",
]

BEAT_REQUIRED_MARKERS = [
    "### Source Context Lock",
    "- **Source Anchor:**",
    "- **Continuity In:**",
    "- **Required Story Movement:**",
    "- **Continuity Out:**",
    "- **Do Not Invent:**",
    "### Beat Instructions",
    "### Context Match Check",
]

BANNED_AI_ECHO_WORDS = [
    "absolutely",
    "completely",
    "relentless",
    "massive",
    "sharp",
    "heavy",
    "pure",
    "extremely",
    "perfectly",
]

MODERN_OR_CLINICAL_WORDS = [
    "velocity",
    "fraction",
    "trajectory",
    "impact",
    "visible",
    "resolving",
]

FORBIDDEN_LENGTH_LANGUAGE = [
    "strict " + "word count",
    "Min " + "Words",
    "Max " + "Words",
]

UNRESOLVED_MARKERS = [
    "UNKNOWN",
    "TBD",
    "TODO",
]

INTERNAL_MONOLOGUE_PHRASES = [
    "he felt",
    "he realized",
    "he thought",
    "she felt",
    "she realized",
    "she thought",
]

DIALOGUE_TAG_RE = re.compile(r'"\s*(?:said|asked|shouted|whispered|muttered|replied)\b', re.IGNORECASE)
BEAT_RE = re.compile(r"^## BEAT\s+\d+:", re.MULTILINE)
PHASE_CHAPTER_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:\*\*)?"
    r"(Chapter\s+(\d+):[^\n]+|Epilogue(?:\s+Teaser)?(?::[^\n]+)?)"
    r"(?:\*\*)?\s*$",
    re.MULTILINE,
)
FIELD_RE = re.compile(r"^- \*\*(Source Anchor|Required Story Movement):\*\* (.+)$", re.MULTILINE)
EXIT_HOOK_PREFIX_RE = re.compile(r"^Exit hook / transition required by source:\s*", re.IGNORECASE)

STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "already",
    "also",
    "among",
    "before",
    "behind",
    "being",
    "chapter",
    "comes",
    "could",
    "every",
    "from",
    "have",
    "into",
    "later",
    "more",
    "only",
    "once",
    "over",
    "than",
    "that",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "through",
    "with",
    "without",
    "would",
    "where",
    "which",
    "while",
    "will",
    "when",
    "what",
    "once",
    "onto",
    "under",
}


@dataclass(frozen=True)
class ChapterFiles:
    slug: str
    label: str
    folder: Path
    draft: Path
    scene_breakdown: Path
    drafting_plan: Path


@dataclass
class ChapterReport:
    chapter: ChapterFiles
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.failures:
            return "FAIL"
        if self.warnings:
            return "WARN"
        return "PASS"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate manuscript chapters against structure, context-lock, and style rules."
    )
    parser.add_argument(
        "book_folder",
        nargs="?",
        default="books/tex-cade",
        help="Book folder containing phase-0.md, rulebook.md, chapter-summaries.md, and chapters/.",
    )
    parser.add_argument(
        "--chapter",
        help="Limit validation or AI prompt output to a chapter folder slug such as chapter-02 or epilogue.",
    )
    parser.add_argument(
        "--ai-prompt",
        action="store_true",
        help="Print an AI semantic review prompt instead of the deterministic validation report.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def chapter_sort_key(path: Path) -> tuple[int, str]:
    if path.name == "epilogue":
        return (999, path.name)
    match = re.search(r"chapter-(\d+)", path.name)
    if match:
        return (int(match.group(1)), path.name)
    return (998, path.name)


def discover_chapters(book_folder: Path) -> list[ChapterFiles]:
    chapters_root = book_folder / "chapters"
    if not chapters_root.exists():
        return []

    chapters: list[ChapterFiles] = []
    for folder in sorted((path for path in chapters_root.iterdir() if path.is_dir()), key=chapter_sort_key):
        if folder.name == "epilogue":
            draft = folder / "epilogue.md"
            label = "Epilogue"
        else:
            draft = folder / f"{folder.name}.md"
            label = folder.name.replace("-", " ").title()
        chapters.append(
            ChapterFiles(
                slug=folder.name,
                label=label,
                folder=folder,
                draft=draft,
                scene_breakdown=folder / "scene-breakdown.md",
                drafting_plan=folder / "drafting-plan.md",
            )
        )
    return chapters


def contains_any(text: str, terms: list[str], *, case_sensitive: bool = False) -> list[str]:
    haystack = text if case_sensitive else text.lower()
    matches: list[str] = []
    for term in terms:
        needle = term if case_sensitive else term.lower()
        if needle in haystack:
            matches.append(term)
    return matches


def tokenize(text: str) -> list[str]:
    return [normalize_token(match.group(0)) for match in re.finditer(r"[A-Za-z][A-Za-z']+", text)]


def normalize_token(token: str) -> str:
    token = token.lower().strip("'")
    if token.endswith("'s"):
        token = token[:-2]
    if len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ied"):
        token = token[:-3] + "y"
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("s"):
        token = token[:-1]
    return token


def key_terms(text: str) -> list[str]:
    seen: set[str] = set()
    terms: list[str] = []
    for token in tokenize(text):
        if len(token) < 4 or token in STOPWORDS:
            continue
        if token not in seen:
            seen.add(token)
            terms.append(token)
    return terms


def coverage(source: str, target: str) -> tuple[float, list[str]]:
    terms = key_terms(source)
    if not terms:
        return 1.0, []
    target_tokens = set(tokenize(target))
    missing = [term for term in terms if term not in target_tokens]
    score = (len(terms) - len(missing)) / len(terms)
    return score, missing


def parse_phase_chapters(book_folder: Path) -> dict[str, str]:
    phase_path = book_folder / "phase-0.md"
    if not phase_path.exists():
        return {}
    text = read_text(phase_path)
    matches = list(PHASE_CHAPTER_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1)
        start = match.end()
        next_chapter_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        next_heading = re.search(r"^##\s+", text[start:next_chapter_start], re.MULTILINE)
        end = start + next_heading.start() if next_heading else next_chapter_start
        body = text[start:end].strip()
        if heading.lower().startswith("epilogue"):
            slug = "epilogue"
        else:
            number = int(match.group(2))
            slug = f"chapter-{number:02d}"
        sections[slug] = body
    return sections


def extract_scene_fields(scene_text: str) -> list[str]:
    fields: list[str] = []
    for match in FIELD_RE.finditer(scene_text):
        field = match.group(2).strip()
        field = EXIT_HOOK_PREFIX_RE.sub("", field).strip()
        if field:
            fields.append(field)
    return fields


def validate_required_book_files(book_folder: Path) -> tuple[list[str], list[str]]:
    passes: list[str] = []
    failures: list[str] = []
    for relative_path in REQUIRED_BOOK_FILES:
        path = book_folder / relative_path
        if path.exists() and path.read_text(encoding="utf-8").strip():
            passes.append(f"Found `{relative_path}`.")
        else:
            failures.append(f"Missing or empty `{relative_path}`.")
    return passes, failures


def validate_scene_breakdown(chapter: ChapterFiles) -> tuple[list[str], list[str]]:
    passes: list[str] = []
    failures: list[str] = []

    if not chapter.scene_breakdown.exists():
        return passes, [f"Missing `{chapter.scene_breakdown}`."]

    text = read_text(chapter.scene_breakdown)
    beats = BEAT_RE.findall(text)
    if not beats:
        failures.append("Scene breakdown has no `## BEAT` sections.")
    else:
        passes.append(f"Scene breakdown has {len(beats)} beat section(s).")

    for marker in BEAT_REQUIRED_MARKERS:
        count = text.count(marker)
        if count == 0:
            failures.append(f"Scene breakdown missing `{marker}`.")
        elif beats and count < len(beats):
            failures.append(
                f"Scene breakdown has {len(beats)} beat(s) but only {count} `{marker}` marker(s)."
            )
    if not failures:
        passes.append("Scene breakdown includes required context-lock structure for every beat.")

    return passes, failures


def validate_draft(chapter: ChapterFiles) -> tuple[list[str], list[str], list[str]]:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    if not chapter.draft.exists():
        return passes, warnings, [f"Missing draft `{chapter.draft}`."]

    text = read_text(chapter.draft)
    if not text.strip():
        return passes, warnings, [f"Draft `{chapter.draft}` is empty."]

    passes.append("Draft exists and is non-empty.")

    forbidden_length = contains_any(text, FORBIDDEN_LENGTH_LANGUAGE)
    if forbidden_length:
        failures.append(f"Draft contains forbidden length language: {', '.join(forbidden_length)}.")

    unresolved = contains_any(text, UNRESOLVED_MARKERS, case_sensitive=True)
    if unresolved:
        failures.append(f"Draft contains unresolved marker(s): {', '.join(unresolved)}.")

    echo_words = contains_any(text, BANNED_AI_ECHO_WORDS)
    if echo_words:
        warnings.append(f"Draft contains banned AI echo word(s): {', '.join(echo_words)}.")

    modern_words = contains_any(text, MODERN_OR_CLINICAL_WORDS)
    if modern_words:
        warnings.append(f"Draft contains modern/clinical word(s): {', '.join(modern_words)}.")

    internal_phrases = contains_any(text, INTERNAL_MONOLOGUE_PHRASES)
    if internal_phrases:
        warnings.append(f"Draft contains internal-monologue phrase(s): {', '.join(internal_phrases)}.")

    dialogue_tags = sorted(set(match.group(0).strip() for match in DIALOGUE_TAG_RE.finditer(text)))
    if dialogue_tags:
        warnings.append(f"Draft may contain unwanted dialogue tag(s): {', '.join(dialogue_tags)}.")

    return passes, warnings, failures


def validate_source_alignment(chapter: ChapterFiles, phase_sections: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    phase_source = phase_sections.get(chapter.slug)
    if not phase_source:
        failures.append(f"No matching `{chapter.slug}` section found in `phase-0.md`.")
        return passes, warnings, failures

    if not chapter.scene_breakdown.exists() or not chapter.draft.exists():
        return passes, warnings, failures

    scene_text = read_text(chapter.scene_breakdown)
    draft_text = read_text(chapter.draft)
    scene_score, scene_missing = coverage(phase_source, scene_text)
    draft_score, draft_missing = coverage(phase_source, draft_text)

    if scene_score < 0.50:
        warnings.append(
            f"Scene breakdown has limited overlap with `phase-0.md` source ({scene_score:.0%}); check missing terms: {', '.join(scene_missing[:8])}."
        )
    else:
        passes.append(f"Scene breakdown overlaps `phase-0.md` source ({scene_score:.0%}).")

    if draft_score < 0.35:
        warnings.append(
            f"Draft has limited overlap with `phase-0.md` source ({draft_score:.0%}); check missing terms: {', '.join(draft_missing[:8])}."
        )
    else:
        passes.append(f"Draft overlaps `phase-0.md` source ({draft_score:.0%}).")

    weak_fields: list[str] = []
    for field in extract_scene_fields(scene_text):
        field_terms = key_terms(field)
        if len(field_terms) < 3:
            continue
        field_score, field_missing = coverage(field, draft_text)
        if field_score < 0.25:
            weak_fields.append(f"{field[:80]}... missing {', '.join(field_missing[:5])}")

    if weak_fields:
        warnings.append(
            "Some beat source anchors or required movements have weak draft coverage: "
            + " | ".join(weak_fields[:3])
        )
    else:
        passes.append("Beat source anchors and required movements have draft coverage.")

    return passes, warnings, failures


def validate_chapter(chapter: ChapterFiles, phase_sections: dict[str, str]) -> ChapterReport:
    report = ChapterReport(chapter=chapter)

    if not chapter.drafting_plan.exists() or not read_text(chapter.drafting_plan).strip():
        report.failures.append(f"Missing or empty `{chapter.drafting_plan}`.")
    else:
        report.passes.append("Drafting plan exists.")

    scene_passes, scene_failures = validate_scene_breakdown(chapter)
    report.passes.extend(scene_passes)
    report.failures.extend(scene_failures)

    draft_passes, draft_warnings, draft_failures = validate_draft(chapter)
    report.passes.extend(draft_passes)
    report.warnings.extend(draft_warnings)
    report.failures.extend(draft_failures)

    source_passes, source_warnings, source_failures = validate_source_alignment(chapter, phase_sections)
    report.passes.extend(source_passes)
    report.warnings.extend(source_warnings)
    report.failures.extend(source_failures)

    return report


def render_report(book_folder: Path, book_passes: list[str], book_failures: list[str], reports: list[ChapterReport]) -> str:
    lines = [
        "# Manuscript Context Validation Report",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Overall Status:** {overall_status(book_failures, reports)}",
        "- **Length Status:** Run `scripts/check_manuscript_length.py` after context validation to review book-level progress.",
        "",
        "## Book Files",
        "",
    ]

    for item in book_passes:
        lines.append(f"- PASS: {item}")
    for item in book_failures:
        lines.append(f"- FAIL: {item}")

    lines.extend(["", "## Chapter Status", "", "| Chapter | Status | Failures | Warnings |", "| --- | --- | ---: | ---: |"])
    for report in reports:
        lines.append(f"| {report.chapter.label} | {report.status} | {len(report.failures)} | {len(report.warnings)} |")

    lines.append("")
    for report in reports:
        lines.extend([f"## {report.chapter.label}", "", f"- **Status:** {report.status}"])
        for item in report.failures:
            lines.append(f"- FAIL: {item}")
        for item in report.warnings:
            lines.append(f"- WARN: {item}")
        if not report.failures and not report.warnings:
            source_passes = [item for item in report.passes if "phase-0.md" in item or "Beat source anchors" in item]
            if source_passes:
                for item in source_passes:
                    lines.append(f"- PASS: {item}")
            else:
                lines.append("- PASS: Deterministic checks passed.")
        lines.append("")

    lines.extend(
        [
            "## AI Semantic Review",
            "",
            "The validator now performs automated `phase-0.md` overlap and beat-coverage checks. Use `--ai-prompt --chapter chapter-XX` when a chapter needs deeper Codex/ChatGPT 5.5 semantic review.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def overall_status(book_failures: list[str], reports: list[ChapterReport]) -> str:
    if book_failures or any(report.failures for report in reports):
        return "FAIL"
    if any(report.warnings for report in reports):
        return "WARN"
    return "PASS"


def build_ai_prompt(book_folder: Path, chapter: ChapterFiles) -> str:
    source_paths = [
        book_folder / "phase-0.md",
        book_folder / "rulebook.md",
        book_folder / "mood-lock.md",
        book_folder / "chapter-summaries.md",
        chapter.scene_breakdown,
        chapter.draft,
    ]
    for path in source_paths:
        if not path.exists():
            raise RuntimeError(f"Cannot build AI prompt; missing `{path}`.")

    return f"""# AI Chapter Context Review Prompt

Use Codex / ChatGPT 5.5 as the primary reviewer. Gemini is optional secondary review only.

Review `{chapter.draft}` against these sources:

- `{book_folder / "phase-0.md"}`
- `{book_folder / "rulebook.md"}`
- `{book_folder / "mood-lock.md"}`
- `{book_folder / "chapter-summaries.md"}`
- `{chapter.scene_breakdown}`

## Required Review

Answer these questions:

1. Does the chapter cover every approved beat in the scene breakdown?
2. Does any scene skip required story movement?
3. Does the chapter invent unsupported names, locations, motives, lore, backstory, or plot bridges?
4. Does continuity in/out match the prior and next chapter requirements?
5. Does POV stay controlled and avoid head-hopping?
6. Does the Western style lock hold?
7. Does the expansion deepen approved material instead of padding?

## Output Format

Return a Markdown report with exactly these sections:

```md
# {chapter.label} Context Review

## Passes

- [List source-locked items that pass.]

## Warnings

- [List concerns that do not block drafting.]

## Failures

- [List source drift, skipped beats, unsupported invention, or style violations that must be fixed.]

## Required Fixes

- [List concrete edits needed before continuing.]
```

If a fact is missing from source, mark it `UNKNOWN`; do not invent it.
"""


def main() -> int:
    args = parse_args()
    book_folder = Path(args.book_folder)
    if not book_folder.exists():
        print(f"Error: book folder not found: {book_folder}", file=sys.stderr)
        return 2

    chapters = discover_chapters(book_folder)
    if args.chapter:
        chapters = [chapter for chapter in chapters if chapter.slug == args.chapter]
        if not chapters:
            print(f"Error: chapter not found: {args.chapter}", file=sys.stderr)
            return 2

    if args.ai_prompt:
        if len(chapters) != 1:
            print("Error: --ai-prompt requires exactly one chapter via --chapter.", file=sys.stderr)
            return 2
        try:
            print(build_ai_prompt(book_folder, chapters[0]))
        except RuntimeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
        return 0

    book_passes, book_failures = validate_required_book_files(book_folder)
    phase_sections = parse_phase_chapters(book_folder)
    reports = [validate_chapter(chapter, phase_sections) for chapter in chapters]
    print(render_report(book_folder, book_passes, book_failures, reports))
    return 1 if overall_status(book_failures, reports) == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
