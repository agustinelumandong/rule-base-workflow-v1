"""Heuristic and LLM-based rule generation from failed sessions."""

from __future__ import annotations

import json
import os
import re
import urllib.request
import urllib.error

from bookforge.core.memory.models import Rule


def generate_heuristic_rules(failed_session: str) -> list[Rule]:
    """Inspect failed session logs for standard violations and propose changes."""
    rules = []

    from bookforge.core.loop import STYLE_TERMS
    matched_style_words = [
        term for term in STYLE_TERMS
        if re.search(rf"\b{re.escape(term)}\b", failed_session, re.IGNORECASE)
    ]

    if matched_style_words:
        word_list_str = ", ".join(f"'{w}'" for w in matched_style_words)
        rules.append(Rule(
            id="style_banned_echo_words",
            pattern=f"\\b({'|'.join(re.escape(w) for w in matched_style_words)})\\b",
            replacement="",
            reason=f"Detected banned AI echo word(s): {word_list_str}",
            file="rulebook.md",
            change=f"\n- Avoid using AI echo words: {word_list_str}."
        ))

    if "dialogue tag" in failed_session.lower() or "said" in failed_session.lower() or "asked" in failed_session.lower():
        rules.append(Rule(
            id="style_no_dialogue_tags",
            pattern=r'\b(said|asked|shouted|replied)\b',
            replacement="",
            reason="Dialogue tags are discouraged when em dash action anchors are active.",
            file="rulebook.md",
            change="\n- Do not use dialogue tags like 'said' or 'asked' when using action anchors."
        ))

    if "teleport" in failed_session.lower() or "location" in failed_session.lower() or "drift" in failed_session.lower():
        rules.append(Rule(
            id="canon_location_consistency",
            pattern="",
            replacement="",
            reason="Character location drift/teleportation detected in validation.",
            file="rulebook.md",
            change="\n- Characters must travel step-by-step. Verify character locations in the snapshot before drafting."
        ))

    if "inventory" in failed_session.lower() or "weapon" in failed_session.lower() or "object" in failed_session.lower():
        rules.append(Rule(
            id="canon_inventory_consistency",
            pattern="",
            replacement="",
            reason="Character using items not registered in their active inventory.",
            file="rulebook.md",
            change="\n- Characters can only use weapons or objects in their active inventory snapshot."
        ))

    if "dead" in failed_session.lower() or "status" in failed_session.lower():
        rules.append(Rule(
            id="canon_status_consistency",
            pattern="",
            replacement="",
            reason="A character marked as dead was found performing actions or speaking in the draft.",
            file="rulebook.md",
            change="\n- Dead characters cannot act or speak. Verify character status in the snapshot."
        ))

    if not rules:
        rules.append(Rule(
            id="general_style_lock_enforcement",
            pattern="",
            replacement="",
            reason="General drafting validation failure detected in the session.",
            file="rulebook.md",
            change="\n- Strictly enforce behavior-driven, literal Western prose styles."
        ))

    return rules


def query_llm_for_rules(failed_session: str) -> list[Rule] | None:
    """Call external LLM APIs (OpenAI/Anthropic/Gemini) if configured."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not (openai_key or anthropic_key or gemini_key):
        return None

    prompt = (
        "You are an expert Western fiction editor and writing pipeline validator. "
        "Analyze the following validation/compilation failure log from a writing session:\n\n"
        f"--- FAILURE LOG ---\n{failed_session}\n-------------------\n\n"
        "Generate 1 to 3 style or guardrail rules to add to rulebook.md or AGENTS.md to prevent this issue. "
        "Each rule must have a unique ID, clear reason, and exact file changes. "
        "Format the output strictly as a JSON object matching this schema:\n"
        "{\n"
        '  "rules": [\n'
        '    {\n'
        '      "id": "rule_id",\n'
        '      "pattern": "regex_pattern_or_empty",\n'
        '      "replacement": "replacement_prose_or_empty",\n'
        '      "reason": "why this rule was added",\n'
        '      "file": "rulebook.md",\n'
        '      "change": "exact text to append/insert"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    text = None
    try:
        if anthropic_key:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            data = json.dumps({
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}]
            }).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                text = res_body["content"][0]["text"]

        elif openai_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "content-type": "application/json"
            }
            data = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                text = res_body["choices"][0]["message"]["content"]

        else:  # gemini_key
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            headers = {"content-type": "application/json"}
            data = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                text = res_body["candidates"][0]["content"]["parts"][0]["text"]

        if text:
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                return [
                    Rule(
                        id=r["id"],
                        pattern=r.get("pattern", ""),
                        replacement=r.get("replacement", ""),
                        reason=r["reason"],
                        file=r["file"],
                        change=r["change"]
                    )
                    for r in parsed.get("rules", [])
                ]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError, ValueError):
        pass

    return None
