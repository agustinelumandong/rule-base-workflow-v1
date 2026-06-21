"""Local TF-IDF and Headroom SDK memory backend implementations."""

from __future__ import annotations

import asyncio
import json
import math
import re
from pathlib import Path
from typing import Any

from bookforge.core.memory.models import Chunk, Rule, MemoryStats
from bookforge.core.memory.chunker import scan_and_chunk_book
from bookforge.core.memory.rule_gen import query_llm_for_rules, generate_heuristic_rules

# Try to import official headroom if installed
try:
    from headroom.memory.easy import Memory
    HAS_OFFICIAL_HEADROOM = True
except ImportError:
    HAS_OFFICIAL_HEADROOM = False


def _resolve_alias(book_folder: Path, name: str, retrieve_fn) -> str | None:
    """Shared alias resolution: aliases.yml first, semantic retrieval fallback."""
    aliases_file = book_folder / "canon" / "entities" / "aliases.yml"
    if aliases_file.exists():
        import yaml
        try:
            aliases_data = yaml.safe_load(aliases_file.read_text(encoding="utf-8"))
            if isinstance(aliases_data, dict):
                aliases = aliases_data.get("aliases", {})
                norm_name = re.sub(
                    r"^(marshal|sheriff|deputy|mr\.|mrs\.|miss|doctor|doc)\s+",
                    "",
                    name.lower().strip()
                )
                for k, v in aliases.items():
                    if k.lower().strip() == norm_name:
                        return v
        except (yaml.YAMLError, OSError, UnicodeDecodeError):
            pass

    results = retrieve_fn(name, limit=5)
    for r in results:
        if r.metadata.get("type") == "canon_character":
            eid = r.metadata.get("entity_id")
            if eid:
                return eid
    for r in results:
        eid = r.metadata.get("entity_id")
        if eid:
            return eid
    return None


class LocalEmbeddingBackend:
    """Zero-dependency local keyword & TF-IDF memory index backend."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._chunks: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text(encoding="utf-8"))
                self._chunks = data.get("chunks", [])
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                self._chunks = []

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_text(json.dumps({"chunks": self._chunks}, indent=2), encoding="utf-8")

    def build(self, book_folder: Path) -> None:
        scanned_chunks = scan_and_chunk_book(book_folder)
        self._chunks = [{"content": text, "metadata": meta} for text, meta in scanned_chunks]
        self._save()

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w{2,}\b", text.lower())

    def retrieve(self, query: str, limit: int = 10) -> list[Chunk]:
        if not self._chunks:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return [Chunk(c["content"], 0.0, c["metadata"]) for c in self._chunks[:limit]]

        doc_freqs: dict[str, int] = {}
        for c in self._chunks:
            for t in set(self._tokenize(c["content"])):
                doc_freqs[t] = doc_freqs.get(t, 0) + 1

        total_docs = len(self._chunks)
        results: list[Chunk] = []

        for c in self._chunks:
            doc_tokens = self._tokenize(c["content"])
            if not doc_tokens:
                continue
            score = 0.0
            for t in q_tokens:
                if t in doc_tokens:
                    tf = doc_tokens.count(t) / len(doc_tokens)
                    df = doc_freqs.get(t, 1)
                    idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
                    score += tf * idf
            if score > 0.0:
                results.append(Chunk(c["content"], score, c["metadata"]))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def resolve(self, book_folder: Path, name: str) -> str | None:
        return _resolve_alias(book_folder, name, self.retrieve)

    def learn(self, failed_session: str) -> list[Rule]:
        return query_llm_for_rules(failed_session) or generate_heuristic_rules(failed_session)

    def stats(self) -> MemoryStats:
        return MemoryStats(
            num_memories=len(self._chunks),
            backend_type="local",
            db_path=str(self.db_path)
        )

    def clear(self) -> None:
        self._chunks = []
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except OSError:
                pass


def _run_async(coro):
    """Run an async coroutine, handling nested event loops via nest_asyncio if needed."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    return asyncio.run(coro)


class HeadroomMemoryBackend:
    """Wrapper backend for the official Headroom memory system."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory = Memory(backend="local", db_path=str(db_path))

    def build(self, book_folder: Path) -> None:
        self.clear()
        scanned_chunks = scan_and_chunk_book(book_folder)

        async def index_all():
            for text, meta in scanned_chunks:
                await self._memory.save(
                    content=text,
                    user_id="bookforge",
                    importance=0.5,
                    metadata=meta
                )

        _run_async(index_all())

    def retrieve(self, query: str, limit: int = 10) -> list[Chunk]:
        async def do_search():
            return await self._memory.search(
                query=query,
                user_id="bookforge",
                top_k=limit,
                include_graph=False
            )

        try:
            results = _run_async(do_search())
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:
            import sys
            sys.stderr.write(f"Failed to retrieve memories: {e}\n")
            sys.stderr.flush()
            return []

        return [Chunk(content=r.content, score=r.score, metadata=r.metadata) for r in results]

    def resolve(self, book_folder: Path, name: str) -> str | None:
        return _resolve_alias(book_folder, name, self.retrieve)

    def learn(self, failed_session: str) -> list[Rule]:
        return query_llm_for_rules(failed_session) or generate_heuristic_rules(failed_session)

    def stats(self) -> MemoryStats:
        async def count_memories():
            await self._memory._ensure_initialized()
            if hasattr(self._memory._backend, "get_user_memories"):
                mems = await self._memory._backend.get_user_memories("bookforge", limit=9999)
                return len(mems)
            return 0

        try:
            count = _run_async(count_memories())
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:
            import sys
            sys.stderr.write(f"Failed to get memory stats: {e}\n")
            sys.stderr.flush()
            count = 0

        return MemoryStats(
            num_memories=count,
            backend_type="headroom",
            db_path=str(self.db_path)
        )

    def clear(self) -> None:
        async def do_clear():
            await self._memory.clear("bookforge")

        try:
            _run_async(do_clear())
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:
            import sys
            sys.stderr.write(f"Failed to clear memories: {e}\n")
            sys.stderr.flush()
