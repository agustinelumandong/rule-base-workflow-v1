"""BookForge Persistent Memory Tier (Layer 3).

Public API re-exports — all callers using `from bookforge.core.memory import X`
or `from bookforge.core import memory as memory_core` continue to work unchanged.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from bookforge.core.memory.models import Chunk, Rule, MemoryStats, MemoryBackend
from bookforge.core.memory.chunker import scan_and_chunk_book
from bookforge.core.memory.rule_gen import generate_heuristic_rules, query_llm_for_rules
from bookforge.core.memory.backends import LocalEmbeddingBackend, HeadroomMemoryBackend, HAS_OFFICIAL_HEADROOM
from bookforge.core.memory.mcp_server import MemoryMCPServer


__all__ = [
    "Chunk",
    "Rule",
    "MemoryStats",
    "MemoryBackend",
    "scan_and_chunk_book",
    "generate_heuristic_rules",
    "query_llm_for_rules",
    "LocalEmbeddingBackend",
    "HeadroomMemoryBackend",
    "HAS_OFFICIAL_HEADROOM",
    "MemoryMCPServer",
    "get_memory_backend",
    "apply_proposal_rules",
]


def get_memory_backend(book_folder: Path) -> MemoryBackend:
    """Resolve and instantiate the configured/active memory backend."""
    if HAS_OFFICIAL_HEADROOM:
        db_path = book_folder / ".bookforge" / "memory.db"
        return HeadroomMemoryBackend(db_path)
    db_path = book_folder / ".bookforge" / "local_memory.json"
    return LocalEmbeddingBackend(db_path)


def apply_proposal_rules(book_folder: Path, proposal_id: str) -> list[str]:
    """Read proposal by UUID, apply rules to target files, and delete proposal."""
    proposal_path = book_folder / ".bookforge" / "proposals" / f"{proposal_id}.yml"
    if not proposal_path.exists():
        raise FileNotFoundError(f"Proposal {proposal_id} not found at {proposal_path}")

    with open(proposal_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    rules_data = data.get("rules", [])
    modified_files = []

    for r_dict in rules_data:
        rule = Rule(
            id=r_dict.get("id"),
            pattern=r_dict.get("pattern", ""),
            replacement=r_dict.get("replacement", ""),
            reason=r_dict.get("reason", ""),
            file=r_dict.get("file", ""),
            change=r_dict.get("change", "")
        )

        # Resolve target file path (book folder → cwd → grandparent)
        target_path = book_folder / rule.file
        if not target_path.exists():
            target_path = Path(rule.file)
        if not target_path.exists():
            target_path = book_folder.parent.parent / rule.file

        content = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

        if content:
            if target_path.suffix.lower() == ".md":
                change_str = rule.change.strip()
                if not change_str.startswith("-"):
                    change_str = f"- {change_str}"

                header_patterns = [
                    r"(##\s+Style\s+Rules\b)",
                    r"(##\s+Guardrails\b)",
                    r"(#\s+Manuscript\s+Agent\s+Instructions\b)"
                ]

                inserted = False
                for pat in header_patterns:
                    match = re.search(pat, content, re.IGNORECASE)
                    if match:
                        start_pos = match.end()
                        next_header_match = re.search(r"\n#+\s+", content[start_pos:])
                        if next_header_match:
                            end_pos = start_pos + next_header_match.start()
                            content = content[:end_pos].rstrip() + f"\n{change_str}\n\n" + content[end_pos:]
                        else:
                            content = content.rstrip() + f"\n{change_str}\n"
                        inserted = True
                        break

                if not inserted:
                    content = content.rstrip() + f"\n\n{change_str}\n"
            else:
                content = content.rstrip() + f"\n{rule.change.strip()}\n"
        else:
            content = f"# {rule.file}\n\n{rule.change.strip()}\n"

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        modified_files.append(str(target_path))

    proposal_path.unlink()
    return modified_files
