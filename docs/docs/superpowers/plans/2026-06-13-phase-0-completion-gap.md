# Phase 0 Completion Gap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the remaining Phase 0 schema-contract gap between the committed starter cut and the full Phase 0 gate in `BOOKFORGE-MASTER-PLAN.md`.

**Architecture:** Keep BookForge as schema contracts plus deterministic tests only. Add missing Pydantic schema modules in focused groups, with no CLI, API, UI, database, RAG, vector store, graph store, workers, external model SDKs, or Phase 1 proof flow.

**Tech Stack:** Python 3.11+, Pydantic v2, pytest, ruff.

---

## Scope Check

Current committed starter cut already covers:

- `bookforge/schemas/project.py`
- `bookforge/schemas/artifact.py`
- `bookforge/schemas/canon.py`
- `bookforge/schemas/character.py`
- `bookforge/schemas/context_package.py`
- `bookforge/schemas/prompt.py`
- `bookforge/schemas/policy.py`
- `bookforge/schemas/capability.py`
- `bookforge/schemas/persona.py`
- `bookforge/schemas/validation.py`
- `bookforge/schemas/review.py`
- `bookforge/schemas/provider.py`
- `bookforge/schemas/export.py`
- `tests/test_phase0_contracts.py`

This plan completes only the full Phase 0 contract gate from `BOOKFORGE-MASTER-PLAN.md:1844-1900`.

Do not build:

- CLI commands
- FastAPI service
- browser UI
- PostgreSQL
- vector or graph database
- RAG pipeline
- external research automation
- real model provider routing
- Phase 1 deterministic proof flow
- Docker production stack

## Gap Matrix

| Master-plan Phase 0 item | Current status | Planned file |
| --- | --- | --- |
| Domain states and error taxonomy | missing | `bookforge/schemas/stage.py`, `bookforge/schemas/errors.py` |
| Chapter schema | missing | `bookforge/schemas/chapter.py` |
| Model run schema | missing | `bookforge/schemas/model_run.py` |
| Object/resource/inventory/story event/state transition | missing | `bookforge/schemas/object.py`, `bookforge/schemas/story_state.py` |
| Historical and period facts | missing | `bookforge/schemas/historical.py` |
| Authenticity policy/pack/findings/research needed | missing | `bookforge/schemas/authenticity.py` |
| Continuity locks/travel/supply/continuity finding | missing | `bookforge/schemas/continuity_lock.py` |
| Western style profile/glossary/finding | missing | `bookforge/schemas/style_profile.py` |
| Character governance/promotion/plot readiness | missing | `bookforge/schemas/character_governance.py` |
| Character arc/antagonist/supporting/evolution | missing | `bookforge/schemas/character_arc.py` |
| Theme governance/theme beats/findings | missing | `bookforge/schemas/theme.py` |
| Source promotion/canonical source roles | missing | `bookforge/schemas/source_promotion.py` |
| Detailed beat/layered beat | missing | `bookforge/schemas/beat.py` |
| Action scene/gunfight plan | missing | `bookforge/schemas/action_scene.py` |
| Numeric lock/number transition/group profile | missing | `bookforge/schemas/numeric_lock.py` |
| Deterministic prompt/persona fixtures | missing | `tests/fixtures/phase0/lone_star_reckoning.yaml`, `tests/fixtures/prompts/humanize.yaml` |

## File Structure

- Create: `tests/test_phase0_completion_contracts.py`
  - Coverage for the remaining Phase 0 schema contracts.
- Create: `bookforge/schemas/errors.py`
  - Typed error codes and error records.
- Create: `bookforge/schemas/stage.py`
  - Stage identity and stage-run state contracts.
- Create: `bookforge/schemas/chapter.py`
  - Chapter, scene, and structural identity contracts.
- Create: `bookforge/schemas/model_run.py`
  - Model-run provenance contract.
- Create: `bookforge/schemas/object.py`
  - Object profile, resource state, inventory state.
- Create: `bookforge/schemas/story_state.py`
  - Story event, state transition, knowledge state, continuity state, thread state.
- Create: `bookforge/schemas/historical.py`
  - Historical fact and availability profile.
