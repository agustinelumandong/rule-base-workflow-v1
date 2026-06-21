"""BookForge Persistent Memory Tier (Layer 3) Core Module.

Provides memory backend protocol, local fallback indexing, and official headroom integration.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, List, Dict, Any, Tuple

# Try to import official headroom if installed
try:
    import headroom
    from headroom.memory.easy import Memory
    HAS_OFFICIAL_HEADROOM = True
except ImportError:
    HAS_OFFICIAL_HEADROOM = False


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


# ---------------------------------------------------------------------------
# Chunker helper: splits files into clean textual paragraphs or blocks
# ---------------------------------------------------------------------------

def scan_and_chunk_book(book_folder: Path) -> list[tuple[str, dict[str, Any]]]:
    """Scan book files and partition them into metadata-tagged chunks."""
    chunks: list[tuple[str, dict[str, Any]]] = []

    # 1. Rulebook
    rulebook_path = book_folder / "rulebook.md"
    if rulebook_path.exists():
        text = rulebook_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": "rulebook.md",
                    "type": "rulebook",
                    "chunk_index": idx
                }))

    # 2. Mood Lock
    mood_lock_path = book_folder / "mood-lock.md"
    if mood_lock_path.exists():
        text = mood_lock_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": "mood-lock.md",
                    "type": "mood_lock",
                    "chunk_index": idx
                }))

    # 3. Phase Outlines
    # Look for outline path in book_folder or phase-0/
    from bookforge.core.scanner import source_path
    outline_path = source_path(book_folder)
    if outline_path and outline_path.exists():
        text = outline_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": outline_path.name,
                    "type": "outline",
                    "chunk_index": idx
                }))

    # 4. Chapter Summaries
    summaries_path = book_folder / "chapter-summaries.md"
    if summaries_path.exists():
        text = summaries_path.read_text(encoding="utf-8")
        for idx, paragraph in enumerate(text.split("\n\n")):
            para = paragraph.strip()
            if para:
                chunks.append((para, {
                    "source": "chapter-summaries.md",
                    "type": "chapter_summaries",
                    "chunk_index": idx
                }))

    # 5. Canon Snapshot
    snapshot_path = book_folder / "canon" / "state" / "snapshot.yml"
    if snapshot_path.exists():
        # Represent entities textually for retrieval
        import yaml
        try:
            snapshot_data = yaml.safe_load(snapshot_path.read_text(encoding="utf-8"))
            if isinstance(snapshot_data, dict):
                # Characters
                for char_id, char_info in snapshot_data.get("characters", {}).items():
                    info_str = f"Character '{char_id}' ({char_info.get('canonical', char_id)}): " \
                               f"tier={char_info.get('tier')}, role={char_info.get('role')}, " \
                               f"status={char_info.get('status')}, location={char_info.get('location')}, " \
                               f"inventory={char_info.get('inventory')}, injuries={char_info.get('injuries')}, " \
                               f"emotional_state={char_info.get('emotional_state')}."
                    chunks.append((info_str, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_character",
                        "entity_id": char_id
                    }))
                # Locations
                for loc_id, loc_info in snapshot_data.get("locations", {}).items():
                    info_str = f"Location '{loc_id}' ({loc_info.get('canonical', loc_id)}): " \
                               f"occupants={loc_info.get('occupants')}."
                    chunks.append((info_str, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_location",
                        "entity_id": loc_id
                    }))
                # Objects
                for obj_id, obj_info in snapshot_data.get("objects", {}).items():
                    info_str = f"Object '{obj_id}' ({obj_info.get('canonical', obj_id)}): " \
                               f"type={obj_info.get('type')}, holder={obj_info.get('holder')}, " \
                               f"state={obj_info.get('state')}."
                    chunks.append((info_str, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_object",
                        "entity_id": obj_id
                    }))
        except Exception:
            # Fallback to indexing snapshot as raw text chunks if parsing fails
            text = snapshot_path.read_text(encoding="utf-8")
            for idx, paragraph in enumerate(text.split("\n\n")):
                para = paragraph.strip()
                if para:
                    chunks.append((para, {
                        "source": "canon/state/snapshot.yml",
                        "type": "canon_snapshot_raw",
                        "chunk_index": idx
                    }))

    # 6. Chapter events
    events_dir = book_folder / "canon" / "events"
    if events_dir.is_dir():
        for event_file in sorted(events_dir.glob("*.event.yml")):
            text = event_file.read_text(encoding="utf-8")
            chunks.append((f"Event Log {event_file.name}:\n{text}", {
                "source": f"canon/events/{event_file.name}",
                "type": "canon_event",
                "chapter": event_file.stem
            }))

    # 7. Chapter drafts
    chapters_dir = book_folder / "chapters"
    if chapters_dir.is_dir():
        for draft_file in sorted(chapters_dir.glob("chapter-*/chapter-*.md")):
            text = draft_file.read_text(encoding="utf-8")
            # Extract chapter folder/slug
            chapter_slug = draft_file.parent.name
            for idx, paragraph in enumerate(text.split("\n\n")):
                para = paragraph.strip()
                if para:
                    chunks.append((para, {
                        "source": f"chapters/{chapter_slug}/{draft_file.name}",
                        "type": "chapter_draft",
                        "chapter": chapter_slug,
                        "chunk_index": idx
                    }))
        # Epilogue
        epilogue_file = chapters_dir / "epilogue" / "epilogue.md"
        if epilogue_file.exists():
            text = epilogue_file.read_text(encoding="utf-8")
            for idx, paragraph in enumerate(text.split("\n\n")):
                para = paragraph.strip()
                if para:
                    chunks.append((para, {
                        "source": "chapters/epilogue/epilogue.md",
                        "type": "epilogue_draft",
                        "chunk_index": idx
                    }))

    return chunks


# ---------------------------------------------------------------------------
# Heuristic Fallback Rule Generator
# ---------------------------------------------------------------------------

def generate_heuristic_rules(failed_session: str) -> list[Rule]:
    """Inspect failed session logs for standard violations and propose changes."""
    rules = []
    
    # 1. AI-isms or banned words
    # Check if failed session lists specific style errors
    from bookforge.core.loop import STYLE_TERMS
    matched_style_words = []
    for term in STYLE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", failed_session, re.IGNORECASE):
            matched_style_words.append(term)
            
    if matched_style_words:
        word_list_str = ", ".join(f"'{w}'" for w in matched_style_words)
        rules.append(Rule(
            id="style_banned_echo_words",
            pattern=f"\\b({'|'.join(re.escape(w) for w in matched_style_words)})\\b",
            replacement="",
            reason=f"Detected banned AI echo word(s): {word_list_str}",
            file="rulebook.md",
            change=f"\n- Avoid using AI echo words: {word_list_str}."
        ))

    # 2. Dialogue tags
    if "dialogue tag" in failed_session.lower() or "said" in failed_session.lower() or "asked" in failed_session.lower():
        rules.append(Rule(
            id="style_no_dialogue_tags",
            pattern=r'\b(said|asked|shouted|replied)\b',
            replacement="",
            reason="Dialogue tags are discouraged when em dash action anchors are active.",
            file="rulebook.md",
            change="\n- Do not use dialogue tags like 'said' or 'asked' when using action anchors."
        ))

    # 3. Teleportation / location drift
    if "teleport" in failed_session.lower() or "location" in failed_session.lower() or "drift" in failed_session.lower():
        rules.append(Rule(
            id="canon_location_consistency",
            pattern="",
            replacement="",
            reason="Character location drift/teleportation detected in validation.",
            file="rulebook.md",
            change="\n- Characters must travel step-by-step. Verify character locations in the snapshot before drafting."
        ))

    # 4. Inventory errors
    if "inventory" in failed_session.lower() or "weapon" in failed_session.lower() or "object" in failed_session.lower():
        rules.append(Rule(
            id="canon_inventory_consistency",
            pattern="",
            replacement="",
            reason="Character using items not registered in their active inventory.",
            file="rulebook.md",
            change="\n- Characters can only use weapons or objects in their active inventory snapshot."
        ))

    # 5. Dead character acting
    if "dead" in failed_session.lower() or "status" in failed_session.lower():
        rules.append(Rule(
            id="canon_status_consistency",
            pattern="",
            replacement="",
            reason="A character marked as dead was found performing actions or speaking in the draft.",
            file="rulebook.md",
            change="\n- Dead characters cannot act or speak. Verify character status in the snapshot."
        ))

    # Default fallback if nothing matches
    if not rules:
        rules.append(Rule(
            id="general_style_lock_enforcement",
            pattern="",
            replacement="",
            reason="General drafting validation failure detected in the session.",
            file="rulebook.md",
            change="\n- Strictly enforce behavior-driven, literal Western prose styles."
        ))

    return rules


# ---------------------------------------------------------------------------
# LLM Integration for learn method
# ---------------------------------------------------------------------------

def query_llm_for_rules(failed_session: str) -> list[Rule] | None:
    """Call external LLM APIs (OpenAI/Anthropic/Gemini) if configured."""
    # Find active API keys
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not (openai_key or anthropic_key or gemini_key):
        return None

    prompt = (
        "You are an expert Western fiction editor and writing pipeline validator. "
        "Analyze the following validation/compilation failure log from a writing session:\n\n"
        f"--- FAILURE LOG ---\n{failed_session}\n-------------------\n\n"
        "Generate 1 to 3 style or guardrail rules to add to rulebook.md or AGENTS.md to prevent this issue. "
        "Each rule must have a unique ID, clear reason, and exact file changes. "
        "Format the output strictly as a JSON object matching this schema:\n"
        "{\n"
        '  "rules": [\n'
        '    {\n'
        '      "id": "rule_id",\n'
        '      "pattern": "regex_pattern_or_empty",\n'
        '      "replacement": "replacement_prose_or_empty",\n'
        '      "reason": "why this rule was added",\n'
        '      "file": "rulebook.md",\n'
        '      "change": "exact text to append/insert"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    try:
        if anthropic_key:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            data = json.dumps({
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}]
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                text = res_body["content"][0]["text"]
                
        elif openai_key:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "content-type": "application/json"
            }
            data = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                text = res_body["choices"][0]["message"]["content"]
                
        else: # gemini_key
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            headers = {"content-type": "application/json"}
            data = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                text = res_body["candidates"][0]["content"]["parts"][0]["text"]

        # Parse JSON
        # Locate JSON content block if not returned as pure JSON
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            rules = []
            for r in parsed.get("rules", []):
                rules.append(Rule(
                    id=r["id"],
                    pattern=r.get("pattern", ""),
                    replacement=r.get("replacement", ""),
                    reason=r["reason"],
                    file=r["file"],
                    change=r["change"]
                ))
            return rules
    except Exception:
        pass # Fall back to heuristics if API call fails
    return None


# ---------------------------------------------------------------------------
# Zero-Dependency Local TF-IDF / BM25 Backend
# ---------------------------------------------------------------------------

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
            except Exception:
                self._chunks = []

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_text(json.dumps({"chunks": self._chunks}, indent=2), encoding="utf-8")

    def build(self, book_folder: Path) -> None:
        scanned_chunks = scan_and_chunk_book(book_folder)
        self._chunks = []
        for text, meta in scanned_chunks:
            self._chunks.append({
                "content": text,
                "metadata": meta
            })
        self._save()

    def _tokenize(self, text: str) -> list[str]:
        # Simple word tokenization (lowercase, alphanumeric)
        return re.findall(r"\b\w{2,}\b", text.lower())

    def retrieve(self, query: str, limit: int = 10) -> list[Chunk]:
        if not self._chunks:
            return []

        # Tokenize query
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return [Chunk(c["content"], 0.0, c["metadata"]) for c in self._chunks[:limit]]

        # Compute document frequencies and word counts
        doc_freqs: dict[str, int] = {}
        for c in self._chunks:
            tokens_in_doc = set(self._tokenize(c["content"]))
            for t in tokens_in_doc:
                doc_freqs[t] = doc_freqs.get(t, 0) + 1

        total_docs = len(self._chunks)
        results: list[Chunk] = []

        for c in self._chunks:
            content = c["content"]
            doc_tokens = self._tokenize(content)
            if not doc_tokens:
                continue

            # Compute simple TF-IDF score
            score = 0.0
            for t in q_tokens:
                if t in doc_tokens:
                    tf = doc_tokens.count(t) / len(doc_tokens)
                    df = doc_freqs.get(t, 1)
                    # Smooth IDF
                    idf = math.log(1.0 + (total_docs - df + 0.5) / (df + 0.5))
                    score += tf * idf

            if score > 0.0:
                results.append(Chunk(content, score, c["metadata"]))

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def resolve(self, book_folder: Path, name: str) -> str | None:
        # 1. Load aliases.yml
        aliases_file = book_folder / "canon" / "entities" / "aliases.yml"
        if aliases_file.exists():
            import yaml
            try:
                aliases_data = yaml.safe_load(aliases_file.read_text(encoding="utf-8"))
                if isinstance(aliases_data, dict):
                    aliases = aliases_data.get("aliases", {})
                    norm_name = name.lower().strip()
                    # Strip titles
                    norm_name = re.sub(r"^(marshal|sheriff|deputy|mr\.|mrs\.|miss|doctor|doc)\s+", "", norm_name)
                    for k, v in aliases.items():
                        if k.lower().strip() == norm_name:
                            return v
            except Exception:
                pass

        # 2. Fall back to semantic retrieval
        results = self.retrieve(name, limit=5)
        # Prioritize canon_character matches first
        for r in results:
            if r.metadata.get("type") == "canon_character":
                eid = r.metadata.get("entity_id")
                if eid:
                    return eid
        # Then check any other entity ID
        for r in results:
            eid = r.metadata.get("entity_id")
            if eid:
                return eid
        return None

    def learn(self, failed_session: str) -> list[Rule]:
        # Try LLM first, fallback to heuristics
        rules = query_llm_for_rules(failed_session)
        if rules is None:
            rules = generate_heuristic_rules(failed_session)
        return rules

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
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Headroom-SDK Wrapped Backend
# ---------------------------------------------------------------------------

class HeadroomMemoryBackend:
    """Wrapper backend for the official Headroom memory system."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        # Ensure parent directory exists so sqlite can open it
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # Instantiate headroom memory
        self._memory = Memory(backend="local", db_path=str(db_path))

    def build(self, book_folder: Path) -> None:
        # Clear existing memories to avoid duplicate index
        self.clear()
        scanned_chunks = scan_and_chunk_book(book_folder)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # If running inside an existing loop, execute via task/future
            async def index_all():
                for text, meta in scanned_chunks:
                    await self._memory.save(
                        content=text,
                        user_id="bookforge",
                        importance=0.5,
                        metadata=meta
                    )
            # Create thread-safe call
            import nest_asyncio
            nest_asyncio.apply()
            loop.run_until_complete(index_all())
        else:
            async def index_all():
                for text, meta in scanned_chunks:
                    await self._memory.save(
                        content=text,
                        user_id="bookforge",
                        importance=0.5,
                        metadata=meta
                    )
            asyncio.run(index_all())

    def retrieve(self, query: str, limit: int = 10) -> list[Chunk]:
        async def do_search():
            return await self._memory.search(
                query=query,
                user_id="bookforge",
                top_k=limit,
                include_graph=False
            )
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                results = loop.run_until_complete(do_search())
            else:
                results = asyncio.run(do_search())
        except Exception:
            return []

        return [Chunk(content=r.content, score=r.score, metadata=r.metadata) for r in results]

    def resolve(self, book_folder: Path, name: str) -> str | None:
        # 1. Load aliases.yml
        aliases_file = book_folder / "canon" / "entities" / "aliases.yml"
        if aliases_file.exists():
            import yaml
            try:
                aliases_data = yaml.safe_load(aliases_file.read_text(encoding="utf-8"))
                if isinstance(aliases_data, dict):
                    aliases = aliases_data.get("aliases", {})
                    norm_name = name.lower().strip()
                    # Strip titles
                    norm_name = re.sub(r"^(marshal|sheriff|deputy|mr\.|mrs\.|miss|doctor|doc)\s+", "", norm_name)
                    for k, v in aliases.items():
                        if k.lower().strip() == norm_name:
                            return v
            except Exception:
                pass

        # 2. Fall back to semantic retrieval
        results = self.retrieve(name, limit=5)
        # Prioritize canon_character matches first
        for r in results:
            if r.metadata.get("type") == "canon_character":
                eid = r.metadata.get("entity_id")
                if eid:
                    return eid
        # Then check any other entity ID
        for r in results:
            eid = r.metadata.get("entity_id")
            if eid:
                return eid
        return None

    def learn(self, failed_session: str) -> list[Rule]:
        # Try LLM first, fallback to heuristics
        rules = query_llm_for_rules(failed_session)
        if rules is None:
            rules = generate_heuristic_rules(failed_session)
        return rules

    def stats(self) -> MemoryStats:
        async def count_memories():
            await self._memory._ensure_initialized()
            if hasattr(self._memory._backend, "get_user_memories"):
                mems = await self._memory._backend.get_user_memories("bookforge", limit=9999)
                return len(mems)
            return 0
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                count = loop.run_until_complete(count_memories())
            else:
                count = asyncio.run(count_memories())
        except Exception:
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
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(do_clear())
            else:
                asyncio.run(do_clear())
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------

