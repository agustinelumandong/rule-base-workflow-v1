#!/usr/bin/env python3
"""BookForge Analytics Core Module."""

from __future__ import annotations

import json
import datetime
from pathlib import Path
from bookforge.core import validator as context_validator

# Try importing tiktoken
try:
    import tiktoken
    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:
    _ENCODING = None


def estimate_tokens(text: str) -> int:
    """Estimate token count of a given string using tiktoken, with a character fallback."""
    if not text:
        return 0
    if _ENCODING is not None:
        try:
            return len(_ENCODING.encode(text, disallowed_special=()))
        except Exception:
            pass
    # Fallback: roughly 1 token per 4 characters
    return max(1, len(text) // 4)


def get_file_metrics(filepath: Path) -> dict[str, int]:
    """Calculate lines, words, chars, and estimated tokens for a single file."""
    if not filepath.exists() or not filepath.is_file():
        return {"lines": 0, "words": 0, "chars": 0, "tokens": 0}
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return {"lines": 0, "words": 0, "chars": 0, "tokens": 0}
        
    lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    words = len(text.split())
    chars = len(text)
    tokens = estimate_tokens(text)
    return {
        "lines": lines,
        "words": words,
        "chars": chars,
        "tokens": tokens
    }


def get_project_file_analytics(book_folder: Path) -> dict[str, any]:
    """Scan book folder and calculate metrics for outline, rules, and chapters."""
    analytics: dict[str, any] = {}
    
    # Core outline & configuration files
    from bookforge.core import scanner
    from bookforge.core.research import get_research_pack_path
    outline_path = scanner.source_path(book_folder)
    core_files = {
        "outline": outline_path if outline_path else (book_folder / "phase-0.md"),
        "rulebook": book_folder / "rulebook.md",
        "mood_lock": book_folder / "mood-lock.md",
        "chapter_summaries": book_folder / "chapter-summaries.md",
        "research_pack": get_research_pack_path(book_folder)
    }
    
    for name, path in core_files.items():
        if path.exists():
            analytics[name] = {
                "filename": path.name,
                "path": str(path),
                "metrics": get_file_metrics(path)
            }

    # Chapters metrics
    chapters = context_validator.discover_chapters(book_folder)
    chapters_analytics = []
    for chap in chapters:
        chap_data = {
            "slug": chap.slug,
            "label": chap.label,
            "folder": str(chap.folder),
            "files": {}
        }
        
        # Check breakdown, draft, continuity
        for f_name, path in [
            ("scene_breakdown", chap.scene_breakdown),
            ("draft", chap.draft),
            ("continuity_out", chap.folder / "continuity-out.md")
        ]:
            if path.exists():
                chap_data["files"][f_name] = {
                    "filename": path.name,
                    "path": str(path),
                    "metrics": get_file_metrics(path)
                }
        chapters_analytics.append(chap_data)
        
    analytics["chapters"] = chapters_analytics
    return analytics


def get_analytics_file_path(book_folder: Path) -> Path:
    return book_folder / "analytics.json"


def load_analytics(book_folder: Path) -> dict[str, any]:
    path = get_analytics_file_path(book_folder)
    if not path.exists():
        return {
            "total_runs": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "last_model_used": "unknown",
            "runs": []
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Ensure default structure is present
        for key, default_val in [
            ("total_runs", 0),
            ("total_input_tokens", 0),
            ("total_output_tokens", 0),
            ("last_model_used", "unknown"),
            ("runs", [])
        ]:
            if key not in data:
                data[key] = default_val
        return data
    except Exception:
        return {
            "total_runs": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "last_model_used": "unknown",
            "runs": []
        }


def save_analytics(book_folder: Path, data: dict[str, any]) -> None:
    path = get_analytics_file_path(book_folder)
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def log_run(book_folder: Path, model: str, input_tokens: int, output_tokens: int, action: str) -> dict[str, any]:
    data = load_analytics(book_folder)
    
    # Update totals
    data["total_runs"] = data.get("total_runs", 0) + 1
    data["total_input_tokens"] = data.get("total_input_tokens", 0) + input_tokens
    data["total_output_tokens"] = data.get("total_output_tokens", 0) + output_tokens
    data["last_model_used"] = model
    
    # Append run entry
    run_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "action": action,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    }
    
    if "runs" not in data:
        data["runs"] = []
    data["runs"].append(run_entry)
    
    # Keep last 50 runs to avoid file bloat
    if len(data["runs"]) > 50:
        data["runs"] = data["runs"][-50:]
        
    save_analytics(book_folder, data)
    return data
