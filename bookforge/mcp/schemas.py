"""MCP tool input/output schemas as dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    ok: bool
    tool: str
    error_code: str | None = None
    message: str | None = None
    hint: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"ok": self.ok, "tool": self.tool}
        if self.error_code:
            d["error_code"] = self.error_code
        if self.message:
            d["message"] = self.message
        if self.hint:
            d["hint"] = self.hint
        if self.data:
            d.update(self.data)
        return d


def queue_status_result(
    book: str,
    active_scene: str | None,
    counts: dict[str, int],
    scenes: list[dict[str, Any]] | None = None,
) -> ToolResult:
    data: dict[str, Any] = {
        "book": book,
        "active_scene": active_scene,
        "counts": counts,
    }
    if scenes is not None:
        data["scenes"] = scenes
    return ToolResult(ok=True, tool="get_queue_status", data=data)


def active_scene_result(
    scene: str,
    chapter: str,
    scene_id: str,
    status: str,
    provider: str,
    target_words: int,
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="get_active_scene",
        data={
            "scene": scene,
            "chapter": chapter,
            "scene_id": scene_id,
            "status": status,
            "provider": provider,
            "target_words": target_words,
        },
    )


def generation_packet_result(
    scene: str,
    packet_path: str,
    packet_tokens: int,
    target_words: int,
    packet_text: str | None = None,
) -> ToolResult:
    data: dict[str, Any] = {
        "scene": scene,
        "packet_path": packet_path,
        "packet_tokens": packet_tokens,
        "target_words": target_words,
        "status": "generation_packet_ready",
    }
    if packet_text is not None:
        data["packet_text"] = packet_text
    return ToolResult(ok=True, tool="build_generation_packet", data=data)


def project_kit_result(
    provider: str,
    kit_path: str,
    active_files: list[str],
    stable_files: list[str],
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="build_project_kit",
        data={
            "provider": provider,
            "kit_path": kit_path,
            "active_files": active_files,
            "stable_files": stable_files,
        },
    )


def validation_result(
    scene: str,
    status: str,
    failures: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="validate_scene",
        data={
            "scene": scene,
            "status": status,
            "failures": failures,
            "warnings": warnings,
        },
    )


def patch_packet_result(
    scene: str,
    patch_packet_path: str,
    patch_tokens: int,
    targets: list[dict[str, Any]],
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="build_patch_packet",
        data={
            "scene": scene,
            "patch_packet_path": patch_packet_path,
            "patch_tokens": patch_tokens,
            "targets": targets,
        },
    )


def save_draft_result(
    draft_path: str,
    word_count: int,
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="save_draft",
        data={
            "draft_path": draft_path,
            "word_count": word_count,
        },
    )


def apply_patch_result(
    draft_path: str,
    validation_after_apply: str,
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="apply_patch",
        data={
            "draft_path": draft_path,
            "validation_after_apply": validation_after_apply,
        },
    )


def scene_report_result(
    scene: str,
    status: str | None,
    validation_path: str | None,
    draft_path: str | None,
    word_count: int | None,
    failures: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="get_scene_report",
        data={
            "scene": scene,
            "status": status,
            "validation_path": validation_path,
            "draft_path": draft_path,
            "word_count": word_count,
            "failures": failures,
            "warnings": warnings,
        },
    )


def research_cache_result(
    entries: list[dict[str, Any]],
    query: str,
) -> ToolResult:
    return ToolResult(
        ok=True,
        tool="query_research_cache",
        data={
            "entries": entries,
            "query": query,
        },
    )
