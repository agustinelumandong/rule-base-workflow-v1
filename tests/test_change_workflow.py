import pytest
import shutil
from pathlib import Path
from bookforge.core.validators.format import ChapterFiles, discover_chapters
from bookforge.cli import main
import sys

@pytest.fixture
def temp_book_with_canon(tmp_path):
    book_dir = tmp_path / "book-test"
    book_dir.mkdir()

    # Create canon directory structure
    (book_dir / "canon" / "events").mkdir(parents=True)
    (book_dir / "canon" / "state").mkdir(parents=True)
    (book_dir / "chapters").mkdir()
    
    # Save a minimal rules/characters file so validation doesn't fail on missing configs
    (book_dir / "rulebook.md").write_text("# Rulebook\n\nNo syndicates.", encoding="utf-8")
    (book_dir / "mood-lock.md").write_text("# Mood Lock\n\nClassic Western style.", encoding="utf-8")
    (book_dir / "chapter-summaries.md").write_text("# Chapter Summaries\n\n## Chapter 01\nSummary of chapter 1.", encoding="utf-8")
    
    # Write a phase-0 outline
    (book_dir / "phase-0.md").write_text("# Outline\n\n## Chapter 01\nThis is the first chapter.", encoding="utf-8")

    # Initial canon state snapshot.yml
    (book_dir / "canon" / "state" / "snapshot.yml").write_text("""
characters:
  Harlan:
    status: alive
    injuries: []
locations:
  Ridge:
    visited: false
objects: {}
""", encoding="utf-8")

    return book_dir


def test_chapter_files_alternate_resolution(temp_book_with_canon):
    # Setup staging folder changes/chapter-01/
    staging_dir = temp_book_with_canon / "changes" / "chapter-01"
    staging_dir.mkdir(parents=True)

    proposal = staging_dir / "proposal.md"
    proposal.write_text("# Scene Breakdown\n\n## Scene 1 [COMBAT]\nCombat scene.", encoding="utf-8")
    
    beats = staging_dir / "beats.md"
    beats.write_text("# Drafting Plan\n\n## BEAT 1\nFirst beat.", encoding="utf-8")
    
    draft = staging_dir / "draft.md"
    draft.write_text("This is draft prose.", encoding="utf-8")

    # Test ChapterFiles constructor resolution
    ch_files = ChapterFiles(staging_dir)
    assert ch_files.slug == "chapter-01"
    assert ch_files.scene_breakdown == proposal
    assert ch_files.drafting_plan == beats
    assert ch_files.draft == draft


def test_discover_chapters_prioritization(temp_book_with_canon):
    # Setup staging folder changes/chapter-01/
    staging_dir = temp_book_with_canon / "changes" / "chapter-01"
    staging_dir.mkdir(parents=True)
    
    # Setup canonical chapters/chapter-01/
    canonical_dir = temp_book_with_canon / "chapters" / "chapter-01"
    canonical_dir.mkdir(parents=True)
    
    # discover_chapters should prefer the folder under changes/
    ch_list = discover_chapters(temp_book_with_canon)
    assert len(ch_list) == 1
    assert ch_list[0].slug == "chapter-01"
    assert "changes" in ch_list[0].folder.parts
    assert "chapters" not in ch_list[0].folder.parts


def test_apply_change_success(temp_book_with_canon, monkeypatch):
    # Setup staging folder changes/chapter-01/
    staging_dir = temp_book_with_canon / "changes" / "chapter-01"
    staging_dir.mkdir(parents=True)

    (staging_dir / "proposal.md").write_text("# Scene Breakdown\n\n## Scene 1 [COMBAT]\nCombat scene.", encoding="utf-8")
    (staging_dir / "beats.md").write_text("# Drafting Plan\n\n## BEAT 1\nFirst beat.", encoding="utf-8")
    (staging_dir / "draft.md").write_text("This is draft prose.", encoding="utf-8")
    (staging_dir / "continuity-out.md").write_text("""
# Continuity Out

```yaml
events:
  - type: visit_location
    actor: Harlan
    location: Ridge
```
""", encoding="utf-8")

    # Run bf apply change chapter-01 via CLI
    monkeypatch.setattr(sys, "argv", ["bookforge", "apply", "change", str(temp_book_with_canon), "chapter-01"])
    assert main() == 0

    # Verify canonical files are compiled
    canon_chapter_dir = temp_book_with_canon / "chapters" / "chapter-01"
    assert canon_chapter_dir.exists()
    assert (canon_chapter_dir / "chapter-01.md").read_text(encoding="utf-8") == "This is draft prose."
    assert (canon_chapter_dir / "scene-breakdown.md").read_text(encoding="utf-8") == "# Scene Breakdown\n\n## Scene 1 [COMBAT]\nCombat scene."
    assert (canon_chapter_dir / "drafting-plan.md").read_text(encoding="utf-8") == "# Drafting Plan\n\n## BEAT 1\nFirst beat."
    assert (canon_chapter_dir / "continuity-out.md").exists()

    # Verify event appended to canon
    event_file = temp_book_with_canon / "canon" / "events" / "chapter-01.event.yml"
    assert event_file.exists()
    
    # Verify snapshot re-folded
    import yaml
    snapshot = yaml.safe_load((temp_book_with_canon / "canon" / "state" / "snapshot.yml").read_text(encoding="utf-8"))
    assert snapshot["locations"]["Ridge"]["visited"] is True

    # Verify staging folder is archived
    assert not staging_dir.exists()
    assert (temp_book_with_canon / ".bookforge" / "archive" / "changes" / "chapter-01").exists()


def test_apply_change_validation_failure(temp_book_with_canon, monkeypatch):
    # Setup staging folder changes/chapter-01/
    staging_dir = temp_book_with_canon / "changes" / "chapter-01"
    staging_dir.mkdir(parents=True)

    # Missing proposal/beats/draft, which will trigger validation errors
    # Write a bad continuity-out file
    (staging_dir / "continuity-out.md").write_text("invalid content", encoding="utf-8")

    # Run bf apply change chapter-01 via CLI
    monkeypatch.setattr(sys, "argv", ["bookforge", "apply", "change", str(temp_book_with_canon), "chapter-01"])
    # Validation fails so command returns 1
    assert main() == 1

    # Verify staging folder remains intact and NOT compiled
    assert staging_dir.exists()
    assert not (temp_book_with_canon / "chapters" / "chapter-01").exists()
