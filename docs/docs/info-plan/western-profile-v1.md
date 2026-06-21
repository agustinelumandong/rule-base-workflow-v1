# Western Profile v1

**Status:** implementation brief  
**Source:** `BOOKFORGE-MASTER-PLAN.md` and `genre-packs/western/`

## Prime Directive

A Western manuscript must be consistent, physical, era-accurate, and character-driven.

## Runtime Scope For Early Phases

For Phase 0, Western Profile v1 is a contract and fixture set. For Phase 1, it is used only in the local proof engine. It should not become a broad genre engine until later phases.

## Required Early Contracts

- `WesternStyleProfile`
- `WesternDialoguePolicy`
- `WesternGlossaryEntry`
- `WesternStyleFinding`
- `WesternPrimeDirectiveValidator` rollup contract
- Western prompt-block metadata
- Western validation checklist fixture

## Required Phase 1 Fixture Checks

- Rewrite over-explained emotion into observable behavior without changing the event.
- Detect polished-modern dialogue.
- Detect caricature dialect.
- Detect purple prose.
- Detect forced glossary insertion.
- Permit approved interior thought when clarity requires it.
- Separate style violations from period-authenticity and character-voice violations.

## Must Not Do Early

- Do not build a full Western research engine.
- Do not auto-approve historical facts.
- Do not turn glossary entries into decorative word stuffing.
- Do not make all characters speak with the same rough dialect.
- Do not let Western style override canon, character profile, period pack, or continuity locks.

## Source Files

- `genre-packs/western/README.md`
- `genre-packs/western/western_style_guide.md`
- `genre-packs/western/western_prompt_blocks.md`
- `genre-packs/western/western_validation_checklist.md`
- `genre-packs/western/western_subgenre_config.yaml`
- `genre-packs/western/western_dialogue_rules.md`
- `genre-packs/western/western_era_accuracy_rules.md`
- `genre-packs/western/western_character_rules.md`
