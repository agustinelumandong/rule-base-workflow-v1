import pytest
from pathlib import Path
from bookforge.core.adapters.compression import get_compression_backend, LocalRegexBackend, HeadroomBackend
from bookforge.core.adapters.research import get_research_backend, ManualBackend, NotebookLMBackend


def test_local_regex_compression():
    compressor = LocalRegexBackend()

    # Test comment removal
    text_with_comments = "Hello<!-- comment --> World"
    assert compressor.compress(text_with_comments) == "Hello World"

    # Test space and newline normalization
    padded_text = """
    # Title

    Some   padded   text.


    More text.
    """
    compressed = compressor.compress(padded_text)
    assert "# Title" in compressed
    assert "Some padded text." in compressed
    assert "\n\n" in compressed
    assert "\n\n\n" not in compressed


def test_headroom_backend_fallback():
    backend = HeadroomBackend()
    text = "Simple paragraph text to compress."
    compressed = backend.compress(text)
    assert len(compressed) <= len(text)


def test_manual_research_backend(tmp_path):
    book_folder = tmp_path / "book-test"
    book_folder.mkdir()

    # Create dummy research template
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    template = templates_dir / "research-pack.md"
    template.write_text("# Research Pack\n\n## Weapons\n- Peacemaker .45\n", encoding="utf-8")

    # Monkeypatch the default template path for tests
    import bookforge.core.research
    bookforge.core.research.DEFAULT_TEMPLATE_PATH = template

    # Seed the book's research-pack.md from the monkeypatched template so the
    # backend has something to query (ManualBackend reads from the book folder).
    from bookforge.core.research import ensure_research_pack
    pack_path = ensure_research_pack(book_folder)
    assert pack_path.exists()

    backend = get_research_backend(book_folder, "manual")
    assert isinstance(backend, ManualBackend)

    # Test query on non-existent
    res = backend.query("Peacemaker")
    assert "Peacemaker .45" in res

    # Test ingest single file
    fact_file = tmp_path / "new_fact.txt"
    fact_file.write_text("## Weapons\n- Winchester '73\n", encoding="utf-8")
    backend.ingest(fact_file)

    # Query again and verify Winchester is ingested
    res_after = backend.query("Winchester")
    assert "Winchester '73" in res_after


def test_get_research_backend_fallback(tmp_path):
    # Verify fallback to ManualBackend when no notebook is associated
    backend = get_research_backend(tmp_path, "notebooklm")
    assert isinstance(backend, ManualBackend)
