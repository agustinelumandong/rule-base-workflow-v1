"""Event-sourced canon and validation subsystem for BookForge.

Public API re-exports — all callers using `from bookforge.core import canon`
continue to work unchanged.
"""

from bookforge.core.canon.io import (
    get_canon_dir,
    get_entities_dir,
    get_events_dir,
    get_state_dir,
    load_yaml_file,
    save_yaml_file,
    load_characters,
    load_aliases,
    load_locations,
    load_objects,
)
from bookforge.core.canon.fold import discover_events, fold_canon
from bookforge.core.canon.validate import validate_canon
from bookforge.core.canon.apply import (
    apply_chapter_event,
    parse_continuity_out_to_event,
    migrate_legacy_book,
)

__all__ = [
    "get_canon_dir",
    "get_entities_dir",
    "get_events_dir",
    "get_state_dir",
    "load_yaml_file",
    "save_yaml_file",
    "load_characters",
    "load_aliases",
    "load_locations",
    "load_objects",
    "discover_events",
    "fold_canon",
    "validate_canon",
    "apply_chapter_event",
    "parse_continuity_out_to_event",
    "migrate_legacy_book",
]
