#!/usr/bin/env python3
"""BookForge Role & Persona Registry Core Module."""

from __future__ import annotations

import json
import yaml
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
    """Finds and loads the model-routing.yml or legacy persona-registry.json config."""
    # 1. Check book folder local overrides first (both YAML and JSON)
    if book_folder:
        local_yaml = Path(book_folder) / "spec" / "model-routing.yml"
        if local_yaml.exists():
            try:
                data = yaml.safe_load(local_yaml.read_text(encoding="utf-8"))
                if data and "personas" in data:
                    return data
            except Exception:
                pass

        local_json = Path(book_folder) / "persona-registry.json"
        if local_json.exists():
            try:
                return json.loads(local_json.read_text(encoding="utf-8"))
            except Exception:
                pass

    # 2. Check root configurations next
    root_yaml = Path("spec/model-routing.yml")
    if root_yaml.exists():
        try:
            data = yaml.safe_load(root_yaml.read_text(encoding="utf-8"))
            if data and "personas" in data:
                return data
        except Exception:
            pass

    root_json = Path("persona-registry.json")
    if root_json.exists():
        try:
            return json.loads(root_json.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 3. Create default in root and return
    try:
        root_json.write_text(json.dumps(DEFAULT_REGISTRY, indent=2), encoding="utf-8")
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
    examples = p_config.get("examples", [])
    model_class = p_config.get("model_class")

    # Class mappings: cheap, mid, strong
    model_classes = {
        "cheap": ["gpt-4o-mini", "claude-3-5-haiku", "gemini-1.5-flash", "local-7b"],
        "mid": ["gpt-4o", "claude-3-5-haiku", "claude-3-5-sonnet", "gemini-1.5-pro", "gpt-4o-mini"],
        "strong": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro", "gpt-4", "opus"]
    }

    model_ok = False
    if allowed_models and model in allowed_models:
        model_ok = True
    elif model in examples:
        model_ok = True
    elif model_class:
        allowed_class_models = model_classes.get(model_class, [])
        if model in allowed_class_models:
            model_ok = True
        else:
            for acm in allowed_class_models:
                if acm in model or model in acm:
                    model_ok = True
                    break

    if not model_ok:
        allowed_desc = allowed_models or examples or [f"class: {model_class}"]
        return False, f"Model '{model}' is not authorized for persona '{persona_name}' (allowed: {allowed_desc})."

    # 3. Action authorization verification
    allowed_actions = p_config.get("allowed_actions", [])
    tasks = p_config.get("tasks", [])
    
    # Map legacy actions to v2 tasks
    action_mappings = {
        "draft": "draft_prose",
        "style": "style_scan_semantic",
        "validate": "validate_review",
        "init": "memory_build",
        "plan": "classify_beats",
        "status": "summarize_continuity",
        "init-action": "memory_build",
        "compile": "memory_build"
    }
    mapped_action = action_mappings.get(action, action)
    
    action_ok = False
    if action in allowed_actions or action in tasks:
        action_ok = True
    elif mapped_action in allowed_actions or mapped_action in tasks:
        action_ok = True
    else:
        for t in tasks + allowed_actions:
            if action in t or t in action:
                action_ok = True
                break

    if not action_ok:
        return False, f"Action '{action}' is not authorized for persona '{persona_name}' (allowed: {allowed_actions or tasks})."

    # 4. Token limit verification
    default_limits = {
        "extractor": 100000,
        "planner": 100000,
        "writer": 50000,
        "reviewer": 80000
    }
    default_limit = default_limits.get(persona_name, 100000)
    token_limit = p_config.get("token_budget_limit", default_limit)
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