def get_memory_backend(book_folder: Path) -> MemoryBackend:
    """Resolve and instantiate the configured/active memory backend."""
    # Check if official headroom is disabled or not installed
    # By default, use headroom if installed. Fallback to local.
    if HAS_OFFICIAL_HEADROOM:
        db_path = book_folder / ".bookforge" / "memory.db"
        return HeadroomMemoryBackend(db_path)
    else:
        db_path = book_folder / ".bookforge" / "local_memory.json"
        return LocalEmbeddingBackend(db_path)


def apply_proposal_rules(book_folder: Path, proposal_id: str) -> list[str]:
    """Read proposal by UUID, apply rules to target files, and delete proposal."""
    proposal_path = book_folder / ".bookforge" / "proposals" / f"{proposal_id}.yml"
    if not proposal_path.exists():
        raise FileNotFoundError(f"Proposal {proposal_id} not found at {proposal_path}")
        
    import yaml
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
        
        # Resolve target file path
        # 1. Check relative to book folder
        target_path = book_folder / rule.file
        # 2. Check relative to current working directory (workspace root)
        if not target_path.exists():
            target_path = Path(rule.file)
        # 3. Check relative to book_folder's parent (e.g. books/../AGENTS.md)
        if not target_path.exists():
            target_path = book_folder.parent.parent / rule.file
            
        # Read content
        if target_path.exists():
            content = target_path.read_text(encoding="utf-8")
        else:
            content = ""
            
        # Apply change
        if content:
            # Let's try to insert nicely into markdown if target is rulebook.md or AGENTS.md
            if target_path.suffix.lower() == ".md":
                # Find if there is a header like '## Style Rules' or '## Guardrails' or '## Banned Words'
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
                # Non-markdown or YAML file: just append
                content = content.rstrip() + f"\n{rule.change.strip()}\n"
        else:
            # File doesn't exist, create it with the change
            content = f"# {rule.file}\n\n{rule.change.strip()}\n"
            
        # Save content
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        modified_files.append(str(target_path))
        
    # Delete the proposal file
    proposal_path.unlink()
    return modified_files


