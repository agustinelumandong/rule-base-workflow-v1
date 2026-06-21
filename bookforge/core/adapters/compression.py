"""BookForge Context Compression Adapters Module."""

from __future__ import annotations

import re
from typing import Protocol

# Try to import official headroom if installed
try:
    import headroom
    HAS_OFFICIAL_HEADROOM = True
except ImportError:
    HAS_OFFICIAL_HEADROOM = False


class CompressionBackend(Protocol):
    """Protocol defining the interface for context compression backends."""

    def compress(self, text: str) -> str:
        """Compresses context text to reduce token footprint."""
        ...


class LocalRegexBackend:
    """Zero-dependency local Markdown/text context compressor."""

    def compress(self, text: str) -> str:
        """Aims for 30-50% token reduction by stripping layout noise,

        redundant spacing, and filler phrases, while keeping structured block headers.
        """
        if not text.strip():
            return ""

        # Remove HTML/XML/Markdown comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        lines = text.splitlines()
        processed = []
        for line in lines:
            # Keep markdown headers intact
            if line.strip().startswith("#"):
                processed.append(line.rstrip())
                continue

            # Strip leading/trailing spaces
            l = line.strip()
            if not l:
                processed.append("")
                continue

            # Reduce multiple spaces within lines
            l = re.sub(r"[ \t]+", " ", l)

            # Skip lines that are purely separator symbols
            if re.match(r"^[=\-_*]{3,}$", l):
                continue

            processed.append(l)

        # Consolidate multiple blank lines into at most one blank line
        res = "\n".join(processed)
        res = re.sub(r"\n{3,}", "\n\n", res)
        return res.strip()


class HeadroomBackend:
    """Wrapper backend for the official Headroom compression engine."""

    def __init__(self) -> None:
        self.local = LocalRegexBackend()

    def _compress_block_with_headroom(self, text: str) -> str:
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
        except (AttributeError, ValueError, TypeError, KeyError):
            pass
        return text

    def compress(self, text: str) -> str:
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
                        compressed_blocks.append(self._compress_block_with_headroom(block_text))
                
                final_text = "\n".join(compressed_blocks)
                if len(final_text) < len(text):
                    return final_text
            except (ValueError, TypeError, KeyError, AttributeError):
                pass # Fall back to local compression on failure
                
        return self.local.compress(text)


def get_compression_backend(backend_type: str = "default") -> CompressionBackend:
    """Returns the configured compression backend."""
    if backend_type == "headroom" or (backend_type == "default" and HAS_OFFICIAL_HEADROOM):
        return HeadroomBackend()
    return LocalRegexBackend()
