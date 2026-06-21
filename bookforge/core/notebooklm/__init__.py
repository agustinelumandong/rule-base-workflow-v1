"""BookForge NotebookLM Integration Core Package."""

from bookforge.core.notebooklm.client import (
    is_nlm_available,
    get_auth_status,
    list_notebooks,
    create_new_notebook,
    query_notebook,
)
from bookforge.core.notebooklm.ops import (
    get_associated_notebook,
    set_associated_notebook,
    sync_research_to_pack,
    upload_local_sources,
    generate_research_outline,
)
