import shutil
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

import yaml

from bookforge.cli import cmd_init
from bookforge.core.characters import extract_character_seeds, scaffold_character_files


class TestCharacterScaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_extract_character_seeds_from_phase_sections(self):
        source = """# Book

## Main Characters

### Jake Moses (Protagonist)
* **Age:** 14.
* **Appearance:** Ash cloak.
* **Voice:** Quiet.

## Supporting and Antagonist Characters

### Winston McCrea (Rival)
* **Personality:** Loud trapper.
"""
        rulebook = """# Rulebook

## Characters
### Jake Moses
- **POV Rules:** Strict third-person limited POV.
- **Private Motive:** Survive independently.
"""
        seeds = extract_character_seeds(source, rulebook)
        self.assertEqual([seed.slug for seed in seeds], ["jake-moses", "winston-mccrea"])
        self.assertEqual(seeds[0].category, "main")
        self.assertEqual(seeds[1].category, "antagonist")
        self.assertIn("Private Motive", seeds[0].rulebook_body)

    def test_scaffold_character_files_writes_parseable_profiles(self):
        book = self.tmp / "book"
        book.mkdir()
        (book / "phase-0.md").write_text(
            """# Book

## Main Characters

### Jake Moses (Protagonist)
* **Age:** 14.
* **Appearance:** Ash cloak.
* **Voice:** Quiet.
""",
            encoding="utf-8",
        )
        (book / "rulebook.md").write_text(
            """# Rulebook

## Characters
### Jake Moses
- **POV Rules:** Strict third-person limited POV.
- **Private Motive:** Survive independently.
""",
            encoding="utf-8",
        )

        created = scaffold_character_files(book)

        profile = book / "characters/main/jake-moses.md"
        self.assertIn(profile, created)
        text = profile.read_text(encoding="utf-8")
        front_matter = text.split("---", 2)[1]
        data = yaml.safe_load(front_matter)
        self.assertEqual(data["id"], "jake-moses")
        self.assertTrue(data["pov"]["allowed"])
        self.assertTrue((book / "characters/cast-index.md").exists())
        self.assertTrue((book / "characters/_schema.character.yml").exists())

    def test_init_creates_character_layer_for_existing_source(self):
        cwd = Path.cwd()
        try:
            import os

            os.chdir(self.tmp)
            book = Path("books/longhunter-series/book-1")
            book.mkdir(parents=True)
            (book / "phase-0.md").write_text(
                """# Book

## Main Characters

### Jake Moses (Protagonist)
* **Appearance:** Ash cloak.
""",
                encoding="utf-8",
            )
            args = Namespace(book_folder="books/longhunter-series/book-1", carry_from=None, agents=None, git=False)
            self.assertEqual(cmd_init(args), 0)
            self.assertTrue((book / "characters/main/jake-moses.md").exists())
        finally:
            import os

            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
