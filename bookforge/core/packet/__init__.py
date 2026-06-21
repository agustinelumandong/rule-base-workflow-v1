"""BookForge Context Packet Core Package."""

from bookforge.core.packet.compress import (
    COMPRESSED_STYLE_LOCK,
    compress_text,
)
from bookforge.core.packet.helpers import (
    read_optional,
    word_excerpt,
    chapter_number,
    chapter_label_patterns,
    extract_heading_section,
    extract_matching_lines,
    chapter_sort_key,
    chapter_slugs,
    neighbor_slug,
    chapter_folder,
    chapter_draft_path,
)
from bookforge.core.packet.excerpt import (
    optimize_character_profiles,
    relevant_rulebook_excerpt_from_text,
    relevant_rulebook_excerpt,
    extract_named_section,
    prior_continuity,
    next_continuity_need,
    pacing_excerpt,
    relevant_research_excerpt,
    load_subgenre_rules,
)
from bookforge.core.packet.builder import (
    TASK_BUDGETS,
    estimate_tokens,
    build_context_packet,
    render_packet,
    main,
)