- Create: `bookforge/schemas/authenticity.py`
  - Authenticity policy, pack, finding, research-needed request.
- Create: `bookforge/schemas/continuity_lock.py`
  - Locked detail, lock projection, travel state, supply state, continuity finding.
- Create: `bookforge/schemas/style_profile.py`
  - Western style profile, dialogue policy, glossary entry, style finding.
- Create: `bookforge/schemas/character_governance.py`
  - Character governance policy, incidental descriptor, promotion request, plot-readiness report.
- Create: `bookforge/schemas/character_arc.py`
  - Antagonist profile, supporting-character function, arc state, change event, evolution delta, series memory.
- Create: `bookforge/schemas/theme.py`
  - Theme policy/profile/arc/beat/findings.
- Create: `bookforge/schemas/source_promotion.py`
  - Canonical source role and promotion record.
- Create: `bookforge/schemas/beat.py`
  - Detailed beat and layered beat profile.
- Create: `bookforge/schemas/action_scene.py`
  - Action scene plan and gunfight plan.
- Create: `bookforge/schemas/numeric_lock.py`
  - Numeric lock, numeric state, number transition, group profile.
- Create: `tests/fixtures/phase0/lone_star_reckoning.yaml`
  - Minimal deterministic fixture manifest for Phase 0 schema validation.
- Create: `tests/fixtures/prompts/humanize.yaml`
  - Prompt metadata fixture referenced by prompt tests.
- Modify: `bookforge/schemas/__init__.py`
  - Export no heavy runtime behavior; keep package import clean.

## Task 1: Domain State, Errors, Chapter, And Model Run

**Files:**
- Create: `tests/test_phase0_completion_contracts.py`
- Create: `bookforge/schemas/errors.py`
- Create: `bookforge/schemas/stage.py`
- Create: `bookforge/schemas/chapter.py`
- Create: `bookforge/schemas/model_run.py`

- [ ] **Step 1: Write failing tests**

Add these tests to `tests/test_phase0_completion_contracts.py`:

```python
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from bookforge.schemas.chapter import ChapterIdentity, SceneIdentity
from bookforge.schemas.errors import ContractError, ErrorCode
from bookforge.schemas.model_run import ModelRunRecord
from bookforge.schemas.stage import StageDefinition, StageRunState


def test_error_record_carries_code_message_and_scope() -> None:
    error = ContractError(
        code=ErrorCode.PROJECT_SCOPE_VIOLATION,
        message="path escapes project root",
        project_id="lone-star",
        artifact_id="artifact:chapter-008:v1",
    )

    assert error.code is ErrorCode.PROJECT_SCOPE_VIOLATION
    assert error.project_id == "lone-star"


def test_stage_definition_declares_required_gates_and_capability() -> None:
    stage = StageDefinition(
        stage_id="phase0.contract_validation",
        required_gates=["project_loaded", "policy_snapshot_loaded"],
        capability_id="validate_contracts",
        allowed_states=[StageRunState.PENDING, StageRunState.RUNNING, StageRunState.COMPLETED],
    )

    assert stage.capability_id == "validate_contracts"
    assert StageRunState.COMPLETED in stage.allowed_states


def test_chapter_and_scene_identity_preserve_story_hierarchy() -> None:
    chapter = ChapterIdentity(
        project_id="lone-star",
        book_id="book-001",
        chapter_id="chapter-008",
        chapter_number=8,
        title="Dust at the Crossing",
    )
    scene = SceneIdentity(
        project_id="lone-star",
        book_id="book-001",
        chapter_id=chapter.chapter_id,
        scene_id="scene-008-001",
        sequence=1,
        pov_character_id="character:darin",
    )

    assert chapter.chapter_number == 8
    assert scene.chapter_id == chapter.chapter_id


def test_model_run_record_requires_prompt_persona_context_policy_and_output() -> None:
    run = ModelRunRecord(
        model_run_id="run:phase0:001",
        project_id="lone-star",
        stage="contract_validation",
        prompt_id="humanize@1.0.0",
        persona_id="western_prose_editor",
        persona_version="1.0.0",
        capability_id="validate_contracts",
        context_package_id="ctx:phase0",
        provider_id="deterministic",
        model="fixture",
        artifact_output_id="artifact:phase0-report:v1",
        policy_snapshot_id="policy:snap:001",
        started_at=datetime(2026, 6, 13, tzinfo=UTC),
    )

    assert run.provider_id == "deterministic"
    assert run.policy_snapshot_id == "policy:snap:001"


def test_model_run_rejects_missing_provenance() -> None:
    with pytest.raises(ValidationError):
        ModelRunRecord(
            model_run_id="run:bad",
            project_id="lone-star",
            stage="contract_validation",
            prompt_id="humanize@1.0.0",
            persona_id="western_prose_editor",
            persona_version="1.0.0",
            capability_id="validate_contracts",
            context_package_id="ctx:phase0",
            provider_id="deterministic",
            model="fixture",
            artifact_output_id="artifact:phase0-report:v1",
        )
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py -q
```

