#!/usr/bin/env python3
"""BookForge Advanced Style, Voice, & POV Gating Module."""

from __future__ import annotations

import re
from pathlib import Path

# Banned Texas Slang (unless explicitly requested)
BANNED_TEXAS_SLANG = ["y'all", "howdy", "partner", "reckon", "drawl"]

# Common Dialogue Tags that are discouraged when em dash action anchors are active
DISCOURAGED_DIALOGUE_TAGS = ["said", "asked", "shouted", "replied", "whispered", "muttered", "cried", "exclaimed"]


def validate_dialogue_style(draft_text: str) -> tuple[list[str], list[str]]:
    """Validates dialogue rules: em dash spacing, dialogue tag avoidance, and slang.
    
    Returns (failures, warnings).
    """
    failures = []
    warnings = []
    
    # 1. Check for Texas slang
    for slang in BANNED_TEXAS_SLANG:
        pattern = re.compile(rf"\b{re.escape(slang)}\b", re.IGNORECASE)
        if pattern.search(draft_text):
            warnings.append(f"Slang Warning: Found discouraged Texas slang '{slang}' in draft.")

    # 2. Parse dialogues and check tag / em dash anchor formatting
    # Regex to find quotes and the immediately following text up to the end of the sentence or next quote
    quote_matches = list(re.finditer(r'"([^"]+)"\s*(.*?)(?="|\.|\n|$)', draft_text))
    
    for match in quote_matches:
        quote_content = match.group(1)
        following_text = match.group(2).strip()
        
        # Check for discouraged dialogue tags right after quote
        # e.g., "Get on the horse," said Harlan.
        for tag in DISCOURAGED_DIALOGUE_TAGS:
            tag_pattern = re.compile(rf"\b{re.escape(tag)}\b", re.IGNORECASE)
            if tag_pattern.match(following_text):
                warnings.append(
                    f"Dialogue Tag Warning: Discouraged dialogue tag '{tag}' used directly after dialogue: '\"{quote_content[:15]}...\" {following_text[:15]}'"
                )

        # Check for em dash spacing if an em dash is used.
        if "--" in following_text or "—" in following_text:
            if "--" in following_text:
                failures.append(
                    f"Em Dash Formatting Failure: Use em-dash `—` instead of double-hyphen `--` in '\"{quote_content[:15]}...\" {following_text[:20]}'."
                )
            elif not re.match(r"^—\s+\S", following_text):
                failures.append(
                    f"Em Dash Formatting Failure: Incorrect em-dash anchor spacing in '\"{quote_content[:15]}...\" {following_text[:20]}'. Use `\"Dialogue.\" — Action`."
                )

    return failures, warnings


def validate_pov_locking(draft_text: str, pov_character: str, all_characters: list[str]) -> list[str]:
    """Checks for POV head-hopping (other characters' internal states/feelings).
    
    Returns list of failures.
    """
    failures = []
    if not pov_character:
        return failures
        
    pov_lower = pov_character.lower()
    other_chars = [c for c in all_characters if c.lower() != pov_lower]
    
    # Verbs indicating internal state
    internal_state_verbs = [
        "felt", "realized", "thought", "knew", "believed", 
        "remembered", "wished", "wanted", "hoped", "sensed", 
        "wondered", "decided", "understood"
    ]
    
    for char in other_chars:
        # Match "Darin felt...", "Darin realized..."
        pattern = re.compile(
            rf"\b{re.escape(char)}\b.*?\b(" + "|".join(internal_state_verbs) + r")\b",
            re.IGNORECASE | re.DOTALL
        )
        # Scan sentence by sentence to keep context localized
        sentences = re.split(r"(?<=[.!?])\s+", draft_text)
        for idx, sentence in enumerate(sentences):
            if pattern.search(sentence):
                failures.append(
                    f"POV Head-Hopping Failure: Internal state of non-POV character '{char}' is described in: '{sentence.strip()}' (Locked POV: {pov_character.capitalize()})."
                )
                
    return failures


def validate_sentence_openers(draft_text: str) -> tuple[list[str], list[str]]:
    """Enforces rules against -ing openers and repeated pronoun/name loops.
    
    Returns (failures, warnings).
    """
    failures = []
    warnings = []
    
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", draft_text) if s.strip()]
    
    # 1. -ing opener check
    # Match sentences starting with a word ending in 'ing' followed by a space
    for sentence in sentences:
        first_word_match = re.match(r"^([a-zA-Z]+)ing\b", sentence)
        if first_word_match:
            word = first_word_match.group(0)
            # Filter out common non-gerund starters like "During"
            exclusions = {
                "during", "bring", "ring", "sing", "thing", "spring",
                "morning", "evening", "nothing", "something", "everything", "anything",
                "king", "wing", "sling", "string", "cling", "fling", "sting", "swing", "wring",
                "lightning", "awning", "ceiling", "lining", "sterling", "cunning", "darling",
                "sibling", "sapling", "farthing", "inkling", "shilling", "herring", "pudding"
            }
            if word.lower() not in exclusions:
                failures.append(
                    f"Sentence Opener Failure: Discouraged '-ing' word opener in: '{sentence[:50]}...'"
                )

    # 2. Repeated pronoun/name loop (same start for 3 or more consecutive sentences)
    loop_count = 1
    last_starter = None
    
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        first_word = re.sub(r"[^a-zA-Z]+", "", words[0]).lower()
        if not first_word:
            continue
            
        if first_word == last_starter:
            loop_count += 1
            if loop_count >= 3:
                warnings.append(
                    f"Pronoun Loop Warning: Repeated sentence opening word '{first_word}' for {loop_count} consecutive sentences starting at: '{sentence[:50]}...'"
                )
        else:
            loop_count = 1
            last_starter = first_word

    return failures, warnings
