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


def _compress_block_with_headroom(text: str) -> str:
    """Helper to compress a single non-lock text block using headroom."""
    try:
        # 1. Try using the universal text compressor designed for raw strings
        try:
            from headroom.compression.universal import compress as universal_compress
            result = universal_compress(text)
            if hasattr(result, "compressed") and isinstance(result.compressed, str):
                if len(result.compressed) < len(text):
                    return result.compressed
        except (ImportError, AttributeError):
            pass

        # 2. Try the message-based compressor by packaging the string into a message list
        if hasattr(headroom, "compress"):
            messages = [{"role": "system", "content": text}]
            result = headroom.compress(
                messages,
                min_tokens_to_compress=0,
                compress_system_messages=True
            )
            if hasattr(result, "messages") and isinstance(result.messages, list) and len(result.messages) > 0:
                compressed_content = result.messages[0].get("content")
                if isinstance(compressed_content, str) and len(compressed_content) < len(text):
                    return compressed_content
    except Exception:
        pass
    return text


def compress_text(text: str) -> str:
    """Compress context text to save tokens.
    
    If headroom-ai is installed, delegates non-locked text blocks to it.
    Otherwise, uses the local fallback compressor.
    """
    if not text.strip():
        return ""

    if HAS_OFFICIAL_HEADROOM:
        try:
            lines = text.splitlines()
            blocks: list[tuple[bool, list[str]]] = []
            
            for line in lines:
                stripped = line.strip()
                is_lock = (
                    stripped.startswith("### Source Context Lock") or
                    stripped.startswith("### Beat Instructions") or
                    stripped.startswith("- **Source Anchor:**") or
                    stripped.startswith("- **Required Story Movement:**") or
                    stripped.startswith("- **Continuity In:**") or
                    stripped.startswith("- **Continuity Out:**")
                )
                
                if not blocks or blocks[-1][0] != is_lock:
                    blocks.append((is_lock, [line]))
                else:
                    blocks[-1][1].append(line)
            
            compressed_blocks = []
            for is_lock, block_lines in blocks:
                block_text = "\n".join(block_lines)
                if is_lock:
                    compressed_blocks.append(block_text)
                else:
                    # Compress standard content block using headroom
                    compressed_blocks.append(_compress_block_with_headroom(block_text))
            
            final_text = "\n".join(compressed_blocks)
            if len(final_text) < len(text):
                return final_text
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
