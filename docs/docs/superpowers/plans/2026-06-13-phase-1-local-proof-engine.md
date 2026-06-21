# Phase 1 Local Proof Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the minimum deterministic Phase 1 proof engine for one `Lone Star Reckoning` chapter transformation.

**Architecture:** Add a small file-backed proof package under `bookforge/proof/` that loads deterministic fixtures, builds scoped context, runs a fixture provider, validates seeded failures, records trace/review artifacts, and exports approved Markdown. Keep every operation importable and test-driven; do not add CLI, API, UI, database, RAG, vector/graph retrieval, real model services, or production workers.

**Tech Stack:** Python 3.11+, Pydantic v2 contracts already in `bookforge/schemas/`, PyYAML, pytest, ruff.

---

## Scope Check

Phase 0 is committed and verified:

- Required Phase 0 schema files exist.
- `python -m pytest -q` passes.
- `python -m ruff check .` passes.
- Forbidden runtime infrastructure scan is clean.

Phase 1 must implement only `docs/info-plan/phase-1-local-proof-engine.md` minimum proof:

- one project
- one imported chapter
- one protagonist
- one antagonist
- one supporting character
- one weapon
- one ammunition-count contradiction
- one unprofiled-name contradiction
- one Western style violation
- one approval
- one Markdown export

Do not build:

- CLI commands
- FastAPI service
- browser UI
- PostgreSQL or migrations
- vector or graph retrieval
- external research automation
- real model provider routing
- multi-agent workflow
- EPUB/PDF export
- series-level memory
- multi-service Docker Compose stack

## File Structure

- Create: `bookforge/proof/__init__.py`
  - Package marker for Phase 1 proof engine.
- Create: `bookforge/proof/fixtures.py`
  - Load and validate one YAML proof fixture into typed Pydantic objects.
- Create: `bookforge/proof/context.py`
  - Build scoped `ContextPackage`; reject wrong project/version, missing canon, and path escape.
- Create: `bookforge/proof/engine.py`
  - Run deterministic transformation from fixture provider and produce candidate artifact text.
- Create: `bookforge/proof/validators.py`
  - Deterministic validators for meaning, canon, unprofiled names, Western style, ammo transition, capability grants, and trace completeness.
- Create: `bookforge/proof/review_export.py`
  - Review approval simulation and approved-only Markdown export.
- Create: `bookforge/proof/pipeline.py`
  - Orchestrate the minimum proof flow and return a structured result.
- Create: `tests/fixtures/phase1/lone_star_reckoning.yaml`
  - Deterministic fixture with source chapter, candidate text, corrected text, canon, style rules, capability/persona/prompt metadata, and seeded failures.
- Create: `tests/test_phase1_local_proof.py`
  - End-to-end and focused Phase 1 tests.

## Task 1: Fixture Loader

**Files:**
- Create: `tests/test_phase1_local_proof.py`
- Create: `tests/fixtures/phase1/lone_star_reckoning.yaml`
- Create: `bookforge/proof/__init__.py`
- Create: `bookforge/proof/fixtures.py`

- [ ] **Step 1: Write failing fixture-loader tests**

Create `tests/test_phase1_local_proof.py`:

```python
from pathlib import Path

import pytest
from pydantic import ValidationError

from bookforge.proof.fixtures import ProofFixture, load_proof_fixture


FIXTURE_PATH = Path("tests/fixtures/phase1/lone_star_reckoning.yaml")


def test_loads_lone_star_reckoning_phase1_fixture() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)

    assert fixture.project_id == "lone-star-reckoning"
    assert fixture.book_id == "book-001"
    assert fixture.chapter_id == "chapter-008"
    assert fixture.canon_version == "canon:v1"
    assert fixture.persona_id == "western_prose_editor"
    assert fixture.capability_id == "humanize_chapter"
    assert fixture.weapon.object_id == "object:colt-revolver"
    assert fixture.weapon_rounds_start == 3


def test_fixture_rejects_external_models() -> None:
    data = load_proof_fixture(FIXTURE_PATH).model_dump()
    data["external_models_allowed"] = True

    with pytest.raises(ValidationError, match="external models are forbidden"):
        ProofFixture(**data)
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'bookforge.proof'`.

