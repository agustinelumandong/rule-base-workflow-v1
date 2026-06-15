"""BookForge Context Compression (Headroom) Module.

Provides token-saving compression for prompts and context packets.
"""

from __future__ import annotations

import re
from pathlib import Path

# Try to import official headroom if installed
try:
    import headroom
    HAS_OFFICIAL_HEADROOM = True
except ImportError:
    HAS_OFFICIAL_HEADROOM = False


def compress_text(text: str) -> str:
    """Compress context text to save tokens.
    
    If headroom-ai is installed, delegates to it.
    Otherwise, uses the local fallback compressor.
    """
    if HAS_OFFICIAL_HEADROOM:
        try:
            # Official headroom typically exposes a compress function or class
            if hasattr(headroom, "compress"):
                return headroom.compress(text)
        except Exception:
            pass # Fall back to local compression on failure
            
    return compress_local(text)


def compress_local(text: str) -> str:
    """Zero-dependency local Markdown/text context compressor.
    
    Aims for 30-50% token reduction by stripping layout noise,
    conversational fillers, and duplicate elements, while preserving
    critical facts, headings, and markdown structures.
    """
    if not text.strip():
        return ""
        
    lines = text.splitlines()
    compressed_lines: list[str] = []
    
    # Conversational/instructional fillers to prune
    FILLER_PATTERNS = [
        (re.compile(r"\bplease\s+(?:make\s+sure\s+to|ensure\s+that|remember\s+to)\b", re.I), ""),
        (re.compile(r"\bthe\s+following\s+is\s+(?:a|the|an)\b", re.I), ""),
        (re.compile(r"\bin\s+order\s+to\b", re.I), "to"),
        (re.compile(r"\bas\s+(?:mentioned|described|detailed)\s+(?:above|previously)\b", re.I), ""),
        (re.compile(r"\bfor\s+the\s+purpose\s+of\b", re.I), "for"),
        (re.compile(r"\bwith\s+respect\s+to\b", re.I), "on"),
        (re.compile(r"\ba\s+number\s+of\b", re.I), "some"),
        (re.compile(r"\bso\s+as\s+to\b", re.I), "to"),
    ]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Let's keep at most one empty line to preserve paragraph breaks
            if compressed_lines and compressed_lines[-1] != "":
                compressed_lines.append("")
            continue
            
        # Do not compress or modify special system headers or locks
        if (
            stripped.startswith("### Source Context Lock") or
            stripped.startswith("### Beat Instructions") or
            stripped.startswith("- **Source Anchor:**") or
            stripped.startswith("- **Required Story Movement:**") or
            stripped.startswith("- **Continuity In:**") or
            stripped.startswith("- **Continuity Out:**")
        ):
            compressed_lines.append(line)
            continue
            
        # Simplify fillers in standard prose/instructions
        modified_line = line
        for pattern, replacement in FILLER_PATTERNS:
            modified_line = pattern.sub(replacement, modified_line)
            
        # Collapse multiple spaces
        modified_line = re.sub(r"[ \t]+", " ", modified_line)
        
        # Strip decorative separators like --- or ***
        if re.match(r"^(?:-{3,}|\*{3,}|_{3,})$", modified_line.strip()):
            continue
            
        # Keep non-empty modified lines
        if modified_line.strip():
            compressed_lines.append(modified_line)
            
    # Join and strip trailing space
    return "\n".join(compressed_lines).strip()