Expected: FAIL during import because `bookforge.schemas.chapter`, `errors`, `model_run`, and `stage` do not exist.

- [ ] **Step 3: Implement minimal schemas**

Create `bookforge/schemas/errors.py`:

```python
from __future__ import annotations

from enum import Enum

from pydantic import Field

from bookforge.schemas.base import ContractModel


class ErrorCode(str, Enum):
    PROJECT_SCOPE_VIOLATION = "project_scope_violation"
    MISSING_REQUIRED_CONTEXT = "missing_required_context"
    INVALID_POLICY = "invalid_policy"
    APPROVAL_REQUIRED = "approval_required"
    VALIDATION_BLOCKED = "validation_blocked"


class ContractError(ContractModel):
    code: ErrorCode
    message: str = Field(min_length=1)
    project_id: str | None = None
    artifact_id: str | None = None
```

Create `bookforge/schemas/stage.py`:

```python
from __future__ import annotations

from enum import Enum

from pydantic import Field

from bookforge.schemas.base import ContractModel


class StageRunState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class StageDefinition(ContractModel):
    stage_id: str = Field(min_length=1)
    required_gates: list[str] = Field(default_factory=list)
    capability_id: str = Field(min_length=1)
    allowed_states: list[StageRunState] = Field(default_factory=list)
```

Create `bookforge/schemas/chapter.py`:

```python
from __future__ import annotations

from pydantic import Field

from bookforge.schemas.base import ContractModel


class ChapterIdentity(ContractModel):
    project_id: str = Field(min_length=1)
    book_id: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)
    chapter_number: int = Field(ge=1)
    title: str = Field(min_length=1)


class SceneIdentity(ContractModel):
    project_id: str = Field(min_length=1)
    book_id: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)
    scene_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    pov_character_id: str | None = None
```

Create `bookforge/schemas/model_run.py`:

```python
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from bookforge.schemas.base import ContractModel


class ModelRunRecord(ContractModel):
    model_run_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    persona_id: str = Field(min_length=1)
    persona_version: str = Field(min_length=1)
    capability_id: str = Field(min_length=1)
    context_package_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    model: str = Field(min_length=1)
    artifact_output_id: str = Field(min_length=1)
    policy_snapshot_id: str = Field(min_length=1)
    started_at: datetime
```

- [ ] **Step 4: Run task tests**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py -q
```

Expected: PASS for Task 1 tests and FAIL for later task tests only after those tests are added.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_phase0_completion_contracts.py bookforge/schemas/errors.py bookforge/schemas/stage.py bookforge/schemas/chapter.py bookforge/schemas/model_run.py
git commit -m "feat: add phase 0 state and model-run contracts"
```

## Task 2: Historical, Authenticity, And Western Style Contracts

**Files:**
- Modify: `tests/test_phase0_completion_contracts.py`
- Create: `bookforge/schemas/historical.py`
- Create: `bookforge/schemas/authenticity.py`
- Create: `bookforge/schemas/style_profile.py`

- [ ] **Step 1: Add failing tests**

Append tests for:

```python
from bookforge.schemas.authenticity import AuthenticityPack, AuthenticityPolicy, ResearchNeededRequest
from bookforge.schemas.historical import AvailabilityProfile, HistoricalFact
from bookforge.schemas.style_profile import WesternDialoguePolicy, WesternGlossaryEntry, WesternStyleProfile


def test_historical_fact_keeps_time_place_evidence_and_review_state() -> None:
    fact = HistoricalFact(
        fact_id="hist:colt-1849",
        claim="Colt pocket revolvers existed in 1849 California.",
        valid_from_year=1849,
        valid_until_year=1873,
        geography="California",
        category="weapon",
        evidence_refs=["source:colt-catalog"],
        review_status="approved",
    )

    assert fact.applies_to(1850, "California") is True
    assert fact.applies_to(1848, "California") is False


def test_availability_profile_records_allowed_blocked_and_research_required() -> None:
    profile = AvailabilityProfile(
        profile_id="availability:1849-california",
        category="transport",
        allowed=["horse", "wagon"],
        blocked=["automobile"],
        research_required=["rail access near settlement"],
    )

    assert "automobile" in profile.blocked


def test_authenticity_policy_and_pack_keep_research_separate_from_canon() -> None:
    policy = AuthenticityPolicy(
        policy_id="authenticity:western-high",
        enabled=True,
        strictness="high",
        required_categories=["weapons", "travel", "law"],
    )
    pack = AuthenticityPack(
        pack_id="pack:1849-california",
        policy_id=policy.policy_id,
        date_range="1849",
        geography="California",
        approved_fact_ids=["hist:colt-1849"],
        blocked_details=["automobile"],
        research_required=["county jail procedure"],
    )

    assert pack.policy_id == policy.policy_id
    assert "county jail procedure" in pack.research_required


def test_research_needed_request_identifies_missing_evidence() -> None:
    request = ResearchNeededRequest(
        request_id="research:law:001",
        project_id="lone-star",
        question="Was this jail procedure available in this county in 1849?",
        category="law",
        affected_artifact_id="artifact:chapter-008:v2",
        risk="unsupported period detail",
    )

    assert request.category == "law"


def test_western_style_profile_dialogue_and_glossary_contracts() -> None:
    profile = WesternStyleProfile(
        profile_id="western:v1",
        prime_directive="consistent, physical, era-accurate, and character-driven",
        blocked_modernisms=["okay", "cop"],
        behavior_first=True,
    )
    dialogue = WesternDialoguePolicy(
        policy_id="western-dialogue:v1",
        dialect_intensity="light",
        blocked_patterns=["pardner"],
    )
    glossary = WesternGlossaryEntry(
        term="livery",
        meaning="stable where horses are kept for hire",
        valid_geography="American West",
        valid_from_year=1800,
        approved=True,
    )

    assert profile.behavior_first is True
    assert dialogue.dialect_intensity == "light"
    assert glossary.approved is True
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py -q
```

Expected: FAIL importing `authenticity`, `historical`, and `style_profile`.

- [ ] **Step 3: Implement minimal schemas**

Create focused Pydantic models with exactly the fields used by tests plus `Field(min_length=1)` on IDs and required strings. Add `HistoricalFact.applies_to(year, geography)` returning true only when year is within bounds and geography matches exactly.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py tests/test_phase0_contracts.py -q
```

Expected: all current tests PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_phase0_completion_contracts.py bookforge/schemas/historical.py bookforge/schemas/authenticity.py bookforge/schemas/style_profile.py
git commit -m "feat: add phase 0 authenticity and style contracts"
```

## Task 3: Character Governance, Arc, And Theme Contracts

**Files:**
- Modify: `tests/test_phase0_completion_contracts.py`
- Create: `bookforge/schemas/character_governance.py`
- Create: `bookforge/schemas/character_arc.py`
- Create: `bookforge/schemas/theme.py`

- [ ] **Step 1: Add failing tests**

Append tests for:

```python
from bookforge.schemas.character_arc import (
    AntagonistProfile,
    CharacterArcState,
    CharacterChangeEvent,
    CharacterEvolutionDelta,
    SupportingCharacterFunction,
)
from bookforge.schemas.character_governance import (
    CharacterGovernancePolicy,
    CharacterPromotionRequest,
    IncidentalCharacterDescriptor,
    PlotReadinessReport,
)
from bookforge.schemas.theme import ThemeArc, ThemeBeat, ThemeGovernancePolicy, ThemeProfile


def test_character_governance_blocks_unprofiled_names_and_tracks_promotion() -> None:
    policy = CharacterGovernancePolicy(
        policy_id="character-governance:v1",
        block_unprofiled_names=True,
        require_profiles_before_plotting=True,
        cast_clutter_threshold=12,
    )
    descriptor = IncidentalCharacterDescriptor(
        descriptor_id="descriptor:livery-hand-001",
        project_id="lone-star",
        display_label="the livery hand",
        naming_allowed=False,
        function="background labor",
    )
    promotion = CharacterPromotionRequest(
        request_id="promotion:livery-hand-001",
        descriptor_id=descriptor.descriptor_id,
        proposed_character_id="character:amos",
        reason="recurs with plot-relevant knowledge",
        reviewer_decision="pending",
    )

    assert policy.block_unprofiled_names is True
    assert promotion.descriptor_id == descriptor.descriptor_id


def test_plot_readiness_report_lists_missing_profiles() -> None:
    report = PlotReadinessReport(
        report_id="plot-readiness:book-001",
        project_id="lone-star",
        missing_profile_ids=["character:antagonist"],
        ready=False,
    )

    assert report.ready is False


def test_character_arc_contracts_cover_antagonist_supporting_and_evolution() -> None:
    antagonist = AntagonistProfile(
        character_id="character:harlan",
        external_goal="control the crossing",
        motive="profit and revenge",
        moral_code="protects his own men",
        forbidden_behavior=["random panic"],
    )
    support = SupportingCharacterFunction(
        character_id="character:mara",
        active_function="withholds key evidence",
        required_until="chapter-010",
        exit_condition="evidence revealed",
    )
    event = CharacterChangeEvent(
        event_id="change:darin:trust",
        character_id="character:darin",
        cause="Mara risks herself with evidence",
        effect="Darin trusts her testimony",
        source_artifact_id="chapter-009",
    )
    state = CharacterArcState(
        character_id="character:darin",
        current_position="guarded trust",
        approved_change_event_ids=[event.event_id],
    )
    delta = CharacterEvolutionDelta(
        delta_id="evolution:darin:book-001",
        character_id="character:darin",
        book_id="book-001",
        carried_forward=["left shoulder scar", "trusts Mara"],
    )

    assert "random panic" in antagonist.forbidden_behavior
    assert support.exit_condition == "evidence revealed"
    assert event.event_id in state.approved_change_event_ids
    assert "trusts Mara" in delta.carried_forward


def test_theme_contracts_require_dramatized_pressure() -> None:
    policy = ThemeGovernancePolicy(
        policy_id="theme:v1",
        anti_lecture=True,
        require_moral_choice=True,
    )
    profile = ThemeProfile(
        theme_id="theme:justice-vs-revenge",
        primary_theme="justice versus revenge",
        forbidden_handling=["sermon"],
    )
    arc = ThemeArc(
        theme_id=profile.theme_id,
        opening_position="revenge looks clean",
        midpoint_pressure="justice costs evidence",
        final_expression="mercy with consequence",
    )
    beat = ThemeBeat(
        beat_id="theme-beat:008",
        theme_id=profile.theme_id,
        question="Will Darin choose lawful proof over revenge?",
        dramatized_through=["refuses easy shot"],
        visible_cost="Harlan escapes",
    )

    assert policy.anti_lecture is True
    assert arc.theme_id == profile.theme_id
    assert "refuses easy shot" in beat.dramatized_through
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py -q
```

Expected: FAIL importing the three new schema modules.

- [ ] **Step 3: Implement minimal schemas**

Create the three schema files with Pydantic models matching every field in the tests. Use `Field(min_length=1)` for identifiers and required strings. Use list defaults with `Field(default_factory=list)`.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py tests/test_phase0_contracts.py -q
```

Expected: all current tests PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_phase0_completion_contracts.py bookforge/schemas/character_governance.py bookforge/schemas/character_arc.py bookforge/schemas/theme.py
git commit -m "feat: add phase 0 character and theme contracts"
```

