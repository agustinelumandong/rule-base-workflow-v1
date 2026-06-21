# BookForge Western Genre Pack

**Status:** planning baseline
**Source seed:** `Western-Writing-style.pdf` and `Western-Writing-style.docx`
**Purpose:** convert Western writing guidance into machine-usable BookForge rules.

This pack is not a single prompt. It is a modular operating layer for Western projects. It supplies generation rules, prompt blocks, validation checks, subgenre routing, and human review criteria.

## Pack Files

- `western_style_guide.md` - core Western writing rules.
- `western_prompt_blocks.md` - reusable prompt blocks for generation and revision.
- `western_validation_checklist.md` - deterministic and model-assisted checks.
- `western_subgenre_config.yaml` - subgenre routing and tone expectations.
- `western_dialogue_rules.md` - dialogue and dialect policy.
- `western_era_accuracy_rules.md` - historical, cultural, and environmental rules.
- `western_character_rules.md` - protagonist, antagonist, supporting-cast, and representation rules.

## Pipeline Use

```text
Story brief
-> select Western genre pack and subgenre
-> create canon bible and authenticity pack
-> create character profiles
-> expand chapter beats
-> draft chapter with Western prompt blocks
-> run Western style and dialogue pass
-> run era, continuity, character, and theme validators
-> run Western prime directive rollup
-> human review
-> final manuscript
```

## Non-Negotiable Principle

A Western manuscript must be consistent, physical, era-accurate, and character-driven.

The genre pack exists to make that principle operational before drafting, during revision, and at final validation.
