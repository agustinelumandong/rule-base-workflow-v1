"""Core research cache module for BookForge."""

from __future__ import annotations

import re
import yaml
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List


@dataclass
class ResearchCacheEntry:
    key: str
    category: str
    subject: str
    period: str
    question: str
    answer: str
    confidence: str = "medium"
    canon_status: str = "pending"  # accepted, pending, rejected, uncached
    source_backend: str = "manual"
    source_notebook_id: Optional[str] = None
    source_titles: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z")
    last_verified_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z")
    expires: str = "never"
    used_by: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ResearchCacheEntry:
        return cls(
            key=data["key"],
            category=data["category"],
            subject=data["subject"],
            period=data["period"],
            question=data["question"],
            answer=data["answer"],
            confidence=data.get("confidence", "medium"),
            canon_status=data.get("canon_status", "pending"),
            source_backend=data.get("source_backend", "manual"),
            source_notebook_id=data.get("source_notebook_id"),
            source_titles=data.get("source_titles", []),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"),
            last_verified_at=data.get("last_verified_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "") + "Z"),
            expires=data.get("expires", "never"),
            used_by=data.get("used_by", [])
        )


def normalize_research_key(question: str, category: str | None = None) -> str:
    """Generates a deterministic research cache key in category/question_slug format."""
    cat = (category or "general").strip().lower().replace(" ", "_")
    
    # Clean question text into a slug: lowercase, replace spaces/dashes with underscores, keep alphanumeric/underscores
    clean_q = question.lower()
    clean_q = re.sub(r"[^\w\s-]", "", clean_q)
    clean_q = re.sub(r"[\s-]+", "_", clean_q).strip("_")
    
    # Fallback to hash if empty
    if not clean_q:
        clean_q = hashlib.md5(question.encode("utf-8")).hexdigest()[:16]
        
    # Limit slug length to 64 chars
    if len(clean_q) > 64:
        clean_q = clean_q[:64].rstrip("_")
        
    return f"{cat}/{clean_q}"


def lookup_research_cache(book_folder: Path, key: str) -> ResearchCacheEntry | None:
    """Looks up a cache entry by key, returning the ResearchCacheEntry or None."""
    # Normalize key to handle truncated slugs or unnormalized formatting
    parts = key.split("/", 1)
    if len(parts) == 2:
        cat, slug = parts
        cat = cat.strip().lower().replace(" ", "_")
        # Clean slug similarly to normalize_research_key
        slug = slug.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s-]+", "_", slug).strip("_")
        if len(slug) > 64:
            slug = slug[:64].rstrip("_")
        key = f"{cat}/{slug}"

    cache_file = book_folder / "research_cache" / f"{key}.yml"
    if not cache_file.exists():
        cache_file = book_folder / "research_cache" / f"{key}.yaml"
        if not cache_file.exists():
            return None
            
    try:
        data = yaml.safe_load(cache_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return ResearchCacheEntry.from_dict(data)
    except Exception:
        pass
    return None


def write_research_cache_entry(book_folder: Path, entry: ResearchCacheEntry) -> Path:
    """Writes a ResearchCacheEntry as a YAML file to the cache directory."""
    cache_file = book_folder / "research_cache" / f"{entry.key}.yml"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(yaml.safe_dump(entry.to_dict(), sort_keys=False), encoding="utf-8")
    return cache_file


def _is_error_answer(answer: str) -> bool:
    """Check if an answer string represents an error rather than valid research."""
    return answer.strip().startswith("Error") and ":" in answer[:20]


# Maps requested category → keywords that should appear in matched section headers
_CATEGORY_HEADER_HINTS: dict[str, set[str]] = {
    "locations": {"location", "geography", "travel", "terrain", "region", "climate", "weather"},
    "weapons": {"weapon", "ammo", "firearm", "rifle", "pistol", "ammunition"},
    "clothing": {"clothing", "gear", "apparel", "attire", "garb"},
    "food": {"food", "provision", "ration", "foraging", "hunting"},
    "medicine": {"medicine", "medical", "health", "injury", "doctor"},
    "horses": {"horse", "equine", "livestock", "mount"},
}


def _passes_quality_gate(answer: str, category: str | None) -> bool:
    """Return True if answer is relevant enough to cache; False to skip caching.

    Rejects:
      - Empty answers
      - "No matching research items found."
      - Error answers
      - Category mismatch (requested category has no matching section headers)
    """
    stripped = answer.strip()
    if not stripped:
        return False
    if stripped == "No matching research items found.":
        return False
    if _is_error_answer(stripped):
        return False
    if not category:
        return True
    # Category mismatch: extract ## headers from answer, check relevance
    cat_key = category.strip().lower().replace(" ", "")
    headers = re.findall(r"^##\s+(.+)$", stripped, re.MULTILINE)
    if headers:
        acceptable = _CATEGORY_HEADER_HINTS.get(cat_key, set())
        if acceptable:
            header_text = " ".join(h.lower() for h in headers)
            if not any(kw in header_text for kw in acceptable):
                return False
    return True


def purge_error_entries(book_folder: Path) -> int:
    """Remove cache entries whose answers are error strings and aren't accepted. Returns count removed."""
    cache_dir = book_folder / "research_cache"
    if not cache_dir.exists():
        return 0
    removed = 0
    for yml_file in list(cache_dir.rglob("*.yml")) + list(cache_dir.rglob("*.yaml")):
        try:
            data = yaml.safe_load(yml_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            if data.get("canon_status") == "accepted":
                continue
            if _is_error_answer(str(data.get("answer", ""))):
                yml_file.unlink()
                removed += 1
        except Exception:
            pass
    return removed


def query_with_cache(
    book_folder: Path,
    question: str,
    backend,
    category: str | None = None,
    scene_key: str | None = None
) -> ResearchCacheEntry:
    """Coordinates lookup, miss execution against backend, scene-tracking, and caching."""
    key = normalize_research_key(question, category)
    entry = lookup_research_cache(book_folder, key)
    
    if entry:
        # Cache hit — but if the answer is an error string, purge and retry
        if _is_error_answer(entry.answer):
            cache_file = book_folder / "research_cache" / f"{entry.key}.yml"
            if not cache_file.exists():
                cache_file = book_folder / "research_cache" / f"{entry.key}.yaml"
            if cache_file.exists():
                cache_file.unlink()
            entry = None
        else:
            # Valid cache hit — record scene_key if needed
            if scene_key and scene_key not in entry.used_by:
                entry.used_by.append(scene_key)
                write_research_cache_entry(book_folder, entry)
            return entry
        
    # Cache miss - call raw_query on backend
    if hasattr(backend, "raw_query"):
        answer = backend.raw_query(question)
    else:
        answer = backend.query(question)
        
    # Do not cache error answers — return them directly without persisting
    if _is_error_answer(answer):
        # Build a temporary entry for return but don't write to cache
        words = [w for w in re.findall(r"\b\w+\b", question) if len(w) > 2]
        subject = " ".join(words[:4]) if words else "general"
        return ResearchCacheEntry(
            key=key,
            category=category or key.split("/")[0],
            subject=subject,
            period="18th century",
            question=question,
            answer=answer,
            confidence="low",
            canon_status="rejected",
            source_backend="manual",
            source_notebook_id=None,
            source_titles=[],
            used_by=[scene_key] if scene_key else []
        )

    # Quality gate — skip caching for irrelevant/empty/no-match answers
    if not _passes_quality_gate(answer, category):
        words = [w for w in re.findall(r"\b\w+\b", question) if len(w) > 2]
        subject = " ".join(words[:4]) if words else "general"
        return ResearchCacheEntry(
            key=key,
            category=category or key.split("/")[0],
            subject=subject,
            period="18th century",
            question=question,
            answer=answer,
            confidence="low",
            canon_status="uncached",
            source_backend="manual",
            source_notebook_id=None,
            source_titles=[],
            used_by=[scene_key] if scene_key else []
        )
        
    # Extract source backend details
    backend_name = backend.__class__.__name__.lower()
    if "notebooklm" in backend_name:
        source_backend = "notebooklm"
        # Access associated notebook ID if available
        try:
            notebook_id = backend._get_notebook_id()
        except AttributeError:
            notebook_id = None
    else:
        source_backend = "manual"
        notebook_id = None
        
    # Determine default subject
    words = [w for w in re.findall(r"\b\w+\b", question) if len(w) > 2]
    subject = " ".join(words[:4]) if words else "general"
    
    entry = ResearchCacheEntry(
        key=key,
        category=category or key.split("/")[0],
        subject=subject,
        period="18th century",
        question=question,
        answer=answer,
        confidence="medium",
        canon_status="pending",
        source_backend=source_backend,
        source_notebook_id=notebook_id,
        source_titles=[],
        used_by=[scene_key] if scene_key else []
    )
    
    write_research_cache_entry(book_folder, entry)
    return entry


def mark_research_accepted(book_folder: Path, key: str) -> None:
    """Accepts a cached research entry by setting canon_status to 'accepted'."""
    entry = lookup_research_cache(book_folder, key)
    if not entry:
        raise FileNotFoundError(f"Research entry with key '{key}' not found in cache.")
    entry.canon_status = "accepted"
    write_research_cache_entry(book_folder, entry)


def is_entry_relevant(entry: ResearchCacheEntry, scene_key: str, research_questions: list[str]) -> bool:
    """Determines if a research cache entry is relevant to a specific scene."""
    if scene_key in entry.used_by:
        return True
        
    for rq in research_questions:
        rq_clean = rq.strip().lower()
        if rq_clean in entry.question.lower() or entry.question.lower() in rq_clean:
            return True
        # Match normalized key
        normalized_rq_key = normalize_research_key(rq, entry.category)
        if normalized_rq_key == entry.key:
            return True
            
    return False


def get_accepted_research_for_scene(
    book_folder: Path,
    scene_key: str,
    research_questions: list[str]
) -> list[ResearchCacheEntry]:
    """Retrieves all accepted cache entries relevant to the scene."""
    cache_dir = book_folder / "research_cache"
    if not cache_dir.exists():
        return []
        
    relevant = []
    
    # Scan for yml files
    for yml_file in cache_dir.rglob("*.yml"):
        try:
            data = yaml.safe_load(yml_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            entry = ResearchCacheEntry.from_dict(data)
            if entry.canon_status != "accepted":
                continue
            if is_entry_relevant(entry, scene_key, research_questions):
                relevant.append(entry)
        except Exception:
            pass
            
    # Scan for yaml files
    for yaml_file in cache_dir.rglob("*.yaml"):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            entry = ResearchCacheEntry.from_dict(data)
            if entry.canon_status != "accepted":
                continue
            if is_entry_relevant(entry, scene_key, research_questions):
                if entry.key not in [e.key for e in relevant]:
                    relevant.append(entry)
        except Exception:
            pass
            
    return relevant
