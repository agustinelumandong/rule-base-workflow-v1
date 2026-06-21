#!/usr/bin/env python3
"""Unit tests for the BookForge Persona and Role Registry validation."""

import json
import unittest
import shutil
from pathlib import Path

from bookforge.core import persona
from bookforge.core import analytics as analytics_module


class TestPersonaRegistry(unittest.TestCase):
    def setUp(self):
        # Create a workspace-friendly temp directory
        self.tmp_dir = Path("tests/temp_test_persona")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        # Ensure registry file in temp dir
        self.registry_path = self.tmp_dir / "persona-registry.json"

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        
        # Clean up any root registry created during default fallback tests
        root_registry = Path("persona-registry.json")
        if root_registry.exists():
            try:
                root_registry.unlink()
            except Exception:
                pass

    def test_load_default_registry(self):
        reg = persona.load_registry(self.tmp_dir)
        self.assertIn("personas", reg)
        self.assertIn("writer", reg["personas"])
        self.assertIn("global_budget_cap_usd", reg)

    def test_unauthorized_model(self):
        # Write custom registry config
        custom_registry = {
            "personas": {
                "writer": {
                    "allowed_models": ["gpt-4o-mini"],
                    "allowed_actions": ["draft"]
                }
            },
            "global_budget_cap_usd": 15.00
        }
        self.registry_path.write_text(json.dumps(custom_registry), encoding="utf-8")

        # writer is trying to use gpt-4o (not in allowed_models)
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="gpt-4o",
            action="draft"
        )
        self.assertFalse(is_allowed)
        self.assertIn("not authorized for persona", reason)

    def test_unauthorized_action(self):
        custom_registry = {
            "personas": {
                "writer": {
                    "allowed_models": ["gpt-4o-mini"],
                    "allowed_actions": ["draft"]
                }
            },
            "global_budget_cap_usd": 15.00
        }
        self.registry_path.write_text(json.dumps(custom_registry), encoding="utf-8")

        # writer trying to run compile
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="gpt-4o-mini",
            action="compile"
        )
        self.assertFalse(is_allowed)
        self.assertIn("not authorized for persona", reason)

    def test_token_budget_cap(self):
        custom_registry = {
            "personas": {
                "writer": {
                    "allowed_models": ["gpt-4o-mini"],
                    "allowed_actions": ["draft"],
                    "token_budget_limit": 1000
                }
            },
            "global_budget_cap_usd": 15.00
        }
        self.registry_path.write_text(json.dumps(custom_registry), encoding="utf-8")

        # writer trying to send 5000 tokens
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="gpt-4o-mini",
            action="draft",
            projected_input_tokens=5000
        )
        self.assertFalse(is_allowed)
        self.assertIn("exceed persona 'writer' budget limit", reason)

    def test_global_budget_cap(self):
        custom_registry = {
            "personas": {
                "writer": {
                    "allowed_models": ["gpt-4o-mini"],
                    "allowed_actions": ["draft"],
                    "token_budget_limit": 100000
                }
            },
            "global_budget_cap_usd": 1.00 # very low budget cap
        }
        self.registry_path.write_text(json.dumps(custom_registry), encoding="utf-8")

        # Log a very expensive run that exceeds the budget cap
        analytics_module.log_run(
            book_folder=self.tmp_dir,
            model="gpt-4",  # $0.03 input, $0.06 output
            input_tokens=30000, # $0.90
            output_tokens=5000, # $0.30
            action="draft"
        )
        # Total cost is now $1.20, exceeding $1.00 cap

        # Trying a small call should be blocked
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="gpt-4o-mini",
            action="draft",
            projected_input_tokens=100
        )
        self.assertFalse(is_allowed)
        self.assertIn("exceeds global budget cap", reason)

    def test_load_yaml_registry(self):
        spec_dir = self.tmp_dir / "spec"
        spec_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = spec_dir / "model-routing.yml"
        
        custom_yaml = (
            "personas:\n"
            "  extractor:\n"
            "    model_class: cheap\n"
            "    examples: [gemini-1.5-flash]\n"
            "    tasks: [memory_build]\n"
        )
        yaml_path.write_text(custom_yaml, encoding="utf-8")
        
        reg = persona.load_registry(self.tmp_dir)
        self.assertIn("personas", reg)
        self.assertIn("extractor", reg["personas"])
        self.assertEqual(reg["personas"]["extractor"]["model_class"], "cheap")

    def test_yaml_capabilities_routing(self):
        spec_dir = self.tmp_dir / "spec"
        spec_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = spec_dir / "model-routing.yml"
        
        custom_yaml = (
            "personas:\n"
            "  writer:\n"
            "    model_class: strong\n"
            "    examples: [custom-writer-llm]\n"
            "    tasks: [draft_prose]\n"
        )
        yaml_path.write_text(custom_yaml, encoding="utf-8")

        # 1. Allowed by example
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="custom-writer-llm",
            action="draft"
        )
        self.assertTrue(is_allowed)

        # 2. Allowed by model_class (strong allows claude-3-5-sonnet)
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="claude-3-5-sonnet",
            action="draft"
        )
        self.assertTrue(is_allowed)

        # 3. Not allowed model
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="unauthorized-small-model",
            action="draft"
        )
        self.assertFalse(is_allowed)
        self.assertIn("not authorized for persona", reason)

        # 4. Action mapped to task (draft maps to draft_prose)
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="claude-3-5-sonnet",
            action="draft"
        )
        self.assertTrue(is_allowed)

        # 5. Unauthorized action
        is_allowed, reason = persona.check_persona_capabilities(
            book_folder=self.tmp_dir,
            persona_name="writer",
            model="claude-3-5-sonnet",
            action="unknown_action_name"
        )
        self.assertFalse(is_allowed)
        self.assertIn("is not authorized for persona", reason)


if __name__ == "__main__":
    unittest.main()

