import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from bookforge.core import validator


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "manuscript-workflow-orchestrator"
    / "scripts"
    / "validate_manuscript_context.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_manuscript_context", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ManuscriptContextValidatorTests(unittest.TestCase):
    def test_validate_chapter_fails_when_compiled_draft_missing_chapter_review(self):
        validator = load_validator()

        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            chapter_folder = book_folder / "chapters" / "chapter-01"
            chapter_folder.mkdir(parents=True)

            (book_folder / "phase-0.md").write_text(
                "# Test Book\n\n## Chapter 1\nJed claims the cabin and decides to stay.\n",
                encoding="utf-8",
            )
            (book_folder / "rulebook.md").write_text(
                "# Rulebook\n\n## Source Hierarchy\nphase-0.md\n\n## Length Handling Rules\nBook-level only.\n\n## Do Not Invent\nNo new visitors.\n\n## Characters\nJed.\n\n## Chapter Continuity Ledger\n### Chapter 1\n- Arrive.\n\n## Unknowns\nNone.\n",
                encoding="utf-8",
            )
            (book_folder / "mood-lock.md").write_text("# Mood Lock\n", encoding="utf-8")
            (book_folder / "chapter-summaries.md").write_text("## Chapter 1\nJed claims the cabin.\n", encoding="utf-8")
            (chapter_folder / "chapter-01.md").write_text(
                "Jed shouldered the bar into place.\n\nHe checked the roof poles and stayed inside till dark.\n",
                encoding="utf-8",
            )
            (chapter_folder / "drafting-plan.md").write_text("# Drafting Plan\n\n## BEAT 1\nClaim the cabin.\n", encoding="utf-8")
            (chapter_folder / "scene-breakdown.md").write_text(
                """## BEAT 1: Claim the Cabin

### Source Context Lock

- **Source Anchor:** Chapter 1 cabin claim.
- **Continuity In:** Jed is alone.
- **Required Story Movement:** Jed secures the cabin and commits to staying.
- **Continuity Out:** Cabin is now his shelter.
- **Do Not Invent:** Extra visitors or attacks.

### Beat Instructions

Write the scene.
""",
                encoding="utf-8",
            )
            (chapter_folder / "continuity-out.md").write_text(
                "## Characters\nJed alive.\n## Locations\nCabin.\n## Changes\nCabin claimed.\n## Unresolved Pressure\nWinter close.\n## Next Chapter Must Know\nJed stays.\n",
                encoding="utf-8",
            )

            chapter_files = validator.ChapterFiles(chapter_folder)
            report = validator.validate_chapter(chapter_files, {"chapter-01": "Jed claims the cabin and decides to stay."})

        self.assertTrue(any("chapter-review" in failure for failure in report.failures))

    def test_validate_chapter_fails_on_underdeveloped_money_beat(self):
        validator = load_validator()

        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            chapter_folder = book_folder / "chapters" / "chapter-01"
            chapter_folder.mkdir(parents=True)

            (book_folder / "phase-0.md").write_text(
                "# Test Book\n\n## Chapter 1\nJed reaches the cabin and finally understands he is home.\n",
                encoding="utf-8",
            )
            (book_folder / "rulebook.md").write_text(
                "# Rulebook\n\n## Source Hierarchy\nphase-0.md\n\n## Length Handling Rules\nBook-level only.\n\n## Do Not Invent\nNo new visitors.\n\n## Characters\nJed.\n\n## Chapter Continuity Ledger\n### Chapter 1\n- Arrive.\n\n## Unknowns\nNone.\n",
                encoding="utf-8",
            )
            (book_folder / "mood-lock.md").write_text("# Mood Lock\n", encoding="utf-8")
            (book_folder / "chapter-summaries.md").write_text("## Chapter 1\nJed reaches the cabin.\n", encoding="utf-8")
            (chapter_folder / "chapter-01.md").write_text(
                "Jed opened the cabin door.\n\nHe saw the dry hearth and knew it would do.\n",
                encoding="utf-8",
            )
            (chapter_folder / "drafting-plan.md").write_text("# Drafting Plan\n\n## BEAT 1\nReach the cabin.\n", encoding="utf-8")
            (chapter_folder / "scene-breakdown.md").write_text(
                """## BEAT 1: Home at Last

### Source Context Lock

- **Source Anchor:** Chapter 1 cabin arrival.
- **Continuity In:** Jed has survived the trail.
- **Required Story Movement:** Jed accepts the cabin as home.
- **Continuity Out:** He stays and prepares to winter there.
- **Do Not Invent:** New enemies or helpers.

### Pacing Guidance

- **Beat Weight:** money
- **Beat Development Floor:** >= 180 words
- **Why This Beat Matters:** This is the chapter's emotional payoff.

### Beat Instructions

Write the scene.
""",
                encoding="utf-8",
            )
            (chapter_folder / "chapter-review.md").write_text(
                "# Chapter Review\n\n## Read-Through Notes\nBrief note.\n\n## Slow Spots\nNone.\n\n## Rushed Spots\nEnding lands too fast.\n\n## Break Opportunities\nNone.\n\n## Decision\nready\n",
                encoding="utf-8",
            )
            (chapter_folder / "continuity-out.md").write_text(
                "## Characters\nJed alive.\n## Locations\nCabin.\n## Changes\nJed stays.\n## Unresolved Pressure\nWinter close.\n## Next Chapter Must Know\nCabin is home.\n",
                encoding="utf-8",
            )

            chapter_files = validator.ChapterFiles(chapter_folder)
            report = validator.validate_chapter(chapter_files, {"chapter-01": "Jed reaches the cabin and finally understands he is home."})

        self.assertTrue(any("underdeveloped" in failure.lower() for failure in report.failures))

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

        self.assertEqual(len(findings), 5)
        self.assertTrue(any("Long narrative-summary" in finding for finding in findings))
        self.assertTrue(any("Behavior-analysis" in finding for finding in findings))
        self.assertTrue(any("Thought-over-behavior narration" in finding for finding in findings))
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

        self.assertGreaterEqual(len(findings), 2)
        self.assertTrue(any("Forbidden modern" in finding for finding in findings))
        self.assertTrue(any("Consecutive short sentence fragments" in finding for finding in findings))

    def test_thought_over_behavior_narration_detection(self):
        validator = load_validator()
        text = (
            "The youngest boys watched him from farther off. "
            "That mattered too.\n\n"
            "Respect showed itself in the way the men quit shoving his shoulder.\n\n"
            "None of it made trust. It made use."
        )

        findings = validator.check_thought_over_behavior_narration(text)

        self.assertEqual(len(findings), 4)
        self.assertTrue(all("Thought-over-behavior narration" in finding for finding in findings))

    def test_thought_over_behavior_narration_honors_config(self):
        validator = load_validator()
        text = "That mattered. That counted. That meant the camp had changed. Careful was worth more."

        disabled = validator.check_thought_over_behavior_narration(
            text,
            {"enabled": False, "max_findings": 2},
        )
        limited = validator.check_thought_over_behavior_narration(
            text,
            {"enabled": True, "max_findings": 2},
        )

        self.assertEqual(disabled, [])
        self.assertEqual(len(limited), 2)

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
                            "year_buckets": [{"name": "frontier_1880s", "start": 1880, "end": 1899}],
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
            (root / "rulebook.md").write_text("**Time Period:** Hard Winter of 1880-1881\n", encoding="utf-8")
            findings = validator.check_style_review_signals(
                "He reckon this was the only way through.",
                root,
            )

        self.assertTrue(any("Forbidden modern" in finding for finding in findings), findings)

    def test_historical_terms_support_severity_buckets(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
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

    def test_plot_mode_risk_requires_rulebook_ban_context(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
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

    def test_validate_draft_emits_soft_copy_paste_and_plot_mode_warnings(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
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
            chapter = validator.ChapterFiles(chapter_folder)

            issues = validator.validate_draft(chapter)

        rule_ids = {issue.rule_id for issue in issues}
        self.assertIn("VALIDATOR_REPEATED_PROSE", rule_ids)
        self.assertIn("VALIDATOR_PLOT_MODE_RISK", rule_ids)

    def test_outline_life_state_contradiction_warns_for_killed_then_treated_person(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            book_folder = Path(tmp)
            (book_folder / "phase-0.md").write_text(
                "# Book\n\nOne wounded ranch hand is killed in the crossfire.\n\nLater the posse treats the injured ranch hand beside the wagon.\n",
                encoding="utf-8",
            )

            issues = validator.validate_outline_life_state_issues(book_folder)

        self.assertTrue(any(issue.rule_id == "VALIDATOR_OUTLINE_LIFE_STATE_CONTRADICTION" for issue in issues))

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


if __name__ == "__main__":
    unittest.main()
