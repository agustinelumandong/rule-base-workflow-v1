import ast
import unittest
from pathlib import Path

from bookforge.core import validator, validators


MIGRATED_PUBLIC_SYMBOLS = (
    "ChapterReport",
    "key_terms",
    "coverage",
    "extract_scene_fields",
    "validate_draft",
    "validate_source_alignment",
    "validate_chapter",
    "collect_all_issues",
    "overall_status",
    "render_report",
    "parse_args",
    "build_ai_prompt",
    "main",
)


class ValidatorFacadeTests(unittest.TestCase):
    def test_validator_is_a_pure_reexport_of_validators_package(self):
        facade_path = Path(validator.__file__)
        tree = ast.parse(facade_path.read_text(encoding="utf-8"))

        implementations = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        self.assertEqual(implementations, [])
        for symbol in MIGRATED_PUBLIC_SYMBOLS:
            self.assertIs(getattr(validator, symbol), getattr(validators, symbol))


    def test_migrated_source_alignment_helpers_preserve_behavior(self):
        fields = validators.extract_scene_fields(
            "- **Source Anchor:** Ride through Granite Pass\n"
            "- **Required Story Movement:** Exit hook / transition required by source: Find the broken wagon\n"
        )

        self.assertEqual(fields, ["Ride through Granite Pass", "Find the broken wagon"])
        self.assertEqual(validators.key_terms("Ride through Granite Pass"), {"ride", "granite", "pass"})


if __name__ == "__main__":
    unittest.main()
