import tempfile
import unittest
from pathlib import Path

from bookforge.core.packet import relevant_research_excerpt
from bookforge.core.research import add_research_fact, get_research_pack_path
from bookforge.core.validator import check_unprofiled_period_terms


class ResearchSystemTests(unittest.TestCase):
    def test_relevant_research_excerpt_filtering(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            research_file = book_folder / "research-pack.md"
            research_file.write_text(
                "# Research Pack\n\n"
                "## Weapons & Ammo\n"
                "- Winchester 1873 rifle.\n\n"
                "## Medicine & Survival\n"
                "- Carbolic acid for cleaning.\n",
                encoding="utf-8"
            )

            # Scene 1: Contains weapon terms
            scene_text_1 = "Jed reached for his rifle and shot at the wolf."
            excerpt_1 = relevant_research_excerpt(book_folder, scene_text_1)
            self.assertIn("## Weapons & Ammo", excerpt_1)
            self.assertNotIn("## Medicine & Survival", excerpt_1)

            # Scene 2: Contains medical terms
            scene_text_2 = "The doctor cleaned the wound."
            excerpt_2 = relevant_research_excerpt(book_folder, scene_text_2)
            self.assertNotIn("## Weapons & Ammo", excerpt_2)
            self.assertIn("## Medicine & Survival", excerpt_2)

            # Scene 3: Contains no matching terms
            scene_text_3 = "Jed looked at the sky."
            excerpt_3 = relevant_research_excerpt(book_folder, scene_text_3)
            self.assertEqual(excerpt_3, "")

    def test_check_unprofiled_period_terms_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            research_file = book_folder / "research-pack.md"
            research_file.write_text(
                "# Research Pack\n\n"
                "## Weapons & Ammo\n"
                "- Winchester 1873 rifle.\n",
                encoding="utf-8"
            )

            # Draft 1: Winchester is documented -> no warnings
            text_1 = "He held the Winchester tight."
            warnings_1 = check_unprofiled_period_terms(text_1, book_folder)
            self.assertEqual(warnings_1, [])

            # Draft 2: Sharps is not documented -> warning raised
            text_2 = "He loaded the Sharps buffalo rifle."
            warnings_2 = check_unprofiled_period_terms(text_2, book_folder)
            self.assertEqual(len(warnings_2), 1)
            self.assertIn("sharps", warnings_2[0])

    def test_add_research_fact_modifications(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            
            # Initial fact addition (creates file from template or basic format)
            add_research_fact(book_folder, "Weapons & Ammo", "Colt Peacemaker revolver.")
            research_file = get_research_pack_path(book_folder)
            self.assertTrue(research_file.exists())
            
            content = research_file.read_text(encoding="utf-8")
            self.assertIn("## Weapons & Ammo", content)
            self.assertIn("Colt Peacemaker revolver.", content)
            
            # Add a second fact to the same category
            add_research_fact(book_folder, "Weapons & Ammo", "Winchester 1873 rifle.")
            content_2 = research_file.read_text(encoding="utf-8")
            self.assertIn("Colt Peacemaker revolver.", content_2)
            self.assertIn("Winchester 1873 rifle.", content_2)
            
            # Add duplicate fact should not change anything
            add_research_fact(book_folder, "Weapons & Ammo", "Winchester 1873 rifle.")
            content_3 = research_file.read_text(encoding="utf-8")
            # Count occurrences of Winchester in file
            self.assertEqual(content_3.count("Winchester 1873 rifle."), 1)

            # Add new custom category
            add_research_fact(book_folder, "Law & Order", "Sheriff had full arrest authority.")
            content_4 = research_file.read_text(encoding="utf-8")
            self.assertIn("## Law & Order", content_4)
            self.assertIn("Sheriff had full arrest authority.", content_4)

    def test_merge_research_pack_contents(self):
        from bookforge.core.research import merge_research_pack_contents
        
        old_content = """# Research Pack

> [!NOTE]
> Automatically synced on 2026-06-17.

### Weapons & Ammo
* **Colt Peacemaker:** A standard issue revolver.
* **Sharps Carbine:** Heavy caliber single shot.
"""
        new_content = """### Weapons & Ammo
* **Colt Peacemaker:** Different description of same gun.
* **Winchester 73:** Repeating lever action rifle.

### Travel & Transport
- **Stagecoach:** Rapid transit coach.
"""
        merged = merge_research_pack_contents(old_content, new_content)
        
        # Colt Peacemaker should keep description from old_content
        self.assertIn("Colt Peacemaker:** A standard issue revolver.", merged)
        self.assertNotIn("Colt Peacemaker:** Different description of same gun.", merged)
        
        # Sharps Carbine must be preserved
        self.assertIn("Sharps Carbine:** Heavy caliber single shot.", merged)
        
        # Winchester 73 must be added
        self.assertIn("Winchester 73:** Repeating lever action rifle.", merged)
        
        # Travel & Transport category must be added
        self.assertIn("### Travel & Transport", merged)
        self.assertIn("Stagecoach:** Rapid transit coach.", merged)


if __name__ == "__main__":
    unittest.main()