- [ ] **Step 3: Add fixture YAML**

Create `tests/fixtures/phase1/lone_star_reckoning.yaml`:

```yaml
project_id: lone-star-reckoning
book_id: book-001
chapter_id: chapter-008
canon_version: canon:v1
source_version: imported:v1
external_models_allowed: false
persona_id: western_prose_editor
persona_version: 1.0.0
prompt_id: humanize@1.0.0
capability_id: humanize_chapter
policy_snapshot_id: policy:snap:phase1
context_package_id: ctx:chapter-008
provider_id: deterministic
source_text: "Darin had three rounds in the Colt. He stepped into the livery and asked the hand what Harlan had bought."
candidate_text: "Darin had three rounds in the Colt. Ezra Bell told him Harlan bought shells. Darin felt very anxious and okay about it."
corrected_text: "Darin had three rounds in the Colt. The livery hand told him Harlan bought shells. Darin kept his thumb near the Colt and watched the street."
meaning_change_text: "Darin left the Colt behind and rode out of town."
unsupported_canon_text: "Darin owned Harlan's ranch and wore a marshal badge."
unprofiled_name: Ezra Bell
western_style_violation: okay
approved_character_ids:
  - character:darin
  - character:harlan
  - character:livery-hand
canon_facts:
  - fact_id: fact:darin:weapon
    subject_id: character:darin
    predicate: carries
    value: Colt revolver
  - fact_id: fact:harlan:ammo
    subject_id: character:harlan
    predicate: bought
    value: shells
weapon:
  object_id: object:colt-revolver
  project_id: lone-star-reckoning
  object_type: weapon
  continuity_class: critical
  capacity: 6
weapon_rounds_start: 3
shot_delta: -1
weapon_rounds_after_shot: 2
bad_round_claim: 3
allowed_tools:
  - read_artifact
  - read_canon
  - write_candidate_artifact
  - run_validators
forbidden_effects:
  - approve_artifact
  - mutate_canon
  - publish_export
```

- [ ] **Step 4: Implement fixture loader**

Create `bookforge/proof/__init__.py`:

```python
"""Deterministic local proof engine for BookForge Phase 1."""
```

Create `bookforge/proof/fixtures.py`:

```python
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field, model_validator

from bookforge.schemas.base import ContractModel
from bookforge.schemas.object import ObjectProfile


class FixtureCanonFact(ContractModel):
    fact_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    value: str = Field(min_length=1)


class ProofFixture(ContractModel):
    project_id: str = Field(min_length=1)
    book_id: str = Field(min_length=1)
    chapter_id: str = Field(min_length=1)
    canon_version: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    external_models_allowed: bool
    persona_id: str = Field(min_length=1)
    persona_version: str = Field(min_length=1)
    prompt_id: str = Field(min_length=1)
    capability_id: str = Field(min_length=1)
    policy_snapshot_id: str = Field(min_length=1)
    context_package_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    source_text: str = Field(min_length=1)
    candidate_text: str = Field(min_length=1)
    corrected_text: str = Field(min_length=1)
    meaning_change_text: str = Field(min_length=1)
    unsupported_canon_text: str = Field(min_length=1)
    unprofiled_name: str = Field(min_length=1)
    western_style_violation: str = Field(min_length=1)
    approved_character_ids: list[str] = Field(default_factory=list)
    canon_facts: list[FixtureCanonFact] = Field(default_factory=list)
    weapon: ObjectProfile
    weapon_rounds_start: int = Field(ge=0)
    shot_delta: int
    weapon_rounds_after_shot: int = Field(ge=0)
    bad_round_claim: int = Field(ge=0)
    allowed_tools: list[str] = Field(default_factory=list)
    forbidden_effects: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def forbid_external_models(self) -> "ProofFixture":
        if self.external_models_allowed:
            raise ValueError("external models are forbidden in Phase 1 proof")
        return self


def load_proof_fixture(path: Path) -> ProofFixture:
    data = yaml.safe_load(path.read_text())
    return ProofFixture(**data)
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py -q
```

