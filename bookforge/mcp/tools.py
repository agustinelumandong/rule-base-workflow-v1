"""MCP tool implementations wrapping core BookForge functions."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from bookforge.mcp.errors import (
    BUILD_ERROR,
    INVALID_REPLACEMENT,
    MISSING_MANIFEST,
    MISSING_PACKET,
    NO_ACTIVE_SCENE,
    PATCH_FAILED,
    QUEUE_BLOCKED,
    QUEUE_INVARIANT_VIOLATION,
    READONLY_MODE,
    SCENE_NOT_FOUND,
    VALIDATION_FAILED,
    error_result,
)
from bookforge.mcp.schemas import (
    ToolResult,
    active_scene_result,
    apply_patch_result,
    generation_packet_result,
    patch_packet_result,
    project_kit_result,
    queue_status_result,
    research_cache_result,
    save_draft_result,
    scene_report_result,
    validation_result,
)


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    normalized = []
    for line in lines:
        normalized.append(line.rstrip())
    return "\n".join(normalized).strip() + "\n"


def _parse_scene_key(chapter: str | None, scene: str | None) -> tuple[str, str] | None:
    if chapter and scene:
        return chapter, scene
    return None


def _resolve_active_scene(book_folder: Path) -> dict | None:
    from bookforge.core.queue import load_queue

    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])
    active_statuses = {
        "generation_packet_ready",
        "ready_for_validation",
        "validation_failed",
        "patch_packet_ready",
    }
    active = [s for s in scenes if s["status"] in active_statuses]
    if len(active) == 1:
        return active[0]
    return None


def get_queue_status(book_folder: Path, args: dict) -> ToolResult:
    from collections import Counter
    from bookforge.core.queue import load_queue

    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])
    counts = dict(Counter(s["status"] for s in scenes))

    active_scene = None
    active_list = [
        s for s in scenes
        if s["status"] not in ("clean", "validation_passed", "committed", "ready_for_generation")
    ]
    if len(active_list) == 1:
        active_scene = active_list[0]["scene_key"]
    elif len(active_list) > 1:
        active_scene = "QUEUE_INVARIANT_VIOLATION"

    include_scenes = args.get("include_scenes", False)
    scene_list = None
    if include_scenes:
        scene_list = [
            {
                "scene_key": s["scene_key"],
                "status": s["status"],
                "provider": s.get("provider", "manual-web"),
                "target_words": s.get("target_words", 3500),
            }
            for s in scenes
        ]

    return queue_status_result(
        book=book_folder.name,
        active_scene=active_scene,
        counts=counts,
        scenes=scene_list,
    )


def get_active_scene(book_folder: Path, args: dict) -> ToolResult:
    from bookforge.core.queue import load_queue

    queue_data = load_queue(book_folder)
    scenes = queue_data.get("scenes", [])
    active_statuses = {
        "generation_packet_ready",
        "ready_for_validation",
        "validation_failed",
        "patch_packet_ready",
    }
    active = [s for s in scenes if s["status"] in active_statuses]

    if not active:
        return error_result(
            "get_active_scene",
            NO_ACTIVE_SCENE,
            "No scene is currently active in the queue.",
            hint="Run get_queue_status to see all scenes and their statuses.",
        )

    if len(active) > 1:
        keys = [s["scene_key"] for s in active]
        return error_result(
            "get_active_scene",
            QUEUE_INVARIANT_VIOLATION,
            f"Multiple active scenes detected: {', '.join(keys)}.",
            hint="Queue invariant requires exactly one active scene.",
        )

    s = active[0]
    parts = s["scene_key"].split("/")
    return active_scene_result(
        scene=s["scene_key"],
        chapter=parts[0],
        scene_id=parts[1],
        status=s["status"],
        provider=s.get("provider", "manual-web"),
        target_words=s.get("target_words", 3500),
    )


def build_generation_packet(book_folder: Path, args: dict) -> ToolResult:
    from bookforge.core.packet.builder import build_scene_packet, estimate_tokens
    from bookforge.core.packet.helpers import scene_folder
    from bookforge.core.queue import load_queue, update_queue_scene, verify_scene_runnable

    chapter = args.get("chapter")
    scene_id = args.get("scene")
    task = args.get("task", "draft-prose")
    force = args.get("force", False)
    include_text = args.get("include_text", False)

    if not chapter or not scene_id:
        active = _resolve_active_scene(book_folder)
        if not active:
            return error_result(
                "build_generation_packet",
                NO_ACTIVE_SCENE,
                "No chapter/scene specified and no active scene in queue.",
                hint="Provide chapter and scene arguments, or ensure an active scene exists.",
            )
        parts = active["scene_key"].split("/")
        chapter, scene_id = parts[0], parts[1]

    scene_key = f"{chapter}/{scene_id}"

    queue_data = load_queue(book_folder)
    scene_entry = None
    for s in queue_data.get("scenes", []):
        if s["scene_key"] == scene_key:
            scene_entry = s
            break

    target_words = 3500
    if scene_entry:
        target_words = scene_entry.get("target_words", 3500)

    is_this_scene_active = scene_entry is not None and scene_entry["status"] == "generation_packet_ready"
    if not force and not is_this_scene_active:
        if not verify_scene_runnable(book_folder, scene_key, force=False):
            return error_result(
                "build_generation_packet",
                QUEUE_BLOCKED,
                f"Scene '{scene_key}' is blocked by queue rules.",
                hint="Use force=true only for debugging. Check dependencies in get_queue_status.",
            )

    try:
        markdown = build_scene_packet(book_folder, chapter, scene_id)
    except Exception as e:
        return error_result("build_generation_packet", BUILD_ERROR, str(e))

    folder = scene_folder(book_folder, chapter, scene_id)
    folder.mkdir(parents=True, exist_ok=True)
    out_path = folder / "generation-packet.md"
    out_path.write_text(markdown, encoding="utf-8")

    try:
        update_queue_scene(
            book_folder,
            scene_key,
            status="generation_packet_ready",
            inc_generation=True,
        )
    except Exception:
        pass

    tokens = estimate_tokens(markdown)
    result = generation_packet_result(
        scene=scene_key,
        packet_path=str(out_path),
        packet_tokens=tokens,
        target_words=target_words,
    )
    if include_text:
        result.data["packet_text"] = markdown
    return result


def build_project_kit(book_folder: Path, args: dict) -> ToolResult:
    from bookforge.core.projectkit import build_project_kit as _build, project_kit_folder, PROVIDERS

    provider = args.get("provider", "chatgpt")
    if provider not in PROVIDERS:
        return error_result(
            "build_project_kit",
            BUILD_ERROR,
            f"Unknown provider '{provider}'. Must be one of: {', '.join(PROVIDERS)}",
        )

    try:
        kit_dir = _build(book_folder, provider)
    except Exception as e:
        return error_result("build_project_kit", BUILD_ERROR, str(e))

    active_files = []
    active_dir = kit_dir / "active"
    if active_dir.exists():
        active_files = sorted(str(p.relative_to(kit_dir)) for p in active_dir.iterdir() if p.is_file())

    stable_files = sorted(
        str(p.relative_to(kit_dir))
        for p in kit_dir.iterdir()
        if p.is_file() and p.name[0].isdigit()
    )

    return project_kit_result(
        provider=provider,
        kit_path=str(kit_dir),
        active_files=active_files,
        stable_files=stable_files,
    )


def validate_scene(book_folder: Path, args: dict) -> ToolResult:
    from bookforge.core.scene import parse_scene_id, load_scene_manifest
    from bookforge.core.packet.helpers import scene_folder
    from bookforge.core.validators.orchestration import validate_scene as _validate
    from bookforge.core.issue import Severity

    chapter = args.get("chapter")
    scene_id = args.get("scene")

    if not chapter or not scene_id:
        active = _resolve_active_scene(book_folder)
        if not active:
            return error_result(
                "validate_scene",
                NO_ACTIVE_SCENE,
                "No chapter/scene specified and no active scene in queue.",
            )
        parts = active["scene_key"].split("/")
        chapter, scene_id = parts[0], parts[1]

    scene_key = f"{chapter}/{scene_id}"
    s_folder = scene_folder(book_folder, chapter, scene_id)
    m_path = s_folder / "manifest.yml"
    if not m_path.exists():
        m_path = book_folder / "changes" / chapter / "scenes" / scene_id / "manifest.yml"
    if not m_path.exists():
        return error_result(
            "validate_scene",
            MISSING_MANIFEST,
            f"Scene manifest not found for {scene_key}.",
        )

    manifest = load_scene_manifest(m_path, book_folder)

    try:
        issues = _validate(manifest)
    except Exception as e:
        return error_result("validate_scene", BUILD_ERROR, str(e))

    failures = []
    warnings = []
    for issue in issues:
        entry = {
            "rule_id": issue.rule_id,
            "message": issue.message,
        }
        if issue.span:
            entry["span"] = issue.span
        if issue.severity == Severity.HARD:
            failures.append(entry)
        else:
            warnings.append(entry)

    status = "validation_failed" if failures else "validation_passed"

    try:
        val_json = s_folder / "validation.json"
        val_json.write_text(
            json.dumps({"status": "clean" if status == "validation_passed" else "failed", "scene": scene_key}),
            encoding="utf-8",
        )
    except Exception:
        pass

    return validation_result(
        scene=scene_key,
        status=status,
        failures=failures,
        warnings=warnings,
    )


def build_patch_packet(book_folder: Path, args: dict) -> ToolResult:
    from bookforge.core.scene import load_scene_manifest
    from bookforge.core.packet.helpers import scene_folder
    from bookforge.core.patch import build_patch_packet as _build_patch

    chapter = args.get("chapter")
    scene_id = args.get("scene")
    failed_rules = args.get("failed_rules", [])

    if not chapter or not scene_id:
        active = _resolve_active_scene(book_folder)
        if not active:
            return error_result(
                "build_patch_packet",
                NO_ACTIVE_SCENE,
                "No chapter/scene specified and no active scene in queue.",
            )
        parts = active["scene_key"].split("/")
        chapter, scene_id = parts[0], parts[1]

    scene_key = f"{chapter}/{scene_id}"
    s_folder = scene_folder(book_folder, chapter, scene_id)
    m_path = s_folder / "manifest.yml"
    if not m_path.exists():
        m_path = book_folder / "changes" / chapter / "scenes" / scene_id / "manifest.yml"
    if not m_path.exists():
        return error_result(
            "build_patch_packet",
            MISSING_MANIFEST,
            f"Scene manifest not found for {scene_key}.",
        )

    manifest = load_scene_manifest(m_path, book_folder)

    if not failed_rules:
        val_json = s_folder / "validation.json"
        if val_json.exists():
            try:
                val_data = json.loads(val_json.read_text(encoding="utf-8"))
                failed_rules = val_data.get("failures", [])
            except Exception:
                pass

    if not failed_rules:
        return error_result(
            "build_patch_packet",
            VALIDATION_FAILED,
            f"No failed rules specified or found for {scene_key}.",
            hint="Run validate_scene first, or provide failed_rules explicitly.",
        )

    try:
        patch_text = _build_patch(manifest, failed_rules)
    except Exception as e:
        return error_result("build_patch_packet", BUILD_ERROR, str(e))

    patch_path = s_folder / "patch-packet.md"
    patch_path.write_text(patch_text, encoding="utf-8")

    targets = [{"rule_id": rule} for rule in failed_rules]

    return patch_packet_result(
        scene=scene_key,
        patch_packet_path=str(patch_path),
        patch_tokens=_estimate_tokens(patch_text),
        targets=targets,
    )


def save_draft(book_folder: Path, args: dict, readonly: bool = True) -> ToolResult:
    if readonly:
        return error_result(
            "save_draft",
            READONLY_MODE,
            "Server is in readonly mode. Draft writes are not allowed.",
            hint="Restart server with --allow-write to enable draft writes.",
        )

    from bookforge.core.packet.helpers import scene_folder
    from bookforge.core.queue import load_queue, update_queue_scene

    chapter = args.get("chapter")
    scene_id = args.get("scene")
    text = args.get("text", "")

    if not chapter or not scene_id:
        active = _resolve_active_scene(book_folder)
        if not active:
            return error_result(
                "save_draft",
                NO_ACTIVE_SCENE,
                "No chapter/scene specified and no active scene in queue.",
            )
        parts = active["scene_key"].split("/")
        chapter, scene_id = parts[0], parts[1]

    scene_key = f"{chapter}/{scene_id}"

    queue_data = load_queue(book_folder)
    scene_entry = None
    for s in queue_data.get("scenes", []):
        if s["scene_key"] == scene_key:
            scene_entry = s
            break

    if not scene_entry:
        return error_result(
            "save_draft",
            SCENE_NOT_FOUND,
            f"Scene '{scene_key}' not found in queue.",
        )

    if scene_entry["status"] not in ("generation_packet_ready", "ready_for_validation", "validation_failed"):
        force = args.get("force", False)
        if not force:
            return error_result(
                "save_draft",
                QUEUE_BLOCKED,
                f"Scene '{scene_key}' has status '{scene_entry['status']}', not ready for draft save.",
                hint="Use force=true to override queue rules (debug only).",
            )

    if not text.strip():
        return error_result(
            "save_draft",
            BUILD_ERROR,
            "Draft text is empty.",
        )

    normalized = _normalize_text(text)

    s_folder = scene_folder(book_folder, chapter, scene_id)
    s_folder.mkdir(parents=True, exist_ok=True)
    draft_path = s_folder / "draft.md"
    draft_path.write_text(normalized, encoding="utf-8")

    word_count = len(re.findall(r"\b\w+\b", normalized))

    try:
        update_queue_scene(book_folder, scene_key, status="ready_for_validation")
    except Exception:
        pass

    return save_draft_result(
        draft_path=str(draft_path),
        word_count=word_count,
    )


def apply_patch(book_folder: Path, args: dict, readonly: bool = True) -> ToolResult:
    if readonly:
        return error_result(
            "apply_patch",
            READONLY_MODE,
            "Server is in readonly mode. Patch writes are not allowed.",
            hint="Restart server with --allow-write to enable patch writes.",
        )

    from bookforge.core.packet.helpers import scene_folder
    from bookforge.core.patch import splice_prose, validate_merged_prose
    from bookforge.core.scene import load_scene_manifest
    from bookforge.core.queue import update_queue_scene

    chapter = args.get("chapter")
    scene_id = args.get("scene")
    replacement_text = args.get("replacement_text", "")

    if not chapter or not scene_id:
        active = _resolve_active_scene(book_folder)
        if not active:
            return error_result(
                "apply_patch",
                NO_ACTIVE_SCENE,
                "No chapter/scene specified and no active scene in queue.",
            )
        parts = active["scene_key"].split("/")
        chapter, scene_id = parts[0], parts[1]

    scene_key = f"{chapter}/{scene_id}"
    s_folder = scene_folder(book_folder, chapter, scene_id)

    draft_path = s_folder / "draft.md"
    if not draft_path.exists():
        return error_result(
            "apply_patch",
            INVALID_REPLACEMENT,
            f"No draft found at {draft_path}. Cannot apply patch to missing draft.",
        )

    original = draft_path.read_text(encoding="utf-8")

    if not replacement_text.strip():
        return error_result(
            "apply_patch",
            INVALID_REPLACEMENT,
            "Replacement text is empty.",
        )

    success, merged = splice_prose(original, replacement_text)
    if not success:
        return error_result(
            "apply_patch",
            INVALID_REPLACEMENT,
            f"Failed to splice replacement into draft: {merged}",
            hint="Ensure replacement contains anchor lines from the original draft.",
        )

    m_path = s_folder / "manifest.yml"
    if not m_path.exists():
        m_path = book_folder / "changes" / chapter / "scenes" / scene_id / "manifest.yml"
    target_words = 3500
    if m_path.exists():
        try:
            manifest = load_scene_manifest(m_path, book_folder)
            target_words = manifest.target_words
        except Exception:
            pass

    validation_errors = validate_merged_prose(merged, target_words)
    if validation_errors:
        return error_result(
            "apply_patch",
            PATCH_FAILED,
            f"Post-apply validation failed: {'; '.join(validation_errors)}",
        )

    draft_path.write_text(merged, encoding="utf-8")

    validation_status = "validation_passed"

    from bookforge.core.validators.orchestration import validate_scene as _validate
    from bookforge.core.scene import load_scene_manifest as _load_manifest

    if m_path.exists():
        try:
            manifest = _load_manifest(m_path, book_folder)
            issues = _validate(manifest)
            from bookforge.core.issue import Severity
            hard_failures = [i for i in issues if i.severity == Severity.HARD]
            if hard_failures:
                validation_status = "validation_failed"
        except Exception:
            pass

    try:
        update_queue_scene(book_folder, scene_key, status=validation_status)
    except Exception:
        pass

    return apply_patch_result(
        draft_path=str(draft_path),
        validation_after_apply=validation_status,
    )


def get_scene_report(book_folder: Path, args: dict) -> ToolResult:
    from bookforge.core.packet.helpers import scene_folder, scene_draft_path
    from bookforge.core.scene import load_scene_manifest
    from bookforge.core.queue import load_queue
    from bookforge.core.issue import Severity

    chapter = args.get("chapter")
    scene_id = args.get("scene")

    if not chapter or not scene_id:
        active = _resolve_active_scene(book_folder)
        if not active:
            return error_result(
                "get_scene_report",
                NO_ACTIVE_SCENE,
                "No chapter/scene specified and no active scene in queue.",
            )
        parts = active["scene_key"].split("/")
        chapter, scene_id = parts[0], parts[1]

    scene_key = f"{chapter}/{scene_id}"
    s_folder = scene_folder(book_folder, chapter, scene_id)

    m_path = s_folder / "manifest.yml"
    if not m_path.exists():
        m_path = book_folder / "changes" / chapter / "scenes" / scene_id / "manifest.yml"
    if not m_path.exists():
        return error_result(
            "get_scene_report",
            MISSING_MANIFEST,
            f"Scene manifest not found for {scene_key}.",
        )

    manifest = load_scene_manifest(m_path, book_folder)

    draft_p = scene_draft_path(s_folder, scene_id)
    word_count = None
    if draft_p.exists():
        try:
            word_count = len(draft_p.read_text(encoding="utf-8").split())
        except Exception:
            pass

    val_json = s_folder / "validation.json"
    status = manifest.status
    failures = []
    warnings = []
    if val_json.exists():
        try:
            val_data = json.loads(val_json.read_text(encoding="utf-8"))
            status = "validation_passed" if val_data.get("status") == "clean" else "validation_failed"
        except Exception:
            pass

    try:
        from bookforge.core.validators.orchestration import validate_scene as _validate
        issues = _validate(manifest)
        for issue in issues:
            entry = {"rule_id": issue.rule_id, "message": issue.message}
            if issue.span:
                entry["span"] = issue.span
            if issue.severity == Severity.HARD:
                failures.append(entry)
            else:
                warnings.append(entry)
    except Exception:
        pass

    q_data = load_queue(book_folder)
    for s in q_data.get("scenes", []):
        if s["scene_key"] == scene_key:
            status = s["status"]
            break

    return scene_report_result(
        scene=scene_key,
        status=status,
        validation_path=str(val_json) if val_json.exists() else None,
        draft_path=str(draft_p) if draft_p.exists() else None,
        word_count=word_count,
        failures=failures,
        warnings=warnings,
    )


def query_research_cache(book_folder: Path, args: dict) -> ToolResult:
    from bookforge.core.research_cache import lookup_research_cache, normalize_research_key

    query = args.get("query", "")
    category = args.get("category", "general")
    key = args.get("key")

    if not key and query:
        key = normalize_research_key(query, category)

    if not key:
        return error_result(
            "query_research_cache",
            BUILD_ERROR,
            "Either 'query' or 'key' must be provided.",
        )

    entry = lookup_research_cache(book_folder, key)
    if not entry:
        return research_cache_result(entries=[], query=query or key)

    return research_cache_result(
        entries=[entry.to_dict()],
        query=query or key,
    )
