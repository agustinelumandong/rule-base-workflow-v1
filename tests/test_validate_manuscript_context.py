import json
import tempfile
import unittest
from pathlib import Path

from bookforge.core import validator


def load_validator():
    # Legacy shims have been removed; return the canonical validator module.
    return validator


class ManuscriptContextValidatorTests(unittest.TestCase):
    def test_parse_phase_chapters_accepts_bold_chapter_lines(self):
        validator = load_validator()

        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text(
                """# Test Book

**Chapter 1: Traplines in the Thaw (~1,100 words)**
Jed checks beaver traps and spots strange smoke.

**Chapter 2: The Flood's Fury (~1,050 words)**
Flood wrecks Jed's canoe and breaks his leg.

### Epilogue: Threefingers' Shadow (~800 words)
Jed returns to the lines months later.
""",
                encoding="utf-8",
            )

            sections = validator.parse_phase_chapters(book_folder)

        self.assertIn("chapter-01", sections)
        self.assertIn("chapter-02", sections)
        self.assertIn("epilogue", sections)
        self.assertIn("beaver traps", sections["chapter-01"])
        self.assertIn("breaks his leg", sections["chapter-02"])
        self.assertIn("months later", sections["epilogue"])

    # ------------------------------------------------------------------
    # A4: -ing sentence opener detection
    # ------------------------------------------------------------------

    def test_ing_opener_detected(self):
        validator = load_validator()
        text = "Running toward the barn, Jed grabbed the post.\nHe checked the latch."
        samples = validator.check_ing_openers(text)
        self.assertTrue(len(samples) > 0, "Expected -ing opener to be detected")
        self.assertIn("Running", samples[0])

    def test_ing_opener_clean(self):
        validator = load_validator()
        text = "Jed grabbed the post.\nHe checked the latch.\nThe door held."
        samples = validator.check_ing_openers(text)
        self.assertEqual(samples, [], "Expected no -ing openers in clean prose")

    def test_ing_opener_excludes_short_words(self):
        """King, Ring, Sing should not trigger (less than 7 chars with -ing)."""
        validator = load_validator()
        text = "King walked into the saloon.\nRing the bell when done."
        samples = validator.check_ing_openers(text)
        self.assertEqual(samples, [], "Short -ing words like King should not be flagged")

    # ------------------------------------------------------------------
    # A5: pronoun/name sentence loop detection
    # ------------------------------------------------------------------

    def test_pronoun_loop_detected(self):
        validator = load_validator()
        text = (
            "He pulled the rifle from the scabbard. "
            "He checked the chamber. "
            "He stepped into the doorway."
        )
        findings = validator.check_pronoun_loops(text)
        self.assertTrue(len(findings) > 0, "Expected pronoun loop to be detected")
        self.assertIn("He", findings[0])

    def test_pronoun_loop_clean(self):
        validator = load_validator()
        text = (
            "He pulled the rifle. "
            "The barrel was cold. "
            "He checked the chamber."
        )
        findings = validator.check_pronoun_loops(text)
        self.assertEqual(findings, [], "Two consecutive same-starts should not trigger (need 3)")

    # ------------------------------------------------------------------
    # em-dash action anchor spacing detection
    # ------------------------------------------------------------------

    def test_em_dash_anchors_detected_incorrect_spacing(self):
        validator = load_validator()
        text = '"Get on the horse."—Harlan tightened the cinch.\n"Get on the horse." —  Harlan tightened.'
        warnings = validator.check_em_dash_anchors(text)
        self.assertTrue(len(warnings) > 0, "Expected spacing warnings to be detected")
        self.assertIn("Incorrect em-dash anchor spacing", warnings[0])

    def test_em_dash_anchors_detected_double_hyphen(self):
        validator = load_validator()
        text = '"Get on the horse." -- Harlan tightened the cinch.'
        warnings = validator.check_em_dash_anchors(text)
        self.assertTrue(len(warnings) > 0, "Expected double-hyphen warnings to be detected")
        self.assertIn("Use em-dash `—` instead of double-hyphen", warnings[0])

    def test_em_dash_anchors_clean(self):
        validator = load_validator()
        text = '"Get on the horse." — Harlan tightened the cinch.'
        warnings = validator.check_em_dash_anchors(text)
        self.assertEqual(warnings, [], "Expected no warnings for correct em-dash spacing")

    # ------------------------------------------------------------------
    # A6: UNKNOWN in context-lock fields
    # ------------------------------------------------------------------

    def test_context_lock_unknown_detected(self):
        validator = load_validator()
        scene_text = """## BEAT 1: Arrival

### Source Context Lock

- **Source Anchor:** UNKNOWN
- **Continuity In:** Jed is at camp.
- **Required Story Movement:** Jed spots the stranger.
- **Continuity Out:** Stranger location established.
- **Do Not Invent:** Names, locations.

### Beat Instructions

Write the scene.
"""
        findings = validator.check_context_lock_unknowns(scene_text)
        self.assertTrue(len(findings) > 0, "Expected UNKNOWN in Source Anchor to be detected")
        self.assertIn("Source Anchor", findings[0])

    def test_context_lock_no_unknowns(self):
        validator = load_validator()
        scene_text = """## BEAT 1: Arrival

### Source Context Lock

- **Source Anchor:** Phase-0, Chapter 1 — Jed checks trapline.
- **Continuity In:** Jed is at camp.
- **Required Story Movement:** Jed spots the stranger.
- **Continuity Out:** Stranger location established.
- **Do Not Invent:** Names, locations.

### Beat Instructions

Write the scene.
"""
        findings = validator.check_context_lock_unknowns(scene_text)
        self.assertEqual(findings, [], "Expected no findings in clean context-lock block")

    # ------------------------------------------------------------------
    # A2: continuity-out.md check
    # ------------------------------------------------------------------

    def test_continuity_out_missing_warns(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            chapter_folder = book_folder / "chapters" / "chapter-01"
            chapter_folder.mkdir(parents=True)
            draft = chapter_folder / "chapter-01.md"
            draft.write_text("Jed pulled the rifle from the scabbard.", encoding="utf-8")
            # No continuity-out.md created

            chapter_files = validator.ChapterFiles(
                slug="chapter-01",
                label="Chapter 01",
                folder=chapter_folder,
                draft=draft,
                scene_breakdown=chapter_folder / "scene-breakdown.md",
                drafting_plan=chapter_folder / "drafting-plan.md",
            )
            passes, warnings = validator.validate_continuity_out(chapter_files)

        self.assertTrue(len(warnings) > 0, "Expected WARN for missing continuity-out.md")
        self.assertIn("missing", warnings[0])

    def test_continuity_out_present_passes(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            chapter_folder = book_folder / "chapters" / "chapter-01"
            chapter_folder.mkdir(parents=True)
            draft = chapter_folder / "chapter-01.md"
            draft.write_text("Jed pulled the rifle from the scabbard.", encoding="utf-8")
            (chapter_folder / "continuity-out.md").write_text(
                "## Characters\nJed alive.\n## Locations\nCamp.\n"
                "## Changes\nNone.\n## Unresolved Pressure\nStranger seen.\n"
                "## Next Chapter Must Know\nJed at camp.",
                encoding="utf-8",
            )

            chapter_files = validator.ChapterFiles(
                slug="chapter-01",
                label="Chapter 01",
                folder=chapter_folder,
                draft=draft,
                scene_breakdown=chapter_folder / "scene-breakdown.md",
                drafting_plan=chapter_folder / "drafting-plan.md",
            )
            passes, warnings = validator.validate_continuity_out(chapter_files)

        self.assertEqual(warnings, [], "Expected no warnings when continuity-out.md is present")
        self.assertTrue(len(passes) > 0)

    # ------------------------------------------------------------------
    # Forbidden Conflict Themes check
    # ------------------------------------------------------------------

    def test_forbidden_conflicts_detected(self):
        validator = load_validator()
        text = "The syndicate controlled the water rights in the valley, leading to a massive land grab."
        findings = validator.check_forbidden_conflicts(text)
        self.assertEqual(len(findings), 3)
        findings_str = " ".join(findings)
        self.assertIn("syndicate", findings_str)
        self.assertIn("water rights", findings_str)
        self.assertIn("land grab", findings_str)

    def test_forbidden_conflicts_clean(self):
        validator = load_validator()
        text = "Jed chased the cattle rustlers across the state line, hunting the dangerous convict."
        findings = validator.check_forbidden_conflicts(text)
        self.assertEqual(findings, [])

    def test_forbidden_conflicts_voss_detected(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text("{}", encoding="utf-8")
            text = "Gideon Voss led his outlaw gang through the winter pass."
            findings = validator.check_forbidden_conflicts(text, root)
        self.assertEqual(len(findings), 1)
        self.assertIn("voss", findings[0])

    def test_forbidden_conflicts_loads_configured_banned_name(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps({"name_policy": {"banned_names": ["silas"], "allowed_names": []}}),
                encoding="utf-8",
            )

            findings = validator.check_forbidden_conflicts(
                "Silas rode with the counterfeit crew.",
                root / "books" / "active" / "chapters" / "chapter-01" / "chapter-01.md",
            )

        self.assertEqual(len(findings), 1)
        self.assertIn("Configured banned name 'silas'", findings[0])

    def test_allowed_names_do_not_bypass_project_rule_ban(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps({"name_policy": {"banned_names": ["voss"], "allowed_names": ["voss"]}}),
                encoding="utf-8",
            )

            findings = validator.check_forbidden_conflicts("Voss waited by the corral.", root)

        self.assertEqual(len(findings), 1)
        self.assertIn("voss", findings[0])

    def test_style_review_signals_are_soft_review_guidance(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_review": {
                            "enabled": True,
                            "max_summary_words_without_dialogue": 10,
                            "analysis_terms": ["realized"],
                            "formal_dialogue_terms": ["traverse"],
                            "time_jump_terms": ["hours later"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            text = (
                "Tex rode past the wash and realized the plan had turned bad. "
                "Dust covered the herd while the men kept moving without a word.\n\n"
                '"We traverse the ridge."\n\n'
                "Hours later, they reached camp."
            )

            findings = validator.check_style_review_signals(text, root)

        self.assertEqual(len(findings), 4)
        self.assertTrue(any("Long narrative-summary" in finding for finding in findings))
        self.assertTrue(any("Behavior-analysis" in finding for finding in findings))
        self.assertTrue(any("Formal dialogue" in finding for finding in findings))
        self.assertTrue(any("time-jump" in finding for finding in findings))

    def test_style_review_signals_banned_terms_and_short_sentences(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_review": {
                            "enabled": True,
                            "banned_terms": ["tactical position", "leverage"],
                            "warn_short_sentence_runs": True,
                        }
                    }
                ),
                encoding="utf-8",
            )
            text = (
                "Tex adjusted his tactical position. He had no leverage. "
                "No bodies. Alive when taken. That changed everything."
            )
            findings = validator.check_style_review_signals(text, root)

        self.assertEqual(len(findings), 2)
        self.assertTrue(any("Forbidden modern" in finding for finding in findings))
        self.assertTrue(any("Consecutive short sentence fragments" in finding for finding in findings))

    def test_style_review_signals_resolves_frontier_profile_from_rulebook(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_review": {
                            "enabled": True,
                            "banned_terms": [],
                        },
                        "style_profiles": {
                            "fallback_profile": "default",
                            "year_buckets": [
                                {
                                    "name": "frontier_1880s",
                                    "start": 1880,
                                    "end": 1899,
                                }
                            ],
                            "profiles": {
                                "frontier_1880s": {
                                    "style_review": {"banned_terms": ["reckon"]},
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "rulebook.md").write_text(
                "**Time Period:** Hard Winter of 1880-1881\n",
                encoding="utf-8",
            )
            findings = validator.check_style_review_signals(
                "He reckon this was the only way through.",
                root,
            )

        self.assertTrue(any("Forbidden modern" in finding for finding in findings), findings)

    def test_style_review_signals_falls_back_to_default_without_matching_year(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_review": {
                            "enabled": True,
                            "banned_terms": ["tactical position"],
                        },
                        "style_profiles": {
                            "fallback_profile": "default",
                            "year_buckets": [
                                {
                                    "name": "frontier_1880s",
                                    "start": 1880,
                                    "end": 1899,
                                }
                            ],
                            "profiles": {
                                "default": {},
                                "frontier_1880s": {
                                    "style_review": {"banned_terms": ["reckon"]},
                                },
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            findings = validator.check_style_review_signals(
                "He was moved by tactical position and grit.",
                root,
            )

        self.assertTrue(any("Forbidden modern" in finding for finding in findings), findings)
        self.assertFalse(any("reckon" in finding.lower() for finding in findings), findings)

    def test_style_review_signals_malformed_profile_config_falls_back(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_review": {
                            "enabled": True,
                            "banned_terms": ["move fast"],
                        },
                        "style_profiles": {
                            "fallback_profile": "default",
                            "year_buckets": "bad",
                            "profiles": "broken",
                        },
                    }
                ),
                encoding="utf-8",
            )
            findings = validator.check_style_review_signals(
                "Move fast and leave no trail.",
                root,
            )

        self.assertTrue(any("Forbidden modern" in finding for finding in findings), findings)

    def test_historical_terms_support_severity_buckets(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory(dir=".") as tmp:
            root = Path(tmp)
            (root / "settings.json").write_text(
                json.dumps(
                    {
                        "style_review": {"enabled": True},
                        "historical_terms": {
                            "banned": ["cost center"],
                            "warn": ["signature page"],
                            "context_required": ["mortgage lien"],
                            "review_only": ["custody"],
                        },
                    }
                ),
                encoding="utf-8",
            )

            findings = validator.check_style_review_signals(
                "That cost center hid the mortgage lien. The signature page put him in custody.",
                root,
            )

        self.assertTrue(any("Banned historical/style terms" in finding for finding in findings), findings)
        self.assertTrue(any("Warn historical/style terms" in finding for finding in findings), findings)
        self.assertTrue(any("Context-required historical/style terms" in finding for finding in findings), findings)
        self.assertTrue(any("Review-only historical/style terms" in finding for finding in findings), findings)

    def test_repeated_sentence_copy_paste_detected(self):
        validator = load_validator()
        text = (
            "Draven backed his horse away from the fire. "
            "The riders held the ridge. "
            "Draven backed his horse away from the fire."
        )

        findings = validator.check_repeated_sentence_duplicates(text)

        self.assertEqual(len(findings), 1)
        self.assertIn("Draven backed his horse away", findings[0])

    def test_repeated_sentence_copy_paste_ignores_tiny_sentences(self):
        validator = load_validator()
        findings = validator.check_repeated_sentence_duplicates("No. No. No.")

        self.assertEqual(findings, [])

    def test_plot_mode_risk_requires_rulebook_ban_context(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory(dir=".") as tmp:
            book_folder = Path(tmp)
            (book_folder / "settings.json").write_text(
                json.dumps(
                    {
                        "plot_mode_review": {
                            "enabled": True,
                            "legal_procedure_threshold": 4,
                            "legal_procedure_terms": ["court", "hearing", "writ", "mortgage"],
                            "ban_markers": ["no courtroom"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            (book_folder / "rulebook.md").write_text(
                "## Hard Story Guardrails\n- No courtroom or trial sequence.\n",
                encoding="utf-8",
            )

            findings = validator.check_plot_mode_risk(
                "The court set a hearing after the writ named the mortgage.",
                book_folder,
            )

        self.assertEqual(len(findings), 1)
        self.assertIn("legal-procedure plot mode", findings[0])

    def test_plot_mode_risk_does_not_warn_without_rulebook_ban(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory(dir=".") as tmp:
            book_folder = Path(tmp)
            (book_folder / "settings.json").write_text(
                json.dumps(
                    {
                        "plot_mode_review": {
                            "enabled": True,
                            "legal_procedure_threshold": 2,
                            "legal_procedure_terms": ["court", "hearing"],
                            "ban_markers": ["no courtroom"],
                        }
                    }
                ),
                encoding="utf-8",
            )
            (book_folder / "rulebook.md").write_text(
                "## Hard Story Guardrails\n- Court pressure is source-approved.\n",
                encoding="utf-8",
            )

            findings = validator.check_plot_mode_risk("The court set a hearing.", book_folder)

        self.assertEqual(findings, [])

    def test_validate_draft_emits_soft_copy_paste_and_plot_mode_warnings(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory(dir=".") as tmp:
            book_folder = Path(tmp)
            (book_folder / "settings.json").write_text(
                json.dumps(
                    {
                        "style_review": {"enabled": False},
                        "plot_mode_review": {
                            "enabled": True,
                            "legal_procedure_threshold": 3,
                            "legal_procedure_terms": ["court", "hearing", "writ"],
                            "ban_markers": ["no courtroom"],
                        },
                    }
                ),
                encoding="utf-8",
            )
            (book_folder / "rulebook.md").write_text("- No courtroom or trial sequence.", encoding="utf-8")
            chapter_folder = book_folder / "chapters" / "chapter-01"
            chapter_folder.mkdir(parents=True)
            draft = chapter_folder / "chapter-01.md"
            draft.write_text(
                "The court set a hearing under the writ. "
                "Draven backed his horse away from the fire. "
                "Draven backed his horse away from the fire.",
                encoding="utf-8",
            )

            issues = validator.validate_draft(
                validator.ChapterFiles(
                    slug="chapter-01",
                    label="Chapter 01",
                    folder=chapter_folder,
                    draft=draft,
                    scene_breakdown=chapter_folder / "scene-breakdown.md",
                    drafting_plan=chapter_folder / "drafting-plan.md",
                )
            )

        self.assertTrue(any(issue.rule_id == "VALIDATOR_REPEATED_PROSE" for issue in issues), issues)
        self.assertTrue(any(issue.rule_id == "VALIDATOR_PLOT_MODE_RISK" for issue in issues), issues)

    # ------------------------------------------------------------------
    # Rulebook contract checks
    # ------------------------------------------------------------------

    def test_rulebook_sections_and_allowed_unknowns_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "mood-lock.md").write_text("## Mood", encoding="utf-8")
            (book_folder / "chapter-summaries.md").write_text("## Summary", encoding="utf-8")
            (book_folder / "rulebook.md").write_text(
                """# Rulebook

## Source Hierarchy
- phase-0

## Length Handling Rules
- Book-level guidance only.

## Do Not Invent
- Keep source-locked.

## Characters
### Tex
- POV Rules: UNKNOWN

## Chapter Continuity Ledger

### Chapter 1: Open
- Required Story Movement: Arrive.

### Epilogue
- Required Story Movement: End.

## Unknowns
None.
""",
                encoding="utf-8",
            )
            (book_folder / "phase-0.md").write_text(
                """# Source

**Chapter 1: Open**
Text.

**Epilogue: End**
Text.
""",
                encoding="utf-8",
            )

            _, failures = validator.validate_required_book_files(book_folder)

        self.assertEqual(failures, [])

    def test_unknown_markers_restricted_to_allowed_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "mood-lock.md").write_text("## Mood", encoding="utf-8")
            (book_folder / "chapter-summaries.md").write_text("## Summary", encoding="utf-8")
            (book_folder / "rulebook.md").write_text(
                """# Rulebook

## Source Hierarchy
- phase-0

## Length Handling Rules
- Book-level guidance only.

## Do Not Invent
- UNKNOWN policy note.

## Characters
### Tex
- POV Rules: UNKNOWN

## Chapter Continuity Ledger
### Chapter 1: Open
- Required Story Movement: Arrive.

### Epilogue
- Required Story Movement: End.

## Unknowns
- Storekeeper identity.
""",
                encoding="utf-8",
            )
            (book_folder / "phase-0.md").write_text(
                """# Source

**Chapter 1: Open**
Text.

**Epilogue: End**
Text.
""",
                encoding="utf-8",
            )

            _, failures = validator.validate_required_book_files(book_folder)

        self.assertTrue(
            any("Rulebook marker policy violation" in item for item in failures),
            failures,
        )

    def test_continuity_ledger_warns_missing_epilogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "mood-lock.md").write_text("## Mood", encoding="utf-8")
            (book_folder / "chapter-summaries.md").write_text("## Summary", encoding="utf-8")
            (book_folder / "rulebook.md").write_text(
                """# Rulebook

## Source Hierarchy
- phase-0

## Length Handling Rules
- Book-level guidance only.

## Do Not Invent
- Keep source-locked.

## Characters
- Tex

## Chapter Continuity Ledger

### Chapter 1: Open
- Required Story Movement: Arrive.

## Unknowns
- Storekeeper identity.
""",
                encoding="utf-8",
            )
            (book_folder / "phase-0.md").write_text(
                """# Source

**Chapter 1: Open**
Text.

**Epilogue: End**
Text.
""",
                encoding="utf-8",
            )

            _, failures = validator.validate_required_book_files(book_folder)

        self.assertTrue(
            any("epilogue" in item.lower() for item in failures),
            failures,
        )

    def test_outline_life_state_contradiction_warns_for_killed_then_treated_person(self):
        with tempfile.TemporaryDirectory(dir=".") as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text(
                """# Source

Chapter 7: Night Guard
One hired hand is killed under the herd.

Chapter 9: Buyer Doubt
Eleanor treats the injured hired hand from the stampede and hears him name Broken Brand Draw.
""",
                encoding="utf-8",
            )
            (book_folder / "mood-lock.md").write_text("## Mood", encoding="utf-8")
            (book_folder / "chapter-summaries.md").write_text("## Summary", encoding="utf-8")
            (book_folder / "rulebook.md").write_text(
                """# Rulebook

## Source Hierarchy
- phase-0

## Length Handling Rules
- Book-level guidance only.

## Do Not Invent
- Keep source-locked.

## Characters
- Eleanor

## Chapter Continuity Ledger
### Chapter 7
- Required Story Movement: Stampede.
### Chapter 9
- Required Story Movement: Buyer doubt.

## Unknowns
None.
""",
                encoding="utf-8",
            )

            issues = validator.validate_required_book_file_issues(book_folder)

        self.assertTrue(
            any(issue.rule_id == "VALIDATOR_OUTLINE_LIFE_STATE_CONTRADICTION" for issue in issues),
            issues,
        )

    def test_direct_rulebook_edit_deprecated(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text("# Outline\n**Chapter 1**\nText", encoding="utf-8")
            (book_folder / "rulebook.md").write_text("# Series Continuity\n## Chapter Continuity Ledger\n### chapter-01\nText\n", encoding="utf-8")
            
            import subprocess
            original_run = subprocess.run
            
            def mock_run(cmd, *args, **kwargs):
                if len(cmd) > 2 and cmd[0] == "git" and cmd[1] == "status":
                    class MockCompletedProcess:
                        stdout = "M rulebook.md\n"
                        stderr = ""
                        returncode = 0
                    return MockCompletedProcess()
                return original_run(cmd, *args, **kwargs)
                
            subprocess.run = mock_run
            try:
                issues = validator.validate_required_book_file_issues(book_folder)
                self.assertTrue(
                    any(issue.rule_id == "VALIDATOR_DIRECT_RULEBOOK_EDIT_DEPRECATED" for issue in issues),
                    "Expected deprecation issue to be raised when rulebook.md is modified in git"
                )
            finally:
                subprocess.run = original_run

    def test_simile_and_metaphor_detection(self):
        validator = load_validator()
        # Test simile/metaphor warning triggers
        text_simile_1 = "The name lay on the paper like an old bloodstain."
        text_simile_2 = "Pain stretches hours out like wet rawhide."
        text_simile_3 = "He looked as if he had seen a ghost."
        
        # Non-simile patterns that should not trigger
        text_clean = "I would like to go. I feel like it is cold. He looks like his father."
        
        findings_simile_1 = validator.check_similes_and_metaphors(text_simile_1)
        findings_simile_2 = validator.check_similes_and_metaphors(text_simile_2)
        findings_simile_3 = validator.check_similes_and_metaphors(text_simile_3)
        findings_clean = validator.check_similes_and_metaphors(text_clean)
        
        self.assertTrue(len(findings_simile_1) > 0, "Expected simile 1 to trigger")
        self.assertTrue(len(findings_simile_2) > 0, "Expected simile 2 to trigger")
        self.assertTrue(len(findings_simile_3) > 0, "Expected simile 3 to trigger")
        self.assertEqual(findings_clean, [], "Expected clean text not to trigger simile warning")

    def test_personification_detection(self):
        validator = load_validator()
        # Personification of inanimate object triggers
        text_personification_1 = "The land did not speak like men wanted it to."
        text_personification_2 = "The night moved around them."
        text_personification_3 = "Wonder wasted room."
        
        # Weapon metaphor triggers
        text_weapon_metaphor = "The Colt was a warning."
        
        # Non-personification patterns
        text_clean = "The horse moved across the creek. Jed spoke to Harlan."
        
        findings_1 = validator.check_personification_of_objects(text_personification_1)
        findings_2 = validator.check_personification_of_objects(text_personification_2)
        findings_3 = validator.check_personification_of_objects(text_personification_3)
        findings_weapon = validator.check_personification_of_objects(text_weapon_metaphor)
        findings_clean = validator.check_personification_of_objects(text_clean)
        
        self.assertTrue(len(findings_1) > 0, "Expected land speaking to trigger")
        self.assertTrue(len(findings_2) > 0, "Expected night moving to trigger")
        self.assertTrue(len(findings_3) > 0, "Expected wonder wasting to trigger")
        self.assertTrue(len(findings_weapon) > 0, "Expected Colt warning metaphor to trigger")
        self.assertEqual(findings_clean, [], "Expected clean text not to trigger personification warning")

    def test_abstract_internalization_detection(self):
        validator = load_validator()
        # Abstract internalization triggers
        text_internal_1 = "He had known the question would come."
        text_internal_2 = "Branton did not wonder long."
        text_internal_3 = "Eleanor believed the storm was passing."
        
        # Dialogue should be ignored
        text_dialogue = '"I believed you," Jed said.'
        
        # Non-internalization patterns
        text_clean = "Jed walked to the barn. He grabbed the post."
        
        findings_1 = validator.check_abstract_internalization(text_internal_1)
        findings_2 = validator.check_abstract_internalization(text_internal_2)
        findings_3 = validator.check_abstract_internalization(text_internal_3)
        findings_dialogue = validator.check_abstract_internalization(text_dialogue)
        findings_clean = validator.check_abstract_internalization(text_clean)
        
        self.assertTrue(len(findings_1) > 0, "Expected he had known to trigger")
        self.assertTrue(len(findings_2) > 0, "Expected did not wonder to trigger")
        self.assertTrue(len(findings_3) > 0, "Expected Eleanor believed to trigger")
        self.assertEqual(findings_dialogue, [], "Expected dialogue containing believed to be ignored")
        self.assertEqual(findings_clean, [], "Expected clean text not to trigger internalization warning")


if __name__ == "__main__":
    unittest.main()
