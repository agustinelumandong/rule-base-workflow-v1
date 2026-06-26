"""Unit tests for BookForge MCP server protocol handling."""

import json
import shutil
import unittest
from pathlib import Path

from bookforge.core.scene import init_scene_manifest
from bookforge.core.queue import build_queue
from bookforge.mcp.server import BookForgeMCPServer, TOOL_SCHEMAS, INSTRUCTIONS


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path("tests/temp_test_mcp_server")
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        (self.tmp_dir / "changes").mkdir(parents=True, exist_ok=True)
        (self.tmp_dir / "chapter-summaries.md").write_text("# Chapter Summaries", encoding="utf-8")
        (self.tmp_dir / "rulebook.md").write_text("# Rulebook\n\nTest rules.", encoding="utf-8")
        (self.tmp_dir / "mood-lock.md").write_text("# Mood Lock\n\nTest mood.", encoding="utf-8")
        (self.tmp_dir / "phase-0.md").write_text("# Phase 0\n\nPeriod: 1800\n\n## chapter-01\n\nTest outline.", encoding="utf-8")
        self.server = BookForgeMCPServer(self.tmp_dir, readonly=True)

    def tearDown(self):
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)

    def test_mcp_lists_expected_tools(self):
        tools = self.server.list_tools()
        tool_names = [t["name"] for t in tools]
        expected = [
            "get_queue_status",
            "get_active_scene",
            "build_generation_packet",
            "build_project_kit",
            "validate_scene",
            "build_patch_packet",
            "save_draft",
            "apply_patch",
            "get_scene_report",
            "query_research_cache",
        ]
        self.assertEqual(tool_names, expected)

    def test_mcp_tool_count(self):
        tools = self.server.list_tools()
        self.assertEqual(len(tools), 10)

    def test_mcp_initialize_returns_instructions(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        res = self.server._handle_request(req)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertEqual(res["id"], 1)
        result = res["result"]
        self.assertEqual(result["protocolVersion"], "2024-11-05")
        self.assertIn("tools", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "bookforge")
        self.assertEqual(result["instructions"], INSTRUCTIONS)

    def test_mcp_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = self.server._handle_request(req)
        self.assertEqual(res["id"], 2)
        tools = res["result"]["tools"]
        self.assertEqual(len(tools), 10)
        for tool in tools:
            self.assertIn("name", tool)
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)

    def test_mcp_tool_call_dispatches_correctly(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_queue_status", "arguments": {}},
        }
        res = self.server._handle_request(req)
        self.assertEqual(res["id"], 3)
        content = res["result"]["content"]
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["type"], "text")
        data = json.loads(content[0]["text"])
        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "get_queue_status")

    def test_mcp_unknown_tool_returns_error(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        }
        res = self.server._handle_request(req)
        content = res["result"]["content"]
        data = json.loads(content[0]["text"])
        self.assertFalse(data["ok"])
        self.assertIn("Unknown tool", data["message"])

    def test_mcp_unknown_method_returns_error(self):
        req = {"jsonrpc": "2.0", "id": 5, "method": "unknown/method", "params": {}}
        res = self.server._handle_request(req)
        self.assertIn("error", res)
        self.assertEqual(res["error"]["code"], -32601)

    def test_mcp_readonly_blocks_write_tool(self):
        req = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "save_draft", "arguments": {"text": "test"}},
        }
        res = self.server._handle_request(req)
        content = res["result"]["content"]
        data = json.loads(content[0]["text"])
        self.assertFalse(data["ok"])
        self.assertEqual(data["error_code"], "READONLY_MODE")

    def test_mcp_allow_write_dispatches_write_tool(self):
        init_scene_manifest(self.tmp_dir, "chapter-01", "scene-01", 3500)
        build_queue(self.tmp_dir)
        from bookforge.core.queue import update_queue_scene
        update_queue_scene(self.tmp_dir, "chapter-01/scene-01", status="generation_packet_ready")
        server = BookForgeMCPServer(self.tmp_dir, readonly=False, allow_write=True)
        text = "The morning broke cold over the ridge. " * 200
        req = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "save_draft", "arguments": {"text": text}},
        }
        res = server._handle_request(req)
        content = res["result"]["content"]
        data = json.loads(content[0]["text"])
        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "save_draft")
        self.assertTrue(Path(data["draft_path"]).exists())

    def test_mcp_notifications_initialized_returns_empty(self):
        req = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        res = self.server._handle_request(req)
        self.assertEqual(res, {})

    def test_mcp_tool_schemas_have_required_fields(self):
        for schema in TOOL_SCHEMAS:
            self.assertIn("name", schema)
            self.assertIn("description", schema)
            self.assertIn("inputSchema", schema)
            self.assertEqual(schema["inputSchema"]["type"], "object")

    def test_project_kit_schema_exposes_workspace_override(self):
        schema = next(tool for tool in TOOL_SCHEMAS if tool["name"] == "build_project_kit")
        properties = schema["inputSchema"]["properties"]
        self.assertIn("workspace_name", properties)
        self.assertIn("workspace", properties)


if __name__ == "__main__":
    unittest.main()
