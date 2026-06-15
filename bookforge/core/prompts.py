"""BookForge Prompt Loader Module.

Loads first-class versioned prompt files from the package directory.
"""

from __future__ import annotations

from pathlib import Path


def load_prompt_template(name: str) -> str:
    """Load a prompt template from the bookforge/prompts directory.
    
    Args:
        name: Relative path to the prompt file (e.g. 'validation/ai_review_prompt.md').
        
    Returns:
        The content of the prompt file.
    """
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / name
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template `{name}` not found in {prompts_dir}")
    
    return prompt_file.read_text(encoding="utf-8")