# ---------------------------------------------------------------------------
# Model Context Protocol stdio/http tools server
# ---------------------------------------------------------------------------

class MemoryMCPServer:
    """Model Context Protocol server exposing memory backend as tools."""

    def __init__(self, backend: MemoryBackend) -> None:
        self.backend = backend

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "headroom_retrieve",
                "description": "Semantic search across persistent book memory chunks (canon, outline, rules, drafts).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Query string to search for."},
                        "limit": {"type": "integer", "description": "Max results to return.", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "headroom_stats",
                "description": "Return database statistics and count of stored memory chunks.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "headroom_retrieve":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            chunks = self.backend.retrieve(query, limit=limit)
            if not chunks:
                return {"content": [{"type": "text", "text": "No matching memories found."}]}
            
            lines = []
            for i, c in enumerate(chunks, start=1):
                src = c.metadata.get("source", "unknown")
                lines.append(f"{i}. [score={c.score:.3f}] [src={src}] {c.content}")
            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        elif name == "headroom_stats":
            st = self.backend.stats()
            stats_str = f"Backend: {st.backend_type}\nDatabase Path: {st.db_path}\nIndexed Chunks: {st.num_memories}"
            return {"content": [{"type": "text", "text": stats_str}]}

        return {"error": f"Unknown tool: {name}"}

    def run_stdio(self) -> None:
        """Run the MCP server over standard input/output using JSON-RPC 2.0."""
        import sys
        
        # Read from stdin, parse JSON-RPC, write to stdout
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                method = req.get("method")
                req_id = req.get("id")
                
                if method == "initialize":
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "bookforge-memory",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "tools": self.list_tools()
                        }
                    }
                elif method == "tools/call":
                    params = req.get("params", {})
                    tool_name = params.get("name")
                    tool_args = params.get("arguments", {})
                    tool_res = self.call_tool(tool_name, tool_args)
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": tool_res
                    }
                else:
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            except Exception as e:
                # Output standard JSON-RPC parse error
                sys.stderr.write(f"MCP Stdio Error: {e}\n")
                sys.stderr.flush()

    def run_http(self, port: int = 8000) -> None:
        """Run a simple, zero-dependency HTTP server for JSON-RPC MCP calls."""
        from http.server import BaseHTTPRequestHandler, HTTPServer
        
        server_self = self
        
        class MCPHTTPHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                try:
                    req = json.loads(body.decode("utf-8"))
                    method = req.get("method")
                    req_id = req.get("id")
                    
                    if method == "tools/list":
                        result = {"tools": server_self.list_tools()}
                    elif method == "tools/call":
                        params = req.get("params", {})
                        tool_name = params.get("name")
                        tool_args = params.get("arguments", {})
                        result = server_self.call_tool(tool_name, tool_args)
                    else:
                        result = {"error": f"Method not supported over HTTP: {method}"}
                        
                    res = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": result
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(res).encode('utf-8'))
                except Exception as e:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(str(e).encode('utf-8'))
                    
        httpd = HTTPServer(('localhost', port), MCPHTTPHandler)
        print(f"Memory MCP HTTP Server listening on http://localhost:{port}")
        httpd.serve_forever()