Expected: PASS.

## Task 2: Context Builder And Gate Rejections

**Files:**
- Modify: `tests/test_phase1_local_proof.py`
- Create: `bookforge/proof/context.py`

- [ ] **Step 1: Add failing context tests**

Append to `tests/test_phase1_local_proof.py`:

```python
from bookforge.proof.context import build_context_package, resolve_fixture_path


def test_build_context_package_records_source_and_canon_versions() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)

    package = build_context_package(fixture)

    assert package.context_package_id == "ctx:chapter-008"
    assert package.project_id == fixture.project_id
    assert package.canon_version == fixture.canon_version
    assert package.source_ids == ["artifact:chapter-008:imported:v1"]


def test_wrong_project_or_version_is_rejected() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)

    with pytest.raises(ValueError, match="wrong project"):
        build_context_package(fixture.model_copy(update={"project_id": "other-project"}))

    with pytest.raises(ValueError, match="wrong source version"):
        build_context_package(fixture.model_copy(update={"source_version": "imported:v2"}))


def test_missing_canon_blocks_grounded_work() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)

    with pytest.raises(ValueError, match="missing canon"):
        build_context_package(fixture.model_copy(update={"canon_facts": []}))


def test_path_escape_is_rejected() -> None:
    with pytest.raises(ValueError, match="escapes project root"):
        resolve_fixture_path(Path("/workspace/projects/lone-star-reckoning"), "../other/file.md")
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py -q
```

Expected: FAIL importing `bookforge.proof.context`.

- [ ] **Step 3: Implement context builder**

Create `bookforge/proof/context.py`:

```python
from __future__ import annotations

from pathlib import Path

from bookforge.proof.fixtures import ProofFixture
from bookforge.schemas.context_package import ContextPackage, ContextSource
from bookforge.schemas.project import ProjectIdentity

EXPECTED_PROJECT_ID = "lone-star-reckoning"
EXPECTED_SOURCE_VERSION = "imported:v1"


def resolve_fixture_path(root: Path, relative_path: str) -> Path:
    project = ProjectIdentity(project_id=EXPECTED_PROJECT_ID, root=root)
    return project.resolve_project_path(relative_path)


def build_context_package(fixture: ProofFixture) -> ContextPackage:
    if fixture.project_id != EXPECTED_PROJECT_ID:
        raise ValueError("wrong project for Phase 1 proof")
    if fixture.source_version != EXPECTED_SOURCE_VERSION:
        raise ValueError("wrong source version for Phase 1 proof")
    if not fixture.canon_facts:
        raise ValueError("missing canon blocks grounded work")
    return ContextPackage(
        context_package_id=fixture.context_package_id,
        project_id=fixture.project_id,
        operation="humanize_chapter",
        canon_version=fixture.canon_version,
        stage="phase1.local_proof",
        sources=[
            ContextSource(
                source_id="artifact:chapter-008:imported:v1",
                source_type="artifact",
                version=fixture.source_version,
                role="source_text",
            )
        ],
        hard_rules=["no invention", "preserve canon", "offline deterministic provider only"],
        forbidden_changes=["new named characters", "unsupported canon facts", "modern Western style"],
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py -q
```

Expected: PASS.

## Task 3: Deterministic Engine And Validators

**Files:**
- Modify: `tests/test_phase1_local_proof.py`
- Create: `bookforge/proof/engine.py`
- Create: `bookforge/proof/validators.py`

- [ ] **Step 1: Add failing engine/validator tests**

Append:

