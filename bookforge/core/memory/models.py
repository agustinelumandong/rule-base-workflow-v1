"""Shared dataclasses and Protocol for the memory subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Any


@dataclass
class Chunk:
    """Represents a piece of indexed knowledge."""
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Rule:
    """Represents a rule proposal generated from a failed session."""
    id: str
    pattern: str
    replacement: str
    reason: str
    file: str
    change: str


@dataclass
class MemoryStats:
    """Represents statistics about the active memory database."""
    num_memories: int
    backend_type: str
    db_path: str
    extra_info: dict[str, Any] = field(default_factory=dict)


class MemoryBackend(Protocol):
    """Protocol for cross-session persistent memory backends."""

    def build(self, book_folder: Path) -> None:
        """Scan, chunk, and index all book assets."""
        ...

    def retrieve(self, query: str, limit: int = 10) -> list[Chunk]:
        """Search the persistent index for relevant chunks."""
        ...

    def resolve(self, book_folder: Path, name: str) -> str | None:
        """Resolve a proper name or alias to canonical ID using aliases.yml with semantic fallback."""
        ...

    def learn(self, failed_session: str) -> list[Rule]:
        """Analyze a failed session log and suggest corrective rules."""
        ...

    def stats(self) -> MemoryStats:
        """Get database size and connection metrics."""
        ...

    def clear(self) -> None:
        """Clear all stored memory in this backend."""
        ...
