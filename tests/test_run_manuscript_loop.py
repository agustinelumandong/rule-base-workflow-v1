import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "manuscript-workflow-orchestrator"
    / "scripts"
    / "run_manuscript_loop.py"
)


def load_loop():
    spec = importlib.util.spec_from_file_location("run_manuscript_loop", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ManuscriptLoopTests(unittest.TestCase):
    def length_state(self, total_words=30500, counts=None):
        loop = load_loop()
        return loop.LengthState(
            target=30000,
            target_source="default",
            target_evidence="",
            target_min=30000,
            target_max=31000,
            total_words=total_words,
            remaining_to_min=max(30000 - total_words, 0),
            counts=counts or [],
        )

    def test_mode_for_status(self):
        loop = load_loop()
        self.assertEqual(loop.mode_for_status("NEEDS_CONTEXT_REPAIR"), "repair")
        self.assertEqual(loop.mode_for_status("NEEDS_CONTINUITY_REPAIR"), "repair")
        self.assertEqual(loop.mode_for_status("NEEDS_STYLE_REPAIR"), "style")
        self.assertEqual(loop.mode_for_status("NEEDS_EXPANSION"), "expansion")
        self.assertEqual(loop.mode_for_status("DONE"), "final")
        self.assertEqual(loop.mode_for_status("BLOCKED"), "blocked")

    def test_classify_done(self):
        loop = load_loop()
        length_state = self.length_state()
        status, reason = loop.classify(
            length_state=length_state,
            book_failures=[],
            reports=[],
            style_issues=[],
            repair_attempts={},
            max_repair_attempts=3,
            continuity_failures=[],
        )
        self.assertEqual(status, "DONE")

    def test_classify_needs_context_repair(self):
        loop = load_loop()
        length_state = self.length_state()
        # Mock a validator report failure
        class MockReport:
            def __init__(self):
                self.failures = ["Context error"]
                self.warnings = []
                self.chapter = type("MockChapter", (), {"slug": "chapter-01"})()

        status, reason = loop.classify(
            length_state=length_state,
            book_failures=[],
            reports=[MockReport()],
            style_issues=[],
            repair_attempts={},
            max_repair_attempts=3,
            continuity_failures=[],
        )
        self.assertEqual(status, "NEEDS_CONTEXT_REPAIR")

    def test_classify_needs_continuity_repair(self):
        loop = load_loop()
        length_state = self.length_state()
        status, reason = loop.classify(
            length_state=length_state,
            book_failures=[],
            reports=[],
            style_issues=[],
            repair_attempts={},
            max_repair_attempts=3,
            continuity_failures=["chapter-01 is missing continuity-out.md"],
        )
        self.assertEqual(status, "NEEDS_CONTINUITY_REPAIR")

    def test_classify_blocked_on_repairs(self):
        loop = load_loop()
        length_state = self.length_state()
        class MockReport:
            def __init__(self):
                self.failures = ["Context error"]
                self.warnings = []
                self.chapter = type("MockChapter", (), {"slug": "chapter-01"})()

        status, reason = loop.classify(
            length_state=length_state,
            book_failures=[],
            reports=[MockReport()],
            style_issues=[],
            repair_attempts={"chapter-01": 3},
            max_repair_attempts=3,
            continuity_failures=[],
        )
        self.assertEqual(status, "BLOCKED")
        self.assertIn("limit reached", reason)

    def test_classify_expansion_takes_priority_over_pacing_rebalance_when_under_target(self):
        loop = load_loop()
        length_state = self.length_state(total_words=29500)
        rhythm_issues = ["Every normal chapter is at or above 2000 words."]
        narrative_issues = [
            loop.narrative_quality.NarrativeIssue(
                "chapter-01",
                "Tension Diversity",
                "WARN",
                "Uniform beat intent pattern in chapter.",
            )
        ]

        status, reason = loop.classify(
            length_state=length_state,
            book_failures=[],
            reports=[],
            style_issues=[],
            repair_attempts={},
            max_repair_attempts=3,
            continuity_failures=[],
            narrative_issues=narrative_issues,
            rhythm_issues=rhythm_issues,
        )

        self.assertEqual(status, "NEEDS_EXPANSION")
        self.assertIn("below target", reason)

    def test_classify_soft_rhythm_warnings_stop_with_warnings(self):
        loop = load_loop()
        length_state = self.length_state(total_words=30000)
        rhythm_issues = [
            loop.ManuscriptIssue(
                severity=loop.Severity.SOFT,
                category=loop.IssueCategory.RHYTHM,
                message="Chapter rhythm advisory.",
            )
        ]

        status, reason = loop.classify(
            length_state=length_state,
            book_failures=[],
            reports=[],
            style_issues=[],
            repair_attempts={},
            max_repair_attempts=3,
            continuity_failures=[],
            rhythm_issues=rhythm_issues,
        )

        self.assertEqual(status, "DONE_WITH_WARNINGS")
        self.assertIn("soft warnings", reason)

    def test_classify_book_level_hard_issue_blocks_expansion(self):
        loop = load_loop()
        length_state = self.length_state(total_words=1000)
        book_failures = [
            loop.ManuscriptIssue(
                severity=loop.Severity.HARD,
                category=loop.IssueCategory.CONTEXT,
                message="Missing rulebook.",
            )
        ]

        status, reason = loop.classify(
            length_state=length_state,
            book_failures=book_failures,
            reports=[],
            style_issues=[],
            repair_attempts={},
            max_repair_attempts=3,
            continuity_failures=[],
        )

        self.assertEqual(status, "NEEDS_BOOK_REPAIR")
        self.assertIn("Book-level hard issues", reason)

    def test_choose_rebalance_chapter_uses_rhythm_trim_candidate(self):
        loop = load_loop()
        counts = [
            loop.length_checker.DraftCount(label="Chapter 1", words=2600),
            loop.length_checker.DraftCount(label="Chapter 2", words=2200),
            loop.length_checker.DraftCount(label="Epilogue", words=500, is_epilogue=True),
        ]
        rhythm_report = SimpleNamespace(
            counts=counts,
            pacing_classes={"chapter-01": "major", "chapter-02": "lean"},
        )

        self.assertEqual(loop.choose_rebalance_chapter(rhythm_report), "chapter-02")

    def test_load_save_persistent_repairs(self):
        loop = load_loop()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            
            # Initially empty
            repairs = loop.load_persistent_repairs(tmp_path)
            self.assertEqual(repairs, {})

            # Save some state
            loop.save_persistent_repairs(tmp_path, {"chapter-01": 2}, "NEEDS_CONTEXT_REPAIR")
            
            # Load it back
            repairs_loaded = loop.load_persistent_repairs(tmp_path)
            self.assertEqual(repairs_loaded, {"chapter-01": 2})

            # Check state file exists
            self.assertTrue((tmp_path / "loop-state.json").exists())


if __name__ == "__main__":
    unittest.main()
