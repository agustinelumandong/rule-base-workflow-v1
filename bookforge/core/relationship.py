#!/usr/bin/env python3
"""BookForge Typed Relationships and Graph Memory Core."""

from __future__ import annotations

import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Relationship:
    subject: str
    relation: str
    object: str
    source_artifact: str = "manual"
    canon_status: str = "approved"
    valid_from: str | None = None
    valid_until: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def load_relationships(book_folder: Path) -> list[dict]:
    """Loads typed relationships from relationships.json."""
    rel_file = book_folder / "relationships.json"
    if not rel_file.exists():
        return []
    try:
        with open(rel_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_relationships(book_folder: Path, relationships: list[dict]):
    """Saves typed relationships to relationships.json."""
    rel_file = book_folder / "relationships.json"
    with open(rel_file, "w", encoding="utf-8") as f:
        json.dump(relationships, f, indent=2)


def add_relationship(
    book_folder: Path,
    subject: str,
    relation: str,
    obj: str,
    source_artifact: str = "manual",
    valid_from: str | None = None
) -> dict:
    """Adds a new typed relationship and saves it."""
    relationships = load_relationships(book_folder)
    
    # Remove existing relationship if it's a duplicate subject-relation-object
    relationships = [
        r for r in relationships
        if not (r["subject"].lower() == subject.lower() and
                r["relation"].lower() == relation.lower() and
                r["object"].lower() == obj.lower())
    ]
    
    new_rel = Relationship(
        subject=subject.lower(),
        relation=relation.lower(),
        object=obj.lower(),
        source_artifact=source_artifact,
        valid_from=valid_from
    ).to_dict()
    
    relationships.append(new_rel)
    save_relationships(book_folder, relationships)
    return new_rel


def validate_relationships_prose(
    scene: dict,
    scene_draft: str,
    relationships: list[dict]
) -> tuple[list[str], list[str]]:
    """Validates scene prose against active character relationships.
    
    Returns (failures, warnings).
    """
    failures = []
    warnings = []
    
    # Identify active characters in this scene
    active_chars = set()
    loc_block = scene.get("character_locations", "")
    if loc_block:
        for pair in loc_block.split(","):
            if ":" in pair:
                active_chars.add(pair.split(":")[0].strip().lower())

    # 1. Conflict / Distrust Rule Validation
    # If A conflict/distrusts/enemy_of B, and they are both active in the scene,
    # the prose must not show them behaving in a friendly or intimate manner.
    friendly_terms = [
        "friend", "partner", "buddy", "darling", "sweetheart", "honey", 
        "hugged", "shared a smile", "laughed together", "embraced"
    ]
    
    conflict_relations = {"conflict", "distrusts", "enemy_of"}
    
    for rel in relationships:
        sub = rel["subject"].lower()
        obj = rel["object"].lower()
        rel_type = rel["relation"].lower()
        
        if rel_type in conflict_relations and sub in active_chars and obj in active_chars:
            # Check if prose shows friendly behavior between sub and obj
            # Find paragraphs containing both names or references
            paragraphs = scene_draft.split("\n\n")
            for para_num, para in enumerate(paragraphs, 1):
                # Check if paragraph mentions both characters
                if re.search(rf"\b{re.escape(sub)}\b", para, re.I) and re.search(rf"\b{re.escape(obj)}\b", para, re.I):
                    # Check for friendly terms in this paragraph
                    for term in friendly_terms:
                        if re.search(rf"\b{re.escape(term)}\b", para, re.I):
                            failures.append(
                                f"Relationship Conflict Failure: {sub.capitalize()} and {obj.capitalize()} are in a '{rel_type}' relationship but paragraph {para_num} depicts friendly behavior via '{term}': '{para[:50]}...'"
                            )

    # 2. Knowledge Boundary Rule Validation
    # If A hides_from B or A has a secret/item B does_not_know (e.g. A hides_from B, or item:secret does_not_know B)
    # E.g. A relationship: subject=secret_name, relation=does_not_know, object=char_name
    # Or subject=char_name, relation=hides_secret, object=secret_name
    for rel in relationships:
        sub = rel["subject"].lower()
        rel_type = rel["relation"].lower()
        obj = rel["object"].lower()
        
        # Scenario: B (obj) does not know a secret (sub)
        # E.g. relation="does_not_know"
        if rel_type == "does_not_know" and obj in active_chars:
            secret = sub
            # If the secret word appears in B's direct dialogue or B's action context
            # We look for B saying or acting on the secret
            # Let's split prose into sentences
            sentences = re.split(r'(?<=[.!?])\s+', scene_draft)
            for sent_num, sent in enumerate(sentences, 1):
                if re.search(rf"\b{re.escape(obj)}\b", sent, re.I) and re.search(rf"\b{re.escape(secret)}\b", sent, re.I):
                    failures.append(
                        f"Knowledge Boundary Failure: {obj.capitalize()} does not know about '{secret}' but sentence {sent_num} describes them interacting with or mentioning it: '{sent[:60]}...'"
                    )
                    
    return failures, warnings
