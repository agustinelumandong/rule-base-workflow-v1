"""Chapter-level validation orchestration and report rendering."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from bookforge.core import action
from bookforge.core import voice as voice_module
from bookforge.core import world as world_module
from bookforge.core.issue import ManuscriptIssue, Severity
from bookforge.core.prompts import load_prompt_template
from bookforge.core.validators.continuity import (
    check_unprofiled_period_terms,
    validate_continuity_out_issues,
)
from bookforge.core.validators.format import (
    UNRESOLVED_MARKERS,
    ChapterFiles,
    _make_issue,
    discover_chapters,
    parse_phase_chapters,
    read_text,
    validate_required_book_file_issues,
    validate_scene_breakdown,
)
from bookforge.core.validators.style import (
    BANNED_AI_ECHO_WORDS,
    INTERNAL_MONOLOGUE_PHRASES,
    MODERN_OR_CLINICAL_WORDS,
    STOPWORDS,
    check_em_dash_anchors,
    check_forbidden_conflicts,
    check_ing_openers,
    check_plot_mode_risk,
    check_pronoun_loops,
    check_repeated_sentence_duplicates,
    check_style_review_signals,
    contains_any,
    dialogue_tags,
    forbidden_length_language,
)

FIELD_RE = re.compile(
    r"^- \*\*(Source Anchor|Required Story Movement):\*\* (.+)$",
    re.MULTILINE,
)
EXIT_HOOK_PREFIX_RE = re.compile(
    r"^Exit hook / transition required by source:\s*",
    re.IGNORECASE,
)


@dataclass
class ChapterReport:
    chapter: ChapterFiles
    passes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.failures:
            return "FAIL"
        if self.warnings:
            return "WARN"
        return "PASS"


def key_terms(text: str) -> set[str]:
    text_clean = re.sub(r"[^A-Za-z0-9\s-]", "", text)
    return {
        word_lower
        for word in text_clean.split()
        if (
            len(word_lower := word.lower()) > 3
            and word_lower not in STOPWORDS
            and not word_lower.startswith("chapter-")
        )
    }


def coverage(source_text: str, target_text: str) -> tuple[float, list[str]]:
    source_words = key_terms(source_text)
    target_words = key_terms(target_text)
    if not source_words:
        return 1.0, []
    matches = source_words.intersection(target_words)
    missing = sorted(source_words.difference(target_words))
    return len(matches) / len(source_words), missing


def extract_scene_fields(scene_text: str) -> list[str]:
    fields: list[str] = []
    for match in FIELD_RE.finditer(scene_text):
        field = EXIT_HOOK_PREFIX_RE.sub("", match.group(2).strip()).strip()
        if field:
            fields.append(field)
    return fields


def _read_chapter_review(chapter: ChapterFiles) -> tuple[str | None, str | None]:
    if not chapter.chapter_review.exists():
        return None, None

    text = read_text(chapter.chapter_review)
    match = re.search(r"(?ims)^##\s+Decision\s*(.+?)\s*(?=^##\s+|\Z)", text)
    if not match:
        return text, None
    decision = match.group(1).strip().splitlines()[0].strip().lower()
    return text, decision


def _beat_window(text: str, phrase: str) -> tuple[int, int] | None:
    phrase_terms = [term for term in key_terms(phrase) if len(term) > 3]
    if not phrase_terms:
        return None

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    for index, paragraph in enumerate(paragraphs):
        paragraph_terms = key_terms(paragraph)
        overlap = len(set(phrase_terms).intersection(paragraph_terms))
        if overlap >= max(1, min(2, len(phrase_terms))):
            start = max(0, index - 1)
            end = min(len(paragraphs), index + 2)
            window_text = "\n\n".join(paragraphs[start:end])
            return len(window_text.split()), overlap
    return None


def validate_chapter_pacing(chapter: ChapterFiles) -> tuple[ManuscriptIssue, ...]:
    from bookforge.core import pacing as pacing_module

    issues: list[ManuscriptIssue] = []
    if not chapter.draft.exists() or not chapter.draft.name.startswith(chapter.slug):
        return tuple(issues)

    review_text, decision = _read_chapter_review(chapter)
    if review_text is None:
        issues.append(_make_issue(
            "CHAPTER_REVIEW_MISSING",
            f"Compiled chapter is missing required `chapter-review.md` at `{chapter.chapter_review}`.",
            chapter=chapter.slug,
            file=chapter.chapter_review,
        ))
        return tuple(issues)

    if decision and decision != "ready":
        issues.append(_make_issue(
            "CHAPTER_REVIEW_NOT_READY",
            f"`chapter-review.md` decision is `{decision}`, so the compiled chapter is not ready.",
            chapter=chapter.slug,
            file=chapter.chapter_review,
        ))

    scene_text = read_text(chapter.scene_breakdown) if chapter.scene_breakdown.exists() else ""
    draft_text = read_text(chapter.draft)
    for beat in pacing_module.extract_beat_metadata(scene_text):
        phrase = beat.why_this_matters or beat.label
        window = _beat_window(draft_text, phrase)
        if window is None:
            issues.append(_make_issue(
                "BEAT_UNDERDEVELOPED",
                f"Beat `{beat.label}` is underdeveloped or missing from the compiled chapter.",
                chapter=chapter.slug,
                file=chapter.draft,
            ))
            continue
        window_words, _ = window
        if beat.development_floor and window_words < beat.development_floor:
            severity = Severity.HARD if beat.weight == "money" else Severity.SOFT
            issues.append(_make_issue(
                "BEAT_UNDERDEVELOPED",
                f"Beat `{beat.label}` is underdeveloped: found about {window_words} words near the beat, below floor {beat.development_floor}.",
                chapter=chapter.slug,
                file=chapter.draft,
                severity=severity,
            ))

    return tuple(issues)


def validate_draft(chapter: ChapterFiles) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    if not chapter.draft.exists():
        issues.append(_make_issue(
            "VALIDATOR_MISSING_DRAFT",
            f"Missing draft `{chapter.draft}`.",
            chapter=chapter.slug,
            file=chapter.draft,
        ))
        return tuple(issues)

    text = read_text(chapter.draft)
    if not text.strip():
        issues.append(_make_issue(
            "VALIDATOR_EMPTY_DRAFT",
            f"Draft `{chapter.draft}` is empty.",
            chapter=chapter.slug,
            file=chapter.draft,
        ))
        return tuple(issues)

    forbidden_length = forbidden_length_language(text)
    for item in forbidden_length:
        issues.append(_make_issue(
            "VALIDATOR_FORBIDDEN_LENGTH_LANGUAGE",
            f"Draft contains forbidden length language: {item}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=item,
        ))

    unresolved = contains_any(text, UNRESOLVED_MARKERS, case_sensitive=True)
    for marker in unresolved:
        issues.append(_make_issue(
            "VALIDATOR_UNRESOLVED_MARKER",
            f"Draft contains unresolved marker(s): {', '.join(unresolved)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=marker,
        ))

    forbidden_conflicts = check_forbidden_conflicts(text, chapter.draft)
    for finding in forbidden_conflicts:
        issues.append(_make_issue(
            "VALIDATOR_FORBIDDEN_CONFLICT",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    echo_words = contains_any(text, BANNED_AI_ECHO_WORDS)
    for word in echo_words:
        issues.append(_make_issue(
            "VALIDATOR_BANNED_ECHO_WORD",
            f"Draft contains banned AI echo word(s): {', '.join(echo_words)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=word,
        ))

    modern_words = contains_any(text, MODERN_OR_CLINICAL_WORDS)
    for word in modern_words:
        issues.append(_make_issue(
            "VALIDATOR_MODERN_WORD",
            f"Draft contains modern/clinical word(s): {', '.join(modern_words)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=word,
        ))

    HISTORICAL_DICTIONARY = {
        "flashlight": 1899,
        "telephone": 1876,
        "teletype": 1902,
        "automobile": 1897,
        "subway": 1897,
        "zipper": 1893,
        "airplane": 1903,
        "radio": 1895,
        "motel": 1925,
        "cinema": 1895,
        "computer": 1940,
        "plastic": 1907,
        "radar": 1935,
        "television": 1927,
        "camera": 1888,
        "dynamite": 1867,
        "barbed wire": 1874,
        "barbed-wire": 1874,
        "phonograph": 1877,
        "typewriter": 1868,
    }

    book_folder = chapter.folder.parent.parent
    from bookforge.core.scanner import source_path
    phase_0_path = source_path(book_folder)
    book_year = 1880
    if phase_0_path and phase_0_path.exists():
        p0_text = phase_0_path.read_text(encoding="utf-8")
        match = re.search(r"(?i)Period:\s*.*?(\d{4})", p0_text)
        if match:
            book_year = int(match.group(1))
        else:
            match_general = re.search(r"\b(18\d{2}|1900)\b", p0_text)
            if match_general:
                book_year = int(match_general.group(1))

    text_lower = text.lower()
    for word, invention_year in HISTORICAL_DICTIONARY.items():
        if invention_year > book_year:
            if re.search(rf"\b{re.escape(word)}\b", text_lower):
                issues.append(_make_issue(
                    "VALIDATOR_ANACHRONISM",
                    f"Draft contains era-inconsistent word(s) for year {book_year}: '{word}' (invented in {invention_year}).",
                    chapter=chapter.slug,
                    file=chapter.draft,
                    span=word,
                ))

    internal_phrases = contains_any(text, INTERNAL_MONOLOGUE_PHRASES)
    for phrase in internal_phrases:
        issues.append(_make_issue(
            "VALIDATOR_INTERNAL_MONOLOGUE",
            f"Draft contains internal-monologue phrase(s): {', '.join(internal_phrases)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=phrase,
        ))

    found_dialogue_tags = dialogue_tags(text)
    for tag in found_dialogue_tags:
        issues.append(_make_issue(
            "VALIDATOR_UNWANTED_DIALOGUE_TAG",
            f"Draft may contain unwanted dialogue tag(s): {', '.join(found_dialogue_tags)}.",
            chapter=chapter.slug,
            file=chapter.draft,
            span=tag,
        ))

    ing_samples = check_ing_openers(text)
    for sample in ing_samples[:3]:
        issues.append(_make_issue(
            "VALIDATOR_ING_OPENER",
            f"Draft contains -ing sentence opener(s): {' | '.join(ing_samples[:3])}",
            chapter=chapter.slug,
            file=chapter.draft,
            span=sample[:50] if sample else None,
        ))

    pronoun_loops = check_pronoun_loops(text)
    for loop in pronoun_loops:
        issues.append(_make_issue(
            "VALIDATOR_PRONOUN_LOOP",
            f"Draft contains pronoun/name sentence loop(s): {'; '.join(pronoun_loops)}",
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    em_dash_warnings = check_em_dash_anchors(text)
    for warning in em_dash_warnings:
        issues.append(_make_issue(
            "VALIDATOR_EM_DASH_ANCHOR",
            warning,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    period_warnings = check_unprofiled_period_terms(text, book_folder)
    for warning in period_warnings:
        issues.append(_make_issue(
            "VALIDATOR_UNPROFILED_PERIOD_TERM",
            warning,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    repeated_sentences = check_repeated_sentence_duplicates(text)
    for finding in repeated_sentences:
        issues.append(_make_issue(
            "VALIDATOR_REPEATED_PROSE",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    plot_mode_risks = check_plot_mode_risk(text, book_folder)
    for finding in plot_mode_risks:
        issues.append(_make_issue(
            "VALIDATOR_PLOT_MODE_RISK",
            finding,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    review_signals = check_style_review_signals(text, chapter.draft)
    for signal in review_signals:
        issues.append(_make_issue(
            "VALIDATOR_STYLE_REVIEW_SIGNAL",
            signal,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    pov_character = ""
    if chapter.scene_breakdown.exists():
        try:
            sb_text = read_text(chapter.scene_breakdown)
            pov_match = re.search(r"(?i)^\s*[\-\*]\s*POV:\s*(\w+)", sb_text, re.MULTILINE)
            if pov_match:
                pov_character = pov_match.group(1).lower()
        except (OSError, UnicodeDecodeError):
            pass

    all_chars = []
    world_state_path = book_folder / "world-state.json"
    if world_state_path.exists():
        try:
            world_state = world_module.load_world_state(book_folder)
            all_chars = list(world_state.get("characters", {}).keys())
        except (json.JSONDecodeError, OSError, UnicodeDecodeError, KeyError):
            pass

    v_failures, v_warnings = voice_module.validate_dialogue_style(text, chapter.draft)
    for failure in v_failures:
        issues.append(_make_issue(
            "VALIDATOR_DIALOGUE_STYLE",
            failure,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    if pov_character and all_chars:
        pov_failures = voice_module.validate_pov_locking(text, pov_character, all_chars)
        for failure in pov_failures:
            issues.append(_make_issue(
                "VALIDATOR_POV_VIOLATION",
                failure,
                chapter=chapter.slug,
                file=chapter.draft,
            ))

    so_failures, so_warnings = voice_module.validate_sentence_openers(text)
    for failure in so_failures:
        issues.append(_make_issue(
            "VALIDATOR_SENTENCE_OPENER_ISSUE",
            failure,
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    return tuple(issues)


def validate_source_alignment(chapter: ChapterFiles, phase_sections: dict[str, str]) -> tuple[ManuscriptIssue, ...]:
    issues: list[ManuscriptIssue] = []
    phase_source = phase_sections.get(chapter.slug)
    if not phase_source:
        issues.append(_make_issue(
            "VALIDATOR_NO_MATCHING_SOURCE",
            f"No matching `{chapter.slug}` section found in `phase-0.md`.",
            chapter=chapter.slug,
        ))
        return tuple(issues)

    if not chapter.scene_breakdown.exists() or not chapter.draft.exists():
        return tuple(issues)

    scene_text = read_text(chapter.scene_breakdown)
    draft_text = read_text(chapter.draft)
    scene_score, scene_missing = coverage(phase_source, scene_text)
    draft_score, draft_missing = coverage(phase_source, draft_text)

    if scene_score < 0.50:
        issues.append(_make_issue(
            "VALIDATOR_WEAK_SOURCE_COVERAGE",
            f"Scene breakdown has limited overlap with `phase-0.md` source ({scene_score:.0%}); check missing terms: {', '.join(scene_missing[:8])}.",
            chapter=chapter.slug,
            file=chapter.scene_breakdown,
        ))

    if draft_score < 0.35:
        issues.append(_make_issue(
            "VALIDATOR_WEAK_SOURCE_COVERAGE",
            f"Draft has limited overlap with `phase-0.md` source ({draft_score:.0%}); check missing terms: {', '.join(draft_missing[:8])}.",
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    weak_fields = []
    for field in extract_scene_fields(scene_text):
        field_terms = key_terms(field)
        if len(field_terms) < 3:
            continue
        field_score, field_missing = coverage(field, draft_text)
        if field_score < 0.25:
            weak_fields.append(f"{field[:80]}... missing {', '.join(field_missing[:5])}")

    if weak_fields:
        issues.append(_make_issue(
            "VALIDATOR_WEAK_BEAT_COVERAGE",
            "Some beat source anchors or required movements have weak draft coverage: " + " | ".join(weak_fields[:3]),
            chapter=chapter.slug,
            file=chapter.draft,
        ))

    return tuple(issues)


def validate_scene(scene: SceneManifest) -> tuple[ManuscriptIssue, ...]:
    """Runs style, length, and forbidden term validations on a single scene draft."""
    from bookforge.core.validators.format import _make_issue, ChapterFiles
    from bookforge.core.issue import Severity, ManuscriptIssue

    issues: list[ManuscriptIssue] = []
    if not scene.draft_path.exists():
        issues.append(_make_issue(
            "SCENE_MISSING_DRAFT",
            f"Scene draft `{scene.draft_path}` is missing.",
            chapter=scene.chapter,
            file=scene.draft_path,
            severity=Severity.HARD
        ))
        return tuple(issues)

    text = scene.draft_path.read_text(encoding="utf-8")
    if not text.strip():
        issues.append(_make_issue(
            "SCENE_EMPTY_DRAFT",
            f"Scene draft `{scene.draft_path}` is empty.",
            chapter=scene.chapter,
            file=scene.draft_path,
            severity=Severity.HARD
        ))
        return tuple(issues)

    # 1. Word count check (±20% tolerance)
    words = len(re.findall(r"\b\w+\b", text))
    lower_bound = int(scene.target_words * 0.8)
    upper_bound = int(scene.target_words * 1.2)
    if words < lower_bound or words > upper_bound:
        issues.append(_make_issue(
            "SCENE_WORD_COUNT_VIOLATION",
            f"Scene draft word count ({words}) is outside ±20% tolerance of target ({scene.target_words} words, range {lower_bound}-{upper_bound}).",
            chapter=scene.chapter,
            file=scene.draft_path,
            severity=Severity.HARD
        ))

    # 2. Forbidden elements
    if scene.forbidden:
        found_forbidden = []
        for term in scene.forbidden:
            if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE):
                found_forbidden.append(term)
        if found_forbidden:
            issues.append(_make_issue(
                "SCENE_FORBIDDEN_ELEMENT",
                f"Scene draft contains forbidden elements: {', '.join(found_forbidden)}.",
                chapter=scene.chapter,
                file=scene.draft_path,
                severity=Severity.HARD
            ))

    # 3. Standard style checks
    mock_cf = ChapterFiles(
        slug=scene.chapter,
        folder=scene.draft_path.parent,
        draft=scene.draft_path,
        scene_breakdown=scene.draft_path.parent / "manifest.yml",
        drafting_plan=scene.draft_path.parent / "manifest.yml"
    )
    style_issues = validate_draft(mock_cf)
    for issue in style_issues:
        if issue.rule_id in ("VALIDATOR_MISSING_DRAFT", "VALIDATOR_EMPTY_DRAFT"):
            continue
        new_msg = f"[{scene.scene_id}] {issue.message}"
        issues.append(_make_issue(
            issue.rule_id,
            new_msg,
            chapter=scene.chapter,
            file=scene.draft_path,
            span=issue.span,
            severity=issue.severity
        ))

    # Deduplicate issues before returning
    seen = set()
    deduped_issues = []
    for issue in issues:
        key = (issue.severity, issue.rule_id, issue.message, issue.chapter, str(issue.file))
        if key not in seen:
            seen.add(key)
            deduped_issues.append(issue)
    return tuple(deduped_issues)



def validate_chapter(chapter: ChapterFiles, phase_sections: dict[str, str]) -> ChapterReport:
    # Import SceneManifest internally to avoid circular references
    from bookforge.core.scene import discover_scenes, SceneManifest

    report = ChapterReport(chapter=chapter)
    
    # Run validation on scenes first if they exist
    book_folder = chapter.folder.parent.parent
    scenes = discover_scenes(chapter.folder, book_folder)
    for scene in scenes:
        scene_issues = validate_scene(scene)
        for issue in scene_issues:
            if issue.severity == Severity.HARD:
                report.failures.append(issue.message)
            else:
                report.warnings.append(issue.message)

    if not chapter.drafting_plan.exists() or not read_text(chapter.drafting_plan).strip():
        report.failures.append(f"Missing or empty `{chapter.drafting_plan}`.")
    else:
        report.passes.append("Drafting plan exists.")

    scene_issues = validate_scene_breakdown(chapter)
    for issue in scene_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    if chapter.scene_breakdown.exists():
        combat_scenes = action.discover_combat_scenes(chapter.scene_breakdown)
        for c_scene in combat_scenes:
            scene_id = c_scene["id"]
            title = c_scene["title"]
            plan_path = action.get_action_plan_path(chapter.folder, scene_id)
            if not plan_path.exists():
                report.failures.append(f"Combat scene '{title}' is defined, but missing action plan: `{plan_path.name}`.")
            else:
                report.passes.append(f"Found combat plan for scene: {title}")
                if chapter.draft.exists():
                    c_passes, c_warnings, c_failures = action.validate_scene_combat(chapter.draft, plan_path)
                    report.passes.extend([f"[{title}] {p}" for p in c_passes])
                    report.warnings.extend([f"[{title}] {w}" for w in c_warnings])
                    report.failures.extend([f"[{title}] {f}" for f in c_failures])

    if chapter.scene_breakdown.exists() and chapter.draft.exists():
        book_folder = chapter.folder.parent.parent
        world_state_path = book_folder / "world-state.json"
        world_state = world_module.load_world_state(book_folder) if world_state_path.exists() else None

        from bookforge.core import relationship as relationship_module
        relationships = relationship_module.load_relationships(book_folder)

        scenes = world_module.discover_scenes_from_breakdown(chapter.scene_breakdown)
        draft_text = read_text(chapter.draft)

        scene_drafts = {}
        draft_sections = re.split(r"(?im)^(?=##|###|scene\s+\d+)", draft_text)
        current_key = "default"
        for sec in draft_sections:
            lines = sec.splitlines()
            if lines:
                match = re.search(r"(?i)scene[-_ ]*(\d+|\w+)", lines[0])
                if match:
                    current_key = f"scene-{match.group(1).lower()}".replace("-combat", "")
                    scene_drafts[current_key] = sec
                    continue
            scene_drafts[current_key] = scene_drafts.get(current_key, "") + "\n" + sec

        if world_state is not None:
            for scene in scenes:
                scene_id = scene["id"]
                title = scene["title"]
                scene_draft = scene_drafts.get(scene_id, draft_text)

                w_failures, w_warnings = world_module.validate_scene_world_state(scene, scene_draft, world_state)

                rel_failures, rel_warnings = relationship_module.validate_relationships_prose(scene, scene_draft, relationships)
                w_failures.extend(rel_failures)
                w_warnings.extend(rel_warnings)

                if not w_failures and not w_warnings:
                    report.passes.append(f"Physical logistics & relationships validated for scene: {title}")
                else:
                    report.failures.extend([f"[{title}] {f}" for f in w_failures])
                    report.warnings.extend([f"[{title}] {w}" for w in w_warnings])

            world_module.save_world_state(book_folder, world_state)

    draft_issues = validate_draft(chapter)
    for issue in draft_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    source_issues = validate_source_alignment(chapter, phase_sections)
    for issue in source_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    continuity_issues = validate_continuity_out_issues(chapter)
    for issue in continuity_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    pacing_issues = validate_chapter_pacing(chapter)
    for issue in pacing_issues:
        if issue.severity == Severity.HARD:
            report.failures.append(issue.message)
        else:
            report.warnings.append(issue.message)

    report.passes = list(dict.fromkeys(report.passes))
    report.failures = list(dict.fromkeys(report.failures))
    report.warnings = list(dict.fromkeys(report.warnings))
    return report




def collect_all_issues(book_folder: Path) -> tuple[ManuscriptIssue, ...]:
    all_issues: list[ManuscriptIssue] = []

    book_issues = validate_required_book_file_issues(book_folder)
    all_issues.extend(book_issues)

    phase_sections = parse_phase_chapters(book_folder)
    chapters = discover_chapters(book_folder)
    for chapter in chapters:
        all_issues.extend(validate_scene_breakdown(chapter))
        all_issues.extend(validate_draft(chapter))
        all_issues.extend(validate_source_alignment(chapter, phase_sections))
        all_issues.extend(validate_continuity_out_issues(chapter))
        all_issues.extend(validate_chapter_pacing(chapter))
        
        # Add scene validation issues
        from bookforge.core.scene import discover_scenes
        scenes = discover_scenes(chapter.folder, book_folder)
        for scene in scenes:
            all_issues.extend(validate_scene(scene))

    return tuple(all_issues)


def overall_status(book_failures: list[str], reports: list[ChapterReport]) -> str:
    if book_failures or any(report.failures for report in reports):
        return "FAIL"
    if any(report.warnings for report in reports):
        return "WARN"
    return "PASS"


def render_report(
    book_folder: Path,
    book_passes: list[str],
    book_failures: list[str],
    book_warnings: list[str],
    reports: list[ChapterReport],
) -> str:
    lines = [
        "# Manuscript Context Validation Report",
        "",
        f"- **Book Folder:** `{book_folder}`",
        f"- **Overall Status:** {overall_status(book_failures, reports)}",
        "- **Length Status:** Run `bf status <book_folder>` to view rhythm and word limits.",
        "",
        "## Book Files",
        "",
    ]
    for item in book_passes:
        lines.append(f"- PASS: {item}")
    for item in book_warnings:
        lines.append(f"- WARN: {item}")
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
            lines.append("- PASS: Deterministic checks passed.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate manuscript context and style rules.")
    parser.add_argument("book_folder", nargs="?", default="books/book-example", help="Path to book folder.")
    parser.add_argument("--chapter", help="Limit checks to a single chapter slug (e.g. chapter-01).")
    parser.add_argument("--ai-prompt", action="store_true", help="Generate an AI semantic review prompt.")
    return parser.parse_args()


def build_ai_prompt(book_folder: Path, chapter: ChapterFiles) -> str:
    from bookforge.core.scanner import source_path
    src = source_path(book_folder)
    if not src:
        raise RuntimeError("Missing outlining source.")
    source_paths = [
        src,
        book_folder / "rulebook.md",
        book_folder / "mood-lock.md",
        book_folder / "chapter-summaries.md",
        chapter.scene_breakdown,
        chapter.draft,
    ]
    for path in source_paths:
        if not path.exists():
            raise RuntimeError(f"Cannot build AI prompt; missing `{path}`.")

    template = load_prompt_template("validation/ai_review_prompt.md")
    return template.format(
        chapter_draft=chapter.draft,
        phase_0=src,
        rulebook=book_folder / "rulebook.md",
        mood_lock=book_folder / "mood-lock.md",
        chapter_summaries=book_folder / "chapter-summaries.md",
        scene_breakdown=chapter.scene_breakdown,
        chapter_label=chapter.label,
    )


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

    book_issues = validate_required_book_file_issues(book_folder)
    book_passes = [i.message for i in book_issues if i.severity == Severity.INFO]
    book_failures = [i.message for i in book_issues if i.severity == Severity.HARD]
    book_warnings = [i.message for i in book_issues if i.severity == Severity.SOFT]

    phase_sections = parse_phase_chapters(book_folder)
    reports = [validate_chapter(chapter, phase_sections) for chapter in chapters]
    print(render_report(book_folder, book_passes, book_failures, book_warnings, reports))
    return 1 if overall_status(book_failures, reports) == "FAIL" else 0
