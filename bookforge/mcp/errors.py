"""MCP error code constants and helpers."""

from __future__ import annotations

from bookforge.mcp.schemas import ToolResult


# Error codes
QUEUE_BLOCKED = "QUEUE_BLOCKED"
NO_ACTIVE_SCENE = "NO_ACTIVE_SCENE"
QUEUE_INVARIANT_VIOLATION = "QUEUE_INVARIANT_VIOLATION"
READONLY_MODE = "READONLY_MODE"
INVALID_REPLACEMENT = "INVALID_REPLACEMENT"
SCENE_NOT_FOUND = "SCENE_NOT_FOUND"
VALIDATION_FAILED = "VALIDATION_FAILED"
PATCH_FAILED = "PATCH_FAILED"
MISSING_PACKET = "MISSING_PACKET"
MISSING_MANIFEST = "MISSING_MANIFEST"
BUILD_ERROR = "BUILD_ERROR"
PROVIDER_ERROR = "PROVIDER_ERROR"


def error_result(
    tool: str,
    code: str,
    message: str,
    hint: str | None = None,
) -> ToolResult:
    return ToolResult(
        ok=False,
        tool=tool,
        error_code=code,
        message=message,
        hint=hint,
    )
