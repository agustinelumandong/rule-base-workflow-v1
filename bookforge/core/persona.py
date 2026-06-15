#!/usr/bin/env python3
"""BookForge Role & Persona Registry Core Module."""

from __future__ import annotations

import json
from pathlib import Path
from bookforge.core import analytics as analytics_module

# Price per 1,000 tokens
MODEL_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku": {"input": 0.001, "output": 0.005},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.00375},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
}

DEFAULT_REGISTRY = {
    "personas": {
        "planner": {
            "allowed_models": ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"],
            "allowed_actions": ["init", "plan", "status", "compile", "init-action"],
            "token_budget_limit": 100000,
            "max_retries": 3,
            "description": "Orchestrates outline, chapter breakdown, and pacing plans."
        },
        "writer": {
            "allowed_models": ["gpt-4o-mini", "claude-3-5-haiku", "gemini-1.5-flash"],
            "allowed_actions": ["draft", "expand", "style"],
            "token_budget_limit": 50000,
            "max_retries": 4,
            "description": "Drafts prose scene-by-scene matching Western style locks."
        },
        "reviewer": {
            "allowed_models": ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"],
            "allowed_actions": ["validate", "check-continuity"],
            "token_budget_limit": 80000,
            "max_retries": 2,
            "description": "Validates chapter continuity, style requirements, and alignment."
        }
    },
    "global_budget_cap_usd": 15.00
}


def load_registry(book_folder: Path | None = None) -> dict[str, any]:
    """Finds and loads the persona-registry.json config."""
    # 1. Check book folder override
    if book_folder:
        local_path = Path(book_folder) / "persona-registry.json"
        if local_path.exists():
            try:
                return json.loads(local_path.read_text(encoding="utf-8"))
            except Exception:
                pass

    # 2. Check root folder
    root_path = Path("persona-registry.json")
    if root_path.exists():
        try:
            return json.loads(root_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 3. Create default in root and return
    try:
        root_path.write_text(json.dumps(DEFAULT_REGISTRY, indent=2), encoding="utf-8")
    except Exception:
        pass
    return DEFAULT_REGISTRY


def calculate_run_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculates the estimated cost of an LLM call in USD."""
    pricing = MODEL_PRICING.get(model, {"input": 0.002, "output": 0.008}) # fallback default pricing
    input_cost = (input_tokens / 1000.0) * pricing["input"]
    output_cost = (output_tokens / 1000.0) * pricing["output"]
    return input_cost + output_cost


def calculate_cumulative_cost(book_folder: Path) -> float:
    """Calculates cumulative cost of all logged runs for a book folder in USD."""
    analytics = analytics_module.load_analytics(book_folder)
    total_cost = 0.0
    for run in analytics.get("runs", []):
        model = run.get("model", "")
        in_tok = run.get("input_tokens", 0)
        out_tok = run.get("output_tokens", 0)
        total_cost += calculate_run_cost(model, in_tok, out_tok)
    return total_cost


def check_persona_capabilities(
    book_folder: Path,
    persona_name: str,
    model: str,
    action: str,
    projected_input_tokens: int = 0
) -> tuple[bool, str]:
    """Validates if an LLM call matches all registry rules.
    
    Returns (is_allowed, reason_message).
    """
    registry = load_registry(book_folder)
    personas = registry.get("personas", {})
    
    # 1. Persona verification
    if persona_name not in personas:
        return False, f"Persona '{persona_name}' is not registered."

    p_config = personas[persona_name]
    
    # 2. Model authorization verification
    allowed_models = p_config.get("allowed_models", [])
    if model not in allowed_models:
        return False, f"Model '{model}' is not authorized for persona '{persona_name}' (allowed: {allowed_models})."

    # 3. Action authorization verification
    allowed_actions = p_config.get("allowed_actions", [])
    if action not in allowed_actions:
        return False, f"Action '{action}' is not authorized for persona '{persona_name}' (allowed: {allowed_actions})."

    # 4. Token limit verification
    token_limit = p_config.get("token_budget_limit", 100000)
    if projected_input_tokens > token_limit:
        return False, f"Projected input tokens ({projected_input_tokens}) exceed persona '{persona_name}' budget limit ({token_limit})."

    # 5. Global budget cap verification
    global_cap = registry.get("global_budget_cap_usd", 15.00)
    cumulative_cost = calculate_cumulative_cost(book_folder)
    
    # Projected cost estimation (assume output is 25% of input)
    projected_output_tokens = projected_input_tokens // 4
    projected_cost = calculate_run_cost(model, projected_input_tokens, projected_output_tokens)
    
    if cumulative_cost + projected_cost > global_cap:
        return False, f"LLM call blocked: Projected cost (${cumulative_cost + projected_cost:.4f}) exceeds global budget cap (${global_cap:.2f})."

    return True, "LLM call authorized."