## Task 4: Story State, Object, Continuity Lock, Numeric Lock, And Source Promotion

**Files:**
- Modify: `tests/test_phase0_completion_contracts.py`
- Create: `bookforge/schemas/object.py`
- Create: `bookforge/schemas/story_state.py`
- Create: `bookforge/schemas/continuity_lock.py`
- Create: `bookforge/schemas/numeric_lock.py`
- Create: `bookforge/schemas/source_promotion.py`

- [ ] **Step 1: Add failing tests**

Append tests for:

```python
from bookforge.schemas.continuity_lock import LockedDetail, LockLevel, LockProjection
from bookforge.schemas.numeric_lock import NumericLock, NumericState, NumberTransition
from bookforge.schemas.object import ObjectProfile, ObjectState, ResourceState
from bookforge.schemas.source_promotion import CanonicalSourceRole, SourcePromotionRecord
from bookforge.schemas.story_state import StateTransition, StoryEvent


def test_object_resource_and_state_contracts_track_current_values() -> None:
    profile = ObjectProfile(
        object_id="object:colt-revolver",
        project_id="lone-star",
        object_type="weapon",
        continuity_class="critical",
        capacity=6,
    )
    resource = ResourceState(
        resource_id="resource:ammo:colt",
        object_id=profile.object_id,
        unit="round",
        quantity=3,
    )
    state = ObjectState(
        object_id=profile.object_id,
        holder_id="character:darin",
        location_id="location:crossing",
        condition="working",
        resource_states=[resource],
        version=1,
    )

    assert state.resource_states[0].quantity == 3


def test_story_event_and_state_transition_keep_before_after_values() -> None:
    event = StoryEvent(
        event_id="event:shot-001",
        project_id="lone-star",
        source_artifact_id="chapter-008",
        description="Darin fires one round.",
    )
    transition = StateTransition(
        transition_id="transition:ammo-001",
        event_id=event.event_id,
        subject_id="resource:ammo:colt",
        property_name="quantity",
        before_value="3",
        after_value="2",
        approval_state="proposed",
    )

    assert transition.before_value == "3"
    assert transition.after_value == "2"


def test_continuity_lock_projection_references_authoritative_record() -> None:
    lock = LockedDetail(
        lock_id="lock:ammo:colt",
        subject_id="resource:ammo:colt",
        property_path="quantity",
        value="2",
        level=LockLevel.STRICT,
        source_record_id="transition:ammo-001",
    )
    projection = LockProjection(
        projection_id="lock-projection:chapter-008",
        project_id="lone-star",
        locked_details=[lock],
        source_versions={"transition:ammo-001": "1"},
    )

    assert projection.locked_details[0].level is LockLevel.STRICT


def test_numeric_lock_and_transition_validate_counts() -> None:
    lock = NumericLock(
        lock_id="numeric:ammo:colt",
        subject_id="resource:ammo:colt",
        property_name="quantity",
        value=3,
        unit="round",
        level="strict",
    )
    state = NumericState(
        subject_id=lock.subject_id,
        property_name=lock.property_name,
        value=3,
        unit="round",
    )
    transition = NumberTransition(
        transition_id="number:ammo-fired",
        subject_id=lock.subject_id,
        before_value=3,
        delta=-1,
        after_value=2,
        reason="one shot fired",
    )

    assert state.value == 3
    assert transition.after_value == 2


def test_source_promotion_records_canonical_working_source() -> None:
    record = SourcePromotionRecord(
        promotion_id="promotion:chapter-008:v2",
        artifact_id="artifact:chapter-008:v2",
        parent_artifact_id="artifact:chapter-008:v1",
        promoted_role=CanonicalSourceRole.CANONICAL_WORKING_SOURCE,
        approval_id="approval:chapter-008:v2",
        superseded_artifact_ids=["artifact:chapter-008:v1"],
    )

    assert record.promoted_role is CanonicalSourceRole.CANONICAL_WORKING_SOURCE
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py -q
```

Expected: FAIL importing object/story state/continuity/numeric/source promotion modules.

