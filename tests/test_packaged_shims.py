import unittest
from pathlib import Path
import sys

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bookforge.core import (
    validator,
    loop,
    length,
    rhythm,
    compiler,
    scanner,
    chain,
    packet,
    budget,
    pacing,
    narrative_quality,
)
from bookforge import cli

class TestPackagedModules(unittest.TestCase):
    def test_imports_and_structure(self):
        # Verify package structure imports cleanly
        self.assertIsNotNone(validator.validate_required_book_files)
        self.assertIsNotNone(loop.run_loop_check)
        self.assertIsNotNone(length.find_drafts)
        self.assertIsNotNone(rhythm.analyze)
        self.assertIsNotNone(compiler.compile_manuscript)
        self.assertIsNotNone(scanner.check_gaps)
        self.assertIsNotNone(chain.analyze_chain)
        self.assertIsNotNone(packet.render_packet)
        self.assertIsNotNone(budget.mode_files)
        self.assertIsNotNone(pacing.build_plan)
        self.assertIsNotNone(narrative_quality.analyze)

    def test_cli_subparsers(self):
        # Verify main CLI entrypoint works
        self.assertIsNotNone(cli.main)

if __name__ == "__main__":
    unittest.main()
