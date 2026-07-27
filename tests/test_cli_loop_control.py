import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bookforge import cli


class RunLoopCliTests(unittest.TestCase):
    def run_cli(self, args):
        try:
            return cli.main(args)
        except SystemExit as error:
            return error.code

    def test_prepare_evaluates_and_prepares_selected_chapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            decision = SimpleNamespace(
                status="NEEDS_CONTEXT_REPAIR",
                report="report",
            )
            with (
                patch("bookforge.cli.loop_controller.evaluate_loop", return_value=decision, create=True),
                patch("bookforge.cli.loop_controller.prepare_loop_action", return_value=book_folder / "chapters/chapter-01/context-packet.md", create=True) as prepare,
            ):
                result = self.run_cli(["run-loop", str(book_folder), "--prepare"])

            self.assertEqual(result, 0)
            prepare.assert_called_once_with(book_folder, decision)

    def test_default_run_only_evaluates(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            decision = SimpleNamespace(status="DONE", report="report")
            with (
                patch("bookforge.cli.loop_controller.evaluate_loop", return_value=decision) as evaluate,
                patch("bookforge.cli.loop_controller.prepare_loop_action") as prepare,
            ):
                result = self.run_cli(["run-loop", str(book_folder)])

            self.assertEqual(result, 0)
            evaluate.assert_called_once()
            prepare.assert_not_called()

    def test_record_repair_records_before_evaluating(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "chapters" / "chapter-01").mkdir(parents=True)
            decision = SimpleNamespace(status="DONE", report="report")
            with (
                patch("bookforge.cli.loop_controller.record_repair_attempt", return_value=1) as record,
                patch("bookforge.cli.loop_controller.evaluate_loop", return_value=decision),
            ):
                result = self.run_cli(["run-loop", str(book_folder), "--record-repair", "chapter-01"])

            self.assertEqual(result, 0)
            record.assert_called_once_with(book_folder, "chapter-01")

    def test_record_repair_rejects_a_missing_chapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            with patch("bookforge.cli.loop_controller.evaluate_loop") as evaluate:
                result = self.run_cli(
                    ["run-loop", str(book_folder), "--record-repair", "chapter-99"]
                )

            self.assertEqual(result, 2)
            evaluate.assert_not_called()

    def test_prepare_and_record_repair_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                ["run-loop", tmp, "--prepare", "--record-repair", "chapter-01"]
            )
        self.assertEqual(result, 2)

    def test_blocked_decision_returns_exit_code_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            decision = SimpleNamespace(status="BLOCKED", report="report")
            with patch("bookforge.cli.loop_controller.evaluate_loop", return_value=decision):
                result = self.run_cli(["run-loop", str(book_folder)])
        self.assertEqual(result, 2)

    def test_prepare_terminal_decision_reports_no_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            decision = SimpleNamespace(status="DONE", report="report")
            with (
                patch("bookforge.cli.loop_controller.evaluate_loop", return_value=decision),
                patch("bookforge.cli.loop_controller.prepare_loop_action", return_value=None) as prepare,
            ):
                result = self.run_cli(["run-loop", str(book_folder), "--prepare"])

            self.assertEqual(result, 0)
            prepare.assert_called_once_with(book_folder, decision)