- [ ] **Step 3: Implement minimal schemas**

Create the five files with exact models and enums used by tests. Keep all values serializable as strings, ints, lists, and dicts. Do not add persistence code.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py tests/test_phase0_contracts.py -q
```

Expected: all current tests PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_phase0_completion_contracts.py bookforge/schemas/object.py bookforge/schemas/story_state.py bookforge/schemas/continuity_lock.py bookforge/schemas/numeric_lock.py bookforge/schemas/source_promotion.py
git commit -m "feat: add phase 0 story-state contracts"
```

## Task 5: Beat And Action Scene Contracts

**Files:**
- Modify: `tests/test_phase0_completion_contracts.py`
- Create: `bookforge/schemas/beat.py`
- Create: `bookforge/schemas/action_scene.py`

- [ ] **Step 1: Add failing tests**

Append tests for:

```python
from bookforge.schemas.action_scene import ActionScenePlan, GunfightPlan
from bookforge.schemas.beat import DetailedBeat, LayeredBeatProfile


def test_detailed_beat_contains_draftable_fields() -> None:
    beat = DetailedBeat(
        beat_id="beat:008:001",
        scene_id="scene-008-001",
        goal="Darin questions the livery hand.",
        conflict="The hand fears Harlan.",
        required_reveal="Harlan bought ammunition.",
        emotional_movement="suspicion hardens into resolve",
        state_change="Darin learns Harlan is armed",
        forbidden_changes=["do not add a gunfight"],
        next_beat_connection="Darin checks the store ledger.",
    )

    assert beat.required_reveal == "Harlan bought ammunition."


def test_layered_beat_profile_lists_required_layers_and_forbidden_shortcuts() -> None:
    profile = LayeredBeatProfile(
        profile_id="layered:slow-burn:v1",
        required_layers=["physical_work", "environment", "social_pressure"],
        escalation_order=["work", "pressure", "threat"],
        forbidden_shortcuts=["sudden exposition dump"],
    )

    assert "physical_work" in profile.required_layers


def test_action_scene_and_gunfight_plan_constrain_logistics() -> None:
    action = ActionScenePlan(
        plan_id="action:chapter-008",
        scene_id="scene-008-004",
        scene_type="gunfight",
        participants=["character:darin", "character:harlan"],
        location_layout="street with trough and store porch",
        movement_limits=["Darin cannot sprint due to shoulder wound"],
        forbidden_impossibilities=["no unsupported reload"],
    )
    gunfight = GunfightPlan(
        plan_id="gunfight:chapter-008",
        action_plan_id=action.plan_id,
        weapon_states={"object:colt-revolver": "3 rounds"},
        shot_order=["character:harlan", "character:darin"],
        ammunition_after={"object:colt-revolver": "2 rounds"},
    )

    assert gunfight.action_plan_id == action.plan_id
    assert gunfight.ammunition_after["object:colt-revolver"] == "2 rounds"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py -q
```

Expected: FAIL importing `beat` and `action_scene`.

- [ ] **Step 3: Implement minimal schemas**

Create `DetailedBeat`, `LayeredBeatProfile`, `ActionScenePlan`, and `GunfightPlan` with fields used by tests. Use list and dict default factories.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py tests/test_phase0_contracts.py -q
```

Expected: all current tests PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_phase0_completion_contracts.py bookforge/schemas/beat.py bookforge/schemas/action_scene.py
git commit -m "feat: add phase 0 beat and action contracts"
```

## Task 6: Deterministic Fixtures And Prompt Metadata

**Files:**
- Modify: `tests/test_phase0_completion_contracts.py`
- Create: `tests/fixtures/phase0/lone_star_reckoning.yaml`
- Create: `tests/fixtures/prompts/humanize.yaml`

- [ ] **Step 1: Add failing fixture tests**

Append tests:

