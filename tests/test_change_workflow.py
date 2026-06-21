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
    (book_dir / "canon" / "entities").mkdir(parents=True)
    (book_dir / "chapters").mkdir()

    # Write a phase-0 outline (chapter discovery source)
    (book_dir / "phase-0.md").write_text(
        "# Outline\n\n## Chapter 01\nThis is the first chapter.\n",
        encoding="utf-8",
    )

    # Required book files
    (book_dir / "mood-lock.md").write_text("# Mood Lock\n\nClassic Western style.", encoding="utf-8")
    (book_dir / "chapter-summaries.md").write_text(
        "# Chapter Summaries\n\n## Chapter 01\nSummary of chapter 1.",
        encoding="utf-8",
    )

    # A rulebook that satisfies every REQUIRED_RULEBOOK_SECTIONS check, including
    # a Chapter Continuity Ledger entry for chapter-01.
    (book_dir / "rulebook.md").write_text(
        "# Rulebook\n\n"
        "## Source Hierarchy\n\nOutline is the source of truth.\n\n"
        "## Length Handling Rules\n\nNo forbidden length language in drafts.\n\n"
        "## Do Not Invent\n\nDo not invent weapon or place names.\n\n"
        "## Chapter Continuity Ledger\n\n### Chapter 01\nHarlan rides to Ridge.\n\n"
        "## Unknowns\n\nNo unresolved markers.\n\n"
        "## Characters\n\n### Harlan\nDrifter. Iron, leather, dirt.\n",
        encoding="utf-8",
    )

    # Durable canon entities. The fold engine reads these to seed snapshot state;
    # events only mutate what entities declare. Characters/locations are keyed by id.
    (book_dir / "canon" / "entities" / "characters.yml").write_text(
        "characters:\n"
        "  harlan:\n"
        "    canonical: \"Harlan\"\n"
        "    tier: main\n"
        "    role: protagonist\n",
        encoding="utf-8",
    )
    (book_dir / "canon" / "entities" / "locations.yml").write_text(
        "locations:\n"
        "  ridge:\n"
        "    canonical: \"Ridge\"\n",
        encoding="utf-8",
    )

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

    # A valid scene breakdown: has a `## BEAT 1` plus the two required markers
    # (### Source Context Lock, ### Beat Instructions). No [COMBAT] tag, so the
    # gate does not require an action-plan JSON.
    proposal_text = (
        "# Scene Breakdown\n\n"
        "## Scene 1\nRide to the ridge.\n\n"
        "## BEAT 1: Approach\n\n"
        "### Source Context Lock\nHarlan on the trail.\n\n"
        "### Beat Instructions\nHarlan rides to Ridge.\n"
    )
    beats_text = "# Drafting Plan\n\n## BEAT 1\nFirst beat.\n"
    draft_text = "This is draft prose.\n"

    (staging_dir / "proposal.md").write_text(proposal_text, encoding="utf-8")
    (staging_dir / "beats.md").write_text(beats_text, encoding="utf-8")
    (staging_dir / "draft.md").write_text(draft_text, encoding="utf-8")
    # continuity-out carries a structured character_mutation event: Harlan moves
    # to ridge. This is one of the event types the fold engine actually applies.
    (staging_dir / "continuity-out.md").write_text(
        "# Continuity Out\n\n"
        "```yaml\n"
        "events:\n"
        "  - type: character_mutation\n"
        "    character_id: harlan\n"
        "    location: ridge\n"
        "```\n",
        encoding="utf-8",
    )

    # Run bf apply change chapter-01 via CLI
    monkeypatch.setattr(sys, "argv", ["bookforge", "apply", "change", str(temp_book_with_canon), "chapter-01"])
    assert main() == 0

    # Verify canonical files are compiled
    canon_chapter_dir = temp_book_with_canon / "chapters" / "chapter-01"
    assert canon_chapter_dir.exists()
    assert (canon_chapter_dir / "chapter-01.md").read_text(encoding="utf-8") == draft_text
    assert (canon_chapter_dir / "scene-breakdown.md").read_text(encoding="utf-8") == proposal_text
    assert (canon_chapter_dir / "drafting-plan.md").read_text(encoding="utf-8") == beats_text
    assert (canon_chapter_dir / "continuity-out.md").exists()

    # Verify event appended to canon
    event_file = temp_book_with_canon / "canon" / "events" / "chapter-01.event.yml"
    assert event_file.exists()

    # Verify snapshot re-folded: harlan's location is ridge, and ridge lists
    # harlan as an occupant (the fold's real output schema).
    import yaml
    snapshot = yaml.safe_load((temp_book_with_canon / "canon" / "state" / "snapshot.yml").read_text(encoding="utf-8"))
    assert snapshot["characters"]["harlan"]["location"] == "ridge"
    assert "harlan" in snapshot["locations"]["ridge"]["occupants"]

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
