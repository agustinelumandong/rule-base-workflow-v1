"""MCP stdio/http server exposing memory backend as tools."""

from __future__ import annotations

import json
from typing import Any

from bookforge.core.memory.models import MemoryBackend


class MemoryMCPServer:
    """Model Context Protocol server exposing memory backend as tools."""

    def __init__(self, backend: MemoryBackend) -> None:
        self.backend = backend

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "headroom_retrieve",
                "description": "Semantic search across persistent book memory chunks (canon, outline, rules, drafts).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Query string to search for."},
                        "limit": {"type": "integer", "description": "Max results to return.", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "headroom_stats",
                "description": "Return database statistics and count of stored memory chunks.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "headroom_retrieve":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            chunks = self.backend.retrieve(query, limit=limit)
            if not chunks:
                return {"content": [{"type": "text", "text": "No matching memories found."}]}
            lines = [
                f"{i}. [score={c.score:.3f}] [src={c.metadata.get('source', 'unknown')}] {c.content}"
                for i, c in enumerate(chunks, start=1)
            ]
            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

        if name == "headroom_stats":
            st = self.backend.stats()
            stats_str = f"Backend: {st.backend_type}\nDatabase Path: {st.db_path}\nIndexed Chunks: {st.num_memories}"
            return {"content": [{"type": "text", "text": stats_str}]}

        return {"error": f"Unknown tool: {name}"}

    def _handle_request(self, req: dict) -> dict:
        method = req.get("method")
        req_id = req.get("id")

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "bookforge-memory", "version": "1.0.0"}
            }
        elif method == "tools/list":
            result = {"tools": self.list_tools()}
        elif method == "tools/call":
            params = req.get("params", {})
            result = self.call_tool(params.get("name"), params.get("arguments", {}))
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
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
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            except (json.JSONDecodeError, KeyError, AttributeError, TypeError, ValueError, OSError) as e:
                sys.stderr.write(f"MCP Stdio Error: {e}\n")
                sys.stderr.flush()

    def run_http(self, port: int = 8000) -> None:
        """Run a simple, zero-dependency HTTP server for JSON-RPC MCP calls."""
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

        httpd = HTTPServer(("localhost", port), MCPHTTPHandler)
        print(f"Memory MCP HTTP Server listening on http://localhost:{port}")
        httpd.serve_forever()