```python
from pathlib import Path

import yaml


def test_lone_star_reckoning_fixture_manifest_exists_and_is_phase0_only() -> None:
    data = yaml.safe_load(Path("tests/fixtures/phase0/lone_star_reckoning.yaml").read_text())

    assert data["project_id"] == "lone-star-reckoning"
    assert data["phase"] == "phase0"
    assert data["external_models_allowed"] is False
    assert set(data["contracts"]) >= {"project", "artifact", "canon", "character", "policy"}


def test_humanize_prompt_fixture_has_machine_readable_metadata() -> None:
    data = yaml.safe_load(Path("tests/fixtures/prompts/humanize.yaml").read_text())

    assert data["id"] == "humanize"
    assert data["version"] == "1.0.0"
    assert "source_artifact" in data["required_inputs"]
    assert "preserve_canon" in data["validation_rules"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py -q
```

Expected: FAIL because fixture YAML files do not exist.

- [ ] **Step 3: Add fixture files**

Create `tests/fixtures/phase0/lone_star_reckoning.yaml`:

```yaml
project_id: lone-star-reckoning
phase: phase0
external_models_allowed: false
contracts:
  - project
  - artifact
  - canon
  - character
  - context_package
  - prompt
  - policy
  - capability
  - persona
  - validation
  - review
  - provider
  - export
```

Create `tests/fixtures/prompts/humanize.yaml`:

```yaml
id: humanize
version: 1.0.0
task: manuscript_transformation
required_inputs:
  - source_artifact
  - approved_canon
  - style_guide
output_contract: transformed_text_with_change_report
validation_rules:
  - preserve_meaning
  - preserve_canon
failure_modes:
  - missing_context
  - unsupported_invention
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_phase0_completion_contracts.py tests/test_phase0_contracts.py -q
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_phase0_completion_contracts.py tests/fixtures/phase0/lone_star_reckoning.yaml tests/fixtures/prompts/humanize.yaml
git commit -m "test: add phase 0 deterministic fixtures"
```

## Task 7: Full Phase 0 Verification

**Files:**
- Inspect: `bookforge/schemas/`
- Inspect: `tests/`
- Inspect: `docs/info-plan/BOOKFORGE-MASTER-PLAN.md`
- Inspect: `docs/info-plan/phase-0-contracts.md`

- [ ] **Step 1: Confirm required schema files exist**

Run:

```bash
python - <<'PY'
from pathlib import Path

required = [
    "project.py",
    "canon.py",
    "character.py",
    "character_governance.py",
    "character_arc.py",
    "theme.py",
    "object.py",
    "story_state.py",
    "historical.py",
    "authenticity.py",
    "continuity_lock.py",
    "style_profile.py",
    "source_promotion.py",
    "beat.py",
    "action_scene.py",
    "numeric_lock.py",
    "chapter.py",
    "artifact.py",
    "context_package.py",
    "policy.py",
    "validation.py",
    "review.py",
    "model_run.py",
    "persona.py",
]

missing = [name for name in required if not (Path("bookforge/schemas") / name).exists()]
if missing:
    raise SystemExit(f"missing schema files: {missing}")
print("all required Phase 0 schema files exist")
PY
```

Expected:

```text
all required Phase 0 schema files exist
```

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests PASS.

- [ ] **Step 3: Run lint**

Run:

```bash
python -m ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 4: Confirm forbidden infrastructure is absent**

Run:

```bash
rg -n "FastAPI|PostgreSQL|psycopg|sqlalchemy|redis|celery|langchain|llama|vector|graph database|uvicorn" bookforge pyproject.toml tests || true
```

Expected: no matches except harmless prose inside tests if added by reviewers. There should be no dependency or runtime implementation for forbidden infrastructure.

- [ ] **Step 5: Commit final verification documentation if changed**

If verification required no edits, do not commit.

If small corrections were made, run:

```bash
git add bookforge tests
git commit -m "chore: align phase 0 completion contracts"
```

## Self-Review

Spec coverage:

- Covers all schema files named by the full Phase 0 master-plan gate.
- Covers current starter files and all missing contract groups.
- Preserves Phase 0-only boundary and forbids runtime infrastructure.
- Keeps tests deterministic and offline.

Placeholder scan:

- No placeholder implementation language remains.
- Every test task includes executable test code or exact verification commands.

Type consistency:

- Every referenced class has a planned file.
- Every test import maps to an exact module path.
- Commit boundaries align with schema groups.
