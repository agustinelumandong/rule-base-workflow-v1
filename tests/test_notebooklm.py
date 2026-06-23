import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bookforge.core import notebooklm


class NotebookLMSystemTests(unittest.TestCase):
    @patch("shutil.which")
    def test_is_nlm_available(self, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        self.assertTrue(notebooklm.is_nlm_available())

        mock_which.return_value = None
        self.assertFalse(notebooklm.is_nlm_available())

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_get_auth_status(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        
        # Test authenticated success case
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Active session: test-user@gmail.com"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        status = notebooklm.get_auth_status()
        self.assertTrue(status["authenticated"])
        self.assertEqual(status["email"], "test-user@gmail.com")

        # Test authenticated success with "configured" word
        mock_proc.stdout = "configured - token valid"
        status = notebooklm.get_auth_status()
        self.assertTrue(status["authenticated"])

        # Test not authenticated
        mock_proc.returncode = 1
        mock_proc.stdout = "Not logged in"
        status = notebooklm.get_auth_status()
        self.assertFalse(status["authenticated"])

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_list_notebooks_json(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps([
            {"id": "uuid-1", "title": "Book 1 Research", "source_count": 4},
            {"notebook_id": "uuid-2", "name": "Book 2 Research", "sources": 10}
        ])
        mock_run.return_value = mock_proc

        notebooks = notebooklm.list_notebooks()
        self.assertEqual(len(notebooks), 2)
        self.assertEqual(notebooks[0]["id"], "uuid-1")
        self.assertEqual(notebooks[0]["title"], "Book 1 Research")
        self.assertEqual(notebooks[0]["sources"], "4")
        self.assertEqual(notebooks[1]["id"], "uuid-2")
        self.assertEqual(notebooks[1]["title"], "Book 2 Research")
        self.assertEqual(notebooks[1]["sources"], "10")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_list_notebooks_text_fallback(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = (
            "  * 12345678-abcd-1234-abcd-1234567890ab - Tex Cade Research (5 sources)\n"
            "  * 87654321-dcba-4321-dcba-ba0987654321 - Outlaws of West\n"
        )
        mock_run.return_value = mock_proc

        notebooks = notebooklm.list_notebooks()
        self.assertEqual(len(notebooks), 2)
        self.assertEqual(notebooks[0]["id"], "12345678-abcd-1234-abcd-1234567890ab")
        self.assertEqual(notebooks[0]["title"], "Tex Cade Research")
        self.assertEqual(notebooks[0]["sources"], "5")
        self.assertEqual(notebooks[1]["id"], "87654321-dcba-4321-dcba-ba0987654321")
        self.assertEqual(notebooks[1]["title"], "Outlaws of West")
        self.assertEqual(notebooks[1]["sources"], "0")

    def test_associated_notebook_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            
            # Initial state should be None
            self.assertIsNone(notebooklm.get_associated_notebook(folder))
            
            # Save associated notebook
            notebooklm.set_associated_notebook(folder, "my-notebook-uuid", "Western Adventures")
            
            # Retrieve associated notebook
            nb = notebooklm.get_associated_notebook(folder)
            self.assertIsNotNone(nb)
            self.assertEqual(nb["id"], "my-notebook-uuid")
            self.assertEqual(nb["title"], "Western Adventures")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_query_notebook(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "This is the answer from NotebookLM."
        mock_run.return_value = mock_proc

        res = notebooklm.query_notebook("uuid-123", "who is the protagonist?")
        self.assertEqual(res, "This is the answer from NotebookLM.")
        mock_run.assert_called_with(
            ["nlm", "notebook", "query", "uuid-123", "who is the protagonist?"],
            capture_output=True,
            text=True,
            check=False
        )

    @patch("bookforge.core.notebooklm.query_notebook")
    def test_sync_research_to_pack(self, mock_query):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            mock_query.return_value = "Key Facts:\n- Ranger Tex Cade is 34.\n- Ranger badge number is 402."

            success = notebooklm.sync_research_to_pack(folder, "uuid-456")
            self.assertTrue(success)

            pack_file = folder / "research-pack.md"
            self.assertTrue(pack_file.exists())
            content = pack_file.read_text(encoding="utf-8")
            self.assertIn("Ranger Tex Cade is 34", content)
            self.assertIn("uuid-456", content)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_upload_local_sources(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            
            # Create files
            (folder / "rulebook.md").write_text("Rule content", encoding="utf-8")
            (folder / "chapter-summaries.md").write_text("Summary content", encoding="utf-8")
            
            chap_dir = folder / "chapters" / "chapter-01"
            chap_dir.mkdir(parents=True)
            (chap_dir / "chapter-01.md").write_text("Chapter content", encoding="utf-8")

            uploaded = notebooklm.upload_local_sources(folder, "uuid-123")
            self.assertEqual(len(uploaded), 3)
            self.assertIn("rulebook.md", uploaded)
            self.assertIn("chapter-summaries.md", uploaded)
            self.assertIn("chapter-01.md", uploaded)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_create_new_notebook(self, mock_run, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        
        # Test JSON parsing
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"id": "new-notebook-uuid", "title": "My New Notebook"})
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        nb_id = notebooklm.create_new_notebook("My New Notebook")
        self.assertEqual(nb_id, "new-notebook-uuid")
        
        # Test fallback regex parsing
        mock_proc.stdout = "Created notebook: My New Notebook (UUID: 87654321-dcba-4321-dcba-ba0987654321)"
        mock_proc.stderr = ""
        nb_id = notebooklm.create_new_notebook("My New Notebook")
        self.assertEqual(nb_id, "87654321-dcba-4321-dcba-ba0987654321")


    @patch("shutil.which")
    @patch("bookforge.core.notebooklm.get_auth_status")
    @patch("bookforge.core.notebooklm.create_new_notebook")
    @patch("bookforge.core.notebooklm.query_notebook")
    @patch("subprocess.run")
    def test_generate_research_outline(self, mock_run, mock_query, mock_create, mock_auth, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        mock_auth.return_value = {"authenticated": True, "email": "test@gmail.com", "error": ""}
        mock_create.return_value = "new-uuid-999"
        
        # Mocking queries (query 1 for research_query, query 2 for generator_prompt)
        mock_query.side_effect = [
            "Authentic Western events",  # research query response
            """# Book Outline: Tex Cade: Texas Ranger - Book 3

## Overview
- Premise: Tex Cade hunts outlaws.

## Returning Characters

### Tex Cade (Protagonist)
- **Role:** POV protagonist.
- **Function:** Special attaché Ranger whose investigation drives the book's main conflict.
- **Profile:** `characters/main/tex-cade.md`
"""  # generator outline response
        ]
        
        # Mock subprocess run for source upload checks
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "books-3"
            folder.mkdir(parents=True)
            
            # Create a research-pack.md file in parent
            (folder.parent / "research-pack.md").write_text("Parent research", encoding="utf-8")
            
            success, msg = notebooklm.generate_research_outline(folder)
            self.assertTrue(success)
            self.assertIn("Successfully created notebook", msg)
            
            # Verify phase-0.md was written
            phase_0 = folder / "phase-0.md"
            self.assertTrue(phase_0.exists())
            self.assertIn("# Book Outline: Tex Cade: Texas Ranger - Book 3", phase_0.read_text(encoding="utf-8"))
            self.assertTrue((folder / "characters/main/tex-cade.md").exists())
            self.assertTrue((folder / "characters/cast-index.md").exists())

    @patch("shutil.which")
    @patch("bookforge.core.notebooklm.get_auth_status")
    @patch("bookforge.core.notebooklm.create_new_notebook")
    @patch("bookforge.core.notebooklm.query_notebook")
    @patch("subprocess.run")
    def test_generate_research_outline_respects_settings(self, mock_run, mock_query, mock_create, mock_auth, mock_which):
        mock_which.return_value = "/usr/local/bin/nlm"
        mock_auth.return_value = {"authenticated": True, "email": "test@gmail.com", "error": ""}
        mock_create.return_value = "new-uuid-999"
        mock_query.side_effect = [
            "Authentic Western events",  # research query response
            "# Book Outline: Tex Cade: Texas Ranger - Book 3"  # generator outline response
        ]
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "books-3"
            folder.mkdir(parents=True)
            
            # Write a settings.json file to temp directory
            (folder / "settings.json").write_text(
                json.dumps({
                    "name_policy": {
                        "allowed_names": ["voss"],
                        "banned_names": ["silas"]
                    }
                }),
                encoding="utf-8"
            )
            
            success, msg = notebooklm.generate_research_outline(folder)
            self.assertTrue(success)
            
            # Check the second query call args (which is the generator prompt)
            generator_prompt = mock_query.call_args_list[1][0][1]
            self.assertIn("The name \"Silas\"", generator_prompt)
            self.assertIn("The name \"Voss\"", generator_prompt)
            self.assertIn("## Returning Characters", generator_prompt)
            self.assertIn("Do not put full character profiles in phase-0.md", generator_prompt)




if __name__ == "__main__":
    unittest.main()
