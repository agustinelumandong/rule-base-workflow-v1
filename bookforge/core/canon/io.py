"""YAML I/O helpers and entity loaders for the canon subsystem."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def get_canon_dir(book_folder: Path) -> Path:
    return book_folder / "canon"


def get_entities_dir(book_folder: Path) -> Path:
    return get_canon_dir(book_folder) / "entities"


def get_events_dir(book_folder: Path) -> Path:
    return get_canon_dir(book_folder) / "events"


def get_state_dir(book_folder: Path) -> Path:
    return get_canon_dir(book_folder) / "state"


# ---------------------------------------------------------------------------
# YAML read/write
# ---------------------------------------------------------------------------

def load_yaml_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        return {}


def save_yaml_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Entity loaders
# ---------------------------------------------------------------------------

def load_characters(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "characters.yml")
    return data.get("characters", {})


def load_aliases(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "aliases.yml")
    return data.get("aliases", {})


def load_locations(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "locations.yml")
    return data.get("locations", {})


def load_objects(book_folder: Path) -> dict:
    data = load_yaml_file(get_entities_dir(book_folder) / "objects.yml")
    return data.get("objects", {})
