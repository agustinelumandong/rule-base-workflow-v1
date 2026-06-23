import unittest
import tempfile
import yaml
from pathlib import Path
from bookforge.core.research_cache import (
    ResearchCacheEntry,
    normalize_research_key,
    lookup_research_cache,
    write_research_cache_entry,
    query_with_cache,
    purge_error_entries,
    mark_research_accepted,
    get_accepted_research_for_scene
)
from bookforge.core.packet.builder import build_scene_packet
from bookforge.core.scene import init_scene_manifest


class MockResearchBackend:
    def __init__(self):
        self.query_count = 0
        self.last_query = None

    def raw_query(self, query_str: str) -> str:
        self.query_count += 1
        self.last_query = query_str
        return f"Mock answer for: {query_str}"

    def query(self, query_str: str) -> str:
        return self.raw_query(query_str)


class ResearchCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.book_folder = Path(self.temp_dir.name)
        
        # Scaffold minimal structure
        (self.book_folder / "characters" / "main").mkdir(parents=True, exist_ok=True)
        (self.book_folder / "rulebook.md").write_text("# Rulebook", encoding="utf-8")
        
        # Initialize manifest
        self.scene_key = "chapter-01/scene-01"
        self.manifest_path = init_scene_manifest(self.book_folder, "chapter-01", "scene-01")
        
        # Update manifest research questions
        manifest_data = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        manifest_data["research_questions"] = ["Could this rifle exist in 1778?"]
        self.manifest_path.write_text(yaml.safe_dump(manifest_data), encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cache_key_is_deterministic(self):
        key1 = normalize_research_key("Could this rifle exist in 1778?", "weapons")
        key2 = normalize_research_key("Could this rifle exist in 1778?", "weapons")
        self.assertEqual(key1, key2)
        self.assertEqual(key1, "weapons/could_this_rifle_exist_in_1778")

        # Category is stripped and lowercase
        key3 = normalize_research_key("Some Query", " Weapons ")
        self.assertTrue(key3.startswith("weapons/"))

    def test_cache_miss_calls_backend(self):
        backend = MockResearchBackend()
        question = "Could this rifle exist in 1778?"
        
        # Cache is empty initially
        entry = lookup_research_cache(self.book_folder, "weapons/could_this_rifle_exist_in_1778")
        self.assertIsNone(entry)
        
        # Query
        entry = query_with_cache(self.book_folder, question, backend, category="weapons")
        self.assertEqual(backend.query_count, 1)
        self.assertEqual(entry.answer, "Mock answer for: Could this rifle exist in 1778?")
        self.assertEqual(entry.canon_status, "pending")

        # Lookup in cache
        cached = lookup_research_cache(self.book_folder, entry.key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.answer, entry.answer)

    def test_cache_hit_skips_backend(self):
        backend = MockResearchBackend()
        question = "Could this rifle exist in 1778?"
        
        # First query (miss)
        query_with_cache(self.book_folder, question, backend, category="weapons")
        self.assertEqual(backend.query_count, 1)

        # Second query (hit)
        entry = query_with_cache(self.book_folder, question, backend, category="weapons")
        self.assertEqual(backend.query_count, 1)  # count remains 1
        self.assertEqual(entry.answer, "Mock answer for: Could this rifle exist in 1778?")

    def test_used_by_scene_is_recorded(self):
        backend = MockResearchBackend()
        question = "Could this rifle exist in 1778?"
        
        # Miss with scene_key
        entry = query_with_cache(
            self.book_folder, question, backend, category="weapons", scene_key="chapter-01/scene-01"
        )
        self.assertEqual(entry.used_by, ["chapter-01/scene-01"])

        # Hit with another scene_key
        entry2 = query_with_cache(
            self.book_folder, question, backend, category="weapons", scene_key="chapter-01/scene-02"
        )
        self.assertIn("chapter-01/scene-01", entry2.used_by)
        self.assertIn("chapter-01/scene-02", entry2.used_by)

    def test_pending_cache_not_packet_eligible(self):
        backend = MockResearchBackend()
        question = "Could this rifle exist in 1778?"
        
        # Query to populate cache as pending
        query_with_cache(
            self.book_folder, question, backend, category="weapons", scene_key="chapter-01/scene-01"
        )
        
        # Render packet
        packet = build_scene_packet(self.book_folder, "chapter-01", "scene-01")
        self.assertNotIn("Relevant Research Facts", packet)
        self.assertNotIn("Mock answer for:", packet)

    def test_accepted_cache_included_in_scene_packet(self):
        backend = MockResearchBackend()
        question = "Could this rifle exist in 1778?"
        
        # Query
        entry = query_with_cache(
            self.book_folder, question, backend, category="weapons", scene_key="chapter-01/scene-01"
        )
        
        # Accept
        mark_research_accepted(self.book_folder, entry.key)
        
        # Render packet
        packet = build_scene_packet(self.book_folder, "chapter-01", "scene-01")
        self.assertIn("Relevant Research Facts", packet)
        self.assertTrue(
            "Mock answer for: Could this rifle exist in 1778?" in packet or
            "Mock answer for: Could rifle exist in 1778?" in packet,
            f"Expected mock answer not found in packet: {packet}"
        )
        self.assertIn("Provenance:", packet)

    def test_rejected_cache_excluded(self):
        backend = MockResearchBackend()
        question = "Could this rifle exist in 1778?"
        
        # Query
        entry = query_with_cache(
            self.book_folder, question, backend, category="weapons", scene_key="chapter-01/scene-01"
        )
        
        # Reject
        entry.canon_status = "rejected"
        write_research_cache_entry(self.book_folder, entry)
        
        # Render packet
        packet = build_scene_packet(self.book_folder, "chapter-01", "scene-01")
        self.assertNotIn("Relevant Research Facts", packet)
        self.assertNotIn("Mock answer for:", packet)


class ErrorAnswerCacheTests(unittest.TestCase):
    """Tests for error answer detection and cache purge behavior."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.book_folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_error_answer_not_cached(self):
        """Query that returns an error should not persist to cache."""
        class ErrorBackend:
            def raw_query(self, q):
                return "Error: research-pack.md does not exist."

        backend = ErrorBackend()
        entry = query_with_cache(
            self.book_folder, "What was the weather?", backend, category="locations"
        )
        # Entry returned but not cached
        self.assertEqual(entry.canon_status, "rejected")
        self.assertIn("Error:", entry.answer)

        # Verify nothing written to cache directory
        cache_dir = self.book_folder / "research_cache"
        if cache_dir.exists():
            yml_files = list(cache_dir.rglob("*.yml")) + list(cache_dir.rglob("*.yaml"))
            self.assertEqual(len(yml_files), 0)

    def test_cached_error_entry_retried_on_lookup(self):
        """If an error entry somehow exists in cache, next query should purge and retry."""
        key = normalize_research_key("What was the weather?", "locations")
        error_entry = ResearchCacheEntry(
            key=key,
            category="locations",
            subject="weather",
            period="18th century",
            question="What was the weather?",
            answer="Error: research-pack.md does not exist.",
            confidence="low",
            canon_status="pending",
            source_backend="manual",
        )
        write_research_cache_entry(self.book_folder, error_entry)

        # Verify it's there
        cached = lookup_research_cache(self.book_folder, key)
        self.assertIsNotNone(cached)
        self.assertIn("Error:", cached.answer)

        # Now query with a backend that returns a good answer
        class GoodBackend:
            def raw_query(self, q):
                return "Hot and dry summers."

        backend = GoodBackend()
        entry = query_with_cache(
            self.book_folder, "What was the weather?", backend, category="locations"
        )
        # Should have retried and gotten the good answer
        self.assertEqual(entry.answer, "Hot and dry summers.")
        self.assertEqual(entry.canon_status, "pending")

        # Error entry should be purged from cache
        cached2 = lookup_research_cache(self.book_folder, key)
        if cached2:
            self.assertNotIn("Error:", cached2.answer)

    def test_purge_error_entries(self):
        """purge_error_entries removes only error entries, keeps valid ones."""
        key1 = normalize_research_key("Weather in summer?", "locations")
        key2 = normalize_research_key("What rifle did he use?", "weapons")

        # Write an error entry
        error_entry = ResearchCacheEntry(
            key=key1, category="locations", subject="weather", period="18th century",
            question="Weather in summer?", answer="Error: file missing.",
            confidence="low", canon_status="pending", source_backend="manual",
        )
        write_research_cache_entry(self.book_folder, error_entry)

        # Write a valid entry
        valid_entry = ResearchCacheEntry(
            key=key2, category="weapons", subject="rifle", period="18th century",
            question="What rifle did he use?", answer="Pennsylvania long rifle.",
            confidence="high", canon_status="accepted", source_backend="manual",
        )
        write_research_cache_entry(self.book_folder, valid_entry)

        removed = purge_error_entries(self.book_folder)
        self.assertEqual(removed, 1)

        # Error entry gone
        self.assertIsNone(lookup_research_cache(self.book_folder, key1))
        # Valid entry still present
        self.assertIsNotNone(lookup_research_cache(self.book_folder, key2))

    def test_purge_empty_cache_returns_zero(self):
        """purge_error_entries on empty directory returns 0."""
        removed = purge_error_entries(self.book_folder)
        self.assertEqual(removed, 0)

    def test_purge_preserves_accepted_error_entries(self):
        """purge_error_entries skips entries with canon_status='accepted', even if error."""
        key = normalize_research_key("Weather in summer?", "locations")
        accepted_error = ResearchCacheEntry(
            key=key, category="locations", subject="weather", period="18th century",
            question="Weather in summer?", answer="Error: some error.",
            confidence="low", canon_status="accepted", source_backend="manual",
        )
        write_research_cache_entry(self.book_folder, accepted_error)

        removed = purge_error_entries(self.book_folder)
        self.assertEqual(removed, 0)
        self.assertIsNotNone(lookup_research_cache(self.book_folder, key))


class QualityGateTests(unittest.TestCase):
    """Tests for P5.1 research answer quality gate."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.book_folder = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_irrelevant_manual_backend_answer_not_cached(self):
        """Backend returning only mismatched headers should not produce a cache file."""
        class WeaponsOnlyBackend:
            def raw_query(self, q):
                return (
                    "## Weapons & Ammo\n"
                    "- Colt Peacemaker: Single-action revolver.\n"
                    "- Winchester 1873: Lever-action rifle.\n"
                )

        backend = WeaponsOnlyBackend()
        entry = query_with_cache(
            self.book_folder,
            "What was the weather like in this region?",
            backend,
            category="locations",
        )
        self.assertEqual(entry.canon_status, "uncached")

        # No cache file should exist
        cache_dir = self.book_folder / "research_cache"
        if cache_dir.exists():
            yml_files = list(cache_dir.rglob("*.yml")) + list(cache_dir.rglob("*.yaml"))
            self.assertEqual(len(yml_files), 0)

    def test_category_mismatch_answer_not_cached(self):
        """Requested category=locations but answer has only weapons headers → uncached."""
        class MismatchBackend:
            def raw_query(self, q):
                return (
                    "## Weapons & Ammo\n"
                    "- Sharps Big Fifty: Single-shot buffalo rifle.\n\n"
                    "## Clothing & Gear\n"
                    "- Wool flannel shirts.\n"
                )

        backend = MismatchBackend()
        entry = query_with_cache(
            self.book_folder,
            "Describe the terrain near the river.",
            backend,
            category="locations",
        )
        self.assertEqual(entry.canon_status, "uncached")
        self.assertNotEqual(entry.canon_status, "pending")

        # Verify no file written
        key = normalize_research_key("Describe the terrain near the river.", "locations")
        self.assertIsNone(lookup_research_cache(self.book_folder, key))


if __name__ == "__main__":
    unittest.main()