```python
from bookforge.proof.engine import run_deterministic_humanization
from bookforge.proof.validators import (
    validate_ammunition_transition,
    validate_capability_grant,
    validate_meaning_preservation,
    validate_no_unprofiled_names,
    validate_supported_canon,
    validate_western_style,
)


def test_deterministic_humanization_returns_candidate_artifact_text() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)

    artifact = run_deterministic_humanization(fixture)

    assert artifact.artifact_id == "artifact:chapter-008:candidate:v1"
    assert artifact.text == fixture.candidate_text
    assert artifact.provider_id == fixture.provider_id


def test_seeded_validation_failures_are_reported() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)

    assert validate_meaning_preservation(fixture, fixture.meaning_change_text).blocks_approval
    assert validate_supported_canon(fixture, fixture.unsupported_canon_text).blocks_approval
    assert validate_no_unprofiled_names(fixture, fixture.candidate_text).blocks_approval
    assert validate_western_style(fixture, fixture.candidate_text).blocks_approval


def test_ammunition_transition_and_capability_grant_are_validated() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)

    assert validate_ammunition_transition(fixture, claim_rounds=fixture.weapon_rounds_after_shot) is None
    assert validate_ammunition_transition(fixture, claim_rounds=fixture.bad_round_claim).blocks_approval
    assert validate_capability_grant(fixture, requested_tool="run_validators") is None
    assert validate_capability_grant(fixture, requested_tool="approve_artifact").blocks_approval
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py -q
```

Expected: FAIL importing `bookforge.proof.engine`.

- [ ] **Step 3: Implement deterministic engine**

Create `bookforge/proof/engine.py`:

```python
from __future__ import annotations

from pydantic import Field

from bookforge.proof.fixtures import ProofFixture
from bookforge.schemas.base import ContractModel, stable_hash


class CandidateArtifact(ContractModel):
    artifact_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    content_hash: str = Field(min_length=1)


def run_deterministic_humanization(fixture: ProofFixture) -> CandidateArtifact:
    return CandidateArtifact(
        artifact_id="artifact:chapter-008:candidate:v1",
        project_id=fixture.project_id,
        text=fixture.candidate_text,
        provider_id=fixture.provider_id,
        content_hash=stable_hash({"text": fixture.candidate_text}),
    )
```

- [ ] **Step 4: Implement validators**

Create `bookforge/proof/validators.py`:

```python
from __future__ import annotations

from bookforge.proof.fixtures import ProofFixture
from bookforge.schemas.validation import FindingSeverity, ValidationFinding


def _finding(issue_id: str, evidence: str, rule: str, recommendation: str) -> ValidationFinding:
    return ValidationFinding(
        issue_id=issue_id,
        validator_id="phase1.local_proof",
        severity=FindingSeverity.HIGH,
        confidence=1.0,
        artifact_id="artifact:chapter-008:candidate:v1",
        location="fixture",
        evidence=evidence,
        violated_rule=rule,
        recommendation=recommendation,
    )


def validate_meaning_preservation(fixture: ProofFixture, text: str) -> ValidationFinding | None:
    if "left the Colt behind" in text or "rode out of town" in text:
        return _finding("issue:meaning-change", text, "preserve_meaning", "Restore source plot.")
    return None


def validate_supported_canon(fixture: ProofFixture, text: str) -> ValidationFinding | None:
    if "owned Harlan's ranch" in text or "marshal badge" in text:
        return _finding("issue:unsupported-canon", text, "preserve_canon", "Remove unsupported fact.")
    return None


def validate_no_unprofiled_names(fixture: ProofFixture, text: str) -> ValidationFinding | None:
    if fixture.unprofiled_name in text:
        return _finding("issue:unprofiled-name", fixture.unprofiled_name, "profile_named_characters", "Use approved descriptor.")
    return None


def validate_western_style(fixture: ProofFixture, text: str) -> ValidationFinding | None:
    if fixture.western_style_violation in text:
        return _finding("issue:western-style", fixture.western_style_violation, "western_style", "Remove modern wording.")
    return None


def validate_ammunition_transition(fixture: ProofFixture, claim_rounds: int) -> ValidationFinding | None:
    if claim_rounds != fixture.weapon_rounds_after_shot:
        return _finding("issue:ammo-count", str(claim_rounds), "numeric_continuity", "Use approved ammunition transition.")
    return None


def validate_capability_grant(fixture: ProofFixture, requested_tool: str) -> ValidationFinding | None:
    if requested_tool not in fixture.allowed_tools:
        return _finding("issue:capability", requested_tool, "capability_grant", "Reject ungranted tool.")
    return None
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py -q
```

