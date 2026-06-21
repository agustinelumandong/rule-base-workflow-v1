# BookForge Genre Packs Developer Instructions

Use these rules when modifying subgenre configuration rules, checklists, or prompt skeletons under `bookforge/genre_packs/`.

---

## 1. Declarative Style & Configuration
- **No Executable Code**: Genre packs must contain only declarative configurations (e.g. YAML, JSON) and markdown reference guidelines. Do not insert Python code files inside genre pack directories.
- **YAML Schema Consistency**: When editing `*_subgenre_config.yaml`:
  - Ensure all keys align with the parser requirements in `bookforge/core/persona.py` and `bookforge/core/validators/style.py`.
  - Maintain correct mappings for `banned_words`, `style_guidelines`, and `required_metadata`.

---

## 2. Document Names & Discovery Conventions
- The genre-pack loader discovers packs by folder name. Inside a genre folder (e.g., `western/`), files must adhere to the standard names:
  - `*_subgenre_config.yaml`
  - `*_style_guide.md`
  - `*_character_rules.md`
  - `*_dialogue_rules.md`
  - `*_setting_rules.md`
  - `*_validation_checklist.md`
- Keep guidelines concise, using clear heading layouts and simple lists.
