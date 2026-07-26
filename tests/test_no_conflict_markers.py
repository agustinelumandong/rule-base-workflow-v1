import unittest
from pathlib import Path


class NoConflictMarkersTests(unittest.TestCase):
    def test_python_sources_contain_no_merge_markers(self):
        root = Path(__file__).resolve().parents[1]
        for path in (*root.joinpath("bookforge").rglob("*.py"), *root.joinpath("tests").rglob("*.py")):
            self.assertNotRegex(
                path.read_text(encoding="utf-8"),
                r"(?m)^(<<<<<<<|=======|>>>>>>>)",
                path.relative_to(root).as_posix(),
            )
