import tempfile
import unittest
from pathlib import Path

from bookforge.core.analytics import (
    estimate_tokens,
    get_file_metrics,
    get_project_file_analytics,
    load_analytics,
    log_run
)


class AnalyticsSystemTests(unittest.TestCase):
    def test_token_estimation(self):
        text = "Hello world! This is a simple sentence."
        tokens = estimate_tokens(text)
        self.assertGreater(tokens, 0)
        # Empty string should return 0
        self.assertEqual(estimate_tokens(""), 0)

    def test_file_metrics_calculation(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.md"
            test_file.write_text("Line one\nLine two\nLine three\n", encoding="utf-8")
            
            metrics = get_file_metrics(test_file)
            self.assertEqual(metrics["lines"], 3)
            self.assertEqual(metrics["words"], 6)
            self.assertEqual(metrics["chars"], len("Line one\nLine two\nLine three\n"))
            self.assertGreater(metrics["tokens"], 0)

    def test_project_file_analytics_scanning(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            
            # Create core files
            (book_folder / "phase-0.md").write_text("Outline content", encoding="utf-8")
            (book_folder / "rulebook.md").write_text("Rules content", encoding="utf-8")
            
            # Create a chapter
            chap_folder = book_folder / "chapters" / "chapter-01"
            chap_folder.mkdir(parents=True)
            (chap_folder / "scene-breakdown.md").write_text("Breakdown content", encoding="utf-8")
            (chap_folder / "chapter-01.md").write_text("Draft content", encoding="utf-8")
            
            analytics = get_project_file_analytics(book_folder)
            
            # Core outline and rulebook should be present
            self.assertIn("outline", analytics)
            self.assertIn("rulebook", analytics)
            self.assertEqual(analytics["outline"]["metrics"]["words"], 2)
            
            # Chapters details should be correct
            self.assertIn("chapters", analytics)
            self.assertEqual(len(analytics["chapters"]), 1)
            self.assertEqual(analytics["chapters"][0]["slug"], "chapter-01")
            self.assertIn("scene_breakdown", analytics["chapters"][0]["files"])
            self.assertIn("draft", analytics["chapters"][0]["files"])

    def test_log_run_and_analytics_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            
            # Check default empty state
            data = load_analytics(book_folder)
            self.assertEqual(data["total_runs"], 0)
            self.assertEqual(data["total_input_tokens"], 0)
            self.assertEqual(data["total_output_tokens"], 0)
            self.assertEqual(data["last_model_used"], "unknown")
            self.assertEqual(len(data["runs"]), 0)
            
            # Log first run
            log_run(book_folder, model="gpt-4o", input_tokens=1000, output_tokens=250, action="draft")
            
            data_1 = load_analytics(book_folder)
            self.assertEqual(data_1["total_runs"], 1)
            self.assertEqual(data_1["total_input_tokens"], 1000)
            self.assertEqual(data_1["total_output_tokens"], 250)
            self.assertEqual(data_1["last_model_used"], "gpt-4o")
            self.assertEqual(len(data_1["runs"]), 1)
            self.assertEqual(data_1["runs"][0]["action"], "draft")
            
            # Log second run
            log_run(book_folder, model="claude-3-5-sonnet", input_tokens=5000, output_tokens=1500, action="repair")
            
            data_2 = load_analytics(book_folder)
            self.assertEqual(data_2["total_runs"], 2)
            self.assertEqual(data_2["total_input_tokens"], 6000)
            self.assertEqual(data_2["total_output_tokens"], 1750)
            self.assertEqual(data_2["last_model_used"], "claude-3-5-sonnet")
            self.assertEqual(len(data_2["runs"]), 2)


if __name__ == "__main__":
    unittest.main()