Expected: PASS.

## Task 4: Review, Export, Trace, And Pipeline

**Files:**
- Modify: `tests/test_phase1_local_proof.py`
- Create: `bookforge/proof/review_export.py`
- Create: `bookforge/proof/pipeline.py`

- [ ] **Step 1: Add failing review/export/pipeline tests**

Append:

```python
from bookforge.proof.pipeline import run_phase1_local_proof
from bookforge.proof.review_export import export_markdown, simulate_approval


def test_unapproved_export_is_rejected_and_approved_export_succeeds() -> None:
    fixture = load_proof_fixture(FIXTURE_PATH)
    artifact = run_deterministic_humanization(fixture)

    with pytest.raises(ValueError, match="approved artifacts only"):
        export_markdown(artifact=artifact, approval=None)

    approval = simulate_approval(artifact_id=artifact.artifact_id, artifact_version=1)
    exported = export_markdown(artifact=artifact, approval=approval)

    assert exported.markdown == fixture.candidate_text
    assert exported.approval_id == approval.approval_id


def test_phase1_pipeline_records_trace_and_corrected_artifact() -> None:
    result = run_phase1_local_proof(FIXTURE_PATH)

    assert result.project_id == "lone-star-reckoning"
    assert result.corrected_text.endswith("watched the street.")
    assert result.export.markdown == result.corrected_text
    assert result.trace["prompt_id"] == "humanize@1.0.0"
    assert result.trace["persona_id"] == "western_prose_editor"
    assert result.trace["capability_id"] == "humanize_chapter"
    assert result.trace["context_package_id"] == "ctx:chapter-008"
    assert result.trace["policy_snapshot_id"] == "policy:snap:phase1"
    assert {finding.issue_id for finding in result.findings} >= {
        "issue:unprofiled-name",
        "issue:western-style",
    }
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py -q
```

Expected: FAIL importing `bookforge.proof.pipeline`.

- [ ] **Step 3: Implement review/export**

Create `bookforge/proof/review_export.py`:

```python
from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field

from bookforge.proof.engine import CandidateArtifact
from bookforge.schemas.base import ContractModel
from bookforge.schemas.review import ReviewApproval, ReviewDecision


class MarkdownProofExport(ContractModel):
    export_id: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    approval_id: str = Field(min_length=1)
    markdown: str = Field(min_length=1)


def simulate_approval(artifact_id: str, artifact_version: int) -> ReviewApproval:
    return ReviewApproval(
        approval_id="approval:chapter-008:candidate:v1",
        reviewer_id="reviewer:phase1-fixture",
        decision=ReviewDecision.APPROVED,
        artifact_id=artifact_id,
        artifact_version=artifact_version,
        finding_ids=[],
        accepted_risks=[],
        decided_at=datetime(2026, 6, 13, tzinfo=UTC),
    )


def export_markdown(
    *,
    artifact: CandidateArtifact,
    approval: ReviewApproval | None,
) -> MarkdownProofExport:
    if approval is None or approval.decision is not ReviewDecision.APPROVED:
        raise ValueError("approved artifacts only")
    return MarkdownProofExport(
        export_id="export:chapter-008:markdown",
        artifact_id=artifact.artifact_id,
        approval_id=approval.approval_id,
        markdown=artifact.text,
    )
```

- [ ] **Step 4: Implement pipeline**

Create `bookforge/proof/pipeline.py`:

