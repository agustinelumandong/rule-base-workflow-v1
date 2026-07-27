import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bookforge.core import loop as loop_core

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

    def test_classify_missing_chapter_review_routes_to_review_state(self):
        loop = load_loop()
        length_state = self.length_state()

        class MockReport:
            def __init__(self):
                self.failures = ["Compiled chapter is missing required `chapter-review.md`."]
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

        self.assertEqual(status, "NEEDS_CHAPTER_REVIEW")
        self.assertIn("review is missing", reason)

    def test_chapter_review_selects_the_failing_chapter(self):
        loop = load_loop()
        self.assertEqual(
            loop.action_chapter(
                "NEEDS_CHAPTER_REVIEW", ["chapter-01"], "NONE", [], []
            ),
            "chapter-01",
        )

    def test_classify_non_ready_chapter_review_routes_to_rhythm_rebalance(self):
        loop = load_loop()
        length_state = self.length_state()

        class MockReport:
            def __init__(self):
                self.failures = ["`chapter-review.md` decision is `needs-rhythm-fix`, so the compiled chapter is not ready."]
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

        self.assertEqual(status, "NEEDS_RHYTHM_REBALANCE")
        self.assertIn("not ready", reason)

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

    def test_evaluate_loop_returns_decision_without_writing_state(self):
        loop = load_loop()
        self.assertTrue(hasattr(loop, "evaluate_loop"))
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            state_path = book_folder / "loop-state.json"
            original_state = {
                "notebook_id": "notebook-123",
                "repair_attempts": {"chapter-01": 1},
            }
            state_path.write_text(json.dumps(original_state), encoding="utf-8")
            with (
                patch.object(loop_core, "build_length_state", return_value=self.length_state()),
                patch.object(loop_core, "_required_book_file_issues", return_value=([], [])),
                patch.object(loop_core.context_validator, "parse_phase_chapters", return_value={}),
                patch.object(loop_core.context_validator, "discover_chapters", return_value=[]),
                patch.object(loop_core, "scan_style_issues", return_value=[]),
                patch.object(loop_core.narrative_quality, "analyze", return_value=SimpleNamespace(issues=[])),
                patch.object(loop_core.check_chapter_rhythm, "analyze", return_value=SimpleNamespace(issues=[], counts=[])),
            ):
                decision = loop.evaluate_loop(book_folder)

            self.assertIsInstance(decision, loop.LoopDecision)
            self.assertEqual(decision.status, "DONE")
            self.assertTrue(decision.terminal)
            self.assertFalse(decision.requires_human)
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), original_state)

    def test_prepare_loop_action_writes_only_packet_and_preserves_state(self):
        loop = load_loop()
        self.assertTrue(hasattr(loop, "LoopDecision"))
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            chapter_folder = book_folder / "chapters" / "chapter-01"
            chapter_folder.mkdir(parents=True)
            source_files = {
                book_folder / "phase-0.md": "# Test Book\n\n## Chapter 1\nA source beat.",
                book_folder / "rulebook.md": "# Rulebook\n\n## Source Hierarchy\nOutline wins.",
                book_folder / "mood-lock.md": "# Mood\n\nPlain prose.",
                book_folder / "chapter-summaries.md": "## Chapter 1\nA summary.",
                chapter_folder / "chapter-01.md": "Draft prose.",
                chapter_folder / "scene-breakdown.md": "## Scene 1\nA hard choice.",
            }
            for path, text in source_files.items():
                path.write_text(text, encoding="utf-8")
            state_path = book_folder / "loop-state.json"
            state_path.write_text(json.dumps({"notebook_id": "notebook-123"}), encoding="utf-8")
            decision = loop.LoopDecision(
                status="NEEDS_CONTEXT_REPAIR",
                reason="Context validator reported chapter failures.",
                prompt_mode="repair",
                target_chapter="chapter-01",
                next_action="Repair context issues in chapter-01.",
                terminal=False,
                requires_human=True,
                report="report",
            )

            packet_path = loop.prepare_loop_action(book_folder, decision)

            self.assertEqual(packet_path, chapter_folder / "context-packet.md")
            self.assertTrue(packet_path.exists())
            for path, text in source_files.items():
                self.assertEqual(path.read_text(encoding="utf-8"), text)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["notebook_id"], "notebook-123")
            self.assertEqual(state["last_decision"]["status"], "NEEDS_CONTEXT_REPAIR")
            self.assertEqual(state["last_prepared_packet"], str(packet_path))
            self.assertIn("last_prepared_at", state)
            self.assertEqual(state["last_status"], "NEEDS_CONTEXT_REPAIR")

    def test_record_repair_attempt_is_explicit_and_blocks_at_limit(self):
        loop = load_loop()
        self.assertTrue(hasattr(loop, "record_repair_attempt"))
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            for expected in (1, 2, 3):
                self.assertEqual(loop.record_repair_attempt(book_folder, "chapter-01"), expected)

            report = SimpleNamespace(
                failures=["Context error"],
                warnings=[],
                chapter=SimpleNamespace(slug="chapter-01"),
            )
            status, _reason = loop.classify(
                self.length_state(), [], [report], [],
                loop.load_persistent_repairs(book_folder), 3, [],
            )
            self.assertEqual(status, "BLOCKED")

    def test_terminal_decision_does_not_prepare_files(self):
        loop = load_loop()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            decision = loop.LoopDecision(
                status="DONE",
                reason="Complete.",
                prompt_mode="final",
                target_chapter=None,
                next_action="Stop.",
                terminal=True,
                requires_human=False,
                report="report",
            )

            self.assertIsNone(loop.prepare_loop_action(book_folder, decision))
            self.assertFalse((book_folder / "loop-state.json").exists())


if __name__ == "__main__":
    unittest.main()
