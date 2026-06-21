import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bookforge.core import narrative_quality


class NarrativeQualityTests(unittest.TestCase):
    def write_chapter(
        self,
        book_folder: Path,
        slug: str,
        draft_text: str,
        scene_text: str,
        continuity_text: str,
    ) -> None:
        chapter_folder = book_folder / "chapters" / slug
        chapter_folder.mkdir(parents=True, exist_ok=True)
        (chapter_folder / f"{slug}.md").write_text(draft_text, encoding="utf-8")
        (chapter_folder / "scene-breakdown.md").write_text(scene_text, encoding="utf-8")
        (chapter_folder / "continuity-out.md").write_text(continuity_text, encoding="utf-8")

    def test_character_distinctiveness_uses_book_continuity_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            self.write_chapter(
                book_folder,
                "chapter-01",
                (
                    "Alden gripped the saddle and chose the creek trail. "
                    "Mara pulled the rope tight and kept watch by the door."
                ),
                (
                    "## BEAT 1\n"
                    "- Intent: alliance/strategy\n"
                    "- Required Story Movement: Alden and Mara choose the creek trail.\n"
                ),
                (
                    "## Characters\n"
                    "- Alden is alive.\n"
                    "- Mara is alive.\n"
                    "## Locations\n"
                    "- Creek trail.\n"
                    "## Changes\n"
                    "- Alden carries the risk of choosing the creek trail.\n"
                    "## Human Stakes Carried\n"
                    "- Alden: risk from the creek choice + must lead the next ride.\n"
                    "- Mara: pressure from the watch + must guard the door.\n"
                    "## Unresolved Pressure\n"
                    "- Riders may follow.\n"
                    "## Next Chapter Must Know\n"
                    "- Alden and Mara leave by the creek.\n"
                ),
            )

            messages = [issue.message for issue in narrative_quality.analyze(book_folder).issues]

            joined = "\n".join(messages)
            self.assertNotIn("Roberts", joined)
            self.assertNotIn("Thessaly", joined)
            self.assertNotIn("Barnabas", joined)
            self.assertNotIn("Eulalia", joined)

    def test_antagonist_overlap_warning_is_reachable(self):
        with patch(
            "bookforge.core.validator.load_project_settings",
            return_value={
                "narrative_quality": {
                    "antagonists": {
                        "first": {
                            "markers": ["first"],
                            "tactical_motifs": ["warrant", "ledger", "threat"],
                        },
                        "second": {
                            "markers": ["second"],
                            "tactical_motifs": ["warrant", "ledger", "threat", "trail"],
                        },
                    }
                }
            },
        ):
            issues: list[narrative_quality.NarrativeIssue] = []

            narrative_quality._check_antagonist_contrast(
                "chapter-01",
                "First used a warrant ledger threat. Second used a warrant ledger threat trail.",
                issues,
            )

        self.assertTrue(
            any("overlapping pressure posture" in issue.message for issue in issues)
        )


if __name__ == "__main__":
    unittest.main()
