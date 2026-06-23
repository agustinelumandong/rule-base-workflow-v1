"""Patching and validation engine for scene-level prose corrections."""

from __future__ import annotations

import re
from pathlib import Path

from bookforge.core.scene import SceneManifest


def build_patch_packet(manifest: SceneManifest, failed_rules: list[str]) -> str:
    """Creates a targeted patch packet containing only failed rules, relevant context, and original draft."""
    draft_p = manifest.draft_path
    draft_content = draft_p.read_text(encoding="utf-8") if draft_p.exists() else "No draft found."

    parts = [
        f"# Patch Packet for: {manifest.scene_id} ({manifest.chapter})",
        "",
        "## Failed Rules / Validation Issues",
        "",
    ]
    for rule in failed_rules:
        parts.append(f"- {rule}")

    parts.extend([
        "",
        "## Scene manifest configuration",
        f"- **Required Beats:**",
    ])
    for beat in manifest.required_beats:
        parts.append(f"  - {beat}")

    if manifest.forbidden:
        parts.append("- **Forbidden:**")
        for term in manifest.forbidden:
            parts.append(f"  - {term}")

    parts.extend([
        "",
        "## Original Draft",
        "",
        "```markdown",
        draft_content,
        "```",
        "",
        "## Instructions",
        "Please rewrite ONLY the sections of the draft that violated the failed rules.",
        "Provide your corrected replacement segment wrapped in a ```markdown ... ``` block.",
        "For splicing, make sure to include 1-2 lines of surrounding text from the original draft at the start and end of the block as anchors.",
        "Do not include any conversational introductions, summaries, or metadata outside the code block."
    ])

    return "\n".join(parts) + "\n"


def splice_prose(original: str, replacement: str) -> tuple[bool, str]:
    """Splices replacement prose into the original text by matching anchors."""
    # Extract from code block if present
    block_match = re.search(r"```(?:markdown)?\n(.*?)\n```", replacement, re.DOTALL | re.IGNORECASE)
    if block_match:
        replacement = block_match.group(1)

    # Clean leading/trailing spaces
    original_clean = original.strip()
    replacement_clean = replacement.strip()

    if not replacement_clean:
        return False, "Replacement content is empty."

    # Split lines
    replacement_lines = [line.rstrip() for line in replacement_clean.splitlines() if line.strip()]
    
    # Try searching for SEARCH/REPLACE blocks first
    sr_pattern = r"(?:SEARCH|<<<<<<<.*?)\n(.*?)\n(?:=======|REPLACE)\n(.*?)(?:\n(?:>>>>>>>|<<<<<<<)|\Z)"
    sr_match = re.search(sr_pattern, replacement, re.DOTALL | re.IGNORECASE)
    if sr_match:
        target = sr_match.group(1).strip()
        repl = sr_match.group(2).strip()
        if target in original:
            return True, original.replace(target, repl)

    # Let's try matching prefix and suffix lines to find boundaries
    # Try with 2 lines, then 1 line
    for anchor_len in (2, 1):
        if len(replacement_lines) < anchor_len * 2:
            continue

        prefix_anchor = "\n".join(replacement_lines[:anchor_len])
        suffix_anchor = "\n".join(replacement_lines[-anchor_len:])

        prefix_idx = original.find(prefix_anchor)
        suffix_idx = original.find(suffix_anchor)

        if prefix_idx != -1 and suffix_idx != -1 and prefix_idx < suffix_idx:
            # We found the range! Replace it!
            new_text = original[:prefix_idx] + "\n".join(replacement_lines) + original[suffix_idx + len(suffix_anchor):]
            return True, new_text

    # Direct substring replacement if the replacement segment is fully contained in original
    if replacement_clean in original:
        return True, original

    return False, "Could not identify splice anchors or search/replace blocks in replacement prose."


def validate_merged_prose(merged_prose: str, target_words: int) -> list[str]:
    """Validates the spliced merged prose against requirements (conversational text, word count)."""
    errors = []

    # Check for conversational prefix/suffix
    lines = [line.strip() for line in merged_prose.splitlines() if line.strip()]
    if lines:
        for idx in range(min(5, len(lines))):
            line = lines[idx]
            if re.search(r"^(here is|sure|revised|corrected|ok|this is|i have|draft|rewrite)\b", line, re.IGNORECASE):
                errors.append(f"Conversational line detected in merged prose header: '{line}'")

        for idx in range(max(0, len(lines) - 5), len(lines)):
            line = lines[idx]
            if re.search(r"^(here is|sure|revised|corrected|ok|this is|i have|draft|rewrite)\b", line, re.IGNORECASE):
                errors.append(f"Conversational line detected in merged prose footer: '{line}'")

    # Check for markdown code blocks that shouldn't be nested
    if "```" in merged_prose:
        errors.append("Merged prose contains markdown code block markers (```).")

    # Word count check
    words = len(re.findall(r"\b\w+\b", merged_prose))
    lower_bound = int(target_words * 0.8)
    upper_bound = int(target_words * 1.2)
    if words < lower_bound or words > upper_bound:
        errors.append(f"Merged prose word count ({words}) is outside ±20% tolerance of target ({target_words} words, range {lower_bound}-{upper_bound}).")

    return errors
