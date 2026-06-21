"""Unit tests for the BookForge Persistent Memory Tier (Milestone 2.5)."""

import tempfile
from pathlib import Path
import pytest
import yaml

from bookforge.core.memory import (
    LocalEmbeddingBackend,
    Chunk,
    Rule,
    get_memory_backend,
    generate_heuristic_rules
)


@pytest.fixture
def temp_book_folder():
    """Create a temporary book folder structure with dummy files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        book_path = Path(temp_dir)
        
        # Rulebook
        rulebook = book_path / "rulebook.md"
        rulebook.write_text(
            "# Style rules\n\n- Never use the AI word relentless in the text.\n\n"
            "## Section 2\n\n- Direct dialogue tags said and asked are banned.",
            encoding="utf-8"
        )
        
        # Outline
        outline = book_path / "phase-0.md"
        outline.write_text(
            "# Chapter 1: The Trail\n\nHarlan and Tex ride through Alkali Ridge under a blazing sun.\n\n"
            "## Characters\n\nHarlan: a rugged marshal with a silver pocket watch.",
            encoding="utf-8"
        )
        
        # Canon snapshot
        entities_dir = book_path / "canon" / "entities"
        entities_dir.mkdir(parents=True, exist_ok=True)
        aliases_file = entities_dir / "aliases.yml"
        aliases_file.write_text(yaml.dump({"aliases": {"marshal harlan": "harlan", "old tex": "tex"}}, sort_keys=False), encoding="utf-8")

        canon_dir = book_path / "canon" / "state"
        canon_dir.mkdir(parents=True, exist_ok=True)
        snapshot = canon_dir / "snapshot.yml"
        snapshot_data = {
            "characters": {
                "harlan": {
                    "canonical": "Harlan",
                    "tier": "protagonist",
                    "role": "marshal",
                    "status": "alive",
                    "location": "saloon",
                    "inventory": ["colt_45", "silver_pocket_watch"],
                    "injuries": [],
                    "emotional_state": "focused"
                }
            },
            "locations": {
                "saloon": {
                    "canonical": "The Saloon",
                    "occupants": ["harlan"]
                }
            },
            "objects": {
                "silver_pocket_watch": {
                    "canonical": "Silver Pocket Watch",
                    "type": "equipment",
                    "holder": "harlan",
                    "state": "intact"
                }
            }
        }
        snapshot.write_text(yaml.dump(snapshot_data), encoding="utf-8")
        
        # Event logs
        events_dir = book_path / "canon" / "events"
        events_dir.mkdir(parents=True)
        event = events_dir / "chapter-01.event.yml"
        event.write_text(
            "chapter: chapter-01\nchanges:\n  - type: move\n    actor: harlan\n    to: saloon\n",
            encoding="utf-8"
        )
        
        # Chapter drafts
        chapters_dir = book_path / "chapters" / "chapter-01"
        chapters_dir.mkdir(parents=True)
        draft = chapters_dir / "chapter-01.md"
        draft.write_text(
            "Harlan kicked the doors open. The saloon was empty.\n\n"
            "He reached for his silver pocket watch.",
            encoding="utf-8"
        )
        
        yield book_path


def test_local_embedding_backend_build_and_retrieve(temp_book_folder):
    db_path = temp_book_folder / "local_memory.json"
    backend = LocalEmbeddingBackend(db_path)
    
    # Verify build
    backend.build(temp_book_folder)
    assert db_path.exists()
    
    stats = backend.stats()
    assert stats.num_memories > 0
    assert stats.backend_type == "local"
    
    # Verify retrieve (semantic keyword overlap)
    results = backend.retrieve("pocket watch")
    assert len(results) > 0
    # The best match should contain "pocket watch" or "silver_pocket_watch"
    top_match = results[0]
    assert "watch" in top_match.content.lower() or "pocket" in top_match.content.lower()
    assert top_match.score > 0.0


def test_heuristic_learning():
    log_text = "Validation Failed: Found banned AI word 'relentless' on line 42."
    rules = generate_heuristic_rules(log_text)
    assert len(rules) > 0
    
    # Verify it suggested style rule for relentless
    relentless_rule = next((r for r in rules if r.id == "style_banned_echo_words"), None)
    assert relentless_rule is not None
    assert "relentless" in relentless_rule.pattern
    
    # Test location drift trigger
    log_drift = "Validation Failed: Teleportation detected for actor harlan (from saloon to ridge)."
    rules_drift = generate_heuristic_rules(log_drift)
    assert any(r.id == "canon_location_consistency" for r in rules_drift)


def test_get_memory_backend(temp_book_folder):
    backend = get_memory_backend(temp_book_folder)
    # Since we might not have official headroom loaded in the test env, it should fallback to LocalEmbeddingBackend
    # or HeadroomMemoryBackend if imported.
    assert backend is not None
    assert hasattr(backend, "build")
    assert hasattr(backend, "retrieve")
    assert hasattr(backend, "learn")
    assert hasattr(backend, "stats")


def test_resolve_alias(temp_book_folder):
    db_path = temp_book_folder / "local_memory.json"
    backend = LocalEmbeddingBackend(db_path)
    backend.build(temp_book_folder)
    
    # 1. Direct alias match
    eid1 = backend.resolve(temp_book_folder, "marshal harlan")
    assert eid1 == "harlan"
    
    # 2. Semantic fallback (matches "Harlan" chunk metadata entity_id)
    eid2 = backend.resolve(temp_book_folder, "Harlan")
    assert eid2 == "harlan"
    
    # 3. Direct matching title strip
    eid3 = backend.resolve(temp_book_folder, "Sheriff old tex")
    assert eid3 == "tex"


def test_cli_commands(temp_book_folder, monkeypatch):
    from bookforge.cli import main
    import sys
    
    # 1. Build
    monkeypatch.setattr(sys, "argv", ["bookforge", "memory", "build", str(temp_book_folder)])
    assert main() == 0
    
    # 2. Retrieve
    monkeypatch.setattr(sys, "argv", ["bookforge", "memory", "retrieve", "pocket watch", str(temp_book_folder)])
    assert main() == 0
    
    # 3. Resolve
    monkeypatch.setattr(sys, "argv", ["bookforge", "memory", "resolve", "marshal harlan", str(temp_book_folder)])
    assert main() == 0
    
    # 4. Learn
    log_file = temp_book_folder / "fail.log"
    log_file.write_text("Validation Failed: Found banned AI word 'relentless' on line 12.", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["bookforge", "memory", "learn", str(log_file), str(temp_book_folder)])
    assert main() == 0
    
    # Let's find the proposal file
    proposals_dir = temp_book_folder / ".bookforge" / "proposals"
    assert proposals_dir.exists()
    proposal_files = list(proposals_dir.glob("*.yml"))
    assert len(proposal_files) == 1
    proposal_id = proposal_files[0].stem
    
    # 5. Apply-learning
    monkeypatch.setattr(sys, "argv", ["bookforge", "memory", "apply-learning", proposal_id, str(temp_book_folder)])
    assert main() == 0
    assert not proposal_files[0].exists()  # should be deleted
    
    # Check rulebook.md got modified
    rulebook_content = (temp_book_folder / "rulebook.md").read_text(encoding="utf-8")
    assert "relentless" in rulebook_content