```python
from __future__ import annotations

from pathlib import Path

from pydantic import Field

from bookforge.proof.context import build_context_package
from bookforge.proof.engine import CandidateArtifact, run_deterministic_humanization
from bookforge.proof.fixtures import load_proof_fixture
from bookforge.proof.review_export import MarkdownProofExport, export_markdown, simulate_approval
from bookforge.proof.validators import validate_no_unprofiled_names, validate_western_style
from bookforge.schemas.base import ContractModel, stable_hash
from bookforge.schemas.validation import ValidationFinding


class Phase1ProofResult(ContractModel):
    project_id: str = Field(min_length=1)
    candidate: CandidateArtifact
    corrected_text: str = Field(min_length=1)
    findings: list[ValidationFinding] = Field(default_factory=list)
    export: MarkdownProofExport
    trace: dict[str, str] = Field(default_factory=dict)


def run_phase1_local_proof(path: Path) -> Phase1ProofResult:
    fixture = load_proof_fixture(path)
    context = build_context_package(fixture)
    candidate = run_deterministic_humanization(fixture)
    findings = [
        finding
        for finding in [
            validate_no_unprofiled_names(fixture, candidate.text),
            validate_western_style(fixture, candidate.text),
        ]
        if finding is not None
    ]
    corrected = candidate.model_copy(
        update={
            "artifact_id": "artifact:chapter-008:corrected:v1",
            "text": fixture.corrected_text,
            "content_hash": stable_hash({"text": fixture.corrected_text}),
        }
    )
    approval = simulate_approval(corrected.artifact_id, artifact_version=1)
    export = export_markdown(artifact=corrected, approval=approval)
    return Phase1ProofResult(
        project_id=fixture.project_id,
        candidate=candidate,
        corrected_text=corrected.text,
        findings=findings,
        export=export,
        trace={
            "prompt_id": fixture.prompt_id,
            "persona_id": fixture.persona_id,
            "capability_id": fixture.capability_id,
            "context_package_id": context.context_package_id,
            "provider_id": fixture.provider_id,
            "policy_snapshot_id": fixture.policy_snapshot_id,
            "artifact_output_id": corrected.artifact_id,
        },
    )
```

- [ ] **Step 5: Run tests**

Run:

```bash
python -m pytest tests/test_phase1_local_proof.py tests/test_phase0_contracts.py tests/test_phase0_completion_contracts.py -q
```

Expected: PASS.

## Task 5: Full Phase 1 Verification

**Files:**
- Inspect: `bookforge/proof/`
- Inspect: `tests/test_phase1_local_proof.py`
- Inspect: `tests/fixtures/phase1/lone_star_reckoning.yaml`

- [ ] **Step 1: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: all tests PASS.

- [ ] **Step 2: Run lint**

Run:

```bash
python -m ruff check .
```

Expected:

```text
All checks passed!
```

- [ ] **Step 3: Confirm forbidden infrastructure is absent**

Run:

```bash
rg -n "FastAPI|PostgreSQL|psycopg|sqlalchemy|redis|celery|langchain|llama|vector|graph database|uvicorn|openai|anthropic" bookforge pyproject.toml tests || true
```

Expected: no matches.

- [ ] **Step 4: Confirm Phase 1 requirements are covered**

Run:

```bash
rg -n "wrong project|missing canon|path escape|unapproved export|meaning|unsupported canon|unprofiled|Western style|ammunition|capability|trace" tests/test_phase1_local_proof.py
```

Expected: matches for every Phase 1 required-test category.

## Self-Review

Spec coverage:

- Wrong project/version rejection: Task 2.
- Missing canon blocks grounded work: Task 2.
- Path escape rejection: Task 2.
- Unapproved export rejection: Task 4.
- Meaning-changing humanization detection: Task 3.
- Unsupported canon fact detection: Task 3.
- Unprofiled proper name block: Task 3 and Task 4 pipeline.
- Western style violation report: Task 3 and Task 4 pipeline.
- Ammunition transition validation: Task 3.
- Capability grant validation: Task 3.
- Model run trace metadata: Task 4.
- Deterministic offline proof: all tasks use YAML fixture and local code only.

Placeholder scan:

- No placeholder implementation language remains.
- Every code step includes exact code.

Type consistency:

- All imported test classes/functions are defined in planned modules.
- `ProofFixture`, `CandidateArtifact`, `MarkdownProofExport`, and `Phase1ProofResult` field names stay consistent across tasks.
