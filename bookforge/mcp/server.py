"""MCP stdio/http server exposing BookForge operations as tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bookforge.mcp import tools as mcp_tools


INSTRUCTIONS = (
    "BookForge is the source-of-truth production system for novel generation. "
    "Use tools to inspect queue, build packets, validate drafts, and create/apply patches. "
    "Do not generate long-form prose through Codex. Long prose must come from provider-web lane. "
    "In readonly mode, do not attempt draft or patch writes."
)

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_queue_status",
        "description": "Returns queue summary with scene counts by status and the currently active scene.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_scenes": {
                    "type": "boolean",
                    "description": "Include full scene list in output.",
                    "default": False,
                }
            },
        },
    },
    {
        "name": "get_active_scene",
        "description": "Returns exactly one active scene from the queue. Fails if zero or multiple active scenes exist.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "build_generation_packet",
        "description": "Build a context packet for scene-level drafting. Writes packet to disk and returns its path and token count.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "string", "description": "Chapter slug (e.g. chapter-10). Uses active scene if omitted."},
                "scene": {"type": "string", "description": "Scene ID (e.g. scene-01). Uses active scene if omitted."},
                "task": {"type": "string", "description": "Task type: draft-prose, continuity-check, etc.", "default": "draft-prose"},
                "force": {"type": "boolean", "description": "Bypass queue dependency checks.", "default": False},
                "include_text": {"type": "boolean", "description": "Include full packet text in response.", "default": False},
            },
        },
    },
    {
        "name": "build_project_kit",
        "description": "Build provider-ready context folder (project kit) with stable and active files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "Provider: chatgpt, claude, gemini, generic.", "default": "chatgpt"},
            },
        },
    },
    {
        "name": "validate_scene",
        "description": "Run deterministic validation on a scene draft. Returns failures and warnings with rule IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "string", "description": "Chapter slug. Uses active scene if omitted."},
                "scene": {"type": "string", "description": "Scene ID. Uses active scene if omitted."},
            },
        },
    },
    {
        "name": "build_patch_packet",
        "description": "Build a patch packet for failed validation rules. Returns path and target paragraph ranges.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "string", "description": "Chapter slug. Uses active scene if omitted."},
                "scene": {"type": "string", "description": "Scene ID. Uses active scene if omitted."},
                "failed_rules": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of failed rule IDs. Auto-detected from validation.json if omitted.",
                },
            },
        },
    },
    {
        "name": "save_draft",
        "description": "Write normalized prose to a scene draft. Requires write mode. Updates queue status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "string", "description": "Chapter slug. Uses active scene if omitted."},
                "scene": {"type": "string", "description": "Scene ID. Uses active scene if omitted."},
                "text": {"type": "string", "description": "Prose text to save as draft."},
                "force": {"type": "boolean", "description": "Bypass queue status checks.", "default": False},
            },
            "required": ["text"],
        },
    },
    {
        "name": "apply_patch",
        "description": "Splice replacement prose into an existing draft. Requires write mode. Validates before and after.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "string", "description": "Chapter slug. Uses active scene if omitted."},
                "scene": {"type": "string", "description": "Scene ID. Uses active scene if omitted."},
                "replacement_text": {"type": "string", "description": "Replacement prose with anchor lines for splicing."},
            },
            "required": ["replacement_text"],
        },
    },
    {
        "name": "get_scene_report",
        "description": "Return scene metrics: word count, validation status, failures, warnings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chapter": {"type": "string", "description": "Chapter slug. Uses active scene if omitted."},
                "scene": {"type": "string", "description": "Scene ID. Uses active scene if omitted."},
            },
        },
    },
    {
        "name": "query_research_cache",
        "description": "Look up a research cache entry by key or query string.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural language research query."},
                "category": {"type": "string", "description": "Research category.", "default": "general"},
                "key": {"type": "string", "description": "Exact cache key (category/slug). Overrides query."},
            },
        },
    },
]


class BookForgeMCPServer:
    """Model Context Protocol server exposing BookForge operations as tools."""

    def __init__(
        self,
        book_folder: Path,
        readonly: bool = True,
        allow_write: bool = False,
        force: bool = False,
    ) -> None:
        self.book_folder = book_folder
        self.readonly = readonly
        self.allow_write = allow_write
        self.force = force

    def _is_write_tool(self, name: str) -> bool:
        return name in ("save_draft", "apply_patch")

    def _tool_dispatch(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._is_write_tool(name) and self.readonly:
            from bookforge.mcp.errors import error_result as _err, READONLY_MODE
            result = _err(name, READONLY_MODE, "Server is in readonly mode.", hint="Restart with --allow-write.")
            return {"content": [{"type": "text", "text": json.dumps(result.to_dict())}]}

        if name not in {t["name"] for t in TOOL_SCHEMAS}:
            from bookforge.mcp.errors import error_result as _err, BUILD_ERROR
            result = _err(name, BUILD_ERROR, f"Unknown tool: {name}")
            return {"content": [{"type": "text", "text": json.dumps(result.to_dict())}]}

        fn = getattr(mcp_tools, name, None)
        if fn is None:
            from bookforge.mcp.errors import error_result as _err, BUILD_ERROR
            result = _err(name, BUILD_ERROR, f"Tool '{name}' has no implementation.")
            return {"content": [{"type": "text", "text": json.dumps(result.to_dict())}]}

        try:
            if self._is_write_tool(name):
                result = fn(self.book_folder, arguments, readonly=False)
            else:
                result = fn(self.book_folder, arguments)
        except Exception as e:
            from bookforge.mcp.errors import error_result as _err, BUILD_ERROR
            result = _err(name, BUILD_ERROR, str(e))

        return {"content": [{"type": "text", "text": json.dumps(result.to_dict())}]}

    def list_tools(self) -> list[dict[str, Any]]:
        return TOOL_SCHEMAS

    def _handle_request(self, req: dict) -> dict:
        method = req.get("method")
        req_id = req.get("id")

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "bookforge", "version": "1.0.0"},
                "instructions": INSTRUCTIONS,
            }
        elif method == "notifications/initialized":
            return {}
        elif method == "tools/list":
            result = {"tools": self.list_tools()}
        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            result = self._tool_dispatch(tool_name, arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def run_stdio(self) -> None:
        """Run the MCP server over standard input/output using JSON-RPC 2.0."""
        import sys
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                res = self._handle_request(req)
                if res:
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()
            except (json.JSONDecodeError, KeyError, AttributeError, TypeError, ValueError, OSError) as e:
                sys.stderr.write(f"MCP Stdio Error: {e}\n")
                sys.stderr.flush()

    def run_http(self, port: int = 8765, host: str = "127.0.0.1") -> None:
        """Run a simple HTTP server for JSON-RPC MCP calls."""
        from http.server import BaseHTTPRequestHandler, HTTPServer

        server_self = self

        class MCPHTTPHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                try:
                    req = json.loads(body.decode("utf-8"))
                    res = server_self._handle_request(req)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(res).encode("utf-8"))
                except (json.JSONDecodeError, KeyError, AttributeError, TypeError, ValueError, OSError) as e:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(str(e).encode("utf-8"))

            def log_message(self, format, *args):
                pass

        httpd = HTTPServer((host, port), MCPHTTPHandler)
        print(f"BookForge MCP HTTP Server listening on http://{host}:{port}")
        httpd.serve_forever()
