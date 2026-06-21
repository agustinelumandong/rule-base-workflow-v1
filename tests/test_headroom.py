import unittest
from bookforge.core.headroom import compress_text


class HeadroomTests(unittest.TestCase):
    def test_compress_text_prunes_filler_phrases(self):
        text = "Please make sure to check the horse. The following is a detailed report."
        compressed = compress_text(text)
        # Check that fillers are removed/simplified
        self.assertNotIn("Please make sure to", compressed)
        self.assertNotIn("The following is a", compressed)
        self.assertIn("check the horse", compressed)

    def test_compress_text_preserves_special_headers_and_locks(self):
        text = (
            "### Source Context Lock\n"
            "- **Source Anchor:** Chapter 1\n"
            "This is a general sentence. Please make sure to read it."
        )
        compressed = compress_text(text)
        # Special headers and locks must be completely preserved
        self.assertIn("### Source Context Lock", compressed)
        self.assertIn("- **Source Anchor:** Chapter 1", compressed)
        # Standard sentence should still be compressed
        self.assertNotIn("Please make sure to", compressed)

    def test_compress_text_removes_decorative_separators_and_spaces(self):
        text = "Line 1\n\n\n---\n\nLine 2\n  \t  \nLine 3"
        compressed = compress_text(text)
        # Layout spacing is minimized, separators are removed
        self.assertNotIn("---", compressed)
        # Collapses multiple blank lines into at most one empty line
        self.assertIn("Line 1\n\nLine 2\n\nLine 3", compressed)


if __name__ == "__main__":
    unittest.main()
