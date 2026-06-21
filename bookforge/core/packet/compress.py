"""Text compression wrapper and style lock representations."""

from __future__ import annotations
from bookforge.core.adapters.compression import get_compression_backend

COMPRESSED_STYLE_LOCK = (
    "Literal Western prose; no AI echo words; no modern/clinical terms; "
    "no dialogue tags when action anchors are requested; behavior over thought; source-locked."
)


def compress_text(text: str) -> str:
    return get_compression_backend().compress(text)
